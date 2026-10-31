"""Focused repair diagnostics, not a replacement for the admitted mutation gate."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, Run, write_json
from mutation_checks import (FAILED_RECEIPT, MUTATIONS, REQUIRED_CATEGORIES,
                             assert_required_coverage, control_case, mutation_case)


def inventory_sensitivity():
    names = [spec[0] for spec in MUTATIONS]
    assert_required_coverage(names)
    if len(set(names)) != len(names):
        raise AssertionError("duplicate mutation names")
    rejected = []
    for category, required in REQUIRED_CATEGORIES.items():
        try:
            assert_required_coverage(set(names) - required)
        except AssertionError:
            rejected.append(category)
        else:
            raise AssertionError("missing category accepted: " + category)
    for name, filename, before, after, _, _ in MUTATIONS:
        text = (ROOT / "rtl" / filename).read_text()
        if text.count(before) != 1 or before == after:
            raise AssertionError("nonunique or ineffective target: " + name)
    return {"required_categories": len(REQUIRED_CATEGORIES),
            "inventory_entries": len(names), "omitted_categories_rejected": rejected,
            "all_targets_unique": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--names", nargs="+", required=True,
                        choices=[spec[0] for spec in MUTATIONS])
    parser.add_argument("--repair-of", default=FAILED_RECEIPT)
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run = Run("evidence/preparation/mutation-repair-" + stamp,
              "focused functional mutation repair", repair_of=args.repair_of)
    print(run.rel(run.path / "receipt.json"), flush=True)
    results, controls, seen = [], [], {}
    try:
        run.versions([("python3", "--version"), ("verilator", "--version"),
                      ("g++", "--version"), ("make", "--version")])
        inventory = inventory_sensitivity()
        for spec in MUTATIONS:
            if spec[0] not in args.names:
                continue
            key = spec[-2], spec[-1]
            if key not in seen:
                control = Run(run.rel(run.path / ("control-" + spec[0])),
                              "unmodified mutation control", repair_of=FAILED_RECEIPT)
                try:
                    result = control_case(control, spec)
                except Exception as exc:
                    control.finish("failed", diagnosis=str(exc))
                    raise
                control.finish("passed", result=result)
                seen[key] = control.rel(control.path / "receipt.json")
                controls.append({"receipt": seen[key], "result": result})
            print("mutation repair: " + spec[0], flush=True)
            result = mutation_case(run, spec)
            result["control_receipt"] = seen[key]
            results.append(result)
            write_json(run.path / "repair-results.json",
                       {"inventory": inventory, "controls": controls, "kills": results})
        if {row["name"] for row in results} != set(args.names):
            raise AssertionError("incomplete selected repair diagnostics")
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc), controls=controls, kills=results)
        raise
    run.finish("passed", controls=controls, kills=results, inventory=inventory)


if __name__ == "__main__":
    main()
