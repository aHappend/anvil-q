"""Mathematical checkpoint comparisons and event-defined, public-port metrics."""

from collections import Counter
from fractions import Fraction
import hashlib
import re

from codec_check import encode_record
from reference import ieee_round
from small_model import CELLS, fixture


def expected_workload(mode, cache, seed):
    observations = {}
    memory, descriptors, logits = fixture(
        mode, cache, seed, tied_head=True, observations=observations)
    return {
        **observations, "geometry": CELLS["small"], "mode": mode, "cache_mode": cache,
        "image_sha256": hashlib.sha256(memory).hexdigest(),
        "expected_logits": logits, "descriptors": descriptors,
    }


def events(text):
    result = []
    for line in text.splitlines():
        if not line.startswith("BENCH_"):
            continue
        words = line.split()
        time = int(words[1])
        if time % 10000 != 5000:
            raise RuntimeError("BENCH_TIMING: observation is not a pre-edge 100MHz sample")
        result.append((time // 10000, words[0][6:], words[2:]))
    result.sort(key=lambda event: event[0])
    if not result:
        raise RuntimeError("BENCH_COVERAGE: missing executed public-port observations")
    return result


def payload_bytes(workload):
    geometry = workload["geometry"]
    useful = set()
    for descriptor in workload["descriptors"]:
        if descriptor[13] & 256 == 0:
            continue
        base, rows, cols, stride, fmt = (
            descriptor[0], descriptor[8], descriptor[9], descriptor[10], descriptor[13] & 3)
        if fmt == 0 or (fmt == 2 and stride == 4096):
            width = 2 if fmt == 2 else 0
            for row in range(rows):
                for col in range(cols):
                    element = ((row // 16) * ((cols + 127) // 128) + col // 128) * 2048
                    element += (row % 16) * 128 + col % 128
                    address = base + (element * 2 if width else element // 2)
                    useful.update(range(address, address + (width or 1)))
            if fmt == 0:
                groups = cols // geometry["group"]
                for row in range(rows):
                    useful.update(range(descriptor[4] + row * descriptor[11],
                                        descriptor[4] + row * descriptor[11] + (groups + 1) // 2))
                    useful.update(range(descriptor[6] + row * descriptor[12],
                                        descriptor[6] + row * descriptor[12] + 2 * groups))
        else:
            for row in range(rows):
                useful.update(range(base + row * stride,
                                    base + row * stride + cols * (4 if fmt == 3 else 2)))
    block = geometry["cache_block"]
    record_length = (4 * block, 2 * block, block + 1)[workload["cache_mode"]]
    region = geometry["kv_heads"] * (geometry["head_dim"] // block) * record_length
    stride = (region + 63) & ~63
    for token_region in range(geometry["layers"] * 2 * geometry["sequence"]):
        start = geometry["image_bytes"] * 2 + token_region * stride
        useful.update(range(start, start + region))
    return useful


def traffic(selected, implementation, useful):
    physical = 64 if implementation == "ht" else 4
    result = {"read_commands": 0, "read_beats": 0, "write_beats": 0,
              "accepted_bytes": 0, "valid_payload_bytes": 0,
              "memory_request_stall_port_cycles": 0, "tensor_issue_events": 0,
              "tensor_issue_cycles": 0, "tensor_mac_contributions": 0,
              "tensor_input_stall_port_cycles": 0, "tensor_output_stall_cycles": 0}
    histogram = Counter()
    issue_cycles = set()
    for time, kind, words in selected:
        if kind == "MEM":
            write, beats, address, be, request_kind = (
                int(words[0]), int(words[1]), int(words[2], 16),
                int(words[3], 16), int(words[4]))
            if write not in (0, 1) or not 1 <= beats <= 16 or (write and beats != 1):
                raise RuntimeError("BENCH_PROTOCOL: malformed accepted memory command")
            result["accepted_bytes"] += physical * beats
            if implementation == "ht":
                if request_kind != -1 or address & 63 or (address & 4095) + 64 * beats > 4096:
                    raise RuntimeError("BENCH_PROTOCOL: malformed DDR command")
                result["valid_payload_bytes"] += sum(
                    address + offset in useful and (not write or be >> (offset % 64) & 1)
                    for offset in range(64 * beats))
            else:
                if not 0 <= request_kind <= 15 or beats != 1:
                    raise RuntimeError("BENCH_PROTOCOL: malformed parent transaction")
                payload = (2 if request_kind in (0, 3, 4, 5, 6, 7) else
                           1 if request_kind in (12, 13, 14, 15) else 4)
                result["valid_payload_bytes"] += payload
            if write:
                result["write_beats"] += 1
            else:
                result["read_commands"] += 1
                result["read_beats"] += beats
                histogram[str(beats)] += 1
        elif kind == "MEM_STALL":
            result["memory_request_stall_port_cycles"] += 1
        elif kind == "MAC":
            lanes = int(words[0])
            if not 1 <= lanes <= (128 if implementation == "ht" else 8):
                raise RuntimeError("BENCH_COVERAGE: invalid active MAC lane count")
            result["tensor_issue_events"] += 1
            result["tensor_mac_contributions"] += lanes
            issue_cycles.add(time)
        elif kind == "MAC_STALL":
            result["tensor_input_stall_port_cycles"] += 1
        elif kind == "MAC_OUTPUT_STALL":
            result["tensor_output_stall_cycles"] += 1
    result["tensor_issue_cycles"] = len(issue_cycles)
    result["read_burst_histogram"] = dict(sorted(histogram.items(), key=lambda item: int(item[0])))
    return result


def cache_observations(trace, workload, implementation):
    geometry = workload["geometry"]
    if geometry["cache_block"] != 1 or geometry["kv_heads"] != 1:
        raise RuntimeError("BENCH_CONFIGURATION: this benchmark declares one-word cache records")
    source = {(row["layer"], row["position"]): row for row in workload["cache"]}
    active = None
    committed = [0] * geometry["layers"]
    pending_writes = set()
    intervals = []
    counters = Counter()
    for time, kind, words in trace:
        if kind in ("KV_CMD", "KV_COMMIT", "PARENT_KV_CMD"):
            if active is not None:
                raise RuntimeError("BENCH_KV_PROTOCOL: overlapping cache commands")
            active = {"start": time, "memory": [], "kind": kind, "words": words}
        elif kind in ("KV_MEM", "PARENT_KV_MEM"):
            if active is None:
                raise RuntimeError("BENCH_KV_PROTOCOL: backing request without logical command")
            active["memory"].append((kind, words))
        elif kind == "KV_STALL":
            counters["memory_request_stall_port_cycles"] += 1
        elif kind == "KV_OUTPUT_STALL":
            counters["response_stall_cycles"] += 1
        elif kind == "KV_RSP":
            if active is None or int(words[0]) != 0 or time <= active["start"]:
                raise RuntimeError("BENCH_KV_PROTOCOL: unexpected/error/creation-edge response")
            operation, args = active["kind"], active["words"]
            memory = active["memory"]
            if implementation == "ht":
                if operation == "KV_COMMIT":
                    layer, position = map(int, args)
                    required = {(layer, position, value, dim)
                                for value in range(2) for dim in range(geometry["head_dim"])}
                    if (position != committed[layer] or
                            not required <= pending_writes or memory or int(words[1], 16)):
                        raise RuntimeError("BENCH_KV_COMMIT: incomplete/incorrect token visibility")
                    committed[layer] += 1
                    counters["commits"] += 1
                elif operation == "KV_CMD":
                    mode, write, value, layer, position, head, block = map(int, args[:7])
                    if mode != workload["cache_mode"] or head != 0 or value not in (0, 1):
                        raise RuntimeError("BENCH_KV_CONFIGURATION")
                    row = source[layer, position]
                    raw = row["raw_value" if value else "raw_key"][block]
                    decoded = row["value" if value else "key"][block]
                    supplied = ieee_round(Fraction(raw, 65536), 5, 10) if mode == 1 else raw
                    returned = supplied if mode == 1 else decoded
                    if int(words[1], 16) != returned & 0xffffffff:
                        raise RuntimeError("BENCH_KV_NUMERICAL: HT response differs from independent codec")
                    record, _, length = encode_record([supplied], mode)
                    address = (geometry["image_bytes"] * 2 +
                               ((layer * 2 + value) * geometry["sequence"] + position) * 64 +
                               block * length)
                    if write:
                        if (position != committed[layer] or
                                int(args[7], 16) != supplied & 0xffffffff or len(memory) != 1):
                            raise RuntimeError("BENCH_KV_NUMERICAL: incorrect HT cache insertion")
                        pending_writes.add((layer, position, value, block))
                        counters["writes"] += 1
                    else:
                        if position >= committed[layer] or len(memory) > 1:
                            raise RuntimeError("BENCH_KV_COMMIT: read of uncommitted data")
                        counters["reads"] += 1
                        counters["misses" if memory else "hits"] += 1
                    for mem_kind, fields in memory:
                        mem_write, mem_address, be, data = (
                            int(fields[0]), int(fields[1], 16),
                            int(fields[2], 16), int(fields[3], 16))
                        offset = address % 64
                        mask = ((1 << length) - 1) << offset if write else (1 << 64) - 1
                        if (mem_kind != "KV_MEM" or mem_write != write or
                                mem_address != address & ~63 or be != mask or
                                (write and data != record << (8 * offset))):
                            raise RuntimeError("BENCH_KV_NUMERICAL: incorrect dense DDR record/mask/address")
                        counters["backing_write_beats" if write else "backing_read_beats"] += 1
                        counters["accepted_backing_bytes"] += 64
                        counters["valid_backing_payload_bytes"] += length
                else:
                    raise RuntimeError("BENCH_KV_PROTOCOL: mixed implementation traces")
            else:
                if operation != "PARENT_KV_CMD":
                    raise RuntimeError("BENCH_KV_PROTOCOL: mixed implementation traces")
                op, layer, position, head, dimension = map(int, args)
                row = source[layer, position]
                if op == 0:
                    if position != committed[layer] or int(words[1], 16) != 0:
                        raise RuntimeError("BENCH_KV_COMMIT: incorrect parent store completion")
                    expected = []
                    for value in range(2):
                        for dim, raw in enumerate(row["raw_value" if value else "raw_key"]):
                            expected.append((0, 8, 3 + value, dim, None))
                            if workload["cache_mode"] == 0:
                                expected.append((1, 9 + value, position, dim, raw & 0xffffffff))
                            else:
                                record, _, _ = encode_record([raw], 2)
                                expected.append((1, 12 + value, position, dim, record >> 8))
                                expected.append((1, 14 + value, position, dim, record & 255))
                    committed[layer] += 1
                    counters["writes"] += 2 * geometry["head_dim"]
                    counters["commits"] += 1
                elif op in (1, 2):
                    if head != 0 or position >= committed[layer]:
                        raise RuntimeError("BENCH_KV_COMMIT: parent read of uncommitted data")
                    data = row["key" if op == 1 else "value"][dimension]
                    if int(words[1], 16) != data & 0xffffffff:
                        raise RuntimeError("BENCH_KV_NUMERICAL: parent read differs from independent codec")
                    expected = [(0, 8 + op, position, dimension, None)] if workload["cache_mode"] == 0 else [
                        (0, 13 + op, position, dimension, None),
                        (0, 11 + op, position, dimension, None)]
                    counters["reads"] += 1
                    counters["misses"] += 1
                else:
                    raise RuntimeError("BENCH_KV_PROTOCOL: unsupported parent command")
                if len(expected) != len(memory):
                    raise RuntimeError("BENCH_KV_COVERAGE: missing/extra parent memory accesses")
                for (mem_kind, fields), expected_request in zip(memory, expected):
                    actual = tuple(int(field, 16) if index == 4 else int(field)
                                   for index, field in enumerate(fields))
                    if (mem_kind != "PARENT_KV_MEM" or actual[:4] != expected_request[:4] or
                            (expected_request[4] is not None and actual[4] != expected_request[4])):
                        raise RuntimeError("BENCH_KV_NUMERICAL: incorrect parent backing record")
                    write, request_kind = actual[:2]
                    if request_kind == 8:
                        counters["scratch_read_bytes"] += 4
                    else:
                        counters["backing_write_beats" if write else "backing_read_beats"] += 1
                        counters["accepted_backing_bytes"] += 4
                        counters["valid_backing_payload_bytes"] += (
                            4 if workload["cache_mode"] == 0 else 1)
            counters["logical_operations"] += 1
            counters["active_cycles"] += time - active["start"]
            intervals.append((active["start"], time))
            active = None
    required = ("commits", "reads", "writes", "misses", "backing_write_beats", "backing_read_beats")
    if (active is not None or committed != [3] * geometry["layers"] or
            any(counters[key] <= 0 for key in required)):
        raise RuntimeError("BENCH_KV_COVERAGE: missing cache comparisons/completions")
    for key in ("hits", "response_stall_cycles", "memory_request_stall_port_cycles"):
        counters.setdefault(key, 0)
    counters["hit_rate"] = counters["hits"] / counters["reads"]
    counters["backing_read_burst_histogram"] = {"1": counters["backing_read_beats"]}
    return dict(counters), intervals


def analyze(text, workload, implementation, banks=16):
    trace = events(text)
    starts = [(time, int(words[0])) for time, kind, words in trace if kind == "TOKEN"]
    ends = [time for time, kind, _ in trace if kind == "DONE"]
    if len(starts) != 3 or len(ends) != 3:
        raise RuntimeError("BENCH_COVERAGE: expected two prefill tokens and one decode token")
    for position, ((start, token_position), end) in enumerate(zip(starts, ends)):
        if (token_position != position or end <= start or
                (position and start <= ends[position - 1])):
            raise RuntimeError("BENCH_TIMING: overlapping/out-of-order tokens")
    vectors = [(time, int(words[0]), int(words[1]), int(words[2], 16))
               for time, kind, words in trace if kind == "VECTOR"]
    windows = []
    consumed = 0
    for position, ((start, _), end) in enumerate(zip(starts, ends)):
        previous = start
        for stage in (stage for stage in workload["vectors"] if stage["position"] == position):
            count = len(stage["values"])
            observed = vectors[consumed:consumed + count]
            if len(observed) != count:
                raise RuntimeError("BENCH_COVERAGE: missing intermediate vector " + stage["name"])
            indices = set()
            for time, vector, index, value in observed:
                if (not previous < time < end or vector != stage[implementation + "_vector"] or
                        index in indices or not 0 <= index < count or
                        value != stage["values"][index] & 0xffffffff):
                    raise RuntimeError(
                        f"BENCH_NUMERICAL: {implementation} token {position} {stage['name']} "
                        f"vector={vector} index={index} value={value:08x}")
                indices.add(index)
            stop = max(row[0] for row in observed)
            windows.append({"domain": stage["domain"], "name": stage["name"],
                            "position": position, "start": previous, "end": stop,
                            "compared_words": count})
            previous = stop
            consumed += count
        windows.append({"domain": "D5", "name": "vocabulary-projection",
                        "position": position, "start": previous, "end": end,
                        "compared_words": workload["geometry"]["vocabulary"]})
    if consumed != len(vectors):
        raise RuntimeError("BENCH_COVERAGE: unexpected extra intermediate vector writes")
    cache, cache_intervals = cache_observations(trace, workload, implementation)
    useful = payload_bytes(workload) if implementation == "ht" else set()
    rows = {}
    for domain in ("D1", "D2", "D3"):
        selected_windows = [row for row in windows if row["domain"] == domain]
        selected_events = [event for event in trace if any(
            row["start"] < event[0] <= row["end"] for row in selected_windows)]
        cycles = sum(row["end"] - row["start"] for row in selected_windows)
        compared = sum(row["compared_words"] for row in selected_windows)
        if cycles <= 0 or compared <= 0:
            raise RuntimeError("BENCH_COVERAGE: empty domain " + domain)
        row = {**traffic(selected_events, implementation, useful),
               "cycles": cycles, "compared_words": compared, "windows": selected_windows}
        row["valid_payload_bytes_per_cycle"] = row["valid_payload_bytes"] / cycles
        row["tensor_issue_cycle_utilization"] = row["tensor_issue_cycles"] / cycles
        row["tensor_lane_utilization"] = row["tensor_mac_contributions"] / (
            cycles * (128 if implementation == "ht" else 8 * banks))
        row["cache_overlap_cycles"] = sum(
            max(0, min(window["end"], stop) - max(window["start"], start))
            for window in selected_windows for start, stop in cache_intervals)
        if domain == "D3":
            if not all(any(window["start"] <= start and stop <= window["end"]
                           for window in selected_windows) for start, stop in cache_intervals):
                raise RuntimeError("BENCH_TIMING: cache operation outside declared attention window")
            row["cache_hits"], row["cache_misses"] = cache["hits"], cache["misses"]
        else:
            row["cache_hits"], row["cache_misses"] = 0, 0
        accesses = row["cache_hits"] + row["cache_misses"]
        row["cache_hit_rate"] = row["cache_hits"] / accesses if accesses else None
        rows[domain] = row
    expected_macs = 3 * sum(len(stage["values"]) * 8 for stage in workload["vectors"]
                            if stage["position"] == 0 and stage["domain"] == "D1")
    if (rows["D1"]["tensor_mac_contributions"] != expected_macs or
            any(rows[domain]["tensor_mac_contributions"] for domain in ("D2", "D3"))):
        raise RuntimeError("BENCH_MAC_COVERAGE: missing/extra projection MAC contributions")
    rows["D4"] = {**cache, "cycles": cache["active_cycles"],
                  "compared_words": cache["reads"] + cache["writes"],
                  "tensor_issue_events": 0, "tensor_issue_cycle_utilization": 0,
                  "valid_payload_bytes_per_cycle":
                      cache["valid_backing_payload_bytes"] / cache["active_cycles"],
                  "scope": "serialized cache command-to-response windows, overlapping D3"}
    whole = [event for event in trace if any(start <= event[0] <= end
                                           for (start, _), end in zip(starts, ends))]
    cycles = sum(end - start for (start, _), end in zip(starts, ends))
    rows["D5"] = {**traffic(whole, implementation, useful), "cycles": cycles,
                  "compared_logits": len(workload["expected_logits"]),
                  "compared_intermediate_words": consumed,
                  "cache": cache}
    rows["D5"]["valid_payload_bytes_per_cycle"] = rows["D5"]["valid_payload_bytes"] / cycles
    rows["D5"]["tensor_issue_cycle_utilization"] = rows["D5"]["tensor_issue_cycles"] / cycles
    rows["D5"]["tensor_lane_utilization"] = rows["D5"]["tensor_mac_contributions"] / (
        cycles * (128 if implementation == "ht" else 8 * banks))
    marker = "SYSTEM_WORKLOAD_MEASURED" if implementation == "ht" else "PARENT_SYSTEM_CHECKED"
    summaries = re.findall(r"^" + marker + r" (.+)$", text, re.MULTILINE)
    if len(summaries) != 1:
        raise RuntimeError("BENCH_COVERAGE: missing/extra completed workload summary")
    measured = {key: int(value) for key, value in re.findall(r"([a-z_]+)=(\d+)", summaries[0])}
    for traced, original in (("accepted_bytes", "accepted_bytes"),
                             ("read_beats", "reads"), ("write_beats", "writes")):
        if rows["D5"][traced] != measured[original]:
            raise RuntimeError("BENCH_COVERAGE: public-port trace/scoreboard traffic disagreement")
    if implementation == "parent" and (
            rows["D5"]["memory_request_stall_port_cycles"] != measured["request_stalls"]):
        raise RuntimeError("BENCH_COVERAGE: parent trace/scoreboard stall disagreement")
    head_macs = 3 * 3 * 8 if workload["mode"] else 0
    if rows["D5"]["tensor_mac_contributions"] != expected_macs + head_macs:
        raise RuntimeError("BENCH_MAC_COVERAGE: missing whole-workload MAC observations")
    return rows
