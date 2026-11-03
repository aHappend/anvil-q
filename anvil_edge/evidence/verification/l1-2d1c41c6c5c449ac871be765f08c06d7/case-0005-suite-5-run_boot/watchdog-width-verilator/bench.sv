
module bench;
  reg clk=0;
  always #5 clk=~clk;
  integer writes=0,reads=0,comparisons=0;
  initial begin
    repeat (4) begin
      @(posedge clk); #1; comparisons=comparisons+1;
    end
    if (comparisons!=4 || $time!=36) $fatal(1,"WATCHDOG_CLOCK_PROGRESS");
    $display("COMPARED %0d",comparisons); $finish;
  end

  initial begin : bounded_cycles
    reg [63:0] watchdog_cycles;
    watchdog_cycles=0;
    while (watchdog_cycles<64'd3700482320) begin
      @(posedge clk); watchdog_cycles=watchdog_cycles+1'b1;
    end
    $fatal(1,"BOOT_CYCLE_BOUND writes=%0d reads=%0d",writes,reads);
  end

endmodule
