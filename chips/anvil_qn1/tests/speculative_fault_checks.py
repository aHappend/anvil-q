"""Cancellation of real accepted-path target decoding, followed by fresh recovery."""

import hashlib
import json
import re

from execution import ROOT, relative
from model import Geometry
from speculation_checks import replace_once, speculative_bench, speculation_images


SPECULATIVE_CANCEL_CASES = {
    1: "root_frame_before_draft",
    2: "accepted_draft_projection",
    3: "accepted_draft_attention",
    4: "unpublished_five_token_batch",
    5: "published_five_token_batch",
}


def speculative_cancel_bench():
    text = speculative_bench()
    text = replace_once(
        text, "reg new_evaluation=1;",
        "reg new_evaluation=1,aborting=0,recovered=0;\n"
        "  integer cancel_case=0,cancelled=0,cancel_edge=-1,commit_transfers=0;\n"
        "  integer cancelled_frames=0,cancelled_reads=0,stalled_commits=0,drained_responses=0;\n"
        "  integer interrupted=0,queue_kind[0:63];")
    text = replace_once(
        text, "if (error!==0 || cancel_done!==0 || think_active!==configured_mode)",
        "if (error!==0 || (!aborting && cancel_done!==0) || "
        "think_active!==configured_mode)")
    for kind in ("request", "logit", "commit"):
        text = replace_once(text, f"if (held_{kind} &&", f"if (!aborting && held_{kind} &&")
    text = replace_once(
        text, "if (mem_rsp_valid && mem_rsp_ready) begin",
        "if (cancel_done) begin\n"
        "        if (!aborting || queued!=0 || done!==0 || token_ready!==0 ||\n"
        "            commit_valid!==0 || logit_valid!==0)\n"
        "          $fatal(1,\"SPEC_CANCEL_DRAIN_OR_PUBLICATION\");\n"
        "        cancelled=cancelled+1;\n"
        "      end\n"
        "      if (aborting && (done!==0 || commit_valid!==0 || logit_valid!==0 || mem_req_valid!==0))\n"
        "        $fatal(1,\"SPEC_CANCEL_NEW_WORK\");\n"
        "      if (commit_valid && !commit_ready) stalled_commits=stalled_commits+1;\n"
        "      if (commit_valid && commit_ready) commit_transfers=commit_transfers+1;\n"
        "      if (mem_rsp_valid && mem_rsp_ready) begin\n"
        "        if (aborting) drained_responses=drained_responses+1;")
    text = replace_once(text, "queue_data[tail]=read_data; queue_tag[tail]=mem_req_tag;",
                        "queue_kind[tail]=mem_req_kind;\n"
                        "        queue_data[tail]=read_data; queue_tag[tail]=mem_req_tag;")
    text = replace_once(
        text, "commit_ready=(cycle%11>=5);",
        "commit_ready=(cycle%11>=5);\n"
        "      if (!recovered && active_tx==1 && cancel_case>=4)\n"
        "        commit_ready=cancel_case==5 && stalled_commits>=3;")
    text = replace_once(
        text, "while (completed<c+1 && guard<450000) begin @(negedge clk);guard=guard+1;end",
        "while (completed<c+1 && !aborting && guard<450000) begin\n"
        "        @(negedge clk);#3;guard=guard+1;\n"
        "      end\n"
        "      if (aborting) begin\n"
        "        guard=0;\n"
        "        while (!cancelled && guard<450000) begin\n"
        "          @(negedge clk);#3;guard=guard+1;\n"
        "        end\n"
        "        if (cancelled!=1 || queued!=0 || completed!=1 ||\n"
        "            commit_transfers!=(cancel_case==5 ? 1:0) ||\n"
        "            (cancel_case>=4 && stalled_commits<3) ||\n"
        "            ((cancel_case==2 || cancel_case==3) && drained_responses==0))\n"
        "          $fatal(1,\"SPEC_CANCEL_EVENT_COVERAGE\");\n"
        "        repeat (4) begin @(negedge clk);#3;end\n"
        "        if (token_ready!==1 || cancelled!=1 || think_active!==1)\n"
        "          $fatal(1,\"SPEC_CANCEL_MODE_OR_IDLE_RECOVERY\");\n"
        "        interrupted=interrupted+1;\n"
        "        // A new sequence abandons all physically written cancelled KV.\n"
        "        // No DUT reset or internal ownership modification is used.\n"
        "        recovered=1;aborting=0;completed=0;active_case=0;total_frames=0;\n"
        "        key_count=0;value_count=0;held_request=0;held_logit=0;held_commit=0;\n"
        "        new_evaluation=1;\n"
        "        for (j=0;j<M*KD;j=j+1) begin key_valid[j]=0;value_valid[j]=0;end\n"
        "        c=-1;\n"
        "      end else")
    text = replace_once(
        text, "if (key_count!=total_frames*KD || value_count!=total_frames*KD)",
        "if (c>=0 && (key_count!=total_frames*KD || value_count!=total_frames*KD))")
    text = replace_once(
        text, "    @(negedge clk);rst_n=1;",
        "    if (!$value$plusargs(\"cancel-case=%d\",cancel_case) || cancel_case<1 || cancel_case>5)\n"
        "      $fatal(1,\"SPEC_CANCEL_CASE_REQUIRED\");\n"
        "    @(negedge clk);rst_n=1;")
    text = replace_once(
        text, '$display("SUMMARY transactions=%0d frames=%0d logits=%0d ',
        "if (interrupted!=1 || !recovered || cancelled!=1)\n"
        "      $fatal(1,\"SPEC_CANCEL_RECOVERY_NOT_COMPARED\");\n"
        '$display("SPEC_CANCEL_SUMMARY case=%0d cancelled_frames=%0d cancelled_requests=%0d '
        'drained_responses=%0d commits_before_cancel=%0d recovery_frames=%0d recovery_transactions=%0d",\n'
        "      cancel_case,cancelled_frames,cancelled_reads,drained_responses,\n"
        "      cancel_case==5 ? 1:0,total_frames,completed);\n"
        '$display("SUMMARY transactions=%0d frames=%0d logits=%0d ')
    text = replace_once(text, "repeat (500000)", "repeat (2000000)")
    driver = r"""
  always @(negedge clk) begin
    #2;
    if (rst_n && !recovered && active_tx==1 && !aborting) begin
      if ((cancel_case==1 && total_frames==2 && !draft_seen) ||
          (cancel_case==2 && active_case==2 && mem_rsp_valid && queue_kind[front]==1 &&
            key_count==2*KD && value_count==2*KD) ||
          (cancel_case==3 && active_case==2 && mem_rsp_valid && queue_kind[front]==9) ||
          (cancel_case==4 && commit_valid && stalled_commits>=3) ||
          (cancel_case==5 && commit_transfers==1)) begin
        if (cancel_case>=2 && (!draft_seen || draft_counts[1]!=4))
          $fatal(1,"SPEC_CANCEL_DRAFT_NOT_ACCEPTED");
        if (cancel_case>=4 && (total_frames!=6 || key_count!=6*KD || value_count!=6*KD))
          $fatal(1,"SPEC_CANCEL_FULL_BATCH_NOT_EVALUATED");
        aborting=1;cancel=1;cancel_edge=cycle;
        cancelled_frames=total_frames-1;cancelled_reads=req_count;
      end
    end else if (cancel && cycle>cancel_edge) cancel=0;
  end
"""
    return replace_once(text, "\nendmodule\n", driver + "\nendmodule\n")


def run_speculative_cancel(run, kind=2, compiled=None, seed=17):
    if kind not in SPECULATIVE_CANCEL_CASES:
        raise ValueError("invalid speculative cancellation case")
    geometry = Geometry()
    images = run.path / "checkpoint-images"
    evaluations, transactions = speculation_images(images, geometry, seed, 4)
    text = speculative_cancel_bench()
    bench = run.path / "speculative_cancel_tb.sv"
    bench.write_text(text)
    parameters = {"N": len(evaluations), "T": len(transactions)}
    binding = {"bench_sha256": hashlib.sha256(text.encode()).hexdigest(),
               "parameters": parameters, "source_sha256": run.hashes,
               "tool_versions": run.tool_versions}
    if compiled is not None and compiled["binding"] != binding:
        raise AssertionError("incompatible speculative cancellation build reuse")
    if compiled is None:
        objects = run.path / "obj-speculative-cancel"
        sources = [relative(p) for p in sorted((ROOT / "rtl").glob("anvil_qn1_*.sv"))]
        run.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                     "--top-module", "top_tb", *[f"-G{k}={v}" for k, v in parameters.items()],
                     "--Mdir", relative(objects), "-o", "simulate", *sources, relative(bench)],
                    "speculative-cancel-compile")
        compiled = {"binary": relative(objects / "simulate"), "binding": binding}
    output = run.execute([compiled["binary"], f"+images={relative(images)}",
                          f"+cancel-case={kind}"], "speculative-cancel-simulation")
    matches = re.findall(
        r"SPEC_CANCEL_SUMMARY case=(\d+) cancelled_frames=(\d+) cancelled_requests=(\d+) "
        r"drained_responses=(\d+) commits_before_cancel=(\d+) recovery_frames=(\d+) "
        r"recovery_transactions=(\d+)", output)
    if len(matches) != 1:
        raise AssertionError("missing speculative cancellation/recovery comparison record")
    counts = list(map(int, matches[0]))
    if (counts[0] != kind or counts[4:] != [int(kind == 5), len(evaluations), len(transactions)]
            or counts[1] < 1 or counts[2] == 0):
        raise AssertionError("speculative cancellation coverage mismatch")
    summary = (f"SUMMARY transactions={len(transactions)} frames={len(evaluations)} "
               f"logits={len(evaluations)*geometry.vocabulary} "
               f"key_writes={len(evaluations)*geometry.kv_dimension} "
               f"value_writes={len(evaluations)*geometry.kv_dimension}")
    if output.count(summary) != 1:
        raise AssertionError("speculative cancellation recovery did not compare all frames/KV")
    result = {"case": SPECULATIVE_CANCEL_CASES[kind], "kind": kind, "seed": seed,
              "geometry": vars(geometry), "evaluations": evaluations,
              "transactions": transactions, "counts": counts, "compiled": compiled}
    (run.path / "speculative-cancel-reference.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def run_speculative_cancel_matrix(run):
    compiled = None
    results = []
    for kind in SPECULATIVE_CANCEL_CASES:
        result = run.component(
            f"speculative-cancel-case{kind}",
            lambda child, kind=kind: run_speculative_cancel(child, kind, compiled=compiled))
        compiled = result["compiled"]
        results.append(result)
    return {"cases": results, "case_count": len(results),
            "recovery_frames": sum(len(r["evaluations"]) for r in results)}
