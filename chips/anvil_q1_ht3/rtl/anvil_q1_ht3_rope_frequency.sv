module anvil_q1_ht3_rope_frequency #(
  parameter HEAD_DIM = 64
) (
  input wire rst_n,
  input wire [4:0] index,
  output wire [56:0] frequency
);
  localparam LEGAL = HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0;
  function automatic [56:0] root(input integer dimensions);
    begin
      case (dimensions)
        2: root = 57'h0000010c6f7a0b6;
        4: root = 57'h0004189374bc6a8;
        6: root = 57'h0028f5c28f5c28f;
        8: root = 57'h008186e27501d39;
        10: root = 57'h010270ac3f8a9fa;
        12: root = 57'h01999999999999a;
        14: root = 57'h02392329aa09009;
        16: root = 57'h02d8621c6ed3e7d;
        18: root = 57'h037274d9d816763;
        20: root = 57'h0404de61f75c130;
        22: root = 57'h048e8e34b46d405;
        24: root = 57'h050f44d8921243b;
        26: root = 57'h05873642371c842;
        28: root = 57'h05f6d2880271b89;
        30: root = 57'h065ea59fdd492cb;
        32: root = 57'h06bf44d53103542;
        34: root = 57'h07194462ae9bebc;
        36: root = 57'h076d31dd82f3fca;
        38: root = 57'h07bb91773d9fcf0;
        40: root = 57'h0804dce799a1293;
        42: root = 57'h08498348bc69bc3;
        44: root = 57'h0889e9792a9752e;
        46: root = 57'h08c66ac27353ff1;
        48: root = 57'h08ff599e0e1c0f1;
        50: root = 57'h09350081face598;
        52: root = 57'h0967a2a87940c46;
        54: root = 57'h09977ccc19640fe;
        56: root = 57'h09c4c5d4f469618;
        58: root = 57'h09efaf75fafaa1b;
        60: root = 57'h0a1866ba7b6a3c0;
        62: root = 57'h0a3f1484ad2db9b;
        64: root = 57'h0a63ddfe63e31e0;
        default: root = 0;
      endcase
    end
  endfunction
  function automatic [56:0] power(input integer exponent);
    reg [56:0] value;
    reg [113:0] product;
    integer k;
    begin
      value = 57'h100000000000000;
      product = 0;
      for (k = 0; k < exponent; k = k + 1) begin
        product = value * root(HEAD_DIM);
        value = (product + 114'h80000000000000) >> 56;
      end
      power = value;
    end
  endfunction
  wire [1823:0] table_bits;
  genvar j;
  generate
    for (j = 0; j < 32; j = j + 1) begin: g_frequency
      localparam [56:0] VALUE = power(j);
      assign table_bits[57*j+:57] = VALUE;
    end
  endgenerate
  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 RoPE HEAD_DIM");
  end
  assign frequency = rst_n && LEGAL && {1'b0, index} < (HEAD_DIM >> 1) ?
    table_bits[57*index+:57] : 57'b0;
endmodule
