
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg in_valid=0,out_ready=0;
  reg signed [32-1:0] x=0;
  wire a_ready,b_ready,a_valid,b_valid,a_error,b_error;
  wire [31:0] a_value,b_value;
  anvil_edge_silu_q16 original(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(a_ready),.x(x),
    .out_valid(a_valid),.out_ready(out_ready),.value(a_value),.arithmetic_error(a_error));
  lowered_anvil_edge_silu_q16 lowered(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(b_ready),.x(x),
    .out_valid(b_valid),.out_ready(out_ready),.value(b_value),.arithmetic_error(b_error));
  integer comparisons=0,outputs=0,i;
  reg [63:0] rng=64'h123456789abcdef1;
  always @(posedge clk or negedge clk) begin
    if ((^{a_ready,b_ready,a_valid,b_valid,a_error,b_error,a_value,b_value})===1'bx)
      $fatal(1,"LOWERING_XZ");
    if ({a_ready,a_valid,a_error,a_value}!=={b_ready,b_valid,b_error,b_value})
      $fatal(1,"LOWERING_EQUIVALENCE");
    if (!rst_n && {a_ready,a_valid,a_error,a_value,b_ready,b_valid,b_error,b_value}!==0)
      $fatal(1,"LOWERING_RESET");
  end
  always @(posedge clk) if (rst_n && a_valid && out_ready) outputs=outputs+1;
  initial begin
    rst_n=0; #0;
    repeat (2) @(negedge clk);
    rst_n=1;
    for (i=0;i<80;i=i+1) begin
      @(negedge clk); #1;
      rng=rng ^ (rng<<13); rng=rng ^ (rng>>7); rng=rng ^ (rng<<17);
      case (i)
        0: x=0; 1: x=-1; 2: x=-1048576; 3: x=-1048577;
        4: x={1'b1,{(32-1){1'b0}}};
        5: x={1'b0,{(32-1){1'b1}}};
        default: x=rng;
      endcase
      in_valid=1; out_ready=0;
      do begin @(posedge clk); end while (!a_ready);
      #1; @(negedge clk); #1; in_valid=0;
      while (!a_valid) begin @(posedge clk); #1; end
      repeat (4) @(negedge clk);
      out_ready=1; @(posedge clk); #1; comparisons=comparisons+1;
      @(negedge clk); #1; out_ready=0;
    end
    if (outputs!=80 || comparisons!=80) $fatal(1,"LOWERING_COUNTS");
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin repeat (200000) @(posedge clk); $fatal(1,"LOWERING_CYCLE_BOUND"); end
endmodule
