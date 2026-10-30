"""Self-contained bounded input-representation and compiled-reuse diagnostic."""

import ast
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
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
    directories = [
        ROOT / FAILED / "case-0084-suite-11-run_tokenizer" /
        "tokenizer-bos-tokens-over-4096-s1/obj",
        ROOT / FAILED / "case-0094-suite-12-run_numerical" /
        "numerical-h8-l1-s17-embedding-negative-inf/obj",
    ]
    inventory = []
    for directory in directories:
        for path in sorted(directory.iterdir()) if directory.exists() else []:
            if path.is_file() and not path.is_symlink() and path.suffix in (".o", ".a", ".gch"):
                inventory.append({"path": str(path.relative_to(ROOT)),
                                  "sha256": sha(path), "bytes": path.stat().st_size})
    # Persist the exact inventory before unlinking, retaining all input/source,
    # generated C++/headers, binaries, failed logs and existing receipts.
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

    def simulate(self, name, bench, sources, comparisons):
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
    run_numerical(candidate)
    run_tokenizer(candidate)
    assert original.rows.keys() == candidate.rows.keys()
    results = []
    for name in original.rows:
        before, sources, comparisons = original.rows[name]
        after, next_sources, next_comparisons = candidate.rows[name]
        assert sources == next_sources and comparisons == next_comparisons
        data = loaded(after)
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


def summary(row):
    return [line for line in (ROOT / row["simulation_receipt"]["stdout"]).read_text().splitlines()
            if line.startswith(("CORE_NUMERIC ", "TEXT_COUNTS ", "COMPARED "))]


def runtime_reuse(evidence):
    started = time.monotonic()
    cleanup_settled_intermediates(evidence)
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
    evidence.tools(("python3", "iverilog", "vvp", "verilator", "g++", "make"))
    representation_equivalence(evidence)
    faults = (
        {"name": "embedding-nan", "key": (0, 0, 0, 1, 0), "word": 0x7E00},
        {"name": "post-gamma-nan", "key": (6, 0, 0, 0, 0), "word": 0x7E00},
        {"name": "read-response-error", "key": (0, 0, 0, 1, 0), "bus_error": True},
        {"name": "write-response-error", "key": (8, 0, 0, 0, 0), "bus_error": True},
    )
    cases = []
    for seed in (1, 17, 89):
        cases.append((f"core-{seed}", lambda scope, seed=seed: core_test(scope, Geometry(), seed)))
        for fault in faults:
            cases.append((f"core-{seed}-{fault['name']}",
                          lambda scope, seed=seed, fault=fault:
                          core_test(scope, Geometry(), seed, fault=fault)))
        cases.append((f"core-multilayer-{seed}", lambda scope, seed=seed: core_test(
            scope, Geometry(layers=2, hidden=16, intermediate=24, query_heads=2), seed)))
        for name, text, options in (
                ("ranked", "ABC", {}),
                ("overflow", "xxxx", {"error": 0x30}),
                ("bos-overflow", "xxx", {"bos": True, "error": 0x30}),
                ("invalid", "ABC", {"raw": b"\xc0\x80", "error": 0x10})):
            cases.append((f"text-{seed}-{name}",
                          lambda scope, seed=seed, name=name, text=text, options=options:
                          tokenizer_test(scope, seed, name, text, byte_capacity=3,
                                         token_capacity=3, **options)))
        for name, text, options in (
                ("capacity", "x" * 4096, {}),
                ("capacity-bos", "x" * 4096, {"bos": True, "error": 0x30}),
                ("capacity-over", "x" * 4097, {"token_capacity": 4097, "error": 0x30})):
            cases.append((f"text-{seed}-{name}",
                          lambda scope, seed=seed, name=name, text=text, options=options:
                          tokenizer_test(scope, seed, name, text, byte_capacity=4096,
                                         **dict({"token_capacity": 4096}, **options))))
    measured_start = time.monotonic()
    evidence.run_cases(cases)
    rows = list(evidence.record["coverage"])
    keys = Counter(row["compile_cache_key"] for row in rows)
    builds = sum(not row["compile_cache_hit"] for row in rows)
    assert len(rows) == len(cases) == 39
    assert builds == len(keys) and builds < len(rows)
    evidence.record["runtime_scheduling_measurement"] = {
        "cases": len(rows), "compilations": builds,
        "without_runtime_reuse_compilations": len(rows),
        "cache_hits": sum(row["compile_cache_hit"] for row in rows),
        "actual_comparisons": sum(row["actual_comparisons"] for row in rows),
        "duration_s": time.monotonic() - measured_start,
        "current_resource_limits": resource_limits(ROOT),
        "compile_summed_s": sum(row["compile_receipt"]["duration_s"]
                                for row in rows if not row["compile_cache_hit"]),
        "simulate_summed_s": sum(row["simulation_receipt"]["duration_s"] for row in rows),
    }
    # Execute the old expanded representation as a live paired control, retaining
    # exact independent expectations and public transaction/comparison summaries.
    for kind, fault in (("text", None), ("core", None), ("fault", faults[-1])):
        baseline = copy.copy(evidence)
        baseline.name_prefix = "expanded-"
        if kind == "text":
            before = tokenizer_test(baseline, 1, "ranked", "ABC", byte_capacity=3,
                                    token_capacity=3, runtime_inputs=False)
            after = next(row for row in rows if row["name"] == "tokenizer-ranked-s1")
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
    cache_recovery(evidence)
    evidence.record["runtime_repair_duration_s"] = time.monotonic() - started
