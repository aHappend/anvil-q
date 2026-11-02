"""Verify exact synthesis frontend normalization with independent cache integers."""

import argparse
import hashlib
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment, ROOT
from legacy_reference import cache_block
from synthesis_probe import lower_codec_writes


def pack(words, width=32):
    return sum((word & ((1 << width)-1)) << (width*index)
               for index, word in enumerate(words))


def vectors():
    rng = random.Random(170043)
    for profile in (2, 3):
        for fmt in (0, 1, 2, 3):
            if profile == 2 and fmt > 1:
                continue
            mode = min(fmt, 2)
            for length in ((1,) if not fmt else (1, 2, 7, 32, 64, 255, 256)):
                for pattern in range(3):
                    values = ([509, -509]*((length+1)//2) if pattern == 0 else
                              [29, -29]*((length+1)//2) if pattern == 1 else
                              [rng.randrange(-(1 << 31), 1 << 31) for _ in range(length)])
                    values = values[:length]
                    block = length if length in (1, 256) else min(256, length+1)
                    if not fmt:
                        metadata, codes, decoded = 0, values, values
                        width = 32
                    else:
                        metadata, codes, decoded = cache_block(values, fmt)
                        width = 8 if fmt == 1 else 4
                    for decoding in (False, True):
                        yield (profile, mode, block, fmt == 3, decoding, length,
                               metadata if decoding else 0,
                               0 if decoding else pack(values),
                               pack(codes, width) if decoding else 0, 0,
                               pack(decoded) if decoding else 0,
                               0 if decoding else pack(codes, width),
                               metadata)
    for mode, metadata, payload in ((1, 0, 128), (2, 0, 8),
                                     (1, 256, 1), (2, 255, 0),
                                     (0, 1, 0), (1, 0, 1 << 32)):
        yield 3, mode, 1, 0, 1, 1, metadata, 0, payload, 1, 0, 0, 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--repair-of", action="append", default=[])
    parser.add_argument("--simulator", choices=("verilator", "iverilog"), default="verilator")
    args = parser.parse_args()
    experiment = Experiment("codec-equivalence", args.preparation, args.repair_of)
    error = None
    try:
        original = (ROOT/"rtl/anvil_q3_cache_codec.sv").read_text()
        frontend = experiment.directory/"frontend.sv"
        frontend.write_text(lower_codec_writes(original).replace(
            "module anvil_q3_cache_codec ", "module frontend_codec ", 1))
        experiment.receipt["frontend_sha256"] = hashlib.sha256(frontend.read_bytes()).hexdigest()
        fixture = experiment.directory/"vectors.txt"
        count = 0
        with fixture.open("w") as stream:
            for vector in vectors():
                stream.write(" ".join(str(int(x)) for x in vector[:6]) + " " +
                             " ".join(f"{x:x}" for x in vector[6:9]) +
                             f" {vector[9]} " +
                             " ".join(f"{x:x}" for x in vector[10:]) + "\n")
                count += 1
        experiment.receipt["fixture_sha256"] = hashlib.sha256(fixture.read_bytes()).hexdigest()
        objects = experiment.directory/"compile-obj"
        sources = ["rtl/anvil_q3_cache_codec.sv", experiment.rel(frontend),
                   "tests/codec_equivalence_tb.sv"]
        if args.simulator == "verilator":
            experiment.receipt["tool_version"] = experiment.run(["verilator", "--version"], "version")
            experiment.run([
                "verilator", "--binary", "--timing", "-Wno-fatal",
                "--top-module", "codec_equivalence_tb", "--Mdir", experiment.rel(objects),
                "-o", "codec-sim", *sources], "compile")
            command = [experiment.rel(objects/"codec-sim")]
        else:
            experiment.receipt["tool_version"] = experiment.run(["iverilog", "-V"], "version")
            binary = experiment.directory/"codec.vvp"
            experiment.run(["iverilog", "-g2012", "-Wall", "-s", "codec_equivalence_tb",
                            "-o", experiment.rel(binary), *sources], "compile")
            command = ["vvp", experiment.rel(binary)]
        output = experiment.run([*command, "+VECTORS="+experiment.rel(fixture)], "simulation")
        if f"SUMMARY codec cases={count} integer_comparisons={count}" not in output:
            raise AssertionError("missing independent codec comparison summary")
        experiment.receipt["comparisons"] = count
        experiment.prune_objects(objects)
    except (RuntimeError, ValueError, AssertionError, KeyError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
