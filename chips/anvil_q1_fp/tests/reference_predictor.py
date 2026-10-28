#!/usr/bin/env python3
"""Bounded axis-aware lossless-storage experiment; no inference or DUT results."""

import argparse
import copy
import hashlib
import json
import lzma
import math
from pathlib import Path
import resource
import shutil
import struct
import sys
import tracemalloc
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import load_json, require, sha
from benchmark_inputs import write_json
from reference_storage import MODES, hashed, retained, shuffle, unshuffle, xor
from verify import Evidence, ROOT


TARGET_VALUES = 131072
CODECS = ("zlib9", "lzma9-extreme")
TRANSFORMS = ("direct", "xor-checkpoint", "position-xor", "position-sub64")
MASK64 = (1 << 64) - 1
DECODER_LIMIT = 128 * 1024 ** 2


def layout(shape, axes):
    require((axes == ["position", "layer", "component"] and len(shape) == 3) or
            (axes == ["vocabulary", "position"] and len(shape) == 2),
            "unsupported predictor axes")
    require(all(type(value) is int and value > 0 for value in shape),
            "invalid predictor dimensions")
    if len(shape) == 3:
        stride = shape[1] * shape[2]
        return stride, stride * max(2, TARGET_VALUES // stride)
    return 1, shape[1] * max(1, TARGET_VALUES // shape[1])


def predict(data, start, shape, axes, method, inverse=False):
    stride, _ = layout(shape, axes)
    require(len(data) % 8 == 0 and start >= 0, "invalid predictor byte extent")
    values = [word[0] for word in struct.iter_unpack("<Q", data)]
    output = []
    for local, value in enumerate(values):
        absolute = start + local
        if len(shape) == 3:
            has_previous = local >= stride
        else:
            has_previous = local >= 1 and absolute % shape[1] != 0
        previous = (output if inverse else values)[local - stride] if has_previous else 0
        if method == "position-xor":
            output.append(value ^ previous)
        else:
            require(method == "position-sub64", "unknown position predictor")
            output.append((value + previous if inverse else value - previous) & MASK64)
    return b"".join(struct.pack("<Q", value) for value in output)


def encode(data, codec):
    require(codec in CODECS, "unsupported predictor codec")
    return (zlib.compress(data, 9) if codec == "zlib9" else
            lzma.compress(data, preset=9 | lzma.PRESET_EXTREME))


def decode(data, codec, size):
    require(codec in CODECS, "unsupported predictor codec")
    decoder = (zlib.decompressobj() if codec == "zlib9" else
               lzma.LZMADecompressor(memlimit=DECODER_LIMIT))
    try:
        result = decoder.decompress(data, max_length=size + 1)
    except (zlib.error, lzma.LZMAError) as error:
        raise ValueError("invalid predictor compressed stream") from error
    require(decoder.eof and not decoder.unused_data and len(result) == size,
            "truncated, oversized or trailing predictor stream")
    return result


def arrays_for(record, kind):
    result = {}
    for mode in MODES:
        matches = [name for name in record["outputs"]
                   if name.endswith(f"/{mode}/{kind}.f64")]
        require(len(matches) == 1, "qualified predictor array missing")
        result[mode] = ROOT / matches[0]
        require(sha(result[mode]) == record["outputs"][matches[0]],
                "qualified predictor array changed")
    return result


def write_archive(directory, arrays, shape, axes, codec, case_id):
    stride, chunk_values = layout(shape, axes)
    size = math.prod(shape) * 8
    require(set(arrays) == set(MODES) and all(
        path.stat().st_size == size for path in arrays.values()), "predictor input shape differs")
    directory.mkdir(parents=True, exist_ok=False)
    index = {
        "schema": 1, "purpose": "axis-predicted-reference-preparation",
        "acceptance_evidence": False, "dtype": "<f8", "shape": shape, "axes": axes,
        "codec": codec, "case_id": case_id, "predictor_stride": stride,
        "predictor_reset": "each-chunk-and-position-series",
        "chunk_values": chunk_values, "modes": {},
    }
    with (directory / "chunks.bin").open("xb") as stream:
        for mode in MODES:
            chunks = []
            with arrays[mode].open("rb") as source, arrays["checkpoint"].open("rb") as base:
                start = 0
                while raw := source.read(chunk_values * 8):
                    baseline = base.read(len(raw))
                    candidates = [(len(encoded), method, encoded)
                                  for method in TRANSFORMS
                                  if method != "xor-checkpoint" or mode != "checkpoint"
                                  for encoded in [encode(shuffle(
                                      raw if method == "direct" else
                                      xor(raw, baseline) if method == "xor-checkpoint" else
                                      predict(raw, start, shape, axes, method)), codec)]]
                    for _, candidate_method, candidate_data in candidates:
                        restored = unshuffle(decode(candidate_data, codec, len(raw)))
                        if candidate_method == "xor-checkpoint":
                            restored = xor(restored, baseline)
                        elif candidate_method.startswith("position-"):
                            restored = predict(restored, start, shape, axes,
                                               candidate_method, inverse=True)
                        require(restored == raw, "candidate complete byte comparison differs")
                    _, method, encoded = min(candidates, key=lambda row: row[0])
                    chunks.append({
                        "start_value": start, "offset": stream.tell(), "length": len(encoded),
                        "values": len(raw) // 8, "transform": method,
                        "predictor_origin": start, "case_id": case_id,
                        "decoded_sha256": hashed(raw), "encoded_sha256": hashed(encoded),
                        "candidate_lengths": {name: length for length, name, _ in candidates},
                    })
                    stream.write(encoded)
                    start += len(raw) // 8
            index["modes"][mode] = {"sha256": sha(arrays[mode]), "bytes": size, "chunks": chunks}
    index["payload_sha256"] = sha(directory / "chunks.bin")
    write_json(directory / "index.json", index)
    return index


def read_archive(directory, shape, axes, case_id, observe, index=None, payload=None):
    index = load_json(directory / "index.json") if index is None else index
    stride, chunk_values = layout(shape, axes)
    require(index["schema"] == 1 and index["dtype"] == "<f8" and
            index["purpose"] == "axis-predicted-reference-preparation" and
            index["shape"] == shape and index["axes"] == axes and
            index["case_id"] == case_id and index["codec"] in CODECS and
            index["predictor_stride"] == stride and
            index["predictor_reset"] == "each-chunk-and-position-series" and
            index["chunk_values"] == chunk_values and set(index["modes"]) == set(MODES),
            "predictor schema, axes, case or reset boundary differs")
    payload = directory / "chunks.bin" if payload is None else payload
    require(sha(payload) == index["payload_sha256"], "predictor payload hash differs")
    total = math.prod(shape)
    expected_offset = 0
    base_chunks = index["modes"]["checkpoint"]["chunks"]

    def chunk_raw(stream, chunk, mode, number):
        start = number * chunk_values
        count = min(chunk_values, total - start)
        require(type(chunk["offset"]) is int and chunk["offset"] >= 0 and
                type(chunk["length"]) is int and 0 < chunk["length"] <= count * 8 + 65536 and
                chunk["start_value"] == start and chunk["values"] == count and
                chunk["predictor_origin"] == start and chunk["case_id"] == case_id and
                chunk["transform"] in TRANSFORMS, "predictor chunk extent or boundary differs")
        stream.seek(chunk["offset"])
        encoded = stream.read(chunk["length"])
        require(len(encoded) == chunk["length"] and hashed(encoded) == chunk["encoded_sha256"],
                "predictor chunk hash differs")
        data = unshuffle(decode(encoded, index["codec"], count * 8))
        method = chunk["transform"]
        if method == "xor-checkpoint":
            require(mode != "checkpoint", "predictor base depends on itself")
            base = chunk_raw(stream, base_chunks[number], "checkpoint", number)
            data = xor(data, base)
        elif method.startswith("position-"):
            data = predict(data, start, shape, axes, method, inverse=True)
        require(hashed(data) == chunk["decoded_sha256"], "decoded predictor chunk hash differs")
        return data

    with payload.open("rb") as stream:
        for mode in MODES:
            row = index["modes"][mode]
            require(row["bytes"] == total * 8 and len(row["chunks"]) ==
                    math.ceil(total / chunk_values), "predictor chunk coverage differs")
            digest = hashlib.sha256()
            for number, chunk in enumerate(row["chunks"]):
                require(chunk["offset"] == expected_offset, "predictor payload coverage differs")
                data = chunk_raw(stream, chunk, mode, number)
                expected_offset += chunk["length"]
                digest.update(data)
                observe(mode, number * chunk_values * 8, data)
            require(digest.hexdigest() == row["sha256"], "predictor complete-array hash differs")
    require(expected_offset == payload.stat().st_size, "unindexed predictor bytes")


def compare(directory, arrays, shape, axes, case_id):
    counts = dict.fromkeys(MODES, 0)

    def observe(mode, offset, data):
        with arrays[mode].open("rb") as source:
            source.seek(offset)
            require(source.read(len(data)) == data, "complete predictor byte comparison differs")
        counts[mode] += len(data)

    read_archive(directory, shape, axes, case_id, observe)
    require(all(count == math.prod(shape) * 8 for count in counts.values()),
            "incomplete predictor byte comparison")
    return counts


def negative_checks(directory, shape, axes, case_id, index):
    rejected = []

    def reject(label, operation):
        try:
            operation()
        except (ValueError, KeyError):
            rejected.append(label)
        else:
            raise ValueError("predictor defect not rejected: " + label)

    def read(altered=None, payload=None, expected_case=case_id):
        read_archive(directory, shape, axes, expected_case, lambda *_: None,
                     index=altered, payload=payload)

    for key, value in (("predictor_stride", index["predictor_stride"] + 1),
                       ("predictor_reset", "carry-across-chunks"),
                       ("axes", list(reversed(axes))), ("shape", [math.prod(shape)])):
        altered = copy.deepcopy(index)
        altered[key] = value
        reject(key, lambda altered=altered: read(altered))
    reject("wrong-case", lambda: read(expected_case=case_id + "-next"))
    for key, value in (("predictor_origin", 1), ("case_id", case_id + "-previous"),
                       ("start_value", 1)):
        altered = copy.deepcopy(index)
        altered["modes"]["checkpoint"]["chunks"][0][key] = value
        reject(key, lambda altered=altered: read(altered))
    if len(index["modes"]["checkpoint"]["chunks"]) > 1:
        altered = copy.deepcopy(index)
        altered["modes"]["checkpoint"]["chunks"][1]["predictor_origin"] = 0
        reject("cross-chunk-predictor-origin", lambda: read(altered))
    raw = (directory / "chunks.bin").read_bytes()
    for name, damaged in (("truncation", raw[:-1]),
                          ("corruption", bytes([raw[0] ^ 1]) + raw[1:]),
                          ("trailing", raw + b"\0")):
        path = directory / (name + ".bin")
        with path.open("xb") as stream:
            stream.write(damaged)
        reject(name, lambda path=path: read(payload=path))
        altered = copy.deepcopy(index)
        altered["payload_sha256"] = sha(path)
        reject(name + "-rebound", lambda altered=altered, path=path: read(altered, path))
    first = index["modes"]["checkpoint"]["chunks"][0]
    encoded = raw[first["offset"]:first["offset"] + first["length"]]
    for label, data, count in (("codec-truncation", encoded[:-1], first["values"] * 8),
                               ("codec-trailing", encoded + b"\0", first["values"] * 8),
                               ("codec-oversize", encoded, first["values"] * 8 - 8)):
        reject(label, lambda data=data, count=count: decode(data, index["codec"], count))
    return rejected


def boundary_fixtures(output, codec):
    comparisons = 0
    for shape, axes in (([15, 24, 896], ["position", "layer", "component"]),
                        ([65539, 3], ["vocabulary", "position"]),
                        ([3, 1], ["vocabulary", "position"])):
        stride, chunk_values = layout(shape, axes)
        count = math.prod(shape)
        for method in TRANSFORMS[2:]:
            # All bit patterns are opaque integers, including NaNs and signed zeros.
            words = [((number * 0x9e3779b97f4a7c15) ^ (number >> 2)) & MASK64
                     for number in range(count)]
            words[:4] = [0, 1 << 63, 0x7ff0000000000000, 0x7ff8000000000001][:min(4, count)]
            raw = b"".join(struct.pack("<Q", value) for value in words)
            rebuilt = bytearray()
            for start in range(0, count, chunk_values):
                part = raw[start * 8:(start + chunk_values) * 8]
                predicted = predict(part, start, shape, axes, method)
                # Independently evaluate each axis boundary and integer word.
                expected = []
                for local in range(len(part) // 8):
                    number = start + local
                    previous = (words[number - stride] if
                                (local >= stride if len(shape) == 3 else
                                 local > 0 and number % shape[1] != 0) else 0)
                    expected.append(words[number] ^ previous if method == "position-xor" else
                                    (words[number] - previous) & MASK64)
                require(predicted == b"".join(struct.pack("<Q", word) for word in expected),
                        "axis boundary independent known answer differs")
                rebuilt.extend(predict(predicted, start, shape, axes, method, inverse=True))
                comparisons += len(part)
            require(bytes(rebuilt) == raw, "chunk/reset fixture differs")
            # A new case always starts from zero, not the previous case's final word.
            require(predict(raw[:stride * 8], 0, shape, axes, method) == raw[:stride * 8],
                    "cross-case predictor reset differs")
    report = {"codec": codec, "compared_bytes": comparisons,
              "coverage": "Both predictors; multi-chunk layer/logit arrays; tail chunks; "
                          "position-depth one; chunk, series and new-case reset; opaque IEEE bits"}
    write_json(output / (codec + "-boundary-fixtures.json"), report)
    return report


def qualification_worker(args):
    record = load_json(ROOT / args.reference_receipt)
    output = ROOT / args.destination
    output.mkdir(parents=True, exist_ok=False)
    report = {"purpose": "axis-prediction-storage-qualification",
              "acceptance_evidence": False, "codecs": {}, "negative_cases": {},
              "boundary_fixtures": []}
    for codec in CODECS:
        rows = []
        for kind, shape, axes in (
                ("layers", [3, 24, 896], ["position", "layer", "component"]),
                ("logits", [151936, 3], ["vocabulary", "position"])):
            arrays = arrays_for(record, kind)
            directory = output / codec / kind
            case_id = "retained-three-position-qualification"
            index = write_archive(directory, arrays, shape, axes, codec, case_id)
            counts = compare(directory, arrays, shape, axes, case_id)
            report["negative_cases"][codec + "/" + kind] = negative_checks(
                directory, shape, axes, case_id, index)
            rows.append({
                "kind": kind, "shape": shape, "axes": axes,
                "raw_bytes": sum(counts.values()), "complete_compared_bytes": counts,
                "payload_bytes": (directory / "chunks.bin").stat().st_size,
                "index_bytes": (directory / "index.json").stat().st_size,
                "chunk_values": index["chunk_values"],
                "payload_bytes_by_mode": {
                    mode: sum(chunk["length"] for chunk in index["modes"][mode]["chunks"])
                    for mode in MODES},
                "transforms": {method: sum(chunk["transform"] == method
                                          for row in index["modes"].values()
                                          for chunk in row["chunks"])
                               for method in TRANSFORMS},
                "candidate_complete_compared_bytes": {
                    method: sum(chunk["values"] * 8 for row in index["modes"].values()
                                for chunk in row["chunks"] if method in chunk["candidate_lengths"])
                    for method in TRANSFORMS},
                "candidate_payload_bytes": {
                    method: sum(chunk["candidate_lengths"][method]
                                for row in index["modes"].values() for chunk in row["chunks"]
                                if method in chunk["candidate_lengths"])
                    for method in TRANSFORMS},
            })
        report["boundary_fixtures"].append(boundary_fixtures(output, codec))
        report["codecs"][codec] = rows
    suite = load_json(ROOT / "tests/data/benchmark_manifest.json")
    positions = [len(load_json(ROOT / case["teacher_tokens"]["path"]))
                 for domain in suite["domains"].values() for case in domain["cases"]]
    require(len(positions) == 50 and sum(positions) == 6442, "frozen teacher suite differs")
    free = shutil.disk_usage(ROOT).free
    reserve = max(1024 ** 3, free // 10)
    report["capacity"] = {}
    for codec, rows in report["codecs"].items():
        payload = sum(math.ceil(sum(positions) * len(MODES) *
                      (24 * 896 if row["kind"] == "layers" else 151936) * 8 *
                      row["payload_bytes"] / row["raw_bytes"]) for row in rows)
        chunks = sum(len(MODES) * math.ceil(math.prod(shape) / layout(shape, axes)[1])
                     for count in positions for shape, axes in (
                         ([count, 24, 896], ["position", "layer", "component"]),
                         ([151936, count], ["vocabulary", "position"])))
        maximum_measured_index_per_chunk = max(
            row["index_bytes"] / (len(MODES) *
            math.ceil(math.prod(row["shape"]) / row["chunk_values"])) for row in rows)
        require(maximum_measured_index_per_chunk <= 2048,
                "measured predictor index exceeds capacity budget")
        index_budget = chunks * 2048 + 50 * 65536
        staging = max(positions) * len(MODES) * (24 * 896 + 151936) * 8
        required = payload + index_budget + staging
        report["capacity"][codec] = {
            "projected_payload_bytes": payload, "index_budget_bytes": index_budget,
            "maximum_measured_index_bytes_per_chunk": maximum_measured_index_per_chunk,
            "peak_raw_staging_bytes": staging, "projected_required_bytes": required,
            "available_bytes": free, "reserve_bytes": reserve,
            "projected_shortfall_bytes": max(0, required + reserve - free),
            "projection_fits": required + reserve <= free,
            "limitation": "Three measured positions only; no full-suite capacity proof. "
                          "All four complete raw modes of the largest case overlap the archive. "
                          "Longer-position predictor compression and future inference RAM unmeasured."}
    files = [path for path in output.rglob("*") if path.is_file()]
    report["measured_probe_storage"] = {
        "logical_bytes_before_report": sum(path.stat().st_size for path in files),
        "allocated_bytes_before_report": sum(path.stat().st_blocks * 512 for path in files),
        "peak_probe_staging_policy": "Files only appended/created; this is the measured peak "
                                     "retained fixture/archive disk footprint before report. "
                                     "No additional raw case arrays were staged.",
        "raw_reference_arrays_copied": False,
        "peak_encoder_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
    }
    write_json(output / "qualification.json", report)
    print(json.dumps(report, indent=2), flush=True)


def decode_worker(args):
    directory = ROOT / args.destination
    index = load_json(directory / "index.json")
    kind = directory.name
    arrays = arrays_for(load_json(ROOT / args.reference_receipt), kind)
    tracemalloc.start()
    counts = compare(directory, arrays, index["shape"], index["axes"], index["case_id"])
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(json.dumps({
        "complete_compared_bytes": counts,
        "peak_decoder_python_heap_bytes": peak,
        "peak_decoder_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        "lzma_decoder_memlimit_bytes": DECODER_LIMIT,
        "rss_scope": "Fresh Linux decoder process including imports, hashes and byte comparisons; "
                     "no encoder or inference. Python heap excludes codec-native allocations.",
    }), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-receipt", type=Path, required=True)
    parser.add_argument("--repair-of", type=Path, required=True)
    parser.add_argument("--worker", choices=("qualify", "decode"))
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    for path in (args.reference_receipt, args.repair_of, args.destination):
        if path is not None:
            require(not path.is_absolute() and ".." not in path.parts and
                    (ROOT / path).resolve().is_relative_to(ROOT), "nonportable predictor argument")
    if args.worker:
        require(args.destination is not None, "predictor worker destination missing")
        (qualification_worker if args.worker == "qualify" else decode_worker)(args)
        return 0
    ev = Evidence("reference-predictor")
    ok = False
    try:
        failure = load_json(ROOT / args.repair_of)
        require(failure["status"] == "failed" and any(
            row["name"] == "projected_complete_reference_capacity" and not row["passed"]
            for row in failure["assertions"]), "missing retained compressed-capacity failure")
        ev.receipt["repair_of"] = {"path": str(args.repair_of), "sha256": sha(ROOT / args.repair_of)}
        original = failure["repair_of"]["path"]
        require(load_json(ROOT / original)["status"] == "failed", "original raw-capacity failure missing")
        ev.receipt["original_capacity_failure"] = {"path": original, "sha256": sha(ROOT / original)}
        for name in ("tests/data/model_manifest.json", "tests/data/benchmark_manifest.json"):
            require(failure["source_sha256"][name] == sha(ROOT / name),
                    "frozen predictor inputs differ")
        ev.receipt["tool_versions"] = {
            "python": sys.version, "zlib": zlib.ZLIB_RUNTIME_VERSION,
            "lzma": "Python stdlib FORMAT_XZ, preset=9|PRESET_EXTREME",
        }
        retained(ev, args.reference_receipt)
        destination = ev.path / "qualified-prediction"
        common = ["--reference-receipt", str(args.reference_receipt),
                  "--repair-of", str(args.repair_of)]
        ok = ev.run("predictor-qualification", [
            sys.executable, "tests/reference_predictor.py", *common,
            "--worker", "qualify", "--destination", str(destination.relative_to(ROOT))],
            timeout=3600)
        ev.assertion("axis_prediction_complete_byte_and_negative_checks", ok)
        if ok:
            report = load_json(destination / "qualification.json")
            ev.receipt["decoder_memory"] = {}
            for codec in CODECS:
                for kind in ("layers", "logits"):
                    label = "decode-" + codec + "-" + kind
                    passed = ev.run(label, [
                        sys.executable, "tests/reference_predictor.py", *common,
                        "--worker", "decode", "--destination",
                        str((destination / codec / kind).relative_to(ROOT))], timeout=3600)
                    ev.assertion(label + "-complete-comparison", passed)
                    ok = passed and ok
                    if passed:
                        ev.receipt["decoder_memory"][codec + "/" + kind] = load_json(
                            ev.path / (label + ".stdout"))
            ev.receipt["capacity"] = report["capacity"]
            capacity_ok = any(row["projection_fits"] for row in report["capacity"].values())
            ev.assertion("projected_complete_reference_capacity", capacity_ok,
                         full_launch_attempted=False, full_suite_capacity_proven=False)
            ok = capacity_ok and ok
    except (ValueError, KeyError, OSError) as error:
        ev.assertion("predictor_exception", False, error=repr(error))
        ok = False
    finally:
        ev.receipt["outputs"] = {
            str(path.relative_to(ROOT)): sha(path)
            for path in ev.path.rglob("*") if path.is_file() and path.name != "receipt.json"}
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
