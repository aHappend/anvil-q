"""Directed RMSNorm/RoPE comparisons derived solely from frozen equations."""

import random

from execution import ROOT, sha256, write_json
from reference import f16_q16, half, rmsnorm, rotate, rope_samples


def vectors(path, unit, seed):
    rng = random.Random(seed)
    cases = []
    h, d, q, k = (16, 2, 8, 1) if unit == 0 else (64, 8, 8, 2)
    edge = [-(1 << 31), (1 << 31) - 1, -65536, 65536, -1, 0, 1, 32768]
    if unit == 0:
        values = [[0] * h, [1] * h, [-1] * h, (edge * 2)[:h],
                  [rng.randrange(-(1 << 31), 1 << 31) for _ in range(h)]]
        gammas = [0, 0x8000, 1, 0x8001, half(1), half(-1), 0x7bff, 0xfbff]
        for mode in range(3):
            for x in values:
                gamma = [gammas[i % len(gammas)] for i in range(h)]
                expected = rmsnorm(x, [f16_q16(v) for v in gamma])
                rows = []
                source, dest, kind = ((0, 1, 5), (7, 8, 6), (0, 14, 7))[mode]
                for col in range(h):
                    rows.extend([(8, 0, source, col, x[col], 0, 2, 0),
                                 (kind, 0 if mode == 2 else 1, 0, col, gamma[col], 0, 1, 0),
                                 (8, 0, dest, col, 0, expected[col], 0, 1)])
                cases.append((1, 32767, mode, 0, rows))
        for invalid in (0x7c00, 0xfc00, 0x7e00):
            cases.append((0, 0, 0, 1, [(8, 0, 0, col, edge[col % 8], 0, 2, 0)
                                      for col in range(h)] +
                          [(5, 0, 0, 0, invalid, 0, 1, 0)]))
    else:
        for pos in (0, 1, 8191, 32767):
            coefficients = rope_samples(pos, d)
            rows = [(11, 0, pos, col, value, 0, q + k, 0)
                    for col, value in enumerate(coefficients)]
            for slot, heads in ((2, q), (3, k)):
                x = [edge[i % len(edge)] if pos in (0, 32767) else
                     rng.randrange(-(1 << 31), 1 << 31) for i in range(heads * d)]
                expected = rotate(x, d, coefficients)
                rows.extend((8, 0, slot, col, value, expected[col], 1, 1)
                            for col, value in enumerate(x))
            cases.append((1, pos, 0, 0, rows))
        for invalid in ((1 << 30) + 1, -(1 << 30) - 1):
            cases.append((0, 0, 0, 1, [(8, 0, 2, 0, 65536, 0, 1, 0),
                                      (8, 0, 2, d // 2, -65536, 0, 1, 0),
                                      (11, 0, 0, 0, invalid, 0, 1, 0)]))
    cases.extend([(2, 0, 0, 1, []), (0, 32768, 0, 1, [])])
    if unit == 0:
        cases.append((0, 0, 3, 1, []))
    lines = [str(len(cases))]
    bits = 0
    errors = 0
    for layer, pos, mode, error, rows in cases:
        lines.append(f"{layer} {pos} {mode} {error} {len(rows)}")
        errors += error
        for kind, bank_layer, row, col, data, expected, reads, writes in rows:
            lines.append(f"{kind} {bank_layer} {row} {col} {data & 0xffffffff:x} "
                         f"{expected & 0xffffffff:x} {reads} {writes}")
            bits += writes * 32
    path.write_text("\n".join(lines) + "\n")
    return {"cases": len(cases), "compared_bits": bits, "expected_errors": errors,
            "geometry": {"HIDDEN_SIZE": h, "HEAD_DIM": d, "NUM_Q_HEADS": q, "NUM_KV_HEADS": k}}


def math_memory_case(run, unit=0, simulator="iverilog", seed=17):
    folder = run.path / f"math-memory-u{unit}-s{seed}-{simulator}"
    folder.mkdir()
    source = folder / "vectors.txt"
    expected = vectors(source, unit, seed)
    write_json(folder / "inputs.json", {**expected, "seed": seed, "sha256": sha256(source)})
    parameters = {"UNIT": unit, **expected["geometry"]}
    rtl = [str(p.relative_to(ROOT)) for p in sorted((ROOT / "rtl").glob("*.sv"))]
    if simulator == "iverilog":
        binary = folder / "math.vvp"
        run.tool(["iverilog", "-g2012", "-Wall", "-s", "math_memory_tb",
                  "-o", run.rel(binary),
                  *[f"-Pmath_memory_tb.{key}={v}" for key, v in parameters.items()],
                  *rtl, "tests/math_memory_tb.sv"])
        command = ["vvp", run.rel(binary)]
    elif simulator == "verilator":
        obj = folder / "obj"
        run.tool(["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                  "--top-module", "math_memory_tb", "--Mdir", run.rel(obj), "-o", "math",
                  *[f"-G{key}={v}" for key, v in parameters.items()],
                  *rtl, "tests/math_memory_tb.sv"])
        command = [run.rel(obj / "math")]
    else:
        raise ValueError(simulator)
    text, record = run.tool([*command, "+vectors=" + run.rel(source)])
    marker = (f"MATH_MEMORY_COMPLETE unit={unit} cases={expected['cases']} "
              f"bits={expected['compared_bits']} errors={expected['expected_errors']}")
    if marker not in text:
        raise AssertionError("incomplete directed math-memory comparisons")
    result = {**expected, "unit": unit, "simulator": simulator, "seed": seed,
              "stdout": record["stdout"], "bit_mismatches": 0}
    write_json(folder / "result.json", result)
    return result
