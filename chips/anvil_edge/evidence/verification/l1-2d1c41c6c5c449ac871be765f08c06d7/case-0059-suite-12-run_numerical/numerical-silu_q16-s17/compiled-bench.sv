
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
    rst_n=0; #1ps; reset_check();
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
transaction(32'h5a0bcc1,32'h5a0bcc1);
transaction(32'h4e834960,32'h4e834960);
transaction(32'h75e2fc57,32'h75e2fc57);
transaction(32'hca24e39a,32'h0);
transaction(32'h2950666d,32'h2950666d);
transaction(32'h86e55426,32'h0);
transaction(32'h3f13c171,32'h3f13c171);
transaction(32'he6cea9fa,32'h0);
transaction(32'h8febddf8,32'h0);
transaction(32'h6014be00,32'h6014be00);
transaction(32'hb5c33744,32'h0);
transaction(32'ha3b09dd,32'ha3b09dd);
transaction(32'h2386a3a0,32'h2386a3a0);
transaction(32'hcf27b35c,32'h0);
transaction(32'h4fec9e2c,32'h4fec9e2c);
transaction(32'h6b837ba8,32'h6b837ba8);
transaction(32'hfff09219,32'h0);
transaction(32'hfffdd959,32'hffffc69a);
transaction(32'hfffbe900,32'hffffeec2);
transaction(32'hfff1a745,32'h0);
transaction(32'hfffb5939,32'hfffff4bd);
transaction(32'hfff19c05,32'h0);
transaction(32'hffff4587,32'hffffc34c);
transaction(32'hfffbfe99,32'hffffeda8);
transaction(32'hfff02a40,32'h0);
transaction(32'hfffcf982,32'hffffdc25);
transaction(32'hfff7a573,32'hffffff7f);
transaction(32'hfff3bf32,32'hfffffffc);
transaction(32'hfff6d7cd,32'hffffffc1);
transaction(32'hfff7f448,32'hffffff57);
transaction(32'hfffb82b9,32'hfffff33d);
transaction(32'hfff1dc0d,32'hffffffff);
    @(negedge clk); #1; x=-12345; in_valid=1; tick();
    @(negedge clk); #1; in_valid=0; rst_n=0;
    #1ps; reset_check(); repeat (2) tick();
    @(negedge clk); #1; rst_n=1;
    repeat (1000) begin tick(); if (out_valid!==0) $fatal(1,"NONLINEAR_RESET_STALE"); end
    if (comparisons!=45) $fatal(1,"NONLINEAR_COUNTS");
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin repeat (200000) @(posedge clk); $fatal(1,"NONLINEAR_CYCLE_BOUND"); end
endmodule
