"""Retain a bounded preparation command without changing its exit status."""

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    parser.add_argument("--repair-of", action="append", default=[])
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9-]+", args.label):
        parser.error("label must contain lowercase letters, digits and hyphens")
    command = args.command
    if command[:1] == ["--"]:
        command = command[1:]
    if not command:
        parser.error("a command is required")
    root = Path(__file__).resolve().parent.parent
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = root / "evidence" / "preparation" / (args.label + "-" + stamp)
    directory.mkdir(parents=True, exist_ok=False)
    source_paths = sorted(p for pattern in ("rtl/*.sv", "design/*.md", "tests/*",
                                            "anvil_q3_reference/rtl/*.sv")
                          for p in root.glob(pattern) if p.is_file())
    relative = lambda p: p.relative_to(root).as_posix()
    receipt = {
        "argv": command, "cwd": ".", "timeout_s": 600,
        "repair_of": args.repair_of,
        "source_sha256": {relative(p): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in source_paths},
        "start_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "stdout_path": relative(directory / "stdout.txt"),
        "stderr_path": relative(directory / "stderr.txt"),
        "tool_version_argv": ["python3", "--version"],
    }
    version = subprocess.run(["python3", "--version"], cwd=root,
                             capture_output=True, text=True, check=False)
    receipt["tool_version"] = version.stdout.strip()
    with (directory / "stdout.txt").open("wb") as stdout, (
            directory / "stderr.txt").open("wb") as stderr:
        try:
            child = subprocess.run(command, cwd=root, stdout=stdout, stderr=stderr,
                                   timeout=600, check=False)
            receipt.update(exit_code=child.returncode, timed_out=False)
        except subprocess.TimeoutExpired:
            receipt.update(exit_code=124, timed_out=True)
        except OSError as exc:
            stderr.write(str(exc).encode())
            receipt.update(exit_code=127, timed_out=False)
    receipt["end_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (directory / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(relative(directory / "receipt.json"), flush=True)
    return receipt["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
