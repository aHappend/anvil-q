"""Bounded performance/equivalence diagnostics, never full-product acceptance."""

import copy
import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parent.parent


def public_summary(row):
    log = (ROOT / row["simulation_receipt"]["stdout"]).read_text()
    return [line for line in log.splitlines()
            if line.startswith(("BOOT_OBSERVATION ", "BOOT_TRANSACTIONS ", "COMPARED "))]


def boot_performance(evidence, prior_receipts):
    from qwen_integration import save
    from storage import boot_test

    evidence.tools(("python3", "iverilog", "vvp", "verilator", "g++", "make"))
    evidence.record["performance_scope"] = (
        "Bounded boot-driver equivalence and one upper-capacity performance cell; "
        "links attempt-0095, not a full L1 retry or an RTL repair.")
    rows = []
    for label, optimize, explicit in (
            ("baseline", False, False), ("optimized", True, False),
            ("explicit", True, True)):
        scope = copy.copy(evidence)
        scope.name_prefix = label + "-"
        rows.append(boot_test(scope, 4097, 17, capacity=4097, trace=True,
                              label=label, optimize=optimize, explicit_clock=explicit))
    for row in rows[1:]:
        assert row["source_sha256"] == rows[0]["source_sha256"]
        assert [item["sha256"] for item in row["input_files"]] == [
            item["sha256"] for item in rows[0]["input_files"]]
        assert public_summary(row) == public_summary(rows[0]), "Public boot trace changed"
        assert row["actual_comparisons"] == rows[0]["actual_comparisons"] > 0
    assert rows[-1]["clock_template"] == "boot"
    assert any(line.startswith("BOOT_OBSERVATION ") for line in public_summary(rows[0]))
    measurements = [{
        "variant": label, "simulation_seconds": row["simulation_receipt"]["duration_s"],
        "compile_seconds": row["compile_receipt"]["duration_s"],
        "comparisons": row["actual_comparisons"], "public_summary": public_summary(row),
        "compile_options": row["compile_options"],
    } for label, row in zip(("baseline", "optimized", "explicit"), rows)]
    evidence.record["boot_clock_equivalence"] = measurements
    save(evidence.path / "boot-clock-equivalence.json", measurements)

    # Keep a four-state compact portability witness, and all admitted seeds on C++.
    scope = copy.copy(evidence)
    scope.simulator_override = "iverilog"
    portable = boot_test(scope, 257, 17, reload=True, label="portable",
                         optimize=False, explicit_clock=False)
    assert portable["simulator"] == "iverilog"
    for seed in (1, 17, 89):
        boot_test(evidence, 257, seed, reload=True, label="seeded",
                  optimize=True, explicit_clock=True)
    for fault in ("crc", "ddr-error", "ddr-read-error", "flash-truncation"):
        boot_test(evidence, 257, 17, fault, optimize=True, explicit_clock=True)

    assert len(prior_receipts) == 1, "Expected the retained upper-capacity boot receipt"
    path = ROOT / prior_receipts[0]
    prior = json.loads(path.read_bytes())
    assert (prior["exit_code"] == 0 and not prior["timed_out"] and
            prior["child_settled"] and prior["process_group_settled"])
    ancestor = next(parent for parent in path.parents
                    if parent.parent == ROOT / "evidence/verification")
    launch = json.loads((ancestor / "launch.json").read_bytes())
    assert all(value == evidence.record["source_sha256"][name]
               for name, value in launch["source_sha256"].items()
               if name.startswith(("rtl/", "anvil_q1_reference/")))
    original_log = (ROOT / prior["stdout"]).read_text()
    original_summary = [line for line in original_log.splitlines()
                        if line.startswith(("BOOT_TRANSACTIONS ", "COMPARED "))]
    assert len(original_summary) == 2 and "COMPARED 6443256" in original_summary
    large = boot_test(evidence, 262144, 17, capacity=262144)
    assert large["clock_driver"] == "explicit-cycle" and large["clock_template"] == "boot"
    assert "OPT_FAST=-O3" in " ".join(large["compile_options"])
    assert public_summary(large) == original_summary
    old_inputs = [argument.split("=", 1)[1] for argument in prior["argv"]
                  if argument.startswith("+verification_file")]
    assert len(old_inputs) == len(large["input_files"]) == 4
    assert [hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in old_inputs] == [
        item["sha256"] for item in large["input_files"]]
    evidence.record["upper_boot_performance"] = {
        "prior_receipt": prior_receipts[0], "associated_runtime_attempt": "attempt-0095",
        "prior_seconds": prior["duration_s"],
        "candidate_seconds": large["simulation_receipt"]["duration_s"],
        "speed_ratio": prior["duration_s"] / large["simulation_receipt"]["duration_s"],
        "comparisons": large["actual_comparisons"],
        "identical_input_hashes_and_exact_scoreboard_counts": True,
        "limitation": "Historical baseline vs fresh candidate on shared execution; "
                      "compact serial pairs establish clock equivalence. Not STA/HIL.",
    }
    save(evidence.path / "upper-boot-performance.json",
         evidence.record["upper_boot_performance"])


def stage_performance(evidence):
    from qwen_integration import run_rtl, save
    from table_artifacts import complete_tables, sha256, validate_producer
    from verify import run_stages

    evidence.tools(("python3", "iverilog", "vvp", "verilator", "g++", "make"))
    observations = []

    def stage(scope, family, consume):
        started = time.monotonic()
        producer, info = complete_tables(scope, family)
        generation_ready = time.monotonic() - started
        record = json.loads((producer / "official-vectors.json").read_bytes())
        vectors = record if family == "qwen" else [
            {"case": index, "input_utf8_hex": row["utf8_hex"],
             "token_ids": row["token_ids"], "decoded_utf8_hex": row["decoded_utf8_hex"]}
            for index, row in enumerate(record["vectors"])]
        if consume:
            compact = [row for row in vectors if row["input_utf8_hex"] == "65cc81"]
            assert len(compact) == 1
            run_rtl(scope, info, vectors[:5] + compact, family,
                    table_source=producer / "tables.hex")
        observations.append({"family": family, "consume": consume,
                             "stage": scope.relative(scope.path),
                             "producer": scope.relative(producer),
                             "producer_ready_seconds": generation_ready})

    def produce_qwen(scope):
        stage(scope, "qwen", False)

    def consume_qwen(scope):
        stage(scope, "qwen", True)

    def produce_deepseek(scope):
        stage(scope, "deepseek", False)

    def consume_deepseek(scope):
        stage(scope, "deepseek", True)

    run_stages(evidence, (produce_qwen, consume_qwen, produce_deepseek, consume_deepseek))
    assert len(observations) == 4 and len({row["stage"] for row in observations}) == 4
    assert len(evidence.record["complete_table_producers"]) == 2
    for family in ("qwen", "deepseek"):
        assert len({row["producer"] for row in observations if row["family"] == family}) == 1
    rows = list(evidence.record["coverage"])
    assert len(rows) == 8 and all(row["status"] == "passed" for row in rows)
    bindings = sorted(evidence.path.glob("case-*/table-binding-*.json"))
    assert len(bindings) == 4
    binding_rows = [json.loads(path.read_bytes()) for path in bindings]
    assert sum(row["cache_hit"] for row in binding_rows) == 2
    producers = list(evidence.record["complete_table_producers"])
    frozen = {row["producer"]: json.loads(
        (ROOT / row["producer"] / "producer.json").read_bytes())["outputs"]
              for row in producers}
    for directory, outputs in frozen.items():
        assert all(sha256(ROOT / directory / name) == expected
                   for name, expected in outputs.items())

    # Absent and stale cache entries are in-memory faults, not edits to evidence.
    key = "deepseek-raw"
    original = evidence.complete_table_producers[key]
    evidence.complete_table_producers[key] = {
        **original, "directory": "intentionally-absent-producer"}
    missing, _ = complete_tables(evidence, "deepseek")
    assert missing != ROOT / observations[-1]["producer"]
    stale = evidence.complete_table_producers[key]
    evidence.complete_table_producers[key] = {**stale, "manifest_sha256": "0" * 64}
    repaired, _ = complete_tables(evidence, "deepseek")
    assert repaired != missing
    assert len(evidence.record["table_producer_recoveries"]) == 2
    assert len(evidence.record["complete_table_producers"]) == 4
    validate_producer(evidence, original)
    validate_producer(evidence, stale)
    for directory, outputs in frozen.items():
        assert all(sha256(ROOT / directory / name) == expected
                   for name, expected in outputs.items())
    summary = {
        "scope": "Four concurrent independent stage scopes, two actual complete official "
                 "table producers; six tokenizer vectors/family, seeds 1/17/89 and "
                 "compact Icarus witnesses, not weighted inference or full L1",
        "observations": sorted(observations, key=lambda row: (row["family"], row["consume"])),
        "stage_batch": evidence.record["case_batches"][0],
        "producer_cache_hits": 2, "missing_or_stale_regenerations": 2,
        "earlier_producers_unchanged": True,
        "comparisons": sum(row["actual_comparisons"] for row in rows),
        "generations": evidence.record["complete_table_producers"],
    }
    evidence.record["official_stage_performance"] = summary
    save(evidence.path / "official-stage-performance.json", summary)


def performance_controls(evidence, prior_receipts):
    """Current-source producer policy, shell preparation and mutation regressions."""
    from unittest.mock import patch
    from deepseek_integration import bos_mutations
    from mutations import run_mutations
    from qwen_integration import run_rtl, save
    from scheduling import scheduling_controls
    from table_artifacts import complete_tables, sha256, validate_producer
    from verify import fifo_test

    evidence.tools(("python3", "iverilog", "vvp", "verilator", "g++", "make"))
    parents = []
    for name in prior_receipts:
        prior = json.loads((ROOT / name).read_bytes())
        assert prior["sources_unchanged"] and prior["child_settled"]
        if prior["exit_code"] != 0:
            assert "performance-controls-" in name
            evidence.record.setdefault("retained_failed_controls", []).append({
                "path": name, "sha256": sha256(ROOT / name),
                "reason": prior["reason"], "acceptance_evidence": False})
            continue
        assert all(not child["timed_out"] and child["child_settled"] and
                   child["process_group_settled"] for child in prior["children"])
        assert all(evidence.record["source_sha256"][source] == expected
                   for source, expected in prior["source_sha256"].items()
                   if not source.startswith("tests/"))
        parents.append({"path": name, "sha256": sha256(ROOT / name)})
    evidence.record["performance_parents"] = parents
    evidence.child(["python3", "tests/scheduling.py", "--source-contract"],
                   "source-contract")
    evidence.child(["python3", "tests/test_qwen_templates.py"], "template-regression")
    scheduling_controls(evidence)

    producer, _ = complete_tables(evidence, "qwen")
    entry = dict(evidence.complete_table_producers["qwen-raw"])
    before_children = len(evidence.record["children"])
    denied = PermissionError(13, "Synthetic denied-path control", str(producer / "producer.json"))
    with patch("table_artifacts.validate_producer", side_effect=denied):
        try:
            complete_tables(evidence, "qwen")
        except PermissionError as error:
            assert error is denied
        else:
            raise AssertionError("Denied producer access was bypassed")
    assert len(evidence.record["children"]) == before_children
    assert evidence.complete_table_producers["qwen-raw"] == entry
    validate_producer(evidence, entry)
    evidence.record["denied_producer_control"] = {
        "scope": "Synthetic PermissionError fixture, not an actual filesystem denial",
        "error": str(denied), "propagated": True, "regeneration_attempted": False}

    generated = {}
    for variant in ("standalone", "reused"):
        directory = evidence.path / ("shell-images-" + variant)
        directory.mkdir()
        argv = ["./.venv/bin/python", "tests/qwen_shell.py", evidence.relative(directory)]
        if variant == "reused":
            validated, _ = complete_tables(evidence, "qwen")
            assert validated == producer
            argv.extend(("--table-source", evidence.relative(validated)))
        child = evidence.child(argv, "shell-images-" + variant)
        reference = json.loads((directory / "shell-reference.json").read_bytes())
        files = {path.name: sha256(path) for path in sorted(directory.glob("shell-*.hex"))}
        assert len(files) == 32 and len(reference["cases"]) == 5
        generated[variant] = {"reference": reference, "files": files, "child": child}

    def without_paths(value):
        if isinstance(value, dict):
            return {key: without_paths(item) for key, item in value.items() if key != "path"}
        if isinstance(value, list):
            return [without_paths(item) for item in value]
        return value

    assert generated["standalone"]["files"] == generated["reused"]["files"]
    assert without_paths(generated["standalone"]["reference"]) == without_paths(
        generated["reused"]["reference"])
    evidence.record["shell_image_reuse"] = {
        "scope": "Image/reference preparation only; full-table shell simulation not run",
        "files_sha256": generated["reused"]["files"],
        "complete_references_equal_except_paths": True,
        "standalone_seconds": generated["standalone"]["child"]["duration_s"],
        "reuse_seconds": generated["reused"]["child"]["duration_s"],
    }

    previous = next(json.loads((ROOT / name).read_bytes()) for name in prior_receipts
                    if "official-stage-performance-" in name)
    old_producer = next(row["producer"] for row in previous["complete_table_producers"]
                        if row["key"] == "qwen-raw")
    rejected = evidence.path / "rejected-cross-invocation"
    rejected.mkdir()
    result = evidence.child(
        ["./.venv/bin/python", "tests/qwen_shell.py", evidence.relative(rejected),
         "--table-source", old_producer], "cross-invocation-rejection", allow_failure=True)
    output = (ROOT / result["stdout"]).read_text() + (ROOT / result["stderr"]).read_text()
    assert (result["exit_code"] not in (0, None) and not result["timed_out"] and
            result["child_settled"] and result["process_group_settled"] and
            "Complete tables must belong to the same fresh invocation" in output)
    assert not list(rejected.iterdir())
    evidence.record["cross_invocation_producer_rejected"] = result

    producer, info = complete_tables(evidence, "deepseek", model_bos=True)
    record = json.loads((producer / "model-bos-vectors.json").read_bytes())
    vectors = [{"case": index, "input_utf8_hex": row["utf8_hex"],
                "token_ids": row["token_ids"], "decoded_utf8_hex": row["decoded_utf8_hex"]}
               for index, row in enumerate(record["vectors"])]
    compact = [row for row in vectors if row["input_utf8_hex"] == "65cc81"]
    assert len(compact) == 1
    run_rtl(evidence, info, vectors[:5] + compact, "deepseek-bos",
            table_source=producer / "tables.hex")
    bos_mutations(evidence, info, compact, table_source=producer / "tables.hex")
    assert len(evidence.record["bos_mutations"]) == 2
    run_mutations(evidence, fifo_test)
    save(evidence.path / "performance-controls.json", {
        "scope": "Bounded current-source harness and defect-sensitivity checks, not full L1",
        "parents": parents, "denied_access_propagated": True,
        "cross_invocation_rejected": True, "bos_mutants_killed": 2,
        "shell_image_reuse": evidence.record["shell_image_reuse"],
        "original_mutation_suite": evidence.relative(evidence.path / "mutation-results.json"),
    })
