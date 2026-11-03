
module bench;
  reg clk=0;
  reg rst_n;
  reg in_valid=0, out_ready=0;
  reg [8:0] in_data=0;
  wire in_ready,out_valid,empty,full;
  wire [8:0] out_data;
  reg expected_ready,expected_valid,expected_empty,expected_full;
  reg [8:0] expected_data;
  integer file,scanned,count=0;
  always #5 clk=~clk;
  anvil_edge_fifo #(.WIDTH(9),.DEPTH(1)) dut(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(in_ready),
    .in_data(in_data),.out_valid(out_valid),.out_ready(out_ready),
    .out_data(out_data),.empty(empty),.full(full));
  task automatic reset_check;
    begin
      if ({in_ready,out_valid,out_data,empty,full}!==13'd0)
        $fatal(1,"FIFO_RESET time=%0t",$time);
    end
  endtask
  task automatic compare;
    begin
      if ({in_ready,out_valid,out_data,empty,full}!==
          {expected_ready,expected_valid,expected_data,expected_empty,expected_full})
        $fatal(1,"FIFO_QUEUE cycle=%0d expected=%h observed=%h",count,
          {expected_ready,expected_valid,expected_data,expected_empty,expected_full},
          {in_ready,out_valid,out_data,empty,full});
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    rst_n=0; #0; reset_check();
    repeat (2) @(negedge clk);
    file=$fopen("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0001-suite-1-run_fifo/fifo-input-d1-s89/vectors.txt","r");
    if (!file) $fatal(1,"missing independent FIFO vectors");
    while (!$feof(file)) begin
      @(negedge clk); #1;
      scanned=$fscanf(file,"%h %h %h %h %h %h %h %h %h\n",
        rst_n,in_valid,out_ready,in_data,expected_ready,expected_valid,
        expected_data,expected_empty,expected_full);
      if (scanned!=9) $fatal(1,"malformed FIFO vector");
      #1; compare();
      @(posedge clk); compare();
      count=count+1;
    end
    if (count!=1008) $fatal(1,"FIFO_COUNT");
    $display("COMPARED %0d",count);
    $finish;
  end
  initial begin
    repeat (20000) @(posedge clk);
    $fatal(1,"FIFO_CYCLE_BOUND");
  end
endmodule
