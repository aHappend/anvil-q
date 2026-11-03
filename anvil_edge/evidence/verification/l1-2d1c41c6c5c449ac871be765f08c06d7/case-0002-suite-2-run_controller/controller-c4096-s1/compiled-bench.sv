
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
  anvil_edge_autoregressive_fsm #(.MAX_PROMPT_TOKENS(4096)) dut(.*);
  reg [31:0] expected_ids[0:4096+15],expected_generated[0:15];
  reg expected_last[0:15];
  integer expected_ops=0,expected_outputs=0,ops=0,outputs=0;
  integer finishes=0,completions=0,comparisons=0,cycle=0,authorized=-1;
  integer case_id=0,token_stalls=0,generated_stalls=0,finish_stalls=0;
  reg captured_last=0;
  reg [31:0] rng;
  initial if (!$value$plusargs("verification_seed=%d",rng)) $fatal(1,"MISSING_VERIFICATION_SEED");
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
    rst_n=0; #1ps; reset_check();
    repeat (2) tick();
    fresh(); case_id=0; vocab_size=1; eos_token_id=0;
max_new_tokens=0; seq_limit=16;
expected_ops=1; expected_outputs=0;
expected_ids[0]=0;
launch();
prompt(0,1);
frame(0,0,0,0);
success();
fresh(); case_id=1; vocab_size=1; eos_token_id=0;
max_new_tokens=1; seq_limit=16;
expected_ops=1; expected_outputs=0;
expected_ids[0]=0;
launch();
prompt(0,1);
frame(0,0,0,0);
success();
fresh(); case_id=2; vocab_size=257; eos_token_id=256;
max_new_tokens=1; seq_limit=16;
expected_ops=1; expected_outputs=1;
expected_ids[0]=5;
expected_generated[0]=0; expected_last[0]=1;
launch();
prompt(5,1);
frame(0,0,0,0);
success();
fresh(); case_id=3; vocab_size=257; eos_token_id=256;
max_new_tokens=3; seq_limit=16;
expected_ops=1; expected_outputs=0;
expected_ids[0]=7;
launch();
prompt(7,1);
frame(0,256,2,0);
success();
fresh(); case_id=4; vocab_size=257; eos_token_id=256;
max_new_tokens=1; seq_limit=16;
expected_ops=1; expected_outputs=1;
expected_ids[0]=8;
expected_generated[0]=9; expected_last[0]=1;
launch();
prompt(8,1);
frame(0,9,1,0);
success();
fresh(); case_id=5; vocab_size=257; eos_token_id=256;
max_new_tokens=0; seq_limit=16;
expected_ops=1; expected_outputs=0;
expected_ids[0]=0;
launch();
prompt(0,1);
frame(0,3,2,0);
success();
fresh(); case_id=6; vocab_size=257; eos_token_id=256;
max_new_tokens=1; seq_limit=16;
expected_ops=1; expected_outputs=1;
expected_ids[0]=1;
expected_generated[0]=254; expected_last[0]=1;
launch();
prompt(1,1);
frame(0,254,3,0);
success();
fresh(); case_id=7; vocab_size=257; eos_token_id=256;
max_new_tokens=3; seq_limit=16;
expected_ops=5; expected_outputs=3;
expected_ids[0]=2;
expected_ids[1]=4;
expected_ids[2]=6;
expected_ids[3]=9;
expected_ids[4]=10;
expected_generated[0]=9; expected_last[0]=0;
expected_generated[1]=10; expected_last[1]=0;
expected_generated[2]=11; expected_last[2]=1;
launch();
prompt(2,0);
prompt(4,0);
prompt(6,1);
frame(0,68,2,0);
frame(1,32,2,1);
frame(2,9,2,0);
frame(3,10,2,1);
frame(4,11,2,0);
success();
fresh(); case_id=8; vocab_size=257; eos_token_id=256;
max_new_tokens=3; seq_limit=16;
expected_ops=3; expected_outputs=1;
expected_ids[0]=2;
expected_ids[1]=4;
expected_ids[2]=9;
expected_generated[0]=9; expected_last[0]=0;
launch();
prompt(2,0);
prompt(4,1);
frame(0,130,2,0);
frame(1,9,2,1);
frame(2,256,2,0);
success();
fresh(); case_id=9; vocab_size=257; eos_token_id=256;
max_new_tokens=4; seq_limit=16;
expected_ops=2; expected_outputs=0;
expected_ids[0]=3;
expected_ids[1]=1;
launch();
prompt(3,0);
prompt(1,1);
frame(0,60,2,0);
frame(1,256,2,1);
success();
fresh(); case_id=10; vocab_size=128256; eos_token_id=128255;
max_new_tokens=1; seq_limit=16;
expected_ops=2; expected_outputs=1;
expected_ids[0]=1;
expected_ids[1]=2;
expected_generated[0]=128254; expected_last[0]=1;
launch();
prompt(1,0);
prompt(2,1);
frame(0,64937,2,0);
frame(1,128254,2,1);
success();
fresh(); case_id=11; vocab_size=151936; eos_token_id=151935;
max_new_tokens=1; seq_limit=16;
expected_ops=2; expected_outputs=1;
expected_ids[0]=1;
expected_ids[1]=2;
expected_generated[0]=151934; expected_last[0]=1;
launch();
prompt(1,0);
prompt(2,1);
frame(0,117831,2,0);
frame(1,151934,2,1);
success();
fresh(); case_id=12; vocab_size=262144; eos_token_id=262143;
max_new_tokens=1; seq_limit=16;
expected_ops=2; expected_outputs=1;
expected_ids[0]=1;
expected_ids[1]=2;
expected_generated[0]=262142; expected_last[0]=1;
launch();
prompt(1,0);
prompt(2,1);
frame(0,247592,2,0);
frame(1,262142,2,1);
success();
fresh(); case_id=13; vocab_size=1; eos_token_id=0;
max_new_tokens=0; seq_limit=4096;
expected_ops=4096; expected_outputs=0;
for (integer compact_index=0; compact_index<4096; compact_index=compact_index+1) expected_ids[compact_index]=0;
launch();
for (integer compact_index=0; compact_index<4095; compact_index=compact_index+1) prompt(0,0);
prompt(0,1);
for (integer compact_index=0; compact_index<4095; compact_index=compact_index+1) frame(compact_index,0,2,compact_index & 1);
frame(4095,0,0,1);
success();

fresh(); case_id=100; vocab_size=257; eos_token_id=256;
max_new_tokens=1; seq_limit=16; expected_ops=1; expected_outputs=0;
expected_ids[0]=0; launch(); prompt(0,1);
while (ops<1) tick();
@(negedge clk); #1; core_done=1;
failure(8'h21);


fresh(); case_id=101; vocab_size=257; eos_token_id=256;
max_new_tokens=1; seq_limit=16; expected_ops=1; expected_outputs=0;
expected_ids[0]=0; launch(); prompt(0,1);
while (ops<1) tick();
@(negedge clk); #1; core_logit_index=1; core_logit_valid=1;
failure(8'h21);


fresh(); case_id=102; vocab_size=257; eos_token_id=256;
max_new_tokens=1; seq_limit=16; expected_ops=1; expected_outputs=0;
expected_ids[0]=0; launch(); prompt(0,1);
while (ops<1) tick();
@(negedge clk); #1; core_error=1;
failure(8'h20);


fresh(); case_id=103; vocab_size=257; eos_token_id=256;
max_new_tokens=1; seq_limit=16; expected_ops=1; expected_outputs=0;
expected_ids[0]=0; launch(); prompt(0,1);
while (ops<1) tick();
@(negedge clk); #1; core_logit_index=257; core_logit_valid=1;
failure(8'h21);


fresh(); case_id=104; vocab_size=257; eos_token_id=256;
max_new_tokens=1; seq_limit=16; expected_ops=1; expected_outputs=0;
expected_ids[0]=0; launch(); prompt(0,1);
while (ops<1) tick();
@(negedge clk); #1; core_logit_index=0; core_logit_valid=1; core_done=1;
failure(8'h21);


fresh(); case_id=105; vocab_size=257; eos_token_id=256;
max_new_tokens=1; seq_limit=16; expected_ops=1; expected_outputs=0;
expected_ids[0]=0; launch(); prompt(0,1);
while (ops<1) tick();
@(negedge clk); #1; logit(0,-100,0); core_logit_index=0; core_logit_valid=1;
failure(8'h21);


fresh(); case_id=106; vocab_size=257; eos_token_id=256;
max_new_tokens=1; seq_limit=16; expected_ops=1; expected_outputs=0;
expected_ids[0]=0; launch(); prompt(0,1);
while (ops<1) tick();
@(negedge clk); #1; logit(0,-100,0); core_logit_index=2; core_logit_valid=1;
failure(8'h21);


fresh(); case_id=107; vocab_size=257; eos_token_id=256;
max_new_tokens=1; seq_limit=16; expected_ops=1; expected_outputs=0;
expected_ids[0]=0; launch(); prompt(0,1);
while (ops<1) tick();
@(negedge clk); #1; begin
integer j;
for (j=0;j<257;j=j+1) logit(j,-100,0);
core_logit_index=257; core_logit_valid=1;
end
failure(8'h21);


fresh(); case_id=200; vocab_size=0; eos_token_id=0; max_new_tokens=0; seq_limit=16;
expected_ops=0; expected_outputs=0; launch(); failure(8'h32);


fresh(); case_id=201; vocab_size=262145; eos_token_id=0; max_new_tokens=0; seq_limit=16;
expected_ops=0; expected_outputs=0; launch(); failure(8'h32);


fresh(); case_id=202; vocab_size=257; eos_token_id=257; max_new_tokens=0; seq_limit=16;
expected_ops=0; expected_outputs=0; launch(); failure(8'h32);


fresh(); case_id=203; vocab_size=257; eos_token_id=256; max_new_tokens=0; seq_limit=0;
expected_ops=0; expected_outputs=0; launch(); failure(8'h32);


fresh(); case_id=204; vocab_size=257; eos_token_id=256; max_new_tokens=0; seq_limit=16777216;
expected_ops=0; expected_outputs=0; launch(); failure(8'h32);


fresh(); case_id=205; vocab_size=257; eos_token_id=256; max_new_tokens=17; seq_limit=16;
expected_ops=0; expected_outputs=0; launch(); failure(8'h32);


fresh(); case_id=210; vocab_size=257; eos_token_id=256; max_new_tokens=1; seq_limit=16;
expected_ops=0; expected_outputs=0; launch(); prompt(257,1); failure(8'h11);
fresh(); case_id=211; vocab_size=257; eos_token_id=256; max_new_tokens=0; seq_limit=1;
expected_ops=0; expected_outputs=0; launch(); prompt(0,0); failure(8'h31);
fresh(); case_id=212; vocab_size=257; eos_token_id=256; max_new_tokens=1; seq_limit=16;
expected_ops=0; expected_outputs=0; launch();
@(negedge clk); #1; core_done=1; failure(8'h21);


fresh(); case_id=112; vocab_size=257; eos_token_id=256; max_new_tokens=2;
seq_limit=2; expected_ops=2; expected_outputs=1;
expected_ids[0]=1; expected_ids[1]=2;
expected_generated[0]=3; expected_last[0]=0;
launch(); prompt(1,0); prompt(2,1); frame(0,0,2,0); frame(1,3,2,1);
failure(8'h31);


fresh(); case_id=213; vocab_size=257; eos_token_id=256; max_new_tokens=0; seq_limit=4097;
expected_ops=0; expected_outputs=0; launch();
repeat (4096) prompt(0,0);
failure(8'h30);


fresh(); case_id=214; vocab_size=257; eos_token_id=256; max_new_tokens=1; seq_limit=16;
expected_ops=1; expected_outputs=0; expected_ids[0]=0;
launch(); prompt(0,1); while (ops<1) tick(); logit(0,-1,0);
fresh(); expected_ops=0; expected_outputs=0; repeat (10) tick();
if (ops!=0 || outputs!=0 || finishes!=0 || completions!=0 || error || busy)
  $fatal(1,"CONTROLLER_RESET_LOGIT_EPOCH");
comparisons=comparisons+1;

    if (token_stalls==0 || finish_stalls==0 ||
        (4096>1 && generated_stalls==0))
      $fatal(1,"CONTROLLER_STALL_COVERAGE");
    if (comparisons!=4203)
      $fatal(1,"CONTROLLER_COMPARE_COUNT actual=%0d",comparisons);
    $display("COMPARED %0d",comparisons);
    $finish;
  end
  initial begin
    repeat (12000000) @(posedge clk);
    $fatal(1,"CONTROLLER_CYCLE_BOUND case=%0d ops=%0d",case_id,ops);
  end
endmodule
