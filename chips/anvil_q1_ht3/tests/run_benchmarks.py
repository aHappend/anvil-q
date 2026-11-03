"""Pinned official-input preparation and independent scoring for compiled RTL.

Preparation is not official-model verification. The default mandatory invocation
reports missing executed RTL observations as failure, never as a toy benchmark.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import urllib.parse
import uuid
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquire_public import fetch
from execution import ROOT, hashes, relative, remaining, timestamp
from official_reference import Checkpoint, Tokenizer, perplexity, scored_position


MANIFEST = ROOT / "tests/official_inputs.json"


def digest(path):
    with path.open("rb") as stream:
        sha = hashlib.sha256()
        while block := stream.read(1024*1024):
            sha.update(block)
    return sha.hexdigest()


def acquire(name, url, sha256, output, revision=None):
    directory = ROOT / f"evidence/official-image-{sha256[:24]}"
    directory.mkdir(parents=True, exist_ok=True)
    candidates = list(directory.glob(name))
    for root in (ROOT/"evidence/preparation").glob("ht3-official-*"):
        candidates.extend(root.glob(f"shard-*/{name}"))
        candidates.extend(root.glob(f"shard-*/{name}.json"))
        candidates.extend(root.glob(f"shard-*/checkpoint-images/{name}"))
    for candidate in candidates:
        if candidate.is_file() and digest(candidate) == sha256:
            return dict(path=relative(candidate), url=url, sha256=sha256, reused=True)
    target = directory / name
    if target.exists():
        # A corrupt cached input is preserved rather than silently replaced.
        directory = ROOT / f"evidence/official-image-{uuid.uuid4().hex[:24]}"
        directory.mkdir()
        target = directory / name
    start = timestamp()
    try:
        record = fetch(url, target, sha256)
        if revision is not None and record["headers"].get("x-revision") != revision:
            raise AssertionError(f"official dataset revision mismatch: {name}")
        return record
    finally:
        with (output / f"acquire-{name.replace('.', '-')}-{uuid.uuid4().hex[:8]}.json").open("x") as out:
            json.dump(dict(url=url, expected_sha256=sha256, start=start, end=timestamp(),
                           path=relative(target), complete=target.is_file(),
                           actual_sha256=digest(target) if target.is_file() else None), out, indent=2)


def official_records(task, pin, path):
    if task == "arc":
        with zipfile.ZipFile(path) as archive:
            rows = [json.loads(line) for line in archive.read(pin["archive_member"]).splitlines()]
        selected = sorted(rows, key=lambda row: row["id"])[:3]
        if [row["id"] for row in selected] != pin["selection"]:
            raise AssertionError("official ARC stable-ID selection changed")
        return [dict(id=row["id"], text=row) for row in selected]
    data = json.loads(path.read_text())
    if (data["dataset"], data["config"], data["split"]) != (
            pin["repository"], pin["config"], pin["split"]):
        raise AssertionError("official dataset/config/split mismatch")
    if any(row["truncated_cells"] for row in data["rows"]):
        raise AssertionError("official text contains truncated cells")
    if task == "wikitext":
        rows = data["rows"]
        start = next(i for i, row in enumerate(rows) if row["row"]["text"].strip())
        # Preserve the title and every newline in the first official article.
        end = next((i for i in range(start+1, len(rows))
                    if rows[i]["row"]["text"].startswith(" = ") and
                    not rows[i]["row"]["text"].startswith(" = = ")), len(rows))
        return [dict(id=f"test/{rows[start]['row_idx']:06d}",
                     text="".join(row["row"]["text"] for row in rows[start:end]),
                     source_rows=[row["row_idx"] for row in rows[start:end]])]
    rows = sorted(data["rows"], key=lambda row: row["row_idx"])[:3]
    if [row["row_idx"] for row in rows] != [0, 1, 2]:
        raise AssertionError("missing official stable source IDs")
    if task == "humaneval" and [row["row"]["task_id"] for row in rows] != [
            "HumanEval/0", "HumanEval/1", "HumanEval/2"]:
        raise AssertionError("HumanEval numeric task selection mismatch")
    if task == "mmlu" and any(row["row"]["subject"] != "abstract_algebra" for row in rows):
        raise AssertionError("MMLU first lexicographic subject mismatch")
    return [dict(id=row["row"].get("task_id", f"{pin['config']}/test/{row['row_idx']:06d}"),
                 text=row["row"]) for row in rows]


def prompt(task, row):
    if task == "gsm8k":
        return row["question"]+"\nShow your reasoning and give the final answer after ####.", row["answer"]
    if task == "humaneval":
        return "Complete the following Python function. Return code only.\n"+row["prompt"], row["canonical_solution"]
    if task == "mmlu":
        choices = "\n".join(f"{chr(65+i)}. {s}" for i, s in enumerate(row["choices"]))
        return row["question"]+"\n"+choices+"\nAnswer with the letter only.", chr(65+row["answer"])
    if task == "arc":
        choices = row["question"]["choices"]
        text = "\n".join(choice["label"]+". "+choice["text"] for choice in choices)
        return row["question"]["stem"]+"\n"+text+"\nAnswer with the label only.", row["answerKey"]
    raise ValueError(f"unsupported benchmark task {task}")


def workload(task, record, pin, tokenizer, template):
    if task == "wikitext":
        tokens = tokenizer.encode(record["text"])
        prefix, count = pin["context_prefix_tokens"], pin["scored_tokens"]
        if len(tokens) < prefix+count:
            raise AssertionError("first official WikiText passage is too short")
        tokens = tokens[:prefix+count]
        text, target = record["text"], None
    else:
        text, target = prompt(task, record["text"])
        prefix_text = template.render(messages=[dict(role="user", content=text)],
                                      tools=None, add_generation_prompt=True)
        prefix_ids = tokenizer.encode(prefix_text)
        tokens = tokenizer.encode(prefix_text+target)
        prefix = 0
        while prefix < min(len(prefix_ids), len(tokens)) and tokens[prefix] == prefix_ids[prefix]:
            prefix += 1
        if prefix == 0 or prefix >= len(tokens):
            raise AssertionError("official teacher-forcing prompt/target boundary is empty")
        count = len(tokens)-prefix
    if len(tokens) > 32768 or any(not 0 <= t < 151936 for t in tokens):
        raise AssertionError("official tokenization outside model contract")
    return dict(task=task, id=record["id"], prompt=text, target_text=target,
                token_ids=tokens, prefix_tokens=prefix, scored_tokens=count,
                # Logit at position p predicts target at p+1, not token p.
                scored_positions=list(range(prefix-1, len(tokens)-1)),
                shifted_targets=tokens[prefix:], seed=17, format="BF16",
                source_rows=record.get("source_rows"),
                token_sha256=hashlib.sha256(json.dumps(tokens).encode()).hexdigest())


def score_workload(work, actual, reference):
    """Compare every vocabulary vector before collecting likelihood or PPL."""
    expected_positions = work["scored_positions"]
    if list(actual) != expected_positions or list(reference) != expected_positions:
        raise AssertionError("missing, duplicated or out-of-order official scored logits")
    rows = []
    for position, target in zip(expected_positions, work["shifted_targets"]):
        if len(actual[position]) != 151936 or len(reference[position]) != 151936:
            raise AssertionError("official model logit vocabulary is not full Qwen")
        rows.append(dict(position=position,
                         **scored_position(actual[position], reference[position], target)))
    result = dict(task=work["task"], id=work["id"], scored_positions=rows,
                  total_nll=math.fsum(row["nll"] for row in rows),
                  teacher_forced_greedy_tokens=[row["greedy_token"] for row in rows])
    if work["task"] == "wikitext":
        result.update(perplexity(rows))
    if work["task"] == "humaneval":
        result["evaluation"] = "reference-code likelihood, not pass@1; no code execution"
    return result


def prepare(output, checkpoint=True):
    from jinja2.sandbox import ImmutableSandboxedEnvironment

    manifest = json.loads(MANIFEST.read_text())
    bindings, failures = {}, []
    model = manifest["model"]
    for name, sha in model["files"].items():
        if name == "model.safetensors" and not checkpoint:
            continue
        try:
            bindings[name] = acquire(name,
                f"https://huggingface.co/{model['repository']}/resolve/{model['revision']}/{name}",
                sha, output)
        except (OSError, ValueError, AssertionError) as exc:
            failures.append(dict(input=name, error=f"{type(exc).__name__}: {exc}"))
    for task, pin in manifest["datasets"].items():
        query = urllib.parse.urlencode(dict(dataset=pin["repository"], config=pin["config"],
                                            split=pin["split"], revision=pin["revision"]))
        url = pin.get("url", "https://datasets-server.huggingface.co/first-rows?"+query)
        try:
            name = "arc-original.zip" if task == "arc" else task+".json"
            bindings[task] = acquire(name, url, pin["sha256"], output,
                                     None if task == "arc" else pin["revision"])
        except (OSError, ValueError, AssertionError) as exc:
            failures.append(dict(input=task, error=f"{type(exc).__name__}: {exc}"))
    with (output/"public-inputs.json").open("x") as out:
        json.dump(dict(bindings=bindings, failures=failures, manifest_sha256=digest(MANIFEST)),
                  out, indent=2)
    required = ("config.json", "tokenizer.json", "tokenizer_config.json")
    if any(name not in bindings for name in required):
        return [], bindings, failures
    config = json.loads((ROOT/bindings["config.json"]["path"]).read_text())
    if (config["hidden_size"], config["intermediate_size"], config["num_hidden_layers"],
            config["vocab_size"]) != (896, 4864, 24, 151936):
        raise AssertionError("pinned model is not full Qwen2.5-0.5B")
    tokenizer = Tokenizer(ROOT/bindings["tokenizer.json"]["path"])
    tokenizer_config = json.loads((ROOT/bindings["tokenizer_config.json"]["path"]).read_text())
    template = ImmutableSandboxedEnvironment().from_string(tokenizer_config["chat_template"])
    works = []
    for task, pin in manifest["datasets"].items():
        if task not in bindings:
            continue
        for record in official_records(task, pin, ROOT/bindings[task]["path"]):
            work = workload(task, record, pin, tokenizer, template)
            works.append(work)
    if checkpoint and "model.safetensors" in bindings:
        checkpoint_data = Checkpoint(ROOT/bindings["model.safetensors"]["path"])
        if checkpoint_data.entries["model.embed_tokens.weight"]["shape"] != [151936, 896]:
            raise AssertionError("checkpoint embedding dimensions do not match official model")
    with (output/"workloads.json").open("x") as out:
        json.dump(works, out, indent=2)
    if not failures and len(works) != 13:
        raise AssertionError("official selection must contain 12 task records and one PPL passage")
    return works, bindings, failures


def checkpoint_image(output, bindings):
    from official_image import DEPENDENCIES, build

    pin = json.loads(MANIFEST.read_text())["model"]["files"]["model.safetensors"]
    config = ROOT/bindings["config.json"]["path"]
    current = hashes()
    candidates = []
    for parent in (ROOT/"evidence/l1", ROOT/"evidence/preparation"):
        candidates.extend(parent.glob(
            "*/*/checkpoint-images/official-image-*/image-manifest.json"))
    for path in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True):
        image = json.loads(path.read_text())
        if (image.get("status") != "passed" or image.get("checkpoint_sha256") != pin
                or image.get("config_sha256") != digest(config)
                or any(image.get("source_sha256", {}).get(p) != current[p] for p in DEPENDENCIES)):
            continue
        payload = ROOT/image["image"]
        if (not payload.is_file() or payload.stat().st_size != image["image_bytes"]
                or digest(payload) != image["image_sha256"]):
            continue
        return dict(manifest=relative(path), manifest_sha256=digest(path),
                    image=relative(payload), image_sha256=image["image_sha256"],
                    image_bytes=image["image_bytes"], reused=True)
    images = output/"checkpoint-images"
    images.mkdir()
    directory = images/f"official-image-{uuid.uuid4().hex[:12]}"
    image = build(directory, ROOT/bindings["model.safetensors"]["path"], config, pin)
    manifest = directory/"image-manifest.json"
    return dict(manifest=relative(manifest), manifest_sha256=digest(manifest),
                image=image["image"], image_sha256=image["image_sha256"],
                image_bytes=image["image_bytes"], reused=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_benchmarks.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    try:
        works, bindings, failures = prepare(output)
        rows = []
        image = None
        if not args.prepare_only:
            if not failures:
                image = checkpoint_image(output, bindings)
            # Explicit implementation gap, not replacement results from software.
            rows = [dict(task=w["task"], id=w["id"], status="not_executed",
                         required_scored_positions=w["scored_tokens"],
                         reason="default-geometry compiled RTL stream adapter "
                                "is not yet implemented") for w in works]
        result = dict(status="passed" if args.prepare_only and not failures else "failed",
                      mode="input preparation only" if args.prepare_only else "official RTL evaluation",
                      selected_records=len(works), acquisition_failures=failures, runs=rows,
                      input_bindings=bindings, checkpoint_image=image,
                      legacy=json.loads(MANIFEST.read_text())["legacy"],
                      coverage_limits=["No full-checkpoint RTL logits, native/represented-image "
                                       "FP64 comparisons, decoded completions, task metrics "
                                       "or RTL WikiText PPL have executed"])
    except (OSError, ValueError, AssertionError, KeyError, ImportError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    with (output/"result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"] != "passed"),
                   timed_out=remaining() <= 0, result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
