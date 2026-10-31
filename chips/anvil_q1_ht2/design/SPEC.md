# Anvil-Q1-HT2 v2.5.0-ht2-fp-spec-sparse

## Authority and implementation status

The independently admitted work order is the acceptance contract. This document
records its interface and numerical freeze; it does not assert acceptance.
The Designer sources connect native arithmetic, the four-slot projection
array, sparse/replay scheduling, vector operators, causal attention,
provisional/committed KV, the HT2 CSR overlay, decoder/execution control,
finite-image validation and the native top. DDR responses cross through a
streaming FIFO; dense panel prefetch overlaps arithmetic issue. Deliverable
compatibility copies are present. This is a design handoff, not numerical,
performance or engineering acceptance. Independent behavioral, synthesis,
timing, hardware and benchmark results remain pending.

Designer owns `rtl/*.sv` and `design/*.md`. Independent Verifier owns
`tests/*.py`, reference models, stimulus, mutations and synthesis. The shared
runtime owns hardware gates, execution records and the final independently
approved PDF. The supplied `anvil_q1_ht_reference/rtl/*.sv` is immutable
provenance, not passing evidence for HT2.

## Geometry and top-level ABI

The required top is `anvil_q1_ht2_top`. Preserve the exact parent parameters and
ports, adding only the batch/commit ports specified below. Defaults:

| Parameter | Default |
|---|---:|
| NUM_LAYERS | 24 |
| HIDDEN_SIZE | 896 |
| INTERMEDIATE_SIZE | 4864 |
| NUM_Q_HEADS / NUM_KV_HEADS / HEAD_DIM | 14 / 2 / 64 |
| GROUP_SIZE / AWQ_BITS | 128 / 4 |
| VOCAB_SIZE / MAX_SEQ_LEN | 151936 / 32768 |
| LANES / BANKS / LANES_PER_BANK | 64 / 8 / 8 |
| DDR_WIDTH / TILE_BEATS / KV_WINDOW | 512 / 256 / 128 |

Legal reduced geometries have layers 1..24, hidden 8..896 and intermediate
8..4864, both multiples of eight, query heads 1..14, KV heads 1..2, even head
dimension 2..64, hidden=query_heads*head_dim, query heads divisible by KV heads,
KV width a multiple of eight, group size 1..hidden dividing hidden and
intermediate, vocabulary 1..151936, sequence length 1..32768, tile beats 1..256
and window 1..min(128,sequence length). Structural parameters remain fixed.
Illegal configurations must elaborate with safe diagnostic-only dimensions and
terminate with `PARAMETER ERROR` before work.

The inherited ports are `clk,ddr_clk,rst_n`, the ordinary token/logit interface,
CSR interface, load interface and 512-bit Avalon memory interface, with exactly
the widths/directions in `anvil_q1_ht_reference/rtl/anvil_q1_ht_top.sv`.
Added inputs are `batch_valid`, `batch_count[2:0]`,
`batch_token_ids[127:0]`, `batch_parents[11:0]`, `commit_ready`.
Added outputs are `batch_ready`, `commit_valid`, `commit_count[2:0]`,
`commit_token_ids[127:0]`, `commit_position[31:0]`, `commit_error`.
Slot zero is the least-significant field. Native `logit_data[31:0]` carries
IEEE FP32 bits. Compatibility `anvil_q1_ht_top` and `anvil_q1_top` retain Q16
behavior and must be compiled separately from reference modules of the same name.

Token and batch presentation together is an error, not duplicate execution.
Batches require a primed committed prefix. A parent is 4 for prefix or an
earlier slot index. Positions are prefix position plus tree depth.
Reject unavailable prefix, illegal topology, IDs outside vocabulary and sequence
overflow before committed-KV mutation. Ordinary logits are vocabulary-index
ascending. A batch emits one atomic 1..4-token commit, never branch logits.
Correction state must be evaluated before any dependent command is accepted.

## Inherited CSR map

This table transcribes the supplied descriptor implementation, including its
staging versus installed-entry distinction. Descriptor index is
`96*layer + 8*kind + projection`; there are `96*NUM_LAYERS` entries.
Unaligned/unsupported accesses fail explicitly.

| Address | Read | Write |
|---|---|---|
| 0x0000 | Parent version 0x02000001 | Error |
| 0x0004 | bits 0 ready, 1 busy, 2 committed, 3 sticky fault | Error |
| 0x0008 | Zero | bit0 invalidate, bit1 recommit, bit2 clear fault/load fault |
| 0x000c | Parent storage mode bit0 (1 BF16, 0 AWQ) | Select mode, invalidate image |
| 0x0010 | Selected descriptor index | Select descriptor |
| 0x0014 | Installed kind | Stage kind 0..11 |
| 0x0018 | Installed layer | Stage layer |
| 0x001c | Installed projection | Stage projection 0..7 |
| 0x0020 | Installed base low | Stage base low |
| 0x0024 | Installed base bit32 | Stage base high (0 or 1) |
| 0x0028 | Installed length | Stage length |
| 0x002c | Error | 1 installs staged entry; 0 no-op |
| 0x0030 / 0x0034 | Token-cycle low / held high | Error |
| 0x0038 / 0x003c | Physical read-beat low / held high | Error |

Control bits 0 and 1 together, upper control bits, invalid mode values and
busy mutations are errors. Clear-fault may accompany invalidate or recommit.
Reads of an absent selected descriptor fail. Install checks identity, selected
index, exact padded length, 64-byte base alignment, physical end and overlap;
length zero removes an entry. Install invalidates the image. Recommit scans
every entry, requiring exactly the needed descriptors, valid load state and
initialized memory interface. Successful recommit optionally clears fault.
Loading modifies/invalidate image ownership. An execution/load fault is sticky.
Parent high-counter reads without snapshots return live high words; this legacy
behavior does **not** apply to the stricter HT2 counters.

Parent tensor kinds: 0 embedding, 1 projection weights, 2 AWQ packed zeros,
3 AWQ FP16 scales, 4 Q/K/V biases, 5 attention norm, 6 FFN norm,
7 final norm, 8 scratch, 9 K, 10 V, 11 parent RoPE storage.
Projections 0..6 are Q,K,V,O,gate,up,down. Global kinds 0,7,8,11 use
layer/projection zero; kinds 1..3 use seven projections, kind4 three,
and per-layer norms/K/V projection zero. Lengths are padded to 64 bytes.
Native HT2 must retain staging/install/recommit semantics while using native
tensor-format boundaries; parent Q16 scratch/KV or host RoPE answers cannot
replace those boundaries.

## HT2 CSR map and ownership

| Address | Function |
|---|---|
| 0x0100 | bits1:0: 0 BF16, 1 FP16, 2 W4-to-BF16, 3 invalid; bit2 speculation; bit3 sparsity |
| 0x0104 | Nonnegative finite BF16 magnitude threshold in bits15:0 |
| 0x0108 | Read-only initialized,image_valid,busy,sticky_error in bits0..3 |
| 0x010c | Reserved |
| 0x0110 / 0x0114 | Accepted committed tokens, low/high |
| 0x0118 / 0x011c | Completed successful batch steps, low/high |
| 0x0120 / 0x0124 | Physical DDR read bytes, low/high |
| 0x0128 / 0x012c | Eligible dense down-projection weight bytes, low/high |
| 0x0130 / 0x0134 | Avoided down-projection weight bytes, low/high |
| 0x0138..0x014c | Reserved aligned words |

Reserved reads return zero; writes error without mutation. Other unsupported and
unaligned accesses error. Reset configuration and threshold are zero; upper
configuration/threshold bits must be zero. Negative zero threshold is legal.
Configuration/threshold writes during execution, loading or pending results
error. Format changes invalidate image and prefix, requiring recommit.
Busy includes loading and pending results.

Each HT2 counter low read acquires that counter's complete 64-bit snapshot on
the accepted CSR transaction. Matching high returns held high and consumes
ownership; high without ownership returns zero/error. Responses hold under
backpressure. Counters wrap modulo 2^64 and reset only with reset.
DDR counters cross through acknowledged full-width snapshots.
Count physical response beats, 64 bytes each, including metadata/replay/rejection.
Count accepted tokens/steps at completed result handshakes. Eligible bytes count
unique dense bursts per actually evaluated logical projection, not replay.
Avoidance is finalized only after replay; replayed skipped bursts avoid zero.
Actual down-projection bytes, including extra replay, are separately measured.

## Cycle & Degenerate-Boundary Table

All transfers use **pre-edge** `valid && ready` and payload. The state listed
after an edge is not a second transfer at that edge.

| Boundary | Required behavior |
|---|---|
| Reset asserted | Asynchronous cancellation; all public outputs, including ready and payload, zero |
| Reset release | Two-flop synchronized release per domain; first release edge cannot accept work |
| Output stall | Valid, error and payload hold until pre-edge handshake |
| Sparse/verifier request at E | Captured after E; response valid after E+1, never after E |
| Nonskipped sparse request | Exactly one DMA handshake before decision response |
| Sparse exact end | Exclusive byte end 2^33 legal; greater end errors without DMA |
| Count 1/tree root | Parent 4 legal; correction can be sole output |
| Four matching nodes | Exactly four outputs, no fifth bonus |
| Duplicate matching children | Lowest slot index chosen |
| MAC first && last | One-beat transaction legal; all contexts start +0 |
| MAC product | Operands after E, partial product E+1, rounded FP32 product E+2 |
| MAC add | Samples E+3, retires E+6; same-edge context forwarding required |
| MAC last at E | Reductions E+7..10, E+11..14, E+15..18; output after E+19 |
| MAC bubbles/stalls | Metadata follows enabled advances; cannot change column context phase |
| MAC output consumed | Next dot admitted only after prior output handshake |
| Non-power-of-two tile/window | Explicit terminal wrap, never binary-mask wrap |
| Singleton sequence/vocabulary/group/tile/window | No negative selects, zero-width dimensions or hidden extra beat |
| Final response plus new_sequence/reset | Reset cancels all ownership; sequence flush cannot reuse provisional KV |
| Fault plus fault-clear | New fault wins; no successful committed-KV update on failure |
| Counter increment plus low read | Snapshot owns pre-edge complete value |
| Projection preflight | Exact padded lengths and extended exclusive ends checked before any weight or metadata request |
| Projection sparse skip | A logical MAC beat is retained even when its physical burst is removed |
| Projection nonzero skip | Required weight read completes before admitting the dense product; no approximate downstream state is exposed |
| Operator slots with unequal scalar latency | Early divide/exp/trig responses remain held until every participating controller response is available |
| Provisional KV layer | Read ownership appears only after the final legal ascending-column write |
| Provisional KV read plus layer write | Reading the layer being written returns an explicit error; unrelated completed layers may be read concurrently |
| Provisional KV retain mask zero | Legal discard of every draft, including correction-only commits |
| Provisional KV flush | Cancels pending responses and all ownership; RAM contents need not reset |
| Attention query fill | Exactly NUM_Q_HEADS*HEAD_DIM ascending selected-format four-slot words |
| Attention invisible node | No scalar-context update, score reduction, exponential sum or KV read for an invisible source |
| Attention equal scores | Strict-greater maximum replacement retains the earliest visible position, including signed-zero ties |
| Attention output | Ascending head then dimension; valid/data/slots/index hold until handshake |
| KV read plus response | Collector accepts a response coincident with its physical request handshake |
| KV layer copy | Entire provisional layer is collected and validated before the first physical write |
| KV copy final write | Completion follows the final acknowledged K/V write, not just request acceptance |
| KV copy failure | Prefix ownership is unchanged; partial raw writes remain outside the committed prefix |
| KV copy and read | Layer copies serialize against attention reads; copy has priority when both are presented while idle |
| HT2 CSR response | One outstanding transaction; forwarding and CDC waits cannot overwrite a stalled response |
| DDR counter snapshot | Source holds all 64 bits before synchronized acknowledgement; core never synchronizes counter bits independently |
| Decoder matrix panel | Exact ascending panel index, active-row mask and slot mask are checked before storing rows |
| Decoder residual read | Synchronous residual read precedes the four-slot registered addition request |
| Ordinary-token output | All logits are buffered internally until every token KV layer is acknowledged; external indices ascend from zero |
| Ordinary-token publication | Final external logit handshake publishes the new prefix and increments accepted tokens; done is high in the following cycle |
| Draft publication | All selected nodes are copied in parent-before-child order, all layers per node, before atomic commit |
| Corrective token | Selected nodes are copied first; a fresh provisional transaction evaluates correction against that reserved prefix, then copies every correction layer |
| Failed KV publication | Physical rows beyond the old prefix may have changed, but old prefix length/target remain unchanged and no successful commit is emitted |
| Sequence flush | Flush wins over inference/result handshakes; ready/valid are suppressed during flush and in-flight work drains before retry |
| Image recommit | Installed descriptor checks precede real model-tensor reads; a host flag cannot assert finite-image ownership |
| DDR command/first response | A physical response coincident with request acceptance is collected exactly once |
| DDR reset debt | Logical owners/mailboxes reset; a power-up-initialized one-word physical debt ledger survives logical reset until every old accepted bus response drains |
| CSR plus inference presentation | CSR presentation reserves admission priority; neither ordinary nor batch input handshakes at that edge |
| Load acquire plus inference presentation | An already visible load-acquire request blocks inference; a request still crossing clocks waits for any accepted inference to finish |
| Load beat | Captured on ddr_clk with pre-edge load_valid && load_ready; next load beat waits for the preceding physical write response |
| Load last or fault | load_done pulses on ddr_clk only after the final write acknowledgement, or after rejecting an invalid beat without traffic; load_error remains sticky until explicit clear |
| Load ownership return | Core remains busy until acknowledgement of the DDR-domain completion pulse returns; image recommit cannot race a pending upload result |
| Fault clear plus pending load acquire | The DDR domain can acknowledge clear before granting the waiting upload; clear cannot deadlock behind the ungranted request |
| DMA arbitration | Local request handshake captures all payload fields; selected owner and request remain registered through transport acceptance and the last response |
| Streaming DDR return | Each owned physical beat is written once into the response FIFO; final-read and accumulated-error tags cross with its payload |
| FIFO reservation | One owned transaction has at most 255 beats; its 512-entry response FIFO can absorb the entire unbackpressurable physical burst |
| FIFO read/stall | Synchronous RAM prefetch owns a separate output register; a stalled output cannot be overwritten by a later FIFO word |
| Panel prefetch | A 128-column ring reserves at most 64 columns per request, only with at least 64 free entries; synchronous column reads release ring storage into a held output register |
| Panel tail | The final request contains exactly the remaining columns, with one W4 or two dense beats per column; no read crosses the preflighted panel end |
| Dense array issue | Activation RAM read and broadcast-word capture use the same column handshake; their held operands advance together into the array |
| AWQ group transition | Stop column admission at the group boundary; previously admitted dequantization/MAC work drains while the next group's zeros/scales are fetched |
| AWQ metadata/data stall | Four dequantization stages and their activation/column tags share the same advance; a blocked array cannot mispair a later activation |
| RMSNorm scaling | After inverse computation, two separately rounded three-stage FP32 multipliers stream x*inverse then product*gamma; gamma/index tags freeze with both pipelines |
| SwiGLU interleave | Ascending input/output indices select engine index[2:0]; eight independent four-slot engines execute without changing per-element arithmetic order |
| SwiGLU minimum geometry | INTERMEDIATE_SIZE=8 gives one vector per engine, with no zero-length engine or hidden extra input |
| SwiGLU abort | Stop public input/output admission, cancel every engine, and finish only after all engine ownership drains, including while abort remains asserted |
| RoPE trig reuse | The first head computes every pair's sin/cos in RTL; later heads read only that command's completed cache entries; reset or a new command requires first-head recomputation |

Reset cannot relabel stale DDR responses as new requests: native integration
must retain reset-safe drain/epoch ownership. Memory data need not reset.
Synchronous storage ports do not acquire asynchronous-reset data writes.
`done` is one clock following final accepted result, never early.

## Connected native integration

The ordinary, batch, commit, logit and CSR interfaces use `clk`. The load
interface and Avalon interface use `ddr_clk`, preserving the parent clocking
contract. Both domains asynchronously assert reset and synchronize release.
No frequency ratio or relative phase between the clocks is assumed.

`anvil_q1_ht2_top.u_execution` contains the native decoder, causal KV routing
and speculative verifier. The decoder's learned projection path instantiates
the four-slot MAC array and sparse DMA predicate; its weights and activation
vectors are actual DDR/model data, not externally supplied operator answers.
The top's DMA mux has four owners: execution reads, execution KV writes,
descriptor-validation reads and image writes. It captures one complete
request and routes every response to that owner. Loading and descriptor
mutation cannot acquire execution ownership concurrently.

The image loader holds a whole-upload reservation. An acquisition invalidates
the image and prefix before any write. Individual beats cross through held,
acknowledged mailboxes, preserve all byte enables, and issue one aligned
64-byte write each. A new beat waits for the previous write's acknowledgement;
zero byte enables are legal as in the parent. Last and errors cross back to
the DDR domain, where completion pulses and a further acknowledgement returns
the reservation to the core. An unaligned load is rejected without a write.
The greatest legal aligned address is `0x1ffffffc0`, whose exclusive end is
exactly `2^33`. Load errors do not make an image valid. Explicit error clear,
descriptor installation and a successful finite-data recommit remain required.

Inference admission is suppressed by CSR presentation, a pending CSR response,
descriptor configuration/validation, a visible load acquisition, active
upload, transport quarantine or sticky error. CSR accesses during execution
can still read counters/status; mutation requests receive explicit errors.
New faults take priority over fault clear. The inherited physical-read-beat
counter crosses as acknowledged whole-width snapshots; its descriptor endpoint
then holds low/high read pairs with parent semantics. HT2 physical-byte reads
use their separate on-demand acknowledged counter snapshots.

The request crossing remains an acknowledged mailbox, with one complete
transaction owned until its final core response handshake. The DDR response
crossing is `anvil_q1_ht2_response_fifo`: a 512-entry, 515-bit dual-clock RAM
FIFO carrying write/read identity, last, error and data. Binary pointers
address RAM; registered Gray pointers cross through two-flop synchronizers.
The destination has a synchronous registered RAM read and holds its output
until consumed. Physical Avalon responses cannot be backpressured, so FIFO
capacity is reserved structurally by the one-transaction/255-beat bound,
not by assuming the core is ready. Overflow or an unexpected response
quarantines the transport. Logical reset cancels FIFO/client ownership while
the reset-persistent physical-debt ledger drains stale physical responses.
FIFO CDC constraints and fitted implementation remain native-gate obligations;
static parsing does not establish CDC or memory inference.

The 29 compatibility modules reside in `rtl/` under their original names.
Their fixed-point formats, interfaces, arithmetic and cycle sequencing remain
the parent contract. Five delivery copies move helper-function evaluation
outside clocked processes without adding registers or changing input samples,
to avoid synthesis treating function-local temporaries as asynchronous-reset
state. The supplied reference directory is unchanged. Compatibility and
reference sources must never be selected together in a compilation.

## Frozen arithmetic and decoder ordering

All primitives use RNE, gradual underflow, signed zero, infinity and canonical
FP32 quiet NaN `0x7fc00000`. BF16/FP16 multiplication rounds once to FP32 in
three registered stages; four-stage FP32 addition rounds separately (no FMA).
Primitive special-value coverage does not allow nonfinite model/decoder data:
execution must error without commit.

AWQ shift is `{lane[0],lane[2:1],2'b00}`. Unsigned q/zero nibbles form signed
q-z; multiply by finite nonnegative FP16 scale in FP32, then round once to BF16.
No Q16 conversion is allowed in the native decoder.

Projection columns ascend logically. Column j accumulates into context j mod4;
contexts start +0 and reduce `((c0+c1)+c2)+c3`. Add bias once afterward.
Skipped physical reads must not remove logical column phase. Every projection
uses the connected four-slot array. Attention dot/value products use the same
four-context ordering, over head dimension/visible absolute position.
Norm and softmax sums instead use ascending FP32 left folds.

Residuals, reductions, scores and nonlinears are FP32. Embeddings expand exactly.
Every learned matrix input rounds once to the selected 16-bit format; W4 uses
BF16. Q/K/V stay FP32 through bias/RoPE and then round at attention/KV boundary.
Normalization weights expand exactly. Per-layer order is attention RMSNorm,
Q/K/V+bias, split-half RoPE, causal GQA, O projection, residual add, FFN RMSNorm,
gate/up+bias, SwiGLU, down, residual add. Final RMSNorm precedes output head.

RMSNorm: ascending `sum=add32(sum,mul32(x_i,x_i))` from +0;
`mean=div32(sum,H)`, `u=add32(mean,RNE32(1e-6))`, `root=sqrt32(u)`,
`inv=div32(1,root)`, `y_i=mul32(mul32(x_i,inv),gamma_i)`.
Validate official epsilon=1e-6 and RoPE base=1e6 rather than silently substitute.
RoPE pairs j with j+D/2, using independently checked correctly rounded
configuration constants `theta^(-2*j/D)` and RTL sin/cos of the separately
rounded position-frequency product. First component is q0*cos - q1*sin;
second is q1*cos + q0*sin, each product/add separately rounded.

GQA uses floor(h/(Q/K)) with bounded control/constants, not runtime division.
Only committed prefix/self/ancestors are visible. Find earliest maximum,
then ascending left-fold sum of exp(score-max), then div each exponential by
sum. Round probability once to selected format before value product.
No sentinel score or online-softmax reassociation replaces these operations.
SwiGLU uses stable sigmoid: gate>=0 -> 1/(1+exp(-gate));
gate<0 -> exp(gate)/(1+exp(gate)); multiply gate by sigmoid, then by up,
then round once before down projection. Argmax is ascending with strict greater.

Division is bounded sequential significand quotient generation; square root is
bounded digit recurrence with exact remainder/sticky decisions. Each finite
request completes within 512 enabled clocks, excluding output backpressure.
No runtime combinational `/` or `%`, `real`, black box or host answer.

Exp completes within 2048 enabled clocks: x<=-104 -> +0, x>=89 -> +infinity;
otherwise n=nearest-even-int(mul32(x,RNE32(1/ln2))), subtract separately rounded
n*LN2_HI and n*LN2_LO, where HI=0x3f317200 and LO=RNE32(ln2-exact(HI)).
Degree-12 Taylor coefficients are RNE32(1/k!), descending Horner with separate
multiply/add, followed by one RNE exact-power-of-two scale.
Mathematical error bound is `2^-15*exp(x)+2^-149`.

Sin/cos complete within 2048 enabled clocks for |angle|<=32768.
Quadrant and reduced FP32 argument decisions use bounded multiword interval
arithmetic with >=256 fractional pi bits, refining to unambiguous RNE decisions
or explicit numerical error. On reduced r use degree-eight polynomials in r*r:
sin=r*sum((-1)^k*r^(2k)/(2k+1)!), cos=sum((-1)^k*r^(2k)/(2k)!),
descending Horner and separately rounded operations, then exact quadrant mapping.
Each absolute mathematical error must be <=2^-18. Position-dependent host tables
are forbidden.

## Sparse and speculative leaves

`anvil_q1_ht2_sparse_dma` takes one column's four BF16 activations, slots,
threshold, aligned 33-bit address and nonzero eight-bit burst count.
It skips iff all participating finite magnitudes are <= threshold. Empty slots,
nonfinite participating activations, negative-nonzero/nonfinite threshold and
invalid address/burst cause decision_error with no DMA.
FP16 predicate conversion must retain original-nonzero information separately.
Every skipped nonzero original activation unconditionally triggers dense replay
before commit unless a later independently admitted certificate proves otherwise.
No heuristic logit margin is authorized.

## Internal native projection layout and interfaces

`anvil_q1_ht2_projection` connects the sparse decision unit, a bounded
one/two-beat metadata/sparse response collector, dense panel prefetch,
64 parallel AWQ dequantizers and the complete four-slot/64-lane MAC array.
Its command latches format, slots, dimensions,
descriptor intervals, down-projection identity and sparse controls. Inputs
are exactly HIDDEN_SIZE or INTERMEDIATE_SIZE; output rows are bounded by the
largest configured hidden/intermediate/vocabulary dimension. All address
preflight and input-vector finite checks precede memory traffic.

The internal native layout is panel-major, then ascending input column, then
64 output rows. Every panel has 64 physical rows, including a partial final
panel. Dense BF16/FP16 columns occupy 128 bytes, least-significant row first.
W4 columns occupy one 64-byte burst, with eight AWQ-permuted eight-row packed
words in the low 32 bytes and padding in the remaining bytes. This padding
is real traffic, not an asserted fourfold packing benefit. Each panel/group
has a 64-byte zero record (eight packed words in the low 32 bytes) and a
128-byte record of 64 finite nonnegative FP16 scales. Metadata records follow
ascending groups within each panel. Required descriptor lengths are exactly
`panels*inputs*(format==W4 ? 64 : 128)`,
`panels*groups*64` and `panels*groups*128`, respectively, where
`panels=ceil(outputs/64)` and `groups=inputs/GROUP_SIZE`.
Padding is charged and inactive rows do not participate in arithmetic.
The native descriptor endpoint, decoder and connected top/image loader use
these lengths. Verifier-owned checkpoint conversion must reproduce this
layout; installed descriptors alone are not a validated image.

The activation stream supplies all four selected-format values for each
ascending input column once, plus four original-arithmetic-nonzero bits.
Those bits survive selected-format and FP16-to-BF16 predicate underflow.
An encoded nonzero also forces the nonzero classification, regardless of
the accompanying bit. All active slots share each collected weight burst.
Skipped columns still send a zero-weight logical beat through the array, so
column modulo-four contexts and transaction first/last do not change.

With sparsity disabled, up to 64 contiguous columns are fetched per request,
with an exact shortened tail. A 128-column synchronous ring retains
unconsumed columns. Credit reservation precedes every request; one native
column uses two beats and one W4 column uses one beat. Broadcast words and
synchronous activation reads enter the same held issue stage. W4 activation/
column tags follow the four-stage dequantization pipeline. Group metadata
changes only after all inputs of the old group have entered dequantization;
it cannot change those already captured products. Sparse operation instead
waits for the connected predicate before each physical weight request and
never fetches a would-be skipped column speculatively.

Only the down-projection command identity enables eligible-byte accounting;
it is independent of whether sparse mode is enabled. Eligible weight bytes
are reported once per original column/panel, avoided bytes only for a
finalized exact-zero skip, and replay bytes when the replay read is accepted.
These event deltas are not physical-read counters: actual accepted response
beats must be counted by the DDR owner.

`cmd_finite_weights` is an internal image-ownership guarantee, never a
host-supplied accuracy certificate. It may be asserted only after hardware
has validated the corresponding complete image, including AWQ metadata.
Without that guarantee, even a zero skip is replayed. A skipped original
nonzero always replays the weight column before its product is accumulated.
No speculative arithmetic result is released before this dense repair.
Replay eliminates avoidance for that column. For validated finite weights,
an exact-zero input contributes only signed-zero products; contexts start
at +0 and separately rounded finite FP32 sums cannot acquire -0 from such
an addition, so the zero-weight logical beat preserves the dense accumulator.
This reasoning remains subject to independent directed verification.

The projection command completes only after all panel result handshakes.
An abort cancels local MAC/dequant/sparse ownership but drains an already
accepted external burst before completing with error. The burst collector
accepts response data coincident with its request handshake and holds the
assembled response under backpressure. Its upstream DDR owner must still
provide reset-safe draining/epochs; this local collector does not solve
stale external responses after a whole-device reset.

## Saved operator and provisional-state interfaces

`anvil_q1_ht2_scalar` serializes internal FP32 add, multiply, divide, square
root, exp and sin/cos requests (opcodes 0..5). Nonfinite decoder operands or
results produce an explicit error. Primitive modules retain their separate
IEEE-special-value behavior.

`anvil_q1_ht2_rmsnorm` takes one command for four masked slots, then HIDDEN_SIZE
ascending FP32 vectors and common selected-format gamma values. Four scalar
paths preserve each slot's ascending square/add left fold, followed by mean,
epsilon addition, square root, reciprocal, x*inverse and gamma multiplication.
It stores input/gamma vectors in synchronous, non-reset RAM and returns
ascending FP32 vectors. Final scaling uses two separate three-stage
multipliers with common stall and gamma/index tags, permitting one vector
per enabled clock after fill. The ordered sum is not reassociated to obtain
that overlap. It does not insert a matrix-input rounding boundary.

`anvil_q1_ht2_swiglu` takes ascending gate/up FP32 vectors for
INTERMEDIATE_SIZE elements. It uses the frozen sign-dependent stable sigmoid
sequence and returns FP32 intermediates, their once-rounded selected-format
encodings and original nonzero flags. Nonfinite narrowing is an execution
error, not an output transfer.
Eight independent four-slot engines execute interleaved element indices;
each receives exactly INTERMEDIATE_SIZE/8 vectors. Both public directions
remain ascending and independent, so inputs may advance while earlier
outputs are pending. Abort cancels and drains every engine before done.

`anvil_q1_ht2_rope` takes four positions and streams split-half pairs, in head
order then ascending j. It returns both FP32 rotated values and their
selected-format encodings, with logical first/second indices. Position-
independent ROM constants cover every even HEAD_DIM from 2 through 64.
They encode RNE32(1000000^(-2*j/HEAD_DIM)), generated with 180-decimal-digit
constant evaluation and rational ties-to-even packing, not position-dependent
host answers. The first head computes each pair's trigonometry in RTL;
later heads reuse a command-local synchronous cache, invalidated by always
recomputing the first head on the next command. Independent high-precision
checking is still mandatory.

`anvil_q1_ht2_fp32_sincos` reduces the exact FP32 input against a 320-fractional-
bit interval for pi/2. Sixteen quotient-bit decisions use eleven 32-bit
subtract/copy steps each, avoiding a combinational wide divider/subtractor.
It bounds the nearest-quadrant decision using the full interval and converts
both residual-magnitude endpoints independently to FP32 with guard/sticky
information. Disagreeing decisions, a domain violation or an unresolved
interval raises an explicit numerical error. Only agreeing endpoints reach
the separately rounded degree-eight Horner sequencer and exact quadrant
mapping. Signed zero is handled directly. No simulator real arithmetic or
position lookup is used. Domain coverage, exact reduction, mathematical error,
completion bound and fitted timing remain independent obligations.

`anvil_q1_ht2_tree_mask` validates count, preceding-parent topology, prefix
ownership and sequence bounds, then returns per-node absolute positions and
four ancestor bits per node, including self. Prefix positions are separately
visible; these bits never make a sibling visible. Its response is registered
after E+1 for a request accepted at E and holds under backpressure.

`anvil_q1_ht2_provisional_kv` stores four nodes' selected-format K/V pairs for
every layer in synchronous block-inference RAM. A begin command establishes
slot ownership. Ascending first..last writes make a complete layer readable;
partial, malformed and stale accesses return explicit errors. A retain command
can only remove owned nodes, including removing every node. It cannot confer
committed ownership. Flush/reset cancels all ownership without clearing RAM.
Committed DDR KV, causal attention traversal, selected-node copying and
corrective-token state publication require connected decoder/top control.
The saved transaction modules below implement raw KV transport and layer copying;
they do not independently confer committed-prefix ownership.

## Saved attention, KV transport and control interfaces

`anvil_q1_ht2_attention` accepts a slot mask, committed prefix length, absolute
node positions, ancestor masks and format. The prefix length is a count: prefix
positions are `0..length-1`. An ordinary first token has length zero, slot0 at
position0 and only its self ancestor bit. The scheduler must supply validated
tree-mask results for a batch. Attention additionally checks self/preceding
ownership, nested ancestor masks, distinct visible positions and that each
node's ancestors occupy exactly the consecutive positions after the prefix.
It rejects out-of-range positions before accepting query words or reading KV.

Queries arrive in head-major, dimension-ascending order as four selected-format
16-bit words. The command owns the query RAM until completion. The attention
controller uses a single outstanding internal KV request: source class,
provisional node, absolute position, mapped KV head and head dimension.
The responding KV subsystem must return the actual selected-format key/value,
not a computed score or host attention result. Responses can coincide with
request acceptance; otherwise request ownership persists until response.
Nonfinite operands/results and KV transport/ownership faults fail execution.

Within each head, the controller traverses committed positions and then
provisional nodes in ascending node order. Each slot participates only for its
prefix/self/ancestors; earlier-parent topology makes that slot's participating
node order an ascending-position order even when siblings have equal or lower
positions than a preceding node. Every source dot accumulates head dimensions
into four FP32 contexts by dimension low bits, reduces `((c0+c1)+c2)+c3`
and multiplies by a separately computed `div32(1,sqrt32(RNE32(HEAD_DIM)))`.
It completes the maximum pass before exponentiation, preserves the earliest
position on ties, folds exponentials in ascending visible position, divides
each by the finished sum and rounds probabilities once to the selected format.
The value pass updates contexts by absolute-position low bits, excluding
invisible positions entirely, before the same ordered reduction.
FP32 outputs stream in ascending head/dimension order. These dot/value products
are native floating point; learned projections remain assigned to the connected
four-slot projection array rather than this scalar sequencer.

Score/exponential/probability arrays are synchronous inferred RAM, reused for
each head. Scalar paths run across the four slots with held-response rendezvous,
not four serial full attention invocations. Latency depends on visible positions,
scalar completion, KV traffic and backpressure; no measured throughput or fitted
timing is implied. Abort drains an owned KV response before error completion.
The containing memory interface must enforce reset epochs/draining: resetting
this controller alone does not distinguish an old untagged DDR response.

Native per-layer committed K/V descriptors each have
`MAX_SEQ_LEN * stride` bytes, where
`stride = 64 * ceil((2*NUM_KV_HEADS*HEAD_DIM)/64)`.
Each absolute-position row is head-major, dimension-ascending, selected-format
16-bit values followed by zero padding through its 64-byte-aligned stride.
K and V use separate nonoverlapping descriptors. This is native HT2 layout,
not the parent's Q16 KV representation. Descriptor installation must enforce
global tensor nonoverlap. Arithmetic preflight uses extended exclusive ends;
an interval ending at `2^33` remains legal.

`anvil_q1_ht2_kv_reader` checks those descriptor lengths, alignment, physical
ends, prefix ownership, position/head/column range before issuing reads. It
caches one matching pair of 512-bit K/V lines using full physical-address tags;
adjacent dimensions in the same lines reuse those actual response registers.
Descriptor/image changes and sequence/copy invalidation must invalidate the
cache. The module checks the selected values for nonfiniteness, retains an
outstanding read across abort until its response drains, and holds its result
under backpressure. Image loading cannot run concurrently with active reads.

`anvil_q1_ht2_kv_writer` accepts one reserved, uncommitted position and a whole
layer's ascending K/V words with exact first/last markers. It checks bounds,
descriptors and finite encoding, collects the complete layer in synchronous
storage and zero-pads its final beat before any write. Every emitted request
is one 64-byte write with all byte enables set and requires one write response;
the containing Avalon adapter supplies burstcount1. Key then value are written
for each beat. Errors/abort drain an accepted request and return failure.
No writer output advances prefix ownership. A failed transfer may leave raw
bytes at a reserved position, which remain invisible to committed reads.

`anvil_q1_ht2_kv` connects that reader/writer to the provisional RAM. It routes
attention reads by their actual prefix/provisional source, preserving layer
and node ownership checks. A copy command names one selected node, layer and
reserved destination position; it reads the completed provisional layer and
feeds the native writer, rejecting missing or nonfinite state. Copy and
attention-read transactions serialize, with command, copy, then read priority
while idle; provisional write handshakes remain explicit. Flush/abort discards
provisional ownership and drains accepted external transactions before error
responses. The decoder/top must copy every layer of every selected token,
complete any correction forward pass, publish the committed prefix atomically,
and only then admit a dependent batch. Layer-copy success alone is not a token
commit, speculative rollback proof or correction-state update.

`anvil_q1_ht2_control` implements the HT2 CSR overlay and forwards the
inherited `0x0000..0x003c` map, except mode address `0x000c`, to the descriptor endpoint.
It implements all five low/high counter pairs, reserved/read-only/unaligned
errors, held CSR responses, format/threshold validation and busy interlocks.
Counter event inputs must be actual completed token/batch handshakes and
finalized logical dense/avoided-byte deltas. Format changes pulse both image
and prefix invalidation. The top must prevent a simultaneous configuration
mutation and new inference/image-load acceptance; accepting an inference on
the same edge using the old configuration is not authorized by the overlay.
The overlay handles inherited mode reads/writes against the same authoritative
format register: zero selects W4-to-BF16, one selects dense BF16 (or retains an
explicitly selected FP16 format). Both dense formats read as one. Every accepted
legacy mode write invalidates image/prefix, including a same-mode write.
The native descriptor endpoint deliberately rejects a directly routed mode
write: integration must not create a second independently mutable format state.

## Connected native decoder and execution transaction

`anvil_q1_ht2_decoder` connects the shared four-slot projection array to
RMSNorm, Q/K/V biases, split-half Q/K RoPE, provisional-KV stores, causal GQA,
O/residual, FFN RMSNorm, gate/up, SwiGLU, down/residual, final RMSNorm and the
tied output head. Per-slot residuals remain FP32 in synchronous RAM.
Every learned projection feeds all active slots from one traversal. Projection
panels remain owned until each valid row has been stored/processed; this also
prevents a following weight request from racing a bias read.
The native argmax checks finite logits, traverses ascending vocabulary indices
and replaces only on strict greater-than, retaining the smallest ID on ties.

The official tied embedding/output matrix occupies global kind0, layer0,
projection0. It uses the dense panel layout above with token IDs as output rows
and hidden dimensions as input columns. Its exact length is
`ceil(VOCAB_SIZE/64)*HIDDEN_SIZE*128`. Byte offset for embedding token `t`,
hidden dimension `j`, is
`floor(t/64)*HIDDEN_SIZE*128 + j*128 + 2*(t mod 64)`.
The RTL implements the power-of-two quotient/remainder by slicing/shifts.
Embedding reads expand the selected 16-bit value exactly. The output head
uses the same descriptor and dense array path, so no additional independently
quantized or host-computed head is introduced. W4-to-BF16 quantizes the seven
decoder matrices, not this shared embedding/head tensor. Embedding/head,
normalization weights and Q/K/V biases remain BF16 in W4 mode; scales remain
FP16. FP16 mode selects FP16 for every dense stored-format tensor.
Conversion must preserve the official tied-weight identity and publish these
format boundaries rather than quantizing the tied head implicitly.

Bias vectors and normalization vectors are ascending 16-bit elements padded
through a 64-byte boundary. Q/K/V bias lengths are respectively
`pad64(2*HIDDEN_SIZE)`, `pad64(2*NUM_KV_HEADS*HEAD_DIM)` and the same KV length.
All normalization lengths are `pad64(2*HIDDEN_SIZE)`.
The parent's Q/K/V bias descriptors remain mandatory; an absent checkpoint bias
must be represented by an explicit zero tensor, not a missing unchecked fetch.
No other projection bias is configured by this ABI.

`anvil_q1_ht2_execution` supplies the connected tree mask, decoder, provisional/
committed KV router and speculative verifier. It never accepts a batch without
an internally cached committed-prefix target. Ordinary commands require
`token_pos == committed_prefix_length`; after reset/sequence flush this is zero.
A sequence flush suppresses command/result handshakes and invalidates prefix
ownership, so a coincident token must be retried after flush. Simultaneously
presented ordinary and batch commands are accepted only as an explicit error,
not two decoder jobs. Disabled speculation, illegal count/IDs/topology, missing
prefix and sequence overflow fail without successful publication.

Ordinary logits are stored in one vocabulary-sized synchronous 32-bit RAM.
After a successful forward pass, all token layers are copied to reserved DDR
rows. Only then are buffered logits emitted externally. Their final handshake
publishes prefix length/target and contributes one accepted token. A batch emits
no ordinary logits. The verifier's mask selects draft nodes in ascending node
order, which is also parent-before-child order. Every layer of each selected
node is copied before moving to the next position. If the returned token list
contains a correction, a new single-slot provisional transaction evaluates it
against the reserved selected-node prefix, then copies every correction layer.
The final reserved length must equal old prefix length plus emitted count.
The one atomic commit handshake publishes the new prefix/target and contributes
the accepted-token count plus one completed batch step.
Public `done` is one clock immediately following the final logit/commit
handshake. Faulted batches return `commit_valid,commit_error` with count/payload
zero and do not increment success counters. Ordinary forward/copy failures
complete with `done,error` without releasing buffered logits. Cancellation of an
already emitting result discards the remaining stream without publication.
Raw partial writes remain outside the old
committed prefix. Sequence cancellation drains accepted transactions before
another command can reuse storage.

## Native descriptor validation and DDR transport

`anvil_q1_ht2_descriptors` preserves the inherited descriptor-index identity,
staging versus installed-entry reads, zero-length removal, global interval
nonoverlap, exact-end legality and recommit scan. Dense/W4 matrix and metadata
lengths use the native panel formulas; K/V lengths use the native row stride.
Scratch kind8 and compatibility RoPE kind11 descriptors retain their inherited
lengths and required presence, but native arithmetic does not consume their
contents. They do not provide residual state or position-dependent trig answers.
Other absent/extra entries fail the full descriptor scan, including stale AWQ
metadata in a dense image.

Successful recommit requires an initialized transport, no loading/failure,
unchanged format and all required descriptors. The endpoint then actually reads
every model-tensor beat (kinds0..7), including packed W4/zero metadata, before
asserting image/finite ownership. Every dense stored halfword, including padding,
must be finite in its selected format. FP16 scales additionally must be
nonnegative; negative zero is accepted. Packed nibbles/zero records need no
floating-point classification. Finite FP16 scales times the bounded signed
four-bit difference produce finite BF16 weights. A read/format/load/numerical
error rejects recommit and retains explicit CSR error/sticky fault.
Loading, installation, invalidation and recommit invalidate prefix ownership;
only successful completed validation asserts `finite_image`.
The image loader/top must interlock loading and new commands against descriptor
validation and CSR mutations, including the same acceptance edge.

`anvil_q1_ht2_transport` serializes core requests through acknowledged
bundled-data mailboxes. It buffers an entire accepted read burst of 1..255 beats
in synchronous DDR-domain RAM before forwarding held responses to the core;
writes are exactly one beat with an acknowledged write response. All command
intervals use extended exclusive ends. Payloads/ready/valid/requests are zero
during reset. The core admits one command until its final response handshake.
Top-level client arbitration and the image loader remain to be connected.

The physical Avalon interface has no response tags or response backpressure.
Consequently reset cancellation cannot erase the count of requests already
accepted by memory. A single ten-bit, FPGA-configuration-initialized storage
word records physical response debt and a fail-closed protocol-fault bit.
It is the deliberately retained storage exception, not logical client
ownership: it is updated on actual Avalon handshakes/responses even while
logical reset is asserted. Logical DDR/core FSMs, counters, mailbox ownership
and buffered-result ownership asynchronously reset normally.
After reset, availability stays low until the old debt has drained; only then
can a new epoch issue traffic. No quiet-time assumption or stale-response
relabeling is used. Full cold FPGA configuration initializes this one word;
ordinary `rst_n` does not. Unexpected response types/counts are explicit
protocol faults and quarantine the transport until FPGA reconfiguration,
instead of guessing ownership. These implementation mechanisms still require
independent reset/CDC, synthesis and hardware checks; they are not timing proof.

`anvil_q1_ht2_counter_cdc` counts actual accepted DDR response beats by64 bytes
in the DDR domain. A core snapshot request crosses as a synchronized toggle;
the source captures and holds all64 bits, acknowledges that toggle, and the
core captures the held bus only after the acknowledgement synchronizer.
New requests are blocked through response consumption. This acknowledged
bundled-data transfer is not independent bit synchronization or throughput
inference. Common reset cancels snapshot ownership and resets the live counter.
Neither sequence flush nor image recommit resets it.

`anvil_q1_ht2_spec_verifier` accepts 1..4 drafts, each node's actually evaluated
target, parents and cached prefix target. Starting from prefix, choose lowest
matching child, append it and continue; if absent append corrective target and
stop. Cap output at four. Commit mask marks selected drafts only.
All used parents are root=4 or earlier index. Standalone leaf validates topology;
top additionally validates prefix, vocabulary, depth and positions.
Rejected KV is provisional and discarded. No host expectation supplies prefix.

## Verification, workload and reproduction contract

Mandatory portable commands, owned by independent Verifier:

```
python3 tests/verify.py --suite behavior
python3 tests/verify.py --suite mutations
python3 tests/verify.py --suite synthesis
python3 tests/verify.py --suite benchmark-contract
python3 tests/verify.py --suite reproduction
python3 tests/verify.py --suite full-model-benchmarks
```

These are required future entry points, not commands claimed to exist or pass in
this source increment. Installed Python3/Icarus/vvp/Verilator/Yosys are required;
tools must not be installed by Designer. L1 does not hardcode JTAG/BDF or
duplicate native timing/physical gates. Verifier freezes the exact request/result
schema in `tests/*.py` and this document before collection.

The authorized bridge command prefix is externally supplied as JSON argv in
`ANVIL_HT2_BRIDGE_ARGV_JSON`. Invoke without shell interpretation, adding
`--request <relative.json> --response <relative.json>`.
`ANVIL_HT2_BENCHMARK_INPUTS` names a project-relative immutable-input manifest
identifying official checkpoint revision, model/config/tokenizer/image hashes,
AWQ provenance, workload hash, reference artifacts and real HT/FP/A100 records.
Missing authorization/artifacts are `BENCHMARK_PREREQUISITE` failures.
Never fabricate a bridge command, checkpoint, reference or comparator.

Schema version1 requests bind a fresh nonce and workload/model/config/tokenizer/
image hashes, full geometry, top, mode, job type, prompt ID/input IDs+hash,
decode limit/EOS IDs, threshold, frozen drafts and measurement/observation
boundaries. Responses bind nonce+request hash and those identities, physical
execution kind, complete tokens/EOS reason, geometry/mode, load/prefill/decode
timings, clock/cycles, commits/steps, physical/baseline/actual/metadata/replay
bytes, replays/corrections/rejections/charged traversals, fidelity raw artifacts
and relative hash-linked native receipts. Real comparator evidence additionally
identifies device, software and matched workload/timing boundaries.
Consumer independently validates identity, exit, completeness, counter/timing
consistency, sequence equality, metrics and provenance. Simulated, reduced and
`integration_only=true` results cannot satisfy full-model acceptance.

Freeze >=2 prompts in each of factual, math, code, multilingual and long-context
domains, >=16 generated tokens unless natural EOS, with official tokenizer and
greedy decoding, in both BF16 and W4-to-BF16. Charge drafts, rejection, correction,
metadata, replay and synchronization. Report prefill separately and cold/warm
loading separately. Compact adapter runs are integration only.
For each mode/full workload require TPM>=8000, accepted-token weight reuse>=3.2,
physical FFN read reduction>=40%, positive speedups over actual HT and FP and
TPM above a matched real batch-one BF16 NVIDIA A100 80GB.
Native-format greedy commits must match dense reference 100%; operator/logit
FP64 NRMSE<=0.02 and cosine>=0.999; zero-reference max abs<=2^-18.
Primitive exactness and nonlinear mathematical bounds are separate requirements.

Independent verification must cover exhaustive 16-bit conversions, exhaustive
AWQ q/zero/lane combinations over representative scales, >=10000 cases per
multiply format and FP32 add, seeds17/43/89, divide/sqrt/nonlinear boundaries,
all256 MAC paths, exact pipeline latency/II, reset/bubbles/stalls, all legal
four-node trees/match choices, sparse threshold neighbors and honest replay.
Compact tuples `(L,H,I,Q,K,D,G,V,S,T,W)` are
`(1,8,8,1,1,8,1,1,1,1,1)`, `(2,24,40,3,1,8,8,31,9,3,3)`,
`(2,64,128,4,2,16,16,257,17,3,5)`. Default full geometry also elaborates/synthesizes.
Compiled Verilator handles larger/multiseed/multitoken work; compact Icarus
smoke is <=500000 cycles and <60s. Actual compiled arithmetic/protocol comparisons
must detect six admitted mutation classes, not compile failure or source hashes.
Yosys must retain connected arithmetic/state,256 live multipliers and zero latches.
Generic synthesis is not timing evidence. Native gates require fitted
Quartus17.1 <=10ns, WNS>=0, no unconstrained functional clock paths and three
consecutive deterministic physical Arria10 GX PCIe Gen3x8 passes.

Each actual execution retains a fresh `evidence/<suite>-<timestamp_or_hash>/`
receipt with exact argv/cwd, tool version, source/input hashes, times, timeout,
exit and raw logs. Preserve failures. Nested per-run directories also end in a
timestamp/hash. Temporary model dumps use `checkpoint-images/` or
`official-image-*`. No runtime directories/private paths/credentials are product
inputs. Clean reproduction copies only declared sources/reference inputs and
regenerates compact behavior+synthesis; full-model reproduction additionally
requires external immutable inputs, comparators and authorized physical bridge.
