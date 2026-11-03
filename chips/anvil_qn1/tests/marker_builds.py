"""Retain completed marker builds even when their later simulation is interrupted."""

import hashlib
import json
from pathlib import Path

from component_cache import component
from execution import ROOT, relative


OPTIMIZATION = "OPT_FAST=-O3 OPT_SLOW=-O3 OPT_GLOBAL=-O3"


def marker_build(run, text, binding, prefill=False):
    stem = "prefill-marker-build" if prefill else "marker-build"
    driver_name = "prefill_marker_driver.cpp" if prefill else "marker_driver.cpp"
    prefix = "prefill-marker" if prefill else "marker"

    def build(child):
        driver = child.path / driver_name
        driver.write_text(text)
        objects = child.path / f"obj-{prefix}"
        parameters = binding["parameters"]
        sources = [relative(p) for p in sorted((ROOT / "rtl").glob("anvil_qn1_*.sv"))]
        child.execute([
            "verilator", "--cc", "--exe", "--build", "-Wno-fatal", "-j", "2",
            "--threads", str(binding["simulation_threads"]),
            "-MAKEFLAGS", OPTIMIZATION, "--top-module", "anvil_qn1_top",
            *[f"-G{k}={v}" for k, v in parameters.items()],
            "--Mdir", relative(objects), "-o", "simulate", *sources,
            f"../{driver_name}"], f"{prefix}-compile")
        binary = objects / "simulate"
        return {"binary": relative(binary), "binding": binding,
                "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                "optimization": OPTIMIZATION}

    def validate(result):
        if result.get("binding") != binding or result.get("optimization") != OPTIMIZATION:
            raise AssertionError("incompatible marker build configuration")
        binary = ROOT / result["binary"]
        if (not binary.is_file() or
                hashlib.sha256(binary.read_bytes()).hexdigest() != result["binary_sha256"]):
            raise AssertionError("missing/changed marker executable")

    def validate_retained(parent, path, receipt, result):
        driver = path.parent / driver_name
        if not driver.is_file() or driver.read_text() != text:
            raise AssertionError("marker build driver snapshot mismatch")
        compiles = [c for c in receipt["commands"] if c["argv"][0] == "verilator"]
        if (len(compiles) != 1 or "-MAKEFLAGS" not in compiles[0]["argv"] or
                compiles[0]["argv"][compiles[0]["argv"].index("-MAKEFLAGS") + 1] != OPTIMIZATION):
            raise AssertionError("missing actual marker compiler optimization")
        stdout = (ROOT / compiles[0]["stdout"]).read_text()
        fast_commands = [line for line in stdout.splitlines()
                         if line.startswith("g++ ") and " -c " in line]
        if not fast_commands or any(" -O3 " not in line or " -Os " in line
                                    for line in fast_commands):
            raise AssertionError("marker compilation did not use O3 exclusively")

    return component(
        run, stem, build,
        inputs=("tests/marker_builds.py", "tests/marker_checks.py",
                "tests/prefill_marker_checks.py", "tests/reference.py"),
        parameters={"binding": binding, "optimization": OPTIMIZATION},
        tools=("python3", "verilator", "g++", "make"),
        validate=validate, validate_retained=validate_retained)
