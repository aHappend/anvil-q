"""Generate full default-geometry numerical outputs, without claiming DUT execution."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint_import import GEOMETRY, Source, file_hash
from retention import Experiment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--packed-directory", type=Path, required=True)
    parser.add_argument("--mode", choices=("awq", "bf16"), required=True)
    parser.add_argument("--cache", choices=("0", "1", "2", "all"), default="all")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    experiment = Experiment(root, args.output, sys.orig_argv, [
        "tests/full_model_reference.cpp", "tests/full_reference_run.py",
        "tests/checkpoint_import.py", "tests/retention.py", "tests/rope_reference.py",
        "data/model/official_inputs.json", "data/model/" + args.mode + "__config.json"])
    if args.repair_of:
        experiment.receipt["repair_of"] = args.repair_of
    source = None
    try:
        packed = args.packed_directory
        if packed.is_absolute() or ".." in packed.parts or any(
                part in (".vulcan", ".git", ".tooling", "VULCAN") for part in packed.parts):
            raise ValueError("packed directory must be a project-relative product experiment")
        source = Source(root, args.mode)
        info = json.loads((root / packed / "import.json").read_text())
        if (info["mode"] != args.mode or info["geometry"] != GEOMETRY or
                any(info["source"][key] != source.info[key]
                    for key in ("repository", "revision", "license_metadata"))):
            raise ValueError("packed image source/geometry identity mismatch")
        bindings = {}
        for filename, field in (("weights.ddr.bin", "image_sha256"),
                                ("descriptors.bin", "descriptors_sha256")):
            path = packed / filename
            digest = file_hash(root / path)
            if digest != info[field]:
                raise ValueError("packed input hash mismatch: " + str(path))
            bindings[str(path)] = digest
        experiment.receipt["input_hashes"] = bindings
        experiment.receipt["official_source"] = info["source"]
        executable = args.output / "full_model_reference"
        experiment.run(["g++", "--version"], "compiler-version")
        experiment.run(["g++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
                        "-ffp-contract=off", "-frounding-math", "-fno-fast-math",
                        str(args.output / "sources/tests/full_model_reference.cpp"),
                        "-o", str(executable)], "compile")
        workload = "11 0 1 0\n29 1 0 0\n101 2 0 1\n"
        (experiment.directory / "tokens.txt").write_text(workload)
        experiment.receipt["workload_sha256"] = hashlib.sha256(workload.encode()).hexdigest()
        results = []
        for cache in range(3) if args.cache == "all" else (int(args.cache),):
            name = f"logits-cache{cache}.bin"
            command = [str(executable), str(packed / "weights.ddr.bin"),
                       str(packed / "descriptors.bin"), "1536", "8960", "12", "2",
                       "128", "128", "28", "151936", "32768", "16",
                       str(int(args.mode == "bf16")), str(cache),
                       str(args.output / "tokens.txt"), str(args.output / name)]
            text = experiment.run(command, f"reference-cache{cache}", timeout=14400)
            data = (experiment.directory / name).read_bytes()
            if (len(data) != 3 * 151936 * 4 or
                    text.count("REFERENCE_LAYER ") != 84 or
                    text.count("REFERENCE_TOKEN ") != 3 or
                    "FULL_REFERENCE_CHECKED tokens=3 vocabulary=151936" not in text):
                raise RuntimeError("incomplete full-model numerical output: cache=" + str(cache))
            results.append({"cache": cache, "tokens": 3, "layers_per_token": 28,
                            "logits_per_token": 151936, "path": str(args.output / name),
                            "sha256": hashlib.sha256(data).hexdigest(),
                            "format": "token-major little-endian signed 32-bit Q16"})
        manifest = {"schema": 1, "scope": "software golden outputs, not RTL or board results",
                    "source": info["source"], "inputs": bindings, "weight_mode": args.mode,
                    "geometry": GEOMETRY, "cache_block": 16,
                    "workload": [[11, 0, 1, 0], [29, 1, 0, 0], [101, 2, 0, 1]],
                    "results": results}
        (experiment.directory / "reference.json").write_text(json.dumps(manifest, indent=2) + "\n")
        experiment.receipt["reference"] = manifest
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1
    finally:
        if source is not None:
            source.close()


if __name__ == "__main__":
    raise SystemExit(main())
