"""Reconfigure four profile sequences in one compiled DUT without resetting it."""

import argparse
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from descriptors import official, PINS
from execution import Experiment
from system_matrix import compile_top
from transformer_reference import make_fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    args = parser.parse_args()
    experiment = Experiment("switching", args.preparation)
    error = None
    try:
        profiles = [
            ("qwen", official("qwen"), True, 1),
            ("deepseek", official("deepseek"), True, 0),
            ("llama-ratio3", None, False, 0),
            ("qwen-return", official("qwen"), True, 1),
        ]
        directories, results = [], []
        experiment.receipt["official_config_sha256"] = PINS
        experiment.receipt["cases"] = results
        for generation, (name, model, bias, weight_format) in enumerate(profiles, 1):
            ratio = model["num_attention_heads"]//model["num_key_value_heads"] if model else 3
            theta = model["rope_theta"] if model else 500000
            identity = hashlib.sha256(name.encode()).hexdigest()[:12]
            directory = experiment.directory / f"profile-{generation}-{identity}"
            directory.mkdir()
            options = dict(seed=17, heads=ratio, kv_heads=1, dimension=2,
                           layers=3, tokens=4, intermediate=5, vocabulary=17,
                           bias=bias, banks=16, page_tokens=2, theta_value=theta,
                           weight_format=weight_format, group_size=128, generation=generation)
            geometry = make_fixture(directory, **options)
            geometry.update(profile=name, generation=generation,
                            scope="compact switching; not full-checkpoint accuracy",
                            fixture_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                            for p in directory.glob("*.txt")})
            directories.append(directory)
            results.append(geometry)
        experiment.receipt["tool_version"] = experiment.run(["verilator", "--version"], "version")
        binary = compile_top(experiment)
        output = experiment.run([experiment.rel(binary), *map(experiment.rel, directories)],
                                "simulation")
        if output.count("SUMMARY top tokens=4 logits=68 ") != 4 or (
                "SUMMARY switching sequences=4 reset_count=1" not in output):
            raise AssertionError("missing no-reset profile numerical comparisons")
        experiment.prune_objects(binary.parent)
    except (RuntimeError, ValueError, AssertionError, KeyError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
