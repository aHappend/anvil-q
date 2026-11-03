"""Original-parent differential execution; never a native numerical oracle."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import ROOT, execute, new_run, relative, source_hashes


def legacy_words(mode, ratio=None, cache=0, dimension=8):
    ratio = (8 if mode == 3 else 1) if ratio is None else ratio
    hidden = dimension * ratio
    block = (0 if mode==4 else 1 if cache==0 else
             2 if mode==2 else 32 if cache==1 else 64)
    return [1, mode, 1, 0 if mode == 4 else 1, 0, cache, 8, 1, hidden, 8,
            ratio, 1, dimension, 3, 4, 1, 1, 0x49742400, 0x358637bd,
            1, 4, 0 if mode == 4 else 1, ratio, 0, block] + [0]*7


def run(preparation=False, modes=(1, 2, 3, 4), repair_of=None, variants_only=False):
    directory = new_run("compatibility", preparation)
    objects = {}
    records = []
    configurations = ([] if variants_only else
                      [(f"mode-{mode}", mode, legacy_words(mode)) for mode in modes])
    for mode, ratio, cache, dimension in (
            (2, 3, 1, 8), (2, 6, 0, 8), (2, 7, 1, 8),
            (3, 8, 1, 2), (3, 8, 2, 2), (3, 8, 3, 2), (4, 3, 1, 2)):
        if mode in modes:
            configurations.append((f"mode-{mode}-ratio-{ratio}-cache-{cache}", mode,
                                   legacy_words(mode, ratio, cache, dimension)))
    if not configurations:
        raise ValueError("Selected modes have no requested compatibility configurations")
    try:
        for label, top, source_directory in (
                ("parent", "anvil_q4_top", ROOT / "anvil_q4_reference/rtl"),
                ("integrated", "anvil_q4_fp_top", ROOT / "rtl")):
            obj = directory / f"{label}-compile-obj"
            objects[label] = obj
            flags = "-std=c++17" + (" -DREFERENCE" if label == "parent" else "")
            execute(directory / f"{label}-compile", [
                "verilator", "--cc", "--exe", "--build", "-Wno-fatal", "-j", "2",
                "--top-module", top, "--Mdir", relative(obj),
                "-MAKEFLAGS", "OPT_FAST=-O3",
                "-CFLAGS", flags,
                *[relative(path) for path in sorted(source_directory.glob("*.sv"))],
                "tests/arithmetic_observer.sv",
                os.path.relpath(ROOT / "tests/compatibility_sim.cpp", obj)], timeout=1800)
        for configuration_label, mode, words in configurations:
            token_count = 2 if configuration_label==f"mode-{mode}" else 1
            fixture = directory / f"descriptor-{configuration_label}.txt"
            fixture.write_text(" ".join(f"{word:x}" for word in words) + "\n")
            observed = {}
            for label, top in (("parent", "anvil_q4_top"), ("integrated", "anvil_q4_fp_top")):
                output = directory / f"{label}-{configuration_label}.json"
                execute(directory / f"{label}-{configuration_label}", [
                    relative(objects[label] / f"V{top}"), relative(fixture),
                    relative(output), str(token_count)], timeout=1800, extra_inputs=[fixture],
                    repair_of=repair_of)
                observed[label] = json.loads(output.read_text())
            for quantity in ("reads", "writes", "logits", "done", "errors", "transactions",
                             "verified_drafts", "invalid_descriptors", "cancellations",
                             "malformed_tokens"):
                if observed["parent"][quantity] != observed["integrated"][quantity]:
                    raise AssertionError(f"Legacy differential mismatch: mode={mode} {quantity}")
            cache_reads = sum(transaction[0]==0 and transaction[1] in (12, 13)
                              for bank in observed["parent"]["transactions"] for transaction in bank)
            cache_writes = sum(transaction[0]==1 and transaction[1] in (12, 13)
                               for bank in observed["parent"]["transactions"] for transaction in bank)
            if words[5] and (not cache_reads or not cache_writes):
                raise AssertionError(f"Compressed cache traffic not observed: {configuration_label}")
            records.append({"mode": mode, "gqa_ratio": words[22], "cache_encoding": words[5],
                            "tokens": token_count, "token_phase_transition": token_count==2,
                            "compared_compressed_cache_reads": cache_reads,
                            "compared_compressed_cache_writes": cache_writes,
                            "independent_expectation": (
                                "distinct zero LM-head yields zero" if mode == 4 else
                                "tied constant FP16(0.5); final Q16 norm rounds to 1; "
                                "each logit is hidden*32768"),
                            "parent_cycles": observed["parent"]["cycles"],
                            "integrated_cycles": observed["integrated"]["cycles"],
                            "transactions": observed["parent"]["reads"] +
                                            observed["parent"]["writes"]})
            if configuration_label == "mode-4":
                parent_profile = observed["parent"]["normal_profile"]
    finally:
        for obj in objects.values():
            if obj.exists():
                shutil.rmtree(obj)
    (directory / "observed.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "synthetic": True,
        "cases": records, "comparison": "exact per-bank tuple/value order; opaque tags checked locally",
    }, indent=2) + "\n")
    if 4 in modes and not variants_only:
        profile(directory, parent_profile)
    print(f"Compatibility receipts: {relative(directory)}", flush=True)
    return directory


def profile(directory, parent_profile):
    from behavior import build
    from native_model import Fixture, descriptor

    records = []
    obj = directory / "profile-compile-obj"
    try:
        binary = build(directory / "native-profile", obj, 16, 16, 128, 3)
        for cache in (0, 2):
            case = directory / "checkpoint-images" / f"profile-cache-{cache}"
            case.mkdir(parents=True)
            words = descriptor(banks=8, element=1, cache=cache, dimension=8,
                               intermediate=8, vocabulary=3, context=4, page_tokens=1)
            words[17] = 0x49742400
            image = Fixture(words, tokens=[1, 1], constant_profile=True).export(case)
            observed = case / "observed.json"
            execute(directory / f"profile-cache-{cache}", [
                relative(binary), relative(image), relative(observed), "--profile"],
                timeout=600)
            native = json.loads(observed.read_text())
            if not native["arithmetic_operations"] or not parent_profile["arithmetic_operations"]:
                raise AssertionError("Profile requires actual arithmetic issue observations")
            records.append({"native_cache_format": cache, "native": native,
                            "parent_lossless": parent_profile})
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    (directory / "profile.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "synthetic": True,
        "workload": {"layers": 1, "hidden": 8, "intermediate": 8, "query_heads": 1,
                     "kv_heads": 1, "head_dim": 8, "vocabulary": 3, "tokens": [1, 1],
                     "weights": "all zero", "embedding": "all 0.5",
                     "gamma": "all 1.0", "bias": "all zero", "rope": "identity",
                     "element_format": "FP16", "parent_mode": 4,
                     "service": "bank-ready (cycle+3*bank)%11>=3; FIFO reply delay "
                                "1+(bank+row+col)%5; logit-ready cycle%13>=4"},
        "scope": "measured zero-weight synthetic traffic profile, not checkpoint performance "
                 "or a trained-weight quality comparison; parent cache is lossless BF16",
        "arithmetic_counter_definition": "all accepted FP32 leaf operations, including "
                  "conversions; flight cycles sum public accepted-to-retired ownership "
                  "over those leaves; tensor counters are additionally reported separately",
        "cases": records}, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--mode", type=int, choices=(1, 2, 3, 4), action="append")
    parser.add_argument("--repair-of")
    parser.add_argument("--variants-only", action="store_true")
    args = parser.parse_args()
    run(args.preparation, tuple(args.mode) if args.mode else (1, 2, 3, 4),
        args.repair_of, args.variants_only)
