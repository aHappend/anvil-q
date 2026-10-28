"""Bounded advisory build-reuse diagnostics; never restarts aggregate acceptance."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_cache import compile_verilator, create_cache
from retention import Experiment


PROBE = """module build_reuse_probe;
  parameter integer ADDEND=2;
  integer operand, expected, observed;
  initial begin
    if (!$value$plusargs("operand=%d",operand) ||
        !$value$plusargs("expected=%d",expected)) $fatal(1,"PROBE_INPUT");
    observed=operand*7+ADDEND;
`ifdef OBSERVE
    $display("PROBE_INSTRUMENTED");
`endif
    if (observed !== expected) $fatal(1,"BUILD_REUSE_NUMERICAL got=%0d expected=%0d",
                                    observed,expected);
    $display("BUILD_REUSE_CHECKED operand=%0d result=%0d",operand,observed);
    $finish;
  end
endmodule
"""


def load(root, path):
    receipt = json.loads((root / path / "receipt.json").read_text())
    if receipt["exit"] != 0:
        raise RuntimeError("failed preparation child: " + str(path))
    return receipt


def costs(receipt):
    return {
        "compilation_s": sum(row["duration_s"] for row in receipt["commands"]
                             if row["argv"][0] == "verilator" and "--binary" in row["argv"]),
        "simulation_s": sum(row["duration_s"] for row in receipt["commands"]
                            if row["argv"][0].endswith(("_sim", "probe_sim"))),
        "builds": receipt.get("builds", []),
    }


def contract(experiment, cache):
    rows = []
    specifications = [
        ("initial", PROBE, 2, False, False, 11, 79, False),
        ("equivalent", PROBE, 2, False, False, 29, 205, True),
        ("source-change", PROBE.replace("operand*7", "operand*8"), 2, False, False, 11, 90, False),
        ("parameter-change", PROBE, 3, False, False, 11, 80, False),
        ("instrumentation-change", PROBE, 2, True, False, 11, 79, False),
        ("mutant", PROBE.replace("operand*7", "operand*7+1"), 2, False, True, 11, 79, False),
        ("return-original", PROBE, 2, False, False, 101, 709, True),
    ]
    for name, source, addend, instrumented, mutant, operand, expected, hit in specifications:
        output = experiment.output / name
        child = Experiment(experiment.root, output, ["build-reuse-contract", name],
                           ["tests/build_cache.py", "tests/build_reuse_check.py", "tests/retention.py"])
        try:
            relative = Path("mutant" if mutant else "sources") / "tests/build_reuse_probe.sv"
            path = child.directory / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source)
            child.receipt["generated_input"] = {
                "path": str(output / relative), "sha256": hashlib.sha256(source.encode()).hexdigest()}
            executable = compile_verilator(child, [
                "verilator", "--binary", "--timing", "-Wno-fatal",
                "--top-module", "build_reuse_probe", "--Mdir", str(output / "obj"),
                "-MAKEFLAGS", "VK_PCH_I_FAST= VK_PCH_I_SLOW=", "-o", "probe_sim",
                f"-GADDEND={addend}", *(["-DOBSERVE"] if instrumented else []),
                str(output / relative)], cache=cache)
            if child.receipt["builds"][-1]["cache_hit"] != hit:
                raise RuntimeError("wrong cache reuse/invalidation decision: " + name)
            text = child.run([executable, f"+operand={operand}", f"+expected={expected}"],
                             "simulate", allow_mismatch=mutant)
            if mutant:
                if child.receipt["commands"][-1]["exit"] == 0 or "BUILD_REUSE_NUMERICAL" not in text:
                    raise RuntimeError("mutant was not rejected by the numerical assertion")
            elif f"BUILD_REUSE_CHECKED operand={operand} result={expected}" not in text:
                raise RuntimeError("missing fresh numerical comparison")
            if instrumented and "PROBE_INSTRUMENTED" not in text:
                raise RuntimeError("instrumentation was not compiled")
            child.receipt["comparison_summary"] = text.strip()
            child.finish(0)
        except (OSError, RuntimeError, ValueError, KeyError) as error:
            child.finish(1, error)
            raise
        rows.append({"case": name, "receipt": str(output / "receipt.json"), **costs(child.receipt)})
    keys = [row["builds"][0]["key"] for row in rows]
    if len(set(keys)) != 5 or keys[0] != keys[1] or keys[0] != keys[-1]:
        raise RuntimeError("content/parameter/instrumentation/mutant key separation failed")
    experiment.receipt["cases"] = rows
    experiment.receipt["scope"] = "synthetic compilation-cache contract only, not accelerator coverage"


def child_run(experiment, cache, name, script, options):
    output = experiment.output / name
    experiment.run(["python3", "-B", "tests/" + script, "--output", str(output),
                    "--build-cache", str(cache), *options], name, timeout=14400)
    return output, load(experiment.root, output)


def connected(experiment, cache):
    rows = []
    receipts = []
    for name, options in (
            ("initial", []), ("equivalent", []),
            ("persistence-bf16-int8", ["--scenario", "persistence", "--mode", "1",
                                      "--cache", "2", "--seed", "29"])):
        output, receipt = child_run(experiment, cache, name, "system_check.py",
                                    ["--simulator", "verilator", *options])
        if receipt["builds"][0]["cache_hit"] != (name != "initial"):
            raise RuntimeError("connected-top build not reused as required")
        if len(receipt["readback_sha256"]) != 2:
            raise RuntimeError("missing complete pre/post DDR readback comparisons")
        rows.append({"case": name, "receipt": str(output / "receipt.json"), **costs(receipt),
                     "comparison_summary": receipt["comparison_summary"]})
        receipts.append(receipt)
    if (receipts[0]["comparison_summary"] != receipts[1]["comparison_summary"] or
            receipts[0]["fixture"] != receipts[1]["fixture"] or
            receipts[0]["readback_sha256"] != receipts[1]["readback_sha256"]):
        raise RuntimeError("equivalent runs changed numerical/protocol observations")
    experiment.receipt["cases"] = rows
    experiment.receipt["scope"] = "small connected-top numerical/protocol and persistence comparisons only"
    output = experiment.output / "icarus-roundtrip"
    experiment.run(["python3", "-B", "tests/system_check.py", "--output", str(output),
                    "--scenario", "roundtrip", "--simulator", "iverilog"], "icarus-roundtrip")
    smoke = load(experiment.root, output)
    if smoke["readback_bytes_per_pass"] != 1024:
        raise RuntimeError("compact Icarus roundtrip did not check both 1024-byte readbacks")
    experiment.receipt["icarus_roundtrip"] = {
        "receipt": str(output / "receipt.json"),
        "simulation_s": next(row["duration_s"] for row in smoke["commands"]
                             if row["argv"][0] == "vvp"),
        "comparison_summary": smoke["comparison_summary"]}


def streaming(experiment, cache):
    rows = []
    for seed in (11, 29):
        output, receipt = child_run(experiment, cache, f"seed{seed}", "stream_projection_check.py",
                                    ["--seed", str(seed), "--compare-parent"])
        builds = receipt["builds"]
        if len(builds) != 3 or any(row["cache_hit"] != (seed == 29) for row in builds):
            raise RuntimeError("streaming HT/parent builds not reused as required")
        rows.append({"case": f"seed{seed}", "receipt": str(output / "receipt.json"),
                     **costs(receipt), "metrics": receipt["metrics"], "parent": receipt["parent"]})
    experiment.receipt["cases"] = rows
    experiment.receipt["scope"] = "two seeded default-width D1 projections, not aggregate acceptance"


def benchmark(experiment, cache):
    rows = []
    for seed in (11, 29):
        output, receipt = child_run(experiment, cache, f"seed{seed}", "system_benchmark.py",
                                    ["--seed", str(seed), "--cache", "0", "--weight-mode", "w4"])
        metrics = receipt["benchmarks"][0]
        for implementation in [metrics["ht"], *metrics["parent"].values()]:
            path = Path(implementation["receipt"]).parent
            child = load(experiment.root, path)
            if child["builds"][0]["cache_hit"] != (seed == 29):
                raise RuntimeError("nested benchmark build reuse mismatch")
            rows.append({"case": str(path), "receipt": str(path / "receipt.json"), **costs(child)})
        recomparison = experiment.output / f"recompare{seed}"
        experiment.run(["python3", "-B", "tests/benchmark_check.py", "--output", str(recomparison),
                        "--ht-receipt", metrics["ht"]["receipt"],
                        "--parent-receipt", metrics["parent"]["4"]["receipt"],
                        "--seed", str(seed)], f"recompare{seed}")
        load(experiment.root, recomparison)
    experiment.receipt["cases"] = rows
    experiment.receipt["scope"] = (
        "two W4/Q16 benchmark cells with fresh traces and dependent recomparison, not full matrix")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scope", required=True, choices=("contract", "connected", "streaming", "benchmark"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    names = [str(path.relative_to(root))
             for folder, pattern in (("rtl", "*.sv"), ("anvil_q2_reference/rtl", "*.sv"), ("tests", "*"))
             for path in sorted((root / folder).glob(pattern)) if path.is_file()]
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    try:
        experiment.run(["python3", "--version"], "python-version")
        cache = args.output / "builds"
        create_cache(root, cache)
        {"contract": contract, "connected": connected, "streaming": streaming,
         "benchmark": benchmark}[args.scope](experiment, cache)
        experiment.receipt["compilation_s"] = sum(row["compilation_s"] for row in experiment.receipt["cases"])
        experiment.receipt["simulation_s"] = sum(row["simulation_s"] for row in experiment.receipt["cases"])
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, ArithmeticError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
