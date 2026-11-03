# Anvil-Q4-FP v1.2.0-bf16-multi-llm

## Status and authority

This specification records the independently admitted native floating-point
contract. It is not a verification result. The accepted parent source inventory
is `anvil_q4_reference/rtl/*.sv`; those files remain unchanged. No repository
source index or authentic `design/GENERATIONAL_HANDOFF.md` was supplied.
Historical parent timing and PPA are therefore unknown.

Designer owns `rtl/*.sv` and `design/*.md`. Independent Verifier owns `tests/*`.
The shared runtime owns execution evidence, timing, physical-board checks and
the final independently approved PDF, which follows engineering acceptance.
The portable entry point will be `anvil_q4_fp_top`. Implementation status and
remaining work are recorded in `ARCHITECTURE.md`; requirements below are not
relaxed by incomplete implementation.

## Public interface and parameters

The top retains the exact parent port names, directions, unsigned widths and
bank slicing documented in `NATIVE_INTERFACES.md`. No benchmark/debug ports are
added. Defaults are BANKS=16, QUEUE_DEPTH=3, TILE_K=128, TILE_ROWS=16.
Legal BANKS are 1,2,4,8,16; QUEUE_DEPTH is 1..16; TILE_K is 1..128;
TILE_ROWS is 1..16. Invalid parameters use diagnostic-only safe widths and a
`PARAMETER ERROR` fatal before work, not a silently supported fallback.
SB=BANKS for legal configurations, otherwise one.

Reset is asynchronous active-low. A transfer uses pre-edge valid AND ready.
All outputs are zero in active reset, and payloads are zero when their valid
control is false. Held valid transfers retain their payload/flags until
acceptance, except reset or explicitly specified cancellation invalidation.
`done`, `error` and `cancel_done` are one-cycle notifications; error implies
done. Normal logits retire once in ascending index, with done after the last
backpressured transfer. Speculative results remain held until verify_ready.

## Cycle and degenerate-boundary table

| Boundary | Required behavior |
|---|---|
| Pre-edge | Sample valid AND ready; no post-edge ready is used retroactively. |
| Active reset | Clear control asynchronously and gate every output to zero. |
| First released edge | Only a pre-edge eligible transfer can be accepted. |
| Flush/cancel and command | Flush/cancel wins; accept no new arithmetic/command. |
| Flush and result | Suppress numerical publication and commit immediately. |
| Externally held request and cancel | Keep tuple/tag/valid until accepted; drain its reply. |
| External acceptance and reply together | Resolve exactly once against pending ownership. |
| Response holding | Each lane/client holds independently; no aggregate ready. |
| QUEUE_DEPTH=1 | One slot per bank, still no reuse before ownership retirement. |
| QUEUE_DEPTH=3 or other non-power-of-two | Explicit bounded wrap, not an address mask. |
| TILE_K=1 | One activation then one weight vector; no zero-width index. |
| TILE_ROWS=1 or 3 | Fixed 17 channels, unused lanes masked, no ghost arithmetic. |
| BANKS=1 | Weight lanes contend fairly in the scheduler, not before it. |
| Final tile/partial word | Mask tails; zero cache tail padding, preserve neighbors. |
| Simultaneous completion and next issue | Respect leaf retirement bubble; no bypass. |
| Successful descriptor commit | Only quiescent; invalidate sequence/prediction/cache generation. |
| Failed descriptor commit | Preserve active descriptor and committed sequence. |
| Speculative retirement and cancellation | Cancellation wins, no tentative commit. |
| Epoch/tag exhaustion | Reject rather than wrap or alias stale responses. |

Reset integration must also reset the external responder or exclude pre-reset
replies from a new reset session. Draining alone never authorizes tag reuse.

## Descriptor

Use 32-word shadow/active storage, atomic quiescent commit, configuration
priority over tokens and normal token priority over drafts. Version 1 modes
1..4 preserve parent semantics and rejection behavior in an isolated path.
Native descriptors have:

| Word | Native value |
|---|---|
| 0,1 | version 2, mode 5 |
| 2 | element format: 0 BF16, 1 FP16 |
| 3,4 | 0 native weights, 0 integer activation quantization |
| 5 | cache: 0 lossless BF16, 1 lossless FP16, 2 FP8 E5M2 |
| 6 | active power-of-two banks, at most BANKS |
| 7..14 | layers, hidden, intermediate, query_heads, kv_heads, head_dim, vocabulary, context |
| 15 | 1 reserved legacy group-size placeholder |
| 16 | QKV-bias enable 0/1 |
| 17,18 | positive finite FP32 RoPE theta, RMS epsilon |
| 19,20 | page_tokens, physical_pages |
| 21 | 0 |
| 22 | GQA ratio 1..8, every integer supported |
| 23 | 1 native image layout |
| 24..31 | 0 |

Ranges: layers 1..64, hidden 2..8192, intermediate 1..32768,
query_heads/kv_heads 1..128, even head_dim 2..256,
vocabulary 1..262144, context 1..131072. Require
query_heads=kv_heads*ratio, hidden=query_heads*head_dim.
page_tokens is 1,2,4,8,16,32; physical_pages is 1..131072, with sufficient
capacity. Validate full-width operands before using narrowed products;
overflow, nonzero reserved words, unknown enums and malformed dimensions
reject commit. No command sees partial updates.

Reset selects native Qwen2.5-7B BF16/lossless-BF16 and available BANKS.
Qwen2.5-7B-Instruct and DeepSeek-R1-Distill-Qwen-7B dimensions are
(layers,hidden,intermediate,query_heads,kv_heads,head_dim,vocabulary) =
(28,3584,18944,28,4,128,152064), QKV bias enabled.
Llama-3.2-1B uses (16,2048,8192,32,8,64,128256), and 3B uses
(28,3072,8192,24,8,128,128256), both without QKV bias.
Checkpoint configuration supplies epsilon, theta, context and RoPE scaling.
Support does not imply executed trained-checkpoint measurements.

## Numerical rules

BF16 is 1/8/7 with bias 127; FP16 is 1/5/10 with bias 15; FP32 is
1/8/23 with bias 127. Use round-to-nearest ties-to-even (RNE), gradual
underflow, tininess after rounding, signed zero, infinity and NaNs.
Generated canonical NaNs are FP32 0x7fc00000, BF16 0x7fc0,
FP16 0x7e00; signaling NaNs raise invalid.
flags[4:0]={invalid,divide_by_zero,overflow,underflow,inexact}.
Numerical exceptions are not protocol errors. No flush-to-zero, saturation,
synthesizable real arithmetic, AWQ or integer activation quantization.

At GEMV input boundaries, narrow FP32 activations RNE to the selected native
16-bit format, then widen exactly; weights already have that format.
Each lane starts at +0 and visits ascending K, separately rounding FP32
multiplication and addition, never FMA/reassociation. Carry FP32 sums unchanged
between K tiles. Masked lanes contribute neither values nor flags.
Add widened native bias only after the entire dot product.
Embedding/gamma widen exactly. Residuals, scores, softmax, RMSNorm and SwiGLU
intermediates remain FP32; narrow only at explicit GEMV/cache boundaries.
Logits are FP32. The reference is this ordered algorithm, not universal bit
identity with fused/reassociated framework kernels.

RMSNorm computes ascending rounded squares/sum, FP32 division by hidden,
epsilon addition, FP32 sqrt, then rounded x*gamma divided by the root.
Attention uses KV head=floor(query_head/ratio), ascending dimension products,
FP32(1/sqrt(head_dim)) scaling, causal positions 0..current, max subtraction,
ordered exp sum/division and ascending weighted-V accumulation.
Split-half RoPE uses separately rounded products:
y0=round(round(x0*cos)-round(x1*sin)),
y1=round(round(x0*sin)+round(x1*cos)).
SwiGLU computes round(silu(gate)*up) followed by down projection,
where silu(x)=FP32(x/FP32(1+exp(-x))).
Ordinary arithmetic primitives are correctly rounded.

Exp uses signed Q56 reduction by ln2=0x00b17217f7d1cf7a, degree-16
Q62 polynomial, RNE product rescaling, coefficients RNE(2^62/n!),
and final FP32 packing. This frozen approximation is not weight/activation
quantization or a generally correctly rounded IEEE transcendental.
NaNs canonicalize, -infinity maps to +0, +infinity maps to +infinity.
Finite x>89 returns infinity with overflow/inexact; x<-104 returns zero
with underflow/inexact. Other finite values use the frozen reduction,
polynomial and packing; nonzero inputs additionally raise inexact.
Independent verification requires exact algorithm agreement and <=1 FP32 ULP
against high precision for finite non-overflow results, including subnormals.

Native greedy selection picks the lowest index on numerical ties, including
signed zero. NaNs cannot beat numbers; all-NaN selects zero. Legacy selection
is separate.

### FP32 leaf edge table

The native arithmetic module is `anvil_q4_fp32` with the exact parent signature.
Opcodes 0..9 are add,sub,mul,div,sqrt,BF16-widen,FP16-widen,BF16-narrow,
FP16-narrow,int32-to-FP32. Opcodes 10..15 return canonical qNaN+invalid.

| Edge after acceptance E0 | Action |
|---|---|
| E0 | Capture operands/op, busy=1, no result. |
| E1 | Classify/unpack. |
| E2 add/sub | Align. |
| E3 add/sub | Arithmetic. |
| E4 add/sub | Normalize. |
| E5 add/sub | Round. |
| E2 mul | Product. |
| E3 mul | Normalize. |
| E5 mul | Round. |
| E8 add/sub/mul | Publish, including special cases. |
| E64 div/sqrt | Publish after bounded recurrence, including specials. |
| E2 conversions/invalid | Publish, including specials. |
| E(L+1) earliest | Retire result, even if ready was high at publication. |
| Following edge earliest | Accept next operation. |

Flush immediately suppresses ready/valid and clears flight state next edge.
Held results and flags cannot change.

### Tensor-array edge table

Default LANES=16,TILE_K=128, legal LANES 1..16 and TILE_K 1..128.
Exact ports are recorded in `NATIVE_INTERFACES.md`. Invalid length 0 or
>TILE_K or mask 0 returns an error response without consuming data.
Command E0 enters LOAD post-edge. Accept exactly length activation beats,
then length weight-vector beats in increasing K. The first weight transfer
is no earlier than the edge after the last activation transfer.

| Edge relative to a weight acceptance W | Action |
|---|---|
| W | Capture raw weight vector and selected broadcast activation. |
| W+1 | Classify/unpack through a dedicated widening register. |
| W+2 | Register widened FP32 operands and conversion flags. |
| W+3 | Simultaneously accept active-lane multiplications. |
| W+11 | Multipliers publish. |
| W+12 | Controller captures/retires all products. |
| W+13 | Simultaneously accept active-lane additions. |
| W+21 | Adders publish. |
| W+22 | Controller captures/retires sums and flags. |
| W+23 | Publish final result, or earliest next weight acceptance. |
| W+24 earliest | Retire final command result. |

The two-register widening path cannot bypass through arithmetic leaves.
Inactive lanes never issue arithmetic or add flags. Stalls move milestones
only at handshake boundaries; accepted leaf operation offsets remain exact.
Last-result publication is a separate registered edge after add capture.

## Native memory and integration

The four named native modules GEMV, decoder, MLP and token-I/O replace only
their inherited scalar memory bundles with 17-channel flattened bundles.
Their inherited functional controls remain, with quantization tied inactive.
Channels 0..15 are exclusively independent native weight reads. Channel 16
is the scalar auxiliary owner. Channel count never depends on BANKS or
TILE_ROWS. The exact widths/signatures are in `NATIVE_INTERFACES.md`.

GEMV loads activations using channel 16. For each K it independently
presents each active lane's row_base+lane, tile_base+K weight request,
deasserts accepted lanes, captures each response into its owning register,
and submits the vector only when every active lane has returned successfully.
Hold K until tensor acceptance; no lane reuse before response retirement.
No native scale/zero-point requests. LM-head uses kind 0, proj 1, layer 0;
decoder projections use kind 1, projection 0..6 and the inherited layer.

MLP and token-I/O pass weight lanes one-to-one from their GEMV. Decoder
passes lanes from direct GEMV or MLP. Eligible scalar leaves use registered
round-robin arbitration with ownership locked from request acceptance to
response retirement, including held requests. Cache and attention remain
distinct scalar owners. Round-robin advances only at response retirement;
phase completion cannot release outstanding ownership.

Top instantiates descriptor, bank_scheduler, speculative, token_io, decoder,
final_norm of the corresponding `anvil_q4_fp_*` types. Decoder instantiates
gemv, rope, attention, kv_cache, mlp, elementwise; mlp is
`anvil_q4_fp_swiglu_mlp`, attention is `anvil_q4_fp_gqa_attention`.
Native GEMV and LM-head use the real tensor array with generated
`tensor_lanes` containing `anvil_q4_fp32` arithmetic. Compatibility is isolated.

Top records stage ownership across all 17 channels and changes it only after
the outgoing stage completes and all held requests, outstanding ownership
and response buffers empty. final_norm uses client 16 only. The native
scheduler fixes CLIENTS=17. Lane identity is preserved through its records.
Native bank=(row+col)&(active_banks-1); c_req_stride remains for inherited
tuple compatibility, not native bank selection. QUEUE_DEPTH bounds slots
per bank; arbitration is bounded and fair.

Every accepted external transaction has a unique opaque 64-bit tag and
recorded bank/client/slot/command-generation/local-subowner association.
Delivery requires full tag and bank equality. Unknown, duplicate, stale and
wrong-bank responses fault the command. Independently buffered client
responses allow other banks to progress under a blocked consumer.
Every write also receives exactly one acknowledged reply.

Cancellation suppresses new local acceptance/publication/commit immediately.
Locally queued work not externally presented may be discarded, but externally
held requests cannot be withdrawn. Accepted operations, including acceptance
on the cancel edge, drain under original tags; drained values do not reach
cancelled arithmetic. Clear local state only after transferring ownership
to drain bookkeeping. Do not change stage, descriptor, compatibility mode or
channel owner before drain_done and all prior ownership is empty.
cancel_done follows that quiescence. Reject tag/epoch exhaustion.

Native kinds: 0 embedding/LM-head (proj 0/1), 1 weights, 4 QKV bias,
5/6/7 gamma, 8 FP32 scratch, 9/10 lossless K/V, 11 FP32 RoPE,
12/13 FP8 K/V, 15 page table. Never emit native kinds 2,3,14 as metadata.
Native weights/embedding/bias/gamma carry one 16-bit element in the low half,
upper half zero. Scratch and RoPE are FP32. Keep parent projection IDs and
scratch slots. Native row-interleaving differs from legacy linear-stride banking.

## Cache and images

Pages are host mapped. Kind 15 uses layer=sequence epoch, row=logical page,
col=0, bit31 valid, bits30:0 physical page. page=position>>log2(page_tokens),
offset=position&(page_tokens-1),
physical row=(physical_page<<log2(page_tokens))|offset.
Reject invalid/out-of-range maps, duplicate live aliases, protected committed
page collisions, context overflow and reads beyond allowed positions.
Pack two lossless 16-bit or four FP8 elements per word, low indices low bits.
Preserve neighboring elements; zero tail padding. Flatten heads with widened
head*head_dim+dimension. Packing/page logic uses no division or modulo.

Lossless cache preserves every stored 16-bit encoding, signed zeros and NaN
payloads, after explicit narrowing. Arithmetic widening may canonicalize NaNs.
FP8 E5M2 is 1/5/2, bias 15, with IEEE-style infinity/NaN/subnormals, RNE,
overflow to infinity and generated canonical qNaN 0x7e. It is a separately
measured lossy floating-point mode, not the unquantized reference.

Weights, embeddings, gamma, bias and split-half FP32 RoPE tables are external
images. Fixtures must be deterministic and labeled synthetic. Manifests bind
configuration, dimensions, format, tuple mapping and table generation by hash.
The portable tensor-file and manifest format is defined in `NATIVE_IMAGE.md`.
Preserve supplied checkpoint RoPE tables including Llama scaling; do not
silently replace them with unscaled tables. No embedded trained weights,
network downloads or invented checkpoint results.

## Sequence and speculation

new_sequence requires position 0; continuation requires committed_tokens.
Require token<vocabulary and position<context. Errors cannot advance state.
A continuation draft must match the prior greedy prediction at token 0;
mismatch returns accepted=0 without execution. Execute token 0 at draft_pos,
then token 1 at draft_pos+1 only if the first prediction matches token 1.
Mismatch after the first target yields accepted=1; two successes yield 2.
A new-sequence draft establishes token 0 without prior prediction.
No speculative logits enter the normal stream.

Tentative KV commits only at successful verify_valid AND verify_ready.
Cancellation, target error or malformed response preserves previous committed
state and rejects/discards tentative pages. Rejected suffixes cannot affect
later normal tokens. Result/committed state stay stable under verify stalls.

## Acceptance and portable reproduction

The independent Verifier implements `python3 tests/verify.py --suite`
`numerics|behavior|compatibility|defects|synthesis|delivery`; no arguments runs
all. Each command creates missing/stale prerequisites itself. These six checks
remain mandatory and append-only. They are not yet implementation results.

Numerics requires exhaustive BF16/FP16 widens and finite adjacent narrow
midpoints/neighbors on both signs, all FP8 decodes/ties, transitions, specials,
flags and signed zero. At least 4096 deterministic random cases per FP32
add/sub/mul/div/sqrt across seeds 17,89,2026, plus directed cases, must have
zero bit/flag mismatches. Exp uses >=4096 finite samples plus boundaries.

Compiled Verilator complete inference must compare every public logit and
relevant stage/cache write to independent references, cover all ratios 1..8
x both element formats x all three caches in multi-token tests, and exercise
banks 1/2/4/8/16, queues 1/3/16, rows 1/3/16, K 1/3/128 and masked tails.
Representative multiseed runs require hidden>=64, multiple layers and >=4
tokens, independently reordered/stalled memory, no unexplained active X/Z.
Cover malformed descriptors, all immediately out-of-range parameters,
boundary dimensions/addresses, atomic config, reset, cancellation, fairness,
tag/epoch exhaustion and accepted0/1/2 speculation with both target failures,
cancel in both targets/at retirement, old-sequence replacement, protected
collisions and capacity-1 rejection. Coverage must be observed counters.

For default 16-bank/16-row inference, decoder, MLP and LM-head each must show
16 distinct same-K weight tuples with row_base..row_base+15, correct banks,
distinct live tags and actual common-edge acceptance in an unstalled cohort.
A separate cohort stalls selected banks while others advance, reorders
lane-distinguishing replies within/across banks and holds client responses.
Scoreboard every tuple/tag/lane/K, observe common 16-lane multiply/add issue,
and compare accumulators, stage writes and all logits. Repeated tuples,
duplicated valid bits and scalar clients do not satisfy parallel coverage.

Compatibility runs parent versus isolated integration for modes 1..4, supported
GQA/cache variants, token_phase, config rejection, cancellation and drafts.
Compare complete public values/order/completion with documented wrapper
latency only. Preserve and independently distinguish parent failures.

Disposable compiled mutants must fail real assertions before cycle bounds for
rounding, flags, GQA, masking, cache packing/pages, response-tag ownership,
speculative rollback and native quantization bypass. Compile failures,
timeouts and matching log strings are not sensitivity proof. Tag mutation
must exercise reordered lane-distinct native weight traffic.

Yosys must read/hierarchy/proc/opt/check and inspect JSON for default and
singleton/non-power-of-two legal geometry: zero latches, unresolved black
boxes, div/mod cells or loops; real sequential state and connected native
decoder/tensor/cache/control; 16 default lanes/banks and separately wired
17 scheduler clients through decoder/MLP/LM-head. Keep large memories inferred.

Delivery runs a fresh source-only relative-path reproduction with compact
complete inference, independent comparison, one mutation and synthesis.
Exclude evidence, metadata and old binaries; scan shipped sources/instructions
for private paths, credentials and fixed PCIe/JTAG identities.
Profile actual matched parent/native cycles, transactions/bytes, simultaneous
banks, arithmetic utilization and stalls; lossless and FP8 separately.
Label synthetic runs and production-shape extrapolation, never invent speedup.

Icarus is limited to compact startup/leaf/one-token checks <=500000 cycles,
selected to finish <60s; larger/multiseed/multitoken work uses compiled
Verilator. No per-cycle flushing or bulk beat-level logs. Preserve fresh,
source-bound exact command/tool/time/timeout/exit/raw-log receipts; per-run
evidence directories end with timestamp/hash, never overwrite failures.
Prune transient compiled intermediates, not source or receipts.

All RTL targets Arria 10 GX 10AX115N2F45E1SG, one synchronous domain at
period<=10.0ns: no combinational / or % operators, synthesizable real,
mixed blocking/nonblocking sequential assignments or unbounded
data-dependent loops. Use registered reads, bounded normalization/arbitration
and sequential div/sqrt. Structural inspection includes all shipped RTL.
No timing waiver is proposed. Generic synthesis is not frequency/fit proof.
The shared runtime independently executes timing lint, Quartus 17.1 STA
WNS>=0 at <=10ns with legal fit, and physical PCIe Gen3x8 HIL with >=3
consecutive deterministic native-computation passes. Engineering acceptance
requires every mandatory check, runtime gate and independent review.
