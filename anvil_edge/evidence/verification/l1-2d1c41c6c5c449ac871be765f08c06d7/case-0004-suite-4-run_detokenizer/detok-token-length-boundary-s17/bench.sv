
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg start=0,in_valid=0,in_last=0,out_ready=0;
  reg [31:0] in_token_id=0;
  wire in_ready,out_valid,out_last,busy,done,error;
  wire [7:0] out_data,error_code;
  wire tbl_req_valid,tbl_rsp_ready;
  wire [63:0] tbl_req_addr;
  reg tbl_req_ready=0,tbl_rsp_valid=0,tbl_rsp_error=0;
  reg [31:0] tbl_rsp_data=0;
  reg config_valid=1,finish_valid=0;
  wire finish_ready;
  reg [31:0] cfg_vocab_size=257,cfg_max_token_byte_length=64;
  reg [63:0] cfg_token_records_base=64'h1000,cfg_token_bytes_base=64'h4000;
  reg [63:0] cfg_token_bytes_count=67;
  anvil_edge_detokenizer dut(.*);
  reg [63:0] addresses[0:255];
  reg [7:0] expected[0:255];
  reg [31:0] rng=17;
  reg outstanding=0,req_held=0,out_held=0;
  reg [63:0] pending_addr=0,held_addr=0;
  reg [8:0] held_out=0;
  integer requests=0,responses=0,outputs=0,completions=0,cycle=0,delay_count=0;
  integer request_stalls=0,output_stalls=0,comparisons=0;
  function automatic [31:0] memory(input [63:0] address);
    begin
      case (address)
        64'h1020: memory=32'h00000003;
64'h1024: memory=32'h00000000;
64'h1028: memory=32'h00000040;
64'h102c: memory=32'h00000001;
64'h4020: memory=32'h4113557f;
64'h4024: memory=32'h41414141;
64'h4028: memory=32'h41414141;
64'h402c: memory=32'h41414141;
64'h4030: memory=32'h41414141;
64'h4034: memory=32'h41414141;
64'h4038: memory=32'h41414141;
64'h403c: memory=32'h41414141;
64'h4040: memory=32'h41414141;
64'h4044: memory=32'h41414141;
64'h4048: memory=32'h41414141;
64'h404c: memory=32'h41414141;
64'h4050: memory=32'h41414141;
64'h4054: memory=32'h41414141;
64'h4058: memory=32'h41414141;
64'h405c: memory=32'h41414141;
64'h4060: memory=32'h00414141;
        default: $fatal(1,"DETOK_UNMAPPED_READ address=%h",address);
      endcase
    end
  endfunction
  task automatic reset_check;
    begin
      if ({in_ready,out_valid,out_data,out_last,busy,done,error,error_code,
           tbl_req_valid,tbl_req_addr,tbl_rsp_ready,finish_ready}!==90'd0)
        $fatal(1,"DETOK_RESET t=%0t",$time);
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
      if ((^{in_ready,out_valid,out_data,out_last,busy,done,error,error_code,
             tbl_req_valid,tbl_req_addr,tbl_rsp_ready,finish_ready})===1'bx)
        $fatal(1,"DETOK_XZ");
      if (req_held && (!tbl_req_valid || tbl_req_addr!==held_addr))
        $fatal(1,"DETOK_REQUEST_STABILITY");
      if (out_held && (!out_valid || {out_last,out_data}!==held_out))
        $fatal(1,"DETOK_OUTPUT_STABILITY");
      req_held=tbl_req_valid && !tbl_req_ready;
      out_held=out_valid && !out_ready;
      held_addr=tbl_req_addr; held_out={out_last,out_data};
      if (req_held) request_stalls=request_stalls+1;
      if (out_held) output_stalls=output_stalls+1;
      if (tbl_rsp_valid && tbl_rsp_ready) begin
        if (!outstanding) $fatal(1,"DETOK_ORPHAN_RESPONSE");
        outstanding=0; responses=responses+1; tbl_rsp_valid<=0;
      end
      if (tbl_req_valid && tbl_req_ready) begin
        if (outstanding || requests>=68 || tbl_req_addr!==addresses[requests])
          $fatal(1,"DETOK_LOOKUP item=%0d expected=%h observed=%h",
                 requests,addresses[requests],tbl_req_addr);
        pending_addr=tbl_req_addr; outstanding=1; delay_count=1+rng[4:2];
        requests=requests+1; comparisons=comparisons+1;
      end
      if (out_valid && out_ready) begin
        if (outputs>=64 || out_data!==expected[outputs] ||
            out_last!==(8'h00==0 && outputs==64-1))
          $fatal(1,"DETOK_BYTES item=%0d expected=%h observed=%h last=%b",
                 outputs,expected[outputs],out_data,out_last);
        outputs=outputs+1; comparisons=comparisons+1;
      end
      if (done) begin
        if (error || outputs!=64 || outstanding || completions!=0)
          $fatal(1,"DETOK_PREMATURE_DONE");
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
    addresses[0]=64'h1020;
addresses[1]=64'h1024;
addresses[2]=64'h1028;
addresses[3]=64'h102c;
addresses[4]=64'h4020;
addresses[5]=64'h4024;
addresses[6]=64'h4024;
addresses[7]=64'h4024;
addresses[8]=64'h4024;
addresses[9]=64'h4028;
addresses[10]=64'h4028;
addresses[11]=64'h4028;
addresses[12]=64'h4028;
addresses[13]=64'h402c;
addresses[14]=64'h402c;
addresses[15]=64'h402c;
addresses[16]=64'h402c;
addresses[17]=64'h4030;
addresses[18]=64'h4030;
addresses[19]=64'h4030;
addresses[20]=64'h4030;
addresses[21]=64'h4034;
addresses[22]=64'h4034;
addresses[23]=64'h4034;
addresses[24]=64'h4034;
addresses[25]=64'h4038;
addresses[26]=64'h4038;
addresses[27]=64'h4038;
addresses[28]=64'h4038;
addresses[29]=64'h403c;
addresses[30]=64'h403c;
addresses[31]=64'h403c;
addresses[32]=64'h403c;
addresses[33]=64'h4040;
addresses[34]=64'h4040;
addresses[35]=64'h4040;
addresses[36]=64'h4040;
addresses[37]=64'h4044;
addresses[38]=64'h4044;
addresses[39]=64'h4044;
addresses[40]=64'h4044;
addresses[41]=64'h4048;
addresses[42]=64'h4048;
addresses[43]=64'h4048;
addresses[44]=64'h4048;
addresses[45]=64'h404c;
addresses[46]=64'h404c;
addresses[47]=64'h404c;
addresses[48]=64'h404c;
addresses[49]=64'h4050;
addresses[50]=64'h4050;
addresses[51]=64'h4050;
addresses[52]=64'h4050;
addresses[53]=64'h4054;
addresses[54]=64'h4054;
addresses[55]=64'h4054;
addresses[56]=64'h4054;
addresses[57]=64'h4058;
addresses[58]=64'h4058;
addresses[59]=64'h4058;
addresses[60]=64'h4058;
addresses[61]=64'h405c;
addresses[62]=64'h405c;
addresses[63]=64'h405c;
addresses[64]=64'h405c;
addresses[65]=64'h4060;
addresses[66]=64'h4060;
addresses[67]=64'h4060;
expected[0]=8'h41;
expected[1]=8'h41;
expected[2]=8'h41;
expected[3]=8'h41;
expected[4]=8'h41;
expected[5]=8'h41;
expected[6]=8'h41;
expected[7]=8'h41;
expected[8]=8'h41;
expected[9]=8'h41;
expected[10]=8'h41;
expected[11]=8'h41;
expected[12]=8'h41;
expected[13]=8'h41;
expected[14]=8'h41;
expected[15]=8'h41;
expected[16]=8'h41;
expected[17]=8'h41;
expected[18]=8'h41;
expected[19]=8'h41;
expected[20]=8'h41;
expected[21]=8'h41;
expected[22]=8'h41;
expected[23]=8'h41;
expected[24]=8'h41;
expected[25]=8'h41;
expected[26]=8'h41;
expected[27]=8'h41;
expected[28]=8'h41;
expected[29]=8'h41;
expected[30]=8'h41;
expected[31]=8'h41;
expected[32]=8'h41;
expected[33]=8'h41;
expected[34]=8'h41;
expected[35]=8'h41;
expected[36]=8'h41;
expected[37]=8'h41;
expected[38]=8'h41;
expected[39]=8'h41;
expected[40]=8'h41;
expected[41]=8'h41;
expected[42]=8'h41;
expected[43]=8'h41;
expected[44]=8'h41;
expected[45]=8'h41;
expected[46]=8'h41;
expected[47]=8'h41;
expected[48]=8'h41;
expected[49]=8'h41;
expected[50]=8'h41;
expected[51]=8'h41;
expected[52]=8'h41;
expected[53]=8'h41;
expected[54]=8'h41;
expected[55]=8'h41;
expected[56]=8'h41;
expected[57]=8'h41;
expected[58]=8'h41;
expected[59]=8'h41;
expected[60]=8'h41;
expected[61]=8'h41;
expected[62]=8'h41;
expected[63]=8'h41;
    repeat (2) tick();
    @(negedge clk); #1; rst_n=1; start=1; tick();
    @(negedge clk); #1; start=0;
    token(0,1);
    if (8'h00!=0) begin
      while (!error) tick();
      repeat (10) begin
        tick();
        if (error!==1 || error_code!==8'h00 || done!==0)
          $fatal(1,"DETOK_ERROR expected=%h observed=%h",8'h00,error_code);
      end
      if (outputs!=64 || completions!=0 || outstanding ||
          requests!=68 || responses!=requests || out_valid || in_ready)
        $fatal(1,"DETOK_ERROR_COUNTS");
    end else begin
      while (completions==0 && !error) tick();
      repeat (10) tick();
      if (error || completions!=1 || outputs!=64 || requests!=68 ||
          responses!=requests || outstanding || busy)
        $fatal(1,"DETOK_COUNTS requests=%0d responses=%0d outputs=%0d error=%h",
               requests,responses,outputs,error_code);
    end
    comparisons=comparisons+1;
    if (comparisons!=requests+64+1) $fatal(1,"DETOK_COMPARISONS");
    $display("DETOK_REQUESTS %0d",requests);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin
    repeat (100000) @(posedge clk); $fatal(1,"DETOK_CYCLE_BOUND");
  end
endmodule
