module anvil_q4_gemv #(
  parameter integer TILE_K=128, TILE_ROWS=8,
  localparam integer SK=(TILE_K>=1 && TILE_K<=128) ? TILE_K : 1,
  localparam integer SR=(TILE_ROWS>=1 && TILE_ROWS<=8) ? TILE_ROWS : 1
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer,
  input wire [2:0] cmd_proj,
  input wire cmd_lmhead,
  input wire [31:0] hidden, intermediate, kv_heads, head_dim, vocabulary, group_size,
  input wire activation_format, activation_a8, weight_asymmetric, qkv_bias,
  input wire [1:0] weight_format,
  output wire done, error,
  output wire result_valid,
  input wire result_ready,
  output wire [31:0] result_index, result_data,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire mem_req_write,
  output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer,
  output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata, mem_req_stride,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata,
  input wire mem_rsp_error
);
  generate if (TILE_K!=SK || TILE_ROWS!=SR) begin : invalid_parameters
    initial $fatal(1,"PARAMETER ERROR: anvil_q4_gemv tiles");
    assign cmd_ready=0; assign done=0; assign error=0; assign result_valid=0;
    assign result_index=0; assign result_data=0;
    assign mem_req_valid=0; assign mem_req_write=0; assign mem_req_kind=0;
    assign mem_req_layer=0; assign mem_req_proj=0; assign mem_req_row=0;
    assign mem_req_col=0; assign mem_req_wdata=0; assign mem_req_stride=0;
    assign mem_rsp_ready=0;
  end else begin : legal
    localparam [5:0] IDLE=0, PREPARE=1, GROUP_COUNT=2, TILE_CMD=3,
      LOAD_READ=4, LOAD_WAIT=5, LOAD_SEND=6, WEIGHT_READ=7, WEIGHT_WAIT=8,
      SCALE_READ=9, SCALE_WAIT=10, ZERO_READ=11, ZERO_WAIT=12,
      NEXT_LANE=13, WEIGHT_SEND=14, TILE_WAIT=15, POST_LANE=16,
      BIAS_READ=17, BIAS_WAIT=18, WIDEN_ISSUE=19, WIDEN_WAIT=20,
      BIAS_ADD=21, BIAS_ADD_WAIT=22, STORE=23, STORE_WAIT=24,
      EMIT=25, ADVANCE_ROW=26, COMPLETE=27;
    reg [5:0] state;
    reg [31:0] layer, h, inter, kd, vocab, group_length, scratch_stride;
    reg [31:0] input_extent, output_extent, source_slot, target_slot;
    reg [31:0] group_stride, count_remaining, payload_stride;
    reg [31:0] row_base, tile_base, tile_length, load_index, input_index;
    reg [31:0] tile_index, group_index, group_offset, row_lane;
    reg [31:0] load_data, value_register, bias_operand;
    reg [2:0] projection;
    reg lmhead, native_fp16, a8, asymmetric, bias_enable, failed;
    reg [1:0] format;
    reg [SR*32-1:0] sums, payloads, scales, zeros;
    reg [SR*3-1:0] lanes;
    wire [16:0] configured_kd=kv_heads[7:0]*head_dim[8:0];
    wire [SR-1:0] next_mask;
    for (genvar n=0;n<SR;n=n+1) begin : masks
      assign next_mask[n]=row_base+32'(n)<output_extent;
    end
    wire [31:0] packed_col=format==1 ? input_index>>3 :
      format==2 ? input_index>>2 : input_index;
    wire port_idle, complete, fault;
    wire [31:0] rdata;
    wire payload_read=state==WEIGHT_READ;
    wire metadata_read=state==SCALE_READ || state==ZERO_READ;
    wire bias_read=state==BIAS_READ;
    wire load_read=state==LOAD_READ;
    wire writing=state==STORE;
    wire issue=(payload_read || metadata_read || bias_read || load_read || writing) && port_idle;
    wire [3:0] request_kind=payload_read ? (lmhead ? 4'd0 : 4'd1) :
      state==SCALE_READ ? 4'd3 : state==ZERO_READ ? 4'd2 : bias_read ? 4'd4 : 4'd8;
    wire [31:0] request_col=load_read ? tile_base+load_index :
      writing || bias_read ? row_base+row_lane :
      metadata_read ? group_index : packed_col;
    wire [31:0] request_row=load_read ? source_slot :
      writing ? target_slot : bias_read ? 32'd0 : row_base+row_lane;
    wire [31:0] request_stride=load_read || writing ? scratch_stride :
      bias_read ? output_extent : metadata_read ? group_stride : payload_stride;
    anvil_q4_mem_port memory_port (
      .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
      .idle(port_idle),.complete(complete),.fault(fault),
      .write(writing),.kind(request_kind),
      .layer(load_read || writing || lmhead ? 32'd0 : layer),
      .proj(load_read || writing ? 3'd0 : lmhead ? 3'd1 : projection),
      .row(request_row),.col(request_col),.wdata(writing ? value_register : 32'd0),
      .stride(request_stride),.rdata(rdata),
      .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
      .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
      .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
      .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
      .mem_req_stride(mem_req_stride),.mem_rsp_valid(mem_rsp_valid),
      .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
    );
    wire array_ready, array_activation_ready, array_weights_ready, array_valid, array_error;
    wire [SR*32-1:0] array_result;
    wire [4:0] array_flags;
    anvil_q4_tensor_array #(.LANES(SR),.TILE_K(SK)) tensor_array (
      .clk(clk),.rst_n(rst_n),.flush(flush),
      .cmd_valid(state==TILE_CMD),.cmd_ready(array_ready),
      .cmd_length(tile_length),.cmd_mask(next_mask),.cmd_accumulators(sums),
      .cmd_a8(a8),.cmd_activation_format(native_fp16),.cmd_asymmetric(asymmetric),
      .cmd_weight_format(format),.activation_valid(state==LOAD_SEND),
      .activation_ready(array_activation_ready),.activation_data(load_data),
      .weights_valid(state==WEIGHT_SEND),.weights_ready(array_weights_ready),
      .weight_payload(payloads),.weight_zero(zeros),.weight_scale(scales),.weight_lane(lanes),
      .out_valid(array_valid),.out_ready(state==TILE_WAIT),
      .result(array_result),.flags(array_flags),.error(array_error)
    );
    wire fp_ready, fp_valid;
    wire [31:0] fp_result;
    wire [4:0] fp_flags;
    anvil_q4_fp32 arithmetic (
      .clk(clk),.rst_n(rst_n),.flush(flush),
      .in_valid(state==WIDEN_ISSUE || state==BIAS_ADD),.in_ready(fp_ready),
      .op(state==BIAS_ADD ? 4'd0 : native_fp16 ? 4'd6 : 4'd5),
      .a(state==BIAS_ADD ? sums[row_lane*32+:32] : bias_operand),
      .b(bias_operand),.out_valid(fp_valid),
      .out_ready(state==WIDEN_WAIT || state==BIAS_ADD_WAIT),
      .result(fp_result),.flags(fp_flags)
    );
    assign cmd_ready=rst_n && !flush && state==IDLE;
    assign done=rst_n && !flush && state==COMPLETE;
    assign error=done && failed;
    assign result_valid=rst_n && !flush && state==EMIT;
    assign result_index=result_valid ? row_base+row_lane : 32'd0;
    assign result_data=result_valid ? value_register : 32'd0;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; layer<=0; h<=0; inter<=0; kd<=0; vocab<=0;
        group_length<=0; scratch_stride<=0; input_extent<=0; output_extent<=0;
        source_slot<=0; target_slot<=0; group_stride<=0; count_remaining<=0;
        payload_stride<=0; row_base<=0; tile_base<=0; tile_length<=0;
        load_index<=0; input_index<=0; tile_index<=0; group_index<=0;
        group_offset<=0; row_lane<=0; load_data<=0; value_register<=0;
        bias_operand<=0; projection<=0; lmhead<=0; native_fp16<=0;
        a8<=0; asymmetric<=0; bias_enable<=0; failed<=0; format<=0;
        sums<=0; payloads<=0; scales<=0; zeros<=0; lanes<=0;
      end else if (flush) begin state<=IDLE; failed<=0; value_register<=0; end
      else if (fault) begin failed<=1; state<=COMPLETE; end
      else case (state)
        IDLE: if (cmd_valid) begin
          layer<=cmd_layer; h<=hidden; inter<=intermediate; kd<={15'd0,configured_kd};
          vocab<=vocabulary; group_length<=group_size;
          scratch_stride<=hidden>intermediate ? hidden : intermediate;
          projection<=cmd_proj; lmhead<=cmd_lmhead; native_fp16<=activation_format;
          format<=cmd_lmhead ? 2'd0 : weight_format;
          a8<=!cmd_lmhead && activation_a8;
          asymmetric<=!cmd_lmhead && weight_asymmetric;
          bias_enable<=!cmd_lmhead && qkv_bias && cmd_proj<3;
          failed<=0; row_base<=0; tile_base<=0; input_index<=0;
          group_index<=0; group_offset<=0; sums<=0;
          if (hidden<2 || hidden>8192 || intermediate<1 || intermediate>32768 ||
              kv_heads==0 || kv_heads>128 || head_dim<2 || head_dim>256 ||
              configured_kd>32768 || group_size==0 || group_size>128 ||
              vocabulary==0 || vocabulary>262144 || cmd_proj>6 ||
              weight_format>2 || (activation_a8 && weight_format==0)) begin
            failed<=1; state<=COMPLETE;
          end else state<=PREPARE;
        end
        PREPARE: begin
          input_extent<=!lmhead && projection==6 ? inter : h;
          count_remaining<=!lmhead && projection==6 ? inter : h;
          group_stride<=0;
          output_extent<=lmhead ? vocab : projection==1 || projection==2 ? kd :
            projection==4 || projection==5 ? inter : h;
          source_slot<=lmhead ? 32'd14 : projection==3 ? 32'd5 :
            projection==6 ? 32'd11 : projection==4 || projection==5 ? 32'd8 : 32'd1;
          target_slot<=projection==0 ? 32'd2 : projection==1 ? 32'd3 :
            projection==2 ? 32'd4 : projection==3 ? 32'd6 :
            projection==4 ? 32'd9 : projection==5 ? 32'd10 : 32'd12;
          state<=GROUP_COUNT;
        end
        GROUP_COUNT: begin
          if (count_remaining>group_length) begin
            count_remaining<=count_remaining-group_length;
            group_stride<=group_stride+1'b1;
          end else begin
            group_stride<=group_stride+1'b1;
            payload_stride<=format==1 ? (input_extent+7)>>3 :
              format==2 ? (input_extent+3)>>2 : input_extent;
            tile_length<=input_extent<SK ? input_extent : 32'(SK);
            load_index<=0; state<=TILE_CMD;
          end
        end
        TILE_CMD: if (array_ready) state<=LOAD_READ;
        LOAD_READ: if (issue) state<=LOAD_WAIT;
        LOAD_WAIT: if (complete) begin load_data<=rdata; state<=LOAD_SEND; end
        LOAD_SEND: if (array_activation_ready) begin
          if (load_index+1<tile_length) begin load_index<=load_index+1'b1; state<=LOAD_READ; end
          else begin
            tile_index<=0; row_lane<=0; payloads<=0; scales<=0; zeros<=0; lanes<=0;
            state<=WEIGHT_READ;
          end
        end
        WEIGHT_READ: if (issue) state<=WEIGHT_WAIT;
        WEIGHT_WAIT: if (complete) begin
          payloads[row_lane*32+:32]<=rdata;
          lanes[row_lane*3+:3]<=format==1 ? input_index[2:0] :
            format==2 ? {1'b0,input_index[1:0]} : 3'd0;
          if (format==0) state<=NEXT_LANE;
          else state<=SCALE_READ;
        end
        SCALE_READ: if (issue) state<=SCALE_WAIT;
        SCALE_WAIT: if (complete) begin
          scales[row_lane*32+:32]<=rdata;
          if (asymmetric) state<=ZERO_READ;
          else state<=NEXT_LANE;
        end
        ZERO_READ: if (issue) state<=ZERO_WAIT;
        ZERO_WAIT: if (complete) begin zeros[row_lane*32+:32]<=rdata; state<=NEXT_LANE; end
        NEXT_LANE: begin
          if (row_lane+1<SR && row_base+row_lane+1<output_extent) begin
            row_lane<=row_lane+1'b1; state<=WEIGHT_READ;
          end else state<=WEIGHT_SEND;
        end
        WEIGHT_SEND: if (array_weights_ready) begin
          input_index<=input_index+1'b1;
          if (group_offset+1<group_length) group_offset<=group_offset+1'b1;
          else begin group_offset<=0; group_index<=group_index+1'b1; end
          if (tile_index+1<tile_length) begin
            tile_index<=tile_index+1'b1; row_lane<=0; state<=WEIGHT_READ;
          end else state<=TILE_WAIT;
        end
        TILE_WAIT: if (array_valid) begin
          sums<=array_result;
          if (array_error) begin failed<=1; state<=COMPLETE; end
          else if (tile_base+tile_length<input_extent) begin
            tile_base<=tile_base+tile_length;
            tile_length<=input_extent-tile_base-tile_length<SK ?
              input_extent-tile_base-tile_length : 32'(SK);
            load_index<=0; state<=TILE_CMD;
          end else begin row_lane<=0; state<=POST_LANE; end
        end
        POST_LANE: begin
          value_register<=sums[row_lane*32+:32];
          if (bias_enable) state<=BIAS_READ;
          else if (lmhead) state<=EMIT;
          else state<=STORE;
        end
        BIAS_READ: if (issue) state<=BIAS_WAIT;
        BIAS_WAIT: if (complete) begin
          if (rdata[31:16]!=0) begin failed<=1; state<=COMPLETE; end
          else begin bias_operand<=rdata; state<=WIDEN_ISSUE; end
        end
        WIDEN_ISSUE: if (fp_ready) state<=WIDEN_WAIT;
        WIDEN_WAIT: if (fp_valid) begin bias_operand<=fp_result; state<=BIAS_ADD; end
        BIAS_ADD: if (fp_ready) state<=BIAS_ADD_WAIT;
        BIAS_ADD_WAIT: if (fp_valid) begin value_register<=fp_result; state<=STORE; end
        STORE: if (issue) state<=STORE_WAIT;
        STORE_WAIT: if (complete) state<=ADVANCE_ROW;
        EMIT: if (result_ready) state<=ADVANCE_ROW;
        ADVANCE_ROW: begin
          if (row_lane+1<SR && row_base+row_lane+1<output_extent) begin
            row_lane<=row_lane+1'b1; state<=POST_LANE;
          end else if (row_base+SR<output_extent) begin
            row_base<=row_base+32'(SR); tile_base<=0; input_index<=0;
            group_index<=0; group_offset<=0; sums<=0; load_index<=0;
            tile_length<=input_extent<SK ? input_extent : 32'(SK);
            state<=TILE_CMD;
          end else state<=COMPLETE;
        end
        COMPLETE: state<=IDLE;
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end endgenerate
endmodule
