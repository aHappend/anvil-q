"""Validate provenance and prerequisites, sharing physical input checks with STA/HIL."""

import json
import shutil

from execution import ROOT, sha256, write_json
from hardware_checks import board_inputs, PhysicalPrerequisiteError
from public_assets import validate_assets

CONFIG_HASH = "9366ca39ab036f807f40ff93f03d77ce910d512174150821a87a87080c2b8c65"
CONFIG_URL = "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-AWQ/raw/main/config.json"


def configuration():
    path = ROOT / "design/qwen2_5_3b_awq_config.json"
    if sha256(path) != CONFIG_HASH:
        raise AssertionError("official configuration byte hash mismatch")
    config = json.loads(path.read_text())
    required = {
        "architectures": ["Qwen2ForCausalLM"], "num_hidden_layers": 36,
        "hidden_size": 2048, "intermediate_size": 11008, "num_attention_heads": 16,
        "num_key_value_heads": 2, "vocab_size": 151936, "max_position_embeddings": 32768,
        "rope_theta": 1000000.0, "rms_norm_eps": 1e-6, "tie_word_embeddings": True,
        "use_sliding_window": False, "torch_dtype": "float16"}
    for key, value in required.items():
        if type(config.get(key)) is not type(value) or config.get(key) != value:
            raise AssertionError(f"configuration {key}: expected {value!r}, observed {config.get(key)!r}")
    quant = config["quantization_config"]
    for key, value in {"bits": 4, "group_size": 128, "zero_point": True,
                       "quant_method": "awq", "version": "gemm"}.items():
        if type(quant.get(key)) is not type(value) or quant.get(key) != value:
            raise AssertionError("quantization configuration " + key)
    assert config["hidden_size"] // config["num_attention_heads"] == 128
    assert config["num_attention_heads"] // config["num_key_value_heads"] == 8
    provenance = json.loads((ROOT / "design/model_provenance.json").read_text())
    if (provenance["configuration"]["url"] != CONFIG_URL or
            provenance["configuration"]["expected_sha256"] != CONFIG_HASH):
        raise AssertionError("public provenance URL/hash mismatch")
    return {"configuration_sha256": CONFIG_HASH, "configuration_url": CONFIG_URL,
            "validated_fields": required, "quantization": quant, "head_dim": 128, "gqa": 8}


def prerequisites(run):
    result = {"configuration": configuration(), "prerequisites": []}

    def required(label, ok, detail):
        result["prerequisites"].append({"requirement": label, "met": bool(ok), "detail": detail})

    for tool in ("python3", "iverilog", "vvp", "verilator", "yosys",
                 "quartus_sh", "quartus_sta", "quartus_pgm"):
        required("executable:" + tool, shutil.which(tool) is not None,
                 "PATH resolution only; version/license/functional availability require actual tool execution")
    provenance = json.loads((ROOT / "design/model_provenance.json").read_text())
    supplied = json.loads((ROOT / "tests/public_assets.json").read_text())
    if supplied.get("schema") != 1:
        raise ValueError("unsupported independent public asset schema")
    assets = list(supplied["assets"])
    for key in ("weight_assets", "tokenizer_assets", "generation_baselines"):
        assets.extend(provenance.get(key, []))
    validated = validate_assets(run, assets)
    result["validated_public_assets"] = validated
    for key, category in (("weight_assets", "weight_slice"), ("tokenizer_assets", "tokenizer")):
        required(key, any(a["category"] == category for a in validated),
                 "Actual revision/license/content validation required; synthetic data is not official")
    for generation in ("Q1", "Q2"):
        required("generation_baseline:" + generation,
                 any(a["category"] == "baseline" and a["generation"] == generation for a in validated),
                 "Real native baseline with public identity; Q1-compatible wrapper is not independent Q1")
    adapters = baseline_adapters(run, validated)
    result["baseline_adapters"] = adapters
    for row in adapters["generations"]:
        required("generation_adapter:" + row["generation"],
                 row["source_bound_execution_adapter"],
                 "Source identity must match an executable native adapter; "
                 "provenance alone does not establish numerical execution")
    try:
        board_inputs(run)
    except PhysicalPrerequisiteError as exc:
        required("identified-physical-board", False, str(exc))
        for item in exc.unmet:
            required("physical-input:" + item, False,
                     "Shared prerequisite/STA/HIL input validation; see physical-prerequisites.json")
    else:
        required("identified-physical-board", True,
                 "Public board inputs validated; physical access, licenses, fit and HIL remain unproven")
    write_json(run.path / "prerequisites.json", result)
    missing = [p["requirement"] for p in result["prerequisites"] if not p["met"]]
    if missing:
        raise RuntimeError("unmet prerequisites: " + ", ".join(missing))
    return result


def baseline_adapters(run, validated):
    """Report adapter readiness separately from acquired public provenance."""
    from benchmark_checks import baseline_prerequisites

    result = baseline_prerequisites(validated, run.hashes)
    write_json(run.path / "baseline-adapters.json", result)
    return result
