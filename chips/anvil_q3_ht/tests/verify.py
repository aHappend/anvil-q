#!/usr/bin/env python3
"""Portable, source-bound independent verification for Anvil-Q3-HT."""

import argparse
import difflib
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model import Geometry, Image, Inference
from leaf import mac_bench
from ddr import ddr_bench
from codec import codec_bench
from tensor import tensor_bench, production_tensor_bench
from arithmetic import arithmetic_bench
from image_map import map_bench
from kv import kv_bench
from ddr_faults import DDR_FAULT_TB
from checkpoint import import_checkpoint, importer_fixture
from parent import parent_bench
from parameters import INVALID_TOP, invalid_bench
from kv_context import context_bench
from tiles import tile_bench


ROOT = Path(__file__).resolve().parents[1]
SEEDS = (17, 89, 101)


def now():
    return datetime.now(timezone.utc).isoformat()


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def inventory():
    return sorted(path for pattern in ("rtl/*.sv", "design/*.md", "tests/*.py",
                                       "anvil_q3_reference/rtl/*.sv")
                  for path in ROOT.glob(pattern))


class Run:
    def __init__(self, stem, argv, preparation=False):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        base = ROOT / "evidence"
        if preparation:
            base /= "preparation"
        self.path = base / f"{stem}-{stamp}"
        self.path.mkdir(parents=True, exist_ok=False)
        self.compiled = {}
        sources = inventory()
        self.receipt = dict(argv=argv, cwd=str(ROOT), started_at=now(),
                            tool_versions={"python3": sys.version},
                            source_sha256={relative(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                           for p in sources},
                            commands=[], results=[], status="running")
        for source in sources:
            target = self.path / "sources" / relative(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        self.save()

    def save(self):
        (self.path / "receipt.json").write_text(json.dumps(self.receipt, indent=2) + "\n")

    def command(self, label, argv, cwd=None, timeout=3600):
        cwd = cwd or ROOT
        stdout, stderr = (self.path / f"{label}.{stream}.txt" for stream in ("stdout", "stderr"))
        record = dict(label=label, argv=[str(a) for a in argv], cwd=str(cwd),
                      started_at=now(), timeout_s=timeout,
                      stdout=relative(stdout), stderr=relative(stderr))
        self.receipt["commands"].append(record)
        self.save()
        start = time.monotonic()
        with stdout.open("wb") as out, stderr.open("wb") as err:
            process = subprocess.Popen(argv, cwd=cwd, stdout=out, stderr=err,
                                       start_new_session=True)
            timed_out = False
            heartbeat = start
            try:
                while True:
                    try:
                        exit_code = process.wait(timeout=30)
                        break
                    except subprocess.TimeoutExpired:
                        elapsed = time.monotonic() - start
                        if elapsed >= timeout:
                            timed_out = True
                            os.killpg(process.pid, 15)
                            try:
                                process.wait(timeout=10)
                            except subprocess.TimeoutExpired:
                                os.killpg(process.pid, 9)
                                process.wait()
                            exit_code = process.returncode
                            break
                        if time.monotonic() - heartbeat >= 30:
                            print(f"progress {label}: child running {int(elapsed)}s", flush=True)
                            heartbeat = time.monotonic()
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, 15)
                    process.wait()
        record.update(ended_at=now(), elapsed_s=time.monotonic() - start,
                      exit_code=exit_code, timed_out=timed_out)
        self.save()
        if exit_code or timed_out:
            raise RuntimeError(f"{label}: exit={exit_code}, timeout={timed_out}; "
                               f"{relative(stdout)}, {relative(stderr)}")
        return stdout.read_text()

    def tool(self, executable):
        if shutil.which(executable) is None:
            raise FileNotFoundError(f"missing executable: {executable}")
        version_flag = "-V" if executable in ("iverilog", "vvp") else "--version"
        version = self.command(f"version-{executable}", [executable, version_flag])
        self.receipt["tool_versions"][executable] = version.strip()
        self.save()

    def finish(self, error=None):
        self.receipt.update(ended_at=now(), status="failed" if error else "passed")
        if error:
            self.receipt["error"] = str(error)
        self.save()
        print(json.dumps(dict(status=self.receipt["status"],
                              receipt=relative(self.path / "receipt.json"),
                              results_count=len(self.receipt["results"]))), flush=True)


TOP_TB = r"""
module verify_top;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n=0, cancel=0, token_valid=0, new_sequence=0, token_phase=0;
  reg logit_ready=0, ddr_cal_ready=0, model_commit=0;
  reg [31:0] token_id=0, token_pos=0;
  wire token_ready, logit_valid, done, error, cancel_done, model_ready;
  wire [31:0] logit_index;
  wire signed [31:0] logit_data;
  reg host_req_valid=0, host_req_write=0, host_rsp_ready=0;
  reg [32:0] host_req_address=0;
  reg [511:0] host_req_wdata=0;
  reg [63:0] host_req_byteenable=0;
  wire host_req_ready, host_rsp_valid, host_rsp_error;
  wire [511:0] host_rsp_rdata;
  wire [32:0] avm_address;
  wire avm_read, avm_write;
  wire [511:0] avm_writedata;
  wire [63:0] avm_byteenable;
  wire [7:0] avm_burstcount;
  reg avm_waitrequest=0, avm_readdatavalid=0;
  reg [511:0] avm_readdata=0;
  reg [1:0] avm_response=0;
  reg inject_response_fault=0, fault_injected=0;
  anvil_q3_ht_top #(@PARAMETERS@) dut (
    .clk(clk), .rst_n(rst_n), .cancel(cancel),
    .token_valid(token_valid), .token_ready(token_ready),
    .token_id(token_id), .token_pos(token_pos), .new_sequence(new_sequence),
    .token_phase(token_phase), .logit_ready(logit_ready),
    .ddr_cal_ready(ddr_cal_ready), .model_commit(model_commit),
    .logit_valid(logit_valid), .logit_index(logit_index), .logit_data(logit_data),
    .done(done), .error(error), .cancel_done(cancel_done), .model_ready(model_ready),
    .host_req_valid(host_req_valid), .host_req_write(host_req_write),
    .host_req_address(host_req_address), .host_req_wdata(host_req_wdata),
    .host_req_byteenable(host_req_byteenable), .host_rsp_ready(host_rsp_ready),
    .host_req_ready(host_req_ready), .host_rsp_valid(host_rsp_valid),
    .host_rsp_rdata(host_rsp_rdata), .host_rsp_error(host_rsp_error),
    .avm_address(avm_address), .avm_read(avm_read), .avm_write(avm_write),
    .avm_writedata(avm_writedata), .avm_byteenable(avm_byteenable),
    .avm_burstcount(avm_burstcount), .avm_waitrequest(avm_waitrequest),
    .avm_readdata(avm_readdata), .avm_readdatavalid(avm_readdatavalid),
    .avm_response(avm_response)
  );
  localparam IMAGE_RECORDS=@IMAGE_RECORDS@;
  localparam MEMORY_CAPACITY=@MEMORY_CAPACITY@;
  reg [32:0] image_address [0:IMAGE_RECORDS-1];
  reg [511:0] image_data [0:IMAGE_RECORDS-1];
  reg [32:0] memory_address [0:MEMORY_CAPACITY-1];
  reg [511:0] memory_data [0:MEMORY_CAPACITY-1];
  integer memory_count=0;
  reg [32:0] queued_address [0:63];
  integer queued_beats [0:63];
  integer queued_due [0:63];
  integer queue_head=0, queue_tail=0, queue_count=0;
  integer service_rr=0;
  reg track_traffic=0;
  integer traffic_reads [0:8], traffic_writes [0:8];
  integer inference_read_stalls=0, inference_write_stalls=0, inference_useful_writes=0;
  function automatic integer traffic_class(input [32:0] address);
    begin
      traffic_class=address<33'h60000000 ? 0 : address<33'h64000000 ? 1 :
        address<33'h6c000000 ? 2 : address<33'h6d000000 ? 3 :
        address<33'h6e000000 ? 4 : address<33'h80000000 ? 5 :
        address<33'hc0000000 ? 6 : address<33'h100000000 ? 7 : 8;
    end
  endfunction
  integer cycle=0, read_commands=0, returned_beats=0, written_beats=0, image_write_beats=0;
  integer i, j, found;
  reg [32:0] held_address;
  reg [511:0] held_write;
  reg [63:0] held_enable;
  reg [7:0] held_burst;
  reg held_read=0, held_write_valid=0, stalled=0;
  reg [31:0] random_state=@SEED@;
  function automatic [31:0] next_random(input [31:0] x);
    reg [31:0] y;
    begin y=x^(x<<13); y=y^(y>>17); next_random=y^(y<<5); end
  endfunction
  task reset_check;
    begin
      if ({token_ready,logit_valid,done,error,cancel_done,model_ready,
           host_req_ready,host_rsp_valid,host_rsp_error,avm_read,avm_write} !== 11'd0)
        $fatal(1,"RESET_STATUS cycle=%0d",cycle);
      if ({logit_index,logit_data,host_rsp_rdata,avm_address,avm_writedata,
           avm_byteenable,avm_burstcount} !== 1193'd0)
        $fatal(1,"RESET_PAYLOAD cycle=%0d",cycle);
    end
  endtask
  always @(posedge clk) begin
    cycle=cycle+1;
    if (!rst_n) reset_check();
    else begin
      if (cycle>@CYCLE_LIMIT@)
        $fatal(1,"INTEGRATION_NO_COMPLETION cycle=%0d reads=%0d returns=%0d writes=%0d",
               cycle,read_commands,returned_beats,written_beats);
      if ((avm_read !== 1'b0 && avm_read !== 1'b1) ||
          (avm_write !== 1'b0 && avm_write !== 1'b1) ||
          (logit_valid !== 1'b0 && logit_valid !== 1'b1) ||
          (done !== 1'b0 && done !== 1'b1) ||
          (error !== 1'b0 && error !== 1'b1))
        $fatal(1,"PUBLIC_XZ cycle=%0d",cycle);
      if (stalled && {avm_read,avm_write,avm_address,avm_writedata,avm_byteenable,avm_burstcount}
          !== {held_read,held_write_valid,held_address,held_write,held_enable,held_burst})
        $fatal(1,"AVALON_STABILITY cycle=%0d",cycle);
      stalled=(avm_read || avm_write) && avm_waitrequest;
      if (track_traffic && avm_read && avm_waitrequest)
        inference_read_stalls=inference_read_stalls+1;
      if (track_traffic && avm_write && avm_waitrequest)
        inference_write_stalls=inference_write_stalls+1;
      held_read=avm_read; held_write_valid=avm_write; held_address=avm_address;
      held_write=avm_writedata; held_enable=avm_byteenable; held_burst=avm_burstcount;
      if (avm_read && avm_write) $fatal(1,"AVALON_READ_WRITE");
      if (avm_readdatavalid) begin
        if (queue_count==0 || cycle<queued_due[queue_head])
          $fatal(1,"SERVICE_OWNERSHIP_OR_LATENCY");
        returned_beats=returned_beats+1;
        if (avm_response!=0) fault_injected=1;
        if (track_traffic)
          traffic_reads[traffic_class(queued_address[queue_head])]=
            traffic_reads[traffic_class(queued_address[queue_head])]+64;
        service_rr=1;
        queued_address[queue_head]=queued_address[queue_head]+64;
        queued_beats[queue_head]=queued_beats[queue_head]-1;
        if (queued_beats[queue_head]==0) begin
          queue_head=(queue_head==63) ? 0 : queue_head+1;
          queue_count=queue_count-1;
        end
      end
      if ((avm_read || avm_write) && !avm_waitrequest) begin
        if (avm_address[5:0]!==0 || avm_burstcount<1 || avm_burstcount>16 ||
            {1'b0,avm_address}+34'(avm_burstcount)*64>34'h200000000 ||
            32'(avm_address[11:0])+32'(avm_burstcount)*64>4096)
          $fatal(1,"AVALON_BOUNDARY address=%h beats=%0d",avm_address,avm_burstcount);
        if (avm_read) begin
          if (queue_count>=64) $fatal(1,"SERVICE_QUEUE_FULL");
          queued_address[queue_tail]=avm_address;
          queued_beats[queue_tail]=avm_burstcount;
          queued_due[queue_tail]=cycle+12;
          queue_tail=(queue_tail==63) ? 0 : queue_tail+1;
          queue_count=queue_count+1; read_commands=read_commands+1;
        end else begin
          if (avm_burstcount!=1 || avm_readdatavalid)
            $fatal(1,"SERVICE_BYTE_BUDGET_OR_WRITE_BURST");
          found=-1;
          for (j=0;j<memory_count;j=j+1)
            if (memory_address[j]==avm_address) found=j;
          if (found<0) begin
            if (memory_count>=MEMORY_CAPACITY) $fatal(1,"MEMORY_MODEL_CAPACITY");
            found=memory_count; memory_count=memory_count+1;
            memory_address[found]=avm_address; memory_data[found]=0;
          end
          for (j=0;j<64;j=j+1)
            if (avm_byteenable[j]) memory_data[found][j*8+:8]=avm_writedata[j*8+:8];
          written_beats=written_beats+1;
          if (track_traffic) begin
            traffic_writes[traffic_class(avm_address)]=traffic_writes[traffic_class(avm_address)]+64;
            inference_useful_writes=inference_useful_writes+$countones(avm_byteenable);
          end
          service_rr=0;
          if (avm_address<33'h0c0000000) image_write_beats=image_write_beats+1;
        end
      end
    end
  end
  always @(negedge clk) begin
    if (!rst_n) begin
      reset_check(); avm_readdatavalid=0; avm_readdata=0;
    end else begin
      random_state=next_random(random_state);
      avm_readdatavalid=0; avm_readdata=0; avm_response=0;
      if (queue_count>0 && cycle+1>=queued_due[queue_head] &&
          (@STRESS@==0 || random_state[2:0]!=0) &&
          (!avm_write || service_rr==0 || (@STRESS@!=0 && random_state[5:3]==0))) begin
        found=-1;
        for (j=0;j<memory_count;j=j+1)
          if (memory_address[j]==queued_address[queue_head]) found=j;
        if (found<0) $fatal(1,"READ_UNWRITTEN_DDR address=%h",queued_address[queue_head]);
        avm_readdatavalid=1;
        avm_readdata=memory_data[found];
        if (inject_response_fault && !fault_injected) avm_response=2;
      end
      avm_waitrequest=(@STRESS@!=0 && random_state[5:3]==0) ||
        (avm_readdatavalid && avm_write);
    end
  end
  task host_write_record(input integer index);
    begin
      @(negedge clk);
      host_req_valid=1; host_req_write=1; host_req_address=image_address[index];
      host_req_wdata=image_data[index]; host_req_byteenable=64'hffffffffffffffff;
      @(posedge clk); while (!host_req_ready) @(posedge clk);
      @(negedge clk); host_req_valid=0;
      @(posedge clk); while (!host_rsp_valid) @(posedge clk);
      if (host_rsp_error !== 0 || host_rsp_rdata !== 0)
        $fatal(1,"HOST_WRITE_RESPONSE index=%0d",index);
      @(negedge clk); host_rsp_ready=1;
      @(posedge clk);
      @(negedge clk); host_rsp_ready=0;
    end
  endtask
  task host_read_record(input integer index);
    reg [512:0] held_response;
    integer pause;
    begin
      @(negedge clk);
      host_req_valid=1; host_req_write=0; host_req_address=image_address[index];
      @(posedge clk); while (!host_req_ready) @(posedge clk);
      @(negedge clk); host_req_valid=0;
      @(posedge clk); while (!host_rsp_valid) @(posedge clk);
      if (host_rsp_error !== 0 || host_rsp_rdata !== image_data[index])
        $fatal(1,"HOST_READBACK index=%0d address=%h actual=%h expected=%h",
               index,image_address[index],host_rsp_rdata,image_data[index]);
      held_response={host_rsp_error,host_rsp_rdata};
      for (pause=0;pause<2;pause=pause+1) begin
        @(posedge clk);
        if (host_rsp_valid !== 1 || {host_rsp_error,host_rsp_rdata} !== held_response)
          $fatal(1,"HOST_RESPONSE_STABILITY");
      end
      @(negedge clk); host_rsp_ready=1;
      @(posedge clk);
      @(negedge clk); host_rsp_ready=0;
    end
  endtask
  integer cancellations=0, rejected_tokens=0, readback_records=0, reset_recommits=0;
  integer fault_completions=0;
  task fault_token;
    begin
      @(negedge clk);
      token_valid=1; token_id=0; token_pos=0; new_sequence=1; token_phase=0;
      inject_response_fault=1;
      @(posedge clk); while (!token_ready) @(posedge clk);
      @(negedge clk); token_valid=0;
      @(posedge clk);
      while (!done) begin
        if (logit_valid!==0) $fatal(1,"MEMORY_FAULT_SUCCESS_SHAPED_LOGIT");
        @(posedge clk);
      end
      if (error!==1 || model_ready!==1 || queue_count!=0 || !fault_injected ||
          logit_valid!==0) $fatal(1,"MEMORY_FAULT_ERROR_COMPLETION");
      fault_completions=fault_completions+1; inject_response_fault=0;
      @(posedge clk); #1;
      if (done!==0) $fatal(1,"MEMORY_FAULT_DONE_PULSE");
    end
  endtask
  task cancel_token;
    begin
      @(negedge clk);
      token_valid=1; token_id=0; token_pos=0; new_sequence=1; token_phase=0;
      @(posedge clk); while (!token_ready) @(posedge clk);
      @(negedge clk); token_valid=0;
      @(posedge clk); while (queue_count==0) @(posedge clk);
      @(negedge clk); cancel=1;
      @(posedge clk);
      if (logit_valid !== 0 || token_ready !== 0 || cancel_done !== 0)
        $fatal(1,"CANCEL_SUPPRESSION");
      @(negedge clk); cancel=0;
      @(posedge clk);
      while (!cancel_done) begin
        if (logit_valid !== 0 || token_ready !== 0)
          $fatal(1,"CANCEL_STALE_RESULT");
        @(posedge clk);
      end
      if (queue_count!=0 || done !== 1 || error !== 1 || model_ready !== 1)
        $fatal(1,"CANCEL_DRAIN_OR_PERSISTENCE");
      cancellations=cancellations+1;
      @(posedge clk); #1;
      if (done !== 0 || cancel_done !== 0) $fatal(1,"CANCEL_PULSE");
    end
  endtask
  task reject_token(input integer id, input integer pos, input integer fresh,
                    input integer phase);
    begin
      @(negedge clk);
      token_valid=1; token_id=id; token_pos=pos; new_sequence=1'(fresh); token_phase=1'(phase);
      @(posedge clk); while (!token_ready) @(posedge clk);
      @(negedge clk); token_valid=0;
      @(posedge clk);
      while (!done) begin
        if (logit_valid !== 0) $fatal(1,"INVALID_TOKEN_LOGIT");
        @(posedge clk);
      end
      if (error !== 1 || queue_count!=0 || logit_valid !== 0 || model_ready !== 1)
        $fatal(1,"INVALID_TOKEN_COMPLETION");
      rejected_tokens=rejected_tokens+1;
      @(posedge clk); #1;
      if (done !== 0) $fatal(1,"INVALID_TOKEN_DONE_PULSE");
    end
  endtask
  reg [31:0] expected [0:@EXPECTED_LAST@];
  integer compared=0, tokens=0;
  integer loading_started=0, loading_cycles=0, readback_started=0, readback_cycles=0;
  reg logit_stalled=0;
  reg [63:0] held_logit;
  task run_token(input integer id, input integer pos, input integer fresh,
                 input integer phase, input integer expected_offset);
    integer row, started, start_reads, start_writes, start_commands;
    begin
      @(negedge clk);
      token_valid=1; token_id=id; token_pos=pos; new_sequence=1'(fresh); token_phase=1'(phase);
      @(posedge clk); while (!token_ready) @(posedge clk);
      started=cycle;
      track_traffic=1; start_reads=returned_beats; start_writes=written_beats;
      start_commands=read_commands;
      if (logit_valid !== 0) $fatal(1,"SAME_EDGE_LOGIT");
      @(negedge clk); token_valid=0;
      row=0;
      begin: token_wait
        forever begin
          @(negedge clk); logit_ready=(@STRESS@==0 || random_state[8:6]!=0);
          @(posedge clk);
          if (logit_stalled && {logit_index,logit_data} !== held_logit)
            $fatal(1,"LOGIT_STABILITY");
          logit_stalled=logit_valid && !logit_ready;
          held_logit={logit_index,logit_data};
          if (error !== 0) $fatal(1,"TOKEN_ERROR id=%0d pos=%0d cycle=%0d",id,pos,cycle);
          if (token_ready !== 0) $fatal(1,"OVERLAPPING_TOKEN_READY");
          if (logit_valid && logit_ready) begin
            if (row>=@VOCAB@ || logit_index!==32'(row) ||
                logit_data!==expected[expected_offset+row])
              $fatal(1,"LOGIT_MISMATCH token=%0d pos=%0d row=%0d index=%0d actual=%0d expected=%0d",
                     id,pos,row,logit_index,$signed(logit_data),$signed(expected[expected_offset+row]));
            row=row+1; compared=compared+1;
          end
          if (done) begin
            if (row!=@VOCAB@) $fatal(1,"LOGIT_COUNT actual=%0d",row);
            tokens=tokens+1;
            $display("TOKEN_COMPARED id=%0d pos=%0d logits=%0d cycles=%0d read_bytes=%0d write_bytes=%0d read_commands=%0d",
                     id,pos,row,cycle-started,(returned_beats-start_reads)*64,
                     (written_beats-start_writes)*64,read_commands-start_commands);
            track_traffic=0;
            disable token_wait;
          end
        end
      end
      @(negedge clk); logit_ready=0;
      @(posedge clk); #1;
      if (done !== 0) $fatal(1,"DONE_PULSE");
    end
  endtask
  initial begin
    for (i=0;i<9;i=i+1) begin traffic_reads[i]=0; traffic_writes[i]=0; end
    $readmemh("@ADDRESS_FILE@",image_address);
    $readmemh("@DATA_FILE@",image_data);
    $readmemh("@EXPECTED_FILE@",expected);
    #1; reset_check();
    repeat(3) @(negedge clk);
    rst_n=1; ddr_cal_ready=1;
    loading_started=cycle;
    for (i=0;i<IMAGE_RECORDS;i=i+1) host_write_record(i);
    loading_cycles=cycle-loading_started; readback_started=cycle;
    for (i=0;i<IMAGE_RECORDS;i=i+1) begin
      host_read_record(i);
      readback_records=readback_records+1;
    end
    readback_cycles=cycle-readback_started;
    // Reset retains the byte-memory image but removes the committed readiness.
    @(negedge clk); #1; rst_n=0;
    #1; reset_check();
    repeat(3) @(negedge clk);
    rst_n=1;
    @(posedge clk); while (!host_req_ready) begin
      if (token_ready !== 0 || model_ready !== 0) $fatal(1,"RESET_COMMIT_GATING");
      @(posedge clk);
    end
    @(negedge clk); model_commit=1;
    @(posedge clk);
    @(negedge clk); model_commit=0;
    if (model_ready !== 1) $fatal(1,"MODEL_COMMIT");
    reset_recommits=reset_recommits+1;
    @TOKENS@
    if (compared!=@EXPECTED_COUNT@ || tokens!=@TOKEN_COUNT@ || queue_count!=0)
      $fatal(1,"INTEGRATION_COVERAGE");
    if (readback_records!=IMAGE_RECORDS || reset_recommits!=1 || image_write_beats!=IMAGE_RECORDS)
      $fatal(1,"PERSISTENT_IMAGE_COVERAGE");
    $display("INTEGRATION_PASS tokens=%0d compared=%0d reads=%0d beats=%0d writes=%0d readback=%0d reset_recommit=%0d cancellations=%0d rejected_tokens=%0d fault_completions=%0d",
             tokens,compared,read_commands,returned_beats,written_beats,
             readback_records,reset_recommits,cancellations,rejected_tokens,fault_completions);
    for (i=0;i<9;i=i+1)
      $display("HT_TRAFFIC class=%0d read_bytes=%0d write_bytes=%0d",
               i,traffic_reads[i],traffic_writes[i]);
    $display("HT_SERVICE read_stalls=%0d write_stalls=%0d useful_write_bytes=%0d queue_capacity=64",
             inference_read_stalls,inference_write_stalls,inference_useful_writes);
    $display("HT_LOADER write_beats=%0d write_cycles=%0d readback_beats=%0d readback_cycles=%0d",
             image_write_beats,loading_cycles,readback_records,readback_cycles);
    $finish;
  end
endmodule
"""


def simulate(run, label, bench, simulator="verilator", top="verify_top", rtl_directory=None,
             normalize=True):
    source = run.path / f"{label}.sv"
    source.write_text(bench)
    rtl = [relative(p) for p in sorted((rtl_directory or ROOT / "rtl").glob("*.sv"))]
    if simulator == "iverilog":
        binary = run.path / f"{label}.vvp"
        run.command(f"{label}-compile", ["iverilog", "-g2012", "-Wall", "-s", top,
                                        "-o", relative(binary), *rtl, relative(source)])
        return run.command(f"{label}-simulate", ["vvp", relative(binary)], timeout=600)
    fixtures = []

    def fixture(match):
        index = len(fixtures)
        fixtures.append(match[1])
        return f"$readmemh(verify_runtime::fixture({index}),"

    compiled_bench = re.sub(r'\$readmemh\("([^"]+)",', fixture, bench)
    seed_values = re.findall(r"\b(?:random_state|rng)\s*=\s*(17|89|101)\s*;", compiled_bench)
    seed = int(seed_values[0]) if seed_values else 17
    compiled_bench = re.sub(
        r"\b(random_state|rng)\s*=\s*(17|89|101)\s*;",
        r"\1=verify_runtime::seed();", compiled_bench)
    compiled_bench = re.sub(r"\bseed=(17|89|101)\b", "seed=runtime", compiled_bench)
    compiled_bench = re.sub(r"\(id\*17\+(17|89|101)\)%65",
                            "(id*17+verify_runtime::seed())%65", compiled_bench)
    runtime_package = """
package verify_runtime;
  function automatic string fixture(input integer index);
    string value;
    if (!$value$plusargs($sformatf("verify_fixture%0d=%%s",index),value))
      $fatal(1,"MISSING_RUNTIME_FIXTURE index=%0d",index);
    return value;
  endfunction
  function automatic integer seed();
    integer value;
    if (!$value$plusargs("verify_seed=%d",value)) $fatal(1,"MISSING_RUNTIME_SEED");
    return value;
  endfunction
endpackage
"""
    compiled_bench = runtime_package + compiled_bench
    if not normalize:
        compiled_bench = bench
    compiled_source = run.path / f"{label}-compiled.sv"
    compiled_source.write_text(compiled_bench)
    digest = hashlib.sha256(compiled_bench.encode() + top.encode())
    for path in rtl:
        digest.update(path.encode())
        digest.update((ROOT / path).read_bytes())
    identity = digest.hexdigest()
    runtime_arguments = [f"+verify_seed={seed}", *(
        f"+verify_fixture{index}={path}" for index, path in enumerate(fixtures))]
    if identity in run.compiled:
        binary = run.compiled[identity]
        run.receipt.setdefault("compile_reuse", []).append(dict(
            case=label, identity=identity, binary=relative(binary),
            source=relative(compiled_source), runtime_arguments=runtime_arguments))
        run.save()
        return run.command(f"{label}-simulate", [relative(binary), *runtime_arguments])
    objects = run.path / f"{label}-compile-obj"
    try:
        run.command(f"{label}-compile",
                    ["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                     "--top-module", top, "--Mdir", relative(objects),
                     "-o", f"../{label}.bin", *rtl, relative(compiled_source)])
        binary = run.path / f"{label}.bin"
        run.compiled[identity] = binary
        return run.command(f"{label}-simulate", [relative(binary), *runtime_arguments])
    finally:
        if objects.exists():
            shutil.rmtree(objects)


def integration(run, seed=17, banks=1, mode=0, tokens=1, layers=1, stress=False,
                simulator="verilator", hidden=16, intermediate=16, tile_rows=1,
                prefix="", rtl_directory=None, kv_heads=1, overrides=None, context=3,
                benchmark=False, memory_fault=False):
    geometry = Geometry(layers=layers, hidden=hidden, intermediate=intermediate,
                        q_heads=8 * kv_heads, kv_heads=kv_heads,
                        head_dim=hidden // (8 * kv_heads), context=context)
    image = Image(geometry, seed)
    oracle = Inference(image, mode)
    sequence = [(0, 0, True, 0)]
    if tokens > 1:
        sequence += [(1, 1, False, 1), (2, 0, True, 0)]
    sequence = sequence[:tokens]
    expected = [value for token, pos, fresh, _ in sequence
                for value in oracle.token(token, pos, fresh)]
    label = (f"{prefix}integration-h{hidden}-i{intermediate}-r{tile_rows}-l{layers}"
             f"-b{banks}-m{mode}-s{seed}-{simulator}")
    image_directory = run.path / "checkpoint-images"
    image_directory.mkdir(exist_ok=True)
    addresses, data, reference = (image_directory / f"{label}-{suffix}.hex"
                                  for suffix in ("address", "data", "expected"))
    records = image.records()
    addresses.write_text("".join(f"{address:09x}\n" for address, _ in records))
    data.write_text("".join(f"{int.from_bytes(record, 'little'):0128x}\n"
                            for _, record in records))
    reference.write_text("".join(f"{value & 0xFFFFFFFF:08x}\n" for value in expected))
    parameters = geometry.parameters() | dict(BANKS=banks, CACHE_MODE=mode, TILE_K=16,
                                              TILE_ROWS=tile_rows, TILE_SLOTS=3, QUEUE_DEPTH=3,
                                              KV_RESIDENT_GROUPS=3)
    parameters.update(overrides or {})
    token_commands = []
    if memory_fault:
        token_commands += ["fault_token();"]
    for index, (token, pos, fresh, phase) in enumerate(sequence):
        if tokens > 1 and index == 2 and not benchmark:
            token_commands += ["reject_token(0,2,0,0);", "cancel_token();"]
        token_commands.append(f"run_token({token},{pos},{int(fresh)},{phase},"
                              f"{index * geometry.vocab});")
    if tokens > 1 and not benchmark:
        token_commands += [f"reject_token({geometry.vocab},0,1,0);",
                           "reject_token(0,1,1,0);", "reject_token(0,2,0,0);",
                           "if (cancellations!=1 || rejected_tokens!=4) "
                           '$fatal(1,"TOKEN_ERROR_COVERAGE");']
    if memory_fault:
        token_commands += ['if (fault_completions!=1) $fatal(1,"MEMORY_FAULT_COVERAGE");']
    replacements = dict(PARAMETERS=",".join(f".{key}({value})" for key, value in parameters.items()),
                        IMAGE_RECORDS=len(records), MEMORY_CAPACITY=len(records) + 1024,
                        ADDRESS_FILE=relative(addresses), DATA_FILE=relative(data),
                        EXPECTED_FILE=relative(reference), EXPECTED_LAST=len(expected) - 1,
                        EXPECTED_COUNT=len(expected), TOKEN_COUNT=len(sequence), VOCAB=geometry.vocab,
                        SEED=seed, STRESS=int(stress),
                        CYCLE_LIMIT=500000 if simulator == "iverilog" else 2000000 * layers * len(sequence),
                        TOKENS="\n".join(token_commands))
    bench = TOP_TB
    for key, value in replacements.items():
        bench = bench.replace(f"@{key}@", str(value))
    if benchmark:
        from benchmark import component_monitors
        bench += component_monitors(run.path, relative, oracle, geometry, parent=False, banks=banks)
    output = simulate(run, label, bench, simulator, rtl_directory=rtl_directory)
    if "INTEGRATION_PASS" not in output:
        raise AssertionError(f"{label}: missing completion record")
    run.receipt["results"].append(dict(case=label, geometry=geometry.__dict__, seed=seed,
                                       parameters=parameters,
                                       banks=banks, cache_mode=mode, image_kind="synthetic",
                                       image_sha256=image.digest, logits=expected,
                                       compared=len(expected), tokens=len(sequence), summary=output))
    run.save()
    return run.receipt["results"][-1]


def synthesis_target(run, label, top, parameters=None, noopt=False):
    parameters = parameters or {}
    script = run.path / f"{label}-synthesis.ys"
    netlist = run.path / f"{label}-netlist.json"
    rtl = " ".join(relative(p) for p in sorted((ROOT / "rtl").glob("*.sv")))
    script.write_text(
        f"read_verilog -defer -sv {'-noopt ' if noopt else ''}{rtl}\n"
        + ("chparam " + " ".join(f"-set {key} {value}" for key, value in parameters.items())
           + f" {top}\n" if parameters else "")
        + f"hierarchy -check -top {top}\n"
        + "proc\nopt_expr\nopt_clean\ncheck -assert\n"
        + "memory -nomap\nopt_clean\ncheck -assert\nstat\n"
        + f"write_json {relative(netlist)}\n")
    run.command(f"{label}-synthesis", ["yosys", "-s", relative(script)])
    modules = json.loads(netlist.read_text())["modules"]
    cell_types = {}
    memory_bits = 0
    for module in modules.values():
        for cell in module.get("cells", {}).values():
            kind = cell["type"]
            cell_types[kind] = cell_types.get(kind, 0) + 1
            if kind in ("$dlatch", "$adlatch", "$dlatchsr", "$div", "$mod",
                        "$divfloor", "$modfloor"):
                raise AssertionError(f"forbidden synthesis cell {kind}")
            if kind == "$mem_v2":
                memory_bits += (int(cell["parameters"]["WIDTH"], 2)
                                * int(cell["parameters"]["SIZE"], 2))
    top_module = modules[top]
    if not top_module.get("cells") or not cell_types.get("$adff"):
        raise AssertionError(f"{label}: no connected sequential hierarchy")
    required = ("token_controller", "decoder_layer", "ddr_arbiter", "ddr_prefetcher",
                "tile_buffers", "tensor_array", "kv_hierarchy", "host_loader", "scratchpad")
    if top == "anvil_q3_ht_top":
        for instance in required:
            cell = top_module["cells"].get(instance)
            if cell is None or cell["type"] not in modules:
                raise AssertionError(f"missing reachable hierarchy instance {instance}")
            live = [bit for connection in cell["connections"].values()
                    for bit in connection if isinstance(bit, int)]
            if not live:
                raise AssertionError(f"disconnected hierarchy instance {instance}")
    if top == "anvil_q3_ht_tensor_array":
        for bank in range(16):
            instance = top_module["cells"].get(f"banks[{bank}].mac16")
            if instance is None:
                raise AssertionError(f"missing production tensor bank {bank}")
            mac_module = modules[instance["type"]]
            for lane in range(16):
                for stage in ("weight2", "product_low3", "product_high3", "product4"):
                    name = f"lanes[{lane}].{stage}"
                    if name not in mac_module["netnames"]:
                        raise AssertionError(f"missing physical lane pipeline {bank}/{name}")
            for level in range(5, 8):
                for node in range(1 << (8 - level)):
                    if f"reduction{level}[{node}].sum" not in mac_module["netnames"]:
                        raise AssertionError(f"missing registered reduction level {level}")
            if "sum8" not in mac_module["netnames"]:
                raise AssertionError("missing final registered reduction")
    if top in ("anvil_q3_ht_ddr_prefetcher", "anvil_q3_ht_kv_hierarchy") and memory_bits == 0:
        raise AssertionError(f"{label}: missing inferred storage")
    run.receipt["results"].append(dict(case=f"{label}-synthesis", top=top,
                                       parameters=parameters, modules=len(modules),
                                       memory_bits=memory_bits, cell_types=cell_types))
    run.save()


def synthesis(run, noopt=False):
    parameters = Geometry().parameters() | dict(BANKS=1, TILE_K=16, TILE_ROWS=1,
                                                TILE_SLOTS=3, KV_RESIDENT_GROUPS=3)
    synthesis_target(run, "integrated", "anvil_q3_ht_top", parameters, noopt)
    synthesis_target(run, "production-tensor", "anvil_q3_ht_tensor_array", noopt=noopt)
    synthesis_target(run, "production-prefetch", "anvil_q3_ht_ddr_prefetcher", noopt=noopt)
    for mode in range(3):
        synthesis_target(run, f"production-kv-mode{mode}", "anvil_q3_ht_kv_hierarchy",
                         dict(CACHE_MODE=mode), noopt)


def frontend_probe(run):
    cases = {
        "round-wire": """input wire signed [127:0] x, output wire signed [31:0] y);
          assign y=anvil_q3_pkg::round_shift_sat32(x,48); endmodule""",
        "round-clocked": """input wire clk, input wire signed [127:0] x,
          output reg [31:0] y);
          always @(posedge clk) y<=anvil_q3_pkg::round_shift_sat32(x,48); endmodule""",
        "half-clocked": """input wire clk, input wire [15:0] x,
          output reg signed [31:0] y);
          always @(posedge clk) y<=anvil_q3_pkg::f16_q16(x); endmodule""",
        "parent-rmsnorm": None,
    }
    failures = []
    for label, body in cases.items():
        if body is None:
            sources = "anvil_q3_reference/rtl/anvil_q3_00_pkg.sv anvil_q3_reference/rtl/anvil_q3_rmsnorm.sv"
        else:
            source = run.path / f"{label}.sv"
            source.write_text("module frontend_probe(" + body + "\n")
            sources = f"rtl/anvil_q3_00_pkg.sv {relative(source)}"
        try:
            run.command(label, ["yosys", "-p", f"read_verilog -sv {sources}"])
            status = "passed"
        except RuntimeError:
            status = "failed"
            failures.append(label)
        run.receipt["results"].append(dict(case=label, status=status))
        run.save()
    if failures:
        raise RuntimeError(f"frontend diagnostic failures: {failures}")


def rmsnorm_frontend_variants(run):
    original = ROOT / "anvil_q3_reference/rtl/anvil_q3_rmsnorm.sv"
    text = original.read_text()
    substitutions = {
        "signed-multiply-branch": (
            "scaled_x : {{32{x[31]}},x}", "scaled_x : $signed({{32{x[31]}},x})"),
        "accumulator-port-cast": (".in_value($signed(square))", ".in_value(square)"),
        "adder-port-cast": (".in_a($signed(mean))", ".in_a(mean)"),
        "unsigned-size-cast": ("64'(HIDDEN_SIZE)", "$unsigned(64'(HIDDEN_SIZE))"),
    }
    cast_section = text[text.index("  anvil_q3_accumulator sum_accumulator"):
                        text.index("  anvil_q3_divider #")]
    substitutions["both-port-casts"] = (
        cast_section, cast_section.replace("$signed(square)", "square")
        .replace("$signed(mean)", "mean"))
    failures = []
    for label, (before, after) in substitutions.items():
        if text.count(before) != 1:
            raise AssertionError(f"diagnostic substitution not unique: {label}")
        source = run.path / f"{label}.sv"
        source.write_text(text.replace(before, after))
        patch = run.path / f"{label}.patch.json"
        patch.write_text(json.dumps(dict(original=relative(original),
                                         original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                                         before=before, after=after,
                                         purpose="frontend-only diagnostic; not functional acceptance"),
                                    indent=2) + "\n")
        try:
            run.command(label, ["yosys", "-p", "read_verilog -sv "
                                f"rtl/anvil_q3_00_pkg.sv {relative(source)}"])
            status = "passed"
        except RuntimeError:
            status = "failed"
            failures.append(label)
        run.receipt["results"].append(dict(case=label, status=status,
                                           patch=relative(patch)))
        run.save()
    if failures:
        raise RuntimeError(f"frontend diagnostic failures: {failures}")


def rmsnorm_frontend_parts(run):
    original = ROOT / "anvil_q3_reference/rtl/anvil_q3_rmsnorm.sv"
    text = original.read_text()
    start = text.index("  anvil_q3_mem_port memory_port (")
    sequential = text.index("  always @(posedge clk")
    prefix = text[:start]
    parts = dict(declarations=prefix + "endmodule\n",
                 sequential=prefix + text[sequential:])
    cursor = start
    while cursor < sequential:
        end = text.index("\n  );", cursor) + len("\n  );")
        instance = text[cursor:end]
        label = instance.split(" (")[0].split()[-1]
        parts[f"instance-{label}"] = prefix + instance + "\nendmodule\n"
        cursor = end
        while cursor < sequential and text[cursor].isspace():
            cursor += 1
    failures = []
    for label, body in parts.items():
        source = run.path / f"{label}.sv"
        source.write_text(body)
        try:
            run.command(label, ["yosys", "-p", "read_verilog -sv "
                                f"rtl/anvil_q3_00_pkg.sv {relative(source)}"])
            status = "passed"
        except RuntimeError:
            status = "failed"
            failures.append(label)
        run.receipt["results"].append(dict(case=label, status=status,
                                           purpose="frontend-only extracted source diagnostic"))
        run.save()
    if failures:
        raise RuntimeError(f"frontend diagnostic failures: {failures}")


def compare_leaf(run, label, bench, top, marker, simulator="verilator"):
    output = simulate(run, label, bench, simulator, top)
    if marker not in output:
        raise AssertionError(f"{label}: missing nonempty comparison completion")
    run.receipt["results"].append(dict(case=label, summary=output))
    run.save()


def smoke_suite(run):
    run.tool("iverilog")
    run.tool("vvp")
    compare_leaf(run, "arithmetic", arithmetic_bench(run.path, relative),
                 "verify_arithmetic", "ARITHMETIC_PASS", "iverilog")
    compare_leaf(run, "mac-smoke", mac_bench(run.path, relative, 17),
                 "verify_mac", "MAC_PASS", "iverilog")
    compare_leaf(run, "tile-first-transfer", tile_bench(compact=True, compact_banks=2),
                 "verify_tiles", "TILE_FIRST_CONSUME_PASS", "iverilog")
    bench, layout = map_bench(run.path, relative)
    compare_leaf(run, "production-image-map", bench, "verify_map", "IMAGE_MAP_PASS", "iverilog")
    run.receipt["results"].append(dict(case="production-image-layout", layout=layout))
    integration(run, simulator="iverilog")
    parameter_rejections(run)


def parameter_rejections(run):
    for label, overrides in INVALID_TOP:
        try:
            simulate(run, f"invalid-{label}", invalid_bench(overrides),
                     "iverilog", "verify_parameters")
        except RuntimeError:
            command = run.receipt["commands"][-1]
            output = (ROOT / command["stdout"]).read_text() + (ROOT / command["stderr"]).read_text()
            if (not command["label"].endswith("-simulate") or command["timed_out"]
                    or not command["exit_code"] or "PARAMETER ERROR" not in output
                    or "MISSING_PARAMETER_DIAGNOSTIC" in output):
                raise
        else:
            raise AssertionError(f"illegal geometry accepted: {label}")
        run.receipt["results"].append(dict(case=f"invalid-{label}", parameters=overrides,
                                           result="explicit-parameter-rejection",
                                           command=command["label"]))
        run.save()


def behavior_suite(run):
    run.tool("verilator")
    compare_leaf(run, "arithmetic", arithmetic_bench(run.path, relative),
                 "verify_arithmetic", "ARITHMETIC_PASS")
    for seed in SEEDS:
        compare_leaf(run, f"mac-s{seed}", mac_bench(run.path, relative, seed),
                     "verify_mac", "MAC_PASS")
        compare_leaf(run, f"tensor-s{seed}", tensor_bench(run.path, relative, seed),
                     "verify_tensor", "TENSOR_PASS")
        compare_leaf(run, f"production-tensor-s{seed}",
                     production_tensor_bench(run.path, relative, seed),
                     "verify_tensor", "PRODUCTION_TENSOR_PASS")
        for banks in (1, 2, 4, 8, 16):
            for mode in range(3):
                integration(run, seed=seed, banks=banks, mode=mode, tokens=3,
                            stress=True, intermediate=24, tile_rows=8)
        integration(run, seed=seed, banks=16, mode=2, tokens=3, hidden=32,
                    intermediate=32, tile_rows=8, kv_heads=2, stress=True,
                    prefix="integrated-boundaries-",
                    overrides=dict(TILE_K=128, TILE_SLOTS=2, QUEUE_DEPTH=1,
                                   BURST_BEATS=1, KV_RESIDENT_GROUPS=1))
    integration(run, banks=16, context=1, prefix="singleton-context-")
    integration(run, layers=36, banks=16)


def ddr_suite(run):
    run.tool("verilator")
    run.receipt["results"].append(importer_fixture(ROOT, run.path))
    run.save()
    compare_leaf(run, "ddr-fault-boundaries", DDR_FAULT_TB,
                 "verify_ddr_faults", "DDR_FAULT_PASS")
    for seed in SEEDS:
        for slots in (2, 3, 4):
            compare_leaf(run, f"tiles-slots{slots}-s{seed}", tile_bench(slots, seed),
                         "verify_tiles", "TILE_PASS")
        for queue, burst in ((1, 1), (3, 16), (16, 16)):
            compare_leaf(run, f"ddr-q{queue}-b{burst}-s{seed}",
                         ddr_bench(seed, queue, burst, stress=True),
                         "verify_ddr", "DDR_PASS")
        compare_leaf(run, f"ddr-stream-s{seed}", ddr_bench(seed, stress=False),
                     "verify_ddr", "DDR_PASS")
        integration(run, seed=seed, banks=16, mode=0, tokens=3,
                    stress=True, prefix="persistence-", memory_fault=True)


def kv_suite(run):
    run.tool("verilator")
    for mode in range(3):
        compare_leaf(run, f"codec-m{mode}", codec_bench(run.path, relative, mode),
                     "verify_codec", "CODEC_PASS")
        compare_leaf(run, f"full-context-m{mode}", context_bench(run.path, relative, mode),
                     "verify_kv_context", "KV_CONTEXT_PASS")
        for seed in SEEDS:
            for resident in (1, 3, 64):
                compare_leaf(run, f"kv-m{mode}-r{resident}-s{seed}",
                             kv_bench(run.path, relative, mode, resident, seed,
                                      dim=258 if resident == 64 else 66),
                             "verify_kv", "KV_HIERARCHY_PASS")
            integration(run, seed=seed, banks=16, mode=mode, tokens=3,
                        hidden=32, intermediate=32, stress=True, prefix="gqa-two-kv-",
                        kv_heads=2)


def reproduce_suite(run):
    for tool in ("python3", "iverilog", "vvp", "yosys"):
        run.tool(tool)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = run.path / f"clean-reproduction-{stamp}"
    directory.mkdir()
    for source in inventory():
        target = directory / relative(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    commands = (
        ("fixture", ["python3", "tests/verify.py", "--probe", "importer"]),
        ("numerical", ["python3", "tests/verify.py", "--probe", "integration",
                       "--simulator", "iverilog"]),
        ("synthesis", ["python3", "tests/verify.py", "--probe", "synthesis-compact"]))
    for label, argv in commands:
        output = run.command(f"reproduce-{label}", argv, cwd=directory)
        records = [json.loads(line) for line in output.splitlines() if line.startswith('{"status":')]
        if (len(records) != 1 or records[0]["status"] != "passed"
                or not records[0]["results_count"]):
            raise AssertionError(f"clean reproduction lacks successful comparisons: {label}")
        child_receipt = directory / records[0]["receipt"]
        if not child_receipt.resolve().is_relative_to(directory.resolve()):
            raise AssertionError("clean reproduction receipt escaped retained clean directory")
        child = json.loads(child_receipt.read_text())
        if child["status"] != "passed" or not child["results"]:
            raise AssertionError(f"clean reproduction receipt is incomplete: {label}")
        run.receipt["results"].append(dict(case=f"clean-{label}", result=records[0],
                                           child_receipt=relative(child_receipt),
                                           directory=relative(directory)))
        run.save()


def benchmark_suite(run):
    from benchmark import execute_benchmark
    execute_benchmark(run, integration, simulate, relative, ROOT)


def mutation_suite(run, only=None):
    run.tool("verilator")
    benches = dict(
        arithmetic=(arithmetic_bench(run.path, relative), "verify_arithmetic", "ARITHMETIC_PASS"),
        mac=(mac_bench(run.path, relative, 17), "verify_mac", "MAC_PASS"),
        ddr=(ddr_bench(stress=True), "verify_ddr", "DDR_PASS"),
        codec=(codec_bench(run.path, relative, 2), "verify_codec", "CODEC_PASS"))
    mutations = (
        ("awq-lane-permutation", "anvil_q3_00_pkg.sv",
         "3'd1: awq_lane_shift = 5'd16;", "3'd1: awq_lane_shift = 5'd4;",
         "arithmetic", "AWQ_LANE_MAPPING"),
        ("dropped-active-lane", "anvil_q3_ht_mac16.sv",
         "assign lane_products[lane*69+:69]=product4;",
         "assign lane_products[lane*69+:69]=lane==0 ? 69'd0 : product4;",
         "mac", "MAC_NUMERICAL"),
        ("wrong-signed-rounding", "anvil_q3_00_pkg.sv",
         "!x[127] && fraction>=half", "!x[127] && fraction>half",
         "arithmetic", "SIGNED_ROUNDING"),
        ("lost-return-beat", "anvil_q3_ht_ddr_prefetcher.sv",
         "if (return_store) return_memory[r_write]<=return_word;",
         "if (return_store && r_write!=0) return_memory[r_write]<=return_word;",
         "ddr", "DDR_ORDERED_BEAT"),
        ("compressed-kv-sign", "anvil_q3_ht_kv_codec.sv",
         "{{5{payload_lane[3]}},payload_lane[3:0]}", "{5'd0,payload_lane[3:0]}",
         "codec", "KV_CODEC_NUMERICAL"),
        ("wrong-gqa-head", "anvil_q3_ht_attention.sv",
         "kv_cmd_valid ? head>>3", "kv_cmd_valid ? head>>2",
         "integration", "TOKEN_ERROR"))
    if only is not None:
        mutations = tuple(case for case in mutations if case[0] == only)
        if not mutations:
            raise ValueError(f"unknown source mutant: {only}")
    required_harnesses = {case[4] for case in mutations}
    for name, (bench, top, marker) in benches.items():
        if name in required_harnesses:
            compare_leaf(run, f"pristine-{name}", bench, top, marker)
    if "integration" in required_harnesses:
        integration(run, prefix="pristine-gqa-")
    for name, filename, before, after, harness, assertion in mutations:
        directory = run.path / f"mutant-{name}"
        directory.mkdir()
        for source in sorted((ROOT / "rtl").glob("*.sv")):
            shutil.copyfile(source, directory / source.name)
        path = directory / filename
        original = path.read_text()
        if original.count(before) != 1:
            raise AssertionError(f"mutation target must be unique: {name}")
        changed = original.replace(before, after)
        path.write_text(changed)
        patch = directory / "mutation.patch"
        patch.write_text("".join(difflib.unified_diff(
            original.splitlines(keepends=True), changed.splitlines(keepends=True),
            fromfile=f"rtl/{filename}", tofile=f"mutant/{filename}")))
        try:
            if harness == "integration":
                integration(run, prefix=f"mutant-{name}-", rtl_directory=directory)
            else:
                bench, top, _ = benches[harness]
                simulate(run, f"mutant-{name}", bench, top=top, rtl_directory=directory)
        except RuntimeError:
            command = run.receipt["commands"][-1]
            output = (ROOT / command["stdout"]).read_text() + (ROOT / command["stderr"]).read_text()
            if (not command["label"].endswith("-simulate") or command["timed_out"]
                    or not command["exit_code"] or assertion not in output):
                raise
        else:
            raise AssertionError(f"undetected source mutant: {name}")
        run.receipt["results"].append(dict(
            case=name, result="detected", assertion=assertion,
            patch=relative(patch), command=command["label"],
            pristine_source_sha256=hashlib.sha256(original.encode()).hexdigest(),
            mutant_source_sha256=hashlib.sha256(changed.encode()).hexdigest()))
        run.save()
    if sum(result.get("result") == "detected" for result in run.receipt["results"]) != len(mutations):
        raise AssertionError("every selected mutation class must be detected")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    entry = parser.add_mutually_exclusive_group(required=True)
    entry.add_argument("--suite", choices=("smoke", "behavior", "ddr4", "kv-gqa", "benchmark",
                                                                             "mutations", "synthesis", "reproduce"))
    entry.add_argument("--probe", choices=("integration", "mac", "ddr", "codec", "tensor", "mutation",
                                           "arithmetic", "image-map", "kv", "kv-context", "tiles", "tiles-compact", "tiles-raw",
                                           "production-tensor",
                                           "ddr-faults", "importer", "parent", "parameters",
                                           "reproduce",
                                           "benchmark-components", "benchmark-stream", "benchmark-cell", "cache-reuse", "synthesis",
                                           "synthesis-compact", "frontend",
                                                                              "frontend-variants", "frontend-parts"))
    entry.add_argument("--import-checkpoint", help="Project-relative local safetensors checkpoint")
    parser.add_argument("--checkpoint-revision", help="Explicit checkpoint repository revision")
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="verilator")
    parser.add_argument("--seed", type=int, choices=SEEDS, default=17)
    parser.add_argument("--banks", type=int, choices=(1, 2, 4, 8, 16), default=1)
    parser.add_argument("--mode", type=int, choices=(0, 1, 2), default=0)
    parser.add_argument("--tokens", type=int, choices=(1, 3), default=1)
    parser.add_argument("--layers", type=int, choices=(1, 36), default=1)
    parser.add_argument("--hidden", type=int, choices=(16, 32, 64, 128), default=16)
    parser.add_argument("--intermediate", type=int, default=16)
    parser.add_argument("--tile-rows", type=int, choices=(1, 8), default=1)
    parser.add_argument("--tile-k", type=int, choices=(16, 32, 64, 128), default=16)
    parser.add_argument("--tile-slots", type=int, choices=(2, 3, 4), default=3)
    parser.add_argument("--queue-depth", type=int, choices=(1, 3, 16), default=3)
    parser.add_argument("--burst-beats", type=int, choices=(1, 2, 4, 8, 16), default=16)
    parser.add_argument("--resident", type=int, choices=(1, 3, 64), default=3)
    parser.add_argument("--kv-heads", type=int, choices=(1, 2), default=1)
    parser.add_argument("--context", type=int, choices=(1, 3, 32768), default=3)
    parser.add_argument("--stress", action="store_true")
    parser.add_argument("--memory-fault", action="store_true")
    parser.add_argument("--repair-of", help="Project-relative earlier preparation receipt")
    parser.add_argument("--yosys-noopt", action="store_true")
    parser.add_argument("--mutation-class", choices=(
        "awq-lane-permutation", "dropped-active-lane", "wrong-signed-rounding",
        "lost-return-beat", "compressed-kv-sign", "wrong-gqa-head"),
        default="wrong-signed-rounding")
    args = parser.parse_args()
    run = Run(args.suite or args.probe or "checkpoint-import", [sys.executable, *sys.argv],
              preparation=not args.suite and not args.import_checkpoint)
    if args.repair_of:
        prior = ROOT / args.repair_of
        if not prior.is_file() or not prior.resolve().is_relative_to(ROOT / "evidence"):
            parser.error("--repair-of must name an existing project evidence receipt")
        run.receipt["repair_of"] = args.repair_of
        run.save()
    try:
        if args.suite:
            if args.suite == "synthesis":
                run.tool("yosys")
                synthesis(run)
            else:
                {"smoke": smoke_suite, "behavior": behavior_suite, "mutations": mutation_suite,
                 "ddr4": ddr_suite, "kv-gqa": kv_suite, "reproduce": reproduce_suite,
                 "benchmark": benchmark_suite}[args.suite](run)
            run.finish()
            return 0
        if args.import_checkpoint:
            manifest = import_checkpoint(ROOT, args.import_checkpoint,
                                         relative(run.path / "checkpoint-images"),
                                         args.checkpoint_revision)
            run.receipt["results"].append(dict(
                case="checkpoint-import", manifest=relative(run.path / "checkpoint-images/manifest.json"),
                image_kind=manifest["image_kind"], revision=manifest["revision"],
                regions=manifest["regions"]))
            run.finish()
            return 0
        if args.probe == "importer":
            run.receipt["results"].append(importer_fixture(ROOT, run.path))
            run.finish()
            return 0
        if args.probe == "parameters":
            run.tool("iverilog")
            run.tool("vvp")
            parameter_rejections(run)
            run.finish()
            return 0
        if args.probe == "reproduce":
            reproduce_suite(run)
            run.finish()
            return 0
        if args.probe == "mutation":
            mutation_suite(run, only=args.mutation_class)
            run.finish()
            return 0
        if args.probe in ("synthesis", "synthesis-compact", "frontend", "frontend-variants", "frontend-parts"):
            run.tool("yosys")
            if args.probe == "synthesis":
                synthesis(run, args.yosys_noopt)
            elif args.probe == "synthesis-compact":
                synthesis_target(run, "integrated", "anvil_q3_ht_top",
                                 Geometry().parameters() | dict(BANKS=1, TILE_K=16,
                                 TILE_ROWS=1, TILE_SLOTS=3, KV_RESIDENT_GROUPS=3))
            elif args.probe == "frontend":
                frontend_probe(run)
            elif args.probe == "frontend-variants":
                rmsnorm_frontend_variants(run)
            else:
                rmsnorm_frontend_parts(run)
        else:
            run.tool(args.simulator)
            if args.simulator == "iverilog":
                run.tool("vvp")
        if args.probe == "mac":
            output = simulate(run, f"mac-s{args.seed}-{args.simulator}",
                              mac_bench(run.path, relative, args.seed),
                              args.simulator, "verify_mac")
            if "MAC_PASS" not in output:
                raise AssertionError("MAC experiment produced no completion record")
            run.receipt["results"].append(dict(case="mac", seed=args.seed, summary=output))
        elif args.probe == "integration":
            integration(run, args.seed, args.banks, args.mode, args.tokens, args.layers,
                        args.stress, args.simulator, args.hidden, args.intermediate,
                        args.tile_rows, kv_heads=args.kv_heads, context=args.context,
                        overrides=dict(TILE_K=args.tile_k, TILE_SLOTS=args.tile_slots,
                                       QUEUE_DEPTH=args.queue_depth, BURST_BEATS=args.burst_beats,
                                       KV_RESIDENT_GROUPS=args.resident),
                        memory_fault=args.memory_fault)
        elif args.probe == "ddr":
            output = simulate(run, f"ddr-s{args.seed}",
                              ddr_bench(args.seed, args.queue_depth, args.burst_beats,
                                        stress=args.stress),
                              args.simulator, "verify_ddr")
            if "DDR_PASS" not in output:
                raise AssertionError("DDR experiment produced no completion record")
            run.receipt["results"].append(dict(case="ddr", seed=args.seed, summary=output))
        elif args.probe == "codec":
            output = simulate(run, f"codec-m{args.mode}",
                              codec_bench(run.path, relative, args.mode),
                              args.simulator, "verify_codec")
            if "CODEC_PASS" not in output:
                raise AssertionError("KV codec experiment produced no completion record")
            run.receipt["results"].append(dict(case="codec", cache_mode=args.mode, summary=output))
        elif args.probe == "kv":
            compare_leaf(run, f"kv-m{args.mode}-s{args.seed}",
                         kv_bench(run.path, relative, args.mode, args.resident, args.seed,
                                  dim=258 if args.resident == 64 else 66),
                         "verify_kv", "KV_HIERARCHY_PASS", args.simulator)
        elif args.probe == "kv-context":
            compare_leaf(run, f"kv-context-m{args.mode}",
                         context_bench(run.path, relative, args.mode),
                         "verify_kv_context", "KV_CONTEXT_PASS", args.simulator)
        elif args.probe == "tiles":
            compare_leaf(run, f"tiles-slots{args.tile_slots}-s{args.seed}",
                         tile_bench(args.tile_slots, args.seed),
                         "verify_tiles", "TILE_PASS", args.simulator)
        elif args.probe == "tiles-compact":
            compare_leaf(run, "tiles-compact", tile_bench(
                         compact=True, compact_banks=args.banks,
                         compact_entries=64 if args.tile_k == 128 else 1),
                         "verify_tiles", "TILE_FIRST_CONSUME_PASS", args.simulator)
        elif args.probe == "tiles-raw":
            output = simulate(run, "tiles-raw", tile_bench(compact=True, compact_banks=2),
                              top="verify_tiles", normalize=False)
            if "TILE_FIRST_CONSUME_PASS" not in output:
                raise AssertionError("raw compact tile probe did not compare")
            run.receipt["results"].append(dict(case="tiles-raw", summary=output))
        elif args.probe == "ddr-faults":
            compare_leaf(run, "ddr-faults", DDR_FAULT_TB,
                         "verify_ddr_faults", "DDR_FAULT_PASS", args.simulator)
        elif args.probe == "parent":
            bench, metadata = parent_bench(run.path, relative, args.seed, args.banks,
                                           args.mode, args.tokens)
            output = simulate(run, f"parent-b{args.banks}-m{args.mode}-s{args.seed}",
                              bench, args.simulator, "verify_parent",
                              ROOT / "anvil_q3_reference/rtl")
            if "PARENT_PASS" not in output:
                raise AssertionError("parent comparison produced no completion")
            run.receipt["results"].append(dict(case="parent", summary=output, **metadata))
        elif args.probe == "benchmark-components":
            from benchmark import component_monitors, component_records
            integration(run, seed=args.seed, banks=args.banks, mode=args.mode,
                        tokens=3, benchmark=True)
            run.receipt["results"].append(dict(
                case="ht-components", domains=component_records(run.receipt["results"][-1]["summary"])))
            parent_banks = min(args.banks, 8)
            geometry = Geometry()
            image = Image(geometry, args.seed)
            oracle = Inference(image, args.mode)
            for token, pos, fresh in ((0, 0, True), (1, 1, False), (2, 0, True)):
                oracle.token(token, pos, fresh)
            bench, metadata = parent_bench(run.path, relative, args.seed, parent_banks,
                                           args.mode, 3, geometry)
            bench += component_monitors(run.path, relative, oracle, geometry,
                                         parent=True, banks=parent_banks)
            output = simulate(run, f"parent-components-b{parent_banks}-m{args.mode}-s{args.seed}",
                              bench, args.simulator, "verify_parent",
                              ROOT / "anvil_q3_reference/rtl")
            run.receipt["results"].append(dict(case="parent-components", summary=output,
                                               domains=component_records(output), **metadata))
        elif args.probe == "benchmark-stream":
            from benchmark import parent_stream_bench
            parent_banks = min(args.banks, 8)
            compare_leaf(run, "ht-stream", ddr_bench(args.seed, stress=False, count=256, base=0),
                         "verify_ddr", "DDR_PASS")
            output = simulate(run, "parent-stream", parent_stream_bench(parent_banks, args.seed),
                              top="verify_parent_stream",
                              rtl_directory=ROOT / "anvil_q3_reference/rtl")
            if "PARENT_STREAM_PASS" not in output:
                raise AssertionError("stream comparison produced no completion")
            run.receipt["results"].append(dict(case="parent-stream", summary=output))
        elif args.probe == "benchmark-cell":
            from benchmark import execute_benchmark
            execute_benchmark(run, integration, simulate, relative, ROOT,
                              seeds=(args.seed,), banks_matrix=(args.banks,), modes=(args.mode,))
        elif args.probe == "cache-reuse":
            for seed in (17, 89):
                compare_leaf(run, f"cache-mac-s{seed}", mac_bench(run.path, relative, seed),
                             "verify_mac", "MAC_PASS")
            if len(run.compiled) != 1 or len(run.receipt.get("compile_reuse", [])) != 1:
                raise AssertionError("expected one compile and two independent seeded executions")
        elif args.probe == "tensor":
            output = simulate(run, f"tensor-b{args.banks}-s{args.seed}",
                              tensor_bench(run.path, relative, args.seed, args.banks,
                                           args.tile_rows), args.simulator, "verify_tensor")
            if "TENSOR_PASS" not in output:
                raise AssertionError("tensor experiment produced no completion record")
            run.receipt["results"].append(dict(case="tensor", banks=args.banks,
                                               seed=args.seed, summary=output))
        elif args.probe == "production-tensor":
            compare_leaf(run, f"production-tensor-s{args.seed}",
                         production_tensor_bench(run.path, relative, args.seed),
                         "verify_tensor", "PRODUCTION_TENSOR_PASS", args.simulator)
        elif args.probe == "arithmetic":
            output = simulate(run, "arithmetic", arithmetic_bench(run.path, relative),
                              args.simulator, "verify_arithmetic")
            if "ARITHMETIC_PASS" not in output:
                raise AssertionError("arithmetic experiment produced no completion record")
            run.receipt["results"].append(dict(case="arithmetic", summary=output))
        elif args.probe == "image-map":
            bench, layout = map_bench(run.path, relative)
            output = simulate(run, "image-map", bench, args.simulator, "verify_map")
            if "IMAGE_MAP_PASS" not in output:
                raise AssertionError("image-map experiment produced no completion record")
            run.receipt["results"].append(dict(case="production-image-map", layout=layout,
                                               summary=output))
    except Exception as error:
        run.finish(error)
        return 1
    run.finish()
    return 0


if __name__ == "__main__":
    sys.exit(main())
