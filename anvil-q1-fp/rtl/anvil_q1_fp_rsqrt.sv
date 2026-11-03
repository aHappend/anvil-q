module anvil_q1_fp_rsqrt(
  input wire clk, rst_n, in_valid,
  input wire [31:0] x,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);
  wire [79:0] input_term;
  wire [23:0] input_significand;
  reg [23:0] valid;
  reg special [0:22];
  (* nomem2reg *) reg [31:0] special_value [0:22];
  (* nomem2reg *) reg [4:0] special_status [0:22];
  reg [47:0] radicand [0:12];
  reg [23:0] root [0:12];
  reg [25:0] root_remainder [0:12];
  reg signed [10:0] half_exponent [0:12];
  wire [97:0] square_root [1:12];
  wire [23:0] initial_denominator;
  wire [24:0] initial_remainder;
  wire [30:0] initial_quotient;
  reg [23:0] denominator [0:9];
  reg [24:0] remainder [0:9];
  reg [30:0] quotient [0:9];
  reg signed [10:0] exponent [0:9];
  reg root_lost [0:9];
  wire [55:0] division [0:9];
  wire signed [10:0] output_grid;
  wire [36:0] packed_result;
  reg [31:0] result_reg;
  reg [4:0] status_reg;
  integer i;
  genvar g;

  assign input_term=anvil_q1_fp_pkg::term32(x);
  assign input_significand=(input_term[63:40]!=0) ? input_term[63:40] : 24'h800000;
  assign initial_denominator=(root[12]!=0) ? root[12] : 24'h800000;
  assign initial_remainder=(initial_denominator==24'h800000) ? 25'd0 : 25'h0800000;
  assign initial_quotient=(initial_denominator==24'h800000) ? 31'd1 : 31'd0;
  assign division[0]=anvil_q1_fp_pkg::divide_steps(
    initial_denominator,initial_remainder,initial_quotient,2'd3);
  assign output_grid=-11'sd30-exponent[9];
  assign packed_result=anvil_q1_fp_pkg::pack_grid(
    {38'd0,quotient[9]},1'b0,output_grid,(remainder[9]!=0) || root_lost[9]);
  assign out_valid=rst_n && valid[23];
  assign result=(rst_n && valid[23]) ? result_reg : 32'd0;
  assign status=(rst_n && valid[23]) ? status_reg : 5'd0;
  generate
    for (g=1;g<13;g=g+1) begin: root_digits
      assign square_root[g]=anvil_q1_fp_pkg::sqrt_two_digits(
        radicand[g-1],root[g-1],root_remainder[g-1]);
    end
    for (g=1;g<10;g=g+1) begin: reciprocal_digits
      assign division[g]=anvil_q1_fp_pkg::divide_steps(
        denominator[g-1],remainder[g-1],quotient[g-1],2'd3);
    end
  endgenerate

  always @(posedge clk) begin
    if (!rst_n) begin
      valid<=0; result_reg<=0; status_reg<=0;
      for (i=0;i<23;i=i+1) begin
        special[i]<=0; special_value[i]<=0; special_status[i]<=0;
      end
      for (i=0;i<13;i=i+1) begin
        radicand[i]<=0; root[i]<=0; root_remainder[i]<=0; half_exponent[i]<=0;
      end
      for (i=0;i<10;i=i+1) begin
        denominator[i]<=0; remainder[i]<=0; quotient[i]<=0;
        exponent[i]<=0; root_lost[i]<=0;
      end
    end else begin
      valid<={valid[22:0],in_valid};
      special[0]<=0; special_value[0]<=0; special_status[0]<=0;
      if (input_term[78]) begin
        special[0]<=1; special_value[0]<=32'h7fc00000;
        special_status[0]<={input_term[79],4'd0};
      end else if (input_term[76]) begin
        special[0]<=1; special_value[0]<={x[31],8'hff,23'd0};
        special_status[0]<=5'b01000;
      end else if (x[31]) begin
        special[0]<=1; special_value[0]<=32'h7fc00000;
        special_status[0]<=5'b10000;
      end else if (input_term[77]) begin
        special[0]<=1; special_value[0]<=0;
      end
      for (i=1;i<23;i=i+1) begin
        special[i]<=special[i-1]; special_value[i]<=special_value[i-1];
        special_status[i]<=special_status[i-1];
      end

      radicand[0]<={24'd0,input_significand} << (input_term[64] ? 24 : 23);
      root[0]<=0; root_remainder[0]<=0;
      half_exponent[0]<=$signed(input_term[74:64]) >>> 1;
      for (i=1;i<13;i=i+1) begin
        radicand[i]<=square_root[i][97:50];
        root[i]<=square_root[i][49:26]; root_remainder[i]<=square_root[i][25:0];
        half_exponent[i]<=half_exponent[i-1];
      end

      denominator[0]<=initial_denominator;
      remainder[0]<=division[0][55:31]; quotient[0]<=division[0][30:0];
      exponent[0]<=half_exponent[12]; root_lost[0]<=root_remainder[12]!=0;
      for (i=1;i<10;i=i+1) begin
        denominator[i]<=denominator[i-1];
        remainder[i]<=division[i][55:31]; quotient[i]<=division[i][30:0];
        exponent[i]<=exponent[i-1]; root_lost[i]<=root_lost[i-1];
      end
      result_reg<=0; status_reg<=0;
      if (valid[22]) begin
        result_reg<=special[22] ? special_value[22] : packed_result[31:0];
        status_reg<=special[22] ? special_status[22] : packed_result[36:32];
      end
    end
  end
endmodule
