#!/usr/bin/env python3
"""Bounded pipe services for direct packed producers; no inference or RTL access."""

import argparse
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import artifact_path, require
from packed_storage import CHUNK_BYTES, Reader, Writer


ROOT = Path(__file__).resolve().parents[1]
OBSERVATIONS = {
    "layers": ([24, 896], ["layer", "component"]),
    "logits": ([151936], ["vocabulary"]),
}


def write_stream(source, destination, kind):
    """Only sealed, complete vectors or explicitly shaped fragments are readable."""
    require(kind in (*OBSERVATIONS, "transactions"), "invalid packed stream kind")
    writer = None
    try:
        if kind == "transactions":
            writer = Writer(destination, transactions=True)
        width = 44 if kind == "transactions" else 4
        chunk = CHUNK_BYTES // width * width
        while raw := source.read(chunk):
            require(len(raw) % width == 0, "partial direct producer element/record")
            if writer is None:
                shape, axes = OBSERVATIONS[kind]
                writer = Writer(destination, dtype="<f4", shape=shape, axes=axes)
            writer.append(raw)
        if writer is not None:
            if kind != "transactions" and writer.total != writer.expected:
                writer.reshape([writer.total // 4], ["fragment"])
            writer.close()
    except BaseException:
        if writer is not None and not writer.stream.closed:
            writer.stream.close()
        raise


def reference_stream(source, output, path, kind, positions):
    """Serve exact full-width views, never a raw on-disk decompression cache."""
    require(kind in OBSERVATIONS and type(positions) is int and 0 < positions <= 32768,
            "invalid packed reference selection")
    shape, axes = (([positions, 24, 896], ["position", "layer", "component"])
                   if kind == "layers" else ([151936, positions], ["vocabulary", "position"]))
    reader = Reader(path, dtype="<f8", shape=shape, axes=axes)
    output.write(struct.pack("<Q", reader.total))
    output.flush()
    while request := source.read(16):
        require(len(request) == 16, "partial packed reference request")
        position, layer = struct.unpack("<QQ", request)
        require(position < positions and (layer < 24 if kind == "layers" else layer == 0),
                "packed reference request out of bounds")
        raw = (reader.view([position, layer, 0], [1, 1, 896]) if kind == "layers" else
               reader.view([0, position], [151936, 1]))
        require(output.write(raw) == len(raw), "short packed reference response")
        output.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("write", "reference"))
    parser.add_argument("kind", choices=(*OBSERVATIONS, "transactions"))
    parser.add_argument("path", type=Path)
    parser.add_argument("positions", nargs="?", type=int)
    args = parser.parse_args()
    path = artifact_path(ROOT, str(args.path))
    if args.operation == "write":
        require(args.positions is None, "unexpected producer position count")
        write_stream(sys.stdin.buffer, path, args.kind)
    else:
        reference_stream(sys.stdin.buffer, sys.stdout.buffer, path, args.kind, args.positions)


if __name__ == "__main__":
    main()
