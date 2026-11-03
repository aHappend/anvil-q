
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg uart_rx=1,axis_bypass=0;
  wire uart_tx;
  reg [31:0] divisor=5,uart_frame_bytes=0;
  reg s_axis_tvalid=0,s_axis_tlast=0,m_axis_tready=0;
  reg [7:0] s_axis_tdata=0;
  wire s_axis_tready,m_axis_tvalid,m_axis_tlast;
  wire [7:0] m_axis_tdata;
  wire rx_valid,rx_last,tx_ready,framing_error,overflow_error,rx_idle,tx_idle,rx_line_idle;
  reg rx_ready=0,tx_valid=0,tx_last=0,receive_enable=1,response_complete=0;
  wire [7:0] rx_data;
  reg [7:0] tx_data=0;
  anvil_edge_uart_io #(.RX_FIFO_DEPTH(3),.TX_FIFO_DEPTH(3)) dut(.*);
  reg [8:0] expected_rx[0:63],expected_tx[0:63];
  integer nrx=0,ntx=0,rx_count=0,tx_count=0,comparisons=0,cycle=0;
  integer rx_stalls=0,tx_stalls=0,serial_bits=0;
  reg rx_hold=0,tx_hold=0,checking=0,random_ready=1;
  reg [8:0] held_rx,held_tx;
  reg [31:0] rng=17;
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic reset_check;
    begin
      if ({s_axis_tready,m_axis_tvalid,m_axis_tdata,m_axis_tlast,
           rx_valid,rx_data,rx_last,tx_ready,framing_error,overflow_error,
           rx_idle,tx_idle,rx_line_idle}!==28'd0 || uart_tx!==1)
        $fatal(1,"UART_RESET t=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n && random_ready) begin
    rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
    rx_ready=rng[0]; m_axis_tready=rng[1];
  end
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n) begin
      if ((^{uart_tx,s_axis_tready,m_axis_tvalid,m_axis_tdata,m_axis_tlast,
             rx_valid,rx_data,rx_last,tx_ready,framing_error,overflow_error,
             rx_idle,tx_idle,rx_line_idle})===1'bx) $fatal(1,"UART_XZ");
      if (checking) begin
        if (framing_error || overflow_error) $fatal(1,"UART_UNEXPECTED_ERROR");
        if (rx_hold && (!rx_valid || {rx_last,rx_data}!==held_rx))
          $fatal(1,"UART_RX_STABILITY");
        if (tx_hold && (!m_axis_tvalid || {m_axis_tlast,m_axis_tdata}!==held_tx))
          $fatal(1,"UART_AXIS_STABILITY");
        rx_hold=rx_valid && !rx_ready;
        tx_hold=m_axis_tvalid && !m_axis_tready;
        held_rx={rx_last,rx_data}; held_tx={m_axis_tlast,m_axis_tdata};
        if (rx_hold) rx_stalls=rx_stalls+1;
        if (tx_hold) tx_stalls=tx_stalls+1;
        if (rx_valid && rx_ready) begin
          if (rx_count>=nrx || {rx_last,rx_data}!==expected_rx[rx_count])
            $fatal(1,"UART_RX_BYTES item=%0d expected=%h observed=%h",
                   rx_count,expected_rx[rx_count],{rx_last,rx_data});
          rx_count=rx_count+1; comparisons=comparisons+1;
        end
        if (m_axis_tvalid && m_axis_tready) begin
          if (tx_count>=ntx || {m_axis_tlast,m_axis_tdata}!==expected_tx[tx_count])
            $fatal(1,"UART_AXIS_BYTES item=%0d",tx_count);
          tx_count=tx_count+1; comparisons=comparisons+1;
        end
      end
    end else begin rx_hold=0; tx_hold=0; end
  end
  task automatic fresh(input bit bypass,input integer frame_bytes);
    begin
      @(negedge clk); #1; checking=0; rst_n=0; uart_rx=1; tx_valid=0;
      s_axis_tvalid=0; axis_bypass=bypass; uart_frame_bytes=frame_bytes;
      rx_count=0; tx_count=0; nrx=0; ntx=0; random_ready=1;
      repeat (2) tick(); @(negedge clk); #1; rst_n=1;
      repeat (8) tick(); checking=1;
    end
  endtask
  task automatic wire_bit(input bit value);
    begin
      uart_rx=value;
      repeat (5) begin @(negedge clk); #1; end
    end
  endtask
  task automatic serial_byte(input [7:0] value,input bit stop);
    integer b;
    begin
      wire_bit(0);
      for (b=0;b<8;b=b+1) wire_bit(value[b]);
      wire_bit(stop);
    end
  endtask
  task automatic transmit(input [7:0] value,input bit last);
    begin
      @(negedge clk); #1; tx_data=value; tx_last=last; tx_valid=1;
      do begin @(posedge clk); end while (!tx_ready);
      #1; @(negedge clk); #1; tx_valid=0;
    end
  endtask
  task automatic decode_serial(input [7:0] value,input integer period);
    integer b,c;
    reg [9:0] bits;
    begin
      bits={1'b1,value,1'b0};
      while (uart_tx!==0) tick();
      for (b=0;b<10;b=b+1)
        for (c=0;c<period;c=c+1) begin
          if (uart_tx!==bits[b] || tx_idle!==0)
            $fatal(1,"UART_TX_BIT bit=%0d phase=%0d expected=%b observed=%b",
                   b,c,bits[b],uart_tx);
          serial_bits=serial_bits+1;
          tick();
        end
      comparisons=comparisons+1;
    end
  endtask
  task automatic bypass_byte(input [7:0] value,input bit last);
    begin
      @(negedge clk); #1; s_axis_tdata=value; s_axis_tlast=last; s_axis_tvalid=1;
      do begin @(posedge clk); end while (!s_axis_tready);
      #1; @(negedge clk); #1; s_axis_tvalid=0;
    end
  endtask
  integer j;
  initial begin
    rst_n=0; #0; reset_check(); repeat (2) tick();

    fresh(0,1);
    fork
      begin transmit(8'h96,1); end
      begin decode_serial(8'h96,5); end
      begin
        while (uart_tx!==0) tick();
        repeat (5*2) tick();
        @(negedge clk); #1; divisor=8; axis_bypass=1;
        uart_frame_bytes=3;
        repeat (5*5) begin
          tick();
          if (s_axis_tready!==0 || m_axis_tvalid!==0)
            $fatal(1,"UART_MID_TX_TRANSPORT");
        end
        comparisons=comparisons+1;
      end
    join
    while (!tx_idle || !s_axis_tready) tick();
    ntx=1; expected_tx[0]=9'h15a;
    transmit(8'h5a,1);
    while (tx_count!=1) tick();
    if (uart_tx!==1 || serial_bits!=50)
      $fatal(1,"UART_TX_CONTROL_LATCH");
    comparisons=comparisons+1;
    divisor=5;
    fresh(0,2);
    nrx=2; expected_rx[0]=9'h041; expected_rx[1]=9'h142;
    fork
      begin
        @(negedge clk); #1;
        serial_byte(8'h41,1); serial_byte(8'h42,1);
      end
      begin
        while (uart_rx!==0) tick();
        repeat (5*2+4) tick();
        @(negedge clk); #1;
        divisor=8; axis_bypass=1; uart_frame_bytes=1;
        repeat (5*4) begin
          tick();
          if (s_axis_tready!==0) $fatal(1,"UART_MID_RX_TRANSPORT");
        end
        comparisons=comparisons+1;
      end
    join
    while (rx_count!=2 || !s_axis_tready) tick();
    nrx=3; expected_rx[2]=9'h177;
    bypass_byte(8'h77,1);
    while (rx_count!=3) tick();
    comparisons=comparisons+1;
    divisor=5; fresh(0,1); checking=0;
    @(negedge clk); #1; uart_rx=0;
    repeat (1) begin @(negedge clk); #1; end
    uart_rx=1;
    repeat (5*2+10) tick();
    if (framing_error!==1 || overflow_error!==0 || rx_valid!==0)
      $fatal(1,"UART_FALSE_START");
    comparisons=comparisons+1;
    fresh(0,1);
    fork
      begin transmit(8'h00,1); end
      begin
        while (uart_tx!==0) tick();
        repeat (5*3) tick();
        @(negedge clk); #1; rst_n=0; checking=0;
        #0; reset_check();
      end
    join
    fresh(1,0);
    repeat (5*12+10) begin
      tick();
      if (uart_tx!==1 || m_axis_tvalid!==0 || rx_valid!==0 ||
          !tx_idle || framing_error || overflow_error)
        $fatal(1,"UART_RESET_TX_EPOCH");
    end
    comparisons=comparisons+1;
    divisor=5; fresh(0,1);
    @(negedge clk); #1; divisor=8;
    repeat (4) tick();
    j=serial_bits;
    fork
      begin transmit(8'h5a,1); end
      begin decode_serial(8'h5a,8); end
    join
    while (!tx_idle) tick();
    if (serial_bits-j!=80 || framing_error || overflow_error)
      $fatal(1,"UART_UPDATED_BIT_PERIOD");
    comparisons=comparisons+1;
    if (comparisons!=13) $fatal(1,"UART_CONTROL_COMPARISONS %0d",comparisons);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin
    repeat (1000000) @(posedge clk); $fatal(1,"UART_CYCLE_BOUND");
  end
endmodule
