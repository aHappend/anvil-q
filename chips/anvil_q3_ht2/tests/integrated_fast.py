"""Public-pin clock-driven Verilator integration without SV coroutine overhead."""

import hashlib
import json
import os
import shutil

from integrated import generate
from receipts import ROOT, cleanup_build, execute, relative, compile_verilator
from serial_reference import Geometry, PackedImage, SerialModel


def generate_nonzero(run, mode, seed, layers=36, compact=False):
    model, vectors, lines, qreads = generate(
        run, layers=layers, nonzero=True, seed=seed, varied=True, compact=compact)
    geometry = (Geometry(layers=layers, hidden=16, kv_heads=1, head_dim=2)
                if compact else Geometry(layers=layers))
    oracle = SerialModel(PackedImage(model), geometry, mode)
    priming = oracle.evaluate(1, 0)
    chain = oracle.evaluate_tree(15, [3, 3, 3, 3], [4, 0, 1, 2], (priming,))
    branch = oracle.evaluate_tree(15, [3, 1, 3, 3], [4, 4, 0, 1], (priming, *chain))
    if any(item.argmax != 3 for item in (priming, *chain, *branch)):
        raise AssertionError("independent fixture does not produce the targeted greedy path")
    committed = (priming, *chain, branch[0], branch[2])
    expected_records = {}
    for token in committed:
        for (layer, value, head, group), record in token.records.items():
            groups = (geometry.head_dim + oracle.capacity - 1) // oracle.capacity
            index = (((layer * 2 + value) * geometry.maximum + token.position) *
                     geometry.kv_heads + head) * groups + group
            expected_records[0x100000000 + index * 64] = record
    address_vectors = vectors.read_text()
    traffic = json.loads((run / "traffic-layout.json").read_text())
    traffic_vectors = (str(len(traffic["qweight_projection"])) + "\n" +
                       " ".join(map(str, traffic["qweight_projection"])) + "\n" +
                       str(len(traffic["ffn_metadata_addresses"])) + "\n" +
                       "\n".join(f"{address:x}" for address in
                                 traffic["ffn_metadata_addresses"]) + "\n")
    vectors.write_text("\n".join(f"{value & 0xffffffff:x}" for value in priming.logits) +
                       f"\n{geometry.hidden} {geometry.kv_heads}\n" +
                       address_vectors + traffic_vectors +
                       f"{len(expected_records)}\n" +
                       "\n".join(f"{address:x} {record:x}"
                                 for address, record in sorted(expected_records.items())) + "\n")
    (run / "oracle-fixture.json").write_text(json.dumps({
        "mode": mode, "seed": seed, "geometry": vars(geometry),
        "priming_logits": priming.logits, "chain_argmax": [item.argmax for item in chain],
        "branch_argmax": [item.argmax for item in branch],
        "expected_committed_records": len(expected_records),
        "scope": "expected values only; not DUT comparison counts",
    }, indent=2) + "\n")
    return model, vectors, lines, qreads


def run_fast_integration(run, mode, seed=17, diagnostic=False, profile=False,
                         diagnostic_cycles=262144, layers=36, compact=False,
                         flat=False):
    model, vectors, lines, qreads = generate_nonzero(run, mode, seed, layers, compact)
    obj = run / "integrated-obj"
    obj.mkdir()
    driver = obj / "integrated_driver.cpp"
    shutil.copyfile(ROOT / "tests/integrated_driver.cpp", driver)
    sources = [relative(path) for directory in ("anvil_q3_ht_reference/rtl", "rtl")
               for path in sorted((ROOT / directory).glob("*.sv"))]
    executable = compile_verilator(run, "integrated-clock-driver-compile", [
        "verilator", "--cc", "--exe", "--build", "-Wno-fatal",
        "-O3", "--expand-limit", "1024",
        *(["--flatten"] if flat else [
            "--inline-mult", "1", "--hierarchical", "tests/native.vlt"]),
        "--top-module", "integrated_clock_tb", "--prefix", "Vintegrated",
        "--Mdir", relative(obj), "-j", "2",
        "--output-split", "20000", "--output-split-cfuncs", "2000",
        "-CFLAGS", "-O3", "-MAKEFLAGS", "OPT_FAST=-O3 OPT_SLOW=-O3",
        *(["-CFLAGS", "-pg", "-LDFLAGS", "-pg"] if profile else []),
        f"-DHT2_TEST_CACHE_MODE={mode}",
        f"-DHT2_TEST_LAYERS={layers}",
        *(["-DHT2_COMPACT_MODEL"] if compact else []),
        *sources, "tests/integrated_clock_tb.sv", driver.name], obj, "Vintegrated")
    try:
        result = execute(run, "integrated-clock-driver-simulate", [
            os.path.relpath(executable, run), f"+vectors={vectors.name}",
            f"+model={model.relative_to(run)}",
            f"+layers={layers}",
            *([f"+sample_cycles={diagnostic_cycles}"] if diagnostic else []),
            *(["+profile"] if profile else [])],
            ["verilator", "--version"], cwd=run)
    finally:
        cleanup_build(obj)
    raw = (result / "stdout.txt").read_text().splitlines()
    observations = [json.loads(line.split(" ", 1)[1]) for line in raw
                    if line.startswith("DIAGNOSTIC " if diagnostic else "RESULT ")]
    if len(observations) != 1:
        raise AssertionError("missing complete integration-driver observation")
    observation = observations[0]
    if diagnostic:
        if observation["evaluated_tokens"] != 1 or any(
                line.startswith("RESULT ") for line in raw):
            raise AssertionError("malformed diagnostic-only observation")
    elif observation["model_lines"] != lines or observation["qweight_reads"] != 3 * qreads or (
            observation["evaluated_tokens"], observation["committed_tokens"]) != (9, 7) or (
            observation.get("nonzero_projection_comparisons", 0) <= 0 or
            observation.get("compared_tree_shapes") != ["chain", "branch"]):
        raise AssertionError("incomplete integrated-model accounting")
    receipt = json.loads((result / "receipt.json").read_text())
    bindings = list(run.glob("integrated-clock-driver-compile-binding-*.json"))
    if len(bindings) != 1:
        raise AssertionError("missing exact integration build binding")
    binding = json.loads(bindings[0].read_text())
    compile_receipt = json.loads((ROOT / binding["compile_receipt"]).read_text())
    summary = {
        "mode": mode, "seed": seed, "layers": layers, "compact": compact,
        "compiler_partition": "flat" if flat else "tile-macro",
        "diagnostic_only": diagnostic, "observed": observation,
        "functional_result": "incomplete" if diagnostic else "nonzero-model-compared",
        "fixture": "independently decoded nonzero AWQ packed image and dense serial HT2 oracle",
        "nonzero_projection_comparisons":
            observation.get("nonzero_projection_comparisons", 0),
        "compared_tree_shapes": observation.get("compared_tree_shapes", []),
        "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
        "driver_sha256": hashlib.sha256(driver.read_bytes()).hexdigest(),
        "compile_duration_s": compile_receipt["duration_s"],
        "compile_receipt": binding["compile_receipt"],
        "simulation_duration_s": receipt["duration_s"],
        "cycles_per_second_including_host_load":
            observation["cycles"] / receipt["duration_s"],
        "receipt": relative(result / "receipt.json"),
    }
    (run / "integrated-clock-driver-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n")
    return summary
