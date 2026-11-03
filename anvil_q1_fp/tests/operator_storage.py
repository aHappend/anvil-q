"""Bounded, lossless operator stimulus storage and checked publication."""

import gzip
import hashlib
import json
import os
import shutil
import struct

REQUEST_MAGIC = b"ANVQ1OP1"
REQUEST_RECORD = struct.Struct("<7I")
BLOCK_BYTES = 1024 * 1024
MAX_COMPRESSED_BYTES = 64 * BLOCK_BYTES
RESERVE_BYTES = 256 * BLOCK_BYTES


class CheckedSink:
    def __init__(self, stream, limit=MAX_COMPRESSED_BYTES):
        self.stream, self.limit = stream, limit
        self.bytes = 0

    def write(self, data):
        if self.bytes + len(data) > self.limit:
            raise OSError("operator compressed-input byte budget exhausted")
        count = self.stream.write(data)
        if count != len(data):
            raise OSError("short operator input write")
        self.bytes += count
        return count

    def flush(self):
        self.stream.flush()


def file_hash(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(BLOCK_BYTES), b""):
            value.update(block)
    return value.hexdigest()


class RequestWriter:
    def __init__(self, path, limit=MAX_COMPRESSED_BYTES):
        self.path = path
        self.limit = limit
        self.reserve = min(RESERVE_BYTES, max(16 * BLOCK_BYTES, 4 * limit))
        free = shutil.disk_usage(path.parent).free
        if free < self.reserve + 4 * limit:
            raise OSError("operator storage headroom below concurrent-input budget: "
                          f"free={free}, required={self.reserve + 4 * limit}")
        self.raw = path.open("xb")
        self.sink = CheckedSink(self.raw, limit)
        try:
            self.compressed = gzip.GzipFile(filename="", mode="wb", fileobj=self.sink,
                                            compresslevel=6, mtime=0)
        except OSError:
            self.raw.close()
            raise
        self.hash = hashlib.sha256(REQUEST_MAGIC)
        self.count = 0
        self.buffer = bytearray(REQUEST_MAGIC)
        self.metadata = None

    def emit(self, write, key, raw):
        record = REQUEST_RECORD.pack(write, *key, raw)
        self.hash.update(record)
        self.buffer.extend(record)
        self.count += 1
        if len(self.buffer) >= BLOCK_BYTES:
            self._flush_block()

    def _flush_block(self):
        if self.compressed.write(self.buffer) != len(self.buffer):
            raise OSError("short compressed operator input write")
        self.buffer.clear()

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        try:
            if kind is None:
                self._flush_block()
            self.compressed.close()
            self.raw.flush()
            os.fsync(self.raw.fileno())
        finally:
            self.raw.close()
        if kind is None:
            count, decoded_hash = inspect_requests(self.path)
            if count != self.count or decoded_hash != self.hash.hexdigest():
                raise ValueError("operator input producer/readback mismatch")
            self.metadata = {
                "format": "gzip-ANVQ1OP1-le7I", "records": count,
                "decoded_bytes": len(REQUEST_MAGIC) + count * REQUEST_RECORD.size,
                "decoded_sha256": decoded_hash,
                "compressed_bytes": self.path.stat().st_size,
                "compressed_sha256": file_hash(self.path),
                "compressed_limit_bytes": self.limit,
                "concurrent_input_budget_bytes": 4 * self.limit,
                "reserved_free_bytes": self.reserve,
                "free_bytes_after_publication": shutil.disk_usage(self.path.parent).free,
            }
            manifest = self.path.with_suffix(self.path.suffix + ".json")
            payload = json.dumps(self.metadata, indent=2) + "\n"
            with manifest.open("x") as stream:
                if stream.write(payload) != len(payload):
                    raise OSError("short operator input manifest write")
                stream.flush()
                os.fsync(stream.fileno())


def request_records(path):
    try:
        with gzip.open(path, "rb") as stream:
            if stream.read(len(REQUEST_MAGIC)) != REQUEST_MAGIC:
                raise ValueError("invalid operator request header")
            while True:
                block = stream.read(REQUEST_RECORD.size * 16384)
                if len(block) % REQUEST_RECORD.size:
                    raise ValueError("truncated operator request record")
                if not block:
                    break
                yield from REQUEST_RECORD.iter_unpack(block)
    except EOFError as error:
        raise ValueError("truncated operator gzip stream") from error


def inspect_requests(path):
    value = hashlib.sha256(REQUEST_MAGIC)
    count = 0
    for fields in request_records(path):
        value.update(REQUEST_RECORD.pack(*fields))
        count += 1
    return count, value.hexdigest()


def request_count(config, name, selector, mode, position):
    _, hidden, intermediate, query, kv, dimension, group, _, _ = config
    if name == "norm":
        return 4 * hidden
    if name == "rope":
        return 3 * (hidden + kv * dimension)
    if name == "attention":
        times = position + 1
        return 4 * kv * dimension + query * (
            2 * dimension * times + dimension * times * (2 * dimension + 1) + dimension)
    if name == "elementwise":
        return 3 * (intermediate if selector == 2 else hidden)
    if name != "gemv":
        raise ValueError("unknown operator request budget: " + name)
    inputs = intermediate if selector == 6 else hidden
    outputs = (kv * dimension if selector in (1, 2) else
               intermediate if selector in (4, 5) else hidden)
    reads = inputs * 9 if mode else inputs * 2 + 9 * (inputs // group)
    return outputs // 8 * reads + outputs * (2 if selector < 3 else 1)


def storage_limit(records):
    raw = len(REQUEST_MAGIC) + records * REQUEST_RECORD.size
    return min(MAX_COMPRESSED_BYTES, max(BLOCK_BYTES, raw + raw // 100 + 1024))


def export_text(source, target):
    """Compact portability fixtures only; production never duplicates streams."""
    with target.open("x") as stream:
        for fields in request_records(source):
            line = f"{' '.join(map(str, fields[:6]))} {fields[6]:08x}\n"
            if stream.write(line) != len(line):
                raise OSError("short operator text export")


def publication(trace, stdout):
    markers = [line.split() for line in stdout.read_text().splitlines()
               if line.startswith("OPERATOR_TRACE_PUBLISHED ")]
    if len(markers) != 1 or len(markers[0]) != 3:
        raise ValueError("missing operator trace publication")
    size, writes = map(int, markers[0][1:])
    if trace.stat().st_size != size or size <= 0 or writes <= 0:
        raise ValueError("incomplete operator trace publication")
    with trace.open() as stream:
        observed = sum(line.startswith("W ") for line in stream)
    if observed != writes:
        raise ValueError("incomplete operator trace write publication")
    return {"bytes": size, "writes": writes, "sha256": file_hash(trace)}
