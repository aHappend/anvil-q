"""Oracle-component checks; no RTL behavior or integration acceptance is claimed."""

import hashlib
import json
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from integrated import generate
from receipts import new_run, relative
from serial_reference import Geometry, PackedImage, SerialModel, rmsnorm, silu


def main():
    run = new_run("serial-oracle-component", preparation=True)
    if silu(0) != 0 or rmsnorm((65536,) * 8, (0x3c00,) * 8) != (65536,) * 8:
        raise AssertionError("analytical scalar kernel endpoint")
    zero = run / f"zero-delta-{time.time_ns()}"
    zero.mkdir()
    model, vectors, _, _ = generate(zero)
    expected = [int(value, 16) for value in vectors.read_text().split()[:8]]
    expected = [value - (1 << 32) if value & (1 << 31) else value for value in expected]
    decoder = SerialModel(PackedImage(model))
    result = decoder.evaluate(1, 0)
    if result.logits != tuple(expected) or any(result.records.values()) or (
            len(result.projections) != 36 * 7):
        raise AssertionError("constant-model analytical logit/KV comparison")
    rows = []
    for mode in (1, 2):
        for seed in (17, 29, 43):
            case = run / f"mode{mode}-seed{seed}-{time.time_ns()}"
            case.mkdir()
            model, _, _, _ = generate(case, nonzero=True, seed=seed, varied=True)
            decoder = SerialModel(PackedImage(model), Geometry(), mode)
            prefix = decoder.evaluate(1, 0)
            chain = decoder.evaluate_tree(15, [3, 3, 3, 3], [4, 0, 1, 2], (prefix,))
            branch = decoder.evaluate_tree(15, [3, 1, 3, 3], [4, 4, 0, 1], (prefix,))
            if [item.position for item in chain] != [1, 2, 3, 4] or (
                    [item.position for item in branch] != [1, 1, 2, 2]):
                raise AssertionError("causal tree positions")
            if len({item.logits for item in (prefix, *chain, *branch)}) <= 1 or (
                    not any(record for key, record in prefix.records.items() if key[1] == 0)):
                raise AssertionError("fixture has constant logits or entirely zero keys")
            for item in (prefix, *chain, *branch):
                if len(item.records) != 36 * 2 * 2 or not any(item.records.values()) or (
                        any(not any(item.projections[layer * 7 + projection])
                            for layer in range(36) for projection in (0, 1, 2, 4, 5))):
                    raise AssertionError("nonzero fixture failed to exercise its numerical paths")
            payload = [[item.position, item.token, list(item.logits),
                        sorted([list(key), value] for key, value in item.records.items())]
                       for item in (prefix, *chain, *branch)]
            encoded = json.dumps(payload, separators=(",", ":")).encode()
            expected_path = case / "oracle-values.json"
            expected_path.write_bytes(encoded + b"\n")
            rows.append({"mode": mode, "seed": seed,
                         "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
                         "values": relative(expected_path),
                         "values_sha256": hashlib.sha256(encoded + b"\n").hexdigest()})
    summary = run / "oracle-component-summary.json"
    summary.write_text(json.dumps({
        "status": "passed", "scope": "software oracle component only; no DUT comparisons",
        "analytical_zero_delta_logit_comparisons": 8, "fixtures": rows,
    }, indent=2) + "\n")
    print(json.dumps({"summary": relative(summary), "status": "passed"}), flush=True)


if __name__ == "__main__":
    main()
