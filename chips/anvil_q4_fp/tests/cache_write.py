"""Independent cache narrowing, packed writes, pages and public readback."""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import execute, new_run, relative, source_hashes
from ieee import convert, decode, pack


def sources(fmt):
    pool = [0, 0x80000000, 0x7f800000, 0xff800000, 0x7fc01234,
            0x7f801234, 0xff801234, 1, 0x80000001, 0x007fffff,
            0x00800000, 0x7f7fffff, 0xff7fffff]
    limits = {"bf16": (0x0080, 0x3f80, 0x7f7e),
              "fp16": (0x0400, 0x3c00, 0x7bfe),
              "fp8": tuple(range(0x7b))}
    for lower in limits[fmt]:
        a = decode(lower, fmt)[2]
        b = decode(lower + 1, fmt)[2]
        midpoint = pack((a + b) / 2)[0]
        for value in (midpoint - 1, midpoint, midpoint + 1):
            pool.extend((value, value | 0x80000000))
    if fmt == "fp8":
        overflow_midpoint = pack(Fraction(61440))[0]
        for value in (overflow_midpoint - 1, overflow_midpoint,
                      overflow_midpoint + 1):
            pool.extend((value, value | 0x80000000))
    return pool


def fixture(path):
    cases = []
    cursors = [0, 0, 0]
    formats = ("bf16", "fp16", "fp8")
    pools = [sources(fmt) for fmt in formats]

    def add(encoding, page_size, position, kd, fault=0):
        logical_pages = position // page_size + 1
        physical_pages = 16
        maps = [0x80000000 | (15 - page) for page in range(logical_pages)]
        protected = []
        if fault == 1:
            maps[-1] &= 0x7fffffff
        elif fault == 2:
            maps[-1] = 0x80000010
        elif fault == 3:
            maps[0] = maps[-1]
        elif fault == 4:
            maps[0] = maps[1]
        elif fault == 5:
            protected = [maps[-1]]
        elif fault == 6:
            protected = [0x80000001, 0x80000001]
        elif fault == 7:
            maps[0] &= 0x7fffffff
        elif fault == 8:
            maps[0] = 0x80000010
        else:
            protected = [0x80000001, 0x80000002]
        values = [pools[encoding][(cursors[encoding] + i) % len(pools[encoding])]
                  for i in range(2 * kd)]
        if not fault:
            cursors[encoding] += len(values)
        converted = [convert(bits, "fp32", formats[encoding])[0] for bits in values]
        width = 8 if encoding == 2 else 16
        per_word = 32 // width
        words = []
        for kind in range(2):
            for start in range(0, kd, per_word):
                words.append(sum(converted[kind * kd + i] << ((i - start) * width)
                                 for i in range(start, min(start + per_word, kd))))
        cases.append({
            "format": encoding, "page_tokens": page_size, "position": position,
            "committed": position, "physical_pages": physical_pages,
            "kv_heads": 1 if kd == 2 else 3 if kd == 6 else 5, "head_dim": 2,
            "maps": maps, "protected_maps": protected, "sources": values,
            "packed": words,
            "readback": [convert(bits, formats[encoding], "fp32")[0]
                         for bits in converted],
            "fault": fault,
        })

    for encoding in range(3):
        for page_size in (1, 2, 4, 8, 16, 32):
            for position in sorted({0, page_size - 1, page_size,
                                    page_size + 1, 2 * page_size - 1}):
                for kd in (2, 6, 10):
                    add(encoding, page_size, position, kd)
        for fault in range(1, 9):
            add(encoding, 2, 4, 6, fault)
    if cursors[2] < len(pools[2]):
        raise AssertionError("FP8 midpoint source coverage is incomplete")
    with path.open("w") as stream:
        stream.write(f"{len(cases)}\n")
        for case in cases:
            stream.write(" ".join(str(case[key]) for key in
                                  ("format", "page_tokens", "position", "committed",
                                   "physical_pages", "kv_heads", "head_dim", "fault")))
            stream.write(f" {len(case['maps'])} {len(case['protected_maps'])}\n")
            for key in ("maps", "protected_maps", "sources", "packed", "readback"):
                stream.write(" ".join(f"{word:08x}" for word in case[key]) + "\n")
    return {"cases": len(cases), "valid_cases": sum(not c["fault"] for c in cases),
            "negative_cases": sum(bool(c["fault"]) for c in cases),
            "source_counts": dict(zip(formats, cursors)),
            "fp8_midpoint_pool": len(pools[2]),
            "oracle": "independent exact rational RNE, canonical NaNs"}


def run(preparation=False):
    directory = new_run("cache-write", preparation)
    image = directory / "cache-write-vectors.txt"
    coverage = fixture(image)
    (directory / "reference.json").write_text(json.dumps({
        "source_sha256": source_hashes(), **coverage}, indent=2) + "\n")
    obj = directory / "compile-obj"
    try:
        execute(directory / "verilator-compile", [
            "verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
            "--top-module", "cache_write_tb", "--Mdir", relative(obj),
            "rtl/anvil_q4_00_fp_pkg.sv", "rtl/anvil_q4_fp32.sv",
            "rtl/anvil_q4_fp_mem_port.sv", "rtl/anvil_q4_fp_kv_cache.sv",
            "tests/cache_write_tb.sv"])
        execute(directory / "verilator-cache-write", [
            relative(obj / "Vcache_write_tb"), f"+vectors={relative(image)}"])
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    print(f"Cache write receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    args = parser.parse_args()
    run(args.preparation)
