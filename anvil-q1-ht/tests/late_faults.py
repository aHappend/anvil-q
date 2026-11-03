"""Public DDR read faults after an independently checked, accepted logit prefix.

The compact two-panel vocabulary is supplemental engineering coverage. It does
not replace any mandatory geometry, benchmark or full-model hardware workload.
"""

from pathlib import Path

from experiments import measurement_records, top_probe


def instrument_late_read(bench, model):
    descriptor = next(entry for entry in model.descriptors if entry[1:4] == (0, 0, 0))
    panel_start = descriptor[4] + model.shape.hidden * 64 * 2
    panel_end = descriptor[4] + descriptor[5]
    declarations = r"""
reg late_arm=0,late_fault_offered=0;
integer late_prefix=0,late_fault_responses=0,late_issued_beats=0;
integer late_commands=0,late_prefix_stalls=0,late_idle_checks=0;
integer late_saved_reads=0,late_saved_uploads=0,late_saved_writes=0;
integer late_rejected_continuations=0,late_rejection_edges=0,late_rejection_idle_checks=0;
reg [32:0] late_fault_address=0;
always @(posedge ddr_clk) if(rst_n) begin
 if(avm_read && !avm_waitrequest) begin
  late_commands=late_commands+1;
  late_issued_beats=late_issued_beats+avm_burstcount;
 end
 if(avm_readdatavalid && avm_response!=0) begin
  if(avm_response!==2'b10 || !late_arm || late_prefix!==64 ||
     late_fault_responses!==0 || !late_fault_offered ||
     late_fault_address<@PANEL_START@ || late_fault_address>=@PANEL_END@)
   $fatal(1,"LATE_READ_FAULT_NOT_AFTER_ACCEPTED_PREFIX");
  late_fault_responses=late_fault_responses+1;
 end
end
"""
    marker = "integer response_writes=0;"
    if bench.count(marker) != 1:
        raise AssertionError("late read declaration insertion site changed")
    bench = bench.replace(marker, marker + declarations)
    marker = "if(reads==READ_FAULT_VALUE) avm_response=2'b10;"
    if bench.count(marker) != 1:
        raise AssertionError("late read public response injection site changed")
    bench = bench.replace(marker, marker + r"""
    if(late_arm && !late_fault_offered) begin
      avm_response=2'b10;
      late_fault_offered=1;
      late_fault_address={cursor[26:0],6'b0};
    end
""")
    inference = r"""
 late_saved_uploads=load_accepts;late_saved_writes=writes;
 @(negedge clk);
 token_id=token_words[0][31:0];token_pos=0;new_sequence=1;token_valid=1;logit_ready=0;
 if(token_ready!==1) $fatal(1,"LATE_READ_TOKEN_NOT_READY");
 edge_tick();
 if(token_ready!==0 || logit_valid!==0 || done!==0 || error!==0)
  $fatal(1,"LATE_READ_ACCEPT_EDGE");
 @(negedge clk);token_valid=0;
 timeout_cycles=0;
 while(late_prefix<64 && timeout_cycles<10000000) begin
  @(negedge clk);
  logit_ready=timeout_cycles%11>3;
  if(logit_valid===1 && logit_index==63 && late_prefix_stalls<31) begin
   logit_ready=0;late_prefix_stalls=late_prefix_stalls+1;
  end
  #0.001;
  if((^{logit_valid,logit_index,logit_data,done,error,token_ready})===1'bx ||
     done!==0 || error!==0 || token_ready!==0)
   $fatal(1,"LATE_READ_PREFIX_STATUS");
  if(logit_valid===1 &&
     (logit_index!==late_prefix ||
      logit_data!==token_words[0][65+32*late_prefix+:32]))
   $fatal(1,"LATE_READ_PREFIX_REFERENCE_MISMATCH");
  if(logit_valid && !logit_ready) begin
   saved_late_index=logit_index;saved_late_data=logit_data;
   edge_tick();
   if(logit_valid!==1 || logit_index!==saved_late_index || logit_data!==saved_late_data)
    $fatal(1,"LATE_READ_PREFIX_STALL_CHANGED");
  end else if(logit_valid && logit_ready) begin
   edge_tick();late_prefix=late_prefix+1;logits=logits+1;
  end else edge_tick();
  if(done!==0 || error!==0) $fatal(1,"LATE_READ_PREFIX_FALSE_COMPLETION");
  timeout_cycles=timeout_cycles+1;
 end
 if(late_prefix!==64 || late_prefix_stalls!==31 || late_fault_responses!==0)
  $fatal(1,"LATE_READ_MISSING_PREFIX_COVERAGE");
 late_arm=1;
 @(negedge clk);logit_ready=0;
 timeout_cycles=0;
 while(done!==1 && timeout_cycles<10000000) begin
  edge_tick();
  if((^{logit_valid,logit_index,logit_data,done,error,token_ready})===1'bx)
   $fatal(1,"LATE_READ_ACTIVE_XZ");
  if(logit_valid!==0) $fatal(1,"LATE_READ_POSTFAULT_LOGIT");
  timeout_cycles=timeout_cycles+1;
 end
 if(done!==1 || error!==1 || token_ready!==0 ||
    late_fault_responses!==1 || outstanding!==0 ||
    reads!==late_issued_beats || avm_read!==0 || avm_write!==0 ||
    load_accepts!==late_saved_uploads || writes!==late_saved_writes)
  $fatal(1,"LATE_READ_NO_DRAINED_ERROR_COMPLETION");
 late_saved_reads=reads;
 repeat(64) begin
  edge_tick();
  if({done,error,logit_valid,token_ready,avm_read,avm_write}!==6'b0 ||
     reads!==late_saved_reads)
   $fatal(1,"LATE_READ_DUPLICATE_OR_SUCCESS_COMPLETION");
  late_idle_checks=late_idle_checks+1;
 end
 csr(0,16'h0004,0,0,32'h0000000c);
 csr(1,16'h0008,4,0,0);
 repeat(30) edge_tick();
 if(token_ready!==1) $fatal(1,"LATE_READ_CLEAR_NOT_READY");
 @(negedge clk);
 token_id=token_words[0][31:0];token_pos=0;new_sequence=0;token_valid=1;
 if(token_ready!==1) $fatal(1,"LATE_READ_CONTINUATION_NOT_ACCEPTED");
 edge_tick();
 if(token_ready!==0 || logit_valid!==0)
  $fatal(1,"LATE_READ_CONTINUATION_ACCEPT_EDGE");
 @(negedge clk);token_valid=0;
 while(done!==1 && late_rejection_edges<2) begin
  edge_tick();late_rejection_edges=late_rejection_edges+1;
  if((^{done,error,logit_valid,token_ready})===1'bx || logit_valid!==0 ||
     reads!==late_saved_reads || outstanding!==0 || avm_read!==0 || avm_write!==0 ||
     load_accepts!==late_saved_uploads || writes!==late_saved_writes)
   $fatal(1,"LATE_READ_CONTINUATION_TRAFFIC_OR_LOGIT");
 end
 if(done!==1 || error!==1)
  $fatal(1,"LATE_READ_CONTINUATION_REJECTION_DEADLINE");
 late_rejected_continuations=late_rejected_continuations+1;
 repeat(31) begin
  edge_tick();
  if({done,error,logit_valid,token_ready,avm_read,avm_write}!==6'b0 ||
     reads!==late_saved_reads || outstanding!==0 ||
     load_accepts!==late_saved_uploads || writes!==late_saved_writes)
   $fatal(1,"LATE_READ_CONTINUATION_DUPLICATE_OR_SIDE_EFFECT");
  late_rejection_idle_checks=late_rejection_idle_checks+1;
 end
 csr(0,16'h0004,0,0,32'h0000000c);
 csr(1,16'h0008,4,0,0);
 repeat(30) edge_tick();
 if(token_ready!==1) $fatal(1,"LATE_READ_CONTINUATION_CLEAR_NOT_READY");
 run_token(token_words[0][31:0],0,1'b1,token_words[0][65+:VOCAB_VALUE*32]);
 if(logits!==64+VOCAB_VALUE || late_fault_responses!==1 ||
    load_accepts!==late_saved_uploads || writes!==late_saved_writes ||
    reads!==late_issued_beats || outstanding!==0)
  $fatal(1,"LATE_READ_RECOVERY_CONSERVATION");
 $display("CHECKS_PASSED late_read prefix_logits=%0d prefix_stalls=%0d faults=%0d drained_read_beats=%0d recovery_logits=%0d idle_checks=%0d uploads=%0d writes=%0d commands=%0d rejected_continuations=%0d rejection_edges=%0d rejection_idle_checks=%0d",
          late_prefix,late_prefix_stalls,late_fault_responses,late_saved_reads,
          VOCAB_VALUE,late_idle_checks,load_accepts,writes,late_commands,
          late_rejected_continuations,late_rejection_edges,late_rejection_idle_checks);
 $finish;
"""
    declarations = "reg [31:0] saved_late_index=0,saved_late_data=0;\n"
    bench = bench.replace("reg late_arm=0", declarations + "reg late_arm=0")
    for key, value in (("@PANEL_START@", panel_start), ("@PANEL_END@", panel_end)):
        bench = bench.replace(key, str(value))
    return bench, inference


def late_read_case(evidence, mode, seed):
    top_probe(evidence, mode, seed, late_read_fault=True)
    transcript = next(
        (evidence.folder.parents[2] / command["stdout"]).read_text()
        for command in reversed(evidence.record["commands"])
        if Path(command["argv"][0]).parts[-2:] == ("compiled", "Vtb"))
    rows = measurement_records(transcript, "CHECKS_PASSED late_read")
    required = {"prefix_logits": 64, "prefix_stalls": 31, "faults": 1,
                "recovery_logits": 67, "idle_checks": 64,
                "rejected_continuations": 1, "rejection_idle_checks": 31}
    if (len(rows) != 1 or any(rows[0].get(key) != value for key, value in required.items()) or
            rows[0].get("rejection_edges") not in (0, 1, 2) or
            min(rows[0][key] for key in ("drained_read_beats", "uploads", "writes", "commands")) <= 0 or
            rows[0]["uploads"] != rows[0]["writes"]):
        raise AssertionError("late read fault lacks observed prefix/error/recovery coverage")
    evidence.record["observations"].append({
        "scope": "public_two_panel_logit_prefix_then_DDR_fault_not_full_model_acceptance",
        "mode": mode, "seed": seed, "observed": rows[0],
        "oracle": "independent fixed-point prefix and complete recovery logits; "
                  "accepted Avalon burst-beat conservation and one error response",
        "image_reuse": "same committed image and sequence reset after clearing sticky error; "
                       "no additional host upload",
        "sequence_invalidation": "in-range position zero without new_sequence rejected "
                                 "within two edges after clearing the memory fault; "
                                 "no DDR traffic or logits, then explicit new-sequence recovery",
    })
    evidence.flush()


def late_read_faults(evidence, seed):
    ledger = evidence.record.setdefault("late_read_fault_cases", [])
    for mode in ("AWQ", "BF16"):
        row = {"mode": mode, "seed": seed, "outcome": "running"}
        ledger.append(row)
        trial = evidence.__class__("late-read-" + mode.lower(),
                                   source_root=evidence.folder / "sources")
        trial.simulation_build_pool = evidence.simulation_build_pool
        trial.record["tool_version_receipt"] = evidence.relative(evidence.folder / "receipt.json")
        row["receipt"] = evidence.relative(trial.folder / "receipt.json")
        evidence.flush()
        try:
            late_read_case(trial, mode, seed)
            row.update(outcome="compared", observed=trial.record["observations"][-1]["observed"])
            trial.finish("probe_passed", "Observed accepted logit prefix, drained DDR fault "
                         "and complete reference recovery with the original uploaded image.")
        except (OSError, RuntimeError, AssertionError, ValueError) as exc:
            row.update(outcome="failed", reason=str(exc))
            trial.finish("failed", str(exc))
            raise
        finally:
            evidence.flush()
