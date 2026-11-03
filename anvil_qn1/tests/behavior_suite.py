"""Requirement-to-component behavior orchestration.

Retained components qualify only with matching computational sources, geometry,
tools, completed commands and retained raw output. Missing/stale components run
automatically. L1 fusion uses the authorized compact two-layer geometry and
retains profile identities; it is not a production-geometry timing measurement.
"""

from behavior_checks import run_behavior_core
from component_cache import component, long_context, marker_case, marker_source_equivalence
from control_checks import controller_scenarios, run_controller
from fault_checks import FAULT_CASES, run_fault_matrix
from memory_checks import run_memory_matrix
from model import Geometry
from parent_checks import run_parent
from prefill_marker_checks import run_prefill_marker
from production_checks import PROFILES, run_fusion_profile
from speculative_fault_checks import SPECULATIVE_CANCEL_CASES, run_speculative_cancel_matrix
from telemetry_checks import run_telemetry


TOOLS = ("python3", "verilator", "g++", "make")
MODEL = ("tests/model.py", "tests/reference.py", "tests/integration.py")
SPECULATION = (*MODEL, "tests/speculation_checks.py")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def validate_core(result):
    cases = result.get("cases", [])
    require(len(cases) == result.get("case_count") == 15, "missing behavior-core cases")
    shapes = {(c["geometry"]["q_heads"], c["prefix"], c["branching"])
              for c in cases if c["geometry"]["max_sequence"] == 16}
    require(shapes == {(ratio, prefix, False) for ratio in (2, 4) for prefix in range(5)}
            | {(ratio, 2, True) for ratio in (2, 4)},
            "missing prefix/branch/GQA coverage")
    require({c["seed"] for c in cases} == {17, 89, 203}, "missing behavior seeds")
    require({c["geometry"]["max_sequence"] for c in cases} == {3, 6, 7, 16},
            "missing capacity/terminal boundary")
    require({c["continuation_fault"] for c in cases} == {1, 2, 3, 4},
            "missing wrong-token/skip/resend/exhaustion rejection")
    for case in cases:
        geometry = Geometry(**case["geometry"])
        require(geometry == Geometry(q_heads=geometry.q_heads,
                                     max_sequence=geometry.max_sequence),
                "changed behavior-core geometry")
        require(len(case["evaluations"]) >= 6 or geometry.max_sequence < 6,
                "missing six compared logical steps")
        require(len(case["transactions"]) >= 3, "missing deferred second transaction")
        require(f"REJECTED continuation_fault={case['continuation_fault']}" in
                case["raw_summary"], "missing observed invalid-continuation rejection")
    frames = sum(len(c["evaluations"]) for c in cases)
    words = sum(len(c["evaluations"]) * c["geometry"]["vocabulary"] for c in cases)
    require(result.get("compared_frames") == frames > 0 and
            result.get("compared_logit_words") == words > 0,
            "incomplete behavior comparison totals")


def validate_memory(result):
    from resume_checks import validate_memory_matrix

    validate_memory_matrix(result)
    cases = result.get("cases", [])
    require(len(cases) == 6 and
            {(c["banks"], c["queue_depth"]) for c in cases} ==
            {(b, q) for b in (1, 8) for q in (1, 3, 16)},
            "missing bank/queue boundary")
    require({c["seed"] for c in cases} == {17, 89, 203} and
            {c["geometry"]["q_heads"] for c in cases} == {2, 4},
            "missing memory seeds/GQA")
    for case in cases:
        require(len(case["transactions"]) == 6, "missing six memory continuation frames")
        if case["banks"] > 1 and case["queue_depth"] > 1:
            require(case["reordered_responses"] > 0, "bank reordering not observed")
    require(result.get("compared_frames") == 36 and
            result.get("compared_logit_words") ==
            sum(6 * c["geometry"]["vocabulary"] for c in cases),
            "missing memory comparison totals")


def validate_faults(result):
    cases = result.get("cases", [])
    require(len(cases) == result.get("case_count") == len(FAULT_CASES) and
            {c["kind"] for c in cases} == set(FAULT_CASES),
            "missing memory/protocol/cancel fault")
    for case in cases:
        kind, counts = case["kind"], case["counts"]
        require(case["case"] == FAULT_CASES[kind] and
                case["geometry"] == vars(Geometry()) and
                (case["banks"], case["queue"], case["seed"]) == (8, 3, 17),
                "changed fault fixture identity")
        require(counts[:4] == [kind, 4 if kind == 8 else 3, 2 if kind <= 8 else 1,
                              int(kind >= 9 and kind != 14)] and
                counts[5:] == [int(kind == 13), 16],
                "missing observed fault/publication/recovery comparisons")
    require(result.get("recovery_frames") == 2 * len(cases),
            "missing fault recovery frames")


def validate_speculative_cancels(result):
    cases = result.get("cases", [])
    require(len(cases) == result.get("case_count") == len(SPECULATIVE_CANCEL_CASES) and
            {c["kind"] for c in cases} == set(SPECULATIVE_CANCEL_CASES),
            "missing speculative cancellation stage")
    for case in cases:
        kind, counts = case["kind"], case["counts"]
        require(case["case"] == SPECULATIVE_CANCEL_CASES[kind] and
                case["geometry"] == vars(Geometry()) and case["seed"] == 17,
                "changed speculative cancellation identity")
        require(counts[0] == kind and counts[1] > 0 and counts[2] > 0 and
                counts[4:] == [int(kind == 5), len(case["evaluations"]),
                               len(case["transactions"])],
                "missing cancellation/publication/recovery comparisons")
    require(result.get("recovery_frames") == sum(len(c["evaluations"]) for c in cases),
            "missing speculative recovery frame total")


def validate_telemetry(result):
    require(result.get("geometry") == vars(Geometry()) and
            result.get("seed") == 17 and result.get("prefix") == 4,
            "changed integrated CSR fixture")
    counts = result["counts"]
    generated = sum(len(t["generated"]) for t in result["transactions"])
    drafts = sum(len(t["nodes"]) for t in result["transactions"])
    accepted = 0
    for transaction in result["transactions"]:
        parent = 4
        for token in transaction["generated"]:
            children = [index for index, (node, ancestor) in
                        enumerate(zip(transaction["nodes"], transaction["parents"]))
                        if node == token and ancestor == parent]
            if not children:
                break
            accepted += 1
            parent = children[0]
    require(len(result["transactions"]) == 3 and counts[0] == 45 and
            counts[1] == counts[2] + counts[3] and counts[1] > 0 and
            counts[4:] == [generated, 0, drafts,
                           len(result["evaluations"]) - 3, accepted,
                           drafts - accepted, 2],
            "missing actual-event CSR classification/snapshot/cycle comparisons")


def validate_controller(result):
    expected = controller_scenarios()
    require(result.get("coverage_names") == [c["name"] for c in expected] and
            result.get("cases") == len(expected) and
            result.get("prefix_lengths") == list(range(5)) and
            result.get("cancel_stages") == [1, 2, 3, 4],
            "missing controller tree/marker/priority cases")
    require(result.get("commits") ==
            sum(not c["fault"] and c["cancel"] in (0, 4) for c in expected) and
            result.get("faults") == sum(bool(c["fault"]) for c in expected),
            "missing compared controller outcomes")


def validate_parent(result):
    counts = result.get("counts", [])
    require(counts[:2] == [6, 24] and counts[2] > 0 and counts[-2:] == [96, 127] and
            len(result.get("expected_logits_q16", [])) == 6 and
            result.get("reference_cycles") == counts[2] and
            result.get("reference_committed_tokens") == 6 and
            result.get("token_counts", {}).get("generated_commit_bus_transfers") == 0,
            "missing unchanged-parent execution/numerical/count semantics")


def prefill_case(run, opening):
    from resume_checks import validate_marker_receipt

    def validate(result):
        require(result.get("counts", [])[:5] ==
                [int(opening), 151936, 0, 0, 152],
                "missing prefill marker/no-generated-token comparisons")

    return component(
        run, "prefill-marker", lambda child: run_prefill_marker(child, opening, threads=8),
        inputs=("tests/prefill_marker_checks.py", "tests/marker_checks.py",
                "tests/speculation_checks.py", "tests/model.py", "tests/reference.py"),
        parameters={"opening": opening, "input_marker": 151667 if opening else 151668,
                    "simulation_threads": 8},
        tools=TOOLS, validate=validate, equivalence=marker_source_equivalence,
        validate_retained=validate_marker_receipt)


def run_behavior_components(run):
    """Protocol/numerical components, excluding the separate fusion comparisons."""
    from resume_checks import orchestration_equivalence

    jobs = (
        ("behavior-core", run_behavior_core,
         (*SPECULATION, "tests/behavior_checks.py"), validate_core),
        ("memory-matrix", run_memory_matrix,
         (*MODEL, "tests/memory_checks.py"), validate_memory),
        ("fault-matrix", run_fault_matrix,
         (*SPECULATION, "tests/memory_checks.py", "tests/fault_checks.py"), validate_faults),
        ("speculative-cancel", run_speculative_cancel_matrix,
         (*SPECULATION, "tests/speculative_fault_checks.py"), validate_speculative_cancels),
        ("integrated-csr", run_telemetry,
         (*SPECULATION, "tests/telemetry_checks.py"), validate_telemetry),
        ("parent-reference", run_parent,
         ("anvil_q3_reference/rtl/*.sv", "tests/parent_checks.py"), validate_parent),
        ("controller", run_controller, ("tests/control_checks.py",), validate_controller),
    )
    results = {}
    for stem, operation, inputs, validate in jobs:
        results[stem] = component(run, stem, operation, inputs=inputs, parameters={},
                                  tools=TOOLS, validate=validate,
                                  equivalence=orchestration_equivalence,
                                  aliases=("smoke-controller",) if stem == "controller" else ())
    results["attention-context"] = long_context(run)
    for opening in (True, False):
        suffix = "open" if opening else "close"
        results[f"generated-marker-{suffix}"] = marker_case(run, opening)
        results[f"prefill-marker-{suffix}"] = prefill_case(run, opening)
    return {"scope": "protocol/numerical components; compact fusion is separate",
            "components": results}


def validate_fusion(result, profile):
    g = Geometry(layers=2, vocabulary=8)
    geometry = vars(g)
    require(profile in PROFILES and result.get("profile") == profile and
            result.get("compact_diagnostic") is True,
            "missing explicitly labeled compact profile measurement")
    fused, baseline = result["fused"], result["without_norm"]
    for record, normalized in ((fused, True), (baseline, False)):
        require(record.get("geometry") == geometry and
                record.get("profile") == profile and
                record.get("normalization") is normalized and
                record.get("compact_diagnostic") is True and
                type(record.get("cycles")) is int and record["cycles"] > 0 and
                type(record.get("requests")) is int and record["requests"] > 0,
                "missing compact two-layer invocation")
        require(record.get("parameters") == {
                    "PROFILE": profile, "COMPACT": 1, "BANKS": 8,
                    "NUM_LAYERS": g.layers, "HIDDEN_SIZE": g.hidden,
                    "INTERMEDIATE_SIZE": g.intermediate, "NUM_Q_HEADS": g.q_heads,
                    "NUM_KV_HEADS": g.kv_heads, "HEAD_DIM": g.head_dim,
                    "VOCAB_SIZE": g.vocabulary, "MAX_SEQ_LEN": g.max_sequence,
                    "GROUP_SIZE": g.group},
                "changed compact fusion elaboration parameters")
        require(record.get("compared_writes") ==
                7 * g.hidden + 2 * g.q_dimension + 4 * g.kv_dimension + 3 * g.intermediate and
                record.get("key_writes") == record.get("value_writes") == g.kv_dimension,
                "incomplete compact layer/projection/norm/KV comparisons")
    for field in ("parameters", "simulation_threads", "measurement", "memory"):
        require(fused.get(field) == baseline.get(field),
                f"fusion comparison changed {field}")
    difference = fused["cycles"] - baseline["cycles"]
    require(fused["requests"] == baseline["requests"] and
            result.get("extra_cycles") == difference and
            result.get("threshold_percent_strict") == 2 and
            100 * difference < 2 * baseline["cycles"],
            "measured normalization overhead is not strictly below 2%")


def fusion_components(run):
    results = {}
    for profile in (1, 2, 3):
        results[str(profile)] = component(
            run, "fusion-compact" if profile == 1 else f"fusion-compact-profile{profile}",
            lambda child, profile=profile: run_fusion_profile(child, profile, compact=True),
            inputs=(*MODEL, "tests/production_checks.py"),
            parameters={"profile": profile, "compact_diagnostic": True},
            tools=TOOLS, validate=lambda result, profile=profile: validate_fusion(result, profile),
            aliases=("fusion-compact",) if profile != 1 else ())
    return results


def run_behavior(run):
    results = run_behavior_components(run)
    results["compact_fusion"] = fusion_components(run)
    results["scope"] = (
        "behavior components and three profile-labeled compact measured fusion comparisons; "
        "production-geometry measurements remain separate")
    return results
