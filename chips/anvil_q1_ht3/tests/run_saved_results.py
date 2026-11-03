"""Revalidate real completed observations and reject simulated reclamation."""

import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, hashes, relative, remaining, timestamp
from retention import digest, find_result, inventory, normalize_argv, validated_result
from verify import TOOLS, dependencies, reconcile_coverage
from run_integrated_geometry import CASES


SUITES = ("integrated_geometry", "parameters", "mutations", "packed_cache",
          "packed_top", "stream_checkpoint", "performance", "attention_timing",
          "compatibility")


def invalid_artifacts(result):
    pending, rejected = [result], {}
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            for name, sha in value.get("artifact_sha256", {}).items():
                path = ROOT/name
                path.resolve().relative_to(ROOT)
                try:
                    if not path.is_file():
                        rejected[name] = "missing"
                    elif digest(path) != sha:
                        rejected[name] = "hash mismatch"
                except FileNotFoundError:
                    rejected[name] = "removed during validation"
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    return rejected


def rejection_details(argv, deps):
    current = hashes()
    candidates = [*(ROOT/"evidence/l1").glob("run-*/*/result.json"),
                  *(ROOT/"evidence/preparation").glob("*/shard-*/result.json")]
    for path in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True):
        receipt_path = path.parent/"receipt.json"
        if not receipt_path.is_file():
            continue
        receipt = json.loads(receipt_path.read_text())
        if (normalize_argv(receipt.get("argv", [])) != normalize_argv(argv)
                or any(receipt.get("source_sha256", {}).get(p) != current[p] for p in deps)):
            continue
        result = json.loads(path.read_text())
        if result.get("status") == "passed":
            return dict(candidate=relative(path), invalid_artifacts=invalid_artifacts(result))
    return dict(candidate=None)


def run(output, suites=SUITES):
    versions = inventory(output, TOOLS)
    rows = []
    assertions = 0
    for name in suites:
        argv = ["python3", f"tests/run_{name}.py"]
        deps = dependencies(argv[1])
        retained = find_result(argv, deps, versions)
        if retained is None:
            raise AssertionError(f"no complete current-source retained result: {name}; "
                                 f"{json.dumps(rejection_details(argv, deps), sort_keys=True)}")
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
    if {"packed_top", "packed_cache"}.issubset(suites):
        negative = [dict(row) for row in rows]
        for row in negative:
            if row["id"] == "packed_top":
                row["status"] = "failed"
        reconcile_coverage(negative)
        packed = next(r for r in negative if r["id"] == "packed_cache")
        if "resolved_coverage" in packed:
            raise AssertionError("failed packed-top matrix closed publication coverage")
        assertions += 1
    reconcile_coverage(rows)
    if {"packed_top", "packed_cache"}.issubset(suites):
        packed = next(r for r in rows if r["id"] == "packed_cache")
        if (packed.get("coverage_limits") or packed.get("resolved_coverage", {}).get("cases") != 10
                or packed["status"] != "passed"):
            raise AssertionError("observed packed-publication coverage did not reconcile")
        assertions += 1
    if {"integrated_geometry", "parameters"}.issubset(suites):
        parameters = next(r for r in rows if r["id"] == "parameters")
        coverage = parameters.get("functional_parameter_coverage", {})
        cases = coverage.get("cases", [])
        if (len(cases) != 2*len(CASES)
                or any({r["format"] for r in cases if r["id"] == name} != {0, 1}
                       for name in CASES)
                or coverage["tile_beats"] != [1, 3, 256]
                or coverage["kv_window"] != [1, 3, 128]
                or coverage["flash_tile"] != [1, 3, 16, 128]
                or parameters["coverage_limits"]
                or not coverage.get("pairwise_cross_complete")
                or coverage["elaborated_cross_triples_without_functional_observation"]):
            raise AssertionError("functional tuples were lost or elaboration became functional coverage")
        negative = [dict(row) for row in rows]
        for row in negative:
            row.pop("functional_parameter_coverage", None)
            if row["id"] == "integrated_geometry":
                row["status"] = "failed"
        reconcile_coverage(negative)
        if any("functional_parameter_coverage" in row for row in negative):
            raise AssertionError("failed geometry matrix published functional coverage")
        assertions += 2
    return dict(status="passed", scope="retained observation validation, not new RTL execution",
                assertions=assertions, rows=rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--suite", choices=SUITES, action="append",
                        help="validate only selected settled suites; never aggregate acceptance")
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_saved_results.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    try:
        result = run(output, tuple(dict.fromkeys(args.suite)) if args.suite else SUITES)
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
