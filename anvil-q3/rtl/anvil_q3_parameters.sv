module anvil_q3_parameters #(
  parameter PROFILE=3,
  parameter NUM_LAYERS=PROFILE==1 ? 24 : PROFILE==2 ? 28 : 36,
  parameter HIDDEN_SIZE=PROFILE==1 ? 896 : PROFILE==2 ? 1536 : 2048,
  parameter INTERMEDIATE_SIZE=PROFILE==1 ? 4864 : PROFILE==2 ? 8960 : 11008,
  parameter NUM_Q_HEADS=PROFILE==1 ? 14 : PROFILE==2 ? 12 : 16,
  parameter NUM_KV_HEADS=2,
  parameter HEAD_DIM=PROFILE==1 ? 64 : 128,
  parameter GROUP_SIZE=128, AWQ_BITS=4, VOCAB_SIZE=151936,
  parameter MAX_SEQ_LEN=32768, BANKS=8, CACHE_MODE=0, INT4_ASYM=0,
  parameter CACHE_BLOCK=1, QUEUE_DEPTH=3, TILE_K=128, TILE_ROWS=8
) ();
  localparam [127:0] L=NUM_LAYERS, H=HIDDEN_SIZE, I=INTERMEDIATE_SIZE;
  localparam [127:0] Q=NUM_Q_HEADS, K=NUM_KV_HEADS, D=HEAD_DIM;
  localparam [127:0] G=GROUP_SIZE, V=VOCAB_SIZE, S=MAX_SEQ_LEN;
  localparam [127:0] SG=GROUP_SIZE>0 ? GROUP_SIZE : 1;
  localparam [127:0] SK=NUM_KV_HEADS>0 ? NUM_KV_HEADS : 1;
  localparam [127:0] CB=CACHE_BLOCK>0 ? CACHE_BLOCK : 1;
  localparam [127:0] CG=PROFILE==3 ? (CACHE_MODE==2 ? 64 : 32) : CB;
  localparam [127:0] BLOCKS=(D+CG-1)/CG;
  localparam [127:0] WORDS=(CG*(CACHE_MODE==2 ? 4 : 8)+31)/32;
  localparam [127:0] U32=128'hffffffff, U64=128'hffffffffffffffff;
  localparam [127:0] EXTENT=H>I ? H : I;
  localparam VALID =
    (PROFILE==1 || PROFILE==2 || PROFILE==3) &&
    NUM_LAYERS>0 && HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 &&
    NUM_Q_HEADS>0 && NUM_KV_HEADS>0 && HEAD_DIM>0 && GROUP_SIZE>0 &&
    VOCAB_SIZE>0 && MAX_SEQ_LEN>0 && S<=32768 &&
    AWQ_BITS==4 && (BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) &&
    QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16 &&
    TILE_K>0 && TILE_K<=128 && TILE_K%8==0 && TILE_ROWS>=1 && TILE_ROWS<=8 &&
    (INT4_ASYM==0 || INT4_ASYM==1) &&
    (CACHE_MODE==0 || CACHE_MODE==1 || (PROFILE==3 && CACHE_MODE==2)) &&
    !(PROFILE==1 && CACHE_MODE!=0) &&
    H==Q*D && Q%SK==0 && D%2==0 &&
    H%8==0 && I%8==0 && H%SG==0 && I%SG==0 &&
    (PROFILE!=3 || Q==8*K) &&
    (PROFILE==3 || ((K*D)%8==0 && CACHE_BLOCK>0 &&
      (CB&(CB-1))==0 && D%CB==0)) &&
    L<=U32 && H<=U32 && I<=U32 && Q<=U32 && K<=U32 && D<=U32 &&
    G<=U32 && V<=U32 && K*D<=U32 && 2*D<=U32 &&
    K*BLOCKS*WORDS<=U32 && K*BLOCKS<=U32 &&
    15*EXTENT<=U32 &&
    4*V*H<=U64 && 4*L*H*I<=U64 && 4*L*H*H<=U64 &&
    4*L*S*K*D<=U64 && 4*L*S*K*BLOCKS*WORDS<=U64 &&
    4*L*S*K*BLOCKS<=U64 &&
    D*128'd4611686018427387904 < (128'd1<<95) &&
    S*128'd16777216 < (128'd1<<64);
  generate if (!VALID) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3 PARAMETER ERROR: dimensions, profile, modes or address bounds");
  end endgenerate
endmodule
