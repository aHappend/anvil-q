# Anvil-Q2-FP2 implementation architecture

## Current source handoff status

The saved sources implement arithmetic leaves, MX encoding/decoding, the
two-owned-slot weight prefetch, the 128-lane tensor stream, CSR telemetry,
two-stage nonlinear units, fused epilogues, a six-query online attention
engine and a tagged DDR transport. The accelerated token graph controller
and compatibility top integration are not yet implemented. The new engines
are therefore not yet an integrated accelerator. This increment is not a
completed design handoff and establishes no functional verification result.
See `SPEC.md` for the unchanged full acceptance contract.

## Tensor dataflow and ownership

`anvil_q2_fp2_bfp_tensor_array` contains literal `ping_pong_prefetch`.
Each slot stores one 128-element decoded BF16 weight tile. A fill pointer
exclusively owns an incomplete slot; its beat count is 0..3 for BF16 or
0..1 for MX. The read pointer owns completed tiles in order. Completion
publishes all 128 halfwords, metadata and accumulated error atomically.
The reader releases its slot only when a matching activation transfer occurs.
The producer may fill the other slot while a completed tile is pending or
being consumed. No combinational downstream-ready chain reaches DDR.

Metadata (`format`, `first`, `last`, `tag`) must be consistent across beats.
Beat completion, not a gap in valid, defines a tile boundary. A flush discards
both local slots and partial fills; the external request controller separately
retains and drains accepted bus requests. Error tiles remain explicit
transactions and cannot silently turn into successful zeros.

Seven registered stages capture and group-align the operands:

| Stage | Work |
| --- | --- |
| 0 | Capture both full BF16 tiles; mask inactive lanes to positive zero |
| 1 | Pairwise exponent maxima |
| 2 | Four-lane exponent maxima |
| 3 | Eight-lane exponent maxima |
| 4 | Sixteen-lane exponent maxima |
| 5 | Thirty-two-lane exponent maxima |
| 6 | Preserve sign and full eight-bit significand; compute lane residuals and group bases |

For each BF16 element let E be the encoded exponent, E'=max(E,1), and
M={E!=0,fraction[6:0]}. Its exact value is sign*M*2^(E'-134).
For group maxima A and W, lane residuals are A-Ea' and W-Ew'.
The multiplier therefore uses exponent
`A + W - 268 - residual_a - residual_w` with the exact 8-by-8 product.
This is a lossless shared-exponent representation, not truncation to a
common short mantissa. The maxima and residuals participate in product
exponent arithmetic. Even the widest BF16 exponent spread remains exact.

Three product stages independently round each lane to FP32. Seven levels of
four-stage FP32 adders then reduce adjacent pairs. Product stage zero is
stream stage 7; the final sum is stage 37, meeting the specified 38 registered
stages. A single fabric enable freezes every arithmetic/metadata register when
the final output stalls; no long ready ripple through 38 stages is needed.
When enabled, the arithmetic accepts one paired tile each clock. The
512-bit memory feed independently limits long-stream tile supply.

Masked operands become +0 before classification. Thus masked NaN payload
bits are not active operands, while every unmasked nonfinite operand,
failed weight tile, tag/row-marker mismatch and intermediate arithmetic
failure is carried to the final failed transaction.

## Arithmetic leaves

`anvil_q2_fp2_add4` uses order/alignment, sum, normalization, round/pack
register cuts. Alignment retains guard/round/sticky information; cancellation
is normalized before ties-to-even rounding. `anvil_q2_fp2_mul3` uses exact
product, normalization and round/pack cuts. The BFP product variant shares
the product-rounding hardware while accepting the lossless aligned record.
Arithmetic special cases implement canonical NaN, infinity and signed zeros;
architectural consumers propagate nonfinite classifications as errors.
No FP operator is implemented with synthesizable real arithmetic or division.

## Nonlinear datapaths and design-time constants

`anvil_q2_fp2_nonlinear.sv` contains the two-stage `rsqrt2`, a two-stage
positive normalized reciprocal and the nine-stage exponential. Their constants
are ordinary shipped RTL in `anvil_q2_fp2_coefficients.sv`, reproducible from
the delivered root with:

```sh
python3 fpga/generate_fp2_coefficients.py
```

The generator uses Python's standard-library 100-digit decimal mathematics
and integer ties-to-even rounding. It generates design constants, not stimulus
or expected DUT outputs, and is not a verification oracle. No tool or package
installation is needed. Independent Verifier mathematics must not copy these
tables as its numerical reference.

Rsqrt stage zero normalizes all positive finite binary32 inputs, including
subnormals, and captures one of 2048 coefficient pairs (1024 mantissa
intervals and two exponent parities). Each interval is centered at m0.
For exponent parity p, y0=1/sqrt(2^p*m0) and slope=y0/(2*m0).
The second stage evaluates y0-slope*(m-m0), rounds to binary32 and restores
the even-exponent scale. This is the seed-derived Newton correction
`y0*(3 - 2^p*m*y0*y0)*0.5`, with its constant products tabulated rather
than three cascaded FP32 multipliers. Coefficients use Q34 and retain the
full binary32 mantissa residual. Two globally enabled registers retain both
items under output stalls; readiness never accepts an unstoreable item.

The reciprocal similarly tabulates the Newton tangent
`2*y0-m*y0*y0` across 2048 mantissa intervals, with Q34 coefficients.
Its intended exercised domains are positive attention denominators and
SwiGLU denominators in [1,2]. It explicitly errors on nonpositive/nonfinite
inputs or a result outside its normal binary32 packer's supported range;
the graph must not use it as an unrestricted underflowing reciprocal.
RMS does not use this approximation for 1/N: a separate 8960-entry ROM
contains correctly rounded rational binary32 constants for every legal N.

The exponential accepts finite nonpositive inputs. Values below -80 return
+0; positive nonzero and nonfinite inputs fail. Its registered cuts are
Q40 magnitude conversion, Q48 log2(e) multiplication, integer/fraction
separation, centered coefficient lookup, linear/residual-square products,
quadratic product, fixed-point polynomial sum, normalization, and RNE packing.
The centered fractional interval has width 1/1024; Q40 coefficients describe
the degree-two local expansion of 2^-fraction. Integer range reduction
restores the power-of-two exponent. No iterative divide or real arithmetic
is present. These constructions still require independent ULP testing and
native timing analysis; coefficient precision is not evidence of acceptance.

## Fused epilogue

`anvil_q2_fp2_epilogue_fusion` contains the required literal `inverse_sqrt`
instance. Independent RoPE/residual/pass/SwiGLU elements are serialized at
the stream boundary while their internal arithmetic pipelines retain the
frozen 7/4/1/24-stage schedules. Full element metadata is owned until
retirement. A registered cleanup cycle clears arithmetic valids before the
next transaction; it does not form a combinational output-valid/flush loop.

RoPE uses four parallel three-stage products followed by the two four-stage
add/subtract branches. Actual theta-dependent FP32 coefficients must be
supplied by the future graph controller; the epilogue does not synthesize
identity coefficients. SwiGLU uses exp9, denominator add4, reciprocal2,
a three-stage negative/nonnegative sign-product slot, gate mul3 and up mul3.
The captured gate and up operands cannot change while the result is stalled.

RMS owns at most 8960 FP32 x/gamma pairs, held only for local replay.
These are internal bounded register storage, not architectural memory writes.
Inputs are accepted four clocks apart; square mul3 feeds ordered sum add4,
with a same-edge feedback selection for consecutive sums. The last sum feeds
mean mul3, epsilon add4, `inverse_sqrt`, normalization mul3 and gamma mul3.
Replay metadata is delayed alongside both products. Input index, first/last,
length and vector tag are checked before storage writes. Malformed metadata
becomes an explicit failed output, not an array access outside the owned range.
N=1 uses the same path and schedule.

## Six-query attention

`anvil_q2_fp2_flash_attn` retains six query heads, one decoded KV token tile,
six running maxima/denominators and six HEAD_DIM-sized numerator vectors.
It does not allocate sequence-sized score or probability storage. The
supported TILE_TOKENS parameter bounds the tile size; the current engine
uses the one-token minimum tile for every legal setting. It does not claim
multi-token tile overlap.

After each KV acceptance, six distinct queries issue on consecutive clocks
through a 128-position balanced FP32 dot tree (out-of-head lanes are +0).
Three-stage score scaling uses the correctly rounded constant
1/sqrt(HEAD_DIM). Head metadata follows all 34 score stages.
KV decoding and score computation never request a second external copy
for another query. The future graph controller is responsible for making
the actual single payload/scale transfer sequence and its accounting visible.

For the first token, each head initializes its numerator directly from v,
its denominator to 1 and maximum to its own score. Later tokens compute
both running-max deltas in parallel, use two exp9 streams, and stream
alpha*old + beta*new through two mul3s and one add4. The denominator is an
additional element of that same update stream. Six heads are updated
independently. Only the final causal token triggers reciprocal normalization.
Tag, complete output vector and error are retained until output acceptance.

Command length must equal position+1. Index progression and the last marker
are checked at every KV transfer, including length one; invalid scale,
nonfinite operand, memory error and malformed metadata yield failed
transactions. The local stream cannot detect an absent future transfer
without an external timeout; responsive-environment progress and the frozen
cycle bound remain independent verification obligations.

## Tagged DDR transport

`anvil_q2_fp2_ddr_engine` accepts logical beat descriptors and returns their
completed responses in descriptor order. External response order is arbitrary.
Each slot owns descriptor, unique external tag, response storage and one of
FREE/QUEUED/SENT/COMPLETE states. Separate allocation, issue and retirement
cursors wrap explicitly at the legal final slot, including odd depths.
QUEUE_DEPTH=1 still allocates two physical DDR slots to preserve the admitted
minimum of two outstanding reads; larger legal depths allocate that many.

The external tag sequence is not reset by flush. Allocation stalls on the
otherwise theoretical sequence-wrap collision with any live tag. Only a
matching SENT tag may write a response slot; unknown and duplicate responses
are consumed and reported through the protocol-fault output, never attached
to another request. A malformed tag does not discharge a real outstanding
request: the environment must eventually supply that request's actual
response to allow drain completion.

Flush annuls QUEUED and COMPLETE work, retains every SENT obligation and
disables new requests and client responses. Matching responses drain without
being published; a completion pulse follows removal of the final SENT slot.
Reset clears visible ownership and outputs. A stalled request is selected
from an unchanged owned descriptor, so its entire payload is stable.
This module is a controller/bridge boundary, not a physical DDR4 controller
or board integration.

## MX decode boundary

`anvil_q2_fp2_mx_decode` interprets E4M3FN and unsigned E8M0, not the
parent int8 cache representation. A four-bit exact significand and signed
binary exponent suffice; conversion to BF16 includes gradual-underflow RNE.
Scale 255, E4 NaN, and BF16 overflow are explicit errors. Zero preserves its
sign even with extreme legal scales.

## CSR boundary

`anvil_q2_fp2_telemetry` is independent of datapath backpressure.
One captured request occupies stage zero; its response occupies stage one.
No new request is accepted until that response retires. Read values capture
at request acceptance, so delayed response consumption cannot tear a word.
Writes and snapshot/clear effects apply at acceptance. A snapshot selects
the coherent captured bank until another snapshot or clear.

Read-only counter words zero-extend their saturating legal width to 64 bits.
Clear resets live and snapshot banks, clears snapshot selection, and dominates
same-edge increments. Simultaneous clear/snapshot selects an all-zero snapshot.
Feature/status reports accelerated capabilities and activity; it is not a
claim that runtime verification or physical acceptance has passed.

## Remaining integration obligations

The graph controller must retain only true graph/branch state, feed GEMV row
results directly into the selected epilogue, accumulate multi-tile rows in
ascending column order and preserve Qwen bias placement. RMS replay and branch
joins need bounded owned register storage. Attention must consume one KV
stream for all six query heads with no sequence-sized score/probability SRAM.

The compatibility branch must instantiate the unmodified parent literally.
The graph must connect the tagged DDR engine to real work, account for
metadata fetches and wait for cancellation draining. It must
translate parent projection coordinates explicitly to output-row-major
logical tensors; this transpose mapping will be documented with the
implemented graph controller rather than guessed here.

`fpga/anvil_q2_fp2.sdc` provides the required 10 ns clock baseline without
false-path or multicycle exceptions. Device assignments and the complete
source manifest remain an integration obligation. A constraint file alone
does not establish STA closure.

## Claim-to-evidence guide

Independent behavior/numerics receipts establish observed correctness only for
their actual coverage. Defect receipts establish successfully compiled exercised
mutant detection. Benchmark receipts establish fixture-specific cycles and
accepted external traffic, not official-checkpoint quality. Yosys receipts
establish logical structure/proxies. Only native comparable Quartus receipts
establish target timing, ALMs, DSPs, registers and RAM; only native board
receipts establish physical deterministic execution. The absent parent handoff
must not be replaced with invented numbers. The shared runtime produces the
independently reviewed product PDF after engineering acceptance.
