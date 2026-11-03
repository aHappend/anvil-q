"""Validate completed observations before reusing an immutable child result."""

import hashlib
import json
from pathlib import Path

from execution import ROOT, execute, hashes, relative
from campaign import artifact as retained_file, available, canonical_argv, logical


def digest(path):
    value = hashlib.sha256()
    with retained_file(path).open("rb") as stream:
        while block := stream.read(1024*1024):
            value.update(block)
    return value.hexdigest()


def artifacts_intact(bindings, required=()):
    """Reclaimed artifacts invalidate a cache candidate, not the current run."""
    if not bindings or any(path not in bindings for path in required):
        return False
    for path, sha in bindings.items():
        artifact = ROOT / path
        artifact.resolve().relative_to(ROOT)
        try:
            matches = available(artifact) and digest(artifact) == sha
        except FileNotFoundError:
            matches = False
        if not matches:
            return False
    return True


def execution_logs_intact(record):
    paths = [record.get(key) for key in ("stdout", "stderr")]
    return (all(isinstance(path, str) for path in paths)
            and artifacts_intact(record.get("artifact_sha256", {}), paths))


def normalize_argv(argv):
    argv = list(argv)
    if "--output" in argv:
        index = argv.index("--output")
        del argv[index:index + 2]
    return argv


def validated_execution(path, binary, binding, sources, inputs, options):
    """Validate a settled compiled case before rescoring its public output."""
    path = Path(path)
    if not available(path):
        return None
    directory = path.parent
    build = json.loads(retained_file(ROOT/binding).read_text())
    compile_path = ROOT/build["compile_receipt"]
    if not available(compile_path):
        return None
    record = json.loads(retained_file(path).read_text())
    compilation = json.loads(retained_file(compile_path).read_text())
    current = hashes()
    identity = build["identity"]
    if digest(binary) != build["binary_sha256"]:
        return None
    executions = [record, compilation]
    artifacts = [path, ROOT/binding, binary, compile_path, directory/"observations.txt",
                 *[directory/p.name for p in inputs]]
    argv = canonical_argv(record.get("argv", []))
    if not argv:
        return None
    executed_binary = argv[0]
    if executed_binary != logical(binary):
        # A reclaimed executable may be rebuilt at a new path, but only identical
        # bytes, sources, parameters, tools and compile arguments permit reuse.
        original_binary = ROOT/executed_binary
        original_binary.resolve().relative_to(ROOT)
        original_binding = original_binary.parent.parent/"binding.json"
        if (original_binary.parent.name != "compile-obj"
                or original_binary.name != binary.name or not available(original_binding)):
            return None
        original_build = json.loads(retained_file(original_binding).read_text())
        original_compile = ROOT/original_build["compile_receipt"]
        if (original_build.get("identity") != identity
                or original_build.get("binary_sha256") != build["binary_sha256"]
                or not available(original_compile)):
            return None
        original_record = json.loads(retained_file(original_compile).read_text())
        def compile_arguments(execution):
            arguments = list(execution.get("argv", []))
            if "--Mdir" in arguments:
                arguments[arguments.index("--Mdir")+1] = "<compile-output>"
            return arguments
        if compile_arguments(original_record) != compile_arguments(compilation):
            return None
        if available(original_binary):
            if digest(original_binary) != build["binary_sha256"]:
                return None
            artifacts.append(original_binary)
        artifacts.extend((original_binding, original_compile))
        executions.append(original_record)
    expected_argv = [executed_binary, f"+vectors={relative(directory/inputs[0].name)}",
                     f"+observations={relative(directory/'observations.txt')}", *options]
    if len(inputs) > 1:
        expected_argv.append(f"+batch={relative(directory/inputs[1].name)}")
    if argv != expected_argv or not available(directory/"observations.txt"):
        return None
    for fresh in inputs:
        retained = directory/fresh.name
        if not available(retained) or digest(retained) != digest(fresh):
            return None
    for execution in executions:
        if (execution.get("exit") != 0 or execution.get("timed_out")
                or execution.get("tool_version_exit") != 0
                or execution.get("tool_version", "").strip() != identity["tool_version"]
                or any(execution.get("source_sha256", {}).get(p) != current[p]
                       or identity["source_sha256"].get(p) != current[p] for p in sources)):
            return None
        for key in ("stdout", "stderr"):
            artifact = ROOT/execution[key]
            if (not available(artifact)
                    or execution.get("artifact_sha256", {}).get(execution[key]) != digest(artifact)):
                return None
            artifacts.append(artifact)
    ledger = directory/"case.json"
    if available(ledger):
        prior = json.loads(retained_file(ledger).read_text()).get("artifact_sha256", {})
        if not prior:
            return None
        for path, sha in prior.items():
            if (path == executed_binary and executed_binary != relative(binary)
                    and not (ROOT/path).is_file()):
                # The build identity, exact compile options and replacement
                # executable bytes were already checked above.
                if sha != build["binary_sha256"]:
                    return None
            elif not available(ROOT/path) or digest(ROOT/path) != sha:
                return None
    return (retained_file(ROOT/record["stdout"]).read_text(),
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
    if not available(result_path) or not available(receipt_path):
        return None
    result = json.loads(retained_file(result_path).read_text())
    receipt = json.loads(retained_file(receipt_path).read_text())
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
    pending, external_tools = [result], set()
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if "artifact_sha256" in value and not artifacts_intact(value["artifact_sha256"]):
                return None
            external_tools.update(ROOT/p for p in value.get("artifact_sha256", {})
                                  if p.endswith(".receipt.json"))
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    if len(argv) > 1 and argv[1] == "tests/run_stream_checkpoint.py":
        from official_stream import intact, validated_chain
        streams = result.get("streams", [])
        if len(streams) != 2 or result.get("bit_identical_vectors") != 2:
            return None
        for paths in streams:
            if not paths or not available(ROOT/paths[-1]):
                return None
            identity = json.loads(retained_file(ROOT/paths[-1]).read_text())["identity"]
            binary = ROOT/identity["binary"]
            build_path = binary.parent.parent/"binding.json"
            image = ROOT/identity["image"]
            if (not available(build_path) or digest(build_path) != identity["build_binding_sha256"]
                    or not available(binary) or digest(binary) != identity["binary_sha256"]
                    or not available(image) or digest(image) != identity["image_sha256"]):
                return None
            build = json.loads(retained_file(build_path).read_text())
            if not intact(build) or any(
                    current.get(p) != sha for p, sha in identity["source_sha256"].items()):
                return None
            chain = validated_chain(ROOT/paths[-1], identity)
            if (chain is None or [r["binding"] for r in chain] != paths
                    or not chain[-1]["summary"]["complete"]):
                return None
    mutation_campaign = len(argv) > 1 and argv[1] == "tests/run_mutations.py"
    if mutation_campaign:
        from run_mutations import validated_campaign
        if not validated_campaign(result, dependencies, versions):
            return None
    children = sorted(set(directory.rglob("*.receipt.json")) | external_tools)
    tool_receipts = []
    for path in children:
        record = json.loads(retained_file(path).read_text())
        if mutation_campaign:
            for ancestor in path.parents:
                if ancestor == directory:
                    break
                if (ancestor/"bundle-manifest.json").is_file():
                    record = dict(record)
                    for key in ("stdout", "stderr"):
                        if key in record:
                            record[key] = relative(ancestor/record[key])
                    record["artifact_sha256"] = {
                        relative(ancestor/p): sha
                        for p, sha in record.get("artifact_sha256", {}).items()}
                    break
        if "tool_version_argv" not in record:
            continue
        tool = Path(record["tool_version_argv"][0]).name
        if tool not in versions or record.get("tool_version_exit") != 0:
            return None
        if record.get("tool_version", "").strip() != versions[tool]:
            return None
        if not execution_logs_intact(record):
            return None
        expected_rejection = False
        if len(argv) > 1 and argv[1] == "tests/run_parameters.py":
            for row in result.get("runs", []):
                if (row.get("invalid") and row.get("status") == "passed"
                        and path.parent == ROOT/row["path"]
                        and path.name in ("rejection.receipt.json", "simulation.receipt.json")
                        and record.get("exit") not in (0, None)
                        and "PARAMETER ERROR" in retained_file(ROOT/record["stdout"]).read_text()):
                    expected_rejection = True
                    break
        if record.get("timed_out") or (record.get("exit") != 0 and not (
                expected_rejection or mutation_campaign)):
            return None
        for key in ("stdout", "stderr"):
            artifact = ROOT / record[key]
            if not available(artifact):
                return None
            if record.get("artifact_sha256", {}).get(record[key]) != digest(artifact):
                return None
        bound_sources = (dependencies if path not in external_tools else
                         [p for p in dependencies if p.endswith(".sv") or p.startswith("design/")])
        if not mutation_campaign and any(record.get("source_sha256", {}).get(p) != current.get(p)
                                        for p in bound_sources):
            return None
        tool_receipts.append(relative(path))
    if not tool_receipts:
        return None
    if argv[1] == "tests/run_epilogue.py":
        if (result.get("commands") != 104 or result.get("vectors") != 168
                or not available(directory / "observations.txt")):
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
    if len(argv) > 1 and argv[1] == "tests/run_synthesis.py":
        # The synthesis driver revalidates every external phase and rescores
        # the final netlist. A summary with just a retained version log cannot.
        return None
    candidates = []
    for result_path in (ROOT / "evidence/l1").glob("run-*/*/result.json"):
        candidates.append(result_path)
    candidates.extend((ROOT/"evidence/preparation").glob("*/shard-*/result.json"))
    for result_path in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True):
        bound = validated_result(result_path, argv, dependencies, versions, allow_failure)
        if bound is not None:
            return bound
    return None
