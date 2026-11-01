"""Converter diagnostics use disposable synthetic inputs, never benchmark assets."""

import hashlib
from pathlib import Path
import random

from benchmarks import require
from reference import BF16, decode, dequant, encode_ratio


def exact_units(bits):
    sign, magnitude, power, special = decode(int(bits), BF16)
    require(special == "finite", "nonfinite diagnostic input")
    return (-1 if sign else 1) * (magnitude << (power + 133))


def rne(numerator, denominator):
    quotient, remainder = divmod(numerator, denominator)
    return quotient + (2 * remainder > denominator or
                       (2 * remainder == denominator and quotient & 1))


def oracle(values, width):
    integers = [exact_units(value) for value in values]
    low, high = min(0, *integers), max(0, *integers)
    limit = (1 << width) - 1
    scale, error = encode_ratio(False, high-low, limit, -133, BF16)
    require(not error, "diagnostic scale overflow")
    scale = max(scale, 1) if high != low else 0x3f80
    units = exact_units(scale)
    zero = max(0, min(limit, rne(-low, units)))
    codes = [max(0, min(limit, (-1 if value < 0 else 1) *
                       rne(abs(value), units) + zero)) for value in integers]
    reconstruction = [dequant(code, zero, scale) for code in codes]
    require(not any(error for _, error in reconstruction), "diagnostic reconstruction overflow")
    return codes, zero, scale, [bits for bits, _ in reconstruction]


def execute(run, binary):
    import numpy as np
    from quantized_checkpoint import packed, quantize
    rng = random.Random(211)
    fixtures = run.path / "checkpoint-images"
    fixtures.mkdir(exist_ok=False)
    table_rows, expected_hashes = [], []
    compared = 0
    for group in (1, 2, 8, 128):
        rows = []
        patterns = ([0], [0x8000], [1], [0x8001], [63, 0x8040],
                    [0x3f80, 0xbf80], [0x3f80, 0x3f81],
                    [0x0080, 0x8081], [0x3f80, 0x8001],
                    [0x0001, 0xbf80], [0x7f7f], [0xff7f])
        for pattern in patterns:
            rows.append([pattern[i % len(pattern)] for i in range(3 * group)])
        rows += [[rng.randrange(0x7e80) | (rng.randrange(2) << 15)
                  for _ in range(3 * group)] for _ in range(32)]
        source = np.array(rows, dtype="<u2")
        src_path = fixtures / f"source-g{group}.bf16"
        src_path.write_bytes(source.tobytes())
        for width in (4, 2):
            codes, zeros, scales, reconstruction = quantize(source, width, group)
            for row, values in enumerate(rows):
                for g in range(3):
                    q, z, s, decoded = oracle(values[g*group:(g+1)*group], width)
                    require(codes[row, g*group:(g+1)*group].tolist() == q and
                            int(zeros[row, g]) == z and int(scales[row, g]) == s and
                            reconstruction[row, g*group:(g+1)*group].tolist() == decoded,
                            f"independent Python group oracle W{width} G{group} row={row}")
                    compared += group
            paths = [fixtures / f"w{width}-g{group}-{suffix}"
                     for suffix in ("weights.bin", "zeros.bin", "scales.bf16")]
            for path, data in zip(paths, (packed(codes, width), packed(zeros, width),
                                         scales.astype("<u2").tobytes())):
                path.write_bytes(data)
            name = f"synthetic-w{width}-g{group}"
            fields = [name, width, group, run.relative(src_path), 0, len(rows), 3*group]
            for path in paths:
                fields.extend((run.relative(path), 0))
            table_rows.append("\t".join(map(str, fields)))
            expected_hashes.append(hashlib.sha256(reconstruction.astype("<u2").tobytes()).hexdigest())
    table = fixtures / "table.tsv"
    table.write_text("\n".join(table_rows) + "\n")
    _, stdout, _ = run.command([run.relative(binary), run.relative(table)],
                               "converter-directed-control")
    records = [line.split() for line in stdout.splitlines() if line.startswith("CHECK ")]
    require(len(records) == len(expected_hashes) and
            [row[-1] for row in records] == expected_hashes,
            "independent fixture reconstruction hashes mismatch")
    detections = []
    # Copies keep the successful control and all accepted/model inputs untouched.
    for role, filename, mask, diagnostic in (
            ("weight", "w4-g1-weights.bin", 1, "packed weight mismatch"),
            ("zero", "w4-g1-zeros.bin", 1, "zero byte mismatch"),
            ("scale", "w4-g1-scales.bf16", 1, "scale byte mismatch"),
            ("padding", "w2-g2-zeros.bin", 0x40, "nonzero metadata/payload padding")):
        original = fixtures / filename
        changed = fixtures / ("mutated-" + filename)
        payload = bytearray(original.read_bytes())
        payload[0] ^= mask
        changed.write_bytes(payload)
        mutation_table = fixtures / f"table-{role}.tsv"
        mutation_table.write_text(table.read_text().replace(run.relative(original),
                                                           run.relative(changed)))
        record, _, stderr = run.command([run.relative(binary), run.relative(mutation_table)],
                                        "converter-defect-" + role, check=False)
        require(record["exit_code"] == 1 and not record["timed_out"] and
                diagnostic in stderr, f"{role}: did not reach independent byte comparison")
        detections.append(role)
    bad = source.copy()
    bad[0, 0] = 0x7f80
    try:
        quantize(bad, 4, group)
    except ValueError as exc:
        require("nonfinite" in str(exc), "wrong invalid-input failure")
    else:
        raise ValueError("nonfinite input was accepted")
    run.receipt["converter_self_tests"] = {
        "exact_python_compared_weights": compared, "cpp_checked_tensors": len(records),
        "executed_byte_defect_detections": detections,
        "scope": "synthetic converter diagnostics only; not official model acceptance",
    }
    run.save()
