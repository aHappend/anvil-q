module anvil_q3_fp_parameters #(
  parameter PROFILE=3, NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_Q_HEADS=16, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, AWQ_BITS=4, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  parameter BANKS=8, CACHE_MODE=0, MODE1_FP8=0, INT4_ASYM=0, CACHE_BLOCK=1,
  parameter QUEUE_DEPTH=3, TILE_K=128, TILE_ROWS=8
) ();
  localparam [127:0] L=NUM_LAYERS, H=HIDDEN_SIZE, I=INTERMEDIATE_SIZE;
  localparam [127:0] Q=NUM_Q_HEADS, K=NUM_KV_HEADS, D=HEAD_DIM;
  localparam [127:0] G=GROUP_SIZE, V=VOCAB_SIZE, S=MAX_SEQ_LEN;
  localparam [127:0] SG=GROUP_SIZE>0 ? GROUP_SIZE : 1;
  localparam [127:0] CG=CACHE_MODE==2 ? 64 : 32;
  localparam [127:0] BLOCKS=(D+CG-1)/CG;
  localparam [127:0] WORDS=8;
  localparam [127:0] MODE0_WORDS=(D+1)>>1;
  localparam [127:0] U32=128'hffffffff, U64=128'hffffffffffffffff;
  localparam [127:0] EXTENT=H>I ? H : I;
  localparam VALID =
    PROFILE==3 && NUM_LAYERS>0 && HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 &&
    NUM_Q_HEADS>0 && NUM_KV_HEADS>0 && HEAD_DIM>0 &&
    GROUP_SIZE>=1 && GROUP_SIZE<=128 && VOCAB_SIZE>0 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 && AWQ_BITS==4 &&
    (BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) &&
    (CACHE_MODE==0 || CACHE_MODE==1 || CACHE_MODE==2) &&
    (MODE1_FP8==0 || MODE1_FP8==1) && (INT4_ASYM==0 || INT4_ASYM==1) &&
    CACHE_BLOCK==1 && QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16 &&
    TILE_K>=8 && TILE_K<=128 && TILE_K%8==0 &&
    TILE_ROWS>=1 && TILE_ROWS<=8 &&
    H==Q*D && Q==8*K && D%2==0 &&
    H%8==0 && I%8==0 && H%SG==0 && I%SG==0 &&
    L<=U32 && H<=U32 && I<=U32 && Q<=U32 && K<=U32 && D<=U32 &&
    G<=U32 && V<=U32 && K*D<=U32 && 2*D<=U32 &&
    K*MODE0_WORDS<=U32 && K*BLOCKS*WORDS<=U32 && K*BLOCKS<=U32 &&
    15*EXTENT<=U32 &&
    4*V*H<=U64 && 4*L*H*I<=U64 && 4*L*H*H<=U64 &&
    4*L*S*K*D<=U64 && 4*L*S*K*BLOCKS*WORDS<=U64 &&
    4*L*S*K*BLOCKS<=U64 &&
    D*128'd4611686018427387904 < (128'd1<<95) &&
    S*128'd16777216 < (128'd1<<64);
  generate if (!VALID) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_FP PARAMETER ERROR: dimensions, modes or address bounds");
  end endgenerate
endmodule
