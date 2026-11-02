"""Synthetic execution-lifecycle diagnostics; these are not RTL acceptance."""

import argparse
import json
import os
from pathlib import Path
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, execute, hashes, relative, remaining, timestamp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(kind="synthetic-execution-helper-diagnostic",
                   argv=["python3","tests/run_execution_helper.py",*sys.argv[1:]],cwd=".",
                   start=timestamp(),timeout=remaining(),source_sha256=hashes(),
                   tool_version=sys.version)
    directory = output / f"expired-budget-{uuid.uuid4().hex[:12]}"
    directory.mkdir()
    marker = relative(directory / "must-not-launch.txt")
    argv = ["python3","-c",f"from pathlib import Path; Path({marker!r}).write_text('launched')"]
    previous = os.environ.get("HT3_CHECK_DEADLINE")
    comparisons = 0
    try:
        os.environ["HT3_CHECK_DEADLINE"] = str(time.time()-1)
        try:
            execute(argv,directory,"expired",["python3","--version"])
        except RuntimeError:
            pass
        else:
            raise AssertionError("expired budget incorrectly reported command success")
    finally:
        if previous is None:
            os.environ.pop("HT3_CHECK_DEADLINE",None)
        else:
            os.environ["HT3_CHECK_DEADLINE"] = previous
    record = json.loads((directory/"expired.receipt.json").read_text())
    if not record["timed_out"] or record["exit"] is not None or record["timeout"] != 0:
        raise AssertionError("expired-budget receipt is not explicit and truthful")
    comparisons += 1
    if (ROOT/marker).exists():
        raise AssertionError("expired-budget command actually launched")
    comparisons += 1
    original = (directory/"expired.receipt.json").read_bytes()
    try:
        execute(argv,directory,"expired",["python3","--version"])
    except FileExistsError:
        pass
    else:
        raise AssertionError("immutable command output was overwritten")
    if (directory/"expired.receipt.json").read_bytes() != original or (ROOT/marker).exists():
        raise AssertionError("output collision changed prior evidence or executed child")
    comparisons += 1
    with (directory/"receipt.json").open("x") as out:
        json.dump(record,out,indent=2)
    result = dict(status="passed",kind="synthetic-execution-helper-diagnostic",
                  assertions=comparisons,expired_budget_receipt=relative(directory/"receipt.json"))
    with (output/"result.json").open("x") as out:
        json.dump(result,out,indent=2)
    receipt.update(exit=0,timed_out=False,end=timestamp(),result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt,out,indent=2)
    print(json.dumps(result),flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
