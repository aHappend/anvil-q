"""Actual shipped-source Yosys checks; frontend/tool failures remain failures."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, execute, hashes, relative, remaining, timestamp
from yosys_frontend import materialize


COMPACT = {
    "NUM_LAYERS": 1, "HIDDEN_SIZE": 8, "INTERMEDIATE_SIZE": 8,
    "NUM_Q_HEADS": 1, "NUM_KV_HEADS": 1, "HEAD_DIM": 8,
    "GROUP_SIZE": 1, "VOCAB_SIZE": 1, "MAX_SEQ_LEN": 1,
    "TILE_BEATS": 1, "KV_WINDOW": 1, "FLASH_TILE": 3,
}


def account(netlist, top):
    modules = netlist["modules"]
    cells = Counter()
    hierarchy = Counter()
    stack = [top]
    while stack:
        name = stack.pop()
        hierarchy[name] += 1
        for cell in modules[name]["cells"].values():
            kind = cell["type"]
            cells[kind] += 1
            if kind in modules:
                stack.append(kind)
    forbidden = {kind: count for kind, count in cells.items()
                 if "latch" in kind.lower() or kind in ("$div", "$mod", "$divfloor", "$modfloor")}
    if forbidden:
        raise AssertionError(f"forbidden runtime/latch cells: {forbidden}")
    return dict(cells=dict(cells), hierarchy=dict(hierarchy))


def run(output, diagnostic=False, compact_only=False, job=None):
    sources = " ".join(materialize(output))
    jobs = [("default-hierarchy", "anvil_q1_ht3_top", {}, False),
            ("compact-mapped", "anvil_q1_ht3_top", COMPACT, True)]
    jobs += [(name, f"anvil_q1_ht3_{name}", params, mapped) for name, params, mapped in (
        ("fp32_add", {}, True), ("fp32_mul", {}, True), ("fp32_divsqrt", {}, True),
        ("fp32_exp", {}, True), ("fp32_sincos", {}, True),
        ("epilogue_fusion", {"MAX_VECTOR": 8, "HEAD_DIM": 8}, False),
        ("flash_attn", {"NUM_Q_HEADS": 1, "NUM_KV_HEADS": 1, "HEAD_DIM": 8,
                        "MAX_SEQ_LEN": 1, "TILE_TOKENS": 3}, False))]
    if job:
        jobs = [entry for entry in jobs if entry[0] == job]
        if not jobs:
            raise ValueError(f"unknown synthesis job {job}")
    elif compact_only:
        jobs = jobs[1:2]
    elif diagnostic:
        jobs = jobs[:1]
    rows = []
    for identifier, top, parameters, mapped in jobs:
        directory = output / f"{identifier}-{uuid.uuid4().hex[:8]}"
        directory.mkdir()
        netlist_path = directory / "netlist.json"
        stat_path = directory / "statistics.json"
        parameter_cmd = ("chparam " + " ".join(f"-set {p} {v}" for p,v in parameters.items())
                         + f" {top}; " if parameters else "")
        script = (f"read_verilog -sv {sources}; {parameter_cmd}"
                  f"hierarchy -check -top {top}; proc; opt_expr; opt_clean; "
                  "check -noinit; memory -nomap; opt_clean; "
                  "select -assert-none t:$dlatch t:$adlatch t:$div t:$mod t:$divfloor t:$modfloor; "
                  + ("techmap; opt; abc; opt_clean; check -noinit; "
                     "select -assert-none t:$_DLATCH_* t:$div t:$mod; " if mapped else "")
                  + f"tee -o {relative(stat_path)} stat -json; write_json {relative(netlist_path)}")
        script_path = directory / "synthesis.ys"
        script_path.write_text(script+"\n")
        try:
            execute(["yosys", "-Q", "-T", "-s", relative(script_path)], directory,
                    "synthesis", ["yosys", "-V"])
            if not netlist_path.is_file() or not stat_path.is_file():
                raise AssertionError("Yosys zero exit without complete netlist/statistics")
            netlist = json.loads(netlist_path.read_text())
            counts = account(netlist, top)
            if identifier == "default-hierarchy":
                lane_count = sum(count for name, count in counts["hierarchy"].items()
                                 if "anvil_q1_ht3_mac_lane" in name)
                if lane_count != 256:
                    raise AssertionError(f"default physical MAC lanes={lane_count}, expected 256")
                for module in ("tensor_array", "epilogue_fusion", "flash_attn",
                               "panel_prefetch", "transport"):
                    if not any(f"anvil_q1_ht3_{module}" in name for name in counts["hierarchy"]):
                        raise AssertionError(f"missing substantive {module} hierarchy")
            if not counts["cells"]:
                raise AssertionError("empty synthesis hierarchy")
            row = dict(id=identifier, status="passed", parameters=parameters,
                       mapped=mapped, accounting=counts)
        except (RuntimeError, AssertionError, ValueError) as exc:
            row = dict(id=identifier, status="failed", parameters=parameters,
                       mapped=mapped, error=str(exc))
        row["receipt"] = relative(directory / "synthesis.receipt.json")
        rows.append(row)
    result = dict(status="passed" if all(r["status"] == "passed" for r in rows) else "failed",
                  runs=rows, diagnostic=diagnostic, compact_only=compact_only,
                  job=job, frontend=relative(output / "frontend.json"))
    with (output / "result.json").open("x") as out:
        json.dump(result, out, indent=2)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--diagnostic", action="store_true")
    mode.add_argument("--compact-only", action="store_true")
    mode.add_argument("--job", choices=("default-hierarchy", "compact-mapped", "fp32_add",
                                       "fp32_mul", "fp32_divsqrt", "fp32_exp", "fp32_sincos",
                                       "epilogue_fusion", "flash_attn"))
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_synthesis.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    result = run(output, args.diagnostic, args.compact_only, args.job)
    receipt.update(exit=0 if result["status"] == "passed" else 1,
                   timed_out=remaining() <= 0 or any(
                       json.loads(p.read_text()).get("timed_out", False)
                       for p in output.rglob("*.receipt.json")),
                   end=timestamp(),
                   result=relative(output / "result.json"))
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
