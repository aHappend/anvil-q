"""Public-pin prefetch response association, boundary and drain experiment."""

import argparse
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import Experiment


CELLS = {"singleton": (2, 1, 1), "default": (4, 8, 3), "maximum": (8, 16, 16)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cell", choices=CELLS, default="default")
    parser.add_argument("--seed", choices=(11, 29, 101), type=int, default=11)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    names = ["rtl/anvil_q2_ht_ddr_prefetcher.sv", "tests/prefetch_tb.sv",
             "tests/prefetch_check.py", "tests/retention.py"]
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    try:
        for tool, flag in (("python3", "--version"), ("iverilog", "-V"), ("vvp", "-V")):
            experiment.run([tool, flag], tool + "-version")
        slots, outstanding, queue = CELLS[args.cell]
        experiment.receipt["configuration"] = {
            "cell": args.cell, "TILE_SLOTS": slots, "READ_OUTSTANDING": outstanding,
            "QUEUE_DEPTH": queue, "seed": args.seed,
            "scope": "read-prefetch public interface, not mixed read/write system coverage"}
        binary = str(args.output / "prefetch.vvp")
        experiment.run(["iverilog", "-g2012", "-Wall", "-s", "prefetch_tb",
                        "-Pprefetch_tb.TILE_SLOTS=" + str(slots),
                        "-Pprefetch_tb.READ_OUTSTANDING=" + str(outstanding),
                        "-Pprefetch_tb.QUEUE_DEPTH=" + str(queue), "-o", binary] +
                       [str(args.output / "sources" / name) for name in names[:2]], "compile")
        text = experiment.run(["vvp", binary, "+seed=" + str(args.seed)], "simulate")
        if not all(label in text for label in (
                "PREFETCH_CHECKED ", "PREFETCH_COVERAGE ", "PREFETCH_STREAM ")):
            raise RuntimeError("missing executed prefetch comparisons/coverage")
        experiment.receipt["comparison_summary"] = text.strip()
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
