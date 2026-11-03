"""Bounded supported-frontend probe, including independent transformed-leaf checks."""

import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, execute, hashes, relative, remaining, timestamp
from reference import primitive_vectors
from yosys_frontend import materialize


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_frontend.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    failures = []
    rows = []
    try:
        sources = materialize(output)
        binary = output / "primitive.vvp"
        selected = [p for p in sources if Path(p).name in {
            f"anvil_q1_ht3_{name}.sv" for name in
            ("reset_sync", "fp32_add", "fp32_mul", "expand16", "narrow32")}]
        vectors = output / "vectors.txt"
        count = 0
        with vectors.open("x") as out:
            for op, a, b, fp, expected in primitive_vectors(17, compact=True):
                out.write(f"{op} {a:08x} {b:08x} {fp} {expected:08x}\n")
                count += 1
        execute(["iverilog", "-g2012", "-Wall", "-s", "primitive_tb",
                 "-o", relative(binary), *selected, "tests/primitive_tb.sv"],
                output, "compile", ["iverilog", "-V"])
        text = execute(["vvp", relative(binary), f"+vectors={relative(vectors)}", "+seed=17"],
                       output, "simulation", ["iverilog", "-V"])
        summary = re.search(r"SUMMARY primitive comparisons=(\d+)", text)
        if not summary or int(summary[1]) != count:
            raise AssertionError("transformed arithmetic missing independent comparisons")
        rows.append(dict(id="transformed-primitives", status="passed", comparisons=count))
        execute(["yosys", "-Q", "-T", "-p", "read_verilog -sv " + " ".join(sources) +
                 "; hierarchy -check -top anvil_q1_ht3_top; stat"],
                output, "frontend", ["yosys", "-V"])
        rows.append(dict(id="default-hierarchy-frontend", status="passed"))
    except (RuntimeError, AssertionError, ValueError) as exc:
        failures.append(str(exc))
    result = dict(status="failed" if failures else "passed", runs=rows, failures=failures)
    with (output / "result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(exit=1 if failures else 0, end=timestamp(),
                   timed_out=any(json.loads(p.read_text()).get("timed_out", False)
                                 for p in output.glob("*.receipt.json")),
                   stdout=relative(output / "frontend.stdout.txt"),
                   stderr=relative(output / "frontend.stderr.txt"))
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
