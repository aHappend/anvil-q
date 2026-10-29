"""Artifact isolation regressions; real composition uses the production stage runner."""

import hashlib
import json
from pathlib import Path
import shutil
import sys
import uuid
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import official


def hashes(directory):
    return {str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(directory.rglob("*")) if path.is_file()}


def integrity_regression(directory):
    pinned = official.manifest()
    fixture = directory / ("corrupt-assets-" + uuid.uuid4().hex)
    data = fixture / "tests/data"
    data.mkdir(parents=True)
    shutil.copyfile(official.ROOT / "tests/data/assets.json", data / "assets.json")
    for item in pinned["ordered_files"]:
        shutil.copyfile(official.ROOT / item["path"], fixture / item["path"])
    corrupt = fixture / pinned["ordered_files"][0]["path"]
    original = corrupt.read_bytes()
    changed = bytes([original[0] ^ 1]) + original[1:]
    # This is a disposable asset copy, never the pinned project input.
    corrupt.write_bytes(changed)
    rejected = directory / ("rejected-validation-" + uuid.uuid4().hex)
    rejected.mkdir()
    with patch.object(official, "ROOT", fixture):
        try:
            official.validate(rejected)
        except RuntimeError as error:
            assert "asset length/hash mismatch" in str(error), str(error)
            mismatch = str(error)
        else:
            raise AssertionError("Corrupt pinned asset was accepted")
    assert not list(rejected.iterdir()), "Rejected assets produced a success-shaped record"
    fresh = directory / ("exclusive-validation-" + uuid.uuid4().hex)
    fresh.mkdir()
    official.validate(fresh)
    before = hashes(fresh)
    try:
        official.validate(fresh)
    except FileExistsError:
        pass
    else:
        raise AssertionError("Validation no longer enforces exclusive record creation")
    assert hashes(fresh) == before, "Exclusive-write rejection mutated earlier evidence"
    result = {"corrupt_asset_rejected": mismatch, "corrupt_copy_sha256":
              hashlib.sha256(changed).hexdigest(),
              "exclusive_write_rejected": True, "earlier_artifacts_unchanged": before}
    with (directory / "artifact-integrity-regression.json").open("x") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print("ARTIFACT_INTEGRITY corrupt_hash_rejected=1 exclusive_write_rejected=1")


def run_composition_regression(evidence):
    from verify import OFFICIAL_STAGES, run_stages, write_json

    evidence.tools(("python3",))
    evidence.child(["python3", "tests/scheduling.py", "--source-contract"],
                   "source-contract-regression")
    evidence.child(["python3", "tests/test_qwen_artifacts.py",
                    evidence.relative(evidence.path)], "artifact-integrity-regression")
    frozen, results = [], []

    def observe(stage):
        def execute(scope):
            for directory, expected in frozen:
                assert hashes(directory) == expected, "A later stage mutated earlier artifacts"
            stage(scope)
            for directory, expected in frozen:
                assert hashes(directory) == expected, "A later stage mutated earlier artifacts"
            validation = scope.path / "qwen-asset-validation.json"
            assert validation.is_file(), f"Validation did not execute for {stage.__name__}"
            snapshot = hashes(scope.path)
            assert snapshot, "Empty stage artifacts"
            frozen.append((scope.path, snapshot))
            results.append({"stage": stage.__name__,
                            "directory": evidence.relative(scope.path),
                            "artifact_sha256": snapshot})
        execute.__name__ = stage.__name__
        return execute

    # Actual fragments, exhaustive/random regex, Unicode/Oniguruma and official
    # reference consumers run sequentially under the same Evidence parent as L1.
    run_stages(evidence, [observe(stage) for stage in OFFICIAL_STAGES[:4]])
    assert len(frozen) == 4 and len({directory for directory, _ in frozen}) == 4
    for directory, expected in frozen:
        assert hashes(directory) == expected, "Earlier evidence changed after composition"
    regex = json.loads((frozen[1][0] / "qwen-regex-audit.json").read_bytes())
    assert regex["exhaustive_max_length"] == 4 and regex["exhaustive_sequences"] > 0
    assert regex["random_sequences_by_seed"] == {"1": 1000, "17": 1000, "89": 1000}
    write_json(evidence.path / "artifact-composition-regression.json", {
        "scope": "Bounded artifact-namespace repair, not full L1 or product acceptance",
        "stages": results, "earlier_artifacts_unchanged": True,
        "regex_exhaustive_sequences": regex["exhaustive_sequences"],
        "regex_random_sequences_by_seed": regex["random_sequences_by_seed"],
    })


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 tests/test_qwen_artifacts.py PROJECT_RELATIVE_EVIDENCE_DIRECTORY")
    directory = Path(sys.argv[1])
    if (directory.is_absolute() or ".." in directory.parts or not directory.is_dir()
            or directory.parts[:2] not in (
                ("evidence", "preparation"), ("evidence", "verification"))):
        raise SystemExit("Output must be an existing project-relative fresh evidence directory")
    integrity_regression(directory)
