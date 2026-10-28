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
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    names = ["rtl/anvil_q2_ht_configuration.sv", "tests/configuration_tb.sv",
             "tests/configuration_check.py", "tests/checkpoint_import.py",
             "tests/rope_reference.py", "tests/retention.py", "data/model/official_inputs.json"]
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    source = None
    try:
        for tool, flag in (("python3", "--version"), ("iverilog", "-V"), ("vvp", "-V")):
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
        binary = str(args.output / "configuration.vvp")
        experiment.run(["iverilog", "-g2012", "-Wall", "-s", "configuration_tb", "-o", binary]
                       + [str(args.output / "sources" / name) for name in names[:2]], "compile")
        text = experiment.run(
            ["vvp", binary, "+descriptors=" + str(args.output / "descriptors.hex"),
             "+mode=" + str(int(args.mode == "bf16")), "+kvbase=" + str(info["kv_base"]),
             "+kvlength=" + str(info["maximum_q16_kv_bytes"])], "simulate", timeout=14400)
        if "CONFIGURATION_CHECKED descriptors=464 " not in text:
            raise RuntimeError("missing default descriptor comparisons")
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
