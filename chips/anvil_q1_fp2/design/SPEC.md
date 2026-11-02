# Anvil-Q1-FP2 v2.2.0-fp2-bfp-fused

## Status and authority

This is the design-side implementation contract, not a verification or acceptance
report. The admitted work order remains authoritative. Implementation is in
progress: the exact tensor, fast-rsqrt, DDR ping-pong and telemetry leaves exist;
the optimized decoder, fused epilogue, attention and top-level integration are
not yet complete. No numerical, performance, synthesis, timing or board result is
claimed here.

The immutable parent is `anvil_q1_fp_reference/rtl/*.sv`. No repository intake
source index was supplied. `design/GENERATIONAL_HANDOFF.md` was absent at intake;
historical parent Quartus timing and PPA are unavailable. Fresh, independent
matched parent measurements and shared-runtime physical reports must establish
all comparative claims. This gap is not a waiver.

Designer owns `rtl/*.sv`, design documentation and `fpga/anvil_q1_fp2.sdc`.
Independent Verifier owns `tests/*.py`, references, stimulus and all functional
simulation/synthesis checks. The final product PDF is produced by the shared
runtime only after engineering acceptance.

## Target, parameters and modes

Target Intel Arria 10 GX `10AX115N2F45E1SG`, one synchronous 100 MHz clock,
10.000 ns period. No generated clocks, inferred runtime division/modulo,
mixed blocking/nonblocking sequential assignments, latches, floating-point
`real` datapaths, or unsubstantiated timing exceptions are permitted.

The top will be `anvil_q1_fp2_top`. Preserve parent parameter order:

| Parameter | Default |
|---|---:|
| NUM_LAYERS | 24 |
| HIDDEN_SIZE | 896 |
| INTERMEDIATE_SIZE | 4864 |
| NUM_Q_HEADS | 14 |
| NUM_KV_HEADS | 2 |
| HEAD_DIM | 64 |
| GROUP_SIZE | 128 |
| AWQ_BITS | 4 |
| VOCAB_SIZE | 151936 |
| MAX_SEQ_LEN | 32768 |

Append `ENABLE_FP2=1`; legal values are 0 and 1. `ENABLE_FP2=0` preserves
parent modes 0/1/2 and rejects mode 3. With FP2 enabled, mode 0 retains AWQ/Q16
compatibility, mode 2 retains FP16 compatibility, mode 1 uses the optimized
BF16 decoder and mode 3 uses optimized Group-32 scaled E4M3FN.

Retain the complete constraints in the parent's `anvil_q1_parameters`:
positive dimensions, AWQ_BITS=4, H=Q*D, Q divisible by KV, even D, H/I divisible
by G and by eight, KV*D divisible by eight, and all 128-bit-evaluated logical
address bounds. MAX_SEQ_LEN is at most 16777215. Fixed optimized tensor width is
64 and MX group size is 32; partial groups use masks/padding, not a new
dimension restriction. Attention TILE_TOKENS must support every integer 1..16.

Mandatory legal geometries include:

| L | H | I | Q | KV | D | G | V | S |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 8 | 8 | 1 | 1 | 8 | 1 | 1 | 1 |
| 2 | 56 | 64 | 7 | 1 | 8 | 8 | 17 | 3 |
| 2 | 112 | 128 | 14 | 2 | 8 | 8 | 17 | 5 |

Illegal parameters must reject clearly, without clamping a legal datapath.
Diagnostic-only widths may remain nonzero so rejection is executable; advisory
lesson `exp-6d5cc92e6f5a86894eaae275` does not relax the legal range.

## Cycle and degenerate-boundary table

All reset is active-low **synchronous**. Edge k samples pre-edge valid and ready;
post-edge values include nonblocking updates. Combinational public outputs are
also reset-gated. No transfer occurs while reset is low. Internal data memories
need not be reset: validity/ownership prevents stale values from becoming public.

| Boundary | Required behavior |
|---|---|
| Reset asserted | Public ready/valid/done/error/status/address/payload outputs are zero; the clock edge clears validity and ownership. |
| First release edge | Idle readiness may assert before the edge; no stale response or result becomes valid. |
| Tensor accept at k | Decoded BF16 operands and conversion status occupy stage 0 after k. |
| Tensor k+1 | Exact 8-by-8 significand products, signs, grid shifts and leading exponents. |
| Tensor k+2 | Eight registered eight-product maxima and associative special-value summaries. |
| Tensor k+3 | Global maximum including accumulator; global special-value summary. |
| Tensor k+4 | Coarse exact placement and below-window event bits. |
| Tensor k+5 | Fine placement, signed exact terms, accumulator and event population count. |
| Tensor k+6..k+11 | Six balanced registered tree levels; first pair includes accumulator using carry-save reduction. |
| Tensor k+12 | Exact magnitude/sign. |
| Tensor k+13 | Registered leading-bit index and magnitude. |
| Tensor k+14 | FP32 retained significand, guard/sticky, exponent and zero preparation. |
| Tensor k+15 | First valid final RNE result/status/events; no earlier result is valid. |
| Tensor output blocked | Freeze every pipeline register and metadata; in_ready=0. Latency counts advancing edges only. |
| Tensor singleton/all masked | Same latency and handshake; acc_in survives, with canonical NaN/sNaN rules and preserved -0 when appropriate. |
| Fast-rsqrt accept at k | Stage 0 holds normalized lookup seed/update and signed power-of-four rescaling information. |
| Fast-rsqrt k+1 | Stage 1 holds the result, status and valid; II=1. Bubbles emerge invalid with zero public payload. |
| DDR one descriptor | One owned slot/ID, including singleton read or write acknowledgment. No implied second beat. |
| DDR two descriptors | Both slots may be outstanding; distinct IDs may respond in either order. |
| DDR return/reuse | Only consumer retirement releases a slot. Full-buffer retirement and descriptor refill may occur on the same edge. |
| DDR zero-latency bridge | A response for a request accepted on the same edge is accepted and wins over INFLIGHT state assignment. |
| CSR accept at k | Capture read/error response and apply valid control write once. |
| CSR k+1 | First asserted response; hold its data/error unchanged until accepted. |
| CSR clear + event + snapshot | Clear counters, maximum, snapshots and sticky error; clear wins. |
| CSR snapshot + event | Snapshot pre-edge values; independently increment live counters. |
| Counter at maximum | Saturate, never wrap; reset > clear > enabled events. |
| FP32 binary accept at k | Operand register stage 0; MULTIPLY is a static 0/1 parameter. |
| FP32 binary k+1..k+8 | Exact significands/exponents, coarse placement, fine signed placement, sum, magnitude, leading index, RNE preparation, then valid result. II=1 with no stalls. |
| FP32 binary stalled | Freeze all nine stages and metadata as for the tensor. |

Command engines, when integrated, must implement the following transfer-based
contract; their concrete compute-state latencies must be documented with their
implementation, not guessed from continuously ready tests:

| Command boundary | Contract |
|---|---|
| Idle command accepted at k | Data cannot transfer before the command. An invalid command consumes no operands. |
| Legal singleton | Its first input is also its last; emit exactly one last output when computation finishes. |
| Final input stalled | Do not advance its index, store its operands, or begin completion until transfer. |
| Final output stalled | Keep valid/data/last/status stable; do not assert done or accept a new command. |
| Final output transferred at f | Pulse done after edge f+1, then return idle. |
| Invalid command at k | Pulse error completion after k+2, consume no input stream, then return idle. |

The first token after reset must explicitly begin a new sequence at position
zero. Reset invalidates logical KV ownership, aborts work, and requires the bridge
to discard responses from the previous reset epoch. Sequence validation and
fatal-operator error termination are not yet integrated.

## Exact tensor and format contract

`anvil_q1_fp2_bfp_tensor_array` has the frozen ports:
`clk,rst_n,in_valid,in_ready,out_ready,format_mx,a[1023:0],b[1023:0],
a_scale[15:0],b_scale[15:0],lane_mask[63:0],acc_in[31:0],
out_valid,result[31:0],status[4:0],alignment_events[6:0]`.
BF16 lane i occupies bits 16*i+:16. MX lane i occupies bits 8*i+:8
in the low 512 bits; high 512 bits are ignored. Each independent operand's
scale bytes are low-group-first (lanes 0..31, then 32..63).

Status is `{invalid,divide_by_zero,overflow,underflow,inexact}`.
Canonical FP32 NaN is `0x7fc00000`. Finite reduction is exactly
RNE_FP32(acc_in + sum(active exact decoded products)), with one final FP32
rounding. Gradual underflow and ties-to-even are mandatory; exact nonzero-term
cancellation yields +0. An empty mask returns acc_in, canonicalizing NaNs and
raising invalid for signaling NaN. Masked operands cannot affect the maximum,
special-value flags, conversion flags or arithmetic.

The implementation uses the admitted direct fixed-grid alternative: signed
544-bit integers measured in units of 2^-266. BF16 significands are eight bits;
their exact products fit sixteen bits. Product placement is split into coarse
32-bit-block and fine 0..31-bit registered stages, followed by an exact signed
tree. The FP32 accumulator joins the first tree node through a carry-save
three-to-two reduction; it is not separately rounded.

E_max is detected over active nonzero finite products and the finite
accumulator. The main reporting window covers exponents E_max down to E_max-63.
An alignment event is one active nonzero product having at least one nonzero bit
below this window. All such bits remain in the exact fixed-grid tail, not a
signless sticky approximation. Physical resources for the entire exact grid,
alignment, normalization and control must be included in the eventual per-lane
ALM comparison. No resource saving is established by this architecture alone.

MX is E4M3FN: sign bit 7, exponent 6:3, fraction 2:0, bias 7; exponent zero
is subnormal, exponent 15/fraction 0..6 is finite, fraction 7 is NaN, and
there is no infinity code. E8M0 scale s denotes 2^(s-127); s=255 is invalid.
Decode the exact value and scale, then RNE to BF16, propagating conversion
overflow/underflow/inexact. NaN codes are quiet; invalid scale sets invalid.
Stored BF16 bits are never modified on the BF16 path.

Generated-fixture quantization remains independently owned by Verifier:
smallest power-of-two scale covering the group's finite maximum, RNE to an even
code, preserved zero sign, and explicit saturation/metadata/padding accounting.
Arithmetic error on decoded operands is distinct from quantization drift
against original BF16 operands.

## Fast inverse square root

`anvil_q1_fp2_fast_rsqrt` has `clk,rst_n,in_valid,x[31:0]` inputs and
`out_valid,result[31:0],status[4:0]` outputs. No backpressure is supported;
the fixed two-stage II=1 contract is counted in the table above.

For positive finite x, normalize x=n*2^(2q), with n in [1,4).
The 2048-entry ROM index is normalized exponent parity plus ten high fraction
bits. The source-local constant function `newton_entry` reproducibly constructs
each entry at its interval midpoint: the actual magic seed is
`0x5f3759df-(normalized_bits>>1)`, followed by exactly one Newton update
y0*(1.5-0.5*n*y0*y0). Fixed-point Q30/Q32/Q31 integer arithmetic constructs
the ROM at elaboration; there are no runtime correction multipliers or
iterative divide/sqrt engines. The second stage rescales the stored FP32 y1
by 2^-q. Normalizing subnormal inputs uses their actual leading significand
bit, not flush-to-zero.

Zero returns signed infinity with divide-by-zero; negative nonzero (including
-infinity) returns canonical NaN with invalid; +infinity returns +0; NaN is
canonical with invalid only for signaling NaN. Approximate positive results
report inexact. The <=0.0025 relative-error threshold, all interval endpoints
and midpoints, exponent boundaries and physical two-stage timing are **pending
independent verification**, not established by the table construction.

## Fundamental FP32 arithmetic

`anvil_q1_fp2_fp32_binary` supplies exact-RNE add (`MULTIPLY=0`) and multiply
(`MULTIPLY=1`) with `clk,rst_n,in_valid,in_ready,out_ready,a[31:0],b[31:0],
out_valid,result[31:0],status[4:0]`. It has nine registered stages, accepting
at k and first asserting its result after k+8. It uses exact signed 576-bit
integers in units of 2^-298, sufficient for the entire finite FP32 product
range and exact addition. Only the final FP32 packing rounds. All IEEE
special values, signaling NaNs, signed zeros, overflow and gradual underflow
follow the common status/rounding contract. Exact add cancellation returns +0;
multiplication of finite zeros preserves the XOR sign.

This deliberately shared exact implementation is not yet integrated into
the command engines. Like the tensor, its physical cost/timing is unmeasured.

## DDR4 application-side channel

The 512-bit channel carries one aligned 64-byte beat per accepted request, and
exactly one response per read or write. The physical controller and PCIe bridge
are external. Preserve parent kind/layer/projection identities. Lane zero is in
the least-significant bits. At most two one-bit IDs are outstanding; never reuse
an ID until its response has retired. The ping-pong implementation conservatively
retains the ID through consumer retirement as well.

Internal `anvil_q1_fp2_ddr_pingpong` accepts a complete descriptor with fields
write/scale/kind/layer/proj/row/col/tag/wdata/wstrb. It queues two descriptors,
issues them in order, captures responses by ID into separate actual 512-bit
buffers, and retires them in descriptor order. `out_tag` recovers the submitted
controller context. Write acknowledgments use the same path. A full buffer can
retire and refill concurrently without overwriting the old public response.

Each floating tensor row is padded independently to a full beat:
BF16 col=32*b and element i is bits 16*i+:16; MX col=64*b and element i is
bits 8*i+:8. Padding elements are zero and must be masked out of arithmetic.
The separate scale plane packs 64 consecutive E8M0 bytes per beat; its col is
the first logical group index (64*b), not the first data element. The last scale
beat is zero padded. Independent weights and activations have independent scale
planes. A partial write uses byte strobes only for valid stored elements.
Metadata-inclusive traffic includes full fetched scale/data beats and repeated
transfers. The full-group MX payload alone is one-half dense BF16 payload;
scale-inclusive dense comparison is not exactly one-half.

DDR stall events are qualified by actual useful optimized work. The ping-pong
leaf reports request backpressure, or an explicitly needed head response still
in flight; returned data stalled solely by its consumer does not count.
The decoder must supply `work_active` and `result_needed` correctly.

## Parent logical memory ABI

The actual source mapping, retained for scalar compatibility, is:

| Kind | Meaning | Row | Column |
|---:|---|---|---|
| 0 | Shared embedding / output-head FP16 or native-16 weights | token or vocabulary ID | hidden component |
| 1 | Packed AWQ weights | input component | output component >> 3 |
| 2 | Packed AWQ zeros | input group index | output component >> 3 |
| 3 | AWQ FP16 scale | input group index | output component |
| 4 | Projection bias | 0 | output component |
| 5 | Input RMSNorm gamma | 0 | hidden component |
| 6 | Post-attention RMSNorm gamma | 0 | hidden component |
| 7 | Final RMSNorm gamma | 0 | hidden component |
| 8 | FP32 or compatibility-Q16 scratchpad | slot | component |
| 9 | K history | token position | KV head*HEAD_DIM + component |
| 10 | V history | token position | KV head*HEAD_DIM + component |
| 11 | RoPE cosine/sine | position | 2*pair + (sine ? 1 : 0) |
| 12 | Native floating projection weight | input component | output component |

Gamma requests use proj zero and row zero, with the actual layer for kinds 5/6
and layer zero for kind 7. GEMV uses actual layer and projection; parent embedding,
scratchpad and RoPE requests use layer/proj zero. Histories use the actual layer,
proj zero. The top must preserve these distinctions.

Projection IDs are Q=0, K=1, V=2, attention output=3, gate=4, up=5, down=6.
Their scratchpad source/target slots are 1->2, 1->3, 1->4, 5->6, 8->9,
8->10 and 11->12 respectively. Scalar AWQ eight-lane packing remains unchanged.
Scratchpad slots are 0 layer input/residual, 1 first-normalized input, 2 Q,
3 K, 4 V, 5 attention output, 6 projected attention, 7 attention residual,
8 second-normalized input, 9 gate, 10 up, 11 SwiGLU product, 12 down,
and 14 final-normalized input. The first residual is slot0+slot6 -> slot7;
the second is slot7+slot12 -> slot0. Input norm is slot0 -> slot1,
post-attention norm slot7 -> slot8, and final norm slot0 -> slot14.

## Telemetry

`anvil_q1_fp2_telemetry_csr` uses the top CSR request/response channel, actual
DDR/alignment/epilogue/ULP event inputs, and `active`/`error_event` from control.
Status active is the controller's actual active state; status error is sticky
architectural error, not a malformed CSR transaction. Malformed requests change
no configuration, counter, snapshot or error state. Unrelated real events may
still update counters on the same edge.

Counters are unsigned saturating 64-bit values. `COUNTER_BITS=64` is the
production default; 1..64 is a leaf-only verification parameter limiting the
saturation value, without adding production preload CSRs. Each clear resets
both live counters and snapshots; counting enable itself follows the written
bit 0. Enable changes take effect after their accepted write edge: events on
that edge see the pre-edge enable.

| Address | Access | Meaning |
|---|---|---|
| 0x000 | RO | Version 0x02020002 |
| 0x004 | RW | bit0 enable; W1 bit1 clear; W1 bit2 snapshot |
| 0x008 | RO | bit0 active; bit1 sticky error; bit2 any saturated counter |
| 0x020/024 | RO | Snapshot DDR stalls low/high |
| 0x030/034 | RO | Snapshot alignment events low/high |
| 0x040/044 | RO | Snapshot epilogue bubbles low/high |
| 0x050/054 | RO | Snapshot ULP-distance sum low/high |
| 0x060 | RO | Snapshot maximum finite ULP distance |
| 0x068/06c | RO | Snapshot finite sample count low/high |
| 0x070/074 | RO | Snapshot nonfinite sample count low/high |

Misalignment, unmapped access, read-only writes and strobed reserved-bit writes
produce an error response and no control side effects. Byte strobes apply only
to selected bytes. Snapshot is atomic and captures pre-increment counter values.
Counter reads initially return zero and subsequently use the most recent
snapshot; they never snapshot implicitly.

Hardware ULP distance means finite ordered-FP32 encoding distance for an actual
FP32->BF16->FP32 round-trip. `ulp_valid` marks an actual sample. Distance
0xffffffff is reserved as a nonfinite-event sentinel (finite round-trip
distances cannot reach it); these samples increment only the nonfinite counter.
Hardware does not claim an unavailable mathematical-oracle answer. The
controller must generate these events at real conversion handshakes.

## Remaining numerical and integration requirements

The following admitted requirements remain mandatory and are not implemented
by merely instantiating the existing leaves:

* Fused commands: RMSNorm gamma*x*rsqrt(mean(x*x)+0x358637bd), theta=1e6
  split-half RoPE from deterministic kind-11 FP32 coefficients, stable monotone
  SwiGLU up*gate*sigmoid(gate), and exact-RNE FP32 residual add.
* Online attention: FP32 running maximum/sum/output, empty-state special case,
  exp rescaling for each chronological tile, one final normalization, no score
  matrix and no second KV pass. GQA must reuse a single KV traversal across
  query heads sharing a KV head.
* Actual decoder dependency graph: input norm, Q/K/V, RoPE, causal attention,
  output projection, residual, second norm, gate/up/SwiGLU/down, residual,
  final norm and output head. Optimized weights/KV use DDR, not scalar fallback.
* Internal vector RAM/registers are allowed; external intermediate SRAM
  materialization between fused optimized operators is not. Full checkpoint
  weights and KV history remain external.
* Fatal invalid/divide-by-zero/overflow must terminate a token without a
  successful partial logit stream afterward.

Required componentwise bounds are RMSNorm 0.005, RoPE 0.0005, SwiGLU 0.002,
attention 0.003, and architectural decoded-weight logits 0.02, each multiplying
max(1,abs(reference)). Fundamental FP32 add/multiply/conversions and required
legacy comparisons are bit-exact. Exp on [-80,0] requires relative error
<=0.0005; values below -80 may become zero with explicit error accounting.
MX quantization drift is reported separately.

## Independent acceptance and reproduction

The unchanged required entry points, to be implemented by Verifier, are:

```sh
python3 tests/verify.py --suite behavior --seeds 17,29,71
python3 tests/verify.py --suite benchmark --seeds 17,29,71
python3 tests/verify.py --suite sensitivity
python3 tests/verify.py --suite synthesis
python3 tests/verify.py --suite portable
```

They must execute real Icarus/Verilator behavior, independent exact/high-precision
references, deliberate compiling defect mutations, Yosys synthesis with zero
latches/div/mod and connected substantive hierarchy, and fresh clean-directory
portable reproduction. They are not yet present and have not run.

Coverage remains: at least 4096 groups per tensor format, all E4M3 codes and both
scale groups, directed BF16 boundaries/cancellation/masking/rounding; at least
256 vectors per epilogue operation; at least 64 attention queries for each of
TILE_TOKENS=1,3,16; all three mandatory seeds across compact and multi-head
geometries, legal modes, continuation/reset/faults/backpressure and required
default-dimension nontrivial token execution.

Production-width five-domain matched benchmarks must be strictly faster in
every domain and aggregate, with cold/warm costs separated. Post-fit ALMs per
active FP tensor lane must decrease by >45%, with complete tail/control resource
accounting; aggregate cycles/ALM and cycles/DSP efficiency must improve. Actual
MX off-chip traffic must decrease by at least 50% against the matched parent,
including scales/padding/repeats. Nominal lane count, generic cells and
payload-only ratios are not proof.

Shared-runtime timing lint, authoritative Quartus 17.1 STA (WNS>=0 at 10 ns)
and physical Arria 10 PCIe Gen3x8 HIL with three consecutive deterministic passes
remain separate mandatory gates. No local cable/BDF, credentials, private paths,
runtime transcript or final-report prerequisite belongs in shipped sources.
