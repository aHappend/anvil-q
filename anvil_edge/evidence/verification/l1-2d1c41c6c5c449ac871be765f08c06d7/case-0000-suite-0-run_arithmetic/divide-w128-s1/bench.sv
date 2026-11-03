
module bench;
  reg clk=0;
  reg rst_n;
  reg in_valid=0, out_ready=0;
  wire in_ready, out_valid;
  integer cycle, count=0;
  always #5 clk=~clk;
  
  reg [127:0] numerator=0, denominator=0;
  wire [127:0] quotient, remainder;
  wire divide_by_zero;
  anvil_edge_unsigned_divider #(.WIDTH(128)) dut(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(in_ready),
    .numerator(numerator),.denominator(denominator),.out_valid(out_valid),
    .out_ready(out_ready),.quotient(quotient),.remainder(remainder),
    .divide_by_zero(divide_by_zero));

  task automatic reset_check;
    begin
      if (in_ready!==0 || out_valid!==0 || (quotient!==0 || remainder!==0 || divide_by_zero!==0))
        $fatal(1,"ARITH_RESET time=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    rst_n=0;
    #0; reset_check();
    repeat (2) @(negedge clk);
    rst_n=1;
    
    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=0");
    numerator=128'h0; denominator=128'h0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=0");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=0 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h0 || divide_by_zero!==1'b1))
      $fatal(1,"ARITH_RESULT trial=0 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h0 || divide_by_zero!==1'b1))
        $fatal(1,"ARITH_STALL trial=0");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=0");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=1");
    numerator=128'h0; denominator=128'h1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=1");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=1 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=1 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=1");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=1");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=2");
    numerator=128'h0; denominator=128'h7fffffffffffffffffffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=2");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=2 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=2 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=2");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=2");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=3");
    numerator=128'h0; denominator=128'hffffffffffffffffffffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=3");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=3 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=3 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=3");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=3");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=4");
    numerator=128'h1; denominator=128'h0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=4");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=4 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h0 || divide_by_zero!==1'b1))
      $fatal(1,"ARITH_RESULT trial=4 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h0 || divide_by_zero!==1'b1))
        $fatal(1,"ARITH_STALL trial=4");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=4");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=5");
    numerator=128'h1; denominator=128'h1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=5");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=5 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=5 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=5");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=5");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=6");
    numerator=128'h1; denominator=128'h7fffffffffffffffffffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=6");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=6 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h1 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=6 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h1 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=6");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=6");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=7");
    numerator=128'h1; denominator=128'hffffffffffffffffffffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=7");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=7 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h1 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=7 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h1 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=7");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=7");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=8");
    numerator=128'h7fffffffffffffffffffffffffffffff; denominator=128'h0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=8");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=8 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h0 || divide_by_zero!==1'b1))
      $fatal(1,"ARITH_RESULT trial=8 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h0 || divide_by_zero!==1'b1))
        $fatal(1,"ARITH_STALL trial=8");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=8");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=9");
    numerator=128'h7fffffffffffffffffffffffffffffff; denominator=128'h1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=9");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=9 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h7fffffffffffffffffffffffffffffff || remainder!==128'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=9 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h7fffffffffffffffffffffffffffffff || remainder!==128'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=9");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=9");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=10");
    numerator=128'h7fffffffffffffffffffffffffffffff; denominator=128'h7fffffffffffffffffffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=10");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=10 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=10 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=10");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=10");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=11");
    numerator=128'h7fffffffffffffffffffffffffffffff; denominator=128'hffffffffffffffffffffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=11");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=11 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h7fffffffffffffffffffffffffffffff || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=11 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h7fffffffffffffffffffffffffffffff || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=11");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=11");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=12");
    numerator=128'hffffffffffffffffffffffffffffffff; denominator=128'h0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=12");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=12 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h0 || divide_by_zero!==1'b1))
      $fatal(1,"ARITH_RESULT trial=12 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h0 || divide_by_zero!==1'b1))
        $fatal(1,"ARITH_STALL trial=12");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=12");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=13");
    numerator=128'hffffffffffffffffffffffffffffffff; denominator=128'h1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=13");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=13 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'hffffffffffffffffffffffffffffffff || remainder!==128'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=13 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'hffffffffffffffffffffffffffffffff || remainder!==128'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=13");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=13");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=14");
    numerator=128'hffffffffffffffffffffffffffffffff; denominator=128'h7fffffffffffffffffffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=14");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=14 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h2 || remainder!==128'h1 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=14 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h2 || remainder!==128'h1 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=14");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=14");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=15");
    numerator=128'hffffffffffffffffffffffffffffffff; denominator=128'hffffffffffffffffffffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=15");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=15 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=15 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=15");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=15");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=16");
    numerator=128'hcd613e30d8f16adf91b7584a2265b1f5; denominator=128'h1e2feb89414c343c1027c4d1c386bbc4;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=16");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=16 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h6 || remainder!==128'h1841b8f95128317730c8bb5f8d3d4b5d || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=16 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h6 || remainder!==128'h1841b8f95128317730c8bb5f8d3d4b5d || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=16");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=16");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=17");
    numerator=128'h78e510617311d8a3c2ce6f447ed4d57b; denominator=128'h35bf992dc9e9c616612e7696a6cecc1b;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=17");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=17 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h2 || remainder!==128'hd65de05df3e4c770071821731373d45 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=17 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h2 || remainder!==128'hd65de05df3e4c770071821731373d45 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=17");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=17");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=18");
    numerator=128'he4b06ce60741c7a87ce42c8218072e8c; denominator=128'h9b810e766ec9d28663ca828dd5f4b3b2;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=18");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=18 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h492f5e6f9877f5221919a9f442127ada || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=18 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h492f5e6f9877f5221919a9f442127ada || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=18");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=18");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=19");
    numerator=128'hb2221a58008a05a6c4647159c324c985; denominator=128'hcd447e35b8b6d8fe442e3d437204e52d;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=19");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=19 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'hb2221a58008a05a6c4647159c324c985 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=19 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'hb2221a58008a05a6c4647159c324c985 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=19");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=19");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=20");
    numerator=128'h1a2b8f1ff1fd42a29755d4c13a902931; denominator=128'h5b6e6e307d4bedc51431193e6c3f339;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=20");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=20 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h4 || remainder!==128'h34ff393d2aa473152498e719f805c4d || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=20 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h4 || remainder!==128'h34ff393d2aa473152498e719f805c4d || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=20");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=20");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=21");
    numerator=128'h25b413f8a9a021ea648a7dd06839eb9; denominator=128'hafbd67f9619699cfe1988ad9f06c144a;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=21");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=21 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h25b413f8a9a021ea648a7dd06839eb9 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=21 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h25b413f8a9a021ea648a7dd06839eb9 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=21");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=21");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=22");
    numerator=128'hb9d179e06c0fd4f5f8130c4237730edf; denominator=128'hc381e88f38c0c8fd8712b8bc076f3787;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=22");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=22 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'hb9d179e06c0fd4f5f8130c4237730edf || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=22 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'hb9d179e06c0fd4f5f8130c4237730edf || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=22");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=22");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=23");
    numerator=128'h8d88348a7eed8d14f06d3fef701966a0; denominator=128'had45f23d3b1a11df587fd2803bab6c39;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=23");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=23 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h8d88348a7eed8d14f06d3fef701966a0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=23 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h8d88348a7eed8d14f06d3fef701966a0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=23");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=23");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=24");
    numerator=128'hf3c64af775a89294c2cd789a380208a9; denominator=128'h6a8ac4ba05805975ed2f89d94a2f20aa;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=24");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=24 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h2 || remainder!==128'h1eb0c1836aa7dfa8e86e64e7a3a3c755 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=24 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h2 || remainder!==128'h1eb0c1836aa7dfa8e86e64e7a3a3c755 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=24");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=24");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=25");
    numerator=128'hec148cb48e73ca47ea90a8f0d66b829e; denominator=128'ha11d459a2f978d8719999e3fa46d6753;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=25");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=25 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h4af7471a5edc3cc0d0f70ab131fe1b4b || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=25 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h4af7471a5edc3cc0d0f70ab131fe1b4b || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=25");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=25");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=26");
    numerator=128'h4be03db0dc2574bdb94067edfe175330; denominator=128'he5446dd4552b82f6be3edc0a1ef2a4f0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=26");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=26 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h4be03db0dc2574bdb94067edfe175330 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=26 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h4be03db0dc2574bdb94067edfe175330 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=26");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=26");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=27");
    numerator=128'h803468b6b610a9f7f9270f4eb8b333a8; denominator=128'h81f9c1f66c0f3459f79b17aeefba91fc;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=27");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=27 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h803468b6b610a9f7f9270f4eb8b333a8 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=27 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h803468b6b610a9f7f9270f4eb8b333a8 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=27");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=27");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=28");
    numerator=128'h3099fdf5ab99254ae901e35cd47d380d; denominator=128'hf9341c68966baea148beab134da98f1d;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=28");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=28 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h3099fdf5ab99254ae901e35cd47d380d || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=28 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h3099fdf5ab99254ae901e35cd47d380d || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=28");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=28");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=29");
    numerator=128'hf0dfb4a5d8a064df7fd63116e1ea24c4; denominator=128'hda71144896c8da1964b2d2bc815a47c5;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=29");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=29 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h166ea05d41d78ac61b235e5a608fdcff || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=29 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h166ea05d41d78ac61b235e5a608fdcff || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=29");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=29");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=30");
    numerator=128'hbe6521cc3e2434e37af027bc08d6af57; denominator=128'haa2ca1af6a107b75677f6cbdcc22af58;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=30");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=30 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h1438801cd413b96e1370bafe3cb3ffff || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=30 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h1438801cd413b96e1370bafe3cb3ffff || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=30");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=30");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=31");
    numerator=128'he1fab9d78c7e134f5dfbd3d12c4a3698; denominator=128'hbcfbb050acab1a6bc69d4bd8b3fa7aa7;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=31");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=31 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h24ff0986dfd2f8e3975e87f8784fbbf1 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=31 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h24ff0986dfd2f8e3975e87f8784fbbf1 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=31");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=31");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=32");
    numerator=128'ha9ec0806705fca161622bd795fec898f; denominator=128'h29e821a4c74803e31ba1621582283d15;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=32");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=32 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h4 || remainder!==128'h24b8173533fba89a79d3523574b953b || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=32 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h4 || remainder!==128'h24b8173533fba89a79d3523574b953b || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=32");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=32");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=33");
    numerator=128'h5eda92d864ac5db9d707107e855c3844; denominator=128'h78255d6807923986bb968a437d5c8dfc;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=33");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=33 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h5eda92d864ac5db9d707107e855c3844 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=33 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h5eda92d864ac5db9d707107e855c3844 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=33");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=33");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=34");
    numerator=128'hd92a4aa2b410d93c4efbc8d60b21fbac; denominator=128'h9403560d97dae38d9d643c25fbb230bb;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=34");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=34 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h4526f4951c35f5aeb1978cb00f6fcaf1 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=34 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h4526f4951c35f5aeb1978cb00f6fcaf1 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=34");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=34");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=35");
    numerator=128'h2b28fef02b9c014ea5ac06d864c2f2e3; denominator=128'h326324dfb695ffb3a1890c78092b4d4;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=35");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=35 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'hd || remainder!==128'h23870fa6742218cb26cacb6dd4fc41f || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=35 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'hd || remainder!==128'h23870fa6742218cb26cacb6dd4fc41f || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=35");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=35");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=36");
    numerator=128'heb8ac8ce8a245e6b33138131c541013d; denominator=128'h678a5aa33b6fe5078c5fe8f8dc3bf364;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=36");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=36 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h2 || remainder!==128'h1c7613881344945c1a53af400cc91a75 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=36 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h2 || remainder!==128'h1c7613881344945c1a53af400cc91a75 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=36");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=36");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=37");
    numerator=128'hd8f33418f3d4e7115804f92283868a29; denominator=128'he8e5b4617589a82b5a702cfa93ea5c4e;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=37");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=37 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'hd8f33418f3d4e7115804f92283868a29 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=37 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'hd8f33418f3d4e7115804f92283868a29 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=37");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=37");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=38");
    numerator=128'h9be3cecb8c497c68a8c24d4244ef7feb; denominator=128'h62397bc701762741bab9f87ff5059285;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=38");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=38 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h39aa53048ad35526ee0854c24fe9ed66 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=38 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h39aa53048ad35526ee0854c24fe9ed66 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=38");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=38");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=39");
    numerator=128'hf463b337d20b5d59db610487c89da11b; denominator=128'h83333218bd91a1b7f03edca7e2dcaa37;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=39");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=39 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h7130811f1479bba1eb2227dfe5c0f6e4 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=39 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h7130811f1479bba1eb2227dfe5c0f6e4 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=39");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=39");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=40");
    numerator=128'hc703806984c8199921167d8fcf23cae8; denominator=128'hf320cd576d14475b349aae908fb5262c;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=40");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=40 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'hc703806984c8199921167d8fcf23cae8 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=40 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'hc703806984c8199921167d8fcf23cae8 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=40");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=40");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=41");
    numerator=128'h5d5f576cdeb8fc4c7b297d0b0e5e18ba; denominator=128'hf0e642f43328ad088ded3c9691eb79fa;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=41");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=41 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h5d5f576cdeb8fc4c7b297d0b0e5e18ba || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=41 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h5d5f576cdeb8fc4c7b297d0b0e5e18ba || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=41");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=41");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=42");
    numerator=128'hd037cdff7c240d4969d495dd81355c53; denominator=128'h67dba8589890086a17b9af5b569643;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=42");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=42 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h201 || remainder!==128'h18a1a5f26b6c6cd0497d7778b24010 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=42 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h201 || remainder!==128'h18a1a5f26b6c6cd0497d7778b24010 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=42");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=42");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=43");
    numerator=128'hc9546b439f9d01298a449ebe89d9bf02; denominator=128'h99901c0475491bc354c56c9a9cc9af4e;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=43");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=43 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h2fc44f3f2a53e566357f3223ed100fb4 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=43 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h2fc44f3f2a53e566357f3223ed100fb4 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=43");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=43");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=44");
    numerator=128'ha2a7ae1f3ac7652ccdf8440407295e42; denominator=128'h2e47dc0e959f3a518cfe5cd12d5db79b;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=44");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=44 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h3 || remainder!==128'h17d019f379e9b63826fd2d907f103771 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=44 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h3 || remainder!==128'h17d019f379e9b63826fd2d907f103771 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=44");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=44");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=45");
    numerator=128'h8d103ed3cc667e971773308cdc6b13ab; denominator=128'hee52bdb6d1020a15d9ed17e3cc0e95ee;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=45");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=45 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h8d103ed3cc667e971773308cdc6b13ab || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=45 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h8d103ed3cc667e971773308cdc6b13ab || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=45");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=45");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=46");
    numerator=128'hf18dd1eed77c96c0084f3dd6415af341; denominator=128'hde3a5db5154ed51212093d26ac512b01;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=46");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=46 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h13537439c22dc1adf64600af9509c840 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=46 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h13537439c22dc1adf64600af9509c840 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=46");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=46");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=47");
    numerator=128'hc10faa4003ba33db73f7ba8e0445d656; denominator=128'h44c5b4763fe31d0347fc816ac16e2284;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=47");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=47 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h2 || remainder!==128'h3784415383f3f9d4e3feb7b88169914e || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=47 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h2 || remainder!==128'h3784415383f3f9d4e3feb7b88169914e || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=47");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=47");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk); numerator=128'hc10faa4003ba33db73f7ba8e0445d656; denominator=128'h44c5b4763fe31d0347fc816ac16e2284; in_valid=1;
    @(posedge clk);
    @(negedge clk); #1; in_valid=0; rst_n=0;
    #1; reset_check();
    repeat (2) @(negedge clk);
    rst_n=1;
    repeat (132) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_RESET_STALE");
    end
    if (count!=48) $fatal(1,"ARITH_COUNT");
    $display("COMPARED %0d",count);
    $finish;
  end
  initial begin
    repeat (100000) @(posedge clk);
    $fatal(1,"ARITH_CYCLE_BOUND");
  end
endmodule
