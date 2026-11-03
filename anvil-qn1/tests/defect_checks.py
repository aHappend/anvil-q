"""Executable disposable RTL mutations against unchanged public-pin oracles.

Each detection requires successful compilation followed by an exited, nonzero
simulation/checker with its declared comparison diagnostic. Compile errors,
timeouts, absent mutants and unrelated failures are infrastructure failures.
Accepted RTL, expected vectors and numerical thresholds are never modified.
"""

import difflib
import hashlib
import json
from pathlib import Path
import shutil

from control_checks import run_controller, run_csr
from execution import ROOT, relative
from integration import run_top
from leaf_checks import run_qk
from speculation_checks import replace_once, run_speculation


QK = "rtl/anvil_qn1_qknorm_rope.sv"
DECODER = "rtl/anvil_qn1_decoder.sv"
GEMV = "rtl/anvil_qn1_gemv.sv"
CTRL = "rtl/anvil_qn1_dual_think_ctrl.sv"
TOP = "rtl/anvil_qn1_top.sv"
SCHEDULER = "rtl/anvil_qn1_bank_scheduler.sv"
CSR = "rtl/anvil_qn1_csr_perf.sv"

# Every substitution is checked for uniqueness before a simulator is invoked.
MUTANTS = {
    "omit-qk-norm": (QK, "qk", (
        (".b(reciprocal),.in_error(reciprocal_failed)",
         ".b(32'h3f800000),.in_error(reciprocal_failed)"),
    ), ("QK_COMPARE",)),
    "share-query-gamma-with-key": (DECODER, "top", (
        (".start_gamma(state==K_CMD ? k_gamma : q_gamma)", ".start_gamma(q_gamma)"),
    ), ("SCRATCH_COMPARE", "KEY_COMPARE")),
    "adjacent-rope": (QK, "qk", (
        ("normalized_head[pair_index*16+:16]", "normalized_head[(2*pair_index)*16+:16]"),
        ("normalized_head[(pair_index+SH)*16+:16]", "normalized_head[(2*pair_index+1)*16+:16]"),
        ("rounded_output[pair_index*16+:16]", "rounded_output[(2*pair_index)*16+:16]"),
        ("rounded_output[(pair_index+SH)*16+:16]", "rounded_output[(2*pair_index+1)*16+:16]"),
    ), ("QK_COMPARE",)),
    # Repeating frequency zero makes every rotary frequency one (theta=1).
    "wrong-theta": (QK, "qk", (
        ("wire [31:0] c={cosine[pair_index*16+:16],16'd0};",
         "wire [31:0] c={cosine[0+:16],16'd0};"),
        ("wire [31:0] s={sine[pair_index*16+:16],16'd0};",
         "wire [31:0] s={sine[0+:16],16'd0};"),
    ), ("QK_COMPARE",)),
    "qkv-bias": (GEMV, "top", (
        ("w4<=start_w4; output_row<=0; base<=0; accumulator<=0; waiting<=0;",
         "w4<=start_w4; output_row<=0; base<=0;\n"
         "              accumulator<=start_w4 && start_proj<=2 ? 32'h3e800000 : 32'd0; waiting<=0;"),
        ("output_row<=output_row+1'b1; base<=0; accumulator<=0; state<=INITIALIZE;",
         "output_row<=output_row+1'b1; base<=0;\n"
         "                accumulator<=w4 && projection<=2 ? 32'h3e800000 : 32'd0; state<=INITIALIZE;"),
    ), ("SCRATCH_COMPARE", "KEY_COMPARE", "VALUE_COMPARE")),
    "q-o-hidden-extent": (DECODER, "top", (
        ("command_mlp ? minput : state==O_CMD ? Q_DIM : HIDDEN_SIZE;",
         "command_mlp ? minput : state==O_CMD ? HIDDEN_SIZE : HIDDEN_SIZE;"),
    ), ("SCRATCH_COMPARE",)),
    "accept-rejected-node": (CTRL, "controller", (
        ("nodes[i*32+:32]==target", "nodes[i*32+:32]!=target"),
    ), ("backend parent/position comparison", "commit token/slice comparison",
        "commit count/position", "unsolicited/extra backend request")),
    # Bypass the ownership-protected read address at the external-memory boundary.
    # During accepted-path evaluation this exposes the next, uncommitted slot.
    "expose-rejected-cache": (TOP, "branch", (
        (".req_layer(dreq_layer),.req_row(dreq_row),.req_col(dreq_col),",
         ".req_layer(dreq_layer),.req_row(!dreq_write &&\n"
         "        (dreq_kind==9 || dreq_kind==10) && draft_owned && backend_owned && !backend_root\n"
         "        ? dreq_row+32'd1 : dreq_row),.req_col(dreq_col),"),
    ), ("UNINITIALIZED_KEY_READ", "UNINITIALIZED_VALUE_READ", "CAUSAL_KV_ADDRESS",
        "SCRATCH_COMPARE")),
    "misassociate-response-tag": (SCHEDULER, "top", (
        ("output_tag<=client_tag[complete_slot];",
         "output_tag<=client_tag[complete_slot]^32'd1;"),
    ), ("TOP_UNEXPECTED_STATUS", "RESPONSE_SCOREBOARD", "SCRATCH_COMPARE")),
    "corrupt-csr-count": (CSR, "csr", (
        ("assign increment[3]=think_tokens;", "assign increment[3]=3'd0;"),
    ), ("CONTROL_PRE_COMPARE", "CONTROL_POST_COMPARE", "CONTROL_ACTIVE_COMPARE")),
    "corrupt-csr-snapshot": (CSR, "csr", (
        ("if (take_snapshot) snapshot[index]<=live[index];",
         "if (take_snapshot) snapshot[index]<=incremented[index];"),
    ), ("CONTROL_PRE_COMPARE", "CONTROL_POST_COMPARE", "CONTROL_ACTIVE_COMPARE")),
}


def oracle(run, kind):
    if kind == "qk":
        return run_qk(run, "verilator")
    if kind == "top":
        return run_top(run, "verilator", cases=1)
    if kind == "branch":
        return run_speculation(run, prefix=2, branching=True, minimum_steps=6)
    if kind == "controller":
        return run_controller(run)
    if kind == "csr":
        return run_csr(run, "verilator")
    raise ValueError(f"unknown mutation oracle: {kind}")


class MutatedSources:
    def __init__(self, run, sources, kind):
        self.run = run
        self.sources = sources
        self.kind = kind

    def __getattr__(self, name):
        return getattr(self.run, name)

    def execute(self, argv, name, **kwargs):
        replaced = [self.sources.get(str(arg), arg) for arg in argv]
        if name.endswith("-simulation"):
            kwargs["expected_exit"] = 1 if self.kind == "controller" else -6
        return self.run.execute(replaced, name, **kwargs)


def run_mutant(run, name):
    source, kind, substitutions, diagnostics = MUTANTS[name]
    original = (ROOT / source).read_text()
    changed = original
    for before, after in substitutions:
        changed = replace_once(changed, before, after)
    if changed == original:
        raise AssertionError(f"missing executable mutant {name}")
    clone = run.path / "mutant-source"
    clone.mkdir(exist_ok=False)
    paths = {}
    hashes = {}
    for path in sorted((ROOT / "rtl").glob("*.sv")):
        target = clone / path.name
        if relative(path) == source:
            target.write_text(changed)
        else:
            shutil.copyfile(path, target)
        paths[relative(path)] = relative(target)
        hashes[relative(path)] = {"original": run.hashes[relative(path)],
                                 "mutant": hashlib.sha256(target.read_bytes()).hexdigest()}
    delta = "".join(difflib.unified_diff(
        original.splitlines(True), changed.splitlines(True), fromfile=source,
        tofile=paths[source]))
    (run.path / "mutant.delta").write_text(delta)
    if any(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != identity["original"]
           for path, identity in hashes.items()):
        raise AssertionError("accepted RTL changed before the mutation experiment")
    first_command = len(run.commands)
    try:
        oracle(MutatedSources(run, paths, kind), kind)
    except (RuntimeError, AssertionError) as error:
        commands = run.commands[first_command:]
        compilations = [c for c in commands if c["argv"][0] == "verilator"]
        simulation = commands[-1] if commands else {}
        if (len(compilations) != 1 or compilations[0]["exit_code"] != 0 or
                not compilations[0]["child_settled"] or
                not Path(simulation.get("stdout", "")).name.endswith("-simulation.stdout.txt") or
                simulation.get("disposition") != "exited" or
                simulation.get("exit_code") in (None, 0) or
                not simulation.get("child_settled")):
            raise RuntimeError(f"{name}: not a valid defect detection: {error}") from error
        output = ((ROOT / simulation["stdout"]).read_text() + "\n" +
                  (ROOT / simulation["stderr"]).read_text())
        detected = [diagnostic for diagnostic in diagnostics if diagnostic in output]
        if not detected or any(marker in output for marker in (
                "CYCLE_BOUND", "TOKEN_LIVENESS", "MISSING_VECTORS", "OPEN_VECTORS",
                "READMEM", "cannot open", "No such file")):
            raise RuntimeError(f"{name}: unrelated/non-comparison simulation failure: {error}") from error
        if any(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != identity["original"]
               for path, identity in hashes.items()):
            raise AssertionError("accepted RTL changed during the mutation experiment")
        result = {"mutant": name, "oracle": kind, "changed_source": source,
                  "source_sha256": hashes, "delta": relative(run.path / "mutant.delta"),
                  "comparison_diagnostics": detected, "checker_exit": simulation["exit_code"],
                  "simulation_stdout": simulation["stdout"],
                  "simulation_stderr": simulation["stderr"],
                  "compilation_exit": compilations[0]["exit_code"],
                  "detected": True}
        (run.path / "detection.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    raise AssertionError(f"independent oracle failed to detect RTL mutant: {name}")


def run_defects(run):
    from campaign_checkpoints import defects_campaign

    return defects_campaign(run)
