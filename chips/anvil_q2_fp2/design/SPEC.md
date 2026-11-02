# Anvil-Q2-FP2 frozen implementation contract

Version: `v2.2.0-fp2-bfp-fused`. Required top: `anvil_q2_fp2_top`.
Target: Intel Arria 10 GX `10AX115N2F45E1SG`, clock period at most 10 ns.

## Status and provenance

This is a design contract, not an acceptance report. The integrated RTL is
submitted for independent verification. The admitted work order remains authoritative, including its complete
coverage matrix and thresholds. No functional, synthesis, timing, board,
speedup, resource or model-quality result is established by this document.
The supplied `anvil_q2_fp_reference/rtl/*.sv` files are immutable.
Neither a repository-intake source index nor a parent
`design/GENERATIONAL_HANDOFF.md` was supplied. No parent physical baseline has
therefore been accepted; comparable source-bound parent Quartus results remain
necessary for physical improvement claims.

Designer owns `rtl/*.sv`, `design/*.md` and `fpga/*`. Independent Verifier owns
`tests/*.py`, generated stimulus, mathematics and execution. Designer does not
run functional simulation or synthesis. The final independently approved PDF is
produced by the shared runtime after engineering acceptance and is not an
engineering-check prerequisite.

## Cycle and degenerate-boundary table

All transaction decisions sample **pre-edge** valid and ready. State and
payload updates are **post-edge**. E0 is the accepting rising edge; a pipeline
with L registered stages produces valid after E(L-1), with earliest transfer
E(L). Every sequential state block uses `posedge clk or negedge rst_n`.

| Boundary | Required behavior |
| --- | --- |
| Active reset | External valid, ready, done, error, cancel-done, writes and payloads are zero. Unreset storage is inaccessible behind cleared ownership/valid bits. |
| First released clock | Only pre-edge handshakes transfer; no invented transfer from a newly asserted post-edge valid. |
| Stalled result | Full payload, metadata and error stay stable until accepted or explicitly aborted. |
| Flush and transfer | Flush aborts local uncommitted pipeline work and has priority over local transfers. Already accepted external memory requests remain drain obligations. |
| Cancel and token acceptance | Cancel wins; requests already accepted on that edge must still drain. |
| Two weight buffers | Filling never writes an owned completed buffer. A buffer is released only by its completed-tile transfer. No same-edge release look-through is required. |
| Simultaneous fill/release | Different independently owned slots may change on one edge without changing either payload association. |
| Single tile | `first && last` is legal. Empty masks contribute positive zero. |
| Partial groups/tiles | Inactive lanes are masked, not counted in group maxima, and do not read nonexistent tensor elements. |
| Queue/tile depth one | Explicit terminal-count wrap, not an underflowing width or power-of-two assumption. |
| Odd queue/tile depth | Wrap on the last legal index; masking by depth minus one is forbidden. |
| CSR clear/increment | Clear wins over every increment on the accepting control-write edge. |
| CSR clear/snapshot | Both together snapshot zero. Snapshot words remain coherent as live counters advance. |
| Final logit | Acceptance precedes the one-clock done pulse. No new token before idle. |

| Operator | Registered stages | Earliest result after E0 | Earliest transfer |
| --- | --- | --- | --- |
| FP32 multiply | 3 | E2 | E3 |
| FP32 add | 4 | E3 | E4 |
| Tensor tile | 38 | E37 | E38 |
| Inverse square root | 2, II=1 | E1 | E2 |
| RoPE pair | 7 | E6 | E7 |
| Residual | 4 | E3 | E4 |
| Pass-through | 1 | E0 | E1 |
| SwiGLU | 24 | E23 | E24 |
| CSR | 2 | E1 | E2 |

RMS input i transfers at E(4*i) without stalls. With final input edge F,
square/ordered-sum finishes F+6; mean multiplication F+7..F+9; epsilon
addition F+10..F+13; rsqrt F+14..F+15; normalization/gamma products
F+16..F+21. First result is valid F+21, earliest transfer F+22; subsequent
results may transfer each clock. N=1 has this same schedule.
FlashAttention must finish within
`(512 + 64*HEAD_DIM)*cmd_len + 64*HEAD_DIM` clocks in a responsive environment,
and never before accepting and normalizing the final causal KV item.

## Defaults and legality

Default dimensions are 28 layers, hidden 1536, intermediate 8960, 12 query
heads, 2 KV heads, head dimension 128, vocabulary 151936, sequence length
32768. Parent parameter order/defaults, including its safe SB rule, are
preserved; `ACCEL_ENABLE=1` and `COUNTER_BITS=64` are appended.

Accelerated ranges: layers 1..28, hidden 1..1536, intermediate 1..8960,
vocabulary 1..151936, sequence 1..32768, even head dimension 2..128,
positive KV heads, query heads exactly six times KV heads and hidden exactly
query-heads times head dimension. Parent divisibility and address-overflow
restrictions remain applicable. BANKS is 1, 2 or 4, QUEUE_DEPTH is 1..16,
AWQ_BITS is 4, COUNTER_BITS is 1..64. MX_GROUP is independently fixed at 32.
FlashAttention TILE_TOKENS is 1..32, including non-powers of two. Unsupported
parameters must reach an explicit `PARAMETER ERROR` before useful traffic,
using safe diagnostic widths and legal-datapath generate guards.

The compact smoke tuple is hidden=48, intermediate=64, query heads=6,
KV heads=1, head dimension=8, GROUP_SIZE=8, vocabulary=16, sequence=3;
explicitly select CACHE_BLOCK=8, since the parent default 16 is not divisible
into this head geometry.

ACCEL_ENABLE=0 uses a literal parent instance. FP_FORMAT=1, WEIGHT_MODE=1 or
CACHE_MODE=1 retains the parent FP16, AWQ or int8-cache meaning. Accelerated
BF16 uses FP_FORMAT=0 and weight/cache modes 0=native or 2=MXFP8.
Mode 2 with ACCEL_ENABLE=0 is rejected.
Mode 2 mixed with FP16, AWQ or the legacy int8 cache is also rejected:
neither the accelerated BF16 graph nor the unchanged parent defines that
combination. Existing legal parent configurations are not reinterpreted.
The exact parameter/port tables and tensor-layout conversion are in
`INTERFACES.md`; the connected graph and storage lifetimes are in
`ARCHITECTURE.md`.

## Numerical rules

FP32 is binary32 RNE, ties to even, gradual underflow, canonical NaN
`0x7fc00000`, with IEEE signed-zero distinctions. No real/shortreal RTL,
flush-to-zero or silent saturation is permitted. Nonfinite architectural
inputs/results fail the transaction; arithmetic primitives still implement
their IEEE classifications. BF16 expansion concatenates 16 zero bits;
narrowing is RNE. Every finite BF16 pattern, including subnormals, round-trips.

E4M3FN has sign 7, exponent 6:3, fraction 2:0 and bias 7. Subnormal magnitude
is fraction times 2^-9. Normal magnitude is (1+fraction/8) times
2^(exponent-7); exponent 15/fraction 6 is 448; fraction 7 at that exponent
is NaN. E8M0 s=0..254 means 2^(s-127); 255 is invalid. Decode exact value
times scale then RNE to BF16; a nonfinite decoded result fails.
Group encoding chooses the smallest supported scale accommodating its maximum
at 448, clamping only at the minimum supported exponent. All-zero groups use
scale 127. Signed zero is preserved; padding is zero and excluded from maxima.

Tensor products round independently to FP32, followed by seven adjacent-pair
balanced FP32 tree levels over all 128 lanes. Row tile sums accumulate in
ascending column order, followed by bias where the graph requires it.
Group exponent alignment retains each lane's exponent residual and entire
significand and must not alter this result.

RMS squares/sums in FP32 input-index order, multiplies by correctly rounded
1/N, adds epsilon `0x358637bd`, applies rsqrt and evaluates
RN(RN(x*inverse)*gamma). Rsqrt must be within 4 ULP for positive finite
inputs, including subnormals; other inputs fail.
RoPE uses Qwen split-half pairs and theta=1000000, with actual FP32
coefficients for `position*theta^(-2*i/HEAD_DIM)`, not identity placeholders.
Its exact arithmetic is RN(RN(x*cos)-RN(y*sin)) and
RN(RN(y*cos)+RN(x*sin)).
SwiGLU is RN(RN(gate*sigmoid(gate))*up); exp(-abs(gate)) stabilizes sigmoid.
Exp on [-80,0] and positive reciprocal each require <=4 ULP. Exp below -80
may return positive zero. SwiGLU's nonnegative branch uses 1/(1+e);
its negative branch uses e/(1+e).

Attention broadcasts each single transferred KV head to six distinct query
heads. It retains six independent online (m,l,o) states and no
O(sequence-length) score/probability store. The first score is explicit;
subsequent updates rescale old l/o when the running maximum changes.
Score reduction uses the fixed balanced FP32 tree followed by correctly
rounded 1/sqrt(HEAD_DIM). Normalize by l only after the final causal key.

## Stream and memory ABI

The admitted exact top, tensor, epilogue, rsqrt and attention port lists are
fixed. Mandatory literal hierarchy includes `anvil_q2_fp2_bfp_tensor_array`,
`anvil_q2_fp2_epilogue_fusion`, `anvil_q2_fp2_flash_attn` and
`anvil_q2_fp2_telemetry`. The tensor owns the named
`ping_pong_prefetch`; the epilogue owns named rsqrt2 `inverse_sqrt`.
These must perform the actual graph, not act as disconnected witnesses.

The DDR interface is a logical 512-bit controller boundary, not a PHY.
An accepted read or write transfers one 64-byte beat and receives exactly one
tagged response. At least two reads may be outstanding; reordered responses
are legal. Never reuse an outstanding tag. Inactive interfaces drive all
request outputs to zero. Element zero occupies least significant bits.
Formats: 0=FP32 words, 1=BF16 halfwords, 2=E4M3FN bytes, 3=E8M0 bytes.
Metadata fetches consume real accounted beats.

Logical GEMV layout is output-row-major: row is output row and column is the
first reduction element. Embeddings use token row/hidden column. Preserve
parent kinds for all logical tensors. Projection scales use kind 3; MX KV
payloads use kinds 12/13 and scales 14/15. Compatibility int8 and MXFP8 must
not share a numerical interpretation.

Tensor weight tiles have four BF16 beats or two MX beats. Each MX beat has
two Group-32 scales in `w_scale[7:0]` and `[15:8]`. Weight and activation
tiles pair in order with equal tags; mismatch and memory errors yield failed
outputs. First/last describe the tile's row position, including first+last.
Tile metadata is repeated consistently on every weight beat. A partial tile
remains owned until completed or flushed; missing beats cannot be inferred
from legal idle cycles.

CSR accepts one request at a time; unsupported, misaligned and read-only
writes fail. CSRs work while token traffic is stalled. Version at 0x0000 is
0x00020200; features/status at 0x0004; control at 0x0008 uses W1 clear bit 0
and snapshot bit 1. Counter low/high pairs are:

| Address | Counter |
| --- | --- |
| 0x0010 | Active cycles |
| 0x0018 | Memory-request stalls |
| 0x0020 | Weight underflow |
| 0x0028 | Tensor bubbles, excluding idle |
| 0x0030 | Epilogue output stalls |
| 0x0038 | Transferred KV bytes |
| 0x0040 | DDR read beats |
| 0x0048 | DDR write beats |
| 0x0050 | Additional KV query-head uses |
| 0x0058 | Completed tokens |
| 0x0060 | MX saturation events |
| 0x0068 | Error completions |

Counters saturate at COUNTER_BITS and zero-extend to 64 bits. Live events
come from actual pre-edge handshakes/state, not fixture expectations.

## Independent acceptance and reproduction contract

Verifier supplies self-contained `python3 tests/verify.py --suite SUITE` for
`behavior`, `numerics`, `defects`, `synthesis`, `benchmark`, `delivery`;
no suite executes all. Tools observed at planning were Python 3.12.3,
Icarus 12.0, Verilator 5.020, Yosys 0.33, g++ and make. No installation,
Quartus license, board access or successful tool execution is implied.
Missing tools are explicit errors. Commands run from the delivered root;
isolated `python3 -I tests/verify.py --suite delivery` must also work.

Required coverage retains the admitted twelve-or-more legal boundary tuples,
all seeds 17/89/203, illegal parameter families, cancellation and reordered
responses, default elaboration, actual 1536/8960/128 operators and compact
28-layer sequencing. Icarus is limited to compact <=500k-cycle runs designed
below 60 seconds; compiled Verilator handles remaining workloads.

Numerics includes all 65536 BF16 patterns, all 256-by-256 MX code/scale
pairs, >=10000 independent tensor tiles, >=10000 stratified rsqrt inputs,
>=1000 RMS vectors, >=10000 nontrivial RoPE pairs, >=10000 SwiGLU elements
and >=100 six-head attention transactions. Tensor/RoPE operation sequences
are bit-exact. RMS/SwiGLU error is <=3e-6+3e-6*abs(reference), attention
<=1e-5+1e-4*abs(reference), compact logits
<=5e-4*(1+abs(reference)). MX reconstruction RMS/max is <=0.065 for
nonzero independently generated groups; quantify compression loss separately.
All ten admitted, successfully compiling numerical/protocol/telemetry mutants
must be detected by genuine observations, not compilation failure.

Five domains execute identical logical fixtures on parent and FP2 with matched
memory service, reporting every domain's cycles, bytes, errors and telemetry.
Measured geometric-mean cycle speedup must exceed one. BF16/MX payload
density is exactly 2x for full beats; unpadded metadata-inclusive density is
64/33, not 2x. KV transfers including scales must be <=1/6 of an executed
six-query nonbroadcast reference. Fused stages perform zero intermediate
architectural SRAM writes.

Real Yosys must find substantive engines and zero latches, unresolved modules,
blackboxes or division/modulo cells. Native shared-runtime gates separately
require rtl-timing-lint, Quartus 17.1 WNS>=0 at <=10 ns and three consecutive
deterministic PCIe Gen3x8 board passes. Throughput/ALM improvement needs
comparable source-bound parent target evidence. Generic cells are not ALMs
or watts. No unmeasured power or official model-quality claim is permitted.
Each independent suite retains a fresh `evidence/<suite>-<timestamp_or_hash>/`
receipt, raw logs, source hashes and summaries; failures are never overwritten.
