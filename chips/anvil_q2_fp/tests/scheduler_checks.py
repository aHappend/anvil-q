"""Public-transaction queued scheduler oracle, independent of slot implementation.

Directed stalls fill the queue, then highest-tag-first bank responses exercise
per-client in-order retirement. Response errors are ordinary tagged completions.
Flush/reset-epoch and malformed-tag campaigns remain separate coverage.
"""

import argparse
from collections import Counter, defaultdict, deque
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import Run, require_time_zero, with_time_zero_check


BENCH = r"""
module tb;
  parameter BANKS=4,DEPTH=3,CLIENTS=3,COUNT=64,SEED=17;
  localparam TOTAL=CLIENTS*COUNT;
  reg clk=0,rst_n;
  always #5 clk=~clk;
  wire idle,drain_done,fault;
  reg [CLIENTS-1:0] cv=0,cw=0,crr=0;
  wire [CLIENTS-1:0] cr,crv,cre;
  reg [CLIENTS*4-1:0] ck=0;
  reg [CLIENTS*3-1:0] cp=0;
  reg [CLIENTS*32-1:0] cl=0,crow=0,ccol=0,cd=0;
  wire [CLIENTS*32-1:0] crd;
  wire [BANKS-1:0] mv,mw,mrr;
  reg [BANKS-1:0] mr=0,mrv=0,mre=0;
  wire [BANKS*4-1:0] mk;
  wire [BANKS*3-1:0] mp;
  wire [BANKS*32-1:0] ml,mrow,mcol,md;
  wire [BANKS*64-1:0] mt;
  reg [BANKS*32-1:0] mrd=0;
  reg [BANKS*64-1:0] mrt=0;
  integer index[0:CLIENTS-1];
  integer active[0:TOTAL-1],which_bank[0:TOTAL-1],due[0:TOTAL-1];
  reg [31:0] response[0:TOTAL-1];
  reg response_error[0:TOTAL-1];
  reg held_client[0:CLIENTS-1],held_memory[0:BANKS-1];
  reg [32:0] client_payload[0:CLIENTS-1];
  reg [199:0] memory_payload[0:BANKS-1];
  integer cycle=0,accepted=0,dispatched=0,returned=0,retired=0;
  integer contention=0,request_stalls=0,result_stalls=0,reverse_pairs=0;
  integer chosen,tag_number,available,c,b,s,done_count=0;
  anvil_q2_bank_scheduler #(BANKS,CLIENTS,DEPTH) dut(
    clk,rst_n,1'b0,idle,drain_done,fault,cv,cr,cw,ck,cl,cp,crow,ccol,cd,
    crv,crr,crd,cre,mv,mr,mw,mk,ml,mp,mrow,mcol,md,mt,mrv,mre,mrr,mrd,mrt);
  initial begin
    rst_n=0;
    for(c=0;c<CLIENTS;c=c+1) begin
      index[c]=0; held_client[c]=0; client_payload[c]=0;
    end
    for(b=0;b<BANKS;b=b+1) begin held_memory[b]=0; memory_payload[b]=0; end
    for(s=0;s<TOTAL;s=s+1) begin
      active[s]=0; which_bank[s]=0; due[s]=0; response[s]=0; response_error[s]=0;
    end
    #1;
    if({idle,drain_done,fault,cr,crv,crd,cre,mv,mw,mk,ml,mp,mrow,mcol,md,mt,mrr} !== 0) begin
      $display("RESET_OBSERVED idle=%b drain_done=%b fault=%b c_req_ready=%h c_rsp_valid=%h mem_req_valid=%h mem_rsp_ready=%h",
        idle,drain_done,fault,cr,crv,mv,mrr);
      $fatal(1,"RESET_NONZERO_X");
    end
    repeat(2) @(negedge clk);
    rst_n=1;
  end
  always @(negedge clk) begin
    if(rst_n) begin
      for(integer j=0;j<CLIENTS;j=j+1) begin
        cv[j]=index[j]<COUNT && (j==0 || cycle>25);
        cw[j]=index[j][0];
        ck[j*4+:4]=1;
        cp[j*3+:3]=j;
        cl[j*32+:32]=0;
        crow[j*32+:32]=j;
        ccol[j*32+:32]=index[j]<8 ? index[j]*BANKS : index[j];
        cd[j*32+:32]=(j<<24)|index[j];
        crr[j]=cycle>120 && ((cycle+3*j+SEED)%11)>2;
      end
      for(integer k=0;k<BANKS;k=k+1) begin
        mr[k]=cycle>30 && ((cycle+k*5+SEED)%9)>2;
        if(!mrv[k] && cycle>80) begin
          chosen=-1; available=0;
          for(integer n=0;n<TOTAL;n=n+1)
            if(active[n]==1 && which_bank[n]==k && due[n]<=cycle) begin
              chosen=n; available=available+1;
            end
          if(chosen>=0) begin
            if(available>1) reverse_pairs=reverse_pairs+1;
            active[chosen]=2;
            mrv[k]=1; mrt[k*64+:64]=chosen;
            mrd[k*32+:32]=response[chosen]; mre[k]=response_error[chosen];
          end
        end
      end
    end
  end
  always @(posedge clk or negedge clk)
    if(!rst_n && $time>0 &&
       {idle,drain_done,fault,cr,crv,crd,cre,mv,mw,mk,ml,mp,mrow,mcol,md,mt,mrr} !== 0)
      $fatal(1,"RESET_EDGE_NONZERO_X");
  always @(posedge clk) begin
    cycle<=cycle+1;
    if(rst_n) begin
      if((^{idle,drain_done,fault,cr,crv,mv,mrr}) === 1'bx) $fatal(1,"ACTIVE_CONTROL_X");
      if(fault || drain_done) $fatal(1,"UNEXPECTED_SCHEDULER_FAULT_OR_DRAIN");
      if($countones(cv)>1) contention=contention+1;
      if($countones(cr)>1) $fatal(1,"MULTIPLE_INGRESS_ACCEPTS");
      for(c=0;c<CLIENTS;c=c+1) begin
        if(held_client[c] && (crv[c] !== 1'b1 ||
            {cre[c],crd[c*32+:32]} !== client_payload[c]))
          $fatal(1,"CLIENT_RESPONSE_INSTABILITY");
        held_client[c]=crv[c] && !crr[c]; client_payload[c]={cre[c],crd[c*32+:32]};
        if(crv[c] && !crr[c]) result_stalls=result_stalls+1;
        if(cv[c] && cr[c]) begin
          $display("CLIENT %0d %0d %0d %0d %0d %0d %0d %0d %08h",
            cycle,c,cw[c],ck[c*4+:4],cl[c*32+:32],cp[c*3+:3],
            crow[c*32+:32],ccol[c*32+:32],cd[c*32+:32]);
          index[c]=index[c]+1; accepted=accepted+1;
        end
        if(crv[c] && crr[c]) begin
          if((^{cre[c],crd[c*32+:32]}) === 1'bx) $fatal(1,"CLIENT_RESPONSE_X");
          $display("RETIRE %0d %0d %08h %0d",cycle,c,crd[c*32+:32],cre[c]);
          retired=retired+1;
        end
      end
      for(b=0;b<BANKS;b=b+1) begin
        if(held_memory[b] && (mv[b] !== 1'b1 ||
            {mw[b],mk[b*4+:4],ml[b*32+:32],mp[b*3+:3],mrow[b*32+:32],
             mcol[b*32+:32],md[b*32+:32],mt[b*64+:64]} !== memory_payload[b]))
          $fatal(1,"HELD_REQUEST_INSTABILITY");
        held_memory[b]=mv[b] && !mr[b];
        memory_payload[b]={mw[b],mk[b*4+:4],ml[b*32+:32],mp[b*3+:3],
          mrow[b*32+:32],mcol[b*32+:32],md[b*32+:32],mt[b*64+:64]};
        if(mv[b] && !mr[b]) request_stalls=request_stalls+1;
        if(mrv[b] && mrr[b]) begin
          $display("RETURN %0d %0d %016h %08h %0d",cycle,b,mrt[b*64+:64],
                   mrd[b*32+:32],mre[b]);
          active[mrt[b*64+:64]]=0; mrv[b]<=0; returned=returned+1;
        end
        if(mv[b] && mr[b]) begin
          if((^{mw[b],mk[b*4+:4],ml[b*32+:32],mp[b*3+:3],mrow[b*32+:32],
                mcol[b*32+:32],md[b*32+:32],mt[b*64+:64]}) === 1'bx)
            $fatal(1,"MEMORY_REQUEST_X");
          if(mt[b*64+:64]>=TOTAL) $fatal(1,"UNEXPECTED_TAG_RANGE");
          tag_number=mt[b*64+:64];
          if(active[tag_number]!=0) $fatal(1,"TAG_REUSE");
          $display("MEMORY %0d %0d %0d %0d %0d %0d %0d %0d %08h %016h",
            cycle,b,mw[b],mk[b*4+:4],ml[b*32+:32],mp[b*3+:3],
            mrow[b*32+:32],mcol[b*32+:32],md[b*32+:32],mt[b*64+:64]);
          response[tag_number]=md[b*32+:32]^32'ha5c35a3c;
          response_error[tag_number]=(tag_number%11)==3;
          which_bank[tag_number]=b; due[tag_number]=cycle+24;
          active[tag_number]=1; dispatched=dispatched+1;
        end
      end
      if(retired==TOTAL && idle) begin
        if(accepted!=TOTAL || dispatched!=TOTAL || returned!=TOTAL ||
           contention==0 || request_stalls==0 || result_stalls==0)
          $fatal(1,"SCHEDULER_ACCOUNTING_OR_COVERAGE");
        if(DEPTH>1 && reverse_pairs==0) $fatal(1,"NO_REVERSE_COMPLETION");
        $display("SCHEDULER_COMPARED %0d %0d %0d %0d %0d %0d %0d",
          accepted,dispatched,returned,retired,request_stalls,result_stalls,reverse_pairs);
        $finish;
      end
    end
  end
endmodule
"""


def compare(trace, banks, clients=3, count=64):
    issued = {}
    dispatched = set()
    returned = set()
    retired = set()
    queues = defaultdict(deque)
    client_counts = Counter()
    summaries = []
    responses_out_of_order = 0
    for line in trace.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "CLIENT":
            _, cycle, client, write, kind, layer, proj, row, col, data = parts
            client = int(client)
            payload = tuple(map(int, (write, kind, layer, proj, row, col))) + (int(data, 16),)
            tag = len(issued)
            issued[tag] = (client, payload)
            queues[client].append(tag)
            client_counts[client] += 1
        elif parts[0] == "MEMORY":
            _, cycle, bank, write, kind, layer, proj, row, col, data, tag = parts
            bank, tag = int(bank), int(tag, 16)
            payload = tuple(map(int, (write, kind, layer, proj, row, col))) + (int(data, 16),)
            assert tag in issued and tag not in dispatched, "scheduler tag allocation/reuse"
            assert payload == issued[tag][1], "scheduler tag/payload association"
            assert sum(payload[1:6]) & (banks - 1) == bank, "scheduler bank selection"
            dispatched.add(tag)
        elif parts[0] == "RETURN":
            _, cycle, bank, tag, data, error = parts
            tag = int(tag, 16)
            assert tag in dispatched and tag not in returned, "invalid/duplicate memory response"
            expected = issued[tag][1][-1] ^ 0xA5C35A3C
            assert int(data, 16) == expected and int(error) == int(tag % 11 == 3)
            if any(t < tag for t in dispatched - returned):
                responses_out_of_order += 1
            returned.add(tag)
        elif parts[0] == "RETIRE":
            _, cycle, client, data, error = parts
            client = int(client)
            assert queues[client], "uncommanded scheduler completion"
            tag = queues[client].popleft()
            assert tag in returned and tag not in retired, "early/duplicate scheduler completion"
            assert (int(data, 16), int(error)) == (
                issued[tag][1][-1] ^ 0xA5C35A3C, int(tag % 11 == 3)), (
                    f"SCHEDULER_RESPONSE_MISMATCH client={client} tag={tag} "
                    f"observed={data}/{error}")
            retired.add(tag)
        elif parts[0] == "SCHEDULER_COMPARED":
            summaries.append(list(map(int, parts[1:])))
    total = clients * count
    assert len(issued) == len(dispatched) == len(returned) == len(retired) == total
    assert all(not queue for queue in queues.values()), "unretired client traffic"
    assert client_counts == Counter({client: count for client in range(clients)})
    assert len(summaries) == 1 and summaries[0][:4] == [total] * 4
    return {"client_requests_compared": total, "memory_requests_compared": total,
            "responses_compared": total, "per_client_ordered_completions": total,
            "out_of_order_bank_responses": responses_out_of_order,
            "request_stall_cycles": summaries[0][4], "result_stall_cycles": summaries[0][5],
            "limitations": "No flush, tag exhaustion, reset-epoch or malformed-tag claim."}


def execute(banks, depth, seed, repair_of=None):
    run = Run(f"verifier-scheduler-b{banks}-q{depth}-s{seed}")
    if repair_of:
        run.receipt["repair_of"] = repair_of
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        bench = run.path / "bench.sv"
        bench.write_text(with_time_zero_check(BENCH))
        run.receipt["generated_sha256"] = {
            run.relative(bench): hashlib.sha256(bench.read_bytes()).hexdigest()}
        binary = run.path / "bench.vvp"
        run.command(["iverilog", "-g2012", "-Wall", "-s", "tb",
                     f"-Ptb.BANKS={banks}", f"-Ptb.DEPTH={depth}", f"-Ptb.SEED={seed}",
                     "-o", run.relative(binary), "rtl/anvil_q2_bank_scheduler.sv",
                     run.relative(bench)], "compile")
        trace = run.command(["vvp", run.relative(binary)], "simulation")
        require_time_zero(trace)
        metrics = compare(trace, banks)
        if depth > 1:
            assert metrics["out_of_order_bank_responses"] > 0
        run.finish("passed-focused-only", metrics=metrics)
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--banks", type=int, choices=(1, 2, 4), default=4)
    parser.add_argument("--depth", type=int, choices=(1, 3, 16), default=3)
    parser.add_argument("--seed", type=int, choices=(17, 43, 89), default=17)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    raise SystemExit(execute(args.banks, args.depth, args.seed, args.repair_of))
