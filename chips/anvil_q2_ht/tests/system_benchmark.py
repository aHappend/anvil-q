"""Five-domain public-port numerical/event-window simulation benchmarks."""

import argparse
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import Experiment
from benchmark_reference import analyze, expected_workload
from scheduling import budget_info, create_budget, run_graph


def observed(experiment, name, script, options, marker):
    output = experiment.output / name
    if experiment.receipt.get("build_cache") is not None:
        options = [*options, "--build-cache", experiment.receipt["build_cache"]]
    experiment.run(["python3", "tests/" + script, "--output", str(output), *options],
                   name, timeout=14400)
    receipt = json.loads((experiment.root / output / "receipt.json").read_text())
    if receipt["exit"] != 0:
        raise RuntimeError("failed benchmark child receipt: " + name)
    for path, digest in receipt["source_hashes"].items():
        if experiment.receipt["source_hashes"].get(path) != digest:
            raise RuntimeError("benchmark source changed across child: " + path)
    text = receipt["comparison_summary"]
    match = re.search(r"^" + marker + r" (.+)$", text, re.MULTILINE)
    if not match:
        raise RuntimeError("missing measured benchmark fields: " + name)
    metrics = {key: int(value) for key, value in re.findall(r"([a-z_]+)=(\d+)", match[1])}
    if any(metrics.get(key, 0) <= 0 for key in ("cycles", "reads", "writes", "accepted_bytes")):
        raise RuntimeError("empty measured benchmark: " + name)
    metrics["accepted_bytes_per_cycle"] = metrics["accepted_bytes"] / metrics["cycles"]
    metrics["simulation_stdout"] = next(
        row["stdout"] for row in receipt["commands"] if row["argv"][0].endswith("system_sim")
        or row["argv"][0].endswith("parent_sim"))
    return receipt, {"receipt": str(output / "receipt.json"), **metrics}


def run_benchmarks(experiment, modes, selected_cache=None, selected_seed=None, workers=None):
    results = {}
    cells = []
    ledger = []
    for mode in modes:
        caches = ((0, 2) if mode == 0 else (0, 1, 2)) if selected_cache is None else (
            2 if selected_cache else 0,)
        for cache in caches:
            for seed in (11, 29, 101) if selected_seed is None else (selected_seed,):
                stem = f"mode{mode}-cache{cache}-seed{seed}"
                cells.append((stem, mode, cache, seed))
                ledger.append({
                    "check": stem + "-ht", "script": "system_check.py",
                    "options": ["--mode", str(mode), "--cache", str(cache), "--seed", str(seed),
                                "--tied-head", "--memory-service", "common",
                                "--simulator", "verilator", "--benchmark-trace"],
                    "marker": "SYSTEM_WORKLOAD_MEASURED", "outcome": "not-executed"})
                if mode == 0:
                    for banks in (1, 4):
                        ledger.append({
                            "check": stem + f"-parent{banks}", "script": "parent_system_check.py",
                            "options": ["--banks", str(banks), "--cache", str(int(cache == 2)),
                                        "--seed", str(seed), "--benchmark-trace"],
                            "marker": "PARENT_SYSTEM_CHECKED", "outcome": "not-executed"})
    experiment.receipt["benchmark_checks"] = ledger

    def execute(row):
        result = observed(experiment, row["check"], row["script"],
                          row["options"], row["marker"])
        with experiment.lock:
            results[row["check"]] = result

    run_graph(experiment, ledger, execute, workers=workers)
    rows = []
    for stem, mode, cache, seed in cells:
        workload = expected_workload(mode, cache, seed)
        ht_receipt, ht = results[stem + "-ht"]
        if any(ht_receipt["fixture"][key] != workload[key]
               for key in ("image_sha256", "expected_logits")):
            raise RuntimeError("benchmark oracle/RTL workload input mismatch")
        ht["domains"] = analyze((experiment.root / ht["simulation_stdout"]).read_text(),
                                workload, "ht")
        baseline = {}
        if mode == 0:
            for banks in (1, 4):
                parent_receipt, metrics = results[stem + f"-parent{banks}"]
                if any(parent_receipt["fixture"][key] != workload[key]
                       for key in ("image_sha256", "expected_logits")):
                    raise RuntimeError("parent/HT workloads are not numerically identical")
                metrics["domains"] = analyze(
                    (experiment.root / metrics["simulation_stdout"]).read_text(),
                    workload, "parent", banks)
                metrics["ht_cycle_normalized_throughput_ratio"] = metrics["cycles"] / ht["cycles"]
                for domain in ("D1", "D2", "D3", "D4", "D5"):
                    metrics["domains"][domain]["ht_window_throughput_ratio"] = (
                        metrics["domains"][domain]["cycles"] / ht["domains"][domain]["cycles"])
                baseline[banks] = metrics
        rows.append({"domains": ["D1", "D2", "D3", "D4", "D5"], "seed": seed,
                     "mode": "BF16" if mode else "W4A16",
                     "cache": ("Q16", "FP16", "INT8")[cache],
                     "tokens": 3, "compared_logits_per_implementation": 9,
                     "image_sha256": workload["image_sha256"], "ht": ht, "parent": baseline})
        experiment.receipt["benchmarks"] = rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, choices=(11, 29, 101))
    parser.add_argument("--cache", type=int, choices=(0, 1),
                        help="parent cache encoding: 0 Q16, 1 INT8")
    parser.add_argument("--weight-mode", choices=("w4", "bf16", "all"), default="all")
    parser.add_argument("--build-cache", type=Path)
    parser.add_argument("--serial-preparation", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    names = []
    for directory in ("rtl", "anvil_q2_reference/rtl", "tests"):
        names += [str(path.relative_to(root)) for path in sorted((root / directory).glob("*"))
                  if path.is_file()]
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    if args.build_cache is not None:
        experiment.receipt["build_cache"] = str(args.build_cache)
    try:
        if budget_info(root) is None:
            create_budget(experiment)
        modes = (0, 1) if args.weight_mode == "all" else (int(args.weight_mode == "bf16"),)
        run_benchmarks(experiment, modes, args.cache, args.seed,
                       workers=1 if args.serial_preparation else None)
        experiment.receipt["service_model"] = {
            "response_latency_cycles_minimum": 3, "maximum_payload_bytes_per_cycle": 64,
            "ht": "one 64-byte read return per cycle; writes wait on a coincident read return",
            "parent": "one 4-byte scalar transaction per bank; at most four banks",
            "output_stalls": "ready is low when elapsed workload cycle modulo seven equals two",
            "scope": "a common latency/bandwidth ceiling on the genuine, different interfaces"}
        experiment.receipt["limits"] = [
            "synthetic H=I=D=8, one layer, tied embedding, V=S=3 only",
            "one-time host image loading/readback and descriptor commit excluded from HT token cycles",
            "parent service is logical memory, not a measured physical DDR or board clock",
            "D1-D3 event windows end on independently compared complete vector writes; "
            "each starts after the preceding vector or accepted token, not an internal FSM transition",
            "D3 windows include KV storage/reads; D4 cache command-to-response windows overlap D3",
            "D5 elapsed metric includes inter-token idle gaps; domain D5 sums accepted-token-to-done windows",
            "MAC counters observe only actual tensor/GEMV public issue ports, not scalar nonlinear/attention MACs",
            "valid payload bandwidth counts valid tensor/record bytes in each transferred beat, "
            "including repeated bytes, not unique useful model bytes or consumer-use efficiency",
            "parent has no hot-cache allocation or raw FP16/BF16 mode; no missing parent mode is invented",
            "tiny H=8 does not activate multiple parent engines or prove long-stream speedup; "
            "the independent default-width D1 streaming check retains its >1 threshold",
            "no full-model hardware, physical frequency, resource fit or timing acceptance"]
        (experiment.directory / "benchmarks.json").write_text(
            json.dumps({"rows": experiment.receipt["benchmarks"],
                        "service_model": experiment.receipt["service_model"],
                        "limits": experiment.receipt["limits"]}, indent=2) + "\n")
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
