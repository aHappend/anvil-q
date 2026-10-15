"""Raw official checkpoint integration; partial coverage never certifies inference.

Requirement mapping: Checkpoint validates provenance/layout/coverage; FP32Model
implements raw-F16 software algebra; FixedModel implements SPEC integer algebra;
rtl_forward compares ordered public writes/logits and measures public transfers.
All dependencies are Python standard library. No checkpoint data is synthesized.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path
import platform
import struct
import sys


PROJECTIONS = ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj",
               "self_attn.o_proj", "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj")
SHIFTS = (0, 16, 4, 20, 8, 24, 12, 28)
DEFAULT_SHAPE = (24, 896, 4864, 14, 2, 64, 128, 151936, 32768)
SOFTWARE_LABEL = "Software Layer (Official HuggingFace FP32/FP16 AWQ Weights)"
HARDWARE_LABEL = "Hardware RTL Output (Official HuggingFace W4A16 RTL Execution)"
PRECISION = {
    "storage": "original binary16 and signed I32 AWQ GEMM words",
    "software": "IEEE binary32 via struct.pack/unpack <f, nearest/ties-even",
    "rounding": "every add/subtract/multiply/divide; separate multiply/add, no FMA",
    "reduction": "increasing input/component/time order; initial FP32 zero",
    "dequantization": "round (q-z)*raw_F16_scale; no fixed-point conversion; no z+1",
    "norm": "round square,sum,/H,+f32(1e-6),sqrt,(x*gamma)/denominator",
    "transcendentals": "host math sqrt/exp/sin/cos followed by binary32 rounding",
    "rope": "f32(position*pow(1e6,-2*i/D)); split-half, independent floating trig",
    "softmax": "max-subtracted, rounded exp/sum/probability/weighted reduction",
    "silu": "stable positive/negative branches with rounded elementary operations",
    "hardware": "SPEC signed32 Q16.16; raw F16 bus; Q2.30 RoPE",
    "postprocessing": "binary64 metrics; not software forward arithmetic",
    "kernel_equivalence": "specified operation order, not an unspecified GPU kernel",
}


class CheckpointError(ValueError):
    pass


class CoverageError(CheckpointError):
    pass


def demand(condition, message):
    if not condition:
        raise CheckpointError(message)


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        demand(key not in obj, "duplicate JSON key: " + key)
        obj[key] = value
    return obj


def strict_json(data):
    return json.loads(data, object_pairs_hook=unique_object,
                      parse_constant=lambda value: invalid_constant(value))


def invalid_constant(value):
    raise CheckpointError("nonfinite JSON constant: " + value)


def shape_valid(shape):
    return (isinstance(shape, list) and bool(shape) and
            all(type(v) is int and v > 0 for v in shape))


def expected_tensors():
    result = {"model.embed_tokens.weight": ("F16", [151936, 896]),
              "model.norm.weight": ("F16", [896]),
              "lm_head.weight": ("F16", [151936, 896])}
    dims = ((896, 896), (896, 128), (896, 128), (896, 896),
            (896, 4864), (896, 4864), (4864, 896))
    for layer in range(24):
        for norm in ("input_layernorm", "post_attention_layernorm"):
            result[f"model.layers.{layer}.{norm}.weight"] = "F16", [896]
        for p, (ni, no) in enumerate(dims):
            prefix = f"model.layers.{layer}.{PROJECTIONS[p]}."
            result[prefix + "qweight"] = "I32", [ni, no // 8]
            result[prefix + "qzeros"] = "I32", [ni // 128, no // 8]
            result[prefix + "scales"] = "F16", [ni // 128, no]
            if p < 3:
                result[prefix + "bias"] = "F16", [no]
    return result


def parse_safetensors(data):
    demand(len(data) >= 8, "safetensors truncated length")
    size = struct.unpack_from("<Q", data)[0]
    demand(2 <= size <= len(data) - 8 and size % 8 == 0,
           "safetensors invalid header length")
    try:
        header = strict_json(data[8:8 + size].decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CheckpointError("safetensors malformed header: " + str(exc)) from exc
    demand(isinstance(header, dict), "safetensors header must be an object")
    payload_base = 8 + size
    descriptors, intervals = {}, []
    for name, entry in header.items():
        if name == "__metadata__":
            demand(isinstance(entry, dict) and
                   all(isinstance(k, str) and isinstance(v, str)
                       for k, v in entry.items()), "safetensors metadata structure")
            continue
        demand(isinstance(entry, dict) and
               set(entry) == {"dtype", "shape", "data_offsets"},
               "safetensors tensor descriptor: " + name)
        dtype, shape, offsets = entry["dtype"], entry["shape"], entry["data_offsets"]
        demand(dtype in ("F16", "I32"), "safetensors unsupported dtype: " + name)
        demand(shape_valid(shape), "safetensors invalid shape: " + name)
        demand(isinstance(offsets, list) and len(offsets) == 2 and
               all(type(v) is int for v in offsets), "safetensors invalid offsets: " + name)
        lo, hi = offsets
        width = 2 if dtype == "F16" else 4
        demand(0 <= lo < hi <= len(data) - payload_base and
               hi - lo == math.prod(shape) * width,
               "safetensors payload bounds/length: " + name)
        intervals.append((lo, hi, name))
        descriptors[name] = dict(dtype=dtype, shape=tuple(shape), start=lo,
                                 end=hi, width=width)
    intervals.sort()
    cursor = 0
    for lo, hi, name in intervals:
        demand(lo == cursor, "safetensors overlapping or noncontiguous payload: " + name)
        cursor = hi
    demand(cursor == len(data) - payload_base, "safetensors trailing/unindexed payload")
    demand(bool(descriptors), "safetensors empty tensor inventory")
    return payload_base, descriptors


class Checkpoint:
    def __init__(self, root, *, data=None, manifest=None, excerpts=None):
        self.root = Path(root)
        base = self.root / "hf_qwen25_05b_awq_spec"
        directory = base / "official_weights"
        self.path = directory / "qwen25_05b_awq_official_slice.safetensors"
        self.data = self.path.read_bytes() if data is None else bytes(data)
        self.manifest = (strict_json((directory / "official_weights_manifest.json").read_text())
                         if manifest is None else manifest)
        self.sha256 = hashlib.sha256(self.data).hexdigest()
        demand(self.sha256 == self.manifest["extracted_safetensors_sha256"],
               "checkpoint SHA-256 mismatch")
        self.base, self.tensors = parse_safetensors(self.data)
        self.original = strict_json((base / "qwen25_05b_awq_tensors.json").read_text())
        self.config = strict_json((base / "config.json").read_text())
        self._validate_original()
        entries = self.manifest["tensors"]
        demand(isinstance(entries, list) and
               len(entries) == self.manifest["tensor_count_extracted"],
               "extracted manifest tensor count")
        names = [entry["name"] for entry in entries]
        demand(len(set(names)) == len(names) and set(names) == set(self.tensors),
               "extracted manifest inventory/duplicates")
        self.payload_sha256 = {}
        original_base = 8 + self.manifest["safetensors_header_bytes"]
        demand(original_base == 68440 and
               self.manifest["safetensors_total_bytes"] == 730652248,
               "original HF byte extent")
        demand(self.manifest["source_repo"] == "Qwen/Qwen2.5-0.5B-Instruct-AWQ" and
               self.manifest["source_url"] == self.original["source_url"],
               "official model source identity")
        for entry in entries:
            name = entry["name"]
            demand(name in self.original["tensors"], "unknown extracted tensor: " + name)
            t, original = self.tensors[name], self.original["tensors"][name]
            loaded, full = entry["loaded_shape"], entry["original_shape"]
            demand(shape_valid(loaded) and shape_valid(full) and
                   tuple(loaded) == t["shape"] and full == original["shape"] and
                   t["dtype"] == entry["dtype"] == original["dtype"],
                   "extracted shape/dtype mismatch: " + name)
            demand(len(loaded) == len(full) and 0 < loaded[0] <= full[0] and
                   loaded[1:] == full[1:], "non-prefix extracted coverage: " + name)
            hf = entry["hf_byte_range"]
            demand(isinstance(hf, list) and len(hf) == 2 and
                   all(type(v) is int for v in hf), "invalid HF byte range: " + name)
            lo, hi = hf
            demand(lo == original_base + original["data_offsets"][0] and
                   hi - lo + 1 == t["end"] - t["start"] and
                   hi < original_base + original["data_offsets"][1],
                   "HF byte range/prefix mismatch: " + name)
            payload = self.data[self.base + t["start"]:self.base + t["end"]]
            digest = hashlib.sha256(payload).hexdigest()
            demand(digest == entry["sha256"], "tensor SHA-256 mismatch: " + name)
            self.payload_sha256[name] = digest
        excerpts = (strict_json((directory / "official_hardware_slices_fp16_awq.json").read_text())
                    if excerpts is None else excerpts)
        self.excerpt_values = self._crosscheck(excerpts)
        self.coverage = self._coverage()

    def _validate_original(self):
        expected = expected_tensors()
        demand(len(expected) == 627 and self.original["num_tensors"] == 627 and
               set(expected) == set(self.original["tensors"]), "original 627-tensor inventory")
        spans = []
        for name, (dtype, shape) in expected.items():
            actual = self.original["tensors"][name]
            demand(actual["dtype"] == dtype and actual["shape"] == shape,
                   "original tensor shape/dtype: " + name)
            offsets = actual["data_offsets"]
            demand(isinstance(offsets, list) and len(offsets) == 2 and
                   all(type(x) is int for x in offsets), "original offsets: " + name)
            lo, hi = offsets
            demand(lo >= 0 and hi - lo == math.prod(shape) * (2 if dtype == "F16" else 4),
                   "original tensor byte length: " + name)
            spans.append((lo, hi))
        spans.sort()
        demand(spans[0][0] == 0 and all(a[1] == b[0] for a, b in zip(spans, spans[1:]))
               and spans[-1][1] == 730652248 - 68440,
               "original tensor payload extent/nonoverlap")
        c = self.config
        required = dict(num_hidden_layers=24, hidden_size=896, intermediate_size=4864,
                        num_attention_heads=14, num_key_value_heads=2,
                        vocab_size=151936, max_position_embeddings=32768,
                        model_type="qwen2", architectures=["Qwen2ForCausalLM"],
                        hidden_act="silu", rms_norm_eps=1e-6, rope_theta=1000000.0,
                        tie_word_embeddings=True, use_sliding_window=False)
        demand(all(c.get(k) == v for k, v in required.items()), "official model configuration")
        quant = c["quantization_config"]
        demand(all(quant.get(k) == v for k, v in
                   dict(bits=4, group_size=128, quant_method="awq",
                        version="gemm", zero_point=True).items()), "AWQ GEMM G128 configuration")
        demand(self.original["awq_packing_order"] == [s // 4 for s in SHIFTS],
               "original AWQ packing order")

    def _crosscheck(self, excerpts):
        demand(excerpts["model_id"] == "Qwen/Qwen2.5-0.5B-Instruct-AWQ" and
               excerpts["awq_gemm_unpack_order"] == [s // 4 for s in SHIFTS] and
               excerpts["group_size"] == 128 and excerpts["bits"] == 4,
               "hardware excerpt configuration")
        checked = 0
        for name, excerpt in excerpts["tensors"].items():
            demand(name in self.tensors, "excerpt uncovered tensor: " + name)
            t = self.tensors[name]
            demand(excerpt["dtype"] == t["dtype"] and
                   excerpt["full_shape"] == self.original["tensors"][name]["shape"],
                   "excerpt full shape/dtype: " + name)
            shape = excerpt["slice_shape"]
            demand(shape_valid(shape) and len(shape) == len(t["shape"]) and
                   all(a <= b for a, b in zip(shape, t["shape"])),
                   "excerpt slice shape: " + name)

            def visit(raw, axis=0, coord=()):
                nonlocal checked
                if axis == len(shape):
                    demand(isinstance(raw, str) and
                           int(raw, 16) == self.raw(name, coord),
                           f"excerpt raw_hex mismatch: {name}{coord}")
                    checked += 1
                else:
                    demand(isinstance(raw, list) and len(raw) == shape[axis],
                           "excerpt raw_hex extent: " + name)
                    for i, item in enumerate(raw):
                        visit(item, axis + 1, coord + (i,))
            visit(excerpt["raw_hex"])
        return checked

    def _coverage(self):
        missing, inventory, available = [], [], 0
        for name, original in self.original["tensors"].items():
            full = original["shape"]
            loaded = list(self.tensors[name]["shape"]) if name in self.tensors else None
            required = name != "lm_head.weight"
            have = math.prod(loaded) if loaded else 0
            if required:
                available += have
            inventory.append(dict(tensor=name, dtype=original["dtype"],
                                  original_shape=full, loaded_shape=loaded,
                                  required_for_tied_execution=required))
            if required and loaded != full:
                first = loaded[0] if loaded else 0
                missing.append(dict(tensor=name, original_shape=full,
                                    missing_coordinates=[[first, full[0]]] +
                                    [[0, n] for n in full[1:]],
                                    missing_elements=(full[0] - first) * math.prod(full[1:])))
        needed = sum(math.prod(t["shape"]) for name, t in self.original["tensors"].items()
                     if name != "lm_head.weight")
        return dict(complete=not missing, extracted_tensors=len(self.tensors),
                    original_tensors=627, quantized_linear_modules=168,
                    inventory=inventory, missing=missing,
                    missing_tensor_count=sum(name not in self.tensors
                                             for name in self.original["tensors"]
                                             if name != "lm_head.weight"),
                    required_elements=needed, available_elements=available,
                    missing_elements=needed - available,
                    absent_duplicate_lm_head="lm_head.weight" not in self.tensors,
                    tied_storage="model.embed_tokens.weight",
                    excerpt_raw_values_checked=self.excerpt_values)

    def require_complete(self):
        if not self.coverage["complete"]:
            first = self.coverage["missing"][0]
            raise CoverageError(f"full official execution blocked: {len(self.coverage['missing'])} "
                                f"missing/partial tensors; {first['tensor']} "
                                f"{first['missing_coordinates']}")

    def raw(self, name, coordinate):
        coordinate = tuple(coordinate)
        if name not in self.tensors:
            raise CoverageError(f"uncovered tensor {name} coordinate {coordinate}")
        t = self.tensors[name]
        if len(coordinate) != len(t["shape"]) or any(
                type(i) is not int or i < 0 or i >= n for i, n in zip(coordinate, t["shape"])):
            raise CoverageError(f"uncovered tensor {name} coordinate {coordinate}; "
                                f"loaded shape {t['shape']}")
        index = 0
        for i, n in zip(coordinate, t["shape"]):
            index = index * n + i
        offset = self.base + t["start"] + t["width"] * index
        return struct.unpack_from("<H" if t["dtype"] == "F16" else "<I", self.data, offset)[0]

    def signed_i32(self, name, coordinate):
        demand(self.tensors[name]["dtype"] == "I32", "signed I32 dtype: " + name)
        raw = self.raw(name, coordinate)
        return raw if raw < 2**31 else raw - 2**32

    def half(self, name, coordinate):
        demand(self.tensors[name]["dtype"] == "F16", "floating F16 dtype: " + name)
        value = struct.unpack("<e", struct.pack("<H", self.raw(name, coordinate)))[0]
        demand(math.isfinite(value), f"nonfinite F16 {name}{tuple(coordinate)}")
        return value

    @staticmethod
    def resolve(kind, layer, projection, row, col):
        demand(all(type(v) is int and v >= 0 for v in (kind, layer, projection, row, col)),
               "invalid public model address")
        if kind == 0:
            demand(layer == projection == 0, "embedding unused address fields")
            return "model.embed_tokens.weight", (row, col)
        if kind in (1, 2, 3, 4):
            demand(layer < 24 and projection < (3 if kind == 4 else 7),
                   "projection/layer address")
            prefix = f"model.layers.{layer}.{PROJECTIONS[projection]}."
            if kind == 4:
                demand(row == 0, "bias unused row")
                return prefix + "bias", (col,)
            return prefix + ("qweight", "qzeros", "scales")[kind - 1], (row, col)
        if kind in (5, 6, 7):
            demand(projection == row == 0 and layer < 24 and (kind != 7 or layer == 0),
                   "norm unused address fields")
            name = ("model.norm.weight" if kind == 7 else
                    f"model.layers.{layer}." +
                    ("input_layernorm.weight" if kind == 5 else "post_attention_layernorm.weight"))
            return name, (col,)
        raise CheckpointError(f"not a checkpoint model kind: {kind}")

    def bus(self, kind, layer, projection, row, col):
        return self.raw(*self.resolve(kind, layer, projection, row, col))


def f32(value):
    demand(math.isfinite(value), "FP32 nonfinite arithmetic input")
    try:
        result = struct.unpack("<f", struct.pack("<f", value))[0]
    except OverflowError as exc:
        raise CheckpointError("FP32 overflow") from exc
    demand(math.isfinite(result), "FP32 nonfinite arithmetic result")
    return result


def fp_sum(values):
    total = f32(0.0)
    for value in values:
        total = f32(total + value)
    return total


class FP32Model:
    """Independent raw binary16 baseline; never uses the integer oracle."""
    def __init__(self, checkpoint, shape=DEFAULT_SHAPE):
        self.checkpoint, self.shape, self.cache = checkpoint, shape, {}
        self.trace = {}
        self.next_position = 0

    def value(self, kind, layer, projection, row, col):
        name, coord = self.checkpoint.resolve(kind, layer, projection, row, col)
        return f32(self.checkpoint.half(name, coord))

    def norm(self, x, kind, layer):
        mean = f32(fp_sum(f32(v * v) for v in x) / len(x))
        denominator = f32(math.sqrt(f32(mean + f32(1e-6))))
        demand(denominator > 0, "FP32 RMSNorm zero denominator")
        return [f32(f32(v * self.value(kind, layer, 0, 0, c)) / denominator)
                for c, v in enumerate(x)]

    def linear(self, x, layer, projection):
        _, h, intermediate, _, kvheads, d, group, _, _ = self.shape
        no = (kvheads * d if projection in (1, 2) else
              intermediate if projection in (4, 5) else h)
        result = []
        for c in range(no):
            products = []
            for k, activation in enumerate(x):
                qw = self.checkpoint.bus(1, layer, projection, k, c // 8)
                qz = self.checkpoint.bus(2, layer, projection, k // group, c // 8)
                delta = ((qw >> SHIFTS[c % 8]) & 15) - ((qz >> SHIFTS[c % 8]) & 15)
                scale = self.value(3, layer, projection, k // group, c)
                demand(scale >= 0, "FP32 negative AWQ scale")
                weight = f32(delta * scale)
                products.append(f32(activation * weight))
            total = fp_sum(products)
            if projection < 3:
                total = f32(total + self.value(4, layer, projection, 0, c))
            result.append(total)
        return result

    def rotate(self, x, heads, position):
        d = self.shape[5]
        result = list(x)
        for head in range(heads):
            for pair in range(d // 2):
                angle = f32(position * math.pow(1000000.0, -2 * pair / d))
                co, si = f32(math.cos(angle)), f32(math.sin(angle))
                a, b = head * d + pair, head * d + pair + d // 2
                result[a] = f32(f32(x[a] * co) - f32(x[b] * si))
                result[b] = f32(f32(x[b] * co) + f32(x[a] * si))
        return result

    def token(self, token, position, new_sequence=False):
        layers, h, _, qheads, kvheads, d, _, vocab, seq = self.shape
        demand(0 <= token < vocab and 0 <= position < seq, "FP32 token bounds")
        if new_sequence:
            demand(position == 0, "FP32 new sequence at nonzero position")
            self.cache.clear()
            self.next_position = 0
        demand(position == self.next_position, "FP32 nonsequential token")
        self.trace = {}
        def capture(layer, stage, values):
            self.trace[layer, stage] = list(values)
            return values
        x = capture(-1, "embedding", [self.value(0, 0, 0, token, c) for c in range(h)])
        for layer in range(layers):
            normalized = capture(layer, "norm_input", self.norm(x, 5, layer))
            q, k, v = [capture(layer, stage, self.linear(normalized, layer, p))
                       for p, stage in enumerate(("q", "k", "v"))]
            q = capture(layer, "q_rope", self.rotate(q, qheads, position))
            k = capture(layer, "k_rope", self.rotate(k, kvheads, position))
            self.cache[layer, position] = k, v
            context = []
            denominator = f32(math.sqrt(d))
            for head in range(qheads):
                kh = head // (qheads // kvheads)
                scores = [f32(fp_sum(f32(q[head * d + c] *
                                              self.cache[layer, t][0][kh * d + c])
                                    for c in range(d)) / denominator)
                          for t in range(position + 1)]
                maximum = max(scores)
                exps = [f32(math.exp(f32(s - maximum))) for s in scores]
                total = fp_sum(exps)
                demand(total > 0, "FP32 softmax zero denominator")
                probabilities = [f32(e / total) for e in exps]
                context.extend(fp_sum(f32(probabilities[t] *
                                          self.cache[layer, t][1][kh * d + c])
                                      for t in range(position + 1)) for c in range(d))
            capture(layer, "context", context)
            projected = capture(layer, "o", self.linear(context, layer, 3))
            residual = capture(layer, "residual_attention",
                               [f32(a + b) for a, b in zip(x, projected)])
            normalized = capture(layer, "norm_post", self.norm(residual, 6, layer))
            gate = capture(layer, "gate", self.linear(normalized, layer, 4))
            up = capture(layer, "up", self.linear(normalized, layer, 5))
            silu = []
            for value in gate:
                e = f32(math.exp(-abs(value)))
                denominator = f32(1.0 + e)
                silu.append(f32(value / denominator) if value >= 0 else
                            f32(f32(value * e) / denominator))
            capture(layer, "silu", silu)
            product = capture(layer, "product", [f32(a * b) for a, b in zip(silu, up)])
            down = capture(layer, "down", self.linear(product, layer, 6))
            x = capture(layer, "residual_mlp", [f32(a + b) for a, b in zip(residual, down)])
        final = capture(-1, "final", self.norm(x, 7, 0))
        logits = [fp_sum(f32(value * self.value(0, 0, 0, row, c))
                         for c, value in enumerate(final)) for row in range(vocab)]
        self.next_position += 1
        return logits


def round_away(numerator, denominator):
    demand(denominator > 0, "integer zero denominator")
    magnitude = (2 * abs(numerator) + denominator) // (2 * denominator)
    return -magnitude if numerator < 0 else magnitude


def clip32(value):
    return min(2**31 - 1, max(-2**31, value))


def half_integer(raw, *, scale=False):
    exponent, mantissa = (raw >> 10) & 31, raw & 1023
    demand(exponent != 31, "integer nonfinite F16")
    significand = mantissa if exponent == 0 else mantissa + 1024
    sign = -1 if raw & 0x8000 else 1
    demand(not scale or sign > 0 or significand == 0, "integer negative AWQ scale")
    power = -8 if exponent == 0 else exponent - 9
    result = round_away(sign * significand * 2**max(power, 0), 2**max(-power, 0))
    return result if scale else clip32(result)


def integer_exp(value):
    demand(value <= 0, "integer exp positive input")
    if value < -16 * 65536:
        return 0
    n, remainder = divmod((-value) << 8, 11629080)
    term = total = 2**24
    for order in range(1, 7):
        numerator = -term * remainder
        term = (-1 if numerator < 0 else 1) * (abs(numerator) // (order * 2**24))
        total += term
    return max(0, total) >> n


class FixedModel:
    """Exact mathematical equations, independent of FP32 and RTL scheduling."""
    def __init__(self, checkpoint, shape=DEFAULT_SHAPE):
        self.checkpoint, self.shape, self.cache = checkpoint, shape, {}
        self.next_position = 0

    def value(self, kind, layer, projection, row, col):
        return half_integer(self.checkpoint.bus(kind, layer, projection, row, col))

    def token(self, token, position, new_sequence=False):
        layers, h, intermediate, qheads, kvheads, d, group, vocab, seq = self.shape
        demand(0 <= token < vocab and 0 <= position < seq, "integer token bounds")
        if new_sequence:
            demand(position == 0, "integer new sequence at nonzero position")
            self.cache.clear()
            self.next_position = 0
        demand(position == self.next_position, "integer nonsequential token")
        self.writes, self.trace, self.saturation = [], {}, {}
        self.saturated_coordinates, bound_calls = {}, {}
        active = (-1, "embedding")

        def bounded(value):
            index = bound_calls.get(active, 0)
            bound_calls[active] = index + 1
            if value < -2**31 or value >= 2**31:
                self.saturation[active] = self.saturation.get(active, 0) + 1
                self.saturated_coordinates.setdefault(active, set()).add(index)
            return clip32(value)

        def capture(layer, stage, values):
            self.trace[layer, stage] = list(values)
            return values

        def store(slot, values):
            self.writes.extend((8, 0, slot, c, v & 0xffffffff) for c, v in enumerate(values))

        def norm(x, layer, kind, slot, stage):
            nonlocal active
            active = (-1 if kind == 7 else layer), stage
            denominator = math.isqrt((sum(v * v for v in x) << 32) // h + 18446744073710)
            demand(denominator > 0, "integer RMSNorm zero denominator")
            reciprocal = 2**64 // denominator
            result = [bounded(round_away(v * self.value(kind, layer, 0, 0, c) *
                                         reciprocal, 2**48)) for c, v in enumerate(x)]
            store(slot, result)
            return capture(active[0], stage, result)

        def linear(x, layer, projection, slot):
            nonlocal active
            stage = ("q", "k", "v", "o", "gate", "up", "down")[projection]
            active = layer, stage
            no = kvheads * d if projection in (1, 2) else intermediate if projection in (4, 5) else h
            result = []
            for c in range(no):
                total = 0
                for k, activation in enumerate(x):
                    qw = self.checkpoint.bus(1, layer, projection, k, c // 8)
                    qz = self.checkpoint.bus(2, layer, projection, k // group, c // 8)
                    delta = ((qw >> SHIFTS[c % 8]) & 15) - ((qz >> SHIFTS[c % 8]) & 15)
                    scale = half_integer(self.checkpoint.bus(3, layer, projection, k // group, c),
                                         scale=True)
                    total += activation * delta * scale
                if projection < 3:
                    total += self.value(4, layer, projection, 0, c) * 65536
                result.append(bounded(round_away(total, 65536)))
            store(slot, result)
            return capture(layer, stage, result)

        def rotate(x, layer, heads, slot, stage):
            nonlocal active
            active = layer, stage
            result = list(x)
            for head in range(heads):
                for pair in range(d // 2):
                    co, si = rope_words(position, pair, d)
                    a, b = head * d + pair, head * d + pair + d // 2
                    result[a] = bounded(round_away(x[a] * co - x[b] * si, 2**30))
                    result[b] = bounded(round_away(x[b] * co + x[a] * si, 2**30))
                    self.writes.extend(((8, 0, slot, a, result[a] & 0xffffffff),
                                        (8, 0, slot, b, result[b] & 0xffffffff)))
            return capture(layer, stage, result)

        x = capture(-1, "embedding", [self.value(0, 0, 0, token, c) for c in range(h)])
        store(0, x)
        for layer in range(layers):
            normalized = norm(x, layer, 5, 1, "norm_input")
            q, k, v = [linear(normalized, layer, p, slot)
                       for p, slot in ((0, 2), (1, 3), (2, 4))]
            q = rotate(q, layer, qheads, 2, "q_rope")
            k = rotate(k, layer, kvheads, 3, "k_rope")
            self.cache[layer, position] = k, v
            self.writes.extend((kind, layer, position, c, value & 0xffffffff)
                               for kind, values in ((9, k), (10, v)) for c, value in enumerate(values))
            active = layer, "context"
            context = []
            for head in range(qheads):
                kh = head // (qheads // kvheads)
                scores = [round_away(sum(q[head * d + c] *
                                              self.cache[layer, t][0][kh * d + c]
                                              for c in range(d)), math.isqrt(d << 32))
                          for t in range(position + 1)]
                exps = [integer_exp(s - max(scores)) for s in scores]
                denominator = sum(exps)
                demand(denominator > 0, "integer softmax zero denominator")
                context.extend(bounded(round_away(sum(e * self.cache[layer, t][1][kh * d + c]
                                                       for t, e in enumerate(exps)), denominator))
                               for c in range(d))
            store(5, context)
            capture(layer, "context", context)
            projected = linear(context, layer, 3, 6)
            active = layer, "residual_attention"
            residual = capture(layer, "residual_attention", [bounded(a + b) for a, b in zip(x, projected)])
            store(7, residual)
            normalized = norm(residual, layer, 6, 8, "norm_post")
            gate, up = linear(normalized, layer, 4, 9), linear(normalized, layer, 5, 10)
            silu = []
            active = layer, "silu"
            for value in gate:
                e = integer_exp(-abs(value))
                sigmoid = (2**48 if value >= 0 else e * 2**24) // (2**24 + e)
                silu.append(bounded(round_away(value * sigmoid, 2**24)))
            capture(layer, "silu", silu)
            active = layer, "product"
            product = capture(layer, "product", [bounded(round_away(a * b, 65536))
                                                 for a, b in zip(silu, up)])
            store(11, product)
            down = linear(product, layer, 6, 12)
            active = layer, "residual_mlp"
            x = capture(layer, "residual_mlp", [bounded(a + b) for a, b in zip(residual, down)])
            store(0, x)
        final = norm(x, 0, 7, 14, "final")
        active = -1, "logits"
        logits = [bounded(round_away(sum(v * self.value(0, 0, 0, row, c)
                                         for c, v in enumerate(final)), 65536))
                  for row in range(vocab)]
        self.next_position += 1
        return logits


def rope_words(position, pair, d):
    angle = position * 1000000.0**(-2 * pair / d)
    return tuple(round_away(int(v * 2**52), 2**22) for v in (math.cos(angle), math.sin(angle)))


def logit_metrics(actual, reference):
    demand(len(actual) == len(reference) and len(actual) >= 5, "logit metric denominator")
    demand(all(math.isfinite(v) for v in itertools.chain(actual, reference)),
           "nonfinite logit metrics")
    errors = [abs(a - b) for a, b in zip(actual, reference)]
    n = len(errors)
    anorm, bnorm = math.fsum(v * v for v in actual), math.fsum(v * v for v in reference)
    atop = sorted(range(n), key=lambda i: (-actual[i], i))[:5]
    btop = sorted(range(n), key=lambda i: (-reference[i], i))[:5]
    return dict(compared_logits=n, max_absolute_error=max(errors),
                mean_absolute_error=math.fsum(errors) / n,
                rmse=math.sqrt(math.fsum(e * e for e in errors) / n),
                cosine_similarity=(math.fsum(a * b for a, b in zip(actual, reference)) /
                                   math.sqrt(anorm * bnorm) if anorm and bnorm else None),
                cosine_undefined_reason=(None if anorm and bnorm else "zero-norm vector"),
                k=5, top1_agreement=atop[0] == btop[0],
                top5_overlap_fraction=len(set(atop) & set(btop)) / 5,
                exact_top5_set_agreement=set(atop) == set(btop),
                hardware_top5=atop, software_top5=btop)


def comparison_skeleton(run, checkpoint):
    return dict(status="incomplete", software_label=SOFTWARE_LABEL, hardware_label=HARDWARE_LABEL,
                source_sha256=run.source_hashes, checkpoint_sha256=checkpoint.sha256,
                tensor_payload_sha256=checkpoint.payload_sha256, coverage=checkpoint.coverage,
                model_configuration=checkpoint.config, shape=list(DEFAULT_SHAPE),
                coordinate_mapping=dict(
                    projections=list(PROJECTIONS), awq_shifts=list(SHIFTS),
                    model_kinds={"0": "embedding[row,col] (also tied logits)",
                                 "1": "projection.qweight[input,packed_output]",
                                 "2": "projection.qzeros[group,packed_output]",
                                 "3": "projection.scales[group,output]",
                                 "4": "QKV.bias[col], row=0",
                                 "5": "input_layernorm[col], row=proj=0",
                                 "6": "post_attention_layernorm[col], row=proj=0",
                                 "7": "model.norm[col], layer=row=proj=0"},
                    file_element_offset="parsed_payload_base + tensor_start + width*row_major_index",
                    layer_mapping="literal original layer, no remapping",
                    uncovered_address="explicit CoverageError with tensor and coordinate"),
                precision=dict(PRECISION, python=sys.version, platform=platform.platform()),
                sequence=[], completed_tokens=0,
                bit_comparison=dict(mismatches=None, compared_writes=0, compared_logits=0,
                                    reason="RTL inference has not completed"),
                per_token=[], aggregate_metrics=None, intermediate_diagnostics=[],
                saturation=None, cycle_measurements=None, memory_transactions=None,
                blockers=[], metrics_unavailable_reason="full official inference not executed")


def write_comparison(run, report):
    (run.out / "official_weights_comparison.json").write_text(json.dumps(report, indent=2) + "\n")


def audit_checkpoint(run, root):
    checkpoint = Checkpoint(root)
    report = comparison_skeleton(run, checkpoint)
    if not checkpoint.coverage["complete"]:
        report["blockers"].append("Missing official tensors/rows; see coverage.missing. "
                                  "No padding, cropped model or skipped layers closes full inference.")
    write_comparison(run, report)
    run.result("official-checkpoint", outcome="provenance_validated",
               checkpoint_sha256=checkpoint.sha256, parsed_tensors=len(checkpoint.tensors),
               raw_excerpt_values=checkpoint.excerpt_values,
               coverage_complete=checkpoint.coverage["complete"],
               missing_elements=checkpoint.coverage["missing_elements"])
    return checkpoint, report


def checkpoint_reader(checkpoint):
    """SystemVerilog byte service reads original file, not converted hex data."""
    bindings = []
    for name, tensor in checkpoint.tensors.items():
        if name == "lm_head.weight":
            continue
        found = None
        for kind in range(8):
            for layer in (range(24) if kind in range(1, 7) else (0,)):
                for projection in (range(3 if kind == 4 else 7)
                                   if kind in (1, 2, 3, 4) else (0,)):
                    if checkpoint.resolve(kind, layer, projection, 0, 0)[0] == name:
                        found = kind, layer, projection
        demand(found is not None, "unmapped checkpoint tensor " + name)
        kind, layer, projection = found
        key = (kind << 35) | (layer << 3) | projection
        shape = tensor["shape"]
        rows, cols = (shape if len(shape) == 2 else (1, shape[0]))
        bindings.append(f"""39'h{key:010x}: begin
 if(row>={rows} || col>={cols})
   $fatal(1,"UNCOVERED {name} coordinate row=%0d col=%0d",row,col);
 offset={checkpoint.base + tensor['start']}+({tensor['width']}*(64'd{cols}*row+col));
 width={tensor['width']};
end""")
    return """
integer checkpoint_fd;
initial begin
 checkpoint_fd=$fopen(""" + json.dumps(str(checkpoint.path)) + ""","rb");
 if(checkpoint_fd==0) $fatal(1,"checkpoint open failed");
end
function automatic [31:0] checkpoint_read(input [3:0] kind,
 input [31:0] layer,input [2:0] proj,input [31:0] row,col);
reg [63:0] offset;
integer width,status,byte_index,octet;
begin
 offset=0; width=0;
 case({kind,layer,proj})
""" + "\n".join(bindings) + """
 default: $fatal(1,"UNCOVERED model address kind=%0d layer=%0d proj=%0d row=%0d col=%0d",
                  kind,layer,proj,row,col);
 endcase
 status=$fseek(checkpoint_fd,offset,0);
 if(status!=0) $fatal(1,"checkpoint seek failure");
 checkpoint_read=0;
 for(byte_index=0;byte_index<width;byte_index=byte_index+1) begin
   octet=$fgetc(checkpoint_fd);
   if(octet<0) $fatal(1,"checkpoint truncated payload");
   checkpoint_read=checkpoint_read | (octet << (8*byte_index));
 end
end endfunction
"""


def raw_submatrix_test(run, checkpoint, command_tb, bus_connect, compile_sim):
    """All 14 supplied projections, first 64 inputs/outputs; not model inference.

    The scaled G64 engine only visits group zero, identical to official G128
    metadata for k=0..63. No missing values are filled or layers remapped.
    """
    activations = [((c * 67) % 509 - 254) * 256 for c in range(64)]
    expected, float_results, integer_results = [], [], []
    for layer in (0, 23):
        for projection in range(7):
            for col in range(64):
                total, products = 0, []
                for row, activation in enumerate(activations):
                    qw = checkpoint.bus(1, layer, projection, row, col // 8)
                    qz = checkpoint.bus(2, layer, projection, 0, col // 8)
                    delta = ((qw >> SHIFTS[col % 8]) & 15) - ((qz >> SHIFTS[col % 8]) & 15)
                    scale = checkpoint.bus(3, layer, projection, 0, col)
                    total += activation * delta * half_integer(scale, scale=True)
                    name, coordinate = checkpoint.resolve(3, layer, projection, 0, col)
                    products.append(f32(f32(activation / 65536) *
                                        f32(delta * checkpoint.half(name, coordinate))))
                floating = fp_sum(products)
                if projection < 3:
                    total += half_integer(checkpoint.bus(4, layer, projection, 0, col)) * 65536
                    name, coordinate = checkpoint.resolve(4, layer, projection, 0, col)
                    floating = f32(floating + checkpoint.half(name, coordinate))
                result = clip32(round_away(total, 65536))
                slot = (2, 3, 4, 6, 9, 10, 12)[projection]
                expected.append((slot, col, result & 0xffffffff))
                integer_results.append(result / 65536)
                float_results.append(floating)
    vector = run.out / "raw-official-submatrix-writes.hex"
    vector.write_text("".join(f"{slot:08x}{col:08x}{value:08x}\n"
                              for slot, col, value in expected))
    reader = checkpoint_reader(checkpoint) + f"""
reg [95:0] expected[0:{len(expected)-1}];
initial $readmemh("{vector}",expected);
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(kind==8) begin
   if(proj!=0 || col>=64 ||
      row!=(cmd_proj==3 ? 5 : (cmd_proj==6 ? 11 : (cmd_proj>=4 ? 8 : 1))))
     $fatal(1,"RAW SUBMATRIX activation address");
   read_memory=((col*67)%509-254)*256;
 end else begin
   if(kind<1 || kind>4 || proj!==cmd_proj ||
      (mem_req_layer!=0 && mem_req_layer!=23) ||
      row>=(kind==1 ? 64 : 1) || col>=(kind==1 || kind==2 ? 8 : 64))
     $fatal(1,"RAW SUBMATRIX model address");
   read_memory=checkpoint_read(kind,mem_req_layer,proj,row,col);
 end
end endfunction
"""
    check = f"""
if(writes>={len(expected)} || mem_req_kind!==8 || mem_req_proj!==0 ||
   {{mem_req_row,mem_req_col,mem_req_wdata}} !== expected[writes])
 $fatal(1,"RAW OFFICIAL SUBMATRIX write mismatch %0d",writes);
"""
    params = (".NUM_LAYERS(24),.HIDDEN_SIZE(64),.INTERMEDIATE_SIZE(64),"
              ".NUM_Q_HEADS(2),.NUM_KV_HEADS(2),.HEAD_DIM(32),"
              ".GROUP_SIZE(64),.MAX_SEQ_LEN(1)")
    instance = f"anvil_q1_w4a16_gemv #({params}) dut({bus_connect},.cmd_proj(cmd_proj));"
    commands = "\n".join(f"cmd_layer={layer}; launch({projection},0);"
                         for layer in (0, 23) for projection in range(7))
    commands += f"""
if(writes!={len(expected)} || completions!=14)
 $fatal(1,"RAW OFFICIAL SUBMATRIX incomplete commands");
"""
    tb = command_tb(instance, reader, check, commands).replace(
        'if(mem_req_layer!==0) $fatal(1,"unexpected layer");',
        "if(mem_req_layer!==(mem_req_kind==8 ? 32'd0 : cmd_layer)) "
        '$fatal(1,"literal official layer/unused scratch layer mismatch");')
    stdout = compile_sim(run, tb, "raw-official-submatrix", timeout=3600, settled=True)
    run.result("raw-official-submatrix", outcome="pass", scope="partial diagnostic only",
               layers=[0, 23], projections=list(PROJECTIONS),
               input_rows=[0, 64], output_channels=[0, 64],
               group_mapping="scaled G64 only visits original G128 group zero",
               padding="none", completed_commands=14, compared_writes=len(expected),
               bit_mismatches=0, compared_products=14 * 64 * 64,
               partial_projection_metrics=logit_metrics(integer_results, float_results),
               metrics_scope="projection components, NOT full-model vocabulary logits",
               stdout=stdout)


def official_top_coverage_test(run, checkpoint, command_tb, bus_connect, compile_sim):
    """Default top executes available embedding/norm, then rejects missing Q row.

    The uncovered read receives a real bus error, never a fabricated model value.
    This is an intentionally failed token, not complete official inference.
    """
    h = 896
    embedding = [half_integer(checkpoint.bus(0, 0, 0, 0, c)) for c in range(h)]
    denominator = math.isqrt((sum(v * v for v in embedding) << 32) // h + 18446744073710)
    demand(denominator > 0, "official input norm denominator")
    reciprocal = 2**64 // denominator
    normalized = [clip32(round_away(v * half_integer(checkpoint.bus(5, 0, 0, 0, c)) *
                                    reciprocal, 2**48)) for c, v in enumerate(embedding)]
    software = FP32Model(checkpoint)
    raw_embedding = [software.value(0, 0, 0, 0, c) for c in range(h)]
    float_norm = software.norm(raw_embedding, 5, 0)
    errors = [abs(v / 65536 - f) for v, f in zip(normalized, float_norm)]
    demand(all(error <= 2 / 256 for error in errors), "official isolated input norm quality")
    expected = [(slot, c, value & 0xffffffff)
                for slot, values in ((0, embedding), (1, normalized))
                for c, value in enumerate(values)]
    path = run.out / "official-top-covered-stages.hex"
    path.write_text("".join(f"{slot:08x}{c:08x}{v:08x}\n" for slot, c, v in expected))
    connect = bus_connect.replace(".cmd_valid(cmd_valid),.cmd_ready(cmd_ready)",
                                  ".token_valid(cmd_valid),.token_ready(cmd_ready)").replace(
        ".cmd_layer(cmd_layer),.cmd_pos(cmd_pos)", ".token_id(cmd_layer),.token_pos(cmd_pos)")
    instance = f"""
wire logit_valid; wire [31:0] logit_index; wire signed [31:0] logit_data;
integer uncovered_reads=0,logits=0;
anvil_q1_top dut({connect},.new_sequence(1'b1),.logit_ready(1'b1),
 .logit_valid(logit_valid),.logit_index(logit_index),.logit_data(logit_data));
always @(posedge clk) if(rst_n && logit_valid)
 $fatal(1,"UNEXPECTED logit from incomplete official token");
"""
    reader = checkpoint_reader(checkpoint) + f"""
reg [31:0] scratch[0:{2*h-1}];
reg [95:0] expected[0:{len(expected)-1}];
initial $readmemh("{path}",expected);
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(kind==8) begin
   if(proj!=0 || row>=2 || col>={h}) $fatal(1,"official covered scratch address");
   read_memory=scratch[row*{h}+col];
   if(^read_memory===1'bx) $fatal(1,"official covered scratch uninitialized");
 end else if(kind==1 && mem_req_layer==0 && proj==0 && row==64 && col==0) begin
   if(uncovered_reads!=0 || writes!={len(expected)})
     $fatal(1,"missing coverage error precondition");
   uncovered_reads=uncovered_reads+1; mem_rsp_error=1;
   $display("EXPECTED_COVERAGE_ERROR tensor=model.layers.0.self_attn.q_proj.qweight row=64 col=0");
   read_memory=0;
 end else begin
   if(uncovered_reads!=0 || kind>7) $fatal(1,"memory effects after uncovered read");
   read_memory=checkpoint_read(kind,mem_req_layer,proj,row,col);
 end
end endfunction
"""
    check = f"""
if(writes>={len(expected)} || mem_req_kind!==8 || mem_req_proj!==0 ||
 {{mem_req_row,mem_req_col,mem_req_wdata}} !== expected[writes])
 $fatal(1,"official covered top write mismatch %0d",writes);
scratch[mem_req_row*{h}+mem_req_col]=mem_req_wdata;
"""
    commands = f"""
launch(0,0);
if(writes!={len(expected)} || completions!=1 || uncovered_reads!=1)
 $fatal(1,"official covered top comparison/error coverage");
$fclose(checkpoint_fd);
"""
    tb = command_tb(instance, reader, check, commands).replace(
        'if(error !== 0 || pending) $fatal(1,"unexpected completion error/outstanding");',
        'if(error !== 1 || pending || uncovered_reads!=1) '
        '$fatal(1,"missing coverage did not fail official token");')
    stdout = compile_sim(run, tb, "official-top-coverage", timeout=3600, settled=True)
    run.result("official-top-coverage", outcome="intended_missing_coverage_rejection",
               scope="partial default-top embedding/input-norm; failed token, NOT official inference",
               configuration=list(DEFAULT_SHAPE), token_id=0, position=0,
               compared_writes=len(expected), bit_mismatches=0,
               covered_stages=["embedding", "layer0.input_layernorm"],
               isolated_norm_max_absolute_error=max(errors), isolated_norm_limit=2 / 256,
               successful_tokens=0, error_completions=1, compared_logits=0,
               uncovered_tensor="model.layers.0.self_attn.q_proj.qweight",
               uncovered_coordinate=[64, 0], response="acknowledged memory error",
               stdout=stdout)


def checkpoint_sensitivity(run, checkpoint):
    """Disposable malformed/provenance/coverage fixtures; authoritative bytes untouched."""
    fixtures = run.out / "checkpoint-fixtures"
    fixtures.mkdir()
    tests = []
    corrupt = bytearray(checkpoint.data)
    corrupt[-1] ^= 1
    tests.append(("payload-corruption", bytes(corrupt), "checkpoint SHA-256 mismatch", False))
    tests.extend([
        ("truncated-length", b"\0\0", "truncated length", True),
        ("header-out-of-bounds", struct.pack("<Q", 2**63), "invalid header length", True),
    ])

    def fixture(header, payload=b"\0\0"):
        raw = header.encode()
        raw += b" " * (-len(raw) % 8)
        return struct.pack("<Q", len(raw)) + raw + payload
    desc = '{"dtype":"F16","shape":[1],"data_offsets":[0,2]}'
    tests.extend([
        ("duplicate-tensor", fixture('{"x":' + desc + ',"x":' + desc + '}'),
         "duplicate JSON key", True),
        ("malformed-json", fixture('{"x":'), "malformed header", True),
        ("unsupported-dtype", fixture('{"x":{"dtype":"F32","shape":[1],"data_offsets":[0,2]}}'),
         "unsupported dtype", True),
        ("shape-length", fixture('{"x":{"dtype":"F16","shape":[2],"data_offsets":[0,2]}}'),
         "payload bounds/length", True),
        ("overlap", fixture('{"x":' + desc + ',"y":' + desc + '}'),
         "overlapping or noncontiguous", True),
        ("metadata", fixture('{"__metadata__":{"x":3},"x":' + desc + '}'),
         "metadata structure", True),
    ])
    for name, data, assertion, parser_only in tests:
        path = fixtures / (name + ".safetensors")
        path.write_bytes(data)
        try:
            if parser_only:
                parse_safetensors(data)
            else:
                Checkpoint(checkpoint.root, data=data)
        except CheckpointError as exc:
            demand(assertion in str(exc), f"wrong fixture assertion {name}: {exc}")
            diagnosis = str(exc)
        else:
            raise AssertionError("checkpoint fixture survived: " + name)
        run.result("checkpoint-mutation-" + name, outcome="intended_rejection",
                   original_sha256=checkpoint.sha256,
                   fixture_path=str(path.relative_to(checkpoint.root)),
                   fixture_sha256=hashlib.sha256(data).hexdigest(), assertion=diagnosis,
                   compilation="not applicable: checkpoint parser negative test")
    altered_manifest = json.loads(json.dumps(checkpoint.manifest))
    altered_manifest["extracted_safetensors_sha256"] = hashlib.sha256(corrupt).hexdigest()
    altered_path = fixtures / "tensor-digest.safetensors"
    altered_path.write_bytes(corrupt)
    altered_manifest_path = fixtures / "tensor-digest-manifest.json"
    altered_manifest_path.write_text(json.dumps(altered_manifest, indent=2) + "\n")
    try:
        Checkpoint(checkpoint.root, data=corrupt, manifest=altered_manifest)
    except CheckpointError as exc:
        demand("tensor SHA-256 mismatch" in str(exc), "tensor digest fixture wrong rejection")
        run.result("checkpoint-mutation-tensor-digest", outcome="intended_rejection",
                   assertion=str(exc), fixture_sha256=hashlib.sha256(corrupt).hexdigest(),
                   fixture_path=str(altered_path.relative_to(checkpoint.root)),
                   fixture_manifest_path=str(altered_manifest_path.relative_to(checkpoint.root)),
                   fixture_manifest_sha256=hashlib.sha256(altered_manifest_path.read_bytes()).hexdigest(),
                   original_sha256=checkpoint.sha256)
    else:
        raise AssertionError("tensor digest mutation survived independently rehashed envelope")
    try:
        checkpoint.bus(1, 0, 0, 64, 0)
    except CoverageError as exc:
        demand("model.layers.0.self_attn.q_proj.qweight" in str(exc) and "(64, 0)" in str(exc),
               "coverage rejection missing tensor/coordinate")
        run.result("checkpoint-mutation-missing-coverage", outcome="intended_rejection",
                   assertion=str(exc), source_sha256=checkpoint.sha256,
                   compilation="not applicable: uncovered checkpoint coordinate")
    else:
        raise AssertionError("missing checkpoint row was silently supplied")


def model_selftests(run):
    """Analytical raw-format fixtures, independent from official-data acceptance."""
    demand(struct.pack("<f", f32(1 + 2**-24)) == struct.pack("<f", 1.0),
           "FP32 ties-even rounding")
    demand(f32(1 + 2**-23) != 1, "FP32 next representable rounding")
    demand(half_integer(0x0001) == 0 and half_integer(0x0080) == 1 and
           half_integer(0x8080) == -1 and half_integer(0x8000) == 0,
           "binary16 subnormal/ties/signed zero")
    demand(half_integer(0x7bff, scale=True) == 4292870144, "unsaturated scale")
    demand(logit_metrics([0.0] * 5, [0.0] * 5)["cosine_similarity"] is None,
           "zero-norm cosine must be undefined")
    demand(logit_metrics([1.0] * 6, [1.0] * 6)["hardware_top5"] == list(range(5)),
           "deterministic ranking tie")

    class AnalyticCheckpoint:
        """Not official: nontrivial exactly representable small algebra fixture."""
        resolve = staticmethod(Checkpoint.resolve)
        def bus(self, kind, layer, projection, row, col):
            if kind in (1, 2):
                values = ([7 + ((row + lane + projection) % 3) for lane in range(8)]
                          if kind == 1 else [8] * 8)
                return sum(value << shift for value, shift in zip(values, SHIFTS))
            value = (1 / 64 if kind == 3 else
                     (col - 3) / 64 if kind == 4 else
                     1.0 if kind in (5, 6, 7) else ((row + col) % 7 - 3) / 16)
            return struct.unpack("<H", struct.pack("<e", value))[0]
        def half(self, name, coordinate):
            if name == "model.embed_tokens.weight":
                return ((coordinate[0] + coordinate[1]) % 7 - 3) / 16
            if name.endswith("scales"):
                return 1 / 64
            if name.endswith("bias"):
                return (coordinate[0] - 3) / 64
            return 1.0
    shape = (2, 8, 8, 2, 1, 4, 8, 8, 4)
    floating, integer = FP32Model(AnalyticCheckpoint(), shape), FixedModel(AnalyticCheckpoint(), shape)
    max_error = 0
    for position in range(4):
        expected = floating.token(position, position, position == 0)
        actual = integer.token(position, position, position == 0)
        demand(len(expected) == len(actual) == 8 and len(integer.writes) > 0,
               "fixture stage/logit denominator")
        max_error = max(max_error, max(abs(a / 65536 - b) for a, b in zip(actual, expected)))
        demand(max_error <= 16 / 256, "analytic fixture integer/FP32 quality")
    # Different data paths must retain raw F16 sub-LSB values in software.
    class SubLSBCheckpoint(AnalyticCheckpoint):
        def half(self, name, coordinate):
            return 2**-24 if name == "model.embed_tokens.weight" else super().half(name, coordinate)
    model = FP32Model(SubLSBCheckpoint(), shape)
    demand(model.value(0, 0, 0, 0, 0) == 2**-24 and half_integer(1) == 0,
           "software baseline incorrectly quantizes original F16")
    run.result("official-model-analytical-fixtures", outcome="pass",
               scope="synthetic mathematical self-tests, not official model inference",
               tokens=4, fp32_sub_lsb_retained=True, max_absolute_error=max_error)


def rtl_forward(run, checkpoint, sequence, writes, expected_logits,
                command_tb, bus_connect, compile_sim, shape=DEFAULT_SHAPE,
                name="official-full-model"):
    """Execute top public pins; model reads come directly from safetensors bytes."""
    layers, h, intermediate, _, kvheads, d, _, vocab, _ = shape
    count, kv = len(sequence), kvheads * d
    write_file, logit_file = run.out / (name + "-writes.hex"), run.out / (name + "-logits.hex")
    write_file.write_text("".join(f"{kind:x}{layer:08x}{row:08x}{col:08x}{value:08x}\n"
                                 for kind, layer, row, col, value in writes))
    logit_file.write_text("".join(f"{value & 0xffffffff:08x}\n" for value in expected_logits))
    connect = bus_connect.replace(".cmd_valid(cmd_valid),.cmd_ready(cmd_ready)",
                                  ".token_valid(cmd_valid),.token_ready(cmd_ready)").replace(
        ".cmd_layer(cmd_layer),.cmd_pos(cmd_pos)", ".token_id(cmd_layer),.token_pos(cmd_pos)")
    bins = count * 12 * 2 * layers * 8
    keys = ("NUM_LAYERS", "HIDDEN_SIZE", "INTERMEDIATE_SIZE", "NUM_Q_HEADS",
            "NUM_KV_HEADS", "HEAD_DIM", "GROUP_SIZE", "VOCAB_SIZE", "MAX_SEQ_LEN")
    params = ",".join(f".{key}({value})" for key, value in zip(keys, shape))
    instance = f"""
reg new_sequence=0,logit_ready=0;
wire logit_valid; wire [31:0] logit_index; wire signed [31:0] logit_data;
anvil_q1_top #({params}) dut({connect},.new_sequence(new_sequence),
 .logit_valid(logit_valid),.logit_ready(logit_ready),
 .logit_index(logit_index),.logit_data(logit_data));
integer observed_logits=0, accepted_tokens=0,final_transfers=0;
integer active_token=-1;
longint unsigned start_edge=0,final_edge=0;
integer logit_stalls=0,response_stalls=0,request_stalls=0;
integer bin_index=0,pending_bin=0,index_init=0,print_index=0;
integer requests_by_address[0:{bins-1}],responses_by_address[0:{bins-1}];
reg [31:0] expected_logits[0:{len(expected_logits)-1}];
reg logit_held=0; reg [63:0] logit_payload;
initial begin
 $readmemh("{logit_file}",expected_logits);
 for(index_init=0;index_init<{bins};index_init=index_init+1) begin
   requests_by_address[index_init]=0; responses_by_address[index_init]=0;
 end
end
always @(negedge clk) logit_ready=rst_n && cycles%5!=0;
function automatic integer counter_bin(input integer token,kind,write_access,layer,proj);
begin counter_bin=((((token*12+kind)*2+write_access)*{layers}+layer)*8+proj); end
endfunction
"""
    reader = checkpoint_reader(checkpoint) + f"""
reg [31:0] scratch[0:{15*intermediate-1}];
reg [31:0] kcache[0:{layers*count*kv-1}],vcache[0:{layers*count*kv-1}];
reg [131:0] expected_writes[0:{len(writes)-1}];
reg [31:0] rope_values[0:{count*d-1}];
integer cache_init;
initial begin
 $readmemh("{write_file}",expected_writes);
 for(cache_init=0;cache_init<{layers*count*kv};cache_init=cache_init+1) begin
   kcache[cache_init]=32'h70000000; vcache[cache_init]=32'h71000000;
 end
"""
    for pos in range(count):
        for pair in range(d // 2):
            for bit, value in enumerate(rope_words(pos, pair, d)):
                reader += f" rope_values[{pos*d+2*pair+bit}]=32'h{value & 0xffffffff:08x};\n"
    reader += f"""
end
task automatic validate_address(input [3:0] kind,input [31:0] layer,
 input [2:0] proj,input [31:0] row,col);
integer limit;
begin
 if(kind>11 || layer>={layers}) $fatal(1,"OFFICIAL kind/layer address");
 if(kind==8) begin
   limit=(row==3 || row==4 ? {kv} : (row>=9 && row<=11 ? {intermediate} : {h}));
   if(layer!=0 || proj!=0 || row>=15 || row==13 || col>=limit)
     $fatal(1,"OFFICIAL scratch address");
 end
 if(kind==9 || kind==10) begin
   if(proj!=0 || row>cmd_pos || row>={count} || col>={kv})
     $fatal(1,"OFFICIAL CAUSAL cache address");
 end
 if(kind==11 && (layer!=0 || proj!=0 || row>={count} || col>={d}))
   $fatal(1,"OFFICIAL RoPE address");
end endtask
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(kind<=7) read_memory=checkpoint_read(kind,mem_req_layer,proj,row,col);
 else if(kind==8) read_memory=scratch[row*{intermediate}+col];
 else if(kind==9) read_memory=kcache[(mem_req_layer*{count}+row)*{kv}+col];
 else if(kind==10) read_memory=vcache[(mem_req_layer*{count}+row)*{kv}+col];
 else if(kind==11) read_memory=rope_values[row*{d}+col];
 else begin $fatal(1,"OFFICIAL invalid read kind"); read_memory=0; end
 if(^read_memory===1'bx) $fatal(1,"OFFICIAL active unknown memory data");
end endfunction
"""
    check = f"""
if(writes>={len(writes)} || mem_req_proj!==0 ||
 {{mem_req_kind,mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata}} !== expected_writes[writes])
 $fatal(1,"OFFICIAL STACK ordered write mismatch %0d",writes);
if(mem_req_kind==8) scratch[mem_req_row*{intermediate}+mem_req_col]=mem_req_wdata;
else if(mem_req_kind==9)
 kcache[(mem_req_layer*{count}+mem_req_row)*{kv}+mem_req_col]=mem_req_wdata;
else if(mem_req_kind==10)
 vcache[(mem_req_layer*{count}+mem_req_row)*{kv}+mem_req_col]=mem_req_wdata;
else $fatal(1,"OFFICIAL forbidden model write");
"""
    commands = "\n".join(f"cmd_layer={item['token_id']};new_sequence={int(item['position']==0)};"
                         f"launch(0,{item['position']});" for item in sequence)
    commands += f"""
if(accepted_tokens!={count} || completions!={count} || final_transfers!={count} ||
 observed_logits!={len(expected_logits)} || writes!={len(writes)})
 $fatal(1,"OFFICIAL incomplete tokens or comparisons");
for(print_index=0;print_index<{bins};print_index=print_index+1)
 if(requests_by_address[print_index]!=0) begin
   if(requests_by_address[print_index]!=responses_by_address[print_index])
     $fatal(1,"OFFICIAL unacknowledged memory operation");
   $display("OFFICIAL_MEM bin=%0d requests=%0d responses=%0d",
     print_index,requests_by_address[print_index],responses_by_address[print_index]);
 end
$display("OFFICIAL_COUNTS writes=%0d logits=%0d completed=%0d",writes,observed_logits,completions);
$fclose(checkpoint_fd);
"""
    tb = command_tb(instance, reader, check, commands)
    tb = tb.replace("integer cycles=0, writes=0, accepted=0, pending=0, delay_count=0;",
                    "longint unsigned cycles=0;\n"
                    "integer writes=0, accepted=0, pending=0, delay_count=0;")
    tb = tb.replace('if(cycles>120000000) $fatal(1,"WATCHDOG");', f"""
if(^{{logit_valid,logit_index,logit_data}}===1'bx)
 $fatal(1,"OFFICIAL active unknown logit");
if(cmd_valid && cmd_ready) begin
 active_token=accepted_tokens; accepted_tokens=accepted_tokens+1;
 start_edge=cycles; logit_stalls=0; request_stalls=0; response_stalls=0;
 $display("OFFICIAL_ACCEPT token=%0d edge=%0d",active_token,cycles);
end
if(logit_held && {{logit_valid,logit_index,logit_data}} !== {{1'b1,logit_payload}})
 $fatal(1,"OFFICIAL stalled logit changed");
logit_held=logit_valid && !logit_ready;
logit_payload={{logit_index,logit_data}};
if(logit_held) logit_stalls=logit_stalls+1;
if(mem_req_valid && !mem_req_ready) request_stalls=request_stalls+1;
if(mem_rsp_valid && !mem_rsp_ready) response_stalls=response_stalls+1;
if(logit_valid && logit_ready) begin
 if(observed_logits>={len(expected_logits)} || logit_index!==observed_logits%{vocab} ||
    logit_data!==expected_logits[observed_logits])
   $fatal(1,"OFFICIAL LOGIT mismatch %0d",observed_logits);
 $display("OFFICIAL_LOGIT token=%0d index=%0d value=%0d",active_token,logit_index,logit_data);
 observed_logits=observed_logits+1;
 if(logit_index=={vocab-1}) begin
   final_edge=cycles; final_transfers=final_transfers+1;
   $display("OFFICIAL_FINAL token=%0d edge=%0d latency=%0d",
      active_token,cycles,cycles-start_edge);
 end
end
""")
    tb = tb.replace('if(mem_req_layer!==0) $fatal(1,"unexpected layer");', """
validate_address(mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col);
if(!mem_req_write && mem_req_wdata!==0) $fatal(1,"OFFICIAL nonzero read wdata");
if(mem_req_write && (mem_req_kind<8 || mem_req_kind>10))
 $fatal(1,"OFFICIAL forbidden write");
bin_index=counter_bin(active_token,mem_req_kind,mem_req_write,mem_req_layer,mem_req_proj);
requests_by_address[bin_index]=requests_by_address[bin_index]+1;
pending_bin=bin_index;
""")
    tb = tb.replace("pending=0; responses=responses+1;", """
pending=0; responses=responses+1;
responses_by_address[pending_bin]=responses_by_address[pending_bin]+1;
""")
    tb = tb.replace("completions=completions+1;", """
if(final_transfers!=completions+1 || cycles!=final_edge+1 || cmd_ready!==0)
 $fatal(1,"OFFICIAL completion/retirement contract");
$display("OFFICIAL_RETIRE token=%0d edge=%0d latency=%0d request_stalls=%0d response_stalls=%0d logit_stalls=%0d",
 active_token,cycles,cycles-start_edge,request_stalls,response_stalls,logit_stalls);
completions=completions+1;
""")
    tb = tb.replace("if(cmd_ready !== 0 || done !== 0 || error !== 0 ||", """
if(logit_valid!==0 || logit_index!==0 || logit_data!==0)
 $fatal(1,"OFFICIAL reset logit leakage");
if(cmd_ready !== 0 || done !== 0 || error !== 0 ||""")
    stdout = compile_sim(run, tb, name, timeout=3600, settled=True)
    return stdout


def full_path_fixture(run, root, command_tb, bus_connect, compile_sim):
    """Exercise the new file-backed top transactor on explicitly synthetic data."""
    fixture = {}
    def half(value):
        return struct.pack("<e", value)
    fixture["model.embed_tokens.weight"] = (
        "F16", [8, 8], b"".join(half(((r + c) % 7 - 3) / 16) for r in range(8) for c in range(8)))
    fixture["model.norm.weight"] = "F16", [8], half(1) * 8
    for layer in range(2):
        for norm in ("input_layernorm", "post_attention_layernorm"):
            fixture[f"model.layers.{layer}.{norm}.weight"] = "F16", [8], half(1) * 8
        for p, projection in enumerate(PROJECTIONS):
            prefix = f"model.layers.{layer}.{projection}."
            words = [sum((7 + ((r + lane + p + layer) % 3)) << shift
                         for lane, shift in enumerate(SHIFTS)) for r in range(8)]
            zero = sum(8 << shift for shift in SHIFTS)
            fixture[prefix + "qweight"] = "I32", [8, 1], b"".join(struct.pack("<I", w) for w in words)
            fixture[prefix + "qzeros"] = "I32", [1, 1], struct.pack("<I", zero)
            fixture[prefix + "scales"] = "F16", [1, 8], half(1 / 64) * 8
            if p < 3:
                fixture[prefix + "bias"] = (
                    "F16", [8], b"".join(half((c - 3 + layer) / 64) for c in range(8)))
    header, payload = {}, bytearray()
    for tensor, (dtype, shape, data) in fixture.items():
        header[tensor] = dict(dtype=dtype, shape=shape,
                              data_offsets=[len(payload), len(payload) + len(data)])
        payload.extend(data)
    encoded = json.dumps(header, separators=(",", ":")).encode()
    encoded += b" " * (-len(encoded) % 8)
    data = struct.pack("<Q", len(encoded)) + encoded + payload
    path = run.out / "SYNTHETIC-NOT-OFFICIAL-path-fixture.safetensors"
    path.write_bytes(data)
    checkpoint = Checkpoint.__new__(Checkpoint)
    checkpoint.root, checkpoint.path, checkpoint.data = root, path, data
    checkpoint.base, checkpoint.tensors = parse_safetensors(data)
    shape = (2, 8, 8, 2, 2, 4, 8, 8, 4)
    floating, integer = FP32Model(checkpoint, shape), FixedModel(checkpoint, shape)
    sequence, writes, logits, metrics = [], [], [], []
    next_token = 0
    for position in range(4):
        token = position if position < 2 else next_token
        sequence.append(dict(token_id=token, position=position))
        software = floating.token(token, position, position == 0)
        hardware = integer.token(token, position, position == 0)
        next_token = max(range(8), key=lambda i: (software[i], -i))
        writes.extend(integer.writes)
        logits.extend(hardware)
        metrics.append(logit_metrics([v / 65536 for v in hardware], software))
        demand(all(abs(a / 65536 - b) <= 16 / 256 + .01 * abs(b)
                   for a, b in zip(hardware, software)), "synthetic path fixture quality")
    stdout = rtl_forward(run, checkpoint, sequence, writes, logits,
                         command_tb, bus_connect, compile_sim, shape=shape,
                         name="synthetic-file-backed-top")
    demand(f"OFFICIAL_COUNTS writes={len(writes)} logits=32 completed=4" in stdout,
           "synthetic full path completed comparisons")
    run.result("synthetic-file-backed-top", outcome="pass",
               scope="synthetic transactor/oracle diagnostic, NOT official inference",
               fixture_path=str(path.relative_to(root)),
               fixture_sha256=hashlib.sha256(data).hexdigest(), configuration=list(shape),
               sequence=sequence, compared_writes=len(writes), compared_logits=32,
               completed_tokens=4, bit_mismatches=0, prediction_metrics=metrics,
               stdout=stdout)


def evaluate_official(run, checkpoint, report, command_tb, bus_connect, compile_sim):
    """No full-model arithmetic or RTL run starts until complete coverage exists."""
    checkpoint.require_complete()
    floating, integer = FP32Model(checkpoint), FixedModel(checkpoint)
    writes, flat_logits, software_logits, stage_records, saturation = [], [], [], [], []
    saturated_logits = []
    sequence = []
    next_token = 0
    for position in range(4):
        token = position if position < 2 else next_token
        item = dict(token_id=token, position=position,
                    role="prefill" if position < 2 else "decode",
                    selection="deterministic token ID" if position < 2 else
                              "previous official software argmax, lowest-index ties")
        sequence.append(item)
        reference = floating.token(token, position, position == 0)
        actual = integer.token(token, position, position == 0)
        next_token = max(range(len(reference)), key=lambda i: (reference[i], -i))
        flat_logits.extend(actual)
        software_logits.append(reference)
        writes.extend(integer.writes)
        saturated_logits.append(integer.saturated_coordinates.get((-1, "logits"), set()))
        for (layer, stage), values in integer.trace.items():
            ref = floating.trace[layer, stage]
            clipped = integer.saturation.get((layer, stage), 0)
            errors = [abs(a / 65536 - b) for a, b in zip(values, ref)]
            limit = 16 / 256
            nonsaturating_errors = [error for i, error in enumerate(errors)
                                    if i not in integer.saturated_coordinates.get((layer, stage), set())]
            isolated = stage in ("norm_input", "norm_post", "q_rope", "k_rope", "silu", "context")
            # End-to-end stage diagnostics are not isolated-unit limits.
            stage_records.append(dict(token_ordinal=position, layer=layer, stage=stage,
                                      compared_elements=len(values),
                                      max_absolute_error=max(errors), saturation_count=clipped,
                                      nonsaturating_final_limit=limit if stage == "final" else None,
                                      nonsaturating_compared_elements=len(nonsaturating_errors),
                                      quality=(all(e <= limit for e in nonsaturating_errors)
                                               if stage == "final"
                                               else None),
                                      isolated_unit_stage=isolated,
                                      observation=("oracle-only SiLU intermediate" if stage == "silu"
                                                   else "integer oracle, requires ordered RTL write proof")))
        saturation.extend(dict(token_ordinal=position, layer=layer, stage=stage, count=count)
                          for (layer, stage), count in integer.saturation.items())
    report.update(sequence=sequence, intermediate_diagnostics=stage_records,
                  saturation=saturation)
    write_comparison(run, report)
    stdout = rtl_forward(run, checkpoint, sequence, writes, flat_logits,
                         command_tb, bus_connect, compile_sim)
    import re
    observed = [[] for _ in sequence]
    for token, index, value in re.findall(r"OFFICIAL_LOGIT token=(\d+) index=(\d+) value=(-?\d+)", stdout):
        token, index, value = int(token), int(index), int(value)
        demand(token < len(observed) and index == len(observed[token]), "ordered RTL logit record")
        observed[token].append(value)
    counts = re.findall(r"OFFICIAL_COUNTS writes=(\d+) logits=(\d+) completed=(\d+)", stdout)
    demand(len(counts) == 1 and tuple(map(int, counts[0])) ==
           (len(writes), len(flat_logits), len(sequence)), "RTL completed comparison denominator")
    demand(all(len(values) == 151936 for values in observed), "full vocabulary RTL logit denominator")
    demand(list(itertools.chain.from_iterable(observed)) == flat_logits,
           "retained RTL transcript/logit mismatch")
    timings = {}
    for token, edge in re.findall(r"OFFICIAL_ACCEPT token=(\d+) edge=(\d+)", stdout):
        timings[int(token)] = dict(accept_edge=int(edge))
    for token, edge, latency in re.findall(
            r"OFFICIAL_FINAL token=(\d+) edge=(\d+) latency=(\d+)", stdout):
        timings[int(token)].update(final_logit_edge=int(edge), cycles=int(latency))
    for token, edge, latency, req, rsp, logit in re.findall(
            r"OFFICIAL_RETIRE token=(\d+) edge=(\d+) latency=(\d+) "
            r"request_stalls=(\d+) response_stalls=(\d+) logit_stalls=(\d+)", stdout):
        timings[int(token)].update(retirement_edge=int(edge), retirement_latency=int(latency),
                                  request_stalls=int(req), response_stalls=int(rsp),
                                  logit_stalls=int(logit))
    demand(set(timings) == set(range(4)) and
           all("retirement_edge" in t and "cycles" in t for t in timings.values()),
           "RTL timing denominator")
    transactions = []
    for index, requests, responses in re.findall(
            r"OFFICIAL_MEM bin=(\d+) requests=(\d+) responses=(\d+)", stdout):
        index, requests, responses = int(index), int(requests), int(responses)
        projection = index % 8
        index //= 8
        layer = index % 24
        index //= 24
        write_access = index % 2
        index //= 2
        kind, ordinal = index % 12, index // 12
        demand(requests == responses and ordinal < 4, "memory request/acknowledgement denominator")
        transactions.append(dict(token_ordinal=ordinal, kind=kind,
                                 access="write" if write_access else "read", layer=layer,
                                 projection=projection, accepted_requests=requests,
                                 accepted_responses=responses))
    demand(bool(transactions), "empty official memory transaction counts")
    per_token = []
    violations = []
    for ordinal, (actual, reference) in enumerate(zip(observed, software_logits)):
        values = [value / 65536 for value in actual]
        metric = logit_metrics(values, reference)
        greedy = max(range(len(actual)), key=lambda i: (actual[i], -i))
        software_greedy = max(range(len(reference)), key=lambda i: (reference[i], -i))
        for index, (raw, a, b) in enumerate(zip(actual, values, reference)):
            if index not in saturated_logits[ordinal] and abs(a - b) > 16 / 256 + .01 * abs(b):
                violations.append(dict(token_ordinal=ordinal, index=index, actual=a, reference=b,
                                       absolute_error=abs(a - b), limit=16 / 256 + .01 * abs(b)))
        per_token.append(dict(sequence[ordinal], metrics=metric,
                              autonomous_rtl_greedy_index=greedy,
                              software_greedy_index=software_greedy,
                              autonomous_rtl_greedy_agreement=greedy == software_greedy,
                              greedy_agreement_context="one-step RTL argmax at shared software-selected "
                                                       "prefix; not a separately executed autonomous rollout",
                              timing=timings[ordinal]))
    report.update(status="executed", completed_tokens=4,
                  bit_comparison=dict(mismatches=0, compared_writes=len(writes),
                                      compared_logits=len(flat_logits), reason=None),
                  per_token=per_token,
                  aggregate_metrics=dict(
                      reduction="all-token concatenated logits; rankings averaged per token",
                      **{key: value for key, value in logit_metrics(
                          [v / 65536 for row in observed for v in row],
                          list(itertools.chain.from_iterable(software_logits))).items()
                         if key not in ("top1_agreement", "top5_overlap_fraction",
                                        "exact_top5_set_agreement", "hardware_top5", "software_top5")},
                      top1_agreement=sum(p["metrics"]["top1_agreement"] for p in per_token) / 4,
                      top5_overlap_fraction=sum(p["metrics"]["top5_overlap_fraction"] for p in per_token) / 4,
                      exact_top5_set_agreement=sum(p["metrics"]["exact_top5_set_agreement"]
                                                  for p in per_token) / 4),
                  cycle_measurements=dict(
                      convention="elapsed rising edge intervals F-A; retirement T-A separately",
                      timing="observed deterministic request/response/logit stalls, not no-stall baseline",
                      cycles_token=sum(t["cycles"] for t in timings.values()) / 4,
                      total_cycles=sum(t["cycles"] for t in timings.values()),
                      per_token=[dict(token_ordinal=n, **timings[n]) for n in range(4)]),
                  memory_transactions=transactions, metrics_unavailable_reason=None,
                  numerical_violations=violations)
    quality = not violations and all(r["quality"] is not False for r in stage_records)
    report["status"] = "pass" if quality else "fail"
    report["blockers"] = [] if quality else ["retained numerical tolerance exceeded"]
    write_comparison(run, report)
    demand(quality, "official full-model numerical tolerance exceeded")
    run.result("official-full-model", outcome="pass", completed_tokens=4,
               compared_writes=len(writes), compared_logits=len(flat_logits), bit_mismatches=0)
