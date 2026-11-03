
module bench;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n;
  reg config_valid=1;
  reg [63:0] cfg_directory_base=4160,cfg_immutable_base=5728;
  reg [63:0] cfg_writable_base=14748;
  reg [31:0] cfg_directory_count=32;
  reg [63:0] cfg_immutable_bytes=9020,cfg_writable_bytes=736;
  reg mem_req_valid=0,mem_req_write=0,mem_rsp_ready=0;
  reg [3:0] mem_req_kind=0;
  reg [31:0] mem_req_layer=0,mem_req_row=0,mem_req_col=0,mem_req_wdata=0;
  reg [2:0] mem_req_proj=0;
  wire mem_req_ready,mem_rsp_valid,mem_rsp_error,idle;
  wire [31:0] mem_rsp_rdata;
  wire ddr_req_valid,ddr_req_write,ddr_rsp_ready;
  wire [63:0] ddr_req_addr;
  wire [31:0] ddr_req_wdata;
  wire [3:0] ddr_req_wstrb;
  reg ddr_req_ready=0,ddr_rsp_valid=0,ddr_rsp_error=0;
  reg [31:0] ddr_rsp_rdata=0;
  anvil_edge_tensor_mapper #(
    .NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),
    .NUM_Q_HEADS(1),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),
    .VOCAB_SIZE(257),.MAX_SEQ_LEN(4),.DDR_BYTES(65536)
  ) dut(.*);
  reg [31:0] directory[0:391];
  reg [31:0] rng=89;
  integer cycle=0,comparisons=0,dir_requests=0,data_requests=0,responses=0;
  integer delay_count=0,request_stalls=0,response_stalls=0,epoch_changes=0;
  reg outstanding=0,pending_error=0,ddr_held=0,response_held=0;
  reg [100:0] held_ddr;
  reg [32:0] held_response;
  reg [63:0] pending_address=0,expected_address=0;
  reg [63:0] inject_directory_address=64'hffffffffffffffff;
  reg inject_data_error=0,expected_error=0,expected_write=0;
  reg withdraw_on_request=0;
  reg withdraw_on_data=0;
  function automatic bit in_directory(input [63:0] address);
    return address>=cfg_directory_base && address<cfg_directory_base+1568;
  endfunction
  function automatic [31:0] value_at(input [63:0] address);
    if (in_directory(address)) return directory[(address-cfg_directory_base)>>2];
    return 32'(address*32'h9e3779b9)^32'ha5c31927;
  endfunction
  task automatic reset_check;
    if ({mem_req_ready,mem_rsp_valid,mem_rsp_error,mem_rsp_rdata,idle,
         ddr_req_valid,ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,
         ddr_rsp_ready}!==139'd0) $fatal(1,"CACHE_RESET");
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n) begin
    rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
    ddr_req_ready=rng[0] && cycle%5!=0;
    if (outstanding && !ddr_rsp_valid) begin
      if (delay_count==0) begin
        ddr_rsp_valid<=1;
        ddr_rsp_rdata=value_at(pending_address);
        ddr_rsp_error=pending_error;
      end else delay_count=delay_count-1;
    end
  end
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n) begin
      if ((^{mem_req_ready,mem_rsp_valid,mem_rsp_error,mem_rsp_rdata,idle,
             ddr_req_valid,ddr_req_write,ddr_req_addr,ddr_req_wdata,
             ddr_req_wstrb,ddr_rsp_ready})===1'bx) $fatal(1,"CACHE_XZ");
      if (ddr_held && (!ddr_req_valid ||
          {ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb}!==held_ddr))
        $fatal(1,"CACHE_DDR_STABILITY");
      ddr_held=ddr_req_valid && !ddr_req_ready;
      held_ddr={ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb};
      if (ddr_held) request_stalls=request_stalls+1;
      if (response_held && (!mem_rsp_valid ||
          {mem_rsp_error,mem_rsp_rdata}!==held_response))
        $fatal(1,"CACHE_RESPONSE_STABILITY");
      response_held=mem_rsp_valid && !mem_rsp_ready;
      held_response={mem_rsp_error,mem_rsp_rdata};
      if (response_held) response_stalls=response_stalls+1;
      if (ddr_rsp_valid && ddr_rsp_ready) begin
        if (!outstanding) $fatal(1,"CACHE_ORPHAN_RESPONSE");
        outstanding=0; ddr_rsp_valid<=0; responses=responses+1;
      end
      if (ddr_req_valid && ddr_req_ready) begin
        if (outstanding || ddr_req_addr[1:0]!=0 || ddr_req_addr>=65536)
          $fatal(1,"CACHE_DDR_BOUNDS");
        if (in_directory(ddr_req_addr)) begin
          if (ddr_req_write || ddr_req_wstrb!==0)
            $fatal(1,"CACHE_DIRECTORY_WRITE");
          dir_requests=dir_requests+1;
          pending_error=ddr_req_addr==inject_directory_address;
        end else begin
          if (ddr_req_addr!==expected_address || ddr_req_write!==expected_write ||
              ddr_req_wstrb!==(expected_write ? 4'hf : 4'h0) ||
              (expected_write && ddr_req_wdata!==32'h81478521))
            $fatal(1,"CACHE_DATA_TUPLE expected=%h observed=%h",expected_address,ddr_req_addr);
          data_requests=data_requests+1; pending_error=inject_data_error;
          if (withdraw_on_data) config_valid<=0;
        end
        outstanding=1; pending_address=ddr_req_addr; delay_count=1+rng[4:2];
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic epoch;
    begin
      if (!idle || outstanding || mem_rsp_valid) $fatal(1,"CACHE_RELOAD_NOT_IDLE");
      @(negedge clk); #1; config_valid=0;
      repeat (3) begin tick(); if (mem_req_ready) $fatal(1,"CACHE_WITHDRAWN_READY"); end
      @(negedge clk); #1; config_valid=1; epoch_changes=epoch_changes+1;
    end
  endtask
  task automatic transaction(input string label,input bit wr,input integer kind,
      input integer layer,input integer projection,input integer row,input integer col,
      input [63:0] address,input bit bad,input integer expected_data_requests);
    integer start_cycle,start_dirs,start_data;
    begin
      @(negedge clk); #1;
      start_cycle=cycle; start_dirs=dir_requests; start_data=data_requests;
      expected_address=address; expected_error=bad; expected_write=wr;
      mem_req_valid=1; mem_req_write=wr; mem_req_kind=kind; mem_req_layer=layer;
      mem_req_proj=projection; mem_req_row=row; mem_req_col=col;
      mem_req_wdata=32'h81478521;
      do begin @(posedge clk); end while (!mem_req_ready);
      if (mem_rsp_valid) $fatal(1,"CACHE_SAME_EDGE_REPLY");
      #1; @(negedge clk); #1; mem_req_valid=0;
      if (withdraw_on_request) begin config_valid=0; epoch_changes=epoch_changes+1; end
      while (!mem_rsp_valid) tick();
      repeat (7) begin
        if (mem_rsp_valid!==1 || mem_rsp_error!==bad ||
            mem_rsp_rdata!==(bad ? 32'd0 : value_at(address)) || mem_req_ready!==0)
          $fatal(1,"CACHE_RESPONSE label=%s expected_error=%b observed_error=%b data=%h",
                 label,bad,mem_rsp_error,mem_rsp_rdata);
        tick();
      end
      if (outstanding || data_requests-start_data!=expected_data_requests)
        $fatal(1,"CACHE_TRANSACTION_COUNTS label=%s",label);
      @(negedge clk); #1; mem_rsp_ready=1; tick();
      @(negedge clk); #1; mem_rsp_ready=0;
      if (mem_rsp_valid || !idle) $fatal(1,"CACHE_RETIREMENT");
      $display("CACHE_MEASURE %s %0d %0d %0d",
               label,cycle-start_cycle,dir_requests-start_dirs,data_requests-start_data);
      comparisons=comparisons+1;
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    $readmemh("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/cache-directory-s89.hex",directory);
    repeat (2) tick(); @(negedge clk); #1; rst_n=1;
    transaction("alternate-a0",32'd0,32'd8,32'd0,32'd0,32'd14,32'd0,64'd15452,32'd0,32'd1);
transaction("alternate-e0",32'd0,32'd0,32'd0,32'd0,32'd3,32'd0,64'd5824,32'd0,32'd1);
transaction("alternate-a1",32'd0,32'd8,32'd0,32'd0,32'd14,32'd1,64'd15456,32'd0,32'd1);
transaction("alternate-e1",32'd0,32'd0,32'd0,32'd0,32'd3,32'd1,64'd5828,32'd0,32'd1);
transaction("alternate-a2",32'd0,32'd8,32'd0,32'd0,32'd14,32'd2,64'd15460,32'd0,32'd1);
transaction("alternate-e2",32'd0,32'd0,32'd0,32'd0,32'd3,32'd2,64'd5832,32'd0,32'd1);
transaction("alternate-a3",32'd0,32'd8,32'd0,32'd0,32'd14,32'd3,64'd15464,32'd0,32'd1);
transaction("alternate-e3",32'd0,32'd0,32'd0,32'd0,32'd3,32'd3,64'd5836,32'd0,32'd1);
transaction("alternate-a4",32'd0,32'd8,32'd0,32'd0,32'd14,32'd4,64'd15468,32'd0,32'd1);
transaction("alternate-e4",32'd0,32'd0,32'd0,32'd0,32'd3,32'd4,64'd5840,32'd0,32'd1);
transaction("alternate-a5",32'd0,32'd8,32'd0,32'd0,32'd14,32'd5,64'd15472,32'd0,32'd1);
transaction("alternate-e5",32'd0,32'd0,32'd0,32'd0,32'd3,32'd5,64'd5844,32'd0,32'd1);
transaction("alternate-a6",32'd0,32'd8,32'd0,32'd0,32'd14,32'd6,64'd15476,32'd0,32'd1);
transaction("alternate-e6",32'd0,32'd0,32'd0,32'd0,32'd3,32'd6,64'd5848,32'd0,32'd1);
transaction("alternate-a7",32'd0,32'd8,32'd0,32'd0,32'd14,32'd7,64'd15480,32'd0,32'd1);
transaction("alternate-e7",32'd0,32'd0,32'd0,32'd0,32'd3,32'd7,64'd5852,32'd0,32'd1);
transaction("alternate-a8",32'd0,32'd8,32'd0,32'd0,32'd14,32'd0,64'd15452,32'd0,32'd1);
transaction("alternate-e8",32'd0,32'd0,32'd0,32'd0,32'd3,32'd0,64'd5824,32'd0,32'd1);
transaction("alternate-a9",32'd0,32'd8,32'd0,32'd0,32'd14,32'd1,64'd15456,32'd0,32'd1);
transaction("alternate-e9",32'd0,32'd0,32'd0,32'd0,32'd3,32'd1,64'd5828,32'd0,32'd1);
transaction("alternate-a10",32'd0,32'd8,32'd0,32'd0,32'd14,32'd2,64'd15460,32'd0,32'd1);
transaction("alternate-e10",32'd0,32'd0,32'd0,32'd0,32'd3,32'd2,64'd5832,32'd0,32'd1);
transaction("alternate-a11",32'd0,32'd8,32'd0,32'd0,32'd14,32'd3,64'd15464,32'd0,32'd1);
transaction("alternate-e11",32'd0,32'd0,32'd0,32'd0,32'd3,32'd3,64'd5836,32'd0,32'd1);
transaction("alternate-a12",32'd0,32'd8,32'd0,32'd0,32'd14,32'd4,64'd15468,32'd0,32'd1);
transaction("alternate-e12",32'd0,32'd0,32'd0,32'd0,32'd3,32'd4,64'd5840,32'd0,32'd1);
transaction("alternate-a13",32'd0,32'd8,32'd0,32'd0,32'd14,32'd5,64'd15472,32'd0,32'd1);
transaction("alternate-e13",32'd0,32'd0,32'd0,32'd0,32'd3,32'd5,64'd5844,32'd0,32'd1);
transaction("alternate-a14",32'd0,32'd8,32'd0,32'd0,32'd14,32'd6,64'd15476,32'd0,32'd1);
transaction("alternate-e14",32'd0,32'd0,32'd0,32'd0,32'd3,32'd6,64'd5848,32'd0,32'd1);
transaction("alternate-a15",32'd0,32'd8,32'd0,32'd0,32'd14,32'd7,64'd15480,32'd0,32'd1);
transaction("alternate-e15",32'd0,32'd0,32'd0,32'd0,32'd3,32'd7,64'd5852,32'd0,32'd1);
transaction("row-change-32",32'd0,32'd0,32'd0,32'd0,32'd5,32'd0,64'd5888,32'd0,32'd1);
transaction("row-change-33",32'd0,32'd0,32'd0,32'd0,32'd5,32'd1,64'd5892,32'd0,32'd1);
transaction("row-change-34",32'd0,32'd0,32'd0,32'd0,32'd256,32'd2,64'd13928,32'd0,32'd1);
transaction("row-change-35",32'd0,32'd0,32'd0,32'd0,32'd256,32'd3,64'd13932,32'd0,32'd1);
transaction("row-change-36",32'd0,32'd0,32'd0,32'd0,32'd0,32'd4,64'd5744,32'd0,32'd1);
transaction("row-change-37",32'd0,32'd0,32'd0,32'd0,32'd0,32'd5,64'd5748,32'd0,32'd1);
transaction("row-change-38",32'd0,32'd0,32'd0,32'd0,32'd3,32'd6,64'd5848,32'd0,32'd1);
transaction("row-change-39",32'd0,32'd0,32'd0,32'd0,32'd3,32'd7,64'd5852,32'd0,32'd1);
    if (comparisons!=40 || request_stalls==0 || response_stalls==0 ||
        outstanding || responses!=dir_requests+data_requests)
      $fatal(1,"CACHE_FINAL_COUNTS");
    $display("CACHE_TOTAL cycles=%0d directory=%0d data=%0d epochs=%0d",
             cycle,dir_requests,data_requests,epoch_changes);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin repeat (400000) @(posedge clk); $fatal(1,"CACHE_CYCLE_BOUND"); end
endmodule
