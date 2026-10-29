"""Public-pin scalar DDR bridge checks; no internal CDC/FSM observations."""

import hashlib
import random

from experiments import measurement_records


def scalar_case(evidence, simulator, seed, core_half=5, ddr_half=1.875):
    rng = random.Random(seed)
    calls = []
    for write in (0, 1):
        for immediate, delay in ((1, 0), (0, 1), (0, 7)):
            for stall in (1, 7, 31):
                for response in (0, 1, 2, 3):
                    address = rng.randrange(1 << 27) * 64
                    if len(calls) % 9 == 0:
                        address = (1 << 33) - 64
                    data = rng.getrandbits(512)
                    mask = rng.choice((0, (1 << 64) - 1, rng.getrandbits(64)))
                    calls.append(
                        f"transaction(1'b{write},33'h{address:09x},"
                        f"512'h{data:0128x},64'h{mask:016x},"
                        f"{immediate},{delay},{stall},{response},{stall});")
    bench = r"""
`timescale 1ns/1ps
module tb;
reg clk=0,ddr_clk=0,rst_n;
always #CORE_HALF clk=!clk;
always #DDR_HALF ddr_clk=!ddr_clk;
reg req_valid=0,req_write=0,rsp_ready=0;
reg [32:0] req_address=0;
reg [511:0] req_wdata=0;
reg [63:0] req_byteenable=0;
wire req_ready,rsp_valid,rsp_error,protocol_error;
wire [511:0] rsp_data;
wire [32:0] avm_address;
wire [7:0] avm_burstcount;
wire avm_read,avm_write;
wire [511:0] avm_writedata;
wire [63:0] avm_byteenable;
reg avm_waitrequest=0,avm_readdatavalid=0,avm_writeresponsevalid=0;
reg [511:0] avm_readdata=0;
reg [1:0] avm_response=0;
integer completed=0,requests=0,commands=0,returns=0,checks=0;
integer immediate_reads=0,immediate_writes=0,delayed_reads=0,delayed_writes=0;
integer fault_returns=0,issue_stalls=0,result_stalls=0,alignment_rejections=0;
integer reset_aborts=0,orphan_rejections=0;
anvil_q1_ht_ddr_scalar product(.*);
task tick;
 begin @(posedge clk);#0.001;end
endtask
task reset_check;
 begin
  if({req_ready,rsp_valid,rsp_data,rsp_error,protocol_error,avm_address,
      avm_burstcount,avm_read,avm_write,avm_writedata,avm_byteenable} !== 1135'b0)
   $fatal(1,"SCALAR_RESET_XZ_OR_NONZERO time=%0t",$time);
 end
endtask
always @(posedge clk or negedge clk or posedge ddr_clk or negedge ddr_clk)
 if(!rst_n) reset_check();
task reset_bridge;
 begin
  @(negedge clk);rst_n=0;req_valid=0;rsp_ready=0;
  avm_waitrequest=0;avm_readdatavalid=0;avm_writeresponsevalid=0;
  avm_readdata=0;avm_response=0;
  #0.001;reset_check();
  repeat(3) tick();
  @(negedge clk);rst_n=1;
  // Neither clock's readiness alone establishes the other domain's reset release.
  repeat(4) @(negedge ddr_clk);
  idle();
 end
endtask
task idle;
 integer n;
 begin
  n=0;
  while(req_ready!==1 && n<100) begin tick();n=n+1;end
  if(req_ready!==1 || rsp_valid!==0 || protocol_error!==0)
   $fatal(1,"SCALAR_IDLE_OR_RESET_RELEASE");
 end
endtask
task offer(input wr,input [32:0] address,input [511:0] data,input [63:0] mask);
 begin
  idle();
  @(negedge clk);
  req_valid=1;req_write=wr;req_address=address;req_wdata=data;req_byteenable=mask;
  #0.001;
  if(req_ready!==1) $fatal(1,"SCALAR_REQUEST_NOT_ACCEPTED");
  tick();
  if(req_ready!==0 || rsp_valid!==0) $fatal(1,"SCALAR_REQUEST_EDGE");
  requests=requests+1;
  @(negedge clk);req_valid=0;
 end
endtask
task bus_check(input wr,input [32:0] address,input [511:0] data,input [63:0] mask);
 begin
  if(avm_read!==!wr || avm_write!==wr || avm_address!==address ||
     avm_burstcount!==1 || avm_writedata!==(wr ? data : 512'b0) ||
     avm_byteenable!==(wr ? mask : 64'hffffffffffffffff))
   $fatal(1,"SCALAR_COMMAND_MISMATCH address=%h expected=%h",avm_address,address);
  checks=checks+1;
 end
endtask
task await_bus;
 integer n;
 begin
  n=0;
  while({avm_read,avm_write}===2'b00 && n<200) begin
   @(negedge ddr_clk);#0.001;n=n+1;
  end
  if((^{avm_read,avm_write})===1'bx || {avm_read,avm_write}===2'b00)
   $fatal(1,"SCALAR_MISSING_COMMAND");
 end
endtask
task drive_response(input wr,input [511:0] data,input [1:0] response);
 begin
  avm_readdatavalid=!wr;avm_writeresponsevalid=wr;
  avm_readdata=data;avm_response=response;
 end
endtask
task result(input [511:0] data,input failed,input integer stall);
 integer n;
 begin
  n=0;
  while(rsp_valid!==1 && n<500) begin tick();n=n+1;end
  if(rsp_valid!==1 || rsp_error!==failed || rsp_data!==data || req_ready!==0)
   $fatal(1,"SCALAR_RESULT_MISMATCH error=%h expected=%h data=%h expected_data=%h",
          rsp_error,failed,rsp_data,data);
  for(n=0;n<stall;n=n+1) begin
   tick();
   if(rsp_valid!==1 || rsp_error!==failed || rsp_data!==data || req_ready!==0 ||
      avm_read!==0 || avm_write!==0)
    $fatal(1,"SCALAR_STALLED_RESULT_CHANGED");
   result_stalls=result_stalls+1;
  end
  @(negedge clk);rsp_ready=1;
  if(rsp_valid!==1) $fatal(1,"SCALAR_PREEDGE_RESULT_LOST");
  tick();
  if(rsp_valid!==0) $fatal(1,"SCALAR_RESULT_NOT_RETIRED");
  @(negedge clk);rsp_ready=0;
  returns=returns+1;
 end
endtask
task transaction(input wr,input [32:0] address,input [511:0] data,
                 input [63:0] mask,input integer immediate,delay,stall,response,output_stall);
 reg [511:0] expected;
 integer n;
 begin
  expected=wr || response!=0 ? 512'b0 : data;
  avm_waitrequest=1;
  fork
   offer(wr,address,data,mask);
   begin
    await_bus();
    for(n=0;n<stall;n=n+1) begin
     @(posedge ddr_clk);
     bus_check(wr,address,data,mask);
     if(avm_waitrequest!==1) $fatal(1,"SCALAR_ISSUE_STALL_NOT_OBSERVED");
     issue_stalls=issue_stalls+1;
     @(negedge ddr_clk);
    end
    bus_check(wr,address,data,mask);
    avm_waitrequest=0;
    if(immediate) drive_response(wr,data,response[1:0]);
    @(posedge ddr_clk);
    bus_check(wr,address,data,mask);
    if(avm_waitrequest!==0) $fatal(1,"SCALAR_COMMAND_NOT_ACCEPTED");
    if(immediate && !(avm_readdatavalid || avm_writeresponsevalid))
     $fatal(1,"SCALAR_IMMEDIATE_RESPONSE_NOT_COINCIDENT");
    commands=commands+1;
    @(negedge ddr_clk);
    avm_readdatavalid=0;avm_writeresponsevalid=0;
    if(!immediate) begin
     repeat(delay) @(negedge ddr_clk);
     drive_response(wr,data,response[1:0]);
     @(posedge ddr_clk);
     if(avm_read!==0 || avm_write!==0) $fatal(1,"SCALAR_DUPLICATED_COMMAND");
     @(negedge ddr_clk);
     avm_readdatavalid=0;avm_writeresponsevalid=0;
    end
    avm_readdata=0;avm_response=0;
   end
   result(expected,response!=0,output_stall);
  join
  idle();
  if(protocol_error!==0) $fatal(1,"SCALAR_FALSE_PROTOCOL_ERROR");
  if(immediate && !wr) immediate_reads=immediate_reads+1;
  if(immediate && wr) immediate_writes=immediate_writes+1;
  if(!immediate && !wr) delayed_reads=delayed_reads+1;
  if(!immediate && wr) delayed_writes=delayed_writes+1;
  if(response!=0) fault_returns=fault_returns+1;
  completed=completed+1;
 end
endtask
task invalid_address(input integer low_bits);
 integer n;
 begin
  offer(0,33'h100000000+low_bits,0,0);
  fork
   result(0,1,7);
   begin
    for(n=0;n<50;n=n+1) begin
     @(posedge ddr_clk);
     if(avm_read!==0 || avm_write!==0) $fatal(1,"SCALAR_UNALIGNED_COMMAND_ISSUED");
    end
   end
  join
  idle();
  alignment_rejections=alignment_rejections+1;
 end
endtask
task abort_transaction(input integer phase);
 integer waiting;
 begin
  avm_waitrequest=1;
  fork
   offer(0,33'h100000040,512'h12345678,64'hffffffffffffffff);
   begin
    await_bus();
    @(posedge ddr_clk);bus_check(0,33'h100000040,0,64'hffffffffffffffff);
    @(negedge ddr_clk);
    if(phase!=0) begin
     avm_waitrequest=0;
     @(posedge ddr_clk);
     commands=commands+1;
     @(negedge ddr_clk);
     if(phase==2) begin
      drive_response(0,512'h12345678,0);
      @(posedge ddr_clk);
      @(negedge ddr_clk);avm_readdatavalid=0;
      waiting=0;
      while(rsp_valid!==1 && waiting<100) begin tick();waiting=waiting+1;end
      if(rsp_valid!==1 || rsp_data!==512'h12345678 || rsp_error!==0 || rsp_ready!==0)
       $fatal(1,"SCALAR_ABORT_NOT_ON_COMPARED_STALLED_RESULT");
     end
    end
    reset_bridge();
   end
  join
  repeat(8) begin
   tick();
   if(rsp_valid!==0 || avm_read!==0 || avm_write!==0 || req_ready!==1)
    $fatal(1,"SCALAR_ABORT_STALE_TRAFFIC");
  end
  reset_aborts=reset_aborts+1;
  transaction(0,33'h1ffffffc0,512'h8877665544332211,
              64'hffffffffffffffff,1,0,7,0,7);
 end
endtask
task orphan(input wr);
 integer n;
 begin
  idle();
  @(negedge ddr_clk);drive_response(wr,512'hbad,0);
  @(posedge ddr_clk);
  @(negedge ddr_clk);avm_readdatavalid=0;avm_writeresponsevalid=0;
  if(protocol_error!==1 || rsp_valid!==0)
   $fatal(1,"SCALAR_ORPHAN_NOT_REPORTED");
  // Fault is sticky: subsequent work must not issue an unowned bus transaction.
  @(negedge clk);req_valid=1;req_write=0;req_address=0;
  if(req_ready!==1) $fatal(1,"SCALAR_ORPHAN_REQUEST_NOT_ACCEPTED");
  tick();requests=requests+1;
  @(negedge clk);req_valid=0;
  fork
   result(0,1,7);
   begin
    for(n=0;n<50;n=n+1) begin
     @(posedge ddr_clk);
     if(avm_read!==0 || avm_write!==0 || protocol_error!==1)
      $fatal(1,"SCALAR_ORPHAN_STICKY_OR_TRAFFIC");
    end
   end
  join
  orphan_rejections=orphan_rejections+1;
  reset_bridge();
 end
endtask
integer offset;
initial begin
 rst_n=0;
`ifndef VERILATOR
 #0;
`endif
 reset_check();
 repeat(4) tick();
 @(negedge clk);rst_n=1;
 idle();
 CASES
 for(offset=1;offset<64;offset=offset+1) invalid_address(offset);
 abort_transaction(0);abort_transaction(1);abort_transaction(2);
 orphan(0);orphan(1);
 if(completed!=75 || commands!=77 || requests!=143 || returns!=140 ||
    alignment_rejections!=63 || reset_aborts!=3 || orphan_rejections!=2 ||
    immediate_reads!=15 || immediate_writes!=12 || delayed_reads!=24 ||
    delayed_writes!=24 || fault_returns!=54 || issue_stalls!=957 || result_stalls!=1412)
  $fatal(1,"SCALAR_MISSING_OBSERVED_COVERAGE completed=%0d commands=%0d requests=%0d returns=%0d issue=%0d result=%0d",
         completed,commands,requests,returns,issue_stalls,result_stalls);
 $display("CHECKS_PASSED scalar completed=%0d commands=%0d requests=%0d returns=%0d immediate_reads=%0d immediate_writes=%0d delayed_reads=%0d delayed_writes=%0d fault_returns=%0d issue_stalls=%0d result_stalls=%0d alignment_rejections=%0d reset_aborts=%0d orphan_rejections=%0d comparisons=%0d",
          completed,commands,requests,returns,immediate_reads,immediate_writes,
          delayed_reads,delayed_writes,fault_returns,issue_stalls,result_stalls,
          alignment_rejections,reset_aborts,orphan_rejections,checks);
 $finish;
end
endmodule
"""
    bench = bench.replace("CORE_HALF", str(core_half)).replace("DDR_HALF", str(ddr_half))
    bench = bench.replace("CASES", "\n".join(calls))
    transcript = evidence.simulate(
        f"scalar-{simulator}-{str(core_half).replace('.', '_')}-"
        f"{str(ddr_half).replace('.', '_')}", bench,
        sources=("anvil_q1_ht_ddr_scalar.sv", "anvil_q1_ht_cdc_mailbox.sv",
                 "anvil_q1_ht_reset_sync.sv"), simulator=simulator)
    records = measurement_records(transcript, "CHECKS_PASSED scalar")
    if len(records) != 1 or records[0]["completed"] != 75 or records[0]["comparisons"] <= 0:
        raise AssertionError("scalar DDR bridge comparison record missing")
    evidence.record["observations"].append({
        "scope": "scalar_DDR_CDC_protocol_not_metastability_or_physical_timing",
        "seed": seed, "simulator": simulator,
        "compute_half_period_ns": core_half, "DDR_half_period_ns": ddr_half,
        "stimulus_sha256": hashlib.sha256("\n".join(calls).encode()).hexdigest(),
        "observed": records[0],
    })
    evidence.flush()
    return records[0]


def scalar_checks(evidence, seed):
    for core_half, ddr_half in ((5, 1.875), (1.875, 5), (5, 5)):
        expected = scalar_case(evidence, "iverilog", seed, core_half, ddr_half)
        actual = scalar_case(evidence, "verilator", seed, core_half, ddr_half)
        if actual != expected:
            raise AssertionError("scalar DDR bridge simulators disagree")
