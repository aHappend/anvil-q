"""Source-bound preparation entry points; these are not mandatory L1 acceptance."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import execute, new_run


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("probe", choices=("fp32", "exp", "attention", "attention-matrix",
                                         "tensor", "native", "native-large", "synthesis",
                                         "arithmetic", "compatibility", "integrated",
                                         "geometries", "delivery", "profile"))
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    commands = {
        "fp32": ["python3", "tests/numerics.py", "--compact", "--preparation"],
        "exp": ["python3", "tests/numerics.py", "--exp", "--compact", "--preparation"],
        "attention": ["python3", "tests/attention.py", "--preparation"],
        "attention-matrix": ["python3", "tests/attention.py", "--matrix", "--preparation"],
        "tensor": ["python3", "tests/tensor.py", "--preparation"],
        "native": ["python3", "tests/behavior.py", "--preparation"],
        "native-large": ["python3", "tests/behavior.py", "--preparation", "--large"],
        "synthesis": ["python3", "tests/synthesis.py", "--preparation", "--singleton"],
        "arithmetic": ["python3", "tests/numerics.py", "--arithmetic", "--preparation"],
        "compatibility": ["python3", "tests/compatibility.py", "--preparation"],
        "integrated": ["python3", "tests/integrated.py", "--preparation"],
        "geometries": ["python3", "tests/behavior.py", "--geometries", "--preparation"],
        "delivery": ["python3", "tests/delivery.py", "--preparation"],
        "profile": ["python3", "tests/compatibility.py", "--mode", "4", "--preparation"],
    }
    execute(new_run(f"{args.probe}-launch", preparation=True),
            commands[args.probe], timeout=2700, repair_of=args.repair_of)
