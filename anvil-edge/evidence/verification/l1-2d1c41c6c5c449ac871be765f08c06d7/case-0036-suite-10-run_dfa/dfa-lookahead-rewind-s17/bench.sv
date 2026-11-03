
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
  
  wire [31:0] span_start,span_end;
  assign out_value={span_start,span_end};
  anvil_edge_tagged_dfa #(.MAX_SPAN_BYTES(64)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.config_valid(1'b1),
    .cfg_ranges_base(64'h1000),.cfg_states_base(64'h10000),
    .cfg_transitions_base(64'h20000),.cfg_tag_ops_base(64'h30000),
    .cfg_accepts_base(64'h40000),.cfg_range_count(32'd2),
    .cfg_class_count(32'd1),.cfg_state_count(32'd4),
    .cfg_transition_count(32'd8),
    .cfg_tag_op_count(32'd2),
    .cfg_accept_count(32'd1),
    .cfg_start_state(32'd0),.cfg_dead_state(32'd3),
    .cfg_tag_register_count(32'd32),.in_valid(in_valid),.in_ready(in_ready),
    .in_scalar(in_value),.in_last(in_last),.out_valid(out_valid),
    .out_ready(out_ready),.out_start(span_start),.out_end(span_end),.out_last(out_last),
    .busy(busy),.done(done),.error(error),.error_code(error_code),
    .tbl_req_valid(tbl_req_valid),.tbl_req_ready(tbl_req_ready),
    .tbl_req_addr(tbl_req_addr),.tbl_rsp_valid(tbl_rsp_valid),
    .tbl_rsp_ready(tbl_rsp_ready),.tbl_rsp_data(tbl_rsp_data),.tbl_rsp_error(tbl_rsp_error));

  reg [63:0] expected[0:4];
  reg [31:0] rng=17;
  reg outstanding=0,req_held=0,out_held=0;
  reg [63:0] pending_addr=0,held_addr=0;
  reg [64:0] held_out=0;
  integer requests=0,responses=0,outputs=0,completions=0,cycle=0,delay_count=0;
  integer req_wait=0,out_wait=0,request_stalls=0,output_stalls=0,comparisons=0;
  integer inputs=0;
  
  function automatic [31:0] memory(input [63:0] address);
    begin
      case (address)
64'h1020: memory=32'h00000000;
64'h1024: memory=32'h0000d7ff;
64'h1028: memory=32'h00000000;
64'h102c: memory=32'h00000000;
64'h1030: memory=32'h0000e000;
64'h1034: memory=32'h0010ffff;
64'h1038: memory=32'h00000000;
64'h103c: memory=32'h00000000;
64'h10020: memory=32'h00000000;
64'h10024: memory=32'h00000000;
64'h10028: memory=32'h00000000;
64'h1002c: memory=32'h00000000;
64'h10030: memory=32'h00000002;
64'h10034: memory=32'h00000000;
64'h10038: memory=32'h00000000;
64'h1003c: memory=32'h00000000;
64'h10040: memory=32'h00000004;
64'h10044: memory=32'h00000000;
64'h10048: memory=32'h00000001;
64'h1004c: memory=32'h00000000;
64'h10050: memory=32'h00000006;
64'h10054: memory=32'h00000001;
64'h10058: memory=32'h00000000;
64'h1005c: memory=32'h00000000;
64'h20020: memory=32'h00000001;
64'h20024: memory=32'h00000000;
64'h20028: memory=32'h00000000;
64'h2002c: memory=32'h00000000;
64'h20030: memory=32'h00000003;
64'h20034: memory=32'h00000000;
64'h20038: memory=32'h00000000;
64'h2003c: memory=32'h00000000;
64'h20040: memory=32'h00000002;
64'h20044: memory=32'h00000000;
64'h20048: memory=32'h00000002;
64'h2004c: memory=32'h00000000;
64'h20050: memory=32'h00000002;
64'h20054: memory=32'h00000000;
64'h20058: memory=32'h00000002;
64'h2005c: memory=32'h00000000;
64'h20060: memory=32'h00000003;
64'h20064: memory=32'h00000000;
64'h20068: memory=32'h00000000;
64'h2006c: memory=32'h00000000;
64'h20070: memory=32'h00000003;
64'h20074: memory=32'h00000000;
64'h20078: memory=32'h00000000;
64'h2007c: memory=32'h00000000;
64'h20080: memory=32'h00000003;
64'h20084: memory=32'h00000000;
64'h20088: memory=32'h00000000;
64'h2008c: memory=32'h00000000;
64'h20090: memory=32'h00000003;
64'h20094: memory=32'h00000000;
64'h20098: memory=32'h00000000;
64'h2009c: memory=32'h00000000;
64'h30020: memory=32'h00000001;
64'h30024: memory=32'h00000000;
64'h30028: memory=32'h00000000;
64'h3002c: memory=32'h00000000;
64'h30030: memory=32'h00000003;
64'h30034: memory=32'h00000001;
64'h30038: memory=32'h00000000;
64'h3003c: memory=32'h00000000;
64'h40020: memory=32'h00000000;
64'h40024: memory=32'h00000001;
64'h40028: memory=32'h00000000;
64'h4002c: memory=32'h00000000;
default: $fatal(1,"TEXT_UNMAPPED_READ address=%h",address);
endcase
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
        if (outputs>=5 || out_value!==expected[outputs] ||
            out_last!==(outputs==5-1))
          $fatal(1,"TEXT_VECTOR item=%0d expected=%h observed=%h last=%b",
                 outputs,expected[outputs],out_value,out_last);
        outputs=outputs+1; comparisons=comparisons+1; out_wait=0;
      end
      if (done) begin
        if (error || outputs!=5 || outstanding || completions!=0)
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
    expected[0]=64'h1;
expected[1]=64'h100000003;
expected[2]=64'h300000006;
expected[3]=64'h60000000a;
expected[4]=64'ha0000000b;
    repeat (2) tick();
    @(negedge clk); #1; rst_n=1; start=1; tick();
    @(negedge clk); #1; start=0;
    item(32'h61,0);
item(32'he9,0);
item(32'h4e2d,0);
item(32'h1f600,0);
item(32'h62,1);
    if (8'h00!=0) begin
      while (!error && completions==0) tick();
      repeat (10) begin
        tick();
        if (error!==1 || error_code!==8'h00 || done!==0 ||
            out_valid!==0 || in_ready!==0)
          $fatal(1,"TEXT_ERROR expected=%h observed=%h",8'h00,error_code);
      end
      if (outputs!=5 || completions!=0 || outstanding)
        $fatal(1,"TEXT_ERROR_COUNTS");
    end else begin
      while (completions==0 && !error) tick();
      repeat (10) tick();
      if (error || completions!=1 || outputs!=5 ||
          responses!=requests || outstanding || busy || inputs!=5)
        $fatal(1,"TEXT_COUNTS inputs=%0d requests=%0d responses=%0d outputs=%0d error=%h",
               inputs,requests,responses,outputs,error_code);
    end
    if ((requests>0 && request_stalls==0) || (5>0 && output_stalls==0))
      $fatal(1,"TEXT_REQUIRED_STALLS");
    comparisons=comparisons+1;
    if (comparisons!=requests+5+1) $fatal(1,"TEXT_COMPARISONS");
    $display("TEXT_COUNTS inputs=%0d requests=%0d responses=%0d outputs=%0d",
             inputs,requests,responses,outputs);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin
    repeat (2000000) @(posedge clk); $fatal(1,"TEXT_CYCLE_BOUND");
  end
endmodule
