"""Independent tensor arithmetic, activation ownership and measured performance."""

from dataclasses import replace
from execution import ROOT, sha256, write_json
from parameters import A, legal
from reference import Fixture


TENSOR_GEOMETRY = replace(A, HIDDEN_SIZE=128, INTERMEDIATE_SIZE=128, HEAD_DIM=16,
                          GROUP_SIZE=128, TILE_K=128, TILE_ROWS=8)


def activation_case(run, banks=8, simulator="iverilog", capacity=11008,
                    rtl=None, must_fail=False):
    if banks not in (1, 2, 4, 8) or capacity <= 0 or capacity % 8:
        raise ValueError("illegal activation-storage probe geometry")
    folder = run.path / f"activation-b{banks}-i{capacity}-{simulator}"
    folder.mkdir()
    expected = {}
    bindings = {}
    for vector, (inputs, outputs) in enumerate(((capacity, 16), (16, 2), (16, 16))):
        activation = [((index * 1664525 + (vector + 1) * 1013904223) & 0xffffffff)
                      for index in range(inputs)]
        activation[:4] = [0x80000000, 0x7fffffff, 0, 0xffffffff]
        signed = [value - (1 << 32) if value >> 31 else value for value in activation]
        values = []
        for row in range(outputs):
            values.append(sum(
                value * (((index * 5 + row * 3 + vector + 1) % 16) -
                         ((index // 8 + row + vector + 1) % 16)) *
                (32768, 65536, 131072)[(index // 8 + row + vector) % 3]
                for index, value in enumerate(signed)))
        expected[vector] = values
        for name, data, width, count in (
                (f"activation-{vector}.hex", activation, 32, max(capacity, 16)),
                (f"expected-{vector}.hex", values, 128, 16)):
            data = [*data, *([0] * (count - len(data)))]
            path = folder / name
            path.write_text("".join(
                f"{value & ((1 << width) - 1):0{width // 4}x}\n" for value in data))
            bindings[name] = sha256(path)
    write_json(folder / "inputs.json", {
        "banks": banks, "capacity": capacity, "bindings": bindings,
        "awq_nibble_offsets": [0, 16, 4, 20, 8, 24, 12, 28],
        "scales_q16": [32768, 65536, 131072],
        "first_result_hold_cycles_per_active_bank": 4096,
        "scope": "public tensor pins; exact integer oracle; no DUT hierarchy",
    })
    sources = (rtl if rtl is not None else
               [str(p.relative_to(ROOT)) for p in sorted((ROOT / "rtl").glob("*.sv"))])
    if simulator == "iverilog":
        binary = folder / "activation.vvp"
        run.tool(["iverilog", "-g2012", "-Wall", "-s", "tensor_activation_tb",
                  f"-Ptensor_activation_tb.BANKS={banks}",
                  f"-Ptensor_activation_tb.CAPACITY={capacity}",
                  "-o", run.rel(binary), *sources, "tests/tensor_activation_tb.sv"])
        command = ["vvp", run.rel(binary)]
    elif simulator == "verilator":
        obj = folder / "obj"
        run.tool(["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                  "--top-module", "tensor_activation_tb", "--Mdir", run.rel(obj),
                  "-o", "activation", f"-GBANKS={banks}", f"-GCAPACITY={capacity}",
                  *sources, "tests/tensor_activation_tb.sv"])
        command = [run.rel(obj / "activation")]
    else:
        raise ValueError(simulator)
    text, receipt = run.tool([*command, "+directory=" + run.rel(folder)], timeout=14400,
                             expected=(0, 1, -6) if must_fail else (0,))
    if must_fail:
        if receipt["exit_code"] == 0 or not any(assertion in text for assertion in (
                "ACTIVATION result id=", "ACTIVATION result stability",
                "ACTIVATION XZ result")):
            raise AssertionError("activation mutation survived or lacked a functional assertion")
        return {"functional_mutation_killed": True, "assertion": text,
                "stdout": receipt["stdout"]}
    if f"ACTIVATION_COMPLETE banks={banks} capacity={capacity}" not in text:
        raise AssertionError("activation-storage probe did not complete")
    observed, completed, recovered = {}, {}, []
    for line in (folder / "activation.tsv").read_text().splitlines():
        fields = line.split()
        if fields[0] == "RESULT" and len(fields) == 4:
            vector, row, value = int(fields[1]), int(fields[2]), int(fields[3], 16)
            if (vector not in expected or not 0 <= row < len(expected[vector]) or
                    (vector, row) in observed or
                    value != expected[vector][row] & ((1 << 128) - 1)):
                raise AssertionError("activation-storage numerical/ownership mismatch")
            observed[vector, row] = value
        elif fields[0] == "COMPLETE" and len(fields) == 7:
            vector, inputs, outputs, requests, req_stalls, res_stalls = map(int, fields[1:])
            if (vector not in expected or vector in completed or
                    inputs != (capacity if vector == 0 else 16) or
                    outputs != len(expected[vector]) or requests != 3 * inputs * outputs or
                    req_stalls <= 0 or res_stalls < 4096):
                raise AssertionError("activation-storage coverage incomplete")
            completed[vector] = list(map(int, fields[2:]))
        elif fields[0] == "RECOVERY" and len(fields) == 2:
            recovered.append(fields[1])
        else:
            raise AssertionError("invalid activation-storage trace entry")
    if (len(observed) != sum(map(len, expected.values())) or set(completed) != set(expected) or
            recovered != ["1", "2", "malformed-load", "3"]):
        raise AssertionError("incomplete activation-storage trace")
    result = {
        "banks": banks, "capacity": capacity, "simulator": simulator,
        "compared_bits": len(observed) * 128, "bit_mismatches": 0,
        "vectors": completed, "recoveries": recovered,
        "trace_sha256": sha256(folder / "activation.tsv"), "stdout": receipt["stdout"],
    }
    write_json(folder / "result.json", result)
    return result


def tensor_case(run, banks=8, simulator="verilator", seed=17):
    g = replace(TENSOR_GEOMETRY, BANKS=banks)
    if not legal(g):
        raise AssertionError("illegal tensor performance geometry")
    fixture = Fixture(g, seed)
    activation = fixture.embeddings[1]
    expected = [sum(a * b for a, b in zip(activation, w)) for w in fixture.weights[0, 0]]
    folder = run.path / f"tensor-b{banks}-s{seed}-{simulator}"
    folder.mkdir()
    memory = [fixture.memory[1, 0, 0, row, col] for row in range(128) for col in range(16)]
    memory += [fixture.memory[2, 0, 0, 0, col] for col in range(16)]
    memory += [fixture.memory[3, 0, 0, 0, col] for col in range(128)]
    for name, values, width in (("memory.hex", memory, 32), ("activations.hex", activation, 32),
                                 ("expected.hex", expected, 128)):
        (folder / name).write_text("".join(f"{v & ((1 << width) - 1):0{width // 4}x}\n"
                                          for v in values))
    write_json(folder / "inputs.json", {
        "fixture_sha256": fixture.digest(), "seed": seed, "banks": banks,
        "rows": 128, "inputs": 128,
        "bindings": {name: sha256(folder / name)
                     for name in ("memory.hex", "activations.hex", "expected.hex")},
        "compute_interval_definition":
            "union of per-bank full-tile operand-ready to final-result-handshake windows; "
            "starts on final scale response for each 8-row/128-input tile, ends on last "
            "row result; includes registered handoff, dot8 and reduction fill/drain and "
            "accumulator interlocks; excludes operand-fill-only gaps; no internal DUT signals"})
    sources = [str(p.relative_to(ROOT)) for p in sorted((ROOT / "rtl").glob("*.sv"))]
    if simulator == "iverilog":
        binary = folder / "tensor.vvp"
        run.tool(["iverilog", "-g2012", "-Wall", "-s", "tensor_tb", f"-Ptensor_tb.BANKS={banks}",
                  "-o", run.rel(binary), *sources, "tests/tensor_tb.sv"])
        command = ["vvp", run.rel(binary)]
    elif simulator == "verilator":
        obj = folder / "obj"
        run.tool(["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                  "--top-module", "tensor_tb", "--Mdir", run.rel(obj), "-o", "tensor",
                  f"-GBANKS={banks}", *sources, "tests/tensor_tb.sv"])
        command = [run.rel(obj / "tensor")]
    else:
        raise ValueError(simulator)
    text, receipt = run.tool([*command, "+directory=" + run.rel(folder)], timeout=14400)
    if f"TENSOR_COMPLETE banks={banks} rows=128 inputs=128" not in text:
        raise AssertionError("incomplete tensor computation")
    results, windows, summary = {}, [], None
    for line in (folder / "tensor.tsv").read_text().splitlines():
        fields = line.split()
        if fields[0] == "RESULT":
            index, value = int(fields[1]), int(fields[2], 16)
            if index in results or not 0 <= index < 128 or value != expected[index] & ((1 << 128) - 1):
                raise AssertionError("tensor numerical mismatch/duplicate")
            results[index] = value
        elif fields[0] == "WINDOW":
            bank, tile, start, end = map(int, fields[1:])
            if not 0 <= bank < banks or not 0 <= tile < 16 // banks or not start < end:
                raise AssertionError("invalid observed compute window")
            windows.append((bank, tile, start, end))
        elif fields[0] == "SUMMARY" and summary is None:
            summary = list(map(int, fields[1:]))
        else:
            raise AssertionError("unknown/duplicate tensor trace entry")
    if len(results) != 128 or len(windows) != 16 or len({w[:2] for w in windows}) != 16 or summary is None:
        raise AssertionError("incomplete tensor full-array/window evidence")
    union = 0
    right = -1
    for start, end in sorted((w[2], w[3]) for w in windows):
        union += max(0, end - max(start, right))
        right = max(right, end)
    if summary[:2] != [banks, 128] or summary[3:] != [union, banks] or summary[2] <= union:
        raise AssertionError("compute-window union/parallelism/total measurement mismatch")
    result = {"banks": banks, "seed": seed, "simulator": simulator, "rows": 128, "inputs": 128,
              "compared_bits": 128 * 128, "bit_mismatches": 0,
              "total_cycles_with_operand_fill": summary[2],
              "tensor_compute_interval_cycles": union, "max_concurrent_compute_banks": banks,
              "windows": windows, "trace_sha256": sha256(folder / "tensor.tsv"),
              "stdout": receipt["stdout"]}
    write_json(folder / "result.json", result)
    return result


def tensor_speedup(run):
    ledger = [tensor_case(run, banks) for banks in (1, 2, 4, 8)]
    single = ledger[0]["tensor_compute_interval_cycles"]
    for result in ledger:
        result["measured_tensor_compute_speedup"] = single / result["tensor_compute_interval_cycles"]
    write_json(run.path / "tensor-speedup.json", ledger)
    if ledger[-1]["tensor_compute_interval_cycles"] >= single:
        raise AssertionError("eight-bank actual tensor compute interval not faster than one bank")
    return ledger
