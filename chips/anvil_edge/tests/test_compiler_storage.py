"""Small synthetic fixtures; all files remain in a fresh preparation scope."""

import json
from pathlib import Path
import shutil
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
    compiler_object_dir, digest,
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
        self.evidence._parent_budget_s = None
        self.evidence.record = {"children": [], "tool_versions": {}}

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
