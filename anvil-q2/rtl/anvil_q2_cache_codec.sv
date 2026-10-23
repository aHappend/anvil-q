module anvil_q2_cache_codec #(
  parameter CACHE_BLOCK=16,
  parameter SAFE_BLOCK=CACHE_BLOCK>0 ? CACHE_BLOCK : 1,
  parameter USE_REG_EXP=0
)(
  input wire [SAFE_BLOCK*32-1:0] block_values,
  output reg [SAFE_BLOCK*8-1:0] block_bytes,
  output reg [7:0] block_exponent,
  input wire [7:0] read_byte, read_exponent,
  output reg signed [31:0] read_value,
  output wire invalid_exponent
);
  reg [32:0] maximum;
  reg [32:0] tree [0:2*SAFE_BLOCK-1];
  reg [63:0] threshold;
  reg signed [31:0] value;
  reg signed [127:0] rounded, reconstructed;
  wire [7:0] active_exponent = USE_REG_EXP ? read_exponent : block_exponent;
  integer i, e;
  generate if(CACHE_BLOCK<=0 || (CACHE_BLOCK & (CACHE_BLOCK-1))!=0) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2 PARAMETER ERROR: cache block must be a positive power of two");
  end endgenerate
  assign invalid_exponent=read_exponent>25;
  always @* begin
    maximum=0;
    value=0;
    rounded=0;
    threshold=0;
    block_bytes=0;
    block_exponent=25;
    tree[0]=0;
    for(i=0;i<SAFE_BLOCK;i=i+1) begin
      value=$signed(block_values[i*32+:32]);
      tree[SAFE_BLOCK+i]=value<0 ? -$signed({value[31],value}) : {1'b0,value};
    end
    for(i=SAFE_BLOCK-1;i>=1;i=i-1) begin
      tree[i]=tree[2*i]>tree[2*i+1] ? tree[2*i] : tree[2*i+1];
    end
    maximum=tree[1];
    for(e=25;e>=0;e=e-1) begin
      threshold=64'd127<<e;
      if({31'd0,maximum}<=threshold) block_exponent=e;
    end
    for(i=0;i<SAFE_BLOCK;i=i+1) begin
      value=$signed(block_values[i*32+:32]);
      rounded=anvil_q2_pkg::round_shift({{96{value[31]}},value},active_exponent);
      if(rounded>127) block_bytes[i*8+:8]=8'h7f;
      else if(rounded< -127) block_bytes[i*8+:8]=8'h81;
      else block_bytes[i*8+:8]=rounded[7:0];
    end
  end
  always @* begin
    reconstructed=$signed({{120{read_byte[7]}},read_byte}) <<< read_exponent;
    read_value=anvil_q2_pkg::sat32(reconstructed);
  end
endmodule
