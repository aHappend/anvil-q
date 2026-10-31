#!/usr/bin/env python3
"""Portable request/result adapter; device configuration is external.

Full-model execution requires ANVIL_HT2_BRIDGE_ARGV_JSON and
ANVIL_HT2_BENCHMARK_INPUTS. Nothing here substitutes a simulation for hardware.
"""

import argparse
import json
import math
import os
from pathlib import Path
import re
import sys
import uuid
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

from benchmark_manifest import (BOUNDARIES, CASES, DEFAULT_GEOMETRY, MANIFEST,
                                MANIFEST_SHA256, canonical, sha256)
from evidence import ROOT, digest, execute, relative, require_success, write_json


class PrerequisiteError(RuntimeError):
    pass


def project_path(value):
    if not isinstance(value, str) or not value:
        raise ValueError("artifact path must be a nonempty project-relative string")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or set(path.parts) & {
        ".vulcan", ".git", ".tooling", "VULCAN"
    }:
        raise ValueError("artifact path is not a deliverable/project evidence path")
    result = ROOT / path
    result.resolve().relative_to(ROOT)
    return result


def artifact(record):
    if not isinstance(record, dict) or not {"path", "sha256"} <= set(record):
        raise ValueError("artifact needs path and sha256")
    path = project_path(record["path"])
    if not re.fullmatch(r"[a-f0-9]{64}", record["sha256"]) or digest(path) != record["sha256"]:
        raise ValueError(f"artifact identity mismatch: {record['path']}")
    return path


def load_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError(f"nonfinite JSON value: {value}")))


def uint(value, name, maximum=None):
    if type(value) is not int or value < 0 or (maximum is not None and value > maximum):
        raise ValueError(f"invalid unsigned counter or ID: {name}")
    return value


def positive(value, name):
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"nonpositive/nonfinite measurement: {name}")
    return value


def execution_provenance(record):
    """Validate hash-bound execution inputs and retained raw output, not a PASS label."""
    path = artifact(record)
    raw = load_json(path)
    for key in ("argv", "cwd", "source_sha256", "start_time", "end_time", "stdout", "stderr"):
        if key not in raw:
            raise ValueError("measurement receipt incomplete")
    if raw.get("exit_code") != 0 or raw.get("timed_out") is not False:
        raise ValueError("measurement receipt failed or timed out")
    if (not isinstance(raw["argv"], list) or not raw["argv"] or
        not all(isinstance(word, str) and word for word in raw["argv"]) or
        not isinstance(raw["source_sha256"], dict) or not raw["source_sha256"]):
        raise ValueError("execution command/source provenance missing")
    project_path(raw["cwd"] or ".")
    start, end = (datetime.fromisoformat(raw[key]) for key in ("start_time", "end_time"))
    if start.tzinfo is None or end.tzinfo is None or end < start:
        raise ValueError("execution receipt timestamp contradiction")
    for source, expected in raw["source_sha256"].items():
        artifact({"path": source, "sha256": expected})
    for channel in ("stdout", "stderr"):
        stream = project_path(str((path.parent / raw[channel]).relative_to(ROOT)))
        if not stream.is_file():
            raise ValueError("measurement raw output missing")
    return raw


def token_ids(values, vocabulary=151936):
    if not isinstance(values, list) or not values:
        raise ValueError("missing token sequence")
    for value in values:
        uint(value, "token ID", vocabulary - 1)
    return values


def bridge_prefix():
    raw = os.environ.get("ANVIL_HT2_BRIDGE_ARGV_JSON")
    if not raw:
        raise PrerequisiteError("BENCHMARK_PREREQUISITE: ANVIL_HT2_BRIDGE_ARGV_JSON is unset")
    prefix = json.loads(raw)
    if not isinstance(prefix, list) or not prefix or not all(
        isinstance(word, str) and word and "\x00" not in word for word in prefix
    ):
        raise PrerequisiteError("BENCHMARK_PREREQUISITE: bridge prefix must be a JSON string array")
    if any(re.search(r"(password|passwd|secret|access[_-]?token|api[_-]?key|bearer)",
                     word, re.I) for word in prefix):
        raise PrerequisiteError("BENCHMARK_PREREQUISITE: credentials are forbidden in bridge argv")
    return prefix


def inputs():
    name = os.environ.get("ANVIL_HT2_BENCHMARK_INPUTS")
    if not name:
        raise PrerequisiteError("BENCHMARK_PREREQUISITE: ANVIL_HT2_BENCHMARK_INPUTS is unset")
    path = project_path(name)
    try:
        document = load_json(path)
        if document["schema_version"] != 1 or document["workload_manifest_sha256"] != MANIFEST_SHA256:
            raise ValueError("benchmark input schema/workload mismatch")
        model = document["model"]
        if model["id"] != MANIFEST["model"] or not re.fullmatch(r"[0-9a-f]{40}", model["revision"]):
            raise ValueError("official immutable checkpoint identity missing")
        if not model["license"] or not model["license_artifact"]:
            raise ValueError("checkpoint license provenance missing")
        artifact(model["license_artifact"])
        config = load_json(artifact(model["config"]))
        expected = {"num_hidden_layers": 24, "hidden_size": 896, "intermediate_size": 4864,
                    "num_attention_heads": 14, "num_key_value_heads": 2, "vocab_size": 151936,
                    "rms_norm_eps": 1e-6, "rope_theta": 1e6,
                    "max_position_embeddings": 32768, "tie_word_embeddings": True}
        if any(config.get(key) != value for key, value in expected.items()):
            raise ValueError("official Qwen configuration disagrees with frozen decoder contract")
        if model["tokenizer"]["revision"] != model["revision"]:
            raise ValueError("tokenizer immutable revision mismatch")
        for record in model["tokenizer"]["files"]:
            artifact(record)
        if not model["tokenizer"]["files"]:
            raise ValueError("tokenizer files missing")
        tensor_names = set()
        for tensor in model["tensors"]:
            if tensor["name"] in tensor_names:
                raise ValueError("duplicate model tensor")
            tensor_names.add(tensor["name"])
            artifact(tensor["artifact"])
            if tensor["dtype"] != "BF16" or not tensor["shape"]:
                raise ValueError("official tensor dtype/shape missing")
            for dimension in tensor["shape"]:
                positive(uint(dimension, "tensor dimension"), "tensor dimension")
        required_names = {"model.embed_tokens.weight", "model.norm.weight"}
        for layer in range(24):
            prefix = f"model.layers.{layer}."
            required_names.update(prefix + name for name in (
                "input_layernorm.weight", "post_attention_layernorm.weight",
                "self_attn.q_proj.weight", "self_attn.k_proj.weight", "self_attn.v_proj.weight",
                "self_attn.o_proj.weight", "self_attn.q_proj.bias", "self_attn.k_proj.bias",
                "self_attn.v_proj.bias", "mlp.gate_proj.weight", "mlp.up_proj.weight",
                "mlp.down_proj.weight"))
        if not required_names <= tensor_names:
            raise ValueError("official checkpoint tensor inventory incomplete")
        for mode in MANIFEST["modes"]:
            image = load_json(artifact(document["images"][mode]))
            if (image["model_revision"] != model["revision"] or
                image["geometry"] != DEFAULT_GEOMETRY or image["mode"] != mode or
                image["config_sha256"] != model["config"]["sha256"]):
                raise ValueError("converted image identity/geometry mismatch")
            if not image["layout"] or not image["descriptors"] or not image["tensors"]:
                raise ValueError("converted image layout and tensors required")
            for record in image["tensors"]:
                artifact(record["artifact"])
        quantization = load_json(artifact(document["awq_provenance"]))
        if (quantization["model_revision"] != model["revision"] or
            quantization["bits"] != 4 or quantization["group_size"] != 128 or
            not quantization["software_versions"] or not quantization["calibration_manifest"]):
            raise ValueError("independently frozen AWQ quantization provenance missing")
        artifact(quantization["calibration_manifest"])
        execution_provenance(quantization["execution_receipt"])
        if set(document["tokenized_cases"]) != {case["id"] for case in CASES}:
            raise ValueError("tokenized workload coverage mismatch")
        for case in CASES:
            record = document["tokenized_cases"][case["id"]]
            ids = token_ids(record["ids"])
            if (len(ids) + 16 > 32768 or record["sha256"] != sha256(ids) or
                record["prompt_sha256"] != sha256(case["prompt"])):
                raise ValueError("tokenized prompt identity/bounds mismatch")
        if set(document["comparators"]) != {"ht", "fp", "a100"}:
            raise ValueError("HT, FP and matched A100 comparator records all required")
        for record in document["comparators"].values():
            artifact(record)
        token_ids(document["eos_token_ids"])
        import checkpoint_images
        checkpoint_images.validate_images(document)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise PrerequisiteError(f"BENCHMARK_PREREQUISITE: {exc}") from exc
    return document, path


def request(document, case, mode, job_type, *, integration_only=False, geometry=None):
    model = document["model"]
    tokenized = document["tokenized_cases"][case["id"]]
    return {
        "schema_version": 1, "run_nonce": uuid.uuid4().hex,
        "workload_manifest_sha256": MANIFEST_SHA256, "model_revision": model["revision"],
        "model_sha256": sha256(model["tensors"]), "config_sha256": model["config"]["sha256"],
        "tokenizer_sha256": sha256(model["tokenizer"]),
        "image_sha256": document["images"][mode]["sha256"], "mode": mode,
        "geometry": geometry or DEFAULT_GEOMETRY, "candidate_top": "anvil_q1_ht2_top",
        "job_type": job_type, "case_id": case["id"], "domain": case["domain"],
        "prompt_sha256": sha256(case["prompt"]), "tokenized_input_sha256": tokenized["sha256"],
        "input_ids": tokenized["ids"], "decode_limit": MANIFEST["decode_limit"],
        "eos_token_ids": document["eos_token_ids"], "sparse_threshold": MANIFEST["sparse_threshold_bf16"],
        "draft_strategy": MANIFEST["draft_strategy"], "measurement_boundaries": BOUNDARIES,
        "reference_observation_boundaries": MANIFEST["observation_boundaries"],
        "integration_only": integration_only,
    }


IDENTITY_FIELDS = (
    "schema_version", "run_nonce", "workload_manifest_sha256", "model_revision", "model_sha256",
    "config_sha256", "tokenizer_sha256", "image_sha256", "mode", "geometry", "candidate_top",
    "job_type", "case_id", "domain", "prompt_sha256", "tokenized_input_sha256",
    "measurement_boundaries", "draft_strategy",
)


def validate_response(response, req, *, full=True):
    if any(response.get(key) != req[key] for key in IDENTITY_FIELDS):
        raise ValueError("bridge response identity mismatch")
    if response.get("request_sha256") != sha256(req):
        raise ValueError("bridge response request hash mismatch")
    if full and (response.get("integration_only") is not False or
                 response.get("execution_kind") != "physical_fpga" or
                 response["geometry"] != DEFAULT_GEOMETRY or req["integration_only"]):
        raise ValueError("full-model acceptance rejects simulated/reduced/integration-only results")
    if not full and (response.get("integration_only") is not True or
                     response.get("execution_kind") != "compiled_rtl"):
        raise ValueError("compact adapter response mislabeled")
    if response.get("status") != "completed":
        raise ValueError("bridge job did not complete successfully")
    provenance = response["provenance"]
    if not provenance or not response["software_versions"]:
        raise ValueError("native measurement/source provenance missing")
    for record in provenance:
        execution_provenance(record)
    image_job = req["job_type"] == "image_validation_load"
    for stage in (("load_cold", "load_warm") if image_job else
                  ("load_cold", "load_warm", "prefill", "decode")):
        timing = response["timings"][stage]
        start = uint(timing["start_monotonic_ns"], "start")
        end = uint(timing["end_monotonic_ns"], "end")
        elapsed = positive(timing["elapsed_ns"], "elapsed")
        if end - start != elapsed:
            raise ValueError("contradictory monotonic timing boundaries")
    if image_job:
        validation = response["image_validation"]
        if (validation.get("finite_tensors") is not True or
            validation.get("descriptors_verified") is not True or
            validation.get("loaded_image_sha256") != req["image_sha256"]):
            raise ValueError("image validation/load failed")
        if full and not response.get("device_identity"):
            raise ValueError("physical device identity missing")
        return response
    clock = positive(response["measured_clock_hz"], "clock")
    counters = response["counters"]
    for key in ("cycles", "committed_tokens", "completed_steps", "physical_read_bytes",
                "down_projection_baseline_bytes", "down_projection_actual_bytes",
                "metadata_bytes", "replay_bytes", "replay_count", "replay_cycles",
                "corrections", "rejections", "avoided_down_projection_bytes",
                "charged_weight_traversals"):
        uint(counters[key], key)
    decode_ns = response["timings"]["decode"]["elapsed_ns"]
    if counters["cycles"] <= 0 or counters["cycles"] / clock > decode_ns / 1e9 * 1.02:
        raise ValueError("cycle count exceeds measured end-to-end wall boundary")
    if counters["replay_cycles"] > counters["cycles"]:
        raise ValueError("replay cycle count exceeds total")
    physical = counters["physical_read_bytes"]
    if physical % 64 or counters["down_projection_actual_bytes"] % 64:
        raise ValueError("physical-byte counts are not accepted 512-bit response beats")
    if (counters["down_projection_actual_bytes"] > physical or
        counters["metadata_bytes"] > physical or counters["replay_bytes"] > physical or
        counters["avoided_down_projection_bytes"] > counters["down_projection_baseline_bytes"]):
        raise ValueError("contradictory DDR/sparse accounting")
    output = token_ids(response["output_token_ids"],
                       response["geometry"]["VOCAB_SIZE"])
    if len(output) != counters["committed_tokens"] or not 1 <= counters["completed_steps"] <= len(output):
        raise ValueError("token/step counters do not match complete output sequence")
    if not 1 <= counters["charged_weight_traversals"] or len(output) > 4 * counters["completed_steps"]:
        raise ValueError("invalid charged traversals or commit batch size")
    if (not full and response["eos_reason"] == "integration_boundary" and
        req.get("integration_decode_min") == 4 and req["decode_limit"] == 7):
        if not 4 <= len(output) <= 7:
            raise ValueError("truncated compact commit-boundary output")
    elif response["eos_reason"] == "eos":
        if output[-1] not in req["eos_token_ids"] or len(output) > req["decode_limit"]:
            raise ValueError("invalid short-EOS termination")
    elif response["eos_reason"] != "limit" or len(output) != req["decode_limit"]:
        raise ValueError("truncated decode output")
    if any(token in req["eos_token_ids"] for token in output[:-1]):
        raise ValueError("decoder continued after EOS")
    if full and not response.get("device_identity"):
        raise ValueError("physical device identity missing")
    return response


def launch(prefix, req, directory, full=True):
    request_path, response_path = directory / "request.json", directory / "response.json"
    write_json(request_path, req)
    process = require_success(execute(
        [*prefix, "--request", relative(request_path), "--response", relative(response_path)],
        directory, "bridge", timeout=2400, inputs=[request_path]))
    if not response_path.is_file():
        raise ValueError("bridge process returned without a response")
    result = validate_response(load_json(response_path), req, full=full)
    return result, {"response": {"path": relative(response_path), "sha256": digest(response_path)},
                    "launch_receipt": relative(process / "receipt.json")}
