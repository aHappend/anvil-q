# Anvil-Q1-FP2 v2.2.0-fp2-bfp-fused

## Status and authority

This is the design-side implementation contract, not a verification or acceptance
report. The admitted work order remains authoritative. The design handoff now
includes the integrated top, decoder schedule, tiled projections, KV writer,
shared-GQA traversal and actual datapath telemetry connections, in addition to
the arithmetic/operator leaves. Independent functional and physical verification
is pending. No numerical, performance, synthesis, timing or board result is
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

The top is `anvil_q1_fp2_top`, with the parent parameter order:

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
| Exp accept at k | Capture signed Q24 argument and special-value classification. |
| Exp k+1..k+7 | Signed base-2 reduction, five Horner registers, then RNE packing; first valid result after k+7, II=1. |
| Reciprocal accept at k | Synchronous reads of two adjacent normalized ROM endpoints, fraction and exponent capture. |
| Reciprocal k+1..k+5 | Difference, interpolation product, interpolated value, RNE preparation, then valid result, II=1. |
| MX quantizer accept at k | Capture operand/mask and masked finite magnitudes. |
| MX quantizer k+1..k+5 | Five registered pairwise maximum levels, independently for each Group-32. |
| MX quantizer k+6 | Capture the two E8M0 scales and delayed original operands. |
| MX quantizer k+7 | Per-lane RNE encoding and flags. |
| MX quantizer k+8 | Registered balanced status/count reduction and matching code/scale payload; II=1. |

The implemented command engines use the following transfer-based contract;
their compute states are described below. Integration must preserve it rather
than assuming continuously ready endpoints:

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
This leaf retains exactly its single magic-seed Newton update. RMSNorm adds
the separate bounded residual-polynomial refinement described below; it does
not change the leaf's result, latency, interface or special-value rules.

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

This shared exact implementation supplies the epilogue and attention arithmetic
boundaries. Like the tensor, its physical cost/timing is unmeasured.

The package also provides `uint32_to_fp32` and `fp32_to_bf16`. Integer conversion
uses RNE, including integers exceeding 24 significant bits. FP32-to-BF16 returns
`{status[4:0],value[15:0]}`, preserves signed zeros and infinities, canonicalizes
NaNs with signaling detection, and reports overflow, inexact and after-rounding
underflow. These are implementation helpers, not independent references.

## Nonlinear arithmetic support

`anvil_q1_fp2_exp` has `clk,rst_n,in_valid,x[31:0]` inputs and
`out_valid,result[31:0],status[4:0]` outputs. Its eight registered stages
have no output backpressure. Input bubbles produce invalid zero public payloads.
The finite supported interval is [-80,80]; attention and stable sigmoid use
only [-80,0]. Finite inputs below -80 return zero with inexact, an intentional
tail approximation whose impact must be included in independent error reports.
Finite inputs above +80 return infinity with overflow/inexact, a range error,
not a claim that exp(81) is an IEEE overflow. Infinities have their mathematical
exp results; NaNs follow the canonical/signaling policy; either zero returns 1.

Finite conversion captures x in signed Q24. Multiplication by Q30
`1549082005` approximates log2(e); arithmetic floor extraction obtains the signed
integer exponent and a Q30 fraction in [0,1). A degree-six Horner approximation
to 2^fraction uses the checked-in integer coefficients
`1073741824,744261118,257941248,59597083,10327387,1431680,165394`,
representing RNE Q2.30 values of ln(2)^j/j!. A separate final stage rounds
the significand ties-to-even and applies the exponent. The required <=0.0005
relative error and monotonicity remain independent verification obligations.

`anvil_q1_fp2_reciprocal` uses the same fixed-pipeline ports and six registers,
with first valid after k+5. It is an approximate reciprocal for nonlinear
normalization, not a correctly rounded IEEE divide primitive. Positive
significands are normalized into [1,2), including input subnormals. Two
1024-word synchronous ROMs supply adjacent Q1.31 values of 1/(1+i/1024).
The source-local `endpoint` constant function generates every endpoint by
bounded integer long division, without runtime division or a file dependency.
Ten fraction bits select an interval; the remaining thirteen interpolate its
endpoints in registered subtract/multiply/subtract stages. Separate RNE
preparation and packing provide gradual output underflow and overflow.
Finite approximate results conservatively report inexact. Zero returns signed
infinity with divide-by-zero; infinity returns signed zero; NaNs follow the
common canonical/signaling policy. Numerical error is not yet measured.

## Group-32 quantization support

`anvil_q1_fp2_mx_quantize` accepts `clk,rst_n,in_valid,bf16_data[1023:0],
lane_mask[63:0]`; outputs are `out_valid,mx_data[511:0],scales[15:0],
status[4:0],saturation_events[6:0]`. It has no output backpressure and its nine
register stages produce first valid after k+8. Output payload/status/counts
are zero when invalid or reset.

Each group independently selects its largest active finite BF16 magnitude
through five registered comparator levels. With leading exponent e and
normalized eight-bit significand t, the minimal unconstrained scale exponent
is e-8 when t<=224, otherwise e-7: 224/128 is the 1.75 significand of the
maximum E4M3FN magnitude 448. The scale exponent is bounded below by -127
(E8M0 zero). A finite BF16 group never needs a scale beyond E8M0 254. An
empty/all-zero group uses scale byte zero. No inactive lane affects scale,
status or saturation, and its output code is zero.

Per-lane integer shifts implement RNE with ties to an even code, including
subnormal-to-normal carries and exponent carries. Zero sign is preserved.
Nonzero discarded bits set inexact; after-rounding subnormal inexact codes
also set underflow. Quiet NaN maps to code 0x7f; signaling NaN additionally
sets invalid. Infinity saturates to signed maximum finite code, increments
saturation_events and sets overflow/inexact. Any finite-code saturation is
also counted and inexact. Independent arithmetic checks must decode these
codes/scales afresh and include that BF16 decoding's own flags: quantization
is not permission to hide a later decode overflow. The module is not yet
connected to architectural activation/KV storage or telemetry.

## Fused epilogue command engine

`anvil_q1_fp2_epilogue_fusion` implements the frozen leaf ports, with parameters
`MAX_VECTOR=4864,HEAD_DIM=64,MAX_POS=32768`. MAX_VECTOR and MAX_POS must be
positive; HEAD_DIM must be positive, even and at least two. All commands require
1<=cmd_len<=MAX_VECTOR. RoPE additionally requires cmd_pos<MAX_POS and a length
that is a positive whole number of heads. The length check enumerates constant
head multiples at elaboration; it creates no runtime remainder operator.

The engine accepts a complete vector before computing, using bounded internal
synchronous data/auxiliary/residual RAM. RMSNorm issues independent squares
at one component per clock into the existing result RAM, then reads those
rounded squares for the original component-order, serial FP32 sum. After
mean/epsilon and fast-rsqrt, its two multiplier pipelines run concurrently:
the first computes x*factor and the second consumes that rounded result with
the corresponding gamma, delayed by nine registers. Input bubbles cannot
misalign gamma because this pass reads the already collected vector. The
result RAM's square contents are dead before normalized outputs overwrite
them; no additional vector RAM or external intermediate transfer is required.
RoPE reads each split-half pair, then issues its two rotations on consecutive
edges through both multipliers. The adder consumes rounded products while later
pairs are being read and issued. Eighteen address/subtraction tag registers
preserve first/second-half destination ownership across both arithmetic stages.
SwiGLU streams exp, denominator add, reciprocal and negative-sigmoid multiply
at initiation interval one, storing selected sigmoid values in result RAM.
Fifteen exp-delay registers, nine reciprocal-delay registers and a 32-stage
sign tag preserve the operand pairing. The positive branch bypasses the
negative-sigmoid product and its flags. After that pass fully drains, a second
stream reads gate/sigmoid/up and cascades the existing two multipliers at
initiation interval one. Sigmoid locations are read before result overwrites.
Residual add likewise streams one collected component per edge.
The engine writes the completed vector to that internal result RAM and then
streams it in original component order. There
are no external intermediate SRAM transfers. `in_last` must coincide exactly
with input index cmd_len-1, including singleton commands. A framing violation
terminates with an error completion and no output vector.

| Op | Operand routing and FP32 boundaries |
|---:|---|
| 0 | RMSNorm: square every x, add squares in component order starting at +0, multiply sum by reciprocal(FP32(cmd_len)), add epsilon 0x358637bd, call the named two-stage `fast_rsqrt`, refine its finite positive result with the residual polynomial below, multiply each x by the refined factor, then multiply by stored in_aux gamma. Every add/multiply is an independent FP32 RNE boundary. |
| 1 | RoPE: within each split-half head, in_aux for first-half component j is cosine and in_aux for second-half component j+D/2 is sine. Compute x*cos-y*sin and y*cos+x*sin with four FP32 products and two FP32 sums. |
| 2 | SwiGLU: e=exp(-abs(gate)), r=reciprocal(1+e); sigmoid is r for a nonnegative gate and e*r for a negative gate. Compute (gate*sigmoid)*in_aux, with in_aux the up projection. Finite tails saturate sigmoid at the exp range limit. For negative infinity the swish factor is its limiting -0 before multiplication by up, avoiding infinity*zero. |
| 3 | Residual: exact-RNE add of in_data and in_residual. |

RoPE coefficients must come from the deterministic FP32 kind-11 table for
`cos(pos*1000000^(-2*j/HEAD_DIM))` and the matching sine. cmd_pos labels and
bounds that supplied table row; this streaming leaf does not fabricate a
coefficient table or independently check trigonometry. The unfinished decoder
must fetch the correct row and route each coefficient to the stated in_aux
position. Arbitrary fixture-specific coefficients are not an integration option.

Arithmetic status is OR-reduced across all component operations and accompanies
each stable output and completion. Command/framing errors assert error with
done. Arithmetic special results retain their common IEEE flags; the decoder
must treat fatal flags as token failure. No performance is inferred from this
buffered schedule.

| Engine boundary | Implemented edge/state sequence |
|---|---|
| Command at k | COLLECT after k; no input transfer before this state. |
| Bad command at k | ERROR_WAIT0 after k, ERROR_WAIT1 after k+1, FINISH with done/error after k+2. No input readiness in these states. |
| Final RoPE input at t | READ_X after t; read/latch first-half x/cos at t+1/t+2 and partner y/sin at t+3/t+4. Issue first/second rotations at t+5/t+6. Later pairs issue every six edges without waiting for arithmetic results. |
| RoPE pair completion | For a rotation issued at p, accept its rounded products in the adder at p+9 and write its destination at p+18. The final write, not the final issue, enters OUT_READ. HEAD_DIM=2 uses the same first/second issue and drain sequence; no pair-index wrap shortcut. |
| Final RMSNorm input at t, length n | RMS_SQUARE after t; read component zero at t+1, accept its square at t+2, write its rounded result at t+11. Consecutive squares issue every edge; the final write at t+n+10 enters READ_X for ordered reduction. No public output is yet valid. |
| RMSNorm singleton reduction | For n=1, write its square at t+11, read/latch that square at t+12/t+13, accept +0+square at t+14 and capture the rounded sum at t+23. Mean, epsilon and fast-rsqrt follow their existing issue/wait boundaries. |
| RMSNorm factor refinement | After fast-rsqrt capture at r, the eight registered add/multiply operations below capture at r+10, r+20, ..., r+80. They accept no vector inputs and emit no outputs. Finite positive inputs then enter RMS_NORMALIZE. Exceptional/zero factors bypass refinement, preserving their status and IEEE operand behavior. Reset aborts every step. |
| RMSNorm normalization | After refined-factor capture at f (r+80 for the finite path, r for bypass), read component zero at f+1, accept x*factor at f+2 and accept the rounded product*gamma at f+11. Write its result at f+20; consecutive results write every edge. Only the final write enters OUT_READ, so aggregate status is fixed before public output. |
| RMSNorm pass ownership | Read counters stop at n; only registered read-valid cycles issue multipliers. Result-write counters advance only on the corresponding multiplier's out_valid. n=1 and non-power-of-two n use these same comparisons, never binary wrap. Reset invalidates all pipeline validity and counters. |

For RMSNorm only, let z be the rounded mean plus epsilon and y the unchanged
fast-rsqrt output. Normalize z=n*2^(2q), n in [1,4), and scale y to
v=y*2^q by exact exponent adjustment. The existing FP32 units execute, in order:
t0=RNE(v*v), t1=RNE(n*t0), r=RNE(1-t1),
t2=RNE(0.375*r), t3=RNE(0.5+t2), t4=RNE(r*t3),
c=RNE(1+t4), factor=RNE(y*c).
Constants are FP32 0x3ec00000, 0x3f000000 and 0x3f800000.
This is the degree-two binomial residual correction
(1-r)^(-1/2) approximately 1+r/2+3*r*r/8, not another Newton update,
iteration or divide/sqrt engine. Normalized operands avoid overflow or
subnormal loss in the residual computation across the positive finite range.
Its purpose is to reduce rsqrt bias and midpoint discretization before BF16/MX
requantization, whose code boundaries can amplify otherwise legal leaf error.
All correction flags join the command status; no correction intermediate
overwrites vector RAM or changes input/output backpressure semantics.
Independent numerical and performance checks must establish the repaired
architecture's accuracy and the additional fixed 80-edge per-command cost.
| Stalled final input | Remain COLLECT, preserving count and memories until its actual transfer. |
| SwiGLU sigmoid pass | After final input t, read component zero at t+1, accept exp at t+2, denominator add at t+10, reciprocal at t+19 and negative-branch product at t+25. Write the selected sigmoid at t+34. Each subsequent component follows one edge later; final write at t+n+33 starts the product pass. Positive components use the delayed reciprocal and exclude the unused product's flags. |
| SwiGLU product pass | After final sigmoid write r, read gate/sigmoid/up at r+1, accept gate*sigmoid at r+2 and its rounded product*up at r+11. Write at r+20; consecutive results write every edge. Singleton n=1 follows both passes, with first public output after t+56. |
| Stream pass ownership | SwiGLU and residual read counters stop at n, including n=1 and non-power-of-two lengths. Only registered read-valid cycles issue the first operator. Completion counts final operator valid results; each pass drains before changing ownership. Reset invalidates every arithmetic pipeline and read-valid tag. |
| Singleton residual | After final input t, read at t+1 and accept add at t+2; add result is valid after t+10, captured and written at t+11. OUT_READ and OUT_LATCH lead to first public output after t+13. Longer residual vectors issue/write consecutive components every edge. |
| Output RAM fetch | OUT_READ obtains synchronous result_q, OUT_LATCH captures payload, OUTPUT holds it. No speculative output index advance. |
| Stalled final output | Remain OUTPUT with payload, last and status unchanged; done stays low. |
| Final output at f | COMPLETE_WAIT after f, FINISH/done after f+1, IDLE after f+2. |

## Single-query tiled online attention

`anvil_q1_fp2_flash_attn` implements the frozen leaf ports and parameters
`HEAD_DIM=64,TILE_TOKENS=16,MAX_SEQ_LEN=32768`. HEAD_DIM and MAX_SEQ_LEN are
positive, and every TILE_TOKENS in 1..16 is legal, including 3. Commands require
1<=cmd_len<=MAX_SEQ_LEN. There is one query load per command, exactly HEAD_DIM
accepted BF16 components with q_last on the final component.

After query loading, synchronous local K/V tile RAM accepts token-major pairs
at II=1 in FILL. kv_last marks each complete HEAD_DIM vector, not the end of
the whole prefix. A tile contains min(TILE_TOKENS, remaining prefix) tokens.
No more KV is accepted while that tile is computed. Only the current tile,
query vector, running FP32 output vector and scalar running state are stored;
there is no full score/probability matrix or complete-history allocation.
Each external K/V pair is accepted once, and no second prefix traversal occurs.

For each token in chronological order, products and additions form the FP32
dot in component order. Its score is multiplied by constant
RNE_FP32(1/sqrt(HEAD_DIM)). `head_scale`, used only to elaborate that constant,
constructs it with 128-bit constant integer quotient and bounded integer square
root followed by RNE. Its constant quotient is not a runtime divider.

The initial state is m=-infinity,l=0,o=0. The first score sets m directly and
selects alpha=0,p=1 without evaluating infinity-infinity. Later scores select
m'=max(m,s), form the two FP32 differences and parallel exp results, then
update l=RNE(alpha*l+p) and every o[j]=RNE(RNE(alpha*o[j])+RNE(p*v[j])).
The next token cannot overwrite an output component before that update
completes. After the last token the scalar reciprocal of l is computed once;
each final FP32 o[j]*reciprocal(l) is streamed with backpressure.

Fatal arithmetic flags terminate the command with error; a nonfinite score is
invalid for this finite online normalization path. Underflow/inexact remain
observable and nonfatal. Status is accumulated and held stable with a stalled
output. All tile settings use the same chronological per-token FP32 operation
order; changing the tile partition changes intake scheduling/storage, not the
numerical reduction order.

| Attention boundary | Implemented edge/state sequence |
|---|---|
| Command at k | QUERY after k; only a bad command takes the two-edge error path. |
| Final query input at q | FILL after q; no KV transfer is accepted earlier. |
| Final KV component of a full/final tile at t | DOT_READ after t, synchronous query/key read at t+1, first dot multiply accepted at t+2. |
| Singleton token, including TILE_TOKENS=1 | The first KV vector closes its tile and uses the empty-state special case; it is not mistaken for an empty prefix. |
| Partial last tile | Close on processed+filled_tokens==cmd_len, without waiting for a full tile. |
| Stalled query/KV final component | No component, tile or token count advances before transfer. |
| Tile update complete | Reuse tile RAM only after all of its tokens have updated m,l,o. |
| Final normalization result | Capture in NORMALIZE_WAIT and enter OUTPUT. |
| Stalled final output | Keep payload/last/status in OUTPUT; no new query/KV acceptance or completion. |
| Final output at f | COMPLETE_WAIT after f, FINISH/done after f+1, IDLE after f+2. |
| Bad command at k | ERROR_WAIT0 after k, ERROR_WAIT1 after k+1, FINISH/done/error after k+2. |

This leaf handles one query head. The shared GQA group and chronological K/V
intake primitives below implement broadcast ownership, but are not yet wired
into an architectural top. Re-reading the external KV prefix once per query
head remains prohibited.

### Shared query-group control

`anvil_q1_fp2_gqa_group` has parameters GROUP_HEADS=7, HEAD_DIM=64 and
MAX_SEQ_LEN=32768, all positive. GROUP_HEADS*HEAD_DIM and
MAX_SEQ_LEN*HEAD_DIM must fit unsigned 32-bit component indexing. Its command
is `cmd_valid/cmd_ready/cmd_len`, with 1<=cmd_len<=MAX_SEQ_LEN. The decoder is
responsible for selecting the correct KV-head group and causal prefix.

Queries enter on `query_valid/query_ready/query_data[15:0]/query_last`, in
head-major order, with exactly HEAD_DIM BF16 components per head. query_last
marks each head's last component. K/V enter on
`kv_valid/kv_ready/k_data[15:0]/v_data[15:0]/kv_last`, in chronological token-major
order, with kv_last marking every HEAD_DIM-component vector. The group accepts
exactly cmd_len vectors once, independently of GROUP_HEADS.

The internal engine interface exposes GROUP_HEADS command/query/KV/output/done
channels. All packed data/status buses are low-head-first; data for head h is
bits 32*h+:32 and flags are bits 5*h+:5. Query and KV payloads are shared buses
with individually qualified valid bits. A per-head accepted mask holds each KV
pair until all siblings consume it. A fast sibling cannot consume a pair twice.
The consumer must connect one real attention leaf per head, with the same
HEAD_DIM, MAX_SEQ_LEN and TILE_TOKENS. Sibling reset is `engines_rst_n`, not
unconditionally rst_n: a group error aborts all leaf commands synchronously.

Group outputs are `out_valid/out_ready/out_data[31:0]/out_head[31:0]/
out_component[31:0]/out_last`, in head-major order. out_last marks the final
component of the final head. Per-head synchronous output RAM and remembered
completion pulses prevent output from any head until every sibling completes
successfully. `status[4:0]` accumulates all sibling flags. Command/input/output
framing violations and invalid/divide-by-zero/overflow flags produce an error
completion and abort siblings. This internal group is not a replacement for
whole-token error/logit ownership.

| Group boundary | Implemented behavior |
|---|---|
| Legal command at k | START after k; issue each sibling command until its own acceptance, then begin queries. No query or KV acceptance at k. |
| Invalid command at k | ERROR_WAIT0 after k, ERROR_WAIT1 after k+1, FINISH/done/error after k+2. No operand acceptance. |
| Final query of final head at q | KV after q; the first KV pair may transfer at q+1. |
| KV pair accepted at t | The holding register is valid after t; first sibling transfers are at t+1 or later. Each sibling transfers exactly once. |
| Differing sibling readiness | Retain payload/last and the accepted mask; suppress valid only for siblings that already transferred. |
| All siblings transfer the held pair at b | Release after b. Refill occurs no earlier than b+1, including a one-head group. |
| Final KV pair | Stop upstream intake immediately; wait for its broadcast and every sibling result/completion. |
| Sibling results | Independent per-head banks capture concurrent outputs; extra components or incorrect last are errors, never silently dropped. |
| Group result fetch | READ_RESULT performs the synchronous bank reads, LATCH_RESULT captures the selected head, OUTPUT holds the public payload. |
| Final output transfer at f | COMPLETE_WAIT after f, FINISH/done after f+1, IDLE after f+2. |
| Singleton head/vector | The first query/KV/output component is also last when HEAD_DIM=1; it follows the same ownership schedule. Architectural geometry retains the parent's even-head constraint. |
| Group fault | No result stream starts; drive sibling reset low, clear held KV validity and complete through ERROR_WAIT0/1. Reset remains asserted for siblings until the group returns idle. |

### Chronological DDR K/V intake

`anvil_q1_fp2_kv_reader` has HEAD_DIM=64 and MAX_SEQ_LEN=32768 parameters.
Its command contains format_mx, layer, first and len; first is the logical
KV-head offset in each history row, not a byte address. len is the positive
causal token count, bounded by MAX_SEQ_LEN. first+HEAD_DIM must not exceed
2^32, evaluated at 33-bit width. Every token reads kind 9 then kind 10 at
row=token index, proj=0, layer=cmd_layer, with the same first/HEAD_DIM slice.

K components are retained in a synchronous HEAD_DIM-word BF16 RAM. V components
pair with the matching registered K and stream on
kv_valid/kv_ready/k_data/v_data/kv_last. The component pointer changes only on
pair acceptance. READ_KEY supplies a complete registered-read edge before each
PAIR state, including component zero and non-power-of-two head dimensions.
kv_last marks each vector, not only the final causal token. The next token's
K command starts only after the preceding V command completes. No whole-history
RAM, score matrix or query-head-specific reread is used.

This block instantiates `anvil_q1_fp2_ddr_read_stream`. The generic reader accepts
kind/layer/proj/row/first/len/format_mx and emits decoded BF16 components with
per-command accumulated conversion status. It rejects zero length and a 33-bit
first+len greater than 2^32 before issuing any descriptor. Tensor-specific row
bounds remain the decoder's responsibility, not a silently clamped reader limit.

The descriptor side is `fetch_valid/fetch_ready/fetch_scale/fetch_kind/
fetch_layer/fetch_proj/fetch_row/fetch_col/fetch_tag`. Every descriptor is a read;
integration ties write/data/strobes to zero at the ping-pong command port.
Responses contain valid/ready/tag/write/error/data. Connect these to the
ping-pong's ordered retirement channel, not directly to unordered physical
responses. A client exclusively owns this channel until its done completion;
the integrated decoder selects one client through that client's completion.
Embedding, projection, history write and history read commands cannot overlap
on this ordered retirement channel. Within a read command both physical slots
can prefetch concurrently.

For BF16, align the first descriptor down to 32 elements and issue subsequent
32-element beats. For MX, align down to 64 elements; before each 2048-element
segment, fetch and cache the aligned 64-byte scale-plane beat, whose col is the
first Group-32 index. Data descriptors then advance by 64 elements. A command
may start partway through either a data beat or scale segment. Select each
scale by absolute element bits 10:5, so a Group-32 transition within a beat
cannot inherit its neighbor's scale. Independent K/V rows load independent
scale planes.

The reader prefetches into both existing ping-pong slots while the consumer
drains a returned beat. It retires a data response only after its last requested
component transfers; final padding is not exposed or included in conversion
flags. It does not issue data beyond the current scale segment. After the last
response of a segment retires it can replace the cached scale plane safely.
An error response, unexpected tag/write acknowledgment or fatal MX/BF16
conversion flag terminates the command. Already accepted requests and a
previously offered stalled descriptor are drained before error completion.
The consumer never receives data from the failing response.

| Read-stream boundary | Implemented behavior |
|---|---|
| Legal command at k | DATA after k for BF16, SCALE after k for MX; no response is assumed present. |
| MX scale request/response | Hold the descriptor until accepted; WAIT_SCALE captures its response before any associated data descriptors issue. |
| Data response held | Response payload/ID remain owned by ping-pong while individual components transfer; a second slot can issue or return concurrently. |
| First/last in same beat | Skip prefix elements, expose exactly len components, and retire on the final component; never require another beat to complete a singleton. |
| Final output stalled | Keep decoded data, last, status, cursor and cached scales stable; do not retire the response. |
| Final data transfer at f | COMPLETE_WAIT after f, FINISH/done after f+1. |
| Invalid command at k | Error completion after k+2 with no descriptors. |
| Response fault | Drain outstanding ownership; only then enter the two-edge error completion path. No new command is accepted during draining. |
| Reset | Abort the stream and clear cursors/counters/scale validity; the common ping-pong/bridge reset must also discard the previous epoch. |

The reader's work_active/result_needed outputs describe real transport
ownership and consumer demand for connection to ping-pong stall telemetry.
No constant synthetic event source is used. The integrated decoder routes the
selected client's work_active/result_needed to the ping-pong stall detector.

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
The decoder supplies `work_active` and `result_needed` from the selected reader
or writer. Computation without outstanding transport, idle clocks and downstream
output stalls alone do not contribute.

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
controller generates these events at real projection-input, KV-write-input and
query-input conversion handshakes. Those operations are mutually exclusive;
there is no priority mux that drops simultaneous conversion samples.

## Integrated decoder and numerical boundaries

The direct top instances are `tensor_array`, `epilogue_fusion`, `flash_attn`
(query-group head zero) and `telemetry_csr`. Other attention siblings, the
query-group controller, `ddr_pingpong`, `decoder_control` and the immutable
`compatibility_decoder` are connected alongside them. The epilogue's direct
`fast_rsqrt` instance implements the required two-stage leaf.

`decoder_control` implements embedding -> (input norm -> Q/K/V projections ->
Q/K RoPE -> external K/V append -> shared-GQA causal attention -> output
projection -> residual -> second norm -> gate/up projections -> SwiGLU -> down
projection -> residual) repeated NUM_LAYERS times -> final norm -> shared
embedding/output head -> logits. All intermediate slots described above are
internal FP32 vector RAM, not external kind-8 transfers. The full weights and
KV history remain external.

Optimized scalar requests are reads of kind 4 (Q/K/V bias), kinds 5/6/7
(gamma) and kind 11 (RoPE); no optimized weight or history fetch uses scalar
transport. Bias and gamma retain the parent native BF16-in-low-halfword ABI,
including rejection of nonzero upper bits. Kind-11 coefficients are full FP32,
row=position, layer/proj=0. For each head, the coefficient stream supplies
cosine to the first half and sine to the second half using the original
interleaved pair table. The bridge/fixture must generate that table from
theta=1000000, not from arbitrary per-fixture constants.

`anvil_q1_fp2_projection` first accepts and caches its complete input vector.
Convert FP32 inputs to BF16 with RNE. In MX mode, quantize each independent
32-element activation group, decode its codes/scales to BF16, and retain those
decoded operands. Cache input groups for reuse across output tiles. A projection
tile contains up to 64 output columns and up to 64 input rows. Weight DDR
reads preserve kind-12 input-row/output-column orientation; each fetched row
has independent Group-32 scales across its output columns. The local transposed
tile feeds one 64-input reduction per output column into the tensor.

This orientation matters: the input-axis dot can cross 64 distinct weight-row
scales. Two tensor scale bytes cannot describe them. Consequently MX transport
is decoded once by the read engine, and architectural reductions use the
tensor's lossless BF16 operand port for those decoded weights and decoded
activations. They are not requantized into a different grouping or secretly
fetched as dense BF16. The standalone tensor's native MX port remains available
for matching Group-32 dot streams. Include decoder/quantizer/transposition costs
in area, cycles and traffic accounting, not just the tensor's tied-off MX port.

The output head uses kind 0, vocabulary row / hidden column orientation, and
the same activation cache and exact 64-input tensor reduction. Within each
projection, increasing input groups round once each to FP32 using the previous
group's FP32 result as acc_in. Q/K/V bias is added once after the entire dot;
the other projections and head have no bias, matching the parent graph.
Projection results, epilogue results and residuals remain FP32. Attention
queries are RNE BF16. K/V writes are RNE BF16 in mode 1 and Group-32 MX in mode 3;
history reads perform the specified MX-to-BF16 conversion before attention.

`anvil_q1_fp2_kv_writer` collects at most 64 components, quantizes if requested,
and issues acknowledged, byte-strobed data/scale writes. BF16 uses one or two
32-element beats; MX uses one 64-element data beat plus a scale-plane write.
Scale writes align to 64 scale bytes and strobe only the one/two updated scale
bytes, preserving neighboring groups. Final data bytes are strobed only for
valid elements; padding must never affect arithmetic. The writer waits for
each acknowledgment, including scale writes, before reusing its group buffer.
It does not claim two outstanding writes; read clients exercise concurrent
ping-pong prefetch.

One query group covers all query heads mapped to a KV head. For each KV head,
the controller supplies its contiguous head-major query group once and launches
exactly one chronological K/V reader with cmd_len=position+1. Group results go
to the corresponding internal attention-output slice. If the group fails,
drain the reader to release accepted DDR ownership before completing the token
with error. A history-reader error already drains its accepted descriptors.

All VOCAB_SIZE logits are retained in synchronous internal RAM until the entire
token has completed successfully. Only then is logit_valid exposed. A late
memory or arithmetic error discards that token's logical result validity;
there can be no earlier successful partial optimized logit stream. Operator
invalid/divide-by-zero/overflow flags are fatal at the controller boundary.
Underflow/inexact remain nonfatal and contribute to leaf status. Error
completion synchronously aborts local operator state; it does not annul or
reuse a live external DDR ID.

| Integrated boundary | Behavior |
|---|---|
| Token transfer at k | Latch token/position/precision/new-sequence. Child command starts after k; changes to token inputs while busy have no effect. |
| Reset | Reset ownership and sequence validity. External bridge discards old responses before releasing reset. With FP2 enabled, the first accepted token must request a new sequence at position zero. |
| New sequence | Position must be zero. Existing external history is logically invalid beyond the new causal prefix; each layer overwrites its current row before reading it. |
| Continuation | Require committed next_position and unchanged precision. A failed token invalidates continuation. |
| Compatibility configuration | ENABLE_FP2=0 delegates token/memory/error/mode behavior to the immutable parent, including mode-3 rejection; all DDR outputs are zero and DDR inputs are ignored. |
| Final operand stalled | Hold feeder x/aux/residual/last and index. No operation completes before the final transfer. |
| Projection singleton/tail | One input/output and partial groups follow the same states; lane masks suppress stale tile entries. Architectural legal geometry still requires multiples of eight. |
| Projection tensor issue | Synchronous activation/tile/sum reads precede valid; ordered result count selects the accumulator bank, independently of issue count. A new input group waits for every prior result. |
| Final projection/epilogue output | Store internal result and count the transfer. Wait for the leaf's delayed done before advancing the graph. |
| Final KV write | Acknowledgment, not request acceptance, completes the stored data/scale group. |
| Optimized final logit stalled | Synchronous RAM result is latched; hold logit index/data until accepted. No next token is accepted. |
| Final logit transferred at f | Decoder COMPLETE_WAIT after f, decoder done after f+1, top done after f+2. Top returns idle after f+3. |
| Top validation error accepted at k | ERROR_WAIT after k, done/error after k+1, idle after k+2; no child memory transaction. |
| DDR/scalar response coincidence | DDR retires only through its ID/tag owner; scalar configuration/bias response uses its separate waiting state. |
| Epilogue bubble | Count while the commanded epilogue is input-ready but its RAM/config feeder has no valid operand. Exclude its reduction/compute states and all final-output stalls. |

Required componentwise bounds are RMSNorm 0.005, RoPE 0.0005, SwiGLU 0.002,
attention 0.003, and architectural decoded-weight logits 0.02, each multiplying
max(1,abs(reference)). Fundamental FP32 add/multiply/conversions and required
legacy comparisons are bit-exact. Exp on [-80,0] requires relative error
<=0.0005; values below -80 may become zero with explicit error accounting.
MX quantization drift is reported separately.

## Integration and source loading

Compile the immutable parent sources before FP2 sources so both packages are
defined before module elaboration. All ROM provenance is in the RTL; there is
no runtime-generated ROM image dependency. A fast design-only syntax command
from the delivered root is:

```sh
iverilog -g2012 -t null -s anvil_q1_fp2_top anvil_q1_fp_reference/rtl/*.sv rtl/*.sv
```

For scalar-only integration use ENABLE_FP2=0 and connect the complete legacy
interface normally. Explicitly tie off every added input as below; output ports
can be connected to bridge/CSR wires or left open:

```systemverilog
// Added input connections on an ENABLE_FP2=0 scalar integration:
.ddr_req_ready(1'b0),
.ddr_rsp_valid(1'b0), .ddr_rsp_id(1'b0), .ddr_rsp_error(1'b0),
.ddr_rsp_rdata(512'd0),
.csr_req_valid(1'b0), .csr_req_write(1'b0), .csr_req_addr(12'd0),
.csr_req_wdata(32'd0), .csr_req_wstrb(4'd0), .csr_rsp_ready(1'b0)
```

For optimized execution, supply the described application-side DDR bridge,
scalar configuration/table responses and CSR channel; unused CSR inputs still
need explicit zero tie-offs. The application beat protocol is not a physical
DDR controller, PCIe endpoint or local host driver.

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
