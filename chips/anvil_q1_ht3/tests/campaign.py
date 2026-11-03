"""Lossless project-owned retention; restoration never overwrites original evidence."""

import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import uuid

from execution import ROOT, relative, timestamp


STORE = ROOT / "evidence/campaign"
_catalog = {}
_restored = {}
_loaded = False
_verified = {}
_PROTECTED = {".vulcan", ".git", ".tooling", "VULCAN"}


def _sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            value.update(block)
    return value.hexdigest()


def logical(path):
    path = Path(path)
    path = path if path.is_absolute() else ROOT / path
    name = relative(path)
    parts = Path(name).parts
    if (len(parts) > 4 and parts[:2] == ("evidence", "campaign")
            and parts[2].startswith("restored-") and parts[3] == "files"):
        name = Path(*parts[4:]).as_posix()
    if not name or Path(name).parts[0] in _PROTECTED:
        raise ValueError(f"not a project-owned retention input: {name}")
    return name


def _read_manifest(path):
    content = path.read_bytes()
    if path.name != f"manifest-{hashlib.sha256(content).hexdigest()}.json":
        raise ValueError(f"campaign manifest hash mismatch: {relative(path)}")
    manifest = json.loads(content)
    if manifest.get("schema") != 1:
        raise ValueError(f"unsupported campaign manifest: {relative(path)}")
    for row in manifest["files"]:
        if logical(row["path"]) != row["path"]:
            raise ValueError("noncanonical campaign dependency")
        object_path = ROOT / row["archive"]
        object_path.resolve().relative_to(STORE.resolve())
        _catalog.setdefault(row["path"], []).append((path, row))
    return manifest


def _load():
    global _loaded
    if not _loaded:
        for path in sorted(STORE.glob("campaign-*/manifest-*.json")):
            _read_manifest(path)
        _loaded = True


def _verify_archive(row):
    archive = ROOT / row["archive"]
    if not archive.is_file():
        raise FileNotFoundError(f"missing retained archive: {row['archive']}")
    info = archive.stat()
    key = (str(archive), info.st_size, info.st_mtime_ns, info.st_ctime_ns,
           row["archive_sha256"], row["archive_bytes"], row["sha256"], row["bytes"])
    if key in _verified:
        return
    if archive.stat().st_size != row["archive_bytes"] or _sha(archive) != row["archive_sha256"]:
        raise ValueError(f"retained archive hash/size mismatch: {row['archive']}")
    value, size = hashlib.sha256(), 0
    with gzip.open(archive, "rb") as stream:
        while block := stream.read(1024 * 1024):
            value.update(block)
            size += len(block)
    if size != row["bytes"] or value.hexdigest() != row["sha256"]:
        raise ValueError(f"retained payload hash/size mismatch: {row['path']}")
    _verified[key] = True


def artifact(path):
    """Resolve missing bytes into a fresh namespace; existing corrupt bytes stay errors."""
    path = Path(path)
    path = path if path.is_absolute() else ROOT / path
    name = logical(path)
    if path.is_file():
        return path
    if path.exists():
        raise ValueError(f"artifact is not a regular file: {relative(path)}")
    _load()
    if name not in _catalog:
        return path
    if len({(row["sha256"], row["mode"]) for _, row in _catalog[name]}) != 1:
        raise ValueError(f"ambiguous retained versions; explicit dependency required: {name}")
    manifest, row = _catalog[name][-1]
    key = (name, row["sha256"], row["mode"])
    if key in _restored:
        restored = _restored[key]
        if restored.is_file() and _sha(restored) == row["sha256"]:
            return restored
        raise ValueError(f"restored artifact changed: {relative(restored)}")
    _verify_archive(row)
    directory = STORE / f"restored-{uuid.uuid4().hex[:12]}"
    restored = directory / "files" / name
    restored.parent.mkdir(parents=True, exist_ok=False)
    start = timestamp()
    with gzip.open(ROOT / row["archive"], "rb") as source, restored.open("xb") as target:
        while block := source.read(1024 * 1024):
            target.write(block)
    restored.chmod(row["mode"])
    if restored.stat().st_size != row["bytes"] or _sha(restored) != row["sha256"]:
        raise ValueError(f"restored artifact hash/size mismatch: {relative(restored)}")
    receipt = dict(schema=1, kind="exact-byte-artifact-restoration", start=start,
                   end=timestamp(), original=name, restored=relative(restored),
                   manifest=relative(manifest), manifest_sha256=_sha(manifest), **row)
    with (directory / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    _restored[key] = restored
    return restored


def available(path):
    return artifact(path).is_file()


def canonical_argv(argv):
    """Compare actual relocated commands without changing their immutable receipts."""
    result = []
    for value in argv:
        if value.startswith("+") and "=" in value:
            prefix, candidate = value.split("=", 1)
            if candidate.startswith("evidence/"):
                value = prefix + "=" + logical(candidate)
        elif value.startswith("evidence/"):
            value = logical(value)
        result.append(value)
    return result


def dependencies(paths):
    """Capture existing JSON-declared files, recording missing obligations explicitly."""
    pending = list(paths)
    found, missing, expected, parse_errors = {}, set(), {}, []
    while pending:
        requested = Path(pending.pop())
        name = logical(requested)
        if name in found or name in missing:
            continue
        path = artifact(requested)
        if not path.is_file():
            missing.add(name)
            continue
        if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
            raise ValueError(f"retention requires regular files: {name}")
        found[name] = path
        if path.suffix != ".json" or path.name in (
                "netlist.json", "statistics.json", "tokenizer.json"):
            continue
        try:
            values = [json.loads(path.read_text())]
        except json.JSONDecodeError as exc:
            parse_errors.append(dict(path=name, error=str(exc)))
            continue
        while values:
            value = values.pop()
            if isinstance(value, dict):
                for field in ("artifact_sha256", "source_sha256"):
                    bindings = value.get(field)
                    if isinstance(bindings, dict):
                        for dependency, sha in bindings.items():
                            expected.setdefault(dependency, set()).add(sha)
                values.extend(value.keys())
                values.extend(value.values())
            elif isinstance(value, list):
                values.extend(value)
            elif isinstance(value, str) and value.startswith(
                    ("rtl/", "design/", "tests/", "evidence/",
                     "anvil_q1_ht2_reference/rtl/")):
                if value.startswith("evidence/campaign/"):
                    continue
                # Strings containing commands, globs or diagnostics are not filenames.
                if any(c in value for c in ("\n", " ", "*", ";", "=")):
                    continue
                candidate = ROOT / value
                candidate.resolve().relative_to(ROOT)
                if candidate.is_dir():
                    continue
                if value.endswith("/checkpoint"):
                    pending.extend(ROOT / (value + suffix)
                                   for suffix in (".rtl.bin", ".host.bin"))
                    continue
                pending.append(candidate)
    conflicts = [dict(path=name, recorded_sha256=sorted(sha), actual_sha256=_sha(found[name]))
                 for name, sha in sorted(expected.items())
                 if name in found and (len(sha) != 1 or _sha(found[name]) not in sha)]
    return found, sorted(missing), conflicts, parse_errors


def preserve(paths, label):
    """Archive a dependency closure, round-trip checking every complete actual byte."""
    start = timestamp()
    _load()
    files, missing, conflicts, parse_errors = dependencies(paths)
    rows = []
    for name, path in sorted(files.items()):
        sha = _sha(path)
        mode = stat.S_IMODE(path.stat().st_mode)
        prior = next((row for _, row in _catalog.get(name, [])
                      if row["sha256"] == sha and row["mode"] == mode), None)
        if prior is not None:
            _verify_archive(prior)
            rows.append(prior)
            continue
        directory = STORE / f"object-{sha}-{uuid.uuid4().hex[:12]}"
        directory.mkdir(parents=True, exist_ok=False)
        archive = directory / "payload.bundle"
        with path.open("rb") as source, archive.open("xb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=1, mtime=None) as target:
                while block := source.read(1024 * 1024):
                    target.write(block)
        row = dict(path=name, sha256=sha, bytes=path.stat().st_size, mode=mode,
                   archive=relative(archive), archive_bytes=archive.stat().st_size,
                   archive_sha256=_sha(archive))
        _verify_archive(row)
        if _sha(path) != sha:
            raise ValueError(f"artifact changed during retention: {name}")
        rows.append(row)
    directory = STORE / f"campaign-{uuid.uuid4().hex[:12]}"
    directory.mkdir(parents=True, exist_ok=False)
    manifest = dict(schema=1, label=label, start=start, end=timestamp(),
                    complete=not missing and not conflicts and not parse_errors,
                    missing_dependencies=missing, dependency_parse_errors=parse_errors,
                    conflicting_dependencies=conflicts,
                    roots=[logical(p) for p in paths], files=rows,
                    retention="gzip complete bytes; original paths and modes preserved; "
                              "restoration only to fresh project-owned destinations")
    content = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    path = directory / f"manifest-{hashlib.sha256(content).hexdigest()}.json"
    pending = directory / f"pending-{uuid.uuid4().hex[:12]}"
    with pending.open("xb") as out:
        out.write(content)
        out.flush()
        os.fsync(out.fileno())
    os.link(pending, path)
    pending.unlink()
    _read_manifest(path)
    return path


def preserve_tree(directory, label, extra=()):
    paths = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix in (".o", ".a", ".gch"):
            continue
        if "compile-obj" in path.parts and not (
                path.name == "driver.cpp" or os.access(path, os.X_OK)):
            continue
        paths.append(path)
    return preserve([*paths, *extra], label)
