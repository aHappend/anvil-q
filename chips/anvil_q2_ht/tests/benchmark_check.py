"""Recompare retained public-port traces; never substitutes for RTL execution."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark_reference import analyze, expected_workload
from retention import Experiment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--ht-receipt", type=Path)
    selection.add_argument("--matrix-receipt", type=Path)
    parser.add_argument("--parent-receipt", type=Path)
    parser.add_argument("--banks", type=int, choices=(1, 4), default=4)
    parser.add_argument("--mode", type=int, choices=(0, 1), default=0)
    parser.add_argument("--cache", type=int, choices=(0, 1, 2), default=0)
    parser.add_argument("--seed", type=int, choices=(11, 29, 101), default=11)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    names = [str(path.relative_to(root))
             for folder in ("rtl", "anvil_q2_reference/rtl", "tests")
             for path in sorted((root / folder).glob("*")) if path.is_file()]
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    try:
        experiment.run(["python3", "--version"], "python-version")
        results = {}
        inputs = []
        cases = []
        if args.matrix_receipt is not None:
            path = args.matrix_receipt
            if path.is_absolute() or ".." in path.parts or args.parent_receipt is not None:
                raise ValueError("matrix receipt must be project-relative and cannot use --parent-receipt")
            matrix = json.loads((root / path).read_text())
            if matrix["exit"] != 0:
                raise RuntimeError("matrix RTL execution did not complete")
            expected = {(mode, cache, seed)
                        for mode, caches in ((0, (0, 2)), (1, (0, 1, 2)))
                        for cache in caches for seed in (11, 29, 101)}
            seen = set()
            for row in matrix["benchmarks"]:
                mode, cache, seed = (int(row["mode"] == "BF16"),
                                    ("Q16", "FP16", "INT8").index(row["cache"]), row["seed"])
                key = mode, cache, seed
                if key in seen or key not in expected:
                    raise RuntimeError("missing/extra/duplicate matrix configuration")
                seen.add(key)
                cases.append(("ht", Path(row["ht"]["receipt"]), mode, cache, seed, 16))
                if set(row["parent"]) != ({"1", "4"} if mode == 0 else set()):
                    raise RuntimeError("incorrect parent benchmark denominator")
                for banks, metrics in row["parent"].items():
                    cases.append(("parent", Path(metrics["receipt"]), mode, cache, seed, int(banks)))
            if seen != expected or len(cases) != 27:
                raise RuntimeError("incomplete fifteen-cell/twenty-seven-execution matrix")
            inputs.append({"matrix_receipt": str(path),
                           "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()})
        else:
            cases.append(("ht", args.ht_receipt, args.mode, args.cache, args.seed, 16))
            if args.parent_receipt is not None:
                cases.append(("parent", args.parent_receipt, args.mode, args.cache, args.seed, args.banks))
        for implementation, path, mode, cache, seed, banks in cases:
            workload = expected_workload(mode, cache, seed)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("input receipts must be project-relative")
            receipt = json.loads((root / path).read_text())
            if receipt["exit"] != 0:
                raise RuntimeError("cannot compare a failed RTL child as successful execution")
            if any(receipt["fixture"][key] != workload[key]
                   for key in ("image_sha256", "expected_logits")):
                raise RuntimeError("retained workload is not the independent model's workload")
            for name, digest in receipt["source_hashes"].items():
                if digest != experiment.receipt["source_hashes"].get(name):
                    raise RuntimeError("retained trace source changed: " + name)
            command = next(row for row in receipt["commands"] if row["argv"][0].endswith(
                "system_sim" if implementation == "ht" else "parent_sim"))
            if command["exit"] != 0 or command["timed_out"]:
                raise RuntimeError("retained simulator did not complete successfully")
            log = root / command["stdout"]
            text = log.read_text()
            label = f"{implementation}-banks{banks}-mode{mode}-cache{cache}-seed{seed}"
            results[label] = analyze(text, workload, implementation, banks)
            inputs.append({"receipt": str(path),
                           "receipt_sha256": hashlib.sha256((root / path).read_bytes()).hexdigest(),
                           "stdout": command["stdout"],
                           "stdout_sha256": hashlib.sha256(log.read_bytes()).hexdigest()})
            lines = text.splitlines()
            index = next(index for index, line in enumerate(lines)
                         if line.startswith("BENCH_VECTOR "))
            original = lines[index]
            fields = original.split()
            fields[-1] = f"{int(fields[-1], 16) ^ 1:08x}"
            lines[index] = " ".join(fields)
            (experiment.directory / (label + "-corrupt-observation.txt")).write_text(
                "\n".join(lines) + "\n")
            try:
                analyze("\n".join(lines), workload, implementation, banks)
            except RuntimeError as error:
                if not str(error).startswith("BENCH_NUMERICAL:"):
                    raise
                results[label]["checker_sensitivity"] = {
                    "corrupted_intermediate_word": "rejected", "diagnostic": str(error)}
            else:
                raise RuntimeError("intermediate checker accepted a corrupted observed word")
        summary = {
            "executions": len(cases),
            "compared_intermediate_words": sum(
                row["D5"]["compared_intermediate_words"] for row in results.values()),
            "compared_logits": sum(row["D5"]["compared_logits"] for row in results.values()),
            "compared_cache_words": sum(row["D4"]["compared_words"] for row in results.values()),
            "completed_cache_commits": sum(row["D4"]["commits"] for row in results.values()),
            "corrupt_observation_rejections": len(results),
        }
        if args.matrix_receipt is not None:
            ratios = {}
            for banks in (1, 4):
                ratios[str(banks)] = {}
                for domain in ("D1", "D2", "D3", "D4", "D5"):
                    values = [
                        results[f"parent-banks{banks}-mode0-cache{cache}-seed{seed}"][domain]["cycles"] /
                        results[f"ht-banks16-mode0-cache{cache}-seed{seed}"][domain]["cycles"]
                        for cache in (0, 2) for seed in (11, 29, 101)]
                    ratios[str(banks)][domain] = {"minimum": min(values), "maximum": max(values)}
            summary["w4_parent_to_ht_event_window_throughput_ratio"] = ratios
        experiment.receipt.update(inputs=inputs, results=results, compared_executions=len(cases),
                                  summary=summary,
                                  scope="retained-trace recomparison and comparator sensitivity")
        (experiment.directory / "comparisons.json").write_text(
            json.dumps(results, indent=2) + "\n")
        (experiment.directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, IndexError, StopIteration) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
