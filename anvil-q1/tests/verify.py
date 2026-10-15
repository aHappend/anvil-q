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
import re
import resource
import selectors
import shutil
import signal
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
        self.out = Path(os.path.abspath(out))
        self.out.mkdir(parents=True, exist_ok=False)
        self.source_hashes = hashes()
        self.commands = []
        self.results = []
        self.started = utc()
        self.started_tick = time.monotonic()
        self.repair_of = repair_of

    def command(self, argv, name, timeout=20, observe_progress=False):
        argv = [str(x) for x in argv]
        start = utc()
        tick = time.monotonic()
        timed_out = False
        observation = None
        if observe_progress:
            code, stdout, stderr, timed_out, observation = self.observe_process(
                argv, timeout, tick)
        else:
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
        if observation is not None:
            observation_path = self.out / (name + "-host-observations.json")
            observation_path.write_text(json.dumps(observation, indent=2) + "\n")
            record["host_observations_path"] = str(observation_path.relative_to(ROOT))
            record["child_user_cpu_s"] = observation["child_user_cpu_s"]
            record["child_system_cpu_s"] = observation["child_system_cpu_s"]
            record["process_group_settled"] = observation["process_group_settled"]
        self.commands.append(record)
        self.save()
        return code, stdout.decode(errors="replace"), stderr.decode(errors="replace")

    def observe_process(self, argv, timeout, tick):
        """Diagnostic-only pipe observation; never drives simulation stimulus."""
        cpu_before = resource.getrusage(resource.RUSAGE_CHILDREN)
        clock_ticks = os.sysconf("SC_CLK_TCK")
        events, cpu_errors = [], []
        streams = {"stdout": bytearray(), "stderr": bytearray()}
        partial = {"stdout": b"", "stderr": b""}
        child_pids = set()

        def live_cpu(pid):
            user = system = 0
            try:
                children = Path(f"/proc/{pid}/task/{pid}/children").read_text().split()
                child_pids.update(int(child) for child in children)
                for process in (pid, *sorted(child_pids)):
                    fields = Path(f"/proc/{process}/stat").read_text().rsplit(")", 1)[1].split()
                    user += int(fields[11])
                    system += int(fields[12])
            except OSError as exc:
                cpu_errors.append(str(exc))
                return None, None
            return user / clock_ticks, system / clock_ticks

        timed_out = False
        with subprocess.Popen(argv, cwd=ROOT, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, start_new_session=True) as process:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ, "stdout")
                selector.register(process.stderr, selectors.EVENT_READ, "stderr")
                try:
                    while selector.get_map():
                        remaining = timeout - (time.monotonic() - tick)
                        if remaining <= 0:
                            timed_out = True
                            break
                        for key, _ in selector.select(min(remaining, 0.1)):
                            data = os.read(key.fileobj.fileno(), 65536)
                            if not data:
                                selector.unregister(key.fileobj)
                                continue
                            stream = key.data
                            streams[stream].extend(data)
                            partial[stream] += data
                            while b"\n" in partial[stream]:
                                line, partial[stream] = partial[stream].split(b"\n", 1)
                                text = line.decode(errors="replace")
                                if text.startswith(("PROGRESS ", "PROJECTION_ACK ",
                                                    "LAYER_ACK ", "EMBEDDING_ACK ", "TOKEN ",
                                                    "COST_START ", "COST_END ",
                                                    "COST_PHASE ")):
                                    now = time.monotonic()
                                    user, system = live_cpu(process.pid)
                                    events.append(dict(message=text, stream=stream,
                                        host_monotonic_s=now, elapsed_wall_s=now-tick,
                                        child_user_cpu_s=user, child_system_cpu_s=system,
                                        observation_work_s=time.monotonic()-now))
                    if not timed_out:
                        process.wait(timeout=max(0.001, timeout-(time.monotonic()-tick)))
                except subprocess.TimeoutExpired:
                    timed_out = True
                finally:
                    # The process group belongs only to this diagnostic invocation.
                    if process.poll() is None or timed_out:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    process.wait(timeout=1)
                    for key in list(selector.get_map().values()):
                        streams[key.data].extend(key.fileobj.read())
        cpu_after = resource.getrusage(resource.RUSAGE_CHILDREN)
        try:
            os.killpg(process.pid, 0)
            settled = False
        except ProcessLookupError:
            settled = True
        return (None if timed_out else process.returncode,
                bytes(streams["stdout"]), bytes(streams["stderr"]), timed_out,
                dict(start_monotonic_s=tick, events=events,
                     child_user_cpu_s=cpu_after.ru_utime-cpu_before.ru_utime,
                     child_system_cpu_s=cpu_after.ru_stime-cpu_before.ru_stime,
                     cpu_sample_resolution_s=1/clock_ticks,
                     cpu_sample_errors=cpu_errors, observed_child_pids=sorted(child_pids),
                     cpu_scope="timeout and its vvp child; final reaped child usage",
                     process_group_settled=settled))

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


def compile_sim(run, text, name, sources=None, timeout=3600, *,
                compiler="iverilog", compiler_args=(), runtime="vvp",
                settled=False):
    sv = run.out / (name+".sv")
    executable = run.out / (name+".vvp")
    sv.write_text(text)
    code, output, err = run.command(
        [compiler, *compiler_args, "-g2012", "-Wall", "-s", "tb", "-o", executable,
         *(sources or RTL), sv], name+"-compile", timeout,
        observe_progress=settled)
    if settled:
        require(run.commands[-1].get("process_group_settled") is True,
                f"{name}: compiler process group did not settle")
    require(code == 0 and not err.strip() and (not settled or not output.strip()),
            f"{name}: compile/warning failure: {output} {err}")
    code, stdout, stderr = run.command([runtime, executable], name+"-simulate", timeout,
                                       observe_progress=settled)
    if settled:
        require(run.commands[-1].get("process_group_settled") is True,
                f"{name}: runtime process group did not settle")
        require(not stderr.strip(), f"{name}: runtime warning/error: {stderr}")
    require(code == 0 and "PASS" in stdout,
            f"{name}: {'subprocess timeout' if code is None else 'behavioral failure'}: {stdout} {stderr}")
    if settled:
        run.result(name+"-artifacts", outcome="pass",
                   testbench=str(sv.relative_to(ROOT)),
                   testbench_sha256=hashlib.sha256(sv.read_bytes()).hexdigest(),
                   executable=str(executable.relative_to(ROOT)),
                   executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest())
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
    rms_boundaries(run)


def rms_boundaries(run):
    cases = [[0]*8, [1,-1,127,-127,128,-128,129,-129],
             [2**31-1,-2**31]*4, [2**31-1]+[0]*7]
    gammas = [0x3c00,0xbc00,0x7bff,0xfbff,0x0001,0x0080,0x8080,0x8000]
    rows = []
    for values in cases:
        reciprocal=(1<<64)//math.isqrt((sum(x*x for x in values)<<32)//8+18446744073710)
        for x,g in zip(values,gammas):
            expected=sat(rounded(x*sat(half_fixed(g))*reciprocal,1<<48))
            rows.append((x,g,expected))
    vector=run.out/"rms-boundaries.hex"
    vector.write_text("\n".join(f"{x&0xffffffff:08x}{g:04x}{v&0xffffffff:08x}"
                                 for x,g,v in rows)+"\n")
    reader=f"""
reg [79:0] vectors[0:31]; initial $readmemh("{vector}",vectors);
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(proj!=0 || row!=0 || col>=8 || (kind!=8 && kind!=5))
   $fatal(1,"RMS boundary address");
 read_memory=kind==8 ? vectors[completions*8+col][79:48] :
   {{16'd0,vectors[completions*8+col][47:32]}};
end endfunction
"""
    check="""
if(mem_req_kind!==8 || mem_req_row!==1 || mem_req_col!==(writes%8) ||
   mem_req_wdata!==vectors[writes][31:0])
 $fatal(1,"RMS widened sum/epsilon/rounding mismatch %0d",writes);
"""
    instance="anvil_q1_rmsnorm #(.NUM_LAYERS(1),.HIDDEN_SIZE(8),.MAX_SEQ_LEN(1)) dut("+BUS_CONNECT+",.cmd_mode(cmd_mode));"
    stdout=compile_sim(run,command_tb(instance,reader,check,
        'repeat(4) launch(0,0); if(writes!=32) $fatal(1,"RMS boundary coverage");'),
        "rms-boundaries")
    run.result("rms_boundaries",outcome="pass",compared=32,
               maximum_square_sum=max(sum(x*x for x in values) for values in cases),
               boundaries="zero denominator input with epsilon, sub-LSB input, signed32 extrema, saturation",
               stdout=stdout)


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
    code,stdout,stderr = run.command(
        ["timeout","--signal=INT","--kill-after=1s",str(seconds),
         "vvp","-n","-v",executable],
        prefix+"-progress",timeout=seconds+3,observe_progress=True)
    require(code in (0,124),"progress unexpected tool failure "+stdout+stderr)
    command = run.commands[-1]
    require(command["process_group_settled"],"progress child process group not settled")
    run.result("bounded-progress",outcome="measurement_not_acceptance",exit_code=code,
               budget_s=seconds,completed_simulation=code==0,
               full_B_gemv_products=573440,minimum_B_gemv_reads=183680,
               raw_stdout=str((run.out/(prefix+"-progress.stdout")).relative_to(ROOT)),
               raw_stderr=str((run.out/(prefix+"-progress.stderr")).relative_to(ROOT)))
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
    observation = json.loads((ROOT/command["host_observations_path"]).read_text())
    events = observation["events"]
    intervals, phases = [], []
    previous = dict(elapsed_wall_s=0,child_user_cpu_s=0,child_system_cpu_s=0,
                    accepted=0,cycles=0,message="simulation launch")
    phase_start = previous
    for event in events:
        event.update({key:int(value) for key,value in
                      re.findall(r"(\w+)=(\d+)",event["message"])})

        def interval(start, end):
            wall = end["elapsed_wall_s"]-start["elapsed_wall_s"]
            user = (None if end["child_user_cpu_s"] is None or
                    start["child_user_cpu_s"] is None else
                    end["child_user_cpu_s"]-start["child_user_cpu_s"])
            system = (None if end["child_system_cpu_s"] is None or
                      start["child_system_cpu_s"] is None else
                      end["child_system_cpu_s"]-start["child_system_cpu_s"])
            cpu = None if user is None or system is None else user+system
            return dict(start=start["message"],end=end["message"],wall_s=wall,
                child_user_cpu_s=user,child_system_cpu_s=system,
                cpu_to_wall_ratio=None if cpu is None else cpu/wall,
                cycles=end["cycles"]-start["cycles"],
                transactions=end["accepted"]-start["accepted"])

        intervals.append(interval(previous,event))
        if not event["message"].startswith("PROGRESS "):
            phases.append(interval(phase_start,event))
            phase_start = event
        previous = event
    cpu = command["child_user_cpu_s"]+command["child_system_cpu_s"]
    ratio = cpu/elapsed
    scheduler = {}
    for key,pattern in (
        ("time_steps",r"(\d+) time steps"),
        ("thread_schedule_events",r"(\d+) thread schedule events"),
        ("assign_events",r"(\d+) assign events"),
        ("other_events",r"(\d+) other events")):
        match = re.search(pattern,stdout+stderr)
        require(match is not None,"missing vvp scheduler statistic "+key)
        scheduler[key] = int(match.group(1))
    require(events and not observation["cpu_sample_errors"],
            "missing or failed public-message CPU observations")
    products = 4*2*(112*112*2+112*16*2+112*128*2+128*112)
    require(products==573440,"B workload arithmetic")
    report = dict(outcome="bounded_measurement_not_acceptance",
        samples=samples,projection_final_write_acknowledgements=acknowledgements,
        host_observations=command["host_observations_path"],
        public_message_intervals=intervals,completed_public_phase_intervals=phases,
        unfinished_phase_after=phase_start["message"],
        scheduler_statistics=scheduler,
        child_user_cpu_s=command["child_user_cpu_s"],
        child_system_cpu_s=command["child_system_cpu_s"],
        cpu_to_wall_ratio=ratio,
        cpu_diagnosis=("CPU-bound event processing; no substantial CPU deprivation observed"
                       if ratio>=0.9 else
                       "substantial non-CPU wall time observed; CPU deprivation versus "
                       "other waiting is not distinguished"),
        observed_public_transactions_at_least=observed,elapsed_wall_s=elapsed,
        observed_floor_transaction_rate_per_s=observed/elapsed,
        full_B_gemv_products=products,current_GEMV_input_metadata_reads_per_product=41/128,
        full_B_GEMV_read_transactions=183680,
        extrapolated_B_GEMV_read_only_s=183680/(observed/elapsed),
        extrapolation_is_not_a_completion_bound=True,
        unchanged_matrix_simulation_timeout_s=25,unchanged_aggregate_budget_s=120,
        diagnosis="Public request/response observations are retained with exact arithmetic "
        "comparisons and deterministic stalls. The current eight-output parallel tile "
        "analytically uses 183680 B input/metadata reads, excluding bias/output/other "
        "engines. Phase intervals span public acknowledgements, not internal states; "
        "the V-to-O interval includes RoPE/attention, O-to-gate includes residual/norm, "
        "and up-to-down includes SiLU/product. CPU samples have kernel tick resolution "
        "and host timestamps record pipe receipt, not exact simulator emission. "
        "This diagnostic does not establish full workload completion.",
        designer_handoff="Retain the Q16.16 contract, signed37 dequantization, signed69 "
        "products, signed128 accumulation, eight real parallel dequantizer/product lanes, "
        "direct GEMV handshake sequencing and all public comparisons. Measured phase "
        "costs inform independent recovery admission, not larger deadlines, reduced "
        "coverage or an unmeasured architectural repair.")
    (run.out/(prefix+"-execution-cost.json")).write_text(json.dumps(report,indent=2)+"\n")


def cost_discriminator(run, tb, instance, commands, params):
    """Advisory matched public-pin capture/replay, never an acceptance shortcut."""
    for relative in run.source_hashes:
        target = run.out / "source-snapshot" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    run.command(["timeout", "--version"], "timeout-version", timeout=2)
    trace_fields = ("mem_req_valid,mem_req_ready,mem_req_write,mem_req_kind,"
                    "mem_req_layer,mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata,"
                    "mem_rsp_valid,mem_rsp_ready,mem_rsp_rdata,mem_rsp_error")
    capture_trace = run.out / "capture-pins.hex"
    normalized = run.out / "capture-normalized.hex"
    declarations = f"""
integer cost_fd=0,cost_norm_fd=0,cost_start=-1,cost_i=0;
initial begin
 cost_fd=$fopen("{capture_trace}","w");
 cost_norm_fd=$fopen("{normalized}","w");
 if(!cost_fd || !cost_norm_fd) $fatal(1,"COST trace open");
end
"""
    capture = tb.replace("integer cycles=0", declarations+"\ninteger cycles=0", 1)
    start_hook = f"""
 if(cost_start<0 && mem_req_valid && mem_req_kind==2 &&
    mem_req_layer==0 && mem_req_proj==0 && completions==0) begin
   if(writes!=224 || pending) $fatal(1,"COST Q capture precondition");
   cost_start=cycles;
   for(cost_i=0;cost_i<112;cost_i=cost_i+1)
     $fdisplay(cost_norm_fd,"%08h",storage[addr(8,0,0,1,cost_i)]);
   $fclose(cost_norm_fd);
   $display("COST_START cycles=%0d accepted=%0d writes=%0d",cycles,accepted,writes);
   $fflush();
 end
 if(cost_start>=0) $fdisplay(cost_fd,"%044h",{{{trace_fields}}});
"""
    capture = capture.replace(' if(cycles>120000000)', start_hook+
                              '\n if(cycles>120000000)', 1)
    end_marker = "       active_gemv_proj=-1;"
    end_hook = """
       if(progress_token==0 && progress_layer==0 && progress_slot==2) begin
         if(writes!=336 || pending || accepted!=responses)
           $fatal(1,"COST final Q acknowledgement coverage");
         $display("COST_END cycles=%0d accepted=%0d writes=%0d",
           cycles,accepted,writes);
         $fclose(cost_fd); $fflush();
         $display("PASS diagnostic Q final write acknowledged"); $finish;
       end
"""
    require(capture.count(end_marker)==1, "COST capture hook ambiguity")
    capture = capture.replace(end_marker, end_hook+end_marker)

    def execute(text, name):
        sv, exe = run.out/(name+".sv"), run.out/(name+".vvp")
        sv.write_text(text)
        code, _, err = run.command(
            ["iverilog","-g2012","-Wall","-s","tb","-o",exe,*RTL,sv],
            name+"-compile", timeout=5)
        require(code==0 and not err.strip(), name+": compile/warning failure "+err)
        code, stdout, stderr = run.command(
            ["timeout","--signal=INT","--kill-after=1s","6",
             "vvp","-n",exe],name+"-simulate",timeout=9,observe_progress=True)
        record = run.commands[-1]
        require(record["process_group_settled"],name+": unsettled simulation")
        require(code==0 and "PASS diagnostic Q final write acknowledged" in stdout,
                name+": capture/replay failed or exceeded six-second cap: "+stdout+stderr)
        observation = json.loads((ROOT/record["host_observations_path"]).read_text())
        events = [e for e in observation["events"] if e["message"].startswith("COST_")]
        require(len(events)==2 and not observation["cpu_sample_errors"],
                name+": missing interval CPU observations")
        start,end = events
        values = [{k:int(v) for k,v in re.findall(r"(\w+)=(\d+)",e["message"])}
                  for e in events]
        wall = end["elapsed_wall_s"]-start["elapsed_wall_s"]
        cpu = sum(end[k]-start[k] for k in ("child_user_cpu_s","child_system_cpu_s"))
        result = dict(name=name,outcome="advisory_measurement",
            start=values[0],end=values[1],matched_wall_s=wall,matched_child_cpu_s=cpu,
            cycles=values[1]["cycles"]-values[0]["cycles"],
            transactions=values[1]["accepted"]-values[0]["accepted"],
            cpu_to_wall_ratio=cpu/wall,
            cpu_s_per_transaction=cpu/(values[1]["accepted"]-values[0]["accepted"]),
            total_child_user_cpu_s=record["child_user_cpu_s"],
            total_child_system_cpu_s=record["child_system_cpu_s"],
            total_wall_s=record["elapsed_s"],
            host_observations=record["host_observations_path"],
            caveat="Intervals use flushed pipe receipt and kernel CPU tick samples, "
                   "not exact simulator timestamps. Trace file I/O is included.")
        run.result(**result)
        return result

    captured = execute(capture, "cost-integrated")
    rows = capture_trace.read_text().splitlines()
    require(len(rows)==captured["cycles"]+1 and
            all(re.fullmatch("[0-9a-fA-F]{44}",r) for r in rows),
            "COST capture trace incomplete or contains X/Z")
    values = [int(r,16) for r in rows]
    # Low 35 bits are response {valid,ready,data,error}.
    require(sum((v>>172)&1 and (v>>171)&1 for v in values)==captured["transactions"],
            "COST captured request count")
    require(sum((v>>34)&1 and (v>>33)&1 for v in values)==captured["transactions"],
            "COST captured response count")
    require(captured["transactions"]==14*(224+9*7)+112+112,
            "COST Q exact transaction count")
    replay_trace = run.out / "replay-pins.hex"
    standalone_params = re.sub(r"\.VOCAB_SIZE\(\d+\),", "", params)
    replay_instance = instance.split("anvil_q1_top #",1)[0]+(
        f"anvil_q1_w4a16_gemv #({standalone_params}) dut("+BUS_CONNECT+
        ",.cmd_proj(cmd_proj));\n")
    replay = capture.replace(instance,replay_instance,1).replace(
        str(capture_trace),str(replay_trace)).replace(
        str(normalized),str(run.out/"replay-normalized.hex"))
    replay = replay.replace(commands, "cmd_layer=0; launch(0,0);",1)
    replay = replay.replace("integer cycles=0",
        f"""reg [172:0] cost_schedule[0:{len(rows)-1}];
integer cost_index=-1;
initial $readmemh("{capture_trace}",cost_schedule);
integer cycles=0""",1)
    # The original reader and all transaction/write assertions remain active.
    # Seed only previously observed/compared normalized scratch and counters.
    normalized_values = normalized.read_text().splitlines()
    require(len(normalized_values)==112,"COST normalized snapshot missing")
    replay = replay.replace(" #0; reset_check();",
        f""" #0; $readmemh("{normalized}",storage,
          addr(8,0,0,1,0),addr(8,0,0,1,111));
 writes=224; accepted={captured["start"]["accepted"]};
 responses={captured["start"]["accepted"]};
 reset_check();""",1)
    old_drive = """   mem_req_ready = cycles%31 != 0;
   mem_rsp_valid = pending && delay_count==0;
   mem_rsp_rdata = reply;"""
    new_drive = f"""
   if(cost_index>=0) cost_index=cost_index+1;
   else if(mem_req_valid) cost_index=0;
   if(cost_index>=0) begin
     if(cost_index>={len(rows)}) $fatal(1,"COST replay schedule exhausted");
     mem_req_ready=cost_schedule[cost_index][171];
     mem_rsp_valid=cost_schedule[cost_index][34];
     mem_rsp_rdata=cost_schedule[cost_index][32:1];
     mem_rsp_error=cost_schedule[cost_index][0];
   end
"""
    require(replay.count(old_drive)==1,"COST replay drive hook ambiguity")
    replay = replay.replace(old_drive,new_drive,1)
    replay = replay.replace(start_hook,start_hook+f"""
 if(cost_index>=0) begin
   if({{{trace_fields}}} !== cost_schedule[cost_index])
     $fatal(1,"COST replay complete public trace mismatch cycle %0d",cost_index);
   if(mem_rsp_valid && mem_rsp_rdata !== reply)
     $fatal(1,"COST replay response differs from independent memory service");
 end
""",1)
    replayed = execute(replay,"cost-standalone")
    require(replay_trace.read_bytes()==capture_trace.read_bytes(),
            "COST replay pin trace differs")
    require(captured["cycles"]==replayed["cycles"] and
            captured["transactions"]==replayed["transactions"],
            "COST mismatched measurement intervals")
    run.result("cost-discriminator",outcome="advisory_measurement_not_acceptance",
        identical_complete_pin_traces=True,compared_cycles=len(rows),
        compared_Q_writes=112,transactions=captured["transactions"],
        integrated_to_standalone_wall_ratio=(
            captured["matched_wall_s"]/replayed["matched_wall_s"]),
        integrated_to_standalone_cpu_ratio=(
            captured["matched_child_cpu_s"]/replayed["matched_child_cpu_s"]),
        scope="Distinguishes integrated hierarchy/routing overhead from cost "
              "present in standalone GEMV plus transactor; cannot separate "
              "GEMV arithmetic from transactor cost. Not four-token completion.")


def transactor_cost_discriminator(run):
    """Checker-cost measurement without DUT execution in one arm; not acceptance."""
    setup_tick = time.monotonic()
    prior = ROOT / "evidence/preparation/verifier-packed-request-cost-discriminator-02"
    require(run.repair_of == str((prior/"receipt.json").relative_to(ROOT)),
            "transactor measurement requires the admitted discriminator-02 link")
    previous = json.loads((prior/"receipt.json").read_text())
    for relative, digest in previous["source_sha256"].items():
        if relative.startswith(("rtl/", "design/", "hf_qwen25_05b_awq_spec/")):
            require(run.source_hashes[relative] == digest,
                    "retained product/source binding changed: "+relative)
    _transactor_cost_replay(run, prior, setup_tick)


def mac_qualified_cost_discriminator(run):
    """Current-source replay against immutable historical inputs; diagnostic only."""
    setup_tick = time.monotonic()
    current = ROOT / "evidence/preparation/verifier-mac-qualified-B17-01/receipt.json"
    prior = ROOT / "evidence/preparation/verifier-packed-request-cost-discriminator-02"
    historical = ROOT / "evidence/preparation/verifier-transactor-cost-discriminator-01/receipt.json"
    require(run.repair_of == str(current.relative_to(ROOT)),
            "current-source measurement requires the admitted mac-qualified B17 link")
    current_receipt = json.loads(current.read_text())
    product_prefixes = ("rtl/", "design/", "hf_qwen25_05b_awq_spec/")
    expected_sources = {p: d for p, d in current_receipt["source_sha256"].items()
                        if p.startswith(product_prefixes)}
    require({p: d for p, d in run.source_hashes.items()
             if p.startswith(product_prefixes)} == expected_sources,
            "current product/source binding differs from mac-qualified B17")
    historical_receipt = json.loads(historical.read_text())
    input_records = [r for r in historical_receipt["results"]
                     if r["name"] == "transactor-cost-inputs"]
    require(len(input_records) == 1, "historical retained input bindings missing")
    bindings = input_records[0]["retained_sha256"]
    for relative, digest in bindings.items():
        path = ROOT / relative
        require(path.parent == prior and
                hashlib.sha256(path.read_bytes()).hexdigest() == digest,
                "original capture/vector binding changed: "+relative)
    historical_arms = [r for r in historical_receipt["results"]
                       if r["name"] in ("cost-standalone", "cost-checker-only")]
    require(len(historical_arms) == 2 and
            all(r["complete_trace_identical"] and r["final_acknowledgement"]
                and r["compared_cycles"] == 10366 and r["transactions"] == 4242
                and r["compared_Q_writes"] == 112 for r in historical_arms),
            "historical matched-arm evidence incomplete")
    run.result("mac-qualified-cost-bindings", outcome="advisory_inputs_checked",
        linked_receipt_sha256={str(p.relative_to(ROOT)):
                              hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (current, prior/"receipt.json", historical)},
        retained_sha256=bindings,
        historical_observations=historical_arms,
        scope="Current RTL/documentation bound to failed B17 receipt; original "
              "capture and vectors bound to historical paired measurement.")
    results = _transactor_cost_replay(run, prior, setup_tick)
    run.result("mac-qualified-cost-comparison",
        outcome="advisory_measurement_not_acceptance",
        historical_observations=historical_arms, current_observations=results,
        caveat="Cross-run observations do not establish causality or an exact "
               "additive cost decomposition. Checker-only executes no DUT. "
               "Four-token B17 completion and engineering acceptance remain open.")


def standalone_phase_cost(run):
    """Implementation-only admitted diagnostic; execution needs separate admission."""
    setup_tick = time.monotonic()
    current = ROOT/"evidence/preparation/verifier-mac-qualified-integrated-cost-01/receipt.json"
    require(run.repair_of == str(current.relative_to(ROOT)),
            "phase measurement requires the admitted integrated-cost receipt")
    receipt = json.loads(current.read_text())
    require({p: d for p, d in run.source_hashes.items() if p != "tests/verify.py"} ==
            {p: d for p, d in receipt["source_sha256"].items()
             if p != "tests/verify.py"},
            "phase measurement permits only tests/verify.py to differ")
    lineage_path = ROOT/receipt["repair_of"]
    require(lineage_path == ROOT/
            "evidence/preparation/verifier-mac-qualified-cost-discriminator-01/receipt.json",
            "unexpected integrated-cost lineage")
    lineage = json.loads(lineage_path.read_text())
    records = [r for r in lineage["results"]
               if r["name"] == "mac-qualified-cost-bindings"]
    require(len(records) == 1, "phase historical lineage bindings missing")
    binding = records[0]
    for relative, digest in binding["linked_receipt_sha256"].items():
        require(hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() == digest,
                "phase linked historical receipt changed: "+relative)
    input_records = [r for r in lineage["results"]
                     if r["name"] == "transactor-cost-inputs"]
    require(len(input_records) == 1 and
            input_records[0]["retained_sha256"] == binding["retained_sha256"],
            "phase historical input bindings disagree")
    origins = binding["retained_sha256"]
    parents = {Path(p).parent for p in origins}
    require(len(parents) == 1, "ambiguous retained input origin")
    prior = ROOT/next(iter(parents))
    require(prior == ROOT/
            "evidence/preparation/verifier-packed-request-cost-discriminator-02",
            "unexpected original input lineage")
    for relative, digest in origins.items():
        require(hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() == digest,
                "phase retained input changed: "+relative)
    historical_path = (ROOT/
        "evidence/preparation/verifier-transactor-cost-discriminator-01/receipt.json")
    require(str(historical_path.relative_to(ROOT)) in
            binding["linked_receipt_sha256"], "historical pair is not linked")
    historical = json.loads(historical_path.read_text())
    arms = [r for r in historical["results"]
            if r["name"] in ("cost-standalone", "cost-checker-only")]
    require(len(arms) == 2 and all(
        r["complete_trace_identical"] and r["final_acknowledgement"] and
        r["compared_cycles"] == 10366 and r["transactions"] == 4242 and
        r["compared_Q_writes"] == 112 for r in arms),
        "phase historical complete-arm guards failed")
    historical_inputs = [r for r in historical["results"]
                         if r["name"] == "transactor-cost-inputs"]
    require(len(historical_inputs) == 1 and
            historical_inputs[0]["retained_sha256"] == origins,
            "phase original historical binding changed")
    for name in ("capture-pins.hex", "capture-normalized.hex",
                 "matrix-B-17-memory.hex", "matrix-B-17-writes.hex",
                 "matrix-B-17-logits.hex"):
        require((current.parent/name).read_bytes() == (prior/name).read_bytes(),
                "integrated receipt input differs from original lineage: "+name)
    for source, digest in receipt["source_sha256"].items():
        require(hashlib.sha256(
            (current.parent/"source-snapshot"/source).read_bytes()).hexdigest() == digest,
            "integrated source snapshot changed: "+source)
    plan = _public_phase_partition(prior/"capture-pins.hex")
    run.result("standalone-phase-cost-bindings", outcome="advisory_inputs_checked",
        linked_receipt_sha256={
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (current, lineage_path)},
        retained_sha256=origins, phase_partition=plan,
        outer_budget_s=60, outer_budget_owner="shared runtime; separate admission required",
        scope="No new stimulus, oracle output, integrated capture or acceptance claim.")
    results = _transactor_cost_replay(run, prior, setup_tick, phase_plan=plan)
    comparisons = []
    for category in ("metadata", "input-product-accumulation", "bias-output-ack"):
        pair = [r["phase_totals"][category] for r in results]
        wall = pair[0]["wall_s"]-pair[1]["wall_s"]
        cpu = pair[0]["child_cpu_s"]-pair[1]["child_cpu_s"]
        comparisons.append(dict(phase=category, observed_wall_difference_s=wall,
            observed_cpu_difference_s=cpu, attribution="inconclusive",
            reason="Pipe buffering, tick quantization and uncalibrated instrumentation "
                   "prevent expression-level or exact additive attribution."))
    invocation_wall = time.monotonic()-run.started_tick
    command_wall = sum(r["elapsed_s"] for r in run.commands)
    run.result("standalone-phase-cost", outcome="advisory_measurement_not_acceptance",
        comparisons=comparisons, preparation_through_pair_wall_s=time.monotonic()-setup_tick,
        invocation_through_pair_wall_s=invocation_wall,
        recorded_command_wall_s=command_wall,
        outside_commands_wall_s=invocation_wall-command_wall,
        outside_commands_scope="Binding, source snapshots, phase derivation, retained "
            "input copies, harness generation, postprocessing and receipt I/O; "
            "not simulator arithmetic. Final receipt serialization/interpreter exit "
            "are outside this timestamp and owned by the shared runtime.",
        scope="Exactly one standalone/checker-only pair; no concrete RTL-expression "
              "hypothesis established by scheduling-region differences alone.")


def _public_phase_partition(path):
    """Partition public scheduling regions, never infer DUT states or arithmetic."""
    rows = path.read_text().splitlines()
    require(len(rows) == 10366 and
            all(re.fullmatch("[0-9a-fA-F]{44}", row) for row in rows),
            "phase public trace missing/XZ")
    values = [int(row, 16) for row in rows]
    requests, responses, pending = [], [], None
    for index, value in enumerate(values):
        if value >> 172 & 1 and value >> 171 & 1:
            require(pending is None, "phase multiple outstanding requests")
            request = dict(index=index, write=(value >> 170) & 1,
                kind=(value >> 166) & 15, layer=(value >> 134) & 0xffffffff,
                proj=(value >> 131) & 7, row=(value >> 99) & 0xffffffff,
                col=(value >> 67) & 0xffffffff)
            requests.append(request)
            pending = request
        if value >> 34 & 1 and value >> 33 & 1:
            require(pending is not None and pending["index"] < index,
                    "phase response not strictly later")
            pending["response_index"] = index
            responses.append(index)
            pending = None
    require(pending is None and len(requests) == len(responses) == 4242 and
            responses[-1] == 10365, "phase transaction/final acknowledgement coverage")
    cursor, spans = 0, []

    def consume(kind, row, col, write=0):
        nonlocal cursor
        require(cursor < len(requests), "phase expected transaction missing")
        request = requests[cursor]
        require((request["kind"], request["row"], request["col"], request["write"],
                 request["layer"], request["proj"]) == (kind, row, col, write, 0, 0),
                "phase unexpected public transaction ordering/address")
        cursor += 1
        return request

    def appearance(request):
        index = request["index"]
        # Include the full valid-but-not-ready prefix of this same transaction.
        while index > 0 and values[index-1] >> 172 & 1:
            require(not (values[index-1] >> 171 & 1) and
                    (values[index-1] >> 35) & ((1 << 136)-1) ==
                    (values[request["index"]] >> 35) & ((1 << 136)-1),
                    "phase stalled boundary changed payload")
            index -= 1
        return index

    for tile in range(14):
        for group in range(7):
            zero = consume(2, group, tile)
            spans.append(dict(start=appearance(zero), category="metadata",
                              tile=tile, group=group))
            for lane in range(8):
                consume(3, group, tile*8+lane)
            first_input = None
            for k in range(group*16, (group+1)*16):
                activation = consume(8, 1, k)
                if first_input is None:
                    first_input = activation
                consume(1, k, tile)
            spans.append(dict(start=appearance(first_input),
                category="input-product-accumulation", tile=tile, group=group))
        bias = consume(4, 0, tile*8)
        spans.append(dict(start=appearance(bias), category="bias-output-ack",
                          tile=tile, group=None))
        for lane in range(1, 8):
            consume(4, 0, tile*8+lane)
        for lane in range(8):
            consume(8, 2, tile*8+lane, write=1)
    require(cursor == len(requests) and spans[0]["start"] == 0,
            "phase exhaustive public request coverage")
    boundaries = [s["start"] for s in spans]+[10365]
    require(all(a < b for a, b in zip(boundaries, boundaries[1:])),
            "phase boundaries not strictly increasing")
    for ordinal, span in enumerate(spans):
        start, end = boundaries[ordinal:ordinal+2]
        span.update(id=ordinal, end=end, elapsed_edges=end-start,
            transactions=sum(start <= r["index"] < end for r in requests),
            responses=sum(start <= i < end or
                          (ordinal == len(spans)-1 and i == end) for i in responses))
    require(sum(s["elapsed_edges"] for s in spans) == 10365 and
            sum(s["transactions"] for s in spans) == 4242 and
            sum(s["responses"] for s in spans) == 4242,
            "phase edge/transaction partition has gap or double count")
    return dict(spans=spans, boundaries=boundaries, elapsed_edges=10365,
        endpoint_inclusive_samples=10366, transactions=4242, responses=4242,
        convention="Edge i is the interval from public sample i to i+1. Spans own "
            "half-open elapsed-edge indices [start,end); transactions at a boundary "
            "sample belong to the following span. Sole exception: final endpoint "
            "response at sample 10365 belongs to the last span, without another edge. "
            "All samples remain compared, including both endpoints. Markers precede "
            "sample service/comparison at each boundary; final endpoint validation "
            "therefore occurs outside measured edges. Stalls, response waits and "
            "intervening gaps belong to the current span until the next public "
            "request's first valid appearance. Input regions include observable "
            "packed-weight-to-next-request gaps, not inferred internal MAC states.")


def _instrument_public_phases(template, plan):
    boundaries = plan["boundaries"]
    declarations = (
        f"integer cost_boundary[0:{len(boundaries)-1}];\n"
        "integer cost_boundary_next=0;\ninitial begin\n"+
        "\n".join(f" cost_boundary[{i}]={edge};"
                  for i, edge in enumerate(boundaries))+"\nend\n")
    require(template.count("integer cycles=0") == 1,
            "phase declaration hook ambiguity")
    template = template.replace("integer cycles=0",
                                declarations+"integer cycles=0", 1)
    hook = " if(cost_start>=0) $fdisplay(cost_fd"
    require(template.count(hook) == 1, "phase boundary hook ambiguity")
    marker = f"""
 if(cost_index>=0 && cost_boundary_next<{len(boundaries)}) begin
   if(cost_index==cost_boundary[cost_boundary_next]) begin
     $display("COST_PHASE boundary=%0d sample=%0d cycles=%0d accepted=%0d writes=%0d",
       cost_boundary_next,cost_index,cycles,accepted,writes);
     $fflush();
     cost_boundary_next=cost_boundary_next+1;
   end
 end
"""
    # Replace only diagnostic messages, retaining every assertion and service step.
    for label in ("COST_START", "COST_END", "PROGRESS", "PROJECTION_ACK",
                  "EMBEDDING_ACK", "LAYER_ACK", "TOKEN"):
        pattern = r'\$display\("'+label+r' [^;]*;'
        template, count = re.subn(pattern, ";", template)
        require(count == 1, "phase diagnostic message hook ambiguity: "+label)
    final = '         $fclose(cost_fd); $fflush();'
    require(template.count(final) == 1, "phase final boundary hook ambiguity")
    template = template.replace(final,
        '         if(cost_index!=10365 || cycles-cost_start!=10365 ||\n'
        '            accepted!=4914 || responses!=4914 || writes!=336 || pending)\n'
        '           $fatal(1,"COST entire interval/count/final acknowledgement");\n'
        f'         if(cost_boundary_next!={len(boundaries)}) '
        '$fatal(1,"COST phase boundary coverage");\n'+final, 1)
    template = template.replace("$fflush();", ";")
    template = template.replace(hook, marker+hook, 1)
    return template


def _public_phase_observations(plan, events, observation, record):
    require(len(events) == len(plan["boundaries"]), "phase marker count")
    counts = []
    for ordinal, (event, edge) in enumerate(zip(events, plan["boundaries"])):
        fields = {k: int(v) for k, v in
                  re.findall(r"(\w+)=(\d+)", event["message"])}
        require(fields["boundary"] == ordinal and fields["sample"] == edge and
                fields["cycles"] == 7+edge and
                all(event[k] is not None for k in
                    ("child_user_cpu_s", "child_system_cpu_s")),
                "phase boundary identity/CPU observation missing")
        counts.append(fields)
    require(counts[0]["accepted"] == 672 and counts[-1]["accepted"] == 4914 and
            counts[0]["writes"] == 224 and counts[-1]["writes"] == 336,
            "phase marker endpoint accounting")
    phases, totals = [], {}
    for span, start, end, left, right in zip(
            plan["spans"], events, events[1:], counts, counts[1:]):
        wall = end["elapsed_wall_s"]-start["elapsed_wall_s"]
        cpu = sum(end[k]-start[k] for k in
                  ("child_user_cpu_s", "child_system_cpu_s"))
        require(wall >= 0 and cpu >= 0 and
                right["accepted"]-left["accepted"] == span["transactions"],
                "phase nonmonotonic observation/transaction ownership")
        measured = dict(span, wall_s=wall, child_cpu_s=cpu,
            attribution="inconclusive",
            resolution_limited=(cpu <= 2*observation["cpu_sample_resolution_s"]),
            observation_work_lower_bound_s=start["observation_work_s"],
            limitation="Timestamp at pipe receipt, followed by sampled child CPU; "
                       "simulator can advance while the observer handles a marker.")
        phases.append(measured)
        total = totals.setdefault(span["category"], dict(
            wall_s=0.0, child_cpu_s=0.0, elapsed_edges=0, transactions=0,
            responses=0, intervals=0, resolution_limited_intervals=0))
        for key in ("wall_s", "child_cpu_s", "elapsed_edges", "transactions", "responses"):
            total[key] += measured[key]
        total["intervals"] += 1
        total["resolution_limited_intervals"] += measured["resolution_limited"]
    wall = events[-1]["elapsed_wall_s"]-events[0]["elapsed_wall_s"]
    cpu = sum(events[-1][k]-events[0][k] for k in
              ("child_user_cpu_s", "child_system_cpu_s"))
    total_cpu = record["child_user_cpu_s"]+record["child_system_cpu_s"]
    before_cpu = events[0]["child_user_cpu_s"]+events[0]["child_system_cpu_s"]
    clock = time.get_clock_info("monotonic")
    return dict(phase_intervals=phases, phase_totals=totals,
        elapsed_edges=plan["elapsed_edges"], marker_count=len(events),
        boundary_ownership=plan["convention"],
        measurement_limits=dict(
            host_clock=clock.implementation, host_clock_resolution_s=clock.resolution,
            cpu_tick_resolution_s=observation["cpu_sample_resolution_s"],
            pipe_buffering="Simulator stdout is a pipe; $fflush at every boundary. "
                "OS buffering/read batching may deliver multiple markers together. "
                "Flushing does not synchronize the simulator and host sampler.",
            observation_work_lower_bound_s=sum(e["observation_work_s"] for e in events),
            instrumentation_overhead_s=None,
            overhead_limit="Only host marker parsing/CPU-sampling work after timestamp "
                "is timed; pipe reads, decoding, scheduling, simulator marker formatting, "
                "flush and boundary dispatch are not isolated. No calibration or "
                "overhead subtraction. Exact overhead and upper bound are unknown.",
            classification="Scheduling regions only; metadata includes dequant-related "
                "traffic, input regions include product/accumulation progression gaps, "
                "bias/output includes final-rounding-related traffic. None isolates "
                "an arithmetic expression or gives an additive causal decomposition."),
        outside_interval=dict(
            setup_wall_s=events[0]["elapsed_wall_s"], setup_child_cpu_s=before_cpu,
            post_interval_wall_s=record["elapsed_s"]-events[-1]["elapsed_wall_s"],
            post_interval_child_cpu_s=total_cpu-before_cpu-cpu,
            post_interval_scope="Final endpoint assertions, acknowledgement, finish, "
                "scheduler statistics, drain and process settlement.",
            matched_wall_s=wall, matched_child_cpu_s=cpu,
            unclassified_inside_wall_s=wall-sum(t["wall_s"] for t in totals.values()),
            unclassified_inside_child_cpu_s=cpu-sum(t["child_cpu_s"] for t in totals.values()),
            caveat="CPU scope is timeout plus child, with tick samples inside and "
                "reaped usage outside; residual differences can reflect quantization."))


def _transactor_cost_replay(run, prior, setup_tick, phase_plan=None):
    """Shared retained service, schedule, assertions and bounded paired execution."""
    for relative in run.source_hashes:
        target = run.out / "source-snapshot" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/relative, target)
    names = ("receipt.json", "cost-standalone.sv", "capture-pins.hex",
             "replay-pins.hex", "capture-normalized.hex", "replay-normalized.hex",
             "matrix-B-17-memory.hex", "matrix-B-17-writes.hex",
             "matrix-B-17-logits.hex")
    bindings = {}
    retained = run.out / "retained-inputs"
    retained.mkdir()
    for name in names:
        data = (prior/name).read_bytes()
        (retained/name).write_bytes(data)
        bindings[str((prior/name).relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
    require((retained/"capture-pins.hex").read_bytes() ==
            (retained/"replay-pins.hex").read_bytes(), "prior trace pair differs")
    require((retained/"capture-normalized.hex").read_bytes() ==
            (retained/"replay-normalized.hex").read_bytes(), "prior scratch pair differs")
    rows = (retained/"capture-pins.hex").read_text().splitlines()
    require(len(rows) == 10366 and
            all(re.fullmatch("[0-9a-fA-F]{44}", row) for row in rows),
            "retained complete trace missing/XZ")
    values = [int(row, 16) for row in rows]
    require(sum(bool(v >> 172 & 1) and bool(v >> 171 & 1) for v in values) == 4242
            and sum(bool(v >> 34 & 1) and bool(v >> 33 & 1) for v in values) == 4242,
            "retained transaction count")
    expected = [int(row, 16) for row in
                (retained/"matrix-B-17-writes.hex").read_text().splitlines()]
    normalized = [int(row, 16) for row in
                  (retained/"capture-normalized.hex").read_text().splitlines()]
    require(len(normalized) == 112 and
            expected[112:224] == [(8 << 128) | (1 << 64) | (c << 32) | value
                                  for c, value in enumerate(normalized)],
            "retained normalized snapshot differs from independent expected writes")
    write_rows = [v for v in values
                  if v >> 172 & 1 and v >> 171 & 1 and v >> 170 & 1]
    require(len(write_rows) == 112 and
            [(((v >> 166) & 15) << 128) |
             (((v >> 134) & 0xffffffff) << 96) |
             (((v >> 99) & 0xffffffff) << 64) |
             (((v >> 67) & 0xffffffff) << 32) |
             ((v >> 35) & 0xffffffff) for v in write_rows] ==
            [(8 << 128) | (2 << 64) | (c << 32) | (expected[224+c] & 0xffffffff)
             for c in range(112)],
            "retained ordered Q writes")
    require(values[-1] >> 34 & 1 and values[-1] >> 33 & 1,
            "retained interval lacks final response acknowledgement")
    template = (retained/"cost-standalone.sv").read_text()
    template = template.replace(str(prior), str(retained))
    # Both arms run the same service, not captured read results. Captured response
    # pins remain the comparison oracle, including idle data and stall timing.
    old_drive = """     mem_rsp_valid=cost_schedule[cost_index][34];
     mem_rsp_rdata=cost_schedule[cost_index][32:1];
     mem_rsp_error=cost_schedule[cost_index][0];"""
    new_drive = """     mem_rsp_valid=pending && delay_count==0;
     mem_rsp_rdata=reply;
     mem_rsp_error=0;"""
    require(template.count(old_drive) == 1, "response service hook ambiguity")
    template = template.replace(old_drive, new_drive)
    template = template.replace(" responses=672;",
        f" responses=672; reply=32'h{(values[0] >> 1) & 0xffffffff:08x};", 1)
    require("responses=672; reply=" in template, "initial service state hook missing")
    if phase_plan is not None:
        template = _instrument_public_phases(template, phase_plan)
    endpoint = re.search(r"anvil_q1_w4a16_gemv #\(.*?\.cmd_proj\(cmd_proj\)\);\n",
                         template, re.S)
    require(endpoint is not None, "standalone public endpoint missing")
    checker = template[:endpoint.start()] + template[endpoint.end():]
    checker_pins = """
reg checker_busy=0;
always @(posedge clk)
 if(!rst_n) checker_busy<=0;
 else if(cmd_valid && cmd_ready) checker_busy<=1;
assign cmd_ready=rst_n && !checker_busy;
assign done=1'b0;
assign error=1'b0;
assign {mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
        mem_req_row,mem_req_col,mem_req_wdata,mem_rsp_ready} =
 (rst_n && cost_index>=0) ?
 {cost_schedule[cost_index][172],cost_schedule[cost_index][170:35],
  cost_schedule[cost_index][33]} : 138'd0;
"""
    checker = checker.replace("integer cost_index=-1;",
                              "integer cost_index=-1;\n"+checker_pins, 1)
    checker = checker.replace("else if(mem_req_valid) cost_index=0;",
                              "else if(checker_busy) cost_index=0;", 1)
    require("anvil_q1_" not in checker, "checker-only arm unexpectedly contains RTL")
    run.result("transactor-cost-inputs", outcome="advisory_inputs_checked",
               retained_sha256=bindings, prior_receipt=run.repair_of,
               normalized_values_compared=112, ordered_Q_writes_checked=112,
               preparation_wall_s=time.monotonic()-setup_tick,
               scope="Retained independent vectors and public capture, not new inference")
    run.command(["timeout", "--version"], "timeout-version", timeout=2)
    results = []
    for name, text, sources in (("cost-standalone", template, RTL),
                                ("cost-checker-only", checker, [])):
        trace = run.out/(name+"-pins.hex")
        norm = run.out/(name+"-normalized.hex")
        text = text.replace(str(retained/"replay-pins.hex"), str(trace)).replace(
            str(retained/"replay-normalized.hex"), str(norm))
        # Check interval and final acknowledgement before the retained finish.
        text = text.replace('         $display("COST_END', """
         if(cost_index!=10365 || cycles-cost_start!=10365 ||
            accepted!=4914 || responses!=4914 || writes!=336 || pending)
           $fatal(1,"COST entire interval/count/final acknowledgement");
         $display("COST_END""", 1)
        sv, exe = run.out/(name+".sv"), run.out/(name+".vvp")
        sv.write_text(text)
        code, _, err = run.command(
            ["iverilog", "-g2012", "-Wall", "-s", "tb", "-o", exe, *sources, sv],
            name+"-compile", timeout=5)
        require(code == 0 and not err.strip(), name+": compile/warning failure "+err)
        compile_record = run.commands[-1]
        code, stdout, stderr = run.command(
            ["timeout", "--signal=INT", "--kill-after=1s", "6",
             "vvp", "-n", "-v", exe], name+"-simulate",
            timeout=9, observe_progress=True)
        record = run.commands[-1]
        require(record["process_group_settled"], name+": unsettled process group")
        require(code == 0 and "PASS diagnostic Q final write acknowledged" in stdout,
                name+": failed or exceeded six-second cap: "+stdout+stderr)
        require(trace.read_bytes() == (retained/"capture-pins.hex").read_bytes(),
                name+": complete trace mismatch")
        require(norm.read_bytes() == (retained/"capture-normalized.hex").read_bytes(),
                name+": normalized scratch mismatch")
        observation = json.loads((ROOT/record["host_observations_path"]).read_text())
        events = [e for e in observation["events"] if e["message"].startswith(
            "COST_PHASE " if phase_plan is not None else ("COST_START ", "COST_END "))]
        require(len(events) == (len(phase_plan["boundaries"]) if phase_plan else 2)
                and not observation["cpu_sample_errors"],
                name+": interval CPU observations missing")
        start, end = events[0], events[-1]
        wall = end["elapsed_wall_s"]-start["elapsed_wall_s"]
        cpu = sum(end[k]-start[k] for k in ("child_user_cpu_s", "child_system_cpu_s"))
        scheduler = {}
        for key, pattern in (
                ("time_steps", r"(\d+) time steps"),
                ("thread_schedule_events", r"(\d+) thread schedule events"),
                ("assign_events", r"(\d+) assign events"),
                ("other_events", r"(\d+) other events")):
            match = re.search(pattern, stdout+stderr)
            require(match is not None, name+": missing scheduler statistic "+key)
            scheduler[key] = int(match.group(1))
        result = dict(name=name, outcome="advisory_measurement_not_acceptance",
            executes_DUT=bool(sources), matched_wall_s=wall, matched_child_cpu_s=cpu,
            compared_cycles=10366, transactions=4242, compared_Q_writes=112,
            final_acknowledgement=True, complete_trace_identical=True,
            compile_wall_s=compile_record["elapsed_s"],
            simulator_setup_wall_s=start["elapsed_wall_s"],
            simulator_setup_child_cpu_s=start["child_user_cpu_s"]+start["child_system_cpu_s"],
            total_wall_s=record["elapsed_s"],
            total_child_cpu_s=record["child_user_cpu_s"]+record["child_system_cpu_s"],
            scheduler_statistics=scheduler,
            scheduler_scope="complete simulator invocation, including setup",
            host_observations=record["host_observations_path"])
        if phase_plan is not None:
            require(not re.search(r"\b(warning|error)\b", stderr, re.I),
                    name+": simulator warning/error "+stderr)
            result.update(_public_phase_observations(
                phase_plan, events, observation, record))
        run.result(**result)
        results.append(result)
    standalone, checker_only = results
    run.result("transactor-cost-discriminator", outcome="advisory_measurement_not_acceptance",
        standalone_to_checker_wall_ratio=standalone["matched_wall_s"]/checker_only["matched_wall_s"],
        standalone_to_checker_cpu_ratio=standalone["matched_child_cpu_s"]/checker_only["matched_child_cpu_s"],
        observed_wall_difference_s=standalone["matched_wall_s"]-checker_only["matched_wall_s"],
        observed_cpu_difference_s=standalone["matched_child_cpu_s"]-checker_only["matched_child_cpu_s"],
        caveat="Checker-only arm executes no DUT and establishes no accelerator functionality. "
               "Both arms include matching trace I/O, service and public assertions. "
               "Pipe receipt timestamps and kernel-tick CPU samples are approximate. "
               "Differences are not an exact additive decomposition or identification "
               "of an expensive expression. Four-token completion remains unestablished.")
    return results


def integrated(run, label, seed, sources=None, name=None, audit=False,
               progress_seconds=None, discriminate_cost=False):
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
    if discriminate_cost:
        cost_discriminator(run,tb,instance,commands,params)
        return
    if progress_seconds is not None:
        progress_probe(run,tb,prefix,sources,progress_seconds)
        return
    stdout=compile_sim(run,tb,prefix,sources=sources,timeout=3600)
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


def protocol_test(run, *, name="protocol", compiler="iverilog",
                  compiler_args=(), runtime="vvp", settled=False):
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
    stdout = compile_sim(run,text,name, compiler=compiler,
                         compiler_args=compiler_args, runtime=runtime, settled=settled)
    require("PASS protocol invalid=4 reset_aborts=3 memory_errors=1" in stdout,
            name+": missing protocol smoke coverage")
    run.result(name, invalid_tokens=4, reset_during_request=2,
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
    attention_boundaries(run)


def attention_boundaries(run):
    """Large exact dot/weighted reductions and wide max-subtraction clipping."""
    reader="""
integer test_case=0;
function automatic [31:0] read_memory(input [3:0] kind,input [2:0] proj,
 input [31:0] row,col);
begin
 if(proj!=0 || col>=8) $fatal(1,"ATTENTION wide component");
 if(kind==8) begin
   if(row==2) read_memory=test_case==0 ? 0 : 32'h7fffffff;
   else if(row==3) read_memory=32'h7fffffff;
   else if(row==4) read_memory=test_case==0 ? 32'h7fffffff : 32'd65536000;
   else begin $fatal(1,"ATTENTION wide scratch"); read_memory=0; end
 end else if((kind==9 || kind==10) && row<=256) begin
   if(kind==9) read_memory=test_case==0 || row%2==0 ?
     32'h7fffffff : -32'sd2147483647;
   else read_memory=test_case==0 ? 32'h7fffffff :
     (row%2==0 ? 32'd65536000 : -32'sd65536000);
 end else begin $fatal(1,"ATTENTION wide causal/address"); read_memory=0; end
end endfunction
"""
    check="""
expected_value=32'h7fffffff;
if(test_case==1 && mem_req_kind!=9) expected_value=65536000;
if(mem_req_col!==(writes%8) || mem_req_proj!==0 ||
   (writes%24<8 ? (mem_req_kind!==9 || mem_req_row!==256) :
    (writes%24<16 ? (mem_req_kind!==10 || mem_req_row!==256) :
     (mem_req_kind!==8 || mem_req_row!==5))) ||
   mem_req_wdata!==expected_value)
 $fatal(1,"ATTENTION widened dot/weighted reduction mismatch %0d",writes);
"""
    instance="anvil_q1_gqa_attention #(.NUM_LAYERS(1),.HIDDEN_SIZE(8),.NUM_Q_HEADS(2),.NUM_KV_HEADS(2),.HEAD_DIM(4),.MAX_SEQ_LEN(257)) dut("+BUS_CONNECT+");"
    stdout=compile_sim(run,command_tb(instance,reader,check,
        'launch(0,256); test_case=1; launch(0,256); if(writes!=48) $fatal(1,"wide attention coverage");'),
        "attention-boundaries")
    run.result("attention_boundaries",outcome="pass",compared_writes=48,
               uniform_weighted_sum=257*(2**31-1)*2**24,
               positive_dot=4*(2**31-1)**2,
               scope="exact extremes, uniform normalized softmax, huge positive/negative scores",
               stdout=stdout)


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
         "accumulators[i]+{{59{product[i][68]}},product[i]}",
         "accumulators[i]+{{75{product[i][52]}},product[i][52:0]}")]
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
                 *overrides,*RTL], f"elaborate-{index}-{label}", timeout=120)
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
                                           f"synthesis-{label}", timeout=600)
        require(code == 0, f"Yosys {label}: {stderr or stdout[-3000:]}")
        modules = json.loads(output.read_text())["modules"]
        visited = set()
        state = 0
        types = set()
        edges = set()

        def module_name(name):
            return modules[name].get("attributes",{}).get("hdlname",name).split()[0].lstrip("\\")

        def visit(name):
            nonlocal state
            if name in visited:
                return
            visited.add(name)
            module = modules[name]
            parent = module_name(name)
            types.add(parent)
            for cell in module.get("cells",{}).values():
                typ = cell["type"]
                require("latch" not in typ.lower(), f"inferred latch: {name} {typ}")
                if "dff" in typ.lower():
                    state += 1
                if typ in modules:
                    require(any(cell["connections"].values()), "disconnected child")
                    child = module_name(typ)
                    edges.add((parent,child))
                    if child in {"anvil_q1_decoder_layer","anvil_q1_rmsnorm",
                                 "anvil_q1_w4a16_gemv","anvil_q1_rope",
                                 "anvil_q1_gqa_attention","anvil_q1_swiglu_mlp"}:
                        for port in ("cmd_valid","cmd_ready","done","error",
                                     "mem_req_valid","mem_rsp_ready"):
                            require(any(isinstance(bit,int) for bit in
                                        cell["connections"].get(port,[])),
                                    f"constant/disconnected {parent}->{child}.{port}")
                    if child == "anvil_q1_awq_dequant":
                        require(any(isinstance(bit,int) for bit in
                                    cell["connections"].get("weight_q16_16",[])),
                                "constant/disconnected dequantized weight")
                    visit(typ)
        visit("anvil_q1_top")
        required = {"anvil_q1_top","anvil_q1_decoder_layer","anvil_q1_rmsnorm",
                    "anvil_q1_w4a16_gemv","anvil_q1_awq_dequant","anvil_q1_rope",
                    "anvil_q1_gqa_attention","anvil_q1_swiglu_mlp"}
        require(required <= types and state>20, f"missing functional hierarchy/state {types}, {state}")
        required_edges = {
            ("anvil_q1_top","anvil_q1_decoder_layer"),
            ("anvil_q1_top","anvil_q1_rmsnorm"),
            *(("anvil_q1_decoder_layer","anvil_q1_"+child) for child in
              ("rmsnorm","w4a16_gemv","rope","gqa_attention","swiglu_mlp")),
            ("anvil_q1_swiglu_mlp","anvil_q1_w4a16_gemv"),
            ("anvil_q1_w4a16_gemv","anvil_q1_awq_dequant")}
        require(required_edges <= edges, f"missing literal hierarchy edges {required_edges-edges}")
        run.result(f"synthesis-{label}", outcome="pass", sequential_cells=state,
                   zero_latches=True, hierarchy=sorted(types),
                   required_connected_edges=sorted(required_edges))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=("behavior","synthesis","portability"), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--probe", choices=("dequant","rope","gemv","official","rms","matrix","protocol","errors","mutations","nonlinear","parameters","toolchain","numerical-audit","progress","cost-discriminator","transactor-cost-discriminator","mac-qualified-cost-discriminator","standalone-phase-cost"), default=None)
    parser.add_argument("--configuration", choices=tuple(MATRIX))
    parser.add_argument("--seed",type=int,default=17)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    valid_probes = {
        "behavior": {None,"dequant","rope","gemv","official","rms","matrix",
                     "protocol","errors","mutations","nonlinear","numerical-audit","progress",
                     "cost-discriminator","transactor-cost-discriminator",
                     "mac-qualified-cost-discriminator","standalone-phase-cost"},
        "portability": {None,"parameters","toolchain"},
        "synthesis": {None}}
    if args.probe not in valid_probes[args.check]:
        parser.error("probe incompatible with check")
    try:
        run = Run(args.out, args.repair_of)
    except FileExistsError:
        parser.exit(2, f"error: refusing occupied output destination: {args.out}\n")
    try:
        tools = (("python3", "iverilog", "vvp") if
                 args.probe in ("transactor-cost-discriminator",
                                "mac-qualified-cost-discriminator",
                                "standalone-phase-cost") else
                 ("python3", "iverilog", "vvp", "yosys"))
        for name in tools:
            executable = shutil.which(name)
            if executable:
                run.command([executable, "-V" if name in ("iverilog","yosys","vvp") else "--version"],
                            name+"-version", timeout=5)
        if args.check == "behavior":
            if args.probe != "standalone-phase-cost":
                slices = manifest(run)
            if args.probe == "standalone-phase-cost":
                require(args.configuration == "B" and args.seed == 17,
                        "standalone phase cost is B17 only")
                standalone_phase_cost(run)
            if args.probe == "transactor-cost-discriminator":
                require(args.configuration == "B" and args.seed == 17,
                        "transactor cost discriminator is B17 only")
                transactor_cost_discriminator(run)
            if args.probe == "mac-qualified-cost-discriminator":
                require(args.configuration == "B" and args.seed == 17,
                        "current-source cost discriminator is B17 only")
                mac_qualified_cost_discriminator(run)
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
            if args.probe == "cost-discriminator":
                require(args.configuration=="B" and args.seed==17,
                        "cost discriminator is B17 only")
                integrated(run,"B",17,discriminate_cost=True)
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
