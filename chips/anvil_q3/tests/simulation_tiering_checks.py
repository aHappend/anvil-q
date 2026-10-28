"""Retained tier-dispatch regression and bounded simulator repair probes.

python3 tests/simulation_tiering_checks.py --probe dispatch
python3 tests/simulation_tiering_checks.py --probe smoke --simulator iverilog
python3 tests/simulation_tiering_checks.py --probe portability
python3 tests/simulation_tiering_checks.py --probe legacy
python3 tests/simulation_tiering_checks.py --probe guard
python3 tests/simulation_tiering_checks.py --probe coverage
python3 tests/simulation_tiering_checks.py --probe preflight

These are advisory diagnostics, not substitutes for the admitted behavior gate.
The legacy probe reproduces the interrupted workload using compiled simulation;
the smoke measures the additional minimum-work public-pin portability case.
Offline coverage/preflight/dispatch probes are nonnumerical. The frozen matrix
requires 96 A cases, 48 B Icarus cases plus 16 selected Verilator cases, and 16 C
cases per simulator. Its 112 Icarus obligations conflict with the current guard;
the separately admitted seven-token supplemental command selects Verilator and
does not conflict. These probes do not repair dispatch or authorize substitution.
"""

import argparse
from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import asdict, replace
import inspect
import json
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decoder_checks import (SimulationTierConflict, decoder_case,
                            validate_simulation_tier)
from execution import Run, write_json
from parameters import A, B, C, compatibility_geometries, startup_geometry


FAILED_RECEIPT = "evidence/check-behavior/20261028T082607Z-96412cd96bb2/receipt.json"


def coverage_sensitivity():
    from verify import mandatory_a_coverage

    records = [
        (replace(A, BANKS=banks, CACHE_MODE=mode, INT4_ASYM=asym),
         seed, simulator, (1, 4, 2, 6, 3, 5, 7), 4)
        for seed in (17, 89, 257)
        for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1))
        for banks in (1, 2, 4, 8)
        for simulator in ("iverilog", "verilator")]
    if mandatory_a_coverage(records) != {"required": 96, "observed": 96}:
        raise AssertionError("incorrect mandatory A inventory")
    invalid = {
        "empty": [],
        "missing-one": records[1:],
        "duplicate": records + records[:1],
        "short-workload": [(*records[0][:3], (1, 4), 4)] + records[1:],
        "wrong-token": [(*records[0][:3], (1, 4, 2, 6, 3, 5, 6), 4)] + records[1:],
        "wrong-phase-boundary": [(*records[0][:4], 2)] + records[1:],
        "verilator-only": [row for row in records if row[2] == "verilator"],
        "simulator-substitution": [
            (*row[:2], "verilator", *row[3:]) for row in records],
    }
    for label, rows in invalid.items():
        try:
            mandatory_a_coverage(rows)
        except AssertionError as exc:
            if "mandatory A dual-simulator coverage incomplete" not in str(exc):
                raise
        else:
            raise AssertionError("incomplete coverage accepted: " + label)
    return {"rejected": list(invalid), "required_A_workloads": 96,
            "scope": "synthetic coverage-accounting sensitivity only; "
                     "no simulator execution or numerical coverage established"}


def preflight_sensitivity():
    import verify

    fake = MagicMock()
    with patch.object(verify, "write_json") as output:
        try:
            verify.behavior_execution_preflight(fake)
        except SimulationTierConflict as exc:
            if "No behavior subtest was launched" not in str(exc):
                raise AssertionError("ambiguous preflight conflict diagnostic") from exc
        else:
            raise AssertionError("incompatible frozen inventory accepted")
        output.assert_called_once()
        report = output.call_args.args[1]
    expected = Counter()
    for label, base in (("A", A), ("B", B), ("C", C)):
        for banks in (1, 2, 4, 8):
            for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
                for seed in ((17,) if label == "C" else (17, 89, 257)):
                    simulators = ("iverilog", "verilator") if label == "A" or seed == 17 else ("iverilog",)
                    for simulator in simulators:
                        expected[label, replace(base, BANKS=banks, CACHE_MODE=mode,
                                                INT4_ASYM=asym), seed, simulator,
                                 (1, 4, 2, 6) if label == "C" else (1, 4, 2, 6, 3, 5, 7),
                                 2 if label == "C" else 4] += 1

    def assert_report(candidate):
        observed = Counter()
        conflict_counts = Counter()
        for row in candidate["obligations"]:
            g = replace(A, **row["geometry"])
            observed[row["profile"], g, row["seed"], row["simulator"],
                     tuple(row["tokens"]), row["prefill_tokens"]] += 1
            if ("conflict" in row) != (row["simulator"] == "iverilog"):
                raise AssertionError("missing or invented per-workload conflict")
            if "conflict" in row:
                if not row["conflict"]:
                    raise AssertionError("empty conflict diagnostic")
                conflict_counts[row["profile"]] += 1
        supplemental = candidate["supplemental_obligations"]
        if (len(supplemental) != 1 or
                supplemental[0]["check_id"] != "supplemental-decoder-a-b8-int4-asymmetric-seed257" or
                supplemental[0]["profile"] != "A" or
                supplemental[0]["geometry"] != asdict(replace(A, BANKS=8, CACHE_MODE=2, INT4_ASYM=1)) or
                supplemental[0]["seed"] != 257 or supplemental[0]["simulator"] != "verilator" or
                supplemental[0]["tokens"] != [1, 4, 2, 6, 3, 5, 7] or
                supplemental[0]["prefill_tokens"] != 4 or "conflict" in supplemental[0]):
            raise AssertionError("admitted supplemental Verilator obligation omitted or substituted")
        if (observed != expected or candidate["status"] != "incompatible" or
                candidate["required_workloads"] != 192 or
                candidate["conflicting_workloads"] != 112 or
                conflict_counts != Counter(A=48, B=48, C=16) or
                candidate["conflicting_supplemental_workloads"] != 0):
            raise AssertionError("incorrect frozen preflight inventory/status")

    assert_report(report)
    invalid = {}
    for label in ("false-compatible", "verilator-only", "duplicate", "wrong-token",
                  "wrong-phase", "missing-conflict", "missing-supplemental",
                  "supplemental-simulator-substitution", "invented-supplemental-conflict",
                  "invented-supplemental-conflict-count"):
        candidate = deepcopy(report)
        if label == "false-compatible":
            candidate["status"] = "compatible"
        elif label == "verilator-only":
            candidate["obligations"] = [row for row in candidate["obligations"]
                                        if row["simulator"] == "verilator"]
        elif label == "duplicate":
            candidate["obligations"].append(deepcopy(candidate["obligations"][0]))
        elif label == "wrong-token":
            candidate["obligations"][0]["tokens"][-1] = 6
        elif label == "wrong-phase":
            candidate["obligations"][0]["prefill_tokens"] = 2
        elif label == "missing-conflict":
            del candidate["obligations"][0]["conflict"]
        elif label == "missing-supplemental":
            candidate["supplemental_obligations"] = []
        elif label == "supplemental-simulator-substitution":
            candidate["supplemental_obligations"][0]["simulator"] = "iverilog"
        elif label == "invented-supplemental-conflict":
            candidate["supplemental_obligations"][0]["conflict"] = "invented conflict"
        else:
            candidate["conflicting_supplemental_workloads"] = 1
        invalid[label] = candidate
    for label, candidate in invalid.items():
        try:
            assert_report(candidate)
        except AssertionError:
            pass
        else:
            raise AssertionError("false-compatible/incomplete inventory accepted: " + label)
    with (patch.object(verify, "write_json"),
          patch.object(verify, "memory_maps") as first_subtest,
          patch.object(verify, "decoder_case") as decoder):
        try:
            verify.numerical_matrix(fake)
        except SimulationTierConflict:
            pass
        else:
            raise AssertionError("behavior executed despite preflight conflict")
        first_subtest.assert_not_called()
        decoder.assert_not_called()
    return {"required_workloads": report["required_workloads"],
            "conflicting_workloads": report["conflicting_workloads"],
            "conflicts_by_profile": {"A": 48, "B": 48, "C": 16},
            "conflicting_supplemental_workloads": 0,
            "rejected": list(invalid),
            "execution_contract": report,
            "scope": "nonnumerical preflight/accounting sensitivity with mocked output; "
                     "no simulator execution or execution-contract reconciliation"}


def guard_sensitivity():
    cases = (
        ("frozen-A-seven-token", A, [1, 4, 2, 6, 3, 5, 7]),
        ("medium-single-token", B, [1]),
        ("large-single-token", C, [1]),
        ("legacy-seven-token", next(compatibility_geometries()), [1, 2, 1, 2, 1, 2, 1]),
        ("above-compact-width", replace(A, HIDDEN_SIZE=48), [1]),
        ("implicit-seven-token-default", A, None),
    )
    for label, g, tokens in cases:
        # An unusable run object proves rejection precedes paths, fixtures and tools.
        try:
            decoder_case(object(), g, simulator="iverilog", tokens=tokens)
        except SimulationTierConflict as exc:
            if "No simulation was launched and no coverage was satisfied" not in str(exc):
                raise AssertionError("ambiguous tier-conflict diagnostic") from exc
        else:
            raise AssertionError("unsafe interpreted workload was accepted: " + label)
        validate_simulation_tier(g, "verilator",
                                 tokens if tokens is not None else [1, 4, 2, 6, 3, 5, 7])
    for hidden in (16, 32):
        validate_simulation_tier(replace(A, HIDDEN_SIZE=hidden), "iverilog", [0])
    try:
        validate_simulation_tier(A, "unrecognized", [0])
    except ValueError:
        pass
    else:
        raise AssertionError("unknown simulator accepted")
    return {"rejected_before_tool_launch": [label for label, _, _ in cases],
            "scope": "tier guard sensitivity only; unresolved mandatory simulator obligations "
                     "and full-workload pacing are not satisfied"}


def dispatch_sensitivity():
    import boundary_checks
    import compatibility_checks
    import mutation_checks
    import verify

    preflight = preflight_sensitivity()
    fake = MagicMock()
    with ExitStack() as stack:
        mocks = {}
        for name in (
                "memory_maps", "compatibility", "boundaries", "integration_faults",
                "mandatory_a_coverage", "behavior_execution_preflight",
                "host_case", "bridge_case", "scheduler_case", "prefetch_case",
                "accumulator_case", "math_memory_case", "scalar_case", "dot8_case",
                "codec_case", "decoder_case", "activation_case"):
            mocks[name] = stack.enter_context(patch.object(
                verify, name, return_value=[] if name in (
                    "memory_maps", "compatibility", "boundaries", "integration_faults") else {}))
        stack.enter_context(patch.object(verify, "write_json"))
        verify.numerical_matrix(fake)
    mocks["behavior_execution_preflight"].assert_called_once_with(fake)
    calls = mocks["decoder_case"].call_args_list
    coverage_calls = mocks["mandatory_a_coverage"].call_args_list
    if (len(coverage_calls) != 1 or len(coverage_calls[0].args[0]) != 48 or
            any(row[2] != "verilator" for row in coverage_calls[0].args[0])):
        raise AssertionError("pending compiled-only dispatch changed before reconciliation")
    try:
        verify.mandatory_a_coverage(coverage_calls[0].args[0])
    except AssertionError as exc:
        if "48 missing, 0 unexpected/duplicate" not in str(exc):
            raise
    else:
        raise AssertionError("pending compiled-only dispatch falsely satisfies frozen coverage")
    observed = Counter()
    for call in calls:
        g = call.args[1]
        seed = call.args[2] if len(call.args) > 2 else call.kwargs["seed"]
        simulator = call.args[3] if len(call.args) > 3 else call.kwargs["simulator"]
        if simulator != "verilator":
            raise AssertionError("decoder matrix routed to interpreted simulation")
        observed[g, seed, tuple(call.kwargs["tokens"]),
                 call.kwargs.get("prefill_tokens", 4),
                 call.kwargs.get("adversarial", False)] += 1
    expected = Counter()
    # Independent Cartesian inventory: A/B use all three seeds; C uses seed17.
    for label, base in (("A", A), ("B", B), ("C", C)):
        for banks in (1, 2, 4, 8):
            for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
                for seed in ((17,) if label == "C" else (17, 89, 257)):
                    g = replace(base, BANKS=banks, CACHE_MODE=mode, INT4_ASYM=asym)
                    tokens = (1, 4, 2, 6) if label == "C" else (1, 4, 2, 6, 3, 5, 7)
                    expected[g, seed, tokens, 2 if label == "C" else 4, False] += 1
    for seed in (17, 89, 257):
        for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
            expected[replace(A, CACHE_MODE=mode, INT4_ASYM=asym),
                     seed, (1, 4), 4, True] += 1
    if observed != expected or len(calls) != 124:
        raise AssertionError("decoder geometry/seed/token/adversarial matrix changed")
    for name in ("host_case", "bridge_case", "scheduler_case", "prefetch_case",
                 "accumulator_case", "math_memory_case", "scalar_case",
                 "dot8_case", "codec_case", "activation_case"):
        simulators = {
            call.kwargs["simulator"] if "simulator" in call.kwargs else call.args[
                3 if name == "bridge_case" else
                4 if name == "prefetch_case" else
                3 if name == "scheduler_case" else
                2 if name in ("math_memory_case", "activation_case") else 1]
            for call in mocks[name].call_args_list
        }
        if simulators != {"iverilog", "verilator"}:
            raise AssertionError("compact dual-simulator coverage lost: " + name)
    activation = Counter(
        (call.args[1], call.args[2], call.kwargs["capacity"])
        for call in mocks["activation_case"].call_args_list)
    expected_activation = Counter(
        (banks, simulator, 8 if banks == 1 else 120)
        for banks in (1, 2, 4, 8) for simulator in ("iverilog", "verilator"))
    expected_activation[8, "verilator", 11008] += 1
    if activation != expected_activation:
        raise AssertionError("compact/full activation-storage tier inventory changed")

    with (patch.object(compatibility_checks, "decoder_case", return_value={"cycles": 1}) as decoder,
          patch.object(compatibility_checks, "codec_case", return_value={}) as codec,
          patch.object(compatibility_checks, "write_json")):
        compatibility_checks.compatibility(fake)
    compact = [call for call in decoder.call_args_list
               if call.kwargs["label"] == "compact-portability"]
    legacy = [call for call in decoder.call_args_list
              if call.kwargs["label"].startswith("legacy-")]
    recovery = [call for call in decoder.call_args_list if call not in compact + legacy]
    if len(compact) != 14 or len(legacy) != 9 or len(recovery) != 15 or codec.call_count != 18:
        raise AssertionError("compatibility case inventory changed")
    if Counter(call.args[1] for call in legacy) != Counter(compatibility_geometries()):
        raise AssertionError("legacy geometry inventory changed")
    for call in legacy:
        if (call.kwargs["simulator"] != "verilator" or
                call.kwargs["tokens"] != [1, 2, 1, 2, 1, 2, 1]):
            raise AssertionError("legacy seven-token workload changed")
    for call in recovery:
        if call.kwargs["simulator"] != "verilator" or call.kwargs["tokens"] != [1, 4]:
            raise AssertionError("startup/recovery workload changed")
    for call in compact:
        g = call.args[1]
        if (g.HIDDEN_SIZE > 32 or g.BANKS != 1 or g.VOCAB_SIZE != 1 or
                g.INTERMEDIATE_SIZE != 8 or call.kwargs["tokens"] != [0]):
            raise AssertionError("noncompact portability workload")
    for function in (boundary_checks.boundaries, boundary_checks.integration_faults):
        with (patch.object(boundary_checks, "decoder_case", return_value={}) as decoder,
              patch.object(boundary_checks, "write_json")):
            function(fake)
        if not decoder.called or any(
                call.kwargs["simulator"] != "verilator" for call in decoder.call_args_list):
            raise AssertionError("integrated recovery/boundary sweep not compiled")
    with ExitStack() as stack:
        mutations = {}
        for name in ("decoder_case", "dot8_case", "scheduler_case", "prefetch_case",
                     "codec_case", "activation_case", "mutation_case"):
            mutations[name] = stack.enter_context(patch.object(
                mutation_checks, name, return_value={"name": "mock", "killed": True}))
        mutations["mutation_case"].side_effect = lambda run, spec: {
            "name": spec[0], "killed": True}
        stack.enter_context(patch.object(mutation_checks, "write_json"))
        mutation_checks.mutations(fake)
    if inspect.signature(mutation_checks.mutation_case).parameters["simulator"].default != "verilator":
        raise AssertionError("mutation matrix defaults to interpreted simulation")
    for name, mock in mutations.items():
        if name == "mutation_case":
            if mock.call_count != len(mutation_checks.MUTATIONS):
                raise AssertionError("mutation inventory changed")
            continue
        for call in mock.call_args_list:
            simulator = call.kwargs.get("simulator")
            if simulator is None and len(call.args) > 1 and isinstance(call.args[1], str):
                simulator = call.args[1]
            if simulator != "verilator":
                raise AssertionError("unmodified mutation baseline not compiled: " + name)
    return {"decoder_matrix_cases": len(calls), "legacy_workloads": len(legacy),
            "startup_recovery_cases": len(recovery), "compact_dual_simulator_cases": len(compact),
            "mutations": len(mutation_checks.MUTATIONS),
            "execution_contract_preflight": preflight,
            "pending_A_dispatch": {"observed_compiled_workloads": 48,
                                   "missing_Icarus_workloads": 48,
                                   "frozen_coverage_rejected": True},
            "scope": "mocked dispatch and inventory only; no numerical acceptance"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", choices=("dispatch", "smoke", "portability", "legacy", "guard",
                                           "coverage", "preflight"),
                        default="dispatch")
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="verilator")
    parser.add_argument("--repair-of", default=FAILED_RECEIPT)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        if args.probe not in ("dispatch", "guard", "coverage", "preflight"):
            parser.error("--worker is only for offline dispatch/guard/coverage/preflight")
        functions = {"guard": guard_sensitivity, "coverage": coverage_sensitivity,
                     "dispatch": dispatch_sensitivity, "preflight": preflight_sensitivity}
        print(json.dumps(functions[args.probe](), sort_keys=True))
        return
    run = Run("evidence/preparation/independent-simulation-tiering-" + args.probe,
              "simulation tiering repair:" + args.probe, repair_of=args.repair_of)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        if args.probe in ("dispatch", "guard", "coverage", "preflight"):
            run.versions([("python3", "--version")])
            text, _ = run.tool(["python3", "tests/simulation_tiering_checks.py",
                               "--probe", args.probe, "--worker"])
            result = json.loads(text)
            preflight = result if args.probe == "preflight" else result.get("execution_contract_preflight")
            if preflight is not None:
                write_json(run.path / "execution-contract.json", preflight["execution_contract"])
        elif args.probe == "portability":
            from compatibility_checks import compact_portability
            run.versions([("iverilog", "-V"), ("vvp", "-V"), ("verilator", "--version")])
            result = compact_portability(run)
        else:
            run.versions([("iverilog", "-V"), ("vvp", "-V")] if args.simulator == "iverilog"
                         else [("verilator", "--version")])
            if args.probe == "legacy":
                if args.simulator != "verilator":
                    raise ValueError("interrupted legacy workload requires compiled simulation")
                g = next(compatibility_geometries())
                result = decoder_case(run, g, simulator="verilator",
                                      tokens=[1, 2, 1, 2, 1, 2, 1], first_new=1,
                                      label="legacy-c1")
            else:
                g = replace(startup_geometry(3), BANKS=1, INTERMEDIATE_SIZE=8, VOCAB_SIZE=1)
                result = decoder_case(run, g, simulator=args.simulator,
                                      tokens=[0], prefill_tokens=1, label="compact-portability")
                if result["cycles"] > 500000:
                    raise AssertionError("portability smoke exceeds compact cycle tier")
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    run.finish("passed", result=result)


if __name__ == "__main__":
    main()
