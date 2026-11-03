"""Read-only retained decoder trace comparison and interruption reconciliation.

From the project root, retain a new advisory reconciliation with:
python3 tests/prepare.py --probe receipt-reconciliation --failed-receipt <receipt>

The input must be a decoder preparation receipt beneath evidence/preparation/.
Mandatory-check retention gaps require shared-runtime diagnosis, not this tool.
An incomplete trace remains rejected and a missing tool exit remains unknown.
This command neither resumes simulation nor repairs shared-runtime persistence.
Standard decoder invocations include explicit --asymmetric selections.
"""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decoder_checks import compare_trace, trace_records
from execution import ROOT, sha256
from reference import Fixture, Geometry


def preparation_receipt_path(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to((ROOT / "evidence/preparation").resolve()):
        raise ValueError(
            "decoder reconciliation accepts only evidence/preparation/ receipts; "
            "mandatory-check retention and persistence failures require shared-runtime "
            "diagnosis; no receipt was read or repaired")
    return path


def decoder_preparation_options(argv):
    """Recognize supported retained invocations without executing their arguments."""
    allowed = {"--probe", "--simulator", "--profile", "--banks", "--mode",
               "--tokens", "--seed", "--repair-of", "--asymmetric"}
    options = argv[2:]
    if (argv[:2] != ["python3", "tests/prepare.py"] or len(options) % 2 or
            any(key not in allowed for key in options[::2]) or
            len(set(options[::2])) != len(options[::2])):
        raise AssertionError("reconciliation supports only the standard decoder preparation")
    options = dict(zip(options[::2], options[1::2]))
    if options.get("--probe") != "decoder":
        raise AssertionError("receipt is not a standard decoder preparation")
    if options.get("--asymmetric", "0") not in ("0", "1"):
        raise AssertionError("invalid decoder asymmetric selection")
    return options


def reconcile(value):
    """Recheck retained bytes without inventing a missing simulator exit."""
    path = preparation_receipt_path(value)
    before = sha256(path)
    record = json.loads(path.read_text())
    options = decoder_preparation_options(record["invocation"]["argv"])
    for name, digest in record["source_hashes"].items():
        source = (path.parent / "sources" / name).resolve()
        source.relative_to(path.parent / "sources")
        if sha256(source) != digest:
            raise AssertionError("retained source hash mismatch: " + name)
    for name in ("tests/reference.py", "tests/decoder_checks.py"):
        if sha256(ROOT / name) != record["source_hashes"][name]:
            raise AssertionError("reconciliation requires the unchanged retained oracle: " + name)
    folders = list(path.parent.glob("decoder-*"))
    if len(folders) != 1:
        raise AssertionError("missing/ambiguous retained decoder folder")
    folder = folders[0]
    fixture = json.loads((folder / "fixture.json").read_text())
    inputs = {}
    for name, digest in fixture["inputs"].items():
        source = (folder / name).resolve()
        source.relative_to(folder)
        if sha256(source) != digest:
            raise AssertionError("retained fixture hash mismatch: " + name)
        inputs[name] = digest
    geometry = Geometry(**fixture["geometry"])
    if geometry.INT4_ASYM != int(options.get("--asymmetric", "0")):
        raise AssertionError("retained geometry differs from decoder asymmetric selection")
    model = Fixture(geometry, fixture["seed"])
    if model.digest() != fixture["fixture_sha256"]:
        raise AssertionError("retained fixture differs from regenerated independent model")
    expected = json.loads((folder / "expected.json").read_text())
    if model.oracle(fixture["tokens"]) != expected:
        raise AssertionError("retained expected arrays differ from independent model")
    tools = []
    for child in sorted(path.parent.glob("tool-*")):
        receipt = child / "receipt.json"
        tools.append({
            "directory": str(child.relative_to(ROOT)),
            "receipt_sha256": sha256(receipt) if receipt.is_file() else None,
            "recorded_execution": json.loads(receipt.read_text()) if receipt.is_file() else None,
            "logs": {name: {"sha256": sha256(child / name),
                            "bytes": (child / name).stat().st_size}
                     for name in ("stdout.txt", "stderr.txt") if (child / name).is_file()},
        })
    counts = Counter(fields[0] for fields in trace_records(folder / "trace.tsv"))
    try:
        numerical = {"status": "complete-retained-trace",
                     "result": compare_trace(folder, expected, geometry,
                                             expected_tokens=fixture["tokens"])}
    except AssertionError as exc:
        numerical = {"status": "rejected-retained-trace", "diagnosis": str(exc)}
    if sha256(path) != before:
        raise AssertionError("original receipt changed during read-only reconciliation")
    storage = os.statvfs(ROOT)
    return {
        "receipt": str(path.relative_to(ROOT)), "receipt_sha256": before,
        "recorded_status": record["status"], "original_receipt_unchanged": True,
        "retained_source_hashes_verified": True, "retained_input_hashes": inputs,
        "independent_expected_arrays_regenerated": True,
        "trace_sha256": sha256(folder / "trace.tsv"), "tools": tools,
        "retained_record_counts": dict(counts),
        "numerical_recheck": numerical,
        "execution_outcome": "inconclusive: original execution status is not repaired "
                             "or inferred from trace bytes",
        "available_bytes": storage.f_bavail * storage.f_frsize,
        "available_inodes": storage.f_favail,
        "scope": "advisory reconciliation only; no simulation rerun, original evidence "
                 "rewrite, process settlement, runtime persistence certification or gate acceptance",
    }


def investigate(failed, comparison):
    receipts = [ROOT / value for value in (failed, comparison)]
    for path in receipts:
        path.resolve().relative_to(ROOT / "evidence")
    records = [json.loads(path.read_text()) for path in receipts]
    traces = []
    for path in receipts:
        matches = list(path.parent.glob("decoder-*/trace.tsv"))
        if len(matches) != 1:
            raise AssertionError("investigation requires exactly one retained decoder trace")
        traces.append(matches[0])
    bad, good = [path.read_bytes() for path in traces]
    prefix = 0
    for left, right in zip(bad, good):
        if left != right:
            break
        prefix += 1
    suffix = 0
    for left, right in zip(reversed(bad[prefix:]), reversed(good[prefix:])):
        if left != right:
            break
        suffix += 1
    bad_end, good_end = len(bad) - suffix, len(good) - suffix
    try:
        list(trace_records(traces[0]))
    except AssertionError as exc:
        rejection = str(exc)
    else:
        raise AssertionError("retained failed trace has no malformed record")
    valid_records = sum(1 for _ in trace_records(traces[1]))
    fixture = json.loads((traces[1].parent / "fixture.json").read_text())
    numerical = compare_trace(
        traces[1].parent,
        json.loads((traces[1].parent / "expected.json").read_text()),
        Geometry(**fixture["geometry"]), expected_tokens=fixture["tokens"])
    inputs = {}
    for name in ("fixture.json", "expected.json", "map.tsv", "memory.hex", "tokens.txt"):
        paths = [trace.parent / name for trace in traces]
        inputs[name] = {"sha256": [sha256(path) for path in paths],
                        "identical_bytes": paths[0].read_bytes() == paths[1].read_bytes()}
    for path, record in zip(receipts, records):
        for name, digest in record["source_hashes"].items():
            if sha256(path.parent / "sources" / name) != digest:
                raise AssertionError("retained source snapshot does not match receipt: " + name)
    changes = sorted(name for name in
                     records[0]["source_hashes"].keys() | records[1]["source_hashes"].keys()
                     if records[0]["source_hashes"].get(name) !=
                     records[1]["source_hashes"].get(name))
    storage = os.statvfs(ROOT)
    return {
        "receipts": [{"path": str(path.relative_to(ROOT)), "sha256": sha256(path),
                      "recorded_status": record["status"]}
                     for path, record in zip(receipts, records)],
        "traces": [{"path": str(path.relative_to(ROOT)), "sha256": sha256(path),
                    "bytes": len(data)}
                   for path, data in zip(traces, (bad, good))],
        "unchanged_prefix_bytes": prefix, "unchanged_suffix_bytes": suffix,
        "failed_divergence_bytes": bad_end - prefix,
        "comparison_divergence_bytes": good_end - prefix,
        "single_contiguous_deletion": bad_end == prefix and good_end > prefix,
        "failed_trace_rejection": rejection, "comparison_valid_records": valid_records,
        "retained_comparison_recheck": numerical,
        "retained_inputs": inputs, "source_snapshot_hashes_verified": True,
        "changed_source_paths": changes,
        "available_bytes": storage.f_bavail * storage.f_frsize,
        "available_inodes": storage.f_favail,
        "scope": "advisory retained-byte comparison; no causal attribution, repair of old "
                 "evidence, runtime persistence certification or mandatory-gate acceptance",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--failed")
    parser.add_argument("--comparison")
    parser.add_argument("--reconcile")
    args = parser.parse_args()
    if args.reconcile:
        if args.failed or args.comparison:
            parser.error("--reconcile cannot be combined with trace comparison")
        result = reconcile(args.reconcile)
    else:
        if not args.failed or not args.comparison:
            parser.error("trace comparison requires --failed and --comparison")
        result = investigate(args.failed, args.comparison)
    print(json.dumps(result, indent=2, sort_keys=True))
