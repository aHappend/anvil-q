"""Read-only measured scheduling diagnostic; never an acceptance substitute."""

import hashlib
import json
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parent.parent
    inputs, simulations = [], []
    for argument in sys.argv[1:]:
        path = Path(argument)
        if (path.is_absolute() or ".." in path.parts or path.name != "receipt.json"
                or path.parts[:2] != ("evidence", "preparation")):
            raise ValueError("Scheduling inputs must be project preparation receipts")
        raw = (root / path).read_bytes()
        receipt = json.loads(raw)
        if receipt["exit_code"] != 0 or not receipt["sources_unchanged"]:
            raise ValueError(f"Unsettled or changed-source scheduling input: {path}")
        for source, expected in receipt["source_sha256"].items():
            if source.startswith("rtl/"):
                actual = hashlib.sha256((root / source).read_bytes()).hexdigest()
                if actual != expected:
                    raise ValueError(f"Design changed since measured execution: {source}")
        inputs.append({"receipt": argument, "sha256": hashlib.sha256(raw).hexdigest(),
                       "source_sha256": receipt["source_sha256"]})
        for row in receipt["coverage"]:
            if row["status"] != "passed":
                raise ValueError(f"Incomplete scheduling input: {row['name']}")
            child = row["simulation_receipt"]
            if (child["exit_code"] != 0 or child["timed_out"]
                    or not child["child_settled"]):
                raise ValueError("Unsettled simulation in scheduling input")
            simulations.append({
                "name": row["name"], "duration_s": child["duration_s"],
                "argv": child["argv"], "stdout": child["stdout"],
                "actual_comparisons": row["actual_comparisons"],
            })
    if not simulations or len({row["name"] for row in simulations}) != len(simulations):
        raise ValueError("Scheduling inputs must contain distinct measured cases")
    total = sum(row["duration_s"] for row in simulations)
    print(json.dumps({
        "scope": "Observed sequential submatrix, excluding all compilation and other L1 suites",
        "acceptance_evidence": False,
        "inputs": inputs, "simulations": simulations, "simulation_seconds": total,
        "patrol_check_seconds": 2700,
        "observed_submatrix_exceeds_patrol": total > 2700,
        "limits": "Historical measurements, not an irreducible runtime lower bound. "
                  "Parallel execution or further source-bound compilation/simulation "
                  "optimization has not been measured. No admitted command, watchdog, "
                  "seed, assertion or coverage requirement is changed.",
    }, indent=2))


if __name__ == "__main__":
    main()
