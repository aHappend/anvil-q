#!/usr/bin/env python3
"""Independent public-pin checks. Generated artifacts are never design inputs.

The check ledger deliberately distinguishes implemented checks from remaining
acceptance obligations; an incomplete matrix must never return success.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RTL = sorted(ROOT.glob("rtl/*.sv"))
KEYS = ("NUM_LAYERS", "HIDDEN_SIZE", "INTERMEDIATE_SIZE", "NUM_Q_HEADS",
        "NUM_KV_HEADS", "HEAD_DIM", "GROUP_SIZE", "VOCAB_SIZE", "MAX_SEQ_LEN")
MATRIX = {"A": (2, 16, 32, 4, 2, 4, 8, 17, 4),
          "B": (2, 112, 128, 14, 2, 8, 16, 19, 3),
          "C": (1, 24, 48, 6, 2, 4, 3, 11, 3),
          "D": (1, 8, 8, 2, 2, 4, 8, 1, 1)}
SHIFTS = (0, 16, 4, 20, 8, 24, 12, 28)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for pattern in ("rtl/*.sv", "tests/*.py", "design/*.md",
                            "hf_qwen25_05b_awq_spec/*.json")
            for p in sorted(ROOT.glob(pattern))}


class Run:
    def __init__(self, out, repair_of=None):
        self.out = Path(out).resolve()
        self.out.mkdir(parents=True, exist_ok=False)
        self.source_hashes = hashes()
        self.commands = []
        self.results = []
        self.started = utc()
        self.repair_of = repair_of

    def command(self, argv, name, timeout=20):
        argv = [str(x) for x in argv]
        start = utc()
        tick = time.monotonic()
        timed_out = False
        try:
            p = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout)
            code, stdout, stderr = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr = None, exc.stdout or b"", exc.stderr or b""
            timed_out = True
        stdout_path = self.out / (name + ".stdout")
        stderr_path = self.out / (name + ".stderr")
        stdout_path.write_bytes(stdout)
        stderr_path.write_bytes(stderr)
        record = dict(argv=argv, cwd=str(ROOT), start_time=start, end_time=utc(),
                      elapsed_s=time.monotonic()-tick, timeout_s=timeout,
                      timed_out=timed_out, exit_code=code,
                      stdout_path=str(stdout_path.relative_to(ROOT)),
                      stderr_path=str(stderr_path.relative_to(ROOT)))
        self.commands.append(record)
        self.save()
        return code, stdout.decode(errors="replace"), stderr.decode(errors="replace")

    def save(self):
        # This is a new output namespace, never a historical execution record.
        (self.out / "receipt.json").write_text(json.dumps(dict(
            start_time=self.started, updated_time=utc(), argv=sys.argv,
            cwd=str(ROOT), source_sha256=self.source_hashes, repair_of=self.repair_of,
            commands=self.commands, results=self.results), indent=2) + "\n")

    def result(self, name, **values):
        self.results.append(dict(name=name, **values))
        self.save()


def require(condition, text):
    if not condition:
        raise AssertionError(text)


def half_fraction(raw):
    """Exact integer numerator / power-of-two denominator, not RTL conversion."""
    sign = -1 if raw & 0x8000 else 1
    exponent, mantissa = (raw >> 10) & 31, raw & 1023
    if exponent == 31:
        raise ValueError("nonfinite binary16")
    significand = mantissa if exponent == 0 else mantissa + 1024
    power = -24 if exponent == 0 else exponent - 25
    return sign * significand * (1 << max(power, 0)), 1 << max(-power, 0)


def rounded(n, d):
    return (-1 if n < 0 else 1) * ((2*abs(n)+d)//(2*d))


def sat(x, bits=16):
    return min((1 << (bits-1))-1, max(-(1 << (bits-1)), x))


def half_fixed(raw, bits=8):
    n, d = half_fraction(raw)
    return rounded(n*(1 << bits), d)


def dequant(qw, qz, h, lane):
    try:
        n, _ = half_fraction(h)
    except ValueError:
        return 0, 1
    if n < 0:
        return 0, 1
    shift = SHIFTS[lane]
    return (((qw >> shift) & 15)-((qz >> shift) & 15))*half_fixed(h, 16), 0


def pack(values):
    return sum((v & 15) << s for v, s in zip(values, SHIFTS))


def manifest(run):
    base = ROOT / "hf_qwen25_05b_awq_spec"
    config = json.loads((base / "config.json").read_text())
    m = json.loads((base / "qwen25_05b_awq_tensors.json").read_text())
    tensors = m["tensors"]
    expected = {"model.embed_tokens.weight": ("F16", [151936, 896]),
                "lm_head.weight": ("F16", [151936, 896]),
                "model.norm.weight": ("F16", [896])}
    dimensions = {"self_attn.q_proj": (896, 896),
                  "self_attn.k_proj": (896, 128),
                  "self_attn.v_proj": (896, 128),
                  "self_attn.o_proj": (896, 896),
                  "mlp.gate_proj": (896, 4864),
                  "mlp.up_proj": (896, 4864),
                  "mlp.down_proj": (4864, 896)}
    for layer in range(24):
        prefix = f"model.layers.{layer}."
        for norm in ("input_layernorm", "post_attention_layernorm"):
            expected[prefix+norm+".weight"] = ("F16", [896])
        for projection, (ni, no) in dimensions.items():
            for suffix, dtype, shape in (
                    ("qweight", "I32", [ni, no//8]),
                    ("qzeros", "I32", [ni//128, no//8]),
                    ("scales", "F16", [ni//128, no])):
                expected[prefix+projection+"."+suffix] = dtype, shape
            if projection in ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj"):
                expected[prefix+projection+".bias"] = "F16", [no]
    require(config["tie_word_embeddings"] is True, "embedding tie configuration")
    require(set(tensors) == set(expected) and len(tensors) == 627, "manifest inventory")
    intervals = []
    for name, (dtype, shape) in expected.items():
        t = tensors[name]
        require((t["dtype"], t["shape"]) == (dtype, shape), "manifest "+name)
        lo, hi = t["data_offsets"]
        require(hi-lo == math.prod(shape)*(2 if dtype == "F16" else 4),
                "manifest byte extent "+name)
        intervals.append((lo, hi))
    intervals.sort()
    require(all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:])),
            "overlapping manifest extents")
    slices = json.loads((base / "official_layer0_awq_slice.json").read_text())
    checked = 0

    def flatten(v):
        if isinstance(v, list):
            return [x for item in v for x in flatten(item)]
        return [v]

    for name, t in slices["tensors"].items():
        require(t["full_shape"] == tensors[name]["shape"], "slice shape "+name)
        values, raw = flatten(t["values"]), flatten(t["raw_hex"])
        require(len(values) == len(raw) == math.prod(t["slice_shape"]), "slice extent")
        for v, h in zip(values, raw):
            bits = int(h, 16)
            if t["dtype"] == "I32":
                require(v & 0xffffffff == bits, "signed I32 raw mismatch")
            else:
                actual = struct.unpack("<e", struct.pack("<H", bits))[0]
                require(abs(v-actual) < 1e-7, "F16 raw mismatch")
            checked += 1
    run.result("authoritative_inputs", tensors=627, quantized_modules=168,
               raw_slice_values=checked, outcome="pass")
    return slices


def compile_sim(run, text, name, sources=None, timeout=20):
    sv = run.out / (name+".sv")
    executable = run.out / (name+".vvp")
    sv.write_text(text)
    code, _, err = run.command(
        ["iverilog", "-g2012", "-Wall", "-s", "tb", "-o", executable,
         *(sources or RTL), sv], name+"-compile", timeout)
    require(code == 0 and not err.strip(), f"{name}: compile/warning failure: {err}")
    code, stdout, stderr = run.command(["vvp", executable], name+"-simulate", timeout)
    require(code == 0 and "PASS" in stdout, f"{name}: behavioral failure: {stdout} {stderr}")
    return stdout


def dequant_cases(slices):
    cases = []
    rng = random.Random(17)
    scales = (0, 0x8000, 1, 127, 128, 129, 255, 256, 0x3c00, 0x6c00,
              0x77ff, 0x7800, 0x7bff, 0xbc00, 0x8001, 0x7c00, 0xfc00, 0x7e00)
    for scale in scales:
        for lane in range(8):
            for w, z in ((15, 0), (0, 15), (8, 0), (0, 8), (7, 0), (0, 7), (9, 9)):
                weights = [rng.randrange(16) for _ in range(8)]
                zeros = [rng.randrange(16) for _ in range(8)]
                weights[lane], zeros[lane] = w, z
                qw, qz = pack(weights), pack(zeros)
                cases.append((qw, qz, scale, lane, *dequant(qw, qz, scale, lane)))
    ts = slices["tensors"]
    official = 0
    for projection in ("self_attn.q_proj", "self_attn.k_proj", "mlp.gate_proj"):
        prefix = "model.layers.0."+projection+"."
        weights, zeros, scales = (ts[prefix+s]["raw_hex"] for s in ("qweight", "qzeros", "scales"))
        for row in weights:
            for word, packed in enumerate(row):
                for lane in range(8):
                    channel = word*8+lane
                    if word < len(zeros[0]) and channel < len(scales[0]):
                        qw, qz = int(packed, 16), int(zeros[0][word], 16)
                        h = int(scales[0][channel], 16)
                        cases.append((qw, qz, h, lane, *dequant(qw, qz, h, lane)))
                        official += 1
    return cases, official


def dequant_test(run, slices):
    cases, official = dequant_cases(slices)
    lines = ["module tb; reg [31:0] qw,qz; reg [15:0] scale; reg [2:0] lane;",
             "wire signed [36:0] w; wire invalid;",
             "anvil_q1_awq_dequant dut(qw,qz,scale,lane,w,invalid); initial begin"]
    for i, (qw, qz, h, lane, w, invalid) in enumerate(cases):
        literal = ("-" if w < 0 else "") + "37'sd"+str(abs(w))
        lines.append(f"qw=32'h{qw:08x}; qz=32'h{qz:08x}; scale=16'h{h:04x}; lane=3'd{lane}; #1;"
                     f'if(w !== {literal} || invalid !== 1\'b{invalid}) '
                     f'$fatal(1,"AWQ case {i} expected {w} invalid {invalid}, got %d %b",w,invalid);')
    lines += [f'$display("PASS dequant comparisons={len(cases)} official={official}"); $finish;',
              "end endmodule"]
    text = "\n".join(lines)
    stdout = compile_sim(run, text, "dequant")
    run.result("dequant", comparisons=len(cases), official_comparisons=official,
               outcome="pass", stdout=stdout)
    return text


BUS_PORTS = """
reg clk=0; always #5 clk=~clk;
reg rst_n=0, cmd_valid=0; wire cmd_ready,done,error;
reg [31:0] cmd_layer=0,cmd_pos=0; reg [2:0] cmd_proj=0; reg [1:0] cmd_mode=0;
wire mem_req_valid,mem_req_write,mem_rsp_ready;
reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
wire [3:0] mem_req_kind; wire [2:0] mem_req_proj;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
reg [31:0] mem_rsp_rdata=0;
"""
BUS_CONNECT = """
.clk(clk),.rst_n(rst_n),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
.cmd_layer(cmd_layer),.cmd_pos(cmd_pos),.done(done),.error(error),
.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
.mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
.mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
"""


def command_tb(instance, reader, expected, commands):
    """Reader supplies immutable tensor/scratch data only, never DUT arithmetic.

    Write expectations are independently precomputed; comparisons sample active
    pre-edge handshakes. The transactor adds deterministic bounded stalls.
    """
    return """module tb;
""" + BUS_PORTS + instance + """
integer cycles=0, writes=0, accepted=0, pending=0, delay_count=0;
integer stalls=0, responses=0, completions=0;
reg [136:0] held; reg was_stalled=0;
reg [31:0] reply; reg [31:0] expected_value;
""" + reader + """
task automatic reset_check;
begin
 if(cmd_ready !== 0 || done !== 0 || error !== 0 ||
    mem_req_valid !== 0 || mem_rsp_ready !== 0 ||
    {mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
     mem_req_row,mem_req_col,mem_req_wdata} !== 136'd0)
   $fatal(1,"RESET public output leakage");
end endtask
always @(negedge clk) begin
 if(!rst_n) reset_check();
 else begin
   mem_req_ready = cycles%4 != 0;
   mem_rsp_valid = pending && delay_count==0;
   mem_rsp_rdata = reply;
 end
end
always @(posedge clk) begin
 cycles=cycles+1;
 if(!rst_n) reset_check();
 else begin
 if(cycles>12000000) $fatal(1,"WATCHDOG");
 if(was_stalled && {mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,
      mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata} !== held)
   $fatal(1,"REQUEST payload changed under backpressure");
 was_stalled=mem_req_valid && !mem_req_ready;
 held={mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,
       mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata};
 if(was_stalled) stalls=stalls+1;
 if(mem_req_valid && mem_req_ready) begin
   if(pending || mem_rsp_ready) $fatal(1,"OUTSTANDING or request/response overlap");
   if(mem_req_layer!==0) $fatal(1,"unexpected layer");
   accepted=accepted+1; pending=1; delay_count=2+cycles%3;
   if(mem_req_write) begin
""" + expected + """
     writes=writes+1; reply=0;
   end else begin
     reply=read_memory(mem_req_kind,mem_req_proj,mem_req_row,mem_req_col);
   end
 end else if(pending && delay_count>0) delay_count=delay_count-1;
 if(mem_rsp_valid && mem_rsp_ready) begin
   if(!pending || delay_count!=0) $fatal(1,"UNEXPECTED response");
   pending=0; responses=responses+1;
 end
 if(done) begin
   if(error !== 0 || pending) $fatal(1,"unexpected completion error/outstanding");
   completions=completions+1;
 end
 end
end
task automatic launch(input integer projection, input integer position);
begin
 @(negedge clk); while(cmd_ready !== 1) @(negedge clk);
 cmd_proj=projection; cmd_pos=position; cmd_valid=1;
 @(negedge clk); cmd_valid=0;
 while(done !== 1) @(negedge clk);
 @(negedge clk);
end endtask
initial begin
 #1; reset_check(); repeat(3) @(negedge clk); rst_n=1;
""" + commands + """
 if(accepted!=responses || pending || writes==0 || stalls==0)
   $fatal(1,"COVERAGE missing transfer/write/stall");
 $display("PASS public writes=%0d transactions=%0d stalls=%0d",writes,accepted,stalls);
 $finish;
end endmodule
"""


def gemv_extremes(run):
    # H=8 and I=16384 are legal. Down projection's 16384 products exceed
    # signed 64-bit range. Its second half cancels to a nonsaturating zero.
    params = "#(.NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(16384),.NUM_Q_HEADS(2),.NUM_KV_HEADS(2),.HEAD_DIM(4),.GROUP_SIZE(8),.MAX_SEQ_LEN(1))"
    instance = "anvil_q1_w4a16_gemv "+params+" dut("+BUS_CONNECT+",.cmd_proj(cmd_proj));"
    reader = """
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 case(kind)
 8: begin
   if(row!=11 || col>=16384) $fatal(1,"activation address");
   read_memory=col<8192 ? 32'd32767 : 32'd32769;
 end
 1: begin
   if(proj!=6 || row>=16384 || col!=0) $fatal(1,"qweight address");
   read_memory=32'hffffffff;
 end
 2: begin
   if(proj!=6 || row>=2048 || col!=0) $fatal(1,"qzero address");
   read_memory=0;
 end
 3: begin
   if(proj!=6 || row>=2048 || col>=8) $fatal(1,"scale address");
   read_memory=16'h7bff;
 end
 default: begin $fatal(1,"illegal kind or forbidden down bias"); read_memory=0; end
 endcase
end endfunction
"""
    expected = """
if(mem_req_kind!==8 || mem_req_row!==12 || mem_req_col!==writes ||
   mem_req_proj!==0 || mem_req_wdata!==0)
 $fatal(1,"GEMV widened cancellation write %0d got %h",writes,mem_req_wdata);
"""
    exact_peak = 8192*32767*64393052160
    require(exact_peak > 2**63, "wide accumulator case must cross signed64")
    stdout = compile_sim(run, command_tb(instance, reader, expected,
                         'launch(6,0); if(writes!=8) $fatal(1,"missing outputs");'),
                         "gemv-wide-cancellation", timeout=35)
    run.result("gemv_wide_cancellation", exact_peak=exact_peak,
               expected_final_accumulator=0, outputs=8, outcome="pass", stdout=stdout)


def rope_test(run):
    d, qh, kvh = 4, 4, 2
    positions = (1, 3, 32767)
    initial = {(slot, c): (-1 if c%2 else 1)*(31+17*c)
               for slot, heads in ((2, qh), (3, kvh)) for c in range(heads*d)}
    # Each invocation starts from the previous public writes, exactly as an
    # ordinary external memory would; only coefficient values are provisioned.
    mem = dict(initial)
    writes = []
    coefficients = {}
    for pos in positions:
        for pair in range(d//2):
            angle = pos*1000000.0**(-2*pair/d)
            for bit, v in enumerate((math.cos(angle), math.sin(angle))):
                coefficients[pos, 2*pair+bit] = rounded(int(v*2**52), 2**22)
        for slot, heads in ((2, qh), (3, kvh)):
            for head in range(heads):
                for pair in range(d//2):
                    a, b = head*d+pair, head*d+pair+d//2
                    x, y = mem[slot, a], mem[slot, b]
                    c, s = coefficients[pos, 2*pair], coefficients[pos, 2*pair+1]
                    xx, yy = sat(rounded(x*c-y*s, 2**30)), sat(rounded(y*c+x*s, 2**30))
                    require(abs(xx-(x*math.cos(pos*1000000**(-2*pair/d))-
                                         y*math.sin(pos*1000000**(-2*pair/d)))) <= 2,
                            "floating RoPE quality")
                    mem[slot, a], mem[slot, b] = xx, yy
                    writes += [(slot, a, xx), (slot, b, yy)]
    expected = run.out / "rope-expected.hex"
    expected.write_text("\n".join(f"{slot:02x}{col:08x}{v&65535:04x}" for slot,col,v in writes)+"\n")
    init_lines = "\n".join(f"storage[{slot}][{col}]=16'h{v&65535:04x};"
                           for (slot,col),v in initial.items())
    coef_cases = "\n".join(f"64'h{pos:08x}{col:08x}:read_memory=32'h{v&0xffffffff:08x};"
                           for (pos,col),v in coefficients.items())
    reader = f"""
reg [15:0] storage[0:3][0:15]; reg [55:0] expected[0:{len(writes)-1}];
initial begin {init_lines} $readmemh("{expected}",expected); end
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(proj!=0) $fatal(1,"RoPE unused projection");
 if(kind==8 && (row==2 || row==3) && col<(row==2 ? 16:8))
   read_memory={{16'd0,storage[row][col]}};
 else if(kind==11) case({{row,col}})
 {coef_cases}
 default: begin $fatal(1,"RoPE coefficient address"); read_memory=0; end
 endcase
 else begin $fatal(1,"RoPE illegal address"); read_memory=0; end
end endfunction
"""
    check = f"""
if(writes>={len(writes)} || mem_req_kind!==8 ||
 {{mem_req_row[7:0],mem_req_col,mem_req_wdata[15:0]}} !== expected[writes] ||
 mem_req_wdata[31:16]!==0)
 $fatal(1,"ROPE write mismatch %0d got row %0d col %0d data %h",
 writes,mem_req_row,mem_req_col,mem_req_wdata);
storage[mem_req_row][mem_req_col]=mem_req_wdata[15:0];
"""
    params = "#(.NUM_LAYERS(1),.HIDDEN_SIZE(16),.NUM_Q_HEADS(4),.NUM_KV_HEADS(2),.HEAD_DIM(4),.MAX_SEQ_LEN(32768))"
    instance = "anvil_q1_rope "+params+" dut("+BUS_CONNECT+");"
    commands = "\n".join(f"launch(0,{p});" for p in positions)
    commands += f'\nif(writes!={len(writes)}) $fatal(1,"RoPE write coverage");'
    stdout = compile_sim(run, command_tb(instance,reader,check,commands), "rope")
    run.result("rope", positions=list(positions), theta=1000000,
               compared_writes=len(writes), floating_tolerance_q8_lsb=2,
               outcome="pass", stdout=stdout)


def portability(run):
    paths = []
    for name in ("iverilog", "iverilog12", "iverilog13", "iverilog-12", "iverilog-13"):
        p = shutil.which(name)
        if p and os.path.realpath(p) not in paths:
            paths.append(os.path.realpath(p))
    majors = set()
    for index, compiler in enumerate(paths):
        code, stdout, stderr = run.command([compiler, "-V"], f"compiler-{index}-version")
        require(code == 0, "compiler version failed")
        version = stdout+stderr
        for major in (12, 13):
            if f"Icarus Verilog version {major}." in version:
                majors.add(major)
        for label, values in [("default", None), *MATRIX.items()]:
            overrides = [] if values is None else [
                argument for key,value in zip(KEYS,values)
                for argument in ("-P", f"anvil_q1_top.{key}={value}")]
            code, _, stderr = run.command(
                [compiler,"-g2012","-Wall","-t","null","-s","anvil_q1_top",
                 *overrides,*RTL], f"elaborate-{index}-{label}", timeout=15)
            require(code == 0 and not stderr.strip(), f"warning-clean elaboration {label}: {stderr}")
            run.result(f"elaboration-{index}-{label}", outcome="pass", executable=compiler)
    require(majors == {12,13}, f"UNMET prerequisite: installed Icarus majors {sorted(majors)}; need 12 and 13")


def synthesis(run):
    for label, values in MATRIX.items():
        script = run.out / f"synthesis-{label}.ys"
        output = run.out / f"netlist-{label}.json"
        script.write_text("read_verilog -sv "+ " ".join(str(p) for p in RTL)+"\n"+
                          "chparam "+" ".join(f"-set {k} {v}" for k,v in zip(KEYS,values))+
                          " anvil_q1_top\nhierarchy -check -top anvil_q1_top\n"+
                          "proc\nopt\nmemory\nopt\ncheck -assert\nwrite_json "+str(output)+"\n")
        code, stdout, stderr = run.command(["yosys","-Q","-T","-s",script],
                                           f"synthesis-{label}", timeout=25)
        require(code == 0, f"Yosys {label}: {stderr or stdout[-3000:]}")
        modules = json.loads(output.read_text())["modules"]
        visited = set()
        state = 0
        types = set()

        def visit(name):
            nonlocal state
            if name in visited:
                return
            visited.add(name)
            module = modules[name]
            types.add(module.get("attributes",{}).get("hdlname",name).split()[0].lstrip("\\"))
            for cell in module.get("cells",{}).values():
                typ = cell["type"]
                require("latch" not in typ.lower(), f"inferred latch: {name} {typ}")
                if "dff" in typ.lower():
                    state += 1
                if typ in modules:
                    require(any(cell["connections"].values()), "disconnected child")
                    visit(typ)
        visit("anvil_q1_top")
        required = {"anvil_q1_top","anvil_q1_decoder_layer","anvil_q1_rmsnorm",
                    "anvil_q1_w4a16_gemv","anvil_q1_awq_dequant","anvil_q1_rope",
                    "anvil_q1_gqa_attention","anvil_q1_swiglu_mlp"}
        require(required <= types and state>20, f"missing functional hierarchy/state {types}, {state}")
        run.result(f"synthesis-{label}", outcome="pass", sequential_cells=state,
                   zero_latches=True, hierarchy=sorted(types))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=("behavior","synthesis","portability"), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--probe", choices=("dequant","rope","gemv"), default=None)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run = Run(args.out, args.repair_of)
    try:
        for name in ("python3", "iverilog", "vvp", "yosys"):
            executable = shutil.which(name)
            if executable:
                run.command([executable, "-V" if name in ("iverilog","yosys","vvp") else "--version"],
                            name+"-version", timeout=5)
        if args.check == "behavior":
            slices = manifest(run)
            if args.probe in (None, "dequant"):
                dequant_test(run, slices)
            if args.probe in (None, "rope"):
                rope_test(run)
            if args.probe in (None, "gemv"):
                gemv_extremes(run)
            if args.probe is None:
                raise AssertionError("INCOMPLETE: mandatory layer-stack matrix, nonlinear quality, "
                                     "protocol/error/reset matrix and behavioral mutations not yet implemented")
        elif args.check == "synthesis":
            synthesis(run)
        else:
            portability(run)
        run.result("check", outcome="pass", scope=args.probe or args.check)
    except (AssertionError, ValueError, OSError, KeyError) as exc:
        run.result("check", outcome="fail", diagnosis=str(exc))
        print(str(exc), file=sys.stderr)
        return 1
    print("PASS", args.probe or args.check)
    return 0


if __name__ == "__main__":
    sys.exit(main())
