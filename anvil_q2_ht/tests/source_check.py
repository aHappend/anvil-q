"""Production source safety checks; not a substitute for native timing/STA."""

import argparse
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import Experiment


def without_comments(text):
    return re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"',
                  lambda match: "".join("\n" if char == "\n" else " " for char in match[0]),
                  text)


def inspect(path, name):
    text = without_comments(path.read_text())
    if re.search(r"\b(?:real|shortreal|realtime)\b|\$(?:itor|rtoi|bitstoshortreal|shortrealtobits)\b",
                 text):
        raise RuntimeError("unsynthesizable floating arithmetic in " + name)
    declarations = list(re.finditer(r"\b(?:localparam|parameter)\b[^;]*;", text))
    constant_operators = []
    for match in re.finditer(r"/|%", text):
        if not any(declaration.start() <= match.start() < declaration.end()
                   for declaration in declarations):
            raise RuntimeError(f"division/remainder outside elaboration declaration: "
                               f"{name}:{text.count(chr(10), 0, match.start()) + 1}")
        constant_operators.append(text.count("\n", 0, match.start()) + 1)
    tokens = list(re.finditer(
        r"[A-Za-z_$][A-Za-z0-9_$]*|<=|>=|==|!=|===|!==|\+\+|--|[^\s]", text))
    values = [token[0] for token in tokens]
    processes = []
    cursor = 0
    while cursor < len(tokens):
        if values[cursor] != "always":
            cursor += 1
            continue
        start = cursor
        cursor += 1
        if values[cursor:cursor + 2] != ["@", "("]:
            continue
        cursor += 2
        sensitivity_start = cursor
        depth = 1
        while depth:
            depth += (values[cursor] == "(") - (values[cursor] == ")")
            cursor += 1
        sensitivity = values[sensitivity_start:cursor - 1]
        if "posedge" not in sensitivity and "negedge" not in sensitivity:
            continue
        if values[cursor] != "begin":
            raise RuntimeError("unsupported sequential process syntax in " + name)
        body_start = cursor
        depth = 1
        cursor += 1
        while depth:
            depth += (values[cursor] == "begin") - (values[cursor] == "end")
            cursor += 1
        body = values[body_start:cursor]
        blocking = []
        nonblocking = 0
        position = 0
        while position < len(body):
            if body[position] == "for":
                position += 1
                if body[position] != "(":
                    raise RuntimeError("unsupported loop-control syntax in " + name)
                level = 1
                position += 1
                while level:
                    level += (body[position] == "(") - (body[position] == ")")
                    position += 1
                continue
            if body[position] == "=":
                blocking.append(position)
            if body[position] == "<=":
                nonblocking += 1
            position += 1
        line = text.count("\n", 0, tokens[start].start()) + 1
        if blocking:
            raise RuntimeError(f"blocking datapath assignment in sequential process: {name}:{line}")
        if not nonblocking:
            raise RuntimeError(f"unrecognized sequential process without registered state: {name}:{line}")
        processes.append({"line": line, "nonblocking_tokens": nonblocking,
                          "asynchronous_active_low_reset": sensitivity ==
                          ["posedge", "clk", "or", "negedge", "rst_n"]})
    return {"source": name, "sequential_processes": processes,
            "elaboration_division_remainder_lines": constant_operators}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    rtl = sorted(str(path.relative_to(root)) for path in (root / "rtl").glob("*.sv"))
    names = rtl + ["tests/source_check.py", "tests/retention.py"]
    experiment = Experiment(root, args.output, sys.orig_argv, names)
    try:
        experiment.run(["python3", "--version"], "python3-version")
        results = [inspect(experiment.directory / "sources" / name, name) for name in rtl]
        report = {"sources": results,
                  "scope": "lexical production-source constraints, not timing closure",
                  "limitations": [
                      "Loop-control assignments are elaboration/iteration controls, not datapath state.",
                      "Synchronous RAM processes intentionally omit reset; validity is tested behaviorally.",
                      "No bounded-depth/100MHz claim follows from lexical checks.",
                      "Native timing lint, actual device mapping and post-fit STA remain mandatory."]}
        (experiment.directory / "source-check.json").write_text(json.dumps(report, indent=2) + "\n")
        experiment.receipt["source_checks"] = report
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, IndexError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
