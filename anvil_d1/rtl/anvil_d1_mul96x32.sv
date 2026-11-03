module anvil_d1_mul96x32 (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire signed [95:0] in_a,
  input wire signed [31:0] in_b,
  output wire out_valid,
  input wire out_ready,
  output wire signed [127:0] out_product
);
  localparam IDLE=0, LIMBS=1, WORD1=2, WORD2=3, WORD3=4;
  reg [2:0] state;
  reg armed, valid, low_unsigned, middle_unsigned;
  reg [31:0] b_latched;
  wire [2:0] limb_ready, limb_valid;
  wire signed [63:0] limb_product [0:2];
  reg [63:0] p0, p1, p2;
  reg [32:0] sum1;
  reg [33:0] sum2;
  reg [31:0] word0, word1;
  reg [127:0] result;
  wire launch=in_valid && in_ready;
  wire [31:0] corrected0=limb_product[0][63:32]+(low_unsigned ? b_latched : 32'd0);
  wire [31:0] corrected1=limb_product[1][63:32]+(middle_unsigned ? b_latched : 32'd0);
  wire [33:0] next_sum2={2'b0,{32{p0[63]}}}+{2'b0,p1[63:32]}+
    {2'b0,p2[31:0]}+{33'd0,sum1[32]};
  wire [31:0] word3={32{p0[63]}}+{32{p1[63]}}+p2[63:32]+{30'd0,sum2[33:32]};
  assign in_ready=rst_n && armed && !flush && state==IDLE && !valid && (&limb_ready);
  assign out_valid=rst_n && !flush && valid;
  assign out_product=rst_n && !flush ? $signed(result) : 128'sd0;
  genvar i;
  generate for (i=0;i<3;i=i+1) begin: limbs
    anvil_d1_mul32 multiply (
      .clk(clk),.rst_n(rst_n),.flush(flush),
      .in_valid(launch),.in_ready(limb_ready[i]),
      .in_a(in_a[i*32+:32]),.in_b(in_b),
      .out_valid(limb_valid[i]),.out_ready(state==LIMBS && (&limb_valid)),
      .out_product(limb_product[i])
    );
  end endgenerate
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; valid<=0; low_unsigned<=0; middle_unsigned<=0;
      b_latched<=0; p0<=0; p1<=0; p2<=0; sum1<=0; sum2<=0;
      word0<=0; word1<=0; result<=0;
    end else begin
      armed<=1;
      if (flush) begin state<=IDLE; valid<=0; result<=0; end
      else begin
        if (out_valid && out_ready) valid<=0;
        case (state)
          IDLE: if (launch) begin
            low_unsigned<=in_a[31]; middle_unsigned<=in_a[63];
            b_latched<=in_b; state<=LIMBS;
          end
          LIMBS: if (&limb_valid) begin
            p0<={corrected0,limb_product[0][31:0]};
            p1<={corrected1,limb_product[1][31:0]};
            p2<=limb_product[2]; state<=WORD1;
          end
          WORD1: begin
            word0<=p0[31:0];
            sum1<={1'b0,p0[63:32]}+{1'b0,p1[31:0]};
            state<=WORD2;
          end
          WORD2: begin
            word1<=sum1[31:0]; sum2<=next_sum2; state<=WORD3;
          end
          WORD3: begin
            result<={word3,sum2[31:0],word1,word0};
            valid<=1; state<=IDLE;
          end
          default: state<=IDLE;
        endcase
      end
    end
  end
endmodule
