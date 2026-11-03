# Anvil-D2 implementation architecture

## Current inventory and ownership

This is an incremental design, not an accepted integrated product.
The unchanged parent directory is input provenance, not a passing baseline.

| Source | Implementation responsibility / current scope |
|---|---|
| `rtl/anvil_d2_fp8_dequant.sv` | Four-stage elastic exact E4M3FN x binary32 to binary32/BF16 |
| `rtl/anvil_d2_bf16_to_q16.sv` | Registered BF16-to-signed-Q16.16 consumer boundary |
| `rtl/anvil_d2_fp8_group_quantizer.sv` | Bounded RAM-backed capture, actual-group maximum, scale selection and byte replay |
| `rtl/anvil_d2_parameters.sv` | Native legality and wide address-product predicate/diagnostic |
| `rtl/anvil_d2_csr.sv` | Parent CSR forwarding plus D2 configuration and snapshot counters |

These components do not yet constitute `anvil_d2_top`,
`anvil_d2_mtp_engine` or `anvil_d2_fp8_mla_moe`. Required integration,
four causal target lanes, MTP weights/transformers, tagged bank ownership,
packed external cache/expert traffic and a completed Quartus source
manifest are remaining design work. Do not infer implemented generation
from the configuration registers alone. No functional, synthesis, timing,
hardware or speedup result is claimed here.

## Frozen boundaries

`SPEC.md` locks the public-edge, parameter, arithmetic, command and
completion contract before RTL. Native memory clients retain the
parent's kind/layer/proj/row/col identity. A downstream D2 service must
translate actual latent/expert accesses into kind-13 packed words and
kind-14 scales and feed dequantized BF16/Q16.16 into the real arithmetic.
It must not operate as a disconnected sidecar.

The intended connected path is:

```
public command / D2 CSR policy
  -> seed target materialization and shared output argmax
  -> sequential native MTP heads
  -> four target-query lanes, per-layer causal barriers
  -> registered verdict -> registered publish
  -> pending final target materialization -> COMPLETE

target/MTP MLA and MoE consumers
  -> FP8 cache/expert ownership service
  -> tagged bounded bank scheduler -> external memory
  <- packed word + scale -> dequant -> BF16/Q16.16 -> consumer MAC

actual target latent write group
  -> group quantizer -> packed payload + FP32 scale -> acknowledged memory
```

Only the numerical leaves and CSR foundation listed above are implemented
in this increment. The connected arrows remain integration obligations.
Preserve literal top instances `mtp` and `fp8` on integration.

## FP8 dequant datapath

Represent each FP8 magnitude as a four-bit integer times an exact power
of two. For exponent zero use fraction and exponent -9; otherwise use
8+fraction and exponent `raw_exponent-10`. A binary32 scale is a 24-bit
integer times `2^(raw_exponent-150)`, or a 23-bit subnormal integer times
`2^-149`. Their exact product needs 28 bits and a signed 11-bit exponent.

| Register | Contents | Work before register |
|---|---|---|
| 0 | Sign, two integer significands, exponent, classification error | Unpack both formats and validate scale/payload |
| 1 | Exact 28-bit magnitude product, exponent, sign/error | 24 by 4-bit product |
| 2 | Rounded binary32 and error | Leading-bit normalization and nearest-even, including gradual underflow |
| 3 | Binary32, rounded BF16, error | Nearest-even BF16 and nonfinite overflow check |

Ready propagates backward as `!valid || successor_ready`. Registers can
accept replacements on retirement edges, but no item bypasses a stage.
After an unstalled input E0 the first visible output follows E3 and the
earliest output handshake is E4. Reset/flush overrides every stage.
An arming register forbids a transfer on the first reset-release edge.
Invalid transactions retain ordering and publish one explicit error with
zero data. Signed underflow zero is retained on successful transactions.

Normalization uses a fixed-depth leading-bit tree and bounded shifts,
not a divider, real arithmetic or lookup of precomputed expected answers.
Helpers are evaluated in combinational wires before sequential capture;
function temporaries are not clocked state. Physical timing remains an
independent Quartus obligation.

## Consumer boundary

`anvil_d2_bf16_to_q16` accepts one BF16 value through a single registered
elastic stage. Widening BF16 to binary32 adds sixteen zero fraction bits,
so directly converting its exact integer-significand representation is
equivalent to that widening followed by conversion. Round a discarded
half bit away from zero; saturate the signed magnitude to 0x7fffffff or
0x80000000. Nonfinite BF16 is an explicit output error, not saturation.
This leaf is not yet attached to inference and does not establish
downstream FP8 consumption by itself.

## Group quantizer

Interface:

| Signal | Meaning |
|---|---|
| `cmd_valid/cmd_ready`, `cmd_count[8:0]` | Start one group of 1..128 Q16.16 values |
| `in_valid/in_ready`, signed `in_q16[31:0]` | Exactly cmd_count accepted source elements |
| `out_valid/out_ready`, `out_fp8[7:0]` | Quantized element stream |
| `out_index[6:0]`, `out_last` | Stable logical position and group end |
| `out_scale[31:0]` | Selected binary32 power-of-two scale, repeated with every byte |
| `done/error` | Separate one-cycle command completion, after final retirement |

Invalid cmd_count produces failed completion and no source/output
handshake. Flush annuls the current group, including unpublished bytes.
No implicit zero extension changes the actual group length.

State sequence is IDLE -> FILL -> SCALE -> READ -> ENCODE -> PUBLISH,
then repeat READ/ENCODE/PUBLISH or enter COMPLETE after the final output
handshake. Dedicated clock-only RAM has 128 signed-32 entries, 512 bytes,
one synchronous read port and one synchronous capture write port. Ownership
is valid only for the current captured count; reset need not clear RAM.
Fill and replay do not overlap, so there is no read-during-write ambiguity.

Track the unsigned magnitude maximum, including 0x80000000 for the most
negative signed input. For maximum with leading bit L, try exponent L-24;
compare against `448*2^(L-8)` exactly and increment the exponent if
necessary. This gives the smallest safe power of two; the all-zero case
selects exponent zero. Nonzero Q16.16 groups need only exponents -24..7,
well within binary32 normal range.

Replay rounds the exact integer/power-of-two ratio to E4M3FN. Subnormal
steps are 2^-9; normal significands have four significant bits. Both use
nearest-even rounding, propagate the significand carry, and saturate the
finite endpoint to 448. No NaN code is generated.

The consumer of this stream must pack indices 0..3 into byte lanes 0..3
and zero-pad only the final external word. A logical row of 129 elements
requires commands 128 and 1 with separately addressed scales. Row/layer/
expert/projection identity is the service owner's responsibility, not
stored implicitly in this numerical leaf.

## CSR composition

The D2 CSR frontend routes inherited addresses to the unchanged
`anvil_d1_csr_perf`, retaining its response, identification and marker/
domain behavior. D2 addresses have their own held registered response;
the frontend admits only one response owner at a time. Configuration
busy includes a public command accepted on the same edge plus integrated
work/drain/publication occupancy, supplied by the future top.

D2 counters consume explicit event increments from integrated clients.
They do not estimate traffic from dimensions. The parent clear/snapshot
command also controls D2 live/saved counters. Saved values are pre-edge
live values; clear has priority over snapshot and increments. The new
registers do not depend on parent snapshots or future product reports.

## Remaining integration decisions and evidence

The native decoder tensor map must be extended to independently weighted
MTP heads without aliasing shared token tensors, projection/gain tensors,
cache or scratch. Exactly four target lanes need separate query/softmax/
context state, immutable committed-prefix broadcasts and explicit
per-layer causal K/V barriers. Use bounded RAM scratch, not full-model
register arrays. A serial parent-top wrapper cannot satisfy this design.

Speculative cache ownership must separate unpublished lane data from the
committed frontier. Verdict precedes publish; output handshakes advance
only the visible frontier. Pending correction/all-accepted tail
materialization advances the target frontier before another block or
COMPLETE. Cancellation invalidates both and drains accepted tagged
transactions; no caller replay is allowed.

The original parent scheduler/top dependencies and historical handoff
are absent. A newly implemented D2 scheduler is not their recovered
original and must not be described as a parent compatibility result.

No preparation experiment is an acceptance result. Designer may perform
only a fast syntax/elaboration check and then hand completed design to
Verifier. The seven independent L1 suites, actual DDR/PCIe observations,
post-fit timing/PPA and later PDF remain with their declared owners.
