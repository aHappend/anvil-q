"""Full-width scheduler boundary proofs on a documented quiescent state cut."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import execute, new_run, relative, source_hashes


def top_epoch(netlist_path, preparation=False):
    from native_model import descriptor

    netlist_path = netlist_path.resolve()
    directory = new_run("top-epoch-boundary", preparation)
    netlist = json.loads(netlist_path.read_text())
    top = netlist["modules"]["anvil_q4_fp_top"]
    removed = [name for name, cell in top["cells"].items()
               if cell["type"] in netlist["modules"]]
    words = descriptor(banks=1, vocabulary=1, intermediate=1, context=2, page_tokens=1)
    packed = sum(word << (32*index) for index, word in enumerate(words))
    constraints = {
        "cancel": "0", "token_valid": "1", "token_id": "0", "token_pos": "0",
        "new_sequence": "1", "token_phase": "0", "logit_ready": "1",
        "cfg_valid": "0", "cfg_commit": "0", "cfg_index": "0", "cfg_wdata": "0",
        "draft_valid": "0", "draft_token0": "0", "draft_token1": "0",
        "draft_pos": "0", "draft_new_sequence": "0", "verify_ready": "1",
        "cfg_done": "0", "cfg_error": "0",
        "legal.words": f"1024'h{packed:0256x}",
        "legal.spec_busy": "0", "legal.scheduler_idle": "1", "legal.routing_idle": "1",
        "legal.parent_cfg_ready": "1", "legal.cfg_busy": "0",
        "legal.scheduler_fault": "0", "legal.unit_done": "0", "legal.unit_error": "0",
        "legal.spec_verify_valid": "0", "legal.n_req_valid": "0", "legal.p_req_valid": "0",
    }
    common = ("-set-init-zero -set-init legal.epoch_serial 4294967295 " +
              " ".join(f"-set {name} {value}" for name, value in constraints.items()))
    script = directory / "boundary.ys"
    script.write_text(
        f"read_json {relative(netlist_path)}\n"
        "select -module anvil_q4_fp_top\n"
        + "\n".join(f"delete {name}" for name in removed) +
        "\nconnect -set rst_n 1'1\nopt_expr\nopt_clean\nasync2sync\n"
        "dffunmap\nopt_expr\nopt_clean\n"
        f"sat -seq 2 {common} -show token_ready -show done -show error\n"
        f"sat -seq 1 {common} -prove token_ready 1 -verify\n"
        f"sat -seq 2 -prove-skip 1 {common} -prove done 1 -prove error 1 -verify\n")
    receipt = execute(directory / "yosys", [
        "yosys", "-Q", "-T", "-s", relative(script)], timeout=600,
        extra_inputs=[netlist_path])
    output = (directory / "yosys/stdout.txt").read_text()
    if "SAT solving finished - model found:" not in output:
        raise AssertionError("Top boundary assumptions have no witness")
    (directory / "observed.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "netlist": relative(netlist_path),
        "initial_state_policy": "quiescent controller with sequence epoch serial 0xffffffff",
        "cut_leaf_instances": removed, "cut_constraints": constraints,
        "proved": "public token_ready before command; public done and error on the next edge",
        "scope": "actual synthesized top control cone with quiescent leaf cutpoints, "
                 "not a power-on reachability or datapath proof",
        "receipt": relative(directory / "yosys/receipt.json"),
        "duration_s": receipt["duration_s"]}, indent=2) + "\n")
    return directory


def run(preparation=False, repair_of=None):
    directory = new_run("identity-boundary", preparation)
    records = []
    for terminal in (0, 1):
        script = directory / f"boundary-{terminal}.ys"
        epoch = 0xffffffff if terminal else 0xfffffffe
        script.write_text(
            "read_verilog -formal -sv rtl/anvil_q4_fp_bank_scheduler.sv "
            "tests/identity_boundary_tb.sv\n"
            "hierarchy -check -top identity_boundary_tb "
            f"-chparam TERMINAL {terminal}\n"
            "proc\nflatten\nasync2sync\ndffunmap\nopt_expr\nopt_clean\n"
            f"sat -seq 64 -set-init-zero -set-init dut.legal.epoch {epoch} "
            "-set-init dut.legal.banks[0].next_serial 16777214 "
            "-prove-asserts -verify\n")
        execute(directory / f"yosys-{terminal}", [
            "yosys", "-Q", "-T", "-s", relative(script)], timeout=600, repair_of=repair_of)
        records.append({"terminal": bool(terminal), "initial_epoch": epoch,
                        "initial_serial": 16777214, "bound_edges": 64,
                        "receipt": relative(directory / f"yosys-{terminal}/receipt.json")})
    (directory / "observed.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "proofs": records,
        "initial_state_policy": "quiescent ownership state; all registers zero except "
            "the full-width epoch and bank serial counters stated above; rst_n held high",
        "assumptions": "single client/bank/slot, continuously willing requester, one-cycle "
            "tag-echoing error-free responder and continuously ready consumer; no flush",
        "scope": "bounded actual-RTL boundary-state proofs, not a power-on reachability "
            "proof of billions of prior transactions or a top sequence-epoch proof",
    }, indent=2) + "\n")
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run(args.preparation, args.repair_of)
