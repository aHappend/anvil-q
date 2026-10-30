"""Reset active public transactions, quiesce EMIF, then compare fresh inference.

The external byte memory survives reset; its outstanding response source does
not. Each recovery explicitly reinstalls descriptors and uploads the synthetic
image. This is reset recovery, not persistent-image reuse across new_sequence.
"""

from pathlib import Path

from experiments import measurement_records, top_probe


def instrument_resets(bench, model):
    weight = next(entry for entry in model.descriptors if entry[1:4] == (1, 0, 0))
    declarations = r"""
reg reset_hold_write=0,reset_stall_read=0;
integer reset_epochs=0,reset_recovery_logits=0,reset_observed_bins=0;
integer reset_wait_edges=0,reset_aborted_tokens=0,reset_cancelled_writes=0;
task reset_start_token;
 begin
  @(negedge clk);
  if(token_ready!==1) $fatal(1,"RESET_TOKEN_NOT_READY");
  token_id=token_words[0][31:0];token_pos=0;new_sequence=1;token_valid=1;logit_ready=0;
  edge_tick();
  if(token_ready!==0 || logit_valid!==0 || done!==0 || error!==0)
   $fatal(1,"RESET_TOKEN_ACCEPT_EDGE");
  @(negedge clk);token_valid=0;
 end
endtask
task reset_recover;
 integer n;
 begin
  #0.125;rst_n=0;
  token_valid=0;new_sequence=0;logit_ready=0;
  csr_valid=0;csr_rsp_ready=0;load_valid=0;load_last=0;
  #0.001;check_reset();
  repeat(6) edge_tick();
  // Reset quiesces the external responder and discards its pending epoch.
  if(outstanding!==0 || avm_readdatavalid!==0 || avm_writeresponsevalid!==0)
   $fatal(1,"RESET_EXTERNAL_SOURCE_NOT_QUIESCENT");
  reads=0;writes=0;load_accepts=0;response_writes=0;cursor=0;
  reset_hold_write=0;reset_stall_read=0;
  @(negedge clk);rst_n=1;
  repeat(150) begin
   edge_tick();
   if(token_ready!==0 || logit_valid!==0 || done!==0 || error!==0 ||
      avm_read!==0 || avm_write!==0 || load_done!==0 || load_error!==0)
    $fatal(1,"RESET_STALE_TRAFFIC_IMAGE_OR_COMPLETION");
  end
  csr(0,16'h0000,0,0,32'h02000001);
  csr(0,16'h0014,0,1,0);
  csr(1,16'h0008,4,0,0);
  upload();
  csr(1,16'h000c,case_header[0],0,0);
  for(n=0;n<descriptor_count;n=n+1)
   csr(1,descriptor_words[n][47:32],descriptor_words[n][31:0],0,0);
  csr(1,16'h0008,2,0,0);
  repeat(30) edge_tick();
  if(token_ready!==1) $fatal(1,"RESET_RECOMMITTED_IMAGE_NOT_READY");
  run_token(token_words[0][31:0],0,1'b1,token_words[0][65+:VOCAB_VALUE*32]);
  reset_recovery_logits=reset_recovery_logits+VOCAB_VALUE;
  reset_epochs=reset_epochs+1;
 end
endtask
task reset_active_case(input integer phase);
 integer waiting,n,observed_final,before_reads;
 reg [31:0] held_index,held_logit;
 begin
  waiting=0;
  if(phase==0) begin
   reset_hold_write=1;
   @(negedge ddr_clk);
   load_address=0;load_data=image[0];load_byteenable=64'hffffffffffffffff;
   load_last=1;load_valid=1;
   #0.001;
   while(load_ready!==1 && waiting<10000) begin
    @(negedge ddr_clk);#0.001;waiting=waiting+1;
   end
   if(load_ready!==1) $fatal(1,"RESET_PRELOAD_NOT_ACCEPTED");
   @(posedge ddr_clk);#0.001;
   @(negedge ddr_clk);load_valid=0;
   waiting=0;
   while(writes!==response_writes+1 && waiting<10000) begin
    @(negedge ddr_clk);#0.001;waiting=waiting+1;
   end
   if(writes!==response_writes+1 || load_done!==0 || load_error!==0)
    $fatal(1,"RESET_NO_OUTSTANDING_WRITE_RESPONSE");
   repeat(7) begin
    @(posedge ddr_clk);#0.001;
    if(writes!==response_writes+1 || avm_writeresponsevalid!==0 || load_done!==0)
     $fatal(1,"RESET_WRITE_RESPONSE_HOLD_FAILED");
   end
   reset_cancelled_writes=reset_cancelled_writes+1;
  end else if(phase==4) begin
   @(negedge clk);
   csr_valid=1;csr_write=0;csr_address=0;csr_wdata=0;csr_rsp_ready=0;
   if(csr_ready!==1) $fatal(1,"RESET_CSR_NOT_READY");
   edge_tick();
   if(csr_rsp_valid!==0) $fatal(1,"RESET_CSR_EARLY_RESPONSE");
   @(negedge clk);csr_valid=0;
   while(csr_rsp_valid!==1 && waiting<10000) begin
    edge_tick();waiting=waiting+1;
   end
   if(csr_rsp_valid!==1 || csr_rdata!==32'h02000001 || csr_error!==0)
    $fatal(1,"RESET_NO_COMPARED_CSR_RESPONSE");
   repeat(7) begin
    edge_tick();
    if(csr_rsp_valid!==1 || csr_rdata!==32'h02000001 || csr_error!==0)
     $fatal(1,"RESET_CSR_STALL_CHANGED");
   end
  end else begin
   reset_stall_read=(phase==2);
   before_reads=reads;
   reset_start_token();
   if(phase==1 || phase==2) begin
    while(!((phase==1 && avm_readdatavalid===1 &&
             (cursor-1)*64>=RESET_WEIGHT_BASE && (cursor-1)*64<RESET_WEIGHT_END) ||
            (phase==2 && avm_read===1 && avm_waitrequest===1)) && waiting<100000) begin
     @(negedge ddr_clk);#0.001;waiting=waiting+1;
     if(done!==0 || error!==0 || logit_valid!==0)
      $fatal(1,"RESET_READ_PHASE_COMPLETED_EARLY");
    end
    if(waiting==100000) $fatal(1,"RESET_READ_PHASE_NOT_OBSERVED phase=%0d",phase);
    if(phase==1) begin
     if(avm_response!==0 || avm_readdata!==memory[cursor-1])
      $fatal(1,"RESET_RESPONSE_NOT_COMPARED");
    end else begin
     for(n=0;n<7;n=n+1) begin
      @(posedge ddr_clk);#0.001;
      if(avm_read!==1 || avm_waitrequest!==1 || reads!==before_reads || outstanding!==0)
       $fatal(1,"RESET_WAITREQUEST_PRECONDITION_LOST");
      reset_wait_edges=reset_wait_edges+1;
     end
    end
   end else begin
    observed_final=0;
    while(observed_final==0 && waiting<10000000) begin
     @(negedge clk);
     logit_ready=0;
     if(logit_valid===1) begin
      if(logit_index!==logits%VOCAB_VALUE ||
         logit_data!==token_words[0][65+32*(logits%VOCAB_VALUE)+:32])
       $fatal(1,"RESET_LOGIT_REFERENCE_MISMATCH");
      if(logit_index==VOCAB_VALUE-1) begin
       observed_final=1;held_index=logit_index;held_logit=logit_data;
      end else logit_ready=1;
     end
     if(observed_final==0) begin
      if(logit_valid===1 && logit_ready===1) logits=logits+1;
      edge_tick();waiting=waiting+1;
      if(done!==0 || error!==0) $fatal(1,"RESET_FINAL_COMPLETED_EARLY");
     end
    end
    if(observed_final!==1) $fatal(1,"RESET_FINAL_STALL_NOT_OBSERVED");
    repeat(7) begin
     edge_tick();
     if(logit_valid!==1 || logit_ready!==0 || logit_index!==held_index ||
        logit_data!==held_logit || done!==0 || error!==0)
      $fatal(1,"RESET_FINAL_STALL_CHANGED");
    end
   end
   reset_aborted_tokens=reset_aborted_tokens+1;
  end
  reset_observed_bins=reset_observed_bins|(1<<phase);
  reset_recover();
 end
endtask
"""
    marker = "task run_token("
    if bench.count(marker) != 1:
        raise AssertionError("reset test cannot identify the public token driver")
    declarations = declarations.replace("RESET_WEIGHT_BASE", str(weight[4])).replace(
        "RESET_WEIGHT_END", str(weight[4] + weight[5]))
    bench = bench.replace(marker, declarations + "\n" + marker, 1)
    marker = "if (writes>response_writes) begin"
    if bench.count(marker) != 1:
        raise AssertionError("reset test cannot identify the external write response source")
    bench = bench.replace(marker, "if (writes>response_writes && !reset_hold_write) begin", 1)
    marker = "  ddr_cycles=ddr_cycles+1;"
    if bench.count(marker) != 1:
        raise AssertionError("reset test cannot identify the external command service")
    bench = bench.replace(marker, "  if(reset_stall_read && avm_read) avm_waitrequest=1;\n" +
                          marker, 1)
    program = r"""
 reset_active_case(0);
 reset_active_case(1);
 reset_active_case(2);
 reset_active_case(3);
 reset_active_case(4);
 if(reset_epochs!=5 || reset_observed_bins!=31 || reset_wait_edges!=7 ||
    reset_aborted_tokens!=3 || reset_cancelled_writes!=1 ||
    reset_recovery_logits!=5*VOCAB_VALUE)
  $fatal(1,"RESET_INTEGRATION_MISSING_OBSERVED_COVERAGE");
 $display("CHECKS_PASSED active_reset epochs=%0d bins=%0d wait_edges=%0d aborted_tokens=%0d cancelled_write_responses=%0d recovery_logits=%0d",
          reset_epochs,reset_observed_bins,reset_wait_edges,reset_aborted_tokens,
          reset_cancelled_writes,reset_recovery_logits);
 $finish;
"""
    return bench, program


def reset_integration(evidence, seed):
    ledger = evidence.record.setdefault("active_reset_cases", [])
    for mode in ("AWQ", "BF16"):
        trial = evidence.__class__("active-reset-" + mode.lower(),
                                  source_root=evidence.folder / "sources")
        trial.simulation_build_pool = evidence.simulation_build_pool
        row = {"mode": mode, "configuration": 0, "seed": seed, "outcome": "running",
               "receipt": evidence.relative(trial.folder / "receipt.json")}
        ledger.append(row)
        evidence.flush()
        try:
            top_probe(trial, mode, seed, reset_validation=True)
            transcript = next(
                (trial.folder.parents[2] / command["stdout"]).read_text()
                for command in reversed(trial.record["commands"])
                if Path(command["argv"][0]).parts[-2:] == ("compiled", "Vtb"))
            records = measurement_records(transcript, "CHECKS_PASSED active_reset")
            expected = {"epochs": 5, "bins": 31, "wait_edges": 7, "aborted_tokens": 3,
                        "cancelled_write_responses": 1, "recovery_logits": 40}
            if len(records) != 1 or any(records[0].get(k) != v for k, v in expected.items()):
                raise AssertionError("active-reset public comparisons or recovery coverage missing")
            trial.finish("probe_passed", "Observed five reset phases and complete independent "
                         "ordered recovery logits; external EMIF source quiesced on reset.")
        except (OSError, RuntimeError, AssertionError, ValueError) as exc:
            row.update(outcome="failed", reason=str(exc))
            trial.finish("failed", str(exc))
            raise
        finally:
            evidence.flush()
        try:
            evidence.bind_child(trial)
        except (OSError, RuntimeError, AssertionError, ValueError) as exc:
            row.update(outcome="failed", reason=str(exc))
            evidence.flush()
            raise
        row.update(outcome="compared", observed=records[0])
        evidence.flush()
