"""Independent byte-layout equations, including full-model 64-bit addresses."""

from dataclasses import asdict, replace
from itertools import product

from execution import ROOT, sha256, write_json
from parameters import A, defaults


def regions(g):
    result = {}
    cursor = 0
    for kind in range(16):
        for projection in range(7):
            inputs, outputs = g.dimensions(projection)
            if kind in (1, 2, 3, 4):
                layers = g.NUM_LAYERS
                rows = inputs if kind == 1 else inputs // g.GROUP_SIZE if kind in (2, 3) else 1
                cols = (outputs + 7) // 8 if kind in (1, 2) else outputs
                if kind == 4 and projection > 2:
                    continue
            elif projection != 0:
                continue
            else:
                layers = 1 if kind in (0, 7, 8, 11) else g.NUM_LAYERS
                rows = (g.VOCAB_SIZE if kind == 0 else 15 if kind == 8 else
                        g.MAX_SEQ_LEN if kind in (9, 10, 11, 12, 13, 14, 15) else 1)
                cols = (g.HIDDEN_SIZE if kind in (0, 5, 6, 7) else
                        max(g.HIDDEN_SIZE, g.INTERMEDIATE_SIZE) if kind == 8 else
                        g.NUM_KV_HEADS * g.HEAD_DIM if kind in (9, 10) else
                        g.HEAD_DIM if kind == 11 else
                        g.NUM_KV_HEADS * g.blocks *
                        ((g.capacity * (4 if g.CACHE_MODE == 2 else 8) + 31) // 32)
                        if kind in (12, 13) else g.NUM_KV_HEADS * g.blocks)
                if ((kind in (9, 10) and g.CACHE_MODE != 0) or
                        (kind >= 12 and g.CACHE_MODE == 0)):
                    continue
            cursor = (cursor + 63) // 64 * 64
            result[kind, projection] = cursor, layers, rows, cols
            cursor += 4 * layers * rows * cols
    return result, (cursor + 63) // 64 * 64


def map_vectors(path, g):
    shapes, extent = regions(g)

    def expected(write, kind, projection, layer, row, col):
        descriptor = shapes.get((kind, projection))
        if descriptor is None or (write and kind not in (8, 9, 10, 12, 13, 14, 15)):
            return 1, 0
        base, layers, rows, cols = descriptor
        if not (0 <= layer < layers and 0 <= row < rows and 0 <= col < cols):
            return 1, 0
        if kind == 8:
            limit = (g.NUM_KV_HEADS * g.HEAD_DIM if row in (3, 4) else
                     g.INTERMEDIATE_SIZE if row in (9, 10, 11, 13) else g.HIDDEN_SIZE)
            if row == 13:
                limit = max(g.HIDDEN_SIZE, g.INTERMEDIATE_SIZE)
            if col >= limit:
                return 1, 0
        return 0, base + 4 * ((layer * rows + row) * cols + col)

    coordinates = set()
    for (kind, proj), (_, layers, rows, cols) in shapes.items():
        for layer, row, col in product((0, layers - 1, layers), (0, rows - 1, rows), (0, cols - 1, cols)):
            for write in (0, 1):
                coordinates.add((write, kind, proj, layer, row, col))
        if kind == 8:
            for row in range(15):
                for col in (0, g.HIDDEN_SIZE - 1, g.HIDDEN_SIZE,
                            g.INTERMEDIATE_SIZE - 1, g.INTERMEDIATE_SIZE,
                            g.NUM_KV_HEADS * g.HEAD_DIM - 1, g.NUM_KV_HEADS * g.HEAD_DIM):
                    if col >= 0:
                        coordinates.add((1, 8, 0, 0, row, col))
    for kind in range(16):
        for proj in range(8):
            coordinates.add((0, kind, proj, 0, 0, 0))
    lines = [format(extent, "x")]
    errors, wide = 0, 0
    for coordinate in sorted(coordinates):
        error, address = expected(*coordinate)
        errors += error
        wide += address > (1 << 32) - 1
        lines.append(" ".join(map(str, (*coordinate, error))) + f" {address:x}")
    path.write_text("\n".join(lines) + "\n")
    return {"cases": len(coordinates), "errors": errors, "wide_addresses": wide,
            "required_bytes": extent}


def map_case(run, g, simulator="iverilog", label="A"):
    folder = run.path / f"memory-map-{label}-p{g.PROFILE}-m{g.CACHE_MODE}-{simulator}"
    folder.mkdir()
    path = folder / "vectors.txt"
    expected = map_vectors(path, g)
    if label == "official" and expected["required_bytes"] > (1 << 32) - 1 and not expected["wide_addresses"]:
        raise AssertionError("missing full-default >4GiB address comparisons")
    write_json(folder / "inputs.json", {**expected, "parameters": asdict(g), "sha256": sha256(path)})
    names = ("PROFILE", "NUM_LAYERS", "HIDDEN_SIZE", "INTERMEDIATE_SIZE", "NUM_KV_HEADS",
             "HEAD_DIM", "GROUP_SIZE", "VOCAB_SIZE", "MAX_SEQ_LEN", "CACHE_MODE", "CACHE_BLOCK")
    parameters = {name: getattr(g, name) for name in names}
    sources = ["rtl/anvil_q3_multiplier.sv", "rtl/anvil_q3_add128.sv",
               "fpga/anvil_q3_memory_map.sv", "tests/map_tb.sv"]
    if simulator == "iverilog":
        binary = folder / "map.vvp"
        run.tool(["iverilog", "-g2012", "-Wall", "-s", "map_tb", "-o", run.rel(binary),
                  *[f"-Pmap_tb.{key}={v}" for key, v in parameters.items()], *sources])
        command = ["vvp", run.rel(binary)]
    elif simulator == "verilator":
        obj = folder / "obj"
        run.tool(["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                  "--top-module", "map_tb", "--Mdir", run.rel(obj), "-o", "map",
                  *[f"-G{key}={v}" for key, v in parameters.items()], *sources])
        command = [run.rel(obj / "map")]
    else:
        raise ValueError(simulator)
    text, record = run.tool([*command, "+vectors=" + run.rel(path)])
    marker = (f"MAP_COMPLETE cases={expected['cases']} errors={expected['errors']} "
              f"wide={expected['wide_addresses']} bytes={expected['required_bytes']}")
    if marker not in text:
        raise AssertionError("incomplete independent physical address comparisons")
    result = {**expected, "parameters": asdict(g), "simulator": simulator,
              "stdout": record["stdout"], "scope": "portable layout arithmetic, not DDR/PCIe HIL"}
    write_json(folder / "result.json", result)
    return result


def memory_maps(run):
    results = []
    for simulator in ("iverilog", "verilator"):
        for mode in (0, 1, 2):
            results.append(map_case(run, replace(A, CACHE_MODE=mode), simulator))
            results.append(map_case(run, replace(defaults(3), CACHE_MODE=mode), simulator, "official"))
        for profile in (1, 2):
            for mode in ((0,) if profile == 1 else (0, 1)):
                results.append(map_case(run, replace(defaults(profile), CACHE_MODE=mode),
                                        simulator, "official"))
    write_json(run.path / "memory-map-results.json", results)
    return results
