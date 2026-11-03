"""Arbitrary-integer scalar expectations and independently specified cycle tables."""

from math import isqrt
import random

from execution import sha256, write_json
from reference import exp_q24, silu


def scalar_vectors(path, unit, seed):
    rng = random.Random(seed)
    cases = []
    if unit == 0:
        pairs = [(0, 1), (1, 1), ((1 << 129) - 1, 1), ((1 << 129) - 1, (1 << 64) - 1),
                 (1 << 128, 1 << 63), (0, 0), (123, 0), (123, 1000)]
        pairs += [(rng.getrandbits(129), rng.getrandbits(64)) for _ in range(100)]
        for a, b in pairs:
            q, r = divmod(a, b) if b else (0, 0)
            cases.append([a, b, q, r, int(b == 0), 129 * (5 + 2) if b else 0, 0])
    elif unit == 1:
        values = [0, 1, 2, 3, 4, (1 << 128) - 1]
        for root in (2, 3, 65535, 1 << 32, (1 << 64) - 1):
            values += [root * root - 1, root * root, min((1 << 128) - 1, root * root + 1)]
        values += [rng.getrandbits(128) for _ in range(100)]
        cases = [[a, 0, isqrt(a), a - isqrt(a) ** 2, 0, 448, 0] for a in values]
    elif unit in (2, 3):
        values = [-1048577, -1048576, -1048575, -1, 0, 1, 65536, -65536,
                  -2147483648, 2147483647]
        values += [rng.randrange(-1100000, 1100000) for _ in range(100)]
        if unit == 2:
            values += [-(1 << 63), (1 << 63) - 1]
        for a in values:
            latency = (1 if a < -1048576 or a >= 0 else 917) if unit == 2 else (
                203 if a == 0 or abs(a) > 1048576 else 1119)
            value = exp_q24(a) if unit == 2 else silu(a)
            cases.append([a & ((1 << (64 if unit == 2 else 32)) - 1), 0,
                          value & 0xffffffff, 0, 0, latency, 0])
    elif unit == 4:
        pairs = [(a, b) for a in (0, -1, 1, -(1 << 31), (1 << 31) - 1)
                 for b in (0, -1, 1, -(1 << 32), (1 << 32) - 1)]
        pairs += [(rng.randrange(-(1 << 31), 1 << 31), rng.randrange(-(1 << 32), 1 << 32))
                  for _ in range(100)]
        cases = [[a & 0xffffffff, b & ((1 << 33) - 1), (a * b) & ((1 << 65) - 1),
                  0, 0, 52, 0] for a, b in pairs]
    else:
        raise ValueError(unit)
    # Independently annul accepted operands at early/middle/last work edges.
    candidate = next(row for row in reversed(cases) if row[5] > 2)
    aborts = [1, candidate[5] // 2, candidate[5]]
    cases += [[*candidate[:6], abort] for abort in aborts]
    path.write_text("".join(" ".join(format(v, "x") for v in row) + "\n" for row in cases))
    return len(cases), len(aborts)


def scalar_case(run, simulator, unit, seed=17):
    folder = run.path / f"scalar-u{unit}-{simulator}-s{seed}"
    folder.mkdir()
    vectors = folder / "vectors.txt"
    count, aborts = scalar_vectors(vectors, unit, seed)
    write_json(folder / "inputs.json", {"unit": unit, "seed": seed,
                                      "vector_sha256": sha256(vectors), "tests": count})
    sources = ["rtl/anvil_q3_divider.sv", "rtl/anvil_q3_isqrt.sv", "rtl/anvil_q3_exp.sv",
               "rtl/anvil_q3_silu.sv", "rtl/anvil_q3_multiplier.sv", "tests/scalar_tb.sv"]
    if simulator == "iverilog":
        binary = folder / "scalar.vvp"
        run.tool(["iverilog", "-g2012", "-Wall", "-s", "scalar_tb", f"-Pscalar_tb.UNIT={unit}",
                  "-o", run.rel(binary), *sources])
        command = ["vvp", run.rel(binary), "+vectors=" + run.rel(vectors)]
    elif simulator == "verilator":
        obj = folder / "obj"
        run.tool(["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                  "--top-module", "scalar_tb", "--Mdir", run.rel(obj), "-o", "scalar",
                  f"-GUNIT={unit}", *sources])
        command = [run.rel(obj / "scalar"), "+vectors=" + run.rel(vectors)]
    else:
        raise ValueError(simulator)
    text, receipt = run.tool(command)
    if f"SCALAR_COMPLETE unit={unit} tests={count} aborted={aborts}" not in text:
        raise AssertionError("incomplete scalar comparisons")
    result = {"simulator": simulator, "unit": unit, "seed": seed, "tests": count,
              "flushes": aborts, "stdout": receipt["stdout"]}
    write_json(folder / "result.json", result)
    return result
