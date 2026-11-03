"""Profile a settled public-pin stream continuation without changing its state."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from execution import ROOT, execute, hashes, relative, remaining, timestamp
from official_stream import DEPENDENCIES, summary, validated_chain
from retention import digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--checkpoint-binding", required=True)
    parser.add_argument("--cycles", type=int, default=20000)
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()
    if args.cycles < 1:
        parser.error("--cycles must be positive")
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_stream_profile.py", *sys.argv[1:]],
                   cwd=".", start=timestamp(), timeout=remaining(),
                   source_sha256=hashes(), tool_version=sys.version)
    try:
        binding = ROOT / args.checkpoint_binding
        row = json.loads(binding.read_text())
        identity = row["identity"]
        current = hashes()
        if any(identity["source_sha256"].get(p) != current[p]
               for p in [*[relative(p) for p in ROOT.glob("rtl/*.sv")], *DEPENDENCIES]):
            raise AssertionError("profile checkpoint does not match current stream sources")
        if not args.fresh:
            chain = validated_chain(binding, identity)
            if not chain or chain[-1]["summary"]["complete"]:
                raise AssertionError("profile requires an intact settled incomplete predecessor")
        binary = ROOT / identity["binary"]
        if digest(binary) != identity["binary_sha256"]:
            raise AssertionError("profile binary hash mismatch")
        predecessor_argv = row["argv"]
        plan = predecessor_argv[predecessor_argv.index("--plan") + 1]
        if (digest(ROOT / plan) != identity["plan_sha256"]
                or digest(ROOT / identity["image"]) != identity["image_sha256"]):
            raise AssertionError("profile plan/image hash mismatch")
        command = [identity["binary"], "--plan", plan, "--image", identity["image"],
                   "--output", relative(output), "--cycles", str(args.cycles)]
        if not args.fresh:
            command += ["--restore", row["checkpoint"]]
        text = execute(["perf", "record", "-F", "99", "--call-graph", "dwarf",
                        "-o", relative(output / "profile.data"), "--", *command],
                       output, "profile", ["perf", "--version"])
        observed = summary(text)
        start = 0 if args.fresh else row["summary"]["cycles"]
        if observed["cycles"] - start != args.cycles:
            raise AssertionError("profile did not execute its complete requested cycle window")
        report = execute(["perf", "report", "--stdio", "--no-children",
                          "-i", relative(output / "profile.data")],
                         output, "report", ["perf", "--version"])
        if "Samples:" not in report:
            raise AssertionError("profiler produced no CPU samples")
        result = dict(status="passed", scope="CPU profile, not inference acceptance",
                      predecessor=relative(binding), predecessor_sha256=digest(binding),
                      fresh=args.fresh, before=None if args.fresh else row["summary"],
                      after=observed)
    except (OSError, RuntimeError, AssertionError, ValueError, KeyError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    with (output / "result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"] != "passed"),
                   timed_out=remaining() <= 0, result=relative(output / "result.json"))
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
