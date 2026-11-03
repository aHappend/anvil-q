module anvil_q1_fp_binary #(parameter MULTIPLY=0)(
  input wire clk, rst_n, in_valid,
  input wire [31:0] a, b,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);
  wire [79:0] first_term, second_term;
  wire [64:0] smaller_aligned, sum, difference, magnitude_next;
  wire invalid_next, nan_next, positive_inf_next, negative_inf_next;
  wire negative_zero_next;
  wire [36:0] packed_result;
  reg [79:0] larger1, smaller1;
  reg valid1, valid2, valid3;
  reg [68:0] magnitude2;
  reg signed [10:0] grid2;
  reg sign2, negative_zero2, lost2, special2;
  reg [31:0] special_value2, result3;
  reg [4:0] special_status2, status3;

  generate if (MULTIPLY) begin: multiply
    assign first_term=anvil_q1_fp_pkg::product32(a,b);
    assign second_term=80'd0;
  end else begin: add
    assign first_term=anvil_q1_fp_pkg::term32(a);
    assign second_term=anvil_q1_fp_pkg::term32(b);
  end endgenerate

  assign smaller_aligned=anvil_q1_fp_pkg::align_magnitude(
    smaller1,$signed(larger1[74:64]));
  assign sum={1'b0,larger1[63:0]}+{1'b0,smaller_aligned[63:0]};
  assign difference={1'b0,larger1[63:0]}-{1'b0,smaller_aligned[63:0]};
  assign magnitude_next=(MULTIPLY || larger1[75]==smaller1[75]) ? sum : difference;
  assign nan_next=larger1[78] || smaller1[78];
  assign positive_inf_next=(larger1[77] && !larger1[75]) ||
    (smaller1[77] && !smaller1[75]);
  assign negative_inf_next=(larger1[77] && larger1[75]) ||
    (smaller1[77] && smaller1[75]);
  assign invalid_next=larger1[79] || smaller1[79] ||
    (positive_inf_next && negative_inf_next);
  assign negative_zero_next=larger1[76] && larger1[75] &&
    (MULTIPLY || (smaller1[76] && smaller1[75]));
  assign packed_result=anvil_q1_fp_pkg::pack_grid(
    magnitude2,(magnitude2==0) ? negative_zero2 : sign2,grid2,lost2);
  assign out_valid=rst_n && valid3;
  assign result=(rst_n && valid3) ? result3 : 32'd0;
  assign status=(rst_n && valid3) ? status3 : 5'd0;

  always @(posedge clk) begin
    if (!rst_n) begin
      larger1<=0; smaller1<=0; valid1<=0; valid2<=0; valid3<=0;
      magnitude2<=0; grid2<=0; sign2<=0; negative_zero2<=0; lost2<=0;
      special2<=0; special_value2<=0; special_status2<=0;
      result3<=0; status3<=0;
    end else begin
      valid1<=in_valid;
      larger1<=0; smaller1<=0;
      if (in_valid) begin
        // IEEE magnitude codes order finite operands, including subnormals, before E0.
        if (!MULTIPLY && a[30:0]<b[30:0]) begin
          larger1<=second_term; smaller1<=first_term;
        end else begin
          larger1<=first_term; smaller1<=second_term;
        end
      end

      valid2<=valid1;
      magnitude2<=valid1 ? {4'd0,magnitude_next} : 69'd0;
      grid2<=(valid1 && larger1[63:0]!=0) ?
        $signed(larger1[74:64])-11'sd63 : 11'sd0;
      sign2<=valid1 && larger1[75];
      negative_zero2<=valid1 && negative_zero_next;
      lost2<=valid1 && smaller_aligned[64];
      special2<=valid1 &&
        (invalid_next || nan_next || positive_inf_next || negative_inf_next);
      special_value2<=0; special_status2<=0;
      if (valid1) begin
        if (invalid_next || nan_next) special_value2<=32'h7fc00000;
        else if (positive_inf_next || negative_inf_next)
          special_value2<={negative_inf_next,8'hff,23'd0};
        special_status2<={invalid_next,4'd0};
      end

      valid3<=valid2;
      result3<=0; status3<=0;
      if (valid2) begin
        result3<=special2 ? special_value2 : packed_result[31:0];
        status3<=special2 ? special_status2 : packed_result[36:32];
      end
    end
  end
endmodule

module anvil_q1_fp_add(
  input wire clk, rst_n, in_valid,
  input wire [31:0] a, b,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);
  anvil_q1_fp_binary #(0) pipeline(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.a(a),.b(b),
    .out_valid(out_valid),.result(result),.status(status)
  );
endmodule

module anvil_q1_fp_mul(
  input wire clk, rst_n, in_valid,
  input wire [31:0] a, b,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);
  anvil_q1_fp_binary #(1) pipeline(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.a(a),.b(b),
    .out_valid(out_valid),.result(result),.status(status)
  );
endmodule
