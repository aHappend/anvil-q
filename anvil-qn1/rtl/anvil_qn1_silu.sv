module anvil_qn1_silu (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire [15:0] in_data,
  output wire out_valid,
  input wire out_ready,
  output wire [15:0] out_data,
  output wire out_error
);
  import anvil_qn1_pkg::*;
  localparam IDLE=0, EXP_REQ=1, EXP_WAIT=2, DENOM=3, PRODUCT=4, DIVIDE=5, ROUND=6, HOLD=7;
  reg [2:0] state;
  reg waiting, failed;
  reg [31:0] x, exponential, denominator, numerator, quotient;
  reg [15:0] result;
  wire exp_ready, exp_valid, exp_error;
  wire [31:0] exp_data;
  wire [31:0] exp_input={1'b1,x[30:0]};
  anvil_qn1_exp exponential_unit (
    .clk(clk),.rst_n(rst_n),.flush(flush),.in_valid(state==EXP_REQ),
    .in_ready(exp_ready),.in_data(exp_input),.out_valid(exp_valid),
    .out_ready(state==EXP_WAIT),.out_data(exp_data),.out_error(exp_error)
  );
  wire arithmetic_state=state==DENOM || state==PRODUCT || state==DIVIDE;
  wire alu_ready, alu_valid, alu_error;
  wire [31:0] alu_data;
  wire [2:0] alu_op=state==DENOM ? 3'd0 : state==PRODUCT ? 3'd2 : 3'd3;
  wire [31:0] alu_a=state==DENOM ? 32'h3f800000 : state==PRODUCT ? x : numerator;
  wire [31:0] alu_b=state==DIVIDE ? denominator : exponential;
  wire [16:0] rounded=round_bf16(quotient);
  anvil_qn1_scalar arithmetic (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(arithmetic_state && !waiting),.in_ready(alu_ready),
    .in_op(alu_op),.in_a(alu_a),.in_b(alu_b),.in_error(1'b0),
    .out_valid(alu_valid),.out_ready(waiting),.out_data(alu_data),.out_error(alu_error)
  );
  assign in_ready=rst_n && !flush && state==IDLE;
  assign out_valid=rst_n && !flush && state==HOLD;
  assign out_data=out_valid ? result : 16'd0;
  assign out_error=out_valid && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; waiting<=0; failed<=0; x<=0; exponential<=0;
      denominator<=0; numerator<=0; quotient<=0; result<=0;
    end else if (flush) begin
      state<=IDLE; waiting<=0; failed<=0; result<=0;
    end else begin
      if (arithmetic_state && !waiting && alu_ready) waiting<=1;
      if (alu_valid && waiting) begin
        waiting<=0;
        if (alu_error) begin result<=0; failed<=1; state<=HOLD; end
        else case (state)
          DENOM: begin
            denominator<=alu_data;
            if (x[31]) state<=PRODUCT;
            else begin numerator<=x; state<=DIVIDE; end
          end
          PRODUCT: begin numerator<=alu_data; state<=DIVIDE; end
          DIVIDE: begin quotient<=alu_data; state<=ROUND; end
          default: begin result<=0; failed<=1; state<=HOLD; end
        endcase
      end else case (state)
        IDLE: if (in_valid && in_ready) begin
          x<={in_data,16'd0}; failed<=0; waiting<=0;
          if (bf16_invalid(in_data)) begin result<=0; failed<=1; state<=HOLD; end
          else state<=EXP_REQ;
        end
        EXP_REQ: if (exp_ready) state<=EXP_WAIT;
        EXP_WAIT: if (exp_valid) begin
          if (exp_error) begin result<=0; failed<=1; state<=HOLD; end
          else begin exponential<=exp_data; state<=DENOM; end
        end
        ROUND: begin
          result<=rounded[16] ? 16'd0 : rounded[15:0];
          failed<=rounded[16]; state<=HOLD;
        end
        HOLD: if (out_ready) state<=IDLE;
        default: begin end
      endcase
    end
  end
endmodule
