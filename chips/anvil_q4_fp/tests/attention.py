"""Independent ordered attention model and head_dim=6 scale boundary probe."""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import ROOT, execute, new_run, relative, source_hashes
from ieee import exp_frozen, operation, pack, sqrt_round


def attention(query, keys, values, scale):
    def op(code, a, b=0):
        return operation(code, a, b)[0]

    scores = []
    for key in keys:
        accumulator = 0
        for q, k in zip(query, key, strict=True):
            accumulator = op(0, accumulator, op(2, q, k))
        scores.append(op(2, accumulator, scale))
    # All probe scores are finite. Native ordered FP comparisons preserve ties.
    from ieee import decode
    maximum = max(scores, key=lambda x: decode(x)[2])
    exponentials = [exp_frozen(op(1, score, maximum))[0] for score in scores]
    total = 0
    for value in exponentials:
        total = op(0, total, value)
    weights = [op(3, value, total) for value in exponentials]
    result = []
    for dimension in range(len(query)):
        accumulator = 0
        for weight, value in zip(weights, values, strict=True):
            accumulator = op(0, accumulator, op(2, weight, value[dimension]))
        result.append(accumulator)
    return {"scores": scores, "exp": exponentials, "weights": weights, "result": result}


def run(preparation=False, repair_of=None):
    directory = new_run("attention-scale", preparation)

    def bits(values):
        return [pack(Fraction(value))[0] for value in values]

    query = bits(("0.5", "-0.75", "1", "1.25", "-0.25", "2"))
    keys = [bits(("1", "0.5", "-1", "2", "-0.25", "1.5")),
            bits(("-0.5", "1.5", "0.75", "-1.25", "2", "-0.75"))]
    values = [bits(("-1", "0.5", "2", "-0.5", "3", "1.25")),
              bits(("1.25", "-2", "0.75", "1.5", "-1", "2.5"))]
    # Contract: FP32(1/sqrt(head_dim)), one rounding of the exact scale.
    scale = sqrt_round(Fraction(1, 6))[0]
    expected = attention(query, keys, values, scale)
    # Retain this discriminant, but do not use it as acceptance.
    double_rounded_scale = operation(3, 0x3f800000,
                                     operation(4, pack(Fraction(6))[0])[0])[0]
    alternative = attention(query, keys, values, double_rounded_scale)
    fixture = directory / "attention-image.txt"
    fixture.write_text("".join(f"{word:08x}\n" for word in
                              query + sum(keys, []) + sum(values, []) + expected["result"]))
    (directory / "reference.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "head_dim": 6, "positions": 2,
        "scale": f"{scale:08x}", "expected": expected,
        "diagnostic_double_rounded_scale": f"{double_rounded_scale:08x}",
        "diagnostic_double_rounded_attention": alternative,
        "synthetic": True,
    }, indent=2) + "\n")
    obj = directory / "compile-obj"
    try:
        execute(directory / "verilator-compile",
                ["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                 "--top-module", "attention_tb", "--Mdir", relative(obj),
                 "rtl/anvil_q4_00_fp_pkg.sv", "rtl/anvil_q4_fp32.sv",
                 "rtl/anvil_q4_fp_mem_port.sv", "rtl/anvil_q4_fp_umul64.sv",
                 "rtl/anvil_q4_fp_exp.sv", "rtl/anvil_q4_fp_gqa_attention.sv",
                 "tests/attention_tb.sv"])
        execute(directory / "verilator-attention",
                [relative(obj / "Vattention_tb"), f"+image={relative(fixture)}"],
                repair_of=repair_of)
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    print(f"Attention probe receipts: {relative(directory)}", flush=True)
    return directory


def matrix_vectors(fixture, dimensions=range(2, 257, 2)):
    import random
    dimensions = tuple(dimensions)
    records = []
    with fixture.open("w") as stream:
        stream.write(f"{len(dimensions)}\n")
        for dimension in dimensions:
            scale = sqrt_round(Fraction(1, dimension))[0]
            ratio = (dimension // 2 - 1) % 8 + 1
            kv_heads = 2
            query_heads = kv_heads * ratio
            rng = random.Random(2026 + dimension)

            def vector():
                return [pack(Fraction(rng.randrange(-16, 17), 16))[0]
                        for _ in range(dimension)]

            queries = [vector() for _ in range(query_heads)]
            keys = [[vector() for _ in range(2)] for _ in range(kv_heads)]
            values = [[vector() for _ in range(2)] for _ in range(kv_heads)]
            expected = [attention(query, keys[head // ratio],
                                  values[head // ratio], scale)["result"]
                        for head, query in enumerate(queries)]
            stream.write(f"{dimension} {ratio} {kv_heads}\n")
            for arrays in (queries, [v for group in keys for v in group],
                           [v for group in values for v in group], expected):
                for vector_words in arrays:
                    stream.writelines(f"{word:08x}\n" for word in vector_words)
            records.append({"head_dim": dimension, "gqa_ratio": ratio,
                            "kv_heads": kv_heads, "query_heads": query_heads,
                            "scale": f"{scale:08x}",
                            "compared_outputs": query_heads * dimension})
    return records


def run_matrix(preparation=False, repair_of=None):
    """All legal dimensions and GQA head mappings, with public-pin comparisons."""
    import re

    directory = new_run("attention-matrix", preparation)
    scales = {dimension: sqrt_round(Fraction(1, dimension))[0]
              for dimension in range(2, 257, 2)}
    text = (ROOT / "rtl/anvil_q4_fp_gqa_attention.sv").read_text()
    entries = re.findall(r"8'd(\d+): attention_scale=32'h([0-9a-fA-F]+);", text)
    observed = {2 * int(index): int(bits, 16) for index, bits in entries}
    if len(entries) != 128 or observed != scales:
        raise AssertionError("attention ROM differs from independently rounded scales")
    fixture = directory / "matrix-image.txt"
    records = matrix_vectors(fixture)
    (directory / "reference.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "synthetic": True,
        "rounding": "exact integer sqrt and rational midpoint comparisons",
        "cases": records, "repair_of": repair_of,
    }, indent=2) + "\n")
    obj = directory / "compile-obj"
    try:
        execute(directory / "verilator-compile",
                ["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                 "--top-module", "attention_matrix_tb", "--Mdir", relative(obj),
                 "rtl/anvil_q4_00_fp_pkg.sv", "rtl/anvil_q4_fp32.sv",
                 "rtl/anvil_q4_fp_mem_port.sv", "rtl/anvil_q4_fp_umul64.sv",
                 "rtl/anvil_q4_fp_exp.sv", "rtl/anvil_q4_fp_gqa_attention.sv",
                 "tests/attention_matrix_tb.sv"])
        execute(directory / "verilator-attention-matrix",
                [relative(obj / "Vattention_matrix_tb"),
                 f"+image={relative(fixture)}"], timeout=1800, repair_of=repair_of)
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    print(f"Attention matrix receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    (run_matrix if args.matrix else run)(args.preparation, args.repair_of)
