module bench;
  anvil_edge_fifo #(.WIDTH(9),.DEPTH(2)) dut();
  initial begin #1; $display("ELABORATION_REACHED"); $finish; end
endmodule
