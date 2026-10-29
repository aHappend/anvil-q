#!/usr/bin/env python3
"""Bounded simulator-tiering diagnostics, not a reduced acceptance campaign.

python3 -B tests/simulation_checks.py --compact compares one AWQ and one BF16
first token with Icarus and Verilator. --performance separately compares the
same configuration-2, seed-89 AWQ first token using -Os and -O3 C++ builds.
--flatten-performance compares -O3 builds with and without module inlining.
None of these commands replaces any mandatory matrix row or native gate.
"""

import argparse
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiments
from verify import Evidence, NONPORTABLE_PATH, ROOT, file_sha256


class SimulationTierChecks(unittest.TestCase):
    def evidence(self):
        trial = Evidence.__new__(Evidence)
        trial.folder = SCRATCH / self._testMethodName
        trial.folder.mkdir(parents=True, exist_ok=False)
        trial.record = {"observations": [], "commands": []}
        trial.flush = lambda: None

        def command(argv, label, timeout=3600, **kwargs):
            row = {"argv": argv, "label": label, "timeout": timeout}
            ordinal = len(trial.record["commands"])
            for key in ("stdout", "stderr"):
                path = trial.folder / f"{ordinal:05d}-{label}-{key}.log"
                path.write_text("synthetic unit-test command evidence\n")
                row[key] = trial.relative(path)
                row[key + "_sha256"] = file_sha256(path)
            trial.record["commands"].append(row)
            if label.endswith("-compile") and argv[0] == "verilator":
                build = ROOT / argv[argv.index("--Mdir") + 1]
                build.mkdir()
                (build / "Vtb").write_bytes(b"synthetic executable")
                (build / "Vtb.o").write_bytes(b"synthetic object")
                (build / "Vtb__ALL.a").write_bytes(b"synthetic archive")
                (build / "Vtb.h.gch").write_bytes(b"synthetic precompiled header")
                (build / "Vtb.cpp").write_text("synthetic generated source\n")
            return "CHECKS_PASSED synthetic comparisons=1\n"

        trial.command = command
        return trial

    def test_compiled_build_keeps_assertions_and_optimizes_cpp(self):
        trial = self.evidence()
        with patch("verify.shutil.which", return_value="verilator"):
            trial.simulate("compiled", "module tb; endmodule", sources=[],
                           simulator="verilator")
        version, compiler, compile_command, simulation = trial.record["commands"]
        argv = compile_command["argv"]
        self.assertEqual(version["argv"], ["verilator", "--version"])
        self.assertIn("--assert", argv)
        self.assertEqual(argv[argv.index("-CFLAGS") + 1], "-O3")
        self.assertGreaterEqual(simulation["timeout"], 3600)
        cleanup, = trial.record["compile_intermediate_cleanup"]
        self.assertEqual(len(cleanup["removed"]), 3)
        build = ROOT / cleanup["build"]
        self.assertEqual(sorted(path.name for path in build.iterdir()),
                         ["Vtb", "Vtb.cpp"])
        self.assertGreater(cleanup["removed_bytes"], 0)

    def test_failed_compile_still_cleans_only_settled_compiler_scratch(self):
        trial = self.evidence()
        original_command = trial.command

        def failing_compile(argv, label, **kwargs):
            output = original_command(argv, label, **kwargs)
            if label.endswith("-compile"):
                raise RuntimeError("synthetic compiler failure")
            return output

        trial.command = failing_compile
        with patch("verify.shutil.which", return_value="verilator"):
            with self.assertRaisesRegex(RuntimeError, "synthetic compiler failure"):
                trial.simulate("failed", "module tb; endmodule", sources=[],
                               simulator="verilator")
        self.assertFalse(any(row["label"].endswith("-simulation")
                             for row in trial.record["commands"]))
        cleanup, = trial.record["compile_intermediate_cleanup"]
        self.assertEqual(len(cleanup["removed"]), 3)
        self.assertTrue((ROOT / cleanup["build"] / "Vtb.cpp").is_file())

    def test_cleanup_rejects_external_directory(self):
        trial = self.evidence()
        with self.assertRaisesRegex(ValueError, "project preparation evidence"):
            trial.cleanup_compile_intermediates(ROOT / "tests")

    def test_cleanup_rejects_symlink_without_deleting_target(self):
        trial = self.evidence()
        build = trial.folder / "compiled"
        build.mkdir()
        target = trial.folder / "retained.o"
        target.write_bytes(b"must remain")
        (build / "external.o").symlink_to(target)
        with self.assertRaisesRegex(ValueError, "escapes"):
            trial.cleanup_compile_intermediates(build)
        self.assertEqual(target.read_bytes(), b"must remain")

    def test_missing_compiled_simulator_does_not_fall_back(self):
        trial = self.evidence()
        with patch("verify.shutil.which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "unavailable: verilator"):
                trial.simulate("missing", "", simulator="verilator")
        self.assertEqual(trial.record["commands"], [])

    def test_explicit_four_state_reset_overrides_compiled_suite(self):
        trial = self.evidence()
        trial.default_simulator = "verilator"
        with patch("verify.shutil.which", return_value="iverilog"):
            trial.simulate("reset", "module tb; endmodule", sources=[],
                           simulator="iverilog", defines=("RESET_ONLY",))
        compile_command, simulation = trial.record["commands"]
        self.assertEqual(compile_command["argv"][0], "iverilog")
        self.assertIn("-DRESET_ONLY", compile_command["argv"])
        self.assertEqual(simulation["argv"][0], "vvp")

    def test_compiled_mutation_default_applies_to_leaf_checks(self):
        trial = self.evidence()
        trial.default_simulator = "verilator"
        with patch("verify.shutil.which", return_value="verilator"):
            trial.simulate("mutation", "module tb; endmodule", sources=[])
        self.assertEqual(trial.record["commands"][2]["argv"][0], "verilator")

    def test_first_token_diagnostic_does_not_change_default_token_set(self):
        trial = self.evidence()
        calls = []
        trial.simulate = lambda name, bench, **kwargs: calls.append((name, bench, kwargs))
        experiments.top_probe(trial, "AWQ", 17)
        self.assertEqual(len(trial.record["engineering_fixture"]["tokens"]), 2)
        self.assertNotIn("diagnostic_scope", trial.record)
        self.assertEqual(calls[0][2]["simulator"], "iverilog")
        self.assertEqual(calls[1][2]["simulator"], "verilator")

    def test_cpp_comparison_does_not_accept_arbitrary_flags(self):
        trial = self.evidence()
        with self.assertRaisesRegex(ValueError, "unsupported C\\+\\+ optimization"):
            trial.simulate("invalid", "", cxx_optimization="-ffast-math")
        self.assertEqual(trial.record["commands"], [])

    def test_seed_and_mode_data_are_not_compiled_into_integration_bench(self):
        trial = self.evidence()
        calls = []
        trial.simulate = lambda name, bench, **kwargs: calls.append((name, bench, kwargs))
        experiments.top_probe(trial, "AWQ", 17)
        first_inputs = dict(trial.record["runtime_input_sha256"])
        experiments.top_probe(trial, "BF16", 89)
        self.assertEqual(calls[0][1], calls[2][1])
        self.assertEqual(calls[1][1], calls[3][1])
        self.assertNotEqual(first_inputs, trial.record["runtime_input_sha256"])
        self.assertTrue(all(trial.record["runtime_input_sha256"][path] == digest
                            for path, digest in first_inputs.items()))
        self.assertEqual(len(trial.record["runtime_cases"]), 2)
        for path, digest in first_inputs.items():
            self.assertEqual(file_sha256(ROOT / path), digest)
        self.assertEqual(len(trial.record["engineering_fixture"]["tokens"]), 2)

    def test_reuse_executes_each_runtime_case_and_binds_the_original_build(self):
        trial = self.evidence()
        pool = {}
        with patch("verify.shutil.which", return_value="verilator"):
            for name in ("awq17", "bf1689"):
                trial.simulate(name, "module tb; endmodule", sources=[],
                               simulator="verilator", build_pool=pool,
                               runtime_args=("+CASE_DIR=" + name,))
        commands = trial.record["commands"]
        self.assertEqual(sum(row["label"].endswith("-compile") for row in commands), 1)
        runs = [row for row in commands if row["label"].endswith("-simulation")]
        self.assertEqual(len(runs), 2)
        self.assertEqual(runs[0]["argv"][0], runs[1]["argv"][0])
        self.assertNotEqual(runs[0]["argv"][1], runs[1]["argv"][1])
        self.assertEqual([row["reused"] for row in trial.record["simulation_builds"]],
                         [False, True])

    def test_changed_options_or_bench_require_another_build(self):
        trial = self.evidence()
        pool = {}
        with patch("verify.shutil.which", return_value="verilator"):
            for name, bench, flags in (
                    ("original", "module tb; endmodule", ()),
                    ("options", "module tb; endmodule", ("CHANGED",)),
                    ("bench", "module tb; initial $finish; endmodule", ())):
                trial.simulate(name, bench, sources=[], simulator="verilator",
                               build_pool=pool, defines=flags)
        self.assertEqual(len(pool), 3)
        self.assertTrue(all(not row["reused"] for row in trial.record["simulation_builds"]))

    def test_changed_executable_is_rejected_not_silently_rebuilt(self):
        trial = self.evidence()
        pool = {}
        with patch("verify.shutil.which", return_value="verilator"):
            trial.simulate("original", "module tb; endmodule", sources=[],
                           simulator="verilator", build_pool=pool)
            build, = pool.values()
            (ROOT / build["executable"]).write_bytes(b"changed")
            with self.assertRaisesRegex(RuntimeError, "compiled simulation build changed"):
                trial.simulate("changed", "module tb; endmodule", sources=[],
                               simulator="verilator", build_pool=pool)
        self.assertEqual(sum(row["label"].endswith("-simulation")
                             for row in trial.record["commands"]), 1)

    def test_missing_producer_compile_log_rejects_reuse(self):
        trial = self.evidence()
        pool = {}
        with patch("verify.shutil.which", return_value="verilator"):
            trial.simulate("original", "module tb; endmodule", sources=[],
                           simulator="verilator", build_pool=pool)
            build, = pool.values()
            log = ROOT / build["compile_command"]["stdout"]
            log.unlink()
            with self.assertRaises(FileNotFoundError):
                trial.simulate("lost", "module tb; endmodule", sources=[],
                               simulator="verilator", build_pool=pool)
            self.assertFalse(log.exists())
        self.assertEqual(sum(row["label"].endswith("-simulation")
                             for row in trial.record["commands"]), 1)

    def test_changed_sources_preserve_clean_reproduction_path_policy(self):
        for name in ("verify", "experiments", "benchmarks", "compatibility",
                     "sensitivity", "simulation_checks", "campaign_costs"):
            with self.subTest(source=name):
                source = ROOT / "tests" / (name + ".py")
                self.assertIsNone(NONPORTABLE_PATH.search(source.read_text()))


def compared_case(parent, label, mode, simulator, config=0, optimization="-O3",
                  flatten=False):
    trial = Evidence(label, repair_of=parent.relative(parent.folder / "receipt.json"),
                     source_root=parent.folder / "sources")
    try:
        experiments.top_probe(trial, mode, 89, config=config,
                              diagnostic_first_token=True, simulator=simulator,
                              cxx_optimization=optimization, flatten=flatten)
        observation = trial.record["observations"][-1]
        rows = observation["observed_counters"]
        tokens = [row for row in rows if "position" in row]
        summaries = [row for row in rows if "preload_beats" in row]
        shape = experiments.MATRIX[config]
        if (len(tokens) != 1 or len(summaries) != 1 or
                tokens[0]["position"] != 0 or tokens[0]["logits"] != shape.vocab or
                summaries[0]["logits"] != shape.vocab or summaries[0]["reads"] <= 0):
            raise AssertionError("diagnostic lacks a fully compared first token")
        command = trial.record["commands"][-1]
        result = {
            "configuration": config, "seed": 89, "mode": mode,
            "simulator": simulator, "cxx_optimization": optimization,
            "flatten": flatten,
            "receipt": parent.relative(trial.folder / "receipt.json"),
            "compared_counters": rows, "simulation_seconds": command["elapsed_seconds"],
            "coverage_limit": "first token only; no matrix or hardware acceptance",
        }
        trial.finish("probe_passed", result["coverage_limit"])
    except (OSError, RuntimeError, AssertionError, ValueError) as exc:
        trial.finish("failed", str(exc))
        raise
    parent.record["observations"].append(result)
    parent.flush()
    return result


def run(args):
    evidence = Evidence("simulation-tiering", args.repair_of)
    evidence.record["scope"] = (
        "Harness regression and simulator performance diagnosis only; "
        "no requirement, mandatory check, or patrol limit is changed.")
    evidence.flush()
    try:
        evidence.command(
            ["python3", "-B", "tests/simulation_checks.py", "--regression-child",
             "--scratch", evidence.relative(evidence.folder / "regression-scratch")],
            "simulation-tier-regression")
        for tool, flags in (("python3", ["--version"]), ("iverilog", ["-V"]),
                            ("vvp", ["-V"]), ("verilator", ["--version"]),
                            ("g++", ["--version"])):
            if shutil.which(tool) is None:
                raise RuntimeError(f"required diagnostic tool unavailable: {tool}")
            evidence.command([tool, *flags], "cxx-version" if tool == "g++" else tool + "-version")
        if args.compact:
            for mode in ("AWQ", "BF16"):
                interpreted = compared_case(evidence, "compact-" + mode.lower() + "-icarus",
                                            mode, "iverilog")
                compiled = compared_case(evidence, "compact-" + mode.lower() + "-compiled",
                                         mode, "verilator")
                if interpreted["compared_counters"] != compiled["compared_counters"]:
                    raise AssertionError(f"{mode}: simulator counters or numerical comparisons differ")
        if args.performance:
            baseline = compared_case(evidence, "performance-os", "AWQ", "verilator",
                                     config=2, optimization="-Os")
            optimized = compared_case(evidence, "performance-o3", "AWQ", "verilator",
                                      config=2)
            if baseline["compared_counters"] != optimized["compared_counters"]:
                raise AssertionError("C++ optimization changed observed comparisons or cycle counts")
            evidence.record["host_simulation_performance"] = {
                "baseline_seconds": baseline["simulation_seconds"],
                "optimized_seconds": optimized["simulation_seconds"],
                "observed_wall_time_ratio": baseline["simulation_seconds"] /
                                            optimized["simulation_seconds"],
                "scope": "host simulator only; not accelerator speedup or budget closure",
            }
        if args.flatten_performance:
            baseline = compared_case(evidence, "performance-hierarchical", "AWQ", "verilator",
                                     config=2)
            flattened = compared_case(evidence, "performance-flattened", "AWQ", "verilator",
                                      config=2, flatten=True)
            if baseline["compared_counters"] != flattened["compared_counters"]:
                raise AssertionError("module inlining changed comparisons or cycle counts")
            evidence.record["host_flattening_performance"] = {
                "baseline_seconds": baseline["simulation_seconds"],
                "flattened_seconds": flattened["simulation_seconds"],
                "observed_wall_time_ratio": baseline["simulation_seconds"] /
                                            flattened["simulation_seconds"],
                "scope": "host simulator only; not accelerator speedup or budget closure",
            }
        evidence.finish("probe_passed", "Bounded tiering diagnosis; full L1 remains incomplete.")
        return 0
    except (OSError, RuntimeError, AssertionError, ValueError) as exc:
        evidence.finish("failed", str(exc))
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--performance", action="store_true")
    parser.add_argument("--flatten-performance", action="store_true")
    parser.add_argument("--repair-of")
    parser.add_argument("--regression-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--scratch", help=argparse.SUPPRESS)
    arguments = parser.parse_args()
    if arguments.regression_child:
        if not arguments.scratch:
            parser.error("regression child needs a fresh scratch path")
        SCRATCH = Path(arguments.scratch)
        if SCRATCH.is_absolute() or ".." in SCRATCH.parts:
            parser.error("scratch must be project-relative")
        if not SCRATCH.resolve().is_relative_to(ROOT / "evidence/preparation"):
            parser.error("scratch must be inside project preparation evidence")
        SCRATCH = SCRATCH.resolve()
        sys.argv = sys.argv[:1]
        unittest.main()
    elif arguments.compact or arguments.performance or arguments.flatten_performance:
        raise SystemExit(run(arguments))
    else:
        parser.error("choose --compact, --performance or --flatten-performance")
