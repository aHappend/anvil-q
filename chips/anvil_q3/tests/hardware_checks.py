"""Real fitted-tool entry points, gated on positive public board identification.

Manifest shape checks reject nonpositive/noninteger DDR quantities before
STA/HIL entry. Schema validity alone never proves physical identity or access.
STA requires one nonempty fitted image; existence alone is not a usable image.
Forbidden Quartus diagnostics are rejected in both tool streams and reports,
including the fitted summary rather than only detailed .rpt files,
even if the tool exits zero and the fitted summary claims success.
Error/fatal records are rejected regardless of diagnostic number; ordinary
informational error counts and unrelated warnings are not error records.
This check does not establish programming success or physical HIL.
Cable enumeration also rejects error/fatal records from either tool stream;
a cable listing cannot override a reported enumeration failure.
Runtime metadata is not a public source or a substitute for these executions.
"""

import json
import math
from pathlib import Path
import re

from execution import ROOT, sha256, write_json

DEVICE = "10AX115N2F45E1SG"


def quartus_error(text):
    return re.search(r"(?mi)^[ \t]*(?:(?:Critical|Fatal)[ \t]+)?"
                     r"(?:Error|Fatal)(?:[ \t]*\([0-9]+\))?[ \t]*:"
                     r"|^[ \t]*Fatal\b", text) is not None


class PhysicalPrerequisiteError(RuntimeError):
    """Missing board inputs, distinct from tool or manifest decoding failures."""

    def __init__(self, unmet):
        self.unmet = tuple(unmet)
        super().__init__("unmet physical prerequisites: " + "; ".join(unmet))


def jtag_inventory(stdout, stderr):
    """Parse cable enumeration only; a cable is not positive board identification."""
    text = stdout + "\n" + stderr
    if re.search(r"No JTAG hardware available", text, re.I):
        raise PhysicalPrerequisiteError(["Quartus reports no JTAG hardware available"])
    if quartus_error(text):
        raise PhysicalPrerequisiteError(["Quartus JTAG enumeration reports an error"])
    cables = []
    for line in text.splitlines():
        match = re.fullmatch(r"\s*(\d+)\)\s+(\S.*\S|\S)\s*", line)
        if match:
            number = int(match.group(1))
            if number < 1 or any(row["index"] == number for row in cables):
                raise PhysicalPrerequisiteError(["invalid/duplicate Quartus JTAG cable index"])
            cables.append({"index": number, "description": match.group(2)})
    if not cables:
        raise PhysicalPrerequisiteError(["no enumerated Quartus JTAG cable records"])
    return {"cables": cables, "scope": "cable enumeration only; "
            "board/device identity, physical access, PCIe/DDR and HIL remain unproven"}


def physical_cable_inventory(run):
    stdout, record = run.tool(["quartus_pgm", "--list"])
    result = {"cable_inventory_stdout": record["stdout"],
              "cable_inventory_stderr": record["stderr"],
              "programming_attempted": False,
              "scope": "read-only cable listing; board identity, licenses, fit, "
                       "PCIe/DDR traffic and HIL unproven"}
    try:
        result["inventory"] = jtag_inventory(
            stdout, (ROOT / record["stderr"]).read_text())
    except PhysicalPrerequisiteError as exc:
        write_json(run.path / "physical-toolchain.json",
                   {**result, "cable_enumeration_met": False, "unmet": exc.unmet})
        raise
    result["cable_enumeration_met"] = True
    write_json(run.path / "physical-toolchain.json", result)
    return result


def board_inputs(run):
    path = ROOT / "fpga/board_manifest.json"
    missing = []
    bindings = {}
    manifest = {}
    if not path.is_file():
        missing.append("fpga/board_manifest.json: positively identified physical board, not example")
    else:
        manifest = json.loads(path.read_text())
        bindings[str(path.relative_to(ROOT))] = sha256(path)
        if (type(manifest.get("schema")) is not int or manifest.get("schema") != 1 or
                manifest.get("device") != DEVICE):
            missing.append("schema 1 and exact Arria 10 GX target " + DEVICE)
        for section, fields in (
                ("board", ("manufacturer", "model", "revision", "documentation_url")),
                ("ddr4", ("part", "documentation_url")),
                ("pcie", ("ip_name", "ip_version", "license_description"))):
            values = manifest.get(section)
            if not isinstance(values, dict):
                missing.append(section + ": object required")
                values = {}
            for field in fields:
                value = values.get(field)
                if not isinstance(value, str) or not value.strip():
                    missing.append(section + "." + field)
        ddr4 = manifest.get("ddr4")
        if isinstance(ddr4, dict):
            for field in ("capacity_bytes", "channels", "data_width_bits"):
                value = ddr4.get(field)
                if type(value) is not int or value <= 0:
                    missing.append("ddr4." + field + ": positive integer required")
        pcie = manifest.get("pcie")
        if (not isinstance(pcie, dict) or
                type(pcie.get("generation")) is not int or pcie.get("generation") != 3 or
                type(pcie.get("lanes")) is not int or pcie.get("lanes") != 8):
            missing.append("identified physical PCIe Gen3 x8 integration")
        if manifest.get("timing_exceptions") != []:
            missing.append("no timing exceptions admitted")
        assets = [manifest.get(k) for k in ("top_source", "pin_qsf", "board_sdc")]
        for field in ("qip_files", "support_sources"):
            items = manifest.get(field)
            if not isinstance(items, list) or (field == "qip_files" and not items):
                missing.append(field)
            else:
                assets.extend(items)
        for value in assets:
            if not isinstance(value, str) or not value:
                missing.append("unidentified board source/IP/constraints")
                continue
            asset = Path(value)
            if asset.is_absolute() or ".." in asset.parts or any(p.startswith(".") for p in asset.parts):
                missing.append("nonportable board input " + value)
                continue
            target = ROOT / asset
            if not target.is_file() or not target.resolve().is_relative_to(ROOT / "fpga"):
                missing.append("missing public FPGA input " + value)
                continue
            bindings[value] = sha256(target)
    write_json(run.path / "physical-prerequisites.json",
               {"unmet": missing, "source_hashes": bindings,
                "physical_access_and_licenses": "not established by a manifest"})
    if missing:
        raise PhysicalPrerequisiteError(missing)
    return manifest


def measured_metric(value, key):
    """Require one finite machine-report value; never default missing metrics."""
    matches = []

    def visit(node):
        if isinstance(node, dict):
            if key in node:
                matches.append(node[key])
            for item in node.values():
                visit(item)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(value)
    if len(matches) != 1 or type(matches[0]) not in (int, float):
        raise AssertionError("missing/ambiguous/non-numeric measured timing metric " + key)
    if type(matches[0]) is float and not math.isfinite(matches[0]):
        raise AssertionError("non-finite measured timing metric " + key)
    return matches[0]


def quartus_sta(run):
    run.versions([("quartus_sh", "--version"), ("quartus_sta", "--version")])
    board_inputs(run)
    results = []
    for banks in (1, 2, 4, 8):
        for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
            folder = run.path / f"fit-b{banks}-m{mode}-a{asym}"
            folder.mkdir()
            _, compile_record = run.tool([
                "quartus_sh", "-t", "fpga/build.tcl",
                "--banks", str(banks), "--cache-mode", str(mode), "--int4-asym", str(asym),
                "--output", run.rel(folder)], timeout=14400)
            projects = list(folder.glob("build-*/*.qpf"))
            if len(projects) != 1:
                raise AssertionError("missing/ambiguous actual fitted project")
            project = projects[0].parent
            output = folder / "timequest.json"
            _, timing_record = run.tool([
                "vulcan", "hardware", "fpga", "quartus-sta",
                "--project-dir", run.rel(project), "--revision", "anvil_q3",
                "--min-setup-slack-ns", "0", "--min-hold-slack-ns", "0",
                "--timeout-s", "14400", "--output", run.rel(output)], timeout=14400)
            timing = json.loads(output.read_text())
            setup = measured_metric(timing, "wns_setup_ns")
            hold = measured_metric(timing, "wns_hold_ns")
            unconstrained = measured_metric(timing, "unconstrained_functional_endpoints")
            exceptions = measured_metric(timing, "unapproved_timing_exceptions")
            if setup < 0 or hold < 0 or unconstrained != 0 or exceptions != 0:
                raise AssertionError("Quartus timing/constraints did not meet admitted acceptance")
            summaries = list(project.rglob("*.fit.summary"))
            if len(summaries) != 1:
                raise AssertionError("missing fitted-device summary")
            summary = summaries[0].read_text()
            statuses = re.findall(r"(?m)^[ \t]*Fitter Status[ \t]*:[ \t]*([^\r\n]*)", summary)
            if (len(statuses) != 1 or re.fullmatch(
                    r"Successful(?:[ \t]+-[ \t]+\S[^\r\n]*)?", statuses[0].strip()) is None):
                raise AssertionError("missing/ambiguous/unsuccessful fitter status: " +
                                     run.rel(summaries[0]))
            devices = re.findall(
                r"(?m)^[ \t]*Device[ \t]*:[ \t]*([^\r\n]*)", summary)
            if len(devices) != 1 or devices[0].strip() != DEVICE:
                raise AssertionError("missing/ambiguous fitted part or part differs from "
                                     "exact admitted device")
            reports = list(project.rglob("*.rpt"))
            if not reports:
                raise AssertionError("no actual compilation reports")
            diagnostics = summaries + reports + [
                ROOT / record[channel]
                for record in (compile_record, timing_record)
                for channel in ("stdout", "stderr")
            ]
            for report in diagnostics:
                text = report.read_text(errors="replace")
                if (re.search(r"(?:Error \(272006\)|Warning \(10268\)|Warning \(10240\))", text) or
                        quartus_error(text)):
                    raise AssertionError("forbidden Quartus error/warning: " + run.rel(report))
            bitstreams = list(project.rglob("*.sof"))
            if (len(bitstreams) != 1 or not bitstreams[0].is_file() or
                    bitstreams[0].stat().st_size == 0):
                raise AssertionError("fitted/programming image absent, ambiguous or empty")
            results.append({"banks": banks, "cache_mode": mode, "int4_asymmetric": asym,
                            "device": DEVICE, "wns_setup_ns": setup, "wns_hold_ns": hold,
                            "unconstrained_functional_endpoints": unconstrained,
                            "unapproved_timing_exceptions": exceptions,
                            "fitter_status": statuses[0].strip(),
                            "fit_summary": run.rel(summaries[0]),
                            "diagnostic_logs": {
                                "compile": {key: compile_record[key]
                                            for key in ("stdout", "stderr")},
                                "timing": {key: timing_record[key]
                                           for key in ("stdout", "stderr")},
                            },
                            "bitstream_sha256": sha256(bitstreams[0]),
                            "timing_receipt": run.rel(output),
                            "scope": "full-default architecture; physical HIL remains separate"})
            write_json(run.path / "quartus-results.json", results)
    return results


def board_hil(run):
    board_inputs(run)
    unmet = [
        "physical execution driver for fitted-image programming, PCIe/DDR4 traffic "
        "and independent output comparison is not implemented",
        "three consecutive physical runs with source/bitstream hashes, board identity "
        "and measured Gen3 x8 link status have not been executed",
    ]
    write_json(run.path / "hil-unmet-prerequisites.json",
               {"unmet": unmet, "hardware_executed": False})
    raise PhysicalPrerequisiteError(unmet)
