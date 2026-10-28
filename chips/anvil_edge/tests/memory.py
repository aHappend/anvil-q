"""Independent concurrent-owner scoreboard for the real memory subsystem."""

from storage import KINDS, packed, synthetic_image


MEMORY = r"""
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg config_valid=0,boot_enable=1,abort_inference=0;
  reg [63:0] cfg_directory_base=@DIRECTORY@;
  reg [31:0] cfg_directory_count=32;
  reg [63:0] cfg_immutable_base=@IMMUTABLE@,cfg_immutable_bytes=@IMMUTABLE_BYTES@;
  reg [63:0] cfg_writable_base=@WRITABLE@,cfg_writable_bytes=@WRITABLE_BYTES@;
  reg [1023:0] cfg_table_bases=1024'h@TABLE_BASES@,cfg_table_bytes=1024'h@TABLE_BYTES@;
  reg core_mem_req_valid=0,core_mem_req_write=0,core_mem_rsp_ready=0;
  reg [3:0] core_mem_req_kind=0;
  reg [31:0] core_mem_req_layer=0,core_mem_req_row=7,core_mem_req_col=0,core_mem_req_wdata=0;
  reg [2:0] core_mem_req_proj=0;
  wire core_mem_req_ready,core_mem_rsp_valid,core_mem_rsp_error;
  wire [31:0] core_mem_rsp_rdata;
  reg tokenizer_tbl_req_valid=0,tokenizer_tbl_rsp_ready=0;
  reg [63:0] tokenizer_tbl_req_addr=0;
  wire tokenizer_tbl_req_ready,tokenizer_tbl_rsp_valid,tokenizer_tbl_rsp_error;
  wire [31:0] tokenizer_tbl_rsp_data;
  reg detokenizer_tbl_req_valid=0,detokenizer_tbl_rsp_ready=0;
  reg [63:0] detokenizer_tbl_req_addr=0;
  wire detokenizer_tbl_req_ready,detokenizer_tbl_rsp_valid,detokenizer_tbl_rsp_error;
  wire [31:0] detokenizer_tbl_rsp_data;
  reg boot_req_valid=0,boot_req_write=1,boot_rsp_ready=0;
  reg [63:0] boot_req_addr=64'h800;
  reg [31:0] boot_req_wdata=32'hf005a5a5;
  reg [3:0] boot_req_wstrb=15;
  wire boot_req_ready,boot_rsp_valid,boot_rsp_error;
  wire [31:0] boot_rsp_rdata;
  wire ddr_req_valid,ddr_req_write,ddr_rsp_ready,idle;
  wire [63:0] ddr_req_addr;
  wire [31:0] ddr_req_wdata;
  wire [3:0] ddr_req_wstrb;
  reg ddr_req_ready=0,ddr_rsp_valid=0,ddr_rsp_error=0;
  reg [31:0] ddr_rsp_rdata=0;
  anvil_edge_memory_subsystem #(
    .NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),.NUM_Q_HEADS(1),
    .NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),.VOCAB_SIZE(257),
    .MAX_SEQ_LEN(4),.DDR_BYTES(65536)
  ) dut(.*);
  reg [31:0] memory[0:16383];
  wire [3:0] request_valid={boot_req_valid,detokenizer_tbl_req_valid,
                           tokenizer_tbl_req_valid,core_mem_req_valid};
  wire [3:0] request_ready={boot_req_ready,detokenizer_tbl_req_ready,
                           tokenizer_tbl_req_ready,core_mem_req_ready};
  wire [3:0] response_valid={boot_rsp_valid,detokenizer_tbl_rsp_valid,
                            tokenizer_tbl_rsp_valid,core_mem_rsp_valid};
  wire [3:0] response_ready={boot_rsp_ready,detokenizer_tbl_rsp_ready,
                            tokenizer_tbl_rsp_ready,core_mem_rsp_ready};
  wire [3:0] response_error={boot_rsp_error,detokenizer_tbl_rsp_error,
                            tokenizer_tbl_rsp_error,core_mem_rsp_error};
  wire [127:0] response_data={boot_rsp_rdata,detokenizer_tbl_rsp_data,
                             tokenizer_tbl_rsp_data,core_mem_rsp_rdata};
  integer accepted[0:3],completed[0:3],stalls[0:3];
  reg active[0:3],held[0:3],expected_error[0:3];
  reg [31:0] expected_data[0:3];
  reg [32:0] held_response[0:3];
  integer cycles=0,requests=0,responses=0,comparisons=0,delay_count=0,wait_count=0;
  integer simultaneous=0,ddr_stalls=0,i;
  reg pending=0,ddr_held=0;
  reg [100:0] held_ddr;
  reg [63:0] pending_addr;
  reg [31:0] rng=@SEED@;
  task automatic reset_check;
    begin
      if ({request_ready,response_valid,response_error,response_data,
           ddr_req_valid,ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,
           ddr_rsp_ready,idle}!==0) $fatal(1,"MEMORY_RESET");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n) begin
    rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
    if (!ddr_req_valid) wait_count=0;
    else if (wait_count<2) wait_count=wait_count+1;
    ddr_req_ready=wait_count>=2 && rng[0] && cycles%5!=0;
    if (pending && !ddr_rsp_valid) begin
      if (delay_count==0) begin ddr_rsp_valid<=1; ddr_rsp_rdata=memory[pending_addr>>2]; end
      else delay_count=delay_count-1;
    end
  end
  always @(posedge clk) begin
    cycles=cycles+1;
    if (rst_n) begin
      if ((^{request_ready,response_valid,response_error,response_data,
             ddr_req_valid,ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,
             ddr_rsp_ready,idle})===1'bx) $fatal(1,"MEMORY_XZ");
      if (!config_valid && (request_ready[2:0]!=0 || response_valid[2:0]!=0))
        $fatal(1,"MEMORY_PRECOMMIT_CLIENT");
      if (config_valid && (boot_req_ready || boot_rsp_valid))
        $fatal(1,"MEMORY_BOOT_AFTER_COMMIT");
      if (request_valid[2:0]==7) simultaneous=simultaneous+1;
      for (integer client=0;client<4;client=client+1) begin
        if (held[client] && (!response_valid[client] ||
            {response_error[client],response_data[client*32+:32]}!==held_response[client]))
          $fatal(1,"MEMORY_OWNER_STABILITY client=%0d",client);
        held[client]=response_valid[client] && !response_ready[client];
        held_response[client]={response_error[client],response_data[client*32+:32]};
        if (held[client]) stalls[client]=stalls[client]+1;
        if (request_valid[client] && request_ready[client]) begin
          if (active[client]) $fatal(1,"MEMORY_DUPLICATE_CAPTURE client=%0d",client);
          active[client]=1; accepted[client]=accepted[client]+1;
        end
        if (response_valid[client]) begin
          if (!active[client] || response_error[client]!==expected_error[client] ||
              (!expected_error[client] &&
               response_data[client*32+:32]!==expected_data[client]))
            $fatal(1,"MEMORY_WRONG_OWNER client=%0d expected=%h observed=%h error=%b",
                   client,expected_data[client],response_data[client*32+:32],response_error[client]);
          if (response_ready[client]) begin
            active[client]=0; completed[client]=completed[client]+1;
            comparisons=comparisons+1;
          end
        end
      end
      if (ddr_held && (!ddr_req_valid ||
          {ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb}!==held_ddr))
        $fatal(1,"MEMORY_DDR_STABILITY");
      ddr_held=ddr_req_valid && !ddr_req_ready;
      held_ddr={ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb};
      if (ddr_held) ddr_stalls=ddr_stalls+1;
      if (ddr_rsp_valid && ddr_rsp_ready) begin
        if (!pending) $fatal(1,"MEMORY_ORPHAN_DDR_RESPONSE");
        pending=0; ddr_rsp_valid<=0; responses=responses+1;
      end
      if (ddr_req_valid && ddr_req_ready) begin
        if (pending || ddr_req_addr[1:0]!=0 || ddr_req_addr>=65536)
          $fatal(1,"MEMORY_DDR_OUTSTANDING_BOUNDS");
        if (!config_valid) begin
          if (!ddr_req_write || ddr_req_addr!==64'h800 ||
              ddr_req_wdata!==32'hf005a5a5 || ddr_req_wstrb!==15)
            $fatal(1,"MEMORY_BOOT_TUPLE");
          memory[ddr_req_addr>>2]=ddr_req_wdata;
        end else begin
          if (ddr_req_write || ddr_req_wstrb!==0 ||
              !(ddr_req_addr==@TOKEN_ADDRESS@ || ddr_req_addr==@BYTE_ADDRESS@ ||
                ddr_req_addr==@CORE_ADDRESS@ ||
                (ddr_req_addr>=@DIRECTORY@ && ddr_req_addr<@DIRECTORY@+1568)))
            $fatal(1,"MEMORY_FORBIDDEN_DDR address=%h",ddr_req_addr);
        end
        pending=1; pending_addr=ddr_req_addr; delay_count=1+rng[4:2];
        requests=requests+1;
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic transact(input integer client,input bit bad);
    integer previous;
    begin
      @(negedge clk); #1;
      previous=completed[client]; expected_error[client]=bad;
      case (client)
        0: begin core_mem_req_valid=1; expected_data[0]=memory[@CORE_ADDRESS@>>2]; end
        1: begin
          tokenizer_tbl_req_addr=bad ? 64'h804 : @TOKEN_ADDRESS@;
          tokenizer_tbl_req_valid=1; expected_data[1]=memory[@TOKEN_ADDRESS@>>2];
        end
        2: begin
          detokenizer_tbl_req_addr=bad ? 64'h808 : @BYTE_ADDRESS@;
          detokenizer_tbl_req_valid=1; expected_data[2]=memory[@BYTE_ADDRESS@>>2];
        end
        3: begin boot_req_valid=1; expected_data[3]=32'hf005a5a5; end
      endcase
      do begin @(posedge clk); end while (!request_ready[client]);
      #1; @(negedge clk); #1;
      case (client)
        0: core_mem_req_valid=0;
        1: tokenizer_tbl_req_valid=0;
        2: detokenizer_tbl_req_valid=0;
        3: boot_req_valid=0;
      endcase
      while (!response_valid[client]) tick();
      repeat (5) tick();
      @(negedge clk); #1;
      case (client)
        0: core_mem_rsp_ready=1;
        1: tokenizer_tbl_rsp_ready=1;
        2: detokenizer_tbl_rsp_ready=1;
        3: boot_rsp_ready=1;
      endcase
      tick();
      if (completed[client]!=previous+1) $fatal(1,"MEMORY_CLIENT_RETIREMENT");
      @(negedge clk); #1;
      case (client)
        0: core_mem_rsp_ready=0;
        1: tokenizer_tbl_rsp_ready=0;
        2: detokenizer_tbl_rsp_ready=0;
        3: boot_rsp_ready=0;
      endcase
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    for (i=0;i<16384;i=i+1) memory[i]=0;
    for (i=0;i<4;i=i+1) begin
      accepted[i]=0; completed[i]=0; active[i]=0; held[i]=0; stalls[i]=0;
      expected_error[i]=0; expected_data[i]=0; held_response[i]=0;
    end
    @VECTORS@
    repeat (2) tick(); @(negedge clk); #1; rst_n=1;
    transact(3,0);
    while (!idle) tick();
    @(negedge clk); #1; config_valid=1; boot_enable=0; boot_req_valid=1;
    fork
      begin repeat (4) transact(0,0); end
      begin transact(1,0); transact(1,1); transact(1,0); transact(1,0); end
      begin transact(2,0); transact(2,1); transact(2,0); transact(2,0); end
    join
    repeat (20) tick();
    if (!idle || pending || requests!=responses || ddr_stalls==0 ||
        simultaneous==0 || comparisons!=13) $fatal(1,"MEMORY_FINAL_COUNTS");
    for (i=0;i<4;i=i+1)
      if (active[i] || accepted[i]!=completed[i] ||
          completed[i]!=(i==3 ? 1 : 4) || stalls[i]==0)
        $fatal(1,"MEMORY_OWNER_COUNTS client=%0d accepted=%0d completed=%0d",
               i,accepted[i],completed[i]);
    $display("MEMORY_TRANSACTIONS requests=%0d responses=%0d",requests,responses);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin repeat (200000) @(posedge clk); $fatal(1,"MEMORY_CYCLE_BOUND"); end
endmodule
"""


def run_memory(evidence):
    evidence.tools(("iverilog", "vvp"))
    fixture = synthetic_image(257)
    destinations, segments = fixture["destinations"], fixture["segments"]
    values = {
        "DIRECTORY": destinations[0x101], "IMMUTABLE": destinations[0x102],
        "IMMUTABLE_BYTES": len(segments[0x102]), "WRITABLE": destinations[0x103],
        "WRITABLE_BYTES": len(segments[0x103]),
        "TABLE_BASES": packed([destinations[kind] for kind in KINDS[4:]], 64),
        "TABLE_BYTES": packed([len(segments[kind]) for kind in KINDS[4:]], 64),
        "TOKEN_ADDRESS": destinations[0x201] + 32 + 8,
        "BYTE_ADDRESS": destinations[0x202] + 32 + 256,
        "CORE_ADDRESS": destinations[0x102] + 4 * 7 * 8,
        "VECTORS": "\n".join(f"memory[{address>>2}]=32'h{word:x};"
                              for address, word, _ in fixture["writes"]),
    }
    for seed in (1, 17, 89):
        bench = MEMORY
        for key, value in {**values, "SEED": seed}.items():
            bench = bench.replace(f"@{key}@", str(value))
        evidence.simulate(f"memory-concurrent-s{seed}", bench, [
            "rtl/anvil_edge_parameters.sv", "rtl/anvil_edge_signed_multiplier.sv",
            "rtl/anvil_edge_tensor_mapper.sv", "rtl/anvil_edge_memory_subsystem.sv",
        ], 13)
