# Anvil-Q2-FP v1.2.0-bf16

## Authority and implementation status

This document freezes the admitted product contract. It is not a test result.
The unchanged `anvil_q2_reference/rtl/` is the parent source, not a passing
baseline. Designer owns `rtl/` and `design/`; independent Verifier owns `tests/`.
The shared runtime owns timing, physical-board gates and the final independently
reviewed product PDF. That PDF is not a prerequisite for engineering checks.

See `ARCHITECTURE.md` for the implemented boundaries and `INTEGRATION.md` for
source-level integration. No functional, synthesis,
timing, resource or hardware pass is claimed by these documents.

## Product and legal parameters

The top is `anvil_q2_fp_top`, for Qwen/Qwen2.5-1.5B-Instruct, not Q1.

| Parameter | Default | Legal settings |
| --- | --- | --- |
| BANKS | 4 | 1, 2, 4 |
| FP_FORMAT | 0 | 0 BF16; 1 IEEE binary16 |
| WEIGHT_MODE | 0 | 0 native selected-format weights; 1 W4A16 AWQ |
| CACHE_MODE | 0 | 0 native packed K/V; 1 block-scaled INT8 |
| NUM_LAYERS | 28 | positive |
| HIDDEN_SIZE | 1536 | positive; NUM_Q_HEADS * HEAD_DIM |
| INTERMEDIATE_SIZE | 8960 | positive |
| NUM_Q_HEADS / NUM_KV_HEADS | 12 / 2 | positive integral GQA ratio |
| HEAD_DIM | 128 | positive even |
| GROUP_SIZE / AWQ_BITS | 128 / 4 | positive dividing hidden and intermediate / exactly 4 |
| VOCAB_SIZE / MAX_SEQ_LEN | 151936 / 32768 | positive / 1..16777215 |
| CACHE_BLOCK | 16 | positive power of two dividing HEAD_DIM |
| QUEUE_DEPTH | 3 | 1..16, including non-power-of-two depths |

Hidden, intermediate and KV-vector sizes are multiples of eight. Dimensions,
products and addresses retain all bounds in the parent parameter validator:
individual dimensions fit unsigned 32 bits; V*H, H*H, H*I, H*K*D,
L*S*K*D, S*D, 2*D, 15*H, 15*I, K*NB*NW, L*S*K*NB*NW and L*S*K*NB
are at most 4294967295, where NB=D/CACHE_BLOCK and
NW=ceil(CACHE_BLOCK/4). These are elaboration-time calculations only.
Illegal parameters must explicitly diagnose `PARAMETER ERROR` without unsafe
zero-width declarations or unbounded elaboration. Diagnostic-only safe widths
must not alter any legal configuration.

## Cycle & Degenerate-Boundary Table

| Boundary | Pre-edge condition | Post-edge effect / priority |
| --- | --- | --- |
| Transfer | valid && ready immediately before rising edge | exactly one acceptance; updated state/payload observed after edge |
| Active reset | rst_n=0 | asynchronous state reset; every public output bit zero, including ready and data |
| First clock after reset release | no pre-edge valid/ready pair | no fabricated transaction; idle readiness may assert |
| Held result/request | valid && !ready | valid and complete payload remain stable until transfer, reset or specified cancellation |
| Top scalar request buffer empty | scalar mux valid && buffer ready | capture complete request; scheduler can first accept it at the next edge |
| Top scalar request buffer full | scheduler client ready | transfer once and clear occupancy; no same-edge refill or combinational ready look-through |
| Top scalar buffer reset/cancel/fault annul | numerical core reset asserted | discard requests not yet accepted by scheduler; scheduler still drains its accepted transactions |
| Attention request buffer empty | selected local memory request valid && local ready | capture complete request; expose downstream valid after edge, with earliest downstream transfer at following edge |
| Attention request buffer full | downstream valid && ready | retire once and clear occupancy; no same-edge refill or ready look-through; otherwise hold every payload bit |
| Attention request buffer reset | rst_n=0 (numerical core annul when integrated) | clear occupancy and payload; discard only locally buffered work, never scheduler-owned transactions |
| Lane first && last | accepted singleton beat | reset logical accumulator to +0, add this product once, emit last=1 |
| Lane first reaches S3 | ready3 && v2 && first2 | select the rounded product after the ordinary accumulation cone; canonicalize either product zero to +0, exactly matching RNE(+0 + product) |
| Lane bubble | !in_valid or !in_ready | no arithmetic/accumulator update for that beat |
| Back-to-back dots | next accepted first follows prior last | no interleaving; next first replaces accumulator base with +0 in S3 |
| Lane occupied output stall | out_valid && !out_ready | occupied stages freeze; no replay of S3 accumulation |
| AWQ lane unchanged since startup | accepted command with any fixed in_lane | continuously selected nibble follows [0,16,4,20,8,24,12,28]; no lane transition required |
| AWQ signed-zero scale | accepted finite +0 or -0 scale | multiply delta by scale normally; preserve IEEE product sign through selected-format conversion |
| QUEUE_DEPTH=1 | single reservation | no assumed binary wrap; preserve ordering and held transfers |
| QUEUE_DEPTH=3 | last slot retires / new allocation | explicit wrap, not a power-of-two mask |
| GROUP_SIZE non-power-of-two | last component of group | explicit offset reset and group increment |
| Single row group / vocabulary / position | first is also last | retire once; no zero-length extra group/iteration |
| Cache read+commit | commit acknowledgements sampled at edge | a pre-edge read cannot observe post-edge validity |
| Failed/partial commit | any write error | invalidate; no partially written token becomes readable |
| New sequence | accepted new_sequence at position zero | annul old cache visibility before new work |
| Cancel/flush plus held memory handshake | held valid && ready before flush edge | parent scheduler accounts for accepted request and drains its response |
| Cancel/flush plus response | accepted response before edge | account once; never commit cancelled arithmetic into new token |
| Fault versus normal completion | fault on same edge | token fails and outstanding accepted traffic drains |
| Decoder command acceptance | idle and cmd_valid | register step zero and its normalization routing/modes together |
| Decoder successful step completion | finished selected engine, no fault, step below ten | advance step and register next engine/projection/modes on the same edge; no extra command cycle |
| Decoder in-flight or fault completion | no successful step transition | hold registered routing through all request/response ownership; reset or next command reinitializes it |
| GEMV bias command | BIAS_ADD and bias adder ready | capture selected final sum, expanded bias and one-hot writeback destination once; hold row index while waiting |
| GEMV bias arithmetic | command accepted at E0 | operand capture E0, order/classify E1, distance E2, align E3, add/subtract E4, normalization distance E5, normalize E6, RNE E7, pack/output E8; earliest result transfer E9 |
| GEMV bias completion | BIAS_ADD_WAIT and adder valid | reject nonfinite result or write exactly the registered one-hot destination; only then advance row or start scratch writes |
| GEMV bias reset/cancel | numerical core reset asserted | annul pending arithmetic and result; no partial bias result writes a sum |

All sequential RTL uses `always @(posedge clk or negedge rst_n)` and
nonblocking state assignments. Combinational division and modulo are forbidden.

## Top and scheduler ABI

Preserve the parent's port names, directions and packed widths:
`clk/rst_n/cancel`; `token_valid/token_ready`, unsigned 32-bit
`token_id/token_pos`, `new_sequence/token_phase`;
`logit_valid/logit_ready`, unsigned 32-bit `logit_index/logit_data`;
`done/error/cancel_done`; and SB=BANKS tagged memory banks.
Per-bank widths are kind=4, projection=3, layer/row/col/data=32, tag=64;
bank b occupies bits b*width +: width.

**Numerical ABI revision:** logit_data is an IEEE FP32 encoding, not Q16.16.
Prefill/decode transition, position validation, cancellation, recovery,
logit backpressure and response-error interpretation retain parent semantics.
The parent scheduler, bus mux, scalar arbiter and memory-port modules retain
their original names and implementations. Preserve unsigned monotonic 64-bit
tags, exhaustion without reuse, per-client in-order retirement, cross-bank
out-of-order response acceptance, round-robin ingress, independently held
requests and flush-edge accounting. Bank selection is the low bits of
kind+layer+projection+row+column.

The top's scalar client has a one-entry registered request buffer between
the numerical bus muxes and scheduler ingress. It captures valid and all
request fields together and holds them until scheduler acceptance. Responses
return through the existing muxes without an added register. This adds one
unstalled request cycle, not an arithmetic stage or a change to the public
memory ABI. BANKS projection clients bypass this scalar-only buffer and retain
independent scheduler access.

Attention additionally registers its complete scalar request immediately after
its local cache/scratch mux, before the decoder and top muxes. This one-entry,
non-fall-through buffer adds one unstalled request cycle for attention traffic.
Its upstream acceptance does not complete a memory operation: the originating
controller still waits for the actual downstream response. Response routing,
numerical operation order and the three-stage tensor lane are unchanged.
Reset clears the buffer; integrated cancellation uses the numerical core reset
while the parent scheduler retains responsibility for previously accepted tags.

Required source hierarchy:

```
anvil_q2_fp_top
  bank_scheduler: anvil_q2_bank_scheduler
  decoder: anvil_q2_fp_decoder_layer
    gemv: anvil_q2_fp_gemv
      banks[b].lane: anvil_q2_fp_dot_lane
    rope: anvil_q2_fp_rope
    attention: anvil_q2_fp_gqa_attention
      kv_cache: anvil_q2_fp_kv_cache
        codec: anvil_q2_fp_cache_codec
    mlp: anvil_q2_fp_swiglu_mlp
    residual: anvil_q2_fp_elementwise
  final_norm: anvil_q2_fp_rmsnorm
```

MLP projections use the same banked floating-point GEMV.

## Floating-point rules and tensor lanes

BF16 has sign/8-bit exponent/7-bit fraction; FP16 has sign/5-bit exponent/
10-bit fraction. Scalar, scratch and accumulation values are binary32.
Round every specified operation separately using nearest, ties to even,
with gradual underflow and signed zeros. Canonical arithmetic NaNs are
FP32 0x7fc00000, BF16 0x7fc0 and FP16 0x7e00. Arithmetic units propagate
IEEE infinities, including invalid operations producing canonical NaN.
Model execution rejects external nonfinite loads and invalid/overflowing
arithmetic with an explicit token/cache error, then drains traffic.
Arithmetic unit coverage must still include nonfinite operands.

Each bank owns eight output accumulators. Bank b starts at row 8*b,
advances by 8*BANKS and masks tail rows. Accumulate ascending input columns,
without reassociation. Dot-lane ports are clk/rst_n, in_valid/in_ready,
in_a[15:0], in_b[127:0], in_first/in_last, out_valid/out_ready,
out_sum[255:0], out_last. Weight lane j is in_b[16*j+:16]; sum lane j is
out_sum[32*j+:32]. Every accepted beat produces one running-sum beat.
Only final sums commit GEMV output, followed by one FP32 bias addition.

Exactly three arithmetic register captures:

| Edge | Action for beat accepted at E0 |
| --- | --- |
| E0 | S1 unpack/classify and exact significand product |
| E1 | S2 normalize and RNE-round product to FP32 |
| E2 | S3 RNE-add product to FP32 accumulator; output valid |
| E3 | earliest receiving handshake |

The empty unstalled latency is those three captures, without another output
register. Initiation interval is one beat/clock. Bubbles do not accumulate;
elastic stalling must neither replay nor discard a sum. The dot stream cannot
interleave unfinished dots.

S3 uses parallel close-subtraction and far-addition paths, selected by operand
signs and effective exponent distance. Close subtraction preserves an exact
25-bit difference; far addition uses guard/round/sticky alignment with at
most one-bit normalization. This changes neither the RNE FP32 operation nor
the cycle table. First-beat selection remains after the ordinary-add result,
with combinational preservation attributes and no added register capture.

Linear inputs round to A16 at GEMV entry; native weights, scales, biases,
embeddings and norm weights are selected-format 16-bit tensors.
Q/K/V round at the attention/cache boundary. Residuals and logits stay FP32.
No wholesale Q16.16 conversion is allowed.

AWQ projection IDs are 0 Q, 1 K, 2 V, 3 output, 4 gate, 5 up, 6 down.
Nibble shifts are [0,16,4,20,8,24,12,28]. Compute delta=qweight-qzero
without +1, multiply by nonnegative finite selected-format scale in FP32,
then round effective weight to the selected 16-bit format.
Negative nonzero/nonfinite scales fail; zero scales yield signed zero weights
with sign equal to the XOR of the converted delta sign and scale sign.
The integer delta zero converts to +0. Both signs of zero scale follow the
same FP32 multiplication and selected-format conversion path as other finite
scales; they are not canonicalized to +0.
This preserves layout and dequantization meaning, not parent fixed-point
bit identity.

## Transformer operators

Execute embedding, every decoder layer, final RMSNorm and output projection.
Each decoder executes pre-attention RMSNorm, biased Q/K/V projections,
split-half RoPE, causal GQA, output projection, residual, pre-MLP RMSNorm,
SwiGLU gate/up/down projections and residual.
GQA heads are contiguous groups of six by default.

RMSNorm sums FP32 squares in ascending component order, divides in FP32 by
the dimension, adds FP32 RNE(1e-6)=0x358637bd, then uses correctly rounded
FP32 square root and reciprocal/division. Scalar division/square root must
be registered iterative/pipelined, not an unrolled combinational divider.
RoPE pairs i and i+HEAD_DIM/2 with
angle=position*1000000^(-2*i/HEAD_DIM). External table transactions supply
FP32 cosine/sine and require independent angle validation.
Softmax subtracts the row maximum, accumulates exponentials and weighted
values in ascending causal token order in FP32, and divides by the FP32
sum. SiLU uses exp(-abs(x)) for stable evaluation.

The common exponential is fixed: for x<=0,
n=RNE_integer(FP32(x*FP32(log2(e)))),
r=FP32(x-FP32(n*FP32(ln(2)))); degree-seven Taylor Horner evaluation
with coefficients FP32 RNE(1/k!), separate FP32 multiplication/addition,
then RNE scaling by 2^n. Return +0 for x<-80 and exactly one for either
zero. Required absolute error against high precision is <=1e-5 on [-80,0],
including boundaries and range-reduction transitions. No alternate
approximation is permitted for SiLU or attention.

## External memory coordinates

Every request has separate kind/layer/projection/row/column coordinates.
Native scalar transactions occupy low 16 bits with high 16 bits zero,
except the specified packed cache. Reads and writes both require a response;
write acceptance alone is not a successful acknowledgement. Any response
error fails its operation. No completed write may be assumed before response.

| Kind | Meaning / coordinates |
| --- | --- |
| 0 | embedding/output weights: layer=0, proj=0, row=token/vocabulary, col=component |
| 1 | native projection: row=input component, col=output component; AWQ packed parent columns |
| 2 / 3 | AWQ packed zero / scale; parent group and packed-column addressing |
| 4 | selected-format bias; layer/proj select projection, row=0, col=output |
| 5 / 6 / 7 | pre-attention / pre-MLP / final norm weights; col=component; final layer=0 |
| 8 | FP32 scratch; parent slot routing below |
| 9 / 10 | packed selected-format K / V; row=token, col=(head*HEAD_DIM+dim)>>1 |
| 11 | FP32 RoPE cosine/sine table; parent coordinates |
| 12 / 13 | packed INT8 K / V; row=token, col=block-word coordinate |
| 14 / 15 | signed block exponent metadata for K / V; row=token, col=block coordinate |

Cache layer is always a separate coordinate. Cache mode 0 packs consecutive
components, lower component first. Cache mode 1 has block coordinate
head*(HEAD_DIM/CACHE_BLOCK)+block, and word coordinate
block_coordinate*ceil(CACHE_BLOCK/4)+word. Pack four signed bytes LSB first,
padding high unused bytes with zero for blocks of one or two.

Scratch transactions retain layer=0, projection=0, row=slot, col=component.
Tokens execute serially, so scratch storage is reused across positions and
layers only after the preceding operation completes. Slots are:

| Slot | Value |
| --- | --- |
| 0 | embedding/current residual |
| 1 | pre-attention normalized input |
| 2 / 3 / 4 | Q / K / V projection results; RoPE overwrites Q/K |
| 5 | attention context |
| 6 | attention output projection |
| 7 | post-attention residual |
| 8 | pre-MLP normalized input |
| 9 / 10 | gate / up projection |
| 11 | SiLU(gate)*up |
| 12 | down projection |
| 13 | unused parent slot |
| 14 | final normalized residual |

AWQ kind 1 uses row=input component, col=output component>>3; kind 2
uses row=group index, col=output component>>3; kind 3 uses row=group
index, col=output component. Group index starts at zero per projection
and advances after GROUP_SIZE ascending inputs. Model projection transactions
carry the selected layer and projection; biases are loaded for Q/K/V only.
Native projection mode does not issue kinds 2/3.
All norm kinds use row=0, projection=0 and col=component; kinds 5/6 use
the current layer, and kind 7 uses layer=0.
RoPE kind 11 uses layer=0, projection=0, row=position, col=2*i for
cosine and 2*i+1 for sine. The same table serves every head and layer.

For otherwise unspecified output-operation order, RMSNorm computes
FP32(FP32(x*FP32(1/sqrt(mean_square+eps)))*gamma).
SiLU computes e=exp(-abs(x)), d=FP32(1+e),
s=FP32((x has negative sign ? e : 1)/d), and FP32(x*s);
the subsequent up product is another separately rounded multiplication.
RoPE uses four separately rounded FP32 products and then the indicated
FP32 subtraction/addition.

Attention computes score=FP32(dot/FP32(sqrt(FP32(HEAD_DIM)))), with
dot starting at +0 and separately rounded products/additions in ascending
dimension order. It computes all scores and their maximum before any
exponential, then sums exponentials in ascending causal position order.
For each context component it separately sums FP32(exponential*V) in the
same position order and divides the final sum by the FP32 denominator.
The output projection reads slot 14 and kind-0 weights, rounds each linear
input to the selected format and accumulates separately rounded FP32
products in ascending component order. Kind-0 weights are native in both
WEIGHT_MODE settings; AWQ compatibility covers the seven decoder projections.

## KV quantization and visibility

Independent blocks per layer/token/head and separately K/V use the smallest
integer e with max(abs(x))<=127*2^e; zero blocks use e=0.
Quantize q=RNE(x/2^e) in [-127,127], and reconstruct selected-format
RNE(q*2^e) before FP32 expansion. -128 is reserved and must fail decode.
Metadata is a signed 16-bit exponent sign-extended to 32 bits.
Nonzero ranges are BF16 [-139,122], FP16 [-30,10]; zero e=0 is legal.
Malformed/out-of-range metadata fails explicitly. Reconstruction overflow
fails; it is not silently clamped or counted as satisfying an error bound.

Per-component error is <=0.5*2^e plus independently computed final-format
rounding allowance. Visibility commits only after all K/V write responses
succeed. Reads before commit, after invalidation/failure or beyond causal
bounds fail. Validity metadata, rather than clearing data RAMs, may invalidate
stale storage.

Storage accounting includes actual data words, metadata, padding and
transactions. A head's K or V mode-0 bytes are 4*ceil(HEAD_DIM/2);
mode-1 bytes are
4*(HEAD_DIM/CACHE_BLOCK)*(ceil(CACHE_BLOCK/4)+1).
No unconditional twofold saving is claimed.

## Independent verification and acceptance

Verifier provides `tests/verify.py --check
behavior|synthesis|defects|benchmark|portability`, with nonzero failure for
missing prerequisites or failed assertions. Required real tools are Python3,
Icarus/vvp or Verilator, and Yosys as applicable. Each execution retains a
unique receipt, source hashes, commands/versions, timestamps, child exits/
timeouts, raw streams and metrics under `evidence/l1/`. Advancing workloads
get child deadlines of at least 3600 seconds. Do not overwrite failures.

Versioned five-domain synthetic workloads: projections/logits; RMSNorm/
residual; RoPE; causal GQA/cache; SwiGLU/integrated decoder/token. All domains
run the complete BANKS=1/2/4 x CACHE_MODE=0/1 x FP_FORMAT=0/1 x
WEIGHT_MODE=0/1 matrix and seeds 17/43/89, including explicit irrelevant
matrix coordinates. Deterministic rational input generation and metrics
are frozen by Verifier before execution. No checkpoint or language-task
accuracy is implied. Parent comparisons run actual AWQ RTL with its actual
fixed-point ABI; parent native mode is not applicable.

Compare every accepted output and visible transaction independently; reject
active X/Z, tag/order/stability errors, missing/duplicate/early/late results,
failed draining, stale cache and unconsumed traffic. Exact normative bits
remain mandatory in addition to high-precision absolute/max/RMS error,
normalized RMSE and defined cosine similarity. Measure accepted/retired
counts, cycles from accepted command through last accepted output,
initiation interval, memory stalls and bank utilization. Speedups come from
actual measured cycles, not bank count.

Required coverage includes >=4096 independently checked lane beats per
format/mode; all IEEE categories and rounding boundaries; back-to-back,
singleton, long and stalled dots; all pipeline occupancies; all 256 INT8
encodings; CACHE_BLOCK=1/2/16 and boundary/extreme/corrupt blocks; scheduler
BANKS=1/2/4 and QUEUE_DEPTH=1/3/16, contention, reverse tags, independent
stalls, unknown/duplicate/wrong-bank tags, response errors and coincident
flush/handshakes/responses; reset/cancel/recovery/invalidation; legal
non-power-of-two group/depth and singleton geometries; and explicit illegal
dimensions, modes and address-overflow diagnostics.

Portable L1 covers complete reduced token execution, native elaboration,
full-size individual projection rows and the 28-layer full-head drift run.
The latter uses >=8 causal positions, actual layer-to-layer residual/output
feedback, FP16 Mode1 versus Mode0, per-layer attention normalized RMSE
<=0.03 and final residual normalized RMSE <=0.05 for the bounded
norm-controlled suite. Report final logit drift and separate adversarial
metrics without extending these bounds to arbitrary inputs.

At least four compiling, comparison-reaching disposable mutants must fail
the normal checker for accumulation/rounding, AWQ layout, cache scale/commit
and response association/stability defects. Compile errors/timeouts are not
defect-sensitivity results. Never mutate accepted RTL in place.

Real Yosys hierarchy/check/synthesis must assert no latches, loops,
undriven required nets, unresolved black boxes or divider/modulo cells and
preserve substantive compute, scalar, scheduler and cache state. Native
default synthesis is mandatory, not replaced by reduced synthesis.
Report parent/product bank/cache statistics separately from target resources.
Clean-directory reproduction copies only declared product and reference
sources and performs fresh compile, simulation, independent comparison and
synthesis without worktree artifacts or private paths.

The shared runtime additionally requires L1.5 timing lint, Quartus 17.1 STA
on Arria 10 GX 10AX115N2F45E1SG at <=10.0 ns, WNS>=0, constrained
functional clocks without functional false/multicycle exceptions, resource
fit, and at least three deterministic numerically checked PCIe Gen3x8
physical-board passes. Native full-shape five-domain timing, including the
integrated 28-layer token path, and the complete bank/cache matrix remain
mandatory. No local JTAG cable/BDF belongs in portable verification.
Only the shared runtime and independent Reviewer can accept delivery.
