"""Focused evaluation-gating regression; not original matrix acceptance.

python3 tests/throughput_checks.py --banks 1 8
"""

import argparse
from dataclasses import replace
from pathlib import Path
import sys
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import execution
from decoder_checks import decoder_case
from execution import ROOT, Run, write_json
from parameters import A
from simulation_tiering_checks import coverage_sensitivity
from verify import shard_inventory


def resources():
    cases = []
    for quota, expected in (("max 100000", 8), ("100000 100000", 1),
                            ("250000 100000", 2), ("50000 100000", 1)):
        files = {"/sys/fs/cgroup/cpu.max": quota,
                 "/sys/fs/cgroup/memory.max": "max"}
        with (patch.object(execution.os, "sched_getaffinity", return_value=set(range(16))),
              patch.object(Path, "is_file", lambda p: str(p) in files),
              patch.object(Path, "read_text", lambda p: files[str(p)]),
              patch.object(execution.os, "sysconf",
                           side_effect=lambda n: 4096 if n == "SC_PAGE_SIZE" else 16 * 1024**2)):
            result = execution.execution_resources()
        assert result["workers"] == expected, result
        assert 1 <= result["build_jobs"] <= min(2, expected), result
        cases.append(result)
    return cases


def cleanup(run):
    directory = run.path / "synthetic-cleanup"
    directory.mkdir()
    files = ("unit.o", "unit.a", "unit.h.fast.gch", "unit.cpp", "unit.h", "unit.mk",
             "decoder", "unrelated.txt")
    for name in files:
        (directory / name).write_text("synthetic cleanup fixture, not a compiled artifact\n")
    binary_key = str((ROOT / "python3").resolve())
    run.transient_builds[binary_key] = directory
    with patch.object(run, "_tool", side_effect=RuntimeError("synthetic unsettled launch")):
        try:
            run.tool(["python3", "-c", "pass"])
        except RuntimeError as exc:
            assert str(exc) == "synthetic unsettled launch"
        else:
            raise AssertionError("unsettled fixture did not fail")
    assert sorted(p.name for p in directory.iterdir()) == sorted(files)
    run.tool(["python3", "-c", "pass"])
    retained = sorted(p.name for p in directory.iterdir())
    assert retained == sorted(name for name in files if Path(name).suffix not in (".o", ".a", ".gch"))
    assert binary_key not in run.transient_builds
    return {"retained": retained, "unsettled_artifacts_preserved": True,
            "scope": "synthetic cleanup sensitivity, not a compiler or RTL result"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--banks", type=int, nargs="+", choices=(1, 2, 4, 8), default=[1, 8])
    args = parser.parse_args()
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run = Run("evidence/preparation/throughput-regression-" + stamp,
              "unchanged seven-token A driver equivalence and harness sensitivity",
              repair_of="evidence/check-behavior/shards/decoder-36c0bbcad86b21431b7d/"
                        "20261029T234437Z-4da4ac961030/tool-0001/receipt.json")
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        resource_result = resources()
        cleanup_result = cleanup(run)
        coverage = coverage_sensitivity()
        inventory = shard_inventory()
        write_json(run.path / "shard-commands.json", inventory)
        run.versions([("verilator", "--version"), ("g++", "--version")])
        jobs = []
        for banks in args.banks:
            for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
                g = replace(A, BANKS=banks, CACHE_MODE=mode, INT4_ASYM=asym)
                for host in (False, True):
                    jobs.append(lambda g=g, host=host: decoder_case(
                        run, g, seed=17, simulator="verilator",
                        tokens=[1, 4, 2, 6, 3, 5, 7], prefill_tokens=4,
                        compiled_host=host, label="gated-host" if host else "sv-control"))
        results = run.parallel(jobs)
        for sv, host in zip(results[::2], results[1::2]):
            assert set(sv) == set(host)
            for field in set(sv) - {"result_path", "driver"}:
                if sv[field] != host[field]:
                    raise AssertionError(f"public/numerical driver difference: {field}")
        write_json(run.path / "driver-equivalence.json", results)
        run.finish("passed", result={
            "scope": "focused driver regression; original simulator contract unresolved",
            "resources": resource_result, "cleanup": cleanup_result, "coverage": coverage,
            "complete_seven_token_cases": len(results), "bit_mismatches": 0,
            "compared_bits": sum(result["compared_bits"] for result in results),
            "inventory": run.rel(run.path / "shard-commands.json")})
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise


if __name__ == "__main__":
    main()
