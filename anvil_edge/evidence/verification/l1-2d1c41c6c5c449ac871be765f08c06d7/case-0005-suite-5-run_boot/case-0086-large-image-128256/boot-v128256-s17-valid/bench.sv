
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg start=0,ddr_cal_done=0,spi_miso=0;
  wire spi_mosi,spi_sck,spi_cs_n;
  wire ddr_req_valid,ddr_req_write,ddr_rsp_ready,boot_done,busy,error;
  wire [63:0] ddr_req_addr;
  wire [31:0] ddr_req_wdata;
  wire [3:0] ddr_req_wstrb;
  wire [7:0] error_code;
  reg ddr_req_ready=0,ddr_rsp_valid=0,ddr_rsp_error=0;
  reg [31:0] ddr_rsp_rdata=0;
  wire [223:0] committed_config_words;
  wire [1279:0] committed_segment_bases,committed_segment_bytes;
  wire [1023:0] committed_metadata;
  wire [511:0] committed_table_counts;
  anvil_edge_ddr4_boot_loader #(
    .NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),
    .NUM_Q_HEADS(1),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),
    .VOCAB_SIZE(128256),.MAX_SEQ_LEN(4),.SPI_CLOCK_HALF_PERIOD(1),
    .DDR_BYTES(8388608)
  ) dut(.*);
  reg [7:0] flash[0:8388607],ddr[0:8388607];
  reg [63:0] write_address[0:1604390],segment_base[0:19],segment_length[0:19];
  reg [31:0] write_data[0:1604390];
  reg [3:0] write_strobe[0:1604390];
  reg [31:0] command_shift=0;
  integer spi_command_bits=0,flash_address=0,flash_bit=0,spi_reads=0;
  always @(negedge spi_cs_n) begin
    spi_command_bits=0; command_shift=0; flash_bit=0; spi_miso=0;
  end
  always @(posedge spi_sck) if (!spi_cs_n) begin
    if (spi_command_bits<32) begin
      command_shift={command_shift[30:0],spi_mosi};
      spi_command_bits=spi_command_bits+1;
      if (spi_command_bits==32) begin
        if (command_shift[31:24]!==8'h03 || command_shift[23:0]>=8388608)
          $fatal(1,"BOOT_SPI_COMMAND %h",command_shift);
        flash_address=command_shift[23:0]; spi_reads=spi_reads+1;
      end
    end else begin
      if (flash_bit==7) begin flash_bit=0; flash_address=flash_address+1; end
      else flash_bit=flash_bit+1;
    end
  end
  always @(negedge spi_sck) if (!spi_cs_n && spi_command_bits==32) begin
    if (flash_address>=6418452) spi_miso=1;
    else spi_miso=flash[flash_address][7-flash_bit];
  end
  reg [31:0] rng=17;
  reg pending=0,held=0,loading=1;
  reg [100:0] held_payload;
  reg [63:0] pending_address=0;
  integer cycle=0,writes=0,reads=0,acknowledgements=0,delay_count=0;
  integer request_stalls=0,response_stalls=0,comparisons=0,phase=0;
  function automatic bit readable(input [63:0] address);
    integer k;
    begin
      readable=0;
      for (k=0;k<20;k=k+1)
        if (address>=segment_base[k] &&
            address<segment_base[k]+segment_length[k] && address[1:0]==0)
          readable=1;
    end
  endfunction
  task automatic reset_check;
    begin
      if ({spi_mosi,spi_sck,ddr_req_valid,ddr_req_write,ddr_req_addr,
           ddr_req_wdata,ddr_req_wstrb,ddr_rsp_ready,boot_done,busy,error,error_code,
           committed_config_words,committed_segment_bases,committed_segment_bytes,
           committed_metadata,committed_table_counts}!==4433'd0 || spi_cs_n!==1)
        $fatal(1,"BOOT_RESET t=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n) begin
    rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
    ddr_req_ready=rng[0] && cycle%7!=0;
    if (pending && !ddr_rsp_valid) begin
      if (delay_count==0) begin
        ddr_rsp_valid<=1;
        ddr_rsp_rdata={ddr[pending_address+3],ddr[pending_address+2],
                       ddr[pending_address+1],ddr[pending_address]};
        ddr_rsp_error=0 && acknowledgements==2;
      end else delay_count=delay_count-1;
    end
  end
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n) begin
      if ((^{spi_mosi,spi_sck,spi_cs_n,ddr_req_valid,ddr_req_write,
             ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,ddr_rsp_ready,
             boot_done,busy,error,error_code,committed_config_words,
             committed_segment_bases,committed_segment_bytes,committed_metadata,
             committed_table_counts})===1'bx) $fatal(1,"BOOT_XZ");
      if (!boot_done && {committed_config_words,committed_segment_bases,
          committed_segment_bytes,committed_metadata,committed_table_counts}!==0)
        $fatal(1,"BOOT_PARTIAL_PUBLICATION");
      if (held && (!ddr_req_valid ||
          {ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb}!==held_payload))
        $fatal(1,"BOOT_DDR_STABILITY");
      held=ddr_req_valid && !ddr_req_ready;
      held_payload={ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb};
      if (held) request_stalls=request_stalls+1;
      if (ddr_rsp_valid && !ddr_rsp_ready) response_stalls=response_stalls+1;
      if (ddr_rsp_valid && ddr_rsp_ready) begin
        if (!pending) $fatal(1,"BOOT_ORPHAN_RESPONSE");
        pending=0; acknowledgements=acknowledgements+1; ddr_rsp_valid<=0;
      end
      if (ddr_req_valid && ddr_req_ready) begin
        if (pending || !ddr_cal_done || ddr_req_addr>=8388604)
          $fatal(1,"BOOT_DDR_OUTSTANDING_OR_BOUNDS");
        if (ddr_req_write) begin
          if (!loading || phase!=0 || writes>=1604391 ||
              ddr_req_addr!==write_address[writes] ||
              ddr_req_wstrb!==write_strobe[writes])
            $fatal(1,"BOOT_WRITE_TUPLE item=%0d addr=%h strobe=%h",
                   writes,ddr_req_addr,ddr_req_wstrb);
          for (integer lane=0;lane<4;lane=lane+1) if (ddr_req_wstrb[lane]) begin
            if (ddr_req_wdata[lane*8+:8]!==write_data[writes][lane*8+:8])
              $fatal(1,"BOOT_WRITE_DATA item=%0d expected=%h observed=%h",
                     writes,write_data[writes],ddr_req_wdata);
            ddr[ddr_req_addr+lane]=ddr_req_wdata[lane*8+:8];
          end
          writes=writes+1;
        end else begin
          loading=0;
          if (writes!=1604391 || !readable(ddr_req_addr) || ddr_req_wstrb!==0)
            $fatal(1,"BOOT_VALIDATION_READ address=%h",ddr_req_addr);
          reads=reads+1;
        end
        pending_address=ddr_req_addr; pending=1; delay_count=1+rng[4:2];
        comparisons=comparisons+1;
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic wait_result(input [7:0] code);
    begin
      while (!boot_done && !error) tick();
      if (code==0) begin
        if (error || !boot_done || writes!=1604391 || pending ||
            acknowledgements!=writes+reads || reads==0 || spi_reads<22 ||
            committed_config_words!==224'h1f500000000010000000100000002000000ff00000005 ||
            committed_segment_bases!==1280'h61fc7c000000000061fc5c000000000061fc3c000000000061fc0c000000000061fbdc000000000061fbbc000000000061fb3c000000000061faec000000000061faac000000000061fa8c000000000061fa5c000000000061fa3c000000000061f61c00000000005e0cfc00000000003ebcdc00000000003ebc5c00000000003eb97c000000000000166000000000000010400000000000001000 ||
            committed_segment_bytes!==1280'h20000000000000002000000000000000200000000000000030000000000000003000000000000000200000000000000080000000000000005000000000000000400000000000000020000000000000003000000000000000200000000000000420000000000003e92000000000001f5020000000000000008000000000000002e000000000003ea31c00000000000006200000000000000040 ||
            committed_metadata!==expected_metadata ||
            committed_table_counts!==512'h10000000100000000000000060000000300000002000000000000000100000000000001000003e9000001f50000000000)
          $fatal(1,"BOOT_COMMIT code=%h writes=%0d reads=%0d ack=%0d spi=%0d",
                 error_code,writes,reads,acknowledgements,spi_reads);
      end else begin
        repeat (10) begin
          tick();
          if (error!==1 || error_code!==code || boot_done!==0 || pending ||
              ddr_req_valid!==0 || spi_cs_n!==1)
            $fatal(1,"BOOT_REJECTION expected=%h observed=%h",code,error_code);
        end
      end
      comparisons=comparisons+1;
    end
  endtask
  integer i;
  reg [1023:0] expected_metadata=1024'hbb8302b038e53ae3fec07695bb1bb8269a53ed2bb23a498642e998780970762900001000000000020000000000000020000000020000000000000001000f0100000000ff000000000000000000000000000000000001f5000000000100000001;
  initial begin
    rst_n=0; #0; reset_check();
    for (i=0;i<8388608;i=i+1) begin flash[i]=8'hff; ddr[i]=0; end
    $readmemh("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0005-suite-5-run_boot/case-0086-large-image-128256/boot-v128256-s17-valid-input/flash.hex",flash,0,6418452-1);
    $readmemh("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0005-suite-5-run_boot/case-0086-large-image-128256/boot-v128256-s17-valid-input/address.hex",write_address,0,1604390);
$readmemh("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0005-suite-5-run_boot/case-0086-large-image-128256/boot-v128256-s17-valid-input/data.hex",write_data,0,1604390);
$readmemh("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0005-suite-5-run_boot/case-0086-large-image-128256/boot-v128256-s17-valid-input/strobe.hex",write_strobe,0,1604390);
segment_base[0]=64'h1000; segment_length[0]=64;
segment_base[1]=64'h1040; segment_length[1]=1568;
segment_base[2]=64'h1660; segment_length[2]=4104988;
segment_base[3]=64'h3eb97c; segment_length[3]=736;
segment_base[4]=64'h3ebc5c; segment_length[4]=128;
segment_base[5]=64'h3ebcdc; segment_length[5]=2052128;
segment_base[6]=64'h5e0cfc; segment_length[6]=256288;
segment_base[7]=64'h61f61c; segment_length[7]=1056;
segment_base[8]=64'h61fa3c; segment_length[8]=32;
segment_base[9]=64'h61fa5c; segment_length[9]=48;
segment_base[10]=64'h61fa8c; segment_length[10]=32;
segment_base[11]=64'h61faac; segment_length[11]=64;
segment_base[12]=64'h61faec; segment_length[12]=80;
segment_base[13]=64'h61fb3c; segment_length[13]=128;
segment_base[14]=64'h61fbbc; segment_length[14]=32;
segment_base[15]=64'h61fbdc; segment_length[15]=48;
segment_base[16]=64'h61fc0c; segment_length[16]=48;
segment_base[17]=64'h61fc3c; segment_length[17]=32;
segment_base[18]=64'h61fc5c; segment_length[18]=32;
segment_base[19]=64'h61fc7c; segment_length[19]=32;
    repeat (2) tick(); @(negedge clk); #1; rst_n=1;
    repeat (20) begin
      tick();
      if (spi_cs_n!==1 || ddr_req_valid!==0 || boot_done!==0)
        $fatal(1,"BOOT_DELAYED_CALIBRATION");
    end
    @(negedge clk); #1; ddr_cal_done=1;
    wait_result(8'h00);
    
    $display("BOOT_TRANSACTIONS writes=%0d reads=%0d acknowledgements=%0d",
             writes,reads,acknowledgements);
    $display("COMPARED %0d",comparisons);
    $finish;
  end
  initial begin : bounded_cycles
    reg [63:0] watchdog_cycles;
    watchdog_cycles=0;
    while (watchdog_cycles<64'd1826036160) begin
      @(posedge clk); watchdog_cycles=watchdog_cycles+1'b1;
    end
    $fatal(1,"BOOT_CYCLE_BOUND writes=%0d reads=%0d",writes,reads);
  end
endmodule
