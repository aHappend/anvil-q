"""Legal parameter elaboration and executable illegal-parameter diagnostics.

Legal rows establish elaboration only, not functional coverage. Illegal cases
must compile successfully before the literal PARAMETER ERROR and nonzero vvp
exit are accepted. Zero-width/reversed-select compiler failures do not pass.
"""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import Evidence, ROOT, rel
from structure import COMPACT


MINIMUM = dict(NUM_LAYERS=1, HIDDEN_SIZE=8, INTERMEDIATE_SIZE=8,
               NUM_Q_HEADS=1, KV_LORA_RANK=1, QK_NOPE_HEAD_DIM=1,
               QK_ROPE_HEAD_DIM=2, V_HEAD_DIM=1, ROUTED_EXPERTS=1,
               TOP_K=1, SHARED_EXPERTS=2, MOE_INTERMEDIATE_SIZE=8,
               FIRST_DENSE_LAYERS=0, VOCAB_SIZE=4, MAX_SEQ_LEN=1,
               BANKS=1, QUEUE_DEPTH=1, TILE_K=8, TILE_ROWS=1)


def matrix():
    legal = [
        ("minimum", MINIMUM),
        ("minimum_dense", MINIMUM | dict(FIRST_DENSE_LAYERS=1)),
        ("compact_banks2_queue3", COMPACT),
        ("banks4_queue16", COMPACT | dict(BANKS=4, QUEUE_DEPTH=16)),
        ("banks8_queue1", COMPACT | dict(BANKS=8, QUEUE_DEPTH=1)),
        ("topk_equals_experts", COMPACT | dict(ROUTED_EXPERTS=6)),
        ("production_defaults", {}),
        ("maximum_geometry", dict(
            NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
            NUM_Q_HEADS=16, KV_LORA_RANK=512, QK_NOPE_HEAD_DIM=128,
            QK_ROPE_HEAD_DIM=64, V_HEAD_DIM=128, ROUTED_EXPERTS=64, TOP_K=6,
            SHARED_EXPERTS=2, MOE_INTERMEDIATE_SIZE=1408, FIRST_DENSE_LAYERS=36,
            VOCAB_SIZE=151936, MAX_SEQ_LEN=32768, BANKS=8, QUEUE_DEPTH=16,
            TILE_K=128, TILE_ROWS=8)),
    ]
    illegal_values = {
        "MODEL_MODE": [-1, 2], "NUM_LAYERS": [0, 37],
        "HIDDEN_SIZE": [0, 7, 2056], "INTERMEDIATE_SIZE": [0, 11016],
        "NUM_Q_HEADS": [0, 17], "KV_LORA_RANK": [0, 513],
        "QK_NOPE_HEAD_DIM": [0, 129], "QK_ROPE_HEAD_DIM": [0, 3, 66],
        "V_HEAD_DIM": [0, 129], "ROUTED_EXPERTS": [0, 65], "TOP_K": [0, 7],
        "SHARED_EXPERTS": [0, 1, 3], "MOE_INTERMEDIATE_SIZE": [0, 1416],
        "FIRST_DENSE_LAYERS": [-1, 3], "VOCAB_SIZE": [0, 3, 151937],
        "MAX_SEQ_LEN": [0, 32769], "BANKS": [0, 3], "QUEUE_DEPTH": [0, 17],
        "TILE_K": [0, 7, 136], "TILE_ROWS": [0, 9],
    }
    illegal = [(f"reject_{name}_{value}", COMPACT | {name: value})
               for name, values in illegal_values.items() for value in values]
    illegal.append(("reject_topk_exceeds_experts", COMPACT | dict(ROUTED_EXPERTS=5, TOP_K=6)))
    return legal, illegal


def elaborate(evidence):
    legal, illegal = matrix()
    sources = sorted(ROOT.glob("anvil_q3_reference/rtl/*.sv")) + sorted(ROOT.glob("rtl/*.sv"))
    ledger = []
    for name, parameters in legal+illegal:
        executable = evidence.path / (name+".vvp")
        argv = ["iverilog", "-g2012", "-Wall", "-s", "anvil_d1_top", "-o", rel(executable)]
        for parameter, value in parameters.items():
            argv.extend(["-P", f"anvil_d1_top.{parameter}={value}"])
        argv.extend(rel(path) for path in sources)
        evidence.run(name+"-compile", argv, ["iverilog", "-V"])
        rejecting = name.startswith("reject_")
        if rejecting:
            output = evidence.run(name+"-diagnostic", ["vvp", rel(executable)], ["vvp", "-V"],
                                  expected_exit_codes=(1,))
            if "PARAMETER ERROR" not in output.read_text():
                raise AssertionError(f"nonzero exit without declared parameter diagnostic: {name}")
        ledger.append(dict(case=name, parameters=parameters,
                           result="explicit rejection" if rejecting else "elaborated"))
        executable.unlink()
        print(f"ELABORATION {name} {ledger[-1]['result']}", flush=True)
    (evidence.path / "elaboration.json").write_text(json.dumps(ledger, indent=2)+"\n")
    return dict(legal_elaborations=len(legal), explicit_illegal_rejections=len(illegal),
                functional_claim=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    evidence = Evidence("parameter-elaboration", args.repair_of)
    try:
        summary = elaborate(evidence)
        evidence.finish("passed", **summary)
        print(json.dumps(summary))
    except Exception as exc:
        evidence.finish("failed", error=str(exc))
        print(str(exc), file=sys.stderr)
        print(rel(evidence.path / "receipt.json"), file=sys.stderr)
        return 1
    print(rel(evidence.path / "receipt.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
