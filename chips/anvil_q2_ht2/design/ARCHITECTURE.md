# Anvil-Q2-HT2 implementation architecture

## Current source state

This is a partial implementation, not a ready accelerator. The accepted parent
RTL remains unchanged under `anvil_q2_ht_reference/rtl/`. Its Q16.16 activation
path and legacy KV codec cannot establish native HT2 numerics.

The new foundation provides leaf RTL for pipelined floating-point arithmetic,
the fixed four-by-128 broadcast tile array, single-owner sparse unpacking,
the six-stage tree decision unit and an exact-ratio native KV codec.
None has independent functional or synthesis evidence yet. The top, full native
model sequencer, transactional cache mapping/storage and approximation operators
still require implementation and integration. Naming a leaf is not evidence
that the top uses it.

| Source under `rtl/` | Implemented leaf structure |
|---|---|
| `anvil_q2_ht2_00_fp_pkg.sv` | Leading-zero, sticky-shift and FP32 RNE packing helpers |
| `anvil_q2_ht2_fp32_add_pipe.sv` | Align, add/subtract, normalize, round: four stages |
| `anvil_q2_ht2_product_pipe.sv` | Native BF16/FP16 decode, multiply, normalize and round: seven stages |
| `anvil_q2_ht2_tile_batch_mac.sv` | 512 product instances, seven four-stage reduction levels, four-stage bias addition |
| `anvil_q2_ht2_unpack_lane.sv` | Ten-stage native/dequantized lane, directly rounding integer-times-BF16 to BF16 |
| `anvil_q2_ht2_sparse_w2w4_dma.sv` | Active-slot union, required-beat run selection, fill ownership, W2 beat reuse and cancellation drainage |
| `anvil_q2_ht2_spec_verifier.sv` | Single-owner six-stage topology/completion validation and greedy-path decision |
| `anvil_q2_ht2_native_kv_codec.sv` | Native BF16 records and sequential exact-ratio INT8 scale/quantize/reconstruct |

Compile the package before the modules importing it. No parent arithmetic helper
is used in the new native path. Parent modules remain reference/legacy sources,
not independent numerical oracles.

From the project root, a leaf-only static elaboration command is:

```sh
iverilog -g2012 -t null \
  -s anvil_q2_ht2_tile_batch_mac \
  -s anvil_q2_ht2_sparse_w2w4_dma \
  -s anvil_q2_ht2_spec_verifier \
  -s anvil_q2_ht2_native_kv_codec rtl/*.sv
```

Icarus Verilog 12.0 is the observed static compiler version, not a dependency
claim for the unimplemented full flow. This command neither simulates nor
synthesizes, does not include a top that has not been implemented, and cannot
satisfy any mandatory acceptance check.

## Arithmetic and native cache implementation decisions

The multiplier stages are operand decode, significand product/exponent sum,
leading-zero detection, normalization, gradual-underflow shift, RNE packing and
output. The adder stages are magnitude selection/alignment, sum/difference,
normalization and RNE packing. Nonfinite classifications travel alongside finite
arithmetic so canonical exceptional results and errors remain aligned.

The tile's global elastic advance freezes every arithmetic register and
sideband together. Bias is delayed through 35 registers to meet the final
four-stage adder. Valid/tag/mask use 39 registers. Annul clears validity so
old arithmetic cannot reappear as a new transfer.

The unpacker uses ten registers, including input and output. Quantized products
are at most a four-bit magnitude times an eight-bit BF16 significand; conversion
does not pass through FP32. Unneeded lanes are replaced before classification.
DMA groups adjacent required beats into a burst and skips gaps; it never
reissues a completed run. Odd native byte offsets mark both bytes of a straddling
element. The W2 cache holds one physical beat, invalidated on reset, annul or
fill/protocol error. Integration must annul it when host writes or mode changes
invalidate weights. Only one accepted external burst is owned at a time.

The native codec interface accepts BF16 `s_data` words and `s_record` with
`2*WORDS+2` byte capacity, selected by `s_encode` and `s_int8`. BF16 records
use `2*WORDS` bytes; INT8 records use `WORDS+2` bytes, with scale first.
Encoding zeros padding. `m_byte_length` names meaningful bytes. Successful
responses provide both encoded records and reconstructed BF16 words.
Error responses set `m_error`, suppress data/record payload and never imply
publication. The codec has variable latency and holds responses until accepted.

For A8, finite BF16 magnitude is an eight-bit significand times a binary power.
The scale algorithm selects a representable BF16 grid, never finer than
2^-133, and divides an at-most-15-bit integer numerator by 127 using a
16-cycle restoring divider. Remainder comparison rounds once, then only a
zero scale is clamped to `0001`. Quantization divides exact shifted integer
significands against the stored scale using the same sequential divider;
both retained-parity ties and saturation are represented explicitly.
Reconstruction multiplies the integer code by the stored scale's significand,
normalizes, gradually underflows and rounds directly to BF16.
No FP32 intermediate or combinational division is used. These are implementation
algorithms awaiting an independently derived exact-rational comparison.

The tree leaf owns only the committed pointer and its decision response.
Its `commit_valid` pulse reports successful response consumption; it does not
by itself store or publish KV data. The future top/cache controller must use
that same consumption event to publish the complete selected-path cache mapping.
Top-level vocabulary range validation and actual target argmax remain required.

## Required connected dataflow

Host/configuration validation -> generation-owning batch scheduler ->
embedding/native activation banks -> layer sequencer -> sparse union DMA ->
shared weight tile -> 4 x 128 native multipliers -> ordered FP32 reduction ->
dependency-tracked row accumulators -> rounded native activation banks.

The layer sequencer must also schedule native scalar/vector normalization,
RoPE, causal grouped-query attention, softmax, residual and SwiGLU operators.
Provisional K/V writes require real memory acknowledgements before completion
bits can reach the tree verifier. Tree response consumption is the single
atomic publication event for both slot mappings and the sequence pointer.
Actual computed logits, not independently supplied target IDs, feed integrated
greedy verification.

| Resource | Owner / release |
|---|---|
| DMA captured request/metadata | One request until response acceptance or cancellation drain |
| Accepted external read | Old generation until every accepted beat is drained |
| Weight broadcast | Shared across active slots; never four duplicated readers |
| FP elastic pipeline | One global advance freezes all data and sidebands |
| Row accumulator | Row/slot generation; next tile waits for the four-stage dependency |
| Provisional KV | Batch generation until atomic selected-path publication or rollback |
| Committed KV map | Changes only at successful response consumption |
| Unreset RAM | Reachable only through reset-protected validity/generation |

## Layout and performance assumptions

All byte layouts and cycle boundaries are frozen in `SPEC.md`. For a complete
128-column tile, payload is 256 native bytes, 64 W4 bytes or 32 W2 bytes.
Four slots reuse that payload; sparsity may suppress it only if the active-slot
union is empty. These are geometry counts, not measured traffic reductions.
An unaligned native tile can span five 64-byte beats; W4 two and W2 two.
Metadata, alignment, rejected drafts, cache/control traffic and stalls all count
in end-to-end measurements.

At 100 MHz the 512 lanes have an analytical peak of 51.2 billion products/s.
This is not achieved model throughput, fit, DSP mapping or timing closure.
The required >=3500 TPM and >50% DDR reduction remain unmeasured.

## Dependencies and handoff

No generational handoff, official model assets, Q2-FP baseline or physical
measurements were present at source intake. Do not invent parent PPA or use
private session data to fill these gaps. Future manifests must resolve inputs
relative to the project root and include immutable SHA-256 values.

Designer may run only a fast static parse/elaboration check. Verifier separately
owns numerical/reference models, tests, corpus/benchmark manifests, mutation
execution, synthesis and clean reproduction. The mandatory commands are listed
in `SPEC.md`; their entry point has not been supplied by this design increment.
No simulation, synthesis, timing, board, benchmark or product acceptance is
claimed here.

The next design increment must implement the compatible top/configuration ABI,
real shared memory arbitration/prefetch/metadata expansion, native activation
storage and model sequencing, approximation operators with coefficient
provenance, dependency-tracked row accumulation, and isolated provisional KV
storage plus atomic selected-path mappings. Native FP16 activations must not
reinterpret BF16 dequantized weights as FP16; integration needs an explicitly
rounded compatible operand boundary. Mode changes/host writes must invalidate
weight reuse. Actual model argmax and acknowledged KV completion bits must
replace leaf-only stimulus at integration. Independent verification follows
the completed design handoff; none of these requirements is satisfied by
standalone leaves or by the static command above.
