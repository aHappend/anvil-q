"""Bounded before/after response-scan comparison; not complete-check pacing.

Run from the project root: python3 tests/responder_scan_checks.py
Every case executes and independently compares both benches. Complete public
traces, fixture identities and numerical results must also match byte-for-byte.
The interpreted case is a compact single-token smoke, not an A-matrix substitute.
"""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decoder_checks import decoder_case
from execution import ROOT, Run, sha256, write_json
from parameters import startup_geometry


FAILED_RECEIPT = "evidence/check-behavior/20261028T082607Z-96412cd96bb2/tool-0124/receipt.json"
GUARDED = """          if (requests!=responses)
            for (j=PENDING-1;j>=0;j=j-1)
              if (selected[b]<0 && live[j] && pb[j]==b && due[j]<=cycle) selected[b]=j;"""
ORIGINAL = """          for (j=PENDING-1;j>=0;j=j-1)
            if (selected[b]<0 && live[j] && pb[j]==b && due[j]<=cycle) selected[b]=j;"""


def check(run):
    run.versions([("python3", "--version"), ("iverilog", "-V"), ("vvp", "-V"),
                  ("verilator", "--version")])
    source = (ROOT / "tests/top_tb.sv").read_text()
    if source.count(GUARDED) != 1:
        raise AssertionError("ambiguous response-scan repair site")
    benches = {}
    for variant, text in (("original", source.replace(GUARDED, ORIGINAL)),
                          ("guarded", source)):
        path = run.path / (variant + "_top_tb.sv")
        path.write_text(text)
        benches[variant] = path
    binding = {name: {"path": run.rel(path), "sha256": sha256(path)}
               for name, path in benches.items()}
    write_json(run.path / "bench-bindings.json", binding)
    geometry = replace(startup_geometry(3), BANKS=1, INTERMEDIATE_SIZE=8, VOCAB_SIZE=1)
    cases = (
        ("compact", geometry, "iverilog", 0),
        ("compact", geometry, "verilator", 0),
        ("multibank", replace(geometry, BANKS=8, CACHE_MODE=2, INT4_ASYM=1),
         "verilator", 0),
        ("cancel", replace(geometry, BANKS=8, VOCAB_SIZE=3), "verilator", 5),
    )
    results = []
    for label, g, simulator, prelude in cases:
        pair, fixtures, timings = {}, {}, {}
        for variant in ("original", "guarded"):
            first_record = len(run.records)
            pair[variant] = decoder_case(
                run, g, simulator=simulator, tokens=[0], prefill_tokens=1,
                prelude=prelude, label=label + "-" + variant,
                testbench=run.rel(benches[variant]))
            # Each invocation compiles and executes; an old executable is never reused.
            records = run.records[first_record:]
            if len(records) != 2 or any(record["exit_code"] != 0 for record in records):
                raise AssertionError("missing fresh successful compilation/simulation")
            timings[variant] = {
                "compile_seconds": records[0]["finished_at"] - records[0]["started_at"],
                "simulation_seconds": records[1]["finished_at"] - records[1]["started_at"],
                "stdout": records[1]["stdout"],
            }
            if pair[variant]["cycles"] > 500000:
                raise AssertionError("diagnostic exceeds compact cycle tier")
            result_path = list(run.path.glob(
                "*-" + simulator + "-" + label + "-" + variant + "/fixture.json"))
            if len(result_path) != 1:
                raise AssertionError("ambiguous diagnostic fixture")
            fixtures[variant] = json.loads(result_path[0].read_text())
        if pair["original"] != pair["guarded"]:
            raise AssertionError("scan guard changed public trace, comparisons or timing")
        for field in ("fixture_sha256", "inputs", "geometry", "seed", "tokens"):
            if fixtures["original"][field] != fixtures["guarded"][field]:
                raise AssertionError("scan comparison used different input " + field)
        if (pair["guarded"]["compared_bits"] <= 0 or
                pair["guarded"]["requests"] <= 0 or
                pair["guarded"]["stalls"]["request"] <= 0 or
                pair["guarded"]["active_cancellations"] != int(prelude == 5)):
            raise AssertionError("empty response/stall/cancellation comparison")
        results.append({"case": label, "simulator": simulator, "timings": timings,
                        "result": pair["guarded"]})
        write_json(run.path / "scan-results.json", results)
    for variant, path in benches.items():
        if sha256(path) != binding[variant]["sha256"]:
            raise AssertionError("diagnostic bench changed during execution")
    return {"cases": results, "bench_bindings": binding,
            "scope": "bounded equivalent response-scan optimization only; "
                     "not full-matrix pacing, simulator-contract authorization, "
                     "Quartus STA or physical HIL"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-of", default=FAILED_RECEIPT)
    args = parser.parse_args()
    run = Run("evidence/preparation/independent-responder-scan",
              "public responder empty-scan scaling repair", repair_of=args.repair_of)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        result = check(run)
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    run.finish("passed", result=result)


if __name__ == "__main__":
    main()
