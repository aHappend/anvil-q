"""Source-bound adapters for pinned public native RTL, never numerical oracles.

Q1 exposes one untagged, noncancelable memory port. The shared pin transactor
connects it directly, using a constant scoreboard tag only; it does not change
data, timing, reset, arithmetic or completion. Q2 executes the supplied RTL only
after every source filename/hash matches its public descriptor.
"""

import json
from pathlib import Path
import shutil
from urllib.parse import urlsplit

from execution import ROOT, sha256, write_json


def source_map(asset):
    names = [Path(urlsplit(item["url"]).path).name for item in asset["contents"]]
    if len(names) != len(set(names)) or any(not n.endswith(".sv") for n in names):
        raise ValueError("native baseline needs unique SystemVerilog source names")
    return dict(zip(names, (item["sha256"] for item in asset["contents"])))


def supported_q1(asset):
    if (asset["category"] != "baseline" or asset["generation"] != "Q1" or
            asset.get("identifier") != "aHappend/anvil-q/anvil-q1"):
        return False
    declared = next(a for a in json.loads((ROOT / "tests/public_assets.json").read_text())["assets"]
                    if a["category"] == "baseline" and a["generation"] == "Q1")
    expected = {Path(urlsplit(item["url"]).path).name: item["sha256"]
                for item in declared["files"]}
    return (asset["revision"] == declared["revision"] and
            asset["license_identifier"] == declared["license_identifier"] and
            asset["license_evidence"]["sha256"] == declared["license_file"]["sha256"] and
            source_map(asset) == expected)


def native_q1_sources(run, asset):
    if not supported_q1(asset):
        raise ValueError("no source-bound Q1 adapter for this public baseline")
    folder = run.path / "native-q1"
    folder.mkdir(exist_ok=True)
    entries = [*asset["contents"], asset["license_evidence"]]
    for entry in entries:
        source = ROOT / entry["retained_path"]
        if source.stat().st_size != entry["size_bytes"] or sha256(source) != entry["sha256"]:
            raise AssertionError("native Q1 acquired content changed before execution")
        destination = folder / Path(urlsplit(entry["url"]).path).name
        if destination.exists():
            if destination.read_bytes() != source.read_bytes():
                raise AssertionError("native Q1 source destination already differs")
        else:
            shutil.copyfile(source, destination)
    sources = [run.rel(folder / name) for name in sorted(source_map(asset))]
    binding = {"identifier": asset["identifier"], "revision": asset["revision"],
               "license": asset["license_evidence"], "acquired": asset["contents"],
               "compiled_source_hashes": {name: sha256(ROOT / name) for name in sources}}
    write_json(folder / "source-binding.json", binding)
    return sources, binding
