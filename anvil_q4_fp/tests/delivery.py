"""Fresh source-only reproduction, with independent native, mutation and synthesis checks."""

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import ROOT, SELECTORS, execute, new_run, relative, source_hashes


def run(preparation=False):
    directory = new_run("clean-delivery", preparation)
    bundle = directory / ("source-bundle-" + directory.name.rsplit("-", 1)[-1])
    bundle.mkdir()
    inventory = {}
    patterns = (
        r"/(?:home|data|root|Users)/[^\s\"']+",
        r"\b[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]\b",
        r"\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})\b",
        r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----",
    )
    for selector in SELECTORS:
        paths = [path for path in sorted(ROOT.glob(selector)) if path.is_file()]
        if not paths:
            raise AssertionError(f"Empty declared source selector: {selector}")
        for path in paths:
            if path.is_symlink():
                raise AssertionError(f"Source bundle cannot depend on symlink: {relative(path)}")
            text = path.read_text()
            for pattern in patterns:
                # The scanner's own regular expressions are not embedded identities.
                if re.search(pattern, text):
                    raise AssertionError(f"Private identity/credential in source: {relative(path)}")
            name = path.relative_to(ROOT)
            destination = bundle / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            inventory[str(name)] = hashlib.sha256(destination.read_bytes()).hexdigest()
    if inventory != source_hashes():
        raise AssertionError("Source-only bundle differs from declared inputs")
    (directory / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    worker = bundle / "tests/delivery.py"
    execute(directory / "fresh-relative-reproduction", [
        "python3", relative(worker), "--worker"], timeout=2400,
        extra_inputs=[directory / "inventory.json"])
    result = json.loads((bundle / "delivery-result.json").read_text())
    if result["source_sha256"] != inventory:
        raise AssertionError("Reproduction did not use the exact source-only inventory")
    (directory / "observed.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "bundle_inventory": inventory,
        "reproduction": result}, indent=2) + "\n")
    print(f"Clean delivery receipts: {relative(directory)}", flush=True)
    return directory


def worker():
    import os
    os.chdir(ROOT)
    import behavior
    import defects
    import synthesis
    import four_state
    from native_model import descriptor

    records = {}
    image_directory = new_run("image-loader")
    execute(image_directory / "manifest-integrity", [
        "python3", "tests/images.py", "--output", relative(image_directory)])
    records["image_integrity"] = relative(image_directory)
    records["native"] = relative(behavior.run(
        banks=1, queue=1, tile_rows=3, tile_k=3, tokens=1,
        words=descriptor(banks=1, intermediate=3, vocabulary=3, context=1, page_tokens=1)))
    records["Icarus_native"] = relative(four_state.run())
    records["mutation"] = relative(defects.numerical_mutants())
    records["synthesis"] = relative(synthesis.run(geometries=[(1, 1, 1, 1)]))
    (ROOT / "delivery-result.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "checks": records,
        "commands_are_project_relative": True}, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--preparation", action="store_true")
    args = parser.parse_args()
    worker() if args.worker else run(args.preparation)
