"""Execute the actual parent with independent tied-embedding W4 token outputs."""

import argparse
import hashlib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import Experiment
from build_cache import compile_verilator
from small_model import fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--banks", type=int, choices=(1, 4), required=True)
    parser.add_argument("--cache", type=int, choices=(0, 1), default=0,
                        help="parent mode: 0 Q16, 1 INT8; parent has no raw FP16 mode")
    parser.add_argument("--seed", type=int, choices=(11, 29, 101), default=11)
    parser.add_argument("--repair-of")
    parser.add_argument("--build-cache", type=Path)
    parser.add_argument("--benchmark-trace", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    parent = sorted(str(path.relative_to(root)) for path in (root / "anvil_q2_reference/rtl").glob("*.sv"))
    names = parent + [
        "tests/parent_system_tb.sv", "tests/parent_system_check.py",
        "tests/small_model.py", "tests/reference.py", "tests/retention.py", "tests/build_cache.py"]
    if args.benchmark_trace:
        names.append("tests/benchmark_ports.sv")
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    try:
        memory, descriptors, logits = fixture(0, 2 if args.cache else 0, args.seed, tied_head=True)
        directory = experiment.directory
        (directory / "image.hex").write_text("".join(f"{byte:02x}\n" for byte in memory))
        (directory / "descriptors.hex").write_text("".join(
            f"{word:08x}\n" for descriptor in descriptors for word in descriptor))
        (directory / "expected.hex").write_text("".join(f"{value & 0xffffffff:08x}\n" for value in logits))
        experiment.receipt["fixture"] = {
            "synthetic": True, "seed": args.seed, "weight_mode": "W4A16",
            "cache": "INT8" if args.cache else "Q16", "tied_embedding": True,
            "geometry": "one layer, H=I=D=8, Q=KV=1, V=S=3, group=block=1",
            "image_sha256": hashlib.sha256(memory).hexdigest(), "expected_logits": logits}
        for tool, flag in (("verilator", "--version"), ("g++", "--version")):
            experiment.run([tool, flag], tool + "-version")
        output = args.output
        executable = compile_verilator(experiment, ["verilator", "--binary", "--timing", "-Wno-fatal",
                        "--top-module", "parent_system_tb", "--Mdir", str(output / "obj"),
                        "-MAKEFLAGS", "VK_PCH_I_FAST= VK_PCH_I_SLOW=", "-o", "parent_sim",
                        f"-GBANKS={args.banks}", f"-GCACHE_MODE={args.cache}"] +
                       [str(output / "sources" / name) for name in parent + ["tests/parent_system_tb.sv"]] +
                       (["-DBENCH_PARENT", str(output / "sources/tests/benchmark_ports.sv")]
                        if args.benchmark_trace else []),
                       cache=args.build_cache)
        text = experiment.run([executable,
                               "+image=" + str(output / "image.hex"),
                               "+descriptors=" + str(output / "descriptors.hex"),
                               "+expected=" + str(output / "expected.hex")] +
                              (["+benchmark_trace"] if args.benchmark_trace else []), "simulate")
        if "PARENT_SYSTEM_CHECKED " not in text:
            raise RuntimeError("missing actual parent comparison summary")
        experiment.receipt["comparison_summary"] = "\n".join(
            line for line in text.strip().splitlines() if not line.startswith("BENCH_"))
        experiment.receipt["service_model"] = {
            "response_latency_cycles": 3, "transactions_per_bank_outstanding": 1,
            "response_backpressure": "ready/valid and exact request tag",
            "request_stalls": "only the bounded occupied bank",
            "response_bytes": 4, "physical_frequency_claim": False}
        experiment.receipt["scope"] = (
            "parent-only small D5 numerical baseline; not five-domain closure, "
            "common-service HT speedup or physical throughput")
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, ArithmeticError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
