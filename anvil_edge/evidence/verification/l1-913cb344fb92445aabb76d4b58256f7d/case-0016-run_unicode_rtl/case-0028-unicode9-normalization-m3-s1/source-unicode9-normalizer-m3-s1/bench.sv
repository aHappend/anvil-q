
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg start=0,in_valid=0,in_last=0,out_ready=0;
  reg [31:0] in_value=0;
  wire in_ready,out_valid,out_last,busy,done,error;
  wire [63:0] out_value;
  wire [7:0] error_code;
  wire tbl_req_valid,tbl_rsp_ready;
  wire [63:0] tbl_req_addr;
  reg tbl_req_ready=0,tbl_rsp_valid=0,tbl_rsp_error=0;
  reg [31:0] tbl_rsp_data=0;
  
  wire [31:0] normalized_scalar;
  assign out_value={32'd0,normalized_scalar};
  anvil_edge_normalizer #(.MAX_SCALARS(256)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.config_valid(1'b1),
    .cfg_normalization(32'd3),.cfg_ranges_base(64'h1000),
    .cfg_decomposition_base(64'h10000),.cfg_scalar_pool_base(64'h20000),
    .cfg_composition_base(64'h30000),.cfg_range_count(32'd2292),
    .cfg_class_count(32'd16),
    .cfg_decomposition_count(32'd2060),
    .cfg_scalar_pool_count(32'd3404),
    .cfg_composition_count(32'd940),
    .in_valid(in_valid),.in_ready(in_ready),.in_scalar(in_value),.in_last(in_last),
    .out_valid(out_valid),.out_ready(out_ready),.out_scalar(normalized_scalar),
    .out_last(out_last),.busy(busy),.done(done),.error(error),.error_code(error_code),
    .tbl_req_valid(tbl_req_valid),.tbl_req_ready(tbl_req_ready),.tbl_req_addr(tbl_req_addr),
    .tbl_rsp_valid(tbl_rsp_valid),.tbl_rsp_ready(tbl_rsp_ready),
    .tbl_rsp_data(tbl_rsp_data),.tbl_rsp_error(tbl_rsp_error));

  reg [63:0] expected[0:37];
  reg [31:0] rng=1;
  reg outstanding=0,req_held=0,out_held=0;
  reg [63:0] pending_addr=0,held_addr=0;
  reg [64:0] held_out=0;
  integer requests=0,responses=0,outputs=0,completions=0,cycle=0,delay_count=0;
  integer req_wait=0,out_wait=0,request_stalls=0,output_stalls=0,comparisons=0;
  integer inputs=0;
  reg [31:0] table_words[0:24571];
  initial $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0016-run_unicode_rtl/case-0028-unicode9-normalization-m3-s1/source-unicode9-normalizer-m3-s1-table.hex",table_words);
  function automatic [31:0] memory(input [63:0] address);
    begin
      if (address[1:0]!=0) $fatal(1,"TEXT_UNALIGNED_READ");
if (address>=64'h1020 && address<64'h9f60) memory=table_words[0+((address-64'h1020)>>2)];
else if (address>=64'h10020 && address<64'h180e0) memory=table_words[9168+((address-64'h10020)>>2)];
else if (address>=64'h20020 && address<64'h23550) memory=table_words[17408+((address-64'h20020)>>2)];
else if (address>=64'h30020 && address<64'h33ae0) memory=table_words[20812+((address-64'h30020)>>2)];
else $fatal(1,"TEXT_UNMAPPED_READ address=%h",address);
    end
  endfunction
  task automatic reset_check;
    begin
      if ({in_ready,out_valid,out_value,out_last,busy,done,error,error_code,
           tbl_req_valid,tbl_req_addr,tbl_rsp_ready} !== '0)
        $fatal(1,"TEXT_RESET t=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) begin
    if (rst_n) begin
      rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
      tbl_req_ready=req_wait>=2 && rng[0] && cycle%5!=0;
      out_ready=out_wait>=3 && rng[1] && cycle%7!=0;
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
      if ((^{in_ready,out_valid,out_value,out_last,busy,done,error,error_code,
             tbl_req_valid,tbl_req_addr,tbl_rsp_ready})===1'bx)
        $fatal(1,"TEXT_XZ");
      if (req_held && (!tbl_req_valid || tbl_req_addr!==held_addr))
        $fatal(1,"TEXT_REQUEST_STABILITY");
      if (out_held && (!out_valid || {out_last,out_value}!==held_out))
        $fatal(1,"TEXT_OUTPUT_STABILITY");
      req_held=tbl_req_valid && !tbl_req_ready;
      out_held=out_valid && !out_ready;
      held_addr=tbl_req_addr; held_out={out_last,out_value};
      if (req_held) request_stalls=request_stalls+1;
      if (out_held) output_stalls=output_stalls+1;
      if (tbl_req_valid) req_wait=req_wait+1;
      if (out_valid) out_wait=out_wait+1;
      if (in_valid && in_ready) inputs=inputs+1;
      if (tbl_rsp_valid && tbl_rsp_ready) begin
        if (!outstanding) $fatal(1,"TEXT_ORPHAN_RESPONSE");
        outstanding=0; responses=responses+1; tbl_rsp_valid<=0;
      end
      if (tbl_req_valid && tbl_req_ready) begin
        if (outstanding || tbl_req_addr[1:0]!=0)
          $fatal(1,"TEXT_REQUEST_CONSERVATION");
        pending_addr=tbl_req_addr; outstanding=1; delay_count=1+rng[4:2];
        requests=requests+1; comparisons=comparisons+1; req_wait=0;
      end
      if (out_valid && out_ready) begin
        if (outputs>=38 || out_value!==expected[outputs] ||
            out_last!==(outputs==38-1))
          $fatal(1,"TEXT_VECTOR item=%0d expected=%h observed=%h last=%b",
                 outputs,expected[outputs],out_value,out_last);
        outputs=outputs+1; comparisons=comparisons+1; out_wait=0;
      end
      if (done) begin
        if (error || outputs!=38 || outstanding || completions!=0)
          $fatal(1,"TEXT_PREMATURE_DONE");
        completions=completions+1;
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic item(input [31:0] value,input bit last);
    begin
      if (!error) begin
        @(negedge clk); #1; in_valid=1; in_value=value; in_last=last;
        do begin @(posedge clk); end while (!in_ready && !error);
        #1; @(negedge clk); #1; in_valid=0;
      end
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    expected[0]=64'h65;
expected[1]=64'h301;
expected[2]=64'h20;
expected[3]=64'h61;
expected[4]=64'h300;
expected[5]=64'h315;
expected[6]=64'h20;
expected[7]=64'h308;
expected[8]=64'h301;
expected[9]=64'h20;
expected[10]=64'h41;
expected[11]=64'h30a;
expected[12]=64'h301;
expected[13]=64'h20;
expected[14]=64'h1100;
expected[15]=64'h1161;
expected[16]=64'h11a8;
expected[17]=64'h20;
expected[18]=64'h1100;
expected[19]=64'h1161;
expected[20]=64'h11a8;
expected[21]=64'h20;
expected[22]=64'h1100;
expected[23]=64'h1161;
expected[24]=64'h11a7;
expected[25]=64'h20;
expected[26]=64'h11099;
expected[27]=64'h110ba;
expected[28]=64'h20;
expected[29]=64'h1d157;
expected[30]=64'h1d165;
expected[31]=64'h20;
expected[32]=64'h1f600;
expected[33]=64'h20;
expected[34]=64'h11935;
expected[35]=64'h11930;
expected[36]=64'h20;
expected[37]=64'h1e030;
    repeat (2) tick();
    @(negedge clk); #1; rst_n=1; start=1; tick();
    @(negedge clk); #1; start=0;
    item(32'h65,0);
item(32'h301,0);
item(32'h20,0);
item(32'h61,0);
item(32'h315,0);
item(32'h300,0);
item(32'h20,0);
item(32'h344,0);
item(32'h20,0);
item(32'h41,0);
item(32'h30a,0);
item(32'h301,0);
item(32'h20,0);
item(32'h1100,0);
item(32'h1161,0);
item(32'h11a8,0);
item(32'h20,0);
item(32'hac01,0);
item(32'h20,0);
item(32'h1100,0);
item(32'h1161,0);
item(32'h11a7,0);
item(32'h20,0);
item(32'h11099,0);
item(32'h110ba,0);
item(32'h20,0);
item(32'h1d15e,0);
item(32'h20,0);
item(32'h1f600,0);
item(32'h20,0);
item(32'h11935,0);
item(32'h11930,0);
item(32'h20,0);
item(32'h1e030,1);
    if (8'h00!=0) begin
      while (!error && completions==0) tick();
      repeat (10) begin
        tick();
        if (error!==1 || error_code!==8'h00 || done!==0 ||
            out_valid!==0 || in_ready!==0)
          $fatal(1,"TEXT_ERROR expected=%h observed=%h",8'h00,error_code);
      end
      if (outputs!=38 || completions!=0 || outstanding)
        $fatal(1,"TEXT_ERROR_COUNTS");
    end else begin
      while (completions==0 && !error) tick();
      repeat (10) tick();
      if (error || completions!=1 || outputs!=38 ||
          responses!=requests || outstanding || busy || inputs!=34)
        $fatal(1,"TEXT_COUNTS inputs=%0d requests=%0d responses=%0d outputs=%0d error=%h",
               inputs,requests,responses,outputs,error_code);
    end
    if ((requests>0 && request_stalls==0) || (38>0 && output_stalls==0))
      $fatal(1,"TEXT_REQUIRED_STALLS");
    comparisons=comparisons+1;
    if (comparisons!=requests+38+1) $fatal(1,"TEXT_COMPARISONS");
    $display("TEXT_COUNTS inputs=%0d requests=%0d responses=%0d outputs=%0d",
             inputs,requests,responses,outputs);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin
    repeat (2000000) @(posedge clk); $fatal(1,"TEXT_CYCLE_BOUND");
  end
endmodule
