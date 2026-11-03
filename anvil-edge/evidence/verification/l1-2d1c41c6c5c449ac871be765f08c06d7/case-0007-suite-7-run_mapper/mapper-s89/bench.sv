
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
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
  reg outstanding=0,held=0,expected_error=0,expected_write=0,inject_error=0;
  reg [63:0] held_addr=0,pending_address=0,expected_address=0;
  reg [36:0] held_fields=0;
  reg pending_data=0;
  integer cycle=0,delay_count=0,data_requests=0,all_requests=0,comparisons=0;
  integer request_stalls=0;
  function automatic [31:0] value_at(input [63:0] address);
    begin
      if (address>=cfg_directory_base && address<cfg_directory_base+1568)
        value_at=directory[(address-cfg_directory_base)>>2];
      else value_at=32'(address*32'h9e3779b9)^32'ha5c31927;
    end
  endfunction
  task automatic reset_check;
    begin
      if ({mem_req_ready,mem_rsp_valid,mem_rsp_error,mem_rsp_rdata,idle,
           ddr_req_valid,ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,
           ddr_rsp_ready}!==139'd0) $fatal(1,"MAPPER_RESET");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n) begin
    rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
    ddr_req_ready=rng[0] && cycle%5!=0;
    if (outstanding && !ddr_rsp_valid) begin
      if (delay_count==0) begin
        ddr_rsp_valid<=1; ddr_rsp_rdata=value_at(pending_address);
        ddr_rsp_error=pending_data && inject_error;
      end else delay_count=delay_count-1;
    end
  end
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n) begin
      if ((^{mem_req_ready,mem_rsp_valid,mem_rsp_error,mem_rsp_rdata,idle,
             ddr_req_valid,ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,
             ddr_rsp_ready})===1'bx) $fatal(1,"MAPPER_XZ");
      if (held && (!ddr_req_valid || ddr_req_addr!==held_addr ||
          {ddr_req_write,ddr_req_wdata,ddr_req_wstrb}!==held_fields))
        $fatal(1,"MAPPER_REQUEST_STABILITY");
      held=ddr_req_valid && !ddr_req_ready;
      held_addr=ddr_req_addr; held_fields={ddr_req_write,ddr_req_wdata,ddr_req_wstrb};
      if (held) request_stalls=request_stalls+1;
      if (ddr_rsp_valid && ddr_rsp_ready) begin
        if (!outstanding) $fatal(1,"MAPPER_ORPHAN_RESPONSE");
        outstanding=0; ddr_rsp_valid<=0;
      end
      if (ddr_req_valid && ddr_req_ready) begin
        if (outstanding || (expected_error && !inject_error) || ddr_req_addr[1:0]!=0)
          $fatal(1,"MAPPER_FORBIDDEN_REQUEST kind=%0d row=%0d col=%0d",
                 mem_req_kind,mem_req_row,mem_req_col);
        all_requests=all_requests+1;
        pending_data=!(ddr_req_addr>=cfg_directory_base &&
                       ddr_req_addr<cfg_directory_base+1568);
        if (pending_data) begin
          if (data_requests!=0 || ddr_req_addr!==expected_address ||
              ddr_req_write!==expected_write ||
              ddr_req_wstrb!==(expected_write ? 4'hf : 4'h0) ||
              (expected_write && ddr_req_wdata!==mem_req_wdata))
            $fatal(1,"MAPPER_DATA_ADDRESS expected=%h observed=%h",
                   expected_address,ddr_req_addr);
          data_requests=data_requests+1;
        end else if (ddr_req_write || ddr_req_wstrb!==0)
          $fatal(1,"MAPPER_DIRECTORY_WRITE");
        outstanding=1; pending_address=ddr_req_addr; delay_count=1+rng[4:2];
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic transaction(input bit wr,input integer kind,input integer layer,
                             input integer projection,input integer row,input integer col,
                             input [63:0] address,input bit bad,input bit bus_error);
    integer previous_requests;
    begin
      @(negedge clk); #1;
      expected_error=bad; expected_write=wr; expected_address=address;
      inject_error=bus_error; data_requests=0; previous_requests=all_requests;
      mem_req_valid=1; mem_req_write=wr; mem_req_kind=kind; mem_req_layer=layer;
      mem_req_proj=projection; mem_req_row=row; mem_req_col=col;
      mem_req_wdata=32'h81478521;
      do begin @(posedge clk); end while (!mem_req_ready);
      #1; @(negedge clk); #1; mem_req_valid=0;
      while (!mem_rsp_valid) tick();
      repeat (5) begin
        if (mem_rsp_valid!==1 || mem_rsp_error!==bad ||
            mem_rsp_rdata!==(bad ? 32'd0 : value_at(address)) || mem_req_ready!==0)
          $fatal(1,"MAPPER_RESPONSE kind=%0d row=%0d col=%0d error=%b data=%h",
                 kind,row,col,mem_rsp_error,mem_rsp_rdata);
        tick();
      end
      if (outstanding || data_requests!=(bad && !bus_error ? 0 : 1) ||
          (bad && !bus_error && all_requests!=previous_requests))
        $fatal(1,"MAPPER_COUNTS");
      @(negedge clk); #1; mem_rsp_ready=1; tick();
      @(negedge clk); #1; mem_rsp_ready=0;
      if (mem_rsp_valid || !idle) $fatal(1,"MAPPER_RETIREMENT");
      comparisons=comparisons+1;
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    $readmemh("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0007-suite-7-run_mapper/mapper-s89-input/directory.hex",directory);
    repeat (2) tick(); @(negedge clk); #1; rst_n=1;
    transaction(0,0,0,0,0,0,5728,0,0);
transaction(0,0,0,0,256,7,13948,0,0);
transaction(0,0,0,0,257,0,0,1,0);
transaction(0,0,0,0,0,8,0,1,0);
transaction(1,0,0,0,0,0,0,1,0);
transaction(0,1,0,0,0,0,13952,0,0);
transaction(0,1,0,0,7,0,13980,0,0);
transaction(0,1,0,0,8,0,0,1,0);
transaction(0,1,0,0,0,1,0,1,0);
transaction(1,1,0,0,0,0,0,1,0);
transaction(0,1,0,1,0,0,14052,0,0);
transaction(0,1,0,1,7,0,14080,0,0);
transaction(0,1,0,1,8,0,0,1,0);
transaction(0,1,0,1,0,1,0,1,0);
transaction(1,1,0,1,0,0,0,1,0);
transaction(0,1,0,2,0,0,14152,0,0);
transaction(0,1,0,2,7,0,14180,0,0);
transaction(0,1,0,2,8,0,0,1,0);
transaction(0,1,0,2,0,1,0,1,0);
transaction(1,1,0,2,0,0,0,1,0);
transaction(0,1,0,3,0,0,14252,0,0);
transaction(0,1,0,3,7,0,14280,0,0);
transaction(0,1,0,3,8,0,0,1,0);
transaction(0,1,0,3,0,1,0,1,0);
transaction(1,1,0,3,0,0,0,1,0);
transaction(0,1,0,4,0,0,14320,0,0);
transaction(0,1,0,4,7,0,14348,0,0);
transaction(0,1,0,4,8,0,0,1,0);
transaction(0,1,0,4,0,1,0,1,0);
transaction(1,1,0,4,0,0,0,1,0);
transaction(0,1,0,5,0,0,14388,0,0);
transaction(0,1,0,5,7,0,14416,0,0);
transaction(0,1,0,5,8,0,0,1,0);
transaction(0,1,0,5,0,1,0,1,0);
transaction(1,1,0,5,0,0,0,1,0);
transaction(0,1,0,6,0,0,14456,0,0);
transaction(0,1,0,6,7,0,14484,0,0);
transaction(0,1,0,6,8,0,0,1,0);
transaction(0,1,0,6,0,1,0,1,0);
transaction(1,1,0,6,0,0,0,1,0);
transaction(0,2,0,0,0,0,13984,0,0);
transaction(0,2,0,0,0,0,13984,0,0);
transaction(0,2,0,0,1,0,0,1,0);
transaction(0,2,0,0,0,1,0,1,0);
transaction(1,2,0,0,0,0,0,1,0);
transaction(0,2,0,1,0,0,14084,0,0);
transaction(0,2,0,1,0,0,14084,0,0);
transaction(0,2,0,1,1,0,0,1,0);
transaction(0,2,0,1,0,1,0,1,0);
transaction(1,2,0,1,0,0,0,1,0);
transaction(0,2,0,2,0,0,14184,0,0);
transaction(0,2,0,2,0,0,14184,0,0);
transaction(0,2,0,2,1,0,0,1,0);
transaction(0,2,0,2,0,1,0,1,0);
transaction(1,2,0,2,0,0,0,1,0);
transaction(0,2,0,3,0,0,14284,0,0);
transaction(0,2,0,3,0,0,14284,0,0);
transaction(0,2,0,3,1,0,0,1,0);
transaction(0,2,0,3,0,1,0,1,0);
transaction(1,2,0,3,0,0,0,1,0);
transaction(0,2,0,4,0,0,14352,0,0);
transaction(0,2,0,4,0,0,14352,0,0);
transaction(0,2,0,4,1,0,0,1,0);
transaction(0,2,0,4,0,1,0,1,0);
transaction(1,2,0,4,0,0,0,1,0);
transaction(0,2,0,5,0,0,14420,0,0);
transaction(0,2,0,5,0,0,14420,0,0);
transaction(0,2,0,5,1,0,0,1,0);
transaction(0,2,0,5,0,1,0,1,0);
transaction(1,2,0,5,0,0,0,1,0);
transaction(0,2,0,6,0,0,14488,0,0);
transaction(0,2,0,6,0,0,14488,0,0);
transaction(0,2,0,6,1,0,0,1,0);
transaction(0,2,0,6,0,1,0,1,0);
transaction(1,2,0,6,0,0,0,1,0);
transaction(0,3,0,0,0,0,13988,0,0);
transaction(0,3,0,0,0,7,14016,0,0);
transaction(0,3,0,0,1,0,0,1,0);
transaction(0,3,0,0,0,8,0,1,0);
transaction(1,3,0,0,0,0,0,1,0);
transaction(0,3,0,1,0,0,14088,0,0);
transaction(0,3,0,1,0,7,14116,0,0);
transaction(0,3,0,1,1,0,0,1,0);
transaction(0,3,0,1,0,8,0,1,0);
transaction(1,3,0,1,0,0,0,1,0);
transaction(0,3,0,2,0,0,14188,0,0);
transaction(0,3,0,2,0,7,14216,0,0);
transaction(0,3,0,2,1,0,0,1,0);
transaction(0,3,0,2,0,8,0,1,0);
transaction(1,3,0,2,0,0,0,1,0);
transaction(0,3,0,3,0,0,14288,0,0);
transaction(0,3,0,3,0,7,14316,0,0);
transaction(0,3,0,3,1,0,0,1,0);
transaction(0,3,0,3,0,8,0,1,0);
transaction(1,3,0,3,0,0,0,1,0);
transaction(0,3,0,4,0,0,14356,0,0);
transaction(0,3,0,4,0,7,14384,0,0);
transaction(0,3,0,4,1,0,0,1,0);
transaction(0,3,0,4,0,8,0,1,0);
transaction(1,3,0,4,0,0,0,1,0);
transaction(0,3,0,5,0,0,14424,0,0);
transaction(0,3,0,5,0,7,14452,0,0);
transaction(0,3,0,5,1,0,0,1,0);
transaction(0,3,0,5,0,8,0,1,0);
transaction(1,3,0,5,0,0,0,1,0);
transaction(0,3,0,6,0,0,14492,0,0);
transaction(0,3,0,6,0,7,14520,0,0);
transaction(0,3,0,6,1,0,0,1,0);
transaction(0,3,0,6,0,8,0,1,0);
transaction(1,3,0,6,0,0,0,1,0);
transaction(0,4,0,0,0,0,14020,0,0);
transaction(0,4,0,0,0,7,14048,0,0);
transaction(0,4,0,0,1,0,0,1,0);
transaction(0,4,0,0,0,8,0,1,0);
transaction(1,4,0,0,0,0,0,1,0);
transaction(0,4,0,1,0,0,14120,0,0);
transaction(0,4,0,1,0,7,14148,0,0);
transaction(0,4,0,1,1,0,0,1,0);
transaction(0,4,0,1,0,8,0,1,0);
transaction(1,4,0,1,0,0,0,1,0);
transaction(0,4,0,2,0,0,14220,0,0);
transaction(0,4,0,2,0,7,14248,0,0);
transaction(0,4,0,2,1,0,0,1,0);
transaction(0,4,0,2,0,8,0,1,0);
transaction(1,4,0,2,0,0,0,1,0);
transaction(0,5,0,0,0,0,14524,0,0);
transaction(0,5,0,0,0,7,14552,0,0);
transaction(0,5,0,0,1,0,0,1,0);
transaction(0,5,0,0,0,8,0,1,0);
transaction(1,5,0,0,0,0,0,1,0);
transaction(0,6,0,0,0,0,14556,0,0);
transaction(0,6,0,0,0,7,14584,0,0);
transaction(0,6,0,0,1,0,0,1,0);
transaction(0,6,0,0,0,8,0,1,0);
transaction(1,6,0,0,0,0,0,1,0);
transaction(0,7,0,0,0,0,14588,0,0);
transaction(0,7,0,0,0,7,14616,0,0);
transaction(0,7,0,0,1,0,0,1,0);
transaction(0,7,0,0,0,8,0,1,0);
transaction(1,7,0,0,0,0,0,1,0);
transaction(0,8,0,0,0,0,15004,0,0);
transaction(1,8,0,0,0,0,15004,0,0);
transaction(0,8,0,0,0,7,15032,0,0);
transaction(1,8,0,0,0,7,15032,0,0);
transaction(0,8,0,0,1,0,15036,0,0);
transaction(1,8,0,0,1,0,15036,0,0);
transaction(0,8,0,0,1,7,15064,0,0);
transaction(1,8,0,0,1,7,15064,0,0);
transaction(0,8,0,0,2,0,15068,0,0);
transaction(1,8,0,0,2,0,15068,0,0);
transaction(0,8,0,0,2,7,15096,0,0);
transaction(1,8,0,0,2,7,15096,0,0);
transaction(0,8,0,0,3,0,15100,0,0);
transaction(1,8,0,0,3,0,15100,0,0);
transaction(0,8,0,0,3,7,15128,0,0);
transaction(1,8,0,0,3,7,15128,0,0);
transaction(0,8,0,0,4,0,15132,0,0);
transaction(1,8,0,0,4,0,15132,0,0);
transaction(0,8,0,0,4,7,15160,0,0);
transaction(1,8,0,0,4,7,15160,0,0);
transaction(0,8,0,0,5,0,15164,0,0);
transaction(1,8,0,0,5,0,15164,0,0);
transaction(0,8,0,0,5,7,15192,0,0);
transaction(1,8,0,0,5,7,15192,0,0);
transaction(0,8,0,0,6,0,15196,0,0);
transaction(1,8,0,0,6,0,15196,0,0);
transaction(0,8,0,0,6,7,15224,0,0);
transaction(1,8,0,0,6,7,15224,0,0);
transaction(0,8,0,0,7,0,15228,0,0);
transaction(1,8,0,0,7,0,15228,0,0);
transaction(0,8,0,0,7,7,15256,0,0);
transaction(1,8,0,0,7,7,15256,0,0);
transaction(0,8,0,0,8,0,15260,0,0);
transaction(1,8,0,0,8,0,15260,0,0);
transaction(0,8,0,0,8,7,15288,0,0);
transaction(1,8,0,0,8,7,15288,0,0);
transaction(0,8,0,0,9,0,15292,0,0);
transaction(1,8,0,0,9,0,15292,0,0);
transaction(0,8,0,0,9,7,15320,0,0);
transaction(1,8,0,0,9,7,15320,0,0);
transaction(0,8,0,0,10,0,15324,0,0);
transaction(1,8,0,0,10,0,15324,0,0);
transaction(0,8,0,0,10,7,15352,0,0);
transaction(1,8,0,0,10,7,15352,0,0);
transaction(0,8,0,0,11,0,15356,0,0);
transaction(1,8,0,0,11,0,15356,0,0);
transaction(0,8,0,0,11,7,15384,0,0);
transaction(1,8,0,0,11,7,15384,0,0);
transaction(0,8,0,0,12,0,15388,0,0);
transaction(1,8,0,0,12,0,15388,0,0);
transaction(0,8,0,0,12,7,15416,0,0);
transaction(1,8,0,0,12,7,15416,0,0);
transaction(0,8,0,0,14,0,15452,0,0);
transaction(1,8,0,0,14,0,15452,0,0);
transaction(0,8,0,0,14,7,15480,0,0);
transaction(1,8,0,0,14,7,15480,0,0);
transaction(0,8,0,0,15,0,0,1,0);
transaction(0,8,0,0,0,8,0,1,0);
transaction(0,8,0,0,0,8,0,1,0);
transaction(0,8,0,0,1,8,0,1,0);
transaction(0,8,0,0,2,8,0,1,0);
transaction(0,8,0,0,3,8,0,1,0);
transaction(0,8,0,0,4,8,0,1,0);
transaction(0,8,0,0,5,8,0,1,0);
transaction(0,8,0,0,6,8,0,1,0);
transaction(0,8,0,0,7,8,0,1,0);
transaction(0,8,0,0,8,8,0,1,0);
transaction(0,8,0,0,9,8,0,1,0);
transaction(0,8,0,0,10,8,0,1,0);
transaction(0,8,0,0,11,8,0,1,0);
transaction(0,8,0,0,12,8,0,1,0);
transaction(0,8,0,0,14,8,0,1,0);
transaction(0,9,0,0,0,0,14748,0,0);
transaction(1,9,0,0,0,0,14748,0,0);
transaction(0,9,0,0,3,7,14872,0,0);
transaction(1,9,0,0,3,7,14872,0,0);
transaction(0,9,0,0,4,0,0,1,0);
transaction(0,9,0,0,0,8,0,1,0);
transaction(0,10,0,0,0,0,14876,0,0);
transaction(1,10,0,0,0,0,14876,0,0);
transaction(0,10,0,0,3,7,15000,0,0);
transaction(1,10,0,0,3,7,15000,0,0);
transaction(0,10,0,0,4,0,0,1,0);
transaction(0,10,0,0,0,8,0,1,0);
transaction(0,11,0,0,0,0,14620,0,0);
transaction(0,11,0,0,3,7,14744,0,0);
transaction(0,11,0,0,4,0,0,1,0);
transaction(0,11,0,0,0,8,0,1,0);
transaction(1,11,0,0,0,0,0,1,0);
transaction(0,8,0,0,13,0,0,1,0);
transaction(0,4,0,3,0,0,0,1,0);
transaction(0,9,1,0,0,0,0,1,0);
transaction(0,0,1,0,0,0,0,1,0);
transaction(0,5,0,1,0,0,0,1,0);
transaction(0,9,0,1,0,0,0,1,0);
transaction(0,15,0,0,0,0,0,1,0);
transaction(0,0,0,0,0,0,5728,1,1);
    if (comparisons!=237 || request_stalls==0)
      $fatal(1,"MAPPER_REQUIRED_COUNTS comparisons=%0d",comparisons);
    $display("MAPPER_DDR_REQUESTS %0d",all_requests);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin
    repeat (1000000) @(posedge clk); $fatal(1,"MAPPER_CYCLE_BOUND");
  end
endmodule
