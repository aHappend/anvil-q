"""Internal clean-copy worker; the mandatory public entry remains verify.py."""

import argparse
from dataclasses import replace
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decoder_checks import decoder_case
from execution import Run
from parameters import A, defaults, legal
from prerequisites import configuration
from structure_checks import structure


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--bounded-smoke", action="store_true")
    args = parser.parse_args()
    run = Run(args.output, "clean-source-reproduction")
    try:
        run.versions([("iverilog", "-V"), ("vvp", "-V"), ("verilator", "--version")])
        config = configuration()
        selected = ([("official-default", defaults(p), True) for p in (1, 2, 3)] +
                    [("unchanged-A", replace(A, CACHE_MODE=m, INT4_ASYM=a), True)
                     for m, a in ((0, 0), (1, 0), (2, 0), (2, 1))]
                    if args.bounded_smoke else None)
        parameters = structure(run, simulators=("iverilog",), include_negative=False,
                               include_timing_lint=False, selected_cases=selected)
        results = []
        for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
            g = replace(A, BANKS=8, CACHE_MODE=mode, INT4_ASYM=asym)
            if not legal(g) or g.NUM_KV_HEADS * g.HEAD_DIM != 2:
                raise AssertionError("A geometry changed")
            results.append(decoder_case(run, g, seed=17,
                                        simulator="verilator",
                                        tokens=[1, 4] if args.bounded_smoke else None))
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    run.finish("passed", result={"configuration": config, "parameters": parameters, "decoder": results,
                                "bounded_smoke": args.bounded_smoke})


if __name__ == "__main__":
    main()
