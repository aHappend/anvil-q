"""Synthetic retained-input preflight checks, not numerical or RTL acceptance."""

import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import software_discrepancy as software


class ReferencePreflightChecks(unittest.TestCase):
    def run_preflight(self, *, missing=False, digest="expected", size=151936 * 4,
                      binding="expected"):
        evidence = Mock()
        evidence.record = {"observations": []}
        transcript = {
            "ordered_logit_vectors": 2,
            "rows": [{"steps": [
                {"ordered_logits": "first.bin", "logits_sha256": "expected"},
                {"ordered_logits": "second.bin", "logits_sha256": "expected"},
            ]}],
        }
        original = copy.deepcopy(transcript)
        bindings = {"first.bin": binding, "second.bin": "expected"}
        digest_results = [FileNotFoundError(), "expected"] if missing else [digest, "expected"]
        sizes = [Mock(st_size=size), Mock(st_size=151936 * 4)]
        error = None
        with patch.object(software, "project_path", side_effect=Path), \
                patch.object(Path, "stat", side_effect=sizes), \
                patch.object(software, "sha", side_effect=digest_results):
            try:
                software.preflight_reference(evidence, transcript, bindings)
            except ValueError as exc:
                error = str(exc)
        self.assertEqual(transcript, original)
        evidence.flush.assert_called_once()
        return evidence.record["observations"][0], error

    def test_complete_inputs_are_read_without_acceptance_claim(self):
        observation, error = self.run_preflight()
        self.assertIsNone(error)
        self.assertEqual(observation["required_vectors"], 2)
        self.assertEqual(observation["read_vectors"], 2)
        self.assertEqual(observation["discrepancies"], [])
        self.assertEqual(observation["scope"],
                         "reference_input_preflight_not_RTL_or_durable_retention")

    def test_missing_input_records_path_and_continues_inventory(self):
        observation, error = self.run_preflight(missing=True)
        self.assertIn("retained inputs were not recreated", error)
        self.assertEqual(observation["read_vectors"], 1)
        self.assertEqual(observation["discrepancies"],
                         [{"path": "first.bin", "reason": "missing"}])

    def test_changed_hash_is_rejected(self):
        observation, error = self.run_preflight(digest="changed")
        self.assertIsNotNone(error)
        self.assertEqual(observation["discrepancies"][0]["actual_sha256"], "changed")

    def test_truncated_vector_is_rejected_even_with_matching_hash(self):
        observation, error = self.run_preflight(size=4)
        self.assertIsNotNone(error)
        self.assertEqual(observation["discrepancies"][0]["actual_bytes"], 4)

    def test_producer_binding_mismatch_is_rejected(self):
        observation, error = self.run_preflight(binding="unbound")
        self.assertIsNotNone(error)
        self.assertEqual(observation["discrepancies"][0]["reason"],
                         "producer_binding_mismatch")
        self.assertEqual(observation["read_vectors"], 1)


if __name__ == "__main__":
    if sys.argv[1:] == ["--retained"]:
        from verify import Evidence

        evidence = Evidence(
            "reference-preflight-regression",
            repair_of="evidence/preparation/verifier-software-discrepancy-20261030T021259Z-092d05ec/receipt.json")
        try:
            evidence.command(["python3", "--version"], "python-version")
            evidence.command(["python3", "-B", "tests/software_discrepancy_checks.py"],
                             "reference-preflight-regression")
            evidence.record["observations"].append({
                "scope": "synthetic_preflight_harness_only_not_reference_or_RTL_acceptance",
                "test_cases": 5,
            })
            evidence.finish("probe_passed", "Synthetic input-preflight regression only.")
        except (OSError, RuntimeError, AssertionError, ValueError) as exc:
            evidence.finish("probe_failed", str(exc))
            raise SystemExit(1)
        print(evidence.relative(evidence.folder / "receipt.json"))
    else:
        unittest.main()
