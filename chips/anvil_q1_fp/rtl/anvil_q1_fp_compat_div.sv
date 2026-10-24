module anvil_q1_fp_compat_div(
  input wire clk, rst_n, in_valid,
  output wire in_ready,
  input wire [127:0] numerator,
  input wire [63:0] denominator,
  output wire out_valid,
  output wire [127:0] quotient,
  output wire [63:0] remainder,
  output wire divide_by_zero
);
  reg busy, valid_reg, zero_reg;
  reg [6:0] digit;
  reg [127:0] dividend, quotient_work, quotient_reg;
  reg [63:0] divisor, remainder_work, remainder_reg;
  wire [64:0] shifted_remainder, next_remainder;
  wire subtract;
  wire [127:0] next_quotient;
  assign shifted_remainder={remainder_work,dividend[127]};
  assign subtract=shifted_remainder>={1'b0,divisor};
  assign next_remainder=subtract ?
    shifted_remainder-{1'b0,divisor} : shifted_remainder;
  assign next_quotient={quotient_work[126:0],subtract};
  assign in_ready=rst_n && !busy;
  assign out_valid=rst_n && valid_reg;
  assign quotient=(rst_n && valid_reg) ? quotient_reg : 128'd0;
  assign remainder=(rst_n && valid_reg) ? remainder_reg : 64'd0;
  assign divide_by_zero=rst_n && valid_reg && zero_reg;
  always @(posedge clk) begin
    if (!rst_n) begin
      busy<=0; valid_reg<=0; zero_reg<=0; digit<=0;
      dividend<=0; quotient_work<=0; quotient_reg<=0;
      divisor<=0; remainder_work<=0; remainder_reg<=0;
    end else begin
      valid_reg<=0; zero_reg<=0;
      if (!busy && in_valid) begin
        digit<=0; dividend<=numerator; divisor<=denominator;
        quotient_work<=0; remainder_work<=0;
        if (denominator==0) begin
          valid_reg<=1; zero_reg<=1; quotient_reg<=0; remainder_reg<=0;
        end else busy<=1;
      end else if (busy) begin
        dividend<=dividend<<1; quotient_work<=next_quotient;
        remainder_work<=next_remainder[63:0];
        if (digit==127) begin
          busy<=0; valid_reg<=1;
          quotient_reg<=next_quotient; remainder_reg<=next_remainder[63:0];
        end else digit<=digit+1;
      end
    end
  end
endmodule
