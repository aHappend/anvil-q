"""Compact startup/drain checks and intentional legal/illegal elaboration matrix."""

from execution import ROOT, relative


STARTUP_BENCH = r"""
module startup_tb;
  parameter B=1,Q=3,H=8,I=8,D=8,QH=2,KH=1,V=8,M=16;
  reg clk=0,rst_n,cancel=0,token_valid=0,new_sequence=0,token_phase=0;
  always #5 clk=~clk;
  reg [31:0] token_id=0,token_pos=0;
  reg logit_ready=0,commit_ready=0,draft_valid=1;
  wire token_ready,logit_valid,done,error,cancel_done;
  wire [31:0] logit_index,logit_data;
  wire [B-1:0] mem_req_valid,mem_req_write,mem_rsp_ready;
  reg [B-1:0] mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
  wire [B*4-1:0] mem_req_kind;
  wire [B*3-1:0] mem_req_proj;
  wire [B*32-1:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
  wire [B*64-1:0] mem_req_tag;
  reg [B*32-1:0] mem_rsp_rdata=0;
  reg [B*64-1:0] mem_rsp_tag=0;
  wire draft_ready,commit_valid,think_active,csr_ready,csr_rsp_valid,csr_error;
  wire [2:0] commit_count;
  wire [159:0] commit_tokens;
  wire [31:0] commit_pos,csr_rdata;
  reg [63:0] saved_tag;
  reg [B*200-1:0] saved_request;
  integer guard,b,selected,tests=0,stalls=0,drains=0,request_errors=0;
  anvil_qn1_top #(.COMPACT(1),.NUM_LAYERS(1),.HIDDEN_SIZE(H),
    .INTERMEDIATE_SIZE(I),.HEAD_DIM(D),.NUM_Q_HEADS(QH),.NUM_KV_HEADS(KH),
    .VOCAB_SIZE(V),.MAX_SEQ_LEN(M),.GROUP_SIZE(8),.BANKS(B),.QUEUE_DEPTH(Q)) dut(
    .clk(clk),.rst_n(rst_n),.cancel(cancel),.token_valid(token_valid),
    .new_sequence(new_sequence),.token_phase(token_phase),.token_id(token_id),
    .token_pos(token_pos),.token_ready(token_ready),.logit_valid(logit_valid),
    .logit_ready(logit_ready),.logit_index(logit_index),.logit_data(logit_data),
    .done(done),.error(error),.cancel_done(cancel_done),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),
    .mem_req_wdata(mem_req_wdata),.mem_req_tag(mem_req_tag),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_error(mem_rsp_error),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_tag(mem_rsp_tag),
    .draft_valid(draft_valid),.draft_ready(draft_ready),.draft_count(3'd1),
    .draft_tokens(128'd0),.draft_parents(12'd4),.commit_valid(commit_valid),
    .commit_ready(commit_ready),.commit_count(commit_count),.commit_tokens(commit_tokens),
    .commit_pos(commit_pos),.think_active(think_active),
    .csr_valid(1'b0),.csr_ready(csr_ready),.csr_write(1'b0),.csr_addr(12'd0),
    .csr_wdata(32'd0),.csr_wstrb(4'd0),.csr_rsp_valid(csr_rsp_valid),
    .csr_rsp_ready(1'b0),.csr_rdata(csr_rdata),.csr_error(csr_error));
  task reset_outputs;
    begin
      if ({token_ready,logit_valid,done,error,cancel_done,logit_index,logit_data,
           mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
           mem_req_row,mem_req_col,mem_req_wdata,mem_req_tag,mem_rsp_ready,
           draft_ready,commit_valid,commit_count,commit_tokens,commit_pos,think_active,
           csr_ready,csr_rsp_valid,csr_rdata,csr_error}!==0)
        $fatal(1,"STARTUP_RESET_XZ_OR_NONZERO");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_outputs();
  task tick;
    begin @(posedge clk);#1;@(negedge clk);#1;end
  endtask
  task no_publication;
    begin
      if (done!==0 || logit_valid!==0 || commit_valid!==0 || draft_ready!==0 ||
          think_active!==0) $fatal(1,"STARTUP_UNEXPECTED_PUBLICATION");
    end
  endtask
  task start;
    begin
      guard=0;
      while (token_ready!==1 && guard<100) begin tick();guard=guard+1;end
      if (token_ready!==1) $fatal(1,"STARTUP_READY");
      if (draft_ready!==0) $fatal(1,"IDLE_DRAFT_QUEUED");
      token_valid=1;new_sequence=1;
      @(posedge clk);
      if (token_ready!==1 || draft_ready!==0) $fatal(1,"STARTUP_TOKEN_HANDSHAKE");
      #1;if (token_ready!==0 || logit_valid!==0 || done!==0)
        $fatal(1,"STARTUP_TOKEN_ORDER");
      @(negedge clk);#1;token_valid=0;new_sequence=0;
      guard=0;
      while (mem_req_valid===0 && guard<100) begin tick();guard=guard+1;end
      if ((^mem_req_valid)===1'bx || mem_req_valid==0) $fatal(1,"STARTUP_NO_REQUEST");
      selected=-1;
      for (b=0;b<B;b=b+1) if (mem_req_valid[b]) begin
        if (selected!=-1 || mem_req_write[b]!==0 || mem_req_kind[b*4+:4]!==0 ||
            mem_req_layer[b*32+:32]!==0 || mem_req_row[b*32+:32]!==0 ||
            mem_req_col[b*32+:32]!==0)
          $fatal(1,"STARTUP_EMBEDDING_ADDRESS");
        selected=b;
      end
      saved_tag=mem_req_tag[selected*64+:64];
      saved_request={mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
                     mem_req_row,mem_req_col,mem_req_wdata,mem_req_tag};
      repeat (5) begin
        tick();no_publication();
        if (mem_req_valid!==(B'(1)<<selected) ||
            {mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
             mem_req_row,mem_req_col,mem_req_wdata,mem_req_tag}!==saved_request)
          $fatal(1,"STARTUP_REQUEST_STABILITY");
        stalls=stalls+1;
      end
      tests=tests+1;
    end
  endtask
  task wait_cancel;
    begin
      guard=0;
      while (cancel_done!==1 && guard<100) begin
        no_publication();if (error!==0) $fatal(1,"CANCEL_BECAME_ERROR");
        tick();guard=guard+1;
      end
      if (cancel_done!==1 || token_ready!==0) $fatal(1,"CANCEL_DRAIN_COMPLETION");
      tick();if (cancel_done!==0) $fatal(1,"DUPLICATE_CANCEL_DONE");
      drains=drains+1;
    end
  endtask
  task accept_request;
    begin
      mem_req_ready=B'(1)<<selected;
      @(posedge clk);
      if (!mem_req_valid[selected]) $fatal(1,"STARTUP_REQUEST_TRANSFER");
      #1;@(negedge clk);#1;mem_req_ready=0;
    end
  endtask
  initial begin
    rst_n=0;#1;reset_outputs();tick();rst_n=1;#1;
    start();
    cancel=1;#1;if (mem_req_valid!==0) $fatal(1,"CANCEL_UNACCEPTED_REQUEST");
    tick();cancel=0;wait_cancel();
    start();accept_request();
    cancel=1;tick();cancel=0;
    repeat (5) begin
      if (cancel_done!==0 || mem_req_valid!==0) $fatal(1,"EARLY_CANCEL_DRAIN");
      tick();
    end
    mem_rsp_valid=B'(1)<<selected;mem_rsp_tag[selected*64+:64]=saved_tag;
    mem_rsp_rdata[selected*32+:32]=32'h00003f80;
    guard=0;
    while (mem_rsp_ready[selected]!==1 && guard<100) begin tick();guard=guard+1;end
    if (mem_rsp_ready[selected]!==1) $fatal(1,"DRAIN_RESPONSE_NOT_READY");
    tick();mem_rsp_valid=0;wait_cancel();
    start();accept_request();
    mem_rsp_valid=B'(1)<<selected;mem_rsp_tag[selected*64+:64]=saved_tag;
    mem_rsp_error=B'(1)<<selected;
    guard=0;
    while (mem_rsp_ready[selected]!==1 && guard<100) begin tick();guard=guard+1;end
    if (mem_rsp_ready[selected]!==1) $fatal(1,"ERROR_RESPONSE_NOT_READY");
    tick();mem_rsp_valid=0;mem_rsp_error=0;
    guard=0;
    while (error!==1 && guard<100) begin no_publication();tick();guard=guard+1;end
    if (error!==1 || done!==0 || commit_valid!==0) $fatal(1,"READ_ERROR_NOT_VISIBLE");
    request_errors=request_errors+1;tick();
    start();accept_request();
    rst_n=0;#1;reset_outputs();tick();tick();rst_n=1;#1;
    if (mem_req_valid!==0 || logit_valid!==0 || commit_valid!==0)
      $fatal(1,"RESET_OWNERSHIP_LEAK");
    $display("SUMMARY startup_tests=%0d request_stalls=%0d cancel_drains=%0d read_errors=%0d reset_owned=1",
      tests,stalls,drains,request_errors);
    $finish;
  end
  initial begin repeat (500000) @(posedge clk);$fatal(1,"CYCLE_BOUND");end
endmodule
"""


def native_sources():
    return [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "rtl").glob("anvil_qn1_*.sv"))]


def run_startup(run, simulator="icarus", banks=1, queue=3, head_dim=8,
                q_heads=2, vocabulary=8, max_sequence=16):
    stem = f"startup-{simulator}-b{banks}-q{queue}-d{head_dim}-g{q_heads}-v{vocabulary}-m{max_sequence}"
    bench = run.path / f"{stem}.sv"
    bench.write_text(STARTUP_BENCH)
    parameters = {"B": banks, "Q": queue, "D": head_dim, "QH": q_heads,
                  "V": vocabulary, "M": max_sequence}
    if simulator == "icarus":
        binary = run.path / f"{stem}.vvp"
        run.execute(["iverilog", "-g2012", "-Wall", "-s", "startup_tb",
                     *[f"-Pstartup_tb.{k}={v}" for k, v in parameters.items()],
                     "-o", relative(binary), *native_sources(), relative(bench)],
                    f"{stem}-compile")
        argv = ["vvp", relative(binary)]
    else:
        objects = run.path / f"obj-{stem}"
        run.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                     "--top-module", "startup_tb",
                     *[f"-G{k}={v}" for k, v in parameters.items()],
                     "--Mdir", relative(objects), "-o", "simulate",
                     *native_sources(), relative(bench)], f"{stem}-compile")
        argv = [relative(objects / "simulate")]
    text = run.execute(argv, f"{stem}-simulation", timeout=600 if simulator == "icarus" else 2700)
    expected = ("SUMMARY startup_tests=4 request_stalls=20 cancel_drains=2 "
                "read_errors=1 reset_owned=1")
    if text.count(expected) != 1:
        raise AssertionError("startup public-pin coverage incomplete")
    return {"simulator": simulator, "banks": banks, "queue_depth": queue,
            "head_dim": head_dim, "gqa": q_heads, "vocabulary": vocabulary,
            "max_sequence": max_sequence, "raw_summary": expected}


def run_elaboration(run):
    native = native_sources()
    legal = []
    for profile in (1, 2, 3):
        run.execute(["iverilog", "-g2012", "-Wall", "-s", "anvil_qn1_top",
                     f"-Panvil_qn1_top.PROFILE={profile}", "-tnull", *native],
                    f"production-profile-{profile}-elaboration")
        legal.append({"profile": profile, "production": True})
    parent = sorted((ROOT / "anvil_q3_reference" / "rtl").glob("*.sv"))
    for file in parent:
        if file.read_bytes() != (ROOT / "rtl" / file.name).read_bytes():
            raise AssertionError(f"legacy delivered copy changed: {file.name}")
    run.execute(["iverilog", "-g2012", "-Wall", "-s", "anvil_q3_top", "-tnull",
                 *[relative(ROOT / "rtl" / p.name) for p in parent]], "legacy-elaboration")
    invalid = {
        "profile-zero": {"PROFILE": 0}, "profile-four": {"PROFILE": 4},
        "compact-mode": {"COMPACT": 2}, "zero-layer": {"NUM_LAYERS": 0},
        "negative-hidden": {"HIDDEN_SIZE": -8}, "zero-hidden": {"HIDDEN_SIZE": 0},
        "intermediate-align": {"INTERMEDIATE_SIZE": 9},
        "head-dimension": {"HEAD_DIM": 7}, "zero-head": {"HEAD_DIM": 0},
        "gqa-ratio": {"NUM_Q_HEADS": 3}, "zero-kv": {"NUM_KV_HEADS": 0},
        "bank-count": {"BANKS": 3}, "bank-zero": {"BANKS": 0},
        "queue-zero": {"QUEUE_DEPTH": 0}, "queue-seventeen": {"QUEUE_DEPTH": 17},
        "group-power": {"GROUP_SIZE": 7}, "group-divisibility": {"GROUP_SIZE": 16},
        "group-upper": {"GROUP_SIZE": 256}, "vocabulary-zero": {"VOCAB_SIZE": 0},
        "vocabulary-upper": {"VOCAB_SIZE": 151937},
        "sequence-zero": {"MAX_SEQ_LEN": 0}, "sequence-upper": {"MAX_SEQ_LEN": 40961},
        "production-override": {"COMPACT": 0, "HIDDEN_SIZE": 8},
        "address-overflow": {"HIDDEN_SIZE": 2147483640},
    }
    base = {"COMPACT": 1, "NUM_LAYERS": 1, "HIDDEN_SIZE": 8,
            "INTERMEDIATE_SIZE": 8, "NUM_Q_HEADS": 2, "NUM_KV_HEADS": 1,
            "HEAD_DIM": 8, "VOCAB_SIZE": 8, "MAX_SEQ_LEN": 16,
            "GROUP_SIZE": 8, "BANKS": 1, "QUEUE_DEPTH": 3}
    for name, overrides in invalid.items():
        params = {**base, **overrides}
        bench = run.path / f"illegal-{name}.sv"
        bench.write_text("module illegal_tb;\n anvil_qn1_top #(" +
                         ",".join(f".{k}({v})" for k, v in params.items()) +
                         ') dut();\n initial begin #5;$fatal(1,"MISSING_PARAMETER_ERROR");end\nendmodule\n')
        binary = run.path / f"illegal-{name}.vvp"
        run.execute(["iverilog", "-g2012", "-Wall", "-s", "illegal_tb", "-o",
                     relative(binary), *native, relative(bench)], f"illegal-{name}-compile")
        text = run.execute(["vvp", relative(binary)], f"illegal-{name}-diagnostic",
                           timeout=600, expected_exit=1)
        if "ANVIL_QN1 PARAMETER ERROR" not in text or "MISSING_PARAMETER_ERROR" in text:
            raise AssertionError(f"intentional diagnostic missing: {name}")
    return {"native_production_elaborations": legal, "legacy_copies": len(parent),
            "illegal_diagnostics": list(invalid)}


def run_smoke(run):
    from leaf_checks import run_qk, run_tensor, run_scalar
    from control_checks import run_csr, run_controller

    results = {"elaboration": run_elaboration(run), "startup": [], "leaves": {}}
    matrix = [(bank, queue, 8, 2, 8, 16)
              for bank in (1, 8) for queue in (1, 3, 16)]
    matrix += [(1, 1, 8, 4, 1, 1), (8, 3, 128, 4, 8, 16)]
    for bank, queue, dimension, heads, vocab, length in matrix:
        results["startup"].append(run_startup(
            run, banks=bank, queue=queue, head_dim=dimension, q_heads=heads,
            vocabulary=vocab, max_sequence=length))
    results["startup"].append(run.component(
        "smoke-startup-compiled",
        lambda child: run_startup(child, "verilator", vocabulary=1, max_sequence=1)))
    for simulator in ("icarus", "verilator"):
        for name, operation in (
                ("scalar", lambda child, s=simulator: run_scalar(child, s)),
                ("qk", lambda child, s=simulator: run_qk(child, s)),
                ("tensor", lambda child, s=simulator: run_tensor(child, s)),
                ("csr", lambda child, s=simulator: run_csr(child, s))):
            results["leaves"][f"{name}-{simulator}"] = run.component(
                f"smoke-{name}-{simulator}", operation)
    results["controller"] = run.component("smoke-controller", run_controller)
    if len(results["startup"]) != 9 or len(results["leaves"]) != 8:
        raise AssertionError("smoke matrix incomplete")
    for leaf in ("scalar", "qk", "tensor"):
        key = {"scalar": "scalar_cases", "qk": "qk_cases", "tensor": "tensor_cases"}[leaf]
        left = results["leaves"][f"{leaf}-icarus"].get(key)
        right = results["leaves"][f"{leaf}-verilator"].get(key)
        if left is None or not left or left != right:
            raise AssertionError(f"dual-simulator {leaf} vector coverage mismatch")
    return results
