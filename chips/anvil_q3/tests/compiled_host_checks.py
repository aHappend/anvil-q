"""Focused public-pin driver equivalence and pacing; not an acceptance gate."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from decoder_checks import decoder_case
from execution import Run
from parameters import A, A_PORTABILITY, C, compatibility_geometries, startup_geometry


def equivalence(run, banks):
    results = []
    for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
        g = replace(A, BANKS=banks, CACHE_MODE=mode, INT4_ASYM=asym)
        pair = run.parallel([
            lambda host=host: decoder_case(
                run, g, simulator="verilator", tokens=[1, 4], prefill_tokens=1,
                label="host" if host else "sv", compiled_host=host, host_cycle_limit=1000000)
            for host in (False, True)])
        for field in set(pair[0]) - {"result_path", "driver"}:
            assert pair[0][field] == pair[1][field], (field, pair[0][field], pair[1][field])
        assert pair[0]["trace_sha256"] == pair[1]["trace_sha256"]
        results.append(pair)
    return {"results": results, "scope": "exact public trace/complete comparison equivalence"}


def compatibility_equivalence(run):
    legacy = next(g for g in compatibility_geometries()
                  if g.PROFILE == 2 and g.CACHE_MODE == 1 and g.CACHE_BLOCK == 64)
    cases = ((startup_geometry(1), [1, 4], 1, 0),
             (legacy, [1, 2, 1, 2, 1, 2, 1], 4, 1))
    jobs = []
    for g, tokens, prefill, first_new in cases:
        for host in (False, True):
            jobs.append(lambda g=g, t=tokens, p=prefill, n=first_new, h=host: decoder_case(
                run, g, simulator="verilator", tokens=t, prefill_tokens=p, first_new=n,
                label="compat-host" if h else "compat-sv", compiled_host=h))
    results = run.parallel(jobs)
    for sv, host in zip(results[::2], results[1::2]):
        assert set(sv) == set(host)
        for field in set(sv) - {"result_path", "driver"}:
            assert sv[field] == host[field], (field, sv[field], host[field])
    return {"results": results,
            "scope": "PROFILE1 implicit startup and seven-token PROFILE2 legacy-C64 "
                     "complete numerical/public-trace equivalence; not the compatibility matrix"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", choices=("equivalence", "compatibility-equivalence", "C",
                                          "C-symmetric", "compact"),
                        default="equivalence")
    parser.add_argument("--banks", type=int, choices=(1, 2, 4, 8), default=8)
    parser.add_argument("--tokens", type=int, choices=(1, 4), default=4,
                        help="C diagnostic prefix length; four tokens by default")
    parser.add_argument("--mode", type=int, choices=(0, 1, 2), default=0,
                        help="compact portability cache mode")
    parser.add_argument("--asymmetric", type=int, choices=(0, 1), default=0)
    parser.add_argument("--repair-of", help="retained diagnostic receipt repaired by this run")
    args = parser.parse_args()
    run = Run("evidence/preparation/compiled-host-" + args.probe,
              "public-pin compiled decoder driver diagnostic",
              repair_of=args.repair_of or (
                         "evidence/check-behavior/20261029T201448Z-48169afcddba/"
                         "tool-0190/receipt.json" if args.probe == "compatibility-equivalence" else
                         "evidence/preparation/compiled-host-equivalence/"
                         "20261029T192252Z-3b6ff5174f03/receipt.json"))
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        run.versions([("verilator", "--version"), ("iverilog", "-V"), ("vvp", "-V"),
                      ("g++", "--version")])
        if args.probe == "equivalence":
            result = equivalence(run, args.banks)
        elif args.probe == "compatibility-equivalence":
            result = compatibility_equivalence(run)
        elif args.probe in ("C", "C-symmetric"):
            result = decoder_case(
                run, replace(C, BANKS=args.banks, CACHE_MODE=2,
                             INT4_ASYM=int(args.probe == "C")),
                simulator="verilator", tokens=[1, 4, 2, 6][:args.tokens],
                prefill_tokens=min(2, args.tokens),
                label="compiled-C", compiled_host=True)
        else:
            result = decoder_case(
                run, replace(A_PORTABILITY, BANKS=args.banks, TILE_K=8, TILE_ROWS=1,
                             QUEUE_DEPTH=1, MAX_SEQ_LEN=1,
                             CACHE_MODE=args.mode, INT4_ASYM=args.asymmetric),
                simulator="iverilog", tokens=[0], prefill_tokens=1, label="minimal-tiles")
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    run.finish("passed", result=result)
    print(json.dumps({"status": "passed", "receipt": run.rel(run.path / "receipt.json")}))


if __name__ == "__main__":
    main()
