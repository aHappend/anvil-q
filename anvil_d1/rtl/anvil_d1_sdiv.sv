module anvil_d1_sdiv #(
  parameter integer NUM_W=128, DEN_W=64,
  localparam integer NW=(NUM_W>=1 && NUM_W<=128) ? NUM_W : 1,
  localparam integer DW=(DEN_W>=1 && DEN_W<=128) ? DEN_W : 1
) (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire signed [NW-1:0] numerator,
  input wire [DW-1:0] denominator,
  output wire out_valid,
  input wire out_ready,
  output wire out_error,
  output wire signed [NW:0] quotient,
  output wire [DW-1:0] remainder
);
  localparam IDLE=0, LAUNCH=1, WAIT_RESULT=2;
  reg [1:0] state;
  reg armed, valid, failed, negative;
  reg [NW-1:0] magnitude;
  reg [DW-1:0] divisor, result_r;
  reg [NW:0] result_q;
  wire [NW-1:0] negated_input;
  wire unused_input_borrow, unused_result_borrow;
  wire core_ready, core_valid, core_error;
  wire [NW-1:0] core_q;
  wire [DW-1:0] core_r;
  wire [NW:0] negated_result;
  anvil_d1_sub_unsigned #(.WIDTH(NW)) negate_input (
    .a({NW{1'b0}}),.b(numerator),.difference(negated_input),.borrow(unused_input_borrow)
  );
  anvil_d1_sub_unsigned #(.WIDTH(NW+1)) negate_result (
    .a({(NW+1){1'b0}}),.b({1'b0,core_q}),
    .difference(negated_result),.borrow(unused_result_borrow)
  );
  anvil_d1_udiv #(.NUM_W(NUM_W),.DEN_W(DEN_W)) core (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==LAUNCH),.in_ready(core_ready),
    .numerator(magnitude),.denominator(divisor),
    .out_valid(core_valid),.out_ready(state==WAIT_RESULT),
    .out_error(core_error),.quotient(core_q),.remainder(core_r)
  );
  assign in_ready=rst_n && armed && !flush && state==IDLE && !valid && core_ready;
  assign out_valid=rst_n && !flush && valid;
  assign out_error=out_valid && failed;
  assign quotient=rst_n && !flush ? $signed(result_q) : {(NW+1){1'b0}};
  assign remainder=rst_n && !flush ? result_r : {DW{1'b0}};
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; valid<=0; failed<=0; negative<=0;
      magnitude<=0; divisor<=0; result_r<=0; result_q<=0;
    end else begin
      armed<=1;
      if (flush) begin state<=IDLE; valid<=0; failed<=0; result_q<=0; result_r<=0; end
      else begin
        if (out_valid && out_ready) valid<=0;
        case (state)
          IDLE: if (in_valid && in_ready) begin
            magnitude<=numerator[NW-1] ? negated_input : $unsigned(numerator);
            negative<=numerator[NW-1]; divisor<=denominator;
            failed<=0; state<=LAUNCH;
          end
          LAUNCH: if (core_ready) state<=WAIT_RESULT;
          WAIT_RESULT: if (core_valid) begin
            result_q<=negative ? negated_result : {1'b0,core_q};
            result_r<=core_r; failed<=core_error; valid<=1; state<=IDLE;
          end
          default: begin state<=IDLE; failed<=1; valid<=1; end
        endcase
      end
    end
  end
endmodule
