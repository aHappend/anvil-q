module anvil_q3_ht2_token_io #(
  parameter HIDDEN_SIZE=2048, VOCAB_SIZE=151936
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_id, cmd_epoch,
  input wire cmd_project,
  input wire [3:0] cmd_mask,
  input wire [127:0] cmd_tokens,
  output wire done, error, idle, fault, drain_done,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_id, logit_epoch, logit_index,
  output wire [1:0] logit_node,
  output wire signed [31:0] logit_data,
  output wire logit_last,
  output wire argmax_valid,
  output wire [127:0] argmax_tokens,
  output wire scratch_req_valid,
  input wire scratch_req_ready,
  output wire scratch_req_write,
  output wire [1:0] scratch_req_node,
  output wire [3:0] scratch_req_mask,
  output wire [31:0] scratch_req_slot, scratch_req_index,
  output wire signed [31:0] scratch_req_wdata,
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
  output wire [63:0] physical_read_beats, activation_read_columns,
  output wire [63:0] candidate_weight_values
);
  localparam [127:0] IMAGE_BYTES=128'(HIDDEN_SIZE)*128'(VOCAB_SIZE)*2;
  localparam [127:0] IMAGE_ALLOCATION=(IMAGE_BYTES+63)&128'hffffffffffffffffffffffffffffffc0;
  localparam LEGAL=HIDDEN_SIZE>0 && (HIDDEN_SIZE&7)==0 &&
    VOCAB_SIZE>0 && 128'(VOCAB_SIZE)<=128'hffffffff &&
    IMAGE_BYTES>0 && IMAGE_ALLOCATION<=128'h40000000;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: shared token image dimensions");
    assign cmd_ready=0; assign done=0; assign error=0; assign idle=0;
    assign fault=0; assign drain_done=0; assign logit_valid=0;
    assign logit_id=0; assign logit_epoch=0; assign logit_index=0;
    assign logit_node=0; assign logit_data=0; assign logit_last=0;
    assign argmax_valid=0; assign argmax_tokens=0;
    assign scratch_req_valid=0; assign scratch_req_write=0; assign scratch_req_node=0;
    assign scratch_req_mask=0; assign scratch_req_slot=0; assign scratch_req_index=0;
    assign scratch_req_wdata=0; assign scratch_rsp_ready=0;
    assign memory_req_valid=0; assign memory_req_address=0; assign memory_req_burstcount=0;
    assign physical_read_beats=0; assign activation_read_columns=0;
    assign candidate_weight_values=0;
  end else begin: datapath
    localparam AW=HIDDEN_SIZE>1 ? $clog2(HIDDEN_SIZE) : 1;
    localparam IDLE=0, LOAD=1, LOAD_RETURN=2, NODE_FIND=3, ROW_PRODUCT=4,
      COMPONENT_OFFSET=5, IMAGE_BASE=6, LINE_CHECK=7, LINE_REQUEST=8,
      LINE_RETURN=9, WEIGHT_SELECT=10, WEIGHT_DECODE=11, EMBED_WRITE=12,
      EMBED_RETURN=13, ARRAY_READ=14, ARRAY_CAPTURE=15, MULTIPLY=16,
      MULTIPLY_WAIT=17, ACCUMULATE=18, ACCUMULATE_WAIT=19,
      ROUND=20, LOGIT_FIND=21, LOGIT=22, COMPLETE=23,
      FAIL_FLUSH=24, FAIL_DRAIN=25, FAIL_DONE=26, FAULTED=27,
      CANCEL_DRAIN=28, CANCEL_DONE=29;
    reg [4:0] state;
    reg failed, project, scratch_pending, memory_pending, cache_valid;
    reg [31:0] id, epoch, component, vocabulary;
    reg [3:0] mask;
    reg [127:0] tokens, activations, logits, best_tokens, best_values;
    reg [1:0] node;
    reg [63:0] row_product, element_offset, logical_address;
    reg [32:0] cached_address;
    reg [511:0] cached_line;
    reg [15:0] weight_f16;
    reg signed [31:0] weight;
    reg [127:0] terms [0:3], sums [0:3];
    reg [63:0] physical_count, activation_count, consumer_count;
    wire [127:0] activation_q;
    wire [3:0] multiplier_ready,multiplier_done,multiplier_error;
    wire [255:0] products;
    wire [3:0] accumulator_ready,accumulator_valid,accumulator_error;
    wire [511:0] accumulated;
    wire [127:0] rounded;
    wire running=rst_n && !flush;
    wire unit_flush=flush || state==FAIL_FLUSH;
    wire active=running && !unit_flush && !failed &&
      state!=CANCEL_DRAIN && state!=CANCEL_DONE;
    wire scratch_fire=scratch_req_valid && scratch_req_ready;
    wire scratch_known=scratch_pending || scratch_fire;
    wire scratch_return=scratch_rsp_valid && scratch_rsp_ready;
    wire memory_fire=memory_req_valid && memory_req_ready;
    wire memory_known=memory_pending || memory_fire;
    wire memory_return=memory_rsp_valid && memory_known;
    wire load_return=active && (state==LOAD || state==LOAD_RETURN) && scratch_return;
    wire [31:0] selected_row=project ? vocabulary : tokens[node*32+:32];
    wire [32:0] aligned_address={logical_address[32:6],6'd0};
    wire [63:0] physical_end={31'd0,aligned_address}+64'd64;
    wire [63:0] image_end=64'h80000000+64'(IMAGE_ALLOCATION);
    wire address_bad=logical_address<64'h80000000 || logical_address>=image_end ||
      physical_end>image_end || physical_end>64'hc0000000;
    wire [15:0] selected_half=cached_line[{logical_address[5:1],4'd0}+:16];
    wire signed [31:0] decoded_weight=anvil_q3_pkg::f16_q16(weight_f16);
    wire all_multiplier_ready=(multiplier_ready&mask)==mask;
    wire all_multiplier_done=(multiplier_done&mask)==mask;
    wire all_accumulator_ready=(accumulator_ready&mask)==mask;
    wire all_accumulator_valid=(accumulator_valid&mask)==mask;
    wire scratch_bad=scratch_rsp_valid && (!scratch_known || scratch_rsp_error ||
      ((state==LOAD || state==LOAD_RETURN) &&
        (scratch_rsp_node!=0 || scratch_rsp_mask!=mask)) ||
      ((state==EMBED_WRITE || state==EMBED_RETURN) &&
        (scratch_rsp_node!=node || scratch_rsp_mask!=(4'b0001<<node))));
    reg classification_bad, command_bad;
    wire fault_now=active && (scratch_bad || (memory_rsp_valid && !memory_known) ||
      memory_rsp_error || classification_bad ||
      (|(multiplier_error&mask)) || (|(accumulator_error&mask)));
    wire drained=!scratch_pending && !memory_pending;
    wire [2:0] active_count={2'd0,mask[0]}+{2'd0,mask[1]}+
      {2'd0,mask[2]}+{2'd0,mask[3]};
    integer n;

    always @* begin
      command_bad=cmd_mask==0;
      classification_bad=state==WEIGHT_DECODE && anvil_q3_pkg::f16_invalid(weight_f16);
      for (integer j=0;j<4;j=j+1) begin
        if (cmd_mask[j] && cmd_tokens[j*32+:32]>=VOCAB_SIZE && !cmd_project)
          command_bad=1;
`ifndef SYNTHESIS
        if (load_return && mask[j] && (^scratch_rsp_rdata[j*32+:32])===1'bx)
          classification_bad=1;
`endif
      end
`ifndef SYNTHESIS
      if ((^{cmd_id,cmd_epoch,cmd_project,cmd_mask})===1'bx) command_bad=1;
      for (integer j=0;j<4;j=j+1)
        if (cmd_mask[j] && !cmd_project && (^cmd_tokens[j*32+:32])===1'bx)
          command_bad=1;
      if (state==WEIGHT_DECODE && (^weight_f16)===1'bx) classification_bad=1;
      if (scratch_rsp_valid &&
          (^{scratch_rsp_error,scratch_rsp_node,scratch_rsp_mask})===1'bx)
        classification_bad=1;
`endif
    end

    assign cmd_ready=running && !failed && state==IDLE && drained &&
      !scratch_rsp_valid && !memory_rsp_valid;
    assign done=running && (state==COMPLETE || state==FAIL_DONE);
    assign error=done && failed;
    assign idle=cmd_ready;
    assign fault=running && failed;
    assign drain_done=running && (state==IDLE || state==CANCEL_DONE);
    assign logit_valid=active && state==LOGIT;
    assign logit_id=logit_valid ? id : 32'd0;
    assign logit_epoch=logit_valid ? epoch : 32'd0;
    assign logit_node=logit_valid ? node : 2'd0;
    assign logit_index=logit_valid ? vocabulary : 32'd0;
    assign logit_data=logit_valid ? $signed(logits[node*32+:32]) : 32'sd0;
    assign logit_last=logit_valid && vocabulary==VOCAB_SIZE-1;
    assign argmax_valid=done && !failed && project;
    assign argmax_tokens=argmax_valid ? best_tokens : 128'd0;
    assign scratch_req_valid=active && !scratch_pending &&
      (state==LOAD || state==EMBED_WRITE);
    assign scratch_req_write=scratch_req_valid && state==EMBED_WRITE;
    assign scratch_req_node=scratch_req_write ? node : 2'd0;
    assign scratch_req_mask=!scratch_req_valid ? 4'd0 :
      scratch_req_write ? (4'b0001<<node) : mask;
    assign scratch_req_slot=scratch_req_valid && !scratch_req_write ? 32'd14 : 32'd0;
    assign scratch_req_index=scratch_req_valid ? component : 32'd0;
    assign scratch_req_wdata=scratch_req_write ? weight : 32'sd0;
    assign scratch_rsp_ready=running && (scratch_pending || scratch_fire);
    assign memory_req_valid=active && state==LINE_REQUEST && !memory_pending;
    assign memory_req_address=memory_req_valid ? aligned_address : 33'd0;
    assign memory_req_burstcount=memory_req_valid ? 8'd1 : 8'd0;
    assign physical_read_beats=running ? physical_count : 64'd0;
    assign activation_read_columns=running ? activation_count : 64'd0;
    assign candidate_weight_values=running ? consumer_count : 64'd0;

    for (genvar b=0;b<4;b=b+1) begin: candidate
      (* ramstyle="M20K", nomem2reg *) reg [31:0] data [0:HIDDEN_SIZE-1];
      reg [31:0] read_data;
      assign activation_q[b*32+:32]=mask[b] ? read_data : 32'd0;
      assign rounded[b*32+:32]=anvil_q3_pkg::round_q32_to_q16($signed(sums[b]));
      always @(posedge clk) begin
        if (load_return && !fault_now && mask[b])
          data[AW'(component)]<=scratch_rsp_rdata[b*32+:32];
        if (active && state==ARRAY_READ && mask[b]) read_data<=data[AW'(component)];
      end
      anvil_q3_multiplier #(.A_W(32),.B_W(32)) multiplier (
        .clk(clk),.rst_n(rst_n),.flush(unit_flush),
        .start(active && state==MULTIPLY && all_multiplier_ready && mask[b]),
        .a($signed(activations[b*32+:32])),.b(weight),
        .ready(multiplier_ready[b]),.done(multiplier_done[b]),
        .error(multiplier_error[b]),.product(products[b*64+:64])
      );
      anvil_q3_accumulator accumulator (
        .clk(clk),.rst_n(rst_n),.flush(unit_flush),
        .in_valid(active && state==ACCUMULATE && all_accumulator_ready && mask[b]),
        .in_ready(accumulator_ready[b]),.in_first(component==0),.in_value($signed(terms[b])),
        .out_valid(accumulator_valid[b]),
        .out_ready(active && state==ACCUMULATE_WAIT && all_accumulator_valid),
        .out_error(accumulator_error[b]),.out_sum(accumulated[b*128+:128])
      );
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; failed<=0; project<=0; scratch_pending<=0; memory_pending<=0;
        cache_valid<=0; id<=0; epoch<=0; component<=0; vocabulary<=0; mask<=0;
        tokens<=0; activations<=0; logits<=0; best_tokens<=0; best_values<=0; node<=0;
        row_product<=0; element_offset<=0; logical_address<=0; cached_address<=0;
        cached_line<=0; weight_f16<=0; weight<=0;
        physical_count<=0; activation_count<=0; consumer_count<=0;
        for (n=0;n<4;n=n+1) begin terms[n]<=0; sums[n]<=0; end
      end else begin
        if (scratch_fire && !scratch_return) scratch_pending<=1;
        if (scratch_return && scratch_known) scratch_pending<=0;
        if (memory_fire && !memory_rsp_valid) memory_pending<=1;
        if (memory_rsp_valid && memory_known) memory_pending<=0;
        if (memory_fire) physical_count<=physical_count+1'b1;
        if (scratch_fire && !scratch_req_write) activation_count<=activation_count+1'b1;
        if (flush) begin
          state<=CANCEL_DRAIN; failed<=0; project<=0; cache_valid<=0;
          id<=0; epoch<=0; component<=0; vocabulary<=0; mask<=0;
          tokens<=0; activations<=0; logits<=0; best_tokens<=0; best_values<=0; node<=0;
          row_product<=0; element_offset<=0; logical_address<=0; cached_address<=0;
          cached_line<=0; weight_f16<=0; weight<=0;
          physical_count<=0; activation_count<=0; consumer_count<=0;
          for (n=0;n<4;n=n+1) begin terms[n]<=0; sums[n]<=0; end
        end else if (fault_now) begin
          failed<=1; cache_valid<=0; state<=FAIL_FLUSH;
        end else case (state)
          IDLE: if (cmd_valid && cmd_ready) begin
            id<=cmd_id; epoch<=cmd_epoch; project<=cmd_project; mask<=cmd_mask;
            tokens<=cmd_tokens; component<=0; vocabulary<=0; node<=0;
            cache_valid<=0; best_tokens<=0; best_values<=0; logits<=0;
            physical_count<=0; activation_count<=0; consumer_count<=0;
            if (command_bad) begin failed<=1; state<=FAIL_FLUSH; end
            else if (cmd_project) state<=LOAD;
            else state<=NODE_FIND;
          end
          LOAD: if (scratch_fire) begin
            if (!scratch_return) state<=LOAD_RETURN;
            else if (component+1'b1==HIDDEN_SIZE) begin component<=0; state<=ARRAY_READ; end
            else component<=component+1'b1;
          end
          LOAD_RETURN: if (scratch_return) begin
            if (component+1'b1==HIDDEN_SIZE) begin component<=0; state<=ARRAY_READ; end
            else begin component<=component+1'b1; state<=LOAD; end
          end
          NODE_FIND: begin
            if (mask[node]) state<=ROW_PRODUCT;
            else if (node==3) state<=COMPLETE;
            else node<=node+1'b1;
          end
          ARRAY_READ: state<=ARRAY_CAPTURE;
          ARRAY_CAPTURE: begin activations<=activation_q; state<=ROW_PRODUCT; end
          ROW_PRODUCT: begin
            row_product<={32'd0,selected_row}*64'(HIDDEN_SIZE*2);
            state<=COMPONENT_OFFSET;
          end
          COMPONENT_OFFSET: begin
            element_offset<=row_product+({32'd0,component}<<1);
            state<=IMAGE_BASE;
          end
          IMAGE_BASE: begin logical_address<=64'h80000000+element_offset; state<=LINE_CHECK; end
          LINE_CHECK: begin
            if (address_bad) begin failed<=1; cache_valid<=0; state<=FAIL_FLUSH; end
            else if (cache_valid && cached_address==aligned_address) state<=WEIGHT_SELECT;
            else state<=LINE_REQUEST;
          end
          LINE_REQUEST: if (memory_fire) begin
            if (!memory_return) state<=LINE_RETURN;
            else begin
              cached_line<=memory_rsp_rdata; cached_address<=aligned_address;
              cache_valid<=1; state<=WEIGHT_SELECT;
            end
          end
          LINE_RETURN: if (memory_return) begin
            cached_line<=memory_rsp_rdata; cached_address<=aligned_address;
            cache_valid<=1; state<=WEIGHT_SELECT;
          end
          WEIGHT_SELECT: begin weight_f16<=selected_half; state<=WEIGHT_DECODE; end
          WEIGHT_DECODE: begin
            weight<=decoded_weight;
            if (project) state<=MULTIPLY;
            else state<=EMBED_WRITE;
          end
          EMBED_WRITE: if (scratch_fire) begin
            if (!scratch_return) state<=EMBED_RETURN;
            else if (component+1'b1<HIDDEN_SIZE) begin
              component<=component+1'b1; state<=ROW_PRODUCT;
            end else if (node==3) state<=COMPLETE;
            else begin component<=0; node<=node+1'b1; state<=NODE_FIND; end
          end
          EMBED_RETURN: if (scratch_return) begin
            if (component+1'b1<HIDDEN_SIZE) begin
              component<=component+1'b1; state<=ROW_PRODUCT;
            end else if (node==3) state<=COMPLETE;
            else begin component<=0; node<=node+1'b1; state<=NODE_FIND; end
          end
          MULTIPLY: if (all_multiplier_ready) begin
            consumer_count<=consumer_count+{61'd0,active_count};
            state<=MULTIPLY_WAIT;
          end
          MULTIPLY_WAIT: if (all_multiplier_done) begin
            for (n=0;n<4;n=n+1)
              terms[n]<=mask[n] ? {{64{products[n*64+63]}},products[n*64+:64]} : 128'd0;
            state<=ACCUMULATE;
          end
          ACCUMULATE: if (all_accumulator_ready) state<=ACCUMULATE_WAIT;
          ACCUMULATE_WAIT: if (all_accumulator_valid) begin
            for (n=0;n<4;n=n+1)
              sums[n]<=mask[n] ? accumulated[n*128+:128] : 128'd0;
            if (component+1'b1==HIDDEN_SIZE) state<=ROUND;
            else begin component<=component+1'b1; state<=ARRAY_READ; end
          end
          ROUND: begin logits<=rounded; node<=0; state<=LOGIT_FIND; end
          LOGIT_FIND: begin
            if (mask[node]) state<=LOGIT;
            else if (node==3) begin
              if (vocabulary+1'b1==VOCAB_SIZE) state<=COMPLETE;
              else begin vocabulary<=vocabulary+1'b1; component<=0; state<=ARRAY_READ; end
            end else node<=node+1'b1;
          end
          LOGIT: if (logit_valid && logit_ready) begin
            if (vocabulary==0 || $signed(logits[node*32+:32])>$signed(best_values[node*32+:32])) begin
              best_values[node*32+:32]<=logits[node*32+:32];
              best_tokens[node*32+:32]<=vocabulary;
            end
            if (node!=3) begin node<=node+1'b1; state<=LOGIT_FIND; end
            else if (vocabulary+1'b1==VOCAB_SIZE) state<=COMPLETE;
            else begin vocabulary<=vocabulary+1'b1; component<=0; state<=ARRAY_READ; end
          end
          COMPLETE: state<=IDLE;
          FAIL_FLUSH: state<=FAIL_DRAIN;
          FAIL_DRAIN: if (drained) state<=FAIL_DONE;
          FAIL_DONE: state<=FAULTED;
          FAULTED: state<=FAULTED;
          CANCEL_DRAIN: if (drained) state<=CANCEL_DONE;
          CANCEL_DONE: state<=IDLE;
          default: begin failed<=1; state<=FAIL_FLUSH; end
        endcase
      end
    end
  end endgenerate
endmodule
