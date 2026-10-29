"""Bounded AWQ trace-loss diagnosis; retained failures are read-only inputs."""

import argparse
import hashlib
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from numerical_checks import compare_lane
from retained import ROOT, Run, audit_streams


def receipt_path(name):
    path = Path(name)
    assert not path.is_absolute() and ".." not in path.parts
    assert path.parts[0] == "evidence" and path.name == "receipt.json"
    resolved = (ROOT / path).resolve()
    resolved.relative_to(ROOT / "evidence")
    return resolved


def reopen(name):
    path = receipt_path(name)
    data = path.read_bytes()
    receipt = json.loads(data)
    hashes, errors = audit_streams(receipt["commands"])
    assert not errors, errors
    assert hashes == receipt["raw_stream_sha256"], "raw-stream identity changed"
    for generated, expected in receipt.get("generated_sha256", {}).items():
        target = (ROOT / generated).resolve()
        target.relative_to(ROOT / "evidence")
        assert hashlib.sha256(target.read_bytes()).hexdigest() == expected, generated
    return receipt


def trace_path(receipt):
    commands = [c for c in receipt["commands"] if c["argv"][0] == "vvp"
                and c["argv"][1:] != ["-V"]]
    assert len(commands) == 1
    return ROOT / commands[0]["stdout"]


def inspect(name):
    receipt = reopen(name)
    trace = trace_path(receipt)
    data = trace.read_bytes()
    counts = dict(IN=0, OUT=0, AWQ_CAPTURE=0)
    first_gap = None
    previous_input = None
    byte_offset = 0
    for line_number, raw in enumerate(data.splitlines(keepends=True), 1):
        words = raw.split()
        if words and words[0].decode() in counts:
            kind = words[0].decode()
            counts[kind] += 1
            if kind == "IN":
                cycle, index = int(words[1]), int(words[2])
                if index != counts["IN"] - 1 and first_gap is None:
                    first_gap = dict(
                        expected_index=counts["IN"] - 1, observed_index=index,
                        observed_cycle=cycle, previous_input=previous_input,
                        line=line_number, byte_offset=byte_offset,
                        observed_record=raw.decode().rstrip())
                previous_input = dict(index=index, cycle=cycle)
        byte_offset += len(raw)
    result = dict(receipt=name, bytes=len(data), counts=counts, first_input_gap=first_gap)
    try:
        result["comparison_metrics"] = compare_lane(trace, "bf16", 4096)
    except (AssertionError, ArithmeticError, ValueError) as exc:
        traceback.print_exc()
        result["comparison_failure"] = f"{type(exc).__name__}: {exc}"
    print(json.dumps(result, indent=2))


def byte_difference(old, fresh):
    prefix = 0
    while prefix < min(len(old), len(fresh)) and old[prefix] == fresh[prefix]:
        prefix += 1
    suffix = 0
    while (suffix < min(len(old), len(fresh)) - prefix
           and old[len(old) - suffix - 1] == fresh[len(fresh) - suffix - 1]):
        suffix += 1
    return dict(common_prefix_bytes=prefix, common_suffix_bytes=suffix,
                old_middle_bytes=len(old) - prefix - suffix,
                fresh_middle_bytes=len(fresh) - prefix - suffix)


def execute(failure, storage):
    run = Run("storage-stream-diagnostic")
    run.receipt.update(failure_receipt=failure, storage_receipt=storage)
    try:
        run.command(["python3", "--version"], "python-version")
        for label, name in (("storage", storage), ("historical", failure)):
            path = receipt_path(name)
            run.receipt.setdefault("input_sha256", {})[name] = (
                hashlib.sha256(path.read_bytes()).hexdigest())
            run.command(["python3", "tests/stream_retention_checks.py",
                         "--action", "reopen", "--path", name], label + "-reopen")
        diagnostic = run.command(
            ["python3", "tests/stream_retention_checks.py", "--action", "inspect",
             "--path", failure], "historical-comparison")
        historical = json.loads(diagnostic.read_text())
        assert historical.get("comparison_failure"), "historical rejection not reproduced"
        assert historical["first_input_gap"] is not None, "missing-record boundary not found"
        children = {}
        for fmt in ("bf16", "fp16"):
            output = run.command(
                ["python3", "tests/awq_lane_checks.py", "--format", fmt,
                 "--repair-of", failure], fmt + "-workload",
                environment={"ANVIL_EVIDENCE_ROOT": run.relative(run.path / "children")})
            names = [s for s in output.read_text().splitlines() if s.endswith("/receipt.json")]
            assert len(names) == 1
            child = reopen(names[0])
            assert child["outcome"] == "passed-focused-only"
            assert child["source_sha256"] == run.receipt["source_sha256"]
            metrics = child["metrics"]
            assert metrics["accepted"] == metrics["retired"] == 4096
            assert metrics["scalar_results_compared"] == 32768
            assert metrics["dequantized_weights_compared"] == 32768
            run.command(["python3", "tests/stream_retention_checks.py", "--action", "reopen",
                         "--path", names[0]], fmt + "-independent-reopen")
            children[fmt] = dict(receipt=names[0], metrics=metrics)
        old_trace = trace_path(reopen(failure)).read_bytes()
        fresh_trace = trace_path(reopen(children["bf16"]["receipt"])).read_bytes()
        # Simulator finish messages contain their distinct generated bench paths.
        old_records = b"".join(line for line in old_trace.splitlines(keepends=True)
                               if line.startswith((b"IN ", b"OUT ")))
        fresh_records = b"".join(line for line in fresh_trace.splitlines(keepends=True)
                                 if line.startswith((b"IN ", b"OUT ")))
        difference = byte_difference(old_records, fresh_records)
        run.finish(
            "passed-focused-only", historical=historical, children=children,
            record_byte_difference=difference,
            limitations="Fresh successful retention does not identify the historical loss mechanism; "
                        "no RTL or capture repair is inferred from non-reproduction.")
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError, KeyError) as exc:
        traceback.print_exc()
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=("inspect", "reopen"))
    parser.add_argument("--path")
    parser.add_argument("--failure-receipt")
    parser.add_argument("--storage-receipt")
    args = parser.parse_args()
    if args.action == "inspect":
        inspect(args.path)
    elif args.action == "reopen":
        receipt = reopen(args.path)
        print(json.dumps(dict(receipt=args.path, outcome=receipt["outcome"],
                              raw_streams_compared=len(receipt["raw_stream_sha256"]))))
    else:
        raise SystemExit(execute(args.failure_receipt, args.storage_receipt))
