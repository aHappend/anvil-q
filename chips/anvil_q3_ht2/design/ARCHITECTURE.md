# HT2 implementation architecture

## Current increment

Implemented sources comprise sparse DMA, the FP package, registered weight
decode/multiply/add helpers, Q16/FP boundary converters, the per-lane stripe
controller, the four-bank tile MAC, private scratch, causal tree attention and
its quantized KV reader, the greedy verifier and atomic KV commit engine,
the batched projection/resident metadata loader and shared embedding/output-head
token I/O, and the connected batched decoder with scalar image/scratch transport,
scratch arbitration and quantized shadow-record staging.
They do not constitute an integrated
public accelerator. The parent RTL is read-only; tests and FPGA integration are not
authored by this increment.

The DMA has four synchronous 16-bit activation banks and one 4-bit keep-mask
bank, each with MAX_COLUMNS entries. No RAM data reset is required: commands
write every addressed entry before a descriptor can enable reads. A three-stage
activation pipeline accepts consecutive columns without a read/write collision
on scan RAM. It counts retained columns, scans retained entries in order, and
issues no qweight traffic before descriptor acceptance.

| Resource | Producer | Consumer | Release / ownership |
| --- | --- | --- | --- |
| Activation and mask RAM | Activation pipeline | Selected-column reader | Entire tile completion or cancellation |
| Selected column registers | Synchronous RAM reader | Address/operand path | Operand transfer |
| Physical request register | Address stage / crossing controller | Shared DDR client | Accepted request or cancellation before acceptance |
| One outstanding-read bit | Physical request transfer | DDR return | One known return, including stale cancellation return |
| 17 source-word banks | Known successful DDR returns | Local AWQ repacker | Operand transfer or cancellation |
| Operand register | Registered repacker | Tile-batch MAC input | weight_valid && weight_ready |

The source-word banks are not a large asynchronously indexed memory. A
descriptor assigns each bank a physical-line selector and a four-bit word
index. Return capture selects one of sixteen source words per bank. Local
repacking selects at most two adjacent banks per nibble. This splits physical
word selection from local nibble permutation across the required R/R+1 boundary.

Command setup pipelines matrix multiplication, allocation rounding and
base-plus-extent separately before activation ingestion. Selected-column
addressing separately registers stride multiplication, packed-start addition
and line alignment/bounds checking. All calculations use widened intermediates.

The one-outstanding policy is intentionally conservative. It fulfills the
corrected one-column assembly contract without a response-backpressure port,
does not reuse lines between columns, and counts every physical reread.
The shared public transport must provide sufficient buffering/prefetch
elsewhere to sustain the arithmetic array. No achieved throughput is inferred
from this leaf's storage or lane counts.

## Registered projection tensor path

`anvil_q3_ht2_tile_batch_mac` owns one output-row tile. Its command registers
hold epoch/layer/projection/row and row/token masks until response transfer.
128 weight decoders share one qweight/qzero burst; each decoder's registered
binary32 weight feeds the corresponding row of four literal token banks.
AWQ source nibbles are selected in local packed-row order exactly once.
DMA is responsible for global-to-local repacking before this interface.

Each of the 512 production lanes has a multiplier and a stripe/tree adder.
The activation path registers binary16 capture, exact binary32 expansion and
broadcast alignment. Weight decode independently registers operand capture,
exact delta-scale multiplication and binary32 normalization. The subsequent
six-stage lane multiplier produces post E8 for a burst accepted at E0.
The shared issued-ordinal tag is delayed to the same product edge.

The next edge captures the product and its stripe into the adder. Its final
rounding result is registered directly in that stripe at E14. Eight stripes
separate updates sufficiently for consecutive issued ordinals. No cycle-level
behavior or achieved initiation interval has yet been independently measured.
The fixed reduction controller issues four first-level additions at last+15
through +18, two second-level additions at +24/+25 and the final addition at
+31. The held top sum register captures the final retiring result at +36.
This deliberately avoids an extra output-register edge after an arithmetic
helper result, which would violate the frozen latency.

All helper stages and shared tags use the same pipeline-enable condition.
Input bubbles are tagged invalid, not interpreted as zero-column beats.
The pipeline runs during feed/drain and freezes while the public result
owns output storage. Flush and faults invalidate all local work; this tensor
leaf owns no DDR returns, so DMA/shared transport retain their own draining
responsibility.

The FP package provides bounded eight-bit leading-zero groups, grouped
leading-zero descriptors, jam shifts, exact FP16 expansion and final
nearest-even pack logic. Arithmetic functions are evaluated on wires outside
resettable sequential processes. Weight decode contains one 11-by-4 product
stage; FP32 multiplication separates its significand multiplier from exponent
normalization and final rounding. Adders separate alignment, arithmetic and
normalization/rounding. FPGA mapping and actual timing/resource suitability
are still unproven and require the unchanged independent hardware gates.

Four-stage conversion helpers express the Q16-to-FP16 and FP32-to-Q16
boundaries. The projection scheduler connects them to common scratch reads
and four-candidate result writes. The enclosing scalar decoder is now connected;
no numerical equivalence is inferred from authored connections.

## Shared projection and resident image metadata

`anvil_q3_ht2_projection` executes a complete projection for one to four
candidate banks. It derives the parent's exact seven-matrix image offsets
from widened elaboration constants, then registers layer products, matrix
offsets and region-base additions separately. Its scratch slot mapping is
identical to the parent: 1->2/3/4, 5->6, 8->9/10 and 11->12.
Each 128-row tile uses the DMA's retained-count/tail-mask descriptor,
consumed by the literal `tile_batch_mac`.

The first row block converts one common-mask scratch read per logical column
through four Q16-to-FP16 helpers. The DMA retains these activation/mask banks
for later row blocks under its internal `RETAIN_SCAN=1` setting.
A complete projection command explicitly flushes prior scan ownership before
setup; row-block commands must match the complete retained scan identity.
No later block rereads scratch activations or reevaluates SwiGLU. Standalone
DMA defaults retain their original ingestion contract.

The literal `resident_metadata` loads all image-backed group records for the
owned row block. Containing packed qzero words are assembled in 17 bounded
source-word banks, then global AWQ nibbles are normalized into local packed
rows. Natural-row scales are captured with a bounded 32-half line selector
per bank. One zero and one scale RAM bank per row provide synchronous resident
queries; query data cannot be visible until all groups load. Tail rows are zero,
and invalid active scales fault explicitly. Metadata uses aligned physical
reads, full allocation-bound checks and actual padding/repeated-line accounting.

The DMA holds a complete logical-column operand during each resident query.
Weight, zero, scale, activation, keep and last fields then transfer together
into the MAC. One physical weight traversal serves all active candidates,
not four serial parent projections. The conservative DMA/query schedule does
not claim measured full-rate array utilization; independent performance checks
remain required.

Four banks of sixteen eight-word result-register groups capture all 512 MAC
entries. Eight-way selection and sixteen-way bank selection are separated
by registers. Four FP32-to-Q16 helpers process one row's candidates together.
For projections 0..2, one shared compatible FP16 bias is read after conversion;
registered expansion, addition and saturation states implement the Q16
boundary. Each active candidate then receives one acknowledged scratch write.
Result storage cannot be overwritten until all tile writes finish.

Three ordered read clients export qweight, metadata and bias traffic for the
future public DDR arbiter. Physical-handshake counters, logical descriptors
and common activation reads remain separate. Fault/cancellation flush local
producers while accepted scratch/bias/metadata/qweight responses drain.
No private read client is an idealized memory bypass.

## Shared embedding and output-head token I/O

`anvil_q3_ht2_token_io` implements the compatible FP16 embedding image and
Q16 scalar output head. Embedding writes active candidate scratch banks
individually. Output-head commands preload slot 14 into four synchronous
activation banks, then walk vocabulary rows with one shared physical weight-line
cache. Every selected FP16 half is expanded once with parent Q16 rules and
broadcast to four literal segmented multipliers; exact signed products feed
four segmented 128-bit accumulators. Component order and final parent
rounding/saturation are preserved, distinct from W4 FP32 tile accumulation.

The head genuinely reuses weights across candidates, but is folded by component.
There is no claim of 512 head multipliers or measured end-to-end token rate.
Aligned-line reads include full physical bytes; candidate-consumer counts
and common activation-preload counts are separate hardware counters.
Narrow rows may share cached lines without altering image geometry.

Complete node logit streams interleave candidates at increasing vocabulary
indices, carry transaction ownership and hold while blocked. Hardware argmax
state updates only on logit handshakes, resolving ties to the smaller ID.
The successful completion edge supplies four argmax IDs for the decoder's
prefix/leaf cache. KV publication remains the verifier/commit engine's
responsibility, not token I/O's.

## Batched scalar decoder and private memory integration

`anvil_q3_ht2_decoder` is a complete internal evaluation scheduler. It connects
one shared projection module, one shared embedding/output head, parent scalar
normalization/RoPE/residual/SiLU kernels, the quantized KV staging module, literal
`tree_attention`, scratch arbitration and literal `private_scratch`.
It is not yet the public top: sequence ownership, ordinary-token publication,
verifier dispatch and physical DDR arbitration remain outside this module.

The scheduler completes each scalar operation for every active node before
advancing to the next shared projection. Q/K/V, O and gate/up/down each walk
weights once for the full active mask. Actual normalized scratch activations
drive Q16-to-FP16 conversion; actual computed SiLU/up products drive down-proj
scanning. Layer order and residual destinations follow the parent slot layout.
All active nodes' rotated K and V are encoded and written to shadow backing
before the first attention command in a layer. Final normalization writes
slot 14 before the shared FP16 head computes complete target logits.

The three-client scalar adapter retains the parent kernel request protocol
without the parent's large combinational all-image mapper. It handles only
normalization, RoPE and scratch kinds actually used by these kernels. Registered
row ordinal/product, column addition and image-base states bound address depth;
allocated line bounds are checked before issuance. Separate 16-way word and
two-way half selection precede the scalar response. Its one-line cache is
invalidated on each evaluation and all cancellation/faults.

The five-client scratch arbiter accepts one upstream request into registered
offer storage, then transfers it to the single physical private-scratch port.
Owner/node/mask are checked on every physical response and remain reserved
until transfer. Cancellation of an upstream-accepted but physically unaccepted
offer generates one internal error response rather than silently dropping the
producer's outstanding bit. Physical accepted accesses drain to their original
producer. Public responses/requests are suppressed during flush itself.
Private scratch validity is cleared only at a drained new-evaluation boundary;
flush does not discard a physical response beneath a waiting producer.

Quantized staging gathers exact partial-group lengths from scratch slots 3/4,
zeros tail values and uses the unchanged INT8/INT4 codec. Node interleaving is
allowed by the sink, but each node is staged in layer/key-value/head/group order.
The sink's stage-ready reassertion retires a validated and accepted shadow write;
a settle edge prevents the ready sampled on the original record handshake from
being mistaken for this retirement. The final record uses the same retirement
barrier. This deliberately prevents early attention from reading unfinished
shadow records. No existing committed count is advanced by the decoder.

Six physical read clients expose qweight, metadata, bias, embedding/head,
normalization/RoPE image and quantized tree-KV traffic. Six accepted-beat
counters retain their distinct categories for complete-transaction accounting;
the enclosing atomic engine's write/copy traffic must be included separately.
Private scratch is on-chip storage rather than fabricated DDR response data.
The public top must route every client through the actual shared Avalon path.

Detailed pre-edge ownership, reset, cancellation, singleton/partial-group
and non-power-of-two-client rules are in SPEC.md's decoder boundary table.
Functional, numerical, mutation, synthesis and current-target evidence remain
entirely pending independent execution.

## Full-product connection plan (public integration not implemented)

`anvil_q3_ht2_top` will own mode-exclusive legacy and HT2 command dispatch.
The unchanged literal `legacy_core` retains parent behavior. HT2 decoder scheduling
will process active candidates together by layer/projection, supply real
SwiGLU activation banks to sparse DMA, normalize resident qzero records to
local packed rows and provide natural-row FP16 scales to `tile_batch_mac`.
Qweight traffic and metadata traffic share the public DDR arbitration path.

The authored MAC provides four physical token banks, 128 lanes per bank,
three-stage shared weight decode, six-stage products/adders, eight stripe sums
per output and the fixed final tree. Surrounding parent scalar paths stay
Q16.16; projection conversion helpers are connected internally but still need
decoder/top wiring.

The batched scalar decoder is now implemented; public integration remains.
Ordered vocabulary logits are connected to the decoder's internal output but
not yet to the verifier/public dispatch. The modules below do not replace that work. Image and
complete integrated extents still require production parameter validation.

## Private scratch, causal attention and atomic KV

`anvil_q3_ht2_private_scratch` implements four synchronous banks with the parent's
15-slot Q16 layout. A common slot/index read can return one to four token values
without reading a separate activation image over DDR for each candidate.
Each bank has initialized-bit RAM, cleared one address per clock after reset or
flush. Bank reads/writes and validity clearing are in reset-free synchronous RAM
processes; controller state is asynchronously reset. Invalid active reads return
an error, not fabricated zeros. Production storage is analytically 864256 data
bytes and 27008 validity bytes; this is not a fitted Arria 10 resource result.

`anvil_q3_ht2_tree_attention` walks the selected node's lower-index parent chain
in two registered stages per ancestor. It verifies positions and the exact
visibility mask before starting a literal unchanged `anvil_q3_ht_attention`
scalar kernel. Query/context accesses use slots 2/5 in the selected node's
scratch bank. The kernel's initial commit command only receives a local private
readiness acknowledgement; it cannot write KV or expose a new committed token.
The decoder waits for validated shadow staging before attention begins.
Parent dot, softmax, context rounding and h>>3 GQA mapping are retained.

The literal `causal_kv_reader` chooses committed backing below the prefix count
and exactly one visible private node above it. It computes aligned parent/shadow
addresses in registered stages, tracks one accepted response, and uses the
unchanged parent symmetric codec to reconstruct INT8/INT4 data before scalar
use. A synchronous tagged resident cache has explicit replacement wrap for
residency one, three and other legal sizes. The wrapper invalidates residency
at each attention command, so a reused request ID cannot expose overwritten
shadow data from an earlier tree. Long-context records still come from DDR,
not from an idealized all-context on-chip array.

`anvil_q3_ht2_spec_verifier` validates four-slot graphs, generates evaluation
positions/visibility, captures ordered node logits and compares them one edge
later. Selection uses a registered child search followed by a registered path
update, packing only matched children in path order. Complete logits, drained
comparison stages and all expected shadow writes are prerequisites of selection.
Missing, duplicate or wrong-owner records/logits fail explicitly. Zero accepted
tokens is an ordinary successful rejection, not a command error.

Its literal `kv_commit_engine` owns one visible count/epoch. Staged records may
interleave nodes, but each node's records have fixed layer/key-or-value/head/group
order, permitting four bounded ownership counters rather than a large bitmap.
Each accepted record is decoded/validated before a shadow write. Four node-major
shadow images follow the entire parent-compatible committed reservation.
Parameter extents use 128-bit constants before runtime address narrowing.

After selection, the engine copies selected records to invisible positions in
path order. One outstanding read reserves the return register, including an
immediate accepted-request return. Writes finish on accepted record requests;
there is no invented write-response-valid input. Available response errors are
monitored independently of read-valid. Two quiet fence edges precede one
cancellation-sensitive publication, after which the verifier registers its held
public response on the following edge. The bridge must map the actual controller
error/fence behavior before this can constitute integrated atomicity evidence.

Flush discards unaccepted requests, drains accepted returns and leaves the
previous visible count unchanged. Explicit new-sequence reset must invalidate
the sequence-owned verifier and its enclosing transport; cancellation instead
flushes without resetting its prefix. Scratch response ownership survives
cancellation until its accepted response drains. No simulation, atomicity,
context, quantization, traffic, synthesis or timing result is inferred from
these authored connections.

## Integration dependencies and pending evidence

| Obligation | Guarantee needed from integration |
| --- | --- |
| Command epoch/layer ownership | Validate against current model and transaction before DMA command |
| Read returns | Ordered, one return per accepted burstcount-one request, with controller errors surfaced |
| Flush | Do not reset/reassign the DDR client until drain_done; no late return can acquire a new column |
| Reset | Reset enclosing read transport along with leaf ownership |
| New sequence / cancellation | Reset sequence-owned visibility only for new sequence; cancellation flush preserves the committed count |
| Tree attention launch | Every selected node/layer shadow record is validated and its physical write accepted before attention reads it |
| Publication fence | Map actual controller response errors through the final accepted write and two quiet fence edges |
| Scratch | Overwrite each candidate's consumed inputs and retain valid response ownership until transfer/drain |
| Metadata | Image-loaded qzero/scales, tail-zeroed and AWQ-local-normalized consistently |
| Activation reuse | Projection retains scan storage across row blocks; decoder must preserve its actual source-slot activations during ownership |
| Physical traffic accounting | Include qweight reads, all metadata, crossing lines, allocation padding and repeated addresses |
| FPGA | Actual HT2 top, Arria 10 device, 10.0-ns SDC, shared-DDR bridge and PCIe host mapping |

Cross-row-block scan reuse is now implemented as an internal elaboration option,
without additional public inputs or a host oracle. The enclosing projection
flushes retained identity at each complete transaction. Static elaboration alone cannot
establish behavior, performance, arithmetic correctness, synthesis or timing.
The single Icarus static elaboration (`iverilog -g2012 -t null`) exited zero.
Its retained command, source hashes, tool version and raw outputs are at
`evidence/preparation/sparse-dma-elaboration-20261102T195513357176Z/receipt.json`.
This checks the sparse-DMA RTL only; the receipt's document hashes describe the
documents before this evidence citation was added. No functional or synthesis
experiment has been executed. Static elaboration is advisory only, not passing
engineering evidence.

The production-width tile MAC was also statically elaborated with all nine
current RTL sources parsed, using `iverilog -g2012 -t null -s
anvil_q3_ht2_tile_batch_mac`. It exited zero in 2.39 seconds; exact argv,
RTL hashes, tool version, times and raw outputs are retained at
`evidence/preparation/tile-mac-elaboration-20261102T200349722122Z/receipt.json`.
No simulation, numerical experiment, synthesis or hardware execution occurred.
The converters were parsed in that command but were not selected elaboration
roots. The arithmetic/tile path still requires independent functional and
structural verification; this receipt does not establish its correctness.

The new KV engine, verifier, KV reader, tree attention and private scratch were
statically elaborated together with the production tile MAC in one Icarus
`-g2012 -t null` invocation. Verifier/tree roots selected INT4, while standalone
engine/reader roots selected their default INT8 configurations. The command
parsed all current RTL and the unchanged reference dependency and exited zero
in 2.44 seconds. Exact argv, source hashes, installed tool version, timestamps
and raw outputs are retained at
`evidence/preparation/kv-tree-scratch-elaboration-20261102T201700004266Z/receipt.json`.
This was a syntax/elaboration check only. No functional simulation, reference
comparison, mutation, synthesis, timing or hardware experiment ran.

The next owned implementation work is connection
of the decoder's staging/logits to the verifier, ordinary-token atomic priming,
sequence/mode control, public top/shared DDR integration and FPGA bridge
configuration. Tests remain exclusively Verifier-owned. The complete design is
not ready for independent verification handoff or engineering acceptance.

## Current increment's static diagnostic

The new projection scheduler, shared token I/O and resident metadata loader
were selected together for a single fast Icarus static-elaboration diagnostic.
Projection and token I/O selected production defaults; the separate metadata
root selected GROUP_SIZE=8 and MAX_INPUTS=9. All current RTL and the immutable
reference dependency were parsed. There was no testbench, simulation,
numerical comparison, synthesis or hardware execution.

The first invocation exited 12 because the command placed the parent package
after RTL that references `anvil_q3_pkg`. Its exact failed argv, source snapshot,
tool version and raw error output remain at
`evidence/preparation/projection-token-io-elaboration-20261102T202949736134Z/receipt.json`.
The corrected invocation loads `anvil_q3_ht_reference/rtl/anvil_q3_00_pkg.sv`
before the HT2 sources, matching the earlier accepted source-order convention.
No RTL changed between those invocations. It exited zero in 2.65 seconds;
the separate linked receipt is
`evidence/preparation/projection-token-io-elaboration-20261102T203019442393Z/receipt.json`.
These are advisory syntax/elaboration results, not engineering acceptance.

Portable compile ordering is parent sources (package first), then HT2 sources
(`anvil_q3_ht2_00_fp_pkg.sv` first among HT2 files). The independently owned
verification entry point must supply both dependencies in that order.

## Decoder increment's static diagnostic

One fast `iverilog -g2012 -t null` command elaborated the connected decoder at
production INT8 defaults, a standalone INT4 KV staging root, and scalar/scratch
arbiter roots with one client. All current RTL and the unchanged parent
dependency were parsed in package-first order. The command exited zero in
2.76 seconds with empty stderr. Exact argv, current RTL source snapshots/hashes,
installed Icarus version, start/end times and raw output paths are retained at
`evidence/preparation/decoder-scalar-staging-elaboration-20261102T204024323384Z/receipt.json`.
No functional simulation, numerical comparison, mutation, synthesis, STA, fit
or physical-board experiment ran. This receipt is an advisory elaboration
diagnostic, not acceptance or a throughput/timing claim.

The decoder's evaluated tree still requires the public sequence controller and
verifier/atomic-engine connection. Ordinary HT2 priming must use the same engine
to publish its one-token KV before caching the computed next-token argmax;
speculative execution must preserve the prior prefix during cancellation.
The literal legacy core, host exclusion, mode latch, common Avalon arbitration,
new-sequence lifecycle and target FPGA/PCIe bridge remain to be implemented.
No ready handoff is claimed for the incomplete public product.
