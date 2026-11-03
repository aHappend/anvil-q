"""Estimate remaining setup from retained public observations, not RTL claims."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, hashes, relative, remaining, timestamp
from official_stream import summary
from retention import digest, execution_logs_intact


def run(binding, manifest):
    row = json.loads(binding.read_text())
    predecessor = row["predecessor"]
    previous_path = ROOT/predecessor["binding"]
    if digest(previous_path) != predecessor["sha256"]:
        raise AssertionError("throughput predecessor changed")
    previous = json.loads(previous_path.read_text())
    receipt_path = ROOT/row["receipt"]
    receipt = json.loads(receipt_path.read_text())
    if (receipt.get("exit") != 0 or receipt.get("timed_out")
            or not execution_logs_intact(receipt)
            or summary((ROOT/receipt["stdout"]).read_text()) != row["summary"]):
        raise AssertionError("throughput sample is not a settled raw public observation")
    beats = row["summary"]["reads"]-previous["summary"]["reads"]
    cycles = row["summary"]["cycles"]-previous["summary"]["cycles"]
    if beats <= 0 or cycles <= 0 or receipt["duration_s"] <= 0:
        raise AssertionError("throughput sample lacks positive observed work")
    image = json.loads(manifest.read_text())
    total = sum(r["length"]//64 for r in image["descriptors"]
                if r["kind"] in (0, 1, 3, 4, 5, 6, 7))
    pending = max(0, total-row["summary"]["reads"])
    inputs = [binding, previous_path, manifest, receipt_path,
              ROOT/receipt["stdout"], ROOT/receipt["stderr"]]
    return dict(status="passed", kind="advisory-throughput-estimate",
                scope="retained setup sample, not current-build or inference acceptance",
                input_sha256={relative(p): digest(p) for p in inputs},
                setup_total_read_beats=total, observed_read_beats=row["summary"]["reads"],
                remaining_read_beats=pending, sample_read_beats=beats, sample_cycles=cycles,
                sample_seconds=receipt["duration_s"],
                cycles_per_second=cycles/receipt["duration_s"],
                read_beats_per_second=beats/receipt["duration_s"],
                estimated_remaining_setup_seconds=pending*receipt["duration_s"]/beats,
                accepted_tokens=row["summary"]["accepted"],
                completed_tokens=row["summary"]["completed"],
                assumption="same validation path and measured average service; not a timeout")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--checkpoint-binding", required=True)
    parser.add_argument("--image-manifest", required=True)
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_setup_estimate.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    result = run(ROOT/args.checkpoint_binding, ROOT/args.image_manifest)
    with (output/"result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(exit=0, timed_out=False, end=timestamp(),
                   result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
