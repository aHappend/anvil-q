"""Bounded advisory array experiment, not the admitted complete L1 suite."""

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys
import time
from datetime import datetime, timezone

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import array_result, pack_words
from scheduling import run_process

SOURCES = [
    "rtl/anvil_q2_ht_00_fp_pkg.sv",
    "rtl/anvil_q2_ht_tensor_lane.sv",
    "rtl/anvil_q2_ht_add128_pipe.sv",
    "rtl/anvil_q2_ht_fp32_add_pipe.sv",
    "rtl/anvil_q2_ht_tensor_array.sv",
    "tests/array_tb.sv",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def vectors(path):
    count = 0
    h = hashlib.sha256()
    with path.open("wb") as stream:
        for seed in (11, 29, 101):
            rng = random.Random(seed)
            for index in range(420):
                mode = int(index >= 140 and index % 3 != 0)
                keep = (1 << index) if index < 128 else rng.getrandbits(128)
                if 128 <= index < 240:
                    keep = (1 << 128) - 1
                activations = [rng.randint(-(1 << 31), (1 << 31) - 1) for _ in range(128)]
                weights = [rng.randrange(16) for _ in range(128)]
                zeros = [rng.randrange(16) for _ in range(128)]
                scales = [rng.choice((0, 0x8000, 1, 0xff, 0x100, 0x3c00,
                                      0x7bff, rng.randrange(0x7c00))) for _ in range(128)]
                bf16 = [rng.choice((0, 0x8000, 1, 0x8001, 0x7f, 0x80,
                                    0x3f80, 0xbf80, 0x7f7f, rng.randrange(0x7f80)))
                        for _ in range(128)]
                if index < 128:
                    activations[index] = index + 1
                    weights[index] = 15
                    zeros[index] = 0
                    scales[index] = 0x3c00
                if index >= 128 and index % 31 == 30:
                    mode = 1
                    activations = [rng.choice((0, 1, -1, 65536, -65536,
                                               65792, 66304, 2147483647))
                                   for _ in range(128)]
                    bf16 = [rng.choice((0, 0x8000, 1, 0x8001, 0x7f, 0x807f,
                                        0x3f80, 0xbf80)) for _ in range(128)]
                if index >= 128 and index % 47 == 46:
                    lane = index % 128
                    keep |= 1 << lane
                    if mode:
                        bf16[lane] = rng.choice((0x7f80, 0x7fc0, 0xff80))
                    else:
                        scales[lane] = rng.choice((0x7c00, 0x7e00, 0xbc00))
                total, fp, error = array_result(mode, keep, activations,
                                                weights, zeros, scales, bf16)
                gap = 0 if index < 260 else rng.randrange(3)
                ready = 1 if index < 260 else rng.randrange(2)
                fields = [str(gap), str(ready), str(mode), f"{keep:032x}",
                          f"{pack_words(activations, 32):01024x}",
                          f"{pack_words(weights, 4):0128x}",
                          f"{pack_words(zeros, 4):0128x}",
                          f"{pack_words(scales, 16):0512x}",
                          f"{pack_words(bf16, 16):0512x}",
                          f"{total:032x}", f"{fp:08x}", str(error)]
                line = (" ".join(fields) + "\n").encode("ascii")
                stream.write(line)
                h.update(line)
                count += 1
    return {"count": count, "sha256": h.hexdigest(), "seeds": [11, 29, 101],
            "scope": "D1 chunk arithmetic only; no other domain or integrated coverage"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="iverilog")
    parser.add_argument("--mutation", choices=("none", "awq-zero", "upper-bank", "bf16-round",
                                              "latency"),
                        default="none")
    parser.add_argument("--repair-of", help="Project-relative receipt for a harness repair")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    output = args.output
    if output.is_absolute() or ".." in output.parts:
        parser.error("output must be project-relative")
    destination = root / output
    destination.mkdir(parents=True, exist_ok=False)
    receipt = {"schema": 1, "advisory": True, "argv": sys.orig_argv,
               "cwd": ".", "start": now(), "timeout_s": 3600,
               "commands": [], "source_hashes": {}, "exit": None,
               "timed_out": False}
    if args.repair_of:
        receipt["repair_of"] = args.repair_of
    exit_code = 1

    def run(argv, label, timeout=3600, allow_mismatch=False):
        command = {"argv": argv, "cwd": ".", "start": now(),
                   "timeout_s": timeout, "stdout": str(output / (label + ".stdout")),
                   "stderr": str(output / (label + ".stderr"))}
        receipt["commands"].append(command)
        start = time.monotonic()
        with (root / command["stdout"]).open("xb") as stdout, \
                (root / command["stderr"]).open("xb") as stderr:
            run_process(root, argv, command, stdout, stderr, timeout)
            if command["timed_out"]:
                receipt["timed_out"] = True
        command["end"] = now()
        command["duration_s"] = time.monotonic() - start
        if command["timed_out"] or (command["exit"] != 0 and not allow_mismatch):
            raise RuntimeError(f"{label} failed; see {command['stdout']} and {command['stderr']}")
        return (root / command["stdout"]).read_text()

    try:
        for name in SOURCES + ["tests/reference.py", "tests/array_check.py", "tests/scheduling.py"]:
            data = (root / name).read_bytes()
            receipt["source_hashes"][name] = hashlib.sha256(data).hexdigest()
            snapshot = destination / "sources" / name
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_bytes(data)
        tools = [("python3", ["--version"])]
        if args.simulator == "iverilog":
            tools += [("iverilog", ["-V"]), ("vvp", ["-V"])]
        else:
            tools += [("verilator", ["--version"]), ("g++", ["--version"])]
        for tool, options in tools:
            if shutil.which(tool) is None:
                raise RuntimeError("missing prerequisite: " + tool)
            run([tool] + options, tool + "-version")
        receipt["vectors"] = vectors(destination / "vectors.txt")
        compile_sources = [str(output / "sources" / name) for name in SOURCES]
        if args.mutation != "none":
            mutations = {
                "awq-zero": ("rtl/anvil_q2_ht_tensor_lane.sv",
                             "$signed({1'b0,weight0})-$signed({1'b0,zero0})",
                             "$signed({1'b0,weight0})-$signed({1'b0,zero0})+5'sd1"),
                "upper-bank": ("rtl/anvil_q2_ht_tensor_array.sv",
                               ".keep(s_valid && s_keep[J])",
                               ".keep(s_valid && s_keep[J] && J<112)"),
                "bf16-round": ("rtl/anvil_q2_ht_tensor_lane.sv",
                               "(|normalized_act1[22:0]) || normalized_act1[24]",
                               "(|normalized_act1[22:0]) || 1'b1"),
                "latency": ("rtl/anvil_q2_ht_tensor_array.sv",
                            "assign m_valid = rst_n && valid_pipeline[34];",
                            "assign m_valid = rst_n && valid_pipeline[33];"),
            }
            name, old, new = mutations[args.mutation]
            original = (destination / "sources" / name).read_text()
            if original.count(old) != 1:
                raise RuntimeError("mutation anchor is not unique")
            mutated = original.replace(old, new)
            mutant_path = destination / "mutant" / name
            mutant_path.parent.mkdir(parents=True, exist_ok=True)
            mutant_path.write_text(mutated)
            diff = "".join(difflib.unified_diff(original.splitlines(True),
                                               mutated.splitlines(True),
                                               fromfile=name, tofile="mutant/" + name))
            (destination / "mutation.diff").write_text(diff)
            receipt["mutation"] = {"name": args.mutation, "path": str(output / "mutant" / name),
                                   "sha256": hashlib.sha256(mutated.encode()).hexdigest(),
                                   "required_assertion": ("LATENCY tag=" if args.mutation == "latency"
                                                          else "NUMERICAL tag=")}
            compile_sources[SOURCES.index(name)] = str(output / "mutant" / name)
        if args.simulator == "iverilog":
            run(["iverilog", "-g2012", "-Wall", "-s", "array_tb", "-o",
                 str(output / "array.vvp")] + compile_sources, "compile")
            argv = ["vvp", str(output / "array.vvp")]
        else:
            run(["verilator", "--binary", "--timing", "-Wno-fatal", "--top-module", "array_tb",
                 "--Mdir", str(output / "obj"), "-MAKEFLAGS", "VK_PCH_I_FAST= VK_PCH_I_SLOW=",
                 "-o", "array_sim"] + compile_sources, "compile")
            argv = [str(output / "obj" / "array_sim")]
        text = run(argv + ["+vectors=" + str(output / "vectors.txt")], "simulate",
                   allow_mismatch=args.mutation != "none")
        if args.mutation != "none":
            if (receipt["commands"][-1]["exit"] == 0 or
                    receipt["mutation"]["required_assertion"] not in text):
                raise RuntimeError("mutant was not rejected by the intended comparison assertion")
            receipt["comparison_summary"] = "EXPECTED_CHECKER_REJECTION: " + text.strip()
        else:
            if f"ARRAY_CHECKED accepted={receipt['vectors']['count']} compared={receipt['vectors']['count']} " not in text:
                raise RuntimeError("missing executed comparison summary")
            receipt["comparison_summary"] = text.strip()
        exit_code = 0
    except (OSError, RuntimeError) as error:
        receipt["failure"] = str(error)
        print(str(error), file=sys.stderr)
    finally:
        receipt["end"] = now()
        receipt["exit"] = exit_code
        (destination / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(output / "receipt.json")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
