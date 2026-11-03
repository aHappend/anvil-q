module anvil_q2_ht_integer_math (
  input wire clk, rst_n, annul,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [3:0] cmd_op,
  input wire signed [127:0] cmd_a, cmd_b,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire signed [127:0] rsp_data,
  output wire rsp_error
);
  import anvil_q2_ht_int_pkg::*;
  localparam [4:0] IDLE=0, PREPARE=1, ADD=2, ABS_DONE=3,
    DIV_BIAS=4, DIV_START=5, DIV_SHIFT=6, DIV_DECIDE=7,
    ROOT_SHIFT=8, ROOT_DECIDE=9, MUL_PRODUCT=10, MUL_ADD=11,
    MUL_NEXT=12, SHIFT_LOW=13, SHIFT_HIGH=14, SHIFT_BIAS=15,
    SIGN=16, RESPONSE=17;
  reg [4:0] state, add_return;
  reg [3:0] operation;
  reg signed [127:0] a, b, result;
  reg negative, failed;
  reg [127:0] lhs, rhs, sum, magnitude;
  reg carry;
  reg [1:0] limb;
  reg [127:0] numerator, quotient;
  reg [63:0] denominator, root;
  reg [66:0] remainder;
  reg [7:0] remaining, distance;
  reg [1:0] mul_i, mul_j;
  reg signed [16:0] mul_a, mul_b;
  reg signed [33:0] product;
  reg [127:0] accumulator, shifted;
  wire [32:0] limb_sum={1'b0,lhs[limb*32+:32]}+
    {1'b0,rhs[limb*32+:32]}+{32'd0,carry};
  wire small_product=operation==M_MUL32;
  wire [1:0] last_limb=small_product ? 2'd1 : 2'd3;
  wire [66:0] div_candidate={2'd0,remainder[63:0],numerator[127]};
  wire [66:0] root_candidate={remainder[64:0],numerator[127:126]};
  wire [66:0] root_trial={1'b0,root,2'b01};
  wire [127:0] next_quotient={quotient[126:0],carry};
  wire [63:0] next_root={root[62:0],carry};
  wire enabled=rst_n && !annul;

  always @* begin
    mul_a=$signed({1'b0,a[mul_i*16+:16]});
    mul_b=$signed({1'b0,b[mul_j*16+:16]});
    if (mul_i==last_limb) mul_a=$signed({a[mul_i*16+15],a[mul_i*16+:16]});
    if (mul_j==last_limb) mul_b=$signed({b[mul_j*16+15],b[mul_j*16+:16]});
  end

  assign cmd_ready=enabled && state==IDLE;
  assign rsp_valid=enabled && state==RESPONSE;
  assign rsp_data=rsp_valid ? result : 128'sd0;
  assign rsp_error=rsp_valid && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; add_return<=IDLE; operation<=0; a<=0; b<=0; result<=0;
      negative<=0; failed<=0; lhs<=0; rhs<=0; sum<=0; magnitude<=0;
      carry<=0; limb<=0; numerator<=0; quotient<=0; denominator<=0;
      root<=0; remainder<=0; remaining<=0; distance<=0;
      mul_i<=0; mul_j<=0; product<=0; accumulator<=0; shifted<=0;
    end else if (annul) begin
      state<=IDLE; failed<=0; result<=0;
    end else case (state)
      IDLE: if (cmd_valid) begin
        a<=cmd_a; b<=cmd_b; operation<=cmd_op;
        negative<=cmd_a[127]; failed<=0; result<=0;
        distance<=cmd_b[7:0]; state<=PREPARE;
      end
      PREPARE: begin
        limb<=0; sum<=0; carry<=0;
        case (operation)
          M_ADD: begin lhs<=a; rhs<=b; add_return<=RESPONSE; state<=ADD; end
          M_SUB: begin lhs<=a; rhs<=~b; carry<=1; add_return<=RESPONSE; state<=ADD; end
          M_MUL64,M_MUL32: begin
            mul_i<=0; mul_j<=0; accumulator<=0; state<=MUL_PRODUCT;
          end
          M_UDIV: begin
            numerator<=a; denominator<=b[63:0]; state<=DIV_START;
          end
          M_RDIV,M_ROUND: begin
            if (a[127]) begin
              lhs<=~a; rhs<=0; carry<=1; add_return<=ABS_DONE; state<=ADD;
            end else begin magnitude<=a; state<=ABS_DONE; end
          end
          M_SQRT: begin
            numerator<=a; root<=0; remainder<=0; remaining<=64; state<=ROOT_SHIFT;
          end
          default: begin failed<=1; state<=RESPONSE; end
        endcase
        if ((operation==M_UDIV || operation==M_RDIV) &&
            (b[63:0]==0 || (|b[127:64]))) begin
          failed<=1; state<=RESPONSE;
        end
        if (operation==M_ROUND && (b<0 || b>127)) begin failed<=1; state<=RESPONSE; end
      end
      ADD: begin
        sum[limb*32+:32]<=limb_sum[31:0];
        carry<=limb_sum[32];
        if (limb==3) begin
          if (add_return==RESPONSE) result<={limb_sum[31:0],sum[95:0]};
          if (add_return==ABS_DONE)
            magnitude<={limb_sum[31:0],sum[95:0]};
          state<=add_return;
        end else limb<=limb+2'd1;
      end
      ABS_DONE: begin
        if (operation==M_RDIV) begin
          lhs<=magnitude; rhs<={64'd0,(b[63:0] >> 1)};
          limb<=0; carry<=0; add_return<=DIV_BIAS; state<=ADD;
        end else state<=SHIFT_LOW;
      end
      DIV_BIAS: begin numerator<=sum; denominator<=b[63:0]; state<=DIV_START; end
      DIV_START: begin
        remainder<=0; quotient<=0; remaining<=128; state<=DIV_SHIFT;
      end
      DIV_SHIFT: begin
        lhs<={61'd0,div_candidate}; rhs<=~{64'd0,denominator};
        limb<=0; carry<=1; add_return<=DIV_DECIDE; state<=ADD;
      end
      DIV_DECIDE: begin
        remainder<=carry ? sum[66:0] : lhs[66:0];
        quotient<=next_quotient; numerator<=numerator << 1;
        if (remaining==1) begin
          shifted<=next_quotient; state<=SIGN;
        end else begin remaining<=remaining-8'd1; state<=DIV_SHIFT; end
      end
      ROOT_SHIFT: begin
        lhs<={61'd0,root_candidate}; rhs<=~{61'd0,root_trial};
        limb<=0; carry<=1; add_return<=ROOT_DECIDE; state<=ADD;
      end
      ROOT_DECIDE: begin
        remainder<=carry ? sum[66:0] : lhs[66:0];
        root<=next_root; numerator<=numerator << 2;
        if (remaining==1) begin result<={64'd0,next_root}; state<=RESPONSE; end
        else begin remaining<=remaining-8'd1; state<=ROOT_SHIFT; end
      end
      MUL_PRODUCT: begin product<=mul_a*mul_b; state<=MUL_ADD; end
      MUL_ADD: begin
        lhs<=accumulator;
        rhs<=$signed({{94{product[33]}},product}) <<
          (({5'd0,mul_i}+{5'd0,mul_j}) << 4);
        limb<=0; carry<=0; add_return<=MUL_NEXT; state<=ADD;
      end
      MUL_NEXT: begin
        accumulator<=sum;
        if (mul_i==last_limb && mul_j==last_limb) begin
          result<=sum; state<=RESPONSE;
        end else begin
          if (mul_j==last_limb) begin mul_j<=0; mul_i<=mul_i+2'd1; end
          else mul_j<=mul_j+2'd1;
          state<=MUL_PRODUCT;
        end
      end
      SHIFT_LOW: begin shifted<=magnitude >> distance[3:0]; state<=SHIFT_HIGH; end
      SHIFT_HIGH: begin
        shifted<=shifted >> {distance[6:4],4'd0}; state<=SHIFT_BIAS;
      end
      SHIFT_BIAS: begin
        lhs<=shifted;
        rhs<=distance!=0 && magnitude[distance-8'd1] ? 128'd1 : 128'd0;
        limb<=0; carry<=0; add_return<=SIGN; state<=ADD;
      end
      SIGN: begin
        if (operation==M_ROUND) shifted<=sum;
        if ((operation==M_RDIV || operation==M_ROUND) && negative) begin
          lhs<=operation==M_ROUND ? ~sum : ~shifted;
          rhs<=0; carry<=1; limb<=0; add_return<=RESPONSE; state<=ADD;
        end else begin
          result<=operation==M_ROUND ? sum : shifted; state<=RESPONSE;
        end
      end
      RESPONSE: if (rsp_ready) state<=IDLE;
      default: begin failed<=1; result<=0; state<=RESPONSE; end
    endcase
  end
endmodule
