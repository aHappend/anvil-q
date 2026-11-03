# Anvil-Q3-FP architecture

## Implementation state

This is the architecture for the admitted full product, not an assertion of
engineering acceptance. The sources implement common format conversion,
three-stage binary32 arithmetic, native
and AWQ dot8 reduction, iterative division/square root, exponential/SiLU,
parameter checks, weight prefetch, tensor accumulation, projection GEMV,
streaming cache codec/controller and residual/SwiGLU element arithmetic,
floating-point RMSNorm, split-half RoPE, causal GQA attention, the MLP command
sequencer, decoder, token I/O and `anvil_q3_fp_top` integration. The parent
RTL remains unchanged. Functional simulation, synthesis, timing and physical
measurements remain independent verification/shared-runtime work.

`SPEC.md` freezes interfaces and behavior. The top connects the numerical
modules through the parent's scheduler and scalar memory-port implementation;
it does not reinterpret integer kernel outputs as floating-point values.

## Preservation boundaries

Reuse `anvil_q3_bank_scheduler` unchanged. The scheduler retains accepted-request
ownership, unique tags, independent bank activity and response reordering.
Top-level sequence/cancel/drain state, client partitioning, decoder ordering,
ping-pong descriptor state and GQA ownership derive from the immutable parent.
Their numerical children must change rather than reinterpret integer outputs.

The required data path is:

```text
selected-format activation stream
  -> bank-local activation RAM
  -> eight exact wideners
native tile RAM -> exact wideners ---------+
AWQ tile RAM -> FP16 scale * signed delta -+-> 8 x FP32 multiply
  -> 4 x FP32 add -> 2 x FP32 add -> 1 x FP32 add
  -> interlocked FP32 row accumulator
  -> optional FP32 bias -> activation-store RNE
```

The three multiply stages are not a three-cycle dot product. Native dot
reduction has twelve registered stages; its accumulator makes fifteen.
AWQ contributes three prefix stages, retaining binary32 dequantized weights.
Independent bank engines remain concurrent, even when row feedback reduces
per-bank issue rate. Row contexts interlock rather than reading stale sums.

## Arithmetic foundation

`rtl/anvil_q3_fp_00_pkg.sv` centralizes bit-level format conversion, bounded
leading-zero trees, right-shift-with-jam and round-to-nearest ties-to-even.
It contains no real-number or file-backed arithmetic. Widening is exact for
finite encodings; NaN payload/sign survive widening for leaf classification.
Arithmetic and narrowing canonicalize NaNs, while Mode-0 storage bypasses
conversion to retain every original bit.

`rtl/anvil_q3_fp_mul.sv` has:

1. Classification, special-result description, normalized 24-bit significands
   and unbiased exponents.
2. Registered 24x24 significand product and exponent sum.
3. Product normalization, gradual underflow, RNE and special-result selection.

`rtl/anvil_q3_fp_add.sv` has:

1. Classification, magnitude ordering and sticky alignment.
2. Registered magnitude addition/subtraction.
3. Bounded leading-zero normalization, RNE and special-result selection.

Each stage has its own valid/ready enable. A blocked output holds its complete
payload; an empty upstream stage can still absorb an operation. Flush/reset
clear valid ownership before any output handshake. Output flags are invalid,
divide-by-zero, overflow, underflow and inexact. Invalid is distinct from a
transport/data-format error. Underflow is inexact tininess after rounding.

Combinational functions are evaluated outside sequential processes to avoid
function-local state becoming spurious asynchronous-reset registers.
Leading-zero normalization uses a logarithmic priority tree, not a linear
procedural shift chain. Pipeline boundaries constrain logic structure but do
not constitute a measured <=10 ns physical result.

`rtl/anvil_q3_fp_dot8.sv` composes eight multiply lanes with the fixed
three-level adjacent reduction. An optional three-stage AWQ prefix carries
the corresponding activations and dtype alongside dequantization. A bounded
in-flight counter drains the path before a native/AWQ mode change, preventing
different prefix lengths from reordering transactions. The internal vector
wrapper carries accumulated flags and format errors through identical
three-stage enables. It does not replace the bank scheduler or row interlock.

`rtl/anvil_q3_fp_divider.sv` emits 27 significand bits using one bounded
shift/subtract iteration per clock. `rtl/anvil_q3_fp_sqrt.sv` consumes two
radicand bits per clock for 27 restoring iterations. Both round once with the
common RNE packer, including remainder-as-sticky, and use explicit exceptional
result paths. Finite operations reach completion after 28 clocks following
acceptance; this is structural edge accounting, not an executed measurement.

`rtl/anvil_q3_fp_exp.sv` reduces x to r=x*2^-k with |r|<=1/16, evaluates
the degree-five Taylor polynomial using registered Horner multiply/add,
then squares k times. For the admitted [-80,0] range k<=11. Every operation
is binary32, and x=0 has an exact dedicated result. Approximation acceptance
is still the independent error bound in `SPEC.md`, not polynomial identity.
`rtl/anvil_q3_fp_silu.sv` uses x/(1+exp(-x)) for nonnegative x and
x*exp(x)/(1+exp(x)) for negative x, with explicit NaN/infinity/zero limits.

## Weight ownership and numerical memory ABI

The two tile slots have independent EMPTY/FILLING/READY/ACTIVE states. A
descriptor owns epoch, layer, projection, bounds and native/AWQ controls.
One slot may fill while the other is consumed. A stalled beat is immutable.
Native tiles store actual 16-bit weights in this path; native mode may not
bypass prefetch. AWQ fetch preserves parent packing and validates scales and
padding before exposing a tile.

`rtl/anvil_q3_fp_weight_prefetcher.sv` derives the parent two-slot controller
and descriptor traversal, with `banks[g].storage` as actual bank instances.
Each slot stores the descriptor's epoch, bounds, projection and format controls.
Eight lane-addressed synchronous RAM sets hold q, z, FP16 scale and raw native
weights. Writes and registered reads occupy a non-reset memory process; reset
and flush clear ownership rather than RAM contents. Native kind-1 responses
select the output row's even/odd half and validate unused high-half padding.
AWQ retains the parent's packed lane permutation and group-index counters.
The fill FSM fetches one element at a time; it does not claim packed-word
coalescing or one eight-lane beat of memory bandwidth per cycle.

`rtl/anvil_q3_fp_tensor_array.sv` keeps bank-distributed output tiles and
replicated eight-lane synchronous activation RAMs. Each engine has a metadata
FIFO of TILE_ROWS entries carrying the dot transaction's row and first/final
contribution flags. This FIFO follows accepted dot transfers rather than a
fixed wall-clock shift count. A row is busy from dot input acceptance through
accumulator output retirement. The three-stage FP32 accumulator uses the
committed sum (or +0 for input zero), and returns row metadata through the
same three elastic stages. Repeated-row beats wait; independently owned rows
and other banks can progress. Explicit endpoint wrapping covers FIFO depths
one and three. A held final result blocks accumulator retirement without
changing the payload or releasing its row prematurely.

`rtl/anvil_q3_fp_gemv.sv` retains the parent scalar memory client, source and
destination scratch slots, and round-robin result selection. Activations
load as raw 16-bit words. Q/K/V biases widen exactly, add in binary32, and
round only at the subsequent selected-format store. All seven projection
codes use the banked tensor path. Upper-half garbage in scalar activation
or coefficient words is a format error; IEEE nonfinites are not confused
with that transport-format check.

The external memory bus is still 32 bits per bank request/response. Native
projection words pack two output-row weights at a common input index.
Scratch words contain one zero-extended selected-format activation. Cache
Mode 0 packs two raw elements; lossy modes use eight words per allocated
block plus one metadata word. Requests retain logical addressing rather than
encoding private byte pointers.

### Registered client-request boundary

The top's `request_staging[client]` registers isolate every producer from
scheduler bank routing and ingress arbitration: weight-fetch clients
`0..BANKS-1` and scalar clients `BANKS..BANKS+8`, including RoPE at `BANKS+2`.
Each is a two-slot FIFO with two local ownership bits, one-bit read/write
pointers and two complete 136-bit payload registers. An unowned slot samples
producer payload speculatively on every edge, independently of valid, flush
and scheduler ready. Producer acceptance locks the write slot; scheduler
acceptance releases the read slot. Owned payload is never rewritten, including
on its retirement edge. Only the small ownership/pointer controller sees
handshake and flush conditions. Responses cross a separate registered boundary
described below.

Producer ready uses pre-edge free-slot credit, not combinational scheduler
arbitration feedback. One occupied slot permits simultaneous retire/refill
into different slots, sustaining one request per clock without downstream
stall. Two occupied slots backpressure the producer; retiring one restores
credit on the next cycle. An empty FIFO accepts two requests even when the
scheduler stalls. Read/write pointers wrap explicitly between slots 0 and 1,
independently of BANKS or the unchanged scheduler QUEUE_DEPTH (including 1
and non-power-of-two 3). Each client has independent credits, preserving
all-bank concurrency.

The weight boundary addressed the retained native 10 ns setup failure
(-0.426 ns setup WNS, +0.037 ns hold WNS): the reported path ran from tensor
`failed` through prefetch request gating/address generation into scheduler
`successor[20][3]`, not through a floating-point multiplier. With staging,
that producer cone terminates at the request register. Subsequent compact
post-fit evidence reported -0.722 ns setup WNS and +0.034 ns hold WNS at 10 ns:
RoPE `failed` reached scheduler `stage[19][0:1]`, and `ABORT_FLUSH` also
reached that arbitration cone. Extending the same elastic boundary to scalar
clients terminates their producer fault/address cones at request registers.
Scheduler routing now uses only registered payload and valid ownership,
without redundant combinational core-flush gating. These are structural
repairs, not claims of new timing closure or production-default physical PPA.

The subsequent retained post-fit result at 10 ns was still failing:
setup WNS -0.823 ns, hold WNS +0.037 ns, with `ABORT_FLUSH` reaching
`request_staging[7].payload[115]`. The original single-slot capture enable
still combined core flush, producer valid and scheduler ready. The two-slot
ownership scheme replaces that enable rather than adding another copy of
the same staging. Prefetch layer/projection/address/kind outputs now depend
on reset and descriptor/fill state, not flush-dependent request valid.
This also removes flush from the measured payload's data-input cone.
Payload bits on invalid cycles are deliberately unspecified except during
reset; only handshakes establish transaction ownership. No physical timing
improvement is claimed until fresh post-fit STA.

Every request gains one unstalled clock between producer acceptance and
scheduler eligibility. Accepted weight staging is retained; scalar reads and
writes now have the same latency/ownership boundary. No arithmetic stage is
added. Registers are independent across clients; the two
tile slots and fill/consume overlap are unchanged. Measured command latency
and bandwidth must be refreshed rather than reusing historical L1 measurements.

Local faults still propagate through the existing completion path and cannot
rewrite an accepted staged payload. Until top-level abort, its original read
or write may be forwarded; no request is fabricated by a fault. Cancel and
top-level core flush combinationally suppress producer readiness, then clear
staged ownership at the edge with priority over retire/refill. Scheduler flush
immediately prevents scheduler admission on cancel/sequence-flush/abort-flush,
and scheduler draining prevents admission thereafter. Forwarded valid and
payload need no core-flush mux before routing. The unchanged scheduler alone
drains already accepted external transactions; unforwarded staged requests are
annulled. Writes already acknowledged are not rolled back, and incomplete cache
commits remain inaccessible. Reset clears both payload and valid; flush clears
ownership without clearing payload. This avoids delaying cancellation or
masking errors to shorten the timing path.

### Registered client-response boundary

Fresh compact post-fit evidence at 10 ns still reported setup WNS -0.645 ns
and hold WNS +0.036 ns. Its critical control path was decoder `failed` through
`unit_flush`, memory-port response ready, scheduler retirement/free-slot
selection and ingress arbitration into `successor[14][1]`. Request staging
does not cut that response-credit path.

The top now inserts `response_staging[client]` between the unchanged scheduler
and every consumer. Each client owns two 33-bit error/data registers, two
ownership bits and one-bit read/write pointers. Scheduler-facing ready uses
only reset and registered free-write-slot capacity. Consumer ready, decoder
failure and core flush cannot affect that ready combinationally. In particular,
a full FIFO cannot accept on the same edge that the consumer retires; credit
returns after the edge. With one owned slot, retirement and insertion use
different slots, preserving ordered delivery without overwriting held payload.
Unowned payload registers sample speculatively; ownership alone locks payload.
Acceptance adds one unstalled clock before consumer retirement, independently
for every client, including read data, write acknowledgments and errors.

Core flush and scheduler fault gate consumer valid/data/error to zero and
annul all local ownership/pointers at the edge, taking priority over transfers.
Scheduler-facing credit deliberately remains capacity-only even during flush;
any response accepted at an annulment edge is discarded. Reset clears payload,
ownership and pointers and forces response-facing outputs to zero. A
producer-local failure may stop its consumer, but cannot propagate through
ready to scheduler arbitration; the bounded FIFO holds responses until the
top-level abort annuls them. Already buffered responses represent completed
external transactions, while the scheduler retains sole responsibility for
draining every still-outstanding external transaction. No stale buffered
response survives a sequence flush, cancellation, fault or epoch restart.
Acknowledged writes are not rolled back; cache commitment rules are unchanged.
Fresh mandatory checks and source-bound post-fit STA must establish this repair;
the failed timing result is not timing closure or production-default PPA.

## Cache hierarchy

The cache controller owns committed positions and epochs. Bounded group
staging and decoded-group storage sit above packed external K/V. Lossy
quantization is group-local; no full-context on-chip register array or
eightfold GQA replication is allowed. K and V writes, including metadata,
must all be acknowledged before commitment becomes visible.

Mode 0 is a raw bit-preserving path. Mode 1 selects Group-32 INT8 or E4M3FN.
Mode 2 selects symmetric or affine Group-64 INT4. Shared exponents and affine
zero points follow `SPEC.md`, not a heuristic range estimate. Invalid
nonfinites, metadata, forbidden payloads and padding produce explicit errors.

`rtl/anvil_q3_fp_cache_codec.sv` buffers at most one 64-element group.
Mode 0 packs/unpacks the untouched 16-bit words, including signed zeros and
NaN payloads. Lossy encoding collects exact represented extrema, searches
shared exponents in ascending order from -256, and uses integer dyadic
ties-to-even rounding. The affine search checks the admitted feasible
zero-point interval and chooses its point nearest zero. FP8 conversion has
its own E4M3FN normal/subnormal rounding boundary; it is not an INT8 alias.
Decode checks the complete metadata and every allocated payload element,
including padding, before exposing output. It scales codes to binary32
before the selected-format cache-read narrowing. Shared exponent and
zero-point selection are sequential; no combinational divider is used.

`rtl/anvil_q3_fp_kv_cache.sv` retains the parent three commands (commit,
read K, read V), per-layer committed-position/prefill state and external
memory-port handshake. Mode-0 groups are two raw elements per word. Lossy
groups allocate eight words plus metadata, with head/block-major addressing.
The controller streams scratch values into the codec and acknowledges
every output write before advancing. Only completion of the final V group
increments committed ownership. A memory or codec failure invalidates
ownership, and flush invalidates it without clearing external storage.
Format ownership is pinned per layer until flush. Reads require a previously
committed position and return a zero-extended selected-format element.
This is bounded group staging above external cache storage, not a
MAX_SEQ_LEN-sized on-chip value array.

## Model arithmetic and activation lifetimes

Norm statistics, dot reductions, QK scores, softmax denominators, weighted
value sums and logits remain binary32. Selected-format stores are explicit
rounding boundaries, listed in `SPEC.md`. RoPE uses Qwen split-half rotation.
Query heads 0..7 use KV head 0 and heads 8..15 use KV head 1 at default
geometry; head selection is a counter/shift, not a divider.

Division and square root use bounded iterative recurrence with at most
128 unstalled clocks. Stable softmax/sigmoid share the nonpositive-argument
exponential bound. SiLU avoids positive exponent growth through exp(-abs(x)).
These units must connect to the decoder; isolated arithmetic leaves do not
establish integrated model correctness.

`rtl/anvil_q3_fp_rmsnorm.sv` walks dimensions in ascending order, squares and
accumulates in binary32, divides by the represented dimension, adds binary32
epsilon `0x358637bd`, takes the square root and divides one by that root.
The output path multiplies x by gamma, then by the reciprocal, before one
selected-format store. The scalar implementation shares a registered adder
and multiplier across these phases and never bypasses their handshakes.

`rtl/anvil_q3_fp_rope.sv` reads selected-format split-half pairs and binary32
cosine/sine coefficients, then performs four registered products and two
registered sums. It rounds each rotated component once and acknowledges both
writes before advancing the pair, head or Q-to-K vector boundary. Coefficients
must be finite with magnitude at most one; bad scalar upper halves and bad
coefficients are explicit data-format errors.

`rtl/anvil_q3_fp_gqa_attention.sv` first commits all current K/V values through
the cache controller. For each query head it scans causal positions to find
the maximum scaled QK score. It then computes each context component by
ascending-position exponential/denominator and weighted-value reductions,
followed by binary32 division and selected-format storage. QK dimensions
always advance in ascending order. The implementation recomputes QK scores
for each context component, trading throughput and external bandwidth for
bounded storage rather than allocating context-sized score RAM. Denominator
and weighted sums restart at +0 for each component. Query-to-KV head mapping
is `head >> 3`; cache values are not replicated per query head. A NaN score
propagates through the head's context rather than being silently omitted
from the maximum. Undefined infinite softmax differences similarly propagate
canonical NaNs; finite stable-softmax exponentials use only nonpositive inputs.

`rtl/anvil_q3_fp_swiglu_mlp.sv` sequences gate, up, SiLU-product and down
commands. The decoder owns the shared GEMV's latched native/AWQ mode throughout
all three projections; the MLP's cmd_awq port is the matching interface
annotation, not a second independently writable GEMV mode. The decoder keeps
the parent's norm/Q/K/V/RoPE/attention/O/residual/norm/MLP/residual ordering
and client allocation. Its arithmetic children retain fault-until-flush
behavior; cache commitment survives ordinary layer/token command boundaries.

`rtl/anvil_q3_fp_token_io.sv` copies raw selected-format embedding words into
scratch slot zero. Output-head projection widens inputs and weights exactly,
then accumulates registered binary32 products in ascending component order.
The accumulator restarts at +0 for every vocabulary row; no activation
narrowing is applied to logits. Indexed logits hold under backpressure.

`rtl/anvil_q3_fp_top.sv` derives the parent sequence/cancellation/drain FSM,
adding sequence-pinned activation dtype and per-token AWQ sampling. A dtype
change without new_sequence follows the same failed-completion/drain path
as an invalid token position. Cancel overrides acceptance and flushes the
core immediately; only the unchanged scheduler retains external transaction
ownership until drain completes. New-sequence flushing invalidates every
layer's cache ownership before embedding starts.

`rtl/anvil_q3_fp_elementwise.sv` implements the parent's two residual modes
and SiLU(gate)*up mode with binary32 arithmetic. It widens scratch operands,
uses the common registered adder/multiplier and stable SiLU unit, then
narrows once for the destination scratch store. Scalar transfers retain
the parent memory-port protocol and fault/flush behavior.

## Performance and evidence model

Count one multiply-accumulate as two useful operations. Eight lanes per bank
give an issue ceiling of 8*BANKS products per cycle, not an achieved MAC rate:
the registered reduction, row feedback, packing, prefetch and memory
backpressure may lower utilization. A 32-bit-per-bank interface at 100 MHz
has an ideal payload ceiling of 0.4*BANKS GB/s in each separately measured
direction; actual accepted request traffic determines observed bandwidth.
Read/write sharing, metadata and padding must not be hidden in that ceiling.

For a dense M-by-K projection, useful work is 2*M*K operations; activation,
weight, output and metadata traffic are counted separately. Default Q/K/V/O,
gate/up/down shapes and compact decoder fixtures must be identified distinctly.
Do not extrapolate sampled row tiles into measured complete-Qwen throughput.
Negative INT-versus-FP comparisons are valid observations.

Independent L1 numerical references, simulation, sensitivity and generic
synthesis remain Verifier work. Native post-synthesis Quartus timing and
physical ALM/DSP evidence are separate from generic cells/storage. Parent
timing/PPA provenance is unresolved because `GENERATIONAL_HANDOFF.md` was
not supplied. Neither the target frequency nor historical parent acceptance
certifies this branch. Product PDF generation follows engineering acceptance.
