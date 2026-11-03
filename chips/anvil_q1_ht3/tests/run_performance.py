"""Matched real HT2/HT3 execution; no theoretical speedup substitutes for data."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import (ROOT, ExecutionFailure, clean_objects, execute, hashes,
                       relative, remaining, timestamp)
from retention import digest
from run_compatibility import check_case, compiled, fixture


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


def simulation_sources(name):
    pattern = "anvil_q1_ht2_reference/rtl/*.sv" if name == "ht2" else "rtl/*.sv"
    return [relative(p) for p in sorted(ROOT.glob(pattern))]+["tests/inference_tb.sv"]


def validated_simulation(path, binary, binding, vectors, fmt, seed, expected, name):
    """Admit only settled matching executions; independently rescore raw logits.

    Older aggregate failures can contain complete individual simulations. Their
    old pass labels are not used. Regenerated input bytes, simulator/binary,
    source hashes and raw diagnostics must match before the current oracle runs.
    """
    record = json.loads(path.read_text())
    current = hashes()
    build = json.loads((ROOT/binding).read_text())
    argv = record.get("argv", [])
    if (record.get("exit") != 0 or record.get("timed_out")
            or record.get("tool_version_exit") != 0
            or record.get("tool_version", "").strip() != build["identity"]["tool_version"]
            or len(argv) != 4 or argv[0] != relative(binary)
            or argv[3] != f"+seed={seed}"
            or digest(binary) != build["binary_sha256"]
            or any(record.get("source_sha256", {}).get(p) != current[p]
                   for p in simulation_sources(name))):
        return None
    directory = path.parent
    if (argv[1] != f"+vectors={relative(directory/'vectors.txt')}"
            or argv[2] != f"+observations={relative(directory/'observations.txt')}"
            or not (directory/"vectors.txt").is_file()
            or digest(directory/"vectors.txt") != digest(vectors)
            or not (directory/"observations.txt").is_file()):
        return None
    for key in ("stdout", "stderr"):
        artifact = ROOT/record[key]
        if (not artifact.is_file()
                or record.get("artifact_sha256", {}).get(record[key]) != digest(artifact)):
            return None
    checked = check_case(directory, (ROOT/record["stdout"]).read_text(),
                         binding, fmt, seed, expected)
    artifacts = [path, directory/"vectors.txt", directory/"observations.txt",
                 ROOT/record["stdout"], ROOT/record["stderr"], ROOT/binding,
                 ROOT/build["compile_receipt"], binary]
    return checked, {relative(p): digest(p) for p in artifacts}


def performance_case(output, name, binary, binding, fmt, seed):
    directory = output/f"{name}-format{fmt}-seed{seed}-{uuid.uuid4().hex[:12]}"
    directory.mkdir()
    vectors, expected = fixture(directory, fmt, seed)
    current = hashes()
    dependencies = [*simulation_sources(name), "tests/run_performance.py",
                    "tests/run_compatibility.py", "tests/reference.py", "tests/execution.py"]
    identity = dict(schema=1, generation=name, format=fmt, seed=seed,
                    source_sha256={p: current[p] for p in dependencies},
                    binary_sha256=digest(binary), binding_sha256=digest(ROOT/binding),
                    vector_sha256=digest(vectors), measurement_rules=MEASUREMENT_RULES)
    candidates = []
    for parent in (ROOT/"evidence/l1", ROOT/"evidence/preparation"):
        candidates.extend(parent.glob(f"*/performance-*/*{name}-format{fmt}-seed{seed}-*/case.json"))
        candidates.extend(parent.glob(f"*/shard-*/*{name}-format{fmt}-seed{seed}-*/case.json"))
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    rejected_receipts = set()
    for candidate in candidates:
        cached = json.loads(candidate.read_text())
        intact = bool(cached.get("artifact_sha256")) and all(
            (ROOT/p).is_file() and digest(ROOT/p) == sha
            for p, sha in cached.get("artifact_sha256", {}).items())
        if not intact and cached.get("simulation_receipt"):
            rejected_receipts.add(ROOT/cached["simulation_receipt"])
        if cached.get("identity") != identity or cached.get("status") != "passed" or not intact:
            continue
        candidates_receipts = [ROOT/cached["simulation_receipt"]]
        break
    else:
        candidates_receipts = []
        # Migrate complete pre-case-cache observations from failed aggregates.
        for parent in (ROOT/"evidence/l1", ROOT/"evidence/preparation"):
            candidates_receipts.extend(parent.glob(
                f"*/performance-*/*{name}-format{fmt}-seed{seed}-*/simulation.receipt.json"))
            candidates_receipts.extend(parent.glob(
                f"*/shard-*/*{name}-format{fmt}-seed{seed}-*/simulation.receipt.json"))
    checked = None
    for path in sorted(candidates_receipts, key=lambda p: p.stat().st_mtime, reverse=True):
        if path in rejected_receipts:
            continue
        checked = validated_simulation(path, binary, binding, vectors, fmt, seed, expected, name)
        if checked is not None:
            simulation_receipt = path
            break
    reused = checked is not None
    if checked is None:
        execute([relative(binary), f"+vectors={relative(vectors)}",
                 f"+observations={relative(directory/'observations.txt')}", f"+seed={seed}"],
                directory, "simulation", ["verilator", "--version"])
        simulation_receipt = directory/"simulation.receipt.json"
        checked = validated_simulation(simulation_receipt, binary, binding, vectors,
                                       fmt, seed, expected, name)
        if checked is None:
            raise AssertionError("fresh simulation failed execution/source/input binding")
    observation, artifacts = checked
    artifacts.update({relative(p): digest(p)
                      for p in (vectors, directory/"image-manifest.json")})
    record = dict(status="passed", identity=identity, observation=observation,
                  reused=reused, simulation_receipt=relative(simulation_receipt),
                  artifact_sha256=artifacts, validated_at=timestamp())
    with (directory/"case.json").open("x") as out:
        json.dump(record, out, indent=2)
    observation.update(image=json.loads((directory/"image-manifest.json").read_text())["sha256"],
                       vectors=digest(vectors), case=relative(directory/"case.json"), reused=reused)
    return observation


def failure_classification(exc, name):
    if isinstance(exc, ExecutionFailure):
        if exc.timed_out:
            launched = exc.record.get("launched", exc.record.get("exit") is not None
                                      or exc.record.get("timeout", 0) > 0)
            return ("execution_budget_timeout" if launched
                    else "execution_budget_unstarted")
        return "simulation_or_tool_failure"
    if isinstance(exc, AssertionError):
        return ("parent_numerical_protocol_failure" if name == "ht2"
                else "HT3_numerical_protocol_failure")
    return "verification_or_input_failure"


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
                try:
                    observations[name] = performance_case(output, name, binary, binding, fmt, seed)
                except (RuntimeError, AssertionError, ValueError, OSError) as exc:
                    rows.append(dict(status="failed", generation=name, format=fmt, seed=seed,
                                     error=f"{type(exc).__name__}: {exc}",
                                     classification=failure_classification(exc, name)))
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
