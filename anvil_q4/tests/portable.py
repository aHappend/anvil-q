"""Execute a fresh source-only reproduction, without original caches or metadata."""

import argparse
import hashlib
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import Experiment, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    args = parser.parse_args()
    experiment = Experiment("portable", args.preparation)
    error = None
    try:
        experiment.receipt["tool_version"] = experiment.run(["python3", "--version"], "version")
        identity = hashlib.sha256(str(experiment.receipt["source_sha256"]).encode()).hexdigest()[:12]
        bundle = experiment.directory/f"bundle-{identity}"
        bundle.mkdir()
        sources = {}
        for pattern in ("rtl/*.sv", "design/*.md", "tests/*"):
            for source in sorted(ROOT.glob(pattern)):
                if not source.is_file():
                    continue
                relative = source.relative_to(ROOT)
                destination = bundle/relative
                destination.parent.mkdir(exist_ok=True, parents=True)
                shutil.copyfile(source, destination)
                sources[relative.as_posix()] = hashlib.sha256(destination.read_bytes()).hexdigest()
        experiment.receipt["copied_source_sha256"] = sources
        experiment.save()
        for name, command in (
                ("icarus", ["top_smoke.py", "--preparation"]),
                ("verilator", ["system_matrix.py", "--preparation", "--case", "0"]),
                ("frontend-equivalence", ["codec_equivalence.py", "--preparation"]),
                ("yosys", ["synthesis_probe.py", "--preparation", "--banks", "1"])):
            experiment.run(["python3", "tests/"+command[0], *command[1:]], name,
                           cwd=bundle, timeout=2700)
        experiment.receipt["reproduction"] = {
            "directory": experiment.rel(bundle),
            "inputs": ["rtl/*.sv", "design/*.md", "tests/*"],
            "completed": ["compact Icarus token", "compiled Verilator end-to-end",
                          "independent frontend comparisons", "Yosys zero-latch hierarchy"],
        }
    except (RuntimeError, ValueError, AssertionError, KeyError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
