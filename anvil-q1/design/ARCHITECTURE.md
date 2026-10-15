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
