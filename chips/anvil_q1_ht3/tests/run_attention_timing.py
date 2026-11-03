"""Frozen no-stall attention timing, including resident successor tile handoff."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, clean_objects, execute, hashes, relative, remaining, timestamp
from retention import digest


def expected_cycles(context, dimension, tile, fmt):
    # SPEC: B=E+D; F0=B+137; publication follows F0+n*(D+1)+2.
    # Publication is post-edge, admission is the next edge, SCORE_READ the next.
    n = min(context, tile)
    first_read = dimension+137+n*(dimension+1)+2+int(n<tile)+2
    lengths = [min(tile, context-start) for start in range(0, context, tile)]
    interval = 47 if fmt>=2 else 33
    last_release = first_read
    for index, count in enumerate(lengths):
        if index:
            last_release += 1
        last_release += count*(interval*dimension+60)+10*dimension+47
    return [last_release+71*(index+1) for index in range(dimension)], last_release+71*dimension+1


def compiled(dimension, tile):
    cache = ROOT/"evidence/compiled"
    cache.mkdir(parents=True, exist_ok=True)
    version_dir = cache/f"attention-timing-version-{uuid.uuid4().hex[:12]}"
    version_dir.mkdir()
    paths = [relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))]+["tests/attention_timing_tb.sv"]
    current = hashes()
    version = execute(["verilator", "--version"], version_dir, "version",
                      ["verilator", "--version"]).strip()
    identity = dict(source_sha256={p: current[p] for p in paths},
                    tool_version=version, dimension=dimension, tile=tile)
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
    for directory in sorted(cache.glob(f"attention-timing-{key}-*")):
        binding, binary = directory/"binding.json", directory/"compile-obj/Vattention_timing_tb"
        if not binding.is_file() or not binary.is_file():
            continue
        record = json.loads(binding.read_text())
        receipt = json.loads((directory/"compile.receipt.json").read_text())
        if (record.get("identity")==identity and receipt.get("exit")==0
                and not receipt.get("timed_out") and record.get("binary_sha256")==digest(binary)):
            return binary, relative(binding)
    directory = cache/f"attention-timing-{key}-{uuid.uuid4().hex[:12]}"
    directory.mkdir()
    objects = directory/"compile-obj"
    execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
             "--top-module", "attention_timing_tb", f"-GD={dimension}", f"-GTILE={tile}",
             "--Mdir", relative(objects), *paths],
            directory, "compile", ["verilator", "--version"])
    binary = objects/"Vattention_timing_tb"
    with (directory/"binding.json").open("x") as out:
        json.dump(dict(identity=identity, binary_sha256=digest(binary),
                       compile_receipt=relative(directory/"compile.receipt.json")), out, indent=2)
    clean_objects(objects)
    return binary, relative(directory/"binding.json")


def run_case(directory, binary, binding, context, dimension, tile, fmt):
    observations = directory/"observations.txt"
    text = execute([relative(binary), f"+observations={relative(observations)}",
                    f"+context={context}", f"+format={fmt}"],
                   directory, "simulation", ["verilator", "--version"])
    expected = (f"SUMMARY attention_timing format={fmt} context={context} dim={dimension} "
                f"tile={tile} inputs={dimension} outputs={dimension} "
                f"requests={context*dimension} responses={context*dimension}")
    if text.count(expected)!=1:
        raise AssertionError("incomplete public attention temporal observations")
    supply = re.search(r"TIMING first_query=(\d+) last_query=(\d+) first_kv=(\d+) last_kv=(\d+)",text)
    if supply is None or int(supply[1])!=1 or int(supply[2])!=dimension:
        raise AssertionError("continuous query timing precondition did not occur")
    if int(supply[3])!=dimension+140:
        raise AssertionError(f"first KV acceptance edge={supply[3]}, "
                             f"frozen query/root/inverse/start edge={dimension+140}")
    output_cycles, done_cycle = expected_cycles(context, dimension, tile, fmt)
    lines = observations.read_text().splitlines()
    if len(lines)!=dimension+1 or lines[-1]!=f"D {done_cycle}":
        raise AssertionError(f"attention done edge: observed={lines[-1:]}, expected={done_cycle}")
    for index, (line, cycle) in enumerate(zip(lines, output_cycles)):
        if line != f"O {index} {0x3f800000:032x} {cycle}":
            raise AssertionError(f"attention output edge: observed={line}, "
                                 f"expected_index={index}, expected_cycle={cycle}")
    return dict(status="passed", context=context, dimension=dimension, tile=tile,
                format=fmt, resident_handoffs=(context-1)//tile,
                output_cycles=output_cycles, done_cycle=done_cycle, binary_binding=binding,
                raw_summary=expected)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--diagnostic", action="store_true")
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_attention_timing.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    rows = []
    for dimension, tile in ([(8,3)] if args.diagnostic else
                            [(8,t) for t in (1,3,16,128)]+[(64,3)]):
        try:
            binary, binding = compiled(dimension, tile)
            for context in ([2*tile] if args.diagnostic else (2*tile, 2*tile+1)):
                for fmt in ((0,) if args.diagnostic else range(4)):
                    directory = output/f"d{dimension}-t{tile}-c{context}-f{fmt}-{uuid.uuid4().hex[:8]}"
                    directory.mkdir()
                    try:
                        rows.append(run_case(directory,binary,binding,context,dimension,tile,fmt))
                    except (RuntimeError, AssertionError, ValueError, OSError) as exc:
                        rows.append(dict(status="failed", dimension=dimension, tile=tile,
                                         context=context, format=fmt, directory=relative(directory),
                                         error=str(exc)))
        except (RuntimeError, AssertionError, ValueError, OSError) as exc:
            rows.append(dict(status="failed", dimension=dimension, tile=tile, error=str(exc)))
    result = dict(status="passed" if rows and all(r["status"]=="passed" for r in rows) else "failed",
                  runs=rows, coverage_limits=["selected temporal diagnostic"] if args.diagnostic else [])
    with (output/"result.json").open("x") as out:
        json.dump(result,out,indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"]!="passed"),
                   result=relative(output/"result.json"),
                   timed_out=any(json.loads(p.read_text()).get("timed_out", False)
                                 for p in output.rglob("*.receipt.json")))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt,out,indent=2)
    print(json.dumps(result),flush=True)
    return receipt["exit"]


if __name__=="__main__":
    raise SystemExit(main())
