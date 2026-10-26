# Anvil-Q3 architecture

## Current implementation boundary

The current implementation connects the Q3 top, complete sequential decoder,
final norm and tied embedding/vocabulary path to the numerical foundation,
tagged bank scheduler and memory-backed tensor/ping-pong prefetch path.
RMSNorm, RoPE, residuals, SwiGLU and GQA execute in RTL. External KV ownership
and commit use per-layer counters and explicit stored-representation decoding.
These are source-level implementations awaiting independent verification,
not an accepted complete product. The portable FPGA subsystem and host/DDR
mapping are implemented under `fpga/`; physical board/IP integration remains
blocked on unidentified board, pinout and generated-IP prerequisites.
Parent reference files remain unchanged. No
simulation, synthesized resource estimate, timing closure or board result is
implied by these sources.

The implemented core hierarchy is:

```text
anvil_q3_top
  bank_scheduler
  decoder
    norm
    gemv
      tensor_array
        weight_prefetcher
        engines[g].dot8
    rope
    attention
      kv_cache
        cache_codec
    mlp
      silu_product
    residual
  final_norm
  token_io
```

The GEMV subtree is:

```text
anvil_q3_gemv
  tensor_array
    weight_prefetcher
      banks[g].storage
    engines[g].dot8
    engines[g].accumulator
  bias_accumulator
```

The MLP commands the decoder's shared GEMV for gate/up/down instead of
replicating the tensor path. The top connects BANKS+9 persistent scalar client
identities to the scheduler: BANKS+1 GEMV clients, norm, RoPE, two attention
clients, MLP elementwise, residual, final norm and token IO. Scheduler ingress
arbitration now evaluates all retiring clients before reusing a slot, including
the last client at QUEUE_DEPTH=1. This was repaired by source inspection, not
by a claimed functional experiment.

## Arithmetic mapping

Dot8 accepts eight activations and eight independently supplied FP16 scales.
At most 8*BANKS exact scalar products are accepted per unstalled cycle.
For BANKS=8 this is an architectural peak of 64 products/cycle, or 6.4 billion
products/second at the *target* 100 MHz, not an achieved rate. Treating a multiply
and add as two operations would double that count; no measurement is claimed.
One 128-by-128 output/input matrix needs 16,384 scalar products independent of
bank count. Fill/drain, accumulation interlocks, DMA and padding add cycles.

The E3 split multiplier treats the activation low half as unsigned16 (extended
with zero) and the high half as signed16. E4 sign-extends before shifting:
`product = low_partial + (high_partial << 16)`. This preserves INT32_MIN and
does not round group contributions. Subsequent registered pair reductions grow
by one bit per level to signed72.

The accumulator carries through eight 16-bit segments with interlocks.
The divider performs restoring long division, also with a registered
low-to-high 16-bit borrow per segment. The root unit uses the radix-four
digit recurrence with a 68-bit remainder candidate and 80-bit padded
segmented subtraction. None relies on a single-cycle 128-bit carry or
unrolled reciprocal/root chain.

Exp performs exact unsigned divisions of bounded nonnegative magnitudes before
restoring each series term's alternating sign. SiLU reuses that exp and a
separate segmented divider for the sigmoid quotient. Its final multiply is
registered before rounding. Neither unit contains an unrolled multi-term
combinational nonlinear calculation.

Scalar full-width multiplication uses registered 16-by-16 magnitude products,
one registered 16-bit carry segment per sum step, and segmented sign
restoration. It covers square, gamma/reciprocal, RoPE, attention, elementwise
and tied vocabulary products. The signed rounded divider similarly performs
magnitude, rounding-offset and sign formation in segments. RoPE subtraction
uses the segmented adder's complemented-B/carry1 mode, not a 128-bit
combinational negation. Final signed32 rounding uses a saturated-range guard,
an arithmetic shift and at most a signed33 increment; it does not negate a
full signed128 accumulator.

FP16 scale conversion has a bounded shift range (-8..21 for finite operands).
NaN/Inf and negative nonzero scales are rejected before their magnitude is used.
The maximum finite FP16 scale maps to 4292870144 unsigned Q16.16.
It must not saturate to INT32_MAX. A masked invalid lane is cleared before
conversion, so padding cannot poison an otherwise valid transaction.

## Storage and ownership

The dot8 owns stage registers from input acceptance to output retirement.
One global enable freezes all stages and their error bits together. Flush
clears all valid state independently of an output stall. Unused data registers
need not be reset or cleared: reset/invalid output gating makes them unobservable.

Scalar units snapshot accepted operands. Divider/root use fixed-size registers,
not operand-dependent elaboration or model-sized arrays. The accumulator
commits its internal running sum only on the final carry segment and retains
an output reservation until the consumer accepts it.

The weight prefetcher owns two physical tile sets per bank,
each indexed by immutable epoch/layer/projection/output-base/input-base/
valid-rows/valid-inputs descriptors. EMPTY -> FILLING -> READY -> ACTIVE
transitions require accepted transfers and complete response accounting.
Only ACTIVE storage feeds dot8, and only the other set may be filled. Each fill
client has at most one outstanding field request; its fixed reservation
selects the destination cell. The scheduler's tag match and per-client response
ordering are required before any returned data changes that FILLING set.
Cancellation drains accepted transactions rather than merely hiding them
with an epoch. The top couples core annulment to a scheduler flush and holds
the core flushed until drain_done. New-sequence invalidation uses the same
handshake before any embedding read. An epoch only advances when a new sequence
is accepted from idle with no scheduler work; wrapping cannot overlap old
accepted traffic. Faults invalidate sequence/cache ownership and use this
drain path before their one error completion.

The scheduler has QUEUE_DEPTH slots per bank, not a three-slot global queue
that would prevent full eight-bank occupancy at the default depth. It supports
independent bank issue/response, per-client in-order retirement, round-robin
ingress, explicit tag-wrap quiescence, and response faults. Returned data has
its own slot ownership under client backpressure. Read/write memory faults are
returned to the owning client, not silently dropped.

At default tile dimensions, the two sets consume
2*8*128*(4+4+16)/8 = 6144 logical bytes per bank, 49152 across eight banks.
Activation vectors are replicated per bank (8*11008*4 = 352256 logical bytes);
row partial sums consume 8*8*16 = 1024 logical bytes. These numbers exclude
pipeline/control registers, padding, inferred RAM granularity and replication
by implementation tools. They are source-level capacities, not fitted usage.

Each engine's activation copy is interleaved across eight reset-free synchronous
lane memories: logical component `8*word+lane` resides at `word` in that lane.
The default is eight 1376-by-32 memories per engine, preserving all 11008
components and independent bank copies. A load writes only its selected lane;
an accepted weight beat reads one word from each enabled lane. Tensor-generated
descriptor input bases and prefetch beat offsets are multiples of eight, so no
lane rotation or extra read port is needed. The registered read data and
resettable operand metadata capture on the same edge; the registered mask
zeros disabled lanes before dot8. Memory contents and read registers are not
reset. Resettable valid/control state prevents their use before a complete
activation load. No large-memory register-forcing attribute is used.

| Activation boundary/event | Pre-edge condition and post-edge effect |
| --- | --- |
| Reset / first released edge | Public outputs remain reset-gated; operand valid/mask reset to zero; no storage read/write during reset |
| Accepted load | Write component `load_index` to its lane and word; malformed last markers do not write |
| Final accepted load | Write the last component and activate compute; no beat is accepted from the previously inactive engine on that edge |
| Accepted beat at E0 | Synchronous lane reads and q/z/scale/row/input/mask capture together; operand valid asserts after E0 |
| Dot8 acceptance at E1 | Earliest dot8 consumption of E0's matched activation/metadata snapshot; no added pipeline stage |
| Operand stall | Read registers, mask and all operand metadata hold; no beat acceptance |
| Masked tail / smallest legal vector | Masked lanes supply zero without reading padding; eight-component vectors use the same mapping |
| Concurrent load/read | LOAD and active compute are disjoint; no legal read/write collision |
| Flush or local fault | Flush/fault control suppresses reads and invalidates operand ownership; retained RAM bits cannot become new work without a new complete load |

This inference-oriented repair addresses the activation-store register expansion
observed in the retained full-default synthesis timeout. It does not establish
that expansion was the sole timeout cause, successful RAM inference, resource
fit or timing closure; those require independent synthesis and physical checks.

Each fill presently reads one qweight word, one qzero word and one FP16 scale
transport word per logical tile cell. This intentionally simple correct-address
schedule repeats packed-word/scale reads: 12 bus bytes per cell, not the
theoretical compressed weight footprint. Two buffers permit overlap but do
not establish end-to-end speedup or efficient DDR utilization. Independent
benchmarks must include that real traffic and fill/drain cost.

The exact dot8 sum enters one segmented adder per bank. Eight-stage dot8
metadata freezes under the same global enable as arithmetic. Row sums are
not rounded per tile; same-edge retire/launch forwards the completed sum to
dependent work. Result backpressure can propagate through the adder and dot8
without overwriting an active buffer or dropping a result.

| Consumer assumption | Provider obligation |
| --- | --- |
| Fill response selects one immutable cell | Scheduler tag match/order plus single outstanding request per fill client |
| Tile data is immutable during compute | Prefetcher ACTIVE ownership until final accepted beat |
| Dot operands include all valid activations | Tensor command's exact-length load phase and registered operand snapshot |
| Partial dot sums remain exact | Segmented signed128 adder with overflow fault and same-edge forwarding |
| Projection completes after stored outputs | GEMV waits for every kind8 write acknowledgement |
| No old response can affect a new sequence | Top flushes all clients and awaits scheduler drain before recovery |

RMSNorm makes two memory passes over its input. It accumulates exact squares,
divides the shifted sum by H, adds the Q64 epsilon, takes an integer root and
computes the reciprocal through multicycle leaves. A second pass multiplies
the unchanged input, converted gamma and reciprocal before the single shift48.
It stores no model-sized norm array.

Attention commits the current token's full K/V before any causal reads.
Per-layer committed/prefill counts and decode flags are the only sequence-sized
ownership state: no layer-by-context validity bitmap is allocated. K and V
are independently gathered one head/block at a time. Incomplete final blocks
fetch only real components; zero padding is supplied to the codec and checked
again on decode. Every payload/metadata write must acknowledge before commit.
Any cache fault invalidates every layer's ownership.

A first score pass computes each query head's maximum; subsequent passes
compute one context component at a time. Recomputing scores trades latency and
memory traffic for bounded local state instead of storing a full context score
array. Dot, exponential and weighted sums have separate segmented signed128
accumulators. Both K and V explicitly traverse codec decode, even Mode0.
No host-computed activation or attention result enters this path.

Token IO serializes finite FP16 embedding reads into scratch0, then later
projects scratch14 against every tied embedding row with exact signed128
accumulation. Vocabulary logits hold their index/value under backpressure.
The final pre-edge accepted logit causes the top's successful done immediately
after that edge. PROFILE1's implicit reset-only empty sequence and ignored
phase are distinct from PROFILE2/3's explicit initialization; faults and
cancellation invalidate every profile and require explicit new_sequence.

External memory remains responsible for model, scratch and context capacity.
For full defaults, a hidden activation vector is 8192 bytes, an FFN vector
44032 bytes, and lossless per-token K+V across 36 layers is 73728 bytes.
At context 32768, lossless K+V is 2415919104 bytes. These are logical capacity
calculations, not allocated on-chip arrays or measured bus traffic. Compression
adds per-head block metadata and alignment. Logical cache coordinates are
implemented and specified in SPEC.md. Physical byte mapping and the host
register ABI are specified in `fpga/INTEGRATION.md`.

## FPGA subsystem and remaining prerequisites

`fpga/anvil_q3_fpga_shell.sv` connects the unchanged core to host control,
an external DDR bridge, reset release and two single-bit status synchronizers.
The host-control CSR slave reserves immutable token commands, exposes a
backpressured one-logit mailbox, records core completion/error pulses, and
provides cancellation without resetting outstanding memory ownership.
Model uploads must finish through the board DMA fabric before token launch.
No host-computed intermediate enters the decoder.

The memory bridge arbitrates all physical banks round-robin with one DDR
transaction outstanding. It retains the originating bank/tag through mapping,
DDR wait states, read/write acknowledgement and response backpressure.
Cancellation leaves the bridge alive so the scheduler can actually drain.
Malformed coordinates produce associated error responses without a DDR issue;
unsolicited DDR responses additionally request a sticky integration fault.
This conservative bridge preserves correctness/ownership but serializes
off-chip traffic. Neither high DDR throughput nor end-to-end speedup is claimed.

The mapper lays out only real tensor regions, aligned to 64 bytes, with
four-byte transport words and separate immutable/per-token/cache ownership.
Logical scratch bounds remain slot-specific despite rectangular allocation.
Address formation uses two registered partial-product multiplications and
three segmented additions, not a combinational 64-bit multiply/add chain.
The host layout utility describes exactly this ABI; it is not an independent
verification model. Combined allocation must fit unsigned64 and identified
physical DDR capacity before host configuration can enable a command.

`fpga/anvil_q3.qsf`, `fpga/anvil_q3.sdc`, `fpga/build.tcl` and the project
preparer supply portable device/project/clock constraints. Each build uses a
new retained subdirectory. A real pin-level board top, electrical constraints,
clock relationships and generated DDR4/PCIe QIP sources are mandatory inputs.
The build refuses their absence rather than fitting a virtual-pin shell or
stub endpoint. There is no fabricated pin assignment or IP black box.
No physical board model, pinout, generated IP or license has been established.
Public immutable model/RoPE data is permitted; host-computed intermediates
are not.

Independent Verifier work must still exercise every admitted matrix and
mutation, including partial-head A geometry, full Group-64 C geometry and
PROFILE1 startup behavior. Real Q1/Q4 baseline assets, actual Quartus/license
availability and physical board access remain unestablished. They cannot be
replaced by a wrapper, simulator or estimated timing.

## Retained preparation

The arithmetic foundation's earlier static elaboration is retained at
`evidence/preparation/static-foundation-ne79ala1/receipt.json`.
The connected tensor/control/codec increment statically elaborated with
Icarus Verilog 12.0, exit0, at
`evidence/preparation/static-tensor-p2caleg1/receipt.json`.
The latter selects the affine INT4 codec and the GEMV/scheduler/parameter/
arithmetic roots; it does not execute any testbench or time-zero diagnostic.
Those receipts cover only the earlier source versions, not the new connected
decoder/top. Both receipts are advisory source-bound syntax evidence, not independent
verification or physical acceptance. No failed functional probe was hidden
or repaired in this increment: no functional probe ran.

The connected 26-file core, including the official-default top and a separate
affine INT4 codec root, statically elaborated with Icarus Verilog 12.0, exit0:
`evidence/preparation/static-decoder-i5arxokj/receipt.json`.
This was one `-g2012 -t null` invocation, with no testbench, simulation,
time-zero parameter execution or synthesis. Its receipt hashes the actual
26 RTL inputs. It neither executes the A/B/C behavior matrices nor proves
that any configuration meets timing, fits a device or runs on hardware.

The subsequent portable FPGA integration statically elaborated with
Icarus Verilog 12.0, exit0:
`evidence/preparation/static-fpga-ylnsdi89/receipt.json`.
Its single invocation selects the official-default core plus the full-default
eight-bank affine INT4 FPGA shell and hashes all 31 SystemVerilog sources.
The two host/project Python files were parsed with `ast.parse` only, not run.
No simulation, synthesis, Quartus project preparation, STA or hardware
experiment was performed. No failed functional probe or repair is claimed.
The 26 core RTL sources and parent reference remain untouched by this
FPGA-only source increment.
