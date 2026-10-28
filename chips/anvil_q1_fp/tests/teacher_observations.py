#!/usr/bin/env python3
"""Compare documented observations with saved independent teacher references.

This offline preparation helper has no transport or device access. Qualification
uses explicitly synthetic observations, not RTL or physical execution.
"""

import argparse
import copy
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark import (FORBIDDEN, MODES, Validator, artifact_path, load_json,
                       ordered_indices, require, sha)
from verify import Evidence, ROOT


def descriptor(path):
    name = str(path.relative_to(ROOT))
    return {"path": name, "sha256": sha(artifact_path(ROOT, name))}


class TeacherObservations:
    def __init__(self, validator, reference):
        self.validator = validator
        self.reference = validator.document(reference)
        require(self.reference["schema"] == 1 and
                self.reference["purpose"] == "complete-collected-teacher-reference-preparation" and
                self.reference["arithmetic"] == "ieee-fp64" and
                self.reference["independent_of_rtl"] is True,
                "not an independent collected teacher reference")
        for name in ("model_manifest", "benchmark_manifest"):
            current = ROOT / "tests/data" / (name + ".json")
            require(self.reference[name] == descriptor(current),
                    "saved teacher reference manifest differs: " + name)
        require(self.reference["reference_sources"], "missing independent reference sources")
        for name, hashed in self.reference["reference_sources"].items():
            validator.artifact({"path": name, "sha256": hashed})
        validator.artifact(self.reference["collector_source"])
        self.cases = {}
        for case in self.reference["cases"]:
            require(case["case"] not in self.cases, "duplicate saved teacher case")
            require(set(case["modes"]) == {"checkpoint", *MODES},
                    "missing saved teacher precision")
            self.cases[case["case"]] = case
        require(len(self.cases) == 50, "incomplete saved teacher suite")

    def positions(self, key, mode, teacher_hash):
        require(mode in MODES and key in self.cases, "unknown observation case/mode")
        case = self.cases[key]
        require(case["teacher_tokens"]["sha256"] == teacher_hash,
                "observation uses another teacher context")
        tokens = self.validator.document(case["teacher_tokens"])
        document = self.validator.document(case["modes"][mode]["positions"])
        require(document["schema"] == 1 and
                document["purpose"] == "collected-fp64-teacher-reference" and
                document["dtype"] == "<f8", "invalid saved teacher layout")
        positions = document["positions"]
        require(ordered_indices(positions, "position", len(tokens)),
                "saved teacher positions incomplete or unordered")
        return positions

    def position(self, actual, expected, mode, label):
        require(type(actual["position"]) is int and type(expected["position"]) is int and
                actual["position"] == expected["position"], "observation position differs")
        require(ordered_indices(actual["layers"], "layer", 24) and
                ordered_indices(expected["layers"], "layer", 24),
                "observation or saved reference layers incomplete")
        threshold = (-1, float("inf")) if mode == "w4a16" else (.999, .01)
        self.validator.arrays(actual["logits"], expected["fp64_logits"],
                              actual["repeat_logits"], 151936, threshold, label)
        threshold = (-1, float("inf")) if mode == "w4a16" else (.9999, .002)
        for observed, reference in zip(actual["layers"], expected["layers"]):
            self.validator.arrays(observed["output"], reference["fp64_output"],
                                  observed["repeat_output"], 896, threshold,
                                  label + "/layer" + str(reference["layer"]))

    def complete(self, results):
        seen = set()
        for record in results["cases"]:
            key, mode = record["case"], record["mode"]
            require((key, mode) not in seen, "duplicate observation case/mode")
            expected = self.positions(key, mode, record["teacher_tokens_sha256"])
            require(len(record["positions"]) == len(expected),
                    "observation teacher position count differs")
            for actual, reference in zip(record["positions"], expected):
                self.position(actual, reference, mode,
                              f"{key}/{mode}/{reference['position']}")
            seen.add((key, mode))
        require(seen == {(key, mode) for key in self.cases for mode in MODES},
                "observation suite incomplete")
        return len(seen)


def qualify(ev, observer):
    """Exercise real saved array ordering/bounds with synthetic FP32 fixtures."""
    key = sorted(observer.cases)[0]
    case = observer.cases[key]
    good = True
    for mode in MODES:
        expected = observer.positions(key, mode, case["teacher_tokens"]["sha256"])[0]
        directory = ev.path / mode
        directory.mkdir()

        def rounded(reference, name):
            raw = observer.validator.artifact(reference).read_bytes()
            values = struct.unpack("<" + "d" * (len(raw) // 8), raw)
            data = struct.pack("<" + "f" * len(values), *values)
            outputs = []
            for suffix in ("original", "repeat"):
                path = directory / (name + "-" + suffix + ".f32")
                with path.open("xb") as stream:
                    stream.write(data)
                outputs.append(descriptor(path))
            return outputs

        logits, repeat = rounded(expected["fp64_logits"], "logits")
        actual = {"position": expected["position"], "logits": logits,
                  "repeat_logits": repeat, "layers": []}
        for layer in expected["layers"]:
            output, repeated = rounded(layer["fp64_output"], "layer-" + str(layer["layer"]))
            actual["layers"].append({"layer": layer["layer"], "output": output,
                                     "repeat_output": repeated})
        observer.position(actual, expected, mode, key + "/" + mode + "/synthetic")
        good = ev.assertion("rounded_saved_reference_" + mode, True,
                            vectors_compared=25, synthetic_observations=True) and good
        broken = directory / "corrupt-logits.f32"
        with broken.open("xb") as stream:
            stream.write(struct.pack("<f", float("nan")) * 151936)
        defects = [
            ("nonfinite", {"logits": descriptor(broken), "repeat_logits": descriptor(broken)},
             "nonfinite numerical array"),
            ("repeat", {"repeat_logits": descriptor(broken)}, "nondeterministic output"),
            ("position", {"position": expected["position"] + 1}, "observation position"),
            ("layers", {"layers": actual["layers"][:-1]}, "layers incomplete"),
        ]
        if mode != "w4a16":
            inverted = directory / "inverted-logits.f32"
            values = struct.unpack("<151936f", (ROOT / logits["path"]).read_bytes())
            with inverted.open("xb") as stream:
                stream.write(struct.pack("<151936f", *(-value for value in values)))
            defects.append(("finite-numerical",
                            {"logits": descriptor(inverted),
                             "repeat_logits": descriptor(inverted)},
                            "numerical fidelity failed"))
        with (directory / "synthetic-pristine.json").open("x") as stream:
            json.dump(actual, stream, indent=2, allow_nan=False)
        for label, change, diagnostic in defects:
            mutant = copy.deepcopy(actual)
            mutant.update(change)
            with (directory / ("synthetic-" + label + ".json")).open("x") as stream:
                json.dump(mutant, stream, indent=2, allow_nan=False)
            try:
                observer.position(mutant, expected, mode, label)
            except ValueError as error:
                rejected = diagnostic in str(error)
                message = str(error)
            else:
                rejected, message = False, "incorrectly accepted"
            good = ev.assertion("reject_" + mode + "_" + label, rejected,
                                diagnostic=message, synthetic_observations=True) and good
    ev.receipt["scope"] = (
        "Three modes, first saved teacher position of one case, 75 complete vectors. "
        "Rounded FP64 synthetic observations and disposable corruptions only; no DUT, "
        "transport qualification, full-model benchmark, timing or physical result.")
    return good


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--references", type=Path, required=True)
    parser.add_argument("--qualify", action="store_true")
    args = parser.parse_args()
    ev = Evidence("teacher-observations-qualification" if args.qualify else "teacher-observations")
    ok = False
    try:
        require(not args.references.is_absolute() and ".." not in args.references.parts and
                not FORBIDDEN.intersection(args.references.parts) and
                (ROOT / args.references).resolve().is_relative_to(ROOT),
                "reference index must be project relative")
        validator = Validator(ROOT, ev)
        observer = TeacherObservations(validator, descriptor(ROOT / args.references))
        if args.qualify:
            ok = qualify(ev, observer)
        else:
            # The offline comparison never substitutes for the admitted validator.
            validator.validate()
            cases = observer.complete(load_json(ROOT / "tests/data/full_model_results.json"))
            ok = ev.assertion("saved_independent_teacher_comparisons", cases == 150, cases=cases)
        path = ev.path / "comparison-metrics.json"
        with path.open("x") as stream:
            json.dump(validator.metrics, stream, indent=2, allow_nan=False)
        ev.receipt["comparison_metrics"] = descriptor(path)
    except (ValueError, KeyError, TypeError, OSError, OverflowError, struct.error) as error:
        ok = False
        ev.assertion("teacher_observation_exception", False, error=repr(error))
    finally:
        ev.finish("passed" if ok else "failed")
    print(json.dumps({"status": ev.receipt["status"],
                      "receipt": str((ev.path / "receipt.json").relative_to(ROOT))}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
