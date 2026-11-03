"""Elaboration and explicit rejection matrix, separate from functional coverage."""

from model import Geometry


INVALID_TOP = (
    ("banks-zero", {"BANKS": 0}), ("banks-three", {"BANKS": 3}),
    ("lanes-eight", {"LANES_PER_BANK": 8}), ("cache-three", {"CACHE_MODE": 3}),
    ("asymmetric", {"INT4_ASYM": 1}), ("awq-eight", {"AWQ_BITS": 8}),
    ("layers-zero", {"NUM_LAYERS": 0}), ("hidden-zero", {"HIDDEN_SIZE": 0}),
    ("intermediate-zero", {"INTERMEDIATE_SIZE": 0}),
    ("query-ratio", {"NUM_Q_HEADS": 7}), ("kv-zero", {"NUM_KV_HEADS": 0}),
    ("dim-zero", {"HEAD_DIM": 0}), ("dim-odd", {"HEAD_DIM": 1}),
    ("group-zero", {"GROUP_SIZE": 0}), ("group-three", {"GROUP_SIZE": 3}),
    ("vocab-zero", {"VOCAB_SIZE": 0}), ("context-zero", {"MAX_SEQ_LEN": 0}),
    ("context-over", {"MAX_SEQ_LEN": 32769}), ("rows-zero", {"TILE_ROWS": 0}),
    ("rows-nine", {"TILE_ROWS": 9}), ("tile-eight", {"TILE_K": 8}),
    ("slots-one", {"TILE_SLOTS": 1}), ("slots-five", {"TILE_SLOTS": 5}),
    ("queue-zero", {"QUEUE_DEPTH": 0}), ("queue-seventeen", {"QUEUE_DEPTH": 17}),
    ("burst-three", {"BURST_BEATS": 3}), ("resident-zero", {"KV_RESIDENT_GROUPS": 0}),
    ("resident-over", {"KV_RESIDENT_GROUPS": 257}),
)


def invalid_bench(overrides):
    parameters = Geometry().parameters() | dict(BANKS=1, TILE_K=16, TILE_ROWS=1,
                                                TILE_SLOTS=3, KV_RESIDENT_GROUPS=3)
    parameters.update(overrides)
    return """
module verify_parameters;
  reg clk=0; always #5 clk=~clk;
  reg rst_n=0;
  anvil_q3_ht_top #(@PARAMETERS@) dut(
    .clk(clk),.rst_n(rst_n),.cancel(1'b0),.token_valid(1'b0),
    .token_id(32'd0),.token_pos(32'd0),.new_sequence(1'b0),.token_phase(1'b0),
    .logit_ready(1'b0),.ddr_cal_ready(1'b0),.model_commit(1'b0),
    .host_req_valid(1'b0),.host_req_write(1'b0),.host_req_address(33'd0),
    .host_req_wdata(512'd0),.host_req_byteenable(64'd0),.host_rsp_ready(1'b0),
    .avm_waitrequest(1'b0),.avm_readdata(512'd0),.avm_readdatavalid(1'b0),
    .avm_response(2'd0));
  initial begin #20; rst_n=1; #80; $fatal(1,"MISSING_PARAMETER_DIAGNOSTIC"); end
endmodule
""".replace("@PARAMETERS@", ",".join(f".{key}({value})" for key, value in parameters.items()))
