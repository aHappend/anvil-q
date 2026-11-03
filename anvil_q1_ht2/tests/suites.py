"""Self-generating mandatory L1 matrix and clean-directory reproduction."""

import shutil
import uuid

from decoder_reference import Geometry
from evidence import ROOT, SOURCE_PATTERNS, digest, execute, relative, require_success, write_json


def partition(directory, label):
    child = directory / f"{label}-{uuid.uuid4().hex[:8]}"
    child.mkdir()
    return child


def behavior(directory, compact=False):
    import compatibility_checks
    import integration_checks
    import leaf_checks
    import operator_checks
    import parameter_checks
    import protocol_checks

    checks = []

    def run(label, function, *args, **kwargs):
        print(f"progress: behavior {label}", flush=True)
        checks.append(function(partition(directory, label), *args, **kwargs))

    run("startup", integration_checks.top, "iverilog",
        Geometry(vocabulary=1, sequence=1, window=1), batch=False, startup=True)
    if compact:
        run("sparse", leaf_checks.sparse, "iverilog")
        run("array", leaf_checks.mac, "verilator")
        run("native-top", integration_checks.top, "verilator")
        return checks
    for simulator in ("iverilog", "verilator"):
        for label in ("conversions", "pipelines", "sparse", "verifier", "masks", "dequant", "mac"):
            run(f"{label}-{simulator}", getattr(leaf_checks, label), simulator)
        for operation in ("divsqrt", "exp", "sincos"):
            run(f"{operation}-{simulator}", leaf_checks.scalars, operation, simulator)
        for operation in ("rmsnorm", "swiglu"):
            run(f"{operation}-{simulator}", operator_checks.vectors, operation, simulator)
        run("control-" + simulator, protocol_checks.control, simulator)
        for kind in ("mailbox", "response_fifo"):
            run(f"{kind}-{simulator}", protocol_checks.cdc, kind, simulator)
    checks.append({"name": "illegal-parameters",
                   "cases": parameter_checks.run(partition(directory, "illegal-parameters"))})
    for mode in (0, 1, 2):
        run(f"compact-top-mode{mode}", integration_checks.top, "verilator",
            Geometry(), mode, 17, threshold=0x3F80 if mode == 2 else 0)
    run("singleton-functional", integration_checks.top, "verilator",
        Geometry(vocabulary=1, sequence=1, window=1), batch=False)
    run("gqa-seed43", integration_checks.top, "verilator",
        Geometry(2, 24, 40, 3, 1, 8, 8, 31, 9, 3, 3), 0, 43)
    run("medium-seed89", integration_checks.top, "verilator",
        Geometry(2, 64, 128, 4, 2, 16, 16, 257, 17, 3, 5), 0, 89)
    for mode in (0, 2):
        run(f"compatibility-{mode}", compatibility_checks.run, mode, 17)
    run("compatibility-entry-alias", compatibility_checks.run, 0, 43, "anvil_q1_top")
    return checks


def reproduction(directory):
    clone = partition(directory, "clean")
    copied = {}
    for pattern in SOURCE_PATTERNS:
        for source in sorted(ROOT.glob(pattern)):
            destination = clone / source.relative_to(ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            copied[str(source.relative_to(ROOT))] = digest(destination)
    if not copied or list(clone.glob("**/*.vvp")) or list(clone.glob("**/compile-obj")):
        raise AssertionError("clean reproduction contains stale binaries")
    write_json(directory / "copied-inputs.json", copied)
    runs = []
    for args, label in ((["--suite", "behavior", "--compact"], "clean-behavior"),
                        (["--probe", "synthesis-top"], "clean-synthesis")):
        run = require_success(execute(
            ["python3", "tests/verify.py", *args], directory, label, timeout=2200,
            cwd=clone, inputs=[clone / path for path in copied]))
        runs.append({"name": label, "receipt": relative(run / "receipt.json")})
    after = {path: digest(clone / path) for path in copied}
    if after != copied:
        raise AssertionError("reproduction modified copied source inputs")
    return [{"name": "clean-directory-reproduction", "copied_files": len(copied),
             "runs": runs, "scope": "compact portable L1; external official hardware "
             "and comparator prerequisites remain required for full-model reproduction"}]
