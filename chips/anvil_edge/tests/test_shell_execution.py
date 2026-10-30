"""Execution-policy/rendering regressions, not functional RTL coverage."""

import json
from pathlib import Path
import sys
import unittest
import uuid
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qwen_shell import shell_case, shell_workers
from verify import Evidence, VerificationFailure


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


if __name__ == "__main__":
    OUTPUT = Path(sys.argv.pop(1))
    INPUTS = Path(sys.argv.pop(1))
    unittest.main()
