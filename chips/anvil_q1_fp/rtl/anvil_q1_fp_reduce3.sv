module anvil_q1_fp_reduce3(
  input wire clk, rst_n, in_valid,
  input wire [719:0] terms,
  input wire [8:0] active,
  input wire force_invalid,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);
  reg valid1, valid2, valid3;
  reg [79:0] terms1 [0:8];
  reg [8:0] active1;
  reg invalid1;
  wire signed [10:0] maxima [1:31];
  wire [69:0] aligned [0:8];
  reg signed [68:0] terms2 [0:8];
  reg signed [10:0] grid2;
  reg special2, negative_zero2, lost2;
  reg [31:0] special_value2;
  reg [4:0] special_status2;
  reg invalid_next, nan_next, pos_inf_next, neg_inf_next;
  reg negative_zero_next, any_active_next, lost_next;
  wire [68:0] sum1 [0:2], carry1 [0:2];
  wire [68:0] sum2 [0:1], carry2 [0:1];
  wire [68:0] sum3, carry3, sum4, carry4;
  wire [68:0] negative_sum, negative_carry;
  wire [68:0] total, negative_total;
  wire [68:0] magnitude;
  wire finite_sign;
  wire [36:0] packed_result;
  reg [31:0] result3;
  reg [4:0] status3;
  integer i, j;
  genvar g;

  // Resolve only local eight-bit carries; a parallel prefix supplies block carries.
  function automatic [68:0] resolve69(input [68:0] a, b);
    reg [71:0] padded_a, padded_b, resolved;
    reg [80:0] select0, select1;
    reg [8:0] generates [0:4];
    reg [8:0] propagates [0:4];
    integer block_index, level;
    begin
      padded_a={3'd0,a}; padded_b={3'd0,b};
      select0=0; select1=0; resolved=0;
      generates[0]=0; propagates[0]=0;
      for (block_index=0;block_index<9;block_index=block_index+1) begin
        select0[block_index*9+:9]=
          {1'b0,padded_a[block_index*8+:8]}+
          {1'b0,padded_b[block_index*8+:8]};
        select1[block_index*9+:9]=
          {1'b0,padded_a[block_index*8+:8]}+
          {1'b0,padded_b[block_index*8+:8]}+9'd1;
        generates[0][block_index]=select0[block_index*9+8];
        propagates[0][block_index]=
          &(padded_a[block_index*8+:8]^padded_b[block_index*8+:8]);
      end
      for (level=0;level<4;level=level+1) begin
        generates[level+1]=generates[level];
        propagates[level+1]=propagates[level];
        for (block_index=0;block_index<9;block_index=block_index+1) begin
          if (block_index>=(1<<level)) begin
            generates[level+1][block_index]=generates[level][block_index] |
              (propagates[level][block_index] &&
               generates[level][block_index-(1<<level)]);
            propagates[level+1][block_index]=propagates[level][block_index] &&
              propagates[level][block_index-(1<<level)];
          end
        end
      end
      resolved[7:0]=select0[7:0];
      for (block_index=1;block_index<9;block_index=block_index+1)
        resolved[block_index*8+:8]=generates[4][block_index-1] ?
          select1[block_index*9+:8] : select0[block_index*9+:8];
      resolve69=resolved[68:0];
    end
  endfunction

  generate
    for (g=0;g<16;g=g+1) begin: leaves
      if (g<9) begin: populated
        assign maxima[16+g]=(active1[g] && terms1[g][63:0]!=0) ?
          $signed(terms1[g][74:64]) : -11'sd1023;
        assign aligned[g]=anvil_q1_fp_pkg::align_term(terms1[g],maxima[1]);
      end else begin: padding
        assign maxima[16+g]=-11'sd1023;
      end
    end
    for (g=1;g<16;g=g+1) begin: trees
      assign maxima[g]=(maxima[2*g]>maxima[2*g+1]) ?
        maxima[2*g] : maxima[2*g+1];
    end
    // Four exact 3:2 compressor levels reduce nine signed terms to two.
    for (g=0;g<3;g=g+1) begin: compressors
      assign sum1[g]=terms2[3*g]^terms2[3*g+1]^terms2[3*g+2];
      assign carry1[g]=((terms2[3*g]&terms2[3*g+1]) |
        (terms2[3*g]&terms2[3*g+2]) |
        (terms2[3*g+1]&terms2[3*g+2])) << 1;
    end
  endgenerate

  assign sum2[0]=sum1[0]^carry1[0]^sum1[1];
  assign carry2[0]=((sum1[0]&carry1[0]) | (sum1[0]&sum1[1]) |
    (carry1[0]&sum1[1])) << 1;
  assign sum2[1]=carry1[1]^sum1[2]^carry1[2];
  assign carry2[1]=((carry1[1]&sum1[2]) | (carry1[1]&carry1[2]) |
    (sum1[2]&carry1[2])) << 1;
  assign sum3=sum2[0]^carry2[0]^sum2[1];
  assign carry3=((sum2[0]&carry2[0]) | (sum2[0]&sum2[1]) |
    (carry2[0]&sum2[1])) << 1;
  assign sum4=sum3^carry3^carry2[1];
  assign carry4=((sum3&carry3) | (sum3&carry2[1]) |
    (carry3&carry2[1])) << 1;

  // -(sum4+carry4) = ~sum4 + ~carry4 + 2, modulo 2^69.
  // Resolve both signs in parallel rather than negate a resolved wide sum.
  assign negative_sum=sum4^carry4^69'd2;
  assign negative_carry=((~sum4&~carry4) |
    ((~sum4|~carry4)&69'd2)) << 1;
  assign total=resolve69(sum4,carry4);
  assign negative_total=resolve69(negative_sum,negative_carry);

  always @* begin
    invalid_next=invalid1; nan_next=0; pos_inf_next=0; neg_inf_next=0;
    negative_zero_next=1; any_active_next=0; lost_next=0;
    for (j=0;j<9;j=j+1) begin
      if (active1[j]) begin
        any_active_next=1;
        invalid_next=invalid_next || terms1[j][79];
        nan_next=nan_next || terms1[j][78];
        pos_inf_next=pos_inf_next || (terms1[j][77] && !terms1[j][75]);
        neg_inf_next=neg_inf_next || (terms1[j][77] && terms1[j][75]);
        negative_zero_next=negative_zero_next && terms1[j][76] && terms1[j][75];
        lost_next=lost_next || aligned[j][69];
      end
    end
    invalid_next=invalid_next || (pos_inf_next && neg_inf_next);
    negative_zero_next=negative_zero_next && any_active_next;
  end

  assign magnitude=total[68] ? negative_total : total;
  assign finite_sign=(total==0) ? negative_zero2 : total[68];
  assign packed_result=anvil_q1_fp_pkg::pack_grid(magnitude,finite_sign,grid2,lost2);
  assign out_valid=rst_n && valid3;
  assign result=(rst_n && valid3) ? result3 : 32'd0;
  assign status=(rst_n && valid3) ? status3 : 5'd0;

  always @(posedge clk) begin
    if (!rst_n) begin
      valid1<=0; valid2<=0; valid3<=0; active1<=0; invalid1<=0;
      grid2<=0; special2<=0; special_value2<=0; special_status2<=0;
      negative_zero2<=0; lost2<=0; result3<=0; status3<=0;
      for (i=0;i<9;i=i+1) begin terms1[i]<=0; terms2[i]<=0; end
    end else begin
      valid1<=in_valid;
      active1<=in_valid ? active : 9'd0;
      invalid1<=in_valid && force_invalid;
      for (i=0;i<9;i=i+1)
        terms1[i]<=(in_valid && active[i]) ? terms[i*80+:80] : 80'd0;

      valid2<=valid1;
      for (i=0;i<9;i=i+1)
        terms2[i]<=(valid1 && active1[i]) ? aligned[i][68:0] : 69'd0;
      grid2<=(valid1 && maxima[1]!=-11'sd1023) ? maxima[1]-11'sd63 : 11'sd0;
      special2<=valid1 && (invalid_next || nan_next || pos_inf_next || neg_inf_next);
      special_value2<=0;
      special_status2<=0;
      if (valid1) begin
        if (invalid_next || nan_next) special_value2<=32'h7fc00000;
        else if (pos_inf_next || neg_inf_next)
          special_value2<={neg_inf_next,8'hff,23'd0};
        special_status2<={invalid_next,4'd0};
      end
      negative_zero2<=valid1 && negative_zero_next;
      lost2<=valid1 && lost_next;

      valid3<=valid2;
      result3<=0; status3<=0;
      if (valid2) begin
        result3<=special2 ? special_value2 : packed_result[31:0];
        status3<=special2 ? special_status2 : packed_result[36:32];
      end
    end
  end
endmodule
