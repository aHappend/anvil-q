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
import threading
import uuid
from decimal import Decimal, localcontext
import struct

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import (BF16, FP16, FP32, add, convert, dequant, multiply, tree,
                       decimal_value, transcendental, dot, kv_encode, kv_decode, decode, encode)

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
        self.lock = threading.RLock()
        self.receipt = {
            "schema": 1, "kind": "advisory-preparation" if preparation else "l1",
            "argv": [sys.executable if not Path(sys.executable).is_absolute() else "python3",
                     "tests/verify.py", *sys.argv[1:]],
            "cwd": ".", "start_time": now(), "source_hashes": hashes(),
            "commands": self.records, "repair_of": repair_of,
        }
        self.versions = set()
        self.started = time.monotonic()
        self.budget_s = min(2670, float(os.environ.get("ANVIL_L1_BUDGET_SECONDS", "2670")))

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

    def command(self, argv, name, cwd=ROOT, timeout=2600, check=True, environment=None):
        timeout = min(timeout, max(0.01, self.budget_s - (time.monotonic() - self.started)))
        with self.lock:
            stdout = self.path / f"{len(self.records):03d}-{name}.stdout.txt"
            stderr = stdout.with_name(stdout.name.replace(".stdout.", ".stderr."))
            start = time.monotonic()
            record = {"argv": [str(a) for a in argv], "cwd": self.relative(cwd),
                      "start_time": now(), "timeout_s": timeout,
                      "stdout": self.relative(stdout), "stderr": self.relative(stderr)}
            if environment:
                record["environment_overrides"] = environment
            self.records.append(record)
        with stdout.open("wb") as out, stderr.open("wb") as err:
            try:
                process = subprocess.Popen([str(a) for a in argv], cwd=cwd,
                                           stdout=out, stderr=err, start_new_session=True,
                                           env={**os.environ, **(environment or {})})
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
        with self.lock:
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
                _, low, low_power, _ = decode(value, fmt)
                if value == fmt.infinity - 1:
                    high, high_power = low + 1, low_power
                else:
                    _, high, high_power, _ = decode(value + 1, fmt)
                power = min(low_power, high_power)
                total = (low << (low_power-power)) + (high << (high_power-power))
                midpoint = encode(False, total, power-1, FP32)[0]
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


class DetectedDefect(Exception):
    """An executed simulation reached the designated independent assertion."""


def simulate(run, tb, parameters=None, simulator="iverilog", root=None, plusargs=()):
    root = root or getattr(run, "design_root", ROOT)
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
        # Verilator 5.020 V3Gate crashes on singleton indexed validity vectors.
        optimizer_flags = (["-fno-gate"] if tb.stem in
                           ("activation_tb", "activation_startup_tb") else [])
        try:
            run.command(["verilator", "--binary", "--timing", "-Wno-fatal",
                         *optimizer_flags,
                         "--unroll-count", "1024", "--unroll-stmts", "100000",
                         "-CFLAGS", "-O0",
                         "--top-module", tb.stem, "--Mdir", run.relative(obj), "-j", "2",
                         *[f"-G{k}={v}" for k, v in parameters.items()], *paths],
                        name + "-compile")
            record, stdout, stderr = run.command(
                [run.relative(obj / ("V" + tb.stem)), *plusargs], name + "-simulate",
                check=not bool(getattr(run, "expected_failure", None)))
        finally:
            if obj.exists():
                shutil.rmtree(obj)
    expected_failure = getattr(run, "expected_failure", None)
    if expected_failure:
        if (record["exit_code"] != 0 and not record["timed_out"] and
                any(marker in stdout + stderr for marker in expected_failure)):
            run.receipt["detected_defect"] = {
                "assertions": [marker for marker in expected_failure
                               if marker in stdout + stderr],
                "command_index": len(run.records) - 1,
            }
            run.save()
            raise DetectedDefect("designated independent assertion rejected mutated RTL")
        raise RuntimeError(f"{name}: mutation survived or failed without its designated assertion")
    if "SUMMARY " not in stdout:
        raise RuntimeError(f"{name}: no executed comparison summary")
    return stdout


def numerics(run, kinds=range(5), simulator="verilator", compact=False,
             vector_prefix="numerics"):
    for kind in kinds:
        vectors = run.path / f"{vector_prefix}-{kind}.txt"
        count = 0
        payload = run.path / f"{vector_prefix}-{kind}.body"
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


def mac_behavior(run, simulator):
    rng = random.Random(17)
    path = run.path / "mac-vectors.txt"
    count = 64 if simulator == "iverilog" else 320
    with path.open("w") as stream:
        stream.write(f"{count}\n")
        for index in range(count):
            ah, bh = bool(index & 1), bool(index & 2)
            af, bf = FP16 if ah else BF16, FP16 if bh else BF16
            mask = index % 16
            pool_a = directed(af) if index % 11 == 3 else [
                0, af.sign, 1, af.bias << af.fraction,
                (af.bias << af.fraction) | 3, af.sign | ((af.bias+1) << af.fraction)]
            pool_b = directed(bf) if index % 13 == 4 else [
                0, bf.sign, 1, bf.bias << bf.fraction, bf.sign | (bf.bias << bf.fraction)]
            activations = [rng.choice(pool_a) for _ in range(512)]
            weights = [rng.choice(pool_b) for _ in range(128)]
            keep = [rng.randrange(4) != 0 and (index % 9 != 0 or j % 128 < 9)
                    for j in range(512)]
            biases = [rng.choice([0, 0x80000000, 0x3f800000, 0xbf800000])
                      for _ in range(4)]
            sums, error = [], False
            for slot in range(4):
                if mask & (1 << slot):
                    result, failed = dot(activations[128*slot:128*(slot+1)], weights,
                                         keep[128*slot:128*(slot+1)], af, bf, biases[slot])
                    error |= failed
                else:
                    result = 0
                sums.append(result)
            stream.write(f"{int(ah):b} {int(bh):b} {mask:x} {pack(keep,1):x} "
                         f"{pack(activations,16):x} {pack(weights,16):x} "
                         f"{pack(biases,32):x} {pack(sums,32):x} {int(error):b}\n")
    stdout = simulate(run, ROOT / "tests/mac_tb.sv", simulator=simulator,
                      plusargs=["+vectors=" + run.relative(path)])
    run.receipt["mac"] = {"summary": stdout.strip(), "simulator": simulator}
    run.save()


def codec_behavior(run, simulator):
    rng = random.Random(89)
    blocks = (1, 2, 16, 128) if simulator == "verilator" else (1, 2, 16)
    for words in blocks:
        rows = []
        samples = [[0] * words, [0x8000] * words]
        for maximum in (1, 2, 63, 64, 65, 127, 128, 0x3f00, 0x3f80, 0x3f81,
                        0x4000, 0x7f7f):
            samples += [[maximum] * words, [maximum | 0x8000] * words,
                        [maximum if i % 2 else maximum | 0x8000 for i in range(words)]]
        for _ in range(100 if words < 128 else 20):
            samples.append([rng.randrange(0x7f80) | (rng.randrange(2) << 15)
                            for _ in range(words)])
        samples += [[0x7f80] * words, [0x7fc0] * words, [0xff80] * words]
        for int8 in (False, True):
            length = words + 2 if int8 else words * 2
            for values in samples:
                record, decoded, error = kv_encode(values, int8)
                rows.append((1, int(int8), pack(values, 16), 0,
                             0 if error else pack(decoded, 16), 0 if error else record,
                             length, int(error), -1))
                if not error:
                    decoded, error = kv_decode(record, words, int8)
                    rows.append((0, int(int8), 0, record,
                                 0 if error else pack(decoded, 16), 0 if error else record,
                                 length, int(error), -1))
        for scale in (0, 0x8000, 0xbf80, 0x7f80, 0x7fc0, 0x3f80):
            record = scale | (0x80 << 16)
            rows.append((0, 1, 0, record, 0, 0, words + 2, 1, -1))
        for cancel in (1, 2, 7, 10):
            values = [0x3f80] * words
            record, decoded, error = kv_encode(values, True)
            rows.append((1, 1, pack(values, 16), 0, pack(decoded, 16), record,
                         words + 2, int(error), cancel))
        path = run.path / f"codec-{words}.txt"
        with path.open("w") as stream:
            stream.write(f"{len(rows)}\n")
            for row in rows:
                stream.write(f"{row[0]:b} {row[1]:b} " +
                             " ".join(f"{n:x}" for n in row[2:7]) +
                             f" {row[7]:b} {row[8]}\n")
        stdout = simulate(run, ROOT / "tests/codec_tb.sv", {"CACHE_BLOCK": words},
                          simulator=simulator, plusargs=["+vectors=" + run.relative(path)])
        run.receipt.setdefault("codec", []).append(
            {"words": words, "summary": stdout.strip(), "simulator": simulator})
        run.save()


def top_fixture(run, stem="compact-model", fp16=False, weight_bits=16,
                sparse=False, int8=False, model=None):
    memory = bytearray(131072)
    descriptors = [bytes(64) for _ in range(32)]
    cursor = 0x1000

    def allocate(payload):
        nonlocal cursor
        address = cursor
        memory[address:address+len(payload)] = payload
        cursor = ((cursor+len(payload)+63)//64)*64
        return address

    for index in (0, 1, 2, 3, *range(16, 28)):
        rows, columns = (1, 8)
        if index in (0, 1):
            rows = 2
        elif index == 3:
            rows = 5
        elif index in range(16, 23):
            rows = 8
        values = [0] * (rows * columns)
        if index == 0:
            values = [0x3f80] * len(values)
        elif index == 1:
            values[:8] = [0x3f80] * 8
        elif index == 3:
            values = [0x3f80 if c % 2 == 0 else 0
                      for _ in range(rows) for c in range(columns)]
        elif index in (2, 23, 24):
            values = [0x3f80] * len(values)
        if model is not None:
            values = model[index]
            if len(values) != rows * columns:
                raise ValueError(f"descriptor {index}: wrong independent fixture shape")
        quantized = weight_bits != 16 and (index == 1 or 16 <= index <= 22)
        if quantized:
            scale = 0x3e80 if model is not None else 0x3f80
            codes = ([int(decimal_value(value, BF16) * 4) + 1 for value in values]
                     if model is not None else [2 if value == 0x3f80 else 1 for value in values])
            if any(code < 0 or code >= 1 << weight_bits for code in codes):
                raise ValueError("fixture weight is not representable at the selected width")
            row_stride = (columns * weight_bits + 7) // 8
            payload = pack(codes, weight_bits).to_bytes(rows * row_stride, "little")
            base = allocate(payload)
            zero_stride = (columns * weight_bits + 7) // 8  # GROUP_SIZE=1.
            zeros = pack([1] * (rows * columns), weight_bits).to_bytes(
                rows * zero_stride, "little")
            zero_base = allocate(zeros)
            scale_base = allocate(scale.to_bytes(2, "little") * (rows * columns))
            scale_stride = 2 * columns
            flags = 0x100 if weight_bits == 4 else 0x103
        else:
            encoded = [convert(value, BF16, FP16)[0] for value in values] if fp16 else values
            payload = pack(encoded, 16).to_bytes(2 * len(values), "little")
            base = allocate(payload)
            zero_base = scale_base = zero_stride = scale_stride = 0
            row_stride = 2 * columns
            flags = 0x102 if fp16 else 0x101
        descriptors[index] = struct.pack(
            "<QQQQIIIIIIQ", base, len(payload), zero_base, scale_base,
            rows, columns, row_stride, zero_stride, scale_stride, flags, 0)
    mode = (2 if fp16 else 1) | ({16: 0, 4: 4, 2: 8}[weight_bits])
    mode |= (16 if sparse else 0) | (32 if int8 else 0)
    config = ([(0x40, mode)] if mode != 1 else []) + [
        (0x44, 4), (0x18, 0x10000), (0x1c, 0), (0x20, 4096), (0x24, 0)]
    for index, descriptor in enumerate(descriptors):
        config.extend((0x1000 + 64*index + 4*word, value)
                      for word, value in enumerate(struct.unpack("<16I", descriptor)))
    image_directory = run.path / "checkpoint-images"
    image_directory.mkdir(exist_ok=True)
    image = image_directory / f"{stem}.hex"
    image.write_text("\n".join(f"{byte:02x}" for byte in memory) + "\n")
    cfg = run.path / f"{stem}-config.txt"
    cfg.write_text(f"{len(config)}\n" + "\n".join(f"{a:04x} {b:08x}" for a, b in config) + "\n")
    return image, cfg


def top_behavior(run, simulator, stem="compact-model", result_key="top_smoke",
                 fp16=False, weight_bits=16, sparse=False, int8=False):
    image, cfg = top_fixture(run, stem, fp16, weight_bits, sparse, int8)
    stdout = simulate(run, ROOT / "tests/top_tb.sv", simulator=simulator,
                      plusargs=["+image=" + run.relative(image), "+config=" + run.relative(cfg)])
    run.receipt[result_key] = {
        "fixture": "analytical residual-identity model: zero projections, unit embeddings/gamma, head rows one/zero",
        "scope": "compact architectural smoke, not official-model fidelity or benchmark acceptance",
        "mode": {"activation": "FP16" if fp16 else "BF16", "weight_bits": weight_bits,
                 "sparse": sparse, "int8_kv": int8},
        "summary": stdout.strip(), "simulator": simulator,
    }
    run.save()


def kv_store_behavior(run, simulator):
    for words, int8 in ((2, False), (2, True), (1, True)):
        rows = []
        records = 16 // words
        decoded = {}

        def append(op, x=0, y=0, z=0, fault=0, data=0, record=0):
            rows.append((op, x, y, z, fault, data, record))

        def begin(count=1, position=3, fresh=False):
            append(0, count, position, int(fresh) | (int(int8) << 1))

        def write(slot, ordinal, generation=0, fault=False, cancel=False):
            values = [0x3f00 + 128*slot + 7*ordinal + i + 19*generation
                      for i in range(words)]
            encoded, result, failed = kv_encode(values, int8)
            if failed:
                raise RuntimeError("invalid KV-store fixture")
            append(4 if cancel else 1, slot, ordinal, fault=int(fault),
                   data=pack(values, 16), record=encoded)
            decoded[slot, ordinal] = pack(result, 16)

        def read(slot, position, source_slot):
            for ordinal in range(records):
                append(2, slot, position, ordinal, data=decoded[source_slot, ordinal])

        begin(4, 0, True)
        for slot in range(4):
            for ordinal in range(records):
                write(slot, ordinal)
        # Node 3 descends from node 2, not its same-depth sibling node 1.
        read(3, 0, 0)
        read(3, 1, 2)
        read(1, 1, 1)
        read(3, 2, 3)
        append(3, 3, 0b1101, 7)
        begin()
        for position, source_slot in enumerate((0, 2, 3)):
            read(0, position, source_slot)
        # Provisional writes must not overwrite previously committed token zero.
        saved = dict(decoded)
        for ordinal in range(records):
            write(0, ordinal, generation=1)
        append(5)
        decoded = dict(saved)
        begin()
        for position, source_slot in enumerate((0, 2, 3)):
            read(0, position, source_slot)
        # Missing acknowledgements/completions cannot publish a pointer or data.
        append(3, fault=1)
        begin()
        write(0, 0, generation=2, fault=True)
        decoded = dict(saved)
        append(3, fault=1)
        begin()
        for position, source_slot in enumerate((0, 2, 3)):
            read(0, position, source_slot)
        write(0, 0, generation=3, cancel=True)
        decoded = dict(saved)
        begin()
        for position, source_slot in enumerate((0, 2, 3)):
            read(0, position, source_slot)
        append(5)
        path = run.path / f"kv-store-b{words}-int8{int(int8)}.txt"
        with path.open("w") as stream:
            stream.write(f"{len(rows)}\n")
            for op, x, y, z, fault, data, record in rows:
                stream.write(f"{op} {x} {y} {z} {fault} {data:x} {record:x}\n")
        stdout = simulate(run, ROOT / "tests/kv_store_tb.sv", {"CACHE_BLOCK": words},
                          simulator=simulator, plusargs=["+vectors=" + run.relative(path)])
        run.receipt.setdefault("kv_store", []).append({
            "cache_block": words, "int8": int8, "transactions": len(rows),
            "summary": stdout.strip(), "simulator": simulator,
        })
        run.save()


def activation_behavior(run, simulator):
    if simulator == "verilator":
        simulate(run, ROOT / "tests/activation_startup_tb.sv", simulator="iverilog")
    configurations = ((1, 1, 17), (136, 2, 89), (256, 2, 211))
    for words, vectors, seed in configurations:
        simulate(run, ROOT / "tests/activation_startup_tb.sv", {"MAX_WORDS": words},
                 simulator=simulator)
        stdout = simulate(run, ROOT / "tests/activation_tb.sv",
                          {"MAX_WORDS": words, "VECTOR_COUNT": vectors, "SEED": seed},
                          simulator=simulator)
        run.receipt.setdefault("activation", []).append({
            "words": words, "vectors": vectors, "seed": seed,
            "summary": stdout.strip(), "simulator": simulator,
        })
        run.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("check", choices=["numerics", "behavior", "mutations", "synthesis",
                                          "benchmarks", "reproduce"])
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--repair-of")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--kind", type=int, choices=range(5))
    parser.add_argument("--mutation", help="run one named disposable defect-sensitivity case")
    parser.add_argument("--reproduction-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--simulator", choices=["iverilog", "verilator"], default="verilator")
    parser.add_argument("--leaf", choices=["tree", "dma", "scalar", "mac", "codec", "kv",
                                          "activation", "activation-startup", "parameters",
                                          "top", "top-mixed", "top-matrix", "all"], default="all")
    args = parser.parse_args()
    run = Run(args.check, args.preparation, args.repair_of)
    try:
        if args.check == "numerics":
            if args.kind is None and args.simulator == "verilator":
                numerics(run, range(5), "iverilog", True)
            numerics(run, [args.kind] if args.kind is not None else range(5),
                     args.simulator, args.compact)
        elif args.check == "behavior":
            if args.leaf in ("parameters", "all"):
                from parameters import execute
                execute(run)
            if args.leaf in ("tree", "all"):
                tree_behavior(run, args.simulator)
            if args.leaf in ("dma", "all"):
                dma_behavior(run, args.simulator)
            if args.leaf in ("scalar", "all"):
                scalar_numerics(run, "verilator")
            if args.leaf in ("mac", "all"):
                mac_behavior(run, args.simulator)
            if args.leaf in ("codec", "all"):
                codec_behavior(run, args.simulator)
            if args.leaf in ("kv", "all"):
                kv_store_behavior(run, args.simulator)
            if args.leaf in ("activation", "all"):
                activation_behavior(run, args.simulator)
            if args.leaf == "activation-startup":
                stdout = simulate(run, ROOT / "tests/activation_startup_tb.sv",
                                  simulator=args.simulator)
                run.receipt["activation_startup"] = stdout.strip()
            if args.leaf == "top":
                top_behavior(run, "verilator")
            if args.leaf == "top-mixed":
                top_behavior(run, "verilator", stem="fp16-w2-sparse-int8-model",
                             result_key="top_mixed_smoke", fp16=True, weight_bits=2,
                             sparse=True, int8=True)
            if args.leaf in ("top-matrix", "all"):
                from integrated import execute
                execute(run)
        elif args.check == "synthesis":
            from synthesis import execute
            execute(run, ROOT, sources(), compact=args.compact)
        elif args.check == "mutations":
            from mutations import execute
            execute(run, args.mutation)
        elif args.check == "reproduce":
            from reproduction import execute, child
            (child if args.reproduction_child else execute)(run)
        elif args.check == "benchmarks":
            from benchmarks import execute
            execute(run)
    except Exception as exc:
        return run.finish(False, f"{type(exc).__name__}: {exc}")
    return run.finish(True, "all requested comparisons passed")


if __name__ == "__main__":
    sys.exit(main())
