"""Matched real HT2/HT3 execution; no theoretical speedup substitutes for data."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, clean_objects, execute, hashes, relative, remaining, timestamp
from run_compatibility import compiled, run_case


MEASUREMENT_RULES = {
    "clock": "simulated 100 MHz core / 50 MHz DDR, not physical timing",
    "start": "pre-edge token acceptance",
    "end": "registered done after last logit and committed writes",
    "included": "prefill/decode arithmetic, accepted DDR traffic and output draining",
    "excluded": "image generation, loader, descriptor validation and warm-up",
    "memory": "same queued response model, seed, waitrequest and 2-DDR-edge delays",
    "consumer": "three-edge initial/per-logit stalls and every fifth cycle not ready",
    "tokens": "token0 fresh, token1 decode, token2 fresh; no untimed warm-up tokens",
    "image": "identical represented image bytes, descriptor order and precision",
}


def parent_compiled():
    paths = [relative(p) for p in sorted(ROOT.glob("anvil_q1_ht2_reference/rtl/*.sv"))]
    paths.append("tests/inference_tb.sv")
    current = hashes()
    identity = dict(source_sha256={p: current[p] for p in paths},
                    define="PARENT_HT2",
                    geometry=dict(L=1, H=8, I=8, Q=1, K=1, D=8, G=8, V=3, S=4))
    cache = ROOT / "evidence/compiled"
    cache.mkdir(parents=True, exist_ok=True)
    directory = cache / f"parent-inference-{uuid.uuid4().hex[:12]}"
    directory.mkdir()
    identity["tool_version"] = execute(["verilator", "--version"], directory, "version",
                                     ["verilator", "--version"]).strip()
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
    for candidate in sorted(cache.glob(f"parent-inference-{key}-*")):
        binding, binary = candidate/"binding.json", candidate/"compile-obj/Vinference_tb"
        if not binding.is_file() or not binary.is_file():
            continue
        record = json.loads(binding.read_text())
        receipt = json.loads((candidate/"compile.receipt.json").read_text())
        if (record.get("identity") == identity and receipt.get("exit") == 0
                and not receipt.get("timed_out")
                and record.get("binary_sha256") == hashlib.sha256(binary.read_bytes()).hexdigest()):
            return binary, relative(binding)
    build = cache / f"parent-inference-{key}-{uuid.uuid4().hex[:12]}"
    build.mkdir()
    objects = build / "compile-obj"
    execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
             "-DPARENT_HT2", "--top-module", "inference_tb", "--Mdir", relative(objects),
             *paths], build, "compile", ["verilator", "--version"])
    binary = objects / "Vinference_tb"
    with (build/"binding.json").open("x") as out:
        json.dump(dict(identity=identity,
                       binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                       compile_receipt=relative(build/"compile.receipt.json")), out, indent=2)
    clean_objects(objects)
    return binary, relative(build/"binding.json")


def measurements(parent, product):
    a, b = parent["measurements"], product["measurements"]
    if len(a) != len(b) or not a:
        raise AssertionError("unmatched or empty completed-token measurements")
    records = []
    for old, new in zip(a, b):
        if old["token"] != new["token"] or min(old["cycles"], new["cycles"]) <= 0:
            raise AssertionError("unmatched performance token or invalid elapsed cycles")
        records.append(dict(token=old["token"], ht2=old, ht3=new,
                            cycle_reduction=1-new["cycles"]/old["cycles"],
                            tpm_ratio=new["simulated_tpm"]/old["simulated_tpm"],
                            ht2_ddr_bytes=64*(old["ddr_read_beats"]+old["ddr_write_beats"]),
                            ht3_ddr_bytes=64*(new["ddr_read_beats"]+new["ddr_write_beats"])))
    return records


def run(output, diagnostic=False):
    binaries = {}
    rows = []
    for name, builder in (("ht2", parent_compiled), ("ht3", compiled)):
        try:
            binaries[name] = builder()
        except (RuntimeError, AssertionError, ValueError, OSError) as exc:
            rows.append(dict(status="failed", generation=name, phase="compile",
                             error=f"{type(exc).__name__}: {exc}"))
    for seed in ((17,) if diagnostic else (17, 89, 2026)):
        for fmt in ((0,) if diagnostic else (0, 1, 2)):
            observations = {}
            for name, (binary, binding) in binaries.items():
                directory = output/f"{name}-format{fmt}-seed{seed}-{uuid.uuid4().hex[:8]}"
                directory.mkdir()
                try:
                    observations[name] = run_case(directory, binary, binding, fmt, seed)
                    observations[name]["image"] = json.loads(
                        (directory/"image-manifest.json").read_text())["sha256"]
                    observations[name]["vectors"] = hashlib.sha256(
                        (directory/"vectors.txt").read_bytes()).hexdigest()
                except (RuntimeError, AssertionError, ValueError, OSError) as exc:
                    rows.append(dict(status="failed", generation=name, format=fmt, seed=seed,
                                     error=f"{type(exc).__name__}: {exc}",
                                     directory=relative(directory),
                                     classification="parent regression aid" if name == "ht2"
                                     else "HT3 independent numerical/protocol failure"))
            if len(observations) == 2:
                old, new = observations["ht2"], observations["ht3"]
                if (old["image"], old["vectors"]) != (new["image"], new["vectors"]):
                    raise AssertionError("performance workloads are not byte-identical")
                rows.append(dict(status="passed", format=fmt, seed=seed,
                                 image_sha256=new["image"], vector_sha256=new["vectors"],
                                 observations=observations, tokens=measurements(old, new)))
    return dict(status="passed" if rows and all(r["status"] == "passed" for r in rows)
                else "failed", runs=rows, measurement_rules=MEASUREMENT_RULES,
                coverage_limits=[
                    "eligible fused-path producer/consumer transition-cycle instrumentation "
                    "and per-path >0.60 reduction assertion remain unimplemented; total "
                    "token latency is not that metric",
                    "authentic historical five-domain fixtures unavailable in RTL-only intake"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--diagnostic", action="store_true")
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_performance.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    try:
        result = run(output, args.diagnostic)
    except (RuntimeError, AssertionError, ValueError, OSError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    with (output/"result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"] != "passed"),
                   result=relative(output/"result.json"),
                   timed_out=any(json.loads(p.read_text()).get("timed_out", False)
                                 for p in output.rglob("*.receipt.json")))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
