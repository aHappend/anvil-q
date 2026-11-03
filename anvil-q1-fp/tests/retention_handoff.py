#!/usr/bin/env python3
"""Observe an existing transaction witness without resuming its simulation."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import artifact_path, load_json, require, sha
from production_checkpoint import validate_segment
from verify import Evidence, ROOT


def validate(witness, observation, ev):
    receipt = load_json(witness / "receipt.json")
    require(receipt["status"] == "passed", "original witness receipt did not pass")
    current = load_json(observation)
    comparisons = {}
    for phase in ("after-child", "after-seal"):
        previous_path = witness / (phase + ".json")
        previous = load_json(previous_path)
        keys = previous.keys() - {"started_at", "ended_at"}
        require(current.keys() == previous.keys(), "observation fields differ")
        differences = [key for key in sorted(keys) if current[key] != previous[key]]
        require(not differences, phase + " differs: " + ", ".join(differences))
        comparisons[phase] = {"path": str(previous_path.relative_to(ROOT)),
                              "sha256": sha(previous_path), "matches": True}
    items = [entry["checkpoint"] for entry in receipt["assertions"]
             if entry["name"] == "transaction_retention_across_seal"]
    require(len(items) == 1, "missing or ambiguous original sealed descriptor")
    chain = []
    row = validate_segment(ev, items[0], chain=chain)
    require(len(chain) == 1 and row["parent"] is None and
            row["start_cycle"] == 0 and row["end_cycle"] == 12005 and
            row["status"] == "paused", "witness reset-origin bounds differ")
    marker = load_json(ROOT / row["paused"]["path"])
    require(marker["responses"] == current["records"] and
            marker["completed_tokens"] == 0, "witness progress differs")
    result = {"comparisons": comparisons, "sealed_inventory_valid": True,
              "segments": len(chain), "completed_tokens": 0,
              "complete_benchmark": False}
    print(json.dumps(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("witness", type=Path)
    parser.add_argument("--validate", type=Path)
    args = parser.parse_args()
    witness = artifact_path(ROOT, str(args.witness))
    if args.validate:
        class Bindings:
            receipt = {}
        validate(witness, artifact_path(ROOT, str(args.validate)), Bindings())
        return 0
    ev = Evidence("retention-handoff")
    passed = False
    try:
        ev.receipt["scope"] = "cross-role retention only; no simulator execution"
        ev.receipt["witness_receipt"] = {
            "path": str((witness / "receipt.json").relative_to(ROOT)),
            "sha256": sha(witness / "receipt.json"),
        }
        require(ev.run("python-version", [sys.executable, "--version"], timeout=30),
                "Python version query failed")
        observation = str((ev.path / "after-handoff.json").relative_to(ROOT))
        require(ev.run("inspect", [
            sys.executable, "tests/transaction_retention.py", "--inspect",
            str((witness / "segment/transactions.u32.gz").relative_to(ROOT)),
            "--destination", observation,
        ], timeout=3600), "existing witness inspection failed; see inspect diagnostics")
        require(ev.run("validate", [
            sys.executable, "tests/retention_handoff.py", str(args.witness),
            "--validate", observation,
        ], timeout=3600), "retention/inventory validation failed; see validate diagnostics")
        ev.assertion("cross_role_retention_and_sealed_inventory", True,
                     observation=observation, complete_benchmark=False)
        passed = True
    except (ValueError, OSError, KeyError, ImportError) as error:
        ev.assertion("retention_handoff_failure", False, diagnostic=str(error))
    finally:
        ev.finish("passed" if passed else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
