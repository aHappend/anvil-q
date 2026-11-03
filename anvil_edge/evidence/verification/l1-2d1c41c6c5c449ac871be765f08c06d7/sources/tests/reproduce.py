"""Fresh declared-source reproduction without prior binaries or runtime state."""

import json
from pathlib import Path
import shutil


def clean_reproduction(evidence, selectors, digest):
    root = Path(__file__).resolve().parent.parent
    clean = evidence.path / "clean-source"
    clean.mkdir()
    manifest = {}
    for selector in selectors:
        matches = [path for path in sorted(root.glob(selector)) if path.is_file()]
        if not matches:
            raise RuntimeError(f"Empty required clean-reproduction selector: {selector}")
        for source in matches:
            relative = source.relative_to(root)
            if source.is_symlink():
                raise RuntimeError(f"Undeclared symlink input {relative}")
            target = clean / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            if digest(source) != digest(target):
                raise RuntimeError(f"Clean-source copy mismatch {relative}")
            manifest[str(relative)] = digest(target)
    (evidence.path / "clean-inputs.json").write_text(json.dumps(manifest, indent=2) + "\n")
    result = evidence.child(
        ["python3", "tests/verify.py", "--probe", "clean-focus"],
        "fresh-boot-inference-synthesis", cwd=clean,
    )
    lines = (root / result["stdout"]).read_text().splitlines()
    summaries = [json.loads(line) for line in lines if line.startswith('{"exit_code":')]
    if len(summaries) != 1 or summaries[0]["exit_code"] != 0:
        raise RuntimeError("Fresh-source worker lacks a successful retained receipt")
    receipt = summaries[0]["receipt"]
    path = Path(receipt)
    if path.is_absolute() or ".." in path.parts or path.parts[:2] != ("evidence", "preparation"):
        raise RuntimeError("Fresh-source worker returned a nonportable receipt")
    record = json.loads((clean / path).read_text())
    coverage = {row["name"]: row for row in record["coverage"]}
    required = ("top-synthetic-q1-s17", "synthesis-minimum")
    if any(coverage.get(name, {}).get("status") != "passed" for name in required):
        raise RuntimeError("Fresh-source reproduction lacks exact inference and synthesis")
    if record["source_sha256"] != manifest or not record["sources_unchanged"]:
        raise RuntimeError("Fresh-source results are not bound to the declared copied inputs")
    evidence.record["coverage"].append({
        "name": "clean-reproduction", "status": "passed",
        "worker_receipt": evidence.relative(clean / path),
        "source_files": len(manifest),
        "scope": "Synthetic minimum-geometry real Q1 autonomous boot, multitoken inference, exact zero-logit UTF-8 output and connected production-hierarchy synthesis; not official-profile or default-model acceptance.",
    })
