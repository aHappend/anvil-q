#!/usr/bin/env python3
"""Bounded, executable evidence replay. Digests never substitute for comparisons."""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time
import uuid

from benchmark import artifact_path, load_json, require, sha


FORMAT = "anvil-executable-replay-v1"
ROLES = ("observation", "repeat", "reference")
_HASHES = {}


def bound_hash(path):
    stat = path.stat()
    identity = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    if path not in _HASHES or _HASHES[path][0] != identity:
        digest = sha(path)
        after = path.stat()
        require(identity == (after.st_dev, after.st_ino, after.st_size,
                             after.st_mtime_ns, after.st_ctime_ns),
                "replay prerequisite changed during hashing: " + str(path.name))
        _HASHES[path] = identity, digest
    return _HASHES[path][1]


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def item(root, path):
    return dict(path=str(path.relative_to(root)), sha256=sha(path))


def write_new(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def checked(root, descriptor):
    require(isinstance(descriptor, dict) and set(descriptor) == {"path", "sha256"},
            "invalid replay prerequisite descriptor")
    path = artifact_path(root, descriptor["path"])
    require(path.is_file() and bound_hash(path) == descriptor["sha256"],
            "missing or altered replay prerequisite: " + descriptor["path"])
    return path


def code_bindings(root):
    return {str(path.relative_to(root)): bound_hash(path)
            for selector in ("rtl/*.sv", "design/*.md", "fpga/*", "tests/*",
                             "anvil_q1_reference/rtl/*.sv")
            for path in sorted(root.glob(selector)) if path.is_file()}


def data_bindings(root, *documents):
    result = {}

    def visit(value):
        if isinstance(value, dict):
            if "path" in value and "sha256" in value:
                descriptor = {key: value[key] for key in ("path", "sha256")}
                checked(root, descriptor)
                previous = result.setdefault(descriptor["path"], descriptor["sha256"])
                require(previous == descriptor["sha256"], "conflicting replay input hashes")
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    for document in documents:
        visit(document)
    return result


def tools(root, names):
    """Bind versions and installed executable bytes, not private installation paths."""
    result = {}
    for name in names:
        path = shutil.which(name)
        require(path is not None, "missing replay tool: " + name)
        argv = [name, "-V" if name in ("vvp", "iverilog") else "--version"]
        completed = subprocess.run(argv, cwd=root, capture_output=True,
                                   timeout=3600, check=False)
        require(completed.returncode == 0, "replay tool version failed: " + name)
        result[name] = dict(argv=argv, sha256=bound_hash(Path(path)),
                            version=(completed.stdout + completed.stderr).decode())
    return result


def specification(root, *, argv, output_index, role, case, mode, workload, tokens,
                  inputs, tool_names, fixture=False, build=None):
    require(role in ROLES and workload in ("teacher", "greedy"), "invalid replay role/workload")
    import numpy as np
    import numpy._core._multiarray_umath as arithmetic
    return dict(format=FORMAT, fixture=fixture, argv=argv, output_index=output_index,
                role=role, case=case, mode=mode, workload=workload, tokens=tokens,
                source_sha256=code_bindings(root), inputs=inputs,
                tools=tools(root, tool_names), reset_origin=True,
                dependencies=dict(numpy=np.__version__, arithmetic_sha256=sha(Path(arithmetic.__file__))),
                environment={"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
                             "MKL_NUM_THREADS": "1", "PYTHONDONTWRITEBYTECODE": "1"},
                build=build)


def validate_spec(root, spec, *, allow_fixture=False):
    import numpy as np
    import numpy._core._multiarray_umath as arithmetic
    require(spec["format"] == FORMAT and type(spec["fixture"]) is bool and
            (allow_fixture or not spec["fixture"]), "fixture cannot establish production replay")
    require(spec["role"] in ROLES and spec["reset_origin"] is True,
            "replay must originate from a separate reset execution")
    require(spec["source_sha256"] == code_bindings(root), "replay sources changed")
    require(isinstance(spec["inputs"], dict) and spec["inputs"], "missing replay inputs")
    for name, digest in spec["inputs"].items():
        checked(root, dict(path=name, sha256=digest))
    require(spec["tools"] and tools(root, spec["tools"]) == spec["tools"],
            "replay tools changed")
    require(spec["dependencies"] == dict(numpy=np.__version__,
                                        arithmetic_sha256=sha(Path(arithmetic.__file__))) and
            spec["environment"] == {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
                                    "MKL_NUM_THREADS": "1", "PYTHONDONTWRITEBYTECODE": "1"},
            "replay numerical dependencies/environment changed")
    argv = spec["argv"]
    require(isinstance(argv, list) and argv and all(isinstance(arg, str) for arg in argv) and
            type(spec["output_index"]) is int and 0 < spec["output_index"] < len(argv) and
            argv[spec["output_index"]] == "{output}", "invalid replay argv/output placeholder")
    require(all(not Path(arg).is_absolute() and "\0" not in arg and
                ".." not in Path(arg).parts for arg in argv),
            "nonportable replay argv")
    require(spec["tokens"] and all(type(token) is int and 0 <= token < 151936
                                  for token in spec["tokens"]), "invalid replay context")
    require(spec["workload"] in ("teacher", "greedy"), "invalid replay workload")
    if not spec["fixture"]:
        require(spec["mode"] in ("bf16", "fp16", "w4a16"), "invalid replay precision")
        manifests = [dict(path="tests/data/" + name + ".json",
                          sha256=spec["inputs"].get("tests/data/" + name + ".json"))
                     for name in ("model_manifest", "benchmark_manifest")]
        required_inputs = data_bindings(root, *[load_json(checked(root, entry))
                                                for entry in manifests])
        require(all(spec["inputs"].get(name) == digest
                    for name, digest in required_inputs.items()),
                "incomplete replay model/dataset input bindings")
        if spec["role"] == "reference":
            require(len(argv) == 9 and spec["output_index"] == 6 and
                    argv[:4] == ["python3", "tests/streaming_replay.py",
                                 "--reference-worker", "--tokens"] and
                    argv[5] == "--destination" and argv[7:] == ["--mode", spec["mode"]] and
                    argv[4] in spec["inputs"] and
                    load_json(checked(root, dict(path=argv[4],
                                                sha256=spec["inputs"][argv[4]]))) == spec["tokens"],
                    "replay is not independent FP64 inference")
        else:
            require("--stream-windows" == argv[-1] and argv[0] in spec["inputs"] and
                    len(argv) == 13 and argv[8:11] == ["preparation-only", "-", "-"] and
                    spec["output_index"] == 4,
                    "replay is not the reset-origin production RTL executable")
            for index in (1, 2, 3):
                require(argv[index] in spec["inputs"], "unbound replay memory/tokens/RoPE input")
            tokens = [int(line) for line in checked(
                root, dict(path=argv[2], sha256=spec["inputs"][argv[2]])).read_text().splitlines()]
            require(tokens == spec["tokens"] and argv[6] == spec["workload"] and
                    argv[5] == str({"bf16": 1, "fp16": 2, "w4a16": 0}[spec["mode"]]) and
                    argv[11] == str(len(tokens)), "replay precision/context command mismatch")
            from production_sim import identity
            build = load_json(checked(root, spec["build"]))
            require(build["build_sources"] == identity() and
                    build["executable"] == dict(path=argv[0], sha256=spec["inputs"][argv[0]]),
                    "replay executable is not bound to the current production build")
            origin = build if build["build_receipt"] is None else load_json(
                checked(root, build["build_receipt"]))
            require(any(record["label"] == "production-build" and
                        record["exit_code"] == 0 and not record["timed_out"]
                        for record in origin["records"]),
                    "missing successful RTL producing build")


def vector_layout(role):
    prefixes = ("selected-", "checkpoint-") if role == "reference" else ("",)
    wide = role == "reference"
    for prefix in prefixes:
        for layer in range(24):
            yield dict(name=prefix + "layers." + ("f64" if wide else "f32"),
                       dtype="<f8" if wide else "<f4", width=896,
                       offset=layer * 896 * (8 if wide else 4))
        yield dict(name=prefix + "logits." + ("f64" if wide else "f32"),
                   dtype="<f8" if wide else "<f4", width=151936, offset=0)


def vector_inventory(directory, role):
    result = []
    expected_sizes = {}
    for view in vector_layout(role):
        size = view["width"] * (8 if view["dtype"] == "<f8" else 4)
        path = directory / view["name"]
        expected_sizes[path] = max(expected_sizes.get(path, 0), view["offset"] + size)
        with path.open("rb") as stream:
            stream.seek(view["offset"])
            raw = stream.read(size)
        require(len(raw) == size, "truncated replay vector")
        result.append({**view, "sha256": hashlib.sha256(raw).hexdigest()})
    require(all(path.stat().st_size == size for path, size in expected_sizes.items()),
            "incomplete/extra replay array payload")
    return result


class Process:
    """One live producer, paused after a complete public-pin observation window."""

    def __init__(self, root, directory, spec, timeout, *, replay_of=None,
                 allow_fixture=False):
        self.root, self.directory, self.spec = root, directory, spec
        require(timeout >= 3600, "replay process allowance below 3600 seconds")
        validate_spec(root, spec, allow_fixture=allow_fixture)
        directory.mkdir(parents=True, exist_ok=False)
        self.output = directory / "payload"
        self.output.mkdir()
        argv = list(spec["argv"])
        argv[spec["output_index"]] = str(self.output.relative_to(root))
        self.stdout = (directory / "stdout.txt").open("xb")
        self.stderr = (directory / "stderr.txt").open("xb")
        self.record = dict(schema=1, execution_id=uuid.uuid4().hex,
                           role=spec["role"], reset_origin=True, replay_of=replay_of,
                           argv=argv, cwd=".", started_at=now(), timeout_s=timeout,
                           tool_version=spec["tools"], source_sha256=spec["source_sha256"],
                           inputs=spec["inputs"], dependencies=spec["dependencies"],
                           environment=spec["environment"], timed_out=False, exit_code=None)
        write_new(directory / "started.json", self.record)
        self.deadline = time.monotonic() + timeout
        self.process = subprocess.Popen(argv, cwd=root, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=self.stderr,
                                        env={**os.environ, **spec["environment"]})
        self.record["pid"] = self.process.pid
        self.lines = queue.Queue(maxsize=128)
        self.reader_stop = threading.Event()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        self.position = -1
        self.current = None
        self.windows = []
        self.finished = False

    def _read(self):
        try:
            for raw in iter(self.process.stdout.readline, b""):
                self.stdout.write(raw)
                self.stdout.flush()
                while not self.reader_stop.is_set():
                    try:
                        self.lines.put(raw, timeout=.1)
                        break
                    except queue.Full:
                        continue
        finally:
            self.process.stdout.close()
            while not self.reader_stop.is_set():
                try:
                    self.lines.put(None, timeout=.1)
                    break
                except queue.Full:
                    continue

    def line(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            self.record["timed_out"] = True
            raise ValueError("replay producer timed out")
        try:
            return self.lines.get(timeout=remaining)
        except queue.Empty as error:
            self.record["timed_out"] = True
            raise ValueError("replay producer timed out") from error

    def next(self):
        require(self.current is None, "unconsumed replay window")
        while True:
            line = self.line()
            require(line is not None, "producer ended before complete ordered coverage")
            if line.startswith(b"WINDOW_READY "):
                require(line == f"WINDOW_READY {self.position + 1}\n".encode(),
                        "incomplete/reordered replay coverage")
                break
        self.position += 1
        directory = self.output / f"position-{self.position}"
        require(directory.is_dir() and not directory.is_symlink(), "missing replay window")
        files = sorted(path for path in directory.iterdir() if path.is_file())
        require(files and all(not path.is_symlink() for path in directory.iterdir()),
                "missing or aliased replay payload")
        window = load_json(directory / "window.json")
        require(window["position"] == self.position and type(window["position"]) is int,
                "reordered payload position")
        tokens = self.spec["tokens"]
        require(self.position < len(tokens) or self.spec["workload"] == "greedy",
                "extra teacher position")
        if self.position < len(tokens):
            require(window["token_id"] == tokens[self.position], "replay context differs")
        self.current = dict(position=self.position, observation=window,
                            payloads=[dict(name=path.name, bytes=path.stat().st_size,
                                           sha256=sha(path)) for path in files])
        self.current["vectors"] = vector_inventory(directory, self.spec["role"])
        self.windows.append(self.current)
        write_new(self.directory / f"window-{self.position:05d}.json", self.current)
        return self.current

    def vector(self, name, dtype, width, offset=0):
        require(self.current is not None and dtype in ("<f4", "<f8") and
                type(width) is int and width > 0 and type(offset) is int and offset >= 0,
                "invalid replay vector extent")
        payload = next((entry for entry in self.current["payloads"]
                        if entry["name"] == name), None)
        require(payload is not None, "missing replay vector payload")
        path = self.output / f"position-{self.position}" / name
        require(path.stat().st_size == payload["bytes"] and sha(path) == payload["sha256"],
                "altered/truncated replay payload")
        size = width * (8 if dtype == "<f8" else 4)
        require(offset + size <= payload["bytes"], "truncated replay vector")
        with path.open("rb") as stream:
            stream.seek(offset)
            raw = stream.read(size)
        require(len(raw) == size, "truncated replay vector")
        return raw

    def release(self):
        """Only release this producer's newly created, verified transient window."""
        require(self.current is not None, "no replay window to release")
        directory = self.output / f"position-{self.position}"
        for entry in self.current["payloads"]:
            path = directory / entry["name"]
            require(path.is_file() and sha(path) == entry["sha256"],
                    "payload changed before release")
        for entry in self.current["payloads"]:
            (directory / entry["name"]).unlink()
        directory.rmdir()
        self.process.stdin.write(f"ACK {self.position}\n".encode())
        self.process.stdin.flush()
        self.current = None

    def finish(self):
        require(self.current is None, "last replay window was not consumed")
        while True:
            line = self.line()
            if line is None:
                break
            require(not line.startswith(b"WINDOW_READY "), "extra replay coverage")
        try:
            code = self.process.wait(timeout=max(1, self.deadline-time.monotonic()))
        except subprocess.TimeoutExpired as error:
            self.record["timed_out"] = True
            raise ValueError("replay producer timed out before exit") from error
        require(code == 0, "replay producing process failed")
        summary = load_json(self.output / "summary.json")
        require(type(summary["positions_completed"]) is int and
                summary["positions_completed"] == self.position + 1,
                "producer summary/ordered coverage differs")
        if not self.spec["fixture"]:
            if self.spec["role"] == "reference":
                require(summary["arithmetic"] == "ieee-fp64" and
                        summary["independent_of_rtl"] is True,
                        "not independent FP64 inference")
            else:
                require(type(summary["requests"]) is int and summary["requests"] > 0 and
                        summary["requests"] == summary["responses"],
                        "production transaction conservation failed")
                if self.spec["workload"] == "greedy":
                    expected = [entry["observation"]["argmax"] for entry in
                                self.windows[len(self.spec["tokens"])-1:]]
                    require(summary["generated_tokens"] == expected,
                            "greedy process summary differs from public logits")
        self._record(code)
        self.finished = True
        return self.record

    def _record(self, code):
        self.reader_stop.set()
        self.reader.join(timeout=5)
        self.process.stdin.close()
        self.stdout.close()
        self.stderr.close()
        self.record.update(exit_code=code, ended_at=now(),
                           stdout=item(self.root, self.directory / "stdout.txt"),
                           stderr=item(self.root, self.directory / "stderr.txt"),
                           window_indexes=[item(self.root, self.directory /
                                                f"window-{position:05d}.json")
                                           for position in range(len(self.windows))],
                           outputs=[item(self.root, path) for path in sorted(self.output.rglob("*"))
                                    if path.is_file()])
        write_new(self.directory / "process.json", self.record)

    def abort(self):
        if self.finished:
            return
        self.reader_stop.set()
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self._record(self.process.returncode)
        self.finished = True

    def seal(self):
        require(self.finished and self.record["exit_code"] == 0 and
                not self.record["timed_out"], "cannot seal a failed producer")
        manifest = dict(format=FORMAT, spec=self.spec, windows=self.windows,
                        producer=item(self.root, self.directory / "process.json"))
        path = self.directory / "replay.json"
        write_new(path, manifest)
        return item(self.root, path)


def validate_manifest(root, descriptor, *, role=None, allow_fixture=False):
    manifest = load_json(checked(root, descriptor))
    require(manifest["format"] == FORMAT, "not an executable replay manifest")
    spec = manifest["spec"]
    validate_spec(root, spec, allow_fixture=allow_fixture)
    require(role is None or spec["role"] == role, "substituted repeat/reference origin")
    producer = load_json(checked(root, manifest["producer"]))
    require(producer["role"] == spec["role"] and producer["reset_origin"] is True and
            producer["replay_of"] is None and producer["exit_code"] == 0 and
            producer["timed_out"] is False and producer["timeout_s"] >= 3600 and
            producer["cwd"] == "." and producer["source_sha256"] == spec["source_sha256"] and
            producer["inputs"] == spec["inputs"] and producer["tool_version"] == spec["tools"] and
            producer["dependencies"] == spec["dependencies"] and
            producer["environment"] == spec["environment"],
            "original producing execution missing/failed/substituted")
    require(isinstance(producer["execution_id"], str) and len(producer["execution_id"]) == 32 and
            type(producer["pid"]) is int and producer["pid"] > 0 and
            datetime.datetime.fromisoformat(producer["started_at"]) <
            datetime.datetime.fromisoformat(producer["ended_at"]),
            "missing original process identity/timestamps")
    argv = list(spec["argv"])
    actual = producer["argv"]
    require(len(actual) == len(argv), "original command differs from replay recipe")
    argv[spec["output_index"]] = actual[spec["output_index"]]
    require(argv == actual, "original command differs from replay recipe")
    for entry in (producer["stdout"], producer["stderr"], *producer["outputs"]):
        checked(root, entry)
    windows = manifest["windows"]
    require(isinstance(windows, list) and windows, "missing replay coverage")
    require((len(windows) == len(spec["tokens"]) if spec["workload"] == "teacher" else
             len(spec["tokens"]) <= len(windows) <= len(spec["tokens"])+127),
            "incomplete replay window coverage")
    for position, window in enumerate(windows):
        require(type(window["position"]) is int and window["position"] == position and
                window["observation"]["position"] == position,
                "incomplete/reordered replay coverage")
        payloads = window["payloads"]
        require(payloads and len({entry["name"] for entry in payloads}) == len(payloads) and
                all(Path(entry["name"]).name == entry["name"] and
                    type(entry["bytes"]) is int and entry["bytes"] > 0 and
                    len(entry["sha256"]) == 64 for entry in payloads),
                "incomplete/duplicate replay payload coverage")
        require([{key: entry[key] for key in ("name", "dtype", "width", "offset")}
                 for entry in window["vectors"]] == list(vector_layout(spec["role"])) and
                all(len(entry["sha256"]) == 64 for entry in window["vectors"]),
                "incomplete/reordered per-vector digest coverage")
        expected_files = {entry["name"] for entry in vector_layout(spec["role"])} | {"window.json"}
        if spec["role"] != "reference":
            expected_files.add("transactions.u32.gz")
        require({entry["name"] for entry in payloads} == expected_files,
                "missing/extra replay payload coverage")
    require(len(producer["window_indexes"]) == len(windows) and
            all(load_json(checked(root, entry)) == window
                for entry, window in zip(producer["window_indexes"], windows)),
            "manifest differs from original producing window indexes")
    return manifest, producer


def vector_descriptor(root, manifest_item, manifest, position, name, dtype, width, offset=0):
    window = manifest["windows"][position]
    payload = next(entry for entry in window["payloads"] if entry["name"] == name)
    # The full payload digest plus explicit extent binds views without pretending
    # a released file exists. Fresh replay verifies the whole payload before use.
    return dict(path=manifest_item["path"], sha256=manifest_item["sha256"],
                replay=dict(format=FORMAT, position=position, name=name, dtype=dtype,
                            width=width, offset=offset, payload_sha256=payload["sha256"]))


class Resolver:
    def __init__(self, root, ev, *, allow_fixture=False):
        self.root, self.ev, self.allow_fixture = root, ev, allow_fixture
        self.manifests = {}
        self.active = {}
        self.closed = False

    def bind(self, descriptor, role=None):
        manifest_item = {key: descriptor[key] for key in ("path", "sha256")}
        key = (manifest_item["path"], manifest_item["sha256"])
        if key not in self.manifests:
            manifest, producer = validate_manifest(
                self.root, manifest_item, role=role, allow_fixture=self.allow_fixture)
            self.manifests[key] = (manifest, producer, manifest_item)
        manifest, producer, _ = self.manifests[key]
        require(role is None or manifest["spec"]["role"] == role,
                "substituted repeat/reference origin")
        view = descriptor["replay"]
        require(set(view) == {"format", "position", "name", "dtype", "width", "offset",
                              "payload_sha256"} and view["format"] == FORMAT and
                type(view["position"]) is int and
                0 <= view["position"] < len(manifest["windows"]),
                "invalid replay vector descriptor")
        payload = next((entry for entry in manifest["windows"][view["position"]]["payloads"]
                        if entry["name"] == view["name"]), None)
        require(payload is not None and payload["sha256"] == view["payload_sha256"],
                "replay descriptor/payload coverage differs")
        require(view["dtype"] in ("<f4", "<f8") and type(view["width"]) is int and
                view["width"] > 0 and type(view["offset"]) is int and view["offset"] >= 0 and
                view["offset"] + view["width"] * (8 if view["dtype"] == "<f8" else 4) <=
                payload["bytes"], "invalid replay vector extent")
        return key, producer

    def _next(self, key, process):
        manifest = self.manifests[key][0]
        window = process.next()
        require(window == manifest["windows"][process.position],
                "replayed payload/ordered observation differs from original execution")

    def _finish(self, key):
        process = self.active.pop(key)
        try:
            if process.current is not None:
                process.release()
            while process.position + 1 < len(self.manifests[key][0]["windows"]):
                self._next(key, process)
                process.release()
            process.finish()
        finally:
            if not process.finished:
                process.abort()
            self.ev.receipt.setdefault("replay_executions", []).append(
                item(self.root, process.directory / "process.json"))

    def read(self, descriptor, dtype, width):
        require(not self.closed, "replay resolver is closed")
        key, _ = self.bind(descriptor)
        view = descriptor["replay"]
        require(view["dtype"] == dtype and view["width"] == width,
                "replay array type/width differs")
        if key in self.active and self.active[key].position > view["position"]:
            self._finish(key)
        if key not in self.active:
            # At most four complete windows (actual/repeat/selected/checkpoint).
            if len(self.active) == 4:
                self._finish(next(iter(self.active)))
            manifest, _, manifest_item = self.manifests[key]
            directory = self.ev.path / ("replay-" + uuid.uuid4().hex)
            self.active[key] = Process(
                self.root, directory, manifest["spec"], 86400, replay_of=manifest_item,
                allow_fixture=self.allow_fixture)
        process = self.active[key]
        while process.position < view["position"]:
            if process.current is not None:
                process.release()
            self._next(key, process)
        return process.vector(view["name"], dtype, width, view["offset"])

    def close(self, success):
        if self.closed:
            return
        self.closed = True
        try:
            if success:
                for key in list(self.active):
                    self._finish(key)
        finally:
            for process in self.active.values():
                process.abort()
                self.ev.receipt.setdefault("replay_executions", []).append(
                    item(self.root, process.directory / "process.json"))
            self.active.clear()


def reference_worker(args):
    from fp64_reference import QwenFP64
    from teacher_reference import selected_stream

    root = Path(__file__).resolve().parents[1]
    model = load_json(root / "tests/data/model_manifest.json")
    config = load_json(checked(root, model["config"]))
    tokens = load_json(artifact_path(root, args.tokens))
    destination = artifact_path(root, args.destination)
    selected = QwenFP64(config, selected_stream(model, args.mode), args.mode)
    checkpoint = QwenFP64(config, selected_stream(model, "checkpoint"), "checkpoint")
    for position, token in enumerate(tokens):
        directory = destination / f"position-{position}"
        directory.mkdir()
        for name, reference in (("selected", selected), ("checkpoint", checkpoint)):
            layers, logits = reference.step(token)
            for kind, values in (("layers", layers), ("logits", logits)):
                with (directory / f"{name}-{kind}.f64").open("xb") as output:
                    output.write(values.astype("<f8").tobytes())
        write_new(directory / "window.json", dict(position=position, token_id=token))
        print(f"WINDOW_READY {position}", flush=True)
        require(sys.stdin.readline() == f"ACK {position}\n", "reference window ACK missing")
    write_new(destination / "summary.json", dict(positions_completed=len(tokens),
                                                arithmetic="ieee-fp64",
                                                independent_of_rtl=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-worker", action="store_true", required=True)
    parser.add_argument("--tokens", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--mode", choices=("bf16", "fp16", "w4a16"), required=True)
    args = parser.parse_args()
    reference_worker(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
