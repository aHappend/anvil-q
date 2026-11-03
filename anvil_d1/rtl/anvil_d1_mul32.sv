module anvil_d1_mul32 (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire signed [31:0] in_a, in_b,
  output wire out_valid,
  input wire out_ready,
  output wire signed [63:0] out_product
);
  reg armed, busy, valid;
  reg [1:0] stage;
  reg [31:0] p00, p00_delay;
  reg signed [32:0] p01, p10;
  reg signed [31:0] p11, p11_delay;
  reg signed [33:0] cross_sum;
  reg [32:0] low_sum;
  reg [31:0] high_sum;
  reg [63:0] result;
  wire [32:0] low_next={1'b0,p00_delay}+{1'b0,cross_sum[15:0],16'd0};
  wire [31:0] high_next=$unsigned(p11_delay)+{{14{cross_sum[33]}},cross_sum[33:16]};
  assign in_ready=rst_n && armed && !flush && !busy && !valid;
  assign out_valid=rst_n && !flush && valid;
  assign out_product=rst_n && !flush ? $signed(result) : 64'sd0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      armed<=0; busy<=0; valid<=0; stage<=0;
      p00<=0; p01<=0; p10<=0; p11<=0; p00_delay<=0; p11_delay<=0;
      cross_sum<=0; low_sum<=0; high_sum<=0; result<=0;
    end else begin
      armed<=1;
      if (flush) begin
        busy<=0; valid<=0; stage<=0; result<=0;
      end else begin
        if (out_valid && out_ready) valid<=0;
        if (in_valid && in_ready) begin
          p00<=$unsigned(in_a[15:0])*$unsigned(in_b[15:0]);
          p01<=$signed({1'b0,in_a[15:0]})*$signed(in_b[31:16]);
          p10<=$signed(in_a[31:16])*$signed({1'b0,in_b[15:0]});
          p11<=$signed(in_a[31:16])*$signed(in_b[31:16]);
          busy<=1; stage<=1;
        end else if (busy) case (stage)
          1: begin
            cross_sum<=$signed({p01[32],p01})+$signed({p10[32],p10});
            p00_delay<=p00; p11_delay<=p11; stage<=2;
          end
          2: begin low_sum<=low_next; high_sum<=high_next; stage<=3; end
          3: begin
            result<={high_sum+{31'd0,low_sum[32]},low_sum[31:0]};
            valid<=1; busy<=0; stage<=0;
          end
          default: begin busy<=0; stage<=0; end
        endcase
      end
    end
  end
endmodule
