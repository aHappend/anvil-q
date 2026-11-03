# Anvil-Q1-HT3 architecture

## Current checkpoint

This is a connected Designer implementation handoff, not a functionally
verified or accepted product. The unchanged parent is
`anvil_q1_ht2_reference/rtl/`. No prior HT3 source was present at intake.
Arithmetic, exact pre-provisional KV conversion, weight dequantization,
the four-slot 256-lane tensor block, seven-mode epilogue, tiled online attention,
image-tagged provisional storage and packed DDR cache adapters are implemented
in owned RTL. The HT3 projection now connects the 256-lane tensor to native,
AWQ and signed-INT8 weight streams, a reserved prefetch and queued DMA arbiter.
The HT3 cache controller connects code-only provisional storage to packed
committed reads and copies. The new decoder connects the Qwen projection,
fused epilogue, attention and FP32 store converter. The execution controller
connects branch/correction processing, selected-node copies and transactional
prefix/result publication. Queued CDC transport and the loader connect through
the external top, inherited CSR control and extension-aware image controller.
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
| `rtl/anvil_q1_ht3_fp32_exp.sv` | 32-enabled-stage range-reduced fixed-point polynomial exponential |
| `rtl/anvil_q1_ht3_fp32_sincos.sv` | 64-enabled-stage quadrant reduction/CORDIC, FP32 and Q48 phase inputs |
| `rtl/anvil_q1_ht3_rope_frequency.sv` | Elaboration-constant Q56 theta=1e6 frequencies for all legal even head dimensions |
| `rtl/anvil_q1_ht3_epilogue_fusion.sv` | Seven-mode four-slot FP32 epilogue with synchronous private retention/replay |
| `rtl/anvil_q1_ht3_mac_lane.sv` | Four-context FP32 multiply/accumulate with recurrence forwarding |
| `rtl/anvil_q1_ht3_tensor_array.sv` | Four physical slots times 64 lanes, held tagged panel results |
| `rtl/anvil_q1_ht3_dequant.sv` | Legacy AWQ boundary plus full-FP32 signed-INT8 weight stream |
| `rtl/anvil_q1_ht3_scalar.sv` | Reserved inference arithmetic response and explicit numeric errors |
| `rtl/anvil_q1_ht3_attn_tiles.sv` | Two bounded K/V tiles, captured scales/masks and overlapping reserved fetch |
| `rtl/anvil_q1_ht3_flash_attn.sv` | FP32 online m/l/o rescaling, tile-local scores, four-slot/GQA attention |
| `rtl/anvil_q1_ht3_provisional_kv.sv` | Code-only image/format-tagged row completeness and fault poisoning |
| `rtl/anvil_q1_ht3_kv_writer.sv` | Bit-preserving INT4/INT8/native records, zero padding and transactional writes |
| `rtl/anvil_q1_ht3_kv_reader.sv` | Actual packed-DDR code extraction, beat caching and captured K/V scales |
| `rtl/anvil_q1_ht3_panel_prefetch.sv` | Reserved two-bank column supply, split native beats and abort-safe request drain |
| `rtl/anvil_q1_ht3_dma_mux.sv` | Ordered request-owner queue, round-robin stall lock, registered tagged responses and same-edge credit reuse |
| `rtl/anvil_q1_ht3_burst_reader.sv` | Held one/two-beat metadata/weight acquisition, including same-edge memory returns |
| `rtl/anvil_q1_ht3_projection.sv` | Connected physical tensor, native/AWQ/full-FP32 INT8 streams, row/group scale lookup and conservative sparse replay |
| `rtl/anvil_q1_ht3_kv.sv` | Connected code-only provisional/committed cache ownership, selected-row copies and complete response drains |
| `rtl/anvil_q1_ht3_01_layout_pkg.sv` | Elaboration-only geometry/group/scale-count/offset functions without divide/modulo operators |
| `rtl/anvil_q1_ht3_decoder.sv` | Actual Qwen graph, direct projection epilogues, FP32 K/V producers, captured layer/head scales and pre-provisional conversion |
| `rtl/anvil_q1_ht3_tree_mask.sv` | Registered four-node ancestor/position classification with inherited root-parent encoding |
| `rtl/anvil_q1_ht3_spec_verifier.sv` | Hardware matching-target path selection and correction-token decision |
| `rtl/anvil_q1_ht3_execution.sv` | Connected decoder/cache, captured image/format, selected-layer copies, private reservation and held prefix/result publication |
| `rtl/anvil_q1_ht3_async_fifo.sv` | Synchronous dual-clock RAM, registered Gray ownership and credited command/response crossings |
| `rtl/anvil_q1_ht3_mailbox.sv` | Held bundled-data request/acknowledgment crossing for loader ownership and responses |
| `rtl/anvil_q1_ht3_transport.sv` | Queued Avalon issue, full-response reservations and reset-surviving physical debt drain |
| `rtl/anvil_q1_ht3_image_loader.sv` | Inherited DDR-clock loader ABI using HT3 mailboxes, real write responses and ownership release |
| `rtl/anvil_q1_ht3_counter_cdc.sv` | Request/acknowledgment snapshot of physical DDR bytes |
| `rtl/anvil_q1_ht3_control.sv` | Inherited CSR/counter ABI and idle-only format/scale-table extension control |
| `rtl/anvil_q1_ht3_descriptors.sv` | Synchronous descriptor RAM, bounds/overlap/format validation, finite model inputs and positive-finite extension scales/zero padding |
| `rtl/anvil_q1_ht3_top.sv` | Exact ordered external ABI, diagnostic-safe legal hierarchy, admission and complete execution/loader/DMA/CDC wiring |

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

## External integration and remaining acceptance

`u_control` owns legacy mode/sparse policy, extension format and scale-table
registers. `u_descriptors` owns installation, immutable image validation and
the generation tag. An accepted loader acquisition or image/format/table
mutation invalidates execution prefix and provisional ownership. No command
can enter between mutation and that invalidation because CSR/loader ownership
also gates top-level admission. A pending result or outstanding DMA excludes
mutations; accepted transactions drain before another owner can reuse memory.

Descriptors are synchronous RAM with a single control-side read/write owner
and a separate registered lookup response. Their mathematical layouts and
lengths select elaboration constants, not a runtime divider or multiplier.
Installation scans existing regions for overlap before changing a descriptor.
Image commit checks every slot/identity/length/bound, each active model
halfword, the extension's overlap with every occupied region, all positive
finite scale entries and zero table padding. Scale-table changes require
recommit; captured decoder/array/cache scales cannot change under backpressure.
The legacy all-zero extension uses the parent's FP16 cache boundary when
legacy FP16 is selected; explicit nonzero cache formats use their own encoding.
The internal cache format is always captured independently of query encoding.

SPEC contains the complete top/CSR/image initialization and execution edge
recurrences. All independent numerical/protocol, quantized-store-to-later-
attention, parameter, compatibility, benchmark/performance, mutation,
synthesis, timing and hardware obligations remain unperformed. The current
epilogue uses conservative serial SIMD schedules; >60% measured transition-
cycle reduction remains required, not inferred from naming or scratch removal.

## Tiled attention and code-preserving cache

Attention uses four scalar workers, bounded synchronous query/output storage,
one tile-local FP32 score bank and two raw K/V tile buffers. Tile storage holds
16-bit containers plus both FP32 scales at each coordinate; masks are retained
per tile token. Capacity is proportional to HEAD_DIM and TILE_TOKENS, never
MAX_SEQ_LEN. Fetch runs independently of score/online-softmax/value arithmetic.
Each source K/V coordinate is fetched once per query-head traversal; the value
phase reuses that tile's retained V, not a second context traversal.

Online rescaling updates both l and o under a new maximum. First contribution
ownership selects alpha=0 without infinity subtraction. Every arithmetic update
is FP32 and separately rounded; probabilities are not narrowed. GQA uses head
and within-group counters. Prefix/ancestor masks exclude invalid sources before
maximum and sums. Tile release occurs on the final o-write edge, and a resident
successor performs its first read on the following edge. Memory supply and the
serial dependent arithmetic still determine actual throughput.

The provisional bank stores only code containers and captures format/image
ownership at command begin. A row needs an exact, complete ascending write
packet before any read; faults poison it until new ownership begins. Flush
invalidates ownership without dropping a held response. Commit packing copies
those raw codes unchanged, with zero padding and separate K/V regions. The
reader extracts codes from real returned DDR bytes and retains layer/head scales
with its request. Attention performs the actual dequantization and reports
overflow independently of successful finite write saturation.

The cache controller selects provisional/committed reads and copies a
selected complete row through the actual packed writer. It checks captured
image/format ownership and retains supplied layer/head scales with read
responses. The decoder reads actual extension-scale DDR bytes at layer begin,
checks them and retains head/K/V association through conversion and reads.
The execution controller advances private reservation only after all layers
of a selected node copy successfully, and public prefix only after every
copy and the final corresponding output transfer. It preserves the inherited
correction traversal. These connections do not constitute executed
store-to-subsequent-attention evidence or a functional/performance verdict.

## Projection and DMA reservations

The actual projection uses a 67-bit architectural activation bank with
synchronous ports, 64 parallel dequantizers and `u_tensor_array`. Native
columns preserve 16-bit encodings; AWQ retains its original unsigned
permutation/FP16-scale/BF16 boundary. INT8 scale bytes are read from the actual
projection subregion of the extension image in output-row/input-group order,
with counters for row/group association and a one-beat scale cache. INT8
results remain FP32 to the physical array. Five-stage tags track the exact
activation/column alongside stalled dequantization.

The panel supply has two low/high synchronous banks retaining 128 columns.
It reserves complete requested beats, not merely returned beats, so pending
DMA responses cannot overwrite unconsumed columns. Bursts are bounded to
half the applicable capacity and TILE_BEATS; TILE_BEATS=1 may divide a native
column into separate commands. A held bus request survives abort, all accepted
responses drain, and a held output remains stable.

The DMA arbiter queues accepted request ownership and registers each response
with its owner and error. It can issue a next client request immediately when
external ready and reservation credit permit, including same-edge final
response retirement when full. It does not insert a PICK/SEND turnaround
sequence or use a single overwritable response-length counter for multiple
outstanding requests. The saved core/DDR transport now uses a command FIFO,
response FIFO, complete-return reservation and persistent physical debt
ledger. It replaces its bus-stage request on the accepting edge for resident,
credited same-kind traffic. No physical DMA turnaround, CDC, frequency or
throughput result is claimed; independent checks remain pending.

Sparse down projection avoids a real weight read only for a genuinely zero
activation column and a finite committed image. Nonzero threshold predictions
replay actual weights, preserving the parent's numerical behavior and
nonzero provenance flags. Actual byte/statistic events are retained for
future independent matched measurements.

## Fused operator retention and phase precision

The epilogue consumes producer data once and retains private FP32 data, the
required auxiliary vector and 16-bit gamma coordinates. Residual/norm/RoPE
boundaries replay that private storage, not external scratch. Four arithmetic
workers run active slots in parallel; coordinate and pair processing is
currently serial. RAM contents are not reset, and command ownership and length
prevent stale reads. Failed input, arithmetic or narrowing never produces a
successful completion.

RoPE uses Q56 frequency constants and a Q48 phase input to the same pipelined
CORDIC used by the FP32 sin/cos primitive. This avoids prematurely rounding
large position*frequency products to FP32. That choice is specific to phase
generation; inference vector multiply/add operations remain separately
rounded FP32. The 48 CORDIC iterations are registered individually; exp's
Horner multiply/add pairs are also separated. These structures are not
STA evidence.

The tensor has 256 physical multiplier/accumulator lanes, not a time-shared
64-lane block. Four per-lane accumulation contexts rotate on accepted columns;
tag pipelines advance through input bubbles and match both arithmetic
latencies. Forwarding supplies a completed context on its same reuse edge.
Reduction occurs only after the last in-flight product/accumulation retires.
This sustains the architectural one-column-per-edge admission interval, but
actual model utilization depends on independent execution/performance
measurements, which remain pending.

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

Attention faults are command-owned: completion relinquishes tile-error
ownership before command readiness returns. The drained tile fetcher accepts
a fresh start from IDLE and clears its previous cancellation/error state.
Displayed requests and accepted responses retain the same drainage rules;
recovery does not require reset or discard memory obligations.

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
