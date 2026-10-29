"""Advisory dispatch, coverage accounting and measured scalability diagnostics.

The original 112 full-workload Icarus obligations remain unestablished.
Compact portability plus full compiled execution is recorded, never represented
as fulfilling that historical dual-simulator acceptance contract.
"""

import argparse
from collections import Counter
from contextlib import ExitStack
from dataclasses import replace
import json
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decoder_checks import decoder_case, validate_simulation_tier
from execution import Run, write_json
from parameters import A, B, C, compatibility_geometries, startup_geometry

FAILED_RECEIPT = "evidence/check-behavior/20261029T153530Z-1b3a394b0fe3/receipt.json"


def expected_workloads():
    rows = []
    for label, base in (("A", A), ("B", B), ("C", C)):
        for banks in (1, 2, 4, 8):
            for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
                for seed in ((17,) if label == "C" else (17, 89, 257)):
                    for simulator in (("iverilog", "verilator") if label == "A" else ("verilator",)):
                        tokens = ((1,) if simulator == "iverilog" else
                                  (1, 4, 2, 6) if label == "C" else (1, 4, 2, 6, 3, 5, 7))
                        prefill = 1 if simulator == "iverilog" else 2 if label == "C" else 4
                        rows.append((label, replace(base, BANKS=banks, CACHE_MODE=mode,
                                                    INT4_ASYM=asym),
                                     seed, simulator, tokens, prefill))
    return rows


def coverage_sensitivity():
    from verify import mandatory_a_coverage, mandatory_decoder_coverage

    complete = expected_workloads()
    a = [row[1:] for row in complete if row[0] == "A"]
    assert mandatory_a_coverage(a) == {"required": 96, "observed": 96}
    assert mandatory_decoder_coverage(complete) == {"required": 160, "observed": 160}
    rejected = []
    for name, checker, rows in (("A", mandatory_a_coverage, a),
                                ("ABC", mandatory_decoder_coverage, complete)):
        for defect, changed in (
                ("missing", rows[1:]), ("duplicate", rows + rows[:1]),
                ("wrong-token", [(*rows[0][:-2], (0,), rows[0][-1]), *rows[1:]]),
                ("wrong-phase", [(*rows[0][:-1], 9), *rows[1:]])):
            try:
                checker(changed)
            except AssertionError:
                rejected.append(name + ":" + defect)
            else:
                raise AssertionError("incorrect workload inventory accepted: " + name + defect)
    return {"actual_required_workloads": 160, "rejected": rejected,
            "original_full_icarus_obligations_unestablished": 112,
            "scope": "offline accounting sensitivity only"}


def preflight_sensitivity():
    import verify

    with patch.object(verify, "write_json") as output:
        verify.behavior_execution_preflight(MagicMock())
    output.assert_called_once()
    report = output.call_args.args[1]
    observed = Counter((row["profile"], replace(A, **row["geometry"]), row["seed"],
                        row["simulator"], tuple(row["tokens"]), row["prefill_tokens"])
                       for row in report["obligations"])
    assert observed == Counter(expected_workloads())
    assert report["status"] == "tiered-dispatch-original-coverage-unresolved"
    assert report["original_coverage"] == {
        "required_full_icarus": {"A": 48, "B": 48, "C": 16},
        "discharged_by_compact_smoke": False,
        "status": "112 original full-workload Icarus obligations remain unestablished",
        "review_required": True}
    assert report["required_workloads"] == 160
    assert len(report["supplemental_obligations"]) == 1
    return {"execution_contract": report, "scope": "offline dispatch inventory; not acceptance"}


def guard_sensitivity():
    cases = ((A, [1, 4]), (B, [1]), (C, [1]),
             (next(compatibility_geometries()), [1, 2, 1, 2, 1, 2, 1]))
    for g, tokens in cases:
        assert validate_simulation_tier(g, "iverilog", tokens)
        assert not validate_simulation_tier(g, "verilator", tokens)
        smoke = {"result_path": "smoke.json"}
        complete = {"result_path": "complete.json"}
        # Execute the real outer dispatcher, with only its recursive workers mocked.
        with (patch("decoder_checks.decoder_case", side_effect=[smoke, complete]) as worker,
              patch("decoder_checks.write_json")):
            result = decoder_case(MagicMock(), g, simulator="iverilog", tokens=tokens)
        assert worker.call_count == 2
        assert worker.call_args_list[0].args[3] == "iverilog"
        assert worker.call_args_list[0].kwargs["tokens"] == [0]
        assert worker.call_args_list[1].args[3] == "verilator"
        assert worker.call_args_list[1].kwargs["tokens"] == tokens
        assert result["tier_dispatch"]["compact_smoke"] == smoke
    assert not validate_simulation_tier(A, "iverilog", [1])
    try:
        validate_simulation_tier(A, "unknown", [1])
    except ValueError:
        pass
    else:
        raise AssertionError("unknown simulator accepted")
    return {"automatic_dispatch_cases": len(cases),
            "scope": "mocked compact-smoke plus unchanged compiled workload; no simulation"}


def dispatch_sensitivity():
    import verify

    fake = MagicMock()
    fake.parallel.side_effect = lambda jobs: [job() for job in jobs]
    with ExitStack() as stack:
        mocks = {}
        for name in ("memory_maps", "compatibility", "boundaries", "integration_faults",
                     "host_case", "bridge_case", "scheduler_case", "prefetch_case",
                     "accumulator_case", "math_memory_case", "scalar_case", "dot8_case",
                     "codec_case", "decoder_case", "activation_case"):
            mocks[name] = stack.enter_context(patch.object(
                verify, name, return_value=[] if name in
                ("memory_maps", "compatibility", "boundaries", "integration_faults") else {}))
        stack.enter_context(patch.object(verify, "write_json"))
        verify.numerical_matrix(fake)
    observed = Counter()
    for call in mocks["decoder_case"].call_args_list:
        if call.kwargs.get("adversarial"):
            continue
        g, seed, simulator = call.args[1:]
        label = "A" if g.HIDDEN_SIZE == 16 else "B" if g.HIDDEN_SIZE == 64 else "C"
        observed[label, g, seed, simulator, tuple(call.kwargs["tokens"]),
                 call.kwargs["prefill_tokens"]] += 1
    assert observed == Counter(expected_workloads())
    assert mocks["decoder_case"].call_count == 172
    return {"decoder_dispatch_cases": 172, "coverage": coverage_sensitivity(),
            "execution_contract_preflight": preflight_sensitivity(),
            "automatic_dispatch": guard_sensitivity(),
            "scope": "offline dispatch regression; no numerical acceptance"}


def scalability(run):
    """Same elaboration, different stimulus: compare raw and streaming transports."""
    jobs = [
        lambda: decoder_case(run, A, seed=17, simulator="verilator", tokens=[1, 4],
                             label="raw", stream_compare=False),
        lambda: decoder_case(run, A, seed=17, simulator="verilator", tokens=[1, 4],
                             label="stream"),
        lambda: decoder_case(run, A, seed=89, simulator="verilator", tokens=[1, 4, 2],
                             prefill_tokens=2, label="different-stimulus"),
    ]
    results = run.parallel(jobs)
    for field in ("logits", "compared_bits", "requests", "cycles", "traffic", "stalls"):
        assert results[0][field] == results[1][field], field
    # Also exercise a complete interrupted legacy workload, twice across seeds.
    legacy = next(compatibility_geometries())
    results.extend(run.parallel([
        lambda n=n: decoder_case(run, legacy, seed=n, simulator="verilator",
                                tokens=[1, 2, 1, 2, 1, 2, 1], label="legacy-reuse")
        for n in (17, 89)]))
    from leaf_checks import dot8_case
    results.extend(run.parallel([
        lambda n=n: dot8_case(run, "verilator", n) for n in (17, 89)]))
    assert len(run.builds) == 3, "expected one A, one legacy and one dot8 build"
    assert len(run.build_reuses) == 4, "all repeated elaborations must reuse binaries"
    raw = run.path / results[0]["result_path"]
    stream = run.path / results[1]["result_path"]
    size = {"raw": (raw.parent / "trace.tsv").stat().st_size,
            "stream": (stream.parent / "trace.tsv").stat().st_size}
    assert size["stream"] < size["raw"] // 10
    return {"results": results, "builds": len(run.builds), "reuses": len(run.build_reuses),
            "trace_bytes": size, "elapsed_s": __import__("time").time() - run.start,
            "scope": "measured focused advisory regression; not full behavior gate"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", choices=("dispatch", "coverage", "preflight", "guard",
                                           "smoke", "portability", "legacy", "scalability"),
                        default="dispatch")
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="verilator")
    parser.add_argument("--repair-of", default=FAILED_RECEIPT)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    offline = {"dispatch": dispatch_sensitivity, "coverage": coverage_sensitivity,
               "preflight": preflight_sensitivity, "guard": guard_sensitivity}
    if args.worker:
        print(json.dumps(offline[args.probe](), sort_keys=True))
        return
    run = Run("evidence/preparation/simulation-tiering-" + args.probe,
              "simulation harness repair:" + args.probe, repair_of=args.repair_of)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        run.versions([("python3", "--version"), ("iverilog", "-V"), ("vvp", "-V"),
                      ("verilator", "--version")])
        if args.probe in offline:
            text, _ = run.tool(["python3", "tests/simulation_tiering_checks.py",
                               "--probe", args.probe, "--worker"])
            result = json.loads(text)
        elif args.probe == "scalability":
            result = scalability(run)
        elif args.probe == "portability":
            from compatibility_checks import compact_portability
            result = compact_portability(run)
        elif args.probe == "legacy":
            result = decoder_case(run, next(compatibility_geometries()),
                                  simulator="verilator", label="legacy-c1",
                                  tokens=[1, 2, 1, 2, 1, 2, 1])
        else:
            g = replace(startup_geometry(3), BANKS=1, INTERMEDIATE_SIZE=8, VOCAB_SIZE=1)
            result = decoder_case(run, g, simulator=args.simulator,
                                  tokens=[0], prefill_tokens=1, label="compact-portability")
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    run.finish("passed", result=result)


if __name__ == "__main__":
    main()
