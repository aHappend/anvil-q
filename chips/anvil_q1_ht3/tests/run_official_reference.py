"""Bounded tokenizer/scoring self-tests and an optional real FP64 model step.

These are reference diagnostics, not RTL benchmark results.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import unicodedata

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, hashes, relative, remaining, timestamp
from official_reference import Checkpoint, QwenFP64, Tokenizer, perplexity, pieces, scored_position
from run_benchmarks import prepare


def rejection(function):
    try:
        function()
    except AssertionError:
        return
    raise AssertionError("independent score sensitivity failed to reject injected defect")


def run(output, model_step):
    works, bindings, failures = prepare(output)
    if failures:
        raise AssertionError(f"official acquisition failed: {failures}")
    tokenizer = Tokenizer(ROOT/bindings["tokenizer.json"]["path"])
    if tokenizer.encode("Hello, world!") != [9707, 11, 1879, 0]:
        raise AssertionError("directed canonical Qwen token IDs mismatch")
    if tokenizer.encode("<|im_start|>") != [151644]:
        raise AssertionError("official added-token ID mismatch")
    for text in (" Hello\n\n", "a  b", "Janet’s ducks", "cafe\u0301", "\t3.14\r\n", "中文 Qwen"):
        if tokenizer.decode(tokenizer.encode(text)) != unicodedata.normalize("NFC", text):
            raise AssertionError("official Unicode/BPE reconstruction mismatch")
    if list(pieces("a  b")) != ["a", " ", " b"]:
        raise AssertionError("whitespace negative-lookahead tokenization mismatch")
    actual = [1000, 1000+math.log(3)]
    row = scored_position(actual, actual, 1)
    if not math.isclose(row["nll"], math.log(4/3), rel_tol=0, abs_tol=2e-13):
        raise AssertionError("FP64 shifted-target log-sum-exp differs from analytic result")
    positions = [dict(position=i, **row) for i in range(16, 144)]
    ppl = perplexity(positions)
    if not math.isclose(ppl["perplexity"], 4/3, rel_tol=0, abs_tol=2e-13):
        raise AssertionError("PPL denominator/padding mismatch")
    rejection(lambda: scored_position([1, 0], [0, 1], 1))
    rejection(lambda: scored_position([0, 0], [0, 1], 1))
    rejection(lambda: perplexity(positions[:-1]))
    rejection(lambda: perplexity([dict(p, position=0) for p in positions]))
    result = dict(status="passed", tokenizer_cases=9, analytic_scored_positions=128,
                  score_defects_rejected=4, official_workloads=len(works),
                  reference_only=True)
    if model_step:
        checkpoint = Checkpoint(ROOT/bindings["model.safetensors"]["path"])
        config = json.loads((ROOT/bindings["config.json"]["path"]).read_text())
        token = works[0]["token_ids"][0]
        observations = []
        for represented in (False, True):
            oracle = QwenFP64(config, checkpoint, represented)
            logits = oracle.step(token)
            observations.append(dict(represented_image=represented, token=token,
                                     shape=list(logits.shape),
                                     logits_sha256=hashlib.sha256(logits.tobytes()).hexdigest(),
                                     greedy_token=int(logits.argmax()),
                                     min_logit=float(logits.min()), max_logit=float(logits.max())))
        result["official_fp64_steps"] = observations
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--model-step", action="store_true")
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_official_reference.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    try:
        result = run(output, args.model_step)
    except (OSError, ValueError, AssertionError, KeyError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    with (output/"result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"] != "passed"),
                   timed_out=remaining() <= 0, result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
