"""Clean-directory delivery reproduction from explicit source-only selectors."""

import hashlib
import json
from pathlib import Path
import re
import shutil

from execution import ROOT, relative
from leaf_checks import run_qk, run_scalar, run_tensor
from numerical_checks import analytic_coefficients
from smoke_checks import run_startup


DELIVERY_SELECTORS = ("rtl/*.sv", "tests/*.py", "design/SPEC.md",
                      "design/ARCHITECTURE.md", "README.md")


def run_reproduction_child(run):
    results = {"startup": [], "scalar": [], "qk": [], "tensor": [],
               "coefficients": analytic_coefficients()}
    for simulator in ("icarus", "verilator"):
        results["startup"].append(run.component(
            f"reproduce-startup-{simulator}",
            lambda child, simulator=simulator: run_startup(child, simulator)))
        results["scalar"].append(run.component(
            f"reproduce-scalar-{simulator}",
            lambda child, simulator=simulator: run_scalar(child, simulator)))
        results["qk"].append(run.component(
            f"reproduce-qk-{simulator}",
            lambda child, simulator=simulator: run_qk(child, simulator)))
        results["tensor"].append(run.component(
            f"reproduce-tensor-{simulator}",
            lambda child, simulator=simulator: run_tensor(child, simulator)))
    if any(len(results[name]) != 2 for name in ("startup", "scalar", "qk", "tensor")):
        raise AssertionError("isolated dual-simulator reproduction coverage missing")
    return results


def run_reproduce(run, child_probe="reproduce-child"):
    files = sorted({path for pattern in DELIVERY_SELECTORS for path in ROOT.glob(pattern)})
    if not files or any(not tuple(ROOT.glob(pattern)) for pattern in DELIVERY_SELECTORS):
        raise AssertionError("delivery reproduction selector matched no source")
    hashes = {relative(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    for name, digest in hashes.items():
        if run.hashes.get(name) != digest:
            raise AssertionError("delivery source changed during reproduction preparation")
    identity = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:12]
    bundle = run.path / f"isolated-project-{identity}"
    bundle.mkdir(exist_ok=False)
    for source in files:
        target = bundle / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    copied = {path.relative_to(bundle).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in bundle.rglob("*") if path.is_file()}
    if copied != hashes:
        raise AssertionError("source-only delivery copy mismatch")
    manifest = {"selectors": DELIVERY_SELECTORS, "source_sha256": hashes,
                "prohibited_inputs_copied": [],
                "reference_tree_dependency": "none: delivered legacy copies are in rtl/",
                "bundle": relative(bundle)}
    (run.path / "reproduction-source-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    output = run.execute(["python3", "-I", "tests/verify.py", "--probe", child_probe],
                         "isolated-reproduction", cwd=bundle)
    receipts = re.findall(r"^RECEIPT (evidence/preparation/[^\n]+/receipt.json)$", output, re.M)
    candidates = []
    for name in receipts:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise AssertionError("nonportable isolated receipt path")
        receipt_path = bundle / path
        receipt = json.loads(receipt_path.read_text())
        if (receipt["entrypoint_argv"][-2:] == ["--probe", child_probe] and
                path.parent.name.startswith(child_probe + "-")):
            candidates.append((receipt_path, receipt))
    if len(candidates) != 1:
        raise AssertionError("isolated child result missing or duplicated")
    path, child = candidates[0]
    def validate(receipt):
        if receipt["status"] != "passed" or receipt["source_sha256"] != hashes:
            raise AssertionError("isolated child failed or used undeclared sources")
        if not receipt["commands"]:
            raise AssertionError("isolated reproduction executed no tool")
        for command in receipt["commands"]:
            if not command["child_settled"] or command["disposition"] != "exited" or command["exit_code"]:
                raise AssertionError("isolated reproduction command did not settle successfully")
            if Path(command["cwd"]).is_absolute() or ".." in Path(command["cwd"]).parts:
                raise AssertionError("isolated tool left its copied project")
        for component in receipt["components"]:
            name = Path(component["receipt"])
            if name.is_absolute() or ".." in name.parts:
                raise AssertionError("isolated component left its copied project")
            validate(json.loads((bundle / name).read_text()))

    validate(child)
    return {"bundle": relative(bundle), "manifest": relative(
                run.path / "reproduction-source-manifest.json"),
            "child_receipt": relative(path), "child_probe": child_probe,
            "copied_source_count": len(files), "source_sha256": hashes,
            "scope": "compact smoke/numerical reproduction" if child_probe == "reproduce-child"
                     else "bounded source-only isolation diagnostic, not full reproduction",
            "results": child["results"]}
