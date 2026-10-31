"""Public Avalon/CSR/token tests against a separately computed decoder."""

from pathlib import Path

from decoder_reference import Decoder, Geometry, Image
from evidence import ROOT, relative, write_json
import ieee_reference as fp
from leaf_checks import simulate


def fixture(directory, geometry, mode, seed):
    image = Image(geometry, mode, seed)
    memory = directory / "memory.hex"
    memory.write_text("".join(
        f"{int.from_bytes(image.memory[i:i + 64], 'little'):0128x}\n"
        for i in range(0, len(image.memory), 64)))
    descriptors = directory / "descriptors.txt"
    descriptors.write_text("".join(" ".join(f"{word:x}" for word in descriptor) + "\n"
                                   for descriptor in image.descriptors))
    native, mathematical = Decoder(image), Decoder(image, fp64=True)
    native_prefix, wide_prefix = [], []
    tokens, expected = [], []
    token = min(3, geometry.vocabulary - 1)
    for position in range(min(5, geometry.sequence)):
        logits, target, state = native.token(token, position, native_prefix)
        wide_logits, _, wide_state = mathematical.token(token, position, wide_prefix)
        native_prefix.append(state)
        wide_prefix.append(wide_state)
        tokens.append(token)
        expected.append(logits)
        token = target
    metrics = []
    for (name, observed), (wide_name, wide) in zip(native.observations, mathematical.observations):
        if name != wide_name:
            raise AssertionError("independent observation boundary mismatch")
        metric = fp.fidelity([fp.as_float(v) for v in observed], wide)
        if metric["nrmse"] > .02 or metric["cosine"] < .999:
            raise AssertionError(f"FP64 boundary {name}: {metric}")
        if all(v == 0 for v in wide) and metric["max_absolute_error"] > 2 ** -18:
            raise AssertionError("zero-reference error")
        metrics.append({"boundary": name, **metric})
    write_json(directory / "reference.json", {
        "geometry": geometry.__dict__, "mode": mode, "seed": seed,
        "tokens": tokens, "expected_logits": expected, "fp64_fidelity": metrics,
        "scope": "seeded compact tensors, not the official model",
    })
    return image, tokens, expected


TOP_PINS = r"""
  reg ddr_clk=0;
  always #7 ddr_clk=~ddr_clk;
  reg token_valid=0, new_sequence=0, logit_ready=0;
  wire token_ready, logit_valid, done, error;
  reg [31:0] token_id=0, token_pos=0;
  wire [31:0] logit_index,logit_data;
  reg csr_valid=0,csr_write=0,csr_rsp_ready=0;
  reg [15:0] csr_address=0;
  reg [31:0] csr_wdata=0;
  wire csr_ready,csr_rsp_valid,csr_error;
  wire [31:0] csr_rdata;
  reg load_valid=0,load_last=0;
  reg [32:0] load_address=0;
  reg [511:0] load_data=0;
  reg [63:0] load_byteenable=0;
  wire load_ready,load_done,load_error;
  wire [32:0] avm_address;
  wire [7:0] avm_burstcount;
  wire avm_read,avm_write;
  wire [511:0] avm_writedata;
  wire [63:0] avm_byteenable;
  reg avm_waitrequest=0,avm_readdatavalid=0,avm_writeresponsevalid=0;
  reg [511:0] avm_readdata=0;
  reg [1:0] avm_response=0;
  reg batch_valid=0,commit_ready=0;
  wire batch_ready,commit_valid,commit_error;
  reg [2:0] batch_count=0;
  reg [127:0] batch_token_ids=0;
  reg [11:0] batch_parents=0;
  wire [2:0] commit_count;
  wire [127:0] commit_token_ids;
  wire [31:0] commit_position;
  anvil_q1_ht2_top #(
    PARAMETERS
  ) dut(.*);
  task reset_check;
    begin
      if ({token_ready,logit_valid,logit_index,logit_data,done,error,csr_ready,
           csr_rsp_valid,csr_rdata,csr_error,load_ready,load_done,load_error,avm_address,
           avm_burstcount,avm_read,avm_write,avm_writedata,avm_byteenable,batch_ready,
           commit_valid,commit_count,commit_token_ids,commit_position,commit_error} !== 0)
        $fatal(1,"RESET_OUTPUT_XZ");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(posedge ddr_clk or negedge ddr_clk) if (!rst_n) reset_check();
"""

MEMORY = r"""
  reg [511:0] memory[0:MEMORY_WORDS-1];
  integer beats_left=0,read_index=0,write_pending=0,bus_cycles=0;
  integer reads=0,writes=0,byte_index;
  reg [617:0] previous_request=0;
  reg request_stalled=0;
  initial $readmemh("MEMORY_PATH",memory);
  always @(posedge ddr_clk) begin
    if (request_stalled && {avm_write,avm_address,avm_burstcount,avm_writedata,avm_byteenable}
        !== previous_request) $fatal(1,"AVALON_STABILITY");
    request_stalled=(avm_read || avm_write) && avm_waitrequest;
    previous_request={avm_write,avm_address,avm_burstcount,avm_writedata,avm_byteenable};
    if ((avm_read || avm_write) && !avm_waitrequest) begin
      if (avm_read && avm_write) $fatal(1,"AVALON_READ_WRITE");
      if (beats_left!=0 || write_pending!=0 || avm_burstcount==0 ||
          avm_address[5:0]!=0 || (avm_address>>6)+avm_burstcount>MEMORY_WORDS)
        $fatal(1,"AVALON_ADDRESS address=%h beats=%0d",avm_address,avm_burstcount);
      if (avm_read) begin
        read_index=avm_address>>6; beats_left=avm_burstcount;
      end else begin
        if (avm_burstcount!=1) $fatal(1,"WRITE_BURST");
        for (byte_index=0;byte_index<64;byte_index=byte_index+1)
          if (avm_byteenable[byte_index])
            memory[avm_address>>6][8*byte_index+:8]=avm_writedata[8*byte_index+:8];
        write_pending=1; writes=writes+1;
      end
    end
    if (avm_readdatavalid) reads=reads+1;
  end
  always @(negedge ddr_clk) begin
    bus_cycles=bus_cycles+1;
    avm_waitrequest=(bus_cycles%7==2 || bus_cycles%7==3);
    avm_readdatavalid=0; avm_writeresponsevalid=0;
    if (beats_left!=0 && bus_cycles%5!=1) begin
      avm_readdatavalid=1; avm_readdata=memory[read_index];
      read_index=read_index+1; beats_left=beats_left-1;
    end
    if (write_pending!=0) begin avm_writeresponsevalid=1; write_pending=0; end
  end
"""

CSR_TASK = r"""
  integer csr_calls=0,age,held;
  reg [31:0] response;
  reg response_error;
  task automatic csr(input wr,input [15:0] address,input [31:0] data,
                     input expect_error,input compare,input [31:0] expected);
    integer wait_cycles,i;
    reg [31:0] held_data;
    reg held_error;
    begin
      @(negedge clk); csr_valid=1; csr_write=wr; csr_address=address; csr_wdata=data;
      csr_rsp_ready=0; wait_cycles=0;
      begin : accept_csr
        forever begin
          @(posedge clk);
          if (csr_ready===1) begin #1; disable accept_csr; end
          #1; wait_cycles=wait_cycles+1;
          if (wait_cycles>50000) $fatal(1,"CSR_ADMISSION");
        end
      end
      @(negedge clk); csr_valid=0; wait_cycles=0;
      while (csr_rsp_valid!==1) begin
        tick(); wait_cycles=wait_cycles+1;
        if (wait_cycles>100000) $fatal(1,"CSR_COMPLETION address=%h",address);
      end
      held_data=csr_rdata; held_error=csr_error;
      for (i=0;i<3;i=i+1) begin
        tick();
        if ({csr_rsp_valid,csr_rdata,csr_error} !== {1'b1,held_data,held_error})
          $fatal(1,"CSR_RESPONSE_STABILITY");
      end
      if (held_error!==expect_error || (compare && held_data!==expected))
        $fatal(1,"CSR_COMPARE address=%h data=%h error=%b expected=%h/%b",
               address,held_data,held_error,expected,expect_error);
      response=held_data; response_error=held_error;
      checked=checked+1; csr_calls=csr_calls+1;
      @(negedge clk); csr_rsp_ready=1; tick();
      @(negedge clk); csr_rsp_ready=0; tick();
    end
  endtask
"""


def top(directory, simulator="verilator", geometry=Geometry(), mode=0, seed=17, batch=True,
        startup=False, threshold=0):
    image, tokens, logits = fixture(directory, geometry, mode, seed)
    parameters = ",\n".join(f".{key}({value})" for key, value in geometry.parameters().items())
    setup = r"""
  integer descriptor_index,kind,layer,projection,base,length,descriptors_read=0;
  integer received=0,result_stalls=0,commits=0;
  reg [31:0] expected[0:VOCAB-1];
  reg [31:0] expected_tokens[0:4];
  initial begin
    INITIAL_RESET_CHECK
    repeat(4) tick(); @(negedge clk); rst_n=1;
    repeat(500) tick();
    csr(0,16'h100,0,0,1,0);
    csr(1,16'h100,CONFIG,0,0,0);
    csr(1,16'h104,THRESHOLD,0,0,0);
    fd=$fopen("DESCRIPTORS","r");
    if (!fd) $fatal(1,"FIXTURE_OPEN");
    while (!$feof(fd)) begin
      rc=$fscanf(fd,"%h %h %h %h %h %h\n",descriptor_index,kind,layer,projection,base,length);
      if (rc!=6) $fatal(1,"FIXTURE_PARSE");
      csr(1,16'h10,descriptor_index,0,0,0);
      csr(1,16'h14,kind,0,0,0);
      csr(1,16'h18,layer,0,0,0);
      csr(1,16'h1c,projection,0,0,0);
      csr(1,16'h20,base,0,0,0);
      csr(1,16'h24,0,0,0,0);
      csr(1,16'h28,length,0,0,0);
      csr(1,16'h2c,1,0,0,0);
      csr(0,16'h28,0,0,1,length);
      descriptors_read=descriptors_read+1;
    end
    $fclose(fd);
    if (descriptors_read!=DESCRIPTOR_COUNT) $fatal(1,"DESCRIPTOR_COVERAGE");
    csr(1,16'h8,6,0,0,0);
    repeat(100) tick();
    csr(0,16'h108,0,0,1,3);
    EXPECTED_LOGITS
    @(negedge clk); token_id=INITIAL_TOKEN; token_pos=0; token_valid=1;
    begin : token_accept
      forever begin @(posedge clk); if (token_ready===1) begin #1; disable token_accept; end end
    end
    @(negedge clk); token_valid=0; age=0;
    while (done!==1) begin
      logit_ready=(age%7<3);
      @(posedge clk);
      if (logit_valid===1) begin
        if (received>=VOCAB || {logit_index,logit_data} !== {32'(received),expected[received]})
          $fatal(1,"TOP_LOGIT index=%0d got=%h expected=%h received=%0d",
                 logit_index,logit_data,expected[received],received);
        checked=checked+1;
        if (logit_ready) received=received+1; else result_stalls=result_stalls+1;
        if (done!==0) $fatal(1,"DONE_EARLY");
      end else if (logit_valid!==0) $fatal(1,"LOGIT_VALID_XZ");
      #1; age=age+1; cycles=cycles+1;
      if (age>150000) $fatal(1,"TOKEN_COMPLETION");
      @(negedge clk);
    end
    if (error!==0 || received!=VOCAB || result_stalls==0) $fatal(1,"TOKEN_RESULT");
    logit_ready=0; tick(); tick();
    csr(0,16'h110,0,0,1,1);
    csr(0,16'h114,0,0,1,0);
    BATCH_BODY
    csr(0,16'h120,0,0,1,reads*64);
    csr(0,16'h124,0,0,1,0);
    csr(0,16'h128,0,0,1,DENSE_BYTES);
    csr(0,16'h12c,0,0,1,0);
    if (reads==0 || writes==0) $fatal(1,"DDR_CONNECTIVITY");
    $display("CHECK compared=%0d logits=%0d commits=%0d read_beats=%0d write_beats=%0d csr=%0d",
             checked,received,commits,reads,writes,csr_calls);
    $finish;
  end
"""
    batch_body = r"""
    EXPECTED_TOKENS
    @(negedge clk); batch_count=4; batch_parents={3'd2,3'd1,3'd0,3'd4};
    batch_token_ids={expected_tokens[4],expected_tokens[3],expected_tokens[2],expected_tokens[1]};
    batch_valid=1;
    begin : batch_accept
      forever begin @(posedge clk); if (batch_ready===1) begin #1; disable batch_accept; end end
    end
    @(negedge clk); batch_valid=0; age=0; held=0; commit_ready=0;
    while (done!==1) begin
      @(posedge clk);
      if (logit_valid!==0) $fatal(1,"BATCH_BRANCH_LOGIT");
      if (commit_valid===1) begin
        if ({commit_count,commit_token_ids,commit_position,commit_error} !==
            {3'd4,expected_tokens[4],expected_tokens[3],expected_tokens[2],expected_tokens[1],
             32'd1,1'b0}) $fatal(1,"TOP_COMMIT");
        held=held+1; checked=checked+1;
        if (commit_ready) commits=commits+1;
        if (done!==0) $fatal(1,"BATCH_DONE_EARLY");
      end else if (commit_valid!==0) $fatal(1,"COMMIT_VALID_XZ");
      #1; age=age+1; cycles=cycles+1;
      if (age>250000) $fatal(1,"BATCH_COMPLETION");
      @(negedge clk); if (held>=5) commit_ready=1;
    end
    if (error!==0 || commits!=1 || held<5) $fatal(1,"BATCH_RESULT");
    commit_ready=0; tick(); tick();
    csr(0,16'h110,0,0,1,5);
    csr(0,16'h114,0,0,1,0);
    csr(0,16'h118,0,0,1,1);
    csr(0,16'h11c,0,0,1,0);
"""
    setup = setup.replace("BATCH_BODY", batch_body if batch and geometry.sequence >= 5 else "")
    setup = setup.replace("EXPECTED_TOKENS", "\n".join(
        f"expected_tokens[{i}]=32'h{token:08x};" for i, token in enumerate(tokens)))
    setup = setup.replace("EXPECTED_LOGITS", "\n".join(
        f"expected[{i}]=32'h{word:08x};" for i, word in enumerate(logits[0])))
    replacements = {
        "INITIAL_RESET_CHECK": "#1; reset_check();" if simulator == "verilator" else "#0; reset_check();",
        "VOCAB": str(geometry.vocabulary), "CONFIG": str(mode | (12 if batch else 0)),
        "INITIAL_TOKEN": str(tokens[0]), "DESCRIPTORS": relative(directory / "descriptors.txt"),
        "DESCRIPTOR_COUNT": str(len(image.descriptors)),
        "THRESHOLD": str(threshold),
        "DENSE_BYTES": str(geometry.layers * geometry.intermediate *
                           ((geometry.hidden + 63) // 64) * (64 if mode == 2 else 128) *
                           (2 if batch and geometry.sequence >= 5 else 1)),
    }
    for key, value in replacements.items():
        setup = setup.replace(key, value)
    if startup:
        setup = r"""
  initial begin
    INITIAL_CHECK
    repeat(4) tick(); @(negedge clk); rst_n=1; repeat(500) tick();
    csr(0,16'h0,0,0,1,32'h02000001);
    csr(0,16'h100,0,0,1,0);
    csr(0,16'h104,0,0,1,0);
    csr(0,16'h108,0,0,1,1);
    csr(0,16'h10c,0,0,1,0);
    csr(0,16'h138,0,0,1,0);
    csr(1,16'h10c,1,1,1,0);
    csr(0,16'h114,0,1,1,0);
    csr(0,16'h110,0,0,1,0);
    csr(0,16'h114,0,0,1,0);
    csr(0,16'h114,0,1,1,0);
    csr(0,16'h120,0,0,1,0);
    csr(0,16'h124,0,0,1,0);
    csr(1,16'h8,4,0,0,0); repeat(100) tick();
    @(negedge clk); #2; rst_n=0;
    #1; reset_check(); repeat(4) tick();
    @(negedge clk); rst_n=1; repeat(500) tick();
    csr(0,16'h100,0,0,1,0);
    if (reads!=0 || writes!=0) $fatal(1,"STARTUP_UNSOLICITED_MEMORY");
    $display("CHECK compared=%0d csr=%0d startup_only=1",checked,csr_calls);
    $finish;
  end
""".replace("INITIAL_CHECK", "#1; reset_check();" if simulator == "verilator" else "#0; reset_check();")
    body = (TOP_PINS.replace("PARAMETERS", parameters) +
            MEMORY.replace("MEMORY_WORDS", str(len(image.memory) // 64)).replace(
                "MEMORY_PATH", relative(directory / "memory.hex")) + CSR_TASK + setup)
    modules = [path.stem.removeprefix("anvil_q1_ht2_")
               for path in sorted((ROOT / "rtl").glob("anvil_q1_ht2_*.sv"))]
    return simulate(directory, f"top-{'startup-' if startup else ''}{mode}-{seed}-{simulator}",
                    body, modules, simulator)
