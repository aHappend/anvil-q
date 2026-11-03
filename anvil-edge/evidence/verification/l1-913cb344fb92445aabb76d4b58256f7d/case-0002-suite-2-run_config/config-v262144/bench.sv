
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg cfg_valid=0,cfg_write=0,cfg_rsp_ready=0;
  reg [31:0] cfg_addr=0,cfg_wdata=0;
  wire cfg_ready,cfg_rsp_valid,cfg_rsp_error;
  wire [31:0] cfg_rdata;
  reg [3:0] status=1;
  reg [7:0] transaction_error_code=0;
  reg write_allowed=1,reload_allowed=1,publish=0;
  reg [223:0] committed_config_words=0;
  wire reload_request,publish_error,serial_update;
  wire [31:0] uart_divisor,eos_token_id,max_new_tokens,transport,profile_id,vocab_size,uart_frame_bytes;
  anvil_edge_config #(.VOCAB_SIZE(262144),.MAX_SEQ_LEN(16)) dut(.*);
  integer comparisons=0,reloads=0,serial_updates=0,requests=0,responses=0;
  task automatic reset_check;
    begin
      if ({cfg_ready,cfg_rsp_valid,cfg_rsp_error,cfg_rdata,reload_request,
           publish_error,serial_update,uart_divisor,eos_token_id,max_new_tokens,
           transport,profile_id,vocab_size,uart_frame_bytes}!==262'd0)
        $fatal(1,"CONFIG_RESET");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(posedge clk) if (rst_n) begin
    if ((^{cfg_ready,cfg_rsp_valid,cfg_rsp_error,cfg_rdata,reload_request,
           publish_error,serial_update,uart_divisor,eos_token_id,max_new_tokens,
           transport,profile_id,vocab_size,uart_frame_bytes})===1'bx)
      $fatal(1,"CONFIG_XZ");
    if (cfg_valid && cfg_ready) requests=requests+1;
    if (cfg_rsp_valid && cfg_rsp_ready) responses=responses+1;
    if (reload_request) reloads=reloads+1;
    if (serial_update) serial_updates=serial_updates+1;
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic transact(input bit wr,input [31:0] address,input [31:0] data,
                          input bit expected_error,input [31:0] expected_data);
    begin
      @(negedge clk); #1; cfg_valid=1; cfg_write=wr; cfg_addr=address; cfg_wdata=data;
      do begin @(posedge clk); end while (!cfg_ready);
      #1; @(negedge clk); #1; cfg_valid=0;
      while (!cfg_rsp_valid) tick();
      repeat (5) begin
        if (cfg_rsp_valid!==1 || cfg_rsp_error!==expected_error ||
            cfg_rdata!==expected_data || cfg_ready!==0)
          $fatal(1,"CONFIG_RESPONSE address=%h error=%b data=%h expected=%h",
                 address,cfg_rsp_error,cfg_rdata,expected_data);
        tick();
      end
      @(negedge clk); #1; cfg_rsp_ready=1; tick();
      @(negedge clk); #1; cfg_rsp_ready=0;
      if (cfg_rsp_valid!==0) $fatal(1,"CONFIG_DUPLICATE_RESPONSE");
      comparisons=comparisons+1;
    end
  endtask
  task automatic publication(input integer vocabulary,input integer profile,
                             input bit expected_error);
    begin
      @(negedge clk); #1;
      committed_config_words={32'd0,32'(vocabulary),32'(profile),32'd1,32'd8,32'd255,32'd5};
      publish=1; tick();
      @(negedge clk); #1; publish=0;
      if (publish_error!==expected_error) $fatal(1,"CONFIG_PUBLICATION");
      comparisons=comparisons+1;
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check(); repeat (2) tick();
    @(negedge clk); #1; rst_n=1;
    publication(256,1,0);
    transact(0,24,0,0,256);
    transact(1,24,1,1,0);
transact(0,24,0,0,256);
if (vocab_size!==256) $fatal(1,"CONFIG_ILLEGAL_ACTIVE_MUTATION");
comparisons=comparisons+1;
transact(1,24,255,1,0);
transact(0,24,0,0,256);
if (vocab_size!==256) $fatal(1,"CONFIG_ILLEGAL_ACTIVE_MUTATION");
comparisons=comparisons+1;
transact(1,24,0,1,0);
transact(0,24,0,0,256);
if (vocab_size!==256) $fatal(1,"CONFIG_ILLEGAL_ACTIVE_MUTATION");
comparisons=comparisons+1;
transact(1,24,262145,1,0);
transact(0,24,0,0,256);
if (vocab_size!==256) $fatal(1,"CONFIG_ILLEGAL_ACTIVE_MUTATION");
comparisons=comparisons+1;
transact(1,24,262145,1,0);
transact(0,24,0,0,256);
if (vocab_size!==256) $fatal(1,"CONFIG_ILLEGAL_ACTIVE_MUTATION");
comparisons=comparisons+1;
transact(1,24,257,0,0);
transact(0,24,0,0,257);
if (vocab_size!==256) $fatal(1,"CONFIG_ILLEGAL_ACTIVE_MUTATION");
comparisons=comparisons+1;
transact(1,24,151936,0,0);
transact(0,24,0,0,151936);
if (vocab_size!==256) $fatal(1,"CONFIG_ILLEGAL_ACTIVE_MUTATION");
comparisons=comparisons+1;
transact(1,24,128256,0,0);
transact(0,24,0,0,128256);
if (vocab_size!==256) $fatal(1,"CONFIG_ILLEGAL_ACTIVE_MUTATION");
comparisons=comparisons+1;
transact(1,24,262144,0,0);
transact(0,24,0,0,262144);
if (vocab_size!==256) $fatal(1,"CONFIG_ILLEGAL_ACTIVE_MUTATION");
comparisons=comparisons+1;
    transact(1,24,257,0,0);
    transact(0,24,0,0,257);
    if (vocab_size!==256) $fatal(1,"CONFIG_EARLY_REINTERPRETATION");
    comparisons=comparisons+1;
    publication(257,1,0);
    if (vocab_size!==257) $fatal(1,"CONFIG_COMMIT");
    comparisons=comparisons+1;
    write_allowed=0;
    transact(1,24,256,1,0); transact(0,24,0,0,257);
    write_allowed=1;
    transact(1,0,1,1,0); transact(1,32,1,1,0);
    transact(1,25,256,1,0); transact(0,40,0,1,0);
    transact(1,4,3,1,0); transact(0,4,0,0,5);
    transact(1,8,257,1,0); transact(0,8,0,0,255);
    transact(1,12,17,1,0); transact(0,12,0,0,8);
    transact(1,16,2,1,0); transact(0,16,0,0,1);
    transact(1,20,0,1,0); transact(0,20,0,0,1);
    transact(1,28,3,1,0);
    reload_allowed=0; transact(1,28,1,1,0);
    reload_allowed=1; transact(1,28,1,0,0);
    if (reloads!=1 || serial_updates!=0) $fatal(1,"CONFIG_COMMAND_SIDE_EFFECTS");
    comparisons=comparisons+1;
    transact(1,24,256,0,0);
    publication(257,1,1);
    if (vocab_size!==257) $fatal(1,"CONFIG_FAILED_PUBLICATION_MUTATION");
    comparisons=comparisons+1;
    transact(0,24,0,0,256);
    publication(256,1,0);
    if (vocab_size!==256 || publish_error) $fatal(1,"CONFIG_RECOVERY");
    comparisons=comparisons+1;
    if (requests!=responses || requests==0) $fatal(1,"CONFIG_COUNTS");
    if (comparisons!=60) $fatal(1,"CONFIG_COMPARISONS %0d",comparisons);
    $display("COMPARED %0d",comparisons); $finish;
  end
endmodule
