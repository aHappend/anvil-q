"""Executing full-model acceptance consumer, independent of bridge PASS flags."""

import math
import uuid

from benchmark_manifest import CASES, DEFAULT_GEOMETRY, MANIFEST, MANIFEST_SHA256
from evidence import digest, relative, write_json
import hardware_workload as bridge
import ieee_reference as fp


def provenance(record):
    document = bridge.load_json(bridge.artifact(record))
    for key in ("argv", "cwd", "source_sha256", "start_time", "end_time", "stdout", "stderr"):
        if key not in document:
            raise ValueError("reference/comparator execution provenance incomplete")
    if document.get("exit_code") != 0 or document.get("timed_out") is not False:
        raise ValueError("reference/comparator execution failed")
    return document


def fidelity(response, document):
    observations = bridge.load_json(bridge.artifact(response["boundary_observations"]))
    if (observations["model_revision"] != document["model"]["revision"] or
        observations["mode"] != response["mode"] or
        observations["case_id"] != response["case_id"] or
        observations["workload_manifest_sha256"] != MANIFEST_SHA256):
        raise ValueError("reference boundary identity mismatch")
    provenance(observations["native_execution_receipt"])
    provenance(observations["fp64_execution_receipt"])
    if observations.get("independent_mathematical_reference") is not True:
        raise ValueError("FP64 mathematical reference is not independently identified")
    records, covered = [], set()
    for item in observations["boundaries"]:
        actual = [fp.as_float(bridge.uint(word, "FP32 bits", 0xFFFFFFFF)) for word in item["actual_fp32_bits"]]
        reference = item["reference_fp64"]
        if not isinstance(reference, list) or not all(type(v) in (float, int) for v in reference):
            raise ValueError("raw FP64 boundary vector required")
        metrics = fp.fidelity(actual, reference)
        if (metrics["nrmse"] > .02 or metrics["cosine"] < .999 or
            (all(v == 0 for v in reference) and metrics["max_absolute_error"] > 2 ** -18)):
            raise ValueError(f"FP64 fidelity failed: {item['operator']}, {metrics}")
        if item["operator"] not in MANIFEST["observation_boundaries"]:
            raise ValueError("unknown decoder observation boundary")
        covered.add(item["operator"])
        records.append({"operator": item["operator"], "elements": len(actual), **metrics})
    if covered != set(MANIFEST["observation_boundaries"]):
        raise ValueError("missing named operator/logit fidelity boundary")
    if response["mode"] == "w4":
        extra = observations["unquantized_bf16_deviation"]
        provenance(extra["execution_receipt"])
        # Report, never confuse unquantized deviation with W4-counterpart fidelity.
        fp.fidelity(extra["actual"], extra["reference"])
    return records


def comparator(record, kind, document):
    value = bridge.load_json(bridge.artifact(record))
    if (value["schema_version"] != 1 or value["kind"] != kind or
        value["workload_manifest_sha256"] != MANIFEST_SHA256 or
        value["model_revision"] != document["model"]["revision"] or
        value["model_config_sha256"] != document["model"]["config"]["sha256"] or
        value["tokenizer"] != document["model"]["tokenizer"] or
        value["measurement_boundaries"] != MANIFEST["boundaries"] or
        not value["software_versions"] or not value["device_identity"] or
        value["integration_only"] is not False):
        raise ValueError(f"mismatched/nonphysical comparator: {kind}")
    expected_kind = "physical_fpga" if kind != "a100" else "physical_gpu"
    if value["execution_kind"] != expected_kind:
        raise ValueError("comparator is not a real matched measurement")
    if kind == "a100" and (value["device_identity"]["model"] != "NVIDIA A100 80GB" or
                           value["batch_size"] != 1 or value["dtype"] != "BF16"):
        raise ValueError("A100 comparator device/precision/batch mismatch")
    provenance(value["execution_receipt"])
    cases = value["cases"]
    expected = {(mode, case["id"]) for mode in MANIFEST["modes"] for case in CASES}
    keyed = {}
    for case in cases:
        key = case["mode"], case["case_id"]
        if key in keyed or key not in expected:
            raise ValueError("duplicate or unknown comparator case")
        bridge.token_ids(case["output_token_ids"])
        positive = bridge.positive(case["decode_elapsed_ns"], "comparator elapsed")
        if case["end_monotonic_ns"] - case["start_monotonic_ns"] != positive:
            raise ValueError("comparator timing contradiction")
        provenance(case["execution_receipt"])
        keyed[key] = case
    if set(keyed) != expected:
        raise ValueError("incomplete matched comparator workload")
    return keyed


def full_model(directory):
    acceptance = {
        "schema_version": 1, "workload_manifest_sha256": MANIFEST_SHA256,
        "status": "failed", "cases": [
            {"mode": mode, "case_id": case["id"], "status": "not_executed"}
            for mode in MANIFEST["modes"] for case in CASES],
        "aggregates": {}, "missing_prerequisites": [], "failure_reasons": [],
        "predicates": {}, "integration_only": False,
    }
    results = []
    try:
        document, input_path = bridge.inputs()
        prefix = bridge.bridge_prefix()
        acceptance["input_manifest"] = {"path": relative(input_path), "sha256": digest(input_path)}
        comparators = {kind: comparator(record, kind, document)
                       for kind, record in document["comparators"].items()}
        for mode in MANIFEST["modes"]:
            work = directory / f"load-{mode}-{uuid.uuid4().hex[:8]}"
            work.mkdir()
            req = bridge.request(document, CASES[0], mode, "image_validation_load")
            _, load_record = bridge.launch(prefix, req, work)
            acceptance.setdefault("image_loads", {})[mode] = load_record
            for case in CASES:
                record = next(item for item in acceptance["cases"]
                              if item["mode"] == mode and item["case_id"] == case["id"])
                pair = {}
                for job in ("dense_reference", "ht2_speculative_sparse"):
                    work = directory / f"{mode}-{case['id']}-{job}-{uuid.uuid4().hex[:8]}"
                    work.mkdir()
                    req = bridge.request(document, case, mode, job)
                    response, evidence = bridge.launch(prefix, req, work)
                    pair[job] = response
                    record[job] = evidence
                dense, candidate = pair["dense_reference"], pair["ht2_speculative_sparse"]
                if (candidate["output_token_ids"] != dense["output_token_ids"] or
                    candidate["eos_reason"] != dense["eos_reason"]):
                    raise ValueError(f"committed sequence mismatch: {mode}/{case['id']}")
                dense_counts, counters = dense["counters"], candidate["counters"]
                if counters["down_projection_baseline_bytes"] != dense_counts["down_projection_actual_bytes"]:
                    raise ValueError("candidate eligible bytes disagree with matched dense execution")
                metrics = fidelity(candidate, document)
                record.update(status="completed", fidelity=metrics,
                              output_token_ids=candidate["output_token_ids"],
                              short_eos=len(candidate["output_token_ids"]) < 16,
                              counters=counters, dense_counters=dense_counts,
                              decode_elapsed_ns=candidate["timings"]["decode"]["elapsed_ns"])
                record["comparator_sequence_equal"] = {
                    kind: cases[mode, case["id"]]["output_token_ids"] == dense["output_token_ids"]
                    for kind, cases in comparators.items()
                }
                if "weight_reuse_explanation" in candidate:
                    record["weight_reuse_explanation"] = candidate["weight_reuse_explanation"]
                results.append(record)
            selected = [item for item in results if item["mode"] == mode]
            tokens = sum(item["counters"]["committed_tokens"] for item in selected)
            elapsed = sum(item["decode_elapsed_ns"] for item in selected)
            charged = sum(item["counters"]["charged_weight_traversals"] for item in selected)
            steps = sum(item["counters"]["completed_steps"] for item in selected)
            dense_down = sum(item["dense_counters"]["down_projection_actual_bytes"] for item in selected)
            actual_down = sum(item["counters"]["down_projection_actual_bytes"] for item in selected)
            physical = sum(item["counters"]["physical_read_bytes"] for item in selected)
            dense_physical = sum(item["dense_counters"]["physical_read_bytes"] for item in selected)
            if not all((tokens, elapsed, charged, steps, dense_down, dense_physical)):
                raise ValueError("empty full-model aggregate denominator")
            aggregate = {
                "committed_tokens": tokens, "elapsed_ns": elapsed, "charged_weight_traversals": charged,
                "completed_steps": steps, "accepted_tokens_per_step": tokens / steps,
                "effective_weight_reuse": tokens / charged,
                "down_projection_dense_bytes": dense_down, "down_projection_actual_bytes": actual_down,
                "physical_read_bytes": physical, "dense_physical_read_bytes": dense_physical,
                "physical_byte_reduction": 1 - physical / dense_physical,
                "ffn_read_reduction": 1 - actual_down / dense_down,
                "tpm": tokens * 60e9 / elapsed, "comparator_tpm": {}, "speedups": {},
                "replay_count": sum(item["counters"]["replay_count"] for item in selected),
                "replay_bytes": sum(item["counters"]["replay_bytes"] for item in selected),
            }
            if aggregate["effective_weight_reuse"] > 4:
                explanations = [item.get("weight_reuse_explanation", "") for item in selected]
                if not all(explanations):
                    raise ValueError("reuse >4 requires a retained measurement-boundary explanation")
                aggregate["weight_reuse_explanations"] = explanations
            predicates = {
                "complete_workload": len(selected) == len(CASES),
                "greedy_equivalence": True, "fidelity": True,
                "tpm_8000": aggregate["tpm"] >= 8000,
                "weight_reuse_3_2": aggregate["effective_weight_reuse"] >= 3.2,
                "ffn_read_reduction_40_percent": aggregate["ffn_read_reduction"] >= .4,
            }
            for kind, cases in comparators.items():
                values = [cases[mode, case["id"]] for case in CASES]
                comparator_tpm = sum(len(item["output_token_ids"]) for item in values) * 60e9 / sum(
                    item["decode_elapsed_ns"] for item in values)
                aggregate["comparator_tpm"][kind] = comparator_tpm
                aggregate["speedups"][kind] = aggregate["tpm"] / comparator_tpm
                predicates[f"faster_than_{kind}"] = aggregate["tpm"] > comparator_tpm
            acceptance["aggregates"][mode] = aggregate
            acceptance["predicates"][mode] = predicates
        if all(all(values.values()) for values in acceptance["predicates"].values()):
            acceptance["status"] = "passed"
        else:
            acceptance["failure_reasons"].append("one or more mandatory performance predicates failed")
    except bridge.PrerequisiteError as exc:
        acceptance["missing_prerequisites"].append(str(exc))
    except Exception as exc:
        acceptance["failure_reasons"].append(f"{type(exc).__name__}: {exc}")
    finally:
        write_json(directory / "acceptance.json", acceptance)
    if acceptance["status"] != "passed":
        raise AssertionError(f"full-model acceptance failed: {relative(directory / 'acceptance.json')}; "
                             f"{acceptance['missing_prerequisites'] or acceptance['failure_reasons']}")
    return [{"name": "full-model-benchmarks", "acceptance": relative(directory / "acceptance.json")}]
