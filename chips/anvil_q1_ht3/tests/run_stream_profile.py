"""Profile a settled public-pin stream continuation without changing its state."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from execution import ROOT, clean_objects, execute, hashes, relative, remaining, timestamp
from official_stream import COMPILE_OPTIONS, DEPENDENCIES, TOP, summary, validated_chain
from retention import digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--checkpoint-binding", required=True)
    parser.add_argument("--cycles", type=int, default=20000)
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--image-manifest")
    parser.add_argument("--profiler", choices=("perf", "gprof"), default="perf")
    parser.add_argument("--build-binding")
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
        image_path = identity["image"]
        if args.image_manifest:
            if not args.fresh:
                raise ValueError("replacement image location is restricted to fresh profiles")
            image = json.loads((ROOT / args.image_manifest).read_text())
            if (image.get("status") != "passed"
                    or image["image_sha256"] != identity["image_sha256"]
                    or image["image_bytes"] != identity["image_bytes"]):
                raise AssertionError("replacement image manifest does not match pinned bytes")
            image_path = image["image"]
        if (digest(ROOT / plan) != identity["plan_sha256"]
                or digest(ROOT / image_path) != identity["image_sha256"]):
            raise AssertionError("profile plan/image hash mismatch")
        command = [identity["binary"], "--plan", plan, "--image", image_path,
                   "--output", relative(output), "--cycles", str(args.cycles)]
        if not args.fresh:
            command += ["--restore", row["checkpoint"]]
        if args.profiler == "perf":
            text = execute(["perf", "record", "-F", "99", "--call-graph", "dwarf",
                            "-o", relative(output / "profile.data"), "--", *command],
                           output, "profile", ["perf", "--version"])
        else:
            if not args.fresh or not args.build_binding:
                raise ValueError("instrumented builds require --fresh and --build-binding")
            build_path = ROOT / args.build_binding
            if digest(build_path) != identity["build_binding_sha256"]:
                raise AssertionError("instrumented parameter/build identity mismatch")
            build = json.loads(build_path.read_text())
            objects = output / "compile-obj"
            objects.mkdir()
            shutil.copyfile(ROOT / "tests/official_stream.cpp", objects / "driver.cpp")
            execute(["verilator", "--cc", "--exe", "--build", "--savable",
                     "--prof-c", "--prof-cfuncs", "-Wno-fatal", "-j", "2",
                     *COMPILE_OPTIONS, "--top-module", TOP, "--Mdir", relative(objects),
                     *[f"-G{k}={v}" for k, v in build["identity"]["parameters"].items()],
                     *[relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))], "driver.cpp"],
                    output, "compile", ["verilator", "--version"])
            command[0] = relative(objects / f"V{TOP}")
            old_prefix = os.environ.get("GMON_OUT_PREFIX")
            os.environ["GMON_OUT_PREFIX"] = relative(output / "gmon")
            try:
                text = execute(command, output, "profile", ["verilator", "--version"])
            finally:
                if old_prefix is None:
                    os.environ.pop("GMON_OUT_PREFIX", None)
                else:
                    os.environ["GMON_OUT_PREFIX"] = old_prefix
                clean_objects(objects)
        observed = summary(text)
        start = 0 if args.fresh else row["summary"]["cycles"]
        if observed["cycles"] - start != args.cycles:
            raise AssertionError("profile did not execute its complete requested cycle window")
        if args.profiler == "perf":
            report_argv = ["perf", "report", "--stdio", "--no-children",
                           "-i", relative(output / "profile.data")]
            version_argv = ["perf", "--version"]
        else:
            profiles = sorted(output.glob("gmon.*"))
            if len(profiles) != 1:
                raise AssertionError("instrumented execution lacks exactly one CPU profile")
            report_argv = ["gprof", command[0], relative(profiles[0])]
            version_argv = ["gprof", "--version"]
        report = execute(report_argv, output, "report", version_argv)
        if ("Samples:" not in report if args.profiler == "perf" else
                "Each sample counts" not in report or "no time accumulated" in report):
            raise AssertionError("profiler produced no CPU samples")
        result = dict(status="passed", scope="CPU profile, not inference acceptance",
                      predecessor=relative(binding), predecessor_sha256=digest(binding),
                      profiler=args.profiler, fresh=args.fresh,
                      before=None if args.fresh else row["summary"],
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
