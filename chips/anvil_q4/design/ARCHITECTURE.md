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
division. Each shadow write temporarily closes the configuration interface
until its derived validity is current. Thus accepting a commit needs no
variable-latency validation: its response and activation occur after the next
edge, matching SPEC.md.

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

## Source inventory and incomplete integration

This is a partial implementation handoff, not a complete accelerator.

| Source | Status |
|---|---|
| `rtl/anvil_q4_descriptor.sv` | Shadow/active descriptor controller and mode-specific validation |
| `rtl/anvil_q4_bank_scheduler.sv` | Tagged, runtime-bank, semantic-coordinate scheduler |
| `rtl/anvil_q4_00_fp_pkg.sv` | Synthesizable integer-bit FP representation, rounding, conversion and ordering helpers |
| `rtl/anvil_q4_fp32.sv` | Single-issue registered FP leaf, including iterative division and square root |
| `rtl/anvil_q4_dequant.sv` | Scalar native/W4/W8 lane dequantization through the actual FP leaf |
| `anvil_q3_reference/rtl/*.sv` | Unchanged architectural reference; not shipped Q4 dependencies |
| Q4 exp/SiLU, tensor array and decoder stages | Not yet implemented |
| `anvil_q4_top` and speculation | Not yet implemented |
| Runtime-configurable legacy datapath | Not yet implemented |
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
Per-tile A8 scale calculation and lane orchestration remain tensor-array work.

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

Current partial-source static elaboration, from the delivered root:

```
iverilog -g2012 -t null rtl/anvil_q4_00_fp_pkg.sv rtl/anvil_q4_bank_scheduler.sv rtl/anvil_q4_descriptor.sv rtl/anvil_q4_fp32.sv rtl/anvil_q4_dequant.sv
```

These are syntax/elaboration commands only, not simulations or acceptance.
The independently owned eventual portable L1 entry points remain
`python3 tests/verify.py --suite smoke|arithmetic|system|compatibility|benchmarks|mutations|synthesis|portable`;
the script is not supplied in this partial design increment.

Claim-to-evidence mapping is intentionally empty for numerical correctness,
synthesis, timing and hardware until those tools actually execute under their
assigned ownership. The Designer handoff reports any static diagnostic
separately. Do not treat this inventory as completed acceptance.
