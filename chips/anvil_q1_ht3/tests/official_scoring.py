"""Persistent, source/input-bound FP64 reference continuation, never RTL output."""

import hashlib
import json
import math
from pathlib import Path
import sys
import uuid

import numpy as np

from execution import ROOT, hashes, relative, remaining, timestamp
from official_reference import QwenFP64, scored_position
from retention import artifacts_intact, digest


NAMES = ("native", "represented_image")
DEPENDENCIES = ("tests/official_scoring.py", "tests/official_reference.py",
                "tests/run_compatibility.py", "tests/reference.py")


def save_state(path, models):
    arrays = {}
    for name, model in models.items():
        arrays[name] = np.asarray(model.cache, dtype="<f8")
        expected = (model.c["num_hidden_layers"], model.position, 2,
                    model.c["num_key_value_heads"], 64)
        if arrays[name].shape != expected or not np.isfinite(arrays[name]).all():
            raise AssertionError("FP64 continuation cache shape/value mismatch")
    with path.open("xb") as out:
        np.savez(out, **arrays)


def restore_state(path, models, position):
    with np.load(path, allow_pickle=False) as arrays:
        if set(arrays.files) != set(models):
            raise AssertionError("FP64 continuation model set mismatch")
        for name, model in models.items():
            values = arrays[name]
            expected = (model.c["num_hidden_layers"], position, 2,
                        model.c["num_key_value_heads"], 64)
            if (values.shape != expected or values.dtype != np.dtype("<f8")
                    or not np.isfinite(values).all()):
                raise AssertionError("invalid saved FP64 continuation")
            model.cache = [[(pair[0].copy(), pair[1].copy()) for pair in layer]
                           for layer in values]
            model.position = position


def checked_chain(path, identity, actual):
    chain, seen = [], set()
    while path is not None:
        if path in seen or not path.is_file():
            return None
        seen.add(path)
        row = json.loads(path.read_text())
        required = [row.get("state")]
        required += [c.get("reference") for c in (row.get("comparison") or {}).get(
            "comparisons", {}).values()]
        if (row.get("identity") != identity or row.get("status") != "passed"
                or not all(isinstance(p, str) for p in required)
                or not artifacts_intact(row.get("artifact_sha256", {}), required)):
            return None
        row["binding"] = relative(path)
        chain.append(row)
        predecessor = row.get("predecessor")
        if predecessor is None:
            path = None
        else:
            path = ROOT/predecessor["binding"]
            if not path.is_file() or digest(path) != predecessor["sha256"]:
                return None
    chain.reverse()
    for position, row in enumerate(chain):
        if row.get("position") != position+1:
            return None
        compared = row.get("comparison")
        if (position in identity["scored_positions"]) != (compared is not None):
            return None
        if compared is not None and (compared.get("position") != position or
                compared.get("actual") != actual.get(position)):
            return None
    return chain


def reference_rows(work, stream, bindings, config, checkpoint):
    actual_positions = {int(p): record for p, record in stream["observations"].items()}
    if not actual_positions:
        return [], dict(reused_steps=0, new_steps=0, complete=False, latest=None)
    if sorted(actual_positions) != work["scored_positions"][:len(actual_positions)]:
        raise AssertionError("official reference input is not a complete scored prefix")
    for row in actual_positions.values():
        if not (ROOT/row["path"]).is_file() or digest(ROOT/row["path"]) != row["sha256"]:
            raise AssertionError("official RTL capture changed before reference scoring")
    current = hashes()
    identity = dict(schema=1, source_sha256={p: current[p] for p in DEPENDENCIES},
                    numpy_version=np.__version__, python_version=sys.version,
                    config_sha256=bindings["config.json"]["sha256"],
                    checkpoint_sha256=bindings["model.safetensors"]["sha256"],
                    token_ids=work["token_ids"], scored_positions=work["scored_positions"],
                    stream_identity=stream["identity"])
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
    cache = ROOT/"evidence/compiled"/f"official-reference-{key}"
    cache.mkdir(parents=True, exist_ok=True)
    chain = []
    for path in sorted(cache.glob("step-*/binding.json"),
                       key=lambda p: p.stat().st_mtime, reverse=True):
        checked = checked_chain(path, identity, actual_positions)
        if checked is not None:
            chain = checked
            break
    models = {name: QwenFP64(config, checkpoint, name == "represented_image")
              for name in NAMES}
    if chain:
        restore_state(ROOT/chain[-1]["state"], models, chain[-1]["position"])
    reused = len(chain)
    for position in range(reused, max(actual_positions)+1):
        if remaining() < 90:
            break
        start = timestamp()
        scored = position in actual_positions
        references = {name: model.step(work["token_ids"][position], emit_logits=scored)
                      for name, model in models.items()}
        directory = cache/f"step-{uuid.uuid4().hex[:12]}"
        directory.mkdir()
        artifacts, comparison = [], None
        if scored:
            captured = actual_positions[position]
            actual = np.fromfile(ROOT/captured["path"], dtype="<f4").astype(np.float64)
            if actual.shape != (151936,) or not np.isfinite(actual).all():
                raise AssertionError("official scored vector is not finite full vocabulary")
            target = work["token_ids"][position+1]
            comparisons = {}
            for name, reference in references.items():
                path = directory/f"{name}.f64"
                with path.open("xb") as out:
                    reference.astype("<f8").tofile(out)
                artifacts.append(path)
                try:
                    metric = scored_position(actual.tolist(), reference.tolist(), target)
                    comparisons[name] = dict(status="passed", **metric)
                except AssertionError as exc:
                    comparisons[name] = dict(status="failed", error=str(exc),
                                             required_cosine=0.9999)
                comparisons[name].update(reference=relative(path), reference_sha256=digest(path))
            maximum = float(actual.max())
            nll = maximum+math.log(math.fsum(math.exp(float(x)-maximum)
                                            for x in actual))-float(actual[target])
            comparison = dict(position=position, shifted_target=target, actual=captured,
                              comparisons=comparisons, nll=nll, greedy_token=int(actual.argmax()))
        state = directory/"state.npz"
        save_state(state, models)
        artifacts.append(state)
        row = dict(status="passed", scope="completed FP64 step, not numerical acceptance",
                   identity=identity, start=start, end=timestamp(), position=position+1,
                   state=relative(state), comparison=comparison,
                   predecessor=(dict(binding=chain[-1]["binding"],
                                     sha256=digest(ROOT/chain[-1]["binding"])) if chain else None),
                   artifact_sha256={relative(p): digest(p) for p in artifacts})
        path = directory/"binding.json"
        with path.open("x") as out:
            json.dump(row, out, indent=2)
        row["binding"] = relative(path)
        chain.append(row)
        print(f"REFERENCE_PROGRESS task={work['task']} id={work['id']} "
              f"position={position} scored={int(scored)}", flush=True)
    return ([row["comparison"] for row in chain if row["comparison"] is not None],
            dict(reused_steps=reused, new_steps=len(chain)-reused,
                 complete=len(chain) == max(actual_positions)+1,
                 latest=chain[-1]["binding"] if chain else None))
