"""Read-only reconciliation of retained controller results, never a replay.

Use tests/verify.py --probe retained-controller-audit --repair-of <recovery receipt>.
Additional --repair-of arguments link prior audits of that same recovery.
Missing historical receipts are reported with nonzero exit, never reconstructed.
The retained-provenance-audit probe checks linked receipt hashes recursively;
it does not certify their functional results or restore missing artifacts.
"""

import json
from pathlib import Path
import re


def receipt_graph(root, links, digest, failure):
    """Inventory receipt ancestry without executing producers or changing evidence."""
    root = root.resolve()
    report = {
        "scope": "Receipt ancestry/hash audit only; no functional or acceptance claim",
        "receipts": [], "gaps": [], "historical_provenance_complete": False,
    }
    visited, active = {}, set()

    def visit(link):
        name, expected = link["path"], link["sha256"]
        relative = Path(name)
        if (relative.is_absolute() or ".." in relative.parts
                or relative.parts[:2] not in (
                    ("evidence", "preparation"), ("evidence", "verification"))
                or relative.name != "receipt.json"):
            raise failure(f"Nonportable retained receipt path: {name}")
        candidate = root / relative
        if not candidate.resolve().is_relative_to((root / "evidence").resolve()):
            raise failure(f"Retained receipt escapes project evidence: {name}")
        if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
            raise failure(f"Invalid retained receipt hash: {name}")
        if name in active:
            report["gaps"].append({"path": name, "issue": "cyclic receipt ancestry"})
            return
        if name in visited:
            if visited[name] != expected:
                report["gaps"].append({
                    "path": name, "issue": "conflicting recorded hashes",
                    "expected_sha256": expected, "other_sha256": visited[name]})
            return
        visited[name] = expected
        entry = {"path": name, "expected_sha256": expected}
        report["receipts"].append(entry)
        try:
            actual = digest(candidate)
        except FileNotFoundError:
            entry["present"] = False
            report["gaps"].append(dict(entry, issue="missing authentic receipt"))
            return
        entry.update(present=True, actual_sha256=actual)
        if actual != expected:
            report["gaps"].append(dict(entry, issue="receipt hash mismatch"))
            return
        receipt = json.loads(candidate.read_text())
        entry["recorded_exit_code"] = receipt["exit_code"]
        entry["interpretation"] = "Hash-bound historical record, not re-execution"
        active.add(name)
        for predecessor in receipt.get("repair_of", []):
            visit(predecessor)
        active.remove(name)

    if not links:
        raise failure("Provenance audit requires at least one --repair-of receipt")
    for link in links:
        visit(link)
    report["historical_provenance_complete"] = not report["gaps"]
    return report


def audit_provenance(evidence, root, digest, write_json, failure):
    report = receipt_graph(root, evidence.record["repair_of"], digest, failure)
    evidence.record["retained_provenance_audit"] = report
    write_json(evidence.path / "retained-provenance-audit.json", report)
    if report["gaps"]:
        raise failure(
            f"Historical provenance incomplete: {len(report['gaps'])} receipt gaps. "
            "See retained-provenance-audit.json. Authentic restoration belongs to "
            "the shared runtime; no producers or simulations were rerun")


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
