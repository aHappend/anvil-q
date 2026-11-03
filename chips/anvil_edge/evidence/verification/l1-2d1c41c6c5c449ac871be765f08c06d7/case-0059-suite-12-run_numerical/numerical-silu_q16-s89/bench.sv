
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg in_valid=0,out_ready=0;
  reg signed [32-1:0] x=0;
  wire in_ready,out_valid,arithmetic_error;
  wire [31:0] value;
  anvil_edge_silu_q16 dut(.*);
  integer comparisons=0;
  task automatic reset_check;
    begin
      if ({in_ready,out_valid,arithmetic_error,value}!==0)
        $fatal(1,"NONLINEAR_RESET");
    end
  endtask
  always @(posedge clk or negedge clk) begin
    if (!rst_n) reset_check();
    if ((^{in_ready,out_valid,arithmetic_error,value})===1'bx)
      $fatal(1,"NONLINEAR_XZ");
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic transaction(input signed [32-1:0] operand,input [31:0] expected);
    begin
      @(negedge clk); #1; x=operand; in_valid=1;
      if (in_ready!==1 || out_valid!==0) $fatal(1,"NONLINEAR_IDLE");
      @(posedge clk);
      if (out_valid!==0) $fatal(1,"NONLINEAR_E0");
      #1; @(negedge clk); #1; in_valid=0;
      while (!out_valid) tick();
      repeat (7) begin
        if (out_valid!==1 || in_ready!==0 || value!==expected || arithmetic_error!==0)
          $fatal(1,"NONLINEAR_VALUE input=%h expected=%h observed=%h",operand,expected,value);
        tick();
      end
      @(negedge clk); #1; out_ready=1; tick();
      if (out_valid!==0) $fatal(1,"NONLINEAR_RETIRE");
      @(negedge clk); #1; out_ready=0;
      comparisons=comparisons+1;
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    repeat (2) tick(); @(negedge clk); #1; rst_n=1;
    transaction(32'h80000000,32'h0);
transaction(32'h7fffffff,32'h7fffffff);
transaction(32'h0,32'h0);
transaction(32'hffffffff,32'h0);
transaction(32'h1,32'h1);
transaction(32'hffff8000,32'hffffcfad);
transaction(32'h8000,32'h4fad);
transaction(32'hffff0000,32'hffffbb27);
transaction(32'h10000,32'hbb27);
transaction(32'hffefffff,32'h0);
transaction(32'hfff00000,32'h0);
transaction(32'hfff00001,32'h0);
transaction(32'h100000,32'h100000);
transaction(32'h7f6b17a4,32'h7f6b17a4);
transaction(32'ha3fd7e36,32'h0);
transaction(32'h5a2f6b1d,32'h5a2f6b1d);
transaction(32'hea806097,32'h0);
transaction(32'h655a1fb1,32'h655a1fb1);
transaction(32'h2e6c028a,32'h2e6c028a);
transaction(32'h5c45b198,32'h5c45b198);
transaction(32'h80f0ada6,32'h0);
transaction(32'h491f4452,32'h491f4452);
transaction(32'hef660ee,32'hef660ee);
transaction(32'h974a3140,32'h0);
transaction(32'he993a110,32'h0);
transaction(32'h952b6765,32'h0);
transaction(32'h564d0fb2,32'h564d0fb2);
transaction(32'h3cfee598,32'h3cfee598);
transaction(32'h7dc22942,32'h7dc22942);
transaction(32'hfff0306a,32'h0);
transaction(32'hfff0addf,32'h0);
transaction(32'hfff4a1d7,32'hfffffff7);
transaction(32'hfff730b3,32'hffffffaa);
transaction(32'hfff2f8ab,32'hfffffffe);
transaction(32'hfff4aaf6,32'hfffffff7);
transaction(32'hfffaf595,32'hfffff7b5);
transaction(32'hfff03395,32'h0);
transaction(32'hfffb2a43,32'hfffff63e);
transaction(32'hfff51e54,32'hfffffff3);
transaction(32'hfff9f6b3,32'hfffffc51);
transaction(32'hfff58c82,32'hffffffec);
transaction(32'hffff82b1,32'hffffd062);
transaction(32'hfffcbf35,32'hffffe102);
transaction(32'hffff1243,32'hffffbcac);
transaction(32'hfffaf5fb,32'hfffff7b2);
    @(negedge clk); #1; x=-12345; in_valid=1; tick();
    @(negedge clk); #1; in_valid=0; rst_n=0;
    #0; reset_check(); repeat (2) tick();
    @(negedge clk); #1; rst_n=1;
    repeat (1000) begin tick(); if (out_valid!==0) $fatal(1,"NONLINEAR_RESET_STALE"); end
    if (comparisons!=45) $fatal(1,"NONLINEAR_COUNTS");
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin repeat (200000) @(posedge clk); $fatal(1,"NONLINEAR_CYCLE_BOUND"); end
endmodule
