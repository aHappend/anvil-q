"""Nonzero reduced multi-token public-pin regression against a rational decoder.

Each probe retains its manifest before simulation. This is not the complete
admitted L1 matrix, scheduler fault campaign or native hardware benchmark.
"""

import argparse
from collections import Counter, deque
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run, require_time_zero, with_time_zero_check
from simulation import compile_model, startup_check, stream_model
from benchmark_checks import StageIntervals
from transformer_reference import Geometry, Transformer, coordinates


BENCH = r"""
module tb;
  parameter BANKS=4,FORMAT=0,WEIGHTS=0,CACHE=0,ENTRIES=1;
  parameter LAYERS=2,HIDDEN=48,INTERMEDIATE=48,QHEADS=6,KVHEADS=1,DIM=8;
  parameter GROUP=12,VOCAB=3,POSITIONS=3,BLOCK=2,DEPTH=3;
  reg clk=0,rst_n,token_valid=0;
  integer SEED=17;
  reg [4095:0] memory_file;
  always #5 clk=~clk;
  reg [31:0] token_id=0,token_pos=0;
  reg new_sequence=0,token_phase=0,logit_ready=0;
  wire token_ready,logit_valid,done,error,cancel_done;
  wire [31:0] logit_index,logit_data;
  wire [BANKS-1:0] req_valid,req_write,rsp_ready;
  reg [BANKS-1:0] req_ready=0,rsp_valid=0;
  wire [BANKS*4-1:0] req_kind;
  wire [BANKS*3-1:0] req_proj;
  wire [BANKS*32-1:0] req_layer,req_row,req_col,req_data;
  wire [BANKS*64-1:0] req_tag;
  reg [BANKS*32-1:0] rsp_data=0;
  reg [BANKS*64-1:0] rsp_tag=0;
  reg [134:0] initial_memory[0:ENTRIES-1];
  reg [102:0] address[0:ENTRIES-1];
  reg [31:0] contents[0:ENTRIES-1];
  reg initialized[0:ENTRIES-1];
  reg busy[0:BANKS-1];
  reg [31:0] pending_data[0:BANKS-1];
  reg [63:0] pending_tag[0:BANKS-1];
  integer response_due[0:BANKS-1];
  reg held_req[0:BANKS-1];
  reg [199:0] previous_req[0:BANKS-1];
  reg held_logit=0;
  reg [63:0] previous_logit=0;
  reg [102:0] location;
  integer i,b,p,found,cycles=0,accepted=0,retired=0,completions=0,requests=0,responses=0;
  integer bank_requests[0:BANKS-1],bank_stalls[0:BANKS-1],logit_stalls=0,logit_wait=0;
  function automatic integer find_address(input [102:0] wanted);
    integer low,high,mid;
    begin
      low=0; high=ENTRIES-1; find_address=-1;
      while(low<=high) begin
        mid=(low+high)>>1;
        if(address[mid]==wanted) begin find_address=mid; low=high+1; end
        else if(address[mid]<wanted) low=mid+1;
        else high=mid-1;
      end
    end
  endfunction
  anvil_q2_fp_top #(
    .NUM_LAYERS(LAYERS),.HIDDEN_SIZE(HIDDEN),.INTERMEDIATE_SIZE(INTERMEDIATE),
    .NUM_Q_HEADS(QHEADS),.NUM_KV_HEADS(KVHEADS),.HEAD_DIM(DIM),.GROUP_SIZE(GROUP),
    .VOCAB_SIZE(VOCAB),.MAX_SEQ_LEN(POSITIONS),.BANKS(BANKS),.CACHE_BLOCK(BLOCK),
    .QUEUE_DEPTH(DEPTH),.CACHE_MODE(CACHE),.FP_FORMAT(FORMAT),.WEIGHT_MODE(WEIGHTS)
  ) dut(
    .clk(clk),.rst_n(rst_n),.cancel(1'b0),
    .token_valid(token_valid),.token_ready(token_ready),
    .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),
    .token_phase(token_phase),.logit_valid(logit_valid),.logit_ready(logit_ready),
    .logit_index(logit_index),.logit_data(logit_data),
    .done(done),.error(error),.cancel_done(cancel_done),
    .mem_req_valid(req_valid),.mem_req_ready(req_ready),.mem_req_write(req_write),
    .mem_req_kind(req_kind),.mem_req_layer(req_layer),.mem_req_proj(req_proj),
    .mem_req_row(req_row),.mem_req_col(req_col),.mem_req_wdata(req_data),
    .mem_req_tag(req_tag),.mem_rsp_valid(rsp_valid),.mem_rsp_error({BANKS{1'b0}}),
    .mem_rsp_ready(rsp_ready),.mem_rsp_rdata(rsp_data),.mem_rsp_tag(rsp_tag));
  initial begin
    rst_n=0;
    if(!$value$plusargs("SEED=%d",SEED)) $fatal(1,"MISSING_SEED");
    if(!$value$plusargs("MEMORY=%s",memory_file)) $fatal(1,"MISSING_MEMORY");
    $readmemh(memory_file,initial_memory);
    for(i=0;i<ENTRIES;i=i+1) begin
      address[i]=initial_memory[i][134:32];
      contents[i]=initial_memory[i][31:0];
      initialized[i]=address[i][102:99]!=8 && address[i][102:99]<9 ||
                     address[i][102:99]==11;
    end
    for(i=0;i<BANKS;i=i+1) begin
      busy[i]=0; pending_data[i]=0; pending_tag[i]=0; response_due[i]=0;
      held_req[i]=0; previous_req[i]=0; bank_requests[i]=0; bank_stalls[i]=0;
    end
    #1;
    if({token_ready,logit_valid,logit_index,logit_data,done,error,cancel_done,
        req_valid,req_write,req_kind,req_layer,req_proj,req_row,req_col,
        req_data,req_tag,rsp_ready} !== 0) $fatal(1,"RESET_NONZERO_X");
    repeat(2) @(negedge clk);
    rst_n=1;
    for(p=0;p<POSITIONS;p=p+1) begin
      @(negedge clk);
      token_pos=p; token_id=p%VOCAB; new_sequence=p==0;
      token_phase=p==POSITIONS-1 && p!=0;
      token_valid=1;
      do @(posedge clk); while(!token_ready);
      @(negedge clk); token_valid=0;
      do @(posedge clk); while(!done);
      @(negedge clk);
    end
    @(negedge clk);
    if(accepted!=POSITIONS || completions!=POSITIONS ||
       retired!=POSITIONS*VOCAB || requests!=responses)
      $fatal(1,"TOKEN_ACCOUNTING");
    for(i=0;i<BANKS;i=i+1) begin
      if(busy[i] || rsp_valid[i]) $fatal(1,"UNDRAINED_RESPONSE");
      $display("BANK %0d %0d %0d",i,bank_requests[i],bank_stalls[i]);
    end
    $display("TOKEN_COMPARED %0d %0d %0d %0d %0d %0d",
             accepted,completions,retired,requests,responses,logit_stalls);
    $finish;
  end
  always @(negedge clk) begin
    if(rst_n) begin
      if(!logit_valid) begin logit_ready=0; logit_wait=0; end
      else if(logit_wait<3) begin logit_ready=0; logit_wait=logit_wait+1; end
      else logit_ready=((cycles+SEED)%13)>3;
      for(integer k=0;k<BANKS;k=k+1) begin
        req_ready[k]=!busy[k] && ((cycles+SEED+3*k)%9)>1;
        if(busy[k] && !rsp_valid[k] && cycles>=response_due[k]) begin
          rsp_valid[k]=1;
          rsp_tag[k*64+:64]=pending_tag[k];
          rsp_data[k*32+:32]=pending_data[k];
        end
      end
    end
  end
  always @(posedge clk or negedge clk)
    if(!rst_n && $time>0 &&
       {token_ready,logit_valid,logit_index,logit_data,done,error,cancel_done,
        req_valid,req_write,req_kind,req_layer,req_proj,req_row,req_col,
        req_data,req_tag,rsp_ready} !== 0) $fatal(1,"RESET_EDGE_NONZERO_X");
  always @(posedge clk) begin
    cycles<=cycles+1;
    if(rst_n) begin
      if((^{token_ready,logit_valid,done,error,cancel_done,req_valid,rsp_ready}) === 1'bx)
        $fatal(1,"ACTIVE_CONTROL_X");
      if(token_valid && token_ready) begin
        accepted<=accepted+1;
        $display("COMMAND %0d %0d %0d %0d",cycles,token_pos,token_id,token_phase);
      end
      if(held_logit && (logit_valid !== 1'b1 ||
                       {logit_index,logit_data} !== previous_logit))
        $fatal(1,"LOGIT_STALL_INSTABILITY");
      held_logit<=logit_valid && !logit_ready;
      previous_logit<={logit_index,logit_data};
      if(logit_valid && !logit_ready) logit_stalls<=logit_stalls+1;
      if(logit_valid && logit_ready) begin
        if((^{logit_index,logit_data}) === 1'bx) $fatal(1,"LOGIT_X");
        $display("LOGIT %0d %0d %0d %08h",cycles,token_pos,logit_index,logit_data);
        retired<=retired+1;
      end
      for(b=0;b<BANKS;b=b+1) begin
        if(held_req[b] && (req_valid[b] !== 1'b1 ||
           {req_write[b],req_kind[b*4+:4],req_layer[b*32+:32],req_proj[b*3+:3],
            req_row[b*32+:32],req_col[b*32+:32],req_data[b*32+:32],req_tag[b*64+:64]}
             !== previous_req[b])) $fatal(1,"HELD_REQUEST_INSTABILITY");
        held_req[b]<=req_valid[b] && !req_ready[b];
        previous_req[b]<={req_write[b],req_kind[b*4+:4],req_layer[b*32+:32],
          req_proj[b*3+:3],req_row[b*32+:32],req_col[b*32+:32],req_data[b*32+:32],
          req_tag[b*64+:64]};
        if(req_valid[b] && !req_ready[b]) bank_stalls[b]=bank_stalls[b]+1;
        if(rsp_valid[b] && rsp_ready[b]) begin
          // Pipe records are independently consumed live, not retained as a dump.
          $fdisplay(32'h80000001,"RSP %0d %0d %016h %08h",cycles,b,rsp_tag[b*64+:64],rsp_data[b*32+:32]);
          rsp_valid[b]<=0; busy[b]=0; responses=responses+1;
        end
        if(req_valid[b] && req_ready[b]) begin
          if((^{req_write[b],req_kind[b*4+:4],req_layer[b*32+:32],req_proj[b*3+:3],
                req_row[b*32+:32],req_col[b*32+:32],req_data[b*32+:32],
                req_tag[b*64+:64]}) === 1'bx) $fatal(1,"ACTIVE_REQUEST_X");
          location={req_kind[b*4+:4],req_layer[b*32+:32],req_proj[b*3+:3],
                    req_row[b*32+:32],req_col[b*32+:32]};
          found=find_address(location);
          if(found<0) $fatal(1,"UNDECLARED_MEMORY_ADDRESS %026h",location);
          if(req_write[b]) begin
            if(location[102:99]!=8 && location[102:99]<9 || location[102:99]==11)
              $fatal(1,"MODEL_TENSOR_WRITE");
            contents[found]=req_data[b*32+:32]; initialized[found]=1;
          end else if(!initialized[found]) $fatal(1,"UNINITIALIZED_MEMORY_READ %026h",location);
          $fdisplay(32'h80000001,"REQ %0d %0d %0d %026h %08h %016h",
            cycles,b,req_write[b],location,req_data[b*32+:32],req_tag[b*64+:64]);
          pending_data[b]=req_write[b] ? 0 : contents[found];
          pending_tag[b]=req_tag[b*64+:64]; busy[b]=1;
          response_due[b]=cycles+2+((req_tag[b*64+:64]+b*3)%7);
          requests=requests+1; bank_requests[b]=bank_requests[b]+1;
        end
      end
      if(done) begin
        if(error !== 1'b0 || requests!=responses) $fatal(1,"TOKEN_FAILED_OR_UNDRAINED");
        $display("DONE %0d %0d",cycles,token_pos);
        completions<=completions+1;
      end
    end
  end
endmodule
"""


def compare(trace, reference, banks, depth=3):
    with trace.open() as lines:
        return compare_lines(lines, reference, banks, depth)


def compare_lines(lines, reference, banks, depth=3):
    intervals = StageIntervals(reference.stages)
    expected_writes = {address: deque(values) for address, values in reference.writes.items()}
    memory = dict(reference.loads)
    pending, seen = {}, set()
    expected_logits = deque(reference.logits)
    commands, completions, summaries = [], [], []
    logit_cycles = {}
    compared_writes = compared_reads = response_count = 0
    kind_counts, bank_counts = Counter(), Counter()
    bank_metrics = {}
    peak_outstanding = 0
    occupied_cycles = Counter()
    for line in lines:
        intervals.observe(line)
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "COMMAND":
            _, cycle, position, token, phase = parts
            commands.append((int(cycle), int(position), int(token), int(phase)))
        elif parts[0] == "REQ":
            _, cycle, bank, write, address, data, tag = parts
            bank, write, address, data, tag = (
                int(bank), int(write), int(address, 16), int(data, 16), int(tag, 16))
            assert tag not in seen, f"duplicate memory tag {tag:016x}"
            seen.add(tag)
            assert sum(coordinates(address)) & (banks - 1) == bank, "wrong memory bank"
            kind_counts[coordinates(address)[0]] += 1
            bank_counts[bank] += 1
            if write:
                assert address in expected_writes and expected_writes[address], (
                    f"uncommanded write at {coordinates(address)}")
                expected = expected_writes[address].popleft()
                assert data == expected, (
                    f"TOKEN_MEMORY_MISMATCH address={coordinates(address)} "
                    f"observed={data:08x} expected={expected:08x}")
                memory[address] = data
                pending[tag] = (bank, 0, int(cycle))
                compared_writes += 1
            else:
                assert address in memory, f"uninitialized/illegal read {coordinates(address)}"
                pending[tag] = (bank, memory[address], int(cycle))
                compared_reads += 1
            peak_outstanding = max(peak_outstanding, len(pending))
        elif parts[0] == "RSP":
            _, cycle, bank, tag, data = parts
            tag, data = int(tag, 16), int(data, 16)
            assert tag in pending, f"unassociated/duplicate response {tag:016x}"
            expected_bank, expected_data, issued_cycle = pending.pop(tag)
            assert (expected_bank, expected_data) == (int(bank), data), (
                "response numerical/tag/bank mismatch")
            assert int(cycle) > issued_cycle, "unaccepted/zero-cycle memory response"
            occupied_cycles[int(bank)] += int(cycle) - issued_cycle
            response_count += 1
        elif parts[0] == "LOGIT":
            _, cycle, position, row, bits = parts
            assert expected_logits, "extra logit"
            expected = expected_logits.popleft()
            assert (int(position), int(row), int(bits, 16)) == expected, (
                f"TOKEN_LOGIT_MISMATCH observed={parts[2:]} expected={expected}")
            logit_cycles[int(position)] = int(cycle)
        elif parts[0] == "DONE":
            completions.append((int(parts[1]), int(parts[2])))
        elif parts[0] == "BANK":
            bank, requests, stalls = map(int, parts[1:])
            assert bank not in bank_metrics, "duplicate bank summary"
            bank_metrics[bank] = {"accepted_requests": requests, "memory_stall_cycles": stalls}
        elif parts[0] == "TOKEN_COMPARED":
            summaries.append(list(map(int, parts[1:])))
    g = reference.g
    assert len(commands) == len(completions) == g.positions, "token count mismatch"
    assert [c[1] for c in commands] == list(range(g.positions)), "position mismatch"
    assert not pending and not expected_logits, "unconsumed response or logit"
    missing = {coordinates(k): len(v) for k, v in expected_writes.items() if v}
    assert not missing, f"missing reference writes: {missing}"
    assert compared_writes > 0 and compared_reads > 0 and response_count == len(seen)
    assert len(summaries) == 1 and summaries[0][0:3] == [
        g.positions, g.positions, g.positions * g.vocabulary], "summary absent/mismatched"
    assert summaries[0][5] > 0, "no observed logit backpressure"
    assert len(bank_counts) == banks, "bank activity coverage absent"
    assert set(bank_metrics) == set(range(banks)), "missing bank metrics"
    assert all(bank_metrics[b]["accepted_requests"] == bank_counts[b] for b in range(banks))
    if banks > 1 and depth > 1:
        assert peak_outstanding > 1, "parallel banks serialized to one outstanding transaction"
    return {
        "shape_class": "reduced", "memory_reads_compared": compared_reads,
        "memory_writes_compared": compared_writes, "responses_compared": response_count,
        "logits_compared": len(reference.logits), "commands": len(commands),
        "token_cycles": [end[0] - begin[0] for begin, end in zip(commands, completions)],
        "accepted_command_to_final_accepted_logit_cycles": [
            logit_cycles[begin[1]] - begin[0] for begin in commands],
        "transactions_by_kind": dict(kind_counts), "transactions_by_bank": dict(bank_counts),
        "bank_metrics": bank_metrics,
        "peak_outstanding_memory_transactions": peak_outstanding,
        "external_bank_occupied_cycles": dict(occupied_cycles),
        "logit_stall_cycles": summaries[0][5],
        "stage_final_ack_interval_cycles": intervals.finish(),
        "limitations": "No scheduler fault/cancel coverage or native full-token performance claim.",
    }


def execute(fmt, weight_mode, cache_mode, banks, seed, geometry=None, depth=3, product="fp",
            expanded_packages=False, simulator="verilator"):
    run = Run(f"verifier-token-{product}-{fmt}-w{weight_mode}-c{cache_mode}-b{banks}-s{seed}")
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        if product == "parent":
            from parent_reference import ParentTransformer
            assert weight_mode == 1, "parent native-weight baseline is not applicable"
            reference = ParentTransformer(cache_mode, seed, geometry)
        else:
            reference = Transformer(fmt, weight_mode, cache_mode, seed, geometry)
        manifest = run.path / "manifest.json"
        definition = reference.manifest()
        definition["frontend"] = "lossless package expansion" if expanded_packages else "original SV"
        manifest.write_text(json.dumps(definition, indent=2) + "\n")
        reference.execute()
        expected = run.path / "reference.json"
        expected.write_text(json.dumps({
            "writes": {f"{k:026x}": [f"{v:08x}" for v in values]
                       for k, values in reference.writes.items()},
            "logits": reference.logits, "stages": reference.stages,
        }, indent=2) + "\n")
        addresses = sorted(set(reference.loads) | set(reference.writes))
        memory = run.path / "memory.hex"
        memory.write_text("".join(
            f"{(address << 32) | reference.loads.get(address, 0):034x}\n" for address in addresses))
        bench = run.path / "bench.sv"
        text = BENCH
        if product == "parent":
            text = text.replace("anvil_q2_fp_top #(", "anvil_q2_top #(").replace(
                ",.FP_FORMAT(FORMAT),.WEIGHT_MODE(WEIGHTS)", "")
        bench.write_text(with_time_zero_check(text))
        run.receipt["generated_sha256"] = {
            run.relative(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (manifest, expected, memory, bench)}
        g = reference.g
        parameters = dict(BANKS=banks, FORMAT=int(fmt == "fp16"), WEIGHTS=weight_mode,
                          CACHE=cache_mode, ENTRIES=len(addresses), LAYERS=g.layers,
                          HIDDEN=g.hidden, INTERMEDIATE=g.intermediate, QHEADS=g.q_heads,
                          KVHEADS=g.kv_heads, DIM=g.head_dim, GROUP=g.group,
                          VOCAB=g.vocabulary, POSITIONS=g.positions, BLOCK=g.block, DEPTH=depth)
        binary = run.path / "bench.vvp"
        sources = sorted((ROOT / ("rtl" if product == "fp" else "anvil_q2_reference/rtl")).glob("*.sv"))
        if expanded_packages:
            from synthesis_checks import expand_packages
            expanded = run.path / "expanded.sv"
            expanded.write_text(expand_packages(sources))
            run.receipt["generated_sha256"][run.relative(expanded)] = hashlib.sha256(
                expanded.read_bytes()).hexdigest()
            sources = [expanded]
        arguments = [f"+SEED={seed}", f"+MEMORY={run.relative(memory)}"]
        if simulator == "verilator":
            binary = compile_model(run, bench, sources, parameters)
            startup_check(run, binary, arguments)
            command = [run.relative(binary), *arguments]
        else:
            run.command(["iverilog", "-g2012", "-Wall", "-s", "tb",
                         *[f"-Ptb.{k}={v}" for k, v in parameters.items()],
                         "-o", run.relative(binary), *[run.relative(p) for p in sources],
                         run.relative(bench)], "compile")
            command = ["vvp", run.relative(binary), *arguments]
        metrics = stream_model(
            run, command, lambda lines: compare_lines(lines, reference, banks, depth),
            ("REQ ", "RSP "),
            ("COMMAND ", "REQ ", "RSP ", "LOGIT ", "DONE ", "TOKEN_COMPARED ", "BANK "))
        if simulator != "verilator":
            require_time_zero(run.path / "simulation.stdout.txt")
        metrics.update(product=product, format=reference.fmt, weight_mode=reference.weight_mode,
                       cache_mode=cache_mode, banks=banks, seed=seed,
                       frontend=definition["frontend"], simulator=simulator)
        run.finish("passed-focused-only", metrics=metrics)
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("bf16", "fp16"), default="bf16")
    parser.add_argument("--product", choices=("fp", "parent"), default="fp")
    parser.add_argument("--weights", type=int, choices=(0, 1), default=0)
    parser.add_argument("--cache", type=int, choices=(0, 1), default=0)
    parser.add_argument("--banks", type=int, choices=(1, 2, 4), default=4)
    parser.add_argument("--seed", type=int, choices=(17, 43, 89), default=17)
    parser.add_argument("--depth", type=int, choices=(1, 3, 16), default=3)
    parser.add_argument("--singleton", action="store_true",
                        help="one layer, token and vocabulary row; GROUP_SIZE=3, CACHE_BLOCK=1")
    parser.add_argument("--expanded-packages", action="store_true",
                        help="independently check the lossless Yosys frontend on real token behavior")
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="verilator",
                        help="compiled sweeps; Icarus is reserved for compact diagnostic comparisons")
    args = parser.parse_args()
    geometry = Geometry(layers=1, positions=1, vocabulary=1, group=3, block=1) if args.singleton else None
    return execute(args.format, args.weights, args.cache, args.banks, args.seed,
                   geometry=geometry, depth=args.depth, product=args.product,
                   expanded_packages=args.expanded_packages, simulator=args.simulator)


if __name__ == "__main__":
    raise SystemExit(main())
