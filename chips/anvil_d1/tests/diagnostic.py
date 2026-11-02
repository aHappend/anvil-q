"""Bounded public-pin preparation, not a substitute for the five admitted suites.

Native case: check every accepted write, every logit, initialized reads, request
stability, registered completion, reset and nonzero comparisons using a generated
complete-inference fixture. Raw memories use actual DUT writes, never oracle
answers as read responses. Compile larger/multitoken work with Verilator.
"""

import argparse
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import Evidence, ROOT, rel
from reference import Fixture, Shape


def hexfile(path, values, digits):
    path.write_text("".join(f"{v:0{digits}x}\n" for v in values))


def packed_key(key):
    kind, layer, proj, row, col = key
    return kind << 99 | layer << 67 | proj << 64 | row << 32 | col


def native_bench(evidence, seed, tokens):
    fixture = Fixture(seed=seed)
    expected_logits = [fixture.token((pos+2) % fixture.shape.vocab, pos)
                       for pos in range(tokens)]
    keys = sorted(set(fixture.initial) | set(fixture.writes))
    expected_writes, starts, counts = [], [], []
    for key in keys:
        starts.append(len(expected_writes))
        counts.append(len(fixture.writes[key]))
        expected_writes.extend(fixture.writes[key])
    image = evidence.path / "checkpoint-images"
    image.mkdir()
    hexfile(image / "keys.hex", [packed_key(k) for k in keys], 26)
    hexfile(image / "memory.hex", [fixture.initial.get(k, 0) & 0xffffffff for k in keys], 8)
    hexfile(image / "initialized.hex", [int(k in fixture.initial) for k in keys], 1)
    hexfile(image / "starts.hex", starts, 8)
    hexfile(image / "counts.hex", counts, 8)
    hexfile(image / "expected-writes.hex", expected_writes, 8)
    hexfile(image / "logits.hex", [v & 0xffffffff for seq in expected_logits for v in seq], 8)
    (evidence.path / "fixture.json").write_text(json.dumps(dict(
        seed=seed, geometry=vars(fixture.shape), tokens=tokens,
        expected_logits=expected_logits, routing=fixture.routing,
        memory_slots=len(keys), expected_writes=len(expected_writes)), indent=2) + "\n")
    bench = NATIVE_BENCH.replace("@SLOTS@", str(len(keys)))
    bench = bench.replace("@WRITES@", str(len(expected_writes)))
    bench = bench.replace("@TOKENS@", str(tokens))
    bench = bench.replace("@CYCLES@", str(500000 if tokens == 1 else 10000000))
    (evidence.path / "native.sv").write_text(bench)
    return fixture


NATIVE_BENCH = r"""
module tb;
  localparam B=2, SLOTS=@SLOTS@, WRITES=@WRITES@, TOKENS=@TOKENS@;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n, cancel=0, token_valid=0, new_sequence=0, token_phase=0;
  reg [31:0] token_id=0, token_pos=0;
  wire token_ready, logit_valid, done, error, cancel_done;
  reg logit_ready=0;
  wire [31:0] logit_index;
  wire signed [31:0] logit_data;
  wire [B-1:0] mem_req_valid, mem_req_write, mem_rsp_ready;
  wire [B*4-1:0] mem_req_kind;
  wire [B*3-1:0] mem_req_proj;
  wire [B*32-1:0] mem_req_layer, mem_req_row, mem_req_col, mem_req_wdata;
  wire [B*64-1:0] mem_req_tag;
  reg [B-1:0] mem_req_ready=0, mem_rsp_valid=0, mem_rsp_error=0;
  reg [B*32-1:0] mem_rsp_rdata=0;
  reg [B*64-1:0] mem_rsp_tag=0;
  wire csr_ready, csr_rsp_valid, csr_error;
  wire [31:0] csr_rdata;
  anvil_d1_top #(
    .NUM_LAYERS(2),.HIDDEN_SIZE(16),.INTERMEDIATE_SIZE(16),.NUM_Q_HEADS(2),
    .KV_LORA_RANK(3),.QK_NOPE_HEAD_DIM(2),.QK_ROPE_HEAD_DIM(2),.V_HEAD_DIM(2),
    .ROUTED_EXPERTS(7),.TOP_K(6),.SHARED_EXPERTS(2),.MOE_INTERMEDIATE_SIZE(8),
    .FIRST_DENSE_LAYERS(1),.VOCAB_SIZE(8),.MAX_SEQ_LEN(5),
    .BANKS(B),.QUEUE_DEPTH(3),.TILE_K(8),.TILE_ROWS(3)
  ) device (
    .clk(clk),.rst_n(rst_n),.cancel(cancel),
    .token_valid(token_valid),.token_ready(token_ready),
    .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),.token_phase(token_phase),
    .logit_valid(logit_valid),.logit_ready(logit_ready),
    .logit_index(logit_index),.logit_data(logit_data),.done(done),.error(error),.cancel_done(cancel_done),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),
    .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_req_tag(mem_req_tag),.mem_rsp_valid(mem_rsp_valid),.mem_rsp_error(mem_rsp_error),
    .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag),
    .csr_valid(1'b0),.csr_write(1'b0),.csr_addr(12'd0),.csr_wdata(32'd0),
    .csr_wstrb(4'd0),.csr_rsp_ready(1'b1),.csr_ready(csr_ready),
    .csr_rsp_valid(csr_rsp_valid),.csr_rdata(csr_rdata),.csr_error(csr_error)
  );
  reg [102:0] keys [0:SLOTS-1];
  reg [31:0] memory [0:SLOTS-1];
  reg initialized [0:SLOTS-1];
  reg [31:0] starts [0:SLOTS-1], counts [0:SLOTS-1];
  integer consumed [0:SLOTS-1];
  reg [31:0] expected [0:WRITES-1], logits [0:TOKENS*8-1];
  reg [B-1:0] pending=0;
  integer delay_cycles [0:B-1];
  reg [B*32-1:0] response_data=0;
  reg [B*64-1:0] response_tag=0;
  reg [200:0] held_request [0:B-1];
  reg [B-1:0] stalled=0;
  reg held_logit=0;
  reg [63:0] previous_logit=0;
  integer cycles=0, writes=0, reads=0, compared_logits=0, completed=0, accepted=0;
  integer request_stalls=0, logit_stalls=0, reset_samples=0;
  integer logit_delay=0;
  integer b, slot, i, position;
  reg [102:0] key;

  function automatic integer lookup(input [102:0] target);
    integer low, high, middle;
    begin
      low=0; high=SLOTS-1; lookup=-1;
      while (low<=high) begin
        middle=(low+high)/2;
        if (keys[middle]==target) begin lookup=middle; low=high+1; end
        else if (keys[middle]<target) low=middle+1;
        else high=middle-1;
      end
    end
  endfunction

  task automatic check_reset;
    begin
      if ({token_ready,logit_valid,logit_index,logit_data,done,error,cancel_done,
           mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
           mem_req_row,mem_req_col,mem_req_wdata,mem_req_tag,mem_rsp_ready,
           csr_ready,csr_rsp_valid,csr_rdata,csr_error} !== 0)
        $fatal(1,"RESET_XZ_OR_NONZERO t=%0t",$time);
      reset_samples=reset_samples+1;
    end
  endtask

  initial begin
    rst_n=0;
    $readmemh("checkpoint-images/keys.hex",keys);
    $readmemh("checkpoint-images/memory.hex",memory);
    $readmemh("checkpoint-images/initialized.hex",initialized);
    $readmemh("checkpoint-images/starts.hex",starts);
    $readmemh("checkpoint-images/counts.hex",counts);
    $readmemh("checkpoint-images/expected-writes.hex",expected);
    $readmemh("checkpoint-images/logits.hex",logits);
    for (i=0;i<SLOTS;i=i+1) consumed[i]=0;
    for (i=0;i<B;i=i+1) delay_cycles[i]=0;
`ifdef VERILATOR
    #1;
`else
    #0;
`endif
    check_reset();
    repeat(2) @(negedge clk);
    #1; rst_n=1;
    for (position=0;position<TOKENS;position=position+1) begin
      @(negedge clk);
      token_id=(position+2)%8; token_pos=position;
      new_sequence=position==0; token_phase=position!=0; token_valid=1;
      @(posedge clk);
      while (!token_ready) @(posedge clk);
      @(negedge clk); token_valid=0;
      while (completed<=position) @(negedge clk);
    end
    repeat(3) @(negedge clk);
    if (writes!==WRITES || compared_logits!==TOKENS*8 || accepted!==TOKENS ||
        completed!==TOKENS || reads==0 || reset_samples<5 || request_stalls==0 ||
        logit_stalls==0) $fatal(1,"MISSING_COMPARISONS writes=%0d expected=%0d logits=%0d accepted=%0d completed=%0d reads=%0d reset=%0d request_stalls=%0d logit_stalls=%0d",
          writes,WRITES,compared_logits,accepted,completed,reads,reset_samples,request_stalls,logit_stalls);
    for (i=0;i<SLOTS;i=i+1)
      if (consumed[i]!==counts[i]) $fatal(1,"MISSING_WRITE slot=%0d",i);
    $display("SUMMARY cycles=%0d tokens=%0d writes=%0d reads=%0d logits=%0d reset=%0d request_stalls=%0d logit_stalls=%0d",
      cycles,completed,writes,reads,compared_logits,reset_samples,request_stalls,logit_stalls);
    $finish;
  end

  always @(negedge clk) begin
    if (!rst_n) check_reset();
    else begin
      for (integer bank=0;bank<B;bank=bank+1)
        mem_req_ready[bank]=!pending[bank] && (cycles+bank)%7!=0;
      if (!logit_valid) begin logit_ready=0; logit_delay=0; end
      else if (logit_delay<4) begin logit_ready=0; logit_delay=logit_delay+1; end
      else logit_ready=1;
    end
  end

  always @(posedge clk) begin
    if (!rst_n) check_reset();
    else begin
      cycles=cycles+1;
      if (cycles>@CYCLES@) $fatal(1,"DIAGNOSTIC_CYCLE_BOUND cycles=%0d reads=%0d writes=%0d logits=%0d",
        cycles,reads,writes,compared_logits);
      if ((^{token_ready,logit_valid,done,error,cancel_done,mem_req_valid,mem_rsp_ready,
             csr_ready,csr_rsp_valid,csr_error}) === 1'bx)
        $fatal(1,"ACTIVE_CONTROL_XZ cycle=%0d",cycles);
      if (token_valid && token_ready) accepted=accepted+1;
      for (b=0;b<B;b=b+1) begin
        if (stalled[b] &&
            {mem_req_valid[b],mem_req_write[b],mem_req_kind[b*4+:4],mem_req_layer[b*32+:32],
             mem_req_proj[b*3+:3],mem_req_row[b*32+:32],mem_req_col[b*32+:32],
             mem_req_wdata[b*32+:32],mem_req_tag[b*64+:64]} !== held_request[b])
          $fatal(1,"REQUEST_UNSTABLE bank=%0d cycle=%0d",b,cycles);
        stalled[b]=mem_req_valid[b] && !mem_req_ready[b];
        held_request[b]={mem_req_valid[b],mem_req_write[b],mem_req_kind[b*4+:4],
          mem_req_layer[b*32+:32],mem_req_proj[b*3+:3],mem_req_row[b*32+:32],
          mem_req_col[b*32+:32],mem_req_wdata[b*32+:32],mem_req_tag[b*64+:64]};
        if (stalled[b]) request_stalls=request_stalls+1;
        if (mem_rsp_valid[b] && mem_rsp_ready[b]) begin
          mem_rsp_valid[b]<=0; pending[b]<=0;
        end
        if (pending[b] && !mem_rsp_valid[b]) begin
          if (delay_cycles[b]==0) begin
            mem_rsp_valid[b]<=1;
            mem_rsp_rdata[b*32+:32]<=response_data[b*32+:32];
            mem_rsp_tag[b*64+:64]<=response_tag[b*64+:64];
          end else delay_cycles[b]=delay_cycles[b]-1;
        end
        if (mem_req_valid[b] && mem_req_ready[b]) begin
          if ((^{mem_req_write[b],mem_req_kind[b*4+:4],mem_req_layer[b*32+:32],
                 mem_req_proj[b*3+:3],mem_req_row[b*32+:32],mem_req_col[b*32+:32],
                 mem_req_wdata[b*32+:32],mem_req_tag[b*64+:64]}) === 1'bx)
            $fatal(1,"REQUEST_XZ cycle=%0d",cycles);
          key={mem_req_kind[b*4+:4],mem_req_layer[b*32+:32],mem_req_proj[b*3+:3],
               mem_req_row[b*32+:32],mem_req_col[b*32+:32]};
          slot=lookup(key);
          if (slot<0) $fatal(1,"UNMAPPED_MEMORY kind=%0d layer=%0d proj=%0d row=%h col=%0d",
            mem_req_kind[b*4+:4],mem_req_layer[b*32+:32],mem_req_proj[b*3+:3],
            mem_req_row[b*32+:32],mem_req_col[b*32+:32]);
          if (pending[b]) $fatal(1,"MEMORY_MODEL_BANK_OWNERSHIP");
          pending[b]<=1;
          delay_cycles[b]=(cycles+b*3)%5;
          response_tag[b*64+:64]<=mem_req_tag[b*64+:64];
          if (mem_req_write[b]) begin
            if (consumed[slot]>=counts[slot]) $fatal(1,"UNEXPECTED_WRITE slot=%0d key=%h",slot,key);
            if (mem_req_wdata[b*32+:32] !== expected[starts[slot]+consumed[slot]])
              $fatal(1,"NUMERICAL_WRITE_MISMATCH cycle=%0d slot=%0d kind=%0d layer=%0d proj=%0d row=%h col=%0d occurrence=%0d actual=%h expected=%h",
                cycles,slot,mem_req_kind[b*4+:4],mem_req_layer[b*32+:32],mem_req_proj[b*3+:3],
                mem_req_row[b*32+:32],mem_req_col[b*32+:32],consumed[slot],
                mem_req_wdata[b*32+:32],expected[starts[slot]+consumed[slot]]);
            consumed[slot]=consumed[slot]+1;
            memory[slot]=mem_req_wdata[b*32+:32];
            initialized[slot]=1;
            response_data[b*32+:32]<=0;
            writes=writes+1;
          end else begin
            if (initialized[slot]!==1'b1) $fatal(1,"UNINITIALIZED_READ slot=%0d key=%h",slot,key);
            response_data[b*32+:32]<=memory[slot];
            reads=reads+1;
          end
        end
      end
      if (held_logit && {logit_valid,logit_index,logit_data} !== {1'b1,previous_logit})
        $fatal(1,"LOGIT_UNSTABLE");
      held_logit=logit_valid && !logit_ready;
      previous_logit={logit_index,logit_data};
      if (held_logit) logit_stalls=logit_stalls+1;
      if (logit_valid && logit_ready) begin
        if (compared_logits>=TOKENS*8 ||
            logit_index !== compared_logits%8 || logit_data !== logits[compared_logits])
          $fatal(1,"LOGIT_MISMATCH count=%0d index=%0d actual=%h expected=%h",
            compared_logits,logit_index,logit_data,logits[compared_logits]);
        compared_logits=compared_logits+1;
      end
      if (done) begin
        if (error !== 1'b0 || compared_logits!==(completed+1)*8)
          $fatal(1,"TOKEN_ERROR_OR_PREMATURE_DONE cycle=%0d error=%b logits=%0d reads=%0d writes=%0d",
            cycles,error,compared_logits,reads,writes);
        completed=completed+1;
      end
      if (logit_valid && logit_ready && logit_index==7) begin
        #1;
        if (done !== 1'b1 || token_ready !== 1'b0)
          $fatal(1,"FINAL_LOGIT_COMPLETION_LATENCY");
      end
    end
  end
endmodule
"""


def simulate(evidence, bench, simulator, source_root=None, extra_sources=()):
    source_root = ROOT if source_root is None else Path(source_root)
    rtl = sorted(source_root.glob("rtl/*.sv"))
    parent = sorted(source_root.glob("anvil_q3_reference/rtl/*.sv"))
    inputs = [rel(p) for p in parent + rtl]+[rel(p) for p in extra_sources]
    bench_path = rel(evidence.path / bench)
    if simulator == "icarus":
        exe = evidence.path / "simulation.vvp"
        evidence.run("compile", ["iverilog", "-g2012", "-Wall", "-s", "tb", "-o",
                                rel(exe), *inputs, bench_path], ["iverilog", "-V"])
        output = evidence.run("simulation", ["vvp", "simulation.vvp"], ["vvp", "-V"],
                              cwd=evidence.path)
        exe.unlink()
    else:
        obj = evidence.path / "obj_dir"
        evidence.run("compile", ["verilator", "--binary", "--timing", "-Wno-fatal",
                                "--top-module", "tb", "-j", "2", "--Mdir", rel(obj),
                                "-o", "simulation", *inputs, bench_path],
                     ["verilator", "--version"])
        try:
            output = evidence.run("simulation", ["./obj_dir/simulation"], ["verilator", "--version"],
                                  cwd=evidence.path)
        finally:
            shutil.rmtree(obj)
    text = output.read_text()
    if "SUMMARY " not in text:
        raise RuntimeError(f"simulator exited zero without comparisons: {rel(output)}")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=["native"], default="native")
    parser.add_argument("--sim", choices=["icarus", "verilator"], default="verilator")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--tokens", type=int, choices=range(1, 5), default=1)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    runs = ([("icarus", 1), ("verilator", args.tokens)] if args.sim == "icarus" and args.tokens > 1
            else [(args.sim, args.tokens)])
    for simulator, tokens in runs:
        evidence = Evidence(f"{args.case}-{simulator}-seed{args.seed}", args.repair_of)
        try:
            native_bench(evidence, args.seed, tokens)
            text = simulate(evidence, "native.sv", simulator)
            evidence.finish("passed", observations=text)
            print(text.strip())
        except Exception as exc:
            evidence.finish("failed", error=str(exc))
            print(str(exc), file=sys.stderr)
            print(rel(evidence.path / "receipt.json"), file=sys.stderr)
            return 1
        print(rel(evidence.path / "receipt.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
