# Phase 2 official weights and software-versus-RTL evaluation

## Status, ownership and scope

This is the design-side mapping and evaluation contract, not a result report.
The authoritative bounded-slice rule defines Phase 2 acceptance on the mounted
54-tensor extraction, not an unmounted full checkpoint. Acceptance covers all
14 official 64x64 projection submatrices and a four-token, two-layer top-level
forward pass. This document specifies the mapping and independent verification
method; measured results belong to the source-bound execution receipts.
Repository intake is null; there is no linked intake source index. Historical
parent acceptance does not certify this revision.

Designer preserves `rtl/*.sv` and `design/SPEC.md`; no concrete official-format
integration defect was identified by this inspection. The existing top consumes
raw packed I32 and binary16 model words over its external memory interface.
Verifier owns implementation in `tests/*.py`, independent references, public-pin
simulation, sensitivity, synthesis and evidence. The existing `floating_stack`
uses fixed-point-converted model data and is not the official FP32 baseline.
The methodology here specifies its independent replacement/additional path,
not an assertion that that path is already implemented.

The retained design is one active token, one reused decoder engine, eight
connected GEMV lanes and one outstanding external-memory transaction. No
model/context-sized internal array, layer bypass, host arithmetic, new top port,
Q8.8 mode or configuration shortcut is introduced. Defaults remain
`L=24,H=896,I=4864,QH=14,KVH=2,D=64,G=128,AWQ_BITS=4,V=151936,SEQ=32768`.
The exact ports, hierarchy, scratch slots, parameter checks, pre-edge/post-edge
table and integer equations remain in [SPEC.md](SPEC.md) and
[ARCHITECTURE.md](ARCHITECTURE.md).

## Authoritative inputs and bounded coverage

All paths are relative to the delivered project root:

| Input | Purpose |
| --- | --- |
| `hf_qwen25_05b_awq_spec/config.json` | Model dimensions, AWQ GEMM G128, epsilon, RoPE and tied embedding configuration |
| `hf_qwen25_05b_awq_spec/qwen25_05b_awq_tensors.json` | Original 627-tensor shape/offset manifest, including 168 quantized linear modules |
| `hf_qwen25_05b_awq_spec/official_weights/official_weights_manifest.json` | 54 extracted tensor entries, original/loaded shapes, inclusive HF byte ranges and SHA-256 digests |
| `hf_qwen25_05b_awq_spec/official_weights/qwen25_05b_awq_official_slice.safetensors` | Actual extracted F16/I32 payloads to parse and serve |
| `hf_qwen25_05b_awq_spec/official_weights/official_hardware_slices_fp16_awq.json` | Raw-hex excerpts to cross-check against parsed coordinates, not replacement tensor data |
| `hf_qwen25_05b_awq_spec/official_layer0_awq_slice.json` | Retained parent submatrix witnesses, with their original partial/synthetic labels |

The extracted-file expected SHA-256 recorded in the supplied manifest is
`f274ceb6f71ac3a9dd0f10ad68007da8dedfd102ac129b12411b26f885a67ef0`.
This recorded value is not a newly verified digest.

The manifest declares the following coordinate coverage, with upper bounds
exclusive:

| Tensor family | Supplied coordinates | Missing for complete execution |
| --- | --- | --- |
| `model.embed_tokens.weight` | `[0:64,0:896]` | Rows `[64:151936]`, also needed for tied logits |
| `model.norm.weight` | `[0:896]` | None declared |
| Layers 0 and 23, both norms and Q/K/V biases | Full original shapes | None declared for these tensors |
| Layers 0 and 23, all seven qweight tensors | Input rows `[0:64]`, all original packed output columns | Rows `[64:896]` for Q/K/V/O/gate/up; `[64:4864]` for down |
| Layers 0 and 23, all seven qzeros/scales tensors | Full original group/output shapes | None declared for metadata; this does not supply missing qweight rows |
| Layers 1 through 22 | No extracted tensors | Both norms, three biases and all seven qweight/qzeros/scales triplets per layer |

Each decoder layer requires 26 tensors: 21 quantized tensors, three biases and
two norms. Thus layers 1..22 lack 572 tensors. The original manifest's separate
`lm_head.weight` is also not extracted; report its absence in the original
627-entry inventory, but do not require a duplicate head for configured tied
execution or claim its unseen contents equal embedding contents.

The full-model inventory remains in the report as context, not a bounded-slice
acceptance blocker. No missing weights are manufactured, padded or repeated.
Unknown model addresses still fail with tensor name and coordinate. Do not
download, install tools or modify authoritative inputs. The resulting experiment
is official-slice inference, not a claim of full 24-layer checkpoint inference.

The standalone sweep uses each of the seven projections in original layers
0 and 23, input rows `[0:64]`, output channels `[0:64]`, packed columns `[0:8]`,
and original metadata group zero. Its G64 hardware fixture visits precisely
the same metadata as original G128 for these input rows. All 14 commands must
complete, comparing 57,344 products and 896 ordered output writes.

The end-to-end tuple, ordered as `(L,H,I,QH,KVH,D,G,V,SEQ)`, is
`(2,56,56,14,2,4,56,64,4)`. Hardware layer 0 maps to checkpoint layer 0 and
hardware layer 1 maps to checkpoint layer 23. Embedding/tied logits use rows
`[0:64]`, components `[0:56]`; both layer norms and final norm use components
`[0:56]`. Every projection uses input rows `[0:56]`; Q/O/gate/up/down use
output channels `[0:56]` (packed columns `[0:7]`), while K/V use channels
`[0:8]` (packed column zero). Bias channels match their projections.
All metadata uses original group zero, identical under hardware G56 and original
G128 for these rows. The fixture retains 14:2 / 7:1 GQA with head dimension 4,
all seven projections, both decoder residuals, both norms, SwiGLU, causal KV,
split-half RoPE and final tied projection. There are no skipped configured
layers, synthetic model values, host arithmetic outputs or RTL changes.

## Raw-file validation and coordinate binding

Use Python standard library only (`struct`, `math`, `json`, `hashlib` and
supporting standard modules), without numpy or an external tensor loader.
Before executing official data, verify the extracted-file digest. Parse the
actual eight-byte little-endian unsigned header length, header JSON and payload.
Reject duplicate JSON tensor names, malformed/truncated headers, unsupported
dtypes, invalid dimensions, shape/byte-length mismatches, out-of-bounds or
overlapping tensor spans and invalid metadata structure. Safetensors
`data_offsets` are half-open and relative to the payload after the header,
not absolute HF file offsets.

Require exactly the 54 declared extracted tensor entries with matching
F16/I32 dtype and loaded shape; check every tensor payload digest. Validate
original shapes against the original 627-tensor manifest and configured 168
linear modules. For each inclusive HF range `[a,b]`, require
`b-a+1 = product(loaded_shape)*element_bytes` and verify it identifies the
declared prefix inside the original tensor span. The original HF payload
base declared by this manifest is `8+68432=68440` bytes. Do not use that original
base as the extracted file's payload base; parse the latter's own header.
Loaded shapes here are leading row prefixes with complete trailing dimensions,
not arbitrarily compacted submatrices.

For a parsed tensor with shape `[R,C]`, element `(r,c)` resides at
`extracted_payload_base + tensor_start + element_bytes*(r*C+c)`;
for `[C]`, use `element_bytes*c`. Bounds must use loaded shapes before access.
Decode I32 with little-endian signed interpretation while preserving
`word & 0xffffffff` for nibble extraction and the bus. Decode F16 directly
with `struct.unpack('<e', raw_two_bytes)`; retain the exact halfword as well.
Do not take rounded decimal JSON values as arithmetic inputs. Cross-check
every available excerpt `raw_hex` at its matching tensor coordinates.
Keep storage-bit identity, arithmetic conversion and coverage checks distinct.

## Public memory address to checkpoint coordinate

Let `P(layer,proj)` be the following unmodified official tensor prefix:

| proj | Prefix suffix after `model.layers.<layer>.` | N -> M |
| --- | --- | --- |
| 0 | `self_attn.q_proj` | 896 -> 896 |
| 1 | `self_attn.k_proj` | 896 -> 128 |
| 2 | `self_attn.v_proj` | 896 -> 128 |
| 3 | `self_attn.o_proj` | 896 -> 896 |
| 4 | `mlp.gate_proj` | 896 -> 4864 |
| 5 | `mlp.up_proj` | 896 -> 4864 |
| 6 | `mlp.down_proj` | 4864 -> 896 |

Every accepted model read uses this single mapping. All model accesses are
read-only, read `wdata` is zero, and unused fields remain zero as in SPEC.
The table uses physical checkpoint layer numbers. The standalone sweep uses
literal layers 0/23; the top fixture translates logical layers 0/1 to physical
layers 0/23 before applying this table. The identical explicit coordinate view
is used by both independent arithmetic models and the raw-file RTL memory service.

| kind | Bus fields | Parsed checkpoint element returned |
| --- | --- | --- |
| 0 embedding/tied output | layer=0,proj=0,row=r,col=c | `model.embed_tokens.weight[r,c]` |
| 1 qweight | layer=l,proj=p,row=k,col=j | `P(l,p).qweight[k,j]` |
| 2 qzeros | layer=l,proj=p,row=g,col=j | `P(l,p).qzeros[g,j]` |
| 3 scales | layer=l,proj=p,row=g,col=c | `P(l,p).scales[g,c]` |
| 4 bias | layer=l,proj=Q/K/V,row=0,col=c | `P(l,p).bias[c]`; no O/MLP bias |
| 5 input norm | layer=l,proj=0,row=0,col=c | `model.layers.l.input_layernorm.weight[c]` |
| 6 post norm | layer=l,proj=0,row=0,col=c | `model.layers.l.post_attention_layernorm.weight[c]` |
| 7 final norm | layer=0,proj=0,row=0,col=c | `model.norm.weight[c]` |

Kinds 1/2 return the original full 32-bit packed word. F16 kinds return the
original halfword in bits `[15:0]` with upper bits zero; the memory service
must not preconvert it. Logical output `c` selects packed column `c//8` and
shift `[0,16,4,20,8,24,12,28][c%8]` in both words. Input `k` selects metadata
group `k//128`. Both implementations use `w=(q-z)*s`, never GPTQ `z+1`.
Tied vocabulary reads use kind 0 and the same immutable embedding storage.

Kinds 8/9/10 are independent mutable scratch/K/V storage with acknowledged
writes, using SPEC's slots and addresses, not checkpoint aliases. Kind 11
provides independently generated Q2.30 RoPE coefficients at row=position,
col=`2*i+cos_or_sin`, for head-local split-half pair i. It cannot provide layer
outputs. Each read or write receives exactly one strictly later response;
request/response transfer never coincides. Preserve frozen stalled payloads,
reset handling, errors, cache causality and public completion semantics.

## Independent numerical paths

The immutable checkpoint coordinate resolver is shared data access, not shared
arithmetic. The integer oracle independently implements SPEC's exact equations:
ordinary finite F16 to signed-32 Q16.16 with nearest/ties-away and saturation;
unsaturated unsigned-32 scales; exact signed-37 dequantization, signed-69
products and signed-128 complete GEMV sums including bias before final rounding.
Keep signed-96 tied reductions, all existing nonlinear widths, zero-denominator
errors and saturation boundaries. Do not reuse RTL helper calculations.

The official software baseline is raw-F16-derived FP32, not fixed-point data
converted back to floating point. Define `f32(x)` by little-endian
`struct.pack/unpack('<f')`, IEEE round-to-nearest/ties-to-even. Decode finite F16
exactly, then promote to FP32. Round every elementary add, subtract, multiply
and divide result to FP32; use separate multiply and add (no FMA). Reduce in
increasing component/input/time order with a zero FP32 accumulator. For GEMV,
round `(q-z)*s`, then each activation product and accumulator addition; add
raw-F16 bias after the complete reduction. These operation boundaries differ
deliberately from the exact fixed-point sum, not from checkpoint coordinates.

For RMSNorm, round each square and sum, division by H, addition of `f32(1e-6)`,
sqrt, then `f32(f32(x*gamma)/denominator)`. Generate floating RoPE angles as
`f32(position * math.pow(1000000.0, -2*i/D))`, round `math.cos/sin` to FP32,
and round each rotation product and sum/difference. Transcendental functions
and sqrt use host `math` followed by explicit FP32 rounding; record Python and
platform details. This is a specified software operation order, not a claim
to reproduce an unspecified GPU kernel or correctly rounded FP32 libm.
Do not feed Q2.30 coefficients into the floating baseline.

Round attention dot products and reductions, divide by rounded sqrt(D), and
use max-subtracted softmax. Round score subtraction, exp, denominator sum,
probability division, weighted products and increasing-time sums. Implement
stable SiLU: for x>=0 use `x/(1+exp(-x))`; otherwise use `x*exp(x)/(1+exp(x))`,
rounding each operation. Round SwiGLU product, both residual additions and
the final norm/tied projection. Required nonfinite model data, arithmetic
overflow and invalid denominators fail explicitly, not with clipped floats
or a success-shaped default. A binary64 supplementary run must be labeled
separately; it is not the FP32 baseline.

Execute embedding, both configured decoder layers, both RMSNorms per layer,
all seven AWQ projections, QKV biases, 7:1 GQA, split-half theta=1e6 RoPE,
causal actual KV history, both residuals, SwiGLU, final RMSNorm and all 64
configured tied logits.
Use at least two prefill tokens followed by two sequential decode tokens.
Record initial IDs and roles; choose decode IDs by the preceding official
floating logits' argmax, ties to the lowest index. Feed identical IDs and
positions to floating, integer and RTL paths. Report autonomous RTL greedy
agreement separately. Retain parent teacher-forced and new-sequence tests.

## Comparison, timing and retained evidence

Compile actual RTL with `iverilog -g2012 -Wall`, package first, then execute
the matching `vvp`. Drive public pins only. Compare every ordered scratch/KV
write and every transferred logit to the integer oracle. Require zero bit
mismatches, explicit compared-element denominators, completed-token counts and
successful final-logit/completion retirement. A timeout, early stop or an empty
comparison is never a zero-mismatch success.

The behavior command emits
`evidence/verification/functional/official_weights_comparison.json` and, after
the behavior check succeeds, the additional requested
`evidence/verification/official_weights_comparison.json`. The latter destination
must not already exist. Reports include the full inventory coverage but require
only the declared bounded slice. A passed official comparison requires both
the submatrix sweep and four successfully retired top-level tokens, nonempty
ordered-write/logit comparisons and retained numerical tolerances, with
`status="passed"` and `blockers=[]`. Failures retain their diagnostics; no
unexecuted measurements are invented. Label
the two sides exactly:
`Software Layer (Official HuggingFace FP32/FP16 AWQ Weights)` and
`Hardware RTL Output (Official HuggingFace W4A16 RTL Execution)`.
Here FP16 names checkpoint storage, FP32 names the software arithmetic above,
and RTL working arithmetic is Q16.16. Record source/checkpoint digests, parsed
coverage/missing coordinate ranges, configuration, mapping, precision order,
token IDs/positions/roles, stage diagnostics, saturation, per-token and aggregate
metrics, cycles and transactions. Unexecuted measurements are null with a reason,
not zero or a fabricated perfect score.

For real logits h=RTL/65536 and f=software, report max and mean abs(h-f),
`sqrt(mean((h-f)^2))` RMSE and cosine `sum(h*f)/sqrt(sum(h*h)*sum(f*f))`.
Cosine is null with an undefined reason if either norm is zero. Use K=5,
descending logits with ascending-index ties: top1 index agreement, top5 set
intersection size/5 and exact top5-set agreement. Retain per-token results and
state aggregate reduction/denominators; metrics can use binary64 postprocessing,
which is not the forward arithmetic. Cosine/ranking have no invented thresholds.

Retain numerical limits: exp max absolute error <=3e-5; isolated nonsaturating
RMSNorm/RoPE/SiLU/attention <=2/256; nonsaturating final-normalized components
<=16/256; each nonsaturating logit error <=16/256+0.01*abs(f). Keep extreme and
saturating coverage separately rather than applying nonsaturating limits to
clipped values. Preserve B17/B89 witnesses and all A/B/C/D seeds 17,43,89,
raw vectors, RNG order, submatrix tests and wide-arithmetic witnesses.

Number observed rising edges. If A is public token acceptance and F is the
final transferred logit, define token latency as F-A elapsed edge intervals.
The post-F completion is observed at the next sampling edge T; record T-A
retirement latency separately. Record both endpoint indices and convention.
Count requests only on pre-edge valid&&ready, responses/acknowledgements
separately, partitioned by token, kind, read/write, layer and projection.
Report cycles/token and request/response/logit stalls. Keep any no-stall
baseline separate from observed stalled timing. Simulation wall time is not
silicon throughput; no clock frequency is implied.

Retain public protocol/reset/errors/active-X/Z checks, causal/future-cache
poison, illegal parameters and commands, mandatory singleton behavior,
all existing defect mutations and actual A/B/C/D Yosys lowering/check/no-latch
and connected-hierarchy inspection. Provenance corruption, malformed-file and
missing-coverage sensitivity fixtures are disposable copies, never changes to
authoritative inputs. A mutation kill requires successful compilation and the
intended assertion, not timeout or compile failure. Require warning-clean
default/A/B/C/D elaboration and matched Icarus12/13 runtimes; unavailable tools
remain blockers without installation or waiver.

## Commands and independent handoff

The admitted commands below are instructions for Verifier/shared-runtime
execution after implementing the verification changes, not commands executed
by Designer. Output destinations must be fresh; refuse occupied paths without
overwriting, deleting or automatic suffix retries. A different destination
requires a new admitted command.

```sh
python3 tests/verify.py --check behavior --out evidence/verification/functional
python3 tests/verify.py --check behavior --probe mutations --out evidence/verification/sensitivity
python3 tests/verify.py --check synthesis --out evidence/verification/synthesis
python3 tests/verify.py --check portability --out evidence/verification/portability
```

The existing `--probe official` behavior selector runs a focused preparation
check of raw provenance, malformed-input sensitivity, all official submatrices
and the four-token top fixture. Preparation results are advisory, not admitted
engineering acceptance; the complete commands above remain runtime obligations.

Normal functional/synthesis child limits are at least 3600 seconds within the
shared runtime's admitted envelope, replacing historical tight watchdogs, not
functional thresholds. Do not run old execution-cost microprofilers. Retain exact
argv/cwd, resolved tool paths/versions, start/end times, timeout/exit, source
hashes or snapshots, seeds, raw stdout/stderr, assertions and process settlement.
Hash nested official inputs as well as RTL, tests, design and root model JSONs.
Preserve failed receipts and repair links. Preparation diagnostics are advisory;
none were run for this documentation handoff. Do not edit runtime-owned metadata
or historical evidence. The final product report is authored by the shared
runtime after engineering acceptance, never a prerequisite for these checks.
