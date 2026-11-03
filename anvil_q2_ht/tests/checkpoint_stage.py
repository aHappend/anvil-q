"""Stage genuine pinned public Qwen checkpoint inputs, without model dependencies."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import Experiment


REPOSITORIES = {
    "awq": "Qwen/Qwen2.5-1.5B-Instruct-AWQ",
    "bf16": "Qwen/Qwen2.5-1.5B-Instruct",
}


def metadata():
    result = {}
    for mode, repository in REPOSITORIES.items():
        url = "https://huggingface.co/api/models/" + repository + "?blobs=true"
        with urllib.request.urlopen(url, timeout=120) as response:
            raw = response.read()
        info = json.loads(raw)
        revision = info["sha"]
        if re.fullmatch("[0-9a-f]{40}", revision) is None:
            raise RuntimeError("remote did not return a pinned commit")
        files = []
        for item in info["siblings"]:
            name = item["rfilename"]
            if name in ("config.json", "generation_config.json", "README.md", "LICENSE",
                        "LICENSE.txt", "model.safetensors.index.json") or name.endswith(".safetensors"):
                files.append({"remote_path": name, "bytes": item.get("size"),
                              "lfs": item.get("lfs"), "git_blob_id": item.get("blobId")})
        if not any(item["remote_path"].endswith(".safetensors") for item in files):
            raise RuntimeError("official repository contains no safetensors checkpoint")
        result[mode] = {"repository": repository, "revision": revision,
                        "api_url": url, "api_sha256": hashlib.sha256(raw).hexdigest(),
                        "license_metadata": info.get("cardData", {}).get("license"),
                        "files": files, "metadata": info}
    return result


def stage(inputs, root):
    destination = root / "data/model"
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "official_inputs.json"
    if manifest_path.exists():
        raise RuntimeError("official input manifest already exists; retain it and use its pins")
    manifest = {"schema": 1, "synthetic": False, "sources": {}}
    for mode, info in inputs.items():
        entry = {key: info[key] for key in ("repository", "revision", "license_metadata")}
        entry["files"] = []
        for item in info["files"]:
            name = item["remote_path"]
            local = destination / (mode + "__" + name.replace("/", "__"))
            partial = local.with_name(local.name + ".partial")
            if partial.exists() or local.exists():
                raise RuntimeError("refusing to overwrite staged input " + str(local.relative_to(root)))
            url = ("https://huggingface.co/" + info["repository"] + "/resolve/" +
                   info["revision"] + "/" + urllib.parse.quote(name))
            digest = hashlib.sha256()
            size = 0
            with urllib.request.urlopen(url, timeout=300) as response, partial.open("xb") as output:
                while chunk := response.read(4 * 1024 * 1024):
                    output.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
            expected = (item.get("lfs") or {}).get("sha256")
            if item.get("bytes") is not None and size != item["bytes"]:
                raise RuntimeError("staged file length mismatch: " + name)
            if expected is not None and digest.hexdigest() != expected:
                raise RuntimeError("staged checkpoint LFS hash mismatch: " + name)
            partial.rename(local)
            entry["files"].append({"path": str(local.relative_to(root)), "remote_path": name,
                                   "bytes": size, "sha256": digest.hexdigest(), "url": url,
                                   "source_lfs_sha256": expected})
            print("STAGED", mode, name, size, digest.hexdigest(), flush=True)
        manifest["sources"][mode] = entry
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


def restore_pinned(root, output):
    manifest_path = root / "data/model/official_inputs.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("synthetic") is not False or set(manifest["sources"]) != set(REPOSITORIES):
        raise ValueError("invalid official input provenance manifest")
    for mode, entry in manifest["sources"].items():
        if entry["repository"] != REPOSITORIES[mode] or not re.fullmatch("[0-9a-f]{40}", entry["revision"]):
            raise ValueError("unexpected official repository or unpinned revision")
        for item in entry["files"]:
            local = Path(item["path"])
            if local.is_absolute() or local.parent != Path("data/model") or ".." in local.parts:
                raise ValueError("input target is outside the declared flat model directory")
            name = item["remote_path"]
            expected_url = ("https://huggingface.co/" + entry["repository"] + "/resolve/" +
                            entry["revision"] + "/" + urllib.parse.quote(name))
            if item["url"] != expected_url:
                raise ValueError("staged source URL differs from pinned official URL")
            target = root / local
            digest = hashlib.sha256()
            size = 0
            if target.exists():
                with target.open("rb") as stream:
                    while chunk := stream.read(4 * 1024 * 1024):
                        digest.update(chunk)
                        size += len(chunk)
            else:
                partial = root / output / (mode + "__" + name.replace("/", "__") + ".partial")
                with urllib.request.urlopen(expected_url, timeout=300) as response, partial.open("xb") as stream:
                    while chunk := response.read(4 * 1024 * 1024):
                        stream.write(chunk)
                        digest.update(chunk)
                        size += len(chunk)
            if digest.hexdigest() != item["sha256"] or size != item["bytes"]:
                raise ValueError("pinned input hash/length mismatch: " + str(local))
            if not target.exists():
                partial.rename(target)
            print("PINNED_INPUT_VERIFIED", local, size, digest.hexdigest(), flush=True)
    (root / output / "metadata.json").write_text(
        json.dumps({"pinned_manifest": str(manifest_path.relative_to(root)),
                    "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                    "sources": manifest["sources"]}, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--stage", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    if args.worker:
        if args.stage and (root / "data/model/official_inputs.json").is_file():
            restore_pinned(root, args.output)
        else:
            inputs = metadata()
            (root / args.output / "metadata.json").write_text(json.dumps(inputs, indent=2) + "\n")
            if args.stage:
                stage(inputs, root)
        print("OFFICIAL_METADATA repositories=2")
        return 0
    experiment = Experiment(root, args.output, sys.orig_argv,
                            ["tests/checkpoint_stage.py", "tests/retention.py"])
    try:
        experiment.run(["python3", "--version"], "python-version")
        argv = ["python3", "tests/checkpoint_stage.py", "--worker", "--output", str(args.output)]
        if args.stage:
            argv.append("--stage")
        text = experiment.run(argv, "stage" if args.stage else "metadata", timeout=14400)
        if "OFFICIAL_METADATA repositories=2" not in text:
            raise RuntimeError("missing metadata completion")
        experiment.receipt["metadata_sha256"] = hashlib.sha256(
            (experiment.directory / "metadata.json").read_bytes()).hexdigest()
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
