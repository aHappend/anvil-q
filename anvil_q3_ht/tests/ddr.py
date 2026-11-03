"""Independent ordered byte-memory scoreboard for the public burst interface."""


DDR_TB = r"""
module verify_ddr;
  reg clk=0; always #5 clk=~clk;
  reg rst_n=0, flush=0, cmd_valid=0, data_ready=0;
  reg [32:0] cmd_address=0;
  reg [31:0] cmd_beats=0;
  reg [159:0] cmd_meta=0;
  wire cmd_ready, data_valid, data_last, data_error, idle, drain_done, fault;
  wire [511:0] data;
  wire [159:0] data_meta;
  wire [32:0] avm_address;
  wire avm_read;
  wire [7:0] avm_burstcount;
  reg avm_waitrequest=0, avm_readdatavalid=0;
  reg [511:0] avm_readdata=0;
  reg [1:0] avm_response=0;
  anvil_q3_ht_ddr_prefetcher #(.QUEUE_DEPTH(@QUEUE@),.BURST_BEATS(@BURST@)) dut(.*);
  localparam N=@COUNT@, STRESS=@STRESS@;
  integer cycle=0, sent=0, checked=0, commands=0, returns=0;
  integer first_return=-1, last_return=-1, maximum_outstanding=0;
  integer waits=0, stalls=0, page_ends=0, high_addresses=0, simultaneous=0;
  integer first_descriptor=-1, last_consume=-1, fill_consume=0;
  integer eh=0, et=0, sh=0, st=0, sc=0, k;
  reg [32:0] expected_address [0:131071], service_address [0:63];
  reg [159:0] expected_meta [0:131071];
  reg expected_last [0:131071];
  integer remaining [0:63], due [0:63];
  reg [31:0] rng=@SEED@;
  reg stalled=0, output_stalled=0;
  reg [48:0] held_command;
  reg [674:0] held_output;
  function automatic [31:0] next_random(input [31:0] x);
    reg [31:0] y;
    begin y=x^(x<<13); y=y^(y>>17); next_random=y^(y<<5); end
  endfunction
  function automatic [511:0] memory_value(input [32:0] address);
    integer lane;
    begin
      for (lane=0;lane<8;lane=lane+1)
        memory_value[lane*64+:64]=64'(address)^(64'h9e3779b97f4a7c15*64'(lane+1));
    end
  endfunction
  task reset_check;
    begin
      if ({cmd_ready,data_valid,data_last,data_error,idle,drain_done,fault,
           avm_read,avm_address,avm_burstcount,data,data_meta} !== 721'd0)
        $fatal(1,"DDR_RESET_XZ");
    end
  endtask
  always @(posedge clk) begin
    cycle=cycle+1;
    if (!rst_n) reset_check();
    else begin
      if (cycle>1000000) $fatal(1,"DDR_PROGRESS");
      if (fault !== 0 || data_error !== 0) $fatal(1,"DDR_UNEXPECTED_FAULT");
      if (stalled && {avm_read,avm_address,avm_burstcount} !== held_command)
        $fatal(1,"DDR_COMMAND_STABILITY");
      stalled=avm_read && avm_waitrequest;
      held_command={avm_read,avm_address,avm_burstcount};
      if (stalled) waits=waits+1;
      if (output_stalled && {data_valid,data_last,data_error,data_meta,data} !== held_output)
        $fatal(1,"DDR_OUTPUT_STABILITY");
      output_stalled=data_valid && !data_ready;
      held_output={data_valid,data_last,data_error,data_meta,data};
      if (output_stalled) stalls=stalls+1;
      if (cmd_valid && cmd_ready) begin
        if (first_descriptor<0) first_descriptor=cycle;
        for (k=0;k<cmd_beats;k=k+1) begin
          if (et>=131072) $fatal(1,"DDR_ORACLE_CAPACITY");
          expected_address[et]=cmd_address+33'(k*64);
          expected_meta[et]=cmd_meta;
          expected_last[et]=(k==cmd_beats-1);
          et=et+1;
        end
        sent=sent+1;
      end
      if (data_valid && data_ready) begin
        if (eh>=et || data!==memory_value(expected_address[eh]) ||
            data_meta!==expected_meta[eh] || data_last!==expected_last[eh])
          $fatal(1,"DDR_ORDERED_BEAT index=%0d meta=%h expected=%h last=%b expected_last=%b",
                 eh,data_meta,expected_meta[eh],data_last,expected_last[eh]);
        eh=eh+1; checked=checked+1;
        last_consume=cycle;
        if (avm_readdatavalid) fill_consume=fill_consume+1;
      end
      if (avm_readdatavalid) begin
        if (sc==0 || cycle<due[sh]) $fatal(1,"DDR_SERVICE_LATENCY_OR_OWNERSHIP");
        if (avm_readdata!==memory_value(service_address[sh]))
          $fatal(1,"DDR_SERVICE_DATA");
        service_address[sh]=service_address[sh]+64;
        remaining[sh]=remaining[sh]-1;
        if (remaining[sh]==0) begin sh=(sh==63)?0:sh+1; sc=sc-1; end
        if (first_return<0) first_return=cycle;
        last_return=cycle; returns=returns+1;
      end
      if (avm_read && !avm_waitrequest) begin
        if (avm_address[5:0]!==0 || avm_burstcount<1 || avm_burstcount>@BURST@ ||
            32'(avm_address[11:0])+32'(avm_burstcount)*64>4096 ||
            {1'b0,avm_address}+34'(avm_burstcount)*64>34'h200000000)
          $fatal(1,"DDR_BURST_BOUNDARY");
        if (sc>=64) $fatal(1,"DDR_SERVICE_QUEUE");
        service_address[st]=avm_address; remaining[st]=avm_burstcount;
        due[st]=cycle+12; st=(st==63)?0:st+1; sc=sc+1;
        if (sc>maximum_outstanding) maximum_outstanding=sc;
        if (sc>4) $fatal(1,"DDR_OUTSTANDING_LIMIT");
        if (avm_readdatavalid) simultaneous=simultaneous+1;
        if (avm_address[32]) high_addresses=high_addresses+1;
        if (32'(avm_address[11:0])+32'(avm_burstcount)*64==4096)
          page_ends=page_ends+1;
        commands=commands+1;
      end
    end
  end
  always @(negedge clk) begin
    if (!rst_n) begin reset_check(); avm_readdatavalid=0; avm_readdata=0; end
    else begin
      rng=next_random(rng);
      avm_waitrequest=STRESS && rng[3:0]<3;
      data_ready=!STRESS || rng[7:4]>=4;
      avm_readdatavalid=0; avm_readdata=0;
      if (sc>0 && cycle+1>=due[sh] && (!STRESS || rng[11:8]>=3)) begin
        avm_readdatavalid=1;
        avm_readdata=memory_value(service_address[sh]);
      end
    end
  end
  integer id;
  initial begin
    #1; reset_check();
    repeat(3) @(negedge clk);
    rst_n=1;
    for (id=0;id<N;id=id+1) begin
      @(negedge clk);
      cmd_valid=1; cmd_meta=160'(id+1);
      cmd_address=STRESS ? 33'h@BASE@+33'(id*8192)+33'((id%3==0)?4032:0) :
        33'h@BASE@+33'(id*4096);
      cmd_beats=STRESS ? 1+(id*17+@SEED@)%65 : 64;
      @(posedge clk); while (!cmd_ready) @(posedge clk);
      @(negedge clk); cmd_valid=0;
    end
    @(posedge clk);
    while (!idle) @(posedge clk);
    if (eh!=et || checked==0 || returns!=checked || commands<1000 ||
        maximum_outstanding!=4 || (@HIGH@ && high_addresses==0) ||
        page_ends==0 || simultaneous==0 || fill_consume==0)
      $fatal(1,"DDR_COVERAGE checked=%0d expected=%0d commands=%0d max_outstanding=%0d",
             checked,et,commands,maximum_outstanding);
    if (STRESS && (waits==0 || stalls==0)) $fatal(1,"DDR_STALL_COVERAGE");
    if (!STRESS && (returns<4096 || returns*100<90*(last_return-first_return+1)))
      $fatal(1,"DDR_STEADY_BANDWIDTH beats=%0d window=%0d",returns,last_return-first_return+1);
    $display("DDR_PASS seed=@SEED@ stress=%0d compared=%0d commands=%0d returns=%0d first=%0d last=%0d window=%0d max_outstanding=%0d waits=%0d stalls=%0d page_ends=%0d high=%0d simultaneous=%0d fill_consume=%0d first_descriptor=%0d last_consume=%0d operation_cycles=%0d",
             STRESS,checked,commands,returns,first_return,last_return,last_return-first_return+1,
             maximum_outstanding,waits,stalls,page_ends,high_addresses,simultaneous,
             fill_consume,first_descriptor,last_consume,last_consume-first_descriptor+1);
    $finish;
  end
endmodule
"""


def ddr_bench(seed=17, queue_depth=3, burst_beats=16, stress=True, count=None,
              base=0x100000000):
    bench = DDR_TB
    # 300 full-page descriptors produce 1200 bursts and 19200 beats.
    for key, value in dict(SEED=seed, QUEUE=queue_depth, BURST=burst_beats,
                           COUNT=count if count is not None else 1200 if stress else 300,
                           STRESS=int(stress), BASE=f"{base:x}", HIGH=int(base >= 1 << 32)).items():
        bench = bench.replace(f"@{key}@", str(value))
    return bench
