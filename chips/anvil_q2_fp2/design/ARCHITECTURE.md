# Anvil-Q2-FP2 implementation architecture

## Current source handoff status

The current increment implements arithmetic leaves, MX encoding/decoding, the
two-owned-slot weight prefetch, the 128-lane tensor stream and CSR telemetry.
The accelerated token controller, fused epilogue, rsqrt2, attention
and compatibility top integration are not yet implemented. This increment is
not a completed design handoff and establishes no verification result.
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
The DDR engine needs independently tagged outstanding slots and response
reordering, accounted metadata fetches and cancellation draining. It must
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
