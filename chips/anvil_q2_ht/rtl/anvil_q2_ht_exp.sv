module anvil_q2_ht_exp (
  input wire clk, rst_n, annul,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire signed [127:0] cmd_x,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [31:0] rsp_data,
  output wire rsp_error
);
  import anvil_q2_ht_int_pkg::*;
  localparam [3:0] IDLE=0, RANGE=1, PRODUCT=2, PRODUCT_WAIT=3,
    DIVIDE=4, DIVIDE_WAIT=5, TERM=6, FINISH=7, RESPONSE=8;
  reg [3:0] state, iteration;
  reg [31:0] remainder, term_magnitude, quotient;
  reg [5:0] power;
  reg term_negative, failed;
  reg signed [31:0] total;
  reg [31:0] result;
  reg [127:0] dividend;
  wire math_ready, math_valid, math_error;
  wire signed [127:0] math_result;
  wire [3:0] math_operation=state==PRODUCT ? M_MUL32 : M_UDIV;
  wire request=state==PRODUCT || state==DIVIDE;
  wire signed [31:0] next_term=term_negative ?
    $signed(quotient) : -$signed(quotient);
  anvil_q2_ht_integer_math arithmetic (
    .clk(clk),.rst_n(rst_n),.annul(annul),
    .cmd_valid(rst_n && !annul && request),.cmd_ready(math_ready),
    .cmd_op(math_operation),
    .cmd_a(state==PRODUCT ? $signed({96'd0,term_magnitude}) : $signed(dividend)),
    .cmd_b(state==PRODUCT ? $signed({96'd0,remainder}) :
      $signed({124'd0,iteration})),
    .rsp_valid(math_valid),.rsp_ready(state==PRODUCT_WAIT || state==DIVIDE_WAIT),
    .rsp_data(math_result),.rsp_error(math_error));
  assign cmd_ready=rst_n && !annul && state==IDLE;
  assign rsp_valid=rst_n && !annul && state==RESPONSE;
  assign rsp_data=rsp_valid ? result : 32'd0;
  assign rsp_error=rsp_valid && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; iteration<=0; remainder<=0; term_magnitude<=0;
      quotient<=0; power<=0; term_negative<=0; failed<=0;
      total<=0; result<=0; dividend<=0;
    end else if (annul) begin state<=IDLE; failed<=0; result<=0; end
    else if (math_valid && math_error) begin
      failed<=1; result<=0; state<=RESPONSE;
    end else case (state)
      IDLE: if (cmd_valid) begin
        failed<=0; power<=0; iteration<=1; term_negative<=0;
        term_magnitude<=16777216; total<=16777216;
        if (cmd_x < -128'sd1048576) begin result<=0; state<=RESPONSE; end
        else if (cmd_x>=0) begin result<=16777216; state<=RESPONSE; end
        else begin remainder<=(~cmd_x[31:0]+32'd1) << 8; state<=RANGE; end
      end
      RANGE: if (remainder>=11629080) begin
        remainder<=remainder-32'd11629080; power<=power+6'd1;
      end else state<=PRODUCT;
      PRODUCT: if (math_ready) state<=PRODUCT_WAIT;
      PRODUCT_WAIT: if (math_valid) begin
        dividend<=$unsigned(math_result) >> 24; state<=DIVIDE;
      end
      DIVIDE: if (math_ready) state<=DIVIDE_WAIT;
      DIVIDE_WAIT: if (math_valid) begin quotient<=math_result[31:0]; state<=TERM; end
      TERM: begin
        term_magnitude<=quotient; term_negative<=!term_negative;
        total<=total+next_term;
        if (iteration==6) state<=FINISH;
        else begin iteration<=iteration+4'd1; state<=PRODUCT; end
      end
      FINISH: begin result<=total<0 ? 32'd0 : ($unsigned(total) >> power); state<=RESPONSE; end
      RESPONSE: if (rsp_ready) state<=IDLE;
      default: begin failed<=1; result<=0; state<=RESPONSE; end
    endcase
  end
endmodule
