"""Independent attention reference: global FP64 softmax, not DUT helper calls."""

import argparse
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
from reference import convert, decode, float_bits, float_value, vector_check


def pack(values, width):
    return sum(v << (width*i) for i, v in enumerate(values))


def tree(mask, prefix):
    ancestors = [0]*4
    positions = [0]*4
    active = [s for s in range(4) if mask & (1 << s)]
    for i, s in enumerate(active):
        parents = active[:i] if mask != 15 or s != 2 else [0]
        ancestors[s] = (1 << s) | sum(1 << p for p in parents)
        positions[s] = prefix + len(parents)
    if mask == 15:
        ancestors[3] = 0b1011
        positions[3] = prefix+2
    return positions, pack(ancestors, 4)


COMPACT_SCHEDULE = (
    (17, 3, 1, 8, 1, False),
    (89, 2, 2, 64, 3, False),
    (2026, 3, 1, 8, 16, False),
    (17, 2, 2, 64, 128, False),
    (89, 1, 1, 8, 16, True),
)


def fixtures(seed, q, k, d, tile, diagnostic=False, long_context=False, compact=False):
    rng = random.Random(seed)
    lengths = sorted({1, max(1, tile-1), tile, tile+1})
    masks = (1, 2, 4, 8, 5, 10, 15) if not diagnostic else (1, 5, 15)
    configurations = [(fmt, fp, length, mask)
                      for fmt in range(4) for fp in (0, 1)
                      for length in lengths for mask in masks]
    if diagnostic:
        configurations = [(fmt, fmt == 1, tile+1, mask)
                          for fmt in range(4) for mask in masks]
    elif compact:
        configurations = [(fmt, fp, length, masks[(fmt*2+fp+i) % len(masks)])
                          for fmt in range(4) for fp in (0, 1)
                          for i, length in enumerate(lengths)]
    if long_context:
        configurations = ([(0, 0, 32768, 1)] if compact else
                          configurations + [(fmt, 0, 32768, 1) for fmt in range(4)])
    for fmt, fp, length, mask in configurations:
        prefix = length-1
        positions, ancestors = tree(mask, prefix)
        queries = [[convert(float_bits(rng.uniform(-1, 1)), fp)
                    if mask & (1 << s) else 0x7FFF
                    for s in range(4)] for _ in range(q*d)]
        keys, values = [], []
        ks, vs = float_bits(0.0625), float_bits(0.03125)
        for source in range(prefix+4):
            for head in range(k):
                for col in range(d):
                    if fmt < 2:
                        x = ((source*3+col+head) % 23-11)*0.25
                        y = ((source+col*5+head*3) % 17-8)*0.125
                        keys.append(convert(float_bits(x), fmt == 1))
                        values.append(convert(float_bits(y), fmt == 1))
                    else:
                        width = 4 if fmt == 2 else 8
                        keys.append((source*d+col+head*3) % (1 << width))
                        values.append((source*d+col*7+head) % (1 << width))
        yield dict(fmt=fmt, fp=int(fp), length=length, prefix=prefix, mask=mask,
                   positions=positions, ancestors=ancestors, query=queries,
                   keys=keys, values=values, ks=ks, vs=vs, error=0, fault=0)
    base = dict(next(fixtures(seed, q, k, d, tile, diagnostic=True)))
    for change in (dict(mask=0, ancestors=0), dict(ancestors=0),
                   dict(query=[[0x7FFF]*4 for _ in range(q*d)]),
                   dict(fault=1), dict(fmt=2, ks=0),
                   dict(fmt=3, vs=0xBF800000)):
        yield {**base, **change, "error": 1}


def value(word, fmt, scale):
    if fmt < 2:
        return float_value(convert(word, fmt == 1, True))
    width = 4 if fmt == 2 else 8
    integer = word - (1 << width) if word & (1 << (width-1)) else word
    return integer * float_value(scale)


def reference(case, slot, head, k, d, q):
    prefix = case["prefix"]
    ancestors = (case["ancestors"] >> (slot*4)) & 15
    sources = list(range(prefix)) + [prefix+s for s in range(4) if ancestors & (1 << s)]
    mapped = head // (q//k)
    query = [float_value(convert(case["query"][head*d+j][slot], case["fp"], True))
             for j in range(d)]
    scores = []
    for source in sources:
        start = (source*k+mapped)*d
        key = [value(case["keys"][start+j], case["fmt"], case["ks"]) for j in range(d)]
        scores.append(math.fsum(a*b for a, b in zip(query, key))/math.sqrt(d))
    maximum = max(scores)
    probabilities = [math.exp(score-maximum) for score in scores]
    denominator = math.fsum(probabilities)
    return [math.fsum(p*value(case["values"][(s*k+mapped)*d+j],
                             case["fmt"], case["vs"])
                      for s, p in zip(sources, probabilities))/denominator
            for j in range(d)]


def compiled_attention(q, k, d, tile):
    """Reuse only an immutable binary bound to exact sources, geometry and tool."""
    source_paths = [relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))]
    source_paths += ["tests/attention_tb.sv"]
    current_hashes = hashes()
    identity = dict(source_sha256={p: current_hashes[p] for p in source_paths},
                    geometry=[q, k, d, tile])
    cache = ROOT / "evidence/compiled"
    cache.mkdir(parents=True, exist_ok=True)
    version_dir = cache / f"attention-version-{uuid.uuid4().hex[:12]}"
    version_dir.mkdir()
    identity["tool_version"] = execute(["verilator", "--version"], version_dir,
                                      "version", ["verilator", "--version"]).strip()
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
    for directory in sorted(cache.glob(f"attention-{key}-*")):
        binding = directory / "binding.json"
        binary = directory / "compile-obj/Vattention_tb"
        if binding.is_file() and binary.is_file():
            record = json.loads(binding.read_text())
            receipt = json.loads((directory / "compile.receipt.json").read_text())
            if (record["identity"] == identity and receipt["exit"] == 0
                    and not receipt["timed_out"]
                    and record["binary_sha256"] == hashlib.sha256(binary.read_bytes()).hexdigest()):
                return binary, relative(binding)
    directory = cache / f"attention-{key}-{uuid.uuid4().hex[:12]}"
    directory.mkdir()
    objects = directory / "compile-obj"
    execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
             "--top-module", "attention_tb", f"-GQ={q}", f"-GK={k}", f"-GD={d}",
             f"-GTILE={tile}", "--Mdir", relative(objects), *source_paths],
            directory, "compile", ["verilator", "--version"])
    binary = objects / "Vattention_tb"
    with (directory / "binding.json").open("x") as out:
        json.dump(dict(identity=identity,
                       binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                       compile_receipt=relative(directory / "compile.receipt.json")), out, indent=2)
    clean_objects(objects)
    return binary, relative(directory / "binding.json")


def run_case(output, seed, q, k, d, tile, diagnostic, long_context=False, compact=False):
    vectors = output / "vectors.txt"
    observations = output / "observations.txt"
    cases = list(fixtures(seed, q, k, d, tile, diagnostic, long_context, compact))
    with vectors.open("x") as out:
        for c in cases:
            out.write(f'{c["fmt"]} {c["fp"]} {c["mask"]} {c["prefix"]} '
                      f'{pack(c["positions"],32):032x} {c["ancestors"]:04x} '
                      f'{c["ks"]:08x} {c["vs"]:08x} {c["error"]} {c["fault"]}\n')
            for row in c["query"]:
                out.write(f"{pack(row,16):016x}\n")
            for key, val in zip(c["keys"], c["values"]):
                out.write(f"{key:04x} {val:04x}\n")
    binary, compile_binding = compiled_attention(q, k, d, tile)
    simulation_failure = None
    try:
        text = execute([relative(binary), f"+vectors={relative(vectors)}",
                        f"+observations={relative(observations)}", f"+seed={seed}"],
                       output, "simulation", ["verilator", "--version"])
    except RuntimeError as exc:
        simulation_failure = str(exc)
        text = (output / "simulation.stdout.txt").read_text()
    summary = re.search(r"SUMMARY attention commands=(\d+) requests=(\d+) "
                        r"output_stalls=(\d+) bus_stalls=(\d+) bubbles=(\d+)", text)
    if not simulation_failure and (
            not summary or int(summary[1]) != len(cases) or min(map(int, summary.groups()[1:])) <= 0):
        raise AssertionError("missing complete public attention coverage summary")
    actual = [[] for _ in cases]
    completed = {}
    observation_failures = []
    lines = observations.read_text().splitlines()
    for line_number, line in enumerate(lines):
        row = line.split()
        if not row or len(row) != (5 if row[0] == "O" else 6):
            if simulation_failure and line_number == len(lines)-1:
                observation_failures.append(dict(message="aborted simulator left incomplete final observation",
                                                 raw=line))
                break
            raise AssertionError("malformed attention observation field count")
        cmd = int(row[1])
        if cmd >= len(cases) or cmd in completed:
            raise AssertionError("unexpected/late attention observation")
        c = cases[cmd]
        if row[0] == "O":
            if int(row[2]) != len(actual[cmd]) or int(row[3], 16) != c["mask"]:
                raise AssertionError("attention coordinate/slot association")
            bits = int(row[4], 16)
            coordinate = [float_value((bits >> (s*32)) & 0xFFFFFFFF) for s in range(4)]
            if any(coordinate[s] != 0 for s in range(4) if not c["mask"] & (1 << s)):
                raise AssertionError("masked attention output contamination")
            actual[cmd].append(coordinate)
        elif row[0] == "C":
            if int(row[2]) != c["error"] or int(row[3]) != len(actual[cmd]):
                raise AssertionError("attention completion mismatch")
            completed[cmd] = dict(cycles=int(row[4]), fetches=int(row[5]))
        else:
            raise AssertionError("malformed attention observation")
    if not simulation_failure and len(completed) != len(cases):
        raise AssertionError("unclosed attention commands")
    comparisons, failures = [], []
    failures.extend(observation_failures)
    if simulation_failure:
        failures.append(dict(message=simulation_failure, completed_commands=len(completed),
                             required_commands=len(cases), first_mismatch=text[-2000:]))
    for cmd, c in enumerate(cases):
        if cmd not in completed:
            continue
        if c["error"]:
            if actual[cmd]:
                raise AssertionError("invalid attention result")
            continue
        if len(actual[cmd]) != q*d:
            raise AssertionError("missing attention vector")
        for slot in range(4):
            if not c["mask"] & (1 << slot):
                continue
            for head in range(q):
                vector = [actual[cmd][head*d+j][slot] for j in range(d)]
                expected = reference(c, slot, head, k, d, q)
                try:
                    cosine, error = vector_check(vector, expected)
                    comparisons.append(dict(command=cmd, slot=slot, head=head,
                                            cosine=cosine, max_abs_error=error,
                                            format=c["fmt"], context=c["length"]))
                except AssertionError as exc:
                    failures.append(dict(command=cmd, slot=slot, head=head,
                                         message=str(exc), actual=vector, reference=expected))
    result = dict(status="failed" if failures else "passed", seed=seed,
                  geometry=dict(q=q, k=k, d=d, tile=tile), commands=len(cases),
                  comparisons=comparisons, failures=failures, completions=completed,
                  diagnostic=diagnostic, raw_summary=summary[0] if summary else None,
                  compact=compact, compile_binding=compile_binding,
                  vector_sha256=hashlib.sha256(vectors.read_bytes()).hexdigest())
    with (output / "result.json").open("x") as out:
        json.dump(result, out, indent=2)
    if failures:
        raise AssertionError(f"{len(failures)} attention assertion/tool failures; {relative(output/'result.json')}")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--compact", action="store_true",
                        help="distributed obligation matrix, not a Cartesian seed sweep")
    parser.add_argument("--seed", type=int, choices=(17,89,2026), default=17)
    parser.add_argument("--tile", type=int, choices=(1,3,16,128), default=3)
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_attention.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    results, errors = [], []
    matrix = ([(args.seed, 3, 1, 8, args.tile, False)] if args.diagnostic else
              COMPACT_SCHEDULE if args.compact else [
        (seed, q, k, d, tile, seed == 17 and tile == 16 and d == 8)
        for seed in (17,89,2026) for q,k,d in ((3,1,8),(2,2,64))
        for tile in (1,3,16,128)])
    for seed,q,k,d,tile,long_context in matrix:
        shard = output / f"q{q}-k{k}-d{d}-tile{tile}-seed{seed}-{uuid.uuid4().hex[:8]}"
        shard.mkdir()
        try:
            result = run_case(shard, seed,q,k,d,tile,args.diagnostic,long_context,args.compact)
            results.append(dict(path=relative(shard/"result.json"), status=result["status"],
                                vectors=len(result["comparisons"]), commands=result["commands"]))
        except (RuntimeError, AssertionError) as exc:
            errors.append(dict(path=relative(shard), error=str(exc),
                               timed_out=getattr(exc, "timed_out", False)))
    result = dict(status="failed" if errors else "passed", shards=results, failures=errors,
                  diagnostic=args.diagnostic, compact=args.compact,
                  schedule=[dict(seed=s,q=q,k=k,d=d,tile=t,long_context=l)
                            for s,q,k,d,t,l in matrix],
                  coverage_limits=["abort/reset during accepted KV", "zero-latency KV response",
                                   "resident-tile handoff edge assertions",
                                   "subnormal/extreme directed vectors"])
    with (output / "result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(exit=1 if errors else 0, end=timestamp(),
                   timed_out=remaining() <= 0 or any(e["timed_out"] for e in errors) or any(
                       json.loads(p.read_text()).get("timed_out", False)
                       for p in output.rglob("*.receipt.json")),
                   result=relative(output/"result.json"))
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
