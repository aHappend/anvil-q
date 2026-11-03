module anvil_q4_parent_exp (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire [31:0] x,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] result,
  output wire [4:0] flags
);
  import anvil_q4_parent_fp_pkg::*;
  localparam [3:0] IDLE=0, CLASSIFY=1, FIXED=2, REDUCE=3,
    REDUCE_ADD=4, REDUCE_SUB=5, POLY_START=6, POLY_WAIT=7,
    POLY_ADD=8, PACK=9, RESPONSE=10;
  localparam signed [63:0] LN2_Q56=64'sh00b17217f7d1cf7a;
  reg [3:0] state;
  reg [31:0] operand, result_register;
  reg [4:0] flag_register, degree;
  reg signed [63:0] remainder;
  reg signed [11:0] power;
  reg [63:0] reduced, polynomial, product_rounded;
  wire [35:0] unpacked = unpack_normalized(operand);
  wire signed [11:0] fixed_shift = $signed(unpacked[35:24])+12'sd33;
  wire [63:0] magnitude = fixed_shift>=0 ?
    ({40'd0,unpacked[23:0]} << $unsigned(fixed_shift)) :
    ({40'd0,unpacked[23:0]} >> $unsigned(-fixed_shift));
  wire mul_ready, mul_valid;
  wire [127:0] product;
  wire [63:0] rounded_product = product[125:62]+
    {63'd0,(product[61] && ((|product[60:0]) || product[62]))};
  wire [26:0] packed_significand = polynomial[63] ?
    {polynomial[63:38],polynomial[37] || (|polynomial[36:0])} :
    {polynomial[62:37],polynomial[36] || (|polynomial[35:0])};
  wire signed [11:0] packed_power=polynomial[63] ? power+12'sd1 : power;
  wire [36:0] packed_result = round_pack32(1'b0,packed_power,packed_significand);

  function automatic [63:0] coefficient(input [4:0] n);
    begin
      case (n)
        0: coefficient=64'h4000000000000000;
        1: coefficient=64'h4000000000000000;
        2: coefficient=64'h2000000000000000;
        3: coefficient=64'h0aaaaaaaaaaaaaab;
        4: coefficient=64'h02aaaaaaaaaaaaab;
        5: coefficient=64'h0088888888888889;
        6: coefficient=64'h0016c16c16c16c17;
        7: coefficient=64'h0003403403403403;
        8: coefficient=64'h0000680680680680;
        9: coefficient=64'h00000b8ef1d2ab64;
        10: coefficient=64'h00000127e4fb778a;
        11: coefficient=64'h0000001ae64567f5;
        12: coefficient=64'h000000023ddb1dff;
        13: coefficient=64'h000000002c248c27;
        14: coefficient=64'h0000000003272e95;
        15: coefficient=64'h000000000035cfe8;
        default: coefficient=64'h0000000000035cfe;
      endcase
    end
  endfunction

  anvil_q4_parent_umul64 multiplier (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==POLY_START),.in_ready(mul_ready),
    .a(polynomial),.b(reduced),.out_valid(mul_valid),
    .out_ready(state==POLY_WAIT),.result(product)
  );
  assign in_ready=rst_n && !flush && state==IDLE;
  assign out_valid=rst_n && !flush && state==RESPONSE;
  assign result=rst_n && !flush ? result_register : 32'd0;
  assign flags=rst_n && !flush ? flag_register : 5'd0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; operand<=0; result_register<=0; flag_register<=0;
      degree<=0; remainder<=0; power<=0; reduced<=0;
      polynomial<=0; product_rounded<=0;
    end else if (flush) begin
      state<=IDLE; result_register<=0; flag_register<=0;
    end else case (state)
      IDLE: if (in_valid) begin
        operand<=x; flag_register<=0; power<=0; state<=CLASSIFY;
      end
      CLASSIFY: begin
        if (is_nan(operand)) begin
          result_register<=32'h7fc00000;
          flag_register<={is_signaling_nan(operand),4'd0}; state<=RESPONSE;
        end else if (is_infinity(operand)) begin
          result_register<=operand[31] ? 32'd0 : 32'h7f800000;
          state<=RESPONSE;
        end else if (ordered_less(32'h42b20000,operand)) begin
          result_register<=32'h7f800000; flag_register<=5'b00101;
          state<=RESPONSE;
        end else if (ordered_less(operand,32'hc2d00000)) begin
          result_register<=0; flag_register<=5'b00011; state<=RESPONSE;
        end else state<=FIXED;
      end
      FIXED: begin
        remainder<=operand[31] ? -$signed(magnitude) : $signed(magnitude);
        state<=REDUCE;
      end
      REDUCE: begin
        if (remainder<0) state<=REDUCE_ADD;
        else if (remainder>=LN2_Q56) state<=REDUCE_SUB;
        else begin
          reduced<=remainder << 6; polynomial<=coefficient(16);
          degree<=15; state<=POLY_START;
        end
      end
      REDUCE_ADD: begin
        remainder<=remainder+LN2_Q56; power<=power-12'sd1; state<=REDUCE;
      end
      REDUCE_SUB: begin
        remainder<=remainder-LN2_Q56; power<=power+12'sd1; state<=REDUCE;
      end
      POLY_START: if (mul_ready) state<=POLY_WAIT;
      POLY_WAIT: if (mul_valid) begin product_rounded<=rounded_product; state<=POLY_ADD; end
      POLY_ADD: begin
        polynomial<=product_rounded+coefficient(degree);
        if (degree==0) state<=PACK;
        else begin degree<=degree-1'b1; state<=POLY_START; end
      end
      PACK: begin
        result_register<=packed_result[31:0];
        flag_register<=packed_result[36:32] |
          (is_zero(operand) ? 5'd0 : 5'b00001);
        state<=RESPONSE;
      end
      RESPONSE: if (out_ready) state<=IDLE;
      default: begin
        result_register<=32'h7fc00000; flag_register<=5'b10000;
        state<=RESPONSE;
      end
    endcase
  end
endmodule
