"""Independent packed-image sparse extraction through the actual public DDR arbiter."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipts import execute, new_run, relative
from reference import packed_image, sparse_expected


def packed_activations(values):
    return sum(value << (16 * token) for token, value in enumerate(values))


def generate(path, seed, compact):
    cases = []
    large_columns = 17 if compact else 11008
    # Geometry and predicate cases are paired, rather than Cartesian expanded.
    shapes = [(8, 0, 5), (8, 7, 5), (64, 0, 5), (64, 1, 5),
              (136, 8, 5), (136, 1, 5), (136, 135, 5),
              (256, 0, 10), (256, 128, 10), (128, 0, large_columns)]
    expected_totals = {"cases": 0, "operands": 0, "physical_bytes": 0,
                       "scanned": 0, "skipped": 0}
    for index, (output, row, columns) in enumerate(shapes):
        for predicate in range(4):
            mask = (15, 1, 10, 5)[predicate]
            sparse = predicate != 0
            threshold = 0 if predicate == 2 else 0x1400
            projection = 5 if predicate == 3 else 6
            activations = []
            for column in range(columns):
                if predicate == 1:
                    values = [0x1400, 0x9400, 0, 0x8000]
                elif predicate == 2:
                    values = [0, 0x8000, 1 if column % 3 == 1 else 0,
                              0xbc00 if column % 3 == 0 else 0]
                else:
                    values = [0x3c00, 0xbc00, 0x1400, 0x9400]
                activations.append(packed_activations(values))
            image, logical = packed_image(output, columns, seed + index)
            requests, operands, rows = sparse_expected(
                0x1000, output, row, activations, mask, sparse, threshold,
                projection, image, logical)
            fields = (f"1000 {output} {row} {columns} {mask:x} {int(sparse):x} "
                      f"{threshold:x} {projection:x} {len(requests)} {len(operands)} "
                      f"{len(image) // 64} {int(index % 2 == 0)} {rows:x}")
            records = [fields, *(f"{act:x}" for act in activations),
                       *(f"{int.from_bytes(image[offset:offset + 64], 'little'):x}"
                         for offset in range(0, len(image), 64)),
                       *(f"{address:x}" for address, _ in requests),
                       *(" ".join(f"{field:x}" for field in entry[:5]) +
                         f" {entry[5]}" for entry in operands)]
            cases.append("\n".join(records))
            expected_totals["cases"] += 1
            expected_totals["operands"] += len(operands)
            expected_totals["physical_bytes"] += 64 * len(requests)
            expected_totals["scanned"] += columns
            expected_totals["skipped"] += columns - len(operands)
    path.write_text(f"{len(cases)}\n" + "\n".join(cases) + "\n")
    return expected_totals


def run_sparse(run, simulator, seed, compact):
    path = run / f"sparse-seed{seed}.txt"
    totals = generate(path, seed, compact)
    sources = ["rtl/anvil_q3_ht2_sparse_dma.sv", "rtl/anvil_q3_ht2_ddr_arbiter.sv",
               "tests/sparse_ddr_tb.sv"]
    if simulator == "iverilog":
        executable = run / "sparse.vvp"
        execute(run, "sparse-compile",
                ["iverilog", "-g2012", "-Wall", "-s", "sparse_ddr_tb", "-o",
                 relative(executable), *sources], ["iverilog", "-V"])
        argv = ["vvp", relative(executable), f"+vectors={relative(path)}"]
        version = ["vvp", "-V"]
    else:
        obj = run / "sparse-obj"
        execute(run, "sparse-compile", ["verilator", "--binary", "--timing", "-Wno-fatal",
                "--top-module", "sparse_ddr_tb", "-GMAX_COLUMNS=11008",
                "--Mdir", relative(obj), "-j", "2", *sources], ["verilator", "--version"])
        argv = [relative(obj / "Vsparse_ddr_tb"), f"+vectors={relative(path)}"]
        version = ["verilator", "--version"]
    output = execute(run, "sparse-simulate", argv, version)
    records = [json.loads(line.removeprefix("RESULT "))
               for line in (output / "stdout.txt").read_text().splitlines()
               if line.startswith("RESULT ")]
    if len(records) != 1:
        raise AssertionError("missing or malformed sparse result")
    observed = records[0]
    for field, expected in totals.items():
        if observed[field] != expected:
            raise AssertionError(f"sparse accounting {field}: {observed[field]} != {expected}")
    for field in ("crossing_operands", "singleton_operands", "immediate_returns",
                  "blocked_requests", "blocked_operands", "descriptor_stalls"):
        if observed[field] <= 0:
            raise AssertionError(f"missing observed sparse coverage: {field}")
    summary = {"seed": seed, "simulator": simulator, "observed": observed,
               "vector_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
               "receipt": relative(output / "receipt.json")}
    (run / "sparse-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulator", choices=["iverilog", "verilator"], default="iverilog")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    # Interpreted execution is always the compact smoke tier.
    compact = args.compact or args.simulator == "iverilog"
    run = new_run("sparse-ddr", preparation=True, repair_of=args.repair_of)
    print(f"sparse evidence: {relative(run)}", flush=True)
    try:
        print(json.dumps(run_sparse(run, args.simulator, args.seed, compact), sort_keys=True))
    except (RuntimeError, AssertionError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
