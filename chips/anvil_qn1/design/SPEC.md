# Anvil-QN1 numerical and transaction specification

Version: `1.0.0-qwen3-qknorm-think`. Intended native top: `anvil_qn1_top`.
This document records the admitted contract, not an acceptance result. The
implementation inventory and outstanding integration are in ARCHITECTURE.md.
Unimplemented requirements below remain requirements; they are not waived.

## Profiles and legal elaboration

| PROFILE | Model | Layers | Hidden | Intermediate | Q heads | KV heads |
|---|---|---:|---:|---:|---:|---:|
| 1 | Qwen/Qwen3-0.6B | 28 | 1024 | 3072 | 16 | 8 |
| 2 | Qwen/Qwen3-1.7B | 28 | 2048 | 6144 | 16 | 8 |
| 3 (default) | Qwen/Qwen3-4B | 36 | 2560 | 9728 | 32 | 8 |

Production constants are HEAD_DIM=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=40960,
GROUP_SIZE=128, LANES=256, theta=1000000, and epsilon32=0x358637bd.
Q_DIM=NUM_Q_HEADS*HEAD_DIM and KV_DIM=NUM_KV_HEADS*HEAD_DIM are **not**
HIDDEN_SIZE aliases. Query head h uses KV head floor(h/GQA), with GQA=2 or 4.
All seven native projections are bias-free.

Native top parameters are PROFILE, COMPACT, NUM_LAYERS, HIDDEN_SIZE,
INTERMEDIATE_SIZE, NUM_Q_HEADS, NUM_KV_HEADS, HEAD_DIM, VOCAB_SIZE,
MAX_SEQ_LEN, GROUP_SIZE, BANKS and QUEUE_DEPTH. COMPACT defaults to zero.
BANKS is 1,2,4,8 (default 8); QUEUE_DEPTH is 1..16 (default 3).
Production overrides must match the selected tuple and constants exactly.

COMPACT=1 permits 1..36 layers, hidden multiples of 8 through 2560,
intermediate multiples of 8 through 9728, head dimensions 8,16,32,64,128,
1..8 KV heads, twice or four times as many Q heads through 32,
1..151936 vocabulary entries, and 1..40960 positions. GROUP_SIZE is a power
of two in 8..128 dividing hidden, intermediate and Q_DIM. It changes geometry,
not numerical rules or the 256-lane interface.

Invalid parameters must compile into the intentional
`ANVIL_QN1 PARAMETER ERROR` diagnostic rather than fail accidentally on widths
or selects. Invalid datapaths need generate guards and minimum diagnostic port
widths. Address products are evaluated at 128-bit elaboration precision and
must fit the specified 32-bit coordinates and 64-bit byte-address products.
Constant elaboration division is allowed; runtime combinational `/` and `%`
are forbidden.

## Numerical rules

Native A16, embeddings, learned gamma, activations and KV are IEEE BF16.
Arithmetic reductions are IEEE binary32, round-to-nearest ties-to-even (RN32).
RNBF16 is correctly rounded, including gradual underflow. Preserve signed zero;
exact cancellation produces positive zero. No legacy Q16 clamping is allowed.
NaN, infinity, negative nonzero AWQ scale, nonzero reserved payload bits or
finite-operation overflow cause a visible error and forbid successful token
commit. Inactive tensor lanes ignore all payloads, including invalid encodings.

W4 q and z are unsigned nibbles. Delta=q-z is -15..15.
Weight=RN32(delta*BF16_scale), product=RN32(weight*BF16_activation).
BF16-weight mode instead forms RN32(BF16_weight*BF16_activation).
Symmetric images use offset-binary q and z=8, not two's-complement packing.
Reduce a tile with a balanced adjacent-ascending 256-lane tree; inactive
coordinates are positive zero. Accumulate tile sums in ascending input-tile
order from positive zero using RN32. Projection outputs round to BF16, except
vocabulary logits remain binary32. Memory order and BANKS must not affect
arithmetic order.

Q and K independently normalize each head. For a head of D coordinates:

1. Square each coordinate with RN32 and sum using a balanced adjacent tree.
2. Mean=RN32(sum/D); v=RN32(mean+epsilon32).
3. Root=RN32(sqrt(v)); reciprocal=RN32(1/root).
4. u_i=RNBF16(RN32(x_i*reciprocal)).
5. y_i=RNBF16(RN32(u_i*gamma_i)).

Each layer has separate Q and K gamma vectors of D values, shared across heads.
Do not normalize V, combine heads or substitute hidden-sized normalization.
Ordinary pre-attention, post-attention and final RMSNorm use their hidden
extent with next-power-of-two padded balanced sums and RN32 division.

RoPE uses split-half pairs (i,i+D/2). At position p, angle is
p*1000000^(-2*i/D). Coefficients are independently rounded to BF16. Compute
binary32 products and separate binary32 add/subtract (no FMA), then RNBF16.
Position zero uses coefficients (1,0). Portable image generators must evaluate
this formula rather than use legacy theta or adjacent-coordinate pairing.
Independent verification covers positions 0,1,32767,32768,40959 and rejects
40960.

Causal attention uses only committed positions through the input and selected
accepted ancestors. Dot products have a balanced HEAD_DIM reduction and
RN32(1/sqrt(HEAD_DIM)) scale. Subtract the maximum before deterministic E.
For x<=0, E(x)=0 when x<-16 and E(0)=1. Otherwise, with L=0x3f317218:
m=floor((-x)/L) using exact represented values; r=RN32(x+RN32(m*L));
t0=1; tk=RN32(RN32(t(k-1)*r)/k), k=1..6.
Sum t0..t6 in order using RN32, clamp to [0,1], and correctly round scaling
by 2^-m. Range reduction and division must be registered sequential algorithms.
Accumulate attention denominator and weighted values in increasing position
order, round each binary32 operation, divide, and round context to BF16.

SiLU is x/(1+E(-x)) for x>=0 and x*E(x)/(1+E(x)) otherwise, with each binary32
operation rounded. Gate and up projections round to BF16; SiLU's result and
the gate/up activation product have BF16 boundaries before down projection.
Both residual additions round to BF16. Final hidden RMSNorm and the tied BF16
embedding matrix generate all vocabulary logits in ascending index order.
Greedy ties choose the lowest token ID.

## Cycle and degenerate-boundary table

All handshakes sample **pre-edge** valid && ready. Registers update after the
edge. Reset is asynchronous active-low; resettable state uses
`always @(posedge clk or negedge rst_n)`. All public valids, ready signals,
pulses, modes and payloads are zero while reset is asserted. Unreset storage
requires reset ownership/validity and cannot leak active X/Z.

| Boundary | Required behavior |
|---|---|
| Reset asserted | No transfer; all public outputs zero, including ready |
| First post-reset edge | Only a pre-edge valid&&ready request can be accepted |
| Head accepted at n | Ownership captured, ready drops; result after n+133, earliest transfer n+134 |
| Tensor accepted at n | Result after 48 enabled intervals, earliest transfer n+49 |
| Blocked tensor output | Globally freeze all arithmetic, tags and valids |
| CSR accepted at n | Response after n+1; earliest transfer n+2; hold under stall |
| Token accepted at n | No same-edge logits, completion or thinking draft acceptance |
| Draft accepted | Backend continuation request is registered on a later edge |
| Backend response accepted | No same-edge commit publication |
| Commit accepted | Count/mode update once; done strictly later |
| No-commit transaction | Done strictly after last frame transfer and cache settlement |
| Completion | Token ready returns only in the following idle cycle |
| QUEUE_DEPTH=1 | No zero-width pointer; accepted request still owns its response slot |
| QUEUE_DEPTH=3 | Explicit bounded wrap, not a power-of-two mask |
| VOCAB_SIZE=1 | First and last frame beat coincide, but completion is later |
| MAX_SEQ_LEN=1 | Position-zero token is terminal; no generated commit or draft |
| BANKS=1 | Same tagged-response/error/drain rules as eight banks |
| HEAD_DIM<128 | Align the sum tree so fused-head latency remains 133 |
| Clear and increments | Clear wins; simultaneous snapshot captures pre-clear values |
| Cancellation and commit | Cancel wins before transfer; earlier public commits cannot be retracted |

Head edge schedule: squares n+4, sum n+39, mean n+40, epsilon n+45,
root n+79, reciprocal n+113, scaled x n+117, rounded u n+118,
gamma product n+122, normalized BF16 n+123, rotary products n+127,
rotary sums n+132, output n+133. No same-edge replacement of retired ownership.
Tensor boundaries are weight formation 4, activation multiplication 4, and
eight five-stage add levels. Sequential assignments are nonblocking only.
Global priority is reset, cancel, detected fault, accepted control, normal work.

## Public top interface

Inputs: clk,rst_n,cancel,token_valid,new_sequence,token_phase,logit_ready;
token_id and token_pos are 32 bits. token_phase=0 is prefill, 1 is decode.
Outputs: token_ready,logit_valid,done,error,cancel_done;
logit_index[31:0],logit_data[31:0] (binary32).

Banked ports preserve parent names and widths: mem_req_valid/ready/write and
mem_rsp_valid/error/ready have BANKS bits. mem_req_kind is BANKS*4,
mem_req_layer/row/col/wdata and mem_rsp_rdata are BANKS*32, mem_req_proj is
BANKS*3, and request/response tags are BANKS*64. Every accepted request,
including writes, receives exactly one matching tagged response. Stalled
requests and responses hold all payloads. Out-of-order banks must retain
association. Wrong-bank, duplicate, stale and unknown tags or response errors
fault the sequence and initiate drain.

Draft inputs are draft_valid,draft_count[2:0],draft_tokens[127:0],
draft_parents[11:0]; draft_ready is output. Commit outputs are
commit_valid,commit_count[2:0],commit_tokens[159:0],commit_pos[31:0],
think_active; commit_ready is input. Ascending tokens occupy ascending
32-bit slices; parents occupy ascending three-bit slices.

CSR inputs are csr_valid,csr_write,csr_addr[11:0],csr_wdata[31:0],
csr_wstrb[3:0],csr_rsp_ready. Outputs are csr_ready,csr_rsp_valid,
csr_rdata[31:0],csr_error. There are no supplied result/acceptance/oracle ports.

## Deferred-final-token and cache publication

Only one host transaction is active. A valid sequence begins at position zero
with new_sequence. Ordinary consumption is consecutive. Prefill may transition
to decode, never back. new_sequence discards old cache ownership and pending
continuation but preserves explicitly configured or committed thinking mode.

For a decode at p producing G=(g0,...,g[b-1]), commit_pos=p+1 and b is 1..5.
All but the final generated token have been evaluated and their KV writes
acknowledged before commit_valid. The last generated token is deferred. After
publication, KV extent is exactly 0..p+b-1; committed token extent is 0..p+b.
The next host input must be **exactly** the final token at position p+b in
decode, with new_sequence=0. Resending evaluated drafts, skipping the final
token or changing its ID is a transaction error, not another valid path.

| Transaction | Frames | Generated commit | KV extent | Next ordinary input |
|---|---:|---|---|---|
| Prefill p | 1 | None | 0..p | Any token at p+1, prefill or first decode |
| Direct decode p<M-1 | 1 | g0 at p+1 | 0..p | g0 at p+1, decode |
| Four accepted drafts plus bonus | 5 | d0,d1,d2,d3,bonus | 0..p+4 | bonus at p+5, decode |
| Zero accepted drafts | 1 | Correction at p+1 | 0..p | Correction at p+1, decode |
| Capacity-truncated batch | b | Ends exactly at M-1 | 0..M-2 | Final token at M-1, decode |
| Terminal materialization p=M-1 | 1 | None | 0..M-1 | None; only a new sequence can continue |
| Invalid/exhausted continuation | No successful new frame | None | Sequence invalidated | Require new_sequence at zero |

The five-token row requires p+5<M. Stop at capacity without wrap, fabricated
tokens or unavailable correction/bonus. Reject any draft whose own path
reaches M, even if it would not be selected. A generated mode marker also ends
the batch before that token is evaluated; it is the deferred final token.

Each generated token has exactly one complete public vocabulary frame in
generating-context order. Every frame transfers indexes 0..VOCAB_SIZE-1.
Prefill and terminal materialization each expose one frame without a commit.
Never expose or interleave rejected/off-path frames. Complete the frame before
the backend argmax response transfers. Public logit backpressure may stall the
backend. commit_valid additionally waits for settled required cache writes.

Physical writes do not establish reachability by themselves. Branch-local
ownership is unpublished until the accepted path is promoted. Rejected state
cannot become reachable by decrementing a position. No outstanding publication
write may first report failure after a successful commit. Memory failure or
cancel before transfer suppresses the unpublished batch and invalidates the
sequence. Cancel after transfer preserves public tokens but invalidates
continuation, drains accepted memory work and emits cancel_done, not done.
An errored partial logit frame is incomplete and invalid. Error never
accompanies successful commit or normal done.

Input markers are observed once at successful input publication. A newly
supplied first decode input is observed after root completion and before
selecting continuation mode. Generated markers are observed at commit. A
deferred-final resubmission materializes KV without observing/counting that
marker again. Later faults do not retract already committed mode changes.

## Dual-mode controller

Reset mode is /no_think. Idle mode writes configure it; committed token 151667
opens thinking, 151668 closes it. Cancel wins; otherwise close wins over open,
which wins over idle configuration. No speculative candidate affects mode.
Busy mode configuration is an error without a side effect.

Direct decoding needs no draft. In thinking nonterminal decoding, exactly one
batch of 1..4 nodes is required, **after** the host token and successful root
input completion. No idle, prefill, direct, terminal or second draft handshake
is allowed. Holding draft_valid before readiness is allowed with stable data.

Parent=4 denotes the root; any other parent must name an earlier node.
Reject invalid count, token ID, forward/self parent, duplicate sibling token or
out-of-capacity path. Support a four-deep chain and branching. Select the unique
greedy-matching child, evaluate its real decoder context, then continue. Publish
the first correction or final bonus subject to marker/capacity truncation.

The controller's backend is verify_valid/ready,verify_parent[2:0],
verify_pos[31:0],verify_rsp_valid/ready,verify_argmax[31:0],verify_error.
Only responses to accepted outstanding requests are legal. Top owns prefill
and terminal orchestration. The standalone controller additionally uses
start_valid/ready,start_pos to launch a nonterminal root, publish_ready as the
cache-publication fence, and done/error for its internal completion.
observed_valid/observed_token report committed input markers.
flush/cancel annul outstanding controller ownership while preserving mode.

## Logical memory image

All scalar BF16 payloads use bits 15:0; bits 31:16 are reserved zero.
Packed W4 q/z occupy all 32 bits. Projection IDs are Q=0,K=1,V=2,O=3,
gate=4,up=5,down=6. Q/K/V consume HIDDEN_SIZE; O consumes Q_DIM;
gate/up consume HIDDEN_SIZE and down consumes INTERMEDIATE_SIZE.
Outputs respectively have Q_DIM,KV_DIM,KV_DIM,HIDDEN_SIZE,
INTERMEDIATE_SIZE,INTERMEDIATE_SIZE,HIDDEN_SIZE coordinates.

| Kind | Row | Column | Payload |
|---:|---|---|---|
| 0 | Token/vocabulary ID | Hidden coordinate | BF16 tied embedding/LM |
| 1 | Input coordinate | Output-row block of eight | Packed qweight |
| 2 | Input group | Output-row block of eight | Packed zero points |
| 3 | Input group | Output row | BF16 group scale |
| 4 | Forbidden in native mode | - | No bias access |
| 5,6 | 0 | Hidden coordinate | Pre/post-attention BF16 gamma, layer selected |
| 7 | 0 | Hidden coordinate | Final BF16 gamma, layer zero |
| 8 | Scratch slot | Coordinate | BF16 activation |
| 9,10 | Sequence position | KV head*HEAD_DIM+coordinate | BF16 K,V, layer selected |
| 11 | Position | 2*pair index + 0/1 | BF16 cosine/sine, layer/proj zero |
| 12,13 | 0 | Head coordinate | Q/K BF16 gamma, layer selected |

The AWQ eight-row shifts are [0,16,4,20,8,24,12,28]. Group rows use ascending
input groups. Coefficient images fix theta=1e6 and the selected HEAD_DIM.
Stream/generate external images; do not instantiate checkpoint-sized on-chip
weights or MAX_SEQ_LEN-sized KV arrays.

Scratch row meanings remain parent-compatible; native widths are BF16:

| Slot | Meaning | Coordinate extent |
|---:|---|---:|
| 0 | Input/residual after second add | HIDDEN_SIZE |
| 1 | Pre-attention norm | HIDDEN_SIZE |
| 2 | Final QK-normalized/rotated Q only | Q_DIM |
| 3 | Final QK-normalized/rotated K only | KV_DIM |
| 4 | V | KV_DIM |
| 5 | Attention context | Q_DIM |
| 6 | O projection | HIDDEN_SIZE |
| 7 | First residual | HIDDEN_SIZE |
| 8 | Post-attention norm | HIDDEN_SIZE |
| 9,10 | Gate/up | INTERMEDIATE_SIZE |
| 11 | BF16 SiLU-gate times up | INTERMEDIATE_SIZE |
| 12 | Down projection | HIDDEN_SIZE |
| 13 | Reserved; no native access | 0 |
| 14 | Final norm | HIDDEN_SIZE |

Raw Q/K and normalized-before-RoPE Q/K must never be externally written.
Scratch allocation is 15*max(HIDDEN_SIZE,INTERMEDIATE_SIZE,Q_DIM) scalar slots
per owned context. Logical byte products include 4*VOCAB_SIZE*HIDDEN_SIZE for
the tied matrix, 4*layers*input_extent*output_extent for conservative projection
address bounds, and 4*layers*MAX_SEQ_LEN*KV_DIM per KV kind. On-chip speculative
activation/KV ownership is bounded to four nodes, not the entire sequence.
Legacy compressed-cache kinds remain available only in the unchanged legacy
top and are not overloaded by native mode.

## CSR ABI

Aligned 32-bit reads ignore wstrb. Writes require 0xf; unsupported offsets,
reserved bits, read-only writes and busy configuration writes return a held
error response without side effects. One response per accepted request.
Control bit0 is desired thinking, bit1 snapshot W1S, bit2 clear W1S.
Idle control writes emit one registered mode pulse. Busy snapshot/clear writes
must preserve the current thinking bit and set at least one action bit; they
cannot configure mode. Busy reference writes are rejected.

| Offset | Meaning |
|---|---|
| 000,004 | Version 0x01000001, profile |
| 008,00c | Control; status bits busy,thinking,sticky-error |
| 010,018,020 | Busy, thinking-busy, direct-busy 64-bit counters |
| 028,030 | Thinking/direct generated committed tokens |
| 038,040 | QK active/blocked cycles |
| 048,04c | Snapshot max absolute finite binary32 score; arithmetic-error count |
| 050,058,060,068 | Draft, verified, accepted, rejected nodes |
| 070,078 | Memory errors; completed/exhausted sequences |
| 080 | Snapshot sequence number |
| 084 | Host-reference-valid |
| 088,090,098 | Host legacy cycles (64), tokens (64), profile (32) |

All multiword counters use low then high word at offset+4, modulo 2^64.
Reads use a coherent snapshot bank; no read side effects. Snapshot captures
pre-edge values while live counters continue. Clear outranks increments;
simultaneous snapshot captures pre-clear values. Snapshot sequence increases
per snapshot. Reference data is host supplied, never a native measured result.
Generated token counters count each committed slice once in its pre-commit
mode. Prefill consumption and final-token resubmission do not recount generated
tokens. sequence_done denotes actual sequence exhaustion/completion, not each
host transaction. Cancelled real QK activity still counts.

## Required independent acceptance

Designer may run only a fast static syntax/elaboration check. Verifier owns
tests/*.py, independent models, functional simulation, mutation and synthesis.
The entry is `python3 tests/verify.py`; no arguments must run every L1 suite.
Suites are smoke,numerical,behavior,benchmark,defects,synthesis,reproduce;
benchmark domains are gsm8k,humaneval,mmlu,boolq,hellaswag.

Required tools are python3,iverilog,vvp,verilator,g++,make,yosys. No tool
installation is authorized. Compact Icarus runs are <=500000 cycles and
designed below 60 seconds; larger/multi-token/multi-seed/mutation work uses
compiled Verilator. Each check must fit 2700 seconds without weakening
functional/numerical thresholds. Use bounded logs, real exit/assertion and
record-count checks, strict active X/Z rejection, and no per-beat flushing.

Require zero bit mismatches for numerical outputs, metadata, frames, commits
and CSRs. The reference uses independent integer/rational IEEE rounding and
independently derived algorithms, with a second math/decimal analytic check.
Seeds are 17,89,203. Per seed: >=256 tensor vectors across formats/masks and
all lanes, >=64 Q and >=64 K heads at HEAD_DIM=128, gamma variation, both GQA
ratios, scale 1/256 and directed zero/constant/outlier/subnormal/invalid cases.
E absolute error <=3e-5 on [-16,0]; BF16 SiLU error <=0.02*max(1,abs(exact)).
Nonzero RMS>=0.1 unity-gamma stress scores <=1.05*sqrt(HEAD_DIM), with scale
invariance within 5% and general gamma-scaled analytic bounds also checked.

Behavior covers every transaction row, exact second transactions for direct,
prefix lengths 0..4, branching, marker/capacity truncation, >=6 logical steps,
all seeds and both GQA ratios, BANKS1/8, QUEUE_DEPTH1/3/16, every compact
logit and external KV address/payload against independent sequential decoding.
Cover malformed drafts, wrong/skipped/resubmitted tokens, stalls, wrong and
duplicate/stale tags, read/write errors, reset during work, and cancellation
before/after publication. Exercise every CSR offset and snapshot/clear/rollover
priority. Production-shaped Q/K/V/O/norm transactions cover all exact profiles;
HEAD_DIM128 attention checks all 40960 independently initialized cache
positions. Neither is a pretrained/full-context top-inference claim.

For **each production profile**, measure actual decoder-layer cycles with the
real 256-lane scheduler and eager-ready fixed-latency memory against a
Verifier-owned clone omitting only QK normalization, preserving RoPE and other
work. Include all normalization stalls and tails. Require C_without_norm>0
and 100*(C_fused-C_without_norm)<2*C_without_norm; no padding, artificial
delay, vocabulary hiding or estimated subtraction.

Each benchmark domain has >=4 identifiable real fixed fixtures and >=6 decode
steps per case, both modes, compact representations of both GQA ratios and all
profile families. Retain immutable IDs/hashes, licenses and vocabulary mapping.
Compare every output against the independent quantized model. These are bounded
numerical-parity benchmarks, not published accuracy or pretrained validation.
Execute unchanged-parent compact inference separately for generational
references and disclose different arithmetic, work and token-count semantics.

Defects must independently detect omitted QK norm, shared Q/K gamma,
adjacent/wrong-theta RoPE, QKV bias, wrong Q/O extents, rejected speculative
acceptance/cache visibility, tag misassociation and broken CSR count/snapshot.
Compile failure, timeout or infrastructure failure is not detection.
Synthesis covers all production profiles and compact boundaries, zero latches,
runtime div/mod, black boxes and multiple drivers, and connected 256-lane and
required feature hierarchy. A clean-directory reproduction copies only shipped
sources and runs compact smoke/numerical checks without original build state.

Native shared-runtime gates remain mandatory: rtl-timing-lint, successful
Quartus 17.1 fit/resource reporting and post-synthesis WNS>=0 at <=10.0 ns on
Intel Arria 10 GX 10AX115N2F45E1SG, then >=3 consecutive deterministic PCIe
Gen3x8 physical HIL passes. Yosys is not STA. Any timing waiver needs actual
post-synthesis proof and independent Coordinator admission.

All execution checks remain mandatory and append-only. Every run retains fresh
timestamp/hash-ended evidence directories, exact commands, source hashes,
versions, raw logs, timeouts/exits and settled-child disposition. Failed
receipts are never overwritten. Preparation is advisory, never acceptance.
The shared runtime produces the independently approved product PDF **after**
engineering acceptance; it is not an L1 prerequisite. No design or verification
selector includes .vulcan/, .git/, .tooling/ or VULCAN/.
