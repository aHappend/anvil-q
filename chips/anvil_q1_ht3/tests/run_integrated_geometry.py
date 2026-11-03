"""Functional legal geometries through public loader, CSR, DDR and logits."""

import argparse
import hashlib
import json
import math
import random
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, execute, hashes, relative, remaining, timestamp
from reference import convert, float_bits
from run_compatibility import (check_case, compiled, matvec, norm, rope, rounded16)
from run_performance import validated_simulation
from run_parameters import legal_cross


CASES = {
    "smallest": dict(L=1, H=8, I=8, Q=1, K=1, D=8, G=1, V=1, S=1,
                     TB=1, KW=1, FT=1),
    "oversized-tile": dict(L=1, H=8, I=8, Q=1, K=1, D=8, G=1, V=1, S=1,
                          TB=3, KW=1, FT=128),
    "nonpower": dict(L=1, H=24, I=40, Q=3, K=1, D=8, G=8, V=17, S=17,
                     TB=3, KW=3, FT=3),
    "medium-gqa": dict(L=1, H=64, I=64, Q=4, K=2, D=16, G=8, V=3, S=4,
                      TB=256, KW=3, FT=16),
}

CROSS_CASES = {}
for name, parameters, _ in legal_cross():
    CROSS_CASES[name] = {
        short: parameters[long] for short, long in (
            ("L", "NUM_LAYERS"), ("H", "HIDDEN_SIZE"), ("I", "INTERMEDIATE_SIZE"),
            ("Q", "NUM_Q_HEADS"), ("K", "NUM_KV_HEADS"), ("D", "HEAD_DIM"),
            ("G", "GROUP_SIZE"), ("V", "VOCAB_SIZE"), ("S", "MAX_SEQ_LEN"),
            ("TB", "TILE_BEATS"), ("KW", "KV_WINDOW"), ("FT", "FLASH_TILE"))
    }
CASES.update(CROSS_CASES)


def reference(embedding, weights, geometry, fmt, traffic):
    """FP64 Qwen equations; no RTL functions, states or intermediate observations."""
    h, d, qh, kh = (geometry[key] for key in ("H", "D", "Q", "K"))
    narrow = lambda values: [rounded16(v, fmt == 1) for v in values]
    cache, result = [], []
    for token, position, fresh in traffic:
        if fresh:
            cache = []
        if position != len(cache):
            raise AssertionError("independent geometry traffic is not a contiguous prefix")
        residual = embedding[token]
        normalized = narrow(norm(residual))
        query = matvec(weights[0], normalized)
        key = matvec(weights[1], normalized)
        value = narrow(matvec(weights[2], normalized))
        query = narrow([v for head in range(qh)
                        for v in rope(query[head*d:(head+1)*d], position)])
        key = narrow([v for head in range(kh)
                      for v in rope(key[head*d:(head+1)*d], position)])
        cache.append((key, value))
        attention = []
        for head in range(qh):
            kv_head = head//(qh//kh)
            q = query[head*d:(head+1)*d]
            scores = [math.fsum(a*b for a, b in zip(q, k[kv_head*d:(kv_head+1)*d])) /
                      math.sqrt(d) for k, _ in cache]
            p = [math.exp(score-max(scores)) for score in scores]
            total = math.fsum(p)
            attention.extend(math.fsum(prob*v[kv_head*d+j]
                                       for prob, (_, v) in zip(p, cache))/total
                             for j in range(d))
        if len(attention) != h:
            raise AssertionError("independent GQA produced the wrong shape")
        projected = matvec(weights[3], narrow(attention))
        residual = [a+b for a, b in zip(residual, projected)]
        normalized = narrow(norm(residual))
        gate, up = matvec(weights[4], normalized), matvec(weights[5], normalized)
        swiglu = narrow([g/(1+math.exp(-g))*u for g, u in zip(gate, up)])
        down = matvec(weights[6], swiglu)
        residual = [a+b for a, b in zip(residual, down)]
        result.append(matvec(embedding, narrow(norm(residual))))
    return result


def fixture(directory, geometry, fmt, seed):
    if geometry["L"] != 1 or fmt not in (0, 1):
        raise ValueError("this functional fixture covers one-layer native formats")
    h, intermediate, kv, vocab = (geometry["H"], geometry["I"],
                                  geometry["K"]*geometry["D"], geometry["V"])
    rng = random.Random(seed)
    embedding = [[rng.choice((-7, -5, -3, 1, 2, 4, 6))/16 for _ in range(h)]
                 for _ in range(vocab)]
    shapes = [(h, h), (kv, h), (kv, h), (h, h),
              (intermediate, h), (intermediate, h), (h, intermediate)]
    weights = [[[rng.randrange(-4, 5)/32 for _ in range(columns)]
                for _ in range(rows)] for rows, columns in shapes]
    image, descriptors = bytearray(), []

    def region(kind, projection, payload):
        base = len(image)
        payload += bytes((-len(payload)) % 64)
        image.extend(payload)
        descriptors.append((8*kind+projection, kind, 0, projection, base, len(payload)))

    def panel(matrix):
        payload = bytearray()
        for start in range(0, len(matrix), 64):
            for column in range(len(matrix[0])):
                for row in range(start, start+64):
                    word = convert(float_bits(matrix[row][column]), fmt == 1) if row<len(matrix) else 0
                    payload.extend(word.to_bytes(2, "little"))
        return payload

    region(0, 0, panel(embedding))
    for projection, matrix in enumerate(weights):
        region(1, projection, panel(matrix))
    for projection, length in enumerate((h, kv, kv)):
        region(4, projection, bytes(length*2))
    for kind in (5, 6, 7):
        region(kind, 0, convert(float_bits(1), fmt == 1).to_bytes(2, "little")*h)
    region(8, 0, bytes(15*max(h, intermediate)*4))
    for kind in (9, 10):
        region(kind, 0, bytes(geometry["S"]*((2*kv+63)//64)*64))
    region(11, 0, bytes(geometry["S"]*geometry["D"]*4))
    if len(image)>262144:
        raise ValueError("fixture exceeds the declared public memory model")
    count = geometry["S"] if geometry["KW"] == 128 else min(geometry["S"], 4)
    traffic = [(position % vocab, position, int(position == 0))
               for position in range(count)]
    if geometry["S"] > 1:
        traffic.append((0, 0, 1))
    expected = reference(embedding, weights, geometry, fmt, traffic)
    vectors = directory/"vectors.txt"
    with vectors.open("x") as out:
        out.write(f"{fmt} {len(image)//64} {len(descriptors)} {len(traffic)}\n")
        for offset in range(0, len(image), 64):
            out.write(f"{offset:08x} {int.from_bytes(image[offset:offset+64], 'little'):0128x}\n")
        for index, kind, layer, projection, base, length in descriptors:
            out.write(f"{index} {kind} {layer} {projection} {base:08x} {length}\n")
        for token, position, fresh in traffic:
            out.write(f"{token} {position} {fresh}\n")
    with (directory/"image-manifest.json").open("x") as out:
        json.dump(dict(kind="independent compact synthetic checkpoint", geometry=geometry,
                       format=fmt, seed=seed, bytes=len(image),
                       sha256=hashlib.sha256(image).hexdigest(), traffic=traffic,
                       descriptors=descriptors, fp64_logits=expected), out, indent=2)
    return vectors, expected


def run(output, case=None, selected_format=None, fresh=False, cross_only=False):
    rows = []
    for name, geometry in CASES.items():
        if case is not None and name != case:
            continue
        if cross_only and name not in CROSS_CASES:
            continue
        try:
            binary, binding = compiled(geometry)
        except (RuntimeError, ValueError, OSError) as exc:
            rows.append(dict(id=name, status="failed", phase="compile", error=str(exc)))
            continue
        for fmt, seed in ((0, 17), (1, 89)):
            if selected_format is not None and fmt != selected_format:
                continue
            directory = output/f"{name}-format{fmt}-seed{seed}-{uuid.uuid4().hex[:8]}"
            directory.mkdir()
            try:
                vectors, expected = fixture(directory, geometry, fmt, seed)
                candidates = [p for parent in (ROOT/"evidence/l1", ROOT/"evidence/preparation")
                              for p in parent.glob(
                                  f"*/*/{name}-format{fmt}-seed{seed}-*/simulation.receipt.json")]
                if fresh:
                    candidates = []
                checked = None
                for path in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True):
                    checked = validated_simulation(path, binary, binding, vectors, fmt, seed,
                                                   expected, "ht3", vocab=geometry["V"])
                    if checked is not None:
                        simulation_receipt = path
                        break
                reused = checked is not None
                if checked is None:
                    execute([relative(binary), f"+vectors={relative(vectors)}",
                             f"+observations={relative(directory/'observations.txt')}",
                             f"+seed={seed}"], directory, "simulation", ["verilator", "--version"])
                    simulation_receipt = directory/"simulation.receipt.json"
                    checked = validated_simulation(simulation_receipt, binary, binding, vectors,
                                                   fmt, seed, expected, "ht3",
                                                   vocab=geometry["V"])
                    if checked is None:
                        raise AssertionError("fresh geometry simulation has invalid provenance")
                observation, artifacts = checked
                traffic = json.loads((directory/"image-manifest.json").read_text())["traffic"]
                if len(observation["metrics"]) != len(traffic):
                    raise AssertionError("functional geometry did not compare every accepted position")
                rows.append(dict(id=name, geometry=geometry, directory=relative(directory),
                                 reused=reused, simulation_receipt=relative(simulation_receipt),
                                 compared_positions=[row[1] for row in traffic],
                                 artifact_sha256=artifacts, **observation))
                with (directory/"case.json").open("x") as out:
                    json.dump(rows[-1], out, indent=2)
            except (RuntimeError, AssertionError, ValueError, OSError) as exc:
                rows.append(dict(id=name, geometry=geometry, format=fmt, seed=seed,
                                 directory=relative(directory), status="failed", error=str(exc)))
    return dict(status="passed" if rows and all(row["status"]=="passed" for row in rows)
                else "failed", runs=rows,
                coverage_limits=(["selected functional geometry/format only"]
                                 if case or selected_format is not None or cross_only else []))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--format", type=int, choices=(0, 1))
    parser.add_argument("--fresh", action="store_true",
                        help="restart selected simulations, never restore partial execution")
    parser.add_argument("--cross-only", action="store_true",
                        help="execute the twelve admitted pairwise parameter tuples")
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_integrated_geometry.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    try:
        result = run(output, args.case, args.format, args.fresh, args.cross_only)
    except (RuntimeError, AssertionError, ValueError, OSError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
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
