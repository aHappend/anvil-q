"""Cold-startup concurrency regression and bounded repair diagnostic."""

from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import threading

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, Run, write_json
from parameters import A, B, defaults
from structure_checks import startup_matrix, sv_literal


OVERRUN_RECEIPT = "evidence/check-structure/20261031T200317Z-85adda2b2504/receipt.json"


def startup_scalability_sensitivity(parent):
    """Synthetic tools prove worker bounds, ordering and diagnostic rejection."""
    scenarios = []
    for scenario in ("concurrent", "missing-marker", "duplicate-marker", "missing-diagnostic",
                     "illegal-zero-exit"):
        with tempfile.TemporaryDirectory(prefix="startup-scalability-", dir=parent) as tmp:
            fixture = Run.__new__(Run)
            fixture.path = Path(tmp)
            fixture.lock = threading.RLock()
            fixture.resources = {"workers": 8}
            fixture.cancelled = threading.Event()
            fixture.active_processes = {}
            active = 0
            peak = 0
            compiles = []
            released = []
            barrier = threading.Barrier(2)
            count = 4 if scenario == "concurrent" else 1
            cases = [{"folder": f"case-{n}", "expected": n % 2 == 0,
                      "instance": "synthetic instance; no RTL execution",
                      "metadata": {"index": n, "expected_legal": n % 2 == 0}}
                     for n in range(count)]
            if scenario.startswith("illegal") or scenario == "missing-diagnostic":
                cases[0]["expected"] = False

            def tool(argv, *, build_class="default", **kwargs):
                nonlocal active, peak
                if build_class != "default":
                    with fixture.lock:
                        active += 1
                        peak = max(peak, active)
                        compiles.append(build_class)
                    if scenario == "concurrent":
                        barrier.wait(timeout=10)
                    with fixture.lock:
                        active -= 1
                    return "synthetic compiler", {}
                binary = ROOT / argv[1 if argv[0] == "vvp" else 0]
                folder = binary.parent if argv[0] == "vvp" else binary.parent.parent
                expected = cases[int(folder.name.split("-")[-1])]["expected"]
                text = "STARTUP_COMPLETE\n" if expected else "PARAMETER ERROR\n"
                code = 0 if expected else 1
                if scenario in ("missing-marker", "missing-diagnostic"):
                    text = ""
                if scenario == "duplicate-marker":
                    text *= 2
                if scenario == "illegal-zero-exit":
                    code = 0
                return text, {"exit_code": code, "stdout": "synthetic-only"}

            fixture.tool = tool
            fixture.compact_startup = lambda binary: released.append(binary)
            try:
                results = startup_matrix(fixture, cases, [], ("iverilog", "verilator"),
                                         "synthetic-results.json")
            except AssertionError:
                assert scenario != "concurrent"
                assert not released
                scenarios.append({"scenario": scenario, "rejected": True})
            else:
                assert scenario == "concurrent"
                assert peak == 2 and len(compiles) == len(released) == 8
                assert [row["index"] for row in results] == [0, 0, 1, 1, 2, 2, 3, 3]
                assert json.loads((fixture.path / "synthetic-results.json").read_text()) == results
                assert compiles.count("icarus-startup") == compiles.count("verilator-startup") == 4
                scenarios.append({"scenario": scenario, "peak_compilers": peak,
                                  "startup_executions": len(results)})
    return {"scope": "synthetic harness only", "scenarios": scenarios}


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run = Run("evidence/preparation/startup-scalability-repair-" + stamp,
              "bounded two-worker cold startup diagnostic", repair_of=OVERRUN_RECEIPT)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        run.versions([("python3", "--version"), ("iverilog", "-V"), ("vvp", "-V"),
                      ("verilator", "--version"), ("g++", "--version"), ("make", "--version")])
        regression = startup_scalability_sensitivity(run.path)
        geometries = [("compact", A, True, asdict(A)),
                      ("tile-boundary", replace(B, BANKS=4, CACHE_MODE=1), True,
                       asdict(replace(B, BANKS=4, CACHE_MODE=1)))]
        geometries += [("official-default", defaults(p), True, {"PROFILE": p})
                       for p in (1, 2, 3)]
        geometries += [("illegal-banks", replace(A, BANKS=3), False,
                        asdict(replace(A, BANKS=3)))]
        cases = []
        for n, (label, geometry, expected, parameters) in enumerate(geometries):
            overrides = ",".join(f".{key}({sv_literal(value)})"
                                 for key, value in parameters.items())
            cases.append({
                "folder": f"geometry-{n:04d}", "expected": expected,
                "instance": f"anvil_q3_top #({overrides}) accelerator "
                            "(.clk(1'b0),.rst_n(1'b0),.cancel(1'b0),.token_valid(1'b0));",
                "metadata": {"label": label, "parameters": asdict(geometry),
                             "overrides": parameters, "expected_legal": expected}})
        run.plan_startup_storage(12)
        rtl = [run.rel(path) for path in sorted((ROOT / "rtl").glob("*.sv"))]
        results = startup_matrix(run, cases, rtl, ("iverilog", "verilator"),
                                 "parameter-results.json")
        assert len(results) == 12
        compilers = [record for record in run.records if record["argv"][0] in
                     ("iverilog", "verilator") and "-o" in record["argv"]]
        overlap = any(a["started_at"] < b["finished_at"] and
                      b["started_at"] < a["finished_at"]
                      for n, a in enumerate(compilers) for b in compilers[n+1:])
        if run.resources["workers"] > 1:
            assert overlap, "cold startup compilers never overlapped"
        result = {"synthetic": regression, "startups": results,
                  "cold_compiler_overlap_observed": overlap,
                  "scope": "12 targeted startup executions, not the complete structure gate"}
        write_json(run.path / "scalability-results.json", result)
        run.finish("passed", result=result)
    except BaseException as exc:
        run.finish("failed", diagnosis=str(exc))
        raise


if __name__ == "__main__":
    main()
