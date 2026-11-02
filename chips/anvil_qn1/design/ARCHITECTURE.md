# Anvil-QN1 architecture and implementation inventory

## Current state

This is an incomplete Designer implementation, not a verified accelerator.
Native mathematical, streaming, controller, CSR, memory scheduler, GEMV,
ordinary normalization, attention, MLP and residual engines are saved.
The native decoder and `anvil_qn1_top` are not yet present. The saved engines
are not connected into an end-to-end accelerator.
No native end-to-end inference, fusion overhead, synthesis, timing, PPA or HIL
result is claimed. Acceptance requirements remain those in SPEC.md.

Static-only preparation:
`evidence/preparation/native-static-20261102T173854Z-4ee1c61b/receipt.json`
retains the initial exit-zero compilation and its epsilon port-width warning.
Explicit package qualification repaired that warning. The same compilation
command then exited zero without diagnostics in
`evidence/preparation/native-static-20261102T173924Z-9cb9d6cc/receipt.json`,
which links the original receipt. Both record byte-identical parent copies.
The roots checked were tensor_array, qknorm_rope, dual_think_ctrl, csr_perf and
parameters, not a native top. No functional simulation or synthesis was run.

The subsequent static-only elaboration of all saved engine roots exited zero
without diagnostics using Icarus 12.0:
`evidence/preparation/memory-arithmetic-static-20261102T175050Z-a28f1429/receipt.json`.
It records the exact command, source hashes, tool output, settled child and
byte-identical parent copies. This is not a simulation or synthesis result,
and no native top was compiled.

The parent consists of 26 original SystemVerilog files in
`anvil_q3_reference/rtl/`. Copies in `rtl/anvil_q3_*.sv` preserve their bytes,
interfaces and FP16/Q16 semantics. Never compile both trees together.
`design/GENERATIONAL_HANDOFF.md` was not supplied. Historical Quartus timing and
PPA cannot be reconstructed or claimed from intake.

## Saved native source inventory

| Source/module | Responsibility |
|---|---|
| anvil_qn1_00_pkg.sv / anvil_qn1_pkg | IEEE encodings, RN packing, jam shifts, AWQ mapping, elaboration predicate, bounded counter carry |
| anvil_qn1_parameters.sv | Intentional illegal-configuration diagnostic |
| anvil_qn1_fp32_mul.sv | Four registered computation stages, finite binary32 product |
| anvil_qn1_fp32_add.sv | Five registered computation stages, finite binary32 sum/subtraction |
| anvil_qn1_fp32_sqrt.sv | Registered restoring square root, fixed 34 computation edges |
| anvil_qn1_fp32_div.sv | Registered restoring division, fixed 34 computation edges |
| anvil_qn1_tensor_array.sv | Real 256-lane W4A16/BF16-weight balanced reduction |
| anvil_qn1_qknorm_rope.sv | Per-head RMSNorm and split-half RoPE without external intermediate writeback |
| anvil_qn1_dual_think_ctrl.sv | Token-first tree verification, marker/capacity cutoff and held batch publication |
| anvil_qn1_csr_perf.sv | Counters, coherent snapshot, mode requests and host reference registers |
| anvil_qn1_scalar.sv | Owned, held-response binary32 add/subtract/multiply/divide/sqrt service |
| anvil_qn1_bank_scheduler.sv | Buffered bank requests, tagged response association, cancellation/fault drain |
| anvil_qn1_gemv.sv | Group/weight/activation gathering and ascending-tile binary32 accumulation |
| anvil_qn1_exp.sv | Exact represented-value range reduction and registered six-term E evaluation |
| anvil_qn1_silu.sv | Registered E, numerator/denominator arithmetic and BF16 SiLU boundary |
| anvil_qn1_rmsnorm.sv | Stream-captured hidden RMSNorm with synchronous local storage and balanced sum |
| anvil_qn1_norm_memory.sv | Acknowledged scratch/gamma ingress and final normalized scratch writes |
| anvil_qn1_attention.sv | Causal GQA, exact head reduction, two-pass external-cache softmax and context |
| anvil_qn1_mlp.sv | Gate/up/down command orchestration and real BF16 SiLU-times-up scratch computation |
| anvil_qn1_elementwise.sv | Acknowledged BF16 residual additions |
| anvil_qn1_head_buffer.sv | Two ordered projected-head buffers feeding the fused leaf without raw writeback |

The private arithmetic helpers have clock enable for streaming pipelines and
flush for annulment. A four-stage helper computes from pre-edge operands on
four enabled edges; its first operand-processing register is not an extra
public transaction-capture register. The tensor wrapper captures at edge n,
then executes 48 computation edges. Add/multiply error bits traverse the same
registers as their values. Invalid finite operations return zero with error,
not a successful saturation or infinity.

Multiplier stages are normalized operand extraction, 24-bit significand
multiply, product/exponent normalization, and gradual-underflow RN packing.
Adder stages are magnitude ordering/unpack, sticky alignment, signed
significand addition, leading-zero normalization, and RN packing. Square root
uses 27 restoring radix-four input-pair iterations. Division forms 26 fractional
quotient bits after the leading one, retaining remainder sticky information.
Both finish rounding internally and publish through their final fixed-latency
register; no combinational divide, floating `real` or simulator math is used.
These register placements are design intent, not established Arria 10 timing.

## Streaming datapaths

The tensor array captures active lanes, masks inactive inputs before arithmetic,
forms delta*scale (or 1*BF16-weight) in four stages, multiplies activations in
four stages and reduces through eight five-stage adjacent-pair add levels.
All 256 lanes have dynamic operands. Tags and valids have the same 48-interval
latency. A stalled output freezes the entire pipeline using a synchronous
clock enable, not a gated clock. The array can accept one independent tile per
cycle when its output is ready.

The fused head block owns one complete head and associated gamma/coefficient
vectors. Its 128-leaf sum tree pads smaller heads with positive zero, preserving
the 35-edge sum alignment. A separate mean register implements exact power-of-
two exponent scaling with IEEE rounding. Root and reciprocal use restoring
arithmetic. Each lane then crosses the specified u and normalized BF16
boundaries. Four products per split-half pair feed separate binary32 rotation
adders. Only the final rounded head becomes externally visible. Registered
output ownership holds all metadata and result/error through backpressure.
Position zero selects identity coefficients; invalid positions or payloads
produce an error-marked, zero-data head at the same 133-interval latency.

The two-buffer projected-head frontend captures complete heads in FIFO order.
Each head retains its own Q/K designation, gamma, coefficients, layer and
position. A fused-leaf ingress transfer releases that raw buffer, allowing
projection to fill it while the leaf owns a different head. A following K
projection may be configured after Q ingress finishes even if Q heads are
still queued. Only final fused outputs may be written externally. The decoder
must connect this frontend directly to its named qknorm_rope instance and
arbitrate final scratch/KV writes alongside projection traffic. The buffers
exist, but that overlap/integration is still outstanding.

## Saved memory and numerical engines

The bank scheduler owns QUEUE_DEPTH slots per bank. Each slot transitions
through free, buffered request, accepted request and returned response.
An independently registered issue owner pins each stalled bank payload.
Responses match the stored 64-bit request tag and bank, including a valid
same-edge request/response transfer. Completed scalar responses move into a
held client response register; bank completion order need not be issue order.
Client tags are returned without reinterpretation.

External tags come from a configuration-initialized, nonwrapping serial
counter which survives host reset. Reset annuls ownership without reusing a
pre-reset tag; late pre-reset responses therefore cannot match new work.
Cancellation and detected faults suppress new traffic, discard unaccepted
requests/returned responses and drain accepted requests. Unknown responses do
not release unrelated ownership. The scheduler exposes fault and drained,
but top-level sequence invalidation, cancellation completion and recovery
remain unimplemented. FPGA configuration initializes the serial once;
the external memory bridge must share the device-configuration lifecycle.

GEMV gathers zero/scale groups first, then active activation/weight lanes.
Response tags select lane/type independently of bank order. AWQ zero and
weight words use the parent eight-row nibble shifts. Scratch requests use
layer/projection zero; AWQ requests use the real layer/projection, and tied-LM
requests use layer/projection zero. Masked tails do not issue scalar requests.
The shared-array interface supplies all 256 dynamic lanes and one tile tag;
the returned partial is added to a binary32 accumulator in ascending input
tile order, starting at positive zero. Projection row results are held and
BF16-rounded. Tied-LM row results remain binary32. No bias request exists.
GEMV currently waits for one tile result before gathering its next tile;
no one-tile-per-cycle projection throughput is claimed.

Ordinary norm uses synchronous raw/gamma RAM and a synchronous binary32 heap
tree. It squares coordinates, initializes padded leaves to positive zero and
computes adjacent balanced sums without reassociation. A scalar arithmetic
service executes division, epsilon, square root, reciprocal and the separate
BF16 x-scale/gamma boundaries. RAM writes/read registers have no asynchronous
reset; reset ownership gates all use of their uninitialized contents. Its
memory wrapper holds every normalized output until its scratch write response
has acknowledged. Residuals similarly read both BF16 inputs, add in binary32,
round to BF16 and await the destination write response.

E range reduction repeatedly subtracts the exact integer significand of L
from an exactly aligned input magnitude; it never floors a rounded quotient.
The following multiple, residual, six Taylor terms, ordered sums, clamp and
binary scaling use the specified RN32 boundaries. SiLU has its own BF16
output boundary. MLP requests real gate/up/down GEMVs from the decoder's
shared service and computes BF16 SiLU-gate times up before down projection.
It does not contain a supplied-result oracle; its command service still needs
the decoder connection.

Attention owns one query head, one K/V head and HEAD_DIM binary32 numerator
storage. It scans positions 0 through the commanded input position once to
find the maximum and again to evaluate deterministic E and accumulate
denominator/weighted values in increasing position order. Re-reading external
K avoids MAX_SEQ_LEN-sized local score storage. The head dot tree has exactly
HEAD_DIM leaves, not an extra 256-lane reduction that could alter signed zero.
Score events come from actual completed binary32 dot/scale arithmetic. Context
division and BF16 rounding produce a held, ascending-coordinate output stream.
The caller must establish acknowledged current/accepted-path KV and fence its
visibility; the attention leaf cannot create or certify cache ownership.

## Controller and integration obligations

The controller starts a nonterminal transaction with a root backend request.
It waits for the root response, then selects the effective mode after committed
input-marker observation. Direct mode publishes the root prediction without
draft acceptance. Thinking mode accepts exactly one validated four-node-or-less
tree. Only a greedy-matching child causes another backend context request;
off-path nodes are not evaluated. A correction, leaf bonus, marker or capacity
boundary finishes the generated batch. Publication additionally waits on
publish_ready, then holds all commit fields until transfer.

Backend requests are registered states and require accepted outstanding
ownership for responses. The backend must compute real contexts and must not
respond until the corresponding full public frame has transferred. Parent 4
means root; another parent names the accepted draft context to evaluate.
The controller's start interface is internal, not an extra public top port.
Top must start it only for nonterminal decode and independently orchestrate
prefill, terminal materialization, cancellation, sequence validity, and pending
deferred-token ID/position. Backend errors and illegal drafts must cause top
sequence invalidation and memory drain. The controller does not itself own
external KV or claim that a memory write has settled.

The CSR block samples request payload/busy/mode on acceptance, executes it on
the following edge and holds one response. Top must arbitrate idle
configuration before a simultaneous token start; an accepted control operation
has priority. Snapshot/clear actions remain available during work without mode
changes. Mode pulses configure the controller; marker changes remain owned by
the controller. Live counters are incremented in bounded 16-bit carry chunks.
Snapshot banks capture pre-edge state atomically. Generated token classification
must use the mode immediately before commit, not a resubmitted deferred token.

Required final literal hierarchy:

```text
anvil_qn1_top
  decoder
    tensor_array
    qknorm_rope
    attention
    mlp
  dual_think_ctrl
  csr_perf
  bank_scheduler
```

Attention, MLP and bank scheduler sources now exist, but the named decoder and
all required hierarchy connections are still to be implemented. Merely
wrapping the legacy decoder would be incorrect:
its Q extents, FP16/Q16 arithmetic, bias behavior, context limit and cache
protocol are different.

## Memory ownership and quantitative design constraints

Weights and committed KV are external. The tied matrix requires
2*VOCAB_SIZE*HIDDEN_SIZE payload bytes (native BF16, excluding transport
padding). Committed KV requires
2 kinds * layers * positions * KV_DIM * 2 payload bytes, but that is not an
on-chip allocation. The banked interface transports a scalar in a 32-bit word.
Scratch coordinate meanings and dimensions are fixed in SPEC.md.

For one projection, useful work is input_extent*output_extent products.
The compute-only tile lower bound is
ceil(input_extent/256)*output_extent accepted tensor vectors plus pipeline and
ordered accumulator service; this is analytical, not measured throughput.
Single-token decoding cannot achieve one useful tile per cycle unless memory
and accumulation sustain it. Q/K normalization must overlap projection and
other required layer work to satisfy the strict measured <2% fusion overhead.
No memory delay, padded reference or omitted vocabulary work may manufacture
that comparison.

Sequence/cache ownership must distinguish: committed extent, the root input
under evaluation, accepted evaluated ancestors, and the final deferred token.
Cache publication must await every required write response. Because the
controller follows only the greedy accepted path, rejected siblings require no
reachable committed KV; future implementation must still fence all staged
state until batch publication and invalidate on cancel/error. Bounded local
speculative storage may cover at most four draft nodes.

## Remaining Designer work

Implement embedding/tied-LM token-I/O orchestration and the named decoder/native
top. Connect the existing memory engines and 256-lane array, load Q/K gamma and
RoPE coefficients once per layer/position, overlap buffered Q/K capture and
fusion with continued projection, and acknowledge final scratch/KV publication.
Wire complete logit frames/argmax responses, deferred-token continuation,
accepted-path cache ownership, cancellation/fault drain, all real CSR events
and every production/compact parameter guard. Complete integration
documentation, then perform at most a fast static elaboration and hand off to
independent Verifier. Do not create verification models or simulation/synthesis
harnesses as Designer.
