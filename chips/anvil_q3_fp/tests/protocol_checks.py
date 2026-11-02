"""Scheduler transaction conservation, association, reordering and drain checks."""

from execution import compiled, icarus, relative, run_compiled


def scheduler(evidence, banks, depth, simulator="verilator"):
    tb = SCHEDULER_TB.replace("@B@", str(banks)).replace("@Q@", str(depth))
    name = f"scheduler-b{banks}-q{depth}-{simulator}"
    rtl = ["anvil_q3_reference/rtl/anvil_q3_bank_scheduler.sv"]
    if simulator == "iverilog":
        output = icarus(evidence, name, tb, rtl)
    else:
        executable = compiled(evidence, name, tb, rtl)
        output = run_compiled(evidence, executable, name, {})
    return {"banks": banks, "queue_depth": depth, "simulator": simulator, "stdout": relative(output)}


SCHEDULER_TB = """
module tb;
  localparam B=@B@,Q=@Q@,C=B+2,N=24;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n,flush=0,reset_sample=0;
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
  anvil_q3_bank_scheduler #(.BANKS(B),.CLIENTS(C),.QUEUE_DEPTH(Q)) dut(.*);
  integer sent[0:C-1],retired[0:C-1],accepted_at[0:C*64-1];
  reg accepted[0:C*64-1],dispatched[0:C*64-1],responded[0:C*64-1];
  reg [199:0] external_hold[0:B-1];
  reg [32:0] client_hold[0:C-1];
  reg [B-1:0] held_req=0;
  reg [C-1:0] held_rsp=0;
  reg live[0:B-1][0:31];
  reg [63:0] tags[0:B-1][0:31],seen_tag[0:4095],old_tag;
  integer ids[0:B-1][0:31],due[0:B-1][0:31],chosen[0:B-1];
  integer bank,client,slot,id,route,seq,free_slot,active_count,oldest_id;
  integer index,phase=0,phase_start=0,cycle=0,ingress=0,issued=0,returned=0,completed=0;
  integer seen_count=0,request_stalls=0,response_stalls=0,reorders=0,overlap=0;
  integer unrelated=0,aborted=0,faults=0,drains=0,normal_completed=0,injections=0;
  reg injection_sent=0,flush_sent=0,draining_expected=0;
  task reset_check;
    begin
      if ({idle,drain_done,fault,c_req_ready,c_rsp_valid,c_rsp_error,c_rsp_rdata,
           mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
           mem_req_row,mem_req_col,mem_req_wdata,mem_req_tag,mem_rsp_ready} !== 0)
        $fatal(1,"RESET scheduler outputs");
    end
  endtask
  initial begin
    rst_n=0;
    for (client=0;client<C;client=client+1) begin sent[client]=0; retired[client]=0; end
    for (id=0;id<C*64;id=id+1) begin accepted[id]=0; dispatched[id]=0; responded[id]=0; end
    for (bank=0;bank<B;bank=bank+1)
      for (slot=0;slot<32;slot=slot+1) live[bank][slot]=0;
    reset_sample<=1; @(posedge reset_sample); reset_check;
    #1; reset_check;
    @(negedge clk); rst_n=1;
  end
  always @(posedge clk) begin
    if (!rst_n) reset_check;
    else begin
      if (fault) begin faults=faults+1; draining_expected=1; end
      if (drain_done) begin
        drains=drains+1;
        if (returned!=issued) $fatal(1,"early drain returned=%0d issued=%0d",returned,issued);
        draining_expected=0;
      end
      for (client=0;client<C;client=client+1) begin
        if (held_rsp[client] && !flush && !draining_expected &&
            (c_rsp_valid[client]!==1'b1 ||
             {c_rsp_error[client],c_rsp_rdata[client*32+:32]}!==client_hold[client]))
          $fatal(1,"STALL scheduler client payload");
        held_rsp[client]=c_rsp_valid[client] && !c_rsp_ready[client] && !flush;
        client_hold[client]={c_rsp_error[client],c_rsp_rdata[client*32+:32]};
        if (held_rsp[client]) response_stalls=response_stalls+1;
        if (draining_expected && c_rsp_valid[client]) $fatal(1,"stale client response during drain");
        if (c_rsp_valid[client] && c_rsp_ready[client]) begin
          if (phase!=0) $fatal(1,"canceled response escaped");
          id=client*64+retired[client];
          if (!accepted[id] || !dispatched[id] || !responded[id] ||
              c_rsp_rdata[client*32+:32] !== (32'(id)^32'ha5c39e17) ||
              c_rsp_error[client] !== (id%13==0))
            $fatal(1,"ASSOCIATION client=%0d seq=%0d expected=%h got=%h error=%b",
              client,retired[client],32'(id)^32'ha5c39e17,c_rsp_rdata[client*32+:32],c_rsp_error[client]);
          retired[client]=retired[client]+1; completed=completed+1;
        end
        if (c_req_valid[client] && c_req_ready[client]) begin
          id=client*64+sent[client];
          if (accepted[id]) $fatal(1,"duplicate ingress id");
          accepted[id]=1; accepted_at[id]=cycle;
          sent[client]=sent[client]+1; ingress=ingress+1;
          if ((mem_req_valid&mem_req_ready)!=0 || (c_rsp_valid&c_rsp_ready)!=0) overlap=overlap+1;
        end
      end
      for (bank=0;bank<B;bank=bank+1) begin
        if (held_req[bank] && !flush && !draining_expected &&
            (mem_req_valid[bank]!==1'b1 ||
             {mem_req_write[bank],mem_req_kind[bank*4+:4],mem_req_layer[bank*32+:32],
              mem_req_proj[bank*3+:3],mem_req_row[bank*32+:32],mem_req_col[bank*32+:32],
              mem_req_wdata[bank*32+:32],mem_req_tag[bank*64+:64]}!==external_hold[bank]))
          $fatal(1,"STALL scheduler external payload");
        held_req[bank]=mem_req_valid[bank] && !mem_req_ready[bank] && !flush;
        external_hold[bank]={mem_req_write[bank],mem_req_kind[bank*4+:4],mem_req_layer[bank*32+:32],
          mem_req_proj[bank*3+:3],mem_req_row[bank*32+:32],mem_req_col[bank*32+:32],
          mem_req_wdata[bank*32+:32],mem_req_tag[bank*64+:64]};
        if (held_req[bank]) request_stalls=request_stalls+1;
        if (mem_rsp_valid[bank] && mem_rsp_ready[bank] && chosen[bank]>=0) begin
          slot=chosen[bank]; id=ids[bank][slot]; oldest_id=id;
          for (index=0;index<32;index=index+1)
            if (live[bank][index] && accepted_at[ids[bank][index]]<accepted_at[oldest_id])
              oldest_id=ids[bank][index];
          if (oldest_id!=id) reorders=reorders+1;
          if (!live[bank][slot] || responded[id]) $fatal(1,"duplicate scoreboard response");
          responded[id]=1; live[bank][slot]=0; returned=returned+1;
        end
        if (mem_req_valid[bank] && mem_req_ready[bank]) begin
          id=mem_req_wdata[bank*32+:32]; client=id/64; seq=id%64;
          if (id>=C*64 || !accepted[id] || dispatched[id]) $fatal(1,"unknown/duplicate external request");
          route=(8+client+(seq%7)+seq+((seq*3+client)&255))&(B-1);
          if (route!=bank || mem_req_write[bank]!==1'(seq&1) ||
              mem_req_kind[bank*4+:4]!==4'd8 || mem_req_layer[bank*32+:32]!==32'(client) ||
              mem_req_proj[bank*3+:3]!==3'(seq%7) || mem_req_row[bank*32+:32]!==32'(seq) ||
              mem_req_col[bank*32+:32]!==32'((seq*3+client)&255))
            $fatal(1,"scheduler payload/routing corruption");
          for (index=0;index<seen_count;index=index+1)
            if (seen_tag[index]===mem_req_tag[bank*64+:64]) $fatal(1,"tag reuse");
          seen_tag[seen_count]=mem_req_tag[bank*64+:64]; seen_count=seen_count+1;
          old_tag=mem_req_tag[bank*64+:64];
          free_slot=-1;
          for (slot=0;slot<32;slot=slot+1) if (!live[bank][slot] && free_slot<0) free_slot=slot;
          if (free_slot<0) $fatal(1,"external scoreboard full");
          live[bank][free_slot]=1; tags[bank][free_slot]=mem_req_tag[bank*64+:64];
          ids[bank][free_slot]=id; due[bank][free_slot]=cycle+20+(id%7);
          dispatched[id]=1; issued=issued+1;
          if (bank!=0 && held_req[0]) unrelated=unrelated+1;
        end
      end
      if (flush) begin draining_expected=1; aborted=ingress-completed; end
      if (phase==0 && completed==C*N && idle) begin
        normal_completed=completed; phase=1; phase_start=cycle;
        for (client=0;client<C;client=client+1) begin sent[client]=N; retired[client]=N; end
      end else if (phase==1 && flush_sent && drain_done) begin
        phase=2; phase_start=cycle; injection_sent=0;
      end else if (phase>=2 && phase<=4 && injection_sent && drain_done) begin
        phase=phase+1; phase_start=cycle; injection_sent=0;
      end else if (phase==5 && idle) begin
        if (normal_completed!=C*N || ingress!=completed+aborted || issued!=returned ||
            faults!=3 || drains!=4 || request_stalls==0 || response_stalls==0 ||
            overlap==0 || (B>1 && unrelated==0) || (Q>1 && reorders==0))
          $fatal(1,"COVERAGE ingress=%0d completed=%0d aborted=%0d issued=%0d returned=%0d faults=%0d drains=%0d stalls=%0d/%0d overlap=%0d unrelated=%0d reorder=%0d",
            ingress,completed,aborted,issued,returned,faults,drains,request_stalls,response_stalls,overlap,unrelated,reorders);
        $display("COMPARED scheduler ingress=%0d completed=%0d aborted=%0d requests=%0d reorders=%0d faults=%0d unrelated=%0d",
          ingress,completed,aborted,issued,reorders,faults,unrelated);
        $finish;
      end
      cycle=cycle+1;
      if (cycle>100000) $fatal(1,"scheduler progress phase=%0d ingress=%0d issued=%0d returned=%0d completed=%0d",phase,ingress,issued,returned,completed);
    end
  end
  always @(negedge clk) begin
    if (!rst_n) reset_check;
    else begin
      flush=0;
      for (client=0;client<C;client=client+1) begin
        c_req_valid[client]=(phase==0 && sent[client]<N) ||
          (phase==1 && !flush_sent && sent[client]<N+4);
        c_req_write[client]=sent[client]&1;
        c_req_kind[client*4+:4]=8; c_req_layer[client*32+:32]=client;
        c_req_proj[client*3+:3]=3'(sent[client]%7); c_req_row[client*32+:32]=sent[client];
        c_req_col[client*32+:32]=(sent[client]*3+client)&255;
        c_req_wdata[client*32+:32]=client*64+sent[client];
        c_rsp_ready[client]=(cycle+client)%13<8;
      end
      for (bank=0;bank<B;bank=bank+1) begin
        mem_req_ready[bank]=(cycle+bank)%11<7 && !(bank==0 && cycle%79<25);
        chosen[bank]=-1;
        for (slot=0;slot<32;slot=slot+1)
          if (live[bank][slot] && due[bank][slot]<=cycle)
            if (chosen[bank]<0 || ((cycle&1) ? ids[bank][slot]>ids[bank][chosen[bank]] :
                ids[bank][slot]<ids[bank][chosen[bank]])) chosen[bank]=slot;
        mem_rsp_valid[bank]=chosen[bank]>=0;
        mem_rsp_error[bank]=0; mem_rsp_rdata[bank*32+:32]=0; mem_rsp_tag[bank*64+:64]=0;
        if (chosen[bank]>=0) begin
          id=ids[bank][chosen[bank]];
          mem_rsp_error[bank]=id%13==0;
          mem_rsp_rdata[bank*32+:32]=32'(id)^32'ha5c39e17;
          mem_rsp_tag[bank*64+:64]=tags[bank][chosen[bank]];
        end
      end
      if (phase==1 && !flush_sent && issued>normal_completed) begin
        flush=1; flush_sent=1; c_req_valid=0;
      end
      if (phase>=2 && phase<=4 && !injection_sent && idle) begin
        mem_rsp_valid[0]=1; chosen[0]=-1;
        mem_rsp_tag[0+:64]=phase==2 ? 64'hffffffffffffffff :
          phase==3 ? seen_tag[0] : old_tag;
        injections=injections+1; injection_sent=1;
      end
    end
  end
endmodule
"""
