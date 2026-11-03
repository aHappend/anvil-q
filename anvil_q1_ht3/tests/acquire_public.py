"""Acquire only public HTTPS inputs, retaining bytes, provenance and failures."""

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
import urllib.parse
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
REVISIONS = {
    MODEL: "7ae557604adf67be50417f59c2c2f167def9a775",
    "openai/gsm8k": "740312add88f781978c0658806c59bc2815b9866",
    "openai/openai_humaneval": "7dce6050a7d6d172f3cc5c32aa97f52fa1a2e544",
    "cais/mmlu": "c30699e8356da336a370243923dbaf21066bb9fe",
    "allenai/ai2_arc": "210d026faf9955653af8916fad021475a3f00453",
    "Salesforce/wikitext": "b08601e04326c79dfdd32d625aee71d232d685c3",
}


def assets(output, first_rows=False):
    rows = []
    requests = [("model-files",
                 f"https://huggingface.co/api/models/{MODEL}/revision/{REVISIONS[MODEL]}?blobs=true")]
    for task, (repo, config, count) in DATASETS.items():
        arguments = dict(dataset=repo, config=config, split="test", revision=REVISIONS[repo])
        if not first_rows:
            arguments.update(offset=0, length=count)
        endpoint = "first-rows" if first_rows else "rows"
        requests.append((task, f"https://datasets-server.huggingface.co/{endpoint}?"+
                         urllib.parse.urlencode(arguments)))
        requests.append((task+"-parquet", "https://datasets-server.huggingface.co/parquet?"+
                         urllib.parse.urlencode(dict(dataset=repo, revision=REVISIONS[repo]))))
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json"):
        requests.append((name, f"https://huggingface.co/{MODEL}/resolve/{REVISIONS[MODEL]}/{name}"))
    for name, url in requests:
        row = dict(id=name)
        try:
            row.update(status="passed", acquisition=fetch(url, output/(name+".json")))
        except (OSError, ValueError, AssertionError) as exc:
            row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        rows.append(row)
    return dict(status="passed" if all(r["status"] == "passed" for r in rows) else "failed",
                records=rows)


def arc_pages(output):
    repo, config, _ = DATASETS["arc"]
    records = []
    for offset in range(0, 1200, 100):
        query = urllib.parse.urlencode(dict(dataset=repo, config=config, split="test",
                                            offset=offset, length=100))
        record = fetch("https://datasets-server.huggingface.co/rows?"+query,
                       output/f"arc-{offset:04d}.json")
        if record["headers"].get("x-revision") != REVISIONS[repo]:
            raise AssertionError("official ARC served a different dataset revision")
        records.append(record)
    return dict(status="passed", records=records)


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
    parser.add_argument("--assets", action="store_true")
    parser.add_argument("--first-rows", action="store_true")
    parser.add_argument("--arc-pages", action="store_true")
    parser.add_argument("--arc-original", action="store_true")
    parser.add_argument("--checkpoint", action="store_true")
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/acquire_public.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), tool_version=sys.version,
                   source_sha256=hashes())
    try:
        if args.arc_original:
            result = dict(status="passed", records=[fetch(
                "https://ai2-public-datasets.s3.amazonaws.com/arc/ARC-V1-Feb2018.zip",
                output/"arc-original.zip")])
        elif args.checkpoint:
            (output/"checkpoint-images").mkdir()
            result = dict(status="passed", records=[fetch(
                f"https://huggingface.co/{MODEL}/resolve/{REVISIONS[MODEL]}/model.safetensors",
                output/"checkpoint-images/model.safetensors",
                "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe")])
        else:
            result = (arc_pages(output) if args.arc_pages else
                  assets(output, args.first_rows) if args.assets else discover(output))
    except (OSError, ValueError, AssertionError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
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
