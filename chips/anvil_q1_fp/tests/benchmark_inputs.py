#!/usr/bin/env python3
"""Prepare canonical benchmark inputs; never manufacture execution evidence."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import DOMAINS, Validator, load_json
from input_prerequisites import fetch
from sequence_cases import generate
from verify import Evidence, ROOT, digest


UPSTREAMS = {
    "Math": "openai/grade-school-math",
    "Code": "openai/human-eval",
    "QA": "mandarjoshi90/triviaqa",
}


def bind_receipt(ev, name, path):
    path = ROOT / path
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError("receipt escapes project")
    record = load_json(path)
    ev.receipt[name] = {"path": str(path.relative_to(ROOT)), "sha256": digest(path)}
    return record


def upstream_inventory(ev):
    ok = ev.run("curl-version", ["curl", "--version"], timeout=30)
    for domain, repo in UPSTREAMS.items():
        metadata = fetch(ev, domain + "-commit",
                         f"https://api.github.com/repos/{repo}/commits/HEAD")
        if metadata is None:
            ok = False
            continue
        revision = load_json(metadata)["sha"]
        if not re.fullmatch("[0-9a-f]{40}", revision):
            raise ValueError("upstream did not return an immutable commit")
        tree = fetch(ev, domain + "-tree",
                     f"https://api.github.com/repos/{repo}/git/trees/{revision}?recursive=1")
        readme = fetch(ev, domain + "-readme",
                       f"https://raw.githubusercontent.com/{repo}/{revision}/README.md")
        ok = tree is not None and readme is not None and ok
        if tree is not None and load_json(tree).get("truncated", True):
            raise ValueError("incomplete upstream tree")
        ev.receipt.setdefault("upstreams", {})[domain] = {
            "repository": repo, "revision": revision,
            "tree": str(tree.relative_to(ROOT)) if tree else None,
            "readme": str(readme.relative_to(ROOT)) if readme else None,
        }
    ev.receipt["scope"] = (
        "Pinned documented upstream inventories/readmes only; no downloaded code execution, "
        "dataset substitution, dependency installation or benchmark execution.")
    return ev.assertion("official_upstream_inventory", ok)


def json_acquisition(ev, upstream_receipt):
    previous = bind_receipt(ev, "upstream_receipt", upstream_receipt)
    if previous["status"] != "passed":
        raise ValueError("upstream discovery did not complete")
    destination = ROOT / "tests/data/acquired" / ev.path.name
    destination.mkdir(parents=True, exist_ok=False)
    ok = ev.run("curl-version", ["curl", "--version"], timeout=30)
    for domain, name in (
        ("Math", "grade_school_math/data/test.jsonl"),
        ("Code", "data/HumanEval.jsonl.gz"),
    ):
        item = previous["upstreams"][domain]
        if item["repository"] != UPSTREAMS[domain]:
            raise ValueError("unexpected official upstream")
        tree = load_json(ROOT / item["tree"])
        if name not in {row["path"] for row in tree["tree"] if row["type"] == "blob"}:
            raise ValueError("payload missing from pinned upstream inventory")
        output = destination / domain / Path(name).name
        output.parent.mkdir()
        payload = fetch(ev, domain + "-json",
                        f"https://raw.githubusercontent.com/{item['repository']}/"
                        f"{item['revision']}/{name}", output)
        ok = payload is not None and ok
        ev.receipt.setdefault("payloads", {})[domain] = {
            **item, "path": str(output.relative_to(ROOT)),
            "sha256": digest(output) if payload else None,
        }
    website = fetch(ev, "QA-official-website", "https://nlp.cs.washington.edu/triviaqa/")
    ok = website is not None and ok
    dependencies = (
        "import importlib.util,json,sys; print(json.dumps({'version':sys.version,"
        "'dependencies':{n:importlib.util.find_spec(n) is not None for n in "
        "('regex','jinja2','tokenizers','transformers','pyarrow','fastparquet','duckdb','polars')}}))")
    ok = ev.run("existing-default-python-input-dependencies",
                [sys.executable, "-c", dependencies], timeout=30) and ok
    ev.receipt["scope"] = (
        "Immutable official Math/Code JSON payloads and documented TriviaQA download links; "
        "not a verified QA inventory, pinned-corpus parity or tokenization result.")
    return ev.assertion("json_acquisition_and_qa_source_discovery", ok)


def qa_archive(ev, discovery_receipt):
    previous = bind_receipt(ev, "discovery_receipt", discovery_receipt)
    website_record = next(row for row in previous["retrievals"]
                          if row["url"] == "https://nlp.cs.washington.edu/triviaqa/")
    website = ROOT / website_record["path"]
    if not website_record["complete"] or digest(website) != website_record["sha256"]:
        raise ValueError("official QA website binding failed")
    if 'href="data/triviaqa-rc.tar.gz"' not in website.read_text():
        raise ValueError("RC archive not linked from the official website")
    destination = ROOT / "tests/data/acquired" / ev.path.name / "QA"
    destination.mkdir(parents=True, exist_ok=False)
    if not ev.run("curl-version", ["curl", "--version"], timeout=30):
        return False
    payload = fetch(ev, "QA-rc-archive",
                    "https://nlp.cs.washington.edu/triviaqa/data/triviaqa-rc.tar.gz",
                    destination / "triviaqa-rc.tar.gz", allowance=3600)
    if payload is None:
        return False
    ok = ev.run("QA-archive-inventory", [
        sys.executable, "tests/benchmark_inputs.py", "--inspect-qa",
        str(payload.relative_to(ROOT)), "--destination",
        str(destination.relative_to(ROOT))], timeout=3600)
    ev.receipt["outputs"] = {
        str(path.relative_to(ROOT)): digest(path)
        for path in destination.iterdir() if path.is_file()}
    ev.receipt["scope"] = (
        "Official TriviaQA v1.0 RC archive retained by exact bytes/hash, with QA JSON only "
        "copied as data after safe member inspection. No downloaded code executes; "
        "verified membership and pinned-split correspondence still require comparison.")
    return ev.assertion("official_qa_archive_inventory", ok)


def qa_membership_diagnostic(ev, args):
    archive = bind_receipt(ev, "qa_receipt", args.qa_receipt)
    upstream = bind_receipt(ev, "upstream_receipt", args.upstream_receipt)
    qa_directory = ROOT / "tests/data/acquired" / Path(args.qa_receipt).parent.name / "QA"
    path = qa_directory / "verified-wikipedia-dev.json"
    checked_payload(ev, {"path": str(path.relative_to(ROOT)),
                         "sha256": archive["outputs"][str(path.relative_to(ROOT))]})
    ok = ev.run("verified-membership-flags", [
        sys.executable, "-c",
        "import json,sys,collections; rows=json.load(open(sys.argv[1]))['Data']; "
        "print(json.dumps({'attempts':len(rows),'question_flags':dict(collections.Counter("
        "str(r.get('QuestionPartOfVerifiedEval')) for r in rows)),"
        "'question_true_without_document_true':[{'id':r['QuestionId'],"
        "'pages':r['EntityPages']} for r in rows if r.get('QuestionPartOfVerifiedEval') is True "
        "and not any(p.get('DocPartOfVerifiedEval') is True for p in r['EntityPages'])]},indent=2))",
        str(path.relative_to(ROOT))], timeout=60)
    item = upstream["upstreams"]["QA"]
    for index, name in enumerate(("utils/utils.py", "evaluation/triviaqa_evaluation.py")):
        payload = fetch(ev, f"QA-upstream-membership-source-{index}",
                        f"https://raw.githubusercontent.com/{item['repository']}/"
                        f"{item['revision']}/{name}")
        ok = payload is not None and ok
    ev.receipt["scope"] = (
        "Diagnose retained canonical-input failure by counting original membership fields and "
        "reading pinned official evaluation sources as data; downloaded code is not executed.")
    return ev.assertion("verified_membership_discriminating_diagnostic", ok)


def qa_membership_source(ev, args):
    upstream = bind_receipt(ev, "upstream_receipt", args.upstream_receipt)
    item = upstream["upstreams"]["QA"]
    payload = fetch(ev, "QA-dataset-utils",
                    f"https://raw.githubusercontent.com/{item['repository']}/"
                    f"{item['revision']}/utils/dataset_utils.py")
    ev.receipt["scope"] = "Pinned official membership helper retained as data; never executed."
    return payload is not None


def inspect_qa(archive, destination):
    inventory = []
    with tarfile.open(archive, "r|gz") as stream:
        for member in stream:
            inventory.append({"name": member.name, "size": member.size,
                              "regular_file": member.isfile()})
            name = Path(member.name)
            if (member.isfile() and name.suffix == ".json" and
                    "qa" in name.parts and "wikipedia" in name.name and
                    "dev" in name.name):
                if member.size > 100 * 1024 * 1024:
                    raise ValueError("unexpected QA JSON size")
                with stream.extractfile(member) as source:
                    payload = source.read()
                with (destination / name.name).open("xb") as output:
                    output.write(payload)
                print(json.dumps({"member": member.name, "bytes": len(payload),
                                  "sha256": digest(destination / name.name)}), flush=True)
    with (destination / "archive_inventory.json").open("x") as output:
        json.dump(inventory, output, indent=2)
        output.write("\n")
    selected = list(destination.glob("*wikipedia*dev*.json"))
    if not selected:
        raise ValueError("archive lacks Wikipedia validation JSON")
    print(json.dumps({"members": len(inventory), "selected": [p.name for p in selected]}))


def write_json(path, value):
    with path.open("x") as output:
        json.dump(value, output, ensure_ascii=True, sort_keys=True, indent=2,
                  allow_nan=False)
        output.write("\n")
    return {"path": str(path.relative_to(ROOT)), "sha256": digest(path)}


def checked_payload(ev, record):
    path = ROOT / record["path"]
    if not path.resolve().is_relative_to(ROOT) or digest(path) != record["sha256"]:
        raise ValueError("payload binding failed: " + record["path"])
    ev.receipt.setdefault("data_sha256", {})[record["path"]] = record["sha256"]
    return path


def unique_rows(rows, key):
    result = {}
    for row in rows:
        identifier = row[key]
        if not isinstance(identifier, str) or not identifier or identifier in result:
            raise ValueError("invalid or duplicate original ID")
        result[identifier] = row
    return result


def verified_membership(base, attempts):
    base_by_id = unique_rows(base, "QuestionId")
    attempts_by_id = unique_rows(attempts, "QuestionId")
    eligible = []
    for identifier, row in attempts_by_id.items():
        if identifier not in base_by_id:
            raise ValueError("verified attempt absent from Wikipedia validation")
        original = base_by_id[identifier]
        if (row["Question"] != original["Question"] or
                row["Answer"]["Value"] != original["Answer"]["Value"] or
                set(row["Answer"]["Aliases"]) != set(original["Answer"]["Aliases"])):
            raise ValueError("verified record differs from validation question/answer")
        if row.get("QuestionVerifiedEvalAttempt") is not True:
            raise ValueError("record lacks explicit verified-evaluation attempt")
        flag = row.get("QuestionPartOfVerifiedEval")
        if type(flag) is not bool:
            raise ValueError("missing verified membership decision")
        if flag:
            eligible.append(row)
    return sorted(eligible, key=lambda row: row["QuestionId"])


def jsonl(path, compressed=False):
    opener = gzip.open if compressed else open
    with opener(path, "rt", encoding="utf-8") as source:
        rows = []
        for line in source:
            # Use the same strict decoder as the acceptance validator.
            class Line:
                def read_text(self):
                    return line
            row = load_json(Line())
            if not isinstance(row, dict):
                raise ValueError("JSONL record is not an object")
            rows.append(row)
    return rows


def canonical(ev, args):
    metadata = bind_receipt(ev, "metadata_receipt", args.metadata_receipt)
    acquired = bind_receipt(ev, "json_receipt", args.json_receipt)
    archive = bind_receipt(ev, "qa_receipt", args.qa_receipt)
    logic = bind_receipt(ev, "logic_receipt", args.logic_receipt)
    membership_source = bind_receipt(ev, "membership_receipt", args.membership_receipt)
    if any(row["status"] != "passed"
           for row in (metadata, acquired, archive, logic, membership_source)):
        raise ValueError("canonical preparation requires completed input acquisitions")
    for record in membership_source["retrievals"]:
        if record["complete"]:
            checked_payload(ev, record)
        else:
            raise ValueError("official membership semantics acquisition incomplete")
    math = jsonl(checked_payload(ev, acquired["payloads"]["Math"]))
    code = jsonl(checked_payload(ev, acquired["payloads"]["Code"]), compressed=True)
    qa_directory = ROOT / "tests/data/acquired" / Path(args.qa_receipt).parent.name / "QA"
    qa_paths = [qa_directory / name for name in
                ("wikipedia-dev.json", "verified-wikipedia-dev.json")]
    for path in qa_paths:
        name = str(path.relative_to(ROOT))
        checked_payload(ev, {"path": name, "sha256": archive["outputs"][name]})
    base_document, verified_document = [load_json(path) for path in qa_paths]
    if (base_document["Domain"] != "Wikipedia" or
            verified_document["Domain"] != "Wikipedia" or
            verified_document["VerifiedEval"] is not True or
            base_document["VerifiedEval"] is not False):
        raise ValueError("not original Wikipedia validation and verified-evaluation sources")
    base, attempts = base_document["Data"], verified_document["Data"]
    qa = verified_membership(base, attempts)
    logic_payload = next(row for row in logic["retrievals"]
                         if row["path"].endswith("logical_deduction_three_objects.json"))
    logical = load_json(checked_payload(ev, logic_payload))["examples"]
    if (len(math), len(code), len(base), len(logical)) != (1319, 164, 7993, 250):
        raise ValueError("upstream canonical split count differs from prescribed corpus")
    code_by_id = unique_rows(code, "task_id")
    qa_by_id = unique_rows(qa, "QuestionId")
    destination = ROOT / "tests/data/prepared" / ev.path.name
    destination.mkdir(parents=True, exist_ok=False)
    prepared = {}
    for domain, rows in (("Math", math), ("Code", list(code_by_id.values())),
                         ("QA", list(qa_by_id.values())), ("Logic", logical),
                         ("Sequence", generate())):
        directory = destination / domain
        directory.mkdir()
        contents = {}
        for index, row in enumerate(rows):
            if domain == "Math":
                identifier = f"{index:06d}"
                if "####" not in row["answer"]:
                    raise ValueError("GSM8K answer lacks official final-answer delimiter")
                content = {
                    "id": identifier,
                    "prompt": row["question"] + "\nReturn only the final numerical answer.",
                    "answers": [row["answer"].rsplit("####", 1)[1].strip()],
                    "source_index": index, "source": row,
                }
            elif domain == "Code":
                identifier = row["task_id"]
                content = {
                    "id": identifier,
                    "prompt": ("Complete the following Python function. Return only the "
                               "function completion, without Markdown fences.\n" + row["prompt"]),
                    "answers": [row["canonical_solution"]], "source": row,
                }
            elif domain == "QA":
                identifier = row["QuestionId"]
                content = {
                    "id": identifier,
                    "prompt": row["Question"] + "\nReturn only the answer.",
                    "answers": list(dict.fromkeys(
                        [row["Answer"]["Value"]] + row["Answer"]["Aliases"] +
                        row["Answer"].get("HumanAnswers", []))),
                    "verified": True, "source": row,
                }
            elif domain == "Logic":
                identifier = f"{index:06d}"
                content = {
                    "id": identifier,
                    "prompt": row["input"] + "\nReturn only the parenthesized option letter.",
                    "answers": [row["target"]], "source_index": index, "source": row,
                }
            else:
                identifier, content = row["id"], row
            if identifier in contents:
                raise ValueError("duplicate canonical content ID")
            if (not content["prompt"] or not content["answers"] or
                    not all(isinstance(answer, str) and answer for answer in content["answers"])):
                raise ValueError("invalid canonical prompt/answer")
            contents[identifier] = content
        identifiers = sorted(contents)
        if len(identifiers) < 10:
            raise ValueError("insufficient canonical cases")
        if domain == "Sequence":
            revision = hashlib.sha1((ROOT / "tests/sequence_cases.py").read_bytes()).hexdigest()
        else:
            revision = metadata["pinned_repositories"][domain]["revision"]
        descriptors = {}
        # Store the complete corpus-derived canonical content, not only its selected prefix.
        for index, identifier in enumerate(identifiers):
            descriptors[identifier] = write_json(directory / f"content-{index:06d}.json",
                                                 contents[identifier])
        inventory = write_json(directory / "canonical_inventory.json", {
            "dataset": DOMAINS[domain], "revision": revision, "ids": identifiers,
            "content_sha256": {key: value["sha256"] for key, value in descriptors.items()},
        })
        selected = write_json(directory / "selected.json", [
            {"id": identifier, "content": descriptors[identifier]} for identifier in identifiers[:10]])
        prepared[domain] = {
            "dataset": DOMAINS[domain], "revision": revision,
            "canonical_inventory": inventory, "selected": selected,
            "count": len(identifiers), "selected_ids": identifiers[:10],
        }
    membership = write_json(destination / "qa_verified_membership.json", {
        "validation_ids": sorted(row["QuestionId"] for row in base),
        "attempted_ids": sorted(row["QuestionId"] for row in attempts),
        "eligible_ids": sorted(qa_by_id),
        "rejected_attempt_ids": sorted(row["QuestionId"] for row in attempts
                                     if row["QuestionPartOfVerifiedEval"] is False),
        "rule": "Wikipedia QuestionPartOfVerifiedEval is true; "
                "original validation ID, question, answer value and alias set must match",
        "document_rule": "Official dataset_utils.read_triviaqa_data restricts document-level "
                         "flags for Web only, not Wikipedia",
        "sources": [{"path": str(path.relative_to(ROOT)), "sha256": digest(path)}
                    for path in qa_paths],
    })
    provenance = {
        "schema": 1, "purpose": "canonical-input-preparation", "acceptance_evidence": False,
        "domains": prepared, "qa_membership": membership,
        "sequence": {"seed": 17, "generator_version": 1,
                     "generator": {"path": "tests/sequence_cases.py",
                                   "sha256": digest(ROOT / "tests/sequence_cases.py")},
                     "revision_semantics": "SHA1 of the published generator bytes"},
        "input_receipts": {key: ev.receipt[key] for key in
                           ("metadata_receipt", "json_receipt", "qa_receipt", "logic_receipt",
                            "membership_receipt")},
        "source_revisions": {
            **{domain: acquired["payloads"][domain]["revision"] for domain in ("Math", "Code")},
            "Logic": logic["upstream_revision"],
        },
        "scope": "Prescribed corpora via documented original JSON sources; no claim of "
                 "byte-identical serialization to Hugging Face parquet. TriviaQA official "
                 "v1.0 archive is content-hash pinned, not an immutable download URL. "
                 "No token arrays, acceptance manifests, AWQ or benchmark results.",
    }
    ev.receipt["prepared_inputs"] = write_json(destination / "preparation.json", provenance)
    ev.receipt["outputs"] = {
        str(path.relative_to(ROOT)): digest(path) for path in destination.rglob("*") if path.is_file()}
    return ev.assertion("complete_canonical_inventories_and_first_ten", True,
                        domains={key: value["count"] for key, value in prepared.items()},
                        verified_attempts=len(attempts), rejected_attempts=len(attempts)-len(qa))


def input_parity(ev, args):
    previous = bind_receipt(ev, "canonical_receipt", args.canonical_receipt)
    acquisition = bind_receipt(ev, "acquisition_receipt", args.acquisition_receipt)
    if previous["status"] != "passed" or acquisition["status"] != "passed":
        raise ValueError("input parity requires completed preparation and acquisition")
    preparation = previous.get("prepared_inputs")
    if preparation is None:
        checked_payload(ev, previous["canonical_worker_receipt"])
        worker = bind_receipt(ev, "canonical_worker_receipt",
                              Path(previous["canonical_worker_receipt"]["path"]))
        preparation = worker["prepared_inputs"]
    checked_payload(ev, preparation)
    checkpoint = ROOT / "tests/data/acquired" / Path(args.acquisition_receipt).parent.name / "model"
    for record in acquisition["retrievals"]:
        if Path(record["path"]).name in (
                "tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"):
            if not record["complete"]:
                raise ValueError("tokenizer acquisition incomplete")
            checked_payload(ev, record)
    destination = ROOT / "tests/data/prepared" / ev.path.name
    ok = ev.run("canonical-template-parity", [
        sys.executable, "tests/benchmark_input_checks.py",
        "--preparation", preparation["path"], "--checkpoint-dir", str(checkpoint.relative_to(ROOT)),
        "--destination", str(destination.relative_to(ROOT))], timeout=3600)
    ev.receipt["outputs"] = {
        str(path.relative_to(ROOT)): digest(path) for path in destination.rglob("*") if path.is_file()}
    if ok:
        report = load_json(destination / "input_integrity_report.json")
        ev.receipt["unestablished_prerequisites"] = [
            "Actual token-ID execution and parity against an existing pinned tokenizer backend"]
        ev.receipt["tokenizer_dependencies"] = report["tokenizer_dependencies"]
    ev.receipt["scope"] = (
        "Complete canonical-source integrity, membership negative cases, Sequence answers, "
        "pinned tokenizer serialization and actual Jinja template rendering only. "
        "No claim of token-ID parity, full-model inference or engineering acceptance.")
    return ev.assertion("canonical_source_and_template_parity", ok)


def unicode_facilities(ev, args):
    acquisition = bind_receipt(ev, "acquisition_receipt", args.acquisition_receipt)
    tokenizer = next(row for row in acquisition["retrievals"]
                     if Path(row["path"]).name == "tokenizer.json")
    checked_payload(ev, tokenizer)
    script = (
        "import ctypes.util,json,shutil,sys; t=json.load(open(sys.argv[1])); "
        "print(json.dumps({'pcre2':ctypes.util.find_library('pcre2-8'),"
        "'perl':shutil.which('perl'),'normalizer':t['normalizer'],"
        "'pre_tokenizer':t['pre_tokenizer'],'post_processor':t['post_processor'],"
        "'decoder':t['decoder'],'bpe_options':{k:v for k,v in t['model'].items() "
        "if k not in ('vocab','merges')}},indent=2))")
    ok = ev.run("existing-unicode-engine-facilities",
                [sys.executable, "-c", script, tokenizer["path"]], timeout=30)
    ev.receipt["scope"] = (
        "Existing Unicode regex engines and exact pinned tokenizer options only; no "
        "installation, approximate tokenizer, token arrays or model execution.")
    return ev.assertion("unicode_tokenizer_facilities_inspected", ok)


def token_inputs(ev, args):
    previous = bind_receipt(ev, "canonical_receipt", args.canonical_receipt)
    parity = bind_receipt(ev, "parity_receipt", args.parity_receipt)
    acquisition = bind_receipt(ev, "acquisition_receipt", args.acquisition_receipt)
    if any(record["status"] != "passed" for record in (previous, parity, acquisition)):
        raise ValueError("token inputs require complete canonical/template/acquisition evidence")
    preparation = previous.get("prepared_inputs")
    if preparation is None:
        checked_payload(ev, previous["canonical_worker_receipt"])
        worker = bind_receipt(ev, "canonical_worker_receipt",
                              Path(previous["canonical_worker_receipt"]["path"]))
        preparation = worker["prepared_inputs"]
    checked_payload(ev, preparation)
    report_name = next(name for name in parity["outputs"]
                       if name.endswith("/input_integrity_report.json"))
    checked_payload(ev, {"path": report_name, "sha256": parity["outputs"][report_name]})
    checkpoint = ROOT / "tests/data/acquired" / Path(args.acquisition_receipt).parent.name / "model"
    for record in acquisition["retrievals"]:
        if Path(record["path"]).name in (
                "tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"):
            if not record["complete"]:
                raise ValueError("tokenizer acquisition incomplete")
            checked_payload(ev, record)
    destination = ROOT / "tests/data/prepared" / ev.path.name
    common = ["--checkpoint-dir", str(checkpoint.relative_to(ROOT)),
              "--destination", str(destination.relative_to(ROOT))]
    ok = ev.run("exact-tokenizer-inputs", [
        sys.executable, "tests/pinned_tokenizer.py", "--prepare", *common,
        "--preparation", preparation["path"], "--integrity-report", report_name], timeout=3600)
    if ok:
        ok = ev.run("independent-perl-unicode-reference", [
            "perl", "tests/tokenizer_reference.pl",
            str((destination / "unicode_request.json").relative_to(ROOT)),
            str((destination / "perl_unicode_reference.json").relative_to(ROOT))], timeout=3600)
    if ok:
        ok = ev.run("independent-unicode-bpe-token-parity", [
            sys.executable, "tests/pinned_tokenizer.py", "--qualify", *common], timeout=3600)
    ev.receipt["outputs"] = {
        str(path.relative_to(ROOT)): digest(path) for path in destination.rglob("*") if path.is_file()}
    ev.receipt["scope"] = (
        "Exact supported pinned tokenizer policy qualification and actual shared prompt/teacher "
        "token arrays. PCRE2 versus Perl Unicode/NFC and ranked-pair versus heap BPE references; "
        "no installed Hugging Face backend equivalence, AWQ, model inference or RTL comparison.")
    return ev.assertion("qualified_pinned_token_inputs", ok)


def token_decoder(ev, args):
    acquisition = bind_receipt(ev, "acquisition_receipt", args.acquisition_receipt)
    tokenizer = next(row for row in acquisition["retrievals"]
                     if Path(row["path"]).name == "tokenizer.json")
    checkpoint = checked_payload(ev, tokenizer).parent
    destination = ROOT / "tests/data/prepared" / ev.path.name
    ok = ev.run("tokenizer-byte-stream-decoder", [
        sys.executable, "tests/pinned_tokenizer.py", "--decoder-check",
        "--checkpoint-dir", str(checkpoint.relative_to(ROOT)),
        "--destination", str(destination.relative_to(ROOT))], timeout=3600)
    ev.receipt["outputs"] = {
        str(path.relative_to(ROOT)): digest(path) for path in destination.rglob("*") if path.is_file()}
    return ev.assertion("pinned_tokenizer_decoder_semantics", ok)


def suite_manifest(ev, args):
    destination = ROOT / "tests/data/benchmark_manifest.json"
    if destination.exists():
        raise ValueError("frozen suite manifest already exists; refusing to overwrite")
    previous = bind_receipt(ev, "canonical_receipt", args.canonical_receipt)
    parity = bind_receipt(ev, "parity_receipt", args.parity_receipt)
    token_record = bind_receipt(ev, "token_receipt", args.token_receipt)
    acquisition = bind_receipt(ev, "acquisition_receipt", args.acquisition_receipt)
    if any(record["status"] != "passed" for record in
           (previous, parity, token_record, acquisition)):
        raise ValueError("suite requires completed canonical, template and token preparation")
    preparation_descriptor = previous.get("prepared_inputs")
    if preparation_descriptor is None:
        worker_path = checked_payload(ev, previous["canonical_worker_receipt"])
        preparation_descriptor = load_json(worker_path)["prepared_inputs"]
    preparation = load_json(checked_payload(ev, preparation_descriptor))
    report_name = next(name for name in token_record["outputs"]
                       if name.endswith("/tokenization_preparation.json"))
    token_descriptor = {"path": report_name, "sha256": token_record["outputs"][report_name]}
    tokens = load_json(checked_payload(ev, token_descriptor))
    integrity_name = next(name for name in parity["outputs"]
                          if name.endswith("/input_integrity_report.json"))
    integrity_descriptor = {"path": integrity_name, "sha256": parity["outputs"][integrity_name]}
    checked_payload(ev, integrity_descriptor)
    if (tokens["preparation_sha256"] != preparation_descriptor["sha256"] or
            tokens["integrity_report_sha256"] != integrity_descriptor["sha256"]):
        raise ValueError("token contexts were prepared from different canonical/template inputs")
    tokenizer = next(record for record in acquisition["retrievals"]
                     if Path(record["path"]).name == "tokenizer.json")
    checked_payload(ev, tokenizer)
    chat_name = next(name for name in parity["outputs"] if name.endswith("/chat_template.jinja"))
    chat_template = {"path": chat_name, "sha256": parity["outputs"][chat_name]}
    checked_payload(ev, chat_template)
    by_case = {}
    for record in tokens["cases"]:
        key = (record["domain"], record["id"])
        if key in by_case:
            raise ValueError("duplicate tokenized case")
        by_case[key] = record
    if len(by_case) != 50:
        raise ValueError("requires all fifty actual tokenized cases")
    domains = {}
    for domain, group in preparation["domains"].items():
        inventory = load_json(checked_payload(ev, group["canonical_inventory"]))
        selected = load_json(checked_payload(ev, group["selected"]))
        cases = []
        for selected_case in selected:
            record = by_case[(domain, selected_case["id"])]
            if record["content"] != selected_case["content"]:
                raise ValueError("tokenized content differs from canonical selection")
            cases.append({name: record[name] for name in
                          ("id", "content", "prompt_tokens", "teacher_tokens")})
        domains[domain] = {
            "dataset": group["dataset"], "revision": group["revision"],
            "canonical_inventory": group["canonical_inventory"], "cases": cases,
        }
        if [case["id"] for case in cases] != inventory["ids"][:10]:
            raise ValueError("tokenized cases differ from admitted first-ten selection")
        if domain == "QA":
            domains[domain]["verified_only"] = True
        if domain == "Sequence":
            domains[domain].update({
                "seed": 17, "generator_version": 1,
                "generator": preparation["sequence"]["generator"]})
    suite = {
        "schema": 1, "suite": "anvil-five-domain-v1", "domains": domains,
        "tokenizer_sha256": tokenizer["sha256"], "chat_template_sha256": chat_template["sha256"],
        "decoding": {"greedy": True, "tie_break": "lowest-token-id",
                     "max_new_tokens": 128, "sampling": False},
        "input_preparation": token_descriptor,
    }
    # Exercise the unchanged real suite validator using actual tokenizer/template artifacts.
    # This does not validate or create a model manifest or any execution result.
    validator = Validator(ROOT, ev)
    observed = validator.suite(suite, {"tokenizer": tokenizer, "chat_template": chat_template})
    ev.receipt["suite_manifest"] = write_json(destination, suite)
    return ev.assertion("complete_frozen_suite_input_manifest", len(observed) == 50,
                        selected_cases=len(observed),
                        missing_acceptance_inputs=[
                            name for name in ("tests/data/model_manifest.json",
                                              "tests/data/full_model_results.json")
                            if not (ROOT / name).is_file()],
                        scope="Actual complete suite inputs only, not full-model benchmark acceptance")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", choices=("upstream-inventory", "json-acquisition",
                                          "qa-archive", "canonical", "qa-membership-diagnostic",
                                          "qa-membership-source", "input-parity", "unicode-facilities",
                                          "token-inputs", "token-decoder", "suite-manifest"))
    parser.add_argument("--repair-of", type=Path)
    parser.add_argument("--upstream-receipt", type=Path)
    parser.add_argument("--discovery-receipt", type=Path)
    parser.add_argument("--inspect-qa", type=Path)
    parser.add_argument("--destination", type=Path)
    for name in ("metadata", "json", "qa", "logic", "membership", "canonical", "acquisition",
                 "parity", "token"):
        parser.add_argument("--" + name + "-receipt", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.inspect_qa is not None:
        if args.destination is None:
            parser.error("--inspect-qa requires --destination")
        inspect_qa(args.inspect_qa, args.destination)
        return 0
    if args.probe is None or args.repair_of is None:
        parser.error("--probe and --repair-of are required")
    ev = Evidence("corpus-" + args.probe)
    ok = False
    try:
        bind_receipt(ev, "repair_of", args.repair_of)
        if args.probe == "upstream-inventory":
            ok = upstream_inventory(ev)
        elif args.probe == "json-acquisition":
            if args.upstream_receipt is None:
                raise ValueError("json-acquisition requires --upstream-receipt")
            ok = json_acquisition(ev, args.upstream_receipt)
        elif args.probe == "qa-archive":
            if args.discovery_receipt is None:
                raise ValueError("qa-archive requires --discovery-receipt")
            ok = qa_archive(ev, args.discovery_receipt)
        elif args.probe == "qa-membership-diagnostic":
            if args.qa_receipt is None or args.upstream_receipt is None:
                raise ValueError("membership diagnostic requires QA and upstream receipts")
            ok = qa_membership_diagnostic(ev, args)
        elif args.probe == "qa-membership-source":
            if args.upstream_receipt is None:
                raise ValueError("membership source requires upstream receipt")
            ok = qa_membership_source(ev, args)
        elif args.probe == "input-parity":
            if args.canonical_receipt is None or args.acquisition_receipt is None:
                raise ValueError("input parity requires canonical and acquisition receipts")
            ok = input_parity(ev, args)
        elif args.probe == "unicode-facilities":
            if args.acquisition_receipt is None:
                raise ValueError("Unicode facilities requires acquisition receipt")
            ok = unicode_facilities(ev, args)
        elif args.probe == "token-inputs":
            if any(value is None for value in
                   (args.canonical_receipt, args.parity_receipt, args.acquisition_receipt)):
                raise ValueError("token inputs require canonical/parity/acquisition receipts")
            ok = token_inputs(ev, args)
        elif args.probe == "token-decoder":
            if args.acquisition_receipt is None:
                raise ValueError("token decoder requires acquisition receipt")
            ok = token_decoder(ev, args)
        elif args.probe == "suite-manifest":
            if any(value is None for value in (args.canonical_receipt, args.parity_receipt,
                                              args.acquisition_receipt, args.token_receipt)):
                raise ValueError("suite requires canonical/parity/acquisition/token receipts")
            if args.worker:
                ok = suite_manifest(ev, args)
            else:
                ok = ev.run("suite-input-manifest", [
                    sys.executable, "tests/benchmark_inputs.py", *sys.argv[1:], "--worker"],
                    timeout=3600)
                if ok:
                    child = load_json(ev.path / "suite-input-manifest.stdout")
                    record = bind_receipt(ev, "suite_worker_receipt", Path(child["receipt"]))
                    ok = (record["status"] == "passed" and ev.assertion(
                        "suite_input_worker_complete", True, suite_manifest=record["suite_manifest"]))
        else:
            if any(getattr(args, name + "_receipt") is None
                   for name in ("metadata", "json", "qa", "logic", "membership")):
                raise ValueError("canonical requires metadata/json/qa/logic/membership receipts")
            if args.worker:
                ok = canonical(ev, args)
            else:
                ok = ev.run("canonical-preparation", [
                    sys.executable, "tests/benchmark_inputs.py", *sys.argv[1:], "--worker"],
                    timeout=3600)
                if ok:
                    child = load_json(ev.path / "canonical-preparation.stdout")
                    record = bind_receipt(ev, "canonical_worker_receipt", Path(child["receipt"]))
                    ok = (record["status"] == "passed" and
                          ev.assertion("canonical_worker_complete", True,
                                       prepared_inputs=record["prepared_inputs"]))
    except (ValueError, KeyError, OSError) as error:
        ev.assertion("input_preparation_exception", False, error=repr(error))
    finally:
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
