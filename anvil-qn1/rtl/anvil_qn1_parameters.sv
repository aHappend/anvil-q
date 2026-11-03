module anvil_qn1_parameters #(
  parameter PROFILE=3, COMPACT=0,
  parameter NUM_LAYERS=PROFILE==3 ? 36 : 28,
  parameter HIDDEN_SIZE=PROFILE==1 ? 1024 : PROFILE==2 ? 2048 : 2560,
  parameter INTERMEDIATE_SIZE=PROFILE==1 ? 3072 : PROFILE==2 ? 6144 : 9728,
  parameter NUM_Q_HEADS=PROFILE==3 ? 32 : 16, NUM_KV_HEADS=8,
  parameter HEAD_DIM=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=40960,
  parameter GROUP_SIZE=128, BANKS=8, QUEUE_DEPTH=3
) ();
  localparam VALID=anvil_qn1_pkg::configuration_valid(PROFILE,COMPACT,
    NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,VOCAB_SIZE,MAX_SEQ_LEN,GROUP_SIZE,BANKS,QUEUE_DEPTH);
  generate if (!VALID) begin: invalid_parameters
    initial $fatal(1,"ANVIL_QN1 PARAMETER ERROR: profile, geometry or address bounds");
  end endgenerate
endmodule
