"""Independent public-port protocol experiments; generated benches are evidence."""

import random
import struct


CONTROLLER = r"""
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg start=0, prompt_valid=0, prompt_last=0;
  reg [31:0] eos_token_id=0,max_new_tokens=0,vocab_size=1,seq_limit=16;
  reg [31:0] prompt_id=0;
  wire prompt_ready,generated_valid,generated_last,core_token_valid;
  wire [31:0] generated_id,core_token_id,core_token_pos;
  wire core_new_sequence,core_logit_ready,busy,done,error,finish_valid;
  wire [7:0] error_code;
  reg generated_ready=0,core_token_ready=0,finish_ready=0;
  reg core_logit_valid=0,core_done=0,core_error=0;
  reg [31:0] core_logit_index=0;
  reg signed [31:0] core_logit_data=0;
  anvil_edge_autoregressive_fsm #(.MAX_PROMPT_TOKENS(CAPACITY)) dut(.*);
  reg [31:0] expected_ids[0:CAPACITY+15],expected_generated[0:15];
  reg expected_last[0:15];
  integer expected_ops=0,expected_outputs=0,ops=0,outputs=0;
  integer finishes=0,completions=0,comparisons=0,cycle=0,authorized=-1;
  integer case_id=0,token_stalls=0,generated_stalls=0,finish_stalls=0;
  reg captured_last=0;
  reg [31:0] rng=SEED;
  reg token_held=0,generated_held=0,finish_held=0;
  reg [64:0] token_payload;
  reg [32:0] generated_payload;
  task automatic reset_check;
    begin
      if ({prompt_ready,generated_valid,generated_id,generated_last,
           core_token_valid,core_token_id,core_token_pos,core_new_sequence,
           core_logit_ready,busy,done,error,error_code,finish_valid} !== 145'd0)
        $fatal(1,"CONTROLLER_RESET t=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) begin
    if (rst_n) begin
      rng=(rng ^ (rng<<13)); rng=(rng ^ (rng>>17)); rng=(rng ^ (rng<<5));
      core_token_ready=rng[0] && cycle%7!=0;
      generated_ready=rng[1] && cycle%11!=0;
      finish_ready=rng[2] && cycle%5!=0;
    end
  end
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n) begin
      if ((^{prompt_ready,generated_valid,generated_id,generated_last,
             core_token_valid,core_token_id,core_token_pos,core_new_sequence,
             core_logit_ready,busy,done,error,error_code,finish_valid})===1'bx)
        $fatal(1,"CONTROLLER_XZ case=%0d",case_id);
      if (token_held && (!core_token_valid ||
          {core_token_id,core_token_pos,core_new_sequence}!==token_payload))
        $fatal(1,"CONTROLLER_TOKEN_STABILITY");
      if (generated_held && (!generated_valid ||
          {generated_id,generated_last}!==generated_payload))
        $fatal(1,"CONTROLLER_GENERATED_STABILITY");
      if (finish_held && !finish_valid) $fatal(1,"CONTROLLER_FINISH_STABILITY");
      token_held=core_token_valid && !core_token_ready;
      generated_held=generated_valid && !generated_ready;
      finish_held=finish_valid && !finish_ready;
      token_payload={core_token_id,core_token_pos,core_new_sequence};
      generated_payload={generated_id,generated_last};
      if (token_held) token_stalls=token_stalls+1;
      if (generated_held) generated_stalls=generated_stalls+1;
      if (finish_held) finish_stalls=finish_stalls+1;
      if (prompt_valid && prompt_ready && prompt_last) captured_last=1;
      if (core_done) authorized=cycle;
      if (core_token_valid && core_token_ready) begin
        if (!captured_last || ops>=expected_ops ||
            core_token_id!==expected_ids[ops] || core_token_pos!==ops ||
            core_new_sequence!==(ops==0))
          $fatal(1,"CONTROLLER_OPERATION case=%0d op=%0d id=%0d pos=%0d",
                 case_id,ops,core_token_id,core_token_pos);
        ops=ops+1; comparisons=comparisons+1;
      end
      if (generated_valid) begin
        if (authorized<0 || cycle<=authorized)
          $fatal(1,"CONTROLLER_EARLY_COMMIT");
      end
      if (generated_valid && generated_ready) begin
        if (outputs>=expected_outputs ||
            generated_id!==expected_generated[outputs] ||
            generated_last!==expected_last[outputs])
          $fatal(1,"CONTROLLER_ARGMAX case=%0d item=%0d observed=%0d last=%b",
                 case_id,outputs,generated_id,generated_last);
        outputs=outputs+1; comparisons=comparisons+1;
      end
      if (finish_valid && finish_ready) begin
        if (outputs!=expected_outputs || ops!=expected_ops)
          $fatal(1,"CONTROLLER_FINISH_OVERTAKE");
        finishes=finishes+1; comparisons=comparisons+1;
      end
      if (done) begin
        if (error || finishes!=1 || completions!=0)
          $fatal(1,"CONTROLLER_DONE");
        completions=completions+1; comparisons=comparisons+1;
      end
    end else begin token_held=0; generated_held=0; finish_held=0; end
  end
  task automatic tick;
    begin @(posedge clk); #1; end
  endtask
  task automatic fresh;
    begin
      @(negedge clk); #1;
      rst_n=0; start=0; prompt_valid=0; core_logit_valid=0;
      core_done=0; core_error=0;
      tick(); @(negedge clk); #1;
      ops=0; outputs=0; finishes=0; completions=0; captured_last=0; authorized=-1;
      rst_n=1;
    end
  endtask
  task automatic launch;
    begin
      @(negedge clk); #1; start=1; tick();
      @(negedge clk); #1; start=0;
    end
  endtask
  task automatic prompt(input integer id,input bit last);
    begin
      @(negedge clk); #1; prompt_id=id; prompt_last=last; prompt_valid=1;
      do begin @(posedge clk); end while (!prompt_ready);
      #1; @(negedge clk); #1; prompt_valid=0;
    end
  endtask
  task automatic logit(input integer idx,input reg signed [31:0] value,
                       input bit simultaneous_done);
    begin
      @(negedge clk); #1;
      core_logit_valid=1; core_logit_index=idx; core_logit_data=value;
      core_done=simultaneous_done;
      do begin @(posedge clk); end while (!core_logit_ready);
      #1; @(negedge clk); #1; core_logit_valid=0; core_done=0;
    end
  endtask
  task automatic frame(input integer operation,input integer winner,
                       input integer mode,input bit simultaneous_done);
    integer j;
    reg signed [31:0] value;
    begin
      while (ops<=operation) tick();
      for (j=0;j<vocab_size;j=j+1) begin
        if (mode==0) value=-2147483648;
        else if (mode==1) value=(j==winner || j==winner+1) ? -1 : -100;
        else if (mode==3) value=j==winner ? 2147483647 : -2147483648;
        else value=j==winner ? -2 : -100;
        logit(j,value,simultaneous_done && j==vocab_size-1);
      end
      if (!simultaneous_done) begin
        repeat (3) tick();
        @(negedge clk); #1; core_done=1; tick();
        @(negedge clk); #1; core_done=0;
      end
    end
  endtask
  task automatic success;
    begin
      while (completions==0 && !error) tick();
      if (error) $fatal(1,"CONTROLLER_UNEXPECTED_ERROR case=%0d code=%h",case_id,error_code);
      repeat (9) tick();
      if (ops!=expected_ops || outputs!=expected_outputs || finishes!=1 ||
          completions!=1 || busy || done || error)
        $fatal(1,"CONTROLLER_COUNTS case=%0d",case_id);
      comparisons=comparisons+1;
    end
  endtask
  task automatic failure(input [7:0] code);
    begin
      while (!error) tick();
      repeat (9) begin
        tick();
        if (error!==1 || error_code!==code || done!==0 ||
            generated_valid!==0 || finish_valid!==0 || core_token_valid!==0)
          $fatal(1,"CONTROLLER_ERROR case=%0d expected=%h observed=%h",
                 case_id,code,error_code);
      end
      comparisons=comparisons+1;
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    repeat (2) tick();
    CASES
    if (token_stalls==0 || finish_stalls==0 ||
        (CAPACITY>1 && generated_stalls==0))
      $fatal(1,"CONTROLLER_STALL_COVERAGE");
    if (comparisons!=COMPARISONS)
      $fatal(1,"CONTROLLER_COMPARE_COUNT actual=%0d",comparisons);
    $display("COMPARED %0d",comparisons);
    $finish;
  end
  initial begin
    repeat (12000000) @(posedge clk);
    $fatal(1,"CONTROLLER_CYCLE_BOUND case=%0d ops=%0d",case_id,ops);
  end
endmodule
"""


def controller_test(evidence, capacity, seed):
    """Expected operations follow tokens and greedy mathematics, not RTL states."""
    cases = []
    count = 0
    rng = random.Random(seed)
    scenarios = [
        (1, [0], 0, [0], 0),
        (1, [0], 1, [0], 0),
        (257, [5], 1, [0], 0),
        (257, [7], 3, [256], 2),
        (257, [8], 1, [9], 1),
        (257, [0], 0, [3], 2),
        (257, [1], 1, [254], 3),
    ]
    if capacity > 1:
        scenarios.extend([
            (257, [2, 4, 6], 3, [9, 10, 11], 2),
            (257, [2, 4], 3, [9, 256], 2),
            (257, [3, 1], 4, [256], 2),
        ])
    if capacity == 4096:
        scenarios.extend((v, [1, 2], 1, [v - 2], 2)
                         for v in (128256, 151936, 262144))
        scenarios.append((1, [0] * capacity, 0, [0], 0))
    for case_id, (vocab, prompt, maximum, selections, mode) in enumerate(scenarios):
        eos = vocab - 1
        outputs = []
        operations = list(prompt)
        frames = [rng.randrange(vocab) for _ in prompt[:-1]]
        if maximum == 0:
            frames.append(selections[0])
        else:
            for n, selected in enumerate(selections):
                if mode == 0:
                    selected = 0
                frames.append(selected)
                if selected == eos:
                    break
                outputs.append((selected, n + 1 == maximum))
                if n + 1 < maximum:
                    operations.append(selected)
        lines = [
            f"fresh(); case_id={case_id}; vocab_size={vocab}; eos_token_id={eos};",
            f"max_new_tokens={maximum}; seq_limit={max(16, len(operations))};",
            f"expected_ops={len(operations)}; expected_outputs={len(outputs)};",
        ]
        lines.extend(f"expected_ids[{i}]={value};" for i, value in enumerate(operations))
        lines.extend(f"expected_generated[{i}]={value}; expected_last[{i}]={int(last)};"
                     for i, (value, last) in enumerate(outputs))
        lines.append("launch();")
        lines.extend(f"prompt({value},{int(i == len(prompt)-1)});"
                     for i, value in enumerate(prompt))
        for i, winner in enumerate(frames):
            frame_mode = mode if i >= len(prompt) - 1 else 2
            # Argmax on Python integers includes the all-INT32_MIN and tie cases.
            values = ((-(1 << 31) if frame_mode == 0 else
                       (-1 if j in (winner, winner + 1) else -100)
                       if frame_mode == 1 else
                       ((1 << 31)-1 if j == winner else -(1 << 31))
                       if frame_mode == 3 else (-2 if j == winner else -100))
                      for j in range(vocab))
            mathematical_winner = max(enumerate(values), key=lambda item: (item[1], -item[0]))[0]
            if i >= len(prompt) - 1 and maximum:
                assert mathematical_winner == frames[i]
            lines.append(f"frame({i},{winner},{frame_mode},{i % 2});")
        lines.append("success();")
        count += len(operations) + len(outputs) + 3
        cases.append("\n".join(lines))

    malformed = [
        ("core_done=1;", "21"),
        ("core_logit_index=1; core_logit_valid=1;", "21"),
        ("core_error=1;", "20"),
        ("core_logit_index=257; core_logit_valid=1;", "21"),
        ("core_logit_index=0; core_logit_valid=1; core_done=1;", "21"),
        ("logit(0,-100,0); core_logit_index=0; core_logit_valid=1;", "21"),
        ("logit(0,-100,0); core_logit_index=2; core_logit_valid=1;", "21"),
        ("""begin
integer j;
for (j=0;j<257;j=j+1) logit(j,-100,0);
core_logit_index=257; core_logit_valid=1;
end""", "21"),
    ]
    for index, (fault, code) in enumerate(malformed):
        cases.append(f"""
fresh(); case_id={100+index}; vocab_size=257; eos_token_id=256;
max_new_tokens=1; seq_limit=16; expected_ops=1; expected_outputs=0;
expected_ids[0]=0; launch(); prompt(0,1);
while (ops<1) tick();
@(negedge clk); #1; {fault}
failure(8'h{code});
""")
        count += 2
    for index, settings in enumerate((
        "vocab_size=0; eos_token_id=0; max_new_tokens=0; seq_limit=16;",
        "vocab_size=262145; eos_token_id=0; max_new_tokens=0; seq_limit=16;",
        "vocab_size=257; eos_token_id=257; max_new_tokens=0; seq_limit=16;",
        "vocab_size=257; eos_token_id=256; max_new_tokens=0; seq_limit=0;",
        "vocab_size=257; eos_token_id=256; max_new_tokens=0; seq_limit=16777216;",
        "vocab_size=257; eos_token_id=256; max_new_tokens=17; seq_limit=16;",
    )):
        cases.append(f"""
fresh(); case_id={200+index}; {settings}
expected_ops=0; expected_outputs=0; launch(); failure(8'h32);
""")
        count += 1
    cases.append("""
fresh(); case_id=210; vocab_size=257; eos_token_id=256; max_new_tokens=1; seq_limit=16;
expected_ops=0; expected_outputs=0; launch(); prompt(257,1); failure(8'h11);
fresh(); case_id=211; vocab_size=257; eos_token_id=256; max_new_tokens=0; seq_limit=1;
expected_ops=0; expected_outputs=0; launch(); prompt(0,0); failure(8'h31);
fresh(); case_id=212; vocab_size=257; eos_token_id=256; max_new_tokens=1; seq_limit=16;
expected_ops=0; expected_outputs=0; launch();
@(negedge clk); #1; core_done=1; failure(8'h21);
""")
    count += 3
    if capacity == 1:
        cases.append("""
fresh(); case_id=111; vocab_size=257; eos_token_id=256; max_new_tokens=1;
expected_ops=0; expected_outputs=0; launch(); prompt(0,0); failure(8'h30);
""")
        count += 1
    else:
        cases.append("""
fresh(); case_id=112; vocab_size=257; eos_token_id=256; max_new_tokens=2;
seq_limit=2; expected_ops=2; expected_outputs=1;
expected_ids[0]=1; expected_ids[1]=2;
expected_generated[0]=3; expected_last[0]=0;
launch(); prompt(1,0); prompt(2,1); frame(0,0,2,0); frame(1,3,2,1);
failure(8'h31);
""")
        count += 4
        cases.append(f"""
fresh(); case_id=213; vocab_size=257; eos_token_id=256; max_new_tokens=0; seq_limit={capacity+1};
expected_ops=0; expected_outputs=0; launch();
repeat ({capacity}) prompt(0,0);
failure(8'h30);
""")
        count += 1
    cases.append("""
fresh(); case_id=214; vocab_size=257; eos_token_id=256; max_new_tokens=1; seq_limit=16;
expected_ops=1; expected_outputs=0; expected_ids[0]=0;
launch(); prompt(0,1); while (ops<1) tick(); logit(0,-1,0);
fresh(); expected_ops=0; expected_outputs=0; repeat (10) tick();
if (ops!=0 || outputs!=0 || finishes!=0 || completions!=0 || error || busy)
  $fatal(1,"CONTROLLER_RESET_LOGIT_EPOCH");
comparisons=comparisons+1;
""")
    count += 2
    bench = CONTROLLER.replace("CAPACITY", str(capacity)).replace("SEED", str(seed))
    bench = bench.replace("CASES", "\n".join(cases)).replace("COMPARISONS", str(count))
    evidence.simulate(f"controller-c{capacity}-s{seed}", bench,
                      ["rtl/anvil_edge_autoregressive_fsm.sv"], count)


def run_controller(evidence):
    evidence.tools(("iverilog", "vvp"))
    for seed in (1, 17, 89):
        for capacity in (1, 3, 4096):
            controller_test(evidence, capacity, seed)


UART = r"""
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg uart_rx=1,axis_bypass=0;
  wire uart_tx;
  reg [31:0] divisor=DIVISOR,uart_frame_bytes=0;
  reg s_axis_tvalid=0,s_axis_tlast=0,m_axis_tready=0;
  reg [7:0] s_axis_tdata=0;
  wire s_axis_tready,m_axis_tvalid,m_axis_tlast;
  wire [7:0] m_axis_tdata;
  wire rx_valid,rx_last,tx_ready,framing_error,overflow_error,rx_idle,tx_idle,rx_line_idle;
  reg rx_ready=0,tx_valid=0,tx_last=0,receive_enable=1,response_complete=0;
  wire [7:0] rx_data;
  reg [7:0] tx_data=0;
  anvil_edge_uart_io #(.RX_FIFO_DEPTH(@DEPTH@),.TX_FIFO_DEPTH(@DEPTH@)) dut(.*);
  reg [8:0] expected_rx[0:63],expected_tx[0:63];
  integer nrx=0,ntx=0,rx_count=0,tx_count=0,comparisons=0,cycle=0;
  integer rx_stalls=0,tx_stalls=0,serial_bits=0;
  reg rx_hold=0,tx_hold=0,checking=0,random_ready=1;
  reg [8:0] held_rx,held_tx;
  reg [31:0] rng=SEED;
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
      repeat (DIVISOR) begin @(negedge clk); #1; end
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
  task automatic decode_serial(input [7:0] value);
    integer b,c;
    reg [9:0] bits;
    begin
      bits={1'b1,value,1'b0};
      while (uart_tx!==0) tick();
      for (b=0;b<10;b=b+1)
        for (c=0;c<DIVISOR;c=c+1) begin
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
    fresh(0,0);
    nrx=3; expected_rx[0]=9'h041; expected_rx[1]=9'h0c3; expected_rx[2]=9'h1a9;
    @(negedge clk); #1;
    serial_byte(8'h41,1); serial_byte(8'hc3,1); serial_byte(8'ha9,1); serial_byte(10,1);
    while (rx_count<nrx) tick();
    repeat (12) tick();
    if (rx_count!=3) $fatal(1,"UART_LF_COUNT");
    comparisons=comparisons+1;
    fork
      begin transmit(8'h96,1); end
      begin decode_serial(8'h96); end
    join
    while (!tx_idle) tick();
    fresh(0,3);
    nrx=3; expected_rx[0]=9'h000; expected_rx[1]=9'h00a; expected_rx[2]=9'h1ff;
    @(negedge clk); #1;
    serial_byte(0,1); serial_byte(10,1); serial_byte(255,1);
    while (rx_count<3) tick();
    comparisons=comparisons+1;
    fresh(1,0);
    nrx=32; ntx=32;
    for (j=0;j<32;j=j+1) begin
      expected_rx[j]={(j==31),8'((j*37+19)&255)};
      expected_tx[j]={(j==31),8'((j*53+7)&255)};
    end
    fork
      begin for (integer k=0;k<32;k=k+1) bypass_byte((k*37+19)&255,k==31); end
      begin for (integer k=0;k<32;k=k+1) transmit((k*53+7)&255,k==31); end
    join
    while (rx_count<32 || tx_count<32) tick();
    repeat (10) tick();
    if (uart_tx!==1 || !tx_idle || !rx_idle) $fatal(1,"UART_BYPASS_DRAIN");
    comparisons=comparisons+1;
    fresh(0,1); checking=0;
    @(negedge clk); #1; serial_byte(8'h5a,0);
    uart_rx=1; repeat (2*DIVISOR+10) tick();
    if (framing_error!==1 || overflow_error!==0) $fatal(1,"UART_BAD_STOP");
    comparisons=comparisons+1;
    fresh(0,1); checking=0; random_ready=0; rx_ready=0;
    @(negedge clk); #1;
    for (j=0;j<@DEPTH@+2;j=j+1) serial_byte(j,1);
    repeat (DIVISOR+12) tick();
    if (overflow_error!==1) $fatal(1,"UART_OVERFLOW");
    comparisons=comparisons+1;
    fresh(0,0); checking=0;
    @(negedge clk); #1; serial_byte(10,1);
    repeat (DIVISOR+12) tick();
    if (framing_error!==1) $fatal(1,"UART_EMPTY_LF");
    comparisons=comparisons+1;
    fresh(0,0); checking=0;
    @(negedge clk); #1; uart_rx=0;
    repeat (4) tick();
    fresh(1,0);
    if (rx_count!=0 || framing_error || overflow_error) $fatal(1,"UART_RESET_RX");
    comparisons=comparisons+1;
    if (rx_stalls==0 || tx_stalls==0 || serial_bits!=10*DIVISOR)
      $fatal(1,"UART_REQUIRED_EVENTS");
    if (comparisons!=78) $fatal(1,"UART_COMPARISONS got=%0d",comparisons);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin
    repeat (1000000) @(posedge clk); $fatal(1,"UART_CYCLE_BOUND");
  end
endmodule
"""


def run_uart(evidence):
    evidence.tools(("iverilog", "vvp"))
    for seed in (1, 17, 89):
        for divisor, depth in ((4, 1), (5, 3), (868, 16), (5, 2)):
            bench = UART.replace("DIVISOR", str(divisor)).replace("@DEPTH@", str(depth))
            bench = bench.replace("SEED", str(seed))
            evidence.simulate(f"uart-d{divisor}-f{depth}-s{seed}", bench,
                              ["rtl/anvil_edge_fifo.sv", "rtl/anvil_edge_uart_io.sv"], 78)
    run_uart_controls(evidence)


def run_uart_controls(evidence):
    evidence.tools(("iverilog", "vvp"))
    for seed in (1, 17, 89):
        for divisor in (4, 5, 868):
            bench = UART.replace("DIVISOR", str(divisor)).replace("@DEPTH@", "3")
            bench = bench.replace("SEED", str(seed))
            # Capture the bit period in the independent decoder; changing the
            # input divisor mid-frame must not change the on-wire bit lengths.
            bench = bench.replace("decode_serial(input [7:0] value);",
                                  "decode_serial(input [7:0] value,input integer period);")
            bench = bench.replace(f"c<{divisor};c=c+1", "c<period;c=c+1")
            begin = bench.index("    fresh(0,0);", bench.index("  integer j;"))
            end = bench.index('    $display("COMPARED', begin)
            bench = bench[:begin] + f"""
    fresh(0,1);
    fork
      begin transmit(8'h96,1); end
      begin decode_serial(8'h96,{divisor}); end
      begin
        while (uart_tx!==0) tick();
        repeat ({divisor}*2) tick();
        @(negedge clk); #1; divisor={divisor+3}; axis_bypass=1;
        uart_frame_bytes=3;
        repeat ({divisor}*5) begin
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
    if (uart_tx!==1 || serial_bits!={divisor*10})
      $fatal(1,"UART_TX_CONTROL_LATCH");
    comparisons=comparisons+1;
    divisor={divisor};
    fresh(0,2);
    nrx=2; expected_rx[0]=9'h041; expected_rx[1]=9'h142;
    fork
      begin
        @(negedge clk); #1;
        serial_byte(8'h41,1); serial_byte(8'h42,1);
      end
      begin
        while (uart_rx!==0) tick();
        repeat ({divisor}*2+4) tick();
        @(negedge clk); #1;
        divisor={divisor+3}; axis_bypass=1; uart_frame_bytes=1;
        repeat ({divisor}*4) begin
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
    divisor={divisor}; fresh(0,1); checking=0;
    @(negedge clk); #1; uart_rx=0;
    repeat (1) begin @(negedge clk); #1; end
    uart_rx=1;
    repeat ({divisor}*2+10) tick();
    if (framing_error!==1 || overflow_error!==0 || rx_valid!==0)
      $fatal(1,"UART_FALSE_START");
    comparisons=comparisons+1;
    fresh(0,1);
    fork
      begin transmit(8'h00,1); end
      begin
        while (uart_tx!==0) tick();
        repeat ({divisor}*3) tick();
        @(negedge clk); #1; rst_n=0; checking=0;
        #0; reset_check();
      end
    join
    fresh(1,0);
    repeat ({divisor}*12+10) begin
      tick();
      if (uart_tx!==1 || m_axis_tvalid!==0 || rx_valid!==0 ||
          !tx_idle || framing_error || overflow_error)
        $fatal(1,"UART_RESET_TX_EPOCH");
    end
    comparisons=comparisons+1;
    if (comparisons!=11) $fatal(1,"UART_CONTROL_COMPARISONS %0d",comparisons);
""" + bench[end:]
            evidence.simulate(f"uart-controls-d{divisor}-s{seed}", bench,
                              ["rtl/anvil_edge_fifo.sv", "rtl/anvil_edge_uart_io.sv"], 11)
        bench = UART.replace("DIVISOR", "5").replace("@DEPTH@", "1").replace("SEED", str(seed))
        bench = bench.replace(".TX_FIFO_DEPTH(1)", ".TX_FIFO_DEPTH(1),.FRAME_LOCK(1)")
        begin = bench.index("    fresh(0,0);", bench.index("  integer j;"))
        end = bench.index('    $display("COMPARED', begin)
        bench = bench[:begin] + """
    fresh(1,0); nrx=2; expected_rx[0]=9'h141; expected_rx[1]=9'h142;
    bypass_byte(8'h41,1);
    while (rx_count!=1) tick();
    @(negedge clk); #1; s_axis_tvalid=1; s_axis_tdata=8'h42; s_axis_tlast=1;
    repeat (15) begin
      tick();
      if (s_axis_tready!==0 || rx_count!=1) $fatal(1,"UART_FRAME_LOCK");
    end
    comparisons=comparisons+1;
    @(negedge clk); #1; response_complete=1; tick();
    @(negedge clk); #1; response_complete=0;
    do begin @(posedge clk); end while (!s_axis_tready);
    #1; @(negedge clk); #1; s_axis_tvalid=0;
    while (rx_count!=2) tick();
    repeat (10) tick();
    @(negedge clk); #1; receive_enable=0; response_complete=1; tick();
    @(negedge clk); #1; response_complete=0;
    repeat (10) begin
      tick();
      if (s_axis_tready!==0) $fatal(1,"UART_RECEIVE_DISABLED");
    end
    comparisons=comparisons+1;
    if (comparisons!=4) $fatal(1,"UART_LOCK_COMPARISONS");
""" + bench[end:]
        evidence.simulate(f"uart-frame-lock-s{seed}", bench,
                          ["rtl/anvil_edge_fifo.sv", "rtl/anvil_edge_uart_io.sv"], 4)


DETOKENIZER = r"""
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg start=0,in_valid=0,in_last=0,out_ready=0;
  reg [31:0] in_token_id=0;
  wire in_ready,out_valid,out_last,busy,done,error;
  wire [7:0] out_data,error_code;
  wire tbl_req_valid,tbl_rsp_ready;
  wire [63:0] tbl_req_addr;
  reg tbl_req_ready=0,tbl_rsp_valid=0,tbl_rsp_error=0;
  reg [31:0] tbl_rsp_data=0;
  reg config_valid=1,finish_valid=0;
  wire finish_ready;
  reg [31:0] cfg_vocab_size=257,cfg_max_token_byte_length=64;
  reg [63:0] cfg_token_records_base=64'h1000,cfg_token_bytes_base=64'h4000;
  reg [63:0] cfg_token_bytes_count=@BYTE_COUNT@;
  anvil_edge_detokenizer dut(.*);
  reg [63:0] addresses[0:255];
  reg [7:0] expected[0:255];
  reg [31:0] rng=@SEED@;
  reg outstanding=0,req_held=0,out_held=0;
  reg [63:0] pending_addr=0,held_addr=0;
  reg [8:0] held_out=0;
  integer requests=0,responses=0,outputs=0,completions=0,cycle=0,delay_count=0;
  integer request_stalls=0,output_stalls=0,comparisons=0;
  function automatic [31:0] memory(input [63:0] address);
    begin
      case (address)
        @MEMORY@
        default: $fatal(1,"DETOK_UNMAPPED_READ address=%h",address);
      endcase
    end
  endfunction
  task automatic reset_check;
    begin
      if ({in_ready,out_valid,out_data,out_last,busy,done,error,error_code,
           tbl_req_valid,tbl_req_addr,tbl_rsp_ready,finish_ready}!==90'd0)
        $fatal(1,"DETOK_RESET t=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) begin
    if (rst_n) begin
      rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
      tbl_req_ready=rng[0] && cycle%5!=0;
      out_ready=rng[1] && cycle%7!=0;
      if (outstanding && !tbl_rsp_valid) begin
        if (delay_count==0) begin
          tbl_rsp_valid<=1; tbl_rsp_data=memory(pending_addr);
          tbl_rsp_error=@BUS_ERROR@;
        end else delay_count=delay_count-1;
      end
    end
  end
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n) begin
      if ((^{in_ready,out_valid,out_data,out_last,busy,done,error,error_code,
             tbl_req_valid,tbl_req_addr,tbl_rsp_ready,finish_ready})===1'bx)
        $fatal(1,"DETOK_XZ");
      if (req_held && (!tbl_req_valid || tbl_req_addr!==held_addr))
        $fatal(1,"DETOK_REQUEST_STABILITY");
      if (out_held && (!out_valid || {out_last,out_data}!==held_out))
        $fatal(1,"DETOK_OUTPUT_STABILITY");
      req_held=tbl_req_valid && !tbl_req_ready;
      out_held=out_valid && !out_ready;
      held_addr=tbl_req_addr; held_out={out_last,out_data};
      if (req_held) request_stalls=request_stalls+1;
      if (out_held) output_stalls=output_stalls+1;
      if (tbl_rsp_valid && tbl_rsp_ready) begin
        if (!outstanding) $fatal(1,"DETOK_ORPHAN_RESPONSE");
        outstanding=0; responses=responses+1; tbl_rsp_valid<=0;
      end
      if (tbl_req_valid && tbl_req_ready) begin
        if (outstanding || requests>=@REQUESTS@ || tbl_req_addr!==addresses[requests])
          $fatal(1,"DETOK_LOOKUP item=%0d expected=%h observed=%h",
                 requests,addresses[requests],tbl_req_addr);
        pending_addr=tbl_req_addr; outstanding=1; delay_count=1+rng[4:2];
        requests=requests+1; comparisons=comparisons+1;
      end
      if (out_valid && out_ready) begin
        if (outputs>=@OUTPUTS@ || out_data!==expected[outputs] ||
            out_last!==(outputs==@OUTPUTS@-1))
          $fatal(1,"DETOK_BYTES item=%0d expected=%h observed=%h last=%b",
                 outputs,expected[outputs],out_data,out_last);
        outputs=outputs+1; comparisons=comparisons+1;
      end
      if (done) begin
        if (error || outputs!=@OUTPUTS@ || outstanding || completions!=0)
          $fatal(1,"DETOK_PREMATURE_DONE");
        completions=completions+1;
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic token(input integer id,input bit last);
    begin
      @(negedge clk); #1; in_valid=1; in_token_id=id; in_last=last;
      do begin @(posedge clk); end while (!in_ready);
      #1; @(negedge clk); #1; in_valid=0;
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    @VECTORS@
    repeat (2) tick();
    @(negedge clk); #1; rst_n=1; start=1; tick();
    @(negedge clk); #1; start=0;
    @STIMULUS@
    if (@ERROR_CODE@!=0) begin
      while (!error) tick();
      repeat (10) begin
        tick();
        if (error!==1 || error_code!==@ERROR_CODE@ || done!==0)
          $fatal(1,"DETOK_ERROR expected=%h observed=%h",@ERROR_CODE@,error_code);
      end
      if (outputs!=@OUTPUTS@ || completions!=0 || outstanding)
        $fatal(1,"DETOK_ERROR_COUNTS");
    end else begin
      while (completions==0 && !error) tick();
      repeat (10) tick();
      if (error || completions!=1 || outputs!=@OUTPUTS@ || requests!=@REQUESTS@ ||
          responses!=requests || outstanding || busy)
        $fatal(1,"DETOK_COUNTS requests=%0d responses=%0d outputs=%0d error=%h",
               requests,responses,outputs,error_code);
    end
    comparisons=comparisons+1;
    if (comparisons!=requests+@OUTPUTS@+1) $fatal(1,"DETOK_COMPARISONS");
    $display("DETOK_REQUESTS %0d",requests);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin
    repeat (100000) @(posedge clk); $fatal(1,"DETOK_CYCLE_BOUND");
  end
endmodule
"""


def detokenizer_test(evidence, seed, name, pieces, *, finish=False, error=0,
                     bad_record=False, invalid_id=False, bus_error=False):
    # The offsets intentionally cross word boundaries and do not start at zero.
    raw = b"\x7f\x55\x13"
    records = {}
    reads = []
    for token, piece in enumerate(pieces):
        offset = len(raw)
        raw += piece
        record = struct.pack("<QII", offset if not bad_record else 1 << 63,
                             len(piece), 1 if piece else 2)
        for word in range(4):
            records[0x1020 + token * 16 + word * 4] = int.from_bytes(
                record[word * 4:word * 4 + 4], "little")
        reads.extend(0x1020 + token * 16 + word * 4 for word in range(4))
        if not bad_record:
            reads.extend((0x4020 + offset + byte) & ~3 for byte in range(len(piece)))
    memory = dict(records)
    padded = raw + b"\x00" * (-len(raw) % 4)
    memory.update({0x4020 + offset: int.from_bytes(padded[offset:offset+4], "little")
                   for offset in range(0, len(padded), 4)})
    if invalid_id:
        reads = []
    if bus_error:
        reads = reads[:1]
    output = b"".join(pieces) if not error else b""
    if not error:
        assert output.decode("utf-8").encode("utf-8") == output
    vectors = [f"addresses[{i}]=64'h{address:x};" for i, address in enumerate(reads)]
    vectors.extend(f"expected[{i}]=8'h{value:02x};" for i, value in enumerate(output))
    stimulus = []
    if invalid_id:
        stimulus.append("token(257,1);")
    else:
        stimulus.extend(f"token({token},{int(not finish and token==len(pieces)-1)});"
                        for token in range(len(pieces)))
    if finish:
        stimulus.append("""
while (!finish_ready && !error) tick();
@(negedge clk); #1; finish_valid=1;
do begin @(posedge clk); end while (!finish_ready);
#1; @(negedge clk); #1; finish_valid=0;
""")
    parameters = {
        "SEED": str(seed), "BYTE_COUNT": str(len(raw)),
        "MEMORY": "\n".join(f"64'h{a:x}: memory=32'h{v:08x};"
                            for a, v in sorted(memory.items())),
        "BUS_ERROR": str(int(bus_error)), "REQUESTS": str(len(reads)),
        "OUTPUTS": str(len(output)), "ERROR_CODE": f"8'h{error:02x}",
        "VECTORS": "\n".join(vectors), "STIMULUS": "\n".join(stimulus),
    }
    bench = DETOKENIZER
    for key, value in parameters.items():
        bench = bench.replace(f"@{key}@", value)
    comparisons = len(reads) + len(output) + 1
    evidence.simulate(f"detok-{name}-s{seed}", bench,
                      ["rtl/anvil_edge_detokenizer.sv"], comparisons)


def run_detokenizer(evidence):
    evidence.tools(("iverilog", "vvp"))
    for seed in (1, 17, 89):
        for name, pieces, options in (
            ("ascii", [b"A"], {}),
            ("split-accent", [b"\xc3", b"\xa9"], {}),
            ("split-emoji", [b"\xf0", b"\x9f\x98", b"\x80"], {"finish": True}),
            ("mixed", [b"hello ", "\u4e2d".encode(), b" e\xcc\x81"], {}),
            ("empty", [], {"finish": True}),
            ("empty-special", [b""], {}),
            ("offset-bounds", [b"A"], {"bad_record": True, "error": 0x11}),
            ("inactive-id", [], {"invalid_id": True, "error": 0x11}),
            ("incomplete", [b"\xe2\x82"], {"error": 0x10}),
            ("bad-continuation", [b"\xc3A"], {"error": 0x10}),
            ("overlong", [b"\xe0\x80\x80"], {"error": 0x10}),
            ("surrogate", [b"\xed\xa0\x80"], {"error": 0x10}),
            ("out-of-range", [b"\xf4\x90\x80\x80"], {"error": 0x10}),
            ("ddr-error", [b"A"], {"bus_error": True, "error": 0x04}),
        ):
            detokenizer_test(evidence, seed, name, pieces, **options)


def bpe_reference(tokens, merges):
    result = list(tokens)
    while True:
        candidates = [(merges[(left, right)][1], index, merges[(left, right)][0])
                      for index, (left, right) in enumerate(zip(result, result[1:]))
                      if (left, right) in merges]
        if not candidates:
            return result
        _, index, replacement = min(candidates)
        result[index:index + 2] = [replacement]


def bpe_test(evidence, seed, name="ranked", *, tie=False, maximum_rank=False):
    tokens = [65, 66] if maximum_rank else [65, 66, 67]
    merges = {(65, 66): (256, 0xFFFFFFFF if maximum_rank else 10)}
    if not maximum_rank:
        merges.update({(66, 67): (257, 10 if tie else 1), (256, 67): (258, 0)})
    expected = bpe_reference(tokens, merges)
    records = b"".join(struct.pack("<IIII", left, right, result, rank)
                       for (left, right), (result, rank) in sorted(merges.items()))
    memory = {0x1020 + offset: int.from_bytes(records[offset:offset+4], "little")
              for offset in range(0, len(records), 4)}
    bench = DETOKENIZER.replace("anvil_edge_detokenizer dut(.*);", """
  anvil_edge_ranked_bpe #(.MAX_PRETOKEN_BYTES(8)) dut(.*);
""")
    begin = bench.index("  reg config_valid=1,finish_valid=0;")
    end = bench.index("  anvil_edge_ranked_bpe", begin)
    bench = bench[:begin] + f"""
  reg config_valid=1;
  reg [31:0] cfg_vocab_size=512,cfg_merge_count={len(merges)};
  reg [63:0] cfg_merge_base=64'h1000;
""" + bench[end:]
    bench = bench.replace("wire [7:0] out_data,error_code;",
                          "wire [31:0] out_token_id;\n  wire [7:0] error_code;")
    bench = bench.replace("reg [7:0] expected[0:255];", "reg [31:0] expected[0:255];")
    bench = bench.replace("reg [8:0] held_out=0;", "reg [32:0] held_out=0;")
    bench = bench.replace("out_data", "out_token_id").replace(",finish_ready", "")
    begin = bench.index("        if (outstanding || requests>=")
    end = bench.index("        pending_addr=", begin)
    bench = bench[:begin] + f"""
        if (outstanding || tbl_req_addr<64'h1020 ||
            tbl_req_addr>=64'h{0x1020+len(records):x} || tbl_req_addr[1:0]!=0)
          $fatal(1,"BPE_LOOKUP_BOUNDS");
""" + bench[end:]
    bench = bench.replace("requests!=@REQUESTS@ ||", "requests==0 ||")
    bench = bench.replace("DETOK", "BPE")
    parameters = {
        "SEED": str(seed), "BUS_ERROR": "0", "ERROR_CODE": "8'h00",
        "OUTPUTS": str(len(expected)),
        "MEMORY": "\n".join(f"64'h{address:x}: memory=32'h{value:x};"
                            for address, value in memory.items()),
        "VECTORS": "\n".join(f"expected[{i}]={value};" for i, value in enumerate(expected)),
        "STIMULUS": "\n".join(f"token({value},{int(i==len(tokens)-1)});"
                              for i, value in enumerate(tokens)),
    }
    for key, value in parameters.items():
        bench = bench.replace(f"@{key}@", value)
    evidence.simulate(f"bpe-{name}-s{seed}", bench, ["rtl/anvil_edge_ranked_bpe.sv"], None)


def run_bpe(evidence):
    evidence.tools(("iverilog", "vvp"))
    for seed in (1, 17, 89):
        bpe_test(evidence, seed)
        bpe_test(evidence, seed, "leftmost-tie", tie=True)
        bpe_test(evidence, seed, "maximum-rank", maximum_rank=True)
