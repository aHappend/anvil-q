"""Focused public-pin driver equivalence and pacing; not an acceptance gate."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from decoder_checks import decoder_case
from execution import Run
from parameters import A, A_PORTABILITY, C


def equivalence(run, banks):
    results = []
    for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
        g = replace(A, BANKS=banks, CACHE_MODE=mode, INT4_ASYM=asym)
        pair = run.parallel([
            lambda host=host: decoder_case(
                run, g, simulator="verilator", tokens=[1, 4], prefill_tokens=1,
                label="host" if host else "sv", compiled_host=host)
            for host in (False, True)])
        for field in set(pair[0]) - {"result_path", "driver"}:
            assert pair[0][field] == pair[1][field], (field, pair[0][field], pair[1][field])
        assert pair[0]["trace_sha256"] == pair[1]["trace_sha256"]
        results.append(pair)
    return {"results": results, "scope": "exact public trace/complete comparison equivalence"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", choices=("equivalence", "C", "compact"), default="equivalence")
    parser.add_argument("--banks", type=int, choices=(1, 2, 4, 8), default=8)
    args = parser.parse_args()
    run = Run("evidence/preparation/compiled-host-" + args.probe,
              "public-pin compiled decoder driver diagnostic",
              repair_of="evidence/preparation/simulation-tiering-workload-pacing/"
                        "20261029T165013Z-5b61884a4a7d/receipt.json")
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        run.versions([("verilator", "--version"), ("iverilog", "-V"), ("vvp", "-V"),
                      ("g++", "--version")])
        if args.probe == "equivalence":
            result = equivalence(run, args.banks)
        elif args.probe == "C":
            result = decoder_case(
                run, replace(C, BANKS=args.banks, CACHE_MODE=2, INT4_ASYM=1),
                simulator="verilator", tokens=[1, 4, 2, 6], prefill_tokens=2,
                label="compiled-C", compiled_host=True)
        else:
            result = decoder_case(
                run, replace(A_PORTABILITY, BANKS=args.banks, TILE_K=8, TILE_ROWS=1,
                             QUEUE_DEPTH=1, MAX_SEQ_LEN=1),
                simulator="iverilog", tokens=[0], prefill_tokens=1, label="minimal-tiles")
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    run.finish("passed", result=result)
    print(json.dumps({"result": result, "receipt": run.rel(run.path / "receipt.json")}))


if __name__ == "__main__":
    main()
