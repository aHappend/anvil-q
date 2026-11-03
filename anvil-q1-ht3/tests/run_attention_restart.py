"""Distinguish stale KV-fault ownership from legal immediate-error completion."""

import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, clean_objects, execute, hashes, relative, remaining, timestamp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_attention_restart.py", *sys.argv[1:]],
                   cwd=".", start=timestamp(), source_sha256=hashes(),
                   timeout=remaining(), tool_version=sys.version)
    objects = output / "compile-obj"
    failures = []
    text = ""
    try:
        execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                 "--top-module", "attention_restart_tb", "--Mdir", relative(objects),
                 *[relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))],
                 "tests/attention_restart_tb.sv"], output, "compile",
                ["verilator", "--version"])
        try:
            text = execute([relative(objects / "Vattention_restart_tb")], output,
                           "simulation", ["verilator", "--version"])
        except RuntimeError as exc:
            failures.append(str(exc))
            text = (output / "simulation.stdout.txt").read_text()
        summary = re.search(r"SUMMARY attention_restart accepts=(\d+) completions=(\d+) "
                            r"fault_responses=(\d+) failures=(\d+) abort_drains=(\d+) "
                            r"reset_canceled=(\d+) zero_responses=(\d+)", text)
        if not summary or tuple(map(int, summary.groups())) != (9, 8, 1, 0, 1, 1, 8):
            failures.append("nine accepted commands require eight completions plus one "
                            "reset cancellation, one aborted response drain and eight zero-latency responses")
    except (RuntimeError, AssertionError) as exc:
        failures.append(str(exc))
    finally:
        clean_objects(objects)
    result = dict(status="failed" if failures else "passed", failures=failures,
                  observations=[line for line in text.splitlines()
                                if line.startswith(("ACCEPT ", "POST_ACCEPT ", "FAULT_RESPONSE ",
                                                    "OBSERVATION ", "SUMMARY "))])
    with (output / "result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(exit=1 if failures else 0, end=timestamp(),
                   timed_out=any(json.loads(p.read_text()).get("timed_out", False)
                                 for p in output.glob("*.receipt.json")),
                   stdout=relative(output / "simulation.stdout.txt"),
                   stderr=relative(output / "simulation.stderr.txt"))
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
