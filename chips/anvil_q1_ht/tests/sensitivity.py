"""Disposable compile-then-functional-rejection tests; originals are never edited."""

import hashlib
from pathlib import Path
import shutil

from experiments import dequant, dma_probe, kv_probe, tensor, top_probe


def run_sensitivity(parent, seed):
    cases = (
        ("awq_permutation", "anvil_q1_ht_00_numeric_pkg.sv",
         "awq_shift = {lane[0], lane[2:1], 2'b00};",
         "awq_shift = {lane, 2'b00};",
         lambda run: dequant(run, seed), "DEQUANT_MISMATCH"),
        ("negative_tie", "anvil_q1_ht_mac_lane.sv",
         "value[15:0] > 16'h8000", "value[15:0] >= 16'h8000",
         lambda run: tensor(run, seed), "TENSOR_MISMATCH"),
        ("lane_17_sign", "anvil_q1_ht_tensor_array.sv",
         ".in_weight_q16(in_weight_q16[37*INDEX+:37])",
         ".in_weight_q16(INDEX == 17 ? -$signed(in_weight_q16[37*INDEX+:37]) : "
         "$signed(in_weight_q16[37*INDEX+:37]))",
         lambda run: tensor(run, seed), "TENSOR_MISMATCH"),
        ("response_cursor", "anvil_q1_ht_weight_dma.sv",
         "cursor <= {cursor[33:6] + 28'd1, 6'b0};",
         "cursor <= {cursor[33:6] + 28'd2, 6'b0};",
         lambda run: dma_probe(run, 1), "DMA_DATA_MISMATCH"),
        ("kv_tag_alias", "anvil_q1_ht_kv_window.sv",
         "mask_data != 0 && tag_data == position && selected_valid",
         "mask_data != 0 && selected_valid",
         lambda run: kv_probe(run, 1), "KV_DATA_OR_TAG_MISMATCH"),
        ("final_logit_stall", "anvil_q1_ht_decoder.sv",
         "wire final_transfer = logit_valid && logit_ready && logit_index == VOCAB_SIZE-1;",
         "wire final_transfer = logit_valid && logit_index == VOCAB_SIZE-1;",
         lambda run: top_probe(run, "AWQ", seed), "TOP_STALLED_LOGIT_CHANGED"),
    )
    for name, filename, before, after, experiment, rejection in cases:
        trial = parent.__class__("mutation-" + name,
                                 source_root=parent.folder / "sources")
        trial.default_simulator = "verilator"
        trial.rtl_root = trial.folder / "mutated-rtl"
        trial.rtl_root.mkdir()
        for source in (trial.folder / "sources/rtl").glob("*.sv"):
            shutil.copyfile(source, trial.rtl_root / source.name)
        target = trial.rtl_root / filename
        original = target.read_text()
        if original.count(before) != 1:
            raise AssertionError(f"mutation no longer identifies exactly one site: {name}")
        target.write_text(original.replace(before, after))
        trial.record["mutation"] = {
            "name": name, "source": "rtl/" + filename, "before": before, "after": after,
            "mutated_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "parent_receipt": parent.relative(parent.folder / "receipt.json"),
            "expected_rejection": rejection,
        }
        trial.record["tool_version_receipt"] = parent.relative(parent.folder / "receipt.json")
        trial.flush()
        try:
            experiment(trial)
        except RuntimeError as exc:
            commands = trial.record["commands"]
            last = commands[-1]
            output = (parent.folder.parents[2] / last["stdout"]).read_text()
            compiled = any(command["exit_code"] == 0 and
                           command["argv"][:2] == ["verilator", "--binary"]
                           for command in commands)
            if (Path(last["argv"][0]).parts[-2:] != ("compiled", "Vtb") or
                    last["exit_code"] not in (1, -6) or last["timed_out"]
                    or not last.get("process_settled") or not compiled or rejection not in output):
                trial.finish("failed", f"Not a qualified functional defect rejection: {exc}")
                raise AssertionError(f"unqualified mutation outcome: {name}") from exc
            trial.finish("defect_rejected", f"Compiled, then public functional assertion {rejection} rejected it.")
        else:
            trial.finish("failed", "Deliberate defect escaped the functional oracle.")
            raise AssertionError(f"undetected defect: {name}")
        parent.record["observations"].append({
            "mutation": name, "compiled": True, "functional_rejection": rejection,
            "receipt": parent.relative(trial.folder / "receipt.json")})
        parent.flush()
