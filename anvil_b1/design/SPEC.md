# Anvil-B1 implementation contract

Version: `v1.0.0-bitnet-b158-2b4t`. Target: Intel Arria 10 GX
`10AX115N2F45E1SG`, synchronous clock period <= 10.0 ns.

## Status and provenance

This is the design contract, not verification or timing evidence. The supplied
source inventory contains only `anvil_q3_reference/rtl/*.sv`. Those files are
immutable compatibility inputs; their expected aggregate SHA-256 is
`1549e8c923beda7cb4f8c93181c471776eff55720d329b7fa9547b76b59f4207`,
using `(cd anvil_q3_reference && sha256sum rtl/*.sv) | sha256sum`.
There is no repository-intake linked source index. The requested parent
`design/GENERATIONAL_HANDOFF.md` was not supplied. No parent STA, PPA or B1
acceptance result is inferred from that missing document.

The design is being implemented incrementally. A module documented here is not
necessarily implemented yet. See ARCHITECTURE.md for the saved-source boundary.
Independent Verifier owns all simulation, numerical models, synthesis and
`tests/*.py`; the shared runtime owns timing, physical hardware gates and the
eventual independently approved product PDF.

## Geometry and graph

Production defaults: layers=30, hidden=2560, intermediate=6912, query heads=20,
KV heads=5, head dimension=128, vocabulary=128256, maximum sequence=4096,
LANES=512, BANKS=8, QUEUE_DEPTH=3, PACKING=0.
Legal layers are 1..30, even head dimension 2..128, KV heads 1..5, query heads
exactly four times KV heads, hidden exactly query heads times head dimension,
intermediate 1..6912, vocabulary 1..128256, sequence 1..4096, BANKS in
{1,2,4,8}, QUEUE_DEPTH 1..16, LANES in {1,2,4,8,16,32,64,128,256,512},
PACKING in {0,1}. All other values require `B1 PARAMETER ERROR`.
Diagnostic-only port dimensions may be guarded; legal geometry is never clamped.

Each bias-free layer executes input learned RMSNorm and shared Q/K/V activation
quantization; Q/K/V projections; split-half RoPE; causal 4:1 GQA; attention
SubLN plus quantization and O projection; residual addition; post-attention
RMSNorm and shared gate/up quantization; gated ReLU-squared; FFN SubLN plus
quantization; down projection; second residual. Final learned RMSNorm feeds the
tied BF16 embedding/output head. Every vocabulary logit is emitted in order.
RoPE theta=500000; RMSNorm epsilon=1e-5. Public model revision:
`microsoft/bitnet-b1.58-2B-4T@04c3b9ad9361b824064a1f25ea60a8be9599b127`.
Model-card Transformers revision:
`096f25ae1f501a084d8ff2dcaf25fbc2bd60eba4`.
These identify external inputs, not downloaded or validated assets.

## Integer arithmetic

Residual, projection, norm and logit data are signed 32-bit Q16.16. All rounding
is nearest, ties to even, including negative numbers. Widen before negation,
absolute value, addition and multiplication. Saturation is only at the declared
32-bit or INT8 boundaries and must produce a numerical-saturation event.
Finite BF16 is converted with RNE and saturation; nonfinite data is an error.
Positive projection multipliers are multiplicative raw Q16.16; zero, negative,
nonfinite or positive BF16 multipliers that round to zero are invalid.

For N raw inputs, accumulate S=sum(X*X) in at least 80 unsigned bits.
M=floor(S/N); R=isqrt((M+42950)<<32).
Y=sat32(RNE(X*G*65536/R)), with learned raw Q16.16 G.
A=max(abs(Y)) is unsigned 32-bit and is finalized across the complete vector
before emission. With A=0 all codes are zero; otherwise
q=clip(RNE(127*Y/A),-128,127). Norm-only drives q=0.
Projection row dot D is signed at least 64-bit, with no tile saturation;
output=sat32(RNE(D*A*W/(127*65536))) using >=128-bit intermediates.
ReLU2=sat32(RNE(max(X,0)^2/65536));
gate-up=sat32(RNE(ReLU2*up/65536)); residual addition saturates.
This is a fixed-point hardware model, not bitwise BF16 Transformers equivalence.

## MAC leaf

`anvil_b1_ternary_mac_array #(LANES=512)` derives local constants
`RADIX_BYTES=(LANES+4)/5` and
`WEIGHT_BITS=(2*LANES > 8*RADIX_BYTES) ? 2*LANES : 8*RADIX_BYTES`.
Neither local constant is an overridable product parameter. Diagnostic guards
apply only for illegal LANES.

| Port | Direction / width |
|---|---|
| clk, rst_n, flush, in_valid, out_ready | input, 1 |
| in_ready, out_valid | output, 1 |
| in_act | input, 8*LANES |
| in_weights | input, WEIGHT_BITS |
| in_mask | input, LANES |
| in_packing, in_first, in_last | input, 1 |
| in_tag | input, 32 |
| out_sum | output, signed 32 |
| out_error, out_first, out_last | output, 1 |
| out_tag | output, 32 |

Lane zero uses the low signed activation byte. Packing=0 uses five
least-significant-first base-three digits per byte, 0=-1, 1=0, 2=+1.
Participating radix bytes >=243 are errors, including their full high bits at
LANES=1 and 2. Packing=1 uses low-first two-bit codes 00=0,01=+1,11=-1;
active 10 is an error. Masked lanes are zero and do not cause code errors.
INT8 -128 is extended before negation. An error result is still an aligned
tile transaction, but must never commit a projection row.

Stage 0 captures operands. Stage 1 decodes/gates signed 9-bit terms. Each
subsequent stage is one registered balanced reduction level. A common advance
enable freezes every payload, valid and metadata register when the final
result is blocked. Accepted E0 produces output post-E(1+log2(LANES)), including
post-E1 for LANES=1 and post-E10 for LANES=512. Steady state is one tile/clock.
This leaf produces a tile sum only; row accumulation belongs to GEMV.

GEMV must retain the identical derived WEIGHT_BITS through operand storage and
connections. Rows are packed continuously, not padded at tile boundaries;
partial byte carry is reassembled into tile-local MAC operands. Canonical
row-tail unused trits/codes encode zero.

## Fusion leaf

`anvil_b1_subln_relu2_fusion #(MAX_VECTOR=6912)` accepts command ports
`cmd_valid,cmd_ready,cmd_mode[1:0],cmd_count[31:0]`, clock/reset/flush,
sample ports `in_valid,in_ready,in_last,in_x,in_up,in_gamma` (three signed
32-bit values), and result ports
`out_valid,out_ready,out_last,out_x` (signed 32), `out_q` (signed 8),
`out_absmax` (unsigned 32), plus `done,error`.
Count is 1..MAX_VECTOR. Modes:
0=NORM_QUANT, 1=RELU2_UP_NORM_QUANT, 2=QUANT_ONLY, 3=NORM_ONLY.
Mode 1 performs both saturated gate arithmetic operations before normalization.
Mode 2 emits the unchanged input X. All modes report the complete output
vector absmax. A bad count or mismatched last yields one error completion,
no successful result vector. No fused intermediate is materialized in external
memory. Commands and their first sample are separate transactions.

## Cycle and degenerate-boundary table

| Boundary | Required behavior |
|---|---|
| Active reset | Asynchronous active-low reset; every public output zero; no transfer |
| First released clock | Idle ready may assert pre-edge; no phantom completion |
| Command at E0 | Sample pre-edge valid && ready exactly once; first data no earlier than E1 |
| Result production | Valid/data post-edge; consumed only at a later pre-edge handshake |
| Stalled result | Valid and every payload/metadata bit unchanged |
| Last result consumed | Completion high post-consumption-edge for one clock |
| Flush/cancel and work | Reset > flush/cancel > work; no success from annulled work |
| Invalid command E0 | Error completion post-E1; no output or memory request |
| MAC LANES=1 | Capture then decode; zero reduction levels; full radix byte checked |
| MAC LANES=2 | One reduction level; each nonzero mask independently valid |
| Fusion count=1 | First accepted sample must also have last; final absmax still finalized |
| Ragged vectors | No assumed divisibility by LANES, 4 or 5 |
| Queue depth=1 or 3 | Explicit final-entry wrap, no power-of-two mask assumption |
| CSR clear + snapshot + event | Clear wins; counters and sticky error zero; snapshot invalid |
| CSR snapshot + event | Snapshot takes pre-edge live values; live event still counts |
| Read and event | Read snapshot only; no torn low/high live-counter read |

All B1 clocked control uses nonblocking assignments exclusively. Runtime
division/modulo is sequential arithmetic; only constant geometry division may
remain in source. Wide arithmetic carries are segmented to at most 32 bits
between registers. Timing closure and mapped ternary zero-DSP use remain
independent physical acceptance obligations.

## CSR ABI and event interface

Top/block CSR ports: inputs `clk,rst_n,csr_valid,csr_write,csr_addr[11:0],
csr_wdata[31:0],csr_rready`; outputs `csr_ready,csr_rvalid,csr_error,
csr_rdata[31:0]`. Exactly one registered response per request, stable until
consumed. No request while a response is blocked. Undefined, misaligned,
reserved-bit writes and read-only writes return error.

Internal event inputs are registered producer pulses/deltas, not new top ports:

| Event | Width | Meaning per sampled edge |
|---|---|---|
| event_busy | 1 | Active token or draining status |
| event_error | 1 | Sticky protocol/data-format error indication |
| event_cycle | 1 | One measured cycle |
| event_mac_tile | 1 | One accepted MAC tile |
| event_valid_trits, event_nonzero_trits | 10 each | Active/nonzero trits in accepted tile, 0..512 |
| event_weight_bytes | 16 | Logical packed bytes of committed rows, padding once |
| event_weight_bus_bytes | 16 | Accepted kind-1 bus bytes |
| event_w4_bytes | 16 | Sum ceil(row_weights/2) for committed rows |
| event_bf16_bytes | 16 | Sum 2*row_weights for committed rows |
| event_stall | 1 | Compute/output stall cycle, counted once |
| event_token_ok, event_token_fail | 1 each | Actual token completions |
| event_saturation | 16 | Count of numerical boundary saturations |
| event_metadata_bytes | 16 | Accepted non-payload metadata bus bytes |

ID 0x000=0x41423130, version 0x004=0x00010000. Status 0x008:
bit0 busy, bit1 sticky error, bit2 snapshot-valid, remaining zero.
Control 0x010: bit0 clear, bit1 snapshot, other bits invalid; reads return zero.
Counters are unsigned saturating 64-bit, low then high, snapshot-only:
cycles 0x020, tiles 0x028, trits 0x030, nonzero 0x038, logical bytes 0x040,
weight bus bytes 0x048, equivalent W4 0x050, equivalent BF16 0x058,
stalls 0x060, successful tokens 0x068, failed completions 0x070,
saturations 0x078, metadata bytes 0x080. Clear invalidates snapshots.
Snapshot is atomic and captures pre-edge live counters without stopping them.
Ratios are software calculations; zero denominator means not-applicable.
Equivalent payload counts are not measured AWQ/BF16 inference performance.

## External memory and token ABI

Top name `anvil_b1_top`; token/logit/tagged memory ports preserve parent names
and widths. Each bank's slice is least-significant-indexed. Memory tags are
opaque 64-bit identities unique across live operations. Cross-bank reorder
must preserve per-client response order. Unknown/duplicate/corrupted tags and
response errors fail explicitly. Cancellation suppresses unissued work,
drains accepted traffic, prevents stale commit and invalidates sequence ownership.

Memory kinds: 0 tied BF16 embedding/head; 1 ternary words; 2 BF16 internal
SubLN (proj=0 attention,1 FFN); 3 positive Q16.16 projection multiplier;
5/6/7 BF16 input/post-attention/final norm; 8 Q16.16 scratch;
11 Q2.30 RoPE; 12/13 packed INT8 K/V; 14/15 unsigned Q16.16 K/V absmax.
Kinds 4,9,10 are invalid. Projection IDs Q,K,V,O,gate,up,down are 0..6.
Projection row is output row; col is little-endian 32-bit word within row.
Kind 3 row=col=0. Norm weights use row=0,col=component, layer=decoder layer
(final norm layer=0). BF16 words have zero upper half.
RoPE uses layer=0,row=position,col=2*pair for cosine and 2*pair+1 for sine;
the same coefficients serve all heads, pair=0..HEAD_DIM/2-1.
Embedding/head row=token/vocabulary ID,col=component, layer=0,proj=0.
KV row=position,col=head*ceil(HEAD_DIM/4)+word, metadata col=head;
layer=decoder layer,proj=0. Tail payload high bytes are zero.
Stored -128 is invalid; absmax zero requires all active codes zero.

Scratch kind 8 has layer=0,proj=0,row=slot,col=component. Slots:
0 residual input; 1 normalized QKV input; 2 Q; 3 K; 4 V; 5 context;
6 O result; 7 attention residual; 8 normalized FFN input; 9 gate; 10 up;
11 gated/normalized FFN boundary; 12 down; 13 layer result;
14 final-normalized; optional 15 attention-SubLN.
Internal fused intermediates never use these slots.

An idle, non-draining top alone accepts tokens. New sequence requires position
zero and invalidates old KV ownership. Otherwise require a valid sequence and
exact next position. Phase 0=prefill,1=decode; decode-to-prefill is illegal
until new sequence. IDs/positions must be in range. Errors invalidate sequence
and complete done&&error. Success emits exactly VOCAB_SIZE ascending stable
logits then done after final handshake. Cancellation suppresses further logits,
drains, emits cancel_done, and fails an active cancelled token exactly once.

## Attention arithmetic

Pair i with i+HEAD_DIM/2. Rotate with Q2.30 C,S using widened products and one
RNE shift of 30, then sat32. Reject coefficients outside [-2^30,2^30].
Position zero is exact identity. Quantize rotated Q and K and unrotated V
separately per head. Commit K,V and metadata before making a position readable.
Each group of four query heads aliases one physical KV head.
Let C_D=RNE(2^30/sqrt(HEAD_DIM)), generated independently at high precision.
Score=sat32(RNE(dot(q8,k8)*Aq*Ak*C_D/(127^2*2^46))).
Decoded V=sat32(RNE(v8*Av/127)).

For each causal score s: m'=max(m,s), a=E(m-m'), b=E(s-m');
l'=RNE(l*a/2^24)+b; z'=RNE(z*a/2^24)+b*V.
Initialize l=z=0, m=first score; use unsigned 64-bit l and signed 96-bit z.
Final context=sat32(RNE(z/l)); zero denominator is an error.
E(x)=2^24 for x>=0; E(x)=0 for x<-1048576.
Otherwise u=(-x)<<16, k=floor(u/2977044472), r=u-k*2977044472;
t0=2^40; tn=RNE(t(n-1)*r/(n*2^32)), n=1..10;
T=sum((-1)^n*tn,n=0..10);
E=clip(RNE(T/2^(16+k)),0,2^24).
The independent reference must compare this approximation to exp on >=4097
grid points and range boundaries with <=2 Q0.24 units error.

## Storage, benchmarks and reproduction

Production ternary weight count=2,084,044,800. Row-padded radix bytes=416,855,040;
signed-two-bit bytes=521,011,200. Tied BF16 embedding=656,670,720 bytes.
Metadata, bus padding, cache and working storage are additional. No complete
model or persistent KV cache may be replicated in FPGA registers.

Official checkpoint importer must translate offset/output-row-interleaved
checkpoint codes, preserve learned multiplicative scales and tied BF16
embedding/head, independently round-trip tails and cross-tile carry.
Official weights/tokenizer, pinned evaluation datasets and isolated HumanEval
executor are not supplied. Missing assets are explicit unmet prerequisites,
not passing zero-sample benchmarks.

Independent L1 entry is `python3 tests/verify.py`, with admitted selectors:
`leaves`, `integration --seed 17|89|203`, `production-geometry`, `mutations`,
`synthesis`, `benchmarks --backend verilator --compact`, `portable-reproduction`.
These commands are a required Verifier deliverable, not implemented or run by
Designer. Tool dependencies: Python 3, Icarus/vvp with SystemVerilog 2012,
Verilator and Yosys; actual versions must be captured by independent execution.
Do not install tools implicitly.
L1 includes real compiled behavior, independent exact numerical comparisons,
required surviving-defect rejection and real synthesis/no-latch checks.
Icarus is bounded compact portability only; Verilator runs larger matrices.
Runtime-native timing lint, Quartus 17.1 STA and three consecutive deterministic
PCIe Gen3x8 physical passes remain mandatory and are not L1 substitutes.

The five domains are GSM8K test final-answer exact match, HumanEval test greedy
pass@1 with official isolated tests, MMLU test accuracy, BoolQ validation accuracy
and HellaSwag validation length-normalized continuation likelihood accuracy.
Production qualification uses two canonical-ID-ordered official items/domain,
zero-shot deterministic greedy, EOS stopping, GSM8K<=256 and HumanEval<=512
generated tokens, with truncations disclosed. The runner must support complete
splits. All candidates use actual model likelihood. Compact L1 scores are only
functional benchmark plumbing, not official model accuracy.
