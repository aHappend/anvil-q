# Anvil-Q1-FP2 architecture

## Design handoff boundary

The integrated source is ready for independent functional verification, not
accepted as a measured accelerator. Implemented modules are:

| Source | Responsibility |
|---|---|
| `rtl/anvil_q1_fp2_00_pkg.sv` | Exact BF16 product records, E4M3FN/scale conversion, leading-bit and associative metadata helpers |
| `rtl/anvil_q1_fp2_bfp_tensor_array.sv` | Elastic 64-lane exact signed 544-bit reduction and one FP32 rounding |
| `rtl/anvil_q1_fp2_fast_rsqrt.sv` | Two-stage normalized magic-seed/single-Newton ROM pipeline |
| `rtl/anvil_q1_fp2_fp32_binary.sv` | Elastic nine-stage exact-RNE FP32 add/multiply primitive |
| `rtl/anvil_q1_fp2_exp.sv` | Eight-stage fixed-point range reduction and degree-six exp polynomial |
| `rtl/anvil_q1_fp2_reciprocal.sv` | Six-stage normalized reciprocal ROM interpolation and FP32 rescaling |
| `rtl/anvil_q1_fp2_mx_quantize.sv` | Nine-stage two-Group-32 scale selection and E4M3FN RNE quantization |
| `rtl/anvil_q1_fp2_epilogue_fusion.sv` | Buffered RMSNorm/RoPE/SwiGLU/residual commands using internal vector RAM and named fast-rsqrt |
| `rtl/anvil_q1_fp2_flash_attn.sv` | Single-query chronological online attention with bounded K/V tile RAM and one final normalization |
| `rtl/anvil_q1_fp2_gqa_group.sv` | Shared-query-group command/broadcast ownership, independent-head result buffering and ordered group output |
| `rtl/anvil_q1_fp2_ddr_read_stream.sv` | BF16/MX vector intake with aligned descriptors, shared-scale caching and held-response consumption |
| `rtl/anvil_q1_fp2_kv_reader.sv` | One chronological external K/V traversal for a whole GQA query group |
| `rtl/anvil_q1_fp2_ddr_pingpong.sv` | Two descriptor/response buffers with ID ownership and ordered retirement |
| `rtl/anvil_q1_fp2_telemetry_csr.sv` | Independent saturating live/snapshot counters and delayed CSR response |
| `rtl/anvil_q1_fp2_projection.sv` | Cached activation groups, transposed 64-by-64 weight tiles, exact tensor groups and native Q/K/V bias |
| `rtl/anvil_q1_fp2_kv_writer.sv` | Acknowledged BF16/MX history data and scale-plane writes with byte strobes |
| `rtl/anvil_q1_fp2_decoder_control.sv` | Complete decoder dependency graph, internal vector/logit RAM, exclusive DDR client routing and scalar configuration |
| `rtl/anvil_q1_fp2_top.sv` | Parent-compatible dispatch, optimized direct named hierarchy, sequence ownership and live telemetry |
| `fpga/anvil_q1_fp2.sdc` | Single 10.000 ns clk constraint, no timing exceptions |

The direct top instances are `tensor_array`, `epilogue_fusion`, `flash_attn`
and `telemetry_csr`; the epilogue instantiates `anvil_q1_fp2_fast_rsqrt` as
`fast_rsqrt`. The first attention head and its sibling heads are connected to
the shared-query-group controller, not left as demonstration-only kernels.

## Tensor dataflow and exactness

Integer-valued exponent/index expressions use explicitly extended 32-bit
`$signed` operands rather than `integer'(...)` casts for Yosys 0.33 frontend
compatibility. Unsigned fields are zero-extended and signed exponents are
sign-extended; arithmetic widths, rounding rules and pipeline boundaries are
unchanged. Independent synthesis must establish frontend acceptance.

FP2 modules use explicit `anvil_q1_fp2_pkg::` function references, matching
the immutable parent's package-qualified pattern. Wildcard package imports
are omitted because the Yosys 0.33 frontend rejects them. This portability
repair changes no function bodies, operand widths, signedness or pipeline state;
fresh independent synthesis and numerical regressions remain required.

The tensor accepts 64 BF16 pairs or two Group-32 MX groups in one advance.
MX conversion precedes the exact BF16 arithmetic and contributes its own
observable status. Masking applies to both conversion and arithmetic effects.
Each product is an eight-by-eight integer multiply plus a signed binary exponent.
Two registered maximum levels select E_max including acc_in.

An absolute fixed grid is used instead of the parent's per-term 64-bit
right-shift-and-sticky approximation. Each product is placed once through
coarse/fine pipeline stages into a 544-bit exact signed domain. A 64-bit
E_max-relative reporting window distinguishes main-window versus exact-tail
alignment events; the tail is retained mathematically, not discarded.
Six registered balanced tree levels reduce all lanes; a first-node
carry-save merge includes the FP32 accumulator without a seventh tree level.
Separate magnitude, leading-bit, rounding-preparation and final-packing
registers establish the frozen k..k+15 schedule.

This choice prioritizes exact cancellation over unsubstantiated ALM claims.
The broad grid and normalization remain physical PPA/timing risks; authoritative
post-fit results must include them. If this implementation misses the >45%
ALM-per-lane reduction, it requires design repair, not exclusion of the tail
or a narrower success claim.

A global elastic clock-enable freezes all data and metadata when the final
valid stage is blocked. With no stall, II=1 and result latency follows the exact
edge table in SPEC.md. Throughput is 64 products per advancing input cycle,
not a claim of 64 delivered MACs per wall-clock cycle under DDR/consumer stalls.

## Storage ownership and overlap

The ping-pong ring has exactly two physical 512-bit response buffers. Each slot
transitions FREE -> QUEUED -> INFLIGHT -> RETURNED -> FREE. Read/write descriptor
payloads and controller tags are stored with their slot. Ring head is retirement
order; ring tail is descriptor allocation order; DDR request ID is slot index.

Both slots may be INFLIGHT simultaneously. An out-of-order response changes
only its matching slot. A later RETURNED slot cannot bypass an older pending
head. Descriptor fields stay stable under request backpressure, and completion
fields stay stable under consumer backpressure. Consumer retirement, not merely
response arrival, releases the slot; this avoids overwriting returned-but-unused
data. At full occupancy, retirement and refill share the freed slot on one edge,
with new descriptor ownership winning over release.

The read-stream engine submits subsequent aligned data descriptors while it
consumes the current ping-pong head. A response remains owned by the ping-pong
slot until its last needed element transfers; a second response can return
concurrently. MX scale reads precede their corresponding data segment and
cache all 64 scale bytes for up to 2048 logical elements. The engine submits no
data from the following scale segment until the current segment retires.
This prevents a stale shared exponent from being applied to prefetched data.
The decoder routes exactly one client until its completion. Projection
computation and scalar bias requests cannot consume another client's DDR
response. This is an implemented ownership schedule, not a measured bandwidth
or overlap result.

## Dependency and lifetime table

| State/resource | Producer | Consumer | Lifetime / guarantee |
|---|---|---|---|
| Tensor decoded group | Input handshake | Product stage | Frozen with global pipeline enable |
| Tensor exact tail | Alignment stages | Exact tree / final RNE | Never replaced by sticky-only cancellation information |
| DDR descriptor | Controller command transfer | DDR request transfer | Full payload held until request acceptance |
| DDR response slot | Matching DDR response transfer | Ordered controller retirement | Cannot be reused while returned but unconsumed |
| ULP sample | Actual FP32->BF16 conversion | Telemetry event input | One event per real conversion; nonfinite sentinel explicit |
| Live counters | Qualified datapath events | Snapshot command | Saturating, independent of CSR response stalls |
| Snapshot counters | Atomic control write | CSR reads | Stable until next snapshot or clear |
| Epilogue input/auxiliary/residual RAM | Accepted command stream | FP32 arithmetic sequencer | All command operands stored before computation; no external fused scratchpad round-trip |
| Epilogue result RAM | Arithmetic sequencer | Output stream | Complete result vector retained until transferred; stalled final output preserves command ownership |
| Attention query RAM | One accepted query vector | All tokens in that command | Loaded once before tile intake |
| Attention K/V tile RAM | Single chronological KV stream | Current tile computation | Reused only after every token of the tile updates running state |
| Attention output RAM | Online alpha/p updates | Next token or final normalization | First token supplies explicit zero instead of reading stale state |
| Group query channels | Q projection / RoPE stream | One attention leaf per query head | All commands launch before head-major queries; each query loads only once |
| Group broadcast register | Chronological K/V reader | Every attention leaf in the query group | Per-head accepted mask prevents duplicates when tile readiness differs |
| Group output RAM banks | Independent attention leaf outputs | Ordered group output stream | No group output is exposed before every sibling completes successfully |
| K/V reader key-vector RAM | Current token's K row | Same token's V stream and query-group broadcast | HEAD_DIM BF16 words, reused only after the V command completes |
| Future KV history | Current K/V projection | Causal attention | External, sequence-owned, invalidated on reset/new-sequence |
| Cached projection inputs | FP32 input conversion / optional MX quantization | Every output tile | One BF16-decoded group RAM per projection command |
| Transposed weight tile | DDR weight-row stream | Tensor input-axis dot | Up to 64 input rows by 64 output columns; masked ragged tails |
| Projection sum bank | Tensor ordered results | Next input group / output stream | FP32 group-boundary rounding, cleared once per output tile |
| Architectural vector slots | Embedding/projection/epilogue/attention outputs | Next graph dependency | Internal FP32 RAM, no optimized external kind-8 accesses |
| Complete logit RAM | Output-head projection | Public logit stream | Invisible until every vocabulary row succeeds; errors discard validity |

## Nonlinear pipeline strategy

Fast-rsqrt normalizes into [1,4), combining exponent parity with ten mantissa
bits to address a 2048-word ROM. The ROM is generated deterministically by an
integer constant function performing the required magic-seed Newton update at
each interval midpoint. Its read and rescale registers are the only two
architectural stages; there is no hidden iterative engine.

The fused epilogue now sequences exact FP32 add/multiply pipelines with bounded
internal input/auxiliary/residual/result RAM. RMSNorm performs a component-order
square/sum reduction, mean/epsilon and fast-rsqrt, then x/factor/gamma products.
Before the vector products, RMSNorm corrects the unchanged leaf result using
the normalized residual r=1-n*v*v and the degree-two binomial polynomial
1+r/2+3*r*r/8. Eight ordered FP32 operations reuse the existing multiplier
and adder, adding 80 fixed edges per finite command, without extra arithmetic
units, external storage, another Newton update or a change to the two-stage
leaf. Power-of-four normalization keeps residual products in a bounded range.
The correction addresses the upstream drift retained in
`evidence/preparation/mx-drift-analysis-20261102T203040Z-fdae560c/receipt.json`:
legal leaf approximation error crossed BF16/MX activation boundaries, while
all 2664 checked quantizer codes and final-head arithmetic matched their actual
operands in the linked localization evidence. Quantization, head arithmetic,
fixtures, references and acceptance tolerances are unchanged. Fresh independent
architecture/operator/performance evidence is required; this is a repair
rationale, not a numerical pass or physical-acceptance claim.
Independent squares now stream through the first multiplier at initiation
interval one and use result RAM as temporary storage. The sum remains serial
in its original FP32 rounding order. Normalization cascades both existing
multiplier pipelines at initiation interval one, with nine gamma-delay
registers preserving component ownership across the first pipeline. Rounded
squares are no longer live when normalized results overwrite the same RAM.
Each pass drains its last valid result before changing RAM ownership; public
outputs still wait for complete status accumulation and retain the original
backpressure and completion schedule. This repairs the serialized RMSNorm
schedule implicated by
`evidence/preparation/fp2-rms-benchmark-20261102T174913Z-7dcd504b/receipt.json`
(FP2 cold/warm 44295/44293 cycles versus parent 31274/31275). These retained
numbers describe the failed pre-repair design, not performance of this repair;
the independent Verifier must rerun the unchanged comparison.
RoPE now reads a split-half pair and issues its two rotations on consecutive
edges through the existing two multipliers. Rounded products feed the adder
while later pairs are being loaded. Address/subtraction tags follow the full
18-edge issue-to-write path, keeping both halves and successive heads distinct.
Its in_aux stream still carries cosine in the first half and sine in the
second, supplied by the decoder's deterministic kind-11 table.

SwiGLU now streams exp(-abs(gate)), denominator add, reciprocal and the
negative-branch product at initiation interval one. Matching exp, reciprocal
and sign delays select the original stable sigmoid branch; the positive branch
does not inherit flags from its unused negative-branch multiplication. This
first pass stores sigmoids in existing result RAM. After draining, a second
pass reads gate/sigmoid/up and streams the two original rounded multiplication
boundaries. Read ownership precedes in-place output overwrites. Residual add
also streams collected components through the existing adder. No arithmetic
units, public ports, external intermediate transfers or coefficient rules
change. All passes drain before exposing aggregate status and ordered,
backpressure-stable results.

These changes address retained numerical-pass performance failures:
`evidence/preparation/fp2-rope-benchmark-20261102T183648Z-e792c676/receipt.json`
(FP2 cold/warm 27550/27551 versus parent 17407/17407) and
`evidence/preparation/fp2-swiglu-benchmark-20261102T183647Z-93e28716/receipt.json`
(FP2 298881/298883 versus parent 273088/273086).
Those are pre-repair measurements, not verified speedups of the new schedules.
Independent numerical, transfer, benchmark and physical checks remain required.

Exp uses signed Q24/base-2 reduction and registered Q30 Horner arithmetic.
Reciprocal normalizes the entire positive finite FP32 domain and interpolates
two adjacent Q1.31 ROM endpoints. Both ROM data and polynomial provenance live
in synthesizable sources; no generated runtime-state files or tool install is
needed. These approximations' numerical bounds and timing remain unverified.

The attention leaf loads one BF16 query, then accepts each K/V pair once into a
bounded TILE_TOKENS*HEAD_DIM tile. It computes chronological FP32 dot scores,
parallel running-max exp rescaling, sum/output updates and one final reciprocal
normalization. A tile can be partial, and TILE_TOKENS=1 or 3 uses real storage
boundaries rather than power-of-two pointer masks. It never stores all scores
or all KV history. See SPEC.md for exact command, framing and completion edges.

The Group-32 MX quantizer selects each scale through five registered maximum
levels, then performs per-lane ties-to-even encoding. Masks suppress metadata,
status and code effects; scales and saturation counts remain public outputs.
It supplies projection activation conversion and external KV packing.
FP32-to-BF16 conversion and integer-to-FP32 helpers have also been added to the
owned package. Independent verification must not reuse these as its oracle.

The decoder joins these blocks through explicit commands and internal FP32
vector storage. Scalar gamma/bias/table responses feed the appropriate command
operands; they are not intermediate scratchpad round-trips. Actual conversion
handshakes, tensor result events, transport demand and epilogue input starvation
feed telemetry. No functional simulation or synthesis has been performed by
Designer.

## Shared GQA traversal primitives

`anvil_q1_fp2_gqa_group` controls GROUP_HEADS independent instances of the
unchanged single-query attention leaf. Its engine channels are flattened,
low-head-first buses. The top retains the required direct
`anvil_q1_fp2_flash_attn flash_attn` instance for head zero and instantiates the
remaining siblings alongside it, connecting all of them to this group
controller. Each leaf uses `engines_rst_n`: a group fault synchronously aborts
siblings still collecting a tile rather than stranding them in a busy state.

The group starts every sibling once and loads queries in head-major component
order. It accepts a chronological K/V component pair into one holding register.
Each sibling sees that pair until its individual handshake; a sent mask then
suppresses that sibling's valid. Only after all siblings accept can the holding
register be reused. Thus different tile-ready timings do not duplicate or drop
components, and the external reader does not reread KV for a different query
head. This conservative broadcast has a one-cycle refill bubble; it makes no
claim of one external pair per cycle.

Independent synchronous result-RAM banks accept all sibling output channels
concurrently. Successful done pulses are remembered. No group result escapes
until all HEAD_DIM components and successful completions have arrived from every
head. Results then stream head-major with stable head/component/last metadata.
Framing errors, unexpected extra outputs and fatal operator flags abort the
group, so a failed sibling cannot leave an apparently successful partial group.
The architectural decoder additionally buffers logits until the whole token
is known to be successful.

`anvil_q1_fp2_kv_reader` reads kind 9 and kind 10 rows for token positions
0..cmd_len-1 exactly once per group. `cmd_first` is the KV-head component offset
in the row containing all KV heads. A synchronous HEAD_DIM-word key-vector RAM
holds the current token's K vector while V streams from the read engine.
Each V transfer pairs with the corresponding registered K component. Only that
bounded vector, response buffers and the attention tiles are resident; history
remains external. BF16 and independently scaled MX rows use identical logical
indices. The controller launches one reader per KV-head group, not one per
query head, with cmd_len=token_pos+1.

The generic read engine and K/V reader expose descriptors for the existing
DDR ping-pong module; neither fabricates DDR completions or owns physical IDs.
Their descriptor fields are all reads. Integration ties the ping-pong write
flag/data/strobes to zero and forwards scale/kind/layer/proj/row/col/tag fields.
These clients have exclusive descriptor/response ownership from command
acceptance through completion in decoder_control. An error drains already accepted requests
and any previously offered stalled descriptor before returning command ownership.
No failed response is exposed as operand data.

## Projection, writeback and top-level integration

The compatibility decoder is the immutable parent instance. ENABLE_FP2=0
preserves its modes, including mode-3 rejection, while the optimized dispatcher
uses DDR for all weights and history. ENABLE_FP2=1 selects that compatibility
decoder only for modes 0 and 2. A token's latched precision cannot change while
it runs, and continuation must match the last committed sequence precision.

Native projection weights preserve input-row/output-column orientation.
Each DDR command reads up to 64 adjacent outputs from one input row; a
64-by-64 local tile transposes this stream into input-axis tensor reductions.
The input activation cache is reused across output tiles. Two response slots
overlap prefetch with scalar component retirement. Synchronous tile/sum reads
precede tensor issue; every prior result retires before the next input group
can read its accumulator bank. Ragged input groups mask unused tile bits.
Output-head weights instead retain vocabulary-row/hidden-column orientation.

MX weight scales are per matrix row along output columns, so an input-axis
dot has more than two independent weight scales. The streaming reader decodes
those scales to exact specified BF16 operands before tile storage. Activation
groups have their own quantization/scales and are decoded once into the cache.
The integrated tensor therefore uses its lossless BF16 port in both modes;
mode 3 still transports MX codes/scales, not dense BF16 weights. Its standalone
native-MX port supports matching-group leaf traffic. This avoids silently
changing the parent's matrix orientation or grouping unrelated exponents.

The KV writer uses one 64-component staging register and one quantizer.
BF16 writes consume up to two beats per group; MX data consumes one beat and
scale-plane writes use one/two byte enables within an aligned metadata beat.
All writes are acknowledged before storage reuse. This conservative writer
does not claim write-side double buffering; read-side ping-pong overlap is real.

The full layer graph, final norm and output head use internal FP32 vector slots.
No optimized external scratchpad transaction is generated. All vocabulary
logits remain buffered until the complete token succeeds. A group failure drains
the shared reader before operator abort; scalar/reader/writer faults complete
only after their response ownership has settled. The reset bridge must discard
old-epoch responses, as required by the external protocol.

ULP telemetry samples actual FP32-to-BF16 rounding for projection inputs,
history writes and queries. These mutually exclusive schedule phases cannot
drop simultaneous samples. Alignment counters receive each tensor result's
full event count. DDR stalls use actual selected-client demand; epilogue bubbles
measure input-ready cycles waiting on RAM/config feeding, not reduction,
computation or downstream stalls.

## Performance and physical acceptance still required

Matched benchmarks must account for the scalar-to-physical-beat adapter on
both sides consistently. Report cold scale/table loading, warm runs, actual
64-byte transactions, padded tails, scale reads and GQA reuse. A full MX group
has 32 bytes of data versus 64 BF16 bytes, plus one scale byte before beat
padding; this arithmetic is not itself a measured 50% total traffic reduction.
Yosys cells are not Arria 10 ALMs; post-fit ALM and DSP efficiency claims require
native matched Quartus measurements.

No experiment or acceptance result is recorded in this document. The missing
generational handoff remains an evidence gap described in SPEC.md.
