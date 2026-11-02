# Anvil-Q3-HT architecture

## Implementation status

This document records implementation choices, not measured results. The integrated
RTL is implemented; independent functional, synthesis, timing and board acceptance
remain pending. See
`SPEC.md` for the frozen numerical, interface, cycle and acceptance contracts.

## Dataflow

Persistent DDR image -> ordered burst reader -> owned M20K tile slots ->
registered bank/lane operands -> sixteen MAC16 banks -> checked exact row
accumulators -> parent-compatible activation slots -> decoder operators.
Encoded KV groups use a separate tagged resident M20K cache with write-through
DDR backing and token-atomic visibility. The top directly contains
`token_controller`, `decoder_layer`, `ddr_arbiter`, `ddr_prefetcher`,
`tile_buffers`, `tensor_array`, `kv_hierarchy`, `host_loader`, `scratchpad`.
These names are connectivity requirements, not permission to add unused engines.

Each HT bank reduces sixteen **input** lanes for one output row. Replicating
sixteen banks produces 256 physically parallel lanes, not a single 256-lane sum.
At 100 MHz the analytical peak is 25.6 billion lane MAC/s; no measured utilization,
DSP mapping, target timing or speedup is implied.

The MAC16 has exactly nine globally enabled registered stages. Multiplication
is split across signed high and unsigned low activation halves; product
combination precedes four single-level binary reduction registers. Masked lanes
are zero before arithmetic and error checks. The leaf preserves exact Q32
products; there is no rounding at tile boundaries.

The operand metadata defaults to 160 bits, transported without interpretation
by MAC16. Integration allocation is bits 31:0 epoch, 63:32 layer, 66:64
projection, 98:67 output row, 130:99 input base, 133:131 row context,
134 first-input flag, 135 last-input flag, 159:136 reserved zero. Flags and
identity must move with validity, never be recovered from live commands.

Each bank uses the immutable parent's checked, eight-segment 128-bit adder.
The first implementation deliberately stalls a dependent row until the checked
sum commits, rather than forwarding an unchecked wide carry. Other banks
remain independent. Slots cannot be recycled until the last operand transfer.

## Saved implementation boundaries

The following sources are implemented but have not undergone independent
functional or synthesis verification:

| Source | Current boundary |
|---|---|
| `rtl/anvil_q3_ht_mac16.sv` | Nine-stage elastic exact sixteen-lane reduction, masked-scale checks and opaque metadata |
| `rtl/anvil_q3_ht_tensor_array.sv` | `banks[g].mac16`, eight-or-fewer checked row contexts per bank, held final row results |
| `rtl/anvil_q3_ht_ddr_prefetcher.sv` | Queued aligned read spans, 4 KiB splitting, reserved synchronous return FIFO, retained burst identities and cancellation drainage |
| `rtl/anvil_q3_ht_tile_buffers.sv` | Round-robin slot allocation, per-location fill ownership, seal/activate, sixteen synchronous lane subbanks per output bank |
| `rtl/anvil_q3_ht_host_loader.sv` | Idle host load/readback, write acceptance responses, persistent commit/readiness and zero-latency read alignment |
| `rtl/anvil_q3_ht_kv_codec.sv` | One-record Q16/INT8/INT4 encode/decode with exponent, padding, reserved-code and canonical-zero checks |
| `rtl/anvil_q3_ht_ddr_arbiter.sv` | Retained round-robin command ownership, ordered read-burst return routing and actual Avalon acceptance feedback |
| `rtl/anvil_q3_ht_ddr_record_port.sv` | Shared one-record transaction/completion storage with irrevocable offered commands and cancellation drainage |
| `rtl/anvil_q3_ht_image_map.sv` | Checked registered parent-kind/image translation, matrix bases/dimensions and parameter-region extent diagnostics |
| `rtl/anvil_q3_ht_scratchpad.sv` | Parent slot meanings, synchronous payload/validity RAM, arbitrary-order writes and unwritten-read errors |
| `rtl/anvil_q3_ht_scalar_adapter.sv` | Retained scalar-client arbitration, checked image access, packed FP16 extraction and one-line immutable-image reuse |
| `rtl/anvil_q3_ht_scratch_arbiter.sv` | Retained round-robin request and response ownership for the shared synchronous scratchpad |
| `rtl/anvil_q3_ht_kv_hierarchy.sv` | Full-token K/V write-through, validated resident records, deterministic replacement, DDR refill and bypass |
| `rtl/anvil_q3_ht_token_controller.sv` | Token/position/phase validation, decoder-layer sequencing, logit completion and cancellation/drain control |
| `rtl/anvil_q3_ht_projection.sv` | Packed matrix spans, bounded tile-local activation staging, ordered lookahead ownership, tensor metadata, checked bias and final-rounding scratch writeback |
| `rtl/anvil_q3_ht_attention.sv` | Parent fixed-point causal attention arithmetic with external HT KV commands and query-head-right-shift GQA mapping |
| `rtl/anvil_q3_ht_decoder_layer.sv` | Complete decoder sequencing, external seven-projection commands, parent normalization/RoPE/SwiGLU/residual operators |
| `rtl/anvil_q3_ht_scratch_backing.sv` | DDR spill data, per-word validity bitmaps, reset/sequence invalidation and retained transaction drainage |
| `rtl/anvil_q3_ht_top.sv` | Connected inference/host paths, five-client DDR arbitration, scratch arbitration, fault aggregation and public reset/backpressure gating |

The portable parent modules have been copied into `rtl/`, with only the
RMSNorm port-cast compatibility exception documented in `SPEC.md`. No changes
were made to `anvil_q3_reference/rtl/`. No verification sources have been authored
or modified by Designer.

The tensor boundary accepts independent per-bank `operand_valid/operand_ready`
streams containing q/z nibbles in natural lane order, sixteen FP16 scales,
sixteen signed Q16 activation words, mask and 160-bit metadata. AWQ packed-output
lane permutation belongs to the packed tile scheduler, not MAC input lane order.
The metadata row-context index must be below TILE_ROWS. First-input packets
start at input base zero; subsequent packets advance by sixteen. A busy context
cannot accept another packet until its exact sum commits. The last-input flag
returns the full 128-bit row sum, without bias or final rounding. The projection scheduler adds Q/K/V bias and performs the sole final rounding
before successful scratch writeback.

The tile boundary allocates a slot with an entry count and immutable owner
metadata. Each entry must receive one write for every bank, including explicitly
zero-masked inactive banks. Duplicate writes and premature seals fault. Each
bank write carries sixteen q/z/scales/masks and the corresponding sixteen
activation words. Activations are stored once per entry on bank-zero writes
and broadcast from sixteen separate synchronous subbanks on consumption.
Seal may coincide with the final
successful write. Activation requires matching metadata. Registered reads
produce entries in order and hold under operand backpressure; the final transfer
alone releases the slot. Integration must derive row/input packet metadata from
the retained slot owner and entry index, not change that owner while filling.
Malformed allocation/write/seal/activation commands are acknowledged and fault,
not silently retried as successful commands.

The DDR reader accepts `cmd_address`, a positive `cmd_beats` span and metadata.
Its `data_last` marks the final beat of the entire span, not every split burst.
Responses reserve FIFO credit before the Avalon command is offered; credit is
released only on output transfer or explicit cancellation discard. The read-only
interface belongs behind the final DDR arbiter. A protocol/response fault
terminates the stream through sticky `fault`; consumers must not wait for an
error-marked beat after that fault. Flush clears queued unissued work and buffered
results but preserves an offered command and accepted reads until drained.
`drain_done` describes empty protocol ownership even while flush is held.

The host loader's memory request acceptance must correspond to **actual Avalon
acceptance**, not merely admission into an arbiter's private queue. Its single
outstanding read has a reserved response register. Writes are one beat. The final
arbiter must route read returns only to the client owning the retained accepted
descriptor; an unexpected loader return raises sticky fault. No token execution
may overlap a host operation. Commit can coexist with a retained completed host
response; a simultaneous accepted host write invalidates readiness.

The KV codec's Mode 0 record holds sixteen uncompressed words; Mode 1 holds
32 codes and Mode 2 64. `count` is the number of actual elements in the record,
not a byte count. Both unused words/codes and compressed padding must be zero on
decode. Results and errors hold until `out_ready`; flush wins over input and
output transfers. The resident hierarchy connects this codec to its backing
record port and scratch-read interface, and the attention engine calls its
commit/read boundary directly.

The DDR arbiter registers both the selected client and every offered command
field. `c_req_ready` means actual platform acceptance, not selection or internal
buffer admission. It retains a separate ordered owner/remaining-beat queue for
reads and routes every return, including a return on the acceptance edge, to that
owner. Read reservations are the requesting client's responsibility: the burst
reader reserves its FIFO and the record/host ports reserve their completion
registers before offering requests. The arbiter supports 1..16-beat reads and
single-beat writes. Host and KV writes deliberately use burstcount one; the
design never offers a multibeat write with incomplete beat-acceptance handling.
A malformed internal request raises sticky fault and is not sent to DDR.
Flush does not retract a command already offered or destroy accepted read owners.

The shared record port admits one aligned 64-byte operation, offers it until
actual acceptance, and reserves its held completion independently of downstream
ready. Writes complete on acceptance; reads complete on their return. Flush
poisons completion visibility but preserves an offered command and accepted
read. No new operation is admitted until poisoned ownership drains. Unexpected
returns raise a sticky fault. This port is shared as a module definition, not as
a single resource: the KV hierarchy and scalar adapter each instantiate one and
arbitrate their external requests through the final DDR arbiter.

The scalar adapter translates parent logical kinds 0..8 and 11. Image accesses
are read-only; kind 8 selects scratch rather than DDR. Packed qweight/zero
requests use word-row indices and input/group columns; scales use output rows
and group columns. Matrix bases/dimensions are also returned by the image map
for the packed scheduler. Legacy KV kinds 9/10/12..15 are not silently
translated to the changed compressed layout: attention must call the HT
hierarchy directly. Its one-line read cache reuses FP16 embedding/gamma/bias
neighbors and RoPE words; top integration must invalidate this cache on accepted
host writes and prohibit host/inference overlap. This adapter is for parent
nonprojection operators, not a scalar replacement for the HT tensor path.

The scratch arbiter holds its selected request while the scratchpad initializes
or stalls, then retains response ownership through the final transfer. Scratch
payload and one-bit validity RAMs use synchronous non-reset processes. Reset or
sequence flush starts a validity-only sweep with requests blocked; data RAM is
never reset. No unwritten payload can become a successful response. Production
storage and exact slot extents are in `SPEC.md`.

The KV command boundary retains parent meanings: op 0 commits all current K/V
scratch values for one layer/position; op 1/2 reads a K/V component. `cmd_epoch`
tags sequence ownership; `cmd_bypass` explicitly skips resident lookup/allocation
without changing encoded DDR semantics. Commit reads and encodes every group,
accepts all write-through records, and only then advances the layer's committed
position counter. Reads reject uncommitted positions and wrong epochs. Resident
tags and encoded records are synchronous M20K arrays, searched one entry per
registered read/comparison pair, with separately reset validity. Misses refill
through DDR; hits issue no backing read. Successful decoding precedes miss
installation. Round-robin replacement explicitly wraps for all legal residency
counts, including 1 and 3. Partial groups pass their actual element counts to
the codec. Address generation is registered across position, head and record
steps and checks the full 33-bit backing extent before truncation. Flush clears
visibility/cache ownership, preserves the persistent image and drains offered
or accepted DDR operations before permitting restart.

The token-controller leaf exposes commands to the real decoder, final norm and
embedding/logit engines, rather than computing surrogate logits. It retains the
parent sequence/phase rules and issues every layer in order. The top gates
`run_enable` with calibrated committed-image readiness and host exclusion, and
derives `last_logit_transfer` from the actual last ready/valid transfer. Its
separate `core_flush` and `memory_flush` distinguish suppression of stale
arithmetic from irrevocable external-memory drainage.

## Integrated projection and decoder

The decoder issues Q, K, V, O and the MLP's gate/up/down commands to one external
projection scheduler. No legacy GEMV instance exists on the HT inference path.
The immutable parent top remains separate compatibility support. Parent
normalization, RoPE, residual, SwiGLU, embedding and tied-head operators retain
their public scalar protocol, translated by the scalar adapter; they do not
request projection weights during HT inference.

The scheduler visits output blocks of BANKS*TILE_ROWS rows, then input tiles
within each block. Entries are context-major with TILE_K/16 packets per context.
A bank's output row is block_base + context*BANKS + bank. Input-tail packets and
output-tail banks are masked explicitly; entirely padded packets retire their
tile entries without creating tensor contexts or results. The original AWQ
output packing permutation is applied while materializing a tile, not while
reducing its sixteen input lanes.

For each tile, group zeros and scales are fetched once per intersected AWQ
group and reused across input lanes and row contexts. Each packed input-major
qweight row span covers the block's output words, not one nibble per command.
Alignment may introduce unused physical bytes, which benchmark traffic accounting
must retain. The prefetcher splits each aligned span at its configured burst
limit and 4 KiB boundaries. One span at a time feeds bounded raw staging;
this is not a claim that every projection command fills four DDR read credits.
The standalone burst engine supports those credits for queued long spans.

The raw staging is bounded by TILE_K and the output block, independent of full
projection dimensions. Sixteen packed-weight RAM subbanks allow a registered
read of all input lanes. Two group-record RAM copies serve the two possible
Group-8 identities in one sixteen-lane packet. Activations are loaded from
scratch into TILE_K words of staging and copied into the owned tile entries;
consumption never reads a newer tile's activation staging. Tile ownership
includes epoch, layer, projection, block row and input base. A retained queue
activates sealed slots in allocation order. Default slot rotation 0/1/2/3 gives
two ping-pong pairs; explicit wrapping also supports three slots.

Fill and consumption are independent. An available slot may be filled while
another slot supplies tensor operands. Per-bank transfer bits prevent duplicate
MAC acceptance when banks stall independently. An entry transfers from tile
storage only after every active bank accepts it. The final entry transfer alone
releases slot ownership. The result writer arbitrates bank completions,
validates identity, adds bias using the checked segmented adder, rounds once,
and waits for the actual scratch response before counting an output row.
Completion requires all output rows, empty tile ownership, idle tensor and
prefetch engines, and a settled result writer.

The final DDR arbiter has five clients: host loader, read prefetcher, scalar
immutable-image adapter, KV record transport and scratch spill transport.
The scratch arbiter has scalar-adapter and KV-commit clients. Host requests
take admission priority over tokens; inference is blocked through the host's
held response. Host writes invalidate both model readiness and the scalar
read cache. Core cancellation suppresses arithmetic immediately, while the
separate memory flush poisons retained transports. The arbiter continues
servicing irrevocable offered commands and accepted read ownership until drain.
Sequence invalidation clears KV visibility and scratch validity, not DDR weights.

## Bounded activation storage

At production dimensions all 54,016 scratch words reside on chip. The resident
prefix is capped at 65,536 words for larger legal geometries; remaining words
spill into the reserved DDR scratch region. Data word i is at
0xc0000000 + 4*i. The last 32 MiB of the reservation, starting at 0xfe000000,
holds one 512-bit validity bitmap for every 512 spilled words. Bitmap j is at
0xfe000000 + 64*j, with bit `(i-65536)&511` identifying the word.
Extent guards reject overlap of data and bitmap reservations.

Reset and sequence invalidation sweep only resident validity bits and spilled
validity records. DDR payload is not cleared. Access remains blocked until both
sweeps finish, so a reset cannot reuse an old bitmap generation. Spilled writes
first accept the four-byte-enabled data write, then update the retained bitmap;
only successful bitmap completion produces the scratch response. Spilled reads
check the bitmap before requesting payload. Flush drains an offered/accepted
transaction before restarting the bitmap sweep. This supports arbitrary-order
writes and rejects unwritten reads without a model-sized on-chip validity array.
DDR calibration gates spill initialization.

## Independent handoff

Designer may run only a fast static elaboration, not functional simulation,
numerical sample harnesses, synthesis, timing or physical probes. The independent
Verifier must author and run all admitted L1 checks immediately after a complete
design handoff; none are waived by this partial implementation.

Static Icarus elaboration of the integrated default HT top and the separate
parent-compatible top exited zero. Its exact command, RTL/design hashes,
tool-version output, raw logs and exit are in
`evidence/preparation/static-elaboration-20261102T142134144202Z/receipt.json`.
At that check, all 26 portable parent copies were byte-identical to their
immutable references. That historical receipt predates the RMSNorm repair below
and does not certify the repaired sources. The earlier leaf-only diagnostic remains retained at
`evidence/preparation/static-elaboration-20261102T140621457716Z/receipt.json`.
No functional simulation, synthesis, timing or hardware experiment ran. These
advisory syntax results do not establish numerical or integrated correctness
and do not satisfy any mandatory acceptance check.

### RMSNorm frontend compatibility repair

The independent integrated synthesis failure is retained at
`evidence/preparation/synthesis-20261102T143051280155Z/receipt.json`.
The same Yosys 0.33 signedness assertion was reproduced on the immutable parent at
`evidence/preparation/frontend-20261102T143230494780Z/receipt.json`.
The isolated both-port-casts case at
`evidence/preparation/frontend-variants-20261102T143538583898Z/receipt.json`
passed frontend elaboration; either single-cast removal failed. That receipt's
overall status remains failed because it also records the failing variants.

The delivered RMSNorm now removes only those two redundant port casts, preserving
all 128 transferred bits and leaving arithmetic, state, latency and interfaces
unchanged. No new functional or synthesis experiment is claimed for this repair.
Independent Verifier must run fresh repair-linked numerical and full synthesis
checks, implement the eight mandatory self-contained `--suite` entrypoints
(the existing `--probe` diagnostics do not implement them), and preserve all
coverage thresholds. Timing and physical-board gates remain pending.

## Ownership and memory boundaries

Tile slot states are EMPTY, FILLING, READY, ACTIVE. Default slots 0/1 and 2/3 are
two ping-pong pairs. Round-robin allocation includes slot 2 when TILE_SLOTS=3.
Reservation records epoch/layer/projection/output/input identity. Packed DDR
reads are retained by accepted burst descriptor, not by a changing producer.
The burst reader reserves all return storage before command issue, supports four
outstanding bursts by default, splits at 4 KiB, handles gaps, and permits
zero-latency response on the same edge as command acceptance. Cancellation
retains an already offered stalled Avalon command; it drains accepted traffic
but suppresses poisoned results. Reset requires platform-consistent drainage
because Avalon has no response transaction identifier across reset.

M20K arrays must use dedicated non-reset synchronous read/write processes.
Validity, owner state and pointers reset separately. No reset writes sweep
weight or cache storage. A read operand holds under backpressure, including when
the following pipeline's global elastic enable is low.

| Producer guarantee | Consumer dependency |
|---|---|
| Host drains writes before commit | Token controller never starts from an uncommitted image |
| DDR reader reserves complete burst capacity | No unbackpressurable return is dropped |
| Packed scheduler retains accepted identity | Tile data never depends on live commands |
| Tile slot remains owned through last transfer | MAC operands cannot observe overwritten RAM |
| MAC freezes data/error/identity together | Accumulator associates each exact sum with its row |
| Accumulator checks signed overflow | No success-shaped saturated result hides an accumulation fault |
| KV commits complete K/V before visibility | Attention cannot read partially written token state |
| Token cancellation drains memory ownership | A restarted token cannot receive stale data |

## Delivery boundaries

Keep all immutable parent source names available under `rtl/` for the reusable
parent-compatible `anvil_q3_top`. HT changes use `anvil_q3_ht_*` names, never
change the parent BANKS legality, and never depend on private paths.
Verification imports no agent/runtime state. Its portable source set is
`rtl/*.sv`, `design/*.md`, `tests/*.py` plus explicitly declared
`anvil_q3_reference/rtl/*.sv` differential inputs.

Image address/extent formulas, analytical default component totals, byte
aperture, host protocol, benchmark baseline mapping, byte-accounted service model
and reproduction commands are in `SPEC.md`. The image-map leaf checks image extents; the top uses that map and the
independently authored importer must use the same ABI.
Analytical totals do not establish readback coverage. Missing official assets prevent
official-image claims, not synthetic verification or design progress.
