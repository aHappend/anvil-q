"""Default 28-layer descriptor validation; does not claim DDR population."""

import argparse
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint_import import Source, prepare
from retention import Experiment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mode", choices=("awq", "bf16"), required=True)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    names = ["rtl/anvil_q2_ht_configuration.sv", "tests/configuration_tb.sv",
             "tests/configuration_check.py", "tests/checkpoint_import.py",
             "tests/rope_reference.py", "tests/retention.py", "data/model/official_inputs.json"]
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    source = None
    try:
        for tool, flag in (("python3", "--version"), ("verilator", "--version"),
                           ("g++", "--version"), ("make", "--version")):
            experiment.run([tool, flag], tool + "-version")
        source = Source(root, args.mode)
        info = prepare(source, args.mode, experiment.directory)
        experiment.receipt["checkpoint"] = source.info
        experiment.receipt["layout"] = info
        experiment.receipt["scope"] = (
            "Default 28-layer descriptor/maximum allocation validation only; "
            "no full image loading, default token execution, timing or hardware claim.")
        data = (experiment.directory / "descriptors.bin").read_bytes()
        words = struct.unpack("<" + "I" * (len(data) // 4), data)
        (experiment.directory / "descriptors.hex").write_text(
            "".join(f"{word:08x}\n" for word in words))
        object_directory = args.output / "obj"
        binary = str(object_directory / "configuration")
        experiment.run(
            ["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "1",
             "--unroll-count", "512",
             "--top-module", "configuration_tb", "--Mdir", str(object_directory),
             "-o", "configuration"]
            + [str(args.output / "sources" / name) for name in names[:2]], "compile")
        text = experiment.run(
            [binary, "+descriptors=" + str(args.output / "descriptors.hex"),
             "+mode=" + str(int(args.mode == "bf16")), "+kvbase=" + str(info["kv_base"]),
             "+kvlength=" + str(info["maximum_q16_kv_bytes"])], "simulate", timeout=14400)
        if "CONFIGURATION_CHECKED descriptors=464 " not in text:
            raise RuntimeError("missing default descriptor comparisons")
        if "CONFIGURATION_RAM_CHECKED pipelined=24 invalid=11" not in text:
            raise RuntimeError("missing synchronous descriptor RAM comparisons")
        experiment.receipt["comparison_summary"] = text.strip()
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1
    finally:
        if source is not None:
            source.close()


if __name__ == "__main__":
    raise SystemExit(main())
