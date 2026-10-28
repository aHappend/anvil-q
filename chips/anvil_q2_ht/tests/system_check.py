"""Synthetic connected-top preparation check; not full-model or physical acceptance."""

import argparse
import difflib
import hashlib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import Experiment
from build_cache import compile_verilator
from small_model import CELLS, fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mode", type=int, choices=(0, 1), default=0)
    parser.add_argument("--cache", type=int, choices=(0, 1, 2), default=0)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="verilator")
    parser.add_argument("--scenario", choices=("tokens", "control", "persistence", "roundtrip"),
                        default="tokens")
    parser.add_argument("--cell", choices=CELLS, default="small")
    parser.add_argument("--repair-of")
    parser.add_argument("--build-cache", type=Path)
    parser.add_argument("--bias-stress", action="store_true")
    parser.add_argument("--bias-boundary", action="store_true")
    parser.add_argument("--tied-head", action="store_true")
    parser.add_argument("--memory-service", choices=("random", "common"), default="random")
    parser.add_argument("--benchmark-trace", action="store_true",
                        help="Verilator-only observation of public submodule ports")
    parser.add_argument("--mutation", choices=("none", "slot-association", "kv-exponent", "bf16-bias"),
                        default="none")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    rtl = sorted(str(path.relative_to(root)) for path in (root / "rtl").glob("*.sv"))
    names = rtl + ["tests/system_tb.sv", "tests/reference.py", "tests/small_model.py",
                   "tests/system_check.py", "tests/retention.py", "tests/build_cache.py"]
    if args.benchmark_trace:
        names.append("tests/benchmark_ports.sv")
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    try:
        tools = [("python3", "--version")]
        tools += ([("iverilog", "-V"), ("vvp", "-V")] if args.simulator == "iverilog"
                  else [("verilator", "--version"), ("g++", "--version")])
        for tool, flag in tools:
            experiment.run([tool, flag], tool + "-version")
        geometry = CELLS[args.cell]
        if args.scenario == "roundtrip" and (
                args.cell != "small" or args.mutation != "none" or args.benchmark_trace):
            raise ValueError("compact roundtrip requires the unmutated small geometry")
        if args.benchmark_trace and (args.simulator != "verilator" or args.scenario != "tokens"):
            raise ValueError("public-port benchmark tracing requires the Verilator tokens scenario")
        if args.memory_service == "common" and args.scenario != "tokens":
            raise ValueError("common benchmark service uses the isolated tokens scenario")
        memory, descriptors, logits = fixture(args.mode, args.cache, args.seed, args.cell,
                                              args.bias_stress, args.tied_head, args.bias_boundary)
        if args.bias_boundary and logits != [2] * 9:
            raise ArithmeticError("direct BF16 bias fixture must produce exactly nine Q16 words of two")
        directory = experiment.directory
        (directory / "image.hex").write_text(
            "".join(f"{int.from_bytes(memory[i:i + 64], 'little'):0128x}\n"
                    for i in range(0, len(memory), 64)))
        (directory / "descriptors.hex").write_text(
            "".join(f"{word:08x}\n" for descriptor in descriptors for word in descriptor))
        (directory / "expected.hex").write_text(
            "".join(f"{word & 0xffffffff:08x}\n" for word in logits))
        experiment.receipt["fixture"] = {
            "synthetic": True, "seed": args.seed, "mode": args.mode, "cache_mode": args.cache,
            "scenario": args.scenario,
            "bias_stress": args.bias_stress,
            "bias_boundary": args.bias_boundary,
            "tied_head": args.tied_head, "memory_service": args.memory_service,
            "geometry": geometry, "cell": args.cell,
            "image_sha256": hashlib.sha256(memory).hexdigest(), "bytes": len(memory),
            "expected_logits": logits,
            "fixture_hashes": {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                               for name in ("image.hex", "descriptors.hex", "expected.hex")}}
        output = args.output
        compilation = [str(output / "sources" / name) for name in rtl + ["tests/system_tb.sv"]]
        if args.benchmark_trace:
            compilation += ["-DBENCH_HT", str(output / "sources/tests/benchmark_ports.sv")]
        parameters = {
            "NUM_LAYERS": geometry["layers"], "HIDDEN_SIZE": geometry["hidden"],
            "INTERMEDIATE_SIZE": geometry["intermediate"],
            "NUM_Q_HEADS": geometry["query_heads"], "NUM_KV_HEADS": geometry["kv_heads"],
            "HEAD_DIM": geometry["head_dim"], "GROUP_SIZE": geometry["group"],
            "CACHE_BLOCK": geometry["cache_block"], "VOCAB_SIZE": geometry["vocabulary"],
            "MAX_SEQ_LEN": geometry["sequence"], "HOT_BLOCKS": geometry["hot_blocks"],
            "QUEUE_DEPTH": geometry["queue"], "TILE_SLOTS": geometry["slots"],
            "READ_OUTSTANDING": geometry["outstanding"], "IMAGE_BYTES": geometry["image_bytes"]}
        if args.mutation != "none":
            changes = {
                "slot-association": (
                    "rtl/anvil_q2_ht_ddr_prefetcher.sv",
                    "fill_valid ? response_generation[response_head] : 32'd0",
                    "fill_valid ? response_generation[response_head]+32'd1 : 32'd0",
                    "SYSTEM_COMPLETION"),
                "kv-exponent": (
                    "rtl/anvil_q2_ht_kv_codec.sv",
                    "record[7:0] <= {3'd0,exponent};",
                    "record[7:0] <= {3'd0,exponent}+8'd1;",
                    "SYSTEM_NUMERICAL"),
                "bf16-bias": (
                    "rtl/anvil_q2_ht_sequencer.sv",
                    "PROJ_BIAS: convert_word(mode ? 4'd7 : 4'd0,",
                    "PROJ_BIAS: convert_word(mode ? 4'd1 : 4'd0,",
                    "SYSTEM_NUMERICAL"),
            }
            name, old, new, expected_assertion = changes[args.mutation]
            if args.mutation == "kv-exponent" and args.cache != 2:
                raise ValueError("KV exponent sensitivity requires INT8 cache mode")
            if args.mutation == "bf16-bias" and not args.bias_boundary:
                raise ValueError("BF16 bias sensitivity requires the directed boundary fixture")
            original = (directory / "sources" / name).read_text()
            if original.count(old) != 1:
                raise RuntimeError("mutation anchor is not unique")
            mutated = original.replace(old, new)
            path = directory / "mutant" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(mutated)
            (directory / "mutation.diff").write_text(
                "".join(difflib.unified_diff(original.splitlines(True),
                                             mutated.splitlines(True),
                                             fromfile=name, tofile="mutant/" + name)))
            compilation[rtl.index(name)] = str(output / "mutant" / name)
            experiment.receipt["mutation"] = {
                "name": args.mutation, "path": str(output / "mutant" / name),
                "sha256": hashlib.sha256(mutated.encode()).hexdigest(),
                "required_assertion": expected_assertion}
        if args.simulator == "iverilog":
            experiment.run(["iverilog", "-g2012", "-Wall", "-s", "system_tb", "-o",
                            str(output / "system.vvp")] +
                           [f"-Psystem_tb.{key}={value}" for key, value in parameters.items()] +
                           compilation, "compile")
            simulation = ["vvp", str(output / "system.vvp")]
        else:
            executable = compile_verilator(experiment, ["verilator", "--binary", "--timing", "-Wno-fatal",
                            "--top-module", "system_tb", "--Mdir", str(output / "obj"),
                            "-MAKEFLAGS", "VK_PCH_I_FAST= VK_PCH_I_SLOW=",
                            "-o", "system_sim"] +
                           [f"-G{key}={value}" for key, value in parameters.items()] +
                           compilation, cache=args.build_cache)
            simulation = [executable]
        text = experiment.run(
            simulation + ["+image=" + str(output / "image.hex"),
             "+descriptors=" + str(output / "descriptors.hex"),
             "+expected=" + str(output / "expected.hex"),
             "+readback=" + str(output / "readback.hex"),
             "+mode=" + str(args.mode), "+cache=" + str(args.cache),
             "+control=" + str(int(args.scenario == "control")),
             "+persistence=" + str(int(args.scenario == "persistence")),
             "+roundtrip=" + str(int(args.scenario == "roundtrip")),
             "+common=" + str(int(args.memory_service == "common")),
             "+seed=" + str(args.seed)] + (["+benchmark_trace"] if args.benchmark_trace else []),
            "simulate",
            allow_mismatch=args.mutation != "none")
        if args.mutation != "none":
            command = experiment.receipt["commands"][-1]
            if command["exit"] == 0 or expected_assertion not in text:
                raise RuntimeError("mutant was not rejected by the intended public-pin assertion")
            experiment.receipt["comparison_summary"] = "EXPECTED_CHECKER_REJECTION: " + text.strip()
            experiment.finish(0)
            return 0
        marker = ("SYSTEM_DDR_ROUNDTRIP_CHECKED beats=16 reads=32 writes=16 "
                  if args.scenario == "roundtrip" else "SYSTEM_CHECKED ")
        if marker not in text:
            raise RuntimeError("missing executed connected-top comparison summary")
        readbacks = (directory / "readback.hex").read_text().splitlines()
        image_beats = 16 if args.scenario == "roundtrip" else len(memory) // 64
        if len(readbacks) != image_beats * 2:
            raise RuntimeError("readback count mismatch")
        expected_hash = hashlib.sha256(memory[:image_beats * 64]).hexdigest()
        observed_hashes = []
        for half in (readbacks[:image_beats], readbacks[image_beats:]):
            data = b"".join(int(line, 16).to_bytes(64, "little") for line in half)
            observed_hashes.append(hashlib.sha256(data).hexdigest())
            if observed_hashes[-1] != expected_hash:
                raise RuntimeError("independent host-readback hash mismatch")
        experiment.receipt["readback_sha256"] = observed_hashes
        experiment.receipt["readback_bytes_per_pass"] = image_beats * 64
        experiment.receipt["comparison_summary"] = "\n".join(
            line for line in text.strip().splitlines() if not line.startswith("BENCH_"))
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, ArithmeticError) as error:
        experiment.finish(1, error)
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
