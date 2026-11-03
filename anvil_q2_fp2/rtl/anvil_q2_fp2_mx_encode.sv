module anvil_q2_fp2_bf16_round (
  input wire [31:0] in_fp32,
  output wire [15:0] out_bf16,
  output wire out_error
);
  wire nan_input=(&in_fp32[30:23]) && (|in_fp32[22:0]);
  wire round_up=in_fp32[15] && ((|in_fp32[14:0]) || in_fp32[16]);
  wire [15:0] rounded=in_fp32[31:16]+{15'd0,round_up};
  assign out_bf16=nan_input ? 16'h7fc0 : rounded;
  assign out_error=(&in_fp32[30:23]) || (&out_bf16[14:7]);
endmodule

module anvil_q2_fp2_mx_encode_lane (
  input wire [15:0] in_bf16,
  input wire [7:0] in_scale,
  output reg [7:0] out_payload,
  output reg out_error
);
  reg [7:0] significand, normalized;
  reg [8:0] rounded, truncated;
  reg [2:0] top;
  reg guard_bit, sticky;
  reg signed [12:0] exponent, unbiased, shift, scale;
  reg [3:0] encoded;
  always @* begin
    significand={|in_bf16[14:7],in_bf16[6:0]};
    top=0;
    if (significand[7]) top=7;
    else if (significand[6]) top=6;
    else if (significand[5]) top=5;
    else if (significand[4]) top=4;
    else if (significand[3]) top=3;
    else if (significand[2]) top=2;
    else if (significand[1]) top=1;
    normalized=significand << (3'd7-top);
    exponent=in_bf16[14:7]==0 ? -13'sd133 :
      $signed({5'd0,in_bf16[14:7]})-13'sd134;
    scale=$signed({5'd0,in_scale})-13'sd127;
    unbiased=exponent+$signed({10'd0,top})-scale;
    shift=scale-exponent-13'sd9;
    rounded=0;
    truncated=0;
    guard_bit=0;
    sticky=0;
    encoded=0;
    out_payload={in_bf16[15],7'd0};
    out_error=0;
    if ((&in_bf16[14:7]) || in_scale==255) begin
      out_payload=8'h7f;
      out_error=1;
    end else if (significand!=0) begin
      if (unbiased < -13'sd6) begin
        if (shift<=0) truncated={1'b0,significand} << (-shift);
        else if (shift<=8) begin
          truncated={1'b0,significand} >> shift[3:0];
          guard_bit=|(significand & (8'd1 << (shift[3:0]-4'd1)));
          if (shift>1)
            sticky=|(significand & (8'hff >> (5'd9-{1'b0,shift[3:0]})));
        end else sticky=|significand;
        rounded=truncated+{8'd0,(guard_bit && (sticky || truncated[0]))};
        out_payload={in_bf16[15],rounded[6:0]};
      end else begin
        rounded={5'd0,normalized[7:4]}+
          {8'd0,(normalized[3] && ((|normalized[2:0]) || normalized[4]))};
        if (rounded[4]) begin
          rounded=rounded >> 1;
          unbiased=unbiased+13'sd1;
        end
        encoded=unbiased[3:0]+4'd7;
        if (unbiased>13'sd8 || (unbiased==13'sd8 && rounded[3:0]>14)) begin
          out_payload=8'h7f;
          out_error=1;
        end else out_payload={in_bf16[15],encoded,rounded[2:0]};
      end
    end
  end
endmodule

module anvil_q2_fp2_mx_encode32 (
  input wire clk, rst_n, flush,
  input wire in_valid,
  output wire in_ready,
  input wire [511:0] in_bf16,
  input wire [31:0] in_mask,
  input wire [31:0] in_tag,
  output wire out_valid,
  input wire out_ready,
  output wire [255:0] out_payload,
  output wire [7:0] out_scale,
  output wire [31:0] out_tag,
  output wire out_error
);
  wire [14:0] maximum [0:62];
  wire [31:0] nonfinite;
  wire [511:0] masked;
  genvar lane, node;
  generate
    for (lane=0;lane<32;lane=lane+1) begin: inputs
      assign masked[16*lane+:16]=in_mask[lane] ? in_bf16[16*lane+:16] : 16'd0;
      assign maximum[31+lane]=masked[16*lane+:15];
      assign nonfinite[lane]=&masked[16*lane+7+:8];
    end
    for (node=0;node<31;node=node+1) begin: maxima
      assign maximum[node]=maximum[2*node+1]>=maximum[2*node+2] ?
        maximum[2*node+1] : maximum[2*node+2];
    end
  endgenerate
  reg [2:0] valid;
  reg [1:0] error_pipe;
  reg error2;
  reg [14:0] max0;
  reg [511:0] data0, data1;
  reg [31:0] tag0, tag1, tag2;
  reg [7:0] scale1, scale2;
  reg [255:0] payload2;
  wire enable=!valid[2] || out_ready;
  reg [7:0] magnitude;
  reg [2:0] top;
  reg signed [12:0] exponent, binary_scale;
  reg [7:0] selected_scale;
  always @* begin
    magnitude={|max0[14:7],max0[6:0]};
    top=0;
    if (magnitude[7]) top=7;
    else if (magnitude[6]) top=6;
    else if (magnitude[5]) top=5;
    else if (magnitude[4]) top=4;
    else if (magnitude[3]) top=3;
    else if (magnitude[2]) top=2;
    else if (magnitude[1]) top=1;
    exponent=max0[14:7]==0 ? -13'sd133 :
      $signed({5'd0,max0[14:7]})-13'sd134;
    magnitude=magnitude << (3'd7-top);
    binary_scale=exponent+$signed({10'd0,top})-
      (magnitude<=8'd224 ? 13'sd8 : 13'sd7);
    if (binary_scale < -13'sd127) binary_scale=-13'sd127;
    selected_scale=max0==0 ? 8'd127 : binary_scale[7:0]+8'd127;
  end
  wire [255:0] encoded;
  wire [31:0] lane_error;
  generate for (lane=0;lane<32;lane=lane+1) begin: encoders
    anvil_q2_fp2_mx_encode_lane encoder (
      .in_bf16(data1[16*lane+:16]),.in_scale(scale1),
      .out_payload(encoded[8*lane+:8]),.out_error(lane_error[lane])
    );
  end endgenerate
  assign in_ready=rst_n && !flush && enable;
  assign out_valid=rst_n && !flush && valid[2];
  assign out_payload=out_valid ? payload2 : 256'd0;
  assign out_scale=out_valid ? scale2 : 8'd0;
  assign out_tag=out_valid ? tag2 : 32'd0;
  assign out_error=out_valid && error2;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid<=0;
      error_pipe<=0;
      error2<=0;
      max0<=0;
      data0<=0;
      data1<=0;
      tag0<=0; tag1<=0; tag2<=0;
      scale1<=0; scale2<=0;
      payload2<=0;
    end else if (flush) valid<=0;
    else if (enable) begin
      valid<={valid[1:0],in_valid};
      if (in_valid) begin
        data0<=masked;
        max0<=maximum[0];
        tag0<=in_tag;
        error_pipe[0]<=|nonfinite;
      end
      if (valid[0]) begin
        data1<=data0;
        scale1<=selected_scale;
        tag1<=tag0;
        error_pipe[1]<=error_pipe[0];
      end
      if (valid[1]) begin
        payload2<=encoded;
        scale2<=scale1;
        tag2<=tag1;
        error2<=error_pipe[1] || (|lane_error);
      end
    end
  end
endmodule
