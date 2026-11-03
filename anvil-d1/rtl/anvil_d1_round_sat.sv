module anvil_d1_round_sat #(
  parameter integer SHIFT=16,
  localparam integer S=(SHIFT>=0 && SHIFT<=96) ? SHIFT : 0
) (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire signed [127:0] in_value,
  output wire out_valid,
  input wire out_ready,
  output wire signed [31:0] out_value
);
  reg armed, valid;
  reg signed [31:0] result;
  wire signed [127:0] integral=in_value >>> S;
  wire increment;
  wire signed [32:0] rounded=$signed(integral[32:0])+$signed({32'd0,increment});
  wire signed [31:0] converted=integral>128'sd2147483647 ? 32'sh7fffffff :
    integral< -128'sd2147483648 ? 32'sh80000000 :
    rounded>33'sd2147483647 ? 32'sh7fffffff :
    rounded< -33'sd2147483648 ? 32'sh80000000 : rounded[31:0];
  generate
    if (SHIFT<0 || SHIFT>96) begin: invalid_parameters
      initial $fatal(1,"ANVIL_D1 PARAMETER ERROR: rounding shift");
    end
    if (S==0) begin: integral_only
      assign increment=1'b0;
    end else begin: fraction
      localparam [S-1:0] HALF={1'b1,{(S-1){1'b0}}};
      assign increment=in_value[127] ? in_value[S-1:0]>HALF : in_value[S-1:0]>=HALF;
    end
  endgenerate
  assign in_ready=rst_n && armed && !flush && !valid;
  assign out_valid=rst_n && !flush && valid;
  assign out_value=rst_n && !flush ? result : 32'sd0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin armed<=0; valid<=0; result<=0; end
    else begin
      armed<=1;
      if (flush) begin valid<=0; result<=0; end
      else begin
        if (out_valid && out_ready) valid<=0;
        if (in_valid && in_ready) begin result<=converted; valid<=1; end
      end
    end
  end
endmodule
