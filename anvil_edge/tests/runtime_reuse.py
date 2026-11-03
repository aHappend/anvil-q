"""Bounded performance repair: python3 tests/verify.py --probe runtime-input-reuse.

Regenerate both representations, compare the complete 150-case target matrix,
execute that matrix and compact paired controls, then measure builds and wall
time. Historical failure links are advisory, never prerequisite passing shards.
This is not aggregate L1, synthesis, timing, HIL or model acceptance.
"""

import ast
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re
import threading
import time
from unittest.mock import patch

from numerics import Geometry, core_test, run_numerical, CORE_BENCH
from protocol import UART
from scheduling import cache_recovery, resource_limits
from text import BENCH, run_tokenizer, tokenizer_test


ROOT = Path(__file__).resolve().parent.parent
FAILED = "evidence/verification/l1-36df656236ac4ca08fea2716eea1590a"
ATTEMPT = ".vulcan/engineering/run-0001/attempt-0131"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x", encoding="ascii") as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write("\n")


def cleanup_settled_intermediates(evidence):
    """Only these two interrupted compilers have disposable objects locally."""
    result_path = ROOT / ATTEMPT / "result.json"
    if not result_path.exists():
        evidence.record["compiler_cleanup"] = {
            "removed": [], "reason": "No authentic settled-attempt record; no historical cleanup"}
        return
    result = json.loads(result_path.read_bytes())
    if (result["exit_code"] != -9 or not result["process_scope_settled"] or
            result["process_scope"]["scope"]["remaining"]):
        raise RuntimeError("Historical compiler cleanup requires settled attempt-0131")
    directories = {
        ROOT / FAILED / "case-0084-suite-11-run_tokenizer" /
        "tokenizer-bos-tokens-over-4096-s1/obj",
        ROOT / FAILED / "case-0094-suite-12-run_numerical" /
        "numerical-h8-l1-s17-embedding-negative-inf/obj",
    }
    for path in (ROOT / FAILED).rglob("receipt.json"):
        row = json.loads(path.read_bytes())
        argv = row.get("argv", [])
        if argv and argv[0] == "verilator" and "--Mdir" in argv:
            relative = Path(argv[argv.index("--Mdir") + 1])
            if (relative.is_absolute() or ".." in relative.parts or
                    relative.parts[:3] != Path(FAILED).parts or relative.name != "obj"):
                raise RuntimeError("Unexpected historical compiler directory")
            directories.add(ROOT / relative)
    settlement_records = []
    finals = sorted((ROOT / "evidence/preparation").glob("*/receipt.json"))
    finals += sorted((ROOT / "evidence/verification").glob("*/receipt.json"))
    for final in finals:
        row = json.loads(final.read_bytes())
        if not row.get("child_settled"):
            continue
        used = False
        for child in row.get("children", []):
            argv = child.get("argv", [])
            if (argv and argv[0] == "verilator" and "--Mdir" in argv and
                    child.get("child_settled") and child.get("process_group_settled", True)):
                relative = Path(argv[argv.index("--Mdir") + 1])
                if relative.is_absolute() or ".." in relative.parts:
                    raise RuntimeError("Unexpected settled preparation compiler directory")
                directory = ROOT / relative
                if directory.is_relative_to(final.parent) and directory.name == "obj":
                    directories.add(directory)
                    used = True
        if used:
            settlement_records.append({"path": str(final.relative_to(ROOT)), "sha256": sha(final)})
    inventory = []
    suffixes = (".o", ".a", ".gch", ".cpp", ".h", ".d", ".mk", ".dat")
    for directory in sorted(directories):
        for path in sorted(directory.iterdir()) if directory.exists() else []:
            if path.is_file() and not path.is_symlink() and path.suffix in suffixes:
                inventory.append({"path": str(path.relative_to(ROOT)),
                                  "sha256": sha(path), "bytes": path.stat().st_size})
    # Persist the exact inventory before unlinking, retaining all input/source,
    # binaries, failed logs and existing receipts. Generated C++/headers are
    # compiler intermediates, not SV sources or input snapshots.
    save(evidence.path / "compiler-cleanup-inventory.json", inventory)
    for row in inventory:
        path = ROOT / row["path"]
        if sha(path) != row["sha256"]:
            raise RuntimeError("Disposable compiler artifact changed before cleanup")
        path.unlink()
    evidence.record["compiler_cleanup"] = {
        "settled_failure_record": str(result_path.relative_to(ROOT)),
        "settled_failure_record_sha256": sha(result_path),
        "inventory": evidence.relative(evidence.path / "compiler-cleanup-inventory.json"),
        "removed_files": len(inventory),
        "removed_bytes": sum(row["bytes"] for row in inventory),
        "additional_settlement_receipts": settlement_records,
    }


class Capture:
    def __init__(self, path):
        self.path = path
        path.mkdir()
        self.name_prefix = ""
        self.rows = {}

    def relative(self, path):
        return str(path.relative_to(ROOT))

    def tools(self, names):
        pass

    def simulate(self, name, bench, sources, comparisons, *, compiled_workload=False):
        assert isinstance(compiled_workload, bool)
        if name.startswith(("numerical-h", "tokenizer-")):
            if name in self.rows:
                raise AssertionError(f"Duplicate representation case {name}")
            self.rows[name] = (bench, sources, comparisons)


def loaded(bench):
    return {
        name: [int(line, 16) for line in (ROOT / path).read_text().splitlines()]
        for path, name in re.findall(r'\$readmemh\("([^"]+)",(\w+)\);', bench)
    }


def assignments(bench, name):
    values = {}
    for index, value in re.findall(
            rf"\b{name}\[(\d+)\]=((?:32|64)'h[0-9a-f]+|\d+);", bench):
        values[int(index)] = int(value.split("'h")[-1], 16) if "'h" in value else int(value)
    assert sorted(values) == list(range(len(values))), name
    return [values[index] for index in range(len(values))]


def expanded_key(bench, sources):
    canonical = re.sub(r"reg\s+\[31:0\]\s+rng=\d+;",
                       "reg [31:0] rng=RUNTIME_SEED;", bench)
    if "$readmemh" in canonical:
        raise AssertionError("Extend baseline file canonicalization before use")
    return hashlib.sha256((canonical + json.dumps(sources)).encode("ascii")).hexdigest()


def representation_equivalence(evidence):
    """Compare every original seeded vector, not just the executed submatrix."""
    original = Capture(evidence.path / "expanded-inputs")
    candidate = Capture(evidence.path / "runtime-inputs")
    with patch("numerics.core_test",
               lambda *a, **k: core_test(*a, **k, runtime_inputs=False)), patch(
                   "text.tokenizer_test",
                   lambda *a, **k: tokenizer_test(*a, **k, runtime_inputs=False)):
        run_numerical(original)
        run_tokenizer(original)
    cases = []

    def collect(function, scope, *args, **kwargs):
        previous = set(scope.rows)
        function(scope, *args, **kwargs)
        name, = scope.rows.keys() - previous
        cases.append((name, lambda real, args=args, kwargs=copy.deepcopy(kwargs):
                      function(real, *args, **kwargs)))

    with patch("numerics.core_test", lambda *a, **k: collect(core_test, *a, **k)), patch(
            "text.tokenizer_test", lambda *a, **k: collect(tokenizer_test, *a, **k)):
        run_numerical(candidate)
        run_tokenizer(candidate)
    assert original.rows.keys() == candidate.rows.keys()
    results = []
    baseline_keys = {}
    for name in original.rows:
        before, sources, comparisons = original.rows[name]
        after, next_sources, next_comparisons = candidate.rows[name]
        assert sources == next_sources and comparisons == next_comparisons
        data = loaded(after)
        baseline_keys[name] = expanded_key(before, sources)
        if name.startswith("numerical-"):
            records = data["initial_records"]
            for field, shift, mask in (
                    ("memory", 0, 0xFFFFFFFF), ("first", 32, 0xFFFFFFFF),
                    ("limit", 64, 0xFFFFFFFF), ("writable", 96, 1)):
                assert assignments(before, field) == [(word >> shift) & mask for word in records]
            assert assignments(before, "expected") == data["expected"]
            assert assignments(before, "expected_logits") == data["expected_logits"]
            assert assignments(before, "count") == [0] * len(records)
            tokens = [int(value) for value in re.findall(r"^\s*token\((\d+),", before, re.M)]
            is_fault = data["fault_config"][0]
            assert tokens == (data["token_words"][:1] if is_fault else data["token_words"])
            if is_fault:
                bus, slot = re.search(
                    r"mem_rsp_error=(\d+) && pending_slot==(\d+);", before).groups()
                assert data["fault_config"][1:] == [int(slot), int(bus)]
            else:
                assert data["fault_config"] == [0, 0, 0]
            # Lookup and all original transfer-time predicates are retained.
            assert re.search(r"case \(key\)(.*?)endcase", before, re.S)[1] == re.search(
                r"case \(key\)(.*?)endcase", after, re.S)[1]
            for diagnostic in re.findall(r'\$fatal\(1,"([^"]+)"', before):
                assert f'$fatal(1,"{diagnostic}"' in after, diagnostic
            vector_count = len(records) + len(data["expected"]) + len(data["expected_logits"])
        else:
            control = data["runtime_control"]
            inputs = [(int(value, 16), int(last)) for value, last in re.findall(
                r"item\(32'h([0-9a-f]+),([01])\);", before)]
            assert inputs == [(word, int(index == control[0] - 1))
                              for index, word in enumerate(data["input_words"][:control[0]])]
            assert assignments(before, "expected") == data["expected"][:control[1]]
            memory = [(int(a, 16), int(v, 16)) for a, v in re.findall(
                r"64'h([0-9a-f]+): memory=32'h([0-9a-f]+);", before)]
            assert memory == [(word >> 32, word & 0xFFFFFFFF)
                              for word in data["table_records"][:control[5]]]
            assert data["table_records"][control[5]:] == [0] * (
                len(data["table_records"]) - control[5])
            assert data["runtime_config"] == [
                int(re.search(pattern, before)[1], 16) for pattern in (
                    r"\.cfg_table_bases\(1024'h([0-9a-f]+)\)",
                    r"\.cfg_table_counts\(512'h([0-9a-f]+)\)",
                    r"\.cfg_metadata\(1024'h([0-9a-f]+)\)")]
            assert f"if (8'h{control[2]:02x}!=0)" in before
            assert f"tbl_rsp_error={control[3]};" in before
            assert f"repeat ({control[4]})" in before
            # The same template supplies every public scoreboard assertion.
            normalized = after
            for expression, literal in (
                    ("runtime_control[1]", str(control[1])),
                    ("runtime_control[0]", str(control[0])),
                    ("runtime_control[2]", f"8'h{control[2]:02x}")):
                normalized = normalized.replace(expression, literal)
            assert re.search(r"always @\(posedge clk\) begin(.*?)task automatic tick",
                             before, re.S)[1] == re.search(
                                 r"always @\(posedge clk\) begin(.*?)task automatic tick",
                                 normalized, re.S)[1]
            vector_count = len(inputs) + control[1] + control[5]
        results.append({"name": name, "vectors_compared": vector_count,
                        "required_comparisons": comparisons, "equal": True})
    save(evidence.path / "representation-equivalence.json", results)
    evidence.record["runtime_representation_equivalence"] = {
        "case_count": len(results), "vectors_compared": sum(r["vectors_compared"] for r in results),
        "all_seeds_capacities_and_rejections_preserved": True,
        "results": evidence.relative(evidence.path / "representation-equivalence.json"),
    }
    return baseline_keys, cases


def summary(row):
    return [line for line in (ROOT / row["simulation_receipt"]["stdout"]).read_text().splitlines()
            if line.startswith(("CORE_NUMERIC ", "TEXT_COUNTS ", "COMPARED "))]


def head_controls(evidence):
    from head_row_reuse import head_bench
    cleanup_settled_intermediates(evidence)
    failures = []
    for label, runtime in (("expanded", False), ("runtime", True)):
        scope = copy.copy(evidence)
        scope.name_prefix = label + "-head-control-"
        try:
            core_test(scope, Geometry(vocabulary=17), 17, runtime_inputs=runtime,
                      bench_transform=lambda bench: head_bench(bench, 8, True, True))
        except Exception as error:
            failures.append(f"{label}: {error}")
    if failures:
        raise RuntimeError("; ".join(failures))


def shell_logging_control(evidence):
    from qwen_shell import shell_case
    directory = evidence.path / "compact-shell-inputs"
    directory.mkdir()
    evidence.child(["python3", "tests/qwen_shell.py", evidence.relative(directory), "--compact"],
                   "compact-shell-inputs")
    info = json.loads((directory / "shell-reference.json").read_bytes())
    row = shell_case(evidence, info, 17, 1, True)
    text = (ROOT / row["simulation_receipt"]["stdout"]).read_text()
    operations = [(int(position), int(token), int(cycle)) for position, token, cycle in re.findall(
        r"QWEN_SHELL_OPERATION frame=0 position=(\d+) token=(\d+) cycles=(\d+)", text)]
    expected = info["cases"][0]["core_operation_ids"]
    assert [(position, token) for position, token, _ in operations] == list(enumerate(expected))
    assert len(operations) == 9
    assert all(operations[i][2] < operations[i + 1][2] for i in range(len(operations) - 1))
    assert text.index("QWEN_SHELL_COMPLETION") < text.index("QWEN_SHELL_OPERATION")
    evidence.record["bounded_shell_logging"] = {
        "operation_measurements": operations, "emitted_only_after_completion": True,
        "actual_comparisons": row["actual_comparisons"],
        "simulation_receipt": row["simulation_receipt"],
        "scope": "Synthetic compact real-core shell; not a pretrained/official-table benchmark",
    }


def runtime_reuse(evidence):
    started = time.monotonic()
    cleanup_settled_intermediates(evidence)
    evidence.record["scheduling_before_cleanup"] = evidence._limits
    evidence._limits = resource_limits(ROOT)
    evidence._slots = threading.BoundedSemaphore(evidence._limits["workers"])
    evidence.record["scheduling"] = evidence._limits
    evidence.record["runtime_repair_scope"] = (
        "attempt-0131 compilation/scheduling repair; advisory equivalence submatrix, not L1 acceptance")
    # Historical linkage is read-only and optional; current controls generate
    # their own inputs, executables and references without predecessor binaries.
    evidence.record["failed_invocation"] = {
        "directory": FAILED, "final_receipt_present": (ROOT / FAILED / "receipt.json").exists(),
        "available_records": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}
            for path in (ROOT / FAILED / "launch.json", ROOT / ATTEMPT / "result.json",
                         ROOT / ATTEMPT / "patrol.json") if path.exists()],
    }
    source = ROOT / FAILED / "sources/tests/numerics.py"
    text_source = ROOT / FAILED / "sources/tests/text.py"
    if source.exists() and text_source.exists():
        for path, constant, value in ((source, "CORE_BENCH", CORE_BENCH),
                                      (text_source, "BENCH", BENCH)):
            tree = ast.parse(path.read_text())
            assigned = next(node.value for node in tree.body if isinstance(node, ast.Assign)
                            and any(isinstance(target, ast.Name) and target.id == constant
                                    for target in node.targets))
            assert ast.literal_eval(assigned) == value, "Original public scoreboard changed"
        evidence.record["historical_scoreboards_byte_identical"] = True
        for path, names in (
                (source, ("signed", "saturate", "round_ratio", "toward_zero", "half",
                          "exponential", "silu", "Geometry", "Reference",
                          "run_numerical", "run_numerical_errors")),
                (text_source, ("tokenizer_fixture", "tokenizer_reference",
                               "run_tokenizer", "run_tokenizer_capacity"))):
            old = {node.name: ast.dump(node, include_attributes=False)
                   for node in ast.parse(path.read_text()).body if hasattr(node, "name")}
            current = {node.name: ast.dump(node, include_attributes=False)
                       for node in ast.parse((ROOT / "tests" / path.name).read_text()).body
                       if hasattr(node, "name")}
            assert all(old[name] == current[name] for name in names)
        evidence.record["historical_references_and_case_matrices_ast_identical"] = True
    evidence.tools(("python3", "iverilog", "vvp", "verilator", "g++", "make"))
    baseline_keys, cases = representation_equivalence(evidence)
    for mask in range(1 << 12):
        for kind in range(12):
            assigned = (mask & ~(1 << kind)) | (1 << kind)
            assert assigned == mask | (1 << kind)
    evidence.record["kind_mask_bookkeeping"] = {
        "equivalent_bit_union_cases": (1 << 12) * 12,
        "original_acceptance_mask": "12'hfff",
        "repair": "Whole-vector accepted-kind union preserves coverage across reset coroutines",
    }
    measured_start = time.monotonic()
    evidence.run_cases(cases)
    rows = list(evidence.record["coverage"])
    keys = Counter(row["compile_cache_key"] for row in rows)
    builds = sum(not row["compile_cache_hit"] for row in rows)
    assert len(rows) == len(cases) == 150
    assert builds == len(keys) and builds < len(rows)
    evidence.record["runtime_scheduling_measurement"] = {
        "cases": len(rows), "compilations": builds,
        "expanded_representation_unique_compilations": len({
            baseline_keys[row["name"]] for row in rows}),
        "cache_hits": sum(row["compile_cache_hit"] for row in rows),
        "actual_comparisons": sum(row["actual_comparisons"] for row in rows),
        "duration_s": time.monotonic() - measured_start,
        "current_resource_limits": resource_limits(ROOT),
        "compile_summed_s": sum(row["compile_receipt"]["duration_s"]
                                for row in rows if not row["compile_cache_hit"]),
        "simulate_summed_s": sum(row["simulation_receipt"]["duration_s"] for row in rows),
    }
    assert builds < evidence.record["runtime_scheduling_measurement"][
        "expanded_representation_unique_compilations"]
    # Execute the old expanded representation as a live paired control, retaining
    # exact independent expectations and public transaction/comparison summaries.
    fault = {"name": "write-response-error", "key": (8, 0, 0, 0, 0), "bus_error": True}
    for kind, fault in (("text", None), ("core", None), ("fault", fault)):
        baseline = copy.copy(evidence)
        baseline.name_prefix = "expanded-"
        if kind == "text":
            before = tokenizer_test(baseline, 1, "bytes-3", "xxx", byte_capacity=3,
                                    token_capacity=3, runtime_inputs=False)
            after = next(row for row in rows if row["name"] == "tokenizer-bytes-3-s1")
        else:
            before = core_test(baseline, Geometry(), 1, fault=fault, runtime_inputs=False)
            after = next(row for row in rows if row["name"] == (
                "numerical-h8-l1-s1" + ("-" + fault["name"] if fault else "")))
        assert before["actual_comparisons"] == after["actual_comparisons"]
        assert summary(before) == summary(after), "Public transaction summaries changed"
    compact = copy.copy(evidence)
    compact.name_prefix = "four-state-"
    compact.simulator_override = "iverilog"
    tokenizer_test(compact, 17, "singleton", "x", byte_capacity=1, token_capacity=1)
    compact.simulate("uart", UART.replace("DIVISOR", "4").replace("@DEPTH@", "1").replace(
        "SEED", "17"), ["rtl/anvil_edge_fifo.sv", "rtl/anvil_edge_uart_io.sv"], 78)
    from head_row_reuse import head_bench, error_bench
    for label, transform, marker in (
            ("warm-reset", lambda bench: head_bench(bench, 8, True, True),
             "HEAD_RESET_RECOVERY warm_abort=1"),
            ("head-error", lambda bench: error_bench(bench, "weight-read"),
             "HEAD_ERROR_RECOVERY weight-read injected=1")):
        scope = copy.copy(evidence)
        scope.name_prefix = label + "-"
        row = core_test(scope, Geometry(vocabulary=17), 17, bench_transform=transform)
        assert marker in (ROOT / row["simulation_receipt"]["stdout"]).read_text()
    cache_recovery(evidence)
    shell_logging_control(evidence)
    costs = []
    for child in evidence.record["children"]:
        removed = child.get("compiler_intermediates_removed")
        if removed is not None:
            argv = child["argv"]
            binary = ROOT / argv[argv.index("--Mdir") + 1] / "simulation"
            costs.append({
                "compile_receipt": str(Path(child["stdout"]).parent / "receipt.json"),
                "discarded_bytes": sum(row["bytes"] for row in removed),
                "retained_executable_bytes": binary.stat().st_size,
            })
    evidence.record["measured_compiler_storage"] = {
        "builds": costs,
        "peak_post_link_output_bytes": max(
            row["discarded_bytes"] + row["retained_executable_bytes"] for row in costs),
        "scope": "Actual post-link project outputs, not process RSS or whole-filesystem peak",
    }
    evidence.record["runtime_repair_duration_s"] = time.monotonic() - started
