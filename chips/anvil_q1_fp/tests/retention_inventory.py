#!/usr/bin/env python3
"""Read-only, non-short-circuit checkpoint inventory diagnosis, not acceptance."""

import argparse
import gzip
import json
from pathlib import Path
import shutil
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import artifact_path, load_json, require, sha
from verify import Evidence, ROOT


def inspect_artifact(root, item):
    path = artifact_path(root, item["path"])
    result = dict(item)
    try:
        before = path.stat()
        result["observed_sha256"] = sha(path)
        after = path.stat()
        stable = ((before.st_size, before.st_mtime_ns, before.st_ino) ==
                  (after.st_size, after.st_mtime_ns, after.st_ino))
        result["status"] = ("changed-during-read" if not stable else
                            "intact" if result["observed_sha256"] == item["sha256"]
                            else "hash-mismatch")
        result["bytes"] = after.st_size
    except FileNotFoundError as error:
        result.update(status="missing", diagnostic=str(error))
    except PermissionError as error:
        result.update(status="access-denied", diagnostic=str(error))
    except OSError as error:
        result.update(status="read-error", diagnostic=str(error))
    return result


def inventory(root, checkpoint):
    checkpoint_path = artifact_path(root, checkpoint)
    try:
        pending = {"path": checkpoint, "sha256": sha(checkpoint_path)}
    except OSError as error:
        failure = {
            "path": checkpoint, "sha256": None,
            "status": ("missing" if isinstance(error, FileNotFoundError) else
                       "access-denied" if isinstance(error, PermissionError) else
                       "read-error"),
            "diagnostic": str(error),
        }
        return {
            "schema": 1, "acceptance_evidence": False,
            "scope": "retained bytes only; not source binding or resume qualification",
            "checkpoint": checkpoint, "segments": [], "ancestry_complete": False,
            "artifacts": [failure], "intact": False, "failures": [failure],
        }
    seen, artifacts, segments = set(), {}, []
    ancestry_complete = True
    while pending is not None:
        name = pending["path"]
        require(name not in seen, "checkpoint ancestry cycle: " + name)
        seen.add(name)
        entry = inspect_artifact(root, pending)
        artifacts[(name, pending["sha256"])] = entry
        if entry["status"] != "intact":
            ancestry_complete = False
            break
        try:
            row = load_json(artifact_path(root, name))
            require(isinstance(row, dict), "checkpoint must be an object")
            require(row["schema"] == 1 and row["acceptance_evidence"] is False,
                    "not an advisory checkpoint")
            binding = row["binding"]
            require(isinstance(binding, dict) and
                    isinstance(binding["inputs"], list) and
                    isinstance(row["artifacts"], list), "invalid artifact inventory")
            segment = {"path": name, "start_cycle": row["start_cycle"],
                       "end_cycle": row["end_cycle"], "status": row["status"],
                       "parent": row["parent"]}
            items = [binding["executable"], *binding["inputs"], *row["artifacts"]]
            items += [row[key] for key in ("state", "paused", "summary") if row[key]]
            references = items + ([row["parent"]] if row["parent"] is not None else [])
            reference_errors = []
            for index, item in enumerate(references):
                try:
                    require(isinstance(item, dict) and
                            isinstance(item.get("path"), str) and
                            isinstance(item.get("sha256"), str),
                            "invalid artifact reference")
                    artifact_path(root, item["path"])
                except ValueError as error:
                    reference_errors.append(f"reference {index}: {error}")
                    continue
                if index < len(items):
                    key = item["path"], item["sha256"]
                    if key not in artifacts:
                        artifacts[key] = inspect_artifact(root, item)
            require(not reference_errors, "; ".join(reference_errors))
        except (ValueError, KeyError, TypeError) as error:
            entry.update(status="invalid-descriptor", diagnostic=str(error))
            ancestry_complete = False
            break
        segments.append(segment)
        pending = row["parent"]
    rows = list(artifacts.values())
    return {"schema": 1, "acceptance_evidence": False,
            "scope": "retained bytes only; not source binding or resume qualification",
            "checkpoint": checkpoint, "segments": segments,
            "ancestry_complete": ancestry_complete,
            "artifacts": rows,
            "intact": ancestry_complete and all(row["status"] == "intact" for row in rows),
            "failures": [row for row in rows if row["status"] != "intact"]}


def selftest(destination):
    from transaction_retention import inspect_trace

    destination.mkdir()
    present = destination / "present"
    present.write_bytes(b"retained fixture\n")
    root = destination.parent
    name = str(present.relative_to(root))
    good = {"path": name, "sha256": sha(present)}
    require(inspect_artifact(root, good)["status"] == "intact", "intact fixture")
    require(inspect_artifact(root, dict(good, sha256="0"*64))["status"] ==
            "hash-mismatch", "corrupt fixture")
    missing = {"path": str((destination / "absent").relative_to(root)),
               "sha256": "0"*64}
    require(inspect_artifact(root, missing)["status"] == "missing", "missing fixture")
    def record(accepted, completed):
        return struct.pack("<11I", accepted, 0, completed, 0, 0, 12, 0, 0, 0, 0, 0)

    valid = record(7, 10) + record(10, 14)
    compressed = gzip.compress(valid, mtime=0)
    damaged = bytearray(compressed)
    damaged[-8] ^= 1
    cases = (
        ("valid", gzip.compress(valid, mtime=0), None),
        ("duplicate", gzip.compress(record(7, 10) * 2, mtime=0),
         "overlapping or out-of-order transaction"),
        ("overlap", gzip.compress(record(7, 10) + record(9, 14), mtime=0),
         "overlapping or out-of-order transaction"),
        ("reordered", gzip.compress(record(10, 14) + record(7, 10), mtime=0),
         "overlapping or out-of-order transaction"),
        ("bad-crc", bytes(damaged), "CRC check failed"),
        ("truncated-header", compressed[:1],
         "Not a gzipped file"),
        ("truncated-payload", compressed[:len(compressed) // 2],
         "Compressed file ended before the end-of-stream marker"),
        ("missing-trailer", compressed[:-8],
         "Compressed file ended before the end-of-stream marker"),
        ("truncated-trailer", compressed[:-1],
         "Compressed file ended before the end-of-stream marker"),
        ("concatenated-overlap",
         gzip.compress(record(7, 10), mtime=0) * 2,
         "overlapping or out-of-order transaction"),
        ("partial-record", gzip.compress(valid + b"x", mtime=0),
         "partial 44-byte transaction record"),
        ("empty", gzip.compress(b"", mtime=0), "empty transaction witness"),
    )
    for name, payload, diagnostic in cases:
        trace = destination / (name + ".gz")
        output = destination / (name + ".json")
        trace.write_bytes(payload)
        try:
            observed = inspect_trace(trace, output)
        except (ValueError, OSError, EOFError) as error:
            require(diagnostic is not None and diagnostic in str(error),
                    name + ": unexpected reader rejection: " + str(error))
            require(not output.exists(), name + ": rejected reader wrote a result")
        else:
            require(diagnostic is None, name + ": invalid trace accepted")
            require(observed["records"] == 2 and observed["reads"] == 2 and
                    observed["gzip_eof_crc_checked"], "valid reader fixture differs")

    # Synthetic ancestry tests never read or repair historical product evidence.
    ancestry = destination / "ancestry"
    ancestry.mkdir()
    def fixture_file(name, data):
        path = ancestry / name
        with path.open("xb") as output:
            output.write(data)
        return {"path": str(path.relative_to(root)), "sha256": sha(path)}

    executable = fixture_file("executable", b"synthetic executable, not runnable\n")
    retained = fixture_file("retained", b"synthetic retained artifact\n")
    absent = {"path": str((ancestry / "missing-trace").relative_to(root)),
              "sha256": "0" * 64}
    binding = {"executable": executable, "inputs": [retained]}
    parent = fixture_file("parent.json", json.dumps({
        "schema": 1, "acceptance_evidence": False, "status": "paused",
        "start_cycle": 0, "end_cycle": 10, "parent": None,
        "binding": binding, "artifacts": [absent],
        "state": None, "paused": None, "summary": None,
    }).encode())
    child = fixture_file("child.json", json.dumps({
        "schema": 1, "acceptance_evidence": False, "status": "paused",
        "start_cycle": 10, "end_cycle": 20, "parent": parent,
        "binding": binding, "artifacts": [],
        "state": None, "paused": None, "summary": None,
    }).encode())
    report = inventory(root, child["path"])
    require(not report["intact"] and report["ancestry_complete"] and
            len(report["segments"]) == 2 and
            [(entry["path"], entry["status"]) for entry in report["failures"]] ==
            [(absent["path"], "missing")],
            "intact child concealed a missing ancestor artifact")
    require(len(report["artifacts"]) == 5,
            "ancestral inventory stopped early or duplicated shared artifacts")
    corrupt = fixture_file("corrupt-parent-child.json", json.dumps({
        "schema": 1, "acceptance_evidence": False, "status": "paused",
        "start_cycle": 10, "end_cycle": 20,
        "parent": dict(parent, sha256="0" * 64),
        "binding": binding, "artifacts": [],
        "state": None, "paused": None, "summary": None,
    }).encode())
    report = inventory(root, corrupt["path"])
    require(not report["intact"] and not report["ancestry_complete"] and
            len(report["segments"]) == 1 and
            [(entry["path"], entry["status"]) for entry in report["failures"]] ==
            [(parent["path"], "hash-mismatch")],
            "corrupt ancestor descriptor accepted or partial inventory lost")
    missing_parent = dict(parent, path=str(
        (ancestry / "missing-parent.json").relative_to(root)))
    missing_child = fixture_file("missing-parent-child.json", json.dumps({
        "schema": 1, "acceptance_evidence": False, "status": "paused",
        "start_cycle": 10, "end_cycle": 20, "parent": missing_parent,
        "binding": binding, "artifacts": [absent],
        "state": None, "paused": None, "summary": None,
    }).encode())
    report = inventory(root, missing_child["path"])
    require(not report["intact"] and not report["ancestry_complete"] and
            len(report["segments"]) == 1 and len(report["artifacts"]) == 5 and
            [(entry["path"], entry["status"]) for entry in report["failures"]] ==
            [(absent["path"], "missing"), (missing_parent["path"], "missing")],
            "missing ancestor concealed child failures or lost partial inventory")
    report = inventory(root, missing_parent["path"])
    require(not report["intact"] and not report["ancestry_complete"] and
            report["segments"] == [] and len(report["artifacts"]) == 1 and
            report["failures"] == report["artifacts"] and
            report["failures"][0]["path"] == missing_parent["path"] and
            report["failures"][0]["status"] == "missing" and
            report["failures"][0]["sha256"] is None,
            "missing starting descriptor lost the structured failure or invented a hash")
    for label, payload in (
        ("malformed-json", b'{"schema":'),
        ("non-object", b"[]"),
        ("missing-binding", json.dumps({
            "schema": 1, "acceptance_evidence": False,
        }).encode()),
        ("invalid-reference", json.dumps({
            "schema": 1, "acceptance_evidence": False, "status": "paused",
            "start_cycle": 0, "end_cycle": 10, "parent": None,
            "binding": binding, "artifacts": [None, absent],
            "state": None, "paused": None, "summary": None,
        }).encode()),
    ):
        invalid = fixture_file(label + ".json", payload)
        descendant = fixture_file(label + "-child.json", json.dumps({
            "schema": 1, "acceptance_evidence": False, "status": "paused",
            "start_cycle": 10, "end_cycle": 20, "parent": invalid,
            "binding": binding, "artifacts": [absent],
            "state": None, "paused": None, "summary": None,
        }).encode())
        for start, expected_segments in ((invalid, 0), (descendant, 1)):
            report = inventory(root, start["path"])
            require(not report["intact"] and not report["ancestry_complete"] and
                    len(report["segments"]) == expected_segments,
                    label + ": malformed descriptor accepted or descendants lost")
            failures = {entry["path"]: entry for entry in report["failures"]}
            require(failures[invalid["path"]]["status"] == "invalid-descriptor" and
                    failures[invalid["path"]]["observed_sha256"] == invalid["sha256"] and
                    bool(failures[invalid["path"]]["diagnostic"]),
                    label + ": malformed descriptor diagnostic/binding lost")
            if label == "invalid-reference":
                require(failures.get(absent["path"], {}).get("status") == "missing",
                        label + ": malformed sibling concealed a missing artifact")
            if expected_segments:
                require(failures[absent["path"]]["status"] == "missing",
                        label + ": previously observed missing artifact lost")
    print(json.dumps({"fixture_comparisons": 3 + len(cases),
                      "ancestry_comparisons": 13,
                      "product_acceptance": False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoints", nargs="*")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--scan", action="store_true")
    mode.add_argument("--selftest", type=Path)
    mode.add_argument("--fixtures-only", action="store_true",
                      help="retain synthetic checker tests without scanning product evidence")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repair-of", type=Path)
    args = parser.parse_args()
    if args.selftest:
        selftest(artifact_path(ROOT, str(args.selftest)))
        return 0
    if args.scan:
        require(len(args.checkpoints) == 1 and args.output is not None,
                "scan requires one checkpoint and an exclusive output path")
        report = inventory(ROOT, args.checkpoints[0])
        with artifact_path(ROOT, str(args.output)).open("x") as output:
            json.dump(report, output, indent=2)
            output.write("\n")
        print(json.dumps({"intact": report["intact"],
                          "ancestry_complete": report["ancestry_complete"],
                          "artifacts": len(report["artifacts"]),
                          "failures": report["failures"]}))
        return 0 if report["intact"] else 1
    require(not args.fixtures_only or not args.checkpoints,
            "fixtures-only cannot inspect product checkpoints")
    require(args.fixtures_only or args.checkpoints,
            "supply explicit checkpoint paths; no evidence discovery")
    ev = Evidence("retention-inventory")
    passed = False
    try:
        if args.fixtures_only:
            ev.receipt["scope"] = (
                "synthetic inventory/reader regressions only; no product evidence "
                "recovery, simulation, resume qualification or acceptance")
        if args.repair_of:
            previous = artifact_path(ROOT, str(args.repair_of))
            require(load_json(previous)["status"] == "failed",
                    "repair receipt did not fail")
            ev.receipt["repair_of"] = {
                "path": str(args.repair_of), "sha256": sha(previous)}
        shutil.copy2(Path(__file__), ev.path / "retention_inventory.py")
        require(ev.run("python-version", [sys.executable, "--version"], timeout=30),
                "Python version query failed")
        fixtures_passed = ev.run("fixtures", [
            sys.executable, "tests/retention_inventory.py", "--selftest",
            str((ev.path / "fixtures").relative_to(ROOT)),
        ])
        ev.assertion("synthetic_inventory_reader_regressions", fixtures_passed,
                     product_acceptance=False)
        require(fixtures_passed, "inventory fixtures failed")
        outcomes = [fixtures_passed]
        for index, checkpoint in enumerate(args.checkpoints):
            report = ev.path / f"inventory-{index}.json"
            succeeded = ev.run(f"inventory-{index}", [
                sys.executable, "tests/retention_inventory.py", "--scan",
                checkpoint, "--output", str(report.relative_to(ROOT)),
            ])
            outcomes.append(succeeded)
            if report.is_file():
                data = load_json(report)
                ev.assertion(f"complete_inventory_{index}", succeeded,
                             report=str(report.relative_to(ROOT)),
                             artifacts=len(data["artifacts"]), failures=data["failures"])
                for number, item in enumerate(data["artifacts"]):
                    if item["status"] != "intact" or not item["path"].endswith(
                            "/transactions.u32.gz"):
                        continue
                    label = f"trace-{index}-{number}"
                    observed = ev.run(label, [
                        sys.executable, "tests/transaction_retention.py", "--inspect",
                        item["path"], "--destination",
                        str((ev.path / (label + ".json")).relative_to(ROOT)),
                    ])
                    outcomes.append(observed)
                    ev.assertion(label + "_independent_eof_crc", observed,
                                 trace=item["path"])
            else:
                ev.assertion(f"complete_inventory_{index}", False,
                             diagnostic="no inventory report; see child logs")
        passed = all(outcomes)
    except (ValueError, OSError, KeyError, TypeError) as error:
        ev.assertion("retention_inventory_failure", False, diagnostic=str(error))
    finally:
        ev.finish("passed" if passed else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT)),
                          "complete_benchmark": False}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
