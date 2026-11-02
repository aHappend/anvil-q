"""Fresh declared-source reproduction, without original binaries/private state."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, execute, hashes, relative, remaining, timestamp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3","tests/run_reproduction.py",*sys.argv[1:]],cwd=".",
                   start=timestamp(),timeout=remaining(),source_sha256=hashes(),tool_version=sys.version)
    bundle = output / f"bundle-{uuid.uuid4().hex[:12]}"
    bundle.mkdir()
    bindings = {}
    for pattern in ("rtl/*.sv", "design/*.md", "tests/*", "anvil_q1_ht2_reference/rtl/*.sv"):
        for source in sorted(ROOT.glob(pattern)):
            if not source.is_file():
                continue
            path = relative(source)
            destination = bundle / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
                raise AssertionError(f"clean-bundle byte mismatch: {path}")
            bindings[path] = digest
    with (output/"bundle-manifest.json").open("x") as out:
        json.dump(dict(source_sha256=bindings,bundle=relative(bundle)),out,indent=2)
    rows = []
    for identifier,script,options in (
            ("compact-behavior","tests/run_parameters.py",["--diagnostic"]),
            ("compact-zero-latch","tests/run_synthesis.py",["--compact-only"])):
        child_path = f"evidence/reproduction-{uuid.uuid4().hex[:12]}"
        argv = ["python3",script,*options,"--output",child_path]
        try:
            execute(argv,output,identifier,["python3","--version"],root=bundle)
            result_path = bundle / child_path / "result.json"
            if not result_path.is_file():
                raise AssertionError("reproduction exited zero without complete child result")
            child = json.loads(result_path.read_text())
            if child.get("status") != "passed":
                raise AssertionError("reproduction exited zero without passing observations")
            rows.append(dict(id=identifier,status="passed",result=relative(result_path),
                             coverage=child.get("coverage_limits",[])))
        except (RuntimeError,AssertionError) as exc:
            rows.append(dict(id=identifier,status="failed",error=str(exc),
                             result=relative(bundle/child_path/"result.json")))
    result = dict(status="passed" if all(r["status"]=="passed" for r in rows) else "failed",
                  runs=rows,bundle_manifest=relative(output/"bundle-manifest.json"),
                  coverage_limits=["compact integrated model-inference reproduction"])
    with (output/"result.json").open("x") as out:
        json.dump(result,out,indent=2)
    receipt.update(exit=0 if result["status"]=="passed" else 1,end=timestamp(),
                   timed_out=remaining()<=0,result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt,out,indent=2)
    print(json.dumps(result),flush=True)
    return receipt["exit"]


if __name__=="__main__":
    raise SystemExit(main())
