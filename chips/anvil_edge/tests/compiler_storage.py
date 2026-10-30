"""Compiler retention regression and affected boot measurement, not acceptance."""

import copy
from pathlib import Path

from scheduling import CompilerStorage


def storage_probe(evidence, *, boot):
    from storage import boot_test
    from verify import ROOT, VerificationFailure, write_json

    evidence.tools(("python3", "make"))
    result = evidence.child([
        "python3", "tests/test_compiler_storage.py", evidence.relative(evidence.path),
    ], "storage-cleanup-regression")
    evidence.record["storage_cleanup_regression"] = {
        "receipt": str(Path(result["stdout"]).parent / "receipt.json"),
        "scope": "Synthetic resource/retention controls and real GNU make target "
                 "selection; not a functional RTL mutation or a peak measurement",
    }
    if not boot:
        return

    # Check before tools, large input files or a substantive compiler launch.
    # The actual child independently reacquires this same shared reservation.
    try:
        with CompilerStorage(ROOT).claim(["verilator", "--build"]) as lease:
            write_json(evidence.path / "boot-storage-preflight.json", lease)
    except OSError as error:
        write_json(evidence.path / "boot-storage-preflight.json", {
            "status": "blocked-before-compilation", "diagnostic": str(error),
            "required_action": "Shared runtime restores project filesystem headroom "
                               "and rechecks capacity; no retained evidence deleted",
        })
        raise

    evidence.tools(("verilator", "g++", "make"))
    rows = []
    for label, pch in (("no-pch", False), ("original-pch", True)):
        scope = copy.copy(evidence)
        scope.compiler_pch = pch
        row = boot_test(scope, 262145, 17, capacity=262145, label=label, trace=True)
        receipt = row["compile_receipt"]
        log = (ROOT / receipt["stdout"]).read_text()
        pch_files = [item for item in receipt["compiler_intermediates_removed"]
                     if item["path"].endswith(".gch")]
        if pch:
            assert len(pch_files) == 2 and "-x c++-header" in log
        else:
            assert not pch_files and "-x c++-header" not in log
        assert receipt["compiler_storage_observation"]["samples"] > 0
        rows.append(row)
    from performance import public_summary
    assert public_summary(rows[0]) == public_summary(rows[1])
    assert any(line.startswith("BOOT_OBSERVATION ") for line in public_summary(rows[0]))
    assert rows[0]["actual_comparisons"] == rows[1]["actual_comparisons"] > 0
    assert rows[0]["source_sha256"] == rows[1]["source_sha256"]
    assert [item["sha256"] for item in rows[0]["input_files"]] == [
        item["sha256"] for item in rows[1]["input_files"]]
    valid = boot_test(evidence, 257, 17, label="valid-no-pch")
    assert valid["actual_comparisons"] > 0
    measurements = [{
        "variant": label, "compile_receipt": row["compile_receipt"],
        "comparisons": row["actual_comparisons"],
        "public_summary": public_summary(row),
    } for label, row in zip(("no-pch", "original-pch"), rows)]
    evidence.record["compiler_storage_measurement"] = {
        "affected_case": "boot-v262145-s17-valid (expected illegal-capacity rejection)",
        "scope": "Same seed, source and input hashes, complete original scoreboard "
                 "and public-pin digest, plus a valid compact autonomous boot. "
                 "Sampled storage high-water marks are lower bounds, not exact peaks. "
                 "Aggregate L1 remains subject to independent review.",
        "measurements": measurements,
        "valid_boot_comparisons": valid["actual_comparisons"],
    }
    write_json(evidence.path / "compiler-storage-measurement.json",
               evidence.record["compiler_storage_measurement"])
    if any(row["compile_receipt"].get("storage_guard_error") for row in rows):
        raise VerificationFailure("Compiler storage guard fired; measurement is incomplete")
