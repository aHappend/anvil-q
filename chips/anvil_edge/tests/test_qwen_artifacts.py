"""Artifact isolation regressions; real composition uses the production stage runner."""

import hashlib
import copy
import json
from pathlib import Path
import shutil
import sys
import uuid
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import official


def hashes(directory):
    return {str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(directory.rglob("*")) if path.is_file()}


def integrity_regression(directory):
    pinned = official.manifest()
    fixture = directory / ("corrupt-assets-" + uuid.uuid4().hex)
    data = fixture / "tests/data"
    data.mkdir(parents=True)
    shutil.copyfile(official.ROOT / "tests/data/assets.json", data / "assets.json")
    for item in pinned["ordered_files"]:
        shutil.copyfile(official.ROOT / item["path"], fixture / item["path"])
    corrupt = fixture / pinned["ordered_files"][0]["path"]
    original = corrupt.read_bytes()
    changed = bytes([original[0] ^ 1]) + original[1:]
    # This is a disposable asset copy, never the pinned project input.
    corrupt.write_bytes(changed)
    rejected = directory / ("rejected-validation-" + uuid.uuid4().hex)
    rejected.mkdir()
    with patch.object(official, "ROOT", fixture):
        try:
            official.validate(rejected)
        except RuntimeError as error:
            assert "asset length/hash mismatch" in str(error), str(error)
            mismatch = str(error)
        else:
            raise AssertionError("Corrupt pinned asset was accepted")
    assert not list(rejected.iterdir()), "Rejected assets produced a success-shaped record"
    fresh = directory / ("exclusive-validation-" + uuid.uuid4().hex)
    fresh.mkdir()
    official.validate(fresh)
    before = hashes(fresh)
    try:
        official.validate(fresh)
    except FileExistsError:
        pass
    else:
        raise AssertionError("Validation no longer enforces exclusive record creation")
    assert hashes(fresh) == before, "Exclusive-write rejection mutated earlier evidence"
    result = {"corrupt_asset_rejected": mismatch, "corrupt_copy_sha256":
              hashlib.sha256(changed).hexdigest(),
              "exclusive_write_rejected": True, "earlier_artifacts_unchanged": before}
    with (directory / "artifact-integrity-regression.json").open("x") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print("ARTIFACT_INTEGRITY corrupt_hash_rejected=1 exclusive_write_rejected=1")


def run_composition_regression(evidence):
    from verify import OFFICIAL_STAGES, run_stages, write_json

    evidence.tools(("python3",))
    evidence.child(["python3", "tests/scheduling.py", "--source-contract"],
                   "source-contract-regression")
    evidence.child(["python3", "tests/test_qwen_artifacts.py",
                    evidence.relative(evidence.path)], "artifact-integrity-regression")
    frozen, results = [], []

    def observe(stage):
        def execute(scope):
            for directory, expected in frozen:
                assert hashes(directory) == expected, "A later stage mutated earlier artifacts"
            stage(scope)
            for directory, expected in frozen:
                assert hashes(directory) == expected, "A later stage mutated earlier artifacts"
            validation = scope.path / "qwen-asset-validation.json"
            assert validation.is_file(), f"Validation did not execute for {stage.__name__}"
            snapshot = hashes(scope.path)
            assert snapshot, "Empty stage artifacts"
            frozen.append((scope.path, snapshot))
            results.append({"stage": stage.__name__,
                            "directory": evidence.relative(scope.path),
                            "artifact_sha256": snapshot})
        execute.__name__ = stage.__name__
        return execute

    # Actual fragments, exhaustive/random regex, Unicode/Oniguruma and official
    # reference consumers run sequentially under the same Evidence parent as L1.
    run_stages(evidence, [observe(stage) for stage in OFFICIAL_STAGES[:4]])
    assert len(frozen) == 4 and len({directory for directory, _ in frozen}) == 4
    for directory, expected in frozen:
        assert hashes(directory) == expected, "Earlier evidence changed after composition"
    regex = json.loads((frozen[1][0] / "qwen-regex-audit.json").read_bytes())
    assert regex["exhaustive_max_length"] == 4 and regex["exhaustive_sequences"] > 0
    assert regex["random_sequences_by_seed"] == {"1": 1000, "17": 1000, "89": 1000}
    write_json(evidence.path / "artifact-composition-regression.json", {
        "scope": "Bounded artifact-namespace repair, not full L1 or product acceptance",
        "stages": results, "earlier_artifacts_unchanged": True,
        "regex_exhaustive_sequences": regex["exhaustive_sequences"],
        "regex_random_sequences_by_seed": regex["random_sequences_by_seed"],
    })


def run_complete_table_regression(evidence):
    """Execute real complete-table consumers below isolated production stages."""
    from deepseek_integration import bos_mutations
    from qwen_integration import rtl_case, run_rtl, validate_table_source
    from verify import write_json

    evidence.tools(("python3", "iverilog", "vvp", "verilator", "g++", "make"))
    results = []

    def stage(scope, family, script, bos):
        argv = ["./.venv/bin/python", script, scope.relative(scope.path)]
        if bos:
            argv.append("--model-bos")
        scope.child(argv, family + "-complete-table-preparation")
        info = json.loads((scope.path / "complete-table-fixture.json").read_bytes())
        table_source = scope.path / "tables.hex"
        assert table_source != evidence.path / "tables.hex"
        validate_table_source(info, table_source)
        frozen = hashes(scope.path)
        record = json.loads((scope.path / (
            "model-bos-vectors.json" if bos else "official-vectors.json")).read_bytes())
        if family == "qwen":
            vectors = record
        else:
            vectors = [{"case": index, "input_utf8_hex": row["utf8_hex"],
                        "token_ids": row["token_ids"],
                        "decoded_utf8_hex": row["decoded_utf8_hex"]}
                       for index, row in enumerate(record["vectors"])]
        compact = [row for row in vectors if row["input_utf8_hex"] == "65cc81"]
        assert len(compact) == 1
        # Five exact benchmark inputs plus the existing compact portability
        # witness; these are tokenizer comparisons, not weighted inference.
        prompts = json.loads((official.ROOT / "tests/data/requirements.json").read_bytes())["prompts"]
        assert [row["input_utf8_hex"] for row in vectors[:5]] == [
            text.encode().hex() for text in prompts]
        selected = vectors[:5] + compact
        assert len({row["input_utf8_hex"] for row in selected}) == 6
        run_rtl(scope, info, selected, family, table_source=table_source)

        def nested(parent):
            parent.run_cases([
                ("capacity-eight", lambda leaf: rtl_case(
                    leaf, info, compact, 89, "verilator", 8, 500000, family,
                    table_source=table_source)),
            ], workers=1)
        scope.run_cases([("nested-table-consumer", nested)], workers=1)
        mutations = []
        if bos:
            def execute_mutants(mutant_scope):
                bos_mutations(mutant_scope, info, compact, table_source=table_source)
                mutations.extend(mutant_scope.record["bos_mutations"])
            scope.run_cases([
                ("bos-mutation-scope", execute_mutants),
            ], workers=1)

        rejected = []
        bad_directory = scope.path / "invalid-table-source"
        bad_directory.mkdir()
        bad_table = bad_directory / "tables.hex"
        bad_table.write_text("00000000\n", encoding="ascii")
        corrupt_info = copy.deepcopy(info)
        corrupt_info["tables"][0]["sha256"] = "0" * 64
        for label, fixture, source, expected in (
                ("missing", info, bad_directory / "missing.hex", FileNotFoundError),
                ("corrupt-memory", info, bad_table, ValueError),
                ("corrupt-table-hash", corrupt_info, table_source, ValueError)):
            with patch.object(scope, "simulate") as simulate:
                try:
                    rtl_case(scope, fixture, compact, 17, "iverilog", 64, 500000,
                             family, table_source=source)
                except expected as error:
                    rejected.append({"case": label, "error": str(error)})
                else:
                    raise AssertionError(f"Invalid table source accepted: {label}")
                simulate.assert_not_called()
        assert len(rejected) == 3
        bindings = []
        for bench in sorted(scope.path.rglob("bench.sv")):
            text = bench.read_text()
            expected = f'$readmemh("{scope.relative(table_source)}",table_words);'
            assert expected in text, f"Wrong producing-stage table in {bench}"
            bindings.append({"bench": scope.relative(bench),
                             "bench_sha256": hashlib.sha256(bench.read_bytes()).hexdigest(),
                             "table_source": scope.relative(table_source),
                             "table_sha256": info["memory_hex_sha256"]})
        assert len(bindings) == (7 if bos else 5), bindings
        for name, digest in frozen.items():
            assert hashlib.sha256((scope.path / name).read_bytes()).hexdigest() == digest, (
                f"Consumer mutated producing-stage artifact: {name}")
        assert not (evidence.path / "tables.hex").exists(), "Aggregate-root table copy"
        results.append({"family": family, "producer": scope.relative(scope.path),
                        "fixture_sha256": frozen["complete-table-fixture.json"],
                        "bindings": bindings, "invalid_sources_rejected": rejected,
                        "bos_mutations": mutations,
                        "producer_artifacts_unchanged": frozen})

    evidence.run_cases([
        ("complete-table-qwen", lambda scope: stage(
            scope, "qwen", "tests/qwen_integration.py", False)),
        ("complete-table-deepseek", lambda scope: stage(
            scope, "deepseek", "tests/deepseek_integration.py", False)),
        ("complete-table-deepseek-bos", lambda scope: stage(
            scope, "deepseek-bos", "tests/deepseek_integration.py", True)),
    ], workers=1)
    rows = [row for row in evidence.record["coverage"] if "simulator" in row]
    assert len(rows) == 17 and sum(row["status"] == "passed" for row in rows) == 15
    mutations = [mutation for result in results for mutation in result["bos_mutations"]]
    assert len(mutations) == 2
    write_json(evidence.path / "complete-table-artifact-regression.json", {
        "scope": "Bounded artifact-path repair; complete official tables, six selected "
                 "vectors per family/policy, not full profile matrix or product acceptance",
        "families": results, "passed_simulations": 15,
        "bos_mutations": mutations,
        "aggregate_root_has_no_tables": True,
    })


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 tests/test_qwen_artifacts.py PROJECT_RELATIVE_EVIDENCE_DIRECTORY")
    directory = Path(sys.argv[1])
    if (directory.is_absolute() or ".." in directory.parts or not directory.is_dir()
            or directory.parts[:2] not in (
                ("evidence", "preparation"), ("evidence", "verification"))):
        raise SystemExit("Output must be an existing project-relative fresh evidence directory")
    integrity_regression(directory)
