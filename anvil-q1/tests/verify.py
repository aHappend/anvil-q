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
    require(d > 0, "rounding division requires a positive denominator")
    return (-1 if n < 0 else 1) * ((2*abs(n)+d)//(2*d))


def sat(x, bits=32):
    return min((1 << (bits-1))-1, max(-(1 << (bits-1)), x))


def half_fixed(raw, bits=16):
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
    require(code == 0 and "PASS" in stdout,
            f"{name}: {'subprocess timeout' if code is None else 'behavioral failure'}: {stdout} {stderr}")
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
integer stalls=0, responses=0, completions=0, busy_holds=0, bubbles=0;
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
 if(^{cmd_ready,done,error,mem_req_valid,mem_rsp_ready} === 1'bx)
   $fatal(1,"ACTIVE unknown handshake at rising edge");
 if(mem_req_valid && ^{mem_req_write,mem_req_kind,mem_req_layer,
    mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata} === 1'bx)
   $fatal(1,"ACTIVE unknown request payload at rising edge");
 if(^{cmd_ready,done,error,mem_req_valid,mem_rsp_ready} === 1'bx)
   $fatal(1,"ACTIVE unknown handshake");
 if(mem_req_valid && ^{mem_req_write,mem_req_kind,mem_req_layer,
    mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata} === 1'bx)
   $fatal(1,"ACTIVE unknown request payload");
   mem_req_ready = cycles%31 != 0;
   mem_rsp_valid = pending && delay_count==0;
   mem_rsp_rdata = reply;
 end
end
always @(posedge clk) begin
 cycles=cycles+1;
 if(!rst_n) reset_check();
 else begin
 if(cycles>120000000) $fatal(1,"WATCHDOG");
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
   accepted=accepted+1; pending=1; delay_count=(accepted%127==0 ? 2 : 0);
   if(accepted%262144==0) begin
     $display("PROGRESS accepted=%0d compared_writes=%0d completed=%0d cycles=%0d",
       accepted,writes,completions,cycles);
     $fflush();
   end
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
 if(cmd_valid && !cmd_ready && !done) busy_holds=busy_holds+1;
 if(!cmd_valid && cmd_ready) begin
   if(mem_req_valid || done || error) $fatal(1,"IDLE bubble produced work");
   bubbles=bubbles+1;
 end
 end
end
task automatic launch(input integer projection, input integer position);
begin
 @(negedge clk); while(cmd_ready !== 1) @(negedge clk);
 cmd_proj=projection; cmd_pos=position; cmd_valid=1;
 repeat(3) begin
   @(negedge clk);
   if(cmd_ready!==0) $fatal(1,"BUSY accepted held valid");
 end
 cmd_valid=0;
 while(done !== 1) @(negedge clk);
 @(negedge clk);
 repeat(2) @(negedge clk);
end endtask
initial begin
 #0; reset_check(); #1; reset_check(); repeat(3) @(negedge clk); rst_n=1;
""" + commands + """
 if(accepted!=responses || pending || writes==0 || stalls==0 ||
    busy_holds==0 || bubbles==0)
   $fatal(1,"COVERAGE missing transfer/write/stall");
 $display("PASS public writes=%0d transactions=%0d stalls=%0d busy_holds=%0d bubbles=%0d",
   writes,accepted,stalls,busy_holds,bubbles);
 $finish;
end endmodule
"""


def gemv_extremes(run, sources=None, name="gemv-wide-cancellation", small=True):
    # H=8 and I=9216 are legal. Down projection's first 4608 products exceed
    # signed 64-bit range. Its second half cancels to a nonsaturating zero.
    params = "#(.NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(9216),.NUM_Q_HEADS(2),.NUM_KV_HEADS(2),.HEAD_DIM(4),.GROUP_SIZE(8),.MAX_SEQ_LEN(1))"
    instance = "anvil_q1_w4a16_gemv "+params+" dut("+BUS_CONNECT+",.cmd_proj(cmd_proj));"
    reader = """
integer test_case=0;
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 case(kind)
 8: begin
   if(row!=11 || col>=9216) $fatal(1,"activation address");
   case(test_case)
   0: read_memory=col<4608 ? 32'd8388352 : -32'sd8388352;
   1: read_memory=col<4608 ? 8388352 : 0;
   2: read_memory=col<4608 ? -8388352 : 0;
   3: read_memory=col==0 ? 256 : 0;
   4: read_memory=col==0 ? -256 : 0;
   5: read_memory=col==0 ? 32'h7fffffff : 0;
   default: read_memory=col==0 ? 32'h80000000 : 0;
   endcase
 end
 1: begin
   if(proj!=6 || row>=9216 || col!=0) $fatal(1,"qweight address");
   if(test_case==0)
     read_memory=row<4608 ? 32'hffffff0f : 32'hfff0ff0f;
   else read_memory=32'hffffffff;
 end
 2: begin
   if(proj!=6 || row>=1152 || col!=0) $fatal(1,"qzero address");
   if(test_case==0)
     read_memory=row<576 ? 32'h000000f0 : 32'h00000000;
   else read_memory=0;
 end
 3: begin
   if(proj!=6 || row>=1152 || col>=8) $fatal(1,"scale address");
   read_memory=(test_case==3 || test_case==4) ? 16'h6c00 : 16'h7bff;
 end
 default: begin $fatal(1,"illegal kind or forbidden down bias"); read_memory=0; end
 endcase
end endfunction
"""
    expected = """
expected_value=test_case==0 ?
 ((writes%8)==1 ? 32'h7fffffff : ((writes%8)==2 ? 32'h80000000 : 0)) :
 ((test_case==1 || test_case==5) ? 32'h7fffffff :
  ((test_case==2 || test_case==6) ? 32'h80000000 :
  (test_case==3 ? 32'd15728640 : -32'sd15728640)));
if(mem_req_kind!==8 || mem_req_row!==12 || mem_req_col!==(writes%8) ||
   mem_req_proj!==0 || mem_req_wdata!==expected_value)
 $fatal(1,"GEMV widened cancellation write %0d got %h",writes,mem_req_wdata);
"""
    exact_peak = 4608*(32767*256)*64393052160
    require(exact_peak > 2**63, "wide accumulator case must cross signed64")
    commands = """
launch(6,0);
if(writes!=8) $fatal(1,"missing outputs");
"""
    stdout = compile_sim(run, command_tb(instance, reader, expected, commands),
                         name, sources=sources, timeout=35)
    run.result("gemv_wide_cancellation", exact_peak=exact_peak,
               expected_cancellation_accumulator=0, outputs=8,
               wide_saturating_outputs=2,
               scales=[65504],
               outcome="pass", stdout=stdout)
    if not small:
        return
    small_reader = reader.replace("9216","8").replace("1152","1").replace(
        "col<4608", "col==0")
    small_params = params.replace("9216","8")
    small_instance = "anvil_q1_w4a16_gemv "+small_params+" dut("+BUS_CONNECT+",.cmd_proj(cmd_proj));"
    small_commands = """
for(test_case=1;test_case<7;test_case=test_case+1) launch(6,0);
if(writes!=48) $fatal(1,"small saturation output coverage");
"""
    stdout = compile_sim(run,command_tb(small_instance,small_reader,expected,small_commands),
                         name+"-saturation",sources=sources)
    run.result("gemv_wide_saturation", outputs=48, scales=[4096,65504],
               outcome="pass", stdout=stdout)


def official_gemv(run, slices):
    """Public 8x8 submatrix evaluation, all within official input group zero."""
    tensors = slices["tensors"]
    activations = [x*256 for x in (-769,511,-257,127,-31,17,-1,3)]
    cases, writes = [], []
    comparisons = 0
    for p,name,no in ((0,"self_attn.q_proj",8),
                      (1,"self_attn.k_proj",8),(4,"mlp.gate_proj",8)):
        prefix = "model.layers.0."+name+"."
        ts = [tensors[prefix+s]["raw_hex"] for s in ("qweight","qzeros","scales")]
        biases = tensors.get(prefix+"bias",{}).get("raw_hex",[])
        for r in range(8):
            for c in range(no//8):
                word = int(ts[0][r][0],16) if r<8 and c==0 else 0
                cases.append((1,p,r,c,word))
        for c in range(no//8):
            cases.append((2,p,0,c,int(ts[1][0][0],16) if c==0 else 0))
        for c in range(no):
            scale = int(ts[2][0][c],16) if c<8 else 0
            cases.append((3,p,0,c,scale))
            total = 0
            if c<8:
                for r,x in enumerate(activations):
                    value,invalid = dequant(int(ts[0][r][0],16),
                                            int(ts[1][0][0],16),scale,c)
                    require(not invalid,"official scale invalid")
                    total += x*value
                    comparisons += 1
            if p<3:
                bias = int(biases[c],16) if c<len(biases) else 0
                cases.append((4,p,0,c,bias))
                total += sat(half_fixed(bias))*65536
            writes.append((2 if p==0 else 3 if p==1 else 9,c,
                           sat(rounded(total,65536)) & 0xffffffff))
    reader_cases = "\n".join(
        f"71'h{((kind<<67)|(p<<64)|(r<<32)|c):018x}:read_memory=32'h{value:08x};"
        for kind,p,r,c,value in cases)
    activation_cases = "\n".join(f"{c}:read_memory=32'h{x&0xffffffff:08x};"
                                  for c,x in enumerate(activations))
    reader = """
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(kind==8) begin
   if(proj!=0 || col>=8 || row!=(cmd_proj==4 ? 8:1))
     $fatal(1,"official activation address");
   case(col)
""" + activation_cases + """
   default:read_memory=0;
   endcase
 end else case({kind,proj,row,col})
""" + reader_cases + """
 default: begin $fatal(1,"official tensor address"); read_memory=0; end
 endcase
end endfunction
"""
    expected = run.out/"official-gemv-writes.hex"
    expected.write_text("\n".join(f"{row:08x}{col:08x}{value:08x}"
                                  for row,col,value in writes)+"\n")
    reader += f"""
reg [95:0] expected[0:{len(writes)-1}];
initial $readmemh("{expected}",expected);
"""
    check = f"""
if(writes>={len(writes)} || mem_req_kind!==8 || mem_req_proj!==0 ||
 {{mem_req_row,mem_req_col,mem_req_wdata}} !== expected[writes])
 $fatal(1,"OFFICIAL GEMV write mismatch %0d",writes);
"""
    params = "#(.NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),.NUM_Q_HEADS(2),.NUM_KV_HEADS(2),.HEAD_DIM(4),.GROUP_SIZE(8),.MAX_SEQ_LEN(1))"
    instance = "anvil_q1_w4a16_gemv "+params+" dut("+BUS_CONNECT+",.cmd_proj(cmd_proj));"
    commands = """
launch(0,0); if(accepted!=41) $fatal(1,"GEMV Q transaction count");
launch(1,0); if(accepted!=82) $fatal(1,"GEMV K transaction count");
launch(4,0); if(accepted!=115) $fatal(1,"GEMV gate forbidden bias/count");
"""
    commands += f'if(writes!={len(writes)}) $fatal(1,"official outputs missing");'
    stdout = compile_sim(run,command_tb(instance,reader,check,commands),
                         "official-gemv",timeout=30)
    run.result("official_gemv", official_scalar_products=comparisons,
               official_submatrices="Q/K/gate rows 0:8 channels 0:8",
               synthetic_padding="none: only supplied rows/channels; scaled G8 stays in official G128 group zero",
               compared_outputs=len(writes), outcome="pass", stdout=stdout)


def rms_test(run):
    rng = random.Random(43)
    values = [rng.randint(-700,700)*256 for _ in range(16)]
    gammas = [0x3c00,0xbc00,0x3800,0x4000,0x0001,0x03ff,0x8000,0x3bff]*2
    reciprocal = (1 << 64)//math.isqrt((sum(x*x for x in values) << 32)//16+18446744073710)
    expected = [sat(rounded(x*sat(half_fixed(h))*reciprocal,1 << 48))
                for x,h in zip(values,gammas)]
    denom = math.sqrt(sum((x/65536)**2 for x in values)/16+1e-6)
    errors = [abs(y/65536-(x/65536)*(sat(half_fixed(g))/65536)/denom)*256
              for x,g,y in zip(values,gammas,expected)]
    require(max(errors)<=2, "floating RMS quality")
    initial = "\n".join(f"activation[{i}]=32'h{x&0xffffffff:08x}; gamma[{i}]=16'h{g:04x}; exp_data[{i}]=32'h{e&0xffffffff:08x};"
                        for i,(x,g,e) in enumerate(zip(values,gammas,expected)))
    reader = f"""
reg [31:0] activation[0:15],exp_data[0:15]; reg [15:0] gamma[0:15];
initial begin {initial} end
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(proj!=0 || row!=0 || col>=16) $fatal(1,"RMS address");
 if(kind==8) read_memory=activation[col];
 else if(kind==5) read_memory={{16'd0,gamma[col]}};
 else begin $fatal(1,"RMS illegal kind"); read_memory=0; end
end endfunction
"""
    check = """
if(mem_req_kind!==8 || mem_req_proj!==0 || mem_req_row!==1 ||
   mem_req_col!==writes || mem_req_wdata!==exp_data[writes])
 $fatal(1,"RMS write mismatch %0d got %h",writes,mem_req_wdata);
"""
    instance = "anvil_q1_rmsnorm #(.NUM_LAYERS(1),.HIDDEN_SIZE(16)) dut("+BUS_CONNECT+",.cmd_mode(cmd_mode));"
    stdout = compile_sim(run, command_tb(instance,reader,check,
                         'launch(0,0); if(writes!=16) $fatal(1,"RMS missing outputs");'), "rms")
    run.result("rms", exact_comparisons=16, floating_max_error_q8_lsb=max(errors),
               threshold_q8_lsb=2, outcome="pass", stdout=stdout)


def exp_integer(x):
    if x < -16*65536:
        return 0
    if x >= 0:
        return 1 << 24
    n, r = divmod(-x*256, 11629080)
    term = total = 1 << 24
    for j in range(1,7):
        numerator = -term*r
        term = (-1 if numerator<0 else 1)*(abs(numerator)//(j*(1 << 24)))
        total += term
    return max(0,total) >> n


def conversion_test(run):
    """Observe ordinary F16 conversion through top embedding writes only."""
    raw = [sign | exponent*1024 | mantissa
           for sign in (0,0x8000) for exponent in range(31)
           for mantissa in (0,1,127,128,129,511,512,1023)]
    require(len(raw)%8==0,"conversion block size")
    expected = [sat(half_fixed(h)) for h in raw]
    vector = run.out/"conversion.hex"
    vector.write_text("\n".join(f"{h:04x}{v&0xffffffff:08x}"
                                 for h,v in zip(raw,expected))+"\n")
    params = dict(zip(KEYS,MATRIX["D"])) | {"VOCAB_SIZE":len(raw)//8}
    connect = BUS_CONNECT.replace(
        ".cmd_valid(cmd_valid),.cmd_ready(cmd_ready)",
        ".token_valid(cmd_valid),.token_ready(cmd_ready)").replace(
        ".cmd_layer(cmd_layer),.cmd_pos(cmd_pos)",
        ".token_id(cmd_layer),.token_pos(cmd_pos)")
    declarations = ",".join(f".{k}({v})" for k,v in params.items())
    text = "module tb;\n"+BUS_PORTS+f"""
reg [47:0] vectors[0:{len(raw)-1}];
integer block_index=0,writes=0,reads=0,cycles=0;
reg pending=0; reg [31:0] reply=0;
wire logit_valid; wire [31:0] logit_index; wire signed [31:0] logit_data;
initial $readmemh("{vector}",vectors);
anvil_q1_top #({declarations}) dut("""+connect+"""
,.new_sequence(1'b1),.logit_valid(logit_valid),.logit_ready(1'b0),
.logit_index(logit_index),.logit_data(logit_data));
always @(negedge clk) begin
 mem_req_ready=rst_n; mem_rsp_valid=rst_n && pending; mem_rsp_rdata=reply;
end
always @(posedge clk) if(rst_n) begin
 cycles=cycles+1; if(cycles>100000) $fatal(1,"CONVERSION watchdog");
 if(done || error || logit_valid) $fatal(1,"CONVERSION unexpected completion");
 if(mem_req_valid && mem_req_ready) begin
   if(pending || mem_rsp_ready || mem_req_layer!==0 || mem_req_proj!==0 ||
      mem_req_col>=8) $fatal(1,"CONVERSION protocol/address");
   pending=1;
   if(mem_req_write) begin
     if(mem_req_kind!==8 || mem_req_row!==0 || mem_req_col!==(writes%8) ||
        mem_req_wdata!==vectors[writes][31:0])
       $fatal(1,"F16 conversion mismatch %0d got %h expected %h",
         writes,mem_req_wdata,vectors[writes][31:0]);
     writes=writes+1; reply=0;
   end else begin
     if(mem_req_kind!==0 || mem_req_row!==block_index ||
        mem_req_col!==(reads%8) || mem_req_wdata!==0)
       $fatal(1,"CONVERSION unexpected model request");
     reply={16'd0,vectors[reads][47:32]}; reads=reads+1;
   end
 end else if(mem_rsp_valid && mem_rsp_ready) pending=0;
end
initial begin
 #0; #1; repeat(3) @(negedge clk);
"""+f"""
 for(block_index=0;block_index<{len(raw)//8};block_index=block_index+1) begin
   rst_n=1; cmd_layer=block_index;
   @(negedge clk); if(cmd_ready!==1) $fatal(1,"CONVERSION not idle");
   cmd_valid=1; @(negedge clk); cmd_valid=0;
   while(writes<(block_index+1)*8) @(negedge clk);
   // Abort after the observed final embedding write, before decoder work.
   rst_n=0; pending=0; mem_rsp_valid=0; repeat(2) @(negedge clk);
 end
 if(writes!={len(raw)} || reads!={len(raw)}) $fatal(1,"CONVERSION coverage");
 $display("PASS ordinary F16 conversions=%0d",writes); $finish;
end endmodule
"""
    stdout = compile_sim(run,text,"conversion")
    run.result("ordinary_f16_conversion",outcome="pass",compared=len(raw),
               exponent_fields=list(range(31)),signed_zeros=True,subnormal_ties=True,
               saturation=True,scope="embedding writes; reset aborts before decoder",
               stdout=stdout)


def elementwise_boundaries(run):
    pairs = [(2**31-1,1),(-2**31,-1),(2**31-1,2**31-1),
             (-2**31,-2**31),(1,-1),(-1,0),(32768,65537),(-32768,65537)]
    product_pairs = [(2**31-1,2**31-1),(2**31-1,-2**31),
                     (-2**31,2**31-1),(1,65536),(-1,65536),
                     (65536,32768),(-65536,32768),(0,-2**31)]
    expectations = [sat(a+b) for a,b in pairs]*2
    for a,b in product_pairs:
        e=exp_integer(-abs(a))
        sigmoid=((1<<48) if a>=0 else e*(1<<24))//((1<<24)+e)
        s=sat(rounded(a*sigmoid,1<<24))
        expectations.append(sat(rounded(s*b,65536)))
    inputs = pairs+pairs+product_pairs
    vector = run.out/"elementwise-boundaries.hex"
    vector.write_text("\n".join(f"{a&0xffffffff:08x}{b&0xffffffff:08x}{v&0xffffffff:08x}"
                                 for (a,b),v in zip(inputs,expectations))+"\n")
    reader = f"""
reg [95:0] vectors[0:23]; initial $readmemh("{vector}",vectors);
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(kind!=8 || proj!=0 || col>=8 ||
    (row!=(cmd_mode==0 ? 0 : (cmd_mode==1 ? 7 : 9)) &&
     row!=(cmd_mode==0 ? 6 : (cmd_mode==1 ? 12 : 10))))
   $fatal(1,"ELEMENTWISE boundary address");
 read_memory=(row==(cmd_mode==0 ? 0 : (cmd_mode==1 ? 7 : 9))) ?
   vectors[cmd_mode*8+col][95:64] : vectors[cmd_mode*8+col][63:32];
end endfunction
"""
    check = """
if(mem_req_kind!==8 || mem_req_proj!==0 || mem_req_col!==(writes%8) ||
   mem_req_row!==(cmd_mode==0 ? 7 : (cmd_mode==1 ? 0 : 11)) ||
   mem_req_wdata!==vectors[writes][31:0])
 $fatal(1,"ELEMENTWISE boundary saturation/rounding mismatch %0d",writes);
"""
    instance = "anvil_q1_elementwise #(.NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),.MAX_SEQ_LEN(1)) dut("+BUS_CONNECT+",.cmd_mode(cmd_mode));"
    commands = """
cmd_mode=0; launch(0,0); cmd_mode=1; launch(0,0); cmd_mode=2; launch(0,0);
if(writes!=24) $fatal(1,"ELEMENTWISE boundary coverage");
"""
    stdout=compile_sim(run,command_tb(instance,reader,check,commands),"elementwise-boundaries")
    run.result("elementwise_boundaries",outcome="pass",compared=24,
               boundaries="signed32 extrema, signed33 residual sums, signed64 products, signed ties",
               stdout=stdout)


def floating_stack(memory, get, fixed, dims, shape, tokens, trace=None):
    """Floating tensor algebra, independent of all integer nonlinear helpers."""
    L,H,I,Q,K,D,G,V,S = shape
    cache = {}
    finals, outputs = [], []
    def capture(ordinal, layer, stage, values):
        if trace is not None:
            trace[ordinal,layer,stage] = list(values)
    def norm(x, kind, layer):
        denominator = math.sqrt(sum(v*v for v in x)/H+1e-6)
        return [v*(fixed(kind,layer,0,0,c)/65536)/denominator
                for c,v in enumerate(x)]
    def linear(x, layer, projection):
        ni,no = dims[projection]
        result = []
        for c in range(no):
            total = 0.0
            for k in range(ni):
                qw = get(1,layer,projection,k,c//8)
                qz = get(2,layer,projection,k//G,c//8)
                w = ((qw >> SHIFTS[c%8]) & 15)-((qz >> SHIFTS[c%8]) & 15)
                scale = half_fixed(get(3,layer,projection,k//G,c),16)/65536
                total += x[k]*w*scale
            if projection < 3:
                total += fixed(4,layer,projection,0,c)/65536
            result.append(total)
        return result
    def rotate(x, heads, position):
        result = list(x)
        for h in range(heads):
            for i in range(D//2):
                angle = position*1000000.0**(-2*i/D)
                a,b = h*D+i,h*D+i+D//2
                co,si = math.cos(angle),math.sin(angle)
                result[a],result[b] = x[a]*co-x[b]*si,x[b]*co+x[a]*si
        return result
    for ordinal,(token,position) in enumerate(tokens):
        if position == 0:
            cache.clear()
        x = [fixed(0,0,0,token,c)/65536 for c in range(H)]
        capture(ordinal,-1,"embedding",x)
        for layer in range(L):
            normalized = norm(x,5,layer)
            capture(ordinal,layer,"norm_input",normalized)
            q = linear(normalized,layer,0)
            k = linear(normalized,layer,1)
            v = linear(normalized,layer,2)
            for stage,values in (("q",q),("k",k),("v",v)):
                capture(ordinal,layer,stage,values)
            q = rotate(q,Q,position)
            k = rotate(k,K,position)
            capture(ordinal,layer,"q_rope",q)
            capture(ordinal,layer,"k_rope",k)
            cache[layer,position] = k,v
            context = []
            for head in range(Q):
                kh = head//(Q//K)
                scores = [sum(q[head*D+c]*cache[layer,t][0][kh*D+c]
                              for c in range(D))/math.sqrt(D)
                          for t in range(position+1)]
                es = [math.exp(s-max(scores)) for s in scores]
                context.extend(sum(e*cache[layer,t][1][kh*D+c]
                                   for t,e in enumerate(es))/sum(es)
                               for c in range(D))
            projected = linear(context,layer,3)
            capture(ordinal,layer,"context",context)
            capture(ordinal,layer,"o",projected)
            residual = [a+b for a,b in zip(x,projected)]
            capture(ordinal,layer,"residual_attention",residual)
            normalized = norm(residual,6,layer)
            capture(ordinal,layer,"norm_post",normalized)
            gate,up = linear(normalized,layer,4),linear(normalized,layer,5)
            capture(ordinal,layer,"gate",gate)
            capture(ordinal,layer,"up",up)
            silu = [a/(1+math.exp(-a)) for a in gate]
            capture(ordinal,layer,"silu",silu)
            product = [a*b for a,b in zip(silu,up)]
            capture(ordinal,layer,"product",product)
            down = linear(product,layer,6)
            capture(ordinal,layer,"down",down)
            x = [a+b for a,b in zip(residual,down)]
            capture(ordinal,layer,"residual_mlp",x)
        x = norm(x,7,0)
        capture(ordinal,-1,"final",x)
        finals.append(x)
        outputs.extend(sum(x[c]*fixed(0,0,0,r,c)/65536 for c in range(H))
                       for r in range(V))
    return finals,outputs


def numerical_audit(run,label,seed,get,fixed,dims,positions,integer_trace,
                    float_trace,saturation,violations,logits,files):
    """Replay stage equations from public vectors, not implementation helpers.

    Rational rounding and separately decoded halfwords cross-check the integer
    oracle. Accurate floating reductions cross-check the unrounded layer stack.
    This is a mathematical contract witness, not an observed RTL result.
    """
    from fractions import Fraction
    L,H,I,Q,K,D,G,V,S = MATRIX[label]
    def nearest(value):
        magnitude = abs(value)
        result = (magnitude+Fraction(1,2)).numerator // (magnitude+Fraction(1,2)).denominator
        return -result if value<0 else result
    def clipped(value):
        return min(2147483647,max(-2147483648,value))
    def raw_half(kind,layer,proj,row,col):
        raw = get(kind,layer,proj,row,col)
        return Fraction.from_float(struct.unpack("<e",struct.pack("<H",raw))[0])
    def coefficient(kind,layer,proj,row,col):
        return clipped(nearest(raw_half(kind,layer,proj,row,col)*65536))
    def exponential(score):
        if score < -1048576:
            return 0
        magnitude = -min(score,0)*256
        n,remainder = divmod(magnitude,11629080)
        terms = [16777216]
        for order in range(1,7):
            value = Fraction(-terms[-1]*remainder,order*16777216)
            terms.append(int(value))
        return max(0,sum(terms))//(2**n)
    weights = {}
    for layer in range(L):
        for projection,(ni,no) in enumerate(dims):
            matrix = []
            for channel in range(no):
                nibble = 4*(channel%2)+(channel%8)//2
                matrix.append([
                    (((get(1,layer,projection,k,channel//8)//(16**nibble))%16)-
                     ((get(2,layer,projection,k//G,channel//8)//(16**nibble))%16))*
                    nearest(raw_half(3,layer,projection,k//G,channel)*65536)
                    for k in range(ni)])
            weights[layer,projection] = matrix
    records = []
    checks = []
    def check(ordinal,layer,stage,expected,float_expected):
        key = ordinal,layer,stage
        actual,reference = integer_trace[key],float_trace[key]
        require(actual==expected,f"AUDIT integer equation {key}")
        float_residual = max(abs(a-b) for a,b in zip(reference,float_expected))
        require(float_residual<1e-10,f"AUDIT floating equation {key}: {float_residual}")
        errors = [a/65536-b for a,b in zip(actual,reference)]
        records.append(dict(token_ordinal=ordinal,position=positions[ordinal],
                            layer=layer,stage=stage,integer_q16_16=actual,
                            floating=reference,error_q8_lsb=[x*256 for x in errors],
                            max_absolute_error_q8_lsb=max(abs(x)*256 for x in errors),
                            rms_error_q8_lsb=math.sqrt(math.fsum(x*x for x in errors)/len(errors))*256,
                            saturation_count=saturation.get(key,0),
                            integer_min=min(actual),integer_max=max(actual),
                            floating_equation_residual=float_residual))
        checks.append(len(actual))
    for ordinal,pos in enumerate(positions):
        def iv(layer,stage):
            return integer_trace[ordinal,layer,stage]
        def fv(layer,stage):
            return float_trace[ordinal,layer,stage]
        token = (seed+ordinal)%V
        embedding = [coefficient(0,0,0,token,c) for c in range(H)]
        check(ordinal,-1,"embedding",embedding,[x/65536 for x in embedding])
        def norm(layer,stage,source_layer,source_stage,kind):
            x,y = iv(source_layer,source_stage),fv(source_layer,source_stage)
            mean = sum(a*a for a in x)*2**32//H+18446744073710
            denominator = math.isqrt(mean)
            require(denominator**2<=mean<(denominator+1)**2,"AUDIT sqrt interval")
            reciprocal = 2**64//denominator
            gamma = [coefficient(kind,max(layer,0),0,0,c) for c in range(H)]
            result = [clipped(nearest(Fraction(a*g*reciprocal,2**48)))
                      for a,g in zip(x,gamma)]
            root = math.sqrt(math.fsum(a*a for a in y)/H+1e-6)
            check(ordinal,layer,stage,result,[a*g/(65536*root) for a,g in zip(y,gamma)])
        def linear(layer,projection,stage,source_stage):
            x,y = iv(layer,source_stage),fv(layer,source_stage)
            expected,reference = [],[]
            for c,row in enumerate(weights[layer,projection]):
                bias = coefficient(4,layer,projection,0,c) if projection<3 else 0
                total = sum(a*w for a,w in zip(x,row))+bias*65536
                expected.append(clipped(nearest(Fraction(total,65536))))
                reference.append(math.fsum(a*w/65536 for a,w in zip(y,row))+bias/65536)
            check(ordinal,layer,stage,expected,reference)
        for layer in range(L):
            source_layer,source_stage = (-1,"embedding") if layer==0 else (layer-1,"residual_mlp")
            norm(layer,"norm_input",source_layer,source_stage,5)
            for projection,stage in enumerate(("q","k","v")):
                linear(layer,projection,stage,"norm_input")
            for stage,heads in (("q",Q),("k",K)):
                a,b = iv(layer,stage),fv(layer,stage)
                actual,reference = list(a),list(b)
                for head in range(heads):
                    for pair in range(D//2):
                        lo,hi = head*D+pair,head*D+pair+D//2
                        co,si = [get(11,0,0,pos,2*pair+bit) for bit in (0,1)]
                        co,si = [v if v<2**31 else v-2**32 for v in (co,si)]
                        actual[lo] = clipped(nearest(Fraction(a[lo]*co-a[hi]*si,2**30)))
                        actual[hi] = clipped(nearest(Fraction(a[hi]*co+a[lo]*si,2**30)))
                        angle = pos/(1000000.0**(2*pair/D))
                        reference[lo] = b[lo]*math.cos(angle)-b[hi]*math.sin(angle)
                        reference[hi] = b[hi]*math.cos(angle)+b[lo]*math.sin(angle)
                check(ordinal,layer,stage+"_rope",actual,reference)
            actual,reference = [],[]
            start = ordinal-pos
            for head in range(Q):
                mapped = (head*K)//Q
                query,query_float = iv(layer,"q_rope"),fv(layer,"q_rope")
                keys = [integer_trace[t,layer,"k_rope"] for t in range(start,ordinal+1)]
                values = [integer_trace[t,layer,"v"] for t in range(start,ordinal+1)]
                fk = [float_trace[t,layer,"k_rope"] for t in range(start,ordinal+1)]
                fvalues = [float_trace[t,layer,"v"] for t in range(start,ordinal+1)]
                scores = [nearest(Fraction(sum(query[head*D+c]*k[mapped*D+c]
                          for c in range(D)),math.isqrt(D*2**32))) for k in keys]
                es = [exponential(s-max(scores)) for s in scores]
                fscores = [math.fsum(query_float[head*D+c]*k[mapped*D+c]
                           for c in range(D))/math.sqrt(D) for k in fk]
                fes = [math.exp(s-max(fscores)) for s in fscores]
                for c in range(D):
                    actual.append(clipped(nearest(Fraction(sum(e*v[mapped*D+c]
                                  for e,v in zip(es,values)),sum(es)))))
                    reference.append(math.fsum(e*v[mapped*D+c]
                                     for e,v in zip(fes,fvalues))/math.fsum(fes))
            check(ordinal,layer,"context",actual,reference)
            linear(layer,3,"o","context")
            check(ordinal,layer,"residual_attention",
                  [clipped(a+b) for a,b in zip(iv(source_layer,source_stage),iv(layer,"o"))],
                  [a+b for a,b in zip(fv(source_layer,source_stage),fv(layer,"o"))])
            norm(layer,"norm_post",layer,"residual_attention",6)
            linear(layer,4,"gate","norm_post")
            linear(layer,5,"up","norm_post")
            silu = []
            for x in iv(layer,"gate"):
                e = exponential(-abs(x))
                sigmoid = ((2**48) if x>=0 else e*2**24)//(2**24+e)
                silu.append(clipped(nearest(Fraction(x*sigmoid,2**24))))
            check(ordinal,layer,"silu",silu,[x/(1+math.exp(-x)) for x in fv(layer,"gate")])
            check(ordinal,layer,"product",
                  [clipped(nearest(Fraction(a*b,65536))) for a,b in zip(silu,iv(layer,"up"))],
                  [a*b for a,b in zip(fv(layer,"silu"),fv(layer,"up"))])
            linear(layer,6,"down","product")
            check(ordinal,layer,"residual_mlp",
                  [clipped(a+b) for a,b in zip(iv(layer,"residual_attention"),iv(layer,"down"))],
                  [a+b for a,b in zip(fv(layer,"residual_attention"),fv(layer,"down"))])
        norm(-1,"final",L-1,"residual_mlp",7)
    contributions = []
    if violations:
        first = violations[0]
        ordinal,vocabulary = divmod(first["index"],V)
        running_integer,running_float = 0,0.0
        for c,(a,b) in enumerate(zip(integer_trace[ordinal,-1,"final"],
                                   float_trace[ordinal,-1,"final"])):
            embedding = coefficient(0,0,0,vocabulary,c)
            running_integer += a*embedding
            running_float += b*embedding/65536
            contributions.append(dict(component=c,embedding_q16_16=embedding,
                integer_final_q16_16=a,floating_final=b,integer_product_q32_32=a*embedding,
                floating_product=b*embedding/65536,error=(a/65536-b)*embedding/65536,
                accumulated_integer=running_integer/2**32,accumulated_floating=running_float,
                accumulated_error=running_integer/2**32-running_float))
        require(clipped(nearest(Fraction(running_integer,65536)))==logits[first["index"]],
                "AUDIT exact logit reduction")
        require(abs(running_float-first["floating_logit"])<1e-12,"AUDIT floating logit reduction")
    prior = ROOT/"evidence/preparation"/(
        "verifier-B17-throughput-diagnostic-04" if seed==17 else "verifier-B89-throughput-diagnostic-01")
    bindings = []
    path = files[0]
    original = prior/path.name
    before = {int(a[1:],16):int(v,16) for a,v in
              (line.split() for line in original.read_text().splitlines())}
    after = {int(a[1:],16):int(v,16) for a,v in
             (line.split() for line in path.read_text().splitlines())}
    sizes = [V*H,L*7*I*(I//8),L*7*(I//G)*(I//8),
             L*7*(I//G)*I,L*3*H,L*H,L*H,H,15*I,L*S*K*D,L*S*K*D,S*D]
    cache_start,cache_end = sum(sizes[:9]),sum(sizes[:11])
    require(before.keys()==after.keys(),"AUDIT memory address inventory changed")
    for address,value in before.items():
        expected = value*256 if cache_start<=address<cache_end else value
        require(after[address]==expected,"AUDIT changed immutable stimulus "+str(address))
    bindings.append(dict(path=str(path.relative_to(ROOT)),prior=str(original.relative_to(ROOT)),
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         immutable_model_words_identical=True,cache_encoding_multiplier=256,
                         regenerated_expectations=[str(p.relative_to(ROOT)) for p in files[1:]]))
    report = dict(configuration=label,seed=seed,observed_rtl=False,
                  stage_records=records,stage_equation_comparisons=sum(checks),
                  saturation_count=sum(saturation.values()),violating_logits=violations,
                  first_violating_logit_component_contributions=contributions,
                  unchanged_vector_bindings=bindings,
                  diagnosis="Replacement integer and floating equations independently replay; "
                  "retained raw model stimuli are unchanged. Oracle quality predictions "
                  "are not completed RTL simulation or engineering acceptance.")
    path = run.out/f"audit-{label}-{seed}.json"
    path.write_text(json.dumps(report,indent=2)+"\n")
    run.result("numerical-audit",configuration=label,seed=seed,
               report=str(path.relative_to(ROOT)),observed_rtl=False,
               stage_equation_comparisons=sum(checks),saturation_count=sum(saturation.values()),
               violating_logits=violations,outcome="prediction")


def progress_probe(run,tb,prefix,sources,seconds):
    sv,executable = run.out/(prefix+".sv"),run.out/(prefix+".vvp")
    sv.write_text(tb)
    code,_,err = run.command(["iverilog","-g2012","-Wall","-s","tb","-o",
                             executable,*(sources or RTL),sv],prefix+"-compile",timeout=5)
    require(code==0 and not err.strip(),"progress compile failure "+err)
    run.command(["timeout","--version"],"timeout-version",timeout=2)
    code,stdout,stderr = run.command(["timeout",str(seconds),"vvp","-v",executable],
                                     prefix+"-progress",timeout=seconds+3)
    require(code in (0,124),"progress unexpected tool failure "+stdout+stderr)
    run.result("bounded-progress",outcome="measurement_not_acceptance",exit_code=code,
               budget_s=seconds,completed_simulation=code==0,
               full_B_gemv_products=573440,minimum_B_gemv_reads=183680,
               raw_stdout=str((run.out/(prefix+"-progress.stdout")).relative_to(ROOT)),
               raw_stderr=str((run.out/(prefix+"-progress.stderr")).relative_to(ROOT)))
    import re
    samples = [dict(accepted=int(a),writes=int(w),completed_tokens=int(t),cycles=int(c))
               for a,w,t,c in re.findall(
                   r"PROGRESS accepted=(\d+) compared_writes=(\d+) completed=(\d+) cycles=(\d+)",
                   stdout)]
    acknowledgements = [dict(token=int(t),layer=int(l),slot=int(s),accepted=int(a),cycles=int(c))
                        for t,l,s,a,c in re.findall(
                            r"PROJECTION_ACK token=(\d+) layer=(\d+) slot=(\d+) accepted=(\d+) cycles=(\d+)",
                            stdout)]
    require(samples,"progress diagnostic observed no public transactions")
    observed = max([s["accepted"] for s in samples]+[a["accepted"] for a in acknowledgements])
    elapsed = run.commands[-1]["elapsed_s"]
    products = 4*2*(112*112*2+112*16*2+112*128*2+128*112)
    require(products==573440,"B workload arithmetic")
    report = dict(outcome="bounded_measurement_not_acceptance",
        samples=samples,projection_final_write_acknowledgements=acknowledgements,
        observed_public_transactions_at_least=observed,elapsed_wall_s=elapsed,
        observed_floor_transaction_rate_per_s=observed/elapsed,
        full_B_gemv_products=products,current_GEMV_input_metadata_reads_per_product=41/128,
        full_B_GEMV_read_transactions=183680,
        extrapolated_B_GEMV_read_only_s=183680/(observed/elapsed),
        extrapolation_is_not_a_completion_bound=True,
        unchanged_matrix_simulation_timeout_s=25,unchanged_aggregate_budget_s=120,
        diagnosis="Public request/response observations are retained with exact arithmetic "
        "comparisons and deterministic stalls. The current eight-output scalar tile "
        "analytically uses 183680 B input/metadata reads, excluding bias/output/other "
        "engines. This diagnostic does not establish full workload completion.",
        designer_handoff="Retain the Q16.16 contract, signed37 dequantization, signed69 "
        "products, signed128 accumulation, scalar eight-output reuse and all public "
        "comparisons. A timeout requires another admitted execution-cost repair, not "
        "larger deadlines or reduced coverage.")
    (run.out/(prefix+"-execution-cost.json")).write_text(json.dumps(report,indent=2)+"\n")


def integrated(run, label, seed, sources=None, name=None, audit=False,
               progress_seconds=None):
    """Functional vector algebra oracle; no RTL state or timing is modeled."""
    L,H,I,Q,K,D,G,V,S = MATRIX[label]
    rng = random.Random(seed)
    kv = K*D
    dims = [(H,H),(H,kv),(H,kv),(H,H),(H,I),(H,I),(I,H)]
    sizes = [V*H,L*7*I*(I//8),L*7*(I//G)*(I//8),
             L*7*(I//G)*I,L*3*H,L*H,L*H,H,15*I,L*S*kv,L*S*kv,S*D]
    offsets = [sum(sizes[:i]) for i in range(12)]

    def address(kind,layer,proj,row,col):
        stride = [row*H+col,
                  ((layer*7+proj)*I+row)*(I//8)+col,
                  ((layer*7+proj)*(I//G)+row)*(I//8)+col,
                  ((layer*7+proj)*(I//G)+row)*I+col,
                  (layer*3+proj)*H+col,layer*H+col,layer*H+col,col,
                  row*I+col,(layer*S+row)*kv+col,(layer*S+row)*kv+col,row*D+col][kind]
        return offsets[kind]+stride

    memory = {}
    def put(kind,l,p,r,c,v):
        memory[address(kind,l,p,r,c)] = v & 0xffffffff
    def get(kind,l,p,r,c):
        return memory[address(kind,l,p,r,c)]
    def fixed(kind,l,p,r,c):
        return sat(half_fixed(get(kind,l,p,r,c)))
    def half(x):
        return struct.unpack("<H",struct.pack("<e",x))[0]

    for r in range(V):
        for c in range(H):
            put(0,0,0,r,c,half(rng.randint(-256,256)/256))
    for l in range(L):
        for p,(ni,no) in enumerate(dims):
            for r in range(ni):
                for w in range(no//8):
                    put(1,l,p,r,w,pack([rng.randint(5,11) for _ in range(8)]))
            for group in range(ni//G):
                for w in range(no//8):
                    put(2,l,p,group,w,pack([rng.randint(7,9) for _ in range(8)]))
                for c in range(no):
                    put(3,l,p,group,c,half(rng.choice((1/128,1/64,3/128))))
            if p<3:
                for c in range(no):
                    put(4,l,p,0,c,half(rng.randint(-24,24)/256))
        for kind in (5,6):
            for c in range(H):
                put(kind,l,0,0,c,half(rng.randint(224,288)/256))
        for pos in range(S):
            for c in range(kv):
                for kind in (9,10):
                    put(kind,l,0,pos,c,(0x7000+c)*256)  # same real-valued poison, Q16.16
    for c in range(H):
        put(7,0,0,0,c,half(rng.randint(240,272)/256))
    for pos in range(S):
        for pair in range(D//2):
            angle=pos*1000000**(-2*pair/D)
            for bit,v in enumerate((math.cos(angle),math.sin(angle))):
                put(11,0,0,pos,2*pair+bit,rounded(int(v*2**52),1 << 22))
    initial = dict(memory)
    expected_writes, logits, final_vectors = [], [], []
    scratch = {}
    integer_trace, float_trace, saturation = {}, {}, {}
    active_stage = None
    def capture(layer,stage,slot=None,n=None,values=None):
        if audit:
            integer_trace[ordinal,layer,stage] = (
                list(values) if values is not None else vector(slot,n))
    def bounded(value):
        if audit and (value < -2147483648 or value > 2147483647):
            saturation[active_stage] = saturation.get(active_stage,0)+1
        return sat(value)
    def write(slot,c,value):
        scratch[slot,c] = value
        expected_writes.append((8,0,slot,c,value & 0xffffffff))
    def vector(slot,n):
        return [scratch[slot,c] for c in range(n)]
    def norm(l,src,dst,kind):
        nonlocal active_stage
        stage = {5:"norm_input",6:"norm_post",7:"final"}[kind]
        active_stage = ordinal,(-1 if kind==7 else l),stage
        x=vector(src,H)
        inv=(1 << 64)//math.isqrt((sum(v*v for v in x) << 32)//H+18446744073710)
        for c,v in enumerate(x):
            write(dst,c,bounded(rounded(v*fixed(kind,l,0,0,c)*inv,1 << 48)))
        capture(active_stage[1],stage,dst,H)
    def linear(l,p,src,dst):
        nonlocal active_stage
        stage = ("q","k","v","o","gate","up","down")[p]
        active_stage = ordinal,l,stage
        ni,no=dims[p]
        x=vector(src,ni)
        for c in range(no):
            total=0
            for k,v in enumerate(x):
                w,invalid=dequant(get(1,l,p,k,c//8),get(2,l,p,k//G,c//8),
                                  get(3,l,p,k//G,c),c%8)
                require(not invalid,"synthetic scale")
                total+=v*w
            if p<3:
                total+=fixed(4,l,p,0,c)*65536
            write(dst,c,bounded(rounded(total,65536)))
        capture(l,stage,dst,no)
    positions = list(range(S))+[0]
    for ordinal,pos in enumerate(positions):
        token=(seed+ordinal)%V
        for c in range(H):
            write(0,c,fixed(0,0,0,token,c))
        capture(-1,"embedding",0,H)
        for l in range(L):
            norm(l,0,1,5)
            for p,src,dst in ((0,1,2),(1,1,3),(2,1,4)):
                linear(l,p,src,dst)
            for slot,heads in ((2,Q),(3,K)):
                stage = "q_rope" if slot==2 else "k_rope"
                active_stage = ordinal,l,stage
                for head in range(heads):
                    for pair in range(D//2):
                        a,b=head*D+pair,head*D+pair+D//2
                        x,y=scratch[slot,a],scratch[slot,b]
                        co=get(11,0,0,pos,2*pair)
                        si=get(11,0,0,pos,2*pair+1)
                        co=co if co<2**31 else co-2**32
                        si=si if si<2**31 else si-2**32
                        write(slot,a,bounded(rounded(x*co-y*si,1 << 30)))
                        write(slot,b,bounded(rounded(y*co+x*si,1 << 30)))
                capture(l,stage,slot,heads*D)
            for slot,kind in ((3,9),(4,10)):
                for c in range(kv):
                    v=scratch[slot,c]
                    put(kind,l,0,pos,c,v & 0xffffffff)
                    expected_writes.append((kind,l,pos,c,v & 0xffffffff))
            active_stage = ordinal,l,"context"
            for head in range(Q):
                kvhead=head//(Q//K)
                scores=[]
                for t in range(pos+1):
                    dot=0
                    for c in range(D):
                        k=get(9,l,0,t,kvhead*D+c)
                        k=k if k<2**31 else k-2**32
                        dot+=scratch[2,head*D+c]*k
                    scores.append(rounded(dot,math.isqrt(D << 32)))
                es=[exp_integer(s-max(scores)) for s in scores]
                for c in range(D):
                    weighted=0
                    for t,e in enumerate(es):
                        v=get(10,l,0,t,kvhead*D+c)
                        weighted+=(v if v<2**31 else v-2**32)*e
                    write(5,head*D+c,bounded(rounded(weighted,sum(es))))
            capture(l,"context",5,H)
            linear(l,3,5,6)
            active_stage = ordinal,l,"residual_attention"
            for c in range(H):
                write(7,c,bounded(scratch[0,c]+scratch[6,c]))
            capture(l,"residual_attention",7,H)
            norm(l,7,8,6)
            linear(l,4,8,9)
            linear(l,5,8,10)
            silus = []
            for c in range(I):
                x=scratch[9,c]
                e=exp_integer(-abs(x))
                sigmoid=((1 << 48) if x>=0 else e*(1 << 24))//((1 << 24)+e)
                active_stage = ordinal,l,"silu"
                silu=bounded(rounded(x*sigmoid,1 << 24))
                silus.append(silu)
                active_stage = ordinal,l,"product"
                write(11,c,bounded(rounded(silu*scratch[10,c],65536)))
            capture(l,"silu",values=silus)
            capture(l,"product",11,I)
            linear(l,6,11,12)
            active_stage = ordinal,l,"residual_mlp"
            for c in range(H):
                write(0,c,bounded(scratch[7,c]+scratch[12,c]))
            capture(l,"residual_mlp",0,H)
        norm(0,0,14,7)
        final_vectors.append(vector(14,H))
        for r in range(V):
            logits.append(sat(rounded(sum(scratch[14,c]*fixed(0,0,0,r,c)
                                          for c in range(H)),65536)))
    float_final,float_logits = floating_stack(
        memory,get,fixed,dims,MATRIX[label],
        [((seed+n)%V,pos) for n,pos in enumerate(positions)],
        trace=float_trace if audit else None)
    final_error = max(abs(a/256-b*256) for actual,reference in zip(final_vectors,float_final)
                      for a,b in zip(actual,reference))
    logit_error = max(abs(a/65536-b) for a,b in zip(logits,float_logits))
    final_quality = all(abs(a/65536-b)<=16/256 for actual,reference in zip(final_vectors,float_final)
                        for a,b in zip(actual,reference))
    logit_quality = all(abs(a/65536-b)<=16/256+0.01*abs(b)
                        for a,b in zip(logits,float_logits))
    violations = [dict(index=n,integer_logit=a/65536,floating_logit=b,
                       absolute_error=abs(a/65536-b),limit=16/256+0.01*abs(b))
                  for n,(a,b) in enumerate(zip(logits,float_logits))
                  if abs(a/65536-b)>16/256+0.01*abs(b)]
    run.result(f"oracle-quality-{label}-{seed}",outcome="prediction",
               observed_rtl=False,final_max_error_q8_lsb=final_error,
               logit_max_absolute_error=logit_error,
               final_quality=final_quality,logit_quality=logit_quality,
               violating_logits=violations)
    prefix=name or f"matrix-{label}-{seed}"
    memfile=run.out/(prefix+"-memory.hex")
    memfile.write_text("\n".join(f"@{a:x} {v:08x}" for a,v in sorted(initial.items()))+"\n")
    expectedfile=run.out/(prefix+"-writes.hex")
    expectedfile.write_text("\n".join(f"{kind:x}{l:08x}{r:08x}{c:08x}{v:08x}"
                                     for kind,l,r,c,v in expected_writes)+"\n")
    logitfile=run.out/(prefix+"-logits.hex")
    logitfile.write_text("\n".join(f"{v&0xffffffff:08x}" for v in logits)+"\n")
    if audit:
        numerical_audit(run,label,seed,get,fixed,dims,positions,integer_trace,
                        float_trace,saturation,violations,logits,
                        (memfile,expectedfile,logitfile))
        return
    addr_expr = [
        "row*H+col","((layer*7+proj)*I+row)*(I/8)+col",
        "((layer*7+proj)*(I/G)+row)*(I/8)+col",
        "((layer*7+proj)*(I/G)+row)*I+col","(layer*3+proj)*H+col",
        "layer*H+col","layer*H+col","col","row*I+col",
        "(layer*S+row)*KV+col","(layer*S+row)*KV+col","row*D+col"]
    cases="\n".join(f"{kind}: addr={offsets[kind]}+{expr};" for kind,expr in enumerate(addr_expr))
    params=",".join(f".{k}({v})" for k,v in zip(KEYS,MATRIX[label]))
    # Reuse the independently checked memory transactor, replacing only its
    # command endpoint with the top's documented token and logit interface.
    instance=f"""
reg new_sequence=1; wire logit_valid; reg logit_ready=0;
wire [31:0] logit_index; wire signed [31:0] logit_data;
integer observed_logits=0, ordinal=0, output_stalls=0, residual_vectors=0;
integer progress_kind=0, progress_slot=0, progress_layer=0, progress_token=0;
integer active_gemv_proj=-1, active_gemv_layer=0;
integer gemv_reads=0, gemv_zeros=0, gemv_scales=0, gemv_weights=0;
integer gemv_inputs=0,gemv_outputs=0,gemv_biases=0,gemv_groups=0,gemv_tiles=0;
reg was_logit_stalled=0; reg [63:0] held_logit;
reg [31:0] expected_logits[0:{len(logits)-1}];
initial $readmemh("{logitfile}",expected_logits);
anvil_q1_top #({params}) dut(
"""+BUS_CONNECT.replace(".cmd_valid(cmd_valid),.cmd_ready(cmd_ready)",".token_valid(cmd_valid),.token_ready(cmd_ready)").replace(
        ".cmd_layer(cmd_layer),.cmd_pos(cmd_pos)",".token_id(cmd_layer),.token_pos(cmd_pos)")+"""
,.new_sequence(new_sequence),.logit_valid(logit_valid),.logit_ready(logit_ready),
.logit_index(logit_index),.logit_data(logit_data));
always @(negedge clk) logit_ready=rst_n && cycles%5!=0;
always @(posedge clk) if(rst_n) begin
 if(was_logit_stalled && {logit_valid,logit_index,logit_data} !== {1'b1,held_logit})
   $fatal(1,"LOGIT stall instability");
 was_logit_stalled=logit_valid && !logit_ready;
 held_logit={logit_index,logit_data};
 if(was_logit_stalled) output_stalls=output_stalls+1;
 if(logit_valid && logit_ready) begin
   if(logit_index !== observed_logits%"""+str(V)+""" ||
      logit_data !== expected_logits[observed_logits])
     $fatal(1,"LOGIT mismatch index %0d expected %h got %h",
       observed_logits,expected_logits[observed_logits],logit_data);
   observed_logits=observed_logits+1;
 end
end
"""
    reader=f"""
localparam H={H},I={I},G={G},S={S},KV={kv},D={D};
reg [31:0] storage[0:{sum(sizes)-1}];
reg [131:0] expected[0:{len(expected_writes)-1}];
initial begin $readmemh("{memfile}",storage); $readmemh("{expectedfile}",expected); end
function automatic integer addr(input [3:0] kind,input [31:0] layer,
 input [2:0] proj,input [31:0] row,col);
integer ni,no;
begin
 ni=(proj==6 ? I : H);
 no=(proj==1 || proj==2 ? KV : (proj==4 || proj==5 ? I : H));
 if(kind>11 || layer>={L}) $fatal(1,"ADDRESS kind/layer");
 if(kind==0 && (layer!=0 || proj!=0 || row>={V} || col>=H))
   $fatal(1,"ADDRESS embedding");
 if(kind>=1 && kind<=3 && (proj>6 ||
    row>=(kind==1 ? ni : ni/G) || col>=(kind==3 ? no : no/8)))
   $fatal(1,"ADDRESS AWQ");
 if(kind==4 && (proj>2 || row!=0 || col>=no))
   $fatal(1,"ADDRESS QKV bias");
 if(kind>=5 && kind<=7 && (proj!=0 || row!=0 || col>=H ||
    (kind==7 && layer!=0))) $fatal(1,"ADDRESS norm");
 if(kind==8 && (layer!=0 || proj!=0 || row>=15 || row==13 ||
    col>=((row==3 || row==4) ? KV : ((row>=9 && row<=11) ? I : H))))
   $fatal(1,"ADDRESS scratch");
 if((kind==9 || kind==10) && (proj!=0 || row>=S || col>=KV))
   $fatal(1,"ADDRESS cache");
 if(kind==11 && (layer!=0 || proj!=0 || row>=S || col>=D))
   $fatal(1,"ADDRESS RoPE");
 case(kind) {cases}
default: begin $fatal(1,"invalid kind"); addr=0; end
endcase end endfunction
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(kind==9 || kind==10) begin
   if(row>cmd_pos) $fatal(1,"CAUSAL future-cache read");
 end
 if(kind==4 && proj>=3) $fatal(1,"FORBIDDEN O/MLP bias");
 read_memory=storage[addr(kind,mem_req_layer,proj,row,col)];
 if(^read_memory === 1'bx) $fatal(1,"uninitialized/illegal memory read");
end endfunction
"""
    check=f"""
if(writes>={len(expected_writes)} ||
 {{mem_req_kind,mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata}} !== expected[writes])
 $fatal(1,"STACK write mismatch %0d kind %0d layer %0d row %0d col %0d got %h expected %h",
 writes,mem_req_kind,mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata,expected[writes]);
if(mem_req_kind<8 || mem_req_kind>10 || mem_req_proj!==0)
 $fatal(1,"illegal memory write");
storage[addr(mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col)]=mem_req_wdata;
"""
    commands="\n".join(f"cmd_layer={(seed+n)%V}; new_sequence={int(pos==0)}; launch(0,{pos});"
                        for n,pos in enumerate(positions))
    commands+=f"""
if(writes!={len(expected_writes)} || observed_logits!={len(logits)} ||
 completions!={len(positions)}) $fatal(1,"STACK coverage");
"""
    tb=command_tb(instance,reader,check,commands).replace(
        'if(mem_req_layer!==0) $fatal(1,"unexpected layer");',
        f'if(mem_req_layer>={L}) $fatal(1,"layer out of range");')
    tb=tb.replace("accepted=accepted+1; pending=1;", f"""
if(!mem_req_write && mem_req_wdata!==0) $fatal(1,"ADDRESS read wdata");
if(!mem_req_write && mem_req_kind==2) begin
 if(active_gemv_proj==-1) begin
   active_gemv_proj=mem_req_proj; active_gemv_layer=mem_req_layer;
   gemv_inputs=(mem_req_proj==6 ? {I} : {H});
   gemv_outputs=((mem_req_proj==1 || mem_req_proj==2) ? {kv} :
                  ((mem_req_proj==4 || mem_req_proj==5) ? {I} : {H}));
   gemv_groups=gemv_inputs/{G}; gemv_tiles=gemv_outputs/8;
   gemv_zeros=0; gemv_scales=0; gemv_weights=0; gemv_reads=0; gemv_biases=0;
 end
 if(mem_req_proj!==active_gemv_proj || mem_req_layer!==active_gemv_layer ||
    mem_req_row!==(gemv_zeros%gemv_groups) ||
    mem_req_col!==(gemv_zeros/gemv_groups))
   $fatal(1,"GEMV group/block metadata reload");
 gemv_zeros=gemv_zeros+1;
end
if(active_gemv_proj!=-1 && !mem_req_write) begin
 if(mem_req_kind==8) gemv_reads=gemv_reads+1;
 if(mem_req_kind==1) begin
   if(mem_req_row!==(gemv_weights%gemv_inputs) ||
      mem_req_col!==(gemv_weights/gemv_inputs))
     $fatal(1,"GEMV packed weight reuse/order");
   gemv_weights=gemv_weights+1;
 end
 if(mem_req_kind==3) begin
   if(mem_req_row!==((gemv_scales/8)%gemv_groups) ||
      mem_req_col!==((gemv_scales/(8*gemv_groups))*8+gemv_scales%8))
     $fatal(1,"GEMV scale metadata reload/order");
   gemv_scales=gemv_scales+1;
 end
 if(mem_req_kind==4) gemv_biases=gemv_biases+1;
end
accepted=accepted+1; pending=1;""")
    tb=tb.replace("accepted%262144==0","accepted%8192==0")
    tb=tb.replace("writes=writes+1; reply=0;",f"""
     if(mem_req_kind==8 &&
        (((mem_req_row==2 && active_gemv_proj==0) ||
          (mem_req_row==3 && active_gemv_proj==1) ||
          (mem_req_row==4 && active_gemv_proj==2) ||
          (mem_req_row==6 && active_gemv_proj==3) ||
          (mem_req_row==9 && active_gemv_proj==4) ||
          (mem_req_row==10 && active_gemv_proj==5) ||
          (mem_req_row==12 && active_gemv_proj==6)) &&
         mem_req_col==((mem_req_row==3 || mem_req_row==4) ? {kv-1} :
           ((mem_req_row==9 || mem_req_row==10) ? {I-1} : {H-1}))))
       begin
         progress_kind=1; progress_slot=mem_req_row;
         progress_layer=active_gemv_layer; progress_token=completions;
       end
     if(mem_req_kind==8 && mem_req_row==0 && mem_req_col=={H-1})
       begin
         if(residual_vectors%{L+1}==0)
           progress_kind=2;
         else
           progress_kind=3;
         progress_layer=residual_vectors%{L+1}-1; progress_token=completions;
       end
     writes=writes+1; reply=0;""")
    tb=tb.replace("completions=completions+1;",
                  'completions=completions+1;\n'
                  '$display("TOKEN completed=%0d accepted=%0d cycles=%0d",completions,accepted,cycles);')
    tb=tb.replace("pending=0; responses=responses+1;", """
   pending=0; responses=responses+1;
   if(progress_kind!=0) begin
     if(progress_kind==1) begin
       if(gemv_zeros!=gemv_tiles*gemv_groups ||
          gemv_scales!=8*gemv_tiles*gemv_groups ||
          gemv_weights!=gemv_tiles*gemv_inputs ||
          gemv_reads!=gemv_tiles*gemv_inputs ||
          gemv_biases!=(active_gemv_proj<3 ? gemv_outputs : 0))
         $fatal(1,"GEMV exact public transaction counts/reuse");
       $display("PROJECTION_ACK token=%0d layer=%0d slot=%0d accepted=%0d cycles=%0d",
         progress_token,progress_layer,progress_slot,accepted,cycles);
       active_gemv_proj=-1;
     end
     else if(progress_kind==2)
       $display("EMBEDDING_ACK token=%0d accepted=%0d cycles=%0d",
         progress_token,accepted,cycles);
     else
       $display("LAYER_ACK token=%0d layer=%0d accepted=%0d cycles=%0d",
         progress_token,progress_layer,accepted,cycles);
     if(progress_kind==2 || progress_kind==3) residual_vectors=residual_vectors+1;
     progress_kind=0;
     $fflush();
   end
""")
    if progress_seconds is not None:
        progress_probe(run,tb,prefix,sources,progress_seconds)
        return
    stdout=compile_sim(run,tb,prefix,sources=sources,timeout=25)
    run.result(prefix,configuration=MATRIX[label],seed=seed,tokens=len(positions),
               compared_writes=len(expected_writes),compared_logits=len(logits),
               floating_final_max_error_q8_lsb=final_error,
               floating_logit_max_absolute_error=logit_error,
               floating_final_quality=final_quality, floating_logit_quality=logit_quality,
               outcome="pass" if final_quality and logit_quality else "fail",stdout=stdout)
    require(final_quality,f"{label}/{seed}: floating layer-stack final activation exceeds 16 LSB")
    require(logit_quality,f"{label}/{seed}: floating layer-stack logit quality")


def rope_test(run):
    d, qh, kvh = 4, 4, 2
    positions = (1, 3, 32767)
    initial = {(slot, c): (-1 if c%2 else 1)*(31+17*c)*256
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
                                         y*math.sin(pos*1000000**(-2*pair/d)))) <= 512,
                            "floating RoPE quality")
                    mem[slot, a], mem[slot, b] = xx, yy
                    writes += [(slot, a, xx), (slot, b, yy)]
    expected = run.out / "rope-expected.hex"
    expected.write_text("\n".join(f"{slot:02x}{col:08x}{v&0xffffffff:08x}" for slot,col,v in writes)+"\n")
    init_lines = "\n".join(f"storage[{slot}][{col}]=32'h{v&0xffffffff:08x};"
                           for (slot,col),v in initial.items())
    coef_cases = "\n".join(f"64'h{pos:08x}{col:08x}:read_memory=32'h{v&0xffffffff:08x};"
                           for (pos,col),v in coefficients.items())
    reader = f"""
reg [31:0] storage[0:3][0:15]; reg [71:0] expected[0:{len(writes)-1}];
initial begin {init_lines} $readmemh("{expected}",expected); end
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(proj!=0) $fatal(1,"RoPE unused projection");
 if(kind==8 && (row==2 || row==3) && col<(row==2 ? 16:8))
   read_memory=storage[row][col];
 else if(kind==11) case({{row,col}})
 {coef_cases}
 default: begin $fatal(1,"RoPE coefficient address"); read_memory=0; end
 endcase
 else begin $fatal(1,"RoPE illegal address"); read_memory=0; end
end endfunction
"""
    check = f"""
if(writes>={len(writes)} || mem_req_kind!==8 ||
 {{mem_req_row[7:0],mem_req_col,mem_req_wdata}} !== expected[writes])
 $fatal(1,"ROPE write mismatch %0d got row %0d col %0d data %h",
 writes,mem_req_row,mem_req_col,mem_req_wdata);
storage[mem_req_row][mem_req_col]=mem_req_wdata;
"""
    params = "#(.NUM_LAYERS(1),.HIDDEN_SIZE(16),.NUM_Q_HEADS(4),.NUM_KV_HEADS(2),.HEAD_DIM(4),.MAX_SEQ_LEN(32768))"
    instance = "anvil_q1_rope "+params+" dut("+BUS_CONNECT+");"
    commands = "\n".join(f"launch(0,{p});" for p in positions)
    commands += f'\nif(writes!={len(writes)}) $fatal(1,"RoPE write coverage");'
    stdout = compile_sim(run, command_tb(instance,reader,check,commands), "rope")
    run.result("rope", positions=list(positions), theta=1000000,
               compared_writes=len(writes), floating_tolerance_q8_lsb=2,
               outcome="pass", stdout=stdout)


def protocol_test(run):
    """No model-service arithmetic: errors are injected at the first read."""
    params = ",".join(f".{k}({v})" for k,v in zip(KEYS,MATRIX["D"]))
    ports = BUS_PORTS
    connect = BUS_CONNECT.replace(
        ".cmd_valid(cmd_valid),.cmd_ready(cmd_ready)",
        ".token_valid(cmd_valid),.token_ready(cmd_ready)").replace(
        ".cmd_layer(cmd_layer),.cmd_pos(cmd_pos)",
        ".token_id(cmd_layer),.token_pos(cmd_pos)")
    text = "module tb;\n"+ports+"""
reg new_sequence=0; wire logit_valid; wire [31:0] logit_index;
wire signed [31:0] logit_data;
integer failures=0, aborts=0, cycle=0;
""" + f"anvil_q1_top #({params}) dut("+connect+"""
,.new_sequence(new_sequence),.logit_valid(logit_valid),.logit_ready(1'b0),
.logit_index(logit_index),.logit_data(logit_data));
task automatic zero_outputs;
begin
 if({cmd_ready,done,error,logit_valid,logit_index,logit_data,
     mem_req_valid,mem_rsp_ready,mem_req_write,mem_req_kind,mem_req_layer,
     mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata} !== 206'd0)
   $fatal(1,"RESET public output leakage");
end endtask
always @(posedge clk) begin
 cycle=cycle+1;
 if(cycle>1000) $fatal(1,"PROTOCOL watchdog");
 if(!rst_n) zero_outputs();
end
always @(negedge clk) if(!rst_n) zero_outputs();
task automatic accept(input [31:0] token,position,input ns);
begin
 @(negedge clk); if(cmd_ready!==1) $fatal(1,"not idle");
 cmd_layer=token; cmd_pos=position; new_sequence=ns; cmd_valid=1;
 @(posedge clk);
 if(mem_req_valid!==0 || mem_rsp_ready!==0)
   $fatal(1,"request accepted on E0");
 @(negedge clk); cmd_valid=0;
 if(cmd_ready!==0 || done!==0 || error!==0)
   $fatal(1,"post E0 busy contract");
end endtask
task automatic rejected(input [31:0] token,position,input ns);
begin
 accept(token,position,ns);
 while(done!==1) begin
   if(mem_req_valid!==0 || logit_valid!==0)
     $fatal(1,"INVALID token produced memory/logits");
   @(negedge clk);
 end
 if(error!==1 || cmd_ready!==0) $fatal(1,"INVALID completion");
 failures=failures+1;
 @(negedge clk);
 if(done!==0 || error!==0 || cmd_ready!==1)
   $fatal(1,"completion pulse/retire contract");
end endtask
task automatic wait_request;
begin
 while(mem_req_valid!==1) @(negedge clk);
 if(mem_req_write!==0 || mem_req_kind!==0 ||
    mem_req_layer!==0 || mem_req_proj!==0 || mem_req_row!==0 || mem_req_col!==0)
   $fatal(1,"first embedding request address");
end endtask
task automatic reset_now;
begin
 rst_n=0; #1; zero_outputs(); @(negedge clk);
 mem_rsp_valid=0; mem_rsp_error=0; mem_req_ready=0; rst_n=1;
 @(negedge clk); if(cmd_ready!==1) $fatal(1,"reset recovery");
 aborts=aborts+1;
end endtask
initial begin
 #0; #1; zero_outputs(); repeat(3) @(negedge clk); rst_n=1;
 rejected(1,0,0); rejected(0,1,0); rejected(0,1,1);
 // Invalid submissions must leave the initial committed position unchanged.
 accept(0,0,0); wait_request();
 repeat(3) begin
   @(negedge clk);
   if(mem_req_valid!==1 || mem_rsp_ready!==0)
     $fatal(1,"stalled request handshake");
 end
 reset_now();
 accept(0,0,1); wait_request(); mem_req_ready=1;
 @(negedge clk); mem_req_ready=0;
 if(mem_req_valid!==0 || mem_rsp_ready!==1)
   $fatal(1,"post R response phase");
 reset_now();
 accept(0,0,0); wait_request(); mem_req_ready=1;
 @(negedge clk); mem_req_ready=0;
 mem_rsp_rdata=0; mem_rsp_error=1; mem_rsp_valid=1;
 @(negedge clk); mem_rsp_valid=0; mem_rsp_error=0;
 while(done!==1) begin
   if(mem_req_valid!==0 || logit_valid!==0)
     $fatal(1,"ERROR generated subsequent traffic");
   @(negedge clk);
 end
 if(error!==1) $fatal(1,"memory error not reported");
 @(negedge clk);
 rejected(0,0,0);
 accept(0,0,1); wait_request(); reset_now();
 if(failures!=4 || aborts!=3) $fatal(1,"PROTOCOL coverage");
 $display("PASS protocol invalid=%0d reset_aborts=%0d memory_errors=1",failures,aborts);
 $finish;
end endmodule
"""
    stdout = compile_sim(run,text,"protocol")
    run.result("protocol", invalid_tokens=4, reset_during_request=2,
               reset_during_response=1, injected_memory_errors=1,
               outcome="pass", stdout=stdout)


def nonlinear_test(run):
    arguments = set(range(-16*65536,1,257))
    for n in range(24):
        boundary = rounded(n*11629080,256)
        arguments.update(-boundary+offset for offset in (-2,-1,0,1,2)
                         if -boundary+offset<=0)
    arguments.update((-16*65536-1,-16*65536,0))
    error = max(abs(exp_integer(x)/(1 << 24)-math.exp(x/65536))
                for x in arguments)
    require(error<=3e-5,"exponential floating maximum error")
    values = [x*256 for x in range(-4096,4097)]
    values.extend([0]*(8-len(values)%8))
    expected = []
    quality = []
    for x in values:
        e = exp_integer(-abs(x))
        sigmoid = ((1 << 48) if x>=0 else e*(1 << 24))//((1 << 24)+e)
        actual = sat(rounded(x*sigmoid,1 << 24))
        reference = x/(1+math.exp(-x/65536))
        quality.append(abs(actual-reference)/256)
        expected.append(actual & 0xffffffff)
    require(max(quality)<=2,"SiLU floating quality")
    expfile = run.out/"silu-expected.hex"
    expfile.write_text("\n".join(f"{x:08x}" for x in expected)+"\n")
    reader = f"""
reg [31:0] expected[0:{len(expected)-1}];
initial $readmemh("{expfile}",expected);
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(kind!=8 || proj!=0 || col>={len(values)} || (row!=9 && row!=10))
   $fatal(1,"SiLU address");
 if(row==10) read_memory=65536;
 else if(col<8193) read_memory=(col-4096)*256;
 else read_memory=0;
end endfunction
"""
    check = f"""
if(writes>={len(values)} || mem_req_kind!==8 || mem_req_proj!==0 ||
 mem_req_row!==11 || mem_req_col!==writes ||
 mem_req_wdata!==expected[writes])
 $fatal(1,"SILU public write mismatch %0d",writes);
"""
    instance = f"anvil_q1_elementwise #(.NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE({len(values)}),.MAX_SEQ_LEN(1)) dut("+BUS_CONNECT+",.cmd_mode(cmd_mode));"
    stdout = compile_sim(run,command_tb(instance,reader,check,
        f'cmd_mode=2; launch(0,0); if(writes!={len(values)}) $fatal(1,"SiLU coverage");'),
        "silu")
    run.result("silu_and_exponential_quality", public_silu_comparisons=len(values),
               silu_max_error_q8_lsb=max(quality), silu_threshold_q8_lsb=2,
               exponential_mathematical_comparisons=len(arguments),
               exponential_max_absolute_error=error,
               exponential_threshold=3e-5,
               exponential_scope="independent integer algorithm versus float, RTL observed via public SiLU",
               outcome="pass", stdout=stdout)
    attention_test(run)


def child_errors(run):
    """Invalid public commands and read-boundary failures, without hierarchy access."""
    common = dict(zip(KEYS, MATRIX["D"]))
    common.pop("VOCAB_SIZE")
    modules = ("w4a16_gemv", "rmsnorm", "rope", "gqa_attention",
               "swiglu_mlp", "decoder_layer", "elementwise")
    for module in modules:
        parameters = dict(common)
        if module == "rmsnorm":
            parameters = {k: common[k] for k in ("NUM_LAYERS","HIDDEN_SIZE","MAX_SEQ_LEN")}
        elif module == "elementwise":
            parameters = {k: common[k] for k in
                          ("NUM_LAYERS","HIDDEN_SIZE","INTERMEDIATE_SIZE","MAX_SEQ_LEN")}
        elif module in ("rope","gqa_attention"):
            parameters = {k: common[k] for k in
                          ("NUM_LAYERS","HIDDEN_SIZE","NUM_Q_HEADS",
                           "NUM_KV_HEADS","HEAD_DIM","MAX_SEQ_LEN")}
        extra = (",.cmd_proj(cmd_proj)" if module == "w4a16_gemv" else
                 ",.cmd_mode(cmd_mode)" if module in ("rmsnorm","elementwise") else "")
        params = ",".join(f".{k}({v})" for k,v in parameters.items())
        cases = [(1,0,0,0,-1,0), (0,1,0,0,-1,0)]
        if module == "w4a16_gemv":
            cases += [(0,0,7,0,-1,0)]
        if module in ("rmsnorm","elementwise"):
            cases += [(0,0,0,3,-1,0)]
        # -2 injects a memory-service fault at the first accepted request.
        cases += [(0,0,0,0,-2,0)]
        if module == "w4a16_gemv":
            cases += [(0,0,0,0,kind,raw) for kind,raw in
                      ((3,0x7c00),(3,0x7e00),(3,0xbc00),
                       (4,0xfc00),(4,0x7e00))]
        if module == "rmsnorm":
            cases += [(0,0,0,mode,kind,raw) for mode,kind in ((0,5),(1,6),(2,7))
                      for raw in (0x7c00,0x7e00)]
        if module == "swiglu_mlp":
            cases += [(0,0,0,0,3,0x7c00)]
        if module == "decoder_layer":
            cases += [(0,0,0,0,5,0x7e00),(0,0,0,0,4,0x7c00),
                      (0,0,0,0,3,0xbc00)]
        launches = "\n".join(
            f"check_error({l},{p},{proj},{mode},{kind},16'h{raw:04x});"
            for l,p,proj,mode,kind,raw in cases)
        text = "module tb;\n"+BUS_PORTS+f"""
anvil_q1_{module} #({params}) dut("""+BUS_CONNECT+extra+""");
integer cycles=0, checks=0, requests=0, replies=0, writes=0;
integer target=-1; reg [15:0] bad=0; reg pending=0, injected=0;
reg [31:0] reply;
always @(negedge clk) begin
 mem_req_ready=rst_n;
 mem_rsp_valid=rst_n && pending;
 mem_rsp_rdata=reply;
end
always @(posedge clk) if(rst_n) begin
 cycles=cycles+1; if(cycles>200000) $fatal(1,"CHILD watchdog");
 if(mem_req_valid && mem_req_ready) begin
   if(pending || injected || mem_rsp_ready) $fatal(1,"CHILD traffic after fault/overlap");
   if(target==-1) $fatal(1,"INVALID child command memory effect");
   requests=requests+1; pending=1;
   if(mem_req_write) writes=writes+1;
   reply=(mem_req_kind==8 ? 65536 :
          (mem_req_kind==1 ? 32'h99999999 :
           (mem_req_kind==2 ? 32'h88888888 :
            (mem_req_kind==4 ? 0 : 16'h3c00))));
   if(target==-2 || mem_req_kind==target) begin
     injected=1; reply={16'd0,bad}; mem_rsp_error=(target==-2);
   end
 end else if(mem_rsp_valid && mem_rsp_ready) begin
   if(!pending) $fatal(1,"CHILD unexpected response");
   pending=0; replies=replies+1;
 end
end
task automatic check_error(input integer l,p,proj,mode,kind,input [15:0] raw);
integer start_requests,start_writes;
begin
 @(negedge clk); if(cmd_ready!==1) $fatal(1,"CHILD not idle");
 start_requests=requests; start_writes=writes;
 target=kind; bad=raw; injected=0; mem_rsp_error=0;
 cmd_layer=l; cmd_pos=p; cmd_proj=proj; cmd_mode=mode; cmd_valid=1;
 @(negedge clk); cmd_valid=0;
 while(done!==1) @(negedge clk);
 if(error!==1 || cmd_ready!==0 || pending || (kind==-1 && writes!=start_writes))
   $fatal(1,"CHILD error propagation/no-write failure");
 if(kind!=-1 && (!injected || requests==start_requests))
   $fatal(1,"CHILD fault not reached");
 checks=checks+1;
 @(negedge clk);
 if(done!==0 || error!==0 || cmd_ready!==1) $fatal(1,"CHILD error retirement");
 mem_rsp_error=0;
end endtask
initial begin
 #1; if({cmd_ready,done,error,mem_req_valid,mem_rsp_ready}!==5'd0)
   $fatal(1,"CHILD reset");
 repeat(3) @(negedge clk); rst_n=1;
"""+launches+f"""
 if(checks!={len(cases)} || requests!=replies) $fatal(1,"CHILD coverage");
 $display("PASS child {module} errors=%0d requests=%0d",checks,requests);
 $finish;
end endmodule
"""
        stdout = compile_sim(run,text,"child-errors-"+module)
        run.result("child-errors-"+module,outcome="pass",cases=len(cases),stdout=stdout)


def top_errors(run):
    """Faults after acknowledged writes and after a genuinely transferred logit."""
    params = dict(zip(KEYS,MATRIX["D"])) | {"VOCAB_SIZE":2}
    declarations = ",".join(f".{k}({v})" for k,v in params.items())
    connect = BUS_CONNECT.replace(
        ".cmd_valid(cmd_valid),.cmd_ready(cmd_ready)",
        ".token_valid(cmd_valid),.token_ready(cmd_ready)").replace(
        ".cmd_layer(cmd_layer),.cmd_pos(cmd_pos)",
        ".token_id(cmd_layer),.token_pos(cmd_pos)")
    text = "module tb;\n"+BUS_PORTS+"""
reg new_sequence=1; wire logit_valid; reg logit_ready=1;
wire [31:0] logit_index; wire signed [31:0] logit_data;
integer cycles=0,scenario=0,checks=0,writes=0,acks=0,logits=0,requests=0,replies=0;
reg pending=0,injected=0,reply_error=0;
reg [31:0] reply=0; reg [31:0] scratch[0:119];
"""+f"anvil_q1_top #({declarations}) dut("+connect+"""
,.new_sequence(new_sequence),.logit_valid(logit_valid),.logit_ready(logit_ready),
.logit_index(logit_index),.logit_data(logit_data));
always @(negedge clk) begin
 mem_req_ready=rst_n; mem_rsp_valid=rst_n && pending;
 mem_rsp_error=reply_error; mem_rsp_rdata=reply;
end
always @(posedge clk) if(rst_n) begin
 cycles=cycles+1; if(cycles>100000) $fatal(1,"TOP fault watchdog");
 if(logit_valid && logit_ready) begin
   if((scenario!=2 && scenario!=9) || logits!=0 ||
      logit_index!==0 || logit_data!==524288)
     $fatal(1,"PARTIAL logit mismatch/scenario");
   logits=logits+1;
 end
 if(mem_req_valid && mem_req_ready) begin
   if(pending || injected || mem_rsp_ready) $fatal(1,"TOP post-fault/overlap traffic");
   pending=1; requests=requests+1; reply_error=0;
   if(mem_req_write) begin
     if(mem_req_kind!=8 && mem_req_kind!=9 && mem_req_kind!=10)
       $fatal(1,"TOP illegal write");
     writes=writes+1;
     if(mem_req_kind==8) scratch[mem_req_row*8+mem_req_col]=mem_req_wdata;
     reply=0;
   end else case(mem_req_kind)
     0,3,5,6,7: reply=16'h3c00;
     1,2,4,9,10: reply=0;
     8: reply=scratch[mem_req_row*8+mem_req_col];
     11: reply=mem_req_col%2==0 ? 32'h40000000 : 0;
     default: $fatal(1,"TOP unknown kind");
   endcase
   if((scenario==1 && acks>0) || (scenario==2 && logits==1)) begin
     injected=1; reply_error=1;
   end
   if(scenario==3 && mem_req_kind==0) begin
     injected=1; reply=16'h7c00;
   end
   if((scenario==4 && mem_req_kind==4) ||
      (scenario==5 && mem_req_kind==3) ||
      (scenario==6 && mem_req_kind==5) ||
      (scenario==7 && mem_req_kind==6) ||
      (scenario==8 && mem_req_kind==7) ||
      (scenario==9 && logits==1 && mem_req_kind==0)) begin
     injected=1; reply=(scenario==5 ? 16'hbc00 : 16'h7e00);
   end
 end else if(mem_rsp_valid && mem_rsp_ready) begin
   pending=0; replies=replies+1;
   if(writes>0) acks=writes;
 end
end
task automatic launch(input ns);
begin
 @(negedge clk); if(cmd_ready!==1) $fatal(1,"TOP not idle");
 cmd_valid=1; new_sequence=ns;
 @(negedge clk); cmd_valid=0;
end endtask
task automatic retire_error;
begin
 while(done!==1) @(negedge clk);
 if(error!==1 || cmd_ready!==0 || pending) $fatal(1,"TOP missing fault completion");
 @(negedge clk);
 if(done!==0 || error!==0 || cmd_ready!==1) $fatal(1,"TOP fault retirement");
end endtask
initial begin
 repeat(3) @(negedge clk); rst_n=1;
 for(scenario=1;scenario<=9;scenario=scenario+1) begin
   writes=0; acks=0; logits=0; injected=0;
   launch(1); retire_error();
   if(!injected || (scenario==1 && acks==0) ||
      ((scenario==2 || scenario==9) && logits!=1))
     $fatal(1,"TOP missing directed fault event");
   checks=checks+1;
   // A fault must invalidate the sequence even though token position is zero.
   launch(0); retire_error(); checks=checks+1;
 end
 if(checks!=18 || requests!=replies) $fatal(1,"TOP fault coverage");
 $display("PASS top errors after_write=1 partial_logit=2 nonfinite_boundaries=7 invalidated=9");
 $finish;
end endmodule
"""
    stdout = compile_sim(run,text,"top-errors")
    run.result("top-errors",outcome="pass",post_write_errors=1,
               partial_logit_errors=2,nonfinite_or_invalid_scale_boundaries=7,
               invalidated_sequence_rejections=9,stdout=stdout)


def attention_test(run):
    H,Q,K,D,S,pos = 112,14,2,8,4,2
    rng = random.Random(89)
    storage = {}
    def put(kind,row,col,value):
        storage[kind,row,col] = value
    for slot,n in ((2,H),(3,K*D),(4,K*D)):
        for c in range(n):
            put(8,slot,c,rng.randint(-500,500)*256)
    for kind in (9,10):
        for t in range(S):
            for c in range(K*D):
                put(kind,t,c,(30000 if t>pos else rng.randint(-600,600))*256)
    initial = dict(storage)
    writes = []
    for slot,kind in ((3,9),(4,10)):
        for c in range(K*D):
            value = storage[8,slot,c]
            put(kind,pos,c,value)
            writes.append((kind,pos,c,value & 0xffffffff))
    quality = []
    for head in range(Q):
        kh = head//7
        dots = [sum(storage[8,2,head*D+c]*storage[9,t,kh*D+c]
                    for c in range(D)) for t in range(pos+1)]
        scores = [rounded(dot,math.isqrt(D << 32)) for dot in dots]
        es = [exp_integer(score-max(scores)) for score in scores]
        f_scores = [dot/2**32/math.sqrt(D) for dot in dots]
        f_es = [math.exp(score-max(f_scores)) for score in f_scores]
        for c in range(D):
            actual = sat(rounded(sum(e*storage[10,t,kh*D+c]
                                    for t,e in enumerate(es)),sum(es)))
            reference = sum(e*storage[10,t,kh*D+c]
                            for t,e in enumerate(f_es))/sum(f_es)
            quality.append(abs(actual-reference)/256)
            writes.append((8,5,head*D+c,actual & 0xffffffff))
    require(max(quality)<=2,"standalone softmax attention floating quality")
    cases = "\n".join(f"72'h{((kind<<64)|(row<<32)|col):018x}:read_memory=32'h{value&0xffffffff:08x};"
                      for (kind,row,col),value in initial.items())
    expfile = run.out/"attention-expected.hex"
    expfile.write_text("\n".join(f"{kind:02x}{row:08x}{col:08x}{value:08x}"
                                for kind,row,col,value in writes)+"\n")
    reader = f"""
reg [103:0] expected[0:{len(writes)-1}];
reg [31:0] keys[0:15], vals[0:15];
initial $readmemh("{expfile}",expected);
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(proj!=0 || ((kind==9 || kind==10) && row>2))
   $fatal(1,"CAUSAL future-cache read or projection");
 if(kind==9 && row==2 && col<16) read_memory=keys[col];
 else if(kind==10 && row==2 && col<16) read_memory=vals[col];
 else case({{4'd0,kind,row,col}})
 {cases}
 default: begin $fatal(1,"attention illegal address"); read_memory=0; end
 endcase
end endfunction
"""
    check = f"""
if(writes>={len(writes)} || mem_req_proj!==0 ||
 {{4'd0,mem_req_kind,mem_req_row,mem_req_col,mem_req_wdata}} !== expected[writes])
 $fatal(1,"ATTENTION write mismatch %0d",writes);
if(mem_req_kind==9) keys[mem_req_col]=mem_req_wdata;
if(mem_req_kind==10) vals[mem_req_col]=mem_req_wdata;
"""
    instance = "anvil_q1_gqa_attention #(.NUM_LAYERS(1),.HIDDEN_SIZE(112),.NUM_Q_HEADS(14),.NUM_KV_HEADS(2),.HEAD_DIM(8),.MAX_SEQ_LEN(4)) dut("+BUS_CONNECT+");"
    stdout = compile_sim(run,command_tb(instance,reader,check,
        f'launch(0,2); if(writes!={len(writes)}) $fatal(1,"attention coverage");'),
        "attention")
    run.result("attention", q_to_kv_ratio=7, poisoned_future_position=3,
               compared_contexts=H, compared_cache_writes=K*D*2,
               floating_max_error_q8_lsb=max(quality),threshold_q8_lsb=2,
               outcome="pass",stdout=stdout)


def mutations(run):
    mutations = [
        ("lane","anvil_q1_awq_dequant.sv","1: shift=16;","1: shift=4;"),
        ("bias","anvil_q1_w4a16_gemv.sv",
         "accumulators[lane]<=accumulators[lane]+\n            ($signed({{96{bias_value[31]}},bias_value}) <<< 16);",
         "accumulators[lane]<=accumulators[lane];"),
        ("gqa","anvil_q1_gqa_attention.sv","(head/RATIO)*HEAD_DIM",
         "(head%NUM_KV_HEADS)*HEAD_DIM"),
        ("rope","anvil_q1_rope.sv",
         "((state==3 || state==11) ? HEAD_DIM/2 : 0)",
         "((state==3 || state==11) ? 1 : 0)"),
        ("cache","anvil_q1_gqa_attention.sv","row=time_index;",
         "row=time_index+1;"),
        ("layer","anvil_q1_top.sv","layer+1<NUM_LAYERS","1'b0"),
        ("dequant32","anvil_q1_awq_dequant.sv",
         "37'sd0 : product[36:0]","37'sd0 : $signed(product[31:0])"),
        ("accumulator64","anvil_q1_w4a16_gemv.sv",
         "reg signed [127:0] accumulators [0:7];","reg signed [63:0] accumulators [0:7];"),
        ("product53","anvil_q1_w4a16_gemv.sv",
         "accumulators[lane]+{{59{product[68]}},product}",
         "accumulators[lane]+{{75{product[52]}},product[52:0]}")]
    for name,filename,before,after in mutations:
        directory = run.out/("mutation-"+name)
        directory.mkdir()
        sources = []
        identity = {}
        for source in RTL:
            text = source.read_text()
            if source.name == filename:
                require(before in text,"mutation target not found "+name)
                text = text.replace(before,after)
            copied = directory/source.name
            copied.write_text(text)
            sources.append(copied)
            identity[source.name] = dict(
                original=hashlib.sha256(source.read_bytes()).hexdigest(),
                mutated=hashlib.sha256(copied.read_bytes()).hexdigest())
        if name in ("accumulator64","product53"):
            try:
                gemv_extremes(run,sources=sources,name="mutation-"+name,
                              small=name=="product53")
            except AssertionError as exc:
                diagnosis = str(exc)
            else:
                raise AssertionError("mutation survived "+name)
        elif name == "dequant32":
            # Independent widened public-port assertions already generated by
            # the unmutated dequant test; no low-32-bit comparison is permitted.
            tb = (run.out/"dequant.sv").read_text()
            try:
                compile_sim(run,tb,"mutation-"+name,sources=sources)
            except AssertionError as exc:
                diagnosis = str(exc)
            else:
                raise AssertionError("mutation survived "+name)
        else:
            try:
                integrated(run,"A",43,sources=sources,name="mutation-"+name)
            except AssertionError as exc:
                diagnosis = str(exc)
            else:
                raise AssertionError("mutation survived "+name)
        require("behavioral failure" in diagnosis and
                ("STACK write mismatch" in diagnosis or
                 "CAUSAL future-cache read" in diagnosis or
                 "AWQ case" in diagnosis or
                 "GEMV widened cancellation" in diagnosis),
                "mutation not killed by intended public behavioral assertion: "+diagnosis)
        run.result("mutation-"+name,outcome="functional_kill",
                   source_sha256=identity,assertion=diagnosis)


def portability(run, elaborate=True):
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
        run.result(f"compiler-{index}", executable=compiler,version=version.strip(),
                   outcome="discovered")
        if not elaborate:
            continue
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


def parameter_test(run):
    base = dict(zip(KEYS,MATRIX["D"]))
    cases = [(key+"-zero",{key:0}) for key in KEYS]
    cases += [("odd-head",{"HEAD_DIM":3}),
              ("head-mismatch",{"NUM_Q_HEADS":3}),
              ("gqa-ratio",{"HIDDEN_SIZE":24,"INTERMEDIATE_SIZE":24,
                            "NUM_Q_HEADS":6,"NUM_KV_HEADS":4}),
              ("group-remainder",{"GROUP_SIZE":3}),
              ("awq-width",{"AWQ_BITS":8}),
              ("cache-overflow",{"NUM_LAYERS":64,"MAX_SEQ_LEN":16777215}),
              ("embedding-overflow",{"VOCAB_SIZE":1073741824}),
              ("attention-bound",{"MAX_SEQ_LEN":16777216})]
    for name,changes in cases:
        values = base | changes
        params = ",".join(f".{key}({value})" for key,value in values.items())
        sv = run.out/(name+".sv")
        exe = run.out/(name+".vvp")
        sv.write_text("module tb; anvil_q1_top #("+params+") dut(); initial #1 $finish; endmodule\n")
        code,_,stderr = run.command(["iverilog","-g2012","-s","tb","-o",exe,*RTL,sv],
                                    name+"-compile",timeout=10)
        require(code==0,"illegal parameter diagnostics unreachable: "+name+" "+stderr)
        code,stdout,stderr = run.command(["vvp",exe],name+"-reject",timeout=5)
        require(code not in (0,None) and "PARAMETER ERROR" in stdout+stderr,
                "missing explicit illegal parameter rejection "+name)
        run.result("parameter-"+name,outcome="expected_rejection",overrides=changes)


def synthesis(run, configuration=None):
    for label, values in MATRIX.items():
        if configuration is not None and label != configuration:
            continue
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
    parser.add_argument("--probe", choices=("dequant","rope","gemv","official","rms","matrix","protocol","errors","mutations","nonlinear","parameters","toolchain","numerical-audit","progress"), default=None)
    parser.add_argument("--configuration", choices=tuple(MATRIX))
    parser.add_argument("--seed",type=int,default=17)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    valid_probes = {
        "behavior": {None,"dequant","rope","gemv","official","rms","matrix",
                     "protocol","errors","mutations","nonlinear","numerical-audit","progress"},
        "portability": {None,"parameters","toolchain"},
        "synthesis": {None}}
    if args.probe not in valid_probes[args.check]:
        parser.error("probe incompatible with check")
    run = Run(args.out, args.repair_of)
    try:
        for name in ("python3", "iverilog", "vvp", "yosys"):
            executable = shutil.which(name)
            if executable:
                run.command([executable, "-V" if name in ("iverilog","yosys","vvp") else "--version"],
                            name+"-version", timeout=5)
        if args.check == "behavior":
            slices = manifest(run)
            if args.probe == "numerical-audit":
                for seed in (17,89):
                    integrated(run,"B",seed,audit=True)
                require(all(r["final_quality"] and r["logit_quality"]
                            for r in run.results if r["name"].startswith("oracle-quality")),
                        "replacement equations fail retained B numerical quality witnesses")
            if args.probe == "progress":
                require(args.configuration=="B" and args.seed==17,
                        "bounded progress diagnostic is B17 only")
                integrated(run,"B",17,progress_seconds=12)
            if args.probe in (None, "dequant"):
                dequant_test(run, slices)
            if args.probe == "mutations":
                dequant_test(run,slices)
                mutations(run)
            if args.probe in (None, "rope"):
                rope_test(run)
            if args.probe in (None, "gemv"):
                gemv_extremes(run)
            if args.probe in (None, "official"):
                official_gemv(run,slices)
            if args.probe in (None, "rms"):
                rms_test(run)
            if args.probe in (None, "protocol"):
                protocol_test(run)
            if args.probe in (None, "errors"):
                child_errors(run)
                top_errors(run)
                conversion_test(run)
                elementwise_boundaries(run)
            if args.probe in (None, "nonlinear"):
                nonlinear_test(run)
            if args.probe=="matrix":
                require(args.configuration is not None,"matrix probe requires configuration")
                integrated(run,args.configuration,args.seed)
            elif args.probe is None:
                for label in MATRIX:
                    for seed in (17,43,89):
                        integrated(run,label,seed)
                mutations(run)
            if args.probe is None:
                run.result("acceptance_gaps",outcome="incomplete",
                           remaining=[
                               "complete seeded matrix with strengthened address/busy/bubble assertions",
                               "total mandatory execution within admitted 120-second budget"])
                raise AssertionError("INCOMPLETE: see acceptance_gaps; focused passes are not full acceptance")
        elif args.check == "synthesis":
            synthesis(run,args.configuration)
        else:
            if args.probe == "parameters":
                parameter_test(run)
            elif args.probe == "toolchain":
                portability(run,elaborate=False)
            else:
                parameter_test(run)
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
