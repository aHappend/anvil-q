"""Actual shipped-source Yosys checks with bounded, resumable mapped jobs.

Only a phase with zero tool exit, valid structural observations and hash-checked
complete RTLIL/JSON artifacts can be resumed. Intermediate gate phases retain
unmapped modules; only the final ABC phase can satisfy the mapped obligation.
Connectivity, latch/div/mod and 256-lane assertions remain active. FPGA power-up
initialization is recorded, not mistaken for a latch or an undriven wire.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import os
import re
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, execute, hashes, relative, remaining, timestamp
from yosys_frontend import materialize
from retention import artifacts_intact, digest, execution_logs_intact


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
JOB_BUDGETS = {"default-hierarchy": 360, "compact-mapped": 1800,
               "compact-hierarchy": 180,
               "fp32_add": 60, "fp32_mul": 60, "fp32_divsqrt": 90,
               "fp32_exp": 150, "fp32_sincos": 120,
               "epilogue_fusion": 90, "flash_attn": 90}


def semantic_sources(script, frontend):
    for entry in frontend["transformations"]:
        name = Path(entry["output"]).name
        canonical = f"<source>/{name}"
        script = re.sub(r"evidence/[^\s:;]*/frontend-sources/" + re.escape(name) + r"(?=[:\s;]|$)",
                        lambda match: canonical, script)
        script = script.replace(entry["output"], canonical)
    return script


def semantic_script(script, frontend, directory):
    script = semantic_sources(script, frontend)
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
            if not execution_logs_intact(receipt):
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


def mapping_groups(netlist):
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
    phases = []
    for index, group in enumerate(groups):
        if len(group) == 1 and "anvil_q1_ht3_decoder" in group[0]:
            module = group[0]
            cells = netlist["modules"][module]["cells"]
            chunks, chunk, cost = [], [], 0
            for name in sorted(cells, key=lambda n: (cells[n]["type"], n)):
                cell = cells[name]
                if not cell["type"].startswith("$") or cell["type"].startswith("$mem"):
                    continue
                width = max((len(v) for v in cell["connections"].values()), default=1)
                # Isolate the 8192-bit indexed panel selections. Do not remap an
                # entire decoder and then spend its remaining allocation folding it.
                estimate = width if cell["type"] not in ("$shiftx", "$shift") else width*4
                if chunk and (cost+estimate > 16384 or len(chunk) >= 512):
                    chunks.append(chunk)
                    chunk, cost = [], 0
                chunk.append(name)
                cost += estimate
                if width >= 4096:
                    chunks.append(chunk)
                    chunk, cost = [], 0
            if chunk:
                chunks.append(chunk)
            for part, chunk in enumerate(chunks):
                selection = " ".join(f"{module}/c:{name}" for name in chunk)
                # Preserve the admitted predecessor chain through map-14.
                # Wide shift expansion creates private aliases and constant
                # mux arms; fold these before serializing subsequent phases.
                # Pending word cells keep their names for later selections.
                compact = (
                    f"opt_expr {module}/t:$_*; opt_clean {module}; "
                    f"setattr -unset src {module}/t:$_* {module}/w:$*; "
                    f"rename -enumerate "
                    + (f"-pattern _ht3map{part}_%_ " if part > 15 else "")
                    + f"{module}/t:$_* {module}/w:$*; "
                    if part >= 15 else "")
                phases.append((f"gates-{index:02d}-map-{part:02d}",
                               f"select -set decoder_cells {selection}; "
                               "select -assert-any @decoder_cells; techmap @decoder_cells; "
                               "select -clear; " + compact))
            phases.append((f"gates-{index:02d}-clean",
                           f"opt_clean {module}; select -clear; "))
        else:
            selection = " ".join(group)
            private_objects = " ".join(f"{name}/t:$_* {name}/w:$*" for name in group)
            compact = (f"setattr -unset src {private_objects}; "
                       f"rename -enumerate -pattern _ht3group{index}_%_ {private_objects}; "
                       if index >= 2 else "")
            phases.append((f"gates-{index:02d}",
                           f"select -set mapping_group {selection}; techmap @mapping_group; "
                           "opt_expr @mapping_group; opt_merge @mapping_group; "
                           "opt_clean @mapping_group; select -clear; " + compact))
    return phases


def mapped_phases(output, identifier, top, parameters, sources, frontend, version,
                  through_phase=None):
    cache = ROOT / "evidence/compiled"
    cache.mkdir(parents=True, exist_ok=True)
    parameter_cmd = ("chparam " + " ".join(f"-set {p} {v}" for p, v in parameters.items())
                     + f" {top}; " if parameters else "")
    phases = [
        ("word", f"read_verilog -sv {sources}; {parameter_cmd}"
         f"hierarchy -check -top {top}; proc; opt_expr; opt_clean; check -assert; "
         "memory -nomap; opt_clean; opt -fast; wreduce; alumacc; opt_clean; "),
        ("gates", "techmap; opt_expr; opt_merge; opt_clean; "),
        ("abc", ("techmap; opt_clean -purge; abc -fast; opt_clean -purge; "
                 if identifier == "compact-mapped" else "abc -fast; opt_clean; ")),
    ]
    predecessor = None
    predecessor_digest = None
    records = []
    for phase, commands in phases:
        commands += ("check -assert; select -assert-none "
                     "t:$dlatch t:$adlatch t:$_DLATCH_* t:$div t:$mod t:$divfloor t:$modfloor; ")
        semantic = semantic_sources(commands, frontend)
        identity = dict(schema=1, job=identifier, top=top, parameters=parameters,
                        phase=phase, commands=semantic, predecessor_sha256=predecessor_digest,
                        source_sha256=frontend["source_sha256"], tool_version=version,
                        frontend_sha256=hashes()["tests/yosys_frontend.py"])
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
        retained = None
        for candidate in sorted(cache.glob(f"synthesis-{phase}-*")):
            binding = candidate / "binding.json"
            if not binding.is_file():
                continue
            record = json.loads(binding.read_text())
            bound_identity = dict(record.get("identity", {}))
            if isinstance(bound_identity.get("commands"), str):
                bound_identity["commands"] = semantic_sources(bound_identity["commands"], frontend)
            phase_receipt = candidate / "synthesis.receipt.json"
            if (bound_identity != identity or record.get("status") != "passed"
                    or not phase_receipt.is_file()
                    or record.get("receipt") != relative(phase_receipt)):
                continue
            receipt = json.loads(phase_receipt.read_text())
            if (receipt.get("exit") != 0 or receipt.get("timed_out")
                    or receipt.get("tool_version", "").strip() != version):
                continue
            if any(receipt.get("source_sha256", {}).get(path) != sha
                   for path, sha in hashes().items() if path.startswith("design/")):
                continue
            required = [relative(candidate / name) for name in
                        ("synthesis.ys", "statistics.json", "netlist.json", "checkpoint.il")]
            if not artifacts_intact(record.get("artifact_sha256", {}), required):
                continue
            if not execution_logs_intact(receipt):
                print(f"CACHE_REJECT {relative(candidate)} missing or changed raw logs",
                      flush=True)
                continue
            retained = candidate
            break
        if retained is None:
            if predecessor is not None:
                # The complete bound chain is hash-validated above. Validate
                # its actual last netlist before advancing, not every growing
                # intermediate netlist again on each resumed invocation.
                checked_account(json.loads((predecessor.parent/"netlist.json").read_text()),
                                top, identifier, False)
            directory = cache / f"synthesis-{phase}-{key}-{uuid.uuid4().hex[:12]}"
            directory.mkdir()
            read_checkpoint = f"read_rtlil {relative(predecessor)}; " if predecessor else ""
            script = (read_checkpoint + commands
                      + f"tee -o {relative(directory / 'statistics.json')} stat -json; "
                      + f"write_json {relative(directory / 'netlist.json')}; "
                      + f"write_rtlil {relative(directory / 'checkpoint.il')}")
            (directory / "synthesis.ys").write_text(script + "\n")
            deadline = os.environ.get("HT3_CHECK_DEADLINE")
            allocation = remaining()
            reserve = (90 if identifier == "compact-mapped" else 30) if phase != "abc" else 0
            if through_phase == phase:
                reserve = 0
            minimum = (240 if identifier == "compact-mapped" and
                       (phase == "word" or "select -set decoder_cells " in commands)
                       else 60 if identifier == "compact-mapped"
                       else 30 if phase == "abc" else 0)
            if allocation-reserve-10 < minimum:
                raise RuntimeError(f"unstarted synthesis phase {phase}: {allocation:.3f}s "
                                   f"remain, reserving {reserve}s ABC and 10s settlement; "
                                   "validated predecessors retained")
            os.environ["HT3_CHECK_DEADLINE"] = str(time.time()+max(0, allocation-reserve-10))
            try:
                execute(["yosys", "-Q", "-T", "-s", relative(directory / "synthesis.ys")],
                        directory, "synthesis", ["yosys", "-V"])
            finally:
                if deadline is None:
                    os.environ.pop("HT3_CHECK_DEADLINE", None)
                else:
                    os.environ["HT3_CHECK_DEADLINE"] = deadline
            counts = checked_account(json.loads((directory / "netlist.json").read_text()),
                                     top, identifier, phase == "abc")
            artifacts = [directory / name for name in
                         ("synthesis.ys", "statistics.json", "netlist.json", "checkpoint.il")]
            if not all(path.is_file() for path in artifacts):
                raise AssertionError(f"incomplete synthesis phase {phase}")
            artifact_sha256 = {relative(path): digest(path) for path in artifacts}
            with (directory / "binding.json").open("x") as out:
                json.dump(dict(identity=identity, status="passed",
                               artifact_sha256=artifact_sha256,
                               receipt=relative(directory / "synthesis.receipt.json")), out, indent=2)
            reused = False
        else:
            directory, counts = retained, None
            artifact_sha256 = record["artifact_sha256"]
            reused = True
        predecessor = directory / "checkpoint.il"
        predecessor_digest = artifact_sha256[relative(predecessor)]
        records.append(dict(phase=phase, status="passed", reused=reused,
                            binding=relative(directory / "binding.json"),
                            receipt=relative(directory / "synthesis.receipt.json")))
        with (output / f"{phase}-progress.json").open("x") as out:
            json.dump(records, out, indent=2)
        if phase == "word" and identifier == "compact-mapped":
            netlist = json.loads((directory / "netlist.json").read_text())
            phases[1:2] = mapping_groups(netlist)
            if through_phase and through_phase not in {name for name, _ in phases}:
                raise ValueError(f"unknown synthesis diagnostic phase: {through_phase}")
        if through_phase == phase:
            return dict(id=identifier, status="passed", parameters=parameters,
                        mapped=False, diagnostic_only=True, phases=records,
                        receipt=records[-1]["receipt"],
                        coverage_limits=["partial mapping diagnostic; final ABC not executed"])
    if counts is None:
        counts = checked_account(json.loads((directory/"netlist.json").read_text()),
                                 top, identifier, True)
    return dict(id=identifier, status="passed", parameters=parameters,
                mapped=True, phases=records, accounting=counts,
                receipt=records[-1]["receipt"], netlist=relative(directory / "netlist.json"),
                statistics=relative(directory / "statistics.json"))


def run(output, diagnostic=False, compact_only=False, job=None, through_phase=None):
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
                                          sources, frontend, version, through_phase))
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
                       mapped=mapped, error=str(exc),
                       timed_out=getattr(exc, "timed_out", False))
            if hasattr(exc, "record"):
                row["receipt"] = exc.record["stdout"].replace(".stdout.txt", ".receipt.json")
        finally:
            if deadline is None:
                os.environ.pop("HT3_CHECK_DEADLINE", None)
            else:
                os.environ["HT3_CHECK_DEADLINE"] = deadline
        if (directory / "synthesis.receipt.json").is_file():
            row.setdefault("receipt", relative(directory / "synthesis.receipt.json"))
        row["directory"] = relative(directory)
        rows.append(row)
    result = dict(status="passed" if all(r["status"] == "passed" for r in rows) else "failed",
                  runs=rows, diagnostic=diagnostic, compact_only=compact_only,
                  job=job, frontend=relative(output / "frontend.json"),
                  coverage_limits=(["partial mapping diagnostic; final ABC not executed"]
                                   if through_phase else []))
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
    parser.add_argument("--through-phase",
                        help="diagnostic checkpoint stop, never complete mapped acceptance")
    args = parser.parse_args()
    if args.through_phase and args.job != "compact-mapped":
        parser.error("--through-phase requires --job compact-mapped")
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_synthesis.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    result = run(output, args.diagnostic, args.compact_only, args.job, args.through_phase)
    receipt.update(exit=0 if result["status"] == "passed" else 1,
                   timed_out=remaining() <= 0 or any(
                       row.get("timed_out", False) for row in result["runs"]) or any(
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
