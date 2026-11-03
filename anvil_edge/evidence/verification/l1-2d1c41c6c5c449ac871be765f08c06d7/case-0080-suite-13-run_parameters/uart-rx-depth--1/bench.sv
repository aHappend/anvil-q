module bench;
  anvil_edge_uart_io #(.RX_FIFO_DEPTH(-1)) dut();
  initial begin #1; $display("ELABORATION_REACHED"); $finish; end
endmodule
