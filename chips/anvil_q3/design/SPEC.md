# Anvil-Q3 implementation contract

## Status and authority

This is an incremental design source, not an acceptance report. The independently
admitted full-profile work order remains authoritative. The current source
increment connects the full sequential decoder, tagged scheduling, external
KV commit/decode and tied embedding/vocabulary path. The portable FPGA shell,
checked byte mapping and host ABI are supplied under `fpga/`, but real
board/IP/pinout integration is blocked by unestablished prerequisites.
The connected RTL is not an independently verified product.
No functional, synthesis, timing, board or cross-generation result is claimed.
The supplied `anvil_q2_reference/rtl/` is read-only architectural reference, never
the expected-answer oracle. No linked intake source index was supplied.

The core entry point is `anvil_q3_top`, targeting the Intel Arria 10 GX
`10AX115N2F45E1SG` with a 10.000 ns clock. Required independent gates remain
provenance/prerequisites, parameter/structure checks, the complete Icarus and
Verilator numerical matrix, five-domain cross-generation benchmarking, functional
mutations, Yosys zero-latch synthesis, Quartus fit/STA, physical PCIe Gen3x8 HIL
and clean-directory reproduction. Missing tools, baseline implementations,
board identity, pinout or IP are unmet prerequisites, not passing substitutions.
`tests/**` belongs to the independent Verifier; the final product PDF belongs
to the shared runtime after engineering acceptance.

## Architectural boundary

The intended default profile is Q3: 36 layers, H=2048, I=11008, Q=16, K=2,
D=128, AWQ group=128, 4-bit weights, vocabulary=151936, context=32768,
BANKS=8, CACHE_MODE=0, INT4_ASYM=0, CACHE_BLOCK=1, QUEUE_DEPTH=3,
TILE_K=128, TILE_ROWS=8. PROFILE=1 and 2 retain the admitted Q1/Q2 numerical
and protocol compatibility, not historical timing. Q3 GQA is exactly 8:1.
Use memory-backed sequential decoder scheduling and bounded tile/activation
storage; do not instantiate full model/context storage on chip.

The top ports and memory-kind encodings preserve the admitted
work order. Bank zero uses the low slices. Valid/ready handshakes sample pre-edge
values; payloads remain stable under backpressure. Tagged transactions must
survive arbitrary permitted response ordering, with explicit ownership and
wrap/drain handling. Cancel suppresses command/logit transfers and drains
accepted transactions before completion.

The token accepted at E0 becomes active after E0; it cannot complete at E0.
After the last accepted vocabulary logit, `done=1,error=0` for one cycle, then
idle. PROFILE1 alone resets into an implicit valid empty sequence and ignores
`token_phase`; PROFILE2/3 require initial `new_sequence=1,token_pos=0`.
All profiles require explicit new-sequence recovery after cancellation/fault.
All other admitted contiguous-position, phase-transition and causal-commit
requirements remain unchanged.

Q3 permits K*D not divisible by eight, including A=(L1,H16,I24,Q8,K1,D2,
G8,V17,S9). Tensor work masks incomplete dot8 lanes; compressed KV groups are
partial independently per head. Padding must not issue nonexistent coordinates,
affect extrema, own cache entries or contribute to arithmetic. Legacy profiles
retain their separate multiple-of-eight KV-product restriction. Mode0 preserves
all 32 Q16.16 bits; Mode1 uses Group-32 INT8, Mode2 Group-64 symmetric or affine
INT4. CACHE_BLOCK affects only legacy profiles.

## Numerical rules used by implemented leaves

Nonquantized external tensors and scales are binary16. Internal activations,
lossless KV, scratch and logits are signed32 Q16.16, not FP16 arithmetic.
For a finite binary16 `h`, the unsigned magnitude in Q16.16 is
`(fraction if exponent=0 else 1024+fraction) * 2^s`, where `s=-8` for
subnormal/zero and otherwise `s=exponent-9`. Right shifts round to nearest,
ties away from zero. Signed activations saturate to signed32; nonnegative
scales retain the unsigned32 result without signed saturation. NaN/Inf is
invalid; negative nonzero scales are invalid; negative zero is legal.

The exact AWQ weight is signed37 `(q-z)*scale_integer`. A dot8 returns the
unrounded sum of eight signed37-by-signed32 products, in signed72 Q32.32.
Scale conversion, masking and errors are per transaction. There is no implicit
`+1` on zero points. The dot8's logical lanes are ordinary consecutive nibbles;
the prefetcher unpacks physical AWQ nibble offsets
`[0,16,4,20,8,24,12,28]` into that logical order.

Across dot8 operations accumulate in signed128 without intermediate rounding or
saturation. Add Q/K/V bias at Q32.32, then round once by 16 and saturate.
Other projections have no bias. GEMV now performs the bias addition through
the segmented adder and the single final rounding through `round_q32_to_q16`.
That helper detects saturation against +/- (2^47 - 2^15) first, then uses
only the low 48 magnitude bits for the bounded rounding increment. It does
not negate or increment an unbounded signed128 value combinationally.
Wide accumulation carry chains must be segmented or
pipelined. General division and integer square root are sequential units, not
combinational helper functions. The admitted RMSNorm, exp/SiLU, RoPE, attention,
codec and residual equations govern the connected modules below.
The arithmetic package deliberately does not provide combinational division,
integer-root, exp or SiLU replacements.

## Leaf interfaces frozen for independent verification

All implemented sequential leaves use `clk`, active-low asynchronous `rst_n`,
and active-high synchronous `flush`. All public outputs are zero during reset.
`flush` takes priority over acceptance and result retirement and discards owned
work. Ready and valid are suppressed while flush is high. All accepted operands
are immutable; later input changes cannot affect the owned transaction.

### `anvil_q3_awq_dot8`

The fixed ports are `clk,rst_n,flush,in_valid,in_ready,out_valid,out_ready,
out_error`, unsigned32 `q_nibbles,z_nibbles`, unsigned128 `scale_f16`,
unsigned256 `activation_q16`, unsigned8 `lane_mask`, signed72 `out_dot`.
Lane i occupies `4*i+:4`, `16*i+:16` and `32*i+:32` respectively.
`out_error` is meaningful with `out_valid`; masked fields cannot cause an error.
Invalid active scales produce an error transaction with the invalid lane zeroed;
the numerical dot on any error transaction must not be consumed as valid data.

| Edge/event | Registered state after edge |
| --- | --- |
| E0 input handshake | Unpacked q/z, FP16 fields, activation, mask |
| E1 | Signed5 subtraction, unsigned32 scale conversion, activation |
| E2 | Signed37 weights and activation |
| E3 | Signed54 low16 and signed53 high16 activation partial products |
| E4 | Eight exact signed69 combined products |
| E5 | Four signed70 pair sums |
| E6 | Two signed71 pair sums |
| E7 | Signed72 result, valid and associated error |
| E8, if ready | Earliest consumption of the E0 transaction |

These edges assume no stalls. Initiation interval is one. Global enable is
`!valid_stage7 || out_ready`; a stall freezes all eight stages, including errors.
Flush is not subject to that enable. A zero lane mask is legal and yields exact
zero without errors even with invalid scale bits in all masked lanes.

### `anvil_q3_divider`

Parameters: NUM_W and DEN_W, each 1..256, defaults 129 and 64.
Ports: `clk,rst_n,flush,start,ready,done,error`, unsigned NUM_W `numerator`,
unsigned DEN_W `denominator`, unsigned NUM_W `quotient`, unsigned DEN_W
`remainder`. Numerator is unsigned; callers implement their signed rounding rule
before launch and sign restoration after completion. Divide-by-zero returns a
single done/error pulse immediately after its acceptance edge, with zero
quotient/remainder. This is a registered fault result, not a combinational
command-to-result path.

For nonzero denominator, let C=ceil((DEN_W+1)/16). A transaction accepted at E0
completes immediately after E[NUM_W*(C+2)]. Each numerator bit has one prepare
edge, C low-to-high 16-bit subtract edges, then one commit edge. Quotient and
remainder are a matched result only on `done && !error`; working output contents
before done are not results. `done` and `error` pulse for one cycle; a following
command may be accepted while observing the previous done pulse. There is no
output backpressure. With no start, the last completed result remains stored.

### `anvil_q3_isqrt`

Ports: `clk,rst_n,flush,start,ready,done,error`, unsigned128 `radicand`,
unsigned64 `root`, unsigned65 `remainder`.
For all operands, return floor(sqrt(radicand)) and exact radicand-root^2.
`error` is always zero. A command accepted at E0 completes after E448: 64
radix-four steps, each one prepare edge, five 16-bit subtract edges and one
commit edge. Completion/launch behavior otherwise matches the divider.

### `anvil_q3_accumulator`

Ports: `clk,rst_n,flush,in_valid,in_ready,in_first,out_valid,out_ready,
out_error`, signed128 `in_value,out_sum`. Accepted `in_first=1` starts a new
sum from zero; otherwise add to the last completed internal sum (reset value
zero). A launch at E0 completes immediately after E8, one 16-bit carry segment
per edge. No intermediate sum is externally valid. Output stalls retain result
and error. A new operation may launch on the edge retiring an old output, but
not on its production edge; minimum input initiation interval is nine cycles.
`out_error` reports signed128 overflow of this addition. Callers must terminate
the enclosing token on an error rather than treating a wrapped result as exact.

### `anvil_q3_exp`

Ports: `clk,rst_n,flush,start,ready,done,error`, signed64 `x`,
unsigned32 `value`. Input x is Q16.16. Output is the admitted E(x) in Q0.24.
At x<-1048576 return zero; at x>=0 return 16777216. For other inputs,
use u=(-x)<<8, n=floor(u/11629080), r=u-n*11629080, t0=16777216,
tj=-sign(tj-1)*floor(floor(abs(tj-1)*r/2^24)/j), j=1..6, and
value=max(0,sum(t0..t6))>>n. The divisions use a child segmented divider,
not reciprocal approximations. The result holds until a subsequent completion.

Acceptance occurs at E0. Boundary cases complete at E1. Interior cases complete
at E917: one range launch, 128 range-division clocks, one range harvest,
then six groups of multiply/launch/128 divide/harvest, then finalization.
The same one-cycle done/error and synchronous-flush contract as divider applies.
The top-level ready requires the child divider to be idle as well.

### `anvil_q3_silu`

Ports: `clk,rst_n,flush,start,ready,done,error`, signed32 `x,value`.
Evaluate exp(-abs(x)) through `anvil_q3_exp`. With e its Q0.24 result,
sigmoid=floor(2^48/(2^24+e)) for x>=0, otherwise
floor((e<<24)/(2^24+e)). Return sat32(R(x*sigmoid,24)).
INT32_MIN magnitude is unsigned32 2147483648, not overflowing signed negation.
The multiply is on magnitude and unsigned25 sigmoid; restore sign after
rounding and saturation.

A command accepted at E0 launches exp at E1 and harvests its done one edge
after the child's completion. It then launches the 196-cycle divider, harvests
it, registers the product, and registers the rounded result/done. Total
latency is exp latency plus 202 cycles: E203 for a boundary exp input and
E1119 for an interior exp input. Child errors terminate with a done/error pulse.
Reset, flush, operand immutability and completion/launch rules match divider.

## Cycle and degenerate-boundary table

### Scalar-path interfaces for the next connected increment

The following interfaces are frozen before implementation. They do not change
the admitted top or dot8 interfaces. Every sequential module has
`clk,rst_n,flush`; reset zeros public outputs and flush synchronously annuls
local work. A parent must drain the scheduler after flushing a client.

`anvil_q3_mem_port` accepts `issue && idle` with `write,kind[3:0],layer[31:0],
proj[2:0],row[31:0],col[31:0],wdata[31:0]`. It exposes the ordinary scalar
`mem_req_*` / `mem_rsp_*` client fields, without external tags. After acceptance
it holds a registered request through its public handshake, then waits for one
response. `complete` pulses after response acceptance, with registered
`rdata[31:0]` and `fault`; request/response errors and unsolicited responses
are explicit faults. No request is issued on the issue-acceptance edge.
The next issue can be accepted while the preceding completion is observed.
At most one request is owned, including single-beat reads and writes.

`anvil_q3_multiplier` has signed operand widths A_W and B_W (1..128;
A_W+B_W<=256), `start,ready,done,error`, signed `a[A_W],b[B_W]`,
and signed full-width `product[A_W+B_W]`. E0 snapshots both operands.
Magnitude formation, accumulation and sign restoration use registered
16-bit carry segments. Every 16-by-16 unsigned partial multiply is separately
registered; no full-width combinational multiply is substituted. `done/error`
pulse for one cycle and the result holds until the next completion. There is
no output backpressure or same-edge command-to-result path. If
A=ceil(A_W/16), B=ceil(B_W/16), C=ceil((A_W+B_W)/16), latency is
A+B+A*B*(C+2)+C clocks after E0, including sign restoration for zero/positive
products as well as negative products. All loop boundaries use explicit
terminal comparisons, including A=B=C=1.

`anvil_q3_rmsnorm` parameters are NUM_LAYERS,HIDDEN_SIZE,MAX_SEQ_LEN.
It accepts `cmd_valid && cmd_ready` with `cmd_layer,cmd_pos[31:0]` and
`cmd_mode[1:0]`: 0 reads scratch0/writes1 with kind5 gamma, 1 reads7/writes8
with kind6 gamma, 2 reads0/writes14 with kind7 gamma. Final gamma uses layer0.
Its scalar `mem_*` interface matches the port above. `done,error` pulse for
one cycle only after all writes acknowledge, or after detecting a command,
data or memory fault. Error latches the leaf unavailable until flush. Mode2
still requires a legal layer coordinate; callers supply layer0.
The implementation makes two sequential input passes, computes the frozen
integer RMS formula with the segmented accumulator/divider/root/multiplier
leaves, and rounds only at the final shift48. Neither input nor gamma is
reinterpreted as an AWQ scale.

`anvil_q3_rope` parameters are NUM_LAYERS,HIDDEN_SIZE,NUM_Q_HEADS,
NUM_KV_HEADS,HEAD_DIM,MAX_SEQ_LEN. Commands contain `cmd_layer,cmd_pos`;
the scalar memory interface and completion/fault behavior match RMSNorm.
It rotates scratch2 and scratch3 in place, finishing both acknowledged pair
writes before advancing a pair or head. Kind11 uses layer0/projection0,
row=position,col=2*pair+{0 cosine,1 sine}; pairs are split-half pairs.
Four signed32-by-signed32 products and two segmented signed128 sums precede
one shift30/round/saturation per component. Coefficients outside signed
[-2^30,+2^30] are malformed and fault. Host coefficient provisioning must
still independently establish theta=1e6 and correct values.

`anvil_q3_elementwise` parameters are NUM_LAYERS,HIDDEN_SIZE,
INTERMEDIATE_SIZE,MAX_SEQ_LEN. Commands and memory ports match RMSNorm.
Modes 0,1,2 mean respectively scratch0+6 ->7, scratch7+12 ->0,
and SiLU(scratch9)*scratch10 ->11. Residuals saturate without a shift;
the SiLU product rounds/shifts16 and saturates. Mode2 traverses
INTERMEDIATE_SIZE, others HIDDEN_SIZE. `anvil_q3_silu` implements the
nonlinear equation, not a host result. Reads and writes of an in-place
destination are serialized; no index advances before its write acknowledgement.

For all scalar commands, E0 accepts operands, the first memory issue occurs
after E0, request payloads remain stable during any stall, and the final write
response produces a registered completion, never a zero-cycle command result.
Flush takes priority over acceptance, response harvest and completion.
The singleton length1 case runs the same first/final element once.
Non-power-of-two lengths increment explicitly without wrap masks.
No scalar leaf allocates context-sized or model-sized storage.

`anvil_q3_signed_divider` exposes `start,ready,done,error`, signed128
`numerator,quotient` and unsigned64 `denominator`. It implements the frozen
rounded division by a positive denominator: magnitude plus floor(d/2),
unsigned quotient, then sign restoration. It accepts INT128_MIN without an
overflowing negation. Denominator zero or an unrepresentable quotient returns
a done/error pulse. Operands snapshot at E0; ordinary completion is E930.
Magnitude/rounding/sign formation each use 16-bit registered segments around
the existing unsigned129/64 divider. No command/result bypass exists.

`anvil_q3_add128` additionally permits elaboration parameter SUBTRACT=1,
selecting exact signed `in_a-in_b`; default zero preserves addition.
Subtraction complements each B segment and starts with carry1; it does not
compute a full-width combinational negation. Its eight-edge latency,
backpressure and signed overflow reporting are unchanged.

`anvil_q3_kv_cache` parameters PROFILE,NUM_LAYERS,NUM_KV_HEADS,HEAD_DIM,
MAX_SEQ_LEN,CACHE_MODE,INT4_ASYM,CACHE_BLOCK retain the scalar memory ports
above. Commands are `cmd_valid,cmd_ready,cmd_op[1:0],cmd_layer,cmd_pos,
cmd_head,cmd_dim[31:0],cmd_phase`; outputs are `done,error` and signed32
`read_data`. Op0 commits the entire token's scratch3/4 K/V; op1 reads one
committed K component; op2 reads one committed V component. A commit requires
position equal to that layer's committed count and legal monotonic phase.
Reads require position strictly below the committed count. PROFILE1 ignores
phase. Flush invalidates every layer's count, phase and all local buffers.
Counts are per layer, never per token on-chip arrays.

Mode0 stores one kind9/10 word per logical component and reads it through the
same codec bypass. Compressed storage uses per-head ceil(D/CAP) blocks,
ceil(CAP*BITS/32) payload words per block, kind12/13 payload and kind14/15
metadata. Column = (head*blocks+block)*words+word for payload and
head*blocks+block for metadata; row is token position and layer is the
accepted layer. Mode0 column=head*D+dimension. A partial final block fetches
only its logical scratch coordinates, excludes padding from codec extrema,
and stores zero unused lanes. Decode fetches the complete block and validates
all padding and metadata, not just the requested lane. Codec instance name
is `cache_codec`. Commit advances only after both K and V and every payload
and metadata write acknowledge; it has no externally observable early commit.
Any fault invalidates all ownership and locks the leaf until flush.
The final-token/single-head/single-component and one-word block use the same
acknowledgement boundary. Responses never advance an unaccepted request.

`anvil_q3_gqa_attention` parameters PROFILE,NUM_LAYERS,HIDDEN_SIZE,NUM_Q_HEADS,
NUM_KV_HEADS,HEAD_DIM,MAX_SEQ_LEN,CACHE_MODE,INT4_ASYM,CACHE_BLOCK.
Commands are `cmd_valid,cmd_ready,cmd_layer,cmd_pos,cmd_phase`; outputs
`done,error`. Its two untagged scalar-client vectors `c_req_* / c_rsp_*`
have exactly the scheduler's per-client fields: client0 is local scratch,
client1 is `kv_cache`. The parent must connect both to the tagged scheduler.
The required `kv_cache.cache_codec` hierarchy is real, with no host
attention intermediates. Each token first commits all current K/V, then
computes only time indices 0..cmd_pos.

Query heads map contiguously to KV heads by the constant Q/K ratio, with
an explicit head-in-group wrap counter. For each query head a first score
pass finds the maximum. Each output component then performs a second score
pass, exp(score-max), exact weighted V and exponential sums, rounded division
and one signed32 saturation into scratch5. Repeated score passes avoid a
context-sized on-chip score array. Three independent segmented signed128
accumulators own dot, exponential and weighted sums. Root, signed rounded
divider, exp and registered limb multipliers implement the frozen equations.
Scores remain signed128; exponential denominators are checked unsigned64.
No head/time/component counter advances before the relevant arithmetic or
write acknowledgement. Mode0 and both compressed K and V reads go through
the cache's explicit stored-representation decode.

Attention E0 snapshots a legal command; root and commit complete on later
edges before score reads. Its final scratch5 write acknowledgement produces
one registered done/error cycle. Cancellation flush has priority throughout
root, commit, score, output and response states. A fault locks all local work
until flush and must cause parent scheduler draining. Length/context1 and
HEAD_DIM2 run the same loops, including the current token once; no future
or uncommitted token is read. Read-only memory must not change K/V ownership
between the max and context passes.

`anvil_q3_swiglu_mlp` parameters NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,
MAX_SEQ_LEN; commands `cmd_layer,cmd_pos`, standard command/completion/flush.
It exposes scalar `mem_*` for the `silu_product` elementwise child and a
shared GEMV command interface: `gemv_cmd_valid,gemv_cmd_ready,
gemv_cmd_proj[2:0],gemv_done,gemv_error`. The parent owns immutable
epoch/layer/position while granting this resource. MLP serially commands
gate4, up5, SiLU/product mode2 and down6, waiting for each completion
before the next command. It completes after down's final stored output.
No additional tensor array is instantiated or hidden behind the MLP.

`anvil_q3_decoder_layer` parameters PROFILE,BANKS,TILE_K,TILE_ROWS,
NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,HEAD_DIM,
GROUP_SIZE,MAX_SEQ_LEN,CACHE_MODE,INT4_ASYM,CACHE_BLOCK.
Commands contain `cmd_epoch,cmd_layer,cmd_pos,cmd_phase`; the ordinary
ready/done/error/flush rules apply. Its BANKS+7 scheduler clients, in ascending
order, are GEMV's BANKS+1 clients, norm, rope, attention's two clients,
MLP elementwise, residual. These client identities do not change between
operations, and all responses must return to their original client.

One layer runs input norm, Q/K/V, RoPE, cache commit/GQA, O, residual0,
post-attention norm, shared-GEMV MLP and residual1. Children are named
`norm,gemv,rope,attention,mlp,residual`. Decoder snapshots all command fields
at E0 and only launches a child on later edges; child completion and fault
propagate through registered control. A final residual write acknowledgement
precedes decoder completion. No phase, index or shared-resource command can
change while an owned command is outstanding. Flush wins simultaneously
with child command, response or completion. All children must be flushed
and the scheduler drained before a new sequence after any token fault.

`anvil_q3_token_io` parameters HIDDEN_SIZE,VOCAB_SIZE,MAX_SEQ_LEN.
Commands have `cmd_project` (0 embedding, 1 vocabulary projection),
`cmd_token,cmd_pos[31:0]`, with the usual command/completion/flush and
scalar memory ports. Embedding reads finite kind0 binary16 at
row=cmd_token,col=component and writes converted scratch0. Projection
reads scratch14 and the same tied kind0 storage at each vocabulary row;
registered signed32 products enter a segmented signed128 accumulator.
The complete row sum is rounded/shifts16/saturated exactly once.
`logit_valid,logit_ready,logit_index[31:0],logit_data signed32` expose
ascending rows; index and value hold while stalled. The final accepted
logit produces done immediately after that edge. Embedding completion
instead follows the final scratch write acknowledgement. No full vocabulary
or embedding model array is local. V=1 and H=1 execute the first/final
work once. FP16 high transport bits and NaN/Inf are rejected.

Top integration uses BANKS+9 permanently assigned clients: decoder's
BANKS+7, final_norm, token_io. `cancel` immediately suppresses command/logit
traffic and flushes core ownership. Scheduler flush is a bounded pulse (or
held cancel), followed by an explicit drain wait with core flush still held.
New-sequence cache invalidation uses the same drain handshake before the
first embedding request. A fault enters this flush/drain path before its
single error completion. A token accepted with illegal startup/coordinates
does not issue any model or cache request. Idle cancellation does not emit
done; active cancellation emits done/error alongside cancel_done. Completion
pulses occur only with cancel deasserted. Internal epoch wrap is permitted
only from idle with scheduler idle, after old ownership has been invalidated
and before a new descriptor is issued, never over undrained traffic.

| Condition | Required behavior |
| --- | --- |
| Active asynchronous reset | All public status, ready, valid and payload outputs zero |
| Reset released, before first edge | Ready may assert when idle; no result valid |
| Input valid and ready before edge | Exactly one command accepted at that edge |
| Output valid and ready before edge | Exactly one result retires unless flush annuls it |
| Flush simultaneous with input/output | Flush wins; no acceptance or retirement |
| Dot8 full pipeline and output stalled | All data, validity and errors freeze together |
| Dot8 stall release | Old output retires and input may enter on the same edge |
| Divider NUM_W=1 or DEN_W=1 | Same algorithm and latency formula; no negative part selects |
| Zero numerator/radicand | Normal fixed-latency zero result |
| Accumulator first plus prior result retirement | Previous output retires; zero-based new operation starts |
| QUEUE_DEPTH=1 or non-power-of-two | Future scheduler uses explicit bounds/wrap, not masked binary wrap |
| TILE_ROWS=1, one tile/beat | Final-read acceptance, not issue alone, releases ownership |
| Q3 HEAD_DIM=2 | Two logical components; independent per-head codec padding |
| MAX_SEQ_LEN=1 or VOCAB_SIZE=1 | Position zero or first logit is also final; no omitted work |

The singleton and concurrency rows describe implemented control paths, not
independently executed coverage.

## Additional control and cache leaf interfaces

### `anvil_q3_parameters`

This zero-port elaboration guard exposes the architectural parameters by name,
with profile-selected layer/head/hidden/FFN defaults. It uses widened constant
arithmetic, not runtime division/modulo. Coordinate limits are distinct from
64-bit byte extents: a tensor need not fit in a flattened 32-bit address.
Q3 accepts partial KV dot8/group geometry; legacy profiles retain the
multiple-of-eight KV constraint and power-of-two, head-dividing CACHE_BLOCK.
Other modules must use diagnostic-only safe widths and must not instantiate an
invalid geometry's datapath before this guard can issue `PARAMETER ERROR`.

### `anvil_q3_bank_scheduler`

Parameters are BANKS, CLIENTS (1..32, default BANKS+1), and QUEUE_DEPTH (1..16
**per physical bank**). The `c_req_*`/`c_rsp_*` scalar-client vectors use the
parent memory fields, with one ready/valid response per accepted request,
including writes. Clients need no tags: the scheduler privately associates
tagged bus responses and returns each client's responses in acceptance order.
Bank routing is the low log2(BANKS) bits of kind+layer+proj+row+col.
One round-robin client request may enter per edge; different physical banks
can issue and return simultaneously. A full target bank does not block a
client targeting a different bank.

The public `mem_*` vectors have the frozen top memory shapes. `idle` means
no outstanding/reserved client work and no cancellation drain. `fault` is a
one-cycle pulse for an unknown/duplicate/wrong-bank response; that response
is consumed, all unissued work is discarded, and accepted transactions drain.
Memory response errors remain associated client error responses.
`flush` stops new client acceptance/results immediately. A previously held
bus request remains visible through the flush edge: if accepted there, its
response must drain too. `drain_done` pulses after all old transactions drain
and flush is low; an idle flush also produces one drain completion.
Callers hold flush until they have annulled owned client work, then deassert
it to await drain completion.

| Pre-edge event | Post-edge effect |
| --- | --- |
| Client request handshake | Immutable fields/owner/tag enter a free bank slot |
| Queued slot selected on later edge | Registered bus hold is established |
| Held bus request handshake | Slot awaits its unique response |
| Matching response, including same edge as issue | Data/error retained in its slot |
| Oldest client response handshake | Slot freed; no newer response can overtake it |
| Flush/fault plus issue/response | Accepted issue is retained for draining; response retires old ownership |
| Tag ffff...ffff allocated | Ingress stops until all slots retire; counter then resets to zero |
| QUEUE_DEPTH=1 | A retiring oldest client response can release its slot to new ingress on the same edge |
| Non-power-of-two depth | Explicit slot search, no masked pointer wrap |
| Client response stalled | Complete data/error stays stable despite other bus responses |

### `anvil_q3_cache_codec`

Parameters PROFILE,CACHE_MODE,INT4_ASYM,CACHE_BLOCK determine CAP:
Mode0=1, Q3 Mode1=32, Q3 Mode2=64, legacy Mode1=CACHE_BLOCK.
CAP is a derived local constant, not an overridable product parameter.
Ports are `clk,rst_n,flush,start,ready,done,error,decode`, unsigned32 `count`,
unsigned(CAP*32) `values_in,payload_in,values_out,payload_out`, and unsigned32
`metadata_in,metadata_out`. Value lanes are signed32 Q16.16, LSB first.
The deliberately uniform payload vector transports Mode0 signed32 values,
Mode1 consecutive signed8 codes, or Mode2 consecutive signed4 codes in its
low CAP*BITS bits. All other payload bits and unused lanes must be zero.
`count` is 1..CAP, independent of physical padded capacity.

E0 snapshots the whole command. Mode0 completes immediately after E0 with a
registered result; consumption is not combinational. Compressed encode scans
one logical value per edge, then tests one exponent per edge for symmetric
modes or a registered extrema/feasibility pair of edges per exponent for
asymmetric mode, then writes one code per edge. Decode takes CAP lane edges
(including padding validation) followed by a metadata consistency edge.
Done/error lasts one cycle; the following edge returns to ready. Results
are meaningful only with done&&!error and are zero otherwise.
Flush wins over start/completion and discards the command.

The accepted values, not live ports, determine extrema/rounding. INT32_MIN
uses a widened magnitude. Mode0 metadata is zero. Compressed decoders reject
reserved metadata bits, out-of-range exponents, forbidden signed codes,
nonzero padding, nonzero symmetric zero-codes and noncanonical affine
zero-codes (the minimum-magnitude feasible signed4 value for the centered
codes). An all-zero block requires e=0,z=0. Original prequantization values
cannot be recovered from codes; exponent minimality is an encoder property,
not an inference from unavailable originals. The decoder applies exact
signed32 saturation to shifted centered codes.

### `anvil_q3_weight_prefetcher`

`anvil_q3_weight_prefetcher` exposes BANKS descriptor, weight-beat and
untagged scalar memory-client vectors. Each bank has its own descriptor
`desc_valid,desc_ready` handshake; `fault` is also bank-vector shaped.
Parameters are BANKS,TILE_K,TILE_ROWS,NUM_LAYERS,HIDDEN_SIZE,
INTERMEDIATE_SIZE,NUM_KV_HEADS,HEAD_DIM,GROUP_SIZE.
Descriptor fields `desc_epoch,desc_layer,desc_output_base,desc_input_base,
desc_valid_rows,desc_valid_inputs` have 32 bits per bank; `desc_proj` has 3.
`desc_epoch` is an ownership label, not permission to discard accepted bus
traffic. The shared scheduler must receive the same cancellation flush.
Only one scalar memory request per bank-client is outstanding, so its
immutable fill-buffer/row/input/field reservation plus the scheduler's tag
match uniquely identifies every fill response.

Descriptors enter alternate EMPTY buffers in FIFO order. Each bank fills
qweight/zero/scale cells, crossing AWQ groups with explicit counters;
projection coordinates and 33-bit tile bounds are checked before fetch.
The first READY buffer becomes ACTIVE without releasing ownership.
Registered beat outputs use `beat_valid,beat_ready`; `beat_q,beat_z` are
32 bits per bank, `beat_scale` is 128, `beat_mask` is 8, and
`beat_epoch,beat_row,beat_input` are 32.
`beat_row_first,beat_row_last,beat_tile_last` are single-bit bank vectors.
Each beat holds eight consecutive inputs for one
output row. Padding lanes are zero. A registered beat can be replaced on
the same edge it is consumed, except the final beat, which releases ACTIVE
ownership only when accepted. The other buffer can fill concurrently.
Incomplete next buffers stall rather than reuse old data.

Faults pulse per bank and lock that bank until flush. Reset zeroes public
outputs and invalidates both buffers without resetting bulk tile storage.
Flush immediately suppresses descriptor/read/client traffic and invalidates
all local ownership; only the scheduler drains accepted memory transactions.
One-row/one-beat tiles use the same final-acceptance release rule, idle tail
banks receive no descriptor, and TILE_K=24 uses an explicit bounded input
counter rather than assuming power-of-two tile size.

The wrapper instantiates `banks[g].storage` of type
`anvil_q3_weight_prefetch_bank`. Its scalar ports are the corresponding slices
of the wrapper ports, with the same parameters except BANKS. EMPTY/FILLING/
READY/ACTIVE storage is physically separate for both tiles. Qweight and qzero
reads also check zero padding beyond the logical projection's output extent.
FP16 scale responses require zero high transport bits and valid nonnegative
finite low halves.

### `anvil_q3_add128`

Ports are `clk,rst_n,flush,in_valid,in_ready,out_valid,out_ready,out_error`,
signed128 `in_a,in_b,out_sum`. E0 snapshots both inputs; E1..E8 perform one
16-bit carry segment each. Immediately after E8 out_valid is set; E9 is
the earliest retirement edge. A new command may enter on that retirement
edge. Operands/results are stable while reserved. Signed overflow is reported
with the result. Flush wins over acceptance/retirement. No hidden running
sum is maintained; this differs intentionally from `anvil_q3_accumulator`.

### `anvil_q3_tensor_array`

Parameters are the weight-prefetcher parameters. Ports are
`clk,rst_n,flush,cmd_valid,cmd_ready`, unsigned32 `cmd_epoch,cmd_layer`,
unsigned3 `cmd_proj`, `load_valid,load_ready,load_last`, signed32 `load_data`,
`done,error`, the BANKS scalar memory-client vector, and BANKS output vectors:
`result_valid,result_ready`, unsigned32-per-bank `result_row` and
signed128-per-bank `result_sum`.

E0 accepts a command and snapshots its projection dimensions. On later edges,
load handshakes supply all input activations in ascending input order,
exactly one per edge at most. `load_last` must be asserted on exactly the
final input. The last load edge starts bank work; no descriptor or weight
request precedes complete activation ownership. The tensor array does not
fetch or calculate activations on the host.

Bank g first owns consecutive output rows starting at g*TILE_ROWS; after a
batch's result handshakes it advances by BANKS*TILE_ROWS. Tail banks do no work.
Each row batch receives input tiles in ascending order, with at most two
resident weight descriptors per bank. Prefetch beat acceptance snapshots
activation reads and operands in a register before dot8 E0. `engines[g].dot8`
has its frozen eight stages; row/first/last metadata freezes with those stages.
Each dot8 result enters a segmented adder for its row's exact signed128 sum.
A same-edge completed addition forwards to the next dependent addition
rather than rereading a stale partial sum. Accumulation interlocks can stall
the array; they do not change the dot8 leaf's II=1 contract.

A result is published only after that row's final input beat accumulates,
with no bias, rounding or saturation. Results within a bank follow row order;
different banks may retire independently. Output backpressure retains exact
row/sum ownership. `done,error=0` is a one-cycle completion after all result
handshakes; the next edge returns to command readiness. Faults instead emit
one `done,error=1`, annul local work and wait for flush before accepting another
command. The enclosing controller must flush/drain the shared scheduler before
recovery; tensor completion does not certify external drain completion.

### `anvil_q3_gemv`

Parameters add MAX_SEQ_LEN to the tensor parameters. Command ports add
unsigned32 `cmd_pos` to the tensor command. `done,error` and the
`c_req_*,c_rsp_*` vectors are its remaining ports: the first BANKS clients
belong to tensor weight fills; client BANKS is the scalar load/bias/write
client. All vector fields use the scheduler's scalar memory format.

After command acceptance, GEMV reads kind8 scratch activations and handshakes
them into tensor_array in ascending coordinate order. Sources/targets are:
Q 1->2, K 1->3, V 1->4, O 5->6, gate 8->9, up 8->10, down 11->12.
All scratch accesses use row=slot,col=component and zero layer/projection.
Output bank results are selected round-robin; Q/K/V alone fetch kind4 bias
at the accepted layer/projection, row0,col=output component.
FP16 bias high transport bits must be zero and NaN/Inf fails the command.
Bias conversion is signed Q16.16 and its accumulator contribution is shifted
left16. A segmented add precedes the single ties-away shift16/signed32
saturation. The result is written to kind8, with completion withheld until
its acknowledgement. Model/scalar memory errors terminate explicitly.

GEMV result writes can overlap other banks' weight prefetch and computation.
Done/error pulses only after all output writes acknowledge (or on a fault
requiring outer drain). As with tensor_array, a fault locks command readiness
until flush; an ordinary successful completion returns to idle. This leaf
does not initialize token sequences or perform attention/cache ownership.

## Connected numerical decoder requirements

The following frozen rules govern the connected decoder modules. Their presence
in source is not a numerical verification result:

* RMSNorm: S=sum(x_i^2); mean=floor((S<<32)/H)+18446744073710;
  root=floor_sqrt(mean); reciprocal=floor(2^64/root);
  y_i=sat32(R(x_i*gamma_i*reciprocal,48)). Zero denominator is a fault.
* RoPE pairs component i with i+D/2. Coefficients are ties-away signed-Q2.30
  samples of cos/sin(position*1000000^(-2*i/D)). Products combine before
  one shift30/saturation. Legacy profiles keep the external coefficient
  interface and this pair ordering.
* Q3 GQA maps each group of eight query heads to one KV head. Scores are
  rounded_div(sum(q*k),floor_sqrt(D<<32)). Subtract the causal score maximum
  before E; context is sat32(rounded_div(sum(v*E),sum(E))).
  Rounded division by positive d is sign(x)*floor((abs(x)+floor(d/2))/d).
  At least signed96 score/value accumulation and unsigned64 exponential
  sums are required. Current uncommitted/future KV entries are not readable.
* Residual addition saturates signed32. SwiGLU uses
  sat32(R(SiLU(gate)*up,16)). Tied FP16 vocabulary projection accumulates
  without intermediate rounding in at least signed96 before shift16/saturation.
* Mode1 uses the least e in [0,25] with maxabs<=127*2^e, codes
  clamp(R(x,e),-127,127). Mode2 symmetric uses least e in [0,29] with
  maxabs<=7*2^e, codes clamp(R(x,e),-7,7). Mode2 affine uses the least e
  in [0,32] admitting z in [-8,7] such that all R(x,e)+z lie in [-8,7],
  with minimum |z| and lower-signed tie break. Decode is sat32((code-z)<<e),
  with z=0 for symmetric modes. Q3 blocks are per-head Group32/Group64;
  metadata exponent occupies bits7:0, signed4 z bits11:8, remaining bits zero.
  Legacy INT8 metadata is an exponent word. Mode0 preserves all signed32 bits.
  The codec leaf implements these block operations; external cache commit,
  logical coordinates and explicit attention reads/dequantization are connected
  in the core. Physical byte-address mapping is implemented by
  `fpga/anvil_q3_memory_map.sv` and specified in `fpga/INTEGRATION.md`.

Here R(x,b)=sign(x)*floor((abs(x)+2^(b-1))/2^b) for b>0, and R(x,0)=x.

## FPGA integration interfaces

`fpga/INTEGRATION.md` freezes the additional portable public interfaces and
their cycle/degenerate-boundary table before independent verification. The
new modules do not change `anvil_q3_top` or dot8 ports.

`anvil_q3_fpga_shell` has the top's architectural parameters and connects the
core, host-control CSR slave, tagged DDR bridge and reset/status synchronizers.
Its clock/reset/status inputs are `accel_clk,system_reset_n,pll_locked,
ddr_cal_success,pcie_link_up`. CSR byte-address input is unsigned8;
`csr_read,csr_write` are bits, byteenable is unsigned4, writedata/readdata
unsigned32; waitrequest/readdatavalid/irq are bits. Memory master address is
unsigned64 bytes, writedata/readdata unsigned32, byteenable unsigned4;
read/write/waitrequest/readdatavalid/writeresponsevalid are bits and response
is unsigned2. The target must provide a real response for writes, not assert
writeresponsevalid on mere command issue.

`anvil_q3_memory_map` accepts `start&&ready` with `request_write`,
unsigned4 kind, unsigned3 projection, unsigned32 layer/row/col, and returns
one-cycle done/error with unsigned64 address. `required_bytes` exposes the
compile-time combined extent. Parameters describe the selected architectural
geometry/cache layout; the host allocation formulas and bounds are public.
No flush input is provided: accepted memory ownership survives core cancel.
Mapping faults terminate with a registered error rather than an aliased
address. There is no same-edge command-to-result path.

`anvil_q3_ddr_bridge` accepts the unchanged BANKS tagged memory vectors and
connects the scalar Avalon master above. Its `bridge_fault` pulse reports
unsolicited/wrong-kind DDR responses; ordinary mapped/memory errors remain
associated with their request. A round-robin arbiter owns one request through
its returned core response. Reset is system-wide, not a per-token flush.

`anvil_q3_host_control` exposes the CSR bus, core token/logit/status ports,
synchronized DDR/PCIe levels, bridge_fault, and required_bytes. Its command
and mailbox semantics, precise register offsets, error reporting, cancellation
priority, read latency and reset-only configuration lock are defined in the
integration document and `fpga/anvil_q3_host.h`. The `csr_waitrequest=1`
reset behavior belongs only to the added Avalon slave, not the frozen top.

`anvil_q3_reset_release` asynchronously asserts output rst_n on
system_reset_n=0 or pll_locked=0, then releases after two accel clock edges.
Physical integration must reset/quiesce the DDR response fabric coherently.
PCIe/calibration loss instead causes host-control cancellation/draining;
it does not discard accepted memory transactions by resetting the bridge.

Actual board pins, licensed/generated IP, physical DDR capacity and compatible
PCIe DMA must be positively identified before a bitstream is built. The
project preparer rejects missing prerequisites and does not create fake IP.
The full mandatory Quartus and HIL acceptance gates remain unchanged.

## Static reproduction

From the delivered root, with Icarus Verilog 12.0:

```sh
iverilog -g2012 -t null \
  -s anvil_q3_top -s anvil_q3_fpga_shell \
  -P anvil_q3_fpga_shell.CACHE_MODE=2 \
  -P anvil_q3_fpga_shell.INT4_ASYM=1 rtl/*.sv fpga/anvil_q3_*.sv
```

This only elaborates the current modules. It does not execute parameter
diagnostics, reset, functional simulation, reference comparisons or synthesis,
and it cannot certify timing. The runtime's mandatory verification selectors
remain unchanged and pending.
The actual static-only receipt for this invocation is
`evidence/preparation/static-fpga-ylnsdi89/receipt.json`.
