#!/usr/bin/env python3
"""Streaming independent architectural address/order audit of production traces.

This is complementary to numerical comparisons and mutable-memory readback.
No DUT internals or RTL transition equations enter the expected schedule.
--allow-prefix reports incomplete coverage explicitly, never benchmark completion.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from architecture import Architecture, CONFIGURATIONS
from benchmark import artifact_path, load_json, require, sha
from benchmark_inputs import write_json
from verify import Evidence, ROOT


PRODUCTION = (24, 896, 4864, 14, 2, 64, 128, 151936, 32768)
MODES = {"w4a16": 0, "bf16": 1, "fp16": 2}


def schedule(config, mode, tokens):
    """Yield (write,kind,layer,projection,row,column,operator) lazily."""
    layers, hidden, intermediate, heads, kv_heads, dimension, group, vocab, depth = config
    require(mode in (0, 1, 2) and tokens and len(tokens) <= depth,
            "invalid architectural schedule input")
    require(all(type(token) is int and 0 <= token < vocab for token in tokens),
            "invalid schedule token ID")

    def access(write, kind, layer=0, proj=0, row=0, col=0, operator=""):
        return write, kind, layer, proj, row, col, operator

    def norm(layer, source, destination, kind):
        operator = "norm" + str(kind)
        for index in range(hidden):
            yield access(0, 8, row=source, col=index, operator=operator)
        for index in range(hidden):
            yield access(0, 8, row=source, col=index, operator=operator)
            yield access(0, kind, layer=layer if kind != 7 else 0,
                         col=index, operator=operator)
            yield access(1, 8, row=destination, col=index, operator=operator)

    def projection(layer, proj):
        operator = "projection" + str(proj)
        inputs = intermediate if proj == 6 else hidden
        outputs = kv_heads * dimension if proj in (1, 2) else (
            intermediate if proj in (4, 5) else hidden)
        source = (1, 1, 1, 5, 8, 8, 11)[proj]
        destination = (2, 3, 4, 6, 9, 10, 12)[proj]
        for block in range(0, outputs, 8):
            for row in range(inputs):
                if mode == 0 and row % group == 0:
                    yield access(0, 2, layer, proj, row // group, block // 8, operator)
                    for lane in range(8):
                        yield access(0, 3, layer, proj, row // group, block + lane, operator)
                yield access(0, 8, row=source, col=row, operator=operator)
                if mode:
                    for lane in range(8):
                        yield access(0, 12, layer, proj, row, block + lane, operator)
                else:
                    yield access(0, 1, layer, proj, row, block // 8, operator)
            if proj < 3:
                for lane in range(8):
                    yield access(0, 4, layer, proj, 0, block + lane, operator)
            for lane in range(8):
                yield access(1, 8, row=destination, col=block + lane, operator=operator)

    def rope(position):
        for slot, count in ((2, heads), (3, kv_heads)):
            for head in range(count):
                for pair in range(dimension // 2):
                    first = head * dimension + pair
                    other = first + dimension // 2
                    yield access(0, 8, row=slot, col=first, operator="rope")
                    yield access(0, 8, row=slot, col=other, operator="rope")
                    yield access(0, 11, row=position, col=2 * pair, operator="rope")
                    yield access(0, 11, row=position, col=2 * pair + 1, operator="rope")
                    yield access(1, 8, row=slot, col=first, operator="rope")
                    yield access(1, 8, row=slot, col=other, operator="rope")

    def attention(layer, position):
        for slot, kind in ((3, 9), (4, 10)):
            for index in range(kv_heads * dimension):
                yield access(0, 8, row=slot, col=index, operator="attention")
                yield access(1, kind, layer, row=position, col=index, operator="attention")
        for head in range(heads):
            kv = head // (heads // kv_heads)

            def score(time):
                for index in range(dimension):
                    yield access(0, 8, row=2, col=head * dimension + index, operator="attention")
                    yield access(0, 9, layer, row=time, col=kv * dimension + index,
                                 operator="attention")

            for time in range(position + 1):
                yield from score(time)
            for component in range(dimension):
                for time in range(position + 1):
                    yield from score(time)
                    yield access(0, 10, layer, row=time, col=kv * dimension + component,
                                 operator="attention")
                yield access(1, 8, row=5, col=head * dimension + component, operator="attention")

    def elementwise(operation):
        operator = "silu" if operation == 2 else "residual" + str(operation)
        for index in range(intermediate if operation == 2 else hidden):
            yield access(0, 8, row=(0, 7, 9)[operation], col=index, operator=operator)
            yield access(0, 8, row=(6, 12, 10)[operation], col=index, operator=operator)
            yield access(1, 8, row=(7, 0, 11)[operation], col=index, operator=operator)

    for position, token in enumerate(tokens):
        for index in range(hidden):
            yield access(0, 0, row=token, col=index, operator="embedding")
            yield access(1, 8, col=index, operator="embedding")
        for layer in range(layers):
            yield from norm(layer, 0, 1, 5)
            for proj in (0, 1, 2):
                yield from projection(layer, proj)
            yield from rope(position)
            yield from attention(layer, position)
            yield from projection(layer, 3)
            yield from elementwise(0)
            yield from norm(layer, 7, 8, 6)
            yield from projection(layer, 4)
            yield from projection(layer, 5)
            yield from elementwise(2)
            yield from projection(layer, 6)
            yield from elementwise(1)
        yield from norm(0, 0, 14, 7)
        for token_id in range(vocab):
            for index in range(hidden):
                yield access(0, 8, row=14, col=index, operator="logits")
                yield access(0, 0, row=token_id, col=index, operator="logits")


def audit_rows(rows, expected, allow_prefix):
    counts = Counter()
    previous = 0
    compared = 0
    for index, row in enumerate(rows):
        require(len(row) == 11, "architectural trace record width")
        begin, end = row[0] + (row[1] << 32), row[2] + (row[3] << 32)
        require(previous < begin < end, "architectural request/response order")
        previous = end
        wanted = next(expected, None)
        require(wanted is not None, "extra architectural memory transaction")
        actual = tuple(row[4:10])
        require(actual == wanted[:6],
                f"architectural address/order at transaction {index}: "
                f"observed={actual}, expected={wanted[:6]}, operator={wanted[6]}")
        counts[wanted[6]] += 1
        compared += 1
    require(compared > 0, "no architectural address comparisons")
    following = next(expected, None)
    require(allow_prefix or following is None, "incomplete architectural memory schedule")
    return {"transactions_compared": compared, "operator_transactions": dict(counts),
            "complete_memory_schedule": following is None,
            "last_response_cycle": previous,
            "next_expected": following, "complete_benchmark": False}


def binary_rows(path):
    from packed_storage import transactions
    yield from transactions(path)


def qualify(ev):
    for name, config in CONFIGURATIONS.items():
        for mode in range(3):
            model = Architecture(config, mode, 17)
            reference = [event[1:7] for event in model.execute() if event[0] == "M"]
            expected = list(schedule(config, mode,
                                     [position % config[7] for position in range(config[8])]))
            require([row[:6] for row in expected] == reference,
                    "streaming schedule differs from independent tensor model")
            rows = [((2*i+1), 0, (2*i+2), 0, *row, 0)
                    for i, row in enumerate(reference)]
            result = audit_rows(iter(rows), iter(expected), False)
            ev.assertion("synthetic_schedule_crosscheck_" + name + "_" + str(mode), True,
                         **result, no_rtl_execution=True)
            for label, index in (("projection", next(i for i, row in enumerate(expected)
                                                    if row[6] == "projection0")),
                                 ("rope", next(i for i, row in enumerate(expected)
                                              if row[6] == "rope")),
                                 ("kv", next(i for i, row in enumerate(expected)
                                            if row[1] == 9))):
                mutants = rows.copy()
                changed = list(mutants[index])
                changed[9] += 1
                mutants[index] = tuple(changed)
                fixture = ev.path / f"{name}-{mode}-{label}-mutant.json"
                write_json(fixture, {
                    "synthetic_observations": True, "no_rtl_execution": True,
                    "configuration": list(config), "mode": mode, "seed": 17,
                    "transaction_index": index, "original_record": rows[index],
                    "mutant_record": mutants[index],
                    "expected_address": expected[index][:6],
                    "generator_sha256": sha(ROOT / "tests/production_schedule.py"),
                    "unchanged_assertion": "architectural address/order",
                })
                try:
                    audit_rows(iter(mutants), iter(expected), False)
                except ValueError as error:
                    require("architectural address/order" in str(error),
                            "wrong synthetic schedule failure")
                    ev.assertion("reject_synthetic_schedule_" + name + "_" + str(mode) +
                                 "_" + label, True, diagnostic=str(error),
                                 fixture={"path": str(fixture.relative_to(ROOT)),
                                          "sha256": sha(fixture)},
                                 no_rtl_execution=True)
                else:
                    raise ValueError("synthetic address defect escaped architectural audit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualify", action="store_true")
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--tokens", type=Path)
    parser.add_argument("--mode", choices=tuple(MODES))
    parser.add_argument("--allow-prefix", action="store_true")
    args = parser.parse_args()
    ev = Evidence("production-schedule")
    passed = False
    try:
        if args.qualify:
            require(not args.trace and not args.tokens and not args.mode and
                    not args.allow_prefix, "qualification cannot replace a real trace audit")
            qualify(ev)
        else:
            require(args.trace and args.tokens and args.mode, "missing real schedule audit input")
            trace = artifact_path(ROOT, str(args.trace))
            tokens = artifact_path(ROOT, str(args.tokens))
            ev.receipt["data_sha256"] = {str(path.relative_to(ROOT)): sha(path)
                                         for path in (trace, tokens)}
            text = tokens.read_text().strip()
            selected = load_json(tokens) if text.startswith("[") else list(map(int, text.split()))
            result = audit_rows(binary_rows(trace),
                                schedule(PRODUCTION, MODES[args.mode], selected),
                                args.allow_prefix)
            write_json(ev.path / "comparisons.json", result)
            ev.assertion("production_public_architectural_address_schedule", True, **result)
        passed = True
    except (ValueError, OSError, KeyError, ImportError) as error:
        ev.assertion("schedule_audit_failure", False, diagnostic=str(error))
    finally:
        ev.finish("passed" if passed else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT)),
                          "complete_benchmark": False}), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
