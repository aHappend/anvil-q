# Anvil-Q1 serialized architecture

The public protocol, exact arithmetic, AWQ unpack table and legal parameter
matrix are frozen in [SPEC.md](SPEC.md). This file describes their implementation.
Each token is processed by one reused decoder engine; no full-model arrays are
allocated. A parent exclusively routes its active child's memory transaction.
External scratch retains intermediate vectors, external KV retains committed
history, and external coefficients implement mathematical Qwen RoPE angles.

Required hierarchy: top -> decoder_layer + final rmsnorm; decoder_layer ->
rmsnorm, w4a16_gemv, rope, gqa_attention, swiglu_mlp; swiglu_mlp ->
w4a16_gemv; each GEMV -> awq_dequant. Shared helpers may implement arithmetic
and transaction control, but must not substitute host-computed results.

## Cycle and degenerate-boundary table

| Edge/event | Pre-edge sampling | Post-edge state |
| --- | --- | --- |
| rst_n=0 | All outward handshakes/status/payload zero | Synchronous state clear |
| E0 | Accept idle token/command | Busy, no request acceptance |
| E1 | Startup edge | First request permitted |
| R | Request valid && ready | Wait response, no second request |
| S, strictly after R | Response valid && ready | Consume data/ack or error |
| Output stall | Logit valid && !ready | Hold index and data |
| F | Final logit valid && ready | Commit position; one done pulse |
| Following edge | Completion retires | Return idle |
| Error completion | Invalid input or errored response | One done+error pulse |
| V=1 | First logit is last | Still wait for its F transfer |
| L=1 / SEQ=1 | First iteration is last | Perform it once |
| New sequence / reset | Invalidate logical history | Never reuse old cache |

Reset dominates all updates. No request and response can transfer on one edge.
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
Activation*W is signed 53-bit Q24; GEMV accumulates sign-extended products and
bias*65536 in signed 96 bits, then round-away shifts 16 and saturates to Q8.8.
The exact sum stays below 2^84 even for unsigned-32-bit input dimensions.
No signed-32-bit scale/dequant or signed-64-bit GEMV truncation is permitted.

Other reductions use 64 bits with widened scaling temporaries: unsigned 96-bit
RMS sum<<16 before dividing by H; wide attention score scaling before dividing
by floor(sqrt(D<<32)). RMS denominator uses floor integer sqrt and reciprocal
floor(2^32/denom); final triple product rounds by 24. Epsilon is 4295 Q32.32.
Logits accumulate Q8.8*Q8.8 into signed Q16.16 64-bit sums, then saturate 32.
RoPE products round by 30; residual additions saturate 16; SiLU rounds by 24
and its up product by 8. Every signed rounding is nearest, ties away from zero.
Binary16 ordinary data saturates Q8.8; nonfinite data is an explicit error.
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
bounded by 16777215, proving weighted sum <2^63. SiLU shares this exponential.
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
| Memory port | 0 idle -> 1 on issue; 1 -> 2 on request-ready; 2 -> 0 on response-valid. Complete/fault are qualified by state 2 and response-valid. Payload registers load only on issue in state 0. |
| GEMV | 0 accepts command -> 1, or 19 on invalid command. 1/3/5/7 issue activation/weight/zero/scale requests -> 2/4/6/8 respectively. Each response advances to the next issue, with 8 -> 9. State 9 checks dequant validity and adds one full 53-bit product -> 10. State 10 loops to 1 for another input; after last input selects QKV bias 11, otherwise output 13. Bias 11 request -> 12 response/check/add -> 13. Output 13 request -> 14 acknowledgement; 14 loops output channels or -> 20. 19 -> 20 -> 0. |
| RMSNorm | 0 -> 1 or invalid 14. 1 request -> 2 square-sum response; 2 loops components or -> 3 mean/epsilon -> 4 sqrt -> 5 reciprocal/check -> 6. 6 request x -> 7 response -> 8 request gamma -> 9 response/check -> 10 output request -> 11 acknowledgement. 11 loops to 6 or -> 15. 14 -> 15 -> 0. |
| RoPE | 0 -> 1 or invalid 14. States 1/3/5/7 request x/y/cos/sin -> 2/4/6/8 responses respectively. 8 -> 9 first rotated write -> 10 ack -> 11 second rotated write -> 12 ack. State 12 advances pair, head, then Q-to-K vector, or -> 15. 14 -> 15 -> 0. |
| Attention | 0 -> 1 or invalid 30. 1 scratch request -> 2 capture -> 3 cache write -> 4 ack; 4 loops components then K-to-V then -> 6. 6 Q request -> 7 response -> 8 K-cache request -> 9 dot response; 9 loops dimensions or -> 10 score -> 11. In max pass 11 updates max and loops time, then starts context pass. In context pass 11 evaluates exponential -> 12 denominator update -> 13 V-cache request -> 14 weighted response -> 15. State 15 loops time or -> 16 context write -> 17 acknowledgement. State 17 advances component, then head with new max pass, or -> 31. 30 -> 31 -> 0. |
| Elementwise | 0 -> 1 or invalid 14. 1 first-source request -> 2 response -> 3 second-source request -> 4 response -> 5 result write -> 6 acknowledgement. 6 loops vector or -> 15. 14 -> 15 -> 0. Mode 0 adds residual/O, mode 1 post residual/down, mode 2 SiLU(gate)*up. |
| MLP | 0 -> 1 or invalid 14. 1 gate-command accepted -> 2 completion; 2 -> 3 up launch -> 4 completion -> 5 SiLU/product launch -> 6 completion -> 7 down launch -> 8 completion -> 15. Each launch waits child ready and each completion waits child done; child error instead enters 15. 14 -> 15 -> 0. |
| Decoder | 0 -> 1 or invalid 4. 1 launches selected step when child ready -> 2; 2 waits done, advances step and returns 1, or -> 3 on last step/error. 4 -> 3 -> 0. Steps 0..10 are input norm,Q,K,V,RoPE,attention,O,residual,post norm,MLP,residual. |
| Top | 0 accepts valid token -> 1, invalid -> 30. 1 embedding request -> 2 conversion response -> 3 scratch write -> 4 ack. 4 loops components or -> 5 decoder launch -> 6 completion. 6 loops layers or -> 7 final norm launch -> 8 completion -> 9. 9 final-vector request -> 10 response -> 11 tied embedding request -> 12 conversion/MAC response -> 13. 13 loops components or -> 15 logit hold. State 15 advances vocabulary only on logit-ready; last transfer commits and enters 31. 30 -> 31 -> 0. Child error/nonfinite read/response fault enters 31 and invalidates sequence. |

Per output channel GEMV executes exactly input_dimension activation products and
one bias read only for Q/K/V, with four reads per input plus one output write.
RMSNorm executes H square terms, one mean, one square root, one reciprocal, then
H output triple products; square root is a 48-step combinational restoring
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
arithmetic stage completion. `anvil_q1_mem_port` and `anvil_q1_bus_mux` provide
single-outstanding service and exclusive child ownership; neither calculates
tensor arithmetic. `anvil_q1_elementwise` is the shared saturating residual/MLP
element helper and `anvil_q1_parameters` owns widened startup diagnostics.
