module anvil_b1_add #(
  parameter integer WIDTH=128,
  localparam integer W=(WIDTH>=1 && WIDTH<=256) ? WIDTH : 1,
  localparam integer SEGMENTS=(W+15)/16,
  localparam integer PAD=16*SEGMENTS
) (
  input wire clk, rst_n, flush, start, subtract,
  input wire [W-1:0] a, b,
  output wire ready, done,
  output wire [W-1:0] result,
  output wire carry_out
);
  reg busy, done_reg, carry, carry_reg, subtract_reg;
  reg [4:0] segment;
  reg [PAD-1:0] operand_a, operand_b, result_reg;
  wire [15:0] b_segment=operand_b[segment*16+:16] ^ {16{subtract_reg}};
  wire [16:0] sum={1'b0,operand_a[segment*16+:16]}+
    {1'b0,b_segment}+{16'd0,carry};
  generate if (WIDTH<1 || WIDTH>256) begin: invalid_parameters
    initial $fatal(1,"B1 PARAMETER ERROR: add WIDTH");
  end endgenerate
  assign ready=rst_n && !flush && !busy;
  assign done=rst_n && !flush && done_reg;
  assign result=rst_n && !flush ? result_reg[W-1:0] : {W{1'b0}};
  assign carry_out=rst_n && !flush && carry_reg;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      busy<=0; done_reg<=0; carry<=0; carry_reg<=0; subtract_reg<=0;
      segment<=0; operand_a<=0; operand_b<=0; result_reg<=0;
    end else if (flush) begin
      busy<=0; done_reg<=0; result_reg<=0; carry_reg<=0;
    end else begin
      done_reg<=0;
      if (start && ready) begin
        operand_a<={{(PAD-W){1'b0}},a};
        operand_b<={{(PAD-W){1'b0}},b};
        subtract_reg<=subtract; carry<=subtract; segment<=0; busy<=1;
      end else if (busy) begin
        result_reg[segment*16+:16]<=sum[15:0];
        carry<=sum[16];
        if (segment+1==SEGMENTS) begin
          carry_reg<=sum[W-16*(SEGMENTS-1)];
          busy<=0; done_reg<=1;
        end else segment<=segment+1'b1;
      end
    end
  end
endmodule
