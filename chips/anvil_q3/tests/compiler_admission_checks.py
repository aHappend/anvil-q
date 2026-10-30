"""Bounded compiler-storage diagnostics; not functional RTL acceptance."""

from dataclasses import asdict, replace
import errno
import json
import os
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import (BUILD_CLASS_RESERVES, DISK_FLOOR_BYTES, ROOT, Run,
                       VERILATOR_UNROLL, write_json)
from parameters import A, C, defaults


FAILED_RECEIPT = "evidence/check-structure/20261030T131046Z-7dc7878092a2/receipt.json"


def admission_fixture(slots=2):
    run = Run.__new__(Run)
    run.path = ROOT / "evidence/preparation/offline-admission-0000"
    run.lock = threading.RLock()
    run.compiler_slots = threading.BoundedSemaphore(slots)
    run.compiler_admissions = {}
    run.cancelled = threading.Event()
    return run


def assert_released(run, slots=2):
    assert not run.compiler_admissions
    for _ in range(slots):
        assert run.compiler_slots.acquire(blocking=False)
    assert not run.compiler_slots.acquire(blocking=False)
    for _ in range(slots):
        run.compiler_slots.release()


def admission_sensitivity():
    """Mock filesystem capacity only; exercise the actual admission and caller."""
    boundaries = []
    for build_class, reserve in BUILD_CLASS_RESERVES.items():
        for delta in (-1, 0, 1):
            run = admission_fixture()
            free = DISK_FLOOR_BYTES + reserve + delta
            with patch("execution.shutil.disk_usage", return_value=SimpleNamespace(free=free)):
                try:
                    with run.compiler_admission(build_class) as admission:
                        assert delta >= 0
                        assert admission["build_class"] == build_class
                        assert admission["build_reserve_bytes"] == reserve
                        assert list(run.compiler_admissions.values()) == [reserve]
                except OSError as exc:
                    assert delta == -1 and exc.errno == errno.ENOSPC
                else:
                    assert delta >= 0
            assert_released(run)
            boundaries.append({"class": build_class, "boundary_delta_bytes": delta,
                               "admitted": delta >= 0})

    small = BUILD_CLASS_RESERVES["icarus-startup"]
    run = admission_fixture()
    with patch("execution.shutil.disk_usage",
               return_value=SimpleNamespace(free=DISK_FLOOR_BYTES + 2 * small)):
        with run.compiler_admission("icarus-startup"):
            with run.compiler_admission("icarus-startup") as admission:
                assert admission["other_build_reserves_bytes"] == small
                assert sum(run.compiler_admissions.values()) == 2 * small
    assert_released(run)

    # One byte short for a simultaneous large build: wait, then admit on release.
    run = admission_fixture()
    attempted, entered = threading.Event(), threading.Event()
    errors = []
    observed = []
    free = DISK_FLOOR_BYTES + BUILD_CLASS_RESERVES["default"] + small - 1

    def capacity(_):
        if threading.current_thread() is not threading.main_thread():
            attempted.set()
        return SimpleNamespace(free=free)

    def contender():
        try:
            with run.compiler_admission() as admission:
                observed.append(admission)
                entered.set()
        except BaseException as exc:
            errors.append(exc)

    with patch("execution.shutil.disk_usage", side_effect=capacity):
        with run.compiler_admission("icarus-startup"):
            thread = threading.Thread(target=contender)
            thread.start()
            assert attempted.wait(5)
            with run.lock:
                assert not entered.is_set()
                assert list(run.compiler_admissions.values()) == [small]
        thread.join(5)
        assert not thread.is_alive() and not errors and entered.is_set()
        assert observed[0]["other_build_reserves_bytes"] == 0
    assert_released(run)

    for waiting_on_slot in (False, True):
        run = admission_fixture(slots=1 if waiting_on_slot else 2)
        attempted.clear()
        errors.clear()
        with patch("execution.shutil.disk_usage",
                   return_value=SimpleNamespace(free=DISK_FLOOR_BYTES + small)):
            with run.compiler_admission("icarus-startup"):
                thread = threading.Thread(target=contender)
                thread.start()
                run.cancelled.set()
                thread.join(5)
                assert not thread.is_alive()
                assert len(errors) == 1 and isinstance(errors[0], RuntimeError)
                assert list(run.compiler_admissions.values()) == [small]
        assert_released(run, slots=1 if waiting_on_slot else 2)

    for failure in ("filesystem", "compiler"):
        run = admission_fixture()
        try:
            if failure == "filesystem":
                with patch("execution.shutil.disk_usage",
                           side_effect=OSError(errno.ENOSPC, "injected capacity failure")):
                    with run.compiler_admission("icarus-startup"):
                        raise AssertionError("filesystem error suppressed")
            else:
                with patch("execution.shutil.disk_usage",
                           return_value=SimpleNamespace(free=DISK_FLOOR_BYTES + small)):
                    with run.compiler_admission("icarus-startup"):
                        raise OSError(errno.ENOSPC, "injected compiler write failure")
        except OSError as exc:
            assert exc.errno == errno.ENOSPC
        else:
            raise AssertionError("disk-full error suppressed")
        assert_released(run)

    # Exercise tool -> _build -> admission, not merely the context manager API.
    for build_class in BUILD_CLASS_RESERVES:
        run = admission_fixture()
        run.resources = {"build_jobs": 2}
        compiler = "verilator" if build_class == "verilator-startup" else "iverilog"
        run.tool_versions = {compiler: {"available": True}}
        run.hashes = {}
        run.build_locks = {}
        run.builds = {}
        reserve = BUILD_CLASS_RESERVES[build_class]
        with (patch.object(run, "validate_live_sources"),
              patch("execution.shutil.disk_usage",
                    return_value=SimpleNamespace(free=DISK_FLOOR_BYTES + reserve)),
              patch.object(run, "_tool",
                           side_effect=OSError(errno.ENOSPC, "injected compiler failure")) as tool):
            try:
                argv = ([compiler, "--binary", "--Mdir", str(run.path / "obj"),
                         "-o", "failed"] if compiler == "verilator" else
                        [compiler, "-o", str(run.path / "failed.vvp")])
                run.tool(argv, build_class=build_class)
            except OSError as exc:
                assert exc.errno == errno.ENOSPC
            else:
                raise AssertionError("compiler failure suppressed")
            assert tool.call_args.kwargs["compiler_admission"]["build_class"] == build_class
            assert tool.call_args.kwargs["compiler_admission"]["build_reserve_bytes"] == reserve
        assert_released(run)

    run = admission_fixture()
    for argv, build_class in ((["iverilog", "-o", "unused"], "unknown"),
                              (["verilator", "--binary", "-o", "unused"], "icarus-startup"),
                              (["iverilog", "-o", "unused"], "verilator-startup"),
                              (["vvp", "unused"], "icarus-startup")):
        try:
            run.tool(argv, build_class=build_class)
        except ValueError:
            pass
        else:
            raise AssertionError("unsupported build-class use accepted")
    assert_released(run)
    return {"scope": "offline capacity/caller regression, not DUT acceptance",
            "boundaries": boundaries, "concurrent_reservation_sum_checked": True,
            "mixed_class_wait_and_release_checked": True,
            "cancellation_wait_paths": 2, "disk_full_release_paths": 5,
            "unknown_or_misapplied_classes_rejected": 4,
            "unmeasured_default_bytes": BUILD_CLASS_RESERVES["default"]}


def measure_startup(run, simulator="iverilog"):
    from structure_checks import sv_literal

    results = []
    sources = [run.rel(p) for p in sorted((ROOT / "rtl").glob("*.sv"))]
    cases = [("compact-A", "anvil_q3_top", asdict(A), sources),
             ("C-b1", "anvil_q3_top", asdict(replace(C, BANKS=1)), sources),
             ("C-b8", "anvil_q3_top", asdict(C), sources)]
    cases += [(f"default-p{profile}", "anvil_q3_top", asdict(defaults(profile)), sources)
              for profile in (1, 2, 3)]
    parent_sources = [run.rel(p) for p in sorted((ROOT / "anvil_q2_reference/rtl").glob("*.sv"))]
    from parameters import baseline_geometries
    for implementation, g in baseline_geometries():
        if g.BANKS != 4:
            continue
        p = {key: value for key, value in asdict(g).items()
             if key not in ("PROFILE", "INT4_ASYM", "TILE_K", "TILE_ROWS")}
        p["COMPAT_Q1"] = int(g.PROFILE == 1)
        cases.append((f"supplied-{implementation}-m{g.CACHE_MODE}", "anvil_q2_top",
                      p, parent_sources))
    from parameters import leaf_cases
    cases += [(f"leaf-{number}", module, p, sources)
              for number, (module, p, legal) in enumerate(leaf_cases())
              if legal and (module in ("anvil_q3_rmsnorm", "anvil_q3_rope") or
                            p.get("BANKS") == 8 and
                            (p.get("QUEUE_DEPTH") == 16 or
                             (p.get("TILE_K"), p.get("TILE_ROWS")) == (128, 8)))]
    if simulator == "verilator":
        cases = [case for case in cases if case[0] in
                 ("compact-A", "C-b8", "default-p3", "supplied-q2-m1", "leaf-49")]
    for label, module, geometry, rtl in cases:
        folder = run.path / label
        folder.mkdir()
        temporary = folder / "temporary"
        temporary.mkdir()
        parameters = ",".join(f".{key}({sv_literal(value)})"
                              for key, value in geometry.items())
        tb = folder / "startup.sv"
        connections = (".clk(1'b0),.rst_n(1'b0),.cancel(1'b0),.token_valid(1'b0)"
                       if module in ("anvil_q3_top", "anvil_q2_top") else
                       ".clk(1'b0),.rst_n(1'b0),.flush(1'b0)")
        tb.write_text(
            "`timescale 1ns/1ps\nmodule parameter_startup;\n"
            f"{module} #({parameters}) accelerator ({connections});\n"
            'initial begin #10; $display("STARTUP_COMPLETE"); $finish; end\nendmodule\n')
        stop = threading.Event()
        samples = []

        def sample():
            while True:
                allocated = 0
                for path in folder.rglob("*"):
                    try:
                        if path.is_file():
                            allocated += path.stat().st_blocks * 512
                    except FileNotFoundError:
                        # Compiler-owned temporary files may disappear between samples.
                        continue
                samples.append(allocated)
                if stop.wait(0.005):
                    return

        monitor = threading.Thread(target=sample)
        monitor.start()
        try:
            with patch.dict(os.environ, {"TMPDIR": str(temporary)}):
                if simulator == "iverilog":
                    executable = folder / "startup.vvp"
                    _, receipt = run.tool([
                        "iverilog", "-g2012", "-Wall", "-s", "parameter_startup",
                        "-o", run.rel(executable), *rtl, run.rel(tb)],
                        build_class="icarus-startup")
                    command = ["vvp", run.rel(executable)]
                else:
                    obj = folder / "obj"
                    executable = obj / "startup"
                    _, receipt = run.tool([
                        "verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                        *VERILATOR_UNROLL, "--top-module", "parameter_startup",
                        "--Mdir", run.rel(obj), "-o", "startup", *rtl, run.rel(tb)],
                        build_class="verilator-startup")
                    command = [run.rel(executable)]
        finally:
            stop.set()
            monitor.join()
        text, simulation = run.tool(command)
        assert text.count("STARTUP_COMPLETE") == 1 and "PARAMETER ERROR" not in text
        result = {
            "label": label, "module": module, "parameters": geometry, "simulator": simulator,
            "compile_receipt": str(Path(receipt["stdout"]).parent / "receipt.json"),
            "startup_receipt": str(Path(simulation["stdout"]).parent / "receipt.json"),
            "tmpdir": run.rel(temporary), "sample_interval_seconds": 0.005,
            "sample_count": len(samples), "sampled_max_allocated_bytes": max(samples),
            "retained_executable_bytes": executable.stat().st_size,
            "measurement_limit": "sampled storage, not a guaranteed transient peak",
        }
        build_class = "icarus-startup" if simulator == "iverilog" else "verilator-startup"
        result["build_reserve_bytes"] = BUILD_CLASS_RESERVES[build_class]
        result["sampled_margin_after_executable_copy_bytes"] = (
            BUILD_CLASS_RESERVES[build_class] - max(samples) - executable.stat().st_size)
        assert result["sampled_margin_after_executable_copy_bytes"] > 0
        results.append(result)
        write_json(run.path / "storage-measurements.json", results)
    return results


def main():
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(admission_sensitivity(), sort_keys=True))
        return
    run = Run("evidence/preparation/compiler-admission",
              "bounded startup compiler storage measurement",
              repair_of="evidence/preparation/compiler-admission/"
                        "20261030T131912Z-217bbd01b25c/receipt.json")
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        simulator = "verilator" if sys.argv[1:] == ["--verilator"] else "iverilog"
        run.versions([("python3", "--version"), ("iverilog", "-V"), ("vvp", "-V"),
                      ("verilator", "--version"), ("g++", "--version"), ("make", "--version")])
        text, _ = run.tool(["python3", "tests/compiler_admission_checks.py", "--worker"])
        result = {"regression": json.loads(text), "measurements": measure_startup(run, simulator),
                  "original_failure": FAILED_RECEIPT}
        run.finish("passed", result=result)
    except BaseException as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
