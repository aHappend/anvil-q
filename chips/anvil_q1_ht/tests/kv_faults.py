"""KV public spill-response, fault and invalid-address conservation checks.

The backing store is an independent word-addressed spill service, not an EMIF
measurement. Existing KV/attention workloads remain separate and unchanged.
"""

from experiments import CLOCK, measurement_records


def kv_fault_case(evidence, depth, seed, simulator):
    bench = CLOCK + r"""
localparam WINDOW=@WINDOW@,POSITIONS=WINDOW+2,WIDTH=16,WORDS=2*2*POSITIONS*WIDTH;
reg new_sequence=0,req_valid=0,req_write=0,req_value=0,rsp_ready=0;
reg [31:0] req_layer=0,req_head=0,req_pos=0,req_dim=0,req_wdata=0;
wire initialized,req_ready,rsp_valid,rsp_error,rsp_hit,protocol_error;
wire [31:0] rsp_data;
wire spill_valid,spill_ready,spill_write,spill_value,spill_rsp_ready;
wire [31:0] spill_layer,spill_pos,spill_col,spill_wdata;
wire spill_rsp_valid,spill_rsp_error;
wire [31:0] spill_rsp_data;
reg [31:0] backing[0:WORDS-1];
reg present[0:WORDS-1];
reg immediate=0,pending=0,pending_error=0;
reg [31:0] pending_data=0;
integer response_delay=0,service_delay=0,traffic_index=0,cycles=0;
integer fault_index=-1;
reg fault_enabled=0,fault_write=0;
integer commands=0,responses=0,writes=0,reads=0,immediate_returns=0,delayed_returns=0;
integer faults=0,comparisons=0,hot=0,cold=0,response_stalls=0,issue_stalls=0;
integer successful_services=0,eviction_faults=0,read_faults=0,invalid_cases=0;
integer epochs=0,reset_compares=0,i,mode,index,total_cycles=0;
reg held_spill=0;
reg [129:0] held_payload;
wire [129:0] spill_payload={spill_write,spill_value,spill_layer,spill_pos,spill_col,spill_wdata};
wire immediate_fault=fault_enabled && spill_write==fault_write && traffic_index==fault_index;
wire [31:0] address=((spill_layer*2+spill_value)*POSITIONS+spill_pos)*WIDTH+spill_col;
assign spill_ready=rst_n && !pending && cycles%11>3;
assign spill_rsp_valid=rst_n &&
  (immediate ? (spill_valid && spill_ready) : (pending && response_delay==0));
assign spill_rsp_error=spill_rsp_valid && (immediate ? immediate_fault : pending_error);
assign spill_rsp_data=!spill_rsp_valid ? 0 :
  (immediate ? (spill_write ? 32'b0 : backing[address]) : pending_data);
function automatic [31:0] expected_word(input integer layer,position,column,value_bit);
 begin
  expected_word=(32'h9e3779b9*(1+layer*104729+position*257+column*3+value_bit)) ^
                (32'h01234567*@SEED@);
 end
endfunction
anvil_q1_ht_kv_window #(.NUM_LAYERS(2),.NUM_KV_HEADS(2),.HEAD_DIM(8),
 .MAX_SEQ_LEN(POSITIONS),.KV_WINDOW(WINDOW)) product(.*);
task check_reset;
 begin
  if({initialized,req_ready,rsp_valid,rsp_data,rsp_error,rsp_hit,protocol_error,
      spill_valid,spill_write,spill_value,spill_layer,spill_pos,spill_col,
      spill_wdata,spill_rsp_ready} !== 171'b0)
   $fatal(1,"KV_SERVICE_RESET_XZ_OR_NONZERO");
  reset_compares=reset_compares+1;
 end
endtask
always @(posedge clk or negedge clk) if(!rst_n) check_reset();
always @(posedge clk) begin
 total_cycles=total_cycles+1;
 if(!rst_n) begin
  pending<=0;response_delay<=0;traffic_index<=0;cycles<=0;held_spill<=0;
 end else begin
  cycles<=cycles+1;
  if(held_spill && (spill_valid!==1 || spill_payload!==held_payload))
   $fatal(1,"KV_SERVICE_ISSUE_STALL_CHANGED");
  held_spill<=spill_valid && !spill_ready;
  if(spill_valid && !spill_ready) begin
   held_payload<=spill_payload;issue_stalls=issue_stalls+1;
  end
  if(spill_valid && spill_ready) begin
   if(pending || spill_layer>=2 || spill_pos>=POSITIONS || spill_col>=WIDTH ||
      (^{spill_write,spill_value,spill_layer,spill_pos,spill_col,spill_wdata})===1'bx)
    $fatal(1,"KV_SERVICE_UNEXPECTED_OR_UNKNOWN_COMMAND");
   if(spill_write) begin
    if(present[address]!==0 ||
       spill_wdata!==expected_word(spill_layer,spill_pos,spill_col,spill_value))
     $fatal(1,"KV_SERVICE_EVICTION_DUPLICATE_OR_DATA");
    if(!immediate_fault) begin backing[address]=spill_wdata;present[address]=1;end
    writes=writes+1;
   end else begin
    if(present[address]!==1 ||
       backing[address]!==expected_word(spill_layer,spill_pos,spill_col,spill_value))
     $fatal(1,"KV_SERVICE_COLD_ADDRESS_OR_DATA");
    reads=reads+1;
   end
   traffic_index<=traffic_index+1;commands=commands+1;
   if(immediate) begin
    if(spill_rsp_valid!==1 || spill_rsp_ready!==1)
     $fatal(1,"KV_SERVICE_IMMEDIATE_RESPONSE_NOT_COINCIDENT");
   end else begin
    pending<=1;
    pending_error<=immediate_fault;
    pending_data<=spill_write ? 32'b0 : backing[address];
    response_delay<=service_delay;
   end
  end
  if(pending && response_delay>0) response_delay<=response_delay-1;
  if(spill_rsp_valid && spill_rsp_ready) begin
   if(!immediate && !pending) $fatal(1,"KV_SERVICE_ORPHAN_RESPONSE");
   pending<=0;responses=responses+1;
   if(immediate) immediate_returns=immediate_returns+1;
   else delayed_returns=delayed_returns+1;
   if(spill_rsp_error) faults=faults+1;
  end
 end
end
task reset_case(input integer instant,delay);
 begin
  @(negedge clk);rst_n=0;req_valid=0;rsp_ready=0;
  fault_enabled=0;immediate=instant;service_delay=delay;
  for(i=0;i<WORDS;i=i+1) begin present[i]=0;backing[i]=0;end
  #0.001;check_reset();
  repeat(3) edge_tick();
  @(negedge clk);rst_n=1;
  repeat((POSITIONS>2*WINDOW ? POSITIONS : 2*WINDOW)+3) edge_tick();
  if(initialized!==1 || req_ready!==1 || {rsp_valid,protocol_error,spill_valid}!==3'b0)
   $fatal(1,"KV_SERVICE_RESET_NOT_IDLE");
  epochs=epochs+1;
 end
endtask
task request(input integer wr,layer,position,column,value_bit,expect_error,expect_hit);
 integer wait_edges,old_reads,old_writes,n;
 reg [31:0] expected_data;
 reg saved_hit;
 begin
  @(negedge clk);
  req_valid=1;req_write=wr;req_layer=layer;req_pos=position;
  req_head=column==-1 ? 0 : column/8;
  req_dim=column==-1 ? 8 : column%8;req_value=value_bit;
  req_wdata=expected_word(layer,position,column,value_bit);
  old_reads=reads;old_writes=writes;
  if(req_ready!==1) $fatal(1,"KV_SERVICE_REQUEST_NOT_READY");
  edge_tick();
  if(rsp_valid!==0 || req_ready!==0) $fatal(1,"KV_SERVICE_ACCEPT_EDGE");
  @(negedge clk);req_valid=0;
  wait_edges=0;
  while(rsp_valid!==1 && wait_edges<10000) begin edge_tick();wait_edges=wait_edges+1;end
  expected_data=wr || expect_error ? 32'b0 : expected_word(layer,position,column,value_bit);
  if(rsp_valid!==1 || rsp_error!==1'(expect_error) ||
     protocol_error!==1'(expect_error) || rsp_data!==expected_data ||
     (rsp_hit!==0 && rsp_hit!==1) || (!wr && rsp_hit!==1'(expect_hit)))
   $fatal(1,"KV_SERVICE_RESULT_MISMATCH wr=%0d l=%0d p=%0d c=%0d err=%b hit=%b got=%h expected=%h",
          wr,layer,position,column,rsp_error,rsp_hit,rsp_data,expected_data);
  saved_hit=rsp_hit;
  if(!wr && !expect_error) begin
   if(expect_hit) begin
    if(reads!==old_reads || writes!==old_writes || wait_edges!==2)
     $fatal(1,"KV_SERVICE_HOT_LATENCY_OR_TRAFFIC");
    hot=hot+1;
   end else begin
    if(reads!==old_reads+1 || writes!==old_writes)
     $fatal(1,"KV_SERVICE_COLD_CONSERVATION");
    cold=cold+1;
   end
  end
  for(n=0;n<7;n=n+1) begin
   edge_tick();
   if(rsp_valid!==1 || rsp_error!==1'(expect_error) || rsp_data!==expected_data ||
      req_ready!==0 || spill_valid!==0 ||
      protocol_error!==1'(expect_error) || rsp_hit!==saved_hit)
    $fatal(1,"KV_SERVICE_RESPONSE_STALL_CHANGED");
   response_stalls=response_stalls+1;
  end
  @(negedge clk);rsp_ready=1;edge_tick();
  if(rsp_valid!==0) $fatal(1,"KV_SERVICE_RESPONSE_NOT_RETIRED");
  @(negedge clk);rsp_ready=0;
  comparisons=comparisons+1;
 end
endtask
task populate(input integer layers,positions);
 integer pp,ll,vv,cc;
 begin
  for(pp=0;pp<positions;pp=pp+1)
   for(ll=0;ll<layers;ll=ll+1)
    for(vv=0;vv<2;vv=vv+1)
     for(cc=0;cc<WIDTH;cc=cc+1) request(1,ll,pp,cc,vv,0,0);
 end
endtask
task failed_quiescence;
 integer n,old_commands,old_responses;
 begin
  old_commands=commands;old_responses=responses;
  for(n=0;n<31;n=n+1) begin
   edge_tick();
   if({req_ready,rsp_valid,spill_valid,protocol_error}!==4'b0001 ||
      commands!==old_commands || responses!==old_responses || pending!==0)
    $fatal(1,"KV_SERVICE_FAULT_FALSE_SUCCESS_OR_MORE_TRAFFIC");
  end
 end
endtask
task successful_case(input integer instant,delay);
 integer start_writes,start_reads,ll,vv,cc;
 begin
  reset_case(instant,delay);start_writes=writes;start_reads=reads;
  populate(2,WINDOW+1);
  if(writes!==start_writes+64 || reads!==start_reads)
   $fatal(1,"KV_SERVICE_EVICTION_COVERAGE");
  for(ll=0;ll<2;ll=ll+1)
   for(vv=0;vv<2;vv=vv+1)
    for(cc=0;cc<WIDTH;cc=cc+1) begin
     request(0,ll,WINDOW,cc,vv,0,1);
     request(0,ll,0,cc,vv,0,0);
    end
  if(commands!==responses || pending!==0) $fatal(1,"KV_SERVICE_UNSETTLED");
  successful_services=successful_services+1;
 end
endtask
initial begin
 rst_n=0;`RESET_DELTA check_reset();
 successful_case(1,0);successful_case(0,1);successful_case(0,7);
 for(mode=0;mode<2;mode=mode+1) begin
  for(index=0;index<3;index=index+1) begin
   reset_case(mode,7);populate(1,WINDOW);
   fault_enabled=1;fault_write=1;
   fault_index=index==0 ? 0 : (index==1 ? 15 : 31);
   request(1,0,WINDOW,0,0,1,0);
   if(traffic_index!==fault_index+1 || commands!==responses)
    $fatal(1,"KV_SERVICE_EVICTION_FAULT_ACCOUNTING");
   failed_quiescence();eviction_faults=eviction_faults+1;
  end
  reset_case(mode,7);populate(1,WINDOW+1);
  fault_enabled=1;fault_write=0;fault_index=traffic_index;
  request(0,0,0,0,0,1,0);
  if(traffic_index!==33 || commands!==responses)
   $fatal(1,"KV_SERVICE_READ_FAULT_ACCOUNTING");
  failed_quiescence();read_faults=read_faults+1;
 end
 for(index=0;index<8;index=index+1) begin
  reset_case(1,0);
  case(index)
   0: request(0,2,0,0,0,1,0);
   1: request(0,0,0,16,0,1,0);
   2: request(0,0,POSITIONS,0,0,1,0);
   3: request(0,0,0,-1,0,1,0);
   4: request(0,0,0,0,0,1,0);
   5: request(0,0,1,0,0,1,0);
   6: request(1,0,1,0,0,1,0);
   7: request(0,0,0,24,0,1,0);
  endcase
  if(traffic_index!==0) $fatal(1,"KV_SERVICE_INVALID_ADDRESS_SPILLED");
  failed_quiescence();invalid_cases=invalid_cases+1;
 end
 if(successful_services!==3 || eviction_faults!==6 || read_faults!==2 ||
    invalid_cases!==8 || faults!==8 || hot!==192 || cold!==192 ||
    immediate_returns==0 || delayed_returns==0 || issue_stalls==0 ||
    commands!==responses || pending!==0)
  $fatal(1,"KV_SERVICE_REQUIRED_COVERAGE_MISSING");
 $display("CHECKS_PASSED kv_service window=%0d seed=@SEED@ successful_services=%0d eviction_faults=%0d read_faults=%0d invalid_cases=%0d faults=%0d hot=%0d cold=%0d immediate_returns=%0d delayed_returns=%0d issue_stalls=%0d response_stalls=%0d commands=%0d responses=%0d comparisons=%0d epochs=%0d reset_compares=%0d cycles=%0d",
          WINDOW,successful_services,eviction_faults,read_faults,invalid_cases,faults,
          hot,cold,immediate_returns,delayed_returns,issue_stalls,response_stalls,
          commands,responses,comparisons,epochs,reset_compares,total_cycles);
 $finish;
end
endmodule
"""
    bench = bench.replace("@WINDOW@", str(depth)).replace("@SEED@", str(seed))
    text = evidence.simulate(f"kv-service-{depth}-{simulator}", bench,
                             ["anvil_q1_ht_kv_window.sv"], simulator=simulator)
    records = measurement_records(text, "CHECKS_PASSED kv_service")
    if len(records) != 1:
        raise AssertionError("KV service lacks a unique observed coverage ledger")
    counts = records[0]
    required = {"successful_services": 3, "eviction_faults": 6, "read_faults": 2,
                "invalid_cases": 8, "faults": 8, "hot": 192, "cold": 192,
                "commands": 548, "responses": 548, "immediate_returns": 210,
                "delayed_returns": 338, "epochs": 19,
                "comparisons": 448 * depth + 656}
    if any(counts.get(key) != value for key, value in required.items()):
        raise AssertionError("KV service did not observe every required response/fault bin")
    if (counts["commands"] != counts["responses"] or
            min(counts[key] for key in ("immediate_returns", "delayed_returns",
                                       "issue_stalls", "response_stalls", "reset_compares")) <= 0):
        raise AssertionError("KV service lacks settled traffic/stall/reset comparisons")
    if simulator == "iverilog" and counts["cycles"] > 500000:
        raise AssertionError("KV Icarus smoke exceeds the compact simulation tier")
    evidence.record.setdefault("kv_service_checks", []).append({
        "scope": "public_KV_logical_spill_port_not_EMIF_or_full_model_acceptance",
        "simulator": simulator, "window": depth, "seed": seed,
        "geometry": {"layers": 2, "kv_heads": 2, "head_dim": 8},
        "observed": counts,
        "response_services": ["request-edge response", "delayed 1 cycle", "delayed 7 cycles"],
        "fault_bins": "first/middle/final eviction response and cold read, both response modes",
        "oracle": "independent address-keyed word store, exact word formula and no duplicate spills",
    })
    evidence.flush()


def kv_faults(evidence, seed):
    if seed == 17 and getattr(evidence, "default_simulator", "iverilog") == "iverilog":
        for depth in (1, 3):
            kv_fault_case(evidence, depth, seed, "iverilog")
    for depth in (1, 3, 128):
        kv_fault_case(evidence, depth, seed, "verilator")
