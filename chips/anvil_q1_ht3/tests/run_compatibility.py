"""Public loader/CSR/DDR/token inference against a mathematical FP64 model.

The compact checkpoint is an independently authored deterministic test image,
not official Qwen weights or a recovered historical benchmark fixture.
"""

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import random
import re
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, clean_objects, execute, hashes, relative, remaining, timestamp
from reference import convert, encode, float_bits, float_value


def logit_check(actual, reference):
    """Model vectors require cosine; the standalone operator error bound is separate."""
    if not actual or len(actual) != len(reference):
        raise AssertionError("missing or wrong-length model logit vector")
    if not all(math.isfinite(x) for x in actual+reference):
        raise AssertionError("nonfinite model logits")
    aa, rr = math.fsum(x*x for x in actual), math.fsum(x*x for x in reference)
    if not aa or not rr:
        if aa != rr or any(x != 0 for x in actual):
            raise AssertionError("model logit zero-vector mismatch")
        cosine = 1.0
    else:
        cosine = math.fsum(a*b for a, b in zip(actual, reference))/math.sqrt(aa*rr)
    error = max(abs(a-b) for a, b in zip(actual, reference))
    if cosine < 0.9999:
        raise AssertionError(f"model logit cosine={cosine}, required=0.9999, error={error}")
    return dict(cosine=cosine, max_abs_error=error, required_cosine=0.9999)


def rounded16(value, fp16):
    bits = encode(Fraction.from_float(value), *( (5, 10) if fp16 else (8, 7)))
    return float_value(convert(bits, fp16, True))


def norm(values):
    scale = 1/math.sqrt(math.fsum(v*v for v in values)/len(values) +
                        float_value(0x358637BD))
    return [v*scale for v in values]


def matvec(matrix, vector):
    return [math.fsum(a*b for a, b in zip(row, vector)) for row in matrix]


def rope(vector, position):
    result = list(vector)
    half = len(vector)//2
    for j in range(half):
        angle = position*1000000**(-2*j/len(vector))
        a, b = vector[j], vector[j+half]
        result[j] = a*math.cos(angle)-b*math.sin(angle)
        result[j+half] = a*math.sin(angle)+b*math.cos(angle)
    return result


def inference_reference(embedding, weights, fmt, traffic):
    fp16 = fmt == 1
    narrow = lambda values: [rounded16(v, fp16) for v in values]
    cache = []
    outputs = []
    for token, position, fresh in traffic:
        if fresh:
            cache = []
        assert position == len(cache)
        residual = embedding[token]
        n = narrow(norm(residual))
        q = narrow(rope(matvec(weights[0], n), position))
        k = narrow(rope(matvec(weights[1], n), position))
        v = narrow(matvec(weights[2], n))
        cache.append((k, v))
        scores = [math.fsum(a*b for a, b in zip(q, key))/math.sqrt(8)
                  for key, _ in cache]
        probabilities = [math.exp(s-max(scores)) for s in scores]
        total = math.fsum(probabilities)
        attention = [math.fsum(p*value[j] for p, (_, value) in zip(probabilities, cache))/total
                     for j in range(8)]
        attention_projection = matvec(weights[3], narrow(attention))
        residual = [a+b for a, b in zip(residual, attention_projection)]
        post = narrow(norm(residual))
        gate = matvec(weights[4], post)
        up = matvec(weights[5], post)
        intermediate = narrow([g/(1+math.exp(-g))*u for g, u in zip(gate, up)])
        down = matvec(weights[6], intermediate)
        residual = [a+b for a, b in zip(residual, down)]
        outputs.append(matvec(embedding, narrow(norm(residual))))
    return outputs


def fixture(directory, fmt, seed, smoke=False):
    rng = random.Random(seed)
    embedding = [[rng.choice((-7, -5, -3, 1, 2, 4, 6))/16 for _ in range(8)]
                 for _ in range(3)]
    weights = [[[rng.randrange(-4, 5)/16 for _ in range(8)] for _ in range(8)]
               for _ in range(7)]
    image = bytearray()
    descriptors = []

    def region(kind, projection, payload):
        base = len(image)
        payload += bytes((-len(payload)) % 64)
        image.extend(payload)
        descriptors.append((kind*8+projection, kind, 0, projection, base, len(payload)))

    def panel(matrix, awq=False):
        payload = bytearray()
        for column in range(8):
            if awq:
                # Legacy AWQ order within each eight-row group:
                # logical lane -> nibble {lane[0],lane[2:1]}.
                beat = bytearray(64)
                for row in range(len(matrix)):
                    code = round(matrix[row][column]*16)+8
                    shift = ((row & 1)*4 + ((row & 7) >> 1))*4
                    word = int.from_bytes(beat[4*(row//8):4*(row//8)+4], "little")
                    word |= code << shift
                    beat[4*(row//8):4*(row//8)+4] = word.to_bytes(4, "little")
                payload.extend(beat)
            else:
                for row in range(64):
                    word = convert(float_bits(matrix[row][column]), fmt == 1) if row<len(matrix) else 0
                    payload.extend(word.to_bytes(2, "little"))
        return payload

    region(0, 0, panel(embedding))
    for projection, matrix in enumerate(weights):
        region(1, projection, panel(matrix, fmt == 2))
    if fmt == 2:
        for projection in range(7):
            zero = sum(8 << (4*j) for j in range(8))
            region(2, projection, zero.to_bytes(4, "little")*8 + bytes(32))
            region(3, projection, (0x2C00).to_bytes(2, "little")*8 + bytes(112))
    for projection in range(3):
        region(4, projection, bytes(16))
    for kind in (5, 6, 7):
        one = convert(float_bits(1), fmt == 1)
        region(kind, 0, one.to_bytes(2, "little")*8)
    region(8, 0, bytes(15*8*4))
    for kind in (9, 10):
        region(kind, 0, bytes(4*64))
    region(11, 0, bytes(4*8*4))
    traffic = [(0, 0, 1)] if smoke else [(0, 0, 1), (1, 1, 0), (2, 0, 1)]
    expected = inference_reference(embedding, weights, fmt, traffic)
    path = directory/"vectors.txt"
    with path.open("x") as out:
        out.write(f"{fmt} {len(image)//64} {len(descriptors)} {len(traffic)}\n")
        for offset in range(0, len(image), 64):
            out.write(f"{offset:08x} {int.from_bytes(image[offset:offset+64], 'little'):0128x}\n")
        for index, kind, layer, projection, base, length in descriptors:
            out.write(f"{index} {kind} {layer} {projection} {base:08x} {length}\n")
        for token, position, fresh in traffic:
            out.write(f"{token} {position} {fresh}\n")
    with (directory/"image-manifest.json").open("x") as out:
        json.dump(dict(kind="independent compact synthetic checkpoint", format=fmt,
                       seed=seed, bytes=len(image), sha256=hashlib.sha256(image).hexdigest(),
                       descriptors=descriptors, traffic=traffic, fp64_logits=expected),
                  out, indent=2)
    return path, expected


def compiled():
    paths = [relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))]+["tests/inference_tb.sv"]
    current = hashes()
    identity = dict(source_sha256={p: current[p] for p in paths},
                    geometry=dict(L=1, H=8, I=8, Q=1, K=1, D=8, G=8, V=3, S=4))
    cache = ROOT/"evidence/compiled"
    cache.mkdir(parents=True, exist_ok=True)
    version_dir = cache/f"inference-version-{uuid.uuid4().hex[:12]}"
    version_dir.mkdir()
    identity["tool_version"] = execute(["verilator", "--version"], version_dir, "version",
                                     ["verilator", "--version"]).strip()
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
    for directory in sorted(cache.glob(f"inference-{key}-*")):
        binding, binary = directory/"binding.json", directory/"compile-obj/Vinference_tb"
        if not binding.is_file() or not binary.is_file():
            continue
        record = json.loads(binding.read_text())
        receipt = json.loads((directory/"compile.receipt.json").read_text())
        if (record["identity"] == identity and receipt["exit"] == 0 and not receipt["timed_out"]
                and record["binary_sha256"] == hashlib.sha256(binary.read_bytes()).hexdigest()):
            return binary, relative(binding)
    directory = cache/f"inference-{key}-{uuid.uuid4().hex[:12]}"
    directory.mkdir()
    objects = directory/"compile-obj"
    execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
             "--top-module", "inference_tb", "--Mdir", relative(objects),
             *paths], directory, "compile", ["verilator", "--version"])
    binary = objects/"Vinference_tb"
    with (directory/"binding.json").open("x") as out:
        json.dump(dict(identity=identity,
                       binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                       compile_receipt=relative(directory/"compile.receipt.json")), out, indent=2)
    clean_objects(objects)
    return binary, relative(directory/"binding.json")


def run_case(directory, binary, binding, fmt, seed, smoke=False):
    vectors, expected = fixture(directory, fmt, seed, smoke)
    observations = directory/"observations.txt"
    text = execute([relative(binary), f"+vectors={relative(vectors)}",
                    f"+observations={relative(observations)}", f"+seed={seed}"],
                   directory, "simulation", ["verilator", "--version"])
    match = re.search(r"SUMMARY inference format=(\d+) tokens=(\d+) logits=(\d+) "
                      r"csr=(\d+) csr_holds=(\d+) output_stalls=(\d+) reads=(\d+) "
                      r"writes=(\d+) bus_waits=(\d+) max_debt=(\d+)", text)
    if (not match or int(match[1]) != fmt or int(match[2]) != len(expected) or
            int(match[3]) != 3*len(expected) or any(int(match[j]) == 0 for j in range(4, 11))):
        raise AssertionError("incomplete integrated inference observation summary")
    actual = [[] for _ in expected]
    cycles = []
    for line in observations.read_text().splitlines():
        parts = line.split()
        if parts[0] == "L":
            token, index, bits = int(parts[1]), int(parts[2]), int(parts[3], 16)
            if token >= len(expected) or index != len(actual[token]):
                raise AssertionError("duplicate or misassociated integrated logit")
            actual[token].append(float_value(bits))
        elif parts[0] == "T":
            if int(parts[1]) != len(cycles):
                raise AssertionError("duplicate or missing cycle measurement")
            cycles.append(dict(token=int(parts[1]), cycles=int(parts[2]),
                               ddr_read_beats=int(parts[3]), ddr_write_beats=int(parts[4]),
                               simulated_tpm=60*100000000/int(parts[2]),
                               timing_basis="simulated 100 MHz core / 50 MHz DDR; not STA"))
        else:
            raise AssertionError("unrecognized inference observation")
    if len(cycles) != len(expected):
        raise AssertionError("missing completed-token measurements")
    metrics = [logit_check(a, b) for a, b in zip(actual, expected)]
    return dict(status="passed", format=fmt, seed=seed, metrics=metrics, measurements=cycles,
                raw_summary=match[0], binary_binding=binding)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_compatibility.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    rows = []
    try:
        binary, binding = compiled()
        for seed in ((17,) if args.smoke else (17, 89, 2026)):
            for fmt in ((0,) if args.smoke else range(3)):
                directory = output/f"format{fmt}-seed{seed}-{uuid.uuid4().hex[:8]}"
                directory.mkdir()
                try:
                    rows.append(run_case(directory, binary, binding, fmt, seed, args.smoke))
                except (RuntimeError, AssertionError, ValueError, OSError) as exc:
                    rows.append(dict(status="failed", format=fmt, seed=seed,
                                     error=f"{type(exc).__name__}: {exc}",
                                     directory=relative(directory)))
    except (RuntimeError, AssertionError, ValueError, OSError) as exc:
        rows.append(dict(status="failed", error=f"{type(exc).__name__}: {exc}"))
    result = dict(status="passed" if rows and all(r["status"]=="passed" for r in rows) else "failed",
                  runs=rows, checkpoint="independent compact synthetic image, not official model",
                  coverage_limits=[] if args.smoke else [
                      "H>=64 integrated inference and legal geometry extrema",
                      "batch/ancestor/correction/commit, nonzero sparse threshold and injected bus errors",
                      "reset/abort during accepted inference and loader/CSR ownership collisions",
                      "unchanged HT2 differential execution",
                      "authentic historical five-domain fixtures unavailable in supplied RTL-only intake"])
    with (output/"result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"]!="passed"),
                   result=relative(output/"result.json"),
                   timed_out=any(json.loads(p.read_text()).get("timed_out", False)
                                 for p in output.rglob("*.receipt.json")))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
