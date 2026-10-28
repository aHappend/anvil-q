"""A public-source-only copy executes the unchanged oracle in a fresh directory."""

from dataclasses import replace
import json
import shutil

from execution import ROOT, sha256, sources, write_json
from parameters import A, legal


def reproduce(run, bounded_smoke=False):
    destination = run.path / "clean-project"
    destination.mkdir()
    copied = {}
    for source in sources():
        relative = source.relative_to(ROOT)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha256(target) != sha256(source):
            raise AssertionError("copy changed " + str(relative))
        copied[str(relative)] = sha256(target)
    if any(p.name in (".vulcan", ".git", ".tooling", "VULCAN") for p in destination.rglob("*")):
        raise AssertionError("runtime/private metadata in clean copy")
    cases = [replace(A, BANKS=8, CACHE_MODE=mode, INT4_ASYM=asym)
             for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1))]
    if not all(legal(g) and g.NUM_KV_HEADS * g.HEAD_DIM == 2 for g in cases):
        raise AssertionError("unchanged A partial-group geometry not accepted")
    write_json(run.path / "copy-manifest.json", copied)
    _, receipt = run.tool(["python3", "tests/reproduce_worker.py",
                          "--output", "evidence/reproduction",
                          *(["--bounded-smoke"] if bounded_smoke else [])],
                         cwd=destination, timeout=43200)
    receipts = list((destination / "evidence/reproduction").glob("*/receipt.json"))
    if len(receipts) != 1:
        raise AssertionError("expected exactly one clean-directory invocation")
    result = json.loads(receipts[0].read_text())
    if result["status"] != "passed" or result["source_hashes"] != copied:
        raise AssertionError("clean reproduction failure or input binding mismatch")
    return {"copy_manifest": run.rel(run.path / "copy-manifest.json"),
            "scope": "bounded clean-copy diagnostic only" if bounded_smoke else "admitted clean reproduction",
            "receipt": run.rel(receipts[0]), "stdout": receipt["stdout"], "result": result["result"]}
