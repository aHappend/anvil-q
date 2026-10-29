"""Read-only reconciliation of retained controller results, never a replay.

Use tests/verify.py --probe retained-controller-audit --repair-of <recovery receipt>.
Additional --repair-of arguments link prior audits of that same recovery.
Missing historical receipts are reported with nonzero exit, never reconstructed.
"""

import json
from pathlib import Path
import re


def audit_controller(evidence, root, digest, write_json, failure):
    """Keep observed comparisons separate from incomplete historical provenance."""
    links = evidence.record["repair_of"]
    if not links:
        raise failure("Controller audit requires a retained recovery --repair-of receipt")
    for link in links[1:]:
        previous = json.loads((root / link["path"]).read_text())
        if ("retained-controller-audit" not in previous["argv"]
                or previous["repair_of"][0] != links[0]):
            raise failure("Additional audit repair links must reference audits of this recovery")
    receipt = root / links[0]["path"]
    recovery = json.loads(receipt.read_text())
    report = {
        "scope": "Read-only retained-results audit; no simulation or acceptance",
        "recovery_receipt": links[0],
        "comparisons": [],
        "predecessors": [],
        "source_changes_since_recovery": [],
        "gaps": [],
    }
    evidence.record["retained_controller_audit"] = report

    def path(name):
        relative = Path(name)
        if (relative.is_absolute() or ".." in relative.parts or
                relative.parts[:2] not in (
                    ("evidence", "preparation"), ("evidence", "verification"))):
            raise failure(f"Nonportable retained evidence path: {name}")
        candidate = root / relative
        if not candidate.resolve().is_relative_to((root / "evidence").resolve()):
            raise failure(f"Retained evidence escapes project evidence: {name}")
        return candidate

    def require(condition, message):
        if not condition:
            raise failure(message)

    require(recovery["exit_code"] == 0 and recovery["child_settled"] is True
            and recovery["sources_unchanged"] is True,
            "Recovery receipt does not record settled successful execution")
    for name, expected in recovery["source_sha256"].items():
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts
                and relative.parts[0] in ("rtl", "design", "fpga",
                                          "anvil_q1_reference", "tests"),
                f"Unexpected retained source: {name}")
        snapshot = receipt.parent / "sources" / relative
        require(snapshot.is_file() and digest(snapshot) == expected,
                f"Missing or changed retained source snapshot: {name}")
        current = root / relative
        if not current.is_file() or digest(current) != expected:
            report["source_changes_since_recovery"].append(name)
    report["source_changes_since_recovery"].extend(sorted(
        set(evidence.record["source_sha256"]) - set(recovery["source_sha256"])))
    require(not {"rtl/anvil_edge_autoregressive_fsm.sv", "tests/protocol.py"}
            .intersection(report["source_changes_since_recovery"]),
            "Controller RTL or public scoreboard changed since retained execution")
    report["retained_source_snapshots_checked"] = len(recovery["source_sha256"])

    expected_cases = {(4096, seed): 4203 for seed in (1, 17, 89)}
    expected_cases.update({(1, seed): 59 for seed in (1, 17)})
    rows = {row["name"]: row for row in recovery["coverage"]}
    require(len(rows) == len(recovery["coverage"]) == len(expected_cases),
            "Unexpected or duplicate retained controller coverage rows")
    equivalence = recovery["controller_repair"]["equivalence"]
    require(len(equivalence) == len(expected_cases)
            and {(row["capacity"], row["seed"]) for row in equivalence}
            == set(expected_cases), "Incomplete retained equivalence matrix")
    for (capacity, seed), count in expected_cases.items():
        name = f"controller-c{capacity}-s{seed}"
        row = rows[name]
        require(row["status"] == "passed"
                and row["required_comparisons"] == row["actual_comparisons"] == count,
                f"Changed comparison threshold or result: {name}")
        child = row["simulation_receipt"]
        require(child["exit_code"] == 0 and child["timed_out"] is False
                and child["child_settled"] is True
                and child["process_group_settled"] is True,
                f"Unsuccessful or unsettled retained simulation: {name}")
        child_path = path(child["stdout"]).parent / "receipt.json"
        require(json.loads(child_path.read_text()) == child,
                f"Embedded and raw child receipts differ: {name}")
        stdout, stderr = path(child["stdout"]), path(child["stderr"])
        totals = re.findall(r"^COMPARED (\d+)$", stdout.read_text(), re.MULTILINE)
        require(totals == [str(count)], f"Raw comparison count mismatch: {name}")
        eq = next(item for item in equivalence
                  if (item["capacity"], item["seed"]) == (capacity, seed))
        require(json.loads(path(eq["result"]).read_text())
                == {key: value for key, value in eq.items() if key != "result"},
                f"Embedded and retained equivalence records differ: {name}")
        require(all(eq[key] is True for key in (
            "passed", "sources_equal", "compact_rendering_equal",
            "complete_ordered_expansion_equal"))
            and eq["required_comparisons"] == eq["original_required_comparisons"] == count,
            f"Retained equivalence does not establish unchanged vectors: {name}")
        report["comparisons"].append({
            "name": name, "capacity": capacity, "seed": seed,
            "required": count, "observed": int(totals[0]),
            "simulation_receipt": str(child_path.relative_to(root)),
            "stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr),
            "equivalence_result": eq["result"],
            "equivalence_sha256": digest(path(eq["result"])),
            "interpretation": "Historical execution, not a new simulation",
        })

    for link in recovery["repair_of"]:
        predecessor = path(link["path"])
        entry = dict(link, present=predecessor.is_file())
        report["predecessors"].append(entry)
        if not entry["present"]:
            report["gaps"].append("Missing authentic predecessor: " + link["path"])
            continue
        require(digest(predecessor) == link["sha256"],
                f"Retained predecessor hash mismatch: {link['path']}")
        prior = json.loads(predecessor.read_text())
        entry.update(exit_code=prior["exit_code"], timed_out=prior["timed_out"])
        raw_error = path(prior["stderr"])
        entry["stderr_sha256"] = digest(raw_error)
        entry["missing_pch_header_diagnostic"] = (
            "Vbench__pch.h.fast" in raw_error.read_text()
            and "No such file or directory" in raw_error.read_text())
    report["historical_provenance_complete"] = not report["gaps"]
    report["observed_comparisons"] = sum(row["observed"] for row in report["comparisons"])
    write_json(evidence.path / "retained-controller-audit.json", report)
    if report["gaps"]:
        raise failure("Retained controller comparisons confirmed; historical provenance "
                      "incomplete. Authentic restoration belongs to the shared runtime. "
                      "See retained-controller-audit.json; no recovery was rerun")
