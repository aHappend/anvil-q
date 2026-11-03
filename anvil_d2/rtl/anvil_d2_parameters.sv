module anvil_d2_parameters #(
  parameter integer MODEL_MODE=0,
  parameter integer NUM_LAYERS=27, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=10944,
  parameter integer NUM_Q_HEADS=16, KV_LORA_RANK=512,
  parameter integer QK_NOPE_HEAD_DIM=128, QK_ROPE_HEAD_DIM=64, V_HEAD_DIM=128,
  parameter integer ROUTED_EXPERTS=64, TOP_K=6, SHARED_EXPERTS=2,
  parameter integer MOE_INTERMEDIATE_SIZE=1408, FIRST_DENSE_LAYERS=1,
  parameter integer VOCAB_SIZE=102400, MAX_SEQ_LEN=32768,
  parameter integer BANKS=8, QUEUE_DEPTH=3, TILE_K=128, TILE_ROWS=8,
  parameter integer GROUP_SIZE=128, MTP_K=4,
  localparam GEOMETRY_OK=
    NUM_LAYERS>=1 && NUM_LAYERS<=36 &&
    HIDDEN_SIZE>=8 && HIDDEN_SIZE<=2048 && (HIDDEN_SIZE & 7)==0 &&
    INTERMEDIATE_SIZE>=8 && INTERMEDIATE_SIZE<=11008 && (INTERMEDIATE_SIZE & 7)==0 &&
    NUM_Q_HEADS>=1 && NUM_Q_HEADS<=16 &&
    KV_LORA_RANK>=1 && KV_LORA_RANK<=512 &&
    QK_NOPE_HEAD_DIM>=1 && QK_NOPE_HEAD_DIM<=128 &&
    QK_ROPE_HEAD_DIM>=2 && QK_ROPE_HEAD_DIM<=64 && (QK_ROPE_HEAD_DIM & 1)==0 &&
    V_HEAD_DIM>=1 && V_HEAD_DIM<=128 &&
    ROUTED_EXPERTS>=1 && ROUTED_EXPERTS<=64 &&
    TOP_K>=1 && TOP_K<=6 && TOP_K<=ROUTED_EXPERTS && SHARED_EXPERTS==2 &&
    MOE_INTERMEDIATE_SIZE>=8 && MOE_INTERMEDIATE_SIZE<=1408 &&
    (MOE_INTERMEDIATE_SIZE & 7)==0 &&
    FIRST_DENSE_LAYERS>=0 && FIRST_DENSE_LAYERS<=NUM_LAYERS &&
    VOCAB_SIZE>=4 && VOCAB_SIZE<=151936 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    (BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8) &&
    QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16 &&
    TILE_K>=8 && TILE_K<=128 && (TILE_K & 7)==0 &&
    TILE_ROWS>=1 && TILE_ROWS<=8 && GROUP_SIZE==128 && MTP_K==4,
  localparam ADDRESS_OK=
    128'(NUM_Q_HEADS)*128'(V_HEAD_DIM)<=128'hffffffff &&
    128'(NUM_Q_HEADS)*128'(KV_LORA_RANK)<=128'hffffffff &&
    128'(NUM_Q_HEADS)*128'(QK_ROPE_HEAD_DIM)<=128'hffffffff &&
    128'(HIDDEN_SIZE)*3<=128'hffffffff &&
    128'(KV_LORA_RANK)*3<=128'hffffffff &&
    128'(KV_LORA_RANK)+128'(QK_ROPE_HEAD_DIM)<=128'hffffffff &&
    128'(MAX_SEQ_LEN)*(128'(KV_LORA_RANK)+128'(QK_ROPE_HEAD_DIM))*4<=128'hffffffff &&
    128'(HIDDEN_SIZE)*128'(MOE_INTERMEDIATE_SIZE)*4<=128'hffffffff &&
    128'(HIDDEN_SIZE)*128'(INTERMEDIATE_SIZE)*4<=128'hffffffff &&
    128'(HIDDEN_SIZE)*128'(VOCAB_SIZE)*4<=128'hffffffff,
  localparam LEGAL=MODEL_MODE==1 || (MODEL_MODE==0 && GEOMETRY_OK && ADDRESS_OK)
) ();
  generate
    if (MODEL_MODE!=0 && MODEL_MODE!=1) begin: invalid_mode
      initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: MODEL_MODE");
    end else if (MODEL_MODE==0 && !GEOMETRY_OK) begin: invalid_geometry
      initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: native geometry, GROUP_SIZE or MTP_K");
    end else if (MODEL_MODE==0 && !ADDRESS_OK) begin: invalid_addresses
      initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: native address product");
    end
  endgenerate
endmodule
