# Anvil-Q3-HT2 v2.5.0-ht2-spec-sparse

## Authority, status and provenance

This is the design specification for the admitted HT2 work order, not an
acceptance report. The complete product is an integrated accelerator with
`anvil_q3_ht2_top`, four-token projection batching, dynamic down-projection
sparsity, causal tree attention and atomic all-layer KV publication. A collection
of leaf modules does not satisfy that objective.

Implementation is currently incomplete. Only the sparse-DMA leaf is present.
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
require implementation and independent coverage; they are not implemented
by this leaf.
Legacy mode invokes the literal parent without an arithmetic correction wrapper.

Weight decode has three registers; FP32 product and every FP32 adder have six
stages including operand capture. Beat E0 gives product post E8 and stripe
commit post E14. Final accepted beat L gives the last commit post L+14,
level-one captures L+15..18/results L+20..23, level-two captures
L+24..25/results L+29..30, final capture L+31 and result post L+36.
Any common freeze must preserve all tags, data and valid stages together.

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
