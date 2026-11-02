"""Native top fault/cancellation experiments using the unchanged integer oracle.

Each interrupted command's observed write prefix is still compared exactly.
Every fault is followed by a complete new sequence using real retained memory,
not oracle-fed scratch data. Targets are public accepted requests/logits only.
Outstanding responses are deliberately held across cancellation to check drain;
no accepted request, late logit or token acceptance may occur on cancel edges.
"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagnostic import native_bench, simulate
from evidence import Evidence, rel


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"testbench recipe anchor is not unique: {old[:80]}")
    return text.replace(old, new, 1)


def faults_bench(evidence, legacy=None):
    if legacy is None:
        native_bench(evidence, 17, 1)
    else:
        from inference import inference_bench
        inference_bench(evidence, seed=17, tokens=1, legacy=legacy)
    path = evidence.path / "native.sv"
    bench = path.read_text()
    begin = bench.index("    for (position=0;position<TOKENS;position=position+1) begin")
    end = bench.index("\n  always @(negedge clk)", begin)
    bench = bench[:begin] + STIMULUS + bench[end:]
    if legacy is None:
        bench = replace_once(bench, "if (cycles>500000)", "if (cycles>10000000)")
    bench = replace_once(bench, "if (stalled[b] &&", "if (stalled[b] && !cancel &&")
    bench = replace_once(bench, "if (held_logit &&", "if (held_logit && !cancel &&")
    bench = replace_once(bench, "if (pending[b] && !mem_rsp_valid[b])",
                         "if (pending[b] && !mem_rsp_valid[b] && !freeze_service)")
    bench = replace_once(bench, "mem_rsp_valid[b]<=1;",
                         "mem_rsp_valid[b]<=1; mem_rsp_error[b]<=pending_error[b];")
    bench = replace_once(bench, "response_tag[b*64+:64]<=mem_req_tag[b*64+:64];",
                         """response_tag[b*64+:64]<=mem_req_tag[b*64+:64];
          pending_error[b]<=0;
          if (!triggered && target_request(b)) begin
            triggered=1; target_transfers=target_transfers+1;
            if (inject_error) pending_error[b]<=1;
            if (inject_tag) response_tag[b*64+:64]<=mem_req_tag[b*64+:64]^64'h8000000000000000;
          end""")
    bench = replace_once(bench, "mem_rsp_valid[b]<=0; pending[b]<=0;",
                         """mem_rsp_valid[b]<=0; mem_rsp_error[b]<=0;
          if (pending_bad_tag[b]) begin
            // An injected unsolicited tag does not discharge ownership.
            // Deliver the real matching response afterwards to satisfy
            // eventual-response fairness and permit fault drain.
            pending_bad_tag[b]<=0;
            response_tag[b*64+:64]<=correct_tag[b*64+:64];
            delay_cycles[b]=5;
          end else pending[b]<=0;""")
    bench = replace_once(bench, "pending_error[b]<=0;",
                         """pending_error[b]<=0; pending_bad_tag[b]<=0;
          correct_tag[b*64+:64]<=mem_req_tag[b*64+:64];""")
    bench = replace_once(bench,
                         "if (inject_tag) response_tag[b*64+:64]<=mem_req_tag[b*64+:64]^64'h8000000000000000;",
                         """if (inject_tag) begin
              pending_bad_tag[b]<=1;
              response_tag[b*64+:64]<=mem_req_tag[b*64+:64]^64'h8000000000000000;
            end""")
    old_done = """      if (done) begin
        if (error !== 1'b0 || compared_logits!==(completed+1)*8)
          $fatal(1,"TOKEN_ERROR_OR_PREMATURE_DONE cycle=%0d error=%b logits=%0d reads=%0d writes=%0d",
            cycles,error,compared_logits,reads,writes);
        completed=completed+1;
      end"""
    new_done = """      if (done) begin
        if (error !== expected_error || (expected_cancel && cancel_done!==1'b1) || pending)
          $fatal(1,"FAULT_COMPLETION_MISMATCH case=%0d actual_error=%b expected_error=%b pending=%b",
            experiment,error,expected_error,pending);
        if (!expected_error) begin
          if (compared_logits!=8) $fatal(1,"RESTART_MISSING_LOGITS");
          for (integer j=0;j<SLOTS;j=j+1)
            if (consumed[j]!==counts[j]) $fatal(1,"RESTART_MISSING_WRITE");
          successful_restarts=successful_restarts+1;
        end else error_completions=error_completions+1;
        completed=completed+1;
      end
      if (cancel_done) begin
        if (pending || mem_req_valid || logit_valid || token_ready)
          $fatal(1,"EARLY_CANCELLATION_COMPLETION");
        cancellation_completions=cancellation_completions+1;
      end
      if (cancel) begin
        if (mem_req_valid!==0 || logit_valid!==0 || token_ready!==0 || done!==0)
          $fatal(1,"CANCEL_EDGE_ACCEPTANCE_OR_TRAFFIC");
        cancel_edges=cancel_edges+1;
      end"""
    bench = replace_once(bench, old_done, new_done)
    # Logit cancellation must keep the offered first logit stalled throughout
    # observation, rather than let a default-ready helper retire it.
    bench = replace_once(bench, "else logit_ready=1;", "else logit_ready=!hold_logits;")
    if legacy is not None:
        bench = replace_once(bench,
            "mem_req_kind[bank*4+:4]==15 && mem_req_proj[bank*3+:3]==0",
            "mem_req_kind[bank*4+:4]==1")
        bench = replace_once(bench, """mem_req_kind[bank*4+:4]==15 &&
        mem_req_proj[bank*3+:3]==3 && mem_req_write[bank]""",
            "(mem_req_kind[bank*4+:4]==9 || mem_req_kind[bank*4+:4]==12) && mem_req_write[bank]")
        bench = replace_once(bench, """mem_req_kind[bank*4+:4]==15 &&
        mem_req_proj[bank*3+:3]==5 && mem_req_row[bank*32+25+:7]<7""",
            "mem_req_kind[bank*4+:4]==1")
    path.write_text(bench)
    return dict(experiments=12, required_successful_sequences=13,
                compared_write_prefixes=True, oracle_seed=17, legacy=legacy,
                targets="native absorption/cache/routed prefetch" if legacy is None else
                        "dense weight prefetch/cache/weight prefetch")


def reset_bench(evidence):
    native_bench(evidence, 17, 1)
    path = evidence.path/"native.sv"
    text = path.read_text()
    interruption = r"""
    @(negedge clk); token_valid=1; new_sequence=1; token_id=2; token_pos=0;
    @(posedge clk); while (!token_ready) @(posedge clk);
    @(negedge clk); token_valid=0;
    while (!(pending && (mem_req_kind[3:0]==15 || mem_req_kind[7:4]==15)))
      @(negedge clk);
    if (completed || compared_logits) $fatal(1,"RESET_TARGET_ALREADY_COMPLETE");
    $display("RESET_TARGET checked_prefix_writes=%0d accepted_reads=%0d",writes,reads);
    #1; rst_n=0; mem_req_ready=0; mem_rsp_valid=0; mem_rsp_error=0;
    mem_rsp_rdata=0; mem_rsp_tag=0; pending=0; stalled=0; held_logit=0;
    #1; check_reset();
    repeat(2) @(negedge clk);
    #1; rst_n=1;
    writes=0; reads=0; accepted=0;
    for (i=0;i<SLOTS;i=i+1) consumed[i]=0;
"""
    text = replace_once(text, "    for (position=0;position<TOKENS;position=position+1) begin",
                        interruption+"\n    for (position=0;position<TOKENS;position=position+1) begin")
    path.write_text(text)
    return dict(reset_mid_work=1, required_successful_restarts=1, checked_prefix=True)


def sequence_bench(evidence):
    from inference import inference_bench
    inference_bench(evidence, seed=17, tokens=2)
    path = evidence.path/"native.sv"
    text = path.read_text()
    opening = "    for (position=0;position<TOKENS;position=position+1) begin"
    prefix = r"""
    for (sequence_experiment=0;sequence_experiment<3;sequence_experiment=sequence_experiment+1) begin
      while (!token_ready) @(negedge clk);
      for (i=0;i<SLOTS;i=i+1) consumed[i]=0;
      completed=0;accepted=0;compared_logits=0;writes=0;reads=0;
"""
    text = replace_once(text, opening, prefix+"\n"+opening)
    closing = r"""
    repeat(3) @(negedge clk);
    if (writes!==WRITES || compared_logits!==TOKENS*8 || completed!==TOKENS)
      $fatal(1,"SEQUENCE_POSITIVE_CONTROL_MISSING");
    for(i=0;i<SLOTS;i=i+1)
      if(consumed[i]!==counts[i]) $fatal(1,"SEQUENCE_MISSING_WRITE");
    good_tokens=good_tokens+completed;
    saved_writes=writes;saved_reads=reads;saved_logits=compared_logits;
    rejecting=1;
    @(negedge clk); while (!token_ready) @(negedge clk);
    token_valid=1;new_sequence=0;token_id=4;
    token_pos=sequence_experiment==0 ? 3 : sequence_experiment==1 ? 2 : 5;
    token_phase=sequence_experiment!=1;
    @(posedge clk); if(token_ready!==1) $fatal(1,"SEQUENCE_INVALID_NOT_ACCEPTED");
    @(negedge clk);token_valid=0;
    while(rejected_commands<=sequence_experiment) @(negedge clk);
    if(writes!=saved_writes || reads!=saved_reads || compared_logits!=saved_logits)
      $fatal(1,"REJECTED_SEQUENCE_COMMAND_MODIFIED_MEMORY_OR_LOGITS");
    rejecting=0;
    end
    if (good_tokens!=6 || rejected_commands!=3) $fatal(1,"SEQUENCE_MISSING_COVERAGE");
    $display("SUMMARY good_tokens=%0d rejected_commands=%0d noncontiguous_positions=1 decode_to_prefill_rejections=1 out_of_range_positions=1",
      good_tokens,rejected_commands);
    $finish;
  end
  reg rejecting=0;
  integer sequence_experiment=0,rejected_commands=0,good_tokens=0;
  integer saved_reads=0,saved_writes=0,saved_logits=0;
"""
    begin = text.index("    repeat(3) @(negedge clk);", text.index(prefix))
    end = text.index("\n  always @(negedge clk)", begin)
    text = text[:begin]+closing+text[end:]
    text = replace_once(text, "      if (done) begin", """      if (done && rejecting) begin
        if(error!==1 || pending || mem_req_valid || logit_valid)
          $fatal(1,"SEQUENCE_ERROR_COMPLETION_MISMATCH");
        rejected_commands=rejected_commands+1;
      end
      if (done && !rejecting) begin""")
    path.write_text(text)
    return dict(successful_tokens=6, noncontiguous_positions=1,
                decode_to_prefill_rejections=1, out_of_range_positions=1,
                successful_restart_after_each_error=True)


STIMULUS = r"""
    pending_error=0;
    for (experiment=0;experiment<12;experiment=experiment+1) begin
      $display("CASE_START experiment=%0d completed=%0d",experiment,completed);
      expected_error=1; expected_cancel=0; triggered=0;
      inject_error=0; inject_tag=0; freeze_service=0; hold_logits=0; target=-1;
      before_completed=completed; before_cancel=cancellation_completions;
      if (experiment==0) begin
        // Idle cancel must not invent a successful or failed token.
        @(negedge clk); cancel=1;
        @(posedge clk); #1;
        @(negedge clk); cancel=0;
        while (cancellation_completions==before_cancel) @(negedge clk);
        if (completed!=before_completed) $fatal(1,"IDLE_CANCEL_INVENTED_TOKEN");
      end else if (experiment==1) begin
        @(negedge clk); while (!token_ready) @(negedge clk);
        token_valid=1; new_sequence=1; token_id=2; token_pos=0; cancel=1;
        before_accepted=accepted;
        @(posedge clk); #1;
        @(negedge clk); cancel=0; token_valid=0;
        while (cancellation_completions==before_cancel) @(negedge clk);
        if (accepted!=before_accepted || completed!=before_completed)
          $fatal(1,"SIMULTANEOUS_CANCEL_ACCEPTANCE");
      end else if (experiment==2 || experiment==3) begin
        start_token(experiment==2 ? 8 : 2, experiment==3 ? 1 : 0);
        while (completed==before_completed) @(negedge clk);
      end else begin
        // Cancellation during raw absorption, cache commit, routed
        // prefetch and held logits. Errors cover reads, writes, prefetch
        // and a malformed/stale response tag.
        if (experiment==4) target=2;
        if (experiment==5) target=3;
        if (experiment==6) target=4;
        if (experiment==7) begin target=-1; hold_logits=1; end
        if (experiment==8) begin target=0; inject_error=1; end
        if (experiment==9) begin target=1; inject_error=1; end
        if (experiment==10) begin target=4; inject_error=1; end
        if (experiment==11) begin target=0; inject_tag=1; end
        freeze_service=experiment>=4 && experiment<=6;
        start_token(2,0);
        if (experiment>=4 && experiment<=7) begin
          if (experiment==7) begin
            while (logit_valid!==1'b1 || logit_ready!==1'b0) @(negedge clk);
            if (logit_index!==0 || logit_data!==logits[0]) $fatal(1,"UNCHECKED_LOGIT_CANCEL_TARGET");
            logit_cancel_targets=logit_cancel_targets+1;
          end else begin
            // Service earlier requests normally, freezing only after
            // ownership of the selected target has been acquired.
            freeze_service=0;
            while (!triggered) @(negedge clk);
            freeze_service=1;
            if (pending==0) $fatal(1,"CANCEL_WITHOUT_OWNED_TARGET");
            owned_cancel_targets=owned_cancel_targets+1;
          end
          expected_cancel=1;
          cancel=1;
          repeat(3) @(negedge clk);
          cancel=0;
          if (experiment!=7) begin
            repeat(13) begin
              @(negedge clk);
              if (cancel_done!==0 || done!==0 || token_ready!==0)
                $fatal(1,"CANCEL_COMPLETED_BEFORE_DRAIN");
              held_drain_cycles=held_drain_cycles+1;
            end
          end
          freeze_service=0;
          while (cancellation_completions==before_cancel) @(negedge clk);
          if (completed!=before_completed+1) $fatal(1,"CANCEL_LOST_ACTIVE_COMPLETION");
        end else begin
          while (completed==before_completed) @(negedge clk);
          if (!triggered) $fatal(1,"FAULT_NOT_ACTUALLY_INJECTED");
          injected_faults=injected_faults+1;
        end
      end
      while (!token_ready) @(negedge clk);
      if (pending) $fatal(1,"RESTART_BEFORE_DRAIN");
      inject_error=0; inject_tag=0; target=-1; freeze_service=0; hold_logits=0;
      expected_error=0; expected_cancel=0; triggered=0; before_completed=completed;
      start_token(2,0);
      while (completed==before_completed) @(negedge clk);
    end
    // Final complete positive control after the final recovery.
    expected_error=0; before_completed=completed;
    start_token(2,0);
    while (completed==before_completed) @(negedge clk);
    repeat(3) @(negedge clk);
    if (successful_restarts!=13 || error_completions!=10 || cancellation_completions!=6 ||
        owned_cancel_targets!=3 || logit_cancel_targets!=1 || injected_faults!=4 ||
        target_transfers!=7 || cancel_edges==0 || held_drain_cycles!=39 ||
        request_stalls==0 || logit_stalls==0 || reset_samples<5)
      $fatal(1,"FAULT_MISSING_COVERAGE successful=%0d errors=%0d cancellations=%0d owned=%0d logits=%0d injected=%0d targets=%0d held_drain=%0d",
        successful_restarts,error_completions,cancellation_completions,
        owned_cancel_targets,logit_cancel_targets,injected_faults,target_transfers,held_drain_cycles);
    $display("SUMMARY fault_experiments=12 successful_restarts=%0d error_completions=%0d cancellation_completions=%0d checked_writes=%0d reads=%0d owned_cancel_targets=%0d logit_cancel_targets=%0d injected_faults=%0d held_drain_cycles=%0d cycles=%0d",
      successful_restarts,error_completions,cancellation_completions,writes,reads,
      owned_cancel_targets,logit_cancel_targets,injected_faults,held_drain_cycles,cycles);
    $finish;
  end
  reg [B-1:0] pending_error=0;
  reg [B-1:0] pending_bad_tag=0;
  reg [B*64-1:0] correct_tag=0;
  reg expected_error=0,expected_cancel=0,inject_error=0,inject_tag=0;
  reg triggered=0,freeze_service=0,hold_logits=0;
  integer experiment=0,target=-1,before_completed=0,before_cancel=0,before_accepted=0;
  integer successful_restarts=0,error_completions=0,cancellation_completions=0;
  integer owned_cancel_targets=0,logit_cancel_targets=0,injected_faults=0;
  integer target_transfers=0,cancel_edges=0,held_drain_cycles=0;
  function automatic integer target_request(input integer bank);
    begin
      target_request=0;
      if (target==0) target_request=!mem_req_write[bank];
      if (target==1) target_request=mem_req_write[bank];
      if (target==2) target_request=mem_req_kind[bank*4+:4]==15 && mem_req_proj[bank*3+:3]==0;
      if (target==3) target_request=mem_req_kind[bank*4+:4]==15 &&
        mem_req_proj[bank*3+:3]==3 && mem_req_write[bank];
      if (target==4) target_request=mem_req_kind[bank*4+:4]==15 &&
        mem_req_proj[bank*3+:3]==5 && mem_req_row[bank*32+25+:7]<7;
    end
  endfunction
  task automatic start_token(input [31:0] id, pos);
    begin
      @(negedge clk); while (token_ready!==1'b1) @(negedge clk);
      if (pending) $fatal(1,"TOKEN_START_WITH_OWNED_MEMORY");
      for (integer j=0;j<SLOTS;j=j+1) consumed[j]=0;
      compared_logits=0;
      token_id=id; token_pos=pos; token_phase=0; new_sequence=1; token_valid=1;
      @(posedge clk);
      if (token_ready!==1'b1) $fatal(1,"FAULT_STIMULUS_NOT_ACCEPTED");
      @(negedge clk); token_valid=0;
    end
  endtask
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-of")
    parser.add_argument("--legacy-profile", type=int, choices=(1, 2, 3))
    parser.add_argument("--reset-only", action="store_true")
    parser.add_argument("--sequence-only", action="store_true")
    args = parser.parse_args()
    evidence = Evidence("native-faults-verilator", args.repair_of)
    try:
        summary = (sequence_bench(evidence) if args.sequence_only else
                   reset_bench(evidence) if args.reset_only else faults_bench(
            evidence, legacy=None if args.legacy_profile is None else (args.legacy_profile, 0, 0)))
        summary["observations"] = simulate(evidence, "native.sv", "verilator")
        evidence.finish("passed", **summary)
        print(summary["observations"].strip())
    except Exception as exc:
        evidence.finish("failed", error=str(exc))
        print(str(exc), file=sys.stderr)
        print(rel(evidence.path / "receipt.json"), file=sys.stderr)
        return 1
    print(rel(evidence.path / "receipt.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
