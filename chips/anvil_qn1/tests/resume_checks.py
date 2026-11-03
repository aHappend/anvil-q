"""Case checkpoints with exact computational snapshots and raw-output validation."""

import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile

from component_cache import assess, component
from execution import ROOT, relative
from model import Geometry


TOOLS = ("python3", "verilator", "g++", "make")
MODEL = ("tests/integration.py", "tests/model.py", "tests/reference.py")
MEMORY_PAIRS = ((1, 1), (8, 3), (1, 16), (8, 1), (1, 3), (8, 16))
WRAPPERS = {
    "tests/memory_checks.py": {"run_memory_matrix"},
    "tests/fault_checks.py": {"run_fault_matrix"},
    "tests/speculative_fault_checks.py": {"run_speculative_cancel_matrix"},
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def orchestration_equivalence(run, path, receipt, name):
    """Only listed matrix wrappers differ; all computational module nodes match."""
    if name not in WRAPPERS:
        return None
    snapshot = path.parent / "source" / name
    if (not snapshot.is_file() or
            hashlib.sha256(snapshot.read_bytes()).hexdigest() !=
            receipt.get("source_sha256", {}).get(name)):
        return None

    def computation(text):
        return [ast.dump(node, include_attributes=False)
                for node in ast.parse(text).body
                if not (isinstance(node, ast.FunctionDef) and node.name in WRAPPERS[name])]

    if computation(snapshot.read_text()) != computation((ROOT / name).read_text()):
        return None
    return {"basis": "snapshot AST equality for every top-level node except named "
                     "matrix orchestration; computational functions/imports/constants unchanged",
            "excluded_wrappers": sorted(WRAPPERS[name]),
            "snapshot_sha256": receipt["source_sha256"][name],
            "current_sha256": run.hashes[name]}


def memory_identity(index):
    require(type(index) is int and index in range(6), "unsupported memory case index")
    banks, queue = MEMORY_PAIRS[index]
    return {"geometry": vars(Geometry(q_heads=2 if index % 2 == 0 else 4)),
            "seed": (17, 89, 203)[index % 3], "banks": banks, "queue_depth": queue}


def validate_memory_case(result, index):
    identity = memory_identity(index)
    require(all(result.get(key) == value for key, value in identity.items()),
            "memory geometry/seed/banks/queue/scenario identity mismatch")
    geometry = Geometry(**identity["geometry"])
    records = result.get("transactions")
    require(isinstance(records, list) and len(records) == 6 and
            [r["position"] for r in records] == list(range(6)),
            "missing six consecutive compared memory frames")
    require(records[0]["input_token"] == 3 and records[1]["input_token"] == 4 and
            all(records[i]["input_token"] == records[i - 1]["argmax"] for i in range(2, 6)) and
            all(0 <= r["argmax"] < geometry.vocabulary for r in records),
            "invalid deferred continuation/reference records")
    summary = result.get("raw_summary", "")
    matches = re.findall(
        r"^SUMMARY transactions=(\d+) logits=(\d+) key_writes=(\d+) "
        r"value_writes=(\d+) memory_requests=(\d+) cycles=(\d+)$", summary, re.M)
    require(len(matches) == 1, "missing/duplicated banked comparison summary")
    counts = list(map(int, matches[0]))
    require(counts[:4] == [6, 6 * geometry.vocabulary,
                          6 * geometry.kv_dimension, 6 * geometry.kv_dimension] and
            counts[4] > 0 and counts[5] > 0, "incomplete memory frame/KV/request comparisons")
    bank_rows = [tuple(map(int, row)) for row in
                 re.findall(r"^BANK bank=(\d+) requests=(\d+)$", summary, re.M)]
    require(len(bank_rows) == identity["banks"] and
            [bank for bank, count in bank_rows] == list(range(identity["banks"])) and
            all(count > 0 for bank, count in bank_rows) and
            sum(count for bank, count in bank_rows) == counts[4],
            "missing/duplicated bank coverage or request conservation")
    reorder = re.findall(r"^REORDER responses=(\d+)$", summary, re.M)
    require(len(reorder) == 1 and int(reorder[0]) == result.get("reordered_responses"),
            "missing/corrupted response reorder comparison")
    require(not (identity["banks"] > 1 and identity["queue_depth"] > 1) or
            int(reorder[0]) > 0, "required bank reordering not observed")


def validate_memory_matrix(result):
    cases = result.get("cases", [])
    require(len(cases) == 6, "incomplete six-case memory matrix")
    for index, case in enumerate(cases):
        validate_memory_case(case, index)
    require(result.get("compared_frames") == 36 and
            result.get("compared_logit_words") == 288,
            "incomplete final memory comparison totals")


def validate_memory_receipt(run, path, receipt, result):
    from integration import generate_images
    from memory_checks import banked_bench

    bench = path.parent / "banked_top_tb.sv"
    require(bench.is_file() and bench.read_text() == banked_bench(),
            "retained memory bench differs from current computational bench")
    geometry = Geometry(**result["geometry"])
    parameters = {"H": geometry.hidden, "I": geometry.intermediate,
                  "QH": geometry.q_heads, "KH": geometry.kv_heads,
                  "D": geometry.head_dim, "V": geometry.vocabulary,
                  "M": geometry.max_sequence, "N": 6, "B": result["banks"],
                  "QUEUE": result["queue_depth"]}
    sources = [relative(p) for p in sorted((ROOT / "rtl").glob("anvil_qn1_*.sv"))]
    objects = path.parent / "obj-banked-top"
    unroll = (["--unroll-count", "256", "--unroll-stmts", "100000"]
              if result["banks"] * result["queue_depth"] >= 128 else [])
    expected_compile = [
        "verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2", *unroll,
        "--top-module", "top_tb", *[f"-G{k}={v}" for k, v in parameters.items()],
        "--Mdir", relative(objects), "-o", "simulate", *sources, relative(bench)]
    commands = [c for c in receipt["commands"]
                if not Path(c["stdout"]).name.startswith("version-")]
    expected_simulation = [relative(objects / "simulate"),
                           f"+images={relative(path.parent / 'checkpoint-images')}"]
    require(len(commands) == 2 and
            [c["argv"] for c in commands] == [expected_compile, expected_simulation] and
            all(c["cwd"] == "." for c in commands), "memory build/simulation argv mismatch")
    output = (ROOT / commands[1]["stdout"]).read_text()
    require(output[-1500:] == result["raw_summary"] and
            not any(marker in output for marker in
                    ("$fatal", "%Error", "Assertion failed", "Warning: $readmem")),
            "retained memory summary does not match successful raw simulation")
    # Regenerate every stimulus/expected tensor, not just tokens or a DUT-output hash.
    with tempfile.TemporaryDirectory(prefix="official-image-", dir=run.path) as directory:
        images = Path(directory) / "checkpoint-images"
        records = generate_images(images, geometry, result["seed"], 6)
        expected = {f"checkpoint-images/{file.name}":
                    hashlib.sha256(file.read_bytes()).hexdigest()
                    for file in images.glob("*.hex")}
    require(records == result["transactions"] and expected and
            receipt.get("transient_image_sha256") == expected,
            "retained memory image/oracle hashes or sequential records differ")


def memory_case(run, index):
    from memory_checks import run_banked_top

    identity = memory_identity(index)
    return component(
        run, f"memory-matrix-case{index:02d}",
        lambda child: run_banked_top(child, Geometry(**identity["geometry"]),
                                     seed=identity["seed"], banks=identity["banks"],
                                     queue=identity["queue_depth"]),
        inputs=(*MODEL, "tests/memory_checks.py"),
        parameters=identity, tools=TOOLS,
        validate=lambda result: validate_memory_case(result, index),
        equivalence=orchestration_equivalence, validate_retained=validate_memory_receipt)


def run_resume_checker(run):
    """Read-only retained-case assessment plus in-memory negative counterexamples."""
    from behavior_suite import SPECULATION, validate_core
    from checker_checks import rejection

    cases = []
    rejections = []
    for index, name in enumerate((
            "evidence/l1-memory-matrix-case00-20261103T101948Z-51f863e8/receipt.json",
            "evidence/l1-memory-matrix-case01-20261103T102509Z-51b556ed/receipt.json")):
        path = ROOT / name
        assessment, result = assess(
            run, path, (*MODEL, "tests/memory_checks.py"), memory_identity(index), TOOLS,
            equivalence=orchestration_equivalence)
        require(assessment["applicable"], f"retained case inapplicable: {assessment['reasons']}")
        validate_memory_case(result, index)
        receipt = json.loads(path.read_text())
        validate_memory_receipt(run, path, receipt, result)
        cases.append(assessment)
        for field in ("geometry", "seed", "banks", "queue_depth", "transactions",
                      "reordered_responses", "raw_summary"):
            broken = copy.deepcopy(result)
            broken[field] = None if field != "raw_summary" else ""
            rejections.append(rejection(
                lambda broken=broken: validate_memory_case(broken, index),
                f"memory-{index}:changed-{field}"))
        for field in ("transient_image_sha256", "commands"):
            broken = copy.deepcopy(receipt)
            broken[field] = {} if field == "transient_image_sha256" else []
            rejections.append(rejection(
                lambda broken=broken: validate_memory_receipt(run, path, broken, result),
                f"memory-{index}:changed-{field}"))
        rejections.append(rejection(
            lambda: validate_memory_case(result, 1 - index),
            f"memory-{index}:wrong-case"))
    core_path = ROOT / "evidence/l1-behavior-core-20261103T094917Z-c0f468fa/receipt.json"
    core, result = assess(run, core_path, (*SPECULATION, "tests/behavior_checks.py"),
                          {"case_count": 15, "compared_frames": 90,
                           "compared_logit_words": 720}, TOOLS)
    require(core["applicable"], f"saved core inapplicable: {core['reasons']}")
    validate_core(result)
    for index in range(15):
        broken = copy.deepcopy(result)
        del broken["cases"][index]
        rejections.append(rejection(lambda: validate_core(broken), f"core:missing-{index}"))
    rejections.append(rejection(
        lambda: validate_memory_matrix({"cases": []}), "memory:partial-matrix"))
    return {"scope": "checker/applicability diagnostics, not mandatory behavior acceptance",
            "memory_cases": cases, "behavior_core": core,
            "rejected_counterexamples": rejections}
