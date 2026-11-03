module anvil_q4_fp_silu (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire [31:0] x,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] result,
  output wire [4:0] flags
);
  localparam [2:0] IDLE=0, EXP_ISSUE=1, EXP_WAIT=2,
    ADD_ISSUE=3, ADD_WAIT=4, DIV_ISSUE=5, DIV_WAIT=6, RESPONSE=7;
  reg [2:0] state;
  reg [31:0] operand, exponential, denominator, result_register;
  reg [4:0] flag_register;
  wire exp_ready, exp_valid, fp_ready, fp_valid;
  wire [31:0] exp_result, fp_result;
  wire [4:0] exp_flags, fp_flags;
  anvil_q4_fp_exp exp_unit (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==EXP_ISSUE),.in_ready(exp_ready),
    .x(operand ^ 32'h80000000),.out_valid(exp_valid),
    .out_ready(state==EXP_WAIT),.result(exp_result),.flags(exp_flags)
  );
  anvil_q4_fp32 arithmetic (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ADD_ISSUE || state==DIV_ISSUE),.in_ready(fp_ready),
    .op(state==ADD_ISSUE ? 4'd0 : 4'd3),
    .a(state==ADD_ISSUE ? 32'h3f800000 : operand),
    .b(state==ADD_ISSUE ? exponential : denominator),
    .out_valid(fp_valid),.out_ready(state==ADD_WAIT || state==DIV_WAIT),
    .result(fp_result),.flags(fp_flags)
  );
  assign in_ready=rst_n && !flush && state==IDLE;
  assign out_valid=rst_n && !flush && state==RESPONSE;
  assign result=out_valid ? result_register : 32'd0;
  assign flags=out_valid ? flag_register : 5'd0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; operand<=0; exponential<=0; denominator<=0;
      result_register<=0; flag_register<=0;
    end else if (flush) begin state<=IDLE; result_register<=0; flag_register<=0; end
    else case (state)
      IDLE: if (in_valid) begin operand<=x; flag_register<=0; state<=EXP_ISSUE; end
      EXP_ISSUE: if (exp_ready) state<=EXP_WAIT;
      EXP_WAIT: if (exp_valid) begin
        exponential<=exp_result; flag_register<=exp_flags; state<=ADD_ISSUE;
      end
      ADD_ISSUE: if (fp_ready) state<=ADD_WAIT;
      ADD_WAIT: if (fp_valid) begin
        denominator<=fp_result; flag_register<=flag_register | fp_flags; state<=DIV_ISSUE;
      end
      DIV_ISSUE: if (fp_ready) state<=DIV_WAIT;
      DIV_WAIT: if (fp_valid) begin
        result_register<=fp_result; flag_register<=flag_register | fp_flags; state<=RESPONSE;
      end
      RESPONSE: if (out_ready) state<=IDLE;
      default: begin result_register<=32'h7fc00000; flag_register<=5'b10000; state<=RESPONSE; end
    endcase
  end
endmodule
