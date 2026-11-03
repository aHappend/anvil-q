"""Default dispatch of every admitted L1 suite under the same cumulative budget.

An exact-source complete suite may be reused after recursive source/tool/command
and artifact checks. Missing/stale work executes, never becomes a skip or pass.
The no-argument aggregate has the same 2700-second budget: a cold campaign that
does not fit fails explicitly and retains its completed children.
"""

from benchmark_checks import DOMAINS, run_benchmark
from behavior_suite import (run_behavior, validate_controller, validate_core, validate_faults,
                            validate_fusion, validate_memory, validate_parent,
                            validate_speculative_cancels, validate_telemetry)
from component_cache import component
from defect_checks import run_defects
from numerical_checks import run_numerical
from reproduction_checks import run_reproduce
from smoke_checks import run_smoke
from synthesis_checks import run_synthesis


def jobs():
    return [
        ("smoke", run_smoke), ("numerical", run_numerical), ("behavior", run_behavior),
        *[(f"benchmark-{domain}", lambda run, domain=domain: run_benchmark(run, domain))
          for domain in DOMAINS],
        ("defects", run_defects), ("synthesis", run_synthesis), ("reproduce", run_reproduce),
    ]


def require_complete(result, name):
    if not isinstance(result, dict) or not result:
        raise AssertionError("missing complete suite results")
    if name == "smoke":
        if (len(result.get("startup", [])) != 9 or len(result.get("leaves", {})) != 8 or
                not result.get("elaboration") or not result.get("controller")):
            raise AssertionError("incomplete smoke suite")
    elif name == "numerical":
        if (result.get("tensor", {}).get("tensor_cases") != 1536 or
                result.get("qk", {}).get("compared_elements") != 99200 or
                len(result.get("coefficients", [])) != 10 or not result.get("elementary")):
            raise AssertionError("incomplete numerical suite")
    elif name == "behavior":
        components = result.get("components", {})
        for stem, validate in (
                ("behavior-core", validate_core), ("memory-matrix", validate_memory),
                ("fault-matrix", validate_faults),
                ("speculative-cancel", validate_speculative_cancels),
                ("integrated-csr", validate_telemetry), ("parent-reference", validate_parent),
                ("controller", validate_controller)):
            validate(components[stem])
        required = {"attention-context", "generated-marker-open", "generated-marker-close",
                    "prefill-marker-open", "prefill-marker-close"}
        if not required <= components.keys():
            raise AssertionError("incomplete integrated marker/context suite")
        for profile in (1, 2, 3):
            validate_fusion(result["compact_fusion"][str(profile)], profile)
    elif name.startswith("benchmark-"):
        domain = name.removeprefix("benchmark-")
        cases = result.get("cases", [])
        if (result.get("domain") != domain or result.get("fixture_count") != 4 or
                len(cases) != 8 or result.get("compared_frames") != 72 or
                result.get("compared_logit_words") != 576 or
                {(c["fixture"]["id"], c["thinking"]) for c in cases} !=
                {(identifier, mode) for identifier in
                 {c["fixture"]["id"] for c in cases} for mode in (False, True)} or
                len({c["fixture"]["id"] for c in cases}) != 4 or
                any(c.get("generated_tokens") != 6 or c.get("decode_cycles", 0) <= 0
                    for c in cases)):
            raise AssertionError("incomplete benchmark domain/mode suite")
    elif name == "defects":
        from defect_checks import MUTANTS
        if (result.get("detected_count") != len(MUTANTS) or
                {c["mutant"] for c in result.get("detections", [])} != set(MUTANTS) or
                any(not c.get("detected") or c.get("checker_exit") in (None, 0) or
                    c.get("compilation_exit") != 0 or not c.get("comparison_diagnostics")
                    for c in result["detections"])):
            raise AssertionError("incomplete executed RTL mutation suite")
    elif name == "synthesis":
        if (result.get("case_count") != 7 or len(result.get("cases", [])) != 7 or
                result.get("production_profiles") != [1, 2, 3] or
                result.get("compact_boundaries") != 4 or
                any(result.get(key) != 0 for key in
                    ("latches", "combinational_div_mod", "unresolved_blackboxes"))):
            raise AssertionError("incomplete synthesis suite")
    elif name == "reproduce":
        if (result.get("child_probe") != "reproduce-child" or not result.get("child_receipt") or
                not result.get("source_sha256") or
                any(len(result.get("results", {}).get(key, [])) != 2
                    for key in ("startup", "scalar", "qk", "tensor"))):
            raise AssertionError("incomplete clean-directory reproduction")
    else:
        raise ValueError(f"unknown mandatory suite: {name}")


def tools_for(name):
    base = ("python3", "verilator", "g++", "make")
    if name == "synthesis":
        return ("python3", "yosys")
    if name == "behavior":
        return (*base, "yosys")
    if name in ("smoke", "numerical", "reproduce"):
        return (*base, "iverilog", "vvp")
    return base


def run_all(run):
    results = {}
    for name, operation in jobs():
        results[name] = component(
            run, name, operation,
            inputs=("tests/*.py", "anvil_q3_reference/rtl/*.sv"),
            parameters={"domain": name.removeprefix("benchmark-")} if name.startswith(
                "benchmark-") else {},
            tools=tools_for(name),
            validate=lambda result, name=name: require_complete(result, name))
    if set(results) != {name for name, _ in jobs()} or len(results) != 11:
        raise AssertionError("default dispatch omitted a mandatory L1 suite/domain")
    return {"scope": "all mandatory L1 suites; compact regulation, not physical signoff",
            "suites": results, "suite_count": len(results)}
