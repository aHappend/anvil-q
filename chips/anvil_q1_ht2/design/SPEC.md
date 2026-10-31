# Anvil-Q1-HT2 v2.5.0-ht2-fp-spec-sparse

## Authority and implementation status

The independently admitted work order is the acceptance contract. This document
records its interface and numerical freeze; it does not assert acceptance.
The initial source increment contains native arithmetic and transaction leaves.
The connected native decoder/top, compatibility delivery copies, complete image
conversion/layout integration and hardware measurements remain unfinished.
Do not use the leaf increment as a reduced substitute for the full product.

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

Reset cannot relabel stale DDR responses as new requests: native integration
must retain reset-safe drain/epoch ownership. Memory data need not reset.
Synchronous storage ports do not acquire asynchronous-reset data writes.
`done` is one clock following final accepted result, never early.

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
