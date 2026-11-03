"""Portable source-bound L1 behavior/reference/synthesis and reproduction checks."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import Experiment, timestamp
from build_cache import create_cache
from scheduling import create_budget, run_graph


TOOLS = ("python3", "iverilog", "vvp", "yosys", "g++")
SOURCE_SELECTORS = (("rtl", "*.sv"), ("anvil_q2_reference/rtl", "*.sv"),
                    ("design", "*.md"), ("design", "*.sdc"), ("tests", "*"))
INPUT_SELECTORS = SOURCE_SELECTORS + (("data/model", "*"),)


def product_sources(root):
    files = []
    for directory, pattern in SOURCE_SELECTORS:
        paths = sorted(path for path in (root / directory).glob(pattern) if path.is_file())
        if not paths:
            raise RuntimeError("empty declared source selector: " + directory + "/" + pattern)
        files.extend(str(path.relative_to(root)) for path in paths)
    return sorted(set(files))


def input_bindings(root):
    bindings = {}
    for directory, pattern in INPUT_SELECTORS:
        paths = sorted(path for path in (root / directory).glob(pattern) if path.is_file())
        if not paths:
            raise RuntimeError("empty declared input selector: " + directory + "/" + pattern)
        for path in paths:
            digest = hashlib.sha256()
            size = 0
            with path.open("rb") as stream:
                while chunk := stream.read(4 * 1024 * 1024):
                    digest.update(chunk)
                    size += len(chunk)
            bindings[str(path.relative_to(root))] = {
                "bytes": size, "sha256": digest.hexdigest()}
    return bindings


def record_input_bindings(experiment, phase):
    bindings = input_bindings(experiment.root)
    name = "declared-inputs-" + phase + ".json"
    with (experiment.directory / name).open("x") as stream:
        json.dump(bindings, stream, indent=2, sort_keys=True)
        stream.write("\n")
    experiment.receipt["declared_inputs_" + phase] = bindings
    experiment.receipt["declared_inputs_" + phase + "_path"] = str(
        experiment.output / name)
    return bindings


def verify_input_bindings(experiment):
    before = experiment.receipt["declared_inputs_before"]
    after = record_input_bindings(experiment, "after")
    changes = {
        "added": sorted(after.keys() - before.keys()),
        "removed": sorted(before.keys() - after.keys()),
        "changed": sorted(name for name in before.keys() & after.keys()
                          if before[name] != after[name]),
    }
    experiment.receipt["declared_input_changes"] = changes
    if any(changes.values()):
        raise RuntimeError("declared verification inputs changed during execution: "
                           + json.dumps(changes, sort_keys=True))


def observe_input_metadata(experiment, boundary):
    with experiment.lock:
        _observe_input_metadata(experiment, boundary)


def _observe_input_metadata(experiment, boundary):
    """Retain interval observations, not a continuous write-event trace."""
    started = timestamp()
    files = {}
    for directory, pattern in INPUT_SELECTORS:
        for path in sorted((experiment.root / directory).glob(pattern)):
            if path.is_file():
                stat = path.stat()
                files[str(path.relative_to(experiment.root))] = {
                    "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns,
                    "ctime_ns": stat.st_ctime_ns, "device": stat.st_dev,
                    "inode": stat.st_ino, "mode": stat.st_mode,
                }
    previous = getattr(experiment, "_input_metadata", None)
    record = {"boundary": boundary, "start": started, "end": timestamp(),
              "files": files}
    if previous is not None:
        record["previous_boundary"] = previous["boundary"]
        before = previous["files"]
        record["changes"] = {
            "added": sorted(files.keys() - before.keys()),
            "removed": sorted(before.keys() - files.keys()),
            "changed": sorted(name for name in before.keys() & files.keys()
                              if before[name] != files[name]),
        }
    path = experiment.directory / "declared-input-metadata.jsonl"
    mode = "x" if previous is None else "a"
    with path.open(mode) as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
    experiment._input_metadata = record
    experiment.receipt["declared_input_metadata_path"] = str(
        experiment.output / path.name)


def run_observed_child(experiment, argv, name, **options):
    try:
        observe_input_metadata(experiment, name + ":before")
    except OSError as error:
        with experiment.lock:
            experiment.receipt["input_metadata_failure"] = str(error)
            experiment.receipt.setdefault("input_metadata_failures", []).append({
                "boundary": name + ":before", "error": str(error),
                "child_failure": None,
            })
        raise
    child_failure = None
    try:
        return experiment.run(argv, name, **options)
    except (OSError, RuntimeError) as error:
        child_failure = str(error)
        raise
    finally:
        try:
            observe_input_metadata(experiment, name + ":after")
        except OSError as error:
            with experiment.lock:
                experiment.receipt["input_metadata_failure"] = str(error)
                experiment.receipt.setdefault("input_metadata_failures", []).append({
                    "boundary": name + ":after", "error": str(error),
                    "child_failure": child_failure,
                })
            if child_failure is None:
                raise


def require_tools(tools):
    missing = [tool for tool in tools if shutil.which(tool) is None]
    if missing:
        raise RuntimeError("unmet tool prerequisites: " + ", ".join(missing))


def portable(experiment, files):
    root = experiment.root
    clean = experiment.output / "clean-project"
    destination = root / clean
    destination.mkdir()
    copied = {}
    for name in files:
        data = (experiment.directory / "sources" / name).read_bytes()
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        copied[name] = hashlib.sha256(data).hexdigest()
    (experiment.directory / "portable-source-manifest.json").write_text(
        json.dumps(copied, indent=2) + "\n")
    checks = (
        ("array", ["python3", "tests/array_check.py", "--output", "evidence/array"]),
        ("ddr-roundtrip", ["python3", "tests/system_check.py", "--output", "evidence/system",
                           "--mode", "0", "--cache", "0",
                           "--scenario", "roundtrip", "--simulator", "iverilog"]),
        ("zero-latch-synthesis", ["python3", "tests/synthesis_check.py", "--output",
                                  "evidence/synthesis", "--top", "anvil_q2_ht_tensor_array",
                                  "--expand-packages"]),
    )
    ledger = [{"check": name, "argv": argv, "outcome": "not-executed"}
              for name, argv in checks]
    experiment.receipt["portable"] = {
        "copied_source_files": len(copied), "source_sha256": copied,
        "working_directory": str(clean), "checks": ledger,
        "scope": "fresh-source 128-lane numerical, synthetic DDR roundtrip and zero-latch smoke only"}
    require_tools(TOOLS)
    for row in ledger:
        name, argv = row["check"], row["argv"]
        row["outcome"] = "running"
        try:
            run_observed_child(experiment, argv, name, cwd=clean, timeout=14400)
            receipt_name = {"array": "array", "ddr-roundtrip": "system",
                            "zero-latch-synthesis": "synthesis"}[name]
            receipt_path = destination / "evidence" / receipt_name / "receipt.json"
            receipt = json.loads(receipt_path.read_text())
            if receipt["exit"] != 0:
                raise RuntimeError("clean child receipt did not succeed")
            row.update(receipt=str(receipt_path.relative_to(root)), outcome="passed")
        except (OSError, RuntimeError, ValueError, KeyError):
            row["outcome"] = "failed"
            raise


def l1(experiment):
    commands = []
    create_budget(experiment)
    build_cache = experiment.output / "verilator-builds"
    create_cache(experiment.root, build_cache)
    experiment.receipt["build_cache"] = str(build_cache)

    def check(name, script, *options):
        if script in ("system_check.py", "parent_system_check.py", "system_benchmark.py",
                      "stream_projection_check.py", "checkpoint_projection_check.py"):
            options = (*options, "--build-cache", str(build_cache))
        commands.append((name, ["python3", "tests/" + script, "--output",
                                str(experiment.output / name), *options]))

    for simulator in ("iverilog", "verilator"):
        check("array-" + simulator, "array_check.py", "--simulator", simulator)
    for seed in (11, 29, 101):
        check(f"D1-streaming-{seed}", "stream_projection_check.py",
              "--seed", str(seed), "--compare-parent")
    for unit in ("convert", "integer", "exp"):
        check("numerical-" + unit, "numerical_check.py", "--unit", unit)
    check("full-reference-crosscheck", "full_reference_check.py")
    check("bridge-logical-mapping", "bridge_mapping_check.py")
    for mutation in ("awq-zero", "upper-bank", "bf16-round", "latency"):
        check("defect-" + mutation, "array_check.py", "--mutation", mutation)
    for mode in (0, 1):
        for cache in (0, 1, 2):
            check(f"system-{mode}-{cache}", "system_check.py", "--simulator", "verilator",
                  "--mode", str(mode), "--cache", str(cache))
            check(f"system-persistence-{mode}-{cache}", "system_check.py",
                  "--simulator", "verilator", "--mode", str(mode), "--cache", str(cache),
                  "--scenario", "persistence", "--seed", str((11, 29, 101)[cache]))
    check("system-default-replay", "system_check.py", "--simulator", "verilator")
    check("system-icarus-roundtrip", "system_check.py", "--simulator", "iverilog",
          "--scenario", "roundtrip")
    for seed, cache in ((11, 0), (29, 1), (101, 2)):
        check(f"system-bf16-bias-{seed}", "system_check.py", "--mode", "1",
              "--cache", str(cache), "--seed", str(seed), "--bias-stress",
              "--simulator", "verilator")
        check(f"system-bf16-bias-boundary-{cache}", "system_check.py", "--mode", "1",
              "--cache", str(cache), "--seed", str(seed), "--bias-boundary",
              "--simulator", "verilator")
    check("defect-bf16-bias", "system_check.py", "--mode", "1", "--bias-boundary",
          "--mutation", "bf16-bias", "--simulator", "verilator")
    for seed in (11, 29, 101):
        check(f"system-control-{seed}", "system_check.py", "--scenario", "control",
              "--seed", str(seed), "--simulator", "verilator")
    for seed, mode, cache in ((11, 0, 0), (29, 1, 1), (101, 0, 2)):
        check(f"system-phase-{seed}", "system_check.py", "--scenario", "control",
              "--cell", "phase", "--seed", str(seed), "--mode", str(mode),
              "--cache", str(cache), "--simulator", "verilator")
    for cell in ("singleton", "nonpower", "block16"):
        for seed, mode, cache in ((11, 0, 0), (29, 1, 1), (101, 0, 2)):
            check(f"system-{cell}-{seed}", "system_check.py", "--cell", cell,
                  "--seed", str(seed), "--mode", str(mode), "--cache", str(cache),
                  "--simulator", "verilator", "--scenario", "control")
            check(f"kv-{cell}-{seed}", "kv_check.py", "--cell", cell, "--seed", str(seed))
    check("defect-slot", "system_check.py", "--mutation", "slot-association",
          "--simulator", "verilator")
    check("defect-kv", "system_check.py", "--mutation", "kv-exponent", "--cache", "2",
          "--simulator", "verilator")
    for cell in ("singleton", "default", "maximum"):
        for seed in (11, 29, 101):
            check(f"prefetch-{cell}-{seed}", "prefetch_check.py", "--cell", cell,
                  "--seed", str(seed))
    for block in (1, 16, 128):
        check("codec-" + str(block), "codec_check.py", "--block", str(block))
    check("parameters", "parameter_check.py")
    check("production-source", "source_check.py")
    check("D5-common-service-benchmark", "system_benchmark.py")
    check("five-domain-ledger-recomparison", "benchmark_check.py", "--matrix-receipt",
          str(experiment.output / "D5-common-service-benchmark" / "receipt.json"))
    for mode in ("awq", "bf16"):
        check("configuration-default-" + mode, "configuration_check.py", "--mode", mode)
        check("official-image-" + mode, "checkpoint_import.py", "--mode", mode)
        check("official-projections-" + mode, "checkpoint_projection_check.py", "--mode", mode)
        check("official-reference-" + mode, "full_reference_run.py", "--mode", mode,
              "--packed-directory", str(experiment.output / ("official-image-" + mode)))
    check("default-synthesis", "synthesis_check.py", "--expand-packages")
    ledger = [{"check": name, "argv": argv, "outcome": "not-executed",
               "receipt": str(experiment.output / name / "receipt.json")}
              for name, argv in commands]
    for row in ledger:
        name = row["check"]
        row["priority"] = 100 if name == "default-synthesis" else (
            90 if name == "D5-common-service-benchmark" else 0)
        if name == "five-domain-ledger-recomparison":
            row["depends_on"] = ["D5-common-service-benchmark"]
        for mode in ("awq", "bf16"):
            if name == "official-image-" + mode:
                row["depends_on"] = ["configuration-default-" + mode]
            elif name == "official-projections-" + mode:
                row["depends_on"] = ["official-image-" + mode]
            elif name == "official-reference-" + mode:
                row["depends_on"] = ["official-image-" + mode, "full-reference-crosscheck"]
    experiment.receipt["l1_checks"] = ledger
    require_tools(TOOLS + ("verilator",))
    manifest = experiment.root / "data/model/official_inputs.json"
    if not manifest.is_file():
        raise RuntimeError("unmet official checkpoint prerequisite: data/model/official_inputs.json")

    def execute(row):
        run_observed_child(experiment, row["argv"], row["check"], timeout=14400,
                           delegated=row["check"] == "D5-common-service-benchmark")

    run_graph(experiment, ledger, execute)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("l1", "portable-reproduction"), required=True)
    parser.add_argument("--output", type=Path,
                        help="unused project-relative evidence directory (default: fresh UUID)")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    output = args.output or Path("evidence/verification") / (args.suite + "-" + uuid.uuid4().hex)
    experiment = None
    try:
        files = product_sources(root)
        experiment = Experiment(root, output, sys.orig_argv, files)
        experiment.receipt["declared_input_selectors"] = [
            directory + "/" + pattern for directory, pattern in INPUT_SELECTORS]
        record_input_bindings(experiment, "before")
        if any(experiment.receipt["declared_inputs_before"][name]["sha256"] != digest
               for name, digest in experiment.receipt["source_hashes"].items()):
            raise RuntimeError("declared sources changed while capturing input snapshots")
        suite_failure = None
        try:
            if args.suite == "portable-reproduction":
                portable(experiment, files)
            else:
                l1(experiment)
        except (OSError, RuntimeError, ValueError, KeyError) as error:
            suite_failure = str(error)
            experiment.receipt["suite_failure"] = str(error)
            raise
        finally:
            try:
                verify_input_bindings(experiment)
            except (OSError, RuntimeError, ValueError, KeyError) as error:
                experiment.receipt["input_binding_failure"] = str(error)
                if suite_failure is None:
                    raise
        experiment.finish(0)
        print("VERIFICATION_COMPLETED suite=" + args.suite)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        if experiment is not None:
            experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
