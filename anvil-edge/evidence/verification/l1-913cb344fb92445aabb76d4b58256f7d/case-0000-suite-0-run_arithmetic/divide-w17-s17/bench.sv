
module bench;
  reg clk=0;
  reg rst_n;
  reg in_valid=0, out_ready=0;
  wire in_ready, out_valid;
  integer cycle, count=0;
  always #5 clk=~clk;
  
  reg [16:0] numerator=0, denominator=0;
  wire [16:0] quotient, remainder;
  wire divide_by_zero;
  anvil_edge_unsigned_divider #(.WIDTH(17)) dut(
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
    numerator=17'h0; denominator=17'h0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=0");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=0 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h0 || divide_by_zero!==1'b1))
      $fatal(1,"ARITH_RESULT trial=0 latency=18");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h0 || divide_by_zero!==1'b1))
        $fatal(1,"ARITH_STALL trial=0");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=0");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=1");
    numerator=17'h0; denominator=17'h1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=1");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=1 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=1 latency=18");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=1");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=1");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=2");
    numerator=17'h0; denominator=17'hffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=2");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=2 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=2 latency=18");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=2");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=2");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=3");
    numerator=17'h0; denominator=17'h1ffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=3");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=3 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=3 latency=18");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=3");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=3");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=4");
    numerator=17'h1; denominator=17'h0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=4");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=4 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h0 || divide_by_zero!==1'b1))
      $fatal(1,"ARITH_RESULT trial=4 latency=18");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h0 || divide_by_zero!==1'b1))
        $fatal(1,"ARITH_STALL trial=4");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=4");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=5");
    numerator=17'h1; denominator=17'h1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=5");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=5 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=5 latency=18");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=5");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=5");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=6");
    numerator=17'h1; denominator=17'hffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=6");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=6 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h1 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=6 latency=18");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h1 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=6");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=6");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=7");
    numerator=17'h1; denominator=17'h1ffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=7");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=7 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h1 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=7 latency=18");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h1 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=7");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=7");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=8");
    numerator=17'hffff; denominator=17'h0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=8");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=8 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h0 || divide_by_zero!==1'b1))
      $fatal(1,"ARITH_RESULT trial=8 latency=18");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h0 || divide_by_zero!==1'b1))
        $fatal(1,"ARITH_STALL trial=8");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=8");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=9");
    numerator=17'hffff; denominator=17'h1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=9");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=9 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'hffff || remainder!==17'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=9 latency=18");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'hffff || remainder!==17'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=9");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=9");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=10");
    numerator=17'hffff; denominator=17'hffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=10");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=10 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=10 latency=18");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=10");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=10");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=11");
    numerator=17'hffff; denominator=17'h1ffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=11");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=11 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'hffff || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=11 latency=18");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'hffff || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=11");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=11");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=12");
    numerator=17'h1ffff; denominator=17'h0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=12");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=12 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h0 || divide_by_zero!==1'b1))
      $fatal(1,"ARITH_RESULT trial=12 latency=18");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h0 || divide_by_zero!==1'b1))
        $fatal(1,"ARITH_STALL trial=12");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=12");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=13");
    numerator=17'h1ffff; denominator=17'h1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=13");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=13 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1ffff || remainder!==17'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=13 latency=18");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1ffff || remainder!==17'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=13");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=13");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=14");
    numerator=17'h1ffff; denominator=17'hffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=14");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=14 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h2 || remainder!==17'h1 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=14 latency=18");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h2 || remainder!==17'h1 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=14");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=14");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=15");
    numerator=17'h1ffff; denominator=17'h1ffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=15");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=15 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'h0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=15 latency=18");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'h0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=15");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=15");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=16");
    numerator=17'h10b41; denominator=17'hd40d;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=16");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=16 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'h3734 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=16 latency=18");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'h3734 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=16");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=16");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=17");
    numerator=17'h19d06; denominator=17'h9b5a;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=17");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=17 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h2 || remainder!==17'h6652 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=17 latency=18");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h2 || remainder!==17'h6652 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=17");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=17");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=18");
    numerator=17'h1ebc5; denominator=17'hbb33;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=18");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=18 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h2 || remainder!==17'h755f || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=18 latency=18");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h2 || remainder!==17'h755f || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=18");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=18");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=19");
    numerator=17'h9449; denominator=17'h5970;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=19");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=19 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'h3ad9 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=19 latency=18");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'h3ad9 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=19");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=19");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=20");
    numerator=17'h1883f; denominator=17'h16908;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=20");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=20 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'h1f37 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=20 latency=18");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'h1f37 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=20");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=20");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=21");
    numerator=17'h1688f; denominator=17'h11493;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=21");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=21 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'h53fc || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=21 latency=18");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'h53fc || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=21");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=21");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=22");
    numerator=17'h152a0; denominator=17'h8e7a;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=22");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=22 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h2 || remainder!==17'h35ac || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=22 latency=18");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h2 || remainder!==17'h35ac || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=22");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=22");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=23");
    numerator=17'h3867; denominator=17'h1d5c1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=23");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=23 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h3867 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=23 latency=18");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h3867 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=23");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=23");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=24");
    numerator=17'hdca; denominator=17'h7f70;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=24");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=24 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'hdca || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=24 latency=18");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'hdca || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=24");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=24");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=25");
    numerator=17'hc4b2; denominator=17'h1a160;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=25");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=25 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'hc4b2 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=25 latency=18");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'hc4b2 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=25");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=25");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=26");
    numerator=17'h17e27; denominator=17'hd6d1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=26");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=26 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'ha756 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=26 latency=18");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'ha756 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=26");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=26");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=27");
    numerator=17'h8138; denominator=17'h1b82b;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=27");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=27 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h8138 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=27 latency=18");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h8138 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=27");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=27");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=28");
    numerator=17'h100d2; denominator=17'h19ad0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=28");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=28 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h100d2 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=28 latency=18");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h100d2 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=28");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=28");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=29");
    numerator=17'ha286; denominator=17'h147f2;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=29");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=29 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'ha286 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=29 latency=18");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'ha286 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=29");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=29");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=30");
    numerator=17'h1b151; denominator=17'h15e6e;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=30");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=30 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'h52e3 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=30 latency=18");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'h52e3 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=30");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=30");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=31");
    numerator=17'h1e3f0; denominator=17'h172d3;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=31");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=31 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'h711d || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=31 latency=18");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'h711d || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=31");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=31");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=32");
    numerator=17'hcd9d; denominator=17'h466b;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=32");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=32 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h2 || remainder!==17'h40c7 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=32 latency=18");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h2 || remainder!==17'h40c7 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=32");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=32");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=33");
    numerator=17'h1ff34; denominator=17'h11a34;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=33");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=33 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'he500 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=33 latency=18");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'he500 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=33");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=33");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=34");
    numerator=17'h1fd7; denominator=17'h479e;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=34");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=34 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h1fd7 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=34 latency=18");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h1fd7 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=34");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=34");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=35");
    numerator=17'h1a00e; denominator=17'h1954f;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=35");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=35 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'habf || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=35 latency=18");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'habf || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=35");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=35");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=36");
    numerator=17'h1c029; denominator=17'h64a4;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=36");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=36 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h4 || remainder!==17'h2d99 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=36 latency=18");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h4 || remainder!==17'h2d99 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=36");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=36");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=37");
    numerator=17'h4d44; denominator=17'h1c3ff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=37");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=37 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h4d44 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=37 latency=18");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h4d44 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=37");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=37");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=38");
    numerator=17'h16940; denominator=17'h110d2;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=38");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=38 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'h586e || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=38 latency=18");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'h586e || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=38");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=38");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=39");
    numerator=17'h11e27; denominator=17'h19a84;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=39");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=39 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h11e27 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=39 latency=18");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h11e27 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=39");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=39");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=40");
    numerator=17'h1e90e; denominator=17'h15f25;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=40");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=40 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'h89e9 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=40 latency=18");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'h89e9 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=40");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=40");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=41");
    numerator=17'h6b86; denominator=17'ha97d;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=41");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=41 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h6b86 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=41 latency=18");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h6b86 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=41");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=41");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=42");
    numerator=17'h11476; denominator=17'h3f3b;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=42");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=42 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h4 || remainder!==17'h178a || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=42 latency=18");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h4 || remainder!==17'h178a || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=42");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=42");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=43");
    numerator=17'h1c3d1; denominator=17'h16e61;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=43");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=43 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'h5570 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=43 latency=18");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'h5570 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=43");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=43");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=44");
    numerator=17'h1470d; denominator=17'h236b;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=44");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=44 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h9 || remainder!==17'h84a || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=44 latency=18");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h9 || remainder!==17'h84a || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=44");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=44");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=45");
    numerator=17'h9e4f; denominator=17'hd1c0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=45");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=45 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h9e4f || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=45 latency=18");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h9e4f || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=45");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=45");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=46");
    numerator=17'h29ea; denominator=17'h103bb;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=46");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=46 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h0 || remainder!==17'h29ea || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=46 latency=18");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h0 || remainder!==17'h29ea || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=46");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=46");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=47");
    numerator=17'h1e12a; denominator=17'h1b7ab;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=47");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<18;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=47 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==17'h1 || remainder!==17'h297f || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=47 latency=18");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==17'h1 || remainder!==17'h297f || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=47");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=47");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk); numerator=17'h1e12a; denominator=17'h1b7ab; in_valid=1;
    @(posedge clk);
    @(negedge clk); #1; in_valid=0; rst_n=0;
    #1; reset_check();
    repeat (2) @(negedge clk);
    rst_n=1;
    repeat (21) begin
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
