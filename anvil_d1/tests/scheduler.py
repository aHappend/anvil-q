"""Public-pin bank/tag ownership and deliberately reordered response scoreboard.

Tags are opaque, captured from accepted memory requests and echoed unchanged.
The oracle is per-client accepted transaction FIFO, never scheduler pointers,
tag decoding or FSM equations. A finite service hold fills actual ownership,
then newest accepted requests return first across all banks. Singleton ordering
is covered by a separate non-singleton mandatory case.
"""

from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))


def scheduler_bench(evidence, banks=2, queue=3):
    bench = BENCH.replace("@BANKS@", str(banks)).replace("@QUEUE@", str(queue))
    (evidence.path/"scheduler.sv").write_text(bench)
    return dict(banks=banks, queue=queue, clients=5, transactions=40,
                require_reordering=banks*queue > 1, finite_service_hold_cycles=100)


BENCH = r"""
module tb;
  localparam B=@BANKS@,Q=@QUEUE@,C=5,N=8,T=C*N;
  reg clk=0; always #5 clk=~clk;
  reg rst_n,flush=0;
  wire idle,drain_done,fault;
  reg [C-1:0] c_req_valid=0,c_req_write=0,c_rsp_ready=0;
  wire [C-1:0] c_req_ready,c_rsp_valid,c_rsp_error;
  reg [C*4-1:0] c_req_kind=0;
  reg [C*3-1:0] c_req_proj=0;
  reg [C*32-1:0] c_req_layer=0,c_req_row=0,c_req_col=0,c_req_wdata=0;
  wire [C*32-1:0] c_rsp_rdata;
  wire [B-1:0] mem_req_valid,mem_req_write,mem_rsp_ready;
  reg [B-1:0] mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
  wire [B*4-1:0] mem_req_kind;
  wire [B*3-1:0] mem_req_proj;
  wire [B*32-1:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
  wire [B*64-1:0] mem_req_tag;
  reg [B*32-1:0] mem_rsp_rdata=0;
  reg [B*64-1:0] mem_rsp_tag=0;
  reg [B-1:0] response_accepted=0;
  anvil_d1_bank_scheduler #(.BANKS(B),.CLIENTS(C),.QUEUE_DEPTH(Q)) device(.*);
  integer sent[0:C-1],received[0:C-1];
  reg ingressed[0:T-1],issued[0:T-1],returned[0:T-1],owned[0:T-1];
  reg [63:0] tags[0:T-1];
  integer bank[0:T-1],order[0:T-1],response_id[0:B-1];
  reg held_req_valid[0:B-1],held_rsp_valid[0:C-1];
  reg [200:0] held_req[0:B-1];
  reg [32:0] held_rsp[0:C-1];
  integer cycles=0,ingress=0,requests=0,responses=0,client_responses=0;
  integer reorderings=0,request_stalls=0,response_stalls=0,peak_owned=0,reset_samples=0;
  integer b,c,id,owner,seq,pending,selected,oldest,newest;
  reg [31:0] expected_data;
  task automatic reset_check;
    begin
      if ({idle,drain_done,fault,c_req_ready,c_rsp_valid,c_rsp_error,c_rsp_rdata,
           mem_req_valid,mem_req_write,mem_req_kind,mem_req_proj,mem_req_layer,
           mem_req_row,mem_req_col,mem_req_wdata,mem_req_tag,mem_rsp_ready} !== 0)
        $fatal(1,"SCHEDULER_RESET_XZ t=%0t idle=%b drain_done=%b fault=%b client_ready=%b client_valid=%b memory_valid=%b response_ready=%b",
          $time,idle,drain_done,fault,c_req_ready,c_rsp_valid,mem_req_valid,mem_rsp_ready);
      reset_samples=reset_samples+1;
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    rst_n=0;
    for(integer j=0;j<C;j=j+1) begin sent[j]=0;received[j]=0;held_rsp_valid[j]=0;end
    for(integer j=0;j<B;j=j+1) begin held_req_valid[j]=0;response_id[j]=-1;end
    for(integer j=0;j<T;j=j+1) begin
      ingressed[j]=0;issued[j]=0;returned[j]=0;owned[j]=0;tags[j]=0;
    end
`ifdef VERILATOR
    #1;
`else
    #0;
`endif
    reset_check(); repeat(2) @(negedge clk); #1; rst_n=1;
    while (client_responses<T) @(negedge clk);
    repeat(5) @(negedge clk);
    if (ingress!=T || requests!=T || responses!=T || fault!==0 || idle!==1 ||
        request_stalls==0 || response_stalls==0 || reset_samples<5 ||
        (B*Q>1 && (reorderings==0 || peak_owned<2)))
      $fatal(1,"SCHEDULER_MISSING_COVERAGE in=%0d req=%0d rsp=%0d reorder=%0d peak=%0d",
        ingress,requests,responses,reorderings,peak_owned);
    $display("SUMMARY scheduler_banks=%0d queue=%0d ingress=%0d memory_requests=%0d memory_responses=%0d client_responses=%0d reordered_responses=%0d peak_owned=%0d request_stalls=%0d response_stalls=%0d reset=%0d cycles=%0d",
      B,Q,ingress,requests,responses,client_responses,reorderings,peak_owned,request_stalls,response_stalls,reset_samples,cycles);
    $finish;
  end
  always @(negedge clk) if (rst_n) begin
    // Only this driver changes response pins; retire pre-edge sampled transfers.
    mem_rsp_valid=mem_rsp_valid & ~response_accepted;
    for (integer j=0;j<C;j=j+1) begin
      c_req_valid[j]=sent[j]<N;
      c_req_write[j]=j%2;
      c_req_kind[j*4+:4]=8;
      c_req_proj[j*3+:3]=0;
      c_req_layer[j*32+:32]=j;
      c_req_row[j*32+:32]=j*N+sent[j];
      c_req_col[j*32+:32]=sent[j];
      c_req_wdata[j*32+:32]=j*N+sent[j]+1000;
      c_rsp_ready[j]=(cycles+j)%9==0;
    end
    for(integer j=0;j<B;j=j+1)
      mem_req_ready[j]=cycles>=30 && (cycles+j)%11!=0;
    // Return only the globally newest available request on this cycle.
    selected=-1;newest=-1;
    if (cycles>=100 && mem_rsp_valid==0) begin
      for(integer j=0;j<T;j=j+1)
        if (owned[j] && order[j]>newest) begin selected=j;newest=order[j];end
      if (selected>=0) begin
        mem_rsp_valid[bank[selected]]=1;
        response_id[bank[selected]]=selected;
        mem_rsp_tag[bank[selected]*64+:64]=tags[selected];
        mem_rsp_rdata[bank[selected]*32+:32]=(selected/N)%2 ? 0 : selected*37+11;
      end
    end
  end
  always @(posedge clk) if (rst_n) begin
    response_accepted=mem_rsp_valid & mem_rsp_ready;
    cycles=cycles+1;
    if(cycles>20000) $fatal(1,"SCHEDULER_CYCLE_BOUND");
    if ((^{idle,drain_done,fault,c_req_ready,c_rsp_valid,mem_req_valid,mem_rsp_ready})===1'bx ||
        fault!==0) $fatal(1,"SCHEDULER_ACTIVE_XZ_OR_FAULT");
    for(c=0;c<C;c=c+1) begin
      if(c_req_valid[c] && c_req_ready[c]) begin
        id=c*N+sent[c];
        if(ingressed[id]) $fatal(1,"DUPLICATE_INGRESS");
        ingressed[id]=1;sent[c]=sent[c]+1;ingress=ingress+1;
      end
      if(held_rsp_valid[c] && {c_rsp_valid[c],c_rsp_error[c],c_rsp_rdata[c*32+:32]} !== {1'b1,held_rsp[c]})
        $fatal(1,"SCHEDULER_RESPONSE_UNSTABLE");
      held_rsp_valid[c]=c_rsp_valid[c] && !c_rsp_ready[c];
      held_rsp[c]={c_rsp_error[c],c_rsp_rdata[c*32+:32]};
      if(held_rsp_valid[c]) response_stalls=response_stalls+1;
      if(c_rsp_valid[c] && c_rsp_ready[c]) begin
        id=c*N+received[c];expected_data=c%2 ? 0 : id*37+11;
        if(received[c]>=sent[c] || !returned[id] || c_rsp_error[c]!==0 ||
            c_rsp_rdata[c*32+:32]!==expected_data)
          $fatal(1,"SCHEDULER_CLIENT_FIFO_MISMATCH client=%0d id=%0d actual=%h expected=%h",
            c,id,c_rsp_rdata[c*32+:32],expected_data);
        received[c]=received[c]+1;client_responses=client_responses+1;
      end
    end
    for(b=0;b<B;b=b+1) begin
      if(held_req_valid[b] &&
        {mem_req_valid[b],mem_req_write[b],mem_req_kind[b*4+:4],mem_req_layer[b*32+:32],
         mem_req_proj[b*3+:3],mem_req_row[b*32+:32],mem_req_col[b*32+:32],
         mem_req_wdata[b*32+:32],mem_req_tag[b*64+:64]} !== held_req[b])
        $fatal(1,"SCHEDULER_REQUEST_UNSTABLE");
      held_req_valid[b]=mem_req_valid[b] && !mem_req_ready[b];
      held_req[b]={mem_req_valid[b],mem_req_write[b],mem_req_kind[b*4+:4],mem_req_layer[b*32+:32],
        mem_req_proj[b*3+:3],mem_req_row[b*32+:32],mem_req_col[b*32+:32],
        mem_req_wdata[b*32+:32],mem_req_tag[b*64+:64]};
      if(held_req_valid[b]) request_stalls=request_stalls+1;
      if(mem_req_valid[b] && mem_req_ready[b]) begin
        id=mem_req_row[b*32+:32];owner=id/N;seq=id%N;
        if(id>=T || !ingressed[id] || issued[id] ||
           mem_req_kind[b*4+:4]!==8 || mem_req_layer[b*32+:32]!==owner ||
           mem_req_proj[b*3+:3]!==0 || mem_req_col[b*32+:32]!==seq ||
           mem_req_write[b]!==1'(owner%2) || mem_req_wdata[b*32+:32]!==32'(id+1000))
          $fatal(1,"SCHEDULER_PACKED_REQUEST_MISMATCH");
        for(integer j=0;j<T;j=j+1)
          if(owned[j] && tags[j]===mem_req_tag[b*64+:64]) $fatal(1,"DUPLICATE_OWNED_TAG");
        owned[id]=1;issued[id]=1;bank[id]=b;tags[id]=mem_req_tag[b*64+:64];
        order[id]=requests;requests=requests+1;
      end
      if(mem_rsp_valid[b] && mem_rsp_ready[b]) begin
        id=response_id[b];
        if(id<0 || !owned[id] || mem_rsp_tag[b*64+:64]!==tags[id])
          $fatal(1,"SCHEDULER_RESPONSE_OWNERSHIP");
        oldest=order[id];
        for(integer j=0;j<T;j=j+1) if(owned[j] && order[j]<oldest) oldest=order[j];
        if(order[id]>oldest) reorderings=reorderings+1;
        owned[id]=0;returned[id]=1;responses=responses+1;
      end
    end
    pending=0;for(integer j=0;j<T;j=j+1) if(owned[j]) pending=pending+1;
    if(pending>peak_owned) peak_owned=pending;
  end
endmodule
"""


if __name__ == "__main__":
    import argparse
    from diagnostic import simulate
    from evidence import Evidence, rel
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-of")
    parser.add_argument("--banks", type=int, choices=(1, 2, 4, 8), default=2)
    parser.add_argument("--queue", type=int, choices=range(1, 17), default=3)
    parser.add_argument("--sim", choices=("icarus", "verilator"), default="icarus")
    args = parser.parse_args()
    evidence = Evidence(f"scheduler-b{args.banks}-q{args.queue}-{args.sim}", args.repair_of)
    try:
        fixture = scheduler_bench(evidence, args.banks, args.queue)
        text = simulate(evidence, "scheduler.sv", args.sim)
        evidence.finish("passed", fixture=fixture, observations=text)
        print(text.strip())
        print(rel(evidence.path/"receipt.json"))
    except Exception as exc:
        evidence.finish("failed", error=str(exc))
        print(str(exc))
        print(rel(evidence.path/"receipt.json"))
        raise SystemExit(1)
