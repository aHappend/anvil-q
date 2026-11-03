module anvil_q1_ht2_parameters #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_Q_HEADS = 14, NUM_KV_HEADS = 2, HEAD_DIM = 64, GROUP_SIZE = 128,
  parameter AWQ_BITS = 4, VOCAB_SIZE = 151936, MAX_SEQ_LEN = 32768,
  parameter LANES = 64, BANKS = 8, LANES_PER_BANK = 8, DDR_WIDTH = 512,
  parameter TILE_BEATS = 256, KV_WINDOW = 128
) ();
  localparam SAFE_GROUP = GROUP_SIZE > 0 ? GROUP_SIZE : 1;
  localparam SAFE_KV = NUM_KV_HEADS > 0 ? NUM_KV_HEADS : 1;
  localparam LEGAL =
    NUM_LAYERS >= 1 && NUM_LAYERS <= 24 &&
    HIDDEN_SIZE >= 8 && HIDDEN_SIZE <= 896 &&
    INTERMEDIATE_SIZE >= 8 && INTERMEDIATE_SIZE <= 4864 &&
    NUM_Q_HEADS >= 1 && NUM_Q_HEADS <= 14 &&
    NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 &&
    HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0 &&
    HIDDEN_SIZE == NUM_Q_HEADS*HEAD_DIM && NUM_Q_HEADS % SAFE_KV == 0 &&
    (HIDDEN_SIZE & 7) == 0 && (INTERMEDIATE_SIZE & 7) == 0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7) == 0 &&
    GROUP_SIZE >= 1 && GROUP_SIZE <= HIDDEN_SIZE &&
    HIDDEN_SIZE % SAFE_GROUP == 0 && INTERMEDIATE_SIZE % SAFE_GROUP == 0 &&
    VOCAB_SIZE >= 1 && VOCAB_SIZE <= 151936 &&
    MAX_SEQ_LEN >= 1 && MAX_SEQ_LEN <= 32768 &&
    AWQ_BITS == 4 && LANES == 64 && BANKS == 8 && LANES_PER_BANK == 8 &&
    DDR_WIDTH == 512 && TILE_BEATS >= 1 && TILE_BEATS <= 256 &&
    KV_WINDOW >= 1 && KV_WINDOW <= 128 && KV_WINDOW <= MAX_SEQ_LEN;
  generate if (!LEGAL) begin : g_illegal
    initial $fatal(1, "ANVIL_Q1_HT2 PARAMETER ERROR: unsupported dimensions or structure");
  end endgenerate
endmodule
