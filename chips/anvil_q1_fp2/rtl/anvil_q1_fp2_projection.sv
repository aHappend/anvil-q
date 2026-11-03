module anvil_q1_fp2_projection #(
  parameter MAX_INPUT=4864, MAX_OUTPUT=151936
) (
  input wire clk, rst_n, cmd_valid,
  output wire cmd_ready,
  input wire cmd_format_mx, cmd_head,
  input wire [31:0] cmd_layer, cmd_inputs, cmd_outputs,
  input wire [2:0] cmd_proj,
  input wire in_valid,
  output wire in_ready,
  input wire [31:0] in_data,
  input wire in_last,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_data, out_index,
  output wire out_last, done, error,
  output wire [4:0] status,
  output wire ulp_valid,
  output wire [31:0] ulp_distance,
  output wire tensor_valid,
  input wire tensor_ready,
  output wire [1023:0] tensor_a, tensor_b,
  output wire [63:0] tensor_mask,
  output wire [31:0] tensor_acc,
  input wire tensor_result_valid,
  input wire [31:0] tensor_result,
  input wire [4:0] tensor_status,
  output wire fetch_valid,
  input wire fetch_ready,
  output wire fetch_scale,
  output wire [3:0] fetch_kind,
  output wire [31:0] fetch_layer,
  output wire [2:0] fetch_proj,
  output wire [31:0] fetch_row, fetch_col, fetch_tag,
  input wire response_valid,
  output wire response_ready,
  input wire [31:0] response_tag,
  input wire response_write, response_error,
  input wire [511:0] response_data,
  output wire work_active, result_needed,
  output wire bias_req_valid,
  input wire bias_req_ready,
  output wire [31:0] bias_layer, bias_col,
  output wire [2:0] bias_proj,
  input wire bias_rsp_valid,
  output wire bias_rsp_ready,
  input wire [31:0] bias_rsp_data,
  input wire bias_rsp_error
);
  localparam GROUPS=(MAX_INPUT+63)/64;
  localparam GB=GROUPS>1 ? $clog2(GROUPS) : 1;
  localparam IDLE=0, COLLECT=1, QUANTIZE=2, QUANT_WAIT=3, STORE=4;
  localparam CLEAR=5, ACT_READ=6, ACT_LATCH=7, WEIGHT_CMD=8, WEIGHT_LOAD=9;
  localparam WEIGHT_WAIT=10, DOT_READ=11, DOT_LATCH=12, DOT_SEND=13;
  localparam DOT_WAIT=14, RESULT_READ=15, RESULT_LATCH=16, BIAS_REQ=17;
  localparam BIAS_RSP=18, BIAS_ADD=19, BIAS_WAIT=20, OUTPUT=21;
  localparam COMPLETE_WAIT=22, ERROR_WAIT0=23, ERROR_WAIT1=24, FINISH=25;
  reg [4:0] state;
  reg format_mx, head, failed;
  reg [2:0] projection;
  reg [31:0] layer, inputs, outputs, received, group_index, output_base;
  reg [31:0] input_base, weight_row, weight_column, dot_column, retired;
  reg [31:0] emit_column, tile_width, group_width, payload, bias;
  reg [1023:0] gathered, activation, weight_q, activation_q;
  reg [31:0] accumulator_q;
  reg [4:0] flags;
  (* ramstyle = "M20K", nomem2reg *) reg [1023:0] activations [0:GROUPS-1];
  (* ramstyle = "M20K", nomem2reg *) reg [1023:0] weights [0:63];
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] sums [0:63];
  wire [20:0] converted=anvil_q1_fp2_pkg::fp32_to_bf16(in_data);
  wire quant_valid;
  wire [511:0] quant_data;
  wire [15:0] quant_scales;
  wire [4:0] quant_status;
  wire [6:0] quant_saturations;
  wire [63:0] collect_mask=64'hffffffffffffffff >> (64-group_width);
  wire [1023:0] decoded_quant;
  wire [4:0] decode_flags [0:126];
  wire [20:0] quant_lane [0:63];
  wire reader_ready, reader_valid, reader_last, reader_done, reader_error;
  wire [15:0] reader_data;
  wire [4:0] reader_status;
  wire add_ready, add_valid;
  wire [31:0] add_result;
  wire [4:0] add_status;
  wire reader_transfer=reader_valid && state==WEIGHT_LOAD;
  wire [31:0] roundtrip={converted[15:0],16'd0};
  wire [31:0] ordered_input=in_data[31] ? ~in_data : in_data ^ 32'h80000000;
  wire [31:0] ordered_roundtrip=roundtrip[31] ? ~roundtrip : roundtrip ^ 32'h80000000;
  assign ulp_valid=rst_n && in_valid && in_ready;
  assign ulp_distance=(in_data[30:23]==255 || roundtrip[30:23]==255) ? 32'hffffffff :
    (ordered_input>ordered_roundtrip ? ordered_input-ordered_roundtrip :
     ordered_roundtrip-ordered_input);
  assign cmd_ready=rst_n && state==IDLE;
  assign in_ready=rst_n && state==COLLECT;
  assign out_valid=rst_n && state==OUTPUT;
  assign out_data=out_valid ? payload : 32'd0;
  assign out_index=out_valid ? output_base+emit_column : 32'd0;
  assign out_last=out_valid && output_base+emit_column+1==outputs;
  assign done=rst_n && state==FINISH;
  assign error=done && failed;
  assign status=rst_n && (done || out_valid) ? flags : 5'd0;
  assign tensor_valid=rst_n && state==DOT_SEND;
  assign tensor_a=tensor_valid ? activation : 1024'd0;
  assign tensor_b=tensor_valid ? weight_q : 1024'd0;
  assign tensor_mask=tensor_valid ? collect_mask : 64'd0;
  assign tensor_acc=tensor_valid ? accumulator_q : 32'd0;
  assign bias_req_valid=rst_n && state==BIAS_REQ;
  assign bias_layer=bias_req_valid ? layer : 32'd0;
  assign bias_proj=bias_req_valid ? projection : 3'd0;
  assign bias_col=bias_req_valid ? output_base+emit_column : 32'd0;
  assign bias_rsp_ready=rst_n && state==BIAS_RSP;
  generate
    if (MAX_INPUT<1 || MAX_OUTPUT<1) begin: invalid_parameters
      initial $fatal(1,"FP2 PROJECTION PARAMETER ERROR");
    end
    for (genvar n=0;n<64;n=n+1) begin: quant_decode
      assign quant_lane[n]=anvil_q1_fp2_pkg::mx_to_bf16(quant_data[8*n+:8],quant_scales[8*(n>>5)+:8]);
      assign decoded_quant[16*n+:16]=n<group_width ? quant_lane[n][15:0] : 16'd0;
      assign decode_flags[63+n]=n<group_width ? quant_lane[n][20:16] : 5'd0;
    end
    for (genvar flag_index=0;flag_index<63;flag_index=flag_index+1) begin: quant_flags
      assign decode_flags[flag_index]=decode_flags[2*flag_index+1] | decode_flags[2*flag_index+2];
    end
  endgenerate
  anvil_q1_fp2_mx_quantize quantizer(
    .clk(clk),.rst_n(rst_n),.in_valid(state==QUANTIZE),.bf16_data(gathered),
    .lane_mask(collect_mask),.out_valid(quant_valid),.mx_data(quant_data),
    .scales(quant_scales),.status(quant_status),.saturation_events(quant_saturations));
  anvil_q1_fp2_ddr_read_stream weight_reader(
    .clk(clk),.rst_n(rst_n),.cmd_valid(state==WEIGHT_CMD),.cmd_ready(reader_ready),
    .cmd_format_mx(format_mx),.cmd_kind(head ? 4'd0 : 4'd12),
    .cmd_layer(head ? 32'd0 : layer),.cmd_proj(head ? 3'd0 : projection),
    .cmd_row(head ? output_base+weight_column : input_base+weight_row),
    .cmd_first(head ? input_base : output_base),
    .cmd_len(head ? group_width : tile_width),
    .out_valid(reader_valid),.out_ready(state==WEIGHT_LOAD),
    .out_data(reader_data),.out_last(reader_last),.status(reader_status),
    .done(reader_done),.error(reader_error),.work_active(work_active),
    .result_needed(result_needed),.fetch_valid(fetch_valid),.fetch_ready(fetch_ready),
    .fetch_scale(fetch_scale),.fetch_kind(fetch_kind),.fetch_layer(fetch_layer),
    .fetch_proj(fetch_proj),.fetch_row(fetch_row),.fetch_col(fetch_col),
    .fetch_tag(fetch_tag),.response_valid(response_valid),.response_ready(response_ready),
    .response_tag(response_tag),.response_write(response_write),
    .response_error(response_error),.response_data(response_data));
  anvil_q1_fp2_fp32_binary #(.MULTIPLY(0)) bias_adder(
    .clk(clk),.rst_n(rst_n),.in_valid(state==BIAS_ADD),.in_ready(add_ready),
    .out_ready(1'b1),.a(payload),.b(bias),.out_valid(add_valid),
    .result(add_result),.status(add_status));
  always @(posedge clk) begin
    if (rst_n && state==STORE)
      activations[group_index[GB-1:0]]<=gathered;
    activation_q<=activations[group_index[GB-1:0]];
    if (reader_transfer)
      weights[weight_column[5:0]][16*weight_row[5:0]+:16]<=reader_data;
    weight_q<=weights[dot_column[5:0]];
    accumulator_q<=sums[(state==RESULT_READ || state==RESULT_LATCH) ?
      emit_column[5:0] : dot_column[5:0]];
    if (rst_n && state==CLEAR) sums[dot_column[5:0]]<=0;
    if (rst_n && tensor_result_valid && (state==DOT_READ || state==DOT_LATCH ||
        state==DOT_SEND || state==DOT_WAIT)) sums[retired[5:0]]<=tensor_result;
  end
  always @(posedge clk) begin
    if (!rst_n) begin
      state<=IDLE; format_mx<=0; head<=0; failed<=0; projection<=0; layer<=0;
      inputs<=0; outputs<=0; received<=0; group_index<=0; output_base<=0;
      input_base<=0; weight_row<=0; weight_column<=0; dot_column<=0; retired<=0;
      emit_column<=0; tile_width<=0; group_width<=0; payload<=0; bias<=0;
      gathered<=0; activation<=0; flags<=0;
    end else if (reader_done && reader_error) begin
      failed<=1; flags<=flags | reader_status; state<=ERROR_WAIT0;
    end else if (tensor_result_valid && (|tensor_status[4:2])) begin
      failed<=1; flags<=flags | tensor_status; state<=ERROR_WAIT0;
    end else begin
      if (tensor_result_valid) begin retired<=retired+1'b1; flags<=flags | tensor_status; end
      case (state)
        IDLE: if (cmd_valid) begin
          format_mx<=cmd_format_mx; head<=cmd_head; layer<=cmd_layer;
          inputs<=cmd_inputs; outputs<=cmd_outputs; projection<=cmd_proj;
          received<=0; group_index<=0; output_base<=0; input_base<=0;
          weight_row<=0; weight_column<=0; dot_column<=0; retired<=0;
          emit_column<=0; gathered<=0; flags<=0; failed<=0;
          group_width<=cmd_inputs<64 ? cmd_inputs : 32'd64;
          tile_width<=cmd_outputs<64 ? cmd_outputs : 32'd64;
          if (cmd_inputs==0 || cmd_inputs>MAX_INPUT || cmd_outputs==0 ||
              cmd_outputs>MAX_OUTPUT || (!cmd_head && cmd_proj>6)) begin
            failed<=1; state<=ERROR_WAIT0;
          end else state<=COLLECT;
        end
        COLLECT: if (in_valid) begin
          gathered[16*received[5:0]+:16]<=converted[15:0];
          flags<=flags | converted[20:16];
          if (in_last!=(received+1==inputs) || (|converted[20:18]) ||
              in_data[30:23]==255) begin failed<=1; state<=ERROR_WAIT0; end
          else if (in_last || (&received[5:0])) begin
            if (format_mx) state<=QUANTIZE;
            else state<=STORE;
          end else received<=received+1'b1;
        end
        QUANTIZE: state<=QUANT_WAIT;
        QUANT_WAIT: if (quant_valid) begin
          flags<=flags | quant_status | decode_flags[0];
          if ((|quant_status[4:2]) || (|decode_flags[0][4:2]) ||
              quant_saturations!=0) begin failed<=1; state<=ERROR_WAIT0; end
          else begin gathered<=decoded_quant; state<=STORE; end
        end
        STORE: begin
          if (received+1==inputs) begin
            group_index<=0; group_width<=inputs<64 ? inputs : 32'd64; state<=CLEAR;
          end else begin
            received<=received+1'b1; group_index<=group_index+1'b1; gathered<=0;
            group_width<=inputs-received-1<64 ? inputs-received-1 : 32'd64;
            state<=COLLECT;
          end
        end
        CLEAR: begin
          if (dot_column+1==tile_width) begin dot_column<=0; state<=ACT_READ; end
          else dot_column<=dot_column+1'b1;
        end
        ACT_READ: state<=ACT_LATCH;
        ACT_LATCH: begin
          activation<=activation_q; weight_row<=0; weight_column<=0;
          state<=WEIGHT_CMD;
        end
        WEIGHT_CMD: if (reader_ready) state<=WEIGHT_LOAD;
        WEIGHT_LOAD: if (reader_transfer) begin
          flags<=flags | reader_status;
          if (head) begin
            if (!reader_last) weight_row<=weight_row+1'b1;
          end else if (!reader_last) weight_column<=weight_column+1'b1;
          if (reader_last) state<=WEIGHT_WAIT;
        end
        WEIGHT_WAIT: if (reader_done) begin
          if (head ? weight_column+1==tile_width : weight_row+1==group_width) begin
            dot_column<=0; retired<=0; state<=DOT_READ;
          end else begin
            if (head) begin weight_column<=weight_column+1'b1; weight_row<=0; end
            else begin weight_row<=weight_row+1'b1; weight_column<=0; end
            state<=WEIGHT_CMD;
          end
        end
        DOT_READ: state<=DOT_LATCH;
        DOT_LATCH: state<=DOT_SEND;
        DOT_SEND: if (tensor_ready) begin
          if (dot_column+1==tile_width) state<=DOT_WAIT;
          else begin dot_column<=dot_column+1'b1; state<=DOT_READ; end
        end
        DOT_WAIT: if (retired==tile_width) begin
          if (input_base+group_width==inputs) begin emit_column<=0; state<=RESULT_READ; end
          else begin
            input_base<=input_base+group_width; group_index<=group_index+1'b1;
            group_width<=inputs-input_base-group_width<64 ?
              inputs-input_base-group_width : 32'd64;
            state<=ACT_READ;
          end
        end
        RESULT_READ: state<=RESULT_LATCH;
        RESULT_LATCH: begin
          payload<=accumulator_q;
          if (!head && projection<3) state<=BIAS_REQ;
          else state<=OUTPUT;
        end
        BIAS_REQ: if (bias_req_ready) state<=BIAS_RSP;
        BIAS_RSP: if (bias_rsp_valid) begin
          if (bias_rsp_error || bias_rsp_data[31:16]!=0 ||
              bias_rsp_data[14:7]==255) begin failed<=1; state<=ERROR_WAIT0; end
          else begin bias<={bias_rsp_data[15:0],16'd0}; state<=BIAS_ADD; end
        end
        BIAS_ADD: if (add_ready) state<=BIAS_WAIT;
        BIAS_WAIT: if (add_valid) begin
          flags<=flags | add_status; payload<=add_result;
          if (|add_status[4:2]) begin failed<=1; state<=ERROR_WAIT0; end
          else state<=OUTPUT;
        end
        OUTPUT: if (out_ready) begin
          if (emit_column+1<tile_width) begin emit_column<=emit_column+1'b1; state<=RESULT_READ; end
          else if (output_base+tile_width==outputs) state<=COMPLETE_WAIT;
          else begin
            output_base<=output_base+tile_width;
            tile_width<=outputs-output_base-tile_width<64 ?
              outputs-output_base-tile_width : 32'd64;
            input_base<=0; group_index<=0; group_width<=inputs<64 ? inputs : 32'd64;
            dot_column<=0; state<=CLEAR;
          end
        end
        COMPLETE_WAIT: state<=FINISH;
        ERROR_WAIT0: state<=ERROR_WAIT1;
        ERROR_WAIT1: state<=FINISH;
        FINISH: state<=IDLE;
        default: begin failed<=1; state<=ERROR_WAIT0; end
      endcase
    end
  end
endmodule
