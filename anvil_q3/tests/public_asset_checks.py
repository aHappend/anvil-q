"""Offline provenance-checker sensitivity, not public asset or DUT acceptance."""

import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Run
from public_assets import descriptor


def public_asset_checks(run):
    folder = run.path.resolve() / "public-asset-fixtures"
    asset_root = folder / "input-project"
    asset = asset_root / "tests/assets/slice.bin"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"\x01\x02\x03\x04")
    revision = "a" * 40
    item = {
        "url": f"https://raw.githubusercontent.com/fixture/fixture/{revision}/slice.bin",
        "sha256": hashlib.sha256(asset.read_bytes()).hexdigest(),
        "size_bytes": 4, "path": "tests/assets/slice.bin",
    }

    class OfflineRun:
        def rel(self, path):
            return str(path.relative_to(asset_root))

        def tool(self, *args, **kwargs):
            raise AssertionError("offline asset fixture attempted network execution")

    rejected = []
    cases = {
        "wrong-length": [10, 14],
        "negative-start": [-1, 2],
        "boolean-start": [False, 3],
        "float-end": [0, 3.0],
        "string-range": "0-3",
        "one-endpoint": [0],
        "reversed-range": [3, 0],
    }
    with patch("public_assets.ROOT", asset_root):
        for byte_range in (None, [10, 13]):
            result = descriptor(OfflineRun(), {**item, "byte_range": byte_range}, revision)
            if result["sha256"] != item["sha256"] or result["byte_range"] != byte_range:
                raise AssertionError("valid retained asset descriptor changed")
        for storage in ("local", "download"):
            candidate = dict(item)
            if storage == "download":
                del candidate["path"]
            for label, byte_range in cases.items():
                try:
                    descriptor(OfflineRun(), {**candidate, "byte_range": byte_range}, revision)
                except ValueError as exc:
                    if str(exc) != "invalid inclusive public byte slice":
                        raise
                    rejected.append(storage + ":" + label)
                else:
                    raise AssertionError(storage + " public asset accepted invalid byte range: " + label)
    return {"valid_controls": 2, "rejected_range_defects": rejected,
            "scope": "offline descriptor fixtures; no baseline identity or physical acceptance"}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        from types import SimpleNamespace
        print(json.dumps(public_asset_checks(SimpleNamespace(path=Path(sys.argv[2]))),
                         sort_keys=True))
        raise SystemExit(0)
    run = Run("evidence/preparation/independent-public-asset-checker",
              "local public asset range validation sensitivity",
              repair_of=sys.argv[1] if len(sys.argv) > 1 else None)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        run.versions([("python3", "--version")])
        text, _ = run.tool(["python3", "tests/public_asset_checks.py", "--worker",
                            run.rel(run.path)])
        result = json.loads(text)
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    run.finish("passed", result=result)
    print(json.dumps(result, sort_keys=True))
