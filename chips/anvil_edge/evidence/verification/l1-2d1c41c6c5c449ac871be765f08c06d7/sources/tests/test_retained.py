"""Disposable ancestry fixtures, not product verification or restored evidence."""

import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import receipt_graph


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReceiptGraphTests(unittest.TestCase):
    def setUp(self):
        self.root = OUTPUT / self._testMethodName
        self.root.mkdir()

    def receipt(self, name, parents=(), exit_code=0):
        path = self.root / "evidence/preparation" / name / "receipt.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"exit_code": exit_code, "repair_of": list(parents)}))
        return {"path": str(path.relative_to(self.root)), "sha256": digest(path)}

    def audit(self, *links):
        return receipt_graph(self.root, links, digest, RuntimeError)

    def test_failed_predecessor_is_preserved(self):
        failed = self.receipt("failed-01", exit_code=1)
        passed = self.receipt("passed-02", [failed])
        before = (self.root / failed["path"]).read_bytes()
        report = self.audit(passed)
        self.assertTrue(report["historical_provenance_complete"])
        self.assertEqual([row["recorded_exit_code"] for row in report["receipts"]], [0, 1])
        self.assertEqual((self.root / failed["path"]).read_bytes(), before)

    def test_missing_and_changed_are_both_reported(self):
        missing = {"path": "evidence/preparation/missing-01/receipt.json",
                   "sha256": "a" * 64}
        changed = self.receipt("changed-02")
        changed["sha256"] = "b" * 64
        report = self.audit(self.receipt("survivor-03", [missing, changed]))
        self.assertFalse(report["historical_provenance_complete"])
        self.assertEqual({row["issue"] for row in report["gaps"]},
                         {"missing authentic receipt", "receipt hash mismatch"})
        self.assertFalse((self.root / missing["path"]).exists())

    def test_shared_ancestor_is_not_a_cycle(self):
        ancestor = self.receipt("ancestor-01")
        left, right = self.receipt("left-02", [ancestor]), self.receipt("right-03", [ancestor])
        report = self.audit(left, right)
        self.assertTrue(report["historical_provenance_complete"])
        self.assertEqual(len(report["receipts"]), 3)

    def test_conflicting_hash_is_rejected(self):
        link = self.receipt("original-01")
        report = self.audit(link, dict(link, sha256="c" * 64))
        self.assertEqual(report["gaps"][0]["issue"], "conflicting recorded hashes")

    def test_denial_is_not_missing_or_regeneration(self):
        link = self.receipt("denied-01")
        with patch("pathlib.Path.read_bytes", side_effect=PermissionError("fixture denial")):
            with self.assertRaises(PermissionError):
                self.audit(link)

    def test_unsafe_paths_are_rejected(self):
        for name in ("/absolute/receipt.json", "evidence/preparation/../receipt.json",
                     ".vulcan/receipt.json", "tests/data/receipt.json"):
            with self.subTest(path=name), self.assertRaises(RuntimeError):
                self.audit({"path": name, "sha256": "d" * 64})
        outside = self.root / "outside-01"
        outside.mkdir()
        (self.root / "evidence/preparation").mkdir(parents=True)
        (self.root / "evidence/preparation/escape-01").symlink_to(outside.resolve())
        with self.assertRaises(RuntimeError):
            self.audit({"path": "evidence/preparation/escape-01/receipt.json",
                        "sha256": "e" * 64})


if __name__ == "__main__":
    OUTPUT = Path(sys.argv.pop(1)) / "receipt-graph-fixtures"
    OUTPUT.mkdir()
    unittest.main()
