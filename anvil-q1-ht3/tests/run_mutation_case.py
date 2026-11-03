"""Focused sensitivity baselines using the unchanged independent public oracles."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, clean_objects, hashes, relative, remaining, timestamp
from reference import convert, float_bits


def epilogue_cases(seed):
    rows = []
    for op in (1, 2, 4):
        length = 64
        x = [[float_bits((i-29)*(0.00005 if op == 1 else 0.03125))
              for i in range(length)] for _ in range(4)]
        aux = [[float_bits((i % 7-3)*0.125) for i in range(length)] for _ in range(4)]
        for slot in (1, 3):
            x[slot] = [0x7FC00000]*length
            aux[slot] = [0x7F800000]*length
        rows.append(dict(op=op, fp16=0, mask=5, length=length, x=x, aux=aux,
                         gamma=[convert(float_bits(1), False)]*length,
                         positions=[1, 0, 32767, 0], error=0))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=("epilogue", "packed_cache", "attention"), required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_mutation_case.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    try:
        if args.case == "epilogue":
            import run_epilogue
            # A separate, finite sensitivity stimulus. The mathematical oracle,
            # narrowing, vector thresholds and public transaction checks are unchanged.
            run_epilogue.cases = epilogue_cases
            observed = run_epilogue.run(17, output)
        elif args.case == "packed_cache":
            from run_packed_cache import run
            observed = run(output)
        else:
            from run_attention import run_case
            observed = run_case(output, 17, 3, 1, 8, 1, diagnostic=True)
        result = dict(status="passed", case=args.case, observation=observed)
    except (RuntimeError, AssertionError, ValueError, OSError) as exc:
        old = output/"result.json"
        observation = json.loads(old.read_text()) if old.is_file() else None
        result = dict(status="failed", case=args.case, error=f"{type(exc).__name__}: {exc}",
                      observation=observation)
    finally:
        objects = output/"compile-obj"
        if objects.is_dir():
            clean_objects(objects)
    # Existing oracle results, including the complete mismatch vectors, are immutable.
    with (output/"case-result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"]!="passed"),
                   result=relative(output/"case-result.json"),
                   timed_out=any(json.loads(p.read_text()).get("timed_out", False)
                                 for p in output.rglob("*.receipt.json")))
    with (output/"case.receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!="observation"}), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
