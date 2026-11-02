"""Isolate controller process lowering, preserving the integrated timeout."""

import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, SuiteDeadline


ORIGINAL_FAILURE = "evidence/preparation/fp2-synthesis-20261102T180335Z-86389c92/receipt.json"


def run(probe):
    source = ROOT / "rtl/anvil_q2_fp2_controller.sv"
    probe.receipt["diagnostic_scope"] = {
        "original_failure": ORIGINAL_FAILURE,
        "controller_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "claim": "process lowering only; no integrated synthesis or functional equivalence",
    }
    probe.version("yosys", "-V")
    script = probe.directory / "controller.ys"
    script.write_text(
        f"read_verilog -sv -defer {source.relative_to(ROOT)}\n"
        "chparam -set NUM_LAYERS 1 -set HIDDEN_SIZE 48 -set INTERMEDIATE_SIZE 64 "
        "-set NUM_Q_HEADS 6 -set NUM_KV_HEADS 1 -set HEAD_DIM 8 "
        "-set VOCAB_SIZE 16 -set MAX_SEQ_LEN 3 anvil_q2_fp2_controller\n"
        "select anvil_q2_fp2_controller\n"
        "proc\n"
        "stat\n"
    )
    probe.command(["yosys", "-Q", "-T", "-s", str(script.relative_to(ROOT))],
                  "controller-lowering", timeout=120)
    probe.compare("controller-process-lowering-completed", True, True, {})


def main():
    probe = Probe("controller-lowering", repair_of=ORIGINAL_FAILURE)
    try:
        with SuiteDeadline():
            run(probe)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
