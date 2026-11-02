#!/usr/bin/env python3
"""Source-bound independent arithmetic, protocol, decoder and synthesis checks."""

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import (  # noqa: E402
    NAN, INVALID, DIVZERO, approximation_interval, binary, bits32, f32,
    reference_selftest, tensor,
)
from operators import simulate_commands  # noqa: E402
from structure import synthesize  # noqa: E402
from protocols import simulate_csr, simulate_ddr  # noqa: E402
from architecture import GEOMETRIES, simulate_architecture  # noqa: E402
from sensitivity import sensitivity  # noqa: E402
from benchmarks import rms_benchmark  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def source_paths():
    return sorted(
        p for pattern in (
            "rtl/*.sv", "tests/*.py", "design/*.md", "fpga/*.sdc",
            "anvil_q1_fp_reference/rtl/*.sv",
        ) for p in ROOT.glob(pattern)
    )


class Run:
    def __init__(self, stem, preparation=False, repair_of=None):
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        relative = Path("evidence/preparation" if preparation else "evidence")
        self.relative = relative / f"{stem}-{stamp}-{uuid.uuid4().hex[:8]}"
        self.path = ROOT / self.relative
        self.path.mkdir(parents=True, exist_ok=False)
        self.receipt = {
            "argv": [sys.executable if sys.argv[0] == "-c" else "python3", *sys.argv],
            "cwd": ".", "started_at": now(), "repair_of": repair_of,
            "source_sha256": {}, "commands": [], "comparisons": [],
        }
        for source in source_paths():
            relative_source = source.relative_to(ROOT)
            self.receipt["source_sha256"][str(relative_source)] = hashlib.sha256(
                source.read_bytes()
            ).hexdigest()
            destination = self.path / "sources" / relative_source
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        self.versions = set()
        self.build_cache = {}

    def command(self, argv, stem, timeout=3600, expect=0, cwd="."):
        command = {
            "argv": list(map(str, argv)), "cwd": str(cwd),
            "started_at": now(), "timeout_s": timeout,
            "stdout": str(self.relative / f"{stem}.stdout.txt"),
            "stderr": str(self.relative / f"{stem}.stderr.txt"),
        }
        started = time.monotonic()
        try:
            with (ROOT / command["stdout"]).open("x") as stdout, (
                ROOT / command["stderr"]
            ).open("x") as stderr:
                process = subprocess.Popen(
                    command["argv"], cwd=ROOT / cwd, stdout=stdout, stderr=stderr,
                )
                command["timed_out"] = False
                while True:
                    try:
                        command["exit_code"] = process.wait(timeout=30)
                        break
                    except subprocess.TimeoutExpired:
                        print(f"progress: {stem}, {time.monotonic()-started:.0f}s", flush=True)
                        if time.monotonic() - started > timeout:
                            command["timed_out"] = True
                            process.terminate()
                            try:
                                process.wait(timeout=10)
                            except subprocess.TimeoutExpired:
                                process.kill()
                                process.wait()
                            command["exit_code"] = process.returncode
                            break
        except OSError as exc:
            command["exit_code"] = None
            command["error"] = str(exc)
            raise
        finally:
            command["ended_at"] = now()
            command["elapsed_s"] = time.monotonic() - started
            self.receipt["commands"].append(command)
        if command["timed_out"] or command["exit_code"] != expect:
            stdout = (ROOT / command["stdout"]).read_text()[-8000:]
            stderr = (ROOT / command["stderr"]).read_text()[-8000:]
            raise RuntimeError(
                f"{stem}: exit {command['exit_code']}, timeout={command['timed_out']}\n"
                f"{stdout}\n{stderr}"
            )
        return command

    def version(self, tool):
        if tool not in self.versions:
            self.command(
                [tool, "-V" if tool in ("iverilog", "vvp") else "--version"],
                f"version-{tool}",
            )
            self.versions.add(tool)

    def finish(self, error=None):
        self.receipt.update(ended_at=now(), exit_code=1 if error else 0)
        if error:
            self.receipt["failure"] = str(error)
        with (self.path / "receipt.json").open("x") as output:
            json.dump(self.receipt, output, indent=2)
            output.write("\n")
        print(f"receipt: {self.relative}/receipt.json", flush=True)
        if (self.path / "build-cache").exists():
            shutil.rmtree(self.path / "build-cache")


def pack_lanes(values, width):
    return sum(value << (width * lane) for lane, value in enumerate(values))


def tensor_vectors(seed, count):
    rng = random.Random(seed)
    records = []
    boundaries = [
        0, 0x8000, 1, 0x7F, 0x80, 0x81, 0x3F00, 0x3F80,
        0x3F81, 0x4000, 0x7F7F, 0xFF7F, 0x7F80, 0xFF80, 0x7FC0, 0x7F81,
    ]
    for mx in (False, True):
        for case in range(count + 1):
            mask = rng.getrandbits(64)
            a = [rng.getrandbits(8 if mx else 16) for _ in range(64)]
            b = [rng.getrandbits(8 if mx else 16) for _ in range(64)]
            scale_a = rng.getrandbits(16) if mx else 0x7F7F
            scale_b = rng.getrandbits(16) if mx else 0x7F7F
            acc = rng.getrandbits(32)
            if case == count:
                # Exactly 1 + 2^-24, halfway between FP32 values with an even low endpoint.
                a, b = [0] * 64, [0] * 64
                acc = 0
                if mx:
                    a[0], a[32], b[0], b[32] = 0x38, 0x38, 0x38, 0x38
                    mask = 1 | (1 << 32)
                    scale_a, scale_b = 0x677F, 0x7F7F
                else:
                    a[0], a[1], b[0], b[1] = 0x3F80, 0x3380, 0x3F80, 0x3F80
                    mask = 3
            elif case < 256 and mx:
                a = [case] * 64
                b = [0x38] * 64
                mask = 0xFFFFFFFFFFFFFFFF
                scale_a, scale_b = 0x7F7F, 0x7F7F
                acc = 0
            elif case < len(boundaries) ** 2 and not mx:
                a = [boundaries[case // len(boundaries)]] * 64
                b = [boundaries[case % len(boundaries)]] * 64
                mask = 0xFFFFFFFFFFFFFFFF
                acc = 0
            elif case % 17 == 0:
                mask = 0
                acc = [0, 0x80000000, 0x7F800001, 0x7FC00000][case % 4]
            elif case % 17 == 1 and not mx:
                a, b = [0] * 64, [0x3F80] * 64
                a[:3] = [0x7F7F, 0xFF7F, 1]
                b[2] = 1
                mask, acc = 7, 0
            elif case % 17 == 2:
                mask, acc = (1 << 31) | (1 << 32), 0
                scale_a, scale_b = 0x807E, 0x7D81
            value, status, events = tensor(a, b, mask, acc, mx, scale_a, scale_b)
            fields = (
                (pack_lanes(a, 8 if mx else 16), 1024),
                (pack_lanes(b, 8 if mx else 16), 1024),
                (int(mx), 1), (scale_a, 16), (scale_b, 16),
                (mask, 64), (acc, 32),
            )
            records.append((fields, value, value, status, events))
    return records


def binary_vectors(seed, count, multiply):
    rng = random.Random(seed)
    edges = [
        0, 0x80000000, 1, 0x007FFFFF, 0x00800000, 0x00800001,
        0x3F000000, 0x3F7FFFFF, 0x3F800000, 0x3F800001, 0x40000000,
        0x7F7FFFFF, 0xFF7FFFFF, 0x7F800000, 0xFF800000, 0x7FC00000, 0x7F800001,
    ]
    pairs = [(a, b) for a in edges for b in edges]
    pairs += [(rng.getrandbits(32), rng.getrandbits(32)) for _ in range(count)]
    records = []
    for a, b in pairs:
        value, flags = binary(a, b, multiply)
        records.append((((a, 32), (b, 32)), value, value, flags, 0))
    return records


def unary_vectors(kind, seed, count):
    rng = random.Random(seed)
    values = [0, 0x80000000, 0x7F800000, 0xFF800000, 0x7FC00000, 0x7F800001]
    if kind == "rsqrt":
        # Every interval's endpoints and midpoint, both exponent parities.
        values += [
            ((127 + parity) << 23) | (interval << 13) | offset
            for parity in range(2) for interval in range(1024)
            for offset in (0, 4096, 8191)
        ]
        values += [
            (exponent << 23) + offset for exponent in range(1, 255)
            for offset in (-1, 0, 1)
        ]
        values += [1, 2, 3, 0x003FFFFF, 0x007FFFFF, 0x7F7FFFFF, 0xBF800000]
        values += [rng.randrange(1, 0x7F800000) for _ in range(count)]
    else:
        values += [bits32(-80 * i / max(1, count - 1)) for i in range(count)]
        values += [bits32(x) for x in (-80, -79.999, -0.5, -0.01, 0.01, 1, 40, 80)]
    records = []
    for value in values:
        x = f32(value)
        if value & 0x7FFFFFFF > 0x7F800000:
            lo = hi = NAN
            flags = INVALID if not value & 0x00400000 else 0
        elif kind == "rsqrt":
            if x == 0:
                lo = hi = (value & 0x80000000) | 0x7F800000
                flags = DIVZERO
            elif x < 0:
                lo = hi = NAN
                flags = INVALID
            elif x == float("inf"):
                lo = hi = 0
                flags = 0
            else:
                lo, hi = approximation_interval(1 / x**0.5, 0.0025, True)
                flags = 1
        else:
            if x == 0:
                lo = hi = 0x3F800000
                flags = 0
            elif x in (float("inf"), float("-inf")):
                lo = hi = 0 if x < 0 else 0x7F800000
                flags = 0
            else:
                import math
                lo, hi = approximation_interval(math.exp(x), 0.0005, True)
                flags = 1
        records.append((((value, 32),), lo, hi, flags, 0))
    return records


def pipeline_tb(kind, vector_path, count, seed):
    tensor_kind = kind == "tensor"
    elastic = tensor_kind or kind in ("add", "multiply")
    latency = {"tensor": 16, "add": 9, "multiply": 9, "rsqrt": 2, "exp": 8}[kind]
    ports = (
        [("a", 1024), ("b", 1024), ("format_mx", 1), ("a_scale", 16),
         ("b_scale", 16), ("lane_mask", 64), ("acc_in", 32)]
        if tensor_kind else
        [("a", 32), ("b", 32)] if kind in ("add", "multiply") else [("x", 32)]
    )
    module = {
        "tensor": "bfp_tensor_array", "add": "fp32_binary",
        "multiply": "fp32_binary", "rsqrt": "fast_rsqrt", "exp": "exp",
    }[kind]
    declarations = "\n".join(
        f"reg [{width-1}:0] {name}=0, scanned_{name}=0;"
        for name, width in ports
    )
    connections = ",".join(f".{name}({name})" for name, _ in ports)
    extra = (
        ",.in_ready(in_ready),.out_ready(out_ready)" if elastic else ""
    ) + (",.alignment_events(events)" if tensor_kind else "")
    parameter = f"#(.MULTIPLY({int(kind == 'multiply')}))" if kind in ("add", "multiply") else ""
    names = ",".join("scanned_" + name for name, _ in ports)
    drive = "\n".join(f"{name}=scanned_{name};" for name, _ in ports)
    scan_format = " ".join(["%h"] * (len(ports) + 4)) + "\\n"
    zero_check = "{out_valid,result,status" + (",events}" if tensor_kind else "}")
    return f"""`timescale 1ns/1ps
module tb;
  reg clk=0,rst_n=0,in_valid=0,out_ready=0;
  always #5 clk=~clk;
  {declarations}
  wire in_ready,out_valid;
  wire [31:0] result;
  wire [4:0] status;
  wire [6:0] events;
  anvil_q1_fp2_{module} {parameter} dut(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),
    .out_valid(out_valid),.result(result),.status(status),
    {connections}{extra});
  {"assign in_ready=rst_n;" if not elastic else ""}
  {"assign events=0;" if not tensor_kind else ""}
  integer file_handle,scan,cycle,i,accepted=0,compared=0,stalls=0,bubbles=0;
  reg [31:0] rng=32'd{seed},lo,hi;
  reg [4:0] flags;
  reg [6:0] event_count;
  reg loaded=0,advance;
  reg [{latency-1}:0] expected_valid=0;
  reg [31:0] expected_lo[0:{latency-1}],expected_hi[0:{latency-1}];
  reg [4:0] expected_flags[0:{latency-1}];
  reg [6:0] expected_events[0:{latency-1}];
  function [31:0] ordered(input [31:0] value);
    ordered=value[31] ? ~value : value ^ 32'h80000000;
  endfunction
  task reset_check;
    begin
      if ({zero_check} !== 0 {"|| in_ready !== 0" if elastic else ""})
        $fatal(1,"RESET outputs not zero");
    end
  endtask
  initial begin
    #1; reset_check();
    @(posedge clk); reset_check();
    #1; reset_check();
    @(negedge clk); reset_check(); rst_n=1;
    file_handle=$fopen("{vector_path}","r");
    if (!file_handle) $fatal(1,"vector open failed");
    for (cycle=0;cycle<500000;cycle=cycle+1) begin
      rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
      if (!loaded && accepted<{count}) begin
        scan=$fscanf(file_handle,"{scan_format}",{names},lo,hi,flags,event_count);
        if (scan!={len(ports)+4}) $fatal(1,"malformed vector");
        {drive}
        loaded=1;
      end
      out_ready=(cycle%31>=5) && rng[3:0]!=0;
      if (!in_valid) in_valid=loaded && (cycle<40 || rng[1:0]!=0);
      #1;
      advance={"!expected_valid["+str(latency-1)+"] || out_ready" if elastic else "1'b1"};
      if (in_ready !== (rst_n && advance)) $fatal(1,"input ready mismatch");
      if (out_valid !== expected_valid[{latency-1}]) $fatal(1,"pre-edge valid mismatch");
      if (!advance) stalls=stalls+1;
      if (!in_valid) bubbles=bubbles+1;
      @(posedge clk);
      if (out_valid && {"out_ready" if elastic else "1'b1"}) compared=compared+1;
      if (advance) begin
        for (i={latency-1};i>0;i=i-1) begin
          expected_valid[i]=expected_valid[i-1];
          expected_lo[i]=expected_lo[i-1]; expected_hi[i]=expected_hi[i-1];
          expected_flags[i]=expected_flags[i-1]; expected_events[i]=expected_events[i-1];
        end
        expected_valid[0]=in_valid;
        expected_lo[0]=lo; expected_hi[0]=hi;
        expected_flags[0]=flags; expected_events[0]=event_count;
        if (in_valid) begin accepted=accepted+1; loaded=0; end
      end
      #1;
      if (out_valid !== expected_valid[{latency-1}])
        $fatal(1,"LATENCY cycle=%0d accepted=%0d",cycle,accepted);
      if (out_valid) begin
        if ((^result) === 1'bx || (^status) === 1'bx || (^events) === 1'bx)
          $fatal(1,"active X/Z cycle=%0d accepted=%0d compared=%0d result=%h status=%h events=%h expected=[%h,%h]/%h",
            cycle,accepted,compared,result,status,events,
            expected_lo[{latency-1}],expected_hi[{latency-1}],expected_flags[{latency-1}]);
        if (ordered(result)<ordered(expected_lo[{latency-1}]) ||
            ordered(result)>ordered(expected_hi[{latency-1}]) ||
            status !== expected_flags[{latency-1}] ||
            events !== expected_events[{latency-1}])
          $fatal(1,"NUMERICAL cycle=%0d accepted=%0d compared=%0d got=%h/%h/%h expected=[%h,%h]/%h/%h",
            cycle,accepted,compared,result,status,events,
            expected_lo[{latency-1}],expected_hi[{latency-1}],
            expected_flags[{latency-1}],expected_events[{latency-1}]);
      end else if ({{result,status,events}} !== 0) $fatal(1,"invalid payload not zero");
      if (accepted=={count} && expected_valid==0) begin
        if (compared!={count} || bubbles==0 {"|| stalls==0" if elastic else ""})
          $fatal(1,"missing transfer/stall/bubble coverage");
        $display("SUMMARY {kind}: accepted=%0d compared=%0d stalls=%0d bubbles=%0d",
          accepted,compared,stalls,bubbles);
        $fclose(file_handle); $finish;
      end
      @(negedge clk);
      if (!loaded) in_valid=0;
    end
    $fatal(1,"cycle watchdog");
  end
endmodule
"""


def simulate_pipeline(run, kind, records, seed, simulator):
    stem = f"{kind}-{seed}-{simulator}"
    directory = run.path / stem
    directory.mkdir()
    vectors = directory / "vectors.txt"
    with vectors.open("x") as output:
        for fields, low, high, status, events in records:
            output.write(" ".join(
                f"{value:0{(width+3)//4}x}" for value, width in fields
            ) + f" {low:08x} {high:08x} {status:02x} {events:02x}\n")
    bench = directory / "tb.sv"
    bench.write_text(pipeline_tb(kind, str(vectors.relative_to(ROOT)), len(records), seed))
    source_name = {
        "tensor": "bfp_tensor_array", "add": "fp32_binary",
        "multiply": "fp32_binary", "rsqrt": "fast_rsqrt", "exp": "exp",
    }[kind]
    sources = [
        "rtl/anvil_q1_fp2_00_pkg.sv", f"rtl/anvil_q1_fp2_{source_name}.sv",
        str(bench.relative_to(ROOT)),
    ]
    compile_and_run(run, directory, bench, sources[:-1], simulator, stem)
    run.receipt["comparisons"].append({
        "kind": kind, "seed": seed, "simulator": simulator,
        "vectors": len(records), "result": "passed",
    })


def compile_and_run(run, directory, bench, sources, simulator, stem, arguments=(), cache=False):
    overrides = getattr(run, "source_overrides", {})
    sources = [*(overrides.get(source, source) for source in sources),
               str(bench.relative_to(ROOT))]
    run.version(simulator)
    digest = hashlib.sha256(simulator.encode())
    for source in sources:
        digest.update((ROOT / source).read_bytes())
    cache_key = digest.hexdigest()
    binaries = getattr(run, "build_cache", {})
    if cache and cache_key in binaries:
        binary_path = binaries[cache_key]
        run.receipt.setdefault("build_reuse", []).append({
            "case": stem, "source_digest": cache_key,
            "binary_sha256": hashlib.sha256(binary_path.read_bytes()).hexdigest(),
        })
        run.command(
            (["vvp"] if simulator == "iverilog" else []) +
            [str(binary_path.relative_to(ROOT)), *arguments], f"{stem}-simulate",
        )
        return
    if simulator == "iverilog":
        run.version("vvp")
        binary_path = directory / "sim.vvp"
        run.command(
            ["iverilog", "-g2012", "-Wall", "-s", "tb", "-o",
             str(binary_path.relative_to(ROOT)), *sources], f"{stem}-compile",
        )
        run.command(["vvp", str(binary_path.relative_to(ROOT)), *arguments], f"{stem}-simulate")
    else:
        obj = directory / "compile-obj"
        try:
            run.command(
                ["verilator", "--binary", "--timing", "-Wno-fatal", "--top-module", "tb",
                 "--Mdir", str(obj.relative_to(ROOT)), "-j", "2", "-CFLAGS", "-O0", *sources],
                f"{stem}-compile",
            )
            if cache:
                cached = run.path / "build-cache" / cache_key
                cached.parent.mkdir(exist_ok=True)
                shutil.copyfile(obj / "Vtb", cached)
                cached.chmod(0o700)
                binaries[cache_key] = cached
            run.command([str((obj / "Vtb").relative_to(ROOT)), *arguments], f"{stem}-simulate")
        finally:
            if obj.exists():
                shutil.rmtree(obj)


def arithmetic(run, seeds, compact=False, simulator=None, leaves=None):
    reference_selftest()
    for seed in seeds:
        for kind in leaves or ("add", "multiply", "tensor", "rsqrt", "exp"):
            records = (
                binary_vectors(seed, 128 if compact else 4096, kind == "multiply")
                if kind in ("add", "multiply") else
                tensor_vectors(seed, 32 if compact else 4096) if kind == "tensor" else
                unary_vectors(kind, seed, 64 if compact else 4096)
            )
            simulate_pipeline(
                run, kind, records, seed,
                simulator or ("iverilog" if compact else "verilator"),
            )


def rsqrt_startup(run):
    """Same accepted +0 operand, with/without an earlier idle input change."""
    run.version("iverilog")
    run.version("vvp")
    failures = []
    for prechange in (False, True):
        stem = "rsqrt-startup-" + ("transitioned-control" if prechange else "stable-zero")
        directory = run.path / stem
        directory.mkdir()
        bench = directory / "tb.sv"
        bench.write_text(f"""`timescale 1ns/1ps
module tb;
  reg clk=0,rst_n=0,in_valid=0;
  reg [31:0] x=32'h{int(prechange):08x};
  wire out_valid;
  wire [31:0] result;
  wire [4:0] status;
  always #5 clk=~clk;
  anvil_q1_fp2_fast_rsqrt dut(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.x(x),
    .out_valid(out_valid),.result(result),.status(status));
  task reset_check;
    if ({{out_valid,result,status}} !== 0) $fatal(1,"reset mismatch");
  endtask
  initial begin
    #1; reset_check();
    @(posedge clk); reset_check();
    #1; reset_check();
    @(negedge clk); reset_check(); rst_n=1; x=0; in_valid=1;
    @(posedge clk);
    #1;
    if ({{out_valid,result,status}} !== 0) $fatal(1,"early result");
    @(negedge clk); in_valid=0;
    @(posedge clk);
    #1;
    $display("OBSERVED valid=%b result=%h status=%h; expected=1/7f800000/08",out_valid,result,status);
    if ({{out_valid,result,status}} !== {{1'b1,32'h7f800000,5'h08}})
      $fatal(1,"+0 rsqrt: expected positive infinity with divide-by-zero at k+1");
    @(negedge clk);
    @(posedge clk);
    #1;
    if ({{out_valid,result,status}} !== 0) $fatal(1,"bubble mismatch");
    $display("SUMMARY checked=1 two-stage latency, +0, divide-by-zero, reset, invalid bubble");
    $finish;
  end
endmodule
""")
        binary_path = directory / "sim.vvp"
        run.command(
            ["iverilog", "-g2012", "-Wall", "-s", "tb", "-o",
             str(binary_path.relative_to(ROOT)),
             "rtl/anvil_q1_fp2_00_pkg.sv", "rtl/anvil_q1_fp2_fast_rsqrt.sv",
             str(bench.relative_to(ROOT))],
            stem + "-compile",
        )
        try:
            run.command(["vvp", str(binary_path.relative_to(ROOT))], stem + "-simulate")
        except RuntimeError as exc:
            failures.append(str(exc))
            run.receipt["comparisons"].append({"case": stem, "result": "failed"})
        else:
            run.receipt["comparisons"].append({"case": stem, "result": "passed"})
    if failures:
        raise RuntimeError("\n".join(failures))


def portable(run):
    clean = run.path / ("clean-project-" + uuid.uuid4().hex[:8])
    clean.mkdir()
    for source in source_paths():
        target = clean / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    run.command(
        ["python3", "tests/verify.py", "--probe", "portable-inner", "--seeds", "17"],
        "clean-reproduction", cwd=clean.relative_to(ROOT),
    )
    receipts = list(clean.glob("evidence/preparation/*/receipt.json"))
    if len(receipts) != 1:
        raise AssertionError("clean reproduction did not retain exactly one execution receipt")
    receipt = json.loads(receipts[0].read_text())
    if receipt["exit_code"] != 0 or not receipt["comparisons"]:
        raise AssertionError("clean simulation/comparison/synthesis failed")
    run.receipt["comparisons"].append({
        "kind": "portable", "receipt": str(receipts[0].relative_to(ROOT)),
        "source_count": len(source_paths()), "result": "passed",
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--suite", choices=["synthesis", "sensitivity", "portable"])
    selector.add_argument("--probe",
                        choices=["arithmetic", "rsqrt-startup", "epilogue", "attention",
                                 "synthesis", "csr", "ddr", "architecture", "sensitivity",
                                 "portable-inner", "rms-benchmark"])
    parser.add_argument("--seeds", default="17,29,71")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--repair-of")
    parser.add_argument("--simulator", choices=["iverilog", "verilator"])
    parser.add_argument("--leaf", action="append",
                        choices=["add", "multiply", "tensor", "rsqrt", "exp"])
    args = parser.parse_args()
    selected = args.suite or args.probe
    run = Run(f"fp2-{selected}", preparation=args.probe is not None, repair_of=args.repair_of)
    error = None
    try:
        if selected == "rsqrt-startup":
            rsqrt_startup(run)
        elif selected == "portable":
            portable(run)
        elif selected == "rms-benchmark":
            rms_benchmark(run, ROOT, compile_and_run)
        elif selected == "portable-inner":
            arithmetic(run, [17], compact=True, leaves=("add", "multiply", "tensor"))
            simulate_csr(run, 17, "iverilog", compile_and_run, 8)
            simulate_ddr(run, 17, "iverilog", compile_and_run)
            synthesize(run, ROOT, tops=("anvil_q1_fp2_bfp_tensor_array",
                                       "anvil_q1_fp2_telemetry_csr"))
        elif selected == "synthesis":
            synthesize(run, ROOT)
        elif selected == "sensitivity":
            sensitivity(run, ROOT, compile_and_run, simulate_pipeline, tensor_vectors,
                        unary_vectors, simulate_commands, simulate_ddr, simulate_csr)
        elif selected == "csr":
            for seed in map(int, args.seeds.split(",")):
                for bits in (8, 64):
                    simulate_csr(run, seed, args.simulator or "iverilog",
                                 compile_and_run, bits)
        elif selected == "ddr":
            for seed in map(int, args.seeds.split(",")):
                simulate_ddr(run, seed, args.simulator or "iverilog", compile_and_run)
        elif selected == "architecture":
            for seed in map(int, args.seeds.split(",")):
                for geometry in GEOMETRIES[:1] if args.compact else GEOMETRIES:
                    for mx in (False, True):
                        simulate_architecture(
                            run, seed, geometry, mx, args.simulator or "verilator",
                            compile_and_run, ROOT,
                        )
        elif selected in ("epilogue", "attention"):
            for seed in map(int, args.seeds.split(",")):
                for tile in ((3,) if selected == "epilogue" or args.compact else (1, 3, 16)):
                    simulate_commands(
                        run, selected, seed,
                        2 if args.compact else 256 if selected == "epilogue" else 64,
                        args.simulator or ("iverilog" if args.compact else "verilator"),
                        compile_and_run, tile,
                    )
        else:
            arithmetic(run, [int(s) for s in args.seeds.split(",")], args.compact,
                       args.simulator, args.leaf)
    except Exception as exc:
        error = exc
        print(str(exc), file=sys.stderr, flush=True)
    finally:
        run.finish(error)
    return 1 if error else 0


if __name__ == "__main__":
    raise SystemExit(main())
