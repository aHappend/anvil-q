"""Public-pin transaction conservation and response-association checks."""

import shutil

from execution import ROOT, VERILATOR_UNROLL, sha256, write_json


def scheduler_case(run, banks=8, depth=3, simulator="iverilog", rtl=None, must_fail=False, wrap=0):
    folder = run.path / (f"scheduler-b{banks}-q{depth}-{simulator}" + (f"-wrap{wrap}" if wrap else ""))
    folder.mkdir()
    sources = rtl if rtl is not None else ["rtl/anvil_q3_bank_scheduler.sv"]
    parameters = {"BANKS": banks, "QUEUE_DEPTH": depth}
    if wrap:
        if rtl is not None or must_fail or wrap not in (1, 2):
            raise ValueError("wrap boundary is a separate non-mutation leaf experiment")
        original = ROOT / "rtl/anvil_q3_bank_scheduler.sv"
        copied = folder / original.name
        shutil.copyfile(original, copied)
        text = copied.read_text()
        before = "holding<=0; next_tag<=0; wrap_pending<=0; draining<=0;"
        after = "holding<=0; next_tag<=64'hfffffffffffffffe; wrap_pending<=0; draining<=0;"
        if text.count(before) != 1:
            raise AssertionError("nonunique scheduler reset seeding site")
        copied.write_text(text.replace(before, after, 1))
        sources = [run.rel(copied)]
        parameters["WRAP_TEST"] = wrap
        write_json(folder / "boundary-initial-state.json", {
            "original_sha256": sha256(original), "copied_sha256": sha256(copied),
            "before": before, "after": after,
            "scope": "isolated initial-state boundary acceleration; unchanged 64-bit wrap/drain "
                     "logic and public-pin scoreboard; not 2^64 production reset-to-wrap transfers"})
    if simulator == "iverilog":
        binary = folder / "scheduler.vvp"
        run.tool(["iverilog", "-g2012", "-Wall", "-s", "scheduler_tb",
                  "-o", run.rel(binary),
                  *[f"-Pscheduler_tb.{k}={v}" for k, v in parameters.items()],
                  *sources, "tests/scheduler_tb.sv"])
        command = ["vvp", run.rel(binary)]
    else:
        obj = folder / "obj"
        run.tool(["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                  *VERILATOR_UNROLL,
                  "--top-module", "scheduler_tb", "--Mdir", run.rel(obj), "-o", "scheduler",
                  *[f"-G{k}={v}" for k, v in parameters.items()],
                  *sources, "tests/scheduler_tb.sv"])
        command = [run.rel(obj / "scheduler")]
    text, receipt = run.tool([*command, "+directory=" + run.rel(folder)],
                             expected=(0, 1, -6) if must_fail else (0,))
    if must_fail:
        if receipt["exit_code"] == 0 or not any(assertion in text for assertion in (
                "SCHEDULER response association/order", "SCHEDULER live tag alias",
                "SCHEDULER client stability", "SCHEDULER bus stability")):
            raise AssertionError("scheduler mutation survived or failed without a functional assertion")
        return {"functional_mutation_killed": True, "assertion": text,
                "stdout": receipt["stdout"]}
    lines = (folder / "scheduler.tsv").read_text().splitlines()
    if wrap:
        if (f"SCHEDULER_WRAP_COMPLETE variant={wrap} transactions=3" not in text or
                lines != [f"WRAP {wrap} 3"]):
            raise AssertionError("incomplete wrap boundary comparisons")
        result = {"banks": banks, "queue_depth": depth, "simulator": simulator,
                  "initial_state_accelerated_copy": True, "issued_and_compared": 3,
                  "tags": [str((1 << 64) - 2), str((1 << 64) - 1), "0"],
                  "variant": "response-and-client-drain" if wrap == 1 else "cancellation-drain",
                  "stdout": receipt["stdout"]}
        write_json(folder / "result.json", result)
        return result
    if ("SCHEDULER_COMPLETE transactions=160" not in text or len(lines) != 10 or
            lines[1:] != ["FAULT 0", "FAULT 1", "FAULT 2", "FLUSH 0", "FLUSH 1",
                          "RESET 0", "RESET 1", "RESET 2", "RECOVERY 1"]):
        raise AssertionError("incomplete scheduler comparisons")
    normal = list(map(int, lines[0].split()[1:]))
    if normal[:4] != [160] * 4:
        raise AssertionError("unconserved scheduler transactions")
    result = {"banks": banks, "queue_depth": depth, "simulator": simulator,
              "accepted": normal[0], "issued": normal[1], "responded": normal[2],
              "retired": normal[3], "associated_memory_errors": normal[4],
              "reordered_responses": normal[5], "simultaneous_bank_requests": normal[6],
              "simultaneous_bank_responses": normal[7], "retire_issue_edges": normal[8],
              "longest_request_stall_cycles": normal[9],
              "longest_client_response_stall_cycles": normal[10],
              "fault_cases": ["unknown", "duplicate", "wrong-bank" if banks > 1 else "unknown"],
              "flush_cases": ["idle", "held-request-accepted-on-flush-edge"],
              "same_edge_issue_response_recovery": True,
              "reset_cases": ["held-bus-request", "accepted-unanswered-request",
                              "returned-client-stalled"],
              "stdout": receipt["stdout"],
              "scope": "scheduler public pins; bounded wrap is a separately source-bound copy"}
    write_json(folder / "result.json", result)
    return result
