# HT2 implementation architecture

## Current increment

Implemented sources comprise sparse DMA, the FP package, registered weight
decode/multiply/add helpers, Q16/FP boundary converters, the per-lane stripe
controller and the four-bank tile MAC. They do not constitute an integrated
accelerator. The parent RTL is read-only; tests and FPGA integration are not
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
The future integrated scheduler must provide sufficient buffering/prefetch
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
boundaries. They are authored but not yet connected to the batched scalar
scheduler; no parent/HT2 numerical equivalence is inferred from their existence.

## Full-product connection plan (integration not implemented)

`anvil_q3_ht2_top` will own mode-exclusive legacy and HT2 command dispatch.
The unchanged literal `legacy_core` retains parent behavior. HT2 scheduling
will process active candidates together by layer/projection, supply real
SwiGLU activation banks to sparse DMA, normalize resident qzero records to
local packed rows and provide natural-row FP16 scales to `tile_batch_mac`.
Qweight traffic and metadata traffic share the public DDR arbitration path.

The authored MAC provides four physical token banks, 128 lanes per bank,
three-stage shared weight decode, six-stage products/adders, eight stripe sums
per output and the fixed final tree. Surrounding parent scalar paths stay
Q16.16; the authored projection conversion helpers still need scheduler wiring.

Private scratch, causal `anvil_q3_ht2_tree_attention`, the batched decoder,
ordered vocabulary logits, `spec_verifier` and its literal KV commit engine
remain to be implemented. Commit visibility is one all-layer publication,
not a sequence of per-layer commits. Shadow placement and all image/scratch/KV
extents require production INT8/INT4 parameter validation.

## Integration dependencies and pending evidence

| Obligation | Guarantee needed from integration |
| --- | --- |
| Command epoch/layer ownership | Validate against current model and transaction before DMA command |
| Read returns | Ordered, one return per accepted burstcount-one request, with controller errors surfaced |
| Flush | Do not reset/reassign the DDR client until drain_done; no late return can acquire a new column |
| Reset | Reset enclosing read transport along with leaf ownership |
| Metadata | Image-loaded qzero/scales, tail-zeroed and AWQ-local-normalized consistently |
| Activation reuse | Retain/reuse scan storage across production row blocks without recomputing SwiGLU or DDR activation reads |
| Physical traffic accounting | Include qweight reads, all metadata, crossing lines, allocation padding and repeated addresses |
| FPGA | Actual HT2 top, Arria 10 device, 10.0-ns SDC, shared-DDR bridge and PCIe host mapping |

Cross-row-block scan reuse is not yet exposed by this fixed-interface DMA leaf;
the scheduler/storage design must resolve it without adding a host oracle or
weakening the required activation reuse. Static elaboration alone cannot
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
