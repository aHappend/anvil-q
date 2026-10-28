"""Public-pin leaf numerical/latency scoreboards independent of implementation."""

from collections import Counter
import random

from execution import ROOT, sha256, write_json
from reference import encode_block, f16_q16


def packed(values, width):
    return sum((v & ((1 << width) - 1)) << (i * width) for i, v in enumerate(values))


def dot8_vectors(path, seed):
    rng = random.Random(seed)
    pipeline = [None] * 8
    rows = []
    bins = Counter()
    transactions = 0

    def emit(q=None, z=None, scales=None, activations=None, mask=255,
             valid=1, ready=1, flush=0, reset=1):
        nonlocal pipeline, transactions
        q = q if q is not None else [rng.randrange(16) for _ in range(8)]
        z = z if z is not None else [rng.randrange(16) for _ in range(8)]
        scales = scales if scales is not None else [rng.choice([0, 1, 0x3c00, 0x7bff, 0x0400])
                                                    for _ in range(8)]
        activations = activations if activations is not None else [
            rng.choice([-2147483648, 2147483647, -65536, 65536, -1, 0, 1,
                        rng.randrange(-2147483648, 2147483648)]) for _ in range(8)]

        def outputs():
            last = pipeline[-1]
            enable = last is None or ready
            if not reset or flush:
                return [0, 0, 0, 0]
            return [int(enable), int(last is not None), last[1] if last else 0,
                    (last[0] & ((1 << 72) - 1)) if last else 0]

        before = outputs()
        if not reset or flush:
            bins["reset" if not reset else "flush-occupancy-" + str(sum(v is not None for v in pipeline))] += 1
            pipeline = [None] * 8
        elif before[0]:
            transaction = None
            if valid:
                error = 0
                total = 0
                for lane in range(8):
                    if mask & (1 << lane):
                        try:
                            scale = f16_q16(scales[lane], scale=True)
                        except ValueError:
                            error = 1
                            scale = 0
                        total += (q[lane] - z[lane]) * scale * activations[lane]
                transaction = total, error
                transactions += 1
                bins["accepted"] += 1
                bins["invalid-scale" if error else "valid-scale"] += 1
            if pipeline[-1] is not None:
                bins["retired"] += 1
                if valid:
                    bins["simultaneous-retire-launch"] += 1
            pipeline = [transaction, *pipeline[:-1]]
        else:
            bins["stalled-occupancy-" + str(sum(v is not None for v in pipeline))] += 1
        after = outputs()
        rows.append([reset, flush, valid, ready, packed(q, 4), packed(z, 4),
                     packed(scales, 16), packed(activations, 32), mask,
                     *before, *after, transactions])

    emit(reset=0, valid=0)
    for lane in range(8):
        for qvalue in range(16):
            for zvalue in range(16):
                emit(q=[qvalue] * 8, z=[zvalue] * 8, scales=[0x3c00] * 8, mask=1 << lane)
                bins[f"lane-{lane}-q-{qvalue}-z-{zvalue}"] += 1
    for scale in (0, 0x8000, 1, 0x7bff, 0x8001, 0xbc00, 0x7c00, 0xfc00, 0x7e00):
        for lane in range(8):
            scales = [0x3c00] * 8
            scales[lane] = scale
            emit(scales=scales)
            emit(scales=scales, mask=255 ^ (1 << lane))
    for occupancy in range(1, 9):
        emit(flush=1)
        for _ in range(8 - occupancy):
            emit(valid=0)
        for _ in range(occupancy):
            emit()
        for _ in range(12):
            emit(ready=0, valid=0)
        for _ in range(9):
            emit(valid=0)
    for occupancy in range(9):
        emit(flush=1)
        for _ in range(occupancy):
            emit()
        emit(flush=1, ready=0)
        for _ in range(9):
            emit(valid=0)
    for _ in range(1024):
        emit(ready=int(rng.random() > .3), valid=int(rng.random() > .2),
             flush=int(rng.random() < .015), mask=rng.randrange(256))
    for _ in range(9):
        emit(valid=0)
    assert all(value is None for value in pipeline)
    assert bins["simultaneous-retire-launch"] > 100 and bins["invalid-scale"] > 0
    path.write_text("".join(" ".join(format(v, "x") for v in row) + "\n" for row in rows))
    return dict(bins), len(rows), transactions


def dot8_case(run, simulator, seed=17, rtl=None, must_fail=False):
    # Explicit names keep every tool output unique, including isolated mutations.
    folder = run.path / (f"dot8-{simulator}-{seed}" + ("-mutant" if must_fail else ""))
    folder.mkdir()
    vectors = folder / "vectors.txt"
    coverage, cycles, transactions = dot8_vectors(vectors, seed)
    write_json(folder / "inputs.json", {"seed": seed, "coverage": coverage,
                                      "vector_sha256": sha256(vectors)})
    source_paths = rtl if rtl is not None else [
        "rtl/anvil_q3_00_pkg.sv", "rtl/anvil_q3_awq_dot8.sv"]
    if simulator == "iverilog":
        binary = folder / "dot8.vvp"
        run.tool(["iverilog", "-g2012", "-Wall", "-s", "dot8_tb",
                  "-o", run.rel(binary), *source_paths, "tests/dot8_tb.sv"])
        command = ["vvp", run.rel(binary), "+vectors=" + run.rel(vectors)]
    else:
        obj = folder / "obj"
        run.tool(["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                  "--top-module", "dot8_tb", "--Mdir", run.rel(obj), "-o", "dot8",
                  *source_paths, "tests/dot8_tb.sv"])
        command = [run.rel(obj / "dot8"), "+vectors=" + run.rel(vectors)]
    text, receipt = run.tool(command, expected=(0, 1, -6) if must_fail else (0,))
    if must_fail:
        if receipt["exit_code"] == 0 or "DOT8 " not in text:
            raise AssertionError("mutation survived or failed for a nonassertion reason")
    elif f"DOT8_COMPLETE cycles={cycles} transactions={transactions}" not in text:
        raise AssertionError("missing exact comparison counts")
    result = {"simulator": simulator, "seed": seed, "cycles_compared": cycles,
              "accepted_transactions": transactions, "coverage": coverage,
              "functional_mutation_killed": must_fail, "stdout": receipt["stdout"]}
    write_json(folder / "result.json", result)
    return result


def codec_vectors(path, mode, asym, profile, block, seed):
    rng = random.Random(seed)
    cap = 1 if mode == 0 else (64 if mode == 2 else 32) if profile == 3 else block
    bits = 32 if mode == 0 else 8 if mode == 1 else 4
    vectors = []
    coverage = Counter()

    def row(decode, values, payload, metadata, expected_values=0, expected_payload=0,
            expected_metadata=0, error=0, count=cap, abort=0, label=""):
        vectors.append([decode, count, values, payload, metadata, error, expected_values,
                        expected_payload, expected_metadata, abort])
        coverage[label] += 1

    corpus = [[0] * cap, [-2147483648] * cap, [2147483647] * cap,
              [-2147483648, 2147483647] * (cap // 2) + ([1] if cap % 2 else [])]
    corpus += [[rng.randrange(-2147483648, 2147483648) for _ in range(cap)] for _ in range(16)]
    corpus += [[v] * cap for v in (-129, -128, -127, -8, -7, -1, 1, 7, 8, 127, 128, 129)]
    for exponent in range(1, 26 if mode == 1 else 30):
        corpus.append([max(-2147483648, min(2147483647,
                           (1 if lane % 2 else -1) * ((3 << exponent) + (1 << (exponent - 1)))))
                       for lane in range(cap)])
    for number, values in enumerate(corpus):
        size = min(len(values), cap) if number % 3 else min(cap, 2)
        values = values[:size]
        codes, metadata, decoded = encode_block(values, mode, bool(asym))
        payload = packed(codes, bits)
        row(0, packed(values, 32), 0, 0, expected_payload=payload,
            expected_metadata=metadata, count=size, label="encode")
        row(1, 0, payload, metadata, expected_values=packed(decoded, 32),
            expected_metadata=metadata if mode else 0, count=size, label="decode")
        if mode:
            row(1, 0, payload, metadata | (1 << 20), error=1, count=size, label="reserved-metadata")
            row(1, 0, payload, 255, error=1, count=size, label="exponent-out-of-range")
            if size < cap:
                row(1, 0, payload | (1 << (size * bits)), metadata, error=1,
                    count=size, label="nonzero-padding")
    if mode:
        row(1, 0, 0, 1, error=1, label="noncanonical-zero-block")
        row(1, 0, 1, 1 << 8, error=1, label="noncanonical-zero-code")
        if not asym:
            row(1, 0, 1 << (bits - 1), 0, error=1, label="forbidden-negative-code")
        row(1, 0, 1 << (cap * bits), 0, error=1, label="unused-transport-bits")
    row(0, 0, 0, 0, count=0, error=1, label="count-zero")
    row(0, 0, 0, 0, count=cap + 1, error=1, label="count-too-large")
    if mode:
        for stage in (1, cap, 2 * cap):
            row(0, packed([2147483647] * cap, 32), 0, 0, abort=stage, label="flush")
    path.write_text("".join(" ".join(format(v, "x") for v in vrow) + "\n" for vrow in vectors))
    return len(vectors), dict(coverage)


def codec_case(run, simulator, mode, asym=0, profile=3, block=1, seed=17,
               rtl=None, must_fail=False):
    folder = run.path / f"codec-p{profile}-m{mode}-a{asym}-c{block}-{simulator}-{seed}"
    folder.mkdir()
    vectors = folder / "vectors.txt"
    count, coverage = codec_vectors(vectors, mode, asym, profile, block, seed)
    write_json(folder / "inputs.json", {"seed": seed, "coverage": coverage,
                                      "vector_sha256": sha256(vectors)})
    parameters = {"PROFILE": profile, "CACHE_MODE": mode, "INT4_ASYM": asym, "CACHE_BLOCK": block}
    sources = rtl if rtl is not None else ["rtl/anvil_q3_cache_codec.sv"]
    if simulator == "iverilog":
        binary = folder / "codec.vvp"
        run.tool(["iverilog", "-g2012", "-Wall", "-s", "codec_tb", "-o", run.rel(binary),
                  *[f"-Pcodec_tb.{k}={v}" for k, v in parameters.items()],
                  *sources, "tests/codec_tb.sv"])
        command = ["vvp", run.rel(binary), "+vectors=" + run.rel(vectors)]
    else:
        obj = folder / "obj"
        run.tool(["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                  "--top-module", "codec_tb", "--Mdir", run.rel(obj), "-o", "codec",
                  *[f"-G{k}={v}" for k, v in parameters.items()],
                  *sources, "tests/codec_tb.sv"])
        command = [run.rel(obj / "codec"), "+vectors=" + run.rel(vectors)]
    text, receipt = run.tool(command, expected=(0, 1, -6) if must_fail else (0,))
    if must_fail:
        import re
        if receipt["exit_code"] == 0 or not re.search(r"CODEC case \d+ mismatch expected", text):
            raise AssertionError("codec mutation survived or failed without numerical assertion")
        return {"functional_mutation_killed": True, "assertion": text,
                "stdout": receipt["stdout"], "coverage_inputs": coverage}
    if f"CODEC_COMPLETE tests={count}" not in text:
        raise AssertionError("missing codec comparisons")
    result = {"simulator": simulator, **parameters, "seed": seed, "comparisons": count,
              "coverage": coverage, "stdout": receipt["stdout"]}
    write_json(folder / "result.json", result)
    return result
