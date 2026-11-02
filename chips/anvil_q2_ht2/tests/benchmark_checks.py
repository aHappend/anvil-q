#!/usr/bin/env python3
"""No-claim unit tests for benchmark corpus, provenance checks and accounting."""

import argparse
from collections import defaultdict
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmarks import (BOUNDARY, DOMAINS, PromptAccount, cell_key, cells, corpus,
                        digest, draft, fidelity, greedy, integer, portable_path,
                        performance_thresholds, prerequisites, read_export,
                        selected_path, summarize, validate_asset)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = None


def begin(cell=None, expected=None):
    return {
        "type": "begin", "prompt_id": "dialogue-00",
        "cell": cell or {"engine": "ht2", "k": 1, "mode": "bf16-dense", "kv": "bf16"},
        "boundary": BOUNDARY, "measured_clock_hz": 100000000,
        "sequence_position": 0,
        "prefill_start_ns": 10, "prefill_end_ns": 110,
        "decode_start_ns": 110, "decode_end_ns": 310,
        "greedy_ids": expected or [0, 1],
    }


def end(ids=None):
    return {"type": "end", "output_ids": ids or [0, 1], "ended_eos": True,
            "fabric_beats": {"prefill": {"read": 1, "write": 0},
                             "decode": {"read": 5, "write": 2}}}


def add_traffic(account):
    for phase, direction, category, count in [
            ("prefill", "read", "weights", 1), ("decode", "read", "weights", 2),
            ("decode", "read", "scales", 1), ("decode", "read", "zero_points", 1),
            ("decode", "read", "control", 1), ("decode", "write", "kv", 2)]:
        account.ddr({"phase": phase, "direction": direction,
                     "category": category, "accepted_beats": count})


def add_vectors(account, next_ids=None):
    next_ids = next_ids or [1] * account.cell["k"]
    for slot in range(account.cell["k"]):
        for layer in range(29):
            vector = [0x3f800000] * account.hidden_size if layer < 28 else [
                0x40000000 if i == next_ids[slot] else 0x3f800000
                for i in range(account.vocabulary)]
            account.vector({"slot": slot, "layer": layer, "actual": vector,
                            "reference": vector, "original_bf16": vector})


def add_batch(account, start=110, finish=210, **overrides):
    ids, parents = draft(account.begin["prompt_id"], account.prefix, account.current,
                         account.cell["k"], account.vocabulary)
    item = {"ids": ids, "parents": parents, "accepted": 1, "mask": 1,
            "next_token": 1, "position": len(account.prefix)+1,
            "accept_ns": start, "commit_ns": finish}
    item.update(overrides)
    account.batch(item)


def completed_account():
    account = PromptAccount(begin(), 4, [1], hidden_size=8)
    add_traffic(account)
    add_vectors(account)
    add_batch(account)
    add_vectors(account)
    add_batch(account, 220, 310)
    return account


class CorpusAndAssetChecks(unittest.TestCase):
    def quantized_binding_fixture(self):
        image = FIXTURES / ("official-image-bindings-" +
                            hashlib.sha256(self.id().encode()).hexdigest()[:8])
        image.mkdir()
        manifest = {"model_provenance": {"revision": "synthetic-only"},
                    "checkpoint_shards": [{"path": "synthetic.bf16", "sha256": "1"*64}],
                    "assets": {"config": {"path": "synthetic.json", "sha256": "2"*64}}}
        files = []
        for width in (2, 4):
            for suffix in ("weights.bin", "zeros.bin", "scales.bf16"):
                path = image / f"w{width}-{suffix}"
                path.write_bytes(b"\x00")
                files.append({"path": str(path.relative_to(FIXTURES)), "sha256": digest(path)})
        from quantized_checkpoint import POLICY
        data = {"kind": "derived-official-quantized-inputs", "policy": POLICY,
                "source": manifest["checkpoint_shards"][0],
                "config": manifest["assets"]["config"],
                "upstream": manifest["model_provenance"], "files": files}
        path = image / "manifest.json"
        path.write_text(json.dumps(data))
        manifest["quantized_weight_inputs"] = [
            {"path": str(path.relative_to(FIXTURES)), "sha256": digest(path)}, *files]
        return manifest, image, data

    def test_complete_quantized_image_binding(self):
        from quantized_checkpoint import benchmark_image
        manifest, image, _ = self.quantized_binding_fixture()
        self.assertEqual(benchmark_image(FIXTURES, manifest), image)

    def test_quantized_image_missing_byte_file(self):
        from quantized_checkpoint import benchmark_image
        manifest, _, _ = self.quantized_binding_fixture()
        manifest["quantized_weight_inputs"].pop()
        with self.assertRaisesRegex(ValueError, "six byte images"):
            benchmark_image(FIXTURES, manifest)

    def test_quantized_image_substituted_digest(self):
        from quantized_checkpoint import benchmark_image
        manifest, _, _ = self.quantized_binding_fixture()
        manifest["quantized_weight_inputs"][-1] = {
            **manifest["quantized_weight_inputs"][-1], "sha256": "3"*64}
        with self.assertRaisesRegex(ValueError, "completely/immutably bound"):
            benchmark_image(FIXTURES, manifest)

    def test_quantized_image_wrong_official_source(self):
        from quantized_checkpoint import benchmark_image
        manifest, _, _ = self.quantized_binding_fixture()
        manifest["checkpoint_shards"] = [{"path": "other.bf16", "sha256": "4"*64}]
        with self.assertRaisesRegex(ValueError, "bound official inputs"):
            benchmark_image(FIXTURES, manifest)

    def test_frozen_corpus(self):
        manifest = json.loads((ROOT / "tests/benchmark_manifest.json").read_text())
        prompts = corpus(ROOT, manifest)
        self.assertEqual(len(prompts), 100)
        self.assertEqual({d: sum(p["domain"] == d for p in prompts.values())
                          for d in DOMAINS}, dict.fromkeys(DOMAINS, 20))

    def test_matrix_has_no_omissions(self):
        matrix = cells()
        self.assertEqual(len(matrix), 50)
        self.assertEqual(len({cell_key(cell) for cell in matrix}), 50)
        self.assertEqual(sum(cell["engine"] == "ht2" for cell in matrix), 48)
        self.assertEqual(len(matrix)*len(DOMAINS), 250)

    def test_immutable_asset_and_tamper(self):
        path = FIXTURES / "asset.json"
        path.write_text('{"no_claim":true}\n')
        binding = {"path": "asset.json", "sha256": digest(path)}
        self.assertEqual(validate_asset(FIXTURES, binding), path)
        path.write_text('{"no_claim":false}\n')
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            validate_asset(FIXTURES, binding)

    def test_null_hash_not_wildcard(self):
        path = FIXTURES / "unpinned.txt"
        path.write_text("test-only\n")
        with self.assertRaisesRegex(ValueError, "missing immutable SHA-256"):
            validate_asset(FIXTURES, {"path": path.name, "sha256": None})

    def test_missing_asset_reports_hash_and_file(self):
        with self.assertRaises(ValueError) as failure:
            validate_asset(FIXTURES, {"path": "missing", "sha256": None})
        self.assertIn("missing immutable SHA-256", str(failure.exception))
        self.assertIn("missing file", str(failure.exception))

    def test_path_escape_and_runtime_metadata_rejected(self):
        for path in ("/outside", "../outside", ".vulcan/state", ".git/config",
                     ".tooling/tool", "VULCAN/report", "a\\b", "C:/asset"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                portable_path(FIXTURES, path)

    def test_symlink_escape_rejected(self):
        link = FIXTURES / "outside-link"
        link.symlink_to(FIXTURES.parent)
        with self.assertRaisesRegex(ValueError, "escapes project"):
            portable_path(FIXTURES, "outside-link/asset")

    def test_missing_groups_are_all_reported(self):
        manifest = json.loads((ROOT / "tests/benchmark_manifest.json").read_text())
        _, errors = prerequisites(FIXTURES, manifest)
        joined = "\n".join(errors)
        for name in ("config", "tokenizer", "tokenizer_config", "checkpoint_index",
                     "generational_handoff", "checkpoint_shards", "quantized_weight_inputs",
                     "q2_fp_sources", "independent_reference_sources", "observations"):
            self.assertIn(name, joined)

    def test_draft_deterministic_and_target_independent(self):
        args = ("logic-03", [5, 6, 7], 8, 4, 151936)
        first = draft(*args)
        self.assertEqual(first, draft(*args))
        self.assertEqual(first[0][0], 8)
        self.assertTrue(all(0 <= p < i for i, p in enumerate(first[1][1:], 1)))
        # Freeze the actual serialized input convention, not a salted host hash().
        seed = b'["sha256-prefix-v1","logic-03",[5,6,7]]'
        expected = int.from_bytes(hashlib.sha256(seed+b"\x01").digest()[:8], "little") % 151936
        self.assertEqual(first[0][1], expected)
        self.assertNotEqual(first, draft("logic-03", [5, 6], 8, 4, 151936))

    def test_draft_legal_widths_and_singleton_vocab(self):
        for width in (1, 2, 4):
            ids, parents = draft("dialogue-00", [], 0, width, 1)
            self.assertEqual(ids, [0]*width)
            self.assertEqual(len(parents), width)
        with self.assertRaises(ValueError):
            draft("dialogue-00", [], 0, 3, 1)


class NumericalAndTreeChecks(unittest.TestCase):
    def test_exact_metrics_and_zero_vector_convention(self):
        self.assertEqual(fidelity([0x3f800000, 0x40000000],
                                  [0x3f800000, 0x40000000]), (Decimal(0), Decimal(1)))
        self.assertEqual(fidelity([0, 0x80000000], [0, 0]), (Decimal(0), Decimal(1)))
        self.assertEqual(fidelity([0x3f800000], [0])[0], Decimal("Infinity"))

    def test_sign_error_is_not_hidden_by_normalization(self):
        error, cosine = fidelity([0xbf800000], [0x3f800000])
        self.assertEqual(error, 2)
        self.assertEqual(cosine, -1)

    def test_nonfinite_and_empty_are_rejected(self):
        for vector in ([], [0x7f800000], [0x7fc00000], [0xff800000]):
            with self.subTest(vector=vector), self.assertRaises(ValueError):
                fidelity(vector, vector)

    def test_bit_input_is_not_host_float_or_boolean(self):
        for value in (True, 1.0, -1, 1 << 32):
            with self.subTest(value=value), self.assertRaises(ValueError):
                fidelity([value], [0])
        with self.assertRaises(ValueError):
            integer(True, "counter")

    def test_argmax_ties_choose_smallest_id(self):
        self.assertEqual(greedy([0x3f800000, 0x40000000, 0x40000000]), 1)

    def test_branch_and_duplicate_choose_correct_path(self):
        self.assertEqual(selected_path([10, 11, 12, 13], [0, 0, 0, 2], [12, 8, 13, 20]),
                         ([0, 2, 3], 20))
        self.assertEqual(selected_path([10, 11, 11, 13], [0, 0, 0, 2], [11, 9, 13, 20]),
                         ([0, 1], 9))

    def test_invalid_parent_rejected(self):
        with self.assertRaises(ValueError):
            selected_path([0, 1, 2, 3], [0, 0, 3, 2], [1, 2, 3, 4])


class AccountingChecks(unittest.TestCase):
    def test_completed_prompt_retains_greedy_identity(self):
        result = completed_account().finish(end())
        expected = hashlib.sha256(b"[0,1]").hexdigest()
        self.assertEqual(result["output_ids_sha256"], expected)
        self.assertEqual(result["sequence_position"], 0)

    def test_cross_width_and_sparse_greedy_equivalence(self):
        from benchmarks import validate_greedy_equivalence
        grouped = defaultdict(dict)
        for cell in cells():
            if cell["engine"] != "ht2":
                continue
            row = completed_account().finish(end())
            # Different precisions/KV policies may legitimately produce different IDs.
            precision = cell["mode"].split("-")[0]
            row["output_ids_sha256"] = hashlib.sha256(
                (precision + cell["kv"]).encode()).hexdigest()
            grouped[cell_key(cell)]["dialogue-00"] = row
        self.assertEqual(validate_greedy_equivalence(grouped), [])
        for changed in ("output_ids_sha256", "tokens", "sequence_position"):
            for width, mode in ((2, "bf16-dense"), (4, "w2-sparse"),
                                (1, "fp16-sparse")):
                with self.subTest(field=changed, width=width, mode=mode):
                    broken = copy.deepcopy(grouped)
                    key = ("ht2", width, mode, "bf16")
                    broken[key]["dialogue-00"][changed] = (
                        "0"*64 if changed == "output_ids_sha256" else 7)
                    self.assertTrue(validate_greedy_equivalence(broken))

    def test_self_consistent_but_different_greedy_exports_rejected(self):
        from benchmarks import validate_greedy_equivalence
        dense = completed_account().finish(end())
        sparse_cell = {"engine": "ht2", "k": 1, "mode": "bf16-sparse", "kv": "bf16"}
        account = PromptAccount(begin(sparse_cell, [2, 1]), 4, [1], hidden_size=8)
        add_traffic(account)
        add_vectors(account)
        add_batch(account)
        add_vectors(account)
        add_batch(account, 220, 310)
        sparse = account.finish(end([2, 1]))
        grouped = {("ht2", 1, "bf16-dense", "bf16"): {"dialogue-00": dense},
                   cell_key(sparse_cell): {"dialogue-00": sparse}}
        errors = validate_greedy_equivalence(grouped)
        self.assertEqual(len(errors), 1)
        self.assertIn("greedy sequence differs", errors[0])
        del grouped[("ht2", 1, "bf16-dense", "bf16")]
        self.assertIn("missing K=1 dense", validate_greedy_equivalence(grouped)[0])

    def test_complete_comparisons_and_actual_traffic(self):
        summary = completed_account().finish(end())
        self.assertEqual(summary["tokens"], 2)
        self.assertEqual(summary["decode_ns"], 200)
        self.assertEqual(summary["prefill_ns"], 100)
        self.assertEqual(summary["compared_vectors"], 58)
        self.assertEqual(summary["acceptance"], {1: 2})
        self.assertEqual(summary["ddr_bytes"], {"prefill": 64, "decode": 448})
        self.assertEqual(summary["ddr_classes"]["decode/read/scales"], 64)
        self.assertEqual(summary["ddr_classes"]["decode/write/kv"], 128)

    def test_metadata_omission_is_detected(self):
        account = completed_account()
        account.beats["decode", "read"] -= 1
        with self.assertRaisesRegex(ValueError, "unaccounted decode read"):
            account.finish(end())

    def test_pointer_defect_is_detected(self):
        account = PromptAccount(begin(), 4, [1], hidden_size=8)
        add_vectors(account)
        with self.assertRaisesRegex(ValueError, "pointer"):
            add_batch(account, position=4)

    def test_early_or_missing_layer_publication_is_detected(self):
        account = PromptAccount(begin(), 4, [1], hidden_size=8)
        with self.assertRaisesRegex(ValueError, "missing production"):
            add_batch(account)

    def test_numerical_defect_is_detected(self):
        account = PromptAccount(begin(), 4, [1], hidden_size=8)
        with self.assertRaisesRegex(ValueError, "fidelity"):
            account.vector({"slot": 0, "layer": 0, "actual": [0xbf800000]*8,
                            "reference": [0x3f800000]*8})

    def test_duplicate_and_partial_vectors_are_rejected(self):
        account = PromptAccount(begin(), 4, [1], hidden_size=8)
        item = {"slot": 0, "layer": 0, "actual": [0x3f800000]*8,
                "reference": [0x3f800000]*8}
        account.vector(item)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            account.vector(item)
        with self.assertRaisesRegex(ValueError, "partial"):
            account.vector({**item, "layer": 28})

    def test_short_non_eos_generation_is_rejected(self):
        account = completed_account()
        account.eos_ids = [3]
        with self.assertRaisesRegex(ValueError, "fewer than 128"):
            account.finish({**end(), "ended_eos": False})

    def test_eos_marker_and_greedy_mismatch_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "EOS marker"):
            completed_account().finish({**end(), "ended_eos": False})
        with self.assertRaisesRegex(ValueError, "greedy sequence"):
            completed_account().finish(end([0, 2]))

    def test_decode_overhead_is_included(self):
        account = PromptAccount(begin(), 4, [1], hidden_size=8)
        add_vectors(account)
        with self.assertRaisesRegex(ValueError, "initial draft overhead"):
            add_batch(account, start=111)

    def test_final_commit_is_measured_endpoint(self):
        account = completed_account()
        account.begin["decode_end_ns"] += 1
        with self.assertRaisesRegex(ValueError, "endpoint"):
            account.finish(end())

    def test_baseline_requires_committed_tokens_and_same_boundary(self):
        cell = {"engine": "anvil-q2-fp", "k": 1, "mode": "baseline", "kv": "baseline"}
        account = PromptAccount(begin(cell), 4, [1])
        add_traffic(account)
        account.token({"id": 0, "commit_ns": 210})
        account.token({"id": 1, "commit_ns": 310})
        self.assertEqual(account.finish(end())["tokens"], 2)
        broken = begin(cell)
        broken["boundary"] = "kernel-only"
        with self.assertRaisesRegex(ValueError, "boundary"):
            PromptAccount(broken, 4, [1])

    def test_quantization_error_separately_reported(self):
        cell = {"engine": "ht2", "k": 1, "mode": "w2-sparse", "kv": "int8"}
        account = PromptAccount(begin(cell), 4, [1], hidden_size=8)
        for layer in range(28):
            account.vector({"slot": 0, "layer": layer,
                            "actual": [0x3f800000]*8, "reference": [0x3f800000]*8})
        account.vector({"slot": 0, "layer": 28,
                        "actual": [0, 0x3f800000, 0, 0],
                        "reference": [0, 0x3f800000, 0, 0],
                        "original_bf16": [0, 0x40000000, 0, 0]})
        self.assertEqual([tuple(Decimal(value) for value in pair)
                          for pair in account.original_quality], [(Decimal("0.5"), Decimal(1))])

    def test_aggregate_is_token_weighted_not_mean_of_tpm(self):
        first = completed_account().finish(end())
        second = copy.deepcopy(first)
        second.update(tokens=6, decode_ns=600)
        combined = summarize([first, second])
        self.assertEqual(combined["tokens"], 8)
        self.assertEqual(Decimal(combined["decode_tpm"]), Decimal(600000000))
        self.assertEqual(Decimal(combined["decode_ddr_bytes_per_token"]), Decimal(112))

    def test_empty_aggregate_is_not_success(self):
        with self.assertRaisesRegex(ValueError, "empty benchmark"):
            summarize([])

    def test_exact_performance_thresholds(self):
        performance_thresholds("3500", "0.5000000001")
        with self.assertRaisesRegex(ValueError, "below 3500"):
            performance_thresholds("3499.999999999", "0.75")
        with self.assertRaisesRegex(ValueError, "greater than 50"):
            performance_thresholds("7000", "0.5")

    def test_negative_or_boolean_beats_rejected(self):
        for count in (-1, True):
            with self.subTest(count=count), self.assertRaises(ValueError):
                completed_account().ddr({"phase": "decode", "direction": "read",
                                         "category": "weights", "accepted_beats": count})


class ExportChecks(unittest.TestCase):
    header = {"scope": "no-claim unit fixture, not a production hardware export"}

    def read_rows(self, rows, header=None, grouped=None):
        path = FIXTURES / (self._testMethodName + ".jsonl")
        path.write_text("".join(json.dumps(row)+"\n" for row in rows))
        grouped = grouped if grouped is not None else defaultdict(dict)
        read_export(path, header or self.header, {"dialogue-00": {"domain": "dialogue"}},
                    4, [1], grouped, hidden_size=8)
        return grouped

    def baseline_rows(self):
        cell = {"engine": "anvil-q2-ht", "k": 1, "mode": "baseline", "kv": "baseline"}
        start = begin(cell)
        traffic = [
            {"type": "ddr", "phase": "prefill", "direction": "read",
             "category": "weights", "accepted_beats": 1},
            {"type": "ddr", "phase": "decode", "direction": "read",
             "category": "weights", "accepted_beats": 5},
            {"type": "ddr", "phase": "decode", "direction": "write",
             "category": "kv", "accepted_beats": 2}]
        return [self.header, start, *traffic, {"type": "token", "id": 0, "commit_ns": 210},
                {"type": "token", "id": 1, "commit_ns": 310}, end()]

    def test_complete_stream(self):
        rows = self.baseline_rows()
        grouped = self.read_rows(rows)
        result = grouped[cell_key(rows[1]["cell"])]["dialogue-00"]
        self.assertEqual(result["tokens"], 2)
        self.assertEqual(result["ddr_bytes"]["decode"], 448)

    def test_stale_header_rejected(self):
        with self.assertRaisesRegex(ValueError, "provenance/header"):
            self.read_rows(self.baseline_rows(), header={"stale": True})

    def test_empty_export_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty observation"):
            self.read_rows([])

    def test_truncated_export_rejected(self):
        with self.assertRaisesRegex(ValueError, "truncated"):
            self.read_rows(self.baseline_rows()[:-1])

    def test_unknown_record_rejected(self):
        rows = self.baseline_rows()
        rows.insert(-1, {"type": "ignored-error"})
        with self.assertRaisesRegex(ValueError, "unknown observation"):
            self.read_rows(rows)

    def test_orphan_record_rejected(self):
        with self.assertRaisesRegex(ValueError, "orphan"):
            self.read_rows([self.header, {"type": "token", "id": 0}])

    def test_duplicate_prompt_rejected(self):
        rows = self.baseline_rows()
        with self.assertRaisesRegex(ValueError, "duplicate cell/prompt"):
            self.read_rows(rows + rows[1:])

    def test_overlapping_prompts_rejected(self):
        rows = self.baseline_rows()
        rows.insert(2, rows[1])
        with self.assertRaisesRegex(ValueError, "overlapping"):
            self.read_rows(rows)


def main():
    global FIXTURES
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", required=True,
                        help="new project-relative directory for retained no-claim unit fixtures")
    args = parser.parse_args()
    FIXTURES = portable_path(ROOT, args.fixtures)
    FIXTURES.mkdir(parents=True, exist_ok=False)
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    print(json.dumps({"scope": "accounting-unit-tests-only; no production observations",
                      "tests": result.testsRun, "failures": len(result.failures),
                      "errors": len(result.errors)}))
    return 0 if result.wasSuccessful() and result.testsRun > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
