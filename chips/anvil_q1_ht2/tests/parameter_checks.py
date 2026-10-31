"""Diagnostic-safe illegal geometry checks, separate from functional coverage."""

import uuid

from decoder_reference import Geometry
from evidence import ROOT, execute, relative, require_success
from integration_checks import TOP_PINS
from leaf_checks import HEADER


INVALID = (
    ("zero-layers", {"NUM_LAYERS": 0}),
    ("excess-layers", {"NUM_LAYERS": 25}),
    ("hidden-zero", {"HIDDEN_SIZE": 0}),
    ("hidden-too-large", {"HIDDEN_SIZE": 904}),
    ("hidden-alignment", {"HIDDEN_SIZE": 9}),
    ("intermediate-zero", {"INTERMEDIATE_SIZE": 0}),
    ("intermediate-too-large", {"INTERMEDIATE_SIZE": 4872}),
    ("intermediate-alignment", {"INTERMEDIATE_SIZE": 9}),
    ("zero-query-heads", {"NUM_Q_HEADS": 0}),
    ("excess-query-heads", {"NUM_Q_HEADS": 15}),
    ("zero-kv-heads", {"NUM_KV_HEADS": 0}),
    ("excess-kv-heads", {"NUM_KV_HEADS": 3}),
    ("odd-head-dimension", {"HEAD_DIM": 7}),
    ("head-too-small", {"HEAD_DIM": 0}),
    ("head-too-large", {"HEAD_DIM": 66}),
    ("query-hidden-mismatch", {"NUM_Q_HEADS": 2}),
    ("gqa-indivisible", {"NUM_Q_HEADS": 3, "NUM_KV_HEADS": 2, "HIDDEN_SIZE": 24}),
    ("kv-width-alignment", {"NUM_Q_HEADS": 2, "HEAD_DIM": 4}),
    ("zero-group", {"GROUP_SIZE": 0}),
    ("group-too-large", {"GROUP_SIZE": 9}),
    ("group-hidden-divisibility", {"GROUP_SIZE": 3, "INTERMEDIATE_SIZE": 24}),
    ("group-intermediate-divisibility", {"GROUP_SIZE": 3, "INTERMEDIATE_SIZE": 8,
                                       "HIDDEN_SIZE": 24, "NUM_Q_HEADS": 3}),
    ("zero-vocabulary", {"VOCAB_SIZE": 0}),
    ("excess-vocabulary", {"VOCAB_SIZE": 151937}),
    ("zero-sequence", {"MAX_SEQ_LEN": 0}),
    ("excess-sequence", {"MAX_SEQ_LEN": 32769}),
    ("awq-width", {"AWQ_BITS": 3}),
    ("array-lanes", {"LANES": 32}),
    ("array-banks", {"BANKS": 4}),
    ("array-bank-lanes", {"LANES_PER_BANK": 4}),
    ("ddr-width", {"DDR_WIDTH": 256}),
    ("zero-tile", {"TILE_BEATS": 0}),
    ("excess-tile", {"TILE_BEATS": 257}),
    ("zero-window", {"KV_WINDOW": 0}),
    ("excess-window", {"KV_WINDOW": 129}),
    ("window-exceeds-sequence", {"MAX_SEQ_LEN": 1, "KV_WINDOW": 2}),
)


def run(directory):
    results = []
    sources = sorted((ROOT / "rtl").glob("anvil_q1_ht2_*.sv"))
    for name, changes in INVALID:
        work = directory / f"{name}-{uuid.uuid4().hex[:8]}"
        work.mkdir()
        parameters = Geometry().parameters()
        parameters.update(changes)
        body = TOP_PINS.replace("PARAMETERS", ",".join(
            f".{key}({value})" for key, value in parameters.items()))
        tb, binary = work / "tb.sv", work / "simulation.vvp"
        tb.write_text(HEADER + body + "\ninitial begin #20; $fatal(1,\"MISSING_DIAGNOSTIC\"); end\nendmodule\n")
        require_success(execute(
            ["iverilog", "-g2012", "-Wall", "-s", "tb", "-o", relative(binary),
             *map(relative, sources), relative(tb)], directory, name + "-compile",
            inputs=[*sources, tb]))
        receipt, run = execute(["vvp", relative(binary)], directory, name + "-diagnostic",
                               timeout=55, inputs=[tb, *sources])
        output = (run / "stdout.txt").read_text() + (run / "stderr.txt").read_text()
        if receipt["exit_code"] == 0 or receipt["timed_out"] or "PARAMETER ERROR" not in output:
            raise AssertionError(f"diagnostic not reached: {name}, {relative(run / 'receipt.json')}")
        results.append({"name": name, "parameters": changes,
                        "expected_rejection_observed": True,
                        "receipt": relative(run / "receipt.json")})
    return results
