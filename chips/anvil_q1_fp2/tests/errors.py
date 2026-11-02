"""Architectural rejection, fault termination and reset-epoch public-pin tests."""


def simulate_errors(run, root, compile_and_run, simulator="iverilog"):
    stem = f"top-errors-{simulator}"
    directory = run.path / stem
    directory.mkdir()
    bench = directory / "tb.sv"
    bench.write_text("""`timescale 1ns/1ps
module tb;
  reg clk=0,rst_n=0,token_valid=0,new_sequence=0,logit_ready=0;
  reg [31:0] token_id=0,token_pos=0;
  reg [1:0] precision_mode=0;
  wire token_ready,logit_valid,done,error;
  wire [31:0] logit_index,logit_data;
  wire mem_req_valid,mem_req_write,mem_rsp_ready;
  wire [3:0] mem_req_kind;
  wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
  wire [2:0] mem_req_proj;
  reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
  reg [31:0] mem_rsp_rdata=0;
  wire ddr_req_valid,ddr_req_write,ddr_req_id,ddr_req_scale,ddr_rsp_ready;
  wire [3:0] ddr_req_kind;
  wire [31:0] ddr_req_layer,ddr_req_row,ddr_req_col;
  wire [2:0] ddr_req_proj;
  wire [511:0] ddr_req_wdata;
  wire [63:0] ddr_req_wstrb;
  reg ddr_req_ready=0,ddr_rsp_valid=0,ddr_rsp_id=0,ddr_rsp_error=0;
  reg [511:0] ddr_rsp_rdata=0;
  reg csr_req_valid=0,csr_req_write=0,csr_rsp_ready=0;
  reg [11:0] csr_req_addr=0;
  reg [31:0] csr_req_wdata=0;
  reg [3:0] csr_req_wstrb=0;
  wire csr_req_ready,csr_rsp_valid,csr_rsp_error;
  wire [31:0] csr_rsp_rdata;
  anvil_q1_fp2_top #(
    .NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),
    .NUM_Q_HEADS(1),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(1),
    .VOCAB_SIZE(1),.MAX_SEQ_LEN(3)) dut(.*);
  always #5 clk=~clk;
  integer cycle=0,completions=0,requests=0,accept_edge=-1,last_completion=-1;
  integer fault_mode=0,request_delay[0:1],scalar_delay=0;
  integer ddr_faults=0,scalar_faults=0,aborted=0,validation=0,test;
  reg outstanding[0:1],scalar_outstanding=0;
  reg request_accept,response_accept,scalar_request_accept,scalar_response_accept;
  reg finished;
  task reset_check;
    if ({token_ready,logit_valid,logit_index,logit_data,done,error,
      mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
      mem_req_row,mem_req_col,mem_req_wdata,mem_rsp_ready,ddr_req_valid,
      ddr_req_write,ddr_req_id,ddr_req_scale,ddr_req_kind,ddr_req_layer,ddr_req_proj,
      ddr_req_row,ddr_req_col,ddr_req_wdata,ddr_req_wstrb,ddr_rsp_ready,
      csr_req_ready,csr_rsp_valid,csr_rsp_rdata,csr_rsp_error} !== 0)
      $fatal(1,"top reset outputs");
  endtask
  task reset_epoch;
    begin
      rst_n=0; token_valid=0; ddr_rsp_valid=0; mem_rsp_valid=0;
      #1; reset_check(); @(posedge clk); reset_check();
      #1; reset_check(); @(negedge clk); reset_check();
      outstanding[0]=0; outstanding[1]=0; scalar_outstanding=0;
      accept_edge=-1; rst_n=1;
    end
  endtask
  task tick;
    integer n;
    begin
      cycle=cycle+1;
      if (cycle>100000) $fatal(1,"error-path cycle watchdog");
      ddr_req_ready=cycle%11>=3;
      mem_req_ready=!scalar_outstanding && cycle%7>=2;
      logit_ready=cycle[0];
      if (!ddr_rsp_valid && fault_mode!=3) begin
        if (outstanding[1] && request_delay[1]==0) begin
          ddr_rsp_valid=1; ddr_rsp_id=1;
        end else if (outstanding[0] && request_delay[0]==0) begin
          ddr_rsp_valid=1; ddr_rsp_id=0;
        end
        ddr_rsp_error=fault_mode==1;
      end
      if (scalar_outstanding && scalar_delay==0 && !mem_rsp_valid) begin
        mem_rsp_valid=1; mem_rsp_error=fault_mode==2; mem_rsp_rdata=32'h00003f80;
      end
      #1;
      if ((^{token_ready,logit_valid,done,error,mem_req_valid,mem_rsp_ready,
        ddr_req_valid,ddr_rsp_ready})===1'bx) $fatal(1,"error-path control X/Z");
      if (logit_valid) $fatal(1,"failed token emitted successful partial logit stream");
      if (token_valid && token_ready) begin
        if (accept_edge>=0) $fatal(1,"duplicate token acceptance");
        accept_edge=cycle;
      end
      if (error !== done) $fatal(1,"all tested completions must be errors");
      if (done) begin
        if (accept_edge<0 || cycle==last_completion+1) $fatal(1,"spurious/duplicate completion");
        if (outstanding[0] || outstanding[1] || scalar_outstanding)
          $fatal(1,"completion before memory ownership retires");
        if (fault_mode==0 && cycle!=accept_edge+2)
          $fatal(1,"top validation completion edge mismatch");
        last_completion=cycle; completions=completions+1; accept_edge=-1;
      end
      request_accept=ddr_req_valid && ddr_req_ready;
      response_accept=ddr_rsp_valid && ddr_rsp_ready;
      scalar_request_accept=mem_req_valid && mem_req_ready;
      scalar_response_accept=mem_rsp_valid && mem_rsp_ready;
      if (fault_mode==0 && (ddr_req_valid || mem_req_valid))
        $fatal(1,"invalid command issued memory request");
      if (ddr_req_valid && (ddr_req_write || ddr_req_kind!=0 ||
          ddr_req_layer!=0 || ddr_req_proj!=0 || ddr_req_row!=0 || ddr_req_col!=0))
        $fatal(1,"token fields changed while busy or unexpected tensor before fault");
      if (mem_req_valid && (mem_req_write || mem_req_kind!=5 || mem_req_col!=0))
        $fatal(1,"unexpected scalar request before injected gamma fault");
      @(posedge clk);
      if (request_accept) begin
        if (outstanding[ddr_req_id]) $fatal(1,"error-path DDR ID reuse");
        outstanding[ddr_req_id]=1; request_delay[ddr_req_id]=4;
        requests=requests+1;
      end
      if (response_accept) begin
        if (!outstanding[ddr_rsp_id]) $fatal(1,"unexpected error response acceptance");
        outstanding[ddr_rsp_id]=0;
        if (ddr_rsp_error) ddr_faults=ddr_faults+1;
      end
      if (scalar_request_accept) begin scalar_outstanding=1; scalar_delay=3; end
      if (scalar_response_accept) begin
        scalar_outstanding=0;
        if (mem_rsp_error) scalar_faults=scalar_faults+1;
      end
      #1;
      if (response_accept) ddr_rsp_valid=0;
      if (scalar_response_accept) mem_rsp_valid=0;
      for (n=0;n<2;n=n+1)
        if (outstanding[n] && request_delay[n]>0) request_delay[n]=request_delay[n]-1;
      if (scalar_outstanding && scalar_delay>0) scalar_delay=scalar_delay-1;
      @(negedge clk);
    end
  endtask
  task command(input [31:0] id,pos,input fresh,input [1:0] mode);
    integer old_completions;
    begin
      old_completions=completions;
      token_id=id; token_pos=pos; new_sequence=fresh; precision_mode=mode;
      token_valid=1;
      tick();
      if (accept_edge<0) $fatal(1,"token was not accepted");
      token_valid=0;
      token_id=32'hffffffff; token_pos=32'hffffffff; precision_mode=0; new_sequence=0;
      while (completions==old_completions) tick();
      tick(); tick();
      if (!token_ready) $fatal(1,"error did not return idle");
    end
  endtask
  initial begin
    outstanding[0]=0; outstanding[1]=0;
    #1; reset_check(); @(posedge clk); reset_check();
    #1; reset_check(); @(negedge clk); reset_check(); rst_n=1;
    fault_mode=0;
    command(0,0,0,1); validation=validation+1;
    command(0,1,1,1); validation=validation+1;
    command(1,0,1,1); validation=validation+1;
    command(0,3,1,1); validation=validation+1;
    for (test=0;test<2;test=test+1) begin
      fault_mode=1; command(0,0,1,test==0 ? 1 : 3);
      fault_mode=0; command(0,1,0,test==0 ? 1 : 3); validation=validation+1;
      fault_mode=2; command(0,0,1,test==0 ? 1 : 3);
      fault_mode=0; command(0,1,0,test==0 ? 1 : 3); validation=validation+1;
    end
    fault_mode=3; token_id=0; token_pos=0; new_sequence=1; precision_mode=1;
    token_valid=1; tick(); token_valid=0;
    while (!outstanding[0] && !outstanding[1]) tick();
    if (accept_edge<0) $fatal(1,"missing live reset precondition");
    aborted=aborted+1; reset_epoch();
    fault_mode=0; command(0,0,0,1); validation=validation+1;
    if (ddr_faults!=2 || scalar_faults!=2 || aborted!=1 ||
        validation!=9 || completions!=13 || requests<6)
      $fatal(1,"error coverage missing: ddr=%0d scalar=%0d abort=%0d validation=%0d done=%0d",
        ddr_faults,scalar_faults,aborted,validation,completions);
    $display("SUMMARY top-errors: completions=%0d validation=%0d ddr_faults=%0d scalar_faults=%0d reset_aborts=%0d",
      completions,validation,ddr_faults,scalar_faults,aborted);
    $finish;
  end
endmodule
""")
    sources = [str(path.relative_to(root)) for pattern in (
        "anvil_q1_fp_reference/rtl/*.sv", "rtl/*.sv") for path in sorted(root.glob(pattern))]
    compile_and_run(run, directory, bench, sources, simulator, stem)
    run.receipt["comparisons"].append({
        "kind": "top-errors", "validation": 9, "ddr_faults": 2,
        "scalar_faults": 2, "reset_aborted_tokens": 1, "completions": 13,
        "result": "passed",
    })
