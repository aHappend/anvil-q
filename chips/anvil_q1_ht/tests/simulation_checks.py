#!/usr/bin/env python3
"""Bounded simulator-tiering diagnostics, not a reduced acceptance campaign.

python3 -B tests/simulation_checks.py --compact compares one AWQ and one BF16
first token with Icarus and Verilator. --performance separately compares the
same configuration-2, seed-89 AWQ first token using -Os and -O3 C++ builds.
Compact compiled runs also verify PCH-free unified integration compilation and
retain measured compile time and settled build-storage counts.
--flatten-performance compares -O3 builds with and without module inlining.
--redirect checks that an explicit multi-token Icarus request executes a separate
compact portability smoke and the complete original workload with Verilator.
--namespaces runs sequential, repeated scenarios on one Evidence instance,
including the inference-to-orphan-fault transition that previously collided.
Diagnostic modes are mutually exclusive. Redirect evidence uses the separate
verifier-simulation-redirect-* parent namespace; performance routing is unchanged.
None of these commands replaces any mandatory matrix row or native gate.
"""

import argparse
import contextlib
import io
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiments
from verify import Evidence, NONPORTABLE_PATH, ROOT, file_sha256


def argument_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--compact", action="store_true")
    modes.add_argument("--performance", action="store_true")
    modes.add_argument("--flatten-performance", action="store_true")
    modes.add_argument("--redirect", action="store_true")
    modes.add_argument("--namespaces", action="store_true")
    parser.add_argument("--repair-of")
    parser.add_argument("--regression-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--scratch", help=argparse.SUPPRESS)
    return parser


class SimulationTierChecks(unittest.TestCase):
    def test_diagnostic_parent_output_routing(self):
        for mode in ("compact", "performance", "flatten-performance", "redirect", "namespaces"):
            with self.subTest(mode=mode):
                args = argument_parser().parse_args(["--" + mode])
                with patch.object(sys.modules[__name__], "Evidence",
                                  side_effect=RuntimeError("stop before execution")) as factory:
                    with self.assertRaisesRegex(RuntimeError, "stop before execution"):
                        run(args)
                expected = ("simulation-" + mode if mode in ("redirect", "namespaces")
                            else "simulation-tiering")
                factory.assert_called_once_with(expected, None)

    def test_combined_diagnostic_modes_are_rejected_before_execution(self):
        modes = ("--compact", "--performance", "--flatten-performance", "--redirect",
                 "--namespaces")
        for index, first in enumerate(modes):
            for second in modes[index + 1:]:
                with self.subTest(first=first, second=second):
                    with contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as rejection:
                            argument_parser().parse_args([first, second])
                    self.assertEqual(rejection.exception.code, 2)

    def evidence(self, suffix=""):
        trial = Evidence.__new__(Evidence)
        trial.folder = SCRATCH / (self._testMethodName + suffix)
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

    def test_unified_build_is_explicit_and_preserves_simulation_options(self):
        trial = self.evidence()
        with patch("verify.shutil.which", return_value="verilator"):
            trial.simulate("unified", "module tb; endmodule", sources=[],
                           simulator="verilator", unified_build=True)
        _, _, compile_command, simulation = trial.record["commands"]
        argv = compile_command["argv"]
        self.assertEqual(argv[argv.index("-MAKEFLAGS") + 1], "VM_PARALLEL_BUILDS=0")
        self.assertIn("--assert", argv)
        self.assertEqual(argv[argv.index("-CFLAGS") + 1], "-O3")
        self.assertGreaterEqual(simulation["timeout"], 3600)
        build, = trial.record["simulation_builds"]
        self.assertIn("VM_PARALLEL_BUILDS=0", build["identity"]["options"])
        self.assertTrue(build["identity"]["unified_build"])

    def test_build_policy_change_cannot_reuse_parallel_build(self):
        trial = self.evidence()
        pool = {}
        with patch("verify.shutil.which", return_value="verilator"):
            for name, unified in (("parallel", False), ("unified", True)):
                trial.simulate(name, "module tb; endmodule", sources=[],
                               simulator="verilator", build_pool=pool,
                               unified_build=unified)
        self.assertEqual(len(pool), 2)
        self.assertEqual([row["reused"] for row in trial.record["simulation_builds"]],
                         [False, False])

    def test_all_integration_geometries_select_pch_free_builds(self):
        for config in range(len(experiments.MATRIX)):
            for mode in ("AWQ", "BF16"):
                with self.subTest(config=config, mode=mode):
                    trial = self.evidence(f"-{config}-{mode.lower()}")
                    calls = []
                    trial.simulate = lambda name, bench, **kwargs: calls.append(kwargs)
                    experiments.top_probe(trial, mode, 17, config=config)
                    reset, functional = calls
                    self.assertEqual(reset["simulator"], "iverilog")
                    self.assertEqual(reset["defines"], ("RESET_ONLY",))
                    self.assertEqual(functional["simulator"], "verilator")
                    self.assertTrue(functional["unified_build"])
                    self.assertEqual(functional["cxx_optimization"], "-O3")
                    self.assertGreaterEqual(functional["timeout"], 3600)
                    self.assertNotIn("diagnostic_scope", trial.record)
                    self.assertGreater(len(trial.record["engineering_fixture"]["tokens"]), 1)

    def test_native_profile_keeps_assertions_and_requires_completed_samples(self):
        trial = self.evidence()
        trial.native_profile = True
        with patch("verify.shutil.which", return_value="verilator"):
            with self.assertRaisesRegex(RuntimeError, "exactly one completed sample"):
                trial.simulate("profile", "module tb; endmodule", sources=[],
                               simulator="verilator")
        _, _, compile_command, simulation = trial.record["commands"]
        argv = compile_command["argv"]
        self.assertIn("--assert", argv)
        self.assertIn("-pg", argv)
        self.assertEqual(argv[argv.index("-LDFLAGS") + 1], "-pg")
        self.assertEqual(simulation["argv"][0], "env")
        self.assertTrue(simulation["argv"][1].startswith("GMON_OUT_PREFIX=evidence/preparation/"))

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

    def test_explicit_multitoken_icarus_request_redirects_without_losing_tokens(self):
        trial = self.evidence()
        calls = []
        trial.simulate = lambda name, bench, **kwargs: calls.append((name, bench, kwargs))
        with patch("experiments.compact_integration_smoke",
                   return_value="compact-smoke/receipt.json") as smoke:
            experiments.top_probe(trial, "AWQ", 17, simulator="iverilog")
        smoke.assert_called_once_with(trial, "AWQ", 17)
        self.assertEqual(len(trial.record["engineering_fixture"]["tokens"]), 2)
        self.assertNotIn("diagnostic_scope", trial.record)
        self.assertEqual([call[2]["simulator"] for call in calls],
                         ["iverilog", "verilator"])
        self.assertEqual(calls[0][2]["defines"], ("RESET_ONLY",))
        self.assertEqual(trial.record["simulation_tier_redirects"][0]["configuration"], 0)

    def test_explicit_large_icarus_request_keeps_original_geometry_and_workload(self):
        trial = self.evidence()
        calls = []
        trial.simulate = lambda name, bench, **kwargs: calls.append((name, bench, kwargs))
        with patch("experiments.compact_integration_smoke",
                   return_value="compact-smoke/receipt.json") as smoke:
            experiments.top_probe(trial, "BF16", 89, config=2, simulator="iverilog")
        smoke.assert_called_once_with(trial, "BF16", 89)
        fixture = trial.record["engineering_fixture"]
        self.assertEqual(fixture["shape"]["hidden"], 128)
        self.assertEqual(len(fixture["tokens"]), 8)
        self.assertNotIn("diagnostic_scope", trial.record)
        self.assertEqual([call[2]["simulator"] for call in calls],
                         ["iverilog", "verilator"])
        self.assertEqual(calls[0][2]["defines"], ("RESET_ONLY",))

    def test_explicit_compact_single_token_icarus_request_stays_interpreted(self):
        trial = self.evidence()
        calls = []
        trial.simulate = lambda name, bench, **kwargs: calls.append((name, bench, kwargs))
        with patch("experiments.compact_integration_smoke") as smoke:
            experiments.top_probe(trial, "AWQ", 17, diagnostic_first_token=True,
                                  simulator="iverilog")
        smoke.assert_not_called()
        self.assertEqual(len(trial.record["engineering_fixture"]["tokens"]), 1)
        self.assertEqual([call[2]["simulator"] for call in calls], ["iverilog"])
        self.assertNotIn("simulation_tier_redirects", trial.record)

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

    def test_sequential_and_repeated_scenarios_keep_exclusive_namespaces(self):
        trial = self.evidence()
        calls = []

        def simulate(name, bench, **kwargs):
            folder = trial.folder / name
            folder.mkdir(exist_ok=False)
            (folder / "tb.sv").write_text(bench)
            calls.append((name, kwargs))

        trial.simulate = simulate
        retained = {}
        for options in ({"diagnostic_first_token": True}, {"orphan_fault": True},
                        {"orphan_fault": True}, {"diagnostic_first_token": True}):
            experiments.top_probe(trial, "AWQ", 17, **options)
            if len(calls) == 2:
                sentinel = trial.folder / calls[0][0] / "retained.txt"
                sentinel.write_text("prior evidence must remain unchanged\n")
            for path, digest in retained.items():
                self.assertEqual(file_sha256(ROOT / path), digest)
            retained.update(trial.record["runtime_input_sha256"])
        cases = trial.record["runtime_cases"]
        self.assertEqual(len(cases), 4)
        self.assertEqual(len({case["directory"] for case in cases}), 4)
        self.assertEqual(len({name for name, _ in calls}), 8)
        for case, (reset, functional) in zip(cases, zip(calls[::2], calls[1::2])):
            self.assertIn(case["namespace"], case["directory"])
            self.assertEqual(reset[0], case["namespace"] + "-four-state-reset")
            self.assertEqual(functional[0], case["namespace"])
            self.assertEqual(reset[1]["runtime_args"], functional[1]["runtime_args"])
            self.assertIn("+CASE_DIR=" + case["directory"], functional[1]["runtime_args"])
            self.assertTrue(all(path.startswith(case["directory"] + "/")
                                for path in case["input_sha256"]))
        self.assertIn("orphan-fault", cases[1]["namespace"])
        self.assertIn("orphan-fault", cases[2]["namespace"])
        self.assertEqual(sentinel.read_text(), "prior evidence must remain unchanged\n")

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
        if simulator == "verilator":
            build, = trial.record["simulation_builds"]
            compile_command = build["compile_command"]
            compile_stdout = (ROOT / compile_command["stdout"]).read_text()
            cleanup, = trial.record["compile_intermediate_cleanup"]
            if (not build["identity"]["unified_build"] or
                    "VM_PARALLEL_BUILDS=0" not in build["identity"]["options"] or
                    "-x c++-header" in compile_stdout or
                    any(row["path"].endswith(".gch") for row in cleanup["removed"])):
                raise AssertionError("integration compilation expanded optional PCH storage")
            directory = (ROOT / build["executable"]).parent
            result["compiled_storage"] = {
                "unified_build": True,
                "compile_seconds": compile_command["elapsed_seconds"],
                "settled_retained_build_bytes": sum(
                    path.stat().st_size for path in directory.rglob("*") if path.is_file()),
                "removed_compiler_scratch_bytes": cleanup["removed_bytes"],
                "pch_compile_commands": 0,
                "scope": "settled storage counts, not peak filesystem usage",
            }
        trial.finish("probe_passed", result["coverage_limit"])
    except (OSError, RuntimeError, AssertionError, ValueError) as exc:
        trial.finish("failed", str(exc))
        raise
    parent.record["observations"].append(result)
    parent.flush()
    return result


def run(args):
    probe = ("simulation-redirect" if args.redirect else
             "simulation-namespaces" if args.namespaces else "simulation-tiering")
    evidence = Evidence(probe, args.repair_of)
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
        if args.namespaces:
            retained = {}
            for mode in ("AWQ", "BF16"):
                counters = []
                for simulator in ("iverilog", "verilator"):
                    experiments.top_probe(evidence, mode, 17, diagnostic_first_token=True,
                                          simulator=simulator)
                    counters.append(evidence.record["observations"][-1]["observed_counters"])
                if counters[0] != counters[1]:
                    raise AssertionError(f"{mode}: compact simulator comparisons differ")
                for _ in range(2):
                    experiments.top_probe(evidence, mode, 17, orphan_fault=True)
                    for path, digest in retained.items():
                        if file_sha256(ROOT / path) != digest:
                            raise AssertionError("earlier scenario input changed: " + path)
                    retained.update(evidence.record["runtime_input_sha256"])
            cases = evidence.record["runtime_cases"]
            names = [row["name"] for row in evidence.record["observations"]]
            builds = evidence.record["simulation_builds"]
            if (len(cases) != 8 or len({case["directory"] for case in cases}) != 8 or
                    len(names) != 14 or len(set(names)) != 14 or
                    len(builds) != 6 or not any(build["reused"] for build in builds)):
                raise AssertionError("missing sequential scenarios, exclusive outputs or build reuse")
            evidence.record["namespace_regression"] = {
                "invocations": len(cases), "exclusive_simulation_outputs": len(names),
                "compiled_runs": len(builds),
                "reused_builds": sum(build["reused"] for build in builds),
                "scope": "compact AWQ/BF16 portability and repeated orphan-fault recovery; "
                         "not aggregate L1 or native acceptance",
            }
            evidence.flush()
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
        if args.redirect:
            for mode in ("AWQ", "BF16"):
                trial = Evidence("redirect-" + mode.lower(),
                                 repair_of=evidence.relative(evidence.folder / "receipt.json"),
                                 source_root=evidence.folder / "sources")
                try:
                    experiments.top_probe(trial, mode, 89, simulator="iverilog")
                    fixture = trial.record["engineering_fixture"]
                    if len(fixture["tokens"]) != 2 or "diagnostic_scope" in trial.record:
                        raise AssertionError("redirect reduced the original workload")
                    redirects = trial.record["simulation_tier_redirects"]
                    if len(redirects) != 1:
                        raise AssertionError("missing simulator redirect provenance")
                    import json
                    smoke_path = ROOT / redirects[0]["compact_smoke_receipt"]
                    smoke = json.loads(smoke_path.read_text())
                    if (smoke.get("outcome") != "probe_passed" or
                            len(smoke["engineering_fixture"]["tokens"]) != 1):
                        raise AssertionError("missing completed compact portability smoke")
                    rows = trial.record["observations"][-1]["observed_counters"]
                    tokens = [row for row in rows if "position" in row]
                    if len(tokens) != 2 or any(row["logits"] != 8 for row in tokens):
                        raise AssertionError("missing complete redirected numerical comparisons")
                    if trial.record["commands"][-1]["argv"][0] == "vvp":
                        raise AssertionError("requested workload still ran interpreted")
                    trial.finish("probe_passed", "Complete redirected compact workload and "
                                 "separate single-token portability smoke.")
                except (OSError, RuntimeError, AssertionError, ValueError) as exc:
                    trial.finish("failed", str(exc))
                    raise
                evidence.record["observations"].append({
                    "mode": mode, "receipt": evidence.relative(trial.folder / "receipt.json"),
                    "compact_smoke_receipt": redirects[0]["compact_smoke_receipt"],
                    "compared_tokens": len(tokens),
                    "ordered_logits": sum(row["logits"] for row in tokens),
                    "scope": "simulator routing only; no large-case patrol closure",
                })
                evidence.flush()
        evidence.finish("probe_passed", "Bounded tiering diagnosis; full L1 remains incomplete.")
        return 0
    except (OSError, RuntimeError, AssertionError, ValueError) as exc:
        evidence.finish("failed", str(exc))
        return 1


if __name__ == "__main__":
    parser = argument_parser()
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
    elif (arguments.compact or arguments.performance or arguments.flatten_performance or
          arguments.redirect or arguments.namespaces):
        raise SystemExit(run(arguments))
    else:
        parser.error("choose --compact, --performance, --flatten-performance, --redirect "
                     "or --namespaces")
