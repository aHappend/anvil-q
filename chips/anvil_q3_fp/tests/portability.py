"""Reproduce from only the declared deliverables, without build/evidence reuse."""

import hashlib
import json
import shutil
import tarfile

from execution import ROOT, relative


PATTERNS = ("rtl/*.sv", "tests/*.py", "anvil_q3_reference/rtl/*.sv",
            "design/SPEC.md", "design/ARCHITECTURE.md")


def copy_sources(destination):
    destination.mkdir()
    copied = {}
    for pattern in PATTERNS:
        paths = sorted(ROOT.glob(pattern))
        if not paths:
            raise AssertionError(f"Declared source selector has no files: {pattern}")
        for source in paths:
            name = source.relative_to(ROOT)
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            original = hashlib.sha256(source.read_bytes()).hexdigest()
            if hashlib.sha256(target.read_bytes()).hexdigest() != original:
                raise AssertionError(f"Reproduction copy mismatch: {name}")
            copied[str(name)] = original
    return copied


def retain_reproduction(evidence, directory, copied, receipts):
    """Keep auditable inputs and child logs independent of the disposable copy."""
    artifacts = {directory / name: digest for name, digest in copied.items()}
    for path in receipts:
        record = json.loads(path.read_text())
        artifacts[path] = hashlib.sha256(path.read_bytes()).hexdigest()
        for field in ("sources", "generated_inputs"):
            for name, digest in record.get(field, {}).items():
                artifacts[directory / name] = digest
        for command in record["commands"]:
            for field in ("stdout", "stderr"):
                artifact = directory / command[field]
                artifacts[artifact] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    archive = evidence.path / "reproduction-inputs-and-logs.tar"
    manifest = {}
    with tarfile.open(archive, "x") as retained:
        for path, digest in sorted(artifacts.items()):
            name = path.relative_to(directory).as_posix()
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise AssertionError(f"Reproduction artifact changed before retention: {name}")
            retained.add(path, arcname=name, recursive=False)
            manifest[name] = digest
    with tarfile.open(archive, "r") as retained:
        for name, digest in manifest.items():
            stream = retained.extractfile(name)
            if stream is None or hashlib.sha256(stream.read()).hexdigest() != digest:
                raise AssertionError(f"Retained reproduction artifact mismatch: {name}")
    return {"archive": relative(archive),
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "members": manifest}


def check(evidence, seed):
    directory = evidence.path / "clean-source-copy"
    copied = copy_sources(directory)
    if any((directory / name).exists() for name in (".git", ".vulcan", ".tooling", "VULCAN")):
        raise AssertionError("Runtime/developer metadata entered reproduction")
    outputs = []
    for args in (["--probe", "top", "--simulator", "iverilog", "--tokens", "1"],
                 ["--probe", "synthesis", "--banks", "1"]):
        output = evidence.run(["python3", "tests/verify.py", *args, "--seed", str(seed)], cwd=directory)
        receipts = list((directory / "evidence" / "preparation").glob("*/receipt.json"))
        passed = [path for path in receipts if json.loads(path.read_text()).get("status") == "passed"]
        if len(passed) != len(outputs) + 1:
            raise AssertionError(f"Clean-source check did not produce its fresh passing tool receipt: {relative(output)}")
        outputs.append(relative(output))
    receipts = sorted((directory / "evidence" / "preparation").glob("*/receipt.json"))
    return {"copied_source_hashes": copied, "stdout": outputs,
            "child_receipts": [relative(path) for path in receipts],
            "retained_reproduction": retain_reproduction(evidence, directory, copied, receipts)}
