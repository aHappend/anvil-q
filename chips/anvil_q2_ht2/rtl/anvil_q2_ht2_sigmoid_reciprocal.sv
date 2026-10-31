module anvil_q2_ht2_sigmoid_reciprocal (
  input wire clk, rst_n, advance,
  input wire [31:0] s_data,
  output wire [31:0] m_data,
  output wire m_error
);
  import anvil_q2_ht2_fp_pkg::*;
  reg [24:0] divisor [0:50], remainder [0:50];
  reg [27:0] quotient [0:50];
  reg signed [11:0] exponent [0:50];
  reg [26:0] significand52;
  reg signed [11:0] exponent52;
  reg [31:0] result53;
  reg error53;
  wire bad_input=s_data<32'h3f800000 || s_data>32'h40000000;
  wire [31:0] operand=bad_input ? 32'h3f800000 : s_data;
  wire delayed_error;
  wire [32:0] packed_result=pack_fp32(1'b0,exponent52,significand52);
  genvar bit_index;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      divisor[0]<=0; remainder[0]<=0; quotient[0]<=0; exponent[0]<=0;
      significand52<=0; exponent52<=0; result53<=0; error53<=0;
    end else if (advance) begin
      divisor[0]<={1'b0,1'b1,operand[22:0]};
      remainder[0]<=1; quotient[0]<=0;
      exponent[0]<=12'sd253-$signed({4'd0,operand[30:23]});
      if (quotient[50][27]) begin
        significand52<={quotient[50][27:2],
          ((|quotient[50][1:0]) || (|remainder[50]))};
        exponent52<=exponent[50]+12'sd1;
      end else begin
        significand52<={quotient[50][26:1],
          (quotient[50][0] || (|remainder[50]))};
        exponent52<=exponent[50];
      end
      result53<=packed_result[31:0]; error53<=packed_result[32];
    end
  end
  generate for (bit_index=0;bit_index<50;bit_index=bit_index+1) begin: restoring
    wire [25:0] shifted={remainder[bit_index],1'b0};
    wire take=shifted>={1'b0,divisor[bit_index]};
    wire [25:0] difference=shifted-{1'b0,divisor[bit_index]};
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        divisor[bit_index+1]<=0; remainder[bit_index+1]<=0;
        quotient[bit_index+1]<=0; exponent[bit_index+1]<=0;
      end else if (advance) begin
        divisor[bit_index+1]<=divisor[bit_index];
        remainder[bit_index+1]<=take ? difference[24:0] : shifted[24:0];
        quotient[bit_index+1]<={quotient[bit_index][26:0],take};
        exponent[bit_index+1]<=exponent[bit_index];
      end
    end
  end endgenerate
  anvil_q2_ht2_delay #(.WIDTH(1),.STAGES(53)) error_delay (
    .clk(clk),.rst_n(rst_n),.advance(advance),
    .s_data(bad_input),.m_data(delayed_error)
  );
  assign m_data=rst_n ? (delayed_error ? 32'h7fc00000 : result53) : 32'd0;
  assign m_error=rst_n && (delayed_error || error53);
endmodule
