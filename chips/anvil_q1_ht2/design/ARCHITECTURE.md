# Native HT2 architecture

## Implementation ledger

This is a partial Designer increment, not a complete accelerator or acceptance
report. The source files describe connected native execution and internal subsystems; absent top-level integration is
not a software fallback or a waived requirement.

The intended path is DDR response ownership -> broadcast weight registers ->
four-slot native projection array -> FP32 residual/operator storage ->
causal provisional-KV decoder -> tree verifier -> atomic commit.
Every learned projection must traverse one shared set of weights for all active
slots. Four serial decoder calls do not implement this architecture.

### Saved source increment

| Source stem under `rtl/` | Implemented structure |
|---|---|
| anvil_q1_ht2_00_fp_pkg | Integer-significand RNE packing, gradual-underflow conversions, classification, AWQ permutation |
| anvil_q1_ht2_reset_sync | Asynchronous assertion and two-edge synchronized domain release |
| anvil_q1_ht2_parameters | Diagnostic-only legal-geometry checker |
| anvil_q1_ht2_fp16_mul | Three registered stages for BF16/FP16 to FP32 product |
| anvil_q1_ht2_fp32_mul | Three registered stages for separately rounded FP32 multiplication |
| anvil_q1_ht2_fp32_add | Capture, align/jam, add/subtract, normalize/round stages |
| anvil_q1_ht2_mac_lane | Four contexts, shared add reduction and equal-edge result forwarding |
| anvil_q1_ht2_tile_batch_mac | Four slots times64 lanes, fixed transaction masks, protocol-error drain |
| anvil_q1_ht2_dequant | AWQ nibble mapping, signed difference, FP16 scale product and BF16 boundary |
| anvil_q1_ht2_fp32_divsqrt | 27 bounded quotient/root iterations, remainder sticky, separate final round |
| anvil_q1_ht2_fp32_exp | Frozen range reduction and degree12 Horner sequencer using separate FP32 units |
| anvil_q1_ht2_sparse_dma | Registered predicate, exact byte-end validation, one-request DMA ownership |
| anvil_q1_ht2_spec_verifier | Registered bounded tree walk, lowest-child selection and correction mask |
| anvil_q1_ht2_fp32_sincos | 320-fractional-bit pi interval, word-serial reduction, separate FP32 sin/cos Horner operations |
| anvil_q1_ht2_scalar | Internal six-op scalar request/response dispatcher with nonfinite execution errors |
| anvil_q1_ht2_burst_reader | One/two-beat collection, equal-edge request/response capture, held response |
| anvil_q1_ht2_projection | Connected four-slot array, sparse predicate, AWQ conversion, exact preflight and column replay |
| anvil_q1_ht2_rmsnorm | Four-slot frozen ascending left folds, mean/epsilon/sqrt/reciprocal and weighted output |
| anvil_q1_ht2_swiglu | Four-slot stable sigmoid, separately rounded products and retained original nonzero bits |
| anvil_q1_ht2_rope_frequency | Position-independent selected-head-dimension FP32 inverse-frequency constants |
| anvil_q1_ht2_rope | Four-slot split-half rotation and selected-format attention boundary |
| anvil_q1_ht2_tree_mask | Registered topology/depth/ancestor validation, no sibling visibility |
| anvil_q1_ht2_provisional_kv | Complete-layer ownership over synchronous K/V RAM, retain/discard and flush |
| anvil_q1_ht2_attention | Four-slot causal GQA score/max/softmax/value sequencing with synchronous per-head intermediate RAM |
| anvil_q1_ht2_kv_reader | Native committed K/V row preflight, acknowledged reads and paired physical-line cache |
| anvil_q1_ht2_kv_writer | Complete-layer finite/protocol validation, padding, reserved-position writes and final-response ownership |
| anvil_q1_ht2_kv | Connected provisional/prefix read routing and selected-node layer copy without premature prefix publication |
| anvil_q1_ht2_counter_cdc | DDR accepted-beat byte counter and acknowledged full-width bundled snapshots |
| anvil_q1_ht2_control | HT2 configuration/status, five held low/high counter pairs and inherited-CSR forwarding |
| anvil_q1_ht2_decoder | Connected all-layer native decoder, synchronous vector storage, tied embedding/head and strict ascending argmax |
| anvil_q1_ht2_execution | Tree/decoder/KV/verifier integration, all-layer selected/correction copies and atomic prefix/result publication |
| anvil_q1_ht2_descriptors | Inherited descriptor transactions with native lengths and real finite-image validation reads |
| anvil_q1_ht2_mailbox | Acknowledged bundled-data clock crossing with held source and destination payloads |
| anvil_q1_ht2_transport | Full-burst response RAM, reset-persistent physical-debt draining and serialized Avalon transactions |

These are source structures, not independently verified numerical or timing
claims. Arithmetic pipeline reset inputs are the containing domain's synchronized
reset; public transaction leaves instantiate their own release synchronizer.
Divide/sqrt and exp use `enable` only for execution advances; a visible response
is consumed by `rsp_valid && rsp_ready` even when execution enable is low.
Dequantization globally stalls its operand/product/error metadata stages when
its final response is blocked. It accepts a new word on each enabled advance.

The array accepts consecutive column beats with no imposed input bubble.
Input bubbles advance valid/tag pipelines but not the accepted logical-column
counter. Output backpressure freezes the completed result, not a new dot.
Missing first, repeated first and changed transaction configuration produce an
error after a bounded pipeline drain. An open transaction has no invented
wall-clock timeout: missing last is observable on a conflicting next first,
and reset cancels an otherwise abandoned transaction.

## Boundaries and dependencies

| Producer / consumer | Ownership and requirement |
|---|---|
| DDR / core | Explicit reset-safe request ownership; acknowledged full-width CDC |
| Weight buffers / MAC | 64 broadcast 16-bit weights per column, two BF16 DDR beats; fixed slot/lane mask per dot |
| MAC / projection | Four FP32 contexts per slot/lane, logical-column phase preserved through skipped reads |
| SwiGLU / sparse DMA | BF16 magnitudes for predicate plus separately retained original-nonzero state |
| Sparse DMA / projection | Decision cannot imply approximation safety; nonzero skips require dense replay |
| Decoder / KV | Prefix+ancestor visibility; rejected branches never own committed entries |
| Decoder / verifier | Node targets come from actual native forward passes; prefix target cached internally |
| Commit / counters | Count tokens/steps only on the accepted atomic result |
| CSR / image | Mutations interlocked with execution/loading/pending results; format invalidates image/prefix |

The MAC uses spatial slot/lane replication (4*64 multipliers), not time-multiplexed
token invocations. FP32 accumulation is separately rounded, with four contexts
to cover four-stage add feedback and explicit same-edge retirement forwarding.
Global enabled advances move operand/product/tag stages together; output stalls
hold ownership. A skipped physical burst still retains its logical-column
arithmetic/context event, or requires an equivalent independently verified phase
mechanism; removing reads must never reorder the dense reduction.

## Outstanding integration

Top-level image loading, arbitration of descriptor validation versus native
execution and acknowledged transport traffic, legacy counter snapshot wiring,
compatibility delivery/timing repairs and the native top must be completed
before a ready handoff. Native decoder/execution and descriptor/transport
subsystems now exist but are not yet a top-level connected accelerator. Their correctness-first
burst/scalar
controller has request/response/control bubbles; array II=1 alone is not
end-to-end utilization or performance evidence, and full throughput scheduling
remains an integration obligation. No scalar Q16 decoder is used as a temporary
HT2 top. Verifier-owned tooling and all runtime-native hardware/performance
evidence remain pending.

## Saved native subsystem dataflow

The projection subsystem preloads its selected-format activation vectors once.
It checks padded descriptor lengths and 34-bit exclusive ends before metadata
or weight traffic. Per panel/group, AWQ scales/zeros are retained while each
column's packed weights are dequantized in 64 parallel lanes. Dense columns
collect two beats into one 1024-bit broadcast register; W4 columns collect one
real padded beat. Every active slot consumes that same register.
Sparsity removes physical reads, not logical MAC beats. Nonzero decisions are
repaired by reading the actual dense column before accumulation; eligible
and avoided deltas never count that column as an avoided read. Actual DDR
response counting remains outside the subsystem.

The sparse finite-image guarantee is fail-safe: absent validated ownership,
the subsystem reads even exact-zero columns. The saved validating image front end must
not manufacture that ownership from a host flag, a descriptor-only recommit
or a software numerical result. Every model tensor and AWQ metadata value
must meet the admitted finite-format rules.

RMSNorm, SwiGLU and RoPE operate on four masked FP32 slot vectors. They use
shared controller sequencing but independent per-slot arithmetic; unequal
divide/exp/trig response times cannot retire only part of a vector.
Selected-format rounding is exposed only at the specified downstream boundary.
RoPE uses immutable inverse-frequency constants, bounded RTL angle reduction
and split-half products; it does not read parent position-dependent RoPE data
as a native arithmetic substitute.

The provisional KV RAM has per-node/per-layer completion ownership, not a
reset loop over tensor storage. A failed partial write cannot become readable.
Retention only removes nodes. The independent tree-mask subsystem computes
absolute position from depth and selects ancestors, including self, without
slot-index position substitution. The saved attention controller consumes
explicit positions/ancestor masks and excludes siblings from KV traffic,
contexts, maximum and softmax reductions. Its KV router checks completed
provisional-layer ownership and committed-prefix bounds. Decoder scheduling
must still connect these contracts and actual projection outputs end to end.

Attention buffers one head's scores, exponentials and selected-format
probabilities in synchronous RAM. Its score products are accumulated into four
dimension-indexed contexts, while value products use absolute-position-indexed
contexts. It performs separate maximum, exponential-sum, probability and value
passes instead of an online-softmax approximation. Query-head to KV-head
mapping uses a compile-time ratio and explicit wrap counters. No runtime
division/remainder, host score, host probability or trigonometric table is
introduced.

Committed K/V live in separate per-layer DDR descriptors, with one padded
selected-format row per absolute position. The paired-line reader caches only
actual returned bytes. The writer validates and buffers a whole provisional
layer before writing a reserved row, and waits for every write response. The
connected KV controller never interprets these raw writes as a token commit.
Publication belongs to the saved execution controller, not the raw writer: all selected-token
layers and any correction must complete before changing the prefix visible to
the next batch. Partial raw writes after faults remain uncommitted.

The CSR overlay has one outstanding response, including forwarded inherited
accesses and physical-counter CDC waits. Local low reads latch pre-edge live
64-bit values; high reads consume the matching snapshot. The DDR physical-byte
counter uses an acknowledged held bus across clocks, with only request and
acknowledgement toggles passing through synchronizers. The overlay is not a
descriptor/image validator and must not manufacture image-valid state.

The theoretical array peak at 100MHz is 25.6 billion separately rounded products/s.
This is not measured throughput. Four token slots alone prove neither accepted
reuse>=3.2 nor TPM>=8000. Rejected/corrective/replay traversals, metadata, wall
time and actual accepted DDR response bytes all remain charged.

## Claim-to-evidence index

There are no functional, synthesis, timing, board or benchmark results in this
Designer increment. Independent Verifier must author and execute the mandatory
commands in SPEC. The runtime alone may approve engineering delivery and produce
the final product PDF afterward.

The first static-only parse attempt is retained at
`evidence/preparation/static-elaboration-20261031T161949Z-a192ef87/receipt.json`.
It failed because `large` and `small` were used as identifiers in the FP32 adder;
those Verilog strength keywords were renamed to `larger_operand` and
`smaller_operand`. This was a parser repair, not a functional experiment.
The repaired static-only elaboration exited zero; its argv, source hashes,
version output and raw logs are retained at
`evidence/preparation/static-elaboration-20261031T162050Z-039c8ae5/receipt.json`.
It parsed all saved RTL roots, not the unfinished native top. This establishes
no behavioral, synthesis, timing or performance result.

The second source increment adds the ten subsystem files listed after the
original thirteen leaves above, preserving all original RTL bytes.
Icarus Verilog 12.0 static-only elaboration of all 23 RTL roots exited zero
with empty stderr. The exact relative argv, source hashes, tool version,
timestamps and raw logs are retained at
`evidence/preparation/static-elaboration-20261031T163332Z-cb1bf6ee/receipt.json`.
No functional simulation, synthesis, tool installation or hardware experiment
was run. Python standard-library arithmetic was used only to generate
immutable pi, polynomial and inverse-frequency source constants, not as a
functional checker or a product execution path. The earlier failed parser
receipt and its repair remain unchanged.

Continuation must start from all saved sources. The fourth increment adds the
connected decoder and execution transaction, native descriptor validation,
mailbox and reset-draining transport. Next connect the image loader and
top-level command/CSR/descriptor/DMA arbitration, including atomic same-edge
mutation interlocks and acknowledged inherited counter snapshots. Then finish
compatibility copies/timing repairs, throughput scheduling and
`anvil_q1_ht2_top`.
Do not mark the design ready or start Designer-owned functional/synthesis
harnesses on the basis of static elaboration.

The third increment adds the six source stems listed after provisional KV:
attention, KV reader, KV writer, connected KV ownership/router, counter CDC and
CSR control. Icarus Verilog 12.0 static-only elaboration of all29 RTL roots
exited zero with empty stderr. Its exact argv, RTL hashes, tool version,
timestamps and raw logs are retained at
`evidence/preparation/static-elaboration-20261031T164134Z-a5a17795/receipt.json`.
No earlier source or failed receipt was replaced. No functional simulation,
synthesis, hardware execution, tool installation, verification-source edit or
reference-source edit was performed in this increment. The connected native
decoder/top and outstanding integration above remain incomplete; this is a
saved continuation, not a ready design or engineering acceptance.

## Fourth saved source increment

The decoder now keeps embeddings/residuals/normalization/projection/operator
vectors in synchronous RAM and sequences the complete native operator order.
Its output head shares the global dense embedding descriptor, including in
W4 mode; the seven decoder matrices use the selected dense/AWQ panel layout.
Q/K/V biases are added only after the four-context reduction. Q/K RoPE and
V encoding establish the attention/KV boundary. The final head traverses
ascending IDs with strict-greater argmax.

The execution controller connects tree validation, the decoder, KV routing and
the greedy verifier. Selected nodes are copied in parent-before-child order,
all layers per node. A correction starts a new provisional transaction only
after selected-node copies finish, uses that reserved prefix for its actual
forward pass, and receives its own all-layer copy. Public prefix state changes
only on the atomic commit or final ordinary-logit handshake. Ordinary logits
are buffered until copy success, preserving a no-logit response for forward/
copy failure. This does not constitute tested sequence equivalence.

The native descriptor endpoint uses the frozen panel/native-KV lengths and
retains parent staging/install/recommit semantics. Recommit actually reads
model-tensor data and validates finite dense values and nonnegative finite
FP16 AWQ scales. A sticky validation-invalidation flag prevents an intervening
image mutation from producing a later successful recommit. The CSR overlay
now handles inherited mode address0x000c against its authoritative format
register instead of forwarding it into a second mode state.

The transport buffers complete read bursts before returning responses through
acknowledged mailboxes. A single configuration-initialized ten-bit physical
debt storage word survives logical resets and is updated even during reset.
Logical FSM/client/mailbox ownership resets; new traffic is held until old
accepted bus responses drain. This deliberately distinguishes physical debt
from reset-cancelled logical ownership without assuming a finite quiet period.
Unexpected response types/counts quarantine the transport explicitly. FPGA
initial-state inference, reset safety, CDC and fitted timing remain independent
verification obligations, not established results.

An intermediate Icarus12.0 static-only elaboration of31 saved RTL roots
exited zero with empty stderr at
`evidence/preparation/static-elaboration-20261031T164820Z-d623f3d5/receipt.json`.
That receipt predates the descriptor/mailbox/transport files and subsequent
integration-source edits; it is not evidence for the final fourth-increment
source set. Earlier failed/parser-repair receipts remain unchanged.

The final34-root static parse initially failed with exit63 at
`evidence/preparation/static-elaboration-20261031T165421Z-7cc171dc/receipt.json`:
the DDR recovery process had accidentally been nested inside the core-clock
process. Moving it to module scope repaired that syntax defect. The fresh
Icarus12.0 static-only elaboration exited zero with empty stderr at
`evidence/preparation/static-elaboration-20261031T165435Z-49556440/receipt.json`,
whose `repair_of` points to the preserved failure. This receipt hashes all34
current RTL files, including the updated CSR overlay. Python standard-library
subprocess/hash/JSON handling recorded these static diagnostics; no functional
simulation, synthesis, hardware execution, tool installation, verification-source
edit or reference-source edit occurred. The missing top-level integration and
throughput/compatibility work remain prerequisites for a ready handoff.
