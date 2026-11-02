"""Independent MLA memory-pin checks, including separating numerical fixtures.

Historical compressed cache may be initialized for these leaf cases. Absorbed
weights are never initialized: every A/B beat must be built by hardware and
compared before it can be read. Context and all other architectural writes are
checked, not just the final projection. Inputs, exact scores, exponential terms,
rational quotients/remainders and forbidden alternatives are frozen before
simulation in mla-fixtures.json.
"""

import argparse
import json
from math import isqrt
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagnostic import hexfile, packed_key, simulate
from evidence import Evidence, rel
from reference import Fixture, Shape, Q16, Q24, exp_trace, rational_round, round_sat, sat32, trunc_div


def constructions():
    cases = []
    for numerator in (65536, -65536, 131073, -131073, 131072, -131072):
        # Only latent component zero contributes to scores. Component one
        # amplifies a one-unit score error into a nonsaturated context error.
        cases.append(dict(name=f"score_{numerator}", qa=[1, 0, 0],
                          history=[[0, 1 << 30, 11]],
                          current=[numerator, -(1 << 30), -7], qr=[0, 0],
                          keys=[[0, 0]], kr=[0, 0]))
    cases += [
        dict(name="equal_three_large", qa=[0, 0, 0],
             history=[[1 << 30, 0, 2], [1 << 30, 0, 3]],
             current=[1 << 30, 1, 8], qr=[0, 0],
             keys=[[0, 0], [0, 0]], kr=[0, 0]),
        dict(name="positive_half", qa=[0, 0, 0], history=[[0, 0, 0]],
             current=[1, 3, 7], qr=[0, 0], keys=[[0, 0]], kr=[0, 0]),
        dict(name="negative_half", qa=[0, 0, 0], history=[[0, 0, 0]],
             current=[-1, -3, -7], qr=[0, 0], keys=[[0, 0]], kr=[0, 0]),
        dict(name="signed_nonintegral", qa=[0, 0, 0],
             history=[[0, 1, -2], [0, 2, -3]],
             current=[1, 2, -3], qr=[0, 0],
             keys=[[0, 0], [0, 0]], kr=[0, 0]),
        dict(name="renormalized_probability", qa=[65536, 0, 0],
             history=[[-131072, 1 << 30, 17], [-262144, -(1 << 30), -21]],
             current=[0, 1 << 29, 9], qr=[0, 0],
             keys=[[0, 0], [0, 0]], kr=[0, 0]),
        dict(name="rotary_score", qa=[0, 0, 0],
             history=[[0, 1 << 30, 1]], current=[1, -(1 << 30), -1],
             qr=[65536, -32768], keys=[[0, 0]], kr=[8, 0]),
        dict(name="score_saturation", qa=[(1 << 31)-1, -(1 << 31), 0],
             history=[[(1 << 31)-1, -(1 << 31), 3]],
             current=[-(1 << 31), (1 << 31)-1, -9],
             qr=[0, 0], keys=[[0, 0]], kr=[0, 0]),
    ]
    return cases


def make_fixture(case, nope=2):
    shape = Shape(hidden=8, intermediate=8, moe_intermediate=8, heads=1,
                  rank=3, nope=nope, rope=2, value=1, layers=1,
                  first_dense=0, experts=1, topk=1, vocab=4, maxseq=3)
    fixture = Fixture(shape, seed=17)
    fixture.initial = {key: 0 for key in fixture.initial
                       if key[0] == 15 and key[2] in (0, 6)}
    x = [Q16] + [0]*7
    for col, value in enumerate(x):
        fixture.initial[8, 0, 0, 1, col] = value
    for r, value in enumerate(case["current"]):
        fixture.initial[15, 0, 0, r, 0] = value
    for r, value in enumerate(case["qa"]):
        fixture.initial[15, 0, 0, 4 << 28, r] = value
    fixture.initial[15, 0, 0, 2 << 28, 0] = Q16
    for r, value in enumerate(case["kr"]):
        fixture.initial[15, 0, 0, (1 << 28) | r, 0] = value
    for r, value in enumerate(case["qr"]):
        fixture.initial[15, 0, 0, (3 << 28) | r, 0] = value
    for r in range(3):
        fixture.initial[15, 0, 0, 5 << 28, r] = (r+1)*8192
    for row in range(8):
        fixture.initial[15, 0, 0, (6 << 28) | row, 0] = (row-4)*4096
    for pos in range(3):
        fixture.initial[15, 0, 6, pos, 0] = Q16
        fixture.initial[15, 0, 6, pos, 1] = 0
    if case["name"] == "rotary_score":
        fixture.initial[15, 0, 6, len(case["history"]), 0] = 49152
        fixture.initial[15, 0, 6, len(case["history"]), 1] = 32768
    for pos, (latent, key) in enumerate(zip(case["history"], case["keys"], strict=True)):
        fixture.cache[0, pos] = latent, key
        for col, value in enumerate(latent+key):
            fixture.initial[15, 0, 3, pos, col] = value
    pos = len(case["history"])
    output = fixture.mla(0, pos, x)
    a, b = fixture.absorbed[0, 0]
    qa = [round_sat(sum(v*w for v, w in zip(row, x, strict=True)), 32) for row in a]
    qr = [fixture.writes[15, 0, 7, 6, r][-1] for r in range(2)]
    qr = [v if v < (1 << 31) else v-(1 << 32) for v in qr]
    scale = isqrt((nope+2) << 32)
    numerators = [sum(v*w for v, w in zip(qa, fixture.cache[0, t][0], strict=True)) +
                  sum(v*w for v, w in zip(qr, fixture.cache[0, t][1], strict=True))
                  for t in range(pos+1)]
    scores = [sat32(trunc_div(n, scale)) for n in numerators]
    traces = [exp_trace(z-max(scores)) for z in scores]
    exponentials = [trace["result"] for trace in traces]
    denominator = sum(exponentials)
    contexts = []
    for r in range(3):
        n = sum(e*fixture.cache[0, t][0][r] for t, e in enumerate(exponentials))
        q, rem = divmod(abs(n), denominator)
        probabilities = [e*Q24//denominator for e in exponentials]
        quantized_n = sum(p*fixture.cache[0, t][0][r] for t, p in enumerate(probabilities))
        contexts.append(dict(numerator=n, denominator=denominator, quotient=q,
                             remainder=rem, expected=rational_round(n, denominator),
                             probabilities=probabilities,
                             forbidden_fixed_probability=round_sat(quantized_n, 24),
                             forbidden_renormalized_probability=rational_round(
                                 quantized_n, sum(probabilities))))
    # Independently expand the contraction rather than consume absorbed A/B.
    unabsorbed_query = [round_sat(sum(
        fixture.raw(0, 4, 0, d, 3)[r] *
        fixture.raw(0, 2, 0, d, 8)[j] * x[j]
        for d in range(nope) for j in range(8)), 32) for r in range(3)]
    unabsorbed_output = [round_sat(sum(
        fixture.raw(0, 6, 0, i, 1)[v] *
        fixture.raw(0, 5, 0, v, 3)[r] * contexts[r]["expected"]
        for v in range(1) for r in range(3)), 32) for i in range(8)]
    if unabsorbed_query != qa or unabsorbed_output != output:
        raise AssertionError("independent unabsorbed contraction disagrees")
    if case["name"].startswith("score_") and case["name"] != "score_saturation" and nope == 2:
        n = int(case["name"].removeprefix("score_"))
        if numerators != [0, n] or scores != [0, trunc_div(n, 131072)]:
            raise AssertionError("score construction does not realize frozen numerator")
    if case["name"] == "equal_three_large":
        if contexts[0]["expected"] != 1 << 30 or contexts[0]["forbidden_fixed_probability"] != (1 << 30)-64:
            raise AssertionError("three-token discriminator lost")
    if case["name"] == "renormalized_probability":
        if not any(c["expected"] != c["forbidden_renormalized_probability"] for c in contexts):
            raise AssertionError("missing renormalized probability discriminator")
    if case["name"] == "rotary_score":
        if scores[-1] == 0 or contexts[1]["expected"] == 0:
            raise AssertionError("rotary score must distinguish omitted rotary arithmetic in the output")
    return fixture, dict(name=case["name"], position=pos, nope=nope, input=x,
                         qa=qa, qr=qr, score_scale=scale,
                         score_numerators=numerators,
                         score_quotients=[trunc_div(n, scale) for n in numerators],
                         score_remainders=[abs(n) % scale for n in numerators],
                         scores=scores, exponentials=traces, contexts=contexts,
                         unabsorbed_query=unabsorbed_query,
                         unabsorbed_output=unabsorbed_output)


def mla_bench(evidence, nope=2):
    fixtures, traces = zip(*(make_fixture(case, nope) for case in constructions()), strict=True)
    keys = sorted(set().union(*(set(f.initial) | set(f.writes) for f in fixtures)))
    starts, counts, expected = [], [], []
    for fixture in fixtures:
        for key in keys:
            starts.append(len(expected))
            counts.append(len(fixture.writes[key]))
            expected.extend(fixture.writes[key])
    image = evidence.path / "checkpoint-images"
    image.mkdir()
    hexfile(image / "keys.hex", [packed_key(k) for k in keys], 26)
    hexfile(image / "memory.hex", [f.initial.get(k, 0) & 0xffffffff for f in fixtures for k in keys], 8)
    hexfile(image / "initialized.hex", [int(k in f.initial) for f in fixtures for k in keys], 1)
    hexfile(image / "starts.hex", starts, 8)
    hexfile(image / "counts.hex", counts, 8)
    hexfile(image / "expected.hex", expected, 8)
    hexfile(image / "positions.hex", [t["position"] for t in traces], 8)
    (evidence.path / "mla-fixtures.json").write_text(json.dumps(traces, indent=2)+"\n")
    bench = BENCH.replace("@SLOTS@", str(len(keys))).replace("@WRITES@", str(len(expected)))
    bench = bench.replace("@CASES@", str(len(fixtures))).replace("@NOPE@", str(nope))
    (evidence.path / "mla.sv").write_text(bench)
    return dict(cases=len(fixtures), expected_writes=len(expected), nope=nope,
                expected_contexts=len(fixtures)*3,
                absorption_words=len(fixtures)*3*(3*8+8*3))


BENCH = r"""
module tb;
  localparam SLOTS=@SLOTS@, WRITES=@WRITES@, CASES=@CASES@;
  reg clk=0; always #5 clk=~clk;
  reg rst_n,flush=0,cmd_valid=0,cmd_phase=1;
  wire cmd_ready,done,error;
  reg [31:0] cmd_epoch=0,cmd_layer=0,cmd_pos=0;
  wire [63:0] kv_read_bytes,kv_write_bytes,kv_dense_equiv_bytes;
  wire c_req_valid,c_req_write,c_rsp_ready;
  wire [3:0] c_req_kind;
  wire [2:0] c_req_proj;
  wire [31:0] c_req_layer,c_req_row,c_req_col,c_req_wdata;
  reg c_req_ready=0,c_rsp_valid=0,c_rsp_error=0;
  reg [31:0] c_rsp_rdata=0;
  anvil_d1_mla_engine #(.NUM_LAYERS(1),.HIDDEN_SIZE(8),.NUM_Q_HEADS(1),
    .KV_LORA_RANK(3),.QK_NOPE_HEAD_DIM(@NOPE@),.QK_ROPE_HEAD_DIM(2),
    .V_HEAD_DIM(1),.MAX_SEQ_LEN(3)) device (
    .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
    .cmd_epoch(cmd_epoch),.cmd_layer(cmd_layer),.cmd_pos(cmd_pos),.cmd_phase(cmd_phase),
    .done(done),.error(error),.kv_read_bytes(kv_read_bytes),
    .kv_write_bytes(kv_write_bytes),.kv_dense_equiv_bytes(kv_dense_equiv_bytes),
    .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),.c_req_write(c_req_write),
    .c_req_kind(c_req_kind),.c_req_layer(c_req_layer),.c_req_proj(c_req_proj),
    .c_req_row(c_req_row),.c_req_col(c_req_col),.c_req_wdata(c_req_wdata),
    .c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),.c_rsp_error(c_rsp_error),
    .c_rsp_rdata(c_rsp_rdata)
  );
  reg [102:0] keys[0:SLOTS-1];
  reg [31:0] memory[0:CASES*SLOTS-1],starts[0:CASES*SLOTS-1],counts[0:CASES*SLOTS-1];
  reg initialized[0:CASES*SLOTS-1];
  reg [31:0] expected[0:WRITES-1],positions[0:CASES-1];
  integer consumed[0:CASES*SLOTS-1];
  integer active=0,stimulus=0,cycles=0,reads=0,writes=0,completions=0,accepted=0;
  integer stalls=0,reset_samples=0,cache_reads=0,cache_writes=0,dense_beats=0;
  integer contexts=0,absorption=0,slot,index,response_delay=0;
  reg pending=0,pending_final=0,stalled=0,preedge_done=0;
  reg [31:0] response_data=0;
  reg [136:0] held=0;
  reg [63:0] saved_reads=0,saved_writes=0,saved_dense=0;
  function automatic integer lookup(input [102:0] target);
    integer low,high,middle;
    begin
      low=0; high=SLOTS-1; lookup=-1;
      while (low<=high) begin
        middle=(low+high)/2;
        if (keys[middle]==target) begin lookup=middle; low=high+1; end
        else if (keys[middle]<target) low=middle+1; else high=middle-1;
      end
    end
  endfunction
  task automatic reset_check;
    begin
      if ({cmd_ready,done,error,kv_read_bytes,kv_write_bytes,kv_dense_equiv_bytes,
           c_req_valid,c_req_write,c_req_kind,c_req_layer,c_req_proj,c_req_row,
           c_req_col,c_req_wdata,c_rsp_ready} !== 0) $fatal(1,"MLA_RESET_XZ_OR_NONZERO");
      reset_samples=reset_samples+1;
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    rst_n=0;
    $readmemh("checkpoint-images/keys.hex",keys);
    $readmemh("checkpoint-images/memory.hex",memory);
    $readmemh("checkpoint-images/initialized.hex",initialized);
    $readmemh("checkpoint-images/starts.hex",starts);
    $readmemh("checkpoint-images/counts.hex",counts);
    $readmemh("checkpoint-images/expected.hex",expected);
    $readmemh("checkpoint-images/positions.hex",positions);
    for (integer j=0;j<CASES*SLOTS;j=j+1) consumed[j]=0;
`ifdef VERILATOR
    #1;
`else
    #0;
`endif
    reset_check(); repeat(2) @(negedge clk); #1; rst_n=1;
    for (stimulus=0;stimulus<CASES;stimulus=stimulus+1) begin
      @(negedge clk); while (cmd_ready!==1'b1) @(negedge clk);
      cmd_epoch=stimulus+1; cmd_pos=positions[stimulus]; cmd_valid=1;
      @(posedge clk);
      if (cmd_ready!==1'b1 || c_req_valid!==0) $fatal(1,"MLA_ACCEPTANCE");
      #1;
      if (cmd_ready!==0 || done!==0 || c_req_valid!==0) $fatal(1,"MLA_POST_ACCEPTANCE");
      @(negedge clk); cmd_valid=0;
      while (completions<=stimulus) @(negedge clk);
      repeat(3) @(negedge clk);
      if ({kv_read_bytes,kv_write_bytes,kv_dense_equiv_bytes} !==
          {saved_reads,saved_writes,saved_dense}) $fatal(1,"MLA_TELEMETRY_UNSTABLE");
    end
    for (integer j=0;j<CASES*SLOTS;j=j+1)
      if (consumed[j]!==counts[j]) $fatal(1,"MLA_MISSING_WRITE index=%0d",j);
    if (writes!=WRITES || contexts!=CASES*3 || absorption!=CASES*144 ||
        accepted!=CASES || completions!=CASES || stalls==0 || reset_samples<5)
      $fatal(1,"MLA_MISSING_COMPARISONS");
    $display("SUMMARY mla_cases=%0d writes=%0d reads=%0d contexts=%0d absorption=%0d stalls=%0d reset=%0d cycles=%0d",
      CASES,writes,reads,contexts,absorption,stalls,reset_samples,cycles);
    $finish;
  end
  always @(negedge clk) if (rst_n) c_req_ready=!pending && cycles%7!=0;
  always @(posedge clk) if (rst_n) begin
    preedge_done=done;
    cycles=cycles+1;
    if (cycles>500000) $fatal(1,"MLA_CYCLE_BOUND");
    if ((^{cmd_ready,done,error,c_req_valid,c_rsp_ready})===1'bx) $fatal(1,"MLA_CONTROL_XZ");
    if (cmd_valid && cmd_ready) begin
      active=stimulus; accepted=accepted+1; cache_reads=0; cache_writes=0; dense_beats=0;
    end
    if (stalled && {c_req_valid,c_req_write,c_req_kind,c_req_layer,c_req_proj,
                   c_req_row,c_req_col,c_req_wdata} !== held) $fatal(1,"MLA_UNSTABLE_REQUEST");
    stalled=c_req_valid && !c_req_ready;
    held={c_req_valid,c_req_write,c_req_kind,c_req_layer,c_req_proj,c_req_row,c_req_col,c_req_wdata};
    if (stalled) stalls=stalls+1;
    if (pending && !c_rsp_valid) begin
      if (response_delay==0) begin c_rsp_valid<=1; c_rsp_rdata<=response_data; end
      else response_delay=response_delay-1;
    end
    if (c_req_valid && c_req_ready) begin
      if (pending || (^{c_req_write,c_req_kind,c_req_layer,c_req_proj,
                       c_req_row,c_req_col,c_req_wdata})===1'bx) $fatal(1,"MLA_REQUEST_XZ_OWNERSHIP");
      slot=lookup({c_req_kind,c_req_layer,c_req_proj,c_req_row,c_req_col});
      if (slot<0) $fatal(1,"MLA_UNMAPPED_MEMORY proj=%0d row=%h col=%0d",c_req_proj,c_req_row,c_req_col);
      index=active*SLOTS+slot;
      pending<=1; response_delay=cycles%5;
      pending_final<=c_req_write && c_req_proj==7 && c_req_row==3 && c_req_col==7;
      if (c_req_kind==15 && c_req_proj==3) begin
        if (c_req_row>positions[active] || c_req_col>=5) $fatal(1,"MLA_EXPANDED_OR_NONCAUSAL_CACHE");
        if (c_req_write) cache_writes=cache_writes+1; else cache_reads=cache_reads+1;
        if (c_req_col==0) dense_beats=dense_beats+1;
      end
      if (c_req_write) begin
        if (consumed[index]>=counts[index] ||
            c_req_wdata !== expected[starts[index]+consumed[index]])
          $fatal(1,"MLA_NUMERICAL_WRITE_MISMATCH case=%0d proj=%0d row=%h col=%0d actual=%h expected=%h",
            active,c_req_proj,c_req_row,c_req_col,c_req_wdata,expected[starts[index]+consumed[index]]);
        consumed[index]=consumed[index]+1; writes=writes+1;
        memory[index]=c_req_wdata; initialized[index]=1; response_data<=0;
        if (c_req_proj==7 && c_req_row==7) contexts=contexts+1;
        if (c_req_proj==1 || c_req_proj==2) absorption=absorption+1;
      end else begin
        if (initialized[index]!==1'b1) $fatal(1,"MLA_UNINITIALIZED_READ");
        response_data<=memory[index]; reads=reads+1;
      end
    end
    if (c_rsp_valid && c_rsp_ready) begin
      if (!pending) $fatal(1,"MLA_UNOWNED_RESPONSE");
      pending<=0; c_rsp_valid<=0;
      if (pending_final) begin
        #1;
        if (done!==1'b1 || error!==0 || cmd_ready!==0) $fatal(1,"MLA_FINAL_ACK_LATENCY");
      end
    end
    if (preedge_done) begin
      if (error!==0 || pending || cache_reads!=2*(positions[active]+1)*5 || cache_writes!=5 ||
          kv_read_bytes!==64'(cache_reads*4) || kv_write_bytes!==64'(cache_writes*4) ||
          kv_dense_equiv_bytes!==64'(dense_beats*(@NOPE@+2+1)*4))
        $fatal(1,"MLA_COMPLETION_TELEMETRY");
      saved_reads=kv_read_bytes; saved_writes=kv_write_bytes; saved_dense=kv_dense_equiv_bytes;
      completions=completions+1;
      #1;
      if (done!==0 || cmd_ready!==1) $fatal(1,"MLA_COMPLETION_RETIREMENT");
    end
  end
endmodule
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim", choices=("icarus", "verilator"), default="verilator")
    parser.add_argument("--nope", type=int, choices=(2, 3), default=2)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    evidence = Evidence(f"mla-{args.sim}-nope{args.nope}", args.repair_of)
    try:
        summary = mla_bench(evidence, args.nope)
        summary["observations"] = simulate(evidence, "mla.sv", args.sim)
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
