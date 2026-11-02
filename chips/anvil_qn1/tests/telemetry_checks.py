"""Integrated public-transaction/CSR comparisons, independent of internal events."""

import hashlib
import json
import re

from execution import ROOT, relative
from model import Geometry
from speculation_checks import replace_once, speculative_bench, speculation_images


TELEMETRY_TASKS = r"""
  task csr_access(input integer write_access,input integer address_value,
                  input reg [31:0] data_value,input integer expected_error,
                  input reg [31:0] expected_value);
    reg [32:0] held_response;
    integer wait_cycles;
    begin
      @(negedge clk);#2;csr_write=write_access;csr_addr=address_value;
      csr_wdata=data_value;csr_rsp_ready=0;
      wait_cycles=0;
      while (csr_ready!==1 && wait_cycles<100) begin
        @(negedge clk);#2;wait_cycles=wait_cycles+1;
      end
      if (csr_ready!==1) $fatal(1,"INTEGRATED_CSR_NOT_READY");
      csr_valid=1;@(posedge clk);
      if (csr_ready!==1) $fatal(1,"INTEGRATED_CSR_ACCEPT");
      #1;if (csr_rsp_valid!==0) $fatal(1,"INTEGRATED_CSR_ZERO_LATENCY");
      @(negedge clk);#2;csr_valid=0;
      @(posedge clk);#1;
      if (csr_rsp_valid!==1 || csr_error!==expected_error[0] ||
          csr_rdata!==expected_value)
        $fatal(1,"INTEGRATED_CSR_COMPARE addr=%h got=%h error=%b expected=%h error=%0d",
          address_value,csr_rdata,csr_error,expected_value,expected_error);
      held_response={csr_error,csr_rdata};
      repeat (3) begin
        @(posedge clk);#1;
        if (csr_rsp_valid!==1 || {csr_error,csr_rdata}!==held_response)
          $fatal(1,"INTEGRATED_CSR_STALL");
      end
      @(negedge clk);#2;csr_rsp_ready=1;
      @(posedge clk);
      if (csr_rsp_valid!==1) $fatal(1,"INTEGRATED_CSR_RETIRE");
      #1;@(negedge clk);#2;
      if (csr_rsp_valid!==0) $fatal(1,"INTEGRATED_CSR_DUPLICATE_RESPONSE");
      csr_comparisons=csr_comparisons+1;
    end
  endtask
  task check_counters;
    integer saved_busy,saved_think,saved_direct,saved_generated;
    begin
      saved_busy=observed_busy_cycles;saved_think=observed_think_cycles;
      saved_direct=observed_direct_cycles;saved_generated=observed_think_tokens;
      // Snapshot while idle must not clear, recount, or resume a transaction.
      csr_access(1,12'h008,3,0,0);
      csr_access(0,12'h080,0,0,1);
      csr_access(0,12'h010,0,0,saved_busy);
      csr_access(0,12'h014,0,0,0);
      csr_access(0,12'h018,0,0,saved_think);
      csr_access(0,12'h01c,0,0,0);
      csr_access(0,12'h020,0,0,saved_direct);
      csr_access(0,12'h024,0,0,0);
      csr_access(0,12'h028,0,0,saved_generated);
      csr_access(0,12'h02c,0,0,0);
      csr_access(0,12'h030,0,0,observed_direct_tokens);
      csr_access(0,12'h034,0,0,0);
      csr_access(0,12'h050,0,0,observed_drafts);
      csr_access(0,12'h054,0,0,0);
      csr_access(0,12'h058,0,0,observed_verified);
      csr_access(0,12'h05c,0,0,0);
      csr_access(0,12'h060,0,0,expected_accepted);
      csr_access(0,12'h064,0,0,0);
      csr_access(0,12'h068,0,0,observed_drafts-expected_accepted);
      csr_access(0,12'h06c,0,0,0);
      csr_access(0,12'h070,0,0,0);
      csr_access(0,12'h074,0,0,0);
      csr_access(0,12'h078,0,0,0);
      csr_access(0,12'h07c,0,0,0);
      csr_access(0,12'h04c,0,0,0);
      csr_access(0,12'h048,0,0,expected_max_score);
      csr_access(0,12'h00c,0,0,2);
      csr_access(0,12'h084,0,0,0);
      csr_access(0,12'h088,0,0,0);
      csr_access(0,12'h08c,0,0,0);
      csr_access(0,12'h090,0,0,0);
      csr_access(0,12'h094,0,0,0);
      csr_access(0,12'h098,0,0,0);
      if (saved_busy!=saved_think+saved_direct || saved_think==0 || saved_direct==0 ||
          saved_generated==0 || observed_drafts==0 || observed_verified==0)
        $fatal(1,"INTEGRATED_CSR_EVENT_COVERAGE");
      csr_access(1,12'h008,5,0,0);
      csr_access(1,12'h008,3,0,0);
      csr_access(0,12'h080,0,0,2);
      csr_access(0,12'h010,0,0,0);
      csr_access(0,12'h028,0,0,0);
      csr_access(0,12'h050,0,0,0);
      csr_access(0,12'h058,0,0,0);
      csr_access(0,12'h060,0,0,0);
      csr_access(0,12'h068,0,0,0);
      csr_access(0,12'h048,0,0,0);
      if (observed_busy_cycles!=saved_busy || observed_think_tokens!=saved_generated)
        $fatal(1,"INTEGRATED_CSR_IDLE_SIDE_EFFECT");
      $display("TELEMETRY_SUMMARY comparisons=%0d busy=%0d thinking_busy=%0d direct_busy=%0d thinking_tokens=%0d direct_tokens=%0d drafts=%0d verified=%0d accepted=%0d rejected=%0d busy_errors=%0d",
        csr_comparisons,saved_busy,saved_think,saved_direct,saved_generated,
        observed_direct_tokens,observed_drafts,observed_verified,expected_accepted,
        observed_drafts-expected_accepted,busy_errors);
    end
  endtask
"""


def telemetry_bench():
    text = speculative_bench()
    text = replace_once(
        text, "reg csr_valid=0,configured_mode=0;",
        "reg csr_valid=0,configured_mode=0,csr_write=1,csr_rsp_ready=1;\n"
        "  reg [11:0] csr_addr=12'h008;\n"
        "  reg [31:0] csr_wdata=1;\n"
        "  reg transaction_owned=0;\n"
        "  integer observed_busy_cycles=0,observed_think_cycles=0,observed_direct_cycles=0;\n"
        "  integer observed_think_tokens=0,observed_direct_tokens=0,observed_drafts=0;\n"
        "  integer observed_verified=0,expected_accepted=0,csr_comparisons=0,busy_errors=0;\n"
        "  reg [31:0] expected_max_score=0;")
    text = replace_once(text,
                        ".csr_write(1'b1),.csr_addr(12'h008),\n"
                        "    .csr_wdata(32'd1)",
                        ".csr_write(csr_write),.csr_addr(csr_addr),\n"
                        "    .csr_wdata(csr_wdata)")
    text = replace_once(text, ".csr_rsp_ready(1'b1)", ".csr_rsp_ready(csr_rsp_ready)")
    text = replace_once(
        text, "cycle=cycle+1;",
        "cycle=cycle+1;\n"
        "      if (transaction_owned) begin\n"
        "        observed_busy_cycles=observed_busy_cycles+1;\n"
        "        if (think_active) observed_think_cycles=observed_think_cycles+1;\n"
        "        else observed_direct_cycles=observed_direct_cycles+1;\n"
        "      end\n"
        "      if (done) transaction_owned=0;\n"
        "      if (token_valid && token_ready) transaction_owned=1;\n"
        "      if (draft_valid && draft_ready) observed_drafts=observed_drafts+draft_counts[active_tx];\n"
        "      if (commit_valid && commit_ready) begin\n"
        "        if (think_active) observed_think_tokens=observed_think_tokens+commit_count;\n"
        "        else observed_direct_tokens=observed_direct_tokens+commit_count;\n"
        "      end")
    text = replace_once(
        text, "total_frames=total_frames+1;active_case=active_case+1;new_evaluation=1;",
        "if (logit_count>V && host_phases[active_tx]) observed_verified=observed_verified+1;\n"
        "          total_frames=total_frames+1;active_case=active_case+1;new_evaluation=1;")
    text = replace_once(
        text, "@(negedge clk);token_valid=0;new_sequence=0;\n      guard=0;",
        "@(negedge clk);token_valid=0;new_sequence=0;\n"
        "      if (c==1) begin\n"
        "        csr_access(1,12'h008,0,1,0);busy_errors=busy_errors+1;\n"
        "        csr_access(1,12'h088,32'h12345678,1,0);busy_errors=busy_errors+1;\n"
        "        if (think_active!==1 || completed!=1 || commit_seen!=0)\n"
        "          $fatal(1,\"INTEGRATED_BUSY_CSR_PRECONDITION\");\n"
        "      end\n"
        "      guard=0;")
    text = replace_once(
        text, '$display("SUMMARY transactions=%0d frames=%0d logits=%0d ',
        "repeat (3) begin @(negedge clk);#2;end\n"
        "    if (!$value$plusargs(\"accepted=%d\",expected_accepted) ||\n"
        "        !$value$plusargs(\"max-score=%h\",expected_max_score))\n"
        "      $fatal(1,\"MISSING_ACCEPTED_REFERENCE\");\n"
        "    check_counters();\n"
        '$display("SUMMARY transactions=%0d frames=%0d logits=%0d ')
    return replace_once(text, "  initial begin\n    rst_n=0;",
                        TELEMETRY_TASKS + "\n  initial begin\n    rst_n=0;")


def run_telemetry(run, geometry=Geometry(), seed=17, prefix=4, compiled=None):
    images = run.path / "checkpoint-images"
    evaluations, transactions = speculation_images(images, geometry, seed, prefix,
                                                   storage_evaluations=8,
                                                   storage_transactions=3,
                                                   minimum_steps=6)
    if len(transactions) != 3:
        raise ValueError("integrated telemetry fixture expects three transactions")
    # Count matching children along the independently generated public path.
    accepted = 0
    for transaction in transactions:
        parent = 4
        for token in transaction["generated"]:
            children = [i for i, (node, ancestor) in enumerate(
                zip(transaction["nodes"], transaction["parents"]))
                if ancestor == parent and node == token]
            if not children:
                break
            accepted += 1
            parent = children[0]
    bench = run.path / "telemetry_tb.sv"
    text = telemetry_bench()
    bench.write_text(text)
    parameters = {"H": geometry.hidden, "I": geometry.intermediate,
                  "QH": geometry.q_heads, "KH": geometry.kv_heads,
                  "D": geometry.head_dim, "V": geometry.vocabulary,
                  "M": geometry.max_sequence, "N": 8, "T": len(transactions)}
    binding = {"bench_sha256": hashlib.sha256(text.encode()).hexdigest(),
               "parameters": parameters, "source_sha256": run.hashes,
               "tool_versions": run.tool_versions}
    if compiled is not None and compiled["binding"] != binding:
        raise AssertionError("incompatible integrated-telemetry build reuse")
    if compiled is None:
        objects = run.path / "obj-telemetry"
        sources = [relative(p) for p in sorted((ROOT / "rtl").glob("anvil_qn1_*.sv"))]
        run.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                     "--top-module", "top_tb", *[f"-G{k}={v}" for k, v in parameters.items()],
                     "--Mdir", relative(objects), "-o", "simulate", *sources, relative(bench)],
                    "telemetry-compile")
        compiled = {"binary": relative(objects / "simulate"), "binding": binding}
    maximum_score = evaluations[-1]["maximum_absolute_score"]
    output = run.execute([compiled["binary"], f"+images={relative(images)}",
                          f"+accepted={accepted}", f"+max-score={maximum_score:08x}"],
                         "telemetry-simulation")
    matches = re.findall(
        r"TELEMETRY_SUMMARY comparisons=(\d+) busy=(\d+) thinking_busy=(\d+) "
        r"direct_busy=(\d+) thinking_tokens=(\d+) direct_tokens=(\d+) drafts=(\d+) "
        r"verified=(\d+) accepted=(\d+) rejected=(\d+) busy_errors=(\d+)", output)
    if len(matches) != 1:
        raise AssertionError("missing integrated CSR/public-handshake comparisons")
    counts = list(map(int, matches[0]))
    expected_tokens = sum(len(t["generated"]) for t in transactions)
    expected_drafts = sum(len(t["nodes"]) for t in transactions)
    if (counts[0] != 45 or counts[1] != counts[2] + counts[3] or
            counts[4:] != [expected_tokens, 0, expected_drafts,
                           len(evaluations) - len(transactions),
                           accepted, expected_drafts - accepted, 2]):
        raise AssertionError(f"integrated telemetry coverage mismatch: {counts}")
    expected_summary = (f"SUMMARY transactions=3 frames={len(evaluations)} "
                        f"logits={len(evaluations)*geometry.vocabulary} "
                        f"key_writes={len(evaluations)*geometry.kv_dimension} "
                        f"value_writes={len(evaluations)*geometry.kv_dimension}")
    if output.count(expected_summary) != 1:
        raise AssertionError("integrated telemetry did not compare complete frames/KV")
    result = {"geometry": vars(geometry), "seed": seed, "prefix": prefix,
              "counts": counts, "maximum_absolute_score": maximum_score,
              "evaluations": evaluations, "transactions": transactions,
              "compiled": compiled, "summary": output[-2000:]}
    (run.path / "telemetry-reference.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
