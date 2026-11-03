"""Disposable source mutations with structured, real comparison failures."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import ROOT, execute, new_run, relative, source_hashes
from numerics import vectors


def protocol_mutants(preparation=False, categories=None, repair_of=None):
    from attention import matrix_vectors
    from cache_write import fixture as cache_fixture
    from native_model import Fixture, descriptor
    from tensor import vectors as tensor_vectors

    directory = new_run("protocol-defects", preparation)
    fp = ("anvil_q4_00_fp_pkg.sv", "anvil_q4_fp32.sv")
    cache_sources = (*fp, "anvil_q4_fp_mem_port.sv", "anvil_q4_fp_kv_cache.sv")
    cases = (
        ("gqa-mapping", "attention_matrix_tb",
         (*fp, "anvil_q4_fp_mem_port.sv", "anvil_q4_fp_umul64.sv",
          "anvil_q4_fp_exp.sv", "anvil_q4_fp_gqa_attention.sv"),
         ("-GCASES=2",), "anvil_q4_fp_gqa_attention.sv",
         "if (ratio_index+1<ratio) ratio_index<=ratio_index+1'b1;",
         "if (1'b0) ratio_index<=ratio_index+1'b1;", "gqa-mapping"),
        ("inactive-mask", "tensor_tb", (*fp, "anvil_q4_fp_tensor_array.sv"),
         ("-GLANES=3", "-GTILE_K=3"), "anvil_q4_fp_tensor_array.sv",
         "length<=cmd_length; index<=0; mask<=cmd_mask;",
         "length<=cmd_length; index<=0; mask<={SL{1'b1}};", "inactive-mask"),
        ("cache-packing", "cache_write_tb", cache_sources, (),
         "anvil_q4_fp_kv_cache.sv",
         "{global_index[1:0],3'd0}", "{(global_index[1:0]^2'b01),3'd0}",
         "cache-packing-page"),
        ("page-addressing", "cache_write_tb", cache_sources, (),
         "anvil_q4_fp_kv_cache.sv",
         "physical_row<=({1'b0,rdata[30:0]}<<page_shift) | (position & (page_size-1));",
         "physical_row<=({1'b0,rdata[30:0]}<<page_shift);", "cache-packing-page"),
        ("response-tag-ownership", "anvil_q4_fp_bank_scheduler",
         ("anvil_q4_fp_bank_scheduler.sv",), ("-GBANKS=16", "-GQUEUE_DEPTH=3"),
         "anvil_q4_fp_bank_scheduler.sv",
         "slot_owner[q] <= selected_client[1];",
         "slot_owner[q] <= selected_client[1] ^ 5'd1;", "response-ownership"),
        ("speculative-rollback", "speculative_tb", ("anvil_q4_fp_speculative.sv",), (),
         "anvil_q4_fp_speculative.sv",
         "accepted<=2; next_prediction<=target_argmax; state<=RESPONSE;",
         "accepted<=1; next_prediction<=target_argmax; state<=RESPONSE;", "speculation"),
        ("speculative-commit", "speculative_tb", ("anvil_q4_fp_speculative.sv",), (),
         "anvil_q4_fp_speculative.sv",
         "assign commit_valid=verify_valid && verify_ready && !failed && !faulted && !abort;",
         "assign commit_valid=verify_valid && !failed && !faulted && !abort;",
         "speculation-commit"),
        ("native-quantization-bypass", "anvil_q4_fp_top",
         tuple(path.name for path in sorted((ROOT / "rtl").glob("*.sv"))),
         ("-GBANKS=1", "-GQUEUE_DEPTH=1", "-GTILE_ROWS=3", "-GTILE_K=3"),
         "anvil_q4_fp_gemv.sv", "load_data<=rdata;",
         "load_data<=rdata[30:23]<8'd127 ? {rdata[31],31'd0} : "
         "rdata[30:23]<8'd150 ? "
         "(rdata & (32'hffffffff << (8'd150-rdata[30:23]))) : rdata;",
         "native-stage-write"),
    )
    selected = [case for case in cases if categories is None or case[0] in categories]
    if not selected or (categories and set(categories) != {case[0] for case in selected}):
        raise ValueError(f"Unknown or empty mutation selection: {categories}")
    records = []
    for label, top, names, parameters, target, original, replacement, kind in selected:
        image = directory / f"{label}-vectors.txt"
        fixture_args = []
        if label == "gqa-mapping":
            matrix_vectors(image, (2, 4))
            fixture_args = [f"+image={relative(image)}"]
        elif label == "inactive-mask":
            tensor_vectors(image, lanes=3, tile_k=3)
            fixture_args = [f"+vectors={relative(image)}"]
        elif label in ("cache-packing", "page-addressing"):
            cache_fixture(image)
            fixture_args = [f"+vectors={relative(image)}"]
        elif label == "native-quantization-bypass":
            image = Fixture(descriptor(banks=1, dimension=2, intermediate=3,
                                       vocabulary=3, context=3), tokens=1).export(directory)
        for variant in ("clean", "mutated"):
            stem = f"{label}-{variant}"
            child = directory / f"{stem}-sources"
            child.mkdir()
            inputs = []
            for name in names:
                text = (ROOT / "rtl" / name).read_text()
                if variant == "mutated" and name == target:
                    if text.count(original) != 1:
                        raise AssertionError(f"Mutation anchor is not unique: {label}")
                    text = text.replace(original, replacement, 1)
                copy = child / name
                copy.write_text(text)
                inputs.append(relative(copy))
            obj = child / "compile-obj"
            mismatch = child / "mismatch.json"
            try:
                if label in ("response-tag-ownership", "native-quantization-bypass"):
                    cpp = ("scheduler_sim.cpp" if label == "response-tag-ownership"
                           else "native_sim.cpp")
                    banks = 16 if label == "response-tag-ownership" else 1
                    command = [
                        "verilator", "--cc", "--exe", "--build", "-Wno-fatal",
                        "-j", "2", "--top-module", top, "--Mdir", relative(obj),
                        *parameters, "-CFLAGS", f"-std=c++17 -DBANKS={banks}",
                        *inputs, os.path.relpath(ROOT / "tests" / cpp, obj)]
                else:
                    command = [
                        "verilator", "--binary", "--timing", "-Wno-fatal",
                        "-j", "2", "--top-module", top, "--Mdir", relative(obj),
                        *parameters, *inputs, f"tests/{top}.sv"]
                execute(directory / f"{stem}-compile", command, timeout=600)
                if label == "response-tag-ownership":
                    args = [relative(mismatch)]
                elif label == "native-quantization-bypass":
                    args = [relative(image), relative(child / "observed.json"),
                            relative(mismatch)]
                else:
                    args = [*fixture_args, f"+mismatch={relative(mismatch)}"]
                execute(directory / f"{stem}-simulation", [
                    relative(obj / f"V{top}"), *args], timeout=300,
                    expect_failure=variant == "mutated",
                    extra_inputs=[*inputs, image], repair_of=repair_of)
                record = {
                    "category": label, "variant": variant,
                    "receipt": relative(directory / f"{stem}-simulation/receipt.json"),
                }
                if variant == "mutated":
                    comparison = json.loads(mismatch.read_text())
                    changed = comparison["expected"] != comparison["observed"]
                    if "expected_flags" in comparison:
                        changed |= comparison["expected_flags"] != comparison["observed_flags"]
                    if "expected_error" in comparison:
                        changed |= comparison["expected_error"] != comparison["observed_error"]
                    if comparison["kind"] != kind or comparison["valid"] != 1 or not changed:
                        raise AssertionError(f"No actual comparison rejected mutation: {label}")
                    record["comparison"] = comparison
                records.append(record)
            finally:
                if obj.exists():
                    shutil.rmtree(obj)
    (directory / "observed.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "protocol_mutants": records,
        "categories": [case[0] for case in selected]}, indent=2) + "\n")
    print(f"Protocol defect receipts: {relative(directory)}", flush=True)
    return directory


def numerical_mutants(preparation=False):
    directory = new_run("numerical-defects", preparation)
    fixture = directory / "fp32-vectors.txt"
    vectors(fixture, compact=True)
    mutants = (
        ("clean", None, None, None),
        ("rounding", "anvil_q4_00_fp_pkg.sv",
         "increment = extended[2] && (extended[1] || extended[0] || extended[3]);",
         "increment = 1'b0;"),
        ("fp-flags", "anvil_q4_fp32.sv",
         "assign flags = out_valid ? result_register[36:32] : 5'd0;",
         "assign flags = 5'd0;"),
    )
    records = []
    for label, target, original, replacement in mutants:
        child = directory / f"{label}-sources"
        child.mkdir()
        inputs = []
        for name in ("anvil_q4_00_fp_pkg.sv", "anvil_q4_fp32.sv"):
            text = (ROOT / "rtl" / name).read_text()
            if name == target:
                if original not in text:
                    raise AssertionError(f"Mutation anchor absent: {label}")
                text = text.replace(original, replacement, 1)
            copy = child / name
            copy.write_text(text)
            inputs.append(relative(copy))
        obj = child / "compile-obj"
        try:
            execute(directory / f"{label}-compile", [
                "verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                "--top-module", "fp32_tb", "--Mdir", relative(obj),
                *inputs, "tests/fp32_tb.sv"])
            mismatch = child / "mismatch.json"
            receipt = execute(directory / f"{label}-simulation", [
                relative(obj / "Vfp32_tb"), f"+vectors={relative(fixture)}",
                f"+mismatch={relative(mismatch)}"], expect_failure=label != "clean",
                extra_inputs=[ROOT / name for name in inputs])
            record = {"mutant": label,
                      "receipt": relative(directory / f"{label}-simulation/receipt.json")}
            if label != "clean":
                comparison = json.loads(mismatch.read_text())
                # A nonzero child exit, text match, timeout or compiler error
                # alone cannot establish defect sensitivity.
                if (comparison["kind"] != "ieee" or comparison["valid"] != 1 or
                    (comparison["expected"] == comparison["observed"] and
                     comparison["expected_flags"] == comparison["observed_flags"])):
                    raise AssertionError(f"Not an executed numerical mismatch: {label}")
                record["comparison"] = comparison
            records.append(record)
        finally:
            if obj.exists():
                shutil.rmtree(obj)
    (directory / "observed.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "numerical_mutants": records,
        "scope": "rounding and FP-flags only"}, indent=2) + "\n")
    print(f"Numerical defect receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--protocol", action="store_true")
    parser.add_argument("--category", action="append")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    if args.protocol or args.category:
        protocol_mutants(args.preparation, args.category, args.repair_of)
    else:
        numerical_mutants(args.preparation)
