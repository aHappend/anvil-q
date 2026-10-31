#!/usr/bin/env python3
"""Portable L1 checks. Each invocation creates a new, source-bound result directory."""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time
import uuid
from decimal import Decimal, localcontext
import struct

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import (BF16, FP16, FP32, add, convert, dequant, multiply, tree,
                       decimal_value, transcendental)

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sources(root=ROOT):
    return sorted(root.glob("rtl/*.sv")) + sorted(root.glob("anvil_q2_ht_reference/rtl/*.sv"))


def hashes(root=ROOT):
    paths = sources(root) + sorted(root.glob("design/*.md"))
    paths += sorted(p for p in (root / "tests").rglob("*")
                    if p.is_file() and "__pycache__" not in p.parts)
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


class Run:
    def __init__(self, stem, preparation=False, repair_of=None):
        suffix = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        base = ROOT / "evidence" / ("preparation" if preparation else "l1")
        self.path = base / f"{stem}-{suffix}-{uuid.uuid4().hex[:8]}"
        self.path.mkdir(parents=True, exist_ok=False)
        self.records = []
        self.receipt = {
            "schema": 1, "kind": "advisory-preparation" if preparation else "l1",
            "argv": [sys.executable if not Path(sys.executable).is_absolute() else "python3",
                     "tests/verify.py", *sys.argv[1:]],
            "cwd": ".", "start_time": now(), "source_hashes": hashes(),
            "commands": self.records, "repair_of": repair_of,
        }
        self.versions = set()

    def relative(self, path):
        return str(Path(path).relative_to(ROOT))

    def tool(self, tool):
        if shutil.which(tool) is None:
            raise RuntimeError(f"missing executable: {tool}")
        if tool not in self.versions:
            self.versions.add(tool)
            args = {"iverilog": ["-V"], "vvp": ["-V"], "verilator": ["--version"],
                    "yosys": ["-V"], "c++": ["--version"]}.get(tool, ["--version"])
            self.command([tool, *args], f"version-{tool}", check=False, timeout=60)

    def command(self, argv, name, cwd=ROOT, timeout=2600, check=True):
        stdout = self.path / f"{len(self.records):03d}-{name}.stdout.txt"
        stderr = stdout.with_name(stdout.name.replace(".stdout.", ".stderr."))
        start = time.monotonic()
        record = {"argv": [str(a) for a in argv], "cwd": self.relative(cwd),
                  "start_time": now(), "timeout_s": timeout,
                  "stdout": self.relative(stdout), "stderr": self.relative(stderr)}
        self.records.append(record)
        with stdout.open("wb") as out, stderr.open("wb") as err:
            try:
                process = subprocess.Popen([str(a) for a in argv], cwd=cwd,
                                           stdout=out, stderr=err, start_new_session=True)
            except OSError as exc:
                record.update(exit_code=None, timed_out=False, error=str(exc), end_time=now())
                raise
            timed_out = False
            while process.poll() is None:
                try:
                    process.wait(timeout=min(30, max(0.01, timeout - (time.monotonic() - start))))
                except subprocess.TimeoutExpired:
                    if time.monotonic() - start >= timeout:
                        import signal
                        os.killpg(process.pid, signal.SIGTERM)
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid, signal.SIGKILL)
                            process.wait()
                        timed_out = True
                    else:
                        print(f"progress: {name}, {int(time.monotonic()-start)}s", flush=True)
        record.update(exit_code=process.returncode, timed_out=timed_out,
                      duration_s=time.monotonic()-start, end_time=now())
        self.save()
        if check and (process.returncode != 0 or timed_out):
            raise RuntimeError(f"{name} failed: exit={process.returncode}, timeout={timed_out}; "
                               f"{self.relative(stdout)}; {self.relative(stderr)}")
        return record, stdout.read_text(errors="replace"), stderr.read_text(errors="replace")

    def save(self):
        (self.path / "receipt.json").write_text(json.dumps(self.receipt, indent=2) + "\n")

    def finish(self, success, reason):
        self.receipt.update(end_time=now(), exit_code=0 if success else 1, reason=reason,
                            source_hashes_unchanged=hashes() == self.receipt["source_hashes"])
        if not self.receipt["source_hashes_unchanged"]:
            self.receipt["exit_code"] = 1
            self.receipt["reason"] += "; source changed during execution"
        self.save()
        print(json.dumps({"exit_code": self.receipt["exit_code"], "reason": self.receipt["reason"],
                          "receipt": self.relative(self.path / "receipt.json")}), flush=True)
        return self.receipt["exit_code"]


def directed(fmt):
    return [0, fmt.sign, 1, fmt.sign | 1, (1 << fmt.fraction) - 1,
            1 << fmt.fraction, (fmt.bias << fmt.fraction),
            (fmt.bias << fmt.fraction) | 1, fmt.infinity - 1,
            fmt.sign | (fmt.infinity - 1), fmt.infinity,
            fmt.sign | fmt.infinity, fmt.nan, fmt.infinity | 1]


def numerical_rows(kind, compact=False):
    rng = random.Random(17)
    if kind == 0:
        for ah in (False, True):
            for bh in (False, True):
                af, bf = (FP16 if ah else BF16), (FP16 if bh else BF16)
                pairs = [(a, b) for a in directed(af) for b in directed(bf)]
                pairs += [(rng.randrange(65536), rng.randrange(65536))
                          for _ in range(10000)]
                for a, b in pairs:
                    yield a, b, 4 | ah | (bh << 1), *multiply(a, b, af, bf)
                for a, b in pairs[:50]:
                    yield a, b, ah | (bh << 1), 0, False
    elif kind in (1, 2):
        pairs = [(a, b) for a in directed(FP32) for b in directed(FP32)]
        pairs += [(rng.getrandbits(32), rng.getrandbits(32)) for _ in range(20000)]
        operation = add if kind == 1 else multiply
        for a, b in pairs:
            yield a, b, 0, *operation(a, b)
    elif kind == 3:
        for half, fmt in ((False, BF16), (True, FP16)):
            for value in range(65536):
                yield value, 0, 2 | half, *convert(value, fmt, FP32)
            # Every destination encoding's adjacent midpoint, on both parities.
            for value in range(fmt.infinity):
                low, _ = convert(value, fmt, FP32)
                high, _ = convert(value + 1, fmt, FP32)
                midpoint = add(low, high)[0]
                midpoint = multiply(midpoint, 0x3f000000)[0]
                for source in (midpoint - 1 if midpoint else 0, midpoint, midpoint + 1):
                    yield source, 0, half, *convert(source, FP32, fmt)
            for value in directed(FP32) + [rng.getrandbits(32) for _ in range(10000)]:
                yield value, 0, half, *convert(value, FP32, fmt)
    else:
        scales = [0, 0x8000, 1, 63, 64, 127, 128, 0x3f00, 0x3f80,
                  0x3f81, 0x7f7f, 0xbf80, 0x7f80, 0x7fc0]
        for fmt, limit in ((2, 16), (3, 4)):
            for q in range(limit):
                for z in range(limit):
                    for scale in scales:
                        yield q, scale, 64 | (z << 2) | fmt, *dequant(q, z, scale)
                        yield q, scale, (z << 2) | fmt, 0, False
        for half, fmt in ((False, BF16), (True, FP16)):
            for value in range(65536):
                result, error = convert(value, fmt, fmt)
                yield value, 0, 64 | half, result, error


def simulate(run, tb, parameters=None, simulator="iverilog", root=ROOT, plusargs=()):
    parameters = parameters or {}
    name = tb.stem + "-" + "-".join(f"{k}{v}" for k, v in parameters.items())
    paths = [str(p.relative_to(ROOT)) for p in sources(root)]
    paths.append(str(tb.relative_to(ROOT)))
    if simulator == "iverilog":
        run.tool("iverilog")
        run.tool("vvp")
        binary = run.path / (name + ".vvp")
        run.command(["iverilog", "-g2012", "-Wall", "-s", tb.stem, "-o",
                     run.relative(binary),
                     *[f"-P{tb.stem}.{k}={v}" for k, v in parameters.items()], *paths],
                    name + "-compile")
        record, stdout, stderr = run.command(
            ["vvp", run.relative(binary), *plusargs], name + "-simulate", timeout=600)
        binary.unlink()
    else:
        run.tool("verilator")
        run.tool("c++")
        obj = run.path / (name + "-compile-obj")
        try:
            run.command(["verilator", "--binary", "--timing", "-Wno-fatal",
                         "--top-module", tb.stem, "--Mdir", run.relative(obj), "-j", "2",
                         *[f"-G{k}={v}" for k, v in parameters.items()], *paths],
                        name + "-compile")
            record, stdout, stderr = run.command(
                [run.relative(obj / ("V" + tb.stem)), *plusargs], name + "-simulate")
        finally:
            if obj.exists():
                shutil.rmtree(obj)
    if "SUMMARY " not in stdout:
        raise RuntimeError(f"{name}: no executed comparison summary")
    return stdout


def numerics(run, kinds=range(5), simulator="verilator", compact=False):
    for kind in kinds:
        vectors = run.path / f"numerics-{kind}.txt"
        count = 0
        payload = run.path / f"numerics-{kind}.body"
        with payload.open("w") as stream:
            for a, b, aux, expected, error in numerical_rows(kind, compact):
                stream.write(f"{a:08x} {b:08x} {aux:08x} {expected:08x} {int(error)}\n")
                count += 1
        with vectors.open("w") as stream, payload.open() as body:
            stream.write(f"{count}\n")
            shutil.copyfileobj(body, stream)
        payload.unlink()
        if simulator == "iverilog" and count > 30000:
            # Full finite-space coverage is compiled; Icarus retains a bounded smoke.
            lines = vectors.read_text().splitlines()[1:1025]
            vectors.write_text(f"{len(lines)}\n" + "\n".join(lines) + "\n")
            count = len(lines)
        stdout = simulate(run, ROOT / "tests/numerics_tb.sv", {"KIND": kind},
                          simulator=simulator, plusargs=["+vectors=" + run.relative(vectors)])
        run.receipt.setdefault("numerics", []).append(
            {"kind": kind, "vectors": count, "sha256": hashlib.sha256(vectors.read_bytes()).hexdigest(),
             "summary": stdout.strip(), "simulator": simulator})
        run.save()


def pack(values, width):
    return sum(value << (width * index) for index, value in enumerate(values))


def tree_vectors(run, layers, maximum):
    pointer = 0
    records = []
    coverage = set()
    rng = random.Random(89)
    cases = []
    for count in (1, 2, 4):
        parents = [0, 0, 1, 2]
        for accepted in range(1, count + 1):
            ids = [10, 11, 12, 13]
            targets = [11, 12, 13, 14]
            if accepted < count:
                targets[accepted - 1] = 999
            cases.append((count, ids, parents, targets, "length-" + str(accepted)))
    cases += [
        (4, [10, 11, 12, 13], [0, 0, 0, 2], [12, 99, 13, 20], "branch-noncontiguous"),
        (4, [10, 11, 11, 13], [0, 0, 0, 2], [11, 99, 13, 20], "duplicate-low-index"),
        (4, [10, 11, 12, 13], [0, 0, 3, 2], [11, 12, 13, 20], "bad-parent"),
        (3, [10, 11, 12, 13], [0, 0, 1, 2], [11, 12, 13, 20], "bad-count"),
        (0, [10, 11, 12, 13], [0, 0, 1, 2], [11, 12, 13, 20], "zero-count"),
    ]

    def append(case, position, new, complete, errors, cancel=-1, hold=3):
        nonlocal pointer
        count, ids, parents, targets, label = case
        result = tree(count, ids, parents, targets, position, pointer, complete, errors,
                      layers, maximum, new)
        accepted, mask, next_token, next_position, error = result
        records.append((count, pack(ids, 32), pack(parents, 2), pack(targets, 32),
                        position, int(new), complete, errors, accepted, mask,
                        next_token, next_position, int(error), cancel, hold))
        if cancel >= 10:
            pointer = 0
        elif cancel == -1 and not error:
            pointer = next_position
            coverage.add(label)
        elif cancel == -1:
            coverage.add("error-" + label)

    full = pack([(1 << layers) - 1] * 4, 28)
    for case in cases:
        append(case, 0, True, full, 0)
    for phase in range(1, 7):
        append(cases[0], 0, True, full, 0, cancel=phase)
        append(cases[0], 0, True, full, 0, cancel=10 + phase)
    for slot in range(4):
        for layer in {0, layers - 1}:
            append(cases[6], 0, True, full & ~(1 << (28 * slot + layer)), 0)
        append(cases[6], 0, True, full, 1 << slot)
    append(cases[0], maximum - 1, True, full, 0)
    append(cases[0], pointer, False, full, 0)
    append(cases[6], maximum - 1, True, full, 0)
    append(cases[0], maximum + 1, True, full, 0)
    append(cases[0], 0, False, full, 0)
    for _ in range(200):
        case = rng.choice(cases)
        append(case, rng.randrange(maximum), bool(rng.randrange(2)), full, 0,
               hold=rng.randrange(1, 6))
    path = run.path / f"tree-l{layers}-s{maximum}.txt"
    with path.open("w") as stream:
        stream.write(f"{len(records)}\n")
        for row in records:
            stream.write(" ".join(f"{n:x}" for n in row[:5]) + f" {row[5]:b} " +
                         " ".join(f"{n:x}" for n in row[6:12]) +
                         f" {row[12]:b} {row[13]} {row[14]}\n")
    return path, coverage


def tree_behavior(run, simulator):
    for layers, maximum in ((1, 5), (28, 5), (28, 32768)):
        path, coverage = tree_vectors(run, layers, maximum)
        stdout = simulate(run, ROOT / "tests/tree_tb.sv",
                          {"NUM_LAYERS": layers, "MAX_SEQ_LEN": maximum},
                          simulator=simulator, plusargs=["+vectors=" + run.relative(path)])
        run.receipt.setdefault("tree", []).append(
            {"layers": layers, "maximum": maximum, "cases": sorted(coverage),
             "summary": stdout.strip(), "simulator": simulator})
        run.save()


def dma_vectors(run):
    rng = random.Random(211)
    rows = []
    for fmt in range(4):
        for offset in (0, 1, 31, 32, 63):
            for pattern in ("dense", "union", "skip", "tiny", "partial"):
                for fault, cancel in ((-1, 0), (0, 0), (-1, 1), (-1, 2), (-1, 3), (-1, 4)):
                    if pattern == "skip" and (fault >= 0 or cancel in (2, 3)):
                        continue
                    if pattern != "dense" and (fault >= 0 or cancel > 0):
                        continue
                    image = bytearray(rng.getrandbits(8) for _ in range(320))
                    weights = [rng.choice([0, 1, 0x3f00, 0x3f80, 0xbf80]) for _ in range(128)]
                    codes = [rng.randrange(16 if fmt == 2 else 4) for _ in range(128)]
                    zeros = [rng.randrange(16 if fmt == 2 else 4) for _ in range(128)]
                    scales = [rng.choice([1, 64, 0x3f00, 0x3f80, 0x3f81]) for _ in range(128)]
                    if fmt < 2:
                        if fmt == 1:
                            weights = [convert(w, BF16, FP16)[0] for w in weights]
                        payload = pack(weights, 16).to_bytes(256, "little")
                    else:
                        payload = pack(codes, 4 if fmt == 2 else 2).to_bytes(64 if fmt == 2 else 32, "little")
                    image[offset:offset+len(payload)] = payload
                    tokens = 15
                    sparse = pattern != "dense"
                    keeps = [pattern != "partial" or j % 128 < 9 for j in range(512)]
                    acts = [0x3f80 if (pattern == "dense" or
                                     (pattern == "union" and (j % 128) % 4 == j // 128) or
                                     (pattern == "tiny" and j == 127) or pattern == "partial")
                            else rng.choice([0, 0x8000]) for j in range(512)]
                    if pattern == "tiny":
                        acts[127] = 1  # Minimum subnormal is nonzero, never threshold it.
                    needed = [any(keeps[128*t+j] and (not sparse or acts[128*t+j] & 0x7fff)
                                  for t in range(4)) for j in range(128)]
                    union_keep = [keeps[j] and (not sparse or bool(acts[j] & 0x7fff))
                                  for j in range(512)]
                    beats = set()
                    for j, required in enumerate(needed):
                        if required:
                            first = offset + (j*2 if fmt < 2 else j >> (1 if fmt == 2 else 2))
                            beats.add(first // 64)
                            if fmt < 2:
                                beats.add((first+1) // 64)
                    if fault >= 0:
                        fault = min(beats)
                    expected = []
                    error = fault >= 0
                    for j, required in enumerate(needed):
                        if fmt < 2:
                            value, lane_error = convert(weights[j], FP16 if fmt == 1 else BF16,
                                                        FP16 if fmt == 1 else BF16) if required else (0, False)
                        else:
                            value, lane_error = dequant(codes[j], zeros[j], scales[j], required)
                        expected.append(value)
                        error |= lane_error
                    if error:
                        expected = [0] * 128
                        union_keep = [False] * 512
                    rows.append((fmt, int(sparse), tokens, pack(acts, 16), pack(keeps, 1),
                                 0x1000+offset, pack(zeros, 4), pack(scales, 16),
                                 int.from_bytes(image, "little"), sum(1 << b for b in beats),
                                 pack(expected, 16), pack(union_keep, 1), int(not beats and not error),
                                 int(error), fault, cancel))
    path = run.path / "dma-vectors.txt"
    with path.open("w") as stream:
        stream.write(f"{len(rows)}\n")
        for row in rows:
            stream.write(f"{row[0]:x} {row[1]:b} " +
                         " ".join(f"{n:x}" for n in row[2:12]) +
                         f" {row[12]:b} {row[13]:b} {row[14]} {row[15]}\n")
    return path


def dma_behavior(run, simulator):
    path = dma_vectors(run)
    stdout = simulate(run, ROOT / "tests/dma_tb.sv", simulator=simulator,
                      plusargs=["+vectors=" + run.relative(path)])
    run.receipt["dma"] = {"summary": stdout.strip(), "simulator": simulator}
    run.save()


def scalar_numerics(run, simulator):
    rng = random.Random(211)
    rows = []
    def fp(value):
        return struct.unpack("<I", struct.pack("<f", value))[0]
    for op in (2, 3, 4, 5):
        if op in (2, 3):
            values = [fp(2.0 ** (exponent / 3)) for exponent in range(-90, 91)]
            values += [fp(10 ** rng.uniform(-12, 12)) for _ in range(500)]
            if op == 2:
                values += [bits | 0x80000000 for bits in values[:200]]
        else:
            values = [fp(x / 4) for x in range(-352, 353)]
            values += [fp(rng.uniform(-80, 80)) for _ in range(500)]
            values += [0, 0x80000000, 1, 0x80000001]
        for bits in values:
            rows.append((op, bits, 0, 1 + rng.randrange(4), -1))
        for cancel in (1, 2, 7, 40):
            rows.append((op, fp(1.25), 0, 3, cancel))
    path = run.path / "scalar-vectors.txt"
    with path.open("w") as stream:
        stream.write(f"{len(rows)}\n")
        for op, a, b, hold, cancel in rows:
            stream.write(f"{op:x} {a:08x} {b:08x} {hold} {cancel}\n")
    stdout = simulate(run, ROOT / "tests/scalar_tb.sv", simulator=simulator,
                      plusargs=["+vectors=" + run.relative(path)])
    observed = {}
    maximum_relative = {}
    maximum_absolute = {}
    for line in stdout.splitlines():
        if not line.startswith("RESULT "):
            continue
        _, index, encoded, error = line.split()
        index, encoded = int(index), int(encoded, 16)
        if index in observed:
            raise RuntimeError(f"duplicate scalar result {index}")
        observed[index] = encoded
        op, a, _, _, cancel = rows[index]
        if cancel != -1 or error != "0":
            raise RuntimeError(f"scalar unexpected response/error row={index} operation={op}")
        actual = decimal_value(encoded)
        expected = transcendental(op, a)
        with localcontext() as context:
            context.prec = 100
            absolute = abs(actual - expected)
            relative = absolute / abs(expected)
            if not actual.is_finite() or relative > Decimal("2e-5") or (
                abs(expected) <= Decimal("0.01") and absolute > Decimal("2e-7")
            ):
                raise RuntimeError(f"scalar accuracy row={index} op={op} input={a:08x} "
                                   f"actual={actual} expected={expected} "
                                   f"absolute={absolute} relative={relative}")
        maximum_relative[op] = max(maximum_relative.get(op, Decimal(0)), relative)
        maximum_absolute[op] = max(maximum_absolute.get(op, Decimal(0)), absolute)
    if set(observed) != {i for i, row in enumerate(rows) if row[-1] == -1}:
        raise RuntimeError("scalar missing or additional results")
    run.receipt["scalar"] = {
        "compared": len(observed), "precision_decimal_digits": 100,
        "max_relative_error": {k: str(v) for k, v in maximum_relative.items()},
        "max_absolute_error": {k: str(v) for k, v in maximum_absolute.items()},
        "summary": next(line for line in stdout.splitlines() if line.startswith("SUMMARY ")),
    }
    run.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("check", choices=["numerics", "behavior", "mutations", "synthesis",
                                          "benchmarks", "reproduce"])
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--repair-of")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--kind", type=int, choices=range(5))
    parser.add_argument("--simulator", choices=["iverilog", "verilator"], default="verilator")
    parser.add_argument("--leaf", choices=["tree", "dma", "scalar", "all"], default="all")
    args = parser.parse_args()
    run = Run(args.check, args.preparation, args.repair_of)
    try:
        if args.check == "numerics":
            numerics(run, [args.kind] if args.kind is not None else range(5),
                     args.simulator, args.compact)
        elif args.check == "behavior":
            if args.leaf in ("tree", "all"):
                tree_behavior(run, args.simulator)
            if args.leaf in ("dma", "all"):
                dma_behavior(run, args.simulator)
            if args.leaf in ("scalar", "all"):
                scalar_numerics(run, args.simulator)
        else:
            raise RuntimeError(f"{args.check}: verification implementation not yet completed")
    except Exception as exc:
        return run.finish(False, f"{type(exc).__name__}: {exc}")
    return run.finish(True, "all requested comparisons passed")


if __name__ == "__main__":
    sys.exit(main())
