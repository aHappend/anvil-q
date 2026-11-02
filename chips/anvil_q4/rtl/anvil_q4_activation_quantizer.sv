module anvil_q4_activation_quantizer (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire [31:0] x, scale,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] result,
  output wire [4:0] flags,
  output wire error
);
  import anvil_q4_fp_pkg::*;
  localparam [3:0] IDLE=0, DIV_ISSUE=1, DIV_WAIT=2, ROUND=3,
    INT_ISSUE=4, INT_WAIT=5, MUL_ISSUE=6, MUL_WAIT=7,
    NARROW_ISSUE=8, NARROW_WAIT=9, WIDEN_ISSUE=10, WIDEN_WAIT=11, RESPONSE=12;
  reg [3:0] state;
  reg [31:0] operand, tensor_scale, result_register;
  reg [4:0] flag_register;
  reg failed;
  wire [31:0] bounded=ordered_less(32'h42fe0000,operand) ? 32'h42fe0000 :
    ordered_less(operand,32'hc2fe0000) ? 32'hc2fe0000 : operand;
  wire [31:0] integer_code=bounded_int_rne(bounded);
  wire fp_ready, fp_valid;
  wire [31:0] fp_result;
  wire [4:0] fp_flags;
  wire [3:0] operation=state==DIV_ISSUE ? 4'd3 :
    state==INT_ISSUE ? 4'd9 : state==MUL_ISSUE ? 4'd2 :
    state==NARROW_ISSUE ? 4'd7 : 4'd5;
  anvil_q4_fp32 arithmetic (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==DIV_ISSUE || state==INT_ISSUE || state==MUL_ISSUE ||
      state==NARROW_ISSUE || state==WIDEN_ISSUE),
    .in_ready(fp_ready),.op(operation),.a(operand),.b(tensor_scale),
    .out_valid(fp_valid),.out_ready(state==DIV_WAIT || state==INT_WAIT ||
      state==MUL_WAIT || state==NARROW_WAIT || state==WIDEN_WAIT),
    .result(fp_result),.flags(fp_flags)
  );
  assign in_ready=rst_n && !flush && state==IDLE;
  assign out_valid=rst_n && !flush && state==RESPONSE;
  assign result=rst_n && !flush ? result_register : 32'd0;
  assign flags=rst_n && !flush ? flag_register : 5'd0;
  assign error=out_valid && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; operand<=0; tensor_scale<=0;
      result_register<=0; flag_register<=0; failed<=0;
    end else if (flush) begin
      state<=IDLE; result_register<=0; flag_register<=0; failed<=0;
    end else case (state)
      IDLE: if (in_valid) begin
        operand<=x; tensor_scale<=scale; flag_register<=0; failed<=0;
        if (is_nan(x) || is_infinity(x) ||
            is_nan(scale) || is_infinity(scale)) begin
          result_register<=32'h7fc00000; flag_register<=5'b10000; state<=RESPONSE;
        end else if (!scale[31] && is_zero(scale) && x[30:0]<=31'h0000003f) begin
          result_register<=is_zero(x) ? 32'd0 : {x[31],31'd0};
          flag_register<=is_zero(x) ? 5'd0 : 5'b00011; state<=RESPONSE;
        end else if (scale[31] || is_zero(scale)) begin
          failed<=1; result_register<=32'h7fc00000; state<=RESPONSE;
        end else state<=DIV_ISSUE;
      end
      DIV_ISSUE: if (fp_ready) state<=DIV_WAIT;
      DIV_WAIT: if (fp_valid) begin
        operand<=fp_result; flag_register<=flag_register | fp_flags; state<=ROUND;
      end
      ROUND: begin operand<=integer_code; state<=INT_ISSUE; end
      INT_ISSUE: if (fp_ready) state<=INT_WAIT;
      INT_WAIT: if (fp_valid) begin
        operand<=fp_result; flag_register<=flag_register | fp_flags; state<=MUL_ISSUE;
      end
      MUL_ISSUE: if (fp_ready) state<=MUL_WAIT;
      MUL_WAIT: if (fp_valid) begin
        operand<=fp_result; flag_register<=flag_register | fp_flags; state<=NARROW_ISSUE;
      end
      NARROW_ISSUE: if (fp_ready) state<=NARROW_WAIT;
      NARROW_WAIT: if (fp_valid) begin
        operand<=fp_result; flag_register<=flag_register | fp_flags; state<=WIDEN_ISSUE;
      end
      WIDEN_ISSUE: if (fp_ready) state<=WIDEN_WAIT;
      WIDEN_WAIT: if (fp_valid) begin
        result_register<=fp_result; flag_register<=flag_register | fp_flags; state<=RESPONSE;
      end
      RESPONSE: if (out_ready) state<=IDLE;
      default: begin failed<=1; state<=RESPONSE; end
    endcase
  end
endmodule
