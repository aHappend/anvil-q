"""Versioned lossless verification storage, independent of inference and RTL.

Containers are immutable after sealing. Per-chunk raw fallback bounds expansion;
hashes bind both encoded bytes and exact decoded bits. Arrays retain C-order
axes, while transaction chunks delta-encode ordered public-pin records. Neither
independently executed observations nor repeats are shared or deduplicated.
"""

import hashlib
from collections import OrderedDict
import json
import math
import os
from pathlib import Path
import struct
import zlib

from benchmark import load_json, require


MAGIC = b"AQPACK01"
END = b"AQEND001"
ENTRY = struct.Struct("<QQQB7x32s32s")
FOOTER = struct.Struct("<QQQ32s8s")
RECORD = struct.Struct("<11I")
CHUNK_BYTES = 1024 * 1024
HEADER_LIMIT = 65536
MAX_BYTES = (1 << 63) - 1
DTYPES = {"<f4": 4, "<f8": 8, "<u4": 4}
INDEX_BLOCK_BYTES = CHUNK_BYTES // ENTRY.size * ENTRY.size


def file_identity(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


class IndexEntries:
    """Random-access sealed index without a workload-sized Python object list."""

    def __init__(self, path, offset, count, identity):
        self.path, self.offset, self.count, self.identity = path, offset, count, identity

    def __len__(self):
        return self.count

    def unchanged(self):
        require(file_identity(self.path.stat()) == self.identity,
                "packed source changed after index validation")

    def __getitem__(self, number):
        require(integer(number) and number < self.count, "packed index out of bounds")
        with self.path.open("rb") as stream:
            require(file_identity(os.fstat(stream.fileno())) == self.identity,
                    "packed source changed after index validation")
            stream.seek(self.offset + number * ENTRY.size)
            raw = stream.read(ENTRY.size)
            require(len(raw) == ENTRY.size and
                    file_identity(os.fstat(stream.fileno())) == self.identity,
                    "packed index changed during read")
        self.unchanged()
        return ENTRY.unpack(raw)

    def __iter__(self):
        with self.path.open("rb") as stream:
            require(file_identity(os.fstat(stream.fileno())) == self.identity,
                    "packed source changed after index validation")
            stream.seek(self.offset)
            remaining = self.count * ENTRY.size
            while remaining:
                raw = stream.read(min(INDEX_BLOCK_BYTES, remaining))
                require(len(raw) == min(INDEX_BLOCK_BYTES, remaining),
                        "truncated packed index")
                remaining -= len(raw)
                yield from ENTRY.iter_unpack(raw)
            require(file_identity(os.fstat(stream.fileno())) == self.identity,
                    "packed index changed during iteration")
        self.unchanged()


def digest(data):
    return hashlib.sha256(data).digest()


def integer(value, low=0, high=MAX_BYTES):
    return type(value) is int and low <= value <= high


def dimensions(dtype, shape, axes):
    require(isinstance(dtype, str) and dtype in DTYPES, "unsupported packed dtype")
    require(isinstance(shape, list) and shape and
            all(integer(value, 1) for value in shape),
            "invalid packed shape")
    require(isinstance(axes, list) and len(axes) == len(shape) and
            all(isinstance(axis, str) and axis and axis.isascii() and len(axis) <= 64
                for axis in axes) and len(set(axes)) == len(axes),
            "invalid packed axes")
    size = math.prod(shape) * DTYPES[dtype]
    require(size <= MAX_BYTES, "packed array size overflow")
    return size


def shuffled(data, width):
    require(len(data) % width == 0, "unaligned packed array bytes")
    return b"".join(data[index::width] for index in range(width))


def unshuffled(data, width):
    require(len(data) % width == 0, "unaligned shuffled bytes")
    result = bytearray(len(data))
    count = len(data) // width
    for index in range(width):
        result[index::width] = data[index * count:(index + 1) * count]
    return bytes(result)


def inflate(data, maximum):
    decoder = zlib.decompressobj()
    try:
        raw = decoder.decompress(data, maximum + 1)
    except zlib.error as error:
        raise ValueError("damaged packed compression stream") from error
    require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
            and len(raw) <= maximum, "truncated, trailing or oversized packed stream")
    return raw


def varint(value):
    require(integer(value, 0, (1 << 64) - 1), "transaction varint overflow")
    output = bytearray()
    while value >= 128:
        output.append((value & 127) | 128)
        value >>= 7
    output.append(value)
    return bytes(output)


def take_varint(data, offset):
    start = offset
    value = 0
    for shift in range(0, 70, 7):
        require(offset < len(data), "truncated transaction varint")
        byte = data[offset]
        offset += 1
        require(shift != 63 or byte <= 1, "transaction varint overflow")
        value |= (byte & 127) << shift
        if not byte & 128:
            require(offset == start + 1 or byte != 0, "noncanonical transaction varint")
            return value, offset
    raise ValueError("transaction varint overflow")


def transaction_fields(raw, previous=0):
    require(len(raw) % RECORD.size == 0, "partial transaction record")
    for words in RECORD.iter_unpack(raw):
        accepted = words[0] | words[1] << 32
        completed = words[2] | words[3] << 32
        require(previous <= accepted < completed and words[4] in (0, 1),
                "overlapping or out-of-order transaction (single-outstanding cycle order) "
                "or invalid write field")
        previous = completed
        yield accepted, completed, words[4:]


def delta_encode(raw):
    output = bytearray()
    previous_cycle = 0
    previous_fields = (0,) * 6
    for accepted, completed, fields in transaction_fields(raw):
        output.extend(varint(accepted - previous_cycle))
        output.extend(varint(completed - accepted))
        for value, previous in zip(fields[:6], previous_fields):
            change = value - previous
            output.extend(varint(2 * change if change >= 0 else -2 * change - 1))
        output.extend(struct.pack("<I", fields[6]))
        previous_cycle, previous_fields = completed, fields[:6]
    return bytes(output)


def delta_decode(data, count, *, maximum_bytes=CHUNK_BYTES):
    require(integer(maximum_bytes, RECORD.size, 64 * CHUNK_BYTES) and
            integer(count, 1) and count <= maximum_bytes // RECORD.size,
            "invalid transaction chunk count")
    offset = previous_cycle = 0
    previous_fields = (0,) * 6
    output = bytearray()
    for _ in range(count):
        gap, offset = take_varint(data, offset)
        duration, offset = take_varint(data, offset)
        accepted, completed = previous_cycle + gap, previous_cycle + gap + duration
        require(previous_cycle <= accepted < completed < 1 << 64,
                "transaction cycle overflow/order")
        fields = []
        for previous in previous_fields:
            value, offset = take_varint(data, offset)
            change = value // 2 if not value & 1 else -(value // 2) - 1
            current = previous + change
            require(integer(current, 0, (1 << 32) - 1), "transaction field overflow")
            fields.append(current)
        require(fields[0] in (0, 1) and offset + 4 <= len(data),
                "invalid transaction write/payload")
        payload, = struct.unpack_from("<I", data, offset)
        offset += 4
        output.extend(RECORD.pack(accepted & 0xffffffff, accepted >> 32,
                                  completed & 0xffffffff, completed >> 32,
                                  *fields, payload))
        previous_cycle, previous_fields = completed, fields
    require(offset == len(data), "trailing transaction delta bytes")
    return bytes(output)


class Writer:
    def __init__(self, path, *, dtype=None, shape=None, axes=None, transactions=False):
        if transactions:
            require(dtype is shape is axes is None, "transaction/array metadata mixed")
            self.header = {"schema": 1, "kind": "transactions", "record_bytes": RECORD.size,
                           "chunk_bytes": CHUNK_BYTES // RECORD.size * RECORD.size}
            self.expected = None
            self.width = RECORD.size
        else:
            self.expected = dimensions(dtype, shape, axes)
            self.width = DTYPES[dtype]
            self.header = {"schema": 1, "kind": "array", "dtype": dtype, "shape": shape,
                           "axes": axes, "chunk_bytes": CHUNK_BYTES}
        encoded = json.dumps(self.header, sort_keys=True, separators=(",", ":")).encode("ascii")
        require(len(encoded) <= HEADER_LIMIT, "packed header too large")
        self.prefix = MAGIC + struct.pack("<I", len(encoded)) + encoded
        self.path = Path(path)
        self.stream = self.path.open("xb")
        self.index_path = self.path.with_name(self.path.name + ".index-partial")
        try:
            self.index_stream = self.index_path.open("x+b")
            require(self.stream.write(self.prefix) == len(self.prefix),
                    "packed header short write")
        except BaseException:
            self.stream.close()
            if hasattr(self, "index_stream"):
                self.index_stream.close()
            raise
        self.entry_count = 0
        self.buffer = bytearray()
        self.total = 0
        self.previous_cycle = 0
        self.sealed = False
        self.closed = False

    def append(self, raw):
        require(not self.closed and isinstance(raw, (bytes, bytearray, memoryview)),
                "invalid append to packed writer")
        require(len(raw) % self.width == 0 and self.total + len(raw) <= MAX_BYTES and
                (self.expected is None or self.total + len(raw) <= self.expected),
                "packed append length/overflow")
        if self.header["kind"] == "transactions":
            for _, completed, _ in transaction_fields(raw, self.previous_cycle):
                self.previous_cycle = completed
        self.total += len(raw)
        size = self.header["chunk_bytes"]
        view = memoryview(raw)
        offset = 0
        if self.buffer:
            count = min(size - len(self.buffer), len(view))
            self.buffer.extend(view[:count])
            offset = count
            if len(self.buffer) == size:
                self._chunk(bytes(self.buffer))
                self.buffer.clear()
        while len(view) - offset >= size:
            self._chunk(bytes(view[offset:offset+size]))
            offset += size
        self.buffer.extend(view[offset:])

    def _chunk(self, raw):
        if self.header["kind"] == "transactions":
            candidate = zlib.compress(delta_encode(raw), 6)
            method = 2
        else:
            candidate = zlib.compress(shuffled(raw, self.width), 6)
            method = 1
        if len(candidate) >= len(raw):
            method, candidate = 0, raw
        offset = self.stream.tell()
        require(self.stream.write(candidate) == len(candidate), "packed payload short write")
        entry = ENTRY.pack(offset, len(candidate), len(raw), method,
                           digest(candidate), digest(raw))
        require(self.index_stream.write(entry) == len(entry), "packed index spool short write")
        self.entry_count += 1

    def reshape(self, shape, axes):
        """Seal a shorter observation fragment without staging raw payload."""
        require(not self.closed and self.header["kind"] == "array",
                "reshape requires an unsealed array")
        expected = dimensions(self.header["dtype"], shape, axes)
        require(expected == self.total and expected <= self.expected,
                "fragment shape differs from written bytes")
        header = {**self.header, "shape": shape, "axes": axes}
        encoded = json.dumps(header, sort_keys=True, separators=(",", ":")).encode("ascii")
        length = len(self.prefix) - 12
        require(len(encoded) <= length, "fragment header exceeds reserved extent")
        prefix = MAGIC + struct.pack("<I", length) + encoded.ljust(length, b" ")
        offset = self.stream.tell()
        self.stream.seek(0)
        require(self.stream.write(prefix) == len(prefix), "fragment header short write")
        self.stream.seek(offset)
        self.prefix, self.header, self.expected = prefix, header, expected

    def write(self, raw):
        self.append(raw)
        return len(raw)

    def close(self):
        require(not self.closed, "packed writer already closed")
        try:
            require(self.expected is None or self.total == self.expected,
                    "incomplete packed array")
            if self.buffer:
                self._chunk(bytes(self.buffer))
                self.buffer.clear()
            offset = self.stream.tell()
            self.index_stream.flush()
            require(self.index_stream.tell() == self.entry_count * ENTRY.size,
                    "packed index spool extent differs")
            self.index_stream.seek(0)
            checksum = hashlib.sha256(self.prefix)
            while index := self.index_stream.read(INDEX_BLOCK_BYTES):
                checksum.update(index)
                require(self.stream.write(index) == len(index), "packed index short write")
            require(self.stream.tell() == offset + self.entry_count * ENTRY.size,
                    "packed index copy extent differs")
            footer = FOOTER.pack(offset, self.entry_count, self.total, checksum.digest(), END)
            require(self.stream.write(footer) == len(footer), "packed footer short write")
            self.stream.flush()
        finally:
            self.closed = True
            try:
                self.stream.close()
            finally:
                self.index_stream.close()
        # A failed seal retains both partial files. Only a completed seal removes
        # this invocation's exclusively created index staging file.
        self.index_path.unlink()
        self.sealed = True

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        if kind is None:
            self.close()
        else:
            self.closed = True
            try:
                self.stream.close()
            finally:
                self.index_stream.close()


class Reader:
    def __new__(cls, path, *, dtype=None, shape=None, axes=None):
        if cls is Reader:
            with Path(path).open("rb") as stream:
                magic = stream.read(8)
            if magic == b"AQTXN002":
                from sparse_transactions import TransactionReader
                return object.__new__(TransactionReader)
        return super().__new__(cls)

    def __init__(self, path, *, dtype=None, shape=None, axes=None):
        self.path = Path(path)
        with self.path.open("rb") as stream:
            identity = file_identity(os.fstat(stream.fileno()))
            size = identity[2]
            require(size >= 12 + FOOTER.size, "truncated packed container")
            prefix = stream.read(12)
            require(prefix[:8] == MAGIC, "unknown packed storage version")
            length, = struct.unpack("<I", prefix[8:])
            require(0 < length <= HEADER_LIMIT and length <= size - 12 - FOOTER.size,
                    "invalid packed header extent")
            header_bytes = stream.read(length)
            # Use the repository JSON decoder to reject duplicates/nonfinite values.
            class Header:
                def read_text(self):
                    try:
                        return header_bytes.decode("ascii")
                    except UnicodeError as error:
                        raise ValueError("non-ASCII packed header") from error
            self.header = load_json(Header())
            header = self.header
            require(isinstance(header, dict) and type(header.get("schema")) is int and
                    header["schema"] == 1,
                    "invalid packed header")
            if header.get("kind") == "array":
                require(set(header) == {"schema", "kind", "dtype", "shape", "axes", "chunk_bytes"},
                        "unexpected packed array metadata")
                expected = dimensions(header["dtype"], header["shape"], header["axes"])
                self.width = DTYPES[header["dtype"]]
                chunk_bytes = CHUNK_BYTES
                if dtype is not None or shape is not None or axes is not None:
                    require((dtype, shape, axes) ==
                            (header["dtype"], header["shape"], header["axes"]),
                            "packed array dtype/shape/axes differ")
            else:
                require(header.get("kind") == "transactions" and
                        set(header) == {"schema", "kind", "record_bytes", "chunk_bytes"} and
                        type(header["record_bytes"]) is int and header["record_bytes"] == RECORD.size and
                        dtype is shape is axes is None, "invalid transaction header")
                expected = None
                self.width = RECORD.size
                chunk_bytes = CHUNK_BYTES // RECORD.size * RECORD.size
            require(type(header["chunk_bytes"]) is int and header["chunk_bytes"] == chunk_bytes,
                    "invalid packed chunk size")
            stream.seek(-FOOTER.size, 2)
            offset, count, self.total, index_digest, magic = FOOTER.unpack(stream.read(FOOTER.size))
            require(magic == END and 0 <= self.total <= MAX_BYTES and
                    self.total % self.width == 0 and
                    (expected is None or self.total == expected) and
                    count == (self.total + chunk_bytes - 1) // chunk_bytes and
                    12 + length <= offset <= size - FOOTER.size and
                    count * ENTRY.size == size - FOOTER.size - offset,
                    "invalid/truncated packed index extent")
            stream.seek(offset)
            checksum = hashlib.sha256(prefix + header_bytes)
            remaining = count * ENTRY.size
            cursor = 12 + length
            number = 0
            while remaining:
                index = stream.read(min(INDEX_BLOCK_BYTES, remaining))
                require(len(index) == min(INDEX_BLOCK_BYTES, remaining),
                        "truncated packed index")
                remaining -= len(index)
                checksum.update(index)
                for start, encoded, decoded, method, _, _ in ENTRY.iter_unpack(index):
                    expected_chunk = min(chunk_bytes, self.total - number * chunk_bytes)
                    require(start == cursor and decoded == expected_chunk and
                            0 < encoded <= decoded and
                            (method == 0 and encoded == decoded or
                             method == (1 if header["kind"] == "array" else 2)),
                            "invalid/overlapping/reordered packed chunk extent or codec")
                    cursor += encoded
                    number += 1
            require(checksum.digest() == index_digest,
                    "damaged packed header/index")
            require(cursor == offset, "unindexed packed payload")
            require(file_identity(os.fstat(stream.fileno())) == identity,
                    "packed source changed during index validation")
        self.entries = IndexEntries(self.path, offset, count, identity)
        self.entries.unchanged()
        self.cache = OrderedDict()

    def chunk(self, number):
        require(integer(number) and number < len(self.entries), "packed chunk index out of bounds")
        self.entries.unchanged()
        if number in self.cache:
            self.cache.move_to_end(number)
            return self.cache[number]
        start, length, decoded, method, encoded_hash, raw_hash = self.entries[number]
        with self.path.open("rb") as stream:
            stream.seek(start)
            encoded = stream.read(length)
        require(len(encoded) == length and digest(encoded) == encoded_hash,
                "damaged/truncated packed payload")
        if method == 0:
            raw = encoded
        elif method == 1:
            raw = unshuffled(inflate(encoded, decoded), self.width)
        else:
            # Two cycle varints, six field varints and one u32: at most 54 bytes/record.
            delta = inflate(encoded, decoded // RECORD.size * 54)
            raw = delta_decode(delta, decoded // RECORD.size,
                               maximum_bytes=self.header["chunk_bytes"])
        require(len(raw) == decoded and digest(raw) == raw_hash, "decoded packed hash differs")
        self.entries.unchanged()
        self.cache[number] = raw
        if len(self.cache) > 2:
            self.cache.popitem(last=False)
        return raw

    def chunks(self):
        previous = 0
        for number in range(len(self.entries)):
            raw = self.chunk(number)
            if self.header["kind"] == "transactions":
                for _, completed, _ in transaction_fields(raw, previous):
                    previous = completed
            yield raw

    def read(self, offset, length):
        require(self.header["kind"] == "array" and integer(offset) and integer(length) and
                offset % self.width == length % self.width == 0 and
                offset + length <= self.total, "packed array read extent/alignment")
        output = bytearray()
        while length:
            number, within = divmod(offset, self.header["chunk_bytes"])
            raw = self.chunk(number)
            count = min(length, len(raw) - within)
            output.extend(raw[within:within + count])
            offset += count
            length -= count
        return bytes(output)

    def view(self, origin, shape, steps=None):
        """C-order rectangular strided view; never converts floating-point bits."""
        require(self.header["kind"] == "array", "view requires a packed array")
        dimensions_ = self.header["shape"]
        steps = [1] * len(dimensions_) if steps is None else steps
        require(all(isinstance(value, list) and len(value) == len(dimensions_)
                    for value in (origin, shape, steps)) and
                all(integer(start) and integer(count, 1) and integer(step, 1) and
                    start + (count - 1) * step < size
                    for start, count, step, size in zip(origin, shape, steps, dimensions_)),
                "packed view shape/origin/stride out of bounds")
        # Coalesce contiguous last-axis reads; vocabulary-major position views
        # intentionally retain their strided offsets instead of transposing data.
        strides = [math.prod(dimensions_[index + 1:]) for index in range(len(dimensions_))]
        output = bytearray()

        def visit(axis, base):
            if axis == len(shape) - 1 and steps[axis] == 1:
                output.extend(self.read((base + origin[axis]) * self.width,
                                        shape[axis] * self.width))
            elif axis == len(shape):
                output.extend(self.read(base * self.width, self.width))
            else:
                for index in range(shape[axis]):
                    visit(axis + 1, base + (origin[axis] + index * steps[axis]) * strides[axis])
        visit(0, 0)
        return bytes(output)


def bound(raw_bytes, *, transactions=False):
    """Conservative logical file bound, independent of any compression ratio."""
    require(integer(raw_bytes, 0 if transactions else 1), "invalid packed capacity input")
    chunk = CHUNK_BYTES // RECORD.size * RECORD.size if transactions else CHUNK_BYTES
    require(not transactions or raw_bytes % RECORD.size == 0, "partial trace capacity input")
    return 12 + HEADER_LIMIT + raw_bytes + ((raw_bytes + chunk - 1) // chunk) * ENTRY.size + FOOTER.size


def pack_array(source, destination, dtype, shape, axes):
    require(Path(source).stat().st_size == dimensions(dtype, shape, axes),
            "source array size differs")
    with Writer(destination, dtype=dtype, shape=shape, axes=axes) as writer:
        with Path(source).open("rb") as stream:
            while raw := stream.read(CHUNK_BYTES):
                writer.append(raw)

def array_output(directory, name, dtype, shape, axes, *, packed=False):
    """Open a direct producer, retaining the legacy byte layout when requested."""
    dimensions(dtype, shape, axes)
    require(name in ("layers", "logits") and dtype in ("<f4", "<f8"),
            "invalid producer array")
    suffix = ".aqp" if packed else ".f64" if dtype == "<f8" else ".f32"
    path = Path(directory) / (name + suffix)
    return path, (Writer(path, dtype=dtype, shape=shape, axes=axes) if packed else path.open("xb"))


def array_bytes(path, item, dtype, width):
    """Decode a hash-bound array descriptor, retaining legacy flat files."""
    require(dtype in DTYPES and integer(width, 1), "invalid expected vector type/width")
    if "storage" not in item:
        require(Path(path).stat().st_size == width * DTYPES[dtype],
                "incomplete numerical array")
        return Path(path).read_bytes()
    storage = item["storage"]
    require(isinstance(storage, dict) and set(storage) ==
            {"format", "dtype", "array_shape", "axes", "origin", "shape", "steps",
             "decoded_sha256"} and storage["format"] == "anvil-packed-v1" and
            storage["dtype"] == dtype, "invalid packed vector descriptor")
    reader = Reader(path, dtype=dtype, shape=storage["array_shape"], axes=storage["axes"])
    require(isinstance(storage["shape"], list) and
            all(integer(value, 1) for value in storage["shape"]) and
            math.prod(storage["shape"]) == width, "packed vector width differs")
    raw = reader.view(storage["origin"], storage["shape"], storage["steps"])
    require(hashlib.sha256(raw).hexdigest() == storage["decoded_sha256"],
            "packed vector decoded hash differs")
    return raw


def array_descriptor(root, path, *, origin=None, shape=None, steps=None):
    from benchmark import sha
    reader = Reader(path)
    require(reader.header["kind"] == "array", "array descriptor requires an array")
    source_shape = reader.header["shape"]
    origin = [0] * len(source_shape) if origin is None else origin
    shape = list(source_shape) if shape is None else shape
    steps = [1] * len(source_shape) if steps is None else steps
    raw = reader.view(origin, shape, steps)
    return {"path": str(Path(path).relative_to(root)), "sha256": sha(Path(path)),
            "storage": {"format": "anvil-packed-v1", "dtype": reader.header["dtype"],
                        "array_shape": source_shape, "axes": reader.header["axes"],
                        "origin": origin, "shape": shape, "steps": steps,
                        "decoded_sha256": hashlib.sha256(raw).hexdigest()}}


class ArraySource:
    """Reuse one verified index/hash when publishing many views of an array."""

    def __init__(self, root, path, *, dtype, shape, axes):
        from benchmark import sha
        self.root, self.path = Path(root), Path(path)
        self.reader = Reader(self.path, dtype=dtype, shape=shape, axes=axes)
        self.identity = self._identity()
        self.sha256 = sha(self.path)
        require(self._identity() == self.identity, "packed source changed during hashing")

    def _identity(self):
        info = self.path.stat()
        return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns

    def descriptor(self, *, origin=None, shape=None, steps=None):
        require(self._identity() == self.identity, "packed source changed during view collection")
        source_shape = self.reader.header["shape"]
        origin = [0] * len(source_shape) if origin is None else origin
        shape = list(source_shape) if shape is None else shape
        steps = [1] * len(source_shape) if steps is None else steps
        raw = self.reader.view(origin, shape, steps)
        require(self._identity() == self.identity, "packed source changed during view collection")
        return {"path": str(self.path.relative_to(self.root)), "sha256": self.sha256,
                "storage": {"format": "anvil-packed-v1", "dtype": self.reader.header["dtype"],
                            "array_shape": list(source_shape), "axes": self.reader.header["axes"],
                            "origin": list(origin), "shape": list(shape), "steps": list(steps),
                            "decoded_sha256": hashlib.sha256(raw).hexdigest()}}


def observation_vector(root, directory, kind, layer=None):
    """Describe a complete production observation, packed or legacy, without copies."""
    from benchmark import sha
    require(kind in ("layers", "logits") and
            (layer is None or kind == "layers" and integer(layer, 0, 23)),
            "invalid observation vector selection")
    directory = Path(directory)
    packed, flat = directory / (kind + ".aqp"), directory / (kind + ".f32")
    require(not (packed.exists() and flat.exists()), "ambiguous packed/legacy observation")
    if packed.exists():
        shape, axes = ([24, 896], ["layer", "component"]) if kind == "layers" else (
            [151936], ["vocabulary"])
        source = ArraySource(root, packed, dtype="<f4", shape=shape, axes=axes)
        return source.descriptor(**({"origin": [layer, 0], "shape": [1, 896]}
                                   if layer is not None else {}))
    require(layer is None, "legacy layer view requires explicit extraction")
    expected = (24 * 896 if kind == "layers" else 151936) * 4
    require(flat.stat().st_size == expected, "incomplete observed production " + kind)
    return {"path": str(flat.relative_to(root)), "sha256": sha(flat)}

def observation_chunks(directory, kind):
    """Decode a complete or explicitly partial checkpoint observation."""
    require(kind in ("layers", "logits"), "invalid observation fragment kind")
    directory = Path(directory)
    paths = [path for path in (directory / (kind + ".aqp"), directory / (kind + ".f32"))
             if path.exists()]
    require(len(paths) <= 1, "ambiguous packed/legacy observation fragment")
    if not paths:
        return
    path = paths[0]
    shape, axes = ([24, 896], ["layer", "component"]) if kind == "layers" else (
        [151936], ["vocabulary"])
    maximum = math.prod(shape) * 4
    if path.suffix == ".aqp":
        reader = Reader(path)
        require(reader.header["kind"] == "array" and reader.header["dtype"] == "<f4"
                and reader.total <= maximum and
                (reader.header["shape"], reader.header["axes"]) in (
                    (shape, axes), ([reader.total // 4], ["fragment"])),
                "invalid packed observation fragment shape/axes")
        yield from reader.chunks()
    else:
        require(path.stat().st_size <= maximum and path.stat().st_size % 4 == 0,
                "invalid legacy observation fragment size")
        with path.open("rb") as source:
            while raw := source.read(CHUNK_BYTES):
                require(len(raw) % 4 == 0, "partial observation fragment element")
                yield raw


def transaction_path(directory):
    paths = [path for path in (Path(directory) / "transactions.aqp",
                              Path(directory) / "transactions.u32.gz") if path.exists()]
    require(len(paths) == 1, "missing or ambiguous packed/legacy transaction witness")
    return paths[0]


def transaction_chunks(path):
    """Yield bounded, validated raw records from packed or legacy witnesses."""
    path = Path(path)
    with path.open("rb") as stream:
        magic = stream.read(8)
    if magic in (MAGIC, b"AQTXN002"):
        reader = Reader(path)
        require(reader.header["kind"] == "transactions", "array used as transaction stream")
        yield from reader.chunks()
    else:
        import gzip
        previous = 0
        with gzip.open(path, "rb") as stream:
            while raw := stream.read(CHUNK_BYTES // RECORD.size * RECORD.size):
                require(len(raw) % RECORD.size == 0, "partial 44-byte transaction record")
                for _, completed, _ in transaction_fields(raw, previous):
                    previous = completed
                yield raw


def transactions(path):
    """Read both existing gzip u32 witnesses and new packed transaction files."""
    for raw in transaction_chunks(path):
        yield from RECORD.iter_unpack(raw)
