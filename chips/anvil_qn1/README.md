# Anvil-QN1

**Connected Designer RTL; independent verification and acceptance pending.**
The native top is `anvil_qn1_top`, defaulting to Qwen3-4B production
geometry. Native arithmetic, tensor, fused QK-Norm/RoPE, speculative-controller,
CSR, tagged memory scheduler, GEMV, ordinary norm, attention, MLP, residual and
projected-head buffer sources are connected through the native decoder/top.
See [SPEC](design/SPEC.md) for the frozen numerical and
transaction contract and [ARCHITECTURE](design/ARCHITECTURE.md) for actual
implementation status.

## Sources and compatibility

`rtl/anvil_qn1_*.sv` are native BF16/binary32 sources. Compile
`anvil_qn1_00_pkg.sv` first. The tensor has 256 dynamic W4A16/BF16-weight lanes;
the fused head uses per-head gamma and theta=1e6 split-half RoPE. Leaf public
ports are declared in their source modules; the fixed top ports are
listed in SPEC.md and implemented in `rtl/anvil_qn1_top.sv`.
Scratch memory uses layer/projection zero, with the parent-compatible
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
iverilog -g2012 -t null -s anvil_qn1_top rtl/anvil_qn1_*.sv
iverilog -g2012 -t null -s anvil_qn1_top \
  -Panvil_qn1_top.PROFILE=1 rtl/anvil_qn1_*.sv
iverilog -g2012 -t null -s anvil_qn1_top \
  -Panvil_qn1_top.PROFILE=2 rtl/anvil_qn1_*.sv
iverilog -g2012 -t null -s anvil_q3_top rtl/anvil_q3_*.sv
```

These are syntax/elaboration commands, not functional or timing verification.
The integrated default-profile native top and legacy top statically elaborated
together without diagnostics using Icarus 12.0; the exact source/command receipt
is `evidence/preparation/integrated-final-static-20261102T180811Z-9289c67d/receipt.json`.
It is advisory syntax evidence only, not a result for the independent
three-profile smoke matrix or the additional commands above.

## Memory images and host sequencing

Native scalar images store finite BF16 in low 16 bits with high 16 bits zero.
AWQ weights/zeros use packed unsigned nibbles with shifts
[0,16,4,20,8,24,12,28]; a symmetric image uses zero point 8. Separate group
scales are nonnegative finite BF16. The tied embedding/LM matrix and learned
normalization weights are BF16. RoPE images use BF16-rounded cosine/sine from
angle=p*1000000^(-2*i/HEAD_DIM), at row p and columns 2*i,2*i+1. Native bias
requests are forbidden. SPEC.md defines every logical memory kind, projection
extent, scratch row and reserved bit.

The host supplies images; no checkpoint is compiled into RTL. A portable
coefficient-image example for the five required boundary positions follows.
It uses 90-digit Decimal arithmetic, split-half frequencies and direct
ties-to-even BF16 quantization, not an intermediate BF16/Q16 approximation.
Each text line is `row column low16_hex` for kind11; high16 is zero on the
memory bus. Select a legal HEAD_DIM and generate further positions as needed.
This is image preparation, not a numerical checker; Verifier must independently
derive and compare the coefficients and resulting DUT values.

```sh
mkdir -p checkpoint-images
python3 - <<'PY' > checkpoint-images/rope-128.txt
from decimal import Decimal, localcontext

HEAD_DIM = 128
POSITIONS = (0, 1, 32767, 32768, 40959)
PI = Decimal("3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825342117")

def bf16(x):
    sign = 0x8000 if x.is_signed() else 0
    n, d = abs(x).as_integer_ratio()
    if not n:
        return sign
    e = n.bit_length() - d.bit_length()
    below = n < (d << e) if e >= 0 else (n << -e) < d
    if below:
        e -= 1
    e = max(e, -126)
    shift = 7 - e
    a, b = (n << shift, d) if shift >= 0 else (n, d << -shift)
    q, r = divmod(a, b)
    q += (2*r > b) or (2*r == b and bool(q & 1))
    if q == 256:
        q = 128
        e += 1
    exponent = e + 127 if q >= 128 else 0
    return sign | (exponent << 7) | (q & 127)

def sincos(angle):
    tau = 2*PI
    x = angle % tau
    if x > PI:
        x -= tau
    s, c, st, ct = x, Decimal(1), x, Decimal(1)
    k = 1
    while True:
        st *= -x*x / Decimal((2*k)*(2*k+1))
        ct *= -x*x / Decimal((2*k-1)*(2*k))
        s += st
        c += ct
        if max(abs(st), abs(ct)) < Decimal("1e-85"):
            return c, s
        k += 1

with localcontext() as ctx:
    ctx.prec = 90
    frequencies = [
        (-Decimal(2*i)*Decimal(1000000).ln()/Decimal(HEAD_DIM)).exp()
        for i in range(HEAD_DIM//2)
    ]
    for p in POSITIONS:
        for i, frequency in enumerate(frequencies):
            c, s = (Decimal(1), Decimal(0)) if p == 0 else sincos(Decimal(p)*frequency)
            print(p, 2*i, f"{bf16(c):04x}")
            print(p, 2*i+1, f"{bf16(s):04x}")
PY
```

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

| Claim | Current evidence/status |
|---|---|
| Connected native/legacy source syntax | Integrated-top static receipt above; Icarus 12.0, exit0, no diagnostics |
| Parent preservation | Same receipt records all 26 byte-identical delivered copies |
| Numerical/protocol/benchmark parity and fusion overhead | Pending independent L1 checks; no result claimed |
| Generic synthesis and live hierarchy | Pending independent synthesis check |
| 100 MHz Arria10 fit/STA and physical PCIe HIL | Pending shared-runtime gates, not inferred from syntax |
| Approved product PDF | Shared-runtime post-acceptance deliverable, not a pre-design prerequisite |
