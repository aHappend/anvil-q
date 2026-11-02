#!/usr/bin/env python3
"""Bounded original/lowered configuration regression; no production synthesis."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from synthesis import expand_packages, flatten_configuration


def execute(run, root, source_paths):
    controls = 0
    for path in source_paths:
        if path.name not in ("anvil_q2_ht_configuration.sv",
                             "anvil_q2_ht2_native_configuration.sv"):
            continue
        original = path.read_text()
        read_index = "shadow_read_address" if "ht2_native" in path.name else "index"
        lowered = flatten_configuration(original, path.name)
        expected = original.replace(
            "reg [15:0] initialized [0:ENTRIES-1];",
            "reg [16*ENTRIES-1:0] initialized;").replace(
            "initialized[cfg_index][cfg_addr[5:2]]",
            "initialized[{cfg_index,cfg_addr[5:2]}]").replace(
            f"initialized[{read_index}]",
            "initialized[{" + read_index + ",4'b0000}+:16]")
        reset = ("for (i=0;i<ENTRIES;i=i+1) initialized[i]<=0;" if "ht2_native" in path.name
                 else "for (i=0; i<ENTRIES; i=i+1) initialized[i]<=0;")
        expected = expected.replace(reset, "initialized<=0;")
        if lowered != expected:
            raise AssertionError(f"lowering changed unrelated configuration logic: {path.name}")
        for broken in (
            original.replace(f"initialized[{read_index}]", "initialized[unsupported]"),
            original.replace("initialized[cfg_index][cfg_addr[5:2]]",
                             "initialized[cfg_index][unsupported]"),
            original.replace(reset, "initialized[0]<=0;"),
            original + "\nwire [15:0] unsupported_mask=initialized[unsupported];\n",
        ):
            try:
                flatten_configuration(broken, path.name)
            except RuntimeError:
                controls += 1
            else:
                raise AssertionError(f"unsupported configuration syntax accepted: {path.name}")
    if controls != 8:
        raise AssertionError("both configuration lowering controls must execute")
    lowered_paths = expand_packages(run, root, source_paths)
    run.tool("iverilog")
    run.tool("vvp")
    results = []
    for snapshot, paths in (("original", source_paths), ("lowered", lowered_paths)):
        for native in (0, 1):
            stem = f"configuration-{snapshot}-native{native}"
            binary = run.path / (stem + ".vvp")
            run.command(
                ["iverilog", "-g2012", "-Wall", "-s", "synthesis_configuration_tb",
                 "-Psynthesis_configuration_tb.NATIVE=" + str(native),
                 "-o", run.relative(binary), *[run.relative(p) for p in paths],
                 run.relative(root / "tests/synthesis_configuration_tb.sv")],
                stem + "-compile")
            _, stdout, _ = run.command(
                ["vvp", run.relative(binary)], stem + "-simulate", timeout=600)
            if f"SUMMARY lowering native={native} compared=1540 " not in stdout:
                raise AssertionError(f"{stem}: missing executed readback comparisons")
            results.append({"snapshot": snapshot, "native": bool(native),
                            "summary": stdout.strip()})
            binary.unlink()
    run.receipt["configuration_lowering_regression"] = {
        "unsupported_syntax_rejections": controls, "runs": results,
        "scope": ("compact public CSR word/mask readback and reset/stall behavior; "
                  "not complete configuration equivalence, synthesis or physical signoff"),
    }
    run.save()
    return lowered_paths


def main():
    from verify import ROOT, Run, sources
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run = Run("configuration-lowering", preparation=True, repair_of=args.repair_of)
    run.receipt["argv"] = ["python3", "tests/synthesis_checks.py", *sys.argv[1:]]
    run.save()
    try:
        run.tool("python3")
        execute(run, ROOT, sources())
    except Exception as exc:
        return run.finish(False, f"{type(exc).__name__}: {exc}")
    return run.finish(True, "configuration lowering regression passed")


if __name__ == "__main__":
    sys.exit(main())
