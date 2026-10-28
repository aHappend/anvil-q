"""V2 lossless transaction framing with bounded buffers and a sparse disk index.

SHA-256 binds framing, order, encoded bytes and decoded records. These are
integrity bindings, not a signature authenticating the producer. V1 arrays and
transactions remain readable without conversion.
"""

from collections import OrderedDict
import hashlib
import json
import os
from pathlib import Path
import struct
import zlib

from benchmark import load_json, require
from packed_storage import (CHUNK_BYTES, ENTRY, FOOTER, HEADER_LIMIT, MAX_BYTES,
                            RECORD, Reader, Writer, delta_encode, digest,
                            file_identity, integer)


MAGIC = b"AQTXN002"
END = b"AQEND002"
FRAME = ENTRY
SPARSE = struct.Struct("<Q")
STRIDE = 64
TRACE_CHUNK_BYTES = 64 * CHUNK_BYTES // RECORD.size * RECORD.size


def layout(raw_bytes, chunk_bytes=TRACE_CHUNK_BYTES):
    require(integer(raw_bytes) and raw_bytes % RECORD.size == 0 and
            integer(chunk_bytes, RECORD.size, TRACE_CHUNK_BYTES) and
            chunk_bytes % RECORD.size == 0, "invalid v2 transaction extent")
    frames = (raw_bytes + chunk_bytes - 1) // chunk_bytes
    indexes = (frames + STRIDE - 1) // STRIDE
    return frames, indexes


def bound(raw_bytes, chunk_bytes=TRACE_CHUNK_BYTES):
    """Raw fallback plus every frame, sparse entry and maximal header/footer."""
    frames, indexes = layout(raw_bytes, chunk_bytes)
    return 12 + HEADER_LIMIT + raw_bytes + frames * FRAME.size + indexes * SPARSE.size + FOOTER.size


class TransactionWriter(Writer):
    def __init__(self, path, *, chunk_bytes=TRACE_CHUNK_BYTES):
        layout(0, chunk_bytes)
        self.header = {"schema": 2, "kind": "transactions", "record_bytes": RECORD.size,
                       "chunk_bytes": chunk_bytes, "index_stride": STRIDE}
        encoded = json.dumps(self.header, sort_keys=True, separators=(",", ":")).encode("ascii")
        self.prefix = MAGIC + struct.pack("<I", len(encoded)) + encoded
        self.path = Path(path)
        self.stream = self.path.open("xb")
        self.index_path = self.path.with_name(self.path.name + ".index-partial")
        try:
            self.index_stream = self.index_path.open("x+b")
            require(self.stream.write(self.prefix) == len(self.prefix),
                    "v2 transaction header short write")
        except BaseException:
            self.stream.close()
            if hasattr(self, "index_stream"):
                self.index_stream.close()
            raise
        self.expected = None
        self.width = RECORD.size
        self.entry_count = self.total = self.previous_cycle = 0
        self.buffer = bytearray()
        self.closed = self.sealed = False
        self.checksum = hashlib.sha256(self.prefix)

    def _chunk(self, raw):
        candidate = zlib.compress(delta_encode(raw), 6)
        method = 2
        if len(candidate) >= len(raw):
            candidate, method = raw, 0
        if self.entry_count % STRIDE == 0:
            entry = SPARSE.pack(self.stream.tell())
            require(self.index_stream.write(entry) == len(entry), "v2 sparse spool short write")
        frame = FRAME.pack(self.entry_count, len(candidate), len(raw), method,
                           digest(candidate), digest(raw))
        require(self.stream.write(frame) == len(frame) and
                self.stream.write(candidate) == len(candidate), "v2 frame short write")
        self.checksum.update(frame)
        self.entry_count += 1

    def close(self):
        require(not self.closed, "packed writer already closed")
        try:
            if self.buffer:
                self._chunk(bytes(self.buffer))
                self.buffer.clear()
            offset = self.stream.tell()
            frames, entries = layout(self.total, self.header["chunk_bytes"])
            require(frames == self.entry_count and
                    self.index_stream.tell() == entries * SPARSE.size,
                    "v2 sparse spool extent differs")
            self.index_stream.flush()
            self.index_stream.seek(0)
            while raw := self.index_stream.read(CHUNK_BYTES):
                self.checksum.update(raw)
                require(self.stream.write(raw) == len(raw), "v2 sparse index short write")
            footer = FOOTER.pack(offset, frames, self.total, self.checksum.digest(), END)
            require(self.stream.write(footer) == len(footer), "v2 footer short write")
            self.stream.flush()
        finally:
            self.closed = True
            try:
                self.stream.close()
            finally:
                self.index_stream.close()
        self.index_path.unlink()
        self.sealed = True


class FrameEntries:
    """At most STRIDE frame headers per seek, without a resident frame list."""

    def __init__(self, path, offset, count, identity):
        self.path, self.offset, self.count, self.identity = path, offset, count, identity

    def __len__(self):
        return self.count

    def unchanged(self):
        require(file_identity(self.path.stat()) == self.identity,
                "packed source changed after index validation")

    def __getitem__(self, number):
        require(integer(number) and number < self.count, "v2 frame index out of bounds")
        self.unchanged()
        with self.path.open("rb") as stream:
            require(file_identity(os.fstat(stream.fileno())) == self.identity,
                    "packed source changed after index validation")
            stream.seek(self.offset + number // STRIDE * SPARSE.size)
            raw = stream.read(SPARSE.size)
            require(len(raw) == SPARSE.size, "truncated v2 sparse entry")
            cursor, = SPARSE.unpack(raw)
            for ordinal in range(number // STRIDE * STRIDE, number + 1):
                stream.seek(cursor)
                raw = stream.read(FRAME.size)
                require(len(raw) == FRAME.size, "truncated v2 frame")
                index, encoded, decoded, method, encoded_hash, raw_hash = FRAME.unpack(raw)
                require(index == ordinal, "reordered v2 frame")
                cursor += FRAME.size
                if ordinal == number:
                    result = cursor, encoded, decoded, method, encoded_hash, raw_hash
                cursor += encoded
            require(file_identity(os.fstat(stream.fileno())) == self.identity,
                    "packed source changed during frame lookup")
        self.unchanged()
        return result

    def __iter__(self):
        for number in range(self.count):
            yield self[number]


class TransactionReader(Reader):
    def __init__(self, path, *, dtype=None, shape=None, axes=None):
        require(dtype is shape is axes is None, "v2 transaction/array metadata mixed")
        self.path = Path(path)
        with self.path.open("rb") as stream:
            identity = file_identity(os.fstat(stream.fileno()))
            size = identity[2]
            require(size >= 12 + FOOTER.size, "truncated v2 container")
            prefix = stream.read(12)
            require(prefix[:8] == MAGIC, "unknown transaction storage version")
            length, = struct.unpack("<I", prefix[8:])
            require(0 < length <= HEADER_LIMIT and length <= size - 12 - FOOTER.size,
                    "invalid v2 header extent")
            encoded = stream.read(length)

            class Header:
                def read_text(self):
                    try:
                        return encoded.decode("ascii")
                    except UnicodeError as error:
                        raise ValueError("non-ASCII v2 header") from error

            self.header = load_json(Header())
            header = self.header
            require(isinstance(header, dict) and set(header) == {
                "schema", "kind", "record_bytes", "chunk_bytes", "index_stride"} and
                type(header["schema"]) is int and header["schema"] == 2 and
                header["kind"] == "transactions" and
                type(header["record_bytes"]) is int and header["record_bytes"] == RECORD.size and
                type(header["index_stride"]) is int and header["index_stride"] == STRIDE,
                "invalid v2 transaction header")
            chunk = header["chunk_bytes"]
            layout(0, chunk)
            self.width = RECORD.size
            stream.seek(-FOOTER.size, 2)
            offset, count, self.total, checksum, end = FOOTER.unpack(stream.read(FOOTER.size))
            frames, indexes = layout(self.total, chunk)
            require(end == END and count == frames and
                    12 + length <= offset <= size - FOOTER.size and
                    offset + indexes * SPARSE.size + FOOTER.size == size,
                    "invalid/truncated v2 sparse extent")
            calculated = hashlib.sha256(prefix + encoded)
            cursor = 12 + length
            for number in range(count):
                require(cursor + FRAME.size <= offset, "truncated v2 frame header")
                if number % STRIDE == 0:
                    stream.seek(offset + number // STRIDE * SPARSE.size)
                    entry, = SPARSE.unpack(stream.read(SPARSE.size))
                    require(entry == cursor, "reordered/overlapping v2 sparse index")
                stream.seek(cursor)
                raw = stream.read(FRAME.size)
                ordinal, encoded_size, decoded, method, _, _ = FRAME.unpack(raw)
                expected = min(chunk, self.total - number * chunk)
                require(ordinal == number and decoded == expected and
                        0 < encoded_size <= decoded and
                        (method == 0 and encoded_size == decoded or method == 2) and
                        cursor + FRAME.size + encoded_size <= offset,
                        "invalid/reordered v2 frame extent or codec")
                calculated.update(raw)
                cursor += FRAME.size + encoded_size
            require(cursor == offset, "unframed v2 payload")
            stream.seek(offset)
            remaining = indexes * SPARSE.size
            while remaining:
                raw = stream.read(min(CHUNK_BYTES, remaining))
                require(len(raw) == min(CHUNK_BYTES, remaining), "truncated v2 sparse index")
                calculated.update(raw)
                remaining -= len(raw)
            require(calculated.digest() == checksum, "damaged v2 header/frames/index")
            require(file_identity(os.fstat(stream.fileno())) == identity,
                    "packed source changed during index validation")
        self.entries = FrameEntries(self.path, offset, count, identity)
        self.entries.unchanged()
        self.cache = OrderedDict()

    def records(self, start, count):
        """Bounded arbitrary record slice, retaining every original word."""
        require(integer(start) and integer(count) and
                start + count <= self.total // RECORD.size, "v2 record slice out of bounds")
        chunk = self.header["chunk_bytes"]
        while count:
            number, within = divmod(start * RECORD.size, chunk)
            raw = self.chunk(number)
            take = min(count, (len(raw) - within) // RECORD.size)
            yield from RECORD.iter_unpack(raw[within:within + take * RECORD.size])
            start += take
            count -= take
