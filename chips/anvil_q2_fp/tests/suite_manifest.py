"""Versioned executable suite definition, frozen before each execution."""

from dataclasses import asdict
from itertools import product

from transformer_reference import Geometry


SEEDS = (17, 43, 89)
DOMAINS = (
    "native/AWQ tensor projections and logits",
    "RMSNorm and residual",
    "split-half RoPE",
    "causal GQA and dual-format KV",
    "SwiGLU and integrated decoder/token",
)


def configurations(seeds=SEEDS):
    return [
        dict(banks=banks, cache_mode=cache, fp_format=fmt, weight_mode=weights, seed=seed)
        for banks, cache, fmt, weights, seed in product(
            (1, 2, 4), (0, 1), ("bf16", "fp16"), (0, 1), seeds)]


def manifest(geometry=None, seeds=SEEDS):
    return {
        "schema": 1, "suite": "anvil-q2-fp-five-domain-v1",
        "shape_class": "reduced",
        "geometry": asdict(geometry or Geometry()),
        "seeds": list(seeds), "domains": list(DOMAINS),
        "matrix": configurations(seeds),
        "domain_matrix_entries": len(configurations(seeds)) * len(DOMAINS),
        "matrix_policy": "Every domain retains all bank/cache/format/weight dimensions.",
        "source_tensors": {
            "embedding": "((seed+11*vocabulary_row+7*component) mod 33 - 16)/31",
            "gamma": "1+((seed+kind+layer+component) mod 5 - 2)/64",
            "delta": "(3*seed+5*layer+7*projection+11*input+13*output) mod 7 - 3",
            "zero": "3+(seed+layer+projection+3*group+5*output) mod 9",
            "scale": "1/(128*2^((seed+layer+projection+group+output) mod 2))",
            "effective_weight": "delta*scale; packed AWQ uses qweight=zero+delta",
            "bias": "((seed+3*layer+5*projection+output) mod 9 - 4)/256",
            "rope": "angle=position*1000000^(-2*pair/head_dim); 100-digit Taylor sin/cos",
            "token": "token_id=position mod vocabulary; increasing positions",
        },
        "formats": {
            "fp": "RNE selected-format tensors, A16 GEMV and QKV boundaries; nonfused FP32 ops",
            "parent": "FP16 tensor loads; saturated Q16.16 scratch; Q2.30 RoPE; half-away rounding",
            "mathematical": "Same exact rational source tensors; 70-digit Decimal true exp/sqrt",
            "parent_native_weights": "not applicable; no invented native parent baseline",
        },
        "operation_order": [
            "embedding", "ascending decoder layers", "ascending-component pre-attention RMSNorm",
            "ascending-column biased Q/K/V projections", "split-half RoPE",
            "cache commit after all K/V acknowledgements", "causal GQA, ascending token/component",
            "output projection", "residual", "pre-MLP RMSNorm",
            "gate/up projections", "SiLU(gate)*up", "down projection", "residual",
            "final RMSNorm", "ascending-vocabulary FP32 logits",
        ],
        "metrics": {
            "bit_conformance": "Every emitted write/logit exactly equals independently rounded oracle.",
            "max_absolute_error": "max(abs(observed-mathematical))",
            "mean_absolute_error": "sum(abs(error))/N",
            "rms_error": "sqrt(sum(error^2)/N)",
            "normalized_rmse": "sqrt(sum(error^2)/max(sum(mathematical^2),1e-30))",
            "cosine_similarity": "dot(obs,ref)/sqrt(dot(obs,obs)*dot(ref,ref)); null if undefined",
            "token_cycles": "Final pre-edge accepted logit cycle minus accepted token-command cycle",
            "domain_intervals": "Measured final-write-ack interval since preceding stage final-write ack",
            "speedup": "Measured matching parent token cycles / measured FP token cycles",
            "bank_utilization": "Observed requests and externally outstanding-request cycles, by bank",
            "storage": "Actual accepted cache writes*4 bytes, including metadata and word padding",
            "transaction_overhead": "Separate request and acknowledged-response counts; not payload bytes",
            "generic_synthesis": "Yosys cell/state/memory counts, not Arria 10 FPGA utilization",
        },
        "directed_coverage": [
            "Unit fixtures separately include zeros, cancellation, signs, subnormals and ties.",
            "Cache fixtures separately include outlier blocks, corruption and partial commit failure.",
            "Norm-controlled 28-layer full-head attention drift has its own retained manifest.",
        ],
        "disclosure": "Synthetic accelerator workloads, not pretrained language-task accuracy.",
        "native_scope": "Native full-token five-domain timing/resources require the shared hardware gates.",
    }
