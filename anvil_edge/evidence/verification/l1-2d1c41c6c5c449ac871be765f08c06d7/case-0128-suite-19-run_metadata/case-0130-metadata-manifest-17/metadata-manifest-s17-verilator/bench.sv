
module bench;
  reg clk=0,rst_n,start=0;
  always #5 clk=~clk;
  wire busy,done,valid_manifest,error;
  wire [7:0] error_code;
  wire [1023:0] staged_metadata;
  wire [511:0] staged_table_counts;
  wire ddr_req_valid,ddr_rsp_ready;
  wire [63:0] ddr_req_addr;
  reg ddr_req_ready=0,ddr_rsp_valid=0,ddr_rsp_error=0;
  reg [31:0] ddr_rsp_rdata=0;
  wire [223:0] staged_config_words=224'h101000000010000000100000002000000ff00000005;
  wire [1279:0] staged_segment_bases=1280'h54c000000000000054a000000000000054800000000000005450000000000000542000000000000054000000000000005380000000000000533000000000000052f000000000000052d000000000000052a000000000000052700000000000004e500000000000004d2c0000000000003cfc0000000000003c7c000000000000399c000000000000166000000000000010400000000000001000;
  wire [1279:0] staged_segment_bytes=1280'h2000000000000000200000000000000020000000000000003000000000000000300000000000000020000000000000008000000000000000500000000000000040000000000000002000000000000000300000000000000030000000000000042000000000000001220000000000001030000000000000008000000000000002e0000000000000233c00000000000006200000000000000040;
  anvil_edge_manifest_validator #(
    .NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),
    .NUM_Q_HEADS(1),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),
    .VOCAB_SIZE(257),.MAX_SEQ_LEN(4),.DDR_BYTES(65536)
  ) dut(.*);
  reg [31:0] memory[0:16383];
  reg [1023:0] expected_metadata;
  reg [31:0] rng=17;
  reg pending=0,held=0;
  reg [63:0] pending_address=0,held_address=0;
  integer delay_count=0,requests=0,responses=0,comparisons=0;
  integer accepted_cases=0,rejected_cases=0,stalls=0,metadata_reads=0;
  integer successes=0;
  task automatic reset_check;
    begin
      if ({busy,done,valid_manifest,error,error_code,staged_metadata,
           staged_table_counts,ddr_req_valid,ddr_req_addr,ddr_rsp_ready}!==1614'd0)
        $fatal(1,"METADATA_RESET t=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n) begin
    rng=rng^(rng<<13); rng=rng^(rng>>17); rng=rng^(rng<<5);
    ddr_req_ready=rng[0];
    if (pending && !ddr_rsp_valid) begin
      if (delay_count==0) begin
        ddr_rsp_valid<=1;
        ddr_rsp_rdata=memory[pending_address>>2];
      end else delay_count=delay_count-1;
    end
  end
  always @(posedge clk) if (rst_n) begin
    if ((^{busy,done,valid_manifest,error,error_code,staged_metadata,
            staged_table_counts,ddr_req_valid,ddr_req_addr,ddr_rsp_ready})===1'bx)
      $fatal(1,"METADATA_XZ");
    if (!valid_manifest && {staged_metadata,staged_table_counts}!==0)
      $fatal(1,"METADATA_PARTIAL_PUBLICATION");
    if (done) successes=successes+1;
    if (held && (!ddr_req_valid || ddr_req_addr!==held_address))
      $fatal(1,"METADATA_REQUEST_HOLD");
    held=ddr_req_valid && !ddr_req_ready; held_address=ddr_req_addr;
    if (held) stalls=stalls+1;
    if (ddr_rsp_valid && ddr_rsp_ready) begin
      if (!pending) $fatal(1,"METADATA_ORPHAN_RESPONSE");
      pending=0; responses=responses+1; ddr_rsp_valid<=0;
    end
    if (ddr_req_valid && ddr_req_ready) begin
      if (pending || ddr_req_addr[1:0]!==0 || ddr_req_addr>=65536)
        $fatal(1,"METADATA_REQUEST_PROTOCOL");
      pending=1; pending_address=ddr_req_addr;
      delay_count=1+rng[3:2]; requests=requests+1;
      if (ddr_req_addr>=15484 && ddr_req_addr<15484+128)
        metadata_reads=metadata_reads+1;
      comparisons=comparisons+1;
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic run_case(input integer case_id,input [7:0] code);
    integer previous_requests,previous_metadata_reads,previous_successes;
    begin
      previous_requests=requests; previous_metadata_reads=metadata_reads;
      previous_successes=successes;
      @(negedge clk); #1; start=1;
      tick();
      if (!busy || done || valid_manifest || error ||
          staged_metadata!==0 || staged_table_counts!==0)
        $fatal(1,"METADATA_RELOAD_ISOLATION case=%0d",case_id);
      @(negedge clk); #1; start=0;
      while (!valid_manifest && !error) tick();
      if (pending || ddr_rsp_valid || requests!=responses ||
          requests<=previous_requests || metadata_reads-previous_metadata_reads!=32)
        $fatal(1,"METADATA_RESPONSE_COUNTS case=%0d",case_id);
      if (code==0) begin
        if (error || !done || error_code!==0 ||
            staged_metadata!==expected_metadata ||
            staged_table_counts!==512'h1000000010000000000000006000000030000000200000000000000010000000100000100000001020000010100000000)
          $fatal(1,"METADATA_ACCEPT case=%0d",case_id);
        accepted_cases=accepted_cases+1;
      end else begin
        if (!error || valid_manifest || done || error_code!==code ||
            staged_metadata!==0 || staged_table_counts!==0)
          $fatal(1,"METADATA_REJECT case=%0d code=%h",case_id,error_code);
        rejected_cases=rejected_cases+1;
      end
      repeat (4) begin
        tick();
        if (done || ddr_req_valid || (code!=0 &&
            (!error || error_code!==code || valid_manifest || staged_metadata!==0)))
          $fatal(1,"METADATA_STICKY_OR_EXTRA_WORK case=%0d",case_id);
      end
      if (successes-previous_successes!=(code==0 ? 1 : 0))
        $fatal(1,"METADATA_DONE_COUNT case=%0d",case_id);
      comparisons=comparisons+1;
      $display("METADATA_CASE %0d code=%0d",case_id,code);
      if (code!=0) begin
        @(negedge clk); #1; rst_n=0;
        repeat (2) tick();
        @(negedge clk); #1; rst_n=1;
      end
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    $readmemh("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0128-suite-19-run_metadata/case-0130-metadata-manifest-17/metadata-manifest-s17-verilator-input/ddr.hex",memory);
    repeat (2) tick();
    @(negedge clk); #1; rst_n=1;
    
    expected_metadata=1024'hbb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e998780970762900001000000000020000000000000020000000020000000000000001000f0100000000ff00000000000000000000000000000000000001010000000100000001;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(0,8'h00);


    expected_metadata=1024'h10000000090000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e99878097076290000100000000002000000000000002000000002000000000000000100100000000000ff00000000000000000000000000000000000001010000000100000002;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(1,8'h00);


    expected_metadata=1024'hbb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e998780970762900001000000000020000000000000020000000020000000000000001000f0100000000ff00000000000000000000000000000000000001010000000100000000;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(2,8'h06);


    expected_metadata=1024'hbb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e998780970762900001000000000020000000000000020000000020000000000000001000f0100000000ff00000000000000000000000000000000000001010000000100000003;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(3,8'h06);


    expected_metadata=1024'hbb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e998780970762900001000000000020000000000000020000000020000000000000001000f0100000000ff000000000000000000000000000000000000010100000001ffffffff;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(4,8'h06);


    expected_metadata=1024'h1bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e998780970762900001000000000020000000000000020000000020000000000000001000f0100000000ff00000000000000000000000000000000000001010000000100000001;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(5,8'h06);


    expected_metadata=1024'h100000000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e998780970762900001000000000020000000000000020000000020000000000000001000f0100000000ff00000000000000000000000000000000000001010000000100000001;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(6,8'h06);


    expected_metadata=1024'h10000000000000000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e998780970762900001000000000020000000000000020000000020000000000000001000f0100000000ff00000000000000000000000000000000000001010000000100000001;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(7,8'h06);


    expected_metadata=1024'h1000000000000000000000000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e998780970762900001000000000020000000000000020000000020000000000000001000f0100000000ff00000000000000000000000000000000000001010000000100000001;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(8,8'h06);


    expected_metadata=1024'h100000000000000000000000000000000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e998780970762900001000000000020000000000000020000000020000000000000001000f0100000000ff00000000000000000000000000000000000001010000000100000001;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(9,8'h06);


    expected_metadata=1024'h10000000000000000000000000000000000000000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e998780970762900001000000000020000000000000020000000020000000000000001000f0100000000ff00000000000000000000000000000000000001010000000100000001;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(10,8'h06);


    expected_metadata=1024'h1000000000000000000000000000000000000000000000000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e998780970762900001000000000020000000000000020000000020000000000000001000f0100000000ff00000000000000000000000000000000000001010000000100000001;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(11,8'h06);


    expected_metadata=1024'h100000000000000000000000000000000000000000000000000000000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e998780970762900001000000000020000000000000020000000020000000000000001000f0100000000ff00000000000000000000000000000000000001010000000100000001;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(12,8'h06);


    expected_metadata=1024'h10010000000090000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e99878097076290000100000000002000000000000002000000002000000000000000100100000000000ff00000000000000000000000000000000000001010000000100000002;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(13,8'h06);


    expected_metadata=1024'h1000000000010000000090000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e99878097076290000100000000002000000000000002000000002000000000000000100100000000000ff00000000000000000000000000000000000001010000000100000002;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(14,8'h06);


    expected_metadata=1024'h100000000000000000010000000090000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e99878097076290000100000000002000000000000002000000002000000000000000100100000000000ff00000000000000000000000000000000000001010000000100000002;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(15,8'h06);


    expected_metadata=1024'h10000000000000000000000000010000000090000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e99878097076290000100000000002000000000000002000000002000000000000000100100000000000ff00000000000000000000000000000000000001010000000100000002;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(16,8'h06);


    expected_metadata=1024'h1000000000000000000000000000000000010000000090000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e99878097076290000100000000002000000000000002000000002000000000000000100100000000000ff00000000000000000000000000000000000001010000000100000002;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(17,8'h06);


    expected_metadata=1024'h100000000000000000000000000000000000000000010000000090000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e99878097076290000100000000002000000000000002000000002000000000000000100100000000000ff00000000000000000000000000000000000001010000000100000002;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(18,8'h06);


    expected_metadata=1024'hbb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e99878097076290000100000000002000000000000002000000002000000000000000100100000000000ff00000000000000000000000000000000000001010000000100000002;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(19,8'h00);


    expected_metadata=1024'hbb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e998780970762900001000000000020000000000000020000000020000000000000001000f0100000000ff00000000000000000000000000000000000001010000000100000001;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(20,8'h00);


    expected_metadata=1024'h10000000090000bb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e99878097076290000100000000002000000000000002000000002000000000000000100100000000000ff00000000000000000000000000000000000001010000000100000002;
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[3871+word_index]=
        expected_metadata[word_index*32+:32];
    run_case(21,8'h00);

    if (accepted_cases!=5 || rejected_cases!=17 || stalls==0 ||
        requests!=responses || pending)
      $fatal(1,"METADATA_COVERAGE accepted=%0d rejected=%0d",accepted_cases,rejected_cases);
    $display("METADATA_COVERAGE accepted=%0d rejected=%0d reads=%0d stalls=%0d",
             accepted_cases,rejected_cases,responses,stalls);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin
    repeat (100000) @(posedge clk);
    $fatal(1,"METADATA_CYCLE_BOUND");
  end
endmodule
