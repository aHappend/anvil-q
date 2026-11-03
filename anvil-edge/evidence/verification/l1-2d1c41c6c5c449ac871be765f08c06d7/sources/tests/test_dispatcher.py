"""Bounded dispatch-only fixtures: never execute product suites or simulators."""

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qwen_shell
import verify


SUITES = (
    "run_arithmetic", "run_fifo", "run_controller", "run_uart", "run_detokenizer",
    "run_boot", "run_config", "run_mapper", "run_bpe", "run_normalization", "run_dfa",
    "run_tokenizer", "run_numerical", "run_parameters", "run_adapters", "run_memory",
    "run_top", "run_top_resets", "run_synthesis", "run_metadata", "run_mapper_cache",
    "run_head_row_reuse", "<lambda>",
)
STAGES = (
    "run_qwen_fragments", "run_qwen_regex", "run_unicode_rtl",
    "run_official_checkpoint", "run_deepseek_reference", "run_deepseek_dfa",
    "run_deepseek_integration", "run_deepseek_boot", "run_deepseek_bos",
    "run_qwen_integration", "run_qwen_boot", "run_qwen_shell",
)


class DispatchCapture:
    def __init__(self, path):
        self.path = path
        self.record = {}
        self.batches = []
        self.commands = []
        self._limits = {"workers": 3}

    def tools(self, names):
        self.tool_names = names

    def relative(self, path):
        return str(path.relative_to(verify.ROOT))

    def child(self, argv, name):
        self.commands.append((argv, name))

    def run_cases(self, cases, *, workers=None):
        self.batches.append(list(cases))

    def finish(self, exit_code, reason):
        self.exit_code, self.reason = exit_code, reason
        return exit_code


class DispatcherTests(unittest.TestCase):
    def setUp(self):
        self.path = OUTPUT / (self._testMethodName + "-" + uuid.uuid4().hex)
        self.path.mkdir()

    def dispatch(self):
        capture = DispatchCapture(self.path)
        with patch.object(verify, "Evidence", return_value=capture), patch.object(
                sys, "argv", ["tests/verify.py", "--check", "l1"]):
            exit_code = verify.main()
        return capture, exit_code

    def assert_contract(self, capture, exit_code):
        self.assertEqual(len(capture.batches), 2)
        suites, stages = capture.batches
        self.assertEqual(tuple(fn.__name__ for _, fn in suites), SUITES)
        self.assertEqual(tuple(fn.__name__ for _, fn in stages), STAGES)
        self.assertEqual([name for name, _ in suites],
                         [f"suite-{i}-{name}" for i, name in enumerate(SUITES)])
        self.assertEqual([name for name, _ in stages], list(STAGES))
        self.assertNotIn(qwen_shell.run_shell_scoreboard, [fn for _, fn in stages])
        self.assertEqual(exit_code, 1)
        self.assertIn("L1 incomplete:", capture.reason)
        self.assertIn("real-model integrations remain incomplete", capture.reason)
        self.assertEqual([name for _, name in capture.commands], [
            "qwen-artifact-integrity-regression", "case-record-integrity-regression",
        ])

    def test_complete_dispatch_and_incomplete_result(self):
        capture, exit_code = self.dispatch()
        self.assert_contract(capture, exit_code)
        marker = object()
        with patch.object(verify, "run_mutations") as mutations:
            capture.batches[0][-1][1](marker)
        mutations.assert_called_once_with(marker, verify.fifo_test)
        verify.write_json(self.path / "observations.json", {
            "scope": "Mocked product work; actual dispatcher executed, no RTL execution",
            "selected_suites": [fn.__name__ for _, fn in capture.batches[0]],
            "selected_stages": [fn.__name__ for _, fn in capture.batches[1]],
            "incomplete_exit_code": exit_code, "incomplete_reason": capture.reason,
            "mutation_suite_forwarded": True,
        })

    def test_oracle_rejects_truncated_suites(self):
        with patch.object(verify, "L1_SUITES", verify.L1_SUITES[:8]):
            capture, exit_code = self.dispatch()
        with self.assertRaises(AssertionError):
            self.assert_contract(capture, exit_code)

    def test_oracle_rejects_compact_stage_substitution(self):
        with patch.object(verify, "OFFICIAL_STAGES",
                          verify.OFFICIAL_STAGES[:4] + (verify.run_shell_scoreboard,)):
            capture, exit_code = self.dispatch()
        with self.assertRaises(AssertionError):
            self.assert_contract(capture, exit_code)

    def test_oracle_rejects_success_for_incomplete_coverage(self):
        capture, exit_code = self.dispatch()
        self.assert_contract(capture, exit_code)
        with self.assertRaises(AssertionError):
            self.assert_contract(capture, 0)

    def test_official_shell_uses_complete_producer_and_full_matrix(self):
        capture = DispatchCapture(self.path)
        producer = self.path / ("complete-table-fixture-" + uuid.uuid4().hex)
        producer.mkdir()
        verify.write_json(self.path / "shell-reference.json", {
            "scope": "Synthetic dispatch fixture only; not tokenizer/model evidence",
        })
        with patch("table_artifacts.complete_tables", return_value=(producer, {})) as tables:
            qwen_shell.run_qwen_shell(capture)
        tables.assert_called_once_with(capture, "qwen")
        self.assertEqual(capture.commands, [([
            "./.venv/bin/python", "tests/qwen_shell.py", capture.relative(self.path),
            "--table-source", capture.relative(producer),
        ], "qwen-shell-reference")])
        cases, = capture.batches
        self.assertEqual([name for name, _ in cases], [
            f"qwen-shell-b{bypass}-s{seed}" for seed in (1, 17, 89) for bypass in (0, 1)
        ])
        with patch.object(qwen_shell, "shell_case") as shell_case:
            for _, case in cases:
                case(capture)
        self.assertEqual([(call.args[2], call.args[3], call.args[4])
                          for call in shell_case.call_args_list],
                         [(seed, bypass, False) for seed in (1, 17, 89) for bypass in (0, 1)])
        verify.write_json(self.path / "observations.json", {
            "scope": "Mocked shell work; no producer or simulation executed",
            "producer_argv": capture.commands[0][0],
            "selected_cases": [name for name, _ in cases],
            "general_only": False,
        })


if __name__ == "__main__":
    OUTPUT = verify.ROOT / sys.argv.pop(1) / ("dispatcher-fixtures-" + uuid.uuid4().hex)
    OUTPUT.mkdir()
    unittest.main(verbosity=2)
