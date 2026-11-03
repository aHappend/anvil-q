module anvil_q2_fp_awq_dequant #(
  parameter FP_FORMAT=0
)(
  input wire clk, rst_n,
  input wire in_valid, output wire in_ready,
  input wire [31:0] in_qweight, in_qzero,
  input wire [15:0] in_scale,
  input wire [2:0] in_lane,
  output wire out_valid, input wire out_ready,
  output wire [15:0] out_weight,
  output wire out_error
);
  import anvil_q2_fp_pkg::*;
  localparam IDLE=0, MULTIPLY=1, WAIT_PRODUCT=2, CONVERT=3, OUTPUT=4;
  reg [2:0] state;
  reg [31:0] delta, scale, product;
  reg [15:0] weight;
  reg failed;
  wire [4:0] shift={in_lane[0],in_lane[2],in_lane[1],2'b00};
  wire [31:0] shifted_weight=in_qweight >> shift;
  wire [31:0] shifted_zero=in_qzero >> shift;
  wire signed [4:0] signed_delta=
    $signed({1'b0,shifted_weight[3:0]})-$signed({1'b0,shifted_zero[3:0]});
  wire [31:0] expanded_scale=expand16(in_scale,FP_FORMAT);
  wire [15:0] converted=narrow16(product,FP_FORMAT);
  wire mul_ready, mul_valid, mul_error;
  wire [31:0] mul_result;
  assign in_ready=rst_n && state==IDLE;
  assign out_valid=rst_n && state==OUTPUT;
  assign out_weight=rst_n ? weight : 16'd0;
  assign out_error=out_valid && failed;
  generate if (FP_FORMAT!=0 && FP_FORMAT!=1) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_FP PARAMETER ERROR: AWQ format");
  end endgenerate
  anvil_q2_fp_scalar arithmetic(
    .clk(clk),.rst_n(rst_n),.in_valid(rst_n && state==MULTIPLY),
    .in_ready(mul_ready),.in_op(3'd1),.in_a(delta),.in_b(scale),
    .out_valid(mul_valid),.out_ready(1'b1),.out_data(mul_result),.out_error(mul_error));
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; delta<=0; scale<=0; product<=0; weight<=0; failed<=0;
    end else case (state)
      IDLE: if (in_valid) begin
        failed<=0;
        if (!fp_is_finite(expanded_scale) ||
            (expanded_scale[31] && !fp_is_zero(expanded_scale))) begin
          failed<=1; weight<=0; state<=OUTPUT;
        end else begin
          delta<=fp_from_int({{27{signed_delta[4]}},signed_delta});
          scale<=expanded_scale; state<=MULTIPLY;
        end
      end
      MULTIPLY: if (mul_ready) state<=WAIT_PRODUCT;
      WAIT_PRODUCT: if (mul_valid) begin
        product<=mul_result;
        if (mul_error) begin failed<=1; weight<=0; state<=OUTPUT; end
        else state<=CONVERT;
      end
      CONVERT: begin
        weight<=converted;
        failed<=!fp_is_finite(expand16(converted,FP_FORMAT));
        state<=OUTPUT;
      end
      OUTPUT: if (out_ready) state<=IDLE;
      default: begin failed<=1; weight<=0; state<=OUTPUT; end
    endcase
  end
endmodule
