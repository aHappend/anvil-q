# Anvil-Q1-HT implementation architecture

## Delivery status

The design-owned RTL is connected for independent verification. This is not
engineering acceptance: numerical parity, throughput, synthesis, device fit,
timing and board execution remain unestablished. The source responsibilities are:

| Source | Responsibility |
| --- | --- |
| `rtl/anvil_q1_ht_reset_sync.sv` | Two-edge local reset release |
| `rtl/anvil_q1_ht_parameters.sv` | Explicit legal-parameter diagnostic |
| `rtl/anvil_q1_ht_mac_lane.sv` | DSP partial products, exact carry-save dot and final rounding |
| `rtl/anvil_q1_ht_tensor_array.sv` | Fixed 8x8 hierarchy, dot protocol, held results |
| `rtl/anvil_q1_ht_tile_bank.sv` | One inferred dual-clock M20K bank |
| `rtl/anvil_q1_ht_weight_tiles.sv` | Two-bank ownership, synchronous compute reads |
| `rtl/anvil_q1_ht_cdc_mailbox.sv` | Stable-payload request/acknowledge CDC |
| `rtl/anvil_q1_ht_weight_dma.sv` | Burst reads into reserved tiles and response-checked upload writes |
| `rtl/anvil_q1_ht_divide.sv` | Unsigned restoring division with 32-bit sequential carry partitions |
| `rtl/anvil_q1_ht_isqrt.sv` | Unsigned integer square root with sequential 32-bit subtraction partitions |
| `rtl/anvil_q1_ht_00_numeric_pkg.sv` | FP16/BF16 conversion, invalid-value guards, saturation and packed AWQ shift mapping |
| `rtl/anvil_q1_ht_dequant.sv` | Registered AWQ difference-times-scale or BF16 conversion |
| `rtl/anvil_q1_ht_math.sv` | Chunked exact modular arithmetic, signed division/rounding and square-root wrapper |
| `rtl/anvil_q1_ht_nonlinear.sv` | Sequential parent exponential recurrence and SiLU |
| `rtl/anvil_q1_ht_kernel.sv` | Shared-memory RMSNorm, RoPE, residual/SwiGLU and full causal GQA command controller |
| `rtl/anvil_q1_ht_kv_window.sv` | Tagged M20K K/V storage, explicit validity and acknowledged logical eviction/cold-read path |
| `rtl/anvil_q1_ht_descriptors.sv` | Held CSR/lookup responses, atomic descriptor installation and complete-set image validation |
| `rtl/anvil_q1_ht_weight_stream.sv` | Descriptor-bound DMA packet stream with tile-counted fault draining |
| `rtl/anvil_q1_ht_projection.sv` | Actual64-lane panel GEMV, parallel dequantization, exact bias and tied logits |
| `rtl/anvil_q1_ht_decoder.sv` | Token/order control, complete kernel/projection sequence and final-logit completion |
| `rtl/anvil_q1_ht_address.sv` | Checked parent-logical to panel-major DDR address translation |
| `rtl/anvil_q1_ht_logical_memory.sv` | Synchronous M20K scratch and tagged-KV request routing |
| `rtl/anvil_q1_ht_ddr_scalar.sv` | Held-payload CDC and response-checked scalar DDR transactions |
| `rtl/anvil_q1_ht_transaction_mux.sv` | Locked single-outstanding descriptor/scalar transaction arbitration |
| `rtl/anvil_q1_ht_avalon_mux.sv` | Held command selection and complete-burst response ownership |
| `rtl/anvil_q1_ht_image_guard.sv` | Cross-clock exclusive upload grants, release and acknowledged error clear |
| `rtl/anvil_q1_ht_top.sv` | Connected resident-image inference, CSR, DDR, tensor and cache hierarchy |
| `rtl/anvil_q1_ht_compat_projection.sv` | Retimed parent logical-memory AWQ/tied-embedding projection |
| `rtl/anvil_q1_top.sv` | Parent-compatible parameter/port entry, separate from the HT hierarchy |

`design/anvil_q1_ht.qsf` selects the actual Arria10 device and product source
inventory; `design/anvil_q1_ht.sdc` constrains compute, DDR, public I/O and
specific CDC paths. The public top is the EMIF application-side accelerator,
not an invented physical DDR4/PCIe shell. Native implementation gates must
integrate the actual board shell, calibration/reset and pin assignments.
The current sources have not been functionally verified.

## Tensor dataflow

Each accepted vector broadcasts one signed activation to 64 signed 37-bit
weights. All lanes instantiate the same `anvil_q1_ht_mac_lane`, under the
required `g_bank[].g_lane[].u_mac` hierarchy.

| Edge relative to accepted beat E | Lane action |
| --- | --- |
| E | Capture activation, weight and boundary metadata |
| E+1 | Four registered signed 17x19, 17x19, 16x19, 16x19 partial products |
| E+2 | Carry-save reduction; resolve low 35 product bits |
| E+3 | Resolve remaining 34 product bits and register exact 69-bit product |
| E+4 | Sign extend product and update the 128-bit carry-save accumulator |
| Last E+5..E+8 | Resolve successive 32-bit accumulator chunks |
| Last E+9 | Round-by-16, ties away from zero, and saturate to int32 |
| Last E+10 | Publish registered lane result and tensor output valid |

Carry-save accumulation uses two 128-bit state vectors and bitwise
XOR/majority logic; no 128-bit carry propagation occurs per product.
`multstyle="dsp"` is attached to the multiplier result registers. Actual hard
DSP mapping and timing remain subject to Quartus evidence, not attributes alone.

Negative rounding operates on the arithmetic-floor quotient: increment only
when the low 16-bit remainder is strictly greater than 0x8000. At a negative
halfway tie, retaining the floor rounds away from zero. Positive rounding
increments on bit15. Saturation uses upper-bit sign consistency plus a 33-bit
candidate, avoiding a combinational 128-bit magnitude negation/add.

The array does not accept a subsequent dot while finalization or output
retirement is pending. Data/mask/valid hold under sink backpressure. An accepted
malformed boundary or mask change latches a protocol fault and suppresses
publication until reset. The integration must escalate this fault.

The projection bias path sends a final synthetic product `65536 * bias_q16`.
This adds the exact shifted bias in the accumulator without exposing a changed
primitive interface or introducing an intermediate rounding boundary.

## Dual-clock tile ownership

`anvil_q1_ht_weight_tiles` contains two separate
`anvil_q1_ht_tile_bank` instances. At the default depth each holds
256 x 512 bits, or 16384 bytes; total weight buffering is 32768 bytes.
The M20K inference arrays have no reset, initialization, model constants or
cross-clock read-modify-write.

The DDR producer alternates bank0/bank1. A fill descriptor reserves the entire
selected FREE bank, taking it to FILL. It supplies a 1..TILE_BEATS beat count
and a nonzero final byte mask. Accepted data writes sequential addresses; an
explicit final-count comparison, not binary masking, terminates the fill.
The supplied `fill_last` must match that comparison. A malformed fill latches
`fill_error` rather than publishing a partial bank.

After the final write, a per-bank full toggle transfers FULL ownership to the
compute domain. Beat count and tail mask are held unchanged from fill start
until ownership returns; they cross as a bundled stable payload only after the
two-flop toggle synchronizer. The compute side captures this payload before
advertising `tile_valid`. Claiming the tile takes it to COMPUTE.

The compute reader first captures a requested address. Its memory port reads
on the following edge, so an address accepted at R yields data after R+1.
An elastic pending-address stage plus output-valid state retains data through
backpressure. Only the final beat receives the partial byte mask. Out-of-range
accepted addresses are explicit sticky compute faults.

Release is accepted only after both read pipeline stages drain. A synchronized
release toggle returns ownership to FREE in DDR. The producer never reuses a
bank merely because the consumer has started or finished issuing reads.
Alternation preserves fill order even if one side stalls. A DDR fill abort
before publication frees the current bank without advancing the alternation
pointer. The packet-stream consumer drains the completion's exact published-tile count
on a read fault. A tile protocol fault instead cancels the active DMA request,
drains its external burst and retires an error without reusing the failed
bank state; this fault requires global reset.

## DMA and preload protocol

`anvil_q1_ht_weight_dma` accepts a compute-domain aligned byte address and
nonzero byte length using a held-payload mailbox. One compute request may be
outstanding, including an unaccepted completion. The DDR sequencer validates
an extended 34-bit address-plus-length against 8 GiB, computes padded beat
count and a final byte mask, then reserves one entire tile before any read.

Read bursts are the minimum of remaining tile beats, 16 and beats to the next
4 KiB boundary. Burst planning is registered. Address, burst count and read
control remain unchanged until accepted. There is no Avalon data-ready signal.
Responses on the command-acceptance edge and on consecutive DDR edges are
captured directly into the reserved tile. The tile's data-ready guarantee is
part of the dependency contract: after successful reservation it must accept
all responses until the final beat, abort or explicit tile fault.

A non-OKAY read response marks the request failed, suppresses further tile
writes, drains the already issued burst, aborts its reserved tile and returns
an error completion, carrying the count of successfully published tiles. No later
burst is issued for that request. An unavailable
tile data sink is also an explicit error, not a dropped successful beat.
Completions cross back through a separate held-payload mailbox.

Preload writes latch every accepted address/data/byte-enable/last tuple. One
write command and its response complete before the next beat is accepted.
Same-edge command acceptance and write response are supported. Non-OKAY write
responses or unaligned input addresses terminate the upload with error.
`load_done` pulses only on final acknowledged success or upload failure;
`load_error` is sticky until an idle `load_clear`. The top must not commit an
image with this error or before `load_idle`. `load_enable` and `load_clear`
are DDR-domain integration controls, not additional public top ports. The image
guard supplies them only after compute-domain ownership has been granted.

An open multi-beat upload excludes inference. A newly arriving request may
wait in its mailbox but cannot issue until upload termination. The top must
also gates token/CSR/load acceptance to enforce the admitted public exclusion
rules. Unexpected unowned responses latch `protocol_error`; they
are never attributed to a new successful request. Reset must quiesce the
external EMIF response source as required by the work order.

`accepted_read_beats` counts observed response beats, including faulted beats,
in DDR. Its two 32-bit counter halves do not form a single 64-bit ripple
incrementer. It is not safe to sample this multibit bus directly in compute:
the top therefore counts all owned DMA/scalar response beats at the Avalon
boundary and transfers acknowledged snapshots to compute. A CSR low-word read
latches that snapshot's high word for the following high-word read.

## Arithmetic services

The divider accepts unsigned widths 1..129, covering signed-magnitude
rounded-division preprocessing as well as the parent's unsigned RMSNorm
division. It returns quotient and remainder, or an explicit divide-by-zero
error, with output backpressure. Every restoring step subtracts at most
32 operand bits plus a registered borrow. Padded remainder width retains
the extra shifted bit even when WIDTH is a multiple of 32.

The square-root service processes two input bits per digit, using three
sequential 32-bit subtraction chunks per trial. It produces floor(sqrt(x))
for unsigned 128-bit input and holds the 64-bit output until accepted.
These services have no runtime `/` or `%` operator. `anvil_q1_ht_math`
integrates both, with signed-magnitude preparation and sign restoration
partitioned into registered 32-bit chunks. Signed rounded division adds half
the unsigned divisor to the magnitude in 129 bits before unsigned division;
signed truncating division does not. Right-shift rounding uses the arithmetic
floor and discarded-bit tests, not a full-width combinational magnitude
negation. Multiplication visits the triangular set of registered 16x16
partial products contributing to the low 128 bits, then adds each in four
registered carry chunks. This preserves specified modular truncations without
a single-cycle 128-bit multiplier. Independent arithmetic comparisons remain
pending.

## Numerical kernel sequencing

The shared kernel controller uses explicit subroutine states for held memory
requests, arithmetic and nonlinear services. A memory response on the request
acceptance edge is supported. Requests cannot overlap: the return state is
latched with the command and is not advanced until its response.
The seven logical memory fields retain the parent interpretation.
`design/SPEC.md` gives command and activation-slot mappings.

RMSNorm first accumulates exact squares with the parent's 96-bit truncation,
then invokes sequential mean division, epsilon addition, integer square root
and reciprocal division. A second pass converts each FP16 gamma, multiplies
the signed input/gamma product by the reciprocal and performs one final
round-by-48/saturation.

RoPE reads each half-vector pair and its Q2.30 table values before computing
four exact products. The signed65 rotated values are rounded only after
addition/subtraction, then written back. Residual sums saturate once; SwiGLU
first saturates the parent SiLU result and then rounds its product with up.

GQA inserts the complete current K and V vectors, finds each query head's
maximum full-context score, and recomputes scores for the exponential and
weighted-value pass, preserving the parent's component-loop behavior.
Query-head-to-KV-head grouping uses an explicit group counter and KV column
base, not runtime head division. Every context position 0..current is
requested; the memory bridge must route hot/cache and cold/backing accesses.
Scores retain signed96 truncation; score differences use signed97. Weighted
products retain signed65 and sums signed96; denominators retain unsigned64.
The six-term exponential performs each parent's signed64 truncation before
truncation-toward-zero division and each signed64 total update. SiLU retains
the parent's unsigned64 sigmoid, signed65 product and round-by-24 boundary.

This intentionally shared, slow numerical service is not used to claim the
64-lane projection speedup. The parallel projection controller has its own
DMA/scale/activation schedule, described below.

## Panel streaming and decoder orchestration

The projection controller preloads its input activations into synchronous M20K
storage, then visits consecutive output panels of up to64 lanes. The physical
matrix ABI is panel-major, with no inter-panel padding; `design/SPEC.md` gives
exact logical-to-physical formulas, including packed-word/nibble ordering and
the short last panel. The embedding ABI is also panel-major along vocabulary,
so one resident FP16 tensor serves both embedding and tied output projection.
This is a bijective upload-time permutation, not a new numerical format.
Checkpoint acquisition, repacking implementation and bijection checks remain
Verifier-owned and have not run.

AWQ loads one panel of zeros and scales for each input group, then requests
that group's contiguous qweight rows. All64 registered dequantizers operate
in parallel. Each weight-row packet also starts a synchronous activation read.
The row's tensor beat waits for dequantization; later groups continue the same
exact tensor dot. BF16 and tied FP16 use the same64 real compute lanes but
require up to two DDR beats per weight row, unlike AWQ's half beat for a full
panel. Q/K/V bias is a final synthetic product before the tensor's final rounding.
The controller never uses rounded results as reconstructed accumulators.

The stream reader reserves bytes in a192-byte register reservoir, retaining
copied bytes while an owned bank is released and its successor is claimed.
It emits1..128-byte packets, removes an initial unaligned byte prefix and
honors final byte masks. The DMA completion's published-tile count crosses
with the fault status in the same acknowledged mailbox. Fault draining waits
for exactly that many tile releases; no sampling of asynchronous emptiness
or finite guessed settling delay is used as evidence of completion.

The decoder dispatches the complete parent operation order, not a shortened
benchmark path. Kernel and projection memory requests are routed according to
the active child command; ownership is retained through its response and
completion. Final-logit transfer directly causes token completion at that
edge. Stalling that final logit holds the entire token open. Embedding
conversion checks invalid FP16 before writing slot0, and new-sequence commands
invalidate cache metadata without modifying image descriptors or DDR weights.

The scalar address controller implements the same physical panel formulas,
including embedding's transposed panel interpretation, with registered
products before issue. Every request is checked against logical shape,
descriptor length and extended8-GiB address bounds. Scratch requests use a
separate synchronous M20K store; K/V requests route to the top-owned window.
The window's backing interface shares the external scalar address controller
through a locked transaction mux, bypassing the resident lookup so a miss
cannot recurse into itself. The main decoder cannot issue another logical
request while its current KV request awaits a spill response.

The scalar DDR adapter holds a complete request and response across clocks.
The shared Avalon arbiter locks a selected command through waitrequest and
demultiplexes all responses to the same master until its entire burst or write
acknowledgement retires. Same-edge acceptance/response is supported. It never
backpressures read data. The single-outstanding transaction mux similarly
locks descriptor/scalar request ownership, including response stalls.

## KV ownership and logical spill

Two M20K data arrays partition K and V by layer, slot and head/dimension.
Each slot also has a synchronous full-position tag and a bitmap covering all
K/V words. A synchronous constant mapping ROM derives the slot in one edge;
it is initialized by an explicit wrap counter, not a power-of-two mask.
The next edge reads tag, bitmap and selected SRAM word, and the third edge
publishes the checked result: accepted address K, valid hit after K+2.

A complete K/V row advances that layer's history limit. An occupied old slot
is preserved until all 2*KV_WIDTH scalar backing writes acknowledge; failure
does not install the replacement tag or word. Cold reads are checked against
current history before issuing a backing request. Hot reads issue no spill
request. New sequence sequentially invalidates metadata and history while
blocking requests, leaving model DDR and unneeded data bits untouched.
The bitmap prevents partial insertion from falsely validating unwritten data.

Backing requests are held until accepted and their responses are checked,
including coincident acceptance/response. The scalar address controller routes
them to distinct per-layer kinds9/10 descriptors and the shared Avalon master.
This connection is not a claim that cold context has executed correctly.

## Descriptor and configuration ownership

The descriptor store is a synchronous packed M20K table indexed by the
admitted layer/kind/projection identity. A dedicated lookup response register
holds base/length/fault while stalled. CSR stages identity and range fields
without changing an installed descriptor. Install checks dimensions, padded
length, 8-GiB bounds and identity before scanning all other installed regions
for overlap. Only its final write changes the table and invalidates the image.
Zero-length install explicitly removes a legal identity.

Commit walks layer/kind/projection with explicit wrap counters and checks the
entire required set against the current mode. AWQ scale/zero descriptors must
be removed for BF16. Successful installation already establishes nonoverlap
as a table invariant. Commit rejects missing/unexpected entries, wrong sizes,
alignment/range errors, pending loads, load faults or unavailable EMIF.
An ordinary CSR accepted at E publishes its response after E+1; install/commit
retain the outstanding transaction until validation ends. All responses hold.

Configuration validation exposes `configuration_busy` for top-level start
exclusion. A CSR request or held response inhibits token acceptance. Upload
acquisition is acknowledged only while the decoder and configuration engine
are idle and no CSR is active; an observed acquisition request inhibits a
same-edge token. `image_modified` invalidates the image at the grant, before
any DDR write can occur. A returned upload completion carries its error bit in
one mailbox payload; a separate acknowledged control message clears an idle
DDR load error. No multibit DDR status is sampled directly. A newly observed
load fault or compute fault wins over an idle sticky-error clear.

## Dependency and integration map

| Consumer | Required producer guarantee |
| --- | --- |
| MAC lanes | Array passes only accepted, well-formed beats and prohibits overlapping dots |
| DMA | Tile reservation guarantees capacity for every unbackpressurable response |
| Tile consumer | Full toggle means all bank writes and metadata are stable |
| Tile producer | Release toggle means all compute reads have retired |
| Mailbox receiver | Source payload remains frozen until acknowledged ownership return |
| Descriptor/CSR logic | Top excludes token/upload starts during mutations and validation; load status/counters cross safely |
| Decoder | Bias, group transitions, activation slots and numerical kernels preserve parent boundaries |
| Kernel attention | Logical-memory bridge sends all K/V requests to the tagged window and connects spill to DDR |
| Top | Synchronize reset release, status and error handling in both domains; drain failed traffic |
| Board shell | Real initialized EMIF clock/reset and write-response support |

The DDR image guard requests ownership before exposing `load_ready`. Compute
holds that reservation until the acknowledged final write (or failed upload)
returns through the completion mailbox. Merely synchronizing busy levels would
not prevent simultaneous starts. During this reservation CSR mutations fail
atomically and token readiness remains low, including gaps between upload beats.
`load_last` is not ownership return: its write response must first complete.
One additional DDR state prevents a following beat from sneaking through during
the `load_done` pulse. Idle load-error clear also holds the reservation until
the DDR domain acknowledges it.

On a numerical/memory error the projection drains its outstanding scalar request
and active packet stream before reporting failure. The decoder then resets its
compute-only children and the tensor dot through local reset synchronizers;
uploaded DDR bytes and descriptors remain intact. Sequence continuation is
invalidated; after clearing sticky status, a valid new sequence clears the KV
history. A read/write response error is not mistaken for a successful zero.
Unexpected responses or corrupt tile ownership set a synchronized fatal status;
the active command drains issued traffic, emits one error completion and cannot
restart without global reset. No finite guessed settling delay certifies drain.
The DMA abort path cannot withdraw a command held under Avalon waitrequest.

Do not reuse the parent's combinational divide/modulo/sqrt/nonlinear functions
in the HT clocked datapath.

## Compatibility entry and physical constraints

`anvil_q1_top` retains the parent's exact parameter order and public port
types. Its parameter validator retains the broader historical arithmetic/address
bounds rather than imposing HT maxima. It uses the same sequential numerical
kernel with an explicitly selected legacy-parameter branch and a scalar
logical-memory projection. That projection uses the original packed AWQ words,
explicit group counters, the same exact tensor accumulation/rounding and FP16
tied embedding. It does not require the HT panel-major image layout or CSR
configuration. It is not instantiated anywhere in `anvil_q1_ht_top`, nor is
it the throughput baseline: the immutable parent remains that baseline.

The QSF paths resolve from `design/`. The SDC uses no blanket asynchronous
clock-group, false-path or multicycle waiver for functional datapaths. Only
asynchronous reset and the inputs of named first synchronizer stages are cut.
Held mailbox payloads and frozen tile metadata have explicit3.750ns maximum
and0ns minimum path bounds; the acknowledgement protocol guarantees the
capture does not race a changing payload. The second synchronizer stages,
all ordinary single-cycle logic and synchronous M20K ports remain timed.
Native Quartus must independently resolve these collections, check generated
memory clocks and report no unconstrained functional paths.

The board adapter must provide512-bit byte-addressed Avalon-MM with write
responses, its actual calibrated application clock and a reset-qualified
`rst_n`. Because the frozen top has no separate calibration port, the shell
must keep `rst_n=0` until calibration succeeds; calibration loss must assert it
and quiesce all EMIF traffic. The image guard's synchronized DDR-up indication
means local reset release under that shell contract, not a fabricated
calibration detector. Shell resource usage, DDR pin placement, PCIe integration
and real generated-clock constraints are native L2/L3 prerequisites, not
established by this core QSF.

## Independent verification and implementation evidence

No behavioral simulation, reference comparison, mutation trial, Yosys synthesis,
Quartus compile, STA or physical-board experiment has been performed by Designer.
The dedicated Verifier owns those sources and checks. Any static elaboration
receipt is advisory preparation only, never arithmetic or protocol acceptance.

The preceding seventeen-source increment passed one Icarus static elaboration
(`iverilog -g2012 -t null` with the explicit source list recorded in
`evidence/preparation/static-elaboration-20261026T105153Z-8144f67b/receipt.json`).
Its exit was zero and no simulation executable was run. The earlier ten-source
receipt remains at
`evidence/preparation/static-elaboration-20261026T104024Z-8f052237/receipt.json`;
neither receipt certifies the integrated product.

The current25-source increment also passed static Icarus elaboration, exit0:
`evidence/preparation/static-elaboration-20261026T110428Z-af197549/receipt.json`.
This earlier command parsed/elaborated only the then-saved modules. No
functional simulation, synthesis or timing check was run.

The admitted D1..D5 suite and all original mandatory execution checks remain
unchanged. Default AWQ projection service-inclusive speedup must independently
meet 8x against the immutable scalar parent under the frozen service policy.
The peak compute capacity is analytically 64 MAC/cycle, or 6.4 GMAC/s at
100 MHz, not a measured rate. Raw DDR peak, DDR service bandwidth and useful
compute-consumed bandwidth are different quantities. Full device fit must
include real EMIF/PCIe shell resources and the 3 MiB default stationary KV data.

`design/SPEC.md` supplies the integration/upload/reproduction protocol. Exact
checkpoint identities, acquisition/repacking implementation, actual verifier
commands beyond the frozen entry points and measured claim-to-evidence links
remain independent verification outputs. No private host path or runtime
metadata is a product dependency.

The connected29-source design passed Icarus Verilog12.0 static elaboration:

```sh
iverilog -g2012 -Wall -t null rtl/*.sv
```

Retained source hashes, exact argv, version and raw output are in
`evidence/preparation/static-elaboration-20261026T112102Z-bce8a451/receipt.json`
(exit0, no diagnostics). Its predecessor at
`evidence/preparation/static-elaboration-20261026T112015Z-76fb7433/receipt.json`
failed with exit2 because the new compatibility projection sorted before its
package. Renaming it to `anvil_q1_ht_compat_projection.sv` restored package-first
portable source ordering; the repaired receipt explicitly links that failure.
No functional executable, synthesis or hardware check was run. Independent
Verifier execution is the next step, with every admitted check still mandatory.
