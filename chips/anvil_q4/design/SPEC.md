# Anvil-Q4 design contract

## Authority and implementation status

The independently admitted work order is the acceptance contract. This document
records its design-facing interfaces; it does not waive any numerical, coverage,
timing, hardware or independent-review requirement. The implementation is in
progress. The source inventory in ARCHITECTURE.md distinguishes implemented
components from outstanding integration. No verification or timing acceptance is
claimed.

The supplied `anvil_q3_reference/rtl/` is architectural reference, not a numerical
oracle, and must remain unchanged. No linked repository-intake source index was
provided. The requested `design/GENERATIONAL_HANDOFF.md` was not supplied, so
parent post-synthesis timing and PPA are unknown.

## Cycle and degenerate-boundary table

All design sequential processes use rising-edge clocks and active-low
asynchronous reset. A transfer uses the ready/valid values immediately before
the edge; register updates are observable immediately after the edge.

| Boundary | Required behavior |
|---|---|
| Active reset | All public outputs, including ready, payload and status, are zero. Reset discards outstanding transactions; the bridge must reset its transaction epoch too. |
| Reset release | No invented transfer. Internal descriptor state starts at the Q4 reset image, not a legacy profile. |
| Idle token accepted at E0 | Capture after E0; first memory request visible no earlier than after E1, transferring no earlier than E2. |
| Stalled request/result | Valid and every payload field remain unchanged until the accepting edge, except reset/cancellation suppression. |
| Request and response at one edge | Legal for the same accepted request. Captured response data cannot affect another transfer at that edge. |
| Final logit accepted at F | `done` is one cycle immediately after F. `token_ready` is zero throughout that completion cycle. Vocabulary one obeys the same rule. |
| Configuration commit accepted at C | The commit does not write a word. `cfg_done` and, on rejection, `cfg_error` pulse after C+1. A failure preserves the active image. |
| Shadow-word write | Shadow-derived validation may deassert `cfg_ready` while it recomputes. A commit is accepted only when this recomputation is complete. |
| Cancellation | Takes priority over configuration/token/draft acceptance; suppress new requests/results, drain accepted requests, invalidate the sequence, pulse `cancel_done`; an interrupted command also completes once with error. |
| Queue depth one | One ownership slot; explicit wrap to zero. A held returned response still owns its slot until consumed. |
| Queue depth three | Explicit `depth-1` wrap, never binary-overflow wrap or a power-of-two mask. |
| Simultaneous retire and allocate | Distinct ownership transitions. A slot retired at an edge is not reused by a request already offered before that edge. |
| Coincident request/response | A response may match a request that handshakes at that edge; a response to an unaccepted offer is a protocol fault. |
| Flush with allocation/response | Flush suppresses new allocations and drops client delivery, but accepted transactions remain owned until response drain. |
| One/16 banks | No invalid-width bank indices. Bank 15 is distinct from bank 7. |
| Tile K one/seven; rows one/three | Explicit tails and masks; these do not redefine legacy eight-channel packing. |
| D two, intermediate one, vocabulary one | Legal Q4 dimensions if the descriptor equations hold; no zero-length reduction or illegal array select. |
| Page tokens one | Page offset zero and logical page equals token position. |
| Failed commit | Old descriptor, sequence and prediction remain unchanged. Only the remembered invalid-index write fault clears. |

## Public top-level interface

The required top is `anvil_q4_top`, with physical parameters `BANKS` in
{1,2,4,8,16}, default 16; `QUEUE_DEPTH` 1..16, default 3; `TILE_K` 1..128,
default 128; `TILE_ROWS` 1..8, default 8. Illegal elaborations require explicit
`PARAMETER ERROR` diagnostics and diagnostic-safe widths/generate guards.

Retain `clk,rst_n,cancel,token_valid,token_ready,token_id[31:0],
token_pos[31:0],new_sequence,token_phase,logit_valid,logit_ready,
logit_index[31:0],logit_data[31:0],done,error,cancel_done`.
Q4 logits carry FP32 bits; legacy logits carry signed Q16.16 bits.
`error` is qualified by `done`.

Add configuration inputs `cfg_valid,cfg_commit,cfg_index[5:0],
cfg_wdata[31:0]` and outputs `cfg_ready,cfg_done,cfg_error`.
Add draft inputs `draft_valid,draft_token0[31:0],draft_token1[31:0],
draft_pos[31:0],draft_new_sequence,verify_ready` and outputs
`draft_ready,verify_valid,verify_accepted[1:0],verify_error`.
Normal tokens have priority over drafts. Legacy `draft_ready` stays zero.

For B banks, request valid/ready/write and response valid/error/ready have B
bits. Request kind has 4B bits, layer/row/col/wdata have 32B bits, projection has
3B bits and tag has 64B bits. Response rdata has 32B bits and tag has 64B bits.
Bank zero occupies the least-significant slice. Requests and responses are
unsigned bit vectors; all writes require responses too.

## Descriptor ABI

Shadow and active images reset identically. A non-commit transfer writes one
shadow word. Index >=32 records a sticky shadow write fault. A commit validates
the entire shadow image and atomically activates it, or rejects without changing
the active image. Rejection clears the invalid-index fault; reserved-word errors
remain until their shadow values are corrected. Successful activation requires
sequence, prediction and cache-epoch invalidation by the top-level controller.
`cfg_ready` requires no outstanding command, result, batch or memory transaction.

| Word | Meaning | Q4 reset |
|---|---|---|
| 0 | ABI version | 1 |
| 1 | Mode: Q1/Q2/Q3/Q4 = 1/2/3/4 | 4 |
| 2 | Activation format: Q4 BF16=0, FP16=1; legacy FP16 tables=1 | 0 |
| 3 | Weight format: Q4 native=0, W4=1, W8=2; legacy AWQ W4=1 | 1 |
| 4 | Activation quantization: A16=0, A8=1; legacy=0 | 0 |
| 5 | Mode-specific cache encoding | 0 |
| 6 | Active banks | BANKS |
| 7 | Layers | 28 |
| 8 | Hidden | 3584 |
| 9 | Intermediate | 18944 |
| 10 | Query heads | 28 |
| 11 | KV heads | 4 |
| 12 | Head dimension | 128 |
| 13 | Vocabulary | 152064 |
| 14 | Context capacity | 32768 |
| 15 | Quantization group size | 128 |
| 16 | QKV bias enable | 1 |
| 17 | FP32 RoPE theta | 0x49742400 (1000000) |
| 18 | FP32 RMS epsilon | 0x358637bd (1e-6) |
| 19 | Page tokens | 32 |
| 20 | Physical page count | 1024 |
| 21 | Weight zero convention: symmetric=0, unsigned asymmetric=1 | 1 |
| 22 | GQA ratio | 7 |
| 23 | Profile identifier (label, not geometry override) | 1 |
| 24 | Legacy cache block length; Q4 requires zero | 0 |
| 25..31 | Reserved, must be zero | 0 |

Common bounds: layers 1..64, hidden 2..8192, intermediate 1..32768, query/KV
heads 1..128, even D 2..256, vocabulary 1..262144, context 1..131072, group
1..128. Require hidden=Q*D, Q=ratio*KV, ratio in {1,3,6,7,8}. Reject overflow
and inconsistent geometry before memory traffic. Theta/epsilon must be positive
finite FP32, not signed zero, infinity or NaN. Q4 A8 requires W4/W8.
Q4 cache is BF16=0 or INT8=1; page tokens in {1,2,4,8,16,32}, pages
1..131072, with physical capacity covering context.

Legacy requires words 2/3/16/21=1 and word4=0. Hidden/intermediate must be
multiples of eight and divisible by group size; Q1/Q2 KV*D is a multiple of
eight; Q3 ratio is eight. Context <=32768, word19=1, word20=context and epsilon
exactly 0x358637bd. Legacy cache encodings are fixed32=0, INT8=1,
symmetric INT4=2, asymmetric INT4=3. Q1 permits only 0; Q2 permits 0/1; Q3
permits all four. Fixed32 always requires word24=1. Q2 INT8 permits power-of-two
word24 from 1 through D dividing D, including 256. Q3 INT8 requires 32 and
Q3 INT4 requires 64, including partial final head blocks. Legacy active banks
are 1/2/4/8 and no greater than physical BANKS.

Construct a legacy default image explicitly: start with ABI1, set mode and
the required legacy format words, cache0/block1, banks=min(BANKS,8), group128,
vocab151936, context32768, bias1, theta1000000, epsilon1e-6, page tokens1,
pages32768, asymmetric weight zeros1, all reserved words zero. Then set
Q1=(layers24,H896,I4864,Q14,KV2,D64,ratio7),
Q2=(28,1536,8960,12,2,128,6), or
Q3=(36,2048,11008,16,2,128,8). Set profile identifier to the host's public-table
label. None of these changes the Q4 reset mode.

## Numerical and memory boundaries

Q4 uses BF16/FP16 external scalar tables, FP32 scratch, reductions and residuals;
round-to-nearest ties-to-even, gradual underflow and canonical NaN 0x7fc00000.
Multiply then add is separate, in increasing input-index order, not FMA.
The arithmetic leaf ops are ADD0, SUB1, MUL2, DIV3, SQRT4, BF16 widening5,
FP16 widening6, BF16 narrowing7, FP16 narrowing8, signed-int32 conversion9.
Other opcodes return canonical NaN/invalid. Flags[4:0] are invalid,
divide-by-zero, overflow, underflow, inexact. Single-issue acceptance at E
produces ADD/SUB/MUL after E+8, conversions after E+2, DIV/SQRT after E+64.
Hold outputs under backpressure; flush annuls work and reopens the next cycle.

Projection codes: Q0,K1,V2,O3,gate4,up5,down6. Q4 kinds: embedding/lm-head0,
weight1,zero2,scale3,bias4,attention gamma5,FFN gamma6,final gamma7,scratch8,
BF16 K9,V10,RoPE11,INT8 K12,V13,scale metadata14,page table15.
Kind0 proj0 is embedding and proj1 is lm-head; legacy kind0 uses proj0 for both.

Let H=hidden, I=intermediate, KD=KV*D, G=group, M=max(H,I).
Projection input Kp is I for down and H otherwise. Output Op is KD for K/V,
I for gate/up and H otherwise. Q4 weights have row=output channel,
col=packed input word with stride ceil(Kp/P), P=native1/W4 8/W8 4.
Zero/scale rows are output channel and columns input group, stride ceil(Kp/G).
Zeros occupy low4/8 bits; scales are positive finite FP32.
W4 lane offsets are [0,16,4,20,8,24,12,28]; W8 bytes ascend from LSB.
Asymmetric zeros encode z directly. Dequantize FP32(q-z)*scale, narrow once
to BF16, then widen for native arithmetic. Signed symmetric modes sign extend.
A8 uses per-tile maxabs/127, zero scale1, RNE codes [-127,127], then BF16.
Mask tails before metadata access or arithmetic.

Q4 kind strides are C0=H; C4=Op; C5/6/7=H; C8=M; C9/10=KD;
C11=D; C12/13=ceil(KD/4); C14=KV; C15=1.
Q4 physical bank = (row*Ckind(proj)+col)&(active_banks-1).
The full semantic identity is
J=(kind<<99)+(layer<<67)+(proj<<64)+row*Ckind(proj)+col.
Only the low bank-index bits need hardware arithmetic. Semantic coordinates
must not be rewritten into this flattened index.
Legacy bank=(kind+layer+proj+row+col)&(active_banks-1), preserving full tuple
identity separately. Never route by tag. These formulas are deliberately
different.

Scratch always has kind8, layer0,proj0,row=slot,col=vector index:

| Slot | Vector | Extent |
|---|---|---|
| 0 | Current residual, initialized from embedding | H |
| 1 | Attention RMS output | H |
| 2 | Q, overwritten by RoPE | H |
| 3 | K, overwritten by RoPE | KD |
| 4 | V | KD |
| 5 | Concatenated contexts | H |
| 6 | O | H |
| 7 | Post-attention residual | H |
| 8 | FFN RMS output | H |
| 9 | Gate | I |
| 10 | Up | I |
| 11 | SiLU(gate)*up | I |
| 12 | Down | H |
| 13 | Reserved, no public access | None |
| 14 | Final RMS output | H |

No slots >=15 or padded-column accesses. Q4 scratch is FP32, legacy Q16.16.
Scratch is a single-command workspace, never committed KV history.

Q4 page kind15 uses layer=sequence epoch,row=logical page,col0,proj0.
Bit31 is valid, bits30:0 physical page. Payload row=physical_page*page_tokens
+offset; payload layer=decoder layer. BF16 cache is always BF16, even for FP16
activations. INT8 bytes pack across head boundaries; preserve shared words and
mask final padding. Kind14 stores independent FP32 K/V per-head scales using
proj0/1. Detect absent/out-of-range/aliased pages and stale epochs.
RoPE kind11 has layer=descriptor generation,row=position,col=2*d/2*d+1;
legacy coefficients retain layer0 and signed Q2.30.

Legacy AWQ kind1 row=input channel,col=output>>3; kind2 row=input group,
col=output>>3; kind3 row=input group,col=output channel, FP16 scale.
Packed weights/zeros use the same eight-lane offsets listed above.
Unquantized cache kind9/10 carries original Q16.16 bits at row=logical position,
col=head*D+dimension. Quantized cache uses payload12/13 and K/V metadata14/15,
never a Q4 page table. With Cb=word24, B=ceil(D/Cb), W=ceil(Cb*bits/32),
payload col=(head*B+block)*W+word; metadata col=head*B+block.
INT8 uses ascending signed bytes; INT4 ascending signed nibbles; padding zero.

For legacy symmetric caches select e from the **unrounded** max magnitude A:
smallest e with A<=L*2^e, L127/Emax25 for INT8 or L7/Emax29 for INT4.
Then signed-magnitude halfway-away-from-zero rounding encodes each scalar.
INT8 raw +/-509 therefore gives e3,codes +/-64,reconstruction +/-512;
symmetric INT4 raw +/-29 gives e3,codes +/-4,reconstruction +/-32.
Asymmetric INT4 instead selects the first e0..32 permitting rounded extrema
plus canonical z in [-8,7] to fit [-8,7]. Do not apply rounded-fit selection
to symmetric caches. Metadata low8=e, Q3 bits11:8=signed z, other bits zero.
Reject forbidden codes, padding, reserved bits and noncanonical metadata.

## Required processing and acceptance

Hardware must perform embedding, every configured decoder layer, final norm and
complete vocabulary projection. Decoder stages are RMSNorm, QKV, split-half
RoPE, causal GQA including current token with max-subtracted softmax, O,
residual, FFN RMSNorm, SwiGLU, residual. QKV bias is descriptor-gated;
O/FFN remain bias-free. GQA groups contiguous ratio-sized query heads.
Two-token greedy speculative verification commits only the accepted prefix;
ties choose the lowest vocabulary index. No host activation oracle or empty
hierarchy substitute is allowed.

Independent Verifier owns tests, exact IEEE/integer models, numerical comparisons,
defect injection, five-domain benchmarks and generic synthesis. All eight
admitted L1 checks remain mandatory. The shared runtime owns timing lint,
Quartus 17.1 STA at <=10 ns with WNS>=0, and Arria 10 GX Gen3x8 board HIL
with at least three deterministic passes. No combinational datapath division or
modulo, mixed blocking/nonblocking sequential assignments, latches or DUT real
math is permitted. A static compiler result is not numerical or timing evidence.
Product PDF generation follows engineering acceptance and is runtime-owned.
