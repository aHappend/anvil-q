"""Public-pin controller scenarios and independently modeled CSR transactions."""

import json
import random

from execution import relative


CSR_INPUTS = (
    ("rst_n", 1), ("csr_valid", 1), ("csr_write", 1), ("csr_addr", 12),
    ("csr_wdata", 32), ("csr_wstrb", 4), ("csr_rsp_ready", 1),
    ("busy", 1), ("think_active", 1), ("qk_busy", 1), ("qk_blocked", 1),
    ("arith_error", 1), ("mem_error", 1), ("sequence_done", 1),
    ("direct_tokens", 3), ("think_tokens", 3), ("draft_nodes", 3),
    ("verified_nodes", 3), ("accepted_nodes", 3), ("rejected_nodes", 3),
    ("score_valid", 1), ("score_fp32", 32),
)
CSR_OUTPUTS = (
    ("csr_ready", 1), ("csr_rsp_valid", 1), ("csr_rdata", 32),
    ("csr_error", 1), ("mode_valid", 1), ("mode_value", 1),
)
COUNTER_OFFSETS = (0x010, 0x018, 0x020, 0x028, 0x030, 0x038, 0x040,
                   0x050, 0x058, 0x060, 0x068, 0x070, 0x078)


def pack_fields(fields, values):
    packed = 0
    for name, width in fields:
        value = values.get(name, 0)
        if not 0 <= value < 1 << width:
            raise ValueError(f"invalid {name}={value}")
        packed = (packed << width) | value
    return packed


class CSRModel:
    """Transactions mature one edge after acceptance; events are edge-counted."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.live = [0] * 13
        self.snapshot = [0] * 13
        self.max_score = self.snapshot_max = 0
        self.arith = self.snapshot_arith = self.sequence = 0
        self.sticky = self.desired = 0
        self.reference = {0x084: 0, 0x088: 0, 0x08C: 0,
                          0x090: 0, 0x094: 0, 0x098: 0}
        self.request = None
        self.response = None
        self.mode_pulse = self.mode_bit = 0

    def outputs(self, pins):
        if not pins["rst_n"]:
            return {}
        return {
            "csr_ready": int(self.request is None and self.response is None),
            "csr_rsp_valid": int(self.response is not None),
            "csr_rdata": 0 if self.response is None else self.response[0],
            "csr_error": 0 if self.response is None else self.response[1],
            "mode_valid": self.mode_pulse,
            "mode_value": self.mode_pulse & self.mode_bit,
        }

    def read(self, address, pins):
        fixed = {0: 0x01000001, 4: 3, 8: self.desired,
                 12: pins["busy"] | pins["think_active"] << 1 | self.sticky << 2,
                 0x048: self.snapshot_max, 0x04C: self.snapshot_arith,
                 0x080: self.sequence, **self.reference}
        for index, base in enumerate(COUNTER_OFFSETS):
            fixed[base] = self.snapshot[index] & 0xFFFFFFFF
            fixed[base + 4] = self.snapshot[index] >> 32
        return (fixed[address], 0) if address in fixed else (0, 1)

    def advance(self, pins):
        if not pins["rst_n"]:
            self.reset()
            return
        before = self.outputs(pins)
        accepted = bool(pins["csr_valid"] and before["csr_ready"])
        mature = self.request
        self.request = None
        if self.response is not None and pins["csr_rsp_ready"]:
            self.response = None
        self.mode_pulse = 0
        snapshot = clear = False
        if mature is not None:
            address, write, data, strobes, busy, mode = mature
            error = bool(address & 3 or write and strobes != 15)
            value = 0
            if not error and write:
                if address == 8:
                    error = bool(data & ~7 or busy and (data & 1 != mode or not data & 6))
                    if not error:
                        snapshot, clear = bool(data & 2), bool(data & 4)
                        if not busy:
                            self.desired = self.mode_bit = data & 1
                            self.mode_pulse = 1
                elif address in self.reference:
                    error = bool(busy or address == 0x084 and data > 1 or
                                 address == 0x098 and data not in (1, 2, 3))
                    if not error:
                        self.reference[address] = data
                else:
                    error = True
            elif not error:
                value, error = self.read(address, pins)
            self.response = (value, int(error))
        if snapshot:
            self.snapshot = list(self.live)
            self.snapshot_max, self.snapshot_arith = self.max_score, self.arith
            self.sequence = (self.sequence + 1) & 0xFFFFFFFF
        increments = (
            pins["busy"], pins["busy"] & pins["think_active"],
            pins["busy"] & (1 - pins["think_active"]),
            pins["think_tokens"], pins["direct_tokens"], pins["qk_busy"],
            pins["qk_blocked"], pins["draft_nodes"], pins["verified_nodes"],
            pins["accepted_nodes"], pins["rejected_nodes"], pins["mem_error"],
            pins["sequence_done"],
        )
        if clear:
            self.live = [0] * 13
            self.max_score = self.arith = self.sticky = 0
        else:
            self.live = [(a + b) & 0xFFFFFFFFFFFFFFFF
                         for a, b in zip(self.live, increments)]
            self.arith = (self.arith + pins["arith_error"]) & 0xFFFFFFFF
            self.sticky |= pins["arith_error"] | pins["mem_error"]
            score = pins["score_fp32"] & 0x7FFFFFFF
            if pins["score_valid"] and score < 0x7F800000:
                self.max_score = max(self.max_score, score)
        if accepted:
            self.request = (pins["csr_addr"], pins["csr_write"], pins["csr_wdata"],
                            pins["csr_wstrb"], pins["busy"], pins["think_active"])


def vector_bench(module, inputs, outputs):
    declarations = "\n".join(
        f"  {kind} [{width-1}:0] {name};"
        for fields, kind in ((inputs, "reg"), (outputs, "wire"))
        for name, width in fields
    )
    input_names = ",".join(name for name, _ in inputs)
    output_names = ",".join(name for name, _ in outputs)
    width_in = sum(width for _, width in inputs)
    width_out = sum(width for _, width in outputs)
    connections = ",".join(f".{name}({name})" for name, _ in inputs + outputs)
    return f"""
module control_tb;
  reg clk=0;
  always #5 clk=~clk;
{declarations}
  reg [{width_in-1}:0] stimulus;
  reg [{width_out-1}:0] expected_before,expected_after;
  reg [4095:0] filename;
  integer fd,rc,count=0,responses=0,errors=0,modes=0,stalls=0;
  {module} dut(.clk(clk),{connections});
  task reset_outputs;
    begin
      if ({{{output_names}}}!==0) $fatal(1,"CONTROL_RESET_XZ_OR_NONZERO");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_outputs();
  initial begin
    {{{input_names}}}=0;
    rst_n=0;
    #1;reset_outputs();
    if (!$value$plusargs("vectors=%s",filename)) $fatal(1,"NO_VECTORS");
    fd=$fopen(filename,"r");if (!fd) $fatal(1,"OPEN_VECTORS");
    rc=$fscanf(fd,"%h %h %h\\n",stimulus,expected_before,expected_after);
    while (rc==3) begin
      @(negedge clk);
      #1;{{{input_names}}}=stimulus;
      #1;
      if ({{{output_names}}}!==expected_before)
        $fatal(1,"CONTROL_PRE_COMPARE edge=%0d got=%h expected=%h",
          count,{{{output_names}}},expected_before);
      @(posedge clk);
      if ({{{output_names}}}!==expected_before)
        $fatal(1,"CONTROL_ACTIVE_COMPARE edge=%0d got=%h expected=%h",
          count,{{{output_names}}},expected_before);
      if (csr_rsp_valid && csr_rsp_ready) begin
        responses=responses+1;if (csr_error) errors=errors+1;
      end
      if (csr_rsp_valid && !csr_rsp_ready) stalls=stalls+1;
      if (mode_valid) modes=modes+1;
      #1;
      if ({{{output_names}}}!==expected_after)
        $fatal(1,"CONTROL_POST_COMPARE edge=%0d got=%h expected=%h",
          count,{{{output_names}}},expected_after);
      count=count+1;
      rc=$fscanf(fd,"%h %h %h\\n",stimulus,expected_before,expected_after);
    end
    if (rc!=0 && rc!=-1) $fatal(1,"MALFORMED_VECTORS");
    $display("SUMMARY edges=%0d responses=%0d errors=%0d modes=%0d stalls=%0d",
      count,responses,errors,modes,stalls);
    $finish;
  end
  initial begin repeat (500000) @(posedge clk);$fatal(1,"CYCLE_BOUND");end
endmodule
"""


def csr_vectors():
    model = CSRModel()
    vectors, requests = [], []
    rng = random.Random(203)
    totals = {"responses": 0, "errors": 0, "modes": 0, "stalls": 0}

    def edge(**overrides):
        pins = {name: 0 for name, _ in CSR_INPUTS}
        pins.update(rst_n=1, csr_rsp_ready=1, csr_wstrb=15)
        for name in ("qk_busy", "qk_blocked", "arith_error", "mem_error",
                     "sequence_done", "score_valid"):
            pins[name] = rng.randrange(2)
        for name in ("direct_tokens", "think_tokens", "draft_nodes", "verified_nodes",
                     "accepted_nodes", "rejected_nodes"):
            pins[name] = rng.randrange(6)
        pins["score_fp32"] = rng.choice((0x3F800000, 0xC1200000, 0x7F800000,
                                        0x7FC00001, 0x00000001, 0x41000000))
        pins.update(overrides)
        if not pins["rst_n"]:
            model.reset()
        before = model.outputs(pins)
        if before.get("csr_rsp_valid"):
            if pins["csr_rsp_ready"]:
                totals["responses"] += 1
                totals["errors"] += before["csr_error"]
            else:
                totals["stalls"] += 1
        totals["modes"] += before.get("mode_valid", 0)
        model.advance(pins)
        after = model.outputs(pins)
        vectors.append((pack_fields(CSR_INPUTS, pins),
                        pack_fields(CSR_OUTPUTS, before),
                        pack_fields(CSR_OUTPUTS, after)))
        return before

    def access(address, write=0, data=0, strobe=15, busy=0, mode=0):
        context = {"busy": busy, "think_active": mode}
        before = edge(csr_valid=1, csr_write=write, csr_addr=address,
                      csr_wdata=data, csr_wstrb=strobe, **context)
        if before.get("csr_ready") != 1:
            raise AssertionError("CSR fixture issued without readiness")
        requests.append({"address": address, "write": write, "data": data,
                         "strobe": strobe, **context})
        edge(csr_rsp_ready=0, **context)
        for _ in range(3):
            edge(csr_rsp_ready=0, **context)
        edge(**context)
        edge(**context)

    edge(rst_n=0)
    for _ in range(12):
        edge(busy=1, think_active=rng.randrange(2))
    access(8, 1, 2)
    addresses = sorted({0, 4, 8, 12, 0x048, 0x04C, 0x080,
                        *model.reference, *COUNTER_OFFSETS,
                        *(a + 4 for a in COUNTER_OFFSETS)})
    for address in addresses:
        access(address)
    for address in model.reference:
        access(address, 1, 1 if address == 0x084 else 2 if address == 0x098 else 0x89ABCDEF)
        access(address)
    access(8, 1, 1)
    access(8)
    access(8, 1, 7)  # snapshot captures pre-clear, while clear outranks events
    for address in addresses:
        access(address)
    access(8, 1, 3, busy=1, mode=1)
    access(8, 1, 5, busy=1, mode=1)
    access(8, 1, 2, busy=1, mode=1)
    access(8, 1, 1, busy=1, mode=1)
    access(8, 1, 8)
    access(8, 1, 1, strobe=7)
    access(9, 1, 0)
    access(1)
    access(0x0A0)
    for address in addresses:
        if address not in (8, *model.reference):
            access(address, 1, 0)
    for address in model.reference:
        access(address, 1, 1, busy=1)
    access(0x084, 1, 2)
    access(0x098, 1, 0)
    access(0x098, 1, 4)
    access(8, 1, 2)
    for address in addresses:
        access(address, strobe=0)  # read strobes are ignored
    edge(csr_valid=1, csr_write=0, csr_addr=4)
    edge(csr_rsp_ready=0)
    edge(rst_n=0, csr_rsp_ready=0)  # reset an owned, stalled response
    access(0)
    access(8)
    access(0x080)
    if not all(totals.values()) or set(addresses) - {
            r["address"] for r in requests if not r["write"]}:
        raise AssertionError("CSR directed coverage missing")
    return vectors, totals, requests


def run_csr(run, simulator="icarus"):
    vectors, totals, requests = csr_vectors()
    vector_file = run.path / f"csr-{simulator}-vectors.txt"
    with vector_file.open("x") as output:
        for row in vectors:
            output.write(" ".join(f"{value:x}" for value in row) + "\n")
    bench = run.path / f"csr-{simulator}_tb.sv"
    bench.write_text(vector_bench("anvil_qn1_csr_perf", CSR_INPUTS, CSR_OUTPUTS))
    sources = ["rtl/anvil_qn1_00_pkg.sv", "rtl/anvil_qn1_csr_perf.sv"]
    name = f"csr-{simulator}"
    if simulator == "icarus":
        binary = run.path / f"{name}.vvp"
        run.execute(["iverilog", "-g2012", "-Wall", "-s", "control_tb", "-o",
                     relative(binary), *sources, relative(bench)], f"{name}-compile")
        argv = ["vvp", relative(binary), f"+vectors={relative(vector_file)}"]
    else:
        objects = run.path / f"obj-{name}"
        run.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                     "--top-module", "control_tb", "--Mdir", relative(objects),
                     "-o", "simulate", *sources, relative(bench)], f"{name}-compile")
        argv = [relative(objects / "simulate"), f"+vectors={relative(vector_file)}"]
    text = run.execute(argv, f"{name}-simulation", timeout=600 if simulator == "icarus" else 2700)
    expected = f"SUMMARY edges={len(vectors)} " + " ".join(
        f"{key}={value}" for key, value in totals.items())
    if text.count(expected) != 1:
        raise AssertionError(f"CSR coverage summary mismatch: expected {expected}")
    (run.path / f"{name}-requests.json").write_text(json.dumps(requests, indent=2) + "\n")
    return {"edges": len(vectors), **totals, "simulator": simulator,
            "read_offsets": sorted({r["address"] for r in requests if not r["write"]}),
            "snapshot_clear": True, "reset_stalled_response": True}


def controller_scenarios():
    scenarios = []

    def add(name, nodes, parents, predictions, mode=1, pos=0, fault=0, cancel=0):
        requests, generated = [(4, pos, predictions[4])], []
        accepted = 0
        if not fault:
            parent = 4
            while True:
                target = predictions[parent]
                generated.append(target)
                matches = [i for i, (t, p) in enumerate(zip(nodes, parents))
                           if t == target and p == parent] if mode else []
                if matches:
                    accepted += 1
                if not matches or target in (151667, 151668) or pos + len(generated) == 15:
                    break
                parent = matches[0]
                requests.append((parent, pos + len(generated), predictions[parent]))
        scenarios.append({"name": name, "mode": mode, "position": pos,
                          "nodes": nodes, "parents": parents, "fault": fault,
                          "cancel": cancel, "requests": requests,
                          "generated": generated, "accepted": accepted})

    for length in range(5):
        nodes = [10, 11, 12, 13]
        predictions = {4: 10, 0: 11, 1: 12, 2: 13, 3: 14}
        predictions[4 if length == 0 else length - 1] = 30
        add(f"prefix-{length}", nodes, [4, 0, 1, 2], predictions)
        add(f"prefix-{length}-second", [50], [4], {4: 40}, pos=length + 1)
    add("branch", [99, 10, 11, 77], [4, 4, 1, 0], {4: 10, 1: 11, 2: 12})
    add("branch-second", [50], [4], {4: 40}, pos=3)
    add("open-marker", [151667], [4], {4: 151667})
    add("open-marker-second", [50], [4], {4: 40}, pos=1)
    add("close-marker", [151668], [4], {4: 151668})
    add("direct", [], [], {4: 20}, mode=0)
    add("direct-second", [], [], {4: 21}, mode=0, pos=1)
    add("capacity", [10, 11], [4, 0], {4: 10, 0: 11, 1: 12}, pos=13)
    add("terminal-start", [], [], {4: 10}, mode=0, pos=15, fault=2)
    for name, nodes, parents, pos in (
            ("count-zero", [], [], 0),
            ("count-five", [1, 2, 3, 4, 5], [4, 0, 1, 2, 3], 0),
            ("token-range", [151936], [4], 0),
            ("self-parent", [10], [0], 0),
            ("forward-parent", [10, 11], [1, 4], 0),
            ("parent-range", [10], [5], 0),
            ("duplicate-sibling", [10, 10], [4, 4], 0),
            ("path-capacity", [10, 11], [4, 0], 14)):
        add(name, nodes, parents, {4: 10}, pos=pos, fault=1)
    for stage in (1, 2, 3, 4):
        add(f"cancel-stage-{stage}", [10, 11], [4, 0],
            {4: 10, 0: 11, 1: 12}, cancel=stage)
    names = {s["name"] for s in scenarios}
    if not all(f"prefix-{n}" in names and f"prefix-{n}-second" in names for n in range(5)):
        raise AssertionError("controller prefix/continuation fixtures missing")
    return scenarios


CONTROLLER_DRIVER = r"""
#include "Vanvil_qn1_dual_think_ctrl.h"
#include "verilated.h"
#include <array>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
struct Request {unsigned parent,pos,argmax;};
struct Case {
    unsigned mode,pos,count,fault,cancel,accepted;
    std::array<unsigned,4> nodes,parents;
    std::vector<Request> requests;
    std::vector<unsigned> generated;
};
void require(bool condition,const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}
int main(int argc,char**argv) {
  try {
    Verilated::commandArgs(argc,argv);
    require(argc==2,"scenario filename");
    std::ifstream input(argv[1]);require(bool(input),"open scenarios");
    Vanvil_qn1_dual_think_ctrl dut;
    unsigned cases=0,commits=0,requests_total=0,faults=0,cancels=0;
    auto edge=[&]() {dut.clk=0;dut.eval();dut.clk=1;dut.eval();};
    auto defaults=[&]() {
      dut.start_valid=0;dut.mode_valid=0;dut.observed_valid=0;dut.observed_token=0;
      dut.draft_valid=0;dut.verify_ready=0;dut.verify_rsp_valid=0;dut.verify_error=0;
      dut.commit_ready=0;dut.publish_ready=0;dut.flush=0;dut.cancel=0;
    };
    std::string name;
    while (input>>name) {
      Case c;unsigned nr,ng;
      input>>c.mode>>c.pos>>c.count>>c.fault>>c.cancel>>c.accepted;
      for(auto&v:c.nodes) input>>v;
      for(auto&v:c.parents) input>>v;
      input>>nr;
      for(unsigned i=0;i<nr;++i) {
        Request r;input>>r.parent>>r.pos>>r.argmax;c.requests.push_back(r);
      }
      input>>ng;
      for(unsigned i=0;i<ng;++i) {unsigned t;input>>t;c.generated.push_back(t);}
      require(bool(input),"malformed scenario");
      defaults();dut.clk=0;dut.rst_n=0;dut.eval();
      require(!(dut.start_ready||dut.busy||dut.done||dut.error||dut.think_active||
        dut.draft_ready||dut.commit_valid||dut.commit_count||dut.commit_pos||
        dut.verify_valid||dut.verify_rsp_ready||dut.event_draft_nodes||
        dut.event_verified_nodes||dut.event_accepted_nodes||dut.event_rejected_nodes),
        name+" reset status");
      for(auto v:dut.commit_tokens) require(v==0,name+" reset payload");
      edge();dut.clk=0;dut.rst_n=1;dut.eval();
      dut.mode_valid=1;dut.mode_value=c.mode;edge();dut.mode_valid=0;
      require(dut.think_active==c.mode,name+" idle mode write");
      for(unsigned i=0;i<4;++i) dut.draft_tokens[i]=c.nodes[i];
      dut.draft_parents=0;
      for(unsigned i=0;i<4;++i) dut.draft_parents|=c.parents[i]<<(3*i);
      dut.draft_count=c.count;dut.draft_valid=1;
      dut.clk=0;dut.eval();
      require(!dut.draft_ready,name+" idle draft must not transfer");
      edge();
      dut.start_valid=1;dut.start_pos=c.pos;
      bool started=false,drafted=false,pending=false,published=false,finished=false;
      unsigned request_index=0,response_index=0,pending_cycle=0,pending_argmax=0;
      unsigned commit_stalls=0,last_commit=0,last_response=0;
      unsigned draft_events=0,verified_events=0,accepted_events=0,rejected_events=0;
      unsigned mode=c.mode;
      for(unsigned cycle=0;cycle<1000 && !finished;++cycle) {
        dut.clk=0;
        dut.start_valid=!started;dut.draft_valid=!drafted;
        dut.verify_ready=cycle%5>=2;
        dut.verify_rsp_valid=pending && cycle>=pending_cycle+3;
        dut.verify_argmax=pending_argmax;
        dut.publish_ready=response_index==c.requests.size() && cycle>last_response+4;
        dut.commit_ready=commit_stalls>=5;
        dut.cancel=(c.cancel==1 && pending && response_index==0) ||
                   (c.cancel==2 && response_index==1 && cycle==last_response+1) ||
                   (c.cancel==3 && commit_stalls==2) ||
                   (c.cancel==4 && published && cycle==last_commit+1);
        dut.eval();
        require(dut.think_active==mode,name+" mode changed without publication");
        if (dut.cancel) {
          require(!(dut.commit_valid||dut.verify_valid||dut.draft_ready),
                  name+" cancel must immediately suppress new transfers");
          edge();
          require(!(dut.busy||dut.commit_valid||dut.verify_valid||dut.done||dut.error),
                  name+" cancel ownership");
          ++cancels;finished=true;break;
        }
        if (dut.error) {
          require(c.fault && !published && !dut.done,name+" unexpected error");
          if(c.fault==1) require(drafted && response_index==1,name+" malformed tree ordering");
          if(c.fault==2) require(!request_index,name+" terminal start issued backend");
          ++faults;finished=true;break;
        }
        if(dut.start_valid && dut.start_ready) {
          require(!started && !dut.draft_ready && !dut.commit_valid,name+" start ordering");
          started=true;
        }
        if(dut.draft_valid && dut.draft_ready) {
          require(started && response_index==1 && !drafted && mode,
                  name+" token-first/draft-second ordering");
          drafted=true;
        }
        if(dut.verify_valid && dut.verify_ready) {
          require(request_index<c.requests.size() && !pending,
                  name+" unsolicited/extra backend request");
          const auto&r=c.requests[request_index];
          require(dut.verify_parent==r.parent && dut.verify_pos==r.pos,
                  name+" backend parent/position comparison");
          if(request_index) require(drafted,name+" node request before draft transfer");
          pending=true;pending_cycle=cycle;pending_argmax=r.argmax;
          ++request_index;++requests_total;
        }
        if(dut.verify_rsp_valid && dut.verify_rsp_ready) {
          require(pending,name+" unowned backend response");
          pending=false;++response_index;last_response=cycle;
        }
        if(dut.commit_valid) {
          require(!c.fault && response_index==c.requests.size() && !pending,
                  name+" publication before verification settlement");
          require(dut.commit_count==c.generated.size() && dut.commit_pos==c.pos+1,
                  name+" commit count/position");
          for(unsigned i=0;i<5;++i)
            require(dut.commit_tokens[i]==(i<c.generated.size()?c.generated[i]:0),
                    name+" commit token/slice comparison");
          if(!dut.commit_ready) ++commit_stalls;
          else {
            require(!published,name+" duplicate stalled commit");
            published=true;last_commit=cycle;++commits;
            for(auto token:c.generated) {
              if(token==151667) mode=1;
              if(token==151668) mode=0;
            }
          }
        }
        if(dut.done) {
          require(published && cycle>last_commit && !dut.start_ready,
                  name+" done ordering");
          require(draft_events==(c.mode?c.count:0) &&
                  verified_events==c.requests.size()-1 &&
                  accepted_events==c.accepted &&
                  rejected_events==(c.mode?c.count-c.accepted:0),
                  name+" event conservation");
          finished=true;
        }
        edge();
        draft_events+=dut.event_draft_nodes;verified_events+=dut.event_verified_nodes;
        accepted_events+=dut.event_accepted_nodes;rejected_events+=dut.event_rejected_nodes;
        require(dut.think_active==mode,name+" post-publication mode");
        if(cycle==0) require(!dut.start_ready && !dut.commit_valid && !dut.done,
                            name+" accepted start cannot complete immediately");
      }
      require(finished,name+" missing required response/commit/error/cancel");++cases;
    }
    require(input.eof() && cases && commits && faults && cancels,"controller coverage");
    // Unsolicited backend response must never be treated as work.
    defaults();dut.rst_n=0;edge();dut.rst_n=1;dut.verify_rsp_valid=1;
    dut.verify_argmax=10;dut.clk=0;dut.eval();
    require(!dut.verify_rsp_ready,"unsolicited response readiness");
    edge();require(dut.error && !dut.commit_valid,"unsolicited response fault");
    // Committed close wins over idle configuration; cancel wins over marker.
    defaults();dut.rst_n=0;edge();dut.rst_n=1;
    dut.mode_valid=1;dut.mode_value=1;dut.observed_valid=1;dut.observed_token=151668;
    edge();require(!dut.think_active,"close marker priority");
    dut.observed_token=151667;dut.cancel=1;edge();
    require(!dut.think_active,"cancel marker priority");
    dut.cancel=0;edge();require(dut.think_active,"committed opening marker");
    dut.observed_valid=0;dut.mode_valid=0;dut.final();
    std::cout<<"SUMMARY controller_cases="<<cases<<" commits="<<commits
      <<" requests="<<requests_total<<" faults="<<faults<<" cancels="<<cancels<<"\n";
    return 0;
  } catch(const std::exception& e) {std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}
}
"""


def run_controller(run):
    cases = controller_scenarios()
    vector_file = run.path / "controller-scenarios.txt"
    with vector_file.open("x") as file:
        for case in cases:
            fields = [case["name"], case["mode"], case["position"], len(case["nodes"]),
                      case["fault"], case["cancel"], case["accepted"],
                      *(case["nodes"] + [0] * 4)[:4],
                      *(case["parents"] + [0] * 4)[:4], len(case["requests"])]
            fields.extend(v for request in case["requests"] for v in request)
            fields.extend([len(case["generated"]), *case["generated"]])
            file.write(" ".join(map(str, fields)) + "\n")
    driver = run.path / "controller_driver.cpp"
    driver.write_text(CONTROLLER_DRIVER)
    objects = run.path / "obj-controller"
    run.execute(["verilator", "--cc", "--exe", "--build", "-Wno-fatal", "-j", "2",
                 "--top-module", "anvil_qn1_dual_think_ctrl", "--Mdir", relative(objects),
                 "-o", "simulate", "rtl/anvil_qn1_dual_think_ctrl.sv",
                 "../controller_driver.cpp"], "controller-compile")
    text = run.execute([relative(objects / "simulate"), relative(vector_file)],
                       "controller-simulation")
    expected_commits = sum(not c["fault"] and c["cancel"] in (0, 4) for c in cases)
    expected_faults = sum(bool(c["fault"]) for c in cases)
    if (text.count(f"SUMMARY controller_cases={len(cases)} commits={expected_commits}") != 1 or
            f"faults={expected_faults} cancels=4" not in text):
        raise AssertionError("controller scenario coverage summary")
    (run.path / "controller-cases.json").write_text(json.dumps(cases, indent=2) + "\n")
    return {"cases": len(cases), "commits": expected_commits, "faults": expected_faults,
            "cancel_stages": [1, 2, 3, 4], "prefix_lengths": list(range(5)),
            "coverage_names": [c["name"] for c in cases], "raw_summary": text.strip()}
