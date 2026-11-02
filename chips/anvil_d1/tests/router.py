"""Public-pin hardware routing, complete experts and retained-prefetch checks.

Fixtures include every affinity row of 64 experts, cutoff ties, all-negative
scores, and distinct generated expert weights. Check every scratch write and
mixture scalar against the independent SwiGLU model. The first gate tile of
each winner must be fetched once by client 1, acknowledged, and never reread
by client 0. Exact routed outputs therefore also test consumption of tile data.
"""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagnostic import hexfile, packed_key, simulate
from evidence import Evidence, rel
from reference import Fixture, Shape, Q16


def fixtures(experts=64, topk=6, hidden=16, tile_k=8, tile_rows=3):
    shape = Shape(hidden=hidden, intermediate=8, moe_intermediate=8,
                  heads=1, rank=1, nope=1, rope=2, value=1, layers=1,
                  first_dense=0, experts=experts, topk=topk, vocab=4, maxseq=1)
    result = []
    for index, seed in enumerate((17, 89, 203)):
        fixture = Fixture(shape, seed=seed)
        fixture.initial = {k: v for k, v in fixture.initial.items()
                           if k[0] == 15 and k[2] in (4, 5)}
        x = [Q16] + [0]*(hidden-1)
        for col, value in enumerate(x):
            fixture.initial[8, 0, 0, 8, col] = value
        for e in range(experts):
            if index == 0:
                score = 3*Q16 if e < min(experts, topk+2) else -Q16-e
            elif index == 1:
                score = -Q16*(experts-e)
            else:
                score = (e % 5-2)*32768
            for col in range(hidden):
                fixture.initial[15, 0, 4, e, col] = score if col == 0 else 0
        output = fixture.moe(0, x)
        routing = fixture.routing[0]
        expected_prefetch = [(e, row, col) for e in routing["winners"]
                             for row in range(min(8, tile_rows))
                             for col in range(min(hidden, tile_k))]
        expected_parameter_words = (topk+2)*(3*hidden*8+16+hidden)
        # This is the distinct-parameter lower bound, not a claim that
        # bounded ping-pong tiles never refetch other weights.
        result.append((fixture, dict(seed=seed, case=index, shape=vars(shape),
                                    input=x, routing=routing, output=output,
                                    prefetch=expected_prefetch,
                                    parameter_words=expected_parameter_words,
                                    dense_parameter_bytes=(experts+2)*(3*hidden*8+16+hidden)*4)))
    return result


def router_bench(evidence, experts=64, topk=6, hidden=16, tile_k=8, tile_rows=3):
    pairs = fixtures(experts, topk, hidden, tile_k, tile_rows)
    keys = sorted(set().union(*(set(f.initial) | set(f.writes) for f, _ in pairs)))
    starts, counts, expected = [], [], []
    for fixture, _ in pairs:
        for key in keys:
            starts.append(len(expected))
            counts.append(len(fixture.writes[key]))
            expected.extend(fixture.writes[key])
    image = evidence.path / "checkpoint-images"
    image.mkdir()
    hexfile(image / "keys.hex", [packed_key(k) for k in keys], 26)
    hexfile(image / "memory.hex", [f.initial.get(k, 0) & 0xffffffff for f, _ in pairs for k in keys], 8)
    hexfile(image / "initialized.hex", [int(k in f.initial) for f, _ in pairs for k in keys], 1)
    hexfile(image / "starts.hex", starts, 8)
    hexfile(image / "counts.hex", counts, 8)
    hexfile(image / "expected.hex", expected, 8)
    hexfile(image / "winners.hex", [e for _, t in pairs for e in t["routing"]["winners"]], 2)
    hexfile(image / "parameters.hex", [
        int(k[0] == 15 and k[2] == 5 and
            (k[3] >> 25) in t["routing"]["winners"]+[experts, experts+1])
        for _, t in pairs for k in keys], 1)
    (evidence.path / "router-fixtures.json").write_text(json.dumps([t for _, t in pairs], indent=2)+"\n")
    bench = BENCH
    for key, value in dict(SLOTS=len(keys), WRITES=len(expected), CASES=len(pairs),
                           EXPERTS=experts, TOPK=topk, HIDDEN=hidden, TILEK=tile_k,
                           TILEROWS=tile_rows).items():
        bench = bench.replace("@"+key+"@", str(value))
    (evidence.path / "router.sv").write_text(bench)
    return dict(cases=len(pairs), experts=experts, topk=topk,
                expected_writes=len(expected), compared_affinities=experts*len(pairs),
                compared_mixture_scalars=hidden*len(pairs),
                required_prefetch_beats=topk*min(8, tile_rows)*min(hidden, tile_k)*len(pairs))


BENCH = r"""
module tb;
  localparam B=2,SLOTS=@SLOTS@,WRITES=@WRITES@,CASES=@CASES@;
  localparam H=@HIDDEN@,NE=@EXPERTS@,NK=@TOPK@,TK=@TILEK@,TR=@TILEROWS@;
  localparam PW=(NK+2)*(3*H*8+16+H);
  localparam TW=(TR<8 ? TR : 8)*(TK<H ? TK : H);
  reg clk=0; always #5 clk=~clk;
  reg rst_n,flush=0,cmd_valid=0;
  wire cmd_ready,done,error;
  reg [31:0] cmd_epoch=0;
  wire [63:0] expert_dma_bytes,expert_dense_equiv_bytes,shared_busy_cycles,prefetch_busy_cycles,overlap_cycles;
  wire [1:0] c_req_valid,c_req_write,c_rsp_ready;
  wire [7:0] c_req_kind;
  wire [5:0] c_req_proj;
  wire [63:0] c_req_layer,c_req_row,c_req_col,c_req_wdata;
  reg [1:0] c_req_ready=0,c_rsp_valid=0,c_rsp_error=0;
  reg [63:0] c_rsp_rdata=0;
  anvil_d1_moe_router_dma #(.NUM_LAYERS(1),.HIDDEN_SIZE(H),.INTERMEDIATE_SIZE(8),
    .MOE_INTERMEDIATE_SIZE(8),.FIRST_DENSE_LAYERS(0),.ROUTED_EXPERTS(NE),.TOP_K(NK),
    .SHARED_EXPERTS(2),.MAX_SEQ_LEN(1),.TILE_K(TK),.TILE_ROWS(TR)) device (
    .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
    .cmd_epoch(cmd_epoch),.cmd_layer(32'd0),.cmd_pos(32'd0),.cmd_phase(1'b1),
    .done(done),.error(error),.expert_dma_bytes(expert_dma_bytes),
    .expert_dense_equiv_bytes(expert_dense_equiv_bytes),.shared_busy_cycles(shared_busy_cycles),
    .prefetch_busy_cycles(prefetch_busy_cycles),.overlap_cycles(overlap_cycles),
    .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),.c_req_write(c_req_write),
    .c_req_kind(c_req_kind),.c_req_layer(c_req_layer),.c_req_proj(c_req_proj),
    .c_req_row(c_req_row),.c_req_col(c_req_col),.c_req_wdata(c_req_wdata),
    .c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),.c_rsp_error(c_rsp_error),
    .c_rsp_rdata(c_rsp_rdata)
  );
  reg [102:0] keys[0:SLOTS-1];
  reg [31:0] memory[0:CASES*SLOTS-1],starts[0:CASES*SLOTS-1],counts[0:CASES*SLOTS-1];
  reg initialized[0:CASES*SLOTS-1];
  reg required_parameter[0:CASES*SLOTS-1];
  reg [31:0] expected[0:WRITES-1];
  reg [6:0] winners[0:CASES*NK-1];
  integer consumed[0:CASES*SLOTS-1];
  integer parameter_reads[0:CASES*SLOTS-1];
  integer prefetched[0:NE*TR*TK-1];
  integer affinity_reads[0:NE-1];
  integer expert_reads[0:NE+1];
  integer active=0,stimulus=0,cycles=0,reads=0,writes=0,completions=0,accepted=0;
  integer stalls=0,reset_samples=0,parameter_words=0,prefetch_words=0,simultaneous=0;
  integer mixtures=0,affinities=0,slot,index,expert,row,col,matrix,tile_index,winner_index;
  integer response_delay[0:1];
  reg [1:0] pending=0,pending_final=0,stalled=0;
  reg preedge_done=0;
  reg [63:0] response_data=0;
  reg [136:0] held[0:1];
  reg [319:0] saved_telemetry=0;
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
      if ({cmd_ready,done,error,expert_dma_bytes,expert_dense_equiv_bytes,
           shared_busy_cycles,prefetch_busy_cycles,overlap_cycles,
           c_req_valid,c_req_write,c_req_kind,c_req_layer,c_req_proj,c_req_row,
           c_req_col,c_req_wdata,c_rsp_ready} !== 0) $fatal(1,"ROUTER_RESET_XZ_OR_NONZERO");
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
    $readmemh("checkpoint-images/winners.hex",winners);
    $readmemh("checkpoint-images/parameters.hex",required_parameter);
    for (integer j=0;j<CASES*SLOTS;j=j+1) begin consumed[j]=0; parameter_reads[j]=0; end
    for (integer j=0;j<B;j=j+1) response_delay[j]=0;
`ifdef VERILATOR
    #1;
`else
    #0;
`endif
    reset_check(); repeat(2) @(negedge clk); #1; rst_n=1;
    for (stimulus=0;stimulus<CASES;stimulus=stimulus+1) begin
      @(negedge clk); while (cmd_ready!==1'b1) @(negedge clk);
      cmd_epoch=stimulus+1; cmd_valid=1;
      @(posedge clk);
      if (cmd_ready!==1'b1 || c_req_valid!==0) $fatal(1,"ROUTER_ACCEPTANCE");
      #1;
      if (cmd_ready!==0 || done!==0 || c_req_valid!==0) $fatal(1,"ROUTER_POST_ACCEPTANCE");
      @(negedge clk); cmd_valid=0;
      while (completions<=stimulus) @(negedge clk);
      repeat(3) @(negedge clk);
      if ({expert_dma_bytes,expert_dense_equiv_bytes,shared_busy_cycles,
           prefetch_busy_cycles,overlap_cycles} !== saved_telemetry)
        $fatal(1,"ROUTER_TELEMETRY_UNSTABLE");
    end
    for (integer j=0;j<CASES*SLOTS;j=j+1)
      if (consumed[j]!==counts[j]) $fatal(1,"ROUTER_MISSING_WRITE index=%0d",j);
    if (writes!=WRITES || mixtures!=CASES*H || affinities!=CASES*NE ||
        accepted!=CASES || completions!=CASES || stalls==0 || reset_samples<5 || simultaneous==0)
      $fatal(1,"ROUTER_MISSING_COMPARISONS");
    $display("SUMMARY router_cases=%0d experts=%0d topk=%0d writes=%0d reads=%0d mixtures=%0d affinities=%0d independent_client_transfers=%0d stalls=%0d reset=%0d cycles=%0d",
      CASES,NE,NK,writes,reads,mixtures,affinities,simultaneous,stalls,reset_samples,cycles);
    $finish;
  end
  always @(negedge clk) if (rst_n)
    for (integer bank=0;bank<B;bank=bank+1)
      c_req_ready[bank]=!pending[bank] && (cycles+bank)%7!=0;
  always @(posedge clk) if (rst_n) begin
    preedge_done=done; cycles=cycles+1;
    if (cycles>2000000) $fatal(1,"ROUTER_CYCLE_BOUND");
    if ((^{cmd_ready,done,error,c_req_valid,c_rsp_ready})===1'bx) $fatal(1,"ROUTER_CONTROL_XZ");
    if (cmd_valid && cmd_ready) begin
      active=stimulus; accepted=accepted+1; parameter_words=0; prefetch_words=0;
      for (integer j=0;j<NE*TR*TK;j=j+1) prefetched[j]=0;
      for (integer j=0;j<NE;j=j+1) affinity_reads[j]=0;
      for (integer j=0;j<NE+2;j=j+1) expert_reads[j]=0;
    end
    if ((c_req_valid & c_req_ready)==2'b11) simultaneous=simultaneous+1;
    for (integer bank=0;bank<B;bank=bank+1) begin
      if (stalled[bank] && {c_req_valid[bank],c_req_write[bank],c_req_kind[bank*4+:4],
          c_req_layer[bank*32+:32],c_req_proj[bank*3+:3],c_req_row[bank*32+:32],
          c_req_col[bank*32+:32],c_req_wdata[bank*32+:32]} !== held[bank])
        $fatal(1,"ROUTER_UNSTABLE_REQUEST");
      stalled[bank]=c_req_valid[bank] && !c_req_ready[bank];
      held[bank]={c_req_valid[bank],c_req_write[bank],c_req_kind[bank*4+:4],
        c_req_layer[bank*32+:32],c_req_proj[bank*3+:3],c_req_row[bank*32+:32],
        c_req_col[bank*32+:32],c_req_wdata[bank*32+:32]};
      if (stalled[bank]) stalls=stalls+1;
      if (pending[bank] && !c_rsp_valid[bank]) begin
        if (response_delay[bank]==0) begin
          c_rsp_valid[bank]<=1; c_rsp_rdata[bank*32+:32]<=response_data[bank*32+:32];
        end else response_delay[bank]=response_delay[bank]-1;
      end
      if (c_req_valid[bank] && c_req_ready[bank]) begin
        if (pending[bank] || (^{c_req_write[bank],c_req_kind[bank*4+:4],c_req_layer[bank*32+:32],
            c_req_proj[bank*3+:3],c_req_row[bank*32+:32],c_req_col[bank*32+:32],
            c_req_wdata[bank*32+:32]})===1'bx) $fatal(1,"ROUTER_REQUEST_XZ_OWNERSHIP");
        slot=lookup({c_req_kind[bank*4+:4],c_req_layer[bank*32+:32],c_req_proj[bank*3+:3],
                     c_req_row[bank*32+:32],c_req_col[bank*32+:32]});
        if (slot<0) $fatal(1,"ROUTER_UNMAPPED_MEMORY");
        index=active*SLOTS+slot; pending[bank]<=1; response_delay[bank]=(cycles+bank*3)%5;
        pending_final[bank]<=c_req_write[bank] && c_req_proj[bank*3+:3]==7 &&
          c_req_row[bank*32+:32]==4 && c_req_col[bank*32+:32]==H-1;
        if (c_req_write[bank]) begin
          if (bank!=0 || consumed[index]>=counts[index] ||
              c_req_wdata[bank*32+:32] !== expected[starts[index]+consumed[index]])
            $fatal(1,"ROUTER_NUMERICAL_WRITE_MISMATCH case=%0d row=%0d col=%0d occurrence=%0d actual=%h expected=%h",
              active,c_req_row[bank*32+:32],c_req_col[bank*32+:32],consumed[index],
              c_req_wdata[bank*32+:32],expected[starts[index]+consumed[index]]);
          consumed[index]=consumed[index]+1; writes=writes+1;
          memory[index]=c_req_wdata[bank*32+:32]; initialized[index]=1;
          response_data[bank*32+:32]<=0;
          if (c_req_proj[bank*3+:3]==7 && c_req_row[bank*32+:32]==4) mixtures=mixtures+1;
          if (c_req_proj[bank*3+:3]==7 && c_req_row[bank*32+:32]==8 && affinities<(active+1)*NE)
            affinities=affinities+1;
        end else begin
          if (initialized[index]!==1'b1) $fatal(1,"ROUTER_UNINITIALIZED_READ");
          response_data[bank*32+:32]<=memory[index]; reads=reads+1;
          if (c_req_proj[bank*3+:3]==4) affinity_reads[c_req_row[bank*32+:32]]=affinity_reads[c_req_row[bank*32+:32]]+1;
          if (c_req_proj[bank*3+:3]==5) begin
            expert=c_req_row[bank*32+25+:7]; matrix=c_req_row[bank*32+23+:2];
            row=c_req_row[bank*32+:23]; col=c_req_col[bank*32+:32];
            if (expert>=NE+2) $fatal(1,"ROUTER_BAD_EXPERT");
            winner_index=-1;
            for (integer j=0;j<NK;j=j+1)
              if (winners[active*NK+j]==expert) winner_index=j;
            if (expert<NE && winner_index<0) $fatal(1,"ROUTER_WRONG_WINNER expert=%0d",expert);
            parameter_words=parameter_words+1; expert_reads[expert]=expert_reads[expert]+1;
            parameter_reads[index]=parameter_reads[index]+1;
            if (bank==1) begin
              if (matrix!=0 || winner_index<0 || row>=TR || col>=TK || row>=8 || col>=H ||
                  winner_index!=prefetch_words/TW) $fatal(1,"ROUTER_PREFETCH_TILE_ORDER");
              tile_index=(expert*TR+row)*TK+col;
              if (prefetched[tile_index]!=0) $fatal(1,"ROUTER_DUPLICATE_PREFETCH");
              prefetched[tile_index]=1; prefetch_words=prefetch_words+1;
            end else if (expert<NE && matrix==0 && row<TR && col<TK)
              $fatal(1,"ROUTER_PREFETCH_REREAD expert=%0d row=%0d col=%0d",expert,row,col);
          end else if (bank==1) $fatal(1,"ROUTER_NONWEIGHT_PREFETCH");
        end
      end
      if (c_rsp_valid[bank] && c_rsp_ready[bank]) begin
        if (!pending[bank]) $fatal(1,"ROUTER_UNOWNED_RESPONSE");
        pending[bank]<=0; c_rsp_valid[bank]<=0;
        if (pending_final[bank]) begin
          #1;
          if (done!==1'b1 || error!==0 || cmd_ready!==0) $fatal(1,"ROUTER_FINAL_ACK_LATENCY");
        end
      end
    end
    if (preedge_done) begin
      if (error!==0 || pending || parameter_words<PW || prefetch_words!=NK*TW ||
          expert_dma_bytes!==64'(parameter_words*4) ||
          expert_dense_equiv_bytes!==64'((NE+2)*(3*H*8+16+H)*4) ||
          shared_busy_cycles==0 || prefetch_busy_cycles==0 || overlap_cycles==0 ||
          overlap_cycles>shared_busy_cycles || overlap_cycles>prefetch_busy_cycles)
        $fatal(1,"ROUTER_COMPLETION_TELEMETRY words=%0d expected=%0d prefetch=%0d overlap=%0d",
          parameter_words,PW,prefetch_words,overlap_cycles);
      for (integer j=0;j<NE;j=j+1)
        if (affinity_reads[j]!=H) $fatal(1,"ROUTER_AFFINITY_ROW_MISSING expert=%0d",j);
      for (integer j=0;j<NK;j=j+1)
        if (expert_reads[winners[active*NK+j]]<3*H*8+16+H) $fatal(1,"ROUTER_WINNER_WEIGHTS_MISSING");
      if (expert_reads[NE]<3*H*8+16+H || expert_reads[NE+1]<3*H*8+16+H)
        $fatal(1,"ROUTER_SHARED_WEIGHTS_MISSING");
      for (integer j=0;j<SLOTS;j=j+1)
        if ((parameter_reads[active*SLOTS+j]!=0) !== required_parameter[active*SLOTS+j])
          $fatal(1,"ROUTER_PARAMETER_COVERAGE case=%0d slot=%0d",active,j);
      saved_telemetry={expert_dma_bytes,expert_dense_equiv_bytes,shared_busy_cycles,prefetch_busy_cycles,overlap_cycles};
      completions=completions+1;
      $display("METRIC case=%0d expert_bytes=%0d dense_expert_bytes=%0d shared_cycles=%0d prefetch_cycles=%0d overlap_cycles=%0d",
        active,expert_dma_bytes,expert_dense_equiv_bytes,shared_busy_cycles,prefetch_busy_cycles,overlap_cycles);
      #1;
      if (done!==0 || cmd_ready!==1) $fatal(1,"ROUTER_COMPLETION_RETIREMENT");
    end
  end
endmodule
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim", choices=("icarus", "verilator"), default="verilator")
    parser.add_argument("--singleton", action="store_true")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    evidence = Evidence("router-"+args.sim+("-singleton" if args.singleton else "-64"), args.repair_of)
    try:
        geometry = dict(experts=1, topk=1, hidden=8, tile_k=8, tile_rows=1) if args.singleton else {}
        summary = router_bench(evidence, **geometry)
        summary["observations"] = simulate(evidence, "router.sv", args.sim)
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
