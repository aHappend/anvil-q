
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg config_valid=1;
  reg [63:0] cfg_directory_base=4160,cfg_immutable_base=7072;
  reg [63:0] cfg_writable_base=28304;
  reg [31:0] cfg_directory_count=60;
  reg [63:0] cfg_immutable_bytes=21232,cfg_writable_bytes=1952;
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
    .NUM_LAYERS(2),.HIDDEN_SIZE(16),.INTERMEDIATE_SIZE(24),
    .NUM_Q_HEADS(2),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),
    .VOCAB_SIZE(257),.MAX_SEQ_LEN(4),.DDR_BYTES(65536)
  ) dut(.*);
  reg [31:0] directory[0:727];
  reg [31:0] rng=89;
  reg outstanding=0,held=0,expected_error=0,expected_write=0,inject_error=0;
  reg [63:0] held_addr=0,pending_address=0,expected_address=0;
  reg [36:0] held_fields=0;
  reg pending_data=0;
  integer cycle=0,delay_count=0,data_requests=0,all_requests=0,comparisons=0;
  integer request_stalls=0;
  function automatic [31:0] value_at(input [63:0] address);
    begin
      if (address>=cfg_directory_base && address<cfg_directory_base+2912)
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
                       ddr_req_addr<cfg_directory_base+2912);
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
    $readmemh("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0007-suite-7-run_mapper/mapper-h16-l2-s89-input/directory.hex",directory);
    repeat (2) tick(); @(negedge clk); #1; rst_n=1;
    transaction(0,0,0,0,0,0,7072,0,0);
transaction(0,0,0,0,256,15,23516,0,0);
transaction(0,0,0,0,257,0,0,1,0);
transaction(0,0,0,0,0,16,0,1,0);
transaction(1,0,0,0,0,0,0,1,0);
transaction(0,1,0,0,0,0,23520,0,0);
transaction(0,1,0,0,15,1,23644,0,0);
transaction(0,1,0,0,16,0,0,1,0);
transaction(0,1,0,0,0,2,0,1,0);
transaction(1,1,0,0,0,0,0,1,0);
transaction(0,1,0,1,0,0,23856,0,0);
transaction(0,1,0,1,15,0,23916,0,0);
transaction(0,1,0,1,16,0,0,1,0);
transaction(0,1,0,1,0,1,0,1,0);
transaction(1,1,0,1,0,0,0,1,0);
transaction(0,1,0,2,0,0,24024,0,0);
transaction(0,1,0,2,15,0,24084,0,0);
transaction(0,1,0,2,16,0,0,1,0);
transaction(0,1,0,2,0,1,0,1,0);
transaction(1,1,0,2,0,0,0,1,0);
transaction(0,1,0,3,0,0,24192,0,0);
transaction(0,1,0,3,15,1,24316,0,0);
transaction(0,1,0,3,16,0,0,1,0);
transaction(0,1,0,3,0,2,0,1,0);
transaction(1,1,0,3,0,0,0,1,0);
transaction(0,1,0,4,0,0,24464,0,0);
transaction(0,1,0,4,15,2,24652,0,0);
transaction(0,1,0,4,16,0,0,1,0);
transaction(0,1,0,4,0,3,0,1,0);
transaction(1,1,0,4,0,0,0,1,0);
transaction(0,1,0,5,0,0,24872,0,0);
transaction(0,1,0,5,15,2,25060,0,0);
transaction(0,1,0,5,16,0,0,1,0);
transaction(0,1,0,5,0,3,0,1,0);
transaction(1,1,0,5,0,0,0,1,0);
transaction(0,1,0,6,0,0,25280,0,0);
transaction(0,1,0,6,23,1,25468,0,0);
transaction(0,1,0,6,24,0,0,1,0);
transaction(0,1,0,6,0,2,0,1,0);
transaction(1,1,0,6,0,0,0,1,0);
transaction(0,1,1,0,0,0,25816,0,0);
transaction(0,1,1,0,15,1,25940,0,0);
transaction(0,1,1,0,16,0,0,1,0);
transaction(0,1,1,0,0,2,0,1,0);
transaction(1,1,1,0,0,0,0,1,0);
transaction(0,1,1,1,0,0,26152,0,0);
transaction(0,1,1,1,15,0,26212,0,0);
transaction(0,1,1,1,16,0,0,1,0);
transaction(0,1,1,1,0,1,0,1,0);
transaction(1,1,1,1,0,0,0,1,0);
transaction(0,1,1,2,0,0,26320,0,0);
transaction(0,1,1,2,15,0,26380,0,0);
transaction(0,1,1,2,16,0,0,1,0);
transaction(0,1,1,2,0,1,0,1,0);
transaction(1,1,1,2,0,0,0,1,0);
transaction(0,1,1,3,0,0,26488,0,0);
transaction(0,1,1,3,15,1,26612,0,0);
transaction(0,1,1,3,16,0,0,1,0);
transaction(0,1,1,3,0,2,0,1,0);
transaction(1,1,1,3,0,0,0,1,0);
transaction(0,1,1,4,0,0,26760,0,0);
transaction(0,1,1,4,15,2,26948,0,0);
transaction(0,1,1,4,16,0,0,1,0);
transaction(0,1,1,4,0,3,0,1,0);
transaction(1,1,1,4,0,0,0,1,0);
transaction(0,1,1,5,0,0,27168,0,0);
transaction(0,1,1,5,15,2,27356,0,0);
transaction(0,1,1,5,16,0,0,1,0);
transaction(0,1,1,5,0,3,0,1,0);
transaction(1,1,1,5,0,0,0,1,0);
transaction(0,1,1,6,0,0,27576,0,0);
transaction(0,1,1,6,23,1,27764,0,0);
transaction(0,1,1,6,24,0,0,1,0);
transaction(0,1,1,6,0,2,0,1,0);
transaction(1,1,1,6,0,0,0,1,0);
transaction(0,2,0,0,0,0,23648,0,0);
transaction(0,2,0,0,1,1,23660,0,0);
transaction(0,2,0,0,2,0,0,1,0);
transaction(0,2,0,0,0,2,0,1,0);
transaction(1,2,0,0,0,0,0,1,0);
transaction(0,2,0,1,0,0,23920,0,0);
transaction(0,2,0,1,1,0,23924,0,0);
transaction(0,2,0,1,2,0,0,1,0);
transaction(0,2,0,1,0,1,0,1,0);
transaction(1,2,0,1,0,0,0,1,0);
transaction(0,2,0,2,0,0,24088,0,0);
transaction(0,2,0,2,1,0,24092,0,0);
transaction(0,2,0,2,2,0,0,1,0);
transaction(0,2,0,2,0,1,0,1,0);
transaction(1,2,0,2,0,0,0,1,0);
transaction(0,2,0,3,0,0,24320,0,0);
transaction(0,2,0,3,1,1,24332,0,0);
transaction(0,2,0,3,2,0,0,1,0);
transaction(0,2,0,3,0,2,0,1,0);
transaction(1,2,0,3,0,0,0,1,0);
transaction(0,2,0,4,0,0,24656,0,0);
transaction(0,2,0,4,1,2,24676,0,0);
transaction(0,2,0,4,2,0,0,1,0);
transaction(0,2,0,4,0,3,0,1,0);
transaction(1,2,0,4,0,0,0,1,0);
transaction(0,2,0,5,0,0,25064,0,0);
transaction(0,2,0,5,1,2,25084,0,0);
transaction(0,2,0,5,2,0,0,1,0);
transaction(0,2,0,5,0,3,0,1,0);
transaction(1,2,0,5,0,0,0,1,0);
transaction(0,2,0,6,0,0,25472,0,0);
transaction(0,2,0,6,2,1,25492,0,0);
transaction(0,2,0,6,3,0,0,1,0);
transaction(0,2,0,6,0,2,0,1,0);
transaction(1,2,0,6,0,0,0,1,0);
transaction(0,2,1,0,0,0,25944,0,0);
transaction(0,2,1,0,1,1,25956,0,0);
transaction(0,2,1,0,2,0,0,1,0);
transaction(0,2,1,0,0,2,0,1,0);
transaction(1,2,1,0,0,0,0,1,0);
transaction(0,2,1,1,0,0,26216,0,0);
transaction(0,2,1,1,1,0,26220,0,0);
transaction(0,2,1,1,2,0,0,1,0);
transaction(0,2,1,1,0,1,0,1,0);
transaction(1,2,1,1,0,0,0,1,0);
transaction(0,2,1,2,0,0,26384,0,0);
transaction(0,2,1,2,1,0,26388,0,0);
transaction(0,2,1,2,2,0,0,1,0);
transaction(0,2,1,2,0,1,0,1,0);
transaction(1,2,1,2,0,0,0,1,0);
transaction(0,2,1,3,0,0,26616,0,0);
transaction(0,2,1,3,1,1,26628,0,0);
transaction(0,2,1,3,2,0,0,1,0);
transaction(0,2,1,3,0,2,0,1,0);
transaction(1,2,1,3,0,0,0,1,0);
transaction(0,2,1,4,0,0,26952,0,0);
transaction(0,2,1,4,1,2,26972,0,0);
transaction(0,2,1,4,2,0,0,1,0);
transaction(0,2,1,4,0,3,0,1,0);
transaction(1,2,1,4,0,0,0,1,0);
transaction(0,2,1,5,0,0,27360,0,0);
transaction(0,2,1,5,1,2,27380,0,0);
transaction(0,2,1,5,2,0,0,1,0);
transaction(0,2,1,5,0,3,0,1,0);
transaction(1,2,1,5,0,0,0,1,0);
transaction(0,2,1,6,0,0,27768,0,0);
transaction(0,2,1,6,2,1,27788,0,0);
transaction(0,2,1,6,3,0,0,1,0);
transaction(0,2,1,6,0,2,0,1,0);
transaction(1,2,1,6,0,0,0,1,0);
transaction(0,3,0,0,0,0,23664,0,0);
transaction(0,3,0,0,1,15,23788,0,0);
transaction(0,3,0,0,2,0,0,1,0);
transaction(0,3,0,0,0,16,0,1,0);
transaction(1,3,0,0,0,0,0,1,0);
transaction(0,3,0,1,0,0,23928,0,0);
transaction(0,3,0,1,1,7,23988,0,0);
transaction(0,3,0,1,2,0,0,1,0);
transaction(0,3,0,1,0,8,0,1,0);
transaction(1,3,0,1,0,0,0,1,0);
transaction(0,3,0,2,0,0,24096,0,0);
transaction(0,3,0,2,1,7,24156,0,0);
transaction(0,3,0,2,2,0,0,1,0);
transaction(0,3,0,2,0,8,0,1,0);
transaction(1,3,0,2,0,0,0,1,0);
transaction(0,3,0,3,0,0,24336,0,0);
transaction(0,3,0,3,1,15,24460,0,0);
transaction(0,3,0,3,2,0,0,1,0);
transaction(0,3,0,3,0,16,0,1,0);
transaction(1,3,0,3,0,0,0,1,0);
transaction(0,3,0,4,0,0,24680,0,0);
transaction(0,3,0,4,1,23,24868,0,0);
transaction(0,3,0,4,2,0,0,1,0);
transaction(0,3,0,4,0,24,0,1,0);
transaction(1,3,0,4,0,0,0,1,0);
transaction(0,3,0,5,0,0,25088,0,0);
transaction(0,3,0,5,1,23,25276,0,0);
transaction(0,3,0,5,2,0,0,1,0);
transaction(0,3,0,5,0,24,0,1,0);
transaction(1,3,0,5,0,0,0,1,0);
transaction(0,3,0,6,0,0,25496,0,0);
transaction(0,3,0,6,2,15,25684,0,0);
transaction(0,3,0,6,3,0,0,1,0);
transaction(0,3,0,6,0,16,0,1,0);
transaction(1,3,0,6,0,0,0,1,0);
transaction(0,3,1,0,0,0,25960,0,0);
transaction(0,3,1,0,1,15,26084,0,0);
transaction(0,3,1,0,2,0,0,1,0);
transaction(0,3,1,0,0,16,0,1,0);
transaction(1,3,1,0,0,0,0,1,0);
transaction(0,3,1,1,0,0,26224,0,0);
transaction(0,3,1,1,1,7,26284,0,0);
transaction(0,3,1,1,2,0,0,1,0);
transaction(0,3,1,1,0,8,0,1,0);
transaction(1,3,1,1,0,0,0,1,0);
transaction(0,3,1,2,0,0,26392,0,0);
transaction(0,3,1,2,1,7,26452,0,0);
transaction(0,3,1,2,2,0,0,1,0);
transaction(0,3,1,2,0,8,0,1,0);
transaction(1,3,1,2,0,0,0,1,0);
transaction(0,3,1,3,0,0,26632,0,0);
transaction(0,3,1,3,1,15,26756,0,0);
transaction(0,3,1,3,2,0,0,1,0);
transaction(0,3,1,3,0,16,0,1,0);
transaction(1,3,1,3,0,0,0,1,0);
transaction(0,3,1,4,0,0,26976,0,0);
transaction(0,3,1,4,1,23,27164,0,0);
transaction(0,3,1,4,2,0,0,1,0);
transaction(0,3,1,4,0,24,0,1,0);
transaction(1,3,1,4,0,0,0,1,0);
transaction(0,3,1,5,0,0,27384,0,0);
transaction(0,3,1,5,1,23,27572,0,0);
transaction(0,3,1,5,2,0,0,1,0);
transaction(0,3,1,5,0,24,0,1,0);
transaction(1,3,1,5,0,0,0,1,0);
transaction(0,3,1,6,0,0,27792,0,0);
transaction(0,3,1,6,2,15,27980,0,0);
transaction(0,3,1,6,3,0,0,1,0);
transaction(0,3,1,6,0,16,0,1,0);
transaction(1,3,1,6,0,0,0,1,0);
transaction(0,4,0,0,0,0,23792,0,0);
transaction(0,4,0,0,0,15,23852,0,0);
transaction(0,4,0,0,1,0,0,1,0);
transaction(0,4,0,0,0,16,0,1,0);
transaction(1,4,0,0,0,0,0,1,0);
transaction(0,4,0,1,0,0,23992,0,0);
transaction(0,4,0,1,0,7,24020,0,0);
transaction(0,4,0,1,1,0,0,1,0);
transaction(0,4,0,1,0,8,0,1,0);
transaction(1,4,0,1,0,0,0,1,0);
transaction(0,4,0,2,0,0,24160,0,0);
transaction(0,4,0,2,0,7,24188,0,0);
transaction(0,4,0,2,1,0,0,1,0);
transaction(0,4,0,2,0,8,0,1,0);
transaction(1,4,0,2,0,0,0,1,0);
transaction(0,4,1,0,0,0,26088,0,0);
transaction(0,4,1,0,0,15,26148,0,0);
transaction(0,4,1,0,1,0,0,1,0);
transaction(0,4,1,0,0,16,0,1,0);
transaction(1,4,1,0,0,0,0,1,0);
transaction(0,4,1,1,0,0,26288,0,0);
transaction(0,4,1,1,0,7,26316,0,0);
transaction(0,4,1,1,1,0,0,1,0);
transaction(0,4,1,1,0,8,0,1,0);
transaction(1,4,1,1,0,0,0,1,0);
transaction(0,4,1,2,0,0,26456,0,0);
transaction(0,4,1,2,0,7,26484,0,0);
transaction(0,4,1,2,1,0,0,1,0);
transaction(0,4,1,2,0,8,0,1,0);
transaction(1,4,1,2,0,0,0,1,0);
transaction(0,5,0,0,0,0,25688,0,0);
transaction(0,5,0,0,0,15,25748,0,0);
transaction(0,5,0,0,1,0,0,1,0);
transaction(0,5,0,0,0,16,0,1,0);
transaction(1,5,0,0,0,0,0,1,0);
transaction(0,5,1,0,0,0,27984,0,0);
transaction(0,5,1,0,0,15,28044,0,0);
transaction(0,5,1,0,1,0,0,1,0);
transaction(0,5,1,0,0,16,0,1,0);
transaction(1,5,1,0,0,0,0,1,0);
transaction(0,6,0,0,0,0,25752,0,0);
transaction(0,6,0,0,0,15,25812,0,0);
transaction(0,6,0,0,1,0,0,1,0);
transaction(0,6,0,0,0,16,0,1,0);
transaction(1,6,0,0,0,0,0,1,0);
transaction(0,6,1,0,0,0,28048,0,0);
transaction(0,6,1,0,0,15,28108,0,0);
transaction(0,6,1,0,1,0,0,1,0);
transaction(0,6,1,0,0,16,0,1,0);
transaction(1,6,1,0,0,0,0,1,0);
transaction(0,7,0,0,0,0,28112,0,0);
transaction(0,7,0,0,0,15,28172,0,0);
transaction(0,7,0,0,1,0,0,1,0);
transaction(0,7,0,0,0,16,0,1,0);
transaction(1,7,0,0,0,0,0,1,0);
transaction(0,8,0,0,0,0,28816,0,0);
transaction(1,8,0,0,0,0,28816,0,0);
transaction(0,8,0,0,0,15,28876,0,0);
transaction(1,8,0,0,0,15,28876,0,0);
transaction(0,8,0,0,1,0,28912,0,0);
transaction(1,8,0,0,1,0,28912,0,0);
transaction(0,8,0,0,1,15,28972,0,0);
transaction(1,8,0,0,1,15,28972,0,0);
transaction(0,8,0,0,2,0,29008,0,0);
transaction(1,8,0,0,2,0,29008,0,0);
transaction(0,8,0,0,2,15,29068,0,0);
transaction(1,8,0,0,2,15,29068,0,0);
transaction(0,8,0,0,3,0,29104,0,0);
transaction(1,8,0,0,3,0,29104,0,0);
transaction(0,8,0,0,3,7,29132,0,0);
transaction(1,8,0,0,3,7,29132,0,0);
transaction(0,8,0,0,4,0,29200,0,0);
transaction(1,8,0,0,4,0,29200,0,0);
transaction(0,8,0,0,4,7,29228,0,0);
transaction(1,8,0,0,4,7,29228,0,0);
transaction(0,8,0,0,5,0,29296,0,0);
transaction(1,8,0,0,5,0,29296,0,0);
transaction(0,8,0,0,5,15,29356,0,0);
transaction(1,8,0,0,5,15,29356,0,0);
transaction(0,8,0,0,6,0,29392,0,0);
transaction(1,8,0,0,6,0,29392,0,0);
transaction(0,8,0,0,6,15,29452,0,0);
transaction(1,8,0,0,6,15,29452,0,0);
transaction(0,8,0,0,7,0,29488,0,0);
transaction(1,8,0,0,7,0,29488,0,0);
transaction(0,8,0,0,7,15,29548,0,0);
transaction(1,8,0,0,7,15,29548,0,0);
transaction(0,8,0,0,8,0,29584,0,0);
transaction(1,8,0,0,8,0,29584,0,0);
transaction(0,8,0,0,8,15,29644,0,0);
transaction(1,8,0,0,8,15,29644,0,0);
transaction(0,8,0,0,9,0,29680,0,0);
transaction(1,8,0,0,9,0,29680,0,0);
transaction(0,8,0,0,9,23,29772,0,0);
transaction(1,8,0,0,9,23,29772,0,0);
transaction(0,8,0,0,10,0,29776,0,0);
transaction(1,8,0,0,10,0,29776,0,0);
transaction(0,8,0,0,10,23,29868,0,0);
transaction(1,8,0,0,10,23,29868,0,0);
transaction(0,8,0,0,11,0,29872,0,0);
transaction(1,8,0,0,11,0,29872,0,0);
transaction(0,8,0,0,11,23,29964,0,0);
transaction(1,8,0,0,11,23,29964,0,0);
transaction(0,8,0,0,12,0,29968,0,0);
transaction(1,8,0,0,12,0,29968,0,0);
transaction(0,8,0,0,12,15,30028,0,0);
transaction(1,8,0,0,12,15,30028,0,0);
transaction(0,8,0,0,14,0,30160,0,0);
transaction(1,8,0,0,14,0,30160,0,0);
transaction(0,8,0,0,14,15,30220,0,0);
transaction(1,8,0,0,14,15,30220,0,0);
transaction(0,8,0,0,15,0,0,1,0);
transaction(0,8,0,0,0,24,0,1,0);
transaction(0,8,0,0,0,16,0,1,0);
transaction(0,8,0,0,1,16,0,1,0);
transaction(0,8,0,0,2,16,0,1,0);
transaction(0,8,0,0,3,8,0,1,0);
transaction(0,8,0,0,4,8,0,1,0);
transaction(0,8,0,0,5,16,0,1,0);
transaction(0,8,0,0,6,16,0,1,0);
transaction(0,8,0,0,7,16,0,1,0);
transaction(0,8,0,0,8,16,0,1,0);
transaction(0,8,0,0,9,24,0,1,0);
transaction(0,8,0,0,10,24,0,1,0);
transaction(0,8,0,0,11,24,0,1,0);
transaction(0,8,0,0,12,16,0,1,0);
transaction(0,8,0,0,14,16,0,1,0);
transaction(0,9,0,0,0,0,28304,0,0);
transaction(1,9,0,0,0,0,28304,0,0);
transaction(0,9,0,0,3,7,28428,0,0);
transaction(1,9,0,0,3,7,28428,0,0);
transaction(0,9,0,0,4,0,0,1,0);
transaction(0,9,0,0,0,8,0,1,0);
transaction(0,9,1,0,0,0,28560,0,0);
transaction(1,9,1,0,0,0,28560,0,0);
transaction(0,9,1,0,3,7,28684,0,0);
transaction(1,9,1,0,3,7,28684,0,0);
transaction(0,9,1,0,4,0,0,1,0);
transaction(0,9,1,0,0,8,0,1,0);
transaction(0,10,0,0,0,0,28432,0,0);
transaction(1,10,0,0,0,0,28432,0,0);
transaction(0,10,0,0,3,7,28556,0,0);
transaction(1,10,0,0,3,7,28556,0,0);
transaction(0,10,0,0,4,0,0,1,0);
transaction(0,10,0,0,0,8,0,1,0);
transaction(0,10,1,0,0,0,28688,0,0);
transaction(1,10,1,0,0,0,28688,0,0);
transaction(0,10,1,0,3,7,28812,0,0);
transaction(1,10,1,0,3,7,28812,0,0);
transaction(0,10,1,0,4,0,0,1,0);
transaction(0,10,1,0,0,8,0,1,0);
transaction(0,11,0,0,0,0,28176,0,0);
transaction(0,11,0,0,3,7,28300,0,0);
transaction(0,11,0,0,4,0,0,1,0);
transaction(0,11,0,0,0,8,0,1,0);
transaction(1,11,0,0,0,0,0,1,0);
transaction(0,8,0,0,13,0,0,1,0);
transaction(0,4,0,3,0,0,0,1,0);
transaction(0,9,2,0,0,0,0,1,0);
transaction(0,0,1,0,0,0,0,1,0);
transaction(0,5,0,1,0,0,0,1,0);
transaction(0,9,0,1,0,0,0,1,0);
transaction(0,15,0,0,0,0,0,1,0);
transaction(0,0,0,0,0,0,7072,1,1);
    if (comparisons!=379 || request_stalls==0)
      $fatal(1,"MAPPER_REQUIRED_COUNTS comparisons=%0d",comparisons);
    $display("MAPPER_DDR_REQUESTS %0d",all_requests);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin
    repeat (1000000) @(posedge clk); $fatal(1,"MAPPER_CYCLE_BOUND");
  end
endmodule
