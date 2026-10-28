"""Adversarial frozen-interface fixtures; not Q2/Q3/Q4 arithmetic implementations."""

from pathlib import Path


ADAPTER = r"""
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg token_valid=0,new_sequence=1,logit_ready=0,config_valid=0;
  reg [31:0] token_id=@TOKEN@,token_pos=0,cfg_active_vocab_size=@ACTIVE@;
  wire token_ready,logit_valid,done,error;
  wire [31:0] logit_index;
  wire signed [31:0] logit_data;
  wire [7:0] error_code;
  wire mem_req_valid,mem_req_write,mem_rsp_ready;
  wire [3:0] mem_req_kind;
  wire [2:0] mem_req_proj;
  wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
  reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
  reg [31:0] mem_rsp_rdata=0;
  anvil_edge_core_adapter #(
    .NUM_LAYERS(2),.HIDDEN_SIZE(16),.INTERMEDIATE_SIZE(24),.NUM_Q_HEADS(2),
    .NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),.VOCAB_SIZE(260),.MAX_SEQ_LEN(4)
  ) dut(.*);
  reg [31:0] rng=@SEED@;
  integer cycles=0,requests=0,responses=0,logits=0,completions=0,tokens=0;
  integer comparisons=0,delay_count=0,request_stalls=0,output_stalls=0;
  integer memory_wait=0,output_wait=0;
  reg pending=0,held=0,logit_held=0;
  reg [135:0] held_request;
  reg [63:0] held_logit;
  task automatic reset_check;
    begin
      if ({token_ready,logit_valid,logit_index,logit_data,done,error,error_code,
           mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
           mem_req_row,mem_req_col,mem_req_wdata,mem_rsp_ready}!==0)
        $fatal(1,"ADAPTER_RESET");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n) begin
    rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
    if (!mem_req_valid) memory_wait=0;
    else if (memory_wait<2) memory_wait=memory_wait+1;
    if (!logit_valid) output_wait=0;
    else if (output_wait<2) output_wait=output_wait+1;
    mem_req_ready=memory_wait>=2 && rng[0] && cycles%7!=0;
    logit_ready=output_wait>=2 && rng[1] && cycles%5!=0;
    if (pending && !mem_rsp_valid) begin
      if (delay_count==0) begin mem_rsp_valid<=1; mem_rsp_rdata=32'hdeadc0de; end
      else delay_count=delay_count-1;
    end
  end
  always @(posedge clk) begin
    cycles=cycles+1;
    if (rst_n) begin
      if ((^{token_ready,logit_valid,logit_index,logit_data,done,error,error_code,
             mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
             mem_req_row,mem_req_col,mem_req_wdata,mem_rsp_ready})===1'bx)
        $fatal(1,"ADAPTER_XZ");
      if (held && (!mem_req_valid ||
          {mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
           mem_req_row,mem_req_col,mem_req_wdata}!==held_request))
        $fatal(1,"ADAPTER_MEMORY_STABILITY");
      if (logit_held && (!logit_valid || {logit_index,logit_data}!==held_logit) &&
          !(@EXPECTED_ERROR@!=0 && (done || error_code!=0)))
        $fatal(1,"ADAPTER_OUTPUT_STABILITY");
      held=mem_req_valid && !mem_req_ready;
      logit_held=logit_valid && !logit_ready;
      held_request={mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
                    mem_req_row,mem_req_col,mem_req_wdata};
      held_logit={logit_index,logit_data};
      if (held) request_stalls=request_stalls+1;
      if (logit_held) output_stalls=output_stalls+1;
      if (token_valid && token_ready) tokens=tokens+1;
      if (mem_rsp_valid && mem_rsp_ready) begin
        if (!pending) $fatal(1,"ADAPTER_ORPHAN_RESPONSE");
        pending=0; mem_rsp_valid<=0; responses=responses+1;
      end
      if (mem_req_valid && mem_req_ready) begin
        if (pending || requests>=2 || mem_req_proj!==0 ||
            {mem_req_write,mem_req_kind,mem_req_layer,mem_req_row,mem_req_col,
             mem_req_wdata} !==
            (requests==0 ? {1'b0,4'd0,32'd0,32'd7,32'd0,32'd0} :
                           {1'b1,4'd9,32'd1,32'd0,32'd7,32'h89abcdef}))
          $fatal(1,"ADAPTER_MEMORY_FIELDS");
        requests=requests+1; comparisons=comparisons+1;
        pending=1; delay_count=1+rng[4:2];
      end
      if (logit_valid && logit_ready) begin
        if (logits>=@ACTIVE@ || logit_index!==32'(logits) ||
            logit_data!==32'(-100000+logits*(@PROFILE@+3)))
          $fatal(1,"ADAPTER_ACTIVE_LOGIT item=%0d index=%0d value=%h",
                 logits,logit_index,logit_data);
        logits=logits+1; comparisons=comparisons+1;
      end
      if (done) begin
        if (completions!=0 || error!==(@EXPECTED_ERROR@!=0) ||
            error_code!==8'(@EXPECTED_ERROR@) || pending || tokens!=1)
          $fatal(1,"ADAPTER_COMPLETION error=%b code=%h expected=%h",
                 error,error_code,8'(@EXPECTED_ERROR@));
        if (@EXPECTED_ERROR@==0 && (logits!=@ACTIVE@ || requests!=2 || responses!=2))
          $fatal(1,"ADAPTER_MISSING_ACTIVE_OUTPUT");
        if (@EARLY_REJECT@ && (requests!=0 || responses!=0 || logits!=0))
          $fatal(1,"ADAPTER_REJECT_TRAFFIC");
        completions=completions+1; comparisons=comparisons+1;
        $display("ADAPTER_COMPLETE active=%0d logits=%0d error=%h",@ACTIVE@,logits,error_code);
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  initial begin
    rst_n=0; #0; reset_check(); repeat (2) tick();
    @(negedge clk); #1; rst_n=1; token_valid=1;
    repeat (8) begin tick(); if (token_ready || mem_req_valid || logit_valid || done)
      $fatal(1,"ADAPTER_UNCOMMITTED_TRAFFIC"); end
    @(negedge clk); #1; config_valid=1;
    do begin @(posedge clk); end while (!token_ready);
    #1; @(negedge clk); #1; token_valid=0;
    while (completions==0) tick();
    repeat (20) tick();
    if (done || logit_valid || tokens!=1 || completions!=1 || pending)
      $fatal(1,"ADAPTER_FINAL_COUNTS");
    if (@EXPECTED_ERROR@==0 && (request_stalls==0 || output_stalls==0))
      $fatal(1,"ADAPTER_STALL_COVERAGE");
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin repeat (200000) @(posedge clk); $fatal(1,"ADAPTER_CYCLE_BOUND"); end
endmodule

// Test-only stand-in for the supplied public interface, never a production source.
module anvil_q1_top #(
  parameter NUM_LAYERS=24,HIDDEN_SIZE=896,INTERMEDIATE_SIZE=4864,
  NUM_Q_HEADS=14,NUM_KV_HEADS=2,HEAD_DIM=64,GROUP_SIZE=128,
  AWQ_BITS=4,VOCAB_SIZE=151936,MAX_SEQ_LEN=32768
) (
  input wire clk,rst_n,token_valid,
  output wire token_ready,
  input wire [31:0] token_id,token_pos,
  input wire new_sequence,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index,
  output wire signed [31:0] logit_data,
  output wire done,error,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire mem_req_write,
  output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer,
  output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row,mem_req_col,mem_req_wdata,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata,
  input wire mem_rsp_error
);
  reg [3:0] phase;
  integer clock_count,index,frames,accepted;
  wire emit=rst_n && phase==5;
  assign token_ready=rst_n && phase==0 && clock_count%(@PROFILE@+1)==0;
  assign mem_req_valid=rst_n && (phase==1 || phase==3);
  assign mem_req_write=rst_n && phase==3;
  assign mem_req_kind=!rst_n ? 0 : (phase==3 ? 9 : 0);
  assign mem_req_layer=rst_n && phase==3 ? 1 : 0;
  assign mem_req_proj=0;
  assign mem_req_row=rst_n && phase==1 ? 7 : 0;
  assign mem_req_col=rst_n && phase==3 ? 7 : 0;
  assign mem_req_wdata=rst_n && phase==3 ? 32'h89abcdef : 0;
  assign mem_rsp_ready=rst_n && (phase==2 || phase==4) &&
                       clock_count%(@PROFILE@+2)==0;
  assign logit_valid=emit;
  assign logit_index=!rst_n ? 0 :
    ((@FAULT@==1 && index==257) || (@FAULT@==2 && index==1) ? index+1 : index);
  assign logit_data=!rst_n ? 0 : (index>=@ACTIVE@ ? 32'h7fffffff :
                                 32'(-100000+index*(@PROFILE@+3)));
  assign done=rst_n && phase==6;
  assign error=rst_n && @FAULT@==4 && phase==6;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin phase<=0; clock_count<=0; index<=0; frames<=0; accepted<=0; end
    else begin
      clock_count<=clock_count+1;
      case (phase)
        0: if (token_valid && token_ready) begin
          if (token_id!==7 || token_pos!==0 || new_sequence!==1 || frames!=0)
            $fatal(1,"FIXTURE_TOKEN_FIELDS");
          frames<=frames+1; phase<=1;
        end
        1: if (mem_req_valid && mem_req_ready) phase<=2;
        2: if (mem_rsp_valid && mem_rsp_ready) begin
          if (mem_rsp_rdata!==32'hdeadc0de || mem_rsp_error)
            $fatal(1,"FIXTURE_READ_RESPONSE");
          phase<=3;
        end
        3: if (mem_req_valid && mem_req_ready) phase<=4;
        4: if (mem_rsp_valid && mem_rsp_ready) begin
          if (mem_rsp_rdata!==32'hdeadc0de || mem_rsp_error)
            $fatal(1,"FIXTURE_WRITE_ACKNOWLEDGEMENT");
          phase<=5;
        end
        5: if (logit_valid && logit_ready) begin
          accepted<=accepted+1;
          if ((@FAULT@==3 && index==255) || (@FAULT@==4 && index==1))
            phase<=6;
          else if (index+1==VOCAB_SIZE) phase<=7;
          else begin index<=index+1; phase<=8; end
        end
        7: if (clock_count%(@PROFILE@+3)==0) begin
          if (accepted!=VOCAB_SIZE) $fatal(1,"FIXTURE_PHYSICAL_COUNT");
          $display("FIXTURE_FRAME physical=%0d profile=%0d",accepted,@PROFILE@);
          phase<=6;
        end
        8: if (clock_count%(@PROFILE@+1)==0) phase<=5;
        6: phase<=9;
        default: begin end
      endcase
    end
  end
endmodule
"""


def adapter_test(evidence, profile, active, seed, fault=0, token=7):
    early_reject = active < 256 or active > 260 or token >= active
    expected_error = (6 if active < 256 or active > 260 else 0x20 if token >= active
                      or fault == 4 else 0x21 if fault else 0)
    bench = ADAPTER
    for key, value in {
        "PROFILE": profile, "ACTIVE": active, "SEED": seed, "FAULT": fault,
        "TOKEN": token, "EXPECTED_ERROR": expected_error,
        "EARLY_REJECT": int(early_reject),
    }.items():
        bench = bench.replace(f"@{key}@", str(value))
    name = f"adapter-contract-p{profile}-v{active}-s{seed}-f{fault}-t{token}"
    evidence.simulate(name, bench, ["rtl/anvil_edge_core_adapter.sv"],
                      active + 3 if expected_error == 0 else None)
    if expected_error == 0:
        child = evidence.record["children"][-1]
        root = Path(__file__).resolve().parent.parent
        lines = (root / child["stdout"]).read_text().splitlines()
        physical = [i for i, line in enumerate(lines) if line.startswith("FIXTURE_FRAME ")]
        complete = [i for i, line in enumerate(lines) if line.startswith("ADAPTER_COMPLETE ")]
        if (len(physical) != 1 or len(complete) != 1 or physical[0] >= complete[0] or
                f"physical=260 profile={profile}" not in lines[physical[0]]):
            raise RuntimeError("Adapter completion did not follow complete physical frame")


def run_adapters(evidence):
    evidence.tools(("iverilog", "vvp"))
    for profile in (1, 2, 3, 4):
        for seed in (1, 17, 89):
            for active in (256, 257, 260):
                adapter_test(evidence, profile, active, seed)
        for fault in (1, 2, 3, 4):
            adapter_test(evidence, profile, 256, 17, fault)
        for active in (1, 255, 261, 262145):
            adapter_test(evidence, profile, active, 17)
        adapter_test(evidence, profile, 256, 17, token=256)
