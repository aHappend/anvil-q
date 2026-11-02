# HT2 implementation architecture

## Current increment

The only implemented block is `rtl/anvil_q3_ht2_sparse_dma.sv`. It does not
constitute an integrated accelerator. The parent RTL is read-only; tests and
FPGA integration are not authored by this increment.

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

## Full-product connection plan (not implemented)

`anvil_q3_ht2_top` will own mode-exclusive legacy and HT2 command dispatch.
The unchanged literal `legacy_core` retains parent behavior. HT2 scheduling
will process active candidates together by layer/projection, supply real
SwiGLU activation banks to sparse DMA, normalize resident qzero records to
local packed rows and provide natural-row FP16 scales to `tile_batch_mac`.
Qweight traffic and metadata traffic share the public DDR arbitration path.

The MAC requires four physical token banks, 128 lanes per bank, three-stage
shared weight decode, six-stage products/adders, eight stripe sums per output
and the fixed final tree. Surrounding parent scalar paths stay Q16.16; their
projection conversion boundaries must be implemented explicitly.

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
