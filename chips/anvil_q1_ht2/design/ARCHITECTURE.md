# Native HT2 architecture

## Implementation ledger

This is the Designer implementation handoff, not an accepted product or
acceptance report. The sources include connected native top-level execution,
streaming memory return, panel prefetch and vector scheduling. Independent
functional, synthesis, timing, board and full-model performance evidence is
still required; source structure does not establish those results.

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
| anvil_q1_ht2_panel_prefetch | Credit-limited 128-column synchronous ring, 64-column burst reservation and held broadcast output |
| anvil_q1_ht2_projection | Connected four-slot array, dense/AWQ streaming issue, sparse predicate, exact preflight and column replay |
| anvil_q1_ht2_rmsnorm | Four-slot frozen ascending left folds, mean/epsilon/sqrt/reciprocal and pipelined weighted output |
| anvil_q1_ht2_swiglu | Eight interleaved four-slot engines with ascending dispatch/retirement and all-engine abort drain |
| anvil_q1_ht2_swiglu_engine | Stable sigmoid, separately rounded products and retained original nonzero bits |
| anvil_q1_ht2_rope_frequency | Position-independent selected-head-dimension FP32 inverse-frequency constants |
| anvil_q1_ht2_rope | Four-slot split-half rotation, per-command RTL-computed trig reuse and selected-format attention boundary |
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
| anvil_q1_ht2_response_fifo | 512-entry dual-clock synchronous RAM FIFO, Gray-pointer synchronization and held output |
| anvil_q1_ht2_transport | Streaming tagged response FIFO, reset-persistent physical-debt draining and serialized Avalon transactions |
| anvil_q1_ht2_image_loader | DDR-domain upload interface, acknowledged beat/result crossings, whole-upload ownership and sticky error clear |
| anvil_q1_ht2_dma_mux | Registered four-owner request arbitration and last-response ownership |
| anvil_q1_ht2_top | Parent-compatible ports plus batch/commit, CSR/load/execution interlocks, native hierarchy and physical transport |
| anvil_q1_ht_* / anvil_q1_top | 29 parent compatibility delivery modules, separate from the immutable reference source set |

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
| DDR / core | Reset-safe request ownership; acknowledged command crossing and Gray-pointer response FIFO |
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

## Integration and scheduling handoff

Top-level image loading, descriptor/execution/transport arbitration, inherited
counter snapshots and compatibility delivery sources are connected. Read
responses now stream through a dual-clock FIFO instead of waiting for a full
burst and then round-tripping each beat through a mailbox. Dense projection
prefetch overlaps the shared array; W4 dequantization carries matching
activation/column tags while group metadata loads. RMSNorm streams its final
two rounded multiplies, SwiGLU interleaves eight independent vector engines,
and RoPE reuses RTL-computed position/frequency results across heads.
Array II=1 and these scheduling structures are not measured end-to-end
utilization or performance. Sparse column reads and ordered scalar reductions
still have protocol/dependency bubbles; all their actual costs must be charged.
No scalar Q16 decoder is used as a temporary HT2 top.
Independent compatibility behavior, timing/resource validation, Verifier-owned
tooling and all runtime-native hardware/performance evidence remain pending.

## Saved native subsystem dataflow

The projection subsystem preloads its selected-format activation vectors once.
It checks padded descriptor lengths and 34-bit exclusive ends before metadata
or weight traffic. Per panel/group, AWQ scales/zeros are retained while each
column's packed weights are dequantized in 64 parallel lanes. Dense columns
collect two beats into one 1024-bit broadcast register; W4 columns collect one
real padded beat. Every active slot consumes that same register.
With sparsity disabled, the prefetcher issues up to 64 contiguous columns per
request (128 dense beats or 64 W4 beats, shortened at the panel tail).
Two 128-entry synchronous RAM banks hold the lower/upper dense words, with
produced/consumed column credits and a separate held output. At most one
reserved burst is outstanding. Native dense issue pairs each fetched column
with its synchronous activation read; W4 issue additionally pipelines the
activation and absolute column through all four dequantization stages.
Group boundaries stop new W4 admission until the next zeros/scales arrive,
without changing the earlier pipeline's metadata or arithmetic order.
The metadata and prefetch paths share registered response ownership.
No prefetch runs on the sparse path: fetching a column before its predicate
would falsely claim skipped physical traffic.

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

RMSNorm retains the exact scalar left fold and reciprocal/square-root order.
Only the final elementwise scaling is overlapped: a synchronous vector read
feeds x*inverse and then a separate gamma multiplier, both with three
registered stages. Gamma/index tags and the read-ownership register stall
with the common arithmetic enable. This does not reassociate either product.

SwiGLU has eight independent four-slot engines. Element i maps to engine
i[2:0], with local index i>>3. Input dispatch and output retirement each
advance monotonically, allowing computation and further vector-RAM reads
while earlier engines run. There is no cross-element reduction to reorder.
Each engine retains the stable-sigmoid sequence and original FP32-nonzero
observation. Abort cancels every engine and drains ownership before completion,
even if the decoder holds abort high. The smallest intermediate vector
supplies exactly one word to each engine. Decoder input/output counters are
independent, so issuing another word cannot overwrite an unretired result.

For each RoPE command, head zero computes every pair's angle and sin/cos
using RTL arithmetic, then writes a synchronous four-slot trig cache.
Subsequent heads use those identical position/frequency results with their
own Q or K inputs. A new command always recomputes head zero, so stale RAM
contents have no validity after reset, error or a position change. This cache
is produced by RTL execution, not a host-generated trigonometric table.

The provisional KV RAM has per-node/per-layer completion ownership, not a
reset loop over tensor storage. A failed partial write cannot become readable.
Retention only removes nodes. The independent tree-mask subsystem computes
absolute position from depth and selects ancestors, including self, without
slot-index position substitution. The saved attention controller consumes
explicit positions/ancestor masks and excludes siblings from KV traffic,
contexts, maximum and softmax reductions. Its KV router checks completed
provisional-layer ownership and committed-prefix bounds. The connected decoder
sequences these contracts and actual projection outputs end to end; independent
behavioral checking must establish their correctness.

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

## Fifth saved source increment

The native top now wires the descriptor endpoint, execution controller, CSR
overlay, image loader, registered DMA mux and reset-draining transport.
All model/projection reads and committed KV writes use this actual transport.
Descriptor validation, KV traffic and image writes have separate registered
response owners. Inference admission excludes CSR presentation/ownership,
pending load acquisition, active image loading and descriptor mutation or
validation. Loading first invalidates image/prefix ownership; successful
physical writes alone never revalidate the model.

The parent load interface remains in the DDR clock domain. Each accepted beat
crosses to the core as a held payload, is written through the same transport
as execution traffic, and waits for the physical response before accepting
the next beat. Final completion returns to the DDR domain before releasing
core ownership. Error clear can be acknowledged while an upload is still
waiting for its grant, avoiding a clear/acquire circular wait. Alignment
validation precedes traffic and an aligned final physical line is legal.

The top retains inherited token-cycle and physical-read-beat observations.
Physical beats cross through acknowledged complete 64-bit mailbox snapshots,
not independent bit synchronizers. HT2 byte snapshots remain independently
on-demand. Ordinary/batch simultaneous presentation reaches one explicit
execution rejection instead of two independent operations.

The 29 parent modules were imported into `rtl/` without editing the reference
directory. Five compatibility delivery copies (`anvil_q1_ht_dequant`,
`anvil_q1_ht_mac_lane`, `anvil_q1_ht_decoder`, `anvil_q1_ht_kernel`,
`anvil_q1_ht_nonlinear`) evaluate existing conversion/round/saturation helpers
on combinational wires before sampling. The arithmetic, register count,
source operands and sampling edges are unchanged; this is synthesis-process
hygiene, not a demonstrated timing or equivalence result.

Icarus Verilog 12.0 static-only elaboration of all66 native/compatibility
source files exited zero with empty stderr at
`evidence/preparation/static-elaboration-20261031T165847Z-38e4a75b/receipt.json`.
That source set predates the subsequent top-level addition of CSR response
errors to the descriptor sticky-fault event. The final source-matched
Icarus12.0 static-only elaboration of all66 files also exited zero with empty
stderr at
`evidence/preparation/static-elaboration-20261031T170104Z-2cffdd57/receipt.json`.
No functional simulation, synthesis,
hardware execution, installation, verification-source edit or reference-source
edit occurred. The earlier failed receipts and repairs remain unchanged.

## Sixth source increment and independent-Verifier handoff

Added `anvil_q1_ht2_response_fifo`, `anvil_q1_ht2_panel_prefetch` and
`anvil_q1_ht2_swiglu_engine`. Updated the transport, projection, decoder,
RMSNorm, SwiGLU and RoPE scheduling, retaining the native top/CSR/load/KV
integration and all compatibility delivery sources. SPEC and the current
architecture sections describe the new ownership and cycle boundaries.

The transport no longer buffers a complete burst before serializing its
responses through a mailbox. The projection no longer serializes each dense
column's memory request, conversion and MAC issue. Dense prefetch and native/
AWQ issue now overlap, while sparse mode still predicates actual requests and
preserves the dense logical-column phase. No approximation certificate or
nonzero-skip acceptance shortcut was added.

RMSNorm scaling, interleaved SwiGLU input/output scheduling and first-head
RoPE trig reuse retain the frozen per-element operation order and rounding
boundaries. Source inspection identified that a held abort could repeatedly
reenter the new SwiGLU wrapper's drain state and prevent its completion.
The abort-entry condition now excludes DRAIN, allowing cancellation to settle.
No functional failure or passing functional experiment is claimed for that
inspection repair.

The initial 69-source Icarus12.0 static-only elaboration exited zero with
empty stderr at
`evidence/preparation/static-elaboration-20261031T170800Z-3a1c8160/receipt.json`.
It predates the held-abort drain repair. The final source-matched 69-source
static-only elaboration also exited zero with empty stderr at
`evidence/preparation/static-elaboration-20261031T171102Z-5178c76c/receipt.json`.
Both retain exact project-relative argv/cwd, source SHA-256 values, version
output, start/end timestamps, timeout/exit and raw stdout/stderr. All earlier
failed receipts remain preserved. Only Icarus static elaboration and Python
standard-library diagnostic recording ran; no functional simulation, synthesis,
tool installation, hardware execution, verification-source edit or
reference-source edit occurred.

The design is handed to independent Verifier for the mandatory behavioral,
numerical, protocol, mutation, synthesis, benchmark-adapter and reproduction
work. Particular new boundaries are continuous DDR responses across unequal
clocks, FIFO reset/debt drain, ring credit/tail/error handling, AWQ group/tag
alignment under stalls, simultaneous SwiGLU input/output and held-abort
completion, RMSNorm tag/operand freeze, and RoPE command-cache ownership.
No tests or acceptance predicates may be replaced by these source descriptions.
Full-model inputs/comparators/bridge execution, physical STA/HIL and measured
performance/fidelity remain unestablished. Final report generation remains
the shared runtime's post-acceptance responsibility.

The next Designer increment must replace per-beat weight-response mailbox
serialization with bounded streaming CDC/burst buffering, overlap projection
weight acquisition with array issue, and address vector scalar-unit utilization
without changing the frozen arithmetic order or backpressure/reset ownership.
Only after that design work is complete should a ready handoff request the
independent Verifier's behavioral, numerical, mutation and synthesis checks.
No claimed array peak, static compiler result or compatibility source import
substitutes for the admitted end-to-end throughput and physical acceptance.
