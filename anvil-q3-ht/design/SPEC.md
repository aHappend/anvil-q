# Anvil-Q3-HT v2.0.0-ht-ddr4

## Status and authority

This is the design contract, not an acceptance report. The integrated RTL is
implemented and awaits independent verification. The admitted work order remains authoritative, including its complete
inference, benchmark, independent verification, timing and physical-board gates.
No simulation, synthesis, timing, bandwidth or accuracy result is asserted here.
The parent sources in `anvil_q3_reference/rtl/` are immutable provenance, not a
passing baseline. No repository-intake source index was supplied.
`design/GENERATIONAL_HANDOFF.md` is absent; the requested parent Quartus STA/PPA
figures are unavailable and must not be inferred.

Delivered parent copies retain their interfaces and numerical definitions.
The sole source compatibility exception is `rtl/anvil_q3_rmsnorm.sv`: redundant
`$signed` casts on the `sum_accumulator.in_value(square)` and
`epsilon_adder.in_a(mean)` connections are removed to address the retained
Yosys 0.33 frontend signedness assertion. Each source and destination is exactly
128 bits, and both destination ports are signed; the direct connections transfer
the same bits without extension, truncation or arithmetic changes. The immutable
`anvil_q3_reference/rtl/` remains unchanged. This repair requires fresh independent
numerical and synthesis regression; prior frontend diagnostics are not acceptance.

Designer owns `rtl/*.sv` and `design/*.md`. Verifier owns `tests/*.py`, including
the importer, deterministic image fixtures, independent numerical models,
testbench generation, receipts and benchmark adapters. The shared runtime owns
timing lint, Quartus STA, board execution and the independently approved final
PDF. That PDF is not a prerequisite of engineering verification.

## Platform and public interface

The final top is `anvil_q3_ht_top`. All logic uses one accelerator `clk` at
100 MHz or faster and asynchronous active-low `rst_n`. A calibrated synchronous
512-bit Avalon-MM interface is supplied by the platform; PHY, CDC and PCIe bridge
integration are outside inference RTL.

Token inputs are `cancel`, `token_valid`, `token_id[31:0]`, `token_pos[31:0]`,
`new_sequence`, `token_phase`, `logit_ready`, `ddr_cal_ready`, `model_commit`.
Outputs are `token_ready`, `logit_valid`, `logit_index[31:0]`, signed
`logit_data[31:0]`, `done`, `error`, `cancel_done`, `model_ready`.
Phase zero is prefill and phase one decode. Positions are consecutive;
`new_sequence` requires zero. Invalid requests complete with error, not logits.
Logits transfer in vocabulary order and hold under backpressure.

The idle-only host channel has inputs `host_req_valid`, `host_req_write`,
`host_req_address[32:0]`, `host_req_wdata[511:0]`,
`host_req_byteenable[63:0]`, `host_rsp_ready`; outputs `host_req_ready`,
`host_rsp_valid`, `host_rsp_rdata[511:0]`, `host_rsp_error`.
One request is one aligned 64-byte beat. Responses are ordered and retained.
Writes invalidate `model_ready`; recommit follows write drainage. Software must
validate image completeness and cryptographic digests before commit. Reset clears
readiness, not DDR contents. Recommit must not require retransmission.

Avalon outputs are `avm_address[32:0]`, `avm_read`, `avm_write`,
`avm_writedata[511:0]`, `avm_byteenable[63:0]`, `avm_burstcount[7:0]`;
inputs are `avm_waitrequest`, `avm_readdata[511:0]`,
`avm_readdatavalid`, `avm_response[1:0]`. Addresses are byte addresses.
The platform must adapt a word-addressed EMIF. Read/write are mutually exclusive.
Acceptance is assertion with low waitrequest; unaccepted commands hold stable.
Responses are ordered, gap-tolerant and have no ready. Response 00 is success.
No command crosses 4 KiB or the exclusive 8 GiB limit.

## Geometry

Production defaults: layers 36, hidden 2048, intermediate 11008, query heads 16,
KV heads 2, head dimension 128, AWQ group 128, AWQ bits 4, vocabulary 151936,
context 32768. Retain the full embedding, RMSNorm, Q/K/V/O/gate/up/down, split-half
RoPE, causal GQA attention, residual, SwiGLU, final normalization and logit path.
All seven projections must use the burst-fed HT array.

Legal HT banks are 1, 2, 4, 8, 16 (default 16), with exactly 16 lanes per bank.
Cache modes are 0, 1, 2 (default 0); HT INT4_ASYM is zero. TILE_K is
16/32/64/128 (default 128), TILE_ROWS 1..8 (default 8), TILE_SLOTS 2..4
(default 4), QUEUE_DEPTH 1..16 (default 3), BURST_BEATS 1/2/4/8/16
(default 16), KV_RESIDENT_GROUPS 1..256 (default 64).
Reduced dimensions obey H=Q*D, Q=8*K, positive even D, positive layer/vocabulary/
context dimensions, H and I multiples of eight and GROUP_SIZE, GROUP_SIZE a power
of two in 8..128, and context at most 32768. All image extents must fit the regions.
Illegal configurations require explicit `PARAMETER ERROR` diagnostics behind
safe-width/legal-datapath generate guards.

## Numerical rules

Activations are signed 32-bit Q16.16. AWQ q/z are unsigned nibbles, delta q-z
is signed [-15,15], with no implicit zero-code increment. Finite nonnegative
binary16 scales convert to unsigned Q16 by nearest rounding, ties upward.
Negative nonzero, infinity and NaN scales fault. Masked lanes contribute zero
and do not fault. Signed embedding, bias and gamma convert by magnitude rounding,
ties away from zero, signed-32 saturation; nonfinite inputs fault.

Lane weights are signed 37 bits, exact lane products signed 69 bits, and a
sixteen-lane reduction signed 73 bits. Different banks are different output rows.
K tiles accumulate exactly in checked signed 128-bit sums. Q/K/V bias is shifted
left 16 before the sole Q32-to-Q16 rounding, ties away from zero with parent
saturation. No per-lane or per-tile rounding is permitted.
Parent arithmetic helpers retain their public numerical definitions; independent
verification must derive mathematical expectations rather than transcribe RTL.

The preserved parent nonlinear rules are integer algorithms, not host floating
point approximations. Unsigned division takes the floor of a nonnegative ratio;
signed division rounds the magnitude by adding floor(denominator/2) before
division and restores sign (nearest, ties away). Division by zero faults.
Integer square root takes floor(sqrt(radicand)). Checked 128-bit add/subtract
faults on signed overflow. Saturating shifts round magnitudes to nearest with
ties away from zero and clamp to signed 32 bits.

RMSNorm first accumulates exact squares S of Q16 activation integers, takes
floor((S*2^32)/H), adds the exact epsilon integer 18446744073710 in Q64,
and takes its integer square root R. Its reciprocal is floor(2^64/R).
Each output is the signed-32 saturated, ties-away rounding of
`activation*gamma_Q16*reciprocal / 2^48`. Zero roots and overflow fault.

The exponential helper accepts signed Q16 x and returns unsigned Q24. It yields
zero below -1048576 and 16777216 at x>=0. Otherwise let
`a=(-x)*256`, `k=floor(a/11629080)`, and `r=a-k*11629080`.
Starting at t0=16777216, terms j=1..6 have alternating sign and magnitude
`floor(abs(t[j-1])*r/(2^24*j))`. The result is the nonnegative sum of all seven
terms shifted right k. SiLU evaluates this exponential at -abs(x), divides
`2^48` (nonnegative x) or `exp*2^24` (negative x) by `2^24+exp`,
and multiplies the resulting Q24 sigmoid by abs(x), with a single half-up
magnitude shift by 24, sign restoration and signed saturation. SwiGLU multiplies
that Q16 result by the up projection and rounds/saturates once at shift 16.
Residuals are checked additions followed by signed-32 saturation.

RoPE uses parent split halves: `(x*cos-y*sin, y*cos+x*sin)` with signed Q2.30
coefficients, checked wide accumulation and ties-away saturation at shift 30.
Attention divides the exact Q/K dot by floor(sqrt(HEAD_DIM*2^32)), producing
Q16 scores with signed nearest rounding. It subtracts the causal maximum,
uses the Q24 exponential above, accumulates exponentials and weighted Q16
values exactly, then divides the latter by the former with signed nearest
rounding and saturates to Q16. The decoder deliberately retains the parent's
multi-pass score recomputation schedule; it does not substitute approximate
floating-point softmax.

Mode 0 stores signed 32-bit Q16 words without quantization. Mode 1 groups 32
elements into signed INT8 [-127,127]; Mode 2 groups 64 into signed INT4 [-7,7].
Choose the smallest nonnegative exponent e with max(abs(x)) <= limit*2^e.
All-zero groups require e=0. Round magnitudes by adding half a step before
shifting, restore sign and clamp. Decode with signed-32 saturating left shift.
Maximum e is 25/29 respectively. Reject reserved minimum codes, invalid headers,
nonzero unused payload/padding and noncanonical zero headers.
GQA uses query_head >> 3, not division by the bank count.

## Cycle & degenerate-boundary table

All transfers use **pre-edge** valid/ready and payload. State and output tables
refer to settled **post-edge** values. Flush/cancel has priority over acceptance.
Unreset RAM is visible only behind reset validity/ownership state.

| Boundary | Required behavior |
|---|---|
| Active reset | Every public valid, ready, done, error, cancel_done and model_ready is zero; invalid payloads zero |
| First released edge | Ready may rise only with calibration, committed image and idle ownership |
| Token accepted at n | Latch at n; no same-edge logit; block another token through completion/drain |
| Last logit transferred | One post-edge interval of done, then idle regardless of token_valid |
| MAC accepted at n | Stage 0 post n; stages 1..8 post n+1..n+8; first output transfer n+9 |
| MAC blocked output | All nine stages, validity, errors and identities freeze together |
| MAC bubble | Shift validity only on global enable; initiation interval one without stalls |
| Registered tile read at n | Operand post n; MAC can accept at n+1, producing post n+9 |
| Tensor accumulator accepted at n | Parent segmented adder result post n+8; first consume n+9 |
| Dependent row update | Stall until prior checked update commits; no speculative forwarding |
| Returned final beat at n | Data stored post n; READY consumer cannot transfer before n+1 |
| Final tile operand transferred | Slot may become EMPTY post that edge, never earlier |
| One-beat operation | First and last coincide; one reservation, transfer and completion |
| Queue depth one | Simultaneous pop/push preserves one new item, explicit wrap to zero |
| Slots/groups depth three | Explicit compare-and-wrap; never a power-of-two mask |
| Simultaneous reserve/release | Release only after final transfer; no earlier recycling |
| Host write and commit together | Accepted write invalidates readiness; later recommit is required |
| Commit with held host response | Allowed after DDR drainage; does not consume or alter the held response |
| Flush with outstanding reads | Poison owners, retain command/return reservations, drain accepted reads |
| Flush and stalled command | Hold previously offered command until accepted; drain its returns |
| Scratch reset/flush | Invalidate via a one-bit-per-word synchronous sweep; requests remain blocked until the sweep finishes |
| Scratch request at n | Registered data/validity post n; response first transfers at n+1 and holds while blocked |
| Scratch unwritten word | Explicit error response and zero payload, never exposed uninitialized RAM |
| Image-map request at n | Registered checked address/extent response post n; first response transfer n+1 |
| Single-record DDR admission | Reserve the sole completion register before offering a command; admission is not Avalon acceptance |
| Single-record cancellation | Keep offered command fields and accepted-read ownership until drainage; discard completion and clear poison before new admission |
| KV command | Accept only while idle; commit traverses all K and V records before incrementing layer visibility |
| KV resident lookup | One synchronous tag/record read followed by a comparison; replacement wraps explicitly, including residency 1 and 3 |
| KV completion | One interval of done/error; successful commands return idle, faults require flush |
| Projection command accepted at n | Identity captured post n; image-map request transfers no earlier than n+1, response no earlier than n+2; DDR and scratch progress is handshake-relative |
| Projection scalar arbitration | Retain selected load/writeback request and owner through actual request acceptance and response; do not switch owners under stall |
| Raw tile materialization | Registered raw q/group/activation read at r; first tile-bank write transfers at r+1; seal follows all writes |
| Ordered tile activation | Seal at s gives READY post s; activation transfers no earlier than s+1, registered tile read no earlier than s+2, MAC acceptance no earlier than s+3 |
| Independently stalled tensor banks | Retain per-bank accepted bits; transfer the shared tile entry only after all active banks have accepted exactly once |
| Tensor final sum accepted by writer | Latch exact sum/identity; optional bias uses the checked eight-segment adder; only then round and offer the held scratch write |
| Projection completion | All real output rows acknowledged by scratch, producer finished, no owned tiles and idle tensor/prefetch; done lasts one interval |
| Scratch spill initialization | Calibration gates bitmap writes; no scratch access until resident and spill validity sweeps settle |
| Scratch spill write | Data byte enables accepted before bitmap update; only bitmap completion acknowledges the word; flush drains and invalidates |
| Reset with external reads | Platform must reset/drain the interface consistently; no untagged old returns may enter a new reset session |

MAC16 stage allocation is fixed: 0 capture; 1 delta and scale decode;
2 dequantization and activation alignment; 3 signed-high/unsigned-low activation
partial multiplication; 4 exact product combination; 5/6/7/8 binary reduction
levels of widths 70/71/72/73. Metadata and masked-scale errors follow all stages.
The tensor input is a ready/valid operand stream after registered tile reads.
Each bank independently retains one pending reduction and uses a checked
segmented accumulator; dependent updates explicitly stall. Final row sums hold
until accepted. Command/load/result handshakes must never infer progress from
fixed DDR latency. The top retains these boundaries.

## Storage and image ABI

| Region | Inclusive base | Exclusive limit |
|---|---|---|
| Packed qweight | 0x000000000 | 0x060000000 |
| Packed qzeros | 0x060000000 | 0x064000000 |
| FP16 scales | 0x064000000 | 0x06c000000 |
| Q/K/V bias | 0x06c000000 | 0x06d000000 |
| Normalization | 0x06d000000 | 0x06e000000 |
| RoPE | 0x06e000000 | 0x080000000 |
| Tied embedding/head | 0x080000000 | 0x0c0000000 |
| Scratch reservation | 0x0c0000000 | 0x100000000 |
| KV backing | 0x100000000 | 0x200000000 |

Each layer concatenates Q,K,V,O,gate,up,down. Matrix input/output sizes are H/H,
H/(K*D), H/(K*D), H/H, H/I, H/I, I/H respectively. Each matrix region starts at a
64-byte boundary. Qweight input-major words pack eight output nibbles; the lane
bit shifts are [0,16,4,20,8,24,12,28]. Qzeros are input-group-major with identical
packing. Scale entries are input-group-major/output-major little-endian binary16.
Unused output lanes are zero. Bias arrays concatenate layer and Q/K/V.
Gamma arrays concatenate each layer's input/post-attention weights then final
gamma. RoPE is position-major/pair-major cosine then sine, signed Q2.30.
Embedding/head is row-major little-endian binary16.

For input count N and output count M, let R=ceil(M/8), G=ceil(N/GROUP_SIZE).
Matrix bytes before alignment are `4*N*R`, `4*G*R`, `2*G*M` for qweight,
qzeros and scale. Add each aligned matrix extent, not an approximate bit count.
Parent scratch slot meanings must be preserved with bounded reusable on-chip
activation storage, not full-model on-chip weights.

The scratchpad uses variable-length slots rather than allocating intermediate
width for every slot. Slots 3/4 have K*D words, slots 9/10/11 have I words, and
the other slots 0..14 have H words. Total storage is `10*H+3*I+2*K*D`
32-bit words: 54,016 words (216,064 payload bytes) at the production geometry,
plus one validity bit per word. The first min(total,65536) words reside on chip.
Larger legal activation geometries spill the remainder to
`0xc0000000+4*logical_word_index`; data must end before 0xfe000000.
Bitmap page j at `0xfe000000+64*j` contains the validity bits of 512 spilled
words, with j=`(logical_word_index-65536)>>9`. Its selected bit is the low nine
bits of `logical_word_index-65536`. All bitmap records fit below 0x100000000.
Production uses no spill payload or bitmap pages. Slot meanings are 0 residual/embedding,
1 input norm, 2 Q, 3 K, 4 V, 5 attention context, 6 O, 7 attention residual,
8 post-attention norm, 9 gate, 10 up, 11 SwiGLU product, 12 down,
13 parent-reserved scratch and 14 final norm. An invalidating sweep clears only
the resident validity RAM, one word per edge, and spilled bitmap records through
the calibrated DDR interface, while readiness is low. Payload RAM is never
reset. Arbitrary-order writes are supported and unwritten reads fault.
Flush does not erase the persistent DDR image.

Mode 0 per-head extent is `64*ceil(4*D/64)`. Mode 1/2 per-head extent is
`64*ceil(D/32)` / `64*ceil(D/64)`. With extent E, the head record starts at
`KV_BASE + ((((layer*2 + is_value)*MAX_SEQ_LEN + position)*K + head)*E)`.
Compressed group j adds `64*j`: bytes 0..31 payload, bytes 32..35 little-endian
exponent with only low eight bits used, bytes 36..63 zero. INT4 low-index code is
in the low nibble. Partial groups zero unused lanes. Mode 0 word j adds `4*j`.
All calculations use enough intermediate bits and reject overflow before any
33-bit address truncation.

The default geometry gives the following analytical component sizes. All matrix
extents already divide 64, so matrix-start alignment adds zero bytes here.
These are layout calculations, not measured image-loading results.

| Component | Bytes |
|---|---:|
| All 36 layers packed qweight | 1,387,266,048 |
| All qzeros | 10,838,016 |
| All FP16 group scales | 43,352,064 |
| All Q/K/V biases | 184,320 |
| All normalization gamma | 299,008 |
| All context RoPE pairs | 16,777,216 |
| Tied embedding/head table | 622,329,856 |
| Total image payload, excluding reserved gaps | 2,081,046,528 |
| Mode 0 full-context KV backing | 2,415,919,104 |
| Mode 1 full-context KV backing | 1,207,959,552 |
| Mode 2 full-context KV backing | 603,979,776 |

Qweight, qzeros and scale ends are 0x052b00000, 0x060a56000 and
0x066958000 respectively. Bias, gamma, RoPE and embedding ends are
0x06c02d000, 0x06d049000, 0x06f000000 and 0x0a5180000 respectively.
They lie below their respective region limits. Mode 0/1/2 backing extents are
0x090000000, 0x048000000 and 0x024000000 bytes, each within the 4 GiB KV region.
Unused image-region gaps and the scratch reservation are not counted as payload.
Reduced geometries require their own checked extents rather than reuse of these
default totals.

## Benchmarks and validation ownership

The project-standard domains are persistent DDR load/readback and tiled transfer,
seven-projection GEMV, KV storage/reconstruction, causal GQA attention, and full
decoder/token execution. This is not an external language-accuracy standard.
All domains require modes 0/1/2, banks 1/4/8/16, seeds 17/89/101. Complete reduced
inference additionally covers bank count 2 and a real 36-layer configuration.
Official checkpoint/tokenizer/benchmark assets are not supplied. Generated
fixtures must be labeled synthetic; no official-model result may be fabricated.

Parent bank mapping is 1->1, 4->4, 8->8, 16->8. Parent PROFILE=3 and INT4_ASYM=0.
HT16 comparison is `ht16_vs_parent8`, not matched banks. The parent's legality
must not be widened. Shared parent baselines must name their source, workload,
mode, seed and service identity; every invocation regenerates its prerequisites.
HT-only host loading has no invented parent equivalent.

The service policy is `byte-budget-64-latency12-rr-v1`: 100 MHz, aggregate 64
bytes/cycle, minimum return n+12 after acceptance at n, independently pipelined
reads, bounded queues of at least 64 descriptors, deterministic round-robin.
HT returns/writes cost 64 bytes; parent scalar transfers cost four bytes, at most
one per bank per cycle. Retained responses are charged exactly once. No hidden
64-byte scalar penalty, coalescing or bank-dependent latency. Report useful,
physical and repeated traffic separately, including parent scratch traffic.
Require >=90% payload bandwidth across >=4096 returned steady-state beats and
greater useful streaming weight-delivery throughput than the mapped executable
parent for every benchmark mode/bank, with observed simultaneous fill/consume.
Do not assert an unmeasured whole-model speedup.

From the delivered root the independent Verifier entry points are:

```
python3 tests/verify.py --suite smoke
python3 tests/verify.py --suite behavior
python3 tests/verify.py --suite ddr4
python3 tests/verify.py --suite kv-gqa
python3 tests/verify.py --suite benchmark
python3 tests/verify.py --suite mutations
python3 tests/verify.py --suite synthesis
python3 tests/verify.py --suite reproduce
```

These are admitted commands, not a claim that a Verifier-owned entry point
exists or passes. Dependencies: Python 3, Icarus (`iverilog`, `vvp`),
compiled Verilator and Yosys; do not install tools. Verifier records actual tool
versions and independently generates fixtures in fresh per-run evidence
directories. Icarus is limited to compact startup/leaf/one-token checks; compiled
Verilator handles production widths and sweeps. Designer does not author these
tests or execute simulations/synthesis.

All eight commands, exhaustive/seeded numerical comparisons, six detected
functional mutant classes, ownership/error/parameter coverage, zero-latch real
hierarchy synthesis and clean-directory reproduction remain mandatory. Native
timing lint and target Quartus <=10 ns timing with valid setup/hold/recovery/
removal and three consecutive physical-board passes are still required.
