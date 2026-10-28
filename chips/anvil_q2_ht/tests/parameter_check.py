"""Legal elaboration and explicit illegal-top-parameter rejection, not numerical coverage."""

import argparse
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import Experiment


BASE = {"NUM_LAYERS": 1, "HIDDEN_SIZE": 8, "INTERMEDIATE_SIZE": 8,
        "NUM_Q_HEADS": 1, "NUM_KV_HEADS": 1, "HEAD_DIM": 8, "GROUP_SIZE": 1,
        "VOCAB_SIZE": 1, "MAX_SEQ_LEN": 1, "CACHE_BLOCK": 1, "HOT_BLOCKS": 1,
        "QUEUE_DEPTH": 1, "TILE_SLOTS": 2, "READ_OUTSTANDING": 1}
LEGAL = {
    "singleton": BASE,
    "nonpower": {**BASE, "HIDDEN_SIZE": 24, "INTERMEDIATE_SIZE": 24,
                 "NUM_Q_HEADS": 3, "HOT_BLOCKS": 3, "QUEUE_DEPTH": 3},
    "block16": {**BASE, "HIDDEN_SIZE": 16, "INTERMEDIATE_SIZE": 16,
                "HEAD_DIM": 16, "CACHE_BLOCK": 16, "GROUP_SIZE": 8,
                "TILE_SLOTS": 4, "READ_OUTSTANDING": 8},
    "default": {},
}
ILLEGAL = [(name + "-zero", {name: 0}) for name in BASE]
ILLEGAL += [
    ("layers-high", {"NUM_LAYERS": 29}), ("hidden-high", {"HIDDEN_SIZE": 1544}),
    ("intermediate-high", {"INTERMEDIATE_SIZE": 8968}), ("query-high", {"NUM_Q_HEADS": 17}),
    ("kv-high", {"NUM_KV_HEADS": 3}), ("head-odd", {"HEAD_DIM": 7}),
    ("vocabulary-high", {"VOCAB_SIZE": 151937}), ("sequence-high", {"MAX_SEQ_LEN": 32769}),
    ("group-nonpower", {"GROUP_SIZE": 3}), ("group-not-divisor", {"GROUP_SIZE": 16}),
    ("group-high", {"GROUP_SIZE": 256}), ("block-nonpower", {"CACHE_BLOCK": 3}),
    ("block-not-divisor", {"CACHE_BLOCK": 16}), ("block-high", {"CACHE_BLOCK": 256}),
    ("hot-high", {"HOT_BLOCKS": 65}), ("queue-high", {"QUEUE_DEPTH": 17}),
    ("slots-one", {"TILE_SLOTS": 1}), ("slots-high", {"TILE_SLOTS": 9}),
    ("outstanding-high", {"READ_OUTSTANDING": 17}), ("banks", {"BANKS": 4}),
    ("lanes", {"LANES_PER_BANK": 4}), ("data-width", {"DDR_DATA_WIDTH": 256}),
    ("gqa-divisibility", {"HIDDEN_SIZE": 24, "NUM_Q_HEADS": 3, "NUM_KV_HEADS": 2}),
    ("hidden-relation", {"HIDDEN_SIZE": 16}),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    rtl = sorted(str(path.relative_to(root)) for path in (root / "rtl").glob("*.sv"))
    experiment = Experiment(root, args.output, sys.orig_argv,
                            rtl + ["tests/parameter_check.py", "tests/retention.py"])
    ledger = []
    experiment.receipt["cells"] = ledger
    try:
        for tool, flag in (("iverilog", "-V"), ("vvp", "-V")):
            experiment.run([tool, flag], tool + "-version")
        sources = [str(args.output / "sources" / name) for name in rtl]
        for legal, cells in ((True, LEGAL.items()), (False, ILLEGAL)):
            for name, overrides in cells:
                parameters = overrides if legal else {**BASE, **overrides}
                binary = str(args.output / (name + ".vvp"))
                argv = ["iverilog", "-g2012", "-Wall", "-s", "anvil_q2_ht_top", "-o", binary]
                argv += [f"-Panvil_q2_ht_top.{key}={value}" for key, value in parameters.items()]
                experiment.run(argv + sources, name + "-compile")
                record = {"cell": name, "parameters": parameters, "legal": legal,
                          "elaborated": True, "functional_coverage": False}
                ledger.append(record)
                if not legal:
                    text = experiment.run(["vvp", binary], name + "-reject", allow_mismatch=True)
                    command = experiment.receipt["commands"][-1]
                    diagnostic = "ANVIL_Q2_HT PARAMETER ERROR: top geometry or production width"
                    if command["exit"] == 0 or text.count(diagnostic) != 1:
                        raise RuntimeError("missing intended parameter diagnostic: " + name)
                    record["explicit_rejection"] = True
        experiment.receipt["summary"] = {"legal_elaborations": len(LEGAL),
                                         "explicit_illegal_rejections": len(ILLEGAL),
                                         "functional_cells": 0}
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
