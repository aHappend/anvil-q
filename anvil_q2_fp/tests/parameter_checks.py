"""Real full-top elaboration and executable illegal-parameter diagnostics."""

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run


REDUCED = {
    "NUM_LAYERS": 1, "HIDDEN_SIZE": 48, "INTERMEDIATE_SIZE": 48,
    "NUM_Q_HEADS": 6, "NUM_KV_HEADS": 1, "HEAD_DIM": 8,
    "GROUP_SIZE": 12, "VOCAB_SIZE": 1, "MAX_SEQ_LEN": 1, "CACHE_BLOCK": 2,
}


def cases():
    yield "native-defaults", {}, True
    for banks in (1, 2, 4):
        for depth in (1, 3, 16):
            yield f"legal-b{banks}-q{depth}", dict(REDUCED, BANKS=banks, QUEUE_DEPTH=depth), True
    invalid = [
        ("BANKS", 0), ("BANKS", 3), ("QUEUE_DEPTH", 0), ("QUEUE_DEPTH", 17),
        *[(name, 0) for name in ("NUM_LAYERS", "HIDDEN_SIZE", "INTERMEDIATE_SIZE",
                                 "NUM_Q_HEADS", "NUM_KV_HEADS", "HEAD_DIM",
                                 "GROUP_SIZE", "VOCAB_SIZE", "MAX_SEQ_LEN", "CACHE_BLOCK")],
        ("FP_FORMAT", 2), ("WEIGHT_MODE", 2), ("CACHE_MODE", 2), ("AWQ_BITS", 3),
        ("HEAD_DIM", 7), ("NUM_KV_HEADS", 4), ("GROUP_SIZE", 7), ("CACHE_BLOCK", 3),
        ("CACHE_BLOCK", 16), ("VOCAB_SIZE", 100000000), ("MAX_SEQ_LEN", 16777216),
        ("HIDDEN_SIZE", 4294967296),
    ]
    for name, number in invalid:
        yield f"illegal-{name.lower()}-{number}", dict(REDUCED, **{name: number}), False


def execute():
    run = Run("verifier-parameters")
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        results = []
        run.receipt["generated_sha256"] = {}
        for label, parameters, legal in cases():
            bench = run.path / f"{label}.sv"
            overrides = ", ".join(f".{name}(64'd{number})"
                                  for name, number in parameters.items())
            bench.write_text(
                "module tb;\nreg clk=0,rst_n;\nalways #5 clk=~clk;\n"
                f"anvil_q2_fp_top #({overrides}) dut(.clk(clk),.rst_n(rst_n));\n"
                'initial begin rst_n=0; #11; $display("ELABORATED"); $finish; end\nendmodule\n')
            run.receipt["generated_sha256"][run.relative(bench)] = (
                hashlib.sha256(bench.read_bytes()).hexdigest())
            binary = run.path / f"{label}.vvp"
            run.command(["iverilog", "-g2012", "-Wall", "-s", "tb",
                         "-o", run.relative(binary),
                         *[str(p.relative_to(ROOT)) for p in sorted((ROOT / "rtl").glob("*.sv"))],
                         run.relative(bench)], f"{label}-compile")
            trace = run.command(["vvp", run.relative(binary)], f"{label}-simulation",
                                expected_codes=(0,) if legal else (1,))
            text = trace.read_text()
            if legal:
                assert "ELABORATED" in text and "PARAMETER ERROR" not in text, (
                    f"legal configuration rejected: {label}")
            else:
                assert "PARAMETER ERROR" in text, f"missing explicit parameter rejection: {label}"
            results.append({"case": label, "legal": legal, "parameters": parameters,
                            "outcome": "elaborated" if legal else "explicitly-rejected"})
        run.finish("passed-focused-only", metrics={"cases": results})
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    raise SystemExit(execute())
