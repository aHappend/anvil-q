"""Compact Icarus descriptor ABI, reset, atomicity and rejection diagnostic."""

import argparse
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from descriptors import descriptor, descriptor_cases, PINS
from execution import Experiment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    experiment = Experiment("descriptor", args.preparation, args.repair_of)
    error = None
    try:
        fixture = experiment.directory/"vectors.txt"
        cases = list(descriptor_cases())
        fixture.write_text(
            "".join(f"{word:08x}\n" for word in descriptor()) +
            "".join(f"{int(bad_index)} {int(accepted)}\n" +
                    "".join(f"{word:08x}\n" for word in image)
                    for name, image, bad_index, accepted in cases))
        experiment.receipt["cases"] = [name for name, *_ in cases]
        experiment.receipt["official_config_sha256"] = PINS
        experiment.receipt["fixture_sha256"] = hashlib.sha256(fixture.read_bytes()).hexdigest()
        experiment.receipt["tool_version"] = experiment.run(["iverilog", "-V"], "iverilog-version")
        experiment.run(["vvp", "-V"], "vvp-version")
        binary = experiment.directory/"descriptor.vvp"
        experiment.run(["iverilog", "-g2012", "-Wall", "-s", "descriptor_tb",
                        "-o", experiment.rel(binary), "rtl/anvil_q4_descriptor.sv",
                        "tests/descriptor_tb.sv"], "compile")
        output = experiment.run(["vvp", experiment.rel(binary),
                                 "+VECTORS="+experiment.rel(fixture)], "simulation")
        if f"SUMMARY descriptor comparisons={len(cases)} " not in output:
            raise AssertionError("missing descriptor coverage summary")
        experiment.receipt["comparisons"] = len(cases)
    except (RuntimeError, ValueError, AssertionError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
