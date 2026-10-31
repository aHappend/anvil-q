"""Generated public-pin checkers and independent vector generators.

Coverage is credited only by completed comparisons. All fixtures are regenerated
from the declared seeds and numerical contract, not previous execution output.
"""

from fractions import Fraction
import itertools
import math
from pathlib import Path
import random
import shutil
import uuid

from evidence import ROOT, execute, relative, require_success, write_json
import ieee_reference as ref


SEEDS = (17, 43, 89)
PREFIX = "anvil_q1_ht2_"
HEADER = r"""
`timescale 1ns/1ps
module tb;
  reg clk=0, rst_n=0;
  always #5 clk=~clk;
  integer fd, rc, row=0, checked=0, cycles=0;
  task tick;
    begin @(posedge clk); #1; cycles=cycles+1;
      if (cycles>500000) $fatal(1,"CYCLE_BOUND");
    end
  endtask
"""


def emit_rows(path, rows):
    count = 0
    with path.open("x") as stream:
        for row in rows:
            stream.write(" ".join(f"{int(item):x}" for item in row) + "\n")
            count += 1
    if not count:
        raise AssertionError("empty fixture")
    return count


def simulate(directory, name, body, modules, simulator="verilator", rtl_dir=None):
    work = directory / f"{name}-{uuid.uuid4().hex[:8]}"
    work.mkdir(exist_ok=False)
    tb = work / "tb.sv"
    tb.write_text(HEADER + body + "\nendmodule\n")
    source_dir = rtl_dir or ROOT / "rtl"
    sources = [source_dir / (PREFIX + module + ".sv") for module in
               dict.fromkeys(["00_fp_pkg", "reset_sync"] + modules)]
    inputs = [tb, *sources, *sorted(directory.glob("*.txt"))]
    source_paths = [relative(p) for p in sources]
    if simulator == "iverilog":
        binary = work / "simulation.vvp"
        require_success(execute(
            ["iverilog", "-g2012", "-Wall", "-s", "tb", "-o", relative(binary),
             *source_paths, relative(tb)], directory, name + "-compile",
            inputs=inputs,
        ))
        result = execute(["vvp", relative(binary)], directory, name + "-simulate",
                         timeout=55, inputs=inputs)
    else:
        obj = work / "compile-obj"
        try:
            require_success(execute(
                ["verilator", "--binary", "--timing", "-Wno-fatal", "--top-module", "tb",
                 "--Mdir", relative(obj), "-j", "2", "-o", "simulation",
                 *source_paths, relative(tb)], directory, name + "-compile",
                timeout=1200, inputs=inputs,
            ))
            result = execute([relative(obj / "simulation")], directory, name + "-simulate",
                             timeout=600, inputs=inputs)
        finally:
            if obj.exists():
                # Only this invocation's named, settled compiler directory.
                shutil.rmtree(obj)
    run = require_success(result)
    output = (run / "stdout.txt").read_text()
    summaries = [line for line in output.splitlines() if line.startswith("CHECK ")]
    if len(summaries) != 1:
        raise AssertionError(f"missing/duplicate comparison summary: {relative(run)}")
    parts = dict(field.split("=", 1) for field in summaries[0].split()[1:])
    if int(parts["compared"]) <= 0:
        raise AssertionError("no actual comparisons")
    return {"name": name, "simulator": simulator, **parts,
            "receipt": relative(run / "receipt.json")}


DIRECTED16 = (0, 0x8000, 1, 2, 0x007F, 0x0080, 0x03FF, 0x0400, 0x3BFF,
              0x3C00, 0x3F7F, 0x3F80, 0x3F81, 0x7BFF, 0x7C00, 0x7C01,
              0x7F7F, 0x7F80, 0x7F81, 0x7FFF, 0xFFFF)
DIRECTED32 = (0, 0x80000000, 1, 2, 0x007FFFFF, 0x00800000, 0x00800001,
              0x3F000000, 0x3F7FFFFF, 0x3F800000, 0x3F800001, 0x33800000,
              0xBF800000, 0x7F7FFFFF, 0x7F800000, 0xFF800000, 0x7F800001,
              0x7FC00000, 0xFFFFFFFF)


def conversion_rows():
    for fp16, fmt in enumerate((ref.BF16, ref.FP16)):
        for bits in range(65536):
            expanded = ref.convert(bits, fmt, ref.FP32)
            yield (fp16, bits, expanded, expanded,
                   ref.convert(expanded, ref.FP32, fmt),
                   int(ref.kind(expanded) in ("nan", "inf")),
                   int(ref.kind(expanded) == "nan"))
    for seed in SEEDS:
        rng = random.Random(seed)
        for fp16, fmt in enumerate((ref.BF16, ref.FP16)):
            for bits in (*DIRECTED32, *(rng.getrandbits(32) for _ in range(10000))):
                yield (fp16, 0, 0, bits, ref.convert(bits, ref.FP32, fmt),
                       int(ref.kind(bits) in ("nan", "inf")), int(ref.kind(bits) == "nan"))


def conversions(directory, simulator="iverilog", rtl_dir=None):
    vectors = directory / "conversions.txt"
    count = emit_rows(vectors, conversion_rows())
    body = r"""
  import anvil_q1_ht2_fp_pkg::*;
  reg fp16;
  reg [15:0] bits16, expected_narrow;
  reg [31:0] expected_expand, bits32;
  reg expected_nonfinite, expected_nan;
  initial begin
    fd=$fopen("VECTORS","r");
    if (!fd) $fatal(1,"FIXTURE_OPEN");
    while (!$feof(fd)) begin
      rc=$fscanf(fd,"%h %h %h %h %h %h %h\n",fp16,bits16,expected_expand,
                 bits32,expected_narrow,expected_nonfinite,expected_nan);
      if (rc!=7) $fatal(1,"FIXTURE_PARSE row=%0d rc=%0d",row,rc);
      if (expand16(bits16,fp16)!==expected_expand)
        $fatal(1,"EXPAND row=%0d input=%h format=%b got=%h expected=%h",
               row,bits16,fp16,expand16(bits16,fp16),expected_expand);
      if (narrow32(bits32,fp16)!==expected_narrow)
        $fatal(1,"NARROW row=%0d input=%h format=%b got=%h expected=%h",
               row,bits32,fp16,narrow32(bits32,fp16),expected_narrow);
      if (fp32_nonfinite(bits32)!==expected_nonfinite ||
          fp32_nan(bits32)!==expected_nan) $fatal(1,"CLASSIFY row=%0d",row);
      row=row+1; checked=checked+4;
    end
    if (row!=COUNT) $fatal(1,"COVERAGE");
    $display("CHECK compared=%0d rows=%0d exhaustive_per_format=65536",checked,row);
    $finish;
  end
"""
    body = body.replace("VECTORS", relative(vectors)).replace("COUNT", str(count))
    return simulate(directory, "conversions-" + simulator, body, [], simulator, rtl_dir)


def pipeline_rows():
    pipes = [[None] * 3, [None] * 3, [None] * 4]
    for seed in SEEDS:
        rng = random.Random(seed)
        directed = list(itertools.product(DIRECTED16, repeat=2))
        wide = list(itertools.product(DIRECTED32, repeat=2))
        # All three seeds contribute to each format's 10,000-case minimum.
        for i in range(21000):
            reset = i in (0, 130, 10200)
            enable = i < 10 or rng.randrange(6) != 0
            valid = i > 5 and rng.randrange(8) != 0
            fmt = ref.FP16 if i & 1 else ref.BF16
            a, b = directed[i] if i < len(directed) else (rng.getrandbits(16), rng.getrandbits(16))
            c, d = wide[i] if i < len(wide) else (rng.getrandbits(32), rng.getrandbits(32))
            values = [ref.multiply(a, b, fmt), ref.multiply(c, d), ref.add(c, d)]
            if reset:
                pipes = [[None] * 3, [None] * 3, [None] * 4]
            elif enable:
                for pipe, result in zip(pipes, values):
                    pipe.pop()
                    pipe.insert(0, result if valid else None)
            expected = []
            for pipe in pipes:
                result = pipe[-1]
                expected += [result is not None, result or 0]
            yield (not reset, enable, valid, i & 1, a, b, c, d, *expected)
    for _ in range(4):
        for pipe in pipes:
            pipe.pop()
            pipe.insert(0, None)
        expected = []
        for pipe in pipes:
            expected += [pipe[-1] is not None, pipe[-1] or 0]
        yield (1, 1, 0, 0, 0, 0, 0, 0, *expected)


def pipelines(directory, simulator="verilator", rtl_dir=None):
    vectors = directory / "pipelines.txt"
    count = emit_rows(vectors, pipeline_rows())
    body = r"""
  reg enable=0, iv=0, fp16=0;
  reg [15:0] a16=0,b16=0;
  reg [31:0] a32=0,b32=0;
  wire v16,vm,va;
  wire [31:0] d16,dm,da;
  reg ev16, evm, eva;
  reg [31:0] ed16, edm, eda;
  reg next_reset;
  integer n16=0,nm=0,na=0;
  anvil_q1_ht2_fp16_mul u16(clk,rst_n,enable,iv,fp16,a16,b16,v16,d16);
  anvil_q1_ht2_fp32_mul um(clk,rst_n,enable,iv,a32,b32,vm,dm);
  anvil_q1_ht2_fp32_add ua(clk,rst_n,enable,iv,a32,b32,va,da);
  task reset_check;
    begin
      if ({v16,vm,va,d16,dm,da} !== 99'b0) $fatal(1,"RESET_OUTPUT_XZ");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    #0;
    RESET_DELTA
    fd=$fopen("VECTORS","r");
    if (!fd) $fatal(1,"FIXTURE_OPEN");
    while (!$feof(fd)) begin
      @(negedge clk); #1;
      rc=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
        next_reset,enable,iv,fp16,a16,b16,a32,b32,ev16,ed16,evm,edm,eva,eda);
      if (rc!=14) $fatal(1,"FIXTURE_PARSE row=%0d rc=%0d",row,rc);
      rst_n=next_reset;
      tick();
      if ({v16,d16} !== {ev16,ed16})
        $fatal(1,"MUL16 row=%0d got=%h:%h expected=%h:%h",row,v16,d16,ev16,ed16);
      if ({vm,dm} !== {evm,edm})
        $fatal(1,"MUL32 row=%0d got=%h:%h expected=%h:%h",row,vm,dm,evm,edm);
      if ({va,da} !== {eva,eda})
        $fatal(1,"ADD32 row=%0d got=%h:%h expected=%h:%h",row,va,da,eva,eda);
      if (enable && rst_n) begin n16=n16+v16; nm=nm+vm; na=na+va; end
      row=row+1; checked=checked+3;
    end
    if (row!=COUNT || n16<30000 || nm<30000 || na<30000) $fatal(1,"COVERAGE");
    $display("CHECK compared=%0d mul16=%0d mul32=%0d add32=%0d",checked,n16,nm,na);
    $finish;
  end
"""
    # Verilator timing mode does not implement #0 inactive-region scheduling.
    body = body.replace("    #0;\n    RESET_DELTA",
                        "    #1; reset_check();" if simulator == "verilator" else "    #0; reset_check();")
    body = body.replace("VECTORS", relative(vectors)).replace("COUNT", str(count))
    return simulate(directory, "pipelines-" + simulator, body,
                    ["fp16_mul", "fp32_mul", "fp32_add"], simulator, rtl_dir)


def scalar_vectors(kind):
    if kind == "divsqrt":
        for a, b in itertools.product(DIRECTED32, repeat=2):
            yield (0, a, b, ref.divide(a, b), 0, 0)
        for a in DIRECTED32:
            yield (1, a, 0, ref.sqrt(a), 0, 0)
        for seed in SEEDS:
            rng = random.Random(seed)
            for i in range(1200):
                a, b = rng.getrandbits(32), rng.getrandbits(32)
                op = i & 1
                yield (op, a, b, ref.sqrt(a) if op else ref.divide(a, b), 0, 0)
    elif kind == "exp":
        samples = [ref.rounded(Fraction(i, 8)) for i in range(-832, 713, 2)]
        samples += list(DIRECTED32)
        _, ln2 = ref.mathematical_constants()
        for k in range(-150, 129):
            center = ref.rounded((k + Fraction(1, 2)) * ln2)
            samples.extend([center - 1, center, center + 1])
        for a in samples:
            expected = ref.exp32(a)
            if ref.kind(a) in ("finite", "zero") and ref.kind(expected) not in ("nan", "inf"):
                with ref.localcontext() as ctx:
                    ctx.prec = 100
                    x = ref.value(a)
                    exact = (ref.Decimal(x.numerator) / ref.Decimal(x.denominator)).exp()
                    measured = ref.value(expected)
                    if abs(measured - Fraction(exact)) > Fraction(exact) / 32768 + ref.pow2(-149):
                        raise AssertionError(f"exp mathematical bound input={a:08x}")
            yield (0, a, 0, expected, 0, 0)
    elif kind == "sincos":
        pi, _ = ref.mathematical_constants()
        samples = [0, 0x80000000, 1, 0x80000001, ref.rounded(32768), ref.rounded(-32768)]
        for k in (1, 2, 3, 7, 31, 127, 1024, 16384, 20860):
            center = ref.rounded(k * pi / 2)
            if center <= ref.rounded(32768):
                samples += [center - 1, center, center + 1,
                            (center - 1) ^ ref.FP32.sign, center ^ ref.FP32.sign]
        for seed in SEEDS:
            rng = random.Random(seed)
            samples += [ref.rounded(Fraction(rng.randrange(-32768000, 32768001), 1000))
                        for _ in range(80)]
        samples += [ref.rounded(32769), 0x7F800000, 0x7F800001]
        for a in samples:
            s, c, error = ref.sincos32(a)
            if not error:
                x = float(ref.value(a))
                if max(abs(ref.as_float(s) - math.sin(x)),
                       abs(ref.as_float(c) - math.cos(x))) > 2 ** -18:
                    raise AssertionError(f"trig mathematical bound input={a:08x}")
            yield (0, a, 0, s, c, error)
    else:
        raise ValueError(kind)


def scalars(directory, kind, simulator="verilator", rtl_dir=None):
    vectors = directory / f"{kind}.txt"
    count = emit_rows(vectors, scalar_vectors(kind))
    common = r"""
  reg enable=1, iv=0, ready=0, op=0;
  reg [31:0] a=0,b=0,expected=0,expected_cos=0;
  reg expected_error=0;
  reg file_op;
  reg [31:0] file_a,file_b;
  wire ir, ov, error;
  wire [31:0] data, cosine;
  integer age, enabled_age, stall;
  INSTANCE
  task reset_check;
    begin
      if ({ir,ov,data,cosine,error} !== 67'b0) $fatal(1,"RESET_OUTPUT_XZ");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    INITIAL_CHECK
    repeat(3) tick();
    @(negedge clk); rst_n=1;
    repeat(4) tick();
    fd=$fopen("VECTORS","r");
    if (!fd) $fatal(1,"FIXTURE_OPEN");
    while (!$feof(fd)) begin
      @(negedge clk);
      rc=$fscanf(fd,"%h %h %h %h %h %h\n",file_op,file_a,file_b,expected,expected_cos,expected_error);
      if (rc!=6) $fatal(1,"FIXTURE_PARSE");
      op=file_op; a=file_a; b=file_b;
      enable=1; iv=1; ready=0;
      if (ir!==1) $fatal(1,"REQUEST_READY row=%0d",row);
      tick();
      @(negedge clk); iv=0;
      age=0; enabled_age=0;
      while (ov!==1) begin
        enable=((age%7)!=3);
        if (enable) enabled_age=enabled_age+1;
        tick(); age=age+1;
        if (enabled_age>LIMIT) $fatal(1,"LATENCY row=%0d enabled=%0d",row,enabled_age);
        if (ov!==0 && ov!==1) $fatal(1,"VALID_XZ");
        @(negedge clk);
      end
      if ({data,cosine,error} !== {expected,expected_cos,expected_error})
        $fatal(1,"NUMERIC row=%0d a=%h b=%h op=%b got=%h/%h/%b expected=%h/%h/%b",
               row,a,b,op,data,cosine,error,expected,expected_cos,expected_error);
      for (stall=0;stall<3;stall=stall+1) begin
        enable=stall[0]; tick();
        if ({ov,data,cosine,error} !== {1'b1,expected,expected_cos,expected_error})
          $fatal(1,"RESPONSE_STABILITY row=%0d",row);
        @(negedge clk);
      end
      ready=1; enable=0;
      @(posedge clk);
      if (ov!==1) $fatal(1,"PREEDGE_RESPONSE");
      #1; cycles=cycles+1;
      if (ov!==0) $fatal(1,"CONSUME_WITH_ENABLE_LOW");
      @(negedge clk); ready=0; enable=1;
      tick();
      row=row+1; checked=checked+1;
    end
    if (row!=COUNT) $fatal(1,"COVERAGE");
    $display("CHECK compared=%0d requests=%0d",checked,row);
    $finish;
  end
"""
    instances = {
        "divsqrt": ("anvil_q1_ht2_fp32_divsqrt dut(clk,rst_n,enable,iv,ir,op,a,b,ov,ready,data);\n"
                    "assign cosine=0; assign error=0;"),
        "exp": ("anvil_q1_ht2_fp32_exp dut(clk,rst_n,enable,iv,ir,a,ov,ready,data);\n"
                "assign cosine=0; assign error=0;"),
        "sincos": ("anvil_q1_ht2_fp32_sincos dut(clk,rst_n,enable,iv,ir,a,ov,ready,data,cosine,error);"),
    }
    common = common.replace("INSTANCE", instances[kind]).replace("VECTORS", relative(vectors))
    common = common.replace("COUNT", str(count)).replace("LIMIT", "512" if kind == "divsqrt" else "2048")
    common = common.replace("INITIAL_CHECK", "#1; reset_check();" if simulator == "verilator"
                            else "#0; reset_check();")
    modules = ["fp32_" + kind, "fp32_mul", "fp32_add"]
    return simulate(directory, kind + "-" + simulator, common, modules, simulator, rtl_dir)


def legal_trees(count):
    return itertools.product(*(tuple([4, *range(i)]) for i in range(count)))


def packed(values, width):
    return sum(int(x) << (width * i) for i, x in enumerate(values))


def tree_walk(parents, drafts, targets, prefix):
    if not 1 <= len(parents) <= 4 or any(p != 4 and p >= i for i, p in enumerate(parents)):
        return 0, 0, 0, True
    tokens, selected = [], []
    parent, target = 4, prefix
    while len(tokens) < 4:
        tokens.append(target)
        matches = [i for i, p in enumerate(parents) if p == parent and drafts[i] == target]
        if not matches:
            break
        node = min(matches)
        selected.append(node)
        target, parent = targets[node], node
    return len(tokens), packed(tokens, 32), sum(1 << i for i in selected), False


def tree_rows():
    for n in range(1, 5):
        for parents in legal_trees(n):
            # Exhaust all binary-token assignments, including duplicate children.
            for drafts in itertools.product((7, 11), repeat=n):
                for targets in itertools.product((7, 11), repeat=n):
                    for prefix in (7, 11, 99):
                        yield (n, packed(drafts, 32), packed(targets, 32), packed(parents, 3),
                               prefix, *tree_walk(parents, drafts, targets, prefix))
    for n, parents in ((0, ()), (5, (4, 4, 4, 4)), (1, (0,)), (1, (5,)),
                       (2, (4, 1)), (2, (1, 0)), (4, (4, 0, 3, 2))):
        yield (n, 0, 0, packed(parents, 3), 9, 0, 0, 0, True)


def verifier(directory, simulator="verilator", rtl_dir=None):
    vectors = directory / "verifier.txt"
    count = emit_rows(vectors, tree_rows())
    body = r"""
  reg iv=0,ready=0;
  reg [2:0] count=0,ec;
  reg [127:0] drafts=0,targets=0,et;
  reg [11:0] parents=0;
  reg [31:0] prefix=0;
  reg [3:0] em;
  reg ee;
  wire ir,ov,error;
  wire [2:0] oc;
  wire [127:0] ot;
  wire [3:0] om;
  integer stall;
  anvil_q1_ht2_spec_verifier dut(clk,rst_n,iv,ir,count,drafts,targets,parents,prefix,
                               ov,ready,oc,ot,om,error);
  task reset_check;
    begin if ({ir,ov,oc,ot,om,error} !== 138'b0) $fatal(1,"RESET_OUTPUT_XZ"); end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    INITIAL_CHECK
    repeat(3) tick(); @(negedge clk); rst_n=1;
    repeat(4) tick();
    fd=$fopen("VECTORS","r");
    if (!fd) $fatal(1,"FIXTURE_OPEN");
    while (!$feof(fd)) begin
      @(negedge clk);
      rc=$fscanf(fd,"%h %h %h %h %h %h %h %h %h\n",
                 count,drafts,targets,parents,prefix,ec,et,em,ee);
      if (rc!=9) $fatal(1,"FIXTURE_PARSE");
      if (ir!==1) $fatal(1,"REQUEST_READY");
      iv=1; tick();
      if (ov!==0) $fatal(1,"LATENCY_E row=%0d",row);
      @(negedge clk); iv=0; tick();
      if ({ov,oc,ot,om,error} !== {1'b1,ec,et,em,ee})
        $fatal(1,"TREE_WALK row=%0d count=%0d parents=%h got=%b:%d:%h:%h:%b expected=%d:%h:%h:%b",
               row,count,parents,ov,oc,ot,om,error,ec,et,em,ee);
      for (stall=0;stall<(row%3);stall=stall+1) begin
        tick();
        if ({ov,oc,ot,om,error} !== {1'b1,ec,et,em,ee}) $fatal(1,"STALL_STABILITY");
      end
      @(negedge clk); ready=1;
      @(posedge clk);
      if ({ov,oc,ot,om,error} !== {1'b1,ec,et,em,ee}) $fatal(1,"PREEDGE_RESULT");
      #1; cycles=cycles+1;
      if (ov!==0) $fatal(1,"DUPLICATE_RESULT");
      @(negedge clk); ready=0;
      row=row+1; checked=checked+1;
    end
    if (row!=COUNT) $fatal(1,"COVERAGE");
    $display("CHECK compared=%0d exhaustive_tree_assignments=%0d",checked,row-7);
    $finish;
  end
"""
    body = body.replace("VECTORS", relative(vectors)).replace("COUNT", str(count))
    body = body.replace("INITIAL_CHECK", "#1; reset_check();" if simulator == "verilator"
                        else "#0; reset_check();")
    return simulate(directory, "verifier-" + simulator, body, ["spec_verifier"], simulator, rtl_dir)


def sparse_expected(address, burst, activations, slots, threshold):
    error = (
        not slots or not burst or address & 63 or address + burst * 64 > 1 << 33
        or ref.kind(threshold, ref.BF16) in ("nan", "inf")
        or threshold & 0x8000 and threshold & 0x7FFF
    )
    selected = [a for i, a in enumerate(activations) if slots >> i & 1]
    error = bool(error or any(ref.kind(a, ref.BF16) in ("nan", "inf") for a in selected))
    skip = not error and all(abs(ref.value(a, ref.BF16)) <= abs(ref.value(threshold, ref.BF16))
                                 for a in selected)
    return skip, error


def sparse_rows():
    thresholds = (0, 0x8000, 1, 0x007F, 0x0080, 0x3C00, 0x3F80, 0x7F7F)
    for threshold in thresholds:
        magnitude = threshold & 0x7FFF
        for slots in range(1, 16):
            for high_slot in range(4):
                for delta in (-1, 0, 1):
                    activations = [magnitude] * 4
                    activations[high_slot] = max(0, magnitude + delta) | (0x8000 if high_slot & 1 else 0)
                    skip, error = sparse_expected(64, 3, activations, slots, threshold)
                    yield (64, 3, packed(activations, 16), slots, threshold, skip, error)
    invalids = [
        (0, 1, [0] * 4, 0, 0), (0, 0, [0] * 4, 15, 0),
        (1, 1, [0] * 4, 15, 0), ((1 << 33) - 64, 1, [0x3F80] * 4, 15, 0),
        ((1 << 33) - 64, 2, [0x3F80] * 4, 15, 0),
        (0, 1, [0x7F80, 0, 0, 0], 1, 0),
        (0, 1, [0x7FC0, 0, 0, 0], 1, 0),
        (0, 1, [0] * 4, 15, 0x8001), (0, 1, [0] * 4, 15, 0x7F80),
        (0, 1, [0] * 4, 15, 0x7F81),
    ]
    for address, burst, activations, slots, threshold in invalids:
        yield (address, burst, packed(activations, 16), slots, threshold,
               *sparse_expected(address, burst, activations, slots, threshold))


def sparse(directory, simulator="iverilog", rtl_dir=None):
    vectors = directory / "sparse.txt"
    count = emit_rows(vectors, sparse_rows())
    body = r"""
  reg iv=0,dr=0,ready=0;
  reg [32:0] address=0;
  reg [7:0] burst=0;
  reg [63:0] activations=0;
  reg [3:0] slots=0;
  reg [15:0] threshold=0;
  reg es,ee;
  wire ir,dv,ov,skipped,error;
  wire [32:0] da;
  wire [7:0] db;
  integer stall,requests=0,skips=0,errors=0;
  anvil_q1_ht2_sparse_dma dut(clk,rst_n,iv,ir,address,burst,activations,slots,threshold,
                            dv,dr,da,db,ov,ready,skipped,error);
  task reset_check;
    begin if ({ir,dv,da,db,ov,skipped,error} !== 46'b0) $fatal(1,"RESET_OUTPUT_XZ"); end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    INITIAL_CHECK
    repeat(3) tick(); @(negedge clk); rst_n=1; repeat(4) tick();
    fd=$fopen("VECTORS","r");
    if (!fd) $fatal(1,"FIXTURE_OPEN");
    while (!$feof(fd)) begin
      @(negedge clk);
      rc=$fscanf(fd,"%h %h %h %h %h %h %h\n",address,burst,activations,slots,threshold,es,ee);
      if (rc!=7) $fatal(1,"FIXTURE_PARSE");
      if (ir!==1) $fatal(1,"REQUEST_READY");
      iv=1; tick();
      if ({dv,ov}!==2'b0) $fatal(1,"LATENCY_E");
      @(negedge clk); iv=0; tick();
      if (es || ee) begin
        if (dv!==0 || {ov,skipped,error}!=={1'b1,es,ee})
          $fatal(1,"SPARSE_DECISION row=%0d got=%b/%b/%b expected=%b/%b",
                 row,ov,skipped,error,es,ee);
        skips=skips+es; errors=errors+ee;
      end else begin
        if (ov!==0 || {dv,da,db}!=={1'b1,address,burst}) $fatal(1,"DMA_REQUEST row=%0d",row);
        for (stall=0;stall<3;stall=stall+1) begin
          tick();
          if (ov!==0 || {dv,da,db}!=={1'b1,address,burst}) $fatal(1,"DMA_STABILITY");
        end
        @(negedge clk); dr=1;
        @(posedge clk);
        if ({dv,da,db}!=={1'b1,address,burst}) $fatal(1,"DMA_PREEDGE");
        requests=requests+1;
        #1; cycles=cycles+1;
        if (dv!==0 || {ov,skipped,error}!==3'b100) $fatal(1,"DMA_COMPLETION");
        @(negedge clk); dr=0;
      end
      for (stall=0;stall<2;stall=stall+1) begin
        tick();
        if (dv!==0 || {ov,skipped,error}!=={1'b1,es,ee}) $fatal(1,"DECISION_STABILITY");
      end
      @(negedge clk); ready=1;
      @(posedge clk);
      if (ov!==1) $fatal(1,"PREEDGE_RESULT");
      #1; cycles=cycles+1;
      if (ov!==0) $fatal(1,"DUPLICATE_DECISION");
      @(negedge clk); ready=0;
      row=row+1; checked=checked+1;
    end
    if (row!=COUNT || requests==0 || skips==0 || errors==0) $fatal(1,"COVERAGE");
    $display("CHECK compared=%0d dma_transactions=%0d skipped=%0d errors=%0d",
             checked,requests,skips,errors);
    $finish;
  end
"""
    body = body.replace("VECTORS", relative(vectors)).replace("COUNT", str(count))
    body = body.replace("INITIAL_CHECK", "#1; reset_check();" if simulator == "verilator"
                        else "#0; reset_check();")
    return simulate(directory, "sparse-" + simulator, body, ["sparse_dma"], simulator, rtl_dir)


def awq_rows():
    scales = (0, 0x8000, 1, 0x03FF, 0x0400, 0x3800, 0x3C00, 0x7BFF,
              0x8001, 0xBC00, 0x7C00, 0xFC00, 0x7C01, 0x7FFF)
    for lane, q, z, scale in itertools.product(range(8), range(16), range(16), scales):
        shift = 4 * (0, 4, 1, 5, 2, 6, 3, 7)[lane]
        # Nonselected nibbles differ, exposing an incorrect AWQ permutation.
        qword = (0x12345678 & ~(15 << shift)) | q << shift
        zword = (0xFEDCBA98 & ~(15 << shift)) | z << shift
        yield (qword, zword, lane, scale, *ref.awq(qword, zword, lane, scale))


def dequant(directory, simulator="verilator", rtl_dir=None):
    vectors = directory / "awq.txt"
    count = emit_rows(vectors, awq_rows())
    body = r"""
  reg iv=0,ready=0;
  reg [31:0] q=0,z=0;
  reg [2:0] lane=0;
  reg [15:0] scale=0,expected=0;
  reg [31:0] fq,fz;
  reg [2:0] fl;
  reg [15:0] fs;
  reg ee=0;
  wire ir,ov,error;
  wire [15:0] data;
  integer age,stall;
  anvil_q1_ht2_dequant dut(clk,rst_n,iv,ir,q,z,lane,scale,ov,ready,data,error);
  task reset_check;
    begin if ({ir,ov,data,error} !== 19'b0) $fatal(1,"RESET_OUTPUT_XZ"); end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    INITIAL_CHECK
    repeat(3) tick(); @(negedge clk); rst_n=1; repeat(4) tick();
    fd=$fopen("VECTORS","r");
    if (!fd) $fatal(1,"FIXTURE_OPEN");
    while (!$feof(fd)) begin
      @(negedge clk);
      rc=$fscanf(fd,"%h %h %h %h %h %h\n",fq,fz,fl,fs,expected,ee);
      if (rc!=6) $fatal(1,"FIXTURE_PARSE");
      q=fq; z=fz; lane=fl; scale=fs;
      #1;
      if (ir!==1) $fatal(1,"REQUEST_READY");
      iv=1; tick();
      @(negedge clk); iv=0; age=0;
      while (ov!==1) begin
        tick(); age=age+1; @(negedge clk);
        if (age>8) $fatal(1,"LATENCY");
      end
      if ({data,error}!=={expected,ee})
        $fatal(1,"AWQ row=%0d lane=%0d q=%h z=%h scale=%h got=%h/%b expected=%h/%b",
               row,lane,q,z,scale,data,error,expected,ee);
      for (stall=0;stall<row%3;stall=stall+1) begin
        tick();
        if ({ov,data,error}!=={1'b1,expected,ee}) $fatal(1,"STALL_STABILITY");
        @(negedge clk);
      end
      ready=1; @(posedge clk);
      if ({ov,data,error}!=={1'b1,expected,ee}) $fatal(1,"PREEDGE_RESULT");
      #1; cycles=cycles+1;
      @(negedge clk); ready=0; row=row+1; checked=checked+1;
    end
    if (row!=COUNT) $fatal(1,"COVERAGE");
    $display("CHECK compared=%0d lanes=8 q_values=16 zero_values=16 scale_classes=14",checked);
    $finish;
  end
"""
    body = body.replace("VECTORS", relative(vectors)).replace("COUNT", str(count))
    body = body.replace("INITIAL_CHECK", "#1; reset_check();" if simulator == "verilator"
                        else "#0; reset_check();")
    return simulate(directory, "awq-" + simulator, body, ["dequant", "fp32_mul"], simulator, rtl_dir)


def matrix_result(beats, fmt, slots, mask):
    contexts = [[[0] * 4 for _ in range(64)] for _ in range(4)]
    for column, (activations, weights) in enumerate(beats):
        for slot in range(4):
            for lane in range(64):
                if slots >> slot & 1 and mask >> lane & 1:
                    c = contexts[slot][lane]
                    c[column % 4] = ref.add(
                        c[column % 4], ref.multiply(activations[slot], weights[lane], fmt))
    result, error = [], False
    for slot in range(4):
        for lane in range(64):
            c = contexts[slot][lane]
            v = ref.add(ref.add(ref.add(c[0], c[1]), c[2]), c[3])
            result.append(v)
            error |= ref.kind(v) in ("nan", "inf")
    return packed(result, 32), error


def mac_rows():
    def row(command=0, iv=0, first=0, last=0, fp16=0, slots=15, mask=(1 << 64)-1,
            activations=0, weights=0, ready=0, valid=0, data=0, error=0):
        return (command, iv, first, last, fp16, slots, mask, activations, weights,
                ready, valid, data, mask if valid else 0, slots if valid else 0, error)

    def reset():
        yield row(command=3)
        yield row(command=3)
        for _ in range(4):
            yield row()

    def transaction(beats, fp16, slots, mask, bubbles=False):
        fmt = ref.FP16 if fp16 else ref.BF16
        data, error = matrix_result(beats, fmt, slots, mask)
        for i, (activations, weights) in enumerate(beats):
            if bubbles and i & 1:
                for _ in range(i % 3 + 1):
                    yield row(fp16=fp16, slots=slots, mask=mask)
            yield row(iv=1, first=i == 0, last=i == len(beats)-1, fp16=fp16,
                      slots=slots, mask=mask, activations=packed(activations, 16),
                      weights=packed(weights, 16))
        for _ in range(18):
            yield row(fp16=fp16, slots=slots, mask=mask)
        for _ in range(4):
            yield row(valid=1, data=data, error=error, fp16=fp16, slots=slots, mask=mask)
        yield row(command=2, ready=1, valid=1, data=data, error=error,
                  fp16=fp16, slots=slots, mask=mask)
        yield row()

    yield from reset()
    for fp16 in (0, 1):
        fmt = ref.FP16 if fp16 else ref.BF16
        for case, (n, slots, mask, bubbles) in enumerate((
            (1, 15, (1 << 64)-1, False), (17, 15, (1 << 64)-1, False),
            (21, 15, (1 << 64)-1, True), (7, 5, (1 << 41)-1, True),
            (5, 10, 0xAAAAAAAAAAAAAAAA, False),
        )):
            rng = random.Random(SEEDS[case % 3])
            beats = []
            for i in range(n):
                activations = [ref.rounded(Fraction(rng.randrange(-1024, 1025), 256), fmt)
                               for _ in range(4)]
                weights = [ref.rounded(Fraction(rng.randrange(-1024, 1025), 512), fmt)
                           for _ in range(64)]
                beats.append((activations, weights))
            yield from transaction(beats, fp16, slots, mask, bubbles)
    # Cancellation and underflow retain their native-format IEEE behavior.
    for fp16 in (0, 1):
        fmt = ref.FP16 if fp16 else ref.BF16
        one = ref.rounded(1, fmt)
        beats = [([one, one | fmt.sign, 1, 0x8000], [one] * 64),
                 ([one | fmt.sign, one, 1, 0], [one] * 64)]
        yield from transaction(beats, fp16, 15, (1 << 64)-1)
    # Reset each product/add/reduction/output phase, then verify no stale output.
    for phase in range(21):
        yield row(iv=1, first=1, last=1, activations=packed([0x3F80] * 4, 16),
                  weights=packed([0x3F80] * 64, 16))
        for age in range(phase):
            yield row(valid=age >= 18, data=packed([0x3F800000] * 256, 32) if age >= 18 else 0)
        yield from reset()
        for _ in range(22):
            yield row()
    # Missing first and repeated first are errors, never silently restarted dots.
    for repeated in (False, True):
        if repeated:
            yield row(iv=1, first=1)
        yield row(iv=1, first=repeated, last=1)
        for _ in range(8):
            yield row()
        yield row(valid=1, error=1)
        yield row(command=2, ready=1, valid=1, error=1)
        yield row()


def mac(directory, simulator="verilator", rtl_dir=None):
    vectors = directory / "mac.txt"
    count = emit_rows(vectors, mac_rows())
    body = r"""
  reg iv=0,first=0,last=0,fp16=0,ready=0;
  reg [3:0] slots=0,es;
  reg [63:0] mask=0,activation=0,em;
  reg [1023:0] weights=0;
  reg [8191:0] ed;
  reg ev,ee;
  reg [2:0] command;
  reg fi,ff,fl,fp,fr;
  reg [3:0] fs;
  reg [63:0] fm,fac;
  reg [1023:0] fw;
  wire ir,ov,error;
  wire [8191:0] data;
  wire [63:0] om;
  wire [3:0] os;
  integer lane,accepted=0,results=0;
  anvil_q1_ht2_tile_batch_mac dut(clk,rst_n,iv,first,last,fp16,ir,slots,mask,
                                activation,weights,ov,ready,data,om,os,error);
  task reset_check;
    begin if ({ir,ov,data,om,os,error} !== 8263'b0) $fatal(1,"RESET_OUTPUT_XZ"); end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    INITIAL_CHECK
    fd=$fopen("VECTORS","r");
    if (!fd) $fatal(1,"FIXTURE_OPEN");
    while (!$feof(fd)) begin
      @(negedge clk); #1;
      rc=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
        command,fi,ff,fl,fp,fs,fm,fac,fw,fr,ev,ed,em,es,ee);
      if (rc!=15) $fatal(1,"FIXTURE_PARSE");
      iv=fi; first=ff; last=fl; fp16=fp; slots=fs;
      mask=fm; activation=fac; weights=fw; ready=fr;
      rst_n=(command!=3);
      #1;
      @(posedge clk);
      if (iv && ir!==1) $fatal(1,"INITIATION_INTERVAL row=%0d",row);
      if (iv) accepted=accepted+1;
      if (command==2) begin
        if ({ov,data,om,os,error} !== {ev,ed,em,es,ee}) $fatal(1,"PREEDGE_RESULT row=%0d",row);
        results=results+1;
      end
      #1; cycles=cycles+1;
      if (command==2) begin
        if (ov!==0) $fatal(1,"DUPLICATE_RESULT");
      end else begin
        if ({ov,om,os,error} !== {ev,em,es,ee})
          $fatal(1,"MAC_PROTOCOL row=%0d got=%b:%h:%h:%b expected=%b:%h:%h:%b",
                 row,ov,om,os,error,ev,em,es,ee);
        for (lane=0;lane<256;lane=lane+1)
          if (data[32*lane+:32] !== ed[32*lane+:32])
            $fatal(1,"MAC_NUMERIC row=%0d slot=%0d lane=%0d got=%h expected=%h",
                   row,lane/64,lane%64,data[32*lane+:32],ed[32*lane+:32]);
      end
      checked=checked+256; row=row+1;
    end
    if (row!=COUNT || results<14 || accepted<100) $fatal(1,"COVERAGE");
    $display("CHECK compared=%0d accepted_beats=%0d completed_dots=%0d live_paths=256",
             checked,accepted,results);
    $finish;
  end
"""
    body = body.replace("VECTORS", relative(vectors)).replace("COUNT", str(count))
    body = body.replace("INITIAL_CHECK", "#1; reset_check();" if simulator == "verilator"
                        else "#0; reset_check();")
    return simulate(directory, "mac-" + simulator, body,
                    ["tile_batch_mac", "mac_lane", "fp16_mul", "fp32_add"], simulator, rtl_dir)


def visibility(parents, prefix_position, prefix_valid, sequence_length=17):
    if not prefix_valid or not 1 <= len(parents) <= 4 or prefix_position >= sequence_length:
        return 0, 0, True
    positions, masks = [], []
    for node in range(len(parents)):
        ancestors = {node}
        parent = parents[node]
        while parent != 4:
            if parent >= node or parent in ancestors:
                return 0, 0, True
            ancestors.add(parent)
            parent = parents[parent]
        position = prefix_position + len(ancestors)
        if position >= sequence_length:
            return 0, 0, True
        positions.append(position)
        masks.append(sum(1 << i for i in ancestors))
    return packed(positions, 32), packed(masks, 4), False


def mask_rows():
    for count in range(1, 5):
        for parents in legal_trees(count):
            for position in (0, 12, 13, 14, 15, 16, 17, 0xFFFFFFFF):
                for prefix_valid in (0, 1):
                    yield (count, packed(parents, 3), position, prefix_valid,
                           *visibility(parents, position, prefix_valid))
    for count, parents in ((0, ()), (5, (4, 4, 4, 4)), (1, (0,)),
                           (2, (4, 1)), (4, (4, 0, 3, 2))):
        yield (count, packed(parents, 3), 0, 1, 0, 0, True)


def masks(directory, simulator="verilator", rtl_dir=None):
    vectors = directory / "masks.txt"
    count = emit_rows(vectors, mask_rows())
    body = r"""
  reg iv=0,ready=0,pv=0;
  reg [2:0] count=0,fc;
  reg [11:0] parents=0,fp;
  reg [31:0] position=0,fx;
  reg fv;
  reg [127:0] ep;
  reg [15:0] em;
  reg ee;
  wire ir,ov,error;
  wire [127:0] positions;
  wire [15:0] ancestors;
  integer stall;
  anvil_q1_ht2_tree_mask #(.MAX_SEQ_LEN(17)) dut(
    clk,rst_n,iv,ir,pv,position,count,parents,ov,ready,positions,ancestors,error);
  task reset_check;
    begin if ({ir,ov,positions,ancestors,error} !== 147'b0) $fatal(1,"RESET_OUTPUT_XZ"); end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    INITIAL_CHECK
    repeat(3) tick(); @(negedge clk); rst_n=1; repeat(4) tick();
    fd=$fopen("VECTORS","r");
    if (!fd) $fatal(1,"FIXTURE_OPEN");
    while (!$feof(fd)) begin
      @(negedge clk);
      rc=$fscanf(fd,"%h %h %h %h %h %h %h\n",fc,fp,fx,fv,ep,em,ee);
      if (rc!=7) $fatal(1,"FIXTURE_PARSE");
      count=fc; parents=fp; position=fx; pv=fv;
      iv=1;
      if (ir!==1) $fatal(1,"REQUEST_READY");
      tick();
      if (ov!==0) $fatal(1,"LATENCY_E");
      @(negedge clk); iv=0; tick();
      if ({ov,positions,ancestors,error} !== {1'b1,ep,em,ee})
        $fatal(1,"CAUSAL_MASK row=%0d parents=%h position=%h got=%b:%h:%h:%b expected=%h:%h:%b",
               row,parents,position,ov,positions,ancestors,error,ep,em,ee);
      for (stall=0;stall<row%3;stall=stall+1) begin
        tick();
        if ({ov,positions,ancestors,error} !== {1'b1,ep,em,ee}) $fatal(1,"STALL_STABILITY");
      end
      @(negedge clk); ready=1;
      @(posedge clk);
      if ({ov,positions,ancestors,error} !== {1'b1,ep,em,ee}) $fatal(1,"PREEDGE_RESULT");
      #1; cycles=cycles+1;
      if (ov!==0) $fatal(1,"DUPLICATE_RESULT");
      @(negedge clk); ready=0;
      checked=checked+1; row=row+1;
    end
    if (row!=COUNT) $fatal(1,"COVERAGE");
    $display("CHECK compared=%0d trees_and_sequence_boundaries=%0d",checked,row);
    $finish;
  end
"""
    body = body.replace("VECTORS", relative(vectors)).replace("COUNT", str(count))
    body = body.replace("INITIAL_CHECK", "#1; reset_check();" if simulator == "verilator"
                        else "#0; reset_check();")
    return simulate(directory, "masks-" + simulator, body, ["tree_mask"], simulator, rtl_dir)
