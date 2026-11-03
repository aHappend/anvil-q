"""Compile and execute five disposable RTL defects; baseline first, no source edits."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, execute, hashes, relative, remaining, timestamp


MUTATIONS = (
    ("int8-extraction", "packed_cache", "anvil_q1_ht3_kv_reader.sv",
     "selected_key[7:0] = cache_key[bit_offset[8:0]+:8];",
     "selected_key[7:0] = cache_key[bit_offset[8:0]+1+:8];", "PACKED_READBACK"),
    ("rope-pairing", "epilogue", "anvil_q1_ht3_epilogue_fusion.sv",
     "read_address = index_q + (HEAD_DIM >> 1);", "read_address = index_q + 1;", None),
    ("rms-epsilon", "epilogue", "anvil_q1_ht3_epilogue_fusion.sv",
     "operand_b = {4{32'h358637bd}};", "operand_b = {4{32'h00000000}};", None),
    ("flash-rescaling", "attention", "anvil_q1_ht3_flash_attn.sv",
     "arithmetic_a[32*s+:32] = maximum[32*s+:32];",
     "arithmetic_a[32*s+:32] = 32'b0;", None),
    ("output-tag", "epilogue", "anvil_q1_ht3_epilogue_fusion.sv",
     "assign out_index = out_valid ? {19'b0, index_q} : 32'b0;",
     "assign out_index = out_valid ? {19'b0, index_q}+32'd1 : 32'b0;", "OUTPUT_TAG"),
)


def bundle(output, name, mutation=None):
    directory = output/f"{name}-{uuid.uuid4().hex[:12]}"
    directory.mkdir()
    bindings = {}
    for pattern in ("rtl/*.sv", "design/*.md", "tests/*", "anvil_q1_ht2_reference/rtl/*.sv"):
        for source in sorted(ROOT.glob(pattern)):
            if not source.is_file():
                continue
            path = relative(source)
            destination = directory/path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            bindings[path] = hashlib.sha256(source.read_bytes()).hexdigest()
            if hashlib.sha256(destination.read_bytes()).hexdigest() != bindings[path]:
                raise AssertionError(f"disposable-copy hash mismatch: {path}")
    changes = []
    if mutation:
        _, _, filename, before, after, _ = mutation
        path = f"rtl/{filename}"
        destination = directory/path
        text = destination.read_text()
        if text.count(before) != 1:
            raise AssertionError(f"mutation anchor is not unique: {filename}")
        destination.write_text(text.replace(before, after, 1))
        changes.append(dict(path=path, before=before, after=after,
                            source_sha256=bindings[path],
                            mutant_sha256=hashlib.sha256(destination.read_bytes()).hexdigest()))
    with (directory/"bundle-manifest.json").open("x") as out:
        json.dump(dict(source_sha256=bindings, changes=changes), out, indent=2)
    return directory


def trial(output, directory, name, case):
    name = f"{name}-{uuid.uuid4().hex[:12]}"
    child_path = f"evidence/case-{uuid.uuid4().hex[:12]}"
    argv = ["python3", "tests/run_mutation_case.py", "--case", case, "--output", child_path]
    tool_error = None
    try:
        execute(argv, output, name, ["python3", "--version"], root=directory)
    except RuntimeError as exc:
        tool_error = str(exc)
    child = directory/child_path
    if not (child/"case-result.json").is_file() or not (child/"case.receipt.json").is_file():
        raise AssertionError(f"mutation trial did not produce settled oracle result: {tool_error}")
    result = json.loads((child/"case-result.json").read_text())
    receipt = json.loads((child/"case.receipt.json").read_text())
    if receipt["timed_out"]:
        raise AssertionError("mutation timeout is not defect sensitivity")
    return child, result, tool_error


def rejection(child, result, marker, root):
    # A compilation or launch failure can never establish sensitivity.
    compiles = list(child.rglob("compile.receipt.json"))
    simulations = list(child.rglob("simulation.receipt.json"))
    if not compiles:
        # The attention runner binds a cached compiled binary explicitly.
        binding_path = (result.get("observation") or {}).get("compile_binding")
        if not binding_path:
            raise AssertionError("no compiling mutation evidence")
        binding_file = root/binding_path
        binding_file.resolve().relative_to(root.resolve())
        binding = json.loads(binding_file.read_text())
        compilation = json.loads((root/binding["compile_receipt"]).read_text())
        if compilation["exit"] != 0 or compilation["timed_out"]:
            raise AssertionError("cached mutation compilation did not pass")
        for path, digest in binding["identity"]["source_sha256"].items():
            if hashlib.sha256((root/path).read_bytes()).hexdigest() != digest:
                raise AssertionError("cached mutation compilation is not source matched")
        binary = binding_file.parent/"compile-obj/Vattention_tb"
        if hashlib.sha256(binary.read_bytes()).hexdigest() != binding["binary_sha256"]:
            raise AssertionError("cached mutation binary has changed")
    if any(json.loads(p.read_text()).get("exit") != 0 or
           json.loads(p.read_text()).get("timed_out") for p in compiles):
        raise AssertionError("compile failure is not sensitivity")
    if not simulations:
        raise AssertionError("mutant did not execute")
    for path in simulations:
        record = json.loads(path.read_text())
        if record["timed_out"] or record["exit"] is None:
            raise AssertionError("mutant did not settle")
    if marker:
        if not any(marker in (p.parent/"simulation.stdout.txt").read_text()
                   and json.loads(p.read_text())["exit"] != 0 for p in simulations):
            raise AssertionError(f"mutant missed intended public assertion: {marker}")
        return dict(kind="public protocol/code assertion", assertion=marker)
    observation = result.get("observation") or {}
    failures = observation.get("failures", [])
    if not failures or any(json.loads(p.read_text())["exit"] != 0 for p in simulations):
        raise AssertionError("mutant missed intended completed numerical comparison")
    if not any("cosine=" in f.get("message", "") for f in failures):
        raise AssertionError("mutant failure was not the independent numerical assertion")
    return dict(kind="independent FP64 vector assertion", failures=failures)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--case", choices=[m[0] for m in MUTATIONS])
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_mutations.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    baselines, rows = {}, []
    for mutation in MUTATIONS:
        name, case, *_ = mutation
        if args.case and args.case != name:
            continue
        try:
            if case not in baselines:
                directory = bundle(output, f"baseline-{case}")
                child, result, error = trial(output, directory, f"baseline-{case}", case)
                if error or result["status"] != "passed":
                    raise AssertionError(f"sensitivity baseline did not pass: {relative(child)}")
                baselines[case] = relative(child/"case-result.json")
            directory = bundle(output, f"mutant-{name}", mutation)
            child, result, error = trial(output, directory, f"mutant-{name}", case)
            if not error or result["status"] != "failed":
                raise AssertionError("mutant was not rejected by executing oracle")
            evidence = rejection(child, result, mutation[-1], directory)
            rows.append(dict(id=name, status="passed", baseline=baselines[case],
                             mutant_result=relative(child/"case-result.json"),
                             delta_manifest=relative(directory/"bundle-manifest.json"),
                             rejection=evidence))
        except (RuntimeError, AssertionError, ValueError, OSError) as exc:
            rows.append(dict(id=name, status="failed", error=f"{type(exc).__name__}: {exc}"))
    result = dict(status="passed" if rows and all(r["status"]=="passed" for r in rows) else "failed",
                  runs=rows, selected=args.case, expected_mutations=1 if args.case else 5)
    if len(rows) != result["expected_mutations"]:
        result["status"] = "failed"
    with (output/"result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"]!="passed"),
                   result=relative(output/"result.json"),
                   timed_out=any(json.loads(p.read_text()).get("timed_out", False)
                                 for p in output.glob("*.receipt.json")))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(dict(status=result["status"],
                          runs=[{k:v for k,v in r.items() if k!="rejection"} for r in rows])),
          flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
