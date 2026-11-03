
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
    repeat (6) begin
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
    repeat (5) begin
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
    repeat (2) begin
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
    repeat (5) begin
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
    repeat (7) begin
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
    repeat (3) begin
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
    repeat (2) begin
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
    numerator=128'hb406dd299b576d64c4905c0914c25b99; denominator=128'h5822d7b023fd7e3642408ea4ff6b17a4;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=16");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=16 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h2 || remainder!==128'h3c12dc9535c70f8400f3ebf15ec2c51 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=16 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h2 || remainder!==128'h3c12dc9535c70f8400f3ebf15ec2c51 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=16");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=16");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=17");
    numerator=128'hd8d8d5ed264a6630108ed79cda2f6b1d; denominator=128'h35d321c0e55a1fb1559d3b5b6a806097;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=17");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=17 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h4 || remainder!==128'h18c4ee990e1e76aba19ea2f302de8c1 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=17 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h4 || remainder!==128'h18c4ee990e1e76aba19ea2f302de8c1 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=17");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=17");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=18");
    numerator=128'h5596030cae6c028ab19637574cb8dc48; denominator=128'h2ba9689fdc45b198920595771399ac11;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=18");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=18 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h29ec9a6cd22650f21f90a1e0391f3037 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=18 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h29ec9a6cd22650f21f90a1e0391f3037 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=18");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=18");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=19");
    numerator=128'h39229c3500f0ada69e8ac0a477ba2604; denominator=128'hda6c3109761caf2595894f462530a93c;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=19");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=19 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h39229c3500f0ada69e8ac0a477ba2604 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=19 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h39229c3500f0ada69e8ac0a477ba2604 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=19");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=19");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=20");
    numerator=128'h52f9f8cb8ef660ee0dad1c34c91f4452; denominator=128'h12027fc9174a3140ba58c212f9692fb2;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=20");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=20 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h4 || remainder!==128'haeff9a731cd9beb244a13e8e37a858a || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=20 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h4 || remainder!==128'haeff9a731cd9beb244a13e8e37a858a || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=20");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=20");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=21");
    numerator=128'h67b7a29a152b676579c3964c6993a110; denominator=128'h55f1c02dbcfee5984712a2a1d64d0fb2;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=21");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=21 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h11c5e26c582c81cd32b0f3aa9346915e || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=21 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h11c5e26c582c81cd32b0f3aa9346915e || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=21");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=21");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=22");
    numerator=128'h56eff6f01835404232e1667fdc22942; denominator=128'h801d2f28250ebab6f8f33ecae299a6f6;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=22");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=22 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h56eff6f01835404232e1667fdc22942 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=22 latency=129");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h56eff6f01835404232e1667fdc22942 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=22");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=22");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=23");
    numerator=128'h2557b48817c55c80b3d4fc2439859cc9; denominator=128'ha2b4dd8cc9cdd174019caa0457acabb8;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=23");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=23 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h2557b48817c55c80b3d4fc2439859cc9 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=23 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h2557b48817c55c80b3d4fc2439859cc9 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=23");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=23");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=24");
    numerator=128'h28f2a5048fe9d7799c94bb6d59521b2d; denominator=128'h4fb59979d68a1c9cad44b70fb873d14f;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=24");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=24 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h28f2a5048fe9d7799c94bb6d59521b2d || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=24 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h28f2a5048fe9d7799c94bb6d59521b2d || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=24");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=24");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=25");
    numerator=128'h7c158fd089ecbcc42c6410e68ee417e9; denominator=128'haa279511c074ffd0fdb33a3a65f9a8e1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=25");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=25 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h7c158fd089ecbcc42c6410e68ee417e9 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=25 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h7c158fd089ecbcc42c6410e68ee417e9 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=25");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=25");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=26");
    numerator=128'h8e33f195f83c7a8857afdd6378921d80; denominator=128'haa365d8849bbe0d185faacccecdac455;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=26");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=26 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h8e33f195f83c7a8857afdd6378921d80 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=26 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h8e33f195f83c7a8857afdd6378921d80 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=26");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=26");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=27");
    numerator=128'hdaa2e8f0ec51676334c7a496fc2437ca; denominator=128'h81aa9b40e6cb8771df405ae88efcf976;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=27");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=27 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h58f84db00585dff1558749ae6d273e54 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=27 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h58f84db00585dff1558749ae6d273e54 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=27");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=27");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=28");
    numerator=128'ha743da7d836d4b86e47b48594ff13942; denominator=128'ha1f21c583d28da2acf9290d39c20feab;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=28");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=28 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h551be254644715c14e8b785b3d03a97 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=28 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h551be254644715c14e8b785b3d03a97 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=28");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=28");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=29");
    numerator=128'h9998505bc2ca30c292b11650cdb6bbe2; denominator=128'h2a387fad43e97b776fbabdc65b65e724;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=29");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=29 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h3 || remainder!==128'h1aeed153f70dbe5c4380dcfdbb850676 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=29 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h3 || remainder!==128'h1aeed153f70dbe5c4380dcfdbb850676 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=29");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=29");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=30");
    numerator=128'ha8d422b24d91a692810f85c4cd9da258; denominator=128'h8ef8db4e8c01a8495e13ae573df9c47f;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=30");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=30 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h19db4763c18ffe4922fbd76d8fa3ddd9 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=30 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h19db4763c18ffe4922fbd76d8fa3ddd9 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=30");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=30");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=31");
    numerator=128'he7e8b802223dfd94737ef2820bb02934; denominator=128'h9500303d94dcf0464d420b674f4e3815;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=31");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=31 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h52e887c48d610d4e263ce71abc61f11f || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=31 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h52e887c48d610d4e263ce71abc61f11f || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=31");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=31");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=32");
    numerator=128'h8df4c18611d902464afd003bdfed75aa; denominator=128'hf477a7996d9c4a3bb1e04f81e60475b2;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=32");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=32 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h8df4c18611d902464afd003bdfed75aa || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=32 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h8df4c18611d902464afd003bdfed75aa || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=32");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=32");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=33");
    numerator=128'hde52838c993248b66f1f5571301cc997; denominator=128'ha6c64441b048324f70306adeb89de396;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=33");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=33 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h378c3f4ae8ea1666feeeea92777ee601 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=33 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h378c3f4ae8ea1666feeeea92777ee601 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=33");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=33");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=34");
    numerator=128'hb98f56e0dbb74880a348958f0c1b286b; denominator=128'hff88a3e93cc5c220f4fae2ac204a05a5;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=34");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=34 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'hb98f56e0dbb74880a348958f0c1b286b || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=34 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'hb98f56e0dbb74880a348958f0c1b286b || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=34");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=34");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=35");
    numerator=128'h7685001cf348fb18c5afc7e04fc30123; denominator=128'he1a07161862fa37f014668b7d35127a9;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=35");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=35 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h7685001cf348fb18c5afc7e04fc30123 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=35 latency=129");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h7685001cf348fb18c5afc7e04fc30123 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=35");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=35");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=36");
    numerator=128'hf298e7f03716039971639a650fc25294; denominator=128'ha4015b31617c0aa9e3e9425440b604cf;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=36");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=36 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h4e978cbed599f8ef8d7a5810cf0c4dc5 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=36 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h4e978cbed599f8ef8d7a5810cf0c4dc5 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=36");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=36");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=37");
    numerator=128'ha2538b7d0feb62d354e61894da3fe246; denominator=128'h9ef8f17fd1b6a55d41a66e2fbfada230;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=37");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=37 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h35a99fd3e34bd76133faa651a924016 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=37 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h35a99fd3e34bd76133faa651a924016 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=37");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=37");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=38");
    numerator=128'hce7a2990018522e96a3a6c781e4bbfd6; denominator=128'h1aae3927f1e3776b9032223ae9846808;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=38");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=38 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h7 || remainder!==128'h13b69978644cdef878db7cdbbbace79e || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=38 latency=129");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h7 || remainder!==128'h13b69978644cdef878db7cdbbbace79e || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=38");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=38");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=39");
    numerator=128'h80b9ec6eb955c0308211c238e397480b; denominator=128'h235fb5c416156a5b0caeaf4660277e07;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=39");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=39 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h3 || remainder!==128'h169acb227715811f5c05b465c320cdf6 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=39 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h3 || remainder!==128'h169acb227715811f5c05b465c320cdf6 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=39");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=39");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=40");
    numerator=128'he44da529cd8769ef460c02f9270c6ff7; denominator=128'h9dd821dc076f29959b295ec0fc9bf6e5;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=40");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=40 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h4675834dc6184059aae2a4382a707912 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=40 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h4675834dc6184059aae2a4382a707912 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=40");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=40");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=41");
    numerator=128'h3e922ec0410ac00a6fe3236fca733e3b; denominator=128'hc6e73bab95cbf345226323243552acae;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=41");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=41 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h3e922ec0410ac00a6fe3236fca733e3b || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=41 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h3e922ec0410ac00a6fe3236fca733e3b || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=41");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=41");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=42");
    numerator=128'hc2751bcb9505762ce89cf8fcf04f8833; denominator=128'hb09e28ad09f0a3ca0c9085d1db0a14f4;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=42");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=42 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h1 || remainder!==128'h11d6f31e8b14d262dc0c732b1545733f || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=42 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h1 || remainder!==128'h11d6f31e8b14d262dc0c732b1545733f || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=42");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=42");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=43");
    numerator=128'h640e09ca5393189146f126b0049d019f; denominator=128'hf2a814206dad410f4a602d8a68ade30c;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=43");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=43 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h640e09ca5393189146f126b0049d019f || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=43 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h640e09ca5393189146f126b0049d019f || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=43");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=43");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=44");
    numerator=128'h213464b4f0cb13f670ae982d7854e13f; denominator=128'hac3a3f850a307ea26c0d6ca94fbbf8fe;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=44");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=44 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h213464b4f0cb13f670ae982d7854e13f || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=44 latency=129");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h213464b4f0cb13f670ae982d7854e13f || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=44");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=44");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=45");
    numerator=128'h84234a21f981de35dcfd9b97539bd49b; denominator=128'he3239341197ecb66b13c5a26e00a2bfe;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=45");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=45 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h84234a21f981de35dcfd9b97539bd49b || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=45 latency=129");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h84234a21f981de35dcfd9b97539bd49b || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=45");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=45");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=46");
    numerator=128'h83cdf30b74424d4f7a279d1a6b3647a3; denominator=128'he1615b4f37b66d56f0b19bb6297f1cbb;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=46");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=46 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h83cdf30b74424d4f7a279d1a6b3647a3 || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=46 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h83cdf30b74424d4f7a279d1a6b3647a3 || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=46");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=46");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=47");
    numerator=128'h21eb380dc4c9e7cc2edadc818b4e4fea; denominator=128'h2c3e7c76d068784b42e47623a1bd4c30;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=47");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<129;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=47 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (quotient!==128'h0 || remainder!==128'h21eb380dc4c9e7cc2edadc818b4e4fea || divide_by_zero!==1'b0))
      $fatal(1,"ARITH_RESULT trial=47 latency=129");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (quotient!==128'h0 || remainder!==128'h21eb380dc4c9e7cc2edadc818b4e4fea || divide_by_zero!==1'b0))
        $fatal(1,"ARITH_STALL trial=47");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=47");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk); numerator=128'h21eb380dc4c9e7cc2edadc818b4e4fea; denominator=128'h2c3e7c76d068784b42e47623a1bd4c30; in_valid=1;
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
