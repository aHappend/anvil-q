"""Advisory dispatch, coverage accounting and measured scalability diagnostics.

The original 112 full-workload Icarus obligations remain unestablished.
Compact portability plus full compiled execution is recorded, never represented
as fulfilling that historical dual-simulator acceptance contract.
"""

import argparse
from collections import Counter
from contextlib import ExitStack
from dataclasses import asdict, replace
from copy import deepcopy
import inspect
import json
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decoder_checks import decoder_case, validate_simulation_tier
from execution import Run, write_json
from parameters import A, A_PORTABILITY, B, C, compatibility_geometries, startup_geometry

FAILED_RECEIPT = "evidence/check-behavior/20261029T153530Z-1b3a394b0fe3/receipt.json"


def expected_workloads():
    rows = []
    for label, base in (("A", A), ("B", B), ("C", C)):
        for banks in (1, 2, 4, 8):
            for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
                for seed in ((17,) if label == "C" else (17, 89, 257)):
                    for simulator in (("iverilog", "verilator") if label == "A" else ("verilator",)):
                        actual_base = A_PORTABILITY if simulator == "iverilog" else base
                        tokens = ((0,) if simulator == "iverilog" else
                                  (1, 4, 2, 6) if label == "C" else (1, 4, 2, 6, 3, 5, 7))
                        prefill = 1 if simulator == "iverilog" else 2 if label == "C" else 4
                        rows.append((label, replace(actual_base, BANKS=banks, CACHE_MODE=mode,
                                                    INT4_ASYM=asym),
                                     seed, simulator, tokens, prefill))
    return rows


def coverage_sensitivity():
    from verify import mandatory_a_coverage, mandatory_decoder_coverage, original_icarus_coverage

    complete = expected_workloads()
    a = [row[1:] for row in complete if row[0] == "A"]
    assert mandatory_a_coverage(a) == {"required": 96, "observed": 96}
    assert mandatory_decoder_coverage(complete) == {"required": 160, "observed": 160}
    rejected = []
    for name, checker, rows in (("A", mandatory_a_coverage, a),
                                ("ABC", mandatory_decoder_coverage, complete)):
        for defect, changed in (
                ("missing", rows[1:]), ("duplicate", rows + rows[:1]),
                ("wrong-token", [(*rows[0][:-2], (1,), rows[0][-1]), *rows[1:]]),
                ("wrong-phase", [(*rows[0][:-1], 9), *rows[1:]])):
            try:
                checker(changed)
            except AssertionError:
                rejected.append(name + ":" + defect)
            else:
                raise AssertionError("incorrect workload inventory accepted: " + name + defect)
    originals = []
    for label, base in (("A", A), ("B", B), ("C", C)):
        for banks in (1, 2, 4, 8):
            for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
                for seed in ((17,) if label == "C" else (17, 89, 257)):
                    tokens = [1, 4, 2, 6] if label == "C" else [1, 4, 2, 6, 3, 5, 7]
                    originals.append({
                        "geometry": asdict(replace(
                            base, BANKS=banks, CACHE_MODE=mode, INT4_ASYM=asym)),
                        "simulator": "iverilog", "tokens": len(tokens),
                        "workload": {"seed": seed, "tokens": tokens,
                                     "prefill_tokens": 2 if label == "C" else 4},
                        "compared_bits": 32, "bit_mismatches": 0})
    assert original_icarus_coverage(originals)["status"] == "passed"
    for defect in ("missing", "compiled", "short", "wrong-phase"):
        changed = deepcopy(originals)
        if defect == "missing":
            changed.pop()
        elif defect == "compiled":
            changed[-1]["simulator"] = "verilator"
        elif defect == "short":
            changed[-1]["workload"]["tokens"] = [1]
            changed[-1]["tokens"] = 1
        else:
            changed[-1]["workload"]["prefill_tokens"] = 9
        report = original_icarus_coverage(changed)
        assert report["status"] == "unestablished" and report["observed"] == 111
        rejected.append("original:" + defect)
    assert original_icarus_coverage([])["observed"] == 0
    for field, value in (("compared_bits", 0), ("bit_mismatches", 1)):
        changed = deepcopy(originals)
        changed[-1][field] = value
        try:
            original_icarus_coverage(changed)
        except AssertionError:
            rejected.append("original:" + field)
        else:
            raise AssertionError("uncompared/mismatched original result accepted: " + field)
    return {"requested_workloads": 160, "rejected": rejected,
            "original_full_icarus_obligations_unestablished": 112,
            "scope": "offline accounting sensitivity only"}


def preflight_sensitivity():
    import verify

    with patch.object(verify, "write_json") as output:
        verify.behavior_execution_preflight(MagicMock())
    output.assert_called_once()
    report = output.call_args.args[1]
    validate_execution_contract(report)
    rejected = []
    for label in ("status", "missing", "duplicate", "token", "phase", "original",
                  "supplemental", "supplemental-simulator", "supplemental-token"):
        changed = deepcopy(report)
        if label == "status":
            changed["status"] = "compatible"
        elif label == "missing":
            changed["obligations"].pop()
        elif label == "duplicate":
            changed["obligations"].append(changed["obligations"][0])
        elif label == "token":
            changed["obligations"][0]["tokens"] = [1]
        elif label == "phase":
            changed["obligations"][0]["prefill_tokens"] = 99
        elif label == "original":
            changed["original_coverage"]["discharged_by_compact_smoke"] = True
        elif label == "supplemental":
            changed["supplemental_obligations"] = []
        elif label == "supplemental-simulator":
            changed["supplemental_obligations"][0]["simulator"] = "iverilog"
        else:
            changed["supplemental_obligations"][0]["tokens"] = [1]
        try:
            validate_execution_contract(changed)
        except AssertionError:
            rejected.append(label)
        else:
            raise AssertionError("incorrect execution contract accepted: " + label)
    return {"execution_contract": report, "rejected": rejected,
            "scope": "offline dispatch inventory; not acceptance"}


def validate_execution_contract(report):
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
    assert report["portability_dispatch"] == {
        "requested": 48, "direct_single_bank": 12,
        "automatic_minimum_single_bank": 36,
        "additional_compiled_requested_geometries": 36,
        "original_coverage_discharged": False}
    assert len(report["supplemental_obligations"]) == 1
    row = report["supplemental_obligations"][0]
    assert row["check_id"] == "supplemental-decoder-a-b8-int4-asymmetric-seed257"
    assert replace(A, **row["geometry"]) == replace(A, BANKS=8, CACHE_MODE=2, INT4_ASYM=1)
    assert (row["seed"], row["simulator"], row["tokens"], row["prefill_tokens"]) == (
        257, "verilator", [1, 4, 2, 6, 3, 5, 7], 4)


def guard_sensitivity():
    cases = ((A, [1]), (A, [1, 4]), (A_PORTABILITY, [0]), (B, [1]), (C, [1]),
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
        compact = worker.call_args_list[0].args[1]
        assert (compact.BANKS, compact.QUEUE_DEPTH, compact.TILE_K,
                compact.TILE_ROWS, compact.MAX_SEQ_LEN) == (1, 1, 8, 1, 1)
        assert worker.call_args_list[1].args[3] == "verilator"
        assert worker.call_args_list[1].kwargs["tokens"] == tokens
        assert result["tier_dispatch"]["compact_smoke"] == smoke
    assert not validate_simulation_tier(replace(A_PORTABILITY, BANKS=1), "iverilog", [0])
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
        stack.enter_context(patch.object(
            verify, "original_icarus_coverage",
            return_value={"status": "passed", "missing": [],
                          "scope": "mocked dispatch-only fixture, no simulations"}))
        stack.enter_context(patch.object(verify, "write_json"))
        verify.numerical_matrix(fake)
    observed = Counter()
    for call in mocks["decoder_case"].call_args_list:
        simulator = call.kwargs.get("simulator", call.args[3] if len(call.args) > 3 else None)
        assert call.kwargs["compiled_host"] == (simulator == "verilator")
        if call.kwargs.get("adversarial"):
            continue
        g, seed, simulator = call.args[1:]
        label = "A" if g.HIDDEN_SIZE == 16 else "B" if g.HIDDEN_SIZE == 64 else "C"
        observed[label, g, seed, simulator, tuple(call.kwargs["tokens"]),
                 call.kwargs["prefill_tokens"]] += 1
    assert observed == Counter(expected_workloads())
    assert mocks["decoder_case"].call_count == 172
    for name in ("host_case", "bridge_case", "scheduler_case", "prefetch_case",
                 "accumulator_case", "math_memory_case", "scalar_case",
                 "dot8_case", "codec_case", "activation_case"):
        index = (3 if name in ("bridge_case", "scheduler_case") else
                 4 if name == "prefetch_case" else
                 2 if name in ("math_memory_case", "activation_case") else 1)
        assert {call.args[index] for call in mocks[name].call_args_list} == {
            "iverilog", "verilator"}, name
    activation = Counter((call.args[1], call.args[2], call.kwargs["capacity"])
                         for call in mocks["activation_case"].call_args_list)
    expected_activation = Counter((b, s, 8 if b == 1 else 120)
                                  for b in (1, 2, 4, 8)
                                  for s in ("iverilog", "verilator"))
    expected_activation[8, "verilator", 11008] += 1
    assert activation == expected_activation
    secondary = secondary_dispatch_sensitivity(fake)
    return {"decoder_dispatch_cases": 172, "coverage": coverage_sensitivity(),
            "execution_contract_preflight": preflight_sensitivity(),
            "secondary_dispatch": secondary,
            "automatic_dispatch": guard_sensitivity(),
            "scope": "offline dispatch regression; no numerical acceptance"}


def secondary_dispatch_sensitivity(fake):
    import boundary_checks
    import compatibility_checks
    import mutation_checks
    with (patch.object(compatibility_checks, "decoder_case", return_value={"cycles": 1}) as decoder,
          patch.object(compatibility_checks, "codec_case", return_value={}) as codec,
          patch.object(compatibility_checks, "write_json")):
        compatibility_checks.compatibility(fake)
    calls = decoder.call_args_list
    compact = [call for call in calls if call.kwargs["label"] == "compact-portability"]
    legacy = [call for call in calls if call.kwargs["label"].startswith("legacy-")]
    recovery = [call for call in calls if call not in compact + legacy]
    assert (len(compact), len(legacy), len(recovery), codec.call_count) == (14, 9, 15, 18)
    assert Counter(call.args[1] for call in legacy) == Counter(compatibility_geometries())
    for call in legacy + recovery:
        assert call.kwargs["simulator"] == "verilator"
        assert call.kwargs["tokens"] == (
            [1, 2, 1, 2, 1, 2, 1] if call in legacy else [1, 4])
        assert call.kwargs.get("compiled_host", False) == (
            call in legacy or call.kwargs["label"] == "implicit-startup")
    for call in recovery:
        expected_prelude = {
            "implicit-startup": 0, "explicit-startup-recovery": 1,
            "bad-first-position": 2, "idle-cancel-recovery": 3,
            "bad-token-recovery": 4, "active-cancel-recovery": 5,
        }[call.kwargs["label"]]
        assert call.kwargs["prelude"] == expected_prelude
        assert call.kwargs["prefill_tokens"] == 1
    for call in compact:
        g = call.args[1]
        assert (g.HIDDEN_SIZE <= 32 and g.BANKS == 1 and g.VOCAB_SIZE == 1 and
                g.INTERMEDIATE_SIZE == 8 and call.kwargs["tokens"] == [0])
    for function in (boundary_checks.boundaries, boundary_checks.integration_faults):
        with (patch.object(boundary_checks, "decoder_case", return_value={}) as decoder,
              patch.object(boundary_checks, "write_json")):
            function(fake)
        assert decoder.called
        assert all(call.kwargs["simulator"] == "verilator"
                   for call in decoder.call_args_list)
    with ExitStack() as stack:
        mocks = {}
        for name in ("decoder_case", "dot8_case", "scheduler_case", "prefetch_case",
                     "codec_case", "activation_case", "mutation_case"):
            mocks[name] = stack.enter_context(patch.object(
                mutation_checks, name, return_value={"name": "mock", "killed": True}))
        mocks["mutation_case"].side_effect = lambda run, spec: {"name": spec[0], "killed": True}
        stack.enter_context(patch.object(mutation_checks, "write_json"))
        mutation_checks.mutations(fake)
    assert inspect.signature(mutation_checks.mutation_case).parameters[
        "simulator"].default == "verilator"
    assert mocks["mutation_case"].call_count == len(mutation_checks.MUTATIONS)
    for name, mock in mocks.items():
        if name == "mutation_case":
            continue
        for call in mock.call_args_list:
            simulator = call.kwargs.get("simulator")
            if simulator is None and len(call.args) > 1 and isinstance(call.args[1], str):
                simulator = call.args[1]
            assert simulator == "verilator", name
    return {"legacy": len(legacy), "recovery": len(recovery), "compact": len(compact),
            "mutations": len(mutation_checks.MUTATIONS)}


def scalability(run):
    """Same elaboration, different stimulus: compare raw and streaming transports."""
    jobs = [
        lambda: decoder_case(run, A, seed=17, simulator="verilator", tokens=[1, 4],
                             label="raw", stream_compare=False, sparse_scan=False),
        lambda: decoder_case(run, A, seed=17, simulator="verilator", tokens=[1, 4],
                             label="stream"),
        lambda: decoder_case(run, A, seed=89, simulator="verilator", tokens=[1, 4, 2],
                             prefill_tokens=2, label="different-stimulus"),
    ]
    results = run.parallel(jobs)
    for field in set(results[0]) - {"trace_sha256", "result_path", "comparison_transport"}:
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


def workload_pacing(run):
    results = run.parallel([
        lambda: decoder_case(run, replace(A, BANKS=1), simulator="iverilog",
                             tokens=[1], prefill_tokens=1, label="A-compact"),
        lambda: decoder_case(run, replace(B, BANKS=1), simulator="verilator",
                             label="B-seven-token"),
        lambda: decoder_case(run, replace(C, CACHE_MODE=2, INT4_ASYM=1),
                             simulator="verilator", tokens=[1, 4, 2, 6],
                             prefill_tokens=2, label="C-four-token"),
    ])
    return {"results": results, "elapsed_s": __import__("time").time() - run.start,
            "scope": "measured representative A/B/C pacing, not the complete matrix"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", choices=("dispatch", "coverage", "preflight", "guard",
                                           "smoke", "portability", "legacy", "scalability",
                                           "workload-pacing"),
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
        elif args.probe == "workload-pacing":
            result = workload_pacing(run)
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
