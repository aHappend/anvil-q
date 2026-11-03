"""Observable defect sensitivity on disposable copies; never edits source RTL."""

import shutil
import uuid

from evidence import ROOT, ExecutionFailure, digest, relative, write_json
import leaf_checks


MUTATIONS = (
    ("multiply-rounding", "fp16_mul",
     "else data2 <= rounded_product;",
     "else data2 <= rounded_product ^ 32'h00000001;",
     leaf_checks.pipelines, "MUL16"),
    ("awq-lane-order", "dequant",
     "awq_shift(in_lane)", "{in_lane, 2'b00}",
     leaf_checks.dequant, "AWQ"),
    ("slot-broadcast", "tile_batch_mac",
     ".activation(in_activation[16*slot+:16])", ".activation(in_activation[0+:16])",
     leaf_checks.mac, "MAC_NUMERIC"),
    ("sparse-cross-slot", "sparse_dma",
     "if (slots[slot]) begin", "if (slots[slot] && slot == 0) begin",
     leaf_checks.sparse, ("SPARSE_DECISION", "DMA_REQUEST")),
    ("causal-sibling-leakage", "tree_mask",
     "next_ancestors[4*node+node] = 1;",
     "next_ancestors[4*node+:4] = (4'b0001 << count) - 1'b1;",
     leaf_checks.masks, "CAUSAL_MASK"),
    ("speculative-mismatch", "spec_verifier",
     "drafts[32*child+:32] == current_target",
     "drafts[32*child+:32] != current_target",
     leaf_checks.verifier, "TREE_WALK"),
)


def run(directory, selected=None):
    results = []
    for name, module, original, replacement, checker, marker in MUTATIONS:
        if selected is not None and name not in selected:
            continue
        work = directory / f"{name}-{uuid.uuid4().hex[:8]}"
        work.mkdir(exist_ok=False)
        baseline = work / f"baseline-{uuid.uuid4().hex[:8]}"
        baseline.mkdir(exist_ok=False)
        baseline_result = checker(baseline, "verilator")
        copied = work / "rtl"
        shutil.copytree(ROOT / "rtl", copied)
        source = copied / f"anvil_q1_ht2_{module}.sv"
        text = source.read_text()
        if text.count(original) != 1:
            raise AssertionError(f"mutation target not unique: {name}")
        before = digest(source)
        source.write_text(text.replace(original, replacement))
        record = {"name": name, "copied_source": relative(source), "before_sha256": before,
                  "after_sha256": digest(source), "expected_assertion": marker,
                  "compile_failure_counts_as_detection": False,
                  "unmutated_comparison": baseline_result}
        try:
            checker(work, "verilator", copied)
        except ExecutionFailure as exc:
            record.update(receipt=relative(exc.directory / "receipt.json"),
                          exit_code=exc.receipt["exit_code"])
            stdout = (exc.directory / "stdout.txt").read_text()
            stderr = (exc.directory / "stderr.txt").read_text()
            record["detected"] = (
                "-simulate-" in exc.directory.name and not exc.receipt["timed_out"]
                and any(item in stdout + stderr
                        for item in (marker if isinstance(marker, tuple) else (marker,)))
            )
            write_json(work / "mutation.json", record)
            if not record["detected"]:
                raise AssertionError(f"mutation not numerically/protocol detected: {name}") from exc
        else:
            record["detected"] = False
            write_json(work / "mutation.json", record)
            raise AssertionError(f"mutated RTL survived oracle: {name}")
        results.append(record)
    if len(results) != (len(selected) if selected is not None else 6) or not all(
        item["detected"] for item in results
    ):
        raise AssertionError("incomplete mutation matrix")
    return results
