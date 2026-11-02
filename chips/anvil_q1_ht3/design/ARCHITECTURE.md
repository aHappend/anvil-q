# Anvil-Q1-HT3 architecture

## Current checkpoint

This is an incomplete Designer source checkpoint, not a working accelerator or
an accepted product. The unchanged parent is
`anvil_q1_ht2_reference/rtl/`. No prior HT3 source was present at intake.
Only arithmetic and exact pre-provisional KV conversion are implemented so far.
No top-level substitution or wrapper around the parent's execution datapath
has been introduced.

## Implemented source decomposition

| Source | Responsibility |
| --- | --- |
| `rtl/anvil_q1_ht3_00_fp_pkg.sv` | IEEE encodings, exact finite packing, RNE narrowing, sticky alignment and AWQ permutation helpers |
| `rtl/anvil_q1_ht3_reset_sync.sv` | Two-edge release interlock with asynchronous assertion |
| `rtl/anvil_q1_ht3_fp32_add.sv` | Four-enabled-stage FP32 add/subtract through operand sign |
| `rtl/anvil_q1_ht3_fp32_mul.sv` | Four-enabled-stage FP32 multiply with exact 24x24 product |
| `rtl/anvil_q1_ht3_expand16.sv` | One-enabled-stage BF16/FP16 expansion |
| `rtl/anvil_q1_ht3_narrow32.sv` | One-enabled-stage RNE BF16/FP16 narrowing |
| `rtl/anvil_q1_ht3_fp32_divsqrt.sv` | Bounded restoring division/square root with a reserved E+64 response |
| `rtl/anvil_q1_ht3_kv_quantize.sv` | Bounded exact-rational RNE signed INT4/INT8 quantization and saturation |
| `rtl/anvil_q1_ht3_kv_store_convert.sv` | Atomic K/V conversion with captured ownership and separate scales |

The FP helper structure and add alignment follow parent prior art, with a
distinct HT3 namespace; no reference file is modified. HT3 multiply has the
required four rather than inherited three enabled stages. The quantizer is new:
it compares exact represented-value half-integer thresholds rather than
forming a rounded FP32 quotient.

## Exact conversion datapath and ownership

Each scalar converter reserves one response slot on request acceptance.
Request registers preserve source bits, scale and format. A normalization
register separates significand decoding from exponent classification. A second
register forms the exact scaled numerator and bounds. Each of eight search
iterations then uses a DSP-friendly 24x9 product register followed by a
33-bit threshold-comparison/update register. A final register encodes the
chosen magnitude and error. The two thresholds at very small/large exponent
differences are mathematically equivalent early outcomes, not FP overflow
handling.

The K/V wrapper owns two scalar response slots and one external response.
It accepts both scalar requests simultaneously, retains the parent's ownership
tags independently of arithmetic, and retires the scalar responses atomically.
It never exposes one successful coordinate without its matching K/V result.
Errors travel alongside the pair; the eventual cache owner must prevent an
errored row from becoming complete. Under held output valid, even a later
abort does not rewrite a visible response.

This boundary consumes active node/coordinate pairs only. Noncontiguous slot
masks are the decoder's admission decision; inactive slot payloads must not be
submitted. Node/layer/head/coordinate scale capture must occur before this
boundary, not be looked up again while the transaction stalls.

Native formats ignore extension scales. Quantized formats preserve FP32 until
the integer threshold conversion and output zero-filled code containers. The
converter contains no provisional FP32 cache and no dequantization path.

## Required integration still to implement

1. Complete numerical primitives: range-reduced exp and sin/cos with the exact
   admitted latencies, stable SiLU, dequantization and
   explicit inference numerical-error propagation.
2. Build four-slot x 64-row tensor compute with deeply registered DSP paths,
   enough accumulation contexts, correct native/AWQ/INT8 boundaries, sparse
   compatibility and source-bound 256-lane accounting.
3. Implement `anvil_q1_ht3_epilogue_fusion`, private vector/pair retention,
   all seven modes and a real decoder graph using `u_epilogue`.
4. Implement `anvil_q1_ht3_flash_attn` with two tiles, FP32 online rescaling,
   GQA/ancestor masks, native/quantized cache adapters and `u_flash_attn`.
5. Connect full-FP32 post-RoPE K and post-projection/bias V to the implemented
   converter. Extend provisional code ownership, store completeness and
   packed committed reads/writes. Do not retain a hidden FP32 provisional
   alternative or requantize during commit.
6. Implement extension CSR/image validation and immutable captured scale
   ownership, packed weight/cache descriptor lengths, bounds/overlap checks,
   padding validation, idle-only mutation and image/prefix invalidation.
7. Integrate transactional batch/tree execution, commit/error drains,
   source-compatible top ports/parameters, CDC-safe transport, ping-pong
   prefetch credits and first-legal-opportunity bus issue.
8. Document the complete integrated no-stall cycle formulas before Verifier
   freezes temporal assertions. Current formulas cover only implemented leaves
   and conversion, not the missing vector/attention/top schedules.

## Planned memory and streaming contracts

Architectural activations remain distinct from operator-boundary scratch.
RMSNorm necessarily retains a vector for statistics and replay; RoPE retains
partners. These private buffers must be bounded by MAX_VECTOR/HEAD_DIM,
not written to shared scratch between fused operators.

For attention, retained Q and o/m/l are bounded by head geometry; exactly two
K/V tiles are bounded by FLASH_TILE. Context length changes traversal count,
not score/probability memory size. Cache formats are BF16, FP16, signed INT4
and signed INT8; native queries remain controlled independently by cmd_fp16.
Each layer/head K/V scale is fixed for the committed image and shared across
tokens/slots.

Each quantized K or V record is 64-byte aligned with
`64*ceil(C*b/512)` bytes, packed coordinate-major and zero padded; K and V
remain separate regions. Runtime layout generation must use counters/shifts
and precomputed constants, not combinational division/modulo. Existing native
regions and legacy image packing stay unchanged.

DMA must reserve return capacity before issuing. Accepted and completed
transactions are distinct. Reset/abort/new sequence invalidate consumers
without abandoning accepted bus responses; successful prefix visibility is
deferred until all required committed writes succeed. No physical rollback of
already acknowledged writes is assumed.

## Design choices, alternatives and limitations

Exact threshold search was chosen over FP32 divide/reciprocal because even a
two-ULP quotient bound cannot decide exact integer half ties. A 300-bit common
denominator aligner was rejected: normalization confines nontrivial decisions
to a 33-bit comparison, with mathematically exact extreme handling. Eight
iterations make latency independent of sign, format and numerical value.
Separate K and V engines avoid cross-association under stalls and let the pair
retire atomically.

The current pair converter is deliberately conservative and non-reentrant.
Its documented initiation interval is not a complete bandwidth analysis.
Subsequent integration must account for conversion in store completion and
demonstrate the actual required throughput; the zero-avoidable-tile-bubble
claim is conditional on resident data and downstream readiness, not a blanket
memory or compute supply guarantee.

The current packing helpers still require independent IEEE testing and
synthesis/STA scrutiny. Register counts and DSP-oriented structure are not
proof of resource fit, bounded physical delay, 200 MHz timing or arithmetic
correctness. No simulation, synthesis, benchmark, physical timing or HIL
result is claimed by this checkpoint.
