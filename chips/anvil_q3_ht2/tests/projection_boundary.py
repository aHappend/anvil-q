"""Legal minimum GQA projection against parent-compatible packed image bytes."""

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from receipts import ROOT, execute, new_run, relative


def run_projection_boundary(run):
    executable = run / "projection-boundary.vvp"
    sources = [relative(path) for directory in ("anvil_q3_ht_reference/rtl", "rtl")
               for path in sorted((ROOT / directory).glob("*.sv"))]
    execute(run, "projection-boundary-compile", [
        "iverilog", "-g2012", "-Wall", "-s", "projection_boundary_tb",
        "-o", relative(executable), *sources, "tests/projection_boundary_tb.sv"],
        ["iverilog", "-V"])
    result = execute(run, "projection-boundary-simulate",
                     ["vvp", relative(executable)], ["vvp", "-V"])
    observations = [json.loads(line.removeprefix("RESULT ")) for line in
                    (result / "stdout.txt").read_text().splitlines()
                    if line.startswith("RESULT ")]
    if len(observations) != 1 or observations[0]["writes"] != 2 or (
            observations[0]["activation_reads"] != 16 or
            observations[0]["qweight_reads"] != 16 or
            not 0 < observations[0]["cycles"] < 100000):
        raise AssertionError("incomplete minimum-GQA projection observations")
    return {"observed": observations[0], "receipt": relative(result / "receipt.json"),
            "expected_q16_per_row": 1024,
            "oracle": "16 exact products of (1-0)*2^-10*1; two real output rows"}


if __name__ == "__main__":
    import argparse
    from verify import enter_tier

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    enter_tier()
    run = new_run("projection-minimum-gqa", preparation=True, repair_of=args.repair_of)
    print(f"Projection boundary evidence: {relative(run)}", flush=True)
    print(json.dumps(run_projection_boundary(run)), flush=True)
