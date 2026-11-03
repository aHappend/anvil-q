#!/usr/bin/env python3
"""Qualify or use an existing isolated HumanEval facility; never install/pull."""

import argparse
import base64
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import Validator, load_json, require, sha
from benchmark_inputs import checked_payload, write_json
from code_worker import POLICY
from verify import Evidence, ROOT


def descriptor(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def docker_command(image, payload):
    require(re.fullmatch("sha256:[0-9a-f]{64}", image) is not None,
            "container must use an inspected immutable local image ID")
    encoded = base64.b64encode(json.dumps(payload, ensure_ascii=True).encode()).decode("ascii")
    return [
        "docker", "run", "--rm", "--pull=never", "--network=none", "--read-only",
        "--user=65534:65534", "--cap-drop=ALL", "--security-opt=no-new-privileges",
        "--pids-limit=64", "--memory=512m", "--cpus=1", "--ulimit=cpu=10",
        "--ulimit=fsize=1048576", "--ulimit=nofile=128", "--ipc=none",
        "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=64m", "--workdir=/tmp",
        "--entrypoint=python3", image, "-I", "-c",
        (ROOT / "tests/code_worker.py").read_text(), encoded,
    ]


def run_case(ev, label, image, content, completion, decode_sha):
    source = content["source"]
    require(source["task_id"] == content["id"], "HumanEval source identity mismatch")
    payload = {
        "case": "Code/" + content["id"], "decode_sha256": decode_sha,
        "prompt": source["prompt"], "completion": completion,
        "test": source["test"], "entry_point": source["entry_point"]}
    executed = ev.run(label, docker_command(image, payload), timeout=3600)
    if not ev.assertion(label + "_isolated_execution_completed", executed):
        return None
    record = ev.receipt["records"][-1]
    result = load_json(ROOT / record["stdout"])
    require(result["schema"] == 1 and result["case"] == payload["case"] and
            result["decode_sha256"] == decode_sha and result["isolated"] is True and
            result["policy"] == POLICY and type(result["passed"]) is bool,
            "malformed isolated evaluator result")
    write_json(ev.path / (label + "-result.json"), result)
    return result


def image_identity(ev, image):
    require(ev.run("docker-version", ["docker", "version", "--format", "{{json .Server}}"],
                   timeout=30), "Docker facility unavailable")
    require(ev.run("existing-image-identity", [
        "docker", "image", "inspect", "--format", "{{json .Id}}", image], timeout=30),
        "existing local evaluator image missing; no pull is permitted")
    record = ev.receipt["records"][-1]
    identity = load_json(ROOT / record["stdout"])
    require(isinstance(identity, str) and re.fullmatch("sha256:[0-9a-f]{64}", identity),
            "invalid inspected Docker image identity")
    ev.receipt["image_identity"] = identity
    return identity


def content_cases(ev):
    suite_path = ROOT / "tests/data/benchmark_manifest.json"
    model_path = ROOT / "tests/data/model_manifest.json"
    validator = Validator(ROOT, ev)
    model = load_json(model_path)
    validator.model(model)
    suite = load_json(suite_path)
    validator.suite(suite, model)
    ev.receipt["input_manifests"] = [descriptor(path) for path in (model_path, suite_path)]
    return {case["id"]: load_json(validator.artifact(case["content"]))
            for case in suite["domains"]["Code"]["cases"]}


def qualify(ev, image, cases):
    require(len(cases) == 10, "qualification requires all ten frozen Code cases")
    records = []
    ok = True
    for index, (identifier, content) in enumerate(cases.items()):
        completion = content["source"]["canonical_solution"]
        decoded = write_json(ev.path / f"canonical-{index:02d}.json",
                             {"text": completion, "purpose": "evaluator-qualification-not-model-output"})
        result = run_case(ev, f"canonical-{index:02d}", image, content, completion, decoded["sha256"])
        observed = result is not None and result["passed"] is True
        ok = ev.assertion(f"canonical_{identifier}_passes_unchanged_tests", observed) and ok
        records.append({"case": identifier, "kind": "canonical", "passed": observed})
        result = run_case(ev, f"wrong-{index:02d}", image, content, "    return None\n",
                          decoded["sha256"])
        rejected = result is not None and result["passed"] is False and result["error"] == "AssertionError"
        ok = ev.assertion(f"wrong_{identifier}_fails_unchanged_tests", rejected) and ok
        records.append({"case": identifier, "kind": "wrong-result", "rejected": rejected})
    # These are deliberately erroneous completions, never generated programs
    # running on the shared host. Each executes only in the same isolation.
    content = next(iter(cases.values()))
    for name, completion, expected in (
        ("syntax", "    return (\n", "SyntaxError"),
        ("exception", "    raise RuntimeError('fixture')\n", "RuntimeError"),
        ("early-exit", "    import sys\n    sys.exit(0)\n", "SystemExit"),
        ("timeout", "    while True:\n        pass\n", "TimeoutError"),
    ):
        decoded = write_json(ev.path / (name + ".json"), {
            "text": completion, "purpose": "evaluator-negative-qualification"})
        result = run_case(ev, name, image, content, completion, decoded["sha256"])
        rejected = result is not None and result["passed"] is False and result["error"] == expected
        ok = ev.assertion("evaluator_rejects_" + name, rejected) and ok
    qualification = {
        "schema": 1, "purpose": "isolated-humaneval-evaluator-qualification",
        "policy": POLICY, "image": image,
        "worker": descriptor(ROOT / "tests/code_worker.py"),
        "launcher": descriptor(ROOT / "tests/isolated_code.py"),
        "canonical_cases": 10, "wrong_result_cases": 10, "failure_classes": 4,
        "passed": bool(ok), "case_results": records,
        "limitations": "Isolated evaluator qualification, not model outputs, scores or hardware evidence."}
    ev.receipt["outputs"] = {
        str(path.relative_to(ROOT)): sha(path) for path in ev.path.glob("*-result.json")}
    artifact = write_json(ev.path / "qualification.json", qualification)
    ev.receipt["qualification"] = artifact
    return ok


def evaluate(ev, image, cases, args):
    require(args.case in cases, "not a selected frozen HumanEval case")
    require(args.decode is not None and args.qualification is not None,
            "evaluation requires actual decode and prior facility qualification")
    qualified = load_json(ROOT / args.qualification)
    require(qualified["purpose"] == "isolated-humaneval-evaluator-qualification" and
            qualified["passed"] is True and qualified["policy"] == POLICY and
            qualified["image"] == image and
            qualified["worker"] == descriptor(ROOT / "tests/code_worker.py") and
            qualified["launcher"] == descriptor(ROOT / "tests/isolated_code.py"),
            "evaluator has not qualified this worker/launcher/image")
    ev.receipt["qualification"] = descriptor(ROOT / args.qualification)
    decoded_path = ROOT / args.decode
    decoded = load_json(decoded_path)
    require(isinstance(decoded["text"], str) and isinstance(decoded["tokens"], list),
            "not an actual token decode artifact")
    model = load_json(ROOT / "tests/data/model_manifest.json")
    require(decoded["tokenizer_sha256"] == model["tokenizer"]["sha256"],
            "decode uses a different tokenizer")
    # A failing task is an evaluation result; tool/parse failures are not.
    result = run_case(ev, "humaneval", image, cases[args.case], decoded["text"], sha(decoded_path))
    require(result is not None, "isolated evaluator did not complete")
    result_path = ev.path / "humaneval-result.json"
    execution = {
        "schema": 1, "purpose": "isolated-code-evaluation",
        "bindings": args.bindings_data, "argv": ev.receipt["argv"], "cwd": ".",
        "tool_version": "Docker local image " + image + "; " + POLICY,
        "started_at": ev.receipt["started_at"], "ended_at": ev.receipt["records"][-1]["ended_at"],
        "timeout_s": 3600, "exit_code": 0, "timed_out": False,
        "stdout": descriptor(ROOT / ev.receipt["records"][-1]["stdout"]),
        "stderr": descriptor(ROOT / ev.receipt["records"][-1]["stderr"]),
        "outputs": [descriptor(result_path)],
    }
    run = write_json(ev.path / "execution.json", execution)
    evaluation = {
        "isolated": True, "environment": "Docker local image " + image, "policy": POLICY,
        "case": "Code/" + args.case, "decode_sha256": sha(decoded_path),
        "passed": result["passed"], "execution": run, "result": descriptor(result_path)}
    ev.receipt["evaluation"] = write_json(ev.path / "evaluation.json", evaluation)
    return ev.assertion("actual_decode_isolated_evaluation_completed", True,
                        task_passed=result["passed"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualify", action="store_true")
    parser.add_argument("--image", required=True)
    parser.add_argument("--case")
    parser.add_argument("--decode", type=Path)
    parser.add_argument("--qualification", type=Path)
    parser.add_argument("--bindings", type=Path)
    args = parser.parse_args()
    for value in (args.decode, args.qualification, args.bindings):
        if value is not None:
            require(not value.is_absolute() and ".." not in value.parts and
                    (ROOT / value).resolve().is_relative_to(ROOT), "nonportable evaluator input")
    ev = Evidence("code-qualification" if args.qualify else "code-evaluation")
    ok = False
    try:
        image = image_identity(ev, args.image)
        cases = content_cases(ev)
        if args.qualify:
            ok = qualify(ev, image, cases)
        else:
            require(args.bindings is not None, "actual evaluation requires execution bindings")
            args.bindings_data = load_json(ROOT / args.bindings)
            current = {
                "model_manifest": sha(ROOT / "tests/data/model_manifest.json"),
                "benchmark_manifest": sha(ROOT / "tests/data/benchmark_manifest.json"),
                "source_sha256": {str(path.relative_to(ROOT)): sha(path)
                                  for pattern in ("rtl/*.sv", "fpga/*")
                                  for path in sorted(ROOT.glob(pattern)) if path.is_file()}}
            require(args.bindings_data == current, "evaluator execution bindings differ")
            ok = evaluate(ev, image, cases, args)
    except (ValueError, KeyError, OSError) as error:
        ev.assertion("isolated_evaluator_exception", False, error=repr(error))
    finally:
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
