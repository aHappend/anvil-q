"""Explicit illegal-parameter diagnostics must survive whole-top elaboration."""

from execution import ROOT, relative


COMPACT = dict(NUM_LAYERS=1, HIDDEN_SIZE=16, INTERMEDIATE_SIZE=24, NUM_Q_HEADS=8,
               NUM_KV_HEADS=1, HEAD_DIM=2, GROUP_SIZE=8, VOCAB_SIZE=1,
               MAX_SEQ_LEN=1, BANKS=1, TILE_K=8, TILE_ROWS=1, QUEUE_DEPTH=3)
INVALID = (
    ("profile", {"PROFILE": 2}), ("layers", {"NUM_LAYERS": 0}),
    ("hidden", {"HIDDEN_SIZE": 0}), ("intermediate", {"INTERMEDIATE_SIZE": 0}),
    ("q_heads", {"NUM_Q_HEADS": 0}), ("kv_heads", {"NUM_KV_HEADS": 0}),
    ("dimension", {"HEAD_DIM": 0}), ("odd_dimension", {"HEAD_DIM": 3, "HIDDEN_SIZE": 24}),
    ("gqa_ratio", {"NUM_Q_HEADS": 4, "HIDDEN_SIZE": 8}),
    ("hidden_product", {"HIDDEN_SIZE": 24}), ("hidden_alignment", {"HIDDEN_SIZE": 17}),
    ("group_zero", {"GROUP_SIZE": 0}), ("group_limit", {"GROUP_SIZE": 129}),
    ("group_divisibility", {"GROUP_SIZE": 3}),
    ("awq_bits", {"AWQ_BITS": 8}), ("vocab", {"VOCAB_SIZE": 0}),
    ("sequence_zero", {"MAX_SEQ_LEN": 0}), ("sequence_limit", {"MAX_SEQ_LEN": 32769}),
    ("banks_zero", {"BANKS": 0}), ("banks_three", {"BANKS": 3}),
    ("cache_mode", {"CACHE_MODE": 3}), ("fp8_boolean", {"MODE1_FP8": 2}),
    ("affine_boolean", {"INT4_ASYM": 2}), ("cache_block", {"CACHE_BLOCK": 0}),
    ("queue_zero", {"QUEUE_DEPTH": 0}), ("queue_limit", {"QUEUE_DEPTH": 17}),
    ("tile_k_zero", {"TILE_K": 0}), ("tile_k_alignment", {"TILE_K": 9}),
    ("tile_k_limit", {"TILE_K": 136}), ("tile_rows_zero", {"TILE_ROWS": 0}),
    ("tile_rows_limit", {"TILE_ROWS": 9}),
    ("layer_address_overflow", {"NUM_LAYERS": 4294967296}),
)


def check(evidence, selected=None):
    results = []
    rtl = [relative(path) for path in sorted((ROOT / "rtl").glob("*.sv"))]
    rtl += ["anvil_q3_reference/rtl/anvil_q3_bank_scheduler.sv",
            "anvil_q3_reference/rtl/anvil_q3_mem_port.sv"]
    for name, changes in INVALID:
        if selected and name not in selected:
            continue
        directory = evidence.path / f"invalid-{name}"
        directory.mkdir()
        parameters = {**COMPACT, **changes}
        banks = parameters["BANKS"] if parameters["BANKS"] in (1, 2, 4, 8) else 1
        tb = "module tb;\nreg clk=0; always #5 clk=~clk;\n"
        tb += "anvil_q3_fp_top #(" + ",".join(f".{key}(64'd{value})" for key, value in parameters.items())
        tb += f""") dut(.clk(clk),.rst_n(1'b0),.cancel(1'b0),.token_valid(1'b0),
          .token_id(32'd0),.token_pos(32'd0),.new_sequence(1'b1),.token_phase(1'b0),
          .token_fp16(1'b0),.token_awq(1'b0),.logit_ready(1'b0),
          .mem_req_ready({banks}'d0),.mem_rsp_valid({banks}'d0),.mem_rsp_error({banks}'d0),
          .mem_rsp_rdata({32 * banks}'d0),.mem_rsp_tag({64 * banks}'d0));
          initial begin #20; $fatal(1,"MISSING EXPECTED PARAMETER DIAGNOSTIC"); end
        endmodule
        """
        (directory / "tb.sv").write_text(tb)
        evidence.run(["iverilog", "-g2012", "-Wall", "-s", "tb", "-o",
                      relative(directory / "sim.vvp"), *rtl, relative(directory / "tb.sv")])
        output = evidence.run(["vvp", "sim.vvp"], cwd=directory, timeout=600, expect_failure=True)
        if "PARAMETER ERROR" not in output.read_text():
            raise AssertionError(f"Illegal {name} did not reach explicit diagnostic: {relative(output)}")
        results.append({"case": name, "parameters": parameters, "diagnostic": relative(output)})
    if not results:
        raise AssertionError("No invalid-parameter comparisons")
    return results
