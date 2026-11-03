"""Small synthetic fixtures; all files remain in a fresh preparation scope."""

import json
import os
from pathlib import Path
import shutil
import signal
import sys
import threading
import time
import unittest
from unittest.mock import patch
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scheduling import (
    CompilerStorage, COMPILER_DISK_BYTES, COMPILER_RETAINED_BYTES, DISK_RESERVE_BYTES,
)
from verify import (
    Evidence, ROOT, VerificationFailure, cleanup_compiler_intermediates,
    compiler_object_dir, digest, settle_process_group, write_json,
)


class CompilerStorageTests(unittest.TestCase):
    def setUp(self):
        self.path = OUTPUT / (self._testMethodName + "-" + uuid.uuid4().hex)
        self.path.mkdir()
        self.evidence = Evidence.__new__(Evidence)
        self.evidence.path = self.path
        self.evidence._root = self.evidence
        self.evidence._lock = threading.RLock()
        self.evidence._child_index = 0
        self.evidence._active_children = {}
        self.evidence._peak_children = 0
        self.evidence._case_scopes = 0
        self.evidence._started = time.monotonic()
        self.evidence._parent_budget_s = None
        self.evidence._compiler_storage = CompilerStorage(self.path)
        self.evidence._slots = threading.BoundedSemaphore(2)
        self.evidence.observe_stdout_prefixes = ()
        self.evidence.record = {"children": [], "tool_versions": {"python3": sys.version}}
        write_json(self.path / "launch.json", {
            "argv": [sys.executable, *sys.argv], "cwd": ".",
            "source_sha256": {
                name: digest(ROOT / name) for name in (
                    "tests/verify.py", "tests/scheduling.py", "tests/test_compiler_storage.py")},
            "scope": "Synthetic harness regression only; not RTL acceptance",
        })

    def test_group_disappearance_is_observed_after_kill(self):
        events = []

        def killpg(group, sig):
            events.append((group, sig))
            if len(events) == 4:
                raise ProcessLookupError

        with patch("verify.os.killpg", side_effect=killpg):
            result = settle_process_group(12345)
        self.assertTrue(result["settled"])
        self.assertTrue(result["sigkill_sent"])
        self.assertEqual(result["samples"], 3)
        self.assertEqual(events, [(12345, 0), (12345, signal.SIGKILL),
                                  (12345, 0), (12345, 0)])

    def test_group_deadline_is_not_a_settlement(self):
        with patch("verify.os.killpg") as killpg:
            result = settle_process_group(12345, timeout=0)
        self.assertFalse(result["settled"])
        self.assertTrue(result["sigkill_sent"])
        self.assertEqual(killpg.call_count, 2)

    def test_disappearing_group_signal_race(self):
        with patch("verify.os.killpg",
                   side_effect=[None, ProcessLookupError(), ProcessLookupError()]):
            result = settle_process_group(12345)
        self.assertTrue(result["settled"])
        self.assertFalse(result["sigkill_sent"])
        self.assertEqual(result["samples"], 2)

    def test_retained_growth_and_concurrent_claims(self):
        budget = COMPILER_DISK_BYTES + COMPILER_RETAINED_BYTES
        capacity = 2 * budget + DISK_RESERVE_BYTES
        self.assertGreater(budget, 192 << 20)
        free = [capacity]
        usage = lambda _: shutil._ntuple_diskusage(capacity, capacity - free[0], free[0])
        manager = CompilerStorage(self.path)
        with patch("scheduling.shutil.disk_usage", side_effect=usage):
            with manager.claim(["verilator", "--build"]) as first:
                self.assertEqual(first["reserved_bytes"], budget)
                self.assertEqual(first["retained_growth_budget_bytes"],
                                 COMPILER_RETAINED_BYTES)
                with manager.claim(["iverilog", "-g2012"]) as second:
                    self.assertEqual(second["total_reserved_bytes"], 2 * budget)
                self.assertEqual(manager.reserved, budget)
            self.assertEqual(manager.reserved, 0)
            # Retained bytes from a settled build must reduce the next launch's space.
            free[0] = budget + DISK_RESERVE_BYTES - 1
            with self.assertRaisesRegex(OSError, "no active build"):
                with manager.claim(["verilator", "--build"]):
                    self.fail("An under-capacity compiler launch was admitted")
            with manager.claim(["verilator", "--version"]) as query:
                self.assertIsNone(query)
            self.assertEqual(manager.reserved, 0)

    def test_waiter_rechecks_after_failed_build_release(self):
        budget = COMPILER_DISK_BYTES + COMPILER_RETAINED_BYTES
        capacity = budget + DISK_RESERVE_BYTES
        entered, finished = threading.Event(), threading.Event()
        errors = []
        manager = CompilerStorage(self.path)

        def wait_for_lease():
            try:
                entered.set()
                with manager.claim(["verilator", "--build"]):
                    finished.set()
            except BaseException as error:
                errors.append(error)

        with patch("scheduling.shutil.disk_usage",
                   return_value=shutil._ntuple_diskusage(capacity, 0, capacity)):
            with self.assertRaisesRegex(RuntimeError, "synthetic failed compiler"):
                with manager.claim(["verilator", "--build"]):
                    worker = threading.Thread(target=wait_for_lease)
                    worker.start()
                    self.assertTrue(entered.wait(5))
                    time.sleep(.05)
                    self.assertFalse(finished.is_set())
                    raise RuntimeError("synthetic failed compiler")
            worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        self.assertTrue(finished.is_set())
        self.assertEqual(manager.reserved, 0)

    def test_storage_cancellation_wakes_waiters_and_survives_recovery(self):
        budget = COMPILER_DISK_BYTES + COMPILER_RETAINED_BYTES
        capacity = budget + DISK_RESERVE_BYTES
        manager = CompilerStorage(self.path)
        waiting, finished = threading.Event(), threading.Event()
        errors = []
        original_wait = manager.condition.wait

        def condition_wait(*args, **kwargs):
            waiting.set()
            return original_wait(*args, **kwargs)

        def wait_for_lease():
            try:
                with manager.claim(["verilator", "--build"]):
                    self.fail("Cancelled waiter launched")
            except BaseException as error:
                errors.append(error)
            finally:
                finished.set()

        with patch("scheduling.shutil.disk_usage",
                   return_value=shutil._ntuple_diskusage(capacity, 0, capacity)), patch.object(
                manager.condition, "wait", side_effect=condition_wait):
            with manager.claim(["verilator", "--build"]):
                worker = threading.Thread(target=wait_for_lease)
                worker.start()
                self.assertTrue(waiting.wait(5))
                manager.cancel("original low headroom")
                manager.cancel("secondary allocation failure")
                self.assertTrue(finished.wait(5))
                self.assertEqual(manager.reserved, budget)
            worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertIn("original low headroom", str(errors[0]))
        self.assertEqual(manager.reserved, 0)
        with patch("scheduling.shutil.disk_usage",
                   return_value=shutil._ntuple_diskusage(10 * capacity, 0, 10 * capacity)):
            with self.assertRaisesRegex(OSError, "original low headroom"):
                with manager.claim(["verilator", "--build"]):
                    self.fail("Recovered space silently reopened admission")
        with manager.claim(["verilator", "--version"]) as query:
            self.assertIsNone(query)

    def test_waiting_admission_detects_falling_headroom(self):
        budget = COMPILER_DISK_BYTES + COMPILER_RETAINED_BYTES
        capacity = budget + DISK_RESERVE_BYTES
        manager = CompilerStorage(self.path)
        free = [capacity]
        with patch("scheduling.shutil.disk_usage", side_effect=lambda _: (
                shutil._ntuple_diskusage(capacity, capacity - free[0], free[0]))):
            with manager.claim(["verilator", "--build"]):
                free[0] = DISK_RESERVE_BYTES - 1
                with self.assertRaisesRegex(OSError, "below .* reserve while waiting"):
                    with manager.claim(["verilator", "--build"]):
                        self.fail("Low-space waiter launched")
                self.assertIsNotNone(manager.cancellation_reason())
        self.assertEqual(manager.reserved, 0)

    def test_active_compiler_observes_peer_cancellation_without_object_directory(self):
        compiler = self.path / "iverilog"
        ready = self.path / "active-ready"
        compiler.write_text(
            "#!/usr/bin/env python3\n"
            "from pathlib import Path\n"
            "import sys, time\n"
            "Path(sys.argv[1]).write_text('started')\n"
            "while True: time.sleep(.1)\n", encoding="ascii")
        compiler.chmod(0o755)
        capacity = 4 * (COMPILER_DISK_BYTES + COMPILER_RETAINED_BYTES)
        errors = []

        def active_compiler():
            try:
                self.evidence.child([str(compiler), str(ready)], "active-peer")
            except BaseException as error:
                errors.append(error)

        with patch("verify.shutil.disk_usage",
                   return_value=shutil._ntuple_diskusage(capacity, 0, capacity)):
            worker = threading.Thread(target=active_compiler)
            worker.start()
            try:
                deadline = time.monotonic() + 5
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertTrue(ready.exists())
            finally:
                self.evidence._compiler_storage.cancel("peer filesystem reserve failure")
                worker.join(25)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertIn("peer filesystem reserve failure", str(errors[0]))
        row, = self.evidence.record["children"]
        self.assertEqual(row["exit_code"], -signal.SIGTERM)
        self.assertTrue(row["child_settled"] and row["process_group_settled"])
        self.assertEqual(row["compiler_storage_cancelled"], "peer filesystem reserve failure")
        self.assertNotIn("storage_guard_error", row)
        self.assertFalse(row["timed_out"])
        self.assertEqual(self.evidence._compiler_storage.reserved, 0)

    def descendant_compiler(self, exit_code):
        compiler = self.path / "verilator"
        compiler.write_text(
            "#!/usr/bin/env python3\n"
            "from pathlib import Path\n"
            "import os, signal, subprocess, sys, time\n"
            "p=Path(sys.argv[sys.argv.index('--Mdir')+1]); p.mkdir()\n"
            "for n in ('partial.o','generated.cpp','generated.h','simulation'):\n"
            " (p/n).write_text('synthetic-'+n)\n"
            "code=\"import os, signal, sys, time; from pathlib import Path; \""
            "\"signal.signal(signal.SIGTERM,signal.SIG_IGN); \""
            "\"Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(3600)\"\n"
            "child=subprocess.Popen([sys.executable,'-c',code,str(p/'descendant-ready')])\n"
            "def terminate(sig,frame):\n"
            " print('COMPILER_TERMINATING_WITH_DESCENDANT',flush=True)\n"
            " time.sleep(.2)\n"
            " child.kill(); child.wait()\n"
            " print('DESCENDANT_REAPED',flush=True)\n"
            f" raise SystemExit({exit_code})\n"
            "signal.signal(signal.SIGTERM,terminate)\n"
            "while not (p/'descendant-ready').exists(): time.sleep(.01)\n"
            "(p/'compiler-ready').write_text(str(os.getpid()))\n"
            "print('COMPILER_AND_DESCENDANT_READY',flush=True)\n"
            "while True: time.sleep(.1)\n", encoding="ascii")
        compiler.chmod(0o755)
        return compiler

    def test_falling_headroom_settles_descendants_before_cleanup(self):
        self.falling_headroom_case(23)

    def test_zero_exit_after_storage_failure_preserves_generated_sources(self):
        self.falling_headroom_case(0)

    def falling_headroom_case(self, exit_code):
        compiler = self.descendant_compiler(exit_code)
        objects = self.path / "obj"
        capacity = 4 * (COMPILER_DISK_BYTES + COMPILER_RETAINED_BYTES)
        low_samples = []
        cleanup = cleanup_compiler_intermediates

        def usage(_):
            free = capacity
            if (objects / "compiler-ready").exists():
                free = DISK_RESERVE_BYTES - 1 - len(low_samples)
                low_samples.append(free)
            return shutil._ntuple_diskusage(capacity, capacity - free, free)

        def checked_cleanup(*args, **kwargs):
            leader = int((objects / "compiler-ready").read_text())
            descendant = int((objects / "descendant-ready").read_text())
            with self.assertRaises(ProcessLookupError):
                os.killpg(leader, 0)
            with self.assertRaises(ProcessLookupError):
                os.kill(descendant, 0)
            return cleanup(*args, **kwargs)

        with patch("verify.shutil.disk_usage", side_effect=usage), patch(
                "verify.cleanup_compiler_intermediates", side_effect=checked_cleanup):
            with self.assertRaisesRegex(VerificationFailure, "Filesystem headroom fell"):
                self.evidence.child(
                    [str(compiler), "--Mdir", str(objects.relative_to(ROOT))],
                    "falling-headroom")
        row, = self.evidence.record["children"]
        self.assertEqual(row["exit_code"], exit_code)
        self.assertFalse(row["timed_out"])
        self.assertTrue(row["child_settled"] and row["process_group_settled"])
        self.assertTrue(row["process_group_settlement"]["settled"])
        self.assertIn(str(DISK_RESERVE_BYTES - 1), row["storage_guard_error"])
        self.assertEqual(row["termination_reason"], row["storage_guard_error"])
        self.assertGreaterEqual(len(low_samples), 2)
        self.assertEqual(self.evidence._compiler_storage.reserved, 0)
        self.assertEqual(self.evidence._compiler_storage.cancellation_reason(),
                         row["storage_guard_error"])
        self.assertEqual(len(row["compiler_intermediates_removed"]), 1)
        self.assertIn("DESCENDANT_REAPED", (ROOT / row["stdout"]).read_text())
        self.assertEqual(self.evidence._active_children, {})
        self.assertTrue((ROOT / row["stdout"]).with_name("receipt.json").exists())
        for name in ("generated.cpp", "generated.h", "simulation"):
            self.assertEqual((objects / name).read_text(), "synthetic-" + name)

    def test_unsettled_group_preserves_artifacts_and_cause(self):
        compiler = self.path / "verilator"
        compiler.write_text("#!/usr/bin/env python3\nraise SystemExit(2)\n", encoding="ascii")
        compiler.chmod(0o755)
        objects = self.path / "obj"
        objects.mkdir()
        for name in ("partial.o", "generated.cpp", "simulation"):
            (objects / name).write_bytes(b"retain-unsettled")
        lease = {"reserved_bytes": COMPILER_DISK_BYTES}
        capacity = DISK_RESERVE_BYTES - 1
        with patch("verify.settle_process_group", return_value={
                "settled": False, "samples": 2, "sigkill_sent": True,
                "duration_s": 10, "timeout_s": 10}), patch(
                "verify.shutil.disk_usage",
                return_value=shutil._ntuple_diskusage(capacity, 0, capacity)), patch(
                "verify.cleanup_compiler_intermediates") as cleanup:
            with self.assertRaisesRegex(VerificationFailure, "Filesystem headroom fell"):
                self.evidence._child(
                    [str(compiler), "--Mdir", str(objects.relative_to(ROOT))],
                    "unsettled-observation-control", 3600, False, None, 0, lease)
        cleanup.assert_not_called()
        row, = self.evidence.record["children"]
        self.assertFalse(row["process_group_settled"])
        self.assertTrue(row["child_settled"])
        self.assertIn("Filesystem headroom fell", row["storage_guard_error"])
        self.assertNotIn("compiler_intermediates_removed", row)
        self.assertIsNotNone(self.evidence._compiler_storage.cancellation_reason())
        for name in ("partial.o", "generated.cpp", "simulation"):
            self.assertEqual((objects / name).read_bytes(), b"retain-unsettled")
        receipt = (ROOT / row["stdout"]).with_name("receipt.json")
        self.assertFalse(json.loads(receipt.read_text())["process_group_settled"])
        self.evidence.record.update(coverage=[], case_batches=[], source_sha256={})
        with patch("verify.SELECTORS", ()):
            self.assertEqual(self.evidence.finish(1, row["storage_guard_error"]), 1)
        final = json.loads((self.path / "receipt.json").read_text())
        self.assertIn(row["storage_guard_error"], final["reason"])
        self.assertIn("did not settle", final["reason"])

    def test_failed_compiler_cleanup_preserves_diagnostics(self):
        # A tiny executable named verilator exercises the real settlement and
        # cleanup path, but is deliberately NOT a simulator/functional mutant.
        compiler = self.path / "verilator"
        compiler.write_text(
            "#!/usr/bin/env python3\n"
            "from pathlib import Path\n"
            "import sys\n"
            "p=Path(sys.argv[sys.argv.index('--Mdir')+1]); p.mkdir()\n"
            "for n in ('partial.o','partial.a','partial.fast.gch','partial.d',"
            "'generated.cpp','generated.h','simulation'):\n"
            " (p/n).write_text('synthetic-'+n)\n"
            "print('SYNTHETIC_FAILED_COMPILER',file=sys.stderr)\n"
            "raise SystemExit(2)\n", encoding="ascii")
        compiler.chmod(0o755)
        evidence = self.evidence
        objects = self.path / "obj"
        row = evidence._child(
            [str(compiler), "--Mdir", str(objects.relative_to(ROOT))],
            "synthetic-failure", 3600, True, None, 0)
        self.assertEqual(row["exit_code"], 2)
        self.assertFalse(row["timed_out"])
        self.assertTrue(row["child_settled"] and row["process_group_settled"])
        self.assertEqual(len(row["compiler_intermediates_removed"]), 4)
        self.assertIn("SYNTHETIC_FAILED_COMPILER", (ROOT / row["stderr"]).read_text())
        self.assertGreater(row["compiler_storage_observation"]["peak_object_allocated_bytes"], 0)
        directory = (ROOT / row["stdout"]).parent
        inventory = json.loads((directory / "cleanup-inventory.json").read_text())
        self.assertFalse(inventory["successful_compile"])
        for item in inventory["artifacts"]:
            self.assertFalse((ROOT / item["path"]).exists())
            expected = ("synthetic-" + Path(item["path"]).name).encode()
            import hashlib
            self.assertEqual(item["sha256"], hashlib.sha256(expected).hexdigest())
        self.assertTrue((directory / "receipt.json").exists())
        for name in ("generated.cpp", "generated.h", "simulation"):
            self.assertEqual((objects / name).read_text(), "synthetic-" + name)

    def test_inventory_denial_does_not_remove_anything(self):
        objects = self.path / "obj"
        objects.mkdir()
        artifact = objects / "partial.o"
        artifact.write_bytes(b"retain-on-inventory-failure")
        before = digest(artifact)
        with patch("verify.write_json", side_effect=PermissionError("synthetic denial")):
            with self.assertRaisesRegex(PermissionError, "synthetic denial"):
                cleanup_compiler_intermediates(objects, self.path, success=False)
        self.assertEqual(digest(artifact), before)

    def test_success_cleanup_preserves_binary_and_symlink(self):
        objects = self.path / "obj"
        objects.mkdir()
        for name in ("generated.cpp", "generated.h", "generated.mk", "object.o", "simulation"):
            (objects / name).write_bytes(b"synthetic-success")
        target = self.path / "preserved-source.o"
        target.write_bytes(b"not-a-compiler-intermediate")
        (objects / "linked.o").symlink_to(target)
        binary_hash = digest(objects / "simulation")
        removed = cleanup_compiler_intermediates(objects, self.path, success=True)
        self.assertEqual(len(removed), 4)
        self.assertEqual(digest(objects / "simulation"), binary_hash)
        self.assertTrue((objects / "linked.o").is_symlink())
        self.assertEqual(target.read_bytes(), b"not-a-compiler-intermediate")
        self.assertEqual(compiler_object_dir(
            ["verilator", "--Mdir", str(objects)], ROOT, self.path), objects)
        with self.assertRaises(VerificationFailure):
            compiler_object_dir(["verilator", "--Mdir", str(self.path)], ROOT, self.path)

    def test_make_suppresses_only_unused_pch_targets(self):
        makefile = self.path / "control.mk"
        makefile.write_text(
            "all: normal.o\n"
            "normal.o: Vbench__pch.h.fast.gch Vbench__pch.h.slow.gch\n"
            "\t@printf 'REAL_OBJECT_RULE\\n'\n"
            "Vbench__pch.h.fast.gch Vbench__pch.h.slow.gch:\n"
            "\t@printf 'UNWANTED_PCH_RULE\\n'; exit 2\n", encoding="ascii")
        base = ["make", "--no-print-directory", "-f", str(makefile)]
        for label, flags, expected in (
            ("baseline", [], 2),
            ("no-pch", ["--old-file=Vbench__pch.h.fast.gch",
                        "--old-file=Vbench__pch.h.slow.gch"], 0),
        ):
            row = self.evidence._child(base + flags, label, 3600, True, self.path, 0)
            self.assertEqual(row["exit_code"], expected)
            log = (ROOT / row["stdout"]).read_text()
            if label == "baseline":
                self.assertIn("UNWANTED_PCH_RULE", log)
            else:
                self.assertEqual(log, "REAL_OBJECT_RULE\n")


if __name__ == "__main__":
    OUTPUT = ROOT / sys.argv.pop(1) / ("compiler-storage-fixtures-" + uuid.uuid4().hex)
    OUTPUT.mkdir()
    unittest.main()
