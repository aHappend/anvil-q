"""Independent native descriptor validation and atomic shadow/active checks."""

import argparse
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import execute, new_run, relative, source_hashes
from native_model import descriptor


def valid_native(w, banks):
    positive = lambda bits: not (bits >> 31) and bits & 0x7fffffff and (
        (bits >> 23) & 255) != 255
    power = lambda value: value > 0 and value & (value - 1) == 0
    return bool(
        len(w) == 32 and all(type(value) is int and 0 <= value < 2**32 for value in w)
        and w[:2] == [2, 5] and w[2] in (0, 1) and w[3:5] == [0, 0]
        and w[5] in (0, 1, 2) and power(w[6]) and w[6] <= banks
        and 1 <= w[7] <= 64 and 2 <= w[8] <= 8192
        and 1 <= w[9] <= 32768 and 1 <= w[10] <= 128 and 1 <= w[11] <= 128
        and 2 <= w[12] <= 256 and w[12] % 2 == 0
        and 1 <= w[13] <= 262144 and 1 <= w[14] <= 131072 and w[15] == 1
        and w[16] in (0, 1) and positive(w[17]) and positive(w[18])
        and power(w[19]) and w[19] <= 32 and 1 <= w[20] <= 131072
        and w[21] == 0 and 1 <= w[22] <= 8 and w[23] == 1
        and w[24:] == [0] * 8 and w[8] == w[10] * w[12]
        and w[10] == w[11] * w[22] and w[19] * w[20] >= w[14])


def cases(banks):
    result = []

    def add(name, words, expected):
        if valid_native(words, banks) != expected:
            raise AssertionError(f"Descriptor oracle/fixture disagreement: {name}")
        result.append((name, words, expected))

    for label, layers, hidden, inter, heads, kv, dim, vocabulary, bias in (
            ("Qwen2.5-7B-Instruct", 28, 3584, 18944, 28, 4, 128, 152064, 1),
            ("DeepSeek-R1-Distill-Qwen-7B", 28, 3584, 18944, 28, 4, 128, 152064, 1),
            ("Llama-3.2-1B", 16, 2048, 8192, 32, 8, 64, 128256, 0),
            ("Llama-3.2-3B", 28, 3072, 8192, 24, 8, 128, 128256, 0)):
        words = descriptor(banks=banks, layers=layers, dimension=dim, ratio=heads // kv,
                           kv_heads=kv, intermediate=inter, vocabulary=vocabulary,
                           context=32768, page_tokens=32, bias=bias)
        if words[8] != hidden:
            raise AssertionError(label)
        add(label + "-synthetic-config-not-checkpoint-execution", words, True)
    for ratio in range(1, 9):
        for element in (0, 1):
            for cache in (0, 1, 2):
                add(f"ratio-{ratio}-element-{element}-cache-{cache}",
                    descriptor(banks=banks, ratio=ratio, element=element, cache=cache,
                               kv_heads=2, dimension=2), True)
    base = descriptor(banks=banks)
    minimum = descriptor(banks=1, dimension=2, intermediate=1, vocabulary=1,
                         context=1, page_tokens=1, bias=0)
    minimum[17:19] = [1, 1]
    add("minimum-positive-subnormal-theta-epsilon", minimum, True)
    maximum = descriptor(banks=banks, layers=64, dimension=256, ratio=8, kv_heads=4,
                         intermediate=32768, vocabulary=262144,
                         context=131072, page_tokens=32)
    maximum[17:19] = [0x7f7fffff, 0x7f7fffff]
    add("maximum-legal-extents", maximum, True)
    for active_banks in (1, 2, 4, 8, 16):
        words = list(base)
        words[6] = active_banks
        add(f"active-banks-{active_banks}", words, active_banks <= banks)
    invalids = {
        0: (0, 1, 3), 1: (0, 1, 2, 3, 4, 6), 2: (2, 0xffffffff),
        3: (1, 2), 4: (1, 2), 5: (3, 4), 6: (0, 3, 32),
        7: (0, 65, 0xffffffff), 8: (0, 1, 8193, 0x80000002),
        9: (0, 32769, 0xffffffff), 10: (0, 129, 0x80000001),
        11: (0, 129, 0xffffffff), 12: (0, 1, 3, 257, 0x80000002),
        13: (0, 262145, 0xffffffff), 14: (0, 131073, 0xffffffff),
        15: (0, 2, 128), 16: (2, 0xffffffff),
        17: (0, 0x80000000, 0xbf800000, 0x7f800000, 0xff800000, 0x7f800001, 0x7fc00000),
        18: (0, 0x80000000, 0xbf800000, 0x7f800000, 0xff800000, 0x7f800001, 0x7fc00000),
        19: (0, 3, 64, 0xffffffff), 20: (0, 131073, 0xffffffff),
        21: (1, 0xffffffff), 22: (0, 9, 0xffffffff), 23: (0, 2, 0xffffffff),
        **{index: (1, 0xffffffff) for index in range(24, 32)},
    }
    for index, values in invalids.items():
        for value in values:
            words = list(base)
            words[index] = value
            add(f"invalid-word-{index}-{value:08x}", words, False)
    for label, edits in (
            ("hidden-product-mismatch", {8: 6}),
            ("head-ratio-mismatch", {10: 2}),
            ("capacity-product-too-small", {14: 3, 19: 1, 20: 2}),
            ("capacity-overflow-attempt", {14: 131072, 19: 0x80000000, 20: 0x80000000})):
        words = list(base)
        for index, value in edits.items():
            words[index] = value
        add(label, words, False)
    add("restore-valid-for-control-tests", base, True)
    return result


def run(preparation=False, banks=16):
    directory = new_run("descriptor", preparation)
    records = cases(banks)
    fixture = directory / "descriptor-vectors.txt"
    with fixture.open("w") as stream:
        stream.write(f"{len(records)}\n")
        for _, words, expected in records:
            stream.write(f"{int(expected)}\n")
            stream.write(" ".join(f"{word:08x}" for word in words) + "\n")
    (directory / "reference.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "banks": banks,
        "cases": [{"name": name, "accepted": expected} for name, _, expected in records],
        "oracle": "independent unbounded-integer native descriptor predicate",
    }, indent=2) + "\n")
    obj = directory / "compile-obj"
    try:
        execute(directory / "verilator-compile", [
            "verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
            "--top-module", "descriptor_tb", "--Mdir", relative(obj),
            f"-GBANKS={banks}", "rtl/anvil_q4_fp_descriptor.sv", "tests/descriptor_tb.sv"])
        execute(directory / "verilator-descriptor", [
            relative(obj / "Vdescriptor_tb"), f"+vectors={relative(fixture)}"])
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    print(f"Descriptor receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--banks", type=int, default=16)
    args = parser.parse_args()
    run(args.preparation, args.banks)
