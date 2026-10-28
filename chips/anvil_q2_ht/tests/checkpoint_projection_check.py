"""Execute real full-input-width projection rows from all official layers/projections."""

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint_import import PROJECTIONS, Source
from reference import array_result, fp32_add, scale_q16
from retention import Experiment
from build_cache import compile_verilator


def fixtures(source, mode, directory, output):
    records = []
    cases = []
    permutation = (0, 4, 1, 5, 2, 6, 3, 7)
    zeros = [0] * 128
    for seed in (11, 29, 101):
        rng = random.Random(seed)
        for layer in range(28):
            for projection, suffix in enumerate(PROJECTIONS):
                rows = 256 if projection in (1, 2) else (8960 if projection in (4, 5) else 1536)
                cols = 8960 if projection == 6 else 1536
                prefix = f"model.layers.{layer}." + suffix
                selected_row = rng.randrange(rows)
                activations = [rng.randint(-(1 << 20), (1 << 20)) for _ in range(cols)]
                chunks = cols // 128
                image = bytearray(chunks * (1024 if mode == "awq" else 4096))
                if mode == "awq":
                    source_weights, _ = source.tensor(prefix + ".qweight", [cols, rows // 8], "I32")
                    source_zeros, _ = source.tensor(prefix + ".qzeros", [chunks, rows // 8], "I32")
                    source_scales, _ = source.tensor(prefix + ".scales", [chunks, rows], "F16")
                    raw_weights = [struct.unpack_from("<I", source.data,
                        source_weights + 4 * (col * (rows // 8) + selected_row // 8))[0]
                                   for col in range(cols)]
                    weights = [(word >> (4 * permutation[selected_row % 8])) & 15
                               for word in raw_weights]
                    group_zeros = [(struct.unpack_from("<I", source.data,
                        source_zeros + 4 * (group * (rows // 8) + selected_row // 8))[0] >>
                        (4 * permutation[selected_row % 8])) & 15 for group in range(chunks)]
                    group_scales = [struct.unpack_from("<H", source.data,
                        source_scales + 2 * (group * rows + selected_row))[0] for group in range(chunks)]
                    expected_sum = sum(activation * (weight - group_zeros[col // 128]) *
                        scale_q16(group_scales[col // 128])
                        for col, (activation, weight) in enumerate(zip(activations, weights)))
                    expected_fp32 = 0
                    for col, weight in enumerate(weights):
                        element = (col // 128) * 2048 + col % 128
                        image[element // 2] |= weight << (4 * (element & 1))
                    zero_base = len(image)
                    zero_record = bytearray((chunks + 1) // 2)
                    for group, value in enumerate(group_zeros):
                        zero_record[group // 2] |= value << (4 * (group % 2))
                    image.extend(zero_record)
                    image.extend(bytes((-len(image)) % 64))
                    scale_base = len(image)
                    image.extend(struct.pack("<" + "H" * chunks, *group_scales))
                    descriptor = struct.pack("<QQQQIIIIIIQ", 0, chunks * 1024,
                        zero_base, scale_base, 1, cols, 1024, (chunks + 1) // 2, chunks * 2, 0x100, 0)
                else:
                    source_weights, _ = source.tensor(prefix + ".weight", [rows, cols], "BF16")
                    weights = list(struct.unpack_from("<" + "H" * cols, source.data,
                                                      source_weights + 2 * selected_row * cols))
                    expected_sum = expected_fp32 = 0
                    for chunk in range(chunks):
                        begin = chunk * 128
                        _, reduced, error = array_result(1, (1 << 128) - 1,
                            activations[begin:begin + 128], zeros, zeros, zeros,
                            weights[begin:begin + 128])
                        if error:
                            raise ArithmeticError("official BF16 row produced nonfinite oracle result")
                        expected_fp32 = fp32_add(expected_fp32, reduced)
                        struct.pack_into("<128H", image, chunk * 4096,
                                         *weights[begin:begin + 128])
                    descriptor = struct.pack("<QQQQIIIIIIQ", 0, chunks * 4096, 0, 0,
                                             1, cols, 4096, 0, 0, 0x102, 0)
                image.extend(bytes((-len(image)) % 64))
                stem = f"seed{seed}-layer{layer}-projection{projection}"
                image_name = stem + ".image.hex"
                activation_name = stem + ".activation.hex"
                (directory / image_name).write_text("".join(f"{byte:02x}\n" for byte in image))
                activation_data = "".join(f"{value & 0xffffffff:08x}\n" for value in activations)
                (directory / activation_name).write_text(activation_data)
                cases.append(f"{int(mode == 'bf16')} {len(image)} {cols} "
                             f"{output / image_name} {output / activation_name} "
                             f"{int.from_bytes(descriptor, 'little'):0128x} "
                             f"{expected_sum & ((1 << 128) - 1):032x} {expected_fp32:08x}\n")
                records.append({"seed": seed, "layer": layer, "projection": projection,
                                "source_row": selected_row, "input_columns": cols, "output_rows": 1,
                                "image_sha256": hashlib.sha256(image).hexdigest(),
                                "activations_sha256": hashlib.sha256(activation_data.encode()).hexdigest(),
                                "expected_sum": expected_sum, "expected_fp32": expected_fp32})
    if len(records) != 588:
        raise RuntimeError("missing official row/seed coverage")
    (directory / "cases.txt").write_text("".join(cases))
    (directory / "fixtures.json").write_text(json.dumps(records, indent=2) + "\n")
    return {"cases": len(records), "seeds": [11, 29, 101], "layers": 28, "projections": 7,
            "rows_per_projection_per_seed": 1,
            "cases_sha256": hashlib.sha256((directory / "cases.txt").read_bytes()).hexdigest(),
            "fixtures_sha256": hashlib.sha256((directory / "fixtures.json").read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mode", choices=("awq", "bf16"), required=True)
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="verilator")
    parser.add_argument("--repair-of")
    parser.add_argument("--build-cache", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    rtl = sorted(str(path.relative_to(root)) for path in (root / "rtl").glob("*.sv"))
    names = rtl + ["tests/checkpoint_projection_tb.sv", "tests/checkpoint_projection_check.py",
                   "tests/checkpoint_import.py", "tests/rope_reference.py", "tests/reference.py",
                   "tests/retention.py", "tests/build_cache.py", "data/model/official_inputs.json"]
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    source = None
    try:
        tools = ([("iverilog", "-V"), ("vvp", "-V")] if args.simulator == "iverilog"
                 else [("verilator", "--version"), ("g++", "--version")])
        for tool, flag in [("python3", "--version")] + tools:
            experiment.run([tool, flag], tool + "-version")
        sources = [str(args.output / "sources" / name) for name in rtl +
                   ["tests/checkpoint_projection_tb.sv"]]
        if args.simulator == "iverilog":
            binary = str(args.output / "projection.vvp")
            experiment.run(["iverilog", "-g2012", "-Wall", "-s", "checkpoint_projection_tb",
                            "-o", binary] + sources, "compile")
            argv = ["vvp", binary]
        else:
            executable = compile_verilator(experiment, ["verilator", "--binary", "--timing", "-Wno-fatal",
                "--top-module", "checkpoint_projection_tb", "--Mdir", str(args.output / "obj"),
                "-MAKEFLAGS", "VK_PCH_I_FAST= VK_PCH_I_SLOW=",
                "-o", "projection_sim"] + sources, cache=args.build_cache)
            argv = [executable]
        source = Source(root, args.mode)
        experiment.receipt["official_source"] = {key: source.info[key] for key in
                                                 ("repository", "revision", "license_metadata")}
        experiment.receipt["fixtures"] = fixtures(source, args.mode, experiment.directory, args.output)
        text = experiment.run(argv + ["+cases=" + str(args.output / "cases.txt")], "simulate")
        if "CHECKPOINT_PROJECTIONS_CHECKED cases=588 rows=588 completions=588 " not in text:
            raise RuntimeError("missing executed official projection comparisons")
        experiment.receipt["comparison_summary"] = text.strip()
        experiment.receipt["scope"] = "full-input-width unbiased row samples, not full-model token execution"
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, ArithmeticError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1
    finally:
        if source is not None:
            source.close()


if __name__ == "__main__":
    raise SystemExit(main())
