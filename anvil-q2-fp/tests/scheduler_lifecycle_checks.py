"""Public-pin scheduler flush, malformed response, reset and recovery checks."""

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run, require_time_zero, with_time_zero_check


BENCH = r"""
module tb;
  parameter BANKS=4,DEPTH=3;
  reg clk=0,rst_n,flush=0,cv=0;
  always #5 clk=~clk;
  wire idle,drain_done,fault,cr,crv,cre;
  wire [31:0] crd;
  reg [31:0] col=0,data=0;
  wire [BANKS-1:0] mv,mw,mrr;
  reg [BANKS-1:0] mr=0,mrv=0,mre=0;
  wire [BANKS*4-1:0] mk;
  wire [BANKS*3-1:0] mp;
  wire [BANKS*32-1:0] ml,mrow,mcol,md;
  wire [BANKS*64-1:0] mt;
  reg [BANKS*32-1:0] mrd=0;
  reg [BANKS*64-1:0] mrt=0;
  reg allow_retire=0,allow_fault=0;
  reg [63:0] tag0,tag1,last_tag=0;
  integer accepted=0,dispatched=0,returned=0,retired=0,abandoned=0;
  integer faults=0,drains=0,coincidences=0,resets=0,cycle=0,phase=0;
  integer i;
  anvil_q2_bank_scheduler #(BANKS,1,DEPTH) dut(
    clk,rst_n,flush,idle,drain_done,fault,cv,cr,1'b0,4'd0,32'd0,3'd0,
    32'd0,col,data,crv,1'b1,crd,cre,mv,mr,mw,mk,ml,mp,mrow,mcol,md,mt,
    mrv,mre,mrr,mrd,mrt);
  task automatic submit(input integer bank_number,input [31:0] payload);
    begin
      @(negedge clk); col=bank_number; data=payload; cv=1;
      do @(posedge clk); while(!cr);
      @(negedge clk); cv=0;
    end
  endtask
  task automatic dispatch(input integer bank_number,input [31:0] payload,
                          output [63:0] captured_tag);
    begin
      do @(negedge clk); while(!mv[bank_number]);
      if({mw[bank_number],mk[bank_number*4+:4],ml[bank_number*32+:32],
          mp[bank_number*3+:3],mrow[bank_number*32+:32],mcol[bank_number*32+:32],
          md[bank_number*32+:32]} !== {1'b0,4'd0,32'd0,3'd0,32'd0,32'(bank_number),payload})
        $fatal(1,"SCHEDULER_DISPATCH_PAYLOAD");
      captured_tag=mt[bank_number*64+:64];
      mr[bank_number]=1;
      @(posedge clk);
      if(mv[bank_number] !== 1'b1) $fatal(1,"DISPATCH_NOT_ACCEPTED");
      @(negedge clk); mr[bank_number]=0;
    end
  endtask
  task automatic respond(input integer bank_number,input [63:0] tag_value,
                         input [31:0] response_value);
    begin
      @(negedge clk);
      mrv[bank_number]=1; mrt[bank_number*64+:64]=tag_value;
      mrd[bank_number*32+:32]=response_value;
      @(posedge clk);
      if(mrr[bank_number] !== 1'b1) $fatal(1,"RESPONSE_NOT_ACCEPTED");
      @(negedge clk); mrv[bank_number]=0;
    end
  endtask
  task automatic drained;
    integer old_drains;
    begin
      old_drains=drains;
      if(!drain_done) do @(negedge clk); while(!drain_done);
      if(crv !== 1'b0 || mv !== 0) $fatal(1,"DRAIN_LEAKED_TRANSACTION");
      @(negedge clk);
      if(idle !== 1'b1 || drains<=old_drains) $fatal(1,"DRAIN_DID_NOT_RECOVER");
    end
  endtask
  task automatic normal(input integer bank_number,input [31:0] payload);
    begin
      submit(bank_number,payload);
      dispatch(bank_number,payload,tag1);
      if(tag1<=last_tag) $fatal(1,"TAG_REUSE_AFTER_DRAIN");
      last_tag=tag1;
      allow_retire=1;
      respond(bank_number,tag1,payload^32'h5a3ca5c3);
      do @(negedge clk); while(!idle);
      allow_retire=0;
      if(crd !== 0) $fatal(1,"INACTIVE_RESPONSE_PAYLOAD");
    end
  endtask
  initial begin
    rst_n=0;
    #1;
    if({idle,drain_done,fault,cr,crv,crd,cre,mv,mw,mk,ml,mp,mrow,mcol,md,mt,mrr} !== 0)
      $fatal(1,"RESET_NONZERO_X");
    repeat(2) @(negedge clk); rst_n=1;

    // Flush preserves a transfer accepted on its edge, and consumes a response
    // on that same edge when two reservations are possible.
    phase=1;
    if(DEPTH>1) begin
      submit(0,32'h101);
      dispatch(0,32'h101,tag0);
    end
    submit(0,32'h202);
    do @(negedge clk); while(!mv[0]);
    tag1=mt[0+:64]; last_tag=tag1;
    repeat(3) begin
      @(posedge clk);
      if(mv[0] !== 1'b1 || mt[0+:64] !== tag1 || md[0+:32] !== 32'h202)
        $fatal(1,"PRE_FLUSH_HELD_REQUEST");
      @(negedge clk);
    end
    flush=1; mr[0]=1;
    if(DEPTH>1) begin mrv[0]=1; mrt[0+:64]=tag0; mrd[0+:32]=32'h5a3ca4c2; end
    @(posedge clk);
    if(!(flush && mv[0] && mr[0]) || (DEPTH>1 && !(mrv[0] && mrr[0])))
      $fatal(1,"FLUSH_COINCIDENCE_NOT_OBSERVED");
    coincidences=coincidences+1;
    @(negedge clk); flush=0; mr=0; mrv=0;
    repeat(4) begin
      @(negedge clk);
      if(drain_done || idle || crv || mv) $fatal(1,"PREMATURE_DRAIN_COMPLETION");
    end
    respond(0,tag1,32'h5a3ca7c1);
    drained();
    normal(BANKS-1,32'h303);

    // An unknown response coincides with an otherwise valid held transfer.
    phase=2;
    submit(0,32'h404);
    do @(negedge clk); while(!mv[0]);
    tag0=mt[0+:64]; last_tag=tag0;
    allow_fault=1; mr[0]=1; mrv[0]=1;
    mrt[0+:64]=64'hfedcba9876543210; mrd[0+:32]=32'hbadbad00;
    @(posedge clk);
    if(!(mv[0] && mr[0] && mrv[0] && mrr[0])) $fatal(1,"FAULT_COINCIDENCE_ABSENT");
    coincidences=coincidences+1;
    @(negedge clk); mr=0; mrv=0;
    if(fault !== 1'b1) $fatal(1,"UNKNOWN_TAG_NOT_FAULTED");
    repeat(3) @(negedge clk);
    respond(0,tag0,32'h5a3ca1c7);
    drained(); allow_fault=0;
    normal(0,32'h505);

    // A duplicate response cannot complete another reservation.
    phase=3; allow_fault=1;
    respond(0,last_tag,32'h5a3ca0c6);
    if(fault !== 1'b1) $fatal(1,"DUPLICATE_TAG_NOT_FAULTED");
    drained(); allow_fault=0;
    normal(0,32'h606);

    if(BANKS>1) begin
      phase=4;
      submit(0,32'h707);
      dispatch(0,32'h707,tag0); last_tag=tag0; allow_fault=1;
      respond(BANKS-1,tag0,32'h5a3ca2c4);
      if(fault !== 1'b1) $fatal(1,"WRONG_BANK_NOT_FAULTED");
      respond(0,tag0,32'h5a3ca2c4);
      drained(); allow_fault=0;
      normal(BANKS-1,32'h808);
    end

    // Asynchronous reset abandons a real dispatched request. Epoch-zero
    // traffic is not relabelled as a new command after reset.
    phase=5;
    submit(0,32'h909);
    dispatch(0,32'h909,tag0);
    @(negedge clk); #1; rst_n=0; resets=resets+1; abandoned=abandoned+1;
    #1;
    if({idle,drain_done,fault,cr,crv,crd,cre,mv,mw,mk,ml,mp,mrow,mcol,md,mt,mrr} !== 0)
      $fatal(1,"MIDSTREAM_ASYNC_RESET_NONZERO_X");
    repeat(2) @(negedge clk); rst_n=1;
    allow_fault=1;
    respond(0,tag0,32'h5a3cacc6);
    if(fault !== 1'b1) $fatal(1,"LATE_RESET_RESPONSE_NOT_FAULTED");
    drained(); allow_fault=0;
    // Allocation restarts only at reset, not at flush/fault.
    submit(0,32'ha0a);
    dispatch(0,32'ha0a,tag1);
    if(tag1 !== 0) $fatal(1,"RESET_TAG_ORIGIN");
    allow_retire=1;
    respond(0,tag1,32'h5a3cafc9);
    do @(negedge clk); while(!idle);
    allow_retire=0;
    if(faults!=(BANKS>1 ? 4 : 3) || drains!=(BANKS>1 ? 5 : 4) ||
       coincidences!=2 || resets!=1 || dispatched!=returned+abandoned-(
         BANKS>1 ? 4 : 3) || retired!=(BANKS>1 ? 5 : 4))
      $fatal(1,"LIFECYCLE_ACCOUNTING got=%0d/%0d/%0d/%0d/%0d",
        dispatched,returned,retired,faults,drains);
    $display("SCHEDULER_LIFECYCLE_COMPARED %0d %0d %0d %0d %0d %0d %0d %0d",
      accepted,dispatched,returned,retired,faults,drains,coincidences,resets);
    $finish;
  end
  always @(posedge clk or negedge clk)
    if(!rst_n && $time>0 &&
       {idle,drain_done,fault,cr,crv,crd,cre,mv,mw,mk,ml,mp,mrow,mcol,md,mt,mrr} !== 0)
      $fatal(1,"RESET_EDGE_NONZERO_X");
  always @(posedge clk) begin
    cycle<=cycle+1;
    if(cycle>10000) $fatal(1,"LIFECYCLE_BOUNDED_PROTOCOL_DEADLOCK");
    if(rst_n) begin
      if((^{idle,drain_done,fault,cr,crv,mv,mrr}) === 1'bx)
        $fatal(1,"LIFECYCLE_CONTROL_X");
      if(fault && !allow_fault) $fatal(1,"UNEXPECTED_LIFECYCLE_FAULT");
      if(fault) faults=faults+1;
      if(drain_done) drains=drains+1;
      if(cv && cr) accepted=accepted+1;
      for(i=0;i<BANKS;i=i+1) begin
        if(mv[i] && mr[i]) dispatched=dispatched+1;
        if(mrv[i] && mrr[i]) returned=returned+1;
      end
      if(crv) begin
        if(!allow_retire || cre !== 1'b0 || crd !== (data^32'h5a3ca5c3))
          $fatal(1,"STALE_OR_CORRUPT_CLIENT_RESPONSE phase=%0d got=%08h",phase,crd);
        retired=retired+1;
      end
    end
  end
endmodule
"""


def execute(banks, depth):
    run = Run(f"verifier-scheduler-lifecycle-b{banks}-q{depth}")
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        bench = run.path / "bench.sv"
        bench.write_text(with_time_zero_check(BENCH))
        run.receipt["generated_sha256"] = {
            run.relative(bench): hashlib.sha256(bench.read_bytes()).hexdigest()}
        binary = run.path / "bench.vvp"
        run.command(["iverilog", "-g2012", "-Wall", "-s", "tb", f"-Ptb.BANKS={banks}",
                     f"-Ptb.DEPTH={depth}", "-o", run.relative(binary),
                     "rtl/anvil_q2_bank_scheduler.sv", run.relative(bench)], "compile")
        trace = run.command(["vvp", run.relative(binary)], "simulation")
        require_time_zero(trace)
        summaries = [line.split()[1:] for line in trace.read_text().splitlines()
                     if line.startswith("SCHEDULER_LIFECYCLE_COMPARED ")]
        assert len(summaries) == 1, "scheduler lifecycle comparisons absent"
        metrics = dict(zip(("accepted", "dispatched", "returned", "retired", "faults",
                            "drains", "coincident_edges", "reset_with_outstanding"),
                           map(int, summaries[0])))
        run.finish("passed-focused-only", metrics=metrics,
                   limitations="Tag exhaustion needs a separate bounded proof; no physical timing claim.")
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--banks", type=int, choices=(1, 2, 4), default=4)
    parser.add_argument("--depth", type=int, choices=(1, 3, 16), default=3)
    args = parser.parse_args()
    raise SystemExit(execute(args.banks, args.depth))
