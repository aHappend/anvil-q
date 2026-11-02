"""Actual shipped-source Yosys checks; frontend/tool failures remain failures."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import os
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, execute, hashes, relative, remaining, timestamp
from yosys_frontend import materialize
from retention import digest


COMPACT = {
    "NUM_LAYERS": 1, "HIDDEN_SIZE": 8, "INTERMEDIATE_SIZE": 8,
    "NUM_Q_HEADS": 1, "NUM_KV_HEADS": 1, "HEAD_DIM": 8,
    "GROUP_SIZE": 1, "VOCAB_SIZE": 1, "MAX_SEQ_LEN": 1,
    "TILE_BEATS": 1, "KV_WINDOW": 1, "FLASH_TILE": 3,
}
JOBS = (
    ("default-hierarchy", "anvil_q1_ht3_top", {}, False),
    ("compact-mapped", "anvil_q1_ht3_top", COMPACT, True),
    ("compact-hierarchy", "anvil_q1_ht3_top", COMPACT, False),
    ("fp32_add", "anvil_q1_ht3_fp32_add", {}, True),
    ("fp32_mul", "anvil_q1_ht3_fp32_mul", {}, True),
    ("fp32_divsqrt", "anvil_q1_ht3_fp32_divsqrt", {}, True),
    ("fp32_exp", "anvil_q1_ht3_fp32_exp", {}, True),
    ("fp32_sincos", "anvil_q1_ht3_fp32_sincos", {}, True),
    ("epilogue_fusion", "anvil_q1_ht3_epilogue_fusion",
     {"MAX_VECTOR": 8, "HEAD_DIM": 8}, False),
    ("flash_attn", "anvil_q1_ht3_flash_attn",
     {"NUM_Q_HEADS": 1, "NUM_KV_HEADS": 1, "HEAD_DIM": 8,
      "MAX_SEQ_LEN": 1, "TILE_TOKENS": 3}, False),
)
JOB_BUDGETS = {"default-hierarchy": 360, "compact-mapped": 420,
               "compact-hierarchy": 180,
               "fp32_add": 60, "fp32_mul": 60, "fp32_divsqrt": 90,
               "fp32_exp": 90, "fp32_sincos": 120,
               "epilogue_fusion": 90, "flash_attn": 90}


def semantic_script(script, frontend, directory):
    for entry in frontend["transformations"]:
        script = script.replace(entry["output"], f"<source>/{Path(entry['output']).name}")
    for name in ("statistics.json", "netlist.json"):
        script = script.replace(relative(directory / name), f"<output>/{name}")
    return script


def retained_job(identifier, top, parameters, mapped, script, frontend, version):
    candidates = list((ROOT / "evidence/l1").glob("run-*/synthesis*/result.json"))
    candidates += list((ROOT / "evidence/preparation").glob("*/shard-*/result.json"))
    current = hashes()
    for result_path in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True):
        previous = json.loads(result_path.read_text())
        for row in previous.get("runs", []):
            if (row.get("id") != identifier or row.get("status") != "passed"
                    or row.get("parameters") != parameters or row.get("mapped") != mapped):
                continue
            receipt_path = ROOT / row["receipt"]
            receipt_path.resolve().relative_to(ROOT)
            if not receipt_path.is_file():
                continue
            receipt = json.loads(receipt_path.read_text())
            directory = receipt_path.parent
            old_frontend_path = directory.parent / "frontend.json"
            if (receipt.get("exit") != 0 or receipt.get("timed_out")
                    or receipt.get("tool_version", "").strip() != version
                    or receipt.get("tool_version_exit") != 0
                    or not old_frontend_path.is_file()):
                continue
            old_frontend = json.loads(old_frontend_path.read_text())
            if old_frontend.get("source_sha256") != frontend["source_sha256"]:
                continue
            transformation = lambda f: [{k: v for k, v in r.items() if k != "output"}
                                        for r in f["transformations"]]
            if transformation(old_frontend) != transformation(frontend):
                continue
            if any(receipt.get("source_sha256", {}).get(p) != current[p]
                   for p in frontend["source_sha256"]):
                continue
            old_script = directory / "synthesis.ys"
            if not old_script.is_file() or semantic_script(
                    old_script.read_text().strip(), old_frontend, directory) != script:
                continue
            artifacts = [directory / name for name in
                         ("netlist.json", "statistics.json", "synthesis.stdout.txt",
                          "synthesis.stderr.txt", "synthesis.ys")]
            if not all(path.is_file() for path in artifacts):
                continue
            if any(receipt.get("artifact_sha256", {}).get(receipt[key]) !=
                   hashlib.sha256((ROOT / receipt[key]).read_bytes()).hexdigest()
                   for key in ("stdout", "stderr")):
                continue
            counts = checked_account(json.loads(artifacts[0].read_text()), top,
                                     identifier, mapped)
            return dict(id=identifier, status="passed", parameters=parameters,
                        mapped=mapped, accounting=counts, receipt=relative(receipt_path),
                        reused=True, revalidated_by="exact command/frontend/tool/source; raw netlist",
                        artifact_sha256={relative(path): hashlib.sha256(path.read_bytes()).hexdigest()
                                         for path in [*artifacts, receipt_path, result_path]})
    return None


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


def checked_account(netlist, top, identifier, mapped):
    counts = account(netlist, top)
    if not counts["cells"]:
        raise AssertionError("empty synthesis hierarchy")
    if identifier in ("default-hierarchy", "compact-mapped", "compact-hierarchy"):
        lane_count = sum(count for name, count in counts["hierarchy"].items()
                         if "anvil_q1_ht3_mac_lane" in name)
        if lane_count != 256:
            raise AssertionError(f"physical MAC lanes={lane_count}, expected 256")
        for module in ("tensor_array", "epilogue_fusion", "flash_attn",
                       "panel_prefetch", "transport"):
            if not any(f"anvil_q1_ht3_{module}" in name for name in counts["hierarchy"]):
                raise AssertionError(f"missing substantive {module} hierarchy")
        counts["physical_mac_lanes"] = lane_count
    sequential = sum(count for kind, count in counts["cells"].items()
                     if any(term in kind.lower() for term in ("dff", "mem")))
    if sequential == 0:
        raise AssertionError("synthesis removed all compute/ownership storage")
    if mapped:
        if not any(kind.startswith("$_") for kind in counts["cells"]):
            raise AssertionError("mapped synthesis contains no generic gate cells")
        unresolved = {kind: count for kind, count in counts["cells"].items()
                      if kind.startswith("$") and not kind.startswith("$_")
                      and not kind.startswith("$mem") and kind not in netlist["modules"]}
        if unresolved:
            raise AssertionError(f"unmapped nonmemory logic: {unresolved}")
    counts["sequential_cells"] = sequential
    counts["initialized_wires"] = {
        module: [name for name, net in netlist["modules"][module]["netnames"].items()
                 if "init" in net.get("attributes", {})]
        for module in counts["hierarchy"]
        if any("init" in net.get("attributes", {})
               for net in netlist["modules"][module]["netnames"].values())
    }
    return counts


def mapped_phases(output, identifier, top, parameters, sources, frontend, version):
    cache = ROOT / "evidence/compiled"
    cache.mkdir(parents=True, exist_ok=True)
    parameter_cmd = ("chparam " + " ".join(f"-set {p} {v}" for p, v in parameters.items())
                     + f" {top}; " if parameters else "")
    phases = [
        ("word", f"read_verilog -sv {sources}; {parameter_cmd}"
         f"hierarchy -check -top {top}; proc; opt_expr; opt_clean; check -assert; "
         "memory -nomap; opt_clean; opt -fast; wreduce; alumacc; opt_clean; "),
        ("gates", "techmap; opt_expr; opt_merge; opt_clean; "),
        ("abc", "abc -fast; opt_clean; "),
    ]
    predecessor = None
    predecessor_digest = None
    records = []
    for phase, commands in phases:
        commands += ("check -assert; select -assert-none "
                     "t:$dlatch t:$adlatch t:$_DLATCH_* t:$div t:$mod t:$divfloor t:$modfloor; ")
        semantic = commands
        for entry in frontend["transformations"]:
            semantic = semantic.replace(entry["output"], f"<source>/{Path(entry['output']).name}")
        identity = dict(schema=1, job=identifier, top=top, parameters=parameters,
                        phase=phase, commands=semantic, predecessor_sha256=predecessor_digest,
                        source_sha256=frontend["source_sha256"], tool_version=version,
                        frontend_sha256=hashes()["tests/yosys_frontend.py"])
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
        retained = None
        for candidate in sorted(cache.glob(f"synthesis-{phase}-{key}-*")):
            binding = candidate / "binding.json"
            if not binding.is_file():
                continue
            record = json.loads(binding.read_text())
            phase_receipt = candidate / "synthesis.receipt.json"
            if record.get("identity") != identity or not phase_receipt.is_file():
                continue
            receipt = json.loads(phase_receipt.read_text())
            if (receipt.get("exit") != 0 or receipt.get("timed_out")
                    or receipt.get("tool_version", "").strip() != version):
                continue
            if not all((ROOT / path).is_file() and digest(ROOT / path) == sha
                       for path, sha in record["artifact_sha256"].items()):
                continue
            if any(receipt.get("artifact_sha256", {}).get(receipt[k]) !=
                   digest(ROOT / receipt[k]) for k in ("stdout", "stderr")):
                continue
            counts = checked_account(json.loads((candidate / "netlist.json").read_text()),
                                     top, identifier, phase == "abc")
            retained = (candidate, counts)
            break
        if retained is None:
            directory = cache / f"synthesis-{phase}-{key}-{uuid.uuid4().hex[:12]}"
            directory.mkdir()
            read_checkpoint = f"read_rtlil {relative(predecessor)}; " if predecessor else ""
            script = (read_checkpoint + commands
                      + f"tee -o {relative(directory / 'statistics.json')} stat -json; "
                      + f"write_json {relative(directory / 'netlist.json')}; "
                      + f"write_rtlil {relative(directory / 'checkpoint.il')}")
            (directory / "synthesis.ys").write_text(script + "\n")
            execute(["yosys", "-Q", "-T", "-s", relative(directory / "synthesis.ys")],
                    directory, "synthesis", ["yosys", "-V"])
            counts = checked_account(json.loads((directory / "netlist.json").read_text()),
                                     top, identifier, phase == "abc")
            artifacts = [directory / name for name in
                         ("synthesis.ys", "statistics.json", "netlist.json", "checkpoint.il")]
            if not all(path.is_file() for path in artifacts):
                raise AssertionError(f"incomplete synthesis phase {phase}")
            with (directory / "binding.json").open("x") as out:
                json.dump(dict(identity=identity, status="passed",
                               artifact_sha256={relative(path): digest(path) for path in artifacts},
                               receipt=relative(directory / "synthesis.receipt.json")), out, indent=2)
            reused = False
        else:
            directory, counts = retained
            reused = True
        predecessor = directory / "checkpoint.il"
        predecessor_digest = digest(predecessor)
        records.append(dict(phase=phase, status="passed", reused=reused,
                            binding=relative(directory / "binding.json"),
                            receipt=relative(directory / "synthesis.receipt.json")))
        with (output / f"{phase}-progress.json").open("x") as out:
            json.dump(records, out, indent=2)
        if phase == "word" and identifier == "compact-mapped":
            netlist = json.loads((directory / "netlist.json").read_text())
            ordered = sorted(netlist["modules"],
                             key=lambda name: (-len(netlist["modules"][name]["cells"]), name))
            groups, group, size = [], [], 0
            for name in ordered:
                cells = len(netlist["modules"][name]["cells"])
                if group and size + cells > 2500:
                    groups.append(group)
                    group, size = [], 0
                group.append(name)
                size += cells
            if group:
                groups.append(group)
            group_phases = []
            for index, group in enumerate(groups):
                selection = " ".join(group)
                group_phases.append((
                    f"gates-{index:02d}",
                    f"select -set mapping_group {selection}; techmap @mapping_group; "
                    "opt_expr @mapping_group; opt_merge @mapping_group; "
                    "opt_clean @mapping_group; select -clear; "))
            phases[1:2] = group_phases
    return dict(id=identifier, status="passed", parameters=parameters,
                mapped=True, phases=records, accounting=counts,
                receipt=records[-1]["receipt"], netlist=relative(directory / "netlist.json"),
                statistics=relative(directory / "statistics.json"))


def run(output, diagnostic=False, compact_only=False, job=None):
    sources = " ".join(materialize(output))
    frontend = json.loads((output / "frontend.json").read_text())
    version = execute(["yosys", "-V"], output, "version", ["yosys", "-V"]).strip()
    jobs = list(JOBS)
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
                  + ("opt_expr; opt_merge; wreduce; alumacc; opt_clean; "
                     "techmap; opt_expr; opt_merge; opt_clean; abc; opt_clean; check -noinit; "
                     "select -assert-none t:$_DLATCH_* t:$div t:$mod; " if mapped else "")
                  + f"tee -o {relative(stat_path)} stat -json; write_json {relative(netlist_path)}")
        script_path = directory / "synthesis.ys"
        script_path.write_text(script+"\n")
        cached = retained_job(identifier, top, parameters, mapped,
                              semantic_script(script, frontend, directory), frontend, version)
        if cached is not None:
            rows.append(cached)
            continue
        deadline = os.environ.get("HT3_CHECK_DEADLINE")
        os.environ["HT3_CHECK_DEADLINE"] = str(time.time() + min(
            remaining(), JOB_BUDGETS[identifier]))
        try:
            if mapped:
                rows.append(mapped_phases(directory, identifier, top, parameters,
                                          sources, frontend, version))
                continue
            execute(["yosys", "-Q", "-T", "-s", relative(script_path)], directory,
                    "synthesis", ["yosys", "-V"])
            if not netlist_path.is_file() or not stat_path.is_file():
                raise AssertionError("Yosys zero exit without complete netlist/statistics")
            netlist = json.loads(netlist_path.read_text())
            counts = checked_account(netlist, top, identifier, mapped)
            row = dict(id=identifier, status="passed", parameters=parameters,
                       mapped=mapped, accounting=counts)
        except (RuntimeError, AssertionError, ValueError) as exc:
            row = dict(id=identifier, status="failed", parameters=parameters,
                       mapped=mapped, error=str(exc))
        finally:
            if deadline is None:
                os.environ.pop("HT3_CHECK_DEADLINE", None)
            else:
                os.environ["HT3_CHECK_DEADLINE"] = deadline
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
    mode.add_argument("--job", choices=tuple(row[0] for row in JOBS))
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
