"""Bounded process-lowering diagnostic for the legacy packed cache codec."""

import argparse
import hashlib
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment
from synthesis_probe import expand_packages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-select-attribute", action="store_true")
    parser.add_argument("--frontend-only", action="store_true")
    parser.add_argument("--static-write-selects", action="store_true")
    parser.add_argument("--masked-writes", action="store_true")
    args = parser.parse_args()
    experiment = Experiment("codec-lowering", preparation=True, repair_of=[
        "evidence/preparation/synthesis-20261102T115751286843Z/receipt.json"])
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["yosys", "-V"], "version")
        frontend = experiment.directory / "frontend.sv"
        experiment.receipt["frontend_sha256"] = expand_packages(frontend)
        if args.masked_writes:
            text = frontend.read_text()
            start = text.index("module anvil_q3_cache_codec ")
            end = text.index("endmodule", start)
            codec = text[start:end]

            def masked_write(match):
                name, width, value = match.groups()
                mask = (1 << int(width))-1
                return (f"{name}<=({name} & ~(8192'd{mask} << (index*{width}))) | "
                        f"((8192'({value}) & 8192'd{mask}) << (index*{width}));")

            codec, count = re.subn(
                r"(result_payload|result_values)\[index\*(4|8|32)\+:\2\]<=([^;]+);",
                masked_write, codec)
            if count != 7:
                raise AssertionError(f"expected seven dynamic writes, found {count}")
            frontend.write_text(text[:start] + codec + text[end:])
            experiment.receipt["frontend_sha256"] = hashlib.sha256(
                frontend.read_bytes()).hexdigest()
        if args.static_write_selects:
            text = frontend.read_text()
            start = text.index("module anvil_q3_cache_codec ")
            end = text.index("endmodule", start)
            codec = text[start:end]

            def static_write(match):
                name, width, value = match.groups()
                return (f"for (integer frontend_lane=0; frontend_lane<{8192//int(width)}; "
                        f"frontend_lane=frontend_lane+1) "
                        f"if (index==frontend_lane) "
                        f"{name}[frontend_lane*{width}+:{width}]<={value};")

            codec, count = re.subn(
                r"(result_payload|result_values)\[index\*(4|8|32)\+:\2\]<=([^;]+);",
                static_write, codec)
            if count != 7:
                raise AssertionError(f"expected seven dynamic writes, found {count}")
            frontend.write_text(text[:start] + codec + text[end:])
            experiment.receipt["frontend_sha256"] = hashlib.sha256(
                frontend.read_bytes()).hexdigest()
        if args.write_select_attribute:
            text = frontend.read_text()
            start = text.index("module anvil_q3_cache_codec ")
            end = text.index("endmodule", start)
            codec = text[start:end]
            old = "always @(posedge clk or negedge rst_n)"
            if codec.count(old) != 1:
                raise AssertionError("cache codec process anchor changed")
            text = text[:start] + codec.replace(
                old, "(* nowrshmsk *) " + old) + text[end:]
            frontend.write_text(text)
            experiment.receipt["frontend_sha256"] = hashlib.sha256(
                frontend.read_bytes()).hexdigest()
        netlist = experiment.directory / "codec.json"
        commands = (
            f"read_verilog -sv -defer {experiment.rel(frontend)}; "
            "hierarchy -check -top anvil_q3_cache_codec; "
            f"write_rtlil {experiment.rel(experiment.directory/'frontend.il')}; ")
        if not args.frontend_only:
            commands += (
                "proc; opt_expr; opt_clean; check -assert; "
                "memory -nomap; opt_clean; check -assert; "
                "select -assert-none t:$dlatch t:$adlatch t:$div t:$mod; "
                f"stat; write_json {experiment.rel(netlist)}")
        experiment.run([
            "yosys", "-Q", "-T", "-p", commands], "lowering")
    except (RuntimeError, ValueError, AssertionError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
