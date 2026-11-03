# Native floating-point implementation

## Implementation status

The connected native implementation has public entry `anvil_q4_fp_top`.
It contains descriptor, speculative control, decoder, final normalization,
embedding/LM-head and seventeen-client bank scheduling. The decoder connects
the native GEMV, RoPE, attention, paged cache, MLP and elementwise stages.
The numerical foundation from the first increment is retained.
The isolated `anvil_q4_parent_*` and `anvil_q3_parent_*` namespace contains the
compatibility dependency closure; no parent reference source is modified.
Implementation is not engineering acceptance.
Independent functional/synthesis/timing/hardware results are not claimed.
No trained-checkpoint execution is claimed.

The complete admitted contract is in `SPEC.md`, with native signatures
frozen in `NATIVE_INTERFACES.md` before RTL implementation.
No authentic parent generational handoff or linked source index was available.
The supplied parent sources remain provenance, not a native numerical oracle.

## Compute and ownership

The native array keeps FP32 accumulators output-stationary across ascending K.
One real FP32 leaf per active row alternates separately rounded multiplication
and addition. BF16/FP16 widening uses two explicit registers before common
multiplier issue; no dequantizer or integer activation path is present.
The activation tile has synchronous registered reads and no asynchronous
reset writes, preserving memory inference.

GEMV narrows each FP32 scratch activation at the explicit native boundary.
Sixteen logical weight channels remain independent even for smaller BANKS.
Each lane separately records request acceptance, response retirement and a
returned value. It cannot issue another K until the current vector enters
the tensor array. Unused rows never issue traffic. Auxiliary channel 16
loads activations, reads bias and writes scratch.

The array arithmetic pipeline uses the precise edges in SPEC, not a
single-cycle behavioral expression. The compute-only full-vector interval
is 23 clocks per K; this is an analytical schedule, not measured throughput.
At 100MHz the full 16-row schedule has a theoretical upper bound of
16/23 MAC per clock (one multiplication plus one addition per MAC),
before activation loading, memory stalls, tile overhead, bias and output.
No claim of achieved clock or end-to-end speedup follows from that bound.

The scalar stages retain FP32 intermediates. SiLU deliberately follows
`x / round(1 + exp(-x))` for both signs; the parent's negative-input stable
algebra changes the rounding order and is not the native contract.
Descriptor validation uses separately registered full-width dimension/page
products, rejects native quantization and reserved fields, and retains the
parent version-1 validation rules. Successful public descriptor commits
invalidate native sequence/prediction and advance the image generation;
failed commits preserve the active sequence.

For a full R-row by K-element native tile, weight traffic is R*K logical
reads and activation traffic is K scratch reads. The external payload is
32 bits per read although each native weight uses only its low 16 bits.
Results remain FP32. Smaller TILE_ROWS lowers spatial resources/utilization;
smaller TILE_K increases command/load overhead without changing rounding
or the 17-channel interface. Smaller BANKS introduces scheduler contention.

## Routing, draining and sequence state

`anvil_q4_fp_mem_arbiter` registers a selected owner before accepting its
request, then captures the complete tuple into a request register. It holds
that owner through the acknowledged response. Round-robin advances only on
response retirement. `anvil_q4_fp_channel_mux` instantiates one arbiter per
logical channel; lane n never becomes another lane or the auxiliary channel.
Decoder auxiliary arbitration gives attention and cache distinct owner
indices. The MLP and decoder use explicit completion fences. The top also
waits for all channel routers and scheduler records to empty before starting
another stage. This adds routing clocks without changing arithmetic offsets.

The scheduler has per-bank fair arbitration, bounded transaction slots,
registered held requests and independent per-client response buffers.
A full-tag comparison matches replies against sent slots, including an
external acceptance/reply on the same edge. Responses from different banks
can be captured together even when another client holds its buffered result.
Flush discards unpresented queues, never an externally held request. Held
requests may still accept during cancellation and are added to the drain.
Local arithmetic is flushed while the scheduler retains these external
ownership records until every reply is consumed.

Native tags use the high half of the 64-bit namespace. Per-bank serial
numbers are not reset on cancellation. Exhausting the serial field waits
for bank quiescence before incrementing its shared tag epoch; exhausting
the epoch faults/drains the current command and enters a terminal no-accept
state until reset, rather than reusing identities.
Compatibility uses the low namespace; its wrapper refuses a tag with bit63
set before it is externally presented. The rejected internal request receives
a registered local error acknowledgement, not an external transfer. A one-shot
abort then drains other already-presented compatibility requests and reports
the failed command; future compatibility commands require reset. This error
path cannot leave a forbidden held tag waiting for external acceptance.
Reset must also reset the responder or exclude all old replies, as required
by SPEC.

Normal and speculative work use separate committed and working position/
epoch registers. A well-formed normal new-sequence command and every accepted
new-sequence draft consume a fresh nonwrapping epoch before target execution,
even if target execution later fails. Malformed normal commands do not
allocate an epoch. Old sequence metadata remains intact until normal success
or speculative result retirement. Tentative continuation rows are beyond
the committed token count; rejected rows are inaccessible and a later normal
token overwrites its complete K/V row. New-sequence writes additionally
scan the protected old epoch's page mappings to reject physical aliases.
No speculative logits reach the public logit stream.

Once a speculative result is published, a late memory fault cannot change
its held payload. It prevents tentative commit and produces an error
completion after draining; result retirement is remembered even if it
occurs while the fault is being drained. Cancellation instead explicitly
invalidates the held result and takes priority over retirement.

The cache streams ascending FP32 K and V scratch elements through the
explicit BF16/FP16/FP8 narrowing boundary, assembling complete packed words
before acknowledged writes. It packs across head boundaries, zeros the
last partial word and never emits integer scales or escape payloads.
FP8 conversion rounds directly from FP32, not through an FP16 intermediate.
Attention's explicit ratio-position counter implements all ratios 1..8
without division; its score storage uses synchronous RAM read/write ports.
Attention scaling uses a 128-entry constant lookup for every legal even
head dimension 2..256. Each entry is single-rounded RNE FP32(1/sqrt(d)),
not a reciprocal of a rounded FP32 root or a square root of a rounded
reciprocal. The accepted command registers d at E0; SCALE_LOAD registers
the lookup result at E1 before cache work can transfer at E2. Reset clears
the scale register, and flush takes priority over loading or using it.
No arithmetic-leaf latency, memory interface or score accumulation order
changes; only the former scale-preparation conversion/sqrt/divide sequence
is replaced.

The literals were derived using integer midpoint comparisons. For the
normalized result exponent e, let N=2^(46-2e) and m=floor(sqrt(N/d)).
Compare 4*N with d*(2*m+1)^2 to round m to nearest, retaining even m on
equality, then pack the FP32 exponent and significand. This avoids
host floating-point and intermediate rounding. Independent Verifier must
check all entries and rerun the unchanged attention comparisons.
The repair addresses the retained component-0 mismatch (expected bf7105bb,
observed bf7105ba) in
`evidence/preparation/attention-scale-20261103T022450000101Z/verilator-attention/receipt.json`
and
`evidence/preparation/attention-scale-20261103T022545973100Z/verilator-attention/receipt.json`.
Those failed receipts remain unchanged; this explanation is not a passing
functional result.

Page validation also compares earlier live mappings against each scanned
candidate, so duplicate aliases not involving the requested page are rejected.
This intentionally bounded sequential scan uses no huge reset-time table:
it can take quadratic page-table traffic in the number of live pages, plus
protected-page scans for a replacing sequence. That is an architectural
bottleneck to measure, not a claim of scalable constant-time translation.

## Compatibility integration

The compatibility clone preserves the parent's arithmetic, projections,
legacy cache formats and control pipeline, with row geometry capped at eight
internally. The native top remains 16-row by default. Configuration writes
accepted by the public descriptor are mirrored to the isolated descriptor.
Both shadows reset to the native image, so sparse writes cannot create
different legacy descriptors. The hidden compatibility active image remains
the valid parent mode-4 reset image until a legacy commit succeeds. Native
commits may be rejected by that hidden descriptor; only the public descriptor
reports configuration status. All commands are blocked during configuration.

Besides namespace changes, two compatibility files have integration edits:
the descriptor shadow/reset treatment just described, and the bank scheduler's
held-request draining. Read-only inspection of the supplied scheduler showed
that cancellation withdrew a held external valid. The isolated copy retains
that request through acceptance/drain to meet the public cancellation
contract. This is a known source-level parent difference, not a measured
parent failure or a passing differential result. The independent compatibility
suite must retain and classify any observed difference; its acceptance
requirements are not waived.

Host images use the tuples and external layout in `NATIVE_IMAGE.md`.
The independent Verifier owns deterministic fixture/export helpers and
source-bound manifest checks; their existence or results are not assumed.

## Reproduction and evidence boundaries

Run the independent portable suites from the delivered root using the six
commands in SPEC once Verifier has authored `tests/verify.py`. They are not
currently present and are not represented as passing. Designer does not
author numerical references, simulation harnesses or synthesis checks.
The shared runtime supplies authoritative timing/fit and physical-board
evidence. The final product PDF is downstream of engineering acceptance,
not an input to design verification.

The first static-only Icarus elaboration failed because the original package
filename sorted after `anvil_q4_fp32.sv` in `rtl/*.sv`.
The receipt is
`evidence/preparation/native-foundation-static-20261103T020343131336Z/receipt.json`.
Renaming the package file to `rtl/anvil_q4_00_fp_pkg.sv` places it before
importing modules without changing package contents. This is a compilation
ordering repair, not numerical verification. No simulation or synthesis
harness was authored or executed.
