"""Source-bound CPU diagnostics of the real public-pin stream, not acceptance."""

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from execution import ROOT, clean_objects, execute, hashes, relative, remaining, timestamp
from official_stream import COMPILE_OPTIONS, DEPENDENCIES, TOP, plan_bytes, summary, validated_chain
from retention import digest, execution_logs_intact


def instrumented_build(output, parameters, reuse, current, sources):
    directory = ROOT / reuse if reuse else output
    objects = directory / "compile-obj"
    argv = ["verilator", "--cc", "--exe", "--build", "--savable",
            "--prof-c", "--prof-cfuncs", "-Wno-fatal", "-j", "2",
            *COMPILE_OPTIONS, "--top-module", TOP, "--Mdir", relative(objects),
            *[f"-G{k}={v}" for k, v in parameters.items()],
            *[relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))], "driver.cpp"]
    if reuse:
        record = json.loads((directory / "compile.receipt.json").read_text())
        if (record.get("exit") != 0 or record.get("timed_out")
                or record.get("argv") != argv or not execution_logs_intact(record)
                or any(record.get("source_sha256", {}).get(p) != current[p] for p in sources)
                or digest(objects / "driver.cpp") != current["tests/official_stream.cpp"]):
            raise AssertionError("instrumented compilation is not an intact settled predecessor")
    else:
        objects.mkdir()
        shutil.copyfile(ROOT / "tests/official_stream.cpp", objects / "driver.cpp")
        execute(argv, output, "compile", ["verilator", "--version"])
    binary = objects / f"V{TOP}"
    with (output / "instrumented-build.json").open("x") as out:
        json.dump(dict(compile_receipt=relative(directory / "compile.receipt.json"),
                       binary=relative(binary), binary_sha256=digest(binary),
                       parameters=parameters,
                       source_sha256={p: current[p] for p in sources}), out, indent=2)
    return binary


def fresh_official_plan(output):
    from run_benchmarks import checkpoint_image, prepare

    works, inputs, failures = prepare(output)
    if failures:
        raise AssertionError(f"official input refresh failed: {failures}")
    image = checkpoint_image(output, inputs)
    manifest = json.loads((ROOT / image["manifest"]).read_text())
    plan = output / "stream-plan.txt"
    plan.write_bytes(plan_bytes(manifest["descriptors"], image["image_bytes"],
                                works[0]["token_ids"][:1], {0}, 151936))
    return plan, image


def run(output, args):
    current = hashes()
    sources = [*[relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))], *DEPENDENCIES]
    predecessor = None
    parameters = {}
    if args.checkpoint_binding:
        path = ROOT / args.checkpoint_binding
        predecessor = json.loads(path.read_text())
        identity = predecessor["identity"]
        if any(identity["source_sha256"].get(p) != current[p] for p in sources):
            raise AssertionError("profile checkpoint does not match current stream sources")
        if not args.fresh:
            chain = validated_chain(path, identity)
            if not chain or chain[-1]["summary"]["complete"]:
                raise AssertionError("profile requires an intact settled incomplete predecessor")
        build_path = ROOT / args.build_binding
        if digest(build_path) != identity["build_binding_sha256"]:
            raise AssertionError("profile parameter/build identity mismatch")
        parameters = json.loads(build_path.read_text())["identity"]["parameters"]
    if args.profiler == "gprof":
        binary = instrumented_build(output, parameters, args.reuse_instrumented_build,
                                    current, sources)
    else:
        binary = ROOT / identity["binary"]
        if digest(binary) != identity["binary_sha256"]:
            raise AssertionError("profile binary hash mismatch")

    # Compilation can outlive reclaimed public payloads; acquire last, not first.
    if args.full_model or args.refresh_image:
        plan, image = fresh_official_plan(output)
        if predecessor:
            if (image["image_bytes"] != identity["image_bytes"]
                    or image["image_sha256"] != identity["image_sha256"]):
                raise AssertionError("refreshed image differs from the original pinned bytes")
            old_argv = predecessor["argv"]
            plan = ROOT / old_argv[old_argv.index("--plan") + 1]
    else:
        old_argv = predecessor["argv"]
        plan = ROOT / old_argv[old_argv.index("--plan") + 1]
        image = dict(image=identity["image"], image_sha256=identity["image_sha256"])
    if (digest(ROOT / image["image"]) != image["image_sha256"]
            or (predecessor and digest(plan) != identity["plan_sha256"])):
        raise AssertionError("profile plan/image hash mismatch")
    command = [relative(binary), "--plan", relative(plan), "--image", image["image"],
               "--output", relative(output), "--cycles", str(args.cycles)]
    if predecessor and not args.fresh:
        command += ["--restore", predecessor["checkpoint"]]
    if args.profiler == "perf":
        text = execute(["perf", "record", "-F", "99", "--call-graph", "dwarf",
                        "-o", relative(output / "profile.data"), "--", *command],
                       output, "profile", ["perf", "--version"])
        report_argv = ["perf", "report", "--stdio", "--no-children",
                       "-i", relative(output / "profile.data")]
        version_argv = ["perf", "--version"]
    else:
        old_prefix = os.environ.get("GMON_OUT_PREFIX")
        os.environ["GMON_OUT_PREFIX"] = relative(output / "gmon")
        try:
            text = execute(command, output, "profile", ["verilator", "--version"])
        finally:
            if old_prefix is None:
                os.environ.pop("GMON_OUT_PREFIX", None)
            else:
                os.environ["GMON_OUT_PREFIX"] = old_prefix
            clean_objects(binary.parent)
        profiles = sorted(output.glob("gmon.*"))
        if len(profiles) != 1:
            raise AssertionError("instrumented execution lacks exactly one CPU profile")
        report_argv = ["gprof", relative(binary), relative(profiles[0])]
        version_argv = ["gprof", "--version"]
    observed = summary(text)
    start = predecessor["summary"]["cycles"] if predecessor and not args.fresh else 0
    if observed["cycles"] - start != args.cycles:
        raise AssertionError("profile did not execute its complete requested cycle window")
    report = execute(report_argv, output, "report", version_argv)
    if ("Samples:" not in report if args.profiler == "perf" else
            "Each sample counts" not in report or "no time accumulated" in report):
        raise AssertionError("profiler produced no CPU samples")
    execution = json.loads((output / "profile.receipt.json").read_text())
    return dict(status="passed", scope="CPU diagnostic, not inference acceptance",
                profiler=args.profiler, fresh=not predecessor or args.fresh,
                predecessor=args.checkpoint_binding, before=(
                    predecessor["summary"] if predecessor and not args.fresh else None),
                after=observed, image=image["image"], image_sha256=image["image_sha256"],
                plan_sha256=digest(plan), duration_s=execution["duration_s"],
                cycles_per_second=args.cycles / execution["duration_s"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--checkpoint-binding")
    mode.add_argument("--full-model", action="store_true")
    parser.add_argument("--build-binding")
    parser.add_argument("--cycles", type=int, default=20000)
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--profiler", choices=("perf", "gprof"), default="gprof")
    parser.add_argument("--reuse-instrumented-build")
    parser.add_argument("--refresh-image", action="store_true")
    args = parser.parse_args()
    if args.cycles < 1:
        parser.error("--cycles must be positive")
    if args.checkpoint_binding and not args.build_binding:
        parser.error("--checkpoint-binding requires --build-binding")
    if args.profiler == "perf" and (args.full_model or args.reuse_instrumented_build):
        parser.error("perf requires an existing checkpoint and its uninstrumented binary")
    if args.profiler == "gprof" and args.checkpoint_binding and not args.fresh:
        parser.error("instrumented builds require fresh RTL execution")
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_stream_profile.py", *sys.argv[1:]],
                   cwd=".", start=timestamp(), timeout=remaining(),
                   source_sha256=hashes(), tool_version=sys.version)
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
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
