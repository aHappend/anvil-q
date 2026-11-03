# Anvil-Q2-FP2 implementation architecture

## Current source handoff status

`anvil_q2_fp2_top` now connects the accelerated token graph, tagged DDR
transport, tensor stream, fused epilogues, six-query attention and telemetry.
Its compatibility generate branch literally instantiates the immutable parent.
Device, source-manifest and clock integration are in `fpga/`. This is a
design handoff for independent verification, not a functional, timing,
performance or delivery acceptance claim. See `SPEC.md` for the unchanged
full acceptance contract and `INTERFACES.md` for the concrete memory ABI.

## Integrated token graph

The default generate branch is accelerated; it does not call the parent
for an accelerated token. The controller loads the BF16 token embedding
and FP32 position-specific RoPE coefficients. For each layer it executes:

1. RMSNorm of the current FP32 residual state with kind-5 BF16 gamma.
2. Q, K and V tensor GEMVs, adding their BF16 biases in FP32.
3. Split-half Q/K RoPE, native or MX KV cache commit, and one causal
   six-query attention transaction per KV head.
4. Output-projection GEMV fused directly with the attention residual add.
5. RMSNorm with kind-6 gamma, gate and up GEMVs joined by SwiGLU, and
   down-projection GEMV fused with the MLP residual add.

After the final layer, kind-7 RMSNorm feeds the tied BF16 embedding matrix
as an output-row-major tensor GEMV. Its FP32 row results pass through the
epilogue to ordered, backpressured logits. Embeddings and tied output
weights are native BF16 in either accelerated weight mode; mode 2 compresses
the seven decoder projection matrices. No accelerated request uses the
parent's kind-8 architectural scratch SRAM.

The controller retains one FP32 row pipeline register between the tensor
row accumulator, optional bias add and selected epilogue. Q/K first halves
are the necessary split-half join, not a second tensor-result SRAM. Gate
results are the real branch join with the later up result. The up result
feeds SwiGLU directly and is not stored separately. Output/down results
feed residual addition directly. RMS uses only its bounded local replay.
Every rounding boundary into tensor/query/KV storage uses BF16 RNE and
rejects nonfinite/overflow results.

| Owned storage | Capacity | Producer, consumer and release |
| --- | --- | --- |
| Residual state | HIDDEN_SIZE FP32 | Embedding/residual epilogue; RMS replay input and next residual join; overwritten only after its old value is read |
| Hidden operands | HIDDEN_SIZE BF16, 128 banks | RMS or normalized attention; Q/K/V, gate/up or output GEMV; phase changes only after the preceding GEMV's final result retires |
| FFN operands | INTERMEDIATE_SIZE BF16, 128 banks | SwiGLU; down GEMV; separate from still-live normalized gate/up input |
| Q | HIDDEN_SIZE BF16 | RoPE pairs; six-head attention command assembly |
| K and V | NUM_KV_HEADS*HEAD_DIM BF16 each | RoPE/pass epilogue; current-position cache encoder/commit |
| Gate branch | INTERMEDIATE_SIZE FP32 | Gate GEMV; up/SwiGLU join at the same row index |
| RoPE join | HEAD_DIM/2 FP32 | First half of one Q or K head; second half's epilogue; reused only after all pairs of that head retire |
| Bias cache | HIDDEN_SIZE BF16 | Accounted kind-4 reads; one Q/K/V projection at a time |
| RoPE coefficients | HEAD_DIM FP32 | Accounted kind-11 reads for this token; all layer/head rotations |
| DDR/weight/activation staging | Fixed beat/tile/queue bounds | Owned descriptors, returned beats, two tensor weight slots and one activation tile |

`anvil_q2_fp2_scalar_store` has synchronous reads and writes in a dedicated
non-reset memory process. The 128-bank vector store returns one full tile
after a registered read. It never asynchronously multiplexes an entire
8960-element activation vector. Validity, phase ownership and complete
write-before-read initialization protect unreset memory contents. The
controller reads a scalar in a separate FSM state before consuming it.
Reset/cancel does not require a multi-thousand-entry clearing loop.

## GEMV prefetch and row ordering

`anvil_q2_fp2_gemv_stream` independently advances weight loading, activation
tile issue and row reduction. Weight loading continues while a previous row
waits in its fused epilogue, until the two actual tensor slots backpressure
it. Both slots can therefore be live; this is not a controller that waits
for a row to retire before filling its successor.

The frontend queues multiple payload reads through the DDR transport without
waiting for each response. BF16 tiles assemble four tensor beats; MX tiles
assemble two, with two real Group-32 scales per beat. A row-local 64-byte
scale cache is fetched through kind 3 and reused for up to 2048 reduction
elements. Crossing that boundary fetches the next scale beat; changing
output row invalidates the cache. An absent tail payload beat is generated
locally as zero rather than reading a nonexistent tile segment. Padding
lanes and unused scale bytes are masked, while every active scale is checked.

Independent monotonically advancing tile ordinals identify weight fill,
activation issue and tensor result order. Row/column cursors wrap explicitly;
no combinational division computes them. Each row accumulates successive
tile partial sums with the four-stage FP32 adder in increasing input-column
order. Feedback waits for the prior addition before accepting another
partial. The first tile initializes the sum without an extra zero add.
The last result is retained until the controller accepts it, after which
the next row may retire. Request/response tag, row-marker or arithmetic
faults remain failed transactions.

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

### Two-stage correction/packing timing repair

The retained compact post-fit failure in
`.vulcan/engineering/run-0001/quartus-sta.json` reports setup WNS -0.851 ns
at 10 ns, with paths from coefficient storage through rsqrt/reciprocal
correction and packing. That historical receipt is not changed. The following
source repair is pending independent numerical checks and fresh native STA;
it is not timing closure or default-product physical acceptance.

The coefficient generator and all Q34/Q40 constants are unchanged. Exact
range analysis removes only redundant arithmetic bits and normalization:

| Quantity | Rsqrt | Reciprocal |
| --- | --- | --- |
| Centered integer residual d | -4096..4095, signed 13 bits | -2048..2047, signed 12 bits |
| Stored Q34 slope S | 0 < S < 2^33 | 0 < S < 2^34 |
| Exact signed product P=S*d | signed 47-bit result of 34-by-13 operands | signed 47-bit result of 35-by-12 operands |
| Shifted correction C=floor(P/2^23) | -2^22 < C < 2^22 | -2^22 < C < 2^22 |
| Corrected Q34 tangent B-C | 2^33 <= B-C < 2^34 | 2^33 <= B-C < 2^34 |

The last range follows from convex, decreasing tangents to
`1/sqrt(2^p*m)` and `1/m`, with normalized m on the binary32 grid
`1 <= m <= 2-2^-23`. The largest tangent is at m=1 in the first
interval; its distance below one exceeds 1000 Q34 units for both
functions. The smallest is at the largest grid point in the last interval
(p=1 for rsqrt). For rsqrt, the true value exceeds 0.5 by at least
2^-26, while the last-interval Taylor remainder is less than
`(1/20)*2^-22`, leaving more than 50 Q34 units above 0.5.
For reciprocal, the corresponding margin is at least
`2^-25-(1/6)*2^-24`, more than 340 Q34 units. Rounding each Q34
coefficient contributes at most 0.5 unit to its base and
`0.5*abs(d)/2^23` to its correction; flooring the product contributes
less than one further unit. Their combined effect is less than two
Q34 units, so none of these bounds crosses a normalization boundary.
Subnormal inputs use the same normalized mantissa grid and only change
the separately restored exponent.

`anvil_q2_fp2_tangent_pack` therefore uses fixed significand bits 33:10,
not a post-correction normalization mux. It splits B-C at bit 10:
the ten low bits independently determine borrow, guard, sticky and the
unrounded significand's parity. The rounded high result is exactly
`B_hi - C_hi - borrow + round_up`. A carry-save compression of
`B_hi`, `~C_hi` and `1-borrow+round_up` feeds one 25-bit carry-propagating
addition, rather than a full-width subtraction followed by another
significand increment. The product shift is still signed floor, and the
rounding rule is still ties-to-even. No product or coefficient bits needed
by the previous numerical result are discarded. Exponent restoration and
normal-range rejection now run in stage zero, independent of the product.
Out-of-range packing remains an explicit error, not saturation.

The existing coefficient capture registers for rsqrt, reciprocal and exp
now use dedicated rising-edge processes without asynchronous data resets.
Reset/flush still clears their owning valid bits; every valid use follows
a coefficient write on the matching acceptance edge. Captures retain the
same enable, input-valid and flush conditions, so stalls cannot change
the pending coefficients. This supplies a synchronous ROM read boundary
for the unchanged generated case tables, replacing the old capture
processes rather than adding a stage. ROM inference remains a synthesis
question, not an asserted result. Rsqrt/reciprocal remain two stages,
II=1, and exp remains nine stages; all public reset levels and flush
priorities are unchanged. The existing coefficient-mutation anchors
remain in both tangent consumers.

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
add/subtract branches. The graph supplies actual theta-dependent FP32
coefficients from accounted kind-11 reads; the epilogue does not synthesize
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
for another query. The controller reads each causal key/value payload and
its scales once per KV head and broadcasts that one stream internally.
Accepted external reads, including padded beats and metadata, are observable
on the actual DDR boundary.

For the first token, each head initializes its numerator directly from v,
its denominator to 1 and maximum to its own score. Later tokens compute
both running-max deltas in parallel, use two exp9 streams, and stream
alpha*old + beta*new through two mul3s and one add4. The denominator is an
additional element of that same update stream. Six heads are updated
independently. Only the final causal token triggers reciprocal normalization.
Tag, complete output vector and error are retained until output acceptance.

Numerator and normalized-output storage has six fixed head banks, each with
HEAD_DIM independently enabled FP32 words. Every write destination is an
elaboration-time constant: first-key initialization writes all words of the
selected head in parallel, and later update/normalization results enable only
their pipelined component's word. Reads select a component within each bank
and then select the head. This avoids HEAD_DIM variable-address initialization
ports and a full-vector variable output write without changing storage capacity,
arithmetic order or cycle schedule. Numerator words asynchronously clear on
active-low reset and hold during flush; first-key initialization still writes
every word before any numerator read and takes priority over later updates.
Normalized words clear on reset, flush and command acceptance, and hold through
output stalls.

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

## Cache publication, cancellation and compatibility

Native cache commit writes BF16 beats with exact byte strobes; MX commit
encodes each real Group-32, writes E4M3FN payload beats and then writes
the physically transferred E8M0 scale beat. Partial groups exclude padding
from their maximum and use zero padding. Every write has an acknowledged
tagged response. The controller starts attention only after all K/V heads'
payload and metadata writes have acknowledged. No uncommitted current
position can be read by a later command.

New-sequence and monotonic-position/phase tracking are local controller
state. A new sequence begins at position zero and rewrites every causal
cache entry before it can become visible; stale later positions are never
read. Cancellation or an active protocol/numerical fault invalidates this
sequence. Local pipelines and prefetch are flushed, the DDR engine retains
all accepted requests, and the controller waits for its drain-done pulse.
Only then does cancellation acknowledge and, for an active token, report
failed completion. A held cancel cannot repeatedly capture a different
active-token status. CSR processing remains independent throughout.

`ACCEL_ENABLE=0` and supported legacy FP16/AWQ/int8-cache selections use the
literal `anvil_q2_fp_top` instance with unchanged parent parameters, ports
and implementation. The wide DDR interface is inactive there. The narrow
interface is inactive in the accelerated branch. A mode-2 request is never
reinterpreted as a legacy numerical format; unsupported mixed-format
configurations reach a diagnostic-only generate branch.

## Telemetry interpretation and host tuning

Counters use actual pre-edge bus/stream handshakes and controller ownership.
KV bytes include all accepted native/MX KV read and write beats, including
metadata and physical padding, at 64 bytes per beat. DDR read/write counters
separately permit read-traffic accounting. One accepted key/value token
stream has G groups in K and G in V, each reused five more times, so the
reuse event increments by 10*G. It does not increment for merely entering
an attention state or for an unaccepted KV item.

Weight underflow requires an available activation and no published matching
weight tile, tracked by actual completed-tile and paired-tile counts.
Tensor bubbles count active, not-yet-issued tile work without a paired
transfer; idle and arithmetic-drain-only periods are excluded. Saturation
events remain zero because this implementation rejects overflow instead of
saturating. A snapshot provides coherent counters for host analysis.

Host recommendations must distinguish high request-stall fraction
(bridge/DDR service), underflow with low request stall (prefetch/service
latency or short transfers), tensor bubbles without underflow
(activation/control backpressure), and epilogue output stalls (downstream
consumption). Compare accepted bytes and complete cycles before suggesting
native/MX storage or queue tuning. Recommendations do not change arithmetic,
acceptance tolerances or modes while a token is active. The independent
five-domain benchmark must derive and report concrete recommendations from
its measured counters, not from this qualitative guide.

## Target integration and remaining acceptance

`fpga/anvil_q2_fp2.qsf` selects the exact Arria 10 device and top.
`fpga/anvil_q2_fp2_sources.tcl` includes all new RTL and the immutable
parent, with the parent package first. `fpga/anvil_q2_fp2.sdc` supplies the
10 ns clock without false-path or multicycle exceptions. See
`fpga/README.md` for portable compilation, bridge responsibilities and reset
sequencing. These files are a core integration, not a newly invented DDR
PHY or PCIe endpoint.

Independent functional/numerical, mutation, synthesis, benchmark and delivery
checks remain mandatory, followed by native timing and board gates.
No clock constraint, static elaboration result, requested performance target
or named instance establishes those results. The present
`design/GENERATIONAL_HANDOFF.md` reports N/A physical results, not a measured
parent baseline. Comparable source-bound parent target evidence remains a
prerequisite for parent-relative throughput/ALM claims, not permission to
fabricate one.

## Claim-to-evidence guide

Independent behavior/numerics receipts establish observed correctness only for
their actual coverage. Defect receipts establish successfully compiled exercised
mutant detection. Benchmark receipts establish fixture-specific cycles and
accepted external traffic, not official-checkpoint quality. Yosys receipts
establish logical structure/proxies. Only native comparable Quartus receipts
establish target timing, ALMs, DSPs, registers and RAM; only native board
receipts establish physical deterministic execution. The parent handoff's N/A
results must not be replaced with invented numbers. The shared runtime produces the
independently reviewed product PDF after engineering acceptance.
