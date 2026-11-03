"""Independent transaction queues and register/event scoreboards."""

from integration_checks import CSR_TASK
from leaf_checks import simulate


def cdc(directory, kind="response_fifo", simulator="verilator"):
    body = r"""
  reg destination_clk=0;
  always #7 destination_clk=~destination_clk;
  reg source_valid=0,destination_ready=0;
  wire source_ready,destination_valid;
  reg [514:0] source_data=0;
  wire [514:0] destination_data;
  reg [514:0] queue[0:4095];
  integer pushed=0,popped=0,stalled=0,full_seen=0,epoch=0,phase=0,age=0;
  reg held_valid=0;
  reg [514:0] held_data=0;
  INSTANCE
  function automatic [514:0] payload(input integer n);
    begin payload={3'(n),32'(n^32'hac53914f),{15{32'(n*32'h2194a651)}}}; end
  endfunction
  always @(posedge clk) begin
    if (!rst_n) begin
      if ({source_ready,destination_valid,destination_data} !== 0)
        $fatal(1,"CDC_RESET_XZ");
    end else if (source_valid && source_ready) begin
      if (pushed>=4096) $fatal(1,"QUEUE_BOUND");
      queue[pushed]=source_data; pushed=pushed+1;
    end else if (source_valid && !source_ready) full_seen=full_seen+1;
  end
  always @(negedge clk) begin
    if (!rst_n && {source_ready,destination_valid,destination_data} !== 0)
      $fatal(1,"CDC_RESET_XZ");
    if (phase==1 || phase==2) begin
      source_valid=(pushed<LIMIT);
      source_data=payload(pushed+epoch*8192);
    end else source_valid=0;
  end
  always @(negedge destination_clk) begin
    age=age+1;
    destination_ready=(phase==2 && age%7<4);
    if (!rst_n && {source_ready,destination_valid,destination_data} !== 0)
      $fatal(1,"CDC_RESET_XZ");
  end
  always @(posedge destination_clk) begin
    if (!rst_n) begin
      held_valid=0;
      if ({source_ready,destination_valid,destination_data} !== 0)
        $fatal(1,"CDC_RESET_XZ");
    end else begin
      if (held_valid && {destination_valid,destination_data} !== {1'b1,held_data})
        $fatal(1,"CDC_STABILITY");
      held_valid=destination_valid && !destination_ready;
      held_data=destination_data;
      if (destination_valid===1) begin
        if (popped>=pushed || destination_data!==queue[popped])
          $fatal(1,"CDC_PAYLOAD epoch=%0d item=%0d got=%h expected=%h",
                 epoch,popped,destination_data,queue[popped]);
        checked=checked+1;
        if (destination_ready) popped=popped+1; else stalled=stalled+1;
      end else if (destination_valid!==0) $fatal(1,"CDC_VALID_XZ");
    end
  end
  initial begin
    INITIAL_CHECK
    repeat(4) tick(); @(negedge clk); rst_n=1; repeat(10) tick();
    phase=1; repeat(FILL_CYCLES) tick();
    if (full_seen==0 || pushed==0 || popped!=0) $fatal(1,"CDC_FULL_COVERAGE");
    phase=2;
    while (popped<LIMIT) tick();
    phase=0; repeat(20) tick();
    if (pushed!=popped || stalled==0) $fatal(1,"CDC_CONSERVATION");
    phase=1; epoch=1; pushed=0; popped=0; repeat(40) tick();
    if (pushed==0) $fatal(1,"RESET_OUTSTANDING_COVERAGE");
    @(negedge clk); #2; rst_n=0; phase=0;
    #1; if ({source_ready,destination_valid,destination_data} !== 0)
      $fatal(1,"CDC_ASYNC_RESET");
    repeat(5) tick(); pushed=0; popped=0; epoch=2;
    @(negedge clk); rst_n=1; repeat(10) tick(); phase=2;
    while (popped<LIMIT) tick();
    phase=0; repeat(20) tick();
    if (pushed!=popped) $fatal(1,"CDC_RESET_EPOCH_CONSERVATION");
    $display("CHECK compared=%0d delivered=%0d full_observations=%0d stalls=%0d",
             checked,popped,full_seen,stalled);
    $finish;
  end
"""
    body = body.replace("INSTANCE", (
        "anvil_q1_ht2_mailbox #(.WIDTH(515))" if kind == "mailbox" else
        "anvil_q1_ht2_response_fifo") +
        " dut(clk,destination_clk,rst_n,source_valid,source_ready,source_data,"
        "destination_valid,destination_ready,destination_data);")
    body = body.replace("LIMIT", "80" if kind == "mailbox" else "1200")
    body = body.replace("FILL_CYCLES", "50" if kind == "mailbox" else "650")
    body = body.replace("INITIAL_CHECK", "#1;" if simulator == "verilator" else "#0;")
    return simulate(directory, f"cdc-{kind}-{simulator}", body, [kind], simulator)


def control(directory, simulator="verilator"):
    body = r"""
  reg ddr_clk=0;
  always #7 ddr_clk=~ddr_clk;
  reg initialized=0,image_valid=0,execution_busy=0,image_loading=0,pending_results=0;
  reg sticky_error=0,ddr_read_beat=0;
  reg [2:0] accepted_tokens=0;
  reg completed_batch=0;
  reg [31:0] eligible_bytes=0,avoided_bytes=0;
  wire [3:0] configuration;
  wire [15:0] sparse_threshold;
  wire invalidate_image,invalidate_prefix;
  reg csr_valid=0,csr_write=0,csr_rsp_ready=0;
  reg [15:0] csr_address=0;
  reg [31:0] csr_wdata=0;
  wire csr_ready,csr_rsp_valid,csr_error;
  wire [31:0] csr_rdata;
  wire legacy_valid,legacy_write,legacy_rsp_ready;
  wire [15:0] legacy_address;
  wire [31:0] legacy_wdata;
  reg legacy_ready=0,legacy_rsp_valid=0,legacy_error=0;
  reg [31:0] legacy_rdata=0;
  reg counting=0;
  reg [63:0] accepted=0,batches=0,eligible=0,avoided=0,snapshot=0;
  integer counter,iteration;
  anvil_q1_ht2_control dut(.*);
  always @(posedge clk) if (counting) begin
    if (csr_valid && csr_ready && csr_address==16'h110) snapshot=accepted;
    accepted=accepted+accepted_tokens; batches=batches+completed_batch;
    eligible=eligible+eligible_bytes; avoided=avoided+avoided_bytes;
  end
  always @(posedge clk or negedge clk) if (!rst_n &&
    {configuration,sparse_threshold,invalidate_image,invalidate_prefix,csr_ready,
     csr_rsp_valid,csr_rdata,csr_error,legacy_valid,legacy_write,legacy_address,
     legacy_wdata,legacy_rsp_ready} !== 0) $fatal(1,"CONTROL_RESET_XZ");
"""
    body += CSR_TASK
    body += r"""
  initial begin
    INITIAL_CHECK
    repeat(4) tick(); @(negedge clk); rst_n=1; repeat(10) tick(); counting=1;
    csr(0,16'h100,0,0,1,0); csr(0,16'h104,0,0,1,0);
    csr(1,16'h100,15,1,1,0); csr(0,16'h100,0,0,1,0);
    csr(1,16'h100,16,1,1,0);
    csr(1,16'h104,32'hbf80,1,1,0);
    csr(1,16'h104,32'h7f80,1,1,0);
    csr(1,16'h104,32'h7fc0,1,1,0);
    csr(1,16'h104,32'h10000,1,1,0);
    csr(1,16'h104,32'h8000,0,1,0);
    csr(0,16'h104,0,0,1,32'h8000);
    csr(1,16'h104,32'h3c00,0,1,0);
    for (iteration=0;iteration<3;iteration=iteration+1) begin
      @(negedge clk);
      execution_busy=(iteration==0); image_loading=(iteration==1); pending_results=(iteration==2);
      csr(1,16'h100,12,1,1,0); csr(1,16'h104,0,1,1,0);
      csr(0,16'h100,0,0,1,0); csr(0,16'h104,0,0,1,32'h3c00);
    end
    @(negedge clk); execution_busy=0; image_loading=0; pending_results=0;
    initialized=1; image_valid=1; sticky_error=1;
    csr(0,16'h108,0,0,1,11);
    csr(1,16'h100,12,0,1,0); csr(0,16'h100,0,0,1,12);
    for (counter=16'h110;counter<=16'h134;counter=counter+8) begin
      csr(0,16'(counter+4),0,1,1,0);
      csr(0,16'(counter),0,0,1,0);
      csr(0,16'(counter+4),0,0,1,0);
      csr(0,16'(counter+4),0,1,1,0);
    end
    for (counter=16'h138;counter<=16'h14c;counter=counter+4) begin
      csr(0,16'(counter),0,0,1,0); csr(1,16'(counter),0,1,1,0);
    end
    csr(0,16'h10c,0,0,1,0); csr(1,16'h10c,0,1,1,0);
    csr(0,16'h111,0,1,1,0); csr(0,16'h150,0,1,1,0);
    @(negedge clk); accepted_tokens=7; completed_batch=1;
    eligible_bytes=32'hffffffff; avoided_bytes=32'h80000001;
    repeat(5) tick();
    csr(0,16'h110,0,0,0,0);
    if (response!==snapshot[31:0]) $fatal(1,"ATOMIC_LOW_COUNTER");
    csr(0,16'h114,0,0,1,snapshot[63:32]);
    @(negedge clk); accepted_tokens=0; completed_batch=0; eligible_bytes=0; avoided_bytes=0;
    csr(0,16'h110,0,0,1,accepted[31:0]); csr(0,16'h114,0,0,1,accepted[63:32]);
    csr(0,16'h118,0,0,1,batches[31:0]); csr(0,16'h11c,0,0,1,batches[63:32]);
    csr(0,16'h128,0,0,1,eligible[31:0]); csr(0,16'h12c,0,0,1,eligible[63:32]);
    csr(0,16'h130,0,0,1,avoided[31:0]); csr(0,16'h134,0,0,1,avoided[63:32]);
    @(negedge ddr_clk); ddr_read_beat=1;
    repeat(23) @(posedge ddr_clk);
    @(negedge ddr_clk); ddr_read_beat=0;
    csr(0,16'h120,0,0,1,23*64); csr(0,16'h124,0,0,1,0);
    if (eligible[63:32]==0 || avoided[63:32]==0 || accepted==0 || batches==0)
      $fatal(1,"COUNTER_WRAP_COVERAGE");
    $display("CHECK compared=%0d csr=%0d low_word_wraps=%0d",checked,csr_calls,eligible[63:32]);
    $finish;
  end
"""
    body = body.replace("INITIAL_CHECK", "#1;" if simulator == "verilator" else "#0;")
    return simulate(directory, "control-" + simulator, body, ["control", "counter_cdc"], simulator)
