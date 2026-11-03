"""Bounded case-persistence controls; no historical replay or acceptance reuse."""

import copy
import json
from pathlib import Path

from protocol import UART


ROOT = Path(__file__).resolve().parent.parent


def run_case_records(evidence, failure, digest, write_json):
    evidence.tools(("python3", "iverilog", "vvp", "verilator", "g++", "make"))
    evidence.child(
        ["python3", "tests/test_case_records.py", evidence.relative(evidence.path)],
        "case-record-regression")
    bench = UART.replace("DIVISOR", "4").replace("@DEPTH@", "1").replace("SEED", "17")
    sources = ["rtl/anvil_edge_fifo.sv", "rtl/anvil_edge_uart_io.sv"]

    def smoke(scope, simulator):
        row = scope.simulate("case-record-uart-" + simulator, bench, sources,
                             78, simulator=simulator)
        scope.record["case_record_control"] = {
            "simulator": simulator, "actual_comparisons": row["actual_comparisons"],
            "scope": "Compact public-port UART diagnostic, not system acceptance",
        }

    evidence.run_cases([
        ("uart-" + simulator,
         lambda scope, simulator=simulator: smoke(scope, simulator))
        for simulator in ("iverilog", "verilator")
    ])
    before = len(evidence.record["case_batches"])
    control = copy.copy(evidence)
    control.record = dict(evidence.record, children=[], coverage=[], case_batches=[])

    def failed_child(scope):
        scope.child(["python3", "-c",
                     "raise SystemExit('EXPECTED_CASE_PERSISTENCE_CONTROL')"],
                    "expected-child-failure")

    def surviving_peer(scope):
        scope.record["surviving_peer"] = {"observed": "completed after peer submission"}

    try:
        control.run_cases([
            ("expected-child-failure", failed_child),
            ("surviving-peer", surviving_peer),
        ], workers=1)
    except failure as error:
        control.record["expected_harness_rejection"] = str(error)
    else:
        raise failure("The deliberately failing child was accepted")
    # Keep the negative harness batch separate from product-functional coverage.
    evidence.record["case_persistence_negative_control"] = control.record
    evidence.record["children"].extend(control.record["children"])
    assert len(evidence.record["case_batches"]) == before
    assert control.record["case_batches"][0]["status"] == "failed"
    assert [row["status"] for row in control.record["case_batches"][0]["results"]] == [
        "failed", "passed"]
    assert control.record["children"][0]["exit_code"] == 1
    log = ROOT / control.record["children"][0]["stderr"]
    assert log.read_text().strip() == "EXPECTED_CASE_PERSISTENCE_CONTROL"
    assert evidence._root._case_scopes == 0 and not evidence._root._active_children

    records = []
    for batch in [*evidence.record["case_batches"], *control.record["case_batches"]]:
        for case in batch["results"]:
            path = ROOT / case["result_record"]
            record = json.loads(path.read_text())
            assert digest(path) == case["result_sha256"]
            assert record["case"] == {
                key: value for key, value in case.items() if key != "result_sha256"}
            assert record["child_settled"] and not record["acceptance_evidence"]
            manifest = record["source_manifest"]
            assert digest(ROOT / manifest["path"]) == manifest["sha256"]
            assert record["record"]["source_sha256"] == evidence.record["source_sha256"]
            assert record["parent_receipt"] == evidence.relative(evidence.path / "receipt.json")
            assert not (ROOT / record["parent_receipt"]).exists()
            records.append({
                "path": case["result_record"], "sha256": case["result_sha256"],
                "status": case["status"], "child_settled": record["child_settled"],
            })
    assert len(records) == 4
    rows = evidence.record["coverage"]
    assert len(rows) == 2 and all(row["status"] == "passed" for row in rows)
    assert {row["simulator"] for row in rows} == {"iverilog", "verilator"}
    summary = {
        "scope": "New compact UART runs and synthetic harness-failure controls only; "
                 "not a repeated controller recovery, full L1, mutation kill or acceptance",
        "case_records": records,
        "compared_uart_observations": sum(row["actual_comparisons"] for row in rows),
        "parent_receipt_absent_while_case_records_readable": True,
        "failed_child_and_completed_peer_retained": True,
        "historical_records_modified": False,
        "mandatory_checks_changed": False,
    }
    evidence.record["case_persistence_measurement"] = summary
    write_json(evidence.path / "case-persistence-measurement.json", summary)
