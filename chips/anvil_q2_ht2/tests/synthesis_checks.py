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
        native = "ht2_native" in path.name
        reset = ("initialized[entry]<=0;" if native else
                 "for (i=0; i<ENTRIES; i=i+1) initialized[i]<=0;")
        if native:
            expected = expected.replace(reset, "initialized[16*entry+:16]<=0;").replace(
                "          initialized[entry][cfg_addr[5:2]]<=1;",
                "          for (integer initialized_word=0;initialized_word<16;\n"
                "               initialized_word=initialized_word+1)\n"
                "            if (cfg_addr[5:2]==initialized_word)\n"
                "              initialized[16*entry+initialized_word]<=1;")
            write_access = "initialized[entry][cfg_addr[5:2]]"
        else:
            expected = expected.replace(reset, "initialized<=0;")
            write_access = "initialized[cfg_index][cfg_addr[5:2]]"
        if lowered != expected:
            raise AssertionError(f"lowering changed unrelated configuration logic: {path.name}")
        for broken in (
            original.replace(f"initialized[{read_index}]", "initialized[unsupported]"),
            original.replace(write_access, "initialized[unsupported][cfg_addr[5:2]]"),
            original.replace(reset, "initialized[0]<=0;"),
            original + "\nwire [15:0] unsupported_mask=initialized[unsupported];\n",
        ):
            try:
                flatten_configuration(broken, path.name)
            except RuntimeError:
                controls += 1
            else:
                raise AssertionError(f"unsupported configuration syntax accepted: {path.name}")
        if native:
            for old, new in (
                ("else if (initialized_write && cfg_index==entry)",
                 "else if (initialized_write)"),
                ("always @(posedge clk or negedge rst_n)", "always @(posedge clk)"),
                ("entry<ENTRIES", "entry<=ENTRIES"),
                ("shadow_read_mask<=initialized[shadow_read_address];",
                 "shadow_read_mask<=initialized[cfg_index];"),
            ):
                if old not in original:
                    raise AssertionError(f"negative control did not mutate source: {old}")
                try:
                    flatten_configuration(original.replace(old, new), path.name)
                except RuntimeError:
                    controls += 1
                else:
                    raise AssertionError(f"unsupported native validity syntax accepted: {old}")
    if controls != 12:
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
    defects = []
    native_path = next(p for p in lowered_paths
                       if p.name == "anvil_q2_ht2_native_configuration.sv")
    native_text = native_path.read_text()
    for name, old, new in (
        ("reset-mask", "initialized[16*entry+:16]<=0;",
         "initialized[16*entry+:16]<=16'hffff;"),
        ("word-bit-order", "initialized[16*entry+initialized_word]",
         "initialized[16*entry+(15-initialized_word)]"),
        ("write-enable", "initialized_write && cfg_index==entry",
         "!initialized_write && cfg_index==entry"),
    ):
        if native_text.count(old) != 1:
            raise AssertionError(f"defect control did not uniquely match: {name}")
        directory = run.path / ("configuration-defect-" + name)
        directory.mkdir()
        mutated = directory / native_path.name
        mutated.write_text(native_text.replace(old, new))
        paths = [mutated if p == native_path else p for p in lowered_paths]
        binary = directory / "configuration.vvp"
        run.command(
            ["iverilog", "-g2012", "-Wall", "-s", "synthesis_configuration_tb",
             "-Psynthesis_configuration_tb.NATIVE=1",
             "-o", run.relative(binary), *[run.relative(p) for p in paths],
             run.relative(root / "tests/synthesis_configuration_tb.sv")],
            "configuration-defect-" + name + "-compile")
        record, stdout, stderr = run.command(
            ["vvp", run.relative(binary)], "configuration-defect-" + name + "-simulate",
            timeout=600, check=False)
        binary.unlink()
        if (record["exit_code"] == 0 or record["timed_out"] or
                "LOWERING_READBACK" not in stdout + stderr):
            raise AssertionError(f"configuration defect escaped intended readback check: {name}")
        defects.append({"defect": name, "assertion": "LOWERING_READBACK",
                        "exit_code": record["exit_code"]})
    run.receipt["configuration_lowering_regression"] = {
        "unsupported_syntax_rejections": controls, "runs": results,
        "executed_defect_controls": defects,
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
