# Anvil-B1 architecture and implementation boundary

The admitted design is a complete external-memory-backed decoder, not a set of
demonstration kernels. SPEC.md fixes the product graph, numerical contract,
public interfaces and acceptance obligations.

## Implementation strategy

Separate the throughput-critical LUT ternary tree from iterative scalar math.
The tree captures a full LANES-wide tile each advancing clock; decode and every
balanced reduction level are separately registered. A global pipeline enable
preserves stalled results and aligned metadata. No multiply is used in this
hierarchy; radix decoding is a finite lookup.

Scalar arithmetic outside that hierarchy uses registered, bounded-carry
operations. Unsigned restoring division and integer square root process one
bit/pair at a time with segmented subtract. Signed multiplication forms 16x16
partial products and segmented sums. Scalar DSPs, if inferred, must be reported
separately from zero-DSP ternary projections. Generic syntax or synthesis cannot
establish Arria 10 mapping or 100 MHz timing.

The fusion working set is bounded by max(hidden,intermediate), never by model
weight count or sequence length. Separate synchronous memories retain vector
samples, gamma and final normalized values. Collection precedes sum-of-squares,
mean, epsilon addition/root, per-element normalization, complete-vector absmax,
then quantized emission. Gate/ReLU2/up intermediates remain local.

The eventual GEMV controller owns complete signed 64-bit row dots. Its packed
source cursor advances continuously within a row, with explicit digit/byte/word
wrap counters, then repacks into the full derived MAC WEIGHT_BITS. This is
important at LANES=1 and 2: no intervening 2*LANES wire is allowed. Activation
quantization is shared across Q/K/V and across gate/up.

The decoder issues learned norm, ternary projection, attention and residual
operations in model order. Attention owns split-half pipelined RoPE and an
INT8 codec, committing physical KV heads only once. Online softmax retains
only one head's running maximum, denominator and weighted context, not a
score/probability SRAM spill.

## Memory ownership

All large model tensors and persistent KV payloads/metadata live externally.
Scratch slots are token-local and single-owner: embedding produces slot 0;
layer input norm produces slot 1; Q/K/V produce 2/3/4; attention consumes
2/3/4 and produces 5; attention-SubLN produces 15; O produces 6; first
residual produces 7; post-attention norm produces 8; gate/up produce 9/10;
fused gated FFN SubLN produces 11; down produces 12; final layer residual
produces 13. Before a following layer, slot 13 becomes slot 0. Final norm
produces 14 for the tied head. A consumer releases a slot only after its
complete read/operation. No two operations overwrite a live source slot.

The planned bank scheduler maps bank to low bank-index bits of
`row XOR col XOR layer XOR zero_extended(kind)`. BANKS is power-of-two; no
runtime modulo is necessary. It assigns opaque globally unique live tags and
retains owner/order state through drain. Returned data is delivered in each
client's request order even when physical banks return out of order.
The parent scheduler has been inspected, but is not yet a B1-qualified reused
component. B1 wraparound, corruption and drain semantics require independent
verification; parent provenance is not a passing baseline.

## Phase schedule conventions

Every listed duration counts advancing clock edges with valid/ready
acceptance at the phase boundary. A state that launches another registered
block requires a separate following observation edge; child completion cannot
be consumed on its own production edge. Memory request and response waits have
unbounded external stall duration. The specification makes no globally fixed
token latency claim.

MAC: capture at E0, decode at E1, level j at E(1+j), j=1..log2(LANES).
Result consumption is a later pre-edge handshake.
Scalar primitive/fusion schedules are documented alongside their implementation
as sources are saved; unfinished phases have no claimed measured latency.

## Current saved-source boundary

Initial implementation work establishes the contract and standalone arithmetic,
ternary and fusion/telemetry foundations. The top-level decoder, complete memory
transport, GEMV row assembler, attention/cache/RoPE integration and token/head
pipeline remain required until explicitly implemented. There is no ready
engineering handoff, functional result, synthesis result, timing result,
benchmark score or product PDF at this boundary. Verification-owned sources
must not be created by Designer.

The missing parent GENERATIONAL_HANDOFF.md prevents historical STA/PPA
comparison only; it does not authorize inventing numbers or waiving B1 timing.
Lessons exp-6d5cc92e6f5a86894eaae275 (diagnostic-safe illegal geometries) and
exp-ccbc2b80623e40ab6ea62b21 (small ownership arrays versus true RAM) inform
structure only and are not acceptance evidence.
