#!/usr/bin/env python3
"""Portable independent L1 verification.

Reproduce: python3 tests/verify.py --suite behavior
Suites: behavior, numerics, defects, synthesis, benchmark, delivery.
With no --suite all six are executed, each with its own 2700-second deadline.
Only declared deliverables are copied for isolated reproduction. Native timing
and physical-board gates belong to the shared runtime, not this L1 verifier.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, SuiteDeadline, run_mx, run_scalar
import fp2_attention_probe as attention
import fp2_benchmark_probe as benchmark
import fp2_configuration_probe as configuration
import fp2_controller_probe as controller
import fp2_epilogue_probe as epilogue
import fp2_format_probe as formats
import fp2_graph_probe as graph
import fp2_gemv_probe as gemv
import fp2_mutations as mutations
import fp2_parent_probe as parent
import fp2_prefetch_probe as prefetch
import fp2_protocol_probe as protocol
import fp2_synthesis_probe as synthesis
import fp2_telemetry_probe as telemetry
import fp2_tensor_probe as tensor
import fp2_top_probe as top


SUITES = ("behavior", "numerics", "defects", "synthesis", "benchmark", "delivery")
INPUTS = ("rtl/*.sv", "design/*.md", "fpga/*", "anvil_q2_fp_reference/rtl/*.sv", "tests/*.py")
SEEDS = (17, 89, 203)
COMMANDS = ((3, 0, 1, 0), (5, 1, 0, 0), (7, 2, 0, 1),
            (4, 0, 1, 0), (8, 1, 0, 1))


class Suite:
    def __init__(self, name, preparation=False):
        self.probe = Probe(name, preparation=preparation)
        self.probe.summary["suite"] = name
        self.probe.summary["runs"] = []
        self.probe.receipt["aggregate_deadline_s"] = 2700
        self.probe.receipt["command_deadline_s"] = 600

    def execute(self, name, operation):
        child = Probe(name, output_parent=self.probe.directory,
                      preparation=self.probe.receipt["kind"] == "independent-verification-preparation")
        error = None
        try:
            operation(child)
        except Exception as failure:
            error = f"{type(failure).__name__}: {failure}"
        status = child.settle(error)
        self.probe.summary["runs"].append({
            "case": name, "status": child.summary["status"],
            "receipt": str((child.directory / "receipt.json").relative_to(ROOT)),
            "comparisons": child.summary["comparisons"],
            "mismatch_count": child.summary["mismatch_count"],
        })
        if status:
            raise AssertionError(f"failed {name}: {child.directory.relative_to(ROOT)}/receipt.json")
        if not sum(child.summary["comparisons"].values()):
            raise AssertionError(f"no independent comparisons executed in {name}")
        return child


def behavior(suite):
    run = suite.execute
    run("configuration-matrix", configuration.run)
    run("icarus-scalar-startup", lambda p: run_scalar(p, "iverilog", compact=True))
    run("icarus-one-token", lambda p: top.run(p, "iverilog"))
    run("prefetch-ownership", prefetch.run)
    for name, scenario, command in protocol.CASES:
        run(name, lambda p: protocol.run(p, scenario, command))
    for bits in (1, 8, 64):
        run(f"csr-counter-width{bits}", lambda p: telemetry.run(p, bits, "iverilog"))
    for seed in SEEDS:
        for weight, cache in ((0, 0), (2, 0), (0, 2), (2, 2)):
            run(f"graph-seed{seed}-weight{weight}-cache{cache}", lambda p: graph.run(
                p, commands=COMMANDS, seed=seed, weight_mode=weight, cache_mode=cache))
        for format_, weight, cache in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)):
            run(f"compat-seed{seed}-format{format_}-weight{weight}-cache{cache}",
                lambda p: parent.run(p, compatibility=True, fp_format=format_,
                                     weight_mode=weight, cache_mode=cache, commands=COMMANDS,
                                     seed=seed, dual_reference=True))
    run("compact-28-layer-sequencing", lambda p: top.run(p, "verilator", layers=28))
    run("full-1536-8960-streamed-operators", gemv.run)
    for tile in (1, 3):
        run(f"distinct-heads-tile{tile}", lambda p: attention.run(p, True, "verilator", 8, tile))
    suite.probe.summary["boundary_matrix"] = [
        {"name": name, "parameters": parameters, "scope": "elaboration and reset/startup"}
        for name, parameters in configuration.LEGAL_CONFIGURATIONS]


def numerics(suite):
    run = suite.execute
    run("bf16-all-storage-patterns", formats.run_storage)
    run("all-e4m3fn-scale-pairs", lambda p: run_mx(p, "verilator"))
    run("group32-independent-encoding", formats.run_encode)
    scalar = run("fp32-and-transcendentals", lambda p: run_scalar(p, "verilator"))
    suite.probe.compare("positive-rsqrt-coverage", True,
                        scalar.summary["comparisons"].get("rsqrt-4ulp", 0) >= 10000, {})
    suite.probe.compare("exp-domain-coverage", True,
                        scalar.summary["comparisons"].get("exp-4ulp", 0) >= 10000, {})
    tiles = run("128-lane-balanced-trees", lambda p: tensor.run(p, False, "verilator"))
    suite.probe.compare("independent-tensor-tiles", True,
                        tiles.summary["coverage"]["independent_random_finite_tiles"] >= 10000, {})
    fused = run("full-fused-numerics", lambda p: epilogue.run(p, False, "verilator"))
    for key, threshold in (("rms_vectors", 1000), ("rope_pairs", 10000), ("swiglu_elements", 10000)):
        suite.probe.compare(key + "-coverage", True, fused.summary["coverage"][key] >= threshold, {})
    suite.probe.compare("full-rms-dimensions", True,
                        {1536, 8960}.issubset(fused.summary["coverage"]["rms_lengths"]), {})
    attention_cases = 0
    for start in range(0, 100, 25):
        shard = run(f"full-128-component-six-head-attention-{start}-{start + 24}",
                    lambda p, start=start: attention.run(
                        p, False, "verilator", 128, 3, case_start=start, case_count=25))
        attention_cases += (shard.summary["attention_fixture_range"]["stop"] -
                            shard.summary["attention_fixture_range"]["start"])
    suite.probe.compare("six-head-attention-transaction-coverage", 100, attention_cases, {})


def defects(suite):
    suite.execute("ten-compiled-non-equivalent-mutants", mutations.run)


def synthesis_checks(suite):
    run = suite.execute
    # A source-bound unresolved integrated failure is not replaced by leaf evidence.
    run("controller-process-lowering", controller.run)
    run("default-accelerated-top", lambda p: synthesis.run(p, "anvil_q2_fp2_top"))
    for name in synthesis.TOPS[:-1]:
        run(f"default-{name}", lambda p: synthesis.run(p, name))
    compact_results = {}
    for weight, cache in ((0, 0), (2, 0), (0, 2), (2, 2)):
        parameters = {**synthesis.COMPACT_TOP, "WEIGHT_MODE": weight, "CACHE_MODE": cache}
        result = run(f"native-mx-weight{weight}-cache{cache}",
                     lambda p: synthesis.run(p, "anvil_q2_fp2_top", parameters))
        compact_results[f"weight{weight}-cache{cache}"] = result.summary["synthesis"]
    for format_, weight, cache in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)):
        parameters = {**synthesis.COMPACT_TOP, "ACCEL_ENABLE": 0,
                      "FP_FORMAT": format_, "WEIGHT_MODE": weight, "CACHE_MODE": cache}
        run(f"compatibility-format{format_}-weight{weight}-cache{cache}",
            lambda p: synthesis.run(p, "anvil_q2_fp2_top", parameters))
    baseline = run("executed-parent-baseline", lambda p: synthesis.run(
        p, "anvil_q2_fp_top", synthesis.COMPACT_TOP))
    suite.probe.summary["comparable_logical_ppa"] = {
        "parameters": synthesis.COMPACT_TOP,
        "parent": baseline.summary["synthesis"], "fp2": compact_results,
        "units": "generic hierarchical logic cells, state bits and inferred memory bits",
        "physical_or_power_claim": "none; generic statistics are not ALMs, DSPs, M20Ks or watts",
    }

    def expanded_parent(probe):
        expanded = synthesis.expand_parent(probe.directory / "exact-package-expansion")
        parent.run(probe, "verilator", expanded_sources=expanded)
    original = run("parent-original-package-behavior", lambda p: parent.run(p, "verilator"))
    expanded = run("parent-exact-expanded-package-behavior", expanded_parent)
    suite.probe.compare("package-expansion-logits", original.summary["logit_bits"],
                        expanded.summary["logit_bits"], {})
    suite.probe.compare("package-expansion-protocol", original.summary["transactions"],
                        expanded.summary["transactions"], {})


def benchmark_checks(suite):
    suite.execute("ping-pong-live-buffer-overlap", lambda p: prefetch.run(p, "verilator"))
    suite.execute("long-stream-accounted-native-mx-density", gemv.run)
    benchmark.run(suite.probe, suite.execute)


def delivery_smokes(suite):
    run = suite.execute
    run("icarus-compact-ieee", lambda p: run_scalar(p, "iverilog", compact=True))
    run("icarus-accelerated-one-token", lambda p: top.run(p, "iverilog"))
    run("verilator-accelerated", lambda p: top.run(p, "verilator"))
    run("verilator-literal-compatibility", lambda p: parent.run(
        p, compatibility=True, dual_reference=True))
    run("independent-128-lane-numerics", lambda p: tensor.run(p, True, "verilator"))
    run("zero-latch-synthesis", lambda p: synthesis.run(p, "anvil_q2_fp2_telemetry"))


def delivery(suite):
    copied = suite.probe.directory / "deliverable-copy"
    copied.mkdir()
    inventory = {}
    for pattern in INPUTS:
        paths = sorted(path for path in ROOT.glob(pattern) if path.is_file())
        if not paths:
            raise FileNotFoundError(f"no declared deliverable matches {pattern}")
        for path in paths:
            relative = path.relative_to(ROOT)
            destination = copied / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            actual = hashlib.sha256(destination.read_bytes()).hexdigest()
            expected = hashlib.sha256(path.read_bytes()).hexdigest()
            suite.probe.compare("exact-deliverable-copy", expected, actual, {"path": str(relative)})
            inventory[str(relative)] = actual
    forbidden = (r"/(?:data|home)/[A-Za-z0-9_-]", r"JTAG_CABLE\s*=", r"PCI_BDF\s*=")
    for relative in inventory:
        if relative.endswith((".py", ".md", ".qsf", ".sdc", ".tcl", ".sv")):
            text = (copied / relative).read_text()
            for literal in forbidden:
                suite.probe.compare("portable-shipped-source", False, bool(re.search(literal, text)),
                                    {"path": relative, "literal": literal})
    if suite.probe.summary["mismatch_count"]:
        raise AssertionError("nonportable declared deliverable")
    suite.probe.summary["copied_source_sha256"] = inventory
    for name, flags in (("normal", []), ("isolated", ["-I"])):
        argv = [sys.executable, *flags, str(copied / "tests/verify.py"),
                "--suite", "delivery", "--delivery-child"]
        # The copied script sets cwd from its own source location, not the parent cwd.
        output = suite.probe.command(argv, f"copied-{name}")
        records = []
        for line in output.read_text().splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("suite") == "delivery" and "receipt" in record:
                records.append(record)
        if len(records) != 1:
            raise AssertionError(f"missing copied {name} verification result")
        receipt = copied / records[0]["receipt"]
        if not receipt.is_file():
            raise FileNotFoundError(f"copied receipt not retained: {receipt.relative_to(ROOT)}")
        retained = json.loads(receipt.read_text())
        summary = json.loads((copied / retained["summary"]).read_text())
        suite.probe.compare("copied-verifier-exit", 0, retained["exit_status"], {"launch": name})
        suite.probe.compare("copied-verifier-comparisons", True,
                            len(summary.get("runs", [])) == 6 and
                            all(sum(row["comparisons"].values()) > 0 and
                                row["status"] == "passed" for row in summary["runs"]),
                            {"launch": name})
        suite.probe.summary["runs"].append({
            "case": f"copied-{name}", "status": summary["status"],
            "receipt": str(receipt.relative_to(ROOT))})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=SUITES)
    parser.add_argument("--delivery-child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.delivery_child and args.suite != "delivery":
        parser.error("--delivery-child is only valid with --suite delivery")
    os.chdir(ROOT)
    operations = dict(zip(SUITES, (behavior, numerics, defects, synthesis_checks,
                                   benchmark_checks, delivery), strict=True))
    exit_status = 0
    for name in (args.suite,) if args.suite else SUITES:
        suite = None
        error = None
        try:
            with SuiteDeadline():
                suite = Suite(name)
                (delivery_smokes if args.delivery_child else operations[name])(suite)
        except Exception as failure:
            error = f"{type(failure).__name__}: {failure}"
        if suite is None:
            print(json.dumps({"suite": name, "status": "failed", "error": error}), flush=True)
            exit_status = 1
        else:
            exit_status |= suite.probe.settle(error)
    return exit_status


if __name__ == "__main__":
    raise SystemExit(main())
