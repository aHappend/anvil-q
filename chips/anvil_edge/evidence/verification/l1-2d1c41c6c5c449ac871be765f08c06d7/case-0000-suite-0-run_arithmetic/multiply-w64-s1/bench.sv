
module bench;
  reg clk=0;
  reg rst_n;
  reg in_valid=0, out_ready=0;
  wire in_ready, out_valid;
  integer cycle, count=0;
  always #5 clk=~clk;
  
  reg signed [63:0] operand_a=0, operand_b=0;
  wire signed [127:0] product;
  anvil_edge_signed_multiplier #(.WIDTH(64)) dut(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(in_ready),
    .operand_a(operand_a),.operand_b(operand_b),
    .out_valid(out_valid),.out_ready(out_ready),.product(product));

  task automatic reset_check;
    begin
      if (in_ready!==0 || out_valid!==0 || (product!==0))
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
    operand_a=64'h8000000000000000; operand_b=64'h8000000000000000;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=0");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=0 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h40000000000000000000000000000000))
      $fatal(1,"ARITH_RESULT trial=0 latency=6");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h40000000000000000000000000000000))
        $fatal(1,"ARITH_STALL trial=0");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=0");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=1");
    operand_a=64'h8000000000000000; operand_b=64'hffffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=1");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=1 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h8000000000000000))
      $fatal(1,"ARITH_RESULT trial=1 latency=6");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h8000000000000000))
        $fatal(1,"ARITH_STALL trial=1");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=1");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=2");
    operand_a=64'h8000000000000000; operand_b=64'h0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=2");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=2 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h0))
      $fatal(1,"ARITH_RESULT trial=2 latency=6");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h0))
        $fatal(1,"ARITH_STALL trial=2");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=2");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=3");
    operand_a=64'h8000000000000000; operand_b=64'h1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=3");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=3 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hffffffffffffffff8000000000000000))
      $fatal(1,"ARITH_RESULT trial=3 latency=6");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hffffffffffffffff8000000000000000))
        $fatal(1,"ARITH_STALL trial=3");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=3");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=4");
    operand_a=64'h8000000000000000; operand_b=64'h7fffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=4");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=4 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hc0000000000000008000000000000000))
      $fatal(1,"ARITH_RESULT trial=4 latency=6");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hc0000000000000008000000000000000))
        $fatal(1,"ARITH_STALL trial=4");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=4");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=5");
    operand_a=64'hffffffffffffffff; operand_b=64'h8000000000000000;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=5");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=5 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h8000000000000000))
      $fatal(1,"ARITH_RESULT trial=5 latency=6");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h8000000000000000))
        $fatal(1,"ARITH_STALL trial=5");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=5");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=6");
    operand_a=64'hffffffffffffffff; operand_b=64'hffffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=6");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=6 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h1))
      $fatal(1,"ARITH_RESULT trial=6 latency=6");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h1))
        $fatal(1,"ARITH_STALL trial=6");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=6");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=7");
    operand_a=64'hffffffffffffffff; operand_b=64'h0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=7");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=7 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h0))
      $fatal(1,"ARITH_RESULT trial=7 latency=6");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h0))
        $fatal(1,"ARITH_STALL trial=7");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=7");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=8");
    operand_a=64'hffffffffffffffff; operand_b=64'h1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=8");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=8 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hffffffffffffffffffffffffffffffff))
      $fatal(1,"ARITH_RESULT trial=8 latency=6");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hffffffffffffffffffffffffffffffff))
        $fatal(1,"ARITH_STALL trial=8");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=8");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=9");
    operand_a=64'hffffffffffffffff; operand_b=64'h7fffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=9");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=9 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hffffffffffffffff8000000000000001))
      $fatal(1,"ARITH_RESULT trial=9 latency=6");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hffffffffffffffff8000000000000001))
        $fatal(1,"ARITH_STALL trial=9");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=9");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=10");
    operand_a=64'h0; operand_b=64'h8000000000000000;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=10");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=10 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h0))
      $fatal(1,"ARITH_RESULT trial=10 latency=6");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h0))
        $fatal(1,"ARITH_STALL trial=10");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=10");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=11");
    operand_a=64'h0; operand_b=64'hffffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=11");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=11 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h0))
      $fatal(1,"ARITH_RESULT trial=11 latency=6");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h0))
        $fatal(1,"ARITH_STALL trial=11");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=11");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=12");
    operand_a=64'h0; operand_b=64'h0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=12");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=12 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h0))
      $fatal(1,"ARITH_RESULT trial=12 latency=6");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h0))
        $fatal(1,"ARITH_STALL trial=12");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=12");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=13");
    operand_a=64'h0; operand_b=64'h1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=13");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=13 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h0))
      $fatal(1,"ARITH_RESULT trial=13 latency=6");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h0))
        $fatal(1,"ARITH_STALL trial=13");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=13");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=14");
    operand_a=64'h0; operand_b=64'h7fffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=14");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=14 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h0))
      $fatal(1,"ARITH_RESULT trial=14 latency=6");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h0))
        $fatal(1,"ARITH_STALL trial=14");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=14");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=15");
    operand_a=64'h1; operand_b=64'h8000000000000000;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=15");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=15 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hffffffffffffffff8000000000000000))
      $fatal(1,"ARITH_RESULT trial=15 latency=6");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hffffffffffffffff8000000000000000))
        $fatal(1,"ARITH_STALL trial=15");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=15");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=16");
    operand_a=64'h1; operand_b=64'hffffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=16");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=16 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hffffffffffffffffffffffffffffffff))
      $fatal(1,"ARITH_RESULT trial=16 latency=6");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hffffffffffffffffffffffffffffffff))
        $fatal(1,"ARITH_STALL trial=16");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=16");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=17");
    operand_a=64'h1; operand_b=64'h0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=17");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=17 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h0))
      $fatal(1,"ARITH_RESULT trial=17 latency=6");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h0))
        $fatal(1,"ARITH_STALL trial=17");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=17");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=18");
    operand_a=64'h1; operand_b=64'h1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=18");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=18 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h1))
      $fatal(1,"ARITH_RESULT trial=18 latency=6");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h1))
        $fatal(1,"ARITH_STALL trial=18");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=18");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=19");
    operand_a=64'h1; operand_b=64'h7fffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=19");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=19 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h7fffffffffffffff))
      $fatal(1,"ARITH_RESULT trial=19 latency=6");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h7fffffffffffffff))
        $fatal(1,"ARITH_STALL trial=19");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=19");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=20");
    operand_a=64'h7fffffffffffffff; operand_b=64'h8000000000000000;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=20");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=20 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hc0000000000000008000000000000000))
      $fatal(1,"ARITH_RESULT trial=20 latency=6");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hc0000000000000008000000000000000))
        $fatal(1,"ARITH_STALL trial=20");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=20");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=21");
    operand_a=64'h7fffffffffffffff; operand_b=64'hffffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=21");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=21 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hffffffffffffffff8000000000000001))
      $fatal(1,"ARITH_RESULT trial=21 latency=6");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hffffffffffffffff8000000000000001))
        $fatal(1,"ARITH_STALL trial=21");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=21");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=22");
    operand_a=64'h7fffffffffffffff; operand_b=64'h0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=22");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=22 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h0))
      $fatal(1,"ARITH_RESULT trial=22 latency=6");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h0))
        $fatal(1,"ARITH_STALL trial=22");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=22");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=23");
    operand_a=64'h7fffffffffffffff; operand_b=64'h1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=23");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=23 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h7fffffffffffffff))
      $fatal(1,"ARITH_RESULT trial=23 latency=6");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h7fffffffffffffff))
        $fatal(1,"ARITH_STALL trial=23");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=23");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=24");
    operand_a=64'h7fffffffffffffff; operand_b=64'h7fffffffffffffff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=24");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=24 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h3fffffffffffffff0000000000000001))
      $fatal(1,"ARITH_RESULT trial=24 latency=6");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h3fffffffffffffff0000000000000001))
        $fatal(1,"ARITH_STALL trial=24");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=24");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=25");
    operand_a=64'h4386bbc4cd613e30; operand_b=64'h9e2feb89414c343c;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=25");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=25 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'he6330ffc0533ef5a203afd3089ac5340))
      $fatal(1,"ARITH_RESULT trial=25 latency=6");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'he6330ffc0533ef5a203afd3089ac5340))
        $fatal(1,"ARITH_STALL trial=25");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=25");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=26");
    operand_a=64'hf311d8a3c2ce6f44; operand_b=64'h98072e8c35bf992d;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=26");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=26 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h5406320854f616ef9df1a74b68532f4))
      $fatal(1,"ARITH_RESULT trial=26 latency=6");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h5406320854f616ef9df1a74b68532f4))
        $fatal(1,"ARITH_STALL trial=26");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=26");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=27");
    operand_a=64'h44647159c324c985; operand_b=64'hf204e52db2221a58;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=27");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=27 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hfc43d098eb5f35164374f90f0ec6c7b8))
      $fatal(1,"ARITH_RESULT trial=27 latency=6");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hfc43d098eb5f35164374f90f0ec6c7b8))
        $fatal(1,"ARITH_STALL trial=27");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=27");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=28");
    operand_a=64'h4d447e35b8b6d8fe; operand_b=64'h71fd42a29755d4c1;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=28");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=28 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h2267ac832d2f4881299e9ee78be1ef7e))
      $fatal(1,"ARITH_RESULT trial=28 latency=6");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h2267ac832d2f4881299e9ee78be1ef7e))
        $fatal(1,"ARITH_STALL trial=28");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=28");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=29");
    operand_a=64'hd1431193e6c3f339; operand_b=64'h78130c4237730edf;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=29");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=29 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hea13f5fab023d8b1138d8a6e3d98fca7))
      $fatal(1,"ARITH_RESULT trial=29 latency=6");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hea13f5fab023d8b1138d8a6e3d98fca7))
        $fatal(1,"ARITH_STALL trial=29");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=29");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=30");
    operand_a=64'h4381e88f38c0c8fd; operand_b=64'hd87fd2803bab6c39;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=30");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=30 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hf595689e5fa4f14fe28f936d87b67c55))
      $fatal(1,"ARITH_RESULT trial=30 latency=6");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hf595689e5fa4f14fe28f936d87b67c55))
        $fatal(1,"ARITH_STALL trial=30");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=30");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=31");
    operand_a=64'h73c64af775a89294; operand_b=64'h85805975ed2f89d9;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=31");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=31 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hc899c595db273402ab901503df817374))
      $fatal(1,"ARITH_RESULT trial=31 latency=6");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hc899c595db273402ab901503df817374))
        $fatal(1,"ARITH_STALL trial=31");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=31");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=32");
    operand_a=64'h246d6753ec148cb4; operand_b=64'h5c2574bdb94067ed;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=32");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=32 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hd1ca58ea9ec0b46d962bc6314a2aea4))
      $fatal(1,"ARITH_RESULT trial=32 latency=6");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hd1ca58ea9ec0b46d962bc6314a2aea4))
        $fatal(1,"ARITH_STALL trial=32");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=32");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=33");
    operand_a=64'h3e3edc0a1ef2a4f0; operand_b=64'hcda98f1d3099fdf5;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=33");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=33 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hf3c2b475745de65537875366fea909b0))
      $fatal(1,"ARITH_RESULT trial=33 latency=6");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hf3c2b475745de65537875366fea909b0))
        $fatal(1,"ARITH_STALL trial=33");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=33");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=34");
    operand_a=64'h88d6af57da711448; operand_b=64'h3cfbb050acab1a6b;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=34");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=34 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'he39d29848d99782be9dcef90b56aca18))
      $fatal(1,"ARITH_RESULT trial=34 latency=6");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'he39d29848d99782be9dcef90b56aca18))
        $fatal(1,"ARITH_STALL trial=34");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=34");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=35");
    operand_a=64'hdeda92d864ac5db9; operand_b=64'h87923986bb968a43;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=35");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=35 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hf97c1ccb0a5291f584b3a325108416b))
      $fatal(1,"ARITH_RESULT trial=35 latency=6");
    repeat (5) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hf97c1ccb0a5291f584b3a325108416b))
        $fatal(1,"ARITH_STALL trial=35");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=35");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=36");
    operand_a=64'h1403560d97dae38d; operand_b=64'hab9c014ea5ac06d8;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=36");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=36 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hf9671690162abace8357eab805c14cf8))
      $fatal(1,"ARITH_RESULT trial=36 latency=6");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hf9671690162abace8357eab805c14cf8))
        $fatal(1,"ARITH_STALL trial=36");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=36");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=37");
    operand_a=64'h4541013d0326324d; operand_b=64'hbb6fe5078c5fe8f8;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=37");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=37 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hed73bfcf48772d5022e2cdbf71298298))
      $fatal(1,"ARITH_RESULT trial=37 latency=6");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hed73bfcf48772d5022e2cdbf71298298))
        $fatal(1,"ARITH_STALL trial=37");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=37");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=38");
    operand_a=64'h13ea5c4ed8f33418; operand_b=64'h68e5b4617589a82b;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=38");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=38 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h829142cf8841ad3228a1dabe3e18008))
      $fatal(1,"ARITH_RESULT trial=38 latency=6");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h829142cf8841ad3228a1dabe3e18008))
        $fatal(1,"ARITH_STALL trial=38");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=38");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=39");
    operand_a=64'h3ab9f87ff5059285; operand_b=64'hfb5262cc7038069;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=39");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=39 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h39a73ce1254a2b1c73c07d0631a988d))
      $fatal(1,"ARITH_RESULT trial=39 latency=6");
    repeat (7) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h39a73ce1254a2b1c73c07d0631a988d))
        $fatal(1,"ARITH_STALL trial=39");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=39");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=40");
    operand_a=64'h7320cd576d14475b; operand_b=64'h5eb8fc4c7b297d0b;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=40");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=40 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h2a993c7060264940e6c07c90bd497fe9))
      $fatal(1,"ARITH_RESULT trial=40 latency=6");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h2a993c7060264940e6c07c90bd497fe9))
        $fatal(1,"ARITH_STALL trial=40");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=40");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=41");
    operand_a=64'hded3c9691eb79fa; operand_b=64'h1355c53f0e642f4;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=41");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=41 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h10d45ff489d21231c0d119c07eb648))
      $fatal(1,"ARITH_RESULT trial=41 latency=6");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h10d45ff489d21231c0d119c07eb648))
        $fatal(1,"ARITH_STALL trial=41");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=41");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=42");
    operand_a=64'h5037cdff7c240d49; operand_b=64'hd89890086a17b9af;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=42");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=42 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hf3a716146b28c3a31950016155cdd5e7))
      $fatal(1,"ARITH_RESULT trial=42 latency=6");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hf3a716146b28c3a31950016155cdd5e7))
        $fatal(1,"ARITH_STALL trial=42");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=42");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=43");
    operand_a=64'h1cc9af4ec9546b43; operand_b=64'h19901c0475491bc3;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=43");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=43 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h2dfe6b7dd7e3ef77455d76377b8c509))
      $fatal(1,"ARITH_RESULT trial=43 latency=6");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h2dfe6b7dd7e3ef77455d76377b8c509))
        $fatal(1,"ARITH_STALL trial=43");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=43");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=44");
    operand_a=64'h5c6b13ab2e47dc0e; operand_b=64'h2c512b01f18dd1ee;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=44");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=44 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hfffb4c9550ad3479b2163b9132c0304))
      $fatal(1,"ARITH_RESULT trial=44 latency=6");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hfffb4c9550ad3479b2163b9132c0304))
        $fatal(1,"ARITH_STALL trial=44");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=44");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=45");
    operand_a=64'h5e3a5db5154ed512; operand_b=64'hc7fc816ac16e2284;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=45");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=45 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'heb61f239a118034e6724402994ae4148))
      $fatal(1,"ARITH_RESULT trial=45 latency=6");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'heb61f239a118034e6724402994ae4148))
        $fatal(1,"ARITH_STALL trial=45");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=45");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=46");
    operand_a=64'haf429ce59ff3078f; operand_b=64'h91cbc2884a5012dc;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=46");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=46 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h22c1da705894d2dbd68098ae3e128ce4))
      $fatal(1,"ARITH_RESULT trial=46 latency=6");
    repeat (3) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h22c1da705894d2dbd68098ae3e128ce4))
        $fatal(1,"ARITH_STALL trial=46");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=46");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=47");
    operand_a=64'hff1a355e526eb523; operand_b=64'h860cea631d3b993f;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=47");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=47 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h6d76f928f3b83d4f72160c29917e9d))
      $fatal(1,"ARITH_RESULT trial=47 latency=6");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h6d76f928f3b83d4f72160c29917e9d))
        $fatal(1,"ARITH_STALL trial=47");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=47");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=48");
    operand_a=64'hd7e54acc62f5680c; operand_b=64'hb023580ccbd3f5e0;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=48");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=48 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hc82cf2e2b8c386a8b0e37e1b9328680))
      $fatal(1,"ARITH_RESULT trial=48 latency=6");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hc82cf2e2b8c386a8b0e37e1b9328680))
        $fatal(1,"ARITH_STALL trial=48");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=48");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=49");
    operand_a=64'hb9b21c95055455e8; operand_b=64'ha57e845465b675cd;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=49");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=49 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h18daf129c1b3062b43e4debe6abbd2c8))
      $fatal(1,"ARITH_RESULT trial=49 latency=6");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h18daf129c1b3062b43e4debe6abbd2c8))
        $fatal(1,"ARITH_STALL trial=49");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=49");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=50");
    operand_a=64'h75bb9188b80599e9; operand_b=64'h43fdda7b1eedaff;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=50");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=50 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h1f44d5eff58df8d39f7e4824242b917))
      $fatal(1,"ARITH_RESULT trial=50 latency=6");
    repeat (6) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h1f44d5eff58df8d39f7e4824242b917))
        $fatal(1,"ARITH_STALL trial=50");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=50");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=51");
    operand_a=64'h4daaac43936aa40c; operand_b=64'h2185cc8ea8ea37f7;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=51");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=51 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'ha2b97ef7e4ccc89ef4e03a8f81adb94))
      $fatal(1,"ARITH_RESULT trial=51 latency=6");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'ha2b97ef7e4ccc89ef4e03a8f81adb94))
        $fatal(1,"ARITH_STALL trial=51");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=51");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=52");
    operand_a=64'h3cc99ae80f0c8a89; operand_b=64'h77c882f4202cc828;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=52");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=52 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h1c71539b3cbfe88f429f441115bcad68))
      $fatal(1,"ARITH_RESULT trial=52 latency=6");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h1c71539b3cbfe88f429f441115bcad68))
        $fatal(1,"ARITH_STALL trial=52");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=52");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=53");
    operand_a=64'h8c250a03e023033d; operand_b=64'h5bc799b0121b2800;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=53");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=53 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'hd676d5cc9df1317f562863e119f08800))
      $fatal(1,"ARITH_RESULT trial=53 latency=6");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'hd676d5cc9df1317f562863e119f08800))
        $fatal(1,"ARITH_STALL trial=53");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=53");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=54");
    operand_a=64'h3e6c6fe94c41d9c0; operand_b=64'h109ff4976a8a43ef;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=54");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=54 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h40dc7fc5d457728927f59ac4ef78a40))
      $fatal(1,"ARITH_RESULT trial=54 latency=6");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h40dc7fc5d457728927f59ac4ef78a40))
        $fatal(1,"ARITH_STALL trial=54");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=54");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=55");
    operand_a=64'h59bc1d97e0f3a7ef; operand_b=64'h51c51f86973082d6;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=55");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=55 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h1ca99e2cc9190bf6c73c9b093cc5bfca))
      $fatal(1,"ARITH_RESULT trial=55 latency=6");
    repeat (2) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h1ca99e2cc9190bf6c73c9b093cc5bfca))
        $fatal(1,"ARITH_STALL trial=55");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=55");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial=56");
    operand_a=64'h8994940e82458cc8; operand_b=64'hd8d07674334de73d;
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial=56");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<6;cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial=56 cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || (product!==128'h12205acac345515a7f396398fcc303a8))
      $fatal(1,"ARITH_RESULT trial=56 latency=6");
    repeat (4) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || (product!==128'h12205acac345515a7f396398fcc303a8))
        $fatal(1,"ARITH_STALL trial=56");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial=56");
    @(negedge clk); out_ready=0;
    count=count+1;

    @(negedge clk); operand_a=64'h8994940e82458cc8; operand_b=64'hd8d07674334de73d; in_valid=1;
    @(posedge clk);
    @(negedge clk); #1; in_valid=0; rst_n=0;
    #1; reset_check();
    repeat (2) @(negedge clk);
    rst_n=1;
    repeat (9) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_RESET_STALE");
    end
    if (count!=57) $fatal(1,"ARITH_COUNT");
    $display("COMPARED %0d",count);
    $finish;
  end
  initial begin
    repeat (100000) @(posedge clk);
    $fatal(1,"ARITH_CYCLE_BOUND");
  end
endmodule
