# Anvil-D1 architecture

## Implementation and evidence boundary

`anvil_d1_top` connects embedding, every decoder layer, final normalization,
vocabulary projection and CSRs. Each native decoder instantiates the named MLA
and router/DMA engines. Legacy mode instantiates the immutable parent directly.
No expected answers, verification oracle, checkpoint adapter or synthetic
affinity input replaces a native datapath.

Target: Intel Arria 10 GX 10AX115N2F45E1SG, synchronous 100 MHz or faster.
No timing closure, resource utilization or board result has yet been obtained.
The historical `GENERATIONAL_HANDOFF.md` input is absent.

## Connected datapath

```
token -> embedding -> hidden
  -> [norm0 -> absorbed MLA -> attention residual
      -> norm1 -> dense or (shared0 + shared1 + Top-K routed) -> residual]
     repeated for every layer
  -> final native norm -> vocabulary projection -> ascending accepted logits

raw MLA weights -> hardware absorption -> exact signed 96-bit A/B in DDR
                                         |
compressed causal cache <-> two-pass MLA --+

router affinity tensor -> full softmax -> stable Top-K -> normalized weights
                              |
shared execution (client 0)    +-> actual first-tile prefetch (client 1)
                              +-> retained tiles -> routed execution

all clients -> tagged bank scheduler -> external banked memory
accepted events/completion deltas -> saturating live CSR counters
                                  -> atomic snapshot -> host ratio calculation
```

The native scheduler wrapper reuses the parent ownership/tag/reorder engine
but gates both external request valid and the ready fed back into that engine
on flush. This closes the parent's request-annul boundary for native
cancellation without changing legacy behavior. Accepted ownership drains;
unaccepted held requests are annulled.

## Arithmetic allocation and lifetime

| Resource | Storage / precision | Ownership |
|---|---|---|
| mul32 | four 16-bit partials, registered cross/limb sums, 64-bit result | acceptance through result retirement |
| mul96x32 | three mul32 instances and registered 128-bit limb assembly | acceptance through result retirement |
| add128 | operands, four 32-bit carry stages, held 128-bit result | acceptance through result retirement |
| accumulator | committed 128-bit sum and separate add128 | sum commits on result handshake |
| unsigned divider | numerator shift register, quotient, bounded remainder | D0 through result retirement |
| signed divider | magnitude/sign prep, unsigned divider, sign-restored result | S0 through result retirement |
| integer root | 128-bit radicand shift register, 64-bit root, 66-bit remainder | 64 digit iterations plus registered output |
| round/saturate | one held 32-bit boundary result | acceptance through result retirement |

Multiplication is exact, with no truncation of cross terms. Unsigned lower
limbs in the 96-bit multiplier receive explicit b*2^32 correction before
128-bit assembly. Sign-extension terms participate in the upper limbs.
No variable-width multiplication, combinational division or combinational
root chain is hidden inside a helper function.

The subtract helper has parallel 16-bit sums and a logarithmic prefix of
block generate/propagate bits. Restoring iteration count remains fixed by
operand width; memory and algorithm schedules remain variable.

Native RMSNorm shares a 32x32 multiplier, accumulator, 128-bit adder, unsigned
divider, registered root, 96x32 multiplier and boundary rounder. Gamma remains
a full native word. Multiplication by the 64-bit reciprocal is decomposed into
two registered products, signed-limb correction, and registered accumulation.
No reciprocal or product is clipped before R_48.

Exponential range reduction and all six Taylor divisions use registered
integer dividers. SiLU uses the stable sign-dependent sigmoid numerator and
a widened -abs(x), then a separate mul32 and R_24 boundary. The exact normal
and shortcut schedules are in SPEC.md; no simulator has yet checked them.
The exponential's two 32-bit multiplier operands use explicitly signed
wire aliases rather than casts directly on module ports, avoiding the
Yosys 0.33 AST-to-wire signedness assertion. These aliases preserve all
operand bits and add no arithmetic, narrowing or pipeline stages; independent
frontend and functional checks of this repair remain required.
SiLU likewise connects its 33-bit negative-absolute exponential argument and
32-bit sigmoid multiplier operand through explicitly signed wire aliases.
This applies the same frontend compatibility repair without changing operand
bits, widths, numerical boundaries, state transitions or pipeline timing.

Hardware absorption streams UK/QN pairs for A and O/UV pairs for B. It keeps
one pair of raw weights, one registered product, one 128-bit accumulator and
one 96-bit completed coefficient. Three acknowledged little-word-first writes
commit that coefficient to DDR. A per-layer epoch-valid table records only
fully completed A/B construction, never partially written coefficients.
This deliberately folded implementation prioritizes exact arithmetic and
bounded state, not an unmeasured throughput claim.

## Storage hierarchy

Production absorbed A/B matrices reside in DDR as three-word coefficients.
They must not become production-size FPGA register arrays.
Compressed cache contains only rank latent and rope key words per causal
position/layer. Two history passes read each word once across all heads.
One token's compressed vector and all head contexts may be retained on chip.
Expert data uses bounded first tiles plus compute ping-pong tiles, not a full
expert cache. Any future inferred RAM must have explicit initialization-valid
ownership; reset does not clear DDR or authorize an uninitialized read.

| Native storage | Maximum declared payload | Lifetime / initialization |
|---|---:|---|
| Loaded queries | 16*(512+64)*32 = 294912 bits | All query words acknowledged before history |
| One compressed token | (512+64)*32 = 18432 bits | All causal-token words loaded before any head |
| Context numerators | 16*512*128 = 1048576 bits | First causal token selects zero as prior sum |
| Per-head max/Z | 16*(32+64) = 1536 bits | Reset at each MLA command |
| Winning first tiles | 6*8*128*32 = 196608 bits | Per-winner valid after acknowledged fill |
| Expert compute banks | 2*8*128*32 = 65536 bits | Projection/row/column tags validate complete fills |
| Mixture numerators | 2048*128 = 262144 bits | First shared expert selects zero as prior sum |

These are architectural declarations, not synthesized resource results.
Large storage uses synchronous read/write processes without asynchronous RAM
reset; command/epoch ownership protects initialization. No production absorbed
matrix or sequence-length cache is allocated in FPGA registers.

### MLA dataflow and reuse

Hardware absorption completes once per layer/weight epoch. Its matrix words
are streamed from DDR by the shared tensor engine rather than retained as a
production on-chip matrix. The tensor's B mode explicitly advances the head
field when its rank counter wraps and retains a single exact accumulator
across all heads before R_32.

D writes the new latent directly into cache. KR temporarily uses rope scratch,
then rotates into the new token's key-cache suffix. Query A and QR/RoPE tensors
occupy their documented scratch objects and are loaded into query RAM. Two
history passes each read every compressed scalar once across all heads. The
first finds architectural-score maxima. The second accumulates exponentials
and exact exponential-weighted latent numerators from the same one-token
buffer. Direct rational context division/half-tie rounding is separate from
diagnostic probability quantization.

The theoretical production cache traffic for a command at causal length L is
`2304*(2*L+1)` bytes: two full causal reads plus one current-token write.
The explicit MHA denominator is `20480*(2*L+1)`. These formulas are analytical
targets for independently counted public transactions, not measured savings.
The baseline counter adds one full dense vector at the first accepted scalar
of each corresponding cache traversal. Raw weights, absorbed writes and
scratch accesses are classified separately.

### Shared/routed work and retained tiles

The affinity tensor uses normalized hidden, not externally supplied scores.
Full-softmax probabilities and stable Top-K scans precede coefficient
normalization. A three-way mux gives client 0 to affinity, expert execution
or mixture work. Client 1 has a separate memory port and prefetch FSM.
Neither FSM's readiness depends on the other's memory service.

First gate tiles have fixed TILE_K row stride and skip invalid final
rows/columns. Routed expert execution reads the retained winning tile using
a registered tile-response slot. Later tiles use two alternating compute
banks tagged by projection and row/column block. The folded scalar MAC
schedule can evict/refetch compute tiles; actual parameter-byte counters
include every such read rather than claiming ideal active-parameter traffic.

Each shared/routed expert runs complete biased gate/up/down SwiGLU. Shared
outputs receive coefficient one; selected routed outputs receive their exact
normalized Q0.24 coefficients. A synchronous signed-128 mixture RAM prevents
premature per-expert summation rounding. Dense-first layers use expert 127,
the dense intermediate width and no extra mixture boundary.

### Integration and command ownership

| Scheduler client | Owner |
|---:|---|
| 0 | Reused native per-layer normalization |
| 1 | MLA absorption/projection/rotation/history subcontrollers |
| 2 | Router affinity, expert tensor or mixture controller |
| 3 | Winning routed weight prefetch |
| 4 | Decoder residual reads/writes |
| 5 | Final native normalization |
| 6 | Native embedding and vocabulary projection |

Kind-8 hidden/norm slots and D1 kind-15 output/work slots are distinct.
The decoder reads each residual/branch pair explicitly and writes the next
parent-compatible hidden slot. SPEC.md records exact slots and their lifetimes.
Subcontroller muxes only change ownership after completion and never change
the route of an outstanding transaction. Fault or cancellation transfers
accepted external ownership to scheduler drain before any new token.

There is a single active token. New sequences invalidate local epoch/tile
validity, and failed or cancelled tokens invalidate sequence continuity.
Every vocabulary logit is registered and can stall independently of memory.
Final-logit acceptance, not first presentation, produces token completion.

RMSNorm streams its source twice: once for S and once for x/gamma output.
It stores no H-wide vector and uses parent-compatible kind-8 scratch slots
documented in SPEC.md. Gamma reads and output writes are acknowledged.
The leaf memory port exposes response transfer directly to its controller,
avoiding an extra registered-completion cycle after final write acknowledgement.
Its `flush` annuls the local view only; the upstream scheduler must atomically
take over all accepted ownership and drain it. Unsolicited responses fault.

## CSR behavior

CSR lives independently of the token pipeline. A registered response slot
allows one outstanding request; neither response valid nor payload depends on
response ready. Live counters are 64-bit saturating. Atomic snapshots copy the
pre-edge live bank, including every domain, without stopping live updates.
Clear invalidates snapshots and wins over simultaneous increments.

The block exports internal configuration signals for top-level delimiter
comparison and domain attribution. It does not infer reasoning from text.
Per-domain cycle attribution uses the token-active interval; global cycles
measure armed elapsed time. All ratio calculations remain host-side.

## Independent handoff

Designer performs only fast static syntax/elaboration. Independent Verifier
owns numerical/reference fixtures, functional simulation, mutation sensitivity,
compatibility, synthesis and clean-copy reproduction. All five admitted L1
commands remain required; current timing lint, Quartus STA and physical HIL
remain shared-runtime gates. No generic or historical result certifies them.
The runtime-generated independently reviewed product PDF follows engineering
acceptance and is not an input to any of these checks.
