module bench;
  anvil_edge_uart_io #(.TX_FIFO_DEPTH(0)) dut();
  initial begin #1; $display("ELABORATION_REACHED"); $finish; end
endmodule
