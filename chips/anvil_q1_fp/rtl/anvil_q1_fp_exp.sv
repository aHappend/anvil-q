module anvil_q1_fp_exp(
  input wire clk, rst_n, in_valid,
  input wire [31:0] x,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);
  localparam [31:0] C0=32'd1073741824, C1=32'd744261118;
  localparam [31:0] C2=32'd257941248, C3=32'd59597083;
  localparam [31:0] C4=32'd10327387, C5=32'd1431680, C6=32'd165394;
  wire [79:0] input_term;
  wire signed [10:0] input_exponent;
  reg [63:0] input_magnitude;
  reg signed [31:0] input_fixed;
  reg signed [31:0] fixed0;
  wire signed [63:0] reduction;
  reg [7:0] valid;
  reg special [0:6];
  reg [31:0] special_value [0:6];
  reg [4:0] special_status [0:6];
  reg [29:0] fraction [1:6];
  reg signed [10:0] exponent [1:6];
  reg [31:0] polynomial [2:6];
  wire [63:0] product [2:7];
  wire [63:0] final_polynomial;
  wire [24:0] rounded_significand;
  wire round_increment;
  wire signed [10:0] rounded_exponent;
  wire [7:0] encoded_exponent;
  wire [22:0] output_fraction;
  reg [31:0] result_reg;
  reg [4:0] status_reg;
  integer i;

  assign input_term=anvil_q1_fp_pkg::term32(x);
  assign input_exponent=$signed(input_term[74:64]);
  always @* begin
    input_magnitude=0; input_fixed=0;
    if (!input_term[78] && !input_term[77] && x[30:0]<=31'h42b20000) begin
      if (input_exponent>=-1)
        input_magnitude={40'd0,input_term[63:40]} << ($signed(32'(input_exponent))+1);
      else if (input_exponent>=-25)
        input_magnitude={40'd0,input_term[63:40]} >> (-$signed(32'(input_exponent))-1);
      input_fixed=$signed(input_magnitude[31:0]);
      if (x[31]) input_fixed=-input_fixed;
    end
  end
  assign reduction=$signed(fixed0)*64'sd1549082005;
  assign product[2]={34'd0,fraction[1]}*{32'd0,C6};
  assign product[3]={34'd0,fraction[2]}*{32'd0,polynomial[2]};
  assign product[4]={34'd0,fraction[3]}*{32'd0,polynomial[3]};
  assign product[5]={34'd0,fraction[4]}*{32'd0,polynomial[4]};
  assign product[6]={34'd0,fraction[5]}*{32'd0,polynomial[5]};
  assign product[7]={34'd0,fraction[6]}*{32'd0,polynomial[6]};
  assign final_polynomial=product[7]+{2'd0,C0,30'd0};
  assign round_increment=final_polynomial[36] &&
    ((|final_polynomial[35:0]) || final_polynomial[37]);
  assign rounded_significand={1'b0,final_polynomial[60:37]}+{24'd0,round_increment};
  assign rounded_exponent=exponent[6]+(rounded_significand[24] ? 11'sd1 : 11'sd0);
  assign encoded_exponent=8'(rounded_exponent+11'sd127);
  assign output_fraction=rounded_significand[24] ?
    rounded_significand[23:1] : rounded_significand[22:0];
  assign out_valid=rst_n && valid[7];
  assign result=(rst_n && valid[7]) ? result_reg : 32'd0;
  assign status=(rst_n && valid[7]) ? status_reg : 5'd0;

  always @(posedge clk) begin
    if (!rst_n) begin
      valid<=0; fixed0<=0; result_reg<=0; status_reg<=0;
      for (i=0;i<7;i=i+1) begin
        special[i]<=0; special_value[i]<=0; special_status[i]<=0;
      end
      for (i=1;i<7;i=i+1) begin fraction[i]<=0; exponent[i]<=0; end
      for (i=2;i<7;i=i+1) polynomial[i]<=0;
    end else begin
      valid<={valid[6:0],in_valid};
      fixed0<=input_fixed;
      special[0]<=0; special_value[0]<=0; special_status[0]<=0;
      if (input_term[78]) begin
        special[0]<=1; special_value[0]<=32'h7fc00000;
        special_status[0]<={input_term[79],4'd0};
      end else if (input_term[77]) begin
        special[0]<=1; special_value[0]<=x[31] ? 32'd0 : 32'h7f800000;
      end else if (x[30:0]==0) begin
        special[0]<=1; special_value[0]<=32'h3f800000;
      end else if (x[31] && x[30:0]>31'h42a00000) begin
        special[0]<=1; special_value[0]<=0; special_status[0]<=5'b00001;
      end else if (!x[31] && x[30:0]>31'h42b20000) begin
        special[0]<=1; special_value[0]<=32'h7f800000; special_status[0]<=5'b00101;
      end
      for (i=1;i<7;i=i+1) begin
        special[i]<=special[i-1]; special_value[i]<=special_value[i-1];
        special_status[i]<=special_status[i-1];
      end

      fraction[1]<=reduction[53:24];
      exponent[1]<=11'($signed(reduction) >>> 54);
      for (i=2;i<7;i=i+1) begin
        fraction[i]<=fraction[i-1]; exponent[i]<=exponent[i-1];
      end
      polynomial[2]<=product[2][61:30]+C5;
      polynomial[3]<=product[3][61:30]+C4;
      polynomial[4]<=product[4][61:30]+C3;
      polynomial[5]<=product[5][61:30]+C2;
      polynomial[6]<=product[6][61:30]+C1;

      result_reg<=0; status_reg<=0;
      if (valid[6]) begin
        if (special[6]) begin
          result_reg<=special_value[6]; status_reg<=special_status[6];
        end else if (rounded_exponent>127) begin
          result_reg<=32'h7f800000; status_reg<=5'b00101;
        end else begin
          result_reg<={1'b0,encoded_exponent,output_fraction};
          status_reg<=5'b00001;
        end
      end
    end
  end
endmodule
