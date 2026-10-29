"""FP64 checkpoint equations versus accepted-parent fixed-point outputs.

This is a numerical-discrepancy measurement, not a published PyTorch/BF16-kernel
accuracy claim. Both networks receive the same input-token trajectory; their
attention histories and intermediate arithmetic remain independent. No tolerance
or expected hardware result is changed by a nonzero software discrepancy.
"""

import argparse
import ctypes
import json
import math
import mmap
from pathlib import Path
import random
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint_reference import CPP, sha
from fixtures import project_path, validate


FLOAT_CPP = CPP + r"""
namespace {
double floating(uint16_t x, bool bfloat) {
    unsigned fraction_bits = bfloat ? 7 : 10, limit = bfloat ? 255 : 31;
    unsigned e = (x >> fraction_bits) & limit;
    unsigned f = x & ((1u << fraction_bits) - 1);
    if (e == limit) throw std::runtime_error("nonfinite floating input");
    int bias = bfloat ? 127 : 15;
    double magnitude = std::ldexp(double(e ? (1u << fraction_bits) + f : f),
                                  int(e ? e : 1) - bias - int(fraction_bits));
    return x & 0x8000 ? -magnitude : magnitude;
}
}
extern "C" int floating_gemv(
    const uint8_t* data, uint64_t size, int format,
    unsigned inputs, unsigned outputs, unsigned group,
    uint64_t w, uint64_t z, uint64_t s, uint64_t bias, int bias_format,
    const double* activation, double* result, char* error, size_t capacity) {
    try {
        if (!inputs || !outputs || inputs > 4864 || outputs > 151936 ||
            format < 0 || format > 2 || !group || inputs % group ||
            (format == 0 && outputs % 8) || bias_format < -1 || bias_format > 1)
            throw std::runtime_error("invalid floating GEMV geometry");
        const unsigned shifts[] = {0, 16, 4, 20, 8, 24, 12, 28};
        for (unsigned c = 0; c < outputs; ++c) {
            double total = 0;
            for (unsigned r = 0; r < inputs; ++r) {
                double weight;
                if (format == 0) {
                    uint64_t packed = uint64_t(r) * (outputs / 8) + c / 8;
                    uint64_t grouped = uint64_t(r / group) * (outputs / 8) + c / 8;
                    int q = (word(data, size, w + 4 * packed, 4) >> shifts[c % 8]) & 15;
                    int zero = (word(data, size, z + 4 * grouped, 4) >> shifts[c % 8]) & 15;
                    double scale = floating(word(data, size,
                        s + 2 * (uint64_t(r / group) * outputs + c), 2), false);
                    if (scale < 0) throw std::runtime_error("negative floating AWQ scale");
                    weight = (q - zero) * scale;
                } else {
                    weight = floating(word(data, size,
                        w + 2 * (uint64_t(c) * inputs + r), 2), format == 1);
                }
                total += activation[r] * weight;
            }
            if (bias_format >= 0)
                total += floating(word(data, size, bias + 2 * c, 2), bias_format == 1);
            if (!std::isfinite(total)) throw std::runtime_error("nonfinite floating dot");
            result[c] = total;
        }
        return 0;
    } catch (const std::exception& e) {
        if (capacity) { std::strncpy(error, e.what(), capacity - 1); error[capacity - 1] = 0; }
        return 1;
    }
}
"""


def decode(bits, bfloat):
    """Exact binary16/bfloat16 value in a Python binary64 container."""
    fractions, bias, limit = (7, 127, 255) if bfloat else (10, 15, 31)
    exponent = bits >> fractions & limit
    fraction = bits & ((1 << fractions) - 1)
    if exponent == limit:
        raise ValueError("nonfinite software-model input")
    mantissa = fraction if exponent == 0 else (1 << fractions) + fraction
    value = math.ldexp(mantissa, (exponent or 1) - bias - fractions)
    return -value if bits & 0x8000 else value


class FloatingGEMV:
    def __init__(self, evidence):
        source = evidence.folder / "floating-gemv.cpp"
        library = evidence.folder / "floating-gemv.so"
        source.write_text("#include <cmath>\n" + FLOAT_CPP)
        evidence.command(["g++", "--version"], "floating-compiler-version")
        evidence.command(
            ["g++", "-std=c++17", "-O3", "-ffp-contract=off", "-Wall", "-Wextra",
             "-Werror", "-shared", "-fPIC", evidence.relative(source),
             "-o", evidence.relative(library)], "floating-compiler")
        evidence.record.setdefault("runtime_input_sha256", {}).update({
            evidence.relative(path): sha(path) for path in (source, library)
        })
        self.library = ctypes.CDLL(str(library))
        self.library.floating_gemv.restype = ctypes.c_int
        self.library.floating_gemv.argtypes = [
            ctypes.c_void_p, ctypes.c_uint64, ctypes.c_int, ctypes.c_uint,
            ctypes.c_uint, ctypes.c_uint, *([ctypes.c_uint64] * 4), ctypes.c_int,
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
            ctypes.c_char_p, ctypes.c_size_t,
        ]

    def evaluate(self, pointer, size, format_id, activation, outputs, group, offsets,
                 bias_format=-1):
        inputs = (ctypes.c_double * len(activation))(*activation)
        result = (ctypes.c_double * outputs)()
        error = ctypes.create_string_buffer(256)
        status = self.library.floating_gemv(
            pointer, size, format_id, len(activation), outputs, group, *offsets,
            bias_format, inputs, result, error, len(error))
        if status:
            raise ValueError(error.value.decode())
        values = list(result)
        if not all(math.isfinite(value) for value in values):
            raise AssertionError("nonfinite software GEMV output")
        return values


def qualify(engine, seed):
    """Different layouts and analytic dots qualify the C++ acceleration only."""
    rng = random.Random(seed)
    compared, rejected, conversions = 0, 0, 0
    for bfloat, format_id in ((False, 2), (True, 1)):
        mask = 0x7f80 if bfloat else 0x7c00
        bits = [value for value in range(65536) if value & mask != mask]
        payload = struct.pack(f"<{len(bits)}H", *bits)
        storage = ctypes.create_string_buffer(payload)
        actual = engine.evaluate(storage, len(payload), format_id, [1.0], len(bits), 1,
                                 (0, 0, 0, 0))
        for value, encoding in zip(actual, bits):
            expected = decode(encoding, bfloat)
            if value != expected:
                raise AssertionError("FP64 checkpoint value differs from Python decoder")
            conversions += 1
        for invalid in (mask, mask | 1, mask | 0x8000, mask | 0x8001):
            storage = ctypes.create_string_buffer(struct.pack("<H", invalid))
            try:
                engine.evaluate(storage, 2, format_id, [1.0], 1, 1, (0, 0, 0, 0))
            except ValueError:
                rejected += 1
            else:
                raise AssertionError("floating evaluator accepted NaN or infinity")
    # Deliberately independent physical-nibble construction, not the RTL mapper.
    permutation = (0, 4, 1, 5, 2, 6, 3, 7)
    for mode in range(3):
        inputs, outputs, group = 24, 16, 8
        activation = [rng.uniform(-8, 8) for _ in range(inputs)]
        bias = [rng.randrange(0x0400, 0x7400) for _ in range(outputs)]
        data = bytearray()
        if mode == 0:
            q = [[rng.randrange(16) for _ in range(outputs)] for _ in range(inputs)]
            z = [[rng.randrange(16) for _ in range(outputs)] for _ in range(inputs // group)]
            scales = [[rng.randrange(0x0400, 0x5000) for _ in range(outputs)]
                      for _ in range(inputs // group)]
            offsets = [0]
            for rows in (q, z):
                for row in rows:
                    for start in range(0, outputs, 8):
                        packed = sum(row[start + lane] << (4 * permutation[lane])
                                     for lane in range(8))
                        data.extend(struct.pack("<I", packed))
                offsets.append(len(data))
            for row in scales:
                data.extend(struct.pack("<16H", *row))
            weights = [[(q[r][c] - z[r // group][c]) * decode(scales[r // group][c], False)
                        for c in range(outputs)] for r in range(inputs)]
            offsets = offsets[:3]
        else:
            bits = [[rng.randrange(0x2000, 0x4200) | (rng.randrange(2) << 15)
                     for _ in range(outputs)] for _ in range(inputs)]
            for c in range(outputs):
                for r in range(inputs):
                    data.extend(struct.pack("<H", bits[r][c]))
            weights = [[decode(value, mode == 1) for value in row] for row in bits]
            offsets = [0, 0, 0]
        offsets.append(len(data))
        data.extend(struct.pack("<16H", *bias))
        storage = ctypes.create_string_buffer(bytes(data))
        for bias_format in (-1, 0, 1):
            actual = engine.evaluate(storage, len(data), mode, activation, outputs, group,
                                     offsets, bias_format)
            for c, value in enumerate(actual):
                terms = [activation[r] * weights[r][c] for r in range(inputs)]
                if bias_format >= 0:
                    terms.append(decode(bias[c], bias_format == 1))
                expected = math.fsum(terms)
                # FP64 reduction error bound, not an RTL parity tolerance.
                bound = 16 * sys.float_info.epsilon * len(terms) * math.fsum(map(abs, terms))
                if abs(value - expected) > bound:
                    raise AssertionError("floating accelerator differs from Python fsum")
                compared += 1
        try:
            engine.evaluate(storage, 0, mode, activation, outputs, group, offsets)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("floating evaluator accepted truncated tensors")
    if compared != 144 or rejected != 11 or conversions != 128768:
        raise AssertionError("missing floating reference qualification")
    return {"floating_dot_comparisons": compared, "invalid_inputs_rejected": rejected,
            "finite_storage_conversions": conversions,
            "arithmetic": "binary64, contraction disabled; Python math.fsum cross-check"}


class FloatingModel:
    """Unquantized activations, exact stored weights, full causal GQA equations."""

    PROJECTIONS = ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj",
                   "self_attn.o_proj", "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj")

    def __init__(self, root, metadata, mode, engine):
        folder = root / mode.lower()
        self.config = json.loads((folder / "config.json").read_text())
        self.inventory = metadata["inventory"]
        self.mode, self.engine = mode, engine
        self.source = (folder / "model.safetensors").open("rb")
        self.mapping = mmap.mmap(self.source.fileno(), 0, access=mmap.ACCESS_COPY)
        self.pointer = ctypes.addressof(ctypes.c_ubyte.from_buffer(self.mapping))
        self.history = [[] for _ in range(24)]
        self.gamma = {
            (layer, phase): self.values(f"model.layers.{layer}.{name}.weight", 0, 896)
            for layer in range(24)
            for phase, name in ((0, "input_layernorm"), (1, "post_attention_layernorm"))
        }
        self.final_gamma = self.values("model.norm.weight", 0, 896)

    def close(self):
        self.mapping.close()
        self.source.close()

    def tensor(self, name):
        return self.inventory["tensors"][name]

    def offset(self, name):
        return 8 + self.inventory["header_bytes"] + self.tensor(name)["data_offsets"][0]

    def values(self, name, start, count):
        tensor = self.tensor(name)
        if (tensor["dtype"] not in ("F16", "BF16") or start < 0 or count < 0 or
                2 * (start + count) > tensor["data_offsets"][1] - tensor["data_offsets"][0]):
            raise ValueError("floating tensor bounds or dtype")
        bits = struct.unpack_from(f"<{count}H", self.mapping, self.offset(name) + 2 * start)
        return [decode(value, tensor["dtype"] == "BF16") for value in bits]

    def projection(self, activation, layer, index):
        prefix = f"model.layers.{layer}.{self.PROJECTIONS[index]}."
        outputs = 128 if index in (1, 2) else 4864 if index in (4, 5) else 896
        if self.mode == "AWQ":
            offsets = [self.offset(prefix + name) for name in ("qweight", "qzeros", "scales")]
            format_id = 0
        else:
            offsets = [self.offset(prefix + "weight"), 0, 0]
            format_id = 1
        offsets.append(self.offset(prefix + "bias") if index < 3 else 0)
        bias_format = int(self.tensor(prefix + "bias")["dtype"] == "BF16") if index < 3 else -1
        return self.engine.evaluate(self.pointer, len(self.mapping), format_id, activation,
                                    outputs, 128, offsets, bias_format)

    def normalize(self, vector, gamma):
        inverse = 1 / math.sqrt(math.fsum(x * x for x in vector) / len(vector) +
                                self.config["rms_norm_eps"])
        return [x * inverse * g for x, g in zip(vector, gamma)]

    def rotate(self, vector, position):
        theta = self.config["rope_theta"]
        for base in range(0, len(vector), 64):
            for pair in range(32):
                angle = position * theta ** (-2 * pair / 64)
                cosine, sine = math.cos(angle), math.sin(angle)
                lo, hi = base + pair, base + pair + 32
                first, second = vector[lo], vector[hi]
                vector[lo] = first * cosine - second * sine
                vector[hi] = first * sine + second * cosine
        return vector

    def token(self, token, position):
        if position == 0:
            self.history = [[] for _ in range(24)]
        if not 0 <= token < 151936 or any(len(history) != position for history in self.history):
            raise ValueError("floating-model token or position order")
        x = self.values("model.embed_tokens.weight", token * 896, 896)
        for layer in range(24):
            normalized = self.normalize(x, self.gamma[layer, 0])
            q, k, v = [self.projection(normalized, layer, index) for index in range(3)]
            q, k = self.rotate(q, position), self.rotate(k, position)
            self.history[layer].append((k, v))
            context = []
            for head in range(14):
                begin, kvbegin = head * 64, (head // 7) * 64
                scores = [math.fsum(q[begin + d] * oldk[kvbegin + d] for d in range(64)) / 8
                          for oldk, _ in self.history[layer]]
                maximum = max(scores)
                probabilities = [math.exp(score - maximum) for score in scores]
                denominator = math.fsum(probabilities)
                context.extend(
                    math.fsum(prob * oldv[kvbegin + d]
                              for prob, (_, oldv) in zip(probabilities, self.history[layer])) /
                    denominator for d in range(64))
            projected = self.projection(context, layer, 3)
            residual = [a + b for a, b in zip(x, projected)]
            normalized = self.normalize(residual, self.gamma[layer, 1])
            gate, up = [self.projection(normalized, layer, index) for index in (4, 5)]
            product = []
            for g, u in zip(gate, up):
                exponential = math.exp(-abs(g))
                sigmoid = 1 / (1 + exponential) if g >= 0 else exponential / (1 + exponential)
                product.append(g * sigmoid * u)
            down = self.projection(product, layer, 6)
            x = [a + b for a, b in zip(residual, down)]
        final = self.normalize(x, self.final_gamma)
        name = "model.embed_tokens.weight"
        format_id = 1 if self.tensor(name)["dtype"] == "BF16" else 2
        return self.engine.evaluate(self.pointer, len(self.mapping), format_id, final, 151936, 128,
                                    (self.offset(name), 0, 0, 0))


def compare(fixed, floating):
    if len(fixed) != 151936 or len(floating) != len(fixed):
        raise AssertionError("software discrepancy requires two complete ordered logit vectors")
    if not all(math.isfinite(value) for value in floating):
        raise AssertionError("nonfinite floating-model logits")
    scaled = [value / 65536 for value in fixed]
    differences = [a - b for a, b in zip(scaled, floating)]
    index = max(range(len(fixed)), key=lambda i: (fixed[i], -i))
    floating_index = max(range(len(floating)), key=lambda i: (floating[i], -i))
    return {
        "ordered_logit_comparisons": len(fixed),
        "max_absolute_error": max(map(abs, differences)),
        "mean_absolute_error": math.fsum(map(abs, differences)) / len(fixed),
        "root_mean_square_error": math.sqrt(math.fsum(d * d for d in differences) / len(fixed)),
        "fixed_point_greedy_token": index, "floating_greedy_token": floating_index,
        "greedy_agreement": index == floating_index,
        "fixed_point_saturated_logits": sum(value in (-2147483648, 2147483647) for value in fixed),
    }


def measure(evidence, manifest_path):
    """Compare a retained reference trajectory without changing its evidence."""
    evidence.command(["python3", "--version"], "software-python-version")
    manifest_path = project_path(manifest_path)
    receipt_path = manifest_path.parent / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    if receipt.get("outcome") != "probe_passed":
        raise ValueError("reference producer did not finish successfully")
    bindings = receipt["runtime_input_sha256"]
    if bindings.get(str(manifest_path)) != sha(manifest_path):
        raise ValueError("reference manifest is not bound to its successful receipt")
    transcript = json.loads(manifest_path.read_text())
    if transcript.get("scope") != "checkpoint_fixed_point_reference_not_RTL_or_board":
        raise ValueError("not a checkpoint integer-reference transcript")
    root = project_path("fixtures/qwen2.5-0.5b")
    metadata = validate(root)
    evidence.record.setdefault("runtime_input_sha256", {}).update({
        str(manifest_path): sha(manifest_path), str(receipt_path): sha(receipt_path),
        str(root / "manifest.json"): sha(root / "manifest.json"),
    })
    for mode in {row["mode"] for row in transcript["rows"]}:
        model = metadata["models"][mode]
        for name, record in model["files"].items():
            path = str(root / mode.lower() / name)
            if bindings.get(path) != record["sha256"]:
                raise ValueError("reference fixture binding differs from pinned checkpoint")
            evidence.record["runtime_input_sha256"][path] = record["sha256"]
    engine = FloatingGEMV(evidence)
    evidence.record["floating_qualification"] = qualify(engine, 17)
    report = {
        "schema": 1, "source_reference": str(manifest_path),
        "scope": "FP64_checkpoint_equations_vs_accepted_parent_fixed_point_not_RTL",
        "arithmetic": "FP64 activations and reductions; original FP16/BF16 checkpoint weights",
        "trajectory": "identical integer-reference input tokens, independent floating KV history",
        "smoke_only": transcript["smoke_only"], "rows": [],
        "published_framework_equivalence": False, "hardware_acceptance": False,
    }
    for row in transcript["rows"]:
        mode = row["mode"]
        expected = metadata["models"][mode]
        if (row["revision"] != expected["revision"] or
                row["checkpoint_sha256"] != expected["tensor_sha256"]):
            raise ValueError("integer reference has mismatched checkpoint identity")
        model = FloatingModel(root, expected, mode, engine)
        result = {"mode": mode, "prompt_index": row["prompt_index"],
                  "prompt": row["prompt"], "steps": []}
        report["rows"].append(result)
        try:
            for position, step in enumerate(row["steps"]):
                if step["position"] != position:
                    raise ValueError("nonconsecutive integer reference positions")
                path = project_path(step["ordered_logits"])
                digest = sha(path)
                if digest != step["logits_sha256"] or bindings.get(str(path)) != digest:
                    raise ValueError("integer logit source hash differs from producer receipt")
                payload = path.read_bytes()
                if len(payload) != 151936 * 4:
                    raise ValueError("truncated integer logit vector")
                fixed = struct.unpack("<151936i", payload)
                floating = model.token(step["input_token"], position)
                metrics = compare(fixed, floating)
                if metrics["fixed_point_greedy_token"] != step["selected_token"]:
                    raise ValueError("integer reference token differs from complete logit argmax")
                output = evidence.folder / f"{mode.lower()}-prompt{row['prompt_index']}-pos{position}-fp64.bin"
                with output.open("xb") as stream:
                    stream.write(struct.pack("<151936d", *floating))
                evidence.record["runtime_input_sha256"].update({
                    str(path): digest, evidence.relative(output): sha(output)})
                metrics.update(position=position, input_token=step["input_token"],
                               floating_logits=evidence.relative(output))
                result["steps"].append(metrics)
                print(json.dumps({"mode": mode, "prompt_index": row["prompt_index"],
                                  **{key: metrics[key] for key in
                                     ("position", "max_absolute_error", "greedy_agreement")}}),
                      flush=True)
                with (evidence.folder / f"discrepancy-{mode.lower()}-{row['prompt_index']}-{position}.json").open("x") as stream:
                    json.dump(metrics, stream, indent=2)
                evidence.flush()
        finally:
            model.close()
    steps = [step for row in report["rows"] for step in row["steps"]]
    if len(steps) != transcript["ordered_logit_vectors"] or not steps:
        raise AssertionError("software comparison did not cover every supplied reference vector")
    report["summary"] = {
        "vectors_compared": len(steps),
        "ordered_logit_comparisons": sum(step["ordered_logit_comparisons"] for step in steps),
        "greedy_agreements": sum(step["greedy_agreement"] for step in steps),
        "max_absolute_error": max(step["max_absolute_error"] for step in steps),
        "discrepancy_is_not_RTL_parity_failure_or_permission_to_relax_parity": True,
    }
    output = evidence.folder / "software-discrepancy.json"
    with output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    evidence.record["runtime_input_sha256"][evidence.relative(output)] = sha(output)
    evidence.record["observations"].append({
        "report": evidence.relative(output), **report["summary"],
        "published_framework_equivalence": False, "hardware_acceptance": False,
    })
    evidence.flush()


def main():
    from verify import Evidence
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--reference-manifest",
                        help="project-relative retained checkpoint-reference.json")
    selection.add_argument("--qualification-only", action="store_true")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    evidence = Evidence("software-discrepancy", args.repair_of)
    try:
        if args.qualification_only:
            engine = FloatingGEMV(evidence)
            evidence.record["floating_qualification"] = qualify(engine, 17)
            evidence.finish("probe_passed", "Software GEMV qualification only; no network comparison.")
        else:
            measure(evidence, args.reference_manifest)
            evidence.finish("probe_passed", "FP64 discrepancy measured; no hardware acceptance claim.")
        return 0
    except Exception as exc:
        evidence.finish("probe_failed", f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
