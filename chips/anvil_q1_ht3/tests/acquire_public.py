"""Acquire only public HTTPS inputs, retaining bytes, provenance and failures."""

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, hashes, relative, remaining, timestamp


MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
DATASETS = {
    "gsm8k": ("openai/gsm8k", "main", 3),
    "humaneval": ("openai/openai_humaneval", "openai_humaneval", 3),
    "mmlu": ("cais/mmlu", "abstract_algebra", 3),
    "arc": ("allenai/ai2_arc", "ARC-Challenge", 3),
    "wikitext": ("Salesforce/wikitext", "wikitext-2-raw-v1", 100),
}


def fetch(url, destination, expected_sha256=None):
    if not url.startswith("https://"):
        raise ValueError("public acquisition requires HTTPS")
    destination.resolve().relative_to(ROOT)
    if destination.exists():
        raise FileExistsError(relative(destination))
    digest = hashlib.sha256()
    request = urllib.request.Request(url, headers={"User-Agent": "anvil-ht3-l1/3"})
    # The complete-check deadline, not a numerical/functional timeout.
    with urllib.request.urlopen(request, timeout=max(1, remaining())) as response:
        final_url = response.url
        if not final_url.startswith("https://"):
            raise ValueError("non-HTTPS public redirect")
        with destination.open("xb") as out:
            while True:
                block = response.read(1024*1024)
                if not block:
                    break
                digest.update(block)
                out.write(block)
        headers = dict(response.headers)
    actual = digest.hexdigest()
    if expected_sha256 is not None and actual != expected_sha256:
        raise AssertionError(f"public input SHA256 mismatch: {relative(destination)}")
    return dict(url=url, final_url=final_url, sha256=actual,
                bytes=destination.stat().st_size, headers=headers,
                path=relative(destination))


def discover(output):
    records, pins = [], {}
    for kind, name in [("models", MODEL), *[("datasets", v[0]) for v in DATASETS.values()]]:
        path = output / f"metadata-{len(records)}.json"
        row = dict(kind=kind, repository=name)
        try:
            record = fetch(f"https://huggingface.co/api/{kind}/{name}", path)
            metadata = json.loads(path.read_text())
            revision = metadata["sha"]
            if len(revision) != 40:
                raise AssertionError("repository response lacks immutable revision")
            pins[name] = revision
            row.update(status="passed", revision=revision, acquisition=record)
        except (OSError, ValueError, KeyError, AssertionError) as exc:
            row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        records.append(row)
    return dict(status="passed" if all(r["status"] == "passed" for r in records)
                else "failed", records=records, revisions=pins)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/acquire_public.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), tool_version=sys.version,
                   source_sha256=hashes())
    result = discover(output)
    with (output / "result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"] != "passed"),
                   timed_out=False, result=relative(output / "result.json"))
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
