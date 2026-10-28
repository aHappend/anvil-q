"""Actual official AWQ bytes through RTL dot8, never a full-model inference claim."""

import json
import random
import struct

from execution import ROOT, VERILATOR_UNROLL, sha256, write_json
from leaf_checks import packed
from public_assets import validate_assets
from reference import f16_q16


def slice_vectors(path, contents):
    ranged = {tuple(item["byte_range"]): ROOT / item["retained_path"]
              for item in contents if item["byte_range"] is not None}
    header_bytes = struct.unpack("<Q", ranged[0, 7].read_bytes())[0]
    header = json.loads(ranged[8, 7 + header_bytes].read_text())
    tensors = {}
    bindings = {}
    prefix = "model.layers.0.self_attn.k_proj."
    for suffix, shape, dtype, first, rows in (
            ("qweight", [2048, 32], "I32", 124, 8),
            ("qzeros", [16, 32], "I32", 0, 2),
            ("scales", [16, 256], "F16", 0, 2)):
        tensor = header[prefix + suffix]
        if tensor["shape"] != shape or tensor["dtype"] != dtype:
            raise AssertionError("official slice tensor shape/dtype mismatch")
        size = 2 if dtype == "F16" else 4
        if tensor["data_offsets"][1] - tensor["data_offsets"][0] != shape[0] * shape[1] * size:
            raise AssertionError("official slice tensor byte extent mismatch")
        begin = 8 + header_bytes + tensor["data_offsets"][0] + first * shape[1] * size
        source = ranged[begin, begin + rows * shape[1] * size - 1]
        tensors[suffix] = list(struct.unpack("<" + ("H" if size == 2 else "I") *
                                              (rows * shape[1]), source.read_bytes()))
        bindings[suffix] = {"shape": shape, "dtype": dtype, "first_row": first,
                            "rows": rows, "sha256": sha256(source)}
    shifts = [0, 16, 4, 20, 8, 24, 12, 28]
    rng = random.Random(17)
    transactions, dequantized = [], []
    for output in range(8):
        q = [(tensors["qweight"][input_lane * 32] >> shifts[output]) & 15
             for input_lane in range(8)]
        z = [(tensors["qzeros"][((124 + input_lane) // 128) * 32] >> shifts[output]) & 15
             for input_lane in range(8)]
        scales = [tensors["scales"][((124 + input_lane) // 128) * 256 + output]
                  for input_lane in range(8)]
        weights = [(a - b) * f16_q16(s, scale=True) for a, b, s in zip(q, z, scales)]
        dequantized.append(weights)
        for lane in range(8):
            activation = [65536] * 8
            transactions.append((q, z, scales, activation, 1 << lane, weights[lane] * 65536))
        for activation in ([-2147483648, 2147483647] * 4,
                           [rng.randrange(-2147483648, 2147483648) for _ in range(8)],
                           [1, -1, 65536, -65536, 0, 32768, -32768, 3]):
            transactions.append((q, z, scales, activation, 255,
                                 sum(a * w for a, w in zip(activation, weights))))
    pipeline = [None] * 8
    vectors = []
    accepted = 0
    retired = 0
    cycle = 0
    while accepted < len(transactions) or any(value is not None for value in pipeline) or cycle == 0:
        if cycle > 2000:
            raise AssertionError("official slice vector generation did not drain")
        reset = int(cycle != 0)
        ready = int(cycle % 73 >= 32)
        valid = int(accepted < len(transactions) and reset)
        q, z, scales, activation, mask, expected = transactions[
            min(accepted, len(transactions) - 1)]
        last = pipeline[-1]
        enable = last is None or ready
        before = [int(enable and reset), int(last is not None and reset), 0,
                  0 if last is None else last & ((1 << 72) - 1)]
        if reset and enable:
            retired += int(last is not None)
            pipeline = [expected if valid else None, *pipeline[:-1]]
            accepted += valid
        last = pipeline[-1]
        after = [int((last is None or ready) and reset), int(last is not None and reset), 0,
                 0 if last is None else last & ((1 << 72) - 1)]
        vectors.append([reset, 0, valid, ready, packed(q, 4), packed(z, 4),
                        packed(scales, 16), packed(activation, 32), mask, *before, *after, accepted])
        cycle += 1
    if accepted != retired or accepted != 88:
        raise AssertionError("official slice vector conservation")
    path.write_text("".join(" ".join(format(value, "x") for value in row) + "\n"
                           for row in vectors))
    return {"transactions": accepted, "cycles": cycle, "tensors": bindings,
            "dequantized_signed37_q16_weights": dequantized,
            "scope": "64 official weights, direct zero nibbles, group-128 boundary; "
                     "synthetic A16-boundary activations, not trained-model decoder inference"}


def official_weight_slice(run, validated=None):
    if validated is None:
        manifest = json.loads((ROOT / "tests/public_assets.json").read_text())
        records = [record for record in manifest["assets"] if record["category"] == "weight_slice"]
        validated = validate_assets(run, records)
    records = [record for record in validated if record["category"] == "weight_slice"]
    if len(records) != 1:
        raise AssertionError("exactly one official model slice required")
    asset = records[0]
    folder = run.path / "official-awq-slice"
    folder.mkdir()
    vectors = folder / "vectors.txt"
    inputs = slice_vectors(vectors, asset["contents"])
    write_json(folder / "frozen-inputs.json",
               {**inputs, "vector_sha256": sha256(vectors), "asset": asset})
    results = []
    for simulator in ("iverilog", "verilator"):
        sources = ["rtl/anvil_q3_00_pkg.sv", "rtl/anvil_q3_awq_dot8.sv", "tests/dot8_tb.sv"]
        if simulator == "iverilog":
            binary = folder / "official.vvp"
            run.tool(["iverilog", "-g2012", "-Wall", "-s", "dot8_tb",
                      "-o", run.rel(binary), *sources])
            command = ["vvp", run.rel(binary)]
        else:
            obj = folder / "obj"
            run.tool(["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                      *VERILATOR_UNROLL, "--top-module", "dot8_tb", "--Mdir", run.rel(obj),
                      "-o", "official", *sources])
            command = [run.rel(obj / "official")]
        text, receipt = run.tool([*command, "+vectors=" + run.rel(vectors)])
        if f"DOT8_COMPLETE cycles={inputs['cycles']} transactions=88" not in text:
            raise AssertionError("official AWQ RTL comparisons incomplete")
        results.append({"simulator": simulator, "transactions": 88, "compared_result_bits": 88 * 72,
                        "bit_mismatches": 0, "stdout": receipt["stdout"]})
    result = {"identifier": asset["identifier"], "revision": asset["revision"],
              "license_identifier": asset["license_identifier"],
              "license_scope": asset["license_scope"], "comparisons": results, "inputs": inputs}
    write_json(folder / "result.json", result)
    return result
