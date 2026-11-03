"""Declared boundary tuples, reset-visible ABI checks and explicit parameter rejection.

This matrix establishes elaboration/startup, not full architectural execution
at every tuple. Compiled architectural tests separately exercise transactions.
"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT
from fp2_synthesis_probe import COMPACT_TOP


DEFAULT = {
    "NUM_LAYERS": 28, "HIDDEN_SIZE": 1536, "INTERMEDIATE_SIZE": 8960,
    "NUM_Q_HEADS": 12, "NUM_KV_HEADS": 2, "HEAD_DIM": 128, "GROUP_SIZE": 128,
    "AWQ_BITS": 4, "VOCAB_SIZE": 151936, "MAX_SEQ_LEN": 32768,
    "BANKS": 4, "CACHE_MODE": 0, "CACHE_BLOCK": 16, "QUEUE_DEPTH": 3,
    "FP_FORMAT": 0, "WEIGHT_MODE": 0, "ACCEL_ENABLE": 1, "COUNTER_BITS": 64,
}


def compact(**overrides):
    return {**DEFAULT, **COMPACT_TOP, **overrides}


LEGAL_CONFIGURATIONS = (
    ("compact-native-tail", compact()),
    ("28-layer-odd-sequence", compact(NUM_LAYERS=28, MAX_SEQ_LEN=17, BANKS=4, QUEUE_DEPTH=16)),
    ("head-four-mx-weight", compact(HEAD_DIM=4, NUM_Q_HEADS=12, NUM_KV_HEADS=2,
                                   INTERMEDIATE_SIZE=8, CACHE_BLOCK=4, MAX_SEQ_LEN=1,
                                   BANKS=2, QUEUE_DEPTH=1, WEIGHT_MODE=2)),
    ("minimum-head-last-position", compact(HEAD_DIM=2, NUM_Q_HEADS=24, NUM_KV_HEADS=4,
                                         INTERMEDIATE_SIZE=8, CACHE_BLOCK=2,
                                         MAX_SEQ_LEN=32768, QUEUE_DEPTH=1)),
    ("native-weight-mx-kv", compact(CACHE_MODE=2, MAX_SEQ_LEN=17, BANKS=2)),
    ("mx-weight-and-kv", compact(WEIGHT_MODE=2, CACHE_MODE=2, BANKS=4, QUEUE_DEPTH=16)),
    ("mx-weight-single-position", compact(WEIGHT_MODE=2, MAX_SEQ_LEN=1, QUEUE_DEPTH=1)),
    ("actual-default-product", DEFAULT.copy()),
    ("literal-compatibility-bf16", compact(ACCEL_ENABLE=0, BANKS=2, QUEUE_DEPTH=1)),
    ("preserved-fp16", compact(FP_FORMAT=1, BANKS=4, QUEUE_DEPTH=16, MAX_SEQ_LEN=17)),
    ("preserved-awq", compact(WEIGHT_MODE=1)),
    ("preserved-int8-cache", compact(CACHE_MODE=1, BANKS=2)),
)


ILLEGAL_CONFIGURATIONS = tuple(
    (f"illegal-{name.lower()}-{value}", compact(**{name: value}))
    for name, value in (
        ("NUM_LAYERS", 0), ("NUM_LAYERS", 29), ("HIDDEN_SIZE", 0),
        ("INTERMEDIATE_SIZE", 0), ("NUM_Q_HEADS", 0), ("NUM_KV_HEADS", 0),
        ("HEAD_DIM", 0), ("HEAD_DIM", 3), ("GROUP_SIZE", 0), ("AWQ_BITS", 3),
        ("VOCAB_SIZE", 0), ("VOCAB_SIZE", 151937), ("MAX_SEQ_LEN", 0),
        ("MAX_SEQ_LEN", 32769), ("BANKS", 3), ("CACHE_BLOCK", 0),
        ("CACHE_BLOCK", 3), ("QUEUE_DEPTH", 0), ("QUEUE_DEPTH", 17),
        ("COUNTER_BITS", 0), ("COUNTER_BITS", 65), ("FP_FORMAT", 2),
        ("WEIGHT_MODE", 3), ("CACHE_MODE", 3), ("ACCEL_ENABLE", 2),
    )
) + (
    ("mx-with-disabled-acceleration", compact(ACCEL_ENABLE=0, WEIGHT_MODE=2)),
    ("mx-with-fp16", compact(FP_FORMAT=1, CACHE_MODE=2)),
    ("wrong-six-query-ratio", compact(HIDDEN_SIZE=32, NUM_Q_HEADS=4)),
    ("address-product-overflow", compact(ACCEL_ENABLE=0, NUM_LAYERS=2147483647)),
)


OUTPUTS = {
    "token_ready": 1, "logit_valid": 1, "logit_index": 32, "logit_data": 32,
    "done": 1, "error": 1, "cancel_done": 1,
    "mem_req_valid": "SB", "mem_req_write": "SB", "mem_req_kind": "SB*4",
    "mem_req_layer": "SB*32", "mem_req_proj": "SB*3", "mem_req_row": "SB*32",
    "mem_req_col": "SB*32", "mem_req_wdata": "SB*32", "mem_req_tag": "SB*64",
    "mem_rsp_ready": "SB", "ddr_req_valid": 1, "ddr_req_write": 1,
    "ddr_req_kind": 4, "ddr_req_layer": 32, "ddr_req_proj": 3,
    "ddr_req_row": 32, "ddr_req_col": 32, "ddr_req_format": 2,
    "ddr_req_tag": 64, "ddr_req_wdata": 512, "ddr_req_wstrb": 64,
    "ddr_rsp_ready": 1, "csr_req_ready": 1, "csr_rsp_valid": 1,
    "csr_rsp_rdata": 32, "csr_rsp_error": 1,
}
INPUTS = {
    "cancel": 1, "token_valid": 1, "token_id": 32, "token_pos": 32,
    "new_sequence": 1, "token_phase": 1, "logit_ready": 1,
    "mem_req_ready": "SB", "mem_rsp_valid": "SB", "mem_rsp_error": "SB",
    "mem_rsp_rdata": "SB*32", "mem_rsp_tag": "SB*64",
    "ddr_req_ready": 1, "ddr_rsp_valid": 1, "ddr_rsp_error": 1,
    "ddr_rsp_tag": 64, "ddr_rsp_rdata": 512,
    "csr_req_valid": 1, "csr_req_write": 1, "csr_req_addr": 16,
    "csr_req_wdata": 32, "csr_req_wstrb": 4, "csr_rsp_ready": 1,
}


def width(expression, banks):
    if isinstance(expression, int):
        return expression
    pieces = expression.split("*")
    return (banks if banks in (1, 2, 4) else 1) * (int(pieces[1]) if len(pieces) == 2 else 1)


def testbench(parameters):
    declarations = "".join(f"wire [{width(size, parameters['BANKS'])-1}:0] {name};\n"
                           for name, size in OUTPUTS.items())
    connections = [".clk(clk)", ".rst_n(rst_n)"]
    connections.extend(f".{name}({name})" for name in OUTPUTS)
    connections.extend(f".{name}({width(size, parameters['BANKS'])}'d0)"
                       for name, size in INPUTS.items())
    params = ",".join(f".{name}({value})" for name, value in parameters.items())
    payload = "{" + ",".join(OUTPUTS) + "}"
    return f"""
module tb;
  reg clk=0; always #5 clk=~clk;
  reg rst_n;
  {declarations}
  anvil_q2_fp2_top #({params}) accelerator({','.join(connections)});
  wire reset_ok=({payload} === 0);
  always @(posedge clk) if(!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET posedge");
  always @(negedge clk) if(!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET negedge");
  initial begin
    rst_n=0; #1;
    if(reset_ok !== 1'b1) $fatal(1,"RESET time0");
    repeat(2) @(negedge clk); rst_n=1;
    repeat(3) @(posedge clk); #1;
    if((^{payload}) === 1'bx || token_ready !== 1'b1 || csr_req_ready !== 1'b1 ||
       logit_valid !== 1'b0 || done !== 1'b0 || error !== 1'b0) $fatal(1,"STARTUP_OR_X");
    $display("OBSERVED_STARTUP 1 1 0 0 0"); $finish;
  end
endmodule
"""


def run(probe, selection="all"):
    probe.version("iverilog", "-V")
    probe.version("vvp", "-V")
    sources = sorted((ROOT / "anvil_q2_fp_reference/rtl").glob("*.sv"))
    sources += sorted((ROOT / "rtl").glob("*.sv"))
    cases = []
    if selection in ("all", "legal"):
        cases += [(name, parameters, True) for name, parameters in LEGAL_CONFIGURATIONS]
    if selection in ("all", "illegal"):
        cases += [(name, parameters, False) for name, parameters in ILLEGAL_CONFIGURATIONS]
    records = []
    for name, parameters, legal in cases:
        source, binary = probe.directory / f"{name}.sv", probe.directory / f"{name}.vvp"
        source.write_text(testbench(parameters))
        probe.command(["iverilog", "-g2012", "-Wall", "-s", "tb", "-o", str(binary),
                       *map(str, sources), str(source)], f"{name}-compile")
        output = probe.command(["vvp", str(binary)], f"{name}-simulation", allow_nonzero=not legal)
        exit_status = probe.receipt["commands"][-1]["exit_status"]
        observed = output.read_text()
        if legal:
            probe.compare("legal-startup-observation", True,
                          observed.count("OBSERVED_STARTUP 1 1 0 0 0") == 1 and exit_status == 0,
                          {"configuration": name})
        else:
            probe.compare("explicit-parameter-rejection", True,
                          exit_status != 0 and "PARAMETER ERROR" in observed and "OBSERVED_STARTUP" not in observed,
                          {"configuration": name, "exit_status": exit_status})
        records.append({"name": name, "parameters": parameters, "legal": legal,
                        "coverage": "elaboration and reset/startup" if legal else "compiled explicit rejection",
                        "stdout": str(output.relative_to(ROOT)), "exit_status": exit_status})
    probe.summary["configuration_matrix"] = records
    probe.compare("configuration-record-count", len(cases), len(records), {})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", choices=("all", "legal", "illegal"), default="all")
    args = parser.parse_args()
    probe = Probe("configuration")
    try:
        run(probe, args.selection)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
