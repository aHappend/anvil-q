"""Independent fixtures for bounded interactive transaction checking and retention."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run
from simulation import stream_model
from stream_retention_checks import reopen


COUNT = 8192
WORKER = r"""
import sys
action, count = sys.argv[1], int(sys.argv[2])
print("FRAME_READY 0", flush=True)
assert input() == "actual-feedback"
for index in range(count):
    data = index ^ (1 if action == "corrupted" and index == 4096 else 0)
    print(f"MEM_REQ {index} {data:08x}")
    if action == "truncated" and index == 4096:
        sys.exit(0)
    print(f"MEM_RSP {index} {index:08x}")
print(f"FRAME_DONE {count}", flush=True)
"""


def fixtures():
    run = Run("attention-bounded-stream-fixtures")
    try:
        run.command(["python3", "--version"], "python-version")
        results = []
        for action in ("healthy", "corrupted", "truncated"):
            child = Run(f"attention-stream-{action}", root=run.relative(run.path / "children"))
            accepted = retired = 0
            summary = False

            def checker(process, lines):
                nonlocal accepted, retired, summary
                assert next(lines) == "FRAME_READY 0\n"
                process.stdin.write("actual-feedback\n")
                process.stdin.flush()
                for line in lines:
                    fields = line.split()
                    if fields[0] == "MEM_REQ":
                        assert accepted == retired
                        assert int(fields[1]) == accepted
                        assert int(fields[2], 16) == accepted, "fixture transaction data mismatch"
                        accepted += 1
                    elif fields[0] == "MEM_RSP":
                        assert accepted == retired + 1
                        assert int(fields[1]) == int(fields[2], 16) == retired
                        retired += 1
                    else:
                        assert line == f"FRAME_DONE {COUNT}\n"
                        assert accepted == retired == COUNT
                        assert not summary
                        summary = True
                assert summary and accepted == retired == COUNT, "fixture incomplete transaction stream"

            try:
                stream_model(
                    child, ["python3", "-c", WORKER, action, str(COUNT)], checker,
                    ("MEM_REQ ", "MEM_RSP "), ("MEM_REQ ", "MEM_RSP "),
                    interactive_feedback=True)
            except AssertionError as exc:
                assert action != "healthy", str(exc)
                expected = ("transaction data mismatch" if action == "corrupted"
                            else "incomplete transaction stream")
                assert expected in str(exc), str(exc)
                child.finish("failed", expected_fixture_rejection=True, failure=str(exc))
                text = (child.path / "simulation.stdout.txt").read_text()
                assert "STREAM_FAILURE_WINDOW_BEGIN" in text
                assert len(text.encode()) < 8192
                results.append(dict(action=action, rejected=True,
                                    receipt=child.relative(child.path / "receipt.json")))
            else:
                assert action == "healthy", "corruption/truncation was not rejected"
                command = child.receipt["commands"][-1]
                expected_stream = "FRAME_READY 0\n" + "".join(
                    f"MEM_REQ {i} {i:08x}\nMEM_RSP {i} {i:08x}\n" for i in range(COUNT))
                expected_stream += f"FRAME_DONE {COUNT}\n"
                protocol = "".join(
                    f"MEM_REQ {i} {i:08x}\nMEM_RSP {i} {i:08x}\n" for i in range(COUNT))
                checked = command["checked_stream"]
                assert checked["sha256"] == hashlib.sha256(expected_stream.encode()).hexdigest()
                assert checked["protocol_sha256"] == hashlib.sha256(protocol.encode()).hexdigest()
                assert checked["bytes"] == len(expected_stream.encode())
                assert checked["lines"] == 2 * COUNT + 2
                assert checked["protocol_records"] == 2 * COUNT
                assert checked["discarded_transaction_counts"] == dict(MEM_REQ=COUNT, MEM_RSP=COUNT)
                text = (ROOT / command["stdout"]).read_text()
                assert "\nMEM_REQ " not in text and "\nMEM_RSP " not in text
                assert len(text.encode()) < 8192
                child.finish("passed-focused-only", compared_transactions=COUNT)
                results.append(dict(action=action, rejected=False,
                                    receipt=child.relative(child.path / "receipt.json")))
            command = child.receipt["commands"][-1]
            assert command["capture_reopen"]["exit_code"] == 0
            assert not command["timed_out"] and command["exit_code"] is not None
            run.command(["python3", "tests/stream_retention_checks.py", "--action", "reopen",
                         "--path", results[-1]["receipt"]], f"{action}-independent-reopen")
        run.finish("passed-focused-only", fixtures=results,
                   limitations="Synthetic checker fixtures, not RTL conformance or deletion attribution.")
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        return 1


def probe(repair_of=None):
    run = Run("attention-bounded-stream-recovery")
    run.receipt["repair_of"] = repair_of or (
        "evidence/l1/l1-benchmark-20261030T034007Z-2c2538b6/receipt.json")
    try:
        run.command(["python3", "--version"], "python-version")
        environment = {"ANVIL_EVIDENCE_ROOT": run.relative(run.path / "children"),
                       "ANVIL_SIM_CACHE": run.relative(run.path / "compiled-models")}
        run.command(["python3", "tests/attention_stream_checks.py"], "fixtures",
                    environment=environment)
        output = run.command(
            ["python3", "tests/attention_checks.py", "--seed", "17", "--reduced"],
            "reduced-attention", environment=environment)
        names = [line for line in output.read_text().splitlines() if line.endswith("/receipt.json")]
        assert len(names) == 1
        child = reopen(names[0])
        assert child["outcome"] == "passed-focused-only"
        assert child["source_sha256"] == run.receipt["source_sha256"]
        simulations = [c for c in child["commands"] if c.get("live_stimulus")]
        assert len(simulations) == 2
        for mode, command in enumerate(simulations):
            metrics = child["metrics"][f"mode{mode}"]
            checked = command["checked_stream"]
            assert metrics["frames_compared"] == 9
            assert metrics["attention_values_compared"] == 432
            assert metrics["memory_requests"] == metrics["memory_responses"] > 0
            assert checked["discarded_transaction_counts"] == {
                "MEM_REQ": metrics["memory_requests"], "MEM_RSP": metrics["memory_responses"]}
            assert checked["protocol_records"] == (
                metrics["memory_requests"] + metrics["memory_responses"]
                + 3 * metrics["frames_compared"] + 1)
            assert command["capture_reopen"]["exit_code"] == 0
            assert command["exit_code"] == 0 and not command["timed_out"]
            text = (ROOT / command["stdout"]).read_text()
            assert "\nMEM_REQ " not in text and "\nMEM_RSP " not in text
            assert len(text.encode()) < 16384
        for name, digest in child["mode0_retention_after_mode1"].items():
            assert child["raw_stream_sha256"][name] == digest
        run.command(["python3", "tests/stream_retention_checks.py", "--action", "reopen",
                     "--path", names[0]], "independent-final-reopen")
        run.finish("passed-focused-only", child_receipt=names[0], metrics=child["metrics"],
                   limitations="Reduced seed-17 RTL and stream fixtures only; no deletion attribution, "
                                "full benchmark, timing, hardware or historical-lineage pass.")
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError, KeyError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    raise SystemExit(probe(args.repair_of) if args.probe else fixtures())
