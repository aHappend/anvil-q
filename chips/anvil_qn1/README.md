# Anvil-QN1

**Implementation in progress; not an accepted or complete accelerator.**
The intended native top is `anvil_qn1_top`, defaulting to Qwen3-4B production
geometry. Native arithmetic, tensor, fused QK-Norm/RoPE, speculative-controller,
CSR, tagged memory scheduler, GEMV, ordinary norm, attention, MLP, residual and
projected-head buffer sources are present. Native decoder/top and end-to-end
integration are still outstanding. See [SPEC](design/SPEC.md) for the frozen numerical and
transaction contract and [ARCHITECTURE](design/ARCHITECTURE.md) for actual
implementation status.

## Sources and compatibility

`rtl/anvil_qn1_*.sv` are native BF16/binary32 sources. Compile
`anvil_qn1_00_pkg.sv` first. The tensor has 256 dynamic W4A16/BF16-weight lanes;
the fused head uses per-head gamma and theta=1e6 split-half RoPE. Leaf public
ports are declared in their source modules; the eventual fixed top ports are
listed in SPEC.md. New memory/numerical engines are not yet connected into
that top. Scratch memory uses layer/projection zero, with the parent-compatible
row meanings documented in SPEC.md.

`anvil_q3_reference/rtl/` contains the 26 supplied parent files, preserved
unchanged. Byte-identical copies ship as `rtl/anvil_q3_*.sv`. The legacy top
remains `anvil_q3_top`, with its original FP16/Q16 payloads and parameters.
Compile **either** parent tree or delivered copies, never both. Native BF16
images are not legacy FP16/Q16 images.

`design/GENERATIONAL_HANDOFF.md` was not supplied. No historical timing/PPA
numbers or inherited passing baseline are claimed.

## Static source commands

From the project root, using an installed SystemVerilog-capable Icarus:

```sh
iverilog -g2012 -t null -s anvil_qn1_tensor_array \
  -s anvil_qn1_qknorm_rope -s anvil_qn1_dual_think_ctrl \
  -s anvil_qn1_csr_perf -s anvil_qn1_parameters \
  -s anvil_qn1_bank_scheduler -s anvil_qn1_gemv \
  -s anvil_qn1_rmsnorm -s anvil_qn1_norm_memory \
  -s anvil_qn1_attention -s anvil_qn1_mlp \
  -s anvil_qn1_elementwise -s anvil_qn1_head_buffer \
  -s anvil_qn1_exp -s anvil_qn1_silu rtl/anvil_qn1_*.sv
iverilog -g2012 -t null -s anvil_q3_top rtl/anvil_q3_*.sv
```

These are syntax/elaboration commands, not functional or timing verification.
There is no runnable native top command until native integration is completed.
The saved engine roots statically elaborated without diagnostics using
Icarus 12.0; the exact source/command receipt is
`evidence/preparation/memory-arithmetic-static-20261102T175050Z-a28f1429/receipt.json`.
It is advisory syntax evidence only.

## Memory images and host sequencing

Native scalar images store finite BF16 in low 16 bits with high 16 bits zero.
AWQ weights/zeros use packed unsigned nibbles with shifts
[0,16,4,20,8,24,12,28]; a symmetric image uses zero point 8. Separate group
scales are nonnegative finite BF16. The tied embedding/LM matrix and learned
normalization weights are BF16. RoPE images use BF16-rounded cosine/sine from
angle=p*1000000^(-2*i/HEAD_DIM), at row p and columns 2*i,2*i+1. Native bias
requests are forbidden. SPEC.md defines every logical memory kind, projection
extent, scratch row and reserved bit.

Assert asynchronous active-low reset before work; every public output is zero
during reset. Start a sequence with new_sequence=1 and position zero. Supply
tokens only on ready/valid transfers and hold stalled payloads. Thinking
drafts transfer only after token acceptance and successful root completion.
After a generated batch, resubmit **only its final generated token**, exactly
at its published final position, to materialize its deferred KV. Do not resend
already evaluated drafts. A terminal position generates a final frame without
another commit. Cancellation drains accepted memory requests and invalidates
continuation; start a fresh sequence after a fault.

## Independent verification and claims

The independent Verifier owns `tests/*.py`, including `tests/verify.py`, which
is not present yet. Required installed tools are Python 3, Icarus/vvp,
Verilator, g++, make and Yosys; actual versions must be recorded with execution.
No tool installation or private environment/cache is part of reproduction.
Once authored by Verifier, the admitted entry points are:

```sh
python3 tests/verify.py
python3 tests/verify.py --suite smoke
python3 tests/verify.py --suite numerical
python3 tests/verify.py --suite behavior
python3 tests/verify.py --suite benchmark --domain gsm8k
python3 tests/verify.py --suite benchmark --domain humaneval
python3 tests/verify.py --suite benchmark --domain mmlu
python3 tests/verify.py --suite benchmark --domain boolq
python3 tests/verify.py --suite benchmark --domain hellaswag
python3 tests/verify.py --suite defects
python3 tests/verify.py --suite synthesis
python3 tests/verify.py --suite reproduce
```

These are required future checks, **not results or currently implemented test
commands**. L1 requires real independent comparisons, defect sensitivity and
synthesis; compact domain tests are numerical-parity workloads, not pretrained
accuracy benchmarks. Static preparation receipts, if any, live under fresh
`evidence/preparation/` subdirectories and cannot establish acceptance.
L1 receipts belong under fresh `evidence/l1-<suite>-<timestamp_or_hash>/`
directories. Failed runs must be retained, not replaced by later successes.

100 MHz timing and PPA require actual shared-runtime Quartus 17.1 Arria 10
10AX115N2F45E1SG evidence. Physical PCIe Gen3x8 claims require the native HIL
gate. No such result is claimed here. The independently approved product PDF
is authored by the shared runtime after engineering acceptance; its absence
before that stage is not a verification failure.
