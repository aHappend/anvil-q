"""Cross-check lazy native-reference machinery against the exact reduced model.

This is an oracle self-check, not a substitute for RTL simulation or native
hardware benchmarks. Receipts explicitly distinguish its reference-only scope.
"""

import argparse
from array import array
import hashlib
from itertools import product
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp_reference import add, multiply
from native_reference import (
    NativeParentTransformer, NativeTransformer, TensorMemory, host_add, host_multiply,
    native_geometry,
)
from native_precision import NativeMathematicalTransformer
from high_precision_reference import MathematicalTransformer
from parent_reference import ParentTransformer
from retained import Run
from transformer_reference import Geometry, Transformer, key
from benchmark_checks import precision as materialized_precision


def arithmetic():
    directed = (
        0, 0x80000000, 1, 2, 3, 0x80000001, 0x007FFFFF, 0x00800000,
        0x33800000, 0x3F000000, 0x3F800000, 0x3F800001, 0x3F800002,
        0xBF800000, 0x7F7FFFFF, 0xFF7FFFFF, 0x7F800000, 0xFF800000,
        0x7FC00000, 0x7F800001, 0xFFC00000,
    )
    pairs = list(product(directed, repeat=2))
    random_source = random.Random(17)
    pairs.extend((random_source.getrandbits(32), random_source.getrandbits(32))
                 for _ in range(4096))
    for a, b in pairs:
        assert host_add(a, b) == add(a, b), f"host add differs: {a:08x} {b:08x}"
        assert host_multiply(a, b) == multiply(a, b), (
            f"host product differs: {a:08x} {b:08x}")
    return 2 * len(pairs)


def same_execution(expected, observed, parent=False):
    expected.execute()
    observed.execute()
    assert set(expected.writes) == set(observed.writes), "write-coordinate set differs"
    for address, values in expected.writes.items():
        assert values == list(observed.writes[address]), f"write sequence differs at {address:026x}"
    assert expected.logits == list(observed.logits), "logits differ"
    assert len(expected.stages) == len(observed.stages), "stage denominator differs"
    components = 0
    for a, b in zip(expected.stages, observed.stages):
        for field in ("domain", "layer", "position", "slot"):
            assert a[field] == b[field], f"stage {field} differs"
        bits = [x & 0xFFFFFFFF for x in a["q16"]] if parent else [
            int(x, 16) for x in a["fp32"]]
        assert bits == list(b["bits"]), "stage bits differ"
        components += len(bits)
    return components


def native_boundaries():
    g = native_geometry()
    assertions = 0
    for fmt, weights, seed in product(("bf16", "fp16"), (0, 1), (17, 43, 89)):
        memory = TensorMemory(fmt, weights, seed, g)
        for proj in range(7):
            inputs, outputs = memory.shape(proj)
            last_col = outputs - 1 if weights == 0 else (outputs - 1) // 8
            for layer, row, col in product((0, 27), (0, inputs - 1), (0, last_col)):
                bits = memory[key(1, layer, proj, row, col)]
                assert 0 <= bits <= 0xFFFFFFFF
                if weights == 0:
                    assert bits >> 16 == 0
                assertions += 1
            invalid = (
                key(1, 28, proj), key(1, 0, proj, inputs, 0),
                key(1, 0, proj, 0, last_col + 1),
            )
            for address in invalid:
                try:
                    memory[address]
                except KeyError:
                    assertions += 1
                else:
                    raise AssertionError("out-of-range native tensor read was accepted")
        for address in (
            key(0, row=g.vocabulary), key(0, col=g.hidden), key(7, layer=1),
            key(8), key(9), key(11, row=g.positions), key(11, col=g.head_dim),
            -1, 2**103,
        ):
            try:
                memory[address]
            except KeyError:
                assertions += 1
            else:
                raise AssertionError("unavailable coordinate was accepted")
    return assertions


def native_execution(fmt, weights, cache, seed):
    g = native_geometry()
    model = NativeTransformer(fmt, weights, cache, seed).execute()
    scratch = g.positions * (2 * g.hidden + g.layers * (
        9 * g.hidden + 3 * g.kv_heads * g.head_dim + 3 * g.intermediate))
    cache_words = (g.kv_heads * g.head_dim if cache == 0 else
                   2 * (g.kv_heads * g.head_dim // g.block) * ((g.block + 3) // 4 + 1))
    cache_writes = g.layers * g.positions * cache_words
    assert len(model.logits) == g.positions * g.vocabulary == 1215488
    assert len(model.stages) == g.positions * (2 + 15 * g.layers) == 3376
    assert sum(map(len, model.writes.values())) == scratch + cache_writes
    digest = hashlib.sha256()

    def network_bytes(vector):
        words = array("I", vector)
        if sys.byteorder != "big":
            words.byteswap()
        return words.tobytes()

    for address, vector in sorted(model.writes.items()):
        digest.update(address.to_bytes(13, "big"))
        digest.update(len(vector).to_bytes(4, "big"))
        digest.update(network_bytes(vector))
    digest.update(network_bytes(model.logits.bits))
    return dict(
        configuration=dict(fp_format=fmt, weight_mode=weights, cache_mode=cache, seed=seed),
        geometry=model.manifest()["geometry"], stages=len(model.stages),
        scratch_words=scratch, cache_write_words_including_metadata_padding=cache_writes,
        logits=len(model.logits), expected_write_and_logit_sha256=digest.hexdigest(),
        digest_encoding="ascending address, 13-byte address, 4-byte count, uint32 values; then logits; all big-endian",
        scope="Complete native-shape independent numerical graph; no RTL execution or native timing claim.")


def execute(native=False, fmt="fp16", weights=1, cache=1, seed=17):
    run = Run("verifier-native-reference-self-check")
    native_configuration = (fmt, weights, cache, seed)
    try:
        run.command(["python3", "--version"], "python-version")
        arithmetic_results = arithmetic()
        geometry = Geometry(layers=2, positions=2, vocabulary=4)
        loads = components = executions = 0
        for fmt, weights, cache in product(("bf16", "fp16"), (0, 1), (0, 1)):
            expected = Transformer(fmt, weights, cache, 43, geometry)
            observed = NativeTransformer(fmt, weights, cache, 43, geometry)
            for address, bits in expected.loads.items():
                assert observed.loads[address] == bits, f"lazy model load differs: {address:026x}"
                loads += 1
            components += same_execution(expected, observed)
            executions += 1
        for cache in (0, 1):
            expected = ParentTransformer(cache, 89, geometry)
            observed = NativeParentTransformer(cache, 89, geometry)
            for address, bits in expected.loads.items():
                assert observed.loads[address] == bits, f"lazy parent load differs: {address:026x}"
                loads += 1
            components += same_execution(expected, observed, parent=True)
            executions += 1
        bounds = native_boundaries()
        mathematical = MathematicalTransformer(17, geometry).execute()
        lazy_mathematical = NativeMathematicalTransformer(17, geometry).execute()
        assert mathematical.stages == lazy_mathematical.stages, "lazy mathematical stages differ"
        assert mathematical.logits == lazy_mathematical.logits, "lazy mathematical logits differ"
        observed_math = NativeMathematicalTransformer(
            89, geometry, observations=observed, parent=True).execute()
        precision = observed_math.precision()
        assert len(precision) == 5 and all(row["values_compared"] > 0 for row in precision.values())
        original_precision = materialized_precision(
            {"stages": expected.stages, "logits": [list(item) for item in expected.logits]},
            MathematicalTransformer(89, geometry).execute(), "parent")
        for domain, metrics in original_precision.items():
            for field, number in metrics.items():
                observed_number = precision[domain][field]
                if number is None:
                    assert observed_number is None
                else:
                    assert math.isclose(number, observed_number, rel_tol=1e-12, abs_tol=1e-15), (
                        f"streaming precision differs: {domain}: {field}")
        native_result = native_execution(*native_configuration) if native else None
        if native_result is not None:
            summary = run.path / "native-reference-summary.json"
            with summary.open("x") as stream:
                json.dump(native_result, stream, indent=2)
                stream.write("\n")
            run.receipt["generated_sha256"] = {
                run.relative(summary): hashlib.sha256(summary.read_bytes()).hexdigest()}
        run.finish("passed-focused-only", metrics={
            "host_arithmetic_results_compared": arithmetic_results,
            "model_loads_compared": loads, "stage_components_compared": components,
            "complete_reduced_reference_graphs_compared": executions,
            "native_coordinate_boundary_assertions": bounds,
            "native_reference_execution": native_result,
            "mathematical_stage_components_compared": sum(
                len(stage["real"]) for stage in mathematical.stages),
            "streaming_parent_precision": precision,
        }, limitations="Reference self-check only; no RTL or native hardware execution in this probe.")
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError, KeyError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", action="store_true")
    parser.add_argument("--format", choices=("bf16", "fp16"), default="fp16")
    parser.add_argument("--weights", type=int, choices=(0, 1), default=1)
    parser.add_argument("--cache", type=int, choices=(0, 1), default=1)
    parser.add_argument("--seed", type=int, choices=(17, 43, 89), default=17)
    args = parser.parse_args()
    raise SystemExit(execute(args.native, args.format, args.weights, args.cache, args.seed))
