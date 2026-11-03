"""Quantized cache publication through the real top and public transport."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, clean_objects, execute, hashes, relative, remaining, timestamp
from reference import float_bits, quantize
from retention import artifacts_intact, digest, execution_logs_intact
from run_compatibility import (check_case, compact_checkpoint, fixture, matvec,
                               norm, rope, rounded16)


def testbench():
    text = (ROOT/"tests/inference_tb.sv").read_text()
    changes = [
        ("  task interrupted_probe;", "  integer packed_format=0, scale_base=0;\n"
         "  integer invalid_wait=0, invalid_reads=0;\n  task interrupted_probe;"),
        ("    csr(1,16'h0100,fmt|(batch_mode?4:0)|(sparse_threshold!=0?8:0),0);",
         "    if(!$value$plusargs(\"packed_format=%d\",packed_format) ||\n"
         "       !$value$plusargs(\"scale_base=%d\",scale_base) ||\n"
         "       (packed_format!=2 && packed_format!=3)) $fatal(1,\"PACKED_TOP_FORMAT\");\n"
         "    csr(1,16'h0150,packed_format,0);\n"
         "    csr(1,16'h0158,scale_base,0); csr(1,16'h015c,0,0);\n"
         "    csr(1,16'h0160,64,0);\n"
         "    csr(1,16'h0100,fmt,0);"),
        ('        $display("SUMMARY inference_probe mode=%s canceled=1 faults=%0d logits=0 debt=%0d",',
         "        fault_armed=0; invalid_reads=read_beats;\n"
         "        tid=1; tpos=1; tv=1; #1;\n"
         "        if(tr!==1) $fatal(1,\"PACKED_REJECT_NOT_READY\");\n"
         "        tick(); tv=0; invalid_wait=0;\n"
         "        while(done!==1 && invalid_wait<64) begin\n"
         "          if(ov!==0 || commit_valid!==0) $fatal(1,\"PACKED_FAILED_PREFIX_VISIBLE\");\n"
         "          tick(); invalid_wait=invalid_wait+1;\n"
         "        end\n"
         "        if(done!==1 || error!==1 || ov!==0 || qc!=0 || read_beats!=invalid_reads)\n"
         "          $fatal(1,\"PACKED_FAILED_PREFIX_ADMITTED\");\n"
         '        $display("PACKED_PREFIX_REJECTION position=1 reads=0 logits=0");\n'
         '        $display("SUMMARY inference_probe mode=%s canceled=1 faults=%0d logits=0 debt=%0d",'),
    ]
    for before, after in changes:
        if text.count(before) != 1:
            raise AssertionError("packed public transactor anchor changed")
        text = text.replace(before, after, 1)
    return text


def reference(fmt, seed):
    embedding, weights = compact_checkpoint(seed)
    cache, result = [], []
    narrow = lambda values: [rounded16(v, False) for v in values]
    width = 4 if fmt == 2 else 8
    for token, position, fresh in ((0, 0, 1), (1, 1, 0), (2, 0, 1)):
        if fresh:
            cache = []
        residual = embedding[token]
        normalized = narrow(norm(residual))
        query = narrow(rope(matvec(weights[0], normalized), position))
        keys = rope(matvec(weights[1], normalized), position)
        values = matvec(weights[2], normalized)
        stored = []
        for vector, scale in ((keys, .125), (values, .0625)):
            decoded = []
            for value in vector:
                code, error = quantize(float_bits(value), float_bits(scale), fmt == 3)
                if error:
                    raise AssertionError("invalid independent quantized fixture")
                signed = code-(1 << width) if code & (1 << (width-1)) else code
                decoded.append(signed*scale)
            stored.append(decoded)
        cache.append(stored)
        scores = [math.fsum(a*b for a, b in zip(query, key))/math.sqrt(8)
                  for key, _ in cache]
        p = [math.exp(s-max(scores)) for s in scores]
        attention = [math.fsum(prob*v[j] for prob, (_, v) in zip(p, cache))/math.fsum(p)
                     for j in range(8)]
        projected = matvec(weights[3], narrow(attention))
        residual = [a+b for a, b in zip(residual, projected)]
        normalized = narrow(norm(residual))
        gate, up = matvec(weights[4], normalized), matvec(weights[5], normalized)
        hidden = narrow([g/(1+math.exp(-g))*u for g, u in zip(gate, up)])
        down = matvec(weights[6], hidden)
        result.append(matvec(embedding, narrow(norm([a+b for a, b in zip(residual, down)]))))
    return result


def compiled(output):
    text = testbench()
    current = hashes()
    sources = [relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))]
    version = execute(["verilator", "--version"], output, "version",
                      ["verilator", "--version"]).strip()
    identity = dict(source_sha256={p: current[p] for p in
                    [*sources, "tests/inference_tb.sv", "tests/run_packed_top.py"]},
                    generated_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    tool_version=version)
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
    cache = ROOT/"evidence/compiled"
    for directory in sorted(cache.glob(f"packed-top-{key}-*")):
        binding = directory/"binding.json"
        if not binding.is_file():
            continue
        row = json.loads(binding.read_text())
        if row.get("identity") != identity or not artifacts_intact(row.get("artifact_sha256")):
            continue
        receipt = json.loads((directory/"compile.receipt.json").read_text())
        if receipt["exit"] == 0 and not receipt["timed_out"] and execution_logs_intact(receipt):
            return directory/"compile-obj/Vinference_tb", relative(binding)
    directory = cache/f"packed-top-{key}-{uuid.uuid4().hex[:12]}"
    directory.mkdir(parents=True)
    source = directory/"inference_tb.sv"
    source.write_text(text)
    objects = directory/"compile-obj"
    execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
             "--top-module", "inference_tb", "--Mdir", relative(objects),
             *sources, relative(source)], directory, "compile", ["verilator", "--version"])
    binary = objects/"Vinference_tb"
    artifacts = [binary, source, *[directory/f"compile.{suffix}" for suffix in
                 ("receipt.json", "stdout.txt", "stderr.txt")]]
    binding = directory/"binding.json"
    with binding.open("x") as out:
        json.dump(dict(identity=identity, artifact_sha256={relative(p): digest(p)
                                                          for p in artifacts}), out, indent=2)
    clean_objects(objects)
    return binary, relative(binding)


def run(output):
    binary, binding = compiled(output)
    rows = []
    for fmt in (2, 3):
        for probe in ("success", "read_error", "write_error", "new_sequence", "reset"):
            directory = output/f"format{fmt}-{probe}-{uuid.uuid4().hex[:12]}"
            directory.mkdir()
            seed = 17
            base = directory/"native-fixture"
            base.mkdir()
            native, _ = fixture(base, 0, seed)
            lines = native.read_text().splitlines()
            precision, uploads, descriptors, tokens = map(int, lines[0].split())
            scale_base = uploads*64
            scales = float_bits(.125) | (float_bits(.0625) << 32)
            vectors = directory/"vectors.txt"
            vectors.write_text("\n".join(
                [f"{precision} {uploads+1} {descriptors} {tokens}",
                 *lines[1:uploads+1], f"{scale_base:08x} {scales:0128x}",
                 *lines[uploads+1:]])+"\n")
            argv = [relative(binary), f"+vectors={relative(vectors)}",
                    f"+observations={relative(directory/'observations.txt')}",
                    f"+seed={seed}", f"+packed_format={fmt}", f"+scale_base={scale_base}"]
            if probe != "success":
                argv.append(f"+probe={probe}")
            try:
                text = execute(argv, directory, "simulation", ["verilator", "--version"])
                if probe == "success":
                    observation = check_case(directory, text, binding, 0, seed,
                                             reference(fmt, seed))
                else:
                    faults = 1 if probe in ("read_error", "write_error") else 0
                    marker = (f"SUMMARY inference_probe mode={probe} canceled=1 "
                              f"faults={faults} logits=0 debt=0")
                    if text.count(marker) != 1 or (directory/"observations.txt").stat().st_size:
                        raise AssertionError("missing/incorrect packed cancellation observation")
                    if probe != "reset" and text.count(
                            "PACKED_PREFIX_REJECTION position=1 reads=0 logits=0") != 1:
                        raise AssertionError("failed packed execution did not reject prefix decode")
                    observation = dict(status="passed", public_summary=marker,
                                       invalid_prefix_rejected=probe != "reset")
                rows.append(dict(observation, format=fmt, query_format=0, probe=probe,
                                 receipt=relative(directory/"simulation.receipt.json")))
            except (RuntimeError, AssertionError, ValueError, OSError) as exc:
                rows.append(dict(format=fmt, probe=probe, status="failed", error=str(exc)))
    return dict(status="passed" if len(rows) == 10 and all(r["status"] == "passed"
                for r in rows) else "failed", runs=rows, required_cases=10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_packed_top.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    try:
        result = run(output)
    except (RuntimeError, AssertionError, ValueError, OSError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    with (output/"result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(exit=int(result["status"] != "passed"), timed_out=remaining() <= 0,
                   end=timestamp(), result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
