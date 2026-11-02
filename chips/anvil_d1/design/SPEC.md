# Anvil-D1 v1.0.0-deepseek-mla-moe

## Authority and implementation status

The admitted work order defines the product. This document fixes implementation
details within that contract; it does not waive any acceptance check.

The current source increment implements native arithmetic primitives, native
RMSNorm, exponential/SiLU, hardware absorption and the telemetry CSR block.
The accelerator integration, MLA, expert execution and router/DMA remain to
be implemented. This is
not a completed accelerator or a ready verification handoff. No functional,
synthesis, timing, board or model-quality result is claimed.

`anvil_q3_reference/rtl/` is an immutable dependency, not a passing baseline.
There is no supplied repository-intake source index or parent acceptance
specification. `design/GENERATIONAL_HANDOFF.md` was not supplied; historical
Quartus timing and PPA are unavailable. Current-product physical results must
come from the shared runtime.

## Product and configuration

The eventual top is `anvil_d1_top`, with `MODEL_MODE=0` selecting native D1 and
`MODEL_MODE=1` selecting the actual immutable `anvil_q3_top`. Every parent port
and parameter meaning is retained in legacy mode. Native mode adds only the
specified CSR top ports, not test or debug ports.

| Native parameter | Default | Legal values |
|---|---:|---|
| NUM_LAYERS | 27 | 1..36 |
| HIDDEN_SIZE | 2048 | 8..2048, multiple of 8 |
| INTERMEDIATE_SIZE | 10944 | 8..11008, multiple of 8 |
| MOE_INTERMEDIATE_SIZE | 1408 | 8..1408, multiple of 8 |
| NUM_Q_HEADS | 16 | 1..16 |
| KV_LORA_RANK | 512 | 1..512 |
| QK_NOPE_HEAD_DIM | 128 | 1..128 |
| QK_ROPE_HEAD_DIM | 64 | even, 2..64 |
| V_HEAD_DIM | 128 | 1..128 |
| ROUTED_EXPERTS | 64 | 1..64 |
| TOP_K | 6 | 1..min(6, ROUTED_EXPERTS) |
| SHARED_EXPERTS | 2 | exactly 2 |
| FIRST_DENSE_LAYERS | 1 | 0..NUM_LAYERS |
| VOCAB_SIZE | 102400 | 4..151936 |
| MAX_SEQ_LEN | 32768 | 1..32768 |
| BANKS | 8 | 1, 2, 4, 8 |
| QUEUE_DEPTH | 3 | 1..16 |
| TILE_K | 128 | 8..128, multiple of 8 |
| TILE_ROWS | 8 | 1..8 |

Hidden width need not equal heads times head dimension. Invalid geometry must
produce a `PARAMETER ERROR` diagnostic, not silently select a smaller design.
Diagnostic-only port widths use minimum legal widths before rejection.
Constant elaboration arithmetic does not authorize runtime division hardware.

`anvil_d1_parameters` is the native geometry/address guard and must be
instantiated by the future native top. Its products check per-object byte or
component extents using 128-bit elaboration arithmetic. The externally supplied
memory address is the documented (kind,layer,proj,row,col) tuple, not a 32-bit
flattening of all model layers/experts. The guard does not change legal
production geometry or impose a resident whole-checkpoint capacity assumption.

Native weights, biases, activations, gamma and rotary table entries are full
signed 32-bit Q16.16 integers. They are not parent packed FP16/AWQ words.
Dense GQA R1-Distill configurations belong to the supported legacy geometry,
not the native MLA/MoE path. No arbitrary published checkpoint bit compatibility,
trained accuracy or unprovided checkpoint download is claimed.

## Cycle and degenerate-boundary table

All handshakes sample **pre-edge** valid and ready. State and payload changes
described below are **post-edge**. All control state uses active-low asynchronous
reset and nonblocking sequential assignments. All observable outputs, including
ready and data, are zero while reset is asserted. An internal armed bit permits
readiness only after the first rising edge following reset deassertion.

| Boundary | Required behavior |
|---|---|
| Reset assertion | Annul valid state; zero public outputs asynchronously |
| First edge after reset release | Idle readiness may become high post-edge |
| Command E0 | Latch accepted command; ready low and done low post-E0 |
| First request | No command request before E1 |
| Valid with ready low | Retain valid and identical payload until transfer or explicit cancellation |
| Request Er | Acquire ownership; same-edge matching response is legal |
| Final write acknowledgement Ef | Command done and outcome visible post-Ef for one cycle |
| Completion Ef+1 | Drop done; idle ready may return |
| Final logit acceptance El | Token done post-El; no new token acceptance at El |
| Cancel K0 | Suppress token acceptance, requests and logits; drain owned transactions before cancel_done |
| CSR C0 | Accept one request and register response post-C0 |
| CSR C1 or later | Earliest response retirement; no simultaneous second acceptance |
| Clear plus increments | Counter clear wins; snapshot invalidated |
| Snapshot plus increments | Snapshot copies pre-edge counters; live increments still occur |
| Flush plus arithmetic acceptance | Flush wins; no output from the annulled operation |
| Depth/queue/sequence length 1 | Explicit terminal comparisons; no zero-width indices |
| Non-power-of-two extent | Explicit last-element comparison, never bitmask wrap |
| Single-beat tile | The same accepted beat owns both first and last semantics |
| Shared and routed service | Independent ownership; neither client waits for the other's readiness |

Primitive arithmetic has single-flight ready/valid interfaces. Result valid
does not depend on result ready; a result is held until accepted. There is a
retirement bubble before a new arithmetic request. `flush` annuls arithmetic
state and takes priority over all transfers. Arithmetic does not own DDR tags.
Invalid engine commands use a separate REJECT state: acceptance E0 never
asserts done; the rejection completion is first visible post-E1.

### Exact arithmetic schedules

`anvil_d1_mul32` has exactly four registered stages:

| Edge | Pre-edge action | Post-edge state |
|---|---|---|
| M0 | Input handshake | Four signed/unsigned 16-bit partial products registered |
| M1 | Stage 1 available | Cross terms combined and outer products delayed |
| M2 | Stage 2 available | Low 32-bit sum/carry and high 32-bit sum registered |
| M3 | Stage 3 available | Final upper carry applied; product valid |
| M4 | Earliest result handshake | Consumer may capture product |

`anvil_d1_mul96x32` launches three signed limb multipliers at its input
handshake M0. The unsigned lower-limb correction is necessary; simply treating
all three limbs as signed is incorrect.

| Edge | Post-edge state |
|---|---|
| M0..M3 | Three limb products follow the four-stage table above |
| M4 | Consume registered limb products; correct unsigned low/middle limbs |
| M5 | Register output limb 0 and limb-1 sum/carry |
| M6 | Register limb-2 sum/carry, including lower-product sign extension |
| M7 | Register limb 3; 128-bit product valid |
| M8 | Earliest downstream acceptance |

`anvil_d1_add128` computes 32 bits and registers carry at each edge:

| Edge | Post-edge state |
|---|---|
| A0 | Input accepted; low 32 result bits and carry registered |
| A1 | Bits 63:32 and carry registered |
| A2 | Bits 95:64 and carry registered |
| A3 | Bits 127:96 registered; complete result and overflow valid |
| A4 | Earliest downstream acceptance |

Subtraction uses complemented B and initial carry one, with a proper signed
subtraction overflow test. `anvil_d1_accumulator` presents this same four-stage
adder result directly and commits its running sum when the result is consumed.
A MAC must launch this separate accumulator no earlier than the edge after its
registered product becomes valid; no fused combinational multiply/wide-add.

For `anvil_d1_udiv` numerator width W, D0 captures operands, D1..DW execute
exactly W restoring iterations, and D(W+1) registers quotient, remainder and
result-valid. A zero denominator still follows the same schedule but reports
an error. Each iteration uses bounded parallel 16-bit carry-prefix subtraction.
The result is consumable no earlier than D(W+2).

For `anvil_d1_sdiv`, S0 accepts and registers unsigned magnitude and sign.
S1 accepts the prepared operands into the unsigned core (D0). S2..S(W+1) are
the W iteration edges; S(W+2) registers the unsigned result. S(W+3) consumes
that result and registers sign restoration. The signed result is consumable
no earlier than S(W+4). Its W+1-bit output preserves the complete magnitude.
Denominators are unsigned and must be positive.

`anvil_d1_isqrt` accepts its unsigned 128-bit radicand at R0. R1..R64 each
consume two most-significant radicand bits with one registered restoring
digit iteration. R65 registers root and remainder; the earliest consumer edge
is R66. Root is floor(sqrt(E)); no combinational root chain is used.

`anvil_d1_round_sat` is a one-stage registered tensor-boundary conversion:
input accepted at B0, result valid post-B0, earliest consumer B1. Its constant
SHIFT selects fractional bits; no runtime shift/rounding convention is inferred
from the parent package.

### Arithmetic safety

The combinational helper `anvil_d1_sub_unsigned` uses parallel 16-bit base
sums and a logarithmic block generate/propagate prefix, followed by local
16-bit carry increments. It is not a runtime divider, multiplier or wide
ripple-borrow loop. It is used within registered division/root iterations and
signed magnitude preparation. These structural bounds are not STA evidence.

Signed products and dot sums retain exact precision: 32x32 -> signed 64;
96x32 -> signed 128; dot accumulation -> signed 128. Absorbed coefficients
are signed 96 bits. Arithmetic overflow and zero denominator are errors, never
successful zero data.

Define `sat32(z)=min(2^31-1,max(-2^31,z))`. For s>0,
`R_s(x)=sat32(sign(x)*floor((abs(x)+2^(s-1))/2^s))`;
`R_0(x)=sat32(x)`. Ties round away from zero. Products are not rounded term by
term. Residual addition saturates.

## Exact native normalization

For H Q16.16 inputs x and Q16.16 gamma g:

```
S = sum(x[j]*x[j])                         # exact unsigned 128
M = floor((S << 32) / H)                   # unsigned Q64
E = M + 2^48                              # native epsilon = 2^-16
d = isqrt(E)                              # floor, unsigned Q32
u = floor(2^64 / d)                        # unsigned Q32 in 64 bits
P[j] = x[j]*g[j]                          # exact signed 64
T[j] = P[j]*u                             # exact signed 128
y[j] = R_48(T[j])                         # sole output rounding
```

The reciprocal is not replaced by direct final division. There is no
intermediate normalized-vector rounding or gamma decoding. Native epsilon
ensures d>=2^24 and u<=2^40; zero d is nevertheless a fault. Reciprocal
multiplication sign-extends P to 96 bits and uses `anvil_d1_mul96x32` twice,
for u's two unsigned 32-bit limbs, with signed-limb corrections and a separate
registered add. The legal operand bounds ensure the combination fits 128 bits.
The parent epsilon and packed gamma behavior remain confined to legacy mode.

Native normalization uses kind 8 parent scratch slots for integration:
mode 0 reads hidden slot 0, writes norm0 slot 1, gamma kind 5;
mode 1 reads attention-residual slot 7, writes norm1 slot 8, gamma kind 6;
mode 2 reads hidden slot 0, writes final-normalized slot 14, gamma kind 7.
Gamma row is zero and column is component; kind 7 layer is zero.

The normalization FSM inserts explicit launch/wait states at every arithmetic
boundary. Its loop count is H for square accumulation followed by H gamma and
reciprocal outputs. Memory latency is variable. Acknowledgement of the final
output write directly changes the engine to its one-cycle COMPLETE state.

For every RMSNorm primitive, if launch is accepted at L0 and the primitive
registers valid post-Ln, the controller consumes it at Ln+1. The next launch
state is visible post-Ln+1; the next primitive can accept no earlier than Ln+2.
This applies separately to square -> accumulator, mean -> epsilon -> root ->
reciprocal, gamma product -> low product -> correction -> high product ->
combination -> rounding. There is no combinational or same-edge consumption
of a newly registered result. The memory port accepts issue at I0, presents
the registered request post-I0 and can transfer it no earlier than I1.
The controller consumes a response at its actual transfer edge, not through
another delayed completion flag.

## Exponential, SiLU, attention and routing equations

For signed Q16.16 x, `exp_q24(x)` is 2^24 for x>=0 and zero for x< -16*2^16.
Otherwise a=(-x)*2^8, n=floor(a/11629080), r=a-n*11629080.
Initialize term=total=2^24; for j=1..6 set
`term=-trunc_toward_zero(term*r/(2^24*j))`, then add term to total.
Return max(total,0)>>n. Taylor divisions truncate, not round.

`anvil_d1_exp` accepts a signed 33-bit x so subtracting extreme architectural
scores cannot overflow. The range checks return a registered result at the
accepting X0 edge for x>=0 or x< -1048576. Otherwise a 32-bit unsigned divider
accepts range-reduction operands at X1, registers quotient/remainder at X34,
and the controller consumes them at X35. The first Taylor multiplication
accepts at X36. Each Taylor term has this schedule relative to its accepting T0:

| Edge | Action |
|---|---|
| T0..T3 | Four-stage multiplication of (-term)*r |
| T4 | Controller captures registered 64-bit product |
| T5 | Signed 64-bit divider wrapper accepts numerator |
| T6 | Unsigned divider accepts prepared magnitude |
| T7..T70 | Exactly 64 restoring iterations |
| T71 | Unsigned result registration |
| T72 | Signed wrapper restores sign and registers valid |
| T73 | Controller captures next signed term |
| T74 | Add term to total; sixth term registers final result |
| T75 | Earliest multiplication acceptance for the next term |

Thus the non-shortcut exponential result is visible post-X485. Result stalls
hold valid/data/error; they do not alter the arithmetic schedule before valid.
The term multiplier negates the bounded 32-bit term before multiplication,
which is exactly equivalent to the specified negated truncating quotient.
Since 0<=r<11629080<2^24, term magnitude never exceeds 2^24; 32-bit signed
term/total storage is exact, with explicit narrowing/overflow checks.

Softmax subtracts its maximum in widened signed precision, accumulates
exponentials exactly, and uses `p_i=floor(e_i*2^24/sum(e))` where probabilities
are architectural outputs. A zero denominator faults.

SiLU uses e=exp_q24(-abs(x)) with a widened absolute value even for -2^31.
For nonnegative x, s=floor(2^48/(2^24+e)); for negative x,
s=floor((e*2^24)/(2^24+e)). Output is R_24(x*s).

`anvil_d1_silu` latches x at S0 and launches the widened -abs(x) exponential
at S1. It consumes that registered result at the following edge, launches a
49/26-bit unsigned divider on the next edge, consumes its registered quotient
on the edge following D50, then separately launches/consumes mul32 and
round_sat. With no result stall, its output is visible post-S61 for exponential
shortcuts and post-S546 for the six-term path. Output valid is held through
backpressure. There is no extra intermediate sigmoid or product rounding.

RoPE uses adjacent even/odd components and host Q16.16 cos/sin:
`x'=R_16(x*cos-y*sin)`, `y'=R_16(x*sin+y*cos)`.
Both products and their sum/difference are exact before the boundary.

Attention score numerator is the exact sum of absorbed query*latent and
rotary query*rotary key, without separate rounding. With
`scale=isqrt((nope+rope)*2^32)`,
`z=sat32(sign(S)*floor(abs(S)/scale))`; there is no extra left shift.
For each head, Z=sum(exp(z-max)) and N[r]=sum(exp(z-max)*c[r]) are exact.
Context rounds N/Z directly, ties away from zero, then saturates.
Floor-quantized probabilities never feed architectural latent context.

Hardware constructs
`A[h,r,j]=sum_d UK[h,d,r]*QN[h,d,j]` and
`B[h,i,r]=sum_v O[i,h*value+v]*UV[h,v,r]`.
Each exact Q32.32 coefficient is stored as three little-word-first beats.
Rebuild per layer/weight epoch before its first native token; new_sequence
conservatively starts a new epoch. No host-generated A/B substitutes for
hardware absorption in complete inference.

`anvil_d1_absorption` independently streams raw UK/QN then O/UV pairs through
mul32 and the separate four-stage accumulator. It loops input component
inside output row inside head, completes all A coefficients before B, and
writes every coefficient word 0,1,2 with an individual acknowledgement.
Reduction 0 uses accumulator in_first; final sum must sign-extend from 96 bits
or fault. Per-layer epoch-valid is set only at the final B-word acknowledgement.
An epoch match completes without raw traffic; flush invalidates all ownership.
This helper needs no production matrix array on chip. Per-command raw-read and
absorbed-write byte totals count actual accepted requests, clear on acceptance,
and remain stable after done. These are separate from cache traffic.

Native boundaries are c=R_16(D*x), kR=RoPE(R_16(KR*x)),
qAbs=R_32(A*x), qR=RoPE(R_16(QR*x)),
output=R_32(sum(B*context)). No expanded K/V DDR cache is permitted.
Each of two causal history passes reads each compressed scalar once across
all heads. Production payload is 2304 bytes/token/layer versus 20480 for the
explicit 16-head uncompressed MHA baseline: mathematical reduction 88.75%.
Observed cache transfers, including matched pass/write accounting, must show
greater than 82%; this is not a saving against parent GQA or total model traffic.

Router affinities are hardware R_16(weight dot normalized hidden) for every
expert. Rank winners by descending score, lower ID first on ties. Use full
softmax, select exactly TOP_K distinct winners, floor-normalize selected
probabilities to 2^24, and distribute leftover units in winner order. P=0
faults. Both shared experts execute at coefficient one.

Each expert projection is R_16(exact dot+bias*2^16), with SiLU on gate and
R_16(gate_silu*up) before down. Mix shared outputs*2^24 plus routed outputs
times normalized coefficients exactly, then R_24 once. Dense-first layers
use expert ID 127 and no extra mixture rounding.

Client 1 prefetches actual first gate tiles for all winning routed experts
while client 0 performs shared execution. Retained acknowledged data must be
consumed without reread. Storage is bounded by one first tile per selected
expert plus two compute tiles, each TILE_K*TILE_ROWS words. Count actual
speculative traffic, failures and overlap, not theoretical labels.

## Memory namespaces

The legacy path retains kinds 0..14 unchanged. Native embedding/projection,
gamma and parent scratch retain kinds 0,5,6,7,8. Kind 15 extensions:

| proj | Object | row | col |
|---:|---|---|---|
| 0 | Raw MLA matrices | matrix[3:0],head[3:0],output_row[23:0] | input component |
| 1 | Absorbed A | head[3:0],output_row[27:0] | 3*input_component+word |
| 2 | Absorbed B | head[3:0],output_row[27:0] | 3*input_component+word |
| 3 | Compressed cache | token position | latent then rotary-key component |
| 4 | Router weights | expert ID | hidden component |
| 5 | Expert weights | expert[6:0],matrix[1:0],output_row[22:0] | input component or bias projection |
| 6 | Rotary table | token position | 2*pair cosine, 2*pair+1 sine |
| 7 | D1 scratch | tensor ID | flattened tensor component |

Raw matrix IDs are D=0, KR=1, QN=2, QR=3, UK=4, UV=5, O=6.
Non-head matrices use head zero. O's input component is flattened head/value.
Expert matrix IDs are gate=0, up=1, down=2, bias=3. Shared expert IDs are
ROUTED_EXPERTS and ROUTED_EXPERTS+1.

D1 scratch tensor IDs are hidden=0,norm0=1,norm1=2,MLAout=3,MoEout=4,
query_latent=5,query_rope=6,latent_context=7,expert_work=8. Parent kind-8
scratch and kind-15/proj-7 scratch are distinct objects; explicit integration
copies, not address aliasing, are required when crossing these namespaces.
Layer is the model layer except global objects use zero. Field overflow faults.

## Telemetry CSR ABI

CSR requests are registered responses with no combinational bypass. Full byte
strobes are required for command/config writes; all counter registers are
read-only. Illegal, unknown, misaligned, partial or busy config writes report
csr_error without the requested side effect. Counter updates from actual
events remain independent of an illegal CSR access.

| Address | Register |
|---|---|
| 0x000 | ID 0x41445631 |
| 0x004 | Version 0x00010000 |
| 0x008 | Command: W1 clear bit 0, snapshot bit 1; reads zero |
| 0x00c | Status: busy bit 0, snapshot-valid bit 1, overflow-sticky bit 2 |
| 0x010 | Domain selection, idle-only, 0..4 |
| 0x014 | Think-begin token, idle-only, default VOCAB_SIZE-2 |
| 0x018 | Think-end token, idle-only, default VOCAB_SIZE-1 |

Unspecified command bits must be zero. A write with both command bits set
clears and invalidates snapshot. Reads never clear. Counter reads address the
snapshot; before the first snapshot they return zero and snapshot-valid is
false. Live counters are unsigned saturating 64 bits. Overflow is sticky
until clear. Configuration and busy state are not reset by counter clear.

Counter pairs begin at 0x040, low word then high, in this order:
cycles,tokens,errors,reasoning_tokens,reasoning_cycles,cache_read_bytes,
cache_write_bytes,cache_dense_equiv_bytes,expert_read_bytes,
expert_dense_equiv_bytes,other_read_bytes,other_write_bytes,
shared_busy_cycles,prefetch_busy_cycles,overlap_cycles.

Per-domain pairs start at 0x100+domain*0x40:
cycles,tokens,reasoning_tokens,read_bytes,write_bytes,expert_bytes.
Unused offsets are illegal, not aliases. Domain names are math,coding,science,
symbolic-logic,mixed-reasoning; selection is host metadata.

Global cycles count every armed clock. Domain cycles count the token-active
interval including acceptance and completion edges. Tokens count accepted
tokens, including tokens that later fail; errors count token_error events.
Global and domain reasoning token increments use token_accept AND
reasoning_active. Top-level delimiter comparison must include begin and
exclude end, with end taking priority if configured delimiters are equal.
Top resets reasoning state on new sequence, cancel or error. Configuration
writes on a simultaneous token acceptance are rejected as busy.

Domain attribution uses the domain_id event input, which top must connect to
the block's configured domain_select output. Internal configuration outputs
also expose think_begin_token and think_end_token to top; they are not added
top ports. Byte events are per-cycle unsigned increments. Engine totals must
be aggregated once at completion, not also counted as transaction increments.
Shared/prefetch/overlap counters use actual active event levels.

Atomic ratio operands and host calculations:
cache reduction = 1-(cache_read_bytes+cache_write_bytes)/cache_dense_equiv_bytes;
expert-only saving = 1-expert_read_bytes/expert_dense_equiv_bytes;
overlap efficiency = overlap_cycles/shared_busy_cycles.
Zero denominators are explicitly undefined, never zero or 100% success.
Other traffic is separate, and the 8-of-66 expert fraction is theoretical only.

## Dependencies, reproduction and evidence

Required tools are Python 3, Icarus/vvp, Verilator and Yosys for independent
portable L1. No tool version or test success is presumed before execution.
Quartus 17.1 and Arria 10 board checks are shared-runtime gates, not L1 scripts.
No tools are installed by this design increment.

Once independently implemented by Verifier, reproduction from the project root:

```
python3 tests/verify.py --suite behavior
python3 tests/verify.py --suite compatibility
python3 tests/verify.py --suite defects
python3 tests/verify.py --suite synthesis
python3 tests/verify.py --suite portable
```

All five commands remain mandatory and self-contained. They are requirements,
not currently delivered or passing verification artifacts. Verifier owns
`tests/*.py`; Designer does not author their model, harness or assertions.
Evidence directories must be fresh and end in a timestamp/hash. No receipt is
acceptance merely because it exists. No product PDF is an engineering input:
the shared runtime produces and independently reviews it after acceptance.

## Claim-to-source index

| Claim | Design source | Evidence status |
|---|---|---|
| Four-stage signed 32x32 | rtl/anvil_d1_mul32.sv | Independent verification pending |
| Eight-stage signed 96x32 | rtl/anvil_d1_mul96x32.sv | Independent verification pending |
| Four-stage add and separate accumulation | rtl/anvil_d1_add128.sv, rtl/anvil_d1_accumulator.sv | Independent verification pending |
| Registered integer division/root | rtl/anvil_d1_udiv.sv, rtl/anvil_d1_sdiv.sv, rtl/anvil_d1_isqrt.sv | Independent verification pending |
| Sole-boundary signed rounding | rtl/anvil_d1_round_sat.sv | Independent verification pending |
| Exact native RMSNorm | rtl/anvil_d1_rmsnorm.sv | Independent verification pending |
| Exact exponential / stable SiLU | rtl/anvil_d1_exp.sv, rtl/anvil_d1_silu.sv | Independent verification pending |
| Hardware exact A/B construction | rtl/anvil_d1_absorption.sv | Independent verification pending |
| Native geometry guard | rtl/anvil_d1_parameters.sv | Not yet integrated; diagnostic execution pending |
| Saturating atomic telemetry | rtl/anvil_d1_csr_perf.sv | Independent verification pending |
| Full native inference, MLA/MoE, legacy top | Not implemented in this increment | Not ready |
| 88.75% MHA cache reduction | Geometry calculation above | Mathematical, not measured |
| 100 MHz timing / physical PPA / HIL | Shared-runtime gates | Not executed |
| Historical parent PPA | Missing GENERATIONAL_HANDOFF.md | Unavailable |
