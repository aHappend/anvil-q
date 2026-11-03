"""Transfer-relative burst cancellation and explicit malformed/fault cases."""


DDR_FAULT_TB = r"""
module verify_ddr_faults;
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
  reg avm_waitrequest=1, avm_readdatavalid=0;
  reg [511:0] avm_readdata=0;
  reg [1:0] avm_response=0;
  anvil_q3_ht_ddr_prefetcher #(.QUEUE_DEPTH(1),.BURST_BEATS(1)) dut(.*);
  integer cycle=0, rejected=0, cancellations=0, compared=0, faults=0;
  always @(posedge clk) begin
    cycle=cycle+1;
    if (cycle>2000) $fatal(1,"DDR_FAULT_PROGRESS");
    if (!rst_n && {cmd_ready,data_valid,data_last,data_error,idle,drain_done,
                   fault,avm_read,avm_address,avm_burstcount,data,data_meta} !== 721'd0)
      $fatal(1,"DDR_FAULT_RESET");
  end
  task enqueue(input [32:0] address, input [31:0] beats, input [159:0] meta);
    begin
      @(negedge clk); cmd_valid=1; cmd_address=address; cmd_beats=beats; cmd_meta=meta;
      @(posedge clk); while (!cmd_ready) @(posedge clk);
      @(negedge clk); cmd_valid=0;
    end
  endtask
  task recover;
    begin
      @(negedge clk); flush=1;
      @(posedge clk);
      @(negedge clk); flush=0;
      @(posedge clk); while (!idle) @(posedge clk);
      if (fault !== 0 || data_valid !== 0 || drain_done !== 1)
        $fatal(1,"DDR_FAULT_RECOVERY");
    end
  endtask
  task expect_fault;
    begin
      @(posedge clk); #1;
      if (fault !== 1 || data_valid !== 0 || cmd_ready !== 0)
        $fatal(1,"DDR_MISSING_EXPLICIT_FAULT");
      faults=faults+1;
    end
  endtask
  task cancel_at(input integer point);
    reg [41:0] held;
    begin
      enqueue(33'h1ffffffc0,1,160'habcdef);
      @(posedge clk); while (!avm_read) @(posedge clk);
      held={avm_read,avm_address,avm_burstcount};
      if (point==0) begin
        @(negedge clk); flush=1;
        repeat(3) begin
          @(posedge clk);
          if ({avm_read,avm_address,avm_burstcount} !== held || drain_done !== 0 ||
              data_valid !== 0) $fatal(1,"DDR_CANCEL_OFFERED_COMMAND");
        end
        @(negedge clk); flush=0;
      end
      @(negedge clk); avm_waitrequest=0;
      @(posedge clk);
      if ({avm_read,avm_address,avm_burstcount} !== held)
        $fatal(1,"DDR_CANCEL_COMMAND_TRANSFER");
      @(negedge clk); avm_waitrequest=1;
      if (point==1) flush=1;
      @(posedge clk);
      @(negedge clk); flush=0; avm_readdatavalid=1; avm_readdata=512'h123456;
      @(posedge clk);
      @(negedge clk); avm_readdatavalid=0; avm_readdata=0;
      if (point==2) begin
        // The returned data reaches a retained output before cancellation.
        @(posedge clk); while (!data_valid) @(posedge clk);
        if (data!==512'h123456 || data_meta!==160'habcdef || data_last!==1)
          $fatal(1,"DDR_CANCEL_BUFFER_SETUP");
        @(negedge clk); flush=1;
        @(posedge clk);
        @(negedge clk); flush=0;
      end
      @(posedge clk); while (!idle) begin
        if (data_valid !== 0) $fatal(1,"DDR_CANCEL_STALE_RESULT");
        @(posedge clk);
      end
      if (fault !== 0) $fatal(1,"DDR_CANCEL_FAULT");
      cancellations=cancellations+1;
    end
  endtask
  task cancel_queued;
    begin
      enqueue(0,4,160'h1234);
      flush=1;
      @(posedge clk);
      if (avm_read!==0 || data_valid!==0) $fatal(1,"DDR_QUEUED_CANCEL_ADMISSION");
      @(negedge clk); flush=0;
      @(posedge clk); while (!idle) begin
        if (avm_read!==0 || data_valid!==0) $fatal(1,"DDR_QUEUED_CANCEL_STALE");
        @(posedge clk);
      end
      if (fault!==0) $fatal(1,"DDR_QUEUED_CANCEL_FAULT");
      cancellations=cancellations+1;
    end
  endtask
  initial begin
    repeat(3) @(negedge clk); rst_n=1;
    // Return at the actual command acceptance edge, including the final aperture beat.
    enqueue(33'h1ffffffc0,1,160'h1234);
    @(posedge clk); while (!avm_read) @(posedge clk);
    @(negedge clk);
    avm_waitrequest=0; avm_readdatavalid=1; avm_readdata={16{32'hdeadc0de}};
    @(posedge clk);
    if (data_valid !== 0) $fatal(1,"DDR_ZERO_LATENCY_SAME_EDGE_OUTPUT");
    @(negedge clk); avm_waitrequest=1; avm_readdatavalid=0; avm_readdata=0;
    @(posedge clk); while (!data_valid) @(posedge clk);
    if (data!=={16{32'hdeadc0de}} || data_meta!==160'h1234 ||
        data_last!==1 || data_error!==0 || fault!==0)
      $fatal(1,"DDR_ZERO_LATENCY_NUMERICAL");
    @(negedge clk); data_ready=1;
    @(posedge clk); compared=compared+1;
    @(negedge clk); data_ready=0;
    @(posedge clk); while (!idle) @(posedge clk);
    cancel_queued(); cancel_at(0); cancel_at(1); cancel_at(2);
    enqueue(33'h100000001,1,0); expect_fault(); rejected=rejected+1; recover();
    enqueue(0,0,0); expect_fault(); rejected=rejected+1; recover();
    enqueue(33'h1ffffffc0,2,0); expect_fault(); rejected=rejected+1; recover();
    // An unsolicited return cannot be attributed to a future descriptor.
    @(negedge clk); avm_readdatavalid=1;
    @(posedge clk);
    @(negedge clk); avm_readdatavalid=0;
    expect_fault(); recover();
    // A real accepted burst with a non-success response must terminate explicitly.
    enqueue(33'h100000000,1,0);
    @(posedge clk); while (!avm_read) @(posedge clk);
    @(negedge clk); avm_waitrequest=0;
    @(posedge clk);
    @(negedge clk); avm_waitrequest=1; avm_readdatavalid=1; avm_response=2;
    @(posedge clk);
    @(negedge clk); avm_readdatavalid=0; avm_response=0;
    expect_fault(); recover();
    if (compared!=1 || cancellations!=4 || rejected!=3 || faults!=5)
      $fatal(1,"DDR_FAULT_COVERAGE");
    $display("DDR_FAULT_PASS zero_latency=%0d cancellation_states=%0d rejected=%0d faults=%0d",
             compared,cancellations,rejected,faults);
    $finish;
  end
endmodule
"""
