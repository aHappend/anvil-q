"""Independent quantized records, all-record publication and cancellation fixtures."""

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipts import execute, new_run, relative, cleanup_build
from reference import kv_encode, kv_decode


def run_atomic(run, mode, seed, mutant=False):
    rng = random.Random(seed)
    layers, heads, dimension = 2, 1, 6
    path = run / "kv-records.txt"
    records = []
    for _ in range(4 * layers * 2 * heads):
        values = [rng.randrange(-(1 << 25), 1 << 25) for _ in range(dimension)]
        encoded = kv_encode(values, mode)
        decoded = kv_decode(encoded, dimension, mode)
        if len(decoded) != dimension:
            raise AssertionError("independent KV fixture self-check")
        records.append(encoded)
    path.write_text("\n".join(f"{record:x}" for record in records) + "\n")
    obj = run / "atomic-obj"
    sources = ["anvil_q3_ht_reference/rtl/anvil_q3_ht_kv_codec.sv",
               "rtl/anvil_q3_ht2_kv_commit_engine.sv", "tests/kv_atomic_tb.sv"]
    if mutant:
        source = Path(__file__).resolve().parents[1] / sources[1]
        original = source.read_text()
        target = "COPY_WRITE: if (request_fire) begin record<=0; state<=ADVANCE_COPY; end"
        if original.count(target) != 1:
            raise AssertionError("early-publication mutation target is not unique")
        mutated = run / "mutant-anvil_q3_ht2_kv_commit_engine.sv"
        mutated.write_text(original.replace(target,
            "COPY_WRITE: if (request_fire) begin record<=0; state<=FENCE_FIRST; end"))
        sources[1] = relative(mutated)
        (run / "mutation.json").write_text(json.dumps({
            "defect": "publish after first copied record instead of all accepted records",
            "original_source": relative(source),
            "original_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "mutant_source": relative(mutated),
            "mutant_sha256": hashlib.sha256(mutated.read_bytes()).hexdigest(),
            "replacement_before": target,
            "replacement_after": "COPY_WRITE: if (request_fire) begin record<=0; state<=FENCE_FIRST; end",
        }, indent=2) + "\n")
    execute(run, "atomic-compile", ["verilator", "--binary", "--timing", "-Wno-fatal",
            "--top-module", "kv_atomic_tb", f"-GCACHE_MODE={mode}", "--Mdir", relative(obj),
            "-j", "2", *sources], ["verilator", "--version"])
    try:
        result = execute(run, "atomic-simulate",
                         [relative(obj / "Vkv_atomic_tb"), f"+vectors={relative(path)}"],
                         ["verilator", "--version"], expect=-6 if mutant else 0)
    finally:
        cleanup_build(obj)
    outputs = [json.loads(line.removeprefix("RESULT "))
               for line in (result / "stdout.txt").read_text().splitlines()
               if line.startswith("RESULT ")]
    if mutant:
        actual_output = (result / "stdout.txt").read_text()
        if outputs or "KV committed record mismatch" not in actual_output:
            raise AssertionError("mutant did not reach the expected independent record mismatch")
        summary = {"mode": mode, "seed": seed, "mutant": True,
                   "discrimination": "independent committed-prefix record mismatch",
                   "record_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                   "receipt": relative(result / "receipt.json")}
        (run / "mutation-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        return summary
    if len(outputs) != 1 or outputs[0]["cancellations"] != 33 or (
            outputs[0]["publications"], outputs[0]["visible_count"]) != (3, 3):
        raise AssertionError("missing or malformed complete atomicity result")
    summary = {"mode": mode, "seed": seed, "observed": outputs[0],
               "record_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
               "receipt": relative(result / "receipt.json")}
    (run / "atomic-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=int, choices=(1, 2), default=1)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--repair-of")
    parser.add_argument("--mutant", action="store_true")
    args = parser.parse_args()
    run = new_run("kv-atomic", preparation=True, repair_of=args.repair_of)
    print(f"atomic evidence: {relative(run)}", flush=True)
    try:
        print(json.dumps(run_atomic(run, args.mode, args.seed, args.mutant), sort_keys=True))
    except (RuntimeError, AssertionError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
