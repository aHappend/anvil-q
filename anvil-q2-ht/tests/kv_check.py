"""Independent transaction-level hot-cache/backing-store comparisons."""

import argparse
import hashlib
from pathlib import Path
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from codec_check import encode_record
from reference import pack_words
from retention import Experiment


CELLS = {
    "singleton": (1, 8, 1, 1, 1, 1),
    "nonpower": (1, 8, 1, 1, 3, 3),
    "block16": (16, 128, 2, 2, 3, 3),
}


def vectors(path, cell, seed):
    block, dimension, layers, heads, sequence, hot = CELLS[cell]
    rng = random.Random(seed)
    base = 4096
    memory = bytearray([0xA5] * 65536)
    rows = []
    writes = 0
    counts = {"commands": 0, "commits": 0, "incomplete_commits": 0,
              "required_hits": 0, "required_misses": 0, "read_before_commit": 0,
              "backing_errors": 0, "held_request_invalidation": 0,
              "invalid_commands": 0, "cross_beat_records": 0,
              "commit_priority": 0, "writes": 0, "backing_read_errors": 0,
              "corrupt_backing_records": 0}
    pieces = [(value, head, part) for value in range(2)
              for head in range(heads) for part in range(dimension // block)]

    def stride(mode):
        size = heads * (dimension // block) * (
            4 * block if mode == 0 else 2 * block if mode == 1 else block + 1)
        return (size + 63) & ~63

    def emit(kind, mode, key=(0, 0, 0, 0, 0), write=0, values=None,
             result=None, error=0, transactions=(), optional=0,
             configuration=None):
        layer, position, value, head, part = key
        configured_base, length = configuration or (
            base, layers * 2 * sequence * stride(mode))
        data = pack_words(values or [0] * block, 32)
        expected = pack_words(result or [0] * block, 32)
        rows.append(
            f"{kind} {mode} {write} {value} {layer} {position} {head} {part} "
            f"{configured_base:x} {length:x} {data:x} {error} {expected:x} "
            f"{len(transactions)} {optional}\n")
        for request_write, address, payload, mask, response, response_error in transactions:
            rows.append(f"{request_write} {address:x} {payload:x} {mask:x} "
                        f"{response:x} {response_error}\n")
        counts["commands"] += 1

    def backing(mode, key, record, write, fail=False, cancel=False):
        nonlocal writes
        layer, position, value, head, part = key
        length = 4 * block if mode == 0 else 2 * block if mode == 1 else block + 1
        address = (base + ((layer * 2 + value) * sequence + position) * stride(mode)
                   + (head * (dimension // block) + part) * length)
        if address // 64 != (address + length - 1) // 64:
            counts["cross_beat_records"] += 1
        data = record.to_bytes(length, "little")
        requests = []
        for beat in range(address & ~63, (address + length + 63) & ~63, 64):
            payload = bytearray(64)
            mask = 0
            for offset in range(64):
                logical = beat + offset - address
                if 0 <= logical < length:
                    payload[offset] = data[logical]
                    mask |= 1 << offset
            if write:
                for offset in range(64):
                    if mask >> offset & 1:
                        memory[beat + offset] = payload[offset]
                writes += 1
            response = int.from_bytes(memory[beat:beat + 64], "little")
            requests.append((write, beat, int.from_bytes(payload, "little"),
                             mask if write else (1 << 64) - 1, response, int(fail)))
            if fail or cancel:
                break
        return requests

    def read(mode, key, stored, policy="optional"):
        record, decoded, _ = stored[key]
        requests = backing(mode, key, record, 0)
        if policy == "hit":
            requests = []
            counts["required_hits"] += 1
        elif policy == "miss":
            counts["required_misses"] += 1
        emit(0, mode, key, result=decoded, transactions=requests,
             optional=int(policy == "optional"))

    for mode in range(3):
        epoch = 0
        mode_start = writes
        while writes - mode_start < 380:
            emit(2, mode)
            stored = {}
            emit(5, mode, error=1)
            counts["commits"] += 1
            counts["incomplete_commits"] += 1
            counts["commit_priority"] += 1
            for layer in range(layers):
                for position in range(sequence):
                    shuffled = list(pieces)
                    rng.shuffle(shuffled)
                    for number, (value, head, part) in enumerate(shuffled):
                        key = layer, position, value, head, part
                        special = [0, 1, -1, -(1 << 31), (1 << 31) - 1,
                                   127, -127, 128, -128, 3 << 20, -(3 << 20)]
                        data = [special[(epoch + number + lane) % len(special)]
                                if lane % 2 == 0 else rng.randint(-(1 << 31), (1 << 31) - 1)
                                for lane in range(block)]
                        if mode == 1:
                            data = [rng.choice((0, 0x8000, 1, 0x3ff, 0x400, 0x7bff,
                                                0xfbff, 0x7c00, 0xfc00, 0x7e00, 0xffff))
                                    for _ in range(block)]
                        record, decoded, length = encode_record(data, mode)
                        stored[key] = record, decoded, length
                        emit(0, mode, key, write=1, values=data, result=decoded,
                             transactions=backing(mode, key, record, 1))
                        counts["writes"] += 1
                        if number == 0:
                            emit(1, mode, (layer, position, 0, 0, 0), error=1)
                            counts["commits"] += 1
                            counts["incomplete_commits"] += 1
                    last = (layer, position, *shuffled[-1])
                    emit(0, mode, last, error=1)
                    counts["read_before_commit"] += 1
                    emit(5, mode, (layer, position, 0, 0, 0))
                    counts["commits"] += 1
                    counts["commit_priority"] += 1
                    read(mode, last, stored, "hit")
                    read(mode, last, stored, "hit")
                    first = (layer, position, *shuffled[0])
                    read(mode, first, stored, "miss" if len(pieces) > hot else "optional")
                    for piece in pieces:
                        read(mode, (layer, position, *piece), stored)
                    emit(1, mode, (layer, position, 0, 0, 0), error=1)
                    counts["commits"] += 1
                    for key in ((layers, 0, 0, 0, 0), (0, sequence, 0, 0, 0),
                                (0, 0, 0, heads, 0),
                                (0, 0, 0, 0, dimension // block)):
                        emit(0, mode, key, error=1)
                        counts["invalid_commands"] += 1
            epoch += 1
        first = (0, 0, *pieces[0])
        record, _, _ = stored[first]
        emit(0, mode, first, error=1, transactions=backing(mode, first, record, 0, fail=True))
        counts["backing_read_errors"] += 1
        emit(0, mode, first, error=1)
        if mode == 2:
            for corrupt_offset, corrupt_byte in ((0, 26), (1, 128)):
                emit(2, mode)
                corrupt_stored = {}
                data = [3 << 20] * block
                for piece in pieces:
                    key = (0, 0, *piece)
                    record, decoded, length = encode_record(data, mode)
                    corrupt_stored[key] = record, decoded, length
                    emit(0, mode, key, write=1, values=data, result=decoded,
                         transactions=backing(mode, key, record, 1))
                    counts["writes"] += 1
                emit(1, mode)
                counts["commits"] += 1
                address = base + corrupt_offset
                memory[address] = corrupt_byte
                emit(4, mode, values=[corrupt_byte] + [0] * (block - 1),
                     configuration=(address, layers * 2 * sequence * stride(mode)))
                record, _, _ = corrupt_stored[first]
                emit(0, mode, first, error=1, transactions=backing(mode, first, record, 0))
                emit(0, mode, first, error=1)
                counts["corrupt_backing_records"] += 1
        emit(2, mode)
        data = [123456] * block
        record, decoded, _ = encode_record(data, mode)
        key = (0, 0, 0, 0, 0)
        emit(0, mode, key, write=1, values=data, error=1,
             transactions=backing(mode, key, record, 1, fail=True))
        counts["backing_errors"] += 1
        emit(1, mode, error=1)
        emit(0, mode, key, error=1)
        emit(3, mode, key, write=1, values=data,
             transactions=backing(mode, key, record, 1, cancel=True))
        counts["held_request_invalidation"] += 1
        emit(0, mode, key, error=1)
        for bad_mode, bad_configuration in (
                (3, None), (mode, (base + 1, 65536)),
                (mode, (base, 0)), (mode, ((1 << 33) - 64, 65536))):
            emit(0, bad_mode, key, error=1, configuration=bad_configuration)
            counts["invalid_commands"] += 1
    path.write_text("".join(rows))
    counts["expected_write_beats"] = writes
    counts["seed"] = seed
    counts["cell"] = cell
    counts["vectors_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cell", choices=CELLS, default="block16")
    parser.add_argument("--seed", choices=(11, 29, 101), type=int, default=11)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    names = ["rtl/anvil_q2_ht_kv_cache.sv", "rtl/anvil_q2_ht_kv_codec.sv",
             "tests/kv_tb.sv", "tests/kv_check.py", "tests/codec_check.py",
             "tests/reference.py", "tests/retention.py"]
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    try:
        for tool, flag in (("python3", "--version"), ("iverilog", "-V"), ("vvp", "-V")):
            experiment.run([tool, flag], tool + "-version")
        experiment.receipt["vectors"] = vectors(
            experiment.directory / "vectors.txt", args.cell, args.seed)
        parameters = zip(("CACHE_BLOCK", "HEAD_DIM", "NUM_LAYERS", "NUM_KV_HEADS",
                          "MAX_SEQ_LEN", "HOT_BLOCKS"), CELLS[args.cell])
        binary = str(args.output / "kv.vvp")
        experiment.run(["iverilog", "-g2012", "-Wall", "-s", "kv_tb", "-o", binary]
                       + [f"-Pkv_tb.{name}={value}" for name, value in parameters]
                       + [str(args.output / "sources" / name) for name in names[:3]], "compile")
        text = experiment.run(["vvp", binary, "+vectors=" + str(args.output / "vectors.txt"),
                               "+seed=" + str(args.seed)], "simulate")
        count = experiment.receipt["vectors"]["commands"]
        if f"KV_CHECKED operations={count} " not in text or "KV_COVERAGE " not in text:
            raise RuntimeError("missing executed KV comparisons/coverage")
        experiment.receipt["comparison_summary"] = text.strip()
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
