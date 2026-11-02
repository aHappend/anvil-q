"""Reproduce from only the declared deliverables, without build/evidence reuse."""

import hashlib
import json
import shutil

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
    return {"copied_source_hashes": copied, "stdout": outputs,
            "child_receipts": [relative(path) for path in sorted(
                (directory / "evidence" / "preparation").glob("*/receipt.json"))]}
