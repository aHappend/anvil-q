# Anvil-Q1-FP architecture and preservation ledger

## Current source boundary

The native arithmetic foundation, scalar kernels, dual-mode command
operators and complete top-level hierarchy are implemented in `rtl/`.
Target constraints are in `fpga/`. This is a Designer handoff, not an
accepted accelerator. Functional, numerical, compatibility, synthesis,
timing, benchmark and hardware checks remain independent acceptance work.
No verification/synthesis/hardware result is claimed.
`SPEC.md` freezes the admitted boundary semantics before RTL is written.

### Frontend portability repair

The independent synthesis attempt retained at
`evidence/preparation/verifier-synthesis-dot-03dkf_yp/receipt.json`
failed during RTL parsing at the first `integer'(...)` cast, before
synthesis or latch analysis. The native arithmetic package and exp
range reduction now express every such cast as `$signed(32'(...))`.
The sized cast extends signed operands with their sign and unsigned
operands with zeros, then `$signed` preserves the original signed
32-bit integer interpretation. This changes no arithmetic widths,
rounding, pipeline stages or interfaces. Independent numerical
revalidation and Yosys synthesis remain required; the retained
pre-repair leaf comparisons do not validate the repaired sources.

No linked repository intake source index was supplied in the work order or
the visible reference tree. The tree contains the thirteen RTL files below
and no checkpoint, tokenizer, AWQ artifact or benchmark corpus. Their
presence is provenance only. This inventory was obtained before creating
deliverable RTL; reference files remain read-only.

## Immutable parent source inventory

Paths in this table are relative to `anvil_q1_reference/rtl/`.

| File | Lines | SHA-256 |
| --- | ---: | --- |
| anvil_q1_00_pkg.sv | 106 | 0402e27ea553398cad6464ce72f71c0e4fc47e61c2455f958fb5393a82f70bb5 |
| anvil_q1_awq_dequant.sv | 38 | 288100e05780872313a9d2f485213959fc5809f56aae4b2c0d22cc61f8c91537 |
| anvil_q1_bus_mux.sv | 35 | 9b41a1c242c344871258f0ba9d861e669cb1688f4b5fb2a46818b729251c2af7 |
| anvil_q1_decoder_layer.sv | 107 | 2fc6e519adde2b04fc2c48e9dbd8968d5d212ff692514f4a822ea15cc4ad5f0b |
| anvil_q1_elementwise.sv | 91 | 07c092ddf26bd21053bed2996880bb38cdd22e7d9914fd6bfa3ff2fdf5dbe793 |
| anvil_q1_gqa_attention.sv | 151 | d0d1c9ebd91967347d4f4bb7c5f0b6b859a2876f945ac1e53def23617ca12edb |
| anvil_q1_mem_port.sv | 49 | fc0b18df80b47572561fd8c8018d465856405a224c03640137d791d0c90b4561 |
| anvil_q1_parameters.sv | 27 | 2d0f084668ac9ed561da2978c10eade6adf142c4ba9673f5bfc3d963755968f9 |
| anvil_q1_rmsnorm.sv | 113 | f97472325fb321ceb39f7c8c9f44f0a8910b9f4ad4ad26a6b7e4b6ccae0666fd |
| anvil_q1_rope.sv | 97 | ccc1066da5f6ab98d43cb408eda6de9c2c7ffc1598c479f25e4636380f81daf2 |
| anvil_q1_swiglu_mlp.sv | 75 | 0e944b6e7bbbaaa28394432f449c50a966d6c3245ede6cf2a0ab6da05a20a4ce |
| anvil_q1_top.sv | 151 | b95e15d3f67d336d91a31b9edb467e9fef6d8171faa11dbc8aa760f06c9114ef |
| anvil_q1_w4a16_gemv.sv | 183 | 86b9aaf74d99ca167e6370a3952739c1093f87f9eb03a1af623e279ff9ef3630 |

Reproduction: `sha256sum anvil_q1_reference/rtl/*.sv`.
No prior acceptance, timing closure or numerical result is inferred.

## Preservation denominator and mapping

The complete original inventory comprises every conditional transition
edge (including holds, reset, fault and default recovery), and every
non-arithmetic control action in top, decoder, MLP, attention, RoPE,
RMSNorm, elementwise, GEMV and memory port. Source hashes above fix the
denominator before implementation. IDs have the form
`module/state/condition/action`; a branch with several assignments
contributes each control assignment separately. Arithmetic expressions
alone are excluded, not the address, counter, ownership or completion
actions surrounding them. Combinational request routing and command
selection are included. Added pipeline states do not increase the
original denominator. Holds are explicit self-edges where a state waits
without a handshake; an unassigned control register holds its value.

The tables below enumerate the entire original state inventory, branch
conditions, edges and associated actions. The classification rule and
exhaustive override tables in "Completed control-preservation mapping"
assign every inventoried edge and control action to retained (R),
equivalent after arithmetic-wait retiming (E), or changed (C).
Each assignment within a grouped row remains a separate denominator item;
neither grouped rows nor added states are a percentage denominator.
Verifier must independently expand and count the complete original inventory
and audit the mapping against both source trees. The Designer mapping is
not an executed >=85% preservation result.

### Common controls and memory port

Every module's synchronous reset, input gating, terminal-state exit and
default state recovery are part of the inventory, including public
ready/done/error decodes. Bus requests are zero during reset.

| Parent state/condition | Original edge/actions |
| --- | --- |
| mem_port reset | state=0; clear wr,kd,pj,ly,rw,cl,wd |
| mem_port 0, issue | Capture write/kind/proj/layer/row/col/data; ->1 |
| mem_port 0, !issue | Hold idle |
| mem_port 1, ready / !ready | ->2 / hold request and all captured fields |
| mem_port 2, rsp_valid / !rsp_valid | ->0, complete and conditional fault / hold outstanding |
| mem_port default | ->0 |
| mem_port decodes | idle at 0; req_valid at 1; rsp_ready/complete at 2; rdata only on complete; fault=complete&&rsp_error |
| bus active | rst_n&&select<N; route selected full request, readiness and response only to selected client |
| bus inactive | Zero request, response readiness and every client response/ready |

### Top

| Parent state/condition | Original edge/actions |
| --- | --- |
| reset | state=0, failed=0, sequence_valid=1; clear token,position,next_position,component,vocabulary,layer |
| own_fault | failed=1, sequence_valid=0; ->31 |
| 0 token_valid, invalid token/position/new-sequence/continuation | failed=0 then 1; ->30 |
| 0 token_valid, legal | latch token/position; component,vocabulary,layer=0; ->1 |
| 0 !token_valid | Hold idle |
| 1 issue / !issue | Embedding read kind0, row token, col component; ->2 / hold |
| 2 complete invalid FP16 | failed=1, sequence_valid=0; ->31 |
| 2 complete legal / !complete | Capture activation; ->3 / hold |
| 3 issue / !issue | Scratch write kind8 slot0 component; ->4 / hold |
| 4 complete, more components | component++; ->1 |
| 4 complete, last / !complete | ->5 / hold |
| 5 ready0 / !ready0 | Issue decoder command with layer/position; ->6 / hold |
| 6 finished0 fault | failed=1, sequence_valid=0; ->31 |
| 6 finished0 more layers | layer++; ->5 |
| 6 finished0 last / !finished0 | ->7 / hold |
| 7 ready1 / !ready1 | Issue final norm mode2, layer0, position; ->8 / hold |
| 8 finished1 fault | failed=1, sequence_valid=0; ->31 |
| 8 finished1 legal / !finished1 | component,vocabulary=0; ->9 / hold |
| 9 issue / !issue | Read scratch slot14 component; ->10 / hold |
| 10 complete / !complete | Capture activation; ->11 / hold |
| 11 issue / !issue | Read tied kind0, row vocabulary, col component; ->12 / hold |
| 12 complete invalid FP16 | failed=1, sequence_valid=0; ->31 |
| 12 complete legal / !complete | Accumulate product; ->13 / hold |
| 13 more components / last | component++, ->9 / ->15 |
| 15 logit_ready, more vocabulary | vocabulary++; component=0; ->9 |
| 15 logit_ready, last | next_position=position+1, sequence_valid=1; ->31 |
| 15 !logit_ready | Hold logit/index/data |
| 30 / 31 / default | ->31 / ->0 / ->0 |
| decodes | token_ready at 0, logit_valid at 15, done at31, error=done&&failed; decoder bus at5/6, norm bus at7/8, own bus otherwise |

### Decoder

| Parent state/condition | Original edge/actions |
| --- | --- |
| reset | state,step,failed,layer,position=0 |
| 0 cmd_valid invalid / legal | latch layer/position, failed=0, step=0; invalid sets failed, ->4 / ->1 |
| 0 !cmd_valid | Hold idle |
| 1 selected ready / !ready | Command selected child, ->2 / hold |
| 2 selected finished fault | failed=1; ->3 |
| 2 selected finished, step10 | ->3 |
| 2 selected finished, other | step++; ->1 |
| 2 !finished | Hold step, selection and child ownership |
| 3 / 4 / default | ->0 / ->3 / ->0 |
| decodes | cmd_ready at0, done at3, error=done&&failed |

Step-to-selection/actions (all original command actions are inventoried):
0 norm/mode0; 1 gemv/Q; 2 gemv/K; 3 gemv/V; 4 rope;
5 attention; 6 gemv/O; 7 residual/mode0; 8 norm/mode1;
9 MLP; 10 residual/mode1. All children receive latched layer/position.

### MLP

| Parent state/condition | Original edge/actions |
| --- | --- |
| reset | state,failed,layer,position=0; projection=4 |
| 0 cmd_valid invalid / legal | latch layer/position, projection=4, failed=0; invalid failed, ->14 / ->1 |
| 0 !cmd_valid | Hold |
| 1 ready0 / !ready0 | Issue gate GEMV; ->2 / hold |
| 2 finished0 fault / legal / !finished0 | failed, ->15 / projection=5, ->3 / hold |
| 3 ready0 / !ready0 | Issue up GEMV; ->4 / hold |
| 4 finished0 fault / legal / !finished0 | failed, ->15 / ->5 / hold |
| 5 ready1 / !ready1 | Issue elementwise mode2; ->6 / hold |
| 6 finished1 fault / legal / !finished1 | failed, ->15 / projection=6, ->7 / hold |
| 7 ready0 / !ready0 | Issue down GEMV; ->8 / hold |
| 8 finished0 / !finished0 | failed=faults0, ->15 / hold |
| 14 / 15 / default | ->15 / ->0 / ->0 |
| decodes | cmd_ready at0, done at15, selected silu_product at5/6 and GEMV otherwise |

### GEMV

| Parent state/condition | Original edge/actions |
| --- | --- |
| reset | state,failed,layer,pos,k,c,inputs,outputs,source_slot,target_slot,projection,qw,qz,lane=0; clear scales/accumulators |
| response fault | failed=1; ->20 |
| 0 cmd_valid invalid | failed=0; latch layer,pos,projection; k,c,lane=0; failed=1; ->19 |
| 0 cmd_valid legal | Same latches/counters; assign inputs/outputs/source/target by projection; ->16 |
| 0 !cmd_valid | Hold |
| 1 request accepted / stalled | Read activation kind8 source_slot,k; ->2 / hold |
| 2 complete / waiting | Capture activation; ->3 / hold |
| 3 request accepted / stalled | Read kind1 layer/projection,k,c/8; ->4 / hold |
| 4 complete / waiting | Capture qw; lane=0; ->9 / hold |
| 5 request accepted / stalled | Read kind2 layer/projection,k/G,c/8; ->6 / hold |
| 6 complete / waiting | Capture qz; lane=0; ->7 / hold |
| 7 request accepted / stalled | Read kind3 layer/projection,k/G,c+lane; ->8 / hold |
| 8 complete invalid scale | failed=1; ->20 |
| 8 complete legal, lane7 / other | Capture scale; lane=0, ->1 / lane++, ->7 |
| 8 waiting | Hold |
| 9 invalid dequant | failed=1; ->20 |
| 9 valid, more k, crossed group | Accumulate all lanes; lane=0, k++; ->5 |
| 9 valid, more k, same group | Accumulate all lanes; lane=0, k++; ->1 |
| 9 valid, last k, projection<3 / other | Accumulate; lane=0; ->11 / ->13 |
| 11 request accepted / stalled | Read bias kind4 layer/projection,c+lane; ->12 / hold |
| 12 complete invalid | failed=1; ->20 |
| 12 complete legal lane7 / other | Add bias; lane=0, ->13 / lane++, ->11 |
| 12 waiting | Hold |
| 13 request accepted / stalled | Write kind8 target_slot,c+lane, rounded/saturated result; ->14 / hold |
| 14 complete lane<7 | lane++; ->13 |
| 14 complete last lane, more outputs | c+=8, k=0,lane=0; ->16 |
| 14 complete final / waiting | ->20 / hold |
| 16 | Clear qw,qz,activation,lane,scales,accumulators; ->5 |
| 19 / 20 | ->20 / clear qw,qz,activation,lane,scales,accumulators, ->0 |
| default/decodes | ->0; cmd_ready at0, done at20, response ready only at2/4/6/8/12/14 |

Projection input/output/scratch actions:
Q H->H 1->2; K H->K*D 1->3; V H->K*D 1->4;
O H->H 5->6; gate H->I 8->9; up H->I 8->10; down I->H 11->12.

### RMSNorm

| Parent state/condition | Original edge/actions |
| --- | --- |
| reset | Clear state,failed,layer,index,src,dst,norm_kind and arithmetic storage |
| memory fault | failed=1; ->15 |
| 0 cmd_valid invalid / legal | failed=0, layer latch,index=0; invalid failed, ->14 / assign src,dst,norm_kind, ->1 |
| 0 !cmd_valid | Hold |
| 1 issue / stalled | Read kind8 src,index; ->2 / hold |
| 2 complete more / last / waiting | Accumulate square; index++, ->1 / ->3 / hold |
| 3 / 4 | Compute mean, ->4 / compute sqrt denominator, ->5 |
| 5 zero denominator / valid | failed, ->15 / compute reciprocal, index=0, ->6 |
| 6 issue / stalled | Read kind8 src,index; ->7 / hold |
| 7 complete / waiting | Capture x; ->8 / hold |
| 8 issue / stalled | Read norm_kind,index; layer0 if kind7 else latched layer; ->9 / hold |
| 9 complete invalid / legal / waiting | failed, ->15 / capture gamma, ->10 / hold |
| 10 issue / stalled | Write kind8 dst,index, normalized result; ->11 / hold |
| 11 complete more / last / waiting | index++, ->6 / ->15 / hold |
| 14 / 15 / default | ->15 / ->0 / ->0 |
| decodes/modes | ready at0, done at15; mode0:0->1/kind5; mode1:7->8/kind6; mode2:0->14/kind7 |

### RoPE

| Parent state/condition | Original edge/actions |
| --- | --- |
| reset | state,failed,key_vector,position,head,pair_index,x,y,cosine,sine=0 |
| memory fault | failed=1; ->15 |
| 0 cmd_valid invalid / legal | latch position; head,pair_index,key_vector,failed=0; invalid failed, ->14 / ->1 |
| 0 !cmd_valid | Hold |
| 1 issue / stalled | Read kind8 Q/K slot, head*D+pair; ->2 / hold |
| 2 complete / waiting | x=rd; ->3 / hold |
| 3 issue / stalled | Read second half at head*D+pair+D/2; ->4 / hold |
| 4 complete / waiting | y=rd; ->5 / hold |
| 5 issue / stalled | Read kind11 position,2*pair; ->6 / hold |
| 6 complete / waiting | cosine=rd; ->7 / hold |
| 7 issue / stalled | Read kind11 position,2*pair+1; ->8 / hold |
| 8 complete / waiting | sine=rd; ->9 / hold |
| 9 issue / stalled | Write first half rotated result, same Q/K slot; ->10 / hold |
| 10 complete / waiting | ->11 / hold |
| 11 issue / stalled | Write second half rotated result; ->12 / hold |
| 12 complete more pairs | pair++; ->1 |
| 12 complete more heads | pair=0,head++; ->1 |
| 12 complete last Q | key_vector=1,head=0,pair=0; ->1 |
| 12 complete last K / waiting | ->15 / hold |
| 14 / 15 / default/decodes | ->15 / ->0 / ->0; ready at0, done at15 |

### Elementwise

| Parent state/condition | Original edge/actions |
| --- | --- |
| reset | state,failed,mode,index,a,b=0 |
| memory fault | failed=1; ->15 |
| 0 cmd_valid invalid / legal | latch mode,index=0,failed=0; invalid failed, ->14 / ->1 |
| 0 !cmd_valid | Hold |
| 1 issue / stalled | Read first kind8 operand by mode; ->2 / hold |
| 2 complete / waiting | a=rd; ->3 / hold |
| 3 issue / stalled | Read second kind8 operand by mode; ->4 / hold |
| 4 complete / waiting | b=rd; ->5 / hold |
| 5 issue / stalled | Write result kind8 target by mode; ->6 / hold |
| 6 complete more / last / waiting | index++, ->1 / ->15 / hold |
| 14 / 15 / default | ->15 / ->0 / ->0 |
| decodes/modes | ready at0, done at15; mode0 0+6->7; mode1 7+12->0; mode2 silu(9)*10->11; mode2 length I else H |

### Attention

| Parent state/condition | Original edge/actions |
| --- | --- |
| reset | Clear state,failed,value_cache,context_pass,layer,position,index,head,time_index,dim,component and all arithmetic storage |
| memory fault | failed=1; ->31 |
| 0 cmd_valid invalid / legal | Latch layer,position; reset traversal/cache/pass/counters and reductions; invalid failed, ->30 / ->1 |
| 0 !cmd_valid | Hold |
| 1 issue / stalled | Read scratch slot3/4,index by value_cache; ->2 / hold |
| 2 complete / waiting | cache_data=rd; ->3 / hold |
| 3 issue / stalled | Write kind9/10 layer,position,index,cache_data; ->4 / hold |
| 4 complete more KV components | index++; ->1 |
| 4 complete last K | value_cache=1,index=0; ->1 |
| 4 complete last V / waiting | ->6 / hold |
| 6 issue / stalled | Read Q slot2,head*D+dim; ->7 / hold |
| 7 complete / waiting | q=rd; ->8 / hold |
| 8 issue / stalled | Read kind9 layer,time_index,(head/RATIO)*D+dim; ->9 / hold |
| 9 complete more dimensions / last / waiting | Accumulate dot; dim++, ->6 / ->10 / hold |
| 10 | Scale score; ->11 |
| 11 max pass | Update max if greater; more time: time++,dim=0,dot=0, ->6; last: context_pass=1,time=0,dim=0,dot=0, ->6 |
| 11 context pass | Capture exp(current-max); ->12 |
| 12 | Accumulate denominator; ->13 |
| 13 issue / stalled | Read kind10 layer,time,(head/RATIO)*D+component; ->14 / hold |
| 14 complete / waiting | Accumulate weighted V; ->15 / hold |
| 15 more time | time++,dim=0,dot=0; ->6 |
| 15 last time, zero denominator / valid | failed, ->31 / ->16 |
| 16 issue / stalled | Write context slot5,head*D+component,weighted/denominator; ->17 / hold |
| 17 complete more components | Reset time,dim,dot,weighted,denominator; component++; ->6 |
| 17 complete more heads | Same reduction reset; head++,component=0,context_pass=0,max reset; ->6 |
| 17 complete final / waiting | Same reduction reset; ->31 / hold |
| 30 / 31 / default/decodes | ->31 / ->0 / ->0; ready at0,done at31 |

### Shared modules and GEMV mapping

`rtl/anvil_q1_mem_port.sv`, `rtl/anvil_q1_bus_mux.sv` and
`rtl/anvil_q1_parameters.sv` retain the parent module names and original
source contents. No memory handshake or routing behavior is intentionally
changed. Bus selection lifetime is guaranteed by the command controllers;
the mux is not an independent ownership tracker.

`anvil_q1_fp_gemv` derives from the inventoried parent GEMV. In mode00:

| Original inventory items | Delivered mapping / classification |
| --- | --- |
| Reset, command acceptance and invalid layer/position/projection | Same state0/19/20 structure, plus precision latch/rejection; retained original actions |
| Projection inputs/outputs/source_slot/target_slot assignments | Same state0 case assignments; retained |
| Request states1,3,5,7,11,13 and response states2,4,6,8,12,14 | Same paired request/response ownership, guards and acknowledgements; retained mode00 actions |
| Kind1/2 packed column c/8 | c>>3, equivalent for unsigned c; no runtime divider |
| Kind2/3 group row k/G | group_index, initialized0 per tile and advanced only on group_offset+1==G; equivalent counter addressing |
| State9 arithmetic/advance action | State9 captures dequantized weights,17 captures products,18 accumulates and performs original advance actions; arithmetic-wait retiming |
| State9 more-k/cross-group conditions | State18 more-k guard and offset wrap; equivalent by group_index=floor(k/G), group_offset=k-group_index*G |
| Bias acceptance/validation and shifted bias accumulation | Same state12 mode00 branch; retained |
| Output rounding/saturation and tile/write/lane order | Same state13/14 mode00 actions; retained |
| Tile clearing and first scales read | Same state16 mode00 branch; retained, including resetting explicit group counters |
| Terminal clearing/exit, fault priority, default recovery and public decodes | Same state20/fault/default structure; retained |

Native mode adds states21/22 to collect eight kind12 weights per input row;
23 launches eight independent one-active-lane mixed dots with the same
binary32 activation and each output's binary32 seed; 24 waits for their
registered results. It uses the same eight-output tiling, projection
assignment, activation slot, bias and scratch-write addresses. States25/26
launch/wait for a native bias add. No native path invokes Q16.16 conversion.
Input responses with nonfinite native words or nonzero upper halves of
16-bit tensor data fault before arithmetic. Fatal arithmetic status is
invalid/divide-by-zero/overflow; underflow/inexact alone are retained data.

AWQ scale decoding, lane permutation, sign extension, FP16 compatibility
conversion, wide accumulation and half-away-from-zero rounding derive
from the parent functions, not native IEEE rounding. The dequantizer's
private scale conversion is shared via the identical integer formula in
`anvil_q1_fp_compat_pkg::f16_scale`. Registering weight and product
separately removes the old scale-decode/multiply/accumulate combinational
chain without changing the intended mode00 sum. Differential execution
is still mandatory; this mapping is implementation rationale, not a
bit-identity result.

## Arithmetic implementation increment

The common term representation stores a 64-bit normalized unsigned
significand (leading one at bit63), its signed leading-bit binary
exponent, sign, zero, infinity, NaN and invalid markers. Input products
are exact before alignment. BF16 and FP16 products need at most 22
significand bits; binary32 products need at most 48. Binary32 seeds
need at most 24. Each therefore fits exactly before alignment.

The three-stage reducer is shared arithmetic, not a fourth dot stage:

| Register stage | Work captured |
| --- | --- |
| 1 | Exact unpacked/prepared terms, mask, forced-invalid |
| 2 | Largest-exponent grid, nine aligned signed integers, exception/zero metadata and alignment loss |
| 3 | Balanced signed reduction and one nearest/even binary32 pack |

Signed aligned integers and every reduction node have 69 bits:
nine magnitudes each below 2^64 have sum magnitude below 9*2^64,
strictly below 2^68, fitting signed69. Alignment shifts are bounded;
exponent distances >=64 yield zero magnitude and record discarded
nonzero bits. Leading-bit encoders use binary subdivisions rather than
an unbounded search. Reduction is balanced with sixteen padded leaves.
No ready signal or hidden queue changes the three registered stages.
Special-value metadata bypasses finite packing only at the same
registered output stage.

The standalone binary32 add/multiply wrappers reuse this reducer.
Multiplication prepares one exact product; addition prepares two exact
binary32 terms. Two-term alignment at 64 positions supplies far more
than binary32 guard precision, but independent verification must still
establish all rounding/status cases; no executed correctness claim is
made here. Underflow detection is after final rounding. Zero sign is
preserved independently of unsigned magnitude storage.

`anvil_q1_fp_dot8_mixed` is the internal binary32-activation/native-weight
variant: a has eight 32-bit lanes, b has eight selected-format 16-bit
lanes, and the seed/result remain binary32. It widens each stored weight
exactly before forming the exact product; it never narrows activation
state. It uses the same three-stage reducer, grid, mask, exception and
reset rules. This additional internal interface does not alter the
required public 16-bit-by-16-bit dot8 interface. Matrix integration must
use the floating reducer for actual native arithmetic, not a fixed-point
path plus disconnected demonstration leaves. Its numerical and
structural reachability coverage remains independent Verifier work.

Stage decomposition is an implementation proposal, not proof of 100 MHz.
Dynamic alignment, leading detection and reduction/packing need actual
Quartus path assessment. Do not add a fourth dot stage to hide a failure.

### Scalar pipelines

The three scalar modules have the exact SPEC.md streaming ports and no
backpressure. Results and status are gated by the corresponding valid bit
and reset. Every pipeline may accept a launch on every clock; no shared
sequential resource reduces the initiation rate. Special results follow
the same metadata latency as finite arithmetic.

| Module | Register-stage organization |
| --- | --- |
| anvil_q1_fp_exp | Input Q24 reduction preparation; log2 range reduction; five Horner stages; final polynomial/nearest-even pack = 8 |
| anvil_q1_fp_reciprocal | Normalize; fourteen two-digit restoring quotient stages; binary32 pack = 16 |
| anvil_q1_fp_rsqrt | Normalize; twelve two-digit restoring root stages; ten three-digit restoring quotient stages; binary32 pack = 24 |

Reciprocal normalizes `abs(x)=m*2^e`, m in [1,2), and computes
`floor(2^28/m)`. Each quotient stage has exactly two shift/compare/subtract
steps, with the denominator propagated alongside the quotient/remainder.
The result is packed on grid `2^(-28-e)`. Division truncation alone has
relative error below 2^-27 before final binary32 rounding. For subnormal
outputs its absolute truncation is below 1/64 output ULP. These are
analytical implementation bounds, not observed verification results.

Reciprocal-square-root chooses `x=M*2^(2h)` with M in [1,4), including
normalized binary32 subnormal inputs. The 48-bit radicand is exactly
M*2^46. Twenty-four restoring root digits produce
`r=floor(sqrt(M)*2^23)`. The ten quotient stages compute
`floor(2^53/r)`, equivalently thirty fractional reciprocal bits.
The final grid is `2^(-30-h)`. The root's relative reciprocal error is
below `2^-23/(1-2^-23)` and quotient truncation adds less than 2^-29
relative error before final rounding, below the admitted 2e-6 bound.
Each root stage contains exactly two digit steps; each reciprocal stage
contains exactly three. There is no combinational division operator.

Exp reduces the bounded input through signed Q24, then multiplies by
nearest-even Q30 log2(e)=1549082005. The product's integer part is k;
the next thirty fractional bits give f in [0,1). It evaluates the
degree-six Taylor polynomial for `2^f` in Horner form with Q30
coefficients, then scales by 2^k at the binary32 pack:

| Degree | Q30 coefficient |
| ---: | ---: |
| 0 | 1073741824 |
| 1 | 744261118 |
| 2 | 257941248 |
| 3 | 59597083 |
| 4 | 10327387 |
| 5 | 1431680 |
| 6 | 165394 |

Constants are nearest/even to `(ln(2)^j/j!)*2^30`, generated with
Python standard-library Decimal at precision80; no external package
or numerical test harness was installed or executed. Horner products
truncate only the fixed-point implementation's low fractional positions;
the binary32 output pack is nearest/even. For 0<=f<1, the omitted
Taylor tail is bounded by
`ln(2)^7/(7!*(1-ln(2)/8)) < 1.7e-5` absolutely. Input/range-reduction
and Q30 coefficient/truncation errors leave analytical margin to the
2e-5 relative softmax contract; independent exponent-bin and seeded
execution still must establish the required bound. This is not an
executed numerical-fidelity claim.

Exp handles zero and infinities before finite range reduction. Finite
x<-80 is the specified softmax clipping case: +0 with inexact and no
underflow assertion on a fabricated tiny intermediate. Finite positive
x>89 is certainly overflow; inputs up to89 still use exponent/rounding
overflow detection. Nonzero finite exp results mark inexact. Nonfinite
external tensors must be rejected at command boundaries even though
scalar leaves define deterministic IEEE special results.

### Iterative compatibility foundations

`anvil_q1_fp_compat_div` accepts an unsigned 128-bit numerator and 64-bit
denominator only on in_valid && in_ready. It performs one restoring
quotient digit per clock with a 65-bit comparison/subtraction and returns
the exact unsigned quotient/remainder after 128 processing edges.
If accepted at E0, a nonzero-denominator result appears after E128;
out_valid lasts one cycle. Zero denominator returns an explicit
divide_by_zero completion after E0, not a successful arithmetic result.
Only the eventual command controller may convert that indication to a
command fault. Reset annuls work.

`anvil_q1_fp_compat_sqrt` has the same acceptance/reset style, a
128-bit radicand and floor unsigned64 root. It performs one two-bit
radicand digit per edge with a 66-bit remainder/trial path. An E0
acceptance produces out_valid/result after E64. These helpers have no
output backpressure; callers must reserve result storage.
`anvil_q1_fp_compat_round_div` applies the parent's half-divisor bias
to the unsigned magnitude, uses the restoring divider and reapplies the
captured sign. Its integration inputs are sign-extended 96-bit reductions,
so magnitude-plus-bias fits 128 bits. This is the parent's half-away
rounding, not nearest/even.

`anvil_q1_fp_compat_exp` sequences exact unsigned quotient/remainder
reduction by 11629080, then six signed Taylor terms. Each term multiplication
is registered before unsigned magnitude division by 16777216*j; sign
application truncates toward zero, as the parent signed division does.
It preserves the parent's clipping at Q16.16 -16, exp(0) and Q24 result.
`anvil_q1_fp_compat_silu` sequences that exp, the original integer sigmoid
division, a registered product and the original half-away rounding.
Neither compatibility helper accepts a new launch while busy. These are
private command-serialized helpers, not replacements for the native
initiation-interval-one scalar interfaces.

## Connected operator and ownership architecture

There is one synchronous clock/reset domain. Every command operator
captures its own precision; changes at the top-level mode input while busy
cannot change any tensor interpretation. Commands are serialized. The
parent's literal instance names and routing hierarchy are retained:

```
anvil_q1_fp_top
  memory_port: anvil_q1_mem_port
  decoder: anvil_q1_fp_decoder_layer
    norm: anvil_q1_fp_rmsnorm
    gemv: anvil_q1_fp_gemv
    rope: anvil_q1_fp_rope
    attention: anvil_q1_fp_gqa_attention
    mlp: anvil_q1_fp_swiglu_mlp
      gemv: anvil_q1_fp_gemv
      silu_product: anvil_q1_fp_elementwise
      bus: anvil_q1_bus_mux
    residual: anvil_q1_fp_elementwise
    bus: anvil_q1_bus_mux
  final_norm: anvil_q1_fp_rmsnorm
  bus: anvil_q1_bus_mux
```

| Boundary | Producer guarantee | Consumer obligation |
| --- | --- | --- |
| Token command | Top captures token/position/precision at valid&&ready | Host holds inputs until accepted; changed precision requires new_sequence at position zero |
| Child command | Parent holds selection and latched command through child completion | Child captures only at cmd_valid&&cmd_ready |
| Memory request | Owning port holds fields until accepted; enables response only afterward | Bridge acknowledges every request once, including writes; does not return old-epoch responses after reset |
| Arithmetic launch | Controller reserves operand/result registers and launches once | Fixed-latency leaf emits valid without backpressure |
| Arithmetic completion | Registered result and status sampled only in corresponding wait state | Controller faults on invalid/divide-by-zero/overflow, otherwise stores result |
| Logit | Top holds index/data/valid through stall | Host accepts each logit once; final acceptance causes one-cycle done |
| Fault/reset | Fault stops traversal; reset clears all pipelines and memory ownership | Recovery requires a new sequence at zero after a fault |

No command overlaps another command's memory ownership. A routing selection
changes only after the selected child has consumed its final acknowledged
transaction and returned completion. The parent command controller retains
selection during all additional arithmetic wait states.

### RMSNorm

Mode00 retains the 96-bit exact square sum, the original floor
`(sum<<32)/H + 18446744073710`, integer square root, floor
`2^64/denominator`, FP16-to-Q16 gamma and final round/saturate at shift48.
Square, accumulation, gamma product and reciprocal product have separate
register boundaries. The two divisions and root are iterative.

Native mode reads binary32 scratch, reduces squares with registered FP32
multiply/add, obtains reciprocal H through the 16-stage scalar pipeline,
multiplies the reduction by that reciprocal, adds binary32 epsilon
`0x358637bd`, then waits for the 24-stage reciprocal square root.
The second traversal reads each x and selected-format gamma, and uses two
registered FP32 multiplications before writing the original destination.
Constants H and D are converted at elaboration through the same mathematical
integer-to-binary32 pack, not by a runtime fixed-point data conversion.
The independent reference must evaluate the formula from decoded input data.

### RoPE

Traversal remains Q heads then K heads, and each pair reads components
i and i+D/2 followed by cosine/sine at kind11 position,2*i/2*i+1.
Compatibility stores four signed 64-bit products before its 65-bit
rotation and original shift30 rounding/saturation. Native mode launches
four FP32 multiplies, captures all four registered results/statuses,
then launches two FP32 add/subtract pipelines. Only after both complete
are first and second half written with independent acknowledgements.
Coefficient generation is external; the model/data manifest must bind
the independently checked theta=1000000 coefficient table.

### Attention

The original cache-write phase, causal two-pass traversal and per-component
context traversal remain. K then V are acknowledged into logical cache
addresses for the current layer/position before score reads begin.
Explicit `kv_head` and `group_offset` registers replace head/RATIO:
they advance only when a head's final component write is acknowledged.
The invariant is `head=kv_head*RATIO+group_offset` and
`0<=group_offset<RATIO`; this gives production grouping 7:1 without
a runtime divider.

Mode00 keeps its signed96 dot/current/max/weighted reductions,
unsigned64 denominator, signed65 weighted product, original floor
sqrt(D<<32), signed rounded division, Q24 exp and final saturation.
Native mode obtains inverse sqrt(D) from the 24-stage kernel, performs
registered FP32 dot multiply/add and score scaling, and records the
maximum score during the first pass. Its second pass recomputes scores,
subtracts the stored max, waits for the 8-stage exp, adds the positive
denominator, and reduces exp*V with FP32 multiply/add. At the final
causal position it checks a positive nonzero denominator, waits for
reciprocal, multiplies the weighted reduction and acknowledges context.
Finite score ordering handles signed zero without treating -0 as
strictly smaller than +0. The initial -infinity max is internal
initialization, never external model data.

### Residual and SwiGLU

Residual modes retain scratch addresses 0+6->7 and 7+12->0.
Compatibility uses the original 33-bit sum/saturation. Native mode
waits for registered FP32 addition. SwiGLU's slot9/slot10->slot11
traversal retains length I. Native SiLU uses a stable sigmoid:
`e=exp(-abs(gate))`, `r=reciprocal(1+e)`, then sigmoid=r for a
nonnegative gate or e*r for a negative gate. Gate*sigmoid and
the subsequent product with up each wait for registered FP32
multiplication. This avoids positive exponential overflow for large
negative gates. MLP retains gate, up, activated product and down order.
Compatibility calls the integer SiLU sequencer before the original
round/saturate product.

### Top and decoder

Decoder preserves all eleven steps and scratch/projection assignments.
Top preserves embedding traversal, all layer commands, final norm, tied
output-weight traversal and ascending vocabulary logits. Native embeddings
and output weights are decoded directly into floating-point operands;
logits use the mixed FP32/native-weight three-stage reducer. Compatibility
retains its signed96 logit sum and shift16 saturation with separate
product and accumulation registers. No state can issue an output write
or logit before its arithmetic result is registered.

## Completed control-preservation mapping

The complete original inventory above, bound by the thirteen source hashes,
is the denominator. The following is a total mapping, not a selection of
favorable rows. **R is the default for every original edge and each original
non-arithmetic assignment/request/decode in every inventory row**, at its
same module instance, state number and condition in mode00, except the
exhaustive E/C overrides below. Waiting self-edges, reset clears, fault
priority and default recovery are included. Each assignment in a grouped
row inherits its row's mapping separately. New native states, precision
latches/guards and arithmetic registers add no denominator items.

| Original module / item | Delivered location | Class and reason |
| --- | --- | --- |
| memory_port, all inventory rows and each action | Same module and exact source | R |
| bus mux, active/inactive request/response actions | Same module and exact source | R |
| decoder, every row/step/command/selection/action | Same states/steps; renamed functional child types | R |
| MLP, every row/projection/selection/action | Same states/projections and child ownership | R |
| GEMV, all items except overrides in its earlier mapping | Same-numbered states and conditions | R |
| GEMV state9 accumulate/advance, each branch and lane/k action | 9->17->18, then original destination; group counters replace quotient comparisons | E; registered arithmetic waits do not change request/ownership/order |
| GEMV kind1/2/3 column/group addressing | c>>3 and group_index | E; unsigned shift and explicit group invariant produce identical addresses |
| RMSNorm state2 square/reduce, index advancement and last transition | 2->16->17->18, then original next read or state3 | E |
| RMSNorm state3 mean transition | 3->40->4 | E; wait for exact integer quotient |
| RMSNorm state4 root transition | 4->41->5 | E; wait for exact floor root |
| RMSNorm state5 denominator validation, reciprocal, index=0, ->6 | 5->42->6, divide-by-zero fault ->15 | E; zero denominator returns explicit fault instead of launching a read |
| RMSNorm state9 legal gamma, ->10 | 9->43->44->45->10 | E; registered gamma/reciprocal products, no address changes |
| RoPE state8 sine capture, ->9 | 8->16->17->9 | E; register four products and packed rotations |
| Elementwise state4 b capture, ->5 | Residual:4->7->5; SiLU:4->8->9->10->11->5 | E; wait for integer sum or SiLU/product without issuing memory |
| Attention legal command, ->1, sqrt_dim nonzero guard | 0->62->63->1; zero root faults at63 | E; constant root is checked before any memory activity |
| Attention state8/13 cache column actions | kv_head*D+dim/component | E; explicit head-group invariant replaces quotient |
| Attention state9 dot/advance actions | 9->36->37->39, then original6/10 | E; product/add registered, dim advancement unchanged |
| Attention state10 score transition | 10->38->11 | E; wait for rounded signed quotient |
| Attention state11 context exp transition | 11->42->43->12 | E; exact parent integer exp sequencing |
| Attention state14 weighted accumulation, ->15 | 14->50->51->15 | E; register weighted product before add |
| Attention state15 last-time valid denominator, ->16 | 15->56->57->16 | E; wait for original rounded quotient and saturation |
| Top state12 legal weight/product/accumulation, ->13 | 12->16->17->13 | E; same signed96 accumulation and original destination |
| Top state0 invalid token, failure assignment/->30 | Same state0 condition and actions, plus sequence_valid=0 | R for original edge/actions; new invalidation is an added action |
| Top continuation condition | State0 additionally rejects changed precision without new_sequence | C for this guard; required new precision-state semantics |

All remaining RMSNorm, RoPE, elementwise, attention and top rows/actions
are R by the explicit total rule: same request kind/row/column, traversal
limits, command capture, memory waits, terminal states and completion
decodes. The top retains reset sequence_valid=1 and initial mode00
position-zero continuation, as the parent does; initial native precision
requires a position-zero new_sequence. Any rejected token invalidates
continuation until recovery, as required by the admitted fault contract.
The new action does not retroactively change the original control-action
denominator.

This mapping predicts preservation well above 85% because it classifies
every original item R/E except the single precision-sensitive continuation
guard. No measured preservation percentage or differential result is
claimed here. Verifier must enumerate/count each original edge and action,
check all mapping invariants and require the admitted >=85% independently.
Any behavioral disagreement is a design failure to repair, not permission
to relabel an action or reduce the denominator.

## Target constraints and matched comparison

`fpga/anvil_q1_fp.qsf` names the exact requested Arria 10 part, every
deliverable RTL source, top, seed17 and balanced optimization.
`fpga/anvil_q1_fp.sdc` declares the 10.000 ns core clock, derived clock
uncertainty, all nonclock input delays (max2.000/min0.500 ns) and all
output delays (max2.000/min0.500 ns). Reset is a timed synchronous input,
not a false path. There are no false-path or multicycle exceptions.
The interface budget assumes a synchronous external memory/token bridge;
it is not an assertion that a particular board trace or PCIe clock meets it.

The core-only QSF virtualizes nonclock ports, leaving clock placement
to fitting. This is a core PPA/STA configuration, **not a PCIe bitstream
or HIL substitute**. A physical run must integrate the shared runtime's
existing source-bound bridge, clock/reset adaptation and actual board
pin constraints. Its post-fit timing must fully constrain both core and
bridge and the resulting bitstream must be bound to the HIL evidence.
Neither virtual ports nor a generic Yosys netlist satisfy L3.

From the delivered project root, the target compiler entry is
`quartus_sh --flow compile fpga/anvil_q1_fp` with an existing Quartus17.1
installation. The checked-in output setting is project-local
`evidence/quartus/anvil_q1_fp`; native execution must allocate fresh
execution output directories and must not overwrite prior results.
The QSF's source paths are relative to its `fpga/` project directory.
The shared runtime owns invocation, limits, output retention and native
gate adapters. No compiler or board execution was performed by Designer.

The matched parent run must use the same part, seed, clock, interface
budgets, virtualization or same physical bridge, fitter settings and
memory implementation. Rename only its top reference for constraints;
do not compare a core-only fit to a bridge-inclusive fit. Record actual
ALMs, DSPs and memory blocks; compute native-minus-parent absolute and
percentage ALM/DSP deltas, with a zero-parent denominator explicitly
reported rather than divided by zero. Retain the untouched parent's
runtime-divider/timing failures. If a bit-compatible timing-repaired
W4A16 comparison is required, identify it as a separate baseline.
The product itself still requires WNS>=0, no unconstrained paths and
three consecutive physical hardware passes; no waiver is presumed.

## Verification and target integration

All four commands and acceptance obligations are in SPEC.md. Designer
does not author tests, reference models, mutation harnesses or simulation/
synthesis probes. Preparation evidence, if any, is advisory and retained
under a unique `evidence/preparation/` child with exact command, source
hashes, tool version, timestamps, timeout/exit and raw logs.

No model/data acquisition or benchmark execution has occurred. Input
acquisition is manifest-driven and remains separate from Designer RTL.
Verifier owns `tests/data/benchmark_manifest.json` and checkpoint/AWQ
provenance manifests. Pin a public immutable checkpoint revision before
retrieval; with an already available Hugging Face CLI the acquisition
form is `hf download Qwen/Qwen2.5-0.5B-Instruct --revision REVISION
--local-dir tests/data/checkpoint`, replacing REVISION with the pinned
manifest commit, never a moving branch. Verify every file hash, tokenizer
and template before deriving both native streams and same-checkpoint AWQ.
Use the exact four dataset sources, canonical record selection and
seed17 Sequence generation in SPEC.md; freeze revisions and actual
record/content hashes before full-model execution. Data preparation must
record tensor layout, scales, zeros, nibble permutation and calibration
provenance. Native tensors' unused upper halves are zero; scratch/KV and
RoPE coefficients remain binary32.

No dataset revision, checkpoint hash, AWQ calibration recipe execution
or Code-isolation environment is invented in this document. If a
required acquisition/reference tool is absent, report it as a prerequisite
failure; do not install tools. All large inputs and generated results
remain project-relative and outside RTL/design/constraint input selectors.
All four portable check commands are in SPEC.md; the independent
`portable` command must exercise a clean-copy smallest legal case in
every mode and must report that bounded result separately from full-model
reproduction. Reduced simulations do not establish model delivery.
Missing model data, isolated Code evaluation, Quartus, hardware bridge
or target hardware remain blockers to full acceptance, not grounds for
substitution. Runtime native gate integration uses the product sources
and target constraints, never a local JTAG cable or PCIe BDF in tests.
Compare parent and product with matched part, interfaces, memory and
settings; report actual parent failures distinctly from product failures.
The independent product PDF follows engineering acceptance.

## Retained Designer diagnostics

`evidence/preparation/designer-static-7289d121cdb3/receipt.json` records
the first increment's fast Icarus syntax/elaboration command for its sixteen
RTL files and twelve arithmetic/GEMV/shared-module roots. Its actual exit
was zero. The receipt retains exact project-relative argv/cwd, input
hashes, tool-version output, times, timeout and raw stdout/stderr.
It is historical advisory preparation only: no top-level product elaboration,
functional simulation, reference comparison, defect injection, synthesis,
benchmark, timing or hardware execution occurred. No failed diagnostic
or repair result is claimed for that increment. The integrated operators
were added afterward; this earlier receipt does not cover them.

The integrated handoff's static receipt is
`evidence/preparation/designer-integration-static-e24a6b519f72/receipt.json`.
It records production top and public-dot8 syntax/elaboration only, with
the actual exit, source hashes, exact argv, compiler version and raw logs.
Neither static receipt can mark an execution.checks command
passed, replace independent verification or authorize the product report.
