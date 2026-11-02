module anvil_q1_fp2_reciprocal (
  input wire clk, rst_n, in_valid,
  input wire [31:0] x,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);

  // Q1.31 endpoint values for 1/(1+i/1024). Only constant ROM generation
  // performs long division; the runtime datapath is a linear interpolation.
  function automatic [31:0] endpoint(input integer index);
    reg [42:0] remainder;
    reg [31:0] quotient;
    integer bit_index;
    begin
      remainder=43'd1 << 41; quotient=0;
      for (bit_index=31;bit_index>=0;bit_index=bit_index-1)
        if (remainder >= (43'(1024+index) << bit_index)) begin
          remainder=remainder-(43'(1024+index) << bit_index);
          quotient[bit_index]=1;
        end
      endpoint=quotient;
    end
  endfunction
  (* ramstyle = "M20K", nomem2reg *)
  reg [31:0] lut_low [0:1023];
  (* ramstyle = "M20K", nomem2reg *)
  reg [31:0] lut_high [0:1023];
  integer entry;
  initial begin
    for (entry=0;entry<1024;entry=entry+1) begin
      lut_low[entry]=endpoint(entry);
      lut_high[entry]=endpoint(entry+1);
    end
  end
  wire [23:0] sig={x[30:23]!=0,x[22:0]};
  wire [4:0] high=anvil_q1_fp2_pkg::leading24(sig);
  wire [23:0] normalized=sig << (5'd23-high);
  wire signed [10:0] input_exponent=x[30:23]==0 ?
    $signed({6'd0,high})-11'sd149 :
    $signed({3'd0,x[30:23]})-11'sd127;
  reg [5:0] valid;
  reg [31:0] low0, high0, base1, base2, interpolated3;
  reg [12:0] fraction0, fraction1;
  reg [31:0] delta1;
  reg [44:0] product2;
  reg signed [10:0] exponent [0:3];
  reg sign [0:4], special [0:4];
  reg [31:0] special_value [0:4];
  reg [4:0] special_status [0:4];
  reg zero4, normal4, guard4, sticky4;
  reg [23:0] kept4;
  reg signed [11:0] biased4;
  reg [31:0] value5;
  reg [4:0] flags5;
  wire [4:0] interpolated_high=interpolated3[31] ? 5'd31 : 5'd30;
  wire signed [11:0] biased_next=
    $signed({7'd0,interpolated_high})-12'sd31-
    $signed({exponent[3][10],exponent[3]})+12'sd127;
  reg [31:0] shifted;
  reg [23:0] kept_next;
  reg guard_next, sticky_next;
  integer distance, i;
  wire [36:0] packed_value=anvil_q1_fp2_pkg::pack_fp32(9'd0,sign[4],zero4,normal4,
    biased4,kept4,guard4,sticky4);
  always @* begin
    distance=biased_next>0 ? $signed({27'd0,interpolated_high})-23 :
      $signed({{21{exponent[3][10]}},exponent[3]})-118;
    shifted=interpolated3 >> distance;
    kept_next=shifted[23:0];
    guard_next=distance>0 && |(interpolated3 & (32'd1 << (distance-1)));
    sticky_next=distance>1 && |(interpolated3 & ((32'd1 << (distance-1))-1));
  end
  assign out_valid=rst_n && valid[5];
  assign result=out_valid ? value5 : 32'd0;
  assign status=out_valid ? flags5 : 5'd0;
  always @(posedge clk) begin
    if (!rst_n) valid<=0;
    else valid<={valid[4:0],in_valid};
  end
  always @(posedge clk) if (rst_n) begin
    low0<=lut_low[normalized[22:13]];
    high0<=lut_high[normalized[22:13]];
    fraction0<=normalized[12:0]; exponent[0]<=input_exponent;
    sign[0]<=x[31]; special[0]<=1;
    special_value[0]<=0; special_status[0]<=0;
    if (x[30:23]==255 && x[22:0]!=0) begin
      special_value[0]<=32'h7fc00000; special_status[0][4]<=!x[22];
    end else if (x[30:0]==0) begin
      special_value[0]<={x[31],8'hff,23'd0}; special_status[0][3]<=1;
    end else if (x[30:23]==255) special_value[0]<={x[31],31'd0};
    else special[0]<=0;
    for (i=1;i<5;i=i+1) begin
      sign[i]<=sign[i-1]; special[i]<=special[i-1];
      special_value[i]<=special_value[i-1]; special_status[i]<=special_status[i-1];
    end
    for (i=1;i<4;i=i+1) exponent[i]<=exponent[i-1];
    base1<=low0; delta1<=low0-high0; fraction1<=fraction0;
    product2<=delta1*fraction1; base2<=base1;
    interpolated3<=base2-32'((product2+45'd4096)>>13);
    normal4<=biased_next>0; zero4<=0; biased4<=biased_next;
    kept4<=kept_next; guard4<=guard_next; sticky4<=sticky_next;
    value5<=special[4] ? special_value[4] : packed_value[31:0];
    flags5<=special[4] ? special_status[4] :
      (packed_value[36:32] | 5'b00001);
  end
endmodule
