#!/usr/bin/env python3
"""Qualify lossless FP64 preparation storage; never produce benchmark results."""

import argparse
import hashlib
import json
import lzma
import math
from pathlib import Path
import shutil
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import load_json, require, sha
from benchmark_inputs import checked_payload, write_json
from verify import Evidence, ROOT


MODES = ("checkpoint", "bf16", "fp16", "w4a16")
CHUNK_VALUES = 32768


def hashed(data):
    return hashlib.sha256(data).hexdigest()


def shuffle(data):
    require(len(data) % 8 == 0, "FP64 bytes are not aligned")
    return b"".join(data[index::8] for index in range(8))


def unshuffle(data):
    require(len(data) % 8 == 0, "shuffled FP64 bytes are not aligned")
    output = bytearray(len(data))
    count = len(data) // 8
    for index in range(8):
        output[index::8] = data[index * count:(index + 1) * count]
    return bytes(output)


def xor(left, right):
    require(len(left) == len(right), "delta byte count differs")
    return bytes(a ^ b for a, b in zip(left, right))


def compress(data, codec):
    return zlib.compress(data, 6) if codec == "zlib" else lzma.compress(data, preset=1)


def decompress(data, codec, expected):
    # Bound the decoder, require the stream footer, and reject trailing bytes.
    decoder = zlib.decompressobj() if codec == "zlib" else lzma.LZMADecompressor()
    try:
        output = decoder.decompress(data, max_length=expected + 1)
    except (zlib.error, lzma.LZMAError) as error:
        raise ValueError("invalid compressed reference chunk") from error
    require(decoder.eof and not decoder.unused_data and len(output) == expected,
            "truncated, oversized or trailing compressed chunk")
    return output


def validate_shape(shape, axes):
    require(isinstance(shape, list) and shape and
            all(type(value) is int and value > 0 for value in shape),
            "invalid reference dimensions")
    require(isinstance(axes, list) and len(axes) == len(shape) and
            len(set(axes)) == len(axes) and all(isinstance(axis, str) for axis in axes),
            "invalid reference axes")


def write_archive(destination, arrays, shape, axes, codec):
    """Store every mode, optionally using exact byte deltas against checkpoint."""
    require(codec in ("zlib", "lzma"), "unsupported codec")
    validate_shape(shape, axes)
    size = math.prod(shape) * 8
    require(set(arrays) == set(MODES) and all(path.stat().st_size == size
            for path in arrays.values()), "reference dimensions disagree with file length")
    destination.mkdir(parents=True, exist_ok=False)
    index = {"schema": 1, "purpose": "lossless-reference-preparation",
             "acceptance_evidence": False, "dtype": "<f8", "shape": shape,
             "axes": axes, "codec": codec, "chunk_values": CHUNK_VALUES,
             "modes": {}}
    with (destination / "chunks.bin").open("xb") as output:
        for mode in MODES:
            chunks = []
            with arrays[mode].open("rb") as source, arrays["checkpoint"].open("rb") as base:
                while raw := source.read(CHUNK_VALUES * 8):
                    original = compress(shuffle(raw), codec)
                    base_raw = base.read(len(raw))
                    delta = xor(raw, base_raw)
                    candidate = compress(shuffle(delta), codec)
                    method, encoded = ("direct", original)
                    if mode != "checkpoint":
                        if raw == base_raw:
                            method, encoded = "identical-checkpoint", b""
                        elif len(candidate) < len(original):
                            method, encoded = "xor-checkpoint", candidate
                    offset = output.tell()
                    output.write(encoded)
                    chunks.append({"offset": offset, "length": len(encoded),
                                   "decoded_bytes": len(raw), "transform": method,
                                   "decoded_sha256": hashed(raw),
                                   "encoded_sha256": hashed(encoded)})
            index["modes"][mode] = {"sha256": sha(arrays[mode]), "bytes": size, "chunks": chunks}
    index["payload_sha256"] = sha(destination / "chunks.bin")
    write_json(destination / "index.json", index)
    return index


def read_archive(directory, shape, axes, observe, index=None, payload=None):
    """Strict bounded decode, externally checking the required dimensions/axis order."""
    index = load_json(directory / "index.json") if index is None else index
    validate_shape(shape, axes)
    require(index["schema"] == 1 and index["dtype"] == "<f8" and
            index["shape"] == shape and index["axes"] == axes and
            index["chunk_values"] == CHUNK_VALUES and
            index["codec"] in ("zlib", "lzma") and set(index["modes"]) == set(MODES),
            "reference storage schema, dimensions or axes differ")
    payload = directory / "chunks.bin" if payload is None else payload
    require(sha(payload) == index["payload_sha256"], "compressed payload hash differs")
    total = math.prod(shape) * 8
    expected_offset = 0
    chunks_count = (total + CHUNK_VALUES * 8 - 1) // (CHUNK_VALUES * 8)
    base_chunks = index["modes"]["checkpoint"]["chunks"]

    def decode_chunk(stream, chunk, count):
        require(type(chunk["offset"]) is int and chunk["offset"] >= 0 and
                type(chunk["length"]) is int and 0 <= chunk["length"] <= count + 65536 and
                chunk["decoded_bytes"] == count, "invalid chunk extent")
        stream.seek(chunk["offset"])
        encoded = stream.read(chunk["length"])
        require(len(encoded) == chunk["length"] and hashed(encoded) == chunk["encoded_sha256"],
                "compressed chunk hash or extent differs")
        if chunk["transform"] == "identical-checkpoint":
            require(not encoded, "identical chunk has payload")
            return None
        require(chunk["transform"] in ("direct", "xor-checkpoint"), "unknown chunk transform")
        return unshuffle(decompress(encoded, index["codec"], count))

    with payload.open("rb") as stream:
        for mode in MODES:
            row = index["modes"][mode]
            require(row["bytes"] == total and len(row["chunks"]) == chunks_count,
                    "reference chunk coverage differs")
            digest = hashlib.sha256()
            for number, chunk in enumerate(row["chunks"]):
                count = min(CHUNK_VALUES * 8, total - number * CHUNK_VALUES * 8)
                require(chunk["offset"] == expected_offset, "overlapping or skipped reference payload")
                raw = decode_chunk(stream, chunk, count)
                expected_offset += chunk["length"]
                if mode == "checkpoint":
                    require(chunk["transform"] == "direct", "checkpoint cannot depend on itself")
                elif chunk["transform"] != "direct":
                    base = decode_chunk(stream, base_chunks[number], count)
                    require(base is not None and hashed(base) == base_chunks[number]["decoded_sha256"],
                            "invalid delta base")
                    raw = base if raw is None else xor(raw, base)
                require(raw is not None and hashed(raw) == chunk["decoded_sha256"],
                        "decoded reference hash differs")
                digest.update(raw)
                observe(mode, number * CHUNK_VALUES * 8, raw)
            require(digest.hexdigest() == row["sha256"], "decoded whole-array hash differs")
    require(expected_offset == payload.stat().st_size, "unindexed reference payload")


def retained(ev, relative):
    require(relative is not None and not relative.is_absolute() and ".." not in relative.parts,
            "missing or nonportable retained receipt")
    path = ROOT / relative
    require(path.resolve().is_relative_to(ROOT), "retained receipt escapes project")
    record = load_json(path)
    require(record["status"] == "passed", "retained reference qualification failed")
    require(any(row["name"] == "teacher_reference_qualification_completed" and row["passed"]
                for row in record["assertions"]), "missing teacher reference qualification")
    for name in ("tests/teacher_reference.py", "tests/fp64_reference.py", "tests/awq_prepare.py"):
        require(record["source_sha256"][name] == sha(ROOT / name),
                "qualified mathematical reference changed")
    ev.receipt.setdefault("retained_receipts", []).append(
        {"path": str(relative), "sha256": sha(path)})
    for name, digest in record["outputs"].items():
        checked_payload(ev, {"path": name, "sha256": digest})
    return record


def qualification_worker(args):
    record = load_json(ROOT / args.reference_receipt)
    output = ROOT / args.destination
    output.mkdir(parents=True, exist_ok=False)
    report = {"purpose": "lossless-storage-qualification", "acceptance_evidence": False,
              "codecs": {}, "negative_cases": []}
    for codec in ("zlib", "lzma"):
        rows = []
        for kind, shape, axes in (
                ("layers", [3, 24, 896], ["position", "layer", "component"]),
                ("logits", [151936, 3], ["vocabulary", "position"])):
            arrays = {}
            for mode in MODES:
                matches = [name for name in record["outputs"]
                           if name.endswith(f"/{mode}/{kind}.f64")]
                require(len(matches) == 1, "retained qualified array missing")
                arrays[mode] = ROOT / matches[0]
                require(sha(arrays[mode]) == record["outputs"][matches[0]],
                        "qualified array changed")
            directory = output / codec / kind
            index = write_archive(directory, arrays, shape, axes, codec)
            compared = {mode: 0 for mode in MODES}

            def observe(mode, offset, data):
                with arrays[mode].open("rb") as source:
                    source.seek(offset)
                    require(source.read(len(data)) == data, "lossless complete byte comparison differs")
                compared[mode] += len(data)

            read_archive(directory, shape, axes, observe)
            require(all(count == math.prod(shape) * 8 for count in compared.values()),
                    "incomplete full-array comparison")
            payload_bytes = (directory / "chunks.bin").stat().st_size
            index_bytes = (directory / "index.json").stat().st_size
            transforms = {method: sum(chunk["transform"] == method
                          for row in index["modes"].values() for chunk in row["chunks"])
                          for method in ("direct", "xor-checkpoint", "identical-checkpoint")}
            rows.append({"kind": kind, "shape": shape, "axes": axes,
                         "raw_bytes": sum(compared.values()), "payload_bytes": payload_bytes,
                         "index_bytes": index_bytes, "complete_compared_bytes": dict(compared),
                         "payload_bytes_by_mode": {
                             mode: sum(chunk["length"] for chunk in index["modes"][mode]["chunks"])
                             for mode in MODES},
                         "transforms": transforms})

            def reject(label, function):
                try:
                    function()
                except (ValueError, KeyError):
                    report["negative_cases"].append(codec + "/" + kind + "/" + label)
                else:
                    raise ValueError("storage defect not rejected: " + label)

            reject("dimensions", lambda: read_archive(directory, list(reversed(shape)), axes, observe))
            reject("axes", lambda: read_archive(directory, shape, list(reversed(axes)), observe))
            raw = (directory / "chunks.bin").read_bytes()
            for name, damaged in (("truncated", raw[:-1]),
                                  ("corrupted", bytes([raw[0] ^ 1]) + raw[1:]),
                                  ("trailing", raw + b"\0")):
                path = directory / (name + ".bin")
                with path.open("xb") as stream:
                    stream.write(damaged)
                reject(name, lambda path=path: read_archive(
                    directory, shape, axes, observe, payload=path))
                # Rebind the container hash to exercise chunk/decoder validation too.
                altered = json.loads(json.dumps(index))
                altered["payload_sha256"] = sha(path)
                reject(name + "-rebound", lambda path=path, altered=altered: read_archive(
                    directory, shape, axes, observe, index=altered, payload=path))
            first = index["modes"]["checkpoint"]["chunks"][0]
            encoded = raw[first["offset"]:first["offset"] + first["length"]]
            reject("codec-truncation", lambda: decompress(
                encoded[:-1], codec, first["decoded_bytes"]))
            reject("codec-trailing", lambda: decompress(
                encoded + b"\0", codec, first["decoded_bytes"]))
            reject("codec-oversize", lambda: decompress(
                encoded, codec, first["decoded_bytes"] - 8))
        # This explicit fixture qualifies exact deduplication without asserting
        # that any two real weight semantics or their inference outputs agree.
        fixture = output / codec / "exact-dedup-fixture"
        original = output / codec / "fixture-input.f64"
        with original.open("xb") as stream:
            stream.write(bytes(range(256)) * 2048)
        arrays = dict.fromkeys(MODES, original)
        index = write_archive(fixture, arrays, [65536], ["element"], codec)
        compared = {mode: 0 for mode in MODES}

        def observe_fixture(mode, offset, data):
            with original.open("rb") as stream:
                stream.seek(offset)
                require(stream.read(len(data)) == data, "exact deduplication fixture differs")
            compared[mode] += len(data)

        read_archive(fixture, [65536], ["element"], observe_fixture)
        require(all(count == 524288 for count in compared.values()) and
                all(chunk["transform"] == "identical-checkpoint"
                    for mode in MODES[1:] for chunk in index["modes"][mode]["chunks"]),
                "exact deduplication path was not fully compared")
        report.setdefault("synthetic_exact_deduplication", {})[codec] = {
            "purpose": "storage-path-test-only", "compared_bytes": compared}
        report["codecs"][codec] = rows
    suite = load_json(ROOT / "tests/data/benchmark_manifest.json")
    positions = [len(load_json(ROOT / case["teacher_tokens"]["path"]))
                 for domain in suite["domains"].values() for case in domain["cases"]]
    require(len(positions) == 50 and sum(positions) == 6442, "frozen teacher suite differs")
    free = shutil.disk_usage(ROOT).free
    reserve = max(1024 ** 3, free // 10)
    estimates = {}
    for codec, rows in report["codecs"].items():
        payload = 0
        # Measured qualification ratios are projections, not worst-case guarantees.
        for row in rows:
            values_per_position = 24 * 896 if row["kind"] == "layers" else 151936
            raw_bytes = sum(positions) * len(MODES) * values_per_position * 8
            payload += math.ceil(raw_bytes * row["payload_bytes"] / row["raw_bytes"])
        chunks = sum(
            len(MODES) * math.ceil(count * values * 8 / (CHUNK_VALUES * 8))
            for count in positions for values in (24 * 896, 151936))
        # JSON index upper budget exceeds each measured per-chunk index cost.
        index_budget = chunks * 1024 + 50 * 65536
        # A future collector using write_archive must stage all four raw modes
        # of one case. Include their full overlap with the growing archive.
        peak_temporary = max(positions) * len(MODES) * (24 * 896 + 151936) * 8
        required = payload + index_budget + peak_temporary
        estimates[codec] = {
            "projected_payload_bytes": payload, "index_budget_bytes": index_budget,
            "peak_temporary_bytes": peak_temporary, "projected_required_bytes": required,
            "temporary_policy": "Four complete raw mode arrays for the largest case, "
                                "overlapping the retained compressed archive; no full-suite raw staging.",
            "available_bytes": free, "reserve_bytes": reserve,
            "projected_shortfall_bytes": max(0, required + reserve - free),
            "projection_fits": required + reserve <= free,
            "limitation": "Measured three-position qualified outputs extrapolated to all "
                          "6442 positions, not measured full-suite compression or a capacity proof."}
    report["capacity"] = estimates
    files = [path for path in output.rglob("*") if path.is_file()]
    report["qualification_storage"] = {
        "file_count": len(files), "logical_bytes_before_report": sum(path.stat().st_size for path in files),
        "allocated_bytes_before_report": sum(path.stat().st_blocks * 512 for path in files),
        "includes": "Both codecs, indexes, retained negative fixtures and exact-dedup fixtures; "
                    "original qualified arrays are external retained inputs, not copied.",
        "maximum_compression_input_bytes": CHUNK_VALUES * 8}
    write_json(output / "qualification.json", report)
    print(json.dumps(report, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-receipt", type=Path, required=True)
    parser.add_argument("--repair-of", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    for path in (args.reference_receipt, args.repair_of, args.destination):
        if path is not None:
            require(not path.is_absolute() and ".." not in path.parts and
                    (ROOT / path).resolve().is_relative_to(ROOT), "nonportable storage argument")
    if args.worker:
        require(args.destination is not None, "missing worker destination")
        qualification_worker(args)
        return 0
    ev = Evidence("reference-storage")
    ok = False
    try:
        old = ROOT / args.repair_of
        require(old.is_file(), "missing original capacity failure")
        failure = load_json(old)
        require(failure["status"] == "failed" and any(
            row["name"] == "reference_output_capacity" and not row["passed"]
            for row in failure["assertions"]), "repair link is not the capacity failure")
        ev.receipt["repair_of"] = {"path": str(args.repair_of), "sha256": sha(old)}
        for name in ("tests/data/model_manifest.json", "tests/data/benchmark_manifest.json"):
            require(failure["source_sha256"][name] == sha(ROOT / name),
                    "frozen inputs differ from the original capacity failure")
        ev.receipt["tool_versions"] = {"python": sys.version, "zlib": zlib.ZLIB_RUNTIME_VERSION,
                                       "lzma": "Python stdlib FORMAT_XZ, preset=1"}
        retained(ev, args.reference_receipt)
        destination = ev.path / "qualified-storage"
        ok = ev.run("storage-qualification", [
            sys.executable, "tests/reference_storage.py", "--worker",
            "--reference-receipt", str(args.reference_receipt),
            "--repair-of", str(args.repair_of),
            "--destination", str(destination.relative_to(ROOT))], timeout=3600)
        ev.receipt["outputs"] = {str(path.relative_to(ROOT)): sha(path)
                                 for path in destination.rglob("*") if path.is_file()}
        ev.assertion("lossless_storage_qualification", ok)
        if ok:
            report = load_json(destination / "qualification.json")
            ev.receipt["capacity"] = report["capacity"]
            capacity_ok = any(row["projection_fits"] for row in report["capacity"].values())
            ev.assertion("projected_complete_reference_capacity", capacity_ok,
                         scope="Measured retained-array projection only; not a full-suite capacity proof",
                         full_launch_attempted=False)
            ok = capacity_ok
    except (ValueError, KeyError, OSError) as error:
        ok = False
        ev.assertion("storage_exception", False, error=repr(error))
    finally:
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
