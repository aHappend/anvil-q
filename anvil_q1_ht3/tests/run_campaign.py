"""Exercise durable retention before any cold rebuild, or seal existing observations."""

import argparse
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import campaign
from execution import ROOT, execute, hashes, relative, remaining, timestamp
from retention import artifacts_intact, digest
from verify import budget_summary


def regression(output):
    assertions = 0
    directory = output / f"synthetic-lifecycle-{uuid.uuid4().hex[:12]}"
    objects = directory / "compile-obj"
    images = directory / "checkpoint-images"
    objects.mkdir(parents=True)
    images.mkdir()
    files = {
        objects / "executable": b"#!/usr/bin/env python3\nprint('synthetic lifecycle 17')\n",
        objects / "driver.cpp": b"synthetic copied driver\n",
        images / "image.bin": bytes(range(256)) * 4096,
        directory / "checkpoint.rtl.bin": b"complete synthetic RTL state\0" * 100,
        directory / "checkpoint.host.bin": b"complete synthetic host state\0" * 100,
        directory / "simulation.stdout.txt": b"synthetic observation; not RTL acceptance\n",
        directory / "simulation.stderr.txt": b"",
        directory / "vectors.txt": b"synthetic fixture bytes\n",
    }
    for path, content in files.items():
        path.write_bytes(content)
    executable = objects / "executable"
    executable.chmod(0o755)
    bindings = {relative(p): digest(p) for p in files}
    receipt = directory / "simulation.receipt.json"
    receipt.write_text(json.dumps(dict(synthetic=True, argv=[relative(executable)],
                                     artifact_sha256=bindings)))
    manifest_path = campaign.preserve([receipt], "synthetic dependency closure")
    manifest = json.loads(manifest_path.read_text())
    if not manifest["complete"] or {r["path"] for r in manifest["files"]} != {
            relative(receipt), *bindings}:
        raise AssertionError("retention dropped a transitive dependency")
    assertions += 1
    for path in files:
        path.unlink()
    if not artifacts_intact(bindings):
        raise AssertionError("exact archives did not survive synthetic reclamation")
    assertions += 1
    restored_paths = []
    for path, content in files.items():
        restored = campaign.artifact(path)
        if (path.exists() or restored == path or restored.read_bytes() != content
                or campaign.logical(restored) != relative(path)):
            raise AssertionError("restoration overwrote evidence or lost its original identity")
        restored_paths.append(relative(restored))
        assertions += 1
    restored_executable = campaign.artifact(executable)
    observed = execute([relative(executable)], directory, "restored-execution",
                       ["python3", "--version"])
    if observed != "synthetic lifecycle 17\n":
        raise AssertionError("restored executable bytes/mode changed")
    assertions += 1
    executed = json.loads((directory/"restored-execution.receipt.json").read_text())
    if (executed["argv"] != [relative(restored_executable)]
            or executed.get("requested_argv") != [relative(executable)]
            or executed["executable_relocation"]["sha256"] != bindings[relative(executable)]):
        raise AssertionError("actual relocated argv and original executable identity were lost")
    assertions += 1
    if campaign.canonical_argv([relative(restored_executable)]) != [relative(executable)]:
        raise AssertionError("relocated argv lost original artifact identity")
    assertions += 1
    # Existing corrupt bytes must never be silently replaced by archived bytes.
    corrupt_path = directory / "vectors.txt"
    corrupt_path.write_bytes(b"synthetic corrupt local bytes")
    if artifacts_intact(bindings):
        raise AssertionError("corrupt existing dependency was hidden by its archive")
    assertions += 1
    row = dict(manifest["files"][0])
    archive = ROOT / row["archive"]
    corrupt_archive = directory / "corrupt.bundle"
    corrupt_archive.write_bytes(archive.read_bytes()[:-1])
    row["archive"] = relative(corrupt_archive)
    try:
        campaign._verify_archive(row)
    except ValueError:
        assertions += 1
    else:
        raise AssertionError("truncated archive accepted")
    wrong_payload = dict(row, archive=relative(archive), sha256="0" * 64)
    try:
        campaign._verify_archive(wrong_payload)
    except ValueError:
        assertions += 1
    else:
        raise AssertionError("wrong decompressed hash accepted")
    missing = directory / "not-produced.bin"
    bad_receipt = directory / "missing.receipt.json"
    bad_receipt.write_text(json.dumps(dict(
        synthetic=True, artifact_sha256={relative(missing): "0" * 64})))
    incomplete = campaign.preserve([bad_receipt], "synthetic missing dependency")
    incomplete_record = json.loads(incomplete.read_text())
    if incomplete_record["complete"] or incomplete_record["missing_dependencies"] != [relative(missing)]:
        raise AssertionError("missing dependency manufactured a complete archive")
    if campaign.available(missing):
        raise AssertionError("missing dependency manufactured bytes")
    assertions += 1
    metadata = directory / "scalar-hash.json"
    metadata.write_text(json.dumps(dict(source_sha256="synthetic scalar provenance")))
    scalar = campaign.preserve([metadata], "synthetic scalar hash metadata")
    if not json.loads(scalar.read_text())["complete"]:
        raise AssertionError("scalar provenance metadata was treated as a dependency map")
    assertions += 1
    malformed = directory / "malformed.json"
    malformed.write_text("synthetic malformed JSON bytes; preserve failure diagnostics")
    malformed_manifest = campaign.preserve([malformed], "synthetic malformed metadata")
    malformed_record = json.loads(malformed_manifest.read_text())
    if (malformed_record["complete"] or len(malformed_record["dependency_parse_errors"]) != 1
            or malformed_record["files"][0]["sha256"] != digest(malformed)):
        raise AssertionError("malformed metadata lost its actual bytes or dependency error")
    assertions += 1
    source = directory / "synthetic-source.py"
    source.write_text("synthetic original source")
    original_sha = digest(source)
    campaign.preserve([source], "synthetic original source snapshot")
    source.write_text("synthetic revised source")
    source_receipt = directory / "source.receipt.json"
    source_receipt.write_text(json.dumps(dict(source_sha256={relative(source): original_sha})))
    source_manifest = campaign.preserve([source_receipt], "synthetic historical source closure")
    source_record = json.loads(source_manifest.read_text())
    if (not source_record["complete"] or source_record["unavailable_source_versions"]
            or not any(r["path"] == relative(source) and r["sha256"] == original_sha
                       for r in source_record["source_snapshots"])):
        raise AssertionError("available exact historical source bytes were lost")
    assertions += 1
    unavailable_receipt = directory / "unavailable-source.receipt.json"
    unavailable_receipt.write_text(json.dumps(dict(
        source_sha256={relative(source): "0" * 64})))
    unavailable_manifest = campaign.preserve([unavailable_receipt], "synthetic absent source")
    unavailable = json.loads(unavailable_manifest.read_text())
    if unavailable["complete"] or unavailable["unavailable_source_versions"] != [
            dict(path=relative(source), sha256="0" * 64)]:
        raise AssertionError("unavailable historical source bytes were manufactured")
    assertions += 1
    row = dict(id="compact-mapped", status="not_started",
               failure_kind="execution_budget_unstarted", available_s=598.39, minimum_s=1800)
    budget = budget_summary([dict(id="synthesis", jobs=[row]),
                             dict(id="performance", status="not_started")])
    if not budget["budget_exhausted"] or budget["unstarted_count"] != 2:
        raise AssertionError("aggregate budget lost allocation-refused rows")
    assertions += 1
    return dict(status="passed", kind="synthetic-campaign-lifecycle", assertions=assertions,
                manifest=relative(manifest_path), restored=restored_paths,
                incomplete_manifest=relative(incomplete), budget_observation=budget,
                scope="retention and scheduling regression only; not RTL acceptance")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--capture", nargs="+")
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_campaign.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    if args.capture:
        manifest = campaign.preserve([ROOT / p for p in args.capture], "existing campaign capture")
        record = json.loads(manifest.read_text())
        result = dict(status="passed" if record["complete"] else "incomplete",
                      manifest=relative(manifest), files=len(record["files"]),
                      missing_dependencies=record["missing_dependencies"],
                      conflicting_dependencies=record["conflicting_dependencies"],
                      unavailable_source_versions=record["unavailable_source_versions"],
                      dependency_parse_errors=record["dependency_parse_errors"],
                      scope="actual retained bytes only; not independent rescoring or acceptance")
    else:
        result = regression(output)
    with (output / "result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(exit=int(result["status"] != "passed"), timed_out=False, end=timestamp(),
                   result=relative(output / "result.json"))
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
