"""Public-pin interaction cases; synthetic assets do not certify official models."""

import hashlib
import json


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise RuntimeError(f"Interaction bench has no unique anchor: {before[:80]}")
    return text.replace(before, after, 1)


def top_interaction_bench(evidence, bench, fixture, prompt, operations, kind, uart):
    from storage import synthetic_image, top_control_scenario

    bench = top_control_scenario(
        bench, fixture, prompt, None, 0, None, False, uart, operations, "")
    if uart:
        exchange = """
    fork
      begin
        @(negedge clk); #1; send_serial(65); send_serial(66);
        send_serial(67); send_serial(10);
      end
      begin decode_serial(); decode_serial(); end
      begin
        while (uart_tx!==0 && !error) tick();
        if (error || !busy || done || outputs || completions)
          $fatal(1,"TOP_CONTROL_UART_DRAIN_EVENT");
        allow_controls=1;
        control(1,32'h04,7,1,0);
        control(1,32'h10,1,1,0);
        control(1,32'h24,3,1,0);
        blocked_prompt();
        if (!busy || done || error || completions)
          $fatal(1,"TOP_CONTROL_UART_EARLY_COMPLETE");
        allow_controls=0; interaction_events=interaction_events+1;
      end
    join
"""
    else:
        exchange = """
    block_output=1;
    send_byte(65,0); send_byte(66,0); send_byte(67,1);
    while (!m_axis_tvalid && !error) tick();
    if (error || !busy || done || outputs || completions || s_axis_tready ||
        m_axis_tdata!==0 || m_axis_tready)
      $fatal(1,"TOP_CONTROL_AXIS_DRAIN_EVENT");
    allow_controls=1;
    control(1,32'h04,7,1,0);
    control(1,32'h10,0,1,0);
    control(1,32'h24,3,1,0);
    control(1,32'h1c,1,1,0);
    control(0,32'h04,0,0,5);
    control(0,32'h10,0,0,1);
    control(0,32'h24,0,0,0);
    blocked_prompt();
    repeat (10) begin
      tick();
      if (!m_axis_tvalid || m_axis_tdata!==0 || m_axis_tready ||
          outputs || completions || done || error || !busy || s_axis_tready)
        $fatal(1,"TOP_CONTROL_AXIS_DRAIN_HOLD");
    end
    allow_controls=0; interaction_events=interaction_events+1;
    @(negedge clk); #1; block_output=0;
"""
    success = f"""
    while (completions==0 && !error) tick();
    repeat (20) tick();
    if (completions!=1 || outputs!=2 || error || pending || busy ||
        cache_k_writes!={operations*8} || cache_v_writes!={operations*8} ||
        embedding_reads!={operations*(fixture['capacity']*8+8)})
      $fatal(1,"TOP_INTERACTION_INFERENCE_COUNTS");
    comparisons=comparisons+1;
"""
    if kind == "serial-drain":
        bench = replace_once(bench, "  reg running=0,out_held=0;", """
  reg running=0,out_held=0;
  reg allow_controls=0,block_output=0;
  integer interaction_events=0,rejected_prompt_edges=0;
  task automatic blocked_prompt;
    begin
      @(negedge clk); #1;
      s_axis_tvalid=1; s_axis_tdata=8'h5a; s_axis_tlast=1;
      repeat (8) begin
        @(posedge clk);
        if (s_axis_tready!==0 || !busy || done || error)
          $fatal(1,"TOP_DRAIN_PROMPT_ADMITTED");
        rejected_prompt_edges=rejected_prompt_edges+1;
        #1;
      end
      @(negedge clk); #1; s_axis_tvalid=0;
    end
  endtask
""")
        bench = replace_once(
            bench, 'if (cfg_valid || cfg_write) $fatal(1,"TOP_HOST_INTERVENTION");',
            'if ((cfg_valid || cfg_write) && !allow_controls) '
            '$fatal(1,"TOP_HOST_INTERVENTION");')
        bench = replace_once(
            bench, "m_axis_tready=rng[3] && cycle%7!=0;",
            "m_axis_tready=!block_output && rng[3] && cycle%7!=0;")
        scenario = "    running=1;\n" + exchange + success + f"""
    running=0;
    control(0,32'h04,0,0,5);
    control(0,32'h10,0,0,{int(not uart)});
    control(0,32'h24,0,0,0);
    control(1,32'h04,7,0,0);
    control(0,32'h04,0,0,7);
    control(1,32'h10,{int(uart)},0,0);
    control(0,32'h10,0,0,{int(uart)});
    control(1,32'h24,3,0,0);
    control(0,32'h24,0,0,3);
    if (interaction_events!=1 || rejected_prompt_edges!=8 ||
        control_requests!=control_responses ||
        error || !boot_done || completions!=1 || outputs!=2)
      $fatal(1,"TOP_SERIAL_UPDATE_CONSERVATION");
    comparisons=comparisons+1;
    $display("TOP_INTERACTION serial_drain=1 controls=%0d",control_responses);
"""
    elif kind == "uart-drain-prompt":
        if not uart:
            raise ValueError("Physical drain prompt rejection requires UART")
        bench = replace_once(
            bench,
            """    if (expect_rejection && (embedding_reads!=0 || inference_writes!=0 ||
                            m_axis_tvalid || done || uart_tx!==1))""",
            """    if (expect_rejection && (m_axis_tvalid || done))""")
        scenario = f"""
    running=1;
    @(negedge clk); #1;
    send_serial(65); send_serial(66); send_serial(67); send_serial(10);
    while (uart_tx!==0 && !error) tick();
    if (error || !busy || done || outputs || completions || s_axis_tready)
      $fatal(1,"TOP_UART_DRAIN_PROMPT_EVENT");
    expect_rejection=1;
    fork
      begin decode_serial(); decode_serial(); end
      begin
        @(negedge clk); #1; send_serial(90);
        while (!error) tick();
        if (error_code!==8'h41 || busy || done || !boot_done || completions)
          $fatal(1,"TOP_UART_DRAIN_PROMPT_ERROR code=%h",error_code);
      end
    join
    repeat (30) begin
      tick();
      if (!error || error_code!==8'h41 || busy || done || !boot_done ||
          s_axis_tready || m_axis_tvalid || uart_tx!==1 || outputs!=2 || completions)
        $fatal(1,"TOP_UART_DRAIN_PROMPT_REJECTION code=%h",error_code);
    end
    if (pending || ddr_req_valid ||
        cache_k_writes!={operations*8} || cache_v_writes!={operations*8} ||
        embedding_reads!={operations*(fixture['capacity']*8+8)})
      $fatal(1,"TOP_UART_DRAIN_PROMPT_EXTRA_OPERATION");
    running=0;
    control(0,32'h20,0,0,32'h41);
    control(0,0,0,0,9);
    if (control_requests!=control_responses)
      $fatal(1,"TOP_UART_DRAIN_PROMPT_CONTROL_CONSERVATION");
    comparisons=comparisons+1;
    $display("TOP_INTERACTION uart_drain_prompt_rejected=1 no_successful_completion=1");
"""
    elif kind == "memory-transport-priority":
        if not uart:
            raise ValueError("Memory/transport coincidence requires physical UART")
        bench = replace_once(bench, "  reg running=0,out_held=0;", """
  reg running=0,out_held=0;
  reg block_response=0,witness_rst_n=0;
  wire witness_overflow;
  integer fault_collisions=0;
  anvil_edge_uart_io #(.RX_FIFO_DEPTH(3),.TX_FIFO_DEPTH(3),.FRAME_LOCK(1))
    transport_event_witness(
      .clk(clk),.rst_n(witness_rst_n),.uart_rx(uart_rx),.uart_tx(),
      .divisor(32'd5),.axis_bypass(1'b0),.uart_frame_bytes(32'd0),
      .s_axis_tvalid(1'b0),.s_axis_tready(),.s_axis_tdata(8'd0),.s_axis_tlast(1'b0),
      .m_axis_tvalid(),.m_axis_tready(1'b0),.m_axis_tdata(),.m_axis_tlast(),
      .rx_valid(),.rx_ready(1'b0),.rx_data(),.rx_last(),
      .tx_valid(1'b0),.tx_ready(),.tx_data(8'd0),.tx_last(1'b0),
      .framing_error(),.overflow_error(witness_overflow),
      .rx_idle(),.tx_idle(),.rx_line_idle(),
      .receive_enable(1'b0),.response_complete(1'b0));
""")
        bench = replace_once(bench, "if (pending && !ddr_rsp_valid) begin",
                             "if (pending && !ddr_rsp_valid && !block_response) begin")
        # This second public-port instance times the deliberately closed RX event,
        # not the expected result. The independent priority rule requires code 04.
        scenario = """
    running=1; block_response=1;
    @(negedge clk); #1;
    send_serial(65); send_serial(66); send_serial(67); send_serial(10);
    while (!pending && !error) tick();
    if (error || !busy || embedding_reads || outputs || completions || ddr_rsp_valid)
      $fatal(1,"TOP_PRIORITY_PENDING_EVENT");
    @(negedge clk); #1; witness_rst_n=1;
    repeat (8) tick();
    expect_rejection=1;
    fork
      begin
        @(negedge clk); #1; send_serial(90);
      end
      begin
        while (!witness_overflow && !error) tick();
        if (error || witness_overflow!==1 || !pending || ddr_rsp_valid)
          $fatal(1,"TOP_PRIORITY_PREMATURE_ERROR");
        @(negedge clk); #1;
        ddr_rsp_valid=1; ddr_rsp_error=1;
        ddr_rsp_rdata={ddr[pending_address+3],ddr[pending_address+2],
                       ddr[pending_address+1],ddr[pending_address]};
        @(posedge clk);
        $display("TOP_PRIORITY_COLLISION cycle=%0d addr=%h valid=%b ready=%b bus_error=%b transport=%b prior_error=%b",
                 cycle,pending_address,ddr_rsp_valid,ddr_rsp_ready,
                 ddr_rsp_error,witness_overflow,error);
        if (witness_overflow!==1 || ddr_rsp_valid!==1 || ddr_rsp_ready!==1 ||
            ddr_rsp_error!==1 || error!==0)
          $fatal(1,"TOP_PRIORITY_NO_COINCIDENCE");
        fault_collisions=fault_collisions+1;
        #1;
        if (error!==1 || error_code!==8'h04 || done)
          $fatal(1,"TOP_PRIORITY_WINNER expected=04 observed=%h",error_code);
        @(negedge clk); #1; ddr_rsp_error=0;
      end
    join
    repeat (20) begin
      tick();
      if (!error || error_code!==8'h04 || done || busy || !boot_done ||
          pending || ddr_req_valid || outputs || completions || embedding_reads ||
          inference_writes || m_axis_tvalid || uart_tx!==1)
        $fatal(1,"TOP_PRIORITY_STICKY_FIRST_ERROR");
    end
    running=0;
    control(0,32'h20,0,0,4);
    control(0,0,0,0,9);
    if (fault_collisions!=1 || control_requests!=control_responses)
      $fatal(1,"TOP_PRIORITY_CONSERVATION");
    comparisons=comparisons+1;
    $display("TOP_INTERACTION memory_transport_priority=1");
"""
    elif kind == "semantic-failed-reload":
        if uart:
            raise ValueError("Semantic reload case uses bypass admission")
        second = synthetic_image(
            257, max_pretoken=16, transport=1, fault="reserved-token")
        if (second["destinations"] != fixture["destinations"] or
                len(second["writes"]) != len(fixture["writes"])):
            raise RuntimeError("Semantic failed reload unexpectedly changed storage layout")
        path = evidence.path / "semantic-reload.hex"
        path.write_text("".join(f"{byte:02x}\n" for byte in second["image"]), encoding="ascii")
        (evidence.path / "semantic-reload-reference.json").write_text(json.dumps({
            "image_sha256": hashlib.sha256(second["image"]).hexdigest(),
            "fault": "reserved-token", "expected_error": 6,
            "recomputed_payload_crcs": True,
            "expected_ddr_writes": second["writes"],
            "scope": "Semantic rejection after all replacement payload writes; no old bundle reuse",
        }, indent=2) + "\n", encoding="ascii")
        updates = []
        for index, (old, new) in enumerate(zip(fixture["writes"], second["writes"])):
            if old[0] != new[0] or old[2] != new[2]:
                raise RuntimeError("Semantic reload address/strobe layout changed")
            if old[1] != new[1]:
                updates.append(f"write_data[{index}]=32'h{new[1]:x};")
        bench = replace_once(bench, "  reg running=0,out_held=0;", """
  reg running=0,out_held=0;
  reg failed_reload=0;
  integer rejected_prompt_edges=0;
  always @(posedge clk) if (rst_n && failed_reload) begin
    if (boot_done || !error || error_code!==8'h06 || done || busy ||
        s_axis_tready || m_axis_tvalid || uart_tx!==1 || ddr_req_valid ||
        outputs!=2 || completions!=1 || cfg_valid)
      $fatal(1,"TOP_SEMANTIC_RELOAD_OLD_IMAGE_EXPOSED");
    if (s_axis_tvalid) rejected_prompt_edges=rejected_prompt_edges+1;
  end
""")
        # Use the original ordinary exchange, without the output-stall scenario.
        original_exchange = "    send_byte(65,0); send_byte(66,0); send_byte(67,1);\n"
        scenario = "    running=1;\n" + original_exchange + success + f"""
    running=0;
    $readmemh("{evidence.relative(path)}",flash,0,{len(second['image'])-1});
    {''.join(updates)}
    writes=0; reads=0; acknowledgements=0; loading=1;
    control(1,32'h1c,1,0,0);
    if (boot_done || error || s_axis_tready || done)
      $fatal(1,"TOP_SEMANTIC_RELOAD_NOT_WITHDRAWN");
    while (!error && !boot_done) tick();
    if (!error || boot_done || error_code!==8'h06 || pending ||
        writes!={len(second['writes'])} || reads==0 ||
        acknowledgements!=writes+reads || outputs!=2 || completions!=1)
      $fatal(1,"TOP_SEMANTIC_RELOAD_REJECTION");
    control(0,32'h20,0,0,6);
    control(0,0,0,0,8);
    failed_reload=1;
    @(negedge clk); #1; s_axis_tvalid=1; s_axis_tdata=65; s_axis_tlast=1;
    repeat (100) tick();
    @(negedge clk); #1; s_axis_tvalid=0;
    if (rejected_prompt_edges!=100 || control_requests!=control_responses)
      $fatal(1,"TOP_SEMANTIC_RELOAD_CONSERVATION");
    comparisons=comparisons+1;
    $display("TOP_INTERACTION semantic_failed_reload=1 rejected_edges=%0d",
             rejected_prompt_edges);
"""
    else:
        raise ValueError("Unknown top interaction")
    # Insertion offsets change when declarations above are extended.
    first = bench.index("    running=1;\n", bench.index("  initial begin\n    rst_n=0;"))
    terminal = bench.index('    $display("BOOT_TRANSACTIONS', first)
    return bench[:first] + scenario + bench[terminal:]


def run_top_interactions(evidence):
    from storage import top_test
    evidence.run_cases([
        (f"interaction-{seed}-{kind}-uart-{uart}",
         lambda scope, seed=seed, kind=kind, uart=uart:
         top_test(scope, seed, uart=uart, interaction=kind))
        for seed in (1, 17, 89) for kind, uart in (
            ("serial-drain", False), ("serial-drain", True),
            ("uart-drain-prompt", True),
            ("semantic-failed-reload", False), ("memory-transport-priority", True))
    ])


def run_drain_prompts(evidence):
    """Only newly added output-drain scenarios; full L1 includes them above."""
    from storage import top_test
    evidence.run_cases([
        (f"drain-prompt-{seed}-{kind}-uart-{uart}",
         lambda scope, seed=seed, kind=kind, uart=uart:
         top_test(scope, seed, uart=uart, interaction=kind))
        for seed in (1, 17, 89) for kind, uart in (
            ("serial-drain", False), ("serial-drain", True),
            ("uart-drain-prompt", True))
    ])


def run_top_token_capacity(evidence):
    from storage import top_test
    evidence.run_cases([
        (f"top-token-capacity-{seed}",
         lambda scope, seed=seed: top_test(scope, seed, input_fault="token-capacity"))
        for seed in (1, 17, 89)
    ])
