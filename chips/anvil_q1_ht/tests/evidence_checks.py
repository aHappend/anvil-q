"""Command evidence regressions; not a storage repair or RTL acceptance check.

Run python3 -B tests/evidence_checks.py --retained for a source-bound receipt.
Synthetic scratch artifacts remain inside that receipt's directory.
"""

import contextlib
import argparse
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify
import persistence
import experiments
import nested_retention
import serialization_events
import campaign_costs


class HistoricalComparisonChecks(unittest.TestCase):
    def setUp(self):
        self.root = SCRATCH / self._testMethodName
        self.root.mkdir(parents=True, exist_ok=False)
        binding = patch.object(campaign_costs, "ROOT", self.root)
        binding.start()
        self.addCleanup(binding.stop)
        self.evidence = SimpleNamespace(
            folder=self.root / "evidence/preparation/current-01234567",
            record={"source_sha256": {"rtl/example.sv": "rtl-hash"}},
            relative=lambda path: str(path.relative_to(self.root)),
            flush=lambda: None,
        )
        self.evidence.folder.mkdir(parents=True)
        self.original = self.root / "evidence/preparation/historical-01234567/receipt.json"
        self.original.parent.mkdir()
        self.fixture = {
            "shape": vars(campaign_costs.MATRIX[0]), "seed": 17, "mode": "AWQ",
            "tokens": [{"expected_logits": [42]}],
        }
        self.child = {
            "probe": "matrix-0-17-awq", "outcome": "probe_passed",
            "start_time": "2026-10-29T00:00:00+00:00",
            "end_time": "2026-10-29T00:00:01+00:00",
            "source_sha256": {"rtl/example.sv": "rtl-hash"},
            "engineering_fixture": self.fixture,
            "commands": [{
                "label": "top-awq-simulation", "argv": ["Vtb"],
                "process_settled": True, "elapsed_seconds": 1,
            }],
            "observations": [{"observed_counters": {"tokens": 1, "logits": 1}}],
            "simulation_builds": [{"key": "build-key", "reused": False}],
        }
        self.original.write_text(json.dumps(self.child))
        campaign_costs.historical_costs(self.evidence)
        self.sample, = self.evidence.record["historical_cost_inventory"]
        self.capture = self.root / self.sample["comparison_receipt"]
        self.fresh = self.evidence.folder / "fresh.json"
        self.fresh.write_text(json.dumps(self.child))
        self.evidence.record["integration_matrix"] = [{
            "receipt": self.evidence.relative(self.fresh),
            "configuration": 0, "seed": 17, "mode": "AWQ",
            "tokens": 1, "ordered_logits": 1,
        }]

    def test_exact_capture_survives_original_loss_without_recreating_it(self):
        self.assertEqual(self.capture.read_bytes(), self.original.read_bytes())
        self.assertEqual(self.evidence.record["runtime_input_sha256"][
            self.sample["comparison_receipt"]], verify.file_sha256(self.capture))
        self.original.unlink()
        campaign_costs.compare_retained(self.evidence)
        comparison, = self.evidence.record["complete_case_comparisons"]
        self.assertEqual(comparison["matching_complete_historical_receipts"],
                         [self.evidence.relative(self.original)])
        matched, = comparison["historical_comparison_inputs"]
        self.assertEqual(matched["original_receipt"], self.evidence.relative(self.original))
        self.assertEqual(matched["captured_receipt"], self.sample["comparison_receipt"])
        self.assertFalse(self.original.exists())

    def test_changed_capture_is_rejected(self):
        self.capture.write_text("{}")
        with self.assertRaisesRegex(AssertionError, "historical comparison receipt changed"):
            campaign_costs.compare_retained(self.evidence)

    def test_missing_capture_does_not_fall_back_to_original(self):
        self.capture.unlink()
        with self.assertRaises(FileNotFoundError):
            campaign_costs.compare_retained(self.evidence)
        self.assertTrue(self.original.exists())
        self.assertFalse(self.capture.exists())

    def test_missing_fresh_result_is_not_replaced_by_history(self):
        self.fresh.unlink()
        with self.assertRaises(FileNotFoundError):
            campaign_costs.compare_retained(self.evidence)

    def test_counter_mismatch_remains_a_failure(self):
        self.child["observations"][-1]["observed_counters"]["tokens"] = 2
        self.fresh.write_text(json.dumps(self.child))
        with self.assertRaisesRegex(AssertionError, "complete-case counters changed"):
            campaign_costs.compare_retained(self.evidence)

    def test_incompatible_historical_sources_are_not_used(self):
        self.evidence.record["historical_cost_inventory"].append({
            **self.sample, "rtl_and_reference_match_current": False,
            "comparison_receipt": "not-captured.json",
        })
        campaign_costs.compare_retained(self.evidence)
        comparison, = self.evidence.record["complete_case_comparisons"]
        self.assertEqual(len(comparison["historical_comparison_inputs"]), 1)


class SupervisionPrerequisiteChecks(unittest.TestCase):
    def test_larger_comparisons_stop_before_evidence_build_or_simulation(self):
        for config in (1, 2):
            for mode in ("AWQ", "BF16"):
                with self.subTest(config=config, mode=mode):
                    diagnostic = io.StringIO()
                    with patch.object(sys, "argv", [
                            "tests/serialization_events.py", "--config", str(config),
                            "--mode", mode]), \
                            patch.object(serialization_events, "Evidence") as evidence, \
                            patch.object(serialization_events, "build") as build, \
                            patch.object(serialization_events, "compare") as compare, \
                            contextlib.redirect_stderr(diagnostic):
                        with self.assertRaises(SystemExit) as caught:
                            serialization_events.main()
                    self.assertEqual(caught.exception.code, 2)
                    for requirement in (
                            "shared-runtime confirmation", "separate-stage supervision",
                            "effective patrol/child limits", "durable evidence retention",
                            "admitted absolute deadline",
                            "independent recovery-plan admission does not establish"):
                        self.assertIn(requirement, diagnostic.getvalue())
                    evidence.assert_not_called()
                    build.assert_not_called()
                    compare.assert_not_called()


class NestedRetentionChecks(unittest.TestCase):
    def setUp(self):
        self.root = SCRATCH / self._testMethodName
        self.root.mkdir(parents=True, exist_ok=False)
        for module in (verify, nested_retention):
            binding = patch.object(module, "ROOT", self.root)
            binding.start()
            self.addCleanup(binding.stop)
        self.evidence = verify.Evidence.__new__(verify.Evidence)
        self.evidence.folder = self.root / "evidence/preparation/parent"
        self.source = self.evidence.folder / "sources/tests/example.py"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("synthetic snapshot\n")
        self.evidence.record = {
            "commands": [], "source_sha256": {
                "tests/example.py": verify.file_sha256(self.source)}}
        self.evidence.create_receipt()
        self.output = io.StringIO()
        redirect = contextlib.redirect_stdout(self.output)
        redirect.__enter__()
        self.addCleanup(redirect.__exit__, None, None, None)
        self.observer = nested_retention.LifecycleObserver(self.evidence)

    def test_normal_receipt_updates_do_not_change_identity(self):
        self.evidence.record["synthetic_update"] = True
        self.evidence.flush()
        self.observer.observe("updated")
        self.assertEqual(self.observer.failures, [])

    def test_missing_receipt_fails_and_is_not_recreated(self):
        path = self.evidence.folder / "receipt.json"
        path.unlink()
        self.observer.observe("lost")
        self.assertFalse(path.exists())
        row, = self.observer.failures[-1]["discrepancies"]
        self.assertEqual(row["path"], "evidence/preparation/parent/receipt.json")
        self.assertEqual(row["errno"], errno.ENOENT)
        self.assertIn('"phase": "lost"', self.output.getvalue())

    def test_changed_source_fails(self):
        self.source.write_text("changed snapshot\n")
        self.observer.observe("changed")
        self.assertEqual(self.observer.failures[-1]["discrepancies"][0]["kind"], "snapshot")

    def test_replaced_source_with_identical_bytes_fails(self):
        replacement = self.source.with_suffix(".replacement")
        replacement.write_bytes(self.source.read_bytes())
        replacement.replace(self.source)
        self.observer.observe("replaced")
        self.assertTrue(self.observer.failures)

    def test_directory_replacement_is_reported(self):
        sources = self.evidence.folder / "sources"
        sources.rename(self.evidence.folder / "preserved-sources")
        sources.mkdir()
        self.observer.observe("directory_replaced")
        self.assertTrue(any(row["kind"] == "directory" for row in
                            self.observer.failures[-1]["discrepancies"]))

    def test_access_denial_is_not_a_success(self):
        with patch.object(self.observer, "file_identity",
                          side_effect=PermissionError(errno.EACCES, "Permission denied")):
            self.observer.observe("denied")
        self.assertTrue(all(row["errno"] == errno.EACCES for row in
                            self.observer.failures[-1]["discrepancies"]))
        self.assertTrue(self.source.exists())

    def test_receipt_contents_and_metadata_are_observed(self):
        self.observer.observe("receipt_state")
        row = self.observer.rows[-1]["targets"][0]["receipt_state"]
        path = self.evidence.folder / "receipt.json"
        self.assertEqual(row["sha256"], verify.file_sha256(path))
        self.assertEqual(row["metadata"]["st_size"], path.stat().st_size)
        self.assertTrue(row["stable_read"])

    def test_live_simulation_and_settlement_are_published(self):
        self.observer.targets[0]["role"] = "child"
        command = {
            "label": "synthetic-simulation", "pid": os.getpid(),
            "argv": ["synthetic-not-executed"], "cwd": ".", "timeout_seconds": 3600,
            "stdout": "synthetic-stdout", "stderr": "synthetic-stderr",
            "timed_out": False}
        self.evidence.record["commands"].append(command)
        self.observer.observe("running")
        self.assertTrue(self.observer.simulation_running_observed)
        command.update(end_time="synthetic", exit_code=0, process_settled=True)
        self.observer.observe("settled")
        rows = [json.loads(line) for line in self.output.getvalue().splitlines()]
        states = [row["command"] for row in rows if row["phase"] == "command_state"]
        self.assertEqual(len(states), 2)
        self.assertEqual(states[0]["argv"], ["synthetic-not-executed"])
        self.assertTrue(states[-1]["process_settled"])
        self.assertEqual(self.observer.failures, [])

    def test_short_functional_simulation_is_not_missed_after_long_compile(self):
        self.observer.stop = Mock()
        self.observer.stop.wait.side_effect = (False, True)
        self.observer.observe = Mock()
        with patch("time.monotonic", side_effect=(0, 120, 121)):
            self.observer.monitor()
        self.assertEqual(self.observer.stop.wait.call_args_list, [call(2), call(2)])
        self.observer.observe.assert_called_once_with("during_child_execution")

    def test_reset_only_simulation_does_not_qualify_functional_observation(self):
        self.observer.targets[0]["role"] = "child"
        self.evidence.record["commands"].append({
            "label": "top-awq-four-state-reset-simulation", "pid": os.getpid(),
            "argv": ["synthetic-not-executed"],
        })
        self.observer.observe("reset_only_running")
        self.assertFalse(self.observer.simulation_running_observed)


class IntegrationProgressChecks(unittest.TestCase):
    def test_diagnostic_selects_exact_case_and_real_matrix_lifecycle(self):
        phases = []
        children = []

        class CaseEvidence:
            def __init__(self, probe=None, source_root=None):
                self.folder = SCRATCH / (probe or "parent")
                self.record = {"observations": []}
                if probe is not None:
                    children.append((probe, source_root))

            def flush(self):
                pass

            def relative(self, path):
                return str(path.relative_to(SCRATCH))

            def finish(self, outcome, reason):
                phases.append(outcome)

        def top(child, mode, seed, config):
            self.assertEqual((mode, seed, config), ("AWQ", 17, 0))
            phases.append("actual_top_probe_entry")
            child.record["observations"].append({"observed_counters": [
                {"position": 0, "logits": 8}, {"position": 0, "logits": 8},
                {"preload_beats": 1, "reads": 1, "logits": 16}]})

        parent = CaseEvidence()
        with patch.object(experiments, "top_probe", side_effect=top) as probe:
            experiments.integration_matrix(
                parent, configurations=(0,), seeds=(17,), modes=("AWQ",),
                lifecycle=lambda phase, child: phases.append(phase))
        probe.assert_called_once()
        self.assertEqual(children, [("matrix-0-17-awq", parent.folder / "sources")])
        self.assertEqual(phases, ["before_child_creation", "after_child_creation",
                                  "actual_top_probe_entry", "probe_passed",
                                  "after_child_finalization"])
        self.assertEqual(len(parent.record["integration_matrix"]), 1)
        self.assertEqual(parent.record["integration_matrix"][0]["ordered_logits"], 16)

    def test_matrix_case_is_recorded_running_before_child_setup(self):
        test = self
        publications = []

        class ProgressEvidence:
            def __init__(self, probe=None, source_root=None):
                if source_root is not None:
                    test.assertEqual(probe, "matrix-0-17-awq")
                    test.assertEqual(source_root, SCRATCH / "matrix/sources")
                    test.assertEqual(publications[-1],
                                     ["running", *["not_run"] * 5])
                    raise RuntimeError("synthetic child setup failure")
                self.folder = SCRATCH / "matrix"
                self.record = {}

            def flush(self):
                publications.append(
                    [case["outcome"] for case in self.record["integration_matrix"]])

        evidence = ProgressEvidence()
        with self.assertRaisesRegex(RuntimeError, "synthetic child setup failure"):
            experiments.integration_matrix(evidence, configurations=(0,))
        self.assertEqual(publications, [
            ["not_run"] * 6, ["running", *["not_run"] * 5]])
        self.assertEqual(evidence.record["integration_matrix"][0]["seed"], 17)
        self.assertEqual(evidence.record["integration_matrix"][0]["mode"], "AWQ")


class PersistenceObservationChecks(unittest.TestCase):
    def observe(self, after=None, named=None):
        baseline = dict(st_dev=1, st_ino=2, st_size=7, st_mtime_ns=10,
                        st_ctime_ns=11, st_mtime=0)
        before = SimpleNamespace(**baseline)
        after = SimpleNamespace(**(baseline | (after or {})))
        named = SimpleNamespace(**(baseline | (named or {})))
        stream = Mock()
        stream.read.return_value = "message"
        path = Mock()
        path.open.return_value.__enter__ = Mock(return_value=stream)
        path.open.return_value.__exit__ = Mock(return_value=False)
        path.stat.return_value = named
        with patch.object(persistence, "project_file", return_value=path), \
                patch.object(persistence.os, "fstat", side_effect=[before, after]), \
                contextlib.redirect_stdout(io.StringIO()):
            return persistence.observe("evidence/preparation/synthetic/message.txt", "test")

    def test_unchanged_open_file_is_readable(self):
        row = self.observe()
        self.assertEqual(row["outcome"], "readable")
        self.assertEqual(row["contents"], "message")
        self.assertEqual(row["mtime_ns"], 10)

    def test_replacement_during_read_is_not_readable(self):
        row = self.observe(named={"st_ino": 3})
        self.assertEqual(row["outcome"], "changed_during_read")
        self.assertEqual(row["read_versions"]["named"]["st_ino"], 3)
        self.assertFalse(persistence.same_file(row, row))

    def test_in_place_change_during_read_is_not_readable(self):
        changed = {"st_mtime_ns": 20, "st_ctime_ns": 21}
        row = self.observe(after=changed, named=changed)
        self.assertEqual(row["outcome"], "changed_during_read")
        self.assertEqual(row["read_versions"]["before"]["st_mtime_ns"], 10)
        self.assertEqual(row["read_versions"]["after"]["st_mtime_ns"], 20)
        self.assertFalse(persistence.same_file(row, row))

    def test_named_file_change_after_read_is_not_readable(self):
        row = self.observe(named={"st_size": 8})
        self.assertEqual(row["outcome"], "changed_during_read")
        self.assertFalse(persistence.same_file(row, row))

    def test_equal_contents_and_mtime_do_not_hide_replacement_between_reads(self):
        first = self.observe()
        second = self.observe()
        for version in second["read_versions"].values():
            version["st_ino"] = 3
        self.assertEqual(first["contents"], second["contents"])
        self.assertEqual(first["mtime_ns"], second["mtime_ns"])
        self.assertFalse(persistence.same_file(first, second))

    def test_unchanged_identity_across_reads_is_accepted(self):
        self.assertTrue(persistence.same_file(self.observe(), self.observe()))

    def test_missing_identity_is_not_success(self):
        row = self.observe()
        del row["read_versions"]
        self.assertFalse(persistence.same_file(row, row))

    def test_changed_ctime_between_reads_is_not_success(self):
        first = self.observe()
        second = self.observe()
        for version in second["read_versions"].values():
            version["st_ctime_ns"] += 1
        self.assertFalse(persistence.same_file(first, second))

    def test_denied_observation_retains_exact_path_and_errno(self):
        relative = "evidence/preparation/synthetic/message.txt"
        failure = PermissionError(errno.EACCES, "Permission denied", relative)
        with patch.object(persistence, "project_file", side_effect=failure), \
                contextlib.redirect_stdout(io.StringIO()):
            row = persistence.observe(relative, "later_verifier_invocation")
        self.assertEqual(row["path"], relative)
        self.assertEqual(row["outcome"], "unavailable")
        self.assertEqual(row["error_type"], "PermissionError")
        self.assertEqual(row["errno"], errno.EACCES)
        self.assertEqual(row["os_error"], "Permission denied")
        self.assertFalse(row["evidence_recreated"])
        self.assertFalse(persistence.same_file(row, row))


class PersistenceWriterChecks(unittest.TestCase):
    def setUp(self):
        self.root = SCRATCH / self._testMethodName
        self.root.mkdir(parents=True, exist_ok=False)
        binding = patch.object(persistence, "ROOT", self.root)
        binding.start()
        self.addCleanup(binding.stop)
        self.relative = "evidence/preparation/observation/message.txt"
        (self.root / self.relative).parent.parent.mkdir(parents=True)

    def test_message_is_complete_before_atomic_publication(self):
        destination = self.root / self.relative
        expected = persistence.MESSAGE + "\nCreation timestamp (UTC): creation\n"
        original_link = Path.hardlink_to
        publications = []

        def publish(path, pending):
            self.assertEqual(path, destination)
            self.assertFalse(destination.exists())
            self.assertEqual(pending.read_text(), expected)
            original_link(path, pending)
            publications.append(destination.read_text())

        with patch.object(persistence, "utc", return_value="creation"), \
                patch.object(persistence.time, "sleep"), \
                patch.object(Path, "hardlink_to", autospec=True, side_effect=publish), \
                contextlib.redirect_stdout(io.StringIO()):
            persistence.writer(self.relative)
        self.assertEqual(publications, [expected])
        self.assertEqual(destination.read_text(), expected)
        self.assertFalse(destination.with_name("message.txt.pending").exists())

    def test_publication_conflict_preserves_both_files(self):
        destination = self.root / self.relative
        original_link = Path.hardlink_to

        def conflict(path, pending):
            path.write_text("existing observation")
            original_link(path, pending)

        with patch.object(persistence.time, "sleep"), \
                patch.object(Path, "hardlink_to", autospec=True, side_effect=conflict), \
                self.assertRaises(FileExistsError):
            persistence.writer(self.relative)
        self.assertEqual(destination.read_text(), "existing observation")
        self.assertTrue(destination.with_name("message.txt.pending").is_file())


class PersistenceAuditChecks(unittest.TestCase):
    def setUp(self):
        self.receipt = "evidence/preparation/synthetic/receipt.json"
        folder = Path(self.receipt).parent
        message = str(folder / "observed/message.txt")
        contents = persistence.MESSAGE + "\nCreation timestamp (UTC): 01\n"
        self.previous = {
            "entry_argv": ["python3", "-B", "tests/persistence.py"], "cwd": ".",
            "observations": [
                {"phase": phase, "outcome": "readable", "path": message,
                 "contents": contents, "mtime_ns": 10, "observation_time": timestamp,
                 "read_versions": {
                     stage: dict(st_dev=1, st_ino=2, st_size=len(contents),
                                 st_mtime_ns=10, st_ctime_ns=11)
                     for stage in ("before", "after", "named")}}
                for phase, timestamp in [
                    ("while_writer_running", "02"),
                    ("after_writer_completion_and_settlement", "04")]],
            "persistence": {"message_path": message}, "observer_errors": [],
            "source_sha256": {
                relative: hashlib.sha256(b"source").hexdigest()
                for relative in (
                    "tests/persistence.py", "rtl/example.sv", "design/SPEC.md",
                    "design/ARCHITECTURE.md", "design/anvil_q1_ht.qsf",
                    "design/anvil_q1_ht.sdc", "anvil_q1_reference/rtl/example.sv")
            },
            "commands": [],
        }
        self.artifacts = {
            str(folder / "sources" / relative): b"source"
            for relative in self.previous["source_sha256"]
        }
        events = [{"event": "created", "path": message, "creation_time": "01"},
                  {"event": "writer_finished", "time": "03"}]
        for label in ("python-version", "bounded-writer"):
            command = {
                "label": label, "exit_code": 0, "timed_out": False,
                "process_settled": True, "cwd": ".",
                "argv": (["python3", "--version"] if label == "python-version" else
                         ["python3", "-B", "tests/persistence.py", "--writer", message]),
            }
            for key in ("stdout", "stderr"):
                name = str(folder / f"{label}-{key}.log")
                raw = (("\n".join(map(json.dumps, events)) + "\n").encode()
                       if label == "bounded-writer" and key == "stdout" else b"")
                self.artifacts[name] = raw
                command.update({key: name, key + "_bytes": len(raw),
                                key + "_sha256": hashlib.sha256(raw).hexdigest()})
            self.previous["commands"].append(command)

    def validate(self):
        def artifact(relative):
            raw = self.artifacts[relative]
            return Mock(read_bytes=Mock(return_value=raw),
                        read_text=Mock(return_value=raw.decode()))
        with patch.object(persistence, "project_file", side_effect=artifact):
            persistence.validate_predecessor(self.previous, self.receipt)

    def test_complete_retained_predecessor_is_accepted(self):
        self.validate()

    def test_each_missing_source_selector_is_rejected(self):
        complete = dict(self.previous["source_sha256"])
        for relative in complete:
            with self.subTest(relative=relative):
                self.previous["source_sha256"] = {
                    name: digest for name, digest in complete.items() if name != relative
                }
                with self.assertRaisesRegex(AssertionError, "source selector is missing"):
                    self.validate()

    def test_runtime_metadata_source_binding_is_rejected(self):
        self.previous["source_sha256"][".vulcan/runtime.json"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "outside deliverable selectors"):
            self.validate()

    def test_wrong_entry_command_is_rejected(self):
        self.previous["entry_argv"] = ["python3", "tests/verify.py"]
        with self.assertRaisesRegex(AssertionError, "invocation differs"):
            self.validate()

    def test_missing_entry_command_is_rejected(self):
        del self.previous["entry_argv"]
        with self.assertRaisesRegex(AssertionError, "invocation differs"):
            self.validate()

    def test_wrong_entry_directory_is_rejected(self):
        self.previous["cwd"] = "tests"
        with self.assertRaisesRegex(AssertionError, "invocation differs"):
            self.validate()

    def test_wrong_child_directory_is_rejected(self):
        self.previous["commands"][-1]["cwd"] = "tests"
        with self.assertRaisesRegex(AssertionError, "finish and settle"):
            self.validate()

    def test_wrong_tool_version_command_is_rejected(self):
        self.previous["commands"][0]["argv"] = ["python3", "other.py"]
        with self.assertRaisesRegex(AssertionError, "tool-version command differs"):
            self.validate()

    def test_changed_log_is_rejected(self):
        self.artifacts[self.previous["commands"][0]["stdout"]] = b"changed"
        with self.assertRaisesRegex(AssertionError, "artifact changed"):
            self.validate()

    def test_changed_source_snapshot_is_rejected(self):
        self.artifacts["evidence/preparation/synthetic/sources/tests/persistence.py"] = b"changed"
        with self.assertRaisesRegex(AssertionError, "artifact changed"):
            self.validate()

    def test_missing_artifact_is_not_recreated(self):
        missing = self.previous["commands"][0]["stderr"]
        with patch.object(persistence, "project_file", side_effect=FileNotFoundError(missing)):
            with self.assertRaises(FileNotFoundError):
                persistence.validate_predecessor(self.previous, self.receipt)

    def test_unsettled_writer_is_rejected(self):
        self.previous["commands"][-1]["process_settled"] = False
        with self.assertRaisesRegex(AssertionError, "finish and settle"):
            self.validate()

    def test_inconsistent_observations_are_rejected(self):
        self.previous["observations"][-1]["mtime_ns"] += 1
        with self.assertRaisesRegex(AssertionError, "consistent"):
            self.validate()

    def test_escaped_log_is_rejected(self):
        self.previous["commands"][0]["stdout"] = "evidence/preparation/other/output.log"
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.validate()

    def test_wrong_temporal_order_is_rejected(self):
        self.previous["observations"][0]["observation_time"] = "05"
        with self.assertRaisesRegex(AssertionError, "trace disagrees"):
            self.validate()

    def test_different_writer_command_is_rejected(self):
        self.previous["commands"][-1]["argv"] = ["python3", "other.py"]
        with self.assertRaisesRegex(AssertionError, "writer command differs"):
            self.validate()

    def audit_later_observation(self, current):
        previous = {
            **self.previous, "probe": "persistence-observation",
            "outcome": "probe_passed",
        }
        evidence = Mock()
        evidence.record = {"observations": []}
        receipt_bytes = json.dumps(previous).encode()
        with patch.object(persistence, "project_file",
                          return_value=Mock(read_bytes=Mock(return_value=receipt_bytes))), \
                patch.object(persistence, "validate_predecessor") as validate, \
                patch.object(persistence, "observe", return_value=current):
            try:
                persistence.audit(evidence, self.receipt)
            finally:
                validate.assert_called_once_with(previous, self.receipt)
                self.assertEqual(evidence.record["observations"], [current])
                self.assertEqual(evidence.record["role_boundary"],
                                 "requires_independent_shared_runtime_confirmation")
                self.assertEqual(evidence.record["predecessor_receipt_sha256"],
                                 hashlib.sha256(receipt_bytes).hexdigest())
                evidence.flush.assert_called()

    def test_later_unchanged_observation_requires_independent_role_confirmation(self):
        self.audit_later_observation(dict(self.previous["observations"][-1],
                                          phase="later_verifier_invocation"))

    def test_later_changed_contents_are_rejected_and_retained(self):
        current = dict(self.previous["observations"][-1], contents="changed",
                       phase="later_verifier_invocation")
        with self.assertRaisesRegex(AssertionError, "later observation differs"):
            self.audit_later_observation(current)

    def test_later_changed_mtime_is_rejected_and_retained(self):
        current = dict(self.previous["observations"][-1], mtime_ns=11,
                       phase="later_verifier_invocation")
        with self.assertRaisesRegex(AssertionError, "later observation differs"):
            self.audit_later_observation(current)

    def test_later_missing_message_is_rejected_and_retained(self):
        current = {"phase": "later_verifier_invocation", "outcome": "missing",
                   "path": self.previous["persistence"]["message_path"]}
        with self.assertRaisesRegex(AssertionError, "later observation differs"):
            self.audit_later_observation(current)

    def test_later_replaced_message_is_rejected_and_retained(self):
        current = dict(self.previous["observations"][-1],
                       phase="later_verifier_invocation")
        current["read_versions"] = {
            stage: dict(version, st_ino=3)
            for stage, version in current["read_versions"].items()}
        with self.assertRaisesRegex(AssertionError, "later observation differs"):
            self.audit_later_observation(current)

    def unavailable_predecessor(self, failure, during_read=False):
        evidence = Mock()
        evidence.record = {"observations": []}
        source = Mock()
        source.read_bytes.side_effect = failure
        with patch.object(persistence, "project_file",
                          **({"return_value": source} if during_read else
                             {"side_effect": failure})), \
                patch.object(persistence, "observe") as observe, \
                patch.object(persistence, "validate_predecessor") as validate:
            with self.assertRaises(type(failure)) as caught:
                persistence.audit(evidence, self.receipt)
        self.assertIs(caught.exception, failure)
        observe.assert_not_called()
        validate.assert_not_called()
        self.assertEqual(evidence.record["predecessor_receipt"], self.receipt)
        self.assertNotIn("predecessor_receipt_sha256", evidence.record)
        self.assertEqual(evidence.record["role_boundary"],
                         "requires_independent_shared_runtime_confirmation")
        self.assertEqual(len(evidence.record["observations"]), 1)
        row = evidence.record["observations"][0]
        self.assertEqual(row["path"], self.receipt)
        self.assertEqual(row["phase"], "audit_prerequisite")
        self.assertEqual(row["error_type"], type(failure).__name__)
        self.assertEqual(row["errno"], failure.errno)
        self.assertFalse(row["evidence_recreated"])
        self.assertEqual(row["scope"],
                         "unavailable_input_not_historical_cause_or_storage_repair")
        self.assertEqual(evidence.flush.call_count, 2)
        return row

    def test_missing_audit_receipt_retains_exact_prerequisite(self):
        row = self.unavailable_predecessor(
            FileNotFoundError(errno.ENOENT, "No such file or directory", self.receipt))
        self.assertEqual(row["outcome"], "missing")

    def test_audit_receipt_disappearing_during_read_is_recorded(self):
        row = self.unavailable_predecessor(
            FileNotFoundError(errno.ENOENT, "No such file or directory", self.receipt),
            during_read=True)
        self.assertEqual(row["outcome"], "missing")

    def test_denied_audit_receipt_retains_os_failure(self):
        row = self.unavailable_predecessor(
            PermissionError(errno.EACCES, "Permission denied", self.receipt))
        self.assertEqual(row["outcome"], "unavailable")
        self.assertEqual(row["os_error"], "Permission denied")


class EntryCommandChecks(unittest.TestCase):
    def test_persistence_invocation_preserves_interpreter_flags(self):
        argv = ["tests/persistence.py", "--audit", "evidence/preparation/earlier/receipt.json"]
        with patch.object(sys, "argv", argv), \
                patch.object(sys, "orig_argv", ["python3", "-B", *argv]):
            self.assertEqual(verify.entry_command(), ["python3", "-B", *argv])

    def test_absolute_script_is_recorded_project_relative(self):
        script = str(verify.ROOT / "tests/verify.py")
        with patch.object(sys, "argv", [script, "--clean-repro"]), \
                patch.object(sys, "orig_argv", [sys.executable, script, "--clean-repro"]):
            self.assertEqual(verify.entry_command(),
                             ["python3", "tests/verify.py", "--clean-repro"])

    def test_external_script_is_rejected(self):
        script = str(verify.ROOT.parent / "outside.py")
        with patch.object(sys, "argv", [script]), \
                patch.object(sys, "orig_argv", [sys.executable, script]):
            with self.assertRaises(ValueError):
                verify.entry_command()


class CommandEvidenceChecks(unittest.TestCase):
    def setUp(self):
        self.root = SCRATCH / self._testMethodName
        self.root.mkdir(parents=True, exist_ok=False)
        self.binding = patch.object(verify, "ROOT", self.root)
        self.binding.start()
        self.addCleanup(self.binding.stop)
        self.evidence = verify.Evidence.__new__(verify.Evidence)
        self.evidence.folder = self.root / "run"
        self.evidence.folder.mkdir()
        self.evidence.record = {"commands": [], "source_sha256": {}}
        self.evidence.create_receipt()

    def test_missing_receipt_is_not_recreated(self):
        path = self.evidence.folder / "receipt.json"
        path.unlink()
        diagnostic = io.StringIO()
        with contextlib.redirect_stderr(diagnostic):
            with self.assertRaises(FileNotFoundError):
                self.evidence.flush()
        self.assertFalse(path.exists())
        event = json.loads(diagnostic.getvalue())
        self.assertEqual(event["event"], "receipt_update_failed")
        self.assertEqual(event["receipt"], "run/receipt.json")
        self.assertEqual(event["errno"], errno.ENOENT)
        self.assertEqual(event["expected_receipt_identity"], {
            "device": self.evidence.receipt_identity[0],
            "inode": self.evidence.receipt_identity[1],
        })
        self.assertFalse(event["evidence_recreated"])
        self.assertFalse(event["acceptance_evidence"])
        self.assertEqual(event["progress_at_failure"]["command_count"], 0)
        self.assertIsNone(event["progress_at_failure"]["last_command"])

    def test_receipt_loss_emits_progress_without_reconstructing_evidence(self):
        record = self.evidence.record
        record.update(
            entry_argv=["python3", "tests/verify.py"], probe="mandatory",
            source_sha256={"rtl/example.sv": "0" * 64},
            mandatory_campaign=[
                {"probe": "dma", "outcome": "completed", "end_time": "earlier"},
                {"probe": "integration-matrix", "outcome": "running", "start_time": "now",
                 "reason": "not part of the bounded diagnostic"},
                {"probe": "synthesis", "outcome": "not_run"},
            ],
        )
        self.command()
        command = dict(record["commands"][-1])
        receipt = self.evidence.folder / "receipt.json"
        receipt.unlink()
        diagnostic = io.StringIO()
        with contextlib.redirect_stderr(diagnostic):
            with self.assertRaises(FileNotFoundError):
                self.evidence.flush()
        event = json.loads(diagnostic.getvalue())
        progress = event["progress_at_failure"]
        self.assertEqual(progress["entry_argv"], ["python3", "tests/verify.py"])
        self.assertEqual(progress["probe"], "mandatory")
        self.assertEqual(progress["command_count"], 1)
        self.assertEqual(progress["last_command"], command)
        self.assertEqual(progress["campaign"], [
            {"probe": "dma", "outcome": "completed", "end_time": "earlier"},
            {"probe": "integration-matrix", "outcome": "running", "start_time": "now"},
            {"probe": "synthesis", "outcome": "not_run"},
        ])
        self.assertEqual(progress["source_binding_count"], 1)
        self.assertEqual(progress["source_bindings_sha256"], hashlib.sha256(
            json.dumps(record["source_sha256"], sort_keys=True).encode()).hexdigest())
        self.assertFalse(receipt.exists())
        self.assertFalse(event["evidence_recreated"])
        self.assertFalse(event["acceptance_evidence"])
        for key in ("stdout", "stderr"):
            raw = (self.root / command[key]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), command[key + "_sha256"])

    def test_receipt_access_denial_preserves_errno_and_original_exception(self):
        path = self.evidence.folder / "receipt.json"
        original = path.read_bytes()
        failure = PermissionError(errno.EACCES, "Permission denied", str(path))
        diagnostic = io.StringIO()
        with patch.object(Path, "open", side_effect=failure), \
                contextlib.redirect_stderr(diagnostic):
            with self.assertRaises(PermissionError) as caught:
                self.evidence.flush()
        self.assertIs(caught.exception, failure)
        self.assertEqual(path.read_bytes(), original)
        event = json.loads(diagnostic.getvalue())
        self.assertEqual(event["error_type"], "PermissionError")
        self.assertEqual(event["errno"], errno.EACCES)
        self.assertEqual(event["os_error"], "Permission denied")
        self.assertEqual(event["receipt"], "run/receipt.json")
        self.assertNotIn(str(self.root), diagnostic.getvalue())
        self.assertFalse(event["evidence_recreated"])

    def test_receipt_loss_retains_nested_matrix_case_not_just_parent_command(self):
        self.command()
        cases = [
            {"configuration": 0, "seed": 17, "mode": "AWQ", "outcome": "compared",
             "receipt": "evidence/preparation/earlier-case/receipt.json",
             "tokens": 2, "ordered_logits": 16, "accepted_DDR_read_beats": 64,
             "initial_preload_beats": 32},
            {"configuration": 0, "seed": 17, "mode": "BF16", "outcome": "running",
             "receipt": "evidence/preparation/active-case/receipt.json"},
            {"configuration": 0, "seed": 89, "mode": "AWQ", "outcome": "not_run"},
        ]
        self.evidence.record["integration_matrix"] = cases
        receipt = self.evidence.folder / "receipt.json"
        receipt.unlink()
        diagnostic = io.StringIO()
        with contextlib.redirect_stderr(diagnostic):
            with self.assertRaises(FileNotFoundError):
                self.evidence.flush()
        event = json.loads(diagnostic.getvalue())
        self.assertEqual(event["progress_at_failure"]["integration_matrix"], cases)
        self.assertEqual(event["progress_at_failure"]["last_command"]["label"],
                         "repeated-label")
        self.assertFalse(receipt.exists())
        self.assertFalse(event["evidence_recreated"])
        self.assertFalse(event["acceptance_evidence"])

    def test_replaced_receipt_is_not_overwritten(self):
        path = self.evidence.folder / "receipt.json"
        path.rename(self.evidence.folder / "original-receipt.json")
        path.write_text("replacement must remain unchanged\n")
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaisesRegex(OSError, "identity changed"):
                self.evidence.flush()
        self.assertEqual(path.read_text(), "replacement must remain unchanged\n")

    def test_receipt_creation_is_exclusive(self):
        path = self.evidence.folder / "receipt.json"
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            self.evidence.create_receipt()
        self.assertEqual(path.read_bytes(), original)

    def command(self, value="original"):
        return self.evidence.command(
            [sys.executable, "-c", f"print({value!r})"], "repeated-label")

    def test_repeated_label_preserves_both_logs(self):
        self.assertEqual(self.command("first"), "first\n")
        self.assertEqual(self.command("second"), "second\n")
        commands = self.evidence.record["commands"]
        self.assertNotEqual(commands[0]["stdout"], commands[1]["stdout"])
        self.assertEqual((self.root / commands[0]["stdout"]).read_text(), "first\n")
        self.assertEqual((self.root / commands[1]["stdout"]).read_text(), "second\n")

    def test_exact_raw_output_hash_and_size(self):
        self.command()
        entry = self.evidence.record["commands"][0]
        for key in ("stdout", "stderr"):
            raw = (self.root / entry[key]).read_bytes()
            self.assertEqual(entry[key + "_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(entry[key + "_bytes"], len(raw))
        self.assertTrue(entry["process_settled"])
        self.assertEqual(entry["exit_code"], 0)

    def test_launch_failure_keeps_raw_files_and_diagnostic(self):
        with self.assertRaisesRegex(RuntimeError, "launch failed"):
            self.evidence.command(["./nonexistent-tool"], "missing-tool")
        entry = self.evidence.record["commands"][0]
        self.assertIsNone(entry["exit_code"])
        self.assertIn("launch_error", entry)
        self.assertTrue((self.root / entry["stdout"]).is_file())
        self.assertTrue((self.root / entry["stderr"]).is_file())

    def test_existing_output_is_not_truncated(self):
        path = self.evidence.folder / "00000-repeated-label-stdout.log"
        path.write_text("preserved\n")
        with self.assertRaisesRegex(RuntimeError, "launch failed"):
            self.command()
        self.assertEqual(path.read_text(), "preserved\n")

    def failed_flush_after_launch(self, failure):
        processes = []
        popen = verify.subprocess.Popen
        flush = self.evidence.flush
        calls = 0

        def launch(*args, **kwargs):
            process = popen(*args, **kwargs)
            processes.append(process)
            return process

        def failing_flush():
            nonlocal calls
            calls += 1
            if calls == 2:
                raise failure
            flush()

        with patch.object(verify.subprocess, "Popen", side_effect=launch), \
                patch.object(self.evidence, "flush", side_effect=failing_flush):
            with self.assertRaises((RuntimeError, ValueError)) as caught:
                self.evidence.command(
                    [sys.executable, "-c", "import time; time.sleep(3600)"],
                    "receipt-failure")
        self.assertEqual(len(processes), 1)
        self.assertIsNotNone(processes[0].poll())
        entry = self.evidence.record["commands"][0]
        self.assertTrue(entry["process_settled"])
        self.assertFalse(entry["timed_out"])
        self.assertNotIn("launch_error", entry)
        for key in ("stdout", "stderr"):
            self.assertTrue((self.root / entry[key]).is_file())
        return entry, caught.exception

    def test_receipt_io_failure_settles_launched_child(self):
        entry, error = self.failed_flush_after_launch(
            FileNotFoundError("synthetic receipt disappearance"))
        self.assertIn("execution failed", str(error))
        self.assertIn("synthetic receipt disappearance", entry["execution_error"])
        self.assertNotEqual(entry["exit_code"], 0)

    def test_receipt_serialization_failure_also_settles_child(self):
        entry, error = self.failed_flush_after_launch(
            ValueError("synthetic receipt serialization failure"))
        self.assertEqual(str(error), "synthetic receipt serialization failure")
        self.assertNotIn("execution_error", entry)

    def test_changed_log_prevents_success(self):
        self.command()
        entry = self.evidence.record["commands"][0]
        (self.root / entry["stdout"]).write_text("changed\n")
        with self.assertRaisesRegex(RuntimeError, "Missing or changed retained"):
            self.evidence.finish("probe_passed", "must not succeed")
        self.assertEqual(json.loads((self.evidence.folder / "receipt.json").read_text())[
            "outcome"], "failed_evidence_changed")

    def test_missing_log_prevents_success_without_reconstruction(self):
        self.command()
        path = self.root / self.evidence.record["commands"][0]["stderr"]
        path.unlink()
        with self.assertRaisesRegex(RuntimeError, "Missing or changed retained"):
            self.evidence.finish("probe_passed", "must not succeed")
        self.assertFalse(path.exists())

    def test_missing_source_snapshot_prevents_success(self):
        self.evidence.record["source_sha256"]["tests/missing.py"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "Missing or changed retained"):
            self.evidence.finish("probe_passed", "must not succeed")

    def test_unchanged_evidence_can_finish(self):
        self.command()
        with contextlib.redirect_stdout(io.StringIO()):
            self.evidence.finish("probe_passed", "synthetic regression only")
        self.assertEqual(self.evidence.record["outcome"], "probe_passed")

    def test_path_escape_label_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "plain filenames"):
            self.evidence.command(["unused"], "../escape")
        self.assertEqual(self.evidence.record["commands"], [])


if __name__ == "__main__":
    if sys.argv[1:2] == ["--retained"]:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--retained", action="store_true")
        parser.add_argument(
            "--repair-of",
            default="evidence/preparation/verifier-retention-handoff-inventory-20261028T042133Z-e1a9dc03/receipt.json")
        args = parser.parse_args()
        evidence = verify.Evidence(
            "command-evidence-regression",
            repair_of=args.repair_of)
        evidence.flush()
        try:
            evidence.command(["python3", "--version"], "python3-version")
            evidence.command(["python3", "-B", "tests/retention_checks.py"],
                             "retention-harness-regression")
            evidence.command(["python3", "-B", "tests/evidence_checks.py", "--scratch",
                              evidence.relative(evidence.folder / "scratch")],
                             "command-evidence-regression")
            evidence.record["observations"].append({
                "scope": "command_harness_only_not_RTL_or_storage_repair",
                "compared": "unique logs, raw hashes, launch failure, child settlement "
                            "on post-launch receipt failure, exclusive receipt creation, "
                            "missing/replaced receipt rejection, fail-closed finalization "
                            "and nested integration-case progress on receipt loss "
                            "and persistence predecessor invocation/cwd/tool-version/"
                            "artifact/settlement/trace validation and fail-closed "
                            "contents/metadata observation across read-time and "
                            "between-observation replacement, including access denial; "
                            "nested lifecycle exact-case selection, receipt updates, "
                            "source/receipt/directory loss or replacement, and immediate "
                            "stdout command/settlement observations (synthetic tests only)",
            })
        except (OSError, RuntimeError, AssertionError, ValueError) as exc:
            evidence.finish("failed", str(exc))
            raise SystemExit(1)
        evidence.finish("probe_passed", "Command evidence regression only; "
                        "cross-role storage persistence and product gates remain unverified.")
    elif len(sys.argv) == 3 and sys.argv[1] == "--scratch":
        SCRATCH = Path(sys.argv[2])
        if SCRATCH.is_absolute() or ".." in SCRATCH.parts:
            raise SystemExit("scratch must be project-relative")
        if not SCRATCH.resolve().is_relative_to(verify.ROOT / "evidence/preparation"):
            raise SystemExit("scratch must be inside project preparation evidence")
        SCRATCH = SCRATCH.resolve()
        sys.argv = sys.argv[:1]
        unittest.main()
    else:
        raise SystemExit("use --retained or --scratch <fresh-project-relative-directory>")
