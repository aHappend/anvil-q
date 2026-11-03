module anvil_q2_ht_add128_pipe (
  input wire clk, rst_n, advance,
  input wire signed [127:0] a, b,
  output wire signed [127:0] sum
);
  reg [127:0] a1, b1, a2, b2, a3, b3;
  reg [31:0] low1;
  reg [63:0] low2;
  reg [95:0] low3;
  reg carry1, carry2, carry3;
  reg signed [127:0] result;
  wire [32:0] part0 = {1'b0,a[31:0]}+{1'b0,b[31:0]};
  wire [32:0] part1 = {1'b0,a1[63:32]}+{1'b0,b1[63:32]}+{32'd0,carry1};
  wire [32:0] part2 = {1'b0,a2[95:64]}+{1'b0,b2[95:64]}+{32'd0,carry2};
  wire [32:0] part3 = {1'b0,a3[127:96]}+{1'b0,b3[127:96]}+{32'd0,carry3};
  assign sum = rst_n ? result : 128'sd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      a1 <= 0; b1 <= 0; a2 <= 0; b2 <= 0; a3 <= 0; b3 <= 0;
      low1 <= 0; low2 <= 0; low3 <= 0;
      carry1 <= 0; carry2 <= 0; carry3 <= 0; result <= 0;
    end else if (advance) begin
      a1 <= a; b1 <= b;
      low1 <= part0[31:0]; carry1 <= part0[32];
      a2 <= a1; b2 <= b1;
      low2 <= {part1[31:0],low1}; carry2 <= part1[32];
      a3 <= a2; b3 <= b2;
      low3 <= {part2[31:0],low2}; carry3 <= part2[32];
      result <= {part3[31:0],low3};
    end
  end
endmodule
