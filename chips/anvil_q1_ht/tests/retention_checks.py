"""Synthetic harness regressions, not storage-repair or RTL acceptance evidence.

Run ``python3 -B tests/retention_checks.py --retained`` for a fresh source-bound
preparation receipt. No historical artifacts are recreated or modified.
"""

import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import retention


class DiagnosisChecks(unittest.TestCase):
    def child(self, discrepancies=(), source_changed=False):
        baseline = {"files": {}, "directories": {}, "live_files": []}
        previous = {
            "probe": "retention", "outcome": "failed",
            "retention": {"baseline": "baseline.json", "baseline_identity": {"id": 1}},
            "source_sha256": {"tests/example.py": "different"} if source_changed else {},
        }
        receipt = Mock()
        receipt.read_text.return_value = json.dumps(previous)
        saved = Mock()
        saved.read_text.return_value = json.dumps(baseline)
        observation = {"phase": "failed_run_later_invocation",
                       "discrepancies": list(discrepancies)}
        stream = io.StringIO()
        with patch.object(retention, "project_file", side_effect=[receipt, saved]), \
                patch.object(retention, "identity", return_value={"id": 1}), \
                patch.object(retention, "workspace_identity", return_value={}), \
                patch.object(retention, "observe") as observe, \
                contextlib.redirect_stdout(stream):
            if discrepancies:
                observe.side_effect = retention.RetentionFailure(observation)
            else:
                observe.return_value = observation
            code = retention.diagnose_child("earlier/receipt.json")
        return code, json.loads(stream.getvalue())

    def test_artifacts_match_is_not_repair_confirmation(self):
        code, result = self.child()
        self.assertEqual(code, 0)
        self.assertEqual(result["outcome"], "artifacts_match")
        self.assertEqual(result["role_handoff_confirmation"],
                         "requires_shared_runtime_confirmation")
        self.assertEqual(result["scope"], "diagnosis_only_not_storage_repair_or_acceptance")

    def test_missing_artifact_fails_and_preserves_observation(self):
        discrepancy = {"path": "earlier/raw.log", "actual": None}
        code, result = self.child([discrepancy])
        self.assertEqual(code, 1)
        self.assertEqual(result["discrepancies"], [discrepancy])
        self.assertEqual(result["outcome"], "discrepancies_found")
        self.assertEqual(result["deleting_actor"], "not_established")

    def test_changed_source_fails_even_with_matching_artifacts(self):
        code, result = self.child(source_changed=True)
        self.assertEqual(code, 1)
        self.assertEqual(result["discrepancies"], [])
        self.assertEqual(result["source_discrepancies"][0]["path"], "tests/example.py")
        self.assertEqual(result["outcome"], "discrepancies_found")

    def test_missing_receipt_fails_without_reconstruction(self):
        stream = io.StringIO()
        with patch.object(retention, "project_file", side_effect=FileNotFoundError), \
                contextlib.redirect_stdout(stream):
            code = retention.diagnose_child("earlier/receipt.json")
        result = json.loads(stream.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(result["outcome"], "missing_prerequisite")
        self.assertEqual(result["discrepancies"][0]["path"], "earlier/receipt.json")

    def test_missing_baseline_records_exact_prerequisite(self):
        previous = {
            "probe": "retention", "outcome": "failed",
            "retention": {"baseline": "earlier/retention-baseline.json"},
        }
        receipt = Mock()
        receipt.read_text.return_value = json.dumps(previous)
        stream = io.StringIO()
        with patch.object(retention, "project_file",
                          side_effect=[receipt, FileNotFoundError]), \
                patch.object(retention, "identity", return_value={"id": 1}), \
                contextlib.redirect_stdout(stream):
            code = retention.diagnose_child("earlier/receipt.json")
        result = json.loads(stream.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(result["earlier_receipt"], "earlier/receipt.json")
        self.assertEqual(result["discrepancies"], [{
            "path": "earlier/retention-baseline.json", "kind": "retention_baseline",
            "expected": "present", "actual": None,
        }])
        self.assertEqual(result["role_handoff_confirmation"],
                         "requires_shared_runtime_confirmation")

    def test_receipt_disappearing_during_read_is_recorded(self):
        receipt = Mock()
        receipt.read_text.side_effect = FileNotFoundError
        stream = io.StringIO()
        with patch.object(retention, "project_file", return_value=receipt), \
                patch.object(retention, "identity", return_value={"id": 1}), \
                contextlib.redirect_stdout(stream):
            code = retention.diagnose_child("earlier/receipt.json")
        result = json.loads(stream.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(result["outcome"], "missing_prerequisite")
        self.assertEqual(result["discrepancies"][0]["kind"], "earlier_receipt")

    def test_missing_workspace_directory_is_explicit(self):
        root = Mock()
        directory = Mock()
        directory.stat.side_effect = FileNotFoundError
        root.__truediv__ = Mock(return_value=directory)
        with patch.object(retention, "ROOT", root):
            result = retention.workspace_identity()
        self.assertEqual(result, {".": None, "evidence": None,
                                  "evidence/preparation": None})

    def test_workspace_loss_becomes_retained_discrepancy(self):
        baseline = {"files": {}, "directories": {}, "live_files": [],
                    "workspace_directories": {"evidence": [1, 2]}}
        with patch.object(retention, "workspace_identity",
                          return_value={"evidence": None}):
            with self.assertRaises(retention.RetentionFailure) as caught:
                retention.observe(baseline, "later_invocation")
        self.assertEqual(caught.exception.observation["discrepancies"], [{
            "path": "evidence", "kind": "workspace_directory",
            "expected": [1, 2], "actual": None,
        }])

    def wrapper(self, result, code):
        evidence = Mock()
        evidence.record = {"observations": [], "commands": [{"exit_code": code}]}
        evidence.command.return_value = json.dumps(result)
        return evidence

    def result(self, outcome="artifacts_match"):
        return {"scope": "diagnosis_only_not_storage_repair_or_acceptance",
                "outcome": outcome, "discrepancies": [], "source_discrepancies": []}

    def test_wrapper_records_failure_before_raising(self):
        result = self.result("missing_prerequisite")
        result["discrepancies"] = [{"path": "earlier/receipt.json", "actual": None}]
        evidence = self.wrapper(result, 1)
        with self.assertRaisesRegex(AssertionError, "missing or changed artifacts"):
            retention.diagnose(evidence, "earlier/receipt.json")
        self.assertEqual(evidence.record["observations"], [result])
        evidence.flush.assert_called_once()
        self.assertEqual(evidence.command.call_args.kwargs["expected_codes"], (0, 1))

    def test_wrapper_rejects_success_exit_with_failure_observation(self):
        evidence = self.wrapper(self.result("discrepancies_found"), 0)
        with self.assertRaisesRegex(AssertionError, "exit disagrees"):
            retention.diagnose(evidence, "earlier/receipt.json")
        self.assertEqual(len(evidence.record["observations"]), 1)

    def test_wrapper_accepts_matching_artifacts_only(self):
        evidence = self.wrapper(self.result(), 0)
        retention.diagnose(evidence, "earlier/receipt.json")
        self.assertEqual(evidence.record["observations"], [self.result()])

    def test_wrapper_rejects_unscoped_output(self):
        result = self.result()
        result["scope"] = "repaired"
        evidence = self.wrapper(result, 0)
        with self.assertRaisesRegex(AssertionError, "missing retention diagnosis scope"):
            retention.diagnose(evidence, "earlier/receipt.json")
        self.assertEqual(evidence.record["observations"], [])


if __name__ == "__main__":
    if sys.argv[1:] == ["--retained"]:
        from verify import Evidence

        evidence = Evidence(
            "retention-harness-regression",
            repair_of="evidence/preparation/verifier-retention-diagnosis-20261028T041107Z-3b0e2178/receipt.json")
        evidence.record["entry_argv"] = ["python3", "-B", "tests/retention_checks.py", "--retained"]
        evidence.flush()
        try:
            evidence.command(["python3", "--version"], "python3-version")
            evidence.command(["python3", "-B", "tests/retention_checks.py"],
                             "retention-harness-regression", timeout=60)
            evidence.record["observations"].append({
                "scope": "synthetic_diagnostic_harness_only_not_storage_repair",
                "compared": "diagnosis child and wrapper success/failure propagation",
                "historical_evidence_modified": False,
            })
        except (OSError, RuntimeError, AssertionError, ValueError) as exc:
            evidence.finish("failed", str(exc))
            raise SystemExit(1)
        evidence.finish("probe_passed", "Synthetic harness regression only; "
                        "storage retention and all product gates remain unverified.")
    else:
        unittest.main()
