"""Revalidate real completed observations and reject simulated reclamation."""

import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, hashes, relative, remaining, timestamp
from retention import find_result, inventory, validated_result
from verify import TOOLS, dependencies, reconcile_coverage


def run(output):
    versions = inventory(output, TOOLS)
    rows = []
    assertions = 0
    for name in ("integrated_geometry", "parameters", "mutations", "packed_cache",
                 "packed_top", "stream_checkpoint", "performance"):
        argv = ["python3", f"tests/run_{name}.py"]
        deps = dependencies(argv[1])
        retained = find_result(argv, deps, versions)
        if retained is None:
            raise AssertionError(f"no complete current-source retained result: {name}")
        candidate = ROOT/retained["result_path"]
        record = json.loads((ROOT/retained["receipt"]).read_text())
        if record.get("timed_out"):
            raise AssertionError("partial timeout was admitted")
        # Refuse the exact candidate when a bound execution log disappears.
        tools = retained["tool_receipts"]
        tool_record = json.loads((ROOT/tools[0]).read_text())
        missing = ROOT/tool_record["stdout"]
        original_is_file = Path.is_file

        def reclaimed(path):
            return False if path == missing else original_is_file(path)

        with patch.object(Path, "is_file", reclaimed):
            if validated_result(candidate, argv, deps, versions) is not None:
                raise AssertionError(f"reclaimed observation accepted: {name}")
        assertions += 2
        if name == "stream_checkpoint":
            result = retained["result"]
            last = json.loads((ROOT/result["streams"][0][-1]).read_text())
            missing = ROOT/last["identity"]["binary"]
            with patch.object(Path, "is_file", reclaimed):
                if validated_result(candidate, argv, deps, versions) is not None:
                    raise AssertionError("reclaimed checkpoint executable accepted")
            assertions += 1
        rows.append(dict(id=name, status=("incomplete" if retained["result"].get("coverage_limits")
                                        else "passed"),
                         coverage_limits=retained["result"].get("coverage_limits", []),
                         receipt=retained["receipt"], result_path=retained["result_path"]))
    negative = [dict(row) for row in rows]
    for row in negative:
        if row["id"] == "packed_top":
            row["status"] = "failed"
    reconcile_coverage(negative)
    packed = next(r for r in negative if r["id"] == "packed_cache")
    if "resolved_coverage" in packed:
        raise AssertionError("failed packed-top matrix closed publication coverage")
    reconcile_coverage(rows)
    packed = next(r for r in rows if r["id"] == "packed_cache")
    if (packed.get("coverage_limits") or packed.get("resolved_coverage", {}).get("cases") != 10
            or packed["status"] != "passed"):
        raise AssertionError("observed packed-publication coverage did not reconcile")
    assertions += 2
    return dict(status="passed", scope="retained observation validation, not new RTL execution",
                assertions=assertions, rows=rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_saved_results.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    try:
        result = run(output)
    except (RuntimeError, ValueError, AssertionError, OSError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    with (output/"result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(exit=int(result["status"] != "passed"), timed_out=remaining() <= 0,
                   end=timestamp(), result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
