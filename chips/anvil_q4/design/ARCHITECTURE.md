# Anvil-Q4 implementation architecture

## Chosen organization

Use an externally backed, tiled, resource-shared accelerator. External memory
holds tables, scratch and KV history; bounded local buffers hold active tensor
tiles and arithmetic state. This avoids whole-model on-chip arrays without
replacing any layer with software-computed results.

Each processing unit issues semantic word requests to a bank scheduler.
The caller supplies the descriptor-derived row stride. The scheduler registers
bank selection, reserves exact tag ownership and offers a stable request.
Returned responses remain owned until the originating client consumes them.
Flush discards client delivery but drains accepted transactions. A malformed
response faults the command, not a success-shaped zero.

The descriptor has separate active/shadow images. Geometry validation uses
registered products and bit-serial remainders rather than combinational
division. Its reset-image constant function is declared at module scope for
standards-compliant constant evaluation, retaining the BANKS-dependent image.
Each shadow write temporarily closes the configuration interface
until its derived validity is current. Thus accepting a commit needs no
variable-latency validation: its response and activation occur after the next
edge, matching SPEC.md.
The registered `cfg_done` and `cfg_error` status outputs are continuously masked
to zero during active reset, including before asynchronous register updates
settle; the mask adds no response cycle.

The intended compute organization shares registered FP32 primitives through
handshake-driven stage controllers. FP32 remains the representation of scratch,
accumulators and residual streams. A16 table/cache boundaries and hardware
dequantization are explicit conversions, not relabeled fixed-point arithmetic.
Legacy execution needs a distinct runtime-configurable fixed-point path with
the parent's observable packing/cache rules.

## Dependencies and ownership

| Producer | Consumer | Guarantee |
|---|---|---|
| Descriptor | Top and engines | Atomic validated geometry; no active-image change on rejection |
| Top | Descriptor | Quiescent only when command, result, batch and memory ownership are empty |
| Engines | Scheduler | Stable semantic coordinates, correct descriptor stride, consume each response once |
| Scheduler | Engines | Registered requests, exact response ownership, explicit errors, bounded bank queues |
| Bridge | Scheduler | One tagged response per accepted read/write; eventual response only for progress tests |
| Top | Cache/speculation | Sequence epoch and accepted-prefix reachability |
| FP leaf | Stage controllers | IEEE operation, declared fixed latency, stable result under stall |
| Shared runtime | Delivery | Independent checks, timing/board gates and post-acceptance product reporting |

## Source inventory and verification boundary

This is an implementation handoff, not independently accepted accelerator
correctness, timing or hardware delivery.

| Source | Status |
|---|---|
| `rtl/anvil_q4_descriptor.sv` | Shadow/active descriptor controller and mode-specific validation |
| `rtl/anvil_q4_bank_scheduler.sv` | Tagged, runtime-bank, semantic-coordinate scheduler |
| `rtl/anvil_q4_00_fp_pkg.sv` | Synthesizable integer-bit FP representation, rounding, conversion and ordering helpers |
| `rtl/anvil_q4_fp32.sv` | Single-issue registered FP leaf, including iterative division and square root |
| `rtl/anvil_q4_dequant.sv` | Scalar native/W4/W8 lane dequantization through the actual FP leaf |
| `anvil_q3_reference/rtl/*.sv` | Unchanged architectural reference; never a test oracle or delivered-build dependency |
| `rtl/anvil_q4_umul64.sv` | Unsigned segmented 64-bit multiplication for the nonlinear unit |
| `rtl/anvil_q4_exp.sv` | Sequential fixed-point range reduction and degree-16 exponential polynomial |
| `rtl/anvil_q4_silu.sv` | Sign-stable SiLU through the exponential and FP32 leaves |
| `rtl/anvil_q4_activation_quantizer.sv` | A8 ratio rounding, signed code conversion, rescaling and BF16 boundary |
| `rtl/anvil_q4_tensor_array.sv` | Bounded activation tile, per-tile A8 scale, masked parallel output rows and ordered FP32 dot reductions |
| `rtl/anvil_q4_mem_port.sv` | Registered single-transaction semantic-word client port, including coincident request/response |
| `rtl/anvil_q4_gemv.sv` | Runtime projection geometry, ragged row/input tiles, group/lane coordinates, descriptor-gated bias and streamed native lm-head |
| `rtl/anvil_q4_rmsnorm.sv` | FP32 squared reduction, mean/epsilon/root, native gamma widening and scratch output |
| `rtl/anvil_q4_rope.sv` | In-place split-half FP32 rotation using generation/position-qualified coefficients |
| `rtl/anvil_q4_elementwise.sv` | Scratch-backed residual addition, copy and SiLU(gate)*up |
| `rtl/anvil_q4_swiglu_mlp.sv` | Connected gate/up, nonlinear product and down projections |
| `rtl/anvil_q4_kv_cache.sv` | Q4 page lookup/alias scan, BF16 codec, per-head K/V INT8/FP32 escape codec and acknowledged payload-before-metadata publication |
| `rtl/anvil_q4_gqa_attention.sv` | Ordered causal scores, max-subtracted softmax and ordered contexts with an explicit cache-command interface |
| `rtl/anvil_q4_decoder_layer.sv` | Connected attention norm/QKV/RoPE/cache/GQA/O/residual/FFN norm/MLP/residual sequencing |
| `rtl/anvil_q4_token_io.sv` | Native embedding widening to slot0 and complete vocabulary projection from slot14 |
| `rtl/anvil_q4_speculative.sv` | Two-target greedy verification, sequence validation and delayed prefix-commit notification |
| `rtl/anvil_q4_top.sv` | Public interface, real required children, complete layer loop, final-logit completion, sequence/epoch ownership, mode switching, cancellation/drain and speculative integration |
| `rtl/anvil_q4_compat.sv` | Runtime Q1/Q2/Q3 full-token sequencer with registered internal memory arbitration |
| `rtl/anvil_q4_legacy_gemv.sv` | Runtime transposed AWQ projection with original fixed-point leaf arithmetic and wide accumulation |
| `rtl/anvil_q3_*.sv` | Self-contained compatibility dependencies copied from the parent, with runtime geometry/cache selection in the stage controllers |
| Independent `tests/*` | Verifier-owned, not authored by Designer |

Descriptor internal outputs are a packed 32-word `active_words` image (word0
in the least-significant 32 bits) and `cfg_busy`. Top integration must use the
successful `cfg_done && !cfg_error` response to invalidate sequences, predictions,
cache epochs and descriptor-generation coefficient bindings.

Scheduler clients are parameterized by CLIENTS. Their packed request/response
fields use the same least-significant-client convention as public banks.
`c_req_stride` is the row stride in **words**, not bytes. `legacy_mode` selects
the additive legacy bank key; otherwise low bits of row*stride+col determine
the bank. Scheduler configuration must remain stable while non-idle. Only
validated descriptors may drive active_banks.

The scheduler supports up to QUEUE_DEPTH owned transactions per bank. Each client
has at most one owned transaction at a time; separate clients enable concurrency
and bank overlap. An offer consumes capacity before bridge acceptance; a returned
response consumes capacity until client retirement. This avoids unbounded
response buffers. It is a resource-sharing choice, not a throughput claim.

The FP leaf normalizes finite operands into a 24-bit significand and signed
unbiased exponent. Addition aligns with guard/round/sticky bits, registers the
sum/difference, normalizes, then rounds. Multiplication registers the exact
48-bit product before normalization/rounding. Division generates 27 quotient
bits by registered restoring subtraction; square root consumes two radicand bits
per restoring iteration. Remainder nonzero contributes the final sticky bit.
The result slot enforces the declared 8/2/64-cycle public latencies, including
special values, and holds until accepted. These are implementation intentions,
not independent arithmetic correctness results.

Conversion ops take BF16/FP16 from a[15:0]; narrowing returns the format encoding
in result[15:0] with result[31:16]=0. BF16/FP16 NaNs narrow to 0x7fc0/0x7e00
and widen to canonical FP32 0x7fc00000. Signaling NaNs set invalid. Tininess is
detected after rounding for underflow flags. FP ordering helpers are unordered
for NaNs and equate signed zeros; stage controllers must propagate NaNs rather
than treating an unordered comparison as a finite default.

`anvil_q4_dequant` accepts one lane using ready/valid. Weight format0 is native,
1 is W4, 2 is W8; activation_format0/1 chooses BF16/FP16 for native input.
W4 lane0..7 uses AWQ offsets and W8 lane0..3 ascending bytes. An inactive lane
returns zero without inspecting its metadata. Active malformed scales/zeros or
native upper bits produce an error response, not a successful zero.
Quantized lanes issue signed integer conversion, FP32 multiplication, BF16
narrowing and exact widening in that order. Native lanes only widen in their
selected format. The output result/flags/error remain stable under backpressure.
Per-tile A8 scale calculation and lane orchestration are supplied by the
tensor-array controller described below; neither has independent numerical
acceptance yet.

## Q4 compute-stage implementation

The tensor array accepts one command containing a valid input-tile length, output
row mask and initial FP32 sums. It first loads all valid activations into a
synchronous bounded RAM. A8 scans the actual tile, computes maxabs/127 (scale1
for an all-zero tile), rounds signed ratios ties-to-even and rescales through the
BF16 boundary. A16 scratch inputs are used directly as FP32; they are not narrowed
again at each projection. After loading, one weight bundle per increasing input
index supplies payload/zero/scale/lane fields for every active output row.
Each active row uses actual dequant, multiply and add children. Masked rows issue
no arithmetic or metadata validation and retain their initial sums. An entire
bundle advances only after every participating lane is ready or has returned.

GEMV drives that protocol from semantic memory coordinates. TILE_ROWS controls
parallel output rows (including three); TILE_K controls input buffering (including
one and seven). The global input/group counters survive input-tile boundaries:
a tile boundary never restarts an AWQ group or packed-word lane. Incomplete rows
and final input tiles are masked before requests. The implementation rereads
packed words and group metadata for individual logical inputs; this is a
correctness-first folded schedule, not a claim of optimal traffic or overlap.
Native/symmetric formats issue no unnecessary zero-point reads. Native lm-head
uses kind0/proj1 and streams every vocabulary row rather than writing outside
the scratch ABI.

RMSNorm traverses squares and sums in increasing index order, divides by hidden,
adds epsilon and computes the root through the FP leaf. Its second pass widens
gamma, multiplies gamma*x, divides by the root and writes the declared norm slot.
RoPE reads both halves before overwriting either, computes four separately
rounded products and the subtract/add pair, then acknowledges both writes.
Its coefficient requests retain descriptor generation and token position.
Elementwise operations read both residual operands before each write.

The exponential converts finite FP32 inputs to signed Q8.56 for repeated ln(2)
range reduction, maintaining a signed binary exponent. A degree-16 Horner
polynomial uses unsigned Q2.62 coefficients, segmented 16x16 products and
32-bit carry-propagating accumulation steps. The final FP32 pack implements
gradual underflow. Extreme finite arguments outside [-104,89] take mathematically
rounded zero/overflow paths; values inside that interval are not clamped.
SiLU uses exp(-abs(x)), computing x*exp(x)/(1+exp(x)) for negative finite x
and x/(1+exp(-x)) otherwise. This prevents an avoidable positive exponential
overflow for large negative inputs. Accuracy remains independently unverified.

Attention owns one reusable 131072-word FP32 score RAM (4194304 data bits),
not a per-layer/model activation array. One query head at a time writes causal
scores, computes max-subtracted exponentials and their ordered sum, normalizes
the stored weights, and then reduces each context component in increasing token
order. RAM reads and writes are synchronous and not asynchronously reset;
the controller writes every used score before reading it. Explicit ratio
counters select contiguous query-head groups. No host-computed score, activation
or acceptance value is supplied.

The decoder has direct real norm, gemv, rope, attention, kv_cache, mlp and
elementwise children. Its twelve phases serialize public scratch lifetimes:
attention norm; Q/K/V; Q/K RoPE; cache plus attention; O; first residual;
FFN norm; SwiGLU/down; final residual. Slot0 is not modified by the attention
residual: the final residual reads slots7/12 and only then updates slot0.
Each engine retains memory ownership through its final acknowledged response.
The attention cache-command channel switches the decoder memory owner to the
direct cache child until its held result is consumed.

## Cache and speculative-controller boundaries

The Q4 cache accepts either a full current-token K/V write from scratch slots3/4
or one scalar K/V read. It validates position reachability against a supplied
committed-token count; the attention caller explicitly permits its just-written
current token. The top must supply a tentative count for a second draft target
without changing the real committed prefix.

Every command resolves its epoch-qualified page entry and checks that physical
page against the other reachable logical pages. This uses a bounded sequential
scan rather than a whole-context tag array. It detects missing, out-of-range and
aliased pages without silently using position as a physical address. This folded
choice adds page-table traffic and requires honest cycle/traffic accounting.
Host mappings must remain fixed during a command, as required by the contract.
Top supplies tentative position counts while keeping the committed prefix
unchanged. New-sequence speculative work also supplies the old epoch and token
count. Before writing any new page, the cache scans the old reachable page
entries and rejects physical overlap. This protects the preceding committed
sequence even when a speculative new sequence later fails or is cancelled.
Both intra-epoch and protected-epoch scans precede payload/metadata writes.

BF16 writes round FP32 scratch once and acknowledge each cache word; reads widen
the stored BF16. INT8 scans each K/V head independently, chooses its representation,
rescans the source and acknowledges its payload before publishing kind14 metadata.
Ordinary heads retain FP32-RNE(maxabs/127), scale1 for all-positive-zero heads,
RNE signed codes [-127,127] and FP32 integer-times-scale reconstruction.

The independently admitted escape selects an entire head if it contains NaN,
infinity, negative zero, or a finite nonzero maximum whose FP32 scale rounds to
zero. The scan records this selection independently of the finite max reduction.
`SCALE_WAIT` changes a zero-rounded scale to the exact marker `0x7fc00000`;
it never divides source values by that zero. In particular, maxabs63 minimum
subnormal units escapes, while maxabs64 yields ordinary scale `0x00000001`.
Escape scalars preserve FP32 bits except canonicalizing all NaNs. They use
kind12/13 proj1, col=head*D+dimension, stride=KD, with the ordinary decoder layer
and physical-token row. Marker metadata retains kind14, col=head, stride=KV,
proj0/1 for K/V. Ordinary packed words use kind12/13 proj0, stride=ceil(KD/4).
The scheduler receives the selected stride, so escape bank routing uses KD
without changing page translation.

For each escaped scalar, the writer acknowledges its FP32 word before inserting
a zero ordinary-byte placeholder. For both representations, `ENCODE` flushes a
packed word at a full word or head boundary. Only after the last payload
acknowledgment can `NEXT_SCALAR` advance to `WRITE_SCALE`. A partial shared word
survives metadata publication and the next head's scan, including D=2; the
next head changes only its own byte fields. Thus later writes preserve earlier
acknowledged bytes, and final unused lanes remain zero. No read/modify/write of
uninitialized external packed storage is needed for a new token.

Reads validate ordinary metadata as positive finite nonzero FP32 or select
escape only on exact marker match. They validate the selected ordinary byte
(zero for escape, never -128 for ordinary) and final padding. Escape reads then
fetch proj1 and return its FP32 bits directly, rejecting noncanonical NaNs.
Marker-authorized finite values require no eligibility rescan. Ordinary reads
use signed integer conversion and FP32 multiplication as before.
Page/epoch protection is shared by both encodings and runs before access.
Payload response faults prevent publication; flush suppresses further work.
Physical writes remain tentative until the existing target/prefix retirement
rules make them reachable. No error/cancellation commits a new prefix.

The A8 tile path separately handles finite scale underflow at its BF16 boundary:
when maxabs/127 rounds to zero, every nonzero input is at most 63 FP32 minimum
subnormals, and every possible rescaled nonzero code rounds to signed BF16 zero.
An exact zero input produces positive zero, as integer code zero times a positive
scale does. The cache instead uses the lossless escape because its FP32 output
has no equivalent BF16 boundary. Neither path changes numerical tolerances or
excludes finite inputs. These implementation paths require independent checking.

The speculative controller compares draft0 with an available prior prediction,
requests actual target execution for accepted candidates, and retains the
target argmax at divergence. It never accepts a host-provided acceptance length.
Its commit notification is asserted only on a successful verify-result transfer,
not while that result is stalled. Flush annuls the notification and all pending
work. An internal abort path annuls uncompleted targets and inhibits prefix
commit immediately. Before result publication it produces a zero-length error
bundle; after publication it preserves the ready/valid bundle and separately
latches the fault. The top remembers result retirement even during fault drain,
so it neither waits for an already-consumed result nor launches another target
to report the fault. The command completes with `done/error`; a previously
published success-shaped verify bundle is not permission to commit after a
fault. The top arbitrates normal-token priority, computes target argmax with
lowest-index ties, withholds tentative sequence/cache commits, connects
cancellation and generates the subsequent done pulse. These are connected RTL
paths, not independently established rollback correctness.

## Public top and compatibility execution

The top uses four scheduler clients: Q4 decoder, final norm, token I/O and
compatibility. Each stage retains ownership until its response/completion
boundary. The full command advances through embedding, all descriptor-selected
layers, final norm and every vocabulary logit. Normal command completion is
driven directly by the final accepted logit, not a later child `done`, to preserve
the public completion cycle exactly. That completion cycle flushes the now
finished compute engines but does not erase committed legacy cache counters.

Configuration has priority over new token/draft acceptance. A successful
descriptor commit invalidates sequence/prediction state and flushes scheduler
and compatibility epochs. Failed commits do neither. Coefficient generation
starts at zero and advances once per successful activation. The descriptor
rejects further commits once its 32-bit generation space is exhausted, rather
than silently reusing an old table generation; reset and bridge/table rebinding
are required before reuse. Sequence epochs are also allocated monotonically,
including failed new-sequence attempts; exhausted epoch space rejects further
new-sequence computation rather than wrapping.

Normal tokens and drafts never handshake together. Draft logits feed the real
argmax reducer internally, not the public normal-logit interface. Target
completion carries this argmax into the speculative child. A stalled verify
result owns the command and prevents configuration or normal-token reuse of its
workspace. Prefix count, committed epoch and next prediction change only on a
successful verify-result handshake. Memory/compute failure drains accepted
transactions before reporting the failed target; cancellation suppresses
pending results, drains, invalidates the active sequence and then pulses
`cancel_done` (and `done/error` for an interrupted command).

Compatibility stages retain signed Q16.16 scratch, FP16 external tables,
Q2.30 coefficients and separate fixed-point helpers. Runtime geometry replaces
the parent's elaboration constants without changing the parent directory.
The compatibility sequencer implements attention norm, Q/K/V, RoPE, cache/GQA,
O, residual, FFN norm, gate/up/SiLU/down, residual, final norm and native
vocabulary projection. Its registered arbiter holds a selected child until the
tagged scheduler returns its response; no bank tag is used as a semantic address.

Legacy GEMV reads the original transposed output-channel packing and selects
the AWQ nibble by the original eight-lane permutation. It folds the original
eight-input arithmetic leaf with one masked scalar lane per launch and sums
its exact wide integer products before the original final rounding. Q4
`TILE_K` therefore cannot truncate or redefine legacy packing, including values
one and seven. This folded organization is not a throughput or traffic
improvement claim.

Legacy cache storage has a bounded 256-scalar codec workspace and 64-layer
committed/prefill counters. Effective block length and exponent rules are runtime
selected by descriptor words5/24: Q1 fixed32; Q2 fixed32/INT8 with every allowed
power-of-two block; Q3 fixed32, INT8 block32 and symmetric/asymmetric INT4 block64.
Runtime shifts and explicit counters replace dimension division. Tail
words/lanes are zeroed, payload and metadata retain their original kind
namespaces, and all legacy traffic uses additive bank routing. Helper rounding
functions used by compatibility controllers are evaluated outside sequential
processes and only their outputs are captured.

## Capacity and performance accounting

For an Op-by-Kp projection the useful work is Op*Kp multiplications and the same
number of accumulator additions; these are separate rounded FP32 operations.
Native weight traffic is Op*Kp words before any reuse. Quantized payload traffic
is Op*ceil(Kp/P), with scale and, for asymmetric formats, zero-point traffic
Op*ceil(Kp/G). Scratch transfers and partial tile masks add explicit overhead.
These are analytical counts, not measured cycles or throughput.

At most BANKS*QUEUE_DEPTH scheduler ownership slots exist. No scalar result may
overwrite a slot still owned by an unconsumed response. Each slot contains its
semantic request, client identity, unique tag and eventual response. Queues use
explicit terminal comparisons and wrapping; queue depth three is not a binary
mask case.

No PPA numbers, physical clock result, model accuracy or speedup has been
measured. Missing parent `design/GENERATIONAL_HANDOFF.md` remains a provenance
gap. Current-source timing must independently pass the required native gates.

## Dependencies and reproduction

Required verification dependencies are Python 3, Icarus (`iverilog`, `vvp`),
Verilator and Yosys. No tools were installed during design. Quartus 17.1 and
the physical bridge are shared-runtime requirements, not portable L1 stubs.

Current-source static elaboration, from the delivered root (both packages
sort before their users):

```
iverilog -g2012 -t null -s anvil_q4_top rtl/*.sv
```

These are syntax/elaboration commands only, not simulations or acceptance.
The independently owned eventual portable L1 entry points remain
`python3 tests/verify.py --suite smoke|arithmetic|system|compatibility|benchmarks|mutations|synthesis|portable`;
the complete entry point remains Verifier-owned; existing cache diagnostics do
not replace these suites.

Claim-to-evidence mapping is intentionally empty for numerical correctness,
synthesis, timing and hardware until those tools actually execute under their
assigned ownership. The Designer handoff reports any static diagnostic
separately. Do not treat this inventory as completed acceptance.

## Repair and remaining acceptance work

The independently admitted cache recovery is implemented above. The original
independent diagnostic receipt
`evidence/preparation/cache-recovery-20261102T112514392034Z/receipt.json`
retains the zero-scale, signed-zero, nonfinite, marker-read and early-metadata
failures against the preceding sources. It is not a result for the repaired RTL.
Designer does not rerun functional probes or alter their independent expectations.

The source-level integration audit repaired speculative faults before target
acceptance and after result publication/retirement: abort prevents new target
launches and all commits, stable published payloads are preserved, and retirement
is remembered across memory drain. These are source-level repairs only, pending
independent protocol and numerical checks. The cache repair preserves those
changes and all legacy sources. Independent verification must compare public
payload/metadata writes and decoded reads, including mixed shared words,
subnormal boundaries, nonfinite/signed-zero heads, malformed traffic, all bank
counts, stalls/errors and speculative rollback. All eight L1 checks and native
timing/board gates remain mandatory; no pass is claimed here.
