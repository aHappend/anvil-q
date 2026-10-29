"""Fault-injected project snapshot retention; not runtime storage recovery.

Reproduce from the project root:
python3 tests/prepare.py --probe snapshot-retention
Successful finalization must reject incomplete snapshots and unfinished children.
It must also reject missing or changed snapshots and missing raw child evidence.
Live-source drift must reject success without rewriting the retained receipt.
It must also reject the next tool launch before creating a child invocation.
Added public sources must reject both launch and successful finalization.
Handoff fixtures use an isolated project root so both mandatory-check and
preparation output locations exercise the unchanged preparation-only path guard.
These fixtures do not repair missing retained evidence or runtime storage.
Optional --comparison-receipt audits a retained public-source snapshot against
the current handoff, retaining hashes and readable diffs without restoring files.
"""

import argparse
import difflib
import errno
import json
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, Run, sha256, sources, write_json


def handoff_source_comparison(receipt):
    receipt = Path(receipt)
    if receipt.is_absolute() or ".." in receipt.parts:
        raise ValueError("handoff receipt must be project-relative")
    receipt = (ROOT / receipt).resolve()
    receipt.relative_to((ROOT / "evidence/preparation").resolve())
    record = json.loads(receipt.read_text())
    hashes = record.get("source_hashes")
    if record.get("source_snapshot_complete") is not True or not isinstance(hashes, dict) or not hashes:
        raise ValueError("handoff comparison requires a complete nonempty source snapshot")
    live = {str(path.relative_to(ROOT)): path for path in sources()}
    changes, damaged, differences = [], [], []
    for name, digest in sorted(hashes.items()):
        relative = Path(name)
        if (not relative.parts or relative.is_absolute() or ".." in relative.parts or
                relative.parts[0] not in ("rtl", "design", "fpga", "tests", "anvil_q2_reference") or
                set(relative.parts).intersection((".vulcan", ".git", ".tooling", "VULCAN")) or
                not isinstance(digest, str) or len(digest) != 64 or
                any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError("invalid public-source handoff manifest entry: " + name)
        snapshot = receipt.parent / "sources" / relative
        snapshot.resolve().relative_to((receipt.parent / "sources").resolve())
        retained = sha256(snapshot) if snapshot.is_file() else None
        actual = sha256(live[name]) if name in live else None
        if retained != digest:
            damaged.append({"path": name, "recorded_sha256": digest, "snapshot_sha256": retained})
        if actual != digest:
            changes.append({"path": name, "retained_sha256": digest, "live_sha256": actual})
            if retained == digest and name in live:
                before, after = snapshot.read_bytes(), live[name].read_bytes()
                try:
                    old_text, new_text = before.decode("utf-8"), after.decode("utf-8")
                except UnicodeDecodeError:
                    differences.append("Binary source differs: " + name + "\n")
                else:
                    differences.extend(difflib.unified_diff(
                        old_text.splitlines(True), new_text.splitlines(True),
                        fromfile="retained/" + name, tofile="live/" + name))
    added = sorted(set(live) - set(hashes))
    return {"receipt": str(receipt.relative_to(ROOT)),
            "receipt_sha256": sha256(receipt), "retained_status": record.get("status"),
            "status": "different" if changes or damaged or added else "identical",
            "changed_or_missing": changes, "damaged_snapshots": damaged, "added": added,
            "diff": "".join(differences),
            "scope": "read-only source identity; no writer attribution, repair or acceptance"}


def handoff_comparison_sensitivity(folder):
    with patch(__name__ + ".ROOT", folder):
        return _handoff_comparison_fixtures(folder)


def _handoff_comparison_fixtures(folder):
    fixture = folder / "evidence/preparation/handoff-fixture"
    snapshot = fixture / "sources/tests/fixture.py"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_text("# retained handoff fixture\n")
    live = folder / "live-fixture.py"
    live.write_bytes(snapshot.read_bytes())
    receipt = fixture / "receipt.json"
    record = {"source_snapshot_complete": True, "status": "passed",
              "source_hashes": {"tests/fixture.py": sha256(snapshot)}}
    write_json(receipt, record)
    relative = receipt.relative_to(ROOT)
    for rejected_path in (receipt, Path("../receipt.json"),
                          Path("evidence/check-structure/receipt.json")):
        try:
            handoff_source_comparison(rejected_path)
        except ValueError:
            pass
        else:
            raise AssertionError("out-of-scope handoff receipt accepted: " + str(rejected_path))
    # Redirect only the isolated public source name; no shipped file is changed.
    class FixturePath:
        def relative_to(self, root):
            return Path("tests/fixture.py")

        def __fspath__(self):
            return str(live)

        def read_bytes(self):
            return live.read_bytes()

    with patch(__name__ + ".sources", return_value=[FixturePath()]):
        if handoff_source_comparison(relative)["status"] != "identical":
            raise AssertionError("identical handoff rejected")
        live.write_text("# changed handoff fixture\n")
        changed = handoff_source_comparison(relative)
        if (changed["status"] != "different" or len(changed["changed_or_missing"]) != 1 or
                "-# retained handoff fixture" not in changed["diff"] or
                "+# changed handoff fixture" not in changed["diff"]):
            raise AssertionError("changed handoff lost hashes or readable diff")
        live.write_bytes(snapshot.read_bytes())
        snapshot.write_text("# damaged retained fixture\n")
        if len(handoff_source_comparison(relative)["damaged_snapshots"]) != 1:
            raise AssertionError("damaged retained source accepted")
    with patch(__name__ + ".sources", return_value=[]):
        if handoff_source_comparison(relative)["changed_or_missing"][0]["live_sha256"] is not None:
            raise AssertionError("missing handoff source accepted")
    snapshot.write_bytes(live.read_bytes())
    (folder / "added.py").write_text("# added handoff fixture\n")
    with patch(__name__ + ".sources", return_value=[FixturePath(), folder / "added.py"]):
        if handoff_source_comparison(relative)["added"] != [
                str((folder / "added.py").relative_to(ROOT))]:
            raise AssertionError("added handoff source omitted")
    for name in ("", "../rtl/fixture.sv", ".vulcan/state.json", "/rtl/fixture.sv"):
        write_json(receipt, dict(record, source_hashes={name: "0" * 64}))
        try:
            handoff_source_comparison(relative)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid handoff manifest path accepted: " + name)
    write_json(receipt, dict(record, source_snapshot_complete=False))
    try:
        handoff_source_comparison(relative)
    except ValueError:
        pass
    else:
        raise AssertionError("incomplete handoff snapshot accepted")
    return {"identical_control": True,
            "rejected": ["changed-live", "damaged-snapshot", "missing-live", "added-live",
                         "invalid-manifest-path", "incomplete-snapshot",
                         "absolute-receipt", "parent-traversal-receipt",
                         "non-preparation-receipt"],
            "scope": "isolated offline fixtures; not persistence recovery"}


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
    with patch("execution.sources", return_value=[source]):
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
        with patch("execution.sources", return_value=[source]):
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
            with patch("execution.sources", return_value=[source]):
                candidate.finish("passed")
        except AssertionError as exc:
            if "retained verification artifact" not in str(exc):
                raise
        else:
            raise AssertionError("successful finalization accepted " + defect)
        if receipt_path.read_bytes() != before:
            raise AssertionError("rejected retention finalization changed receipt")
        candidate.finish("failed", diagnosis="deliberate offline retention defect: " + defect)
    live_source_defects = ("changed-live-source", "missing-live-source", "added-live-source")
    for defect in live_source_defects:
        live_source = folder / (defect + ".py")
        live_source.write_text("# isolated live-source identity fixture\n")
        with patch("execution.sources", return_value=[live_source]):
            candidate = Run(completion_output, "offline-" + defect)
        selected = [live_source]
        if defect == "changed-live-source":
            live_source.write_text("# changed live-source identity fixture\n")
        elif defect == "missing-live-source":
            live_source.unlink()
        else:
            added = folder / "added-live-source-fixture.py"
            added.write_text("# additional isolated public source\n")
            selected.append(added)
        receipt_path = candidate.path / "receipt.json"
        before = receipt_path.read_bytes()
        try:
            with patch("execution.sources", return_value=selected):
                candidate.finish("passed")
        except AssertionError as exc:
            expected = ("live verification source selection changed during execution"
                        if defect == "added-live-source"
                        else "live verification source changed during execution")
            if expected not in str(exc):
                raise
        else:
            raise AssertionError("successful finalization accepted " + defect)
        if receipt_path.read_bytes() != before:
            raise AssertionError("source-drift rejection changed retained receipt")
        candidate.finish("failed", diagnosis="deliberate offline source drift: " + defect)
    launch_defects = ("changed-live-source", "missing-live-source", "added-live-source",
                      "incomplete-snapshot")
    for defect in launch_defects:
        live_source = folder / ("prelaunch-" + defect + ".py")
        live_source.write_text("# isolated prelaunch identity fixture\n")
        with patch("execution.sources", return_value=[live_source]):
            candidate = Run(completion_output, "offline-prelaunch-" + defect)
        selected = [live_source]
        if defect == "changed-live-source":
            live_source.write_text("# changed before child launch\n")
        elif defect == "missing-live-source":
            live_source.unlink()
        elif defect == "added-live-source":
            added = folder / "prelaunch-added-source-fixture.py"
            added.write_text("# additional isolated prelaunch public source\n")
            selected.append(added)
        else:
            candidate.source_snapshot_complete = False
        receipt_path = candidate.path / "receipt.json"
        before = receipt_path.read_bytes()
        with (patch("execution.subprocess.run") as child,
              patch("execution.sources", return_value=selected)):
            try:
                candidate.tool(["python3", "-c", "print('must not launch')"])
            except AssertionError as exc:
                expected = (
                    "incomplete verification snapshot" if defect == "incomplete-snapshot"
                    else "live verification source selection changed during execution"
                    if defect == "added-live-source"
                    else "live verification source changed during execution")
                if expected not in str(exc):
                    raise
            else:
                raise AssertionError("tool launched despite " + defect)
            child.assert_not_called()
        if (candidate.records or list(candidate.path.glob("tool-*")) or
                receipt_path.read_bytes() != before):
            raise AssertionError("prelaunch rejection changed retained execution evidence")
        candidate.finish("failed", diagnosis="deliberate offline prelaunch defect: " + defect)
    return {"snapshot_failure_propagated": True, "failed_receipt_retained": True,
            "fresh_control_preserved_failure": True,
            "initial_incomplete_receipt_survives_failed_update": True,
            "corrupted_snapshot_rejected": True,
            "incomplete_successful_finalizations_rejected": len(completion_defects),
            "rejected_finalization_preserved_receipt": True,
            "completed_negative_test_preserved": True,
            "retention_defects_rejected": list(retention_defects),
            "live_source_defects_rejected": list(live_source_defects),
            "prelaunch_defects_rejected": list(launch_defects),
            "handoff_comparison": handoff_comparison_sensitivity(folder),
            "scope": "offline project fixtures only; not shared-runtime persistence recovery"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder")
    parser.add_argument("--comparison-receipt")
    args = parser.parse_args()
    folder = Path(args.folder)
    result = snapshot_retention_checks(folder)
    if args.comparison_receipt:
        comparison = handoff_source_comparison(args.comparison_receipt)
        write_json(ROOT / folder / "handoff-comparison.json", comparison)
        result["handoff_comparison_actual"] = comparison
    print(json.dumps(result, sort_keys=True))
    if args.comparison_receipt and comparison["status"] != "identical":
        raise SystemExit(1)
