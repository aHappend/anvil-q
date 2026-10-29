#!/usr/bin/env python3
"""Bounded synthetic reference allocation diagnostics, never collection approval."""

import argparse
import gc
import json
import os
from pathlib import Path
import resource
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import load_json, require, sha
from memory_capacity_checks import Monitor, availability, process_sample
from verify import Evidence, ROOT


THREAD_KEYS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
               "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")


def extents():
    suite = load_json(ROOT / "tests/data/benchmark_manifest.json")
    rows, bindings = [], {}
    for group in suite["domains"].values():
        for case in group["cases"]:
            lengths = {}
            for key in ("teacher_tokens", "prompt_tokens"):
                item = case[key]
                path = ROOT / item["path"]
                require(not Path(item["path"]).is_absolute() and
                        path.resolve().is_relative_to(ROOT),
                        "token fixture escapes project")
                require(sha(path) == item["sha256"], "token fixture hash differs")
                tokens = load_json(path)
                require(tokens and all(type(token) is int and 0 <= token < 151936
                                       for token in tokens), "invalid token fixture")
                lengths[key] = len(tokens)
                bindings[item["path"]] = item["sha256"]
            rows.append({"teacher_positions": lengths["teacher_tokens"],
                         "greedy_positions_maximum": lengths["prompt_tokens"] + 127})
    require(len(rows) == 50, "reference diagnostic needs all fifty case extents")
    teacher = max(row["teacher_positions"] for row in rows)
    observer = max(max(row.values()) for row in rows)
    require(0 < teacher <= observer <= 32768, "invalid reference extents")
    return teacher, observer, bindings, rows


def worker():
    import numpy as np
    from fp64_reference import decode, encode, rope, silu

    positions, observer, bindings, _ = extents()
    report = {
        "purpose": "synthetic-maximum-context-reference-component-memory",
        "acceptance_evidence": False,
        "numpy_version": np.__version__, "python_version": sys.version,
        "teacher_positions": positions, "observer_positions": observer,
        "token_sha256": bindings,
        "thread_settings": {key: os.environ.get(key) for key in THREAD_KEYS},
        "whole_process_memory_qualified": False,
        "collection_launched": False, "phases": [],
    }

    def snapshot(label, **detail):
        samples = process_sample(os.getpid())
        require(len(samples) == 1, "unexpected reference diagnostic child")
        report["phases"].append({
            "phase": label, **samples[0][1],
            "ru_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            **detail})
        print(json.dumps({"phase": label}), flush=True)

    snapshot("numpy-and-reference-imports")
    # Repeat in one process to expose retention; do not infer a fifty-case bound.
    for repeat in range(3):
        for mode, bits in (("bf16", 0x3e00), ("fp16", 0x3000)):
            raw = np.full((4864, 896), bits, dtype="<u2")
            values = decode(raw if mode == "bf16" else raw.view("<f2"),
                            "BF16" if mode == "bf16" else "F16")
            require(np.all(values == .125), "synthetic native decode differs")
            snapshot(f"{repeat}-{mode}-largest-weight-decode",
                     decoded_payload_bytes=values.nbytes)
            del raw, values
        x = np.full((positions, 896), .125, dtype="<f8")
        weights = np.full((4864, 896), .125, dtype="<f8")
        gate = x @ weights.T
        require(gate.shape == (positions, 4864) and np.all(gate == 14.),
                "maximum-shape FP64 BLAS known answer differs")
        up = gate.copy()
        activated = silu(gate) * up
        require(np.isfinite(activated).all(), "synthetic activation is nonfinite")
        snapshot(f"{repeat}-projection-and-swiglu",
                 named_payload_bytes=sum(a.nbytes for a in (x, weights, gate, up, activated)))
        del weights, gate, up, activated
        q = np.full((positions, 14, 64), .125, dtype="<f8")
        rotated = rope(q, np.arange(positions, dtype="<f8")[:, None, None], 1000000.)
        require(np.isfinite(rotated).all(), "synthetic RoPE is nonfinite")
        mask = np.triu(np.ones((positions, positions), dtype=bool), 1)
        key = np.full((positions, 64), .125, dtype="<f8")
        value = key.copy()
        for head in range(14):
            scores = q[:, head] @ key.T / 8
            scores[mask] = -np.inf
            exponentials = np.exp(scores - scores.max(axis=1, keepdims=True))
            probabilities = exponentials / exponentials.sum(axis=1, keepdims=True)
            context = probabilities @ value
            require(np.allclose(context, .125, rtol=0, atol=1e-14),
                    "synthetic causal-attention known answer differs")
        snapshot(f"{repeat}-attention-last-head-and-rope")
        del q, rotated, mask, key, value, scores, exponentials, probabilities, context
        layers = [x.copy() for _ in range(24)]
        stacked = np.asarray(layers)
        del layers
        serialized = np.transpose(stacked, (1, 0, 2)).astype("<f8").tobytes()
        require(len(serialized) == positions * 24 * 896 * 8,
                "maximum layer serialization extent differs")
        snapshot(f"{repeat}-layer-stack-transpose-cast-serialization",
                 stack_bytes=stacked.nbytes, serialized_bytes=len(serialized))
        del serialized
        final = stacked[-1]
        final = final / np.sqrt(np.mean(final * final, axis=-1, keepdims=True) + 1e-6)
        raw_rows = np.full((1024, 896), 0x3e00, dtype="<u2")
        rows = decode(raw_rows, "BF16")
        # Match the raw teacher's retained previous block/cast/write lifetimes.
        for block in range(2):
            logits = rows @ final.T
            payload = logits.astype("<f8").tobytes()
            require(logits.shape == (1024, positions) and
                    len(payload) == 1024 * positions * 8 and
                    np.isfinite(logits).all(), "synthetic vocabulary block differs")
        snapshot(f"{repeat}-vocabulary-blocks-and-retained-stack")
        # Exercise the actual conversion helpers' temporaries, not their imitation.
        for mode in ("bf16", "fp16"):
            converted = encode(rows, mode)
            require(converted.nbytes == 1024 * 896 * 2, "conversion extent differs")
        del x, stacked, final, raw_rows, rows, logits, payload, converted
        gc.collect()
        snapshot(f"{repeat}-post-release")
    report["scope"] = (
        "Synthetic components at actual maximum teacher extents, three serial repeats. "
        "No checkpoint weights, reference inference, RTL, collection or packed services. "
        "Known answers check fixture execution only, not product numerical acceptance. "
        "RSS observations include this worker's interpreter/NumPy/BLAS and allocator "
        "retention, but do not bound unexercised AWQ decode, complete 24-layer lifetimes, "
        "all vocabulary blocks, surviving orchestration metadata, build/comparison peaks, "
        "mapped files/page tables, kernel charges or other users. No memory reserved.")
    print("ANVIL_REFERENCE_MEMORY " + json.dumps(report), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        worker()
        return 0
    ev = Evidence("reference-component-memory")
    ok = False
    try:
        positions, observer, bindings, rows = extents()
        ev.receipt["data_sha256"] = bindings
        ev.receipt["observed_availability"] = availability()
        from collection_capacity import array_allocation
        stat = os.statvfs(ev.path)
        allocation = array_allocation(rows, stat.f_frsize)
        required_bytes = 2 * allocation["rounded_array_data_bytes_one_successful_attempt"]
        required_inodes = 2 * allocation["unique_array_payload_file_inodes_one_attempt"]
        available_bytes = stat.f_bavail * stat.f_frsize
        ev.receipt["admitted_raw_path_array_floor_observation"] = {
            "required_array_bytes_with_one_retained_failure": required_bytes,
            "required_array_inodes_with_one_retained_failure": required_inodes,
            "available_bytes": available_bytes, "available_inodes": stat.f_favail,
            "byte_shortfall_before_traces_and_metadata": max(0, required_bytes - available_bytes),
            "array_floor_fits_observed_capacity":
                required_bytes <= available_bytes and required_inodes <= stat.f_favail,
            "reserved_bytes": 0, "storage_guard_changed": False,
            "complete_storage_qualified": False,
            "scope": "Same raw array formula as the admitted production preflight, "
                     "not a production invocation. Gzip traces, metadata, logs, staging, "
                     "other checks and native-gate retention are additional. Packed "
                     "collection remains disabled; no compression ratio assumed.",
        }
        # Load the actual collector's imports without executing its entrypoint.
        import production_sim
        require(callable(production_sim.run_collection), "collector entrypoint missing")
        with Monitor() as monitor:
            ok = ev.run("reference-component-worker", [
                sys.executable, "tests/reference_memory_checks.py", "--worker"],
                timeout=3600)
        ev.receipt["orchestrator_and_child_observation"] = {
            **monitor.report(),
            "scope": "This Evidence orchestrator plus component worker, not a production "
                     "collection orchestrator. Includes source hashing high-water via "
                     "ru_maxrss; 20-ms samples can miss peaks and shared pages double-count.",
        }
        require(ok, "reference component worker failed")
        output = (ev.path / "reference-component-worker.stdout").read_text()
        reports = [json.loads(line.removeprefix("ANVIL_REFERENCE_MEMORY "))
                   for line in output.splitlines() if line.startswith("ANVIL_REFERENCE_MEMORY ")]
        require(len(reports) == 1, "reference component report missing or ambiguous")
        report = reports[0]
        suffixes = ("bf16-largest-weight-decode", "fp16-largest-weight-decode",
                    "projection-and-swiglu", "attention-last-head-and-rope",
                    "layer-stack-transpose-cast-serialization",
                    "vocabulary-blocks-and-retained-stack", "post-release")
        expected_phases = ["numpy-and-reference-imports", *(
            f"{repeat}-{suffix}" for repeat in range(3) for suffix in suffixes)]
        require(report["teacher_positions"] == positions and
                report["observer_positions"] == observer and
                report["token_sha256"] == bindings and
                [row["phase"] for row in report["phases"]] == expected_phases,
                "reference component diagnostic incomplete")
        ev.receipt["component_observation"] = report
        ev.assertion("synthetic_reference_components_executed", True,
                     repeats=3, phases=22, complete_process_bound=False,
                     capacity_admitted=False, collection_launched=False)
    except (OSError, ValueError, KeyError, ImportError) as error:
        ok = False
        ev.assertion("reference_component_diagnostic_exception", False, error=repr(error))
    finally:
        ev.receipt["outputs"] = {
            str(path.relative_to(ROOT)): sha(path)
            for path in ev.path.iterdir() if path.is_file() and path.name != "receipt.json"}
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
