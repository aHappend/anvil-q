#!/usr/bin/env python3
"""Synthetic maximum-frame memory diagnostics; never production permission."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import struct
import subprocess
import sys
import threading
import zlib

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import load_json, require, sha
from packed_storage import CHUNK_BYTES, RECORD, Reader, Writer
from sparse_transactions import TRACE_CHUNK_BYTES
from verify import Evidence, ROOT, now


PRIOR = "evidence/preparation/verifier-packed-storage-e6dq66yt/receipt.json"
SOURCES = ("tests/memory_capacity_checks.py", "tests/memory_map_fixture.cpp",
           "tests/packed_producer_fixture.cpp", "tests/packed_storage.py",
           "tests/sparse_transactions.py", "tests/packed_stream.py",
           "tests/packed_stream.hpp", "tests/production_storage.hpp",
           "tests/production_sim.cpp", "tests/production_sim.py",
           "tests/fp64_reference.py", "tests/awq_prepare.py",
           "tests/teacher_reference.py", "tests/collection_capacity.py")


def process_sample(pid):
    """Inspect only this diagnostic's process subtree, never unrelated tasks."""
    try:
        fields = {}
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith(("VmRSS:", "VmHWM:")):
                key, value, unit = line.split()
                require(unit == "kB", "unexpected Linux RSS unit")
                fields[key[:-1]] = int(value) * 1024
        children = Path(f"/proc/{pid}/task/{pid}/children").read_text().split()
    except (FileNotFoundError, ProcessLookupError):
        return []
    return [(pid, fields)] + [entry for child in children
                             for entry in process_sample(int(child))]


class Monitor:
    def __init__(self):
        self.stop = threading.Event()
        self.peak = self.processes = self.samples = 0
        self.highwaters = {}
        self.error = None
        self.thread = threading.Thread(target=self.sample)

    def sample(self):
        try:
            while not self.stop.is_set():
                rows = process_sample(os.getpid())
                self.samples += 1
                self.peak = max(self.peak, sum(row.get("VmRSS", 0) for _, row in rows))
                self.processes = max(self.processes, len(rows))
                for pid, row in rows:
                    self.highwaters[pid] = max(self.highwaters.get(pid, 0),
                                              row.get("VmHWM", 0))
                self.stop.wait(.02)
        except BaseException as error:
            self.error = error

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *unused):
        self.stop.set()
        self.thread.join()
        if self.error is not None:
            raise self.error

    def report(self):
        return {
            "sample_interval_s": .02, "samples": self.samples,
            "sampled_aggregate_rss_peak_bytes": self.peak,
            "maximum_sampled_process_count": self.processes,
            "sum_observed_per_process_highwaters_bytes": sum(self.highwaters.values()),
            "worker_self_ru_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            "largest_reaped_child_ru_maxrss_bytes":
                resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss*1024,
            "scope": "Worker subtree only; enclosing Evidence orchestrator excluded. "
                     "Shared pages double-counted. Sampling can miss transient processes "
                     "and peaks; sum of observed highwaters is not a proven RSS bound.",
            "whole_process_memory_qualified": False,
        }


def xorshift(value):
    value ^= value << 13 & 0xffffffff
    value ^= value >> 17
    return (value ^ value << 5) & 0xffffffff


def availability():
    fields = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith(("MemTotal:", "MemAvailable:")):
            name, value, unit = line.split()
            require(unit == "kB", "unexpected Linux memory unit")
            fields[name[:-1]] = int(value)*1024
    # Observe the current unified cgroup and each finite ancestor limit.
    membership = Path("/proc/self/cgroup").read_text().splitlines()
    unified = [line.split(":", 2)[2] for line in membership if line.startswith("0::")]
    limits = []
    if unified:
        relative = Path(unified[0].lstrip("/"))
        require(".." not in relative.parts, "invalid unified cgroup membership")
        base = Path("/sys/fs/cgroup")
        group = base / relative
        while group.is_relative_to(base):
            maximum, current = group/"memory.max", group/"memory.current"
            if maximum.is_file() and current.is_file():
                raw, used = maximum.read_text().strip(), int(current.read_text())
                limits.append({"level": len(group.relative_to(base).parts),
                               "limit_bytes": None if raw == "max" else int(raw),
                               "observed_current_bytes": used,
                               "observed_headroom_bytes":
                                   None if raw == "max" else max(0, int(raw)-used)})
            if group == base:
                break
            group = group.parent
    finite = [row["observed_headroom_bytes"] for row in limits
              if row["observed_headroom_bytes"] is not None]
    return {**fields, "unified_cgroup_observations": limits,
            "effective_observed_available_bytes": min([fields["MemAvailable"], *finite]),
            "reserved_bytes": 0, "atomic_snapshot": False,
            "limitation": "Live host/cgroup observation, not exclusive or reserved capacity. "
                         "Unexposed cgroup ancestors and non-unified limits are unresolved."}


def assessment(directory):
    from collection_capacity import memory_accounting
    manifest = load_json(ROOT/"tests/data/model_manifest.json")
    suite = load_json(ROOT/"tests/data/benchmark_manifest.json")
    rows = []
    bindings = {}
    for group in suite["domains"].values():
        for case in group["cases"]:
            teacher, prompt = (ROOT/case[key]["path"]
                               for key in ("teacher_tokens", "prompt_tokens"))
            for path, key in ((teacher, "teacher_tokens"), (prompt, "prompt_tokens")):
                require(sha(path) == case[key]["sha256"], "capacity token binding changed")
                bindings[str(path.relative_to(ROOT))] = sha(path)
            rows.append({"teacher_positions": len(load_json(teacher)),
                         "greedy_positions_maximum": len(load_json(prompt))+127})
    require(len(rows) == 50, "memory assessment omitted full-suite cases")
    result = memory_accounting(rows)
    map_report = load_json(directory/"map.stdout")
    mapped = {}
    for mode, stream in manifest["streams"].items():
        size = 0
        for name in ("weights", "scales", "zeros"):
            if name in stream:
                path = ROOT/stream[name]["path"]
                # The enclosing Evidence source inventory independently hashes inputs.
                size += path.stat().st_size
        mapped[mode] = size
    node_bytes = map_report["requested_node_bytes"]
    # Treat every mapped weight byte as resident, never assume mmap is free.
    # The legacy flat-reference path also retains two complete mapped arrays.
    positions = result["largest_observer_positions"]
    mapped_weights = max(mapped.values())
    observer_payload = (
        result["observer_kv_entries"]*node_bytes +
        result["observer_scratch_value_and_initialized_bytes"] +
        mapped_weights + positions*64*4 +
        result["conservative_visible_codec_buffer_budget_bytes"] +
        4*151936*8 + 4*896*8)
    legacy_reference_mapping = result["largest_teacher_positions"]*(24*896+151936)*8
    reference_payload = (result["conservative_visible_reference_array_budget_bytes"] +
                         max(mapped_weights, sum((ROOT/item["path"]).stat().st_size
                                                 for item in manifest["checkpoint"])) +
                         result["conservative_visible_codec_buffer_budget_bytes"])
    visible_peak = max(observer_payload, reference_payload,
                       observer_payload+legacy_reference_mapping)
    observed = availability()
    return {
        "whole_workload": result, "token_sha256": bindings,
        "model_manifest_sha256": sha(ROOT/"tests/data/model_manifest.json"),
        "benchmark_manifest_sha256": sha(ROOT/"tests/data/benchmark_manifest.json"),
        "mapped_weight_file_bytes_by_mode": mapped,
        "mapped_weight_residency_policy": "Charge every mapped byte as resident, "
                                         "even though actual page residency is demand-driven.",
        "observed_kv_requested_node_bytes": node_bytes,
        "kv_requested_allocation_bytes": result["observer_kv_entries"]*node_bytes,
        "map_node_measurement_scope": "Exact std::map key/value type and compiler in a "
            "131072-entry synthetic process. Requested bytes exclude malloc metadata, "
            "arena fragmentation and retention; not an ABI-independent node-size bound.",
        "conservative_visible_payload_peak_budget_bytes": visible_peak,
        "phase_budgets_bytes": {"observer_packed": observer_payload,
                               "teacher_reference": reference_payload,
                               "observer_legacy_flat_references":
                                   observer_payload+legacy_reference_mapping},
        "unresolved_additive_peak_terms": [
            "C++ malloc metadata, arena fragmentation/retention, compiler-specific node "
            "layout outside the measured ABI, Verilated state and compiler/linker peak.",
            "Python/module/orchestrator metadata, zlib workspace, interpreter/allocator "
            "overhead and retained earlier-mode allocations.",
            "NumPy/BLAS workspace, internal temporary allocations and retention beyond "
            "the conservatively charged visible expressions; not executable in the "
            "currently selected shared-runtime interpreter.",
            "Mapped weight payload is fully charged above, but page tables, mapping "
            "objects, alignment and filesystem/kernel-cache overhead remain additional.",
            "Concurrent unrelated users/processes, unexposed cgroup constraints and "
            "non-atomic changes to the observed available memory.",
        ],
        "whole_process_peak_bound_bytes": None,
        "observed_availability": observed,
        "visible_payload_budget_within_observed_availability":
            visible_peak <= observed["effective_observed_available_bytes"],
        "full_workload_memory_qualified": False, "full_workload_storage_qualified": False,
        "collection_resumption_authorized": False,
        "scope": "Conservative visible-payload planning, not measured full inference, "
                 "reserved memory, an enforced cap or a complete-process upper bound.",
    }


def reference_fixtures(directory):
    directory.mkdir()
    results = {}
    for kind, shape, axes in (
        ("layers", [2, 24, 896], ["position", "layer", "component"]),
        ("logits", [151936, 2], ["vocabulary", "position"]),
    ):
        path = directory / (kind + ".aqp")
        # Integer IEEE encodings, including signed zeros and subnormals.
        values = (0, 1 << 63, 1, (1 << 63) | 1, 0x3ff0000000000000)
        total = 8
        for size in shape:
            total *= size
        digest = hashlib.sha256()
        with Writer(path, dtype="<f8", shape=shape, axes=axes) as writer:
            for start in range(0, total, CHUNK_BYTES):
                raw = b"".join(struct.pack("<Q", values[i % len(values)])
                               for i in range(start//8, min(start+CHUNK_BYTES, total)//8))
                writer.append(raw)
                digest.update(raw)
        require(b"".join(Reader(path).chunks()) == b"".join(
            struct.pack("<Q", values[i % len(values)]) for i in range(total//8)),
            "maximum-frame reference fixture changed bits")
        results[kind] = {"raw_sha256": digest.hexdigest(), "raw_bytes": total,
                         "file_sha256": sha(path)}
    return results


def consume(directory):
    reader = Reader(directory / "transactions.aqp")
    require(len(reader.entries) == 3 and
            reader.header["chunk_bytes"] == TRACE_CHUNK_BYTES,
            "maximum-frame diagnostic did not create three maximum frames")
    count = TRACE_CHUNK_BYTES // RECORD.size
    random_ = 17
    digest = hashlib.sha256()
    compared = 0
    for number in range(3):
        raw = reader.chunk(number)
        require(len(raw) == TRACE_CHUNK_BYTES, "nonmaximal diagnostic frame")
        digest.update(raw)
        for row in RECORD.iter_unpack(raw):
            random_ = xorshift(random_)
            i = compared
            cycle = (1 << 32) + i*9
            expected = (cycle & 0xffffffff, cycle >> 32, (cycle+3) & 0xffffffff,
                        (cycle+3) >> 32, i%2, i%13, i%24, i%7, i,
                        i ^ 0x12345678, random_ if i%2 else random_ ^ 0xffffffff)
            require(row == expected, "maximum-frame record/cycle/order/payload mismatch")
            compared += 1
        require(len(reader.cache) <= 2, "maximum-frame cache grew beyond two frames")
    require(list(reader.cache) == [1, 2], "maximum-frame cache eviction did not occur")
    last = raw
    del raw
    # Force eviction/reload while a caller still holds the previous frame.
    first = reader.chunk(0)
    require(first[:44] == RECORD.pack((1 << 32) & 0xffffffff, 1, 3, 1, 0, 0, 0, 0,
                                      0, 0x12345678, xorshift(17) ^ 0xffffffff) and
            reader.chunk(2) == last and len(reader.cache) == 2,
            "maximum-frame seek/reload changed retained bytes")
    return {"records_compared": compared, "frames": 3,
            "frame_raw_bytes": TRACE_CHUNK_BYTES, "raw_sha256": digest.hexdigest(),
            "cache_eviction_and_reload_checked": True, "codecs_mocked": False,
            "independent_producer_repeats": 1,
            "limitation": "Synthetic storage diagnostic, not model execution or repeat qualification."}


def run_child(directory, label, command):
    record = {"argv": command, "cwd": ".", "started_at": now(), "timeout_s": 3600,
              "stdout": str((directory/(label+".stdout")).relative_to(ROOT)),
              "stderr": str((directory/(label+".stderr")).relative_to(ROOT))}
    try:
        with (ROOT/record["stdout"]).open("xb") as out, \
                (ROOT/record["stderr"]).open("xb") as err:
            child = subprocess.run(command, cwd=ROOT, stdout=out, stderr=err,
                                   timeout=3600, check=False)
        record.update(exit_code=child.returncode, timed_out=False)
    except subprocess.TimeoutExpired:
        record.update(exit_code=None, timed_out=True)
        raise
    finally:
        record["ended_at"] = now()
        with (directory/(label+".command.json")).open("x") as output:
            json.dump(record, output, indent=2)
    require(child.returncode == 0, "memory diagnostic child failed: " + label)
    return record


def worker(args):
    directory = ROOT / args.destination
    with Monitor() as monitor:
        if args.worker == "producer":
            result = reference_fixtures(directory / "references")
            executable = directory / "producer"
            command = [str(executable.relative_to(ROOT)), "maximum-frame",
                       str((directory/"observations").relative_to(ROOT)),
                       str(TRACE_CHUNK_BYTES//44),
                       str((directory/"references/layers.aqp").relative_to(ROOT)),
                       str((directory/"references/logits.aqp").relative_to(ROOT)),
                       str((directory/"producer-count.txt").relative_to(ROOT))]
            run_child(directory, "maximum-frame-producer", command)
            require(int((directory/"producer-count.txt").read_text()) ==
                    3*(TRACE_CHUNK_BYTES//44), "producer frame count mismatch")
            result = {"reference_fixtures": result, "cpp_producer_completed": True}
        elif args.worker == "consumer":
            result = consume(directory / "observations")
        elif args.worker == "map":
            run_child(directory, "map-allocation", [
                str((directory/"map-fixture").relative_to(ROOT))])
            result = load_json(directory / "map-allocation.stdout")
        else:
            raise ValueError("invalid memory diagnostic worker")
    print(json.dumps({**result, "memory": monitor.report()}, indent=2))


def reassess(relative):
    """Recompute changed accounting without replaying unchanged codec probes."""
    ev = Evidence("memory-capacity-accounting")
    ok = False
    try:
        require(not relative.is_absolute() and ".." not in relative.parts,
                "nonportable preceding memory receipt")
        record = load_json(ROOT/relative)
        require(record["status"] == "passed", "preceding maximum-frame diagnostic failed")
        for name in SOURCES:
            if name != "tests/memory_capacity_checks.py":
                require(record["diagnostic_source_sha256"][name] == sha(ROOT/name),
                        "preceding allocation/codec source changed: "+name)
        source = relative.parent/"map.stdout"
        require(record["outputs"][str(source)] == sha(ROOT/source),
                "retained map diagnostic changed")
        ev.receipt["preceding_maximum_frame_diagnostic"] = {
            "path": str(relative), "sha256": sha(ROOT/relative)}
        with (ev.path/"map.stdout").open("xb") as output:
            output.write((ROOT/source).read_bytes())
        require(ev.run("assessment", [sys.executable, "tests/memory_capacity_checks.py",
            "--worker", "assessment", "--destination", str(ev.path.relative_to(ROOT))],
            timeout=3600), "changed memory accounting failed")
        result = load_json(ev.path/"assessment.stdout")
        require(result["whole_process_peak_bound_bytes"] is None and
                not result["full_workload_memory_qualified"] and
                not result["collection_resumption_authorized"],
                "partial accounting improperly qualified collection")
        ev.assertion("changed_memory_accounting_no_codec_replay", True, **result)
        ok = True
    except (ValueError, KeyError, OSError) as error:
        ev.assertion("memory_accounting_exception", False, diagnostic=repr(error))
    finally:
        ev.receipt["outputs"] = {
            str(path.relative_to(ROOT)): sha(path) for path in ev.path.rglob("*")
            if path.is_file() and path.name != "receipt.json"}
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path/"receipt.json").relative_to(ROOT)),
                      "production_collection_authorized": False}))
    return 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("producer", "consumer", "map", "assessment"))
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--assessment-of", type=Path)
    args = parser.parse_args()
    require(not (args.worker and args.assessment_of), "select one memory diagnostic operation")
    if args.worker:
        require(args.destination is not None and not args.destination.is_absolute() and
                ".." not in args.destination.parts, "nonportable diagnostic directory")
        if args.worker == "assessment":
            print(json.dumps(assessment(ROOT/args.destination), indent=2))
        else:
            worker(args)
        return 0
    if args.assessment_of:
        return reassess(args.assessment_of)
    ev = Evidence("maximum-frame-memory")
    ok = False
    try:
        prior = load_json(ROOT / PRIOR)
        require(prior["status"] == "passed", "preceding codec diagnostic missing")
        ev.receipt["preceding_diagnostic"] = {"path": PRIOR, "sha256": sha(ROOT / PRIOR)}
        ev.receipt["diagnostic_source_sha256"] = {name: sha(ROOT/name) for name in SOURCES}
        ev.receipt["purpose"] = "bounded-synthetic-maximum-frame-memory-not-capacity-admission"
        ev.receipt["codec_versions"] = {"zlib_build": zlib.ZLIB_VERSION,
                                       "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION}
        ev.receipt["observed_availability_before"] = availability()
        require(ev.receipt["observed_availability_before"][
                    "effective_observed_available_bytes"] >= 2*1024**3,
                "maximum-frame diagnostic needs observed 2 GiB memory headroom; "
                "nothing reserved")
        relative = str(ev.path.relative_to(ROOT))
        require(os.statvfs(ROOT).f_bavail * os.statvfs(ROOT).f_frsize > 1024**3,
                "diagnostic needs observed 1 GiB free scratch space; nothing reserved")
        for label, command in (
            ("cxx-version", ["c++", "--version"]),
            ("python-version", [sys.executable, "--version"]),
            ("compile-producer", ["c++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                "-Itests", "tests/packed_producer_fixture.cpp", "-lz", "-o",
                relative+"/producer"]),
            ("compile-map", ["c++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                "tests/memory_map_fixture.cpp", "-o", relative+"/map-fixture"]),
        ):
            require(ev.run(label, command, timeout=3600), label+" failed")
        reports = {}
        for operation in ("map", "producer", "consumer", "assessment"):
            require(ev.run(operation, [sys.executable, "tests/memory_capacity_checks.py",
                "--worker", operation, "--destination", relative], timeout=3600),
                operation+" memory diagnostic failed")
            reports[operation] = load_json(ev.path/(operation+".stdout"))
            ev.assertion(operation+"_bounded_memory_diagnostic", True,
                         **reports[operation])
        require(reports["producer"]["memory"]["maximum_sampled_process_count"] >= 7,
                "did not observe worker, C++ observer and five concurrent codec services")
        ev.assertion("five_concurrent_codec_children_observed", True,
                     full_workload_capacity_qualified=False,
                     collection_resumption_authorized=False)
        ev.receipt["limits"] = {
            "maximum_trace_frames": 3, "map_entries": 131072,
            "production_collection": False, "rtl_built": False, "inference": False,
            "dependencies_installed": False, "complete_capacity_proven": False}
        ok = True
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
        ev.assertion("maximum_frame_memory_exception", False, diagnostic=repr(error))
    finally:
        ev.receipt["outputs"] = {
            str(path.relative_to(ROOT)): sha(path) for path in ev.path.rglob("*")
            if path.is_file() and path.name != "receipt.json"}
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path/"receipt.json").relative_to(ROOT)),
                      "production_collection_authorized": False}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
