"""Reduced public-pin token failure/cancel/drain and numerical recovery tests.

The impulse/zero-matrix workload has an independently computed, nonzero final
logit. Fault injection uses memory responses, never forced internal state.
"""

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp_reference import convert, unit_impulse_norm
from retained import ROOT, Run, require_time_zero, with_time_zero_check
from simulation import compile_model, startup_check


SCENARIOS = (
    "cancel-held", "cancel-outstanding", "cancel-response", "cancel-projection",
    "cancel-cache-write", "cancel-stalled-logit", "response-error", "embedding-nan",
    "embedding-upper-bits", "scratch-nan", "scratch-overflow", "activation-overflow",
    "bias-nan", "rope-nan", "invalid-token",
)


BENCH = r"""
module tb;
  parameter BANKS=4,FORMAT=0,WEIGHTS=0,CACHE=0;
  integer SCENARIO=0;
  parameter NORM=32'h40ddb39f,LOGIT=32'h40de0000;
  reg clk=0,rst_n,cancel=0,token_valid=0,new_sequence=1;
  reg [31:0] token_id=0;
  always #5 clk=~clk;
  wire token_ready,logit_valid,done,error,cancel_done;
  wire [31:0] logit_index,logit_data;
  reg logit_ready=0;
  wire [BANKS-1:0] qv,qw,sr;
  reg [BANKS-1:0] qr=0,sv=0,se=0;
  wire [BANKS*4-1:0] qk;
  wire [BANKS*3-1:0] qp;
  wire [BANKS*32-1:0] ql,qrow,qcol,qd;
  wire [BANKS*64-1:0] qt;
  reg [BANKS*32-1:0] sd=0;
  reg [BANKS*64-1:0] st=0;
  reg [31:0] scratch[0:719],cache[0:95];
  reg scratch_valid[0:719],cache_valid[0:95];
  reg busy[0:BANKS-1],held[0:BANKS-1];
  reg [199:0] payload[0:BANKS-1];
  reg [31:0] pending_data[0:BANKS-1];
  reg [63:0] pending_tag[0:BANKS-1];
  reg pending_error[0:BANKS-1];
  integer due[0:BANKS-1],held_cycles[0:BANKS-1];
  integer i,b,kind,row,col,layer,proj,idx,logit_wait=0;
  integer epoch=0,cycle=0,requests=0,responses=0,accepts=0,logits=0,completions=0;
  integer trigger_cycle=-1,drain_waits=0,flush_handshakes=0,simultaneous_responses=0;
  reg triggered=0, first_completed=0,hold_cancel=0,pending_cancel=0;
  reg [15:0] one16;
  reg [31:0] response_value,expected_write;
  reg response_error;
  anvil_q2_fp_top #(
    .NUM_LAYERS(1),.HIDDEN_SIZE(48),.INTERMEDIATE_SIZE(48),
    .NUM_Q_HEADS(6),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(12),
    .VOCAB_SIZE(1),.MAX_SEQ_LEN(1),.BANKS(BANKS),.CACHE_BLOCK(2),
    .CACHE_MODE(CACHE),.FP_FORMAT(FORMAT),.WEIGHT_MODE(WEIGHTS)
  ) dut(clk,rst_n,cancel,token_valid,token_ready,token_id,32'd0,new_sequence,1'b0,
    logit_valid,logit_ready,logit_index,logit_data,done,error,cancel_done,
    qv,qr,qw,qk,ql,qp,qrow,qcol,qd,qt,sv,se,sr,sd,st);
  task automatic command;
    begin
      @(negedge clk); token_valid=1;
      do @(posedge clk); while(!token_ready);
      @(negedge clk); token_valid=0;
    end
  endtask
  initial begin
    rst_n=0;
    if(!$value$plusargs("SCENARIO=%d",SCENARIO)) $fatal(1,"MISSING_SCENARIO");
    one16=FORMAT==0 ? 16'h3f80 : 16'h3c00;
    for(i=0;i<720;i=i+1) begin scratch[i]=0; scratch_valid[i]=0; end
    for(i=0;i<96;i=i+1) begin cache[i]=0; cache_valid[i]=0; end
    for(i=0;i<BANKS;i=i+1) begin
      busy[i]=0; held[i]=0; payload[i]=0; due[i]=0; held_cycles[i]=0;
      pending_data[i]=0; pending_tag[i]=0; pending_error[i]=0;
    end
    #1;
    if({token_ready,logit_valid,logit_index,logit_data,done,error,cancel_done,
        qv,qw,qk,ql,qp,qrow,qcol,qd,qt,sr} !== 0) $fatal(1,"RESET_NONZERO_X");
    repeat(2) @(negedge clk); rst_n=1;
    if(SCENARIO==14) token_id=1;
    command();
    do @(posedge clk); while(!done);
    if(error !== 1'b1 || logits!=0 || requests!=responses ||
       cancel_done !== (SCENARIO<6) || (SCENARIO!=14 && !triggered))
      $fatal(1,"FIRST_ERROR_COMPLETION scenario=%0d error=%b logits=%0d req/rsp=%0d/%0d",
        SCENARIO,error,logits,requests,responses);
    first_completed=1;
    @(negedge clk);
    // A failed sequence may not resume without new_sequence.
    epoch=1; new_sequence=0; token_id=0;
    command();
    do @(posedge clk); while(!done);
    if(error !== 1'b1 || logits!=0 || cancel_done) $fatal(1,"FAILED_SEQUENCE_REUSED");
    @(negedge clk);
    // Keep old external scratch/cache words to expose stale-data mistakes.
    epoch=2; new_sequence=1;
    command();
    do @(posedge clk); while(!done);
    if(error !== 1'b0 || logits!=1 || requests!=responses || accepts!=3)
      $fatal(1,"RECOVERY_COMPLETION");
    #1;
    if(completions!=3) $fatal(1,"COMPLETION_COUNT");
    if(SCENARIO==0 && flush_handshakes==0) $fatal(1,"FLUSH_EDGE_HANDSHAKE_ABSENT");
    if(SCENARIO==2 && simultaneous_responses==0) $fatal(1,"CANCEL_RESPONSE_COINCIDENCE_ABSENT");
    if(SCENARIO<5 && drain_waits==0) $fatal(1,"NO_REAL_DRAIN_WAIT");
    $display("TOP_LIFECYCLE_COMPARED %0d %0d %0d %0d %0d %0d %0d",
      accepts,requests,responses,logits,drain_waits,flush_handshakes,simultaneous_responses);
    $finish;
  end
  always @(negedge clk) if(rst_n) begin
    if(hold_cancel) begin cancel=0; hold_cancel=0; end
    if(pending_cancel) begin
      cancel=1; hold_cancel=1; pending_cancel=0;
    end
    logit_ready=epoch==2 && cycle%7>1;
    if(epoch==0 && !triggered && SCENARIO==5 && logit_valid) begin
      logit_wait=logit_wait+1;
      if(logit_wait==5) begin cancel=1; hold_cancel=1; triggered=1; trigger_cycle=cycle; end
    end
    for(integer k=0;k<BANKS;k=k+1) begin
      qr[k]=!busy[k] && cycle%5>0;
      if(epoch==0 && !triggered && SCENARIO==0) begin
        qr[k]=0;
        if(qv[k]) held_cycles[k]=held_cycles[k]+1;
        if(held_cycles[k]==4) begin
          cancel=1; hold_cancel=1; qr[k]=1; triggered=1; trigger_cycle=cycle;
        end
      end
      if(epoch==0 && !triggered && SCENARIO==1 && busy[k]) begin
        cancel=1; hold_cancel=1; triggered=1; trigger_cycle=cycle;
      end
      if(busy[k] && !sv[k] && cycle>=due[k]) begin
        sv[k]=1; st[k*64+:64]=pending_tag[k];
        sd[k*32+:32]=pending_data[k]; se[k]=pending_error[k];
        if(epoch==0 && !triggered && SCENARIO==2) begin
          cancel=1; hold_cancel=1; triggered=1; trigger_cycle=cycle;
        end
      end
    end
  end
  always @(posedge clk or negedge clk)
    if(!rst_n && $time>0 &&
       {token_ready,logit_valid,logit_index,logit_data,done,error,cancel_done,
        qv,qw,qk,ql,qp,qrow,qcol,qd,qt,sr} !== 0) $fatal(1,"RESET_EDGE_NONZERO_X");
  always @(posedge clk) begin
    cycle<=cycle+1;
    if(rst_n) begin
      if((^{token_ready,logit_valid,done,error,cancel_done,qv,sr}) === 1'bx)
        $fatal(1,"ACTIVE_CONTROL_X");
      if(token_valid && token_ready) begin
        accepts=accepts+1;
        $display("COMMAND %0d %0d %0d",cycle,epoch,new_sequence);
      end
      if(epoch==1 && |qv) $fatal(1,"INVALID_SEQUENCE_ISSUED_MEMORY");
      if(triggered && !first_completed && requests!=responses) begin
        drain_waits=drain_waits+1;
        if(done || token_ready) $fatal(1,"TOKEN_COMPLETED_BEFORE_DRAIN");
      end
      if(logit_valid && logit_ready) begin
        if(epoch!=2 || logit_index !== 0 || logit_data !== LOGIT)
          $fatal(1,"RECOVERY_LOGIT_MISMATCH got=%08h expected=%08h",logit_data,LOGIT);
        logits=logits+1;
      end
      if(cancel && logit_valid) $fatal(1,"CANCELLED_LOGIT_VISIBLE");
      for(b=0;b<BANKS;b=b+1) begin
        if(held[b] && !cancel && (qv[b] !== 1'b1 ||
           {qw[b],qk[b*4+:4],ql[b*32+:32],qp[b*3+:3],qrow[b*32+:32],
            qcol[b*32+:32],qd[b*32+:32],qt[b*64+:64]} !== payload[b]))
          $fatal(1,"TOP_HELD_REQUEST_INSTABILITY");
        held[b]=qv[b] && !qr[b];
        payload[b]={qw[b],qk[b*4+:4],ql[b*32+:32],qp[b*3+:3],qrow[b*32+:32],
                    qcol[b*32+:32],qd[b*32+:32],qt[b*64+:64]};
        if(sv[b] && sr[b]) begin
          $display("RSP %0d %0d %016h %08h %0d",cycle,b,st[b*64+:64],sd[b*32+:32],se[b]);
          sv[b]<=0; busy[b]=0; responses=responses+1;
          if(cancel) simultaneous_responses=simultaneous_responses+1;
        end
        if(qv[b] && qr[b]) begin
          kind=qk[b*4+:4]; layer=ql[b*32+:32]; proj=qp[b*3+:3];
          row=qrow[b*32+:32]; col=qcol[b*32+:32];
          if((^{qw[b],qk[b*4+:4],ql[b*32+:32],qp[b*3+:3],qrow[b*32+:32],
                qcol[b*32+:32],qd[b*32+:32],qt[b*64+:64]}) === 1'bx)
            $fatal(1,"ACTIVE_MEMORY_X");
          if(((kind+layer+proj+row+col)&(BANKS-1))!=b || layer!=0)
            $fatal(1,"BAD_MEMORY_BANK_OR_LAYER");
          if(cancel) flush_handshakes=flush_handshakes+1;
          response_value=0; response_error=0;
          case(kind)
            0: begin
              if(qw[b] || proj!=0 || row!=0 || col>=48) $fatal(1,"BAD_EMBEDDING_ADDRESS");
              response_value=col==0 ? {16'd0,one16} : 0;
            end
            1,2,3,4: begin
              if(qw[b] || proj>6 || row>=48 || col>=48) $fatal(1,"BAD_PROJECTION_ADDRESS");
              if(kind==3) response_value={16'd0,one16};
            end
            5,6,7: begin
              if(qw[b] || proj!=0 || row!=0 || col>=48) $fatal(1,"BAD_NORM_ADDRESS");
              response_value={16'd0,one16};
            end
            8: begin
              if(proj!=0 || row>=15 || col>=48) $fatal(1,"BAD_SCRATCH_ADDRESS");
              idx=row*48+col;
              if(qw[b]) begin
                expected_write=col==0 && (row==1 || row==8 || row==14) ? NORM :
                               (col==0 && (row==0 || row==7) ? 32'h3f800000 : 0);
                if(qd[b*32+:32] !== expected_write)
                  $fatal(1,"RECOVERY_SCRATCH_MISMATCH row=%0d col=%0d got=%08h expected=%08h",
                    row,col,qd[b*32+:32],expected_write);
                scratch[idx]=qd[b*32+:32]; scratch_valid[idx]=1;
              end else begin
                if(!scratch_valid[idx]) $fatal(1,"UNINITIALIZED_SCRATCH");
                response_value=scratch[idx];
              end
            end
            9,10,12,13,14,15: begin
              if(proj!=0 || row!=0 || col>=8) $fatal(1,"BAD_CACHE_ADDRESS");
              if((CACHE==0 && kind>10) || (CACHE==1 && kind<12))
                $fatal(1,"WRONG_CACHE_MODE_TRAFFIC");
              idx=(kind-9)*8+col;
              if(qw[b]) begin
                if(qd[b*32+:32] !== 0) $fatal(1,"NONZERO_ZERO_FIXTURE_CACHE");
                cache[idx]=qd[b*32+:32]; cache_valid[idx]=1;
              end else begin
                if(!cache_valid[idx]) $fatal(1,"UNINITIALIZED_CACHE");
                response_value=cache[idx];
              end
            end
            11: begin
              if(qw[b] || proj!=0 || row!=0 || col>=8) $fatal(1,"BAD_ROPE_ADDRESS");
              response_value=col[0] ? 0 : 32'h3f800000;
            end
            default: $fatal(1,"BAD_MEMORY_KIND");
          endcase
          if(epoch==0 && !triggered) begin
            if((SCENARIO==3 && kind==1) ||
               (SCENARIO==4 && qw[b] && (kind==9 || kind==12))) begin
              // Trigger at the next inactive edge, while this accepted request
              // still needs its deliberately delayed response.
              triggered=1; trigger_cycle=cycle;
              pending_cancel=1;
            end
            if(!qw[b] && (
               (SCENARIO>=6 && SCENARIO<=8 && kind==0) ||
               (SCENARIO==9 && kind==8 && row==0) ||
               (SCENARIO==10 && kind==8 && row==0) ||
               (SCENARIO==11 && kind==8 && row==1) ||
               (SCENARIO==12 && kind==4) ||
               (SCENARIO==13 && kind==11))) begin
              triggered=1; trigger_cycle=cycle;
              if(SCENARIO==6) response_error=1;
              else if(SCENARIO==8) response_value=32'h00010000|response_value;
              else if(SCENARIO==10 || SCENARIO==11) response_value=32'h7f7fffff;
              else if(SCENARIO==9) response_value=32'h7fc00000;
              else if(SCENARIO==13) response_value=32'h7fc00000;
              else response_value=FORMAT==0 ? 32'h00007fc0 : 32'h00007e00;
            end
          end
          pending_data[b]=response_value; pending_error[b]=response_error;
          pending_tag[b]=qt[b*64+:64]; busy[b]=1; due[b]=cycle+12;
          $display("REQ %0d %0d %0d %0d %0d %0d %0d %0d %08h %016h",
            cycle,b,qw[b],kind,layer,proj,row,col,qd[b*32+:32],qt[b*64+:64]);
          requests=requests+1;
        end
      end
      if(done) completions=completions+1;
    end
  end
endmodule
"""


def execute(case, fmt, weights, cache, banks):
    run = Run(f"verifier-top-{case}-{fmt}-w{weights}-c{cache}-b{banks}")
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        norm = unit_impulse_norm(48)
        logit = convert(convert(norm, "fp32", fmt), fmt)
        parameters = dict(
            BANKS=banks, FORMAT=int(fmt == "fp16"), WEIGHTS=weights, CACHE=cache,
            NORM=f"32'h{norm:08x}", LOGIT=f"32'h{logit:08x}")
        bench = run.path / "bench.sv"
        bench.write_text(with_time_zero_check(BENCH))
        run.receipt["generated_sha256"] = {
            run.relative(bench): hashlib.sha256(bench.read_bytes()).hexdigest()}
        run.receipt["scenario"] = dict(case=case, format=fmt, weights=weights, cache=cache, banks=banks)
        binary = compile_model(run, bench, sorted((ROOT / "rtl").glob("*.sv")), parameters)
        arguments = [f"+SCENARIO={SCENARIOS.index(case)}"]
        startup_check(run, binary, arguments)
        trace = run.command([run.relative(binary), *arguments], "simulation")
        summaries = [line.split()[1:] for line in trace.read_text().splitlines()
                     if line.startswith("TOP_LIFECYCLE_COMPARED ")]
        assert len(summaries) == 1, "top lifecycle comparisons absent"
        metrics = dict(zip(("commands", "requests", "responses", "recovery_logits", "drain_waits",
                            "flush_handshakes", "simultaneous_responses"), map(int, summaries[0])))
        assert metrics["commands"] == 3 and metrics["recovery_logits"] == 1
        assert metrics["requests"] == metrics["responses"] > 0
        run.finish("passed-focused-only", metrics=metrics)
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=SCENARIOS, required=True)
    parser.add_argument("--format", choices=("bf16", "fp16"), default="bf16")
    parser.add_argument("--weights", type=int, choices=(0, 1), default=0)
    parser.add_argument("--cache", type=int, choices=(0, 1), default=0)
    parser.add_argument("--banks", type=int, choices=(1, 2, 4), default=4)
    args = parser.parse_args()
    raise SystemExit(execute(args.case, args.format, args.weights, args.cache, args.banks))
