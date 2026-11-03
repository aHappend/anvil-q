#!/usr/bin/env python3
"""Compact executed regressions for attempt-714 stimulus/trace integrity."""

import errno
import argparse
import gzip
import io
import json
import resource
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify
from architecture import CONFIGURATIONS
from operators import OperatorReference, compare_operator
from operator_storage import (CheckedSink, RequestWriter, export_text, file_hash,
                              inspect_requests, publication, REQUEST_MAGIC,
                              REQUEST_RECORD, MAX_COMPRESSED_BYTES, RESERVE_BYTES)

FAILURES = (
    "evidence/preparation/verifier-l1-rxe27sl2/receipt.json",
    "evidence/preparation/verifier-production-gemv4-mode1-wkrl2h8z/receipt.json",
    "evidence/preparation/verifier-operator-storage-d2go51td/receipt.json",
    "evidence/preparation/verifier-operator-storage-ruc96al5/receipt.json",
)


def rejects(ev, name, function, errors, message):
    diagnostic = ""
    try:
        function()
    except errors as error:
        diagnostic = str(error)
    return ev.assertion(name, bool(diagnostic) and message in diagnostic,
                        diagnostic=diagnostic)


def check(ev):
    soft, hard = resource.getrlimit(resource.RLIMIT_CORE)
    if soft != 0:
        resource.setrlimit(resource.RLIMIT_CORE, (0, hard))
    good = True
    for path in FAILURES:
        prior = verify.ROOT / path
        if prior.is_file():
            ev.receipt.setdefault("diagnostic_repairs", []).append(
                {"path": path, "sha256": verify.digest(prior)})
    class ShortSink(io.BytesIO):
        def write(self, data):
            super().write(data[:-1])
            return len(data)-1

    class FullSink(io.BytesIO):
        def write(self, data):
            raise OSError(errno.ENOSPC, "injected no space left on device")

    for name, sink, text in (
        ("short_input_write", ShortSink(), "short operator input write"),
        ("input_storage_full", FullSink(), "no space left"),
    ):
        good = rejects(ev, name, lambda: CheckedSink(sink).write(b"12345678"),
                       OSError, text) and good
        (ev.path / (name+".partial")).write_bytes(sink.getvalue())
    good = rejects(ev, "bounded_input_storage",
                   lambda: CheckedSink(io.BytesIO(), limit=7).write(b"12345678"),
                   OSError, "budget exhausted") and good
    with open("/dev/full", "wb", buffering=0) as full:
        good = rejects(ev, "executed_input_storage_full",
                       lambda: CheckedSink(full).write(b"12345678"),
                       OSError, "No space left on device") and good
    good = ev.run("version-c++", ["c++", "--version"], timeout=30) and good

    fixture = ev.path / "operator-io-fixture"
    compiled = ev.run("io-fixture-compile", [
        "c++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
        "tests/operator_io_fixture.cpp", "-lz", "-o",
        str(fixture.relative_to(verify.ROOT))])
    good = ev.assertion("io_fixture_compiled", compiled) and good
    if not compiled:
        return False
    for name, path, expected, marker in (
        ("pristine", ev.path / "io-pristine.trace", 0, "CHECKED_TRACE_PUBLICATION_OK"),
        ("short", ev.path / "io-short.trace", 10, "CHECKED_TRACE_WRITE_REJECTED"),
        ("full", Path("/dev/full"), 11, "CHECKED_TRACE_PUBLICATION_REJECTED"),
    ):
        ev.run("io-fixture-"+name, [str(fixture.relative_to(verify.ROOT)), name,
                                   str(path) if name == "full" else
                                   str(path.relative_to(verify.ROOT))])
        record = ev.receipt["records"][-1]
        good = ev.assertion("executed_trace_"+name,
                            record["exit_code"] == expected and not record["timed_out"] and
                            marker in (verify.ROOT / record["stdout"]).read_text(),
                            child_exit=record["exit_code"],
                            expected_exit=expected) and good

    config = CONFIGURATIONS["minimum"]
    good = verify.operator_check(ev, config=config, operations={"gemv": (4,)}) and good
    for mode in (0, 1, 2):
        label = f"gemv-selector4-mode{mode}"
        compressed = ev.path / (label+".requests.bin.gz")
        trace = ev.path / (label+"-revised.trace")
        text = ev.path / (label+".requests")
        export_text(compressed, text)
        with text.open() as stream:
            reference = OperatorReference(config, mode, 17, io.StringIO())
            reference.execute_operator("gemv", 4, 0, config[0]-1)
            expected = []
            for line in stream:
                row = line.split()
                expected.append((*map(int, row[:6]), int(row[6], 16)))
        from operator_storage import request_records
        good = ev.assertion("lossless_mode"+str(mode),
                            list(request_records(compressed)) == expected and
                            len(expected) == reference.count,
                            records=reference.count,
                            text_bytes=text.stat().st_size,
                            compressed_bytes=compressed.stat().st_size) and good
        for defect, content, message in (
            ("truncated", trace.read_text()[:-1], "truncated operator trace"),
            ("missing_trailer", "\n".join(trace.read_text().splitlines()[:-1])+"\n",
             "missing operator coverage"),
            ("missing_write", "\n".join(trace.read_text().splitlines()[1:])+"\n",
             "operator write address mismatch"),
            ("observed_malformed", trace.read_text().replace(
                trace.read_text().splitlines()[0],
                "W 8 W 8 0 0 9 2191 3e811100 15670654", 1),
             "malformed operator trace"),
        ):
            mutant = ev.path / f"mode{mode}-{defect}.trace"
            mutant.write_text(content)
            report = ev.path / f"mode{mode}-{defect}.json"
            good = rejects(ev, f"mode{mode}_{defect}",
                           lambda: compare_operator(reference, mutant, report),
                           ValueError, message) and good
        record = next(r for r in ev.receipt["records"] if r["label"] == label+"-revised")
        if mode == 1:
            missing = ev.path / "missing-publication.stdout"
            original_stdout = (verify.ROOT / record["stdout"]).read_text()
            missing.write_text("\n".join(
                line for line in original_stdout.splitlines()
                if not line.startswith("OPERATOR_TRACE_PUBLISHED "))+"\n")
            good = rejects(ev, "missing_publication_rejected",
                           lambda: publication(trace, missing), ValueError,
                           "missing operator trace publication") and good
            incomplete = ev.path / "incomplete-publication.trace"
            incomplete.write_bytes(trace.read_bytes()[:-1])
            good = rejects(ev, "incomplete_publication_rejected",
                           lambda: publication(incomplete, verify.ROOT / record["stdout"]),
                           ValueError, "incomplete operator trace publication") and good
            # Run the actual compiled testbench with an output sink that fails on flush.
            argv = ["+trace=/dev/full" if arg.startswith("+trace=") else arg
                    for arg in record["argv"]]
            ev.run("rtl-output-storage-full", argv, timeout=3600)
            failure = ev.receipt["records"][-1]
            good = ev.assertion(
                "rtl_trace_publication_fails_closed",
                failure["exit_code"] not in (0, None) and not failure["timed_out"] and
                "OPERATOR_TRACE_PUBLICATION" in
                (verify.ROOT / failure["stdout"]).read_text(),
                child_exit=failure["exit_code"]) and good
            data = gzip.decompress(compressed.read_bytes())
            for defect, payload in (
                ("record_truncated", gzip.compress(data[:-1], mtime=0)),
                ("gzip_truncated", compressed.read_bytes()[:-5]),
                ("gzip_corrupted", compressed.read_bytes()[:-8] + b"\x00"*8),
            ):
                mutant = ev.path / (defect+".bin.gz")
                mutant.write_bytes(payload)
                good = rejects(ev, defect+"_python",
                               lambda: inspect_requests(mutant),
                               (ValueError, OSError, EOFError), "") and good
                argv = [
                    "+oracle_binary="+str(mutant.relative_to(verify.ROOT))
                    if arg.startswith("+oracle_binary=") else
                    "+trace="+str((ev.path / (defect+".trace")).relative_to(verify.ROOT))
                    if arg.startswith("+trace=") else arg for arg in record["argv"]]
                ev.run(defect+"-consumer", argv, timeout=3600)
                failed = ev.receipt["records"][-1]
                good = ev.assertion(
                    defect+"_consumer_rejected",
                    failed["exit_code"] not in (0, None) and not failed["timed_out"] and
                    "OPERATOR_" in (verify.ROOT / failed["stdout"]).read_text(),
                    child_exit=failed["exit_code"]) and good
            # Four-state compact portability uses the identical exported logical records.
            exe = ev.path / "operator-icarus.vvp"
            parameters = {"OP": 3, **dict(zip(verify.PARAMETERS, config))}
            compiled = verify.compile_simulation(ev, "compact-icarus-compile", [
                "iverilog", "-g2012", "-Wall", "-s", "operator_tb",
                "-o", str(exe.relative_to(verify.ROOT)),
                *[f"-Poperator_tb.{key}={value}" for key, value in parameters.items()],
                *[str(p.relative_to(verify.ROOT)) for p in sorted(verify.ROOT.glob("rtl/*.sv"))],
                "tests/operator_tb.sv"], exe)
            output = ev.path / "icarus.trace"
            argv = ["vvp", str(exe.relative_to(verify.ROOT)), *[
                "+oracle="+str(text.relative_to(verify.ROOT))
                if arg.startswith("+oracle=") else
                "+trace="+str(output.relative_to(verify.ROOT))
                if arg.startswith("+trace=") else arg
                for arg in record["argv"][1:] if not arg.startswith("+oracle_binary=")]]
            executed = compiled and ev.run("compact-icarus", argv, timeout=3600)
            good = ev.assertion(
                "compact_icarus_pristine_numerical_and_exact_trace",
                executed and file_hash(output) == file_hash(trace) and
                compare_operator(reference, output, ev.path / "icarus-reference.json")) and good
            if executed:
                publication(output, ev.path / "compact-icarus.stdout")
                argv = ["+trace=/dev/full" if arg.startswith("+trace=") else arg
                        for arg in argv]
                ev.run("icarus-output-storage-full", argv, timeout=3600)
                failed = ev.receipt["records"][-1]
                good = ev.assertion(
                    "icarus_trace_publication_fails_closed",
                    failed["exit_code"] not in (0, None) and not failed["timed_out"] and
                    "OPERATOR_TRACE_" in (verify.ROOT / failed["stdout"]).read_text(),
                    child_exit=failed["exit_code"]) and good
    for path in ev.path.iterdir():
        if path.is_file() and path.name != "receipt.json":
            ev.receipt.setdefault("data_sha256", {})[
                str(path.relative_to(verify.ROOT))] = file_hash(path)
    ev.finish("running")
    for kind in ("pristine", "corrupt", "missing"):
        executed = ev.run(
            "recovery-reader-"+kind, [
                sys.executable, "tests/operator_storage_checks.py",
                "--recovery-fixture", str((ev.path / "receipt.json").relative_to(verify.ROOT)),
                "--fixture-kind", kind], timeout=3600)
        record = ev.receipt["records"][-1]
        child = json.loads((verify.ROOT / record["stdout"]).read_text().splitlines()[-1])
        ev.receipt.setdefault("children", []).append(child["receipt"])
        good = ev.assertion("recovery_reader_"+kind, executed,
                            receipt=child["receipt"]) and good
    return good


def recovery_fixture(ev, prior, kind):
    """Isolated dispatch fixture: real retained bytes, no fake production results."""
    import shutil
    verify.PRODUCTION = CONFIGURATIONS["minimum"]
    retained = json.loads(prior.read_text())
    # Keep real hash-bound reports/logs, but put disposable stimulus and traces here.
    for source in prior.parent.glob("gemv-selector4-mode*"):
        if source.is_file():
            shutil.copyfile(source, ev.path / source.name)
    for name in list(retained["data_sha256"]):
        source = verify.ROOT / name
        copied = ev.path / source.name
        if source.parent == prior.parent and copied.is_file():
            retained["data_sha256"][str(copied.relative_to(verify.ROOT))] = retained[
                "data_sha256"][name]
    target = ev.path / "gemv-selector4-mode1-revised.trace"
    if kind == "corrupt":
        target.write_text(target.read_text().replace("W 8", "W 8 W 8", 1))
    elif kind == "missing":
        target.unlink()
    fixture = ev.path / "prior.json"
    fixture.write_text(json.dumps(retained))
    dispatched = []

    def capture(*args, **kwargs):
        dispatched.extend(kwargs["cases"])
        return True

    verify.operator_check = capture
    passed = verify.production_recovery(ev, fixture)
    row = next(a for a in ev.receipt["assertions"]
               if a["name"] == "completed_children_not_reclassified")
    expected_reuse = [("gemv", 4, mode) for mode in (0, 1, 2)
                      if kind == "pristine" or mode != 1]
    all_cases = [(name, selector, mode)
                 for name in verify.OPERATOR_IDS
                 for selector in (range(7) if name == "gemv" else
                                  range(3) if name in ("norm", "elementwise") else (0,))
                 for mode in (0, 1, 2)]
    return ev.assertion(
        "recovery_dispatch_"+kind,
        passed and sorted(map(tuple, row["reused"])) == sorted(expected_reuse) and
        sorted(dispatched) == sorted(case for case in all_cases if case not in expected_reuse),
        reused=row["reused"], regenerated_cases=dispatched,
        scope="Recovery reader/dispatch fixture only; no production execution claimed")


def retained_capacity(ev, source):
    """Measure lossless compression of actual failed-shard input, not RTL fidelity."""
    import shutil
    source = verify.ROOT / source
    prior = source.parent / "receipt.json"
    original = json.loads(prior.read_text())
    relative = str(source.relative_to(verify.ROOT))
    expected_hash = original["data_sha256"][relative]
    if file_hash(source) != expected_hash:
        raise ValueError("retained input no longer matches original receipt")
    target = ev.path / "retained-production-input.bin.gz"
    with source.open("rb") as stream, RequestWriter(target) as writer:
        if stream.read(len(REQUEST_MAGIC)) != REQUEST_MAGIC:
            raise ValueError("retained production input header")
        while True:
            block = stream.read(REQUEST_RECORD.size * 16384)
            if len(block) % REQUEST_RECORD.size:
                raise ValueError("truncated retained production input")
            if not block:
                break
            for record in REQUEST_RECORD.iter_unpack(block):
                writer.emit(record[0], record[1:6], record[6])
    free = shutil.disk_usage(ev.path).free
    # This intentionally overestimates smaller shards at the measured largest-shard rate.
    # The hard bound remains the per-file cap, not this extrapolation.
    from verify import l1_jobs
    cases = sum(len(job[3].get("cases", ())) for job in l1_jobs()
                if job[1] is verify.operator_check)
    cases += 3  # maximum-position runs all precisions
    projection = cases * writer.metadata["compressed_bytes"]
    hard_bound = cases * MAX_COMPRESSED_BYTES
    ev.receipt["retained_capacity_measurement"] = {
        "source": relative, "original_receipt": str(prior.relative_to(verify.ROOT)),
        "source_sha256": expected_hash, **writer.metadata,
        "old_duplicate_bytes": source.stat().st_size +
            source.with_suffix("").stat().st_size,
        "l1_operator_input_count": cases,
        "largest_measured_shard_rate_projection_bytes": projection,
        "projection_is_not_a_proven_upper_bound": True,
        "hard_all_input_ceiling_bytes": hard_bound,
        "four_concurrent_input_ceiling_bytes": 4 * MAX_COMPRESSED_BYTES,
        "free_bytes": free, "reserve_bytes": RESERVE_BYTES,
        "full_l1_hard_capacity_established": free >= hard_bound + RESERVE_BYTES,
        "full_model_capacity_established": False,
    }
    return ev.assertion("retained_production_input_lossless",
                        writer.metadata["decoded_sha256"] == expected_hash,
                        measured_records=writer.count)


def main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retained-input", type=Path)
    parser.add_argument("--recovery-fixture", type=Path)
    parser.add_argument("--fixture-kind", choices=("pristine", "corrupt", "missing"),
                        default="pristine")
    args = parser.parse_args()
    ev = verify.Evidence("operator-storage")
    good = False
    try:
        if args.recovery_fixture:
            good = recovery_fixture(ev, verify.ROOT / args.recovery_fixture, args.fixture_kind)
        else:
            good = ev.versions() and check(ev)
        if good and args.retained_input:
            good = retained_capacity(ev, args.retained_input) and good
    except (ValueError, OSError, EOFError, AssertionError, KeyError) as error:
        ev.assertion("operator_storage_exception", False, diagnostic=repr(error))
    finally:
        ev.finish("passed" if good else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(verify.ROOT))}))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
