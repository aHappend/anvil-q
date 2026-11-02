# Anvil-Q3-HT2 v2.5.0-ht2-spec-sparse

## Authority, status and provenance

This is the design specification for the admitted HT2 work order, not an
acceptance report. The complete product is an integrated accelerator with
`anvil_q3_ht2_top`, four-token projection batching, dynamic down-projection
sparsity, causal tree attention and atomic all-layer KV publication. A collection
of leaf modules does not satisfy that objective.

Implementation is currently incomplete. Sparse DMA, registered FP32 helpers,
Q16 projection-boundary converters and the four-bank tile MAC are authored.
Private scratch, a causal parent-Q16 attention wrapper with quantized KV reader,
the greedy verifier and atomic shadow/copy engine are also authored as leaves.
The batched decoder/projection scheduler, integrated top and FPGA files are absent.
Independent functional verification, synthesis, timing, fit and board execution
are pending. No performance or numerical result is claimed.

`anvil_q3_ht_reference/rtl/` is the immutable, explicit source dependency.
There is no supplied repository-intake source index. The authentic
`design/GENERATIONAL_HANDOFF.md` is absent; historical parent Quartus timing/PPA
cannot be compared until it is restored through authorized intake. Do not
substitute generic synthesis estimates or reconstructed historical documents.

Designer owns `rtl/`, `design/` and `fpga/`; independent Verifier owns `tests/`.
The shared runtime owns execution records, hardware gates and the final,
independently reviewed product PDF. The PDF is not a prerequisite of engineering
verification. Runtime metadata is not a product source dependency.

## Frozen geometry

| Parameter | Production value |
| --- | --- |
| Layers / hidden / intermediate | 36 / 2048 / 11008 |
| Query heads / KV heads / head dimension | 16 / 2 / 128 |
| AWQ group / bits | 128 / 4 |
| Vocabulary / maximum sequence | 151936 / 32768 |
| Candidate capacity / weight lanes | 4 / 128 |
| Cache mode / asymmetric INT4 | 1 (INT8) / 0 |

Cache mode 2 is symmetric INT4. Mode 0 is only available for legal legacy
configurations. Four banks of 128 arithmetic lanes mean 512 physical products
per retained burst, not 2048 multipliers. Leaf weight-lane configurations are
8, 16, 32, 64 and 128; the production DDR interface remains 512 bits.

Legal geometries have positive layer, vocabulary and KV-head counts, positive
even head dimension, query heads equal to eight times KV heads, hidden size
equal to query heads times head dimension, and hidden/intermediate dimensions
divisible by eight and group size. Group size is 8, 16, 32, 64 or 128;
maximum sequence length is 1 through 32768. Preserve legal legacy bank, tile,
queue, burst and residency settings. All image, scratch, committed-KV and
four-token shadow extents must be checked using widened arithmetic against
their disjoint 33-bit address regions. The full-size parent's uncompressed
cache reservation is a known parameter-bound concern, not passing provenance.

New parameterized modules use a diagnostic-only invalid generate branch ending
in `PARAMETER ERROR` before traffic. They must not substitute a legal datapath
for an illegal configuration.

## Cycle and degenerate-boundary table

All transfers use pre-edge `valid && ready`. Outputs after an edge describe
registered state; they cannot transfer retroactively on that edge.

| Boundary | Required behavior |
| --- | --- |
| Active-low asynchronous reset | Public valid, ready, requests, data, addresses, metadata, completion and errors are zero. Internal RAM need not reset. |
| First rising edge after reset release | Idle registered state is eligible for normal traffic; no prior output is treated as transferred. |
| Synchronous flush | Suppress public traffic; discard private work; retain accepted-read ownership until returns drain. |
| Flush with prospective publication | Flush wins; committed prefix remains unchanged. |
| Fault with ordinary transfer | Fault recovery wins over datapath progress; already accepted transport operations remain accounted and owned. |
| Blocked producer | Valid and every associated field stay stable until transfer or explicit cancellation/fault. |
| Empty MAC tile | No input beat; positive-zero result post command edge + 1. |
| One-column DMA | Final activation follows the same three-stage capture/predicate/update pipeline as longer commands. |
| DMA capacity one | One RAM entry, no zero-width address; last and first activation coincide. |
| Non-power-of-two DMA capacity | Explicit ordinal bounds; no power-of-two wrap assumption. |
| Same-edge DDR request and response | Explicit accepted-request ownership recognizes the response exactly once. |
| Two-line column | First response never publishes an operand; final response at R publishes one operand post R + 1. |
| Cancel before second-line acceptance | Drop the unaccepted second request; drain only actual accepted reads. |
| All-sparse DMA | Zero physical reads; descriptor transfer precedes completion. |
| Queue/residency one or three | Explicit wrap counters in their owning future modules; no modulo operator. |
| KV count one / capacity | Both legal; padding and complete expected-record accounting still apply. |

### Atomic commit leaf implementation boundary

The internal `anvil_q3_ht2_kv_commit_engine` takes a transaction command
`cmd_id/epoch/base_pos/mask`, the frozen staged-record interface, and a selected
path `commit_count[2:0]/commit_nodes[7:0]` (two bits per node, path order).
`staged` means every active node has completed all expected shadow writes.
`publish_valid/publish_count/publish_pos` is a one-edge notification of the
single registered visible-count update; it has no response-ready dependency.
`visible_count/visible_epoch` are internal reader visibility gates, not host
correctness inputs. `done` is a one-edge completion and `error` is held in the
faulted state until flush; `idle/fault/drain_done`
describe transaction recovery. Command acceptance reserves all four shadows.

Per-node records must arrive in increasing `(layer, value, head, group)` order,
where key precedes value within each layer. Different nodes may interleave.
This bounds duplicate/missing-record accounting to four ordinal counters and
four expected-field tuples without a large asynchronous bitmap. An accepted
stage record is checked by the unchanged parent symmetric codec in decode mode
before its shadow write. The last HEAD_DIM group supplies its actual count.
Wrong ownership, order, header, reserved code or padding is a transaction fault.

Committed records retain the parent address formula
`0x100000000 + (((layer*2+value)*MAX_SEQ_LEN+position)*NUM_KV_HEADS+head)*HEAD_BYTES
+ group*64`. Four shadow images follow the complete committed extent and use
node-major `(node, layer, value, head, group)` order. Address generation has
separate registered multiply, add and final region-check stages. Copy destinations
are never below the old visible count. Only an explicitly selected active,
unique path can copy records; a zero-count path publishes no memory writes.

The record-memory transport reserves one read response before accepting a
request. Writes complete on accepted request, not on a fictitious write response.
`memory_rsp_error` is also monitored without `memory_rsp_valid`, allowing the
enclosing bridge to forward available Avalon response faults. A two-edge quiet
fence follows the final accepted copy write before publication; the future
public-DDR integration must map its controller error indication over this fence
and must not claim persistent-memory durability. Flush drops unaccepted requests,
drains accepted reads and suppresses publication. A fault preserves the visible
prefix and recovers only after a flush; flush alone preserves the sequence.
Reset, including an enclosing explicit new-sequence reset, invalidates visibility.

| Atomic boundary | Registered behavior |
| --- | --- |
| Stage handshake | Capture ownership and full record; no shadow write before codec validation. |
| Same-edge read request/return | Capture once using pending-or-accepted ownership. |
| Flush plus request | Request output is suppressed; only previously accepted reads drain. |
| Flush plus publication | No publication; old visible count survives. |
| Last copy write | Advance only after accepted physical write; then two quiet fence edges. |
| Zero accepted nodes | Preserve count and pass through the same cancellation-sensitive fence. |
| Publication | One count update, then engine completion on the following edge. |
| Stage or transport fault | Stop new traffic, retain read ownership, preserve visible prefix. |
| Invalid geometry | Diagnostic-only branch; no substituted datapath or public traffic. |

### Greedy verifier leaf implementation boundary

`anvil_q3_ht2_spec_verifier` implements the frozen command/evaluation/logit/
staging/response/record-memory ports. Geometry parameters are NUM_LAYERS,
NUM_KV_HEADS, HEAD_DIM, MAX_SEQ_LEN, CACHE_MODE and VOCAB_SIZE. The literal
`kv_commit_engine` instance owns visible prefix state. The top must reset this
sequence-owned verifier explicitly on a new sequence, together with the enclosing
transport; speculative cancellation instead uses flush, preserving visibility.
The prefix-root argmax comes from the decoder's cached hardware result.

Graph validation uses two registered stages per slot. Lower-index active parents
permit bounded ancestor-mask and depth construction, including roots in any slot.
Evaluation begins only after graph validation and engine command acceptance.
Each node's logit stream may interleave with other nodes, but its vocabulary
indices are strictly ordered and complete. Logit operand capture precedes a
registered signed comparison; acceptance at E updates argmax post E+1.
`eval_done` may coincide with the final accepted logit or staged record.
Selection waits until this comparison pipeline drains and the last shadow write
finishes. Missing logits or missing records are faults, not indefinite successful
waiting. No stage/logit transfer is accepted after eval_done.

Selection alternates registered child search and path update: two edges per
accepted node, at most four accepted nodes. A no-match search returns the current
target argmax, including successful zero-token rejection. Commit copies only
the selected path. The public response is registered on the edge after the
engine's publication; downstream response backpressure cannot defer publication.
Faults pulse local cancellation to the engine, drain accepted reads, then publish
a held zero-data error response. Fault recovery requires flush. A flush suppresses
all response/evaluation valid signals and clears local transaction metadata.
The verifier's visibility descriptor is not a substitute for attention.

### Causal attention leaf boundary

The internal `anvil_q3_ht2_tree_attention` evaluates one selected candidate/layer
using the unchanged parent Q16 attention arithmetic kernel. Projections remain
batched; sequential attention traversal does not replicate weight traversal.
Its command includes id, epoch, layer, selected node, active mask, base prefix
count, all node positions and the selected node's four-bit visibility mask.
Only a unique visible node at each virtual position base..selected-position is
legal. The selected node must be visible and no descendant can be visible.
The parent kernel's initial per-layer commit operation is intercepted as a
private-read readiness acknowledgement: no memory write or count publication
results from it. The decoder must finish validated shadow staging for that
node/layer before launching attention.

Query/context scratch requests carry the selected node alongside the parent
scratch interface. They address parent slots 2 and 5 in that node's private
scratch image. Prefix positions read the complete committed backing extent;
positions at or above base select exactly one visible private node. Siblings
never receive a key/value request. Query head h uses the parent h>>3 GQA mapping.
`anvil_q3_ht2_kv_read_port` generates the same parent committed address and
node-major shadow address as the engine, using registered address stages.
Its synchronous bounded resident cache tags epoch, transaction and address,
uses explicit replacement wrap for residency one or non-power-of-two sizes,
and never substitutes residency for long-context capacity.

Record returns are ownership checked and decoded through the unchanged parent
symmetric codec before scalar use. Thus attention sees quantized reconstruction,
not pre-quantization staging values. Returned data is a held valid/error response.
Flush invalidates residency, cancels unaccepted requests and drains accepted
physical reads. Scratch return ownership is likewise retained while cancellation
drains an accepted request. Reset must reset the enclosing transport too.
The wrapper does not alter the parent's dot/softmax/context rounding or invoke
an external attention oracle. Independent causal contexts, GQA mapping,
quantization, protocol and timing checks remain pending.

### Private scratch boundary

`anvil_q3_ht2_private_scratch` provides four literal synchronous Q16 word banks
with the parent's 15-slot lengths and offsets. One request owns one slot/index.
A read mask selects one to four banks at that same address; a write selects
exactly one node and its one-hot mask. Scalar consumers select their node's
32-bit slice; projection ingestion can read all four slices in one access.
Requests return a held mask/node/data/error response. Command capture, slot-map
capture and bounds/address checks precede synchronous bank access; response valid
is published on that bank-access edge, with no redundant data-copy register.
Reads of uninitialized selected entries are explicit errors; inactive banks
are zero and are not validated.

Only initialized bits are cleared, synchronously and one address per edge in
all four banks, after reset/flush. Ready remains low until clearing completes.
All data and initialized RAM ports use non-asynchronous sequential blocks.
There are no multiported asynchronous array substitutions. The decoder must
overwrite every consumed slot entry for each new candidate; retained initialized
bits do not authorize reuse of another candidate's scalar values.
Production has 54016 words per node: 864256 data bytes plus 27008 validity bytes
across four nodes (analytical storage, not a fit result). Widened geometry
arithmetic validates the complete four-bank extent against the declared scratch
reservation. This real on-chip scratch is not a DDR bypass for weights, metadata
or committed/shadow KV, whose public transport remains mandatory.

Reset has highest priority, then flush/cancellation, then faults, then ordinary
progress. Inactive outputs are zero. No response may be accepted twice or
overwrite a pending transaction.

## Frozen arithmetic and execution order

AWQ nibbles are unsigned q and zero z; the signed weight delta is q-z.
Source words use row permutation `[0,4,1,5,2,6,3,7]`. Activations and nonnegative
scales are finite IEEE binary16, including subnormals and signed zero. Invalid
active operands are errors; inactive tokens/rows do not classify or contribute
their payloads. Decode delta times scale exactly into binary32, multiply by the
exact binary16 expansion with binary32 nearest-even rounding, and round every
binary32 addition nearest-even. Products are never rounded prematurely to
binary16; exact zeros normalize to positive zero.

Each output/token has eight binary32 stripes. Retained issued ordinal j updates
stripe j & 7, in order. The final tree is
`((s0+s1)+(s2+s3))+((s4+s5)+(s6+s7))`, with rounding at every node.
Sparse reassociation and removed contributions are distinct numerical effects.

Surrounding parent normalization, RoPE, attention, residual, SiLU/SwiGLU, bias
and logits retain Q16.16 semantics. Projection inputs convert Q16.16 to binary16
nearest-even; completed binary32 sums convert to signed Q16.16 nearest, ties
away from zero, with signed-32 saturation before the parent bias insertion
order. The signed-Q16.16 input range is inside finite binary16 range, so the
input conversion must not produce infinity; rounding at the negative endpoint
may produce -32768, which is finite. FP32-to-Q16 overflow saturates only at the
declared conversion boundary, never inside FP32 arithmetic. These boundaries
are implemented by the projection-boundary helpers below; their connection
to the complete decoder and independent numerical coverage remain pending.
Legacy mode invokes the literal parent without an arithmetic correction wrapper.

Weight decode has three registers; FP32 product and every FP32 adder have six
stages including operand capture. Beat E0 gives product post E8 and stripe
commit post E14. Final accepted beat L gives the last commit post L+14,
level-one captures L+15..18/results L+20..23, level-two captures
L+24..25/results L+29..30, final capture L+31 and result post L+36.
Any common freeze must preserve all tags, data and valid stages together.

## Arithmetic helper and tile interfaces

The tile MAC implements the frozen public ports and bus widths in the admitted
plan. All outputs are valid-gated, with 32-bit sum entry `(token*128+row)`
at the least-significant corresponding slice. Leaf `WEIGHT_LANES` reduces
physical lane count without changing the fixed public buses; unused rows are
zero. Additional geometry parameters `NUM_LAYERS`, `HIDDEN_SIZE`,
`INTERMEDIATE_SIZE`, `NUM_KV_HEADS` and `HEAD_DIM` validate column, layer and
row identities. Their production defaults are the frozen geometry. Invalid
parameters select only the terminating diagnostic branch.

Commands accept a nonempty token/row mask; selected local rows must exist in
the projection and leaf capacity. Projection 6 takes intermediate columns;
others take hidden columns. Projections 1/2 produce KV-head rows, 4/5 produce
intermediate rows, and the remainder produce hidden rows. Column beats must
be strictly increasing, legal original column indices, have a nonempty keep
mask contained in the command token mask, and set `in_last` exactly on the
declared retained-beat count. Active token activations are classified even
when that token's keep bit is zero; its arithmetic contribution is then zero.
Inactive command tokens/rows do not classify payloads.

| Helper | Ports in addition to clk/rst_n/flush/enable | Registered stages |
| --- | --- | --- |
| `anvil_q3_ht2_weight_decode` | in_valid, in_q[3:0], in_zero[3:0], in_scale_f16[15:0]; out_valid, out_error, out_weight_f32[31:0] | Capture; exact 11-by-4 unsigned product and sign/power; exact FP32 normalization |
| `anvil_q3_ht2_fp32_mul` | in_valid, in_a/in_b[31:0]; out_valid, out_error, out_result[31:0] | Capture; finite operand expansion; significand multiply; leading-zero/exponent descriptor; normalize/jam; nearest-even round/pack |
| `anvil_q3_ht2_fp32_add` | Same binary32 interface, plus retire_valid/retire_error/retire_result[31:0] | Capture; magnitude order/field decode; alignment/jam; add/subtract; normalize; nearest-even round/pack |
| `anvil_q3_ht2_q16_to_f16` | in_valid, signed in_q16[31:0]; out_valid, out_error, out_f16[15:0] | Capture; unsigned absolute magnitude; leading-zero/normalization descriptor; nearest-even round/pack |
| `anvil_q3_ht2_f32_to_q16` | in_valid, in_f32[31:0]; out_valid, out_error, signed out_q16[31:0] | Capture; scale/guard descriptor; signed magnitude; ties-away rounding/saturation |

An input accepted at E gives decode post E+2, six-stage FP32 output post E+5,
or four-stage conversion output post E+3. Helpers use a common clock enable:
disable freezes all data/error/valid registers, and reset/flush clears them
regardless of enable. Helper output valid describes registered state, not an
additional independent ready/valid transfer. A scheduler must reserve their
fixed-rate output storage before enabling them. They are internal interfaces,
not host-provided numerical oracles.

The adder's `retire_*` signals describe its pending sixth-stage rounding
result **before** the retirement edge and are gated by enable. Lane stripe
or tree storage captures this result at that edge, providing the sixth
register directly rather than adding a seventh register after `out_result`.
For the final reduction, the top's held sum register provides that register.
No public result is asserted by this combinational retirement interface.

The tile broadcasts 128 registered weights to four literal token banks, each
with 128 `anvil_q3_ht2_mac_lane` instances at production width. Each lane has
one six-stage multiplier, one shared six-stage stripe/tree adder, eight
32-bit stripe registers, four level-one results and two level-two results.
Three registered shared activation stages align with weight decode. Issued
ordinal tags align through nine decode/product stages and five pre-retirement
adder stages. Arithmetic pipelines do not stall on input bubbles; valid tags
preserve each operation. They freeze together while the held tile result
is blocked. No next command overlaps result ownership.

Faults discard arithmetic, set persistent `fault`, and return an explicit
zero-sum error response one edge after the offending accepted command/beat.
The error response holds normally under backpressure; flush is required to
leave persistent fault recovery. Empty legal commands return a positive-zero
result one edge after command acceptance. Zero columns are legal only at
the MAC descriptor boundary, not as an empty source projection in DMA.

FP32 helpers reject NaN/Inf, report arithmetic overflow instead of saturating,
handle finite normal/subnormal operands, and normalize exact zero to positive
zero. Simulation-only active X/Z classification becomes an explicit error.
Only FP32-to-Q16 conversion has signed saturation. These are implementation
intent and interfaces, not independently checked numerical results.

## Sparse-DMA leaf interface

`anvil_q3_ht2_sparse_dma` has the admitted fixed ports. Candidate i occupies
bits i*16 through i*16+15 of activation buses. Local row masks always have
128 bits and packed weights always have 512 bits.

| Group | Fields |
| --- | --- |
| Clock/control | `clk`, `rst_n`, `flush` |
| Command handshake | `cmd_valid`, `cmd_ready` |
| Command identity | `cmd_epoch[31:0]`, `cmd_layer[31:0]`, `cmd_proj[2:0]` |
| Matrix/block | `cmd_qweight_base[32:0]`, `cmd_output_count[31:0]`, `cmd_row_base[31:0]`, `cmd_columns[31:0]` |
| Candidate/sparsity | `cmd_token_mask[3:0]`, `cmd_sparse_enable`, `cmd_threshold_f16[15:0]` |
| Activation input | `act_valid`, `act_ready`, `act_column[31:0]`, `act_f16[63:0]` |
| Descriptor | `tile_valid`, `tile_ready`, `tile_columns[31:0]`, `tile_row_mask[127:0]` |
| Read request | `memory_req_valid`, `memory_req_ready`, `memory_req_address[32:0]`, `memory_req_burstcount[7:0]` |
| Read return | `memory_rsp_valid`, `memory_rsp_error`, `memory_rsp_rdata[511:0]` |
| Operand | `weight_valid`, `weight_ready`, `weight_column[31:0]`, `weight_data[511:0]`, `weight_activation_f16[63:0]`, `weight_keep_mask[3:0]`, `weight_last` |
| Status | `done`, `error`, `idle`, `drain_done`, `fault` |
| Counters | `scanned_columns[31:0]`, `skipped_columns[31:0]`, `issued_weight_beats[31:0]` |

Implementation capacity parameter `MAX_COLUMNS` defaults to 11008, is positive,
and describes activation RAM capacity, not a padded model dimension. Commands
have 1..MAX_COLUMNS columns, output count positive and divisible by eight,
row base below output count, projection 0..6 and a nonempty token mask. A
zero-column matrix command is invalid (an all-sparse nonempty matrix is legal).
Epoch/layer are opaque command ownership metadata at this leaf; the integrated
scheduler must validate them against the model and transaction.

Threshold 0x1400 is 2^-10. Threshold is latched and must be finite and
nonnegative; negative zero is legal. With sparsity enabled for projection 6,
candidate i keeps c exactly when active_i and abs(a_i,c) > threshold.
Otherwise every active candidate keeps each column. Invalid active activations
are errors even on columns another candidate would skip. Inactive candidate
payloads are stored as zero.

Activation capture, predicate and retained-count/storage update are three
registered stages. Final descriptor appears post last activation edge + 2.
All activation columns are buffered before reads. Descriptor transfer precedes
the first request. Sparse decisions precede address generation.

### Packed image versus physical lines

The matrix base is 64-byte aligned in qweight region `[0,0x60000000)`.
Original column stride S is output_count >> 1 bytes, with no column padding.
N is min(128, output_count-row_base), W0 is row_base >> 3 and W1 is
(row_base+N-1) >> 3. Span P is base + column*S + (W0 << 2), length B is
((W1-W0)+1) << 2. Read A0 = P & ~63 and, only if P[5:0]+B > 64,
A1 = A0+64. Every accepted request has burstcount one.

The full matrix allocation is round_up_64(columns*S). Validate the allocation,
complete requested lines and all widened intermediate addresses before traffic.
Allocation padding may be read; another matrix or region may not. For example,
output_count 8, row_base 0, column 1 reads base and selects byte four.
Output_count 64, column 1 selects byte 32. Arbitrary row bases select containing
packed words and repack global row g into local row r with the AWQ permutation.
Invalid local rows are zero. The MAC must unpack this local convention once.

One selected logical column owns at most one outstanding physical read at a
time. A crossing span requests its lines in ascending order. No prefetch,
coalescing or cross-column line reuse is implemented. Each retained logical
column produces exactly one operand, even if two lines were fetched. Incidental
neighboring/skipped bytes never become operands. Repeated physical addresses
are actual rereads and count separately.

After synchronous RAM read and retained-column selection, three registered address stages
calculate stride product, packed start and aligned descriptor. Seventeen
individually captured 32-bit source-word banks bound extraction. On each return,
each bank selects at most one of sixteen physical words. On the following edge,
each local nibble selects one of two adjacent source words and one of eight
nibbles, then repacks into local AWQ order. No 1024-bit variable barrel shift
is used. A final return at R publishes the operand post R+1.

Counters reset on command acceptance, hold until the next command, and count
accepted logical activations/physical reads, not offered traffic. Flush/reset
clear public counters. Physical bytes are 64 times issued_weight_beats; useful
packed bytes and metadata traffic must be reported separately by integration.
Completion pulses post final operand/empty-descriptor transfer + 1, after
drain. Error completion is explicit and fault persists until flush. Cancellation
drain_done is a pulse after accepted reads drain; cancelled data never completes
as a successful operand. Reset requires the enclosing transport reset to
invalidate old returns; flush alone retains read ownership.

## Remaining integrated contracts

The public HT2 top must retain every parent port verbatim and add the admitted
mode, sparse-control and draft-tree request/response ports. Latch mode at a new
sequence, arbitrate one physical DDR interface, prioritize ordinary tokens
when idle, exclude host changes during inference, and compute the prefix
argmax in hardware. All seven projections, embedding, output head, complete
36-layer decoder, private node scratch and long-context backing remain required.
Output-head weights must also be reused across candidates.

Tree parent code 4 means prefix root; other parents must be active lower-index
nodes. Attention includes prefix, self and ancestors only. Query head h maps
to KV head h >> 3. Greedy path lengths 0..4 use complete ordered signed-Q16
logit streams and smallest-ID argmax ties. No bonus token commits.

The verifier must literally instantiate the commit engine. All active nodes'
INT8/INT4 K/V records are privately staged with exact ownership and expected
counts. Records use the parent's symmetric power-of-two exponent format,
canonical zero/tail padding and reserved-code rejection. Copy accepted path
records only into invisible positions after the old prefix. Publish the new
visible count once, only after all layers/heads/groups finish and all transport
work drains. Avalon writes are accepted at write && !waitrequest; no fictitious
write-response-valid signal may be introduced. Response backpressure cannot
delay or cause publication.

## Required acceptance and reproduction

Independent Verifier must implement both project-relative commands:

```
python3 tests/verify.py --suite all
python3 tests/verify.py --suite clean-repro
```

They are not present or runnable yet. Required tools are installed Python,
Icarus/vvp, compiled Verilator and Yosys; do not install tools through this role.
L1 includes seeds 17/29/43, independent integer/rational FP oracles, complete
compact model and public-DDR checks, cancellation/atomicity record comparisons,
six runnable defect-sensitivity mutations, production and compact synthesis,
zero latches/div/mod cells and portable clean reproduction.

Icarus is restricted to compact startup/leaf/one-token smoke below 500000
cycles; medium/production, multi-token, sweeps and mutations use compiled
Verilator. No per-cycle traces or fabricated pass receipts qualify.
Fixtures must be identified as independently generated, not actual checkpoint
or natural-language accuracy evidence.

Claim-to-check obligations include exact 4x qweight reuse, measured useful
candidate-weight bandwidth >=3.4x, 40%/50% down-projection read savings, and
at least 40% total-FFN traffic reduction on an identified accepted-batch
workload including metadata, padding, rereads and rejected work. Down-only
sparse savings must not be mislabeled whole-FFN savings.

The shared runtime separately executes L1.5 timing lint, L2 Quartus 17.1
successful device fit and WNS>=0 at 10.0 ns, and L3 Arria 10 GX PCIe Gen3x8
HIL with three consecutive deterministic passes. No combinational division or
modulo or mixed sequential assignment ownership is permitted. No present
evidence establishes these gates or authorizes a timing waiver.
