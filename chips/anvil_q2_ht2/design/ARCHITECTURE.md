# Anvil-Q2-HT2 implementation architecture

## Current source state

This is a connected RTL handoff for independent verification, not an accepted
accelerator. The accepted parent
RTL remains unchanged under `anvil_q2_ht_reference/rtl/`. Its Q16.16 activation
path and legacy KV codec cannot establish native HT2 numerics.

The new foundation provides leaf RTL for pipelined floating-point arithmetic,
the fixed four-by-128 broadcast tile array, single-owner sparse unpacking,
the six-stage tree decision unit and an exact-ratio native KV codec.
None has independent functional or synthesis evidence yet. A connected native
KV subsystem now combines real external memory requests, the exact-ratio codec,
acknowledged record/layer progress, isolated scratch pages, ancestor-aware
translation and the tree's atomic pointer/mapping publication. The compatible
top and a native model sequencer now connect these subsystems through all
configured layers. Metadata, tensor issue, parallel row storage and queued DDR
bursts now overlap. Payload read-ahead, eight independently owned local
decoders, tile-streamed RMSNorm coefficients and streaming vector results
extend that overlap without changing the frozen DMA leaf. Context-local
metadata/payload preparation now shares an eight-owner registered read arbiter;
activation requests use two elastic stages, and normalization statistics use
streaming products/exp plus a pipelined adjacent-pair tree.
No model has executed in this Designer role, and no throughput is certified.
Native scalar, vector, rotate-half pair and transactional-cache attention
operators are connected by that sequencer.
A native shared-memory adapter reuses the parent DDR
arbitrator for one weight stream and three acknowledged single-beat clients.
A connected configuration subsystem routes
legacy requests to the unchanged parent and native requests to a separately
validated atomic descriptor bank. A connected weight path expands required
metadata groups and feeds the sparse DMA through one shared read interface
with explicit ordered memory ownership. Neither
subsystem has independent execution evidence yet.
A connected tensor engine now owns the activation store, weight path, physical
MAC and ordered row accumulator. It returns real unbiased FP32 projection rows,
with A9's independent format selection. The sequencer supplies model operations.
Naming a leaf or subsystem is not evidence that the top uses it.

| Source under `rtl/` | Implemented leaf structure |
|---|---|
| `anvil_q2_ht2_00_fp_pkg.sv` | Leading-zero, sticky-shift and FP32 RNE packing helpers |
| `anvil_q2_ht2_fp32_add_pipe.sv` | Align, add/subtract, normalize, round: four stages |
| `anvil_q2_ht2_product_pipe.sv` | Independent activation/weight BF16/FP16 decode, multiply, normalize and round: seven stages |
| `anvil_q2_ht2_tile_batch_mac.sv` | 512 product instances, seven four-stage reduction levels, four-stage bias addition |
| `anvil_q2_ht2_unpack_lane.sv` | Ten-stage native/dequantized lane, directly rounding integer-times-BF16 to BF16 |
| `anvil_q2_ht2_sparse_w2w4_dma.sv` | Active-slot union, required-beat run selection, fill ownership, W2 beat reuse and cancellation drainage |
| `anvil_q2_ht2_spec_verifier.sv` | Single-owner six-stage topology/completion validation and greedy-path decision |
| `anvil_q2_ht2_native_kv_codec.sv` | Native BF16 records and sequential exact-ratio INT8 scale/quantize/reconstruct |
| `anvil_q2_ht2_convert_pipe.sv` | Four-stage FP32/native conversion, gradual underflow and direct RNE at each boundary |
| `anvil_q2_ht2_fp32_mul_pipe.sv` | Seven-stage full FP32 product used by the native scalar/statistics operators |
| `anvil_q2_ht2_row_accumulator.sv` | Four-stage ordered row accumulation with explicit dependency and first/last checking |
| `anvil_q2_ht2_activation_store.sv` | Four synchronous native tile RAMs with two elastic read stages, reset validity, keep checking and write-first collisions |
| `anvil_q2_ht2_kv_map.sv` | Four-bank atomic logical map, ancestor translation, scratch allocator and instantiated tree verifier |
| `anvil_q2_ht2_native_kv_store.sv` | Instantiated map/codec, packed native DDR records, acknowledged progress and cancellation drainage |
| `anvil_q2_ht2_mode_control.sv` | Serialized extension registers and legacy configuration forwarding with cancelled-response drainage |
| `anvil_q2_ht2_descriptor_check.sv` | Registered native descriptor shape, format, stride, extent and region checks |
| `anvil_q2_ht2_native_configuration.sv` | Shadow/committed banks, cache reservation, overlap scanning and atomic native descriptor publication |
| `anvil_q2_ht2_configuration.sv` | Connected mode adapter and legacy/native configuration routing |
| `anvil_q2_ht2_metadata_tile.sv` | Exact slot-union group selection, cached metadata reads and per-lane expansion |
| `anvil_q2_ht2_weight_path.sv` | Eight ordered independently prepared tile contexts, local decoders, shared W2 cache, registered sixteen-client/eight-owner read arbitration and ordered owner drainage |
| `anvil_q2_ht2_payload_prefetch.sv` | Context-local exact needed-beat gather, isolated image, W2 beat reuse and cancellation drainage through the shared arbiter |
| `anvil_q2_ht2_tensor_engine.sv` | Connected activation store, idle-time native operand reads, weight path, A9 MAC and ordered row accumulator; held FP32 projection-row stream |
| `anvil_q2_ht2_ddr_fabric.sv` | Native weight-burst adapter and three single-beat clients sharing the unchanged parent DDR arbitrator; accepted-beat accounting |
| `anvil_q2_ht2_inverse.sv` | Sequential exact-ratio reciprocal and integer-radicand rsqrt, normalization and FP32 RNE packing |
| `anvil_q2_ht2_scalar.sv` | Connected FP32 add/multiply/inverse, split-reduction degree-12 exp and stable-sign sigmoid |
| `anvil_q2_ht2_vector_unit.sv` | Real buffered RMSNorm/residual/SwiGLU/stable-softmax/product operations, pairwise FP32 statistics and native boundary conversion |
| `anvil_q2_ht2_stream_reduction.sv` | Sixteen occupied adjacent-pair levels, four-stage adders, input closure/drain and held partial response |
| `anvil_q2_ht2_rope_pair.sv` | Four FP32 products/two sums and paired native conversions for checkpoint-provided rotate-half coefficients |
| `anvil_q2_ht2_scalar_reader.sv` | Bounds-checked cached native coefficient reads, exact format expansion and accepted-request cancellation drainage |
| `anvil_q2_ht2_native_tile_reader.sv` | Bounds-checked 1..128-word native coefficient tiles with aligned beat cache and accepted-request drainage |
| `anvil_q2_ht2_delay.sv` | Enabled registered alignment for arithmetic operands, framing, tags and errors |
| `anvil_q2_ht2_vector_result_pipe.sv` | Eighteen-stage ordered RMSNorm/residual/product/softmax-output arithmetic and native conversion |
| `anvil_q2_ht2_exp_datapath.sv` | 160-stage non-fused split-range degree-12 exponential with gradual-underflow packing |
| `anvil_q2_ht2_sigmoid_reciprocal.sv` | 53-stage restoring reciprocal restricted to sigmoid's [1,2] denominator domain |
| `anvil_q2_ht2_swiglu_pipe.sv` | 242-stage stable sigmoid, ordered gate/up multiplication and native conversion |
| `anvil_q2_ht2_attention.sv` | Native query conversion, grouped transactional K/V reads, FP32 dot/softmax/weighted-value computation and native head result |
| `anvil_q2_ht2_model_sequencer.sv` | Connected embedding/layer/final-head schedule, column-banked native RAM, full-tile input staging, parallel row retirement, RoPE, KV acknowledgements, attention and real greedy target IDs |
| `anvil_q2_ht2_projection_store_pipe.sv` | Four parallel bias/native-boundary paths, eight elastic stages, row/mask/tag/last/error alignment and exact bypass for unbiased sums |
| `anvil_q2_ht2_vector_input_pipe.sv` | Paired four-stage BF16/FP16 expansion, one operand pair per enabled cycle, partial-tile framing, retained tags and explicit invalid-count errors |
| `anvil_q2_ht2_top.sv` | Parent-compatible ports/defaults, native/legacy configuration and execution routing, one external Avalon owner, token/draft priority and native cancellation drain |
| `anvil_q2_ht2_legacy_logit_pipe.sv` | Three-stage elastic parent-Q16.16-to-FP32 RNE representation, with unchanged logit data/index |

Compile the package before the modules importing it. No parent arithmetic helper
is used in the new native path. Parent modules remain reference/legacy sources,
not independent numerical oracles.

From the project root, a leaf-only static elaboration command is:

```sh
iverilog -g2012 -t null \
  -s anvil_q2_ht2_tile_batch_mac \
  -s anvil_q2_ht2_sparse_w2w4_dma \
  -s anvil_q2_ht2_spec_verifier \
  -s anvil_q2_ht2_native_kv_store \
  -s anvil_q2_ht2_convert_pipe \
  -s anvil_q2_ht2_fp32_mul_pipe \
  -s anvil_q2_ht2_row_accumulator \
  -s anvil_q2_ht2_activation_store \
  -s anvil_q2_ht2_configuration \
  -s anvil_q2_ht2_weight_path \
  -s anvil_q2_ht2_tensor_engine \
  -s anvil_q2_ht2_ddr_fabric \
  -s anvil_q2_ht2_attention \
  -s anvil_q2_ht2_rope_pair \
  -s anvil_q2_ht2_scalar_reader \
  rtl/*.sv \
  anvil_q2_ht_reference/rtl/anvil_q2_ht_configuration.sv \
  anvil_q2_ht_reference/rtl/anvil_q2_ht_ddr_fabric.sv
```

Icarus Verilog 12.0 is the observed static compiler version, not a dependency
claim for the unexecuted full flow. This historical leaf command neither simulates nor
synthesizes, does not elaborate the newly connected product top, and cannot
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

Admitted A9 is implemented: MAC `s_fp16` selects activation decode and the new
one-bit `s_weight_fp16` selects weight decode. Product-lane `fp16` and
`weight_fp16` independently control exponent, significand, infinity and NaN
classification. Both decodes are registered in the same first product stage;
no operand conversion, format guessing or tag encoding is used. Decoded state
then advances through the existing seven stages, so alternating selector
combinations require no new pipeline stage or sideband. The tensor engine
retains the command's native format and selects FP16 weights only for a
validated FP16 weight-path response. W4/W2 reconstructed weights select BF16
even with FP16 activations.

The unpacker uses ten registers, including input and output. Quantized products
are at most a four-bit magnitude times an eight-bit BF16 significand; conversion
does not pass through FP32. Unneeded lanes are replaced before classification.
DMA groups adjacent required beats into a burst and skips gaps; it never
reissues a completed run. Odd native byte offsets mark both bytes of a straddling
element. The DMA address bound now uses the highest required aligned beat,
rather than a hypothetical full tile extending past masked final columns.
This is necessary for a legal partial final tile at the 33-bit address limit.
The W2 cache holds one physical beat, invalidated on reset, annul or
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
`anvil_q2_ht2_kv_map` instantiates it and writes selected-path mappings on the
same successful response-consumption edge. The native store instantiates that
map and supplies completion/error bits from real acknowledged K/V writes.
The connected model sequencer now supplies actual computed target argmax;
the subsystem input is independent stimulus only in leaf verification.

### Native storage and publication

`anvil_q2_ht2_activation_store` accepts full native tiles for one slot on its
write port and reads four slots in parallel. Each stored tile includes 128 keep
bits and has separate reset-protected initialization state. Missing required
lanes, invalid indices and tail-column violations return explicit errors.
Inactive slots/lanes return zero and do not require initialized storage.
Simultaneous accepted reads/writes of the same address are write-first.
Read/write legal-keep masks use continuous per-lane expressions, including
singleton and partial final tiles, so constant tile inputs are evaluated at
startup without requiring an address transition. This repairs the procedural
mask startup defect recorded in
`evidence/preparation/behavior-20261031T181004Z-ae317f6e/receipt.json`
(first legal write returned an unknown error at 26 ns). Interfaces, asynchronous
reset, ownership, stalls and mask bounds are unchanged. Fresh independent
four-state activation-startup, compiled activation-ownership and affected
integrated-top checks remain required; this change is not a functional pass.
The default 16 vectors of 8960 words occupy about 9.2 Mbit of operand data
before keep/valid/control overhead; this is a capacity calculation, not fit.

The converter expands native operands exactly when representable in FP32 and
rounds FP32 directly to the chosen native format, including subnormal results.
Its direction/format/sign/classification/data/tag advance together through four
registers. The FP32 multiplier has a 48-bit exact significand product and
separate leading-zero, normalization, denormalization, rounding and output
stages. The new scalar multiplier is not a replacement for the array's 512
native product lanes.

The row accumulator accepts one tile at a time. First-tile sums are delayed
alongside the adder rather than arithmetically adding +0, preserving a legal
negative-zero initial value. Further tiles require identical row/tag/mask and
the next increasing column-tile index. A dependent input is blocked until
the four-stage result retires. Last or error returns one held response;
nonlast retirement updates the owned accumulator without an external response.
This intentionally conservative scheduler is not a throughput demonstration.

The map uses MAX_SEQ_LEN+4 physical token pages. Reset reserves pages 0..3
as scratch and begins allocation at four. Successful append consumes selected
scratch pages, then replaces them from a monotonic bounded cursor. A successful
new sequence records its four current scratch IDs as excluded seed pages,
resets the cursor to zero and makes every old committed mapping unreachable.
The allocator skips those four IDs and never revisits another assigned page
within that sequence. It needs no reset sweep of a large free bitmap. Four
interleaved map RAMs permit one publication write per bank for an accepted
path of up to four contiguous logical positions, even for noncontiguous slots.
Publication and committed origin change only on the tree response handshake.
An internal allocator bound violation is explicit sticky `allocator_error`,
not a wrapped physical page. Annul leaves committed data and pending scratch
replenishment intact; new batches wait for replenishment.

The native store's begin ports capture count/IDs/parents/position, BF16 versus
INT8 KV, and a 33-bit base/extent. Its write port addresses slot, layer, K/V,
head and block and accepts BF16 block words. The read port adds the requesting
node and absolute sequence position. Translation selects a committed page or
one of that node's provisional ancestors/self. The progress scoreboard rejects
reads before the relevant record's successful acknowledgement. Writing a
different slot may interleave, but each slot writes increasing layer then
K/V/head/block ordinal. Final layer completion includes both K and V, all heads
and every cache block; it is not a count of issued requests.

The store has one external memory owner. Its `mem_*` port requests a single
aligned 512-bit beat and receives a ready/valid response for reads and writes.
Packed records cross beat boundaries correctly through a bounded six-beat
window; partial writes have exact byte enables. All address products/additions
are registered before issue and record bounds are checked in 64 bits.
`mem_rsp_ready` deliberately remains asserted for an owned transaction during
annul so the previous request drains; no new request is accepted until drained.
External memory/fabric must preserve response ownership and hold responses
under backpressure. Every issued read/write, including partial-record padding
and encoded scale bytes, must be charged by future integrated traffic counters.

Begin-time region validation requires the full physical-page allocation,
rounded up to a 64-byte boundary. A committed format/base/extent is immutable
until the controller is reset. Even new-sequence offers with a different
layout are rejected, because speculative writes under a changed stride could
alias still-visible old data. The future mode/configuration integration must
drain and reset this subsystem while quiescent to invalidate incompatible KV;
ordinary batch annul never provides that invalidation. An unchanged-layout
new sequence can reuse old physical pages only after successful publication.
Failed or cancelled new sequences retain the old mapping/data/configuration.

`s_finish_valid` supplies computed target IDs only after inference. The store
itself supplies the 112 completion bits and four error bits to the map/tree.
Finish waits for memory work and read/write responses to retire and seals
the batch against further operations. The six-stage tree then holds the batch
response until consumption. Cancel on that edge wins over publication.

### Configuration and shared weight loading

The mode-control adapter implements the three HT2 extension addresses.
The new configuration wrapper connects its forwarded requests to the unchanged
parent configuration in legacy mode, or to the native controller otherwise.
One adapter owner spans the request/response lifetime, including cancelled
response drainage. Native BF16/K=1 are reset defaults. Native legacy-selector
shadows remain readable/writable but cannot override HT2_MODE's selected
formats. A mode change invalidates native publication and resets legacy
configuration; a K-only change does not discard descriptors. Model/cache
configuration is not ready for use again until successful revalidation.

The native descriptor checker is single-owner, with registered shape, product,
length, bound and response stages. It returns up to three 33-bit base/34-bit
exclusive-end pairs: payload, zero points and scales. The native configuration
controller first reserves the native store's complete MAX_SEQ_LEN+4 physical
pages, then scans each validated region against prior regions. It permits
only the parent's exact embedding/head payload alias. Reserved descriptors
must be zero; uninitialized shadow words read as zero rather than exposing
unreset memory. Native row-major descriptors are separate from the parent's
legacy tiled layout and byte-exact flags. Roles/layouts are frozen in SPEC.md.

After all checks, one descriptor per cycle copies into an inactive committed
RAM bank. The last copy edge switches the bank, committed mode and cache
base/extent atomically. Failed/cancelled validation never switches banks.
The native controller retains an error response for a cancelled accepted
configuration request so the adapter can drain it; cancellation does not
silently strand that owner. Descriptor responses are independently annulled.
Every mode-bit change still must drain/invalidate actual KV and weight state
at the future top. The wrapper's descriptor invalidation alone is not that
cache implementation.

The metadata tile reader owns one captured row/column and activation union.
It registers row-stride products, row addresses, column offsets and bounds
before offering memory work. It derives the union's required metadata beats,
gathers at most two zero-point lines and five scale lines, and expands every
required lane together. An eight-line metadata cache retains aligned beats
between tiles; misses issue only lines required by a nonzero union lane.
GROUP_SIZE=1 no longer loops through 128 group-state sequences.
Required nonfinite scales, fetched
nonzero padding, out-of-range keeps or failed reads form explicit errors.
Zero scales, signed zeros and subnormal scales are not silently filtered.
No metadata read is issued for a wholly skipped tile or native payload.

The connected weight path instantiates one metadata reader, payload gatherer
and frozen sparse DMA for each of eight contexts.
Eight tile contexts retain original activations, descriptor coordinates, tag,
format, expanded metadata and effective keeps until response retirement.
Acceptance/output pointers preserve response order, while per-context
stage-started/stage-complete flags guard independent intermediate progression.
The metadata and prefetch units prepare later contexts while decoders own older tiles.
Their requests share one registered, round-robin-selected burst offer; a
eight-entry owner FIFO routes returned beats independently of the current
offer. Actual last markers are compared with each accepted beat count.
Error responses have no usable tensor payload; missing terminators retain
ownership, and annul drains before reuse. Metadata/DMA/cache invalidation is explicit via annul, including the connected
top's mode/host-write invalidation.
Each frozen DMA remains single-owner through its ten-stage decode and held
response; this overlap alone does not establish sustained production throughput.

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

The next design increment must complete multi-tile weight throughput and
word-oriented model scheduling. Legacy-token/native-batch retirement and the
legacy FP32-extension surfaces have been implemented as described below,
but remain independently untested. A9 represents mixed BF16-weight/FP16-activation operands
without another rounding boundary. The model sequencer/native store now drive
argmax and acknowledged KV completion bits respectively. Independent
verification follows the completed design handoff; these source connections
are not execution evidence and the serialized schedule does not meet the
throughput objective by construction alone.

### A9 repair and connected tensor execution

The retained defect was a shared product-format selector: HT2_MODE permits
FP16 activations with W4/W2 weights, but the unpacker reconstructs BF16
weights. The previous product lane interpreted both operands using `fp16`.
Admitted A9 repairs that contradiction by adding the independent weight
selector described above. No existing source increment was replaced.

An analytical counterexample uses one kept lane, zero bias and positive-zero
remaining lanes: FP16 activation `3c01` is exactly 1025/1024. A quantized code
1, zero point 0 and BF16 scale `3f80` reconstruct weight `3f80`, exactly 1
in BF16. The required product is 1025/1024 (FP32 `3f802000`).
With the previous shared `s_fp16=1`, that weight was
instead interpreted as FP16 15/8, producing 15375/8192. With the previous shared `s_fp16=0`,
the activation is interpreted as BF16 129/16384. Both selections are finite
but wrong; masking and error propagation cannot distinguish or repair them.
These are encoding-derived values, not results from an executed simulation.

Converting the activation to BF16 would introduce an unadmitted rounding
boundary (the example rounds to 1). Converting every BF16 weight to FP16
cannot be lossless either: BF16 `0001` is 2^-133, below the smallest positive
FP16 value. Excluding FP16 quantized modes violates required integration
coverage. Inferring formats from operand bits is ambiguous; identical 16-bit
patterns are legal in both formats. Tag or mask overloading would silently
change their frozen semantics.

The repaired interface supplies `s_fp16=1, s_weight_fp16=0` for that example.
The expected encoding above is an analytical requirement, not an executed
numerical result. Verifier owns independent bit-exact checks of all four
selector combinations, alternating formats, stalls, annul, signed zeros,
subnormals and specials. All original numerical and timing thresholds remain.

`anvil_q2_ht2_tensor_engine` captures the descriptor, vector ID, row range,
token mask, activation mode, weight mode, sparsity policy and tag at command
acceptance. Retained command validation precedes any RAM or DDR request:
columns must be 8..MAX_WORDS, divisible by eight and GROUP_SIZE; rows must lie
inside the descriptor's 1..151936 rows; weight flags must match the captured
policy; the token mask must be nonempty and the activation vector in range.
Its parameters are MAX_WORDS (default 8960, 8..8960 divisible by eight and
GROUP_SIZE), VECTOR_COUNT (default 16, 1..32), and power-of-two GROUP_SIZE
(default 128, 1..128). Invalid parameter tuples use a guarded diagnostic
branch, not clamping.

The internal activation store exposes a full-tile write/acknowledgement port
to the future native model controller. Writes have priority over new commands;
the controller must retire a write acknowledgement before starting work.
While a command runs, the engine alone reads its selected vector for all
active tokens. Increasing 128-column tiles generate explicit partial-tail
keeps. The weight path computes union sparsity and returns the captured
activation, shared weight and format together. A successful response transfers
directly into the physical four-by-128 MAC with the two operand selectors.
Its zero tile bias is not a model bias: the subsequent model operation must
add each row's actual Qwen bias once after the complete dot product, before
rounding at the activation boundary.

An eight-entry row/column prefetch FIFO accompanies weight-path acceptance.
The producer can read/fetch the next tile or row before older weight responses
return. A separate sixty-four-entry issue FIFO accompanies actual MAC input
acceptance, without
waiting for the 39-stage MAC or four-stage row accumulator. FIFO entries
remain owned until the corresponding MAC result transfers into the accumulator.
The accumulator alone enforces increasing-column arithmetic dependencies;
no dependent sum reads an unavailable accumulator. Its result uses the FIFO
row, not the producer's advanced cursor. One-tile rows set first and last
together. Each complete row produces `m_sum` (four FP32 words), absolute
`m_row`, active mask, tag, error and last. A stalled result holds all payload
while later work may fill the bounded issue capacity and then backpressure
the globally elastic MAC. `m_last` marks the final requested row or an error.
Activation, weight, format/tag/mask, MAC and accumulator errors cannot return
a successful partial row. Arithmetic validity is flushed before the terminal
error response. A weight-protocol fault first annuls the weight operation,
drains accepted memory ownership and any outstanding operand read, then returns
that error. External annul
suppresses responses and invalidates activation tiles; accepting a new command
waits for the weight path's drain. The sticky fault output is reset only by
reset; top-level fault/cancellation coordination is still required.

### Native shared-memory adapter

`anvil_q2_ht2_ddr_fabric` instantiates the unchanged parent DDR fabric with three
acknowledged single-beat clients for native KV, scalar model reads and host
access respectively. Its primary burst-read port serves the one shared weight
stream; the secondary burst port is inactive. Round-robin arbitration, read-owner queue,
private response slots, held Avalon commands and write acknowledgements are
retained rather than reimplemented. READ_OUTSTANDING remains 1..16 (default 8).

The adapter captures up to eight aligned 1..127-beat weight/metadata requests,
checking each 33-bit extent. Invalid requests return an ordered terminal fill
error without DDR issue. Accepted requests split into at-most-16-beat bursts
at 4-KiB boundaries. Independent issue/delivery heads allow later owners'
bursts to precede earlier owners' fill consumption. Acceptance reserves the
request's entire footprint within a shared 128-entry synchronous 513-bit
return RAM; aggregate reservations, not per-request fit alone, bound storage
even with fill_ready continuously low. Separate write/read pointers and stored
occupancy track returns and output prefetch; an output register holds its beat
under backpressure. Only fill consumption decrements remaining delivery beats.
Annul blocks new owners and exposed
client requests, but accepted owners remain obligations, including captured
unissued suffixes: their remaining beats complete into the cancelling owner's drain interface.
It is not silently shortened or reused by a new tile. Exposed single-beat
owners must likewise drain their accepted responses on annul.

All backend bursts are explicitly split before crossing a 4-KiB boundary.
The two 64-bit counters increment only on actual accepted Avalon read/write
commands, including metadata, KV, scalar and host traffic routed through this
fabric. Multiply beat totals by 64 to account for physical DDR bytes, including
partial-write padding. They are internal subsystem observations, not added
benchmark-only product ports. Pipelined burst issue removes per-beat
consume-before-issue serialization, but is not production throughput,
prefetch/decode utilization, timing or resource-fit evidence.

The compatible top, model sequencer and product-level DDR/KV path are now
connected; their behavior remains independently untested and their throughput
schedule remains incomplete. Missing official model/tokenizer/corpus inputs,
the Q2-FP baseline and authentic `design/GENERATIONAL_HANDOFF.md` are separate
prerequisites, not consequences of this interface conflict. Existing accepted
source increments and mandatory checks remain in place.

### Native nonlinear/statistics and attention execution

`anvil_q2_ht2_inverse` is a single-owner arithmetic engine, not a combinational
division expression or a coefficient ROM. Write a finite positive magnitude
as M*2^(e-23), where M is the complete 24-bit normalized integer significand
and e is unbiased. A leading-zero stage includes subnormal inputs. For
reciprocal, a 26-bit restoring remainder produces floor(2^50/M), one quotient
bit per cycle, with provisional result exponent -e-1. For rsqrt, it produces
floor(2^77/(M*2^(e mod 2))), where parity is e's low bit, then a 28-step
restoring integer square root of the 56-bit quotient. The provisional result
exponent is -floor(e/2)-1, using arithmetic shift, including negative e.
These formulas are derivations of the desired significand, not recorded
comparison results.

The candidate significand has 24 retained bits plus guard/round/sticky.
An exact power-of-two result can produce a leading carry; normalization shifts
it and increments the exponent. The division remainder and square-root
remainder join sticky, so discarded fractional information is not silently
truncated. A separate gradual-underflow shift precedes the existing RNE pack.
Rsqrt's integer construction uses the identity
floor(sqrt(floor(N/D)))=floor(sqrt(N/D)); both remainders distinguish an exact
root from a fractional one. The implementation therefore targets direct RNE
FP32 results for these finite operations, without Newton seed tables or
intermediate native-format rounding. Independent numerical checks are pending.

`anvil_q2_ht2_scalar` shares one existing seven-stage FP32 multiplier, one
four-stage adder and that inverse engine. It waits for the full registered
response before issuing dependent arithmetic. Exp first selects
k=RNE_integer(x*log2(e)), then forms
r=(x-k*ln2_hi)-k*ln2_lo with non-fused FP32 operations.
The chosen k remains in a signed ten-bit register. A degree-12 Taylor
polynomial is evaluated in descending-degree Horner order, with separate
registered multiply and add for every coefficient. Scaling by 2^k uses
exponent adjustment, gradual-underflow shift and RNE packing, not multiplication
by an overflowed/underflowed FP32 power-of-two constant.

All polynomial coefficients are RNE FP32 encodings of the exact rational 1/n!.
Constants and their mathematical provenance are:

| Purpose | FP32 encoding | Definition |
|---|---|---|
| Range conversion | `3fb8aa3b` | RNE_FP32(1/ln(2)) |
| Split high | `3f317200` | Exact binary value 0.693145751953125 |
| Split low | `35bfbe8e` | RNE_FP32(ln(2)-0.693145751953125) |
| Degrees 0,1 | `3f800000`, `3f800000` | 1, 1 |
| Degrees 2,3,4 | `3f000000`, `3e2aaaab`, `3d2aaaab` | 1/2!, 1/3!, 1/4! |
| Degrees 5,6,7,8 | `3c088889`, `3ab60b61`, `39500d01`, `37d00d01` | 1/n! |
| Degrees 9,10,11,12 | `3638ef1d`, `3493f27e`, `32d7322b`, `310f76c7` | 1/n! |
| RMSNorm epsilon | `358637bd` | RNE_FP32(1/1000000) |

These are mathematical constants authored for the native path, not imported
parent lookup results or fitted checkpoint-specific coefficients. For inputs
with magnitude at most 128, the range reduction keeps the polynomial argument
near [-ln(2)/2,ln(2)/2]; the ideal Taylor remainder is bounded by
exp(abs(r))*abs(r)^13/13!. This analytical truncation bound does not establish
the total hardware error of finite-precision reduction/polynomial/scaling.
The independent 2e-5 relative and 2e-7 near-zero absolute requirements remain
mandatory. Larger finite positive exp inputs overflow with explicit error;
larger negative inputs are below FP32 range and return positive zero.
Nonfinite operands return defined/canonical data with error.

Sigmoid evaluates z=exp(-abs(x)), then reciprocal(1+z). For nonnegative x
that reciprocal is the result; for negative x the result is z times the
reciprocal. It never forms exp(abs(x)) and never subtracts a near-one result
from one on the negative branch. Finite magnitudes greater than 128 produce
their representable limiting value; NaNs/nonfinite inputs remain explicit
errors. No silent catch or success-shaped replacement handles an arithmetic
fault.

`anvil_q2_ht2_vector_unit` connects this scalar engine to three synchronous
FP32 RAMs and streaming result pipelines. One input pass owns exactly count words.
The operand/auxiliary RAMs support the second normalization/output pass;
the work RAM stores actual computed softmax exponentials. No data RAM is
asynchronously cleared. Control/count/phase validity makes old words
unreachable until the required new input/compute pass completes.
Sixteen reset-protected occupied flags guard sixteen FP32 partial sums in
`anvil_q2_ht2_stream_reduction`. Each incoming square/exponential merges adjacent
equal-sized blocks from level zero upward through a four-register FP32 adder
at each level. Independent levels and successive pairs pipeline concurrently;
the final occupied levels still fold in increasing level order. RMSNorm squares
inputs in a seven-stage pipeline during the RAM load, rather than making a
second scalar square pass. After its maximum is known, softmax reads operands
at one word per clock, subtracts that maximum in four stages and evaluates exp
in 160 stages. A matching 164-register index delay directs each exponential
write to its original RAM location. Valid/last shift registers clear on
annul/failure/new operation, so stale arithmetic cannot enter a new reduction.
The final leaf closes input; a partial response is offered only after all carry
valids have drained, and then holds under backpressure. The singleton count
holds level zero without any imaginary padded addition; non-power-of-two
counts retain the same low-to-high partial fold as before.

RMSNorm, residual addition, SwiGLU, stable max-subtracted softmax and product
produce real FP32 results and native rounded output streams. Input framing,
nonfinite operands, arithmetic overflow and conversion errors explicitly fail
the owned operation. Output stalls prevent the next element from replacing
its response. The full model must still route stored activations through the
native output, not treat the companion pre-boundary FP32 value as native RAM
data. Softmax's FP32 companion is an internal attention statistic; measuring
its normalization accuracy is distinct from downstream activation-format
rounding. Both remain independently checked where required.

`anvil_q2_ht2_rope_pair` computes (a*c-b*s,b*c+a*s), using four ordered FP32
products, two additions and synchronized FP32-to-native converters. Native
Qwen pairing is rotate-half: a is component j and b is j+HEAD_DIM/2.
Cosine/sine must come from the actual checkpoint's descriptor-3 table at the
node's path-depth position. No theta, scaling policy or official coefficient
asset has been fabricated. The pair unit cannot establish that the future
sequencer loaded the correct table.

`anvil_q2_ht2_scalar_reader` gives that sequencer a single acknowledged DDR
read owner for embedding/gamma/bias/RoPE words. It separately registers
row*stride, column offset, base addition and bounds checking before offering
a request. Native formats are decoded from retained validated descriptor
flags. It caches one physical beat, but converts/classifies every selected
word even on a hit. It invalidates reuse on annul and drains accepted reads;
top-level model/mode/host-write changes must provide that invalidation.
Traffic through this client belongs in the shared fabric's actual counters.

The tensor engine now exposes an idle-time four-slot activation-read port
using the same RAM and checks as projection reads. Write offers have first
priority, model read offers second, projection commands third. An external
read owns the shared response and prevents new writes/commands until consumed.
Projection state selects only its retained vector/tile/keep/tag; external
signals cannot alter an active projection. This permits future model
sequencing to run the vector/RoPE operators on existing native storage without
duplicating all vectors in another register file.

`anvil_q2_ht2_attention` connects native query expansion, scalar FP32
arithmetic, the stable-softmax vector unit, synchronous per-head storage and
the native store's real acknowledged K/V read interface. It handles one
query head/slot/layer at a time; it does not duplicate four DDR readers.
For two KV heads, query-head lower/upper halves select their GQA head; for
one KV head all queries select zero. Query components expand according to
BF16/FP16, whereas decoded KV components are always BF16 as required by the
native cache formats. Dot products traverse increasing dimensions and FP32
weighted-value sums traverse increasing visible positions. Scores scale by
the computed FP32 rsqrt of HEAD_DIM. Per-node origin/position bound the
context; every read retains the query slot, so the existing KV map remains
the authority for committed-prefix and ancestor/self visibility.

Attention uses the softmax FP32 result before any native probability boundary
for internal statistics/weighted-V accumulation, then rounds the completed
head into selected-format activation storage. Context data RAM is not reset:
the first position explicitly uses +0 as the prior sum, and all components
are written before later positions/output can read them. Input geometry,
KV faults, tags, probability indices/last, arithmetic and conversion errors
terminate the head without successful data. Batch rollback/publication remain
the native store's responsibility. The top must co-annul attention and that
store; kv_idle prevents acceptance while the physical owner drains.

These operators are connected through the configurable 28-layer product
datapath described below. The completed RTL handoff remains subject to all
independent numerical, throughput and physical requirements. No
simulation/reference/mutation/synthesis harness was authored. No functional,
error-bound, DSP-fit, timing or TPM result follows from these source changes.

### Connected native model schedule and product ownership

The product top now instantiates the retained parent product for legacy mode
and the native sequencer for BF16/FP16 modes. The native hierarchy is
top -> model -> tensor engine -> physical MAC/weight path -> sparse DMA,
and top -> model -> transactional cache -> map -> six-stage spec verifier.
These are real connected paths, not a leaf-only list or externally supplied
target-model answers. Legacy and native Avalon outputs share one mode-selected
external port. Quiescent switching also requires parent configuration readiness:
that readiness is inhibited by the parent's real fault/cancellation drainage.
New host/token requests are inhibited during configuration offers/responses.

The native sequencer owns ten vectors in each of four token banks, with 128
synchronous native-word column RAMs per token. A scalar access selects one
column bank, while input staging reads a complete 128-column tile in one
registered access followed by capture.
Complete-vector bits reset on each batch/annul and are set only after the
required vector's final write. Every operand read checks them and its bounds.
For residual/SwiGLU loading, two tile reads capture source and auxiliary
vectors; RMSNorm instead reads its auxiliary coefficient tile from the shared
memory client. A paired four-stage converter feeds the buffered vector operator
one FP32 operand pair per enabled cycle. A 1..128-word tile count protects
partial tails; only the last tile's last transferred element asserts the
vector operator's final marker. Output stalls freeze both conversions and
their shared framing. Annul clears the feeder generation before reuse.
Embedding writes hidden state. Each layer then schedules:

1. RMSNorm into normalization storage, followed by broadcast Q, K and V
   projections; each actual bias is added once to its complete FP32 dot result.
2. Rotate-half Q/K pairs using descriptor-3 cosine/sine at batch position plus
   node depth, followed by all K/V block write acknowledgements for the layer.
3. Per-slot/head causal GQA through the transactional ancestor map, attention
   output projection, residual, second RMSNorm, gate/up projections, SwiGLU,
   down projection and residual.

The same schedule repeats through NUM_LAYERS (1..28). Final RMSNorm and
vocabulary projection emit ascending-index, slot-tagged FP32 logits. Greedy
argmax updates only when each logit transfers; equal values retain the smaller
ID, including opposite signed zeros. Only these computed IDs feed cache finish.
The held batch response is the transactional cache's held tree response, so
publication cannot precede logits or required K/V acknowledgements. Draft
publication also waits for batch_ready; legacy-token requests retire internally
through done/error without depending on that added input.
New-sequence origin changes only on successful response consumption.

Native vector/projection boundaries use the selected-format rounded result.
FP16 K/V expands to FP32 then rounds to BF16 for the explicitly BF16/INT8 cache;
the query remains FP16. Native KV bytes are never produced by relabeling an
FP16 word or the parent's Q16.16 codec.

For projection input, the controller copies complete source tiles into one
128-column tensor staging vector per slot, with explicit final-tile keeps. It then
launches one tensor command covering the actual row count. The tensor's shared
weight stream broadcasts to all active slots. An eight-entry FP32 row FIFO
accepts complete tensor rows independently of the controller's bias, native
conversion, word writes and logit transfers. It stores row index, sums,
token mask, tag, error and last together. Consumption validates the record
against the expected row before exposing it; annul clears queue ownership.
Four parallel bias-add/conversion paths retire a row through eight elastic
stages, writing all active slots' native words together. Unbiased rows bypass
the add result exactly, preserving signed-zero behavior. Row/mask/tag/last
and arithmetic errors advance/stall together. An independent stored-row
counter checks ordered writes, and the final row's write precedes complete
vector publication and phase advance. Vocabulary logits remain FP32 and
can transfer consecutive slots on consecutive clocks; greedy updates still
occur only on those transfers.
The model RAM and input
tile staging are distinct storage and copy costs; this increment does not
silently claim zero-copy use of the tensor's optional idle-time read interface.
The latter remains available but unused in this schedule.

A computation error co-annuls all arithmetic/attention and provisional cache
ownership, drains scalar/weight/KV memory, then returns one zero-acceptance
error. Native top cancellation/fabric faults suppress same-edge publication,
annul the batch, drain all accepted native/host/fabric ownership, and hold the
aborted draft's terminal error until response acceptance; an aborted
legacy-token request instead retires done/error after drainage. Committed cache
state survives batch cancellation. Quiescent mode/descriptor changes instead
invalidate incompatible committed cache state. Parent cancellation remains
the unchanged parent implementation.

Legacy-mode logits now pass through a three-stage elastic representation
pipeline: signed Q16.16 magnitude, leading-zero normalization, then FP32 RNE
packing. Data/index accompany that conversion; no result is replaced with
zero merely because the parent is selected. Parent done/error are retained
until all buffered logits have retired. These are the parent's actual fixed
results represented in FP32, not a reinterpretation of their bits or a claim
that legacy inference meets native numerical fidelity.

Eight queued tile contexts overlap
metadata preparation, payload read-ahead and local decoding; sixty-four issue records decouple
MAC input from dependent row accumulation, and eight completed rows feed
parallel row storage. Eight DDR owners share one capacity-reserved return RAM,
without duplicating token-specific weight streams. Input-vector staging now
copies full tiles rather than individual words. Each of eight context-bound
DMA instances keeps the frozen single-owner/ten-stage contract, while replaying
an isolated payload image gathered through one shared DDR interface. Each
context now has independently owned metadata and payload preparation, removing
the single metadata-address engine and single payload owner's serialization.
These context-local producers all feed the same registered sixteen-client
arbiter, with eight accepted memory owners; none is a token-specific reader.
An accepted offer can be replaced at the same edge with another eligible
producer, without accepting the still-visible old request twice.
The shared W2 cache holds eight physical beats across context reuse and blocks
duplicate requests matching a pending cacheable read. A cache-hit response
acknowledges the local gatherer, then holds its beat until consumed; it never
creates an external owner or accepted DDR beat. The per-context gatherers
read only the union's needed beats.
Context data is unreachable before successful payload completion, and context
reuse waits for ordered response consumption. On annul, local replay can
terminate immediately because its beats are already captured; accepted external
reads still drain through their original owners.

The native coefficient tile reader validates row/column/count, separately
registers address calculations, and gathers up to five beats through an
eight-line cache. It returns native bits/format/tag without premature rounding.
It shares one registered memory-offer/response owner with the scalar reader;
cancelled accepted requests cannot be reassigned to the other reader.
RMSNorm now loads activation/gamma pairs at one enabled word per cycle after
tile capture. No scalar coefficient request/conversion round-trip is made per
element. The source format of gamma is retained independently in the paired
conversion pipeline.

Vector output RAM reads have a registered pending stage feeding either an
eighteen-stage ordinary result pipeline or a 242-stage SwiGLU pipeline.
RMSNorm performs two ordered seven-stage FP32 products; residual and simple
product are aligned to that fourteen-stage arithmetic boundary, followed by
four-stage native conversion. Softmax scales its actual stored FP32
exponentials. Global stalls freeze arithmetic, validity, framing, errors,
indices and tags together. The model stores accepted vector results directly
in its selected synchronous column bank, rather than serializing each result
through scalar-write controller states. Complete-vector publication follows
the final checked write.

The streaming SwiGLU path computes z=exp(-abs(x)), reciprocal(1+z), and selects
that reciprocal for nonnegative x or z times the reciprocal for negative x.
It then computes `(x*sigmoid(x))*up` as two distinct FP32 products.
The exp datapath has 160 registered stages: classified safe argument,
seven-stage range multiplication, registered integer rounding and encoding,
parallel split-ln(2) products and ordered subtraction, twelve eleven-stage
Horner steps, registered exponent adjustment/underflow/packing. Its
coefficients are the same mathematical FP32 encodings now shared in the
package with the scalar engine, not checkpoint-derived tables.
Only exceptional exp inputs take the explicitly tagged canonical/error
bypass. The restricted-domain sigmoid reciprocal uses registered setup,
fifty one-bit restoring steps, normalization and RNE packing (53 stages).
Inputs outside its declared [1,2] domain produce canonical NaN with error;
they are not clamped to a successful reciprocal. Sign/operands and all
sidebands align with these stages before the final four-stage native
conversion. These pipeline counts are source-level design contracts,
not observed simulation results or timing closure.

The activation store now has two elastic read stages. Registered RAM output,
read metadata, missing-word checks and response capture remain aligned during
stalls, while a consumed response can be replaced on the same edge.
Four row/column ownership records associate accepted activation requests with
their later weight-path submission. The projection scanner advances on read
acceptance, not on completion of each isolated request/response round-trip;
weight and accumulator ownership still retire in order.

| Internal boundary | Pre-edge transfer and post-edge result |
|---|---|
| Activation tile | Accept at n; RAM/read metadata at n; response after n+1; first consume n+2; full stages hold together on stall |
| RMSNorm square | Accept input at n; square/valid after n+6; tree first owns it at n+7 |
| Softmax statistic | Read RAM at r; subtraction accepts at r+1; exp/index/valid after r+164; tree and work-RAM write consume at r+165 |
| Partial tree, count one | Leaf at f closes input; held level-zero response after f+1, first consume f+2 |
| Partial tree, larger count | Four registered stages per adjacent-pair carry; response waits for all carries, never just the final input's arrival |
| Context/cache replacement | A context frees only at ordered output consumption; a cached word is captured before replacement can affect its held local response |
| Annul and response/commit | Annul wins, clears logical validity/reuse and drains accepted external owners; no same-edge success publication |

These are source-level scheduling contracts, not measured benefits of 512
physical lanes or a replacement for independently executed coverage.
All numerical, compatibility, traffic, >=3500 TPM, fit/timing and hardware
requirements remain unchanged and independently untested.

## Advisory diagnostic index

| Claim | Actual retained result |
|---|---|
| Initial arithmetic/DMA/tree/codec snapshot parses | Icarus 12.0 static exit 0: `evidence/preparation/ht2-leaf-static-20261031T152612032440Z/receipt.json`; the later exceptional-dequantization edit was not in that snapshot |
| Updated arithmetic/DMA and new storage/configuration-adapter snapshot parses | Icarus 12.0 static exit 0: `evidence/preparation/ht2-storage-static-20261031T153805186666Z/receipt.json`; includes the previous dequantization repair |
| Connected configuration/metadata/weight snapshot parses | Icarus static exit 0: `evidence/preparation/ht2-configuration-weight-static-20261031T154545083175Z/receipt.json`; includes the actual-required-beat bound repair and all five new configuration/weight modules |
| A9 repair, connected tensor engine and native memory adapter parse | Icarus 12.0 static exit 0 in 2.52 seconds: `evidence/preparation/ht2-a9-tensor-ddr-static-20261031T155617253142Z/receipt.json`; current RTL hashes remained unchanged during the check |
| Scalar/inverse/vector/RoPE/attention/coefficient-read hierarchy and shared activation reads parse | Icarus static exit 0 in 2.22 seconds: `evidence/preparation/ht2-native-operators-static-20261031T160729691043Z/receipt.json`; includes the current tensor-engine port extension and all six new modules |
| Connected production model/top snapshot parses | Icarus static exit 0: `evidence/preparation/ht2-connected-model-static-20261031T161815492504Z/receipt.json`; predates the overlap and retirement changes |
| Tensor issue/row overlap, burst-return storage and compatible retirement parse | Production-top Icarus static exit 0 in 2.92 seconds: `evidence/preparation/ht2-overlap-retirement-static-20261031T162359268379Z/receipt.json`; predates queued metadata/DDR ownership and banked model staging |
| Queued metadata/DDR ownership, banked model staging, parallel row storage and paired vector-input streaming parse | Production-top Icarus static exit 0 in 3.02 seconds: `evidence/preparation/ht2-prefetch-staging-static-20261031T163418421007Z/receipt.json`; all 33 current HT2 modules and 22 parent modules were included |
| Payload read-ahead, context-bound decoder pool, coefficient tiles and streaming vector arithmetic | Advisory static diagnostic retained at `evidence/preparation/ht2-read-ahead-vector-static-20261031T164353Z/receipt.json`; exact source hashes and compiler outcome are recorded there, not functional acceptance |
| Concurrent context preparation, elastic activation scheduling and pipelined normalization statistics | Static diagnostic receipt: `evidence/preparation/ht2-stream-scheduling-static-65a0e91c/receipt.json`; consult its exact source hashes and exit status; no behavioral or synthesis claim |
| Parent preservation for this increment | All 22 parent hashes equal the previous receipt in the new static receipt |
| Functional/numerical/mutation/synthesis/model results | Not executed; independent Verifier ownership |
| Production fit, DSP mapping, timing, board behavior and throughput | No evidence; mandatory shared-runtime gates and benchmark acceptance remain outstanding |

All receipts retain exact portable argv/cwd, source hashes, compiler-version
logs, start/end timestamps, timeout/exit status and raw stdout/stderr. These are
static-elaboration diagnostics only, not passing L1 evidence. No simulation or
synthesis harness was authored or executed by Designer. The first two historical
receipts predate the configuration/metadata increment and its required-beat
address-bound repair; the third includes that increment but predates A9.
The fourth first includes the independent operand selectors, tensor engine and
native memory adapter; the fifth also includes the native operator hierarchy
and idle-time activation-read port. The sixth connects the model sequencer and
top; the seventh adds bounded overlap and legacy retirement. The eighth adds
queued tile/DDR ownership, beat-oriented metadata expansion, full-tile banked
input staging, parallel projection storage and paired vector-input streaming.
Every frozen DMA instance remains single-owner through response consumption;
no latency or transaction-ownership relaxation was made. The ninth snapshot
adds payload read-ahead, a context-bound decoder pool, native coefficient tile
reads and streaming ordinary/SwiGLU result execution. It also prevents a
malformed metadata response's discarded suffix from reaching a subsequent
metadata operation. These are inspection-driven changes, not claimed repairs
of independently executed functional failures. This increment addresses inspected serialization/ownership bottlenecks;
no functional failing test or numerical repair was executed or claimed.
Static elaboration does not establish numerical
behavior, cancellation correctness, memory inference, timing or performance.
