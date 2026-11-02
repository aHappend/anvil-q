"""Public top cancellation/fault/drain/restart checks, without internal probes."""

from execution import ROOT, compiled, relative, run_compiled
from integration import TOP_TB, key_bits
from model import Fixture


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise AssertionError(f"Control harness hook changed: {old}")
    return text.replace(old, new)


def check(evidence, banks=1, mode=0, fp8=0, affine=0):
    results = []
    fixture = Fixture(cache_mode=mode, fp8=fp8, affine=affine, check_budget=evidence.ensure_budget)
    initial = dict(fixture.memory)
    fixture.token(token=1)
    initial.update({key: value for key, value in fixture.memory.items() if key[0] == 11})
    text = "0 0 2 0\n"
    text += "".join(f"0 {key_bits(key):026x} {value:08x}\n" for key, value in sorted(initial.items()))
    text += "".join(f"1 {key_bits(key):026x} {value:08x}\n" for key, value in fixture.writes)
    text += "".join(f"2 {index:026x} {value:08x}\n" for index, value in enumerate(fixture.logits[0]))
    rtl = [relative(path) for path in sorted((ROOT / "rtl").glob("*.sv"))]
    rtl += ["anvil_q3_reference/rtl/anvil_q3_bank_scheduler.sv",
            "anvil_q3_reference/rtl/anvil_q3_mem_port.sv"]
    for scenario in ("cancel-fill", "cancel-cache", "cancel-logit", "cancel-active",
                     "cancel-result-hold", "memory-fault", "cache-fault", "active-fault"):
        evidence.ensure_budget()
        tb = TOP_TB.replace("localparam B=1;", f"localparam B={banks}, VOCAB=3;")
        tb = tb.replace(".CACHE_MODE(0)", f".CACHE_MODE({mode}),.MODE1_FP8({fp8}),.INT4_ASYM({affine})")
        tb = tb.replace("integer low,high,middle,", """
          reg injected=0,trigger=0,abort_expected=0;
          integer cancel_pulses=0,error_completions=0,restart_logits=0;
          reg previous_done=0,previous_cancel_done=0;
          reg queued_error[0:B-1][0:31];
          integer low,high,middle,""")
        tb = replace_once(tb, "if (held_logit &&", "if (!cancel && !abort_expected && held_logit &&")
        tb = replace_once(tb, "if (held_request[bank] &&", "if (!cancel && !abort_expected && held_request[bank] &&")
        tb = replace_once(tb, "if (mem_req_write[bank]) begin",
                          "if (mem_req_write[bank] && accepted_token==2) begin")
        # Canceled writes still reach memory, but do not consume successful-run expectations.
        tb = replace_once(tb, "if (memory_index<0 && !mutable_used[mutable_index])", """
          if (mem_req_write[bank]) begin
            mutable_key[mutable_index]=key; mutable_used[mutable_index]=1;
            mutable_data[mutable_index]=mem_req_wdata[bank*32+:32];
          end
          if (memory_index<0 && !mutable_used[mutable_index])""")
        tb = replace_once(tb, "due[bank][queue_tail[bank]]=cycle+2+(requests%5);", """
          queued_error[bank][queue_tail[bank]]=0;
          if (accepted_token==1 && !injected && mem_req_kind[bank*4+:4]==1) begin
            trigger=1;
            @FAULT@
          end
          due[bank][queue_tail[bank]]=cycle+9+(requests%5);""")
        tb = replace_once(tb, "if (token_valid && token_ready) begin", """
          if (cancel || ((mem_rsp_valid & mem_rsp_ready & mem_rsp_error)!=0)) abort_expected=1;
          if (done && previous_done) $fatal(1,"done not a pulse");
          if (cancel_done && previous_cancel_done) $fatal(1,"cancel_done not a pulse");
          previous_done=done; previous_cancel_done=cancel_done;
          if (cancel_done) cancel_pulses=cancel_pulses+1;
          if (cancel && (token_ready || logit_valid)) $fatal(1,"cancel priority");
          if (accepted_token==1 && logit_valid && logit_ready) $fatal(1,"aborted token emitted logit");
          if (token_valid && token_ready) begin
            if (accepted_token==1) begin abort_expected=0; held_request=0; held_logit=0; end""")
        tb = replace_once(tb, "if (error!==1'b0) $fatal", """
          if (completed_token==0) begin
            if (error!==1'b1 || !injected || compared_logits!=0)
              $fatal(1,"missing observable injected error");
            for (bank=0;bank<B;bank=bank+1)
              if (occupied[bank]!=0) $fatal(1,"done before external drain");
            error_completions=error_completions+1;
          end else if (error!==1'b0) $fatal""")
        tb = replace_once(tb, "if (accepted_token!=TOKENS ||", """
          if (error_completions!=1 || cancel_pulses!=@CANCELS@)
            $fatal(1,"missing injected completion/restart");
          if (accepted_token!=TOKENS ||""")
        tb = replace_once(tb, "token_valid=accepted_token<TOKENS;", """
          cancel=0;
          if (@TRIGGER@ && accepted_token==1 && !injected) begin
            cancel=1; injected=1;
          end
          token_valid=accepted_token<TOKENS && (accepted_token==0 || completed_token==1);""")
        tb = replace_once(tb, "token_id=accepted_token%VOCAB; token_pos=accepted_token;",
                          "token_id=accepted_token==0 ? 0 : 1; token_pos=0;")
        tb = replace_once(tb, "new_sequence=accepted_token==0; token_phase=accepted_token>=2;",
                          "new_sequence=1; token_phase=0;")
        tb = replace_once(tb, "logit_ready=cycle%13<9;",
                          "logit_ready=accepted_token==2 && cycle%13<9;")
        tb = replace_once(tb, "mem_rsp_valid[bank]=occupied[bank]!=0 && due[bank][queue_head[bank]]<=cycle;", """
          mem_rsp_valid[bank]=occupied[bank]!=0 && due[bank][queue_head[bank]]<=cycle;
          mem_rsp_error[bank]=mem_rsp_valid[bank] && queued_error[bank][queue_head[bank]];""")
        if scenario in ("cancel-cache", "cache-fault"):
            tb = replace_once(tb, "if (accepted_token==1 && !injected && mem_req_kind[bank*4+:4]==1) begin", """
              if (accepted_token==1 && !injected && mem_req_write[bank] &&
                (mem_req_kind[bank*4+:4]==9 || mem_req_kind[bank*4+:4]==10 ||
                 mem_req_kind[bank*4+:4]>=12)) begin""")
        if scenario in ("cancel-active", "active-fault"):
            tb = replace_once(tb, "if (accepted_token==1 && !injected && mem_req_kind[bank*4+:4]==1) begin", """
              if (accepted_token==1 && !injected && mem_req_write[bank] &&
                mem_req_kind[bank*4+:4]==8 && mem_req_row[bank*32+:32]==2) begin""")
        if scenario == "cancel-result-hold":
            tb = replace_once(tb, "mem_req_ready[bank]=(cycle+bank)%7<5;", """
              mem_req_ready[bank]=(cycle+bank)%7<5 &&
                !(accepted_token==1 && mem_req_valid[bank] && mem_req_write[bank] &&
                  mem_req_kind[bank*4+:4]==8 && mem_req_row[bank*32+:32]==2);""")
        is_fault = scenario in ("memory-fault", "cache-fault", "active-fault")
        tb = tb.replace("@FAULT@", "queued_error[bank][queue_tail[bank]]=1; injected=1;"
                        if is_fault else "")
        held_projection = """mem_req_valid[0] && !mem_req_ready[0] && mem_req_write[0] &&
          mem_req_kind[0+:4]==8 && mem_req_row[0+:32]==2"""
        tb = tb.replace("@TRIGGER@", "1'b0" if is_fault else
                        "logit_valid" if scenario == "cancel-logit" else
                        held_projection if scenario == "cancel-result-hold" else "trigger")
        tb = tb.replace("@CANCELS@", "0" if is_fault else "1")
        name = f"control-{scenario}-b{banks}-m{mode}-f{fp8}-a{affine}"
        executable = compiled(evidence, name, tb, rtl)
        output = run_compiled(evidence, executable, name, {"vectors.txt": text})
        results.append({"case": scenario, "banks": banks, "cache_mode": mode,
                        "fp8": fp8, "affine": affine, "restart_logits": fixture.vocab,
                        "restart_writes": len(fixture.writes), "stdout": relative(output)})
    return results


def rejected_sequence(evidence, case, banks=1):
    """A valid token, a rejected command with no memory side effects, then restart."""
    fixture = Fixture(check_budget=evidence.ensure_budget)
    initial = dict(fixture.memory)
    fixture.token()
    initial.update({key: value for key, value in fixture.memory.items() if key[0] == 11})
    text = "0 0 3 0\n"
    text += "".join(f"0 {key_bits(key):026x} {value:08x}\n" for key, value in sorted(initial.items()))
    text += "".join(f"1 {key_bits(key):026x} {value:08x}\n" for key, value in fixture.writes * 2)
    text += "".join(f"2 {index:026x} {value:08x}\n"
                    for index, value in enumerate(fixture.logits[0] * 2))
    tb = TOP_TB.replace("localparam B=1;", f"localparam B={banks}, VOCAB=3;")
    tb = replace_once(tb, "if (error!==1'b0) $fatal", """
        if (completed_token==1) begin
          if (error!==1'b1 || requests!=rejected_requests || compared_logits!=3)
            $fatal(1,"invalid sequence command accepted or changed public memory/logits");
        end else if (error!==1'b0) $fatal""")
    tb = replace_once(tb, "integer dtype,awq,TOKENS,", "integer rejected_requests=0;\ninteger dtype,awq,TOKENS,")
    tb = replace_once(tb, "accepted_token=accepted_token+1; token_start=cycle;",
                      "accepted_token=accepted_token+1; if (accepted_token==2) rejected_requests=requests; token_start=cycle;")
    tb = replace_once(tb, "token_id=accepted_token%VOCAB; token_pos=accepted_token;", """
      token_id=0; token_pos=accepted_token==1 ? @POSITION@ : 0;
      token_fp16=accepted_token==1 && @DTYPE@;""")
    tb = replace_once(tb, "new_sequence=accepted_token==0; token_phase=accepted_token>=2;",
                      "new_sequence=accepted_token!=1; token_phase=@PHASE@;")
    values = {"dtype": ("1", "1'b1", "1'b0"),
              "position": ("2", "1'b0", "1'b0"),
              "phase-reversal": ("1", "1'b0", "accepted_token==0"),
              "token-id": ("1", "1'b0", "1'b0")}
    if case not in values:
        raise ValueError(f"Unknown rejection scenario {case}")
    position, dtype, phase = values[case]
    tb = tb.replace("@POSITION@", position).replace("@DTYPE@", dtype).replace("@PHASE@", phase)
    if case == "token-id":
        tb = replace_once(tb, "token_id=0; token_pos=", "token_id=accepted_token==1 ? 3 : 0; token_pos=")
    rtl = [relative(path) for path in sorted((ROOT / "rtl").glob("*.sv"))]
    rtl += ["anvil_q3_reference/rtl/anvil_q3_bank_scheduler.sv",
            "anvil_q3_reference/rtl/anvil_q3_mem_port.sv"]
    name = f"rejected-{case}-b{banks}"
    executable = compiled(evidence, name, tb, rtl)
    output = run_compiled(evidence, executable, name, {"vectors.txt": text})
    return {"case": case, "successful_logits": 6, "rejected_commands": 1,
            "stdout": relative(output)}
