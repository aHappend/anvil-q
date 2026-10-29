"""Streaming production-operator oracle, independent of RTL arithmetic.

Synthetic engineering vectors are deliberately not model benchmark inputs.
Each request carries an independently derived address and response word; no
production-sized dense memory or complete transformer checkpoint is allocated.
"""

from collections import defaultdict
import json
import math
import struct
from functools import lru_cache

from architecture import Architecture, PARAMETERS, encode16, metrics
from numerical import bits32, decode, float32


PRODUCTION = (24, 896, 4864, 14, 2, 64, 128, 151936, 32768)
OPERATOR_IDS = {"norm": 0, "rope": 1, "attention": 2, "gemv": 3, "elementwise": 4}
REQUEST_MAGIC = b"ANVQ1OP1"
REQUEST_RECORD = struct.Struct("<7I")


@lru_cache(maxsize=4096, typed=True)
def stored_value(value, mode):
    encoded = encode16(value, mode)
    eb, fb = (8, 7) if mode == 1 else (5, 10)
    return float(decode(encoded, eb, fb)[3])


class OperatorReference(Architecture):
    def __init__(self, config, mode, seed, requests, binary_requests=None):
        self.config = dict(zip(PARAMETERS, config))
        self.mode, self.seed = mode, seed
        self.memory = {}
        self.group = ""
        self.position = 0
        self.requests = requests
        self.binary_requests = binary_requests
        if binary_requests is not None:
            binary_requests.write(REQUEST_MAGIC)
        self.expected_writes = []
        self.count = 0

    def source_value(self, key):
        kind, layer, projection, row, col = key
        if kind == 11:
            angle = row * 1000000.0**(-2*(col//2)/self.config["D"])
            value = math.sin(angle) if col & 1 else math.cos(angle)
            return float32(bits32(value)) if self.mode else round(value*2**30)/2**30
        mixed = self.seed
        for coordinate in key:
            mixed = ((mixed ^ (coordinate+0x9e3779b9))*0x85ebca6b) & 0xffffffff
            mixed ^= mixed >> 13
        if kind == 1:
            return mixed
        if kind == 2:
            return 0x77777777
        if kind == 3:
            return 1/128
        if kind in (5, 6, 7):
            value = (48+(mixed & 31))/64
        else:
            value = ((mixed & 63)-32)/(1024 if kind == 12 else 128)
        if kind in (0, 4, 5, 6, 7, 12):
            return stored_value(value, self.mode or 2)
        return value

    def raw(self, key, value):
        kind = key[0]
        if kind in (1, 2):
            return int(value)
        if kind in (0, 3, 4, 5, 6, 7, 12):
            return encode16(value, self.mode or 2)
        if self.mode:
            return bits32(value)
        return round(value*2**(30 if kind == 11 else 16)) & 0xffffffff

    def emit(self, write, key, raw):
        self.requests.write(f"{write} {' '.join(map(str, key))} {raw:08x}\n")
        if self.binary_requests is not None:
            self.binary_requests.write(REQUEST_RECORD.pack(write, *key, raw))
        self.count += 1

    def read(self, kind, layer=0, proj=0, row=0, col=0):
        key = kind, layer, proj, row, col
        value = self.memory[key] if key in self.memory else self.source_value(key)
        self.emit(0, key, self.raw(key, value))
        return value

    def write(self, kind, value, layer=0, proj=0, row=0, col=0):
        key = kind, layer, proj, row, col
        self.emit(1, key, self.raw(key, value))
        self.expected_writes.append((key, value, self.group))
        self.memory[key] = value

    def execute_operator(self, name, selector, position, layer):
        self.position = position
        if name == "norm":
            self.norm(layer, (0, 7, 0)[selector], (1, 8, 14)[selector],
                      (5, 6, 7)[selector])
        elif name == "rope":
            self.rope(layer)
        elif name == "attention":
            self.attention(layer)
        elif name == "gemv":
            self.gemv(layer, selector)
        elif name == "elementwise":
            self.elementwise(layer, selector)
        else:
            raise ValueError("unknown operator: " + name)


def compare_operator(reference, trace, report, prefix_only=False):
    groups = defaultdict(lambda: ([], []))
    count = 0
    coverage = None
    with trace.open() as stream:
        for line in stream:
            fields = line.split()
            if fields and fields[0] == "C":
                if coverage is not None:
                    raise ValueError("duplicate operator coverage trailer")
                coverage = list(map(int, fields[1:]))
                continue
            if coverage is not None or len(fields) != 8 or fields[0] != "W":
                raise ValueError("malformed operator trace")
            if count >= len(reference.expected_writes):
                raise ValueError("extra operator write")
            key, value, group = reference.expected_writes[count]
            if tuple(map(int, fields[1:6])) != key:
                raise ValueError("operator write address mismatch")
            if reference.mode:
                observed = float32(int(fields[6], 16))
                if not math.isfinite(observed):
                    raise ValueError("operator nonfinite output")
                groups[group][0].append(observed)
                groups[group][1].append(value)
            count += 1
    if coverage is None or len(coverage) != 9:
        raise ValueError("missing operator coverage")
    (requests, responses, writes, request_stalls, response_waits, mode, seed,
     latency, memory_stalls) = coverage
    if (requests != reference.count or requests != responses or writes != count or
            count != len(reference.expected_writes) or count == 0 or
            request_stalls == 0 or response_waits == 0 or
            not 0 < memory_stalls < latency or
            (mode, seed) != (reference.mode, reference.seed)):
        raise ValueError("incomplete operator request/write/precision/seed coverage")
    results = {}
    for name, (actual, expected) in groups.items():
        result = metrics(actual, expected)
        result["passed"] = result["normalized_max_absolute_error"] <= 0.002 and (
            result["reference_all_zero"] or result["cosine"] is not None and
            result["cosine"] >= 0.9999)
        results[name] = result
    passed = all(g["passed"] for g in results.values())
    report.write_text(json.dumps({
        "passed": passed, "groups": results, "writes_compared": count,
        "coverage": coverage, "synthetic_engineering_only": True,
        "prefix_only": prefix_only,
        "prefix_cycles" if prefix_only else "command_latency_cycles": latency,
        "memory_stall_cycles": memory_stalls,
        "non_memory_stall_cycles": latency-memory_stalls,
    }, indent=2) + "\n")
    return passed
