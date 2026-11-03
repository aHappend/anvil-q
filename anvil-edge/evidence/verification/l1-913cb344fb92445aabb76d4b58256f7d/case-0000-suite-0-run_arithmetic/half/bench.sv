
module bench;
  import anvil_edge_numeric_pkg::*;
  integer file, scanned, count;
  reg [15:0] bits;
  reg invalid;
  reg [31:0] expected;
  initial begin
    count=0;
    file=$fopen("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0000-suite-0-run_arithmetic/half-input/vectors.txt","r");
    if (!file) $fatal(1,"missing independent half vectors");
    while (!$feof(file)) begin
      scanned=$fscanf(file,"%h %h %h\n",bits,invalid,expected);
      if (scanned!=3) $fatal(1,"malformed independent half vector");
      if (f16_invalid(bits)!==invalid)
        $fatal(1,"HALF_CLASS bits=%h",bits);
      if (!invalid && f16_q16(bits)!==expected)
        $fatal(1,"HALF_VALUE bits=%h expected=%h observed=%h",
               bits,expected,f16_q16(bits));
      count=count+1;
    end
    if (count!=65536) $fatal(1,"half coverage count=%0d",count);
    $display("COMPARED %0d",count);
    $finish;
  end
endmodule
