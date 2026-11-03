"""Resumable real-domain simulations and executable mutation comparisons."""

import hashlib
import json
from pathlib import Path
import re
import tempfile

from component_cache import assess, component
from execution import ROOT, relative
from model import Geometry
from resume_checks import MODEL, TOOLS, orchestration_equivalence, require


BENCHMARK_INPUTS = (*MODEL, "tests/speculation_checks.py", "tests/benchmark_checks.py")
DEFECT_INPUTS = (*MODEL, "tests/speculation_checks.py", "tests/control_checks.py",
                 "tests/leaf_checks.py", "tests/defect_checks.py")


def validate_benchmark_case(result, fixture, family, seed, thinking):
    from benchmark_checks import FIXTURE_MANIFEST_SHA256, compact_tokens

    require(result.get("fixture") == fixture and
            result.get("fixture_manifest_sha256") == FIXTURE_MANIFEST_SHA256 and
            (result.get("family"), result.get("seed"), result.get("thinking")) ==
            (family, seed, thinking) and
            result.get("geometry") == vars(Geometry(q_heads=4 if family == 3 else 2)) and
            result.get("prompt_tokens") == compact_tokens(fixture["description"]),
            "benchmark fixture/family/seed/mode/mapping identity mismatch")
    rows = result.get("measurements", [])
    transactions = result["transactions"]
    require(len(rows) == len(transactions) and len(rows) > 0,
            "missing benchmark public-transaction measurements")
    for index, (row, transaction) in enumerate(zip(rows, transactions)):
        require(len(row) == 6 and row[:3] ==
                [index, transaction["phase"], int(thinking and index >= 1)] and
                row[3] > 0 and row[4] == len(transaction["generated"]) and row[5] > 0,
                "benchmark mode/cycle/token/request comparison mismatch")
    decode = [r for r in rows if r[1] == 1]
    require(result.get("compared_frames") == len(result["evaluations"]) == 9 and
            result.get("compared_logit_words") == 72 and
            result.get("generated_tokens") == sum(r[4] for r in decode) == 6 and
            result.get("decode_cycles") == sum(r[3] for r in decode) > 0,
            "missing six decode steps/full frames/throughput measurements")


def validate_benchmark_receipt(run, path, receipt, result):
    from benchmark_checks import benchmark_bench, benchmark_images

    bench = path.parent / "benchmark_tb.sv"
    require(bench.is_file() and bench.read_text() == benchmark_bench(),
            "retained domain bench differs from current computation")
    simulation = [c for c in receipt["commands"]
                  if Path(c["stdout"]).name == "benchmark-simulation.stdout.txt"]
    require(len(simulation) == 1 and simulation[0]["argv"] == [
        result["compiled"]["binary"], f"+images={relative(path.parent / 'checkpoint-images')}",
        f"+transactions={len(result['transactions'])}", f"+thinking={int(result['thinking'])}"],
        "benchmark simulation argv mismatch")
    output = (ROOT / simulation[0]["stdout"]).read_text()
    rows = [list(map(int, row)) for row in re.findall(
        r"^BENCH_TX tx=(\d+) phase=(\d+) mode=(\d+) cycles=(\d+) tokens=(\d+) requests=(\d+)$",
        output, re.M)]
    require(rows == result["measurements"] and output.count(
        f"SUMMARY transactions={len(rows)} frames=9 logits=72 key_writes=72 value_writes=72") == 1,
        "benchmark raw measurements/full-frame/KV comparisons differ")
    with tempfile.TemporaryDirectory(prefix="official-image-", dir=run.path) as directory:
        images = Path(directory) / "checkpoint-images"
        prompt, evaluations, transactions = benchmark_images(
            images, result["fixture"], Geometry(**result["geometry"]),
            result["seed"], result["thinking"])
        expected = {f"checkpoint-images/{p.name}": hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in images.glob("*.hex")}
    require(prompt == result["prompt_tokens"] and evaluations == result["evaluations"] and
            transactions == result["transactions"] and
            expected == receipt.get("transient_image_sha256"),
            "benchmark regenerated independent image/reference mismatch")
    validate_benchmark_build(run, result["compiled"])


def validate_benchmark_build(run, compiled):
    from benchmark_checks import benchmark_bench

    binary = ROOT / compiled["binary"]
    path = binary.parent.parent / "receipt.json"
    require(binary.is_file() and path.is_file(), "missing retained benchmark build")
    receipt = json.loads(path.read_text())
    assessment, _ = assess(run, path, BENCHMARK_INPUTS, {}, TOOLS,
                           equivalence=orchestration_equivalence)
    require(assessment["applicable"], "stale/incomplete benchmark build owner")
    require(hashlib.sha256(binary.read_bytes()).hexdigest() ==
            receipt.get("artifact_sha256", {}).get(binary.relative_to(path.parent).as_posix()),
            "changed benchmark executable")
    binding = compiled["binding"]
    require(binding["bench_sha256"] == hashlib.sha256(benchmark_bench().encode()).hexdigest() and
            binding["rtl_sha256"] == {k: v for k, v in run.hashes.items()
                                     if k.startswith("rtl/anvil_qn1_")} and
            all(binding["tool_versions"].get(t) == run.tool_versions[t] for t in TOOLS),
            "benchmark executable computational source/tool mismatch")
    compiles = [c for c in receipt["commands"] if c["argv"][0] == "verilator"]
    require(len(compiles) == 1 and
            all(f"-G{k}={v}" in compiles[0]["argv"]
                for k, v in binding["parameters"].items()) and
            compiles[0]["argv"][-1] == relative(path.parent / "benchmark_tb.sv"),
            "benchmark executable parameter/bench mismatch")


def benchmark_build(run, family):
    for parent in (ROOT / "evidence/preparation", ROOT / "evidence"):
        paths = sorted(parent.glob("*benchmark-*/receipt.json"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        for path in paths:
            receipt = json.loads(path.read_text())
            result = receipt.get("results")
            if not isinstance(result, dict):
                continue
            compiled = result.get("compiled")
            if (not compiled or compiled.get("binding", {}).get("parameters") !=
                    {"P": family, "QH": 4 if family == 3 else 2} or
                    compiled["binding"].get("tool_versions") != run.tool_versions):
                continue
            try:
                validate_benchmark_build(run, compiled)
            except AssertionError:
                continue
            return compiled
    return None


def benchmark_domain(run, domain):
    from benchmark_checks import (DOMAINS, FIXTURE_MANIFEST_SHA256, check_fixture_manifest,
                                  fixture_manifest, run_benchmark_case)
    from suite_dispatch import require_complete

    if domain not in DOMAINS:
        raise ValueError(f"unknown benchmark domain: {domain}")
    check_fixture_manifest()
    results, builds = [], {}
    for index, fixture in enumerate(fixture_manifest(domain)):
        family, seed = (1, 2, 3, 3)[index], (17, 89, 203, 17)[index]
        if family not in builds:
            builds[family] = benchmark_build(run, family)
        for thinking in (False, True):
            def operation(child, fixture=fixture, family=family, seed=seed, thinking=thinking):
                result = run_benchmark_case(child, fixture, family, seed,
                                            thinking, builds[family])
                builds[family] = result["compiled"]
                return result
            result = component(
                run, f"benchmark-{domain}-case{index}-mode{int(thinking)}", operation,
                inputs=BENCHMARK_INPUTS,
                parameters={"fixture": fixture, "family": family, "seed": seed,
                            "thinking": thinking},
                tools=TOOLS, validate=lambda r, f=fixture, p=family, s=seed, t=thinking:
                validate_benchmark_case(r, f, p, s, t),
                equivalence=orchestration_equivalence,
                validate_retained=validate_benchmark_receipt,
                aliases=(f"benchmark-{domain}-{'thinking' if thinking else 'direct'}",)
                if index == 0 else ())
            results.append(result)
    result = {"domain": domain,
              "scope": "bounded compact real-domain numerical parity, not published accuracy",
              "cases": results, "fixture_manifest_sha256": FIXTURE_MANIFEST_SHA256,
              "fixture_count": 4, "compared_frames": sum(r["compared_frames"] for r in results),
              "compared_logit_words": sum(r["compared_logit_words"] for r in results),
              "modes": {str(int(mode)): {
                  "generated_tokens": sum(r["generated_tokens"] for r in results
                                          if r["thinking"] == mode),
                  "decode_cycles": sum(r["decode_cycles"] for r in results if r["thinking"] == mode),
              } for mode in (False, True)}}
    require_complete(result, f"benchmark-{domain}")
    require({r["family"] for r in results} == {1, 2, 3} and
            {r["geometry"]["q_heads"] for r in results} == {2, 4},
            "missing benchmark profile/GQA coverage")
    return result


def validate_baseline(result, kind):
    from behavior_suite import validate_controller

    if kind == "qk":
        require(result.get("qk_cases") == 17 and result.get("compared_elements") == 136 and
                result.get("dimension") == 8 and result.get("latency") == 133,
                "incomplete passing QK mutation baseline")
    elif kind == "top":
        require(result.get("geometry") == vars(Geometry()) and result.get("seed") == 17 and
                len(result.get("transactions", [])) == 1 and
                "SUMMARY transactions=1 logits=8 key_writes=8 value_writes=8" in
                result.get("raw_summary", ""), "incomplete passing top mutation baseline")
    elif kind == "branch":
        require(result.get("prefix") == 2 and result.get("branching") is True and
                result.get("geometry") == vars(Geometry()) and
                len(result.get("evaluations", [])) == 6 and
                len(result.get("transactions", [])) == 4,
                "incomplete passing speculative mutation baseline")
    elif kind == "controller":
        validate_controller(result)
    elif kind == "csr":
        require(result.get("responses") == 187 and result.get("edges") == 1325 and
                result.get("errors") == 48 and result.get("modes") == 4 and
                result.get("stalls") == 561 and result.get("snapshot_clear") is True and
                result.get("reset_stalled_response") is True,
                "incomplete passing CSR mutation baseline")
    else:
        raise ValueError(f"unknown baseline kind: {kind}")


def validate_detection(result, name):
    from defect_checks import MUTANTS

    source, kind, substitutions, diagnostics = MUTANTS[name]
    require(result.get("mutant") == name and result.get("oracle") == kind and
            result.get("changed_source") == source and result.get("detected") is True and
            result.get("compilation_exit") == 0 and result.get("checker_exit") not in (0, None) and
            result.get("comparison_diagnostics") and
            set(result["comparison_diagnostics"]) <= set(diagnostics),
            "missing real executable mutant comparison failure")


def validate_detection_receipt(run, path, receipt, result):
    from defect_checks import MUTANTS
    from speculation_checks import replace_once

    source, kind, substitutions, diagnostics = MUTANTS[result["mutant"]]
    for name, binding in result["source_sha256"].items():
        require(binding["original"] == run.hashes[name], "mutant parent RTL source changed")
        clone = path.parent / "mutant-source" / Path(name).name
        expected = (ROOT / name).read_text()
        if name == source:
            for before, after in substitutions:
                expected = replace_once(expected, before, after)
        require(clone.is_file() and clone.read_text() == expected and
                hashlib.sha256(clone.read_bytes()).hexdigest() == binding["mutant"],
                "missing/incorrect disposable mutant source")
    commands = receipt["commands"]
    compiles = [c for c in commands if c["argv"][0] == "verilator"]
    simulations = [c for c in commands
                   if Path(c["stdout"]).name.endswith("-simulation.stdout.txt")]
    require(len(compiles) == len(simulations) == 1 and compiles[0]["exit_code"] == 0,
            "mutant compilation missing/unsuccessful")
    simulation = simulations[0]
    require(simulation["exit_code"] == result["checker_exit"] and
            simulation["disposition"] == "exited" and simulation["child_settled"] and
            simulation["stdout"] == result["simulation_stdout"] and
            simulation["stderr"] == result["simulation_stderr"],
            "mutant nonzero comparison execution not retained")
    output = (ROOT / simulation["stdout"]).read_text() + "\n" + (
        ROOT / simulation["stderr"]).read_text()
    require([d for d in diagnostics if d in output] == result["comparison_diagnostics"] and
            not any(marker in output for marker in
                    ("CYCLE_BOUND", "TOKEN_LIVENESS", "MISSING_VECTORS", "OPEN_VECTORS",
                     "READMEM", "cannot open", "No such file")),
            "mutant failure is not a known independent comparison")


def defects_campaign(run):
    from defect_checks import MUTANTS, oracle, run_mutant
    from suite_dispatch import require_complete

    baselines = {}
    for kind in sorted({record[1] for record in MUTANTS.values()}):
        names = [name for name, record in MUTANTS.items() if record[1] == kind]
        baselines[kind] = component(
            run, f"defects-baseline-{kind}", lambda child, kind=kind: oracle(child, kind),
            inputs=DEFECT_INPUTS, parameters={}, tools=TOOLS,
            validate=lambda r, kind=kind: validate_baseline(r, kind),
            equivalence=orchestration_equivalence,
            aliases=tuple(f"mutation-baseline-{name}" for name in names))
    detections = []
    for name in MUTANTS:
        detections.append(component(
            run, f"defects-{name}", lambda child, name=name: run_mutant(child, name),
            inputs=DEFECT_INPUTS, parameters={"mutant": name}, tools=TOOLS,
            validate=lambda r, name=name: validate_detection(r, name),
            equivalence=orchestration_equivalence,
            validate_retained=validate_detection_receipt, aliases=(f"mutation-{name}",)))
    result = {"scope": "executed disposable RTL mutations against independent public-pin oracles",
              "passing_baselines": baselines, "detections": detections,
              "required_mutants": list(MUTANTS), "detected_count": len(detections)}
    require_complete(result, "defects")
    return result


def run_campaign_checker(run):
    """Revalidate all case checkpoints, then reject damaged in-memory summaries."""
    import copy
    from benchmark_checks import DOMAINS
    from checker_checks import rejection
    from suite_dispatch import require_complete

    domains = {name: benchmark_domain(run, name) for name in DOMAINS}
    defects = defects_campaign(run)
    rejected = []
    for domain, result in domains.items():
        for index in range(8):
            broken = copy.deepcopy(result)
            del broken["cases"][index]
            rejected.append(rejection(
                lambda broken=broken, domain=domain: require_complete(
                    broken, f"benchmark-{domain}"), f"{domain}:missing-case-{index}"))
        for case in result["cases"]:
            for field in ("fixture", "family", "seed", "thinking", "measurements",
                          "compared_frames", "generated_tokens", "decode_cycles"):
                broken = copy.deepcopy(case)
                broken[field] = [] if field == "measurements" else None
                rejected.append(rejection(
                    lambda broken=broken, case=case: validate_benchmark_case(
                        broken, case["fixture"], case["family"], case["seed"], case["thinking"]),
                    f"{domain}:{case['fixture']['id']}:{case['thinking']}:changed-{field}"))
    for result in defects["detections"]:
        for field in ("mutant", "detected", "checker_exit", "compilation_exit",
                      "comparison_diagnostics"):
            broken = copy.deepcopy(result)
            broken[field] = 0 if field == "checker_exit" else None
            rejected.append(rejection(
                lambda broken=broken, name=result["mutant"]: validate_detection(broken, name),
                f"mutant:{result['mutant']}:changed-{field}"))
    return {"scope": "checkpoint/checker diagnostics, not mandatory suite acceptance",
            "domains": {name: {"frames": value["compared_frames"],
                              "words": value["compared_logit_words"],
                              "modes": value["modes"]} for name, value in domains.items()},
            "detected_mutants": [r["mutant"] for r in defects["detections"]],
            "rejected_counterexamples": rejected,
            "executed_new_cases": sum(not c.get("reused") for c in run.components)}
