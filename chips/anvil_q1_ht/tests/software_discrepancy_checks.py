"""Synthetic retained-input preflight checks, not numerical or RTL acceptance."""

import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import software_discrepancy as software


class ReferenceProducerBindingChecks(unittest.TestCase):
    def run_preparation(self, binding_error=None, preparation_error=None):
        evidence = Mock()
        evidence.record = {}
        producer = Mock()
        producer.folder = Path("evidence/preparation/synthetic-01234567")
        producer.relative.side_effect = str
        producer.record = {}
        events = Mock()
        events.attach_mock(producer.finish, "finish")
        events.attach_mock(evidence.bind_child, "bind")
        evidence.bind_child.side_effect = binding_error
        with patch("verify.Evidence", return_value=producer), \
                patch("checkpoint_reference.prepare", side_effect=preparation_error) as prepare, \
                patch.object(software, "measure") as measure:
            events.attach_mock(measure, "measure")
            failure = binding_error or preparation_error
            if failure is None:
                software.prepare_and_measure(evidence, seed=89, smoke=True)
            else:
                with self.assertRaises(type(failure)) as caught:
                    software.prepare_and_measure(evidence, seed=89, smoke=True)
                self.assertIs(caught.exception, failure)
            prepare.assert_called_once_with(producer, smoke=True, seed=89)
        return evidence, producer, events, measure

    def test_finalized_producer_is_bound_before_comparison(self):
        evidence, producer, events, measure = self.run_preparation()
        self.assertEqual([event[0] for event in events.mock_calls],
                         ["finish", "bind", "measure"])
        evidence.bind_child.assert_called_once_with(producer)
        producer.finish.assert_called_once_with(
            "probe_passed", "Integer checkpoint reference; not RTL or board acceptance.")
        measure.assert_called_once_with(
            evidence, str(producer.folder / "checkpoint-reference.json"))

    def test_lost_child_evidence_prevents_comparison_without_refinalizing_child(self):
        evidence, producer, events, measure = self.run_preparation(
            binding_error=FileNotFoundError("synthetic finalized child disappeared"))
        self.assertEqual([event[0] for event in events.mock_calls], ["finish", "bind"])
        evidence.bind_child.assert_called_once_with(producer)
        producer.finish.assert_called_once_with(
            "probe_passed", "Integer checkpoint reference; not RTL or board acceptance.")
        measure.assert_not_called()

    def test_failed_preparation_cannot_be_bound_or_compared(self):
        evidence, producer, events, measure = self.run_preparation(
            preparation_error=ValueError("synthetic reference failure"))
        self.assertEqual([event[0] for event in events.mock_calls], ["finish"])
        producer.finish.assert_called_once_with(
            "probe_failed", "ValueError: synthetic reference failure")
        evidence.bind_child.assert_not_called()
        measure.assert_not_called()


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
                "test_cases": unittest.defaultTestLoader.loadTestsFromModule(
                    sys.modules[__name__]).countTestCases(),
            })
            evidence.finish("probe_passed", "Synthetic input-preflight regression only.")
        except (OSError, RuntimeError, AssertionError, ValueError) as exc:
            evidence.finish("probe_failed", str(exc))
            raise SystemExit(1)
        print(evidence.relative(evidence.folder / "receipt.json"))
    else:
        unittest.main()
