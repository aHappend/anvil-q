"""Exhaustive native cache decoding through the actual public cache interface."""

import argparse
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import execute, new_run, relative, source_hashes
from ieee import convert


def run(preparation=False, compact=False):
    directory = new_run("cache-decode", preparation)
    fixture = directory / "cache-vectors.txt"
    counts = {}
    with fixture.open("w") as stream:
        for encoding, fmt, extent in ((0, "bf16", 65536), (1, "fp16", 65536),
                                      (2, "fp8", 256)):
            count = 0
            for bits in range(0, extent, 257 if compact and extent > 256 else 1):
                result, _ = convert(bits, fmt, "fp32")
                stream.write(f"{encoding} {bits:x} {result:08x}\n")
                count += 1
            counts[fmt] = count
    (directory / "reference.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "decode_counts": counts,
        "oracle": "independent rational IEEE conversion"}, indent=2) + "\n")
    obj = directory / "compile-obj"
    try:
        execute(directory / "verilator-compile", [
            "verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
            "--top-module", "cache_decode_tb", "--Mdir", relative(obj),
            "rtl/anvil_q4_00_fp_pkg.sv", "rtl/anvil_q4_fp32.sv",
            "rtl/anvil_q4_fp_mem_port.sv", "rtl/anvil_q4_fp_kv_cache.sv",
            "tests/cache_decode_tb.sv"])
        execute(directory / "verilator-cache-decode", [
            relative(obj / "Vcache_decode_tb"), f"+vectors={relative(fixture)}"],
            timeout=1800)
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    print(f"Cache decode receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    run(args.preparation, args.compact)
