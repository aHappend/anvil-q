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


def build(directory, obj, banks, tile_rows, tile_k, queue):
    execute(directory / "verilator-compile", [
        "verilator", "--cc", "--exe", "--build", "-Wno-fatal", "-j", "2",
        "--top-module", "anvil_q4_fp_top", "--Mdir", relative(obj),
        f"-GBANKS={banks}", f"-GQUEUE_DEPTH={queue}",
        f"-GTILE_ROWS={tile_rows}", f"-GTILE_K={tile_k}",
        "-CFLAGS", f"-std=c++17 -DBANKS={banks} -DCOHORT_MONITOR",
        "-MAKEFLAGS", "OPT_FAST=-O3",
        *[relative(path) for path in sorted((ROOT / "rtl").glob("*.sv"))],
        "tests/arithmetic_observer.sv",
        os.path.relpath(ROOT / "tests/native_sim.cpp", obj)], timeout=1800)
    return obj / "Vanvil_q4_fp_top"


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
        binary = build(directory, obj, banks, tile_rows, tile_k, queue)
        execute(directory / "verilator-native",
                [relative(binary), relative(fixture),
                 relative(directory / "observed.json")], timeout=1800,
                extra_inputs=[directory / "checkpoint-images/manifest.json"])
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    print(f"Native inference receipts: {relative(directory)}", flush=True)
    return directory


def run_matrix(preparation=False):
    directory = new_run("native-matrix", preparation)
    obj = directory / "compile-obj"
    records = []
    try:
        binary = build(directory, obj, 1, 3, 3, 3)
        for element in (0, 1):
            for cache in (0, 1, 2):
                for ratio in range(1, 9):
                    label = f"element-{element}-cache-{cache}-ratio-{ratio}"
                    case = directory / "checkpoint-images" / label
                    case.mkdir(parents=True)
                    words = descriptor(banks=1, element=element, cache=cache,
                                       ratio=ratio, dimension=2, intermediate=5,
                                       vocabulary=5, context=3)
                    image = Fixture(words, tokens=2).export(case)
                    observed = case / "observed.json"
                    execute(directory / f"simulate-{label}", [
                        relative(binary), relative(image), relative(observed)],
                        timeout=300, extra_inputs=[case / "checkpoint-images/manifest.json"])
                    records.append({
                        "element_format": element, "cache_format": cache,
                        "gqa_ratio": ratio, "tokens": 2,
                        "receipt": relative(directory / f"simulate-{label}/receipt.json"),
                        "observed": json.loads(observed.read_text()),
                    })
                    print(f"Native matrix: {len(records)}/48 {label}", flush=True)
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    (directory / "observed.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "synthetic": True,
        "geometry": {"banks": 1, "tile_rows": 3, "tile_k": 3, "queue_depth": 3},
        "cases": records}, indent=2) + "\n")
    print(f"Native matrix receipts: {relative(directory)}", flush=True)
    return directory


def run_geometries(preparation=False):
    directory = new_run("native-geometries", preparation)
    records = []
    geometries = (
        ((1, 1, 1, 1), [(17, 0, 0, 2, 1, 1, 1, 1)]),
        ((2, 16, 3, 3), [(89, 1, 1, 6, 1, 5, 5, 3)]),
        ((4, 3, 128, 3), [(2026, 0, 2, 2, 2, 5, 5, 2)]),
        ((8, 1, 1, 16), [(17, 1, 2, 2, 8, 17, 17, 2)]),
        ((16, 3, 128, 16), [
            (seed, element, element, 2, 8, 17, 17, 2)
            for seed in (17, 89, 2026) for element in (0, 1)] +
         [(17, 0, 0, 8, 4, 19, 19, 4)]),
    )
    for geometry, cases in geometries:
        banks, queue, tile_k, tile_rows = geometry
        obj = directory / f"banks-{banks}-compile-obj"
        try:
            binary = build(directory / f"banks-{banks}", obj, banks, tile_rows, tile_k, queue)
            for index, (seed, element, cache, dimension, ratio, inter, vocab, tokens) in enumerate(cases):
                large = dimension==8
                words = descriptor(
                    banks=banks, element=element, cache=cache, dimension=dimension,
                    ratio=ratio, kv_heads=2 if large else 1, layers=2 if large else 1,
                    intermediate=inter, vocabulary=vocab, context=max(tokens, 1),
                    page_tokens=1 if tokens==1 else 2, bias=int(vocab!=1))
                case = directory / "checkpoint-images" / f"banks-{banks}-case-{index}"
                case.mkdir(parents=True)
                image = Fixture(words, seed, tokens).export(case)
                observed = case / "observed.json"
                execute(directory / f"banks-{banks}-case-{index}", [
                    relative(binary), relative(image), relative(observed)],
                    timeout=1800, extra_inputs=[case / "checkpoint-images/manifest.json"])
                records.append({"geometry": geometry, "descriptor": words,
                                "seed": seed, "tokens": tokens, "synthetic": True,
                                "observed": json.loads(observed.read_text()),
                                "receipt": relative(directory / f"banks-{banks}-case-{index}/receipt.json")})
                print(f"Native geometry compared: banks={banks} seed={seed} format={element}",
                      flush=True)
        finally:
            if obj.exists():
                shutil.rmtree(obj)
    (directory / "observed.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "cases": records}, indent=2) + "\n")
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--large", action="store_true")
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--geometries", action="store_true")
    args = parser.parse_args()
    if args.geometries:
        run_geometries(args.preparation)
    elif args.matrix:
        run_matrix(args.preparation)
    else:
        run(args.preparation, words=descriptor(
            dimension=8, ratio=4, kv_heads=2, layers=2,
            intermediate=19, vocabulary=19, context=5,
            element=int(args.fp16), cache=int(args.fp16)) if args.large else None,
            tokens=4 if args.large else 2)
