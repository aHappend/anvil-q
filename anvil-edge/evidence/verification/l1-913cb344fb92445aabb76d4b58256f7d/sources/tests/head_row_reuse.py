"""Bounded public-port numerical/address A/B checks for output-head/row reuse.

Historical RTL is used only for the optional preparation comparison. Current L1
uses the delivered hierarchy, independent integer tensors and real DDR replies.
No cached tensor values or implementation state are supplied by the scoreboard.
"""

import copy
import difflib
import hashlib
import json
import re
import shutil
from pathlib import Path

from mapper_cache import SOURCES, fixture_bench, measured, require
from numerics import Geometry, Reference, core_test


ROOT = Path(__file__).resolve().parent.parent
BASELINE = (
    "evidence/preparation/official-qwen-shell-general-bypass-"
    "712c10b7d55d402ea5765e7ba02b0280/receipt.json"
)


def replace_once(text, before, after):
    require(text.count(before) == 1, f"Expected unique bench/source anchor: {before}")
    return text.replace(before, after)


def head_bench(bench, hidden, cached, lifecycle=False):
    """Augment, never replace, the existing independent write/logit comparisons."""
    declarations = r"""
  integer head_reads=0,head_weights=0,operation_start=0,head_start=0;
  integer operation_requests=0;
  reg head_phase=0;
"""
    bench = replace_once(bench, "  reg [11:0] kinds_seen=0;",
                         "  reg [11:0] kinds_seen=0;\n" + declarations)
    bench = replace_once(bench, "        requests=requests+1;", r"""
        requests=requests+1; operation_requests=operation_requests+1;
        if (head_phase) begin
          if (mem_req_write || (mem_req_kind!=0 &&
              !(mem_req_kind==8 && mem_req_row==14)))
            $fatal(1,"HEAD_UNEXPECTED_REQUEST");
          if (mem_req_kind==0) begin
            if (mem_req_row!==32'(head_weights/@H@) ||
                mem_req_col!==32'(head_weights%@H@))
              $fatal(1,"HEAD_PHYSICAL_WEIGHT_ORDER");
            head_weights=head_weights+1;
          end else begin
            if (mem_req_col!==32'(head_reads%@H@))
              $fatal(1,"HEAD_ACTIVATION_ORDER");
            head_reads=head_reads+1;
          end
        end
        if (mem_req_write && mem_req_kind==8 &&
            mem_req_row==14 && mem_req_col==@H@-1) begin
          if (head_phase) $fatal(1,"HEAD_DUPLICATE_FINAL_NORM");
          head_phase=1; head_start=cycles;
        end
""".replace("@H@", str(hidden)))
    bench = replace_once(bench, "        active_operation=active_operation+1;", """
        active_operation=active_operation+1;
        head_phase=0; head_reads=0; head_weights=0;
        operation_start=cycles; operation_requests=0;
""")
    bench = replace_once(bench, "        completions=completions+1;", f"""
        if (!head_phase || head_weights!=VOCAB*{hidden} ||
            head_reads!={hidden if cached else 'VOCAB*' + str(hidden)})
          $fatal(1,"HEAD_COUNTS reads=%0d weights=%0d",head_reads,head_weights);
        $display("HEAD_MEASURE %0d %0d %0d %0d %0d %0d",
          active_operation,cycles-operation_start,cycles-head_start,
          operation_requests,head_reads,head_weights);
        completions=completions+1;
""")
    if lifecycle:
        # Abort the second operation only after its vector is warm and a full
        # physical row has retired. Reset external memory and the scoreboard as
        # a new power-on epoch, then repeat the exact three-operation reference.
        start = bench.index("    rst_n=0; #0; reset_check();") + len(
            "    rst_n=0; #0; reset_check();")
        end = bench.index("    repeat (2) tick();", start)
        vectors = bench[start:end]
        stimulus = "token(1,0,1);\ntoken(2,1,0);\ntoken(0,2,0);"
        require(stimulus in bench, "Missing independent three-token stimulus")
        prefix = r"""
    token(1,0,1);
    @(negedge clk); #1; token_id=2; token_pos=1; new_sequence=0; token_valid=1;
    do begin @(posedge clk); end while (!token_ready);
    #1; @(negedge clk); #1; token_valid=0;
    wait (logit_valid && logit_index==1);
    if (!head_phase || head_weights<@H@*2 || head_reads!=@H@)
      $fatal(1,"HEAD_RESET_NOT_WARM");
    @(negedge clk); #1; rst_n=0;
    pending=0; mem_rsp_valid=0; mem_rsp_error=0;
    request_held=0; logit_held=0;
    requests=0; responses=0; write_count=0; logits=0; completions=0;
    comparisons=0; active_operation=-1; kinds_seen=0;
    head_phase=0; head_reads=0; head_weights=0;
    @VECTORS@
    repeat (2) tick(); @(negedge clk); #1; rst_n=1;
    $display("HEAD_RESET_RECOVERY warm_abort=1");
"""
        prefix = prefix.replace("@H@", str(hidden)).replace("@VECTORS@", vectors)
        bench = replace_once(bench, stimulus, prefix + stimulus)
    return bench


def metrics(result):
    text = (ROOT / result["simulation_receipt"]["stdout"]).read_text()
    rows = [dict(zip(("operation", "cycles", "head_cycles", "requests",
                      "activation_reads", "weight_reads"), map(int, match.groups())))
            for match in re.finditer(r"^HEAD_MEASURE (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)$",
                                     text, re.MULTILINE)]
    return {"rows": rows, "simulation_seconds": result["simulation_receipt"]["duration_s"],
            "simulation_receipt": result["simulation_receipt"],
            "bench_sha256": result["bench_sha256"]}


def error_bench(bench, target):
    """Error on an actual head DDR reply, followed by new-sequence recovery."""
    bench = head_bench(bench, 8, True)
    bench = replace_once(bench, "  reg head_phase=0;", """
  reg head_phase=0;
  reg inject_enabled=1,pending_injection=0;
  integer injected=0,failure_seen=0;
""")
    predicate = {
        "activation-read": "mem_req_kind==8 && mem_req_row==14 && mem_req_col==3",
        "weight-read": "mem_req_kind==0 && mem_req_row==2 && mem_req_col==3",
        "weight-nonfinite": "mem_req_kind==0 && mem_req_row==2 && mem_req_col==3",
    }[target]
    bench = replace_once(bench, "        requests=requests+1; operation_requests=operation_requests+1;",
                         f"""
        pending_injection=inject_enabled && head_phase && ({predicate});
        requests=requests+1; operation_requests=operation_requests+1;
""")
    bench = replace_once(
        bench, "begin mem_rsp_valid<=1; mem_rsp_rdata=memory[pending_slot]; end",
        """
      begin
        mem_rsp_valid<=1; mem_rsp_rdata=memory[pending_slot];
        mem_rsp_error=pending_injection && @BUS@;
        if (pending_injection) begin
          injected=injected+1;
          if (!@BUS@) mem_rsp_rdata=32'h7e00;
        end
      end
""".replace("@BUS@", str(int(target != "weight-nonfinite"))))
    start = bench.index("      if (done) begin") + len("      if (done) begin")
    end = bench.index("\n    end\n  end\n  task automatic tick;", start)
    success = bench[start:end]
    require(success.endswith("\n      end"), "Changed core completion block")
    success = success[:-len("\n      end")]
    expected_logits = 0 if target == "activation-read" else 2
    bench = bench[:start] + f"""
        if (inject_enabled) begin
          if (error!==1 || injected!=1 || pending || failure_seen!=0 ||
              logits!={expected_logits} || active_operation!=0 || !head_phase)
            $fatal(1,"HEAD_ERROR_PROPAGATION error=%b injected=%0d logits=%0d",
                   error,injected,logits);
          failure_seen=failure_seen+1;
        end else begin
{success}
        end
      end""" + bench[end:]
    start = bench.index("    rst_n=0; #0; reset_check();") + len(
        "    rst_n=0; #0; reset_check();")
    end = bench.index("    repeat (2) tick();", start)
    vectors = bench[start:end]
    stimulus = "token(1,0,1);\ntoken(2,1,0);\ntoken(0,2,0);"
    prefix = r"""
    @(negedge clk); #1; token_id=1; token_pos=0; new_sequence=1; token_valid=1;
    do begin @(posedge clk); end while (!token_ready);
    #1; @(negedge clk); #1; token_valid=0;
    wait (failure_seen==1); repeat (3) tick();
    if (token_ready!==1 || done!==0 || error!==0 || pending ||
        mem_req_valid || mem_rsp_valid || injected!=1)
      $fatal(1,"HEAD_ERROR_SETTLEMENT");
    @(negedge clk); #1;
    inject_enabled=0; pending_injection=0; mem_rsp_error=0;
    requests=0; responses=0; write_count=0; logits=0; completions=0;
    comparisons=0; active_operation=-1; kinds_seen=0;
    head_phase=0; head_reads=0; head_weights=0;
    @VECTORS@
    $display("HEAD_ERROR_RECOVERY @TARGET@ injected=%0d",injected);
"""
    prefix = prefix.replace("@VECTORS@", vectors).replace("@TARGET@", target)
    return replace_once(bench, stimulus, prefix + stimulus)


def historical(evidence):
    prior = ROOT / BASELINE
    receipt = json.loads(prior.read_bytes())
    overrides = dict(evidence.source_overrides)
    entries = []
    for source in ("rtl/anvil_q1_top.sv", "rtl/anvil_edge_tensor_mapper.sv"):
        retained = prior.parent / "sources" / source
        expected = receipt["source_sha256"][source]
        require(hashlib.sha256(retained.read_bytes()).hexdigest() == expected,
                f"Historical source hash mismatch: {source}")
        destination = evidence.path / ("before-" + Path(source).name)
        shutil.copyfile(retained, destination)
        overrides[source] = evidence.relative(destination)
        diff = evidence.path / (Path(source).stem + "-before-after.diff")
        diff.write_text("".join(difflib.unified_diff(
            retained.read_text().splitlines(True), (ROOT / source).read_text().splitlines(True),
            fromfile="before/" + source, tofile=source)), encoding="ascii")
        entries.append({"source": source, "before_sha256": expected,
                        "diff": evidence.relative(diff)})
    evidence.record["head_row_baseline"] = {
        "receipt": BASELINE, "sha256": hashlib.sha256(prior.read_bytes()).hexdigest(),
        "sources": entries,
        "scope": "Only two changed modules overridden; all other current RTL is identical",
    }
    before = copy.copy(evidence)
    before.source_overrides = overrides
    return before


def killed(evidence, name, source, edits, execute, assertion):
    original = (ROOT / source).read_text()
    changed = original
    for before, after in edits:
        changed = replace_once(changed, before, after)
    directory = evidence.path / ("reuse-mutant-" + name)
    directory.mkdir()
    path = directory / Path(source).name
    path.write_text(changed, encoding="ascii")
    diff = directory / "mutation.diff"
    diff.write_text("".join(difflib.unified_diff(
        original.splitlines(True), changed.splitlines(True),
        fromfile=source, tofile="mutant/" + source)), encoding="ascii")
    mutant = copy.copy(evidence)
    mutant.source_overrides = {**evidence.source_overrides, source: evidence.relative(path)}
    mutant.name_prefix = "reuse-mutant-" + name + "-"
    first = len(evidence.record["coverage"])
    failure = None
    try:
        execute(mutant)
    except Exception as error:
        failure = error
    rows = evidence.record["coverage"][first:]
    require(len(rows) == 1 and failure is not None, f"Reuse mutant survived: {name}")
    row = rows[0]
    child = row.get("simulation_receipt", {})
    require(row.get("compile_receipt", {}).get("exit_code") == 0 and
            child.get("exit_code") not in (0, None) and not child.get("timed_out") and
            child.get("child_settled") and child.get("process_group_settled"),
            f"Reuse mutant has no compiled, settled functional rejection: {name}")
    output = (ROOT / child["stdout"]).read_text() + (ROOT / child["stderr"]).read_text()
    require(assertion in output and "%Error:" in output,
            f"Reuse mutant missed original assertion {assertion}: {name}")
    row.update(status="expected-functional-rejection", mutation_assertion=assertion)
    evidence.record.setdefault("head_row_mutations", []).append({
        "name": name, "diff": evidence.relative(diff), "assertion": assertion,
        "simulation_receipt": child,
    })


def run_head_row_reuse(evidence, comparison=False):
    geometry = Geometry(vocabulary=17)
    before = historical(evidence) if comparison else None
    summary = []
    for seed in (1, 17, 89):
        ref = Reference(geometry, seed)
        for position, token in enumerate((1, 2, 0)):
            ref.token(token, position)
        normalized = [row["word"] for row in ref.trace if row["stage"] == "final-norm"]
        require(len(set(tuple(normalized[n:n+geometry.hidden])
                          for n in range(0, len(normalized), geometry.hidden))) == 3,
                "Activation epochs must differ to detect stale operation reuse")
        versions = [("after", evidence, True)]
        if before is not None:
            versions.insert(0, ("before", before, False))
        pair = {}
        for label, scope, cached in versions:
            case = copy.copy(scope)
            case.name_prefix = "head-" + label + "-"
            result = core_test(case, geometry, seed,
                               bench_transform=lambda bench, cached=cached:
                               head_bench(bench, geometry.hidden, cached))
            pair[label] = metrics(result)
            require(len(pair[label]["rows"]) == 3, "Missing operation measurements")
        if before is not None:
            for old, new in zip(pair["before"]["rows"], pair["after"]["rows"]):
                require(new["weight_reads"] == old["weight_reads"] == 136 and
                        old["requests"] - new["requests"] == 128 and
                        new["cycles"] < old["cycles"], "Head A/B conservation/speedup failed")
        summary.append({"seed": seed, "geometry": geometry.__dict__, **pair})
    evidence.record["head_reuse_measurements"] = summary
    # Reset during a warm, backpressured logit frame, then prove a fresh epoch.
    reset_scope = copy.copy(evidence)
    reset_scope.name_prefix = "head-warm-reset-"
    result = core_test(reset_scope, geometry, 17,
                       bench_transform=lambda bench: head_bench(bench, 8, True, True))
    require("HEAD_RESET_RECOVERY warm_abort=1" in
            (ROOT / result["simulation_receipt"]["stdout"]).read_text(),
            "No warm reset/recovery observed")
    for target in ("activation-read", "weight-read", "weight-nonfinite"):
        scope = copy.copy(evidence)
        scope.name_prefix = "head-error-" + target + "-"
        result = core_test(scope, geometry, 17,
                           bench_transform=lambda bench, target=target:
                           error_bench(bench, target))
        require(f"HEAD_ERROR_RECOVERY {target} injected=1" in
                (ROOT / result["simulation_receipt"]["stdout"]).read_text(),
                "Head read error/nonfinite recovery was not exercised")
    # A larger, multilayer geometry prevents a vector-length-specialized pass.
    scope = copy.copy(evidence)
    scope.name_prefix = "head-wide-"
    core_test(scope, Geometry(layers=2, hidden=16, intermediate=24, query_heads=2,
                              vocabulary=17), 89,
              bench_transform=lambda bench: head_bench(bench, 16, True))
    # This compact three-operation case stays below 500k cycles; the interpreter
    # independently checks four-state startup and held outputs.
    scope = copy.copy(evidence)
    scope.name_prefix = "head-four-state-"
    scope.simulator_override = "iverilog"
    core_test(scope, geometry, 17,
              bench_transform=lambda bench: head_bench(bench, 8, True))

    row_metrics = []
    for seed in (1, 17, 89):
        bench, labels = fixture_bench(evidence, seed, False, row_reuse=True)
        pair = {}
        for label, scope in ([("before", before)] if before is not None else []) + [
                ("after", evidence)]:
            result = scope.simulate(f"row-{label}-s{seed}", bench, SOURCES, len(labels))
            rows = measured(evidence, result, labels)
            require(all(row["data_requests"] == 1 for row in rows),
                    "Row cache bypassed physical tensor requests")
            pair[label] = {"rows": rows, "cycles": sum(row["cycles"] for row in rows),
                           "simulation_seconds": result["simulation_receipt"]["duration_s"],
                           "bench_sha256": result["bench_sha256"],
                           "receipt": result["simulation_receipt"]}
        if before is not None:
            require(pair["before"]["bench_sha256"] == pair["after"]["bench_sha256"] and
                    pair["after"]["cycles"] < pair["before"]["cycles"] and
                    [r["directory_requests"] for r in pair["before"]["rows"]] ==
                    [r["directory_requests"] for r in pair["after"]["rows"]],
                    "Row A/B changed stimulus/descriptors or did not reduce cycles")
        row_metrics.append({"seed": seed, **pair})
        lifecycle_bench, lifecycle_labels = fixture_bench(evidence, seed, True, row_reuse=True)
        result = evidence.simulate(f"row-lifecycle-s{seed}", lifecycle_bench, SOURCES,
                                   len(lifecycle_labels))
        lifecycle_rows = measured(evidence, result, lifecycle_labels)
        by_label = {row["label"]: row for row in lifecycle_rows}
        for label in ("withdraw-row-refill", "reset-refill", "same-address-reload"):
            require(by_label[label]["directory_requests"] > 0,
                    f"Epoch invalidation did not cause descriptor refill: {label}")
        for label in ("withdraw-warm-row", "withdraw-row-hit", "reset-hit",
                      "same-address-hit"):
            require(by_label[label]["directory_requests"] == 0,
                    f"Warm row/descriptor hit not observed: {label}")
        evidence.record.setdefault("row_reuse_lifecycle", []).append({
            "seed": seed, "rows": lifecycle_rows,
            "simulation_receipt": result["simulation_receipt"],
        })
    evidence.record["row_reuse_measurements"] = row_metrics
    for name, edits, assertion in (
        ("wrong-component", [("head_activation_q<=head_activations[component];",
                             "head_activation_q<=head_activations[0];")],
         "CORE_NUMERIC_LOGIT"),
        ("cross-operation", [
            ("        activation_reuse_valid<=0;\n        if (token_id",
             "        activation_reuse_valid<=activation_reuse_valid;\n        if (token_id"),
            ("FINISH: begin activation_reuse_valid<=0; state<=IDLE; end",
             "FINISH: begin state<=IDLE; end")], "CORE_NUMERIC_LOGIT"),
    ):
        killed(evidence, name, "rtl/anvil_q1_top.sv", edits,
               lambda scope: core_test(scope, geometry, 17), assertion)
    for name, edits, assertion in (
        ("wrong-row", [("cache_row[descriptor_cache_index]==request_row;",
                       "1'b1;")], "CACHE_DATA_TUPLE"),
        ("withdrawal", [("if (!config_valid || !cache_context_matches) begin",
                        "if (1'b0) begin")], "CACHE_RESPONSE"),
    ):
        killed(evidence, name, SOURCES[-1], edits,
               lambda scope: scope.simulate("row-lifecycle", lifecycle_bench, SOURCES,
                                             len(lifecycle_labels)), assertion)


def run_head_row_shell(evidence):
    """Same SPI image and public DDR/byte oracle before/after, two small extents."""
    from qwen_shell import shell_case

    before = historical(evidence)
    measurements = []
    for capacity in (257, 1025):
        inputs = evidence.path / f"shell-capacity-{capacity}"
        inputs.mkdir()
        evidence.child(["./.venv/bin/python", "tests/qwen_shell.py",
                        evidence.relative(inputs), "--compact", str(capacity)],
                       f"reuse-shell-reference-{capacity}")
        info = json.loads((inputs / "shell-reference.json").read_bytes())
        pair = {}
        for label, scope in (("before", before), ("after", evidence)):
            case = copy.copy(scope)
            case.name_prefix = f"reuse-shell-{capacity}-{label}-"
            result = shell_case(case, info, 17, 1, True)
            text = (ROOT / result["simulation_receipt"]["stdout"]).read_text()
            operations = [
                {"position": int(m[1]), "token": int(m[2]), "cycle": int(m[3])}
                for m in re.finditer(
                    r"QWEN_SHELL_OPERATION frame=0 position=(\d+) token=(\d+) cycles=(\d+)",
                    text)]
            boot = re.findall(r"QWEN_SHELL_BOOT .* cycles=(\d+)", text)
            completion = re.findall(r"QWEN_SHELL_COMPLETION frame=0 cycles=(\d+)", text)
            require(len(boot) == len(completion) == 1 and len(operations) == 9,
                    "Missing integrated cycle/operation measurements")
            pair[label] = {
                "operations": operations, "boot_cycle": int(boot[0]),
                "completion_cycle": int(completion[0]),
                "inference_cycles": int(completion[0]) - operations[0]["cycle"],
                "simulation_seconds": result["simulation_receipt"]["duration_s"],
                "bench_sha256": result["bench_sha256"],
                "simulation_receipt": result["simulation_receipt"],
                "comparisons": result["actual_comparisons"],
            }
        require(pair["before"]["bench_sha256"] == pair["after"]["bench_sha256"] and
                pair["before"]["boot_cycle"] == pair["after"]["boot_cycle"] and
                pair["after"]["inference_cycles"] < pair["before"]["inference_cycles"] and
                [(r["position"], r["token"]) for r in pair["before"]["operations"]] ==
                [(r["position"], r["token"]) for r in pair["after"]["operations"]],
                "Integrated A/B changed stimulus, boot, feedback identity or did not improve")
        measurements.append({"capacity": capacity, "active_vocabulary": 257,
                             "seed": 17, "transport": "bypass", **pair})
    evidence.record["head_row_shell_measurements"] = measurements
    evidence.record["head_row_shell_scope"] = (
        "Synthetic H8/L1, two physical capacities, same byte/physical-weight/write oracle. "
        "Not complete tokenizer tables, full-model execution or an authorized full-table retry."
    )
