# Anvil-Q1-FP v1.2.0-bf16 specification

## Authority and implementation status

The independently admitted work order governs this design. This document
records its interfaces and numerical rules; it does not waive any acceptance
condition. The parent is source provenance, not a verified implementation.
The RTL includes the integrated top, native and compatibility command
operators, scalar kernels and shared memory/routing modules described in
ARCHITECTURE.md. This is a Designer implementation, not an accepted product.
There is no passing functional verification, resource result, timing result,
hardware result or product PDF yet. Static elaboration is not correctness.

Designer owns `rtl/*.sv`, these two design documents and `fpga/*`.
Independent Verifier owns `tests/**`. The shared runtime owns engineering
execution records, native hardware gates and the post-acceptance report.
`anvil_q1_reference/rtl/` is immutable.

## Product and legal parameters

Target: Intel Arria 10 GX `10AX115N2F45E1SG`, 100 MHz or faster, clock
period <=10 ns. Production defaults are:

| Parameter | Value |
| --- | ---: |
| NUM_LAYERS | 24 |
| HIDDEN_SIZE | 896 |
| INTERMEDIATE_SIZE | 4864 |
| NUM_Q_HEADS | 14 |
| NUM_KV_HEADS | 2 |
| HEAD_DIM | 64 |
| GROUP_SIZE | 128 |
| AWQ_BITS | 4 |
| VOCAB_SIZE | 151936 |
| MAX_SEQ_LEN | 32768 |

Model: `Qwen/Qwen2.5-0.5B-Instruct`; RoPE theta=1000000;
RMSNorm epsilon is binary32 `0x358637bd` (nearest binary32 to 1e-6).
All parent parameter legality checks remain mandatory: positive dimensions;
H=Q*D; Q divisible by K; D even; AWQ_BITS=4; H and I divisible by
G and eight; K*D divisible by eight; S<=16777215; each dimension
fits 32 unsigned bits; V*H, H*H, H*I, H*K*D, L*S*K*D, S*D,
2*D, 15*H and 15*I fit 32 unsigned bits. Illegal configurations
must produce explicit parameter diagnostics rather than become supported
datapaths. Safe widths/generate guards may only enable those diagnostics.

Mandatory legal tuples `(L,H,I,Q,K,D,G,V,S)` are production defaults,
`(1,8,8,1,1,8,1,1,1)`, `(2,24,40,3,1,8,1,3,3)` and
`(2,56,72,7,1,8,8,5,3)`. There is no legal HEAD_DIM=1 case.

## External interface

`anvil_q1_fp_top` retains the exact parameters and ports of
`anvil_q1_reference/rtl/anvil_q1_top.sv`, adding only
`input wire [1:0] precision_mode`. Token IDs, positions, logit indices,
request layers/rows/columns/write data and response data remain 32 bits.
Request kind is four bits, projection three bits. `logit_data` retains
`output wire signed [31:0]`; interpret its bits, not its Verilog signedness,
as binary32 in native modes.

| precision_mode | Interpretation |
| --- | --- |
| 00 | Parent W4A16 AWQ and Q16.16 compatibility |
| 01 | Native BF16 tensors, binary32 arithmetic/scratch/KV/logits |
| 10 | Native FP16 tensors, binary32 arithmetic/scratch/KV/logits |
| 11 | Invalid command, fault completion without memory activity |

Capture mode only on a pre-edge token_valid && token_ready handshake.
Ignore mode changes while busy. A changed mode requires an accepted
new_sequence at position zero. Reject continuation with a different mode.
Faults invalidate continuation until a valid new sequence at position zero.
Do not infer encoding from data values.

Every command operator retains its parent's parameters and command/memory
port names, widths and directions, appending input `[1:0] cmd_precision`.
It latches precision at command acceptance. Required literal hierarchy:

```
anvil_q1_fp_top
  memory_port
  decoder
    norm
    gemv
    rope
    attention
    mlp
      gemv
      silu_product
      bus
    residual
    bus
  final_norm
  bus
```

Use corresponding `anvil_q1_fp_*` module types; unchanged memory-port and
bus modules may retain parent names. Required floating-point leaves must
drive functional native results, not be disconnected demonstrations.

## Memory and ownership

One outstanding memory request; separate request and response handshakes.
Request fields remain stable until acceptance. Only an already accepted
request enables response acceptance. This excludes same-edge request/response
completion. Reads and writes each require exactly one response. Keep bus
ownership until completion. Unsolicited responses do not modify state.
Reset annuls the outstanding transaction and all in-flight arithmetic.

| Kind | Layout |
| ---: | --- |
| 0 | Embedding and tied output weights |
| 1 | AWQ packed weight nibbles |
| 2 | AWQ packed zero nibbles |
| 3 | AWQ per-output/group FP16 scales |
| 4 | Q/K/V bias |
| 5,6,7 | First, second, final normalization weights |
| 8 | Scratch tensor, row=slot, col=component |
| 9,10 | K/V cache: layer, row=position, col=kv_head*HEAD_DIM+dimension |
| 11 | RoPE coefficients: row=position, col=2*pair_index+sin_select |
| 12 | Native matrix: layer, projection, row=input, col=output |

Kinds 0,4,5,6,7,12 carry native selected-format data in `[15:0]`;
upper bits must be zero. Kind 12 is not used in compatibility mode.
Native scratch/KV/coefficient words are binary32. Compatibility encodings
are unchanged, including Q2.30 coefficients and AWQ lane nibble shifts
`[0,16,4,20,8,24,12,28]`. Invalid or negative nonzero FP16 scales fault.
No native conversion through a Q16.16 saturation path is permitted.

Projections 0..6 are Q,K,V,O,gate,up,down. Scratch slots:
0 residual; 1 first norm; 2 Q; 3 K; 4 V; 5 context; 6 O projection;
7 first residual; 8 second norm; 9 gate; 10 up; 11 activated product;
12 down; 14 final norm. GQA uses kv_head=floor(query_head/7) in
production. Explicit counters, not runtime division, implement GQA and
AWQ group advancement.

## Cycle and degenerate-boundary table

Reset is explicitly **synchronous active-low**, inherited from the parent:
`always @(posedge clk) if (!rst_n) ...`. Reset has priority over every
handshake, fault, arithmetic completion, counter increment and write.
All sequential assignments are nonblocking. Public valid/ready/done/error,
request fields and output data are gated to zero while rst_n is low.
The reset edge clears arithmetic pipelines and ownership.

| Event immediately before edge | Required state immediately after edge |
| --- | --- |
| rst_n=0, regardless of other inputs | Cleared state; no public transfer/result |
| First edge after reset release, no command | Idle token readiness, no request/logit/done |
| E0: token_valid && token_ready | Token/mode latched; ready low; no implied logit |
| E1: owner issues into idle memory port | Request becomes visible and stable |
| E2: mem_req_valid && mem_req_ready | Request outstanding; response ready enabled |
| E3: mem_rsp_valid && mem_rsp_ready | Retire one response, including write acknowledgement |
| Response valid before any request acceptance | No response transfer or architectural change |
| Request valid && !ready | Same valid and every request field after edge |
| Logit valid && !ready | Same logit valid/index/data after edge |
| EL: last logit valid && ready | done=1 for one complete cycle |
| EL+1 | done=0; return to idle readiness, independent of token_valid |
| Fault retirement | One error-completion cycle; continuation invalidated |
| Arithmetic result concurrent with reset/fault | Annul result; no later stale write/logit |
| Changed precision during an active command | Latched precision unchanged |
| S=1, position=0 | Only causal time index zero; no circular-mask wrapping |
| S=3, final legal position=2 | Visit 0,1,2; compare limits explicitly |
| V=1 | First accepted logit is also last; exactly one completion |
| One eight-lane output tile | No phantom next-tile request or extra output |
| Zero dot mask | Return seed under binary32 special/zero rules |
| Single active dot lane | Exactly that lane and seed; inactive exceptions ignored |
| New sequence and otherwise-invalid position | Invalid command; reset/recovery does not excuse it |

Reset must also be exercised during request stall, response wait, each
arithmetic stage, scalar-kernel wait, each operator command, logit stall
and completion. After each reset phase the same cleared-state row applies.
No simultaneous read/write arbitration exists: the single memory port
serializes transactions; write acknowledgement is not a second request.
Fault/reset priority is above ordinary increment/completion. Sequence
position comparison is unsigned and does not assume power-of-two depth.

## Dot arithmetic and status

`anvil_q1_fp_dot8` has the following fixed interface:

```
input wire clk, rst_n, in_valid;
input wire [1:0] in_precision;
input wire [127:0] a, b;
input wire [7:0] lane_mask;
input wire [31:0] acc_in;
output wire out_valid;
output wire [31:0] result;
output wire [4:0] status;
```

Lane i is `[16*i+:16]`. Accept one launch each cycle, without ready or
backpressure. The caller reserves result storage before launch.
Exactly three register stages: E0 capture product preparation, E1 capture
aligned terms, E2 capture reduction/rounded output. A launch at E1 produces
its result after E3. Bubbles produce out_valid=0, result=0, status=0.
Reset discards all in-flight launches.

BF16 is 1/8/7, bias 127. FP16 is 1/5/10, bias 15. Binary32 is
1/8/23, bias 127. Decode IEEE fields directly and multiply integer
significands exactly. Include the exact binary32 seed as the ninth term.
Among finite nonzero terms, let M be the largest absolute term and
`e=floor(log2(M))`. The alignment grid step is `2^(e-63)`.
Truncate each magnitude toward zero onto that grid, retaining 64
significand positions per term. Sum signed grid integers with sufficient
guard width, then normalize and round once to binary32, nearest/even.
Nine terms each lose less than one grid step; the sum's absolute
alignment loss is less than nine steps, independently of cancellation.
This is not repeated BF16 addition, Q16.16 accumulation or an FP64 claim.

`status[4:0]` = invalid, divide-by-zero, overflow, underflow, inexact.
An inactive lane contributes neither value, signed zero nor exception.
Quiet NaNs produce canonical `0x7fc00000`; signaling NaNs set invalid.
Zero times infinity and a sum containing both signed infinities are
invalid. A same-signed infinity is preserved without overflow status.
Finite overflow returns signed infinity with overflow and inexact.
Underflow uses tininess after rounding and requires inexactness.
Gradual underflow is mandatory. Alignment discards with any nonzero
discarded bits and non-exact final rounding set inexact. A result
rounded to the smallest normal is not tiny. Underflow is determined when
packing a nonzero aligned sum; exact cancellation on the alignment grid
does not itself set underflow, even when alignment had discarded bits.

Exact cancellation of nonzero terms gives +0 under nearest/even.
An entirely zero sum is -0 only when the seed and every active
zero product are negative zero; mixed zero signs give +0. Nonzero
negative results rounded to zero retain their sign. An all-zero mask
therefore preserves the seed, except NaN canonicalization/signaling rules.
Unsupported dot precisions 00/11 give canonical NaN with invalid;
command operators reject invalid command mode before issuing arithmetic.

External nonfinite model data, invalid arithmetic, divide-by-zero or
overflow cause command fault completion, never successful zero tensors.
Underflow and inexact alone are not command faults.

## Other floating-point operators

All native matrix accumulations, scores, denominators, contexts,
normalization reductions, residuals and logits use binary32 or wider.
Input storage quantization is separate from arithmetic error.
Compatibility rounding, saturation and invalid-scale/nibble semantics
remain the parent's, not native nearest/even semantics.

RMSNorm: `x_i*gamma_i/sqrt(sum(x_j*x_j)/H+epsilon)`.
RoPE: Qwen split-half rotation at indices i and i+D/2, angle
`p*1000000^(-2*i/D)`, every Q/K head. Kind-11 contents and theta provenance
are independently checked; adjacent-pair rotation is not equivalent.
Attention: causal QK/sqrt(D), max-subtracted stable exp, positive
denominator, weighted V, 7:1 production GQA. SwiGLU: silu(gate)*up,
then down projection. Preserve residual placement and the decoder's
eleven-step order: norm, Q, K, V, RoPE, attention, O, residual,
second norm, MLP, residual.

Scalar kernels expose `clk,rst_n,in_valid`, binary32 `x`,
`out_valid`, binary32 `result` and `[4:0] status`, without backpressure.
Latencies count register stages exactly as for the dot leaf:
exp=8, reciprocal=16, reciprocal-square-root=24. Initiation interval=1.
Use bounded registered range reduction/refinement, no combinational
division or unbounded iteration. Integration observes registered
completion; command latency also includes real memory waits.

Exp(0)=1 exactly; softmax x<-80 returns zero. On [-80,0],
relative error <=2e-5 plus one output-rounding ULP. Reciprocal and
reciprocal-square-root relative error <=2e-6 plus one output-rounding
ULP for positive finite inputs with normal mathematical results;
subnormal results have absolute error <=2 ULP. Canonicalize NaNs;
signaling NaNs are invalid. Reciprocal signed zero returns signed
infinity with divide-by-zero, signed infinity returns signed zero.
Reciprocal-square-root +infinity returns +0; signed zero returns
same-signed infinity with divide-by-zero; negative nonzero inputs,
including -infinity, are invalid. Exp(-infinity)=+0 and
exp(+infinity)=+infinity; other exp classes and finite overflow/
underflow follow the status rules above. Full finite exp input
range must not silently reinterpret positive inputs as softmax zero.

## Independent acceptance and reproduction

The required portable entrypoints, to be authored by Verifier, are:

```
python3 tests/verify.py --check prerequisites
python3 tests/verify.py --check l1
python3 tests/verify.py --check benchmark-contract
python3 tests/verify.py --check portable
```

Required existing binaries: python3, iverilog, vvp, yosys. Do not install
tools. Each run exclusively allocates a new evidence directory and retains
exact commands, hashes, versions, limits, timestamps, exits and raw logs;
failed runs are never overwritten. Functional simulation child allowances
are at least 3600 seconds. X/Z, parser failures, missing inputs, nonzero
exits and timeouts are failures, not skipped coverage.

Acceptance includes all mandatory small configurations in all three modes
and seeds 17,53,89; production elaboration, production operators and
address/schedule cases; 24-layer reduced-width integration; independent
address/protocol/numerical scoreboards; backpressure, faults, resets and
sequence/mode recovery; parent differential compatibility of logits and
all scratch/KV writes. Timing differences alone may be documented as waits.

Dot coverage includes every 16-bit encoding per format across directed
pairings, >=100000 seeded eight-lane vectors per format, all 256 masks,
boundaries, ties, denormals, special values, seeded cancellation and the
nine-grid-step bound. Each scalar kernel requires exponent/range-boundary
coverage and >=100000 seeded finite cases against independent mathematics.
Mutations must execute and fail unchanged relevant assertions for BF16
bias, FP16 subnormal handling, dot latency, cancellation, AWQ permutation,
7:1 grouping, theta/split-half rotation, mode latching and logit stability.
Compilation failure alone is not numerical mutation sensitivity.

Per finite operator case and precision: cosine >=0.9999 and normalized
max absolute error <=0.002. Per 24-layer integration case and native
precision: final-logit cosine >=0.999 and normalized max error <=0.01.
Normalize by max(1,max(abs(reference))); zero references use absolute
error, not an invented cosine. Report ordered-bit max ULP distance and
max XOR bit error with special/zero classes separated. These metrics
do not replace exact dot or architectural assertions.

Real Yosys full-hierarchy and arithmetic-leaf synthesis must check
consistency, zero latches, no undriven/black-box arithmetic, meaningful
sequential logic and reachable required operators. Reject runtime
division/modulo and mixed assignment styles in sequential blocks;
compile-time-only parameter expressions are allowed.

The exact full checkpoint and all production layers/dimensions remain
mandatory. `tests/data` must pin checkpoint revision/hashes, tokenizer/
template, tensor layouts, BF16/FP16 streams and same-checkpoint W4A16
AWQ artifact, recipe, calibration, scales, zeros and nibble order.
The project versioned five-domain suite uses first ten canonical-ID
records of GSM8K test, HumanEval, TriviaQA verified validation and
BIG-Bench Hard logical_deduction_three_objects; Sequence has ten
published seed-17 copy/reversal/key-retrieval cases. Pin revisions,
record IDs and content hashes in `tests/data/benchmark_manifest.json`.
All modes share tokenized prompts/template, greedy lowest-ID ties and
128 maximum new tokens. Generated Code evaluation requires an existing
suitably isolated execution environment.

Execute every case in every mode on the integrated product. Compare
shared teacher-forced logits to independent FP64 decoded-weight inference;
measure greedy task results separately. Report per-layer/final fidelity,
per-domain scores, accepted-token/final-logit and first-logit cycles,
arithmetic/stall cycles and generation latency. Report storage quantization
deviation from the original checkpoint separately. Missing artifacts or
execution facilities fail benchmark-contract; reduced L1 cases do not
substitute for full-model execution. Hardware execution may provide this
evidence only if bound to the actual accepted bitstream and input hashes.

The shared runtime executes separate mandatory L1.5 timing lint, L2
Quartus 17.1 fully constrained post-fit STA (WNS>=0 at <=10 ns) and L3
Arria 10 PCIe Gen3x8 HIL. At least three consecutive deterministic
physical passes are required. No local cable/BDF is shipped in tests.
No unjustified false/multicycle exceptions or arithmetic black boxes.
Compare ALM/DSP/memory to parent at identical part, constraints, memory
and tool settings. Keep actual parent failures; identify a timing-repaired
bit-compatible baseline separately if needed. Generic cells are not ALMs,
DSPs or timing. Any waiver needs actual Quartus STA and independent admission.

Portable clean-copy checks copy only deliverable sources, constraints,
tests, reference RTL and declared available inputs; exclude runtime
metadata, binaries, prior evidence and private-session dependencies.
Generated outputs are outside input selectors. No final product report
is an engineering prerequisite. The runtime authors/reviews/renders the
PDF only after all engineering gates pass.
