"""Source/data-bound full-model evidence validation; never performs model inference.

The on-disk schema is documented in tests/BENCHMARK.md. Numerical summaries are
recomputed from full binary arrays, not accepted from self-reported metrics.
"""

import hashlib
import datetime
from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path
import re
import struct


MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
DIMENSIONS = dict(layers=24, hidden=896, intermediate=4864, query_heads=14,
                  kv_heads=2, head_dim=64, group_size=128, vocab=151936,
                  max_seq_len=32768)
DOMAINS = {
    "Math": "openai/gsm8k:test",
    "Code": "openai/openai_humaneval:test",
    "QA": "mandarjoshi/trivia_qa:rc.wikipedia/validation",
    "Sequence": "anvil-sequence-v1",
    "Logic": "maveriq/bigbenchhard:logical_deduction_three_objects",
}
MODES = ("bf16", "fp16", "w4a16")
SIMULATION_BACKENDS = ("iverilog", "verilator")
EXECUTION_BACKENDS = (*SIMULATION_BACKENDS, "arria10")
FORBIDDEN = {".vulcan", ".git", ".tooling", "VULCAN", "__pycache__"}


def load_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result

    def constant(value):
        raise ValueError("nonfinite JSON constant: " + value)

    def number(value):
        decoded = float(value)
        if not math.isfinite(decoded):
            raise ValueError("nonfinite JSON number: " + value)
        return decoded

    return json.loads(path.read_text(), object_pairs_hook=pairs, parse_constant=constant,
                      parse_float=number)


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def token_ids(value):
    return (isinstance(value, list) and
            all(integer(token) and token < DIMENSIONS["vocab"] for token in value))


def production_dimensions(value):
    return (isinstance(value, dict) and value == DIMENSIONS and
            all(integer(dimension, 1) for dimension in value.values()))


def artifact_path(root, name):
    root = root.resolve()
    path = Path(name)
    require(not path.is_absolute() and ".." not in path.parts and
            not FORBIDDEN.intersection(path.parts), "nonportable artifact path: " + name)
    full = root / path
    resolved = full.resolve()
    require(resolved.is_relative_to(root), "artifact escapes project: " + name)
    require(not FORBIDDEN.intersection(resolved.relative_to(root).parts),
            "runtime-owned artifact target: " + name)
    return full


def product_source_hashes(root):
    return {str(path.relative_to(root)): sha(artifact_path(root, str(path.relative_to(root))))
            for selector in ("rtl/*.sv", "fpga/*")
            for path in sorted(root.glob(selector)) if path.is_file()}


def ordered_indices(rows, key, count):
    return (isinstance(rows, list) and len(rows) == count and
            all(isinstance(row, dict) and integer(row.get(key)) and row[key] == index
                for index, row in enumerate(rows)))


def measured_cycles(summary, observed):
    fields = ("accepted_to_last", "first_logit", "arithmetic", "memory_stall", "control")
    for counts in (summary, observed):
        require(isinstance(counts, dict) and
                all(integer(counts.get(key)) for key in fields) and
                0 < counts["first_logit"] <= counts["accepted_to_last"] and
                counts["accepted_to_last"] == sum(
                    counts[key] for key in ("arithmetic", "memory_stall", "control")),
                "invalid measured cycle accounting")
    require(summary == observed, "cycles differ from raw integrated trace")


def greedy_stop(tokens, reason, eos):
    require(0 < len(tokens) <= 128 and
            all(integer(t) and t < 151936 for t in tokens) and
            reason in ("eos", "max_new_tokens") and
            (reason != "max_new_tokens" or len(tokens) == 128),
            "incomplete greedy generation")
    require(all(integer(token) and token < 151936 for token in eos) and eos,
            "invalid model EOS tokens")
    require(not any(token in eos for token in tokens[:-1]) and
            ((reason == "eos") == (tokens[-1] in eos)),
            "generation stopped before/after its declared EOS")


class Validator:
    def __init__(self, root, ev):
        self.root, self.ev = root.resolve(), ev
        self.artifacts = {}
        self.metrics = []
        self.decoders = {}

    def artifact(self, descriptor):
        require(isinstance(descriptor, dict), "artifact must be a path/sha256 descriptor")
        name, expected = descriptor["path"], descriptor["sha256"]
        full = artifact_path(self.root, name)
        require(full.is_file(), "missing artifact: " + name)
        require(re.fullmatch("[0-9a-f]{64}", expected) is not None,
                "invalid sha256: " + name)
        if name not in self.artifacts:
            self.artifacts[name] = sha(full)
        require(self.artifacts[name] == expected, "artifact hash mismatch: " + name)
        self.ev.receipt.setdefault("data_sha256", {})[name] = expected
        return full

    def document(self, descriptor):
        return load_json(self.artifact(descriptor))

    def decoded_text(self, decode, tokens, tokenizer):
        from pinned_tokenizer import PinnedDecoder

        require(decode["tokens"] == tokens and
                decode["tokenizer_sha256"] == tokenizer["sha256"],
                "generated text not bound to tokenizer")
        path = self.artifact(tokenizer)
        if path not in self.decoders:
            self.decoders[path] = PinnedDecoder(load_json(path))
        expected = self.decoders[path].decode(tokens, skip_special=True)
        require(isinstance(decode["text"], str) and decode["text"] == expected,
                "generated text differs from pinned token decoding")
        return expected

    def run(self, descriptor, bindings, purpose="full-model-execution"):
        run = self.document(descriptor)
        require(type(run["schema"]) is int and run["schema"] == 1 and run["purpose"] == purpose,
                "fixture/reduced/synthetic records cannot establish model execution")
        require(type(run["exit_code"]) is int and run["exit_code"] == 0 and
                run["timed_out"] is False,
                "execution failed or incomplete")
        require(run["bindings"] == bindings, "execution source/data bindings differ")
        require(isinstance(run["argv"], list) and run["argv"] and
                all(isinstance(arg, str) and "\0" not in arg for arg in run["argv"]) and
                run["argv"][0].strip(), "missing exact argv")
        require(run["cwd"] == ".", "execution cwd must be project relative")
        started = datetime.datetime.fromisoformat(run["started_at"])
        ended = datetime.datetime.fromisoformat(run["ended_at"])
        require(isinstance(run["tool_version"], str) and run["tool_version"].strip() and
                started.tzinfo and ended.tzinfo and started < ended,
                "execution version/timestamps missing")
        require(isinstance(run["timeout_s"], (int, float)) and
                run["timeout_s"] >= 3600, "execution allowance below 3600 seconds")
        for key in ("stdout", "stderr"):
            self.artifact(run[key])
        require(run["outputs"], "execution output bindings missing")
        for output in run["outputs"]:
            self.artifact(output)
        return run

    @staticmethod
    def produced(descriptor, run):
        require(descriptor in run["outputs"], "artifact not bound to producing execution")

    def model(self, model):
        require(type(model["schema"]) is int and model["schema"] == 1 and
                model["model"] == MODEL, "wrong checkpoint")
        require(production_dimensions(model["dimensions"]), "not the complete production model")
        require(re.fullmatch("[0-9a-f]{40}", model["revision"]) is not None,
                "checkpoint revision must be a fixed commit")
        require(model["rope_theta"] == 1000000 and model["rms_norm_eps"] == 1e-6,
                "wrong Qwen numerical configuration")
        checkpoint = model["checkpoint"]
        require(checkpoint, "checkpoint shards missing")
        for item in checkpoint:
            self.artifact(item)
        checkpoint_hashes = {item["path"]: item["sha256"] for item in checkpoint}
        for key in ("tokenizer", "chat_template", "config"):
            self.artifact(model[key])
        config = self.document(model["config"])
        for name, expected in dict(
                num_hidden_layers=24, hidden_size=896, intermediate_size=4864,
                num_attention_heads=14, num_key_value_heads=2, vocab_size=151936,
                max_position_embeddings=32768, rope_theta=1000000.0,
                rms_norm_eps=1e-6, tie_word_embeddings=True).items():
            value = config[name]
            valid_type = (type(value) is bool if type(expected) is bool else
                          integer(value, 1) if type(expected) is int else
                          type(value) in (int, float))
            require(valid_type and value == expected,
                    "checkpoint configuration mismatch: " + name)
        layout = self.document(model["tensor_layout"])
        require(layout["model_revision"] == model["revision"], "tensor layout revision mismatch")
        tensors = layout["tensors"]
        required = {"model.embed_tokens.weight": [151936, 896],
                    "model.norm.weight": [896]}
        for layer in range(24):
            prefix = f"model.layers.{layer}."
            required.update({
                prefix + "input_layernorm.weight": [896],
                prefix + "post_attention_layernorm.weight": [896],
                prefix + "self_attn.q_proj.weight": [896, 896],
                prefix + "self_attn.k_proj.weight": [128, 896],
                prefix + "self_attn.v_proj.weight": [128, 896],
                prefix + "self_attn.o_proj.weight": [896, 896],
                prefix + "self_attn.q_proj.bias": [896],
                prefix + "self_attn.k_proj.bias": [128],
                prefix + "self_attn.v_proj.bias": [128],
                prefix + "mlp.gate_proj.weight": [4864, 896],
                prefix + "mlp.up_proj.weight": [4864, 896],
                prefix + "mlp.down_proj.weight": [896, 4864],
            })
        for name, shape in required.items():
            dimensions = tensors[name]["shape"]
            require(isinstance(dimensions, list) and dimensions == shape and
                    all(integer(dimension, 1) for dimension in dimensions),
                    "tensor missing/wrong shape: " + name)
            require(tensors[name]["checkpoint_path"] in checkpoint_hashes,
                    "tensor not bound to checkpoint shard: " + name)
        require(layout["tied_output_embedding"] is True, "tied output weights missing")
        for mode in MODES:
            stream = model["streams"][mode]
            require(stream["checkpoint_sha256"] == checkpoint_hashes,
                    "stream derived from another checkpoint: " + mode)
            self.artifact(stream["weights"])
            self.artifact(stream["layout"])
            require(stream["recipe"] and stream["tool_version"], "unrecorded stream conversion")
            if mode == "w4a16":
                require(integer(stream["bits"]) and stream["bits"] == 4 and
                        integer(stream["group_size"]) and stream["group_size"] == 128 and
                        stream["nibble_order"] == [0, 4, 1, 5, 2, 6, 3, 7] and
                        all(integer(nibble) for nibble in stream["nibble_order"]),
                        "AWQ layout differs from parent")
                for key in ("scales", "zeros", "calibration"):
                    self.artifact(stream[key])
            else:
                require(stream["encoding"] == mode and
                        stream["rounding"] == "nearest-even", "native encoding mismatch")

    def suite(self, suite, model):
        require(type(suite["schema"]) is int and suite["schema"] == 1 and
                suite["suite"] == "anvil-five-domain-v1",
                "wrong versioned benchmark suite")
        decoding = suite["decoding"]
        require(isinstance(decoding, dict) and
                decoding.get("greedy") is True and
                decoding.get("sampling") is False and
                type(decoding.get("max_new_tokens")) is int and decoding == {
            "greedy": True, "tie_break": "lowest-token-id", "max_new_tokens": 128,
            "sampling": False}, "different decoding settings")
        require(suite["tokenizer_sha256"] == model["tokenizer"]["sha256"] and
                suite["chat_template_sha256"] == model["chat_template"]["sha256"],
                "tokenizer/template mismatch")
        cases = {}
        for domain, dataset in DOMAINS.items():
            group = suite["domains"][domain]
            require(group["dataset"] == dataset, "wrong dataset: " + domain)
            require(re.fullmatch("[0-9a-f]{40}", group["revision"]) is not None,
                    "unpinned dataset: " + domain)
            inventory = self.document(group["canonical_inventory"])
            ids = inventory["ids"]
            require(inventory["dataset"] == dataset and
                    inventory["revision"] == group["revision"],
                    "canonical inventory bound to another dataset revision")
            require(len(ids) >= 10 and all(isinstance(x, str) for x in ids) and
                    ids == sorted(set(ids)), "inventory must contain sorted unique dataset IDs")
            require(len(group["cases"]) == 10, "domain requires exactly ten cases: " + domain)
            require([case["id"] for case in group["cases"]] == ids[:10],
                    "selected cases are not first ten canonical IDs: " + domain)
            if domain == "Sequence":
                require(group["seed"] == 17 and group["generator_version"] == 1,
                        "Sequence generator must be published seed-17 version 1")
                self.artifact(group["generator"])
            if domain == "QA":
                require(group["verified_only"] is True, "TriviaQA must use verified validation")
            for case in group["cases"]:
                content = self.document(case["content"])
                require(content["id"] == case["id"] and content["prompt"] and
                        isinstance(content["prompt"], str) and
                        isinstance(content["answers"], list) and content["answers"] and
                        all(isinstance(answer, str) for answer in content["answers"]),
                        "missing prompt/answers")
                require(inventory["content_sha256"][case["id"]] == case["content"]["sha256"],
                        "selected content differs from canonical inventory")
                if domain == "QA":
                    require(content["verified"] is True, "unverified TriviaQA record")
                prompt = self.document(case["prompt_tokens"])
                require(prompt and all(integer(t) and t < 151936 for t in prompt),
                        "invalid prompt tokens")
                require(len(prompt) + 128 <= 32768, "prompt exceeds sequence capacity")
                contexts = self.document(case["teacher_tokens"])
                require(contexts[:len(prompt)] == prompt and len(contexts) >= len(prompt) and
                        all(integer(t) and t < 151936 for t in contexts),
                        "invalid/shared teacher-forcing context")
                require(len(contexts) <= 32768, "teacher context exceeds capacity")
                key = domain + "/" + case["id"]
                require(key not in cases, "duplicate case")
                cases[key] = (domain, case, content, contexts)
        require(set(suite["domains"]) == set(DOMAINS), "wrong five-domain set")
        return cases

    def array_bytes(self, descriptor, dtype, width):
        from packed_storage import array_bytes
        return array_bytes(self.artifact(descriptor), descriptor, dtype, width)

    def arrays(self, actual, reference, repeat, width, threshold, label, wide=False):
        encoding = "d" if wide else "f"
        a = self.array_bytes(actual, "<f8" if wide else "<f4", width)
        r = self.array_bytes(reference, "<f8", width)
        again = self.array_bytes(repeat, "<f8" if wide else "<f4", width)
        require(a == again, "nondeterministic output: " + label)
        values = struct.unpack("<" + encoding * width, a)
        expected = struct.unpack("<" + "d" * width, r)
        require(all(math.isfinite(v) for v in (*values, *expected)),
                "nonfinite numerical array: " + label)
        norm = max(1.0, max(map(abs, expected)))
        error = max(abs(x-y) for x, y in zip(values, expected)) / norm
        rnorm = math.hypot(*expected)
        anorm = math.hypot(*values)
        cosine = (math.fsum((x / anorm) * (y / rnorm)
                           for x, y in zip(values, expected))
                  if anorm and rnorm else None)
        require(error <= threshold[1] and
                (not rnorm or threshold[0] == -1 or
                 cosine is not None and cosine >= threshold[0]),
                f"numerical fidelity failed: {label}: cosine={cosine}, normalized_error={error}")
        max_ulp = max_xor = signed_zero = zeros = 0
        for value, ref in zip(values, expected):
            try:
                ref_bits = struct.unpack("<I", struct.pack("<f", ref))[0]
                bits = struct.unpack("<I", struct.pack("<f", value))[0]
            except OverflowError as error:
                raise ValueError("FP64 reference outside finite FP32 range: " + label) from error
            if value == 0 and ref == 0:
                zeros += 1
                signed_zero += bits != ref_bits
                continue
            def ordered(word):
                return (~word & 0xffffffff) if word & 0x80000000 else word | 0x80000000
            max_ulp = max(max_ulp, abs(ordered(bits)-ordered(ref_bits)))
            max_xor = max(max_xor, bits ^ ref_bits)
        self.metrics.append(dict(label=label, cosine=cosine, normalized_error=error,
                                 max_ulp=max_ulp, max_xor=max_xor,
                                 zero_pairs=zeros, nan_pairs=0, infinity_pairs=0,
                                 signed_zero_differences=signed_zero))
        return values, expected

    def results(self, results, cases, bindings, model):
        require(type(results["schema"]) is int and results["schema"] == 1 and
                results["purpose"] == "full-model-execution",
                "synthetic/fixture results are not benchmarks")
        require(production_dimensions(results["dimensions"]), "reduced-model results")
        require(results["bindings"] == bindings, "results bound to different sources/data")
        records = results["cases"]
        require(len(records) == 150, "requires 50 cases in each of three modes")
        execution = self.run(results["execution"], bindings)
        repeated = self.run(results["repeat_execution"], bindings)
        require(results["execution"] != results["repeat_execution"],
                "repeat execution must be an independent run record")
        reference = self.run(results["reference_execution"], bindings, "full-model-reference")
        require(reference["arithmetic"] == "ieee-fp64" and
                reference["independent_of_rtl"] is True and
                reference["weight_semantics"] == "decoded-selected-stream",
                "not independent FP64 selected-weight inference")
        require(reference["source_sha256"] and reference["dependencies"],
                "reference code/dependency provenance missing")
        for path, hashed in reference["source_sha256"].items():
            self.artifact(dict(path=path, sha256=hashed))
        backend = execution["backend"]
        require(backend in EXECUTION_BACKENDS, "not real integrated execution")
        require(repeated["backend"] == backend, "repeat backend mismatch")
        for run in (execution, repeated):
            require(run["top"] == "anvil_q1_fp_top" and production_dimensions(run["dimensions"]),
                    "execution is not the complete integrated production product")
        def retained_files(run):
            identities = set()
            for descriptor in (*run["outputs"], run["stdout"], run["stderr"]):
                stat = self.artifact(descriptor).stat()
                identities.add((stat.st_dev, stat.st_ino))
            return identities

        execution_files, repeated_files = retained_files(execution), retained_files(repeated)
        require(execution_files.isdisjoint(repeated_files),
                "repeat execution must retain separate, non-overwritten output and log files")
        require(retained_files(reference).isdisjoint(execution_files | repeated_files),
                "reference execution must retain separate, non-overwritten output and log files")
        if backend == "arria10":
            self.artifact(execution["bitstream"])
            require(repeated["bitstream"] == execution["bitstream"], "repeat bitstream mismatch")
            hil = self.document(execution["hil"])
            require(hil["part"] == "10AX115N2F45E1SG" and
                    hil["pcie"] == "Gen3x8" and len(hil["passes"]) >= 3,
                    "missing three physical Arria 10 passes")
            last_sequence = None
            pass_files = set()
            for item in hil["passes"]:
                record = self.run(item, bindings)
                require(record["backend"] == "arria10" and
                        record["top"] == "anvil_q1_fp_top" and
                        production_dimensions(record["dimensions"]),
                        "physical HIL pass is not the complete integrated production product")
                files = retained_files(record)
                require(files.isdisjoint(pass_files),
                        "physical HIL passes must retain separate, non-overwritten "
                        "output and log files")
                pass_files.update(files)
                require(record["bitstream"] == execution["bitstream"] and
                        record["deterministic"] is True, "HIL bitstream/determinism mismatch")
                require(integer(record["sequence"]) and
                        (last_sequence is None or record["sequence"] == last_sequence + 1),
                        "physical HIL passes are not consecutive")
                last_sequence = record["sequence"]
                require(all(record["coverage"][name] is True for name in
                            ("token_logit", "memory_bridge", "precision_selection",
                             "backpressure", "reset_recovery")),
                        "incomplete physical HIL protocol coverage")
        seen = set()
        scores = {}
        for record in records:
            key, mode = record["case"], record["mode"]
            require(key in cases and mode in MODES and (key, mode) not in seen,
                    "unknown or duplicate result case/mode")
            seen.add((key, mode))
            domain, case, content, contexts = cases[key]
            require(record["teacher_tokens_sha256"] == case["teacher_tokens"]["sha256"] and
                    record["prompt_tokens_sha256"] == case["prompt_tokens"]["sha256"],
                    "contexts differ across modes")
            require(record["stream_sha256"] == model["streams"][mode]["weights"]["sha256"],
                    "case uses wrong weight stream")
            trace = self.document(record["trace"])
            self.produced(record["trace"], execution)
            require(trace["case"] == key and trace["mode"] == mode and
                    token_ids(trace["accepted_tokens"]) and
                    trace["accepted_tokens"] == contexts and trace["faults"] == [] and
                    integer(trace["logit_count_per_token"]) and
                    trace["logit_count_per_token"] == 151936,
                    "incomplete integrated token/logit trace")
            positions = record["positions"]
            require(ordered_indices(positions, "position", len(contexts)),
                    "missing teacher-forced positions")
            require(isinstance(trace["cycles"], list) and
                    len(trace["cycles"]) == len(positions),
                    "incomplete raw integrated cycle trace")
            for position in positions:
                label = f"{key}/{mode}/{position['position']}"
                for name, run in (("logits", execution), ("repeat_logits", repeated),
                                  ("fp64_logits", reference),
                                  ("decoded_weight_logits", reference),
                                  ("checkpoint_fp64_logits", reference)):
                    self.produced(position[name], run)
                require(self.array_bytes(position["fp64_logits"], "<f8", 151936) ==
                        self.array_bytes(position["decoded_weight_logits"], "<f8", 151936),
                        "selected-weight FP64 references differ: " + label)
                self.arrays(position["logits"], position["fp64_logits"],
                            position["repeat_logits"], 151936,
                            (.999, .01) if mode != "w4a16" else (-1, float("inf")), label)
                require(ordered_indices(position["layers"], "layer", 24),
                        "missing per-layer comparisons")
                for layer in position["layers"]:
                    for name, run in (("output", execution), ("repeat_output", repeated),
                                      ("fp64_output", reference)):
                        self.produced(layer[name], run)
                    self.arrays(layer["output"], layer["fp64_output"],
                                layer["repeat_output"], 896,
                                (.9999, .002) if mode != "w4a16" else (-1, float("inf")),
                                label + "/layer" + str(layer["layer"]))
                # This separate comparison reports storage quantization, not RTL error.
                self.arrays(position["decoded_weight_logits"],
                            position["checkpoint_fp64_logits"],
                            position["decoded_weight_logits"], 151936,
                            (-1, float("inf")), label + "/storage-quantization", wide=True)
                cycles = position["cycles"]
                measured_cycles(cycles, trace["cycles"][position["position"]])
            greedy = record["greedy"]
            require(token_ids(greedy["repeat_tokens"]) and
                    greedy["tokens"] == greedy["repeat_tokens"],
                    "nondeterministic greedy generation")
            config = self.document(model["config"])
            eos = config["eos_token_id"]
            eos = eos if isinstance(eos, list) else [eos]
            greedy_stop(greedy["tokens"], greedy["stop_reason"], eos)
            require(integer(greedy["cycles"], 1) and
                    integer(trace["generation_cycles"], 1) and
                    greedy["cycles"] == trace["generation_cycles"], "generation latency missing")
            require(token_ids(trace["generated_tokens"]) and
                    trace["generated_tokens"] == greedy["tokens"], "greedy trace mismatch")
            require(len(greedy["steps"]) == len(greedy["tokens"]),
                    "missing greedy-position logits")
            for index, step in enumerate(greedy["steps"]):
                self.produced(step["logits"], execution)
                self.produced(step["repeat_logits"], repeated)
                actual = self.array_bytes(step["logits"], "<f4", 151936)
                repeated_logits = self.array_bytes(step["repeat_logits"], "<f4", 151936)
                require(actual == repeated_logits,
                        "missing/nondeterministic greedy logits")
                logits = struct.unpack("<151936f", actual)
                require(all(math.isfinite(v) for v in logits), "nonfinite greedy logits")
                token = max(range(151936), key=logits.__getitem__)
                require(greedy["tokens"][index] == token,
                        "not greedy lowest-ID-tie generation")
                require(token_ids(step["context"]) and
                        step["context"] == self.document(case["prompt_tokens"]) +
                        greedy["tokens"][:index], "greedy continuation context mismatch")
            decode = self.document(greedy["decode"])
            text = self.decoded_text(decode, greedy["tokens"], model["tokenizer"])
            self.produced(greedy["decode"], execution)
            if domain == "Code":
                evaluation = self.document(greedy["evaluation"])
                require(evaluation["isolated"] is True and evaluation["environment"] and
                        evaluation["policy"] and evaluation["case"] == key and
                        evaluation["decode_sha256"] == greedy["decode"]["sha256"] and
                        type(evaluation["passed"]) is bool,
                        "missing isolated Code evaluation")
                evaluated = self.run(evaluation["execution"], bindings, "isolated-code-evaluation")
                self.produced(evaluation["result"], evaluated)
                outcome = self.document(evaluation["result"])
                require(outcome["case"] == key and
                        outcome["decode_sha256"] == greedy["decode"]["sha256"] and
                        outcome["passed"] is evaluation["passed"],
                        "isolated Code score differs from raw evaluator output")
                score = float(evaluation["passed"])
            else:
                text = text.strip()
                answers = content["answers"]
                require(isinstance(answers, list) and all(isinstance(x, str) for x in answers),
                        "invalid task answers")
                if domain == "Math":
                    numbers = re.findall(r"-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?",
                                         text.replace(",", ""))
                    require(all(re.fullmatch(r"-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?",
                                             answer) for answer in answers),
                            "Math gold answers must be extracted numeric values")
                    score = float(bool(numbers) and Decimal(numbers[-1]) in
                                  [Decimal(answer) for answer in answers])
                elif domain == "QA":
                    def normalize(value):
                        value = re.sub(r"[^\w\s]", "", value.lower())
                        return " ".join(re.sub(r"\b(a|an|the)\b", " ", value).split())
                    score = float(normalize(text) in [normalize(a) for a in answers])
                else:
                    score = float(text in answers)
            scores.setdefault(domain + "/" + mode, []).append(score)
        require(seen == {(case, mode) for case in cases for mode in MODES},
                "full-model case/mode completeness failure")
        return {key: math.fsum(values)/len(values) for key, values in scores.items()}

    def inputs(self):
        descriptors = {}
        documents = {}
        for name in ("model_manifest", "benchmark_manifest"):
            path = artifact_path(self.root, "tests/data/" + name + ".json")
            require(path.is_file(), "missing artifact: " + str(path.relative_to(self.root)))
            descriptors[name] = sha(path)
            documents[name] = self.document(dict(path=str(path.relative_to(self.root)),
                                                 sha256=descriptors[name]))
        model, suite = documents["model_manifest"], documents["benchmark_manifest"]
        self.model(model)
        cases = self.suite(suite, model)
        return descriptors, model, cases

    def validate(self):
        descriptors, model, cases = self.inputs()
        path = artifact_path(self.root, "tests/data/full_model_results.json")
        require(path.is_file(), "missing artifact: tests/data/full_model_results.json")
        results = self.document(dict(path="tests/data/full_model_results.json",
                                     sha256=sha(path)))
        source_hashes = product_source_hashes(self.root)
        require(source_hashes, "product sources missing")
        bindings = dict(model_manifest=descriptors["model_manifest"],
                        benchmark_manifest=descriptors["benchmark_manifest"],
                        source_sha256=source_hashes)
        scores = self.results(results, cases, bindings, model)
        return dict(cases=150, task_scores=scores, numerical=self.metrics,
                    backend_note="Simulation and physical evidence are not interchangeable")

    def collection_requirements(self, descriptors, cases):
        """Describe validated input demand, never observed execution or a transport."""
        rows = []
        for key, (domain, case, _, contexts) in sorted(cases.items()):
            rows.append(dict(case=key, domain=domain,
                             prompt_tokens=case["prompt_tokens"],
                             teacher_tokens=case["teacher_tokens"],
                             teacher_positions=len(contexts)))
        positions = sum(row["teacher_positions"] for row in rows) * len(MODES)
        return dict(
            schema=1, purpose="offline-collection-requirements",
            acceptance_evidence=False, endpoint_contacted=False,
            execution_established=False,
            resume_prerequisites=dict(
                status="qualification-not-established",
                scope="physical-benchmark-collection",
                permitted_benchmark_backends=list(EXECUTION_BACKENDS),
                simulation_alternative=dict(
                    backends=list(SIMULATION_BACKENDS),
                    status="execution-not-established",
                    requires_complete_production_model=True,
                    requires_all_cases_modes_and_repeats=True,
                    requires_independent_fp64_and_measured_cycles=True,
                    substitutes_for_native_gates=False),
                mandatory_native_gates=["rtl-timing-lint", "quartus-sta", "board-hil"],
                required_platform_inputs=[
                    "Authorized non-programming production adapter/API documentation",
                    "Versioned qualification request and response schema",
                    "Exact authorized non-programming qualification invocation"],
                qualification_must_establish=[
                    "Current source, constraints, data and accepted bitstream identity",
                    "Memory kinds 0-12 and projections 0-6 with mode-specific encodings",
                    "Accepted-token precision, sequence reset, ready/valid and fault semantics",
                    "Complete ordered logits, layer observations and independent repeats",
                    "Measured token, arithmetic, memory-stall, control and generation cycles"],
                endpoint_availability="not-determined",
                policy_denial_is_rtl_failure=False,
                next_step=(
                    "Collect genuine complete-model execution using an admitted backend; "
                    "physical collection first requires the documented interface"),
                note="Offline requirements only; no transport or remote command is authorized."),
            bindings=dict(
                model_manifest=descriptors["model_manifest"],
                benchmark_manifest=descriptors["benchmark_manifest"],
                source_sha256=product_source_hashes(self.root)),
            dimensions=DIMENSIONS.copy(), modes=list(MODES), cases=rows,
            required=dict(
                case_mode_records=len(rows) * len(MODES),
                teacher_position_mode_records=positions,
                logits_per_position=DIMENSIONS["vocab"],
                layer_outputs_per_position=DIMENSIONS["layers"],
                values_per_layer=DIMENSIONS["hidden"],
                independent_dut_runs=2,
                greedy_max_new_tokens=128),
            limitations=[
                "Counts are required observations, not completed comparisons.",
                "No adapter invocation or wire protocol is defined by this inventory.",
                "Qualification, greedy execution, measured cycles, FP64 comparisons, "
                "native timing/resources and three physical passes remain mandatory."])


def validate_input_manifests(root, ev):
    """Validate collection inputs without importing numerical inference tools."""
    validator = Validator(root, ev)
    model = load_json(root / "tests/data/model_manifest.json")
    suite = load_json(root / "tests/data/benchmark_manifest.json")
    validator.model(model)
    cases = validator.suite(suite, model)
    config = load_json(validator.artifact(model["config"]))
    return model, suite, cases, config


def check(root, ev):
    try:
        paths = {name: artifact_path(root, f"tests/data/{name}.json") for name in
                 ("model_manifest", "benchmark_manifest", "full_model_results")}
    except (ValueError, OSError) as error:
        return ev.assertion("full_model_inputs_and_execution", False,
                            reason=f"{type(error).__name__}: {error}")
    missing = [str(path.relative_to(root)) for path in paths.values()
               if not path.is_file()]
    if missing:
        diagnostics = []
        resume_prerequisites = None
        if all(paths[name].is_file() for name in ("model_manifest", "benchmark_manifest")):
            validator = Validator(root, ev)
            try:
                descriptors, _, cases = validator.inputs()
                requirements = validator.collection_requirements(descriptors, cases)
            except (ValueError, KeyError, TypeError, OSError, OverflowError, struct.error,
                    InvalidOperation) as error:
                diagnostics.append(f"{type(error).__name__}: {error}")
                ev.assertion("full_model_available_inputs", False, reason=diagnostics[-1])
            else:
                path = ev.path / "collection-requirements.json"
                with path.open("x") as stream:
                    json.dump(requirements, stream, indent=2, allow_nan=False)
                    stream.write("\n")
                ev.assertion("full_model_available_inputs", True, cases=len(cases),
                             scope="Input integrity only; no model execution established",
                             collection_requirements=dict(
                                 path=str(path.relative_to(root)), sha256=sha(path)))
                resume_prerequisites = requirements["resume_prerequisites"]
        return ev.assertion("full_model_inputs_and_execution", False, missing=missing,
                            input_diagnostics=diagnostics,
                            resume_prerequisites=resume_prerequisites,
                            reason="missing artifact(s): " + ", ".join(missing))
    validator = Validator(root, ev)
    try:
        report = validator.validate()
    except (ValueError, KeyError, TypeError, OSError, OverflowError, struct.error,
            InvalidOperation) as error:
        return ev.assertion("full_model_inputs_and_execution", False,
                            reason=f"{type(error).__name__}: {error}")
    path = ev.path / "full-model-validation.json"
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return ev.assertion("full_model_inputs_and_execution", True,
                        report=str(path.relative_to(root)), cases=150)


if __name__ == "__main__":
    import sys

    print(
        "tests/benchmark.py is a validation library, not an inference entrypoint. "
        "Use python3 tests/verify.py --check benchmark-contract to validate "
        "existing full-model evidence; that command does not perform inference.",
        file=sys.stderr,
    )
    sys.exit(2)
