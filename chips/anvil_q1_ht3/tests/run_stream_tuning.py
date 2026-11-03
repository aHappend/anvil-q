"""Compare portable C++ optimization on unchanged, public-pin RTL execution."""

import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))

from execution import ROOT, execute, hashes, relative, remaining, timestamp
import official_stream
from retention import artifacts_intact, digest, execution_logs_intact


OPTIONS = {
    "baseline": ["-O3", "-CFLAGS", "-O3"],
    "lto": ["-O3", "-CFLAGS", "-O3 -flto=2", "-LDFLAGS", "-flto=2"],
}


def run(output, args):
    comparison = None
    if args.compare:
        path = ROOT / args.compare
        comparison = json.loads(path.read_text())
        receipt = json.loads((path.parent / "receipt.json").read_text())
        if (comparison.get("status") != "passed" or receipt.get("exit") != 0
                or receipt.get("timed_out")
                or not artifacts_intact(comparison["artifact_sha256"])):
            raise AssertionError("comparison is not an intact settled sample")
    compiler = execute(["g++", "--version"], output, "compiler", ["g++", "--version"]).strip()
    with patch.object(official_stream, "COMPILE_OPTIONS", OPTIONS[args.flavor]):
        if args.geometry == "compact":
            checked = official_stream.self_test(output)
            stream = json.loads((ROOT / checked["resumed"]).read_text())
            build = json.loads((ROOT / stream["binary_binding"]).read_text())
            state = json.loads((ROOT / stream["checkpoints"][-1]).read_text())
            scope = "compact completed inference with independent FP64 logits"
        else:
            from run_benchmarks import checkpoint_image, prepare

            binary, binding = official_stream.compiled(output)
            works, inputs, failures = prepare(output)
            if failures:
                raise AssertionError(f"official input acquisition failed: {failures}")
            image = checkpoint_image(output, inputs)
            manifest = json.loads((ROOT / image["manifest"]).read_text())
            directory = output / f"sample-{uuid.uuid4().hex[:12]}"
            directory.mkdir()
            stream = official_stream.run_stream(
                directory, image, manifest["descriptors"],
                works[0]["token_ids"][:1], {0}, 151936, binary, binding,
                chunk_cycles=args.cycles, max_new_chunks=1)
            if stream["reused_chunks"] or stream["summary"]["cycles"] != args.cycles:
                raise AssertionError("timing sample was not fresh complete-cycle execution")
            state = json.loads((ROOT / stream["checkpoints"][-1]).read_text())
            build = json.loads(binding.read_text())
            checked = None
            scope = "full-dimensional setup timing only; not official inference acceptance"
    states = [json.loads((ROOT / p).read_text()) for p in stream["checkpoints"]]
    receipts = [json.loads((ROOT / row["receipt"]).read_text()) for row in states]
    if any(r.get("exit") != 0 or r.get("timed_out") or not execution_logs_intact(r)
           for r in receipts):
        raise AssertionError("timing sample includes incomplete execution")
    duration = sum(r["duration_s"] for r in receipts)
    if duration <= 0:
        raise AssertionError("nonpositive measured simulation duration")
    checkpoint = ROOT / (state["checkpoint"] + ".rtl.bin")
    observed = {str(p): record["sha256"] for p, record in stream["observations"].items()}
    result = dict(status="passed", scope=scope, geometry=args.geometry, flavor=args.flavor,
                  compiler_version=compiler, build_identity=build["identity"],
                  public_summary=stream["summary"], measurements=stream["measurements"],
                  observed_logit_sha256=observed, checked=checked,
                  plan_sha256=stream["identity"]["plan_sha256"],
                  image_sha256=stream["identity"]["image_sha256"],
                  rtl_state_sha256=digest(checkpoint),
                  simulation_s=duration, cycles_per_second=stream["summary"]["cycles"] / duration,
                  artifact_sha256={
                      path: sha for row in states for path, sha in row["artifact_sha256"].items()
                      if not path.endswith((".rtl.bin", ".host.bin"))},
                  checkpoints=stream["checkpoints"])
    if args.compare:
        path = ROOT / args.compare
        other = json.loads(path.read_text())
        receipt = json.loads((path.parent / "receipt.json").read_text())
        a, b = dict(other["build_identity"]), dict(result["build_identity"])
        a.pop("compile_options")
        b.pop("compile_options")
        if (other != comparison or other.get("status") != "passed" or receipt.get("exit") != 0
                or receipt.get("timed_out") or a != b
                or other["compiler_version"] != compiler
                or not artifacts_intact(other["artifact_sha256"])):
            raise AssertionError("comparison is not an intact source/tool-matched sample")
        for field in ("geometry", "public_summary", "measurements", "observed_logit_sha256",
                      "plan_sha256", "image_sha256", "rtl_state_sha256"):
            if other[field] != result[field]:
                raise AssertionError(f"compiler optimization changed {field}")
        result.update(compared=relative(path), compared_sha256=digest(path),
                      measured_speed_ratio=other["simulation_s"] / duration)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--geometry", choices=("compact", "full"), required=True)
    parser.add_argument("--flavor", choices=tuple(OPTIONS), required=True)
    parser.add_argument("--cycles", type=int, default=10000)
    parser.add_argument("--compare")
    args = parser.parse_args()
    if args.cycles < 1:
        parser.error("--cycles must be positive")
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_stream_tuning.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    try:
        result = run(output, args)
    except (OSError, RuntimeError, AssertionError, ValueError, KeyError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    with (output / "result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"] != "passed"),
                   timed_out=remaining() <= 0, result=relative(output / "result.json"))
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("artifact_sha256", "build_identity", "checkpoints", "checked")}),
          flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
