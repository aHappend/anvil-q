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
_known_manifests = set()
_verified = {}
_PROTECTED = {".vulcan", ".git", ".tooling", "VULCAN"}


def _sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            value.update(block)
    return value.hexdigest()


def _stream_sha(stream):
    stream.seek(0)
    value = hashlib.sha256()
    while block := stream.read(1024 * 1024):
        value.update(block)
    return value.hexdigest(), stream.tell()


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
    for row in [*manifest["files"], *manifest.get("source_snapshots", [])]:
        if logical(row["path"]) != row["path"]:
            raise ValueError("noncanonical campaign dependency")
        object_path = ROOT / row["archive"]
        object_path.resolve().relative_to(STORE.resolve())
        _catalog.setdefault(row["path"], []).append((path, row))
    _known_manifests.add(path)
    return manifest


def _load():
    for path in sorted(STORE.glob("campaign-*/manifest-*.json")):
        if path not in _known_manifests:
            _read_manifest(path)


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
        if restored.exists():
            if (restored.is_file() and _sha(restored) == row["sha256"]
                    and stat.S_IMODE(restored.stat().st_mode) == row["mode"]):
                return restored
            raise ValueError(f"restored artifact changed: {relative(restored)}")
        del _restored[key]
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
    found, missing, expected, source_versions, parse_errors = {}, set(), {}, {}, []
    while pending:
        requested = Path(pending.pop())
        name = logical(requested)
        if name in found or name in missing:
            continue
        path = artifact(requested)
        if not path.is_file():
            missing.add(name)
            continue
        if path.is_symlink():
            raise ValueError(f"retention requires regular files: {name}")
        found[name] = path
        if path.suffix != ".json" or path.name in (
                "netlist.json", "statistics.json", "tokenizer.json"):
            continue
        try:
            values = [json.loads(artifact(path).read_text())]
        except FileNotFoundError:
            found.pop(name)
            missing.add(name)
            continue
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
                            target = source_versions if field == "source_sha256" else expected
                            target.setdefault(dependency, set()).add(sha)
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
                if (not candidate.is_file() and not candidate.suffix
                        and "/compile-obj/" not in value
                        and value not in expected and value not in source_versions):
                    continue
                pending.append(candidate)
    return found, sorted(missing), expected, parse_errors, source_versions


def preserve(paths, label):
    """Archive a dependency closure, round-trip checking every complete actual byte."""
    start = timestamp()
    _load()
    files, missing, expected, parse_errors, source_versions = dependencies(paths)
    rows = []
    for name, path in sorted(files.items()):
        try:
            source = artifact(ROOT/name).open("rb")
        except FileNotFoundError:
            missing.append(name)
            continue
        with source:
            sha, size = _stream_sha(source)
            mode = stat.S_IMODE(os.fstat(source.fileno()).st_mode)
            prior = next((row for _, row in _catalog.get(name, [])
                          if row["sha256"] == sha and row["mode"] == mode), None)
            if prior is not None:
                _verify_archive(prior)
                rows.append(prior)
                continue
            directory = STORE / f"object-{sha}-{uuid.uuid4().hex[:12]}"
            directory.mkdir(parents=True, exist_ok=False)
            archive = directory / "payload.bundle"
            source.seek(0)
            with archive.open("xb") as raw:
                with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=1, mtime=None) as target:
                    while block := source.read(1024 * 1024):
                        target.write(block)
            row = dict(path=name, sha256=sha, bytes=size, mode=mode,
                       archive=relative(archive), archive_bytes=archive.stat().st_size,
                       archive_sha256=_sha(archive))
            _verify_archive(row)
            if _stream_sha(source) != (sha, size):
                raise ValueError(f"artifact changed during retention: {name}")
            rows.append(row)
    observed = {row["path"]: row["sha256"] for row in rows}
    conflicts = [dict(path=name, recorded_sha256=sorted(sha), actual_sha256=observed[name])
                 for name, sha in sorted(expected.items())
                 if name in observed and (len(sha) != 1 or observed[name] not in sha)]
    snapshots, unavailable_versions = [], []
    for name, versions in sorted(source_versions.items()):
        for sha in sorted(versions):
            snapshot = next((row for row in rows
                             if row["path"] == name and row["sha256"] == sha), None)
            if snapshot is None:
                snapshot = next((row for _, row in _catalog.get(name, [])
                                 if row["sha256"] == sha), None)
            if snapshot is None:
                unavailable_versions.append(dict(path=name, sha256=sha))
            else:
                _verify_archive(snapshot)
                snapshots.append(snapshot)
    manifest = dict(schema=1, label=label, start=start, end=timestamp(),
                    complete=not missing and not conflicts and not parse_errors
                             and not unavailable_versions,
                    missing_dependencies=missing, dependency_parse_errors=parse_errors,
                    conflicting_dependencies=conflicts,
                    source_snapshots=snapshots, unavailable_source_versions=unavailable_versions,
                    roots=[logical(p) for p in paths], files=rows,
                    retention="gzip complete bytes; original paths and modes preserved; "
                              "restoration only to fresh project-owned destinations")
    return _publish(manifest)


def _publish(manifest):
    directory = STORE / f"campaign-{uuid.uuid4().hex[:12]}"
    directory.mkdir(parents=True, exist_ok=False)
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


def retain_replacement(replacement, original, expected_sha256, expected_bytes, cause):
    """Bind new actual bytes to an old identity only after exact independent equality."""
    replacement = Path(replacement)
    if replacement.stat().st_size != expected_bytes or _sha(replacement) != expected_sha256:
        raise ValueError("replacement differs from the original expected hash/length")
    source_manifest = preserve([replacement], "fresh exact-byte replacement input")
    source = json.loads(source_manifest.read_text())
    row = next(r for r in source["files"] if r["path"] == logical(replacement))
    alias = dict(row, path=logical(original))
    return _publish(dict(
        schema=1, label="explicit exact-byte replacement identity", start=timestamp(),
        end=timestamp(), complete=source["complete"], roots=[logical(replacement)],
        files=[row, alias], source_snapshots=[], missing_dependencies=[],
        conflicting_dependencies=[], dependency_parse_errors=[], unavailable_source_versions=[],
        replacement=dict(original=logical(original), actual=logical(replacement),
                         expected_sha256=expected_sha256, expected_bytes=expected_bytes,
                         source_manifest=relative(source_manifest), cause=cause)))


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
