"""Exact/rational and Decimal controls for the NumPy official-model reference."""

from collections import Counter
from decimal import Decimal, localcontext
import hashlib
import json
import random
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import (BF16, FP16, FP32, add, convert, decode, dequant, dot,
                       decimal_value, encode_ratio, kv_encode, multiply, transcendental)
import official_reference as candidate


def word(value):
    return int(candidate.bits32(value))


def scalar(bits):
    return np.asarray(bits, dtype="<u4").view("<f4")


def require_same(actual, expected, label):
    actual = np.asarray(actual).ravel()
    expected = np.asarray(expected).ravel()
    if actual.shape != expected.shape:
        raise AssertionError(f"{label}: shape {actual.shape} != {expected.shape}")
    wrong = np.flatnonzero(actual != expected)
    if wrong.size:
        i = int(wrong[0])
        raise AssertionError(f"{label}[{i}]: {int(actual[i]):x} != {int(expected[i]):x}")
    return int(actual.size)


def exact_statistic(values):
    partials = []
    for value in values:
        level, current = 0, int(value)
        while level < len(partials) and partials[level] is not None:
            current, error = add(partials[level], current)
            if error:
                raise ArithmeticError("nonfinite exact statistic")
            partials[level] = None
            level += 1
        if level == len(partials):
            partials.append(current)
        else:
            partials[level] = current
    result = 0
    for partial in partials:
        if partial is not None:
            result, error = add(result, partial)
            if error:
                raise ArithmeticError("nonfinite exact statistic fold")
    return result


def decimal_round(value, fmt=FP32):
    numerator, denominator = abs(value).as_integer_ratio()
    result, error = encode_ratio(value.is_signed(), numerator, denominator, 0, fmt)
    if error:
        raise ArithmeticError("oracle overflow")
    return result


def decimal_trig(value):
    with localcontext() as context:
        context.prec = 100
        pi = Decimal("3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825342117068")
        x = value % (2*pi)
        if x > pi:
            x -= 2*pi
        cosine, sine, cterm, sterm = Decimal(1), x, Decimal(1), x
        for index in range(1, 200):
            cterm *= -x*x / ((2*index-1)*(2*index))
            sterm *= -x*x / ((2*index)*(2*index+1))
            cosine += cterm
            sine += sterm
            if max(abs(cterm), abs(sterm)) < Decimal("1e-95"):
                return cosine, sine
        raise ArithmeticError("Decimal trigonometric series did not converge")


def exact_projection(activation, weights, half=False, quantized=False, bias=0):
    af, wf = (FP16 if half else BF16), (BF16 if quantized else FP16 if half else BF16)
    a = [int(x) for x in candidate.narrow(activation, half)]
    w = [int(x) for x in candidate.narrow(weights, wf == FP16)]
    accumulator = None
    for start in range(0, len(a), 128):
        count = min(128, len(a)-start)
        result, error = dot(a[start:start+count]+[0]*(128-count),
                            w[start:start+count]+[0]*(128-count),
                            [True]*count+[False]*(128-count), af, wf)
        if error:
            raise ArithmeticError("oracle dot overflow")
        if accumulator is None:
            accumulator = result
        else:
            accumulator, error = add(accumulator, result)
            if error:
                raise ArithmeticError("oracle tile accumulator overflow")
    result, error = add(accumulator, bias)
    if error:
        raise ArithmeticError("oracle projection bias overflow")
    return result


class Audit:
    """Samples real official operands, not synthetic expected result tables."""

    def __init__(self):
        self.counts = Counter()
        self.max_relative_error = 0.0
        self.max_absolute_error_near_zero = 0.0
        self.rope_positions = set()

    def projection(self, activation, weights, result, half, quantized, bias, name):
        row = int(hashlib.sha256(name.encode()).hexdigest()[:8], 16) % weights.shape[0]
        expected = exact_projection(activation, weights[row], half, quantized,
                                    0 if bias is None else word(bias[row]))
        self.counts["official_projection_rows"] += require_same(
            word(result[row]), expected, "official exact projection "+name)
        self.counts["official_projection_products"] += int(activation.size)

    def normalizer(self, x, actual, epsilon):
        products = [multiply(int(v), int(v))[0] for v in candidate.bits32(x)]
        total = exact_statistic(products)
        count = encode_ratio(False, 1, len(products), 0, FP32)[0]
        mean = multiply(total, count)[0]
        argument = add(mean, word(np.float32(epsilon)))[0]
        expected = transcendental(3, argument)
        self.approximation(float(actual), expected, "official rsqrt")
        self.counts["official_norm_products"] += len(products)
        self.counts["official_normalizers"] += 1

    def rope(self, position, theta, dimension, cosine, sine, half):
        key = (position, theta, dimension, half)
        if key in self.rope_positions:
            return
        with localcontext() as context:
            context.prec = 100
            for pair in range(dimension//2):
                angle = Decimal(position) * (
                    -Decimal(2*pair)/dimension * Decimal(str(theta)).ln()).exp()
                c, s = decimal_trig(angle)
                for actual, expected in ((cosine[pair], c), (sine[pair], s)):
                    fp32 = decimal_round(expected)
                    native = convert(fp32, FP32, FP16 if half else BF16)[0]
                    self.counts["rope_coefficients"] += require_same(
                        candidate.narrow(actual, half), native, "checkpoint RoPE coefficient")
        self.rope_positions.add(key)

    def approximation(self, actual, expected, label):
        with localcontext() as context:
            context.prec = 100
            error = abs(Decimal.from_float(actual)-expected)
            if abs(expected) <= Decimal("0.01"):
                self.max_absolute_error_near_zero = max(
                    self.max_absolute_error_near_zero, float(error))
                if error > Decimal("0.0000002"):
                    raise AssertionError(label+" absolute error")
            else:
                relative = error/abs(expected)
                self.max_relative_error = max(self.max_relative_error, float(relative))
                if relative > Decimal("0.00002"):
                    raise AssertionError(label+" relative error")
        self.counts["high_precision_comparisons"] += 1

    def nonlinear(self, operation, x, y):
        for index in sorted({0, len(x)//2, len(x)-1}):
            self.approximation(float(y[index]), transcendental(operation, word(x[index])),
                               "official nonlinear")
        self.counts["official_nonlinear_samples"] += len({0, len(x)//2, len(x)-1})

    def cache(self, values, int8, record, reconstructed):
        encoded, decoded, error = kv_encode(
            [convert(word(v), FP32, BF16)[0] for v in values], int8)
        if error:
            raise ArithmeticError("oracle KV overflow")
        expected = encoded.to_bytes(2+len(values) if int8 else 2*len(values), "little")
        if record != expected:
            raise AssertionError("official exact KV encoded bytes")
        self.counts["official_kv_values"] += require_same(
            candidate.narrow(reconstructed), decoded, "official exact KV reconstruction")
        self.counts["official_kv_bytes"] += len(record)

    def summary(self):
        return {"comparison_counts": dict(self.counts),
                "max_relative_error": self.max_relative_error,
                "max_absolute_error_near_zero": self.max_absolute_error_near_zero}


def execute():
    rng = random.Random(211)
    counts = Counter()
    with np.errstate(over="ignore", invalid="ignore"):
        for half, fmt in ((False, BF16), (True, FP16)):
            encodings = np.arange(65536, dtype="<u2")
            expected = [convert(i, fmt, FP32)[0] for i in range(65536)]
            actual = candidate.bits32(candidate.expand(encodings, half)).copy()
            actual[np.isnan(candidate.expand(encodings, half))] = FP32.nan
            counts["exhaustive_expansion"] += require_same(actual, expected, "expand")
            expected = [convert(i, fmt, fmt)[0] for i in range(65536)]
            counts["exhaustive_native_conversion"] += require_same(
                candidate.narrow(candidate.expand(encodings, half), half), expected, "native")
            sources = [rng.getrandbits(32) for _ in range(10000)]
            sources += [0, FP32.sign, 1, FP32.sign | 1, 0x7f7fffff,
                        FP32.infinity, FP32.nan, 0xff800000]
            for value in range(fmt.infinity):
                sign, m, p, _ = decode(value, fmt)
                if value == fmt.infinity-1:
                    n, q = m+1, p
                else:
                    _, n, q, _ = decode(value+1, fmt)
                low = min(p, q)
                middle = encode_ratio(False, (m << (p-low))+(n << (q-low)),
                                      2, low, FP32)[0]
                sources.extend((middle, middle+1, max(0, middle-1)))
            expected = [convert(i, FP32, fmt)[0] for i in sources]
            counts["narrow_midpoints_and_random"] += require_same(
                candidate.narrow(scalar(sources), half), expected, "narrow")
            pairs = [(rng.randrange(65536), rng.randrange(65536)) for _ in range(10000)]
            a, b = zip(*pairs)
            actual = candidate.times(candidate.expand(a, half), candidate.expand(b, half))
            counts["native_products"] += require_same(
                candidate.bits32(actual), [multiply(x, y, fmt, fmt)[0] for x, y in pairs],
                "native products")
        pairs = [(rng.getrandbits(32), rng.getrandbits(32)) for _ in range(10000)]
        pairs += [(0x80000000, 0x80000000), (1, 0x80000001),
                  (0x7f800000, 0xff800000), (0x3f800000, 0xbf800000)]
        a, b = zip(*pairs)
        for function, oracle, name in ((candidate.plus, add, "fp32_add"),
                                       (candidate.times, multiply, "fp32_product")):
            counts[name] += require_same(
                candidate.bits32(function(scalar(a), scalar(b))),
                [oracle(x, y)[0] for x, y in pairs], name)
    audit = Audit()
    for half in (False, True):
        for size in (1, 8, 127, 128, 129, 1536):
            a = candidate.boundary(np.array([rng.uniform(-1, 1) for _ in range(size)]), half)
            w = candidate.boundary(np.array([[rng.uniform(-1, 1) for _ in range(size)]
                                            for _ in range(3)]), half)
            result = candidate.ordered_rows(w, a)
            for row in range(3):
                counts["ordered_dot_rows"] += require_same(
                    word(result[row]), exact_projection(a, w[row], half), "ordered dot")
            counts["statistics"] += require_same(
                word(candidate.statistic(a)), exact_statistic(candidate.bits32(a)), "statistic")
        for size in (1, 2, 16, 128):
            values = np.asarray([rng.uniform(-3, 3) for _ in range(size)], dtype="<f4")
            for int8 in (False, True):
                record, reconstructed = candidate.cache_block(values, int8)
                audit.cache(values, int8, record, reconstructed)
    for maximum in (0, 1, 63, 64, 127, 128, 0x3f80, 0x7f7f):
        values = candidate.expand([maximum, maximum | 0x8000, 0, 0x8000])
        _, _, error = kv_encode([maximum, maximum | 0x8000, 0, 0x8000], True)
        if error:
            try:
                candidate.cache_block(values, True)
            except ValueError as exc:
                if "nonfinite native activation boundary" not in str(exc):
                    raise
                counts["explicit_kv_overflow_rejections"] += 1
            else:
                raise AssertionError("cache overflow silently accepted")
            continue
        record, reconstructed = candidate.cache_block(values, True)
        audit.cache(values, True, record, reconstructed)
    for width in (2, 4):
        for q in range(1 << width):
            for z in range(1 << width):
                scales = np.array([0, 1, 63, 64, 127, 128, 0x3f00, 0x3f80, 0xbf80],
                                  dtype="<u2")
                actual = candidate.narrow(candidate.dequantized(
                    np.full(scales.shape, q), np.full(scales.shape, z), scales))
                counts["dequant"] += require_same(
                    actual, [dequant(q, z, int(s))[0] for s in scales], "dequant")
    for value in (-80, -20, -1, -0.01, 0, 0.01, 1, 20, 80):
        x = np.float32(value)
        for operation, actual in (
                (4, np.float32(np.exp(float(x)))),
                (5, np.float32(1 / (1 + np.exp(-float(x)))))):
            audit.approximation(float(actual), transcendental(operation, word(x)), "nonlinear")
            counts["nonlinear"] += 1
    for half in (False, True):
        for position in (0, 1, 2, 32767):
            angles = position*np.power(1e6, np.arange(64, dtype="float64")*(-2/128))
            audit.rope(position, 1e6, 128,
                       candidate.boundary(np.cos(angles), half),
                       candidate.boundary(np.sin(angles), half), half)
    # These are executed wrong numerical results, not compiler/time-out controls.
    defects = [
        ("bf16_tie", candidate.narrow(scalar(0x3f808000)) ^ 1, convert(0x3f808000, FP32, BF16)[0]),
        ("w2_sign", candidate.narrow(candidate.dequantized(np.array([0]), np.array([3]),
                                                         np.array([0x3f80], dtype="<u2"))) ^ 0x8000,
         [dequant(0, 3, 0x3f80)[0]]),
        ("tile_result", candidate.bits32(result).copy() ^ 1, candidate.bits32(result)),
    ]
    for name, actual, expected in defects:
        try:
            require_same(actual, expected, "injected "+name)
        except AssertionError:
            counts["rejected_numerical_corruptions"] += 1
        else:
            raise AssertionError("undetected numerical corruption "+name)
    with tempfile.TemporaryDirectory(prefix="reference-integrity-") as directory:
        path = Path(directory) / "checkpoint-fragment.bin"
        path.write_bytes(bytes(range(128)))
        binding = {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        candidate.validate_asset(Path(directory), binding)
        path.write_bytes(b"\xff" + bytes(range(1, 128)))
        try:
            candidate.validate_asset(Path(directory), binding)
        except ValueError as exc:
            if "SHA-256" not in str(exc):
                raise
            counts["rejected_asset_corruptions"] += 1
        else:
            raise AssertionError("undetected checkpoint-byte corruption")
    if not all(counts.values()) or counts["rejected_numerical_corruptions"] != 3:
        raise AssertionError("missing comparison coverage")
    print(json.dumps({"primitive_comparisons": dict(counts), "audit": audit.summary(),
                      "scope": "Software-reference controls only; no RTL/production acceptance."}),
          flush=True)


def validate_execution(output):
    """Check retained full logits/greedy IDs and every required layer observation."""
    data = json.loads((output / "result.json").read_text())
    if data["implementation_sha256"] != {
            p: candidate.digest(candidate.ROOT / p) for p in candidate.IMPLEMENTATION}:
        raise AssertionError("reference execution source mismatch")
    for binding in data["inputs"]:
        candidate.validate_asset(candidate.ROOT, binding)
    if data["kind"] != "software-reference-only" or data["cache_block"] not in (
            1, 2, 4, 8, 16, 32, 64, 128):
        raise AssertionError("invalid reference execution identity")
    counts = data["numerical_audit"]["comparison_counts"]
    for required in ("official_normalizers", "official_norm_products",
                     "official_projection_rows", "official_projection_products",
                     "official_kv_values", "official_kv_bytes", "official_nonlinear_samples",
                     "high_precision_comparisons", "rope_coefficients"):
        if counts.get(required, 0) <= 0:
            raise AssertionError("unexecuted official comparison "+required)
    if data["max_softmax_sum_error"] > 2e-4:
        raise AssertionError("reference softmax sum error")
    records = data["tokens"]
    if len(records) < 3 or data["layers_executed"] != len(records)*28:
        raise AssertionError("missing full-model token/layer execution")
    rows = [json.loads(line) for line in (output / "layers.jsonl").read_text().splitlines()]
    if [(r["position"], r["layer"]) for r in rows] != [
            (p, layer) for p in range(len(records)) for layer in range(28)]:
        raise AssertionError("incomplete or duplicated layer observations")
    for row in rows:
        if (row["input_id"], row["phase"]) != (
                records[row["position"]]["input_id"], records[row["position"]]["phase"]):
            raise AssertionError("layer observation belongs to another request")
        for field, elements in (("activation", 1536), ("key", 256), ("value", 256)):
            summary = row[field]
            if summary["count"] != elements or len(summary["first_values"]) != 8:
                raise AssertionError("missing readable numerical layer values")
            scalars = [summary[k] for k in ("min", "max", "mean", "rms")]
            if not all(np.isfinite(scalars)) or not summary["min"] <= summary["mean"] <= summary["max"]:
                raise AssertionError("invalid numerical layer statistics")
            if any(not summary["min"] <= x <= summary["max"] for x in summary["first_values"]):
                raise AssertionError("invalid layer sample")
        expected_bytes = 1024 if data["kv"] == "bf16" else 512+1024//data["cache_block"]
        if row["kv_bytes"] != expected_bytes:
            raise AssertionError("incorrect KV encoded byte count")
    compared, corruptions = 0, 0
    for position, record in enumerate(records):
        logits = np.load(output / f"logits-{position}.npy", allow_pickle=False)
        if logits.dtype != np.dtype("<f4") or logits.shape != (151936,) or not np.isfinite(logits).all():
            raise AssertionError("invalid retained full-vocabulary logits")
        if record["position"] != position or record["logits"] != candidate.summaries(logits):
            raise AssertionError("retained logits do not match execution summary")
        greedy = max(range(logits.size), key=lambda i: float(logits[i]))
        if greedy != record["greedy_id"]:
            raise AssertionError("retained logits disagree with greedy ID")
        if record["phase"] == "decode" and record["input_id"] != records[position-1]["greedy_id"]:
            raise AssertionError("decode input is not the previous actual greedy result")
        compared += logits.size
        corrupted = logits.copy()
        corrupted.view("<u4")[position] ^= np.uint32(1)
        expected_hash = record["logits"]["sha256_fp32_le"]
        try:
            if hashlib.sha256(corrupted.tobytes()).hexdigest() != expected_hash:
                raise AssertionError("injected retained logit corruption")
        except AssertionError:
            corruptions += 1
        else:
            raise AssertionError("undetected actual official-logit corruption")
        try:
            if (greedy+1) % logits.size != record["greedy_id"]:
                raise AssertionError("injected greedy result corruption")
        except AssertionError:
            corruptions += 1
        else:
            raise AssertionError("undetected actual greedy corruption")
    if compared <= 0 or corruptions != 2*len(records):
        raise AssertionError("missing retained-output/corruption coverage")
    data["retained_output_check"] = {
        "compared_logits": int(compared), "layer_records": len(rows),
        "executed_official_output_corruptions_rejected": corruptions}
    print(json.dumps({"output": str(output.relative_to(candidate.ROOT)),
                      "checked": data["retained_output_check"]}), flush=True)
    return data


def quality(output, baseline, position):
    record = json.loads((output / "result.json").read_text())["tokens"][position]
    original = json.loads((baseline / "result.json").read_text())["tokens"][position]
    if record["input_id"] != original["input_id"] or record["phase"] != "prefill":
        raise AssertionError("quality comparison does not have the same committed input prefix")
    a = np.load(output / f"logits-{position}.npy", allow_pickle=False).astype("float64")
    b = np.load(baseline / f"logits-{position}.npy", allow_pickle=False).astype("float64")
    aa, bb = np.sum(a*a), np.sum(b*b)
    if min(aa, bb) <= 0:
        raise AssertionError("empty original-quality comparison")
    return {"compared_logits": int(a.size), "nrmse": float(np.sqrt(np.sum((a-b)**2)/bb)),
            "cosine": float(np.sum(a*b)/np.sqrt(aa*bb)),
            "original_greedy_id": original["greedy_id"], "mode_greedy_id": record["greedy_id"],
            "scope": "bounded original-weight difference, not same-weight fidelity acceptance"}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] != "--validate" or len(sys.argv) < 3:
            raise SystemExit("usage: official_reference_tests.py [--validate OUTPUT ...]")
        for directory in sys.argv[2:]:
            validate_execution(candidate.portable_path(candidate.ROOT, directory))
    else:
        execute()
