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
tensor block, the seven-mode epilogue, bounded tiled online attention,
image-tagged provisional code storage, packed committed-cache readers/writers,
a projection containing the physical tensor array, a reserved panel prefetch
and queued DMA arbiter, and a cache controller connecting provisional storage
to committed reads and code-preserving copies.
There is not yet a connected HT3 top/decoder, extension scale/image controller,
transactional prefix/branch executor or core/DDR transport. These blocks are
not yet integrated into model execution. A standalone converter does not satisfy
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

## Connected projection and reserved weight supply

`anvil_q1_ht3_projection` preserves the parent projection port order, appending
`cmd_int8_weights`, `cmd_int8_scale_base[32:0]` and
`cmd_int8_scale_length[31:0]`; TILE_BEATS is a trailing parameter. Its legal
HIDDEN_SIZE, INTERMEDIATE_SIZE, GROUP_SIZE and VOCAB_SIZE match the parent.
Illegal geometries instantiate diagnostic-only zero outputs. Group counts are
elaboration constants derived with bounded shift/subtract, not RTL divide/modulo.

The actual `u_tensor_array` is the four-slot by 64-row HT3 tensor, fed from
synchronous architectural activation retention and registered weight columns.
Native weights retain their encoded BF16/FP16 boundary. AWQ uses 64 parallel
HT3 dequantizers, the inherited lane permutation, unsigned zero subtraction
and BF16 result boundary. Signed INT8 extracts ascending low bytes and feeds
the dequantizers' full FP32 results to the tensor's FP32 weight port. No INT8
result is narrowed before multiplication with its encoded activation.
Column/activation tags advance with the same five enabled registers as weight
dequantization and freeze with its output backpressure.

For N input coordinates and P=ceil(output_rows/64), weight descriptor lengths
are 128*N*P bytes native and 64*N*P bytes AWQ/INT8. Traversal is panel, input
column, ascending row within the fixed 64-row panel. Partial-panel rows remain
masked, while physical descriptor panels retain all 64 rows. AWQ metadata is
panel, input group: 64 bytes of zero metadata and 128 bytes of FP16 scale
metadata per panel/group, preserving inherited padding and permutation.

INT8 scale ports name the *projection's logical subregion* of the committed
extension table, not the entire table. Its base is four-byte aligned and its
exact length is output_rows*input_groups*4 bytes. Only the entire extension
table is rounded/aligned to 64 bytes; a logical projection subregion need not
be. Entry order is output row then input group. A captured panel-scale base,
group counter and row-stride counter select each scale without runtime divide.
A one-beat scale cache extracts actual little-endian FP32 bytes. Distinct
groups and rows cannot acquire a new scale while an old dequantization is
stalled: scales are captured by arithmetic on its accepted input edge.
Positive finite scales, including subnormals, are checked before that group's
columns are submitted. Table-level padding, overlap, bounds, image ownership
and projection-0..6-only override admission still belong to the missing image
controller and decoder.

Sparse down projection preserves the parent conservative behavior. The
BF16 threshold predicate may predict a skipped column, but a nonzero encoded
activation, preserved pre-narrowing nonzero flag, or unproven finite weight
image forces a real replay read. Only a genuinely zero column with a finite
image avoids weight bytes. Metadata is still loaded and validated. A skipped
column submits zero weights with the original activation signs; it does not
invent an approximate nonzero result. Eligible, avoided and replay statistics
are emitted at actual classification/read/compute events.

`anvil_q1_ht3_panel_prefetch` reserves all requested return beats before issue.
Two 128-entry synchronous low/high banks retain 128 complete columns plus
one held output. Native reservation capacity is 256 beats; compact AWQ/INT8
capacity is 128 beats. A burst is at most min(TILE_BEATS,128) native or
min(TILE_BEATS,64) compact, shortened for the final extent. TILE_BEATS=1
therefore splits native columns across separate one-beat requests without
losing their low/high association. Issued-minus-released beats are the
capacity measure; returned-but-unconsumed columns remain reserved. A displayed
request survives abort until acceptance, then drains along with every earlier
request. Held outputs also survive abort until transfer.

`anvil_q1_ht3_dma_mux` directly admits the selected client's request on the
external request-accepting edge, with a DEPTH-entry ordered ownership queue
(default eight, legal 1..32). Round-robin arbitration locks selection during
request backpressure. On a full queue, final incoming-response retirement
provides same-edge replacement credit. A one-register response reservation
captures data, owner and error together; no incoming response can transfer to
a client on its capture edge. Invalid zero-length, unaligned, overflowing or
multi-beat-write commands generate explicit error responses without issuing
invalid memory traffic. Unexpected response type/last/ownership raises the
sticky protocol fault. CHECK_RESPONSE_LAST is 0 or 1, default 1; the projection
uses 0 because the parent projection channel has no last signal. Length and
type ownership are still checked/count-retired, never guessed from a single
current-command counter. Return order is the admitted ordered transport
contract, not support for untagged out-of-order responses.

### Projection and DMA cycle recurrences

These formulas describe connected RTL edges, not measured timing or acceptance.
Let E be projection command acceptance, N its input length, and assume valid
activations whenever ready. Preflight multiply, length and validation execute
at E+1..E+3. Activations accept at E+4..E+N+3. Panel setup is E+N+4;
for dense traffic prefetch command is E+N+5 and metadata selection E+N+6.
Sparse traffic selects metadata at E+N+5 without dense prefetch.

For a burst-reader command accepted at A, its memory request is first
presented for acceptance at A+1. Let R be its actual request edge and T_j
its actual jth incoming DMA beat edge. The DMA arbiter captures each beat at
T_j; the reader consumes it at T_j+1 with ready consumers. The projection
retires the held assembled response at T_last+2. There is no assumption that
issuing a metadata request bypasses older queued weight responses.

For prefetch, let T be a column's final incoming DMA beat edge. With available
output reservations and projection in STREAM, prefetch RAM writes complete
at T+1, synchronous output fetch occurs at T+2, and the projection captures
the column and its synchronous activation read at P=T+3. Native tensor
input is P+1; quantized dequantization input is P+1 and tensor input P+6.
Input bubbles, return gaps and reservation stalls delay exactly these
acceptance/read edges. Consecutive compact resident columns can enter
dequantization every edge; native admission is conditional on its two-beat
memory supply. This is not an unconditional one-column-per-bus-edge claim.

AWQ group setup executes META_BEGIN, ZERO_SEND/WAIT, SCALE_SEND/WAIT and a
metadata-validation edge before STREAM. Each SEND accepts one reader command;
each WAIT ends at the corresponding T_last+2 edge above. INT8 group setup
executes INT8_BEGIN, then for each active row an ADDRESS edge and a WORD
capture edge on a scale-cache hit. A miss inserts INT8_SEND command acceptance,
INT8_WAIT through T_last+2, then WORD on the next edge. Subsequent row addresses
advance by input_groups*4. The final group column cannot capture a successor
column until the next group's metadata has been validated; already issued
arithmetic continues independently with its captured scales.

Sparse per-column acquisition executes SPARSE_READ, SPARSE_CLASSIFY and,
unless the exact-zero skip is legal, WEIGHT_SEND/WAIT through T_last+2.
The following STREAM edge submits the column, directly native or into the
same five-stage dequantization/tag pipe. The next column returns to
SPARSE_READ or group metadata setup. Threshold prediction is not treated
as a memory return or a completed arithmetic transaction.

Let M be a panel's final actual tensor input transfer. Tensor output is
visible after M+24; projection captures it at M+25 and its held panel output
first transfers at M+26. With final output ready, done is visible after that
final transfer edge and lasts one cycle. A successor panel uses setup,
prefetch-command and metadata-selection edges following the preceding panel
transfer. Output stalls add their actual held interval. Abort/error cancels
internal arithmetic, preserves any already held panel, drains the reader,
prefetch and queued DMA obligations, and only then emits failed completion.
No integrated model, fusion-transition or end-to-end cycle formula is claimed
until decoder/top execution is connected.

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
an additional `in_image[31:0]`/`out_image[31:0]` ownership tag, captured on
request acceptance and held alongside format and coordinates. There is
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

## Tiled online FlashAttention implementation

`anvil_q1_ht3_flash_attn` preserves the ordered parent attention ports, appending
`cmd_kv_format[1:0]`, `kv_key_scale[31:0]` and `kv_value_scale[31:0]`. Its
parameters are NUM_Q_HEADS, NUM_KV_HEADS, HEAD_DIM, MAX_SEQ_LEN and trailing
TILE_TOKENS=16. The legal attention geometry matches the top; TILE_TOKENS is
1..128, including when larger than MAX_SEQ_LEN. Invalid geometry constructs
only zero-valued diagnostic outputs and emits `PARAMETER ERROR`.

The query stream contains NUM_Q_HEADS*HEAD_DIM ascending coordinates, four
16-bit slots per beat. `cmd_fp16` selects query encoding independently of
the cache format. Cache formats 0/1 expand BF16/FP16; formats 2/3 interpret
zero-filled low INT4/INT8 two's-complement codes, expand those integers exactly,
and multiply by the captured positive finite FP32 K/V scales. Code-container,
scale, active query, active cache and arithmetic errors are explicit. No
probability is narrowed to BF16 or FP16.

Command validation retains the parent prefix/ancestor contract: each active
slot includes itself, references only active earlier ancestors, has distinct
ancestor positions, includes the ancestors of its ancestors and occupies
prefix_length+ancestor_count-1 below MAX_SEQ_LEN. Inactive ancestor rows are
zero. GQA head mapping uses an incrementing head/within-group counter, not
runtime division.

`u_tiles`, an `anvil_q1_ht3_attn_tiles` instance, reserves exactly two
TILE_TOKENS-by-HEAD_DIM K/V tile buffers. Each coordinate retains the raw
16-bit words and captured FP32 K/V scales together. A tile-local four-bit
mask marks the slots permitted to consume each token. Prefix coordinates
are fetched once in ascending order; provisional nodes follow in ascending
node order, omitting nodes visible to no active query. Fetching the next
tile overlaps arithmetic on the current tile. Only one memory-side response
is outstanding, with its buffer/coordinate reserved before request display.
Zero-latency request/response retirement is supported.

Computation retains only Q, one HEAD_DIM-by-four FP32 output accumulator,
four running maxima/sums and one TILE_TOKENS-by-four score buffer. No retained
array scales with MAX_SEQ_LEN. For each tile it computes separately rounded
FP32 dot products and the FP32 1/sqrt(HEAD_DIM) scaling. A tile maximum includes
the previous running maximum. Previously unseen slots use alpha=0 explicitly,
rather than subtracting two infinities. Previously seen slots use
alpha=exp(m_old-m_new). It rescales l and every o coordinate, then evaluates
each tile-local p=exp(score-m_new), adds p to l and p*V to o. Masks precede
maximum/sum/update participation. A tile masked for one slot therefore leaves
that slot's running state unchanged. Final FP32 outputs are o/l in ascending
head/coordinate order. An empty slot attention set errors rather than issuing
0/0.

The final weighted-output write releases the consumed buffer on that same
edge. If the next buffer is already resident, the following edge performs
its first score-memory read without a tile-handoff-only state. A fill owner
can acquire a buffer on its release edge. Arithmetic latency and memory
starvation remain separately counted; this is not a bandwidth-independent
zero-stall or measured-performance claim.

Abort or an error annuls further computation, but displayed memory requests
remain stable until accepted and all accepted responses drain. Issued scalar
transactions finish into their reserved slots and are retired during drain.
An already valid attention output holds its data/index/slots through stalls,
even on abort; the command fails after that held response transfers. Active
reset cancels internal ownership. The enclosing transport must still implement
the admitted reset epoch/drain rules for external accepted DDR traffic.

### Attention no-stall and bounded-transaction cycle formulas

All offsets below are **edges**, not claimed measured cycle results. Let
D=HEAD_DIM, Q=NUM_Q_HEADS, E=accepted command, and B=final accepted query beat.
With continuously valid input, first query acceptance is E+1 and B=E+Q*D.
The scalar wrapper used by attention consumes an add/multiply response six
edges after its request, an exp response 34 edges after its request, and a
divide/sqrt response 67 edges after its request. These wrapper transaction
offsets include operand reservation, primitive issue, held-response capture
and controller retirement; the primitive register counts remain unchanged.
A dependent scalar request issues one edge after retirement.

Root request is B+1, reciprocal request B+69, and first tile-start acceptance
is B+137. Later heads begin their tile fetch on the edge after the previous
head's final output transfer, once the fetch owner is idle. All legal finite
numeric values use the same schedule; input/scale errors take the error drain.

For a tile with n retained tokens, let A be its first SCORE_READ edge and H
the edge that writes its final weighted output coordinate and releases it.
The exact compute-only interval is:

| Cache format | H-A |
| --- | --- |
| Native BF16/FP16 | n*(33*D+60)+10*D+47 |
| Quantized INT4/INT8 | n*(47*D+60)+10*D+47 |

Score-coordinate read initiation intervals are 16 edges native and 23
quantized, including two synchronous read/capture edges, dependent FP32
multiply/add and optional dequantization. Score-token initiation intervals
are respectively 16*D+8 and 23*D+8. The last score-store edge F is
A+n*(score_coordinate_interval*D+8)-1. Alpha subtract/exp, l rescale and the
whole-o rescale end at G=F+10*D+49. Each probability/value token then takes
17*D+52 edges native or 24*D+52 quantized; H=G+n*that_interval-1.

For a resident successor tile, A_next=H+1. For a nonresident successor,
TILE_WAIT adds exactly the observed wait through publication/admission; the
first score read follows the edge admitting that resident tile. On the final
tile, first output transfer is H+71 and the HEAD_DIM output transfers are
71 edges apart, so final head output transfer is H+71*D. The 71 includes
two synchronous read/capture edges, request issue, the 67-edge scalar divide
retirement and the held-output transfer edge. After the final head, successful
done is visible one edge after its final output transfer, assuming all
prefetch obligations have retired. Actual stalls extend their own wait
intervals; no constant long-context latency is invented.

For independent temporal construction of tile supply, `u_tiles` start at F0
selects its free buffer at F0+1, scans its first source at F0+2 and displays
the first request for acceptance at F0+3. With ready memory, same-edge returns
and no skipped sources, coordinate requests are consecutive within a token;
the next token starts one scan edge after the last coordinate. A full n-token
tile publishes valid after F0+n*(D+1)+2; a partial final tile additionally
uses one end-of-source scan edge. Each invisible provisional source scanned
adds one edge. A memory response latency lambda adds lambda edges per
coordinate, and each request-ready stall adds its observed held edges.
Between tiles there is a publication edge, buffer-pick edge and source-scan
edge; buffer-credit waits add their actual delay. On a simultaneous release
and pick, the released credit can be reserved on that edge. These finite
per-state recurrences, together with the compute formulas, define the
complete attention-focused no-stall transaction without assuming memory
service independent of the selected cache adapter.

## Provisional code ownership and packed DDR adapters

`anvil_q1_ht3_provisional_kv` retains the parent's command/write/read ports,
adding format/image tags on admission, writes and reads, a write_fault input,
and format/image response tags. Command begin reserves nonzero slot ownership,
clears row completeness/poison state and captures one immutable format/image.
A pruning command may only remove slots and must use that same format/image.
Storage holds one raw 32-bit K/V code pair per coordinate, not a private FP32
alternative. Rows become readable only after all C ascending coordinates
retire with exact first/last markers, matching image/format and no fault.

A malformed/faulted row is poisoned until a new command begins. An active
writer error poisons its row even when a mismatched write names a different
row. Native nonfinite values and quantized nonzero container upper bits are
store errors. Reading an incomplete, poisoned, colliding, unowned or
wrong-image/format row returns a held explicit error. Simultaneous read/write
to different complete rows is allowed; a row being written or completing on
that edge cannot be consumed by a simultaneous read.

Command/write readiness has the same ownership exclusions as the parent.
A correct final write at E establishes completeness after E, so the first
read may accept at E+1. Read acceptance at R produces a held synchronous-RAM
response visible after R, first transferable at R+1. A retiring response
can be replaced by another accepted read on that edge. Flush annuls slot and
row ownership but does not rewrite or discard an already held response; its
consumer must drain and annul it. No RAM reset is required.

`anvil_q1_ht3_kv_writer` preserves the parent writer ports, appending
cmd_kv_format. `anvil_q1_ht3_kv_reader` preserves the parent reader ports,
appending req_kv_format, captured req_key_scale/req_value_scale and held
rsp_key_scale/rsp_value_scale. Their inherited fp16 ports remain for
interface compatibility; the explicit KV format selects native cache encoding,
not query encoding. Integration must supply the resolved cache format.

For width b=16 native, b=4 INT4 or b=8 INT8, M=ceil(C*b/512) beats and
stride=64*M bytes. Each separate K/V region has length MAX_SEQ_LEN*stride,
base aligned to 64 bytes, and coordinate c at bits b*c of token p's record
base+p*stride. The writer copies code bits unchanged into separate zero-cleared
K/V records; unused record padding stays zero. It writes every K beat followed
by every V beat, with all 64 byte enables asserted. It does not quantize,
dequantize or interleave regions. Both adapters validate exact lengths,
prefix/position bounds, alignment, 33-bit address limits and K/V region
nonoverlap. Offset multiplication and address addition use distinct register
stages; bit/beat selection uses shifts/slices, never division/modulo.

Reader beat caching is tagged by both physical addresses and cache format.
The actual DDR word is sliced into a zero-filled 16-bit code container at the
ascending nibble/byte position. Quantized scales are captured from the
request's layer/head table association, not looked up again after a stall;
native formats ignore them. Scale validity and native selected-word finiteness
are checked explicitly. FP32 dequantization/overflow checking occurs in
attention, not external testbench arithmetic. Format/image/scale mutations
must invalidate the cache and prefix through the integrating controller.

Both adapters reserve one response obligation before request display and
handle same-edge requests/returns. Displayed requests hold through abort
until accepted, then accepted returns drain. Invalidate during an unfinished
read causes an error after drain. Held client responses retain data/error/
scales unchanged under later abort/invalidate; higher-level ownership prevents
their reuse. A writer response does not itself advance prefix validity:
the integrating commit controller must await every successful required row
copy before exposing its selected branch.

### Packed adapter no-stall cycles

For writer command acceptance E, first input acceptance is E+4 after separate
offset/address/check edges, and final input B=E+C+3. First DMA acceptance
is B+2. For constant response latency lambda>=0 and DMA always ready,
the 2*M writes accept every lambda+1 edges. Final write response is
B+1+2*M*(lambda+1); the writer response first transfers at
B+2+2*M*(lambda+1). At lambda=0 all DDR writes accept on consecutive edges.
There are no pad-word cycles or response-turnaround-only scheduler states.
Client response stalls extend held ownership; the next command cannot accept
on the client-response retiring edge.

For reader acceptance E, offset/address/check/lookup occur at E+1..E+4.
A cache hit first transfers its response at E+6. On a miss, first key DMA
acceptance is E+5. For K/V return latencies lambda_K and lambda_V, the client
response first transfers at E+8+lambda_K+lambda_V. Request-ready stalls add
their exact held edges. These bounds cover C=8, partial aligned records,
non-power-of-two geometry and final legal token positions without clamping.
Invalid requests return explicit errors instead of issuing out-of-bounds DMA.

### Required producer, cache and packing integration

The following remains mandatory at the still-missing integrated controller/
decoder boundary; standalone cache modules do not complete these obligations:

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

## Connected code-only cache controller

`anvil_q1_ht3_kv` preserves the parent KV controller's ordered ports and appends
explicit command/store/read/copy cache formats, image tags, a store-fault bit,
and read K/V scale inputs/outputs. The inherited read_fp16/copy_fp16 inputs
remain ABI containers; explicit cache format controls KV encoding, not query
encoding. The controller connects `u_provisional`, `u_committed_reader` and
`u_committed_writer` to real read and write DMA channels. No full-precision
provisional alternative exists in this hierarchy.

Command begin captures slot, format and image ownership. A retain/subset
command cannot introduce a new slot or change image/format. Stores pass only
their already converted 16-bit containers, original tags and fault to the
provisional bank; a conversion fault poisons the row rather than completing
it. Image ownership is checked for provisional and committed reads and copies.
Quantized provisional reads return the stored codes with the captured
layer/head K/V scales, never a retained FP32 producer value. Native reads
return their actual stored encodings. Invalid scales are rejected on read;
dequantization and its overflow reporting remain the attention engine's job.

The controller permits one read or one copy transaction, with store/copy
exclusions matching ownership needs. Provisional reads and writes still use
the bank's row-collision/completeness checks. Provisional stores do not modify
committed DDR and therefore do not unnecessarily invalidate a concurrent
committed-read cache. Copy and image/sequence invalidation do invalidate it.
Copy captures the selected node/layer/position and descriptor regions, reads
every coordinate from the complete provisional row, and streams its codes
unchanged into the actual packed writer. Failed/incomplete/image-mismatched
rows cannot generate usable copies. No dequantize/requantize boundary is
inserted.

Separate reader, writer and provisional response reservations survive
flush/abort long enough to drain. A flush annuls row ownership immediately,
but cannot leave a held provisional response to be consumed by a later read
or copy. Already displayed/accepted DDR transactions are drained by the
adapters. A held public read/copy response retains all payload and error
fields until transfer, even on later abort. Copy response is successful only
after the writer's actual required responses retire successfully; it is not
itself permission to advance the prefix. The missing execution controller
must aggregate every selected node and layer, and publish prefix advancement
transactionally after all copies succeed.

### Cache-controller no-stall cycle formulas

For a legal provisional read accepted at E, the bank request transfers at
E+1, its synchronous response retires into the controller at E+2, and the
held public response first transfers at E+3. An admission error is visible
after E and first transfers at E+1. Neither accepts a replacement read on
its response-retiring edge.

A committed read accepted at E enters the packed reader at E+1. Relative
to that packed-reader acceptance, use the adapter formulas above; the
controller adds one final held-response transfer edge. Thus a cache hit first
transfers publicly at E+8 and a miss at
E+10+lambda_K+lambda_V, with request stalls and external return latencies
counted as defined for the adapter. Actual codes and both scale tags are
registered with the result.

For a legal copy accepted at E, writer command transfers at E+1, its
offset/address/check execute at E+2..E+4, and input readiness is observed at
E+5. The first provisional read accepts at E+6, its response retires at
E+7, and the first code pair enters the writer at E+8. Each subsequent
coordinate takes three edges (read request, response capture, writer input).
Final code-pair input is B=E+3*C+5. The packed writer's DMA/write-response
formula applies from B; the controller's public copy response first transfers
one edge after that writer response transfers. Copy-read faults abort the
reserved writer and wait for its failed response rather than inventing a
copy completion. Flush/abort completion waits for *all* previously reserved
provisional/reader/writer responses; its bound is their remaining documented
transaction bound plus externally imposed memory/output stalls.

The FP32 producer-to-converter connection under the decoder, scale-table
lookup ownership, branch selection and full commit/prefix executor remain
unimplemented. Connected cache adapters alone do not satisfy the mandatory
store-to-subsequent-attention model transaction.

## Required integrated datapath

The literal decoder instances must be `u_epilogue` and `u_flash_attn`, with
`u_tensor_array` under the actual projection containing four physical slots
times 64 MAC rows. Naming disconnected modules is not integration.

The graph is input norm -> Q/K/V -> Q/K RoPE -> attention -> output projection
plus residual -> post-attention norm -> gate/up SwiGLU -> down projection
plus residual, repeated per layer, then final norm and logits.

The tensor is now connected under the actual HT3 projection. That projection,
the epilogue, attention and cache controller must still be connected
to the actual decoder/top; their presence alone is not model execution
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
