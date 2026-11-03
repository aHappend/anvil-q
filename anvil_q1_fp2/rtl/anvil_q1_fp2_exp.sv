module anvil_q1_fp2_exp (
  input wire clk, rst_n, in_valid,
  input wire [31:0] x,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);
  // exp(x)=2^(n+f), with signed floor reduction and f in [0,1).
  // Coefficients are RNE Q2.30 values of ln(2)^j/j!, j=0..6.
  localparam [31:0] C0=32'd1073741824, C1=32'd744261118;
  localparam [31:0] C2=32'd257941248, C3=32'd59597083;
  localparam [31:0] C4=32'd10327387, C5=32'd1431680, C6=32'd165394;
  wire [23:0] sig={x[30:23]!=0,x[22:0]};
  wire signed [10:0] scale=x[30:23]==0 ? -11'sd125 :
    $signed({3'd0,x[30:23]})-11'sd126;
  reg [31:0] magnitude;
  reg signed [31:0] fixed_input, fixed0;
  wire signed [63:0] reduced=$signed(fixed0)*64'sd1549082005;
  reg [7:0] valid;
  reg special [0:6];
  reg [31:0] special_value [0:6];
  reg [4:0] special_status [0:6];
  reg [29:0] fraction [1:6];
  reg signed [10:0] exponent [1:6];
  reg [31:0] polynomial [2:6];
  wire [63:0] product [2:7];
  wire [63:0] final_polynomial=product[7]+{2'd0,C0,30'd0};
  wire [24:0] rounded={1'b0,final_polynomial[60:37]}+
    {24'd0,final_polynomial[36] &&
      ((|final_polynomial[35:0]) || final_polynomial[37])};
  wire signed [10:0] final_exponent=exponent[6]+
    (rounded[24] ? 11'sd1 : 11'sd0);
  reg [31:0] value7;
  reg [4:0] flags7;
  integer i;
  always @* begin
    magnitude=0;
    if (x[30:23]!=255 && x[30:0]<=31'h42a00000) begin
      if (scale>=0) magnitude={8'd0,sig} << scale;
      else magnitude={8'd0,sig} >> (-scale);
    end
    fixed_input=x[31] ? -$signed(magnitude) : $signed(magnitude);
  end
  assign product[2]={34'd0,fraction[1]}*{32'd0,C6};
  assign product[3]={34'd0,fraction[2]}*{32'd0,polynomial[2]};
  assign product[4]={34'd0,fraction[3]}*{32'd0,polynomial[3]};
  assign product[5]={34'd0,fraction[4]}*{32'd0,polynomial[4]};
  assign product[6]={34'd0,fraction[5]}*{32'd0,polynomial[5]};
  assign product[7]={34'd0,fraction[6]}*{32'd0,polynomial[6]};
  assign out_valid=rst_n && valid[7];
  assign result=out_valid ? value7 : 32'd0;
  assign status=out_valid ? flags7 : 5'd0;
  always @(posedge clk) begin
    if (!rst_n) valid<=0;
    else valid<={valid[6:0],in_valid};
  end
  always @(posedge clk) if (rst_n) begin
    fixed0<=fixed_input;
    special[0]<=1; special_value[0]<=0; special_status[0]<=0;
    if (x[30:23]==255 && x[22:0]!=0) begin
      special_value[0]<=32'h7fc00000; special_status[0][4]<=!x[22];
    end else if (x[30:23]==255) begin
      special_value[0]<=x[31] ? 32'd0 : 32'h7f800000;
    end else if (x[30:0]==0) special_value[0]<=32'h3f800000;
    else if (x[30:0]>31'h42a00000) begin
      // The public supported finite range is [-80,80]. Negative tails
      // are intentionally saturated; positive out-of-range values are errors.
      special_value[0]<=x[31] ? 32'd0 : 32'h7f800000;
      special_status[0]<=x[31] ? 5'b00001 : 5'b00101;
    end else special[0]<=0;
    for (i=1;i<7;i=i+1) begin
      special[i]<=special[i-1]; special_value[i]<=special_value[i-1];
      special_status[i]<=special_status[i-1];
    end
    fraction[1]<=reduced[53:24];
    exponent[1]<=11'($signed(reduced) >>> 54);
    for (i=2;i<7;i=i+1) begin
      fraction[i]<=fraction[i-1]; exponent[i]<=exponent[i-1];
    end
    polynomial[2]<=product[2][61:30]+C5;
    polynomial[3]<=product[3][61:30]+C4;
    polynomial[4]<=product[4][61:30]+C3;
    polynomial[5]<=product[5][61:30]+C2;
    polynomial[6]<=product[6][61:30]+C1;
    value7<=special[6] ? special_value[6] :
      {1'b0,8'(final_exponent+11'sd127),
        (rounded[24] ? rounded[23:1] : rounded[22:0])};
    flags7<=special[6] ? special_status[6] : 5'b00001;
  end
endmodule
