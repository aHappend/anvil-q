"""Source-bound unit shards. All diagnostics are retained in a fresh directory."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import primitive_vectors, quantizer_vectors
from execution import ROOT, clean_objects, execute, hashes, relative, remaining


def run(suite, simulator, seed, output, limit=None, offset=0):
    vectors = output / "vectors.txt"
    rows = (primitive_vectors(seed, compact=simulator == "icarus")
            if suite == "primitive" else quantizer_vectors(seed))
    count = 0
    with vectors.open("x") as out:
        for ordinal, row in enumerate(rows):
            if ordinal < offset:
                continue
            if limit is not None and count == limit:
                break
            if suite == "primitive":
                op, a, b, fp16, expected = row
                out.write(f"{op} {a:08x} {b:08x} {fp16} {expected:08x}\n")
            else:
                x, scale, int8, code, error = row
                out.write(f"{x:08x} {scale:08x} {int8} {code:04x} {error}\n")
            count += 1
    sources = ["rtl/anvil_q1_ht3_00_fp_pkg.sv",
               "rtl/anvil_q1_ht3_reset_sync.sv"]
    if suite == "primitive":
        sources += [f"rtl/anvil_q1_ht3_{module}.sv" for module in
                    ("fp32_add", "fp32_mul", "expand16", "narrow32")]
    else:
        sources.append("rtl/anvil_q1_ht3_kv_quantize.sv")
    tb = f"tests/{suite}_tb.sv"
    if simulator == "icarus":
        binary = output / "simulation.vvp"
        execute(["iverilog", "-g2012", "-Wall", "-s", f"{suite}_tb",
                 "-o", relative(binary), *sources, tb], output, "compile",
                ["iverilog", "-V"])
        argv = ["vvp", relative(binary)]
        version = ["iverilog", "-V"]
    else:
        objects = output / "compile-obj"
        execute(["verilator", "--binary", "--timing", "-Wno-fatal",
                 "-j", "2", "--top-module", f"{suite}_tb",
                 "--Mdir", relative(objects), *sources, tb], output, "compile",
                ["verilator", "--version"])
        argv = [relative(objects / f"V{suite}_tb")]
        version = ["verilator", "--version"]
    try:
        text = execute([*argv, f"+vectors={relative(vectors)}", f"+seed={seed}"],
                       output, "simulation", version)
    finally:
        if simulator == "verilator":
            clean_objects(objects)
    summary = re.search(rf"SUMMARY {suite} comparisons=(\d+)\b", text)
    if not summary or int(summary[1]) != count:
        raise AssertionError(f"missing complete summary: expected {count}; {text[-2000:]}")
    if suite == "quantizer" and (limit is None or offset == 0):
        errors = re.search(r"errors=(\d+)\b", text)
        if not errors or int(errors[1]) == 0:
            raise AssertionError("missing invalid-input error comparisons")
    result = {"suite": suite, "simulator": simulator, "seed": seed,
              "compared": count, "vector_sha256": hashlib.sha256(vectors.read_bytes()).hexdigest(),
              "status": "passed", "raw_summary": summary[0], "diagnostic_limit": limit}
    result["vector_offset"] = offset
    with (output / "result.json").open("x") as out:
        json.dump(result, out, indent=2)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("primitive", "quantizer"), required=True)
    parser.add_argument("--simulator", choices=("icarus", "verilator"), required=True)
    parser.add_argument("--seed", type=int, choices=(17, 89, 2026), default=17)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, help="bounded diagnostic prefix, not full coverage")
    parser.add_argument("--repair-of", help="project-relative immutable prior diagnostic receipt")
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()
    output = ROOT / args.output
    if output.exists():
        raise FileExistsError("fresh output required: " + args.output)
    output.mkdir(parents=True)
    receipt = {"kind": "independent-unit-preparation",
               "argv": ["python3", "tests/run_unit.py", *sys.argv[1:]], "cwd": ".",
               "start": datetime.now(timezone.utc).isoformat(), "timeout": remaining(),
               "source_sha256": hashes(), "tool_version": sys.version,
               "stdout": relative(output / "driver.stdout.txt"),
               "stderr": relative(output / "driver.stderr.txt")}
    if args.repair_of:
        receipt["repair_of"] = args.repair_of
    try:
        if args.suite == "quantizer" and args.simulator == "icarus" and args.limit is None:
            rows = list(quantizer_vectors(args.seed))
            results = []
            for offset in range(0, len(rows), 12000):
                shard = output / f"part-{offset:05d}-{hashlib.sha256(str(offset).encode()).hexdigest()[:8]}"
                shard.mkdir()
                results.append(run(args.suite, args.simulator, args.seed, shard,
                                   min(12000, len(rows)-offset), offset))
            if sum(r["compared"] for r in results) != len(rows):
                raise AssertionError("split quantizer omitted comparisons")
            result = dict(status="passed", suite=args.suite, simulator=args.simulator,
                          seed=args.seed, compared=len(rows), shards=results,
                          maximum_shard_cycle_bound=12000*28+8)
            with (output / "result.json").open("x") as out:
                json.dump(result, out, indent=2)
        else:
            result = run(args.suite, args.simulator, args.seed, output, args.limit, args.offset)
        (output / "driver.stdout.txt").write_text(json.dumps(result) + "\n")
        (output / "driver.stderr.txt").write_text("")
        receipt["exit"] = 0
        print(json.dumps(result), flush=True)
    except Exception as exc:
        (output / "driver.stdout.txt").write_text("")
        (output / "driver.stderr.txt").write_text(f"{type(exc).__name__}: {exc}\n")
        receipt["exit"] = 1
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
    receipt["end"] = datetime.now(timezone.utc).isoformat()
    receipt["timed_out"] = any(json.loads(p.read_text()).get("timed_out", False)
                               for p in output.rglob("*.receipt.json"))
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
        out.write("\n")
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
