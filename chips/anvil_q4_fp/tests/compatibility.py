"""Original-parent differential execution; never a native numerical oracle."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import ROOT, execute, new_run, relative, source_hashes


def legacy_words(mode):
    dimension, ratio = 8, 8 if mode == 3 else 1
    hidden = dimension * ratio
    return [1, mode, 1, 0 if mode == 4 else 1, 0, 0, 8, 1, hidden, 8,
            ratio, 1, dimension, 3, 4, 1, 1, 0x49742400, 0x358637bd,
            1, 4, 0 if mode == 4 else 1, ratio, 0, 0 if mode == 4 else 1] + [0]*7


def run(preparation=False, modes=(1, 2, 3, 4)):
    directory = new_run("compatibility", preparation)
    objects = {}
    records = []
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
                "-CFLAGS", flags,
                *[relative(path) for path in sorted(source_directory.glob("*.sv"))],
                os.path.relpath(ROOT / "tests/compatibility_sim.cpp", obj)], timeout=1800)
        for mode in modes:
            fixture = directory / f"descriptor-mode-{mode}.txt"
            fixture.write_text(" ".join(f"{word:x}" for word in legacy_words(mode)) + "\n")
            observed = {}
            for label, top in (("parent", "anvil_q4_top"), ("integrated", "anvil_q4_fp_top")):
                output = directory / f"{label}-mode-{mode}.json"
                execute(directory / f"{label}-mode-{mode}", [
                    relative(objects[label] / f"V{top}"), relative(fixture),
                    relative(output)], timeout=1800, extra_inputs=[fixture])
                observed[label] = json.loads(output.read_text())
            for quantity in ("reads", "writes", "logits", "done", "errors", "transactions"):
                if observed["parent"][quantity] != observed["integrated"][quantity]:
                    raise AssertionError(f"Legacy differential mismatch: mode={mode} {quantity}")
            records.append({"mode": mode, "tokens": 2, "token_phase_transition": True,
                            "independent_expectation": "zero LM-head yields exact zero logits",
                            "parent_cycles": observed["parent"]["cycles"],
                            "integrated_cycles": observed["integrated"]["cycles"],
                            "transactions": observed["parent"]["reads"] +
                                            observed["parent"]["writes"]})
    finally:
        for obj in objects.values():
            if obj.exists():
                shutil.rmtree(obj)
    (directory / "observed.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "synthetic": True,
        "cases": records, "comparison": "exact per-bank tuple/value order; opaque tags checked locally",
    }, indent=2) + "\n")
    print(f"Compatibility receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--mode", type=int, choices=(1, 2, 3, 4))
    args = parser.parse_args()
    run(args.preparation, (args.mode,) if args.mode else (1, 2, 3, 4))
