
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg in_valid=0,out_ready=0;
  reg signed [64-1:0] x=0;
  wire in_ready,out_valid,arithmetic_error;
  wire [31:0] value;
  anvil_edge_exp_q24 dut(.*);
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
  task automatic transaction(input signed [64-1:0] operand,input [31:0] expected);
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
    transaction(64'h8000000000000000,32'h0);
transaction(64'h7fffffffffffffff,32'h1000000);
transaction(64'h0,32'h1000000);
transaction(64'hffffffffffffffff,32'hffff00);
transaction(64'h1,32'h1000000);
transaction(64'hffffffffffff8000,32'h9b45b0);
transaction(64'h8000,32'h1000000);
transaction(64'hffffffffffff0000,32'h5e2d59);
transaction(64'h10000,32'h1000000);
transaction(64'hffffffffffefffff,32'h0);
transaction(64'hfffffffffff00000,32'h1);
transaction(64'hfffffffffff00001,32'h1);
transaction(64'h100000,32'h1000000);
transaction(64'h7f6b17a4b406dd29,32'h1000000);
transaction(64'hd596030cae6c028a,32'h0);
transaction(64'h5c45b19892059577,32'h1000000);
transaction(64'h1e8ac0a477ba2604,32'h1000000);
transaction(64'hef660ee0dad1c34,32'h1000000);
transaction(64'h3a58c212f9692fb2,32'h1000000);
transaction(64'he993a11012027fc9,32'h0);
transaction(64'h3cfee5984712a2a1,32'h1000000);
transaction(64'ha32e1667fdc22942,32'h0);
transaction(64'h1d2f28250ebab6,32'h1000000);
transaction(64'h97c55c80b3d4fc24,32'h0);
transaction(64'h568a1c9cad44b70f,32'h1000000);
transaction(64'h2a279511c074ffd0,32'h1000000);
transaction(64'h5faacccecdac455,32'h1000000);
transaction(64'h7c2437caaa365d88,32'h1000000);
transaction(64'hefbabdc65b65e724,32'h0);
transaction(64'hfffffffffff5470f,32'h171);
transaction(64'hfffffffffff9b234,32'h77e0);
transaction(64'hfffffffffff7bf38,32'h1111);
transaction(64'hfffffffffffbc275,32'h3afd6);
transaction(64'hfffffffffff17605,32'h8);
transaction(64'hfffffffffffe6fde,32'h35a1f7);
transaction(64'hfffffffffff447bf,32'h88);
transaction(64'hfffffffffff9e9c7,32'h94f0);
transaction(64'hfffffffffff9a841,32'h734e);
transaction(64'hfffffffffff95fa0,32'h56d3);
transaction(64'hfffffffffff23b20,32'h11);
transaction(64'hfffffffffffdb389,32'h19b32b);
transaction(64'hfffffffffff60399,32'h304);
transaction(64'hfffffffffffde3ea,32'h1f0bc0);
transaction(64'hfffffffffffe060d,32'h23798a);
transaction(64'hfffffffffff18365,32'h8);
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
