#!/usr/bin/env python3
"""Bounded production-prefix measurement, not collection restart or feasibility approval.

Run only after append-only admission: python3 tests/feasibility_probe.py
Nine fresh production RTL processes cover observation, reset-origin repeat and
executable replay in all modes. Independent schedule/content checks run while
transactions arrive on a binary pipe, never a per-beat stdout transcript.
"""

from contextlib import closing
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import select
import struct
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from architecture import metrics
from benchmark import load_json, require, sha, validate_input_manifests
from benchmark_inputs import write_json
from collection_capacity import filesystem_capacity, retained_usage, transactions as count_transactions
from production_schedule import MODES, PRODUCTION, schedule
from production_sim import checked, memory_table, prepare_rope
from production_trace import StreamOracle, embedding
from streaming_replay import production_bindings
from teacher_reference import decoded_rows, selected_stream
from verify import Evidence, ROOT, now, source_inventory


RECORD = struct.Struct("<11I")
CHILD_ALLOWANCE = 3600


def floating(word, mode):
    value = (struct.unpack("<f", struct.pack("<I", word))[0] if mode != "w4a16"
             else (word if word < 2**31 else word - 2**32) / 65536.0)
    require(math.isfinite(value), "nonfinite prefix milestone")
    return value


def compare(values, reference, enforce):
    require(len(values) == len(reference) and values and
            all(math.isfinite(x) for x in (*values, *reference)),
            "incomplete/nonfinite prefix numerical vector")
    result = metrics(values, reference)
    if enforce:
        require(result["normalized_max_absolute_error"] <= .002 and
                (result["reference_all_zero"] or
                 result["cosine"] is not None and result["cosine"] >= .9999),
                "prefix numerical fidelity: " + json.dumps(result))
    return {**result, "native_fidelity_enforced": enforce,
            "compatibility_fp64_deviation_only": not enforce}


def reference(model, mode, token, destination):
    """Whole first norm and first eight Q outputs over actual selected weights."""
    import numpy as np
    stream = selected_stream(model, mode)
    x = decoded_rows(stream, stream.get("model.embed_tokens.weight")[token], mode)
    gamma = stream.weight("model.layers.0.input_layernorm.weight", mode)
    epsilon = float(np.float32(1e-6)) if mode != "w4a16" else 1e-6
    normalized = x * gamma / np.sqrt(np.mean(x*x, dtype=np.float64) + epsilon)
    q = (stream.weight("model.layers.0.self_attn.q_proj.weight", mode)[:8] @ normalized +
         stream.weight("model.layers.0.self_attn.q_proj.bias", mode)[:8])
    require(x.shape == normalized.shape == (896,) and q.shape == (8,) and
            all(np.isfinite(array).all() for array in (x, normalized, q)),
            "independent prefix reference shape/finite")
    # Retain exact reference bytes, including independent recomputation on replay.
    result = {}
    for name, array in (("embedding", x), ("norm", normalized), ("q8", q)):
        with (destination / (name + ".f64")).open("xb") as output:
            output.write(array.astype("<f8").tobytes())
        result[name] = array.tolist()
    return result


class PrefixAudit:
    """Independent expected public transactions, conservation and numerical milestones."""

    def __init__(self, mode, token, expected_values):
        self.mode = mode
        self.expected = iter(schedule(PRODUCTION, MODES[mode], [token]))
        self.oracle = StreamOracle(mode)
        self.reference = expected_values
        self.previous = self.count = 0
        self.digest = hashlib.sha256()
        self.scratch = {}
        self.embeddings = {}
        self.vectors = {"embedding": [], "norm": [], "q8": []}
        self.comparisons = {}
        self.milestones = {}
        self.started = time.monotonic()

    def feed(self, row):
        require(len(row) == 11, "prefix record width")
        start, end = row[0] + (row[1] << 32), row[2] + (row[3] << 32)
        require(self.previous < start < end, "prefix request/response order")
        self.previous = end
        wanted = next(self.expected, None)
        require(wanted is not None and tuple(row[4:10]) == wanted[:6],
                f"prefix architectural address/order at {self.count}: "
                f"observed={tuple(row[4:10])}, expected={wanted}")
        write, kind, layer, proj, source, column, data = row[4:]
        require(not self.comparisons.get("q8"), "extra transaction after prefix milestone")
        self.count += 1
        self.digest.update(RECORD.pack(*row))
        if kind != 8:
            require(not write and kind in (0, 1, 2, 3, 4, 5, 12),
                    "unexpected prefix external access")
            require(data == self.oracle.read(kind, layer, proj, source, column),
                    "prefix external tensor bytes")
            if kind == 0:
                self.embeddings[column] = embedding(data, self.mode)
            return
        key = source, column
        if not write:
            require(key in self.scratch and self.scratch[key] == data,
                    "prefix acknowledged scratch readback")
            return
        name = {0: "embedding", 1: "norm", 2: "q8"}.get(source)
        require(name is not None and column == len(self.vectors[name]),
                "prefix milestone column/order")
        if name == "embedding":
            require(column in self.embeddings and data == self.embeddings[column],
                    "prefix embedding conversion")
        self.scratch[key] = data
        self.vectors[name].append(floating(data, self.mode))
        width = 8 if name == "q8" else 896
        if len(self.vectors[name]) == width:
            self.comparisons[name] = compare(
                self.vectors[name], self.reference[name], self.mode != "w4a16")
            self.milestones[name] = {
                "cycle": end, "transactions": self.count,
                "audit_elapsed_s": time.monotonic() - self.started}

    def finish(self):
        require(set(self.comparisons) == {"embedding", "norm", "q8"},
                "incomplete prefix numerical milestone")
        return {
            "transactions": self.count, "last_response_cycle": self.previous,
            "decoded_transaction_sha256": self.digest.hexdigest(),
            "milestones": self.milestones, "comparisons": self.comparisons,
            "completed_layers": 0, "completed_tokens": 0, "complete_benchmark": False,
        }


class StorageSampler:
    """Measured project-local new-run allocation; no evidence reclamation."""

    def __init__(self, ev):
        self.ev = ev
        self.directory = ev.path
        self.peak_allocated = self.peak_logical = 0
        self.samples = 0
        self.error = None
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def sample(self):
        allocated = logical = 0
        for parent, directories, filenames in os.walk(self.directory, followlinks=False):
            directories[:] = [name for name in directories
                              if not (Path(parent) / name).is_symlink()]
            for name in filenames:
                try:
                    info = (Path(parent) / name).lstat()
                except FileNotFoundError:
                    continue  # Compiler/atomic receipt staging may finish between samples.
                allocated += info.st_blocks * 512
                logical += info.st_size
        self.samples += 1
        self.peak_allocated = max(self.peak_allocated, allocated)
        self.peak_logical = max(self.peak_logical, logical)

    def loop(self):
        try:
            while not self.stop.is_set():
                self.sample()
                self.stop.wait(.25)
        except OSError as error:
            self.error = str(error)

    def __enter__(self):
        self.sample()
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join()
        self.sample()
        self.ev.receipt["storage_measurement"] = self.result()
        self.ev.receipt["filesystem_after"] = filesystem_capacity(ROOT)
        self.ev.finish("running")

    def result(self):
        require(self.error is None, "storage sampling failure: " + str(self.error))
        return {
            "peak_observed_new_run_allocated_bytes": self.peak_allocated,
            "peak_observed_new_run_logical_bytes": self.peak_logical,
            "samples": self.samples, "sampling_interval_s": .25,
            "scope": "Entire new probe directory including build, repeats, replay and mutants",
            "limitation": "Sampled high-water measurement, not an instantaneous upper bound; "
                          "excludes process RSS, filesystem metadata and pre-existing evidence.",
        }


def execute(ev, executable, table, rope, directory, mode, token, values):
    directory.mkdir()
    require(sha(executable) == ev.receipt["executable"]["sha256"],
            "prefix executable changed before launch")
    audit = PrefixAudit(mode, token, values)
    read_fd, write_fd = os.pipe()
    argv = [str(executable.relative_to(ROOT)), str(table.relative_to(ROOT)),
            str(rope.relative_to(ROOT)), str(directory.relative_to(ROOT)),
            str(token), str(MODES[mode]), str(write_fd)]
    record = {
        "label": directory.name, "argv": argv, "cwd": ".", "started_at": now(),
        "timeout_s": CHILD_ALLOWANCE, "timed_out": False,
        "stdout": str((directory / "stdout.txt").relative_to(ROOT)),
        "stderr": str((directory / "stderr.txt").relative_to(ROOT)),
        "observation_channel": "inherited binary pipe, <11I per completed transaction",
        "reset_origin": True, "role": directory.name, "exit_code": None,
    }
    ev.receipt["records"].append(record)
    ev.finish("running")
    started = time.monotonic()
    buffer = bytearray()
    process = None
    try:
        with (directory / "stdout.txt").open("xb") as out, \
                (directory / "stderr.txt").open("xb") as err:
            process = subprocess.Popen(argv, cwd=ROOT, stdout=out, stderr=err,
                                       pass_fds=(write_fd,))
            record["pid"] = process.pid
            os.close(write_fd)
            write_fd = None
            while True:
                remaining = CHILD_ALLOWANCE - (time.monotonic() - started)
                if remaining <= 0:
                    record["timed_out"] = True
                    raise ValueError("prefix child allowance exceeded; milestone incomplete")
                readable, _, _ = select.select([read_fd], [], [], min(1., remaining))
                if not readable:
                    continue
                raw = os.read(read_fd, 44 * 1024)
                if not raw:
                    break
                buffer.extend(raw)
                consumed = len(buffer) // RECORD.size * RECORD.size
                for row in RECORD.iter_unpack(buffer[:consumed]):
                    audit.feed(row)
                del buffer[:consumed]
            require(not buffer, "truncated live prefix record")
            process.wait(timeout=max(.001, CHILD_ALLOWANCE - (time.monotonic() - started)))
            record["exit_code"] = process.returncode
            require(process.returncode == 0, "prefix simulator failed: " + record["stderr"])
        result = audit.finish()
        summary = load_json(directory / "prefix.json")
        require(summary["requests"] == summary["responses"] == result["transactions"] and
                summary["cycles"] == result["last_response_cycle"] and
                summary["q_outputs"] == 8 and
                summary["completed_layers"] == summary["completed_tokens"] == 0 and
                summary["complete_benchmark"] is False,
                "prefix producer/independent conservation mismatch")
        result["elapsed_s"] = time.monotonic() - started
        result["process_pid"] = process.pid
        write_json(directory / "live-audit.json", result)
        return result
    finally:
        if process is not None and process.poll() is None:
            # Only this owned diagnostic child is stopped; no production process is touched.
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if process is not None:
            record["exit_code"] = process.returncode
        os.close(read_fd)
        if write_fd is not None:
            os.close(write_fd)
        record.update(ended_at=now(), elapsed_s=time.monotonic() - started)
        record["partial_observation"] = {
            "transactions": audit.count, "last_response_cycle": audit.previous,
            "completed_numerical_milestones": list(audit.comparisons),
            "milestones": audit.milestones,
            "comparisons": audit.comparisons,
            "complete_prefix": set(audit.comparisons) == {"embedding", "norm", "q8"},
            "complete_benchmark": False,
        }
        ev.finish("running")


def prefix_rows(path):
    with gzip.open(path, "rb") as stream:
        while raw := stream.read(RECORD.size * 1024):
            require(len(raw) % RECORD.size == 0, "partial prefix transaction record")
            yield from RECORD.iter_unpack(raw)


def replay_bytes(path, mode, token, values):
    audit = PrefixAudit(mode, token, values)
    with closing(prefix_rows(path)) as rows:
        for row in rows:
            audit.feed(row)
    return audit.finish()


def defects(ev, pristine, mode, token, values):
    """Mutate actual retained RTL bytes; unchanged pristine assertion must reject."""
    cases = {
        "address": "prefix architectural address/order",
        "response-order": "prefix request/response order",
        "tensor-bytes": "prefix external tensor bytes",
        "scratch-readback": "prefix acknowledged scratch readback",
        "numerical": "prefix numerical fidelity",
        "missing-milestone": "incomplete prefix numerical milestone",
        "truncated-record": "transaction",
    }
    require(mode == "bf16", "numerical defect requires native enforcement")
    replay_bytes(pristine, mode, token, values)
    for label, diagnostic in cases.items():
        target = ev.path / ("mutant-" + label + ".u32.gz")
        changed = False
        with closing(prefix_rows(pristine)) as rows, gzip.open(target, "xb") as output:
            for index, row in enumerate(rows):
                row = list(row)
                if label == "address" and index == 0:
                    row[9] += 1
                    changed = True
                elif label == "response-order" and index == 1:
                    row[2:4] = row[:2]
                    changed = True
                elif label == "tensor-bytes" and index == 0:
                    row[10] ^= 1
                    changed = True
                elif label == "scratch-readback" and not changed and row[4:6] == [0, 8]:
                    row[10] ^= 1
                    changed = True
                elif label == "numerical" and row[4:6] == [1, 8] and row[8] == 1:
                    row[10] ^= 0x80000000
                    changed = True
                elif (label == "missing-milestone" and row[4:6] == [1, 8] and
                      row[8:10] == [2, 7]):
                    changed = True
                    continue
                raw = RECORD.pack(*row)
                if label == "truncated-record" and index == 0:
                    output.write(raw[:-1])
                    changed = True
                    break
                output.write(raw)
        require(changed, "prefix defect site not reached: " + label)
        try:
            replay_bytes(target, mode, token, values)
        except (ValueError, EOFError, struct.error) as error:
            require(diagnostic.lower() in str(error).lower(),
                    "wrong prefix defect rejection: " + label + ": " + str(error))
            ev.assertion("reject_actual_bytes_" + label, True,
                         diagnostic=str(error), path=str(target.relative_to(ROOT)),
                         sha256=sha(target), pristine_assertion_passed=True,
                         compilation_failure_is_not_rejection=True)
        else:
            raise ValueError("actual-byte defect escaped: " + label)


def workload(suite, measurements):
    """Entire frozen workload, including distinct repeats and fresh replay."""
    rows = []
    totals = {mode: {"minimum_transactions": 0, "maximum_transactions": 0,
                     "largest_single_token_transaction_count": 0}
              for mode in MODES}
    for domain, group in suite["domains"].items():
        require(len(group["cases"]) == 10, "five-domain case denominator")
        for case in group["cases"]:
            teacher = load_json(ROOT / case["teacher_tokens"]["path"])
            prompt = load_json(ROOT / case["prompt_tokens"]["path"])
            n, p = len(teacher), len(prompt)
            require(0 < n <= 32768 and 0 < p <= p + 127 <= 32768,
                    "whole workload position limits")
            modes = {}
            for mode, precision in MODES.items():
                t = count_transactions(PRODUCTION, precision, n)
                low = count_transactions(PRODUCTION, precision, p)
                high = count_transactions(PRODUCTION, precision, p + 127)
                # Two reset-origin executions plus fresh executable replay of each.
                minimum, maximum = 4*(t+low), 4*(t+high)
                totals[mode]["minimum_transactions"] += minimum
                totals[mode]["maximum_transactions"] += maximum
                longest = max(n, p + 127)
                last_token = count_transactions(PRODUCTION, precision, longest) - (
                    count_transactions(PRODUCTION, precision, longest - 1) if longest > 1 else 0)
                totals[mode]["largest_single_token_transaction_count"] = max(
                    totals[mode]["largest_single_token_transaction_count"], last_token)
                modes[mode] = {
                    "teacher_transactions_per_reset_run": t,
                    "greedy_transactions_per_reset_run_minimum": low,
                    "greedy_transactions_per_reset_run_maximum": high,
                    "two_originals_plus_replay_each_minimum": minimum,
                    "two_originals_plus_replay_each_maximum": maximum}
            rows.append({"case": domain + "/" + case["id"], "teacher_positions": n,
                         "prompt_positions": p, "greedy_positions_maximum": p + 127,
                         "modes": modes})
    require(len(suite["domains"]) == 5 and len(rows) == 50, "whole workload denominator")
    for mode, total in totals.items():
        measured = measurements[mode]
        # A prefix rate is explicitly not representative of a whole layer/token.
        rate = measured["transactions"] / measured["elapsed_s"]
        total.update({
            "measured_prefix_transactions_per_s": rate,
            "constant_prefix_rate_estimate_minimum_s": total["minimum_transactions"] / rate,
            "constant_prefix_rate_estimate_maximum_s": total["maximum_transactions"] / rate,
            "uncompressed_trace_bytes_minimum_all_originals_and_replays":
                total["minimum_transactions"] * RECORD.size,
            "uncompressed_trace_bytes_maximum_all_originals_and_replays":
                total["maximum_transactions"] * RECORD.size,
            "largest_two_observer_token_window_uncompressed_trace_bytes":
                total["largest_single_token_transaction_count"] * 2 * RECORD.size,
            "estimate_is_not_bound_or_feasibility_pass": True})
    return {
        "cases": rows, "totals": totals, "reset_origin_runs_per_case_mode_workload": 2,
        "fresh_replay_runs_charged_per_original": 1,
        "original_reset_origin_rtl_processes": 600,
        "fresh_reset_origin_rtl_replay_processes_charged": 600,
        "additional_backwards_access_replays": "unmeasured, additional",
        "independent_fp64_full_inference_cost": "unmeasured, additional",
        "full_token_window_vector_payload_bytes":
            (24 * 896 + 151936) * (2 * 4 + 2 * 8),
        "whole_workload_storage_fit": None,
        "storage_accounting": "Uncompressed trace extents and four live vector payloads "
                              "only; not encoded gzip size, allocation bounds or a claim "
                              "that prefix storage predicts a complete-token window. "
                              "Build, metadata, processes and retained failures add costs.",
        "retained_failed_runs": "preserved and separately inventoried, never amortized away",
        "completed_full_layers": 0, "completed_full_tokens": 0,
        "full_workload_feasible": None, "accelerated_collection_selected": False,
        "limitation": "Counts cover all fifty cases, three modes, full teacher contexts and "
                     "greedy prompt..prompt+127 positions, reset repeats and replay. Measured "
                     "first-norm/Q8 throughput cannot certify attention, FFN, logits, full "
                     "reference/replay costs, live-window storage or aggregate deadline fit.",
    }


def run(ev):
    import numpy as np
    started = time.monotonic()
    model, suite, _, _ = validate_input_manifests(ROOT, ev)
    ev.receipt["data_sha256"] = production_bindings(ROOT, model, suite)
    ev.receipt["numerical_library"] = {"numpy": np.__version__, "python": sys.version}
    ev.receipt["scope"] = "bounded prefix discriminator only; no production restart"
    ev.receipt["linked_original_failure"] = {
        "attempt": 710,
        "receipt": "evidence/preparation/verifier-production-simulation-_o7vrtgh/receipt.json",
        "observed_runtime_termination_s": 2701,
        "preparation_receipt_is_not_success": True}
    ev.receipt["filesystem_before"] = filesystem_capacity(ROOT)
    ev.receipt["retained_evidence_before"] = retained_usage(ROOT / "evidence")
    case = next(iter(suite["domains"].values()))["cases"][0]
    token = load_json(checked(ev, case["teacher_tokens"]))[0]
    ev.receipt["token_source"] = case["teacher_tokens"]
    ev.receipt["token_id"] = token
    for name, argv in (
            ("verilator", ["verilator", "--version"]),
            ("cxx", ["c++", "--version"]),
            ("python", [sys.executable, "--version"])):
        require(ev.run(name + "-version", argv, timeout=30), "missing installed " + name)
    results = {}
    with StorageSampler(ev) as storage:
        obj = ev.path / "obj"
        command = [
            "verilator", "--cc", "--exe", "--build", "--savable", "-j", "2", "-O3",
            "-Wno-fatal", "--top-module", "anvil_q1_fp_top",
            "--Mdir", str(obj.relative_to(ROOT)), "-CFLAGS", "-O3 -std=c++17",
            "-LDFLAGS", "-lz",
            *[str(p.relative_to(ROOT)) for p in sorted((ROOT / "rtl").glob("*.sv"))],
            str(ROOT / "tests/feasibility_prefix.cpp")]
        require(ev.run("prefix-build", command, timeout=1800), "prefix build failed")
        executable = obj / "Vanvil_q1_fp_top"
        ev.receipt["executable"] = {
            "path": str(executable.relative_to(ROOT)), "sha256": sha(executable)}
        # Compiler staging belongs to this new successful build only.
        for path in obj.iterdir():
            if path.is_file() and path.suffix in (".o", ".a", ".gch"):
                path.unlink()
        for mode in ("bf16", "fp16", "w4a16"):
            directory = ev.path / mode
            directory.mkdir()
            table = memory_table(ev, model, mode, directory / "memory.txt")
            rope = prepare_rope(directory / "rope.u32", 1, mode)
            comparisons = []
            references = []
            for role in ("observation", "reset-repeat", "executable-replay"):
                reference_dir = directory / (role + "-reference")
                reference_dir.mkdir()
                reference_started = time.monotonic()
                values = reference(model, mode, token, reference_dir)
                references.append(values)
                reference_elapsed = time.monotonic() - reference_started
                result = execute(ev, executable, table, rope, directory / role,
                                 mode, token, values)
                result["reference_elapsed_s"] = reference_elapsed
                result["reference_sha256"] = {
                    p.name: sha(p) for p in sorted(reference_dir.glob("*.f64"))}
                trace = directory / role / "transactions.u32.gz"
                replay_started = time.monotonic()
                replayed = replay_bytes(trace, mode, token, values)
                result["retained_bytes_audit_elapsed_s"] = time.monotonic() - replay_started
                require(replayed["decoded_transaction_sha256"] ==
                        result["decoded_transaction_sha256"] and
                        replayed["comparisons"] == result["comparisons"],
                        "live pipe differs from executable retained bytes")
                result["trace"] = {"path": str(trace.relative_to(ROOT)), "sha256": sha(trace),
                                   "bytes": trace.stat().st_size}
                comparisons.append(result)
                ev.assertion("completed_prefix_" + mode + "_" + role, True, **result)
            require(len({row["process_pid"] for row in comparisons}) == 3,
                    "prefix execution roles do not identify separate processes")
            require(all(row["decoded_transaction_sha256"] ==
                        comparisons[0]["decoded_transaction_sha256"] and
                        row["reference_sha256"] == comparisons[0]["reference_sha256"]
                        for row in comparisons), "prefix reset-repeat/replay byte mismatch")
            require(references[0] == references[1] == references[2],
                    "independent recomputed reference mismatch")
            results[mode] = comparisons[0]
            if mode == "bf16":
                defects(ev, directory / "observation/transactions.u32.gz",
                        mode, token, references[0])
        report = workload(suite, results)
        require(production_bindings(ROOT, model, suite) == ev.receipt["data_sha256"] and
                source_inventory() == ev.receipt["source_sha256"] and
                sha(executable) == ev.receipt["executable"]["sha256"],
                "prefix sources/data/executable changed during measurement")
        report.update(measured_mode_prefixes=results, elapsed_s=time.monotonic() - started,
                      measurement_status="completed-prefix-only",
                      complete_benchmark=False, acceptance_evidence=False,
                      hardware_interface_capability="unestablished; no device access attempted")
        write_json(ev.path / "measurement.json", report)
    ev.receipt["storage_measurement"] = storage.result()
    ev.receipt["filesystem_after"] = filesystem_capacity(ROOT)
    ev.assertion("bounded_measurement_not_full_feasibility", True,
                 completed_numerical_prefixes=9, completed_layers=0, completed_tokens=0,
                 full_workload_feasible=None, accelerated_collection_selected=False)


def main():
    require(len(sys.argv) == 1, "prefix probe accepts no collection/timeout overrides")
    ev = Evidence("feasibility-prefix")
    passed = False
    try:
        run(ev)
        passed = True
    except (ValueError, OSError, KeyError, ImportError, EOFError, struct.error,
            subprocess.TimeoutExpired) as error:
        ev.assertion("prefix_measurement_failure", False, diagnostic=str(error),
                     incomplete_measurement=True, full_workload_feasible=None)
    finally:
        ev.finish("passed" if passed else "failed")
        print(json.dumps({"status": ev.receipt["status"],
                          "receipt": str((ev.path / "receipt.json").relative_to(ROOT)),
                          "complete_benchmark": False, "full_workload_feasible": None}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
