"""Startup retention regressions; advisory, not parameter or RTL acceptance."""

import errno
import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compiler_admission_checks import admission_fixture, admission_sensitivity, assert_released
from execution import (BUILD_CLASS_RESERVES, DISK_FLOOR_BYTES, ROOT, Run, VERILATOR_UNROLL,
                       STARTUP_RETAIN_BYTES, sha256, write_json)


CAPACITY_FAILED_RECEIPT = "evidence/check-structure/20261030T140107Z-c15e3fa79f44/receipt.json"


def retention_sensitivity(run):
    """Mock compilers only: actual archive, restore, retention and admission code."""
    fixture = admission_fixture()
    fixture.path = run.path / "offline-fixture"
    fixture.path.mkdir()
    fixture.resources = {"build_jobs": 2}
    fixture.tool_versions = {"iverilog": {"fixture": "original"},
                             "verilator": {"fixture": "original"}}
    fixture.hashes = {"fixture-source": "original"}
    fixture.build_locks, fixture.builds, fixture.build_reuses = {}, {}, []
    fixture.transient_builds = {}
    source = fixture.path / "fixture.sv"
    source.write_text("synthetic original input\n")
    commands = []
    compiler_exit = 0
    simulation_exit = 0
    payload = b"synthetic executable fixture\n" * 32768

    def tool(argv, **kwargs):
        nonlocal compiler_exit, simulation_exit
        is_compiler = argv[0] in ("iverilog", "verilator")
        status = compiler_exit if is_compiler else simulation_exit
        folder = fixture.path / f"synthetic-tool-{len(commands):04d}"
        folder.mkdir()
        commands.append(list(argv))
        if is_compiler:
            output = Path(argv[argv.index("-o") + 1])
            if argv[0] == "verilator":
                output = Path(argv[argv.index("--Mdir") + 1]) / output
            binary = ROOT / output
            binary.parent.mkdir(parents=True, exist_ok=True)
            binary.write_bytes(payload)
        record = {"exit_code": status, "stdout": fixture.rel(folder / "stdout.txt"),
                  "stderr": fixture.rel(folder / "stderr.txt"),
                  "expected_exit_codes": list(kwargs["expected"]),
                  "process_scope_settled": True}
        (folder / "stdout.txt").write_text("synthetic tool fixture\n")
        (folder / "stderr.txt").write_text("")
        write_json(folder / "receipt.json", record)
        if status not in kwargs["expected"]:
            raise AssertionError("synthetic tool exit " + str(status))
        return "synthetic tool fixture", record

    def command(simulator, number):
        folder = fixture.path / f"build-{number:04d}"
        if simulator == "iverilog":
            binary = folder / "startup.vvp"
            argv = ["iverilog", "-o", fixture.rel(binary), fixture.rel(source)]
            simulation = ["vvp", fixture.rel(binary)]
            build_class = "icarus-startup"
        else:
            binary = folder / "obj/startup"
            argv = ["verilator", "--binary", "--Mdir", fixture.rel(binary.parent),
                    "-o", "startup", fixture.rel(source)]
            simulation = [fixture.rel(binary)]
            build_class = "verilator-startup"
        return argv, simulation, binary, build_class

    with (patch.object(fixture, "validate_live_sources"),
          patch("execution.shutil.disk_usage",
                return_value=SimpleNamespace(free=16 * 1024**3)),
          patch.object(fixture, "_tool", side_effect=tool)):
        fixture.plan_startup_storage(4)
        for simulator in ("iverilog", "verilator"):
            argv, simulation, binary, build_class = command(simulator, len(commands))
            fixture.tool(argv, build_class=build_class)
            assert_released(fixture)
            cached, _ = fixture.startup_executables[str(binary.resolve())]
            assert cached.name == "executable.gz" and cached.stat().st_size < len(payload) // 10
            assert gzip.decompress(cached.read_bytes()) == payload
            try:
                fixture.compact_startup(binary)
            except AssertionError as exc:
                assert "unexecuted startup" in str(exc)
            else:
                raise AssertionError("unexecuted startup was released")
            assert binary.read_bytes() == payload
            fixture.tool(simulation)
            fixture.compact_startup(binary)
            assert not binary.exists() and cached.is_file()
            before = len(commands)
            fixture.tool(argv, build_class=build_class)
            assert len(commands) == before, "compressed reuse launched compiler"
            assert binary.read_bytes() == payload
            fixture.tool(simulation)
            fixture.compact_startup(binary)
        assert fixture.startup_storage["remaining"] == 0
        assert len(fixture.build_reuses) == 2
        assert len(fixture.builds) == 2

        # A settled, asserted startup is recorded even if the future reserve falls.
        del fixture.startup_storage
        fixture.plan_startup_storage(488)
        argv, simulation, binary, build_class = command("verilator", len(commands))
        fixture.tool(argv, build_class=build_class)
        fixture.tool(simulation)
        required = (DISK_FLOOR_BYTES + BUILD_CLASS_RESERVES["verilator-startup"] +
                    487 * STARTUP_RETAIN_BYTES)
        with patch("execution.shutil.disk_usage",
                   return_value=SimpleNamespace(free=required - 1)):
            fixture.compact_startup(binary)
        assert not binary.exists() and fixture.startup_storage["remaining"] == 487
        saved = json.loads((fixture.path / "startup-storage.json").read_text())
        assert saved["available_bytes"] == required - 1
        assert len(saved["completed"]) == 1
        cached, _, _ = fixture.builds[next(reversed(fixture.builds))]
        fixture.validate_cached_build(cached)

        # Fresh compiler dispatch remains blocked until complete-matrix capacity returns.
        recovery_cases = []
        for scenario in ("recovers", "persistent-shortage", "cancelled", "compiler-failure"):
            argv, _, binary, build_class = command("verilator", len(commands))
            argv.insert(1, "-D" + scenario.replace("-", "_"))
            before = len(commands)
            samples = []

            def capacity(_):
                free = required if len(samples) >= 2 else required - 1
                if scenario in ("persistent-shortage", "cancelled"):
                    free = required - 1
                samples.append(free)
                if scenario == "cancelled":
                    fixture.cancelled.set()
                return SimpleNamespace(free=free)

            def admitted_tool(*args, **kwargs):
                assert samples[-1] >= kwargs["compiler_admission"]["required_bytes"]
                return tool(*args, **kwargs)

            compiler_exit = 255 if scenario == "compiler-failure" else 0
            with (patch("execution.shutil.disk_usage", side_effect=capacity),
                  patch("execution.CAPACITY_RECOVERY_SECONDS",
                        0 if scenario == "persistent-shortage" else 1),
                  patch("execution.CAPACITY_POLL_SECONDS", 0.001),
                  patch.object(fixture, "_tool", side_effect=admitted_tool)):
                try:
                    fixture.tool(argv, build_class=build_class)
                except OSError as exc:
                    assert scenario == "persistent-shortage" and exc.errno == errno.ENOSPC
                except RuntimeError as exc:
                    assert scenario == "cancelled" and "cancelled" in str(exc)
                except AssertionError as exc:
                    assert scenario == "compiler-failure" and "exit 255" in str(exc)
                else:
                    assert scenario == "recovers"
            assert len(commands) == before + int(scenario in ("recovers", "compiler-failure"))
            assert_released(fixture)
            assert fixture.startup_storage["remaining"] == 487
            recovery_cases.append({"scenario": scenario, "capacity_samples": samples,
                                   "compiler_launched": len(commands) > before,
                                   "reservations_released": True})
            fixture.cancelled.clear()
        compiler_exit = 0
        del fixture.startup_storage

        # A failed compile is never archived or reused, even if it leaves a binary.
        argv, simulation, binary, build_class = command("verilator", len(commands))
        argv.insert(1, "-DRETENTION_FAILURE_CASE")
        compiler_exit = 255
        before = len(fixture.builds)
        try:
            fixture.tool(argv, build_class=build_class)
        except AssertionError as exc:
            assert "exit 255" in str(exc)
        else:
            raise AssertionError("failed compiler was suppressed")
        assert binary.read_bytes() == payload and len(fixture.builds) == before
        assert_released(fixture)
        compiler_exit = 0
        fixture.tool(argv, build_class=build_class)
        simulation_exit = 1
        try:
            fixture.tool(simulation)
        except AssertionError:
            pass
        else:
            raise AssertionError("failed simulation was suppressed")
        assert binary.read_bytes() == payload
        assert str(binary.resolve()) not in getattr(fixture, "startup_simulations", {})
        # Negative parameter exits are compactable only after explicit caller validation.
        fixture.tool(simulation, expected=(0, 1))
        fixture.compact_startup(binary)
        simulation_exit = 0

        # Changed generated input, source inventory and tool identity force new builds.
        for change in ("source", "inventory", "tool"):
            if change == "source":
                source.write_text("synthetic changed input\n")
            elif change == "inventory":
                fixture.hashes = {"fixture-source": "changed"}
            else:
                fixture.tool_versions["verilator"] = {"fixture": "changed"}
            before = len(commands)
            fixture.tool(argv, build_class=build_class)
            assert len(commands) == before + 1
            fixture.tool(simulation)
            fixture.compact_startup(binary)

        # Archive corruption rejects reuse without launching another compiler.
        cached = fixture.builds[next(reversed(fixture.builds))][0]
        cached.write_bytes(cached.read_bytes() + b"deliberate synthetic corruption")
        before = len(commands)
        try:
            fixture.tool(argv, build_class=build_class)
        except AssertionError as exc:
            assert "identity changed" in str(exc)
        else:
            raise AssertionError("corrupt archive reused")
        assert len(commands) == before

    boundaries = []
    for delta in (-1, 0, 1):
        fixture = admission_fixture()
        fixture.path = run.path / f"capacity-{delta + 1}"
        fixture.path.mkdir()
        count = 488
        required = (DISK_FLOOR_BYTES + BUILD_CLASS_RESERVES["verilator-startup"] +
                    count * STARTUP_RETAIN_BYTES)
        with patch("execution.shutil.disk_usage",
                   return_value=SimpleNamespace(free=required + delta)):
            fixture.plan_startup_storage(count)
            with patch("execution.CAPACITY_RECOVERY_SECONDS", 0):
                try:
                    with fixture.compiler_admission("verilator-startup") as admission:
                        assert delta >= 0
                        assert admission["future_startup_retention_bytes"] == count * STARTUP_RETAIN_BYTES
                except OSError as exc:
                    assert delta < 0 and exc.errno == errno.ENOSPC
        assert_released(fixture)
        assert json.loads((fixture.path / "startup-storage.json").read_text())["remaining"] == count
        boundaries.append({"delta_bytes": delta, "admitted": delta >= 0})

    # Confirm the complete startup matrix is counted before any dispatch.
    from parameters import positive_cases, negative_cases, leaf_cases, baseline_geometries
    from structure_checks import structure
    class PreflightStop(Exception):
        pass
    fake = SimpleNamespace(plan_startup_storage=lambda count: (_ for _ in ()).throw(PreflightStop(count)))
    try:
        structure(fake)
    except PreflightStop as exc:
        full_count = exc.args[0]
    else:
        raise AssertionError("structure dispatched before complete matrix preflight")
    expected_count = 2 * (len(list(positive_cases())) + len(list(negative_cases())) +
                          len(list(leaf_cases())) + len(list(baseline_geometries())))
    assert full_count == expected_count == 488
    cleanup = admission_fixture()
    cleanup.path = run.path / "cleanup-ownership"
    cleanup.path.mkdir()
    cleanup.records = []
    for label, status, settled in (("completed", 0, True), ("failed", 1, True),
                                    ("live", None, False), ("unrecorded", 0, True)):
        directory = cleanup.path / label
        directory.mkdir()
        for name in ("model.o", "model.a", "model.gch", "executable.gz",
                     "receipt.json", "stdout.txt", "model.cpp", "startup"):
            (directory / name).write_text("synthetic retained identity: " + name)
        if label != "unrecorded":
            cleanup.records.append({"argv": ["verilator", "--Mdir", cleanup.rel(directory)],
                                    "cwd": ".", "exit_code": status,
                                    "process_scope_settled": settled})
    (cleanup.path / "completed/linked.o").symlink_to(cleanup.path / "failed/model.o")
    removed = cleanup.reclaim_settled_compiler_intermediates()
    assert {item["path"] for item in removed} == {
        cleanup.rel(cleanup.path / "completed" / name)
        for name in ("model.o", "model.a", "model.gch")}
    for label in ("failed", "live", "unrecorded"):
        assert len(list((cleanup.path / label).iterdir())) == 8
    assert (cleanup.path / "completed/linked.o").is_symlink()
    assert len(list((cleanup.path / "completed").iterdir())) == 6
    return {"scope": "synthetic driver regression; no RTL acceptance",
            "round_trips": 4, "compressed_reuses": 2,
            "compiler_failure_preserved": True, "simulation_failure_preserved": True,
            "source_inventory_tool_changes_recompile": True,
            "corrupt_archive_rejected": True, "matrix_executions": full_count,
            "capacity_boundaries": boundaries, "post_compaction_recovery": recovery_cases,
            "cleanup_scope": "only identified successful settled .o/.a/.gch; "
                             "failed/live/unrecorded files, symlinks and retained evidence preserved"}


def retained_binary_round_trips(run):
    """Execute copied, previously settled startup binaries before/after compression."""
    original = ROOT / CAPACITY_FAILED_RECEIPT
    original_run = original.parent
    saved = json.loads(original.read_text())
    assert saved["status"] == "failed"
    # This is archive/simulator usability evidence, never a new compilation claim.
    for name, digest in saved["source_hashes"].items():
        if name.startswith(("rtl/", "anvil_q2_reference/rtl/")):
            assert run.hashes[name] == digest, "retained binary RTL differs from current RTL"
    results = []
    completed = json.loads((original_run / "startup-storage.json").read_text())["completed"]
    for simulator, suffix in (("iverilog", "/startup.vvp"),
                              ("verilator", "/obj/startup")):
        retained = next(item for item in completed if item["executable"].endswith(suffix))
        archive_source = ROOT / retained["archive"]
        Run.validate_cached_build(archive_source)
        assert sha256(archive_source) == retained["archive_sha256"]
        original_simulation = json.loads((ROOT / retained["simulation_receipt"]).read_text())
        assert original_simulation["process_scope_settled"] is True
        assert original_simulation["exit_code"] == 0 and not original_simulation["timeout"]
        binary = run.path / ("round-trip-" + simulator)
        with gzip.open(archive_source, "rb") as stream, binary.open("wb") as target:
            shutil.copyfileobj(stream, target)
        binary.chmod(0o755)
        digest = sha256(binary)
        assert digest == retained["executable_sha256"]
        argv = ["vvp", run.rel(binary)] if simulator == "iverilog" else [run.rel(binary)]
        text, before = run.tool(argv)
        assert text.count("STARTUP_COMPLETE") == 1 and "PARAMETER ERROR" not in text
        archive = binary.with_suffix(".gz")
        with binary.open("rb") as stream, archive.open("wb") as target:
            with gzip.GzipFile(filename="", mode="wb", fileobj=target, mtime=0) as out:
                shutil.copyfileobj(stream, out)
        with gzip.open(archive, "rb") as stream, binary.open("wb") as target:
            shutil.copyfileobj(stream, target)
        assert sha256(binary) == digest
        after_text, after = run.tool(argv)
        assert after["exit_code"] == before["exit_code"] and after_text == text
        results.append({"simulator": simulator, "original_archive": run.rel(archive_source),
                        "original_simulation_receipt": retained["simulation_receipt"],
                        "executable_sha256": digest, "archive_sha256": sha256(archive),
                        "bytes": binary.stat().st_size, "archive_bytes": archive.stat().st_size,
                        "before": before["stdout"], "after": after["stdout"],
                        "scope": "retained startup binary archive round trip, not fresh compilation"})
    return results


def cold_startup_round_trips(run):
    """Fresh positive/negative compilation, assertion, compaction and cached reuse."""
    from parameters import A
    from structure_checks import sv_literal

    run.plan_startup_storage(8)
    rtl = [run.rel(path) for path in sorted((ROOT / "rtl").glob("*.sv"))]
    results = []
    for label, geometry, expected in (("positive", A, True),
                                      ("negative", replace(A, BANKS=3), False)):
        folder = run.path / label
        folder.mkdir()
        tb = folder / "startup.sv"
        overrides = ",".join(f".{key}({sv_literal(value)})"
                             for key, value in asdict(geometry).items())
        tb.write_text(
            "`timescale 1ns/1ps\nmodule parameter_startup;\n"
            f"anvil_q3_top #({overrides}) accelerator "
            "(.clk(1'b0),.rst_n(1'b0),.cancel(1'b0),.token_valid(1'b0));\n"
            'initial begin #10; $display("STARTUP_COMPLETE"); $finish; end\nendmodule\n')
        for simulator in ("iverilog", "verilator"):
            if simulator == "iverilog":
                binary = folder / "startup.vvp"
                compile_argv = ["iverilog", "-g2012", "-Wall", "-s", "parameter_startup",
                                "-o", run.rel(binary), *rtl, run.rel(tb)]
                simulation = ["vvp", run.rel(binary)]
                build_class = "icarus-startup"
            else:
                obj = folder / "obj"
                binary = obj / "startup"
                compile_argv = ["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                                *VERILATOR_UNROLL, "--top-module", "parameter_startup",
                                "--Mdir", run.rel(obj), "-o", "startup", *rtl, run.rel(tb)]
                simulation = [run.rel(binary)]
                build_class = "verilator-startup"
            for iteration in range(2):
                allocated_before = sum(path.stat().st_blocks * 512
                                       for path in run.path.rglob("*") if path.is_file())
                executions = len(run.records)
                if label == "positive" and simulator == "verilator" and iteration == 0:
                    disk_usage = shutil.disk_usage
                    samples = []

                    def recovering_capacity(path):
                        actual = disk_usage(path)
                        required = (DISK_FLOOR_BYTES + BUILD_CLASS_RESERVES["verilator-startup"] +
                                    run.startup_storage["remaining"] * STARTUP_RETAIN_BYTES)
                        free = required - 1 if len(samples) < 2 else actual.free
                        samples.append(free)
                        return SimpleNamespace(free=free)

                    with patch("execution.shutil.disk_usage", side_effect=recovering_capacity):
                        _, compile_record = run.tool(compile_argv, build_class=build_class)
                    assert len(samples) >= 3
                    assert samples[0] < compile_record["compiler_admission"]["required_bytes"]
                    assert compile_record["compiler_admission"]["capacity_wait_seconds"] > 0
                else:
                    _, compile_record = run.tool(compile_argv, build_class=build_class)
                assert len(run.records) == executions + int(iteration == 0)
                assert compile_record["exit_code"] == 0
                if simulator == "verilator":
                    assert compile_record["argv"][1:3] == ["-j", "1"]
                digest = sha256(binary)
                text, record = run.tool(
                    simulation, expected=(0,) if expected else tuple(range(-128, 129)))
                if expected:
                    assert text.count("STARTUP_COMPLETE") == 1 and "PARAMETER ERROR" not in text
                else:
                    assert record["exit_code"] != 0 and "PARAMETER ERROR" in text
                if not results:
                    with patch("execution.shutil.disk_usage",
                               return_value=SimpleNamespace(free=DISK_FLOOR_BYTES)):
                        run.compact_startup(binary)
                    assert run.startup_storage["available_bytes"] < run.startup_storage["required_bytes"]
                else:
                    run.compact_startup(binary)
                assert not binary.exists() and not run.compiler_admissions
                retained_delta = (sum(path.stat().st_blocks * 512
                                      for path in run.path.rglob("*") if path.is_file()) -
                                  allocated_before)
                assert 0 <= retained_delta <= STARTUP_RETAIN_BYTES
                results.append({
                    "label": label, "simulator": simulator, "cache_reuse": bool(iteration),
                    "parameters": asdict(geometry), "executable_sha256": digest,
                    "compile_receipt": str(Path(compile_record["stdout"]).parent / "receipt.json"),
                    "simulation_receipt": str(Path(record["stdout"]).parent / "receipt.json"),
                    "observed_exit": record["exit_code"],
                    "retained_allocated_delta_bytes": retained_delta,
                    "scope": "bounded startup/retention diagnostic, not structure matrix acceptance"})
                write_json(run.path / "cold-startup-results.json", results)
    assert len(run.builds) == 4 and len(run.build_reuses) == 4
    assert run.startup_storage["remaining"] == 0
    assert all(cached.suffix == ".gz" for cached, _, _ in run.builds.values())
    return results


def main():
    if sys.argv[1:] == ["--worker"]:
        raise ValueError("--worker requires an output directory")
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        holder = SimpleNamespace(path=ROOT / sys.argv[2])
        holder.path.mkdir()
        print(json.dumps({"admission": admission_sensitivity(),
                          "retention": retention_sensitivity(holder)}, sort_keys=True))
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--repair-of", default=CAPACITY_FAILED_RECEIPT)
    args = parser.parse_args()
    output = ("evidence/preparation/startup-capacity-recovery-" +
              datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    run = Run(output,
              "compact future startup build retention", repair_of=args.repair_of)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        run.versions([("python3", "--version"), ("iverilog", "-V"), ("vvp", "-V"),
                      ("verilator", "--version"), ("g++", "--version"), ("make", "--version")])
        text, _ = run.tool(["python3", "tests/startup_retention_checks.py",
                            "--worker", run.rel(run.path / "regressions")])
        result = {"original_failure": CAPACITY_FAILED_RECEIPT, "regressions": json.loads(text),
                  "retained_binary_round_trips": retained_binary_round_trips(run),
                  "cold_startup_round_trips": cold_startup_round_trips(run)}
        from parameters import positive_cases, negative_cases, leaf_cases, baseline_geometries
        count = 2 * (len(list(positive_cases())) + len(list(negative_cases())) +
                     len(list(leaf_cases())) + len(list(baseline_geometries())))
        capacity = Run.__new__(Run)
        capacity.path = run.path / "next-structure-capacity"
        capacity.path.mkdir()
        capacity.plan_startup_storage(count)
        result["next_structure_dispatch"] = {
            "capacity_observation_only": True, "compiler_admission_required": True,
            "capacity_available": capacity.check_startup_storage()}
        run.finish("passed", result=result)
    except BaseException as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
