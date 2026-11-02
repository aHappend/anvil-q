"""Executable independent leaf arithmetic experiment (not complete L1 closure)."""

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipts import ROOT, execute, new_run, relative
from reference import fp_operation, q16_to_half, single_to_q16, weight


ARITH_SOURCES = [
    "rtl/anvil_q3_ht2_00_fp_pkg.sv", "rtl/anvil_q3_ht2_fp32_add.sv",
    "rtl/anvil_q3_ht2_fp32_mul.sv", "rtl/anvil_q3_ht2_weight_decode.sv",
    "rtl/anvil_q3_ht2_q16_to_f16.sv", "rtl/anvil_q3_ht2_f32_to_q16.sv",
]


def vectors(path, seed, compact=False):
    rng = random.Random(seed)
    records = []

    def record(a, b, q=1, z=0, scale=0x3c00, control=1, offered=1):
        add, ae = fp_operation(a, b, False)
        mul, me = fp_operation(a, b, True)
        w, we = weight(q, z, scale)
        qh = q16_to_half(a)
        fq, fe = single_to_q16(a)
        fields = (control, offered, a, b, q, z, scale, add, mul, w,
                  qh, fq, ae | (me << 1) | (we << 2) | (fe << 4))
        records.append(" ".join(f"{field:x}" for field in fields))

    directed = [
        (0x3f800000, 0x3f800000), (0x3f800000, 0xbf800000),
        (0x3f800000, 0x33800000), (0x3f800001, 0x33800000),
        (0x00000001, 0x3f800000), (0x007fffff, 0x3f800000),
        (0x00800000, 0x3f000000), (0x80000001, 0x40000000),
        (0x7f7fffff, 0x40000000), (0x7f800000, 0),
        (0x7fc12345, 0x3f800000), (0, 0x80000000),
    ]
    for a, b in directed:
        record(a, b)
    half_scales = [0, 0x8000, 1, 0x3ff, 0x400, 0x1400, 0x3c00,
                   0x3c01, 0x7bff, 0xbc00, 0x7c00, 0x7e00]
    for q in range(16):
        for z in range(16):
            scale = half_scales[(q * 16 + z) % len(half_scales)]
            record(rng.getrandbits(32), rng.getrandbits(32), q, z, scale)
    for stage in range(6):
        record(0, 0, control=2, offered=0)
        for _ in range(stage + 1):
            record(0x3f800000, 0x40000000)
        record(0, 0, control=2, offered=0)
        for _ in range(7):
            record(0, 0, offered=0)
    for _ in range(32 if compact else 2048):
        record(rng.getrandbits(32), rng.getrandbits(32),
               rng.randrange(16), rng.randrange(16), rng.randrange(65536),
               control=rng.choice((0, 1, 1, 1)), offered=rng.randrange(4) != 0)
    for _ in range(8):
        record(0, 0, offered=0)
    path.write_text("\n".join(records) + "\n")
    return len(records)


def run_arithmetic(run, simulator="iverilog", seed=17, compact=False):
    vector_path = run / f"arithmetic-seed{seed}.txt"
    count = vectors(vector_path, seed, compact)
    if simulator == "iverilog":
        executable = run / "arithmetic.vvp"
        execute(run, "arithmetic-compile",
                ["iverilog", "-g2012", "-Wall", "-s", "arithmetic_tb",
                 "-o", relative(executable), *ARITH_SOURCES, "tests/arithmetic_tb.sv"],
                ["iverilog", "-V"])
        argv = ["vvp", relative(executable), f"+vectors={relative(vector_path)}"]
        version = ["vvp", "-V"]
    else:
        obj = run / "arithmetic-obj"
        execute(run, "arithmetic-compile",
                ["verilator", "--binary", "--timing", "-Wno-fatal", "--top-module",
                 "arithmetic_tb", "--Mdir", relative(obj), "-j", "2",
                 *ARITH_SOURCES, "tests/arithmetic_tb.sv"], ["verilator", "--version"])
        argv = [relative(obj / "Varithmetic_tb"), f"+vectors={relative(vector_path)}"]
        version = ["verilator", "--version"]
    result_path = execute(run, "arithmetic-simulate", argv, version)
    lines = (result_path / "stdout.txt").read_text().splitlines()
    outputs = [json.loads(line.removeprefix("RESULT ")) for line in lines
               if line.startswith("RESULT ")]
    if len(outputs) != 1 or outputs[0]["cycles"] != count:
        raise AssertionError("missing or malformed complete arithmetic result")
    for field in ("inputs", "comparisons", "stall_edges", "flush_edges"):
        if not isinstance(outputs[0][field], int) or outputs[0][field] <= 0:
            raise AssertionError(f"missing observed arithmetic coverage: {field}")
    summary = {"seed": seed, "simulator": simulator, "vector_count": count,
               "vector_sha256": hashlib.sha256(vector_path.read_bytes()).hexdigest(),
               "observed": outputs[0], "receipt": relative(result_path / "receipt.json")}
    (run / "arithmetic-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulator", choices=["iverilog", "verilator"], default="iverilog")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    run = new_run("arithmetic", preparation=True)
    print(f"arithmetic evidence: {relative(run)}", flush=True)
    try:
        result = run_arithmetic(run, args.simulator, args.seed, args.compact)
    except (RuntimeError, AssertionError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
