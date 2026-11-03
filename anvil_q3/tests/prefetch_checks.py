"""Independently generated AWQ words, descriptor ownership and observable overlap."""

from execution import write_json
from parameters import PREFETCH_DIMENSIONS


def prefetch_case(run, banks=8, tile_k=24, tile_rows=3, simulator="iverilog",
                  rtl=None, must_fail=False):
    folder = run.path / f"prefetch-b{banks}-k{tile_k}-r{tile_rows}-{simulator}"
    folder.mkdir()
    parameters = {**PREFETCH_DIMENSIONS, "BANKS": banks, "TILE_K": tile_k, "TILE_ROWS": tile_rows}
    # The harness freezes these leaf-only dimensions; no query-head/top geometry is implied.
    write_json(folder / "geometry.json", parameters)
    sources = (rtl if rtl is not None else
               ["rtl/anvil_q3_00_pkg.sv", "rtl/anvil_q3_weight_prefetcher.sv"]) + [
                   "tests/prefetch_tb.sv"]
    if simulator == "iverilog":
        binary = folder / "prefetch.vvp"
        run.tool(["iverilog", "-g2012", "-Wall", "-s", "prefetch_tb", "-o", run.rel(binary),
                  *[f"-Pprefetch_tb.{k}={v}" for k, v in parameters.items()], *sources])
        command = ["vvp", run.rel(binary)]
    else:
        obj = folder / "obj"
        run.tool(["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                  "--top-module", "prefetch_tb", "--Mdir", run.rel(obj), "-o", "prefetch",
                  *[f"-G{k}={v}" for k, v in parameters.items()], *sources])
        command = [run.rel(obj / "prefetch")]
    text, receipt = run.tool([*command, "+directory=" + run.rel(folder)],
                             expected=(0, 1, -6) if must_fail else (0,))
    if must_fail:
        if receipt["exit_code"] == 0 or not any(assertion in text for assertion in (
                "PREFETCH premature activation/swap", "PREFETCH active-buffer overwrite",
                "PREFETCH beat data/ownership", "PREFETCH coordinate/group/field")):
            raise AssertionError("prefetch mutation survived or failed without a functional assertion")
        return {"functional_mutation_killed": True, "assertion": text,
                "stdout": receipt["stdout"]}
    lines = [line.split() for line in (folder / "prefetch.tsv").read_text().splitlines()]
    required, acknowledged, activated = {}, {}, set()
    for bank in range(banks):
        for tile in range(4):
            rows = 1 if tile == 2 else tile_rows
            inputs = 1 if tile == 2 else tile_k - 3 if tile == 1 and tile_k > 8 else tile_k
            input_base = (0, 5, 7, 129)[tile]
            row_base = 1 if tile == 2 else bank * 8
            key = bank, tile
            required[key] = {
                word for row in range(row_base, row_base + rows)
                for col in range(input_base, input_base + inputs)
                for word in ((1, col, row // 8), (2, col // 8, row // 8), (3, col // 8, row))}
            acknowledged[key] = {}
    for line in lines:
        if line[0] == "RESPONSE":
            cycle, bank, tile, kind, row, col = map(int, line[1:])
            key, word = (bank, tile), (kind, row, col)
            if word not in required[key]:
                raise AssertionError("response outside immutable descriptor footprint")
            acknowledged[key][word] = min(cycle, acknowledged[key].get(word, cycle))
        elif line[0] == "ACTIVATE":
            cycle, bank, tile = map(int, line[1:])
            key = bank, tile
            if key in activated or set(acknowledged[key]) != required[key] or any(
                    when >= cycle for when in acknowledged[key].values()):
                raise AssertionError("prefetch activated before every needed word responded")
            activated.add(key)
    if activated != set(required):
        raise AssertionError("missing descriptor activations")
    requests = [list(map(int, line[1:])) for line in lines if line[0] == "REQUEST"]
    records = [list(map(int, line[1:])) for line in lines if line[0] == "BANK"]
    summary = [list(map(int, line[1:])) for line in lines if line[0] == "SUMMARY"]
    directed = [" ".join(line) for line in lines
                if line[0] not in ("REQUEST", "RESPONSE", "ACTIVATE", "BANK", "SUMMARY")]
    if (f"PREFETCH_COMPLETE banks={banks} descriptors={banks*4}" not in text or
            len(records) != banks or len(summary) != 1 or
            summary[0] != [len(requests), len(requests)] or
            directed != [*[f"FAULT {i}" for i in range(8)], "CANCEL_FILL 1",
                         "CANCEL_ACTIVE_STALLED 1", "RECOVERY 1"]):
        raise AssertionError("missing prefetch comparison/conservation records")
    for bank, offered, consumed, beats, overlap in records:
        if not (offered == consumed == 4 and beats > 0 and overlap > 0):
            raise AssertionError("prefetch bank coverage missing")
        if not any(r[1] == bank and r[2] > 0 and r[6] == 1 for r in requests):
            raise AssertionError("no bus-level next-tile/active-beat overlap")
    result = {"banks": banks, "tile_k": tile_k, "tile_rows": tile_rows,
              "simulator": simulator, "bank_records": records, "requests": len(requests),
              "three_successive_swaps_per_bank": True,
              "projection_group_boundary_and_partial_kv": True,
              "fault_cases": ["zero-row descriptor", "memory error", "nonzero AWQ padding",
                              "NaN scale", "negative scale", "FP16 transport high bits",
                              "infinite scale", "unsolicited response"],
              "flush_cases": ["idle", "accepted outstanding fill", "active output stalled"],
              "fresh_epoch_recovery": True,
              "overlap_trace": run.rel(folder / "prefetch.tsv"), "stdout": receipt["stdout"],
              "scope": "prefetch public pins; accepted memory draining belongs to scheduler"}
    write_json(folder / "result.json", result)
    return result
