# HT implementation architecture

## Connected implementation and evidence boundary

The saved implementation includes the fixed-latency physical tensor datapath,
ordered read prefetcher, banked tile store, dense-record KV codec/cache,
configuration validator, shared DDR fabric, host port, scalar coefficient
reader, format converter, multi-tile projection controller, banked vector
storage, iterative integer/exp services, complete numerical token sequencer,
KV burst read-ahead and the connected `anvil_q2_ht_top`. Its legal-parameter
branch contains the five actual named instances `prefetcher`, `tile_buffers`,
`tensor_array`, `kv_cache` and `sequencer`. This is a design handoff, not an
acceptance claim. Independent functional, synthesis and physical checks remain
pending for every component and their integration.

The parent source tree remains unchanged. Its numerical rules inform W4
compatibility; its combinational reciprocal and square-root functions must not
be placed in a production single-cycle HT path. Nonlinear control uses
bounded multi-cycle arithmetic rather than large unrolled replacements.

## Tensor issue and reduction

There are 16 physical banks, each containing eight arithmetic lane instances.
Logical lane `j` maps to bank `j[3:0]`, lane `j[6:4]`. Memory delivery must
implement this mapping with independently readable synchronous RAM slices.
Each issue contains one output row's 128 input contributions. Output-row
contexts are interleaved so accumulation feedback cannot serialize issue.

Each lane captures its own operands at E0. W4 dequantization retains a signed
37-bit result. A signed decomposition into four 19-by-17 partial products
avoids a single combinational 37-by-32 multiplier followed by a long sum.
The low halves have explicit positive sign bits; the high halves are signed.
Partial products form at E4, two signed partial rows add at E5 and combine at E6.
The following seven tree levels each pipeline a 128-bit addition across four
32-bit carry stages. Two's-complement extension happens before reduction.

BF16 lane multiplication uses explicit integer significands and exponents,
not `real` or `shortreal`. Q16 activation conversion is nearest-even and finite.
BF16 subnormal weights retain their effective exponent and unhidden
significand. Product packing includes guard/sticky bits for FP32 subnormal
rounding. The tree uses 27-bit significands (24 retained plus guard, round and
sticky), magnitude ordering, jammed alignment, add/subtract, bounded
normalization and nearest-even packing. Exact cancellation returns positive
zero; the sum of two negative zeros retains negative zero.

Integer and floating tree datapaths have identical register counts. The
common enable freezes operands, partial products, carries, floating metadata,
errors, validity, modes and tags together. There is no extra output register.
Reset clears state asynchronously; public outputs are additionally reset
qualified. Errors preserve transaction identity and latency.

## Ordered prefetcher

`anvil_q2_ht_ddr_prefetcher` accepts a queued tile read containing a 64-byte
aligned byte address, 1..64 beats, slot number and generation. The caller must
allocate the complete corresponding slot before presenting the command; this
is the reservation for every future unbackpressurable beat. A command is
range-checked against `region_base` and exclusive `region_end`; the latter is
34 bits so the end of the full 8 GiB space is representable.

The request queue, current tile, held Avalon command and ordered accepted-burst
ring have distinct ownership. Each burst ring entry records slot, generation,
starting beat, burst length and final-tile-burst flag. A tile can have multiple
accepted bursts. The ring head advances only on its final returned beat, not on
command issue. The ring supports a final response and a new accepted command on
the same edge, including depth one. Both queue pointers and ring pointers wrap
explicitly, including non-power-of-two depths.

Burst lengths are the minimum of remaining beats, 16 and the distance to the
next 4 KiB boundary. A registered command holds address/count unchanged under
waitrequest, including flush and DDR fault. Once a command is accepted its ring
reservation remains until all responses return. There is no read-response
ready signal.

`fill_*` is a direct, reset-qualified return-beat event sampled at the same
edge as `avm_readdatavalid`. Its slot/generation/offset identify reserved
storage; it is not a backpressurable response. `reject_*` reports a malformed
accepted tile command as a registered one-cycle event. `fault` reports malformed
requests, unexpected responses, non-OK responses and DDR faults. Integration
must latch faults and initiate global draining. A held-high `ddr_fault` may
hold `fault` high. Absence of a fault does not establish numerical correctness.

Flush drops unissued queued/current work, suppresses return delivery and drains
accepted reads. `drained` is a level indicating flush/drain with no held or
accepted transactions. `idle` additionally requires no queued/current work and
no drain state. A shared DDR fabric must route only this client's ordered read
returns into the prefetcher; host and KV transactions cannot be injected into
its response channel.

## Tile RAM and ownership

`anvil_q2_ht_tile_buffers` owns two to eight slots, four by default. Explicit
states are FREE, FILLING, READY, EXECUTING and DRAINING. Allocation supplies a
generation different from that slot's previous generation. In a new allocation
all completeness and error state clears; RAM payloads need not clear.
Allocation does not itself issue a DDR command.

The independently handshaken operand channel loads one 128-lane activation
vector and keep mask per slot. The metadata channel loads expanded zeros/scales
for each of 16 output rows in W4 mode; BF16 requires no AWQ metadata. The fill
channel accepts exactly 16 W4 or 64 BF16 ordered beats. A final beat is checked,
not trusted: offset, mode-derived total, generation and final marker must agree.
A bad or errored fill cannot make a tile executable.

Completeness becomes READY on the registered scheduling edge after the last
required input has been stored. The execute channel claims READY ownership.
Each issue supplies a slot/generation, output row and downstream arithmetic
tag, and returns a complete operand vector one registered RAM-read edge later.
The one-entry output can be replaced on its accepting edge and freezes all
RAM-read registers under backpressure. Release is blocked while that slot has
a stalled output or a simultaneous issue. A slot must be released before a
new generation is allocated.

Each of the 16 banks contains eight independent RAM slices. Logical lane
`bank + 16*slice` has a weight RAM, AWQ metadata RAM and activation RAM.
W4 beat `r` writes row `r` in every slice. BF16 beat `{r,q}` writes row `r`
in the two slices per bank belonging to logical quarter `q`. All 128 slice
read ports operate together. No serialized 128-way weight selection supplies
the array. The `ramstyle` attributes request M20K inference, but actual mapping,
capacity and routing remain unproven until the native Quartus gate.

Flush immediately suppresses operand output and enters DRAINING. Slots return
to FREE only after `drain_complete` is observed with flush deasserted; generation
history is retained. Stale returns cannot write a new allocation. Integration
must hold the drain-complete indication long enough for this edge.

## Dense KV codec

`anvil_q2_ht_kv_codec` is a serial, bounded-depth record encoder/decoder. It
accepts one block at a time and holds its response
until a later accepting edge. `annul` discards in-progress local codec work; the
cache controller remains responsible for external transaction draining.
Block size is a power of two in 1..128. `WORDS` is a diagnostic port-size helper
and must equal `CACHE_BLOCK` for a legal instance.

Mode zero encodes exactly `4*B` little-endian Q16 bytes. Mode one encodes
exactly `2*B` little-endian raw FP16 bytes from each input word's low half,
returning zero-extended payloads. The codec intentionally does not reject raw
FP16 NaN/Inf: storage is lossless, whereas numerical consumption must validate
and convert separately. Mode two encodes exactly `B+1` bytes: exponent, then
signed bytes. Unused output bytes are zero on encoding.

INT8 encoding scans exact unsigned magnitudes, searches monotonically from
exponent zero to 25, and performs magnitude-based halfway-away rounding with
clamping to [-127,127]. The response includes reconstructed values so resident
storage can match a forced DDR miss, rather than accidentally retaining
uncompressed inputs. Decoding rejects exponent greater than 25 and byte -128.
Expansion is signed 64-bit followed by saturation; no 32-bit overflow is
allowed before the clamp.

## Hybrid KV controller

`anvil_q2_ht_kv_cache` exposes the admitted block and commit channels plus
configuration, a single-beat backing-memory client and an idle indication for
global draining. Commit has priority over a simultaneous block request.
Only one block or commit transaction is outstanding, including its held
response. The backing-memory client is a request/response channel, not a
completion-on-request-acceptance shortcut. Its fabric must return a response
for a write only after the physical DDR write response.

For block size `B`, head count `K` and head dimension `D`, the number of blocks
per head is `D >> clog2(B)`. Let `R` be record length (4B, 2B or B+1 bytes)
and `S = align_up(K * (D/B) * R,64)`. The byte address is

```
cfg_base
+ (((layer * 2 + value) * MAX_SEQ_LEN + position) * S)
+ ((head * (D/B) + block) * R)
```

Here the divisions describe compile-time geometry only; no runtime divider is
used in addressing. The configuration base must be 64-byte aligned and its
allocation must cover `NUM_LAYERS * 2 * MAX_SEQ_LEN * S` bytes inside 8 GiB.
These conditions keep every full-beat backing read within the allocation,
including the padding at each token-region end. Configuration is stable until
an invalidate; the top must invalidate KV state when committed cache
configuration changes.

Address generation has separate token-region, stride-product and base/range
stages. Write encoding precedes memory issue. Dense record bytes are coalesced
into masked 64-byte commands; a crossing record generates additional beats
without overwriting neighboring records. Reads unpack only the record's
bytes before codec validation. Each write beat awaits a real backing response.
There is no padded 64-byte allocation for an individual small INT8 record.

The M20K-requested resident RAM stores decoded blocks: exact Q16 values,
zero-extended raw FP16 payloads, or reconstructed INT8 values. Parallel tag
comparisons feed a bounded binary selection network. A resident read uses a
synchronous RAM read and emits no backing request. A miss or successful write
installs only after all memory responses and codec validation. Replacement
is round-robin with an explicit wrap, including capacity one and three.
All writes are write-through, so eviction never discards dirty data.

Each layer has a consecutive committed-position count and a bitmap covering
both K/V selectors, all heads and all blocks of its next position. Only a
successful, fully acknowledged block write sets a bitmap bit. Commit requires
every bit, the expected consecutive position and a valid configuration.
It then advances that layer's count and clears the bitmap. Reads of uncommitted
positions fail even if a matching resident tag exists. Global token publication,
prefill/decode phase rules and cancellation completion remain sequencer/top
responsibilities.

Invalidation clears resident and commit validity, not DDR bytes. It immediately
suppresses public block/commit responses and codec work. If a backing command
is already held, its address/data/mask remain stable until acceptance; an
accepted transaction drains before idle reasserts. Responses consumed during
drain are discarded rather than installed. Memory or codec faults invalidate
all cache visibility and produce an error response for the active request.
An incomplete commit returns an error without exposing its position.

## Configuration ownership and atomic commit

The configuration module separates mutable host shadow state from committed
descriptor snapshots. Shadow payload RAM is qualified by per-word reset
validity; no bulk asynchronous RAM clear is needed. Required shapes and formats
are derived from parameters and descriptor index, never trusted host shapes.
Each required descriptor produces its main interval and, for AWQ, two derived
auxiliary intervals. A sequential scan compares every new interval with all
previous intervals, including the entire configured KV allocation. It checks
all reserved entries rather than skipping their content.

Descriptor multiplication, length construction, range construction and
overlap comparisons occur in distinct states. Pairwise interval storage has
synchronous reads and an explicit read/compare phase, so no multi-hundred-entry
combinational overlap network is required. Validation length depends on the
descriptor count; it is not a one-cycle CSR write.

Only after validation completes does the module copy the shadow image into
the inactive committed bank. The final copy edge swaps bank ownership and
committed mode/base/length together, generates `configuration_changed`, and
creates the successful configuration response. An annul during copying does
not change the active bank. Failed commits preserve the previous model
configuration, rather than leaving a partially copied table accessible.

The top must serialize commit/invalidate against accepted token/host activity.
The chosen integration priority is configuration, then idle host access, then
a new token. Idle shadow edits do not authorize DDR weight writes while the
previous committed configuration remains valid. Configuration changes must
invalidate sequence/KV visibility and coefficient-cache validity before the
next operation.

## Shared DDR ownership

The fabric captures one stable external command at a time. A prefetcher
handshake transfers a burst into this command register; physical Avalon
acceptance subsequently inserts its owner/count into the fabric's ordered read
ring. Thus the fabric can add request latency but never returns data on the
upstream acceptance edge. The prefetcher's tile reservation remains live
through both levels of ownership.

Read-client capacity is reserved at capture: one private held response for
each single-beat client, already-reserved tile storage for weight prefetch,
and sixteen reserved lines for KV read-ahead. The fabric has separate
unbackpressurable return ports for those two burst owners. No second request
for a single-beat client is accepted before its response retires.
The read ring tracks accepted bursts, and the beat counter advances only on
actual `avm_readdatavalid`. Physical write acceptance instead records an
independent write owner, released only on `avm_writeresponsevalid`. Read and
write returns can coincide for different owners. Both use the response code
supplied by the platform for that cycle.

Round-robin command selection prevents a perpetually requesting prefetcher
from excluding metadata/KV/host service. Queue pointers wrap explicitly for
all admitted outstanding counts. A command register is not withdrawn on a
DDR fault or cancellation; its owner must drain the actual response. The
fabric reports unexpected/non-OK responses and malformed requests through
`fault`. A misaligned single-beat client request returns an error without
touching DDR. The weight prefetcher and KV burst adapter construct legal bursts;
an illegally formed internal burst faults and is not issued.

The host frontend owns an accepted request through physical completion and
external response acceptance. Its `memory_idle` separately indicates that no
command/response remains in DDR, even if its completed external response is
backpressured. Cancellation inhibits new host work, not a previously accepted
write's physical completion. Host writes while configuration is committed
return an error, without issuing a fabric command.

## Projection scheduling and accumulation

The projection engine has independent cyclic allocation, main-prefetch,
activation, metadata and execution cursors. Allocation can reserve every free
slot without waiting for older metadata or computation. The allocation
records tile address, logical input/output bases and a monotonically advancing
generation. The main cursor can enqueue future tile bursts while the execution
cursor issues a different slot; neither cursor owns the other's storage.
Release precedes reuse by a registered edge.

An activation request obtains 128 Q16 words from the sequencer's
on-chip vector store. The projection engine derives the column keep mask from
the logical dimensions rather than trusting a memory payload mask. In W4 mode
the metadata cursor reads output-major/group-minor zeros and scales, expands
each group into its physical lane slices, and sends all 16 metadata rows,
including zero metadata for padded output rows. A two-line scalar read cache
allows a zero line and a scale line to coexist. BF16 needs no AWQ metadata.

Execution claims only an allocated slot whose required channels have been
sent; tile-buffer readiness still gates the final registered transition.
It issues the tile's logical output rows in increasing order, then releases
the slot only when the tile-buffer output can retire safely. It executes
input chunks in increasing order for one 16-row output group. The next
output group may already be prefetched, but cannot overwrite the current
group's accumulator contexts.

Array tags contain a 24-bit command epoch, an eight-bit chunk index and a
32-bit logical output row. Accepted results must match the active epoch,
output group, storage mode and that row's next chunk index. A four-stage
128-bit segmented adder and a four-stage FP32 adder form cross-chunk sums.
Each row's busy bit prevents feedback hazards, including one-row recurrence.
The first BF16 chunk bypasses addition to positive zero, retaining its exact
FP32 word; subsequent chunks use the specified ordered FP32 additions.
Results become externally available only after all chunk sums for that group
have been written back. Row/result order is independent of downstream stalls.

The emitted sums are deliberately **before bias and final conversion**.
The sequencer adds Q/K/V bias at the admitted scale/format, then applies the
sole final conversion before writing the destination vector. Numerical or
memory faults propagate to global draining instead of returning a successful
partial row. The projection engine alone is not D5 or complete model execution.

## Numerical token sequence and vector storage

The sequencer is a registered controller with one outstanding scalar helper
request at a time. Generic request/wait states preserve the request's return
state and operands; a helper's newly created response is consumed on a later
edge. Projection allocation, DDR prefetch, metadata loading, array issue and
cross-chunk accumulation remain independent of this scalar controller.

The logical vectors are X (residual hidden state), N (normalized hidden state),
Q, K, V, A (attention context), O (projection output), G (gate), U (up) and
M (SwiGLU). Twelve physical vector identities of `max(H,I)` words are allocated.
Logical lane `bank+16*slice` has a dedicated 32-bit RAM slice. One RAM port
writes scalar results; one shared read port obtains all 128 activation lanes
or a scalar read. Simultaneous scalar/tile requests give scalar priority.
The RAM output is selected through registered eight-slice and sixteen-bank
muxes for scalar reads. A blocked tile response prevents scalar reads from
overwriting its data. No RAM payload reset is required: embedding and each
operator initialize all logically consumed values before use. Tail activations
are explicitly masked to zero before array transfer.

The token program performs embedding and then, for each layer, first RMSNorm,
Q/K/V projection/bias, split-half RoPE, K/V store/commit, causal GQA,
O projection and residual, second RMSNorm, gate/up projections, SwiGLU,
down projection and residual. After all layers it performs final RMSNorm and
the complete LM head. Layer/vector counters wrap at their actual dimensions;
no runtime division is used for head grouping or block indexing.

Q/K/V projection biases are FP16-to-Q16 plus exact shifted addition in W4
mode, or actual BF16-to-FP32 plus rounded FP32 addition in BF16 mode.
There is only one final result conversion. Non-AWQ FP16 LM-head words preserve
the parent's signed Q16 dot rule through exact scalar accumulation. BF16
LM-head rows load 128 activations and actual BF16 weights and arbitrate the
same physical tensor array after tiled projection work is complete. Its chunk
tag is `{vocabulary,input_column}`; fixed-tree chunk results accumulate in
increasing column order before one Q16 conversion. No second array or
floating-point software fallback is hidden behind that interface.

RMSNorm performs an exact square sum, floor mean, epsilon addition, floor
integer square root, floor reciprocal and full-width normalization products.
RoPE reads both split-half components before writing either result. SwiGLU
uses the six-term integer exponential, integer sigmoid quotient, Q24 SiLU
rounding and Q16 gate/up rounding. Residuals saturate only at their output
boundary. The exact equations are specified in `design/SPEC.md`.

The shared integer service adds/subtracts 128-bit values through four
registered 32-bit carry stages. Signed multiplication decomposes operands
into signed-top/unsigned-low 16-bit limbs, forms a registered 17-by-17 partial
product and accumulates its shifted signed value through that segmented
adder. Division consumes one dividend bit per trial and serializes every
wide subtract; square root consumes two radicand bits per trial with the
same bounded subtract. RHAZ separates magnitude formation, two shift stages,
round increment and sign restoration. There is no unrolled Newton reciprocal,
unrolled square-root datapath, runtime division/remainder operator or
`real`/`shortreal` computation.

For each query head, attention stores exact rounded scores for all causal
positions in synchronous RAM and finds their maximum. A second pass stores
the specified exponentials and exact denominator. Each context component
then reads V blocks, forms the exact weighted sum and performs one signed
rounded division. KV-head selection uses an explicit consecutive group
counter. Score/exponent RAM entries are overwritten before the corresponding
head reads them; reset/invalidation clears control visibility rather than
bulk-clearing these RAMs.

## KV DDR burst read-ahead

The block cache's single-logical-beat backing interface connects to
`anvil_q2_ht_kv_burst`, not directly to a one-beat-only DDR implementation.
A miss reserves sixteen 512-bit line slots and issues a real Avalon read
burst of 1..16 beats. Its start is the requested beat and its end is bounded
by the configured allocation and 4 KiB page. The first returned beat is the
requested result; later beats populate a synchronous read-ahead buffer.
The adapter completes the logical backing request only after every burst
response has returned and all response codes have been checked.

Subsequent backing-beat hits avoid another Avalon read; independently,
resident decoded-block hits avoid even a backing request. The adapter clears
its read-ahead validity before every masked write and forwards writes through
the fabric's real write-response ownership. These are byte-coalesced
single-beat writes, not a claim of multi-beat write aggregation. Invalidation
clears read-ahead validity but leaves accepted backing requests live until
their actual response retires, so the block cache cannot deadlock while
draining. Future speculative bytes do not expose uncommitted tokens.
Measurements must distinguish fetched bytes from useful consumed bytes.

## Global configuration, sequence and cancellation ownership

Configuration requests take priority over host requests, which take priority
over new tokens. Token acceptance requires a committed model, DDR readiness
and quiescent host, projection, KV and DDR services. Configuration changes
invalidate sequence, KV and coefficient-cache visibility. Host writes are
possible only with invalidated configuration and invalidate immutable
coefficient reads before subsequent inference.
Annul also discards an internal held descriptor-lookup response; otherwise
a canceled lookup could retain the single response slot and block the next
token's descriptor request. Public configuration responses are not discarded.

The sequencer enforces position, new-sequence and prefill/decode rules.
The prefill cursor advances only after a completed prefill token; the first
decode freezes it. K and V blocks are written for every head/block of a layer
and acknowledged before that layer's commit. No logit generation starts
before all layers have completed. `done` follows acceptance of the last
vocabulary logit, including vocabulary one.

Cancellation or any module fault generates a global annul pulse. It clears
compute validity, vector helper work and sequence/KV visibility without
resetting DDR ownership or contents. Every already-held Avalon command stays
live until acceptance; its recorded read/write owner drains its actual
responses. Completed host responses remain externally held until accepted.
The drain waits for fabric, both burst owners, coefficient readers, projection
and KV services, followed by registered settling edges. A canceled active
token receives one error completion; idle cancellation never invents one.
Repeated assertion while a cancel is pending does not multiply completions.
Once a drain-completion pulse is published, a subsequent cancel does not mask
it; a simultaneous fresh fault suppresses normal token completion in favor
of the single post-drain error completion.
No token/host/configuration request is accepted during cancellation/draining.

## Format boundaries

The conversion engine has E0 capture, E1 decode and E2 result registers.
Its common advance freezes payload/error/valid state under output blocking.
Integer normalization uses the existing bounded leading-zero tree; rounding
uses explicit retained/remainder/midpoint logic. Float-to-Q16 handles shifts
outside the useful range by exact zero or saturation, without oversized
variable shifts. FP16/BF16/FP32 nonfinite inputs are errors, not silently
saturated values.

Q16-to-FP16 nearest-even conversion is the explicit lossy boundary required
for integrated FP16 KV mode. It is distinct from the raw storage codec's
lossless 16-bit payload handling. BF16 norm/embedding/bias values and final
FP32 accumulations use their explicitly selected conversions, not FP16
reinterpretation. Independent verification of all rounding and subnormal
boundaries remains pending.

## Timing constraints

`design/anvil_q2_ht.sdc` defines the 10.0 ns application clock with setup/hold
uncertainties of 0.2/0.1 ns. Application inputs have external arrival bounds
0.2..2.0 ns; output receivers require 2.0 ns setup and 0.2 ns hold.
All application interfaces, including DDR-controller response signals and
bridge-facing request signals, belong to this clock domain. Physical PCIe
and DDR clocks and crossings terminate in the runtime-supplied platform, not
in a silently asynchronous HT application interface.

The external reset asserts asynchronously and must be deasserted synchronously
by the platform. Reset is constrained as an input rather than blanket
false-pathed through live control logic; reset recovery/removal and public
reset-qualified output paths remain visible to timing analysis. Payload RAM
contents/read registers are not reset, but all public validity and ownership
state is. No false-path or multicycle exception waives a functional endpoint.
These are integration constraints, not a claim of post-fit timing closure.

## Memory/control ownership required by integration

| Resource | Producer | Consumer | Release |
| --- | --- | --- | --- |
| Weight image | Host, only before commit | DDR prefetch | Configuration invalidation permits writes, not automatic erasure |
| Filling tile slot | Ordered DDR returns | Tile scheduler | Full response count, then registered ready transition |
| Executing tile slot | Scheduler | Tensor issue | Final accepted row issue and safe generation retirement |
| Array result | Arithmetic pipeline | Ordered row context | `m_valid && m_ready` |
| KV resident block | Successful backing write/read | Attention | Replacement only with authoritative backing data |
| Token visibility | KV commit | Later causal reads | Sequence invalidation/cancel/fault |

Tile-slot index wrap and queue wrap must compare explicitly against their
configured depth minus one. A simultaneous completion/issue may update both
ends but cannot reuse a slot before its registered ready state. A returned
beat is associated with the oldest accepted read command, never the currently
selected request. Cancellation is a drain operation, not a controller reset.

## Performance interpretation

128 lanes at 100 MHz give an analytical peak of 12.8 billion lane
multiplications per second, not measured throughput. A W4 row chunk contains
64 weight bytes; a BF16 row chunk contains 256 weight bytes. Full tiles contain
1024 W4 or 4096 BF16 weight bytes plus AWQ metadata where applicable.
Actual performance must include burst/service stalls, metadata, activation
reuse, tail masking, pipeline fill and row-context availability. Only real
execution can establish the required 75% read-beat utilization or speedup
against the supplied one/four-bank parent.

## Source and evidence discipline

Product commands and source paths are project-relative. Verification outputs
belong in fresh generated directories, never in `rtl/` or `tests/`.
Designer performs no functional simulation, numerical reference execution,
defect mutation or synthesis. The connected default top passed the fast
static command
`iverilog -g2012 -Wimplicit -s anvil_q2_ht_top -t null rtl/*.sv`
with Icarus Verilog 12.0, with no diagnostics. An earlier static elaboration
warned about an imported operation constant in an instance-port conditional;
an explicitly sized operation wire repairs that connection.
This is parsing/elaboration only: no numerical, synthesis or timing result
is implied. No functional or
synthesis preparation harness/receipt was authored. No product PDF is produced
before engineering acceptance.

The portable design source list is `rtl/*.sv`, `design/SPEC.md`,
`design/ARCHITECTURE.md` and `design/anvil_q2_ht.sdc`; parent comparisons
add the unchanged `anvil_q2_reference/rtl/*.sv`. The top has no dependency on
generated binaries, a private work directory or a previously rendered report.
From the project root, the independent Verifier-owned commands are
`python3 tests/verify.py --suite l1` and
`python3 tests/verify.py --suite portable-reproduction`. Their reference,
fixture, mutation, checkpoint-import and bridge sources are owned by Verifier,
not substituted by this design handoff. Full reproduction additionally needs
the declared genuine pinned checkpoint/configuration/license inputs in
`data/model/`, Python 3, Icarus/vvp, Verilator, Yosys, a C++ compiler, Quartus
17.1 and the runtime's hardware bridge. No tools are installed by this design.
