"""Bounded compiled-decoder throughput diagnostic, never matrix acceptance.

python3 tests/throughput_probe.py --cycles 1000000 --workers 1 2 4 8

The complete C/BANKS8/INT4-symmetric/seed17 four-token fixture is unchanged.
By default only a fixed prefix executes, with every original public-edge
assertion and online numerical write comparison. Exit 2 denotes that incomplete
prefix. --pgo --complete-pgo additionally runs all four tokens with complete
independent comparisons. Neither diagnostic discharges admitted matrix gates.
Timed runs and instrumented host/model attribution are kept separate.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import shutil
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

from decoder_checks import allocate, compare_trace
from execution import ROOT, Run, VERILATOR_UNROLL, sha256, write_json
from parameters import C
from reference import Fixture


def fixture(folder):
    folder.mkdir()
    g = replace(C, BANKS=8, CACHE_MODE=2, INT4_ASYM=0)
    model = Fixture(g, 17)
    tokens = [1, 4, 2, 6]
    expected = model.oracle(tokens)
    allocate(model, folder, tokens)
    write_json(folder / "expected.json", expected)
    mapping = {}
    for line in (folder / "map.tsv").read_text().splitlines():
        kind, layer, proj, base, rows, cols = map(int, line.split())
        mapping[kind, layer, proj] = base, cols
    with (folder / "expected-writes.txt").open("w") as out:
        out.write(str(len(expected["writes"])) + "\n")
        for token, kind, layer, proj, row, col, value in expected["writes"]:
            base, cols = mapping[kind, layer, proj]
            out.write(f"{base + row * cols + col} {token} {value:08x}\n")
    write_json(folder / "fixture.json", {
        "geometry": asdict(g), "seed": 17, "tokens": tokens, "prefill_tokens": 2,
        "fixture_sha256": model.digest(),
        "files": {p.name: sha256(p) for p in folder.iterdir() if p.is_file()}})
    return g


VARIANTS = {
    "baseline": (False, False, False, False),
    "optimized": (True, False, False, False),
    "gated": (True, True, False, False),
    "profile-baseline": (False, False, True, False),
    "profile-gated": (True, True, True, False),
    "flattened": (True, True, False, True),
    "os-gated": (False, True, False, False),
    "lto": (True, True, False, False),
}


def build(run, g, name, optimize, gating, profile=False, flatten=False,
          compiler_flags=()):
    obj = run.path / name
    constants = {"BANKS": g.BANKS, "QUEUE_DEPTH": g.QUEUE_DEPTH,
                 "LAYERS": g.NUM_LAYERS, "PROFILE": g.PROFILE,
                 "KV_DIM": g.NUM_KV_HEADS * g.HEAD_DIM,
                 "INTERMEDIATE": g.INTERMEDIATE_SIZE, "HIDDEN": g.HIDDEN_SIZE,
                 "VOCAB": g.VOCAB_SIZE, "THROUGHPUT_PROBE": 1,
                 "EVAL_GATING": int(gating)}
    if profile:
        constants["PROFILE_EVAL"] = 1
    flags = "-O3 -fno-tree-vectorize -std=c++20 " + " ".join(
        f"-DHOST_{key}={value}" for key, value in constants.items())
    flags += " " + " ".join(compiler_flags)
    if name == "lto":
        flags += " -flto"
    argv = ["verilator", "--cc", "--exe", "--assert", "-Wno-fatal",
            *VERILATOR_UNROLL, "--top-module", "anvil_q3_top",
            "--Mdir", run.rel(obj), "-o", "decoder", "-CFLAGS", flags]
    generation = [flag for flag in compiler_flags if flag.startswith("-fprofile-generate=")]
    if generation:
        argv += ["-LDFLAGS", " ".join(generation)]
    if flatten:
        argv.append("--flatten")
    if name == "lto":
        argv += ["-LDFLAGS", "-flto"]
    argv += [f"-G{key}={value}" for key, value in asdict(g).items()]
    argv += [str(p.relative_to(ROOT)) for p in sorted((ROOT / "rtl").glob("*.sv"))]
    argv += [os.path.relpath(ROOT / "tests/decoder_host.cpp", obj)]
    run.tool(argv)
    make = ["make", "-C", run.rel(obj), "-f", "Vanvil_q3_top.mk",
            "-j", str(run.resources["build_jobs"])]
    if optimize:
        make += ["OPT_FAST=-O3", "OPT_SLOW=-O3", "OPT_GLOBAL=-O3"]
    run.tool(make)
    return obj / "decoder"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", type=int, default=1000000)
    parser.add_argument("--workers", type=int, nargs="+", default=[1, 2, 4, 8])
    parser.add_argument("--variants", nargs="+", choices=VARIANTS,
                        default=list(VARIANTS)[:5])
    parser.add_argument("--pgo", action="store_true",
                        help="measure a fresh GCC profile-guided candidate against the same prefix")
    parser.add_argument("--complete-pgo", action="store_true",
                        help="also execute and independently compare all four unchanged C tokens")
    parser.add_argument("--repair-of", default=(
        "evidence/check-behavior/shards/decoder-36c0bbcad86b21431b7d/"
        "20261029T234437Z-4da4ac961030/tool-0001/receipt.json"))
    args = parser.parse_args()
    if args.complete_pgo and not args.pgo:
        parser.error("--complete-pgo requires --pgo")
    if not 10000 <= args.cycles <= 2000000 or any(w not in (1, 2, 4, 8) for w in args.workers):
        parser.error("bounded prefix requires 10000..2000000 cycles and 1/2/4/8 workers")
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run = Run("evidence/preparation/compiled-throughput-" + stamp,
              "prefix throughput and host attribution; not engineering acceptance",
              repair_of=args.repair_of)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        run.versions([("python3", "--version"), ("verilator", "--version"),
                      ("g++", "--version"), ("make", "--version")])
        environment = {"affinity": sorted(os.sched_getaffinity(0)),
                       "resources": run.resources}
        for name in ("cpu.max", "cpu.stat", "memory.max", "cpu/cpu.cfs_quota_us",
                     "cpu/cpu.cfs_period_us"):
            path = Path("/sys/fs/cgroup") / name
            environment[name] = path.read_text() if path.is_file() else None
        write_json(run.path / "environment.json", environment)
        original = run.path / "fixture"
        g = fixture(original)
        binaries = {}

        def execute(name, suffix):
            folder = run.path / ("sample-" + suffix)
            shutil.copytree(original, folder, copy_function=os.link)
            text, record = run.tool([
                run.rel(binaries[name]), "+directory=" + run.rel(folder),
                "+tokens=4", "+first_new=1", "+prefill=2", "+prelude=0",
                "+fault=0", "+boundary=0", "+restart=-1", "+stream_compare=1",
                "+sparse_scan=1", f"+throughput_cycles={args.cycles}"], expected=(2,))
            result = json.loads(text)
            result.update({"variant": name, "receipt": str(Path(record["stdout"]).parent /
                                                          "receipt.json"),
                           "trace_sha256": sha256(folder / "trace.tsv"),
                           "executable_sha256": sha256(binaries[name])})
            return result

        samples = []
        for name in args.variants:
            binaries[name] = build(run, g, name, *VARIANTS[name])
            samples.append(execute(name, name))
            # The compiler and simulator have settled; only named intermediates go.
            for path in binaries[name].parent.iterdir():
                if path.is_file() and path.suffix in (".o", ".a", ".gch"):
                    path.unlink()
        if args.pgo:
            profiles = run.path / "training-profiles"
            binaries["pgo-train"] = build(
                run, g, "pgo-train", True, True,
                compiler_flags=("-fprofile-generate=" + run.rel(profiles),))
            samples.append(execute("pgo-train", "pgo-training"))
            generated = sorted(profiles.glob("*.gcda"))
            if not generated:
                raise AssertionError("GCC training produced no execution profiles")
            use_profiles = run.path / "use-profiles"
            use_profiles.mkdir()
            bindings = []
            for source in generated:
                target = use_profiles / source.name.replace("#pgo-train#", "#pgo#")
                if target == use_profiles / source.name:
                    raise AssertionError("unexpected GCC profile object path: " + source.name)
                shutil.copyfile(source, target)
                bindings.append({"training": run.rel(source), "use": run.rel(target),
                                 "sha256": sha256(source)})
            write_json(run.path / "profile-bindings.json", bindings)
            binaries["pgo"] = build(
                run, g, "pgo", True, True,
                compiler_flags=("-fprofile-use=" + os.path.relpath(use_profiles, run.path / "pgo"),
                                "-Werror=missing-profile", "-Werror=coverage-mismatch"))
            samples.append(execute("pgo", "pgo"))
            for name in ("pgo-train", "pgo"):
                for path in binaries[name].parent.iterdir():
                    if path.is_file() and path.suffix in (".o", ".a", ".gch"):
                        path.unlink()
        for workers in args.workers:
            variant = args.variants[-1]
            start = time.monotonic()
            with ThreadPoolExecutor(max_workers=workers) as pool:
                concurrent = list(pool.map(
                    lambda i: execute(variant, f"concurrent-{workers}-{i}"), range(workers)))
            samples += concurrent
            write_json(run.path / f"concurrency-{workers}.json", {
                "workers": workers, "wall_seconds": time.monotonic() - start,
                "samples": concurrent})
        identity = ("cycles", "requests", "responses", "writes", "expected_remaining",
                    "edge_digest", "trace_sha256")
        reference = {key: samples[0][key] for key in identity}
        if any({key: sample[key] for key in identity} != reference for sample in samples):
            raise AssertionError("optimization changed public-edge prefix or exact write comparison")
        write_json(run.path / "measurements.json", samples)
        complete = None
        if args.complete_pgo:
            folder = run.path / "complete-C"
            shutil.copytree(original, folder, copy_function=os.link)
            _, record = run.tool([
                run.rel(binaries["pgo"]), "+directory=" + run.rel(folder),
                "+tokens=4", "+first_new=1", "+prefill=2", "+prelude=0",
                "+fault=0", "+boundary=0", "+restart=-1", "+stream_compare=1",
                "+sparse_scan=1", "+throughput_cycles=0"], timeout=14400)
            complete = compare_trace(
                folder, json.loads((folder / "expected.json").read_text()), g,
                expected_tokens=[1, 4, 2, 6])
            complete.update({"simulator": "verilator", "workload": {
                "seed": 17, "tokens": [1, 4, 2, 6], "prefill_tokens": 2},
                "receipt": str(Path(record["stdout"]).parent / "receipt.json"),
                "executable_sha256": sha256(binaries["pgo"])})
            write_json(run.path / "complete-C.json", complete)
        run.finish("passed", result={"scope": "compiler candidate diagnostic; not matrix acceptance",
                                     "measurements": run.rel(run.path / "measurements.json"),
                                     "prefix_equivalence": reference,
                                     "complete_C": complete})
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise


if __name__ == "__main__":
    main()
