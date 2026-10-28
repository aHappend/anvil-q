"""Independent default-width, multi-output W4 projection and memory observations."""

import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import struct
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import rhaz, sat32, scale_q16
from retention import Experiment
from build_cache import compile_verilator


def fixture(directory, output, seed):
    rows = cols = 1536
    chunks = cols // 128
    rng = random.Random(seed)
    activations = [rng.randint(-(1 << 20), 1 << 20) for _ in range(cols)]
    image = bytearray((rows // 16) * chunks * 1024)
    zero_base = len(image)
    zero_stride = chunks // 2
    image.extend(bytes(rows * zero_stride))
    image.extend(bytes((-len(image)) % 64))
    scale_base = len(image)
    image.extend(bytes(rows * chunks * 2))
    image.extend(bytes((-len(image)) % 64))
    sums = []
    for row in range(rows):
        total = 0
        for chunk in range(chunks):
            zero = rng.randrange(16)
            scale = rng.choice((0x0001, 0x0800, 0x2800, 0x3000, 0x3800, 0x3C00))
            image[zero_base + row * zero_stride + chunk // 2] |= zero << (4 * (chunk % 2))
            struct.pack_into("<H", image, scale_base + 2 * (row * chunks + chunk), scale)
            converted_scale = scale_q16(scale)
            for lane in range(128):
                weight = rng.randrange(16)
                element = ((row // 16) * chunks + chunk) * 2048 + (row % 16) * 128 + lane
                image[element // 2] |= weight << (4 * (element % 2))
                total += activations[chunk * 128 + lane] * (weight - zero) * converted_scale
        sums.append(total)
    descriptor = struct.pack("<QQQQIIIIIIQ", 0, zero_base, zero_base, scale_base,
                             rows, cols, 1024, zero_stride, chunks * 2, 0x100, 0)
    (directory / "image.hex").write_text("".join(f"{byte:02x}\n" for byte in image))
    (directory / "activation.hex").write_text(
        "".join(f"{word & 0xffffffff:08x}\n" for word in activations))
    (directory / "rows.hex").write_text(
        "".join(f"{word & ((1 << 128) - 1):032x}00000000\n" for word in sums))
    (directory / "parent_expected.hex").write_text(
        "".join(f"{sat32(rhaz(word, 16)) & 0xffffffff:08x}\n" for word in sums))
    (directory / "cases.txt").write_text(
        f"0 {len(image)} {cols} {output / 'image.hex'} {output / 'activation.hex'} "
        f"{int.from_bytes(descriptor, 'little'):0128x} "
        f"{sums[0] & ((1 << 128) - 1):032x} 00000000\n")
    return {
        "synthetic": True, "seed": seed, "rows": rows, "columns": cols,
        "group_size": 128, "expected_mac_contributions": rows * cols,
        "image_sha256": hashlib.sha256(image).hexdigest(),
        "fixture_hashes": {
            name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
            for name in ("image.hex", "activation.hex", "rows.hex", "parent_expected.hex",
                         "cases.txt")},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=int, choices=(11, 29, 101), default=11)
    parser.add_argument("--compare-parent", action="store_true")
    parser.add_argument("--build-cache", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    rtl = sorted(str(path.relative_to(root)) for path in (root / "rtl").glob("*.sv"))
    names = rtl + ["tests/checkpoint_projection_tb.sv", "tests/stream_projection_check.py",
                   "tests/reference.py", "tests/retention.py", "tests/build_cache.py"]
    parent = sorted(str(path.relative_to(root))
                    for path in (root / "anvil_q2_reference/rtl").glob("*.sv"))
    if args.compare_parent:
        names += parent + ["tests/parent_projection_tb.sv", "tests/projection_metrics_ports.sv"]
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    try:
        for tool, flag in (("python3", "--version"), ("verilator", "--version"),
                           ("g++", "--version")):
            experiment.run([tool, flag], tool + "-version")
        experiment.receipt["fixture"] = fixture(experiment.directory, args.output, args.seed)
        executable = compile_verilator(experiment, [
            "verilator", "--binary", "--timing", "-Wno-fatal",
            "--top-module", "checkpoint_projection_tb", "--Mdir", str(args.output / "obj"),
            "-MAKEFLAGS", "VK_PCH_I_FAST= VK_PCH_I_SLOW=", "-o", "stream_sim",
            *[str(args.output / "sources" / name) for name in
              rtl + ["tests/checkpoint_projection_tb.sv"]],
        ], cache=args.build_cache)
        text = experiment.run([
            executable, "+stream=1",
            "+cases=" + str(args.output / "cases.txt"),
            "+row_results=" + str(args.output / "rows.hex"),
            "+q16_results=" + str(args.output / "parent_expected.hex"),
        ], "simulate")
        match = re.search(r"^STREAM_PROJECTION_CHECKED (.+)$", text, re.MULTILINE)
        if not match:
            raise RuntimeError("missing executed full-width projection comparisons")
        metrics = {key: int(value) for key, value in
                   re.findall(r"([a-z][a-z0-9_]*)=(\d+)", match[1])}
        if (metrics["rows"], metrics["cols"], metrics["issues"]) != (1536, 1536, 18432):
            raise RuntimeError("incomplete default-width projection observations")
        if metrics.get("q16_rows") != 1536 or "STREAM_Q16_READBACK_CHECKED rows=1536" not in text:
            raise RuntimeError("missing actual RTL final conversion/storage comparisons")
        experiment.receipt["metrics"] = metrics
        metrics["tensor_mac_contributions"] = metrics["issues"] * 128
        metrics["tensor_issue_cycle_utilization"] = metrics["issues"] / metrics["cycles"]
        metrics["valid_payload_bytes"] = metrics["bytes"]
        metrics["valid_payload_bytes_per_cycle"] = metrics["bytes"] / metrics["cycles"]
        histogram = {int(length): int(count) for length, count in re.findall(
            r"^STREAM_BURSTS length=(\d+) count=(\d+)$", text, re.MULTILINE)}
        if (set(histogram) != set(range(1, 17)) or
                sum(length * count for length, count in histogram.items()) != metrics["beats"]):
            raise RuntimeError("incomplete measured streaming burst histogram")
        metrics["read_burst_histogram"] = {
            str(length): count for length, count in histogram.items() if count}
        metrics["cache_hits"], metrics["cache_misses"] = 0, 0
        metrics["cache_hit_rate"] = None
        experiment.receipt["comparison_summary"] = text.strip()
        if args.compare_parent:
            baseline = {}
            experiment.receipt["parent"] = baseline
            for banks in (1, 4):
                label = f"parent{banks}"
                executable = compile_verilator(experiment, [
                    "verilator", "--binary", "--timing", "-Wno-fatal",
                    "--top-module", "parent_projection_tb",
                    "--Mdir", str(args.output / (label + "-obj")),
                    "-MAKEFLAGS", "VK_PCH_I_FAST= VK_PCH_I_SLOW=",
                    "-o", "parent_sim", f"-GBANKS={banks}",
                    *[str(args.output / "sources" / name) for name in
                      parent + ["tests/parent_projection_tb.sv"]],
                    str(args.output / "sources/tests/projection_metrics_ports.sv"),
                ], label + "-compile", cache=args.build_cache)
                parent_text = experiment.run([
                    executable,
                    "+image=" + str(args.output / "image.hex"),
                    "+activation=" + str(args.output / "activation.hex"),
                    "+expected=" + str(args.output / "parent_expected.hex"),
                ], label + "-simulate")
                parent_match = re.search(r"^PARENT_PROJECTION_CHECKED (.+)$",
                                         parent_text, re.MULTILINE)
                if not parent_match:
                    raise RuntimeError("missing real parent projection comparisons")
                measured = {key: int(value) for key, value in
                            re.findall(r"([a-z][a-z0-9_]*)=(\d+)", parent_match[1])}
                if (measured["banks"], measured["rows"], measured["cols"]) != (banks, 1536, 1536):
                    raise RuntimeError("parent projection geometry mismatch")
                engines = [
                    {"issues": int(issues), "stalls": int(stalls)}
                    for issues, stalls in re.findall(
                        r"^DEFAULT_PARENT_MAC_PORTS issues=(\d+) stalls=(\d+)$",
                        parent_text, re.MULTILINE)]
                if (len(engines) != banks or any(row["issues"] <= 0 for row in engines) or
                        sum(row["issues"] for row in engines) * 8 != 1536 * 1536):
                    raise RuntimeError("missing actual full-width parent MAC issue observations")
                measured["engine_port_counters"] = engines
                measured["tensor_issue_events"] = sum(row["issues"] for row in engines)
                measured["tensor_mac_contributions"] = measured["tensor_issue_events"] * 8
                measured["tensor_engine_issue_utilization"] = (
                    measured["tensor_issue_events"] / (banks * measured["cycles"]))
                measured["tensor_input_stall_port_cycles"] = sum(
                    row["stalls"] for row in engines)
                measured["cache_hits"], measured["cache_misses"] = 0, 0
                measured["cache_hit_rate"] = None
                measured["valid_payload_bytes_per_cycle"] = (
                    measured["valid_payload_bytes"] / measured["cycles"])
                measured["read_burst_histogram"] = {"1": measured["reads"]}
                measured["ht_cycle_normalized_throughput_ratio"] = (
                    measured["cycles"] / metrics["cycles"])
                baseline[str(banks)] = measured
            if baseline["4"]["ht_cycle_normalized_throughput_ratio"] <= 1:
                raise RuntimeError("measured streaming W4 throughput ratio must exceed one")
        experiment.receipt["scope"] = (
            "D1 synthetic default-width W4 projection, exact sums for every HT row; "
            "actual HT rounding helper and vector store produce checked Q16 outputs; "
            "optional actual parent O-projection checks the identical Q16 outputs; "
            "not five-domain closure, official checkpoint or physical timing")
        experiment.receipt["service_model"] = (
            "minimum three-cycle response latency; at most one 64-byte DDR/metadata "
            "return per cycle, metadata defers to weight returns; commands stall at cycle "
            "modulo 13 equals seven and returns at modulo seven equals two for both "
            "implementations; HT activation is a separate on-chip operand service; "
            "HT results retire into the actual on-chip vector store whereas parent "
            "scratch writes use its genuine scalar request interface")
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
