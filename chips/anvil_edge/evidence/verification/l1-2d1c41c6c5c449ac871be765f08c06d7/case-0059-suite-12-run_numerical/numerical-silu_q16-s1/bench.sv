
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
transaction(32'h4386bbc4,32'h4386bbc4);
transaction(32'hc14c343c,32'h0);
transaction(32'hf311d8a3,32'h0);
transaction(32'h26cecc1b,32'h26cecc1b);
transaction(32'h49e9c616,32'h49e9c616);
transaction(32'h98072e8c,32'h0);
transaction(32'h55f4b3b2,32'h55f4b3b2);
transaction(32'hf204e52d,32'h0);
transaction(32'h71fd42a2,32'h71fd42a2);
transaction(32'h66c3f339,32'h66c3f339);
transaction(32'h87d4bedc,32'h0);
transaction(32'ha9a021e,32'ha9a021e);
transaction(32'hbbab6c39,32'h0);
transaction(32'h85805975,32'h0);
transaction(32'h246d6753,32'h246d6753);
transaction(32'h5c2574bd,32'h5c2574bd);
transaction(32'hfff3de54,32'hfffffffc);
transaction(32'hfffaa570,32'hfffff98c);
transaction(32'hfffd81e6,32'hffffcf43);
transaction(32'hfff6133f,32'hffffffe0);
transaction(32'hfff9b531,32'hfffffd06);
transaction(32'hfff917d5,32'hfffffe3b);
transaction(32'hfffffac6,32'hfffffd6a);
transaction(32'hfffc965a,32'hffffe421);
transaction(32'hfff11ad5,32'h0);
transaction(32'hffff5e04,32'hffffc7cf);
transaction(32'hfff7c486,32'hffffff71);
transaction(32'hfffcefed,32'hffffdcfa);
transaction(32'hfffd420f,32'hffffd581);
transaction(32'hfff58946,32'hffffffec);
transaction(32'hfffbbf7a,32'hfffff0b9);
transaction(32'hfffbfd91,32'hffffedb6);
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
