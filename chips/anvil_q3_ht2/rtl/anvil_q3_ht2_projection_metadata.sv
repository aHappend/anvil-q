module anvil_q3_ht2_projection_metadata #(
  parameter MAX_INPUTS=11008, GROUP_SIZE=128
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [32:0] cmd_qzeros_base, cmd_scales_base,
  input wire [31:0] cmd_inputs, cmd_outputs, cmd_row_base,
  output wire done, error, idle, fault, drain_done,
  input wire query_valid,
  output wire query_ready,
  input wire [31:0] query_column,
  output wire operand_valid,
  input wire operand_ready,
  output wire operand_error,
  output wire [511:0] operand_qzero,
  output wire [2047:0] operand_scale_f16,
  output wire memory_req_valid,
  input wire memory_req_ready,
  output wire [32:0] memory_req_address,
  output wire [7:0] memory_req_burstcount,
  input wire memory_rsp_valid, memory_rsp_error,
  input wire [511:0] memory_rsp_rdata,
  output wire [31:0] issued_metadata_beats
);
  localparam LEGAL=MAX_INPUTS>0 && 64'(MAX_INPUTS)<=64'hffffffff &&
    (GROUP_SIZE==8 || GROUP_SIZE==16 || GROUP_SIZE==32 ||
     GROUP_SIZE==64 || GROUP_SIZE==128);
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: projection metadata parameters");
    assign cmd_ready=0; assign done=0; assign error=0; assign idle=0;
    assign fault=0; assign drain_done=0; assign query_ready=0;
    assign operand_valid=0; assign operand_error=0;
    assign operand_qzero=0; assign operand_scale_f16=0;
    assign memory_req_valid=0; assign memory_req_address=0;
    assign memory_req_burstcount=0; assign issued_metadata_beats=0;
  end else begin: datapath
    localparam GSHIFT=$clog2(GROUP_SIZE);
    localparam GROUPS=(64'(MAX_INPUTS)+GROUP_SIZE-1)>>GSHIFT;
    localparam GA=GROUPS>1 ? $clog2(GROUPS) : 1;
    localparam IDLE=0, EXTENT_ROUND=1, EXTENT_END=2, EXTENT_CHECK=3,
      GROUP_PRODUCT=4, GROUP_START=5, GROUP_LINES=6,
      REQUEST=7, RETURN=8, ZERO_SAVE=9, NEXT_GROUP=10,
      READY=11, QUERY_READ=12, RESPONSE=13, DRAIN=14, FAULTED=15;
    reg [3:0] state;
    reg failed, cancelled, outstanding, scales, loaded_pulse, drain_pulse;
    reg [31:0] inputs, outputs, row_base, rows, groups, group_index;
    reg [31:0] zero_words, zero_stride, line_index, last_line, physical_count;
    reg [32:0] zero_base, scale_base, request_address;
    reg [63:0] zero_bytes, scale_bytes, zero_allocation, scale_allocation;
    reg [63:0] zero_end, scale_end, group_product, span_start;
    reg [8:0] span_bytes;
    reg command_bad, query_bad;
    reg [GA-1:0] query_group;
    wire [511:0] zero_q;
    wire [2047:0] scale_q;
    wire [31:0] source_word [0:16];
    wire running=rst_n && !flush;
    wire request_fire=memory_req_valid && memory_req_ready;
    wire response_known=outstanding || request_fire;
    wire response_fire=running && memory_rsp_valid && response_known;
    wire query_fire=query_valid && query_ready;
    wire [63:0] rounded_zero=(zero_bytes+63)&64'hffffffffffffffc0;
    wire [63:0] rounded_scale=(scale_bytes+63)&64'hffffffffffffffc0;
    wire [63:0] aligned_start=span_start&64'hffffffffffffffc0;
    wire [9:0] span_end_offset={4'd0,span_start[5:0]}+{1'b0,span_bytes};
    wire [63:0] physical_end=aligned_start+
      (({54'd0,span_end_offset}+63)&64'hffffffffffffffc0);
    wire bad_lines=span_bytes==0 || span_end_offset>320 ||
      aligned_start < (scales ? {31'd0,scale_base} : {31'd0,zero_base}) ||
      physical_end > (scales ? scale_end : zero_end);
    wire transport_fault=(memory_rsp_valid && !response_known) ||
      memory_rsp_error;
    wire [127:0] scale_bad;
    wire scale_capture=response_fire && scales &&
      (state==REQUEST || state==RETURN) && !transport_fault && !failed;
    wire zero_capture=response_fire && !scales &&
      (state==REQUEST || state==RETURN) && !transport_fault && !failed;
    wire fault_now=transport_fault || (scale_capture && |scale_bad);
    wire ram_read=running && state==QUERY_READ && !query_bad && !fault_now;
    wire zero_save=running && state==ZERO_SAVE && !fault_now;
    wire [63:0] remaining={32'd0,cmd_outputs}-{32'd0,cmd_row_base};
    wire [31:0] command_rows=remaining>128 ? 32'd128 : remaining[31:0];
    wire [63:0] command_last={32'd0,cmd_row_base}+{32'd0,command_rows}-1;
    wire [63:0] command_zero_stride=(({32'd0,cmd_outputs}+64'd7)>>3)<<2;

    assign cmd_ready=running && !failed && !memory_rsp_valid &&
      (state==IDLE || state==READY);
    assign query_ready=running && !failed && state==READY &&
      !cmd_valid && !memory_rsp_valid;
    assign done=running && loaded_pulse;
    assign error=running && failed;
    assign idle=running && !failed && !outstanding &&
      (state==IDLE || state==READY);
    assign fault=running && failed;
    assign drain_done=running && (drain_pulse || state==IDLE);
    assign operand_valid=running && state==RESPONSE && !failed;
    assign operand_error=operand_valid && query_bad;
    assign operand_qzero=operand_valid && !query_bad ? zero_q : 512'd0;
    assign operand_scale_f16=operand_valid && !query_bad ? scale_q : 2048'd0;
    assign memory_req_valid=running && !failed && state==REQUEST;
    assign memory_req_address=memory_req_valid ? request_address : 33'd0;
    assign memory_req_burstcount=memory_req_valid ? 8'd1 : 8'd0;
    assign issued_metadata_beats=running ? physical_count : 32'd0;

    for (genvar w=0;w<17;w=w+1) begin: source_words
      reg [31:0] data;
      reg [2:0] owner_line;
      reg [3:0] owner_word;
      wire [5:0] word_offset={2'd0,span_start[5:2]}+6'(w);
      assign source_word[w]=data;
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin owner_line<=0; owner_word<=0; end
        else if (flush) begin owner_line<=0; owner_word<=0; end
        else if (state==NEXT_GROUP && !scales && !fault_now) begin
          owner_line<={2'd0,word_offset[4]};
          owner_word<=word_offset[3:0];
        end
      end
      always @(posedge clk) begin
        if (zero_capture && !fault_now && w<zero_words &&
            line_index==owner_line)
          data<=memory_rsp_rdata[{owner_word,5'd0}+:32];
      end
    end
    for (genvar b=0;b<128;b=b+1) begin: row_bank
      (* ramstyle="M20K", nomem2reg *) reg [3:0] zeros [0:GROUPS-1];
      (* ramstyle="M20K", nomem2reg *) reg [15:0] scales_ram [0:GROUPS-1];
      reg [3:0] read_zero;
      reg [15:0] read_scale;
      reg [2:0] scale_owner_line;
      reg [4:0] scale_owner_half;
      wire [9:0] half_offset={5'd0,span_start[5:1]}+10'(b);
      wire [3:0] row_offset={1'b0,row_base[2:0]}+4'(b&7);
      wire [31:0] selected_word=row_offset[3] ?
        source_word[(b>>3)+1] : source_word[b>>3];
      wire [4:0] source_bit=anvil_q3_pkg::awq_lane_shift(row_offset[2:0]);
      localparam LOCAL_BIT=(b>>3)*32+
        ((b&7)==0 ? 0 : (b&7)==1 ? 16 : (b&7)==2 ? 4 :
         (b&7)==3 ? 20 : (b&7)==4 ? 8 : (b&7)==5 ? 24 :
         (b&7)==6 ? 12 : 28);
      wire [15:0] captured_scale=memory_rsp_rdata[{scale_owner_half,4'd0}+:16];
      wire this_scale=scale_capture && b<rows && line_index==scale_owner_line;
      reg invalid_scale;
      always @* begin
        invalid_scale=captured_scale[14:10]==31 ||
          (captured_scale[15] && captured_scale[14:0]!=0);
`ifndef SYNTHESIS
        if ((^captured_scale)===1'bx) invalid_scale=1;
`endif
      end
      assign scale_bad[b]=this_scale && invalid_scale;
      assign zero_q[LOCAL_BIT+:4]=read_zero;
      assign scale_q[b*16+:16]=read_scale;
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin scale_owner_line<=0; scale_owner_half<=0; end
        else if (flush) begin scale_owner_line<=0; scale_owner_half<=0; end
        else if (state==NEXT_GROUP && scales && !fault_now) begin
          scale_owner_line<=half_offset[7:5];
          scale_owner_half<=half_offset[4:0];
        end
      end
      always @(posedge clk) begin
        if (zero_save)
          zeros[GA'(group_index)]<=b<rows ? selected_word[source_bit+:4] : 4'd0;
        if (this_scale && !fault_now)
          scales_ram[GA'(group_index)]<=captured_scale;
        if (running && state==GROUP_LINES && scales && b>=rows && !fault_now)
          scales_ram[GA'(group_index)]<=16'd0;
        if (ram_read) begin
          read_zero<=zeros[query_group];
          read_scale<=scales_ram[query_group];
        end
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; failed<=0; cancelled<=0; outstanding<=0;
        scales<=0; loaded_pulse<=0; drain_pulse<=0;
        inputs<=0; outputs<=0; row_base<=0; rows<=0; groups<=0; group_index<=0;
        zero_words<=0; zero_stride<=0; line_index<=0; last_line<=0; physical_count<=0;
        zero_base<=0; scale_base<=0; request_address<=0;
        zero_bytes<=0; scale_bytes<=0; zero_allocation<=0; scale_allocation<=0;
        zero_end<=0; scale_end<=0; group_product<=0; span_start<=0; span_bytes<=0;
        command_bad<=0; query_bad<=0; query_group<=0;
      end else begin
        loaded_pulse<=0; drain_pulse<=0;
        if (request_fire && !memory_rsp_valid) outstanding<=1;
        if (memory_rsp_valid && response_known) outstanding<=0;
        if (request_fire) physical_count<=physical_count+1'b1;
        if (flush) begin
          state<=DRAIN; failed<=0; cancelled<=1;
          scales<=0; inputs<=0; outputs<=0; row_base<=0; rows<=0;
          groups<=0; group_index<=0; zero_words<=0; zero_stride<=0;
          line_index<=0; last_line<=0; physical_count<=0;
          zero_base<=0; scale_base<=0; request_address<=0;
          zero_bytes<=0; scale_bytes<=0; zero_allocation<=0; scale_allocation<=0;
          zero_end<=0; scale_end<=0; group_product<=0; span_start<=0; span_bytes<=0;
          command_bad<=0; query_bad<=0; query_group<=0;
        end else if (fault_now) begin
          failed<=1; cancelled<=0; state<=DRAIN;
        end else begin
          case (state)
            IDLE,READY: begin
              if (cmd_valid && cmd_ready) begin
                inputs<=cmd_inputs; outputs<=cmd_outputs; row_base<=cmd_row_base;
                rows<=command_rows;
                groups<=({32'd0,cmd_inputs}+GROUP_SIZE-1)>>GSHIFT;
                zero_words<=(command_last>>3)-({32'd0,cmd_row_base}>>3)+1;
                zero_stride<=command_zero_stride[31:0];
                zero_base<=cmd_qzeros_base; scale_base<=cmd_scales_base;
                zero_bytes<=(({32'd0,cmd_inputs}+GROUP_SIZE-1)>>GSHIFT) *
                  command_zero_stride;
                scale_bytes<=(({32'd0,cmd_inputs}+GROUP_SIZE-1)>>GSHIFT) *
                  ({32'd0,cmd_outputs}<<1);
                command_bad<=cmd_inputs==0 || cmd_inputs>MAX_INPUTS ||
                  cmd_outputs==0 ||
                  cmd_row_base>=cmd_outputs ||
                  cmd_qzeros_base[5:0]!=0 || cmd_scales_base[5:0]!=0 ||
                  cmd_qzeros_base<33'h060000000 ||
                  cmd_scales_base<33'h064000000;
`ifndef SYNTHESIS
                if ((^{cmd_inputs,cmd_outputs,cmd_row_base,
                        cmd_qzeros_base,cmd_scales_base})===1'bx) command_bad<=1;
`endif
                scales<=0; group_index<=0; physical_count<=0;
                cancelled<=0; query_bad<=0; state<=EXTENT_ROUND;
              end else if (query_fire) begin
                query_group<=GA'(query_column>>GSHIFT);
                query_bad<=query_column>=inputs;
`ifndef SYNTHESIS
                if ((^query_column)===1'bx) query_bad<=1;
`endif
                state<=QUERY_READ;
              end
            end
            EXTENT_ROUND: begin
              zero_allocation<=rounded_zero; scale_allocation<=rounded_scale;
              state<=EXTENT_END;
            end
            EXTENT_END: begin
              zero_end<={31'd0,zero_base}+zero_allocation;
              scale_end<={31'd0,scale_base}+scale_allocation;
              state<=EXTENT_CHECK;
            end
            EXTENT_CHECK: begin
              if (command_bad || zero_end<=zero_base || scale_end<=scale_base ||
                  zero_end>64'h64000000 || scale_end>64'h6c000000) begin
                failed<=1; state<=DRAIN;
              end else state<=GROUP_PRODUCT;
            end
            GROUP_PRODUCT: begin
              group_product<={32'd0,group_index} *
                (scales ? ({32'd0,outputs}<<1) : {32'd0,zero_stride});
              state<=GROUP_START;
            end
            GROUP_START: begin
              span_start<=group_product+
                (scales ? {31'd0,scale_base} : {31'd0,zero_base});
              state<=GROUP_LINES;
            end
            GROUP_LINES: begin
              // Row offsets are added separately from the group stride product.
              span_start<=span_start+
                (scales ? ({32'd0,row_base}<<1) : ({32'd0,(row_base>>3)}<<2));
              span_bytes<=scales ? 9'(rows<<1) : 9'(zero_words<<2);
              state<=NEXT_GROUP;
            end
            NEXT_GROUP: begin
              if (bad_lines) begin failed<=1; state<=DRAIN; end
              else begin
                request_address<=aligned_start[32:0];
                line_index<=0; last_line<=32'((span_end_offset-1)>>6);
                state<=REQUEST;
              end
            end
            REQUEST: if (request_fire) begin
              if (!response_fire) state<=RETURN;
              else if (line_index!=last_line) begin
                line_index<=line_index+1'b1; request_address<=request_address+33'd64;
              end else if (!scales) state<=ZERO_SAVE;
              else if (group_index+1'b1==groups) begin
                loaded_pulse<=1; state<=READY;
              end else begin
                group_index<=group_index+1'b1; scales<=0; state<=GROUP_PRODUCT;
              end
            end
            RETURN: if (response_fire) begin
              if (line_index!=last_line) begin
                line_index<=line_index+1'b1; request_address<=request_address+33'd64;
                state<=REQUEST;
              end else if (!scales) state<=ZERO_SAVE;
              else if (group_index+1'b1==groups) begin
                loaded_pulse<=1; state<=READY;
              end else begin
                group_index<=group_index+1'b1; scales<=0; state<=GROUP_PRODUCT;
              end
            end
            ZERO_SAVE: begin scales<=1; state<=GROUP_PRODUCT; end
            QUERY_READ: state<=RESPONSE;
            RESPONSE: if (operand_valid && operand_ready) begin
              if (query_bad) begin failed<=1; state<=DRAIN; end
              else state<=READY;
            end
            DRAIN: if (!outstanding) begin
              if (cancelled) begin state<=IDLE; drain_pulse<=1; end
              else state<=FAULTED;
            end
            FAULTED: state<=FAULTED;
            default: begin failed<=1; state<=DRAIN; end
          endcase
        end
      end
    end
  end endgenerate
endmodule
