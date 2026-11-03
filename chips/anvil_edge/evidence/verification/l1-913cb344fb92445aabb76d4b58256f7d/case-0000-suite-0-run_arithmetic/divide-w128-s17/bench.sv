
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
    repeat (4) begin
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
    repeat (6) begin
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
    repeat (3) begin
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
    repeat (6) begin
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
    repeat (4) begin
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
    repeat (4) begin
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
    repeat (3) begin
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
    repeat (3) begin
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
    repeat (4) begin
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
    repeat (5) begin
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
    repeat (5) begin
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
    repeat (6) begin
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
    repeat (2) begin
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
    numerator=128'h4dad2986ce8349606a06e9ab85a0bcc1; denominator=128'h2cb85f3f4a24e39a5d998017f5e2fc57;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=16");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=16 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h20f4ca47845e65c60c6d69938fbdc06a || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=16 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h20f4ca47845e65c60c6d69938fbdc06a || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=16");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=16");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=17");
    numerator=128'h8a4996efb447c0ceb48438b5c41f9dfd; denominator=128'heae0d2c11c339464473d212ba950666d;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=17");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=17 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h8a4996efb447c0ceb48438b5c41f9dfd || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=17 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h8a4996efb447c0ceb48438b5c41f9dfd || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=17");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=17");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=18");
    numerator=128'hd0b0090d625909923fb81d2706e55426; denominator=128'hdc159e6a409c38f26b68b48ebf13c171;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=18");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=18 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'hd0b0090d625909923fb81d2706e55426 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=18 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'hd0b0090d625909923fb81d2706e55426 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=18");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=18");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=19");
    numerator=128'ha3f96f0e51436d1fcd68615c80690847; denominator=128'hb969ec07f1f83a79af371d87d8a8f065;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=19");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=19 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'ha3f96f0e51436d1fcd68615c80690847 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=19 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'ha3f96f0e51436d1fcd68615c80690847 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=19");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=19");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=20");
    numerator=128'h8d1a6bffff9a39142335e9e266cea9fa; denominator=128'hcaa7e9bfd00724a123cf493f0febddf8;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=20");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=20 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h8d1a6bffff9a39142335e9e266cea9fa || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=20 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h8d1a6bffff9a39142335e9e266cea9fa || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=20");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=20");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=21");
    numerator=128'he1ff83ab26a2658f32521553e014be00; denominator=128'hcd425ec38f1389998869510db4a02517;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=21");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=21 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h14bd24e7978edbf5a9e8c4462b7498e9 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=21 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h14bd24e7978edbf5a9e8c4462b7498e9 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=21");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=21");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=22");
    numerator=128'h54bec7d835c33744af929a91f4873115; denominator=128'hb730d88fe1e8a4aa1f9db8dd8a3b09dd;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=22");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=22 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h54bec7d835c33744af929a91f4873115 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=22 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h54bec7d835c33744af929a91f4873115 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=22");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=22");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=23");
    numerator=128'h68e06b0c4f27b35c11b5aecda386a3a0; denominator=128'hdbd5f6d2f09529af81dda9da14f50791;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=23");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=23 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h68e06b0c4f27b35c11b5aecda386a3a0 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=23 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h68e06b0c4f27b35c11b5aecda386a3a0 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=23");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=23");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=24");
    numerator=128'h9995d8aaff0f3b81a3e2889c795e846b; denominator=128'h689edcd6cfec9e2caebf999324405d96;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=24");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=24 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h30f6fbd42f229d54f522ef09551e26d5 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=24 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h30f6fbd42f229d54f522ef09551e26d5 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=24");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=24");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=25");
    numerator=128'h561d2417eb837ba8818dced3d0398c72; denominator=128'h925b1ec95f4807bc6ecace3c0490ca26;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=25");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=25 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h561d2417eb837ba8818dced3d0398c72 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=25 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h561d2417eb837ba8818dced3d0398c72 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=25");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=25");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=26");
    numerator=128'hbd27b4f2c0855ac9e599e3580d3a2dc6; denominator=128'h7a2c3b72f5a2224a0ce02d285ac9cd0e;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=26");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=26 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h42fb797fcae3387fd8b9b62fb27060b8 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=26 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h42fb797fcae3387fd8b9b62fb27060b8 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=26");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=26");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=27");
    numerator=128'h1520627c63d6f69947feaa35ff4cb50; denominator=128'h1df995313d2b9a3667cc1752de27660b;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=27");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=27 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h1520627c63d6f69947feaa35ff4cb50 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=27 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h1520627c63d6f69947feaa35ff4cb50 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=27");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=27");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=28");
    numerator=128'h3fa244adf517a77536be6e688e8b88c2; denominator=128'hee06e0b5c15cfd1f515f75186e41524;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=28");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=28 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h4 || remainder!==128'h4208c8084c0682d6266912272fb3432 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=28 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h4 || remainder!==128'h4208c8084c0682d6266912272fb3432 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=28");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=28");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=29");
    numerator=128'h468629e8c95613ef1071e6da44673e23; denominator=128'hd422051f9a98f4d0bf5da6cc3157e672;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=29");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=29 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h468629e8c95613ef1071e6da44673e23 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=29 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h468629e8c95613ef1071e6da44673e23 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=29");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=29");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=30");
    numerator=128'he6d747b48db0eb42887b5f5f8e384a7b; denominator=128'h4ebf6be1a897b98f400b49322125fd8a;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=30");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=30 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h2 || remainder!==128'h49586ff13c8178240864ccfb4bec4f67 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=30 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h2 || remainder!==128'h49586ff13c8178240864ccfb4bec4f67 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=30");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=30");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=31");
    numerator=128'h2bb4c81151a20dc3590ad570eaa1a8c3; denominator=128'h932d838de8b6e53d1817d0235502bfbd;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=31");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=31 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h2bb4c81151a20dc3590ad570eaa1a8c3 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=31 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h2bb4c81151a20dc3590ad570eaa1a8c3 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=31");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=31");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=32");
    numerator=128'h55c9dfdb45c7a738c84b75db940e6e2b; denominator=128'hfd9399c0c0d644210cf5ce20027fd9eb;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=32");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=32 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h55c9dfdb45c7a738c84b75db940e6e2b || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=32 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h55c9dfdb45c7a738c84b75db940e6e2b || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=32");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=32");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=33");
    numerator=128'hbea12ba57797b9dc04eb48705916ca58; denominator=128'hdd00e8fa212f8fc794baead45c2c169;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=33");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=33 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'hd || remainder!==128'hb106e5a3ca11509dc1369a3ce32f803 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=33 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'hd || remainder!==128'hb106e5a3ca11509dc1369a3ce32f803 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=33");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=33");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=34");
    numerator=128'h42114abf4f4e45b432c3233dba9eba35; denominator=128'hb71e77b2fc9e4dc6bf89b6551335276b;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=34");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=34 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h42114abf4f4e45b432c3233dba9eba35 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=34 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h42114abf4f4e45b432c3233dba9eba35 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=34");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=34");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=35");
    numerator=128'h9efd9ce2054a108a7c22ca48e8f8746d; denominator=128'h236dac08af9d96348676b326906e6a67;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=35");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=35 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h4 || remainder!==128'h1146ecbf46d3b7b86247fdaea73ecad1 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=35 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h4 || remainder!==128'h1146ecbf46d3b7b86247fdaea73ecad1 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=35");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=35");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=36");
    numerator=128'hf391361abb4cca3e7c21ab0d672bd7e9; denominator=128'hd10322399713d85bfa843e7cf5b67503;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=36");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=36 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h228e13e12438f1e2819d6c90717562e6 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=36 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h228e13e12438f1e2819d6c90717562e6 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=36");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=36");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=37");
    numerator=128'hfed259c33215ff4f2eebdd04643e2ec8; denominator=128'had22a5cd269aed1df5fd749b405cf5d4;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=37");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=37 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h51afb3f60b7b123138ee686923e138f4 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=37 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h51afb3f60b7b123138ee686923e138f4 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=37");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=37");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=38");
    numerator=128'hcdbbb62365f2c2ce849dddd1c43af35; denominator=128'h4e1c7a4189776347f9288931d78ee74f;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=38");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=38 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'hcdbbb62365f2c2ce849dddd1c43af35 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=38 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'hcdbbb62365f2c2ce849dddd1c43af35 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=38");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=38");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=39");
    numerator=128'h50c5238ceb914b43e3c44e83ce104541; denominator=128'h2954cac80ca84ac850eff308cf8f95c3;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=39");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=39 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h277058c4dee9007b92d45b7afe80af7e || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=39 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h277058c4dee9007b92d45b7afe80af7e || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=39");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=39");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=40");
    numerator=128'hb0fb0baf17c13b146b436ce7ed0ba755; denominator=128'h402373eed6c500f44fd46da3c55e0334;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=40");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=40 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h2 || remainder!==128'h30b423d16a37392bcb9a91a0624fa0ed || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=40 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h2 || remainder!==128'h30b423d16a37392bcb9a91a0624fa0ed || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=40");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=40");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=41");
    numerator=128'h7af1f5a66757bf9bff41dda5a84ebb83; denominator=128'h8b04422515cc9e1d8ac9b7621334518f;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=41");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=41 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h7af1f5a66757bf9bff41dda5a84ebb83 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=41 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h7af1f5a66757bf9bff41dda5a84ebb83 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=41");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=41");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=42");
    numerator=128'h399568613de05552fab3520fa2f1d748; denominator=128'h9373452a43e5eca6f539e15e8843a942;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=42");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=42 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h399568613de05552fab3520fa2f1d748 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=42 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h399568613de05552fab3520fa2f1d748 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=42");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=42");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=43");
    numerator=128'hc996e734b94bd74cd26be6629d52d7a; denominator=128'h961ec5f97c9fd32ce3405e87b990dea6;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=43");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=43 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'hc996e734b94bd74cd26be6629d52d7a || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=43 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'hc996e734b94bd74cd26be6629d52d7a || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=43");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=43");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=44");
    numerator=128'h38f40afe7c8a1d56d30f0290648c8fa9; denominator=128'ha0768bb88402cc0d686b4c8f8dd1e2d3;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=44");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=44 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h38f40afe7c8a1d56d30f0290648c8fa9 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=44 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h38f40afe7c8a1d56d30f0290648c8fa9 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=44");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=44");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=45");
    numerator=128'h75985078f7a6975613d07a7071ef624e; denominator=128'h7ba217043aa3c05e37f83844c0718532;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=45");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=45 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h75985078f7a6975613d07a7071ef624e || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=45 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h75985078f7a6975613d07a7071ef624e || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=45");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=45");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=46");
    numerator=128'hf8421fc13055291bd1d2a80d51787cb1; denominator=128'hf627c0200743c7f899210c635d352450;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=46");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=46 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h21a5fa12911612338b19ba9f4435861 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=46 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h21a5fa12911612338b19ba9f4435861 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=46");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=46");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=47");
    numerator=128'h84fa49ef91612c4e93f8d5a3be97c0e1; denominator=128'hd51012f6e4b841e60dbe6bc16c34cf6c;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=47");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=47 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h84fa49ef91612c4e93f8d5a3be97c0e1 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=47 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h84fa49ef91612c4e93f8d5a3be97c0e1 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=47");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=47");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk); numerator=128'h84fa49ef91612c4e93f8d5a3be97c0e1; denominator=128'hd51012f6e4b841e60dbe6bc16c34cf6c; in_valid=1;
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
