"""Real positive and negative elaboration/startup, independently legal geometries."""

from dataclasses import asdict
import json
import re
import shutil
import time

from execution import ROOT, VERILATOR_UNROLL, write_json
from parameters import positive_cases, negative_cases, legal, leaf_cases, leaf_legal, baseline_geometries


def sv_literal(value):
    if -(1 << 31) <= value < 1 << 31:
        return str(value)
    return ("-" if value < 0 else "") + f"128'sd{abs(value)}"


def sequential_lint():
    errors = []
    for source in sorted((ROOT / "rtl").glob("*.sv")):
        text = re.sub(r"//[^\n]*|/\*.*?\*/|\"(?:\\.|[^\"\\])*\"", "", source.read_text(), flags=re.S)
        for match in re.finditer(r"\balways\s*@\s*\(([^)]*)\)\s*begin", text):
            sensitivity = match.group(1)
            if "posedge" not in sensitivity and "negedge" not in sensitivity:
                continue
            if not re.fullmatch(r"\s*posedge\s+clk(?:\s+or\s+negedge\s+rst_n)?\s*", sensitivity):
                errors.append(f"{source.name}: noncontractual sequential sensitivity")
            depth, end = 1, match.end()
            for token in re.finditer(r"\bbegin\b|\bend\b", text[match.end():]):
                depth += 1 if token.group() == "begin" else -1
                if depth == 0:
                    end = match.end() + token.start()
                    break
            block = text[match.end():end]
            # Procedural for-loop induction is not a state assignment.
            block = re.sub(r"\bfor\s*\([^)]*\)", "", block)
            if re.search(r"(?<![<>=!])=(?!=)", block):
                errors.append(f"{source.name}: blocking state assignment in sequential block")
    if errors:
        raise AssertionError("\n".join(errors))
    return {"sequential_assignment_violations": 0}


def timing_lint(run):
    if shutil.which("vulcan") is None:
        # The fallback is the same forbidden runtime-cell assertion, not a waiver.
        from synthesis_checks import synthesis_case
        from parameters import A
        return synthesis_case(run, A, "timing-lint-fallback")
    output = run.path / "rtl-timing-lint.json"
    _, receipt = run.tool(["vulcan", "hardware", "fpga", "rtl-timing-lint",
                          "--project", ".", "--rtl-glob", "rtl/*.sv",
                          "--max-comb-div-width", "0", "--output", run.rel(output)])
    report = json.loads(output.read_text())
    required_sources = {k: v for k, v in run.hashes.items() if k.startswith("rtl/")}
    if (report.get("gate") != "rtl-timing-lint" or report.get("status") != "passed" or
            report.get("source_sha256") != required_sources):
        raise AssertionError("native timing lint lacks current-source passing result")
    for key in ("rtl_div_mod_hazards", "netlist_div_mod_hazards",
                "mixed_assign_hazards", "lut_clock_gate_hazards"):
        if report.get(key) != []:
            raise AssertionError("native timing lint hazard or missing report field " + key)
    return {"native_report": report, "stdout": receipt["stdout"],
            "scope": "forbidden-structure lint; does not establish physical timing"}


def startup_matrix(run, cases, sources, simulators, output):
    """Two independent cold compilers at most; every case still executes separately."""
    completed = {}
    progress = time.monotonic()

    def execute(number, case):
        nonlocal progress
        folder = run.path / case["folder"]
        folder.mkdir()
        tb = folder / "startup.sv"
        tb.write_text("`timescale 1ns/1ps\nmodule parameter_startup;\n" +
                      case["instance"] +
                      '\ninitial begin #10; $display("STARTUP_COMPLETE"); $finish; end\nendmodule\n')
        results = []
        expected = case["expected"]
        for simulator in simulators:
            if simulator == "iverilog":
                binary = folder / "startup.vvp"
                run.tool(["iverilog", "-g2012", "-Wall", "-s", "parameter_startup",
                          "-o", run.rel(binary), *sources, run.rel(tb)],
                         build_class="icarus-startup")
                command = ["vvp", run.rel(binary)]
            else:
                obj = folder / "obj"
                run.tool(["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                          *VERILATOR_UNROLL, "--top-module", "parameter_startup",
                          "--Mdir", run.rel(obj), "-o", "startup", *sources, run.rel(tb)],
                         build_class="verilator-startup")
                binary = obj / "startup"
                command = [run.rel(binary)]
            text, receipt = run.tool(command, expected=(0,) if expected else tuple(range(-128, 129)))
            if expected:
                if "PARAMETER ERROR" in text or text.count("STARTUP_COMPLETE") != 1:
                    raise AssertionError("legal startup incomplete: " + case["folder"])
            elif receipt["exit_code"] == 0 or "PARAMETER ERROR" not in text:
                raise AssertionError("illegal startup did not explicitly reject: " + case["folder"])
            result = {**case["metadata"], "simulator": simulator, "stdout": receipt["stdout"]}
            if "independent_q1" not in result:
                result["observed_exit"] = receipt["exit_code"]
            results.append(result)
            with run.lock:
                completed[number] = list(results)
                write_json(run.path / output, [
                    row for index in sorted(completed) for row in completed[index]])
                if time.monotonic() - progress >= 30:
                    print(f"startup {output}: {sum(map(len, completed.values()))}/"
                          f"{len(cases)*len(simulators)}", flush=True)
                    progress = time.monotonic()
            run.compact_startup(binary)
        return results

    rows = run.parallel([lambda number=number, case=case: execute(number, case)
                         for number, case in enumerate(cases)], max_workers=2)
    return [row for result in rows for row in result]


def structure(run, *, simulators=("iverilog", "verilator"), include_negative=True,
              include_timing_lint=True, selected_cases=None):
    from preparation_checks import preparation_dispatch_sensitivity
    from harness_checks import (board_prerequisite_sensitivity, decoder_trace_sensitivity,
                                hardware_metrics, inflight_tool_receipt,
                                physical_inventory_sensitivity, fitted_summary_sensitivity)
    from public_asset_checks import public_asset_checks
    from compiler_admission_checks import admission_sensitivity, clean_worker_sensitivity
    from startup_retention_checks import retention_sensitivity
    from startup_scalability_checks import startup_scalability_sensitivity

    cases = [(label, g, True) for label, g in positive_cases()]
    if include_negative:
        cases += [(label, g, False) for label, g in negative_cases()]
    if selected_cases is not None:
        cases = selected_cases
    leaf_count = sum(include_negative or expected for _, _, expected in leaf_cases())
    run.plan_startup_storage(
        (len(cases) + leaf_count + len(list(baseline_geometries()))) * len(simulators))
    lint = {"assignments": sequential_lint(), "hardware_metric_checker": hardware_metrics(),
            "compiler_admission_checker": admission_sensitivity(run.path),
            "compiler_clean_worker_checker": clean_worker_sensitivity(run.path),
            "startup_retention_checker": retention_sensitivity(run),
            "startup_scalability_checker": startup_scalability_sensitivity(run.path),
            "preparation_dispatch_checker": preparation_dispatch_sensitivity(),
            "public_asset_checker": public_asset_checks(run),
            "board_prerequisite_checker": board_prerequisite_sensitivity(run),
            "physical_inventory_checker": physical_inventory_sensitivity(run),
            "fitted_summary_checker": fitted_summary_sensitivity(run),
            "decoder_trace_checker": decoder_trace_sensitivity(run),
            "inflight_tool_receipt": inflight_tool_receipt(run)}
    if include_timing_lint:
        lint["timing"] = timing_lint(run)
    write_json(run.path / "parameter-manifest.json",
               [{"label": label, "parameters": asdict(g), "legal": expected}
                for label, g, expected in cases])
    rtl = [str(p.relative_to(ROOT)) for p in sorted((ROOT / "rtl").glob("*.sv"))]
    startup_cases = []
    for number, (label, g, expected) in enumerate(cases):
        if legal(g) != expected:
            raise AssertionError(f"verification geometry error: {label} {asdict(g)}")
        connections = ".clk(1'b0),.rst_n(1'b0),.cancel(1'b0),.token_valid(1'b0)"
        overrides = {"PROFILE": g.PROFILE} if label == "official-default" else asdict(g)
        parameters = ",".join(f".{k}({sv_literal(v)})" for k, v in overrides.items())
        startup_cases.append({
            "folder": f"geometry-{number:04d}", "expected": expected,
            "instance": f"anvil_q3_top #({parameters}) accelerator ({connections});",
            "metadata": {"label": label, "parameters": asdict(g), "overrides": overrides,
                         "expected_legal": expected}})
    results = startup_matrix(run, startup_cases, rtl, simulators, "parameter-results.json")
    leaves = leaf_structure(run, simulators=simulators, include_negative=include_negative)
    parents = parent_structure(run, simulators=simulators)
    return {"parameters": results, "leaf_parameters": leaves, "supplied_parameters": parents, "lint": lint,
            "scope": "elaboration/diagnostics only; no functional or timing certification"}


def parent_structure(run, *, simulators=("iverilog", "verilator")):
    cases = list(baseline_geometries())
    if not hasattr(run, "startup_storage"):
        run.plan_startup_storage(len(cases) * len(simulators))
    write_json(run.path / "supplied-parameter-manifest.json",
               [{"implementation": implementation, "parameters": asdict(g)}
                for implementation, g in cases])
    sources = [str(p.relative_to(ROOT)) for p in sorted(
        (ROOT / "anvil_q2_reference/rtl").glob("*.sv"))]
    startup_cases = []
    for number, (implementation, g) in enumerate(cases):
        if not legal(g):
            raise AssertionError("illegal supplied-baseline geometry")
        parameters = {key: value for key, value in asdict(g).items()
                      if key not in ("PROFILE", "INT4_ASYM", "TILE_K", "TILE_ROWS")}
        parameters["COMPAT_Q1"] = int(implementation == "q1-wrapper")
        overrides = ",".join(f".{key}({sv_literal(value)})" for key, value in parameters.items())
        startup_cases.append({
            "folder": f"supplied-geometry-{number:04d}", "expected": True,
            "instance": f"anvil_q2_top #({overrides}) accelerator "
                        "(.clk(1'b0),.rst_n(1'b0),.cancel(1'b0),.token_valid(1'b0));",
            "metadata": {"implementation": implementation, "parameters": parameters,
                         "independent_q1": False}})
    return startup_matrix(run, startup_cases, sources, simulators, "supplied-parameter-results.json")


def leaf_structure(run, *, simulators=("iverilog", "verilator"), include_negative=True):
    cases = [(module, parameters, expected) for module, parameters, expected in leaf_cases()
             if include_negative or expected]
    if not hasattr(run, "startup_storage"):
        run.plan_startup_storage(len(cases) * len(simulators))
    write_json(run.path / "leaf-parameter-manifest.json",
               [{"module": module, "parameters": p, "legal": expected}
                for module, p, expected in cases])
    sources = [str(p.relative_to(ROOT)) for p in sorted((ROOT / "rtl").glob("*.sv"))]
    startup_cases = []
    for number, (module, parameters, expected) in enumerate(cases):
        if leaf_legal(module, parameters) != expected:
            raise AssertionError("leaf legality manifest disagreement")
        overrides = ",".join(f".{key}({sv_literal(value)})" for key, value in parameters.items())
        startup_cases.append({
            "folder": f"leaf-geometry-{number:04d}", "expected": expected,
            "instance": f"{module} #({overrides}) accelerator "
                        "(.clk(1'b0),.rst_n(1'b0),.flush(1'b0));",
            "metadata": {"module": module, "parameters": parameters, "expected_legal": expected}})
    return startup_matrix(run, startup_cases, sources, simulators, "leaf-parameter-results.json")
