# Anvil-Q1-HT v2.0.0-ht-ddr4

## Authority and implementation status

The admitted work order is the acceptance contract. This document records its
design-facing interfaces and the implementation increments; it does not waive
any acceptance requirement. The immutable compatibility source is
`anvil_q1_reference/rtl/`. It is not verification evidence.

Current increments implement the tensor primitive, parameter/reset logic,
dual-clock ping-pong tile storage, burst DMA, preload writes, sequential
arithmetic, AWQ/BF16 conversion, nonlinear and decoder numerical kernels,
a tagged stationary KV window with a response-checked logical spill interface,
descriptor/CSR control, a panel-streaming parallel projection controller and
complete decoder orchestration. Scalar DDR transport, logical address translation,
on-chip scratch/KV routing and transaction/Avalon arbiters are also saved.
The integrated top now connects these paths, including exclusive upload grants,
KV spill traffic, coherent counter snapshots and compute-only fault recovery.
A separate parent-compatible entry and target QSF/SDC are supplied. This
describes implemented source, not a verified inference or board result.
No inference, performance, timing, synthesis, resource
fit or model-accuracy result is claimed. Verification belongs to the independent
Verifier; `tests/*.py` is not Designer-owned.

## Fixed structure and supported dimensions

Target: Intel Arria 10 GX `10AX115N2F45E1SG`. Compute clock is at least 100 MHz,
initially constrained to 10.000 ns. The EMIF application clock is independently
constrained to 3.750 ns, subject to confirmation by the actual board adapter.
The fixed structure is 64 lanes, eight banks of eight lanes, 512 DDR data bits
and four AWQ bits. Defaults are 24 layers, hidden size 896, intermediate size
4864, 14 query heads, two KV heads, head dimension 64, group size 128, vocabulary
151936 and maximum sequence length 32768.

Supported dimensions are positive subsets of these maxima. Hidden size equals
query-head count times head dimension. Head dimension is even; query-head count
is divisible by KV-head count. Hidden, intermediate and KV widths are multiples
of eight. Group size divides hidden and intermediate sizes. Tile depth is any
integer 1..256; KV window is any integer 1..128 not greater than maximum sequence
length. Non-power-of-two sizes require explicit terminal-count wraps.
Illegal configurations must reach an explicit `PARAMETER ERROR` diagnostic
without malformed array/select elaboration first. The top passes a complete
safe diagnostic-only tuple to dependent instances for an illegal configuration;
its public outputs remain reset and its validator emits the explicit error.

## Numerical contract

Activations and logits are signed Q16.16 int32. AWQ uses unsigned qweight and
qzero nibbles, with no zero-point-plus-one adjustment. Logical lanes 0..7 have
packed-word bit shifts `[0,16,4,20,8,24,12,28]`. Finite, nonnegative FP16 scales
(negative zero permitted) convert to unsigned Q16 magnitude. The exact signed
37-bit dequantized weight is `(qweight-qzero)*scale`. The signed product is 69
bits; dot accumulation is exact signed 128 bits. Round right shifts to nearest
magnitude, ties away from zero, then saturate at the specified output boundary.
Q/K/V bias is added as `bias_q16 << 16` before final round-by-16, never to an
already rounded tensor output.

Embedding, bias and normalization gamma use the parent's FP16 conversion,
including subnormals, signed zero and saturation; exponent-all-ones values are
errors. BF16 projections convert finite BF16 to saturated Q16.16, with the same
rounding rule, and then use the same fixed-point operations. BF16 is not FP16
reinterpretation. BF16 NaN/Inf are errors. Projection modes do not change the
parent's FP16 embedding/bias/gamma storage.

The numerical kernel controller implements the parent's RMSNorm, RoPE, attention,
exponential and SiLU widths, truncation points and operation ordering. RMSNorm
uses a 96-bit sum, floor division of `(sum << 32)` by hidden size, epsilon
18446744073710, integer square root, floor reciprocal `2^64/denominator` and
final round-by-48. Attention preserves rounded division, the six-term exponential
recurrence and its truncation-toward-zero division and cutoff. RoPE uses Q2.30
tables and round-by-30. These implementations still require independent parity
checks; their existence is not evidence that parity or timing has been achieved.
Fixed-point parity is not a claim of IEEE floating-point Qwen equivalence.

## Cycle & Degenerate-Boundary Table

All transfers use values immediately before a rising edge. Observations below
mean immediately after that edge's nonblocking updates.

| Boundary | Required behavior |
| --- | --- |
| Reset asserted | Public outputs are zero; no transfer is accepted. Memories need not reset, but validity and ownership do. |
| Reset release | Each domain uses a two-flop asynchronous-assert/synchronous-release reset synchronizer. Domain readiness is permitted only after local release. |
| Tensor input edge E | Accept iff pre-edge `in_valid && in_ready`; the first accepted beat requires `in_first`. |
| Single-beat dot | Both `in_first` and `in_last` on the same accepted beat are legal. |
| Open dot | One vector per cycle may be accepted. Mask is constant; another `in_first` is illegal. |
| Last tensor input E | Four product-latency edges; exact carry-save accumulation at E+4. |
| Tensor finalization | Resolve 32-bit carry chunks at E+5..E+8, round at E+9, publish at E+10. |
| Tensor stall | Output valid, data and mask hold until accepted. No following dot is accepted before the current result transfers. |
| AWQ/BF16 row accepted at P | Capture the packet and synchronously read its activation using the pre-edge input index; advance that index only on packet acceptance. |
| Projection conversion without stalls | At P+1 capture lane conversion/difference and activation/boundary metadata; at P+2 register products and matching metadata. The tensor can accept them at P+3. Following rows may enter on consecutive edges. |
| Projection feed stall | The row buffer and both dequantizer stages retain their respective payloads and metadata. Simultaneous retirement/refill uses the old stage payload for retirement. |
| Projection group end, including group size 1 | Stop accepting packets after the last group row; reload zeros/scales only after that row transfers to the tensor and its block settles. Single-row first/final flags travel with the row. |
| Tensor violation | Sticky `protocol_error`, no successful result until reset. The illegal accepted beat never enters the arithmetic pipeline. |
| Tile depth 1 | One beat may be a complete tile. Full ownership is published only after its final accepted write. |
| Tile depth 3/other nonpowers | Compare against the explicit final index; never mask a binary counter to wrap. |
| Tile read edge R | Accepted address yields registered data after R+1. |
| KV read edge K | A tagged resident hit yields data after K+2. |
| KV accepted write | Response follows the committed SRAM write; a colliding old slot is not modified until every spill write has acknowledged successfully. |
| KV depth 1 | Eviction must finish before replacing the sole position; layer/head/position tags still distinguish entries. |
| KV clear | Requests are blocked while one slot per cycle is invalidated. An idle `new_sequence` initiates this clear; it does not touch model storage. |
| New sequence | Invalidate history/tags, not DDR weights. Drain active transactions before reuse. |
| Avalon issue+response | Capture a response on the same edge as command acceptance, as well as consecutive response edges. |
| Reset with traffic | External EMIF transaction source must also quiesce/reset; stale pre-reset responses cannot enter a new epoch. |
| Final logit stalled | No completion until final output transfer. Index/data remain fixed. |
| Final logit accepted F | `done=1,error=0` after F for exactly one compute cycle. |
| Invalid token/order | No logits; one error completion within two compute edges of acceptance. Preserve sequence validity, next position and cache history, including when a rejected command asserts `new_sequence`. An independent execution fault still invalidates continuation. |
| Simultaneous error/result | Error takes priority; no successful completion or newly published result. |
| Execution fault in any active decoder state | Latch failure and invalidate continuation; suppress new requests/commands and logits. Retain an accepted embedding response or active child ownership until it drains, then emit one error completion. A fault before acceptance completes without waiting for an unissued transaction. |
| Descriptor install | Scan all existing regions before atomically replacing the selected entry; exclude that entry's old region from overlap comparisons. |
| Descriptor commit | Scan all required identities and exact padded lengths before setting image validity or responding. |
| CSR accepted at E | Ordinary read/write response becomes valid after E+1 and holds until a later accepted response edge. Install/commit wait for all validation. |
| CSR fault plus clear | A new fault wins over clearing the sticky error. Clearing an existing load fault also requests its acknowledged DDR-domain clear. |
| Upload vs token/CSR | Compute grants exclusive upload ownership before DDR can assert load-ready; CSR activity wins over a grant and token start. |
| Upload last beat | Its accepted write response, not load-last acceptance, releases ownership. No next upload beat can transfer during the completion pulse. |

## Numerical kernel integration interface

`anvil_q1_ht_kernel` uses the parent's logical memory request/response fields
and accepts one command at a time. `cmd_op` is 0=first RMSNorm, 1=second
RMSNorm, 2=final RMSNorm, 3=RoPE, 4=first residual, 5=second residual,
6=SiLU-times-up, 7=GQA attention (including K/V insertion).
Layer and position are checked on command acceptance. `done` is one cycle;
`error` qualifies it. A memory or arithmetic error terminates that command
without further writes. The parent activation-slot meanings are retained:

| Slot | Meaning |
| --- | --- |
| 0 | Layer input / second residual output |
| 1 | First normalized input |
| 2,3,4 | Q, K, V projections |
| 5 | Attention output |
| 6 | Output projection |
| 7 | First residual output |
| 8 | Second normalized input |
| 9,10,11 | Gate, up, SiLU(gate)*up |
| 12 | Down projection |
| 13 | Reserved scratch slot |
| 14 | Final normalized input to tied vocabulary projection |

The kernel's sequential math service resolves additions and negations in
32-bit chunks and multiplies using registered 16x16 partial products with
chunked accumulation. This slow shared service is for nonlinear/norm/attention
operations, not a replacement for the required parallel GEMV array.
Division distinguishes unsigned floor, signed truncation and signed
nearest-magnitude ties-away rounding. Operations have held ready/valid results.
An invalid opcode or zero divisor returns an explicit error.

`anvil_q1_ht_dequant` converts one accepted lane at a time, with a registered
conversion/difference stage followed by a registered product. Its `in_value`
contains FP16 scale in AWQ mode or BF16 weight in BF16 mode. An erroneous input
returns `out_error`, never a valid zero-weight substitute.
Both stages are elastic: independent valid bits allow one new lane value per
cycle when downstream service permits, while result data/error hold during
backpressure. This does not change conversion widths or rounding.

## Descriptor tensor layout

All entries are little-endian. All final lengths round up to 64 bytes; bases
must be 64-byte aligned. Projection and embedding storage use the panel-major
physical layout below. This is an initial-upload permutation, not a change to
the parent logical tensor identity or an authorization for per-token repacking.
The independently owned fixture/repacking implementation must check the
permutation bijectively against the actual checkpoint and record it in its
descriptor manifest. That implementation and its provenance are still pending.

Let `I` be the projection input count, `O` its output count, `G=I/GROUP_SIZE`,
`K=NUM_KV_HEADS*HEAD_DIM`, and `S=max(HIDDEN_SIZE,INTERMEDIATE_SIZE)`.
Projection IDs 0..6 are Q, K, V, O, gate, up and down. Q/O have
`I=HIDDEN_SIZE,O=HIDDEN_SIZE`; K/V have `I=HIDDEN_SIZE,O=K`; gate/up have
`I=HIDDEN_SIZE,O=INTERMEDIATE_SIZE`; down has
`I=INTERMEDIATE_SIZE,O=HIDDEN_SIZE`. Index multiplication in this table is
host/ABI notation, not permission for a long single-cycle RTL datapath.

| Kind | Identities | Shape and byte offset |
| --- | --- | --- |
| 0 | Global layer0, proj0 | Logical FP16 embedding `[VOCAB_SIZE,HIDDEN_SIZE]`; physical panels group up to64 vocabulary rows, then hidden column, then vocabulary lane; tied projection uses this same tensor |
| 1 AWQ | Every layer, proj0..6 | Logical uint32 qweight `[I,O/8]`; physical output panel, input row, packed word; the eight physical nibbles in each word are unchanged |
| 2 AWQ | Every layer, proj0..6 | Logical uint32 qzero `[G,O/8]`; physical output panel, group row, packed word; same packed lane order |
| 3 AWQ | Every layer, proj0..6 | Logical FP16 scale `[G,O]`; physical output panel, group row, output lane |
| 1 BF16 | Every layer, proj0..6 | Logical BF16 `[I,O]`; physical output panel, input row, output lane; kinds2/3 must be absent |
| 4 | Every layer, proj0..2 | FP16 bias `[O]`, `2*col` |
| 5,6 | Every layer, proj0 | FP16 first/second norm gamma `[HIDDEN_SIZE]`, `2*col` |
| 7 | Global layer0, proj0 | FP16 final gamma `[HIDDEN_SIZE]`, `2*col` |
| 8 | Global layer0, proj0 | int32 scratch `[15,S]`, `4*(row*S+col)`; reserved slot13 has the same stride |
| 9,10 | Every layer, proj0 | int32 K/V backing `[MAX_SEQ_LEN,K]`, `4*(position*K+head*HEAD_DIM+dim)` |
| 11 | Global layer0, proj0 | int32 Q2.30 RoPE `[MAX_SEQ_LEN,HEAD_DIM]`, `4*(position*HEAD_DIM+2*pair+sin_select)` |

For a matrix with logical output column `c`, let `b=64*floor(c/64)` and
`w=min(64,O-b)`. Its panel begins at element `b*R`, where `R` is `I` for
weights and `G` for quantization metadata. A dense16 entry has byte offset
`2*(b*R + row*w + c-b)`. An AWQ packed word at logical word column `j`
uses `b=64*floor(j/8)` and byte offset
`4*((b/8)*R + row*(w/8) + j-(b/8))`. Scales use the dense16 formula.
There is no padding between panels or rows, including a short last panel.
Only the descriptor's final64-byte padding is present.

For embedding logical `(token,hidden_column)`, use the dense16 formula with
`c=token`, `row=hidden_column`, `O=VOCAB_SIZE`, `R=HIDDEN_SIZE`.
Thus both embedding lookup and the tied vocabulary projection address the same
FP16 values, without maintaining a second, possibly divergent model copy.
Division/floor notation here specifies the host ABI; hardware uses shifts,
explicit group counters and registered products, not runtime division.

Kind8 retains its declared nonoverlapping DDR reservation, but the HT logical
bridge serves all15 activation slots from a synchronous on-chip M20K shadow.
Its contents are not implicitly initialized from uploaded scratch bytes.
The decoder writes every activation before use. Kinds9/10 are separate DDR
backing stores reached only through the tagged KV window's cold/eviction path.

Descriptor entry identity is implicit in its index. Staging writes at
0x0014..0x0028 do not change an installed entry. Install verifies that staging
identity equals the selected index, required length, bounds and all overlaps
before replacement. A zero LENGTH_BYTES removes an otherwise legal selected
identity; a subsequent commit still rejects any missing required tensor.
This permits explicit removal of AWQ kinds2/3 when changing to BF16 mode.
Reads of the six descriptor fields return the selected **installed** entry,
not staging registers, and error when it is absent. The CSR index itself can
be read even if the selected entry is absent.

Changing mode or successfully installing/removing a descriptor invalidates
the image. Invalid operations leave existing descriptors, mode and image state
unchanged, apart from recording a sticky error and an error response.
Commit sequentially scans the complete model set; successful install already
enforces pairwise nonoverlap as a table invariant. All metadata mutations
reject engine/load busy conflicts. Lookup has a separate held response.
The top excludes token and upload starts during configuration validation and
arbitrates same-edge mutation/start requests. A granted upload invalidates the
image before writes become possible. Acknowledged mailbox messages synchronize
ownership, completion/error and load-error clear. A separate mailbox transfers
coherent DDR-beat counter snapshots; no multibit asynchronous counter is sampled.

## Stationary KV interface and history

`anvil_q1_ht_kv_window` accepts layer, head, position, dimension, K/V selection
and a signed word. SRAM addresses partition both layer and head. Position
tags and per-K/V-word validity are checked before returning any resident data.
A constant, synchronous position-to-slot ROM is initialized with an explicit
0..KV_WINDOW-1 wrap counter, including non-power-of-two windows; no runtime
division or modulo selects the ring index.

K and V words for the next position in each layer may be written in any order,
but the entire K/V row must finish before that layer starts another position.
History advances only on that complete row. Historical writes are rejected;
the decoder only inserts the current position. Reads may select any completed
causal row or an already valid word of the current row. Unwritten words and
out-of-range requests report errors rather than successful zeros.

A tag collision spills every K and V word of the old complete row through
the `spill_*` logical interface, waiting for each write response. Only after
the final success may the first replacement word be installed. A cold read
uses that interface without pretending to be a resident hit or changing the
window. Spill requests hold while stalled and accept coincident command
acceptance/response. A fault preserves the un-replaced old slot, reports an
error response and quiesces requests until an idle new-sequence clear or reset.
The top/DDR bridge connects this interface exclusively to separate descriptor
kinds9/10 through the scalar address/DDR path. Its numerical/protocol behavior,
including cold full-context retrieval, still requires independent verification.

## Tensor primitive

`anvil_q1_ht_tensor_array` has exactly these ports:

| Direction | Name | Width/meaning |
| --- | --- | --- |
| input | `clk`, `rst_n` | Compute clock and active-low reset |
| input/output | `in_valid`, `in_ready` | Input handshake |
| input | `in_first`, `in_last` | Dot boundaries |
| input | `in_activation` | signed 32 |
| input | `in_weight_q16` | 2368, lane i signed 37 at `[37*i+:37]` |
| input | `in_mask` | 64, constant within a dot |
| output/input | `out_valid`, `out_ready` | Held output handshake |
| output | `out_data` | 2048, lane i signed 32 at `[32*i+:32]` |
| output | `out_mask` | 64, zeroed masked outputs |
| output | `protocol_error` | Sticky until reset |

Literal hierarchy is `g_bank[0..7].g_lane[0..7].u_mac`, with
`anvil_q1_ht_mac_lane` at each leaf. Bias integration uses an extra final
accepted vector with activation 65536 and each lane's signed Q16 bias as its
weight. This adds exactly `bias << 16` to the full accumulator before rounding;
it does not reconstruct precision from rounded outputs.

## Parallel projection and decoder boundaries

`anvil_q1_ht_projection` accepts projection IDs0..6 with the parent meanings,
plus internal ID7 for tied vocabulary logits. It first reads the complete input
activation vector into synchronous M20K storage. For each up-to64-output panel
it loads group zeros/scales once, streams contiguous packed matrix rows through
the actual ping-pong banks, dequantizes all64 lanes in parallel, and submits
vectors to the tensor primitive. AWQ group transitions preserve the open exact
dot product; group metadata reloads never round a partial accumulation.
Packet acceptance, synchronous activation fetch, dequantization and tensor
submission overlap for AWQ/BF16 rows. First/final/group-end flags and activations
advance with the corresponding weights, not with the next packet's index.
BF16 and tied FP16 projections stream a whole panel without AWQ metadata.
Q/K/V bias is a final exact synthetic tensor product before the one rounding
boundary. Tail masks suppress both invalid padding checks and unused outputs.
Projection results write the parent activation slots; internal ID7 emits
ordered vocabulary logits with stable index/data under backpressure.

`anvil_q1_ht_weight_stream` looks up the descriptor, checks the extended range,
aligns the DDR request down to64 bytes and discards its initial byte offset.
A bounded192-byte reservoir joins512-bit tile reads into packets of at most
128 bytes. Packets never straddle an ownership boundary without first copying
the required bytes into the reservoir. The DMA completion carries its count
of successfully published tiles; an error drains exactly those tiles and
waits for the completion before reporting failure. Neither a guessed CDC delay
nor an empty-tile observation substitutes for the returned ownership count.

The decoder dispatches, in order: first RMSNorm; Q/K/V; RoPE; full causal GQA;
O; first residual; second RMSNorm; gate/up; SiLU product; down; second residual.
After the last layer it dispatches final RMSNorm and tied vocabulary projection.
A successful final-logit transfer drives the decoder completion on that same
edge, rather than waiting for a later projection-controller idle state.
Invalid input commands leave the previous successful position available for
retry; an internal execution fault invalidates sequence continuation.
A valid `new_sequence` command clears KV metadata before the first embedding
read and leaves the image and mode untouched.

The scalar address bridge checks logical shapes as well as descriptor bounds.
Its registered panel/row products precede address issue; aligned one-beat reads
extract exactly one16/32-bit little-endian entry. Runtime backing writes use
four byte enables at their addressed word; no read-modify-write is used.
The scalar transport checks both read and write responses and captures a
response coincident with command acceptance. Held request/response CDC mailboxes
carry full payloads. The Avalon arbiter retains command ownership through
waitrequest, then response ownership through the complete read burst or write
response; its arbitration never invents a read-data-ready signal.

## Integrated public contract

The top must be `anvil_q1_ht_top`, with `u_dma`, `u_tiles`, `u_tensor`, `u_kv`
and `u_decoder`. It must execute the full parent decoder sequence and use the
parallel engine for real projections. A separately elaboratable parent
`anvil_q1_top` interface must be preserved without altering the immutable source.
No per-token host weight port is permitted on the HT path.

DDR uses addressed, aligned 64-byte load writes with byte enables and write
responses, plus 1..16-beat reads that split at 4 KiB and the 8 GiB boundary.
One read burst and one write response may be outstanding; reserve all burst
capacity before issue. No Avalon read-data-ready signal exists. Upload and
inference are mutually exclusive. Payload is held during waitrequest.

The CSR map is version 0x0000, status 0x0004, control 0x0008, mode 0x000c,
descriptor index 0x0010, six descriptor words 0x0014..0x0028, install 0x002c,
and token-cycle/read-beat counters 0x0030..0x003c. Version is 0x02000001.
Exactly one transaction may be outstanding; responses must hold under stall.
Install and commit acknowledge only after full validation. Descriptor index is
`(((layer*12)+kind)*8)+proj`. Reject undefined/reserved fields, missing tensors,
overlaps, unaligned regions, overflow and mutations while busy. Commit requires
all preload responses and complete model validation. Invalid writes are atomic.

All weights remain DDR-resident across tokens and soft new sequences. Two
dual-clock M20K tile banks require explicit FREE/FILL/FULL/COMPUTE ownership.
The KV default window is 128 positions per layer with tagged K/V data and
lossless local-DDR spill, retaining full causal context up to 32768 positions.
The window data alone totals 3145728 bytes at default dimensions. Ring-index
equality never establishes a hit without matching tags.

## Acceptance and evidence boundary

The mandatory independent L1 matrix, deliberate mutations, full-default
synthesis and clean-directory reproduction remain required. Native timing
lint, Quartus 17.1 STA/device fit and physical-board checks remain mandatory.
The five project-standardized domains are DDR residency, tensor GEMV, resident
and spilled attention, decoder kernels/layers, and full-model ordered logits.
The exact BF16/AWQ checkpoint/tokenizer identities must be pinned and validated.
Reduced parameter tests do not establish full-model acceptance.

At 100 MHz the 512-bit consumer peak is 6.4 GB/s. At 266.666667 MHz the raw
DDR interface peak is 17.066667 GB/s. Measured DDR service and compute-consumed
bandwidth must be reported separately. No measured throughput exists yet.
The independently approved product PDF is authored by the shared runtime only
after engineering acceptance, not an input prerequisite for that acceptance.

## Host and board integration

The public HT port names, widths and signedness are declared in
`rtl/anvil_q1_ht_top.sv`. They do not depend on dimension overrides:

| Domain | Interface |
| --- | --- |
| Compute | `token_valid/ready`, uint32 `token_id/token_pos`, `new_sequence`; `logit_valid/ready`, uint32 `logit_index`, signed int32 `logit_data`, one-cycle `done/error` |
| Compute | `csr_valid/write`, uint16 byte `csr_address`, uint32 `csr_wdata`, `csr_ready`, held `csr_rsp_valid/rdata/error`, `csr_rsp_ready` |
| DDR | `load_valid/ready`, uint33 byte `load_address`,512-bit `load_data`,64-bit `load_byteenable`, `load_last`, `load_done/error` |
| DDR | uint33 byte `avm_address`, uint8 `avm_burstcount`, `avm_read/write`,512-bit `avm_writedata/readdata`,64-bit `avm_byteenable`, `avm_waitrequest/readdatavalid`,2-bit `avm_response`, `avm_writeresponsevalid` |

There is no HT host logical-memory request port. `anvil_q1_top` is a separate
compatibility entry with exactly the parent's ten parameters, ordering and
logical-memory interface. Its host memory remains in the original logical
layout, not the HT panel layout. Compile product and immutable reference tops
separately: they intentionally have the same compatibility module name.

CSR offsets are32-bit aligned. Every undefined offset or reserved-field write
returns a held error response and sets sticky error; no invalid mutation partly
changes the image, installed descriptors or storage mode.

| Offset | Access and contents |
| --- | --- |
| 0x0000 | RO version0x02000001 |
| 0x0004 | RO status READY bit0, BUSY bit1, IMAGE_VALID bit2, ERROR bit3; upper bits zero |
| 0x0008 | CONTROL WO bits0=invalidate,1=commit,2=idle error clear; bits0+1 together illegal, other bits zero; reads zero |
| 0x000c | RW mode0=AWQ,1=BF16; change invalidates image |
| 0x0010 | RW selected descriptor index |
| 0x0014..0x0028 | RW staging KIND,LAYER,PROJ,BASE_LOW,BASE_HIGH,LENGTH_BYTES; reads inspect the installed selected entry and error if absent |
| 0x002c | WO bit0=install; other bits zero; reads are undefined/errors |
| 0x0030,0x0034 | RO last/current token-cycle low/high |
| 0x0038,0x003c | RO lifetime owned DDR-read-response beat low/high |

BASE_HIGH uses only bit0; the descriptor index is
`(((layer*12)+kind)*8)+proj`. All mode, staging, index, control and install
mutations reject an engine/upload busy conflict. READY reports idle eligibility,
not the temporary token inhibition caused by the CSR read itself. Sticky error
inhibits new HT tokens until explicitly cleared. A CSR transaction/response
also temporarily excludes token starts, avoiding a same-edge mutation race.

Read each64-bit counter low then high. The low read captures its high half;
the next high read returns that captured half, then releases it. A high read
without a preceding low reads the current high half. The DDR counter is an
acknowledged coherent snapshot, so it can lag the external DDR edge by a CDC
round trip. It includes scalar and burst responses, including owned faulted
beats, but excludes writes, unowned stray responses and host upload bytes.
For exact benchmark boundaries the Verifier must count public accepted
transactions directly, not infer same-edge totals from this delayed CSR.
Token cycles count compute edges from token acceptance to final accepted logit
or error completion, not CPU wall time.

The integration sequence is:

1. Supply free-running compute and calibrated EMIF application clocks. Assert
   `rst_n=0` and reset/quiesce the EMIF transaction source. Keep it asserted
   until real EMIF initialization succeeds. The top has no calibration port;
   this reset qualification is the shell's mandatory contract.
2. Release reset and wait for descriptor/KV initialization. Use handshakes,
   not a fixed software sleep. Version/status CSR access becomes ready after
   initialization. All public outputs remain zero while reset is asserted.
3. Select storage mode, install the complete nonoverlapping descriptor set
   from a validated manifest, then stream the image using independently
   addressed64-byte aligned beats and byte enables. The first `load_valid`
   initiates a cross-clock exclusive grant; hold its payload until ready.
   Preserve valid/payload through stalls. `load_last` ends the upload, not a
   burst of inference reads. Wait for `load_done`, check `load_error`, and wait
   for core BUSY to clear after the acknowledgement crosses back.
4. Commit with CONTROL bit1. Wait for the held CSR response and reject errors.
   Commit does not succeed before all writes and descriptor validation finish.
   The image remains invalid after a failed upload. An idle CONTROL bit2
   clear round trip is required before retrying a failed upload.
5. Submit position0 for an initial sequence, or `new_sequence=1,token_pos=0`
   to restart. Otherwise positions must follow the last successful position.
   Consume each ordered logit using ready/valid. A stalled final logit must
   not complete early. Reuse the same committed image for subsequent tokens
   and at least two sequences without uploads or host weight service.
6. On numerical or owned-memory failure, wait for the error completion before
   reuse; clear sticky status and begin a new sequence. Protocol corruption,
   unexpected unowned Avalon responses or a failed tile ownership invariant
   require global reset after outstanding external traffic has drained.
   Global reset invalidates descriptors/image; soft new sequence does not.

The Avalon arbiter allows at most one entire response-owned transaction at a
time, a stricter bound than one read burst plus one write response. Weight
prefetch still overlaps independent on-chip compute on the other tile bank.
Write responses are mandatory; an adapter that only accepts writes but never
returns `avm_writeresponsevalid` cannot complete an upload or eviction.
The adapter must not return pre-reset traffic after reset release.

## Fixture acquisition and deterministic image preparation

No checkpoint/tokenizer hashes or passing model results are supplied by the
RTL intake. The independent Verifier owns acquisition, the manifest, repacking
code and fixture checks. Until exact identities are recorded, full-model
acceptance is blocked; this design does not silently choose another AWQ model.
The acquisition/repacking procedure must:

1. Pin an immutable revision of `Qwen/Qwen2.5-0.5B-Instruct` BF16 and the
   specifically requested corresponding AWQ artifact. Preserve original
   checkpoint shards, index, config, tokenizer/chat template and quantization
   metadata. Record origin, revision, byte length and SHA-256 of every input
   file in a project-relative fixture inventory. Missing AWQ identity is an
   explicit unmet prerequisite, not authorization to quantize another model.
2. Validate architecture dimensions, projection names/shapes, tied embedding
   identity, nibble permutation and no qzero-plus-one convention. Reject
   nonfinite tensor values. BF16 projection data retains actual BF16 bits;
   FP16 embedding/bias/gamma and Q2.30 RoPE must follow the frozen numerical
   contract, with any software-model discrepancy reported separately.
3. Produce both logical tensors and the exact panel-major byte images described
   above. For every logical entry, calculate its physical offset and verify
   inverse mapping/value identity; check each byte is assigned exactly once
   except explicit final zero padding. In particular, do not permute packed
   AWQ nibbles a second time when grouping words into64-output panels.
4. Allocate disjoint64-byte aligned ranges within8 GiB, including scratch and
   full K/V backing reservations. Emit mode, tensor identity, logical shape,
   byte length, base address and image/input hashes in the descriptor manifest.
   Check extended address ends and the complete descriptor index set before
   generating upload beats. Scratch/cache are runtime state, not immutable
   checkpoint tensors. Upload only the manifest's immutable data/padding,
   then install/commit with the preceding protocol.

This procedure must be implemented in independently owned `tests/*.py` and
re-executed, not replaced with this prose or with DUT-generated expected data.
No credential, private account path, local JTAG cable or PCIe BDF may be a
delivered dependency.

## Independent acceptance and project-standardized benchmarks

Required prerequisites are existing Python3, Icarus (`iverilog/vvp`), Yosys,
Vulcan native hardware commands, Quartus17.1 and the real Arria10 GX DDR4/
PCIe Gen3x8 bridge. They are prerequisites, not authorization to install tools.
Record actual versions in evidence. The Designer only performs static RTL
elaboration; no behavioral/synthesis harness belongs in Designer preparation.

Verifier entry points, executed from the delivered root, are fixed:

```sh
python3 tests/verify.py
python3 tests/verify.py --clean-repro
vulcan hardware fpga rtl-timing-lint
vulcan hardware fpga quartus-sta
vulcan hardware fpga board-hil
```

These commands are required checks, not claims that the independent verification
sources or results already exist. Missing tools/fixtures, child failures,
unobserved coverage, X/Z on active outputs, mismatches, latches, runtime div/mod
cells or absent required structural storage/arithmetic must fail explicitly.
Use unique retained evidence directories, progressing child bounds of at least
3600 seconds and settled timed-out process trees; preserve every failure.
The clean reproduction command copies only declared product sources, immutable
parent references and caller-supplied hash-validated fixtures into a new clean
directory and runs actual AWQ/BF16 numerical, DMA/KV and synthesis checks.
It is packaging validation, not a replacement for the complete matrix.

L1 uses seeds17,89,257 for each tuple below in both AWQ and BF16:

| Layers | Hidden | Intermediate | Q heads | KV heads | Head dim | Group | Vocab | Max seq | Tile | Window |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 8 | 8 | 1 | 1 | 8 | 1 | 8 | 1 | 1 | 1 |
| 2 | 24 | 40 | 3 | 1 | 8 | 8 | 17 | 9 | 3 | 3 |
| 2 | 128 | 256 | 4 | 2 | 32 | 128 | 67 | 17 | 16 | 5 |

Also elaborate/synthesize the actual full-default hierarchy and compare full
default-width GEMVs for all seven projections and vocabulary, including tails.
The numerical reference must be independently mathematical, not a translation
of the new FSM or a digest supplied by the DUT. Yosys must preserve two
substantive bank stores, KV storage and real64-lane multiply/accumulator state,
assert zero latches and no runtime division/modulo, and check connectivity.
Generic synthesis is not proof of DSP/M20K mapping or timing.

Every reachable directed bin must be observed, including coincident first/last;
tile depths1/3/256; windows1/3/128; all64 lanes/AWQ nibble positions; exact/tail
panels; signed extremes, ties, saturation, subnormal/negative-zero/invalid
FP16/BF16; bias/no-bias; at least three group transitions; at least four
alternating tile swaps with real fill/compute overlap; bursts1/2/15/16;4KiB/end
bounds; immediate/gapped/consecutive/issue-edge responses; waitrequest stalls
1/7/31 and seeded random stalls; final-logit stalls; busy CSR/load conflicts;
reset idle/filling/computing/stalled; new/illegal token/order; layer/head KV
isolation, ring/tag alias and cold spill. Resident hits must issue zero DDR
cache reads; repeated tokens issue zero uploads/host weight requests.
Test every zero dimension, inconsistent head relation, unsupported structural
constant, nondividing group, tile0/257 and window0/129 for explicit rejection.
Inject first/middle/final read and write faults and require error, never success.

In independent disposable copies, inject separately compiling defects for AWQ
permutation, tie direction, one lane product/sign, ownership/beat accounting,
KV wrap/tag alias and logit-stall/final completion. Each must be rejected by
a relevant functional assertion/reference, not by syntax or a missing tool.
Cover numerical and integrated memory/cache paths; preserve mutations/traces.

The explicitly project-standardized five-domain protocol is not a claim of an
external published suite:

| Domain | Frozen measurement |
| --- | --- |
| D1 DDR | Initial upload, persistent reuse, accepted bytes/DDR edges under unstalled and directed stalled service; no PCIe token weight traffic |
| D2 GEMV | Identical logical tensors for all seven full-default AWQ projections; actual immutable parent and HT compute-only/service-inclusive cycles; separate matched packed arithmetic baseline; independent BF16 measurements |
| D3 Attention | Hit-only zero-DDR recent-window cycles and complete causal cold/spilled-context cycles, separately reported |
| D4 Kernels/layers | Full-dimension RMSNorm/RoPE/SwiGLU and complete decoder layers against independent bit-exact expected values |
| D5 Model | Actual24-layer checkpoint, five prompts below, prefill separated from16 consecutive greedy decode tokens, every ordered logit and selected token compared independently |

D2's service policy accepts a parent logical request when idle and responds one
compute cycle later. HT commands are accepted immediately and return one DDR
beat each DDR edge starting the following edge. Report clocks and all raw
cycles; convert mixed-domain elapsed counts using those actual frequencies.
Require service-inclusive AWQ speedup at least8.0x for **each** default
projection; values above16x do not fail. Do not label transport improvement as
lane-only compute improvement. There is no parent BF16 observation to invent.

D5 prompts are exactly:

1. `Explain why the sky is blue.`
2. `Write a Python function that reverses a list.`
3. `Solve 17 * 23 and explain the calculation.`
4. `All roses are flowers. Some flowers fade quickly. Must all roses fade quickly?`
5. `Translate hello into French, Spanish, and German.`

Use the pinned tokenizer's documented chat template and lowest vocabulary
index for a greedy tie. Publish fixture/input identity, warmup, sink policy,
measurement edges, every raw cycle count and supplemental SHA-256 transcript
digests. Effective decode tokens/sec is
`decoded_tokens * actual_compute_frequency / total_decode_compute_cycles`,
including device-local stalls/nonlinear work/logit backpressure. Report upload,
prefill, raw DDR peak, measured DDR service and compute-consumed bandwidth
separately. No absolute token-rate floor was supplied.

Native L1.5 rejects timing-risk RTL. Native L2 must independently compile the
real target/shell, resolve all clocks/CDC, prove zero unconstrained functional
paths, DSP/M20K inference/device fit and WNS>=0 at10ns compute and actual EMIF
period. Native L3 requires at least three deterministic consecutive successful
physical-board runs, full-model bytes/logits and at least two sequences without
re-upload. All original checks remain mandatory; neither missing hardware nor
passing reduced tests waive them. The product PDF is produced and independently
approved by the shared runtime only after engineering acceptance.
