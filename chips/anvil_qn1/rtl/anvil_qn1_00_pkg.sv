package anvil_qn1_pkg;
  localparam [31:0] EPSILON32 = 32'h358637bd;

  function automatic fp32_invalid(input logic [31:0] value);
    fp32_invalid = value[30:23] == 8'hff;
  endfunction

  function automatic bf16_invalid(input logic [15:0] value);
    bf16_invalid = value[14:7] == 8'hff;
  endfunction

  function automatic bf16_scale_invalid(input logic [15:0] value);
    bf16_scale_invalid = bf16_invalid(value) ||
      (value[15] && value[14:0] != 0);
  endfunction

  function automatic [5:0] leading_zero32(input logic [31:0] value);
    reg [31:0] part;
    reg [5:0] count;
    begin
      part = value;
      count = 0;
      if (part[31:16] == 0) begin count = count + 16; part = part << 16; end
      if (part[31:24] == 0) begin count = count + 8; part = part << 8; end
      if (part[31:28] == 0) begin count = count + 4; part = part << 4; end
      if (part[31:30] == 0) begin count = count + 2; part = part << 2; end
      if (!part[31]) count = count + 1;
      leading_zero32 = value == 0 ? 6'd32 : count;
    end
  endfunction

  function automatic [26:0] shift_jam27(
    input logic [26:0] value, input logic [11:0] distance
  );
    reg [26:0] shifted, discarded;
    begin
      if (distance == 0) shift_jam27 = value;
      else if (distance >= 27) shift_jam27 = {26'd0, |value};
      else begin
        shifted = value >> distance;
        discarded = value << (12'd27-distance);
        shift_jam27 = {shifted[26:1], shifted[0] | (|discarded)};
      end
    end
  endfunction

  // significand[26] is the leading one, [2:0] are guard/round/sticky.
  function automatic [32:0] round_pack32(
    input logic negative,
    input logic signed [11:0] exponent,
    input logic [26:0] significand
  );
    reg [26:0] shifted;
    reg [24:0] rounded;
    reg signed [11:0] adjusted;
    reg [7:0] biased;
    begin
      adjusted = exponent;
      shifted = significand;
      if (exponent < -12'sd126) begin
        shifted = shift_jam27(significand, $unsigned(-12'sd126-exponent));
        adjusted = -12'sd126;
      end
      rounded = {1'b0, shifted[26:3]} +
        {24'd0, (shifted[2] && (shifted[1] || shifted[0] || shifted[3]))};
      if (rounded[24]) begin
        rounded = rounded >> 1;
        adjusted = adjusted + 1'b1;
      end
      biased = 0;
      if (rounded[23]) biased = 8'(adjusted + 12'sd127);
      if (significand == 0 || rounded == 0)
        round_pack32 = {1'b0, negative, 31'd0};
      else if (adjusted > 12'sd127)
        round_pack32 = {1'b1, 32'd0};
      else round_pack32 = {1'b0, negative, biased, rounded[22:0]};
    end
  endfunction

  function automatic [16:0] round_bf16(input logic [31:0] value);
    reg [16:0] rounded;
    begin
      rounded = {1'b0, value[31:16]} +
        {16'd0, (value[15] && ((|value[14:0]) || value[16]))};
      if (fp32_invalid(value) || rounded[14:7] == 8'hff)
        round_bf16 = {1'b1, 16'd0};
      else round_bf16 = {1'b0, rounded[15:0]};
    end
  endfunction

  function automatic [31:0] delta32(
    input logic [3:0] quantized, input logic [3:0] zero_point
  );
    reg signed [5:0] delta;
    reg [4:0] magnitude;
    reg [30:0] encoded;
    begin
      delta = $signed({2'd0, quantized}) - $signed({2'd0, zero_point});
      magnitude = delta[5] ? 5'(-delta) : delta[4:0];
      case (magnitude)
        0: encoded = 31'h00000000;
        1: encoded = 31'h3f800000;
        2: encoded = 31'h40000000;
        3: encoded = 31'h40400000;
        4: encoded = 31'h40800000;
        5: encoded = 31'h40a00000;
        6: encoded = 31'h40c00000;
        7: encoded = 31'h40e00000;
        8: encoded = 31'h41000000;
        9: encoded = 31'h41100000;
        10: encoded = 31'h41200000;
        11: encoded = 31'h41300000;
        12: encoded = 31'h41400000;
        13: encoded = 31'h41500000;
        14: encoded = 31'h41600000;
        default: encoded = 31'h41700000;
      endcase
      delta32 = {delta[5], encoded};
    end
  endfunction

  function automatic [4:0] awq_lane_shift(input logic [2:0] lane);
    begin
      case (lane)
        0: awq_lane_shift = 0;
        1: awq_lane_shift = 16;
        2: awq_lane_shift = 4;
        3: awq_lane_shift = 20;
        4: awq_lane_shift = 8;
        5: awq_lane_shift = 24;
        6: awq_lane_shift = 12;
        default: awq_lane_shift = 28;
      endcase
    end
  endfunction

  function automatic configuration_valid(
    input integer profile, compact, layers, hidden, intermediate,
    q_heads, kv_heads, head_dim, vocabulary, sequence_length,
    group_size, banks, queue_depth
  );
    reg dimensions_valid, production_valid;
    reg [127:0] h, i, q, k, d, l, v, s, g, extent;
    begin
      h=128'(hidden); i=128'(intermediate); q=128'(q_heads);
      k=128'(kv_heads); d=128'(head_dim); l=128'(layers);
      v=128'(vocabulary); s=128'(sequence_length); g=128'(group_size);
      extent=h>i ? h : i;
      dimensions_valid=(profile==1 || profile==2 || profile==3) &&
        (compact==0 || compact==1) && layers>=1 && layers<=36 &&
        hidden>=8 && hidden<=2560 && intermediate>=8 && intermediate<=9728 &&
        (hidden & 7)==0 && (intermediate & 7)==0 &&
        (head_dim==8 || head_dim==16 || head_dim==32 ||
         head_dim==64 || head_dim==128) &&
        kv_heads>=1 && kv_heads<=8 && q_heads<=32 &&
        (q_heads==2*kv_heads || q_heads==4*kv_heads) &&
        vocabulary>=1 && vocabulary<=151936 &&
        sequence_length>=1 && sequence_length<=40960 &&
        group_size>=8 && group_size<=128 && (g & (g-1'b1))==0 &&
        (h & (g-1'b1))==0 && (i & (g-1'b1))==0 &&
        ((q*d) & (g-1'b1))==0 &&
        (banks==1 || banks==2 || banks==4 || banks==8) &&
        queue_depth>=1 && queue_depth<=16 &&
        15*extent<=128'hffffffff && q*d<=128'hffffffff &&
        k*d<=128'hffffffff &&
        4*v*h<=128'hffffffffffffffff &&
        4*l*h*i<=128'hffffffffffffffff &&
        4*l*h*q*d<=128'hffffffffffffffff &&
        4*l*s*k*d<=128'hffffffffffffffff;
      production_valid=layers==(profile==3 ? 36 : 28) &&
        hidden==(profile==1 ? 1024 : profile==2 ? 2048 : 2560) &&
        intermediate==(profile==1 ? 3072 : profile==2 ? 6144 : 9728) &&
        q_heads==(profile==3 ? 32 : 16) && kv_heads==8 && head_dim==128 &&
        vocabulary==151936 && sequence_length==40960 && group_size==128;
      configuration_valid=dimensions_valid && (compact==1 || production_valid);
    end
  endfunction

  function automatic [63:0] event_add64(input logic [63:0] value, input logic [2:0] delta);
    reg [16:0] low;
    reg carry1, carry2, carry3;
    begin
      low={1'b0,value[15:0]}+{14'd0,delta};
      carry1=low[16];
      carry2=carry1 && (&value[31:16]);
      carry3=carry1 && (&value[47:16]);
      event_add64={value[63:48]+{15'd0,carry3},
        value[47:32]+{15'd0,carry2},value[31:16]+{15'd0,carry1},low[15:0]};
    end
  endfunction
endpackage
