"""Synthetic persistence fixtures; no RTL or historical evidence claims."""

import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify import Evidence, VerificationFailure, digest, write_json


class CaseRecordTests(unittest.TestCase):
    def setUp(self):
        self.path = OUTPUT / (self._testMethodName + "-" + uuid.uuid4().hex)
        self.path.mkdir()
        self.evidence = Evidence.__new__(Evidence)
        self.evidence.path = self.path
        self.evidence.source_overrides = {}
        self.evidence.record = {
            "children": [], "coverage": [], "case_batches": [],
            "source_sha256": {"tests/fixture.py": "a" * 64},
            "tool_versions": {},
        }
        self.evidence._root = self.evidence
        self.evidence._lock = threading.RLock()
        self.evidence._tool_lock = threading.RLock()
        self.evidence._limits = {"workers": 2}
        self.evidence._case_index = 0
        self.evidence._case_scopes = 0
        write_json(self.path / "launch.json", {"synthetic_fixture": True})

    def record(self, case):
        path = ROOT / case["result_record"]
        self.assertEqual(digest(path), case["result_sha256"])
        report = json.loads(path.read_text())
        self.assertFalse(report["acceptance_evidence"])
        self.assertEqual(report["case"], {key: value for key, value in case.items()
                                         if key != "result_sha256"})
        self.assertEqual(report["source_manifest"]["sha256"],
                         digest(self.path / "launch.json"))
        self.assertFalse((ROOT / report["parent_receipt"]).exists())
        return report

    def test_nested_metadata_and_original_failure_survive(self):
        def inner(scope):
            scope.record["observed_counts"] = {"transactions": 7}
            scope.record["coverage"].append({"name": "synthetic", "status": "passed"})

        def outer(scope):
            scope.run_cases([("inner", inner)], workers=1)
            raise VerificationFailure("original failure after settled inner")

        with self.assertRaisesRegex(VerificationFailure, "original failure"):
            self.evidence.run_cases([("outer", outer)], workers=1)
        batches = self.evidence.record["case_batches"]
        self.assertEqual(len(batches), 2)
        outer_case, inner_case = (batch["results"][0] for batch in batches)
        outer_record, inner_record = self.record(outer_case), self.record(inner_case)
        self.assertEqual(outer_record["case"]["status"], "failed")
        self.assertIn("original failure", outer_record["case"]["error"])
        self.assertEqual(inner_record["record"]["observed_counts"], {"transactions": 7})
        self.assertEqual(outer_record["record"]["coverage"],
                         inner_record["record"]["coverage"])
        self.assertEqual(self.evidence._case_scopes, 0)

    def test_peer_settlement_and_records_are_exclusive(self):
        def fail(scope):
            raise VerificationFailure("intentional fixture")

        def pass_case(scope):
            scope.record["completed"] = True

        with self.assertRaisesRegex(VerificationFailure, "intentional fixture"):
            self.evidence.run_cases([("failure", fail), ("peer", pass_case)])
        cases = self.evidence.record["case_batches"][0]["results"]
        self.assertEqual({row["status"] for row in cases}, {"passed", "failed"})
        for case in cases:
            report = self.record(case)
            path = ROOT / case["result_record"]
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                write_json(path, report)
            self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.evidence._case_scopes, 0)

    def test_persistence_denial_is_fatal_but_accounting_settles(self):
        original = write_json

        def deny(path, value):
            if path.name == "case-result.json":
                raise PermissionError("synthetic case-record denial")
            original(path, value)

        with patch("verify.write_json", side_effect=deny):
            with self.assertRaisesRegex(VerificationFailure, "synthetic case-record denial"):
                self.evidence.run_cases([("denied", lambda scope: None)], workers=1)
        batch, = self.evidence.record["case_batches"]
        case, = batch["results"]
        self.assertEqual(batch["status"], "failed")
        self.assertEqual(case["status"], "failed")
        self.assertIn("PermissionError", case["persistence_error"])
        self.assertFalse((ROOT / case["result_record"]).exists())
        self.assertNotIn("result_sha256", case)
        self.assertEqual(self.evidence._case_scopes, 0)

    def test_child_scope_records_do_not_alias_sibling_metadata(self):
        def populate(scope, value):
            scope.record["local_value"] = value
            scope.record["coverage"].append({"value": value})

        self.evidence.run_cases([
            ("one", lambda scope: populate(scope, 1)),
            ("two", lambda scope: populate(scope, 2)),
        ])
        cases = self.evidence.record["case_batches"][0]["results"]
        for case in cases:
            report = self.record(case)
            expected = 1 if case["name"] == "one" else 2
            self.assertEqual(report["record"]["local_value"], expected)
            self.assertEqual(report["record"]["coverage"], [{"value": expected}])
        self.assertNotIn("local_value", self.evidence.record)


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    OUTPUT = ROOT / sys.argv.pop(1) / ("case-record-fixtures-" + uuid.uuid4().hex)
    OUTPUT.mkdir()
    unittest.main()
