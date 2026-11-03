"""Source-bound preparation entry points; these are not mandatory L1 acceptance."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import execute, new_run


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("probe", choices=("fp32", "exp", "attention"))
    args = parser.parse_args()
    commands = {
        "fp32": ["python3", "tests/numerics.py", "--compact", "--preparation"],
        "exp": ["python3", "tests/numerics.py", "--exp", "--compact", "--preparation"],
        "attention": ["python3", "tests/attention.py", "--preparation"],
    }
    execute(new_run(f"{args.probe}-launch", preparation=True),
            commands[args.probe], timeout=600)
