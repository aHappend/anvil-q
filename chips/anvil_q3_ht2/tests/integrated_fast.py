"""Public-pin clock-driven Verilator integration without SV coroutine overhead."""

import hashlib
import json
import shutil

from integrated import generate
from receipts import ROOT, cleanup_build, execute, relative


def run_fast_integration(run, mode, diagnostic=False):
    model, vectors, lines, qreads = generate(run)
    obj = run / "integrated-obj"
    obj.mkdir()
    driver = obj / "integrated_driver.cpp"
    shutil.copyfile(ROOT / "tests/integrated_driver.cpp", driver)
    sources = [relative(path) for directory in ("anvil_q3_ht_reference/rtl", "rtl")
               for path in sorted((ROOT / directory).glob("*.sv"))]
    parameters = {
        "NUM_LAYERS": 36, "HIDDEN_SIZE": 64, "INTERMEDIATE_SIZE": 8,
        "NUM_Q_HEADS": 16, "NUM_KV_HEADS": 2, "HEAD_DIM": 4,
        "GROUP_SIZE": 8, "VOCAB_SIZE": 8, "MAX_SEQ_LEN": 8, "BANKS": 1,
        "CACHE_MODE": mode, "TILE_K": 16, "QUEUE_DEPTH": 3,
        "BURST_BEATS": 1, "KV_RESIDENT_GROUPS": 3,
    }
    execute(run, "integrated-clock-driver-compile", [
        "verilator", "--cc", "--exe", "--build", "-Wno-fatal",
        "--top-module", "anvil_q3_ht2_top", "--prefix", "Vintegrated",
        "--Mdir", relative(obj), "-j", "2", "-CFLAGS", "-O3",
        *[f"-G{name}={value}" for name, value in parameters.items()],
        *sources, driver.name], ["verilator", "--version"])
    try:
        result = execute(run, "integrated-clock-driver-simulate", [
            relative(obj / "Vintegrated"), f"+vectors={relative(vectors)}",
            f"+model={relative(model)}",
            *(["+sample_cycles=16384"] if diagnostic else [])],
            ["verilator", "--version"])
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
    elif observation["model_lines"] != lines or observation["qweight_reads"] != 4 * qreads or (
            observation["evaluated_tokens"], observation["committed_tokens"]) != (13, 7):
        raise AssertionError("incomplete integrated-model accounting")
    receipt = json.loads((result / "receipt.json").read_text())
    summary = {
        "mode": mode, "diagnostic_only": diagnostic, "observed": observation,
        "functional_result": "incomplete" if diagnostic else "constant-model-smoke",
        "fixture": "independent constant embedding, zero AWQ deltas, nonzero head",
        "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
        "driver_sha256": hashlib.sha256(driver.read_bytes()).hexdigest(),
        "simulation_duration_s": receipt["duration_s"],
        "cycles_per_second_including_host_load":
            observation["cycles"] / receipt["duration_s"],
        "receipt": relative(result / "receipt.json"),
    }
    (run / "integrated-clock-driver-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n")
    return summary
