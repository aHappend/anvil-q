# Anvil-Q1-HT3 implementation specification

Version: `v3.0.0-ht3-fp-flash-fused`.

## Authority and implementation status

The admitted work order remains the complete product contract. This document
records implementation decisions, not a substitute or relaxation of its
acceptance criteria. No linked repository-intake index, parent specification,
historical benchmark fixtures or parent acceptance receipts were supplied.
Compatibility must be derived from `anvil_q1_ht2_reference/rtl/`, which is
read-only provenance, not a numerical oracle.

**Current implementation is incomplete.** The owned RTL now includes arithmetic,
write conversion, native/AWQ/INT8 weight dequantization, a four-slot 256-lane
tensor block and the seven-mode epilogue. There is not yet a connected HT3
top, projection/decoder, tiled attention engine, extension scale/image controller
or packed committed-cache transport. The tensor and epilogue blocks are not yet
integrated into model execution. A standalone converter does not satisfy
integrated store-to-subsequent-attention acceptance.
The portable functional suite, synthesis, benchmarks, timing, hardware gates and
product report have not run. No readiness or performance claim is made here.

Designer owns `rtl/*.sv` and `design/*.md`. Independent Verifier owns `tests/*`.
The shared runtime runs the mandatory `python3 tests/verify.py` command, native
timing lint, Quartus STA and physical HIL in the admitted sequence. The final
independently approved PDF is a post-engineering runtime deliverable.

## Cycle and degenerate-boundary table

All transfers use **pre-edge** `valid && ready`. State and registered outputs
change **after** that edge. Newly computed responses cannot transfer
retroactively on their creation edge.

| Boundary | Required behavior |
| --- | --- |
| Active `rst_n=0` | All public valid, ready, data, address, control, completion and error outputs are zero; accepted operations are canceled. |
| Reset release R1 | Release synchronizer stage one rises; operation remains disabled. |
| Reset release R2 | Synchronized release rises after the edge; no request transferred at R2. |
| Reset release R3 | Earliest request-accepting edge. |
| Enabled L-stage primitive accepted at E | Valid appears after E+(L-1) enabled edges; earliest transfer is the following edge. |
| Primitive enable low | All valid and payload pipeline registers freeze together. |
| Response valid, ready low | Valid, data, error and association remain unchanged. |
| Singleton packet | First and last are both asserted on the same accepted coordinate. |
| Non-power-of-two extent | Counters compare against the extent, never truncate as a wrap rule. |
| Simultaneous final retirement and new request | Only permitted where explicitly supported; current transaction converters deliberately do not accept a replacement on a response-retiring edge. |
| Abort before response creation | Finish reserved conversion obligations, return an error-bearing transaction, and prohibit usable row admission. |
| Abort while response is held | Do not mutate that held response; the owner separately annuls/invalidate its row and drains it. |
| Reset and transfer coincide | Reset wins; no transfer is admitted. |
| Flush/new sequence with external reads/writes accepted | Invalidate ownership but drain external responses; never silently abandon a bus obligation. |

Clocked state uses active-low asynchronous assertion. Release is synchronized
independently in the core and DDR domains. Arithmetic leaves and converter
transactions implement a two-edge release interlock. Integration must distribute
the raw domain reset to these interlocked leaves rather than cascade release
synchronizers and inadvertently change the documented startup table.

## Frozen external integration contract

The future top is `anvil_q1_ht3_top`, with the exact ordered external ports,
directions, widths and signedness of `anvil_q1_ht2_top`. In particular,
`logit_data` is a signed 32-bit **container of FP32 bits**, not an integer
conversion. Existing token, loader, CSR, Avalon, four-slot batch, commit and
ancestor semantics are preserved.

All parent parameters retain their names/defaults. Legal ranges are:

| Parameter | Legal values |
| --- | --- |
| NUM_LAYERS | 1..24 |
| HIDDEN_SIZE | 8..896, multiple of eight |
| INTERMEDIATE_SIZE | 8..4864, multiple of eight |
| NUM_Q_HEADS / NUM_KV_HEADS | 1..14 / 1..2; integral Q/KV ratio |
| HEAD_DIM | Even, 2..64; HIDDEN_SIZE=NUM_Q_HEADS*HEAD_DIM |
| KV coordinates | NUM_KV_HEADS*HEAD_DIM must be a multiple of eight |
| GROUP_SIZE | 1..HIDDEN_SIZE; divides HIDDEN_SIZE and INTERMEDIATE_SIZE |
| AWQ_BITS | 4 |
| VOCAB_SIZE / MAX_SEQ_LEN | 1..151936 / 1..32768 |
| LANES / BANKS / LANES_PER_BANK / DDR_WIDTH | 64 / 8 / 8 / 512 |
| TILE_BEATS | 1..256 |
| KV_WINDOW | 1..min(128,MAX_SEQ_LEN) |
| FLASH_TILE | Trailing parameter; default 16; 1..128 independently of context length |

Illegal parameterizations require an explicit `PARAMETER ERROR` diagnostic and
a diagnostic-safe generate branch; they must not construct an illegal datapath.
Minimum-one widths are diagnostic-only, never a clamp on legal behavior.

## Arithmetic foundations

IEEE binary32 add and multiply round separately, RNE, with gradual underflow.
BF16 and binary16 conversions also use RNE and gradual underflow. Primitive
special values include canonical quiet NaN `0x7fc00000`, signed infinities and
IEEE signed-zero rules. Inference owners reject nonfinite active inputs and
nonfinite arithmetic outputs; masked slots are never submitted for conversion.

| Module | Interface / enabled-register latency |
| --- | --- |
| `anvil_q1_ht3_fp32_add` | `clk,rst_n,enable,in_valid,in_a,in_b,out_valid,out_data`; four stages |
| `anvil_q1_ht3_fp32_mul` | Same ports; four stages |
| `anvil_q1_ht3_expand16` | `clk,rst_n,enable,in_valid,in_data,in_fp16,out_valid,out_data`; one stage |
| `anvil_q1_ht3_narrow32` | Same control; 32-bit input, 16-bit output; one stage |
| `anvil_q1_ht3_fp32_divsqrt` | `clk,rst_n,enable,req_valid,req_ready,req_sqrt,req_a,req_b,rsp_valid,rsp_ready,rsp_data`; reserved transaction, response visible E+64 |

The multiply pipeline separates operand capture, exact 24x24 multiplication,
normalization/RNE rounding and final exponent/fraction encoding. Four stages are a temporal contract,
not evidence of achieved frequency. Add captures operands, aligns magnitudes,
adds/subtracts and rounds. Payload and format selection remain associated across
global enabled-pipeline stalls.

Divide/square-root captures at E, normalizes at E+1, initializes the bounded
restoring engine at E+2, iterates 27 times at E+3..E+29, rounds at E+30,
and releases the reserved response after E+64. Exceptional inputs use the same
release edge. Admission requires enable; after admission, the transaction
continues independently of enable and holds its response until acknowledged.
Earliest transfer is E+65 and earliest following request E+66. This is a
transaction engine, not a globally enabled arithmetic pipeline.

`anvil_q1_ht3_fp32_exp` uses ports
`clk,rst_n,enable,in_valid,in_data,out_valid,out_data`, with 32 enabled stages.
It decodes the represented input into fixed-point Q48, derives an integer
power of two using a Q32 reciprocal-ln2 constant, subtracts that power times
Q48 ln2, and evaluates a degree-eight exponential polynomial in Q40.
Each Horner multiply and coefficient addition has a separate register.
Final binary32 packing applies the retained exponent, including gradual
underflow. Inputs at or below -104 return zero; inputs at or above 89 return
positive infinity. Those are safe outer bounds, not replacements for rounding
within the representable boundary interval. NaN canonicalizes; negative
infinity maps to zero. The internal approximation is subject to independent
admitted error checks, not an exact-exp claim.

`anvil_q1_ht3_fp32_sincos` has the same streaming control/data input and
outputs `out_valid,out_sin,out_cos,out_error`. It has 64 enabled stages.
Its supported finite angle domain is [-32768,32768], covering every legal
RoPE position/frequency. Nonfinite or out-of-domain angles return canonical
NaNs with error at the same latency. Signed zero produces signed-zero sine
and exactly one cosine. Reduction uses a nearest quadrant, a Q48 half-pi
constant and 48 registered Q48 CORDIC rotations. Mapping, FP32 packing and
retiming complete the 64 stages. Payload, quadrant, sign, zero and error
all freeze with enable.

The same file provides `anvil_q1_ht3_sincos_phase`, a 64-stage internal
primitive with unsigned 65-bit Q48 `in_phase` magnitude plus
`in_negative,in_zero,in_error`. It must be supplied a magnitude <=32768
and the correct zero/error flags. Its outputs match the FP32-input wrapper.
`anvil_q1_ht3_rope_frequency` supplies unsigned Q56 frequencies. A dimension-
specific Q56 root of theta=1e6 is raised to each constant pair index at
elaboration; no runtime exponentiation, division or real arithmetic is used.
The epilogue multiplies the full position by this frequency and passes a Q48
phase directly to the CORDIC. It does not first round a large RoPE angle to
FP32, which could otherwise lose significant phase at position 32767.

`anvil_q1_ht3_scalar` reserves a held inference response for opcodes 0 add,
1 multiply, 2 divide, 3 square root and 4 exp; other opcodes error. It captures
operands on request E, issues to the leaf at E+1 and registers its response
after E+5 for add/multiply, E+33 for exp, or E+66 for divide/square root.
Earliest transfer is the following edge. Invalid active input/opcode returns
an error response after E; output nonfinite is an inference error. The
wrapper does not change the primitive IEEE special-value contract.

## Tensor and weight stream

`anvil_q1_ht3_tensor_array` uses the parent's tile-batch MAC input/output
shape and adds trailing internal inputs `in_weight_fp32` and
`in_weights_fp32[2047:0]`. These are internal ports, not a top-level ABI
extension. `in_weight_fp32=0` interprets the 64 legacy 16-bit row weights
according to `in_fp16`; `in_weight_fp32=1` consumes the 64 full FP32 row
weights instead. Activations remain four encoded 16-bit slot values.
All weights, masks, slots and format belong to the same accepted column.

There are four physical slot generate branches, each with 64 instantiated
`anvil_q1_ht3_mac_lane` blocks. Each lane contains a four-stage multiplier
and four-stage accumulator, four independent FP32 accumulation contexts and
same-edge result forwarding. Accepted columns select contexts cyclically
0,1,2,3; bubbles do not advance the context selector. This permits one column
per core edge without the four-stage accumulation recurrence inserting
bubbles. Products and accumulation round separately. Final reduction is
`((context0+context1)+context2)+context3`; it is not an implicit FMA or
FP64 accumulator.

First/last may coincide. First is mandatory on the first beat and forbidden
thereafter; masks, slots, activation format and weight source format must
remain identical throughout the packet. Active inputs and arithmetic overflow
are checked; inactive lanes/slots neither consume nonfinite data nor report
numeric errors. Output payload and tags hold under backpressure.

For N consecutive accepted columns beginning at E, the last column arrives
at B=E+N-1. Last product visibility is B+3, last accumulation is issued at
B+4, and its context retires at B+8. Reduction requests occur at B+9,
B+14 and B+19; the final lane result registers at B+23. The array response
is visible after B+24 and first transferable at B+25, independent of N.
Malformed packet input switches to a bounded bad-drain response visible
ten edges after that malformed acceptance, with error and zero data.
There is no new-packet admission on a response-retiring edge.

`anvil_q1_ht3_dequant` provides a globally stalled five-enabled-stage
ready/valid stream. Legacy AWQ extracts unsigned nibbles using
`{lane[0],lane[2:1],2'b00}`, subtracts unsigned zero, expands FP16 scale,
multiplies in FP32, and RNE-narrows to BF16. `out_data` expands that BF16
boundary; `out_weight` carries the BF16 bits. As inherited, a zero legacy
scale is allowed; negative nonzero and nonfinite legacy scales error.
INT8 uses the signed low byte, a positive finite FP32 scale, full FP32
product at `out_data`, and zero `out_weight`. INT8 consumers must use the
tensor's full-FP32 weight input, not its encoded legacy input. Errors are
carried explicitly and the owner must not consume errored payload as weights.

## Standalone fused epilogue

`anvil_q1_ht3_epilogue_fusion` implements the admitted exact external
epilogue interface and modes 0..6. It accepts a command, validates length,
slots and active RoPE positions, acquires exactly one ascending input stream,
then executes the selected operations using private retained vectors.
Input, auxiliary and gamma storage have MAX_VECTOR entries with synchronous
read/write ports and no RAM reset. Ownership state prevents stale observation.
Inactive slots are stored/output as zero; inactive auxiliary/gamma fields are
not numeric-error sources. Mode 7 and malformed commands explicitly error.

Modes 1/5/6 use FP32 sum of squares, division by represented vector length,
epsilon `0x358637bd`, square root, reciprocal, and two FP32 multiplies for
input and gamma. Gamma is expanded from the selected 16-bit format, without
intermediate result narrowing. Mode 6 first performs residual addition in
the private buffer. Mode 5 normalizes before split-half RoPE. RoPE overwrites
each private pair only after both FP32 results have been calculated. Mode 3
uses exp(-abs(g)); positive gates use g/(1+exp(-g)), negative gates use
(g*exp(g))/(1+exp(g)), followed by multiplication by up. Large finite negative
gates therefore do not request an overflowing exp(-g).

Output replay is ascending. The FP32 stream is narrowed only for
`out_encoded`; nonfinite active arithmetic and nonfinite narrowing output
cause an explicit command error instead of usable output. This finite-output
policy includes BF16/FP16 overflow. Output valid, index, slots and both payload
encodings hold until transfer. Abort drains any issued arithmetic. If an
output is already held, it is retained until transfer before the aborted
command completes with error. Successful `done` pulses after the last output
transfer; a failed/aborted command pulses done and asserts error. Error is
sticky until the next accepted command or reset.

### Epilogue no-stall transaction cycle formulas

Let E be command acceptance, L the vector length, P=L/2 for RoPE modes,
and h=L/HEAD_DIM for RoPE modes. With valid held whenever ready and all outputs
ready, first input acceptance A is E+2 for modes 0/1/3/4/6, or E+h+2
for modes 2/5. Length divisibility is validated by an explicit head counter,
not combinational division/modulo. Final input acceptance is B=A+L-1.
The following formulas give the **edge of final output transfer T**, after
which done is visible. The final output becomes visible one edge before T.

| Mode | T relative to final input B |
| --- | --- |
| 0 bypass | B+3*L+1 |
| 1 RMSNorm | B+28*L+204 |
| 2 RoPE | B+101*P+3*L+1 |
| 3 SwiGLU | B+120*L+1 |
| 4 residual | B+11*L+1 |
| 5 RMSNorm then RoPE | B+101*P+28*L+204 |
| 6 residual then RMSNorm | B+36*L+204 |

These are conservative serial SIMD schedules, not claimed performance gains.
For unambiguous derivation, a four-stage arithmetic request issued at I is
consumed by the controller at I+4; exp at I+32; sin/cos at I+64; the reserved
divide/sqrt response at I+65. A dependent issue occurs one edge after that
consumption. Initial data read/load precedes issue by two edges. Residual,
sum-of-squares, normalized-output and SwiGLU coordinate initiation intervals
are respectively 8,12,13,117 edges. The normalization scalar tail between
last sum issue and first normalized-coordinate issue includes three reserved
divide/sqrt transactions and one add. RoPE pairs initiate 101 edges apart,
including two partner reads and two writes. Output replay initiates one
transfer every three edges. Input bubbles and held-output edges add their
actual delays; no arithmetic stage counts depend on numeric value or slot
population.

## Exact FP32-to-quantized KV conversion

`anvil_q1_ht3_kv_quantize` accepts one finite FP32 source, a positive finite FP32
scale and `in_int8`. It returns a zero-extended 16-bit container, using only
bits 3:0 for signed INT4 or 7:0 for signed INT8. No FP32 division,
reciprocal multiplication or intermediate 16-bit narrowing participates in
rounding:

`q = clamp(RNE_integer(exact_value(x)/exact_value(s)), qmin, qmax)`.

Positive and negative zero map to zero. Finite excess magnitude saturates.
Invalid scale or nonfinite source returns an explicit error transaction, not a
valid zero-valued store. The owner must refuse completeness/visibility for that
row. An errored response's zero payload is not usable data.

### Exact threshold algorithm

Decode each nonzero finite operand to a 24-bit integer significand and a binary
scale, then normalize the significand by left-shifting its leading one to bit
23. Let their normalized exponent difference be `e`. The normalized-significand
ratio is strictly between 1/2 and 2.

If `e>=8`, every supported signed magnitude saturates. If `e<=-2`, its rounded
magnitude is zero. Otherwise `-1<=e<=7`, and the entire exact comparison fits
33 bits:

`2*abs(x) > (2*mid+1)*s`

is evaluated as `(normalized_x << (e+1)) > normalized_s*(2*mid+1)`.
There is no discarded fraction or approximate quotient. Equality selects the
upper integer exactly when `mid` is odd, implementing nearest-even ties for
both signs. Eight fixed binary-search iterations search 0..7, 0..8,
0..127 or 0..128 according to sign/format, including saturation. The
two's-complement sign is applied only after magnitude selection.

### Scalar no-stall cycle formula

The scalar engine is non-reentrant and runs to its reserved response slot
independently of downstream readiness.

| Edge relative to request E | Post-edge operation |
| --- | --- |
| 0 | Capture FP32 source, scale and format |
| 1 | Normalize significands and calculate represented exponents |
| 2 | Select exact shifted numerator or mathematically justified early result; initialize search bounds |
| 3+2*i, i=0..7 | Register midpoint and exact 24x9 threshold product |
| 4+2*i, i=0..7 | Update binary-search bounds by exact comparison |
| 19 | Register encoded result and error, assert response valid |
| 20 | Earliest response transfer |

Thus visibility is **E+19**, earliest transfer **E+20**, for every input,
including invalid inputs, zero and saturated values. Stalling response
retirement adds exactly the number of unaccepted response edges; search latency
does not depend on numeric value. There is no acceptance on the retiring edge;
the earliest next request is one edge later.

## Key/value pair store boundary

`anvil_q1_ht3_kv_store_convert` accepts a complete full-FP32 K/V pair with format,
separate K/V scales and the parent's node/layer/column/first/last tags. There is
one reserved pair transaction. Both scalar quantizers accept on the same edge
as the pair request, and the wrapper joins their held responses atomically.
The output includes `out_error` and is a response channel, not permission to
admit an erroneous row.

Native formats 0/1 narrow directly from captured FP32 with BF16/FP16 RNE.
Quantized formats 2/3 use the exact converters with no intervening narrowing.
Native scale fields are ignored. Quantized output upper bits are zero; native
output is the IEEE 16-bit encoding. Nonfinite active input or native narrowing
overflow is an explicit error. Abort is sticky for an accepted in-flight pair
until response creation; response fields do not change under backpressure.

The submitting decoder must issue only active slots, preserve ascending
coordinates per row, set first exactly at coordinate zero and last exactly at
`C-1`, and capture the scale associated with the submitted layer/head. The
converter preserves those tags; it does not guess row geometry. It must not be
fed the parent's already narrowed `encoded_key_q`/`encoded_value_q`.

For quantized mode, scalar responses are visible at E+19, joined after E+20,
and the pair first transfers at E+21. For native mode, the pair becomes visible
after E+1 and first transfers at E+2. With continuously ready consumers and
requests, pair initiation intervals are therefore 22 and 3 edges respectively.
For N consecutive pairs of a single format, first request E and no stalls,
the final pair transfers at E+22*N-1 (quantized) or E+3*N-1 (native).
This conservative converter is not a throughput or zero-stall-attention claim.
Integration may overlap separate row preparation, but must preserve these
documented converter timings or explicitly revise this implementation
specification before independent temporal expectations are authored.

### Required producer, cache and packing integration

The following remains mandatory and is not implemented by the standalone
converter:

* K source is FP32 after projection, bias and complete split-half RoPE.
  V source is FP32 after projection and bias. Query encoding alone uses
  `cmd_fp16`; it must not narrow the quantized K/V source.
* Scale association is `(layer,head,K-before-V)` from the committed extension
  table, with counter-based head/coordinate mapping and stable captured tags.
* Provisional storage retains only the codes and image/format ownership.
  Self/ancestor attention reads and dequantizes those same codes. Incomplete,
  annulled or errored rows are invisible.
* For C=NUM_KV_HEADS*HEAD_DIM and b=4/8, each separate K or V token record has
  stride `64*ceil(C*b/512)` bytes; descriptor length is MAX_SEQ_LEN times
  that stride. Coordinate c occupies bits `[b*c+:b]`, no 16-bit gaps.
  INT4 coordinate zero is the first low nibble; INT8 uses ascending bytes.
  Padding is zero and full aligned records are written.
* Commit copies codes bit-for-bit, without conversion; prefix visibility
  advances only after successful required write responses. Failed partial DDR
  writes cannot expose a successful prefix. Abort/reset/new sequence invalidate
  ownership and drain accepted external transactions.
* Invalid/overlapping/unaligned/out-of-range regions reject image commit.
  Scale or format mutation requires idle ownership, image recommit and prefix
  invalidation. Dequantization overflow is an inference error, distinct from
  successful finite write saturation.

## Required integrated datapath

The literal decoder instances must be `u_epilogue` and `u_flash_attn`, with
`u_tensor_array` under the actual projection containing four physical slots
times 64 MAC rows. Naming disconnected modules is not integration.

The graph is input norm -> Q/K/V -> Q/K RoPE -> attention -> output projection
plus residual -> post-attention norm -> gate/up SwiGLU -> down projection
plus residual, repeated per layer, then final norm and logits.

The implemented epilogue and tensor block described above must be connected
to the actual decoder/projection; their presence alone is not model execution
or a measured fusion improvement. Private replay costs are included in the
standalone formulas. Shared-scratch operator-boundary round trips remain
forbidden.

FlashAttention must preserve the parent attention ports plus KV format/scales,
GQA, causal/ancestor masking and four-slot ownership. It uses two bounded tiles
and running FP32 m/l/o with exact first-tile handling and final o/l.
Each required K/V coordinate is fetched once per query-head traversal and V
reused within the tile; no context-proportional score/probability array or
second full-context value traversal is permitted. Empty attention errors.

The extension CSR map remains 0x0150 format control, 0x0154 version
`0x03000003`, 0x0158/0x015c scale-table base, 0x0160 length;
0x0164..0x017c are reserved. Native legacy format values and legacy identity
remain unchanged; legacy format 3 stays invalid. INT8 override affects
projections 0..6, not the inherited LM-head/embedding layouts. AWQ retains
unsigned code-minus-zero, FP16 scales, BF16 dequantization and lane permutation
`{lane[0],lane[2:1],2'b00}`.

## Implementation and independent acceptance obligations

No combinational division/modulo operators, mixed sequential assignment styles,
inferred latches, unsynthesizable real arithmetic, simulation replacements or
broad timing exceptions are allowed. Internal target is 5.0 ns/200 MHz;
external and mandatory minimum target is <=10.0 ns/100 MHz on Arria 10 GX
10AX115N2F45E1SG. Achieved timing requires actual Quartus STA.

Mandatory independent L1 includes real compact Icarus, compiled Verilator,
exact IEEE and exact-integer quantization references, seeds 17/89/2026,
integrated store-to-later-attention, parameter/stall/abort/error matrices,
compiled defect sensitivity, actual default hierarchy and compact mapped Yosys
zero-latch/div/mod checks, and clean-directory reproduction. Each nonzero
epilogue, attention and logit vector must satisfy cosine >=0.9999; standalone
FP32 epilogue/attention error is <=2e-4*max(1,max_abs(reference)). The admitted
primitive tolerances and exhaustive directed/store-boundary coverage remain
unchanged.

Official pinned Qwen full-dimension RTL inference on GSM8K, HumanEval, MMLU,
ARC-Challenge and WikiText-2 remains mandatory. Selection, prompts, token IDs,
FP64 logits, sampled metrics, >=128 WikiText scored tokens and authentic
legacy-fixture availability must be recorded independently. No toy weights may
stand in for official model runs. HumanEval generated code is not executed in
the shared environment. Matched actual HT2/HT3 runs must measure per-eligible-
path >60% transition-cycle reduction and actual total cycles/TPM, with simulated
and physical results labeled separately.

No acceptance evidence exists yet. The required implementation work remaining
is listed in `design/ARCHITECTURE.md`; none of these obligations is waived.
