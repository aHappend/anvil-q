"""Content-bound Verilator builds shared only inside one fresh verification run."""

import hashlib
import fcntl
import json
import os
from pathlib import Path
import shutil
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_verilator(experiment, argv, label="compile", cache=None):
    """Return a real executable; cache hits are observations, not tool executions."""
    mdir_index = argv.index("--Mdir") + 1
    binary = argv[argv.index("-o") + 1]
    if cache is None:
        experiment.run(argv, label)
        return str(Path(argv[mdir_index]) / binary)
    if cache.is_absolute() or ".." in cache.parts:
        raise ValueError("build cache must be project-relative")
    cache_directory = experiment.root / cache
    marker = json.loads((cache_directory / "run.json").read_text())
    if marker != {"schema": 1, "scope": "run-local-verilator", "directory": str(cache)}:
        raise RuntimeError("unrecognized run-local build cache")
    started = time.monotonic()
    versions = {}
    for tool in ("verilator", "g++", "make"):
        executable = shutil.which(tool)
        if executable is None:
            raise RuntimeError("missing build prerequisite: " + tool)
        text = experiment.run([tool, "--version"], label + "-" + tool + "-identity")
        versions[tool] = {"version": text, "executable_sha256": digest(Path(executable))}
    inputs = {}
    canonical = []
    for index, value in enumerate(argv):
        if index == mdir_index:
            canonical.append("<build-directory>")
        elif value.endswith(".sv"):
            path = Path(value)
            relative = path.relative_to(experiment.output)
            if relative.parts[0] not in ("sources", "mutant"):
                raise ValueError("compilation must use retained source snapshots")
            data = (experiment.root / path).read_bytes()
            if b"`include" in data:
                raise ValueError("cache requires explicit sources, not unresolved includes")
            name = str(relative)
            inputs[name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            canonical.append("<input>/" + name)
        else:
            canonical.append(value)
    if not inputs:
        raise ValueError("empty Verilator compilation")
    # Bind the complete environment by hash without retaining credentials or host paths.
    environment = hashlib.sha256(json.dumps(dict(os.environ), sort_keys=True).encode()).hexdigest()
    identity = {"schema": 1, "argv": canonical, "inputs": inputs, "tools": versions,
                "environment_sha256": environment}
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    entry = cache / key
    directory = experiment.root / entry
    executable = entry / "obj" / binary
    manifest_path = directory / "build.json"
    waiting = time.monotonic()
    with (cache_directory / (key + ".lock")).open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        lock_wait = time.monotonic() - waiting
        hit = directory.exists()
        if hit:
            if not manifest_path.is_file():
                raise RuntimeError("incomplete/failed build cache producer; retained at " + str(entry))
            manifest = json.loads(manifest_path.read_text())
            if manifest["identity"] != identity or manifest["exit"] != 0:
                raise RuntimeError("build cache identity/producer mismatch")
            if digest(experiment.root / executable) != manifest["executable_sha256"]:
                raise RuntimeError("build cache executable changed")
            for name, binding in inputs.items():
                if digest(directory / "input" / name) != binding["sha256"]:
                    raise RuntimeError("build cache source changed: " + name)
        else:
            directory.mkdir()
            try:
                for name in inputs:
                    target = directory / "input" / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes((experiment.directory / name).read_bytes())
                command = [
                    str(entry / "obj") if index == mdir_index else
                    str(entry / "input" / value[len("<input>/"):]) if value.startswith("<input>/") else value
                    for index, value in enumerate(canonical)]
                experiment.run(command, label)
                manifest = {"identity": identity, "exit": 0,
                            "producer_receipt": str(experiment.output / "receipt.json"),
                            "command": experiment.receipt["commands"][-1],
                            "executable": str(executable),
                            "executable_sha256": digest(experiment.root / executable)}
                with manifest_path.open("x") as stream:
                    json.dump(manifest, stream, indent=2)
                    stream.write("\n")
            except (OSError, RuntimeError, ValueError, KeyError) as error:
                with (directory / "build-failure.json").open("x") as stream:
                    json.dump({"producer_receipt": str(experiment.output / "receipt.json"),
                               "failure": str(error), "identity": identity}, stream, indent=2)
                    stream.write("\n")
                raise
    experiment.receipt.setdefault("builds", []).append({
        "label": label, "key": key, "cache_hit": hit, "manifest": str(entry / "build.json"),
        "producer_receipt": manifest["producer_receipt"], "executable": str(executable),
        "executable_sha256": manifest["executable_sha256"],
        "compile_duration_s": 0 if hit else manifest["command"]["duration_s"],
        "producer_lock_wait_s": lock_wait,
        "lookup_and_build_duration_s": time.monotonic() - started})
    return str(executable)


def create_cache(root, path):
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("build cache must be project-relative")
    directory = root / path
    directory.mkdir(parents=True, exist_ok=False)
    with (directory / "run.json").open("x") as stream:
        json.dump({"schema": 1, "scope": "run-local-verilator", "directory": str(path)}, stream)
        stream.write("\n")
