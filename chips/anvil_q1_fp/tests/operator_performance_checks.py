#!/usr/bin/env python3
"""Bounded exact-reuse and buffered-input repair comparisons, not full L1."""

import argparse
from contextlib import contextmanager
import io
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import architecture
import operators
import verify
from numerical import decode


@contextmanager
def uncached():
    encoding, stored = architecture.encode16, operators.stored_value
    try:
        architecture.encode16 = operators.encode16 = encoding.__wrapped__
        operators.stored_value = stored.__wrapped__
        yield
    finally:
        architecture.encode16 = operators.encode16 = encoding
        operators.stored_value = stored


def conversion_check(ev):
    good = True
    for mode in (0, 1, 2):
        config = architecture.CONFIGURATIONS["nonpower"]
        outputs = []
        for reuse in (False, True):
            started = time.monotonic()
            stream, binary = io.StringIO(), io.BytesIO()

            def generate():
                reference = operators.OperatorReference(config, mode, 17, stream, binary)
                for name in operators.OPERATOR_IDS:
                    for selector in (range(7) if name == "gemv" else
                                     range(3) if name in ("norm", "elementwise") else (0,)):
                        reference.execute_operator(name, selector, 2, 1)
                model = architecture.Architecture(config, mode, 17)
                fixture = ev.path / f"conversion-mode{mode}-reuse{int(reuse)}.hex"
                model.write_fixture(fixture)
                model.execute()
                return reference, model, fixture

            if reuse:
                reference, model, fixture = generate()
            else:
                with uncached():
                    reference, model, fixture = generate()
            outputs.append((stream.getvalue(), binary.getvalue(),
                            reference.expected_writes, model.events, fixture))
            ev.receipt.setdefault("measurements", []).append({
                "mode": mode, "reuse": reuse, "elapsed_s": time.monotonic()-started,
                "requests": reference.count})
        old, new = outputs
        good = ev.assertion(
            f"mode{mode}_exact_uncached_reference_identity",
            old[:4] == new[:4] and verify.digest(old[4]) == verify.digest(new[4]),
            requests_bytes=len(new[0]), writes=len(new[2]), events=len(new[3]),
            fixture_sha256=verify.digest(new[4])) and good
        decoded = b"".join(
            operators.REQUEST_RECORD.pack(*map(int, row.split()[:6]),
                                          int(row.split()[6], 16))
            for row in new[0].encode().splitlines())
        good = ev.assertion(
            f"mode{mode}_binary_exact_text_records",
            new[1] == operators.REQUEST_MAGIC + decoded) and good
    # Eviction is bounded, and both formats preserve the unchanged exact core.
    for mode in (1, 2):
        for bits in range(65536):
            eb, fb = (8, 7) if mode == 1 else (5, 10)
            _, kind, _, value = decode(bits, eb, fb)
            if kind not in ("nan", "inf"):
                value = float(value)
                if architecture.encode16(value, mode) != architecture.encode16.__wrapped__(value, mode):
                    raise ValueError("conversion cache differs")
    good = ev.assertion("bounded_format_aware_cache",
                        architecture.encode16.cache_info().currsize <= 8192 and
                        operators.stored_value.cache_info().currsize <= 4096,
                        encoding_cache=list(architecture.encode16.cache_info()),
                        decode_cache=list(operators.stored_value.cache_info())) and good
    return good


def input_check(ev, production=False):
    config = operators.PRODUCTION if production else architecture.CONFIGURATIONS["nonpower"]
    # operator_check executes the pristine numerical/protocol assertions first.
    mode = 1
    good = verify.operator_check(ev, config=config, operations={"gemv": (4,)},
                                 cases=(("gemv", 4, mode),))
    binary_run = next(r for r in ev.receipt["records"]
                      if r["label"] == "gemv-selector4-mode1-revised")
    text_argv = [arg.replace("-revised.trace", "-text.trace")
                 for arg in binary_run["argv"] if not arg.startswith("+oracle_binary=")]
    executed = ev.run("formatted-input-baseline", text_argv, timeout=86400)
    binary_trace = ev.path / "gemv-selector4-mode1-revised.trace"
    text_trace = ev.path / "gemv-selector4-mode1-text.trace"
    good = ev.assertion("buffered_formatted_exact_trace",
                        executed and verify.digest(binary_trace) == verify.digest(text_trace),
                        trace_sha256=verify.digest(binary_trace),
                        binary_elapsed_s=binary_run["elapsed_s"],
                        formatted_elapsed_s=ev.receipt["records"][-1]["elapsed_s"]) and good
    binary = ev.path / "gemv-selector4-mode1.requests.bin"
    text = ev.path / "gemv-selector4-mode1.requests"
    data = binary.read_bytes()
    with text.open() as stream:
        require_magic = data[:8] == operators.REQUEST_MAGIC
        index = 8
        for line in stream:
            row = line.split()
            expected = (*map(int, row[:6]), int(row[6], 16))
            if operators.REQUEST_RECORD.unpack_from(data, index) != expected:
                raise ValueError("binary/text request mismatch")
            index += operators.REQUEST_RECORD.size
    good = ev.assertion("all_input_records_identical",
                        require_magic and index == len(data),
                        records=(index-8)//28,
                        text_sha256=verify.digest(text), binary_sha256=verify.digest(binary)) and good
    if not production:
        for name, contents, diagnostic in (
            ("header", b"INVALID!" + data[8:], "OPERATOR_BINARY_OPEN"),
            ("truncated", data[:-1], "OPERATOR_EXTRA_REQUEST"),
            ("extra", data + data[8:36], "OPERATOR_MISSING_REQUESTS"),
            ("address", data[:12] + (15).to_bytes(4, "little") + data[16:],
             "OPERATOR_ARCHITECTURAL_ADDRESS"),
        ):
            mutant = ev.path / (name + ".bin")
            mutant.write_bytes(contents)
            argv = [arg if not arg.startswith("+oracle_binary=") else
                    "+oracle_binary=" + str(mutant.relative_to(verify.ROOT))
                    for arg in binary_run["argv"]]
            argv = [arg if not arg.startswith("+trace=") else
                    "+trace=" + str((ev.path / (name + ".trace")).relative_to(verify.ROOT))
                    for arg in argv]
            success = ev.run("input-defect-" + name, argv, timeout=86400)
            record = ev.receipt["records"][-1]
            output = (verify.ROOT / record["stdout"]).read_text()
            good = ev.assertion(
                "input_defect_" + name,
                not success and record["exit_code"] is not None and
                not record["timed_out"] and diagnostic in output,
                diagnostic=diagnostic) and good
    return good


def production_reference_check(ev):
    class HashWriter:
        def __init__(self):
            self.hash = hashlib.sha256()

        def write(self, text):
            self.hash.update(text.encode())

    observations = []
    for reuse in (False, True):
        stream = HashWriter()

        def generate():
            model = operators.OperatorReference(operators.PRODUCTION, 1, 17, stream)
            model.execute_operator("gemv", 4, 0, 23)
            return model

        with ev.profile("production-reference-" + ("cached" if reuse else "uncached")):
            if reuse:
                model = generate()
            else:
                with uncached():
                    model = generate()
        observations.append({
            "request_sha256": stream.hash.hexdigest(), "requests": model.count,
            "reference_sha256": hashlib.sha256(
                json.dumps(model.expected_writes).encode()).hexdigest()})
    return ev.assertion("production_exact_reference_and_request_identity",
                        observations[0] == observations[1], observations=observations)


def check(ev, production=False):
    good = conversion_check(ev)
    if production:
        good = production_reference_check(ev) and good
    return input_check(ev, production) and good


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production", action="store_true")
    args = parser.parse_args()
    ev = verify.Evidence("operator-performance")
    good = False
    try:
        good = ev.versions() and check(ev, args.production)
    except (ValueError, KeyError, OSError, AssertionError) as error:
        ev.assertion("repair_probe_exception", False, diagnostic=repr(error))
    finally:
        ev.finish("passed" if good else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(verify.ROOT))}))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
