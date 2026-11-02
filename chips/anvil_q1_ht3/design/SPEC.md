# Anvil-Q1-HT3 implementation specification

Version: `v3.0.0-ht3-fp-flash-fused`.

## Authority and implementation status

The admitted work order remains the complete product contract. This document
records implementation decisions, not a substitute or relaxation of its
acceptance criteria. No linked repository-intake index, parent specification,
historical benchmark fixtures or parent acceptance receipts were supplied.
Compatibility must be derived from `anvil_q1_ht2_reference/rtl/`, which is
read-only provenance, not a numerical oracle.

**Current implementation is incomplete.** The current owned RTL consists of
arithmetic and write-conversion foundations. There is not yet a connected HT3
top, decoder, tensor array, fused epilogue, tiled attention engine, extension
scale/image controller or packed committed-cache transport. A standalone
converter does not satisfy integrated store-to-subsequent-attention acceptance.
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

Required but not yet implemented primitives retain the admitted contracts:
exp 32 enabled stages and sin/cos 64 enabled stages. These latencies must not
be inferred from parent operator modules.

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

The epilogue's exact admitted four-slot streaming interface and modes 0..6
remain fixed. Mode 7 errors. RMSNorm uses epsilon `0x358637bd`, FP32 statistic
and FP32 gamma multiplication without internal BF16 narrowing. RoPE uses
theta=1e6, split-half pairing and all legal positions. SiLU must use stable
branches/range reduction for large negative inputs. Bounded private
whole-vector/pair retention is permitted but must be counted; shared-scratch
operator-boundary round trips are not fusion.

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
