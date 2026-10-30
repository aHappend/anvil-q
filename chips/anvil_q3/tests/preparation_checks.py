"""Offline preparation/boundary dispatch; never simulation or synthesis acceptance."""

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import asdict, replace
import io
import json
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Run
from parameters import defaults
from reference import Geometry


def compiler_candidate_dispatch_sensitivity():
    from contextlib import contextmanager
    import inspect
    import compiled_host_checks
    from compiled_build import build
    from decoder_checks import decoder_case
    from execution import ROOT
    from parameters import C
    from verify import behavior_inventory, shard_inventory

    assert inspect.signature(decoder_case).parameters["profile_compile"].default is False
    jobs = behavior_inventory()
    assert all(not job.kwargs.get("profile_compile", False) for job in jobs)
    selected = next(row for row in shard_inventory("evidence/check-c-four-token")["shards"]
                    if row["id"] == "decoder-36c0bbcad86b21431b7d")
    assert selected["argv"] == [
        "python3", "tests/verify.py", "--check", "behavior", "--behavior-shard",
        "decoder-36c0bbcad86b21431b7d", "--output",
        "evidence/check-c-four-token/decoder-36c0bbcad86b21431b7d"]
    for probe, profiled in (("C", False), ("C-symmetric", True)):
        fake_run = MagicMock()
        fake_run.rel.return_value = "offline-mocked-receipt"
        with (patch.object(sys, "argv", [
                  "tests/compiled_host_checks.py", "--probe", probe,
                  "--banks", "8", "--tokens", "4"]),
              patch.object(compiled_host_checks, "Run", return_value=fake_run),
              patch.object(compiled_host_checks, "decoder_case",
                           return_value={"scope": "offline mock only"}) as decoder,
              redirect_stdout(io.StringIO())):
            compiled_host_checks.main()
        assert decoder.call_args.kwargs["profile_compile"] is profiled
        assert decoder.call_args.kwargs["tokens"] == [1, 4, 2, 6]
        assert decoder.call_args.kwargs["prefill_tokens"] == 2
        assert decoder.call_args.args[1].INT4_ASYM == int(probe == "C")

    class OfflineBuild:
        path = ROOT / "evidence/preparation/offline-profile-0000"
        resources = {"build_jobs": 2}
        tool_versions = {}
        admitted = False

        def __init__(self):
            self.commands = []
            self.version_queries = []

        def rel(self, path):
            return str(path.relative_to(ROOT))

        def versions(self, argv):
            self.version_queries.extend(argv)

        def tool(self, argv):
            if argv[0] == "make":
                assert self.admitted, "compiler launched outside resource admission"
            self.commands.append(argv)

        @contextmanager
        def compiler_admission(self):
            self.admitted = True
            try:
                yield
            finally:
                self.admitted = False

    offline = OfflineBuild()
    build(offline, C, "pgo", True, True,
          compiler_flags=("-fprofile-use=../profiles", "-Werror=missing-profile",
                          "-Werror=coverage-mismatch"),
          sources=["rtl/anvil_q3_top.sv"])
    flags = offline.commands[0][offline.commands[0].index("-CFLAGS") + 1]
    assert "-fprofile-prefix-path=" + str(offline.path) in flags
    assert "-Werror=missing-profile" in flags and "-Werror=coverage-mismatch" in flags
    assert offline.version_queries == [("make", "--version")]
    assert len(offline.commands) == 2 and not offline.admitted
    return {"scope": "offline compiler dispatch only; no tool/DUT result",
            "admitted_workloads_unchanged": len(jobs),
            "candidate_default_disabled": True, "diagnostic_routes": 2,
            "isolated_command_preserved": True,
            "compiler_admission_and_profile_diagnostics_preserved": True}


def preparation_dispatch_sensitivity():
    import prepare
    import boundary_checks

    results = []
    for official in (False, True):
        for profile in ((3,) if not official else (1, 2, 3)):
            for banks in (1, 8):
                for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
                    if official and mode > profile - 1:
                        continue
                    argv = [
                        "tests/prepare.py", "--probe", "synthesis",
                        "--profile", str(profile), "--banks", str(banks),
                        "--mode", str(mode), "--asymmetric", str(asym),
                    ]
                    if official:
                        argv.append("--official-defaults")
                    expected = replace(
                        defaults(profile) if official else Geometry(),
                        BANKS=banks, CACHE_MODE=mode, INT4_ASYM=asym)
                    fake_run = MagicMock()
                    with (patch.object(sys, "argv", argv),
                          patch.object(prepare, "Run", return_value=fake_run),
                          patch.object(prepare, "synthesis_case", return_value={}) as synth,
                          redirect_stdout(io.StringIO())):
                        prepare.main()
                    synth.assert_called_once()
                    observed = synth.call_args.args[1]
                    if observed != expected:
                        raise AssertionError(
                            "synthesis preparation geometry mismatch: "
                            f"argv={argv!r}, expected={asdict(expected)!r}, "
                            f"observed={asdict(observed)!r}")
                    fake_run.finish.assert_called_once_with("passed", result={})
                    results.append({
                        "official_defaults": official, "geometry": asdict(observed),
                    })
                    expected_label = "official-default" if official else "bounded-A"
                    if synth.call_args.args[2] != expected_label:
                        raise AssertionError("synthesis preparation scope label mismatch")
    activation_cases = []
    for banks, capacity in ((1, 8), (2, 120), (4, 120), (8, 11008)):
        for simulator in ("iverilog", "verilator"):
            fake_run = MagicMock()
            with (patch.object(sys, "argv", [
                      "tests/prepare.py", "--probe", "activation-storage",
                      "--banks", str(banks), "--simulator", simulator]),
                  patch.object(prepare, "Run", return_value=fake_run),
                  patch.object(prepare, "activation_case", return_value={}) as activation,
                  redirect_stdout(io.StringIO())):
                prepare.main()
            activation.assert_called_once_with(fake_run, banks, simulator, capacity=capacity)
            fake_run.finish.assert_called_once_with("passed", result={})
            activation_cases.append({
                "banks": banks, "capacity": capacity, "simulator": simulator,
            })
    decoder_cases = []
    for profile in (1, 2, 3):
        for simulator in ("iverilog", "verilator"):
            for seed in (17, 89, 257):
                for controls in (None, (1, 8, 1), (16, 128, 8)):
                    argv = [
                        "tests/prepare.py", "--probe", "decoder",
                        "--profile", str(profile), "--simulator", simulator,
                        "--seed", str(seed), "--mode", str(profile - 1),
                        "--asymmetric", str(int(profile == 3)),
                    ]
                    depth, tile_k, rows = controls or (3, 24, 3)
                    if controls is not None:
                        argv.extend(["--queue-depth", str(depth), "--tile-k", str(tile_k),
                                     "--tile-rows", str(rows)])
                    expected = replace(
                        prepare.startup_geometry(profile), BANKS=8,
                        CACHE_MODE=profile - 1, INT4_ASYM=int(profile == 3),
                        QUEUE_DEPTH=depth, TILE_K=tile_k, TILE_ROWS=rows)
                    fake_run = MagicMock()
                    with (patch.object(sys, "argv", argv),
                          patch.object(prepare, "Run", return_value=fake_run),
                          patch.object(prepare, "decoder_case", return_value={}) as decoder,
                          redirect_stdout(io.StringIO())):
                        prepare.main()
                    decoder.assert_called_once()
                    observed = decoder.call_args.args[1]
                    if (observed != expected or
                            decoder.call_args.kwargs["simulator"] != simulator or
                            decoder.call_args.kwargs["seed"] != seed):
                        raise AssertionError(
                            "decoder preparation dispatch mismatch: "
                            f"argv={argv!r}, expected={asdict(expected)!r}, "
                            f"observed={asdict(observed)!r}")
                    fake_run.finish.assert_called_once_with("passed", result={})
                    decoder_cases.append({
                        "geometry": asdict(observed), "simulator": simulator, "seed": seed,
                        "explicit_controls": controls is not None,
                    })
    for probe in ("decoder", "dot8", "activation-storage"):
        with (patch.object(sys, "argv", [
                  "tests/prepare.py", "--probe", probe, "--official-defaults"]),
              patch.object(prepare, "Run") as constructor,
              redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO())):
            try:
                prepare.main()
            except SystemExit as exc:
                if exc.code != 2:
                    raise
            else:
                raise AssertionError("unsupported official-defaults flag silently accepted")
        constructor.assert_not_called()
    fake_run = MagicMock()
    with (patch.object(boundary_checks, "singleton_case", return_value={}) as singleton,
          patch.object(boundary_checks, "decoder_case", return_value={}) as decoder,
          patch.object(boundary_checks, "write_json")):
        boundary_checks.boundaries(fake_run)
    extrema_cases = [
        call for call in decoder.call_args_list
        if call.kwargs.get("label") == "queue-tile-maxima"
    ]
    expected_extrema = {
        (simulator, 8, 2, 1)
        for simulator in ("verilator",)
    }
    observed_extrema = []
    for call in extrema_cases:
        g = call.args[1]
        if (call.args[0] is not fake_run or
                g != replace(boundary_checks.A, BANKS=g.BANKS, CACHE_MODE=g.CACHE_MODE,
                             INT4_ASYM=g.INT4_ASYM,
                             QUEUE_DEPTH=16, TILE_K=128, TILE_ROWS=8) or
                call.kwargs["tokens"] != [1, 4, 2, 6, 3, 5, 7] or
                call.kwargs["prefill_tokens"] != 4):
            raise AssertionError("integrated queue/tile maxima dispatch changed")
        observed_extrema.append(
            (call.kwargs["simulator"], g.BANKS, g.CACHE_MODE, g.INT4_ASYM))
    if (len(observed_extrema) != len(expected_extrema) or
            set(observed_extrema) != expected_extrema or
            singleton.call_count != 16):
        raise AssertionError("incomplete minimum/maximum queue/tile dispatch")
    return {"dispatch_cases": results, "activation_dispatch_cases": activation_cases,
            "decoder_dispatch_cases": decoder_cases,
            "boundary_extrema_dispatch_cases": observed_extrema,
            "compiler_candidate": compiler_candidate_dispatch_sensitivity(),
            "unsupported_probes_rejected": 3,
            "scope": "offline mocked dispatch only; no synthesis or physical acceptance"}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        print(json.dumps(preparation_dispatch_sensitivity(), sort_keys=True))
        raise SystemExit(0)
    run = Run("evidence/preparation/independent-preparation-dispatch",
              "preparation geometry selection",
              repair_of=sys.argv[1] if len(sys.argv) > 1 else None)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        run.versions([("python3", "--version")])
        text, _ = run.tool(["python3", "tests/preparation_checks.py", "--worker"])
        result = json.loads(text)
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    run.finish("passed", result=result)
    print(json.dumps({"dispatch_cases": len(result["dispatch_cases"])}, sort_keys=True))
