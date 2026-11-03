"""Distinguish a RoPE implementation mismatch from FP32 representational limits."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import binary, decode, encode, float_bits, float_value
from run_epilogue import cases, expected
from run_unit import ROOT, hashes, relative


def cosine(a, b):
    aa, bb = sum(x*x for x in a), sum(x*x for x in b)
    return sum(x*y for x,y in zip(a,b)) / math.sqrt(aa*bb) if aa and bb else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    source = ROOT / args.input
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(kind="independent-subnormal-diagnosis",
                   argv=["python3", "tests/diagnose_subnormal.py", *sys.argv[1:]],
                   cwd=".", start=datetime.now(timezone.utc).isoformat(), timeout=None,
                   source_sha256=hashes(),
                   input_sha256={args.input: hashlib.sha256(source.read_bytes()).hexdigest()},
                   tool_version=sys.version, stdout=relative(output / "stdout.txt"),
                   stderr=relative(output / "stderr.txt"))
    if args.repair_of:
        receipt["repair_of"] = args.repair_of
    try:
        ledger = json.loads(source.read_text())
        fixtures = cases(ledger["seed"])
        diagnosis = []
        for failure in ledger["failures"]:
            c = fixtures[failure["command"]]
            if c["op"] not in (2, 3):
                raise AssertionError("diagnostic applies only to standalone RoPE/SwiGLU")
            slot = failure["slot"]
            reference = expected(c, slot)
            rounded = [float_value(float_bits(x)) for x in reference]
            sequential = []
            encoded = c["x"][slot].copy()
            if c["op"] == 2:
                for start in range(0, c["length"], 64):
                    for j in range(32):
                        angle = c["positions"][slot] * 1000000.0 ** (-2.0*j/64)
                        sin, cos = float_bits(math.sin(angle)), float_bits(math.cos(angle))
                        a, b = c["x"][slot][start+j], c["x"][slot][start+j+32]
                        ac, bs = binary(1, a, cos), binary(1, b, sin)
                        ax, bc = binary(1, a, sin), binary(1, b, cos)
                        encoded[start+j] = binary(0, ac, bs ^ 0x80000000)
                        encoded[start+j+32] = binary(0, ax, bc)
            else:
                for i, a in enumerate(c["x"][slot]):
                    exp = float_bits(math.exp(-abs(float_value(a))))
                    denominator = binary(0, 0x3F800000, exp)
                    numerator = binary(1, a, exp if a >> 31 else 0x3F800000)
                    _, sn, vn = decode(numerator)
                    _, sd, vd = decode(denominator)
                    silu = encode(vn / vd, zero_sign=sn ^ sd)
                    encoded[i] = binary(1, silu, c["aux"][slot][i])
            sequential = [float_value(x) for x in encoded]
            same = all(float_bits(a) == float_bits(b)
                       for a,b in zip(failure["actual"], sequential))
            diagnosis.append(dict(command=failure["command"], slot=slot,
                                  mode=c["op"],
                                  position=c["positions"][slot], fp16=c["fp16"],
                                  actual_cosine=cosine(failure["actual"], reference),
                                  ideal_final_fp32_rne_cosine=cosine(rounded, reference),
                                  independently_separate_rne_cosine=cosine(sequential, reference),
                                  actual_matches_separate_rne=same,
                                  required_cosine=0.9999,
                                  actual_bits=[f"{float_bits(x):08x}" for x in failure["actual"]],
                                  separate_rne_bits=[f"{x:08x}" for x in encoded]))
        (output / "diagnosis.json").write_text(json.dumps(diagnosis, indent=2) + "\n")
        text = json.dumps([{k:v for k,v in row.items() if not k.endswith("_bits")}
                           for row in diagnosis]) + "\n"
        (output / "stdout.txt").write_text(text)
        (output / "stderr.txt").write_text("")
        print(text, end="")
        receipt["exit"] = 0
    except Exception as exc:
        (output / "stdout.txt").write_text("")
        (output / "stderr.txt").write_text(f"{type(exc).__name__}: {exc}\n")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        receipt["exit"] = 1
    receipt["end"] = datetime.now(timezone.utc).isoformat()
    with (output / "receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
