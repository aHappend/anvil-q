#!/usr/bin/env python3
"""Qualify a real late production checkpoint or audit its completed layer prefix.

Branching from one saved state is not an independent benchmark repeat from
reset. Incomplete observations never become tests/data/full_model_results.json.
"""

import argparse
from contextlib import ExitStack
import hashlib
import itertools
import json
import math
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from architecture import metrics
from benchmark import artifact_path, load_json, require, sha
from benchmark_inputs import write_json
from production_checkpoint import event_record, execution, validate_segment, trace_rows
from production_sim import descriptor
from packed_storage import Reader, observation_chunks, transaction_path
from verify import Evidence, ROOT


def exact_fragments(runs, filename, position=None):
    for run in runs:
        if filename in ("layers.f32", "logits.f32"):
            directory = run / f"position-{position}"
            for raw in observation_chunks(directory, filename.split(".")[0]):
                yield from raw
            continue
        path = run / (f"position-{position}" if position is not None else "") / filename
        if path.exists():
            with path.open("rb") as source:
                while data := source.read(1024 * 1024):
                    yield from data


def fp32_classes(values):
    counts = dict.fromkeys(("positive_zero", "negative_zero", "subnormal",
                            "normal", "infinity", "nan"), 0)
    for value in values:
        bits, = struct.unpack("<I", struct.pack("<f", value))
        magnitude = bits & 0x7fffffff
        exponent, fraction = magnitude >> 23, magnitude & 0x7fffff
        if magnitude == 0:
            key = "negative_zero" if bits >> 31 else "positive_zero"
        elif exponent == 0:
            key = "subnormal"
        elif exponent == 255:
            key = "nan" if fraction else "infinity"
        else:
            key = "normal"
        counts[key] += 1
    return counts


def qualify(ev, item, cycles):
    head = validate_segment(ev, item)
    require(head["status"] == "paused" and cycles >= 2,
            "late qualification requires a paused process and at least two cycles")
    start, binding = head["end_cycle"], head["binding"]
    baseline_path = ev.path / "uninterrupted-branch"
    baseline, _ = execution(ev, binding, baseline_path, start + cycles, head, item)
    first_path, second_path = ev.path / "split-first", ev.path / "split-second"
    first, first_item = execution(ev, binding, first_path, start + cycles // 2, head, item)
    runs = [first_path]
    if first["status"] == "paused":
        validate_segment(ev, first_item, binding)
        last, _ = execution(ev, binding, second_path, start + cycles, first, first_item)
        runs.append(second_path)
    else:
        last = first
    require(last["status"] == baseline["status"] and
            last["end_cycle"] == baseline["end_cycle"], "late checkpoint branch progress differs")
    if last["status"] == "paused":
        require(sha(ROOT / last["state"]["path"]) == sha(ROOT / baseline["state"]["path"]),
                "late checkpoint DUT/host state differs")
    else:
        require(load_json(ROOT / last["summary"]["path"]) ==
                load_json(ROOT / baseline["summary"]["path"]),
                "late checkpoint completed summaries differ")
    compared = 0
    resumed_rows = itertools.chain.from_iterable(
        trace_rows(transaction_path(path)) for path in runs)
    for actual, wanted in itertools.zip_longest(
            resumed_rows, trace_rows(transaction_path(baseline_path))):
        require(actual is not None and actual == wanted, "late checkpoint public trace differs")
        compared += 1
    require(compared > 0, "no late checkpoint public transaction comparisons")
    for actual, wanted in itertools.zip_longest(
            exact_fragments(runs, "events.jsonl"),
            exact_fragments([baseline_path], "events.jsonl")):
        require(actual is not None and actual == wanted, "late checkpoint public events differ")
    positions = {int(path.name.removeprefix("position-"))
                 for run in [baseline_path, *runs] for path in run.glob("position-*")}
    for position in sorted(positions):
        for filename in ("layers.f32", "logits.f32"):
            for actual, wanted in itertools.zip_longest(
                    exact_fragments(runs, filename, position),
                    exact_fragments([baseline_path], filename, position)):
                require(actual is not None and actual == wanted, "late checkpoint vector differs")
    ev.assertion("late_checkpoint_actual_rtl_branch_equivalence", True,
                 start_cycle=start, end_cycle=last["end_cycle"], transactions=compared,
                 source_checkpoint=item, identical_serialized_state=last["status"] == "paused",
                 identical_events_and_vector_fragments=True,
                 benchmark_independent_repeat_coverage=False, complete_benchmark=False)


def audit(ev, item):
    chain = []
    head = validate_segment(ev, item, chain=chain)
    binding = head["binding"]
    require(binding["workload"] == "teacher", "layer prefix audit requires matching teacher reference")
    layers_path = artifact_path(ROOT, binding["arguments"][8])
    positions = int(binding["arguments"][10])
    reference_reader = None
    if layers_path.suffix == ".aqp":
        reference_reader = Reader(layers_path, dtype="<f8", shape=[positions, 24, 896],
                                  axes=["position", "layer", "component"])
    else:
        require(layers_path.stat().st_size == positions * 24 * 896 * 8,
                "teacher reference layer shape")
    completed = {}
    fragments = {}
    for row in reversed(chain):
        for entry in row["artifacts"]:
            path = ROOT / entry["path"]
            if path.name == "events.jsonl":
                with path.open("rb") as events:
                    for line in events:
                        event = event_record(line)
                        if event["event"] == "layer":
                            key = event["position"], event["layer"]
                            require(key not in completed, "duplicate completed layer event")
                            completed[key] = event
            elif path.name in ("layers.f32", "layers.aqp"):
                position = int(path.parent.name.removeprefix("position-"))
                # The helper rejects duplicate encodings and checks fragment
                # dtype/axes and every decoded chunk before using the bits.
                for raw in observation_chunks(path.parent, "layers"):
                    fragments.setdefault(position, bytearray()).extend(raw)
    require(completed, "no complete real production layer observations")
    results = []
    observed_keys = set()
    with ExitStack() as stack:
        reference = None if reference_reader else stack.enter_context(layers_path.open("rb"))
        for position, raw in sorted(fragments.items()):
            count = len(raw) // (896 * 4)
            require(position < positions and count <= 24, "partial layer vector shape")
            require(count == sum(key[0] == position for key in completed),
                    "layer events/fragments disagree")
            for layer in range(count):
                require((position, layer) in completed, "nonconsecutive completed layers")
                offset = layer * 896 * 4
                actual = struct.unpack("<896f", raw[offset:offset + 896*4])
                offset = (position * 24 + layer) * 896 * 8
                if reference_reader:
                    raw_expected = reference_reader.read(offset, 896 * 8)
                else:
                    reference.seek(offset)
                    raw_expected = reference.read(896 * 8)
                require(len(raw_expected) == 896 * 8, "truncated completed-layer reference")
                expected = struct.unpack("<896d", raw_expected)
                require(all(math.isfinite(value) for value in (*actual, *expected)),
                        "nonfinite completed production layer/reference")
                observed_keys.add((position, layer))
                result = metrics(actual, expected)
                result["classes"] = {
                    "observed_fp32": fp32_classes(actual),
                    "fp32_rounded_fp64_reference": fp32_classes(expected),
                }
                passed = binding["mode"] == "w4a16" or (
                    result["normalized_max_absolute_error"] <= .002 and
                    (result["reference_all_zero"] or
                     result["cosine"] is not None and result["cosine"] >= .9999))
                result.update(position=position, layer=layer, passed=passed,
                              native_fidelity_limits_applied=binding["mode"] != "w4a16",
                              completion_cycle=completed[position, layer]["cycle"])
                results.append(result)
                require(passed, "completed production layer failed independent FP64 bounds: " +
                        json.dumps(result))
    require(observed_keys == set(completed), "missing completed production layer vector")
    write_json(ev.path / "layer-prefix-comparisons.json", {
        "source_checkpoint": item, "mode": binding["mode"], "layers": results,
        "complete_benchmark": False, "independent_repeat_coverage": False,
        "limitations": "Completed layer prefix only; no final-logit, whole-token, "
                      "late-layer, task-score, hardware or benchmark completion claim."})
    ev.assertion("partial_production_layers_independent_reference", True,
                 layers=len(results), elements=len(results)*896, mode=binding["mode"],
                 independent_repeat_coverage=False, complete_benchmark=False)


def compare_timeout(ev, old_path, item):
    """Link a retained timeout to graceful suspension, not to an RTL repair."""
    old = load_json(old_path)
    timed_out = [row for row in old["records"] if row.get("timed_out")]
    require(old["status"] == "failed" and len(timed_out) == 1,
            "expected exactly one retained failed simulation timeout")
    previous = timed_out[0]
    head = validate_segment(ev, item)
    binding = head["binding"]
    require(head["parent"] is None and head["status"] == "paused",
            "timeout comparison requires the first gracefully paused segment")
    hashes = {name: value for name, value in old["source_sha256"].items()
              if name.startswith("rtl/")}
    require(hashes == {name: value for name, value in binding["build_sources"].items()
                       if name.startswith("rtl/")}, "RTL differs across timeout recovery")
    old_args, new_args = previous["argv"], binding["arguments"]
    def reference_hash(path, kind):
        positions = int(new_args[10])
        shape, axes = (([positions, 24, 896], ["position", "layer", "component"])
                       if kind == "layers" else
                       ([151936, positions], ["vocabulary", "position"]))
        if path.suffix != ".aqp":
            require(path.stat().st_size == math.prod(shape) * 8,
                    "timeout reference array shape differs")
            return sha(path)
        reader = Reader(path, dtype="<f8", shape=shape, axes=axes)
        digest = hashlib.sha256()
        for raw in reader.chunks():
            digest.update(raw)
        return digest.hexdigest()
    for old_index, new_index in ((1, 0), (2, 1), (3, 2), (9, 8), (10, 9)):
        left = artifact_path(ROOT, old_args[old_index])
        right = artifact_path(ROOT, new_args[new_index])
        kind = "layers" if old_index == 9 else "logits"
        require((reference_hash(left, kind) == reference_hash(right, kind)) if old_index in (9, 10)
                else (sha(left) == sha(right)), "timeout recovery input/reference differs")
        ev.receipt.setdefault("data_sha256", {}).update({
            str(left.relative_to(ROOT)): sha(left), str(right.relative_to(ROOT)): sha(right)})
    require(old_args[5:9] == new_args[4:8], "timeout recovery workload differs")
    receipt = load_json(artifact_path(ROOT, head["receipt"]))
    current = next(row for row in receipt["records"] if row["label"] == "segment")
    require(current["exit_code"] == 0 and not current["timed_out"] and
            current["timeout_s"] >= 3600, "recovery child did not finish normally")
    logs = [artifact_path(ROOT, row["stdout"]).read_text().splitlines()
            for row in (previous, current)]
    progress = [[line for line in lines if line.startswith(("PROGRESS ", "LAYER "))]
                for lines in logs]
    require(progress[0] == progress[1] and progress[0],
            "timeout recovery observed progress differs")
    before = artifact_path(ROOT, old_args[4])
    after = (ROOT / head["state"]["path"]).parent
    identical_bytes = 0
    for left, right in itertools.zip_longest(
            exact_fragments([before], "layers.f32", 0),
            exact_fragments([after], "layers.f32", 0)):
        require(left is not None and left == right, "timeout recovery completed layer bytes differ")
        identical_bytes += 1
    require(identical_bytes > 0, "timeout recovery has no completed layer bytes")
    ev.receipt["repair_of"] = descriptor(old_path)
    result = {
        "original_timeout_receipt": descriptor(old_path),
        "graceful_checkpoint": item, "original_timeout_s": previous["timeout_s"],
        "original_elapsed_s": previous["elapsed_s"],
        "current_timeout_s": current["timeout_s"],
        "current_elapsed_s": current["elapsed_s"], "end_cycle": head["end_cycle"],
        "identical_rtl": True, "identical_inputs_and_selected_references": True,
        "identical_retained_progress_lines": len(progress[0]),
        "identical_completed_layer_bytes": identical_bytes,
        "complete_benchmark": False,
        "limitations": "Procedural recovery only. C++ collection/serialization changed; "
                      "commands and stop conditions differ. No same-command causal "
                      "isolation, performance gain, completed token or RTL fix is claimed.",
    }
    write_json(ev.path / "timeout-recovery-comparison.json", result)
    ev.assertion("retained_timeout_linked_to_graceful_source_bound_checkpoint", True, **result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--qualify", type=Path)
    operation.add_argument("--audit", type=Path)
    operation.add_argument("--compare-timeout", type=Path)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--cycles", type=int, default=1000000)
    args = parser.parse_args()
    ev = Evidence("production-resume")
    passed = False
    try:
        require(bool(args.checkpoint) == bool(args.compare_timeout),
                "--checkpoint is required only for --compare-timeout")
        path = artifact_path(ROOT, str(args.qualify or args.audit or args.checkpoint))
        item = descriptor(path)
        require(ev.run("verilator-version", ["verilator", "--version"], timeout=30),
                "installed Verilator unavailable")
        if args.qualify:
            qualify(ev, item, args.cycles)
        elif args.audit:
            classes = fp32_classes((0.0, -0.0, 2**-149, 1.0, float("inf"), float("nan")))
            require(all(count == 1 for count in classes.values()),
                    "FP32 output classification fixture failed")
            ev.assertion("synthetic_host_fp32_classification", True, **classes,
                         no_rtl_execution=True)
            audit(ev, item)
        else:
            compare_timeout(ev, artifact_path(ROOT, str(args.compare_timeout)), item)
        passed = True
    except (ValueError, OSError, KeyError, ImportError) as error:
        ev.assertion("production_resume_failure", False, diagnostic=str(error))
    finally:
        ev.finish("passed" if passed else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT)),
                          "complete_benchmark": False}), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
