# Anvil-D2 frozen implementation contract

Version: `2.0.0-deepseek-r1-mtp-fp8`. Intended product top:
`anvil_d2_top`. Target: Intel Arria 10 GX `10AX115N2F45E1SG`,
one clock, period at most 10.0 ns.

## Status and provenance

This document records the independently admitted contract, not acceptance
results. The initial project supplies 27 unchanged files under
`anvil_d1_reference/rtl/`. No repository-intake source index,
`design/GENERATIONAL_HANDOFF.md`, original `anvil_q3_bank_scheduler`,
original `anvil_q3_top`, checkpoint, tokenizer or benchmark manifest is
provided. Do not equate implementation work with recovery of those inputs.
Parent compatibility and historical physical PPA remain unproven without
the corresponding original inputs.

Designer owns `rtl/*.sv`, this file, `design/ARCHITECTURE.md` and
`fpga/quartus_gate.json`. Independent Verifier owns `tests/*`. Functional
simulation, reference models, mutations and synthesis belong to Verifier.
The shared runtime owns timing lint, Quartus STA, physical hardware gates,
engineering state and the later independently approved product PDF.

The current integrated implementation inventory is in `ARCHITECTURE.md`.
Native draft/target compute and FP8 consumers are connected in
`anvil_d2_top`; their presence is not numerical, behavioral, synthesis or
timing acceptance.

## Public interface and parameters

Retain every parameter, default, port width and signedness of
`anvil_d1_reference/rtl/anvil_d1_top.sv`. Add integer parameter `MTP_K=4`
and the following ports:

| Port | Direction | Meaning |
|---|---|---|
| `spec_valid`, `spec_last` | output wire | Held committed beat / final beat of block |
| `spec_ready` | input wire | Retirement permission |
| `spec_token`, `spec_pos` | output wire [31:0] | Token and absolute position |
| `spec_count`, `spec_accepted` | output wire [2:0] | Visible block size and accepted draft-prefix length |

The memory interface remains BANKS-flattened, 32-bit data, 64-bit tags;
CSR addresses remain 12 bits. No external draft/verdict ports are allowed.
Outside generation every speculative output is zero.

Native bounds and all inherited address-product constraints remain:

| Parameter | Legal values |
|---|---|
| `NUM_LAYERS` | 1..36 |
| `HIDDEN_SIZE` | 8..2048, multiple of 8 |
| `INTERMEDIATE_SIZE` | 8..11008, multiple of 8 |
| `NUM_Q_HEADS` | 1..16 |
| `KV_LORA_RANK` | 1..512 |
| `QK_NOPE_HEAD_DIM` | 1..128 |
| `QK_ROPE_HEAD_DIM` | even, 2..64 |
| `V_HEAD_DIM` | 1..128 |
| `ROUTED_EXPERTS` | 1..64 |
| `TOP_K` | 1..min(6, ROUTED_EXPERTS) |
| `SHARED_EXPERTS` | 2 |
| `MOE_INTERMEDIATE_SIZE` | 8..1408, multiple of 8 |
| `FIRST_DENSE_LAYERS` | 0..NUM_LAYERS |
| `VOCAB_SIZE` | 4..151936 |
| `MAX_SEQ_LEN` | 1..32768 |
| `BANKS` | 1, 2, 4, 8 |
| `QUEUE_DEPTH` | 1..16, including non-powers of two |
| `TILE_K` | 8..128, multiple of 8 |
| `TILE_ROWS` | 1..8 |
| `GROUP_SIZE`, `MTP_K` | 128, 4 |

Native validation must retain these 32-bit address limits: heads times
value dimension, heads times latent rank, heads times RoPE dimension,
3H, 3R, R+RoPE, `4*MAX_SEQ_LEN*(R+RoPE)`,
`4*H*MOE_INTERMEDIATE_SIZE`, `4*H*INTERMEDIATE_SIZE`, and
`4*H*VOCAB_SIZE`. Evaluate products with sufficiently wide unsigned
constants. Illegal settings must reach an explicit `PARAMETER ERROR`;
diagnostic-safe port widths and legal-datapath generate guards must prevent
earlier illegal selects/arrays. Native-only bounds must not change legacy
`MODEL_MODE=1` legality.

## Cycle & degenerate-boundary table

An event means a pre-edge `valid && ready` handshake. Merely asserting
valid never advances a token frontier or transfer counter.

| Boundary / simultaneous event | Required post-edge behavior |
|---|---|
| `rst_n=0` | Public valid/ready/strobes/payload/status/counters zero immediately; documented configuration defaults apply |
| First release edge | Set arming; no pre-edge transfer is accepted |
| Input handshake at E | Capture exactly one item; changing pins after E is not another item |
| Stalled request/response/output | Hold full payload, tag, status and metadata; no retirement |
| Accepted response at E | Enter a registered consuming stage after E; no same-edge data shortcut |
| Dequant input at E0 | Unpack after E0; product after E1; binary32 after E2; BF16/output after E3; earliest retirement E4 |
| Dequant downstream stall | Each register advances only if its successor has space; no bypass |
| Flush/cancel and issue/completion together | Flush/cancel wins, annuls unpublished output, drains already accepted requests |
| Reset/flush in any arithmetic stage | Discard all in-flight items, without a delayed publication |
| Counter clear and snapshot/increment | Clear wins; snapshot captures pre-edge live values otherwise; increment updates live values |
| Queue depth 1 | Full/empty and ownership remain exact; no zero-width pointer or assumed second slot |
| Queue depth 3 or other non-power of two | Explicit terminal wrap, never binary-overflow wrap |
| Group length 1 | One valid source and byte; no unwritten RAM tail participates in maximum |
| Group lengths 2,3,127 | Real valid elements only; final packed word padded with zero |
| Group length 128 | Exactly one scale and 128 payload bytes |
| Lengths 129,255,256 | Split into independent groups; never cross tensor-row boundaries |
| `MAX_SEQ_LEN=1` | Parent-compatible input processing legal; generation has zero capacity and fails |
| Publish handshake of final beat | Retire once; materialize final target state if pending; do not complete early |
| COMPLETE state | One-cycle done; token_ready remains zero, returns only in following armed idle state |
| Held cancel | One completion after drain/release, not repeated pulses |

Synchronous storage write/read ports must reside in a clock-only process,
without asynchronous RAM clearing. Reset validity/ownership, not bulk RAM.
Never read an uninitialized entry as a live item.

## CSR contract

Preserve all parent identification, reasoning markers, domain IDs 0..4,
access, busy, strobe, snapshot and error rules.

| Address | Access/reset | Meaning |
|---|---|---|
| `0x280` | RO, `0x00020000` | D2 version |
| `0x284` | RW, 0 | bit 0 MTP enable, bit 1 FP8 enable |
| `0x288` | RW, 1 | Generated-token limit, 1..MAX_SEQ_LEN |
| `0x28c` | RW, VOCAB_SIZE-1 | EOS token, 0..VOCAB_SIZE-1 |
| `0x290` | RW, 0 | bit 0 generation enable, independent of feature bits |

Reserved bits must read zero; writing any reserved bit is an error.
Configuration writes require full strobes and idle with no active token,
speculative block, pending materialization, outstanding memory or unpublished
output. An invalid write responds with `csr_error` and changes nothing.
In MODEL_MODE=1, attempts to enable generation, MTP or FP8 explicitly fail.
Generation policy survives completion and cancellation.

Snapshot-based 64-bit counters start at `0x300`, low then high, eight-byte
stride: generation cycles; retired generated tokens; proposed tokens;
committed accepted draft tokens; rejected blocks; cache payload read bytes;
cache payload write bytes; cache scale bytes; expert payload read bytes;
expert scale bytes; verification-active cycles. Counters measure executed
cycles or actual handshakes, not predicted byte savings. Preserve the parent
clear-before-snapshot priority.

## Command classification, positions and completion

Classify only on an accepted public command. Generation entry is exactly
`MODEL_MODE==0 && generation_enable && token_phase`. The four feature values
0,1,2,3 select sequential uncompressed, MTP uncompressed, sequential FP8,
and combined generation. Feature bits never implicitly enable generation.
Reset preserves parent logit transactions for either token_phase value.
With generation policy set, token_phase=0 is still a non-generation prefill.

The input token is a newly supplied real seed at absolute position p.
Materialize its target hidden state/KV before selecting target anchor b.
The first emitted token is b at p+1. `new_sequence=1` requires p=0 and a
new epoch after old work is discarded/drained. Otherwise the sequence must
be valid and p must be the next unmaterialized position. Reject invalid
IDs, positions, discontinuities and prefill after decode through a failed,
drained completion. Never silently substitute a position.

The limit counts only generated beats retired on the committed stream:
not the seed or prompt, not rejected drafts. At most
`min(generation_limit, MAX_SEQ_LEN-1-p)` tokens become visible. A seed at
MAX_SEQ_LEN-1 fails with no output and invalidates continuation. A nonzero
capacity tail shortens successfully. First retired generated EOS terminates
the command; seed EOS does not count as an emitted EOS.

For g outputs, positions are p+1 through p+g. All outputs, including the
last correction/all-accepted tail, must have target hidden/KV materialized
before done. The next caller supplies a NEW seed at p+g+1; no replay of the
last output. EOS retains materialized continuation context. A full sequence
requires a new sequence at zero.

During compute, stalls, final materialization and drain token_ready is zero.
No public logit handshake occurs during generation; all logit outputs are
zero, independently of logit_ready. Non-generation retains the inherited
full vocabulary logit transaction, completion and next-position p+1.

| Controller phase | Exit condition / effect |
|---|---|
| IDLE / command classification | Accepted public command, validate seed/position/policy |
| SEQUENCE_FLUSH / DRAIN | Annul old speculative state; wait for accepted memory work |
| SEED_MATERIALIZE | Embedding, all target layers, final norm and target logits |
| ANCHOR | Greatest target logit, smallest token ID on ties |
| DRAFT | Sequentially compute up to four native independently weighted heads |
| VERIFY_LAYER / BARRIER | Four causal lanes; all required earlier candidate K/V available at each layer |
| VERDICT | Register longest matching prefix; discard rejected suffix |
| PUBLISH | Distinct registered state, stable committed stream under stalls |
| PENDING_MATERIALIZE | Complete any emitted token without target state; acknowledge writes |
| NEXT_BLOCK | Use fully materialized committed context; never replay emitted tokens |
| COMPLETE | One-cycle successful done after all retirement/materialization/drain |
| ABORT_FLUSH / DRAIN | Invalidate continuation and unpublished work; drain accepted memory |
| CANCEL_COMPLETE | Preserve inherited idle/active cancellation distinctions |

Count/accepted describe only the visible, terminal-truncated block and are
constant on all its beats. last marks the block boundary, not command
completion. Sequential generation publishes count=1, accepted=0, last=1.
Error/cancel preserves already observed output history but requires a new
sequence before subsequent success.

### Integrated engine cycle and ownership table

The implementation uses registered state transitions. A row labeled
"handshake" samples pre-edge valid AND ready; a row labeled "cycle"
does not imply that a transfer occurred. Target results remain in HOLD
while the engine reads hidden vectors or executes head-history appends.

| Engine state(s) | Edge condition and registered effect |
|---|---|
| IDLE | Public token handshake captures seed, phase, generation policy, features, limit and EOS; invalid input enters abort without executing it |
| CONTEXT_FLUSH | One cycle invalidates target/head/FP8 ownership and pulses scheduler flush; used for a new sequence or context replay |
| CONTEXT_DRAIN | Wait for both scheduler drain and complete transport idle; never issue a target during drain |
| JOURNAL_READ / JOURNAL_CAPTURE | Synchronous actual-token/phase RAM read, then capture one prior context token; no public output |
| TARGET_COMMAND | Internal target command handshake captures seed, replay token, four-lane verification block or pending final token |
| TARGET_RESULT | Target result handshake registers actual greedy predictions; seed/replay/materialization proceed to commit; verification proceeds to verdict |
| TARGET_COMMIT / TARGET_COMMIT_WAIT | Internal prefix-commit handshake, then wait for all selected target-cache write acknowledgements |
| APPEND_SELECT / APPEND_SWITCH | Select a retained target lane; change to draft transport ownership only after full transport idle |
| APPEND_COMMAND | Actual-token head-history command handshake; position 0 explicitly restarts head history |
| HIDDEN_REQUEST / HIDDEN_RESPONSE | Indexed lane-local hidden read handshake and separate registered response consumption |
| HIDDEN_FEED | Head-history input handshake for exactly one hidden component; loop for H components |
| APPEND_WAIT / APPEND_DRAIN | Wait for actual native head computation/commit completion and idle transport before restoring target ownership |
| TARGET_RELEASE | Release handshake only after target commit, no pending hidden response and full transport idle |
| AFTER_TARGET | Replay advances to the next saved position or seed; seed sets next position; verification selects last-lane prediction or pending-token materialization |
| BLOCK_PREPARE | One cycle bounds depth to min(4,remaining limit-1,remaining capacity-1); zero depth selects singleton publication |
| DRAFT_SWITCH / DRAFT_COMMAND | Idle transport ownership switch followed by sequential native draft command handshake |
| DRAFT_RESULT / DRAFT_WAIT / DRAFT_DRAIN | Capture independently computed drafts, wait for private-head rollback completion and idle transport, then select target verification |
| VERDICT_COMMAND | Handshake passes actual anchor/draft/target predictions to the verdict leaf; it registers decision before publishing |
| PUBLISH | Only committed-output handshakes advance visible position, journal and generated-token counts; stalled payload/metadata remain fixed |
| PUBLICATION_WAIT | Distinct block-publication completion; choose terminal-truncated materialized prefix, never rejected suffix |
| BLOCK_FINISH | After required final materialization, either begin another block or enter COMPLETE |
| COMPLETE | One cycle done, error only on failure; token_ready=0; following cycle enters IDLE |
| ABORT_FLUSH / ABORT_DRAIN | Annul unpublished work, invalidate sequence and drain accepted tagged memory before failed completion |
| CANCEL_COMPLETE | One pulse after cancel release/drain; failed done accompanies it only when a public command was active |

The journal contains one 33-bit actual token/phase per legal sequence
position, never hidden/model vectors. It is written only on a legal
seed handshake or generated-output retirement. If MTP is enabled after
unprimed actual tokens, replay positions 0 through seed_position-1 to
build true hidden/head history. A precision change also replays that
actual context with the newly selected arithmetic, rebuilding target
cache and absorption state. Both use a fresh internal epoch, emit no
public replay logits/tokens, and include all replay work in cycle/byte
costs. Already observed tokens are not regenerated or changed.

For a verified block commit
`min(spec_count,spec_accepted+1,active_verification_lanes)` leading target
rows after the final output handshake. Each retained row's unnormalized
hidden vector primes actual-token head history before release.
Any final visible correction or all-accepted tail without target state
is materialized exactly once through the one-lane target before
BLOCK_FINISH. No public handshake is generated by that materialization.
For a singleton block the anchor itself is this pending token.

The 29 target memory clients share slots 0..8 with the nine draft
clients only in nonoverlapping phases. A registered owner changes only
after adapter, group service and scheduler idle. Hidden reads during
head priming remain lane-local. The FP8 group service owns scheduler
slot 29, for 30 total clients. Native target verification still launches
all active lanes concurrently and retains explicit per-layer barriers;
transport reuse does not serialize the four decoder invocations.

## Native MTP and parallel target verification

Required literal hierarchy: top instance `mtp` of
`anvil_d2_mtp_engine`, and top instance `fp8` of
`anvil_d2_fp8_mla_moe`.

For each depth execute
`Transformer_head(Projection_head(concat(RMS_hidden(h_previous),
RMS_embedding(Embedding(token_previous)))))`, then shared output projection
and deterministic argmax. Gains, concatenation projection and transformer
weights are programmable per head. Tied images are permitted explicitly,
but distinct heads must never silently share weights. Execute real
attention/MLA, residual and dense/MoE paths, not token lookups or
externally fabricated predictions.

From fully materialized context, select anchor b. Head 0 consumes context
hidden and Embedding(b) to propose d1; later heads consume preceding hidden
and embeddings d1,d2,d3. Four target-query lanes evaluate [b,d1,d2,d3] in
one causally masked block to predict [v1,v2,v3,v4]. At each layer use an
immutable committed prefix and appropriate earlier candidate positions,
never future lanes. Broadcast committed cache reads, retain separate query,
softmax and context accumulators and impose explicit per-layer barriers.
All four lanes must overlap on a nontrivial verified attention window;
four serial complete target invocations are forbidden.

Let a be the longest matching draft prefix. For a<4, publish
[b,d1..da,v(a+1)]; otherwise publish [b,d1,d2,d3,d4]. Stop at the first
mismatch. Shorten for EOS, capacity and remaining limit BEFORE publication.
Materialize any emitted final token not covered by target evaluation.
Keep draft and target scratch isolated until the verdict; no rejected KV
may become committed. Exact sequence equivalence is required versus a
sequential target with identical weights and numerics.

## FP8 numerical contract

E4M3FN: sign bit 7, exponent bits 6:3, fraction bits 2:0, bias 7.
Exponent zero is signed zero/subnormal, magnitude `fraction*2^-9`.
Normal magnitude is `(8+fraction)*2^(exponent-10)`, including exponent
15 fractions 0..6. Maximum finite is 448. Exponent 15 fraction 7 is NaN.
Decode every code. Scales are positive finite nonzero IEEE binary32;
negative, signed zero, infinity and NaN scales explicitly error.

Compute the exact FP8 times scale product; round to binary32 nearest,
ties-even with gradual underflow; derive BF16 nearest, ties-even FROM
that binary32 result. Preserve floating signed zero. Any rounded overflow
to nonfinite explicitly errors. An errored dequant transaction publishes
out_error=1 and zero data, never a successful substitute.

The leaf `anvil_d2_fp8_dequant` has the specified clk/rst_n/flush,
in_valid/in_ready, in_fp8[7:0], in_scale[31:0], out_valid/out_ready,
out_fp32[31:0], out_bf16[15:0], out_error ports. It has exactly four
elastic register stages (unpack, product, binary32, BF16/publication), no
unstalled bypass, and the E0..E4 schedule in the boundary table.

Native tensor boundaries remain signed Q16.16. FP8 consumers widen BF16
exactly to FP32, then convert to signed Q16.16 nearest, ties-away-from-zero
with signed-32 saturation, before parent-compatible wide MAC/absorption.
Do not call this an all-FP32 transformer. Preserve parent-compatible
rounding/saturation, wide absorption, RMS epsilon and nonlinear rules
in uncompressed mode.

Cache group scaling uses the smallest representable positive power of two
satisfying `max_abs<=448*scale`, scale 1 for an all-zero group. Quantize
actual Q16.16 inputs divided by scale to E4M3FN nearest ties-even, saturate
to finite 448, never NaN. Unwritten tails do not participate. For Q16.16
nonzero groups the legal selected scale exponents range from -24 to 7.
Expert input scales may be arbitrary positive finite binary32, not just
these powers of two.

Each group contains at most 128 components and cannot cross row, layer,
expert or projection boundaries. Store one four-byte FP32 scale and packed
payload, four bytes per word, earliest component in bits 7:0. Pad only
the last word with zero. Payload and scale ownership/validity are atomic
under replacement, epoch change and cancellation. Expert ownership includes
current expert/layer/projection/group.

## Memory identities, ownership and bandwidth

Retain parent address meanings in compatible mode. In FP8 mode use kind
13 for payload, kind 14 for FP32 scale; proj 3 is latent cache, proj 5 is
routed-expert matrices. Layer/row retain logical tensor identities. For
logical component c, payload col is `c>>2`, scale col is `c>>7`.
RoPE/expanded unrelated tensors must not be relabeled latent savings.

MTP-only parameters use kind 12, layer NUM_LAYERS+head_index, head_index
0..3. Projection 0 is H by 2H concatenation, projection 1 hidden RMS gain,
projection 2 embedding RMS gain. Native decoder tensor roles and remaining
head parameter projections use the map below. Shared embeddings/output
retain parent identities.

### Native draft transformer mapping and private context

The four native MTP transformers use the native decoder arithmetic with
independently addressed attention, residual and routed/shared-MoE weights.
All four additional heads are MoE layers, beyond FIRST_DENSE_LAYERS in
the target stack. This does not change the target dense-layer parameter.
The physical arithmetic may be reused sequentially between depths; weights
and absorption ownership are indexed by depth, never implicitly tied.

All entries below have kind 12 and layer NUM_LAYERS+head. The row/column
encoding is a tensor identity, not a byte-address multiplication.

| Projection | Row | Column / tensor |
|---|---|---|
| 0 | output component | hidden-first 2H concatenation input component |
| 1, 2 | 0 | hidden/embedding input RMS gain component |
| 3 | 0, 1, 2 | attention, FFN, final-output RMS gain component |
| 4 | native MLA raw row, high nibble 0..6 | Native raw MLA matrix column, unchanged |
| 4 | `0x70000000 + expert` | H-component router affinity row |
| 4 | `0x80000000 + absolute_position` | RoPE cosine/sine pair components |
| 5 | `{expert[6:0],matrix[1:0],output_row[22:0]}` | Native gate/up/down matrix (matrix 0/1/2), or bias (matrix 3, col 0/1/2) |
| 6 | absolute candidate position | Head-private committed latent then RoPE components |
| 7 | `{query_head[3:0],matrix_b,27-bit_output_row}` | Three-word exact signed-96 absorbed coefficient; A uses matrix_b=0, B uses 1 |

Router/rotary prefixes do not overlap raw MLA rows. The new absorbed B tag
uses row bit 27; legal native output dimensions use only bits 10:0.
Shared token weights keep kind 0, layer/projection 0. Head hidden, query
and FFN scratch remains local and does not occupy these external rows.
FP8 routed matrices retain projection 5, use kinds 13/14 and the same
NUM_LAYERS+head and encoded expert row; bias rows are not compressed.
MTP-private latent context is separate from target latent context and is
not counted as target-cache compression.

Head d's first valid hidden state is at absolute position d+1, formed
from the previous-depth state one position earlier and the actual token
at that position. The reused native decoder runs relative position
`absolute_position-(head+1)` so its causal scan has no nonexistent
leading states. Translate its cache row and RoPE table row back to
absolute positions. Do not shift the RoPE angle or include dummy prefix
keys in the softmax denominator.

Maintain a contiguous committed frontier per head, initialized to d+1.
Before speculation the generation controller must warm every applicable
head over actual committed context. A speculative diagonal additionally
needs the earlier-position states of later heads: execute the triangular
dependency graph, not four unrelated decoder commands. Retain bounded
previous-depth hidden vectors for that replay. These are integration
obligations, not permission to read an uninitialized head prefix.

`anvil_d2_draft_cache` holds at most four private candidate rows per head
in synchronous RAM. A head command must append exactly at its committed
frontier plus current private count. Writes capture all latent/RoPE
components in order before causal reads. Reads below the frontier go to
the head-private committed store; reads at/above it use captured RAM.
Only explicit commit-through-position writes private rows to external
memory and advances each head frontier after acknowledgements. Commit
discards all remaining private suffix rows. Ordinary head release keeps
private rows for the following dependent head execution. Flush invalidates
both committed ownership and private ownership and requires a new epoch.

| Draft-cache boundary / edge | Effect |
|---|---|
| Reset / first release edge | Zero handshakes, then arm only; RAM contents are not validity |
| Head command handshake | Capture epoch/depth/absolute position; reject discontinuity, overflow or fifth private row |
| Latent/RoPE write handshake | Synchronous private RAM write; registered acknowledgement, never external publication |
| Last component write | Finish capture only after its response retires; reads then become legal |
| Private read handshake | Synchronous RAM read, held registered response |
| Committed-prefix read | One owned external request, registered consumer response after acceptance |
| Head release | Require complete capture and no response/work pending; increment private row count |
| Commit handshake | Freeze all heads; select only rows at/before committed through-position |
| Commit write response | Advance word/row/frontier only after successful acknowledgement |
| Commit completion | Discard unselected suffixes, pulse done separately, then return idle |
| Flush/error during request | Annul local ownership; shared tagged transport must drain accepted requests |
| Rank 1 / MAX_SEQ_LEN 1 | CW remains at least 3; no valid head position exists at sequence length 1 |

The native head execution schedule is projection command/capture ->
projection output/local writes -> private-cache command -> decoder ->
final RMS -> shared vocabulary projection/greedy selection -> held hidden
stream -> result -> release. Complete h_next is the decoder residual
output (scratch row 0), not final normalized output row 14. Predictions
use row 14 and smallest-ID logit tie breaking. Completion and cache release
must wait for the full hidden stream; downstream stalls cannot overwrite
the hidden vector. Memory/arithmetic errors annul unpublished head results
and latch a fault until flush. No public externally fabricated prediction
or verdict port is introduced by this internal head interface.

`anvil_d2_draft_sequence` sequences that datapath. An append command
supplies one actual target-materialized token and its H-component hidden
stream in contiguous position order. At position p execute each head
d with p>=d+1, using the retained previous-position depth-(d-1) hidden
(target hidden for d=0) and the actual token at p. A new-sequence append
requires position 0 and resets head-cache ownership. Append commits its
actual head K/V only after all computations succeed, then atomically
replaces the retained hidden history. This eager priming is required when
MTP is active; a controller enabling MTP on existing unprimed context must
replay its real token/target history before requesting a speculative block.
It must not pretend absent head state is zero or an already warmed cache.

A speculate command uses the retained committed context, a real target
anchor token at its next position and proposed depth 0..4. For column c,
execute heads c..K-1 where their first legal position has been reached.
Head c's prediction is the next diagonal proposal; later heads supply
the earlier causal states required at the next column. Column 0 consumes
committed prior-depth history; later columns consume the preceding column's
prior-depth hidden, never a future-column state. Two alternating 4H RAM
banks suffice. At K=4 and a mature prefix this executes ten transformer
passes (4+3+2+1), not four independent token lookups.

The correctness-first implementation discards **all** temporary head K/V
before publishing draft results; subsequent accepted-token append commands
recompute actual head state from the committed history. This costs replay
cycles and is not a speculative speedup claim. It prevents rejection from
publishing any head suffix and handles EOS/limit truncation without
rollback writes. Target candidate K/V commit remains independent.

| Draft sequencer state / edge | Effect |
|---|---|
| IDLE append handshake | Validate new sequence at 0, or exact epoch/next position |
| RESTART | Flush head/cache ownership for a new sequence; do not clear RAM |
| INPUT | Capture exactly H materialized target hidden components |
| SELECT | Select legal next native depth; skip only mathematically absent leading states |
| HEAD_COMMAND | Handshake with native head; freeze selected depth/token/position |
| SOURCE_READ / SOURCE_FEED | Registered history RAM read followed by held input handshake |
| HEAD_OUTPUT | Capture residual hidden stream with exact index/last checks |
| HEAD_RESULT | Record diagonal prediction; next column token is that computed prediction |
| COMMIT / WAIT | Append acknowledges actual head rows; speculate commits only through the old context, discarding private suffix |
| COPY_READ / COPY_WRITE | Copy complete append staging into retained history without exposing a partial frontier |
| RESULT stall | Hold packed computed proposals and count; committed history is unchanged |
| COMPLETE | One-cycle operation done; next command starts only in following idle |
| Reset/flush/error | Annul unpublished results; error invalidates continuation and requires a new sequence |
| Depth 0 / first context at 0 | No head executes for zero proposals; first append has only target hidden |
| Sequence tail | Reject any command that would compute or propose an out-of-range absolute position |

### MTP input projection implementation boundary

`anvil_d2_mtp_projection` implements the native head's input operation,
not the subsequent transformer or the complete MTP engine. On its command
handshake capture head 0..3, previous token and absolute candidate position;
then accept exactly HIDDEN_SIZE previous-hidden Q16.16 components. Read
the selected token's shared embedding through kind 0, layer/projection 0,
row token, col component. Independently RMS-normalize hidden and embedding
using the unchanged parent numerical primitives and epsilon.

Head weights are kind 12, layer NUM_LAYERS+head: projection 1/2, row 0,
col component for hidden/embedding gains; projection 0, row output
component, col input component for H by 2H concatenation projection.
Concatenation order is hidden first, embedding second. There is no bias.
Wide accumulation and the Q16.16 projection rounding follow the unchanged
parent tensor arithmetic. This realizes independently programmed gains
and projection for all four heads without rewriting the parent.

The previous-hidden vector, 2H normalized concatenation, and H projected
output use separate synchronous RAMs (4H signed32 words total). No
intermediate vector spills to external memory. An internal ready/valid
memory adapter acknowledges each registered RAM read/write after its
request edge; only shared embedding and actual head-weight reads reach
the external client. Output is an H-component held stream, not a token
lookup or externally supplied prediction.

| Projection state / edge | Effect |
|---|---|
| IDLE command handshake | Capture head/token/position; explicit failed completion for illegal fields |
| FILL input handshake | Store one previous-hidden component; no transfer outside this phase |
| HIDDEN_NORM / WAIT | Execute parent RMSNorm using hidden RAM and head projection-1 gains |
| EMBEDDING_NORM / WAIT | Read shared embedding; execute RMSNorm with projection-2 gains |
| Local memory request handshake | Synchronous RAM access; registered response is visible only after the edge |
| Local response stall | Hold data/status; do not admit another internal request |
| PROJECT / WAIT | Parent tensor computes H rows over 2H normalized inputs |
| OUT_READ / OUT_PUBLISH | Synchronous output-RAM read, followed by stable held component |
| Final component handshake | Enter separate one-cycle COMPLETE |
| Child memory/arithmetic failure | Flush children, annul unpublished output, failed COMPLETE then FAULTED |
| Reset/flush | Annul local response and RAM ownership; no bulk RAM clearing |
| First release edge | Arm only; no pre-edge transfer |
| Minimum H=8, any legal non-power-of-two H | Explicit final-component tests, no power-of-two wrap assumptions |

Reset zeros public handshakes/data and arming; flush/reset is required to
leave FAULTED. The head-specific transformer, residual/MLA/FFN and final
shared output projection are connected in `anvil_d2_draft_head`. This component
does not establish four native draft heads or causal verification by itself.

### MTP verdict/publication implementation boundary

`anvil_d2_mtp_verdict` is an internal consumer of actual engine results.
It is not a substitute for the required draft/target datapaths. A command
captures anchor b, up to four draft/verification pairs, first output
position, maximum visible count 1..5, and EOS. Packed pairs are depth-first
with depth 0 in bits 31:0. Proposed count 0 is the sequential anchor-only
case; counts 1..4 support bounded MTP tails.

Compute the longest matching prefix, never independent accepted-token
bits. On mismatch emit anchor, the matching draft prefix, and the first
target correction; on all-accept emit anchor and every proposed draft.
First shorten for caller limit/sequence capacity, then first EOS.
Visible accepted count is min(matching prefix, visible count minus one).
Neither later matches nor terminally discarded drafts become accepted
retirements. `accepted_retire` identifies only an actual handshake of
an accepted-draft beat; `rejected_block` is one cycle at verdict capture
for an actual mismatch, not an output-retirement count.

| Verdict state / edge | Effect |
|---|---|
| IDLE command handshake | Register all engine results and command fields; no public output |
| DECIDE edge | Register selected tokens, terminal-truncated count, accepted prefix and rejection |
| VERDICT edge | Enter distinct registered PUBLISH state; publication was still inactive before the edge |
| PUBLISH stall | Hold token, position, last/count/accepted and beat provenance |
| PUBLISH handshake | Retire exactly one beat; advance index/absolute position only after the edge |
| Final beat handshake | Enter PUBLICATION_COMPLETE; no same-edge done |
| PUBLICATION_COMPLETE | One-cycle block-publication done, not public command completion |
| Invalid command | Explicit failed publication completion, no output, then FAULTED |
| Flush/reset | Annul unpublished beats and completion; reset requires one arming edge |
| Count 0 proposals / visible limit 1 / EOS anchor | Single anchor beat, accepted 0, last 1 |
| First position at sequence end | Shorten to one beat; first position outside the sequence fails |

`publication_done` does not certify target materialization, write
acknowledgements or command completion. The engine/controller
drains/materializes the final emitted token before the public COMPLETE.
No top-level engine-result input is authorized by this internal component.

### Target-lane and speculative-cache implementation boundary

`anvil_d2_target_lanes` contains four native target decoders. Its internal
command captures epoch, first absolute candidate position, packed input
tokens (lane 0 in bits 31:0), active-lane count 1..4, phase, FP8 mode and
whether the one-lane invocation forwards the ordinary public logit
stream. Multi-lane commands cannot forward public logits. It performs
embedding, every native layer, final normalization and shared output
projection. Target predictions are held until the engine accepts them.
Target hidden vectors remain available through an internal indexed
ready/valid read interface until explicit release.

The connected `anvil_d2_verify_cache` owns raw and effective candidate
K/V in synchronous RAM, with four rows per layer, independent of
MAX_SEQ_LEN. Its layer command must precede decoder issue. Layer zero
starts a new private block; subsequent layers must have the same epoch,
positions, active lanes and precision and appear in order. Illegal
commands or malformed cache accesses latch an explicit fault, requiring
the integrated top's abort/drain path.

| Target/cache phase or edge | Effect |
|---|---|
| IDLE command handshake | Validate all active token IDs, positions and lane count; capture once |
| EMBED / WAIT | Launch all active shared-embedding paths and wait for every completion |
| LAYER_PREPARE | Establish private candidate ownership before issuing decoders |
| DECODER / WAIT | Launch active decoder instances concurrently; retain independent arithmetic state |
| CAPTURE cache write handshake | Write only the writer's private row; register its local acknowledgement |
| Last private K/V capture | Wait for every lane's complete latent and RoPE vectors |
| FP8 group conversion | Quantize real latent sources and store dequantized BF16/Q16.16 consumers; leave RoPE raw |
| BARRIER | Wait until every active lane presents its initial row-0/component-0 read |
| GATHER read handshake | Accept matching cache requests together only from causally eligible lanes |
| Prefix request/response | Fetch one real committed value; capture returned data before broadcast |
| Candidate read | Synchronous private-RAM access; no external speculative publication |
| BROADCAST stall | Hold each lane's response until that lane accepts; do not refetch or retire twice |
| First-pass tail | Hold early lanes' second-pass starts; finish all first-pass windows first |
| Second pass | Restart the block at row zero with separate per-lane maxima, normalization and accumulators |
| Layer completion | Advance only after both cache passes and every active decoder complete |
| Final norm / projection | Preserve parent numerical boundaries; choose greatest logit, smallest ID on ties |
| RESULT / HOLD | Hold actual predictions and hidden storage; no next command before release |
| Commit handshake | Copy only the requested leading materialized rows, in layer/lane/component order |
| Final commit acknowledgement | Publish internal commit_done; no public command completion is implied |
| Hidden read handshake | Registered local-RAM response, held until accepted; invalid lane/index returns error |
| Release handshake | Require successful commit, no pending hidden response and idle local/cache ownership |
| Reset/flush | Annul private ownership, responses and unpublished results; do not clear bulk RAM |

During the attention window, the participating mask for row r is exactly
the active lanes satisfying `r<=first_pos+lane`. A future-lane read or
write mismatch fails explicitly rather than changing the causal mask.
Committed-prefix reads use a single shared request and independently
held lane responses. This is not four serial invocations of a target top.
The first-pass/second-pass rendezvous preserves the unchanged parent
MLA's two-pass softmax arithmetic.

Private raw sources and FP8 effective consumers are separate memories.
Commit copies original raw Q16.16 sources so the connected group service
reproduces original quantization, including the group maximum and tail,
instead of choosing a new scale from already rounded consumer values.
Only commit may publish candidate K/V externally. A terminally truncated
verdict must supply its visible materialized-prefix count; the cache must
not be committed using a longer, unpublished draft prefix.

`anvil_d2_lane_memory` implements each lane's live scratch layout:

| Logical local tensor | Row / extent |
|---|---|
| Kind 8, projection 0 | Rows 0,1,7,8,14, each H words |
| Kind 15, projection 7 | Rows 3,4, each H words |
| Kind 15, projection 7 | Rows 5,7, each NUM_Q_HEADS*KV_LORA_RANK words |
| Kind 15, projection 7 | Row 6, NUM_Q_HEADS*QK_ROPE_HEAD_DIM words |
| Kind 15, projection 7 | Row 8, max(INTERMEDIATE_SIZE,MOE_INTERMEDIATE_SIZE+HIDDEN_SIZE,ROUTED_EXPERTS) words |

No truncated-address aliasing is permitted for an invalid local access.
The adapter acknowledges it with an explicit error and zero data.
Layer-local scratch is reusable only because the lane controller imposes
the full decoder layer barrier; hidden row 0 persists across that barrier.
Weights, wide absorbed coefficients and committed cache retain parent
logical identities outside this local scratch map.

These target components are integrated with the native
draft subsystem and public controller in `anvil_d2_top`. Their static
elaboration is not numerical, behavioral, synthesis or timing acceptance.

Use bounded queues, tagged bank arbitration and explicit owner/epoch
tracking. Associate responses by tag, never arrival order. Unknown,
duplicate and wrong-epoch responses cannot update live transactions.
Errors explicitly terminate the operation and invalidate speculation.
Cancellation stops issue and drains accepted transactions. Never replace
a memory failure with software reference tensors.

### D2 tagged scheduler implementation boundary

`anvil_d2_bank_scheduler` accepts 1..32 untagged internal clients, with
one live request per client and `QUEUE_DEPTH` independently reserved slots
per external bank. Supported banks/depths are the native values above.
An internal client may not reuse its reservation before its response
handshake. Different clients and banks may progress independently.
Bank steering is the low bank bits of `col ^ row ^ layer ^ kind ^ proj`;
the full logical tensor address is transmitted unchanged. This is a D2
transport choice, not a reconstruction of the absent original scheduler.

Each bank arbitrates clients round-robin with explicit wrap and registers
the selected external request before exposing it. Its slot stores the
complete request, owner and a unique 64-bit tag. Tags advance by BANKS
and are never recycled on flush. Exhaustion is an explicit fault, not
tag wrap. After reset the external memory system must discard responses
from before reset, since reset reinitializes the public tag namespace.
Within a reset lifetime, stale epochs/duplicates cannot alias a live tag.

| Scheduler edge / boundary | Effect |
|---|---|
| Client request handshake | Reserve free slot, capture address/data/tag and advance client fairness cursor |
| Queued slot selected | Register bank issue owner; first external valid is after this edge |
| External request stalled | Keep slot, tag and complete payload fixed |
| External request handshake | Mark slot issued; no client completion yet |
| Matching external response handshake | Register data/error in its reserved slot; publish to client only after the edge |
| Same-edge request and response for its tag | Capture response in the reservation; no combinational client bypass |
| Client response stalled | Retain returned slot and complete payload/status |
| Client response handshake | Release slot and client ownership |
| Unknown/duplicate tag in normal operation | Consume without changing a live slot; latch fault and stop new issue |
| Fault while a bank request is already held | Retain that request until acceptance or explicit flush; select no new queued request |
| Flush with queued/returned slots | Annul them and stop external issue immediately |
| Flush with accepted external work | Retain only issued tags; drain matching responses without client publication |
| Flush plus matching response | Free matching issued slot; flush never strands an acknowledged request |
| Draining with unknown/stale response | Consume without changing live ownership or publishing data |
| Last drain response | Release its slot; drain_done becomes visible after the edge |
| Depth/client/bank count one | One real reservation, explicit wrap to zero, no zero-width identifiers |

`drain_done` means no reserved slots or held bank requests, including when
flush is held. `idle` additionally requires no flush/drain/fault and the
post-reset arming edge. A returned memory error is both a held client
error response and a scheduler fault; the integration owner must initiate
abort/drain. Reset clears ownership and public outputs, not external memory.

A full group transfers 128 payload + 4 scale bytes versus D1's 512
signed-32 bytes. Against BF16 payload alone it is half, but including scale
it is 132/256, not half. Required >=2x reductions against actual D1 apply
SEPARATELY to matched, nontrivial latent and routed-expert workloads,
including scales, padding, retries and refetches. Do not claim this for
singleton tails. Logical transfer bytes are not measured DDR4 bus traffic.

### Scalar native FP8 adaptation boundary

`anvil_d2_fp8_adapter` accepts 1..32 native scalar clients, preserving one
outstanding request per client and independent passthrough responses.
With FP8 disabled it preserves logical external tensor requests. With
FP8 enabled it converts actual latent components (kind 15, projection 3,
col<KV_LORA_RANK) and routed-expert matrix reads (kind 15, projection 5).
Routed expert identity is row bits 31:25, matrix identity bits 24:23 and
matrix output row bits 22:0. Matrix 0/1 have H input columns; matrix 2 has
MOE_INTERMEDIATE_SIZE. Bias matrix identity 3 and shared/dense experts
remain signed32; RoPE cache columns remain unchanged.

The group-command base is the component with its low seven bits cleared.
Count is min(128,actual matrix/latent row length minus base). No group
extends into another row, projection or expert. The connected `fp8`
service returns actual dequantized Q16.16 consumers. A bounded 16-group
decoded RAM working set holds complete owner keys, not just scales.
Residency becomes valid only after all ordered elements and successful
service completion. All resident validity clears on flush/fault.

| Adapter boundary | Effect |
|---|---|
| Transformed scalar read accepted | Capture owner, full logical group key and requested element |
| Decoded group hit | Synchronous RAM read, then held scalar response |
| Group miss | Invalidate victim, request/fetch/dequantize full actual group and validate every output index/last |
| Group completion | Publish complete resident ownership, then return the requested Q16.16 element |
| First latent group write | Require group-aligned column; capture source and group identity |
| Intermediate latent scalar write | Capture exact next component and return registered RAM-ownership acknowledgement |
| Intervening weight read from same writer | Pass through while waiting for the group's next component; do not deadlock tensor computation |
| Final latent scalar captured | Start real group quantization/packed writes and scale write |
| Final scalar acknowledgement | Wait until the group service completes all required external acknowledgements |
| New latent write | Invalidate matching decoded group before accepting replacement sources |
| Transformed memory/numeric/protocol fault | Return explicit failed scalar response, invalidate all decoded owners and latch fault |
| Flush/reset or idle precision-mode change | Top must invalidate adapter and group-service ownership together |
| Passthrough response stall | Preserve its independent owner/data/error until actual acceptance |

Intermediate write acknowledgements are owned capture, not a claim that
the group's DDR writes have completed. The final group acknowledgement
and top-level drain are mandatory before successful command completion.
Passthrough transactions retain scheduler tag ownership outside this
adapter. No bandwidth savings result follows merely from this mapping;
the independent suites must measure accepted external transfers,
including scales, padding, refetches and unchanged tensors.

The adapter exposes an internal group interface for connection to the
literal top-level `fp8` instance. This is a connected implementation,
not a claim of independently verified inference.

### FP8 group service implementation boundary

`anvil_d2_fp8_mla_moe` is a serialized group service shared by latent-cache
and routed-expert consumers. This internal interface does not alter the
fixed public top. A command specifies epoch, layer, row, aligned logical
base column, actual count 1..128, read/write, expert/cache and prefetch.
Projection is 3 for cache, 5 for expert. A read returns signed Q16.16,
binary32 and BF16 per element; consumers must use the Q16.16 result for
the specified hybrid MAC boundary. Read-prefetch loads the same resident
buffer but produces no element stream. Expert writes and write-prefetch
are explicitly invalid. The integration adapter, not this group service,
determines actual tensor-row lengths and excludes non-latent RoPE and
non-routed/bias expert tensors.

There are two independent resident ownership records, one per consumer
class, each containing epoch, layer, row, base column and actual count.
A miss invalidates the selected record before memory issue, fetches the
scale plus all packed words, validates/dequantizes every actual element
and only then marks the group resident. A different epoch invalidates both
records. A matching read may replay the decoded group without refetch.
The numerical RAM is 256 x 80 bits (FP32, BF16, Q16.16), not model-sized
storage. A shared 32-word packed staging RAM supports miss decoding and
cache quantization. No bulk RAM clearing or asynchronous read is needed.

Cache writes capture exactly the actual group through the quantizer,
pack low-component-first bytes, and write all payload words followed by
the scale, waiting for every acknowledgement. The command completes
only after the scale acknowledgement. The selected resident record stays
invalid; a later read observes the stored quantized values, not the
unquantized input. Atomicity here means ownership/publication: no other
group command is admitted during the write. A cancelled partial write
must never be used as live context; top-level epoch/sequence validity and
scheduler drain enforce that boundary. Physical external words are not
transactionally rolled back.

| Group service state / edge | Effect |
|---|---|
| IDLE command handshake | Capture full identity/count; reject invalid command through failed completion |
| Read hit | Synchronous numerical-RAM read, then held element publication |
| Read miss scale/payload request | Held request, wait for registered scheduler response before consuming |
| DECODE_READ / DECODE_ISSUE | Synchronous packed-RAM read, select actual byte, enter four-stage dequant |
| DECODE_WAIT / CONVERT / STORE | Capture FP32/BF16; registered ties-away Q16 conversion; store all three forms |
| Last successful STORE | Make full ownership record valid; prefetch completes or normal read replays |
| QUANTIZE_CAPTURE | Accept exactly count signed-Q16 elements; exclude unwritten tails |
| QUANTIZE_PACK | Pack actual quantizer outputs; final word's unfilled bytes are zero |
| WRITE_PAYLOAD / WRITE_SCALE | Wait for every accepted request's acknowledgement; scale is last |
| OUT_PUBLISH stall | Hold index/last and all numerical forms, without advancing |
| Final element retirement | Enter separate COMPLETE, never a same-edge done |
| Any memory/numerical error | Invalidate both records, flush arithmetic, failed COMPLETE then FAULTED |
| Flush at any stage | Annul publication and both owners; integration flushes/drains scheduler concurrently |
| First release edge | Arm only; no command/source/output/memory handshake |
| Count 1 or 127 | One or 32 packed words respectively; only actual elements decode |
| Simultaneous RAM read/write | States exclude same-array concurrent operations; no collision-mode dependency |

`fault` remains set after failed completion until flush/reset. `done/error`
are one-cycle command completion signals. Memory responses belong to the
single outstanding internal service request; external tag validation is
the scheduler's responsibility. Actual byte counters must be driven from
external bank handshakes, not these earlier queue-admission handshakes.
The service is connected through the native decoder adapter to the real
cache/expert arithmetic. Numerical/behavioral evidence remains independent.

## Implementation and independent acceptance obligations

All synthesizable RTL has zero combinational division/modulo operators
and no mixed blocking/nonblocking sequential assignments. Use explicit
wraps, shifts and multicycle division/reciprocal/square root. Bound
register-to-register logic depth. No timing waiver is presumed; only
Coordinator review backed by actual Quartus post-synthesis STA may
consider one without lowering the 100 MHz objective.

All seven admitted commands remain mandatory and self-contained:

```
python3 tests/verify.py --suite numerical
python3 tests/verify.py --suite behavior
python3 tests/verify.py --suite compatibility
python3 tests/verify.py --suite defects
python3 tests/verify.py --suite synthesis
python3 tests/verify.py --suite benchmark
python3 tests/verify.py --suite reproduce
```

These are required future Verifier entry points, not claims that the test
files or results already exist. Keep failing prerequisite observations and
run otherwise executable comparisons. Never skip a mandatory command or
replace its thresholds with newer supplemental checks.

Acceptance retains all of the admitted numerical, behavioral, parameter,
mutation and synthesis matrix: all 256 FP8 codes at 16 scales; at least
10000 independent rational/integer numerical cases; rounding/error
boundaries and group lengths 1,2,3,4,127,128,129,255,256; nonzero
nonsymmetric absorbed versus unabsorbed equations; five domains times
seeds 17,89,233; hidden sizes 8,64 and bounded 2048; real accepted
prefixes 0..4; all EOS positions; limits 1..5; sequence tails; ties;
concurrent causal verification/future-lane leakage; reset/cancel/stalls;
reordered/error/stale/duplicate memory; final materialization; public
singleton/non-power-of-two queue traffic; every admitted parameter
boundary and one-below/above illegal diagnostics. Mutants must compile
and fail the normal behavioral scoreboard, not fail by text matching,
timeout or compilation. Integrated Yosys must show zero latches, no
undriven/black-box production cells, substantive connected native MTP/FP8
state and preserved hierarchy artifacts.

The mandatory four-mode public-pin scenario prefills positions 0 and 1
with inherited logits, accepts a distinct seed at position 2, generates
exactly three reference tokens at 3,4,5, stalls and holds the first
committed beat, forbids early retirement/done/next command, then accepts
a NEW held seed at 6 only after COMPLETE. Separately reject replay at 5.
Cover generation policy reset to zero, generation at new_sequence
position 0, zero capacity, terminal shortening, EOS and prefill after
decode. No internal forcing or fabricated verdicts may substitute.

Independent compact Icarus runs remain <=500000 simulated cycles and
target <60 seconds; larger/multi-seed/benchmark/mutation work uses
compiled Verilator. Respect 600-second vvp and 2700-second check patrols
without weakening functional coverage. No per-cycle/beat stdout or
per-request flushing. Each suite rebuilds current sources in fresh
canonically named evidence directories and regenerates missing/stale
prerequisites. Retain source hashes, exact commands, tool versions,
times, timeouts/exits, raw logs and failed receipts/mutant diffs.

Five domains are mathematical reasoning, code reasoning, scientific
reasoning, logical deduction and general multi-step question answering.
Absent authoritative images, label deterministic generated fixtures
synthetic architectural workloads, not pretrained DeepSeek quality.
Compare identical completed output workloads and memory conditions under
D1, D2 compatible, FP8-only, MTP-only and combined. Report actual cycles,
bytes, accepted/proposed ratios, signed speedups, and tokens/s at 100 MHz,
separating prompt, warmup/absorption, draft, verify, rollback, stalls,
decode and final materialization. Disclose FP8 differences versus D1.
Never invent parent timing/PPA or assume a speculative speedup.

Clean-directory reproduction copies declared product/reference/test
sources only, excluding `.vulcan/`, `.git/`, `.tooling/` and `VULCAN/`,
and runs fresh compact numerical/integration/synthesis work. Runtime
gates remain timing lint, Quartus 17.1 Arria 10 STA at <=10.0 ns with
WNS>=0, and PCIe Gen3x8 hardware bridge with at least three consecutive
deterministic passes. Report real post-fit resources/Fmax/slack and
power only with method/conditions. Generic synthesis is not physical
timing/PPA. Final PDF production occurs only after independent engineering
acceptance and is never an engineering-test prerequisite.
