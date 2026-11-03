"""Independent CSR register/counter model and pre-/post-edge vector comparisons.

Snapshot copies pre-edge counters; clear wins over concurrent increments.
Response acceptance and retirement are different edges, even with ready high.
This suite reads every global/domain pair and tests stalls, invalid accesses,
all partial strobes, busy configuration, reset mid-response and five domains.
No internal DUT paths or simulator-only initial counter values are used.
"""

import argparse
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagnostic import hexfile, simulate
from evidence import Evidence, rel


FIELDS = dict(rst_n=1, csr_valid=1, csr_write=1, csr_addr=12,
              csr_wdata=32, csr_wstrb=4, csr_rsp_ready=1,
              token_accept=1, token_complete=1, token_error=1, reasoning_active=1,
              shared_busy=1, prefetch_busy=1, domain_id=3,
              cache_read_bytes=32, cache_write_bytes=32, cache_dense_equiv_bytes=32,
              expert_read_bytes=32, expert_dense_equiv_bytes=32,
              other_read_bytes=32, other_write_bytes=32)
OUTPUTS = dict(csr_ready=1, csr_rsp_valid=1, csr_rdata=32, csr_error=1,
               domain_select=3, think_begin_token=32, think_end_token=32)
MASK = (1 << 64)-1


def pack(fields, values):
    result = 0
    for name, width in fields.items():
        result = result << width | values[name]
    return result


class CSRModel:
    def __init__(self):
        self.reset()

    def reset(self):
        self.armed = False
        self.response = None
        self.response_data = 0
        self.busy = False
        self.domain = 0
        self.begin, self.end = 6, 7
        self.live = [0]*15
        self.domains = [[0]*6 for _ in range(5)]
        self.saved = [0]*15
        self.saved_domains = [[0]*6 for _ in range(5)]
        self.snapshot_valid = False
        self.overflow = False

    def outputs(self, rst_n):
        if not rst_n:
            return {name: 0 for name in OUTPUTS}
        return dict(csr_ready=int(self.armed and self.response is None),
                    csr_rsp_valid=int(self.response is not None),
                    csr_rdata=self.response_data,
                    csr_error=int(self.response is not None and self.response[1]),
                    domain_select=self.domain,
                    think_begin_token=self.begin, think_end_token=self.end)

    def access(self, v):
        address = v["csr_addr"]
        if address % 4:
            return 0, True
        if v["csr_write"]:
            if v["csr_wstrb"] != 15:
                return 0, True
            data = v["csr_wdata"]
            if address == 8:
                return 0, data > 3
            if address in (16, 20, 24):
                illegal = self.busy or v["token_accept"] or data >= (5 if address == 16 else 8)
                return 0, bool(illegal)
            return 0, True
        fixed = {0: 0x41445631, 4: 0x10000, 8: 0,
                 12: int(self.busy) | int(self.snapshot_valid)*2 | int(self.overflow)*4,
                 16: self.domain, 20: self.begin, 24: self.end}
        if address in fixed:
            return fixed[address], False
        if 0x40 <= address < 0xb8:
            index, high = divmod(address-0x40, 8)
            value = self.saved[index] if self.snapshot_valid else 0
            return (value >> (32 if high else 0)) & 0xffffffff, False
        if 0x100 <= address < 0x240:
            domain, offset = divmod(address-0x100, 0x40)
            if offset < 48:
                index, high = divmod(offset, 8)
                value = self.saved_domains[domain][index] if self.snapshot_valid else 0
                return (value >> (32 if high else 0)) & 0xffffffff, False
        return 0, True

    def tick(self, v):
        if not v["rst_n"]:
            self.reset()
            return None
        accepted = v["csr_valid"] and self.armed and self.response is None
        retired = self.response is not None and v["csr_rsp_ready"]
        result = self.access(v) if accepted else None
        clear = accepted and v["csr_write"] and not result[1] and v["csr_addr"] == 8 and v["csr_wdata"] & 1
        snapshot = accepted and v["csr_write"] and not result[1] and v["csr_addr"] == 8 and v["csr_wdata"] & 2 and not clear
        if snapshot:
            self.saved = self.live.copy()
            self.saved_domains = [row.copy() for row in self.domains]
            self.snapshot_valid = True
        increments = [
            1, v["token_accept"], v["token_error"], v["token_accept"]*v["reasoning_active"],
            v["reasoning_active"], v["cache_read_bytes"], v["cache_write_bytes"],
            v["cache_dense_equiv_bytes"], v["expert_read_bytes"], v["expert_dense_equiv_bytes"],
            v["other_read_bytes"], v["other_write_bytes"], v["shared_busy"],
            v["prefetch_busy"], v["shared_busy"]*v["prefetch_busy"]]
        domain_increments = [
            int(self.busy or v["token_accept"]), v["token_accept"],
            v["token_accept"]*v["reasoning_active"],
            v["cache_read_bytes"]+v["expert_read_bytes"]+v["other_read_bytes"],
            v["cache_write_bytes"]+v["other_write_bytes"], v["expert_read_bytes"]]
        if clear:
            self.live = [0]*15
            self.domains = [[0]*6 for _ in range(5)]
            self.saved = [0]*15
            self.saved_domains = [[0]*6 for _ in range(5)]
            self.snapshot_valid = self.overflow = False
        elif self.armed:
            for i, increment in enumerate(increments):
                total = self.live[i]+increment
                self.overflow |= total > MASK
                self.live[i] = min(MASK, total)
            if v["domain_id"] < 5:
                row = self.domains[v["domain_id"]]
                for i, increment in enumerate(domain_increments):
                    total = row[i]+increment
                    self.overflow |= total > MASK
                    row[i] = min(MASK, total)
        if v["token_complete"] or v["token_error"]:
            self.busy = False
        elif v["token_accept"]:
            self.busy = True
        if retired:
            self.response = None
        if accepted:
            self.response = result
            self.response_data = 0 if v["csr_write"] or result[1] else result[0]
            if v["csr_write"] and not result[1]:
                if v["csr_addr"] == 16:
                    self.domain = v["csr_wdata"]
                elif v["csr_addr"] == 20:
                    self.begin = v["csr_wdata"]
                elif v["csr_addr"] == 24:
                    self.end = v["csr_wdata"]
        self.armed = True
        return result


def vectors():
    model = CSRModel()
    inputs, before, after, ledger = [], [], [], []
    defaults = {name: 0 for name in FIELDS}
    defaults.update(rst_n=1, csr_rsp_ready=1)
    rng = random.Random(203)
    coverage = dict(accepted=0, errors=0, response_stalls=0, reset_response=0,
                    simultaneous_clear_events=0, snapshot_reads=0)

    def step(**overrides):
        v = defaults | overrides
        pre = model.outputs(v["rst_n"])
        if pre["csr_rsp_valid"] and not v["csr_rsp_ready"]:
            coverage["response_stalls"] += 1
        if not v["rst_n"] and model.response is not None:
            coverage["reset_response"] += 1
        result = model.tick(v)
        if result is not None:
            coverage["accepted"] += 1
            coverage["errors"] += result[1]
            ledger.append(dict(edge=len(inputs), addr=v["csr_addr"], write=v["csr_write"],
                               wdata=v["csr_wdata"], wstrb=v["csr_wstrb"],
                               expected_data=0 if v["csr_write"] or result[1] else result[0],
                               expected_error=result[1]))
            if v["csr_addr"] == 8 and v["csr_write"] and v["csr_wdata"] & 1 and not result[1]:
                if v["cache_read_bytes"] and v["token_accept"]:
                    coverage["simultaneous_clear_events"] += 1
            if not v["csr_write"] and v["csr_addr"] >= 0x40 and not result[1]:
                coverage["snapshot_reads"] += 1
        inputs.append(pack(FIELDS, v))
        before.append(pack(OUTPUTS, pre))
        after.append(pack(OUTPUTS, model.outputs(v["rst_n"])))

    def request(address, write=False, data=0, strobe=15, stall=0, **events):
        while not model.outputs(1)["csr_ready"]:
            step()
        step(csr_valid=1, csr_write=int(write), csr_addr=address,
             csr_wdata=data, csr_wstrb=strobe, **events)
        for _ in range(stall):
            # Keep another valid request asserted through the held response;
            # it must neither change the response nor mutate configuration.
            step(csr_valid=1, csr_write=1, csr_addr=16, csr_wdata=4,
                 csr_wstrb=15, csr_rsp_ready=0)
        step()

    step(rst_n=0)
    step(rst_n=0)
    step()
    step()
    for addr in (0, 4, 8, 12, 16, 20, 24):
        request(addr, stall=3)
    request(8, True, 3, token_accept=1, reasoning_active=1,
            cache_read_bytes=0xffffffff, expert_read_bytes=0xffffffff)
    request(12)
    request(16, True, 2)  # busy configuration
    request(20, True, 3, token_complete=1)  # completion pre-edge is still busy
    request(24, True, 4)
    for domain in range(5):
        request(16, True, domain)
        request(16)
        step(domain_id=domain, token_accept=1, reasoning_active=1)
        for _ in range(7):
            step(domain_id=domain, reasoning_active=1,
                 shared_busy=1, prefetch_busy=1,
                 **{name: rng.randint(0, 0xffffffff) for name in FIELDS if name.endswith("_bytes")})
        step(domain_id=domain, token_complete=1, token_error=domain % 2)
    request(8, True, 2, cache_read_bytes=17, other_write_bytes=29, stall=5)
    for address in list(range(0x40, 0xb8, 4)) + [
            0x100+domain*0x40+offset for domain in range(5) for offset in range(0, 48, 4)]:
        request(address)
    # Repeat reads must not clear snapshots, despite additional live events.
    request(0x68, other_read_bytes=0xffffffff)
    request(0x68)
    for strobe in range(15):
        for address in (8, 16, 20, 24):
            request(address, True, 1, strobe)
    for address in (1, 3, 0x1c, 0x3c, 0xb8, 0x130, 0x17c, 0x240, 0xffc):
        request(address)
    for address, data in ((16, 5), (20, 8), (24, 0xffffffff), (8, 4)):
        request(address, True, data)
    for address in (0, 4, 12, 0x40, 0x104):
        request(address, True, 0xffffffff)
    request(8, True, 1)
    request(12)
    for address in (0x40, 0x44, 0x68, 0x100, 0x10c):
        request(address)
    step(csr_valid=1, csr_addr=0)
    step(rst_n=0, csr_rsp_ready=0)
    step(rst_n=0)
    step()
    step()
    request(20)
    request(24)
    if any(count == 0 for count in coverage.values()):
        raise AssertionError(f"CSR missing checked events: {coverage}")
    return inputs, before, after, ledger, coverage


def csr_bench(evidence):
    inputs, before, after, ledger, coverage = vectors()
    image = evidence.path / "checkpoint-images"
    image.mkdir()
    hexfile(image / "inputs.hex", inputs, (sum(FIELDS.values())+3)//4)
    hexfile(image / "before.hex", before, (sum(OUTPUTS.values())+3)//4)
    hexfile(image / "after.hex", after, (sum(OUTPUTS.values())+3)//4)
    (evidence.path / "csr-fixtures.json").write_text(json.dumps(
        dict(edges=len(inputs), accesses=ledger, coverage=coverage), indent=2)+"\n")
    declarations = "\n".join(f"reg [{width-1}:0] {name}=0;" for name, width in FIELDS.items())
    declarations += "\n"+"\n".join(f"wire [{width-1}:0] {name};" for name, width in OUTPUTS.items())
    pins = ",\n".join(f".{name}({name})" for name in list(FIELDS)+list(OUTPUTS))
    bench = BENCH.replace("@DECLARATIONS@", declarations).replace("@PINS@", pins)
    bench = bench.replace("@INPUTS@", ",".join(FIELDS)).replace("@OUTPUTS@", ",".join(OUTPUTS))
    bench = bench.replace("@IW@", str(sum(FIELDS.values()))).replace("@OW@", str(sum(OUTPUTS.values())))
    bench = bench.replace("@EDGES@", str(len(inputs)))
    (evidence.path / "csr.sv").write_text(bench)
    return dict(edges=len(inputs), pin_comparisons=2*len(inputs), **coverage)


BENCH = r"""
module tb;
  reg clk=0; always #5 clk=~clk;
  @DECLARATIONS@
  anvil_d1_csr_perf #(.VOCAB_SIZE(8)) device (.clk(clk),@PINS@);
  reg [@IW@-1:0] inputs[0:@EDGES@-1];
  reg [@OW@-1:0] before_values[0:@EDGES@-1],after_values[0:@EDGES@-1];
  integer reset_samples=0;
  task automatic reset_check;
    begin
      if ({@OUTPUTS@} !== 0) $fatal(1,"CSR_RESET_XZ_OR_NONZERO t=%0t",$time);
      reset_samples=reset_samples+1;
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    rst_n=0;
    $readmemh("checkpoint-images/inputs.hex",inputs);
    $readmemh("checkpoint-images/before.hex",before_values);
    $readmemh("checkpoint-images/after.hex",after_values);
`ifdef VERILATOR
    #1;
`else
    #0;
`endif
    reset_check();
    for (integer edge_index=0;edge_index<@EDGES@;edge_index=edge_index+1) begin
      @(negedge clk); #1; {@INPUTS@}=inputs[edge_index];
      @(posedge clk);
      if ({@OUTPUTS@} !== before_values[edge_index])
        $fatal(1,"CSR_PRE_EDGE_MISMATCH edge=%0d actual=%h expected=%h",
          edge_index,{@OUTPUTS@},before_values[edge_index]);
      #1;
      if ({@OUTPUTS@} !== after_values[edge_index])
        $fatal(1,"CSR_POST_EDGE_MISMATCH edge=%0d actual=%h expected=%h",
          edge_index,{@OUTPUTS@},after_values[edge_index]);
    end
    if (reset_samples<5) $fatal(1,"CSR_MISSING_RESET_SAMPLES");
    $display("SUMMARY csr_edges=%0d pin_comparisons=%0d reset=%0d",@EDGES@,@EDGES@*2,reset_samples);
    $finish;
  end
endmodule
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim", choices=("icarus", "verilator"), default="icarus")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    evidence = Evidence("csr-"+args.sim, args.repair_of)
    try:
        summary = csr_bench(evidence)
        summary["observations"] = simulate(evidence, "csr.sv", args.sim)
        evidence.finish("passed", **summary)
        print(summary["observations"].strip())
    except Exception as exc:
        evidence.finish("failed", error=str(exc))
        print(str(exc), file=sys.stderr)
        print(rel(evidence.path / "receipt.json"), file=sys.stderr)
        return 1
    print(rel(evidence.path / "receipt.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
