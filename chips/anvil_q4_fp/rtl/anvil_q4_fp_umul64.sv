module anvil_q4_fp_umul64 (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire [63:0] a, b,
  output wire out_valid,
  input wire out_ready,
  output wire [127:0] result
);
  localparam [2:0] IDLE=0, MULTIPLY=1, ALIGN=2, ADD=3, RESPONSE=4;
  reg [2:0] state;
  reg [63:0] left, right;
  reg [127:0] accumulator, term;
  reg [31:0] partial;
  reg [1:0] ai, bi, limb;
  reg carry;
  wire [32:0] sum={1'b0,accumulator[limb*32+:32]}+
    {1'b0,term[limb*32+:32]}+{32'd0,carry};
  wire [3:0] partial_position={2'd0,ai}+{2'd0,bi};
  assign in_ready=rst_n && !flush && state==IDLE;
  assign out_valid=rst_n && !flush && state==RESPONSE;
  assign result=out_valid ? accumulator : 128'd0;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; left<=0; right<=0; accumulator<=0; term<=0;
      partial<=0; ai<=0; bi<=0; limb<=0; carry<=0;
    end else if (flush) begin state<=IDLE; accumulator<=0; end
    else case (state)
      IDLE: if (in_valid) begin
        left<=a; right<=b; accumulator<=0; ai<=0; bi<=0; state<=MULTIPLY;
      end
      MULTIPLY: begin partial<=left[ai*16+:16]*right[bi*16+:16]; state<=ALIGN; end
      ALIGN: begin term<={96'd0,partial} << {partial_position,4'd0}; limb<=0; carry<=0; state<=ADD; end
      ADD: begin
        accumulator[limb*32+:32]<=sum[31:0]; carry<=sum[32];
        if (limb!=3) limb<=limb+1'b1;
        else if (bi!=3) begin bi<=bi+1'b1; state<=MULTIPLY; end
        else if (ai!=3) begin ai<=ai+1'b1; bi<=0; state<=MULTIPLY; end
        else state<=RESPONSE;
      end
      RESPONSE: if (out_ready) state<=IDLE;
      default: state<=IDLE;
    endcase
  end
endmodule
