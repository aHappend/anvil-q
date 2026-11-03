"""Validate completed observations before reusing an immutable child result."""

import hashlib
import json
from pathlib import Path

from execution import ROOT, execute, hashes, relative


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024*1024):
            value.update(block)
    return value.hexdigest()


def normalize_argv(argv):
    argv = list(argv)
    if "--output" in argv:
        index = argv.index("--output")
        del argv[index:index + 2]
    return argv


def validated_execution(path, binary, binding, sources, inputs, options):
    """Validate a settled compiled case before rescoring its public output."""
    path = Path(path)
    if not path.is_file():
        return None
    directory = path.parent
    build = json.loads((ROOT/binding).read_text())
    compile_path = ROOT/build["compile_receipt"]
    if not compile_path.is_file():
        return None
    record = json.loads(path.read_text())
    compilation = json.loads(compile_path.read_text())
    current = hashes()
    identity = build["identity"]
    if digest(binary) != build["binary_sha256"]:
        return None
    expected_argv = [relative(binary), f"+vectors={relative(directory/inputs[0].name)}",
                     f"+observations={relative(directory/'observations.txt')}", *options]
    if len(inputs) > 1:
        expected_argv.append(f"+batch={relative(directory/inputs[1].name)}")
    if record.get("argv") != expected_argv or not (directory/"observations.txt").is_file():
        return None
    for fresh in inputs:
        retained = directory/fresh.name
        if not retained.is_file() or digest(retained) != digest(fresh):
            return None
    artifacts = [path, ROOT/binding, binary, compile_path, directory/"observations.txt",
                 *[directory/p.name for p in inputs]]
    for execution in (record, compilation):
        if (execution.get("exit") != 0 or execution.get("timed_out")
                or execution.get("tool_version_exit") != 0
                or execution.get("tool_version", "").strip() != identity["tool_version"]
                or any(execution.get("source_sha256", {}).get(p) != current[p]
                       or identity["source_sha256"].get(p) != current[p] for p in sources)):
            return None
        for key in ("stdout", "stderr"):
            artifact = ROOT/execution[key]
            if (not artifact.is_file()
                    or execution.get("artifact_sha256", {}).get(execution[key]) != digest(artifact)):
                return None
            artifacts.append(artifact)
    ledger = directory/"case.json"
    if ledger.is_file():
        prior = json.loads(ledger.read_text()).get("artifact_sha256", {})
        if not prior or any(not (ROOT/p).is_file() or digest(ROOT/p) != sha
                            for p, sha in prior.items()):
            return None
    return ((ROOT/record["stdout"]).read_text(),
            {relative(p): digest(p) for p in artifacts})


def inventory(output, tools):
    versions = {}
    for tool, argv in tools.items():
        versions[tool] = execute(argv, output, f"version-{tool}", argv).strip()
    return versions


def validated_result(result_path, argv, dependencies, versions, allow_failure=False):
    """Return None for stale/incomplete results; never reuse a partial timeout."""
    result_path = Path(result_path)
    result_path.resolve().relative_to(ROOT)
    directory = result_path.parent
    receipt_path = directory / "receipt.json"
    if not result_path.is_file() or not receipt_path.is_file():
        return None
    result = json.loads(result_path.read_text())
    receipt = json.loads(receipt_path.read_text())
    status = result.get("status")
    if status not in (("passed", "failed") if allow_failure else ("passed",)):
        return None
    if (receipt.get("timed_out") or receipt.get("exit") != int(status != "passed")
            or normalize_argv(receipt.get("argv", [])) != normalize_argv(argv)):
        return None
    current = hashes()
    if any(receipt.get("source_sha256", {}).get(p) != current.get(p)
           for p in dependencies):
        return None
    children = list(directory.rglob("*.receipt.json"))
    tool_receipts = []
    for path in children:
        record = json.loads(path.read_text())
        if "tool_version_argv" not in record:
            continue
        tool = Path(record["tool_version_argv"][0]).name
        if tool not in versions or record.get("tool_version_exit") != 0:
            return None
        if record.get("tool_version", "").strip() != versions[tool]:
            return None
        if record.get("timed_out") or record.get("exit") != 0:
            # Explicit nonzero illegal-parameter rejection is not reusable here.
            return None
        for key in ("stdout", "stderr"):
            artifact = ROOT / record[key]
            if not artifact.is_file():
                return None
            if record.get("artifact_sha256", {}).get(record[key]) != digest(artifact):
                return None
        if any(record.get("source_sha256", {}).get(p) != current.get(p)
               for p in dependencies):
            return None
        tool_receipts.append(relative(path))
    if not tool_receipts:
        return None
    if argv[1] == "tests/run_epilogue.py":
        if (result.get("commands") != 104 or result.get("vectors") != 168
                or not (directory / "observations.txt").is_file()):
            return None
    if argv[1] == "tests/run_unit.py":
        if (not isinstance(result.get("compared"), int) or result["compared"] <= 0
                or result.get("diagnostic_limit") is not None
                or result.get("vector_offset", 0) != 0):
            return None
        if result.get("shards") and sum(row["compared"] for row in result["shards"]) != result["compared"]:
            return None
    return dict(result=result, receipt=relative(receipt_path),
                result_path=relative(result_path), tool_receipts=tool_receipts,
                result_sha256=digest(result_path), receipt_sha256=digest(receipt_path))


def find_result(argv, dependencies, versions, allow_failure=False):
    candidates = []
    for result_path in (ROOT / "evidence/l1").glob("run-*/*/result.json"):
        candidates.append(result_path)
    for result_path in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True):
        bound = validated_result(result_path, argv, dependencies, versions, allow_failure)
        if bound is not None:
            return bound
    return None
