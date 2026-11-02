"""Public-pin K=4 tile numerical/cycle reference comparisons."""

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipts import execute, new_run, relative, cleanup_build
from reference import pack_rows, tile_sum, f32


SOURCES = ["rtl/anvil_q3_ht2_00_fp_pkg.sv", "rtl/anvil_q3_ht2_fp32_add.sv",
           "rtl/anvil_q3_ht2_fp32_mul.sv", "rtl/anvil_q3_ht2_weight_decode.sv",
           "rtl/anvil_q3_ht2_mac_lane.sv", "rtl/anvil_q3_ht2_tile_batch_mac.sv",
           "tests/tile_tb.sv"]


def generate(path, seed, lanes, compact):
    rng = random.Random(seed)
    scales_pool = [0, 0x8000, 1, 0x3ff, 0x400, 0x1400, 0x3c00, 0x3c01, 0x7bff]
    acts_pool = [0, 0x8000, 1, 0x8001, 0x3ff, 0x83ff, 0x400,
                 0x8400, 0x1400, 0x9400, 0x3c00, 0xbc00, 0x7bff, 0xfbff]
    cases = []
    input_count = 0

    def case(columns, mask, row_mask, repeated=False):
        nonlocal input_count
        beats = []
        for column in range(columns):
            qs = [(row + column) & 15 for row in range(128)]
            zs = [((row >> 4) + column) & 15 for row in range(128)]
            scales = sum((0x1400 if repeated else rng.choice(scales_pool)) << (16 * row)
                         for row in range(128))
            acts = sum((0x3c00 if repeated else rng.choice(acts_pool)) << (16 * token)
                       for token in range(4))
            keep = mask if column % 5 else mask & (1 << ((column // 5) % 4))
            if not keep:
                keep = mask
            if repeated:
                qs = [row & 15 for row in range(128)]
                zs = [(row >> 4) & 15 for row in range(128)]
                keep = mask
            beats.append((pack_rows(qs), pack_rows(zs), scales, acts, keep))
        if repeated:
            # Every partial addition is exact: |delta| * 11008 < 2^24.
            # Thus rational summation proves the specified striped result without
            # copying the DUT's cycle-state implementation.
            from fractions import Fraction
            expected = sum(f32(Fraction(((row & 15) - ((row >> 4) & 15)) * columns, 1024))
                           << (32 * (token * 128 + row))
                           for token in range(4) for row in range(lanes)
                           if mask & (1 << token) and row_mask & (1 << row))
        else:
            expected = tile_sum(beats, mask, row_mask)
        records = [f"{columns} {mask:x} {row_mask:x} 0 {columns}",
                   *(f"{(expected >> (token * 4096)) & ((1 << 4096) - 1):x}"
                     for token in range(4))]
        for column, beat in enumerate(beats):
            records.append(f"{column:x} " + " ".join(f"{field:x}" for field in beat) +
                           f" {int(column == columns - 1):x}")
        cases.append("\n".join(records))
        input_count += columns

    for count in (0, 1, 7, 8, 9, 64):
        case(count, 15, (1 << lanes) - 1)
    for mask in range(1, 16):
        case(9, mask, (1 << lanes) - 1)
    case(7, 15, 1)
    case(8, 15, (1 << (lanes - 1)) - 1)
    if not compact:
        case(1024, 15, (1 << lanes) - 1)
        case(11008, 15, (1 << lanes) - 1, repeated=True)
    path.write_text(f"{len(cases)}\n" + "\n".join(cases) + "\n")
    return {"cases": len(cases), "inputs": input_count, "outputs": len(cases)}


def run_tile(run, simulator, seed, compact):
    lanes = 8 if simulator == "iverilog" else 128
    path = run / f"tile-seed{seed}.txt"
    totals = generate(path, seed, lanes, compact)
    if simulator == "iverilog":
        executable = run / "tile.vvp"
        execute(run, "tile-compile", ["iverilog", "-g2012", "-Wall", "-s", "tile_tb",
                "-o", relative(executable), *SOURCES], ["iverilog", "-V"])
        argv = ["vvp", relative(executable), f"+vectors={relative(path)}"]
        version = ["vvp", "-V"]
    else:
        obj = run / "tile-obj"
        execute(run, "tile-compile", ["verilator", "--binary", "--timing", "-Wno-fatal",
                "--top-module", "tile_tb", "-GWEIGHT_LANES=128", "-GHIDDEN_SIZE=2048",
                "-GNUM_KV_HEADS=2", "-GHEAD_DIM=128", "--Mdir", relative(obj),
                "-j", "2", "--output-split", "20000", "--output-split-cfuncs", "2000",
                "-CFLAGS", "-O0", *SOURCES], ["verilator", "--version"])
        argv = [relative(obj / "Vtile_tb"), f"+vectors={relative(path)}"]
        version = ["verilator", "--version"]
    try:
        output = execute(run, "tile-simulate", argv, version)
    finally:
        if simulator == "verilator":
            cleanup_build(obj)
    records = [json.loads(line.removeprefix("RESULT "))
               for line in (output / "stdout.txt").read_text().splitlines()
               if line.startswith("RESULT ")]
    if len(records) != 1:
        raise AssertionError("missing or malformed tile result")
    for field, expected in totals.items():
        if records[0][field] != expected:
            raise AssertionError(f"tile {field}: {records[0][field]} != {expected}")
    if records[0]["max_consecutive_beats"] < 64:
        raise AssertionError("no observed 64-beat initiation-interval-one sequence")
    summary = {"seed": seed, "simulator": simulator, "observed": records[0],
               "vector_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
               "receipt": relative(output / "receipt.json")}
    (run / "tile-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulator", choices=["iverilog", "verilator"], default="iverilog")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    compact = args.compact or args.simulator == "iverilog"
    run = new_run("tile", preparation=True, repair_of=args.repair_of)
    print(f"tile evidence: {relative(run)}", flush=True)
    try:
        print(json.dumps(run_tile(run, args.simulator, args.seed, compact), sort_keys=True))
    except (RuntimeError, AssertionError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
