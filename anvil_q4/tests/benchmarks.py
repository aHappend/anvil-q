"""Source-bound five-domain cross-generation, bank and profile benchmarks."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from descriptors import official, PINS
from execution import Experiment, ROOT
from legacy_reference import make_fixture as legacy_fixture
from system_matrix import compile_top
from transformer_reference import make_fixture as native_fixture


DOMAINS = ("tensor/dequant/GEMV", "RMSNorm/RoPE", "GQA/softmax/KV",
           "SwiGLU/residual", "complete-token/prefill/decode")


def parse_metrics(output, geometry):
    rows = []
    summary = next(line for line in output.splitlines() if line.startswith("SUMMARY top "))
    totals = {key: int(value) for key, value in re.findall(r"(\w+)=(\d+)", summary)}
    for line in output.splitlines():
        if not line.startswith("METRIC "):
            continue
        metric = {key: int(value) for key, value in re.findall(r"(\w+)=(\d+)", line)}
        index = metric.pop("domain")
        if index != len(rows) or not metric["comparisons"] or not metric["observation_span_cycles"]:
            raise AssertionError("missing measured domain correctness or traffic span")
        metric["domain"] = DOMAINS[index]
        rows.append(metric)
    if len(rows) != 5 or totals["tokens"] != geometry["tokens"] or (
            totals["logits"] != geometry["tokens"]*geometry["vocabulary"]):
        raise AssertionError("missing benchmark tokens/logits/domains")
    if (rows[4]["read_words"], rows[4]["write_words"], rows[4]["comparisons"]) != (
            totals["read_words"], totals["write_words"], totals["intermediate_comparisons"]):
        raise AssertionError("domain traffic/comparison conservation")
    h, k, i = geometry["hidden"], geometry["kv_heads"]*geometry["head_dim"], geometry["intermediate"]
    layers, tokens = geometry["layers"], geometry["tokens"]
    useful_macs = [tokens*layers*(2*h*h+2*h*k),
                   tokens*(2*h*(2*layers+1)+2*layers*(h+k)),
                   h*layers*tokens*(tokens+1),
                   tokens*layers*(3*h*i+2*i)]
    useful_macs.append(sum(useful_macs)+tokens*h*geometry["vocabulary"])
    for row, work in zip(rows, useful_macs):
        row["reference_multiply_work"] = work
        row["work_definition"] = "mathematical tensor/norm/attention multiply count; not DUT issue count"
    return {
        "measured": totals, "domains": rows,
        "simulation_tokens_per_second_at_100mhz": totals["tokens"]*100000000/totals["cycles"],
        "clock_hz": 100000000, "measurement": "cycle simulation, not board throughput",
        "traffic_scope": "per-domain public-ABI traffic; span includes intervening work",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--case", type=int, nargs="+")
    args = parser.parse_args()
    experiment = Experiment("benchmarks", args.preparation)
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["verilator", "--version"], "version")
        binary = compile_top(experiment)
        results = []
        experiment.receipt["cases"] = results
        cases = [(mode, banks) for mode in (1, 2, 3, 4) for banks in (1, 2, 4, 8)]
        cases.append((4, 16))
        for index, (mode, banks) in enumerate(cases):
            if args.case is not None and index not in args.case:
                continue
            identity = hashlib.sha256(f"{mode}/{banks}/17".encode()).hexdigest()[:12]
            directory = experiment.directory/f"case-{identity}"
            directory.mkdir()
            if mode != 4:
                geometry = legacy_fixture(directory, seed=17, mode=mode, banks=banks)
            else:
                geometry = native_fixture(directory, seed=17, heads=3, kv_heads=1,
                                          dimension=2, banks=banks, weight_format=1,
                                          layers=3, tokens=4, vocabulary=17, intermediate=5)
                geometry["mode"] = 4
            geometry["fixture_sha256"] = {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in directory.glob("*.txt")}
            print(f"benchmark mode={mode} banks={banks}", flush=True)
            output = experiment.run([experiment.rel(binary), experiment.rel(directory)],
                                    f"simulation-{index}")
            results.append({**geometry, **parse_metrics(output, geometry)})
            experiment.save()
        if args.case is None:
            directories, profiles = [], []
            experiment.receipt["official_config_sha256"] = PINS
            for generation, name in enumerate(("qwen", "deepseek", "llama", "qwen"), 1):
                model = official(name) if name != "llama" else None
                ratio = model["num_attention_heads"]//model["num_key_value_heads"] if model else 3
                theta = model["rope_theta"] if model else 500000
                directory = experiment.directory/f"switch-{generation}-{hashlib.sha256(name.encode()).hexdigest()[:12]}"
                directory.mkdir()
                geometry = native_fixture(
                    directory, seed=17, heads=ratio, kv_heads=1, dimension=2,
                    layers=3, tokens=4, vocabulary=17, intermediate=5, banks=16,
                    bias=name != "llama", theta_value=theta, generation=generation)
                profiles.append({"profile": name, **geometry})
                directories.append(experiment.rel(directory))
            output = experiment.run([experiment.rel(binary), *directories], "switching")
            segments = re.split(r"(?=SUMMARY top )", output)[1:]
            if len(segments) != 4 or "SUMMARY switching sequences=4 reset_count=1" not in output:
                raise AssertionError("missing switching benchmark correctness")
            experiment.receipt["switching"] = [
                {**geometry, **parse_metrics(segment, geometry)}
                for segment, geometry in zip(segments, profiles)]
            output = experiment.run(["python3", "tests/speculative_probe.py"],
                                    "speculative", timeout=2700)
            receipts = [line for line in output.splitlines()
                        if line.startswith("evidence/") and line.endswith("/receipt.json")]
            if len(receipts) != 1:
                raise AssertionError("missing speculative benchmark execution receipt")
            receipt = json.loads((ROOT/receipts[0]).read_text())
            if receipt["exit_code"] != 0 or {row["accepted"] for row in receipt["cases"]} != {0, 1, 2}:
                raise AssertionError("missing speculative benchmark acceptance-length coverage")
            experiment.receipt["speculative"] = {
                "receipt": receipts[0], "cases": receipt["cases"],
                "measurement": "compiled Q4 greedy verification cycles and public traffic",
                "legacy_applicability": "Q1/Q2/Q3 do not expose draft acceptance",
            }
        if not results:
            raise AssertionError("no benchmark executed")
        experiment.receipt["schema"] = 1
        (experiment.directory/"metrics.json").write_text(json.dumps(results, indent=2)+"\n")
        experiment.prune_objects(binary.parent)
    except (RuntimeError, ValueError, AssertionError, KeyError, StopIteration) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
