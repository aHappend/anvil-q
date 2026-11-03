"""Run an owned bounded diagnostic in a fresh project-local receipt namespace."""

import argparse
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, execute, relative


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stem", required=True)
    parser.add_argument("--repair-of")
    parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.stem.replace("-", "").isalnum():
        parser.error("stem must be alphanumeric with optional hyphens")
    argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
    if len(argv) < 2 or argv[0] != "python3" or not argv[1].startswith("tests/"):
        parser.error("diagnostics must execute a project-owned Python test script")
    script = (ROOT / argv[1]).resolve()
    script.relative_to(ROOT / "tests")
    output = ROOT / "evidence/preparation" / f"{args.stem}-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True)
    child = output / f"shard-{uuid.uuid4().hex[:12]}"
    command = [*argv, "--output", relative(child)]
    try:
        execute(command, output, "tool", ["python3", "--version"])
    except RuntimeError:
        pass
    record = json.loads((output / "tool.receipt.json").read_text())
    nested_timeouts = []
    for path in child.rglob("*.json"):
        if path.name != "receipt.json" and not path.name.endswith(".receipt.json"):
            continue
        if json.loads(path.read_text()).get("timed_out", False):
            nested_timeouts.append(relative(path))
    record.update(kind="bounded-verifier-preparation",
                  outer_execution_timed_out=record["timed_out"],
                  timed_out=record["timed_out"] or bool(nested_timeouts),
                  nested_timeout_receipts=nested_timeouts,
                  launcher_argv=["python3", "tests/prepare.py", *sys.argv[1:]])
    if args.repair_of:
        record["repair_of"] = args.repair_of
    with (output / "receipt.json").open("x") as out:
        json.dump(record, out, indent=2)
        out.write("\n")
    print(json.dumps(dict(receipt=relative(output/"receipt.json"), exit=record["exit"],
                          timed_out=record["timed_out"])), flush=True)
    return 1 if record["timed_out"] or record["exit"] != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
