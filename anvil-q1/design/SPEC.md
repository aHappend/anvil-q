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

The authoritative configuration is `model_type=qwen2`,
`architectures=["Qwen2ForCausalLM"]`, activation SiLU and AWQ GEMM W4 G128
with zero points. The manifest covers 627 tensors and 168 quantized modules.
For each layer, Q/O have (N,M)=(896,896), K/V=(896,128),
gate/up=(896,4864), down=(4864,896). Storage is I32 qweight[N,M/8],
I32 qzeros[N/128,M/8], F16 scales[N/128,M]; only Q/K/V have F16 bias[M].
The independent Verifier must validate all manifest entries, not infer them
from the partial slice. All 24 layers and the tied vocabulary projection
execute in RTL, without sliding-window truncation or host arithmetic.

The supplied Layer-0 Q/K/gate qweight excerpts are input rows 0..7 and packed
output columns 0..7 (logical channels 0..63). Their zero excerpts cover groups
0..6, packed columns 0..7. Q/K scale excerpts cover groups 0..6 and scalar
channels 0..7; gate scales cover only groups 0..5 and scalar channels 0..7.
Q/K biases, Layer-0 input norm and final model norm cover components 0..7.
Thus weight/zero availability for 64 channels does not imply matching supplied
scales for 64 channels. V/O/up/down, other components/groups and padded
integration data are synthetic unless separately supplied.

## Cycle and degenerate-boundary table

All transfers sample **pre-edge** valid and ready. State changes are post-edge.
Reset is synchronous active low, with combinational gating of outward signals.
The combinational dequantizer has no reset and always evaluates its inputs.

| Event | Pre-edge | Immediately post-edge |
| --- | --- | --- |
| Reset asserted | All outward valid/ready/done/error and payloads zero | Rising edge clears state and sequence validity |
| First deasserted idle cycle | token_ready/cmd_ready high | No state change absent a transfer |
| E0 command/token acceptance | valid && ready | Busy, ready low, no completion or request transfer |
| E1 | Busy startup; GEMV tile-clear state 16 | First request may become valid; GEMV enters zero-request state 5 |
| Stalled request | valid && !ready | All request fields unchanged |
| R request transfer | req_valid && req_ready | req_valid low, rsp_ready high |
| S response transfer, S > R | rsp_valid && rsp_ready | rsp_ready low; dependent operation advances |
| GEMV packed-weight S | State 4 accepts packed word | Enter MAC state 9; next edge performs all eight lane MACs and selects next input/group/completion path |
| Stalled logit | valid && !ready | Index and data unchanged |
| F final logit transfer | valid && ready | One-cycle done, ready remains low; commit position |
| Completion retirement | done high | Return idle next edge |
| Error | Invalid accepted command or response error | Invalid command first enters pending error, never completion immediately after E0; then one-cycle done+error and idle |
| Singleton vocabulary | First logit is also last | Same F rule, never skip its transfer |
| Singleton context/layer | Index zero is also final | Execute the operation once, then terminate |
| New sequence accepted | position must be zero | Old logical cache invalidated; storage need not erase |
| Reset during transaction | Reset has priority | Forget outstanding work; memory integration discards obsolete response |

There are no simultaneous master requests or overlapping outstanding responses.
Writes also require responses. An errored response stops the active operation.
Top-level memory errors invalidate sequence state; a new-sequence position-zero
token is required. Invalid tokens cause no memory writes or logits and do not
change committed sequence state. Busy valid inputs are not accepted.
Position must equal the next committed position, initially zero. Token ID must
be below V and position below SEQ, without wrapping. `new_sequence` is sampled
only on acceptance and requires position zero. Only the final logit transfer
commits the position; readiness stays low until completion retires. Any child
error, memory error or nonfinite required model value stops further requests
and logits and invalidates the sequence. Acknowledged writes are not rolled
back and transferred logits are not retractable, but neither constitutes a
successfully completed token. Valid bubbles do nothing.

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

Internal response-data isolation does not change this public interface.
Each bus mux forwards response data only to its selected child, driving zero
to the others. Each memory-port helper exposes data only on its existing
response transfer (`complete`); no response is registered or delayed.
GEMV alone uses a direct request/response FSM instead of that helper, exposing
read data only during an accepted response in its response-wait states.
Response-dependent arithmetic operands are zero outside their consuming
response states: top binary16 conversion in states 2/12 and logit multiply
in 12, RMSNorm square in 2, attention K-dot in 9 and V-weighted product in 14,
and GEMV binary16 bias conversion in 12. Valid consuming data, including X/Z
bits, is not sanitized; response errors retain their existing priority.
Standalone engines retain the same behavior without a parent mux.
The consuming-state isolation itself adds no clock gating, storage or protocol
cycles. The separate GEMV amendment instantiates eight arithmetic lanes and
removes helper request staging only within GEMV, preserving transaction order,
counts and numerical results; it makes no measured speedup claim.

Top ports remain `clk,rst_n,token_valid,token_ready,token_id[31:0],
token_pos[31:0],new_sequence,logit_valid,logit_ready,logit_index[31:0],
signed logit_data[31:0],done,error` and the memory interface.
Each memory master outputs `mem_req_valid,mem_req_write,mem_req_kind[3:0],
mem_req_layer[31:0],mem_req_proj[2:0],mem_req_row[31:0],
mem_req_col[31:0],mem_req_wdata[31:0],mem_rsp_ready` and receives
`mem_req_ready,mem_rsp_valid,mem_rsp_rdata[31:0],mem_rsp_error`.
Read write-data is zero; every accepted read or write gets one strictly later
response. Clocked children use `cmd_valid,cmd_ready,cmd_layer[31:0],
cmd_pos[31:0],done,error` with the same memory interface; GEMV additionally
uses `cmd_proj[2:0]` and RMSNorm `cmd_mode[1:0]`. Reserved projection/mode
and invalid layer/position fail before any memory effects.

Scratch slots: residual 0, input norm 1, Q 2, K 3, V 4, attention context 5,
O 6, post-attention residual 7, post norm 8, gate 9, up 10,
SiLU(gate)*up 11, down 12, reserved 13, final norm 14.
Tensor nonquantized reads use low-halfword IEEE binary16; scratch/cache use
all 32 bits as signed Q16.16; coefficients are signed Q2.30. This intentionally
replaces the former low-halfword Q8.8 working encoding with no legacy mode.
Packed model words and binary16 model tensors are not rewritten.
GEMV source->target slots are Q 1->2, K 1->3, V 1->4, O 5->6,
gate 8->9, up 8->10, down 11->12. RMS modes 0,1,2 select
0->1/input norm, 7->8/post norm and 0->14/final norm respectively.
RoPE updates Q/K; attention caches rotated K and unrotated V and writes context.

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
At 0x6c00, deltas +/-8 give +/-2147483648 and +/-7 give +/-1879048192;
0x77ff with +/-1 gives +/-2146435072; 0x7800 with +/-1 gives +/-2147483648.
These are full signed-37 values, not signed-32 aliases.

RMS epsilon is 1e-6 with fixed integer round(1e-6*2^64)=18446744073710.
The mean uses a widened unsigned temporary before shifting; the square root is
a bounded 64-iteration restoring algorithm. D>0 by epsilon; zero is nonetheless
an explicit error. R<2^43 and the output triple product has magnitude <2^105.
Qwen RoPE pairs i and i+HEAD_DIM/2, theta=1000000. The external memory provisions
independent rounded Q2.30 cos(position*theta^(-2*i/HEAD_DIM)) and sine,
clipped only to the coefficient representation.
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

Process consecutive output blocks of eight with exactly eight actually
instantiated `anvil_q1_awq_dequant` children, each fixed to its logical lane,
and eight explicitly signed-69 products feeding eight signed-128 accumulators.
This architecture is identical across legal parameter configurations; it is
neither eight scalar iterations nor wrappers around a shared scalar result.
Each block clears the accumulators. At each input group load one packed zero
word and eight binary16 scales in lane order; retain only this group's metadata.
For each increasing input index read one activation and one packed weight,
then perform all eight lane MACs on one following edge without intermediate
rounding/saturation. Any invalid dequantizer fails the operation without
accepting any lane's MAC result. Reload metadata on arithmetic
group transitions, including G=3. After all inputs, read/add one bias per lane
only for Q/K/V and write eight final values in channel order, waiting for each
acknowledgement. O and all MLP projections never request bias.

All tile state is command-local and invalid on reset, completion, rejection or
fault. For N inputs and M outputs there are exactly N*M scalar products through
(M/8)*N parallel MAC edges, M writes and
(M/8)*(2*N+9*(N/G)) reads, plus M reads for biased projections. Eight
accumulators, eight scales, eight combinational lane datapaths and fixed holds
are independent of model/context dimensions. No group-count-sized metadata
array is allocated. The four-token B analytical input/metadata count remains
183680, excluding biases, writes and other engines. The amendment preserves
public transaction order and counts; this is not a measured speedup or
completion-time bound.

GEMV request-valid derives directly from request state, with no helper issue
or request-register stage. Payloads derive only from held command/index/data,
stay stable while valid && !ready, and zero unused fields/read write-data.
Write data selects the stable completed accumulator, with final rounding and
saturation enabled only in write-request state 13. Request states never assert
response-ready, and response-wait states never assert request-valid. A request
transfer always enters response wait; only a strictly later response transfer
advances work. This applies equally to writes. No speculative request,
response-driven combinational request, same-edge request/response transfer or
unacknowledged write is allowed. Response data is zero outside an accepted
response in a wait state; active consuming data, including X/Z, is unchanged.
Other engines retain `anvil_q1_mem_port` staging and selected-child isolation.

## Parameter boundary matrix

All dimensions are positive unsigned-32-bit quantities; all address products
must fit unsigned 32 bits using widened checks. H=QH*D; QH divisible by KVH;
D even; H and I divisible by G; H,I,KVH*D divisible by eight; bits=4.
SEQ <= 16777215 retains the admitted softmax denominator bound. Unsupported
values require an explicit startup diagnostic before command acceptance.
Widened unsigned-128 calculations bound V*H (embedding), H*H, H*I and
H*KVH*D (projection entries), L*SEQ*KVH*D (cache), SEQ*D and 2*D
(RoPE), and 15*H and 15*I (scratch) by 4294967295.
Zero group/head divisors are guarded for diagnostic-only elaboration; they
are never substituted as legal parameter values or used to clamp commands.

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
All A/B/C/D cases require seeds 17,43,89, unchanged stimulus distributions,
exact stage/cache/logit integer comparisons and public-pin reference arithmetic.
Quality limits remain exponential absolute error <=3e-5; isolated nonsaturating
RMSNorm/RoPE/SiLU/attention error <=2/256 real units; final norm <=16/256;
logits <=16/256+0.01*abs(floating reference). These are not new-format LSB
counts. Prior Q8.8-directed working inputs preserve real values by multiplying
their integer encodings by 256. Full-range saturation and cancellation cases
use exact integer expectations. All nine retained mutations (wrong AWQ lane,
omitted QKV bias, wrong GQA association, wrong RoPE pairing/coefficient use,
stale/future cache indexing, skipped decoder layer, signed-32 dequant
truncation, signed-64 GEMV accumulation truncation and signed-53 product
truncation), protocol/fault
coverage, actual Yosys zero-latch checks and Icarus 12/13 remain required.
Retain the existing 25-second matrix simulation and 120-second complete-check
budgets. Missing Icarus13 remains an external unmet prerequisite, not a waiver.
Engineering acceptance remains INCOMPLETE until all applicable obligations
close. Verifier first establishes actual four-token B17 completion with the
existing matrix probe and unchanged 25-second simulation watchdog, linked to
`evidence/preparation/verifier-response-isolation-B17-01/receipt.json`.
Predicted arithmetic quality, transaction progress and static elaboration do
not certify that completion. New parallel-lane synthesis must independently
check eight connected dequantizers and lane-result consumption in each concrete
GEMV, not merely presence of the dequantizer module type. Historical scalar
synthesis cannot certify the amendment.

The concrete state-transition conditions and arithmetic iteration counts in
[ARCHITECTURE.md, Concrete state transition and iteration inventory](ARCHITECTURE.md#concrete-state-transition-and-iteration-inventory)
are part of this contract. They specify each issue/response state and each
component/head/group/layer/vocabulary loop rather than promising a fixed token
latency independent of memory backpressure.

GEMV freezes these transitions: 0 acceptance -> 16 tile initialization, or 19
invalid-command pending. State 16 clears tile state -> 5. Request states
5,7,1,3,11,13 advance only on mem_req_valid && mem_req_ready to response-wait
states 6,8,2,4,12,14 respectively. State 6 captures zero -> 7. State 8
validates/captures scale and advances lane -> 7, or after lane 7 resets lane
-> 1. State 2 captures activation -> 3. State 4 captures packed weight -> 9.
State 9 performs all eight MACs on one edge and directly increments k and
selects 1 within a group or 5 on a group transition; after the final input,
lane zero and 11 for QKV or 13 otherwise. No input-advance state 10 remains.
State 12 validates/converts/adds bias, loops 11 for next lane or resets lane
-> 13. State 14 acknowledges output and selects 13 for next lane, 16 with
incremented output block and reset input/lane, or completion 20. State 19
-> 20; state 20 invalidates tile state -> 0. Reset dominates all transitions.
Any accepted response error in a wait state takes priority over normal
capture/progression and enters failed completion 20, with no subsequent request.
Invalid scale/bias or any invalid dequantizer likewise fails. Completion lasts
one cycle. Thus there are N*M products on (M/8)*N parallel MAC edges, eight
accumulator clears per block and nine metadata reads per group/block.

RMSNorm transitions are 0 -> 1/2 H square reads -> 3 mean -> 4 bounded
64-step combinational sqrt -> 5 checked reciprocal -> 6/7 x read -> 8/9
gamma read/check -> 10/11 write/ack. Repeat the output loop H times, then
15 completion -> 0; invalid commands use 14->15. The square-root loop is
combinational, not 64 artificial wait cycles.

Unchanged RoPE iterates (QH+KVH)*D/2 pairs, with x/y/cos/sin reads and two
acknowledged writes per pair. Attention caches 2*KVH*D components and, per
query head, computes (position+1) D-product dots for max, then that many dots
for each of D context components, with six-term exponentials and complete
normalized weighted division. No context-sized score array is allocated.
Elementwise loops H residual additions or I SiLU/products. MLP launches/waits
gate, up, elementwise, down; decoder launches/waits input norm, Q,K,V,RoPE,
attention,O,residual,post norm,MLP,residual. Top embeds H components, invokes
each of L layers, final norm and V*H tied output products. Every launch waits
child ready, every retirement waits done, and every memory loop waits the
strictly later response. The sole V=1 logit still transfers before commitment.
