"""FP32 -> provisional codes -> real packed DMA -> reader -> attention."""

import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, clean_objects, execute, hashes, relative, remaining, timestamp
from reference import convert, float_bits, float_value, quantize, vector_check


def fixtures(path):
    references = {}
    with path.open("x") as out:
        for fmt in range(4):
            ks, vs = float_bits(0.125), float_bits(0.0625)
            out.write(f"{fmt} {ks:08x} {vs:08x}\n")
            query_bits = [convert(float_bits((i % 7-3)/512), False) for i in range(128)]
            query = [float_value(convert(bits, False, True)) for bits in query_bits]
            for bits in query_bits:
                out.write(f"{bits:04x}\n")
            stored = []
            for row in range(2):
                keys, values = [], []
                for col in range(128):
                    code = row*128+col-128
                    # Exact ties, saturation and negative values include every signed
                    # INT8 code; the offset exercises rounding before any BF16 boundary.
                    a = code*0.125 + (0.0625 if col % 5 == 0 else 0)
                    b = (127-row*128-col)*0.0625 + (0.03125 if col % 7 == 0 else 0)
                    x, y = float_bits(a), float_bits(b)
                    if fmt < 2:
                        key, value = convert(x, fmt == 1), convert(y, fmt == 1)
                    else:
                        key, ke = quantize(x, ks, fmt == 3)
                        value, ve = quantize(y, vs, fmt == 3)
                        assert not ke and not ve
                    keys.append(key)
                    values.append(value)
                    out.write(f"{x:08x} {y:08x} {key:04x} {value:04x}\n")
                width = (16, 16, 4, 8)[fmt]
                beats = (128*width+511)//512
                for words in (keys, values):
                    packed = sum(word << (i*width) for i, word in enumerate(words))
                    for beat in range(beats):
                        out.write(f"{(packed >> (512*beat)) & ((1 << 512)-1):0128x}\n")
                if fmt < 2:
                    stored.append(([float_value(convert(k, fmt == 1, True)) for k in keys],
                                   [float_value(convert(v, fmt == 1, True)) for v in values]))
                else:
                    signed = lambda code: code-(1 << width) if code & (1 << (width-1)) else code
                    stored.append(([signed(k)*float_value(ks) for k in keys],
                                   [signed(v)*float_value(vs) for v in values]))
            expected = []
            for head in range(2):
                start = head*64
                scores = [math.fsum(a*b for a, b in
                                    zip(query[start:start+64], key[start:start+64]))/8
                          for key, _ in stored]
                probabilities = [math.exp(score-max(scores)) for score in scores]
                denominator = math.fsum(probabilities)
                expected.extend(math.fsum(p*value[j] for p, (_, value) in
                                          zip(probabilities, stored))/denominator
                                for j in range(start, start+64))
            references[fmt] = expected
    return references


def run(output):
    vectors, observations = output/"vectors.txt", output/"observations.txt"
    expected = fixtures(vectors)
    objects = output/"compile-obj"
    sources = [relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))]
    execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
             "--top-module", "packed_cache_tb", "--Mdir", relative(objects),
             *sources, "tests/packed_cache_tb.sv"], output, "compile",
            ["verilator", "--version"])
    text = execute([relative(objects/"Vpacked_cache_tb"), f"+vectors={relative(vectors)}",
                    f"+observations={relative(observations)}"], output, "simulation",
                   ["verilator", "--version"])
    clean_objects(objects)
    summary = re.search(r"SUMMARY packed_cache commands=(\d+) codes=(\d+) writes=(\d+) "
                        r"reads=(\d+) holds=(\d+) zero_returns=(\d+) delayed_returns=(\d+) "
                        r"attention_outputs=(\d+)", text)
    if not summary or tuple(map(int, (summary[1], summary[2], summary[8]))) != (4, 2048, 512):
        raise AssertionError("incomplete packed-cache observations")
    faults = re.findall(r"^SUMMARY packed_faults dma_errors=(\d+) abort_drains=(\d+) "
                        r"reset_debts=(\d+) poisoned_rows=(\d+) flush_invalidations=(\d+)$",
                        text, re.MULTILINE)
    if len(faults) != 1 or tuple(map(int, faults[0])) != (4, 4, 4, 4, 4):
        raise AssertionError("missing packed fault/publication observations")
    actual = {fmt: [] for fmt in range(4)}
    for line in observations.read_text().splitlines():
        fmt, index, bits = line.split()
        fmt, index = int(fmt), int(index)
        if fmt not in actual or index != len(actual[fmt]):
            raise AssertionError("duplicate or misassociated packed attention result")
        actual[fmt].append(float_value(int(bits, 16)))
    vectors_checked = []
    for fmt in range(4):
        for head in range(2):
            start = head*64
            metric = vector_check(actual[fmt][start:start+64], expected[fmt][start:start+64])
            vectors_checked.append(dict(format=fmt, head=head, metric=metric))
    return dict(status="passed", raw_summary=summary[0], vectors=vectors_checked,
                faults=dict(zip(("dma_errors", "abort_drains", "reset_debts",
                                 "poisoned_rows", "flush_invalidations"), map(int, faults[0]))),
                coverage_limits=["integrated quantized-cache prefix-publication matrix"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_packed_cache.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    try:
        result = run(output)
    except (RuntimeError, AssertionError, ValueError, OSError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    with (output/"result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"] != "passed"),
                   result=relative(output/"result.json"),
                   timed_out=any(json.loads(p.read_text()).get("timed_out", False)
                                 for p in output.glob("*.receipt.json")))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
