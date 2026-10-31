# Anvil-Q2-HT2 specification

Version: v2.5.0-ht2-fp-spec-sparse. Target: Intel Arria 10 GX
10AX115N2F45E1SG, synchronous 100 MHz or faster.

## Authority and implementation status

The independently admitted work order is the acceptance contract. This document
records its design boundaries; it does not waive any requirement. The initial
source tree contained only the 22 modules in `anvil_q2_ht_reference/rtl/`.
Those sources are preserved unchanged. No repository intake/source index or
`design/GENERATIONAL_HANDOFF.md` was supplied. Parent timing/PPA numbers, official
checkpoint/tokenizer/corpus inputs and the Q2-FP baseline have not been supplied.
Do not interpret the parent's provenance as passing HT2 evidence.

Implementation is incremental. See `ARCHITECTURE.md` for the actual connected
scope and outstanding work. In particular, leaf RTL is not an implemented
28-layer accelerator, a measured throughput result, or engineering acceptance.

## Public top-level contract

The required entry is `anvil_q2_ht2_top`. Preserve every parameter, default and
port of `anvil_q2_ht_reference/rtl/anvil_q2_ht_top.sv`, all legacy descriptor and
configuration addresses, host access, cancellation/fault drainage and Avalon-MM
ordering. Add unsigned packed ports:

| Direction | Names and widths |
|---|---|
| Input | `draft_valid`, `draft_count[2:0]`, `draft_ids[127:0]`, `draft_parent[7:0]`, `draft_pos[31:0]`, `draft_new_sequence` |
| Output | `draft_ready`, `batch_valid`, `batch_accepted[2:0]`, `batch_mask[3:0]`, `batch_next_token[31:0]`, `batch_position[31:0]`, `batch_error` |
| Input | `batch_ready` |
| Output | `logit_slot[1:0]`, `logit_fp32[31:0]` |

Legacy token offers have priority over draft offers and execute K=1. Each batch
returns exactly one response after all its slot-tagged provisional logits.
`logit_fp32` is the native result on the same valid/index/slot transfer as the
legacy-representation `logit_data`. There are no benchmark-only hardware ports.

Reset mode is native BF16, K=1. At `0x0040`, HT2_MODE bits 1:0 select
legacy/BF16/FP16 (0/1/2), bits 3:2 select native/W4/W2 (0/1/2), bit 4
enables exact sparsity, bit 5 selects INT8 KV. Other bits and encoding 3
are illegal. `0x0044` HT2_K accepts 1, 2, 4 only; `0x0048` is HT2_STATUS.
Unsupported/misaligned accesses error. Mode changes require quiescence and
invalidate incompatible cached weights/KV atomically.

## Descriptor and weight byte layout

The parent descriptor is 64 bytes, little-endian:

| Byte offset | Width | Meaning |
|---|---|---|
| 0 | 8 | Payload base |
| 8 | 8 | Payload byte extent |
| 16 | 8 | Zero-point base |
| 24 | 8 | Scale base |
| 32 | 4 | Rows |
| 36 | 4 | Columns |
| 40 | 4 | Payload row stride |
| 44 | 4 | Zero-point row stride |
| 48 | 4 | Scale row stride |
| 52 | 4 | Flags |
| 56 | 8 | Reserved, zero |

Native descriptor flags use bit 8 valid and bits 1:0
BF16=1, FP16=2, W4=0, W2=3. All other bits are zero; mode-dependent
validation must not apply these meanings to legacy descriptors.
Native element bytes are least-significant byte first. Quantized codes are
unsigned; W4 uses bits 3:0 then 7:4, W2 uses bits 1:0, 3:2, 5:4, 7:6.
Rows and columns are in increasing logical order. Groups have GROUP_SIZE
consecutive columns; metadata groups are row-major. For a row with C columns,
G=C/GROUP_SIZE, the minimum payload lengths are 2*C, ceil(C/2), ceil(C/4)
for native, W4, W2; zero-point lengths are ceil(G/2), ceil(G/4); scales
are 2*G bytes. Metadata padding in the last byte is zero. Strides include
padding and must be at least these lengths. All extents, strides and address
additions require overflow/bounds validation before memory issue.

Example W4 codes [1,14,2,7] occupy bytes `e1 72`. Zero points [8,3]
occupy `38`. BF16 scales [1,0.5] occupy `80 3f 00 3f`. With GROUP_SIZE=2,
the reconstructed four weights are [-7,6,-0.5,2], rounded once to BF16.
Example W2 codes [0,1,2,3] occupy `e4`; zero point 1 and scale 0.5
reconstruct [-0.5,0,0.5,1]. Native tiles contain 128 weights (256 bytes),
W4 tiles 64 bytes, W2 tiles 32 bytes. Aligned external reads are 64 bytes;
unaligned tiles require enough beats for the offset and payload. Actual DDR
accounting includes padding, metadata, KV and control beats, not hypothetical
suppressed reads.

## Floating point

Native operand/storage formats are IEEE BF16 or binary16, never Q16.16.
Products round to binary32 before any addition; accumulation is non-fused
binary32 RNE. Gradual underflow, ties-even, signed zero, infinity and canonical
NaNs are required: BF16 `7fc0`, FP16 `7e00`, FP32 `7fc00000`.
Invalid/nonfinite operands and overflow propagate transaction errors, never a
finite-success substitution. Masked lanes contribute +0 without exceptions.
Finite cancellation is +0; -0 plus -0 is -0.

Each tile has four slots of 128 lanes, sharing the 128 weight operands.
Adjacent lanes pair first; seven binary reduction levels each have four
register stages. A seven-stage product and four-stage bias addition make 39
stages total. Inter-tile row accumulation is four-stage FP32 addition in
increasing column-tile order with true dependency tracking.

All 28 model layers require native embedding, RMSNorm (epsilon 1e-6), QKV and
output projection, causal GQA with checkpoint RoPE, max-subtracted softmax,
residuals, SwiGLU, final normalization and logits. Every activation storage
boundary rounds to its selected format; RMSNorm/attention statistics are FP32.
Exp/sigmoid/reciprocal/rsqrt relative error is at most 2e-5 on the exercised
finite model domain, absolute error at most 2e-7 near zero. Softmax row
absolute sum error is at most 2e-4. These do not relax elementary bit-exactness.
Coefficient/algorithm provenance must accompany their implementation.

## Sparsity and DMA

The required `anvil_q2_ht2_sparse_w2w4_dma` has the frozen work-order ports.
Only all-zero magnitude bits (including either signed zero) may skip a lane.
The fetch mask is the union across active slots, not the mask of one slot.
Eligible SwiGLU outputs are tested after BF16/FP16 rounding. Dequantization is
`RNE_BF16((q-z)*scale)` using an exact signed integer difference and BF16 scale.
Native BF16/FP16 ignore metadata. Invalid/nonfinite scales error rather than
returning a successful zero tile.

The DMA is single-owner until completion/drain. A retained adjacent W2
half-beat can be reused only with valid address/generation ownership.
Cancellation never abandons an accepted external transaction. Late fills
must be drained before reuse and cannot populate a new generation.

## Speculation and transactional cache

Nodes are topologically ordered, count 1/2/4, with root parent zero and each
other parent less than its node index. Slot zero is the mandatory input.
Choose the lowest-index child whose ID equals its selected parent's actual
target-model greedy argmax; argmax ties choose the smaller vocabulary ID.
Stop at a missing matching child or leaf. Return the final node's target ID.
Successful accepted count is 1..K; failures/cancellation commit zero.
Attention sees the committed prefix plus that node's ancestors/self, never
siblings/descendants. Position/RoPE follows depth, not slot index.

All active slots/layers stage acknowledged K/V writes into isolated provisional
generations. Completion bit `28*t+l` certifies slot t/layer l.
At response acceptance, cache mapping and sequence pointer publish together,
mapping noncontiguous selected slots to consecutive committed positions.
No early publication under output stall. Error, annul, stale generation or
incomplete write leaves the old committed data/pointer visible. Concurrent
host writes to live model/cache storage while busy are rejected.

BF16 KV is little-endian BF16. Native INT8 records store a positive
little-endian BF16 scale followed by CACHE_BLOCK signed bytes [-127,127].
For nonzero finite blocks, let a=max(abs(x)), r=RNE_BF16(exact(a/127));
store s=max_BF16(`0001`,r). Quantize the exact ratio x/s once to an
RNE integer, saturate to [-127,127]; decode exact q*s once to BF16.
No intermediate FP32 rounding is allowed. All-zero blocks store scale `3f80`
and zero bytes; signed zero reconstructs +0. Reject nonfinite inputs.
For +/-`0001`, scale is `0001`, q=+/-1 and reconstruction is +/-`0001`.
At a=63*2^-133 the unclamped scale rounds to zero; at 64*2^-133 it rounds
to `0001`. Both stored scales are `0001`, not the all-zero-block exception.
Legacy KV formats are unchanged and are not this codec.

## Cycle & Degenerate-Boundary Table

| Event/boundary | Required behavior |
|---|---|
| Pre-edge n | Only valid AND ready transfers; payload is stable through sampling |
| Post-edge n | First register stage owns an input transferred at n |
| Active reset | Every public output, including ready/address/data, is zero |
| First released edge | Ordinary handshakes may sample; no preexisting response/commit |
| MAC, no stall | Valid after n+38; earliest consumption n+39 |
| DMA decision | Registered sparse union after n+1; first request no earlier than n+2 |
| DMA final fill f | Valid after f+9; earliest consumption f+10 |
| DMA all skipped | Inject at n+2; valid after n+11 |
| Tree | Valid after n+5; earliest publication n+6 |
| Output stalled | Valid/payload hold; no repeated/early completion/publication |
| Reset/annul on commit edge | Reset/annul wins, no publication |
| Singleton sequence/vocabulary/group/cache/queue/outstanding/hot-block | Legal within full geometry constraints; no zero-width indices |
| Queue depth 3, sequence length 5 | Explicit terminal wrap, never binary-overflow wrap |
| One column tile | First and last coincide; one accumulator initialization/result |
| Partial final tile | Out-of-range columns masked before operand evaluation |
| Simultaneous input/output | Only elastic stages explicitly permitting replacement can replace |
| Flush and accepted response | Flush wins; external ownership still drains |
| Fault and ordinary transfer | Fault wins after reset/cancel; no partial success |
| Sequence exhaustion | Reject overflow before any cache/pointer publication |

Control/pipelines use asynchronous active-low reset. Unreset RAM requires
reset generation/valid protection and synchronous registered reads/writes.
There may be no active X/Z, inferred latches, unresolved black boxes,
combinational division/modulo or mixed sequential assignment styles.

## Legal parameters

NUM_LAYERS 1..28, HIDDEN_SIZE 8..1536, INTERMEDIATE_SIZE 8..8960,
NUM_Q_HEADS 1..16, NUM_KV_HEADS 1..2, HEAD_DIM even 2..128,
HIDDEN_SIZE=NUM_Q_HEADS*HEAD_DIM and integral Q/KV ratio. Hidden,
intermediate and KV dimensions are divisible by eight. GROUP_SIZE is a
power of two 1..128 dividing hidden/intermediate dimensions. VOCAB_SIZE is
1..151936, MAX_SEQ_LEN 1..32768. BANKS=16, LANES_PER_BANK=8,
DDR_DATA_WIDTH=512. TILE_SLOTS 2..8, READ_OUTSTANDING 1..16,
QUEUE_DEPTH 1..16. CACHE_BLOCK is a power of two 1..128 dividing
HEAD_DIM; HOT_BLOCKS 1..64. Physical slot/lane counts remain four/128.
Illegal geometry must reach an explicit PARAMETER ERROR with
diagnostic-safe widths and a guarded legal datapath, not silently clamp.

## Independent acceptance (not executed by Designer)

Verifier owns `tests/**` and the six self-contained `tests/verify.py`
commands: `numerics`, `behavior`, `mutations`, `synthesis`, `benchmarks`,
`reproduce`. None is optional or replaced by leaf elaboration.
All encodings require conversion/classification coverage; arithmetic needs
at least 10000 seeded finite/special pairs per format and bit-exact independent
integer/rational oracles. A8 coverage compares scale bytes, every q byte
and reconstruction for both signs, mixed/zero/minimum-subnormal blocks,
63/64 boundaries, retained-parity ties and saturation.

Integration seeds 17/89/211 cover K=1/2/4, native BF16/FP16 and W4/W2,
dense/sparse, both native KV formats. Require accepted lengths 1/2/3/4,
branch/chain/duplicate/mismatch/isolation, invalid traffic, rollback/readback,
cancel/fault in every phase, stale responses, reset, metadata/fill errors,
all-interface backpressure and publication stalls. Require zero scoreboarding
mismatches/X/Z, compact, partial-tile, medium and production execution.
Layer/logit comparisons require NRMSE <=0.01 and cosine >=0.999 against
an independent floating-point reference with identical activation boundaries
and actual checkpoint/quantization. Greedy speculative output must exactly
match non-speculative target inference under the same mode/KV policy.

All eight admitted mutations must actually execute and trigger the intended
assertion, not merely fail compilation or time out. Synthesis checks the
complete real hierarchy, storage/arithmetic retention and zero latches/black
boxes. Clean reproduction copies only declared sources/manifested inputs,
elaborates the top, runs independent compact numerical/transactional/A8
smoke and zero-latch synthesis without private paths or cached binaries.

The five domains are dialogue/instruction, mathematics, code, factual
knowledge and logic, with >=20 prompts/domain and >=128 generated tokens
unless EOS; >=1000 committed generated tokens/domain/cell. All admitted
K/mode/KV cells, including separately reported FP16, require actual execution.
Report end-to-end accepted-token TPM including rejected drafts and all overhead,
prefill/decode, actual DDR bytes, acceptance distribution and measured frequency.
A declared production K=4 sparse/mixed configuration must sustain >=3500
aggregate decode TPM and >50% actual bytes/token reduction versus K=1 native
BF16 dense. Execute both HT and Q2-FP baselines on the same board/corpus/
accounting boundary, report per-domain values and quality versus BF16.
The objective's 930 TPM is not this run's measured baseline.

Shared-runtime L1.5 timing lint, L2 Quartus 17.1 STA and L3 Arria 10
PCIe Gen3x8 HIL remain mandatory; HIL needs three consecutive deterministic
passes. Production fit, 512-DSP mapping, WNS >=0 at <=10 ns and no
unconstrained functional paths require actual Quartus evidence, not generic
cells. No timing waiver is admitted. Product PDF is runtime-owned and follows
independent engineering acceptance, never an L1 prerequisite.
