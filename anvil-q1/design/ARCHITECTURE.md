# Anvil-Q1 serialized architecture

The public protocol, exact arithmetic, AWQ unpack table and legal parameter
matrix are frozen in [SPEC.md](SPEC.md). This file describes their implementation.
Each token is processed by one reused decoder engine; no full-model arrays are
allocated. A parent exclusively routes its active child's memory transaction.
External scratch retains intermediate vectors, external KV retains committed
history, and external coefficients implement mathematical Qwen RoPE angles.

Response data is routed only to the selected child at each bus mux; unselected
children receive zero. The memory-port helper exposes read data only during
its existing response transfer (`complete`, state 2 and response-valid).
Neither isolation point changes request/response valid, ready or error routing.
On an active response, data bits, including X/Z, pass through unchanged.
Standalone engines retain response-transfer qualification without depending on
a parent mux. GEMV implements it directly in its response-wait states rather
than instantiating the memory-port helper. The helper and all other engines'
transaction staging remain unchanged; no clock gating is introduced.

Response-dependent arithmetic has separate consuming-state operand isolation:
top converts binary16 only on its state-2 embedding or state-12 tied-weight
response and enables logit multiplication operands only on state 12; each
RMSNorm squares response data only in state 2; attention feeds K to its dot
product only on the state-9 response and V to its weighted product only on
state 14; GEMV converts bias only on state 12. Other response types, including
write acknowledgements, cannot toggle those arithmetic inputs with their data.
All consuming edges, arithmetic widths, rounding, transaction counts and error
priority remain unchanged. This removes avoidable inactive-data fanout; it is
not a measured execution-time improvement. Following the eight-lane amendment,
independent B17 four-token completion must first be established against the
unchanged 25-second simulation watchdog, linked to
`evidence/preparation/verifier-response-isolation-B17-01/receipt.json`, before
the remaining seeds and complete 120-second checks can establish coverage.
Engineering acceptance remains INCOMPLETE, including the independently unmet
Icarus13 prerequisite; static elaboration does not establish acceptance.

Required hierarchy: top -> decoder_layer + final rmsnorm; decoder_layer ->
rmsnorm, w4a16_gemv, rope, gqa_attention, swiglu_mlp; swiglu_mlp ->
w4a16_gemv; each GEMV -> eight instantiated awq_dequant children. Shared helpers may implement arithmetic
and transaction control, but must not substitute host-computed results.

## Cycle and degenerate-boundary table

| Edge/event | Pre-edge sampling | Post-edge state |
| --- | --- | --- |
| rst_n=0 | All outward handshakes/status/payload zero | Synchronous state clear |
| Idle after reset deassertion | token_ready or cmd_ready high | Remain idle absent valid |
| E0 | Accept idle token/command | Busy, no request acceptance |
| E1 | Startup edge; GEMV state 16 clears tile | First request permitted; GEMV presents zero request in state 5 |
| Request stall | Request valid && !ready | Every request payload stable |
| R | Request valid && ready | Wait response, no second request |
| S, strictly after R | Response valid && ready | Consume data/ack or error |
| GEMV packed-weight S | State 4 accepts packed word | Enter state 9; next edge updates all eight accumulators and selects next input/group/completion path |
| Output stall | Logit valid && !ready | Hold index and data |
| F | Final logit valid && ready | Commit position; one done pulse, ready low |
| Following edge | Completion retires | Return idle |
| Error completion | Invalid input or errored response | One done+error pulse, never immediately after E0 |
| V=1 | First logit is last | Still wait for its F transfer |
| L=1 / SEQ=1 | First iteration is last | Perform it once |
| New sequence / reset | Invalidate logical history | Never reuse old cache |

Reset dominates all updates. R drops request-valid and asserts response-ready;
S drops response-ready, and may present the next request only after that edge.
No request and response can transfer on one edge.
No simultaneous read/write is supported; every write waits for acknowledgement.
Non-power-of-two groups and contexts use arithmetic division and comparisons,
never bit-mask wrap. See SPEC for invalid-token versus memory-error recovery.

## AWQ lane table

| lane | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nibble index | 0 | 4 | 1 | 5 | 2 | 6 | 3 | 7 |
| bit shift | 0 | 16 | 4 | 20 | 8 | 24 | 12 | 28 |

## Arithmetic implementation boundaries

Scale S is unsigned 32 bits (max 4292870144), explicitly nonnegative when
extended into signed multiplication. Delta is signed in [-15,15]. Exact W is
signed 37-bit Q21.16 despite its historical port name `weight_q16_16`.
Activation*W is signed 69-bit Q32; GEMV accumulates sign-extended products and
bias*65536 in signed 128 bits, then round-away shifts 16 and saturates to Q16.16.
The exact sum stays below 2^100 even for unsigned-32-bit input dimensions.
No signed-32-bit scale/dequant or signed-64-bit GEMV truncation is permitted.

RMS accumulates squares in unsigned 96 bits and forms
M=floor((T<<32)/H)+18446744073710 in unsigned 128 bits (Q64.64).
Its 64-step restoring sqrt gives unsigned-64 Q32.32 D; R=floor(2^64/D)
uses a numerator wider than 64 bits. The signed-128 triple product rounds by 48.
Attention dots, scores and weighted sums are signed 96 bits; scores divide
the Q32 dot directly by floor(sqrt(Dimension<<32)). A signed-97 max difference
is clipped before narrowing for exp. Weighted division uses the full sum.
Logits use signed-64 Q32 products and signed-96 sums, then round by 16 and
saturate signed 32. RoPE has signed-64 products and signed-65 sums, rounded
by 30; residual additions use signed 33 bits. SiLU rounds by 24 and its up
product by 16. Every signed rounding is nearest, ties away from zero, with
129-bit unsigned magnitude/carry temporaries for signed-128 helper inputs.
Binary16 ordinary data saturates Q16.16; nonfinite data is an explicit error.
Working scratch/cache use all 32 bits, without a legacy Q8.8 mode.
Scale conversion has its separate unsaturated rule, including subnormal ties.
Binary16 exponent arithmetic explicitly zero-extends the five-bit exponent to
32 bits before applying `$signed` and subtracting the fixed-point exponent
offset. This preserves the nonnegative exponent and signed shift calculation
without the `integer'(...)` cast syntax rejected by the Yosys 0.33 frontend.
The same form is used in the package conversions and standalone dequantizer;
mantissa widths, subnormal handling, rounding and output widths are unchanged.

Softmax uses max subtraction and the six-term Q0.24 range-reduced exponential
defined in SPEC (LN2=11629080, cutoff -16). Context uses the entire nonzero
exponential sum, signed weighted accumulation and rounded division. SEQ is
bounded by 16777215, proving weighted sum magnitude <2^79 and denominator
<2^48. Zero divisors explicitly fail operations. SiLU shares this exponential.
RoPE coefficient provisioning uses theta=1000000 and split-half pairing.

## Parameter matrix and integration

| Case | L,H,I,QH,KVH,D,G,V,SEQ |
| --- | --- |
| Default | 24,896,4864,14,2,64,128,151936,32768 |
| A | 2,16,32,4,2,4,8,17,4 |
| B | 2,112,128,14,2,8,16,19,3 |
| C | 1,24,48,6,2,4,3,11,3 |
| D | 1,8,8,2,2,4,8,1,1 |

Reject zero/overflow dimensions, odd D, H != QH*D, nonintegral GQA ratio,
nondividing group, non-eight-aligned packed channels, bits !=4, address-product
overflow and SEQ>16777215. Widen checks themselves to prevent wrapped approval.
Legal grouping need not be a power of two.
Address-product checks use unsigned 128 bits: V*H, H*H, H*I, H*KVH*D,
L*SEQ*KVH*D, SEQ*D, 2*D, 15*H and 15*I must fit unsigned 32 bits.
Zero dimensions, odd D, head mismatch, bad GQA ratio, nondividing G, bits!=4,
overflow and excessive sequence length are illegal, with explicit diagnostics.

Compile design inputs as `rtl/*.sv` in SystemVerilog-2012 mode, using package
source first where required. Standalone clocked engines accept cmd_valid/ready
and return done/error; top accepts token_valid/ready and streams ordered logits.
After reset submit token position zero; subsequent positions must be consecutive.
To restart or recover from a memory error submit new_sequence with position zero.
The memory service must acknowledge writes and provision all immutable model and
RoPE values; it must never calculate missing accelerator outputs.

No independent checks or full-checkpoint inference results are claimed by this
document. The independent Verifier owns all behavioral/synthesis harnesses and
actual executable/version records. Advisory lessons exp-6d5cc92e6f5a86894eaae275
(meaningful parameter rejection) and exp-652f89e7783eeb1726867f05 (reachable
singleton coverage) motivate boundaries, not evidence of current correctness.

## Concrete state transition and iteration inventory

States below are the numeric state registers in the corresponding RTL files.
All unspecified states recover to idle. Reset takes priority over every listed
transition. Any active transaction fault takes priority over normal completion,
sets failure and enters the completion state. Completion lasts exactly one
cycle and unconditionally returns idle. For a rejected command, an intermediate
error-pending state preserves the required no-completion-immediately-after-E0
interval. A nonfinite tensor read is an operation error, not a successful zero.

| Engine | State transitions and conditions |
| --- | --- |
| Memory port (engines other than GEMV) | 0 idle -> 1 on issue; 1 -> 2 on request-ready; 2 -> 0 on response-valid. Complete/fault are qualified by state 2 and response-valid. Read data passes through only when complete; otherwise zero. Payload registers load only on issue in state 0. |
| GEMV | 0 accepts command -> 16 tile initialization, or 19 invalid-command pending. 16 clears tile state -> 5. Request states 5/7/1/3/11/13 advance only on request-valid && request-ready to response-wait states 6/8/2/4/12/14 respectively. State 6 captures zero -> 7. State 8 validates/captures scale and advances lane -> 7, or after lane 7 resets lane -> 1. State 2 captures activation -> 3. State 4 captures packed weight -> 9. State 9 checks all eight dequantizers and performs eight parallel MACs on one edge, directly increments k and selects 1 within group or 5 at a group boundary; after final input, lane zero and 11 for QKV or 13 otherwise. No state-10 advance bubble remains. State 12 validates/converts/adds bias, selects next lane -> 11 or resets lane -> 13. State 14 acknowledges output, selects next lane -> 13, next output block with k/lane reset -> 16, or completion 20. State 19 -> 20; state 20 invalidates tile state -> 0. Any accepted response error has priority over capture/progression and enters failed completion 20 without another request; invalid scale/bias or any invalid dequantizer likewise fails. |
| RMSNorm | 0 -> 1 or invalid 14. 1 request -> 2 square-sum response; 2 loops components or -> 3 mean/epsilon -> 4 sqrt -> 5 reciprocal/check -> 6. 6 request x -> 7 response -> 8 request gamma -> 9 response/check -> 10 output request -> 11 acknowledgement. 11 loops to 6 or -> 15. 14 -> 15 -> 0. |
| RoPE | 0 -> 1 or invalid 14. States 1/3/5/7 request x/y/cos/sin -> 2/4/6/8 responses respectively. 8 -> 9 first rotated write -> 10 ack -> 11 second rotated write -> 12 ack. State 12 advances pair, head, then Q-to-K vector, or -> 15. 14 -> 15 -> 0. |
| Attention | 0 -> 1 or invalid 30. 1 scratch request -> 2 capture -> 3 cache write -> 4 ack; 4 loops components then K-to-V then -> 6. 6 Q request -> 7 response -> 8 K-cache request -> 9 dot response; 9 loops dimensions or -> 10 score -> 11. In max pass 11 updates max and loops time, then starts context pass. In context pass 11 evaluates exponential -> 12 denominator update -> 13 V-cache request -> 14 weighted response -> 15. State 15 loops time or -> 16 context write -> 17 acknowledgement. State 17 advances component, then head with new max pass, or -> 31. 30 -> 31 -> 0. |
| Elementwise | 0 -> 1 or invalid 14. 1 first-source request -> 2 response -> 3 second-source request -> 4 response -> 5 result write -> 6 acknowledgement. 6 loops vector or -> 15. 14 -> 15 -> 0. Mode 0 adds residual/O, mode 1 post residual/down, mode 2 SiLU(gate)*up. |
| MLP | 0 -> 1 or invalid 14. 1 gate-command accepted -> 2 completion; 2 -> 3 up launch -> 4 completion -> 5 SiLU/product launch -> 6 completion -> 7 down launch -> 8 completion -> 15. Each launch waits child ready and each completion waits child done; child error instead enters 15. 14 -> 15 -> 0. |
| Decoder | 0 -> 1 or invalid 4. 1 launches selected step when child ready -> 2; 2 waits done, advances step and returns 1, or -> 3 on last step/error. 4 -> 3 -> 0. Steps 0..10 are input norm,Q,K,V,RoPE,attention,O,residual,post norm,MLP,residual. |
| Top | 0 accepts valid token -> 1, invalid -> 30. 1 embedding request -> 2 conversion response -> 3 scratch write -> 4 ack. 4 loops components or -> 5 decoder launch -> 6 completion. 6 loops layers or -> 7 final norm launch -> 8 completion -> 9. 9 final-vector request -> 10 response -> 11 tied embedding request -> 12 conversion/MAC response -> 13. 13 loops components or -> 15 logit hold. State 15 advances vocabulary only on logit-ready; last transfer commits and enters 31. 30 -> 31 -> 0. Child error/nonfinite read/response fault enters 31 and invalidates sequence. |

GEMV uses exactly eight combinational dequantizers and explicitly signed-69
products feeding eight signed-128 accumulators. Each child has a constant
logical lane 0..7 and its own current-group scale. Every legal configuration
uses this same architecture, not a configuration-specific scalar shortcut.
Per block, each input group fetches one packed zero and eight scales in lane
order; each increasing input fetches one activation and one packed weight.
One following MAC edge accumulates all eight products in parallel and chooses
the next input/group/completion path on that edge. Per-lane accumulation order
remains increasing input index, without intermediate rounding or saturation.
After the last input, all eight QKV biases are added before any final write.
O/MLP request no bias; eight outputs are written in channel order with an
acknowledgement for each. Exactly N*M scalar products through (M/8)*N parallel
MAC edges, (M/8)*(2*N+9*(N/G)) input/metadata reads, M optional
QKV bias reads and M acknowledged writes occur. Group comparison uses division,
not a power-of-two mask. Metadata is logically invalidated at every command
boundary, reset and error. Eight accumulators, eight scales, eight combinational
lane datapaths and fixed holding/control registers are bounded independently
of model dimensions; no activation/group/context-sized arrays are added.
For the retained four-token B workload, analytical input/metadata reads remain
183680, excluding biases, writes and other engines. Public transaction order
and counts are unchanged by the parallel-MAC/direct-handshake amendment.
Neither this count nor fewer arithmetic/request-launch edges proves completion
within the unchanged execution budgets.

Only GEMV replaces helper issue/register/request staging with direct requests.
Request-valid derives solely from request state; payloads derive from held
command/index/data registers, with read write-data and unused fields zero.
No index or accumulator changes while its request is stalled. Final output
rounding/saturation is enabled only in write-request state 13, selecting a
stable completed accumulator. Request states never assert response-ready;
response-wait states never assert request-valid. Accepted requests always wait
for a strictly later response, including write acknowledgements. Data passes
through only on a real response transfer; bias conversion additionally requires
state 12. Consuming X/Z is not sanitized. No speculative request, same-edge
request/response transfer or response-driven combinational request is permitted.
RMSNorm executes H square terms, one mean, one square root, one reciprocal, then
H output triple products; square root is a 64-step combinational restoring
integer algorithm, without multipliers or data-dependent iteration count.
RoPE executes (QH+KVH)*D/2 pair rotations, four reads and two writes per pair.
Attention writes 2*KVH*D cache elements. Per Q head, it computes (position+1)
dots for max, then (position+1) dots for each of D output components. Each dot
has D product iterations. Recomputing scores avoids a default-context array;
this deliberately trades memory traffic for bounded internal storage.
Every exp evaluation has exactly six polynomial terms, not six clock delays.
Elementwise executes H residual additions or I SiLU/products. Top computes
V*H tied output products after all L real decoder invocations.

Each memory transaction's latency is actual issue/request-stall/response-stall
progress, not a free-running delay counter. Square-root and polynomial loops
are combinational arithmetic structures; no clock latency is inferred from a
source-level for-loop. All state waits depend on public handshakes or actual
arithmetic stage completion. `anvil_q1_mem_port` (outside GEMV), GEMV's direct
FSM and `anvil_q1_bus_mux` provide single-outstanding service and exclusive
child ownership; the transaction helper and mux calculate no tensor arithmetic.
`anvil_q1_elementwise` is the shared saturating residual/MLP
element helper and `anvil_q1_parameters` owns widened startup diagnostics.
