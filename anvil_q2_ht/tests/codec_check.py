"""Independent dense Q16/raw-FP16/block-INT8 codec public-pin comparisons."""

import argparse
import hashlib
from pathlib import Path
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import pack_words, rhaz, sat32
from retention import Experiment


def encode_record(values, mode):
    if mode == 0:
        return pack_words(values, 32), list(values), 4 * len(values)
    if mode == 1:
        payloads = [value & 0xffff for value in values]
        return pack_words(payloads, 16), payloads, 2 * len(values)
    maximum = max(abs(value) for value in values)
    exponent = next((e for e in range(26) if maximum <= 127 * 2 ** e), 25)
    encoded = [max(-127, min(127, rhaz(value, exponent))) for value in values]
    record = bytes([exponent] + [value & 255 for value in encoded])
    return int.from_bytes(record, "little"), [sat32(value * 2 ** exponent)
                                             for value in encoded], 1 + len(values)


def decode_record(record, block, mode):
    if mode == 0:
        return [(record >> (32 * i)) & 0xffffffff for i in range(block)], False
    if mode == 1:
        return [(record >> (16 * i)) & 0xffff for i in range(block)], False
    exponent = record & 255
    values = [(record >> (8 * (i + 1))) & 255 for i in range(block)]
    invalid = exponent > 25 or 128 in values
    if invalid:
        return [0] * block, True
    return [sat32((value if value < 128 else value - 256) * 2 ** exponent)
            for value in values], False


def vectors(path, block):
    rows = []
    coverage = {"seeds": [11, 29, 101], "encode_modes": [0, 0, 0],
                "decode_modes": [0, 0, 0], "exponents": [], "invalid_decode": 0,
                "invalid_mode": 0, "raw_fp16_payloads": []}
    observed_exponents = set()
    raw_words = set()

    def add_encode(values, mode):
        record, decoded, length = encode_record(values, mode)
        rows.append((1, mode, pack_words(values, 32), 0, pack_words(decoded, 32),
                     record, length, 0))
        coverage["encode_modes"][mode] += 1
        if mode == 2:
            observed_exponents.add(record & 255)
        if mode == 1:
            raw_words.update(value & 0xffff for value in values)
        add_decode(record, mode)

    def add_decode(record, mode):
        decoded, invalid = decode_record(record, block, mode)
        length = (4 * block, 2 * block, 1 + block)[mode]
        rows.append((0, mode, 0, record, pack_words(decoded, 32), record, length, int(invalid)))
        coverage["decode_modes"][mode] += 1
        coverage["invalid_decode"] += int(invalid)

    for seed in coverage["seeds"]:
        rng = random.Random(seed)
        for exponent in range(26):
            threshold = min(127 * 2 ** exponent, (1 << 31) - 1)
            cases = [threshold, -threshold, max(0, threshold - 1),
                     min((1 << 31) - 1, threshold + 1)]
            for value in cases:
                data = [0] * block
                data[rng.randrange(block)] = value
                add_encode(data, 2)
            if exponent:
                tie = 3 * 2 ** (exponent - 1)
                data = [rng.choice((tie, -tie, threshold, -threshold)) for _ in range(block)]
                add_encode(data, 2)
        for value in (0, -1, 1, -(1 << 31), (1 << 31) - 1):
            add_encode([value] * block, 0)
            add_encode([value] * block, 2)
        for word in (0, 0x8000, 1, 0x8001, 0x3ff, 0x400, 0x7bff, 0xfbff,
                     0x7c00, 0xfc00, 0x7e00, 0xfe00, 0xffff):
            add_encode([word] * block, 1)
        for index in range(240):
            values = [rng.randint(-(1 << 31), (1 << 31) - 1) for _ in range(block)]
            add_encode(values, index % 3)
        for exponent in (26, 255):
            add_decode(exponent, 2)
        for lane in range(block):
            add_decode(128 << (8 * (lane + 1)), 2)
        for encode in (0, 1):
            rows.append((encode, 3, 0, 0, 0, 0, 0, 1))
            coverage["invalid_mode"] += 1
    if observed_exponents != set(range(26)):
        raise RuntimeError("independent stimulus did not encode every INT8 exponent")
    coverage["exponents"] = sorted(observed_exponents)
    coverage["raw_fp16_payloads"] = sorted(raw_words)
    width = block * 8
    with path.open("w") as stream:
        for encode, mode, data, record, decoded, expected_record, length, error in rows:
            stream.write(f"{encode} {mode} {data:0{width}x} {record:0{width}x} "
                         f"{decoded:0{width}x} {expected_record:0{width}x} {length} {error}\n")
    coverage["vectors"] = len(rows)
    coverage["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return coverage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--block", type=int, choices=(1, 16, 128), default=16)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    names = ["rtl/anvil_q2_ht_kv_codec.sv", "tests/codec_tb.sv",
             "tests/codec_check.py", "tests/reference.py", "tests/retention.py"]
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    try:
        for tool, flag in (("python3", "--version"), ("iverilog", "-V"), ("vvp", "-V")):
            experiment.run([tool, flag], tool + "-version")
        experiment.receipt["vectors"] = vectors(experiment.directory / "vectors.txt", args.block)
        binary = str(args.output / "codec.vvp")
        experiment.run(["iverilog", "-g2012", "-Wall", "-s", "codec_tb",
                        "-Pcodec_tb.CACHE_BLOCK=" + str(args.block), "-o", binary] +
                       [str(args.output / "sources" / name) for name in names[:2]], "compile")
        text = experiment.run(["vvp", binary,
                               "+vectors=" + str(args.output / "vectors.txt")], "simulate")
        count = experiment.receipt["vectors"]["vectors"]
        if f"accepted={count} compared={count} " not in text:
            raise RuntimeError("missing executed codec comparison count")
        experiment.receipt["comparison_summary"] = text.strip()
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
