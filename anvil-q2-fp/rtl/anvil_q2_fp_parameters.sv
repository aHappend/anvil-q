module anvil_q2_fp_parameters #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  NUM_Q_HEADS=12, NUM_KV_HEADS=2, HEAD_DIM=128, GROUP_SIZE=128,
  AWQ_BITS=4, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  BANKS=4, FP_FORMAT=0, WEIGHT_MODE=0, CACHE_MODE=0, CACHE_BLOCK=16,
  QUEUE_DEPTH=3
)();
  localparam [127:0] L=NUM_LAYERS, H=HIDDEN_SIZE, I=INTERMEDIATE_SIZE;
  localparam [127:0] Q=NUM_Q_HEADS, K=NUM_KV_HEADS, D=HEAD_DIM;
  localparam [127:0] G=GROUP_SIZE, V=VOCAB_SIZE, S=MAX_SEQ_LEN;
  localparam [127:0] B=CACHE_BLOCK, LIMIT=128'd4294967295;
  localparam SG=GROUP_SIZE>0 ? GROUP_SIZE : 1;
  localparam SK=NUM_KV_HEADS>0 ? NUM_KV_HEADS : 1;
  localparam SB=CACHE_BLOCK>0 ? CACHE_BLOCK : 1;
  localparam [127:0] NB=D/SB, NW=(B+3)/4;
  localparam VALID =
    NUM_LAYERS>0 && HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 &&
    NUM_Q_HEADS>0 && NUM_KV_HEADS>0 && HEAD_DIM>0 && GROUP_SIZE>0 &&
    VOCAB_SIZE>0 && MAX_SEQ_LEN>0 && AWQ_BITS==4 &&
    (BANKS==1 || BANKS==2 || BANKS==4) &&
    (FP_FORMAT==0 || FP_FORMAT==1) && (WEIGHT_MODE==0 || WEIGHT_MODE==1) &&
    (CACHE_MODE==0 || CACHE_MODE==1) && QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16 &&
    CACHE_BLOCK>0 && (CACHE_BLOCK & (CACHE_BLOCK-1))==0 && HEAD_DIM%SB==0 &&
    L<=LIMIT && H<=LIMIT && I<=LIMIT && Q<=LIMIT && K<=LIMIT &&
    D<=LIMIT && G<=LIMIT && V<=LIMIT && S<=128'd16777215 &&
    H==Q*D && NUM_Q_HEADS%SK==0 && HEAD_DIM%2==0 &&
    HIDDEN_SIZE%SG==0 && INTERMEDIATE_SIZE%SG==0 &&
    HIDDEN_SIZE%8==0 && INTERMEDIATE_SIZE%8==0 && (K*D)%8==0 &&
    V*H<=LIMIT && H*H<=LIMIT && H*I<=LIMIT && H*K*D<=LIMIT &&
    L*S*K*D<=LIMIT && S*D<=LIMIT && 2*D<=LIMIT &&
    15*H<=LIMIT && 15*I<=LIMIT &&
    K*NB*NW<=LIMIT && L*S*K*NB*NW<=LIMIT && L*S*K*NB<=LIMIT;
  generate if (!VALID) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_FP PARAMETER ERROR: dimensions, modes or address bounds");
  end endgenerate
endmodule
