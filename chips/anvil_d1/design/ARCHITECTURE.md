# Anvil-D1 architecture

## Implementation increment

The current increment is the arithmetic/normalization/CSR foundation. There
is deliberately no placeholder `anvil_d1_top` returning canned results.
The remaining native pipeline is an implementation obligation, not a claimed
feature of these partial sources.

Target: Intel Arria 10 GX 10AX115N2F45E1SG, synchronous 100 MHz or faster.
No timing closure, resource utilization or board result has yet been obtained.
The historical `GENERATIONAL_HANDOFF.md` input is absent.

## Intended connected datapath

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

The eventual native decoder must instantiate the literal MLA and router/DMA
modules. Top must instantiate that decoder and the CSR block. Legacy mode
must instantiate the actual immutable parent, not reimplement its arithmetic.
The accepted parent scheduler and interfaces are prior art; new native
cancellation must suppress new external requests while retaining ownership
until drain. Reusing an unmodified parent block cannot waive that requirement.

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

## Storage hierarchy

Production absorbed A/B matrices reside in DDR as three-word coefficients.
They must not become production-size FPGA register arrays.
Compressed cache contains only rank latent and rope key words per causal
position/layer. Two history passes read each word once across all heads.
One token's compressed vector and all head contexts may be retained on chip.
Expert data uses bounded first tiles plus compute ping-pong tiles, not a full
expert cache. Any future inferred RAM must have explicit initialization-valid
ownership; reset does not clear DDR or authorize an uninitialized read.

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

## Remaining work before a ready design handoff

Implement and connect hardware absorption, reusable native tensor/activation
execution, two-pass MLA, router/dual-client retained prefetch, expert SwiGLU,
decoder residual sequencing, embedding/projection, parameter guards, native
bank scheduling/cancellation, legacy top selection and telemetry aggregation.
Finish exact schedules and integration documentation for those modules.
Then perform at most a fast static syntax/elaboration check and hand off to
Verifier for all independent simulation, numerical, mutation and synthesis
work. Do not treat this partial increment as satisfying those obligations.
