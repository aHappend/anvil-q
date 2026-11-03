"""Synthetic reclamation/allocation/retry checks, not hardware acceptance."""

import argparse
import ast
import copy
from contextlib import redirect_stdout
import errno
import io
import json
import math
import os
from pathlib import Path
import sys
import time
import uuid
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import (ROOT, ExecutionFailure, failure_details, hashes, relative,
                       remaining, timestamp)
from retention import artifacts_intact, digest, execution_logs_intact, validated_execution
from run_mutations import trial
from run_compatibility import resumable_case
from run_synthesis import semantic_sources
from official_reference import QwenFP64
from official_scoring import likelihood, restore_state, save_state
from verify import MINIMUM_ALLOCATIONS, child, dependencies, reconcile_coverage, schedule
from run_integrated_geometry import CROSS_CASES
from run_parameters import legal_cross
import numpy as np


def run(output):
    assertions = 0
    cross_directory = output/f"synthetic-cross-coverage-{uuid.uuid4().hex[:12]}"
    cross_directory.mkdir()
    cross_label = ("functional TILE_BEATS/KV_WINDOW/FLASH_TILE cross matrix; "
                   "the legal boundary cross received source elaboration only")
    current_sources = hashes()
    geometry_rows = []
    for name, geometry in CROSS_CASES.items():
        positions = [*range(geometry["S"] if geometry["KW"] == 128
                            else min(geometry["S"], 4)), 0]
        for fmt, seed in ((0, 17), (1, 89)):
            geometry_rows.append(dict(
                synthetic=True, status="passed", id=name, geometry=geometry,
                format=fmt, seed=seed, compared_positions=positions,
                metrics=[dict(cosine=1.0) for _ in positions],
                measurements=[dict(synthetic=True) for _ in positions],
                simulation_receipt="synthetic-only; no RTL execution"))

    def cross_reconciliation(cases):
        parameters = dict(status="passed", synthetic=True, runs=[
            dict(id=name, parameters=p, status="passed") for name, p, _ in legal_cross()])
        geometries = dict(status="passed", synthetic=True, runs=cases)
        rows = []
        for name, value in (("parameters", parameters), ("integrated_geometry", geometries)):
            script = f"tests/run_{name}.py"
            result_path = cross_directory/f"{name}-result.json"
            receipt_path = cross_directory/f"{name}-receipt.json"
            result_path.write_text(json.dumps(value))
            receipt_path.write_text(json.dumps(dict(
                synthetic=True, exit=0, timed_out=False,
                source_sha256={p: current_sources[p] for p in dependencies(script)})))
            rows.append(dict(id=name, status="incomplete" if name == "parameters" else "passed",
                             coverage_limits=[cross_label] if name == "parameters" else [],
                             result=relative(result_path), receipt=relative(receipt_path)))
        reconcile_coverage(rows)
        return rows[0]

    reconciled = cross_reconciliation(geometry_rows)
    if (reconciled["coverage_limits"] or reconciled["status"] != "passed"
            or not reconciled["functional_parameter_coverage"].get("pairwise_cross_complete")):
        raise AssertionError("complete synthetic pairwise observations did not reconcile")
    assertions += 1
    for defect in ("missing_tuple", "duplicate_tuple", "missing_comparison",
                   "wrong_position", "short_context", "wrong_geometry", "wrong_seed"):
        cases = copy.deepcopy(geometry_rows)
        index = next(i for i, row in enumerate(cases) if row["geometry"]["KW"] == 128)
        if defect == "missing_tuple":
            del cases[index]
        elif defect == "duplicate_tuple":
            cases.append(copy.deepcopy(cases[index]))
        elif defect == "missing_comparison":
            cases[index]["metrics"].pop()
        elif defect == "wrong_position":
            cases[index]["compared_positions"][-2] -= 1
        elif defect == "short_context":
            for key in ("metrics", "measurements", "compared_positions"):
                cases[index][key] = cases[index][key][:4]
        elif defect == "wrong_geometry":
            cases[index]["geometry"]["KW"] = 3
        else:
            cases[index]["seed"] = 2026
        rejected = cross_reconciliation(cases)
        if rejected["coverage_limits"] != [cross_label] or rejected["status"] != "incomplete":
            raise AssertionError(f"synthetic coverage defect closed the parameter cross: {defect}")
        assertions += 1
    filename = "anvil_q1_ht3_decoder.sv"
    old = f"evidence/preparation/synthetic-old-abc/shard-123/frontend-sources/{filename}"
    new = f"evidence/preparation/synthetic-new-def/shard-456/frontend-sources/{filename}"
    command = f"select module/c:$shiftx${old}:0$42; techmap; "
    expected = f"select module/c:$shiftx$<source>/{filename}:0$42; techmap; "
    for path in (old, new):
        frontend = dict(transformations=[dict(output=path)])
        if semantic_sources(command, frontend) != expected:
            raise AssertionError("reused RTLIL source locations changed synthesis cache identity")
        if semantic_sources(command.replace(filename, "different.sv"), frontend) == expected:
            raise AssertionError("synthesis normalization erased a different source selection")
        assertions += 2
    names = ("netlist.json", "synthesis.stdout.txt", "synthesis.stderr.txt",
             "executable", "driver.cpp")
    artifacts = {}
    for name in names:
        path = output / name
        path.write_text(f"synthetic {name}\n")
        artifacts[relative(path)] = digest(path)
    record = dict(stdout=relative(output/names[1]), stderr=relative(output/names[2]),
                  artifact_sha256=artifacts)
    if not artifacts_intact(artifacts) or not execution_logs_intact(record):
        raise AssertionError("complete synthetic artifacts rejected")
    assertions += 1
    for name in names:
        path = output/name
        original = path.read_bytes()
        # Synthetic candidates only; never remove retained execution evidence.
        path.unlink()
        if artifacts_intact(artifacts):
            raise AssertionError(f"reclaimed {name} accepted")
        if "stderr" in name or "stdout" in name:
            if execution_logs_intact(record):
                raise AssertionError("reclaimed raw log accepted")
        path.write_bytes(original)
        assertions += 1
    omitted = {p: sha for p, sha in artifacts.items() if not p.endswith("driver.cpp")}
    if artifacts_intact(omitted, artifacts):
        raise AssertionError("omitted required driver accepted")
    assertions += 1
    old_build = output/f"synthetic-old-build-{uuid.uuid4().hex[:12]}"
    new_build = output/f"synthetic-new-build-{uuid.uuid4().hex[:12]}"
    for build in (old_build, new_build):
        (build/"compile-obj").mkdir(parents=True)
    binary = new_build/"compile-obj/Vinference_tb"
    binary.write_bytes(b"synthetic executable bytes; never executed")
    old_binary = old_build/"compile-obj/Vinference_tb"
    sources = {"tests/inference_tb.sv": hashes()["tests/inference_tb.sv"]}
    identity = dict(source_sha256=sources, tool_version="synthetic tool version")

    def synthetic_receipt(directory, stem, argv):
        stdout, stderr = directory/f"{stem}.stdout.txt", directory/f"{stem}.stderr.txt"
        stdout.write_text("synthetic observation; not tool execution")
        stderr.write_text("")
        record = dict(synthetic=True, argv=argv, exit=0, timed_out=False,
                      source_sha256=sources, tool_version_exit=0,
                      tool_version=identity["tool_version"],
                      stdout=relative(stdout), stderr=relative(stderr),
                      artifact_sha256={relative(p): digest(p) for p in (stdout, stderr)})
        path = directory/f"{stem}.receipt.json"
        path.write_text(json.dumps(record))
        return path

    for build in (old_build, new_build):
        compiled_receipt = synthetic_receipt(
            build, "compile", ["verilator", "--Mdir", relative(build/"compile-obj")])
        (build/"binding.json").write_text(json.dumps(dict(
            synthetic=True, identity=identity, compile_receipt=relative(compiled_receipt),
            binary_sha256=digest(binary))))
    old_case = output/f"synthetic-old-case-{uuid.uuid4().hex[:12]}"
    new_case = output/f"synthetic-new-case-{uuid.uuid4().hex[:12]}"
    old_case.mkdir()
    new_case.mkdir()
    for directory in (old_case, new_case):
        (directory/"vectors.txt").write_text("identical synthetic vectors")
    (old_case/"observations.txt").write_text("synthetic public output")
    simulated_receipt = synthetic_receipt(
        old_case, "simulation",
        [relative(old_binary), f"+vectors={relative(old_case/'vectors.txt')}",
         f"+observations={relative(old_case/'observations.txt')}"])
    (old_case/"case.json").write_text(json.dumps(dict(
        synthetic=True, artifact_sha256={relative(old_binary): digest(binary),
                                        relative(old_case/"observations.txt"):
                                        digest(old_case/"observations.txt")})))

    def rebound():
        return validated_execution(simulated_receipt, binary, relative(new_build/"binding.json"),
                                   list(sources), [new_case/"vectors.txt"], [])

    checked = rebound()
    if (checked is None or relative(binary) not in checked[1]
            or relative(old_binary) in checked[1]):
        raise AssertionError("identical rebuilt executable could not rebind complete observations")
    assertions += 1
    binary.write_bytes(b"different synthetic executable bytes")
    if rebound() is not None:
        raise AssertionError("different rebuilt executable admitted old observations")
    binary.write_bytes(b"synthetic executable bytes; never executed")
    assertions += 1
    (old_case/"simulation.stdout.txt").unlink()
    if rebound() is not None:
        raise AssertionError("executable replacement concealed reclaimed raw observations")
    assertions += 1
    import run_benchmarks

    events = []
    synthetic = output / f"synthetic-benchmark-{uuid.uuid4().hex[:12]}"

    def compilation(directory):
        events.append("compile")
        if (directory / "synthetic-public-input").exists():
            raise AssertionError("reclaimable public input was acquired before compilation")
        return "synthetic-binary", "synthetic-binding"

    def acquisition(directory):
        events.append("acquire")
        (directory / "synthetic-public-input").write_text("synthetic input")
        return [dict(task="synthetic", id="scheduling-only")], {}, []

    def image(directory, bindings):
        events.append("image")
        if not (directory / "synthetic-public-input").is_file():
            raise AssertionError("post-build acquisition missing")
        return dict(image="synthetic-input")

    def evaluation(directory, works, bindings, payload, build, smoke, chunks):
        events.append("execute")
        if build != ("synthetic-binary", "synthetic-binding"):
            raise AssertionError("compiled build was not passed to execution")
        return [dict(task="synthetic", id="scheduling-only", status="incomplete")]

    with patch("official_stream.compiled", side_effect=compilation), \
            patch("run_benchmarks.prepare", side_effect=acquisition), \
            patch("run_benchmarks.checkpoint_image", side_effect=image), \
            patch("run_benchmarks.evaluate", side_effect=evaluation), \
            patch.object(sys, "argv", ["tests/run_benchmarks.py", "--stream-smoke",
                                      "--output", relative(synthetic)]), \
            redirect_stdout(io.StringIO()):
        exit_code = run_benchmarks.main()
    if exit_code != 1 or events != ["compile", "acquire", "image", "execute"]:
        raise AssertionError("benchmark lifecycle reordered inputs or concealed incomplete execution")
    assertions += 1
    events.clear()
    with patch("official_stream.compiled", side_effect=AssertionError("must not compile")), \
            patch("run_benchmarks.prepare", side_effect=acquisition), \
            patch("run_benchmarks.evaluate", side_effect=AssertionError("must not execute")), \
            patch.object(sys, "argv", ["tests/run_benchmarks.py", "--prepare-only",
                                      "--output", relative(output / f"prepare-{uuid.uuid4().hex[:12]}")]), \
            redirect_stdout(io.StringIO()):
        exit_code = run_benchmarks.main()
    if exit_code != 0 or events != ["acquire"]:
        raise AssertionError("input-only mode no longer excludes RTL compilation/execution")
    assertions += 1
    image_directory = output/"checkpoint-images"/f"official-image-{uuid.uuid4().hex[:12]}"
    image_directory.mkdir(parents=True)
    payload = image_directory/"image.bin"
    payload.write_bytes(b"synthetic pinned input; not a model")
    manifest = image_directory/"image-manifest.json"
    manifest.write_text(json.dumps(dict(descriptors=[])))
    image_record = dict(image=relative(payload), image_sha256=digest(payload),
                        image_bytes=payload.stat().st_size, manifest=relative(manifest))
    expected_image = payload.read_bytes()
    stream_calls = []

    def reclaim_then_resume(directory, image, *args, **kwargs):
        stream_calls.append(directory)
        if len(stream_calls) <= 2:
            payload.unlink()
            if len(stream_calls) == 1:
                raise FileNotFoundError(errno.ENOENT, "synthetic input reclamation",
                                        str(payload.resolve()))
            stderr = directory/"simulation.stderr.txt"
            stderr.write_text("OFFICIAL_STREAM_FAILURE cannot open pinned memory image\n")
            stdout = directory/"simulation.stdout.txt"
            stdout.write_text("")
            raise ExecutionFailure("synthetic child input reclamation",
                                   dict(argv=["synthetic", "--image", image["image"]],
                                        timed_out=False, exit=1, launched=True,
                                        stderr=relative(stderr), stdout=relative(stdout)))
        if payload.read_bytes() != expected_image:
            raise AssertionError("pinned input was not restored byte-for-byte")
        result = dict(status="incomplete", summary=dict(complete=0))
        (directory/"stream-result.json").write_text(json.dumps(result))
        return result

    work = dict(task="synthetic", id="lifetime-only", token_ids=[0, 1],
                scored_positions=[0], scored_tokens=1)
    with patch("official_stream.run_stream", side_effect=reclaim_then_resume), \
            patch("run_benchmarks.score_executed", return_value=dict(status="incomplete")):
        rows = run_benchmarks.evaluate(output, [work], {}, image_record,
                                      ("synthetic-binary", "synthetic-binding"))
    if (len(stream_calls) != 3 or rows[0]["status"] != "incomplete"
            or len(rows[0]["input_recoveries"]) != 2
            or payload.read_bytes() != expected_image):
        raise AssertionError("input recovery lost an attempt, changed bytes or fabricated completion")
    assertions += 1
    with payload.open("rb") as source:
        try:
            run_benchmarks.restore_image(source, image_record, output, dict(synthetic=True))
        except FileExistsError:
            assertions += 1
        else:
            raise AssertionError("input recovery overwrote an existing artifact")
    with patch("official_stream.run_stream", side_effect=ExecutionFailure(
            "synthetic numerical failure",
            dict(argv=["synthetic", "--image", image_record["image"]],
                 timed_out=False, exit=1, launched=True))), \
            patch("run_benchmarks.score_executed", side_effect=AssertionError("must not score")):
        rows = run_benchmarks.evaluate(output, [work], {}, image_record,
                                      ("synthetic-binary", "synthetic-binding"))
    if rows[0]["status"] != "failed" or "synthetic numerical failure" not in rows[0]["error"]:
        raise AssertionError("input recovery concealed a non-input execution failure")
    assertions += 1
    previous = os.environ.get("HT3_CHECK_DEADLINE")
    try:
        deadline = time.time()+70
        os.environ["HT3_CHECK_DEADLINE"] = str(deadline)
        for identifier in ("integrated_geometry", "parameters", "mutations",
                           "stream_checkpoint", "benchmarks"):
            with patch("verify.execute", side_effect=AssertionError("must not launch")):
                row = child(identifier, [f"tests/run_{identifier}.py"], output,
                            budget=1800, reserve=30,
                            minimum=MINIMUM_ALLOCATIONS[identifier])
            if (row["status"] != "not_started"
                    or row["failure_kind"] != "execution_budget_unstarted"
                    or float(os.environ["HT3_CHECK_DEADLINE"]) != deadline):
                raise AssertionError("insufficient allocation launched or reset the deadline")
            assertions += 1
        os.environ["HT3_CHECK_DEADLINE"] = str(time.time()+600)

        def sufficient(argv, parent, identifier, version):
            allocation = float(os.environ["HT3_CHECK_DEADLINE"])-time.time()
            if not 350 < allocation <= 360:
                raise AssertionError("useful cold compilation allocation not preserved")
            directory = ROOT/argv[argv.index("--output")+1]
            directory.mkdir()
            (directory/"result.json").write_text(json.dumps(dict(status="passed")))

        with patch("verify.execute", side_effect=sufficient):
            row = child("synthetic-useful", ["tests/not-hardware.py"], output,
                        budget=360, reserve=30, minimum=300)
        if row["status"] != "passed":
            raise AssertionError("useful allocation rejected")
        assertions += 1
    finally:
        if previous is None:
            os.environ.pop("HT3_CHECK_DEADLINE", None)
        else:
            os.environ["HT3_CHECK_DEADLINE"] = previous
    cold = output / f"synthetic-cold-case-{uuid.uuid4().hex[:12]}"
    cold.mkdir()
    with patch("run_compatibility.validated_execution", return_value=None), \
            patch("run_compatibility.remaining", return_value=23.985), \
            patch("run_compatibility.execute", side_effect=AssertionError("must not launch")):
        try:
            resumable_case(cold, ROOT/"tests/synthetic-executable", "synthetic-binding",
                           [cold/"vectors.txt"], [], "synthetic-unstarted-",
                           lambda where, text: None)
        except RuntimeError as exc:
            if (failure_details(exc).get("failure_kind") != "execution_budget_unstarted"
                    or exc.record["minimum_s"] != 120 or exc.record["launched"]):
                raise AssertionError("cold-case refusal was not an explicit unstarted obligation")
            assertions += 1
        else:
            raise AssertionError("insufficient residual time admitted a cold simulation")
    admission = RuntimeError("synthetic execution admitted")
    with patch("run_compatibility.validated_execution", return_value=None), \
            patch("run_compatibility.remaining", return_value=120), \
            patch("run_compatibility.execute", side_effect=admission) as launched:
        try:
            resumable_case(cold, ROOT/"tests/synthetic-executable", "synthetic-binding",
                           [cold/"vectors.txt"], [], "synthetic-cold-boundary-",
                           lambda where, text: None)
        except RuntimeError as exc:
            if exc is not admission or launched.call_count != 1:
                raise AssertionError("useful cold allocation did not reach execution")
            assertions += 1
        else:
            raise AssertionError("synthetic execution failure disappeared")
    with patch("run_compatibility.validated_execution", return_value=None), \
            patch("run_compatibility.remaining", return_value=120), \
            patch("run_compatibility.execute", side_effect=AssertionError("must not launch")):
        try:
            resumable_case(cold, ROOT/"tests/synthetic-executable", "synthetic-binding",
                           [cold/"vectors.txt"], [], "synthetic-cold-batch-",
                           lambda where, text: None, minimum=180)
        except RuntimeError as exc:
            if (failure_details(exc).get("failure_kind") != "execution_budget_unstarted"
                    or exc.record["minimum_s"] != 180):
                raise AssertionError("batch did not retain its larger cold allocation")
            assertions += 1
        else:
            raise AssertionError("short batch allocation was accepted")
    retained_case = output / f"synthetic-retained-case-{uuid.uuid4().hex[:12]}"
    retained_case.mkdir()
    retained_receipt = retained_case/"simulation.receipt.json"
    retained_receipt.write_text("{}")
    reuse = output / f"synthetic-reused-case-{uuid.uuid4().hex[:12]}"
    reuse.mkdir()
    with patch.object(Path, "glob", return_value=[retained_receipt]), \
            patch("run_compatibility.validated_execution", return_value=("checked", {"synthetic": "hash"})), \
            patch("run_compatibility.remaining", side_effect=AssertionError("reuse needs no cold allocation")), \
            patch("run_compatibility.execute", side_effect=AssertionError("must not launch")):
        row = resumable_case(reuse, ROOT/"tests/synthetic-executable", "synthetic-binding",
                             [reuse/"vectors.txt"], [], "synthetic-reused-",
                             lambda where, text: dict(status="passed"))
        if not row["reused"] or row["simulation_receipt"] != relative(retained_receipt):
            raise AssertionError("settled observations were lost at a short remaining allocation")
        assertions += 1
    seen = []

    def failed_baseline(argv, parent, stem, version, root):
        if stem in seen:
            raise AssertionError("retry would collide with immutable prior outputs")
        seen.append(stem)
        directory = root/argv[argv.index("--output")+1]
        directory.mkdir(parents=True)
        (directory/"case-result.json").write_text(json.dumps(dict(status="failed")))
        (directory/"case.receipt.json").write_text(json.dumps(dict(timed_out=False)))
        raise RuntimeError("deliberate synthetic baseline rejection")

    disposable = output/f"synthetic-bundle-{uuid.uuid4().hex[:12]}"
    disposable.mkdir()
    with patch("run_mutations.execute", side_effect=failed_baseline):
        for _ in range(2):
            _, result, error = trial(output, disposable, "baseline-epilogue", "epilogue")
            if result["status"] != "failed" or error is None:
                raise AssertionError("failed baseline became success")
            assertions += 1
    if len(set(seen)) != 2:
        raise AssertionError("failed baseline retry names not unique")
    assertions += 1
    if len({j[0] for j in schedule()}) != len(schedule()):
        raise AssertionError("duplicate mandatory job")
    assertions += 1
    for path in (ROOT/"tests").glob("*.py"):
        ast.parse(path.read_text(), filename=relative(path))
    config = dict(hidden_size=64, num_attention_heads=1, num_key_value_heads=1,
                  num_hidden_layers=1, rope_theta=1000000, hidden_act="silu",
                  use_sliding_window=False, tie_word_embeddings=True,
                  vocab_size=3, max_position_embeddings=8, rms_norm_eps=1e-6)
    rng = np.random.default_rng(2026)
    weights = {"model.embed_tokens.weight": rng.normal(0, .1, (3, 64)),
               "model.norm.weight": np.ones(64)}
    prefix = "model.layers.0."
    for kind in ("input_layernorm", "post_attention_layernorm"):
        weights[prefix+kind+".weight"] = np.ones(64)
    for kind in ("q", "k", "v", "o"):
        weights[prefix+f"self_attn.{kind}_proj.weight"] = rng.normal(0, .01, (64, 64))
        if kind != "o":
            weights[prefix+f"self_attn.{kind}_proj.bias"] = np.zeros(64)
    for kind in ("gate", "up", "down"):
        weights[prefix+f"mlp.{kind}_proj.weight"] = rng.normal(
            0, .01, (64, 8) if kind == "down" else (8, 64))

    class SyntheticWeights:
        def tensor(self, name, selection=None):
            return weights[name] if selection is None else weights[name][selection]

    checkpoint = SyntheticWeights()
    full = {name: QwenFP64(config, checkpoint, name == "represented_image")
            for name in ("native", "represented_image")}
    reduced = {name: QwenFP64(config, checkpoint, name == "represented_image")
               for name in full}
    for name in full:
        full[name].step(0)
        if reduced[name].step(0, emit_logits=False) is not None:
            raise AssertionError("unscored step unexpectedly produced logits")
    state = output/"synthetic-reference-state.npz"
    save_state(state, reduced)
    restored = {name: QwenFP64(config, checkpoint, name == "represented_image")
                for name in full}
    restore_state(state, restored, 1)
    for name in full:
        expected = full[name].step(1)
        actual = restored[name].step(1)
        if not np.array_equal(actual, expected):
            raise AssertionError("restored FP64 state or omitted prefix logits changed results")
        assertions += 1
    try:
        restore_state(state, restored, 2)
    except AssertionError:
        assertions += 1
    else:
        raise AssertionError("wrong reference position accepted")
    nll = likelihood(np.asarray([1000, 1000+math.log(3)], dtype=np.float64), 1)
    if not math.isclose(nll, math.log(4/3), rel_tol=0, abs_tol=2e-13):
        raise AssertionError("persistent score likelihood differs from analytic FP64 result")
    assertions += 1
    return dict(status="passed", kind="synthetic-harness-regression",
                assertions=assertions, cases=list(names),
                scope="cache/allocation/retry and synthetic FP64 continuation; not RTL acceptance")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/run_harness_regression.py", *sys.argv[1:]],
                   cwd=".", start=timestamp(), timeout=remaining(),
                   source_sha256=hashes(), tool_version=sys.version)
    result = run(output)
    (output/"result.json").write_text(json.dumps(result, indent=2))
    receipt.update(exit=0, timed_out=False, end=timestamp(),
                   result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
