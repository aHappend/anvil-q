module anvil_q1_unsigned_divider #(parameter WIDTH=129)(
  input wire clk, rst_n, start,
  output wire ready, done, error,
  input wire [WIDTH-1:0] numerator,
  input wire [63:0] divisor,
  output wire [WIDTH-1:0] quotient
);
  reg [1:0] state;
  reg failed;
  reg [31:0] bits_left;
  reg [WIDTH-1:0] dividend, result;
  reg [63:0] denominator, remainder;
  wire [64:0] trial;
  wire subtract;
  assign trial={remainder,dividend[WIDTH-1]};
  assign subtract=trial>={1'b0,denominator};
  assign ready=rst_n && state==0;
  assign done=rst_n && state==2;
  assign error=done && failed;
  assign quotient=rst_n ? result : {WIDTH{1'b0}};
  always @(posedge clk) begin
    if(!rst_n) begin
      state<=0; failed<=0; bits_left<=0; dividend<=0;
      result<=0; denominator<=0; remainder<=0;
    end else case(state)
      0: if(start) begin
        failed<=divisor==0; dividend<=numerator; denominator<=divisor;
        remainder<=0; result<=0; bits_left<=WIDTH;
        if(divisor==0) state<=3;
        else state<=1;
      end
      1: begin
        if(subtract) remainder<=trial-{1'b0,denominator};
        else remainder<=trial[63:0];
        dividend<=dividend<<1;
        result<=(result<<1) | {{(WIDTH-1){1'b0}},subtract};
        bits_left<=bits_left-1;
        if(bits_left==1) state<=2;
      end
      2: state<=0;
      3: state<=2;
      default: state<=0;
    endcase
  end
endmodule
