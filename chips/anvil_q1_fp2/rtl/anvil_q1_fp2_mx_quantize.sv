module anvil_q1_fp2_mx_quantize (
  input wire clk, rst_n, in_valid,
  input wire [1023:0] bf16_data,
  input wire [63:0] lane_mask,
  output wire out_valid,
  output wire [511:0] mx_data,
  output wire [15:0] scales,
  output wire [4:0] status,
  output wire [6:0] saturation_events
);
  import anvil_q1_fp2_pkg::*;
  function automatic [7:0] choose_scale(input [14:0] peak);
    reg [7:0] significand;
    reg [7:0] normalized;
    integer high, exponent, power;
    begin
      significand={peak[14:7]!=0,peak[6:0]};
      high=integer'(leading16({8'd0,significand}));
      normalized=significand << (7-high);
      exponent=(peak[14:7]==0 ? -133 : integer'({1'b0,peak[14:7]})-134)+high;
      power=exponent-(normalized<=224 ? 8 : 7);
      if (peak==0 || power< -127) choose_scale=0;
      else choose_scale=8'(power+127);
    end
  endfunction
  // {saturation, flags, code}. Quantization and arithmetic conversion status
  // are intentionally separate; finite lossy rounding sets inexact.
  function automatic [13:0] encode(input [15:0] x, input [7:0] scale, input active);
    reg [7:0] sig;
    reg [15:0] kept, rounded;
    reg [7:0] code;
    reg [4:0] flags;
    reg guard_bit, sticky_bit, saturation;
    integer high, base, exponent, encoded_exponent, distance;
    begin
      sig={x[14:7]!=0,x[6:0]};
      high=integer'(leading16({8'd0,sig}));
      base=x[14:7]==0 ? -133 : integer'({1'b0,x[14:7]})-134;
      exponent=base+high-(integer'({1'b0,scale})-127);
      code={x[15],7'd0}; flags=0; saturation=0;
      kept=0; rounded=0; guard_bit=0; sticky_bit=0; distance=0; encoded_exponent=0;
      if (x[14:7]==255) begin
        if (x[6:0]!=0) begin code=8'h7f; flags[4]=!x[6]; end
        else begin code={x[15],7'h7e}; saturation=1; flags=5'b00101; end
      end else if (sig!=0) begin
        if (exponent>=-6) begin
          distance=high-3; encoded_exponent=exponent+7;
        end else begin
          distance=(integer'({1'b0,scale})-127)-9-base;
          encoded_exponent=0;
        end
        if (distance>0) begin
          if (distance<=16) begin
            kept={8'd0,sig} >> distance;
            guard_bit=|({8'd0,sig} & (16'd1 << (distance-1)));
            sticky_bit=|({8'd0,sig} & ((16'd1 << (distance-1))-1));
          end else sticky_bit=1;
        end else kept={8'd0,sig} << (-distance);
        rounded=kept+{15'd0,guard_bit && (sticky_bit || kept[0])};
        if (encoded_exponent!=0 && rounded>=16) begin
          rounded=rounded>>1; encoded_exponent=encoded_exponent+1;
        end
        if (encoded_exponent>15 || (encoded_exponent==15 && rounded>14)) begin
          code={x[15],7'h7e}; saturation=1; flags[0]=1;
        end else if (encoded_exponent==0) code={x[15],7'(rounded)};
        else code={x[15],4'(encoded_exponent),rounded[2:0]};
        flags[0]=flags[0] || guard_bit || sticky_bit;
        flags[1]=flags[0] && code[6:3]==0;
      end
      if (!active) begin code=0; flags=0; saturation=0; end
      encode={saturation,flags,code};
    end
  endfunction
  reg [8:0] valid;
  reg [1023:0] operands [0:6];
  reg [63:0] masks [0:6];
  (* nomem2reg *) reg [14:0] maxima0 [0:63];
  (* nomem2reg *) reg [14:0] maxima1 [0:31];
  (* nomem2reg *) reg [14:0] maxima2 [0:15];
  reg [14:0] maxima3 [0:7];
  reg [14:0] maxima4 [0:3];
  reg [14:0] maxima5 [0:1];
  reg [15:0] scale6, scale7, scale8;
  reg [511:0] encoded7, encoded8;
  (* nomem2reg *) reg [4:0] lane_flags7 [0:63];
  reg [63:0] lane_saturated7;
  reg [4:0] flags8;
  reg [6:0] saturations8;
  wire [13:0] encoded_lane [0:63];
  wire [4:0] flag_tree [0:126];
  wire [6:0] saturation_tree [0:126];
  integer i;
  genvar lane;
  generate for (lane=0;lane<64;lane=lane+1) begin: lanes
    assign encoded_lane[lane]=encode(operands[6][16*lane+:16],
      scale6[8*(lane>>5)+:8],masks[6][lane]);
    assign flag_tree[63+lane]=lane_flags7[lane];
    assign saturation_tree[63+lane]={6'd0,lane_saturated7[lane]};
  end
  for (lane=0;lane<63;lane=lane+1) begin: status_tree
    assign flag_tree[lane]=flag_tree[2*lane+1] | flag_tree[2*lane+2];
    assign saturation_tree[lane]=saturation_tree[2*lane+1]+saturation_tree[2*lane+2];
  end endgenerate
  assign out_valid=rst_n && valid[8];
  assign mx_data=out_valid ? encoded8 : 512'd0;
  assign scales=out_valid ? scale8 : 16'd0;
  assign status=out_valid ? flags8 : 5'd0;
  assign saturation_events=out_valid ? saturations8 : 7'd0;
  always @(posedge clk) begin
    if (!rst_n) valid<=0;
    else valid<={valid[7:0],in_valid};
  end
  always @(posedge clk) if (rst_n) begin
    operands[0]<=bf16_data; masks[0]<=lane_mask;
    for (i=1;i<7;i=i+1) begin operands[i]<=operands[i-1]; masks[i]<=masks[i-1]; end
    for (i=0;i<64;i=i+1)
      maxima0[i]<=lane_mask[i] && bf16_data[16*i+7+:8]!=255 ?
        bf16_data[16*i+:15] : 15'd0;
    for (i=0;i<32;i=i+1)
      maxima1[i]<=maxima0[2*i]>maxima0[2*i+1] ? maxima0[2*i] : maxima0[2*i+1];
    for (i=0;i<16;i=i+1)
      maxima2[i]<=maxima1[2*i]>maxima1[2*i+1] ? maxima1[2*i] : maxima1[2*i+1];
    for (i=0;i<8;i=i+1)
      maxima3[i]<=maxima2[2*i]>maxima2[2*i+1] ? maxima2[2*i] : maxima2[2*i+1];
    for (i=0;i<4;i=i+1)
      maxima4[i]<=maxima3[2*i]>maxima3[2*i+1] ? maxima3[2*i] : maxima3[2*i+1];
    for (i=0;i<2;i=i+1)
      maxima5[i]<=maxima4[2*i]>maxima4[2*i+1] ? maxima4[2*i] : maxima4[2*i+1];
    scale6<={choose_scale(maxima5[1]),choose_scale(maxima5[0])};
    scale7<=scale6;
    for (i=0;i<64;i=i+1) begin
      encoded7[8*i+:8]<=encoded_lane[i][7:0];
      lane_flags7[i]<=encoded_lane[i][12:8];
      lane_saturated7[i]<=encoded_lane[i][13];
    end
    encoded8<=encoded7; scale8<=scale7;
    flags8<=flag_tree[0]; saturations8<=saturation_tree[0];
  end
endmodule
