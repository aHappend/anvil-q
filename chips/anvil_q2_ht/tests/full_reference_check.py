"""Cross-check the efficient full-model oracle against independent exact mathematics."""

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import (fp32_add, fp32_product_q16_bf16, fraction_q16,
                       ieee_round, ieee_value, array_result)
from retention import Experiment
from small_model import CELLS, fixture


def arithmetic(experiment, executable):
    rng = random.Random(101)
    inputs, expected = [], []
    counts = {}

    def emit(op, a, b=0):
        inputs.append(f"{op:x} {a & 0xffffffff:x} {b:x}\n")
        counts[op] = counts.get(op, 0) + 1
        try:
            if op in (0, 1, 2):
                eb, fb = ((5, 10), (8, 7), (8, 23))[op]
                result = fraction_q16(ieee_value(a, eb, fb)) & 0xffffffff
            elif op in (3, 4):
                eb, fb = (8, 7) if op == 3 else (5, 10)
                result = ieee_round(Fraction(a, 65536), eb, fb)
            elif op == 5:
                result = fp32_add(a, b)
            else:
                result = fp32_product_q16_bf16(a, b)
            expected.append(f"{result:x}")
        except (ValueError, OverflowError):
            expected.append("error")

    for word in range(65536):
        emit(0, word)
        emit(1, word)
        activation = rng.choice((0, 1, -1, -(1 << 31), (1 << 31) - 1,
                                 rng.randint(-(1 << 31), (1 << 31) - 1)))
        emit(6, activation, word)
    values = {0, 1, -1, -(1 << 31), (1 << 31) - 1}
    for power in range(31):
        for offset in range(-3, 4):
            for sign in (-1, 1):
                value = sign * ((1 << power) + offset)
                if -(1 << 31) <= value < 1 << 31:
                    values.add(value)
    values.update(rng.randint(-(1 << 31), (1 << 31) - 1) for _ in range(4096))
    for value in sorted(values):
        emit(3, value)
        emit(4, value)
    for _ in range(8192):
        a, b = rng.getrandbits(32), rng.getrandbits(32)
        emit(2, a)
        emit(5, a, b)
    for a, b in ((0x80000000, 0x80000000), (0, 0x80000000), (1, 1),
                 (0x3f800000, 0x33800000), (0x3f800001, 0x33800000),
                 (0x7f7fffff, 0x7f7fffff), (0x00800000, 0x807fffff)):
        emit(5, a, b)
    directory = experiment.directory
    (directory / "arithmetic.txt").write_text("".join(inputs))
    (directory / "arithmetic.expected").write_text("\n".join(expected) + "\n")
    output = experiment.output
    text = experiment.run([str(executable), "--arithmetic", str(output / "arithmetic.txt"),
                           str(output / "arithmetic.observed")], "arithmetic")
    if "REFERENCE_ARITHMETIC_CHECKED " not in text:
        raise RuntimeError("missing reference arithmetic completion marker")
    observed = (directory / "arithmetic.observed").read_text().splitlines()
    if len(observed) != len(expected):
        raise RuntimeError("reference arithmetic comparison count mismatch")
    for index, (actual, required) in enumerate(zip(observed, expected)):
        if actual != required:
            raise RuntimeError(f"reference arithmetic mismatch case={index} "
                               f"input={inputs[index].strip()} got={actual} expected={required}")
    return {"comparisons": len(expected), "operations": counts,
            "input_sha256": hashlib.sha256("".join(inputs).encode()).hexdigest()}


def system_cases(experiment, executable, cells, bias_stress=False, bias_boundary=False):
    records = []
    for cell in cells:
        g = CELLS[cell]
        for seed, mode, cache in ((11, 0, 0), (29, 1, 1), (101, 0, 2),
                                  (11, 1, 0), (29, 0, 1), (101, 1, 2)):
            if bias_boundary and mode != 1:
                continue
            memory, descriptors, expected = fixture(mode, cache, seed, cell, bias_stress,
                                                     bias_boundary=bias_boundary)
            name = f"{cell}-seed{seed}-mode{mode}-cache{cache}" + ("-bias-stress" if bias_stress else "")
            if bias_boundary:
                name += "-bias-boundary"
            path = experiment.directory / name
            path.mkdir()
            (path / "image.bin").write_bytes(memory)
            (path / "descriptors.bin").write_bytes(b"".join(struct.pack("<16I", *d) for d in descriptors))
            count = min(3, g["sequence"])
            (path / "tokens.txt").write_text("".join(
                f"{position % g['vocabulary']} {position} {int(position == 0)} {int(position == 2)}\n"
                for position in range(count)))
            relative = experiment.output / name
            args = [str(executable), str(relative / "image.bin"), str(relative / "descriptors.bin")]
            args += [str(g[key]) for key in ("hidden", "intermediate", "query_heads",
                     "kv_heads", "head_dim", "group", "layers", "vocabulary", "sequence", "cache_block")]
            args += [str(mode), str(cache), str(relative / "tokens.txt"), str(relative / "logits.bin")]
            text = experiment.run(args, name)
            data = (path / "logits.bin").read_bytes()
            required = struct.pack("<" + "i" * len(expected), *expected)
            if "FULL_REFERENCE_CHECKED " not in text or data != required:
                raise RuntimeError("full reference token/logit mismatch: " + name)
            records.append({"cell": cell, "seed": seed, "mode": mode, "cache": cache,
                            "bias_stress": bias_stress,
                            "bias_boundary": bias_boundary,
                            "tokens": count, "compared_logits": len(expected),
                            "image_sha256": hashlib.sha256(memory).hexdigest(),
                            "logits_sha256": hashlib.sha256(data).hexdigest()})
    return records


def projection_boundaries(experiment, executable):
    records = []
    for sign in (1, -1):
        path = experiment.directory / ("projection-positive" if sign > 0 else "projection-negative")
        path.mkdir()
        activations = [sign] + [0] * 127
        weights = [0x3e80] + [0] * 127
        bias = 0x3680 | (0x8000 if sign < 0 else 0)
        image = struct.pack("<128H", *weights) + bytes(4096 - 256) + struct.pack("<H", bias)
        descriptors = (
            struct.pack("<QQQQIIIIIIQ", 0, 4096, 0, 0, 1, 128, 4096, 0, 0, 0x102, 0) +
            struct.pack("<QQQQIIIIIIQ", 4096, 2, 0, 0, 1, 1, 2, 0, 0, 0x102, 0))
        (path / "image.bin").write_bytes(image)
        (path / "descriptors.bin").write_bytes(descriptors)
        (path / "activation.bin").write_bytes(struct.pack("<128i", *activations))
        _, reduced, fault = array_result(1, (1 << 128) - 1, activations,
                                         [0] * 128, [0] * 128, [0] * 128, weights)
        if fault:
            raise RuntimeError("nonfinite directed reference input")
        expected = fraction_q16(ieee_value(fp32_add(reduced, bias << 16), 8, 23))
        relative = path.relative_to(experiment.root)
        text = experiment.run([str(executable), "--projection", str(relative / "image.bin"),
                               str(relative / "descriptors.bin"), str(relative / "activation.bin"),
                               "0", "1", "1", "128", str(relative / "observed.bin")], path.name)
        data = (path / "observed.bin").read_bytes()
        if "REFERENCE_PROJECTION_CHECKED rows=1" not in text or data != struct.pack("<i", expected):
            raise RuntimeError("BF16 bias must enter FP32 without prior Q16 rounding: " + path.name)
        records.append({"sign": sign, "expected_q16": expected,
                        "observed_sha256": hashlib.sha256(data).hexdigest()})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cell", choices=(*CELLS, "all"), default="all")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    experiment = Experiment(root, args.output, sys.orig_argv, [
        "tests/full_model_reference.cpp", "tests/full_reference_check.py",
        "tests/reference.py", "tests/small_model.py", "tests/retention.py"])
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    try:
        experiment.run(["g++", "--version"], "compiler-version")
        executable = args.output / "full_model_reference"
        experiment.run(["g++", "-std=c++17", "-O2", "-Wall", "-Wextra",
                        "-ffp-contract=off", "-frounding-math", "-fno-fast-math",
                        str(args.output / "sources/tests/full_model_reference.cpp"),
                        "-o", str(executable)], "compile")
        experiment.receipt["arithmetic"] = arithmetic(experiment, executable)
        experiment.receipt["projection_boundaries"] = projection_boundaries(experiment, executable)
        experiment.receipt["systems"] = system_cases(
            experiment, executable, CELLS if args.cell == "all" else (args.cell,))
        experiment.receipt["bias_stress_systems"] = system_cases(
            experiment, executable, ("small", "nonpower"), bias_stress=True)
        experiment.receipt["bias_boundary_systems"] = system_cases(
            experiment, executable, ("small",), bias_boundary=True)
        experiment.receipt["scope"] = (
            "independent C++/exact-Python oracle comparison; not RTL or physical execution")
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, ArithmeticError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
