"""Execute real official-image packing or compact packing sensitivity controls."""

import argparse
import io
import json
from pathlib import Path
import sys
import uuid

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, hashes, relative, remaining, timestamp
from official_image import build, check_panel, layout, panel_bytes
from run_benchmarks import prepare


def self_test():
    # Non-square/non-panel-sized matrix exposes both transposition and padding.
    matrix = np.array([[0x3e00+row*7+column for column in range(5)]
                       for row in range(70)], dtype="<u2")
    payload = b"".join(panel_bytes(matrix))
    check_panel(io.BytesIO(payload), 0, matrix)
    for row in range(70):
        for column in range(5):
            offset = ((row//64)*5+column)*128+(row%64)*2
            if int.from_bytes(payload[offset:offset+2], "little") != int(matrix[row,column]):
                raise AssertionError("panel address formula mismatch")
    rejected = []
    for name in ("transpose", "padding"):
        corrupt = bytearray(payload)
        if name == "transpose":
            corrupt[:128] = matrix[:64, 1].tobytes()
        else:
            corrupt[(5+0)*128+6*2] = 1
        try:
            check_panel(io.BytesIO(corrupt), 0, matrix)
        except AssertionError:
            rejected.append(name)
        else:
            raise AssertionError(f"packing checker accepted corruption: {name}")
    return dict(status="passed", scope="compact image-packer harness only",
                checked_codes=350, rejected=rejected)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_official_image.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    try:
        if args.self_test:
            result = self_test()
        else:
            _, bindings, failures = prepare(output)
            if failures:
                raise AssertionError(f"official input acquisition failed: {failures}")
            pin = json.loads((ROOT/"tests/official_inputs.json").read_text())
            images = output/"checkpoint-images"
            images.mkdir()
            result = build(images/f"official-image-{uuid.uuid4().hex[:12]}",
                           ROOT/bindings["model.safetensors"]["path"],
                           ROOT/bindings["config.json"]["path"],
                           pin["model"]["files"]["model.safetensors"])
    except (OSError, RuntimeError, AssertionError, ValueError, KeyError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    with (output/"result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"] != "passed"),
                   timed_out=remaining() <= 0, result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ("descriptors","geometry")}),
          flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
