"""Execution-policy/rendering regressions, not functional RTL coverage."""

import json
from pathlib import Path
import sys
import time
import unittest
import uuid
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qwen_shell import shell_case, shell_workers
from verify import (
    Evidence, VerificationFailure, observe_phase_stdout, relay_phase_progress,
)
from cycle_driver import full_capacity_measurement


class ShellExecutionTests(unittest.TestCase):
    def policy_case(self, requested, compiled, arguments=()):
        evidence = Evidence.__new__(Evidence)
        evidence.path = OUTPUT / uuid.uuid4().hex
        evidence.path.mkdir()
        evidence.simulator_override = requested
        evidence.explicit_clock = None
        evidence.name_prefix = ""
        evidence.source_overrides = {}
        evidence.record = {"coverage": []}
        with patch.object(Evidence, "_simulate_attempt",
                          side_effect=lambda record, *args, **kwargs: (record, kwargs)):
            return evidence.simulate(
                "policy-unit", "module bench; endmodule\n", [], 1,
                compiled_workload=compiled, runtime_arguments=arguments)

    def test_compiled_workload_routes_interpreter_request(self):
        record, options = self.policy_case("iverilog", True, ("+test_input=17",))
        self.assertEqual(record["requested_simulator"], "iverilog")
        self.assertEqual(record["simulator"], "verilator")
        self.assertEqual(options["runtime_arguments"], ("+test_input=17",))
        self.assertEqual(record["runtime_arguments"], ["+test_input=17"])

    def test_compact_interpreter_control_is_retained(self):
        record, _ = self.policy_case("iverilog", False)
        self.assertEqual(record["simulator"], "iverilog")

    def test_unknown_backend_is_not_silently_replaced(self):
        with self.assertRaises(VerificationFailure):
            self.policy_case("unknown", True)

    def test_worker_limit_respects_singleton_and_resource_cap(self):
        for available in (1, 2, 3, 8):
            scope = Mock()
            scope._limits = {"workers": available}
            self.assertEqual(shell_workers(scope), min(3, available))

    def test_shell_transport_changes_only_runtime_inputs(self):
        info = json.loads((INPUTS / "shell-reference.json").read_bytes())
        scope = Mock()
        benches = []
        for bypass in (0, 1):
            scope.simulate.reset_mock()
            shell_case(scope, info, 17, bypass, False)
            args, options = scope.simulate.call_args
            self.assertTrue(options["compiled_workload"])
            self.assertEqual(options["simulator"], "verilator")
            self.assertEqual(options["runtime_arguments"],
                             (f"+verification_bypass={bypass}",))
            self.assertIn("QWEN_SHELL_INVALID_TRANSPORT", args[1])
            self.assertNotIn(f"BYPASS={bypass},", args[1])
            benches.append(args[1].replace(info["images"][bypass]["path"], "IMAGE"))
        self.assertEqual(benches[0], benches[1])

    def measurement(self, observations=(), status="failed"):
        scope = Mock()
        info = json.loads((INPUTS / "shell-reference.json").read_bytes())
        scope.record = {"coverage": [{
            "name": "qwen-shell-b0-s1", "status": status,
            "simulation_receipt": {
                "stdout": "evidence/preparation/fixture-test/simulation/stdout.log",
                "duration_s": 12,
                "stdout_observations": [
                    {"line": line, "observed_elapsed_s": elapsed}
                    for elapsed, line in observations],
            },
        }]}
        return full_capacity_measurement(scope, info, time.monotonic())

    def test_incomplete_measurement_cannot_certify_feasibility(self):
        result = self.measurement()
        self.assertEqual(len(result["cells"]), 6)
        self.assertEqual(result["completed_cells"], 0)
        self.assertFalse(result["subset_completed_within_budget"])
        self.assertFalse(result["aggregate_cold_feasibility_demonstrated"])
        self.assertFalse(result["aggregate_retry_authorized"])
        self.assertIn("early tool/input/evidence failure", result["conclusion"])
        self.assertTrue(all(not frame["intervals"] for cell in result["cells"]
                            for frame in cell["frames"]))

    def test_phase_intervals_use_observed_endpoints(self):
        result = self.measurement((
            (1, "QWEN_SHELL_PHASE phase=input_begin frame=0 cycles=100"),
            (2, "QWEN_SHELL_PHASE phase=input_sent frame=0 cycles=130"),
            (4, "QWEN_SHELL_PHASE phase=core_begin frame=0 operation=0 cycles=200"),
            (5, "QWEN_SHELL_PHASE phase=head_begin frame=0 operation=0 cycles=300"),
            (8, "QWEN_SHELL_PHASE phase=head_ack frame=0 operation=0 cycles=600"),
            (9, "QWEN_SHELL_PHASE phase=output_progress frame=0 bytes=1 cycles=700"),
            (10, "QWEN_SHELL_PHASE phase=output_progress frame=0 bytes=8 cycles=800"),
            (11, "QWEN_SHELL_COMPLETION frame=0 cycles=900"),
        ))
        cell = result["cells"][0]
        intervals = {item["name"]: item for item in cell["frames"][0]["intervals"]}
        self.assertEqual(intervals["input_transport"]["cycles"], 30)
        self.assertEqual(intervals["post_input_to_first_core_request"]["cycles"], 70)
        self.assertEqual(intervals["physical_head_traversal"]["cycles"], 300)
        self.assertEqual(intervals["physical_head_traversal"]["observed_wall_s"], 3)
        self.assertEqual(intervals["last_output_to_done"]["cycles"], 100)
        self.assertEqual(cell["completed_frames"], 1)
        self.assertEqual(cell["status"], "failed")
        self.assertFalse(result["aggregate_retry_authorized"])

    def test_shell_observability_is_bounded_and_public(self):
        info = json.loads((INPUTS / "shell-reference.json").read_bytes())
        scope = Mock()
        shell_case(scope, info, 17, 1, False)
        bench = scope.simulate.call_args.args[1]
        self.assertNotIn("dut.", bench)
        self.assertIn("next_progress=next_progress+64'd16777216", bench)
        for phase in ("input_begin", "input_sent", "core_begin", "head_begin", "head_ack"):
            self.assertIn("phase=" + phase, bench)

    def test_phase_reader_preserves_split_lines_without_duplicate_events(self):
        directory = OUTPUT.resolve() / uuid.uuid4().hex
        directory.mkdir()
        path = directory / "phase-stream.txt"
        path.write_bytes(b"other diagnostic\nQWEN_SHELL_PHASE phase=input_")
        record, state = {"stdout_observations": []}, {"offset": 0, "partial": b""}
        observe_phase_stdout(path, record, state, ("QWEN_SHELL_",), 1)
        self.assertEqual(record["stdout_observations"], [])
        with path.open("ab") as stream:
            stream.write(b"sent frame=0 cycles=30\n")
        observe_phase_stdout(path, record, state, ("QWEN_SHELL_",), 2)
        observe_phase_stdout(path, record, state, ("QWEN_SHELL_",), 3)
        self.assertEqual(record["stdout_observations"], [{
            "line": "QWEN_SHELL_PHASE phase=input_sent frame=0 cycles=30",
            "observed_elapsed_s": 2,
        }])

    def test_unavailable_live_log_is_explicit_evidence_loss(self):
        path = OUTPUT.resolve() / uuid.uuid4().hex / "unavailable.txt"
        record, state = {"stdout_observations": []}, {"offset": 0, "partial": b""}
        observe_phase_stdout(path, record, state, ("QWEN_SHELL_",), 1)
        self.assertEqual(record["evidence_error"]["error"], "FileNotFoundError")
        self.assertEqual(record["evidence_error"]["errno"], 2)
        self.assertEqual(record["stdout_observations"], [])
        self.assertFalse(path.exists())

    def progress_record(self):
        return {"index": 7, "stdout_observations": [],
                "stdout_progress_reports": []}, {}

    def add_progress(self, record, cycles, elapsed, **fields):
        values = {"frame": 0, "acknowledgements": cycles // 4, "cycles": cycles, **fields}
        record["stdout_observations"].append({
            "line": "QWEN_SHELL_PROGRESS " +
                    " ".join(f"{key}={value}" for key, value in values.items()),
            "observed_elapsed_s": elapsed,
        })

    def test_progress_relay_requires_actual_advance_and_rate_limits(self):
        record, state = self.progress_record()
        with patch("builtins.print") as output:
            relay_phase_progress(record, state, 0)
            output.assert_not_called()
            self.add_progress(record, 100, 1)
            relay_phase_progress(record, state, 1)
            self.assertEqual(output.call_count, 1)
            relay_phase_progress(record, state, 40)
            self.assertEqual(output.call_count, 1)
            self.add_progress(record, 200, 41)
            relay_phase_progress(record, state, 41)
            self.add_progress(record, 300, 42)
            relay_phase_progress(record, state, 42)
            self.assertEqual(output.call_count, 2)
            relay_phase_progress(record, state, 43, force=True)
            self.assertEqual(output.call_count, 3)
            relay_phase_progress(record, state, 44, force=True)
            self.assertEqual(output.call_count, 3)
        reports = record["stdout_progress_reports"]
        self.assertEqual([row["cycles"] for row in reports], [100, 200, 300])
        self.assertEqual(reports[-1]["acknowledgements"], 75)
        self.assertEqual(reports[-1]["observed_elapsed_s"], 42)
        self.assertEqual(reports[-1]["relayed_elapsed_s"], 43)
        self.assertEqual(reports[-1]["child_index"], 7)
        self.assertEqual([row["at_settlement"] for row in reports], [False, False, True])
        self.assertNotIn("passed", reports[-1])

    def test_progress_relay_preserves_phase_and_ignores_non_events(self):
        record, state = self.progress_record()
        record["stdout_observations"].append({
            "line": "QWEN_SHELL_PHASE phase=head_begin frame=2 operation=5 cycles=900",
            "observed_elapsed_s": 1,
        })
        record["stdout_observations"].append({
            "line": "QWEN_SHELL_INVALID_TRANSPORT cycles=1000",
            "observed_elapsed_s": 2,
        })
        with patch("builtins.print") as output:
            relay_phase_progress(record, state, 3)
        message = output.call_args.args[0]
        self.assertTrue(message.startswith("VERIFICATION_CHILD_PROGRESS "))
        self.assertTrue(output.call_args.kwargs["flush"])
        report = json.loads(message.split(" ", 1)[1])
        self.assertEqual(report["phase"], "head_begin")
        self.assertEqual(report["operation"], 5)
        self.assertEqual(report["cycles"], 900)
        self.assertEqual(report["frame"], 2)

    def test_progress_relay_is_bounded_without_discarding_observations(self):
        record, state = self.progress_record()
        with patch("builtins.print") as output:
            for index in range(140):
                self.add_progress(record, index, index * 31)
                relay_phase_progress(record, state, index * 31, force=True)
        self.assertEqual(output.call_count, 128)
        self.assertEqual(len(record["stdout_progress_reports"]), 128)
        self.assertEqual(len(record["stdout_observations"]), 140)


if __name__ == "__main__":
    OUTPUT = Path(sys.argv.pop(1))
    INPUTS = Path(sys.argv.pop(1))
    unittest.main()
