# Anvil-Q2-HT v2.0.0-ht-ddr4

## Authority and implementation status

The admitted work order requires a complete DDR4-resident, 28-layer
Qwen2.5-1.5B accelerator, not an isolated arithmetic core. The source increments
documented here do not relax that requirement. Engineering acceptance, checkpoint
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

The 34-interval array latency is measured in advancing edges, not elapsed edges
while stalled. Each integer tree level is a four-register 32-bit carry chain.
Each FP32 tree level has separate alignment, add/subtract, normalization and
rounding registers. Initiation interval is one without output blocking.

## Saved configuration and image ABI

`anvil_q2_ht_configuration` implements the admitted configuration request and
response registers, shadow descriptor storage and registered committed-descriptor
lookup. The public top is not yet implemented; this module's `operation_busy`,
`quiescent` and `annul` inputs still require system integration. Shadow writes
are rejected during an operation. They do not mutate the active configuration.
Configuration responses persist until accepted. A successful commit atomically
switches a double-buffered descriptor bank after validation and copying finish.
An unsuccessful or annulled commit preserves the previous active bank and its
weight/cache configuration.

Descriptor fields and offsets are those of the admitted 64-byte descriptor.
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
token sequencer. External tile buffers, prefetcher and tensor array still need
to be connected by the top/sequencer integration.

Projection results are exact signed 128-bit W4 sums or FP32 BF16 sums,
indexed by logical row and held under backpressure. The engine does **not**
apply Q/K/V bias or final Q16 conversion; the sequencer must perform those
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

`anvil_q2_ht_ddr_fabric` arbitrates the prefetch burst stream and up to four
single-beat clients, three by default. It keeps an ordered read-owner ring,
per-client held responses and independent write-response ownership. A captured
command remains stable until physical acceptance, including during global
cancellation. Read-response capacity is reserved before issue. Read bursts
use 1..16 beats and remain within a 4 KiB page. Current write clients issue
single masked beats; this is not a claim of multi-beat write aggregation.
`anvil_q2_ht_host_port` enforces idle host access and write protection after
commit. `anvil_q2_ht_scalar_reader` caches two immutable DDR lines for 16/32-bit
coefficient accesses and legally drains invalidated work.

None of these saved modules constitutes completed top-level integration,
functional verification, synthesis, timing closure or hardware evidence.

## Required integration and acceptance

The final top must connect actual instances named `prefetcher`, `tile_buffers`,
`tensor_array`, `kv_cache` and `sequencer` of the corresponding HT modules.
The sequencer must execute embedding, both norms, Q/K/V and biases, split-half
RoPE, causal GQA, O/residual, SwiGLU, final norm and every vocabulary logit.
No CPU substitution, constant-output wrapper or serialized replacement for the
128 physical lanes is acceptable.

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

The five normative domains are tensor projections, nonlinear/residual
operations, causal attention, hybrid KV/memory, and full token/throughput.
Independent verification must implement every admitted boundary, randomized,
official-checkpoint, defect-sensitivity, synthesis and reproduction requirement.
Required portable entry commands, authored by Verifier, are:

```
python3 tests/verify.py --suite l1
python3 tests/verify.py --suite portable-reproduction
```

Native runtime L1.5 timing lint, L2 Quartus 17.1 STA and L3 Arria 10 GX PCIe
Gen3x8 board gates remain additional mandatory acceptance checks. Missing tools,
genuine checkpoints or hardware are unmet prerequisites, never passing results.
