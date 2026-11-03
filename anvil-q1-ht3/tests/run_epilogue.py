"""Public-stream epilogue checks against independently evaluated FP64 formulas."""

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import convert, float_bits, float_value, vector_check
from run_unit import ROOT, execute, hashes, relative


def pack(values, width):
    return sum(value << (i * width) for i, value in enumerate(values))


def cases(seed):
    rng = random.Random(seed)
    cases = []
    for op in range(7):
        for fp16 in (0, 1):
            for variant, mask in enumerate((1, 2, 4, 8, 5, 10, 15)):
                length = 64 if op in (2, 5) else (1, 8, 64)[variant % 3]
                x = [[float_bits(rng.uniform(-3, 3)) for _ in range(length)]
                     for _ in range(4)]
                aux = [[float_bits(rng.uniform(-2, 2)) for _ in range(length)]
                       for _ in range(4)]
                if variant == 0:
                    x = [[0] * length for _ in range(4)]
                if variant == 1:
                    x = [[float_bits((-1 if i & 1 else 1) * (i + 1) / 8)
                          for i in range(length)] for _ in range(4)]
                if variant == 2:
                    x = [[(1 if i & 1 else 0x80000001) for i in range(length)]
                         for _ in range(4)]
                if variant == 3 and op == 3:
                    x = [[float_bits(-100 if i & 1 else -1000)
                          for i in range(length)] for _ in range(4)]
                for slot in range(4):
                    if not mask & (1 << slot):
                        x[slot] = [0x7FC00000] * length
                        aux[slot] = [0x7F800000] * length
                gamma_value = (0.0, 1.0, 1.5)[variant % 3]
                gamma = [convert(float_bits(gamma_value), fp16)] * length
                positions = [(0, 1, 32767)[(slot + variant) % 3] for slot in range(4)]
                cases.append(dict(op=op, fp16=fp16, mask=mask, length=length,
                                  x=x, aux=aux, gamma=gamma, positions=positions,
                                  error=0))
    base = dict(op=0, fp16=0, mask=1, length=1, x=[[float_bits(1)]] * 4,
                aux=[[0]] * 4, gamma=[0x3F80], positions=[0] * 4, error=1)
    for updates in (dict(op=7), dict(mask=0), dict(length=0), dict(op=2),
                    dict(x=[[0x7FC00000]] * 4),
                    dict(op=1, gamma=[0x7F80])):
        cases.append({**base, **updates})
    return cases


def expected(case, slot):
    x = [float_value(b) for b in case["x"][slot]]
    aux = [float_value(b) for b in case["aux"][slot]]
    gamma = [float_value(convert(b, case["fp16"], True)) for b in case["gamma"]]
    op = case["op"]
    if op in (4, 6):
        x = [a + b for a, b in zip(x, aux)]
    if op in (1, 5, 6):
        inverse = 1.0 / math.sqrt(sum(a * a for a in x) / len(x) + 1e-6)
        x = [a * inverse * g for a, g in zip(x, gamma)]
    if op in (2, 5):
        out = x.copy()
        for start in range(0, len(x), 64):
            for j in range(32):
                angle = case["positions"][slot] * 1000000.0 ** (-2.0 * j / 64)
                a, b = x[start + j], x[start + j + 32]
                out[start + j] = a * math.cos(angle) - b * math.sin(angle)
                out[start + j + 32] = a * math.sin(angle) + b * math.cos(angle)
        x = out
    if op == 3:
        def silu(a):
            if a >= 0:
                return a / (1 + math.exp(-a))
            e = math.exp(a)
            return a * e / (1 + e)
        x = [silu(a) * b for a, b in zip(x, aux)]
    return x


def run(seed, output):
    fixtures = cases(seed)
    vectors = output / "vectors.txt"
    observations = output / "observations.txt"
    with vectors.open("x") as out:
        for c in fixtures:
            out.write(f'{c["op"]} {c["mask"]} {c["fp16"]} {c["length"]} '
                      f'{pack(c["positions"],32):032x} {c["error"]}\n')
            for i in range(c["length"]):
                out.write(f'{pack([x[i] for x in c["x"]],32):032x} '
                          f'{pack([x[i] for x in c["aux"]],32):032x} {c["gamma"][i]:04x}\n')
    sources = [relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))]
    objects = output / "compile-obj"
    execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
             "--top-module", "epilogue_tb", "--Mdir", relative(objects),
             *sources, "tests/epilogue_tb.sv"], output, "compile", ["verilator", "--version"])
    text = execute([relative(objects / "Vepilogue_tb"), f"+vectors={relative(vectors)}",
                    f"+observations={relative(observations)}", f"+seed={seed}"],
                   output, "simulation", ["verilator", "--version"])
    if f"SUMMARY epilogue commands={len(fixtures)} " not in text:
        raise AssertionError("missing complete command summary")
    actual = [[] for _ in fixtures]
    completed = set()
    for line in observations.read_text().splitlines():
        row = line.split()
        command = int(row[1])
        if command >= len(fixtures):
            raise AssertionError("unexpected command output")
        c = fixtures[command]
        if row[0] == "C":
            if command in completed or int(row[2]) != c["error"]:
                raise AssertionError("duplicate completion or incorrect error")
            if int(row[3]) != len(actual[command]):
                raise AssertionError("completion output count mismatch")
            completed.add(command)
            continue
        if row[0] != "O" or int(row[2]) != len(actual[command]) or int(row[3], 16) != c["mask"]:
            raise AssertionError("output ordering/slot mismatch")
        bits, enc = int(row[4], 16), int(row[5], 16)
        coordinate = []
        for s in range(4):
            value = (bits >> (32 * s)) & 0xFFFFFFFF
            narrowed = (enc >> (16 * s)) & 65535
            if c["mask"] & (1 << s):
                if narrowed != convert(value, c["fp16"]):
                    raise AssertionError(f"encoded RNE mismatch command={command} slot={s}")
            elif value != 0 or narrowed != 0:
                raise AssertionError("masked nonfinite operand contaminated output")
            coordinate.append(float_value(value))
        actual[command].append(coordinate)
    if len(completed) != len(fixtures):
        raise AssertionError("missing completions")
    comparisons = []
    failures = []
    for command, c in enumerate(fixtures):
        if c["error"]:
            if actual[command]:
                raise AssertionError("invalid command emitted data")
            continue
        if len(actual[command]) != c["length"]:
            raise AssertionError("missing coordinates")
        for slot in range(4):
            if c["mask"] & (1 << slot):
                vector = [coordinate[slot] for coordinate in actual[command]]
                reference = expected(c, slot)
                try:
                    cosine, error = vector_check(vector, reference)
                except AssertionError as exc:
                    aa = sum(x*x for x in vector)
                    rr = sum(x*x for x in reference)
                    cosine = (sum(a*r for a,r in zip(vector, reference)) / math.sqrt(aa*rr)
                              if aa and rr else None)
                    error = max(abs(a-r) for a,r in zip(vector,reference))
                    failures.append(dict(command=command, mode=c["op"], fp16=c["fp16"],
                                         slot=slot, message=str(exc), actual=vector,
                                         reference=reference,
                                         final_rne_reference=[float_value(float_bits(x))
                                                              for x in reference]))
                comparisons.append(dict(command=command, mode=c["op"], fp16=c["fp16"],
                                        slot=slot, cosine=cosine, max_abs_error=error))
    result = dict(status="failed" if failures else "passed", seed=seed, commands=len(fixtures),
                  vectors=len(comparisons), comparisons=comparisons, failures=failures)
    with (output / "result.json").open("x") as out:
        json.dump(result, out, indent=2)
    if failures:
        first = failures[0]
        raise AssertionError(f'{len(failures)} vector failures; first command={first["command"]} '
                             f'mode={first["mode"]} fp16={first["fp16"]} slot={first["slot"]}: '
                             f'{first["message"]}; {relative(output / "result.json")}')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, choices=(17, 89, 2026), default=17)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repair-of", help="prior immutable diagnostic receipt")
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(kind="independent-epilogue-preparation",
                   argv=["python3", "tests/run_epilogue.py", *sys.argv[1:]], cwd=".",
                   start=datetime.now(timezone.utc).isoformat(), timeout=None,
                   source_sha256=hashes(), tool_version=sys.version,
                   stdout=relative(output / "driver.stdout.txt"),
                   stderr=relative(output / "driver.stderr.txt"))
    if args.repair_of:
        receipt["repair_of"] = args.repair_of
    try:
        result = run(args.seed, output)
        summary = {key: value for key, value in result.items() if key != "comparisons"}
        (output / "driver.stdout.txt").write_text(json.dumps(summary) + "\n")
        (output / "driver.stderr.txt").write_text("")
        print(json.dumps(summary), flush=True)
        receipt["exit"] = 0
    except Exception as exc:
        (output / "driver.stdout.txt").write_text("")
        (output / "driver.stderr.txt").write_text(f"{type(exc).__name__}: {exc}\n")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        receipt["exit"] = 1
    receipt["end"] = datetime.now(timezone.utc).isoformat()
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
