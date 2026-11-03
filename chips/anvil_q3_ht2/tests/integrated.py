"""Complete-model public host/Avalon smoke with an independent constant-model oracle."""

import argparse
import hashlib
import json
from math import isqrt
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipts import ROOT, execute, new_run, relative, cleanup_build
from reference import pack_rows, nearest_div


def generate(run, *, layers=36, nonzero=False):
    hidden, intermediate, kvdim, group, vocabulary, maximum = 64, 8, 8, 8, 8, 8
    image = {}

    def store(address, data):
        for offset, value in enumerate(data):
            line, byte = divmod(address + offset, 64)
            image.setdefault(line * 64, bytearray(64))[byte] = value

    def half_array(address, values):
        store(address, b"".join(value.to_bytes(2, "little") for value in values))

    offsets = [0, 0x60000000, 0x64000000]
    qreads = []
    for layer in range(layers):
        for projection, (inputs, outputs) in enumerate((
                (hidden, hidden), (hidden, kvdim), (hidden, kvdim), (hidden, hidden),
                (hidden, intermediate), (hidden, intermediate), (intermediate, hidden))):
            groups = inputs // group
            zeros = [[(row * 3 + g * 5 + layer + projection) & 15
                      for row in range(outputs)] for g in range(groups)]
            qweight = b"".join(pack_rows(
                [(value + 1) & 15 for value in zeros[column // group]]
                if nonzero else zeros[column // group]).to_bytes(
                outputs // 2, "little") for column in range(inputs))
            qzero = b"".join(pack_rows(row).to_bytes(outputs // 2, "little")
                             for row in zeros)
            scales = (b"\x00\x14" if nonzero else b"\x00\x3c") * (groups * outputs)
            for region, data in enumerate((qweight, qzero, scales)):
                store(offsets[region], data)
                if region == 0:
                    qreads.extend((offsets[0] + column * (outputs // 2)) & ~63
                                  for column in range(inputs))
                offsets[region] += (len(data) + 63) & ~63
        half_array(0x6c000000 + layer * (hidden + 2 * kvdim) * 2,
                   [0] * (hidden + 2 * kvdim))
    half_array(0x6d000000, [0x3c00] * ((2 * layers + 1) * hidden))
    # Zero projected Q/K makes rotation irrelevant, but the complete image is valid.
    store(0x6e000000, b"\x00\x3c\x00\x00" * (maximum * 4))
    half_array(0x80000000, [0x3c00] * (vocabulary * hidden))
    head = [0xbc00, 0xb800, 0, 0x3c00, 0x3800, 0x3400, 0xb400, 0]
    half_array(0xc0000000, [weight for weight in head for _ in range(hidden)])
    images = run / "checkpoint-images"
    images.mkdir()
    model = images / "model-lines.txt"
    model.write_text(str(len(image)) + "\n" + "\n".join(
        f"{address:x} {int.from_bytes(data,'little'):x}"
        for address, data in sorted(image.items())) + "\n")
    # The optional nonzero image is for differential legacy testing only; the
    # scalar expectations below are valid only for the zero-delta smoke.
    # RMS epsilon is the parent scalar contract's floor(1e-6 * 2**64).
    root = isqrt((1 << 64) + 18446744073710)
    reciprocal = (1 << 64) // root
    normalized = nearest_div(65536 * 65536 * reciprocal, 1 << 48)
    weights_q16 = [-65536, -32768, 0, 65536, 32768, 16384, -16384, 0]
    expected = [nearest_div(hidden * normalized * weight, 65536)
                for weight in weights_q16]
    vectors = run / "integration-vectors.txt"
    vectors.write_text(("" if nonzero else "\n".join(
        f"{value & 0xffffffff:x}" for value in expected) + "\n") +
                       str(len(qreads)) + "\n" +
                       "\n".join(f"{address:x}" for address in qreads) + "\n")
    return model, vectors, len(image), len(qreads)


def run_integrated(run, mode, diagnostic=False):
    model, vectors, model_lines, qreads = generate(run)
    sources = [relative(path) for folder in ("anvil_q3_ht_reference/rtl", "rtl")
               for path in sorted((ROOT / folder).glob("*.sv"))]
    obj = run / "integrated-obj"
    execute(run, "integrated-compile", [
        "verilator", "--binary", "--timing", "-Wno-fatal", "--top-module",
        "integrated_tb", f"-GCACHE_MODE={mode}", "--Mdir", relative(obj),
        "-j", "2", *sources, "tests/integrated_tb.sv"], ["verilator", "--version"])
    try:
        result = execute(run, "integrated-simulate", [
            relative(obj / "Vintegrated_tb"), f"+vectors={relative(vectors)}",
            f"+model={relative(model)}", *(["+diagnostic"] if diagnostic else [])],
            ["verilator", "--version"])
    finally:
        cleanup_build(obj)
    raw = (result / "stdout.txt").read_text()
    if diagnostic:
        observations = [json.loads(line.removeprefix("DIAGNOSTIC "))
                        for line in raw.splitlines() if line.startswith("DIAGNOSTIC ")]
        progress = [json.loads(line.removeprefix("PROGRESS "))
                    for line in raw.splitlines() if line.startswith("PROGRESS ")]
        if len(observations) != 1 or not progress or "RESULT " in raw or (
                observations[0]["evaluated_tokens"] < 1):
            raise AssertionError("bounded diagnostic did not reach its public observation")
        receipt = json.loads((result / "receipt.json").read_text())
        summary = {"diagnostic_only": True, "functional_result": "incomplete",
                   "mode": mode, "observed": observations[0],
                   "progress": progress,
                   "simulation_duration_s": receipt["duration_s"],
                   "cycles_per_second_including_host_load":
                       observations[0]["cycles"] / receipt["duration_s"],
                   "receipt": relative(result / "receipt.json")}
        (run / "diagnostic-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        return summary
    observed = [json.loads(line.removeprefix("RESULT ")) for line in
                raw.splitlines() if line.startswith("RESULT ")]
    if len(observed) != 1 or observed[0]["model_lines"] != model_lines or (
            observed[0]["qweight_reads"] != 3 * qreads or
            observed[0]["evaluated_tokens"] != 9 or observed[0]["committed_tokens"] != 3):
        raise AssertionError("missing complete public-top smoke observations")
    summary = {"mode": mode, "observed": observed[0],
               "fixture": "independent constant embedding, zero AWQ deltas, nonzero head",
               "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
               "receipt": relative(result / "receipt.json")}
    (run / "integrated-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=int, choices=(1, 2), default=1)
    parser.add_argument("--repair-of")
    parser.add_argument("--diagnostic", action="store_true")
    args = parser.parse_args()
    run = new_run("integrated", preparation=True, repair_of=args.repair_of)
    print(f"integrated evidence: {relative(run)}", flush=True)
    try:
        print(json.dumps(run_integrated(run, args.mode, args.diagnostic), sort_keys=True))
    except (RuntimeError, AssertionError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
