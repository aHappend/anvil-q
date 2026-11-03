module anvil_q4_fp_gemv #(
  parameter integer TILE_K=128, TILE_ROWS=16,
  localparam integer SK=(TILE_K>=1 && TILE_K<=128) ? TILE_K : 1,
  localparam integer SR=(TILE_ROWS>=1 && TILE_ROWS<=16) ? TILE_ROWS : 1
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
  output wire [16:0] mem_req_valid,
  input wire [16:0] mem_req_ready,
  output wire [16:0] mem_req_write,
  output wire [67:0] mem_req_kind,
  output wire [543:0] mem_req_layer,
  output wire [50:0] mem_req_proj,
  output wire [543:0] mem_req_row, mem_req_col, mem_req_wdata, mem_req_stride,
  input wire [16:0] mem_rsp_valid,
  output wire [16:0] mem_rsp_ready,
  input wire [543:0] mem_rsp_rdata,
  input wire [16:0] mem_rsp_error
);
  generate if (TILE_K!=SK || TILE_ROWS!=SR) begin : invalid_parameters
    initial $fatal(1,"PARAMETER ERROR: anvil_q4_fp_gemv tiles");
    assign cmd_ready=0; assign done=0; assign error=0; assign result_valid=0;
    assign result_index=0; assign result_data=0;
    assign mem_req_valid=0; assign mem_req_write=0; assign mem_req_kind=0;
    assign mem_req_layer=0; assign mem_req_proj=0; assign mem_req_row=0;
    assign mem_req_col=0; assign mem_req_wdata=0; assign mem_req_stride=0;
    assign mem_rsp_ready=0;
  end else begin : legal
    localparam [4:0] IDLE=0, PREPARE=1, TILE_CMD=2,
      LOAD_READ=3, LOAD_WAIT=4, NARROW=5, NARROW_WAIT=6, LOAD_SEND=7,
      WEIGHT_START=8, WEIGHT_COLLECT=9, WEIGHT_SEND=10, TILE_WAIT=11,
      POST_LANE=12, BIAS_READ=13, BIAS_WAIT=14, WIDEN=15, WIDEN_WAIT=16,
      BIAS_ADD=17, BIAS_ADD_WAIT=18, STORE=19, STORE_WAIT=20,
      EMIT=21, ADVANCE_ROW=22, COMPLETE=23;
    reg [4:0] state;
    reg [31:0] layer, h, inter, kd, vocab, scratch_stride;
    reg [31:0] input_extent, output_extent, source_slot, target_slot;
    reg [31:0] row_base, tile_base, tile_length, load_index, tile_index, row_lane;
    reg [31:0] load_data, value_register, bias_operand;
    reg [15:0] narrow_activation;
    reg [2:0] projection;
    reg lmhead, native_fp16, bias_enable, failed;
    reg [32*SR-1:0] sums;
    reg [255:0] payloads;
    reg [15:0] pending, awaiting, returned, lane_fault;
    wire [63:0] configured_kd={32'd0,kv_heads}*{32'd0,head_dim};
    wire [15:0] active_mask;
    for (genvar n=0;n<16;n=n+1) begin : masks
      assign active_mask[n]=n<SR && row_base+32'(n)<output_extent;
    end

    wire port_idle, complete, fault;
    wire [31:0] rdata;
    wire load_read=state==LOAD_READ;
    wire bias_read=state==BIAS_READ;
    wire writing=state==STORE;
    wire issue=(load_read || bias_read || writing) && port_idle;
    anvil_q4_fp_mem_port memory_port (
      .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
      .idle(port_idle),.complete(complete),.fault(fault),
      .write(writing),.kind(bias_read ? 4'd4 : 4'd8),
      .layer(bias_read ? layer : 32'd0),.proj(bias_read ? projection : 3'd0),
      .row(load_read ? source_slot : writing ? target_slot : 32'd0),
      .col(load_read ? tile_base+load_index : row_base+row_lane),
      .wdata(writing ? value_register : 32'd0),
      .stride(bias_read ? output_extent : scratch_stride),.rdata(rdata),
      .mem_req_valid(mem_req_valid[16]),.mem_req_ready(mem_req_ready[16]),
      .mem_req_write(mem_req_write[16]),.mem_req_kind(mem_req_kind[64+:4]),
      .mem_req_layer(mem_req_layer[512+:32]),.mem_req_proj(mem_req_proj[48+:3]),
      .mem_req_row(mem_req_row[512+:32]),.mem_req_col(mem_req_col[512+:32]),
      .mem_req_wdata(mem_req_wdata[512+:32]),.mem_req_stride(mem_req_stride[512+:32]),
      .mem_rsp_valid(mem_rsp_valid[16]),.mem_rsp_ready(mem_rsp_ready[16]),
      .mem_rsp_rdata(mem_rsp_rdata[512+:32]),.mem_rsp_error(mem_rsp_error[16])
    );

    for (genvar n=0;n<16;n=n+1) begin : weight_channels
      assign mem_req_valid[n]=rst_n && !flush && state==WEIGHT_COLLECT && pending[n];
      assign mem_req_write[n]=1'b0;
      assign mem_req_kind[n*4+:4]=mem_req_valid[n] ? (lmhead ? 4'd0 : 4'd1) : 4'd0;
      assign mem_req_layer[n*32+:32]=mem_req_valid[n] && !lmhead ? layer : 32'd0;
      assign mem_req_proj[n*3+:3]=mem_req_valid[n] ? (lmhead ? 3'd1 : projection) : 3'd0;
      assign mem_req_row[n*32+:32]=mem_req_valid[n] ? row_base+32'(n) : 32'd0;
      assign mem_req_col[n*32+:32]=mem_req_valid[n] ? tile_base+tile_index : 32'd0;
      assign mem_req_wdata[n*32+:32]=32'd0;
      assign mem_req_stride[n*32+:32]=mem_req_valid[n] ? input_extent : 32'd0;
      assign mem_rsp_ready[n]=rst_n && !flush && state==WEIGHT_COLLECT && awaiting[n];
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          pending[n]<=0; awaiting[n]<=0; returned[n]<=0; lane_fault[n]<=0;
          payloads[n*16+:16]<=0;
        end else if (flush) begin
          pending[n]<=0; awaiting[n]<=0; returned[n]<=0; lane_fault[n]<=0;
          payloads[n*16+:16]<=0;
        end else if (state==WEIGHT_START) begin
          pending[n]<=active_mask[n]; awaiting[n]<=0; returned[n]<=0; lane_fault[n]<=0;
        end else if (state==WEIGHT_COLLECT) begin
          if (mem_req_valid[n] && mem_req_ready[n]) begin
            pending[n]<=0; awaiting[n]<=1;
          end
          if (mem_rsp_valid[n] && mem_rsp_ready[n]) begin
            awaiting[n]<=0; returned[n]<=1;
            payloads[n*16+:16]<=mem_rsp_rdata[n*32+:16];
            lane_fault[n]<=mem_rsp_error[n] || mem_rsp_rdata[n*32+16+:16]!=0;
          end
        end
      end
    end

    wire array_ready, array_activation_ready, array_weights_ready, array_valid, array_error;
    wire [32*SR-1:0] array_result;
    wire [4:0] array_flags;
    anvil_q4_fp_tensor_array #(.LANES(SR),.TILE_K(SK)) tensor_array (
      .clk(clk),.rst_n(rst_n),.flush(flush),
      .cmd_valid(state==TILE_CMD),.cmd_ready(array_ready),
      .cmd_length(tile_length),.cmd_mask(active_mask[SR-1:0]),.cmd_accumulators(sums),
      .cmd_activation_format(native_fp16),.activation_valid(state==LOAD_SEND),
      .activation_ready(array_activation_ready),.activation_data(narrow_activation),
      .weights_valid(state==WEIGHT_SEND),.weights_ready(array_weights_ready),
      .weight_payload(payloads[16*SR-1:0]),
      .out_valid(array_valid),.out_ready(state==TILE_WAIT),
      .result(array_result),.flags(array_flags),.error(array_error)
    );
    wire fp_ready, fp_valid;
    wire [31:0] fp_result;
    wire [4:0] fp_flags;
    anvil_q4_fp32 arithmetic (
      .clk(clk),.rst_n(rst_n),.flush(flush),
      .in_valid(state==NARROW || state==WIDEN || state==BIAS_ADD),.in_ready(fp_ready),
      .op(state==NARROW ? (native_fp16 ? 4'd8 : 4'd7) :
        state==WIDEN ? (native_fp16 ? 4'd6 : 4'd5) : 4'd0),
      .a(state==NARROW ? load_data : state==WIDEN ? bias_operand : sums[row_lane*32+:32]),
      .b(state==BIAS_ADD ? bias_operand : 32'd0),
      .out_valid(fp_valid),.out_ready(state==NARROW_WAIT || state==WIDEN_WAIT ||
        state==BIAS_ADD_WAIT),.result(fp_result),.flags(fp_flags)
    );
    assign cmd_ready=rst_n && !flush && state==IDLE;
    assign done=rst_n && !flush && state==COMPLETE;
    assign error=done && failed;
    assign result_valid=rst_n && !flush && state==EMIT;
    assign result_index=result_valid ? row_base+row_lane : 32'd0;
    assign result_data=result_valid ? value_register : 32'd0;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; layer<=0; h<=0; inter<=0; kd<=0; vocab<=0; scratch_stride<=0;
        input_extent<=0; output_extent<=0; source_slot<=0; target_slot<=0;
        row_base<=0; tile_base<=0; tile_length<=0; load_index<=0; tile_index<=0;
        row_lane<=0; load_data<=0; value_register<=0; bias_operand<=0;
        narrow_activation<=0; projection<=0; lmhead<=0; native_fp16<=0;
        bias_enable<=0; failed<=0; sums<=0;
      end else if (flush) begin
        state<=IDLE; failed<=0; value_register<=0; sums<=0;
      end else if (fault) begin failed<=1; state<=COMPLETE; end
      else case (state)
        IDLE: if (cmd_valid) begin
          layer<=cmd_layer; h<=hidden; inter<=intermediate; kd<=configured_kd[31:0];
          vocab<=vocabulary; scratch_stride<=hidden>intermediate ? hidden : intermediate;
          projection<=cmd_proj; lmhead<=cmd_lmhead; native_fp16<=activation_format;
          bias_enable<=!cmd_lmhead && qkv_bias && cmd_proj<3;
          failed<=0; row_base<=0; tile_base<=0; load_index<=0; sums<=0;
          if (hidden<2 || hidden>8192 || intermediate<1 || intermediate>32768 ||
              kv_heads==0 || kv_heads>128 || head_dim<2 || head_dim>256 ||
              head_dim[0] || configured_kd>32768 ||
              vocabulary==0 || vocabulary>262144 || cmd_proj>6 ||
              group_size!=1 || weight_format!=0 || activation_a8 || weight_asymmetric) begin
            failed<=1; state<=COMPLETE;
          end else state<=PREPARE;
        end
        PREPARE: begin
          input_extent<=!lmhead && projection==6 ? inter : h;
          tile_length<=!lmhead && projection==6 ?
            (inter<SK ? inter : 32'(SK)) : (h<SK ? h : 32'(SK));
          output_extent<=lmhead ? vocab : projection==1 || projection==2 ? kd :
            projection==4 || projection==5 ? inter : h;
          source_slot<=lmhead ? 32'd14 : projection==3 ? 32'd5 :
            projection==6 ? 32'd11 : projection==4 || projection==5 ? 32'd8 : 32'd1;
          target_slot<=projection==0 ? 32'd2 : projection==1 ? 32'd3 :
            projection==2 ? 32'd4 : projection==3 ? 32'd6 :
            projection==4 ? 32'd9 : projection==5 ? 32'd10 : 32'd12;
          state<=TILE_CMD;
        end
        TILE_CMD: if (array_ready) state<=LOAD_READ;
        LOAD_READ: if (issue) state<=LOAD_WAIT;
        LOAD_WAIT: if (complete) begin load_data<=rdata; state<=NARROW; end
        NARROW: if (fp_ready) state<=NARROW_WAIT;
        NARROW_WAIT: if (fp_valid) begin narrow_activation<=fp_result[15:0]; state<=LOAD_SEND; end
        LOAD_SEND: if (array_activation_ready) begin
          if (load_index+1<tile_length) begin load_index<=load_index+1'b1; state<=LOAD_READ; end
          else begin tile_index<=0; state<=WEIGHT_START; end
        end
        WEIGHT_START: state<=WEIGHT_COLLECT;
        WEIGHT_COLLECT: if (&(returned | ~active_mask)) begin
          if (|(lane_fault & active_mask)) begin failed<=1; state<=COMPLETE; end
          else state<=WEIGHT_SEND;
        end
        WEIGHT_SEND: if (array_weights_ready) begin
          if (tile_index+1<tile_length) begin
            tile_index<=tile_index+1'b1; state<=WEIGHT_START;
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
          else begin bias_operand<=rdata; state<=WIDEN; end
        end
        WIDEN: if (fp_ready) state<=WIDEN_WAIT;
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
            row_base<=row_base+32'(SR); tile_base<=0; sums<=0; load_index<=0;
            tile_length<=input_extent<SK ? input_extent : 32'(SK); state<=TILE_CMD;
          end else state<=COMPLETE;
        end
        COMPLETE: state<=IDLE;
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end endgenerate
endmodule
