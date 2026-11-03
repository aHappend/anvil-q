"""Reconcile retained source-matched assertions; execute missing suites normally."""

import argparse
import copy
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, hashes, relative, remaining, timestamp
from retention import inventory
from verify import TOOLS, child, reconcile_coverage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_coverage_reconciliation.py", *sys.argv[1:]],
                   cwd=".", start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    os.environ.setdefault("HT3_CHECK_DEADLINE", str(time.time()+remaining()))
    try:
        versions = inventory(output, TOOLS)
        rows = [child(name, [f"tests/run_{name}.py", *options], output,
                      versions=versions)
                for name, options in (("attention_restart", []), ("attention", ["--compact"]),
                                      ("attention_timing", []))]
        negative = copy.deepcopy(rows)
        negative[0]["status"] = "failed"
        reconcile_coverage(negative)
        if negative[1].get("resolved_coverage"):
            raise AssertionError("failed supporting check incorrectly closed coverage")
        reconcile_coverage(rows)
        labels = rows[1].get("resolved_coverage", {}).get("labels", [])
        if set(labels) != {"abort/reset during accepted KV", "zero-latency KV response"}:
            raise AssertionError("current source-matched public assertions did not reconcile")
        if (rows[1].get("resident_tile_coverage", {}).get("cases") != 40
                or rows[1]["resident_tile_coverage"]["handoffs"] != 60
                or "resident-tile handoff edge assertions" in rows[1]["coverage_limits"]):
            raise AssertionError("complete resident-tile observations did not reconcile")
        missing = copy.deepcopy(negative)
        missing[1] = {k: v for k, v in rows[1].items()
                      if k not in ("resident_tile_coverage", "resolved_coverage")}
        missing[1]["coverage_limits"] = list(rows[1]["reported_coverage_limits"])
        missing[2]["status"] = "failed"
        reconcile_coverage(missing)
        if ("resident_tile_coverage" in missing[1]
                or "resident-tile handoff edge assertions" not in missing[1]["coverage_limits"]):
            raise AssertionError("failed timing evidence incorrectly closed resident coverage")
        if "subnormal/extreme directed vectors" not in rows[1]["coverage_limits"]:
            raise AssertionError("unexecuted numerical coverage was incorrectly closed")
        result = dict(status="passed", scope="cross-suite evidence reconciliation only",
                      assertions=5, rows=rows)
    except (OSError, RuntimeError, AssertionError, ValueError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    with (output/"result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"] != "passed"),
                   timed_out=remaining() <= 0, result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
