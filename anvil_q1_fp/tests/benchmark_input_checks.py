#!/usr/bin/env python3
"""Integrity and template checks for prepared inputs, not benchmark acceptance."""

import argparse
import ast
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import DOMAINS, load_json, require, sha
from benchmark_inputs import jsonl, verified_membership, write_json
from sequence_cases import generate

ROOT = Path(__file__).resolve().parents[1]


def artifact(descriptor):
    path = Path(descriptor["path"])
    require(not path.is_absolute() and ".." not in path.parts, "nonportable input path")
    full = ROOT / path
    require(full.resolve().is_relative_to(ROOT), "input escapes project")
    require(sha(full) == descriptor["sha256"], "input hash mismatch: " + str(path))
    return full


def document(descriptor):
    return load_json(artifact(descriptor))


def check_inputs(preparation):
    require(preparation["purpose"] == "canonical-input-preparation" and
            preparation["acceptance_evidence"] is False, "not input preparation")
    require(set(preparation["domains"]) == set(DOMAINS), "incorrect domain set")
    receipts = {key: document(value) for key, value in preparation["input_receipts"].items()}
    original = receipts["json_receipt"]["payloads"]
    math = jsonl(artifact(original["Math"]))
    code = jsonl(artifact(original["Code"]), compressed=True)
    membership = document(preparation["qa_membership"])
    wiki, attempted = [document(value)["Data"] for value in membership["sources"]]
    qa = {row["QuestionId"]: row for row in attempted
          if row["QuestionPartOfVerifiedEval"] is True}
    require(len(wiki) == 7993 and len(attempted) == 318 and len(qa) == 297,
            "unexpected original TriviaQA denominators")
    require(membership["eligible_ids"] == sorted(qa), "incorrect QA verified inventory")
    require(membership["rejected_attempt_ids"] ==
            sorted(row["QuestionId"] for row in attempted
                   if row["QuestionPartOfVerifiedEval"] is False),
            "unverified attempts were omitted or relabelled")
    logic_source = next(row for row in receipts["logic_receipt"]["retrievals"]
                        if row["path"].endswith("logical_deduction_three_objects.json"))
    logic = document(logic_source)["examples"]
    originals = {
        "Math": {f"{index:06d}": row for index, row in enumerate(math)},
        "Code": {row["task_id"]: row for row in code},
        "QA": qa,
        "Logic": {f"{index:06d}": row for index, row in enumerate(logic)},
        "Sequence": {row["id"]: row for row in generate()},
    }
    require({key: len(value) for key, value in originals.items()} ==
            {"Math": 1319, "Code": 164, "QA": 297, "Logic": 250, "Sequence": 10},
            "incomplete original corpora")
    selected_contents = []
    compared = 0
    for domain, group in preparation["domains"].items():
        inventory = document(group["canonical_inventory"])
        selected = document(group["selected"])
        require(group["dataset"] == DOMAINS[domain] and
                inventory["dataset"] == DOMAINS[domain] and
                inventory["revision"] == group["revision"], "inventory identity mismatch")
        require(inventory["ids"] == sorted(originals[domain]), "incomplete original ID inventory")
        require([row["id"] for row in selected] == sorted(originals[domain])[:10],
                "incorrect canonical first-ten selection")
        require(set(inventory["content_sha256"]) == set(originals[domain]),
                "incomplete canonical content hashes")
        directory = artifact(group["canonical_inventory"]).parent
        files = sorted(directory.glob("content-*.json"))
        require(len(files) == len(originals[domain]), "missing canonical content files")
        for path in files:
            content = load_json(path)
            identifier = content["id"]
            require(sha(path) == inventory["content_sha256"][identifier], "content hash mismatch")
            original_row = originals[domain][identifier]
            if domain == "Sequence":
                require(content == original_row, "Sequence content differs from published generator")
            else:
                require(content["source"] == original_row, "original record changed")
            if domain == "Math":
                require(content["answers"] == [original_row["answer"].split("####")[-1].strip()]
                        and content["prompt"].startswith(original_row["question"] + "\n"),
                        "GSM8K answer/prompt extraction differs")
            elif domain == "QA":
                require(content["verified"] is True and
                        original_row["QuestionPartOfVerifiedEval"] is True and
                        content["prompt"].startswith(original_row["Question"] + "\n") and
                        original_row["Answer"]["Value"] in content["answers"],
                        "unverified or changed QA case")
            elif domain == "Code":
                require(content["prompt"].endswith(original_row["prompt"]) and
                        content["answers"] == [original_row["canonical_solution"]],
                        "HumanEval source prompt/completion changed")
            elif domain == "Logic":
                require(content["prompt"].startswith(original_row["input"] + "\n") and
                        content["answers"] == [original_row["target"]], "Logic source changed")
            compared += 1
        selected_contents.extend((domain, row["id"], document(row["content"])) for row in selected)
    require(compared == 2040 and len(selected_contents) == 50, "input comparison denominator mismatch")

    # Explicitly reject attempts marked false, even if their documents are marked true.
    fixture = {
        "QuestionId": "fixture", "Question": "fixture",
        "Answer": {"Value": "value", "Aliases": ["value"]},
        "QuestionVerifiedEvalAttempt": True, "QuestionPartOfVerifiedEval": False,
        "EntityPages": [{"DocPartOfVerifiedEval": True}],
    }
    require(verified_membership([fixture], [fixture]) == [], "false verification attempt accepted")
    changed = {**fixture, "QuestionPartOfVerifiedEval": True, "Question": "changed"}
    try:
        verified_membership([fixture], [changed])
    except ValueError:
        pass
    else:
        raise ValueError("changed verification question was accepted")
    duplicated = [fixture, fixture]
    try:
        verified_membership(duplicated, [fixture])
    except ValueError:
        pass
    else:
        raise ValueError("duplicate original question ID was accepted")
    require(verified_membership([fixture], [{**fixture, "QuestionPartOfVerifiedEval": True,
                                           "EntityPages": []}])[0]["QuestionId"] == "fixture",
            "Wikipedia incorrectly requires Web-only document flags")

    sequence = generate()
    require(sequence == generate() and Counter(row["kind"] for row in sequence) ==
            {"exact-copy": 4, "reversal": 3, "key-retrieval": 3}, "Sequence reproducibility mismatch")
    for row in sequence:
        body = row["prompt"].split(":\n", 1)[1]
        if row["kind"] == "exact-copy":
            expected = body
        elif row["kind"] == "reversal":
            expected = " ".join(body.split()[::-1])
        else:
            query = row["prompt"].split("assigned to ", 1)[1].split(":", 1)[0]
            expected = dict(line.split("=", 1) for line in body.splitlines())[query]
        require(row["answers"] == [expected], "Sequence answer does not follow its instruction")
    return selected_contents, compared


def check_template(checkpoint, cases, destination):
    import jinja2
    from jinja2.sandbox import ImmutableSandboxedEnvironment

    configuration = load_json(checkpoint / "tokenizer_config.json")
    tokenizer = load_json(checkpoint / "tokenizer.json")
    vocab = load_json(checkpoint / "vocab.json")
    require(tokenizer["model"]["type"] == "BPE" and tokenizer["model"]["vocab"] == vocab,
            "tokenizer JSON and separate vocabulary disagree")
    merges = (checkpoint / "merges.txt").read_text().splitlines()
    if merges and merges[0].startswith("#version:"):
        merges = merges[1:]
    pairs = [line.split() for line in merges if line]
    require(all(len(row) == 2 for row in pairs), "malformed BPE merge pair")
    serialized_pairs = tokenizer["model"]["merges"]
    require(pairs == [row.split() if isinstance(row, str) else row for row in serialized_pairs],
            "tokenizer JSON and separate merge ranks disagree")
    added = {row["id"]: row["content"] for row in tokenizer["added_tokens"]}
    require(added == {int(key): value["content"]
                      for key, value in configuration["added_tokens_decoder"].items()},
            "added token identity differs between pinned artifacts")
    require(added[151644] == "<|im_start|>" and added[151645] == "<|im_end|>",
            "Qwen ChatML special IDs changed")
    template = configuration["chat_template"]
    with (destination / "chat_template.jinja").open("x") as stream:
        stream.write(template)
    environment = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
    compiled = environment.from_string(template)
    default_system = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."
    rendered = []
    for index, (domain, identifier, content) in enumerate(cases):
        messages = [{"role": "user", "content": content["prompt"]}]
        actual = compiled.render(messages=messages, tools=None, add_generation_prompt=True)
        expected = ("<|im_start|>system\n" + default_system + "<|im_end|>\n" +
                    "<|im_start|>user\n" + content["prompt"] + "<|im_end|>\n" +
                    "<|im_start|>assistant\n")
        require(actual == expected, "pinned template differs from explicit ChatML expectation")
        path = destination / f"rendered-{index:02d}.json"
        rendered.append({"domain": domain, "id": identifier,
                         "rendered": write_json(path, {"messages": messages, "text": actual})})
    explicit = [{"role": "system", "content": "Explicit system."},
                {"role": "user", "content": "Literal braces {{x}}\nUnicode: \u00e9"},
                {"role": "assistant", "content": "Previous answer."},
                {"role": "user", "content": "Next."}]
    expected = "".join("<|im_start|>" + row["role"] + "\n" + row["content"] +
                       "<|im_end|>\n" for row in explicit) + "<|im_start|>assistant\n"
    require(compiled.render(messages=explicit, tools=None, add_generation_prompt=True) == expected,
            "explicit-system/multi-turn template parity failed")
    return {
        "python_version": sys.version, "jinja2_version": jinja2.__version__,
        "vocabulary_entries_compared": len(vocab), "merge_ranks_compared": len(pairs),
        "added_tokens_compared": len(added), "rendered_cases": rendered,
        "tokenizer_dependencies": {name: importlib.util.find_spec(name) is not None
                                   for name in ("tokenizers", "transformers", "tiktoken")},
        "scope": "Template rendering and serialized tokenizer consistency only; "
                 "no token-ID backend parity or token arrays are claimed.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--checkpoint-dir", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    for name in ("preparation", "checkpoint_dir", "destination"):
        supplied = getattr(args, name)
        require(not supplied.is_absolute() and ".." not in supplied.parts,
                "arguments must use project-relative paths")
        path = (ROOT / supplied).resolve()
        require(path.is_relative_to(ROOT), "argument escapes project")
        setattr(args, name, path)
    for name in ("benchmark_inputs.py", "sequence_cases.py", "benchmark_input_checks.py"):
        ast.parse((ROOT / "tests" / name).read_text(), filename=name)
    args.destination.mkdir(parents=True, exist_ok=False)
    cases, compared = check_inputs(load_json(args.preparation))
    report = check_template(args.checkpoint_dir, cases, args.destination)
    report.update({"canonical_records_compared": compared, "selected_cases_compared": len(cases),
                   "membership_negative_cases": 3, "sequence_answer_comparisons": 10})
    write_json(args.destination / "input_integrity_report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
