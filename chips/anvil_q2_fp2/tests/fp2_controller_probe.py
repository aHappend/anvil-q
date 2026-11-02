"""Isolate controller process lowering, preserving the integrated timeout."""

import hashlib
import json
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, SuiteDeadline


ORIGINAL_FAILURE = "evidence/preparation/fp2-synthesis-20261102T180335Z-86389c92/receipt.json"


def run(probe, fixed_destination=False):
    source = ROOT / "rtl/anvil_q2_fp2_controller.sv"
    probe.receipt["diagnostic_scope"] = {
        "original_failure": ORIGINAL_FAILURE,
        "controller_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "claim": "process lowering only; no integrated synthesis or functional equivalence",
    }
    probe.version("yosys", "-V")
    if fixed_destination:
        text = source.read_text()
        for width, lanes in ((16, 32), (8, 64)):
            needle = f"""              for (element=0;element<{lanes};element=element+1)
                if (attention_payload_offset+element<HEAD_DIM) begin
                  if (attention_read_kind[0])
                    value_buffer[{width}*(attention_payload_offset+element)+:{width}]<=
                      rsp_data[{width}*element+:{width}];
                  else key_buffer[{width}*(attention_payload_offset+element)+:{width}]<=
                    rsp_data[{width}*element+:{width}];
                end"""
            replacement = f"""              for (element=0;element<HEAD_DIM;element=element+1)
                if (element>=attention_payload_offset &&
                    element<attention_payload_offset+{lanes}) begin
                  if (attention_read_kind[0])
                    value_buffer[{width}*element+:{width}]<=
                      rsp_data[{width}*(element-attention_payload_offset)+:{width}];
                  else key_buffer[{width}*element+:{width}]<=
                    rsp_data[{width}*(element-attention_payload_offset)+:{width}];
                end"""
            if text.count(needle) != 1:
                raise ValueError(f"controller diagnostic anchor changed ({width}-bit)")
            text = text.replace(needle, replacement, 1)
        source = probe.directory / "controller-disposable.sv"
        source.write_text(text)
        probe.receipt["diagnostic_scope"]["disposable_sha256"] = hashlib.sha256(
            source.read_bytes()).hexdigest()
        probe.receipt["diagnostic_scope"]["change"] = (
            "constant destination element selects, guarded offset-to-source selection; "
            "diagnostic only, admitted RTL unchanged")
    script = probe.directory / "controller.ys"
    script.write_text(
        f"read_verilog -sv -defer {source.relative_to(ROOT)}\n"
        "chparam -set NUM_LAYERS 1 -set HIDDEN_SIZE 48 -set INTERMEDIATE_SIZE 64 "
        "-set NUM_Q_HEADS 6 -set NUM_KV_HEADS 1 -set HEAD_DIM 8 "
        "-set VOCAB_SIZE 16 -set MAX_SEQ_LEN 3 anvil_q2_fp2_controller\n"
        "select -assert-min 1 *anvil_q2_fp2_controller\n"
        "select *anvil_q2_fp2_controller\n"
        "proc\n"
        "stat\n"
        f"write_json {probe.directory.relative_to(ROOT)}/controller.json\n"
    )
    probe.command(["yosys", "-Q", "-T", "-s", str(script.relative_to(ROOT))],
                  "controller-lowering", timeout=120)
    modules = json.loads((probe.directory / "controller.json").read_text())["modules"]
    controllers = [module for name, module in modules.items()
                   if name.endswith("anvil_q2_fp2_controller") and not name.startswith("$abstract")]
    probe.compare("lowered-controller-count", 1, len(controllers), {})
    if len(controllers) != 1:
        raise AssertionError("controller selection did not elaborate exactly one concrete module")
    cells = controllers[0].get("cells", {})
    state = sum("dff" in cell["type"].lower() for cell in cells.values())
    probe.compare("controller-retained-state", True, state > 0, {"state_cells": state})
    probe.compare("controller-remaining-processes", 0,
                  len(controllers[0].get("processes", {})), {})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixed-destination", action="store_true")
    args = parser.parse_args()
    probe = Probe("controller-lowering", repair_of=
                  "evidence/preparation/fp2-controller-lowering-20261102T183843Z-f735b54e/receipt.json")
    probe.receipt["prior_probe_assessment"] = (
        "Prior probe selected an absent unparameterized module; zero lowered processes "
        "invalidate its completion comparison. This run asserts concrete selection and state.")
    try:
        with SuiteDeadline():
            run(probe, args.fixed_destination)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
