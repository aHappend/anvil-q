"""Injected external-memory failures, cancellation, and new-sequence recovery.

The transactor derives phase triggers from accepted public memory traffic and
publication handshakes. It never observes decoder state or internal ownership.
Every aborted sequence is followed by an invalid ordinary continuation and two
fully compared transactions in a fresh sequence, without resetting the DUT
(except the explicitly selected reset-in-work case).
"""

import hashlib
import json
import re

from execution import ROOT, relative
from integration import generate_images
from memory_checks import banked_bench
from model import Geometry
from speculation_checks import replace_once


FAULT_CASES = {
    1: "qweight_read_error",
    2: "kv_write_error",
    3: "scale_reserved_payload",
    4: "embedding_nonfinite",
    5: "unknown_response_tag",
    6: "duplicate_response_tag",
    7: "wrong_response_bank",
    8: "stale_previous_sequence_tag",
    9: "cancel_projection_outstanding",
    10: "cancel_qk_normalization",
    11: "cancel_causal_attention",
    12: "cancel_before_commit",
    13: "cancel_after_commit",
    14: "reset_projection_outstanding",
    15: "cancel_stalled_logits",
}


FAULT_TASKS = r"""
  task clear_epoch;
    begin
      for (j=0;j<M*KD;j=j+1) begin key_valid[j]=0;value_valid[j]=0;end
      key_count=0;value_count=0;
    end
  endtask
  task submit(input integer position,input integer fresh_sequence);
    begin
      @(negedge clk);#3;
      active_case=position;logit_count=0;commit_seen=0;
      for (j=0;j<15*MAX;j=j+1) begin writes[j]=0;scratch_valid[j]=0;end
      guard=0;
      while (token_ready!==1 && guard<100) begin @(negedge clk);#3;guard=guard+1;end
      if (token_ready!==1) $fatal(1,"RECOVERY_TOKEN_NOT_READY");
      if (fresh_sequence) clear_epoch();
      token_id=host_tokens[position];token_pos=position;token_phase=host_phases[position];
      new_sequence=fresh_sequence;token_valid=1;
      @(posedge clk);
      if (token_ready!==1) $fatal(1,"RECOVERY_TOKEN_HANDSHAKE");
      #1;if (token_ready!==0 || logit_valid!==0 || done!==0)
        $fatal(1,"RECOVERY_ACCEPT_ORDER");
      @(negedge clk);#3;token_valid=0;new_sequence=0;
    end
  endtask
  task success;
    integer expected_completion;
    begin
      expected_completion=completed+1;guard=0;
      while (completed<expected_completion && guard<450000) begin
        @(negedge clk);#3;guard=guard+1;
      end
      if (completed!=expected_completion) $fatal(1,"RECOVERY_COMPLETION_TIMEOUT");
      if (key_count!=(active_case+1)*KD || value_count!=(active_case+1)*KD)
        $fatal(1,"RECOVERY_KV_EXTENT");
    end
  endtask
  task rejected_continuation;
    integer before_errors,before_requests;
    begin
      @(negedge clk);#3;test_phase=2;
      before_errors=error_seen;before_requests=req_count;
      guard=0;
      while (token_ready!==1 && guard<100) begin @(negedge clk);#3;guard=guard+1;end
      if (token_ready!==1) $fatal(1,"INVALID_SEQUENCE_NOT_READY");
      token_id=expected_tokens[1];token_pos=2;token_phase=1;new_sequence=0;token_valid=1;
      @(posedge clk);
      if (token_ready!==1) $fatal(1,"INVALID_SEQUENCE_HANDSHAKE");
      #1;@(negedge clk);#3;token_valid=0;
      guard=0;
      while (error_seen==before_errors && guard<100) begin
        @(negedge clk);#3;guard=guard+1;
      end
      if (error_seen!=before_errors+1 || req_count!=before_requests || queued!=0)
        $fatal(1,"INVALID_SEQUENCE_NOT_REJECTED");
      repeat (4) begin @(negedge clk);#3;end
      if (error_seen!=before_errors+1) $fatal(1,"INVALID_SEQUENCE_DUPLICATE_ERROR");
    end
  endtask
"""


def fault_bench():
    text = banked_bench()
    text = replace_once(
        text, "integer request_bank=0,response_bank=0,response_slot=0,b,o,slot;",
        "integer request_bank=0,response_bank=0,response_slot=0,b,o,slot;\n"
        "  integer test_phase=0,fault_kind=0,injected=0,error_seen=0,cancellation_seen=0;\n"
        "  integer response_count=0,drain_responses=0,abort_cycle=-1,norm_cycle=-1;\n"
        "  integer queue_kind[0:63],queue_column[0:63];\n"
        "  reg queue_write[0:63];\n"
        "  reg spoof_response=0,reset_probe=0;\n"
        "  reg [63:0] prior_tag=0;\n"
        "  integer prior_bank=0,publication_transfers=0,stalled_commit_edges=0;\n"
        "  integer stalled_logit_edges=0;")
    text = replace_once(
        text, "if (error!==0 || cancel_done!==0 || think_active!==0 || draft_ready!==0)",
        "if ((test_phase==0 && (error!==0 || cancel_done!==0)) ||\n"
        "          think_active!==0 || draft_ready!==0)")
    text = replace_once(
        text, "if (held_request && (mem_req_valid!==1 ||",
        "if (!injected && held_request && (mem_req_valid!==1 ||")
    text = replace_once(
        text, "if (held_logit && (logit_valid!==1 ||",
        "if (!injected && held_logit && (logit_valid!==1 ||")
    text = replace_once(
        text, "if (held_commit && (commit_valid!==1 ||",
        "if (!injected && held_commit && (commit_valid!==1 ||")
    text = replace_once(
        text, "if (held_banks[b] && (bank_mem_req_valid[b]!==1 ||",
        "if (!injected && held_banks[b] && (bank_mem_req_valid[b]!==1 ||")
    text = replace_once(
        text, "if (mem_rsp_valid && mem_rsp_ready) begin",
        "if ((^{token_ready,logit_valid,done,error,cancel_done,commit_valid,\n"
        "             bank_mem_req_valid,bank_mem_rsp_ready})===1'bx)\n"
        "        $fatal(1,\"FAULT_ACTIVE_STATUS_XZ\");\n"
        "      if (error) begin\n"
        "        if (test_phase==0 || queued!=0 || done!==0 || commit_valid!==0 ||\n"
        "            logit_valid!==0 || token_ready!==0)\n"
        "          $fatal(1,\"FAULT_ERROR_PUBLICATION_OR_DRAIN\");\n"
        "        error_seen=error_seen+1;\n"
        "      end\n"
        "      if (cancel_done) begin\n"
        "        if (test_phase!=1 || fault_kind<9 || fault_kind==14 || queued!=0 ||\n"
        "            done!==0 || error!==0 || commit_valid!==0 || token_ready!==0)\n"
        "          $fatal(1,\"FAULT_CANCEL_PUBLICATION_OR_DRAIN\");\n"
        "        cancellation_seen=cancellation_seen+1;\n"
        "      end\n"
        "      if (test_phase==2 && (logit_valid!==0 || commit_valid!==0 || done!==0))\n"
        "        $fatal(1,\"INVALID_SEQUENCE_PUBLICATION\");\n"
        "      if (test_phase==1 && injected &&\n"
        "          (done!==0 || commit_valid!==0 || logit_valid!==0 || bank_mem_req_valid!==0))\n"
        "        $fatal(1,\"FAULT_NEW_WORK_AFTER_ABORT\");\n"
        "      if (test_phase==1 && commit_valid && !commit_ready)\n"
        "        stalled_commit_edges=stalled_commit_edges+1;\n"
        "      if (test_phase==1 && logit_valid && !logit_ready)\n"
        "        stalled_logit_edges=stalled_logit_edges+1;\n"
        "      if (mem_rsp_valid && mem_rsp_ready && !spoof_response) begin\n"
        "        response_count=response_count+1;\n"
        "        if (injected) drain_responses=drain_responses+1;\n"
        "        if (prior_tag==0) begin prior_tag=mem_rsp_tag;prior_bank=response_bank;end\n"
        "        if (test_phase==1 && queue_kind[response_slot]==12 &&\n"
        "            queue_column[response_slot]==D-1) norm_cycle=cycle;")
    text = replace_once(
        text, "queue_bank[response_slot]=queue_bank[front];",
        "queue_bank[response_slot]=queue_bank[front];\n"
        "        queue_kind[response_slot]=queue_kind[front];\n"
        "        queue_column[response_slot]=queue_column[front];\n"
        "        queue_write[response_slot]=queue_write[front];")
    text = replace_once(
        text, "queue_bank[tail]=request_bank;",
        "queue_bank[tail]=request_bank;queue_kind[tail]=mem_req_kind;\n"
        "        queue_column[tail]=mem_req_col;queue_write[tail]=mem_req_write;")
    text = replace_once(
        text, "if (mem_req_valid && mem_req_ready) begin",
        "if (mem_req_valid && mem_req_ready) begin\n"
        "        if (test_phase==2) $fatal(1,\"INVALID_SEQUENCE_MEMORY_WORK\");")
    text = replace_once(
        text, "commit_seen=1;last_commit_cycle=cycle;",
        "commit_seen=1;last_commit_cycle=cycle;\n"
        "          if (test_phase==1) publication_transfers=publication_transfers+1;")
    start = text.index("    @(negedge clk);rst_n=1;\n    for (c=0;c<N;c=c+1) begin")
    end = text.index("  initial begin repeat (500000)", start)
    text = text[:start] + r"""
    if (!$value$plusargs("fault=%d",fault_kind) || fault_kind<1 || fault_kind>15)
      $fatal(1,"FAULT_CASE_REQUIRED");
    @(negedge clk);#3;rst_n=1;
    submit(0,1);success();
    // The stale-tag case explicitly crosses a new-sequence ownership epoch.
    if (fault_kind==8) begin submit(0,1);success();end
    test_phase=1;
    submit(1,0);
    guard=0;
    while (!injected && guard<450000) begin @(negedge clk);#3;guard=guard+1;end
    if (!injected) $fatal(1,"FAULT_TRIGGER_NOT_OBSERVED");
    if (fault_kind==14) begin
      repeat (3) begin @(negedge clk);#3;reset_outputs();end
      rst_n=1;
    end
    guard=0;
    while (fault_kind!=14 && error_seen+cancellation_seen==0 && guard<450000) begin
      @(negedge clk);#3;guard=guard+1;
    end
    if (queued!=0 ||
        (fault_kind<=8 && (error_seen!=1 || cancellation_seen!=0)) ||
        (fault_kind>=9 && fault_kind!=14 && (cancellation_seen!=1 || error_seen!=0)))
      $fatal(1,"FAULT_COMPLETION_NOT_OBSERVED kind=%0d error=%0d cancel=%0d queue=%0d",
        fault_kind,error_seen,cancellation_seen,queued);
    if (publication_transfers!=(fault_kind==13 ? 1:0))
      $fatal(1,"FAULT_COMMIT_TRANSFER_COUNT");
    if ((fault_kind==9 || fault_kind==11) && drain_responses==0)
      $fatal(1,"CANCEL_OUTSTANDING_NOT_EXERCISED");
    if ((fault_kind==12 || fault_kind==13) && stalled_commit_edges<3)
      $fatal(1,"COMMIT_STALL_NOT_EXERCISED");
    if (fault_kind==15 && stalled_logit_edges<3)
      $fatal(1,"LOGIT_STALL_NOT_EXERCISED");
    repeat (4) begin @(negedge clk);#3;end
    rejected_continuation();
    test_phase=0;injected=0;held_request=0;held_banks=0;held_logit=0;held_commit=0;
    submit(0,1);success();
    submit(1,0);success();
    if (completed!=(fault_kind==8 ? 4:3) || error_seen!=(fault_kind<=8 ? 2:1))
      $fatal(1,"FAULT_RECOVERY_COUNTS");
    $display("FAULT_SUMMARY kind=%0d successes=%0d errors=%0d cancels=%0d drain_responses=%0d commits_before_abort=%0d recovery_frames=2 recovery_logits=%0d",
      fault_kind,completed,error_seen,cancellation_seen,drain_responses,publication_transfers,2*V);
    $finish;
  end
""" + text[end:]
    text = replace_once(text, "  initial begin\n    rst_n=0;", FAULT_TASKS +
                        "\n  initial begin\n    rst_n=0;")
    text = replace_once(text, "repeat (500000)", "repeat (2000000)")
    # This driver changes only host inputs, after the base negedge transactor.
    driver = r"""
  always @(negedge clk) begin
    #2;
    spoof_response=0;mem_rsp_error=0;
    if (rst_n && test_phase==1) begin
      if ((fault_kind==12 || fault_kind==13) && !injected)
        commit_ready=fault_kind==13 && stalled_commit_edges>=3;
      if (fault_kind==15 && !injected) logit_ready=0;
      if (!injected && fault_kind<=8 && mem_rsp_valid &&
          ((fault_kind==1 && queue_kind[response_slot]==1 && !queue_write[response_slot]) ||
           (fault_kind==2 && queue_kind[response_slot]==9 && queue_write[response_slot]) ||
           (fault_kind==3 && queue_kind[response_slot]==3) ||
           (fault_kind>=4 && queue_kind[response_slot]==0))) begin
        case (fault_kind)
          1,2: mem_rsp_error=1;
          3: mem_rsp_rdata=mem_rsp_rdata|32'h00010000;
          4: mem_rsp_rdata=32'h00007f80;
          5: begin mem_rsp_tag=64'hfffffffffffffffd;spoof_response=1;end
          6,8: begin mem_rsp_tag=prior_tag;response_bank=prior_bank;spoof_response=1;end
          7: begin
            if (B==1) $fatal(1,"WRONG_BANK_REQUIRES_MULTIPLE_BANKS");
            response_bank=(response_bank+1)%B;spoof_response=1;
          end
        endcase
        injected=1;abort_cycle=cycle;
      end
      if (!injected &&
          ((fault_kind==9 && mem_rsp_valid && queue_kind[response_slot]==1) ||
           (fault_kind==10 && norm_cycle>=0 && cycle==norm_cycle+60) ||
           (fault_kind==11 && mem_rsp_valid && queue_kind[response_slot]==9 &&
             !queue_write[response_slot]) ||
           (fault_kind==12 && commit_valid && stalled_commit_edges>=3) ||
           (fault_kind==13 && publication_transfers==1) ||
           (fault_kind==14 && mem_rsp_valid && queue_kind[response_slot]==1) ||
           (fault_kind==15 && logit_valid && stalled_logit_edges>=3))) begin
        if (fault_kind==10 && (key_count!=KD || value_count!=KD))
          $fatal(1,"QK_CANCELLATION_PHASE_NOT_OBSERVED");
        injected=1;abort_cycle=cycle;
        if (fault_kind==14) begin
          reset_probe=1;rst_n=0;queued=0;front=0;tail=0;mem_rsp_valid=0;
          held_request=0;held_banks=0;held_logit=0;held_commit=0;
        end else cancel=1;
      end else if (injected && cancel && cycle>abort_cycle) cancel=0;
    end else cancel=0;
  end
"""
    return replace_once(text, "\nendmodule\n", driver + "\nendmodule\n")


def run_fault_case(run, kind, compiled=None, geometry=Geometry(), seed=17,
                   banks=8, queue=3):
    if kind not in FAULT_CASES or kind == 7 and banks == 1:
        raise ValueError("unsupported fault-case geometry")
    images = run.path / "checkpoint-images"
    records = generate_images(images, geometry, seed, 2)
    bench = run.path / "fault_top_tb.sv"
    text = fault_bench()
    bench.write_text(text)
    parameters = {"H": geometry.hidden, "I": geometry.intermediate,
                  "QH": geometry.q_heads, "KH": geometry.kv_heads,
                  "D": geometry.head_dim, "V": geometry.vocabulary,
                  "M": geometry.max_sequence, "N": 2, "B": banks, "QUEUE": queue}
    binding = {"bench_sha256": hashlib.sha256(text.encode()).hexdigest(),
               "parameters": parameters, "source_sha256": run.hashes,
               "tool_versions": run.tool_versions}
    if compiled is not None and compiled["binding"] != binding:
        raise AssertionError("incompatible fault-transactor build reuse")
    if compiled is None:
        objects = run.path / "obj-fault-top"
        sources = [relative(p) for p in sorted((ROOT / "rtl").glob("anvil_qn1_*.sv"))]
        unrolling = (["--unroll-count", "256", "--unroll-stmts", "100000"]
                     if banks * queue >= 128 else [])
        run.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                     *unrolling, "--top-module", "top_tb",
                     *[f"-G{k}={v}" for k, v in parameters.items()],
                     "--Mdir", relative(objects), "-o", "simulate",
                     *sources, relative(bench)], "fault-top-compile")
        compiled = {"binary": relative(objects / "simulate"), "binding": binding}
    output = run.execute([compiled["binary"], f"+images={relative(images)}",
                          f"+fault={kind}"], f"fault-{kind:02d}-simulation")
    matches = re.findall(
        r"FAULT_SUMMARY kind=(\d+) successes=(\d+) errors=(\d+) cancels=(\d+) "
        r"drain_responses=(\d+) commits_before_abort=(\d+) recovery_frames=2 "
        r"recovery_logits=(\d+)", output)
    if len(matches) != 1 or int(matches[0][0]) != kind:
        raise AssertionError("missing fault/recovery independent comparison record")
    numbers = list(map(int, matches[0]))
    expected = [kind, 4 if kind == 8 else 3, 2 if kind <= 8 else 1,
                int(kind >= 9 and kind != 14)]
    if numbers[:4] != expected or numbers[5:] != [int(kind == 13), 2 * geometry.vocabulary]:
        raise AssertionError("fault/recovery coverage count mismatch")
    result = {"case": FAULT_CASES[kind], "kind": kind, "geometry": vars(geometry),
              "banks": banks, "queue": queue, "seed": seed, "reference": records,
              "counts": numbers, "compiled": compiled, "summary": output[-1500:]}
    (run.path / "fault-reference.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def run_fault_matrix(run):
    from resume_checks import fault_matrix

    return fault_matrix(run)
