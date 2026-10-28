"""Fault-injected project snapshot retention; not runtime storage recovery.

Reproduce from the project root:
python3 tests/prepare.py --probe snapshot-retention
Successful finalization must reject incomplete snapshots and unfinished children.
It must also reject missing or changed snapshots and missing raw child evidence.
Live-source drift must reject success without rewriting the retained receipt.
These fixtures do not repair missing retained evidence or runtime storage.
"""

import errno
import json
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, Run, sha256, write_json


def snapshot_retention_checks(folder):
    folder = (ROOT / folder).resolve()
    folder.relative_to(ROOT)
    folder.mkdir()
    source = folder / "input.py"
    source.write_text("# snapshot retention fixture\n")
    output = folder / "invocations"
    with patch("execution.sources", return_value=[source]), \
            patch("execution.shutil.copyfile",
                  side_effect=OSError(errno.ENOSPC, "injected snapshot disk-full fixture")):
        try:
            Run(output, "offline-snapshot-failure")
        except OSError as exc:
            if exc.errno != errno.ENOSPC:
                raise
        else:
            raise AssertionError("snapshot copy failure did not propagate")
    children = list(output.iterdir())
    if len(children) != 1:
        raise AssertionError("snapshot failure lost its unique invocation directory")
    receipt = children[0] / "receipt.json"
    if not receipt.is_file():
        raise AssertionError("snapshot copy failure left no invocation receipt")
    failed_bytes = receipt.read_bytes()
    record = json.loads(failed_bytes)
    if (record["status"] != "failed" or record["source_snapshot_complete"] is not False or
            "snapshot" not in record["diagnosis"] or record["executions"] != []):
        raise AssertionError("snapshot failure was not explicitly retained")
    with patch("execution.sources", return_value=[source]):
        control = Run(output, "offline-snapshot-control")
        control.finish("passed")
    successful = json.loads((control.path / "receipt.json").read_text())
    relative = str(source.relative_to(ROOT))
    if (successful["source_snapshot_complete"] is not True or
            successful["source_hashes"] != {relative: sha256(source)} or
            (control.path / "sources" / relative).read_bytes() != source.read_bytes()):
        raise AssertionError("successful snapshot changed source identity")
    if receipt.read_bytes() != failed_bytes or control.path == children[0]:
        raise AssertionError("fresh invocation overwrote retained snapshot failure")
    full_output = folder / "full-storage-invocations"
    writes = 0

    def fail_after_initial_receipt(path, record):
        nonlocal writes
        writes += 1
        if writes > 1:
            raise OSError(errno.ENOSPC, "injected receipt disk-full fixture")
        write_json(path, record)

    with patch("execution.sources", return_value=[source]), \
            patch("execution.shutil.copyfile",
                  side_effect=OSError(errno.ENOSPC, "injected snapshot disk-full fixture")), \
            patch("execution.write_json", side_effect=fail_after_initial_receipt):
        try:
            Run(full_output, "offline-snapshot-and-receipt-failure")
        except OSError as exc:
            if exc.errno != errno.ENOSPC:
                raise
        else:
            raise AssertionError("failed receipt update did not propagate")
    retained = list(full_output.glob("*/receipt.json"))
    if len(retained) != 1 or writes != 2:
        raise AssertionError("initial receipt was not retained when storage stayed full")
    initial = json.loads(retained[0].read_text())
    if (initial["status"] != "running" or initial["source_snapshot_complete"] is not False or
            initial["executions"] != []):
        raise AssertionError("incomplete snapshot was reported as complete")
    corrupt_output = folder / "corrupt-copy-invocations"
    copyfile = shutil.copyfile

    def corrupt_copy(src, dst):
        result = copyfile(src, dst)
        Path(dst).write_bytes(b"corrupted snapshot fixture\n")
        return result

    with patch("execution.sources", return_value=[source]), \
            patch("execution.shutil.copyfile", side_effect=corrupt_copy):
        try:
            Run(corrupt_output, "offline-snapshot-copy-corruption")
        except OSError as exc:
            if exc.errno != errno.EIO:
                raise
        else:
            raise AssertionError("corrupted snapshot copy was reported complete")
    corrupt_receipts = list(corrupt_output.glob("*/receipt.json"))
    if len(corrupt_receipts) != 1:
        raise AssertionError("corrupted snapshot lost its unique receipt")
    corrupt_record = json.loads(corrupt_receipts[0].read_text())
    if (corrupt_record["status"] != "failed" or
            corrupt_record["source_snapshot_complete"] is not False or
            corrupt_record["executions"] != [] or
            "hash mismatch" not in corrupt_record["diagnosis"]):
        raise AssertionError("corrupted snapshot failure was not explicitly retained")
    completion_output = folder / "completion-guard-invocations"
    completion_defects = (
        ("incomplete-snapshot", False, []),
        ("unfinished-child", True, [{"exit_code": None, "timeout": False}]),
        ("timed-out-child", True, [{"exit_code": None, "timeout": True}]),
        ("launch-failure", True, [{"exit_code": None, "timeout": False,
                                  "launch_error": "injected launch failure"}]),
    )
    for name, complete, executions in completion_defects:
        with patch("execution.sources", return_value=[source]):
            candidate = Run(completion_output, "offline-" + name)
        candidate.source_snapshot_complete = complete
        candidate.records = executions
        candidate.finish("running")
        path = candidate.path / "receipt.json"
        before = path.read_bytes()
        try:
            candidate.finish("passed")
        except AssertionError as exc:
            if "incomplete verification execution" not in str(exc):
                raise
        else:
            raise AssertionError("successful finalization accepted " + name)
        if path.read_bytes() != before:
            raise AssertionError("rejected finalization changed incomplete receipt")
        candidate.finish("failed", diagnosis="deliberately incomplete offline fixture")
    with patch("execution.sources", return_value=[source]):
        completed = Run(completion_output, "offline-completed-negative-test")
    # Negative tests may deliberately accept a nonzero, completed child exit.
    completed.tool(["python3", "-c", "raise SystemExit(1)"], expected=(1,))
    completed.finish("passed")
    if json.loads((completed.path / "receipt.json").read_text())["status"] != "passed":
        raise AssertionError("completion guard rejected a completed negative test")
    retention_defects = (
        "missing-source", "changed-source", "missing-stdout", "missing-stderr",
        "missing-child-receipt", "changed-child-receipt",
    )
    for defect in retention_defects:
        with patch("execution.sources", return_value=[source]):
            candidate = Run(completion_output, "offline-" + defect)
        candidate.tool(["python3", "-c", "print('retention fixture')"])
        snapshot = candidate.path / "sources" / source.relative_to(ROOT)
        child_receipt = candidate.path / "tool-0000/receipt.json"
        if defect == "missing-source":
            snapshot.unlink()
        elif defect == "changed-source":
            snapshot.write_bytes(b"changed offline snapshot fixture\n")
        elif defect in ("missing-stdout", "missing-stderr"):
            (ROOT / candidate.records[0][defect.removeprefix("missing-")]).unlink()
        elif defect == "missing-child-receipt":
            child_receipt.unlink()
        else:
            changed = dict(candidate.records[0], exit_code=1)
            write_json(child_receipt, changed)
        receipt_path = candidate.path / "receipt.json"
        before = receipt_path.read_bytes()
        try:
            candidate.finish("passed")
        except AssertionError as exc:
            if "retained verification artifact" not in str(exc):
                raise
        else:
            raise AssertionError("successful finalization accepted " + defect)
        if receipt_path.read_bytes() != before:
            raise AssertionError("rejected retention finalization changed receipt")
        candidate.finish("failed", diagnosis="deliberate offline retention defect: " + defect)
    live_source_defects = ("changed-live-source", "missing-live-source")
    for defect in live_source_defects:
        live_source = folder / (defect + ".py")
        live_source.write_text("# isolated live-source identity fixture\n")
        with patch("execution.sources", return_value=[live_source]):
            candidate = Run(completion_output, "offline-" + defect)
        if defect == "changed-live-source":
            live_source.write_text("# changed live-source identity fixture\n")
        else:
            live_source.unlink()
        receipt_path = candidate.path / "receipt.json"
        before = receipt_path.read_bytes()
        try:
            candidate.finish("passed")
        except AssertionError as exc:
            if "live verification source changed during execution" not in str(exc):
                raise
        else:
            raise AssertionError("successful finalization accepted " + defect)
        if receipt_path.read_bytes() != before:
            raise AssertionError("source-drift rejection changed retained receipt")
        candidate.finish("failed", diagnosis="deliberate offline source drift: " + defect)
    return {"snapshot_failure_propagated": True, "failed_receipt_retained": True,
            "fresh_control_preserved_failure": True,
            "initial_incomplete_receipt_survives_failed_update": True,
            "corrupted_snapshot_rejected": True,
            "incomplete_successful_finalizations_rejected": len(completion_defects),
            "rejected_finalization_preserved_receipt": True,
            "completed_negative_test_preserved": True,
            "retention_defects_rejected": list(retention_defects),
            "live_source_defects_rejected": list(live_source_defects),
            "scope": "offline project fixtures only; not shared-runtime persistence recovery"}


if __name__ == "__main__":
    print(json.dumps(snapshot_retention_checks(Path(sys.argv[1])), sort_keys=True))
