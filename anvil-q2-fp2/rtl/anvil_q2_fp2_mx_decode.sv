module anvil_q2_fp2_mx_decode (
  input wire [7:0] in_payload, in_scale,
  output reg [15:0] out_bf16,
  output reg out_error
);
  reg [3:0] mantissa;
  reg [7:0] normalized, rounded;
  reg [8:0] quotient;
  reg signed [12:0] exponent, unbiased, shift;
  reg [7:0] encoded;
  reg guard_bit, sticky;
  reg [1:0] top;
  always @* begin
    mantissa=in_payload[6:3]==0 ?
      {1'b0,in_payload[2:0]} : {1'b1,in_payload[2:0]};
    top=0;
    if (mantissa[3]) top=3;
    else if (mantissa[2]) top=2;
    else if (mantissa[1]) top=1;
    exponent=$signed({5'd0,in_scale})-13'sd136;
    if (in_payload[6:3]!=0)
      exponent=$signed({9'd0,in_payload[6:3]})+
        $signed({5'd0,in_scale})-13'sd137;
    unbiased=exponent+$signed({11'd0,top});
    normalized={4'd0,mantissa} << (3'd7-{1'b0,top});
    quotient=0;
    rounded=0;
    guard_bit=0;
    sticky=0;
    encoded=0;
    shift=-13'sd133-exponent;
    out_bf16={in_payload[7],15'd0};
    out_error=0;
    if (in_scale==255 || in_payload[6:0]==7'h7f) begin
      out_bf16=16'h7fc0;
      out_error=1;
    end else if (mantissa!=0) begin
      if (unbiased>13'sd127) begin
        out_bf16={in_payload[7],8'hff,7'd0};
        out_error=1;
      end else if (unbiased>=-13'sd126) begin
        encoded=unbiased[7:0]+8'd127;
        out_bf16={in_payload[7],encoded,normalized[6:0]};
      end else begin
        if (shift<=0) quotient={5'd0,mantissa} << (-shift);
        else if (shift<=4) begin
          quotient={5'd0,mantissa} >> shift[2:0];
          guard_bit=|(mantissa & (4'd1 << (shift[2:0]-3'd1)));
          if (shift>1)
            sticky=|(mantissa & (4'hf >> (4'd5-{1'b0,shift[2:0]})));
        end else sticky=|mantissa;
        rounded=quotient[7:0]+{7'd0,(guard_bit && (sticky || quotient[0]))};
        out_bf16={in_payload[7],7'd0,rounded};
      end
    end
  end
endmodule
