"""Public-pin greedy graph, ordered logits and complete 36-layer KV comparisons."""

import argparse
import hashlib
import json
import random
import sys

sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipts import execute, new_run, relative, cleanup_build
from reference import kv_encode


def pack(values, width):
    return sum(value << (width * index) for index, value in enumerate(values))


def expected_graph(mask, tokens, parents, root, scores):
    positions, visibility = [0] * 4, [0] * 4
    if not mask or root >= 8:
        raise ValueError("invalid root")
    for node in range(4):
        if not mask & (1 << node):
            if tokens[node] or parents[node]:
                raise ValueError("inactive payload")
            continue
        parent = parents[node]
        if tokens[node] >= 8 or (parent != 4 and (
                parent >= node or not mask & (1 << parent))):
            raise ValueError("invalid node")
        if any(mask & (1 << prior) and parents[prior] == parent and
               tokens[prior] == tokens[node] for prior in range(node)):
            raise ValueError("duplicate sibling")
        positions[node] = 0 if parent == 4 else positions[parent] + 1
        visibility[node] = (1 << node) | (0 if parent == 4 else visibility[parent])
    targets = [max(range(8), key=lambda index: (row[index], -index)) for row in scores]
    path, parent, target = [], 4, root
    while len(path) < 4:
        children = [node for node in range(4) if mask & (1 << node) and
                    parents[node] == parent and tokens[node] == target]
        if not children:
            break
        parent = children[0]
        path.append(parent)
        target = targets[parent]
    return positions, visibility, path, target


def generate(path, mode, seed):
    rng = random.Random(seed)
    fixtures = []
    for length in range(5):
        scores = [[rng.randrange(-200000, -100000) for _ in range(8)] for _ in range(4)]
        for node in range(4):
            target = node + 2 if node + 1 < length else 7
            scores[node][target] = 1000
        fixtures.append((15, [1, 2, 3, 4], [4, 0, 1, 2], 1 if length else 7, scores))
    tie_scores = [[-32768] * 8 for _ in range(4)]
    for row in tie_scores:
        row[2] = row[6] = 32768
    fixtures.extend([
        (15, [1, 3, 2, 4], [4, 4, 0, 1], 1, tie_scores),
        (15, [1, 2, 3, 2], [4, 0, 0, 2], 1, tie_scores),
        (12, [0, 0, 2, 3], [0, 0, 4, 2], 2, tie_scores),
    ])
    for mask, tokens, parents, root in (
            (0, [0]*4, [0]*4, 1),
            (1, [8, 0, 0, 0], [4, 0, 0, 0], 1),
            (1, [1, 0, 0, 0], [0, 0, 0, 0], 1),
            (1, [1, 0, 0, 0], [1, 0, 0, 0], 1),
            (2, [0, 1, 0, 0], [0, 0, 0, 0], 1),
            (3, [1, 1, 0, 0], [4, 4, 0, 0], 1),
            (1, [1, 1, 0, 0], [4, 0, 0, 0], 1),
            (1, [1, 0, 0, 0], [4, 0, 0, 0], 8)):
        fixtures.append((mask, tokens, parents, root, tie_scores))
    text = [str(len(fixtures))]
    histogram = [0] * 5
    invalid = 0
    for mask, tokens, parents, root, scores in fixtures:
        try:
            positions, visibility, nodes, target = expected_graph(
                mask, tokens, parents, root, scores)
            bad = 0
            histogram[len(nodes)] += 1
        except ValueError:
            bad, positions, visibility, nodes, target = 1, [0]*4, [0]*4, [], 0
            invalid += 1
        text.append(f"{mask:x} {pack(tokens,32):x} {pack(parents,3):x} {root:x} "
                    f"{bad} {pack(positions,32):x} {pack(visibility,4):x} "
                    f"{sum(1<<node for node in nodes):x} {len(nodes)} "
                    f"{pack([tokens[node] for node in nodes],32):x} "
                    f"{target:x} {pack(nodes,2):x}")
        text.extend(f"{score & 0xffffffff:x}" for row in scores for score in row)
        for _ in range(4 * 36 * 2):
            text.append(f"{kv_encode([rng.randrange(-262144,262145) for _ in range(6)],mode):x}")
    path.write_text("\n".join(text) + "\n")
    return {"cases": len(fixtures), "invalid": invalid, "acceptance_lengths": histogram}


def run_spec(run, mode, seed):
    path = run / "spec-vectors.txt"
    expected = generate(path, mode, seed)
    obj = run / "spec-obj"
    execute(run, "spec-compile", [
        "verilator", "--binary", "--timing", "-Wno-fatal",
        "--top-module", "speculative_tb", f"-GCACHE_MODE={mode}",
        "--Mdir", relative(obj), "-j", "2",
        "anvil_q3_ht_reference/rtl/anvil_q3_ht_kv_codec.sv",
        "rtl/anvil_q3_ht2_kv_commit_engine.sv",
        "rtl/anvil_q3_ht2_spec_verifier.sv", "tests/speculative_tb.sv"],
        ["verilator", "--version"])
    try:
        result = execute(run, "spec-simulate",
                         [relative(obj / "Vspeculative_tb"), f"+vectors={relative(path)}"],
                         ["verilator", "--version"])
    finally:
        cleanup_build(obj)
    outputs = [json.loads(line.removeprefix("RESULT ")) for line in
               (result / "stdout.txt").read_text().splitlines() if line.startswith("RESULT ")]
    if len(outputs) != 1 or outputs[0]["cases"] != expected["cases"] or (
            outputs[0]["invalid"] != expected["invalid"] or
            outputs[0]["lengths"] != expected["acceptance_lengths"]):
        raise AssertionError("missing complete greedy/graph comparisons")
    summary = {"mode": mode, "seed": seed, "observed": outputs[0],
               "vector_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
               "receipt": relative(result / "receipt.json")}
    (run / "spec-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=int, choices=(1, 2), default=1)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run = new_run("speculative", preparation=True, repair_of=args.repair_of)
    print(f"speculative evidence: {relative(run)}", flush=True)
    try:
        print(json.dumps(run_spec(run, args.mode, args.seed), sort_keys=True))
    except (RuntimeError, AssertionError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
