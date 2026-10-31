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
HT2_STATUS is read-only: bit 0 operation busy, bit 1 quiescent, bit 2 native
committed cache valid, bit 3 sticky fault; all remaining bits are zero.
The internal mode-control adapter serializes extension and forwarded legacy
configuration transactions. A forwarded request owns the downstream response
until it is captured or drained after cancellation. Invalid writes never
partially update mode/K.

`anvil_q2_ht2_configuration` now connects this adapter to the unchanged parent
configuration controller in legacy mode and to a separate native controller
otherwise. It is an internal subsystem, not the still-missing product top.
Every mode-bit change invalidates native descriptor publication; legacy
configuration is reset on a mode change or explicit configuration invalidation.
Software must revalidate the model after changing mode, and rewrite legacy
shadow configuration when returning to legacy mode. Native shadow descriptors
survive invalidation; a failed validation leaves the preceding committed bank
unchanged. K-only changes do not discard descriptor banks. Top-level cache/DMA
invalidation and quiescence enforcement remain integration obligations.

The legacy configuration register addresses remain:

| Address | Access | Meaning |
|---|---|---|
| `0000` | R | Product family ID `41513248` |
| `0004` | R | Native revision `02050002`; parent revision in legacy mode |
| `0008` | R/W | Command: 0 no-op, 1 validate/publish, 2 invalidate; reads zero |
| `000c` | R | Bits 0 loaded, 1 busy, 2 sticky fault, 3 DDR ready |
| `0010` | R/W | Legacy weight selector shadow, values 0..1 |
| `0014` | R/W | Legacy cache selector shadow, values 0..2 |
| `0018`, `001c` | R/W | KV base low 32 bits and bit 32 |
| `0020`, `0024` | R/W | KV extent low 32 bits and bit 32 |
| `1000+64*i+4*w` | R/W | Shadow descriptor i, 32-bit word w (0..15) |

In native mode `0010`/`0014` retain readable/writable legacy shadows but
do not override HT2_MODE's native weight/KV policies. Writes above one to
either 33-bit address/extent high word error without changing the shadow.
Configuration writes require quiescence. Validation reserves the full native
MAX_SEQ_LEN+4-page cache extent, checks every descriptor and all region
overlaps, copies to an inactive RAM bank, then switches the committed bank
in one edge. Only byte-identical embedding/head payload aliasing is allowed;
all other payload/metadata/cache overlap is an error. Cancellation abandons
validation without bank publication and returns an error to drain an accepted
internal configuration request. Uninitialized shadow words read as zero.

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

There are `16+16*NUM_LAYERS` descriptor entries. Native descriptor roles and
shapes retain the parent's index assignment:

| Entry | Role | Rows | Columns |
|---|---|---|---|
| 0 | Token embedding | VOCAB_SIZE | HIDDEN_SIZE |
| 1 | Vocabulary projection | VOCAB_SIZE | HIDDEN_SIZE |
| 2 | Final RMSNorm gamma | 1 | HIDDEN_SIZE |
| 3 | RoPE coefficient table | MAX_SEQ_LEN | HEAD_DIM |
| `16+16*l+0`, `+3` | Q, attention output projections | HIDDEN_SIZE | HIDDEN_SIZE |
| `16+16*l+1`, `+2` | K, V projections | NUM_KV_HEADS*HEAD_DIM | HIDDEN_SIZE |
| `16+16*l+4`, `+5` | SwiGLU gate, up projections | INTERMEDIATE_SIZE | HIDDEN_SIZE |
| `16+16*l+6` | SwiGLU down projection | HIDDEN_SIZE | INTERMEDIATE_SIZE |
| `16+16*l+7`, `+8` | Layer input, post-attention RMSNorm gamma | 1 | HIDDEN_SIZE |
| `16+16*l+9` | Q bias | 1 | HIDDEN_SIZE |
| `16+16*l+10`, `+11` | K, V bias | 1 | NUM_KV_HEADS*HEAD_DIM |
| 4..15, `16+16*l+12..15` | Reserved | Entire descriptor is zero | Entire descriptor is zero |

Here l is 0..NUM_LAYERS-1. In native mode all payloads are row-major,
including projection weights; the parent legacy mode retains its tiled layout.
Vocabulary and layer projection formats follow HT2_MODE's weight selection:
native uses the selected activation format; W4/W2 use flags `100`/`103`.
Embedding, gamma, bias and RoPE descriptors always use the selected native
format (`101`/`102`). Native elements and row strides are two-byte aligned.
Quantized payloads/zero points may begin at any byte; scale bases and strides
are two-byte aligned. Native descriptors have zero metadata addresses/strides.
RoPE rows contain interleaved cosine/sine pairs for HEAD_DIM/2 rotary pairs,
with each coefficient stored in the selected native format. Their checkpoint
configuration/provenance and model sequencing are still required; an address
validator does not establish correct RoPE coefficients or execution.

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

Admitted recovery A9 adds unsigned one-bit `s_weight_fp16` to
`anvil_q2_ht2_tile_batch_mac`. `s_fp16` selects only the activation format;
`s_weight_fp16` independently selects the weight format (0 BF16, 1 FP16).
Each lane captures both operands' decoded significands, exponents and
classifications on the same enabled edge. There is no additional conversion
or rounding boundary. All four selector combinations are defined. Native
descriptor flags select their validated weight format; W4/W2 outputs always
select BF16, including when activations are FP16. Selectors are transaction
payload and obey the same input hold/acceptance rules as operands. A9 changes
neither the seven product stages nor the 39-stage MAC, masks, errors or tags.

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

The internal metadata tile reader accepts a validated descriptor, logical row,
128-aligned starting column, four native activation tiles, masks and tag.
It recomputes the exact active-slot union, rejects tail keep bits outside the
descriptor's columns, and reads only quantization groups required by that
union. Two cached aligned beats independently hold zero-point and scale data;
annul invalidates both and drains an accepted read. Expansion returns zero
points in four bits/lane, BF16 scales in 16 bits/lane, effective per-slot keeps
and the computed payload byte address. Padding bits in a fetched final
zero-point byte must be zero; nonfinite required scales and memory errors
return errors, not usable zero-filled metadata. Skipped groups have no reads.

`anvil_q2_ht2_weight_path` connects this reader to the frozen sparse DMA and
serializes their accepted memory ownership. It forwards aligned read requests
with actual beat counts and holds captured activations/masks/tag until the
decoded shared weight tile is consumed. Errors suppress usable tensor payloads.
Annul drains the old burst before accepting another tile. The surrounding
memory fabric must hold fill data under backpressure and mark the last beat;
the path checks that marker against its accepted request length. Missing
termination cannot be treated as a successful response or silently timed out.
This subsystem does not implement the model sequencer. A9 supplies independent
MAC operand selectors without converting or reinterpreting reconstructed
weights. The connected tensor engine retains the command's activation mode and
uses the captured weight-path response format to select the weight decoder.
Neither selector comes from live configuration while a tile is in flight.

The internal tensor engine owns an activation store, a weight path, the physical
four-slot MAC and the ordered row accumulator. A command names a published
descriptor, activation vector, contiguous row range, active-token mask, native
activation format, weight policy, sparsity policy and tag. It returns one
unbiased FP32 row for all active tokens at a time; model bias addition and
activation-boundary rounding belong to the subsequent model operation, not
repeated column-tile processing. Descriptor columns are scanned in increasing
128-column tiles; masks exclude the final tile's unused columns. A tile is
shared across all active tokens and its error terminates the command with one
error-marked last response, not a successful partial row. This is a connected
projection subsystem, not full-model execution.

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

### Native cache storage layout

The internal native cache controller uses physical token pages and a logical
position map. This does not change legacy cache addressing. For CACHE_BLOCK=B,
let H=HEAD_DIM/B and R=2*NUM_KV_HEADS*H. Each physical token page has
NUM_LAYERS*R records. Record order is increasing layer, K then V, increasing
KV head, increasing block. Records are contiguous, without per-record
alignment padding. The BF16 record length is 2*B; the INT8 length is B+2.
Page byte stride is NUM_LAYERS*R times the selected record length.
Physical page p begins at configured base plus p times the page stride.
The base is 64-byte aligned. The region must contain MAX_SEQ_LEN+4 physical
pages, rounded up to a 64-byte boundary, within the 33-bit address space.
Every accepted external request transfers one aligned 64-byte beat; partial
writes use byte enables and reads include alignment/padding traffic.

Four scratch pages are distinct from every committed page. At successful
response consumption, selected scratch IDs map to consecutive logical
positions in selected-path order, in the same edge as the tree pointer update.
The four-bank logical map can write all four consecutive positions on that
edge, including wrap between bank three and bank zero. Subsequent scratch
replenishment must finish before the next batch can be accepted.
Failed/cancelled batches do not change the map, pointer, committed origin or
allocation cursor. Aborted physical writes remain confined to scratch pages.

For a successful new sequence, the logical origin becomes the supplied
position and old committed mappings become unreachable atomically. Queries
below that origin are errors, never stale reads. New-sequence computation
cannot read the preceding sequence as a prefix. Format/base/extent cannot
change while committed native cache state exists, even for a new-sequence
offer: differing physical layouts could alias the old committed data before
publication. The top's still-required quiescent configuration invalidation
must reset the native cache controller before adopting an incompatible layout,
after all accepted memory transactions drain. Batch annul is rollback, not
cache invalidation, and must preserve the previous committed state.

The internal write scheduler orders each slot's records by increasing layer
and then increasing record ordinal within the layer. Slots may interleave.
A layer completion bit becomes true only after successful acknowledgement of
every beat of every K/V record for that layer. Reads of provisional records
require an acknowledged preceding write, and translation exposes only the
requesting node's ancestors/self at their path-depth positions. Protocol,
codec, bounds or memory errors propagate to the batch error path and prohibit
publication.

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
| Conversion | Four registers, valid after n+3; first consumption n+4; format/direction/tag stall together |
| FP32 multiply helper | Seven registers; operands at n produce result after n+6; caller advances all sidebands identically |
| Row accumulation | Four-stage addition; first tile initializes without changing signed zero; next dependent tile waits for retirement at n+4 |
| Single-tile row | First and last coincide; one response after n+3, earliest consumption n+4 |
| Activation read | Registered RAM read at n, response after n+1, first consumption n+2 |
| Activation read/write collision | An accepted legal full-tile write forwards new data and keep bits to a simultaneous read of the same slot/address |
| Activation tile overwrite | Replaces the full tile and keep bits; not a partial merge with the previous tile |
| Activation annul | Clears reset-protected tile validity and cancels responses; data RAM is not reset |
| KV map query | Registered map read at n, response after n+1; held query blocks finishing/publication |
| KV final write beat | Accepted memory acknowledgement updates record progress; only the last record can set layer completion |
| KV annul with accepted memory request | Suppress ordinary responses and drain that request before accepting another batch |
| KV new-sequence publication | Discard old logical visibility on publication, never at offer/acceptance of the batch |
| KV scratch replenishment | Scan past four excluded seed pages with explicit bounds; no power-of-two wrap or page reuse while committed |
| Extension configuration | Local response after acceptance n; forwarded request offered after n and held until downstream acceptance |
| Mode/K write during active work | Error response, no mode/K mutation or change pulse |
| Mode/K change indication | One post-edge pulse on successful changing write; invalid/no-op writes have no change pulse |
| Configuration cancellation | Drop unaccepted forwarded offer; drain accepted downstream response before accepting another request |
| Native descriptor leaf | Capture at n; region/error response after n+5; earliest consumption n+6 |
| Native descriptor publication | Only final inactive-bank copy edge switches the committed bank; validation error/annul leaves it unchanged |
| Native metadata, no metadata reads | Capture at n; native/wholly skipped result after n+5; earliest consumption n+6 |
| Metadata group boundary | GROUP_SIZE=1 scans at most 128 groups; GROUP_SIZE=128 scans one; no metadata for an unrequired group |
| Partial tile at address-space end | DMA bounds actual required aligned beats, not masked columns beyond the descriptor's final column |
| Weight-path annul | Child response validity is annulled immediately; live accepted burst owner remains until its final fill transfer |
| A9 operand formats | Both independent decoders capture at the same enabled edge; output stalls freeze all decoded state; annul prevents old valid results |
| Tensor command | Capture at n; validate retained command before any activation or memory request; no same-edge row response |
| Tensor single column tile | First and last coincide; the row accumulator initializes once and returns one unbiased FP32 row |
| Tensor partial column tile | Only columns below descriptor width enter activation reads, sparse union and MAC keeps |
| Tensor nonlast column tile | Wait for row-accumulator dependency retirement before requesting the next increasing tile |
| Tensor row response stalled | Row, FP32 sums, mask, tag, last and error hold; no next-row read or command acceptance |
| Tensor activation write and command | Write offer has priority; command waits for outstanding write response retirement |
| Tensor annul/fault | Annul suppresses output and drains weight ownership; fault flushes arithmetic state before the terminal error response; no next command before drain |
| Native shared-memory request | Capture one weight-burst owner; serialize its aligned beats onto the parent's acknowledged single-beat client without duplicating a weight stream |
| Native shared-memory fill | Hold each returned beat/error/last under fill backpressure; advance address only on fill consumption |
| Native shared-memory annul | Suppress new bursts; finish all beats of an already accepted burst and deliver its terminating fill to the draining owner before reuse |
| Native shared-memory invalid burst | Return an explicit terminal fill error without issuing DDR traffic |
| Native shared-memory counters | Increment only on actual accepted Avalon read/write commands; do not reset on batch annul or count suppressed/hypothetical reads |

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
A9 additionally requires independent bit-exact checks of all four
activation/weight selector combinations, alternating formats, backpressure,
annul, signed zeros, subnormals and specials. These augment the existing
checks; no original threshold or required check is replaced.

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
