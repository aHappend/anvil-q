# Anvil-Q3-FP v1.2.0-bf16: implementation contract

## Status and provenance

This document records the admitted product contract, not verification results.
The immutable input is `anvil_q3_reference/rtl/*.sv` (26 files).
No repository-intake source index was supplied.
`design/GENERATIONAL_HANDOFF.md` was not supplied. Historical parent Quartus
timing and physical ALM/DSP counts are unknown. Comparative physical acceptance
requires the genuine handoff or independently retained, matched parent
measurements on the specified device. Generic synthesis is not physical PPA.

Designer owns `rtl/*.sv`, this document and `design/ARCHITECTURE.md`.
Verifier independently owns `tests/*.py`, reference models, simulations,
mutation checks and synthesis. No passing result is implied by an interface
definition or by static elaboration.

## Product and legal geometry

The top is `anvil_q3_fp_top`. The target is Intel Arria 10 GX
`10AX115N2F45E1SG`, one clock, period at most 10.0 ns.

| Parameter | Default | Legal contract |
|---|---:|---|
| PROFILE | 3 | Exactly 3 in this branch |
| NUM_LAYERS | 36 | Positive, address bounds below |
| HIDDEN_SIZE | 2048 | Positive; equals NUM_Q_HEADS * HEAD_DIM |
| INTERMEDIATE_SIZE | 11008 | Positive |
| NUM_Q_HEADS | 16 | Exactly 8 * NUM_KV_HEADS |
| NUM_KV_HEADS | 2 | Positive |
| HEAD_DIM | 128 | Positive and even |
| GROUP_SIZE | 128 | 1..128 |
| AWQ_BITS | 4 | Exactly 4 |
| VOCAB_SIZE | 151936 | Positive |
| MAX_SEQ_LEN | 32768 | 1..32768 |
| BANKS | 8 | 1, 2, 4, 8 |
| CACHE_MODE | 0 | 0, 1, 2 |
| MODE1_FP8 | 0 | Boolean; effective only in Mode 1 |
| INT4_ASYM | 0 | Boolean; effective only in Mode 2 |
| CACHE_BLOCK | 1 | Compatibility-only; exactly 1 |
| QUEUE_DEPTH | 3 | 1..16 |
| TILE_K | 128 | 8..128, divisible by 8 |
| TILE_ROWS | 8 | 1..8 |

Both hidden and intermediate sizes are divisible by 8 and GROUP_SIZE. Parameters,
products and addresses are checked before narrowing, using the parent's
128-bit elaboration arithmetic. In particular all logical dimensions, K*D,
2*D, cache column extents and 15*max(H,I) fit 32 bits; byte extents
4*V*H, 4*L*H*I, 4*L*H*H, 4*L*S*K*D and quantized payload/metadata extents
fit 64 bits. Invalid configurations issue `PARAMETER ERROR`. Safe diagnostic
widths and generate guards must prevent invalid expressions from preempting
that diagnostic; they are not permission to clamp a legal geometry.

## Public interface and token ownership

All parent top ports retain their names, widths, directions and low-bank-first
slice ordering. `B=BANKS`:

| Direction | Signals |
|---|---|
| Input, scalar | clk, rst_n, cancel, token_valid, new_sequence, token_phase, logit_ready |
| Input, 32 bits each | token_id, token_pos |
| Added input, scalar | token_fp16, token_awq |
| Output, scalar | token_ready, logit_valid, done, error, cancel_done |
| Output, 32 bits each | logit_index, logit_data |
| Output, B bits each | mem_req_valid, mem_req_write, mem_rsp_ready |
| Input, B bits each | mem_req_ready, mem_rsp_valid, mem_rsp_error |
| Output | mem_req_kind[4*B], mem_req_layer[32*B], mem_req_proj[3*B] |
| Output | mem_req_row[32*B], mem_req_col[32*B], mem_req_wdata[32*B], mem_req_tag[64*B] |
| Input | mem_rsp_rdata[32*B], mem_rsp_tag[64*B] |

`logit_data` is binary32 bits (the parent's signed port declaration does not
give the bits integer semantics). Accept controls only at
`token_valid && token_ready`. `token_fp16=0` means BF16, `1` means FP16.
Pin the activation format until an accepted new sequence. A format change
without new_sequence errors and drains. `token_awq` may change between tokens,
never during one token. Native weights use the activation format; AWQ scales
are always FP16.

Keep the parent's first-token/new-sequence, ordered position, prefill-to-decode,
no decode-to-prefill, single-active-token, indexed-logit, memory-fault and
last-logit completion semantics. Cancellation overrides acceptance, flushes
internal ownership and drains every accepted external request. Stale epochs
cannot produce logits or expose cache entries. Acknowledged writes are not
rolled back. `done` and `cancel_done` pulse for one cycle; error is meaningful
with done. New sequences invalidate cache ownership without external zeroing.
There is no timeout-generated success.

## Frozen internal interface deltas

Except for the entries below, each parent-derived module keeps its counterpart's
port names, directions, widths and memory protocol. Changed numerical modules
use the `anvil_q3_fp_` prefix. These interfaces are requirements for integration,
not claims that all corresponding modules already exist.

| Module boundary | Exact delta |
|---|---|
| top | Add scalar inputs token_fp16, token_awq; binary32 interpretation of logit_data |
| decoder_layer | Add scalar cmd_fp16, cmd_awq inputs |
| gemv | Add scalar cmd_fp16, cmd_awq inputs |
| tensor_array | Add scalar cmd_fp16, cmd_awq inputs; load_data becomes [15:0]; result_sum becomes [B*32-1:0] |
| weight_prefetcher | Add [B-1:0] desc_fp16, desc_awq inputs; add [B*128-1:0] beat_weight16 output |
| weight_prefetch_bank | Add scalar desc_fp16, desc_awq inputs; add [127:0] beat_weight16 output |
| rmsnorm, rope, elementwise, token_io | Add scalar cmd_fp16 input |
| swiglu_mlp | Add scalar cmd_fp16, cmd_awq inputs |
| gqa_attention, kv_cache | Add scalar cmd_fp16 input; add MODE1_FP8 parameter |
| decoder_layer | Also add MODE1_FP8 parameter, forwarded to attention/cache |
| dot8 | New interface specified below; not the parent's integer dot interface |
| cache_codec | New streaming group interface specified below |

`kv_cache.read_data` retains its 32-bit port width and carries a
zero-extended selected-format 16-bit cache-read element. Scratch-facing
parent-derived scalar modules likewise keep 32-bit memory ports while
validating zero upper halves. These are numerical ABI changes, not port
width changes.

Command controls are sampled at the existing `cmd_valid && cmd_ready` or
`desc_valid && desc_ready` handshake and stored with ownership. Native prefetch
still returns AWQ q/z/scale outputs, zero when inactive; AWQ beats return
zero beat_weight16. Metadata/masks/row/epoch remain associated with each beat.
`desc_fp16` identifies native weight interpretation, even though tile RAM stores
unmodified bits. There are no benchmark/debug-only top ports.

Required literal hierarchy:

```text
anvil_q3_fp_top
  bank_scheduler : anvil_q3_bank_scheduler (unchanged parent implementation)
  decoder
    norm
    gemv
      tensor_array
        weight_prefetcher
          banks[g].storage
        engines[g].dot8
    rope
    attention
    mlp
    residual
  final_norm
  token_io
```

Scheduler clients, ingress fairness, queue depths, low-bit bank routing, unique
64-bit tags, held requests, ordered client responses, reordered external
responses and flush/drain remain real RTL behavior. Keep the two independent
prefetch slots EMPTY/FILLING/READY/ACTIVE and overlap filling with consuming.

The top inserts a two-slot request FIFO for every client before
`bank_scheduler`: weight-fetch clients `0..BANKS-1` and scalar clients
`BANKS..BANKS+8`, including RoPE at `BANKS+2`. This does not change module
ports or scheduler queue depth. A producer request
accepted at E0 owns a complete registered 136-bit payload (write, kind, layer,
projection, row, column, write data). It is first eligible for scheduler
acceptance at E1, adding one unstalled clock per request, including scalar
reads/writes and each AWQ q/z/scale read. Responses use the registered, ordered
boundary described below. Registered addresses and scheduler-facing valid do not depend
combinationally on producer failure or core flush. Payload may remain present
without valid; only valid transfers establish scheduler ownership.

Each slot samples producer payload on every edge while locally unowned, even
without producer valid. Acceptance locks the selected slot; only ownership and
the read/write pointers depend on handshakes or flush. Payload capture enables
therefore depend only on registered local ownership, not core flush, producer
valid or scheduler ready. Prefetch request fields are reset-gated but not
valid/flush-gated; fields without valid are not transactions.

Ready requires a free slot at the pre-edge sample; it does not anticipate a
scheduler retirement. With one slot owned, retire/refill on the same edge
preserves one queued request and supports one transfer per clock. With both
slots owned, a retirement restores producer credit for the following cycle,
not the retirement edge. FIFO ordering is independent of scheduler backpressure.

The FIFO retains accepted reads/writes independently of later producer-local
fault/flush gating, until forwarded or annulled by top-level core flush.

Each client also has a two-slot response FIFO carrying the complete 33-bit
error/data payload. A scheduler response accepted at E0 becomes visible to
the consumer post-E0 and can first retire at E1. Scheduler-facing ready is
reset-gated free-write-slot credit derived solely from registered ownership
and pointers. It never uses consumer ready, decoder failure, core flush or
same-edge consumer retirement lookahead. One occupied slot permits simultaneous
retire/refill into distinct slots; a full FIFO restores scheduler credit only
after a retirement edge. A held valid response preserves both data and error.
Unowned slots may sample payload speculatively; only handshakes own responses.
Reset clears payload, ownership and pointers and gates both sides' outputs to
zero. Core flush or scheduler fault immediately suppresses consumer-facing
valid/data/error and clears ownership/pointers on the edge, with priority over
either transfer. Scheduler credit remains capacity-only during flush; any
coincident accepted response is discarded, never delivered after restart.
Buffered responses have already retired externally; the unchanged scheduler
still drains all outstanding external transactions before abort completion.
Neither buffering boundary changes top ports, scheduler parameters or epochs.
All existing error propagation remains active. Core flush immediately
suppresses producer readiness and clears staged ownership on the edge, with
priority over forwarding/refill. Scheduler flush immediately suppresses
scheduler admission on cancel and abort flush; its existing
draining state suppresses admission thereafter. Staged valid and payload are
not redundantly gated by core flush before scheduler routing/arbitration.
Requests already accepted by the scheduler retain its unchanged flush/drain
semantics; an unforwarded staged request is discarded, not externally issued
or awaited. External writes already acknowledged are not rolled back; failed
or cancelled cache commits remain inaccessible. No local failure signal is
delayed to achieve this boundary.

Sequence start clears core/cache and staging ownership, but does not flush
the scheduler. Token acceptance requires `state==IDLE && scheduler_idle`,
with cancellation and scheduler faults excluded. Scheduler idle proves no live
slots and no drain in progress. Successful completion follows all operation
acknowledgments and the last logit handshake; failed/cancelled completion
follows external drain and core/staging annulment. Thus no prior request is
pending in the client FIFOs at sequence acceptance. No command issues in
IDLE or either sequence-start state. `SEQUENCE_FLUSH` retains its core-clear
cycle, followed by `SEQUENCE_DRAIN`, which waits for `scheduler_idle` rather
than a drain-done pulse from an unnecessary scheduler flush. Epoch increments,
sequence dtype sampling and cache invalidation remain unchanged. An unexpected
external response still invokes the scheduler fault/abort path. The parent
scheduler implementation, tags, fairness and queue ordering are unchanged.

### Arithmetic interfaces

`anvil_q3_fp_mul` and `anvil_q3_fp_add`:

```text
input  clk, rst_n, flush, in_valid, out_ready
input  in_a[31:0], in_b[31:0]
output in_ready, out_valid, out_data[31:0], out_flags[4:0]
```

Each has three independently enabled elastic register stages. Multiplication
stages are unpack/classification, 24-bit significand product/exponent,
normalization/RNE/special selection. Addition stages are classification and
alignment, add/subtract, normalization/RNE/special selection.

The dot interface is:

```text
input  clk, rst_n, flush, in_valid, out_ready, in_fp16, in_awq
input  weight16[127:0], activation16[127:0]
input  q_nibbles[31:0], z_nibbles[31:0], scale_f16[127:0], lane_mask[7:0]
output in_ready, out_valid, out_error, out_dot[31:0], out_flags[4:0]
```

Here q/z nibbles are already decoded into ascending input-lane order by the
prefetcher. Packed external output-row permutation is handled once at fetch.
`out_error` is an AWQ data-format error, separate from IEEE flags. Flags are
the OR of participating leaf operations. Native dot latency is 12 stages;
AWQ adds a 3-stage dequantization prefix. Mixed-mode dot transactions are not
allowed to overtake one another. Per-bank tensor command mode is constant.

New `anvil_q3_fp_divider` has scalar clk/rst_n/flush/start inputs,
numerator[31:0], denominator[31:0] inputs, ready/done/error outputs,
quotient[31:0] and flags[4:0] outputs. New `anvil_q3_fp_sqrt` has the same
control handshake, radicand[31:0] input, value[31:0] and flags[4:0] outputs.
Both use binary32 and accept only start && ready; they complete every finite
operation within 128 unstalled clocks. IEEE exceptional results use flags,
not protocol error. done is a one-cycle pulse, values remain registered until
the next operation, flush clears completion and ownership.

`anvil_q3_fp_exp` and `anvil_q3_fp_silu` retain the parent's
clk/rst_n/flush/start, ready/done/error, x/value port names, but x and value
are both [31:0] binary32 bits. Completion is within 1024 unstalled clocks for
exp. Exp accepts nonpositive arguments, exp(0)=1, and produces finite [0,1].
For -80<=x<=0 its absolute error is at most 2^-23+2^-15*exp(x);
x<-80 may return zero. Positive arguments are an explicit input-domain error,
not a silent clamp. SiLU uses exp(-abs(x)): +infinity maps to +infinity,
-infinity to -0, signed zeros retain sign, and NaNs canonicalize.

### Cache group interface

`anvil_q3_fp_cache_codec` is a bounded group codec with parameters CACHE_MODE,
MODE1_FP8 and INT4_ASYM. It does not own position commitment:

```text
input  clk, rst_n, flush, cmd_valid, cmd_decode, cmd_fp16
input  cmd_count[6:0]                 (1..32 or 1..64 as configured)
output cmd_ready, done, error
input  in_valid, in_last, in_data[31:0]
output in_ready
output out_valid, out_last, out_data[31:0]
input  out_ready
```

For lossy encode, input beats hold zero-extended original 16-bit elements;
output is metadata followed by eight payload words including zero padding.
For lossy decode, input is metadata followed by eight payload words; output
beats hold zero-extended selected-format elements, only cmd_count elements.
Mode 0 uses original 16-bit element inputs and packed word outputs for encode,
and the reverse for decode, without metadata. Input/output counts and last
are checked. No output precedes validation of all input bits/metadata.
Mode 0 accepts 1..64 elements. The KV controller selects head/group boundaries.
All output beats hold under backpressure; flush annuls incomplete groups.

## Cycle and degenerate-boundary table

E0 is the rising edge accepting pre-edge valid && ready.

| Boundary | Required post-edge behavior |
|---|---|
| Reset asserted | All public valid/ready/pulses/request fields/response-facing outputs/logit fields zero |
| Reset deasserted, idle | Ready may assert combinationally; no result/ownership appears spontaneously |
| Primitive E0/E1/E2 | Stages 1/2/3 respectively; first out_valid/data post-E2 |
| Primitive earliest retirement | E3 with pre-edge out_valid && out_ready |
| Native dot | Multiply post-E2; reduction post-E5/E8/E11 |
| Row accumulator after dot | Accumulated value post-E14, earliest retirement E15 |
| AWQ | Three additional dequantization stages before multiply |
| Held output | Payload, flags and metadata immutable while valid && !ready |
| Retire and replace | Same edge can consume held output and replace its stage |
| Bubble | Not a transaction; must not accumulate, advance row or raise an error |
| Flush/cancel/reset plus transfer | Annul/flush/reset wins; no old result escapes |
| New sequence accepted at E0 | Scheduler already idle; increment epoch and sample dtype/AWQ; post-E0 core flush clears cache/staging ownership, without scheduler flush |
| Sequence-start E1/E2 | E1 clears core/staging ownership and enters SEQUENCE_DRAIN; E2 enters EMBED only if scheduler idle; no drain-done pulse is required |
| Cancel/fault during sequence start | Cancel immediately flushes scheduler/core; fault takes the existing abort-flush/drain path; neither can issue embedding work |
| QUEUE_DEPTH=1 | Singleton queue supports simultaneous retire/refill without overwrite |
| QUEUE_DEPTH=3 | Explicit endpoint wrap, never binary-mask wrap |
| TILE_ROWS=1 or 3 | Row interlock waits for previous sum commitment; no fixed eight-row assumption |
| TILE_K=8 | A one-beat tile can be both first and last; tail masks still apply |
| VOCAB_SIZE=1 | Index zero is also last logit; completion still requires its handshake |
| MAX_SEQ_LEN=1 | Position zero only; later position errors, never wraps to a live entry |
| Partial cache group | Scan valid elements only; allocated padding is zero and validated |
| Failed/cancelled K/V write | Never establishes committed position, even if a subset was acknowledged |
| Tensor metadata FIFO full | Issue waits for a slot; simultaneous head retirement and tail insertion preserve order |
| Accumulator retirement and another-row issue | Commit old sum/release its row and reserve the other row on the same edge |
| Repeated-row issue at retirement | Conservatively waits one further clock; never bypasses an uncommitted sum |
| Prefetch RAM fill plus active read | Independent owned slots may write/read concurrently; held beat disables replacement read |
| Any client request accepted at E0 | Registered payload/valid visible post-E0; earliest scheduler acceptance E1 |
| Any client request held | Entire payload remains unchanged until scheduler acceptance or top-level flush; producer-local faults cannot rewrite it |
| Client FIFO has one request, retire/refill | Forward old request and accept replacement into the other slot on the same edge; each owns its own response |
| Client FIFO empty, scheduler stalled | Accept up to two requests independently; backpressure while both slots are owned |
| Client FIFO full, scheduler retires | No producer acceptance on that edge; released slot is available next cycle |
| Unowned request slot | Speculatively sample producer payload regardless of valid/flush; only an accepted handshake establishes ownership |
| Client stage plus cancel/core flush | Producer readiness suppressed; scheduler flush/draining suppresses admission; clear staged valid on the edge before any refill; scheduler-owned requests still drain |
| Client stage reset / first post-reset edge | Reset clears payload/ownership; after release an empty stage may accept, but cannot forward before E1 |
| Client stage, BANKS=1 / QUEUE_DEPTH=1 or 3 | One independent register per weight or scalar client; no pointers or power-of-two depth assumption |
| Scheduler response accepted at E0 | Error/data registered post-E0; earliest consumer retirement E1 |
| Response FIFO, one owned slot, retire/refill | Retire old head and own new tail in distinct slots; preserve order and complete payload |
| Response FIFO full, consumer retires | No scheduler acceptance on that edge; capacity returns next cycle, without ready lookahead |
| Response held, consumer not ready | Head data/error remain immutable until retirement or annulment |
| Response FIFO plus cancel/core flush/scheduler fault | Suppress consumer output immediately; clear ownership/pointers before refill, discarding coincident input; external drain remains scheduler-owned |
| Response FIFO reset / first released edge | Both interfaces zero during reset; empty capacity may assert after release, but no consumer valid until an accepted response |
| Response FIFO, BANKS=1 / QUEUE_DEPTH=1 or 3 | Two local slots per client, independent of scheduler depth; explicit one-bit pointer toggle |
| Codec final input and validation | Last is checked on acceptance; lossy output waits for complete group/padding validation |
| Codec output retirement and last write acknowledgment | Separate events; cache commitment requires the acknowledgment, not just codec retirement |

Wall-clock latency includes stalls. Counters advance on transfers, not asserted
valid alone. A repeated row cannot read an uncommitted accumulator. Masked lanes
are +0 and cannot contribute exceptional flags.

## Floating-point rules

BF16 has sign/exponent/fraction 1/8/7 and bias 127; FP16 has 1/5/10 and bias 15.
Use binary32 internal arithmetic, round-to-nearest ties-to-even (RNE), gradual
underflow, signed zero, infinity and NaNs. Arithmetic NaNs canonicalize to
0x7fc00000, 0x7fc0 or 0x7e00. Mode-0 storage is the deliberate exception and
preserves every original bit. Exact input widening preserves a NaN's sign and
payload for the consuming arithmetic operation to classify signaling NaNs.
Output narrowing is an arithmetic rounding boundary and canonicalizes NaNs.
Leaf flags[4:0] are invalid, divide-by-zero, overflow, underflow, inexact.
Underflow means tininess after rounding plus inexact. Protocol errors are not
IEEE flags.

Each bank has eight multiply lanes and an adjacent pairwise reduction:
(0+1),(2+3),(4+5),(6+7), then adjacent pairs, then root. Initialize each row
to +0; add tile contributions in ascending input order with binary32 RNE after
each addition. Do not reassociate to avoid feedback dependencies.

AWQ uses unsigned q,z, signed delta=q-z in -15..15 and nonnegative finite
FP16 scales, permitting either signed zero. Weight=RN32(delta*FP16(scale)),
then RN32(weight*widen(activation)); do not narrow dequantized weights.
External packed output ordering uses parent shifts [0,16,4,20,8,24,12,28],
equivalently permutation [0,4,1,5,2,6,3,7]. Bad scales or nonzero padding
are data-format errors.

## Memory ABI

Preserve logical kind/layer/projection/row/column addressing and transaction
semantics, not the parent's fixed-point data encoding.

| Kind | Representation |
|---|---|
| 0 | Embeddings/output-head selected-format 16 bits, upper response half zero |
| 1 native | row=input index, col=output index>>1; even/odd output weights in low/high halves |
| 1/2/3 AWQ | Parent packed q/z/FP16-scale layout |
| 4..7 | Selected-format bias/norm coefficients in low 16 bits, upper half zero |
| 8 | Parent scratch slots 0..14; zero-extended selected-format activations |
| 9/10 | Mode-0 packed K/V, two original elements per word |
| 11 | Binary32 RoPE cos/sin at parent pair addresses |
| 12/13 | Quantized K/V payload |
| 14/15 | Quantized K/V metadata |

Unused native weight halves are zero. Q/K/V biases are added in binary32 before
one selected-format activation store rounding. Other named activation-store
boundaries are norm outputs, each RoPE output, attention output, gate/up/down
projection outputs, SiLU*up, and both residual sums. Tensor accumulators,
attention scores/softmax, norm statistics and logits are not narrowed at
intermediate binary32 arithmetic boundaries.

Mode-0 col=h*ceil(HEAD_DIM/2)+(d>>1), half=d[0], row=token position.
Lossy block count=ceil(HEAD_DIM/G), G=32 for Mode 1 or 64 for Mode 2.
Payload col=(head*blocks+block)*8+word, metadata col=head*blocks+block.
Full and partial blocks allocate eight payload words. Element zero occupies
the least-significant payload bits. All padding bits are zero.

## Hierarchical cache numerics and commitment

Mode 0 is bit-exact for all 65536 encodings. Mode 1 uses symmetric signed INT8
[-127,127] or finite E4M3FN (bias 7, subnormals, maximum 448; 0x7f/0xff are
forbidden payloads). Mode 2 uses signed INT4 [-7,7], or affine [-8,7].
There is no eightfold KV replication: query head h maps to KV head h>>3.

For symmetric formats choose the smallest integer e in [-256,256] with
max(abs(x)) <= L*2^e, L=127,7,448 respectively. All-zero groups use e=0.
Encode RNE(x/2^e) into the selected code format, with bounded finite endpoint
saturation only; decode in binary32 then RNE-narrow to the selected format.
For affine INT4 choose the smallest e allowing rounded extrema and z in
[max(-8,-8-rmin),min(7,7-rmax)]. Choose z=0 if possible, otherwise the endpoint
nearest zero. Encode clamp(RNE(x/2^e)+z,-8,7), decode (code-z)*2^e.
All-zero affine groups use e=z=0. Lossy input nonfinites explicitly error.

Metadata is signed e[15:0], signed z[19:16] (zero for other formats),
fp16[20], Mode-1 FP8[21], CACHE_MODE[23:22], zero[31:24].
Decode validates all fields, forbidden codes and padding.
The on-chip tier holds bounded staging/decoded groups, not full-context
register storage. A position commits only after every relevant K and V
payload/metadata write is acknowledged. Epoch and position ownership gate
reads; failed/cancelled commits remain inaccessible.

## Model operations and acceptance

Keep seven projections Q/K/V/O/gate/up/down and parent decoder ordering:
norm, Q/K/V with biases, split-half RoPE, causal GQA, O, residual, norm,
SwiGLU, down, residual. RMSNorm uses binary32 epsilon 1e-6 and binary32
square/sum/mean/epsilon/reciprocal-square-root operations. RoPE uses
x*cos-y*sin and x*sin+y*cos, theta=1000000. Attention uses ascending
dimension/position order, binary32 QK, division by sqrt(HEAD_DIM),
max-subtracted stable softmax and binary32 weighted-value accumulation.
Never route these operations through fixed-point parent kernels.

The scalar norm implementation starts the square sum at +0 and adds each
rounded square in ascending dimension order. Mean is RN32(sum/float(H)),
epsilon is `0x358637bd`, reciprocal is RN32(1/sqrt(RN32(mean+epsilon))),
and the store value is narrow(RN32(RN32(x*gamma)*reciprocal)).
The dimension conversion to binary32 uses RNE.
RoPE computes RN32(RN32(x*cos)-RN32(y*sin)) and
RN32(RN32(y*cos)+RN32(x*sin)); only those final values narrow.
The host supplies coefficients for angle
`token_pos * 1000000.0**(-2*pair_index/HEAD_DIM)` in binary32, with
pair_index in `[0,HEAD_DIM/2)`. Coefficients must be finite and in [-1,1].

Attention starts each QK dot at +0, adds RN32(q[d]*k[d]) in ascending d,
then divides by RN32(sqrt(float(HEAD_DIM))). For each head, a causal
maximum scan precedes component-wise stable-softmax scans. Each component
restarts denominator and weighted sum at +0, sums exp(score-max) and
RN32(exp(score-max)*v[component]) in ascending position order, then divides
the weighted sum by the denominator in binary32. No exp or sum is narrowed
to the activation format. Recomputing identical scores between scans is
intentional and does not change arithmetic order. NaN scores contaminate
the head's maximum and context; NaN/undefined infinity differences propagate
canonical NaNs instead of becoming a positive-domain exp command.
Output-head logits use ascending scalar products/additions from +0, with
no narrowing after the last addition.

The MLP sequences the decoder's shared GEMV using its existing projection
handshake (4, 5, then 6). The decoder's captured cmd_fp16/cmd_awq controls
remain fixed through these projections. The MLP's cmd_fp16 is also captured
for its elementwise child; its cmd_awq input annotates the shared mode and
does not add an independent mode-change channel.

## Source integration and reset/start

Compile `rtl/*.sv` with the immutable parent files
`anvil_q3_reference/rtl/anvil_q3_bank_scheduler.sv` and
`anvil_q3_reference/rtl/anvil_q3_mem_port.sv`. The package filename sorts
before its users. No other parent numerical module is in the FP top's
active hierarchy. A portable static elaboration command from the project
root, requiring Icarus Verilog with SystemVerilog support, is:

```sh
iverilog -g2012 -t null -s anvil_q3_fp_top rtl/*.sv \
  anvil_q3_reference/rtl/anvil_q3_bank_scheduler.sv \
  anvil_q3_reference/rtl/anvil_q3_mem_port.sv
```

Static elaboration does not establish functional or timing acceptance.
The immutable parent directory is also a required source input for the
independently authored comparison/reproduction suites, not a generated cache.

Assert rst_n low before starting traffic, then release it with the synchronous
clock running. The first accepted token uses new_sequence=1 and token_pos=0;
hold token inputs unchanged until token_ready accepts them. Serve each bank's
tagged memory requests using the floating-point ABI above and return write
acknowledgments as well as read responses. Keep logit_ready asserted or
backpressure complete indexed logits. Start another token only at token_ready,
using the next position and the same dtype unless beginning a new sequence.
For cancellation, assert cancel, release it, continue returning all previously
accepted external transactions, and wait for cancel_done before restarting.
Never reuse the fixed-point parent's memory image as a floating-point image.

Verifier's mandatory, independently runnable commands are:

```sh
python3 tests/verify.py --suite numerics
python3 tests/verify.py --suite protocol
python3 tests/verify.py --suite behavior --seed 17
python3 tests/verify.py --suite behavior --seed 89
python3 tests/verify.py --suite behavior --seed 211
python3 tests/verify.py --suite benchmark
python3 tests/verify.py --suite synthesis
python3 tests/verify.py --suite defects
python3 tests/verify.py --suite portability
```

No arguments executes the aggregate. These commands are the required delivery
entry points, not statements that verification sources are already authored.
The admitted numerical thresholds, exhaustive encoding checks, deterministic
transaction counts, full bank/cache/dtype/AWQ matrix, six observable mutation
kills and matched immutable-parent comparisons remain mandatory. In particular
well-conditioned fixture cosine floors are 0.999/0.99/0.95 for Modes 0/1/2;
they do not replace exact arithmetic, cache and protocol assertions.
Report all five domains: projection, attention/cache, norm/RoPE/residual,
SiLU/SwiGLU, integrated decoder/token/logit. Report actual cycles, stalls,
useful operations, payload/metadata/padding bytes and 100 MHz bandwidth gap.
Synthetic fixtures and sampled default-shape tiles are not a checkpoint run.

Use compact Icarus for startup/leaf smoke and compiled Verilator for substantive
sweeps. L1 does not perform native timing/physical-board gates. Actual Yosys
checks must establish no latches, blackboxes, undriven/conflicting signals or
datapath division/modulo, retained memory inference and active required
hierarchy. All sequential assignments are nonblocking; no combinational
division/modulo datapath is allowed. Bounded normalization and registered
arithmetic are implementation requirements, not timing evidence.

The shared runtime owns timing lint, Quartus STA, HIL, execution evidence and
the independently approved final PDF after engineering acceptance. The PDF
is never a prerequisite to the engineering commands above.
