"""Disposable RTL mutations rejected by unchanged public-interface oracles."""

import hashlib
import json

from execution import ROOT, relative
from portability import copy_sources


MUTATIONS = (
    ("rounding", "rtl/anvil_q3_fp_00_pkg.sv",
     "{24'd0,(work[2] && (work[1] || work[0] || work[3]))};\n      if (rounded[24])",
     "{24'd0,(work[2] && (work[1] || work[0]))};\n      if (rounded[24])",
     ["--probe", "primitives"], "IEEE "),
    ("lane-mask", "rtl/anvil_q3_fp_dot8.sv",
     "lane_mask[lane] ? activation16[lane*16+:16] : 16'd0",
     "activation16[lane*16+:16]",
     ["--probe", "dots"], "DOT "),
    ("awq-permutation", "rtl/anvil_q3_fp_00_pkg.sv",
     "3'd1: awq_lane_shift = 5'd16;", "3'd1: awq_lane_shift = 5'd4;",
     ["--probe", "tensor", "--banks", "2"], "TENSOR row="),
    ("cache-metadata", "rtl/anvil_q3_fp_cache_codec.sv",
     "metadata<={8'd0,2'(CACHE_MODE),1'(CACHE_MODE==1 && MODE1_FP8!=0),fp16,4'd0,shared_exp};",
     "metadata<={8'd1,2'(CACHE_MODE),1'(CACHE_MODE==1 && MODE1_FP8!=0),fp16,4'd0,shared_exp};",
     ["--probe", "cache"], "CACHE cmd="),
    ("gqa-head", "rtl/anvil_q3_fp_gqa_attention.sv",
     ".cmd_head(head>>3)", ".cmd_head(head>>4)",
     ["--probe", "top", "--heads", "16", "--tokens", "1"], "SCRATCH/CACHE "),
    ("scheduler-association", "anvil_q3_reference/rtl/anvil_q3_bank_scheduler.sv",
     "tag[INDEX]==mem_rsp_tag[b*64+:64]",
     "tag[INDEX]==(mem_rsp_tag[b*64+:64]^64'd1)",
     ["--probe", "scheduler", "--banks", "2", "--queue-depth", "3"], "ASSOCIATION "),
)


def check(evidence, seed, selected=None):
    results = []
    real_sources = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for folder in ("rtl", "anvil_q3_reference/rtl") for path in (ROOT / folder).glob("*.sv")}
    for name, filename, old, new, argv, diagnostic in MUTATIONS:
        if selected and name not in selected:
            continue
        directory = evidence.path / f"mutant-{name}"
        copied = copy_sources(directory)
        target = directory / filename
        text = target.read_text()
        if text.count(old) != 1:
            raise AssertionError(f"Mutation {name} has no unique source witness")
        target.write_text(text.replace(old, new))
        mutated_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        if mutated_hash == copied[filename]:
            raise AssertionError(f"Mutation {name} left source unchanged")
        for source, digest in copied.items():
            if source != filename and hashlib.sha256((directory / source).read_bytes()).hexdigest() != digest:
                raise AssertionError(f"Mutation changed unintended source: {source}")
        print(f"MUTATION {name}", flush=True)
        output = evidence.run(["python3", "tests/verify.py", *argv, "--simulator", "verilator",
                               "--seed", str(seed)], cwd=directory, expect_failure=True)
        receipts = list((directory / "evidence" / "preparation").glob("*/receipt.json"))
        if len(receipts) != 1:
            raise AssertionError(f"Missing unique mutant execution receipt: {name}")
        receipt = json.loads(receipts[0].read_text())
        commands = receipt.get("commands", [])
        if receipt.get("status") != "failed" or not commands:
            raise AssertionError(f"Mutation did not reach independent checker: {name}")
        failing = commands[-1]
        if (failing.get("timed_out") or failing.get("exit_code", 0) == 0 or
                failing["argv"][0] in ("verilator", "iverilog", "yosys") or
                not any(command["argv"][0] == "verilator" and command.get("exit_code") == 0
                        for command in commands)):
            raise AssertionError(f"Tool/compile/progress failure is not a mutation kill: {name}")
        mismatch = directory / failing["stdout"]
        messages = [line for line in mismatch.read_text().splitlines() if diagnostic in line]
        if not messages:
            raise AssertionError(f"Mutation did not reach its intended observable mismatch: {name}")
        results.append({"mutation": name, "source": filename, "original_sha256": copied[filename],
                        "mutated_sha256": mutated_hash, "diagnostic": messages[0],
                        "receipt": relative(receipts[0]), "stdout": relative(output)})
    for filename, digest in real_sources.items():
        if hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() != digest:
            raise AssertionError(f"Real RTL changed during mutation execution: {filename}")
    if not results or (selected is None and len(results) != 6):
        raise AssertionError("Missing intended observable mutation kills")
    return results
