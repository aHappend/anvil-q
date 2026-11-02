# Anvil-Q1-FP2 architecture

## Current implementation boundary

The design is not ready for independent verification of the full product.
Implemented leaves are:

| Source | Responsibility |
|---|---|
| `rtl/anvil_q1_fp2_00_pkg.sv` | Exact BF16 product records, E4M3FN/scale conversion, leading-bit and associative metadata helpers |
| `rtl/anvil_q1_fp2_bfp_tensor_array.sv` | Elastic 64-lane exact signed 544-bit reduction and one FP32 rounding |
| `rtl/anvil_q1_fp2_fast_rsqrt.sv` | Two-stage normalized magic-seed/single-Newton ROM pipeline |
| `rtl/anvil_q1_fp2_fp32_binary.sv` | Elastic nine-stage exact-RNE FP32 add/multiply primitive |
| `rtl/anvil_q1_fp2_exp.sv` | Eight-stage fixed-point range reduction and degree-six exp polynomial |
| `rtl/anvil_q1_fp2_reciprocal.sv` | Six-stage normalized reciprocal ROM interpolation and FP32 rescaling |
| `rtl/anvil_q1_fp2_mx_quantize.sv` | Nine-stage two-Group-32 scale selection and E4M3FN RNE quantization |
| `rtl/anvil_q1_fp2_epilogue_fusion.sv` | Buffered RMSNorm/RoPE/SwiGLU/residual commands using internal vector RAM and named fast-rsqrt |
| `rtl/anvil_q1_fp2_flash_attn.sv` | Single-query chronological online attention with bounded K/V tile RAM and one final normalization |
| `rtl/anvil_q1_fp2_ddr_pingpong.sv` | Two descriptor/response buffers with ID ownership and ordered retirement |
| `rtl/anvil_q1_fp2_telemetry_csr.sv` | Independent saturating live/snapshot counters and delayed CSR response |
| `fpga/anvil_q1_fp2.sdc` | Single 10.000 ns clk constraint, no timing exceptions |

Shared GQA traversal, the decoder controller and top-level are outstanding.
The named top instances required at integration are `tensor_array`,
`epilogue_fusion`, `flash_attn` and `telemetry_csr`; the epilogue must instantiate
`anvil_q1_fp2_fast_rsqrt`. A module-name shell is not an implemented decoder.

## Tensor dataflow and exactness

The tensor accepts 64 BF16 pairs or two Group-32 MX groups in one advance.
MX conversion precedes the exact BF16 arithmetic and contributes its own
observable status. Masking applies to both conversion and arithmetic effects.
Each product is an eight-by-eight integer multiply plus a signed binary exponent.
Two registered maximum levels select E_max including acc_in.

An absolute fixed grid is used instead of the parent's per-term 64-bit
right-shift-and-sticky approximation. Each product is placed once through
coarse/fine pipeline stages into a 544-bit exact signed domain. A 64-bit
E_max-relative reporting window distinguishes main-window versus exact-tail
alignment events; the tail is retained mathematically, not discarded.
Six registered balanced tree levels reduce all lanes; a first-node
carry-save merge includes the FP32 accumulator without a seventh tree level.
Separate magnitude, leading-bit, rounding-preparation and final-packing
registers establish the frozen k..k+15 schedule.

This choice prioritizes exact cancellation over unsubstantiated ALM claims.
The broad grid and normalization remain physical PPA/timing risks; authoritative
post-fit results must include them. If this implementation misses the >45%
ALM-per-lane reduction, it requires design repair, not exclusion of the tail
or a narrower success claim.

A global elastic clock-enable freezes all data and metadata when the final
valid stage is blocked. With no stall, II=1 and result latency follows the exact
edge table in SPEC.md. Throughput is 64 products per advancing input cycle,
not a claim of 64 delivered MACs per wall-clock cycle under DDR/consumer stalls.

## Storage ownership and overlap

The ping-pong ring has exactly two physical 512-bit response buffers. Each slot
transitions FREE -> QUEUED -> INFLIGHT -> RETURNED -> FREE. Read/write descriptor
payloads and controller tags are stored with their slot. Ring head is retirement
order; ring tail is descriptor allocation order; DDR request ID is slot index.

Both slots may be INFLIGHT simultaneously. An out-of-order response changes
only its matching slot. A later RETURNED slot cannot bypass an older pending
head. Descriptor fields stay stable under request backpressure, and completion
fields stay stable under consumer backpressure. Consumer retirement, not merely
response arrival, releases the slot; this avoids overwriting returned-but-unused
data. At full occupancy, retirement and refill share the freed slot on one edge,
with new descriptor ownership winning over release.

The future controller must schedule ahead sufficiently to overlap one buffer's
transfer with consumption of the other. The leaf's concurrency alone does not
prove end-to-end overlap or bandwidth improvement.

## Dependency and lifetime table

| State/resource | Producer | Consumer | Lifetime / guarantee |
|---|---|---|---|
| Tensor decoded group | Input handshake | Product stage | Frozen with global pipeline enable |
| Tensor exact tail | Alignment stages | Exact tree / final RNE | Never replaced by sticky-only cancellation information |
| DDR descriptor | Controller command transfer | DDR request transfer | Full payload held until request acceptance |
| DDR response slot | Matching DDR response transfer | Ordered controller retirement | Cannot be reused while returned but unconsumed |
| ULP sample | Actual FP32->BF16 conversion | Telemetry event input | One event per real conversion; nonfinite sentinel explicit |
| Live counters | Qualified datapath events | Snapshot command | Saturating, independent of CSR response stalls |
| Snapshot counters | Atomic control write | CSR reads | Stable until next snapshot or clear |
| Epilogue input/auxiliary/residual RAM | Accepted command stream | FP32 arithmetic sequencer | All command operands stored before computation; no external fused scratchpad round-trip |
| Epilogue result RAM | Arithmetic sequencer | Output stream | Complete result vector retained until transferred; stalled final output preserves command ownership |
| Attention query RAM | One accepted query vector | All tokens in that command | Loaded once before tile intake |
| Attention K/V tile RAM | Single chronological KV stream | Current tile computation | Reused only after every token of the tile updates running state |
| Attention output RAM | Online alpha/p updates | Next token or final normalization | First token supplies explicit zero instead of reading stale state |
| Future grouped queries | Q projection / RoPE | All GQA query heads | Must permit one chronological shared KV traversal |
| Future KV history | Current K/V projection | Causal attention | External, sequence-owned, invalidated on reset/new-sequence |

## Nonlinear pipeline strategy

Fast-rsqrt normalizes into [1,4), combining exponent parity with ten mantissa
bits to address a 2048-word ROM. The ROM is generated deterministically by an
integer constant function performing the required magic-seed Newton update at
each interval midpoint. Its read and rescale registers are the only two
architectural stages; there is no hidden iterative engine.

The fused epilogue now sequences exact FP32 add/multiply pipelines with bounded
internal input/auxiliary/residual/result RAM. RMSNorm performs a component-order
square/sum reduction, mean/epsilon and fast-rsqrt, then x/factor/gamma products.
RoPE performs split-half pairs; its in_aux stream carries cosine in the first
half and sine in the second. The decoder must obtain those deterministic FP32
coefficients from kind 11 for the command position. SwiGLU uses exp(-abs(gate))
and a normalized reciprocal to avoid unstable positive exp or iterative divide.
Residuals use the same exact-RNE add pipeline. Result buffering permits original
vector order and stable downstream backpressure without an external round-trip.

Exp uses signed Q24/base-2 reduction and registered Q30 Horner arithmetic.
Reciprocal normalizes the entire positive finite FP32 domain and interpolates
two adjacent Q1.31 ROM endpoints. Both ROM data and polynomial provenance live
in synthesizable sources; no generated runtime-state files or tool install is
needed. These approximations' numerical bounds and timing remain unverified.

The attention leaf loads one BF16 query, then accepts each K/V pair once into a
bounded TILE_TOKENS*HEAD_DIM tile. It computes chronological FP32 dot scores,
parallel running-max exp rescaling, sum/output updates and one final reciprocal
normalization. A tile can be partial, and TILE_TOKENS=1 or 3 uses real storage
boundaries rather than power-of-two pointer masks. It never stores all scores
or all KV history. See SPEC.md for exact command, framing and completion edges.

The Group-32 MX quantizer selects each scale through five registered maximum
levels, then performs per-lane ties-to-even encoding. Masks suppress metadata,
status and code effects; scales and saturation counts remain public outputs.
It is a precursor for activation/KV packing, not yet an integrated transport.
FP32-to-BF16 conversion and integer-to-FP32 helpers have also been added to the
owned package. Independent verification must not reuse these as its oracle.

These are substantive leaves, but they are not yet an accelerator. The decoder
must still join the required named hierarchy, share one KV traversal across
each GQA query group, compose projection/epilogue dependencies, and connect
real conversion/transport/starvation events to telemetry. No simulation or
synthesis has been performed by Designer.

## Integration and performance accounting still required

The compatibility branch must preserve the immutable parent's complete scalar
ABI and mode behavior, while optimized modes must use DDR for floating weights
and KV. Preserve logical projection orientation: parent native projection
weights are indexed by input row and output column; embedding/output-head
weights use vocabulary row and hidden column.

The optimized branch must hold residuals and intermediate vectors internally,
integrate the actual decoder dependency graph, and coordinate fatal status
with logit buffering so a failed token cannot appear partially successful.
No top-level shortcut or parent scalar fallback may be called optimized BF16/MX.

Matched benchmarks must account for the scalar-to-physical-beat adapter on
both sides consistently. Report cold scale/table loading, warm runs, actual
64-byte transactions, padded tails, scale reads and GQA reuse. A full MX group
has 32 bytes of data versus 64 BF16 bytes, plus one scale byte before beat
padding; this arithmetic is not itself a measured 50% total traffic reduction.
Yosys cells are not Arria 10 ALMs; post-fit ALM and DSP efficiency claims require
native matched Quartus measurements.

No experiment or acceptance result is recorded in this document. The missing
generational handoff remains an evidence gap described in SPEC.md.
