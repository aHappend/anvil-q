# Anvil-Q1 implementation contract

## Scope and integration

The implementation targets `Qwen/Qwen2.5-0.5B-Instruct-AWQ` using the immutable
`hf_qwen25_05b_awq_spec/*.json` inputs. This is a serialized functional accelerator
core, not a physical chip, DRAM controller, throughput claim or demonstrated
full-checkpoint inference. The external memory service supplies model tensors,
scratch, persistent KV storage and mathematical RoPE coefficients. It must not
replace accelerator arithmetic. Tokenization and sampling are outside the core.

Defaults: 24 layers, hidden 896, intermediate 4864, 14 query heads, 2 KV heads,
head dimension 64, group 128, AWQ bits 4, vocabulary 151936, context 32768.
Use all seven quantized projections per layer, Q/K/V biases only, two decoder
residuals, two per-layer RMSNorms and final RMSNorm. Execution ties embedding and
output projection storage because configuration says `tie_word_embeddings=true`.
The manifest lists both embedding and lm_head; this does not establish equality
of unavailable full tensors. The Layer-0 slice contains partial real data only;
unsupplied integration tensors and padding must be explicitly synthetic.

## Cycle and degenerate-boundary table

All transfers sample **pre-edge** valid and ready. State changes are post-edge.
Reset is synchronous active low, with combinational gating of outward signals.
The combinational dequantizer has no reset and always evaluates its inputs.

| Event | Pre-edge | Immediately post-edge |
| --- | --- | --- |
| Reset asserted | All outward valid/ready/done/error and payloads zero | Rising edge clears state and sequence validity |
| First deasserted idle cycle | token_ready/cmd_ready high | No state change absent a transfer |
| E0 command/token acceptance | valid && ready | Busy, ready low, no completion or request transfer |
| E1 | Busy startup | First request may become valid |
| Stalled request | valid && !ready | All request fields unchanged |
| R request transfer | req_valid && req_ready | req_valid low, rsp_ready high |
| S response transfer, S > R | rsp_valid && rsp_ready | rsp_ready low; dependent operation advances |
| Stalled logit | valid && !ready | Index and data unchanged |
| F final logit transfer | valid && ready | One-cycle done, ready remains low; commit position |
| Completion retirement | done high | Return idle next edge |
| Error | Invalid accepted command or response error | One-cycle done+error, then idle |
| Singleton vocabulary | First logit is also last | Same F rule, never skip its transfer |
| Singleton context/layer | Index zero is also final | Execute the operation once, then terminate |
| New sequence accepted | position must be zero | Old logical cache invalidated; storage need not erase |
| Reset during transaction | Reset has priority | Forget outstanding work; memory integration discards obsolete response |

There are no simultaneous master requests or overlapping outstanding responses.
Writes also require responses. An errored response stops the active operation.
Top-level memory errors invalidate sequence state; a new-sequence position-zero
token is required. Invalid tokens cause no memory writes or logits and do not
change committed sequence state. Busy valid inputs are not accepted.

## Public memory and scratch contract

Every master uses the admitted `mem_req_*`/`mem_rsp_*` interface with a single
outstanding transaction. Kinds: 0 embedding, 1 qweight, 2 qzeros, 3 scales,
4 QKV bias, 5 input norm, 6 post norm, 7 final norm, 8 scratch, 9 K cache,
10 V cache, 11 RoPE. Only kinds 8,9,10 are writable. Unused fields are zero.
Projection codes are Q=0,K=1,V=2,O=3,gate=4,up=5,down=6; 7 is invalid.
Embedding addresses are row=vocabulary index, col=hidden index. Packed tensors
use row=input index (qweight) or group index (zeros/scales), and col=packed word
or scalar scale channel. Norm/bias use row zero. Cache uses layer, row=position,
col=flattened KV component. Scratch uses row=slot, col=component.
RoPE uses row=position and col=2*pair+cos/sin selector, pair local to a head.

Scratch slots: residual 0, input norm 1, Q 2, K 3, V 4, attention context 5,
O 6, post-attention residual 7, post norm 8, gate 9, up 10,
SiLU(gate)*up 11, down 12, reserved 13, final norm 14.
Tensor nonquantized reads use low-halfword IEEE binary16; scratch/cache use
all 32 bits as signed Q16.16; coefficients are signed Q2.30. This intentionally
replaces the former low-halfword Q8.8 working encoding with no legacy mode.
Packed model words and binary16 model tensors are not rewritten.

## Numerical widths and boundaries

| Quantity | Representation / rule |
| --- | --- |
| Activations, residuals, biases, cache, norm coefficients | signed 32-bit Q16.16 |
| Ordinary binary16 conversion | nearest, ties away, saturate signed 32; nonfinite error |
| Scale conversion S | unsigned 32-bit round-away(scale*65536), max 4292870144 |
| Dequantized W | signed 37-bit Q21.16, exact delta*S, max magnitude 64393052160 |
| Activation times W | explicitly signed 69-bit product, 32 fractional bits |
| GEMV accumulation | signed 128-bit; combined sum magnitude <2^100 |
| Bias contribution | converted Q16.16 integer multiplied by 65536 into Q32 sum |
| GEMV output | round-away by 16 bits, saturate signed-32 Q16.16 |
| Logits | signed-64 products, signed-96 Q32 sum, magnitude <2^94; round by 16, saturate signed 32 |
| RMS square sum T | unsigned 96 bits, T<2^94 |
| RMS mean M | floor((T<<32)/H)+18446744073710, unsigned-128 Q64.64 |
| RMS denominator D / reciprocal R | floor_integer_sqrt(M), then floor(2^64/D), unsigned-64 Q32.32 |
| RMS output | signed-128 x*gamma*R, round-away by 48, saturate signed-32 Q16.16 |
| RoPE rotation | signed-64 products, signed-65 sums/differences; round by 30, saturate signed 32 |
| Attention dots / scores | signed-96 Q32 dot; round-away(dot/Dscale), signed-96 Q16.16 score |
| Attention weighted sum | signed 96 bits, magnitude <2^79; complete rounded division, saturate signed 32 |
| Residual / elementwise results | signed-33 addition / signed-64 multiplication; round product by 16, saturate signed 32 |

Rounding helpers use unsigned magnitude/sign arithmetic and a carry bit beyond
their signed-128 operands. Saturation occurs only at declared output boundaries,
never on linear products or partial reductions. Division by zero is an explicit
operation error; callers guard denominators before using division results.
The working range is [-32768,32768-2^-16].

Finite nonnegative AWQ scales are never rejected or saturated for old signed
32-bit limits. Negative zero is zero. Negative nonzero scales and nonfinite
scales assert invalid and return zero; GEMV must error rather than consume it.
Subnormals round by the same rule (including half-LSB ties), not unconditional
flush. No GPTQ +1 adjustment is permitted.

| Logical output lane | Nibble index | Bit shift |
| --- | --- | --- |
| 0 | 0 | 0 |
| 1 | 4 | 16 |
| 2 | 1 | 4 |
| 3 | 5 | 20 |
| 4 | 2 | 8 |
| 5 | 6 | 24 |
| 6 | 3 | 12 |
| 7 | 7 | 28 |

Both packed words preserve the I32 bit pattern. The equation is
`(u4_weight-u4_zero)*round_away(binary16_scale*65536)`.
For scale 0x6c00 and delta 15 the full result is 4026531840; for 0x7bff
and delta 15 it is 64393052160. Negative deltas produce exact negatives.

RMS epsilon is 1e-6 with fixed integer round(1e-6*2^64)=18446744073710.
The mean uses a widened unsigned temporary before shifting; the square root is
a bounded 64-iteration restoring algorithm. D>0 by epsilon; zero is nonetheless
an explicit error. R<2^43 and the output triple product has magnitude <2^105.
Qwen RoPE pairs i and
i+HEAD_DIM/2, theta=1000000. The external memory provisions independent rounded
Q2.30 cosine/sine coefficients for position and pair.
GQA maps h to floor(h/(QH/KVH)); attention includes positions zero through
current position only. Scale is floor(sqrt(HEAD_DIM<<32)) in Q16.16.
Score division uses nearest, ties away from zero on the complete dot integer,
without an extra left shift. Max subtraction uses signed 97 bits and clips
against the -16 cutoff before narrowing for the exponential. Softmax is
max-subtracted, with normalized full exponential sum. Its unsigned-64
denominator is <2^48 and must be nonzero.

The shared exponential for nonpositive Q16.16 x returns zero below -16;
otherwise u=(-x)<<8 is Q0.24, n=floor(u/11629080), r=u-n*11629080.
Starting term=2^24, evaluate six terms
`term_j=trunc_zero(-term_(j-1)*r/(j*2^24))`; shift their nonnegative sum
right by n. SiLU uses this E at -abs(x): sigmoid is floor(2^48/(2^24+E))
for nonnegative x, floor((E<<24)/(2^24+E)) otherwise. Round x*sigmoid
by 24 bits, then round SiLU*up by 16 bits, saturating each Q16.16 boundary.
The SiLU exponential receives -abs(x) directly in Q16.16.

## Bounded eight-output GEMV

Process consecutive output blocks of eight with one reused scalar dequantizer
and multiplier, not eight parallel arithmetic lanes. Each block clears eight
signed-128 accumulators. At each input group load one packed zero word and
eight binary16 scales; retain only this group's metadata. For each increasing
input index read one activation and one packed weight, then perform eight
scalar lane MACs without intermediate rounding. Reload metadata on arithmetic
group transitions, including G=3. After all inputs, read/add one bias per lane
only for Q/K/V and write eight final values in channel order, waiting for each
acknowledgement. O and all MLP projections never request bias.

All tile state is command-local and invalid on reset, completion, rejection or
fault. For N inputs and M outputs there are exactly N*M products, M writes and
(M/8)*(2*N+9*(N/G)) reads, plus M reads for biased projections. Eight
accumulators, eight scales and scalar holds are independent of model/context
dimensions. The four-token B analytical input/metadata count is 183680 versus
2293760 previously; this is not a measured speedup or completion-time bound.

## Parameter boundary matrix

All dimensions are positive unsigned-32-bit quantities; all address products
must fit unsigned 32 bits using widened checks. H=QH*D; QH divisible by KVH;
D even; H and I divisible by G; H,I,KVH*D divisible by eight; bits=4.
SEQ <= 16777215 retains the admitted softmax denominator bound. Unsupported
values require an explicit startup diagnostic before command acceptance.

| Configuration | L,H,I,QH,KVH,D,G,V,SEQ | Intended boundary |
| --- | --- | --- |
| Default | 24,896,4864,14,2,64,128,151936,32768 | Complete model dimensions |
| A | 2,16,32,4,2,4,8,17,4 | Two layers and retained cache |
| B | 2,112,128,14,2,8,16,19,3 | 7:1 GQA |
| C | 1,24,48,6,2,4,3,11,3 | Non-power-of-two groups/context |
| D | 1,8,8,2,2,4,8,1,1 | First/last logit coincide |
| Invalid | zero dimension, odd D, H mismatch, bad ratio | Explicit rejection |
| Invalid | nondividing G, bits != 4 | Explicit rejection |
| Invalid | cache/embedding/projection address overflow | Explicit rejection |
| Invalid | SEQ > 16777215 | Explicit rejection |

No default-sized activation or cache arrays may be instantiated internally.
Verification sources are independently owned `tests/*.py`; generated harnesses
and evidence are not RTL inputs. Functional, numerical, mutation, zero-latch
synthesis and both Icarus-major portability acceptance remain independent work.

The concrete state-transition conditions and arithmetic iteration counts in
[ARCHITECTURE.md, Concrete state transition and iteration inventory](ARCHITECTURE.md#concrete-state-transition-and-iteration-inventory)
are part of this contract. They specify each issue/response state and each
component/head/group/layer/vocabulary loop rather than promising a fixed token
latency independent of memory backpressure.
