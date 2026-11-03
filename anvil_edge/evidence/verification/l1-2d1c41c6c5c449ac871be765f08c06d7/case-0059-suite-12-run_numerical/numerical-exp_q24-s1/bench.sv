
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
transaction(64'h4386bbc4cd613e30,32'h1000000);
transaction(64'h9e2feb89414c343c,32'h0);
transaction(64'hf311d8a3c2ce6f44,32'h0);
transaction(64'h98072e8c35bf992d,32'h0);
transaction(64'h44647159c324c985,32'h1000000);
transaction(64'hf204e52db2221a58,32'h0);
transaction(64'h4d447e35b8b6d8fe,32'h1000000);
transaction(64'h71fd42a29755d4c1,32'h1000000);
transaction(64'hd1431193e6c3f339,32'h0);
transaction(64'h78130c4237730edf,32'h1000000);
transaction(64'h4381e88f38c0c8fd,32'h1000000);
transaction(64'hd87fd2803bab6c39,32'h0);
transaction(64'h73c64af775a89294,32'h1000000);
transaction(64'h85805975ed2f89d9,32'h0);
transaction(64'h246d6753ec148cb4,32'h1000000);
transaction(64'h5c2574bdb94067ed,32'h1000000);
transaction(64'hfffffffffff3de54,32'h5a);
transaction(64'hfffffffffffaa570,32'h13602);
transaction(64'hfffffffffffd81e6,32'h152b91);
transaction(64'hfffffffffff6133f,32'h335);
transaction(64'hfffffffffff9b531,32'h7948);
transaction(64'hfffffffffff917d5,32'h4197);
transaction(64'hfffffffffffffac6,32'hfad391);
transaction(64'hfffffffffffc965a,32'h86f9b);
transaction(64'hfffffffffff11ad5,32'h5);
transaction(64'hffffffffffff5e04,32'h87f886);
transaction(64'hfffffffffff7c486,32'h116d);
transaction(64'hfffffffffffcefed,32'hbf845);
transaction(64'hfffffffffffd420f,32'h107f7c);
transaction(64'hfffffffffff58946,32'h1df);
transaction(64'hfffffffffffbbf7a,32'h3a4e9);
transaction(64'hfffffffffffbfd91,32'h4a4fb);
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
