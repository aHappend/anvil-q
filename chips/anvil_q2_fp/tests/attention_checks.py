"""Live causal attention drift with actual-output feedback across all layers.

The full workload uses 28 layers, 12/2 heads, D=128 and eight positions.
Sparse FP32 host projections/feedback use shared fixed weights 1/4 and 1/32;
each next layer is constructed from the preceding observed RTL output, not an
independently reset activation. This focused attention workload is not a
complete native decoder, full-vocabulary projection or native-token benchmark.
Reduced complete decoder/token tests and the native hardware gate are distinct.
"""

import argparse
from collections import defaultdict, deque
from dataclasses import asdict
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark_checks import error_metrics
from fp_reference import add, multiply, rounded, value
from retained import ROOT, Run, require_time_zero, with_time_zero_check
from simulation import compile_model, startup_check
from transformer_reference import Geometry, Transformer, coordinates, key


BENCH = r"""
module tb;
  parameter MODE=0,LAYERS=28,HIDDEN=1536,QHEADS=12,KVHEADS=2,DIM=128;
  parameter POSITIONS=8,BLOCK=16;
  localparam KVSIZE=KVHEADS*DIM,CACHE_STRIDE=KVSIZE;
  localparam CACHE_ENTRIES=7*LAYERS*POSITIONS*CACHE_STRIDE;
  reg clk=0,rst_n,cmd_valid=0;
  always #5 clk=~clk;
  reg [31:0] layer=0,pos=0;
  wire ready,done,error,mv,mw,mrr;
  reg mr=0,mrv=0;
  wire [3:0] mk;
  wire [2:0] mp;
  wire [31:0] ml,mrow,mcol,md;
  reg [31:0] mrd=0;
  reg [31:0] query[0:HIDDEN-1],keys[0:KVSIZE-1],values[0:KVSIZE-1];
  reg [31:0] cache[0:CACHE_ENTRIES-1];
  reg initialized[0:CACHE_ENTRIES-1];
  reg pending=0,held=0;
  reg [135:0] payload=0;
  integer command,i,scanned,index,due=0,cycle=0,requests=0,responses=0,writes=0;
  reg [31:0] response_data=0;
  anvil_q2_fp_gqa_attention #(
    .NUM_LAYERS(LAYERS),.HIDDEN_SIZE(HIDDEN),.NUM_Q_HEADS(QHEADS),
    .NUM_KV_HEADS(KVHEADS),.HEAD_DIM(DIM),.MAX_SEQ_LEN(POSITIONS),
    .CACHE_MODE(MODE),.CACHE_BLOCK(BLOCK),.EXPLICIT_PHASE(1),.FP_FORMAT(1)
  ) dut(clk,rst_n,cmd_valid,ready,layer,pos,done,error,mv,mr,mw,mk,ml,mp,
        mrow,mcol,md,mrv,mrr,mrd,1'b0,pos==POSITIONS-1 && pos!=0);
  initial begin
    rst_n=0;
    for(i=0;i<CACHE_ENTRIES;i=i+1) begin cache[i]=0; initialized[i]=0; end
    #1;
    if({ready,done,error,mv,mw,mk,ml,mp,mrow,mcol,md,mrr} !== 0)
      $fatal(1,"RESET_NONZERO_X");
    repeat(2) @(negedge clk); rst_n=1;
    for(command=0;command<LAYERS*POSITIONS;command=command+1) begin
      $display("FRAME_READY %0d",command); $fflush();
      scanned=$fscanf(32'h80000000,"%d %d",layer,pos);
      if(scanned!=2 || layer>=LAYERS || pos>=POSITIONS)
        $fatal(1,"MALFORMED_LIVE_COMMAND");
      for(i=0;i<HIDDEN;i=i+1) begin
        scanned=$fscanf(32'h80000000,"%h",query[i]);
        if(scanned!=1) $fatal(1,"MALFORMED_QUERY_VECTOR");
      end
      for(i=0;i<KVSIZE;i=i+1) begin
        scanned=$fscanf(32'h80000000,"%h",keys[i]);
        if(scanned!=1) $fatal(1,"MALFORMED_KEY_VECTOR");
      end
      for(i=0;i<KVSIZE;i=i+1) begin
        scanned=$fscanf(32'h80000000,"%h",values[i]);
        if(scanned!=1) $fatal(1,"MALFORMED_VALUE_VECTOR");
      end
      @(negedge clk); cmd_valid=1;
      do @(posedge clk); while(!ready);
      $display("ATTENTION_COMMAND %0d %0d %0d",cycle,layer,pos);
      @(negedge clk); cmd_valid=0;
      do @(posedge clk); while(!done);
      if(error || pending || mrv || requests!=responses ||
         writes!=(command+1)*(HIDDEN+(MODE==0 ? KVSIZE :
           2*(KVSIZE/BLOCK)*((BLOCK+3)/4+1))))
        $fatal(1,"ATTENTION_COMPLETION_ACCOUNTING");
      $display("FRAME_DONE %0d %0d %0d %0d %0d",command,cycle,requests,responses,writes);
      $fflush();
      @(negedge clk);
    end
    $display("ATTENTION_COMPARED %0d %0d %0d",LAYERS*POSITIONS,requests,responses);
    $fflush(); $finish;
  end
  always @(negedge clk) if(rst_n) begin
    mr=!pending && cycle%13>1;
    if(pending && !mrv && cycle>=due) begin mrv=1; mrd=response_data; end
  end
  always @(posedge clk or negedge clk)
    if(!rst_n && $time>0 && {ready,done,error,mv,mw,mk,ml,mp,mrow,mcol,md,mrr} !== 0)
      $fatal(1,"RESET_EDGE_NONZERO_X");
  always @(posedge clk) begin
    cycle<=cycle+1;
    if(rst_n) begin
      if((^{ready,done,error,mv,mrr}) === 1'bx) $fatal(1,"ATTENTION_CONTROL_X");
      if(held && (mv !== 1'b1 || {mw,mk,ml,mp,mrow,mcol,md} !== payload))
        $fatal(1,"ATTENTION_HELD_REQUEST_INSTABILITY");
      held<=mv && !mr; payload<={mw,mk,ml,mp,mrow,mcol,md};
      if(mrv && mrr) begin
        $display("MEM_RSP %0d %08h",cycle,mrd);
        mrv<=0; pending=0; responses=responses+1;
      end
      if(mv && mr) begin
        if((^{mw,mk,ml,mp,mrow,mcol,md}) === 1'bx) $fatal(1,"ATTENTION_REQUEST_X");
        if(mp!=0) $fatal(1,"ATTENTION_NONZERO_PROJECTION");
        response_data=0;
        if(mk==8) begin
          if(ml!=0) $fatal(1,"ATTENTION_SCRATCH_LAYER");
          if(mw) begin
            if(mrow!=5 || mcol>=HIDDEN) $fatal(1,"ATTENTION_OUTPUT_ADDRESS");
          end else case(mrow)
            2: begin
              if(mcol>=HIDDEN) $fatal(1,"ATTENTION_QUERY_ADDRESS");
              response_data=query[mcol];
            end
            3: begin
              if(mcol>=KVSIZE) $fatal(1,"ATTENTION_KEY_ADDRESS");
              response_data=keys[mcol];
            end
            4: begin
              if(mcol>=KVSIZE) $fatal(1,"ATTENTION_VALUE_ADDRESS");
              response_data=values[mcol];
            end
            default: $fatal(1,"ATTENTION_BAD_SCRATCH_SLOT");
          endcase
        end else begin
          if(mk<9 || mk>15 || mk==11 || ml>=LAYERS || mrow>pos || mcol>=CACHE_STRIDE)
            $fatal(1,"ATTENTION_CACHE_ADDRESS_OR_CAUSALITY");
          if((MODE==0 && mk>10) || (MODE==1 && mk<12)) $fatal(1,"ATTENTION_CACHE_MODE");
          index=((mk-9)*LAYERS*POSITIONS+ml*POSITIONS+mrow)*CACHE_STRIDE+mcol;
          if(mw) begin cache[index]=md; initialized[index]=1; end
          else begin
            if(!initialized[index]) $fatal(1,"ATTENTION_UNCOMMITTED_CACHE");
            response_data=cache[index];
          end
        end
        $display("MEM_REQ %0d %0d %0d %0d %0d %0d %08h",
                 cycle,mw,mk,ml,mrow,mcol,md);
        pending=1; due=cycle+2;
        requests=requests+1;
        if(mw) writes=writes+1;
      end
    end
  end
endmodule
"""


class AttentionReference(Transformer):
    def _tensors(self):
        self.weights, self.biases, self.norms = {}, {}, {}


def initial_residual(seed, position, hidden, adversarial):
    if adversarial:
        return [rounded(Fraction(64 if j % 128 == 0 else (-1)**j, 1 if j % 128 == 0 else 4096))
                for j in range(hidden)]
    return [rounded(Fraction((seed + position * 11 + j * 7) % 33 - 16, 31))
            for j in range(hidden)]


def projected_inputs(residual, geometry):
    quarter = rounded(Fraction(1, 4))
    query = [multiply(x, quarter) for x in residual]
    keys, values = [], []
    for head in range(geometry.kv_heads):
        source_head = head * (geometry.q_heads // geometry.kv_heads)
        for dim in range(geometry.head_dim):
            source = source_head * geometry.head_dim + dim
            keys.append(multiply(residual[source], quarter))
            values.append(multiply(residual[(source + geometry.head_dim // 2) % geometry.hidden], quarter))
    return query, keys, values


def readout(residual, seed):
    result = []
    for row in range(8):
        total = 0
        for j, x in enumerate(residual):
            weight = rounded(Fraction((seed + 13 * row + 7 * j) % 17 - 8, 128))
            total = add(total, multiply(x, weight))
        result.append(total)
    return result


def run_mode(run, mode, seed, geometry, adversarial):
    g = geometry
    reference = AttentionReference("fp16", 0, mode, seed, g)
    bench = run.path / f"mode{mode}.sv"
    bench.write_text(with_time_zero_check(BENCH))
    parameters = dict(MODE=mode, LAYERS=g.layers, HIDDEN=g.hidden, QHEADS=g.q_heads,
                      KVHEADS=g.kv_heads, DIM=g.head_dim, POSITIONS=g.positions, BLOCK=g.block)
    binary = compile_model(run, bench, sorted((ROOT / "rtl").glob("*.sv")), parameters,
                           label=f"mode{mode}-compile")
    startup_check(run, binary, label=f"mode{mode}-startup")
    stimulus = run.path / f"mode{mode}-stimulus.jsonl"
    outputs = run.path / f"mode{mode}-observations.jsonl"

    def transact(process, raw):
        memory = {}
        current = []
        expected = {}
        actual = {}
        pending = None
        start_cycle = None
        active_frame = -1
        frame_context = None
        contexts = defaultdict(list)
        final_residuals, logits, cycles = [], [], []
        compared_requests = compared_responses = compared_writes = 0
        frame_count = 0
        with stimulus.open("x") as inputs_log, outputs.open("x") as observation_log:
            for line in process.stdout:
                raw.write(line)
                fields = line.split()
                if not fields:
                    continue
                if fields[0] == "FRAME_READY":
                    frame = int(fields[1])
                    assert frame == frame_count and pending is None
                    position, layer = divmod(frame, g.layers)
                    if layer == 0:
                        current = initial_residual(seed, position, g.hidden, adversarial)
                    query, k, v = projected_inputs(current, g)
                    for slot, vector in ((2, query), (3, k), (4, v)):
                        for col, bits in enumerate(vector):
                            memory[key(8, row=slot, col=col)] = bits
                    reference.writes.clear()
                    reference.commit(k, layer, position, False)
                    reference.commit(v, layer, position, True)
                    context = reference.attention(query, layer, position)
                    reference.store(5, context, "attention", layer, position)
                    expected = {address: deque(values) for address, values in reference.writes.items()}
                    actual = {}
                    frame_context = position, layer, current[:]
                    active_frame = frame
                    inputs_log.write(json.dumps({
                        "frame": frame, "layer": layer, "position": position,
                        "actual_previous_residual": [f"{x:08x}" for x in current],
                        "query": [f"{x:08x}" for x in query],
                        "key": [f"{x:08x}" for x in k], "value": [f"{x:08x}" for x in v],
                    }) + "\n")
                    inputs_log.flush()
                    process.stdin.write(f"{layer} {position}\n" +
                                        " ".join(f"{x:08x}" for x in query + k + v) + "\n")
                    process.stdin.flush()
                elif fields[0] == "ATTENTION_COMMAND":
                    assert tuple(map(int, fields[2:])) == (frame_context[1], frame_context[0])
                    start_cycle = int(fields[1])
                elif fields[0] == "MEM_REQ":
                    assert pending is None, "multiple scalar requests outstanding"
                    cycle, write, kind, layer, row, col = map(int, fields[1:7])
                    data = int(fields[7], 16)
                    address = key(kind, layer, row=row, col=col)
                    if write:
                        assert address in expected and expected[address], (
                            f"unexpected attention/cache write {coordinates(address)}")
                        want = expected[address].popleft()
                        assert data == want, (
                            f"ATTENTION_BIT_MISMATCH mode={mode} frame={active_frame} "
                            f"address={coordinates(address)} got={data:08x} expected={want:08x}")
                        if kind == 8:
                            actual[col] = data
                        compared_writes += 1
                    else:
                        assert address in memory, f"uninitialized attention read {coordinates(address)}"
                    pending = write, address, data if write else memory[address], cycle
                    compared_requests += 1
                elif fields[0] == "MEM_RSP":
                    assert pending is not None, "uncommanded attention memory completion"
                    write, address, data, issued = pending
                    assert int(fields[1]) > issued
                    assert int(fields[2], 16) == (0 if write else data), "attention memory data mismatch"
                    if write:
                        memory[address] = data
                    pending = None
                    compared_responses += 1
                elif fields[0] == "FRAME_DONE":
                    assert int(fields[1]) == active_frame
                    assert pending is None and all(not q for q in expected.values())
                    assert set(actual) == set(range(g.hidden)), "missing attention components"
                    position, layer, before = frame_context
                    observed = [actual[j] for j in range(g.hidden)]
                    contexts[layer].extend(observed)
                    # This feedback is formed from observed RTL data, not the
                    # expected context, and is the next FRAME_READY input.
                    current = [add(a, multiply(b, rounded(Fraction(1, 32))))
                               for a, b in zip(before, observed)]
                    cycles.append(int(fields[2]) - start_cycle)
                    observation_log.write(json.dumps({
                        "frame": active_frame, "layer": layer, "position": position,
                        "rtl_attention_output": [f"{x:08x}" for x in observed],
                        "actual_chained_residual": [f"{x:08x}" for x in current],
                        "measured_command_to_done_cycles": cycles[-1],
                    }) + "\n")
                    observation_log.flush()
                    if layer + 1 == g.layers:
                        final_residuals.extend(current)
                        logits.extend(readout(current, seed))
                    frame_count += 1
                elif fields[0] == "ATTENTION_COMPARED":
                    assert list(map(int, fields[1:])) == [
                        g.layers * g.positions, compared_requests, compared_responses]
            assert frame_count == g.layers * g.positions
            assert pending is None and compared_requests == compared_responses > 0
        return {
            "contexts": dict(contexts), "final_residuals": final_residuals, "readout_logits": logits,
            "metrics": {"frames_compared": frame_count, "memory_requests": compared_requests,
                        "memory_responses": compared_responses, "writes_compared": compared_writes,
                        "attention_values_compared": g.layers * g.positions * g.hidden,
                        "command_to_done_cycles": cycles},
        }

    observed = run.interactive([run.relative(binary)], f"mode{mode}-simulation", transact)
    for path in (bench, stimulus, outputs):
        run.receipt["generated_sha256"][run.relative(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return observed


def execute(seed, reduced=False, adversarial=False):
    run = Run(f"verifier-attention-drift-{'reduced' if reduced else 'native-heads'}-s{seed}" +
              ("-adversarial" if adversarial else "-bounded"))
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        geometry = (Geometry(layers=3, positions=3, block=2) if reduced else
                    Geometry(layers=28, hidden=1536, intermediate=8960, q_heads=12, kv_heads=2,
                             head_dim=128, group=128, positions=8, block=16))
        definition = run.path / "manifest.json"
        definition.write_text(json.dumps({
            "suite": "anvil-q2-fp-attention-drift-v1", "geometry": asdict(geometry), "seed": seed,
            "shape_class": "reduced" if reduced else "native heads / focused attention",
            "input_class": "outlier/adversarial" if adversarial else "bounded norm-controlled",
            "initial": "((seed+11*position+7*component) mod 33 - 16)/31",
            "sparse_projections": "q=x/4; k=head-group-first(x)/4; v=half-shifted(x)/4; FP32",
            "feedback": "RNE_FP32(x+RNE_FP32(actual_RTL_attention_output/32)), never reset per layer",
            "reference": "Independent rational RNE FP32 and selected-format quantization per operation",
            "readout": "Eight FP32 host readouts of actual final residual, weights in [-8,8]/128",
            "limits": "Per-layer attention NRMSE<=0.03; final residual NRMSE<=0.05; bounded class only",
            "not_claimed": "Native full decoder/token throughput, RTL full-vocabulary logits or FPGA timing",
        }, indent=2) + "\n")
        run.receipt["generated_sha256"] = {
            run.relative(definition): hashlib.sha256(definition.read_bytes()).hexdigest()}
        native, compressed = [run_mode(run, mode, seed, geometry, adversarial) for mode in (0, 1)]

        def metric(a, b):
            return error_metrics([float(value(x)) for x in a], [float(value(x)) for x in b])

        layer_metrics = [
            metric(compressed["contexts"][layer], native["contexts"][layer])
            for layer in range(geometry.layers)]
        residual = metric(compressed["final_residuals"], native["final_residuals"])
        logit = metric(compressed["readout_logits"], native["readout_logits"])
        results = {
            "layer_attention": layer_metrics, "final_residual": residual,
            "host_readout_logit_drift": logit, "mode0": native["metrics"], "mode1": compressed["metrics"],
            "thresholds_applied": not adversarial,
        }
        path = run.path / "drift.json"
        path.write_text(json.dumps(results, indent=2) + "\n")
        if not adversarial:
            assert all(m["normalized_rmse"] <= 0.03 for m in layer_metrics), "attention drift > 0.03"
            assert residual["normalized_rmse"] <= 0.05, "residual drift > 0.05"
        run.finish("passed-focused-only", metrics=results,
                   limitations="Host sparse scalar feedback/readout; native full-token HIL remains mandatory.")
        return 0
    except (AssertionError, ArithmeticError, BrokenPipeError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, choices=(17, 43, 89), default=17)
    parser.add_argument("--reduced", action="store_true")
    parser.add_argument("--adversarial", action="store_true")
    args = parser.parse_args()
    raise SystemExit(execute(args.seed, args.reduced, args.adversarial))
