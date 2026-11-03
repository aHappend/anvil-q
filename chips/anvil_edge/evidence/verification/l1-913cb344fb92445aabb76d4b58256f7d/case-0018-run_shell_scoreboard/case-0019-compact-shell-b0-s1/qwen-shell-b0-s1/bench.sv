
module bench;
  reg clk=0,rst_n;
  always #5 clk=~clk;
  reg ddr_cal_done=0,spi_miso=0,uart_rx=1;
  reg s_axis_tvalid=0,s_axis_tlast=0,m_axis_tready=0;
  reg [7:0] s_axis_tdata=0;
  wire uart_tx,s_axis_tready,m_axis_tvalid,m_axis_tlast;
  wire [7:0] m_axis_tdata;
  wire spi_mosi,spi_sck,spi_cs_n;
  wire ddr_req_valid,ddr_req_write,ddr_rsp_ready,boot_done,busy,done,error;
  wire [63:0] ddr_req_addr;
  wire [31:0] ddr_req_wdata;
  wire [3:0] ddr_req_wstrb;
  wire [7:0] error_code;
  reg ddr_req_ready=0,ddr_rsp_valid=0,ddr_rsp_error=0;
  reg [31:0] ddr_rsp_rdata=0;
  reg cfg_valid=0,cfg_write=0,cfg_rsp_ready=0;
  reg [31:0] cfg_addr=0,cfg_wdata=0;
  wire cfg_ready,cfg_rsp_valid,cfg_rsp_error;
  wire [31:0] cfg_rdata;
  anvil_edge_top #(
    .NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),
    .NUM_Q_HEADS(1),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),
    .VOCAB_SIZE(257),.MAX_SEQ_LEN(64),.SPI_CLOCK_HALF_PERIOD(1),
    .MAX_PROMPT_BYTES(4096),.MAX_PROMPT_TOKENS(4096),
    .RX_FIFO_DEPTH(16),.TX_FIFO_DEPTH(3),.DDR_BYTES(32768)
  ) dut(.*);
  localparam EXTENT=32768,FRAMES=2;
  integer BYPASS;
  initial begin
    if (!$value$plusargs("verification_bypass=%d",BYPASS) ||
        (BYPASS!=0 && BYPASS!=1)) $fatal(1,"QWEN_SHELL_INVALID_TRANSPORT");
  end
  reg [7:0] flash[0:EXTENT-1];
  reg [31:0] ddr[0:EXTENT/4-1];
  reg [63:0] segment_base[0:19];
  integer segment_length[0:19],segment_flash[0:19];
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
        if (command_shift[31:24]!==8'h03 || command_shift[23:0]>=EXTENT)
          $fatal(1,"BOOT_SPI_COMMAND %h",command_shift);
        flash_address=command_shift[23:0]; spi_reads=spi_reads+1;
      end
    end else begin
      if (flash_bit==7) begin flash_bit=0; flash_address=flash_address+1; end
      else flash_bit=flash_bit+1;
    end
  end
  always @(negedge spi_sck) if (!spi_cs_n && spi_command_bits==32) begin
    if (flash_address>=24280) spi_miso=1;
    else spi_miso=flash[flash_address][7-flash_bit];
  end

  reg [31:0] rng=1;
  reg pending=0,held=0,running=0,out_held=0,loading=1;
  reg [100:0] held_payload;
  reg [8:0] held_output;
  reg [63:0] pending_address=0;
  integer delay_count=0,writes=0,reads=0,acknowledgements=0;
  integer boot_segment=0,boot_offset=0,request_stalls=0,output_stalls=0;
  integer comparisons=0,frame=0,outputs=0,completions=0,reloads=0;
  integer frame_done=0,input_count=0,embedding_reads=0,activation_writes=0;
  integer total_activation_writes=0,prompt_count=0,matched_write=-1,active_operation=-1;
  integer operation_index=0,embedding_index=0,inference_reads=0;
  reg [31:0] input_bytes[0:4095],expected_tokens[0:63],output_bytes[0:4095];
  reg [63:0] operation_cycles[0:63];
  reg [63:0] expected_write_address[0:65535];
  reg [31:0] expected_write_data[0:65535];
  reg [31:0] expected_write_operation[0:65535];
  integer expected_write_next[0:65535];
  integer write_head[bit [95:0]];
  reg write_seen[0:65535];
  integer scoreboard_fault=0;
  reg fault_injected=0;
  integer input_length=0,output_length=0,operation_count=0,write_count=0;
  reg [63:0] cycles=0;
  reg [63:0] next_progress=64'd16777216;
  integer observed_input=0,observed_output=0;
  reg final_head_pending=0,input_finished=0;
  function automatic bit within_segment(input [63:0] address);
    begin
      within_segment=0;
      for (integer k=0;k<20;k=k+1)
        if (address>=segment_base[k] &&
            address<segment_base[k]+segment_length[k] && address[1:0]==0)
          within_segment=1;
    end
  endfunction
  task automatic reset_check;
    begin
      if ({spi_mosi,spi_sck,ddr_req_valid,ddr_req_write,ddr_req_addr,
           ddr_req_wdata,ddr_req_wstrb,ddr_rsp_ready,boot_done,busy,error,error_code,
           done,s_axis_tready,m_axis_tvalid,m_axis_tdata,m_axis_tlast,
           cfg_ready,cfg_rsp_valid,cfg_rsp_error,cfg_rdata}!==0 ||
          spi_cs_n!==1 || uart_tx!==1) $fatal(1,"QWEN_SHELL_RESET");
    end
  endtask
  task automatic check_write(input [63:0] address,input [31:0] value,
                            input [3:0] strobe,input integer operation);
    reg [95:0] key;
    begin
      key={32'(operation),address};
      matched_write=write_head.exists(key) ? write_head[key] : -1;
      if (matched_write<0 || activation_writes>=write_count || strobe!==4'hf)
        $fatal(1,"QWEN_SHELL_UNEXPECTED_WRITE frame=%0d op=%0d address=%h",
               frame,operation,address);
      if (write_seen[matched_write] || address!==expected_write_address[matched_write] ||
          operation!=expected_write_operation[matched_write])
        $fatal(1,"QWEN_SHELL_WRITE_INDEX");
      if (value!==expected_write_data[matched_write])
        $fatal(1,"QWEN_SHELL_NUMERICAL_WRITE frame=%0d item=%0d address=%h got=%h expected=%h",
               frame,matched_write,address,value,expected_write_data[matched_write]);
      write_seen[matched_write]=1;
      write_head[key]=expected_write_next[matched_write];
      activation_writes=activation_writes+1;
      total_activation_writes=total_activation_writes+1;
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n) begin
    rng=rng^(rng<<13); rng=rng^(rng>>17); rng=rng^(rng<<5);
    ddr_req_ready=rng[0] || rng[1];
    m_axis_tready=rng[2] && rng[3];
    if (pending && !ddr_rsp_valid) begin
      if (delay_count==0) begin
        ddr_rsp_valid<=1;
        ddr_rsp_rdata=ddr[pending_address>>2];
      end else delay_count=delay_count-1;
    end
  end
  always @(posedge clk) begin
    cycles=cycles+1;
    if (cycles>=64'd29004856000)
      $fatal(1,"QWEN_SHELL_CYCLE_BOUND frame=%0d embedding=%0d writes=%0d",
             frame,embedding_reads,activation_writes);
    if (rst_n) begin
      if ((^{spi_mosi,spi_sck,spi_cs_n,ddr_req_valid,ddr_req_write,
             ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,ddr_rsp_ready,
             boot_done,busy,done,error,error_code,uart_tx,s_axis_tready,
             m_axis_tvalid,m_axis_tlast,m_axis_tdata,cfg_ready,cfg_rsp_valid,
             cfg_rsp_error,cfg_rdata})===1'bx) $fatal(1,"QWEN_SHELL_XZ");
      if (error) $fatal(1,"QWEN_SHELL_ERROR frame=%0d code=%h cycles=%0d embedding=%0d activation=%0d outputs=%0d",
                           frame,error_code,cycles,embedding_reads,activation_writes,outputs);
      if (held && (!ddr_req_valid ||
          {ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb}!==held_payload))
        $fatal(1,"QWEN_SHELL_REQUEST_STABILITY");
      held=ddr_req_valid && !ddr_req_ready;
      held_payload={ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb};
      if (held) request_stalls=request_stalls+1;
      if (ddr_rsp_valid && ddr_rsp_ready) begin
        if (!pending) $fatal(1,"QWEN_SHELL_ORPHAN_RESPONSE");
        if (final_head_pending) begin
          $display("QWEN_SHELL_PHASE phase=head_ack frame=%0d operation=%0d cycles=%0d",
                   frame,operation_index,cycles);
          $fflush();
          final_head_pending=0;
        end
        pending=0; ddr_rsp_valid<=0; acknowledgements=acknowledgements+1;
      end
      if (ddr_req_valid && ddr_req_ready) begin
        if (pending || !ddr_cal_done || ddr_req_addr>=EXTENT ||
            ddr_req_addr[1:0]!==0 || !within_segment(ddr_req_addr))
          $fatal(1,"QWEN_SHELL_DDR_PROTOCOL address=%h",ddr_req_addr);
        if (ddr_req_write) begin
          if (!running) begin
            if (!loading || boot_segment>=20 ||
                ddr_req_addr!==segment_base[boot_segment]+boot_offset ||
                ddr_req_wstrb!==((segment_length[boot_segment]-boot_offset>=4) ?
                                 4'hf : (4'h1<<(segment_length[boot_segment]-boot_offset))-1))
              $fatal(1,"QWEN_SHELL_BOOT_WRITE_ORDER segment=%0d offset=%0d",
                     boot_segment,boot_offset);
            for (integer lane=0;lane<4;lane=lane+1) if (ddr_req_wstrb[lane]) begin
              if (ddr_req_wdata[lane*8+:8]!==
                  flash[segment_flash[boot_segment]+boot_offset+lane])
                $fatal(1,"QWEN_SHELL_BOOT_SOURCE_BYTE");
              ddr[ddr_req_addr>>2][lane*8+:8]=ddr_req_wdata[lane*8+:8];
            end
            boot_offset=boot_offset+4; writes=writes+1;
            if (boot_offset>=segment_length[boot_segment]) begin
              $display("QWEN_SHELL_BOOT_SEGMENT segment=%0d cycles=%0d",
                       boot_segment,cycles);
              $fflush();
              boot_segment=boot_segment+1; boot_offset=0;
            end
          end else begin
            active_operation=(embedding_reads-1)/2064;
            if (scoreboard_fault==3 && !fault_injected && activation_writes==write_count-1) begin
              fault_injected=1;
              $display("SCOREBOARD_INJECT missing address=%h",ddr_req_addr);
            end else begin
              if (scoreboard_fault==1 && !fault_injected) begin
                fault_injected=1;
                $display("SCOREBOARD_INJECT wrong-value address=%h",ddr_req_addr);
                check_write(ddr_req_addr,ddr_req_wdata^32'd1,ddr_req_wstrb,active_operation);
              end else check_write(ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,active_operation);
              if (scoreboard_fault==2 && !fault_injected &&
                  expected_write_next[matched_write]<0) begin
                fault_injected=1;
                $display("SCOREBOARD_INJECT duplicate address=%h",ddr_req_addr);
                check_write(ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,active_operation);
              end
            end
            ddr[ddr_req_addr>>2]=ddr_req_wdata;
          end
        end else begin
          if (ddr_req_wstrb!==0 || boot_segment!=20)
            $fatal(1,"QWEN_SHELL_READ_BEFORE_BOOT_WRITES");
          loading=0; reads=reads+1;
          if (running) begin
            inference_reads=inference_reads+1;
            if (ddr_req_addr>=segment_base[2] &&
                ddr_req_addr<segment_base[2]+64'd8224) begin
              if (input_count!=input_length) $fatal(1,"QWEN_SHELL_PARTIAL_PREFILL");
              operation_index=embedding_reads/2064;
              embedding_index=embedding_reads%2064;
              if (operation_index>=operation_count)
                $fatal(1,"QWEN_SHELL_EXTRA_CORE_OPERATION");
              if (embedding_index<8) begin
                if (ddr_req_addr!==segment_base[2]+
                    64'd32*expected_tokens[operation_index]+4*embedding_index)
                  $fatal(1,"QWEN_SHELL_PREFILL_FEEDBACK frame=%0d op=%0d token=%0d address=%h",
                         frame,operation_index,expected_tokens[operation_index],ddr_req_addr);
                if (embedding_index==0) begin
                  operation_cycles[operation_index]=cycles;
                  $display("QWEN_SHELL_PHASE phase=core_begin frame=%0d operation=%0d cycles=%0d",
                           frame,operation_index,cycles);
                  $fflush();
                end
              end else if (ddr_req_addr!==segment_base[2]+4*(embedding_index-8))
                $fatal(1,"QWEN_SHELL_HEAD_FRAME_ORDER");
              if (embedding_index==8) begin
                $display("QWEN_SHELL_PHASE phase=head_begin frame=%0d operation=%0d cycles=%0d",
                         frame,operation_index,cycles);
                $fflush();
              end
              if (embedding_index==2064-1)
                final_head_pending=1;
              embedding_reads=embedding_reads+1;
            end
          end
        end
        pending_address=ddr_req_addr; pending=1; delay_count=rng[5:4];
        comparisons=comparisons+1;
      end
      if (running) begin
        if (input_finished && observed_input==0) begin
          observed_input=1;
          $display("QWEN_SHELL_PHASE phase=input_sent frame=%0d cycles=%0d",
                   frame,cycles);
          $fflush();
        end
        if (outputs!=observed_output) begin
          if (observed_output==0 || outputs==output_length) begin
            $display("QWEN_SHELL_PHASE phase=output_progress frame=%0d bytes=%0d cycles=%0d",
                     frame,outputs,cycles);
            $fflush();
          end
          observed_output=outputs;
        end
        if (cfg_valid || cfg_write || !boot_done || !spi_cs_n)
          $fatal(1,"QWEN_SHELL_HOST_INTERVENTION_OR_BOOT_REENTRY");
        if (out_held && (!m_axis_tvalid || {m_axis_tlast,m_axis_tdata}!==held_output))
          $fatal(1,"QWEN_SHELL_OUTPUT_STABILITY");
        out_held=m_axis_tvalid && !m_axis_tready;
        held_output={m_axis_tlast,m_axis_tdata};
        if (out_held) output_stalls=output_stalls+1;
        if (!BYPASS && m_axis_tvalid) $fatal(1,"QWEN_SHELL_UNSELECTED_OUTPUT");
        if (BYPASS && m_axis_tvalid && m_axis_tready) begin
          if (embedding_reads<prompt_count*2064)
            $fatal(1,"QWEN_SHELL_INTERMEDIATE_PREFILL_OUTPUT");
          if (outputs>=output_length || m_axis_tdata!==output_bytes[outputs][7:0] ||
              m_axis_tlast!==(outputs==output_length-1))
            $fatal(1,"QWEN_SHELL_OUTPUT_BYTE frame=%0d item=%0d got=%h expected=%h",
                   frame,outputs,m_axis_tdata,output_bytes[outputs]);
          outputs=outputs+1; comparisons=comparisons+1;
        end
        if (s_axis_tvalid && s_axis_tready) begin
          if (!BYPASS || input_count>=input_length ||
              s_axis_tdata!==input_bytes[input_count][7:0] ||
              s_axis_tlast!==(input_count==input_length-1))
            $fatal(1,"QWEN_SHELL_INPUT_BINDING");
          input_count=input_count+1;
        end
        if (done) begin
          if (frame_done!=0 || outputs!=output_length || pending || ddr_req_valid ||
              m_axis_tvalid || uart_tx!==1 || activation_writes!=write_count ||
              embedding_reads!=operation_count*2064 ||
              acknowledgements!=writes+reads+total_activation_writes)
            $fatal(1,"QWEN_SHELL_DRAIN frame=%0d output=%0d writes=%0d embedding=%0d",
                   frame,outputs,activation_writes,embedding_reads);
          for (integer item=0;item<write_count;item=item+1)
            if (!write_seen[item]) $fatal(1,"QWEN_SHELL_MISSING_WRITE item=%0d",item);
          frame_done=frame_done+1; completions=completions+1; comparisons=comparisons+1;
          $display("QWEN_SHELL_COMPLETION frame=%0d cycles=%0d",frame,cycles);
          $fflush();
        end
      end
      if (cycles>=next_progress) begin
        $display("QWEN_SHELL_PROGRESS frame=%0d running=%0d input=%0d embedding=%0d activation=%0d output=%0d reads=%0d acknowledgements=%0d cycles=%0d",
                 frame,running,input_count,embedding_reads,activation_writes,outputs,
                 reads,acknowledgements,cycles);
        $fflush();
        next_progress=next_progress+64'd16777216;
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic send_axis(input [7:0] value,input bit last);
    begin
      @(negedge clk); #1; s_axis_tvalid=1; s_axis_tdata=value; s_axis_tlast=last;
      do begin @(posedge clk); end while (!s_axis_tready);
      #1; @(negedge clk); #1; s_axis_tvalid=0;
    end
  endtask
  task automatic serial_bit(input bit value);
    begin uart_rx=value; repeat (5) begin @(negedge clk); #1; end end
  endtask
  task automatic send_serial(input [7:0] value);
    begin
      serial_bit(0);
      for (integer bit_index=0;bit_index<8;bit_index=bit_index+1)
        serial_bit(value[bit_index]);
      serial_bit(1);
    end
  endtask
  task automatic decode_serial;
    reg [9:0] expected_frame;
    begin
      while (outputs<output_length) begin
        expected_frame={1'b1,output_bytes[outputs][7:0],1'b0};
        wait (uart_tx===0); #1;
        if (embedding_reads<prompt_count*2064)
          $fatal(1,"QWEN_SHELL_UART_INTERMEDIATE_PREFILL_OUTPUT");
        for (integer bit_index=0;bit_index<10;bit_index=bit_index+1)
          repeat (5) begin
            if (uart_tx!==expected_frame[bit_index] || done!==0)
              $fatal(1,"QWEN_SHELL_UART_BIT frame=%0d byte=%0d bit=%0d",
                     frame,outputs,bit_index);
            tick();
          end
        outputs=outputs+1; comparisons=comparisons+1;
      end
    end
  endtask
  task automatic wait_boot;
    begin
      wait (boot_done);
      @(negedge clk); #1;
      wait (!busy);
      if (boot_segment!=20 || pending || ddr_rsp_valid || loading ||
          writes!=5848 || reads==0 || spi_reads<22 ||
          acknowledgements!=writes+reads)
        $fatal(1,"QWEN_SHELL_BOOT_CONSERVATION");
      $display("QWEN_SHELL_BOOT writes=%0d reads=%0d acknowledgements=%0d cycles=%0d",
               writes,reads,acknowledgements,cycles);
      $fflush();
      comparisons=comparisons+1;
    end
  endtask
  task automatic reload_image;
    begin
      if (running || busy || pending || ddr_rsp_valid || ddr_req_valid || spi_cs_n!==1)
        $fatal(1,"QWEN_SHELL_RELOAD_NOT_IDLE");
      @(negedge clk); #1;
      writes=0; reads=0; acknowledgements=0; boot_segment=0; boot_offset=0;
      total_activation_writes=0;
      loading=1; spi_reads=0;
      cfg_valid=1; cfg_write=1; cfg_addr=32'h1c; cfg_wdata=1;
      do begin @(posedge clk); end while (!cfg_ready);
      #1; @(negedge clk); #1; cfg_valid=0; cfg_write=0;
      while (!cfg_rsp_valid) tick();
      repeat (3) begin
        if (!cfg_rsp_valid || cfg_rsp_error || cfg_rdata!==0)
          $fatal(1,"QWEN_SHELL_RELOAD_RESPONSE");
        tick();
      end
      @(negedge clk); #1; cfg_rsp_ready=1; tick();
      @(negedge clk); #1; cfg_rsp_ready=0;
      if (boot_done) $fatal(1,"QWEN_SHELL_RELOAD_NOT_WITHDRAWN");
      wait_boot(); reloads=reloads+1;
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    if (!$value$plusargs("scoreboard_fault=%d",scoreboard_fault)) scoreboard_fault=0;
    if (scoreboard_fault<0 || scoreboard_fault>3) $fatal(1,"INVALID_SCOREBOARD_FAULT");
    $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0018-run_shell_scoreboard/shell-flash-0.hex",flash,0,24280-1);
        segment_base[0]=64'd4096; segment_length[0]=64; segment_flash[0]=888;
    segment_base[1]=64'd4160; segment_length[1]=1568; segment_flash[1]=952;
    segment_base[2]=64'd5728; segment_length[2]=10940; segment_flash[2]=2520;
    segment_base[3]=64'd16668; segment_length[3]=4576; segment_flash[3]=13460;
    segment_base[4]=64'd21244; segment_length[4]=128; segment_flash[4]=18036;
    segment_base[5]=64'd21372; segment_length[5]=4144; segment_flash[5]=18164;
    segment_base[6]=64'd25516; segment_length[6]=290; segment_flash[6]=22308;
    segment_base[7]=64'd25808; segment_length[7]=1056; segment_flash[7]=22600;
    segment_base[8]=64'd26864; segment_length[8]=48; segment_flash[8]=23656;
    segment_base[9]=64'd26912; segment_length[9]=48; segment_flash[9]=23704;
    segment_base[10]=64'd26960; segment_length[10]=32; segment_flash[10]=23752;
    segment_base[11]=64'd26992; segment_length[11]=64; segment_flash[11]=23784;
    segment_base[12]=64'd27056; segment_length[12]=80; segment_flash[12]=23848;
    segment_base[13]=64'd27136; segment_length[13]=128; segment_flash[13]=23928;
    segment_base[14]=64'd27264; segment_length[14]=32; segment_flash[14]=24056;
    segment_base[15]=64'd27296; segment_length[15]=48; segment_flash[15]=24088;
    segment_base[16]=64'd27344; segment_length[16]=48; segment_flash[16]=24136;
    segment_base[17]=64'd27392; segment_length[17]=32; segment_flash[17]=24184;
    segment_base[18]=64'd27424; segment_length[18]=32; segment_flash[18]=24216;
    segment_base[19]=64'd27456; segment_length[19]=32; segment_flash[19]=24248;
    repeat (2) tick(); @(negedge clk); #1; rst_n=1;
    repeat (20) begin
      tick();
      if (spi_cs_n!==1 || ddr_req_valid!==0 || boot_done!==0)
        $fatal(1,"QWEN_SHELL_DELAYED_CALIBRATION");
    end
    @(negedge clk); #1; ddr_cal_done=1;
    $display("QWEN_SHELL_START transport=%0d cycles=%0d",BYPASS,cycles);
    $fflush();
    wait_boot();
    for (frame=0;frame<FRAMES;frame=frame+1) begin
      case (frame)
      0: begin
        input_length=3;
        output_length=8;
        operation_count=9;
        prompt_count=2;
        write_count=1368;
        $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0018-run_shell_scoreboard/shell-case-0-input.hex",input_bytes,0,2);
        $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0018-run_shell_scoreboard/shell-case-0-tokens.hex",expected_tokens,0,8);
        $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0018-run_shell_scoreboard/shell-case-0-output.hex",output_bytes,0,7);
        $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0018-run_shell_scoreboard/shell-case-0-write-address.hex",expected_write_address,0,1367);
        $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0018-run_shell_scoreboard/shell-case-0-write-data.hex",expected_write_data,0,1367);
        $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0018-run_shell_scoreboard/shell-case-0-write-operation.hex",expected_write_operation,0,1367);
      end
      1: begin
        input_length=4;
        output_length=8;
        operation_count=10;
        prompt_count=3;
        write_count=1520;
        $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0018-run_shell_scoreboard/shell-case-1-input.hex",input_bytes,0,3);
        $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0018-run_shell_scoreboard/shell-case-1-tokens.hex",expected_tokens,0,9);
        $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0018-run_shell_scoreboard/shell-case-1-output.hex",output_bytes,0,7);
        $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0018-run_shell_scoreboard/shell-case-1-write-address.hex",expected_write_address,0,1519);
        $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0018-run_shell_scoreboard/shell-case-1-write-data.hex",expected_write_data,0,1519);
        $readmemh("evidence/verification/l1-913cb344fb92445aabb76d4b58256f7d/case-0018-run_shell_scoreboard/shell-case-1-write-operation.hex",expected_write_operation,0,1519);
      end
      default: $fatal(1,"QWEN_SHELL_UNKNOWN_FRAME");
    endcase
      outputs=0; frame_done=0; input_count=0; embedding_reads=0;
      activation_writes=0; inference_reads=0; out_held=0;
      observed_input=0; observed_output=0; final_head_pending=0; input_finished=0;
      write_head.delete();
      for (integer item=write_count-1;item>=0;item=item-1) begin
        write_seen[item]=0;
        expected_write_next[item]=
          write_head.exists({expected_write_operation[item],expected_write_address[item]}) ?
          write_head[{expected_write_operation[item],expected_write_address[item]}] : -1;
        write_head[{expected_write_operation[item],expected_write_address[item]}]=item;
      end
      running=1;
      $display("QWEN_SHELL_PHASE phase=input_begin frame=%0d cycles=%0d",
               frame,cycles);
      $fflush();
      if (BYPASS) begin
        for (integer item=0;item<input_length;item=item+1)
          send_axis(input_bytes[item][7:0],item==input_length-1);
        input_finished=1;
      end else begin
        fork
          begin
            @(negedge clk); #1;
            for (integer item=0;item<input_length;item=item+1)
              send_serial(input_bytes[item][7:0]);
            input_count=input_length;
            send_serial(10);
            input_finished=1;
          end
          decode_serial();
        join
      end
      wait (frame_done!=0);
      repeat (20) tick();
      if (frame_done!=1 || busy || pending || ddr_req_valid || m_axis_tvalid ||
          outputs!=output_length || input_count!=input_length || inference_reads==0)
        $fatal(1,"QWEN_SHELL_FINAL_COUNTS");
      for (integer operation=0;operation<operation_count;operation=operation+1)
        $display("QWEN_SHELL_OPERATION frame=%0d position=%0d token=%0d cycles=%0d",
                 frame,operation,expected_tokens[operation],operation_cycles[operation]);
      $display("QWEN_SHELL_FRAME frame=%0d transport=%0d prompt_bytes=%0d operations=%0d output_bytes=%0d embedding_reads=%0d activation_writes=%0d cycles=%0d",
               frame,BYPASS,input_count,operation_count,outputs,embedding_reads,
               activation_writes,cycles);
      $fflush();
      running=0;
      if (frame==0 && FRAMES>1) reload_image();
    end
    if (completions!=FRAMES || request_stalls==0 ||
        (BYPASS && output_stalls==0) || reloads!=(FRAMES>1 ? 1 : 0))
      $fatal(1,"QWEN_SHELL_COVERAGE");
    $display("QWEN_SHELL_COUNTS frames=%0d reloads=%0d request_stalls=%0d output_stalls=%0d",
             completions,reloads,request_stalls,output_stalls);
    $display("COMPARED %0d",comparisons); $fflush(); $finish;
  end
endmodule
