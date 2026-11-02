"""Quantized causal-tree/GQA context checks against an independent scalar oracle."""

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipts import ROOT, execute, new_run, relative, cleanup_build
from reference import causal_context, kv_encode, kv_decode


SOURCES = [
    "anvil_q3_ht_reference/rtl/" + name + ".sv" for name in (
        "anvil_q3_00_pkg", "anvil_q3_mem_port", "anvil_q3_multiplier",
        "anvil_q3_add128", "anvil_q3_accumulator", "anvil_q3_divider",
        "anvil_q3_signed_divider", "anvil_q3_isqrt", "anvil_q3_exp",
        "anvil_q3_ht_attention", "anvil_q3_ht_kv_codec")
] + ["rtl/anvil_q3_ht2_kv_read_port.sv", "rtl/anvil_q3_ht2_tree_attention.sv",
     "tests/tree_attention_tb.sv"]


def generate(path, seed, mode):
    rng = random.Random(seed)
    layers, heads, dim, maximum, hidden = 2, 2, 4, 8, 64
    records_per_token = layers * 2 * heads
    fixtures = []
    for layer in range(layers):
        for subset in range(8):
            ancestry = [n for n in range(3) if subset & (1 << n)] + [3]
            parents = [4] * 4
            depth = [0] * 4
            for a, b in zip(ancestry, ancestry[1:]):
                parents[b] = a
                depth[b] = depth[a] + 1
            fixtures.append((layer, 3, parents, depth, ancestry))
    for parents in ([4, 0, 1, 2], [4, 4, 0, 1], [4, 0, 0, 2]):
        for node in range(4):
            ancestry = []
            ancestor = node
            while ancestor != 4:
                ancestry.append(ancestor)
                ancestor = parents[ancestor]
            ancestry.reverse()
            depth = [0 if p == 4 else 1 for p in parents]
            for n, p in enumerate(parents):
                depth[n] = 0 if p == 4 else depth[p] + 1
            fixtures.append((node & 1, node, parents, depth, ancestry))
    text = [str(len(fixtures))]
    for layer, node, parents, depth, ancestry in fixtures:
        base = 2
        positions = [base + d for d in depth]
        visibility = sum(1 << n for n in ancestry)
        query = [rng.randrange(-256, 257) * 256 for _ in range(hidden)]
        image = [0] * ((maximum + 4) * records_per_token)
        decoded = {}
        for private in (False, True):
            for token in range(4 if private else maximum):
                for record_layer in range(layers):
                    for value in range(2):
                        for head in range(heads):
                            values = [rng.randrange(-262144, 262145) for _ in range(dim)]
                            record = kv_encode(values, mode)
                            key = (private, token, record_layer, value, head)
                            decoded[key] = kv_decode(record, dim, mode)
                            ordinal = (record_layer * 2 + value) * heads + head
                            index = (maximum * records_per_token + token * records_per_token +
                                     ordinal if private else
                                     ((record_layer * 2 + value) * maximum + token) * heads + head)
                            image[index] = record
        expected = []
        for qhead in range(heads * 8):
            kvhead = qhead // 8
            causal = [(False, p) for p in range(base)] + [(True, n) for n in ancestry]
            keys = [decoded[private, token, layer, 0, kvhead] for private, token in causal]
            values = [decoded[private, token, layer, 1, kvhead] for private, token in causal]
            expected.extend(causal_context(query[qhead * dim:(qhead + 1) * dim],
                                           keys, values, dim))
        text.append(f"{layer} {base} {node} f {visibility:x} "
                    f"{sum(p << (32*n) for n,p in enumerate(positions)):x} "
                    f"{sum(p << (3*n) for n,p in enumerate(parents)):x}")
        text.extend(f"{value & 0xffffffff:x}" for value in query + expected)
        text.extend(f"{record:x}" for record in image)
    path.write_text("\n".join(text) + "\n")
    return len(fixtures)


def run_tree(run, mode, seed, mutant=None, residency=3):
    path = run / f"tree-mode{mode}-seed{seed}.txt"
    cases = generate(path, seed, mode)
    sources = list(SOURCES)
    if mutant:
        if mutant == "gqa":
            original_path = ROOT / "anvil_q3_ht_reference/rtl/anvil_q3_ht_attention.sv"
            before = "kv_cmd_head=kv_cmd_valid ? head>>3 : 32'd0;"
            after = "kv_cmd_head=kv_cmd_valid ? ((head>>3)^32'd1) : 32'd0;"
        else:
            original_path = ROOT / "rtl/anvil_q3_ht2_kv_read_port.sv"
            before = "node<=private_node; lane<=6'(cmd_dim&(CAP-1));"
            after = "node<=(private_node^2'd1); lane<=6'(cmd_dim&(CAP-1));"
        original = original_path.read_text()
        if original.count(before) != 1:
            raise AssertionError("tree mutation target not unique")
        copy = run / f"mutant-{original_path.name}"
        copy.write_text(original.replace(before, after))
        sources[sources.index(relative(original_path))] = relative(copy)
        (run / "mutation.json").write_text(json.dumps({
            "defect": mutant, "source": relative(original_path),
            "source_sha256": hashlib.sha256(original_path.read_bytes()).hexdigest(),
            "mutant": relative(copy), "before": before, "after": after,
        }, indent=2) + "\n")
    obj = run / "tree-obj"
    execute(run, "tree-compile", ["verilator", "--binary", "--timing", "-Wno-fatal",
            "--top-module", "tree_attention_tb", f"-GCACHE_MODE={mode}",
            f"-GKV_RESIDENT_GROUPS={residency}", "--Mdir", relative(obj),
            "-j", "2", *sources], ["verilator", "--version"])
    try:
        output = execute(run, "tree-simulate",
                         [relative(obj / "Vtree_attention_tb"), f"+vectors={relative(path)}"],
                         ["verilator", "--version"], expect=-6 if mutant else 0)
    finally:
        cleanup_build(obj)
    raw = (output / "stdout.txt").read_text()
    records = [json.loads(line.removeprefix("RESULT ")) for line in raw.splitlines()
               if line.startswith("RESULT ")]
    if mutant:
        diagnostic = "tree context mismatch" if mutant == "gqa" else "tree sibling visibility leak"
        if records or diagnostic not in raw:
            raise AssertionError("tree mutant failed without targeted discrimination")
        observed = {"defect": mutant, "discrimination": diagnostic}
    else:
        if len(records) != 1 or records[0]["cases"] != cases or (
                records[0]["contexts"] != cases * 64):
            raise AssertionError("missing complete independently compared tree result")
        observed = records[0]
    summary = {"mode": mode, "seed": seed, "residency": residency, "observed": observed,
               "vector_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
               "receipt": relative(output / "receipt.json")}
    (run / "tree-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=int, choices=(1, 2), default=1)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--residency", type=int, choices=(1, 3), default=3)
    parser.add_argument("--mutant", choices=("gqa", "sibling"))
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run = new_run("tree-attention", preparation=True, repair_of=args.repair_of)
    print(f"tree evidence: {relative(run)}", flush=True)
    try:
        print(json.dumps(run_tree(run, args.mode, args.seed, args.mutant, args.residency),
                         sort_keys=True))
    except (RuntimeError, AssertionError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
