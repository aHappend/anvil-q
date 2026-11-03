"""CSR public-pin oracle based on accepted requests and independent event accounting."""

import argparse
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, simulate


TELEMETRY_TB = r"""
module tb;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n;
  reg [9:0] events=0;
  reg [15:0] bytes=0,reuses=0;
  reg req_valid=0,req_write=0,rsp_ready=0;
  reg [15:0] address=0;
  reg [31:0] data=0;
  reg [3:0] strobe=0;
  wire req_ready,rsp_valid,rsp_error;
  wire [31:0] rsp_data;
  anvil_q2_fp2_telemetry #(.COUNTER_BITS(@CW@)) telemetry(
    clk,rst_n,events[0],events[1],events[2],events[3],events[4],bytes,
    events[5],events[6],reuses,events[7],events[8],events[9],
    req_valid,req_write,address,data,strobe,req_ready,rsp_valid,rsp_data,rsp_error,rsp_ready);
  integer fd,n,cycle=0,read_events,read_bytes,read_reuses,read_valid,read_write;
  integer read_address,read_strobe,read_ready,requests=0,responses=0,stalls=0;
  reg [31:0] read_data;
  reg held=0;
  reg [32:0] held_payload;
  wire reset_ok=({req_ready,rsp_valid,rsp_data,rsp_error} === 0);
  string input_path;
  always @(posedge clk) if(!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET posedge");
  always @(negedge clk) if(!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET negedge");
  initial begin
    rst_n=0; #1;
    if(reset_ok !== 1'b1) $fatal(1,"RESET time0");
    repeat(2) @(negedge clk); rst_n=1;
    if(!$value$plusargs("INPUT=%s",input_path)) $fatal(1,"missing INPUT");
    fd=$fopen(input_path,"r"); if(!fd) $fatal(1,"open INPUT");
    while(!$feof(fd)) begin
      n=$fscanf(fd,"%d %d %d %d %d %d %h %d %d\n",read_events,
        read_bytes,read_reuses,read_valid,read_write,read_address,read_data,read_strobe,read_ready);
      if(n!=9) begin if(!$feof(fd)) $fatal(1,"malformed INPUT"); end
      else begin
        events=read_events; bytes=read_bytes; reuses=read_reuses;
        req_valid=read_valid; req_write=read_write; address=read_address;
        data=read_data; strobe=read_strobe; rsp_ready=read_ready;
        @(posedge clk);
        if((^{req_ready,rsp_valid,rsp_error}) === 1'bx) $fatal(1,"CSR_ACTIVE_X");
        if(held && (rsp_valid !== 1'b1 || {rsp_data,rsp_error} !== held_payload))
          $fatal(1,"CSR_STALLED_RESPONSE");
        if(req_valid) begin
          if(req_ready !== 1'b1) $fatal(1,"CSR_NOT_READY_FOR_DIRECTED_REQUEST");
          requests=requests+1; $display("ACCEPT %0d",cycle);
        end
        if(rsp_valid && rsp_ready) begin
          if((^{rsp_data,rsp_error}) === 1'bx) $fatal(1,"CSR_PAYLOAD_X");
          $display("RESPONSE %0d %08h %0d",cycle,rsp_data,rsp_error);
          responses=responses+1;
        end
        held=rsp_valid && !rsp_ready;
        if(held) begin held_payload={rsp_data,rsp_error}; stalls=stalls+1; end
        #1;
        if(req_valid && rsp_valid !== 1'b0) $fatal(1,"CSR_EARLY_RESPONSE");
        @(negedge clk); cycle=cycle+1;
      end
    end
    if(held || rsp_valid || requests!=responses || stalls==0) $fatal(1,"CSR_ACCOUNTING");
    $display("SUMMARY %0d %0d %0d",requests,responses,stalls); $finish;
  end
endmodule
"""


def transactions():
    yield 0, 0, 0, 15
    yield 0, 4, 0, 15
    for address in range(16, 112, 4):
        yield 0, address, 0, 15
    yield 1, 8, 2, 1
    for address in range(16, 112, 4):
        yield 0, address, 0, 15
    yield 1, 8, 3, 1
    for address in range(16, 112, 4):
        yield 0, address, 0, 15
    yield 1, 8, 1, 0
    yield 0, 16, 0, 15
    yield 1, 8, 1, 1
    yield 0, 16, 0, 15
    for address in (0, 4, 16, 20, 108, 1, 7, 9, 15, 112, 65532):
        for write in (0, 1):
            yield write, address, 3, 15


def stimulus(counter_bits):
    rng = random.Random(203)
    live, snapshot = [0] * 12, None
    expected = {}
    rows = []
    maximum = (1 << counter_bits) - 1
    requests = list(transactions())
    for cycle in range(11 * len(requests)):
        flags = 1023 if cycle < 16 else rng.randrange(1024)
        byte_count = 65535 if cycle % 13 == 0 else rng.randrange(129)
        reuse_count = 65535 if cycle % 17 == 0 else 5
        request = cycle % 11 == 0
        write, address, value, strobe = requests[cycle // 11] if request else (0, 0, 0, 0)
        rows.append((flags, byte_count, reuse_count, int(request), write, address, value,
                     strobe, int(cycle % 11 >= 5)))
        if request:
            error, data = False, 0
            if address & 3:
                error = True
            elif address == 0:
                data, error = 0x20200, bool(write)
            elif address == 4:
                data = 15 | ((flags & 1) << 8) | (int(snapshot is not None) << 9)
                error = bool(write)
            elif address == 8:
                pass
            elif 16 <= address <= 108:
                selected = live if snapshot is None else snapshot
                data = (selected[(address - 16) // 8] >> (32 if address & 4 else 0)) & 0xFFFFFFFF
                error = bool(write)
            else:
                error = True
            expected[cycle] = (data, int(error))
        clear = request and write and address == 8 and strobe & 1 and value & 1
        capture = request and write and address == 8 and strobe & 1 and value & 2
        if clear:
            live = [0] * 12
            snapshot = [0] * 12 if capture else None
        else:
            if capture:
                snapshot = live.copy()
            increments = [(flags >> bit) & 1 for bit in range(5)]
            increments += [byte_count, (flags >> 5) & 1, (flags >> 6) & 1,
                           reuse_count, (flags >> 7) & 1, (flags >> 8) & 1, (flags >> 9) & 1]
            live = [min(maximum, count + increment)
                    for count, increment in zip(live, increments, strict=True)]
    return rows, expected


def run(probe, counter_bits=8, simulator="iverilog", override=None):
    rows, expected = stimulus(counter_bits)
    inputs = probe.directory / "inputs.txt"
    inputs.write_text("".join(
        f"{flags} {byte_count} {reuse} {valid} {write} {address} {value:08x} {strobe} {ready}\n"
        for flags, byte_count, reuse, valid, write, address, value, strobe, ready in rows))
    source = probe.directory / "tb.sv"
    source.write_text(TELEMETRY_TB.replace("@CW@", str(counter_bits)))
    output = simulate(probe, source, [override or ROOT / "rtl/anvil_q2_fp2_telemetry.sv"],
                      simulator, [f"+INPUT={inputs.relative_to(ROOT)}"])
    accepted, observed = set(), set()
    pending = []
    summary = None
    for line in output.read_text().splitlines():
        words = line.split()
        if words[:1] == ["ACCEPT"]:
            cycle = int(words[1])
            if cycle in accepted or cycle not in expected:
                raise AssertionError("duplicate/unexpected CSR acceptance")
            accepted.add(cycle)
            pending.append(cycle)
        elif words[:1] == ["RESPONSE"]:
            cycle, data, failed = int(words[1]), int(words[2], 16), int(words[3])
            if not pending:
                raise AssertionError("CSR response without accepted request")
            issue = pending.pop(0)
            observed.add(issue)
            probe.compare("csr-data", expected[issue][0], data, {"issue_cycle": issue})
            probe.compare("csr-error", expected[issue][1], failed, {"issue_cycle": issue})
            probe.compare("csr-latency", issue + 5, cycle, {"issue_cycle": issue})
        elif words[:1] == ["SUMMARY"]:
            summary = tuple(map(int, words[1:]))
    probe.compare("csr-accepted-count", len(expected), len(accepted), {})
    probe.compare("csr-response-count", len(expected), len(observed), {})
    if summary is None:
        raise AssertionError("missing CSR summary")
    probe.compare("csr-real-stalls", True, summary[2] > 0, {})
    probe.summary["counter_bits"] = counter_bits
    probe.summary["requests"] = len(expected)
    probe.summary["coverage"] = ["live/snapshot low/high pairs", "clear+snapshot+increment",
                                 "saturation", "zero extension", "byte-strobe suppression",
                                 "read-only errors", "misalignment", "response stalls"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counter-bits", type=int, choices=(1, 8, 64), default=8)
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="iverilog")
    args = parser.parse_args()
    probe = Probe("telemetry")
    try:
        run(probe, args.counter_bits, args.simulator)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
