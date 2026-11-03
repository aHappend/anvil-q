# Anvil-Q2-HT v2.0.0-ht-ddr4

## Authority and implementation status

The admitted work order requires a complete DDR4-resident, 28-layer
Qwen2.5-1.5B accelerator, not an isolated arithmetic core. The implementation
documented here does not relax that requirement. Engineering acceptance, checkpoint
provenance, independent functional verification, native timing closure and board
execution are outstanding. Parent sources in `anvil_q2_reference/rtl/` are
read-only compatibility inputs, not verified HT sources.

Designer owns `rtl/*.sv`, this document, `design/ARCHITECTURE.md` and
`design/anvil_q2_ht.sdc`. Independent Verifier owns `tests/*` and `data/model/*`.
The runtime owns native hardware gates and the post-acceptance product report.

## Production geometry and platform

The top is `anvil_q2_ht_top`, targeting Intel Arria 10 GX
`10AX115N2F45E1SG` at a period no greater than 10.0 ns. Production geometry is
28 layers, hidden 1536, intermediate 8960, 12 query heads, two KV heads,
head dimension 128, group size 128, vocabulary 151936 and maximum sequence
32768. Compute width is fixed at 16 banks of eight lanes. Application DDR is
8 GiB, byte-addressed through a 512-bit Avalon-MM interface in the accelerator
clock domain. The external DDR controller owns physical memory timing and CDC.

Legal small geometries remain verification cases, never production substitutes.
Dimensions, queue/cache depths, tensor formats and allocation overlaps must be
explicitly validated before operation. Weights remain resident across tokens,
layers, new sequences and cancellation. Reset may require descriptor recommit
but not weight reload.

Legal dimensions are layers 1..28, hidden 8..1536, intermediate 8..8960,
query heads 1..16, KV heads 1..2, even head dimension 2..128, vocabulary
1..151936 and sequence length 1..32768. Hidden equals query heads times
head dimension; query heads divide into consecutive equal KV-head groups.
Hidden, intermediate and total KV width are divisible by eight. Group size
is a power of two in 1..128 dividing hidden and intermediate; cache block is
a power of two in 1..128 dividing head dimension. Tile slots support 2..8
(default four), outstanding reads 1..16 (default eight), request queue 1..16
(default three) and hot blocks 1..64 (default 64). Singleton and non-power-of-two
queue/cache capacities are legal. Production bank/lane/data widths are fixed;
unsupported values enter an explicit diagnostic branch, not a narrower design.

## Public system interface and configuration

All signals are synchronous to `clk`, except asynchronous assertion of active-low
`rst_n`. During reset every public output, including ready, data and addresses,
is zero. The platform must synchronize reset release and flush its controller
transactions with accelerator reset, while retaining DDR contents.

| Channel | Inputs | Outputs |
| --- | --- | --- |
| Token | `token_valid`, `token_id[31:0]`, `token_pos[31:0]`, `new_sequence`, `token_phase` | `token_ready` |
| Logits | `logit_ready` | `logit_valid`, `logit_index[31:0]`, signed `logit_data[31:0]` |
| Control | `cancel`, `ddr_ready`, `ddr_fault` | `done`, `error`, `cancel_done` |
| Configuration request | `cfg_valid`, `cfg_write`, `cfg_addr[15:0]`, `cfg_wdata[31:0]` | `cfg_ready` |
| Configuration response | `cfg_rsp_ready` | `cfg_rsp_valid`, `cfg_rdata[31:0]`, `cfg_error` |
| Host memory request | `host_req_valid`, `host_req_write`, `host_req_addr[32:0]`, `host_req_wdata[511:0]`, `host_req_be[63:0]` | `host_req_ready` |
| Host memory response | `host_rsp_ready` | `host_rsp_valid`, `host_rsp_rdata[511:0]`, `host_rsp_error` |
| Avalon command | `avm_waitrequest` | `avm_address[32:0]`, `avm_read`, `avm_write`, `avm_writedata[511:0]`, `avm_byteenable[63:0]`, `avm_burstcount[4:0]` |
| Avalon response | `avm_readdata[511:0]`, `avm_readdatavalid`, `avm_writeresponsevalid`, `avm_response[1:0]` | None; read returns cannot be backpressured |

Transfers are pre-edge valid/ready handshakes; registered responses remain
valid until a later accepting edge. Configuration and host channels each
allow one outstanding transaction, including its held response. Host
transactions use aligned 64-byte addresses and one beat. Writes require
idle operation and invalidated configuration; committed idle readback remains
available. Host success waits for a DDR response, not command acceptance.
Configuration requests have priority over host requests, which have priority
over a new token. Busy configuration writes return errors without mutation.

All configuration addresses are four-byte aligned. Registers are:

| Address | Meaning |
| --- | --- |
| `0x0000` | Read-only ID `0x41513248` |
| `0x0004` | Read-only version `0x02000000` |
| `0x0008` | CONTROL: write-one bit 0 commit, bit 1 invalidate; mutually exclusive |
| `0x000c` | STATUS: bit 0 model loaded, bit 1 busy, bit 2 sticky fault, bit 3 DDR ready |
| `0x0010` | Weight mode: 0 W4A16, 1 BF16 |
| `0x0014` | Cache mode: 0 Q16, 1 raw FP16, 2 block INT8 |
| `0x0018`, `0x001c` | KV base low 32 / high one bit |
| `0x0020`, `0x0024` | KV allocation length low 32 / high one bit |
| `0x1000 + 64*i` | Descriptor `i`, sixteen 32-bit words |

Unsupported addresses, reserved-bit writes, misalignment and invalid commits
return `cfg_error`. Commit may take multiple cycles; it responds successfully
only after every required descriptor and overlap check completes. Successful
recommit clears sticky fault when no new fault is present. Invalidation,
recommit and cancellation do not erase weights.

Phase zero is prefill and phase one decode. Positions are consecutive;
`new_sequence` requires position zero and invalidates KV visibility. Returning
to prefill after decode is illegal. The prefill count freezes on first decode.
Invalid tokens complete once with error and no logits. Successful logits
appear in increasing vocabulary order, hold under backpressure and precede
completion of their token; the final logit must be accepted before `done`.
Cancellation inhibits new work, drains held/accepted memory commands and
invalidates speculative and sequence state. It produces one `cancel_done`
after cancel releases and draining finishes, and `done/error` with it only
if a token was active. Fault completion also waits for legal draining.

## Arithmetic boundaries

`RHAZ(x,b)` rounds an exact signed magnitude right by `b` bits, with ties away
from zero; `b=0` is identity. `sat32` clamps to signed 32-bit limits.
No intermediate integer truncation is permitted except explicitly specified
format conversions.

In W4A16 mode, each kept lane computes
`activation_Q16 * (unsigned_weight_nibble - unsigned_zero_nibble) * scale_Q16`.
Scales use the parent's unsigned finite-FP16-to-Q16 conversion, including its
full 32-bit positive magnitude range. Negative nonzero scales and NaN/Inf
are faults; negative zero is accepted. Dequantized weights are signed 37 bits,
products signed 69 bits, and chunk/cross-chunk sums signed 128 bits. Q/K/V bias
is added as `bias_Q16 << 16` before the sole final RHAZ by 16 and saturation.
The importer, not the array, removes source AWQ nibble permutation
`[0,4,1,5,2,6,3,7]`; qzero is never incremented.

In BF16 mode, convert Q16 activations to BF16 using nearest-even rounding.
Multiply actual BF16 operands to FP32, supporting subnormals and nearest-even
rounding. Reduce 128 products by a fixed adjacent-pair balanced tree with
nearest-even rounding at each FP32 addition. Add chunk results in increasing
chunk order, then bias, then convert once to Q16 using RHAZ and saturation.
Nonfinite kept operands or arithmetic results cause a numerical fault.
Inactive lanes are positive zero and their input payloads do not cause faults.
BF16 results have their own independent oracle, not W4 parent equivalence.

## Tensor array interface

`anvil_q2_ht_tensor_array` exposes exactly:

| Direction | Ports |
| --- | --- |
| Input | `clk`, `rst_n`, `s_valid`, `s_mode`, `s_keep[127:0]` |
| Input | `s_act[4095:0]`, `s_w4[511:0]`, `s_zero[511:0]` |
| Input | `s_scale[2047:0]`, `s_bf16[2047:0]`, `s_tag[63:0]`, `m_ready` |
| Output | `s_ready`, `m_valid`, `m_mode`, signed `m_sum[127:0]` |
| Output | `m_fp32[31:0]`, `m_tag[63:0]`, `m_error` |

Lane zero occupies the least-significant slice. Mode zero selects W4;
mode one selects BF16. The inactive result field is zero. A numerical error
does not drop a vector or alter its tag: the errored result follows the same
channel, and the downstream sequencer must abort/drain the token.

## Cycle & Degenerate-Boundary Table

All handshake decisions use pre-edge `valid && ready`. Post-edge updates are
not consumable on the same edge that creates them.

| Boundary | Required behavior |
| --- | --- |
| Active asynchronous reset | All public outputs zero, pipeline validity cleared |
| First edge after reset | May capture a legal array input; no result yet |
| E0 capture | Latch operands, mask, mode and tag |
| E1 | Decode scales/nibbles and activation magnitudes |
| E2-E3 | Dequantize W4 or convert activation to BF16 |
| E4-E6 | Form/register full products |
| E7-E10 | Reduction of adjacent lanes, 128 to 64 |
| E11-E14 | 64 to 32 |
| E15-E18 | 32 to 16 |
| E19-E22 | 16 to 8 |
| E23-E26 | 8 to 4 |
| E27-E30 | 4 to 2 |
| E31-E34 | 2 to 1; result valid immediately after E34 |
| E35 | Earliest result consumption |
| Output blocked | Freeze every pipeline register; input ready zero |
| Output accepted with input accepted | Advance once; no bubble required |
| All lanes masked | Exact zero with original tag and no operand fault |
| One kept lane | Same latency and reduction order; other operands positive zero |
| Non-power-of-two ownership depth | Explicit wrap at depth minus one |
| Single-beat transfer | First and last coincide; exactly one acceptance/completion |
| Flush with returned beat | Drain old ownership; never reassign the beat |
| Prefetch queue/outstanding depth one | No zero-width pointer; explicit wrap to zero |
| Prefetch simultaneous ring push/pop | Count unchanged; old head response consumed once |
| Tile final fill with final metadata | Completeness stored now; READY only at a later edge |
| Tile issue with output consumption | One synchronous RAM read replaces the consumed vector |
| Tile fill/metadata/operand write with another slot's issue | Independent RAM write/read ports operate on the same edge; issue data appears after that edge without an additional register |
| Tile slots two through eight, including three | RAM address widths follow configured depth; full public slot range and ownership checks precede every enabled access |
| Tile output blocked with future-slot fill | RAM read registers hold; independent writes may continue in FILLING slots |
| Tile flush with issue/allocate | Flush wins; no new memory/ownership operation |
| Tile release with same-slot issue | Release waits; no same-generation reuse race |
| KV codec block one | Scan, exponent search and last-element paths remain reachable |
| KV codec response creation | Cannot consume response until a later valid/ready edge |
| KV codec annul with response/input | Annul wins and suppresses both channel handshakes |
| KV block plus commit request | Commit alone is accepted |
| KV write response | Acknowledge every backing beat before resident install/bitmap update |
| KV incomplete commit | Error response; committed count unchanged |
| KV resident read | Synchronous resident RAM read; no DDR request |
| KV invalidation with backing acceptance | Held command is accepted and then drained, not withdrawn |
| KV invalidation with backing response | Consume old response, clear visibility, do not install |
| KV capacity one or three | Explicit round-robin wrap; no binary-mask approximation |
| Configuration request | One outstanding request, including its held response |
| Commit validation | No successful response before the last validation/copy edge |
| Commit failure or cancellation | Previously committed descriptor bank/configuration unchanged |
| Descriptor lookup | Registered response; invalid indices return an error, not aliased data |
| Descriptor lookup replacement | Accepting a held response and a new lookup on the same edge replaces data/error together; an invalid lookup returns zero data without reading RAM |
| Descriptor lookup annul | Discard the local held lookup response so a canceled generation cannot block a subsequent request |
| Concurrent configuration/host/token requests | Integration must arbitrate configuration before host before a new token |
| Fabric client request | Acceptance reserves command storage and a private response slot |
| Fabric physical write acceptance | Not completion; wait for `avm_writeresponsevalid` |
| Fabric response creation with ready already high | Registered client response remains valid until a later edge |
| Fabric depth one, simultaneous read issue/retirement | Explicit ring wrap and push/pop count update |
| Host request forbidden by committed configuration | Registered error without a DDR command |
| Host cancellation after acceptance | Preserve held command; return its actual backing response |
| Scalar-reader invalidation | Discard cached validity and old result; legally drain held/accepted reads |
| Projection allocation versus release of the same slot | Allocate no earlier than the next edge after release |
| Projection final row issue | Retire slot only when the tile-buffer output can no longer be blocked |
| Projection context recurrence | Busy scoreboard prevents reading an unfinished accumulation |
| Projection final chunk | Emit row results only after all registered chunk accumulations complete |
| Format conversion | E0 capture, E1 decode, E2 registered result; freeze coherently on blocked output |
| Vector scalar read | Accept at E0; RAM data is selected by an eight-way slice stage then a sixteen-bank stage; registered response persists |
| Simultaneous vector scalar/tile requests | Scalar request wins the shared RAM read port; tile request is not accepted |
| Held vector tile response | No scalar RAM read can overwrite it before acceptance |
| Integer service | One request outstanding; each wide carry operation advances four 32-bit stages |
| Divider / square root | One trial per bounded multi-cycle iteration; no unrolled reciprocal or square-root path |
| KV burst miss | Reserve sixteen line slots, accept one bounded read burst, then acknowledge the logical beat after all returns |
| KV burst invalidate | Clear cached visibility but retain held commands and complete the accepted backing request |
| KV burst write | Clear read-ahead validity and await the actual DDR write response |
| Final logit, vocabulary one | Accept index zero once, then complete on a later clock |

The 34-interval array latency is measured in advancing edges, not elapsed edges
while stalled. Each integer tree level is a four-register 32-bit carry chain.
Each FP32 tree level has separate alignment, add/subtract, normalization and
rounding registers. Initiation interval is one without output blocking.

## Saved configuration and image ABI

`anvil_q2_ht_configuration` implements the admitted configuration request and
response registers, shadow descriptor storage and registered committed-descriptor
lookup. In the public top this module's `operation_busy`,
`quiescent` and `annul` inputs are connected to global ownership and drain state.
Shadow writes
are rejected during an operation. They do not mutate the active configuration.
Configuration responses persist until accepted. A successful commit atomically
switches a double-buffered descriptor bank after validation and copying finish.
An unsuccessful or annulled commit preserves the previous active bank and its
weight/cache configuration.

Committed descriptor payloads use a dedicated, clock-enabled synchronous RAM
read register without reset or a non-RAM data assignment. Invalid lookup indices
do not enable the RAM read; registered response error/valid bits mask the
unmodified payload register to zero. A valid lookup captured at E0 produces its
response immediately after E0, with earliest consumption at E1. Backpressure
holds the payload, validity and error together, without an extra pipeline edge.

Descriptor fields and offsets are those of the admitted 64-byte descriptor.
All fields are little-endian:

| Offset | Field |
| --- | --- |
| `+0` | Main base, u64; only low 33 bits allowed |
| `+8` | Main byte length, u64 |
| `+16`, `+24` | Qzero and scale bases, u64 each; only low 33 bits allowed |
| `+32`, `+36` | Rows and columns, u32 each |
| `+40` | Tile or row stride in bytes, u32 |
| `+44`, `+48` | Zero and scale row strides in bytes, u32 each |
| `+52` | Flags: valid bit 8; format bits 1:0; all other bits zero |
| `+56` | Reserved u64, zero |

Formats are AWQ-packed 0, FP16 1, BF16 2 and signed Q2.30 3.
There are `16+16*NUM_LAYERS` entries. A tiled matrix element `(o,i)`
uses tile `(o>>4)*ceil(cols/128)+(i>>7)` and element
`(o&15)*128+(i&127)`. Tiles contain 1024 low-nibble-first W4 bytes or
4096 little-endian BF16 bytes. Auxiliary arrays are output-major/group-minor;
zeros are unsigned packed nibbles, scales finite nonnegative FP16.
Entries 0 and 1 are row-major embedding and LM-head tables, with
`rows=VOCAB_SIZE`, `cols=HIDDEN_SIZE`, and FP16 in W4 mode or actual BF16 in
BF16 mode. The plain LM-head interpretation preserves the parent's embedding
lookup/logit-weight convention and permits tied table aliasing. It does not
reinterpret a non-AWQ LM head as W4. Entry 2 is a one-row final norm vector.
Entry 3 has `MAX_SEQ_LEN` rows and `HEAD_DIM` signed Q2.30 words per row:
word `2*j` is cosine and word `2*j+1` sine for split-half pair `j`.
Layer entries 0..6 are tiled Q/K/V/O/gate/up/down matrices. Layer entries
7 and 8 are one-row norm vectors, and 9..11 one-row Q/K/V biases.
Norm and bias words have the selected table format, not AWQ packing.
All reserved descriptors must read as zero.

Tile strides are 64-byte aligned and at least 1024 W4 or 4096 BF16 bytes.
Plain strides are at least the logical row length and aligned to the element
size. Main `byte_length` must cover every declared tensor element/tile,
including padded tiles. Its entire declared range participates in overlap
checks. For AWQ, auxiliary lengths are derived as
`(rows-1)*row_stride + logical_auxiliary_row_bytes`; host-supplied pointers do
not define unchecked lengths. Non-AWQ descriptors have zero auxiliary bases
and strides. Address sums are widened before bounds checking.

Commit checks every required entry, format, shape, flags, reserved field,
stride, main/auxiliary range and pairwise overlap, as well as the selected
dense KV allocation. The only overlap exception is identical complete
embedding/LM-head descriptors. Unwritten shadow words read as zero through
reset validity masks; RAM payload reset is unnecessary. Validation inspects
metadata, not the actual DDR payload: independent real load/readback/hash
verification remains mandatory and cannot be replaced by a successful commit.

## Saved internal computation and memory services

`anvil_q2_ht_projection` controls multi-slot allocation, main-tile prefetch,
activation acquisition, AWQ metadata expansion, registered tile issue/release,
and ordered cross-chunk accumulation. Its descriptor input must come from a
successful configuration commit. It is a projection engine, not the complete
token sequencer. The top connects it through the sequencer to the actual tile
buffers, prefetcher and tensor array.

Projection results are exact signed 128-bit W4 sums or FP32 BF16 sums,
indexed by logical row and held under backpressure. The engine does **not**
apply Q/K/V bias or final Q16 conversion; the sequencer performs those
once after the last chunk. Sixteen row contexts are interleaved. BF16 stores
the first chunk directly, preserving signed zero, and adds subsequent chunks
in increasing order using the four-stage FP32 adder. Padded rows are never
issued as logical outputs; padded columns are masked. Explicit per-context
busy state also supports singleton row recurrence without a feedback hazard.
Lookahead allocations have independent generations, activations, metadata
and accepted-read ownership.

`anvil_q2_ht_convert` supplies the format-boundary operations below. Its
three registered stages are shared-enable elastic stages, not unbounded
combinational floating-point arithmetic. Float-to-Q16 rounds halfway away
from zero and saturates; Q16-to-float rounds nearest-even. Nonfinite floating
inputs produce an explicit error.

| `s_op` | Conversion |
| --- | --- |
| 0 | FP16 payload to signed Q16 |
| 1 | BF16 payload to signed Q16 |
| 2 | FP32 to signed Q16 |
| 3 | Signed Q16 to FP16 payload |
| 4 | Signed Q16 to BF16 payload |
| 5 | Signed Q16 to FP32 |
| 6 | FP16 payload to FP32 |
| 7 | BF16 payload to FP32 |

Payloads occupy the low 16 bits; 16-bit results are zero-extended. Unsupported
operations return an error. Raw-FP16 KV storage bypasses numerical conversion
and continues to preserve every payload bit.

`anvil_q2_ht_ddr_fabric` arbitrates separate weight-prefetch and KV read-ahead
burst streams and up to four single-beat clients, three by default. The top
uses four clients: host, KV writes, sequencer coefficients and AWQ metadata.
It keeps an ordered read-owner ring,
per-client held responses and independent write-response ownership. A captured
command remains stable until physical acceptance, including during global
cancellation. Read-response capacity is reserved before issue. Read bursts
use 1..16 beats and remain within a 4 KiB page. Current write clients issue
single masked beats; this is not a claim of multi-beat write aggregation.
`anvil_q2_ht_host_port` enforces idle host access and write protection after
commit. `anvil_q2_ht_scalar_reader` caches two immutable DDR lines for 16/32-bit
coefficient accesses and legally drains invalidated work.

`anvil_q2_ht_kv_burst` backs the block cache with up to sixteen consecutive
read-ahead beats. The burst ends at the smaller of sixteen beats, the 4 KiB
page boundary and the configured allocation end. Every read has reserved
line storage, and future logical beat requests can hit this buffer without
another Avalon read. A write invalidates read-ahead state and forwards its
original byte enables; completion still requires the physical write response.
Invalidation never withdraws held commands or drops the response needed by
the block cache's drain. Speculatively fetched bytes are not logical token
visibility and must not be counted as useful bandwidth until consumed.

## Connected token implementation

`anvil_q2_ht_top` connects actual instances named `prefetcher`, `tile_buffers`,
`tensor_array`, `kv_cache` and `sequencer` in its legal-parameter generate
branch. The invalid branch drives zero and reports an explicit parameter error.
No parent module definition is copied or overwritten.

`anvil_q2_ht_sequencer` executes embedding, first norm, Q/K/V projections and
biases, split-half RoPE, K/V backing writes and per-layer commit, causal GQA,
O projection/residual, second norm, gate/up/SwiGLU/down/residual, every layer,
final norm and every vocabulary logit. It does not return token completion
until the final logit handshake. Its vector store is partitioned into 16 banks
with eight slices each. The same registered 128-lane array executes both
tiled projections and BF16 row-major LM-head chunks, using an explicit input
arbiter rather than a second hidden array.

W4-mode plain FP16 LM-head words follow the parent's signed Q16 conversion,
exact dot accumulation and sole final RHAZ by 16; they are not falsely packed
as AWQ. BF16 LM-head chunks use actual BF16 weights, the array's fixed tree,
ordered FP32 chunk additions and one final Q16 conversion. All inactive
activation lanes are explicitly zeroed before array transfer.

The integer service implements limb-serial signed 32/64-bit multiplication,
segmented 128-bit addition/subtraction, restoring division, digit-by-digit
integer square root and signed RHAZ. The following nonlinear rules are exact:
RMS mean is `floor((sum(x*x)<<32)/H)+18446744073710`, denominator is its floor
integer square root, reciprocal is `floor(2^64/denominator)`, and normalized
output is `sat32(RHAZ(x*gamma*reciprocal,48))`. RoPE uses complete signed
products and additions before RHAZ by 30. Attention divides the exact Q/K dot,
with signed nearest-away division, by `floor_isqrt(HEAD_DIM<<32)`; consecutive
query-head groups use the corresponding KV head. Scores are stored per causal
position; softmax subtracts their maximum, computes all exponents, sums them
exactly and performs one rounded weighted quotient per output component.

For Q8.24 exponentiation, `x<-1048576` gives zero and `x>=0` gives `16777216`.
Otherwise `u=(-x)<<8`, `n=floor(u/11629080)`, `r=u-n*11629080`,
`term=total=16777216`; six successive terms negate the previous sign and use
`floor(floor(abs(term)*r/2^24)/j)` for `j=1..6`. The result is
`max(total,0)>>n`. The iterative engine performs those operations with bounded
integer arithmetic. SiLU uses the parent's integer sigmoid quotient and
Q24 rounding; SwiGLU then multiplies the rounded/saturated SiLU by the up
vector, rounds by 16 and saturates. Residual addition saturates at its output
boundary. No software computation substitutes for these RTL operations.

These source implementations are not functional verification, synthesis,
timing closure or hardware evidence.

## Required integration and acceptance

Independent verification must exercise the connected hierarchy and the entire
token path, not just the module declarations or isolated arithmetic.

Four tile slots are the default, with at least two future tiles independently
owned while a current tile executes. Ordered read responses must use capacity
reserved before command issue. Bursts are 1..16 beats, split at 4 KiB, with
stable stalled commands. Writes complete only on DDR write response.
Cancellation suppresses new work, preserves legally held commands, drains all
accepted transactions, invalidates sequence/KV visibility and produces exactly
one completion without modifying weight contents.

KV storage has authoritative dense DDR records plus M20K resident blocks.
Q16 records preserve all 32 bits; raw FP16 records preserve all 16 payload bits.
INT8 records contain an exponent byte followed by signed block bytes, not one
64-byte padded record per small block. Commit exposes a position only after all
K/V backing writes succeed. Integrated Q16-to-FP16 conversion is nearest-even
and is not claimed lossless for arbitrary Q16 values.

The block interface uses `cmd_valid/cmd_ready`, `cmd_write`, `cmd_value`
(zero K, one V), `cmd_layer/pos/head/block[31:0]` and
`cmd_data[CACHE_BLOCK*32-1:0]`; responses use `rsp_valid/rsp_ready`,
the same-width `rsp_data` and `rsp_error`. Commit uses
`commit_valid/commit_ready`, `commit_layer/pos[31:0]` and the shared response
channel. Commit wins simultaneous requests. Positions commit consecutively,
only after every K and V block has completed its backing writes; an incomplete
or failed commit never exposes that position. Reads cannot access an
uncommitted position. Invalidation clears resident/commit visibility without
clearing DDR weights or dropping accepted backing transactions.

For block size B, records occupy 4B Q16 bytes, 2B raw-FP16 bytes, or B+1 INT8
bytes. Records are head/block-major; only the end of each token's K or V
region is rounded up to 64 bytes. INT8 chooses the smallest exponent e in
0..25 with `max(abs(x))<=127*2^e`, encodes `clamp(RHAZ(x,e),-127,127)`,
and reconstructs `sat32(signed_byte<<e)`. Reads reject e above 25 and byte
-128. Resident data holds the codec's reconstructed values, not uncompressed
inputs presented as an INT8 hit.

The five normative domains are tensor projections, nonlinear/residual
operations, causal attention, hybrid KV/memory, and full token/throughput.
Independent verification must implement every admitted boundary, randomized,
official-checkpoint, defect-sensitivity, synthesis and reproduction requirement.
Seeds are 11, 29 and 101. Mandatory observations include at least 100 consecutive
array vectors at II=1, exact 34-interval advancing-edge latency, influence of
all 128 lanes, every output stall position, at least 4096 useful streaming
read beats with at least 75% post-startup utilization, and at least 1000
accepted mixed transactions in each randomized memory run. Directed singleton
cases and depth-three wrap cases cannot be omitted.

Every domain requires numerical RTL observations with failing assertions and
executed coverage counters. Independent defect sensitivity must reject wrong
AWQ permutation/zero, a disconnected upper bank, response/slot misassociation,
KV exponent/commit corruption and BF16 rounding corruption by the intended
behavioral assertion, not compilation failure. Yosys must synthesize the
actual default-width hierarchy with meaningful ports/storage and zero latches.
The supplied parent must execute at banks one and four under a declared common
memory service model; measured long-streaming W4 projection throughput must
exceed the four-bank parent. Other domain speedups are measured, not assumed.

Official packed-image provenance/readback and projection rows from every
layer and all seven projections in both modes remain mandatory L1 checks.
Native L3 must execute complete default 28-layer tokens, at least two prefill
then one decode, with all logits checked in both weight and all three cache
modes, retained full-image hashes, no inference-time weight writes, maximum
allocation checks and three consecutive complete physical passes. Small
geometries or generic synthesis never replace these requirements.
Required portable entry commands, authored by Verifier, are:

```
python3 tests/verify.py --suite l1
python3 tests/verify.py --suite portable-reproduction
```

Native runtime L1.5 timing lint, L2 Quartus 17.1 STA and L3 Arria 10 GX PCIe
Gen3x8 board gates remain additional mandatory acceptance checks. Missing tools,
genuine checkpoints or hardware are unmet prerequisites, never passing results.
Full reproduction stages genuine pinned Qwen/Qwen2.5-1.5B-Instruct-AWQ and
Qwen/Qwen2.5-1.5B-Instruct data under `data/model/` with revision, license and
file hashes. Portable reproduction uses only declared product sources and
deterministic small fixtures in a fresh directory. Neither command may use
private host state, cached binaries or a premature product PDF as acceptance.
