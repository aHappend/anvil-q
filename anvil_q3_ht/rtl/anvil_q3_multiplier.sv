module anvil_q3_multiplier #(
  parameter integer A_W=32, B_W=32,
  localparam integer AW=(A_W>=1 && A_W<=128) ? A_W : 1,
  localparam integer BW=(B_W>=1 && B_W<=128) ? B_W : 1
) (
  input wire clk, rst_n, flush, start,
  input wire signed [AW-1:0] a,
  input wire signed [BW-1:0] b,
  output wire ready, done, error,
  output wire signed [AW+BW-1:0] product
);
  localparam integer AC=(AW+15)/16, BC=(BW+15)/16;
  localparam integer PW=AW+BW, PC=(PW+15)/16;
  localparam IDLE=0, ABS_A=1, ABS_B=2, MULTIPLY=3, PREPARE=4, ADD=5, SIGN=6;
  reg [2:0] state;
  reg done_reg, error_reg, negative, a_negative, b_negative, carry;
  reg [7:0] segment, a_index, b_index;
  reg [AC*16-1:0] raw_a, magnitude_a;
  reg [BC*16-1:0] raw_b, magnitude_b;
  reg [31:0] partial_product;
  reg [PC*16-1:0] sum, term, result;
  wire [16:0] a_absolute={1'b0,~raw_a[segment*16+:16]}+{16'd0,carry};
  wire [16:0] b_absolute={1'b0,~raw_b[segment*16+:16]}+{16'd0,carry};
  wire [16:0] addition={1'b0,sum[segment*16+:16]}+
    {1'b0,term[segment*16+:16]}+{16'd0,carry};
  wire [16:0] sign_segment={1'b0,~sum[segment*16+:16]}+{16'd0,carry};
  wire [PC*16-1:0] extended_partial=(PC*16)'(partial_product);

  generate if (A_W<1 || A_W>128 || B_W<1 || B_W>128 || A_W+B_W>256) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3 PARAMETER ERROR: multiplier widths");
  end endgenerate
  assign ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && done_reg;
  assign error=done && error_reg;
  assign product=rst_n && !flush ? $signed(result[PW-1:0]) : {PW{1'b0}};

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; done_reg<=0; error_reg<=0;
      negative<=0; a_negative<=0; b_negative<=0; carry<=0;
      segment<=0; a_index<=0; b_index<=0;
      raw_a<=0; raw_b<=0; magnitude_a<=0; magnitude_b<=0;
      partial_product<=0; sum<=0; term<=0; result<=0;
    end else if (flush) begin
      state<=IDLE; done_reg<=0; error_reg<=0; result<=0;
    end else begin
      done_reg<=0;
      error_reg<=0;
      case (state)
        IDLE: if (start && ready) begin
          raw_a<={{(AC*16-AW){a[AW-1]}},a};
          raw_b<={{(BC*16-BW){b[BW-1]}},b};
          a_negative<=a[AW-1]; b_negative<=b[BW-1];
          negative<=a[AW-1]^b[BW-1];
          carry<=1; segment<=0; sum<=0; a_index<=0; b_index<=0;
          state<=ABS_A;
        end
        ABS_A: begin
          magnitude_a[segment*16+:16]<=a_negative ? a_absolute[15:0] : raw_a[segment*16+:16];
          carry<=a_absolute[16];
          if (segment+1==AC) begin segment<=0; carry<=1; state<=ABS_B; end
          else segment<=segment+1'b1;
        end
        ABS_B: begin
          magnitude_b[segment*16+:16]<=b_negative ? b_absolute[15:0] : raw_b[segment*16+:16];
          carry<=b_absolute[16];
          if (segment+1==BC) begin segment<=0; state<=MULTIPLY; end
          else segment<=segment+1'b1;
        end
        MULTIPLY: begin
          partial_product<=magnitude_a[a_index*16+:16]*magnitude_b[b_index*16+:16];
          state<=PREPARE;
        end
        PREPARE: begin
          term<=extended_partial << ((a_index+b_index)*16);
          carry<=0; segment<=0; state<=ADD;
        end
        ADD: begin
          sum[segment*16+:16]<=addition[15:0];
          carry<=addition[16];
          if (segment+1==PC) begin
            segment<=0;
            if (b_index+1<BC) begin b_index<=b_index+1'b1; state<=MULTIPLY; end
            else if (a_index+1<AC) begin
              b_index<=0; a_index<=a_index+1'b1; state<=MULTIPLY;
            end else begin carry<=1; state<=SIGN; end
          end else segment<=segment+1'b1;
        end
        SIGN: begin
          result[segment*16+:16]<=negative ? sign_segment[15:0] : sum[segment*16+:16];
          carry<=sign_segment[16];
          if (segment+1==PC) begin done_reg<=1; state<=IDLE; end
          else segment<=segment+1'b1;
        end
        default: begin state<=IDLE; done_reg<=1; error_reg<=1; result<=0; end
      endcase
    end
  end
endmodule
