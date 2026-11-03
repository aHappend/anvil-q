"""Public-pin token abort, tagged-drain, stale-response and recovery checks."""

import argparse
from fractions import Fraction
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, SuiteDeadline, simulate
from fp2_reference import exact, finite
from fp2_top_probe import TOP_TB, embedding, expected_logits
from fp2_benchmark_probe import CSR_TASK


CASES = (
    ("accept-edge-cancel", 0, (3, 0, 1, 0)),
    ("cancel-partial-prefetch", 1, (3, 0, 1, 0)),
    ("cancel-two-outstanding-and-old-responses", 2, (3, 0, 1, 0)),
    ("memory-error-response", 3, (3, 0, 1, 0)),
    ("malformed-response-tag", 4, (3, 0, 1, 0)),
    ("invalid-token-range", 5, (16, 0, 1, 0)),
    ("invalid-position-range", 6, (3, 3, 1, 0)),
    ("invalid-sequence-phase", 7, (3, 0, 0, 1)),
    ("nonfinite-embedding", 8, (3, 0, 1, 0)),
)


def testbench():
    text = TOP_TB.replace("module tb;", "module tb;" + CSR_TASK + r"""
  integer scenario=0,abort_count=0,cancel_count=0,fault_count=0,late_count=0,csr_checks=0;
  integer cancel_cycle=-1,suppressed_tokens=0,successful_count=0;
  reg command_accepted=0,cancel_issued=0,fault_issued=0,malformed_response=0,weight_held=0;
""", 1)
    for needle, replacement in (
        (".csr_req_valid(1'b0)", ".csr_req_valid(bench_csr_valid)"),
        (".csr_req_write(1'b0)", ".csr_req_write(bench_csr_write)"),
        (".csr_req_addr(16'd0)", ".csr_req_addr(bench_csr_addr)"),
        (".csr_req_wdata(32'd0)", ".csr_req_wdata(bench_csr_data)"),
        (".csr_req_wstrb(4'd0)", ".csr_req_wstrb(4'hf)"),
        (".csr_rsp_ready(1'b1)", ".csr_rsp_ready(bench_csr_ready)"),
    ):
        if text.count(needle) != 1:
            raise ValueError(f"protocol CSR anchor changed: {needle}")
        text = text.replace(needle, replacement, 1)
    text = text.replace("    rst_n=0;", """
    if(!$value$plusargs("SCENARIO=%d",scenario)) $fatal(1,"missing SCENARIO");
    rst_n=0;""", 1)
    text = text.replace("    while (cycle<500000) begin", r"""
    while (cycle<500000) begin
      cancel=0;
      if(command_index==0 && scenario==0 && !cancel_issued) begin
        cancel=1; cancel_issued=1; cancel_cycle=cycle;
      end
      if(command_index==0 && (scenario==1 || scenario==2) && !cancel_issued &&
         weight_held && outstanding>=(scenario==1 ? 1 : 2)) begin
        ddr_req_ready=0;
        bench_csr(16'h0000,0,0);
        if(bench_csr_observation !== 32'h00020200) $fatal(1,"CSR_DURING_STALLED_TOKEN");
        csr_checks=csr_checks+1;
        cancel=1; cancel_issued=1; cancel_cycle=cycle;
        for(i=0;i<16;i=i+1) if(pending[i]) due[i]=cycle+24+i;
      end
""", 1)
    text = text.replace("ddr_rsp_tag=tags[chosen]; ddr_rsp_rdata=responses[chosen];", r"""
          ddr_rsp_tag=tags[chosen]; ddr_rsp_rdata=responses[chosen]; ddr_rsp_error=0;
          malformed_response=0;
          if(command_index==0 && !fault_issued && (scenario==3 || scenario==4)) begin
            fault_issued=1;
            if(scenario==3) ddr_rsp_error=1;
            else begin ddr_rsp_tag=tags[chosen] ^ 64'h8000000000000000; malformed_response=1; end
          end
""", 1)
    text = text.replace("if (held_request &&", "if (!cancel && !fault_issued && held_request &&", 1)
    text = text.replace("if (held_logit &&", "if (!cancel && held_logit &&", 1)
    text = text.replace(
        "if (token_valid && token_ready) accepted_tokens=accepted_tokens+1;", r"""
      if(cancel && (token_ready !== 1'b0 || ddr_req_valid !== 1'b0 || logit_valid !== 1'b0))
        $fatal(1,"CANCEL_PRIORITY");
      if(cancel && token_valid) suppressed_tokens=suppressed_tokens+1;
      if (token_valid && token_ready) begin
        accepted_tokens=accepted_tokens+1; command_accepted=1;
      end""", 1)
    text = text.replace(
        "pending[active_response]=0; outstanding=outstanding-1;\n        response_count=response_count+1;",
        r"""
        if(malformed_response) begin
          fault_count=fault_count+1;
          due[active_response]=cycle+24;
        end else begin
          pending[active_response]=0; outstanding=outstanding-1;
          response_count=response_count+1;
          if(ddr_rsp_error) fault_count=fault_count+1;
          if(cancel_cycle>=0 && command_index==0) late_count=late_count+1;
        end""", 1)
    text = text.replace("pending[slot]=1; tags[slot]=ddr_req_tag; due[slot]=cycle+2+(random_state[9:6]);",
                        r"""
        pending[slot]=1; tags[slot]=ddr_req_tag; due[slot]=cycle+2+(random_state[9:6]);
        if(command_index==0 && (scenario==1 || scenario==2) && !cancel_issued && ddr_req_kind==1) begin
          due[slot]=1000000; weight_held=1;
        end""", 1)
    text = text.replace(
        "responses[slot]=read_beat(ddr_req_kind,ddr_req_row,ddr_req_col,ddr_req_format);", r"""
          responses[slot]=read_beat(ddr_req_kind,ddr_req_row,ddr_req_col,ddr_req_format);
          if(command_index==0 && scenario==8 && !fault_issued) begin
            responses[slot][15:0]=16'h7fc0; fault_issued=1; fault_count=fault_count+1;
          end""", 1)
    start = text.index("      if(done) begin")
    end = text.index("      previous_logit_accept=", start)
    text = text[:start] + r"""
      if(cancel_done) begin
        if(command_index!=0 || !cancel_issued || outstanding!=0 || cancel)
          $fatal(1,"CANCEL_DONE_BEFORE_DRAIN");
        cancel_count=cancel_count+1;
      end
      if(done || (cancel_done && scenario==0)) begin
        if(command_index==0) begin
          if(outstanding!=0 || logits!=0 || logit_valid) $fatal(1,"ABORT_LEAK_OR_UNDRAINED");
          if(scenario==0) begin
            if(done || accepted_tokens!=0) $fatal(1,"CANCEL_ACCEPTED_NEW_TOKEN");
          end else begin
            if(!done || error !== 1'b1 || accepted_tokens!=1) $fatal(1,"MISSING_ERROR_COMPLETION");
            abort_count=abort_count+1;
          end
          if(scenario<=2 && cancel_done !== 1'b1) $fatal(1,"MISSING_CANCEL_COMPLETION");
          $display("ABORT_OBSERVED %0d %0d %0d %0d",scenario,accepted_tokens,outstanding,cycle);
          command_index=1; command_accepted=0; logits=0;
        end else begin
          if(!done || error || cancel_done || logits!=16 || outstanding!=0 ||
             !previous_logit_accept) $fatal(1,"RECOVERY_COMPLETION");
          successful_count=successful_count+1;
          if(scenario==2 && (maximum_outstanding<2 || late_count<2 || csr_checks!=1))
            $fatal(1,"MISSING_TWO_RESPONSE_DRAIN");
          if(scenario==1 && (late_count<1 || csr_checks!=1)) $fatal(1,"MISSING_PARTIAL_DRAIN");
          if(scenario==0 && suppressed_tokens!=1) $fatal(1,"MISSING_CANCEL_EDGE");
          if((scenario==3 || scenario==4 || scenario==8) && fault_count!=1)
            $fatal(1,"MISSING_FAULT_INJECTION");
          if(response_count!=reads+writes) $fatal(1,"REQUEST_RESPONSE_CONSERVATION");
          $display("CASE_SUMMARY %0d %0d %0d %0d %0d %0d %0d %0d %0d",
            scenario,abort_count,cancel_count,fault_count,late_count,csr_checks,
            successful_count,response_count,reads+writes);
          $finish;
        end
      end
""" + text[end:]
    text = text.replace("token_valid=accepted_tokens==command_index;",
                        "token_valid=command_index<command_count && !command_accepted;", 1)
    return text


def run(probe, scenario, first_command, seed=17):
    source = probe.directory / "tb.sv"
    source.write_text(testbench())
    images = probe.directory / "checkpoint-images"
    images.mkdir()
    image = images / "embeddings.hex"
    image.write_text("".join(f"{embedding(row,column):04x}\n"
                             for row in range(16) for column in range(48)))
    commands = images / "commands.txt"
    commands.write_text("2\n" + " ".join(map(str, first_command)) + "\n4 0 1 0\n")
    rtl = sorted((ROOT / "anvil_q2_fp_reference/rtl").glob("*.sv"))
    rtl += sorted((ROOT / "rtl").glob("*.sv"))
    output = simulate(probe, source, rtl, "verilator",
                      [f"+IMAGE={image.relative_to(ROOT)}", f"+COMMANDS={commands.relative_to(ROOT)}",
                       f"+SEED={seed}", f"+SCENARIO={scenario}"])
    logits, summaries, aborts = {}, [], []
    for line in output.read_text().splitlines():
        words = line.split()
        if words[:1] == ["LOGIT"]:
            command, index, bits = int(words[1]), int(words[2]), int(words[3], 16)
            if command != 1 or index in logits or not 0 <= index < 16:
                raise AssertionError("aborted/stale/duplicate logit")
            logits[index] = bits
        elif words[:1] == ["CASE_SUMMARY"]:
            summaries.append(list(map(int, words[1:])))
        elif words[:1] == ["ABORT_OBSERVED"]:
            aborts.append(list(map(int, words[1:])))
    probe.compare("public-abort-observation", 1, len(aborts), {})
    probe.compare("recovery-logit-count", 16, len(logits), {})
    reference = expected_logits(4)
    for index, bits in logits.items():
        difference = abs(exact(bits) - exact(reference[index])) if finite(bits) else None
        probe.compare("fresh-sequence-independent-logit", True, difference is not None and
                      difference <= Fraction(5, 10000) * (1 + abs(exact(reference[index]))),
                      {"index": index, "bits": f"{bits:08x}"})
    if len(summaries) != 1 or len(summaries[0]) != 9:
        raise AssertionError("missing complete protocol observations")
    observed = summaries[0]
    probe.compare("error-completion-count", int(scenario != 0), observed[1], {})
    probe.compare("cancel-completion-count", int(scenario <= 2), observed[2], {})
    probe.compare("fault-observed", int(scenario in (3, 4, 8)), observed[3], {})
    probe.compare("recovery-success-count", 1, observed[6], {})
    probe.compare("external-obligation-conservation", observed[7], observed[8], {})
    probe.summary["protocol_case"] = {"scenario": scenario, "first_command": first_command,
                                      "seed": seed, "observations": observed, "aborts": aborts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=[case[0] for case in CASES], default=CASES[2][0])
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if args.all:
        from verify import Suite
        suite = Suite("protocol-cases", preparation=True)
        error = None
        try:
            with SuiteDeadline():
                for name, scenario, command in CASES:
                    suite.execute(name, lambda p: run(p, scenario, command))
        except Exception as failure:
            error = f"{type(failure).__name__}: {failure}"
        return suite.probe.settle(error)
    name, scenario, command = next(case for case in CASES if case[0] == args.case)
    probe = Probe(name, repair_of=
                  "evidence/preparation/fp2-cancel-two-outstanding-and-old-responses-20261102T185029Z-e0618d62/receipt.json")
    probe.receipt["repair_description"] = (
        "Hold projection payload reads, not the serial embedding startup read, so the "
        "required two-outstanding prefetch event can actually occur before cancellation.")
    try:
        with SuiteDeadline():
            run(probe, scenario, command)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
