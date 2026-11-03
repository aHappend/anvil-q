"""Differential legacy behavior using both unchanged-parent and HT2 public pins."""

import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from integrated import generate
from receipts import ROOT, cleanup_build, compile_verilator, execute, relative


def run_compatibility(run, mode):
    model, _, lines, _ = generate(run, layers=1, nonzero=True)
    obj = run / "compatibility-obj"
    sources = [relative(path) for directory in ("anvil_q3_ht_reference/rtl", "rtl")
               for path in sorted((ROOT / directory).glob("*.sv"))]
    binary = compile_verilator(run, "compatibility-compile", [
        "verilator", "--binary", "--timing", "-Wno-fatal",
        "--top-module", "compatibility_tb", f"-GCACHE_MODE={mode}",
        "--Mdir", relative(obj), "-j", "2",
        "--output-split", "20000", "--output-split-cfuncs", "2000",
        "-CFLAGS", "-O3", *sources, "tests/compatibility_tb.sv"],
        obj, "Vcompatibility_tb")
    try:
        result = execute(run, "compatibility-simulate",
                         [relative(binary), f"+model={relative(model)}"],
                         ["verilator", "--version"])
    finally:
        cleanup_build(obj)
    records = [json.loads(line.removeprefix("RESULT ")) for line in
               (result / "stdout.txt").read_text().splitlines() if line.startswith("RESULT ")]
    if len(records) != 1:
        raise AssertionError("missing complete public-pin compatibility results")
    observed = records[0]
    expected = {"model_lines": lines, "completed_tokens": 2, "logits": 16,
                "rejected_commands": 2, "cancellations": 1, "read_errors": 1}
    for field, value in expected.items():
        if observed.get(field) != value:
            raise AssertionError(f"incomplete legacy observations: {field}")
    for field in ("host_transactions", "ddr_reads", "ddr_writes", "compared_edges",
                  "blocked_requests", "blocked_logits"):
        if observed.get(field, 0) <= 0:
            raise AssertionError(f"unobserved legacy event: {field}")
    summary = {"mode": mode, "observed": observed,
               "compared_transactions": sum(observed[field] for field in (
                   "host_transactions", "ddr_reads", "ddr_writes", "logits")),
               "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
               "oracle": "unchanged parent RTL on identical public inputs",
               "fixture": "one-layer legal nonzero AWQ model, 64 hidden, vocabulary 8",
               "receipt": relative(result / "receipt.json")}
    (run / "compatibility-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
