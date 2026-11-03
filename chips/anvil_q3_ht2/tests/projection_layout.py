"""True-row projections through the shared Avalon transport and packed byte image."""

import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from receipts import ROOT, cleanup_build, compile_verilator, execute, relative
from reference import half, pack_rows, q16_to_half, single_to_q16, tile_sum


def compact_parameters():
    return {"NUM_LAYERS": 3, "HIDDEN_SIZE": 16, "INTERMEDIATE_SIZE": 24,
            "NUM_Q_HEADS": 8, "NUM_KV_HEADS": 1, "HEAD_DIM": 2,
            "GROUP_SIZE": 8, "VOCAB_SIZE": 4, "MAX_SEQ_LEN": 8, "BANKS": 1}


def fixture(run, kv_heads):
    hidden, intermediate, group, layers = 16 * kv_heads, 24, 8, 3
    kv_rows = 2 * kv_heads
    dimensions = [(hidden, hidden), (hidden, kv_rows), (hidden, kv_rows),
                  (hidden, hidden), (hidden, intermediate),
                  (hidden, intermediate), (intermediate, hidden)]
    image, matrices, offsets = {}, {}, [0, 0x60000000, 0x64000000]

    def store(address, data):
        for offset, byte in enumerate(data):
            image[address + offset] = byte

    def line(address):
        return int.from_bytes(bytes(image.get(address + i, 0xa5)
                                    for i in range(64)), "little")

    for layer in range(layers):
        for projection, (inputs, outputs) in enumerate(dimensions):
            capacity = ((outputs + 7) // 8) * 8
            stride = capacity // 2
            zeros = [[(layer * 5 + projection * 3 + g * 7 + row * 5) % 16
                      for row in range(capacity)] for g in range(inputs // group)]
            weights = [[(layer + projection * 7 + column * 3 + row * 11) % 16
                        for row in range(capacity)] for column in range(inputs)]
            scales = [[(0x1000, 0x1400, 0x1800, 0x1c00)[
                (g + row + projection + layer) % 4] + (row * 13 + g * 17) % 128
                for row in range(outputs)] for g in range(inputs // group)]
            payloads = (
                b"".join(pack_rows(rows).to_bytes(stride, "little") for rows in weights),
                b"".join(pack_rows(rows).to_bytes(stride, "little") for rows in zeros),
                b"".join(value.to_bytes(2, "little") for rows in scales for value in rows))
            bases = list(offsets)
            for kind, data in enumerate(payloads):
                allocation = (len(data) + 63) // 64 * 64
                # Padding is not a scale operand; infinity catches padded-row validation.
                store(offsets[kind], b"\x00\x7c" * (allocation // 2))
                store(offsets[kind], data)
                offsets[kind] += allocation
            matrices[layer, projection] = (bases, weights, zeros, scales)
        biases = [(0x1400, 0x9400, 0x1800, 0x9800)[(row + layer) % 4]
                  for row in range(hidden + 2 * kv_rows)]
        store(0x6c000000 + layer * (hidden + 2 * kv_rows) * 2,
              b"".join(value.to_bytes(2, "little") for value in biases))

    records, expected = [], {"cases": 0, "writes": 0, "activation_reads": 0,
                             "qweight_reads": 0, "metadata_reads": 0,
                             "bias_reads": 0}
    for layer in range(layers):
        for projection, (inputs, outputs) in enumerate(dimensions):
            mask = (1, 15, 10)[(layer + projection) % 3]
            bases, weights, zeros, scales = matrices[layer, projection]
            stride = ((outputs + 7) // 8) * 4
            activations = [[((-1 if (c + t) % 3 == 0 else 1) *
                             ((t + 1) * 8192 + c * 37 + layer * 19)) & 0xffffffff
                            for t in range(4)] for c in range(inputs)]
            beats = [(pack_rows(weights[c]), pack_rows(zeros[c // group]),
                      sum(v << (16 * r) for r, v in enumerate(scales[c // group])),
                      sum(q16_to_half(v) << (16 * t)
                          for t, v in enumerate(activations[c])), mask)
                     for c in range(inputs)]
            sums = tile_sum(beats, mask, (1 << outputs) - 1)
            values = []
            for row in range(outputs):
                bias = 0
                if projection < 3:
                    bias_row = row + (0 if projection == 0 else
                                      hidden if projection == 1 else hidden + kv_rows)
                    bias = int(half((0x1400, 0x9400, 0x1800, 0x9800)[
                        (bias_row + layer) % 4]) * 65536)
                for token in range(4):
                    bits, error = single_to_q16(
                        (sums >> (32 * (128 * token + row))) & 0xffffffff)
                    assert not error
                    signed = bits if bits < 0x80000000 else bits - 0x100000000
                    values.append(max(-0x80000000, min(0x7fffffff, signed + bias))
                                  & 0xffffffff if mask & (1 << token) else 0)
            requests = [[], [], []]
            for column in range(inputs):
                start = bases[0] + column * stride
                requests[0].extend(range(start & ~63,
                                         ((start + stride - 1) & ~63) + 64, 64))
            for g in range(inputs // group):
                for base, size in ((bases[1] + g * stride, stride),
                                   (bases[2] + g * outputs * 2, outputs * 2)):
                    requests[1].extend(range(base & ~63,
                                             ((base + size - 1) & ~63) + 64, 64))
            if projection < 3:
                bias_start = 0x6c000000 + layer * (hidden + 2 * kv_rows) * 2 + (
                    0 if projection == 0 else
                    hidden * 2 if projection == 1 else (hidden + kv_rows) * 2)
                requests[2] = [(bias_start + row * 2) & ~63 for row in range(outputs)]
            source = (1, 1, 1, 5, 8, 8, 11)[projection]
            target = (2, 3, 4, 6, 9, 10, 12)[projection]
            records.append(f"{layer} {projection} {mask:x} {inputs} {outputs} "
                           f"{source} {target} " + " ".join(str(len(v)) for v in requests))
            records.extend(f"{sum(v << (32*t) for t,v in enumerate(row)):032x}"
                           for row in activations)
            records.extend(f"{v:08x}" for v in values)
            for client in requests:
                records.extend(f"{address:x} {line(address):0128x}" for address in client)
            expected["cases"] += 1
            expected["writes"] += outputs * mask.bit_count()
            expected["activation_reads"] += inputs
            for category, client in zip(("qweight_reads", "metadata_reads", "bias_reads"),
                                        requests):
                expected[category] += len(client)
    vectors = run / "projection-layout-vectors.txt"
    vectors.write_text(f"{expected['cases']}\n" + "\n".join(records) + "\n")
    return vectors, expected


def run_projection_layout(run, kv_heads=1):
    vectors, expected = fixture(run, kv_heads)
    obj = run / "projection-layout-obj"
    sources = [relative(p) for directory in ("anvil_q3_ht_reference/rtl", "rtl")
               for p in sorted((ROOT / directory).glob("*.sv"))]
    binary = compile_verilator(run, "projection-layout-compile", [
        "verilator", "--cc", "--exe", "--build", "--timing", "--hierarchical",
        "--expand-limit", "1024", "-Wno-fatal", "--top-module", "projection_layout_tb",
        f"-DHT2_LAYOUT_KV_HEADS={kv_heads}", "--Mdir", relative(obj), "-j", "2",
        *sources, "tests/projection_layout_tb.sv", "tests/compiled.vlt",
        str(ROOT / "tests/timed_driver.cpp"), "-CFLAGS",
        "-DHT2_TIMED_PROJECTION_LAYOUT",
        "-o", "Vprojection_layout_tb"], obj, "Vprojection_layout_tb")
    try:
        result = execute(run, "projection-layout-simulate",
                         [relative(binary), f"+vectors={relative(vectors)}"],
                         ["verilator", "--version"])
    finally:
        cleanup_build(obj)
    records = [json.loads(v.removeprefix("RESULT ")) for v in
               (result / "stdout.txt").read_text().splitlines() if v.startswith("RESULT ")]
    if len(records) != 1 or any(records[0].get(k) != v for k, v in expected.items()):
        raise AssertionError(f"projection layout observations differ: {records} != {expected}")
    if not (records[0]["blocked_requests"] > 0 and records[0]["blocked_scratch"] > 0
            and records[0]["immediate_reads"] > 0 and records[0]["delayed_reads"] > 0):
        raise AssertionError("projection layout lacks actual transport/stall coverage")
    summary = {"kv_heads": kv_heads, "kv_rows": kv_heads * 2, "layers": 3,
               "observed": records[0],
               "vector_sha256": hashlib.sha256(vectors.read_bytes()).hexdigest(),
               "receipt": relative(result / "receipt.json")}
    (run / "projection-layout-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    import argparse
    from receipts import new_run
    from synthesis import run_synthesis
    from verify import Ledger, enter_tier

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-of")
    parser.add_argument("--synthesis-only", action="store_true")
    args = parser.parse_args()
    enter_tier()
    run = new_run("projection-layout", preparation=True, repair_of=args.repair_of)
    ledger = Ledger(run, "projection-layout-preparation")
    print(f"Projection layout evidence: {relative(run)}", flush=True)
    if args.synthesis_only:
        for mode in (1, 2):
            ledger.check(f"minimum-gqa-top-mode{mode}", run_synthesis,
                         "anvil_q3_ht2_top", mode, compact_parameters())
    else:
        for heads in (1, 2, 3):
            ledger.check(f"kvheads{heads}", run_projection_layout, heads)
    ledger.finish()
