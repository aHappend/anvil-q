"""Compare uninterrupted and response-debt checkpointed public-pin executions."""

import argparse
import copy
import json
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, hashes, relative, remaining, timestamp
from official_stream import compiled, run_stream, validated_chain
from retention import digest
from run_compatibility import fixture, logit_check
import numpy as np


def run(output):
    images = output/"checkpoint-images"
    images.mkdir()
    vectors, expected = fixture(images, 0, 17)
    lines = vectors.read_text().splitlines()
    _, uploads, count, _ = map(int, lines[0].split())
    payload = bytearray(uploads*64)
    for line in lines[1:uploads+1]:
        address, data = line.split()
        start = int(address, 16)
        payload[start:start+64] = int(data, 16).to_bytes(64, "little")
    descriptors = []
    for line in lines[uploads+1:uploads+count+1]:
        index, kind, layer, projection, base, length = line.split()
        descriptors.append(dict(index=int(index), kind=int(kind), layer=int(layer),
                                projection=int(projection), base=int(base, 16), length=int(length)))
    tokens = [int(line.split()[0]) for line in lines[uploads+count+1:][:2]]
    parameters = dict(NUM_LAYERS=1, HIDDEN_SIZE=8, INTERMEDIATE_SIZE=8,
                      NUM_Q_HEADS=1, NUM_KV_HEADS=1, HEAD_DIM=8,
                      GROUP_SIZE=8, VOCAB_SIZE=3, MAX_SEQ_LEN=4,
                      TILE_BEATS=3, KV_WINDOW=3, FLASH_TILE=3)
    binary, binding = compiled(output, parameters)
    results = []
    for mode, cycles in (("continuous", 450000), ("checkpointed", 509)):
        image_path = images/f"{mode}.bin"
        image_path.write_bytes(payload)
        directory = output/f"{mode}-{uuid.uuid4().hex[:12]}"
        directory.mkdir()
        image = dict(image=relative(image_path), image_bytes=len(payload),
                     image_sha256=digest(image_path))
        record = run_stream(directory, image, descriptors, tokens, {0, 1}, 3,
                            binary, binding, chunk_cycles=cycles)
        if record["status"] != "passed":
            raise AssertionError(f"{mode} checkpoint experiment did not complete")
        results.append(record)
    a, b = results
    debt_restores = []
    for path in b["checkpoints"][:-1]:
        row = json.loads((ROOT/path).read_text())
        if row["summary"]["debt"]:
            debt_restores.append(dict(binding=path, debt=row["summary"]["debt"]))
    if not debt_restores or len(b["checkpoints"]) < 2:
        raise AssertionError("no actual accepted-memory response debt crossed a restore")
    if a["measurements"] != b["measurements"] or a["summary"] != b["summary"]:
        raise AssertionError("checkpoint altered public token cycles/traffic/completion")
    metrics = []
    for position in range(2):
        x, y = (ROOT/r["observations"][position]["path"] for r in results)
        if x.read_bytes() != y.read_bytes():
            raise AssertionError("restored RTL logits differ from uninterrupted execution")
        metrics.append(logit_check(np.fromfile(y, dtype="<f4").tolist(), expected[position]))
    original = json.loads((ROOT/b["checkpoints"][-1]).read_text())
    rejected = []
    for mutation in ("source", "host_hash", "predecessor_hash", "summary", "argv"):
        row = copy.deepcopy(original)
        if mutation == "source":
            row["identity"]["source_sha256"]["tests/official_stream.cpp"] = "0"*64
        elif mutation == "host_hash":
            path = next(p for p in row["artifact_sha256"] if p.endswith(".host.bin"))
            row["artifact_sha256"][path] = "0"*64
        elif mutation == "predecessor_hash":
            row["predecessor"]["sha256"] = "0"*64
        elif mutation == "summary":
            row["summary"]["complete"] = 0
        else:
            row["argv"][-1] += "-wrong"
        path = output/f"disposable-{mutation}-{uuid.uuid4().hex[:12]}.json"
        with path.open("x") as out:
            json.dump(row, out, indent=2)
        if validated_chain(path, original["identity"]) is not None:
            raise AssertionError(f"checkpoint sensitivity accepted {mutation}")
        rejected.append(mutation)
    return dict(status="passed", scope="compact transactor/checkpoint verification",
                bit_identical_vectors=2, fp64_metrics=metrics,
                restored_memory_debt=debt_restores, retention_defects_rejected=rejected,
                streams=[r["checkpoints"] for r in results])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_stream_checkpoint.py", *sys.argv[1:]],
                   cwd=".", start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    try:
        result = run(output)
    except (OSError, RuntimeError, AssertionError, ValueError, KeyError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    with (output/"result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"] != "passed"),
                   timed_out=remaining() <= 0, result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(dict(status=result["status"], result=receipt["result"],
                          error=result.get("error"))), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
