"""Public-pin integrated speculation, fault, drain and rollback comparisons."""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import ROOT, execute, new_run, relative, source_hashes
from native_model import Fixture, descriptor


def command(step, *, draft=False, token1=0, accepted=0, error=False,
            action=0, targets=1, fresh=False, expectations=None):
    return {"draft": draft, "token0": step["token"], "token1": token1,
            "position": step["position"], "fresh": fresh,
            "accepted": accepted, "error": error, "action": action,
            "targets": targets,
            "writes": [item for record in (expectations or [step])
                       for item in record["writes"]],
            "logits": [] if draft or error else step["logits"]}


def write_script(path, commands):
    with path.open("w") as stream:
        stream.write(f"{len(commands)}\n")
        for cmd in commands:
            stream.write(" ".join(str(int(cmd[field])) for field in (
                "draft", "token0", "token1", "position", "fresh", "accepted",
                "error", "action", "targets")) + "\n")
            stream.write(f"{len(cmd['writes'])}\n")
            for key, value in cmd["writes"]:
                stream.write(" ".join(f"{word:x}" for word in (*key, value)) + "\n")
            stream.write(f"{len(cmd['logits'])}\n")
            stream.writelines(f"{word:x}\n" for word in cmd["logits"])


def run(preparation=False, repair_of=None):
    directory = new_run("integrated-control", preparation)
    fixture = Fixture(descriptor(banks=1, dimension=2, intermediate=3,
                                 vocabulary=5, context=5, page_tokens=1),
                      tokens=[2, None, None, None])
    image = fixture.export(directory)
    s = fixture.steps
    initial = command(s[0], fresh=True)
    scenarios = {}
    scenarios["accepted-zero"] = [
        initial, command({**s[1], "token": (s[1]["token"]+1) % 5},
                         draft=True, token1=s[2]["token"], targets=0,
                         expectations=[{"writes": []}]), command(s[1]), command(s[2])]
    scenarios["accepted-one"] = [
        initial, command(s[1], draft=True, token1=(s[2]["token"]+1) % 5, accepted=1),
        command(s[2]), command(s[3])]
    scenarios["accepted-two"] = [
        initial, command(s[1], draft=True, token1=s[2]["token"], accepted=2,
                         targets=2, expectations=s[1:3]), command(s[3])]
    for action, label in ((1, "target-zero-fault"), (2, "target-one-fault"),
                          (3, "target-zero-cancel"), (4, "target-one-cancel"),
                          (5, "retirement-cancel")):
        scenarios[label] = [
            initial, command(s[1], draft=True, token1=s[2]["token"],
                             accepted=2 if action==5 else 0, error=action<3,
                             action=action, targets=1 if action in (1, 3) else 2,
                             expectations=s[1:3]), command(s[1]), command(s[2])]
    obj = directory / "compile-obj"
    records = []
    try:
        execute(directory / "compile", [
            "verilator", "--cc", "--exe", "--build", "-Wno-fatal", "-j", "2",
            "--top-module", "anvil_q4_fp_top", "--Mdir", relative(obj),
            "-GBANKS=1", "-GQUEUE_DEPTH=3", "-GTILE_ROWS=3", "-GTILE_K=3",
            "-CFLAGS", "-std=c++17 -DBANKS=1", "-MAKEFLAGS", "OPT_FAST=-O3",
            *[relative(path) for path in sorted((ROOT / "rtl").glob("*.sv"))],
            os.path.relpath(ROOT / "tests/integrated_sim.cpp", obj)], timeout=1800)
        for label, commands in scenarios.items():
            script, observed = directory / f"{label}.txt", directory / f"{label}.json"
            write_script(script, commands)
            execute(directory / label, [
                relative(obj / "Vanvil_q4_fp_top"), relative(image),
                relative(script), relative(observed)], timeout=600, repair_of=repair_of)
            records.append({"case": label, "observed": json.loads(observed.read_text()),
                            "receipt": relative(directory / label / "receipt.json")})
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    (directory / "observed.json").write_text(json.dumps({
        "source_sha256": source_hashes(), "synthetic": True,
        "cases": records}, indent=2) + "\n")
    print(f"Integrated control receipts: {relative(directory)}", flush=True)
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run(args.preparation, args.repair_of)
