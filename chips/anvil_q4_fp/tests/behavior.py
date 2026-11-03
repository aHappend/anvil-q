"""Compiled complete native inference with a public transaction oracle."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import ROOT, execute, new_run, relative, source_hashes
from native_model import Fixture, descriptor


def run(preparation=False, *, banks=16, tile_rows=16, tile_k=128, queue=3,
        words=None, seed=17, tokens=2):
    directory = new_run("native-inference", preparation)
    if words is None:
        words = descriptor(banks=banks, dimension=2, ratio=1, kv_heads=1,
                           intermediate=19, vocabulary=19, context=5)
    fixture = Fixture(words, seed, tokens).export(directory)
    (directory / "sources.json").write_text(json.dumps(source_hashes(), indent=2) + "\n")
    obj = directory / "compile-obj"
    try:
        execute(directory / "verilator-compile", [
            "verilator", "--cc", "--exe", "--build", "-Wno-fatal", "-j", "2",
            "--top-module", "anvil_q4_fp_top", "--Mdir", relative(obj),
            f"-GBANKS={banks}", f"-GQUEUE_DEPTH={queue}",
            f"-GTILE_ROWS={tile_rows}", f"-GTILE_K={tile_k}",
            "-CFLAGS", f"-std=c++17 -DBANKS={banks}",
            *[relative(path) for path in sorted((ROOT / "rtl").glob("*.sv"))],
            # Generated makefiles run from --Mdir, so resolve the one C++ input
            # relative to that directory, without embedding a host path.
            os.path.relpath(ROOT / "tests/native_sim.cpp", obj)],
            timeout=1800)
        execute(directory / "verilator-native",
                [relative(obj / "Vanvil_q4_fp_top"), relative(fixture),
                 relative(directory / "observed.json")], timeout=1800)
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    print(f"Native inference receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--large", action="store_true")
    parser.add_argument("--fp16", action="store_true")
    args = parser.parse_args()
    run(args.preparation, words=descriptor(
        dimension=8, ratio=4, kv_heads=2, layers=2,
        intermediate=19, vocabulary=19, context=5,
        element=int(args.fp16), cache=int(args.fp16)) if args.large else None,
        tokens=4 if args.large else 2)
