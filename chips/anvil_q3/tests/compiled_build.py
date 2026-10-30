"""Fresh, source-bound compiled-host builds and optional GCC profile training."""

from dataclasses import asdict
import os
from pathlib import Path
import shutil

from execution import ROOT, VERILATOR_UNROLL, sha256, write_json


def build(run, g, name, optimize, gating, profile=False, flatten=False,
          compiler_flags=(), *, edge_digest=True, sources=None):
    obj = run.path / name
    constants = {"BANKS": g.BANKS, "QUEUE_DEPTH": g.QUEUE_DEPTH,
                 "LAYERS": g.NUM_LAYERS, "PROFILE": g.PROFILE,
                 "KV_DIM": g.NUM_KV_HEADS * g.HEAD_DIM,
                 "INTERMEDIATE": g.INTERMEDIATE_SIZE, "HIDDEN": g.HIDDEN_SIZE,
                 "VOCAB": g.VOCAB_SIZE, "THROUGHPUT_PROBE": 1,
                 "EVAL_GATING": int(gating), "EDGE_DIGEST": int(edge_digest)}
    if profile:
        constants["PROFILE_EVAL"] = 1
    flags = "-O3 -fno-tree-vectorize -std=c++20 " + " ".join(
        f"-DHOST_{key}={value}" for key, value in constants.items())
    flags += " " + " ".join(compiler_flags)
    if any(flag.startswith(("-fprofile-generate=", "-fprofile-use="))
           for flag in compiler_flags):
        # GCC otherwise encodes the entire build path in one .gcda filename.
        flags += " -fprofile-prefix-path=" + str(run.path.resolve())
    if Path(name).name == "lto":
        flags += " -flto"
    argv = ["verilator", "--cc", "--exe", "--assert", "-Wno-fatal",
            *VERILATOR_UNROLL, "--top-module", "anvil_q3_top",
            "--Mdir", run.rel(obj), "-o", "decoder", "-CFLAGS", flags]
    generation = [flag for flag in compiler_flags if flag.startswith("-fprofile-generate=")]
    if generation:
        argv += ["-LDFLAGS", " ".join(generation)]
    if flatten:
        argv.append("--flatten")
    if Path(name).name == "lto":
        argv += ["-LDFLAGS", "-flto"]
    argv += [f"-G{key}={value}" for key, value in asdict(g).items()]
    argv += sources if sources is not None else [
        str(p.relative_to(ROOT)) for p in sorted((ROOT / "rtl").glob("*.sv"))]
    argv += [os.path.relpath(ROOT / "tests/decoder_host.cpp", obj)]
    run.tool(argv)
    make = ["make", "-C", run.rel(obj), "-f", "Vanvil_q3_top.mk",
            "-j", str(run.resources["build_jobs"])]
    if optimize:
        make += ["OPT_FAST=-O3", "OPT_SLOW=-O3", "OPT_GLOBAL=-O3"]
    with run.compiler_admission():
        run.tool(make)
    return obj / "decoder"


def profiled_host(run, g, folder, sources, command):
    """Train a fresh executable prefix; the caller still runs the entire workload."""
    relative = str(folder.relative_to(run.path))
    training = folder / "compiler-training"
    training.mkdir()
    for name in ("map.tsv", "memory.hex", "tokens.txt", "expected-writes.txt"):
        shutil.copyfile(folder / name, training / name)
    profiles = folder / "training-profiles"
    train_name, use_name = "pgo-train", "pgo"
    binary = build(
        run, g, relative + "/" + train_name, True, True,
        sources=sources,
        compiler_flags=("-march=native", "-fprofile-generate=" + run.rel(profiles)))
    training_command = [
        "+directory=" + run.rel(training) if arg.startswith("+directory=") else arg
        for arg in command]
    run.tool([run.rel(binary), *training_command, "+throughput_cycles=1000000"],
             expected=(2,), timeout=14400)
    run.release_intermediates(binary.parent)
    generated = sorted(profiles.glob("*.gcda"))
    if not generated:
        raise AssertionError("GCC training produced no execution profiles")
    use_profiles = folder / "use-profiles"
    use_profiles.mkdir()
    bindings = []
    for source in generated:
        target = use_profiles / source.name.replace("pgo-train#", "pgo#")
        if target.name == source.name:
            raise AssertionError("unexpected GCC profile object path: " + source.name)
        shutil.copyfile(source, target)
        bindings.append({"training": run.rel(source), "use": run.rel(target),
                         "sha256": sha256(source)})
    write_json(folder / "profile-bindings.json", bindings)
    binary = build(
        run, g, relative + "/" + use_name, True, True,
        sources=sources, compiler_flags=(
            "-march=native",
            "-fprofile-use=" + os.path.relpath(use_profiles, folder / use_name),
            "-fprofile-partial-training",
            "-Werror=missing-profile", "-Werror=coverage-mismatch"))
    return binary
