"""Bounded storage/streaming repair diagnostics; never replace admitted checks."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retained import ROOT, Run, audit_streams
from simulation import cleanup_intermediates, stream_model


INTERRUPTED = Path("evidence/l1/l1-behavior-20261030T010810Z-e2a4ad77")
HISTORICAL_TOKEN = INTERRUPTED / (
    "children/verifier-token-fp-fp16-w0-c0-b1-s17-20261030T011017Z-bb91c5ec/receipt.json")


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def publish(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from strings(key)
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, str):
        yield value


def cleanup_interrupted(directory):
    # This one explicitly assigned, settled attempt is not a general evidence GC.
    settled_path = ROOT / ".vulcan/engineering/run-0001/attempt-0990/settled.json"
    settled = json.loads(settled_path.read_text())
    assert settled["id"] == 990 and settled["process_scope_settled"]
    assert settled["process_scope"]["scope"]["settled"]
    assert not settled["process_scope"]["scope"]["remaining"]
    assert settled["process_scope"]["exit_code"] == -9
    root = ROOT / INTERRUPTED
    files = sorted(p for p in root.rglob("*") if p.is_file())
    candidates = [p for p in files if p.suffix in (".o", ".a", ".gch")]
    observed_bytes = sum(p.stat().st_size for p in candidates)
    assert (len(candidates), observed_bytes) in ((0, 0), (45, 145657754)), (
        f"unexpected cleanup inventory: {len(candidates)} files / {observed_bytes} bytes")
    protected, parsed, empty = set(), [], []
    for path in files:
        if path.suffix != ".json":
            continue
        if not path.stat().st_size:
            empty.append(str(path.relative_to(ROOT)))
            continue
        data = json.loads(path.read_text())
        protected.update(strings(data))
        if path.name == "receipt.json":
            parsed.append(str(path.relative_to(ROOT)))
    assert len(parsed) == 120
    assert len([p for p in empty if p.endswith("/receipt.json")]) == 3
    assert str(INTERRUPTED / "failed-ledger.json") in empty
    inventory = []
    for path in candidates:
        info = path.lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1
        assert not path.is_symlink() and path.parent.name == "compile-obj"
        assert str(path.relative_to(ROOT)) not in protected and str(path) not in protected
        assert not path.parent.is_symlink()
        parent = path.parent.parent
        assert (parent / "compile-compiled.sv").is_file()
        assert (path.parent / "Vtb.mk").is_file()
        log = parent / "compile.stdout.txt"
        assert f"Entering directory '{path.parent}'" in log.read_text()
        inventory.append(dict(path=str(path.relative_to(ROOT)), bytes=info.st_size,
                              inode=info.st_ino, uid=info.st_uid, sha256=sha(path)))
    keep = {str(p.relative_to(ROOT)): sha(p) for p in files if p not in candidates}
    publish(directory / "cleanup-inventory.json", dict(
        settled_record_sha256=sha(settled_path), removed=inventory,
        preserved_sha256=keep, parseable_child_receipts=parsed, empty_json_files=empty,
        prior_failed_probe="evidence/preparation/storage-hygiene-cleanup-"
                           "20261030T012055Z-f89a9ead/receipt.json",
        inventory_status=("attributed-candidates" if candidates else
                          "already absent at inspection; no deletion by this probe; writer unknown"),
        authorization="Assigned cleanup of 45 settled attempt-0990 disposable intermediates only"))
    for row in inventory:
        path = ROOT / row["path"]
        info = path.lstat()
        assert (info.st_ino, info.st_uid, info.st_size) == (
            row["inode"], row["uid"], row["bytes"])
        assert sha(path) == row["sha256"]
        path.unlink()
    assert all(sha(ROOT / name) == expected for name, expected in keep.items())
    print(json.dumps(dict(removed_files=len(inventory),
                          removed_bytes=sum(row["bytes"] for row in inventory),
                          preserved_files=len(keep), parseable_receipts=120, empty_receipts=3)))


def fixtures(directory):
    objects = directory / "fixture-obj"
    objects.mkdir()
    run = SimpleNamespace(path=directory, receipt={}, relative=lambda p: str(p.relative_to(ROOT)))
    for name in ("Vtb.o", "Vtb.a", "Vtb.gch", "Vtb", "Vtb.cpp", "Vtb.h", "Vtb.mk", "raw.stdout.txt"):
        (objects / name).write_bytes(name.encode())
    preserved = {name: sha(objects / name) for name in
                 ("Vtb", "Vtb.cpp", "Vtb.h", "Vtb.mk", "raw.stdout.txt")}
    removed = cleanup_intermediates(run, objects, [objects / "Vtb"])
    assert len(removed) == 3 and not cleanup_intermediates(run, objects)
    assert all(sha(objects / name) == expected for name, expected in preserved.items())
    bound = objects / "receipt-bound.o"
    bound.write_bytes(b"must remain")
    run.receipt["artifact_sha256"] = {str(bound.relative_to(ROOT)): sha(bound)}
    try:
        cleanup_intermediates(run, objects)
    except AssertionError as exc:
        assert "receipt-bound" in str(exc)
    else:
        raise AssertionError("receipt-bound object was removed")
    assert bound.read_bytes() == b"must remain"
    other = directory / "symlink-obj"
    other.mkdir()
    (other / "unsafe.o").symlink_to(bound)
    try:
        cleanup_intermediates(run, other)
    except AssertionError as exc:
        assert "unattributed" in str(exc)
    else:
        raise AssertionError("symlink object was removed")
    publish(directory / "fixture-results.json", dict(
        removed=removed, preserved_sha256=preserved,
        receipt_bound_rejected=True, symlink_rejected=True, repeated_cleanup_idempotent=True))
    print("CLEANUP_FIXTURES_COMPARED 5")


def replay(run):
    from benchmark_checks import stage_intervals
    from token_checks import compare, compare_lines
    from transformer_reference import Geometry

    path = ROOT / HISTORICAL_TOKEN
    old = json.loads(path.read_text())
    hashes, errors = audit_streams(old["commands"])
    assert not errors and hashes == old["raw_stream_sha256"]
    for name, expected in old["source_sha256"].items():
        if name.startswith(("rtl/", "design/", "anvil_q2_reference/rtl/")):
            assert sha(ROOT / name) == expected, f"nonowned source changed: {name}"
    manifest = json.loads((path.parent / "manifest.json").read_text())
    record = json.loads((path.parent / "reference.json").read_text())
    reference = SimpleNamespace(
        g=Geometry(**manifest["geometry"]), stages=record["stages"],
        loads={}, writes={int(k, 16): [int(v, 16) for v in values]
                          for k, values in record["writes"].items()},
        logits=[tuple(x) for x in record["logits"]])
    memory = path.parent / "memory.hex"
    for line in memory.open():
        bits = int(line, 16)
        address = bits >> 32
        # Match the independent memory model, not the simulated mutable RAM.
        if (address >> 99) not in (8, 9, 10, 12, 13, 14, 15):
            reference.loads[address] = bits & 0xFFFFFFFF
    trace = path.parent / "simulation.stdout.txt"
    prior = compare(trace, reference, 1)
    for name, expected in old["metrics"].items():
        if name in prior:
            assert json.loads(json.dumps(prior[name])) == expected, (
                f"legacy comparison changed: {name}")
    assert prior["stage_final_ack_interval_cycles"] == stage_intervals(trace, record)
    model = (old.get("compiled_models", []) + old.get("reused_compiled_models", []))[0]
    assert sha(ROOT / model["binary"]) == model["binary_sha256"]
    run.command(["verilator", "--version"], "verilator-version")
    result = stream_model(
        run, [model["binary"], "+SEED=17", f"+MEMORY={memory.relative_to(ROOT)}"],
        lambda lines: compare_lines(lines, reference, 1), ("REQ ", "RSP "),
        ("COMMAND ", "REQ ", "RSP ", "LOGIT ", "DONE ", "TOKEN_COMPARED ", "BANK "))
    assert result == prior, "live stream metrics differ from retained transaction comparison"
    digest, count = hashlib.sha256(), 0
    prefixes = ("COMMAND ", "REQ ", "RSP ", "LOGIT ", "DONE ", "TOKEN_COMPARED ", "BANK ")
    with trace.open() as lines:
        for line in lines:
            if line.startswith(prefixes):
                digest.update(line.encode())
                count += 1
    checked = run.receipt["commands"][-1]["checked_stream"]
    assert checked["protocol_sha256"] == digest.hexdigest()
    assert checked["protocol_records"] == count
    assert (run.path / "simulation.stdout.txt").stat().st_size < 16384
    # Replay deliberate corruptions through the unchanged numerical/tag oracle.
    rejected = []
    for defect in ("write-data", "response-tag", "duplicate-tag", "missing-response"):
        changed = False
        def lines():
            nonlocal changed
            with trace.open() as source:
                for line in source:
                    parts = line.split()
                    if not changed and parts:
                        if defect == "write-data" and parts[0] == "REQ" and parts[3] == "1":
                            parts[5] = f"{int(parts[5], 16) ^ 1:08x}"
                        elif defect == "response-tag" and parts[0] == "RSP":
                            parts[3] = "ffffffffffffffff"
                        elif defect == "duplicate-tag" and parts[0] == "REQ":
                            changed = True
                            yield line
                            yield line
                            continue
                        elif defect == "missing-response" and parts[0] == "RSP":
                            changed = True
                            continue
                        else:
                            yield line
                            continue
                        changed = True
                        line = " ".join(parts) + "\n"
                    yield line
        try:
            compare_lines(lines(), reference, 1)
        except AssertionError as exc:
            assert changed
            rejected.append(dict(defect=defect, diagnostic=str(exc)))
        else:
            raise AssertionError(f"stream checker accepted {defect}")
    return dict(historical_receipt=str(HISTORICAL_TOKEN), metrics=result,
                identical_protocol_records=count, protocol_sha256=digest.hexdigest(),
                old_stdout_bytes=trace.stat().st_size,
                retained_stdout_bytes=(run.path / "simulation.stdout.txt").stat().st_size,
                corruptions_rejected=rejected)


def execute(action):
    run = Run("storage-hygiene-" + action, root="evidence/preparation")
    try:
        run.command(["python3", "--version"], "python-version")
        if action in ("cleanup", "fixtures"):
            output = run.command(
                ["python3", "tests/storage_hygiene_checks.py", "--worker", action,
                 "--directory", run.relative(run.path)], action)
            metrics = {"worker_output": output.read_text()}
        elif action == "replay":
            metrics = replay(run)
        else:
            cases = [("icarus", ["--simulator", "iverilog"]), ("compiled", []),
                     ("cached", ["--seed", "43"])]
            children = {}
            for label, extra in cases:
                output = run.command(
                    ["python3", "tests/token_checks.py", "--singleton", "--format", "fp16",
                     "--weights", "1", "--cache", "1", "--banks", "2", *extra], label,
                    environment={"ANVIL_EVIDENCE_ROOT": run.relative(run.path / "children"),
                                 "ANVIL_SIM_CACHE": run.relative(run.path / "compiled-models")})
                receipts = [line for line in output.read_text().splitlines()
                            if line.endswith("/receipt.json")]
                assert len(receipts) == 1
                child = json.loads((ROOT / receipts[0]).read_text())
                assert child["outcome"] == "passed-focused-only"
                children[label] = child
            streams = [next(c["checked_stream"] for c in children[k]["commands"]
                            if "checked_stream" in c) for k in ("icarus", "compiled")]
            assert streams[0]["protocol_sha256"] == streams[1]["protocol_sha256"]
            assert streams[0]["protocol_records"] == streams[1]["protocol_records"] > 0
            assert len(children["compiled"]["compiled_models"]) == 1
            assert len(children["cached"]["reused_compiled_models"]) == 1
            model = children["compiled"]["compiled_models"][0]
            assert model == children["cached"]["reused_compiled_models"][0]
            assert sha(ROOT / model["binary"]) == model["binary_sha256"]
            for name, expected in model["artifact_sha256"].items():
                assert sha(ROOT / name) == expected
            objects = (ROOT / model["binary"]).parent
            assert not any(p.suffix in (".o", ".a", ".gch") for p in objects.iterdir())
            removed = children["compiled"]["disposable_build_intermediates"]
            assert removed and all(not (ROOT / row["path"]).exists() for row in removed)
            assert list(objects.glob("*.cpp")) and list(objects.glob("*.h"))
            metrics = dict(identical_protocol_records=streams[0]["protocol_records"],
                           removed_files=len(removed),
                           removed_bytes=sum(row["bytes"] for row in removed),
                           cached_model_reused=True,
                           children={k: v["metrics"] for k, v in children.items()})
        run.finish("passed-focused-only", metrics=metrics,
                   limitations="Storage/streaming repair only; all mandatory checks and hardware gates remain.")
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError, KeyError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=("cleanup", "fixtures", "replay", "cache"))
    parser.add_argument("--worker", choices=("cleanup", "fixtures"))
    parser.add_argument("--directory")
    args = parser.parse_args()
    if args.worker:
        directory = (ROOT / args.directory).resolve()
        directory.relative_to(ROOT / "evidence/preparation")
        if args.worker == "cleanup":
            cleanup_interrupted(directory)
        else:
            fixtures(directory)
    else:
        assert args.action
        raise SystemExit(execute(args.action))
