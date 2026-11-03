"""Check the portable logical bridge mapping against actual public RTL ports."""

import argparse
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retention import Experiment


def inspect(root):
    mapping = json.loads((root / "tests/hardware_bridge.json").read_text())
    text = (root / "rtl/anvil_q2_ht_top.sv").read_text()
    header = text.split(") (", 1)[1].split("\n);", 1)[0]
    ports = {"inputs": {}, "outputs": {}}
    for declaration in re.finditer(r"\b(input|output)\s+wire\s+([^;]*?)(?=\b(?:input|output)\b|$)",
                                   header):
        direction, names = declaration.groups()
        names = re.sub(r"\bsigned\b", "", names).strip().rstrip(",").strip()
        size = re.match(r"\[(\d+):(\d+)\]", names)
        width = abs(int(size[1]) - int(size[2])) + 1 if size else 1
        if size:
            names = names[size.end():]
        for name in names.split(","):
            name = name.strip()
            if not re.fullmatch(r"[a-z_][a-z_0-9]*", name):
                raise RuntimeError("unparsed public port declaration: " + name)
            ports[direction + "s"][name] = width
    if any(mapping[key] != value for key, value in ports.items()):
        raise RuntimeError("logical bridge pin names/widths/directions mismatch")
    all_ports = set(ports["inputs"]) | set(ports["outputs"])
    for transaction in mapping["transactions"].values():
        for key in ("request", "response", "commands", "responses"):
            if key in transaction and not set(transaction[key]) <= all_ports:
                raise RuntimeError("bridge transaction refers to an unknown port")
    if (mapping["top"] != "anvil_q2_ht_top" or mapping["device"] != "10AX115N2F45E1SG" or
            mapping["clock_period_ns"] != 10.0 or mapping["pcie"]["generation"] != 3 or
            mapping["pcie"]["lanes"] != 8 or
            mapping["transactions"]["avalon"]["capacity_bytes"] != 1 << 33 or
            mapping["registers"]["default_descriptor_count"] != 16 + 16 * 28):
        raise RuntimeError("bridge target/default geometry mismatch")
    return {"input_pins": len(ports["inputs"]), "output_pins": len(ports["outputs"]),
            "transactions": len(mapping["transactions"]),
            "scope": "logical mapping consistency only; native transport and board execution remain required"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    experiment = Experiment(root, args.output, sys.orig_argv, [
        "rtl/anvil_q2_ht_top.sv", "tests/hardware_bridge.json",
        "tests/bridge_mapping_check.py", "tests/retention.py"])
    try:
        experiment.run(["python3", "--version"], "python-version")
        experiment.receipt["mapping"] = inspect(experiment.directory / "sources")
        experiment.finish(0)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, IndexError) as error:
        experiment.finish(1, error)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
