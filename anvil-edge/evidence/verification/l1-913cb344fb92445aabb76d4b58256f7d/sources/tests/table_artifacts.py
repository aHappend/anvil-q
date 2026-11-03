"""Fresh-invocation complete-table producers with explicit, hashed consumer paths."""

import hashlib
import json
from pathlib import Path
import threading
import uuid


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_producer(root, entry):
    from qwen_integration import validate_table_source

    relative = Path(entry["directory"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Complete-table producer must belong to this fresh invocation")
    directory = root.path / relative
    manifest_path = directory / "producer.json"
    if sha256(manifest_path) != entry["manifest_sha256"]:
        raise ValueError("Complete-table producer manifest changed")
    manifest = json.loads(manifest_path.read_bytes())
    if manifest["source_sha256"] != root.record["source_sha256"]:
        raise ValueError("Complete-table producer source identity changed")
    for name, expected in manifest["outputs"].items():
        path = directory / name
        if path.is_symlink() or sha256(path) != expected:
            raise ValueError("Complete-table producer output changed: " + name)
    info = json.loads((directory / "complete-table-fixture.json").read_bytes())
    validate_table_source(info, directory / "tables.hex")
    return directory, info


def complete_tables(evidence, family, *, model_bos=False):
    """Regenerate absent/stale prerequisites without touching earlier producer outputs."""
    from qwen_integration import save

    if family not in ("qwen", "deepseek") or (model_bos and family != "deepseek"):
        raise ValueError("Unsupported complete-table producer policy")
    root = evidence._root
    key = family + ("-bos" if model_bos else "-raw")
    with root._lock:
        lock = root._table_locks.setdefault(key, threading.Lock())
    with lock:
        entry = root.complete_table_producers.get(key)
        recovery = None
        if entry is not None:
            try:
                directory, info = validate_producer(root, entry)
            except (FileNotFoundError, ValueError) as error:
                recovery = {"previous_producer": dict(entry),
                            "reason": f"{type(error).__name__}: {error}"}
                root.record.setdefault("table_producer_recoveries", []).append(recovery)
                entry = None
        cache_hit = entry is not None
        if entry is None:
            directory = root.path / ("table-producer-" + key + "-" + uuid.uuid4().hex)
            directory.mkdir()
            argv = ["./.venv/bin/python", f"tests/{family}_integration.py",
                    evidence.relative(directory)]
            if model_bos:
                argv.append("--model-bos")
            child = evidence.child(argv, "complete-table-producer-" + key)
            outputs = {str(path.relative_to(directory)): sha256(path)
                       for path in sorted(directory.rglob("*")) if path.is_file()}
            manifest = {
                "family": family, "model_bos": model_bos,
                "source_sha256": root.record["source_sha256"],
                "outputs": outputs, "generation": child, "recovery": recovery,
            }
            save(directory / "producer.json", manifest)
            entry = {"directory": str(directory.relative_to(root.path)),
                     "manifest_sha256": sha256(directory / "producer.json")}
            directory, info = validate_producer(root, entry)
            root.complete_table_producers[key] = entry
            with root._lock:
                root.record.setdefault("complete_table_producers", []).append({
                    "key": key, "producer": evidence.relative(directory),
                    "manifest_sha256": entry["manifest_sha256"], "generation": child})
        binding = {
            "key": key, "cache_hit": cache_hit, "producer": evidence.relative(directory),
            "manifest_sha256": entry["manifest_sha256"],
            "table_source": evidence.relative(directory / "tables.hex"),
            "memory_hex_sha256": info["memory_hex_sha256"],
            "recovery": recovery,
        }
        save(evidence.path / ("table-binding-" + key + "-" + uuid.uuid4().hex + ".json"),
             binding)
        return directory, info
