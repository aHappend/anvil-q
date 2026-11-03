"""Frozen redistributable prompts and measurement rules (before collection)."""

import hashlib
import json


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha256(value):
    return hashlib.sha256(canonical(value)).hexdigest()


_RETRIEVAL = "\n".join(
    f"Record {i:04d}: storage bin contains item-{(i * 73 + 19) % 997:03d}."
    for i in range(512))

CASES = (
    {"id": "facts-1", "domain": "factual",
     "prompt": "Explain why Earth has seasons. Distinguish axial tilt from orbital distance."},
    {"id": "facts-2", "domain": "factual",
     "prompt": "Give three differences between a compiler and an interpreter, with examples."},
    {"id": "math-1", "domain": "mathematics",
     "prompt": "A tank fills at 7 liters per minute and drains at 3. It starts with 11 liters. "
               "How much is present after 13 minutes? Explain each step."},
    {"id": "math-2", "domain": "mathematics",
     "prompt": "Find the smallest positive integer divisible by 8, 12, and 15. Show the factorization."},
    {"id": "code-1", "domain": "code",
     "prompt": "Write Python code to merge two sorted lists without sorting their concatenation. "
               "Include a short test."},
    {"id": "code-2", "domain": "code",
     "prompt": "Write a Python function checking balanced parentheses, brackets and braces. "
               "Explain the stack invariant."},
    {"id": "multilingual-1", "domain": "multilingual",
     "prompt": "Responde en espa\u00f1ol: explica tres formas de ahorrar agua en casa."},
    {"id": "multilingual-2", "domain": "multilingual",
     "prompt": "\u7528\u4e2d\u6587\u89e3\u91ca\u4e8c\u5206\u67e5\u627e\uff0c"
               "\u5e76\u7ed9\u51fa\u4e00\u4e2a\u5c0f\u4f8b\u5b50\u3002"},
    {"id": "retrieval-1", "domain": "long_context",
     "prompt": _RETRIEVAL + "\nWhich item is in record 0371? Quote that record and explain how you found it."},
    {"id": "retrieval-2", "domain": "long_context",
     "prompt": _RETRIEVAL + "\nCompare the items in records 0047 and 0463. Quote both records."},
)

DEFAULT_GEOMETRY = {
    "NUM_LAYERS": 24, "HIDDEN_SIZE": 896, "INTERMEDIATE_SIZE": 4864,
    "NUM_Q_HEADS": 14, "NUM_KV_HEADS": 2, "HEAD_DIM": 64, "GROUP_SIZE": 128,
    "AWQ_BITS": 4, "VOCAB_SIZE": 151936, "MAX_SEQ_LEN": 32768,
    "LANES": 64, "BANKS": 8, "LANES_PER_BANK": 8, "DDR_WIDTH": 512,
    "TILE_BEATS": 256, "KV_WINDOW": 128,
}

BOUNDARIES = {
    "stream": "batch-one single-stream",
    "decode": "first draft generation through final accepted token, including transfer, "
              "rejection, correction, replay and synchronization",
    "prefill": "separate from steady decode",
    "image_load": "report cold and warm separately",
    "draft_generation_included": True,
    "metadata_and_replay_charged": True,
}

MANIFEST = {
    "schema_version": 1, "model": "Qwen/Qwen2.5-0.5B-Instruct",
    "cases": CASES, "modes": ("bf16", "w4"),
    "decode_limit": 16, "decoding": "greedy, smallest-ID tie",
    "draft_strategy": {"kind": "previous committed token repetition", "nodes": 4,
                       "parents": [4, 0, 1, 2],
                       "account_generation_and_transfer": True},
    "sparse_threshold_bf16": 0x3B80,
    "boundaries": BOUNDARIES,
    "observation_boundaries": [
        "embedding", "attention_norm", "q", "k", "v", "rope_q", "rope_k",
        "attention", "o", "attention_residual", "ffn_norm", "gate", "up",
        "swiglu", "down", "ffn_residual", "final_norm", "logits",
    ],
    "thresholds": {"nrmse_max": .02, "cosine_min": .999,
                   "zero_reference_max_absolute": 2 ** -18,
                   "tpm_min": 8000, "weight_reuse_min": 3.2,
                   "ffn_read_reduction_min": .4,
                   "committed_sequence_equality": 1.0},
}
MANIFEST_SHA256 = sha256(MANIFEST)
