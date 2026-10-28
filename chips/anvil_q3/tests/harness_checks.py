"""Bounded verification-source consistency diagnostic, not DUT acceptance."""

import json

from benchmark_checks import baseline_prerequisites, quality_lock
from execution import ROOT, SELECTORS, sources
from mutation_checks import MUTATIONS
from parameters import legal, negative_cases, positive_cases, leaf_cases, leaf_legal, startup_geometry
from dataclasses import replace
from baseline_discovery import (fork_entries, reference_entries, q4_history_entries,
                                pull_request_entries, commit_search_entries, issue_search_entries,
                                verify_indexed_blob)
from hardware_checks import measured_metric


def native_baseline_sensitivity():
    """Offline adapter fixtures, not acquired provenance or numerical execution."""
    from copy import deepcopy
    from native_baselines import supported_q1

    declared = json.loads((ROOT / "tests/public_assets.json").read_text())["assets"]
    q1 = next(asset for asset in declared
              if asset["category"] == "baseline" and asset["generation"] == "Q1")
    fixture = {
        "category": "baseline", "generation": "Q1", "identifier": q1["identifier"],
        "revision": q1["revision"], "license_identifier": q1["license_identifier"],
        "license_evidence": deepcopy(q1["license_file"]),
        "contents": deepcopy(q1["files"]),
    }
    if not supported_q1(fixture):
        raise AssertionError("pinned native Q1 adapter fixture rejected")
    status = baseline_prerequisites([fixture], {})
    if ([row["generation"] for row in status["generations"]] != ["Q1", "Q2"] or
            [row["source_bound_execution_adapter"] for row in status["generations"]]
            != [True, False, False] or not status["unmet"]):
        raise AssertionError("native Q1 adapter fixture incorrectly qualified another generation")
    variants = []
    for field, value in (
            ("category", "weight_slice"), ("generation", "Q4"),
            ("identifier", "Q1-compatible wrapper"), ("revision", "0" * 40),
            ("license_identifier", "unidentified")):
        candidate = deepcopy(fixture)
        candidate[field] = value
        variants.append((field, candidate))
    for label in ("license-hash", "source-hash", "source-name", "missing-source"):
        candidate = deepcopy(fixture)
        if label == "license-hash":
            candidate["license_evidence"]["sha256"] = "0" * 64
        elif label == "source-hash":
            candidate["contents"][0]["sha256"] = "0" * 64
        elif label == "source-name":
            candidate["contents"][0]["url"] += ".renamed.sv"
        else:
            candidate["contents"].pop()
        variants.append((label, candidate))
    for label, candidate in variants:
        if supported_q1(candidate):
            raise AssertionError("native Q1 adapter accepted mismatched " + label)
        status = baseline_prerequisites([candidate], {})
        if any(row["source_bound_execution_adapter"] for row in status["generations"]):
            raise AssertionError("mismatched native Q1 fixture qualified an adapter: " + label)
    duplicate = deepcopy(fixture)
    duplicate["contents"].append(deepcopy(duplicate["contents"][0]))
    try:
        supported_q1(duplicate)
    except ValueError:
        pass
    else:
        raise AssertionError("native Q1 adapter accepted duplicate source names")
    return {"accepted_adapter_fixtures": 1,
            "mismatched_adapter_fixtures_rejected": [label for label, _ in variants],
            "duplicate_source_names_rejected": True,
            "scope": "offline identity fixtures only; no public asset acquisition, "
                     "baseline numerical execution or Q4 coverage"}


def fitted_summary_sensitivity(run):
    """Exercise the STA driver with offline reports, never actual fitted images."""
    from types import SimpleNamespace
    from unittest.mock import patch
    from execution import write_json
    from hardware_checks import DEVICE, quartus_sta

    folder = run.path / "fitted-summary-fixtures"
    folder.mkdir()
    fixtures = (
        ("successful", "Fitter Status : Successful - offline fixture\n", True),
        ("successful-no-date", "Fitter Status : Successful\n", True),
        ("unsuccessful", "Fitter Status : Unsuccessful - offline fixture\n", False),
        ("missing", "", False),
        ("conflicting", "Fitter Status : Successful\nFitter Status : Unsuccessful\n", False),
        ("duplicate", "Fitter Status : Successful\nFitter Status : Successful\n", False),
        ("unknown", "Fitter Status : Pending\n", False),
        ("suffix", "Fitter Status : Successful but incomplete\n", False),
    )
    device_fixtures = (
        ("device-missing", "", False),
        ("device-wrong", "Device : 10AX115N2F45E2SG\n", False),
        ("device-duplicate", f"Device : {DEVICE}\nDevice : {DEVICE}\n", False),
        ("device-conflicting", f"Device : {DEVICE}\nDevice : 10AX115N2F45E2SG\n", False),
        ("device-exact", f"Device : {DEVICE}\n", True),
    )
    cases = [(name, status, f"Device : {DEVICE}\n", accepted, "fitter status")
             for name, status, accepted in fixtures]
    cases.extend((name, "Fitter Status : Successful\n", device, accepted, "fitted part")
                 for name, device, accepted in device_fixtures)
    cases.extend((
        ("image-missing", "Fitter Status : Successful\n", f"Device : {DEVICE}\n",
         False, "fitted/programming image"),
        ("image-empty", "Fitter Status : Successful\n", f"Device : {DEVICE}\n",
         False, "fitted/programming image"),
        ("image-duplicate", "Fitter Status : Successful\n", f"Device : {DEVICE}\n",
         False, "fitted/programming image"),
    ))
    diagnostic_cases = {
        f"{stage}-{channel}-{code}": (stage, channel, code)
        for stage in ("quartus_sh", "vulcan")
        for channel in ("stdout", "stderr")
        for code in ("Error (272006)", "Warning (10268)", "Warning (10240)",
                     "Error (293001)", "Error", "Critical Error (12345)", "Fatal",
                     "Fatal Error (12345)")
    }
    cases.extend((name, "Fitter Status : Successful\n", f"Device : {DEVICE}\n",
                  False, "forbidden quartus")
                 for name in diagnostic_cases)
    report_diagnostic_cases = {
        f"{report}-{code}": (report, code)
        for report in ("anvil_q3.fit.summary", "anvil_q3.sta.rpt")
        for code in ("Error (272006)", "Warning (10268)", "Warning (10240)",
                     "Error (293001)", "Error", "Critical Error (12345)", "Fatal",
                     "Fatal Error (12345)")
    }
    cases.extend((name, "Fitter Status : Successful\n", f"Device : {DEVICE}\n",
                  False, "forbidden quartus")
                 for name in report_diagnostic_cases)
    timing_cases = {
        "timing-zero-slack": ({"wns_setup_ns": 0, "wns_hold_ns": 0}, True),
        "timing-negative-setup": ({"wns_setup_ns": -0.001}, False),
        "timing-negative-hold": ({"wns_hold_ns": -0.001}, False),
        "timing-unconstrained": ({"unconstrained_functional_endpoints": 1}, False),
        "timing-unapproved-exception": ({"unapproved_timing_exceptions": 1}, False),
    }
    cases.extend((name, "Fitter Status : Successful\n", f"Device : {DEVICE}\n",
                  accepted, "timing/constraints")
                 for name, (_, accepted) in timing_cases.items())
    results = []
    for name, status, device, accepted, diagnosis in cases:
        case = folder / name
        case.mkdir()
        write_json(case / "fixture.json", {
            "scope": "synthetic STA-driver input/output fixture, not engineering evidence",
            "physical_tools_executed": False, "programmable_image": False,
        })

        def tool(argv, **kwargs):
            if argv[0] == "quartus_sh":
                output = ROOT / argv[argv.index("--output") + 1]
                project = output / "build-offline-fixture"
                project.mkdir()
                (project / "anvil_q3.qpf").write_text("OFFLINE CHECKER FIXTURE\n")
                (project / "anvil_q3.fit.summary").write_text(
                    status + device)
                (project / "anvil_q3.fit.rpt").write_text("OFFLINE CHECKER FIXTURE\n")
                if name in report_diagnostic_cases:
                    report, code = report_diagnostic_cases[name]
                    with (project / report).open("a") as stream:
                        stream.write(code + ": deliberately injected checker fixture\n")
                if name != "image-missing":
                    (project / "anvil_q3.sof").write_bytes(
                        b"" if name == "image-empty" else b"NOT A PROGRAMMABLE IMAGE\n")
                if name == "image-duplicate":
                    (project / "duplicate.sof").write_bytes(b"NOT A PROGRAMMABLE IMAGE\n")
            elif argv[0] == "vulcan":
                metrics = {
                    "wns_setup_ns": 0.25, "wns_hold_ns": 0.125,
                    "unconstrained_functional_endpoints": 0,
                    "unapproved_timing_exceptions": 0,
                }
                if name in timing_cases:
                    metrics.update(timing_cases[name][0])
                write_json(ROOT / argv[argv.index("--output") + 1], metrics)
            else:
                raise AssertionError("unexpected offline fixture command")
            output = ROOT / argv[argv.index("--output") + 1]
            logs = output if argv[0] == "quartus_sh" else output.parent
            record = {}
            text = ""
            for channel in ("stdout", "stderr"):
                path = logs / (argv[0] + "-" + channel + ".txt")
                content = "OFFLINE CHECKER FIXTURE: no physical tool execution\n"
                content += ("Info: Error diagnostics follow the standard severity format\n"
                            "Warning (99999): unrelated offline warning fixture\n"
                            "Quartus Prime was successful. 0 errors, 1 warning\n")
                if name in diagnostic_cases:
                    stage, stream, code = diagnostic_cases[name]
                    if (argv[0], channel) == (stage, stream):
                        content += code + ": deliberately injected checker fixture\n"
                path.write_text(content)
                record[channel] = str(path.relative_to(ROOT))
                if channel == "stdout":
                    text = content
            return text, record

        fixture_run = SimpleNamespace(
            path=case, versions=lambda tools: None, tool=tool,
            rel=lambda path: str(path.relative_to(ROOT)))
        with patch("hardware_checks.board_inputs", return_value={}):
            try:
                result = quartus_sta(fixture_run)
            except AssertionError as exc:
                if accepted or diagnosis not in str(exc).lower():
                    raise
                results.append({"fixture": name, "rejected": True, "diagnosis": str(exc)})
            else:
                if not accepted:
                    raise AssertionError("STA driver accepted invalid fitted summary: " + name)
                if len(result) != 16:
                    raise AssertionError("offline STA driver omitted bank/cache architectures")
                if name == "timing-zero-slack" and any(
                        row["wns_setup_ns"] != 0 or row["wns_hold_ns"] != 0
                        for row in result):
                    raise AssertionError("STA driver changed exact zero-slack boundary")
                if any(row["fitter_status"] != status.split(":", 1)[1].strip() or
                       not row["fit_summary"].endswith(".fit.summary") for row in result):
                    raise AssertionError("STA driver lost fitted-status provenance")
                for row in result:
                    for stage in ("compile", "timing"):
                        for channel in ("stdout", "stderr"):
                            path = ROOT / row["diagnostic_logs"][stage][channel]
                            if not path.is_file() or not path.is_relative_to(case):
                                raise AssertionError("STA driver lost diagnostic-log provenance")
                results.append({"fixture": name, "rejected": False, "architectures": len(result)})
    write_json(folder / "results.json", results)
    return {"fixtures": results, "scope": "offline driver sensitivity only; "
            "no Quartus execution, timing closure, fitted bitstream or HIL"}


def physical_inventory_sensitivity(run):
    """Offline cable-list fixtures do not establish connected hardware."""
    from types import SimpleNamespace
    from unittest.mock import Mock
    from hardware_checks import (jtag_inventory, physical_cable_inventory,
                                 PhysicalPrerequisiteError)

    cable = "1) USB-Blaster [USB-0]"
    expected = [{"index": 1, "description": "USB-Blaster [USB-0]"}]
    for stdout, stderr in ((cable, ""), ("", cable)):
        if jtag_inventory(stdout, stderr)["cables"] != expected:
            raise AssertionError("JTAG cable enumeration changed")
    multiple = jtag_inventory(cable + "\n2) USB-BlasterII [USB-1]\n", "")
    if len(multiple["cables"]) != 2:
        raise AssertionError("JTAG enumeration dropped a cable")
    invalid = (
        ("Quartus Prime Programmer was successful. 0 errors, 0 warnings\n",
         "No JTAG hardware available\n"),
        ("No JTAG hardware available\n", ""),
        ("", ""),
        ("Quartus Prime Programmer was successful. 0 errors, 0 warnings\n", ""),
        (cable, "No JTAG hardware available\n"),
        (cable, "Error (213019): Can't scan JTAG chain\n"),
        (cable, "Fatal: enumeration failed\n"),
        (cable, "Fatal enumeration failed\n"),
        (cable + "\n" + cable, ""),
        ("0) USB-Blaster [USB-0]", ""),
    )
    diagnostic_cases = tuple(
        (cable + "\n" + diagnostic + ": injected enumeration failure\n", "")
        if channel == "stdout" else
        (cable, diagnostic + ": injected enumeration failure\n")
        for channel in ("stdout", "stderr")
        for diagnostic in ("Error", "Error (213019)", "Critical Error (213019)",
                           "Fatal", "Fatal Error (213019)")
    )
    invalid += diagnostic_cases
    for index, (stdout, stderr) in enumerate(invalid):
        try:
            jtag_inventory(stdout, stderr)
        except PhysicalPrerequisiteError:
            pass
        else:
            raise AssertionError("JTAG inventory accepted missing/invalid hardware: " + str(index))
    folder = ROOT / run.path / "jtag-inventory-fixtures"
    folder.mkdir()
    driver_cases = (
            ("absent", invalid[0][0], invalid[0][1], False),
            ("present", cable, "", True),
    ) + tuple((f"diagnostic-{index}", stdout, stderr, False)
              for index, (stdout, stderr) in enumerate(diagnostic_cases))
    for name, stdout, stderr, met in driver_cases:
        case = folder / name
        case.mkdir()
        (case / "stdout.txt").write_text(stdout)
        (case / "stderr.txt").write_text(stderr)
        tool = Mock(return_value=(stdout, {
            "stdout": str((case / "stdout.txt").relative_to(ROOT)),
            "stderr": str((case / "stderr.txt").relative_to(ROOT)),
            "exit_code": 0,
        }))
        try:
            result = physical_cable_inventory(SimpleNamespace(path=case, tool=tool))
        except PhysicalPrerequisiteError:
            if met:
                raise
        else:
            if not met or result["cable_enumeration_met"] is not True:
                raise AssertionError("zero-exit absent cable was accepted")
        tool.assert_called_once_with(["quartus_pgm", "--list"])
        report = json.loads((case / "physical-toolchain.json").read_text())
        if report["cable_enumeration_met"] is not met or report["programming_attempted"]:
            raise AssertionError("cable enumeration report misstates physical work")
    return {"valid_fixture_cases": 3, "rejected_inventory_defects": len(invalid),
            "zero_exit_tool_fixtures": len(driver_cases),
            "scope": "offline parser sensitivity only; no physical identification or HIL"}


def board_prerequisite_sensitivity(run):
    """Offline input-checker fixtures; never identify or program a physical board."""
    from types import SimpleNamespace
    from unittest.mock import patch
    from hardware_checks import board_inputs, PhysicalPrerequisiteError
    from execution import write_json
    from prerequisites import prerequisites

    folder = run.path / "board-prerequisite-fixtures"
    folder.mkdir()
    fixture_root = folder / "input-project"
    (fixture_root / "fpga").mkdir(parents=True)
    example = json.loads((ROOT / "fpga/board_manifest.example.json").read_text())
    example.update({
        "status": "OFFLINE CHECKER FIXTURE ONLY: not physical board identification",
        "board": {"manufacturer": "checker fixture", "model": "synthetic input",
                  "revision": "fixture", "documentation_url": "https://example.invalid/board"},
        "ddr4": {"part": "checker fixture", "documentation_url": "https://example.invalid/ddr",
                 "capacity_bytes": 1024, "channels": 1, "data_width_bits": 32},
        "pcie": {"generation": 3, "lanes": 8, "ip_name": "checker fixture",
                 "ip_version": "fixture", "license_description": "not real IP"},
        "top_source": "fpga/fixture.sv", "pin_qsf": "fpga/fixture.qsf",
        "board_sdc": "fpga/fixture.sdc", "qip_files": ["fpga/fixture.qip"],
        "support_sources": [],
    })
    for name in ("fixture.sv", "fixture.qsf", "fixture.sdc", "fixture.qip"):
        (fixture_root / "fpga" / name).write_text("// offline checker fixture only\n")
    control = folder / "valid-schema-control"
    control.mkdir()
    write_json(fixture_root / "fpga/board_manifest.json", example)
    with patch("hardware_checks.ROOT", fixture_root):
        if board_inputs(SimpleNamespace(path=control)) != example:
            raise AssertionError("physical input checker changed valid schema content")
    cases = {
        "missing-qip": ({"qip_files": ["fpga/absent.qip"]},
                        "missing public FPGA input fpga/absent.qip"),
        "missing-support": ({"support_sources": ["fpga/absent.sv"]},
                            "missing public FPGA input fpga/absent.sv"),
        "missing-ddr-documentation": (
            {"ddr4": {**example["ddr4"], "documentation_url": None}}, "ddr4.documentation_url"),
        "timing-exception": ({"timing_exceptions": ["fixture-only exception"]},
                             "no timing exceptions admitted"),
        "metadata-source": ({"top_source": ".vulcan/fixture.sv"},
                            "nonportable board input .vulcan/fixture.sv"),
        "parent-source": ({"top_source": "../fixture.sv"},
                          "nonportable board input ../fixture.sv"),
    }
    for field in ("capacity_bytes", "channels", "data_width_bits"):
        for label, value in (("negative", -1), ("zero", 0), ("boolean", True),
                             ("float", 1.0), ("string", "1"), ("null", None)):
            cases[f"{field}-{label}"] = (
                {"ddr4": {**example["ddr4"], field: value}},
                "ddr4." + field + ": positive integer required")
    cases.update({
        "boolean-schema": ({"schema": True}, "schema 1 and exact Arria 10 GX target 10AX115N2F45E1SG"),
        "float-pcie-generation": (
            {"pcie": {**example["pcie"], "generation": 3.0}},
            "identified physical PCIe Gen3 x8 integration"),
        "float-pcie-lanes": (
            {"pcie": {**example["pcie"], "lanes": 8.0}},
            "identified physical PCIe Gen3 x8 integration"),
        "nonobject-ddr": ({"ddr4": []}, "ddr4: object required"),
        "nonobject-board": ({"board": None}, "board: object required"),
        "nonobject-pcie": ({"pcie": "fixture"}, "pcie: object required"),
        "whitespace-board-model": (
            {"board": {**example["board"], "model": " "}}, "board.model"),
        "nontext-board-model": (
            {"board": {**example["board"], "model": 123}}, "board.model"),
    })
    for name, (updates, expected) in cases.items():
        output = folder / name
        output.mkdir()
        write_json(fixture_root / "fpga/board_manifest.json", {**example, **updates})
        with patch("hardware_checks.ROOT", fixture_root):
            try:
                board_inputs(SimpleNamespace(path=output))
            except PhysicalPrerequisiteError as exc:
                if expected not in exc.unmet:
                    raise AssertionError("missing precise physical input diagnosis: " + name) from exc
                report = json.loads((output / "physical-prerequisites.json").read_text())
                if list(exc.unmet) != report["unmet"]:
                    raise AssertionError("physical input exception/report disagreement")
            else:
                raise AssertionError("invalid board input accepted: " + name)
    output = folder / "prerequisite-delegation"
    output.mkdir()
    marker = "fixture-only missing generated IP"
    with patch("prerequisites.configuration", return_value={}), \
            patch("prerequisites.validate_assets", return_value=[]), \
            patch("prerequisites.baseline_adapters", return_value={"generations": []}), \
            patch("prerequisites.board_inputs",
                  side_effect=PhysicalPrerequisiteError([marker])) as validator:
        try:
            prerequisites(SimpleNamespace(path=output))
        except RuntimeError as exc:
            if not str(exc).startswith("unmet prerequisites: ") or marker not in str(exc):
                raise AssertionError("unexpected prerequisite failure") from exc
        else:
            raise AssertionError("prerequisite gate accepted missing physical inputs")
        validator.assert_called_once()
    report = json.loads((output / "prerequisites.json").read_text())
    rows = [row for row in report["prerequisites"]
            if row["requirement"] == "physical-input:" + marker]
    if len(rows) != 1 or rows[0]["met"] is not False:
        raise AssertionError("prerequisite gate lost shared physical input rejection")
    return {"rejected_input_defects": list(cases), "shared_validation_failure_retained": True,
            "valid_schema_control": "offline synthetic fixture only",
            "scope": "offline checker fixtures only; no physical identity, access, fit or HIL"}


def inflight_tool_receipt(run):
    from receipt_write_checks import receipt_write_checks
    from snapshot_retention_checks import snapshot_retention_checks

    atomic_updates = receipt_write_checks(run.path / "receipt-write-fixtures")
    snapshot_retention = snapshot_retention_checks(run.path / "snapshot-retention-fixtures")
    receipt = run.path / ("tool-%04d" % len(run.records)) / "receipt.json"
    script = (
        "import json, pathlib, sys; "
        "record=json.loads(pathlib.Path(sys.argv[1]).read_text()); "
        "assert record['argv'][0]=='python3'; "
        "assert record['exit_code'] is None and not record['timeout']; "
        "assert 'finished_at' not in record; "
        "assert record['timeout_s']>=3600; "
        "print('in-flight tool receipt retained')"
    )
    text, record = run.tool(["python3", "-c", script, run.rel(receipt)])
    if text.strip() != "in-flight tool receipt retained" or record["exit_code"] != 0:
        raise AssertionError("in-flight tool receipt was not independently observed")
    completed = json.loads(receipt.read_text())
    aggregate = json.loads((run.path / "receipt.json").read_text())
    if completed != record or aggregate["executions"][-1] != completed:
        raise AssertionError("completed child receipt differs from retained aggregate")
    if (completed.get("finished_at", 0) < completed["started_at"] or
            completed["exit_code"] != 0 or completed["timeout"]):
        raise AssertionError("child completion was not durably retained")
    if ((ROOT / completed["stdout"]).read_text().strip() !=
            "in-flight tool receipt retained" or
            (ROOT / completed["stderr"]).read_bytes() != b""):
        raise AssertionError("completed child logs differ from observed storage probe")
    return {"receipt": run.rel(receipt), "observed_before_child_exit": True,
            "completed_receipt_and_aggregate_read_back": True,
            "completed_logs_read_back": True,
            "atomic_update_sensitivity": atomic_updates,
            "snapshot_failure_sensitivity": snapshot_retention,
            "scope": "project subprocess retention only; not shared-runtime persistence recovery"}


def decoder_trace_sensitivity(run):
    from decoder_checks import compare_trace
    from parameters import A

    folder = run.path / "trace-checker-sensitivity"
    folder.mkdir()
    expected = {"writes": [], "logits": [[7, 11], [13, 17]]}
    lines = [
        "TOKEN\t0\t1\t1", "REQUEST\t0\t0\t1\t0\t2\t1",
        "LOGIT\t0\t0\t7\t7", "LOGIT\t0\t1\t11\t8", "DONE\t0\t8",
        "TOKEN\t1\t2\t9", "LOGIT\t1\t0\t13\t11", "LOGIT\t1\t1\t17\t12",
        "DONE\t1\t12", "STALLS\t0\t0\t0", "SUMMARY\t2\t2\t1\t1\t14",
    ]
    original = folder / "valid"
    original.mkdir()
    path = original / "trace.tsv"
    path.write_text("\n".join(lines) + "\n")
    valid = compare_trace(original, expected, A, expected_tokens=[1, 2])
    if valid["compared_bits"] != 128 or valid["token_cycles"] != [8, 4]:
        raise AssertionError("trace checker changed valid measured work")
    mutations = {
        "wrong-token-identifier": (0, "TOKEN\t0\t2\t1"),
        "negative-token-identifier": (0, "TOKEN\t0\t-1\t1"),
        "out-of-range-token-identifier": (0, f"TOKEN\t0\t{A.VOCAB_SIZE}\t1"),
        "negative-logit-token": (2, "LOGIT\t-1\t0\t7\t7"),
        "duplicate-token": (0, lines[0] + "\n" + lines[0]),
        "zero-cycle-completion": (4, "DONE\t0\t1"),
        "negative-stall-count": (9, "STALLS\t-1\t0\t0"),
        "zero-cycle-logit": (2, "LOGIT\t0\t0\t7\t1"),
        "negative-logit-cycle": (2, "LOGIT\t0\t0\t7\t-1"),
        "logit-after-completion": (3, "LOGIT\t0\t1\t11\t9"),
        "summary-before-completion": (10, "SUMMARY\t2\t2\t1\t1\t11"),
        "same-cycle-logits": (3, "LOGIT\t0\t1\t11\t7"),
        "decreasing-logit-cycles": (3, "LOGIT\t0\t1\t11\t6"),
        "overlapping-token-intervals": (5, "TOKEN\t1\t2\t8"),
        "summary-at-completion": (10, "SUMMARY\t2\t2\t1\t1\t12"),
        "delayed-completion": (8, "DONE\t1\t13"),
        "missing-request-field": (1, "REQUEST\t0\t0\t1\t0\t2"),
        "extra-request-field": (1, lines[1] + "\t99"),
        "empty-request-field": (1, "REQUEST\t0\t0\t1\t0\t\t1"),
        "invalid-decimal-field": (1, "REQUEST\t0\t0\t1\t0\tXZ\t1"),
        "invalid-hex-write": (1, "WRITE\t0\t8\t0\t0\t0\t0\t0000000x\t2"),
        "blank-record": (1, ""),
        "negative-request-token": (1, "REQUEST\t-1\t0\t1\t0\t2\t1"),
        "unaccepted-request-token": (1, "REQUEST\t2\t0\t1\t0\t2\t1"),
        "negative-request-bank": (1, "REQUEST\t0\t-1\t1\t0\t2\t1"),
        "out-of-range-request-bank": (1, f"REQUEST\t0\t{A.BANKS}\t1\t0\t2\t1"),
        "negative-request-kind": (1, "REQUEST\t0\t0\t-1\t0\t2\t1"),
        "out-of-range-request-kind": (1, "REQUEST\t0\t0\t16\t0\t2\t1"),
        "invalid-request-direction": (1, "REQUEST\t0\t0\t1\t2\t2\t1"),
        "immutable-tensor-write": (1, "REQUEST\t0\t0\t1\t1\t2\t1"),
        "request-at-token-acceptance": (1, "REQUEST\t0\t0\t1\t0\t1\t1"),
        "request-after-token-completion": (1, "REQUEST\t0\t0\t1\t0\t9\t1"),
        "negative-request-tag": (1, "REQUEST\t0\t0\t1\t0\t2\t-1"),
        "overflow-request-tag": (1, f"REQUEST\t0\t0\t1\t0\t2\t{1 << 64}"),
    }
    for name, (index, replacement) in mutations.items():
        case = folder / name
        case.mkdir()
        mutated = list(lines)
        mutated[index] = replacement
        (case / "trace.tsv").write_text("\n".join(mutated) + "\n")
        try:
            compare_trace(case, expected, A, expected_tokens=[1, 2])
        except AssertionError:
            pass
        else:
            raise AssertionError("trace checker accepted malformed measurement: " + name)
    truncated = folder / "unterminated"
    truncated.mkdir()
    (truncated / "trace.tsv").write_text("\n".join(lines))
    try:
        compare_trace(truncated, expected, A, expected_tokens=[1, 2])
    except AssertionError as exc:
        if "unterminated trace record" not in str(exc):
            raise
    else:
        raise AssertionError("trace checker accepted unterminated record")
    write_expected = {**expected, "writes": [[0, 8, 0, 0, 0, 0, 7]]}
    write_lines = list(lines)
    write_lines[1] = "REQUEST\t0\t0\t8\t1\t3\t1"
    write_lines.insert(2, "WRITE\t0\t8\t0\t0\t0\t0\t00000007\t3")
    write_valid = folder / "valid-write"
    write_valid.mkdir()
    (write_valid / "trace.tsv").write_text("\n".join(write_lines) + "\n")
    if compare_trace(write_valid, write_expected, A, expected_tokens=[1, 2])["compared_bits"] != 160:
        raise AssertionError("trace checker changed valid write comparison")
    write_defects = {
        "negative-write-cycle": -1,
        "zero-write-cycle": 0,
        "write-at-token-acceptance": 1,
        "write-after-token-completion": 9,
        "write-without-same-edge-request": 4,
    }
    for name, cycle in write_defects.items():
        case = folder / name
        case.mkdir()
        mutated = list(write_lines)
        mutated[2] = f"WRITE\t0\t8\t0\t0\t0\t0\t00000007\t{cycle}"
        (case / "trace.tsv").write_text("\n".join(mutated) + "\n")
        try:
            compare_trace(case, write_expected, A, expected_tokens=[1, 2])
        except AssertionError:
            pass
        else:
            raise AssertionError("trace checker accepted malformed measurement: " + name)
    request_defects = {
        "write-with-only-read-request": "REQUEST\t0\t0\t1\t0\t3\t1",
        "write-with-wrong-kind-request": "REQUEST\t0\t0\t9\t1\t3\t1",
        "write-with-duplicate-request": write_lines[1] + "\nREQUEST\t0\t1\t8\t1\t3\t2",
    }
    for name, replacement in request_defects.items():
        case = folder / name
        case.mkdir()
        mutated = list(write_lines)
        mutated[1] = replacement
        if name == "write-with-duplicate-request":
            mutated[-1] = "SUMMARY\t2\t2\t2\t2\t14"
        (case / "trace.tsv").write_text("\n".join(mutated) + "\n")
        try:
            compare_trace(case, write_expected, A, expected_tokens=[1, 2])
        except AssertionError:
            pass
        else:
            raise AssertionError("trace checker accepted unowned write: " + name)
    fault_lines = [
        "FAULT_REQUEST\t-2\t0\t8\t1\t0\t5",
        "FAULT_WRITE\t-2\t8\t0\t0\t0\t0\t00000007\t0",
        "ABORTED\t1\t1\t1\t1", "REJECT\t1\t0",
        *write_lines,
    ]
    fault_lines[-1] = "SUMMARY\t2\t2\t2\t2\t14"
    fault_valid = folder / "valid-fault-write"
    fault_valid.mkdir()
    (fault_valid / "trace.tsv").write_text("\n".join(fault_lines) + "\n")
    if compare_trace(fault_valid, write_expected, A, expected_tokens=[1, 2],
                     fault_scenario=1)["compared_bits"] != 192:
        raise AssertionError("trace checker changed valid aborted write comparison")
    fault_defects = {
        "fault-write-with-only-read-request": (0, "FAULT_REQUEST\t-2\t0\t1\t0\t0\t5"),
        "fault-write-with-wrong-kind-request": (0, "FAULT_REQUEST\t-2\t0\t9\t1\t0\t5"),
        "fault-write-without-same-edge-request":
            (1, "FAULT_WRITE\t-2\t8\t0\t0\t0\t0\t00000007\t1"),
    }
    for name, (index, replacement) in fault_defects.items():
        case = folder / name
        case.mkdir()
        mutated = list(fault_lines)
        mutated[index] = replacement
        (case / "trace.tsv").write_text("\n".join(mutated) + "\n")
        try:
            compare_trace(case, write_expected, A, expected_tokens=[1, 2], fault_scenario=1)
        except AssertionError:
            pass
        else:
            raise AssertionError("trace checker accepted unowned aborted write: " + name)
    return {"valid_compared_bits": 128, "rejected_trace_defects": list(mutations),
            "valid_write_compared_bits": 160,
            "rejected_write_timing_defects": list(write_defects),
            "rejected_write_request_defects": list(request_defects),
            "valid_fault_write_compared_bits": 192,
            "rejected_fault_write_request_defects": list(fault_defects),
            "unterminated_record_rejected": True,
            "scope": "checker fixtures only; not RTL execution or benchmark acceptance"}


def hardware_metrics():
    key = "wns_setup_ns"
    valid = (0, 0.125, -0.125, 3)
    for value in valid:
        if measured_metric({"corners": [{"timing": {key: value}}]}, key) != value:
            raise AssertionError("measured timing metric changed")
    invalid = ({}, {key: True}, {key: "0.0"}, {key: None},
               {key: float("nan")}, {key: float("inf")}, {key: -float("inf")},
               {"corners": [{key: 0}, {key: -1}]})
    for index, report in enumerate(invalid):
        try:
            measured_metric(report, key)
        except AssertionError:
            pass
        else:
            raise AssertionError("invalid measured timing metric accepted: case " + str(index))
    return {"finite_metrics_preserved": len(valid), "invalid_metrics_rejected": len(invalid),
            "scope": "checker sensitivity only; no physical timing measurement"}


def baseline_index_sensitivity():
    content = b"hello\n"
    indexed = {"type": "blob", "mode": "100644", "size": 6,
               "sha": "ce013625030ba8dba906f756967f9e9ca394464a"}
    verify_indexed_blob(indexed, content)
    invalid = (
        ({}, content),
        ({**indexed, "type": "tree"}, content),
        ({**indexed, "mode": "120000"}, content),
        ({**indexed, "size": True}, content),
        ({**indexed, "size": 0}, content),
        ({**indexed, "size": 4194305}, content),
        ({**indexed, "sha": None}, content),
        ({**indexed, "sha": "main"}, content),
        ({**indexed, "sha": "0" * 40}, content),
        ({**indexed, "size": 7}, content),
        (indexed, b"Hello\n"),
        (indexed, content[:-1]),
    )
    for item, data in invalid:
        try:
            verify_indexed_blob(item, data)
        except AssertionError:
            pass
        else:
            raise AssertionError("unbound or altered public candidate content accepted")
    return {"known_git_blob_verified": 1, "invalid_blobs_rejected": len(invalid),
            "scope": "offline source-index checker fixtures; not baseline acceptance"}


def commit_search_sensitivity():
    repository = "public-owner/candidate"
    revision = "1" * 40
    item = {"sha": revision, "repository": {"full_name": repository}}
    valid = {"total_count": 1, "incomplete_results": False, "items": [item]}
    if commit_search_entries(valid, repository) != [{"revision": revision}]:
        raise AssertionError("public commit search lost immutable identity")
    empty = {**valid, "total_count": 0, "items": []}
    if commit_search_entries(empty, repository) != []:
        raise AssertionError("empty public commit search invented a candidate")
    invalid = (
        {}, {**valid, "total_count": True}, {**valid, "total_count": -1},
        {**valid, "total_count": 0}, {**valid, "incomplete_results": 0},
        {**valid, "items": {}}, {**valid, "items": [None]},
        {**valid, "items": [{**item, "sha": "main"}]},
        {**valid, "items": [{**item, "repository": None}]},
        {**valid, "items": [{**item, "repository": {"full_name": None}}]},
        {**valid, "items": [{**item, "repository": {"full_name": "other/repo"}}]},
    )
    for payload in invalid:
        try:
            commit_search_entries(payload, repository)
        except AssertionError:
            pass
        else:
            raise AssertionError("malformed or wrong-repository commit search accepted")
    return {"valid_candidates": 1, "empty_candidates": 0,
            "invalid_responses_rejected": len(invalid),
            "scope": "parser fixtures only; not baseline validation"}


def issue_search_sensitivity():
    repository = "public-owner/candidate"
    item = {"number": 1, "state": "open", "title": "Q4 source availability",
            "repository_url": "https://api.github.com/repos/" + repository,
            "html_url": "https://github.com/" + repository + "/issues/1"}
    valid = {"total_count": 1, "incomplete_results": False, "items": [item]}
    result = issue_search_entries(valid, repository)
    if len(result) != 1 or result[0]["number"] != 1 or result[0]["url"] != item["html_url"]:
        raise AssertionError("public issue search lost discussion identity")
    if issue_search_entries({**valid, "total_count": 0, "items": []}, repository):
        raise AssertionError("empty issue search invented a candidate")
    invalid = (
        {}, {**valid, "total_count": True}, {**valid, "total_count": -1},
        {**valid, "total_count": 0}, {**valid, "incomplete_results": 0},
        {**valid, "items": {}}, {**valid, "items": [None]},
        *({**valid, "items": [{**item, **change}]} for change in (
            {"number": True}, {"number": 0}, {"state": "unknown"},
            {"repository_url": None}, {"repository_url": "https://api.github.com/repos/other/repo"},
            {"title": None}, {"html_url": "https://github.com/other/repo/issues/1"},
            {"pull_request": {}},
        )),
    )
    for payload in invalid:
        try:
            issue_search_entries(payload, repository)
        except AssertionError:
            pass
        else:
            raise AssertionError("malformed or wrong-repository issue search accepted")
    return {"valid_discussions": len(result), "invalid_responses_rejected": len(invalid),
            "scope": "parser sensitivity only; not baseline validation"}


def reconciliation_scope_sensitivity():
    """Reject out-of-scope receipts before accessing evidence bytes."""
    from unittest.mock import patch
    from trace_integrity import (preparation_receipt_path, reconcile,
                                 decoder_preparation_options)

    valid = "evidence/preparation/decoder-scope-fixture/receipt.json"
    if preparation_receipt_path(valid) != (ROOT / valid).resolve():
        raise AssertionError("decoder preparation scope changed")
    invalid = ("evidence/check-prerequisites/missing-scope-fixture/receipt.json",
               "tests/missing-scope-fixture.json",
               "../missing-scope-fixture.json")
    for value in invalid:
        with patch("trace_integrity.sha256") as read_receipt:
            try:
                reconcile(value)
            except ValueError as exc:
                if "require shared-runtime diagnosis" not in str(exc):
                    raise AssertionError("reconciliation lost actionable scope diagnosis") from exc
            else:
                raise AssertionError("decoder reconciliation accepted out-of-scope receipt")
            read_receipt.assert_not_called()
    base = ["python3", "tests/prepare.py", "--probe", "decoder"]
    invocations = (base, base + ["--asymmetric", "0"],
                   base + ["--profile", "3", "--banks", "8", "--mode", "2",
                           "--asymmetric", "1", "--seed", "257", "--tokens", "7",
                           "--simulator", "iverilog"])
    for argv in invocations:
        options = decoder_preparation_options(argv)
        if options.get("--asymmetric", "0") != ("1" if argv is invocations[-1] else "0"):
            raise AssertionError("reconciliation changed the decoder asymmetric selection")
    invalid_invocations = (
        base + ["--asymmetric", "2"],
        base + ["--asymmetric", "1", "--asymmetric", "0"],
        base + ["--asymmetric"],
        base + ["--unknown", "1"],
        ["python3", "tests/prepare.py", "--probe", "harness"],
    )
    for argv in invalid_invocations:
        try:
            decoder_preparation_options(argv)
        except AssertionError:
            pass
        else:
            raise AssertionError("reconciliation accepted an invalid decoder invocation")
    return {"accepted_preparation_path_shape": 1,
            "out_of_scope_paths_rejected_before_read": len(invalid),
            "accepted_decoder_invocations": len(invocations),
            "invalid_decoder_invocations_rejected": len(invalid_invocations),
            "scope": "path/invocation fixtures only; no receipt or runtime persistence repaired"}


def harness(run):
    from delivery_gate_checks import delivery_gate_sensitivity
    from preparation_checks import preparation_dispatch_sensitivity
    from simulation_tiering_checks import dispatch_sensitivity

    run.versions([("python3", "--version")])
    inflight = inflight_tool_receipt(run)
    first_versions = dict(run.tool_versions)
    run.versions([("iverilog", "-V")])
    if any(run.tool_versions.get(name) != record for name, record in first_versions.items()
           if name != "iverilog"):
        raise AssertionError("successive version collection discarded prior tool provenance")
    metrics = hardware_metrics()
    native_baselines = native_baseline_sensitivity()
    baseline_index = baseline_index_sensitivity()
    commit_search = commit_search_sensitivity()
    issue_search = issue_search_sensitivity()
    reconciliation_scope = reconciliation_scope_sensitivity()
    preparation_dispatch = preparation_dispatch_sensitivity()
    simulation_tiering = dispatch_sensitivity()
    fitted_summaries = fitted_summary_sensitivity(run)
    physical_inventory = physical_inventory_sensitivity(run)
    board_inputs = board_prerequisite_sensitivity(run)
    delivery_gates = delivery_gate_sensitivity(run)
    traces = decoder_trace_sensitivity(run)
    selected = {str(path.relative_to(ROOT)) for path in sources()}
    required = {"tests/verify.py", "tests/reproduce_worker.py", "tests/reference.py",
                "tests/top_tb.sv", "rtl/anvil_q3_top.sv"}
    if not required.issubset(selected) or selected != set(run.hashes):
        raise AssertionError("incomplete verification/source receipt binding")
    run.tool(["python3", "-m", "compileall", "-q", "tests"])
    run.tool(["python3", "tests/verify.py", "--help"])
    positive, negative = positive_cases(), negative_cases()
    for label, geometry in positive:
        if not legal(geometry):
            raise AssertionError("bad positive geometry " + label)
    for label, geometry in negative:
        if legal(geometry):
            raise AssertionError("bad negative geometry " + label)
    covered = {geometry for _, geometry in positive}
    for profile in (2, 3):
        geometry = replace(startup_geometry(profile), CACHE_MODE=1 if profile == 2 else 2,
                           INT4_ASYM=int(profile == 3))
        if geometry not in covered:
            raise AssertionError("functional fault-recovery geometry absent from structure gate")
    absent = baseline_prerequisites([], run.hashes)
    if len(absent["unmet"]) != 4 or absent["q1_wrapper_is_independent_q1"]:
        raise AssertionError("missing baseline prerequisite detection failed")
    supplied = [{"sha256": value, "url": "https://example.invalid/" + name.rsplit("/", 1)[-1]}
                for name, value in run.hashes.items() if name.startswith("anvil_q2_reference/rtl/")]
    fixture = [{"category": "baseline", "generation": generation,
                "contents": supplied}
               for generation in ("Q1", "Q2")]
    present = baseline_prerequisites(fixture, run.hashes)
    if ([row["public_provenance_met"] for row in present["generations"]]
            != [True, True, False] or
            [row["source_bound_execution_adapter"] for row in present["generations"]]
            != [False, True, False] or len(present["unmet"]) != 3):
        raise AssertionError("baseline provenance confused with executable adapter coverage")
    renamed = [{"category": "baseline", "generation": "Q2",
                "contents": [{**item, "url": item["url"] + ".renamed.sv"}
                             for item in supplied]}]
    if any(row["source_bound_execution_adapter"]
           for row in baseline_prerequisites(renamed, run.hashes)["generations"]):
        raise AssertionError("source-bound baseline adapter accepted renamed RTL")
    revision = "1" * 40
    if (q4_history_entries([{"sha": revision}]) != [{"revision": revision}] or
            q4_history_entries([]) != []):
        raise AssertionError("public Q4 path history identity parsing changed")
    invalid_history = ({}, [None], [{}], [{"sha": "main"}], [{"sha": 1}])
    for payload in invalid_history:
        try:
            q4_history_entries(payload)
        except AssertionError:
            pass
        else:
            raise AssertionError("malformed public Q4 path history accepted")
    pr = {"number": 1, "state": "closed",
          "head": {"sha": revision, "repo": {"full_name": "public-owner/candidate"}}}
    parsed_prs = pull_request_entries([pr])
    deleted_pr = pull_request_entries([{**pr, "head": {"sha": revision, "repo": None}}])
    if (parsed_prs[0]["revision"] != revision or
            parsed_prs[0]["repository"] != "public-owner/candidate" or
            deleted_pr[0]["repository"] is not None or pull_request_entries([]) != []):
        raise AssertionError("public PR head identity parsing changed")
    invalid_prs = ({}, [None], [{**pr, "number": True}], [{**pr, "number": 0}],
                   [{**pr, "state": "merged"}], [{**pr, "head": None}],
                   [{**pr, "head": {"sha": "main", "repo": None}}],
                   [{**pr, "head": {"sha": revision, "repo": {"full_name": "../candidate"}}}])
    for payload in invalid_prs:
        try:
            pull_request_entries(payload)
        except AssertionError:
            pass
        else:
            raise AssertionError("malformed public PR head accepted")
    for kind in ("branches", "tags"):
        entries = reference_entries(kind, [{"name": "q4-candidate", "commit": {"sha": revision}}])
        if entries != [{"name": "q4-candidate", "revision": revision}]:
            raise AssertionError("immutable public reference parsing changed")
    release = reference_entries("releases", [{"tag_name": "v4", "target_commitish": "main"}])
    if "revision" in release[0] or release[0]["target_commitish"] != "main":
        raise AssertionError("release metadata was treated as an immutable source revision")
    for kind, payload in (("branches", {}), ("tags", [None]),
                          ("tags", [{"name": "v4", "commit": {"sha": "main"}}]),
                          ("branches", [{"name": "v4", "commit": None}]),
                          ("releases", [{"tag_name": ""}])):
        try:
            reference_entries(kind, payload)
        except AssertionError:
            pass
        else:
            raise AssertionError("malformed public reference was accepted: " + kind)
    fork = {"full_name": "public-owner/candidate", "default_branch": "main", "fork": True}
    parsed_forks = fork_entries([fork])
    if (len(parsed_forks) != 1 or parsed_forks[0]["repository"] != fork["full_name"] or
            parsed_forks[0]["default_branch"] != "main" or "revision" in parsed_forks[0] or
            fork_entries([]) != []):
        raise AssertionError("public fork metadata confused with immutable source identity")
    invalid_forks = ({}, [None], [{**fork, "fork": False}],
                     [{**fork, "fork": 1}], [{**fork, "full_name": "../candidate"}],
                     [{**fork, "default_branch": ""}])
    for payload in invalid_forks:
        try:
            fork_entries(payload)
        except AssertionError:
            pass
        else:
            raise AssertionError("malformed public fork was accepted")
    leaves = leaf_cases()
    for module, parameters, expected in leaves:
        if leaf_legal(module, parameters) != expected:
            raise AssertionError("leaf legality mismatch " + module)
    for name, filename, before, _after, _kind, geometry in MUTATIONS:
        if (ROOT / "rtl" / filename).read_text().count(before) != 1:
            raise AssertionError("nonunique mutation target " + name)
        if not legal(geometry):
            raise AssertionError("illegal mutation geometry " + name)
    frozen, _ = quality_lock()
    if frozen != json.loads((ROOT / "tests/benchmark_lock.json").read_text()):
        raise AssertionError("frozen corpus/reference changed")
    return {"positive_geometries": len(positive), "negative_geometries": len(negative),
            "inflight_tool_receipt": inflight,
            "successive_tool_versions_preserved": sorted(run.tool_versions),
            "hardware_metrics": metrics,
            "native_baseline_adapter_checker": native_baselines,
            "public_baseline_index_checker": baseline_index,
            "public_commit_search_parser": commit_search,
            "public_issue_search_parser": issue_search,
            "reconciliation_scope_checker": reconciliation_scope,
            "preparation_dispatch_checker": preparation_dispatch,
            "simulation_tiering_dispatch_checker": simulation_tiering,
            "fitted_summary_checker": fitted_summaries,
            "physical_inventory_checker": physical_inventory,
            "board_prerequisite_checker": board_inputs,
            "delivery_gate_checker": delivery_gates,
            "decoder_trace_sensitivity": traces,
            "leaf_geometries": len(leaves),
            "public_q4_history_parser": {"valid_commit_count": 1,
                                         "invalid_responses_rejected": len(invalid_history),
                                         "scope": "parser fixtures, not baseline execution"},
            "public_pull_request_parser": {"valid_head_count": len(parsed_prs),
                                           "deleted_repository_not_invented": True,
                                           "invalid_payloads_rejected": len(invalid_prs)},
            "public_fork_parser": {"valid_candidate_count": len(parsed_forks),
                                   "invalid_payloads_rejected": len(invalid_forks)},
            "unique_mutation_targets": len(MUTATIONS), "frozen_quality_lock": "matched",
            "scope": "Python/source consistency only; no functional/structure/coverage gate passed"}
