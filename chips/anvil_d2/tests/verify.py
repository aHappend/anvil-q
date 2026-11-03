#!/usr/bin/env python3
"""Portable source-current L1 verification and retained preparation probes."""

import argparse
import difflib
import hashlib
import json
import random
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import bf16_to_q16, committed_block, dequantize, quantize_group
from transformer_reference import Geometry, Target, WeightImage, argmax, matvec, rms

ROOT = Path(__file__).resolve().parents[1]
CHECK_DEADLINE = time.monotonic()+2700


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class Experiment:
    def __init__(self, stem, preparation=False):
        self.started_monotonic = time.monotonic()
        suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        self.directory = ROOT / "evidence" / ("preparation" if preparation else "verification") / (
            stem + "-" + suffix)
        self.directory.mkdir(parents=True)
        sources = sorted({p for pattern in (
            "rtl/*.sv", "anvil_d1_reference/rtl/*.sv", "design/*.md",
            "fpga/quartus_gate.json", "tests/*")
            for p in ROOT.glob(pattern) if p.is_file()})
        self.receipt = {
            "started_at": timestamp(),
            "entry_argv": [str(Path(sys.executable).name), "tests/verify.py", *sys.argv[1:]],
            "cwd": ".",
            "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sources},
            "commands": [], "results": {},
        }
        self.save()

    def save(self):
        (self.directory / "receipt.json").write_text(json.dumps(self.receipt, indent=2) + "\n")

    def execute(self, argv, name, timeout=600):
        remaining = CHECK_DEADLINE-time.monotonic()
        if remaining <= 0:
            raise TimeoutError("whole-check 2700-second execution budget exhausted")
        timeout = min(timeout, remaining)
        if Path(argv[0]).name == "vvp":
            timeout = min(timeout, 600)
        relative = self.directory.relative_to(ROOT)
        record = {"argv": argv, "cwd": ".", "started_at": timestamp(),
                  "timeout_s": timeout,
                  "stdout": str(relative / (name + ".stdout.txt")),
                  "stderr": str(relative / (name + ".stderr.txt"))}
        self.receipt["commands"].append(record)
        self.save()
        start = time.monotonic()
        try:
            with (ROOT / record["stdout"]).open("w") as stdout, (
                    ROOT / record["stderr"]).open("w") as stderr:
                try:
                    process = subprocess.Popen(argv, cwd=ROOT, stdout=stdout, stderr=stderr)
                    deadline = start+timeout
                    while True:
                        try:
                            exit_code = process.wait(timeout=min(30, max(0.01, deadline-time.monotonic())))
                            break
                        except subprocess.TimeoutExpired:
                            if time.monotonic() >= deadline:
                                process.kill()
                                process.wait()
                                raise
                            print(f"progress: {name} executing ({int(time.monotonic()-start)}s)",
                                  flush=True)
                    record["exit_code"] = exit_code
                    record["timed_out"] = False
                except subprocess.TimeoutExpired:
                    record["exit_code"] = None
                    record["timed_out"] = True
                    raise
        finally:
            record["ended_at"] = timestamp()
            record["duration_s"] = time.monotonic() - start
            self.save()
        if exit_code:
            raise RuntimeError(f"{name} exited {exit_code}; see {record['stdout']} "
                               f"and {record['stderr']}")
        return (ROOT / record["stdout"]).read_text()

    def finish(self, success, error=None):
        self.receipt.update(ended_at=timestamp(), success=success)
        if error:
            self.receipt["error"] = error
        self.save()
        print(str((self.directory / "receipt.json").relative_to(ROOT)), flush=True)

    def cleanup_intermediates(self):
        for directory in self.directory.iterdir():
            if directory.is_dir() and "-obj" in directory.name:
                for pattern in ("*.o", "*.a", "*.gch"):
                    for path in directory.glob(pattern):
                        path.unlink()


def dequant_vectors(path):
    scales = [0x00000001, 0x00000101, 0x007FFFFF, 0x00800000,
              0x00800001, 0x33800000, 0x3EAAAAAB, 0x3F000001,
              0x3F7FFFFF, 0x3F800000, 0x3F800001, 0x3FC00000,
              0x40000000, 0x477FE000, 0x7B000001, 0x7F7FFFFF]
    vectors = [(code, scale) for scale in scales for code in range(256)]
    vectors += [(code, scale) for scale in (
        0x3F808000, 0x3F818000, 0x3FFF8000, 0x007F8000, 0x00008000, 0x7F7F8000)
        for code in range(256)]
    rng = random.Random(17)
    vectors += [(rng.randrange(256), rng.randrange(1, 0x7F800000)) for _ in range(10000)]
    vectors += [(code, scale) for scale in (
        0, 0x80000000, 0xBF800000, 0x7F800000, 0x7FC00001, 0xFF800000)
        for code in (0, 1, 0x38, 0x7E, 0x7F, 0x80, 0xFF)]
    with path.open("w") as stream:
        for code, scale in vectors:
            fp32, bf16, error = dequantize(code, scale)
            stream.write(f"{code:02x} {scale:08x} {fp32:08x} {bf16:04x} {error:x}\n")
    return len(vectors)


def run_dequant(experiment, simulator, rtl="rtl/anvil_d2_fp8_dequant.sv",
                expect_mismatch=False):
    directory = experiment.directory.relative_to(ROOT)
    vectors = experiment.directory / "dequant-vectors.txt"
    count = dequant_vectors(vectors)
    if simulator == "icarus":
        experiment.execute(["iverilog", "-V"], "iverilog-version")
        binary = directory / "dequant.vvp"
        experiment.execute(["iverilog", "-g2012", "-Wall", "-s", "dequant_tb", "-o",
                            str(binary), rtl, "tests/dequant_tb.sv"],
                           "dequant-compile")
        argv = ["vvp", str(binary)]
    else:
        experiment.execute(["verilator", "--version"], "verilator-version")
        obj = directory / "dequant-obj"
        experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal",
                            "--top-module", "dequant_tb", "--Mdir", str(obj),
                            "-o", "dequant-sim", rtl,
                            "tests/dequant_tb.sv"], "dequant-compile", 1200)
        argv = [str(obj / "dequant-sim")]
    try:
        output = experiment.execute(argv + ["+vectors=" + str(vectors.relative_to(ROOT))],
                                    "dequant-simulation")
    except RuntimeError:
        command = experiment.receipt["commands"][-1]
        output = (ROOT / command["stdout"]).read_text() + (ROOT / command["stderr"]).read_text()
        if not expect_mismatch or command.get("timed_out") or "DEQUANT_MISMATCH" not in output:
            raise
        experiment.receipt["results"]["mutant"] = {
            "rejected_by": "normal exact-bit numerical scoreboard",
            "raw_diagnostic": output.strip(),
        }
        experiment.save()
        return
    if expect_mismatch:
        raise AssertionError("behavioral mutant survived normal numerical scoreboard")
    experiment.receipt["results"]["dequant"] = {
        "simulator": simulator, "vectors": count,
        "all_codes_at_distinct_scales": 16, "seeded_random_cases": 10000,
        "public_pin_scoreboard": True, "raw_summary": output.strip(),
    }
    experiment.save()


def run_public_smoke(experiment, boundaries=False, interrupts=False):
    directory = experiment.directory.relative_to(ROOT)
    obj = directory / "public-obj"
    sources = [str(p.relative_to(ROOT)) for pattern in (
        "rtl/*.sv", "anvil_d1_reference/rtl/*.sv") for p in sorted(ROOT.glob(pattern))]
    experiment.execute(["verilator", "--version"], "verilator-version")
    experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                        "--top-module", "top_smoke_tb", "--Mdir", str(obj),
                        "-o", "public-sim", *(["-GCAPACITY=5"] if boundaries else []),
                        *sources, "tests/top_smoke_tb.sv"],
                       "public-compile", 1200)
    output = experiment.execute([str(obj / "public-sim")] +
                                (["+boundaries"] if boundaries else
                                 ["+interrupts"] if interrupts else []),
                                "public-simulation", 1200)
    experiment.receipt["results"]["public-smoke"] = {
        "geometry": {"hidden": 8, "layers": 1, "banks": 2, "queue_depth": 3},
        "weight_fixture": "all-zero tensors; FP8 missing scales positive one",
        "oracle": "zero output projection gives zero logits and greedy token zero",
        "raw_summary": output.strip(),
        "scope": ("public cancellation at draft, verify, publish and memory drain; "
                  "bus error and sequence invalidation" if interrupts else
                  "four-mode EOS, zero-capacity and terminal shortening" if boundaries else
                  "bounded protocol smoke, not nonzero transformer numerical coverage"),
    }
    experiment.save()


def run_target_model(experiment, geometry=Geometry(), seed=17, modes=(0, 1, 2, 3),
                     override=None, expect_mismatch=False, mtp_fixture="random",
                     command_sequence=None, domain=0, compiled=None, parent=False):
    if parent and (tuple(modes) != (0,) or any(
            command[4] for command in (command_sequence or ()))):
        raise ValueError("unchanged parent consumes single-token/logit commands only")
    directory = experiment.directory.relative_to(ROOT)
    image = WeightImage(geometry, seed)
    if any(mode & 1 for mode in modes):
        image.add_mtp(mtp_fixture)
    words = image.external_words(True)
    fixture_directory = experiment.directory / "checkpoint-images"
    fixture_directory.mkdir()
    image_path = fixture_directory / "target-weights.txt"
    absorption_path = experiment.directory / "absorption-expected.txt"
    expected_path = experiment.directory / "cache-expected.txt"
    commands_path = experiment.directory / "commands.txt"
    image_path.write_text("".join(f"{address:026x} {word:08x}\n"
                                 for address, word in sorted(words.items())))
    absorption_path.write_text("".join(f"{address:026x} {word:08x}\n" for address, word in
                                      sorted(image.expected_absorption.items())))
    commands = []
    expected = {}
    for mode in modes:
        target = Target(image, bool(mode & 2))
        for token, position, fresh, phase, generate, limit in (command_sequence or (
                (1, 0, 1, 0, 0, 3), (2, 1, 0, 0, 0, 3),
                (3, 2, 0, 1, 1, 3), (4, 6, 0, 1, 1, 1))):
            if fresh:
                target = Target(image, bool(mode & 2))
            logits = target.process(token)
            outputs = logits
            if generate:
                outputs = []
                for _ in range(limit):
                    predicted = argmax(logits)
                    outputs.append(predicted)
                    logits = target.process(predicted)
            command = len(commands)+1
            # Select an EOS absent from this bounded continuation when possible.
            eos = next((token_id for token_id in range(geometry.vocab-1, -1, -1)
                        if token_id not in outputs), geometry.vocab-1) if generate else (
                            geometry.vocab-1)
            if generate and eos in outputs:
                raise AssertionError("bounded model fixture must provide an unused EOS")
            commands.append((command, mode, generate, token, position, fresh, phase,
                             limit, eos, len(outputs), 0, outputs))
            expected.update({(command << 103) | address: word
                             for address, word in target.expected_cache_words().items()})
    expected_path.write_text("".join(f"{address:034x} {word:08x}\n"
                                    for address, word in sorted(expected.items())))
    with commands_path.open("w") as stream:
        for *header, outputs in commands:
            stream.write(" ".join(map(str, header)) + "\n")
            stream.writelines(f"{output & 0xFFFFFFFF:08x}\n" for output in outputs)
    parameters = {
        "HIDDEN": geometry.hidden, "LAYERS": geometry.layers, "HEADS": geometry.heads,
        "RANK": geometry.rank, "NOPE": geometry.nope, "ROPE": geometry.rope,
        "VALUE": geometry.value, "EXPERTS": geometry.experts, "TOPK": geometry.top_k,
        "FIRST_DENSE": geometry.first_dense, "VOCAB": geometry.vocab,
        "CAPACITY": geometry.capacity, "BANKS": geometry.banks, "QUEUE": geometry.queue,
        "PARENT": int(parent),
    }
    sources = [str(p.relative_to(ROOT)) for pattern in (
        "rtl/*.sv", "anvil_d1_reference/rtl/*.sv") for p in sorted(ROOT.glob(pattern))]
    if override:
        sources = [override.get(path, path) for path in sources]
    obj = directory / "target-obj"
    if compiled is not None and (
            compiled["geometry"] != geometry.__dict__ or compiled["parent"] != parent or
            compiled["source_sha256"] != experiment.receipt["source_sha256"] or
            not (ROOT / compiled["binary"]).is_file()):
        experiment.receipt["rebuilt_stale_prerequisite"] = compiled["receipt"]
        experiment.save()
        compiled = None
    if compiled is None:
        experiment.execute(["verilator", "--version"], "verilator-version")
        experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                            "--top-module", "top_model_tb", "--Mdir", str(obj),
                            "-o", "target-sim",
                            *(f"-G{name}={value}" for name, value in parameters.items()),
                            *sources, "tests/top_model_tb.sv"], "target-compile", 1200)
        binary = obj / "target-sim"
    else:
        binary = Path(compiled["binary"])
        experiment.receipt["compiled_prerequisite"] = compiled
    experiment.receipt["results"]["target-fixtures"] = {
        "seed": seed, "geometry": geometry.__dict__, "modes": list(modes),
        "mtp_fixture": mtp_fixture,
        "commands": len(commands),
        "oracle": "independent arbitrary-precision unabsorbed equations and exact fixed-point boundaries",
        "image_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
        "domain": domain,
        "parent": parent,
        "command_expectations": [
            {"command": header[0], "mode": header[1], "generation": bool(header[2]),
             "token": header[3], "position": header[4], "expected": outputs}
            for *header, outputs in commands],
    }
    experiment.save()
    try:
        output = experiment.execute([str(binary),
                                     "+image=" + str(image_path.relative_to(ROOT)),
                                     "+expected=" + str(expected_path.relative_to(ROOT)),
                                     "+absorption=" + str(absorption_path.relative_to(ROOT)),
                                     "+commands=" + str(commands_path.relative_to(ROOT)),
                                     "+domain=" + str(domain),
                                     *(["+require-prefix=" + mtp_fixture[6:]]
                                       if mtp_fixture.startswith("prefix") else []),
                                     *(["+require-rejection"] if mtp_fixture=="reject-first" else [])],
                                    "target-simulation", 1800)
    except RuntimeError:
        command = experiment.receipt["commands"][-1]
        output = (ROOT / command["stdout"]).read_text() + (ROOT / command["stderr"]).read_text()
        if not expect_mismatch or command.get("timed_out") or not any(
                error in output for error in (
                    "TARGET_CACHE_MISMATCH", "TARGET_LOGIT_MISMATCH", "TARGET_TOKEN_MISMATCH")):
            raise
        experiment.receipt["results"]["mutant"] = {
            "rejected_by": "normal independent sequential target/cache scoreboard",
            "raw_diagnostic": output.strip(),
        }
        experiment.save()
        return
    if expect_mismatch:
        raise AssertionError("MTP/cache mutant survived independent target scoreboard")
    experiment.receipt["results"]["target-model"] = {"raw_summary": output.strip()}
    experiment.save()
    return {
        "binary": str(binary), "geometry": geometry.__dict__,
        "parent": parent,
        "source_sha256": experiment.receipt["source_sha256"],
        "receipt": str((experiment.directory / "receipt.json").relative_to(ROOT)),
    }


def run_head_model(experiment, override=None, expect_mismatch=False):
    image = WeightImage()
    image.add_mtp()
    rng = random.Random(233)
    directory = experiment.directory.relative_to(ROOT)
    images = experiment.directory / "checkpoint-images"
    images.mkdir()
    image_path = images / "native-head-weights.txt"
    image_path.write_text("".join(f"{address:026x} {word:08x}\n"
                                 for address, word in sorted(image.words.items())))
    absorption_path = experiment.directory / "head-absorption.txt"
    absorption_path.write_text("".join(f"{address:026x} {word:08x}\n" for address, word in
                                      sorted(image.expected_absorption.items())))
    models = [Target(SimpleNamespace(
        geometry=replace(image.geometry, layers=1, first_dense=0),
        embedding=image.embedding, final_gain=image.mtp_native.final_gain,
        layers=[weights])) for weights in image.mtp_native.layers]
    vectors = experiment.directory / "head-vectors.txt"
    with vectors.open("w") as stream:
        for position in range(1, 6):
            for head in range(min(position, 4)):
                token = 1+(position+head) % 5
                hidden = [rng.randrange(-131072, 131073) for _ in range(8)]
                gains, projection = image.mtp_projections[head]
                projected = matvec(projection, [
                    *rms(hidden, gains[0]), *rms(image.embedding[token], gains[1])])
                logits = models[head].process_hidden(projected, position)
                expected = models[head].last_raw_hidden
                stream.write(f"{head} {token} {position} {argmax(logits)}\n")
                stream.writelines(f"{a & 0xFFFFFFFF:08x} {b & 0xFFFFFFFF:08x}\n"
                                  for a, b in zip(hidden, expected))
    sources = [str(p.relative_to(ROOT)) for pattern in (
        "rtl/*.sv", "anvil_d1_reference/rtl/*.sv") for p in sorted(ROOT.glob(pattern))]
    if override:
        sources = [override.get(path, path) for path in sources]
    obj = directory / "head-obj"
    experiment.execute(["verilator", "--version"], "verilator-version")
    experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                        "--top-module", "draft_head_tb", "--Mdir", str(obj),
                        "-o", "head-sim", *sources, "tests/draft_head_tb.sv"],
                       "head-compile", 1200)
    try:
        output = experiment.execute([str(obj / "head-sim"),
                                     "+image=" + str(image_path.relative_to(ROOT)),
                                     "+absorption=" + str(absorption_path.relative_to(ROOT)),
                                     "+vectors=" + str(vectors.relative_to(ROOT))],
                                    "head-simulation", 600)
    except RuntimeError:
        command = experiment.receipt["commands"][-1]
        output = (ROOT / command["stdout"]).read_text() + (ROOT / command["stderr"]).read_text()
        if not expect_mismatch or command.get("timed_out") or not any(
                error in output for error in ("HEAD_HIDDEN_MISMATCH", "HEAD_TOKEN_MISMATCH")):
            raise
        experiment.receipt["results"]["mutant"] = {
            "rejected_by": "normal independent native-head hidden/token scoreboard",
            "raw_diagnostic": output.strip(),
        }
        experiment.save()
        return
    if expect_mismatch:
        raise AssertionError("MTP alignment mutant survived native-head scoreboard")
    experiment.receipt["results"]["native-head"] = {
        "heads": 4, "commands": 14, "seed": 233,
        "oracle": "independent RMS, concatenation, nonzero MLA, routed/shared experts and tied output",
        "raw_summary": output.strip(),
    }
    experiment.save()


def run_alignment_mutant(experiment):
    path = "rtl/anvil_d2_mtp_projection.sv"
    original = (ROOT / path).read_text()
    before, after = "embedding_address ? token : raw_row", "embedding_address ? token+32'd1 : raw_row"
    if original.count(before) != 1:
        raise AssertionError("alignment mutation anchor must occur exactly once")
    mutated = original.replace(before, after)
    copied = experiment.directory / Path(path).name
    copied.write_text(mutated)
    diff_path = experiment.directory / "mutant.diff"
    diff_path.write_text("".join(difflib.unified_diff(
        original.splitlines(True), mutated.splitlines(True), fromfile=path,
        tofile="disposable/" + copied.name)))
    experiment.receipt["mutation"] = {
        "defect": "mtp-embedding-alignment",
        "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "mutated_sha256": hashlib.sha256(mutated.encode()).hexdigest(),
        "diff": str(diff_path.relative_to(ROOT)),
    }
    experiment.save()
    run_head_model(experiment, {path: str(copied.relative_to(ROOT))}, expect_mismatch=True)


def run_target_mutant(experiment, defect):
    path, before, after = {
        "causal-mask": (
            "rtl/anvil_d2_verify_cache.sv",
            "layer_base+(read_row-first_pos)*CW+read_col",
            "layer_base+((read_row+32'd1<first_pos+{29'd0,lanes}) ? "
            "read_row-first_pos+32'd1 : read_row-first_pos)*CW+read_col"),
        "rejected-kv": (
            "rtl/anvil_d2_mtp_engine.sv",
            "kept_lanes<=verified_kept;", "kept_lanes<=target_lanes;"),
    }[defect]
    original = (ROOT / path).read_text()
    if original.count(before) != 1:
        raise AssertionError(f"{defect} mutation anchor must occur exactly once")
    mutated = original.replace(before, after)
    copied = experiment.directory / Path(path).name
    copied.write_text(mutated)
    diff_path = experiment.directory / "mutant.diff"
    diff_path.write_text("".join(difflib.unified_diff(
        original.splitlines(True), mutated.splitlines(True), fromfile=path,
        tofile="disposable/" + copied.name)))
    experiment.receipt["mutation"] = {
        "defect": defect, "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "mutated_sha256": hashlib.sha256(mutated.encode()).hexdigest(),
        "diff": str(diff_path.relative_to(ROOT)),
    }
    experiment.save()
    run_target_model(experiment, Geometry(layers=2), modes=(1,),
                     override={path: str(copied.relative_to(ROOT))}, expect_mismatch=True,
                     mtp_fixture="reject-first")


def run_numerical_leaf(experiment, leaf, simulator):
    directory = experiment.directory.relative_to(ROOT)
    vectors = experiment.directory / (leaf + "-vectors.txt")
    if leaf == "bf16":
        with vectors.open("w") as stream:
            for bits in range(65536):
                result, error = bf16_to_q16(bits)
                stream.write(f"{bits:04x} {result:08x} {error:x}\n")
        rtl = "rtl/anvil_d2_bf16_to_q16.sv"
        count = 65536
    else:
        rng = random.Random(233)
        lengths = [1, 2, 3, 4, 127, 128, 129, 255, 256]
        logical = [[0] * length for length in lengths]
        logical += [[-0x80000000, 0x7FFFFFFF, -1, 0, 1]]
        from reference import FP8_POSITIVES
        midpoints = [int((low + high) * 32768) for low, high in zip(
            FP8_POSITIVES, FP8_POSITIVES[1:])]
        logical += [[448 << 16, *midpoints], [-(448 << 16), *(-x for x in midpoints)]]
        logical += [[rng.randrange(-0x80000000, 0x80000000) for _ in range(length)]
                    for _ in range(12) for length in lengths]
        groups = [values[start:start+128] for values in logical
                  for start in range(0, len(values), 128)]
        count = sum(map(len, groups))
        with vectors.open("w") as stream:
            for group in groups:
                scale, codes = quantize_group(group)
                stream.write(f"{len(group)} {scale:08x}\n")
                for value, code in zip(group, codes):
                    stream.write(f"{value & 0xFFFFFFFF:08x} {code:02x}\n")
        rtl = "rtl/anvil_d2_fp8_group_quantizer.sv"
    top = leaf + "_tb"
    bench = "tests/" + top + ".sv"
    if simulator == "icarus":
        experiment.execute(["iverilog", "-V"], "iverilog-version")
        binary = directory / (leaf + ".vvp")
        experiment.execute(["iverilog", "-g2012", "-Wall", "-s", top, "-o",
                            str(binary), rtl, bench], leaf + "-compile")
        argv = ["vvp", str(binary)]
    else:
        experiment.execute(["verilator", "--version"], "verilator-version")
        obj = directory / (leaf + "-obj")
        experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal",
                            "--top-module", top, "--Mdir", str(obj),
                            "-o", leaf + "-sim", rtl, bench], leaf + "-compile", 1200)
        argv = [str(obj / (leaf + "-sim"))]
    output = experiment.execute(argv + ["+vectors=" + str(vectors.relative_to(ROOT))],
                                leaf + "-simulation")
    experiment.receipt["results"][leaf] = {
        "simulator": simulator, "vectors": count,
        "public_pin_scoreboard": True, "raw_summary": output.strip(),
    }
    experiment.save()


def run_synthesis_probe(experiment, configuration="compact"):
    directory = experiment.directory.relative_to(ROOT)
    sources = [str(p.relative_to(ROOT)) for pattern in (
        "rtl/*.sv", "anvil_d1_reference/rtl/*.sv") for p in sorted(ROOT.glob(pattern))]
    parameters = {
        "NUM_LAYERS": 1, "HIDDEN_SIZE": 8, "INTERMEDIATE_SIZE": 8,
        "NUM_Q_HEADS": 1, "KV_LORA_RANK": 2, "QK_NOPE_HEAD_DIM": 2,
        "QK_ROPE_HEAD_DIM": 2, "V_HEAD_DIM": 2, "ROUTED_EXPERTS": 2,
        "TOP_K": 1, "MOE_INTERMEDIATE_SIZE": 8, "FIRST_DENSE_LAYERS": 1,
        "VOCAB_SIZE": 4, "MAX_SEQ_LEN": 12, "BANKS": 2,
        "QUEUE_DEPTH": 3, "TILE_K": 8, "TILE_ROWS": 1,
    }
    if configuration == "minimum":
        parameters.update(KV_LORA_RANK=1, QK_NOPE_HEAD_DIM=1, V_HEAD_DIM=1,
                          BANKS=1, QUEUE_DEPTH=1, MAX_SEQ_LEN=1)
    elif configuration == "production":
        parameters = {}
    script = experiment.directory / "integrated.ys"
    commands = [
        "read_verilog -sv " + " ".join(sources),
        *(["chparam " + " ".join(f"-set {key} {value}" for key, value in parameters.items()) +
           " anvil_d2_top"] if parameters else []),
        "hierarchy -check -top anvil_d2_top",
        "proc", "opt_expr", "opt_clean", "check -noinit -assert",
        "memory -nomap", "opt_clean", "check -noinit -assert", "stat",
        f"write_json {directory}/integrated.json",
    ]
    script.write_text("\n".join(commands) + "\n")
    experiment.execute(["yosys", "-V"], "yosys-version")
    experiment.execute(["yosys", "-s", str(script.relative_to(ROOT))],
                       "integrated-synthesis", 1800)
    netlist = json.loads((experiment.directory / "integrated.json").read_text())
    cell_counts = {}
    memory_bits = 0
    for module in netlist["modules"].values():
        if int(module.get("attributes", {}).get("blackbox", "0"), 2):
            raise AssertionError("black-box module in synthesized hierarchy")
        for cell in module.get("cells", {}).values():
            kind = cell["type"]
            cell_counts[kind] = cell_counts.get(kind, 0) + 1
            if "latch" in kind.lower() or kind in ("$div", "$mod", "$divfloor", "$modfloor"):
                raise AssertionError(f"forbidden synthesis cell {kind}")
            if kind.startswith("$mem"):
                params = cell["parameters"]
                memory_bits += int(params.get("WIDTH", "0"), 2) * int(
                    params.get("SIZE", "0"), 2)
    sequential = sum(value for kind, value in cell_counts.items() if "dff" in kind.lower())
    assert sequential > 100, f"insubstantial sequential state: {sequential}"
    assert memory_bits > 0, "no inferred memory state"
    top = netlist["modules"]["anvil_d2_top"]
    for instance in ("mtp", "fp8"):
        assert instance in top["cells"], f"missing integrated {instance}"
        assert any(isinstance(bit, int) for connections in top["cells"][instance][
            "connections"].values() for bit in connections), f"constant {instance}"
    experiment.receipt["results"]["synthesis-probe"] = {
        "configuration": configuration, "parameters": parameters,
        "sequential_cell_definitions": sequential,
        "memory_definition_bits": memory_bits,
        "cell_definition_counts": cell_counts,
        "scope": "integrated RAM-preserving generic synthesis; not physical timing/PPA",
    }
    experiment.save()


def run_parameter_probe(experiment):
    sources = [str(p.relative_to(ROOT)) for pattern in (
        "rtl/*.sv", "anvil_d1_reference/rtl/*.sv") for p in sorted(ROOT.glob(pattern))]
    compact = {
        "NUM_LAYERS": 1, "HIDDEN_SIZE": 8, "INTERMEDIATE_SIZE": 8,
        "NUM_Q_HEADS": 1, "KV_LORA_RANK": 1, "QK_NOPE_HEAD_DIM": 1,
        "QK_ROPE_HEAD_DIM": 2, "V_HEAD_DIM": 1, "ROUTED_EXPERTS": 6,
        "TOP_K": 1, "MOE_INTERMEDIATE_SIZE": 8, "FIRST_DENSE_LAYERS": 1,
        "VOCAB_SIZE": 4, "MAX_SEQ_LEN": 5, "BANKS": 1, "QUEUE_DEPTH": 1,
        "TILE_K": 8, "TILE_ROWS": 1,
    }
    bounds = {
        "NUM_LAYERS": (1, 36), "HIDDEN_SIZE": (8, 2048), "INTERMEDIATE_SIZE": (8, 11008),
        "NUM_Q_HEADS": (1, 16), "KV_LORA_RANK": (1, 512), "QK_NOPE_HEAD_DIM": (1, 128),
        "QK_ROPE_HEAD_DIM": (2, 64), "V_HEAD_DIM": (1, 128), "ROUTED_EXPERTS": (1, 64),
        "TOP_K": (1, 6), "SHARED_EXPERTS": (2, 2), "MOE_INTERMEDIATE_SIZE": (8, 1408),
        "FIRST_DENSE_LAYERS": (0, 1), "VOCAB_SIZE": (4, 151936),
        "MAX_SEQ_LEN": (1, 32768), "BANKS": (1, 8), "QUEUE_DEPTH": (1, 16),
        "TILE_K": (8, 128), "TILE_ROWS": (1, 8),
        "GROUP_SIZE": (128, 128), "MTP_K": (4, 4),
    }
    invalid = [{name: value} for name, (low, high) in bounds.items()
               for value in (low-1, high+1)]
    invalid += [{"BANKS": 3}, {"HIDDEN_SIZE": 10}, {"INTERMEDIATE_SIZE": 10},
                {"MOE_INTERMEDIATE_SIZE": 10}, {"QK_ROPE_HEAD_DIM": 3}, {"TILE_K": 10},
                {"ROUTED_EXPERTS": 1, "TOP_K": 2}, {"MODEL_MODE": 2}]
    legal = [{"BANKS": banks, "QUEUE_DEPTH": queue}
             for banks, queue in ((1, 1), (2, 3), (4, 16), (8, 1))]
    legal += [{"KV_LORA_RANK": rank} for rank in (1, 127, 128, 129, 512)]
    legal += [{"MAX_SEQ_LEN": 1}, {"VOCAB_SIZE": 7}, {"TOP_K": 6},
              {"FIRST_DENSE_LAYERS": 0}, {"TILE_K": 128, "TILE_ROWS": 8},
              {"HIDDEN_SIZE": 2048}, {"NUM_LAYERS": 36}]
    experiment.execute(["iverilog", "-V"], "iverilog-version")
    results = []
    for rejected, cases in ((True, invalid), (False, legal)):
        for overrides in cases:
            case = len(results)
            parameters = {**compact, **overrides}
            binary = experiment.directory / f"parameters-{case}.vvp"
            experiment.execute(["iverilog", "-g2012", "-Wall", "-s", "anvil_d2_top",
                                *(item for name, value in parameters.items()
                                  for item in ("-P", f"anvil_d2_top.{name}={value}")),
                                "-o", str(binary.relative_to(ROOT)), *sources],
                               f"parameter-{case}-compile", 600)
            try:
                output = experiment.execute(["vvp", str(binary.relative_to(ROOT))],
                                            f"parameter-{case}-diagnostic")
            except RuntimeError:
                command = experiment.receipt["commands"][-1]
                output = (ROOT / command["stdout"]).read_text() + (ROOT / command["stderr"]).read_text()
                if not rejected or command.get("timed_out") or "PARAMETER ERROR" not in output:
                    raise
            else:
                if rejected:
                    raise AssertionError(f"illegal parameter configuration accepted: {overrides}")
            results.append({"overrides": overrides,
                            "observation": "explicit fatal diagnostic" if rejected else
                                           "integrated elaboration only"})
            experiment.receipt["results"]["parameters"] = results
            experiment.save()


def run_dequant_mutant(experiment, defect):
    source_path = ROOT / "rtl/anvil_d2_fp8_dequant.sv"
    original = source_path.read_text()
    before, after = {
        "fp8-bias": ("})-11'sd10", "})-11'sd9"),
        "bf16-tie": ("bits[15] && ((|bits[14:0]) || bits[16])", "bits[15]"),
    }[defect]
    if original.count(before) != 1:
        raise AssertionError(f"mutation anchor for {defect} must occur exactly once")
    mutated = original.replace(before, after)
    copied = experiment.directory / "anvil_d2_fp8_dequant.sv"
    copied.write_text(mutated)
    (experiment.directory / "mutant.diff").write_text("".join(difflib.unified_diff(
        original.splitlines(True), mutated.splitlines(True),
        fromfile="rtl/anvil_d2_fp8_dequant.sv",
        tofile="disposable/anvil_d2_fp8_dequant.sv")))
    experiment.receipt["mutation"] = {
        "defect": defect, "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "mutated_sha256": hashlib.sha256(mutated.encode()).hexdigest(),
        "diff": str((experiment.directory / "mutant.diff").relative_to(ROOT)),
    }
    experiment.save()
    run_dequant(experiment, "verilator", str(copied.relative_to(ROOT)), expect_mismatch=True)


def run_service_probe(experiment, rtl="rtl/anvil_d2_fp8_mla_moe.sv",
                      expect_mismatch=False):
    rng = random.Random(89)
    directory = experiment.directory.relative_to(ROOT)
    vectors = experiment.directory / "service-vectors.txt"
    fixtures = []
    for row, length in enumerate([1, 2, 3, 4, 127, 128, 129, 255, 256] * 5):
        values = [rng.randrange(-0x80000000, 0x80000000) for _ in range(length)]
        for base in range(0, length, 128):
            part = values[base:base+128]
            scale, codes = quantize_group(part)
            fixtures.append((0, 1, row % 3, row, base, part, scale, codes))
    for sequence in range(24):
        count = 128 if sequence < 6 else [1, 2, 3, 4, 127, 128][sequence % 6]
        # Revisit the same expert key with changed scales and payload after flush.
        scale = [0x3EAAAAAB, 0x3F800001, 0x3F818000][sequence % 3]
        codes = [rng.randrange(127) | (rng.randrange(2) << 7) for _ in range(count)]
        fixtures.append((1, 1, 2, (sequence // 3) % 2, 0, [0] * count, scale, codes))
    with vectors.open("w") as stream:
        for operation, epoch, layer, row, base, values, scale, codes in fixtures:
            stream.write(f"{operation} {epoch} {layer} {row} {base} {len(values)} 0 {scale:08x}\n")
            for value, code in zip(values, codes):
                fp32, bf16, error = dequantize(code, scale)
                q16, qerror = bf16_to_q16(bf16)
                assert not error and not qerror
                stream.write(f"{value & 0xFFFFFFFF:08x} {code:02x} {fp32:08x} "
                             f"{bf16:04x} {q16:08x}\n")
    obj = directory / "service-obj"
    experiment.execute(["verilator", "--version"], "verilator-version")
    experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal",
                        "--top-module", "fp8_service_tb", "--Mdir", str(obj),
                        "-o", "service-sim", "rtl/anvil_d2_fp8_dequant.sv",
                        "rtl/anvil_d2_fp8_group_quantizer.sv",
                        "rtl/anvil_d2_bf16_to_q16.sv", rtl,
                        "tests/fp8_service_tb.sv"], "service-compile", 1200)
    try:
        output = experiment.execute([str(obj / "service-sim"),
                                     "+vectors=" + str(vectors.relative_to(ROOT))],
                                    "service-simulation")
    except RuntimeError:
        command = experiment.receipt["commands"][-1]
        output = (ROOT / command["stdout"]).read_text() + (ROOT / command["stderr"]).read_text()
        diagnostics = ("SERVICE_NUMERICAL_MISMATCH", "CACHE_PACKING_MISMATCH",
                       "CACHE_SCALE_WRITE_MISMATCH", "GROUP_READ_OR_FLUSH_INVALIDATION_ACCOUNTING")
        if not expect_mismatch or command.get("timed_out") or not any(
                diagnostic in output for diagnostic in diagnostics):
            raise
        experiment.receipt["results"]["mutant"] = {
            "rejected_by": "normal numerical/transfer scoreboard",
            "raw_diagnostic": output.strip(),
        }
        experiment.save()
        return
    if expect_mismatch:
        raise AssertionError("behavioral service mutant survived normal scoreboard")
    experiment.receipt["results"]["service"] = {
        "fixtures": len(fixtures), "seed": 89, "raw_summary": output.strip(),
        "scope": "cache packing/roundtrip and expert dequantized Q16 boundary; not MAC/logit coverage",
    }
    experiment.save()


def run_service_mutant(experiment, defect):
    source_path = ROOT / "rtl/anvil_d2_fp8_mla_moe.sv"
    original = source_path.read_text()
    before, after = {
        "byte-order": ("selected_byte=payload_q >> {element_index[1:0],3'b000}",
                       "selected_byte=payload_q >> {~element_index[1:0],3'b000}"),
        "scale-group": ("base_col>>7", "base_col>>6"),
        "scale-invalidation": ("resident_valid<=0; epoch_valid<=0;", "epoch_valid<=0;"),
    }[defect]
    if original.count(before) != 1:
        raise AssertionError(f"mutation anchor for {defect} must occur exactly once")
    mutated = original.replace(before, after)
    copied = experiment.directory / "anvil_d2_fp8_mla_moe.sv"
    copied.write_text(mutated)
    (experiment.directory / "mutant.diff").write_text("".join(difflib.unified_diff(
        original.splitlines(True), mutated.splitlines(True),
        fromfile="rtl/anvil_d2_fp8_mla_moe.sv",
        tofile="disposable/anvil_d2_fp8_mla_moe.sv")))
    experiment.receipt["mutation"] = {
        "defect": defect, "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "mutated_sha256": hashlib.sha256(mutated.encode()).hexdigest(),
        "diff": str((experiment.directory / "mutant.diff").relative_to(ROOT)),
    }
    experiment.save()
    run_service_probe(experiment, str(copied.relative_to(ROOT)), expect_mismatch=True)


def run_verdict_probe(experiment, simulator, rtl="rtl/anvil_d2_mtp_verdict.sv",
                      expect_mismatch=False):
    directory = experiment.directory.relative_to(ROOT)
    vectors = experiment.directory / "verdict-vectors.txt"
    cases = 0
    with vectors.open("w") as stream:
        for proposed in range(5):
            for prefix in range(proposed+1):
                drafts = [1, 2, 3, 4]
                targets = drafts.copy()
                if prefix < proposed:
                    targets[prefix] += 10
                for limit in range(1, 6):
                    for first in (1, 9, 11):
                        untruncated, _, _ = committed_block(
                            0, drafts, targets, proposed, limit, first, 12, 99)
                        for eos_index in range(-1, len(untruncated)):
                            eos = 99 if eos_index < 0 else untruncated[eos_index]
                            expected, accepted, rejected = committed_block(
                                0, drafts, targets, proposed, limit, first, 12, eos)
                            packed_drafts = sum(token << (32*i) for i, token in enumerate(drafts))
                            packed_targets = sum(token << (32*i) for i, token in enumerate(targets))
                            packed_expected = sum(token << (32*i) for i, token in enumerate(expected))
                            stream.write(f"0 {packed_drafts:032x} {packed_targets:032x} "
                                         f"{proposed} {limit} {first} {eos:x} "
                                         f"{len(expected)} {accepted} {int(rejected)} "
                                         f"{packed_expected:040x} {prefix} {eos_index}\n")
                            cases += 1
    if simulator == "icarus":
        experiment.execute(["iverilog", "-V"], "iverilog-version")
        binary = directory / "verdict.vvp"
        experiment.execute(["iverilog", "-g2012", "-Wall", "-s", "verdict_tb", "-o",
                            str(binary), rtl, "tests/verdict_tb.sv"],
                           "verdict-compile")
        argv = ["vvp", str(binary)]
    else:
        experiment.execute(["verilator", "--version"], "verilator-version")
        obj = directory / "verdict-obj"
        experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal",
                            "--top-module", "verdict_tb", "--Mdir", str(obj),
                            "-o", "verdict-sim", rtl,
                            "tests/verdict_tb.sv"], "verdict-compile", 1200)
        argv = [str(obj / "verdict-sim")]
    try:
        output = experiment.execute(argv + ["+vectors=" + str(vectors.relative_to(ROOT))],
                                    "verdict-simulation")
    except RuntimeError:
        command = experiment.receipt["commands"][-1]
        output = (ROOT / command["stdout"]).read_text() + (ROOT / command["stderr"]).read_text()
        if not expect_mismatch or command.get("timed_out") or "VERDICT_MISMATCH" not in output:
            raise
        experiment.receipt["results"]["mutant"] = {
            "rejected_by": "normal committed-block numerical/protocol scoreboard",
            "raw_diagnostic": output.strip(),
        }
        experiment.save()
        return
    if expect_mismatch:
        raise AssertionError("acceptance mutant survived normal committed-block scoreboard")
    experiment.receipt["results"]["verdict"] = {
        "cases": cases, "simulator": simulator, "raw_summary": output.strip(),
        "scope": "public-pin block publication unit; not native MTP-head prefix coverage",
    }
    experiment.save()


def run_acceptance_mutant(experiment):
    original = (ROOT / "rtl/anvil_d2_mtp_verdict.sv").read_text()
    before, after = "else prefix_matches=0;", "else prefix_matches=1;"
    if original.count(before) != 1:
        raise AssertionError("acceptance mutation anchor must occur exactly once")
    mutated = original.replace(before, after)
    copied = experiment.directory / "anvil_d2_mtp_verdict.sv"
    copied.write_text(mutated)
    (experiment.directory / "mutant.diff").write_text("".join(difflib.unified_diff(
        original.splitlines(True), mutated.splitlines(True),
        fromfile="rtl/anvil_d2_mtp_verdict.sv", tofile="disposable/anvil_d2_mtp_verdict.sv")))
    experiment.receipt["mutation"] = {
        "defect": "acceptance-past-mismatch",
        "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "mutated_sha256": hashlib.sha256(mutated.encode()).hexdigest(),
        "diff": str((experiment.directory / "mutant.diff").relative_to(ROOT)),
    }
    experiment.save()
    run_verdict_probe(experiment, "verilator", str(copied.relative_to(ROOT)),
                      expect_mismatch=True)


def run_scheduler(experiment, banks=2, queue=3):
    directory = experiment.directory.relative_to(ROOT)
    binary = directory / "scheduler.vvp"
    experiment.execute(["iverilog", "-V"], "iverilog-version")
    experiment.execute(["iverilog", "-g2012", "-Wall", "-s", "scheduler_tb",
                        "-P", f"scheduler_tb.BANKS={banks}",
                        "-P", f"scheduler_tb.QUEUE_DEPTH={queue}", "-o", str(binary),
                        "rtl/anvil_d2_bank_scheduler.sv", "tests/scheduler_tb.sv"],
                       "scheduler-compile")
    output = experiment.execute(["vvp", str(binary)], "scheduler-simulation", 600)
    experiment.receipt["results"]["scheduler"] = {
        "banks": banks, "queue_depth": queue, "raw_summary": output.strip(),
        "oracle": "public accepted transactions, unique payloads and saved external tags",
        "scope": "out-of-order, bank stalls, response stalls, duplicate/unknown/stale tags, "
                 "flush with outstanding work, injected bus error and conservation",
    }
    experiment.save()


def run_rms(experiment, hidden=2048, simulator="verilator"):
    directory = experiment.directory.relative_to(ROOT)
    vectors = experiment.directory / "rms-vectors.txt"
    with vectors.open("w") as stream:
        for seed in (17, 89, 233):
            rng = random.Random(seed)
            values = [rng.randrange(-131072, 131073) for _ in range(hidden)]
            gains = [rng.randrange(32768, 98305) for _ in range(hidden)]
            expected = rms(values, gains)
            for value, gain, result in zip(values, gains, expected):
                stream.write(f"{value & 0xFFFFFFFF:08x} {gain:08x} "
                             f"{result & 0xFFFFFFFF:08x}\n")
    sources = [str(p.relative_to(ROOT)) for p in sorted(
        (ROOT / "anvil_d1_reference/rtl").glob("*.sv"))]
    if simulator == "icarus" and hidden <= 32:
        experiment.execute(["iverilog", "-V"], "iverilog-version")
        binary = directory / "rms.vvp"
        experiment.execute(["iverilog", "-g2012", "-Wall", "-s", "rms_tb",
                            "-P", f"rms_tb.HIDDEN={hidden}", "-o", str(binary),
                            *sources, "tests/rms_tb.sv"], "rms-compile")
        argv = ["vvp", str(binary)]
    else:
        experiment.execute(["verilator", "--version"], "verilator-version")
        obj = directory / "rms-obj"
        experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                            "--top-module", "rms_tb", "--Mdir", str(obj),
                            f"-GHIDDEN={hidden}", "-o", "rms-sim", *sources,
                            "tests/rms_tb.sv"], "rms-compile", 1200)
        argv = [str(obj / "rms-sim")]
    output = experiment.execute(argv + ["+vectors=" + str(vectors.relative_to(ROOT))],
                                "rms-simulation")
    experiment.receipt["results"]["rms"] = {
        "hidden": hidden, "seeds": [17, 89, 233], "raw_summary": output.strip(),
        "oracle": "arbitrary-precision sum, integer square root, reciprocal and Q16 rounding",
        "scope": "inherited native RMS datapath used by D2; not full-geometry transformer inference",
    }
    experiment.save()


def run_target_lanes(experiment):
    directory = experiment.directory.relative_to(ROOT)
    image = WeightImage(Geometry(layers=2), 233)
    images = experiment.directory / "checkpoint-images"
    images.mkdir()
    image_path = images / "lane-weights.txt"
    image_path.write_text("".join(f"{address:026x} {word:08x}\n"
                                 for address, word in sorted(image.words.items())))
    absorption_path = experiment.directory / "lane-absorption.txt"
    absorption_path.write_text("".join(f"{address:026x} {word:08x}\n" for address, word in
                                      sorted(image.expected_absorption.items())))
    target = Target(image)
    result_path = experiment.directory / "lane-results.txt"
    with result_path.open("w") as stream:
        for token in (1, 2, 3, 4):
            prediction = argmax(target.process(token))
            stream.write(f"{prediction:08x}\n")
            stream.writelines(f"{value & 0xFFFFFFFF:08x}\n"
                              for value in target.last_raw_hidden)
    cache_path = experiment.directory / "lane-cache.txt"
    cache_path.write_text("".join(f"{address:026x} {word:08x}\n" for address, word in
                                 sorted(target.expected_cache_words().items())))
    sources = [str(p.relative_to(ROOT)) for pattern in (
        "rtl/*.sv", "anvil_d1_reference/rtl/*.sv") for p in sorted(ROOT.glob(pattern))]
    obj = directory / "lanes-obj"
    experiment.execute(["verilator", "--version"], "verilator-version")
    experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                        "--top-module", "target_lanes_tb", "--Mdir", str(obj),
                        "-o", "lanes-sim", *sources, "tests/target_lanes_tb.sv"],
                       "lanes-compile", 1200)
    output = experiment.execute([str(obj / "lanes-sim"),
                                 "+image=" + str(image_path.relative_to(ROOT)),
                                 "+cache=" + str(cache_path.relative_to(ROOT)),
                                 "+absorption=" + str(absorption_path.relative_to(ROOT)),
                                 "+results=" + str(result_path.relative_to(ROOT))],
                                "lanes-simulation")
    experiment.receipt["results"]["target-lanes"] = {
        "seed": 233, "geometry": image.geometry.__dict__, "raw_summary": output.strip(),
        "oracle": "independent sequential target, four distinct tokens, two layers",
        "scope": "public unit interface: exact hidden/KV/tokens, held results, registered "
                 "commit/release, simultaneous four-lane query-weight transfers per layer",
    }
    experiment.save()


def parent_prerequisites(experiment):
    observations = {
        "generational_handoff": (ROOT / "design/GENERATIONAL_HANDOFF.md").is_file(),
        "original_scheduler": any("module anvil_q3_bank_scheduler" in p.read_text()
                                  for p in (ROOT / "anvil_d1_reference/rtl").glob("*.sv")),
        "original_legacy_top": any("module anvil_q3_top" in p.read_text()
                                   for p in (ROOT / "anvil_d1_reference/rtl").glob("*.sv")),
    }
    experiment.receipt["results"]["parent_prerequisites"] = observations
    experiment.save()
    return observations


def run_parent_comparison(experiment):
    observations = parent_prerequisites(experiment)
    binary = experiment.directory.relative_to(ROOT) / "parent.vvp"
    parameters = {
        "NUM_LAYERS": 1, "HIDDEN_SIZE": 8, "INTERMEDIATE_SIZE": 8,
        "NUM_Q_HEADS": 1, "KV_LORA_RANK": 3, "QK_NOPE_HEAD_DIM": 2,
        "QK_ROPE_HEAD_DIM": 2, "V_HEAD_DIM": 2, "ROUTED_EXPERTS": 2,
        "TOP_K": 1, "MOE_INTERMEDIATE_SIZE": 8, "FIRST_DENSE_LAYERS": 1,
        "VOCAB_SIZE": 7, "MAX_SEQ_LEN": 12, "BANKS": 2,
        "QUEUE_DEPTH": 3, "TILE_K": 8, "TILE_ROWS": 1,
    }
    sources = [str(p.relative_to(ROOT)) for p in sorted(
        (ROOT / "anvil_d1_reference/rtl").glob("*.sv"))]
    experiment.execute(["iverilog", "-V"], "iverilog-version")
    experiment.execute(["iverilog", "-g2012", "-Wall", "-s", "anvil_d1_top",
                        *(item for key, value in parameters.items()
                          for item in ("-P", f"anvil_d1_top.{key}={value}")),
                        "-o", str(binary), *sources], "unchanged-parent-compile")
    run_target_model(experiment, parent=True, modes=(0,), command_sequence=(
        (1, 0, 1, 0, 0, 1), (2, 1, 0, 0, 0, 1), (3, 2, 0, 1, 0, 1),
        (4, 3, 0, 1, 0, 1)))
    if not all(observations.values()):
        raise FileNotFoundError("original parent dependencies/historical handoff missing; "
                                "see parent_prerequisites in receipt")


def result_rows(output, prefix):
    return [{key: int(value) for key, value in re.findall(r"(\w+)=(-?\d+)", line)}
            for line in output.splitlines() if line.startswith(prefix + " ")]


def run_benchmark(experiment, component, compact_probe=False):
    manifest_path = ROOT / "tests/benchmark_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if compact_probe:
        manifest["domains"] = manifest["domains"][:1]
        manifest["seeds"] = manifest["seeds"][:1]
        experiment.receipt["probe_scope"] = "one benchmark cell, not five-domain closure"
    (experiment.directory / "benchmark-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    geometry = Geometry(**manifest["geometry"])
    compiled = None
    rows = []
    for domain in manifest["domains"]:
        for seed in manifest["seeds"]:
            first, seed_token = domain["tokens"]
            child, compiled = component(
                f"domain{domain['id']}-seed{seed}",
                lambda e, d=domain, s=seed: run_target_model(
                    e, geometry, seed=s, domain=d["id"], compiled=compiled,
                    command_sequence=(
                        (first, 0, 1, 0, 0, manifest["generation_limit"]),
                        (seed_token, 1, 0, 1, 1, manifest["generation_limit"]))))
            output = child.receipt["results"]["target-model"]["raw_summary"]
            measurements = result_rows(output, "COMMAND_RESULT")
            transfers = {row["command"]: row for row in result_rows(output, "TRANSFER_RESULT")}
            counters = {row["command"]: row for row in result_rows(output, "COUNTER_RESULT")}
            if len(measurements) != 8 or len(transfers) != 8 or len(counters) != 8:
                raise AssertionError("benchmark missing command/transfer measurements")
            baseline = next(row for row in measurements if row["mode"] == 0 and row["generation"])
            expectations = child.receipt["results"]["target-fixtures"]["command_expectations"]
            base_tokens = next(row["expected"] for row in expectations
                               if row["mode"] == 0 and row["generation"])
            for row in measurements:
                row.update(transfers[row["command"]])
                row.update(counters[row["command"]])
                row.update(domain_id=domain["id"], seed=seed,
                           phase="generation" if row["generation"] else "prefill",
                           receipt=str((child.directory / "receipt.json").relative_to(ROOT)))
                if row["generation"]:
                    if row["tokens"] != manifest["generation_limit"]:
                        raise AssertionError("unmatched completed benchmark token count")
                    row["committed_tokens_per_second_at_100mhz"] = (
                        row["tokens"]*manifest["clock_hz"]/row["cycles"])
                    row["speedup_vs_d2_compatible"] = baseline["cycles"]/row["cycles"]
                    row["signed_speedup_percent"] = (
                        row["speedup_vs_d2_compatible"]-1)*100
                    actual_tokens = next(entry["expected"] for entry in expectations
                                         if entry["command"] == row["command"])
                    row["tokens_differ_from_uncompressed"] = actual_tokens != base_tokens
                    row["accepted_proposed_ratio"] = (
                        row["accepted"]/row["proposed"] if row["proposed"] else None)
                rows.append(row)
            experiment.receipt["results"]["benchmark_rows"] = rows
            experiment.save()
    if len(rows) != (8 if compact_probe else 5*3*4*2):
        raise AssertionError("five-domain/three-seed/four-mode measurement matrix incomplete")
    experiment.receipt["results"]["measurement_scope"] = (
        "accepted logical 32-bit memory transfers, including scales/refetches; "
        "simulation cycles at assumed 100MHz, not measured DDR4 bursts or physical timing; "
        "compact tails do not establish the matched full-group >=2x bandwidth requirement")
    experiment.save()
    if not compact_probe:
        run_parent_comparison(experiment)


def run_reproduction(experiment):
    destination = experiment.directory / ("clean-project-" + uuid.uuid4().hex[:8])
    destination.mkdir()
    copied = {}
    for pattern in ("rtl/*.sv", "anvil_d1_reference/rtl/*.sv", "design/*.md",
                    "fpga/quartus_gate.json", "tests/*"):
        for source in sorted(ROOT.glob(pattern)):
            if not source.is_file():
                continue
            relative = source.relative_to(ROOT)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            copied[str(relative)] = hashlib.sha256(target.read_bytes()).hexdigest()
    experiment.receipt["results"]["reproduction_input_sha256"] = copied
    experiment.save()
    # Each child resolves its root from its own script, not the original workspace.
    script = str((destination / "tests/verify.py").relative_to(ROOT))
    for probe, extra in (
            ("oracle", []), ("dequant", ["--simulator", "icarus"]),
            ("public-smoke", []), ("target-model", ["--mode", "0"]),
            ("synthesis-probe", ["--configuration", "minimum"])):
        experiment.execute(["python3", script, "--probe", probe, *extra],
                           "clean-" + probe, 1800)
    if any((destination / name).exists() for name in (".git", ".vulcan", ".tooling", "VULCAN")):
        raise AssertionError("runtime/developer metadata entered reproduction")
    receipts = sorted(destination.glob("evidence/preparation/*/receipt.json"))
    if len(receipts) != 5:
        raise AssertionError("missing clean reproduction results")
    experiment.receipt["results"]["reproduction_receipts"] = [
        str(path.relative_to(ROOT)) for path in receipts]
    for path in receipts:
        result = json.loads(path.read_text())
        if result.get("success") is not True:
            raise AssertionError("clean reproduction child did not succeed")
    experiment.save()


def run_prefix_matrix(component):
    compiled = None
    for prefix in range(5):
        _, compiled = component(
            f"native-prefix{prefix}", lambda e, p=prefix: run_target_model(
                e, modes=(1,), mtp_fixture=f"prefix{p}", compiled=compiled,
                command_sequence=((1, 0, 1, 0, 0, 5), (3, 1, 0, 1, 1, 5))))


def run_suite(experiment, suite):
    def component(stem, operation):
        child = Experiment("d2-" + suite + "-" + stem,
                           preparation=experiment.directory.parent.name == "preparation")
        path = str((child.directory / "receipt.json").relative_to(ROOT))
        experiment.receipt.setdefault("component_receipts", []).append(path)
        experiment.save()
        try:
            result = operation(child)
        except Exception as error:
            child.finish(False, str(error))
            raise
        else:
            child.finish(True)
        finally:
            child.cleanup_intermediates()
        if time.monotonic()-experiment.started_monotonic >= 2700:
            raise TimeoutError("whole-check 2700-second execution budget exhausted")
        return child, result

    if suite == "numerical":
        component("reference", lambda e: e.execute(
            ["python3", "-m", "unittest", "discover", "-s", "tests",
             "-p", "test_reference.py"], "oracle-unit-tests"))
        for simulator in ("icarus", "verilator"):
            component("dequant-" + simulator, lambda e, s=simulator: run_dequant(e, s))
        for leaf in ("quantizer", "bf16"):
            component(leaf, lambda e, kind=leaf: run_numerical_leaf(e, kind, "icarus"))
        component("fp8-service", run_service_probe)
        component("native-heads", run_head_model)
        component("routed-target", lambda e: run_target_model(
            e, Geometry(layers=2), modes=(0, 2)))
    elif suite == "behavior":
        experiment.receipt["repair"] = "implement behavior execution after argparse rejection"
        experiment.save()
        component("public-smoke", run_public_smoke)
        component("public-boundaries", lambda e: run_public_smoke(e, boundaries=True))
        component("public-interrupts", lambda e: run_public_smoke(e, interrupts=True))
        for simulator in ("icarus", "verilator"):
            component("verdict-" + simulator, lambda e, s=simulator: run_verdict_probe(e, s))
        component("nonzero-four-mode", run_target_model)
        component("routed-rejection", lambda e: run_target_model(
            e, Geometry(layers=2), modes=(1, 3), mtp_fixture="reject-first"))
        for banks, queue in ((1, 1), (2, 3), (4, 16), (8, 1)):
            component(f"scheduler-b{banks}-q{queue}",
                      lambda e, b=banks, q=queue: run_scheduler(e, b, q))
        run_prefix_matrix(component)
        for hidden in (8, 64, 2048):
            component(f"rms-h{hidden}", lambda e, h=hidden: run_rms(e, h))
        component("causal-four-lanes", run_target_lanes)
        component("medium-integrated", lambda e: run_target_model(
            e, Geometry(hidden=64, layers=2, banks=4, queue=16), modes=(0,),
            command_sequence=((1, 0, 1, 0, 0, 1), (3, 1, 0, 1, 1, 1))))
    elif suite == "defects":
        component("dequant-control", lambda e: run_dequant(e, "verilator"))
        component("service-control", run_service_probe)
        component("verdict-control", lambda e: run_verdict_probe(e, "verilator"))
        component("head-control", run_head_model)
        component("target-control", lambda e: run_target_model(
            e, Geometry(layers=2), modes=(1,), mtp_fixture="reject-first"))
        for defect in ("fp8-bias", "bf16-tie"):
            component(defect, lambda e, d=defect: run_dequant_mutant(e, d))
        for defect in ("byte-order", "scale-group", "scale-invalidation"):
            component(defect, lambda e, d=defect: run_service_mutant(e, d))
        component("mtp-alignment", run_alignment_mutant)
        component("acceptance-past-mismatch", run_acceptance_mutant)
        for defect in ("causal-mask", "rejected-kv"):
            component(defect, lambda e, d=defect: run_target_mutant(e, d))
    elif suite == "synthesis":
        for configuration in ("minimum", "compact", "production"):
            component(configuration, lambda e, config=configuration: run_synthesis_probe(e, config))
        component("parameters", run_parameter_probe)
    elif suite == "compatibility":
        parent_prerequisites(experiment)
        component("reset-compatible", run_public_smoke)
        for seed in (17, 89, 233):
            component(f"independent-d1-numerics-seed{seed}", lambda e, s=seed: run_target_model(
                e, seed=s, modes=(0,)))
        run_parent_comparison(experiment)
    elif suite == "benchmark":
        parent_prerequisites(experiment)
        run_benchmark(experiment, component)
    elif suite == "reproduce":
        run_reproduction(experiment)
    elif suite == "native-prefixes":
        run_prefix_matrix(component)
    elif suite == "benchmark-cell":
        run_benchmark(experiment, component, compact_probe=True)
    else:
        raise ValueError(f"unknown suite {suite}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--suite", choices=[
        "numerical", "behavior", "compatibility", "defects", "synthesis", "benchmark", "reproduce"])
    operation.add_argument("--probe", choices=["dequant", "quantizer", "bf16", "public-smoke",
                                         "synthesis-probe", "fp8-bias", "bf16-tie",
                                         "fp8-service", "byte-order", "scale-group",
                                         "scale-invalidation", "verdict",
                                         "acceptance-past-mismatch", "oracle", "target-model",
                                         "public-boundaries", "native-head", "mtp-alignment",
                                         "parameters", "causal-mask", "rejected-kv",
                                         "scheduler", "public-interrupts", "native-prefixes",
                                         "rms", "parent-prerequisites", "target-lanes",
                                         "benchmark-cell"])
    parser.add_argument("--simulator", choices=["icarus", "verilator"], default="icarus")
    parser.add_argument("--repair-of", help="Project-relative retained failed receipt")
    parser.add_argument("--geometry", choices=["compact", "routed", "medium"], default="compact")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--banks", type=int, choices=[1, 2, 4, 8], default=2)
    parser.add_argument("--queue", type=int, choices=[1, 3, 16], default=3)
    parser.add_argument("--hidden", type=int, choices=[8, 64, 2048], default=2048)
    parser.add_argument("--mode", type=int, action="append", choices=[0, 1, 2, 3])
    parser.add_argument("--mtp-fixture", choices=[
        "random", "reject-first", "prefix0", "prefix1", "prefix2", "prefix3", "prefix4"],
                        default="random")
    parser.add_argument("--workload", choices=["standard", "full-block"], default="standard")
    parser.add_argument("--configuration", choices=["minimum", "compact", "production"],
                        default="compact")
    args = parser.parse_args()
    experiment = Experiment("d2-" + (args.probe or args.suite), preparation=bool(args.probe))
    if args.repair_of:
        prior = Path(args.repair_of)
        if prior.is_absolute() or ".." in prior.parts or not (ROOT / prior).is_file():
            raise ValueError("--repair-of must name an existing project-relative receipt")
        experiment.receipt["repair_of"] = str(prior)
        experiment.save()
    try:
        experiment.execute(["python3", "--version"], "python-version")
        if args.suite:
            run_suite(experiment, args.suite)
        elif args.probe == "dequant":
            run_dequant(experiment, args.simulator)
        elif args.probe == "public-smoke":
            run_public_smoke(experiment)
        elif args.probe == "public-boundaries":
            run_public_smoke(experiment, boundaries=True)
        elif args.probe == "public-interrupts":
            run_public_smoke(experiment, interrupts=True)
        elif args.probe == "native-prefixes":
            run_suite(experiment, "native-prefixes")
        elif args.probe == "benchmark-cell":
            run_suite(experiment, "benchmark-cell")
        elif args.probe == "target-model":
            geometry = (Geometry(layers=2) if args.geometry == "routed" else
                        Geometry(hidden=64, layers=2) if args.geometry == "medium" else Geometry())
            run_target_model(experiment, geometry, seed=args.seed,
                             modes=tuple(args.mode) if args.mode is not None else (0, 1, 2, 3),
                             mtp_fixture=args.mtp_fixture,
                             command_sequence=(
                                 (1, 0, 1, 0, 0, 5), (3, 1, 0, 1, 1, 5)
                             ) if args.workload == "full-block" else None)
        elif args.probe == "native-head":
            run_head_model(experiment)
        elif args.probe == "mtp-alignment":
            run_alignment_mutant(experiment)
        elif args.probe == "parameters":
            run_parameter_probe(experiment)
        elif args.probe == "scheduler":
            run_scheduler(experiment, args.banks, args.queue)
        elif args.probe == "rms":
            run_rms(experiment, args.hidden, args.simulator)
        elif args.probe == "target-lanes":
            run_target_lanes(experiment)
        elif args.probe == "parent-prerequisites":
            run_parent_comparison(experiment)
        elif args.probe in ("causal-mask", "rejected-kv"):
            run_target_mutant(experiment, args.probe)
        elif args.probe == "synthesis-probe":
            run_synthesis_probe(experiment, args.configuration)
        elif args.probe in ("fp8-bias", "bf16-tie"):
            run_dequant_mutant(experiment, args.probe)
        elif args.probe == "fp8-service":
            run_service_probe(experiment)
        elif args.probe in ("byte-order", "scale-group", "scale-invalidation"):
            run_service_mutant(experiment, args.probe)
        elif args.probe == "verdict":
            run_verdict_probe(experiment, args.simulator)
        elif args.probe == "acceptance-past-mismatch":
            run_acceptance_mutant(experiment)
        elif args.probe == "oracle":
            experiment.execute(["python3", "-m", "unittest", "discover", "-s", "tests",
                                "-p", "test_reference.py"], "oracle-unit-tests")
        else:
            run_numerical_leaf(experiment, args.probe, args.simulator)
    except Exception as error:
        experiment.finish(False, str(error))
        raise
    finally:
        experiment.cleanup_intermediates()
    experiment.finish(True)


if __name__ == "__main__":
    main()
