
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
    rst_n=0; #1ps; reset_check();
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
transaction(64'h75e2fc574dad2986,32'h1000000);
transaction(64'hc73d212ba950666d,32'h0);
transaction(64'h86e55426eae0d2c1,32'h0);
transaction(64'h4d68615c80690847,32'h1000000);
transaction(64'h3969ec07f1f83a79,32'h1000000);
transaction(64'h6014be00caa7e9bf,32'h1000000);
transaction(64'h2f929a91f4873115,32'h1000000);
transaction(64'ha3b09dd54bec7d8,32'h1000000);
transaction(64'hcf27b35c11b5aecd,32'h0);
transaction(64'h1995d8aaff0f3b81,32'h1000000);
transaction(64'h4fec9e2caebf9993,32'h1000000);
transaction(64'h8490ca26561d2417,32'h0);
transaction(64'h125b1ec95f4807bc,32'h1000000);
transaction(64'hbd2b9a3667cc1752,32'h0);
transaction(64'h8ee06e0b5c15cfd1,32'h0);
transaction(64'h495613ef1071e6da,32'h1000000);
transaction(64'hfffffffffff62afc,32'h384);
transaction(64'hfffffffffff424bf,32'h76);
transaction(64'hfffffffffff80169,32'h161b);
transaction(64'hfffffffffff9d7ed,32'h8ae8);
transaction(64'hfffffffffffb215a,32'h1f705);
transaction(64'hfffffffffffa3441,32'hc73b);
transaction(64'hfffffffffff57699,32'h1bd);
transaction(64'hfffffffffffaa057,32'h12fe5);
transaction(64'hfffffffffff302fa,32'h26);
transaction(64'hfffffffffff8b8f4,32'h2d47);
transaction(64'hfffffffffffab93b,32'h14eed);
transaction(64'hfffffffffff04ffb,32'h2);
transaction(64'hfffffffffff19eb9,32'h9);
transaction(64'hfffffffffffb22d9,32'h1f9f8);
transaction(64'hfffffffffff09d69,32'h3);
transaction(64'hfffffffffffef2f7,32'h598077);
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
