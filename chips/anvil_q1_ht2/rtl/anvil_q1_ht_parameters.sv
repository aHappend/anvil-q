module anvil_q1_ht_parameters #(
  parameter NUM_LAYERS = 24,
  parameter HIDDEN_SIZE = 896,
  parameter INTERMEDIATE_SIZE = 4864,
  parameter NUM_Q_HEADS = 14,
  parameter NUM_KV_HEADS = 2,
  parameter HEAD_DIM = 64,
  parameter GROUP_SIZE = 128,
  parameter AWQ_BITS = 4,
  parameter VOCAB_SIZE = 151936,
  parameter MAX_SEQ_LEN = 32768,
  parameter LANES = 64,
  parameter BANKS = 8,
  parameter LANES_PER_BANK = 8,
  parameter DDR_WIDTH = 512,
  parameter TILE_BEATS = 256,
  parameter KV_WINDOW = 128
) ();
  localparam SAFE_GROUP = GROUP_SIZE > 0 ? GROUP_SIZE : 1;
  localparam SAFE_KV = NUM_KV_HEADS > 0 ? NUM_KV_HEADS : 1;
  localparam VALID =
    NUM_LAYERS > 0 && NUM_LAYERS <= 24 &&
    HIDDEN_SIZE > 0 && HIDDEN_SIZE <= 896 &&
    INTERMEDIATE_SIZE > 0 && INTERMEDIATE_SIZE <= 4864 &&
    NUM_Q_HEADS > 0 && NUM_Q_HEADS <= 14 &&
    NUM_KV_HEADS > 0 && NUM_KV_HEADS <= 2 &&
    HEAD_DIM > 0 && HEAD_DIM <= 64 &&
    GROUP_SIZE > 0 && GROUP_SIZE <= HIDDEN_SIZE &&
    VOCAB_SIZE > 0 && VOCAB_SIZE <= 151936 &&
    MAX_SEQ_LEN > 0 && MAX_SEQ_LEN <= 32768 &&
    HIDDEN_SIZE == NUM_Q_HEADS * HEAD_DIM &&
    NUM_Q_HEADS % SAFE_KV == 0 && HEAD_DIM % 2 == 0 &&
    HIDDEN_SIZE % 8 == 0 && INTERMEDIATE_SIZE % 8 == 0 &&
    (NUM_KV_HEADS * HEAD_DIM) % 8 == 0 &&
    HIDDEN_SIZE % SAFE_GROUP == 0 && INTERMEDIATE_SIZE % SAFE_GROUP == 0 &&
    AWQ_BITS == 4 && LANES == 64 && BANKS == 8 && LANES_PER_BANK == 8 &&
    DDR_WIDTH == 512 && TILE_BEATS >= 1 && TILE_BEATS <= 256 &&
    KV_WINDOW >= 1 && KV_WINDOW <= 128 && KV_WINDOW <= MAX_SEQ_LEN;

  generate
    if (!VALID) begin : invalid_parameters
      initial $fatal(1, "ANVIL_Q1_HT PARAMETER ERROR: unsupported dimensions or structure");
    end
  endgenerate
endmodule
