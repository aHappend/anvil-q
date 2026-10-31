# Native HT2 architecture

## Implementation ledger

This is a partial Designer increment, not a connected accelerator or acceptance
report. The source files describe implemented leaves only; absent integration is
not a software fallback or a waived requirement.

The intended path is DDR response ownership -> broadcast weight registers ->
four-slot native projection array -> FP32 residual/operator storage ->
causal provisional-KV decoder -> tree verifier -> atomic commit.
Every learned projection must traverse one shared set of weights for all active
slots. Four serial decoder calls do not implement this architecture.

### Saved source increment

| Source stem under `rtl/` | Implemented structure |
|---|---|
| anvil_q1_ht2_00_fp_pkg | Integer-significand RNE packing, gradual-underflow conversions, classification, AWQ permutation |
| anvil_q1_ht2_reset_sync | Asynchronous assertion and two-edge synchronized domain release |
| anvil_q1_ht2_parameters | Diagnostic-only legal-geometry checker |
| anvil_q1_ht2_fp16_mul | Three registered stages for BF16/FP16 to FP32 product |
| anvil_q1_ht2_fp32_mul | Three registered stages for separately rounded FP32 multiplication |
| anvil_q1_ht2_fp32_add | Capture, align/jam, add/subtract, normalize/round stages |
| anvil_q1_ht2_mac_lane | Four contexts, shared add reduction and equal-edge result forwarding |
| anvil_q1_ht2_tile_batch_mac | Four slots times64 lanes, fixed transaction masks, protocol-error drain |
| anvil_q1_ht2_dequant | AWQ nibble mapping, signed difference, FP16 scale product and BF16 boundary |
| anvil_q1_ht2_fp32_divsqrt | 27 bounded quotient/root iterations, remainder sticky, separate final round |
| anvil_q1_ht2_fp32_exp | Frozen range reduction and degree12 Horner sequencer using separate FP32 units |
| anvil_q1_ht2_sparse_dma | Registered predicate, exact byte-end validation, one-request DMA ownership |
| anvil_q1_ht2_spec_verifier | Registered bounded tree walk, lowest-child selection and correction mask |

These are source structures, not independently verified numerical or timing
claims. Arithmetic pipeline reset inputs are the containing domain's synchronized
reset; public transaction leaves instantiate their own release synchronizer.
Divide/sqrt and exp use `enable` only for execution advances; a visible response
is consumed by `rsp_valid && rsp_ready` even when execution enable is low.
Dequantization globally stalls its operand/product/error metadata stages when
its final response is blocked. It accepts a new word on each enabled advance.

The array accepts consecutive column beats with no imposed input bubble.
Input bubbles advance valid/tag pipelines but not the accepted logical-column
counter. Output backpressure freezes the completed result, not a new dot.
Missing first, repeated first and changed transaction configuration produce an
error after a bounded pipeline drain. An open transaction has no invented
wall-clock timeout: missing last is observable on a conflicting next first,
and reset cancels an otherwise abandoned transaction.

## Boundaries and dependencies

| Producer / consumer | Ownership and requirement |
|---|---|
| DDR / core | Explicit reset-safe request ownership; acknowledged full-width CDC |
| Weight buffers / MAC | 64 broadcast 16-bit weights per column, two BF16 DDR beats; fixed slot/lane mask per dot |
| MAC / projection | Four FP32 contexts per slot/lane, logical-column phase preserved through skipped reads |
| SwiGLU / sparse DMA | BF16 magnitudes for predicate plus separately retained original-nonzero state |
| Sparse DMA / projection | Decision cannot imply approximation safety; nonzero skips require dense replay |
| Decoder / KV | Prefix+ancestor visibility; rejected branches never own committed entries |
| Decoder / verifier | Node targets come from actual native forward passes; prefix target cached internally |
| Commit / counters | Count tokens/steps only on the accepted atomic result |
| CSR / image | Mutations interlocked with execution/loading/pending results; format invalidates image/prefix |

The MAC uses spatial slot/lane replication (4*64 multipliers), not time-multiplexed
token invocations. FP32 accumulation is separately rounded, with four contexts
to cover four-stage add feedback and explicit same-edge retirement forwarding.
Global enabled advances move operand/product/tag stages together; output stalls
hold ownership. A skipped physical burst still retains its logical-column
arithmetic/context event, or requires an equivalent independently verified phase
mechanism; removing reads must never reorder the dense reduction.

## Outstanding integration

High-precision sin/cos reduction and polynomial sequencing, array integration,
native decoder, provisional/committed KV,
CSR/image installation, sparse replay, reset-safe DDR ownership and compatibility
timing repairs must be completed before a ready handoff. No scalar Q16 decoder
is used as a temporary HT2 top. Verifier-owned tooling and all runtime-native
hardware/performance evidence remain pending.

The theoretical array peak at 100MHz is 25.6 billion separately rounded products/s.
This is not measured throughput. Four token slots alone prove neither accepted
reuse>=3.2 nor TPM>=8000. Rejected/corrective/replay traversals, metadata, wall
time and actual accepted DDR response bytes all remain charged.

## Claim-to-evidence index

There are no functional, synthesis, timing, board or benchmark results in this
Designer increment. Independent Verifier must author and execute the mandatory
commands in SPEC. The runtime alone may approve engineering delivery and produce
the final product PDF afterward.

The first static-only parse attempt is retained at
`evidence/preparation/static-elaboration-20261031T161949Z-a192ef87/receipt.json`.
It failed because `large` and `small` were used as identifiers in the FP32 adder;
those Verilog strength keywords were renamed to `larger_operand` and
`smaller_operand`. This was a parser repair, not a functional experiment.
The repaired static-only elaboration exited zero; its argv, source hashes,
version output and raw logs are retained at
`evidence/preparation/static-elaboration-20261031T162050Z-039c8ae5/receipt.json`.
It parsed all saved RTL roots, not the unfinished native top. This establishes
no behavioral, synthesis, timing or performance result.
