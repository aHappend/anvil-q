module anvil_q1_awq_dequant(
  input wire [31:0] qweight_word, qzero_word,
  input wire [15:0] scale_f16,
  input wire [2:0] lane,
  output reg signed [36:0] weight_q16_16,
  output reg invalid
);
  function automatic [31:0] scale_integer(input [15:0] h);
    reg [63:0] magnitude;
    integer shift;
    begin
      magnitude = h[14:10] == 0 ? {54'd0,h[9:0]} : {53'd0,1'b1,h[9:0]};
      shift = h[14:10] == 0 ? -8 : $signed({27'd0,h[14:10]})-9;
      if (shift >= 0) magnitude = magnitude << shift;
      else magnitude = (magnitude + (64'd1 << (-shift-1))) >> (-shift);
      scale_integer = magnitude[31:0];
    end
  endfunction
  reg [4:0] shift;
  reg [3:0] w, z;
  reg signed [4:0] delta;
  reg signed [32:0] scale_extended;
  reg signed [37:0] product;
  always @* begin
    case (lane)
      0: shift=0; 1: shift=16; 2: shift=4; 3: shift=20;
      4: shift=8; 5: shift=24; 6: shift=12; default: shift=28;
    endcase
    w = (qweight_word >> shift) & 32'hf;
    z = (qzero_word >> shift) & 32'hf;
    delta = $signed({1'b0,w})-$signed({1'b0,z});
    scale_extended = $signed({1'b0,scale_integer(scale_f16)});
    product = {{33{delta[4]}},delta} * {{5{scale_extended[32]}},scale_extended};
    invalid = (scale_f16[14:10] == 31) ||
              (scale_f16[15] && (scale_f16[14:0] != 0));
    weight_q16_16 = invalid ? 37'sd0 : product[36:0];
  end
endmodule
