"""Independent masked, tiled tensor arithmetic and public edge-table checks."""

import argparse
from fractions import Fraction
import json
import random
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import execute, new_run, relative, source_hashes
from ieee import convert, operation, pack


def vectors(path, lanes=16, tile_k=128):
    rng = random.Random(89)
    records = []
    with path.open("w") as stream:
        for fmt_id, fmt in enumerate(("bf16", "fp16")):
            for length in sorted(set((1, min(3, tile_k), tile_k))):
                for mask in sorted(set((1, (1 << lanes)-1, ((1 << lanes)-1) & 0x5555))):
                    if not mask:
                        continue
                    for special in (False, True):
                        accumulator = [pack(Fraction(lane-7, 8))[0] for lane in range(lanes)]
                        activations = [rng.getrandbits(16) if special else
                                       pack(Fraction(rng.randrange(-13, 14), 16), fmt)[0]
                                       for _ in range(length)]
                        weights = [[rng.getrandbits(16) if special else
                                    pack(Fraction(rng.randrange(-19, 20), 32), fmt)[0]
                                    for _ in range(lanes)] for _ in range(length)]
                        result, flags = list(accumulator), 0
                        for k in range(length):
                            x, xf = convert(activations[k], fmt, "fp32")
                            flags |= xf
                            for lane in range(lanes):
                                if mask & (1 << lane):
                                    weight, wf = convert(weights[k][lane], fmt, "fp32")
                                    product, pf = operation(2, x, weight)
                                    result[lane], af = operation(0, result[lane], product)
                                    flags |= wf | pf | af
                        stream.write(f"{length} {mask:x} {fmt_id}\n")
                        for values in (accumulator, activations, sum(weights, []), result, [flags]):
                            stream.write(" ".join(f"{word:x}" for word in values) + "\n")
                        records.append({"length": length, "mask": mask,
                                        "format": fmt, "special": special})
    return records


def run(preparation=False, lanes=16, tile_k=128, repair_of=None):
    directory = new_run("tensor", preparation)
    fixture = directory / "tensor-vectors.txt"
    records = vectors(fixture, lanes, tile_k)
    (directory / "reference.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "lanes": lanes, "tile_k": tile_k,
        "cases": records}, indent=2) + "\n")
    obj = directory / "compile-obj"
    try:
        execute(directory / "verilator-compile", [
            "verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
            "--top-module", "tensor_tb", "--Mdir", relative(obj),
            f"-GLANES={lanes}", f"-GTILE_K={tile_k}",
            "rtl/anvil_q4_00_fp_pkg.sv", "rtl/anvil_q4_fp32.sv",
            "rtl/anvil_q4_fp_tensor_array.sv", "tests/tensor_tb.sv"])
        execute(directory / "verilator-tensor", [
            relative(obj / "Vtensor_tb"), f"+vectors={relative(fixture)}"],
            repair_of=repair_of)
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    print(f"Tensor receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--lanes", type=int, default=16)
    parser.add_argument("--tile-k", type=int, default=128)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run(args.preparation, args.lanes, args.tile_k, args.repair_of)
