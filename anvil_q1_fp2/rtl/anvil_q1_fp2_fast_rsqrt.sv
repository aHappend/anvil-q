module anvil_q1_fp2_fast_rsqrt (
  input wire clk, rst_n, in_valid,
  input wire [31:0] x,
  output wire out_valid,
  output wire [31:0] result,
  output wire [4:0] status
);
  // Q32 integer construction of one magic-seed Newton update at each bin midpoint.
  // The initializer is elaboration-time ROM data, not a run-time multiplier datapath.
  function automatic [31:0] newton_entry(input integer index);
    reg [31:0] normalized_bits, seed_bits;
    reg [31:0] x_q30, y_q32, correction_q31, answer_q32;
    reg [63:0] yy, corrected;
    reg [95:0] xyy;
    reg [24:0] rounded;
    reg guard_bit, sticky_bit;
    integer shift;
    begin
      normalized_bits={1'b0,8'(127+(index>>10)),10'(index),13'h1000};
      seed_bits=32'h5f3759df-(normalized_bits>>1);
      x_q30={8'd0,1'b1,normalized_bits[22:0]} << (7+(index>>10));
      y_q32={8'd0,1'b1,seed_bits[22:0]} << ($signed({24'd0,seed_bits[30:23]})-118);
      yy=y_q32*y_q32;
      xyy={64'd0,x_q30}*{32'd0,yy};
      correction_q31=32'(64'hc0000000-(xyy>>64));
      corrected=y_q32*correction_q31;
      answer_q32=corrected[62:31];
      shift=answer_q32[31] ? 8 : 7;
      guard_bit=|(answer_q32 & (32'd1 << (shift-1)));
      sticky_bit=|(answer_q32 & ((32'd1 << (shift-1))-1));
      rounded={1'b0,24'(answer_q32 >> shift)}+
        {24'd0,guard_bit && (sticky_bit || answer_q32[shift])};
      if (rounded[24]) newton_entry={1'b0,8'(answer_q32[31] ? 127 : 126),23'd0};
      else newton_entry={1'b0,8'(answer_q32[31] ? 126 : 125),rounded[22:0]};
    end
  endfunction

  (* ramstyle = "M20K", nomem2reg *)
  reg [31:0] newton_lut [0:2047];
  integer entry;
  initial begin
    for (entry=0;entry<2048;entry=entry+1) newton_lut[entry]=newton_entry(entry);
  end
  reg valid0, valid1, special0;
  reg [31:0] seed0, special_value0, value1;
  reg [4:0] special_status0, status1;
  reg signed [9:0] power0;
  wire [23:0] input_sig={x[30:23]!=0,x[22:0]};
  wire [4:0] input_high=anvil_q1_fp2_pkg::leading24(input_sig);
  wire [23:0] normalized_sig=input_sig << (5'd23-input_high);
  wire signed [10:0] unbiased=x[30:23]==0 ?
    $signed({6'd0,input_high})-11'sd149 : $signed({3'd0,x[30:23]})-11'sd127;
  wire [10:0] lut_index={unbiased[0],normalized_sig[22:13]};
  wire signed [10:0] half_exponent=unbiased >>> 1;
  wire signed [11:0] result_exponent=
    $signed({4'd0,seed0[30:23]})-$signed({{2{power0[9]}},power0});
  reg next_special;
  reg [31:0] next_special_value;
  reg [4:0] next_special_status;
  always_comb begin
    next_special=1; next_special_value=0; next_special_status=0;
    if (x[30:23]==255 && x[22:0]!=0) begin
      next_special_value=32'h7fc00000; next_special_status[4]=!x[22];
    end else if (x[30:0]==0) begin
      next_special_value={x[31],8'hff,23'd0}; next_special_status[3]=1;
    end else if (x[31]) begin
      next_special_value=32'h7fc00000; next_special_status[4]=1;
    end else if (x[30:23]==255) next_special_value=0;
    else next_special=0;
  end
  assign out_valid=rst_n && valid1;
  assign result=out_valid ? value1 : 32'd0;
  assign status=out_valid ? status1 : 5'd0;
  always @(posedge clk) begin
    if (!rst_n) begin valid0<=0; valid1<=0; end
    else begin valid0<=in_valid; valid1<=valid0; end
  end
  always @(posedge clk) if (rst_n) begin
    seed0<=newton_lut[lut_index];
    power0<=half_exponent[9:0];
    special0<=next_special;
    special_value0<=next_special_value; special_status0<=next_special_status;
    if (valid0) begin
      value1<=special0 ? special_value0 : {1'b0,result_exponent[7:0],seed0[22:0]};
      status1<=special0 ? special_status0 : 5'b00001;
    end else begin value1<=0; status1<=0; end
  end
endmodule
