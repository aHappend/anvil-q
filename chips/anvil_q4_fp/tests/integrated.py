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


class GreedyFixture(Fixture):
    def __init__(self, words, weights):
        self.greedy_weights = weights
        super().__init__(words, tokens=[0, None, None], constant_profile=True)

    def build_image(self):
        super().build_image()
        for row, weight in enumerate(self.greedy_weights):
            self.lm_head[row] = [weight] + [0] * (self.words[8] - 1)
            for col, value in enumerate(self.lm_head[row]):
                self.initial[0, 0, 1, row, col] = value
        self.constant_profile = False


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
    words = descriptor(banks=1, dimension=2, intermediate=3,
                       vocabulary=5, context=5, page_tokens=1)
    words[20] = 10
    fixture = Fixture(words, tokens=[2, None, None, None])
    replacement = Fixture(words, tokens=[3, None, None], epoch=2, pages=[4, 3, 2, 1, 0])
    fixture.initial.update({key: value for key, value in replacement.initial.items() if key[0]==15})
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
    r = replacement.steps
    scenarios["new-sequence-replacement"] = [
        initial, command(r[0], draft=True, fresh=True, token1=r[1]["token"],
                         accepted=2, targets=2, expectations=r[:2]), command(r[2])]
    scenarios["new-sequence-rollback"] = [
        initial, command(r[0], draft=True, fresh=True, token1=r[1]["token"],
                         accepted=2, targets=2, action=5, expectations=r[:2]), command(s[1])]
    for label, edits in (("bad-token", {"token": 5}),
                         ("skipped-position", {"position": 2}),
                         ("repeated-position", {"position": 0})):
        scenarios[label] = [
            initial, command({**s[1], **edits}, error=True, targets=0,
                             expectations=[{"writes": []}]), command(s[1])]
    scenarios["bad-new-sequence-position"] = [
        initial, command(s[1], fresh=True, error=True, targets=0,
                         expectations=[{"writes": []}]), command(s[1])]
    scenario_images = {}
    collision = Fixture(words, tokens=[2, None, None])
    collision.initial.update({key: value for key, value in replacement.initial.items()
                              if key[0]==15})
    collision.initial[15, 2, 0, 0, 0] = 0x80000009
    collision_dir = directory / "checkpoint-images/protected-collision"
    collision_dir.mkdir()
    scenario_images["protected-page-collision"] = collision.export(collision_dir)
    scenarios["protected-page-collision"] = [
        initial, command(r[0], draft=True, fresh=True, token1=r[1]["token"],
                         error=True, targets=1), command(s[1])]
    minimum = Fixture(descriptor(banks=1, dimension=2, intermediate=1,
                                 vocabulary=1, context=1, page_tokens=1, bias=0), tokens=1)
    minimum_dir = directory / "checkpoint-images/capacity-one"
    minimum_dir.mkdir()
    scenario_images["capacity-one-rejection"] = minimum.export(minimum_dir)
    scenarios["capacity-one-rejection"] = [
        command(minimum.steps[0], draft=True, error=True, targets=0,
                expectations=[{"writes": []}]), command(minimum.steps[0], fresh=True)]
    for label, weights, expected_index in (
            ("greedy-all-nan", [0x7fc0] * 5, 0),
            ("greedy-leading-nan-negative-tie", [0x7fc0, 0xbf80, 0xff80, 0xbf80, 0x7fc0], 1),
            ("greedy-infinity-tie", [0x7fc0, 0x7f80, 0x3f80, 0x7f80, 0xff80], 1),
            ("greedy-zero-tie", [0, 0x8000, 0, 0x8000, 0], 0),
            ("greedy-finite-tie", [0xbf80, 0x3f80, 0x3f80, 0, 0x7fc0], 1)):
        directed = GreedyFixture(words, weights)
        if directed.tokens[1:] != [expected_index, expected_index]:
            raise AssertionError(f"Directed greedy reference does not discriminate: {label}")
        case = directory / "checkpoint-images" / label
        case.mkdir()
        scenario_images[label] = directed.export(case)
        steps = directed.steps
        scenarios[label] = [
            command(steps[0], fresh=True),
            command(steps[1], draft=True, token1=steps[2]["token"], accepted=2,
                    targets=2, expectations=steps[1:3])]
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
                relative(obj / "Vanvil_q4_fp_top"), relative(scenario_images.get(label, image)),
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
