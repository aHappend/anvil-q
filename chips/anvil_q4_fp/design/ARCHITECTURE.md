# Native floating-point implementation

## Implementation status

The initial design increment implements the native numerical package,
`anvil_q4_fp32`, `anvil_q4_fp_tensor_array`, `anvil_q4_fp_gemv`,
`anvil_q4_fp_mem_port`, `anvil_q4_fp_descriptor`, `anvil_q4_fp_exp`,
`anvil_q4_fp_umul64`, `anvil_q4_fp_silu`, `anvil_q4_fp_rmsnorm`,
`anvil_q4_fp_rope` and `anvil_q4_fp_elementwise`.
It is a partial implementation, not a ready top-level product.
Top/scheduler, decoder/MLP/token-I/O routing, attention, cache,
speculative integration and isolated compatibility remain to be implemented.
Independent functional/synthesis/timing/hardware results are not claimed.
No trained-checkpoint execution is claimed.

The complete admitted contract is in `SPEC.md`, with native signatures
frozen in `NATIVE_INTERFACES.md` before RTL implementation.
No authentic parent generational handoff or linked source index was available.
The supplied parent sources remain provenance, not a native numerical oracle.

## Compute and ownership

The native array keeps FP32 accumulators output-stationary across ascending K.
One real FP32 leaf per active row alternates separately rounded multiplication
and addition. BF16/FP16 widening uses two explicit registers before common
multiplier issue; no dequantizer or integer activation path is present.
The activation tile has synchronous registered reads and no asynchronous
reset writes, preserving memory inference.

GEMV narrows each FP32 scratch activation at the explicit native boundary.
Sixteen logical weight channels remain independent even for smaller BANKS.
Each lane separately records request acceptance, response retirement and a
returned value. It cannot issue another K until the current vector enters
the tensor array. Unused rows never issue traffic. Auxiliary channel 16
loads activations, reads bias and writes scratch.

The array arithmetic pipeline uses the precise edges in SPEC, not a
single-cycle behavioral expression. The compute-only full-vector interval
is 23 clocks per K; this is an analytical schedule, not measured throughput.
At 100MHz the full 16-row schedule has a theoretical upper bound of
16/23 MAC per clock (one multiplication plus one addition per MAC),
before activation loading, memory stalls, tile overhead, bias and output.
No claim of achieved clock or end-to-end speedup follows from that bound.

The scalar stages retain FP32 intermediates. SiLU deliberately follows
`x / round(1 + exp(-x))` for both signs; the parent's negative-input stable
algebra changes the rounding order and is not the native contract.
Descriptor validation uses separately registered full-width dimension/page
products, rejects native quantization and reserved fields, and retains the
parent version-1 validation rules. Sequence invalidation on a successful
descriptor commit remains a top-level integration obligation.

For a full R-row by K-element native tile, weight traffic is R*K logical
reads and activation traffic is K scratch reads. The external payload is
32 bits per read although each native weight uses only its low 16 bits.
Results remain FP32. Smaller TILE_ROWS lowers spatial resources/utilization;
smaller TILE_K increases command/load overhead without changing rounding
or the 17-channel interface. Smaller BANKS introduces scheduler contention.

## Remaining integration obligations

The scheduler must retain complete 64-bit tags, independent response buffers,
fair per-bank slots and cancellation drain ownership. Recorded stage and
scalar subowners must survive phase changes and cancellation, not depend on
current-phase combinational demultiplexing. No outgoing owner may be replaced
until all its held/accepted/buffered work has retired or transferred to drain.

The top must preserve the exact public parent signature and isolate modes
1..4 from native version2/mode5. Copying an old integer/quantized datapath
under a native module name is not an implementation of native arithmetic.

Host images use the inherited logical kind/layer/projection/row/column tuples,
with native row-interleaved banking, low-half native elements, FP32 scratch/
RoPE, and host-mapped page tables. The independent Verifier will supply
deterministic fixture/export helpers and source-bound manifest hashes.

## Reproduction and evidence boundaries

Run the independent portable suites from the delivered root using the six
commands in SPEC once Verifier has authored `tests/verify.py`. They are not
currently present and are not represented as passing. Designer does not
author numerical references, simulation harnesses or synthesis checks.
The shared runtime supplies authoritative timing/fit and physical-board
evidence. The final product PDF is downstream of engineering acceptance,
not an input to design verification.

The first static-only Icarus elaboration failed because the original package
filename sorted after `anvil_q4_fp32.sv` in `rtl/*.sv`.
The receipt is
`evidence/preparation/native-foundation-static-20261103T020343131336Z/receipt.json`.
Renaming the package file to `rtl/anvil_q4_00_fp_pkg.sv` places it before
importing modules without changing package contents. This is a compilation
ordering repair, not numerical verification. No simulation or synthesis
harness was authored or executed.
