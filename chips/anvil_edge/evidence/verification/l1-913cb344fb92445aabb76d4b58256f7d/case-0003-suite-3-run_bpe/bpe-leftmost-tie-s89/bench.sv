
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg start=0,in_valid=0,in_last=0,out_ready=0;
  reg [31:0] in_token_id=0;
  wire in_ready,out_valid,out_last,busy,done,error;
  wire [31:0] out_token_id;
  wire [7:0] error_code;
  wire tbl_req_valid,tbl_rsp_ready;
  wire [63:0] tbl_req_addr;
  reg tbl_req_ready=0,tbl_rsp_valid=0,tbl_rsp_error=0;
  reg [31:0] tbl_rsp_data=0;

  reg config_valid=1;
  reg [31:0] cfg_vocab_size=512,cfg_merge_count=3;
  reg [63:0] cfg_merge_base=64'h1000;
  anvil_edge_ranked_bpe #(.MAX_PRETOKEN_BYTES(8)) dut(.*);

  reg [63:0] addresses[0:255];
  reg [31:0] expected[0:255];
  reg [31:0] rng=89;
  reg outstanding=0,req_held=0,out_held=0;
  reg [63:0] pending_addr=0,held_addr=0;
  reg [32:0] held_out=0;
  integer requests=0,responses=0,outputs=0,completions=0,cycle=0,delay_count=0;
  integer request_stalls=0,output_stalls=0,comparisons=0;
  function automatic [31:0] memory(input [63:0] address);
    begin
      case (address)
        64'h1020: memory=32'h41;
64'h1024: memory=32'h42;
64'h1028: memory=32'h100;
64'h102c: memory=32'ha;
64'h1030: memory=32'h42;
64'h1034: memory=32'h43;
64'h1038: memory=32'h101;
64'h103c: memory=32'ha;
64'h1040: memory=32'h100;
64'h1044: memory=32'h43;
64'h1048: memory=32'h102;
64'h104c: memory=32'h0;
        default: $fatal(1,"BPE_UNMAPPED_READ address=%h",address);
      endcase
    end
  endfunction
  task automatic reset_check;
    begin
      if ({in_ready,out_valid,out_token_id,out_last,busy,done,error,error_code,
           tbl_req_valid,tbl_req_addr,tbl_rsp_ready}!==90'd0)
        $fatal(1,"BPE_RESET t=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) begin
    if (rst_n) begin
      rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
      tbl_req_ready=rng[0] && cycle%5!=0;
      out_ready=rng[1] && cycle%7!=0;
      if (outstanding && !tbl_rsp_valid) begin
        if (delay_count==0) begin
          tbl_rsp_valid<=1; tbl_rsp_data=memory(pending_addr);
          tbl_rsp_error=0;
        end else delay_count=delay_count-1;
      end
    end
  end
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n) begin
      if ((^{in_ready,out_valid,out_token_id,out_last,busy,done,error,error_code,
             tbl_req_valid,tbl_req_addr,tbl_rsp_ready})===1'bx)
        $fatal(1,"BPE_XZ");
      if (req_held && (!tbl_req_valid || tbl_req_addr!==held_addr))
        $fatal(1,"BPE_REQUEST_STABILITY");
      if (out_held && (!out_valid || {out_last,out_token_id}!==held_out))
        $fatal(1,"BPE_OUTPUT_STABILITY");
      req_held=tbl_req_valid && !tbl_req_ready;
      out_held=out_valid && !out_ready;
      held_addr=tbl_req_addr; held_out={out_last,out_token_id};
      if (req_held) request_stalls=request_stalls+1;
      if (out_held) output_stalls=output_stalls+1;
      if (tbl_rsp_valid && tbl_rsp_ready) begin
        if (!outstanding) $fatal(1,"BPE_ORPHAN_RESPONSE");
        outstanding=0; responses=responses+1; tbl_rsp_valid<=0;
      end
      if (tbl_req_valid && tbl_req_ready) begin

        if (outstanding || tbl_req_addr<64'h1020 ||
            tbl_req_addr>=64'h1050 || tbl_req_addr[1:0]!=0)
          $fatal(1,"BPE_LOOKUP_BOUNDS");
        pending_addr=tbl_req_addr; outstanding=1; delay_count=1+rng[4:2];
        requests=requests+1; comparisons=comparisons+1;
      end
      if (out_valid && out_ready) begin
        if (outputs>=1 || out_token_id!==expected[outputs] ||
            out_last!==(8'h00==0 && outputs==1-1))
          $fatal(1,"BPE_BYTES item=%0d expected=%h observed=%h last=%b",
                 outputs,expected[outputs],out_token_id,out_last);
        outputs=outputs+1; comparisons=comparisons+1;
      end
      if (done) begin
        if (error || outputs!=1 || outstanding || completions!=0)
          $fatal(1,"BPE_PREMATURE_DONE");
        completions=completions+1;
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic token(input integer id,input bit last);
    begin
      @(negedge clk); #1; in_valid=1; in_token_id=id; in_last=last;
      do begin @(posedge clk); end while (!in_ready);
      #1; @(negedge clk); #1; in_valid=0;
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    expected[0]=258;
    repeat (2) tick();
    @(negedge clk); #1; rst_n=1; start=1; tick();
    @(negedge clk); #1; start=0;
    token(65,0);
token(66,0);
token(67,1);
    if (8'h00!=0) begin
      while (!error) tick();
      repeat (10) begin
        tick();
        if (error!==1 || error_code!==8'h00 || done!==0)
          $fatal(1,"BPE_ERROR expected=%h observed=%h",8'h00,error_code);
      end
      if (outputs!=1 || completions!=0 || outstanding ||
          requests==0 || responses!=requests || out_valid || in_ready)
        $fatal(1,"BPE_ERROR_COUNTS");
    end else begin
      while (completions==0 && !error) tick();
      repeat (10) tick();
      if (error || completions!=1 || outputs!=1 || requests==0 ||
          responses!=requests || outstanding || busy)
        $fatal(1,"BPE_COUNTS requests=%0d responses=%0d outputs=%0d error=%h",
               requests,responses,outputs,error_code);
    end
    comparisons=comparisons+1;
    if (comparisons!=requests+1+1) $fatal(1,"BPE_COMPARISONS");
    $display("BPE_REQUESTS %0d",requests);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin
    repeat (100000) @(posedge clk); $fatal(1,"BPE_CYCLE_BOUND");
  end
endmodule
