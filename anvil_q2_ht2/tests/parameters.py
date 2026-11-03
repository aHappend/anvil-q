"""Parameter elaboration and executable diagnostic checks, not datapath coverage."""


def execute(run):
    from verify import ROOT, sources
    run.tool("iverilog")
    run.tool("vvp")
    compact = {
        "NUM_LAYERS": 1, "HIDDEN_SIZE": 8, "INTERMEDIATE_SIZE": 8,
        "NUM_Q_HEADS": 1, "NUM_KV_HEADS": 1, "HEAD_DIM": 8,
        "GROUP_SIZE": 1, "VOCAB_SIZE": 1, "MAX_SEQ_LEN": 1,
        "TILE_SLOTS": 2, "READ_OUTSTANDING": 1, "QUEUE_DEPTH": 1,
        "CACHE_BLOCK": 1, "HOT_BLOCKS": 1,
    }
    top = "anvil_q2_ht2_top"
    cases = []
    for label, overrides in (
        ("singleton", {}),
        ("nonpower-queue-sequence", {"QUEUE_DEPTH": 3, "MAX_SEQ_LEN": 5}),
        ("partial-columns", {"HIDDEN_SIZE": 120, "NUM_Q_HEADS": 15,
                             "INTERMEDIATE_SIZE": 136, "GROUP_SIZE": 8}),
        ("medium", {"HIDDEN_SIZE": 64, "NUM_Q_HEADS": 8,
                    "INTERMEDIATE_SIZE": 64, "GROUP_SIZE": 8, "CACHE_BLOCK": 8}),
        ("maximum-block", {"HIDDEN_SIZE": 128, "HEAD_DIM": 128,
                           "INTERMEDIATE_SIZE": 128, "GROUP_SIZE": 128,
                           "CACHE_BLOCK": 128}),
    ):
        cases.append((top, label, {**compact, **overrides}, False))
    invalid = {
        "NUM_LAYERS": (0, 29), "HIDDEN_SIZE": (0, 1544),
        "INTERMEDIATE_SIZE": (0, 8968, 9), "NUM_Q_HEADS": (0, 17),
        "NUM_KV_HEADS": (0, 3), "HEAD_DIM": (0, 3, 130),
        "GROUP_SIZE": (0, 3, 256, 16), "VOCAB_SIZE": (0, 151937),
        "MAX_SEQ_LEN": (0, 32769), "BANKS": (0, 8),
        "LANES_PER_BANK": (0, 4), "DDR_DATA_WIDTH": (0, 256),
        "TILE_SLOTS": (0, 1, 9), "READ_OUTSTANDING": (0, 17),
        "QUEUE_DEPTH": (0, 17), "CACHE_BLOCK": (0, 3, 256, 16),
        "HOT_BLOCKS": (0, 65),
    }
    for parameter, values in invalid.items():
        for value in values:
            cases.append((top, f"invalid-{parameter}-{value}",
                          {**compact, parameter: value}, True))
    cases.append((top, "invalid-hidden-head-shape", {**compact, "HIDDEN_SIZE": 16}, True))
    cases.append((top, "invalid-query-kv-ratio", {
        **compact, "HIDDEN_SIZE": 24, "NUM_Q_HEADS": 3, "NUM_KV_HEADS": 2}, True))
    for parameter, values in (("NUM_LAYERS", (0, 29)), ("MAX_SEQ_LEN", (0, 32769))):
        for value in values:
            cases.append(("anvil_q2_ht2_spec_verifier", f"invalid-{parameter}-{value}",
                          {parameter: value}, True))
    cache = {"NUM_LAYERS": 1, "NUM_KV_HEADS": 1, "HEAD_DIM": 8,
             "CACHE_BLOCK": 1, "MAX_SEQ_LEN": 1, "VOCAB_SIZE": 1}
    for parameter, values in (
        ("NUM_LAYERS", (0, 29)), ("NUM_KV_HEADS", (0, 3)),
        ("HEAD_DIM", (0, 3, 130)), ("CACHE_BLOCK", (0, 3, 256, 16)),
        ("MAX_SEQ_LEN", (0, 32769)), ("VOCAB_SIZE", (0, 151937)),
    ):
        for value in values:
            cases.append(("anvil_q2_ht2_native_kv_store", f"invalid-{parameter}-{value}",
                          {**cache, parameter: value}, True))
    paths = [str(path.relative_to(ROOT)) for path in sources()]
    run.receipt["parameters"] = []
    for index, (module, label, parameters, rejected) in enumerate(cases):
        name = f"parameters-{index:03d}-{module}-{label}"
        binary = run.path / (name + ".vvp")
        try:
            run.command(["iverilog", "-g2012", "-Wall", "-s", module, "-o",
                         run.relative(binary),
                         *[f"-P{module}.{key}={value}" for key, value in parameters.items()],
                         *paths], name + "-compile")
            record = {"module": module, "case": label, "parameters": parameters,
                      "expect_rejection": rejected, "elaborated": True}
            if rejected:
                status, stdout, stderr = run.command(
                    ["vvp", run.relative(binary)], name + "-diagnostic", check=False,
                    timeout=600)
                if (status["exit_code"] == 0 or status["timed_out"] or
                        "PARAMETER ERROR" not in stdout + stderr):
                    raise RuntimeError(f"{module} {label}: missing explicit parameter rejection")
                record["executed_parameter_error"] = True
            else:
                record["scope"] = "elaboration only; no functional coverage claimed"
            run.receipt["parameters"].append(record)
            run.save()
        finally:
            binary.unlink(missing_ok=True)
    if not any(row["expect_rejection"] for row in run.receipt["parameters"]):
        raise RuntimeError("no parameter diagnostics executed")
