#!/usr/bin/env python3
"""Bounded no-inference/no-RTL tests for the proposed packed evidence format."""

import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import random
import struct
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import Validator, artifact_path, load_json, require, sha
from packed_storage import (CHUNK_BYTES, END, ENTRY, FOOTER, HEADER_LIMIT, MAGIC,
                            RECORD, Reader, Writer, array_bytes, array_descriptor,
                            bound, delta_decode,
                            delta_encode, dimensions, pack_array, take_varint,
                            transactions, varint)
from verify import Evidence, ROOT


def worker(destination):
    destination.mkdir(parents=True, exist_ok=False)
    report = {"schema": 1, "acceptance_evidence": False,
              "scope": "synthetic codec only; no RTL, inference, collection or result assembly",
              "positive_cases": [], "rejections": []}

    def reject(name, function, errors=(ValueError,)):
        try:
            function()
        except errors as error:
            report["rejections"].append({"name": name, "diagnostic": str(error)})
        else:
            raise ValueError("packed storage defect was not rejected: " + name)

    def put(name, data):
        path = destination / name
        with path.open("xb") as stream:
            stream.write(data)
        return path

    def decoded(path):
        return b"".join(Reader(path).chunks())

    # Bit patterns, not float conversions: include both zeros, denormals,
    # infinities and multiple signaling/quiet NaN payloads in both widths.
    patterns = {
        "<f4": (0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x00800000,
                0x3f800000, 0x7f7fffff, 0x7f800000, 0xff800000, 0x7f800001,
                0x7fc01234, 0xffc04321),
        "<f8": (0, 0x8000000000000000, 1, 0x8000000000000001, 0xfffffffffffff,
                0x10000000000000, 0x3ff0000000000000, 0x7fefffffffffffff,
                0x7ff0000000000000, 0xfff0000000000000, 0x7ff0000000000001,
                0x7ff8123456789abc, 0xfff823456789abcd),
    }
    rng = random.Random(17)
    for dtype, words in patterns.items():
        width = 8 if dtype == "<f8" else 4
        raw = b"".join(word.to_bytes(width, "little") for word in words)
        source = put(dtype[1:] + "-bits.raw", raw)
        path = destination / (dtype[1:] + "-bits.aqp")
        pack_array(source, path, dtype, [len(words)], ["element"])
        require(decoded(path) == raw and Reader(path).read(0, len(raw)) == raw,
                "floating-point payload bits changed")
        report["positive_cases"].append({"name": dtype + "-special-bits",
                                         "compared_bytes": len(raw)})

    # Independently construct a C-order 3D array with unique per-coordinate words.
    # Distinct extents catch axis swaps. Include cross-chunk and strided reads.
    shape, axes = [3, 5, 12001], ["position", "layer", "component"]
    raw = b"".join(struct.pack("<Q", (p << 48) | (layer << 32) | component)
                   for p in range(shape[0]) for layer in range(shape[1])
                   for component in range(shape[2]))
    source = put("coordinate-array.raw", raw)
    path = destination / "coordinate-array.aqp"
    pack_array(source, path, "<f8", shape, axes)
    reader = Reader(path, dtype="<f8", shape=shape, axes=axes)
    require(decoded(path) == raw, "complete 3D raw offset traversal differs")
    for origin, extent, steps in (
            ([0, 0, 0], [3, 5, 12001], [1, 1, 1]),
            ([1, 2, 11997], [2, 2, 2], [1, 2, 2]),
            ([0, 1, 130], [2, 3, 100], [2, 1, 19]),
            ([2, 4, 12000], [1, 1, 1], [1, 1, 1])):
        expected = b"".join(struct.pack("<Q", (p << 48) | (layer << 32) | component)
                            for p in range(origin[0], origin[0] + extent[0] * steps[0], steps[0])
                            for layer in range(origin[1], origin[1] + extent[1] * steps[1], steps[1])
                            for component in range(origin[2], origin[2] + extent[2] * steps[2], steps[2]))
        actual = reader.view(origin, extent, steps)
        require(actual == expected, "strided 3D coordinate view differs")
        report["positive_cases"].append({"name": "3D-view", "origin": origin,
                                         "shape": extent, "steps": steps,
                                         "compared_bytes": len(actual)})
    offset = CHUNK_BYTES - 16
    require(reader.read(offset, 64) == raw[offset:offset + 64], "cross-chunk read differs")
    reject("wrong-axis-order", lambda: Reader(path, dtype="<f8", shape=shape,
                                              axes=["layer", "position", "component"]))
    reject("wrong-shape", lambda: Reader(path, dtype="<f8", shape=[5, 3, 12001], axes=axes))
    for name, origin, extent, steps in (
            ("negative-origin", [-1, 0, 0], [1, 1, 1], None),
            ("end-overflow", [2, 4, 12000], [1, 1, 2], None),
            ("boolean-origin", [True, 0, 0], [1, 1, 1], None),
            ("stride-overflow", [0, 0, 0], [2, 1, 1], [3, 1, 1]),
            ("zero-stride", [0, 0, 0], [1, 1, 1], [0, 1, 1]),
            ("wrong-rank", [0], [1], None)):
        reject(name, lambda origin=origin, extent=extent, steps=steps:
               reader.view(origin, extent, steps))
    for name, offset_, length in (("unaligned-offset", 1, 8), ("unaligned-count", 0, 1),
                                  ("read-overrun", len(raw), 8), ("negative-count", 0, -8)):
        reject(name, lambda offset_=offset_, length=length: reader.read(offset_, length))

    # Vocabulary-major logits: extracting one position must stride over positions,
    # not reinterpret the flat payload as position-major.
    raw_logits = b"".join(struct.pack("<Q", v * 13 + p)
                          for v in range(10007) for p in range(13))
    logits = destination / "vocabulary-major.aqp"
    with Writer(logits, dtype="<f8", shape=[10007, 13],
                axes=["vocabulary", "position"]) as output:
        output.append(raw_logits)
    for position in (0, 5, 12):
        observed = Reader(logits).view([0, position], [10007, 1])
        expected = b"".join(struct.pack("<Q", v * 13 + position) for v in range(10007))
        require(observed == expected, "vocabulary-major position offsets differ")
        report["positive_cases"].append({"name": "vocabulary-position-view",
                                         "position": position, "compared_bytes": len(observed)})

    # Incompressible raw fallback must never exceed the proven format bound.
    for number, count in enumerate((4, CHUNK_BYTES, CHUNK_BYTES + 12)):
        raw_noise = rng.randbytes(count)
        noise = destination / f"noise-{number}.aqp"
        with Writer(noise, dtype="<f4", shape=[count // 4], axes=["word"]) as output:
            for start in range(0, count, 32768):
                output.append(raw_noise[start:start + 32768])
        require(decoded(noise) == raw_noise and noise.stat().st_size <= bound(count) and
                any(entry[3] == 0 for entry in Reader(noise).entries),
                "raw fallback/bound differs")
        report["positive_cases"].append({"name": "raw-fallback-bound", "raw_bytes": count,
                                         "actual_bytes": noise.stat().st_size, "bound": bound(count)})

    # Complete independent repeats remain independently written payload files.
    repeats = []
    for repeat in range(2):
        repeat_path = destination / f"independent-repeat-{repeat}.aqp"
        with Writer(repeat_path, dtype="<f8", shape=[len(patterns["<f8"])],
                    axes=["element"]) as output:
            output.append((destination / "f8-bits.raw").read_bytes())
        repeats.append(repeat_path)
    require(repeats[0].stat().st_ino != repeats[1].stat().st_ino and
            decoded(repeats[0]) == decoded(repeats[1]), "independent repeat was aliased")
    reject("exclusive-output", lambda: Writer(repeats[0], dtype="<f8", shape=[1], axes=["x"]),
           errors=(FileExistsError,))
    reject("dimension-overflow", lambda: dimensions("<f8", [1 << 62], ["x"]))
    reject("boolean-dimension", lambda: dimensions("<f8", [True], ["x"]))
    reject("duplicate-axes", lambda: dimensions("<f8", [2, 2], ["x", "x"]))

    # Regenerate valid outer hashes for structural mutations so checks cannot
    # merely rely on one enclosing digest to reject malformed indices.
    pristine = path.read_bytes()
    prefix_size = 12 + struct.unpack("<I", pristine[8:12])[0]
    index_start, entry_count, total, _, _ = FOOTER.unpack(pristine[-FOOTER.size:])
    entries = [list(entry) for entry in ENTRY.iter_unpack(pristine[index_start:-FOOTER.size])]

    def index_mutant(name, mutate):
        changed = copy.deepcopy(entries)
        mutate(changed)
        index = b"".join(ENTRY.pack(*entry) for entry in changed)
        payload = pristine[:index_start] + index + FOOTER.pack(
            index_start, entry_count, total,
            hashlib.sha256(pristine[:prefix_size] + index).digest(), END)
        mutant = put(name + ".aqp", payload)
        reject(name, lambda: decoded(mutant))

    index_mutant("overlapping-offset", lambda rows: rows[1].__setitem__(0, rows[0][0]))
    index_mutant("skipped-offset", lambda rows: rows[0].__setitem__(0, rows[0][0] + 1))
    index_mutant("reordered-index", lambda rows: rows.reverse())
    index_mutant("decoded-size", lambda rows: rows[0].__setitem__(2, rows[0][2] - 8))
    index_mutant("encoded-size-overflow", lambda rows: rows[0].__setitem__(1, (1 << 64) - 1))
    index_mutant("wrong-codec", lambda rows: rows[0].__setitem__(3, 255))
    index_mutant("raw-hash", lambda rows: rows[0].__setitem__(5, b"\x00" * 32))
    for name, mutant in (
            ("truncated-magic", pristine[:7]),
            ("truncated-header", pristine[:prefix_size - 1]),
            ("truncated-payload", pristine[:index_start - 1]),
            ("truncated-index", pristine[:-FOOTER.size - 1]),
            ("truncated-footer", pristine[:-1]),
            ("appended-junk", pristine + b"x"),
            ("version", b"AQPACK99" + pristine[8:]),
            ("bad-header", pristine[:13] + bytes([pristine[13] ^ 1]) + pristine[14:]),
            ("bad-index-hash", pristine[:-40] + bytes([pristine[-40] ^ 1]) + pristine[-39:])):
        damaged = put(name + ".aqp", mutant)
        reject(name, lambda damaged=damaged: decoded(damaged))
    payload_damage = bytearray(pristine)
    payload_damage[prefix_size] ^= 1
    damaged = put("damaged-payload.aqp", payload_damage)
    reject("payload-bit-flip", lambda: decoded(damaged))

    # Construct records independently, exercising every u32 field and both halves
    # of 64-bit cycles. Alternating fields exercise negative and positive deltas.
    record_rows = []
    cycle = (1 << 32) - 5
    for index in range(CHUNK_BYTES // 44 + 17):
        accepted = cycle + index % 7
        completed = accepted + 1 + index % 11
        fields = (index % 2, (0xffffffff if index % 2 else 0), index % 24,
                  index % 7, index * 7919 & 0xffffffff,
                  (0xffffffff - index * 17) & 0xffffffff, rng.getrandbits(32))
        record_rows.append((accepted & 0xffffffff, accepted >> 32,
                            completed & 0xffffffff, completed >> 32, *fields))
        cycle = completed
    record_rows.append((0xfffffffe, 0xffffffff, 0xffffffff, 0xffffffff,
                        1, 0, 0, 0, 0, 0, 0xffffffff))
    records = b"".join(RECORD.pack(*row) for row in record_rows)
    trace = destination / "transactions.aqp"
    with Writer(trace, transactions=True) as output:
        for start in range(0, len(records), 44 * 37):
            output.append(records[start:start + 44 * 37])
    require(list(transactions(trace)) == record_rows and decoded(trace) == records and
            trace.stat().st_size <= bound(len(records), transactions=True),
            "transaction fields/order/cycles changed")
    legacy = put("transactions.u32.gz", gzip.compress(records, mtime=0))
    require(list(transactions(legacy)) == record_rows, "backward gzip reader differs")
    report["positive_cases"].append({"name": "trace-lossless-and-legacy",
                                     "records": len(record_rows), "decoded_bytes": len(records),
                                     "actual_bytes": trace.stat().st_size,
                                     "bound": bound(len(records), transactions=True)})

    first = RECORD.pack(*record_rows[0])
    second = RECORD.pack(*record_rows[1])
    for name, data in (("partial-record", first[:-1]), ("reordered-record", second + first),
                        ("duplicate-record", first + first),
                        ("invalid-write", RECORD.pack(*record_rows[0][:4], 2,
                                                     *record_rows[0][5:]))):
        reject(name, lambda data=data: delta_encode(data))
    for value in (0, 1, 127, 128, (1 << 32) - 1, (1 << 64) - 1):
        require(take_varint(varint(value), 0) == (value, len(varint(value))),
                "varint boundary differs")
    for name, data in (("varint-overflow", b"\xff" * 9 + b"\x02"),
                        ("varint-unterminated", b"\xff" * 10),
                        ("varint-truncated", b"\x80"),
                        ("varint-noncanonical", b"\x80\x00")):
        reject(name, lambda data=data: take_varint(data, 0))
    reject("encode-varint-overflow", lambda: varint(1 << 64))
    reject("delta-trailing-bytes", lambda: delta_decode(delta_encode(first) + b"x", 1))
    reject("delta-truncated-payload", lambda: delta_decode(delta_encode(first)[:-1], 1))
    cycle_overflow = varint((1 << 64) - 1) + varint(1) + b"\x00" * 6 + b"\x00" * 4
    reject("delta-cycle-overflow", lambda: delta_decode(cycle_overflow, 1))
    field_overflow = b"\x00\x01" + varint(1 << 33) + b"\x00" * 5 + b"\x00" * 4
    reject("delta-field-overflow", lambda: delta_decode(field_overflow, 1))
    bad_zlib = zlib.compress(delta_encode(first)) + b"x"
    from packed_storage import inflate
    reject("compressed-trailing-stream", lambda: inflate(bad_zlib, 54))
    reject("compressed-expansion", lambda: inflate(zlib.compress(b"x" * 1024), 54))

    class Inputs:
        def __init__(self):
            self.receipt = {}

    validator = Validator(ROOT, Inputs())
    actual_path = destination / "validator-actual.aqp"
    reference_path = destination / "validator-reference.aqp"
    repeat_path = destination / "validator-repeat.aqp"
    for selected_path, dtype in ((actual_path, "<f4"), (repeat_path, "<f4"),
                                 (reference_path, "<f8")):
        encoding = "f" if dtype == "<f4" else "d"
        with Writer(selected_path, dtype=dtype, shape=[2, 3],
                    axes=["position", "component"]) as output:
            output.append(struct.pack("<6" + encoding, 1., -2., 3., 1., -2., -3.))
    actual = array_descriptor(ROOT, actual_path, origin=[0, 0], shape=[1, 3])
    repeated = array_descriptor(ROOT, repeat_path, origin=[0, 0], shape=[1, 3])
    reference = array_descriptor(ROOT, reference_path, origin=[0, 0], shape=[1, 3])
    validator.arrays(actual, reference, repeated, 3, (.9999, .002), "packed-pristine")
    flat_actual = put("validator-legacy.f32", struct.pack("<3f", 1., -2., 3.))
    flat_reference = put("validator-legacy.f64", struct.pack("<3d", 1., -2., 3.))
    legacy_actual = {"path": str(flat_actual.relative_to(ROOT)), "sha256": sha(flat_actual)}
    legacy_reference = {"path": str(flat_reference.relative_to(ROOT)), "sha256": sha(flat_reference)}
    validator.arrays(legacy_actual, reference, repeated, 3, (.9999, .002), "mixed-formats")
    validator.arrays(actual, legacy_reference, legacy_actual, 3, (.9999, .002), "legacy-reference")
    changed_view = array_descriptor(ROOT, actual_path, origin=[1, 0], shape=[1, 3])
    reject("same-container-different-repeat-view", lambda: validator.arrays(
        actual, reference, changed_view, 3, (.9999, .002), "view-repeat-mutant"))
    reject("numerical-defect-packed-view", lambda: validator.arrays(
        changed_view, reference, changed_view, 3, (.9999, .002), "numerical-mutant"))
    for name, key, value in (
            ("descriptor-wrong-shape", "array_shape", [3, 2]),
            ("descriptor-wrong-axes", "axes", ["component", "position"]),
            ("descriptor-wrong-dtype", "dtype", "<f8"),
            ("descriptor-wrong-decoded-hash", "decoded_sha256", "0" * 64),
            ("descriptor-unknown-format", "format", "unknown"),
            ("descriptor-missing-index", "origin", None)):
        mutant = copy.deepcopy(actual)
        mutant["storage"][key] = value
        reject(name, lambda mutant=mutant: validator.array_bytes(mutant, "<f4", 3))
    reject("descriptor-width-overflow", lambda: array_bytes(actual_path, actual, "<f4", 6))
    changed_binding = copy.deepcopy(actual)
    changed_binding["sha256"] = "0" * 64
    reject("descriptor-outer-file-hash", lambda: validator.array_bytes(changed_binding, "<f4", 3))
    report["positive_cases"].append({"name": "unchanged-validator-numerics",
                                     "comparisons": 3, "minimum_cosine": .9999,
                                     "maximum_normalized_error": .002})

    # A complete read must check cycle ordering across chunk boundaries, not only
    # within each delta frame. Both chunks below have valid internal hashes.
    split = destination / "cross-chunk-order.aqp"
    with Writer(split, transactions=True) as output:
        output.append(records)
    split_bytes = split.read_bytes()
    start, count, total, _, _ = FOOTER.unpack(split_bytes[-FOOTER.size:])
    split_entries = [list(entry) for entry in ENTRY.iter_unpack(split_bytes[start:-FOOTER.size])]
    # Replace the second chunk's contents with valid earlier records of its size.
    count_raw = split_entries[1][2] // 44
    early = b"".join(RECORD.pack(*row) for row in record_rows[:count_raw])
    encoded = zlib.compress(delta_encode(early), 6)
    entry = split_entries[1]
    entry[1], entry[3], entry[4], entry[5] = len(encoded), 2, hashlib.sha256(encoded).digest(), hashlib.sha256(early).digest()
    prefix = split_bytes[:entry[0]] + encoded
    index = b"".join(ENTRY.pack(*row) for row in split_entries)
    footer = FOOTER.pack(len(prefix), count, total,
                         hashlib.sha256(split_bytes[:12 + struct.unpack("<I", split_bytes[8:12])[0]] +
                                        index).digest(), END)
    reordered = put("cross-chunk-reordered.aqp", prefix + index + footer)
    reject("cross-chunk-transaction-order", lambda: list(transactions(reordered)))
    report["tools"] = {"python": sys.version, "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION}
    report["full_workload_capacity_qualified"] = False
    report["production_format_enabled"] = False
    with (destination / "qualification.json").open("x") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--repair-of", type=Path)
    args = parser.parse_args()
    if args.worker:
        require(args.destination is not None, "packed diagnostic destination missing")
        worker(artifact_path(ROOT, str(args.destination)))
        return 0
    require(args.destination is None, "destination is worker-only")
    ev = Evidence("packed-storage")
    passed = False
    try:
        ev.receipt["scope"] = "bounded codec diagnostics only; collection remains paused"
        ev.receipt["tool_versions"] = {"python": sys.version, "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION}
        if args.repair_of:
            previous = artifact_path(ROOT, str(args.repair_of))
            require(load_json(previous)["status"] == "failed", "repair link did not fail")
            ev.receipt["repair_of"] = {"path": str(args.repair_of), "sha256": sha(previous)}
        passed = ev.run("codec-roundtrip-corruption", [
            sys.executable, "tests/packed_storage_checks.py", "--worker", "--destination",
            str((ev.path / "synthetic").relative_to(ROOT))], timeout=3600)
        ev.assertion("packed_codec_roundtrip_and_corruption", passed,
                     full_workload_capacity_qualified=False, collection_resumption_authorized=False)
        if passed:
            ev.receipt["qualification"] = load_json(ev.path / "synthetic/qualification.json")
    except (ValueError, OSError, KeyError) as error:
        ev.assertion("packed_codec_diagnostic_exception", False, diagnostic=repr(error))
    finally:
        ev.receipt["outputs"] = {str(path.relative_to(ROOT)): sha(path)
                                 for path in ev.path.rglob("*")
                                 if path.is_file() and path.name != "receipt.json"}
        ev.finish("passed" if passed else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
