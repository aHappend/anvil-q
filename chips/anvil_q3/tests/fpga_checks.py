"""Portable FPGA control verification, never a substitute for physical HIL.

Host/bridge tests assert reset at time zero before the first clock, check settled
outputs before that clock, and check outputs in the active region on both edges
while reset is held. Completion records retain the measured reset-edge coverage.
Run from the project root with either iverilog or verilator:
python3 tests/prepare.py --probe host-control --simulator iverilog
python3 tests/prepare.py --probe ddr-bridge --banks 8 --mode 2 --simulator iverilog
"""

import re
from dataclasses import replace

from execution import write_json
from map_checks import regions
from parameters import A


def bridge_case(run, banks=8, mode=0, simulator="iverilog"):
    folder = run.path / f"ddr-bridge-b{banks}-m{mode}-{simulator}"
    folder.mkdir()
    shapes, extent = regions(replace(A, CACHE_MODE=mode))
    scratch_base = shapes[8, 0][0]
    write_json(folder / "inputs.json", {"banks": banks, "cache_mode": mode,
                                      "scratch_base": scratch_base, "required_bytes": extent})
    sources = ["rtl/anvil_q3_multiplier.sv", "rtl/anvil_q3_add128.sv",
               "fpga/anvil_q3_memory_map.sv", "fpga/anvil_q3_ddr_bridge.sv",
               "tests/bridge_tb.sv"]
    if simulator == "iverilog":
        binary = folder / "bridge.vvp"
        run.tool(["iverilog", "-g2012", "-Wall", "-s", "bridge_tb",
                  f"-Pbridge_tb.BANKS={banks}", f"-Pbridge_tb.CACHE_MODE={mode}",
                  "-o", run.rel(binary), *sources])
        command = ["vvp", run.rel(binary)]
    elif simulator == "verilator":
        obj = folder / "obj"
        run.tool(["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                  "--top-module", "bridge_tb", f"-GBANKS={banks}", f"-GCACHE_MODE={mode}",
                  "--Mdir", run.rel(obj), "-o", "bridge", *sources])
        command = [run.rel(obj / "bridge")]
    else:
        raise ValueError(simulator)
    text, receipt = run.tool([*command, f"+scratch_base={scratch_base:x}", f"+extent={extent:x}"])
    counts = re.findall(
        r"^BRIDGE_COMPLETE transactions=(\d+) faults=(\d+) reset_edges=(\d+)$",
        text, re.M)
    if (len(counts) != 1 or tuple(map(int, counts[0][:2])) != (8*banks, banks) or
            int(counts[0][2]) < 5):
        raise AssertionError("incomplete portable DDR bridge comparisons")
    result = {"banks": banks, "cache_mode": mode, "simulator": simulator,
              "reset_edges": int(counts[0][2]),
              "transactions": 8*banks, "wrong_kind_faults": banks, "stdout": receipt["stdout"],
              "scope": "public bridge pins with a synthetic Avalon responder; not physical DDR/HIL"}
    write_json(folder / "result.json", result)
    return result


def host_case(run, simulator="iverilog"):
    folder = run.path / ("host-control-" + simulator)
    folder.mkdir()
    sources = ["fpga/anvil_q3_host_control.sv", "fpga/anvil_q3_reset_release.sv", "tests/host_tb.sv"]
    if simulator == "iverilog":
        binary = folder / "host.vvp"
        run.tool(["iverilog", "-g2012", "-Wall", "-s", "host_tb",
                  "-o", run.rel(binary), *sources])
        command = ["vvp", run.rel(binary)]
    elif simulator == "verilator":
        obj = folder / "obj"
        run.tool(["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                  "--top-module", "host_tb", "--Mdir", run.rel(obj), "-o", "host", *sources])
        command = [run.rel(obj / "host")]
    else:
        raise ValueError(simulator)
    text, receipt = run.tool(command)
    counts = re.findall(
        r"^HOST_CONTROL_COMPLETE checks=(\d+) reset_edges=(\d+)$", text, re.M)
    if len(counts) != 1 or int(counts[0][0]) < 60 or int(counts[0][1]) < 5:
        raise AssertionError("incomplete portable host control comparisons")
    result = {"simulator": simulator, "checks": int(counts[0][0]),
              "reset_edges": int(counts[0][1]), "stdout": receipt["stdout"],
              "scope": "public CSR/control pins; not PCIe endpoint, DDR PHY, fitted timing or HIL"}
    write_json(folder / "result.json", result)
    return result
