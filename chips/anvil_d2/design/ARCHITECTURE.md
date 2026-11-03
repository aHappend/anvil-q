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
| `rtl/anvil_d2_bank_scheduler.sv` | Per-bank reserved tagged slots, independent client responses, registered issue and flush/drain |
| `rtl/anvil_d2_fp8_mla_moe.sv` | Connected group quantization/packed memory writes and cache/expert prefetch/dequantized read service |
| `rtl/anvil_d2_mtp_projection.sv` | On-chip previous-hidden/embedding RMS normalization and independently weighted H by 2H input projection |
| `rtl/anvil_d2_mtp_verdict.sv` | Longest-prefix correction, terminal truncation and registered held block publication |

These components do not yet constitute `anvil_d2_top`,
or `anvil_d2_mtp_engine`. The FP8 group service is implemented, but its
connection to native MLA/MoE consumers is not. Required integration,
four causal target lanes, head transformers, shared committed-prefix
broadcast, speculative cache ownership/materialization and a completed
Quartus source manifest remain design work. Do not infer implemented
generation from configuration registers or the publication leaf alone.
No functional, synthesis, timing, hardware or speedup result is claimed.

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

The numerical leaves are now connected within the FP8 group service and
the parent arithmetic is connected within the MTP input projection.
Neither path is yet integrated with a complete native target/MTP decoder.
The system-level arrows remain integration obligations. Preserve literal
top instances `mtp` and `fp8` on integration.

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
The FP8 group service now attaches this leaf after dequantization and
stores its result alongside FP32/BF16. The decoder adapter must consume
that Q16.16 result; service-local conversion alone is not inference.

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

The group service packs indices 0..3 into byte lanes 0..3 and zero-pads
only the final external word. A logical row of 129 elements requires
commands 128 and 1 with separately addressed scales. The still-required
decoder adapter derives those commands from actual tensor shapes.
Row/layer/expert/projection identity is held in the service, not stored
implicitly in this numerical leaf.

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

The input projection tensor map is implemented: kind 12, layer
NUM_LAYERS+head, projections 0/1/2 for concatenation/hidden gain/embedding
gain. The native head transformer map must still be finalized without
aliasing those tensors, shared token tensors, cache or scratch. Exactly
four target lanes need separate query/softmax/context state, immutable
committed-prefix broadcasts and explicit per-layer causal K/V barriers.
Use bounded RAM scratch, not full-model register arrays. A serial
parent-top wrapper cannot satisfy this design.

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

## Tagged transport

The D2 scheduler is a new implementation, not a recovered parent
dependency. Each bank owns QUEUE_DEPTH request/response slots. A slot
passes FREE -> QUEUED -> ISSUED -> RETURNED -> FREE; QUEUED also has
a separately registered held-issue selector. One outstanding request
per internal client avoids imposing tags or reordering on parent leaf
interfaces. Distinct clients may queue/issue concurrently, and external
responses are matched against all issued tags of their bank.

Both client arbitration and queued-slot issue use explicit round-robin
wraps, including singleton and non-power-of-two depths. All payloads and
tags remain in reserved slots while stalled. An external response enters
a registered RETURNED slot before a client can consume it. A same-edge
request/response is matched to the just-accepted held request explicitly,
not routed combinationally to the client.

Flush annuls queued and returned slots, keeps issued ownership and
consumes their responses without publication. Tag sequences persist
across flush, preventing a delayed prior-epoch response from aliasing a
new request. Tags are unique across banks and never wrap. Reset starts
a new tag namespace, requiring the external memory reset boundary to
discard prior-reset responses. Unknown/duplicate tags fault normal
operation without writing any live slot. A fault stops new arbitration
but does not retract an already held request before acceptance or flush.
During drain unknown responses are discarded.

Request slots are small register ownership records, not model storage.
Large numerical vectors remain in synchronous RAMs. Registered issue
breaks the arbitration-to-public-request path. Physical 100 MHz timing
is still unmeasured.

## FP8 service ownership and external transactions

`anvil_d2_fp8_mla_moe` accepts one bounded group command. Its two resident
records separately retain latent-cache and routed-expert identities:
epoch/layer/row/base-column/count. A full record becomes valid only
after every fetched payload byte/scale has successfully passed exact
dequantization and Q16.16 conversion. A miss invalidates the selected
record first; epoch change or cancellation invalidates both.

Read-prefetch executes the same fetch/decode path without emitting an
element stream. A subsequent matching command reads the resident
numerical RAM. There is no stale-scale-only hit: numerical payload and
its complete scale-derived owner are published together. The RAM holds
256 x 80 bits, comprising FP32, BF16 and Q16.16 for two groups. A separate
32 x 32-bit staging RAM holds packed external words.

Cache writes connect the quantizer to the real memory client. All valid
source elements are captured; actual quantized bytes are packed and
written as kind 13, followed by the FP32 scale as kind 14. Both preserve
the logical layer/row and cache projection 3. Write completion waits
for every acknowledgement, including the scale. The cache resident
record remains invalid, so a later read cannot silently bypass
quantization by consuming the original signed32 input.

Expert commands select projection 5 and accept arbitrary legal binary32
scales. Matrix/bias/routed/shared classification and actual group lengths
must come from the future native adapter; the service cannot infer them
from an arbitrary row number. Raw parent per-element requests are not
yet adapted into these commands. On any failure both records invalidate,
arithmetic flushes, a failed completion publishes once, and FAULTED
requires explicit flush/reset.

Service queue handshakes are not physical external transfers. Top-level
byte counters must count scheduler external bank handshakes separately
by cache/expert, payload/scale, read/write and unchanged RoPE tensors.
No bandwidth measurement or savings result is claimed from group sizes.

## MTP input projection and verdict leaves

`anvil_d2_mtp_projection` captures the previous hidden vector on-chip,
normalizes it with head-specific gains, independently normalizes the
shared embedding of the prior token, concatenates hidden then embedding,
and executes an independently weighted H by 2H projection. It reuses
unchanged parent RMSNorm/tensor/registered arithmetic primitives,
including epsilon, reciprocal/square-root semantics, wide accumulation
and final Q16.16 rounding. Shared embedding remains kind 0; all input
head weights use kind 12 with independently addressed head layers.

Three synchronous RAMs hold H previous-hidden, 2H normalized and H
projected words. Parent leaf memory requests for those intermediates
are served locally with registered responses, including write
acknowledgements. Only embedding and gain/projection weight reads reach
the external client. The projected hidden stream is an input to a
still-required native transformer head, not a predicted token.

`anvil_d2_mtp_verdict` captures internally computed anchor/draft/target
results, selects only the longest matching draft prefix and its first
correction, then truncates for capacity, remaining visible limit and
first EOS. The registered VERDICT state precedes held PUBLISH.
Accepted-retire events require a real stream handshake and exclude
the anchor/correction or terminally discarded drafts. Publication
completion is deliberately separate from public command completion:
the latter still needs target materialization and acknowledged writes.
This leaf alone does not establish native MTP computation or generation.
