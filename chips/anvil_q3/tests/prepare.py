"""Bounded advisory diagnostics; never an engineering acceptance substitute.

Reproduce decoder completion-checker sensitivity from the project root:
python3 tests/prepare.py --probe decoder-trace-checker
Both this probe and structure() run the same valid/defective trace fixtures.
Simulation via --probe decoder also checks completion on the final-logit edge.
Select a required decoder seed without changing the mandatory matrix:
python3 tests/prepare.py --probe decoder --seed 89 --banks 8 --mode 1
The default seed remains 17; diagnostic results are not mandatory-gate acceptance.
Decoder probes also forward --queue-depth, --tile-k and --tile-rows to the DUT:
python3 tests/prepare.py --probe decoder --queue-depth 16 --tile-k 128 --tile-rows 8
Omitting these controls retains the reduced profile's 3/24/3 defaults.
Read-only physical-tool discovery (not fit, programming or HIL):
python3 tests/prepare.py --probe physical-toolchain
This probe fails on absent/invalid cable enumeration even when Quartus exits zero.
Offline cable-list checker sensitivity (no hardware access):
python3 tests/prepare.py --probe physical-inventory-checker
Offline native Q1 adapter identity sensitivity (no asset acquisition):
python3 tests/prepare.py --probe native-baseline-checker
The admitted harness probe also rejects changed revision/license/source identity,
missing or renamed RTL and duplicate source filenames. These fixtures do not
establish public provenance, numerical behavior or Q4 coverage.
Cable listings accompanied by error, critical-error or fatal diagnostics in
either tool stream must fail, including when cable enumeration exits zero.
Offline fitted-summary driver sensitivity (no Quartus or hardware access):
python3 tests/prepare.py --probe fitted-summary-checker
The driver requires exactly one successful fitter status and exactly one
matching device record; duplicate/conflicting records are rejected.
Missing, duplicate and empty fitted-image fixtures must also be rejected.
Zero-exit compilation/STA stdout and stderr fixtures inject each forbidden
Quartus diagnostic; a successful summary must not hide those failures.
Additional numbered/unnumbered error and fatal records must also fail, while
informational error counts and unrelated warning records remain legal.
Separate summary and STA-report fixtures inject the same diagnostics to ensure
report scanning includes both summary and detailed report files.
The same driver fixtures accept exactly zero setup/hold slack and reject
negative setup/hold slack, unconstrained endpoints and unapproved exceptions.
These synthetic files never establish a usable bitstream, timing closure or HIL.
Offline decoder reconciliation scope-guard sensitivity (no evidence repair):
python3 tests/prepare.py --probe reconciliation-scope-checker
Offline retained-source/log/receipt finalization sensitivity:
python3 tests/prepare.py --probe snapshot-retention
Missing or changed snapshots, missing raw logs and missing or changed child
receipts reject success without rewriting the previous aggregate receipt.
This detects project evidence loss; it does not repair shared-runtime retention.
Full-default synthesis diagnostic (not the mandatory synthesis matrix or STA):
python3 tests/prepare.py --probe synthesis --official-defaults --profile 3
Without --official-defaults, synthesis retains the reduced A geometry.
The flag is supported only for memory-map and synthesis probes.
Offline synthesis/decoder/activation dispatch regression (no DUT execution):
python3 tests/preparation_checks.py
Activation lane-memory capacity, stalls, tails and recovery (public pins):
python3 tests/prepare.py --probe activation-storage --banks 8 --simulator iverilog
This uses all 11008 activation components; smaller bank cases include eight-component
and tile-tail vectors. Each active bank's first result is held for 4096 cycles
to propagate backpressure through prefetched operands. Malformed loads,
mid-load reset/flush and stalled-result flush must recover with new full loads.
Three isolated activation mutations test write-lane, read-word and stall-enable
sensitivity. These probes do not replace any mandatory gate.
"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decoder_checks import decoder_case
from execution import Run
from reference import Geometry
from leaf_checks import codec_case, dot8_case
from prerequisites import prerequisites, baseline_adapters
from synthesis_checks import synthesis_case
from compatibility_checks import startup_geometry
from scalar_checks import scalar_case
from mutation_checks import MUTATIONS, mutation_case
from benchmark_checks import quality_lock, quality_case, native_q1_benchmark, baseline_prerequisites
from public_assets import validate_assets
from execution import ROOT
import json
from execution import write_json
from structure_checks import timing_lint, parent_structure
from harness_checks import (harness, board_prerequisite_sensitivity, decoder_trace_sensitivity,
                            physical_inventory_sensitivity, fitted_summary_sensitivity,
                            reconciliation_scope_sensitivity, baseline_index_sensitivity,
                            native_baseline_sensitivity)
from scheduler_checks import scheduler_case
from prefetch_checks import prefetch_case
from frontend_probe import frontend_probe
from synthesis_checks import lower_packages
from boundary_checks import singleton_case
from acquire_assets import acquire_assets
from official_slice import official_weight_slice
from math_memory_checks import math_memory_case
from accumulator_checks import accumulator_case
from tensor_checks import activation_case, tensor_case
from reproduce import reproduce
from map_checks import map_case
from parameters import A, defaults
from fpga_checks import host_case, bridge_case
from hardware_checks import board_inputs, physical_cable_inventory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", choices=["decoder", "dot8", "codec", "prerequisites",
                                          "synthesis", "scalar", "mutation", "quality",
                                          "quality-decoder", "hardware-help", "timing-lint",
                                          "harness", "scheduler", "prefetch",
                                          "synthesis-frontend", "lowered-decoder",
                                          "singleton", "acquire-assets", "official-slice",
                                          "math-memory", "accumulator", "tensor",
                                          "reproduce-smoke", "memory-map", "host-control",
                                          "ddr-bridge", "baseline-structure",
                                          "physical-prerequisites", "native-q1-smoke",
                                          "native-q1-benchmark", "baseline-adapters",
                                          "trace-integrity", "receipt-reconciliation",
                                          "board-input-checker", "snapshot-retention",
                                          "decoder-trace-checker", "physical-toolchain",
                                          "physical-inventory-checker",
                                          "fitted-summary-checker",
                                          "reconciliation-scope-checker",
                                          "baseline-index-checker",
                                          "native-baseline-checker",
                                          "activation-storage"], required=True)
    parser.add_argument("--failed-receipt",
                        help="retained decoder preparation receipt; reconciliation cannot "
                             "repair mandatory-check retention or runtime persistence")
    parser.add_argument("--comparison-receipt")
    parser.add_argument("--queue-depth", type=int, choices=[1, 3, 16], default=3)
    parser.add_argument("--wrap", type=int, choices=[0, 1, 2], default=0)
    parser.add_argument("--tile-k", type=int, choices=[8, 24, 128], default=24)
    parser.add_argument("--tile-rows", type=int, choices=[1, 3, 8], default=3)
    parser.add_argument("--mutation", choices=[m[0] for m in MUTATIONS], default="zero-subtraction")
    parser.add_argument("--unit", type=int, choices=range(5), default=0)
    parser.add_argument("--simulator", choices=["iverilog", "verilator"], default="iverilog")
    parser.add_argument("--mode", type=int, choices=[0, 1, 2], default=0)
    parser.add_argument("--asymmetric", type=int, choices=[0, 1], default=0)
    parser.add_argument("--banks", type=int, choices=[1, 2, 4, 8], default=8)
    parser.add_argument("--profile", type=int, choices=[1, 2, 3], default=3)
    parser.add_argument("--prelude", type=int, choices=range(6), default=0)
    parser.add_argument("--first-new", type=int, choices=[0, 1], default=1)
    parser.add_argument("--tokens", type=int, choices=range(1, 10), default=7)
    parser.add_argument("--seed", type=int, choices=[17, 89, 257],
                        help="decoder diagnostic seed (default: 17)")
    parser.add_argument("--repair-of")
    parser.add_argument("--fault-scenario", type=int, choices=range(10), default=0)
    parser.add_argument("--adversarial", action="store_true")
    parser.add_argument("--implementation", choices=["q3", "q2", "q1-wrapper"], default="q3")
    parser.add_argument("--official-defaults", action="store_true",
                        help="use selected profile's full defaults for memory-map or synthesis")
    args = parser.parse_args()
    if args.seed is not None and args.probe != "decoder":
        parser.error("--seed is supported only for --probe decoder")
    if args.official_defaults and args.probe not in ("memory-map", "synthesis"):
        parser.error("--official-defaults is supported only for memory-map or synthesis")
    run = Run("evidence/preparation/independent-" + args.probe, args.probe,
              repair_of=args.repair_of)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        if args.probe in ("physical-toolchain", "physical-inventory-checker",
                          "fitted-summary-checker", "reconciliation-scope-checker",
                          "baseline-index-checker", "native-baseline-checker"):
            tools = [("python3", "--version")]
        else:
            tools = [("iverilog", "-V"), ("vvp", "-V")] if args.simulator == "iverilog" else [
                ("verilator", "--version")]
        run.versions(tools)
        if args.probe == "native-baseline-checker":
            text, _ = run.tool([
                "python3", "-c",
                "import json,sys; sys.path.insert(0,'tests'); "
                "from harness_checks import native_baseline_sensitivity; "
                "print(json.dumps(native_baseline_sensitivity(),sort_keys=True))",
            ])
            result = json.loads(text)
        elif args.probe == "baseline-index-checker":
            text, _ = run.tool([
                "python3", "-c",
                "import json,sys; sys.path.insert(0,'tests'); "
                "from harness_checks import baseline_index_sensitivity; "
                "print(json.dumps(baseline_index_sensitivity(),sort_keys=True))",
            ])
            result = json.loads(text)
        elif args.probe == "reconciliation-scope-checker":
            text, _ = run.tool([
                "python3", "-c",
                "import json,sys; sys.path.insert(0,'tests'); "
                "from harness_checks import reconciliation_scope_sensitivity; "
                "print(json.dumps(reconciliation_scope_sensitivity(),sort_keys=True))",
            ])
            result = json.loads(text)
        elif args.probe == "fitted-summary-checker":
            text, _ = run.tool([
                "python3", "-c",
                "import json,sys; from pathlib import Path; from types import SimpleNamespace; "
                "sys.path.insert(0,'tests'); "
                "from harness_checks import fitted_summary_sensitivity; "
                "print(json.dumps(fitted_summary_sensitivity("
                "SimpleNamespace(path=Path(sys.argv[1]).resolve())),sort_keys=True))",
                run.rel(run.path),
            ])
            result = json.loads(text)
        elif args.probe == "physical-toolchain":
            run.versions([("quartus_sh", "--version"), ("quartus_sta", "--version"),
                          ("quartus_pgm", "--version")])
            missing = [name for name in ("quartus_sh", "quartus_sta", "quartus_pgm")
                       if not run.tool_versions[name]["available"]]
            if missing:
                raise RuntimeError("missing physical toolchain executables: " + ", ".join(missing))
            result = physical_cable_inventory(run)
        elif args.probe == "physical-inventory-checker":
            text, _ = run.tool([
                "python3", "-c",
                "import json,sys; from pathlib import Path; from types import SimpleNamespace; "
                "sys.path.insert(0,'tests'); "
                "from harness_checks import physical_inventory_sensitivity; "
                "print(json.dumps(physical_inventory_sensitivity("
                "SimpleNamespace(path=Path(sys.argv[1]))),sort_keys=True))",
                run.rel(run.path),
            ])
            result = json.loads(text)
        elif args.probe == "decoder-trace-checker":
            run.versions([("python3", "--version")])
            text, _ = run.tool([
                "python3", "-c",
                "import json,sys; from pathlib import Path; from types import SimpleNamespace; "
                "sys.path.insert(0,'tests'); "
                "from harness_checks import decoder_trace_sensitivity; "
                "print(json.dumps(decoder_trace_sensitivity("
                "SimpleNamespace(path=Path(sys.argv[1]))),sort_keys=True))",
                run.rel(run.path),
            ])
            result = json.loads(text)
        elif args.probe == "snapshot-retention":
            run.versions([("python3", "--version")])
            text, _ = run.tool(["python3", "tests/snapshot_retention_checks.py",
                                run.rel(run.path / "snapshot-retention-fixtures")])
            result = json.loads(text)
        elif args.probe == "board-input-checker":
            result = board_prerequisite_sensitivity(run)
        elif args.probe == "receipt-reconciliation":
            if not args.failed_receipt:
                raise ValueError("receipt-reconciliation requires --failed-receipt")
            run.versions([("python3", "--version")])
            text, _ = run.tool(["python3", "tests/trace_integrity.py",
                                "--reconcile", args.failed_receipt])
            result = json.loads(text)
            write_json(run.path / "receipt-reconciliation.json", result)
        elif args.probe == "trace-integrity":
            if not args.failed_receipt or not args.comparison_receipt:
                raise ValueError("trace-integrity requires both retained receipt paths")
            run.versions([("python3", "--version")])
            text, _ = run.tool(["python3", "tests/trace_integrity.py",
                                "--failed", args.failed_receipt,
                                "--comparison", args.comparison_receipt])
            result = json.loads(text)
            write_json(run.path / "trace-integrity.json", result)
        elif args.probe == "baseline-adapters":
            run.versions([("python3", "--version"), ("curl", "--version")])
            declared = list(json.loads((ROOT / "tests/public_assets.json").read_text())["assets"])
            provenance = json.loads((ROOT / "design/model_provenance.json").read_text())
            declared.extend(provenance.get("generation_baselines", []))
            assets = validate_assets(run, [a for a in declared if a["category"] == "baseline"])
            result = baseline_adapters(run, assets)
            if result["unmet"]:
                raise RuntimeError("unmet native baseline prerequisites: " +
                                   "; ".join(result["unmet"]))
        elif args.probe in ("native-q1-smoke", "native-q1-benchmark"):
            run.versions([("python3", "--version"), ("curl", "--version")])
            declared = json.loads((ROOT / "tests/public_assets.json").read_text())["assets"]
            assets = validate_assets(run, [a for a in declared if a["category"] == "baseline"])
            write_json(run.path / "baseline-prerequisites.json",
                       baseline_prerequisites(assets, run.hashes))
            result = native_q1_benchmark(
                run, assets, simulator=args.simulator,
                bounded_smoke=args.probe == "native-q1-smoke")
        elif args.probe == "physical-prerequisites":
            result = board_inputs(run)
        elif args.probe == "baseline-structure":
            result = parent_structure(run, simulators=(args.simulator,))
        elif args.probe == "ddr-bridge":
            result = bridge_case(run, args.banks, args.mode, args.simulator)
        elif args.probe == "host-control":
            result = host_case(run, args.simulator)
        elif args.probe == "memory-map":
            from dataclasses import replace
            result = map_case(run, replace(defaults(args.profile) if args.official_defaults else A,
                                           CACHE_MODE=args.mode),
                              args.simulator, "official" if args.official_defaults else "A")
        elif args.probe == "reproduce-smoke":
            result = reproduce(run, bounded_smoke=True)
        elif args.probe == "tensor":
            result = tensor_case(run, args.banks, args.simulator)
        elif args.probe == "activation-storage":
            result = activation_case(run, args.banks, args.simulator,
                                     capacity=11008 if args.banks == 8 else
                                     8 if args.banks == 1 else 120)
        elif args.probe == "accumulator":
            result = accumulator_case(run, args.simulator)
        elif args.probe == "math-memory":
            result = math_memory_case(run, args.unit, args.simulator)
        elif args.probe == "official-slice":
            result = official_weight_slice(run)
        elif args.probe == "acquire-assets":
            result = acquire_assets(run)
        elif args.probe == "singleton":
            result = singleton_case(run, args.banks, args.mode, args.asymmetric, args.simulator)
        elif args.probe == "lowered-decoder":
            folder = run.path / "lowering"
            folder.mkdir()
            rtl = [run.rel(p) for p in lower_packages(folder)]
            result = decoder_case(run, Geometry(BANKS=args.banks, CACHE_MODE=args.mode,
                                                INT4_ASYM=args.asymmetric),
                                  simulator=args.simulator, tokens=[1, 4], rtl=rtl,
                                  label="yosys-lowering-equivalence")
        elif args.probe == "synthesis-frontend":
            result = frontend_probe(run)
        elif args.probe == "prefetch":
            result = prefetch_case(run, args.banks, args.tile_k, args.tile_rows, args.simulator)
        elif args.probe == "scheduler":
            result = scheduler_case(run, args.banks, args.queue_depth, args.simulator, wrap=args.wrap)
        elif args.probe == "harness":
            result = harness(run)
        elif args.probe == "timing-lint":
            result = timing_lint(run)
        elif args.probe == "hardware-help":
            result = {}
            for selector in ("rtl-timing-lint", "quartus-sta", "board-hil"):
                _, record = run.tool(["vulcan", "hardware", "fpga", selector, "--help"])
                result[selector] = record
        elif args.probe == "synthesis":
            from dataclasses import replace
            run.versions([("yosys", "-V")])
            geometry = replace(defaults(args.profile) if args.official_defaults else Geometry(),
                               BANKS=args.banks, CACHE_MODE=args.mode,
                               INT4_ASYM=args.asymmetric)
            label = "official-default" if args.official_defaults else "bounded-A"
            result = synthesis_case(run, geometry, label)
        elif args.probe == "quality-decoder":
            result = quality_case(run, args.mode, args.asymmetric, args.banks)
        elif args.probe == "quality":
            result, _ = quality_lock()
            write_json(run.path / "corpus-lock.json", result)
        elif args.probe == "mutation":
            result = mutation_case(run, next(m for m in MUTATIONS if m[0] == args.mutation),
                                   args.simulator)
        elif args.probe == "scalar":
            result = scalar_case(run, args.simulator, args.unit)
        elif args.probe == "prerequisites":
            result = prerequisites(run)
        elif args.probe == "dot8":
            result = dot8_case(run, args.simulator)
        elif args.probe == "codec":
            result = codec_case(run, args.simulator, args.mode, args.asymmetric)
        else:
            from dataclasses import replace
            result = decoder_case(run, replace(startup_geometry(args.profile),
                                               BANKS=args.banks, CACHE_MODE=args.mode,
                                               INT4_ASYM=args.asymmetric,
                                               QUEUE_DEPTH=args.queue_depth,
                                               TILE_K=args.tile_k, TILE_ROWS=args.tile_rows),
                                  simulator=args.simulator,
                                  seed=17 if args.seed is None else args.seed,
                                  prelude=args.prelude, first_new=args.first_new,
                                  fault_scenario=args.fault_scenario,
                                  adversarial=args.adversarial,
                                  implementation=args.implementation,
                                  tokens=[1, 4, 2, 6, 3, 5, 7, 8, 9][:args.tokens])
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    run.finish("passed", result=result)


if __name__ == "__main__":
    main()
