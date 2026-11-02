"""Legal elaboration boundaries and executable invalid-parameter diagnostics."""

import json

from receipts import ROOT, execute, relative


def run_parameters(run):
    sources = [relative(path) for directory in ("anvil_q3_ht_reference/rtl", "rtl")
               for path in sorted((ROOT / directory).glob("*.sv"))]
    tile = "anvil_q3_ht2_tile_batch_mac"
    top = "anvil_q3_ht2_top"
    sparse = "anvil_q3_ht2_sparse_dma"
    cases = [(f"lanes-{lanes}", tile, {"WEIGHT_LANES": lanes,
                                      "HIDDEN_SIZE": 16, "NUM_KV_HEADS": 1,
                                      "HEAD_DIM": 2}, False)
             for lanes in (8, 16, 32, 64, 128)]
    cases += [
        ("bad-k", tile, {"K": 3}, True),
        ("zero-lanes", tile, {"WEIGHT_LANES": 0}, True),
        ("unsupported-lanes", tile, {"WEIGHT_LANES": 7}, True),
        ("zero-head", tile, {"HEAD_DIM": 0}, True),
        ("odd-head", tile, {"HEAD_DIM": 127}, True),
        ("zero-scan", sparse, {"MAX_COLUMNS": 0}, True),
        ("negative-scan", sparse, {"MAX_COLUMNS": -1}, True),
        ("bad-retain-scan", sparse, {"RETAIN_SCAN": 2}, True),
        ("bad-group", top, {"GROUP_SIZE": 7}, True),
        ("zero-layers", top, {"NUM_LAYERS": 0}, True),
        ("zero-hidden", top, {"HIDDEN_SIZE": 0}, True),
        ("zero-vocabulary", top, {"VOCAB_SIZE": 0}, True),
        ("zero-sequence", top, {"MAX_SEQ_LEN": 0}, True),
        ("overlong-sequence", top, {"MAX_SEQ_LEN": 32769}, True),
        ("bad-gqa", top, {"NUM_Q_HEADS": 8}, True),
        ("bad-cache", top, {"CACHE_MODE": 3}, True),
        ("bad-queue", top, {"QUEUE_DEPTH": 0}, True),
        ("bad-burst", top, {"BURST_BEATS": 3}, True),
        ("kv-region-overflow", top, {"NUM_LAYERS": 4096}, True),
    ]
    observations = []
    for name, module, parameters, invalid in cases:
        executable = run / f"{name}.vvp"
        compile_result = execute(run, f"elaborate-{name}", [
            "iverilog", "-g2012", "-Wall", "-s", module,
            *[f"-P{module}.{key}={value}" for key, value in parameters.items()],
            "-o", relative(executable), *sources], ["iverilog", "-V"])
        row = {"case": name, "module": module, "parameters": parameters,
               "elaboration_receipt": relative(compile_result / "receipt.json"),
               "functional_simulation": False}
        if invalid:
            result = execute(run, f"diagnostic-{name}", ["vvp", relative(executable)],
                             ["vvp", "-V"], expect=1)
            raw = (result / "stdout.txt").read_text() + (result / "stderr.txt").read_text()
            if "PARAMETER ERROR" not in raw:
                raise AssertionError(f"invalid parameter did not reach explicit diagnostic: {name}")
            row["diagnostic_receipt"] = relative(result / "receipt.json")
        observations.append(row)
    summary = {"legal_lane_widths": [8, 16, 32, 64, 128],
               "elaborations": len(observations),
               "invalid_diagnostics": sum(invalid for _, _, _, invalid in cases),
               "observed": observations}
    (run / "parameters-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
