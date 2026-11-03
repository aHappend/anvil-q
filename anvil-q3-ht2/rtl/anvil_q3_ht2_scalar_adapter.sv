module anvil_q3_ht2_scalar_adapter #(
  parameter CLIENTS=3, NUM_LAYERS=36, HIDDEN_SIZE=2048,
  parameter HEAD_DIM=128, MAX_SEQ_LEN=32768,
  localparam NC=CLIENTS>=1 && CLIENTS<=16 ? CLIENTS : 1,
  localparam CW=NC>1 ? $clog2(NC) : 1
) (
  input wire clk, rst_n, flush, invalidate,
  input wire [NC-1:0] c_req_valid, c_req_write,
  output wire [NC-1:0] c_req_ready,
  input wire [NC*2-1:0] c_req_node,
  input wire [NC*4-1:0] c_req_kind,
  input wire [NC*3-1:0] c_req_proj,
  input wire [NC*32-1:0] c_req_layer, c_req_row, c_req_col, c_req_wdata,
  output wire [NC-1:0] c_rsp_valid, c_rsp_error,
  input wire [NC-1:0] c_rsp_ready,
  output wire [NC*32-1:0] c_rsp_rdata,
  output wire idle, fault, drain_done,
  output wire scratch_req_valid,
  input wire scratch_req_ready,
  output wire scratch_req_write,
  output wire [1:0] scratch_req_node,
  output wire [3:0] scratch_req_mask,
  output wire [31:0] scratch_req_slot, scratch_req_index, scratch_req_wdata,
  input wire scratch_rsp_valid,
  output wire scratch_rsp_ready,
  input wire scratch_rsp_error,
  input wire [1:0] scratch_rsp_node,
  input wire [3:0] scratch_rsp_mask,
  input wire [127:0] scratch_rsp_rdata,
  output wire memory_req_valid,
  input wire memory_req_ready,
  output wire [32:0] memory_req_address,
  output wire [7:0] memory_req_burstcount,
  input wire memory_rsp_valid, memory_rsp_error,
  input wire [511:0] memory_rsp_rdata,
  output wire [63:0] physical_read_beats
);
  localparam [127:0] H=128'(HIDDEN_SIZE), D=128'(HEAD_DIM);
  localparam [127:0] NORM_BYTES=(2*128'(NUM_LAYERS)+1)*H*2;
  localparam [127:0] ROPE_BYTES=128'(MAX_SEQ_LEN)*D*4;
  localparam LEGAL=CLIENTS==NC && NUM_LAYERS>0 && HIDDEN_SIZE>0 &&
    HEAD_DIM>0 && (HEAD_DIM&1)==0 && MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    H<=128'hffffffff && D<=128'hffffffff &&
    NORM_BYTES<=128'h01000000 && ROPE_BYTES<=128'h12000000;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: scalar image adapter");
    assign c_req_ready=0; assign c_rsp_valid=0; assign c_rsp_error=0; assign c_rsp_rdata=0;
    assign idle=0; assign fault=0; assign drain_done=0;
    assign scratch_req_valid=0; assign scratch_req_write=0; assign scratch_req_node=0;
    assign scratch_req_mask=0; assign scratch_req_slot=0; assign scratch_req_index=0;
    assign scratch_req_wdata=0; assign scratch_rsp_ready=0;
    assign memory_req_valid=0; assign memory_req_address=0; assign memory_req_burstcount=0;
    assign physical_read_beats=0;
  end else begin: datapath
    localparam IDLE=0, CHECK=1, ROW_PRODUCT=2, COLUMN_ADD=3, IMAGE_BASE=4,
      LINE_CHECK=5, READ_REQUEST=6, READ_RETURN=7, SELECT_WORD=8,
      SELECT_HALF=9, RESPONSE=10, SCRATCH_REQUEST=11, SCRATCH_RETURN=12,
      CANCEL_DRAIN=13, FAIL_DRAIN=14, FAULTED=15;
    reg [3:0] state;
    reg failed, writing, response_error, memory_pending, scratch_pending, cache_valid;
    reg [CW-1:0] pointer, owner;
    reg [1:0] node;
    reg [3:0] kind;
    reg [2:0] projection;
    reg [31:0] layer, row, column, write_data, response_data, selected_word;
    reg [63:0] row_ordinal, row_product, byte_offset, logical_address, physical_count;
    reg [32:0] cached_address;
    reg [511:0] cached_line;
    wire running=rst_n && !flush;
    wire active=running && !failed && state!=CANCEL_DRAIN && state!=FAIL_DRAIN;
    wire scratch_fire=scratch_req_valid && scratch_req_ready;
    wire scratch_known=scratch_pending || scratch_fire;
    wire scratch_return=scratch_rsp_valid && scratch_rsp_ready;
    wire memory_fire=memory_req_valid && memory_req_ready;
    wire memory_known=memory_pending || memory_fire;
    wire memory_return=memory_rsp_valid && memory_known;
    wire [32:0] aligned_address={logical_address[32:6],6'd0};
    wire [63:0] image_origin=kind==11 ? 64'h6e000000 : 64'h6d000000;
    wire [63:0] image_allocation=kind==11 ?
      (64'(ROPE_BYTES)+63)&64'hffffffffffffffc0 :
      (64'(NORM_BYTES)+63)&64'hffffffffffffffc0;
    wire address_bad=logical_address<image_origin ||
      logical_address>=image_origin+image_allocation ||
      {31'd0,aligned_address}+64>image_origin+image_allocation ||
      logical_address[63:33]!=0 || logical_address[0] ||
      (kind==11 && logical_address[1]);
    wire identity_bad=scratch_rsp_valid && (!scratch_known || scratch_rsp_node!=node ||
      scratch_rsp_mask!=(4'b0001<<node));
    reg command_bad, classification_bad;
    wire fault_now=active && (identity_bad || (memory_rsp_valid && !memory_known) ||
      memory_rsp_error || classification_bad);
    wire drained=!memory_pending && !scratch_pending;
    integer selected, candidate;

    always @* begin
      selected=-1; candidate=0;
      for (integer c=0;c<NC;c=c+1) begin
        candidate=32'(pointer)+c;
        if (candidate>=NC) candidate=candidate-NC;
        if (selected<0 && c_req_valid[candidate]) selected=candidate;
      end
      command_bad=projection!=0;
      case (kind)
        8: command_bad=command_bad || layer!=0 || row>14;
        5,6: command_bad=command_bad || writing || layer>=NUM_LAYERS ||
          row!=0 || column>=HIDDEN_SIZE;
        7: command_bad=command_bad || writing || layer!=0 ||
          row!=0 || column>=HIDDEN_SIZE;
        11: command_bad=command_bad || writing || layer!=0 ||
          row>=MAX_SEQ_LEN || column>=HEAD_DIM;
        default: command_bad=1;
      endcase
      classification_bad=0;
`ifndef SYNTHESIS
      if (state==CHECK && (^{writing,node,kind,projection,layer,row,column})===1'bx)
        command_bad=1;
      if (scratch_rsp_valid && scratch_known && !scratch_rsp_error &&
          (^scratch_rsp_rdata[node*32+:32])===1'bx) classification_bad=1;
      if (state==SELECT_HALF &&
          (kind==11 ? (^selected_word)===1'bx :
           logical_address[1] ? (^selected_word[31:16])===1'bx :
           (^selected_word[15:0])===1'bx)) classification_bad=1;
`endif
    end

    for (genvar c=0;c<NC;c=c+1) begin: clients
      assign c_req_ready[c]=active && state==IDLE && drained && selected==c &&
        !memory_rsp_valid && !scratch_rsp_valid;
      assign c_rsp_valid[c]=active && state==RESPONSE && owner==c;
      assign c_rsp_error[c]=c_rsp_valid[c] && response_error;
      assign c_rsp_rdata[c*32+:32]=c_rsp_valid[c] && !response_error ? response_data : 32'd0;
    end
    assign idle=active && state==IDLE && drained;
    assign drain_done=running && drained && (state==IDLE || state==FAULTED);
    assign fault=running && failed;
    assign scratch_req_valid=active && state==SCRATCH_REQUEST && !scratch_pending;
    assign scratch_req_write=scratch_req_valid && writing;
    assign scratch_req_node=scratch_req_valid ? node : 2'd0;
    assign scratch_req_mask=scratch_req_valid ? (4'b0001<<node) : 4'd0;
    assign scratch_req_slot=scratch_req_valid ? row : 32'd0;
    assign scratch_req_index=scratch_req_valid ? column : 32'd0;
    assign scratch_req_wdata=scratch_req_write ? write_data : 32'd0;
    assign scratch_rsp_ready=running && scratch_known;
    assign memory_req_valid=active && state==READ_REQUEST && !memory_pending;
    assign memory_req_address=memory_req_valid ? aligned_address : 33'd0;
    assign memory_req_burstcount=memory_req_valid ? 8'd1 : 8'd0;
    assign physical_read_beats=running ? physical_count : 64'd0;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; failed<=0; writing<=0; response_error<=0;
        memory_pending<=0; scratch_pending<=0; cache_valid<=0;
        pointer<=0; owner<=0; node<=0; kind<=0; projection<=0;
        layer<=0; row<=0; column<=0; write_data<=0; response_data<=0;
        selected_word<=0; row_ordinal<=0; row_product<=0; byte_offset<=0;
        logical_address<=0; physical_count<=0; cached_address<=0; cached_line<=0;
      end else begin
        if (scratch_fire && !scratch_return) scratch_pending<=1;
        if (scratch_return && scratch_known) scratch_pending<=0;
        if (memory_fire && !memory_rsp_valid) memory_pending<=1;
        if (memory_rsp_valid && memory_known) memory_pending<=0;
        if (memory_fire) physical_count<=physical_count+1'b1;
        if (invalidate) cache_valid<=0;
        if (flush) begin
          state<=CANCEL_DRAIN; failed<=0; cache_valid<=0; response_error<=0;
          pointer<=0; owner<=0; node<=0; writing<=0; kind<=0; projection<=0;
          layer<=0; row<=0; column<=0; write_data<=0; response_data<=0;
          selected_word<=0; row_ordinal<=0; row_product<=0; byte_offset<=0;
          logical_address<=0; cached_address<=0; cached_line<=0; physical_count<=0;
        end else if (fault_now) begin
          failed<=1; cache_valid<=0; response_data<=0; state<=FAIL_DRAIN;
        end else case (state)
          IDLE: if (active && selected>=0 && c_req_ready[selected]) begin
            owner<=CW'(selected); writing<=c_req_write[selected];
            node<=c_req_node[selected*2+:2]; kind<=c_req_kind[selected*4+:4];
            projection<=c_req_proj[selected*3+:3]; layer<=c_req_layer[selected*32+:32];
            row<=c_req_row[selected*32+:32]; column<=c_req_col[selected*32+:32];
            write_data<=c_req_wdata[selected*32+:32]; response_data<=0;
            response_error<=0; state<=CHECK;
          end
          CHECK: begin
            if (command_bad) begin response_error<=1; state<=RESPONSE; end
            else if (kind==8) state<=SCRATCH_REQUEST;
            else begin
              if (kind==11) row_ordinal<={32'd0,row};
              else if (kind==7) row_ordinal<=64'(NUM_LAYERS)*2;
              else row_ordinal<=({32'd0,layer}<<1)+64'(kind==6);
              state<=ROW_PRODUCT;
            end
          end
          ROW_PRODUCT: begin
            if (kind==11) row_product<=row_ordinal*64'(HEAD_DIM*4);
            else row_product<=row_ordinal*64'(HIDDEN_SIZE*2);
            state<=COLUMN_ADD;
          end
          COLUMN_ADD: begin
            byte_offset<=row_product+({32'd0,column}<<(kind==11 ? 2 : 1));
            state<=IMAGE_BASE;
          end
          IMAGE_BASE: begin logical_address<=image_origin+byte_offset; state<=LINE_CHECK; end
          LINE_CHECK: begin
            if (address_bad) begin response_error<=1; state<=RESPONSE; end
            else if (!invalidate && cache_valid && cached_address==aligned_address)
              state<=SELECT_WORD;
            else state<=READ_REQUEST;
          end
          READ_REQUEST: if (memory_fire) begin
            if (!memory_return) state<=READ_RETURN;
            else begin
              cached_line<=memory_rsp_rdata; cached_address<=aligned_address;
              cache_valid<=!invalidate; state<=SELECT_WORD;
            end
          end
          READ_RETURN: if (memory_return) begin
            cached_line<=memory_rsp_rdata; cached_address<=aligned_address;
            cache_valid<=!invalidate; state<=SELECT_WORD;
          end
          SELECT_WORD: begin
            selected_word<=cached_line[{logical_address[5:2],5'd0}+:32];
            state<=SELECT_HALF;
          end
          SELECT_HALF: begin
            if (kind==11) response_data<=selected_word;
            else if (logical_address[1]) response_data<={16'd0,selected_word[31:16]};
            else response_data<={16'd0,selected_word[15:0]};
            state<=RESPONSE;
          end
          SCRATCH_REQUEST: if (scratch_fire) begin
            if (!scratch_return) state<=SCRATCH_RETURN;
            else begin
              response_data<=scratch_rsp_rdata[node*32+:32];
              response_error<=scratch_rsp_error; state<=RESPONSE;
            end
          end
          SCRATCH_RETURN: if (scratch_return) begin
            response_data<=scratch_rsp_rdata[node*32+:32];
            response_error<=scratch_rsp_error; state<=RESPONSE;
          end
          RESPONSE: if (c_rsp_ready[owner]) begin
            pointer<=owner==NC-1 ? {CW{1'b0}} : owner+1'b1;
            response_data<=0; response_error<=0; state<=IDLE;
          end
          CANCEL_DRAIN: if (drained) state<=IDLE;
          FAIL_DRAIN: if (drained) state<=FAULTED;
          FAULTED: begin end
          default: begin failed<=1; cache_valid<=0; state<=FAIL_DRAIN; end
        endcase
      end
    end
  end endgenerate
endmodule
