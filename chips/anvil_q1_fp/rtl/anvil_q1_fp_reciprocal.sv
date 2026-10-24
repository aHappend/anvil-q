module anvil_q1_fp_reciprocal(
  input wire clk, rst_n, in_valid,
  input wire [31:0] x,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);
  wire [79:0] input_term;
  wire [23:0] input_denominator;
  reg [15:0] valid;
  reg [23:0] denominator [0:14];
  reg [24:0] remainder [0:14];
  reg [30:0] quotient [0:14];
  reg signed [10:0] exponent [0:14];
  reg sign [0:14];
  reg special [0:14];
  reg [31:0] special_value [0:14];
  reg [4:0] special_status [0:14];
  wire [55:0] division [1:14];
  wire signed [10:0] output_grid;
  wire [36:0] packed_result;
  reg [31:0] result_reg;
  reg [4:0] status_reg;
  integer i;
  genvar g;
  assign input_term=anvil_q1_fp_pkg::term32(x);
  assign input_denominator=(input_term[63:40]!=0) ? input_term[63:40] : 24'h800000;
  assign output_grid=-11'sd28-exponent[14];
  assign packed_result=anvil_q1_fp_pkg::pack_grid(
    {38'd0,quotient[14]},sign[14],output_grid,remainder[14]!=0);
  assign out_valid=rst_n && valid[15];
  assign result=(rst_n && valid[15]) ? result_reg : 32'd0;
  assign status=(rst_n && valid[15]) ? status_reg : 5'd0;
  generate for (g=1;g<15;g=g+1) begin: digits
    assign division[g]=anvil_q1_fp_pkg::divide_steps(
      denominator[g-1],remainder[g-1],quotient[g-1],2'd2);
  end endgenerate

  always @(posedge clk) begin
    if (!rst_n) begin
      valid<=0; result_reg<=0; status_reg<=0;
      for (i=0;i<15;i=i+1) begin
        denominator[i]<=0; remainder[i]<=0; quotient[i]<=0;
        exponent[i]<=0; sign[i]<=0; special[i]<=0;
        special_value[i]<=0; special_status[i]<=0;
      end
    end else begin
      valid<={valid[14:0],in_valid};
      denominator[0]<=input_denominator;
      remainder[0]<=input_denominator==24'h800000 ? 25'd0 : 25'h0800000;
      quotient[0]<=input_denominator==24'h800000 ? 31'd1 : 31'd0;
      exponent[0]<=$signed(input_term[74:64]);
      sign[0]<=x[31]; special[0]<=0; special_value[0]<=0; special_status[0]<=0;
      if (input_term[78]) begin
        special[0]<=1; special_value[0]<=32'h7fc00000;
        special_status[0]<={input_term[79],4'd0};
      end else if (input_term[76]) begin
        special[0]<=1; special_value[0]<={x[31],8'hff,23'd0};
        special_status[0]<=5'b01000;
      end else if (input_term[77]) begin
        special[0]<=1; special_value[0]<={x[31],31'd0};
      end
      for (i=1;i<15;i=i+1) begin
        denominator[i]<=denominator[i-1];
        remainder[i]<=division[i][55:31]; quotient[i]<=division[i][30:0];
        exponent[i]<=exponent[i-1]; sign[i]<=sign[i-1];
        special[i]<=special[i-1]; special_value[i]<=special_value[i-1];
        special_status[i]<=special_status[i-1];
      end
      result_reg<=0; status_reg<=0;
      if (valid[14]) begin
        result_reg<=special[14] ? special_value[14] : packed_result[31:0];
        status_reg<=special[14] ? special_status[14] : packed_result[36:32];
      end
    end
  end
endmodule
