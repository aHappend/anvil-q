# Anvil-Q2-FP implementation architecture

## Design handoff

The design sources connect the complete token path: embedding, every decoder,
final normalization and output projection. The numerical operators implement
IEEE encoding/rounding primitives, exactly three-stage eight-row tensor lanes,
registered/iterative scalar arithmetic, the frozen exponential, AWQ
dequantization, packed native and block-scaled cache control, causal GQA,
banked GEMV, RMSNorm, residual/SwiGLU operations and split-half RoPE.
The parent scheduler, bus mux, scalar arbiter and memory-port sources are
copied without changes. The top has no Q1 compatibility mode; the reference
retains that separate product.

The complete required behavior is in `SPEC.md`, and integration instructions
are in `INTEGRATION.md`. This is a source handoff for independent verification,
not functional, synthesis, benchmark, timing or hardware acceptance.

## Arithmetic boundaries

Selected-format inputs expand exactly to FP32 bit encodings; they do not
pass through the parent's Q16.16 format. A product record carries a sign,
classification, exact 48-bit integer significand and signed binary exponent.
Normalization/rounding is a separate operation. The fixed-width rounders
handle normals, gradual underflow, overflow, ties and canonical NaNs.
FP32 addition aligns with guard/round/sticky information and rounds once.

The tensor lane uses three elastic occupied stages. S1 holds eight exact
products and first/last markers. S2 holds eight rounded FP32 products.
S3 holds eight running sums and the output marker, sharing its arithmetic
result with the persistent per-dot accumulators. S3 advancement, not output
consumption, updates accumulator state. An occupied stalled S3 cannot
reapply its product. A first marker resets the addition base to +0.

The retained -4.076 ns setup failure launches from lane `first2` and ends
at `sum3`/`accumulator`. The first-beat operation now selects its result
after the FP32 addition cone rather than muxing the accumulator operand
before alignment and normalization. Adding +0 to a rounded product is
the product itself, except that either signed zero becomes +0; S2 already
canonicalizes NaNs. This bypass does not depend on the previous dot's
accumulator, including a previous nonfinite result. Constant-index
combinational wires feed both S3 sum and accumulator registers, outside
the sequential processes.

The shared combinational FP32 adder uses nine-bit exponent arithmetic,
a five-level sticky alignment barrel and a five-level leading-zero tree
instead of integer-width exponent chains and a serial highest-bit priority
loop. Sign-controlled two's-complement addition shares the mantissa
add/subtract carry path. RNE, subnormal handling, signed zeros and nonfinite
classification are unchanged. These changes add no register captures,
do not reassociate accumulation and leave elastic advancement unchanged.
They are timing-repair candidates, not a measured timing pass. Independent
Verifier must check lane and scalar arithmetic, including singleton dots,
consecutive dots, cancellation, special values and stalls; the shared
runtime must obtain fresh post-fit STA at the unchanged 10.000 ns target.

Scalar arithmetic shares one command slot. Add uses a registered FP32
adder; multiply registers its exact product before rounding. Divide performs
one restoring quotient bit per cycle, and square root performs one radix-4
digit per cycle. Both carry remainder information into final RNE rounding.
No behavioral real arithmetic, vendor-only floating primitive, combinational
divide or unrolled reciprocal is used.

The exponential controller issues separate scalar operations for range
reduction and each Horner multiply/add. Its constants and operation ordering
are the frozen specification, not an independently selectable approximation.
Its single output slot holds a result through backpressure.

Scalar command operation codes are 0 add, 1 multiply, 2 divide, 3 square
root and 4 scale by two to the signed exponent in in_b[12:0].
Inputs/outputs are unsigned FP32 encodings, except that scale exponent.
The unit serializes commands and holds out_data/out_error while stalled.
out_error denotes a nonfinite result; callers additionally reject nonfinite
model inputs before invoking arithmetic. Unsupported operation codes return
canonical NaN with error rather than successful zero.

The AWQ stream continuously maps lane bits to nibble shifts
[0,16,4,20,8,24,12,28], including a lane held constant since startup.
It registers the nibble delta and expanded scale, uses a shared
scalar multiplier and then rounds to the selected format. Both signs of
zero scale use this same path to preserve the IEEE product's signed zero
rather than bypassing arithmetic with a forced +0. Invalid scales
and overflowing effective weights produce an explicit error response.
The codec similarly has one complete block command/result slot. Its decode
flag selects packed signed-byte/exponent input instead of native values.
It scans selected-format magnitudes for the minimum admissible exponent;
scaling, integer rounding, reconstruction and selected-format conversion
are separated by registers. Every output includes an error flag; failed
outputs cannot commit cache validity. Codec command dimensions are bounded
by the legal Q2 geometry, whose hidden-size squared bound implies
HEAD_DIM<65536. The cache controller below owns packing, transactions and
atomic token visibility.

## Banked and scratch-memory operators

`anvil_q2_fp_gemv` contains the required `banks[b].lane` instance in every
bank. A separate controller per bank owns its scalar memory client, row
group, input column, group offset, native/AWQ weight assembly and final
write acknowledgements. No bank shares another bank's accumulator or memory
reservation. The external-client path exposes all banks to the unchanged
tagged scheduler; a standalone scalar-memory path uses the parent arbiter.
The memory-fetch schedule does not claim a sustained one-beat-per-clock
end-to-end GEMV rate: only the tensor lane's arithmetic interface has that
initiation interval. Bank utilization and throughput remain measurements
for the independent suite and hardware gates.

Each bank reads one FP32 activation and eight native weights or one packed
AWQ word per input column, dequantizes AWQ rows, feeds the lane and observes
its running-sum response before advancing. The source/target scratch slots
are the parent slots in SPEC.md. AWQ scales/zeros are reused within a group,
with explicit GROUP_SIZE wrap counters. Inactive banks finish without memory
traffic; tail rows are masked. Q/K/V add each selected-format bias once.
Every active running sum is checked for nonfinite execution results.

Each bank's final bias addition uses `bias_adder:anvil_q2_fp_add`, a
single-command registered FP32 unit. The selected sum and bias are captured
before arithmetic; ordering/classification, exponent distance, sticky alignment,
add/subtract, normalization distance, normalization, RNE increment and result
packing occupy separate clocks. The bank holds its row index until the
adder response and writes back only a finite result. At command acceptance
it also registers an eight-bit one-hot writeback destination. Constant-index
sum updates use that registered destination, rather than decoding `element`
again on the completion edge. Quartus `preserve`/`dont_merge` attributes retain
this destination boundary through register optimization. This separates the
reported `element[1]` to `sums[1][28:29]` control path as well as splitting
indexed operand selection from the FP32 arithmetic. All eight final sums, tail masking,
bias-once semantics and memory coordinates remain unchanged. The added latency
is outside the tensor lane: its three captures and one-beat initiation interval
are unchanged. Both direct decoder and MLP GEMV instances use this controller.
The retained -4.035 ns setup failure motivates this repair; only fresh shared
runtime Quartus STA can establish timing closure.

RMSNorm performs an ascending square-and-sum pass and a reread/output pass.
Mean, epsilon addition, square root, reciprocal and output multiplications
are separate FP32 operations. Elementwise modes retain the parent's three
slot pairs for the two residuals and SiLU-times-up. RoPE keeps independent
head-base/pair counters, uses external FP32 tables and four multiply plus
two add/subtract commands per split-half pair. Every scratch/model/table
read is checked for the applicable finite encoding before arithmetic, and
all writes wait for acknowledgements.

## Cache lifetime and attention

The cache keeps a committed-position count and a prefill/decode cursor per
layer, rather than a validity bit for every external component. Serial
contiguous token commits make this sufficient: the only readable positions
are strictly below that layer's committed count. Invalidation, reset and failed
commits make partial or stale external writes unreachable. No external RAM
clear is needed. K and V have separate transactions, but share one final
visibility event after all successful write acknowledgements.

Mode 0 collects two adjacent FP32 scratch components, rounds each to the
selected native format and emits one packed word. Mode 1 collects a native
block, invokes `codec`, writes its padded data words and then its sign-extended
exponent word. The controller advances dimension/block, KV head and K/V
selection explicitly. It reads and validates an entire compressed block before
returning a requested component; any reserved byte, malformed metadata,
nonzero padding or failed reconstruction fails the read.

The standalone cache's `invalidate` suppresses new work and completions but
does not withdraw a held memory request. Its ABORT state drains that port and
any running codec command before exposing readiness. At the integrated top,
cancellation instead resets numerical clients and uses the unchanged scheduler
to drain tagged external transactions. A new sequence resets all cache counts.
Repeated invalidation cannot resurrect old visibility.

Attention first computes the FP32 square root of HEAD_DIM and commits current
K/V. For each query head it walks causal positions in ascending order, and
components in ascending order within each dot. Q is rounded to the selected
format; cached K/V already crossed the same boundary. Separate FP32 multiply
and add operations produce each dot; one FP32 division by the registered
square root produces its score. Explicit head-within-group counters implement
contiguous GQA without a run-time divider.

One MAX_SEQ_LEN-by-32-bit RAM holds the current head's scores. The score pass
tracks the maximum. A second pass reads each score, computes the frozen
exponential of its difference from the maximum, overwrites that entry with
the exponential and accumulates the denominator. Finally, for each output
component, an ascending causal-position pass accumulates FP32(exp*V) and
divides by that same denominator. This is not an online/reassociated softmax.
All score/exponential RAM entries read by a command have first been written
by that command. The RAM has synchronous accesses and no physical reset;
asynchronously reset control prevents stale reads.

The attention cache/scratch request mux feeds a local one-entry registered
request buffer. Occupancy and all payload fields have `preserve`/`dont_merge`
attributes, as at the existing top scalar boundary. Neither valid nor ready
falls through: capture into an empty slot and downstream acceptance are
separate edges, with no same-edge refill. This separates attention's
state-dependent cache selection from the decoder/top request muxes. It adds
one unstalled cycle per attention memory request without changing arithmetic,
causal traversal, cache visibility or independent projection-bank access.
Responses retain the existing unbuffered route; the selected controller waits
for the response, so selection cannot change while the buffer owns a request.
Reset annuls local occupancy/payload. Integrated cancellation resets this
buffer with the numerical core, while scheduler-accepted traffic still drains.

At native geometry this temporary RAM contains 32768*32 bits, reused across
heads, layers and tokens. A compressed block buffer contains
CACHE_BLOCK*16 native bits, ceil(CACHE_BLOCK/4)*32 packed bits and one
32-bit exponent. These are architectural capacities, not measured FPGA
resources. Cache contents and all model/scratch tensors reside behind the
external transaction interface.

## Orchestration and ownership

Each bank has an independent memory client and eight-row dot lane; no global
one-outstanding shortcut is permitted. Parent arbitration and tagged scheduler
retain original names. Commands, responses and arithmetic have distinct
ownership lifetimes. Accepted memory writes require responses before cache
visibility commits. Cancellation resets numerical clients while the parent
scheduler drains accepted memory traffic.

The decoder retains the parent's eleven-step order. The MLP sequences gate,
up, SiLU-times-up and down operations using its own instance of the same
banked floating-point GEMV, not the fixed-point parent. Direct decoder
projections and MLP projection clients share the top scheduler's bank-client
slices through the unchanged bus mux. There are BANKS independent projection
clients plus one scalar-operation client at the top. The parent's arbitration,
tag allocation and completion ordering remain in that scheduler.

The scalar-operation client now registers its complete request after the top
bus mux and before scheduler ingress. This cuts the reported attention
`state.VALUE` to scheduler `col`/`layer` path at the nested numerical mux
boundary, rather than modifying the accepted scheduler. The one-entry buffer
uses Quartus `preserve` and `dont_merge` attributes on its occupancy and
payload registers to retain this physical boundary through register
optimization. These attributes do not change simulation or handshake behavior;
they are not evidence that synthesis previously removed the boundary.
The buffer
has no valid fall-through or ready look-through: an empty slot accepts the
selected scalar request at one edge, and the scheduler can accept it starting
at the next edge. While full, all fields hold and upstream readiness is low;
retirement clears occupancy without same-edge refill. Scalar controllers
already wait for each response, so this introduces one unstalled request
cycle without limiting the independent BANKS projection clients or changing
the tensor lane's three-stage arithmetic contract. Responses remain unbuffered
through the original muxes, whose selection stays fixed until completion.

The buffer shares the numerical core's asynchronous reset/annul domain.
Cancellation or fault recovery discards only its not-yet-scheduler-accepted
request. Scheduler-owned transactions still drain under the parent's existing
flush-edge accounting, and a new sequence cannot reuse the discarded request.
The original reported setup slack was -4.362 ns at 10.000 ns; this register
boundary is a timing repair candidate, not a measured timing-closure claim.
Independent functional checks and shared-runtime Quartus STA must rerun.

The retained setup summary's complete launch name is
`anvil_q2_fp_decoder_layer:decoder|anvil_q2_fp_gqa_attention:attention|state.VALUE`;
its endpoints include `anvil_q2_bank_scheduler:bank_scheduler|col[1][21]`
and `anvil_q2_bank_scheduler:bank_scheduler|layer[1][19]`. Hierarchy separators
are part of these node names, not an endpoint delimiter. The available report
lists endpoints/slack but not the intervening cell arcs. Its report timestamp
also precedes the retained map/fit reports, despite the staged RTL matching
the inspected sources. Therefore the historical -4.362 ns failure must remain
recorded, but cannot certify either failure or closure of the current fitted
netlist. The local attention boundary addresses the identified request/control
cone; fresh independent functional verification and complete post-fit timing
paths are required. The reported HIDDEN_SIZE=16, two-query/one-KV-head build
is reduced, not native timing/resource acceptance.

The top retains the parent's serial vocabulary projection: for each logit,
it walks normalized components in ascending order, rounds the linear input
to the selected format and issues separate FP32 multiply/add commands.
Output weights and embeddings share the parent's kind-0 table, now selected
BF16/FP16. AWQ applies to decoder projection kinds 1/2/3, not kind 0.
The logit sum and index remain unchanged while logit_valid && !logit_ready.

Top faults annul numerical clients and invalidate sequence state, then flush
and drain the scheduler before the error completion. Cancellation suppresses
logits immediately and retains the parent's cancel_done behavior. Accepted
requests retain scheduler ownership even when numerical clients are reset;
there is no path from a drained old response into a new token.

## Reproduction and ownership

Source order is the package before modules, using `rtl/*.sv`.
No tool installation is authorized. Independent Verifier supplies exact
supported tool versions, executable portable L1 commands and benchmark-vector
entrypoints under `tests/`; Designer does not author those harnesses.
The required entrypoints are listed in `SPEC.md`, but are not claimed present
or executable until the Verifier handoff.
The shared runtime supplies the native hardware bridge and final report.
Device-specific cable identities, private host paths and runtime metadata
are not product inputs.
