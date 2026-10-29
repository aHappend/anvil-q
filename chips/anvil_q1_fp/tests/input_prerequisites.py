#!/usr/bin/env python3
"""Retained public-input and execution-facility diagnostics, never acceptance."""

import argparse
import json
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import artifact_path, load_json
from verify import Evidence, ROOT, digest


REPOSITORIES = (
    ("model", "models", "Qwen/Qwen2.5-0.5B-Instruct"),
    ("Math", "datasets", "openai/gsm8k"),
    ("Code", "datasets", "openai/openai_humaneval"),
    ("QA", "datasets", "mandarjoshi/trivia_qa"),
    ("Logic", "datasets", "maveriq/bigbenchhard"),
)


def fetch(ev, label, url, output=None, allowance=120):
    output = output or ev.path / (label + ".response")
    if output.exists():
        raise ValueError("refusing to overwrite acquisition output: " + str(output))
    ok = ev.run(label, [
        "curl", "--fail", "--show-error", "--location", "--silent",
        "--connect-timeout", "30", "--max-time", str(allowance),
        "--output", str(output.relative_to(ROOT)), url,
    ], timeout=allowance + 30)
    ev.receipt.setdefault("retrievals", []).append({
        "url": url, "path": str(output.relative_to(ROOT)),
        "sha256": digest(output) if output.is_file() else None,
        "complete": ok,
    })
    ev.assertion(label + "_retrieved", ok, url=url)
    return output if ok else None


def acquire_metadata(ev):
    if not shutil.which("curl"):
        return ev.assertion("public_acquisition_tool", False, missing="curl")
    if not ev.run("curl-version", ["curl", "--version"], timeout=30):
        return False
    ok = True
    for label, kind, repository in REPOSITORIES:
        metadata = fetch(ev, label + "-metadata",
                         f"https://huggingface.co/api/{kind}/{repository}")
        if metadata is None:
            ok = False
            continue
        data = load_json(metadata)
        revision = data["sha"]
        if not re.fullmatch("[0-9a-f]{40}", revision):
            raise ValueError("public repository did not supply a fixed revision: " + repository)
        ev.receipt.setdefault("pinned_repositories", {})[label] = {
            "repository": repository, "revision": revision,
            "metadata_sha256": digest(metadata),
        }
        names = {item["rfilename"] for item in data["siblings"]}
        prefix = "" if kind == "models" else "datasets/"
        base = f"https://huggingface.co/{prefix}{repository}/resolve/{revision}/"
        selected = sorted(name for name in names
                          if name in ("README.md", "LICENSE", "LICENSE.txt",
                                      "LICENSE.md", "config.json",
                                      "tokenizer_config.json", "tokenizer.json",
                                      "vocab.json", "merges.txt",
                                      "model.safetensors.index.json"))
        for index, name in enumerate(selected):
            ok = (fetch(ev, f"{label}-provenance-{index}", base + name) is not None) and ok
        ev.receipt["pinned_repositories"][label]["files"] = sorted(names)
    ev.receipt["scope"] = (
        "Public repository metadata and pinned licensing/configuration/tokenizer files only. "
        "No fabricated input manifests, derived weights, model execution or benchmark results.")
    return ok


def acquire_files(ev, receipt):
    previous = ROOT / receipt
    if not previous.resolve().is_relative_to(ROOT):
        raise ValueError("metadata receipt escapes project")
    data = load_json(previous)
    ev.receipt["metadata_receipt"] = {
        "path": str(previous.relative_to(ROOT)), "sha256": digest(previous)}
    if data["status"] != "passed":
        raise ValueError("metadata acquisition did not complete")
    output_root = ROOT / "tests/data/acquired" / ev.path.name
    output_root.mkdir(parents=True, exist_ok=False)
    ok = ev.run("curl-version", ["curl", "--version"], timeout=30)
    for label, kind, repository in REPOSITORIES:
        item = data["pinned_repositories"][label]
        if item["repository"] != repository or not re.fullmatch("[0-9a-f]{40}", item["revision"]):
            raise ValueError("unexpected metadata repository/revision")
        prefix = "" if kind == "models" else "datasets/"
        base = f"https://huggingface.co/{prefix}{repository}/resolve/{item['revision']}/"
        directory = output_root / label
        directory.mkdir()
        selected = []
        for name in item["files"]:
            if label == "model":
                include = (name.endswith(".safetensors") or name in (
                    "config.json", "tokenizer.json", "tokenizer_config.json",
                    "vocab.json", "merges.txt", "README.md", "LICENSE"))
            else:
                include = name in ("README.md", "LICENSE", "LICENSE.md", "LICENSE.txt")
                include |= (
                    label == "Math" and name.startswith("main/test") or
                    label == "Code" and name.startswith("openai_humaneval/test") or
                    label == "QA" and name.startswith("rc.wikipedia/validation") or
                    label == "Logic" and "logical_deduction_three_objects" in name
                ) and name.endswith(".parquet")
                include |= label == "Logic" and name == "bigbenchhard.py"
            if include:
                path = Path(name)
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError("unsafe remote filename")
                output = directory / path
                output.parent.mkdir(parents=True, exist_ok=True)
                fetched = fetch(ev, f"{label}-file-{len(selected)}",
                                base + quote(name, safe="/"), output, allowance=3600)
                selected.append(name)
                ok = (fetched is not None) and ok
        ev.receipt.setdefault("acquired_repositories", {})[label] = {
            "repository": repository, "revision": item["revision"], "files": selected}
        payload = [name for name in selected if name.endswith((".parquet", ".safetensors"))]
        payload_ok = bool(payload)
        ok = ev.assertion(label + "_raw_payload_acquired", payload_ok,
                          files=payload, scope="A dataset loader script is not dataset records") and ok
    ev.receipt["scope"] = (
        "Exact pinned public checkpoint/tokenizer and prescribed raw dataset splits. "
        "Raw acquisition is not tokenization, AWQ calibration or full-model execution.")
    return ok


def execution_facilities(ev):
    ok = True
    if shutil.which("bwrap"):
        # Trusted probe only: no model-generated code is executed.
        argv = [
            "bwrap", "--unshare-all", "--die-with-parent", "--new-session",
            "--ro-bind", "/usr", "/usr", "--ro-bind", "/lib", "/lib",
            "--ro-bind-try", "/lib64", "/lib64", "--proc", "/proc",
            "--dev", "/dev", "--tmpfs", "/tmp", "--clearenv",
            "--setenv", "PATH", "/usr/bin", "--chdir", "/tmp",
            "/usr/bin/python3", "-I", "-c",
            "import os,socket; assert not os.path.exists('/data'); "
            "assert not os.path.exists('/home'); "
            "assert os.listdir('/sys') == [] if os.path.exists('/sys') else True; "
            "assert socket.if_nameindex() == [(1,'lo')]; "
            "print('trusted isolation smoke only; evaluator not qualified')",
        ]
        observed = ev.run("bubblewrap-trusted-isolation", argv, timeout=60)
        ok = ev.assertion("bubblewrap_can_launch_isolated_trusted_process", observed) and ok
    else:
        ok = ev.assertion("bubblewrap_available", False) and ok
    if shutil.which("docker"):
        observed = ev.run("docker-daemon-capability", [
            "docker", "version", "--format", "{{json .Server}}"], timeout=30)
        ok = ev.assertion("docker_daemon_access", observed) and ok
    if shutil.which("vulcan"):
        observed = ev.run("shared-runtime-board-help", [
            "vulcan", "hardware", "fpga", "board-hil", "--help"], timeout=60)
        ok = ev.assertion("shared_runtime_board_help_available", observed) and ok
    else:
        ok = ev.assertion("shared_runtime_cli_available", False) and ok
    ev.receipt["scope"] = (
        "Trusted isolation launch, read-only Docker server version and documented board CLI help. "
        "No image pull, generated Code execution, device discovery, board programming or hardware run. "
        "CLI help is not a working source/data-bound full-model bridge.")
    return ok


def reference_dependencies(ev, interpreter):
    script = (
        "import importlib.util,json,sys; print(json.dumps({'version':sys.version,"
        "'dependencies':{name:importlib.util.find_spec(name) is not None for name in "
        "('numpy','pyarrow','fastparquet','pandas','regex','jinja2','duckdb','polars')}}))")
    return ev.run("reference-dependencies", [str(interpreter), "-c", script], timeout=30)


def reference_environment(ev):
    """Validate the selected environment without choosing or modifying one."""
    ev.receipt["scope"] = (
        "Current PATH-resolved Python and its actual NumPy-importing child only. "
        "No environment selection, installation, inference, capacity reservation "
        "or collection authorization. A CLI environment is not shared-runtime clearance.")
    previous = ROOT / "evidence/preparation/verifier-prerequisites-2lqylqym/receipt.json"
    ev.receipt["retained_failure"] = {
        "path": str(previous.relative_to(ROOT)), "sha256": digest(previous)}
    script = """
import json, os, subprocess, sys
print("ANVIL_ENV " + json.dumps({
    "event": "parent",
    "python_version": sys.version,
    "same_executable_as_probe": sys.executable == sys.argv[1],
    "thread_settings": {key: os.environ.get(key) for key in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
        "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")},
}), flush=True)
import numpy
print("ANVIL_ENV " + json.dumps({"event": "parent_import", "numpy_version": numpy.__version__}),
      flush=True)
numpy.show_config()
sys.stdout.flush()
child = '''
import json, sys, numpy
assert sys.executable == sys.argv[1], "child interpreter changed"
assert numpy.__version__ == sys.argv[2], "child NumPy version changed"
print("ANVIL_ENV " + json.dumps({"event": "child_import", "numpy_version": numpy.__version__,
                  "same_executable_as_parent": True}), flush=True)
'''
subprocess.run([sys.executable, "-c", child, sys.executable, numpy.__version__],
               check=True)
"""
    completed = ev.run("path-parent-child-numpy-import", [
        "python3", "-c", script, sys.executable], timeout=3600)
    events = []
    for line in (ev.path / "path-parent-child-numpy-import.stdout").read_text().splitlines():
        if line.startswith("ANVIL_ENV "):
            events.append(json.loads(line.removeprefix("ANVIL_ENV ")))
    expected = ("parent", "parent_import", "child_import")
    valid = (completed and tuple(row.get("event") for row in events) == expected and
             events[0]["same_executable_as_probe"] is True and
             events[1]["numpy_version"] == events[2]["numpy_version"] and
             events[2]["same_executable_as_parent"] is True)
    ev.receipt["environment_observations"] = events
    ev.receipt["outputs"] = {
        str(path.relative_to(ROOT)): digest(path)
        for path in ev.path.iterdir() if path.is_file() and path.name != "receipt.json"}
    return ev.assertion("selected_parent_and_child_numpy_import", valid,
                        environment_changed=False, collection_launched=False,
                        shared_runtime_environment_qualified=False,
                        full_suite_capacity_proven=False)


def remaining_inputs(ev, interpreter, metadata_receipt, acquisition_receipt):
    metadata = load_json(ROOT / metadata_receipt)
    previous = load_json(ROOT / acquisition_receipt)
    for key, path in (("metadata", metadata_receipt), ("acquisition", acquisition_receipt)):
        ev.receipt[key + "_receipt"] = {"path": str(path), "sha256": digest(ROOT / path)}
    logic = metadata["pinned_repositories"]["Logic"]
    source = fetch(ev, "Logic-loader",
                   "https://huggingface.co/datasets/maveriq/bigbenchhard/resolve/" +
                   logic["revision"] + "/bigbenchhard.py")
    if source is not None:
        ev.receipt["logic_loader_scope"] = (
            "Downloaded as data for source-URL inspection; never imported or executed")
    root = ROOT / "tests/data/acquired" / (ROOT / acquisition_receipt).parent.name
    parquet = next((root / "Math").rglob("*.parquet"))
    read_ok = ev.run("pandas-parquet-reader", [
        str(interpreter), "-c",
        "import pandas as pd,sys; frame=pd.read_parquet(sys.argv[1]); "
        "print('rows',len(frame)); print('columns',list(frame.columns))",
        str(parquet.relative_to(ROOT)),
    ], timeout=3600)
    ev.assertion("existing_parquet_reader_usable", read_ok)
    images_ok = True
    if shutil.which("docker"):
        images_ok = ev.run("existing-isolation-images", ["docker", "image", "ls", "--no-trunc",
                           "--format", "{{json .}}"], timeout=30)
        ev.assertion("existing_isolation_image_inventory_completed", images_ok)
    ev.receipt["scope"] = (
        "Original Logic acquisition retained only its card, not records. This diagnostic "
        "retains the pinned loader as data and attempts the existing corpus reader. "
        "Docker image discovery is not evaluator qualification. No generated code executes.")
    return source is not None and read_ok and images_ok


def logic_upstream(ev):
    metadata = fetch(ev, "Logic-upstream-commit",
                     "https://api.github.com/repos/suzgunmirac/BIG-Bench-Hard/commits/main")
    if metadata is None:
        return False
    revision = load_json(metadata)["sha"]
    if not re.fullmatch("[0-9a-f]{40}", revision):
        raise ValueError("Logic upstream did not supply a fixed commit")
    directory = ROOT / "tests/data/acquired" / ev.path.name / "Logic"
    directory.mkdir(parents=True, exist_ok=False)
    payload = fetch(
        ev, "Logic-records",
        f"https://raw.githubusercontent.com/suzgunmirac/BIG-Bench-Hard/{revision}/"
        "bbh/logical_deduction_three_objects.json",
        output=directory / "logical_deduction_three_objects.json")
    license_file = fetch(
        ev, "Logic-license",
        f"https://api.github.com/repos/suzgunmirac/BIG-Bench-Hard/license?ref={revision}",
        output=directory / "license-response.json")
    if payload is None:
        return False
    examples = load_json(payload)["examples"]
    valid = len(examples) >= 10 and all(
        isinstance(row.get("input"), str) and isinstance(row.get("target"), str)
        for row in examples)
    ev.receipt["upstream_revision"] = revision
    return ev.assertion("Logic_original_records_acquired", valid and license_file is not None,
                        record_count=len(examples), license_acquired=license_file is not None)


def docker_isolation(ev):
    image = "vulcan-solver:0.8.0"
    script = (
        "import importlib.util,json,os,socket; "
        "assert os.getuid()==65534; "
        "status=open('/proc/self/status').read(); "
        "assert 'CapEff:\\t0000000000000000' in status; "
        "assert 'NoNewPrivs:\\t1' in status; "
        "assert socket.if_nameindex()==[(1,'lo')]; "
        "assert os.getpid()==1; "
        "print(json.dumps({'uid':os.getuid(),'capabilities':'none','network':'loopback-only',"
        "'dependencies':{n:importlib.util.find_spec(n) is not None for n in "
        "('numpy','pyarrow','fastparquet','regex','jinja2','tokenizers','transformers')}}))")
    argv = [
        "docker", "run", "--rm", "--pull=never", "--network=none",
        "--read-only", "--user=65534:65534", "--cap-drop=ALL",
        "--security-opt=no-new-privileges", "--pids-limit=64", "--memory=512m",
        "--cpus=1", "--ulimit=cpu=30", "--ulimit=fsize=10485760",
        "--ulimit=nofile=128", "--ipc=none",
        "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=64m",
        "--entrypoint=python3", image, "-I", "-c", script,
    ]
    ok = ev.run("trusted-container-isolation", argv, timeout=120)
    ev.receipt["scope"] = (
        "Trusted qualification of an already present image, with no host mounts, network, "
        "capabilities, image pull or installation. No generated code or benchmark evaluation.")
    return ev.assertion("existing_container_isolation_smoke", ok)


def native_reference(ev, interpreter, acquisition_receipt, mode, streams_receipt=None):
    receipt_path = ROOT / acquisition_receipt
    if not receipt_path.resolve().is_relative_to(ROOT):
        raise ValueError("acquisition receipt escapes project")
    previous = load_json(receipt_path)
    if previous["status"] != "passed":
        raise ValueError("input acquisition is incomplete")
    ev.receipt["acquisition_receipt"] = {
        "path": str(receipt_path.relative_to(ROOT)), "sha256": digest(receipt_path)}
    directory = ROOT / "tests/data/acquired" / receipt_path.parent.name / "model"
    for record in previous["retrievals"]:
        path = ROOT / record["path"]
        if path.is_relative_to(directory):
            if not record["complete"] or digest(path) != record["sha256"]:
                raise ValueError("acquired input hash mismatch: " + record["path"])
            ev.receipt.setdefault("data_sha256", {})[record["path"]] = record["sha256"]
    version_ok = ev.run("reference-numpy-version", [str(interpreter), "-c",
                                        "import numpy,sys; print(sys.version); print(numpy.__version__)"],
                       timeout=30)
    if not ev.assertion("reference_dependency_imported", version_ok):
        return False
    selftest = ev.run("reference-selftest",
                     [str(interpreter), "tests/fp64_reference.py", "--selftest"])
    if not ev.assertion("independent_reference_known_answers", selftest):
        return False
    if mode == "native-streams":
        destination = ROOT / "tests/data/streams" / ev.path.name
        argv = [str(interpreter), "tests/fp64_reference.py", "--prepare",
                "--checkpoint-dir", str(directory.relative_to(ROOT)),
                "--destination", str(destination.relative_to(ROOT)), "--revision",
                previous["acquired_repositories"]["model"]["revision"]]
    else:
        if streams_receipt is None:
            raise ValueError("fp64-diagnostic requires --streams-receipt")
        stream_record = load_json(ROOT / streams_receipt)
        if stream_record["status"] != "passed":
            raise ValueError("native streams did not complete conversion")
        for name, hashed in stream_record["outputs"].items():
            if digest(ROOT / name) != hashed:
                raise ValueError("selected stream hash mismatch: " + name)
        ev.receipt["selected_streams_receipt"] = {
            "path": str(streams_receipt), "sha256": digest(ROOT / streams_receipt)}
        streams_dir = ROOT / "tests/data/streams" / (ROOT / streams_receipt).parent.name
        destination = ev.path / "reference-outputs"
        argv = [str(interpreter), "tests/fp64_reference.py", "--diagnostic",
                "--checkpoint-dir", str(directory.relative_to(ROOT)),
                "--destination", str(destination.relative_to(ROOT)),
                "--streams-dir", str(streams_dir.relative_to(ROOT))]
    ok = ev.run(mode, argv, timeout=3600)
    ev.receipt["outputs"] = {
        str(path.relative_to(ROOT)): digest(path) for path in sorted(destination.rglob("*"))
        if path.is_file()}
    ev.receipt["scope"] = (
        "Native stream conversion or three-token full-dimension FP64 reference diagnostic only. "
        "No AWQ artifact, benchmark case execution, DUT comparison, timing or HIL acceptance.")
    return ev.assertion(mode + "_completed", ok)


def bridge_capabilities(ev):
    ok = ev.run("documented-hardware-commands", ["vulcan", "hardware", "--help"], timeout=60)
    ok = ev.run("documented-fpga-commands",
                ["vulcan", "hardware", "fpga", "--help"], timeout=60) and ok
    ev.receipt["scope"] = (
        "Public command documentation only. No bridge state files, runtime metadata, "
        "device accesses, remote commands or hardware execution.")
    return ev.assertion("documented_bridge_capabilities_inspected", ok)


def production_interface(ev):
    """Inspect public help only; never infer a transport from a remote shell gate."""
    ev.receipt["scope"] = (
        "Bounded public CLI documentation inspection only. No runtime state, "
        "private storage, remote commands, device access, programming or inference. "
        "Documentation success does not qualify a production execution interface.")
    ok = True
    for label, argv in (
        ("runtime-version", ["vulcan", "hardware", "--version"]),
        ("public-command-help", ["vulcan", "--help"]),
        ("hardware-command-help", ["vulcan", "hardware", "--help"]),
        ("fpga-command-help", ["vulcan", "hardware", "fpga", "--help"]),
        ("board-gate-help", ["vulcan", "hardware", "fpga", "board-hil", "--help"]),
        ("doctor-help", ["vulcan", "hardware", "doctor", "--help"]),
        ("status-help", ["vulcan", "hardware", "status", "--help"]),
    ):
        observed = ev.run(label, argv, timeout=60)
        ok = ev.assertion(label + "_read", observed) and ok
    ev.receipt["intended_execution_bindings"] = {
        "top": "anvil_q1_fp_top",
        "source_sha256": {
            path: hashed for path, hashed in ev.receipt["source_sha256"].items()
            if path.startswith(("rtl/", "fpga/"))
        },
        "artifacts": {},
        "note": "Local identities only; no endpoint has attested these bindings.",
    }
    for name in (
        "tests/data/model_manifest.json",
        "tests/data/benchmark_manifest.json",
        "evidence/preparation/verifier-reference-collector-full-6rkm2hzx/receipt.json",
        "evidence/preparation/verifier-reference-collector-full-6rkm2hzx/"
        "collected-reference/teacher_references.json",
    ):
        try:
            path = artifact_path(ROOT, name)
            present = path.is_file()
            diagnostic = None if present else "missing artifact: " + name
        except (ValueError, OSError) as error:
            present = False
            diagnostic = f"{type(error).__name__}: {error}"
        ok = ev.assertion("binding_" + name, present, reason=diagnostic) and ok
        if present:
            ev.receipt["intended_execution_bindings"]["artifacts"][name] = digest(path)
    ev.receipt["required_endpoint_capabilities"] = {
        "source_data_binding": "Attest current RTL/constraints, manifests and accepted bitstream.",
        "memory_transport": (
            "Service kinds 0..12 and projections 0..6 with documented tensor offsets, "
            "FP32 scratch/KV, native low-half weights, AWQ packing and acknowledged writes."),
        "precision_control": (
            "Select 00/01/10 on accepted tokens; preserve sequence and reset semantics."),
        "token_logit_transport": (
            "Drive ready/valid tokens and retain all 151936 ordered logits per token, "
            "faults, backpressure and independent repeats."),
        "cycle_observation": (
            "Measure accepted-to-last, first-logit, arithmetic, memory-stall, "
            "control and generation cycles."),
        "layer_observation": (
            "Retain 896 FP32-equivalent values for every one of 24 layers "
            "at every teacher position without modifying the accepted design."),
        "nonprogramming_diagnostic": (
            "Document an authorized capability/identity request and its response schema "
            "that requires no remote command invention or device programming."),
    }
    ev.receipt["qualification"] = {
        "documentation_commands_completed": bool(ok),
        "endpoint_contacted": False,
        "hardware_availability": "not determined",
        "observer_implemented": False,
        "status": "not-established",
    }
    ev.assertion("production_execution_interface_qualified", False,
                 reason="Public help inspection is not an endpoint capability response; "
                        "route the required endpoint capabilities for platform documentation.")
    return False


def helper_validation(ev):
    script = (
        "import ast,pathlib; paths=['tests/input_prerequisites.py','tests/fp64_reference.py',"
        "'tests/benchmark_inputs.py','tests/benchmark_input_checks.py','tests/sequence_cases.py',"
        "'tests/awq_prepare.py','tests/isolated_code.py','tests/code_worker.py',"
        "'tests/teacher_reference.py']; "
        "[(ast.parse(pathlib.Path(p).read_text(),filename=p),print('parsed',p)) for p in paths]")
    ok = ev.assertion("new_recovery_helpers_parse",
                      ev.run("recovery-helper-syntax", ["python3", "-c", script], timeout=30))
    binding_script = """
import hashlib,json,pathlib,sys
from types import SimpleNamespace
sys.path.insert(0,'tests')
from benchmark_inputs import checked_payload
path=pathlib.Path(sys.argv[1])
path.write_bytes(b'input-binding-fixture')
record={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
holder=SimpleNamespace(receipt={})
if checked_payload(holder,record) != path.resolve():
    raise ValueError('valid project-relative binding rejected')
rejected=0
for invalid in ({**record,'sha256':'0'*64},
                {'path':'../not-a-project-input','sha256':'0'*64}):
    try:
        checked_payload(holder,invalid)
    except ValueError:
        rejected+=1
    else:
        raise ValueError('invalid payload binding accepted')
print(json.dumps({'valid_bindings':1,'rejected_invalid_bindings':rejected}))
"""
    ok = ev.assertion("corpus_payload_bindings_fail_closed",
                      ev.run("corpus-input-binding-sensitivity", [
                          sys.executable, "-c", binding_script,
                          str((ev.path / "binding-fixture.bin").relative_to(ROOT))],
                          timeout=60)) and ok
    original = ROOT / "evidence/preparation/verifier-public-inputs-he8oltf0/receipt.json"
    if original.is_file():
        previous = load_json(original)
        changed = [name for name, hashed in previous["source_sha256"].items()
                   if name.startswith(("rtl/", "fpga/", "design/", "anvil_q1_reference/rtl/"))
                   and ev.receipt["source_sha256"].get(name) != hashed]
        ev.receipt["design_preservation_receipt"] = {
            "path": str(original.relative_to(ROOT)), "sha256": digest(original)}
        ok = ev.assertion("recovery_preserved_design_and_parent_sources",
                          not changed, changed=changed) and ok
    else:
        ok = ev.assertion("design_preservation_receipt_available", False) and ok
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", choices=("public-inputs", "acquire-files",
                        "execution-facilities", "reference-dependencies",
                        "native-streams", "fp64-diagnostic", "remaining-inputs",
                        "logic-upstream", "docker-isolation", "bridge-capabilities",
                        "production-interface", "reference-environment",
                        "helper-validation"), required=True)
    parser.add_argument("--metadata-receipt", type=Path)
    parser.add_argument("--python-facility", type=Path, default=Path(sys.executable))
    parser.add_argument("--acquisition-receipt", type=Path)
    parser.add_argument("--streams-receipt", type=Path)
    args = parser.parse_args()
    ev = Evidence(args.probe)
    ok = False
    try:
        if args.probe == "public-inputs":
            ok = acquire_metadata(ev)
        elif args.probe == "acquire-files":
            if args.metadata_receipt is None:
                raise ValueError("acquire-files requires --metadata-receipt")
            ok = acquire_files(ev, args.metadata_receipt)
        elif args.probe == "reference-dependencies":
            ok = reference_dependencies(ev, args.python_facility)
        elif args.probe == "reference-environment":
            ok = reference_environment(ev)
        elif args.probe == "logic-upstream":
            ok = logic_upstream(ev)
        elif args.probe == "docker-isolation":
            ok = docker_isolation(ev)
        elif args.probe == "bridge-capabilities":
            ok = bridge_capabilities(ev)
        elif args.probe == "production-interface":
            ok = production_interface(ev)
        elif args.probe == "helper-validation":
            ok = helper_validation(ev)
        elif args.probe == "remaining-inputs":
            if args.metadata_receipt is None or args.acquisition_receipt is None:
                raise ValueError("remaining-inputs requires metadata and acquisition receipts")
            ok = remaining_inputs(ev, args.python_facility,
                                  args.metadata_receipt, args.acquisition_receipt)
        elif args.probe in ("native-streams", "fp64-diagnostic"):
            if args.acquisition_receipt is None:
                raise ValueError("native reference requires --acquisition-receipt")
            ok = native_reference(ev, args.python_facility, args.acquisition_receipt,
                                  args.probe, args.streams_receipt)
        else:
            ok = execution_facilities(ev)
    except (ValueError, KeyError, OSError) as error:
        ev.assertion("prerequisite_diagnostic_exception", False, error=repr(error))
    finally:
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
