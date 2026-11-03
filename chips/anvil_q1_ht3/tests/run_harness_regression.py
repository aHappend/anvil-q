"""Synthetic reclamation/allocation/retry checks, not hardware acceptance."""

import argparse
import ast
import json
import math
import os
from pathlib import Path
import sys
import time
import uuid
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, hashes, relative, remaining, timestamp
from retention import artifacts_intact, digest, execution_logs_intact
from run_mutations import trial
from official_reference import QwenFP64
from official_scoring import likelihood, restore_state, save_state
from verify import MINIMUM_ALLOCATIONS, child, schedule
import numpy as np


def run(output):
    assertions = 0
    names = ("netlist.json", "synthesis.stdout.txt", "synthesis.stderr.txt",
             "executable", "driver.cpp")
    artifacts = {}
    for name in names:
        path = output / name
        path.write_text(f"synthetic {name}\n")
        artifacts[relative(path)] = digest(path)
    record = dict(stdout=relative(output/names[1]), stderr=relative(output/names[2]),
                  artifact_sha256=artifacts)
    if not artifacts_intact(artifacts) or not execution_logs_intact(record):
        raise AssertionError("complete synthetic artifacts rejected")
    assertions += 1
    for name in names:
        path = output/name
        original = path.read_bytes()
        # Synthetic candidates only; never remove retained execution evidence.
        path.unlink()
        if artifacts_intact(artifacts):
            raise AssertionError(f"reclaimed {name} accepted")
        if "stderr" in name or "stdout" in name:
            if execution_logs_intact(record):
                raise AssertionError("reclaimed raw log accepted")
        path.write_bytes(original)
        assertions += 1
    omitted = {p: sha for p, sha in artifacts.items() if not p.endswith("driver.cpp")}
    if artifacts_intact(omitted, artifacts):
        raise AssertionError("omitted required driver accepted")
    assertions += 1
    previous = os.environ.get("HT3_CHECK_DEADLINE")
    try:
        deadline = time.time()+70
        os.environ["HT3_CHECK_DEADLINE"] = str(deadline)
        for identifier in ("integrated_geometry", "parameters", "mutations",
                           "stream_checkpoint", "benchmarks"):
            with patch("verify.execute", side_effect=AssertionError("must not launch")):
                row = child(identifier, [f"tests/run_{identifier}.py"], output,
                            budget=1800, reserve=30,
                            minimum=MINIMUM_ALLOCATIONS[identifier])
            if (row["status"] != "not_started"
                    or row["failure_kind"] != "execution_budget_unstarted"
                    or float(os.environ["HT3_CHECK_DEADLINE"]) != deadline):
                raise AssertionError("insufficient allocation launched or reset the deadline")
            assertions += 1
        os.environ["HT3_CHECK_DEADLINE"] = str(time.time()+600)

        def sufficient(argv, parent, identifier, version):
            allocation = float(os.environ["HT3_CHECK_DEADLINE"])-time.time()
            if not 350 < allocation <= 360:
                raise AssertionError("useful cold compilation allocation not preserved")
            directory = ROOT/argv[argv.index("--output")+1]
            directory.mkdir()
            (directory/"result.json").write_text(json.dumps(dict(status="passed")))

        with patch("verify.execute", side_effect=sufficient):
            row = child("synthetic-useful", ["tests/not-hardware.py"], output,
                        budget=360, reserve=30, minimum=300)
        if row["status"] != "passed":
            raise AssertionError("useful allocation rejected")
        assertions += 1
    finally:
        if previous is None:
            os.environ.pop("HT3_CHECK_DEADLINE", None)
        else:
            os.environ["HT3_CHECK_DEADLINE"] = previous
    seen = []

    def failed_baseline(argv, parent, stem, version, root):
        if stem in seen:
            raise AssertionError("retry would collide with immutable prior outputs")
        seen.append(stem)
        directory = root/argv[argv.index("--output")+1]
        directory.mkdir(parents=True)
        (directory/"case-result.json").write_text(json.dumps(dict(status="failed")))
        (directory/"case.receipt.json").write_text(json.dumps(dict(timed_out=False)))
        raise RuntimeError("deliberate synthetic baseline rejection")

    disposable = output/f"synthetic-bundle-{uuid.uuid4().hex[:12]}"
    disposable.mkdir()
    with patch("run_mutations.execute", side_effect=failed_baseline):
        for _ in range(2):
            _, result, error = trial(output, disposable, "baseline-epilogue", "epilogue")
            if result["status"] != "failed" or error is None:
                raise AssertionError("failed baseline became success")
            assertions += 1
    if len(set(seen)) != 2:
        raise AssertionError("failed baseline retry names not unique")
    assertions += 1
    if len({j[0] for j in schedule()}) != len(schedule()):
        raise AssertionError("duplicate mandatory job")
    assertions += 1
    for path in (ROOT/"tests").glob("*.py"):
        ast.parse(path.read_text(), filename=relative(path))
    config = dict(hidden_size=64, num_attention_heads=1, num_key_value_heads=1,
                  num_hidden_layers=1, rope_theta=1000000, hidden_act="silu",
                  use_sliding_window=False, tie_word_embeddings=True,
                  vocab_size=3, max_position_embeddings=8, rms_norm_eps=1e-6)
    rng = np.random.default_rng(2026)
    weights = {"model.embed_tokens.weight": rng.normal(0, .1, (3, 64)),
               "model.norm.weight": np.ones(64)}
    prefix = "model.layers.0."
    for kind in ("input_layernorm", "post_attention_layernorm"):
        weights[prefix+kind+".weight"] = np.ones(64)
    for kind in ("q", "k", "v", "o"):
        weights[prefix+f"self_attn.{kind}_proj.weight"] = rng.normal(0, .01, (64, 64))
        if kind != "o":
            weights[prefix+f"self_attn.{kind}_proj.bias"] = np.zeros(64)
    for kind in ("gate", "up", "down"):
        weights[prefix+f"mlp.{kind}_proj.weight"] = rng.normal(
            0, .01, (64, 8) if kind == "down" else (8, 64))

    class SyntheticWeights:
        def tensor(self, name, selection=None):
            return weights[name] if selection is None else weights[name][selection]

    checkpoint = SyntheticWeights()
    full = {name: QwenFP64(config, checkpoint, name == "represented_image")
            for name in ("native", "represented_image")}
    reduced = {name: QwenFP64(config, checkpoint, name == "represented_image")
               for name in full}
    for name in full:
        full[name].step(0)
        if reduced[name].step(0, emit_logits=False) is not None:
            raise AssertionError("unscored step unexpectedly produced logits")
    state = output/"synthetic-reference-state.npz"
    save_state(state, reduced)
    restored = {name: QwenFP64(config, checkpoint, name == "represented_image")
                for name in full}
    restore_state(state, restored, 1)
    for name in full:
        expected = full[name].step(1)
        actual = restored[name].step(1)
        if not np.array_equal(actual, expected):
            raise AssertionError("restored FP64 state or omitted prefix logits changed results")
        assertions += 1
    try:
        restore_state(state, restored, 2)
    except AssertionError:
        assertions += 1
    else:
        raise AssertionError("wrong reference position accepted")
    nll = likelihood(np.asarray([1000, 1000+math.log(3)], dtype=np.float64), 1)
    if not math.isclose(nll, math.log(4/3), rel_tol=0, abs_tol=2e-13):
        raise AssertionError("persistent score likelihood differs from analytic FP64 result")
    assertions += 1
    return dict(status="passed", kind="synthetic-harness-regression",
                assertions=assertions, cases=list(names),
                scope="cache/allocation/retry and synthetic FP64 continuation; not RTL acceptance")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_harness_regression.py", *sys.argv[1:]],
                   cwd=".", start=timestamp(), timeout=remaining(),
                   source_sha256=hashes(), tool_version=sys.version)
    result = run(output)
    (output/"result.json").write_text(json.dumps(result, indent=2))
    receipt.update(exit=0, timed_out=False, end=timestamp(),
                   result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
