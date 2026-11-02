"""Bounded public-pin numerical diagnostic; not the complete admitted L1 suite.

Run: python3 tests/fp2_probe.py --kind scalar
Receipts and failed observations are retained in evidence/preparation/.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_reference import add, finite, multiply, mx_decode, transcendental, ulp_distance


ROOT = Path(__file__).resolve().parents[1]


SCALAR_TB = r"""
module tb;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n, flush=0, enable=1, in_valid=0, in_error=0, out_ready=1;
  reg [31:0] a=0, b=0;
  reg [31:0] read_a, read_b;
  wire va, vm, vr, ve, vc, rr;
  wire [31:0] da, dm, dr, de, dc;
  wire ea, em, er, ee, ec;
  anvil_q2_fp2_add4 add_dut(clk,rst_n,flush,enable,in_valid,in_error,a,b,va,da,ea);
  anvil_q2_fp2_mul3 mul_dut(clk,rst_n,flush,enable,in_valid,in_error,a,b,vm,dm,em);
  anvil_q2_fp2_rsqrt2 sqrt_dut(clk,rst_n,in_valid,rr,a,vr,out_ready,dr,er);
  anvil_q2_fp2_exp9 exp_dut(clk,rst_n,flush,enable,in_valid,in_error,a,ve,de,ee);
  anvil_q2_fp2_reciprocal2 recip_dut(clk,rst_n,flush,enable,in_valid,in_error,a,vc,dc,ec);
  integer fd, n, id, cycle=0, count=0, k;
  string input_path;
  always @(posedge clk) begin
    if (!rst_n && {va,vm,vr,ve,vc,rr,da,dm,dr,de,dc,ea,em,er,ee,ec} !== 0)
      $fatal(1,"RESET_OUTPUT_X_OR_NONZERO posedge");
  end
  always @(negedge clk) begin
    if (!rst_n && {va,vm,vr,ve,vc,rr,da,dm,dr,de,dc,ea,em,er,ee,ec} !== 0)
      $fatal(1,"RESET_OUTPUT_X_OR_NONZERO negedge");
  end
  initial begin
    rst_n=0;
    #1;
    if ({va,vm,vr,ve,vc,rr,da,dm,dr,de,dc,ea,em,er,ee,ec} !== 0)
      $fatal(1,"RESET_OUTPUT_X_OR_NONZERO time0");
    repeat(2) @(negedge clk);
    rst_n=1;
    if (!$value$plusargs("INPUT=%s",input_path)) $fatal(1,"missing INPUT");
    fd=$fopen(input_path,"r");
    if (!fd) $fatal(1,"input open");
    while (!$feof(fd)) begin
      n=$fscanf(fd,"%d %h %h\n",id,read_a,read_b);
      if (n!=3) begin
        if (!$feof(fd)) $fatal(1,"malformed stimulus");
      end else begin
        a=read_a;
        b=read_b;
        in_valid=1;
        @(posedge clk); #1;
        for (k=0;k<10;k=k+1) begin
          if (va !== (k==3) || vm !== (k==2) || vr !== (k==1) ||
              vc !== (k==1) || ve !== (k==8)) $fatal(1,"LATENCY id=%0d k=%0d",id,k);
          if (va) $display("RESULT %0d add %08h %0d",id,da,ea);
          if (vm) $display("RESULT %0d mul %08h %0d",id,dm,em);
          if (vr) $display("RESULT %0d rsqrt %08h %0d",id,dr,er);
          if (vc) $display("RESULT %0d reciprocal %08h %0d",id,dc,ec);
          if (ve) $display("RESULT %0d exp %08h %0d",id,de,ee);
          @(negedge clk);
          in_valid=0;
          @(posedge clk); #1;
        end
        @(negedge clk);
        count=count+1;
      end
    end
    $display("SUMMARY %0d",count);
    $fclose(fd);
    $finish;
  end
endmodule
"""


MX_TB = r"""
module tb;
  reg [7:0] payload, scale;
  wire [15:0] result;
  wire failed;
  integer p,s;
  anvil_q2_fp2_mx_decode decoder(payload,scale,result,failed);
  initial begin
    for (s=0;s<256;s=s+1)
      for (p=0;p<256;p=p+1) begin
        payload=p; scale=s; #1;
        $display("RESULT %0d %04h %0d",s*256+p,result,failed);
      end
    $display("SUMMARY 65536");
    $finish;
  end
endmodule
"""


def hashes():
    paths = []
    for pattern in ("rtl/*.sv", "tests/*.py", "design/*.md", "fpga/*",
                    "anvil_q2_fp_reference/rtl/*.sv"):
        paths.extend(path for path in ROOT.glob(pattern) if path.is_file())
    paths.sort()
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


class Probe:
    def __init__(self, kind, repair_of=None):
        name = f"fp2-{kind}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:8]}"
        self.directory = ROOT / "evidence" / "preparation" / name
        self.directory.mkdir(parents=True, exist_ok=False)
        self.receipt = {
            "kind": "independent-public-pin-numerical-preparation",
            "argv": [sys.executable, *sys.argv],
            "cwd": ".",
            "start_unix": time.time(),
            "source_sha256": hashes(),
            "python_version": sys.version,
            "commands": [],
            "repair_of": repair_of,
        }
        self.summary = {"comparisons": {}, "mismatches": [], "mismatch_count": 0}
        self.versions = {}

    def command(self, argv, stem, timeout=600):
        stdout = self.directory / f"{stem}.stdout.txt"
        stderr = self.directory / f"{stem}.stderr.txt"
        record = {
            "argv": [str(a) for a in argv],
            "cwd": ".",
            "start_unix": time.time(),
            "timeout_s": timeout,
            "stdout": str(stdout.relative_to(ROOT)),
            "stderr": str(stderr.relative_to(ROOT)),
            "timed_out": False,
        }
        self.receipt["commands"].append(record)
        with stdout.open("w") as out, stderr.open("w") as err:
            try:
                result = subprocess.run(argv, cwd=ROOT, stdout=out, stderr=err, timeout=timeout)
                record["exit_status"] = result.returncode
            except subprocess.TimeoutExpired:
                record["timed_out"] = True
                record["exit_status"] = None
                raise
            finally:
                record["end_unix"] = time.time()
        if result.returncode:
            raise RuntimeError(f"tool exit {result.returncode}: {record['stderr']}")
        return stdout

    def version(self, tool, flag):
        if not shutil.which(tool):
            raise FileNotFoundError(f"required tool unavailable: {tool}")
        path = self.command([tool, flag], f"version-{tool}")
        self.versions[tool] = path.read_text().splitlines()[:3]

    def compare(self, label, expected, actual, context):
        self.summary["comparisons"][label] = self.summary["comparisons"].get(label, 0) + 1
        if expected != actual:
            self.summary["mismatch_count"] += 1
            if len(self.summary["mismatches"]) < 24:
                self.summary["mismatches"].append(
                    {"check": label, "expected": expected, "actual": actual, **context}
                )

    def settle(self, error=None):
        self.summary["status"] = "failed" if error or self.summary["mismatch_count"] else "passed"
        self.summary["error"] = error
        path = self.directory / "summary.json"
        path.write_text(json.dumps(self.summary, indent=2) + "\n")
        self.receipt.update(
            end_unix=time.time(),
            exit_status=int(self.summary["status"] != "passed"),
            tool_versions=self.versions,
            summary=str(path.relative_to(ROOT)),
            artifact_sha256={
                str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.directory.iterdir()
                if p.is_file() and p.suffix not in (".json", ".txt")
            },
        )
        receipt = self.directory / "receipt.json"
        receipt.write_text(json.dumps(self.receipt, indent=2) + "\n")
        print(json.dumps({"receipt": str(receipt.relative_to(ROOT)), **self.summary}), flush=True)
        return self.receipt["exit_status"]


def scalar_vectors():
    directed = [
        0, 0x80000000, 1, 0x007FFFFF, 0x00800000, 0x00800001,
        0x3F000000, 0x3F800000, 0x3F800001, 0x40000000,
        0x7F7FFFFF, 0x7F800000, 0xFF800000, 0x7FC00000,
        0xBF800000, 0xC2A00000, 0xC2A00001, 0x80000001,
    ]
    pairs = [(a, b) for a in directed for b in directed]
    randomizer = random.Random(17)
    pairs += [(randomizer.getrandbits(32), randomizer.getrandbits(32)) for _ in range(12000)]
    for exponent in range(255):
        for offset in (0, 1, 4095, 4096, 8191, 8192, 0x7FFFFF):
            a = (exponent << 23) | offset
            if a:
                pairs.append((a, 0x3F800000))
    return pairs


def run_scalar(probe, simulator, compact=False):
    pairs = scalar_vectors()
    if compact:
        pairs = pairs[:324]
    source = probe.directory / "tb.sv"
    source.write_text(SCALAR_TB)
    inputs = probe.directory / "inputs.txt"
    inputs.write_text("".join(f"{i} {a:08x} {b:08x}\n" for i, (a, b) in enumerate(pairs)))
    rtl = [ROOT / "rtl" / name for name in (
        "anvil_q2_fp2_arithmetic.sv", "anvil_q2_fp2_nonlinear.sv", "anvil_q2_fp2_coefficients.sv"
    )]
    output = simulate(probe, source, rtl, simulator, [f"+INPUT={inputs.relative_to(ROOT)}"])
    seen = set()
    summary = None
    with output.open() as stream:
        for line in stream:
            words = line.split()
            if words[:1] == ["SUMMARY"]:
                summary = int(words[1])
            if words[:1] != ["RESULT"]:
                continue
            _, index, operation, data, failed = words
            index, actual, failed = int(index), int(data, 16), int(failed)
            if (index, operation) in seen or not 0 <= index < len(pairs):
                raise AssertionError(f"duplicate/out-of-range observation {index} {operation}")
            seen.add((index, operation))
            a, b = pairs[index]
            context = {"index": index, "a": f"{a:08x}", "b": f"{b:08x}"}
            if operation in ("add", "mul"):
                expected = add(a, b) if operation == "add" else multiply(a, b)
                probe.compare(operation, f"{expected:08x}", f"{actual:08x}", context)
                expected_error = not finite(a) or not finite(b) or not finite(expected)
                probe.compare(operation + "-error", int(expected_error), failed, context)
            else:
                invalid = not finite(a) or (
                    bool(a >> 31) or (a & 0x7FFFFFFF) == 0
                    if operation != "exp" else not a >> 31 and (a & 0x7FFFFFFF) != 0
                )
                if invalid:
                    probe.compare(operation + "-invalid", 1, failed, context)
                    continue
                if operation == "exp" and a > 0xC2A00000:
                    probe.compare("exp-cutoff", 0, actual, context)
                    probe.compare("exp-cutoff-error", 0, failed, context)
                    continue
                expected = transcendental(a, operation)
                # The reciprocal's admitted architectural domain is [1,32768].
                if operation == "reciprocal" and not 0x3F800000 <= a <= 0x47000000:
                    continue
                probe.compare(operation + "-error", 0, failed, context)
                probe.compare(
                    operation + "-4ulp", True,
                    finite(actual) and ulp_distance(expected, actual) <= 4,
                    {**context, "reference": f"{expected:08x}", "observed": f"{actual:08x}",
                     "ulp": ulp_distance(expected, actual)},
                )
    probe.compare("summary-count", len(pairs), summary, {})
    probe.compare("observation-count", 5 * len(pairs), len(seen), {})


def simulate(probe, source, rtl, simulator, extra=None):
    extra = extra or []
    probe.version(simulator, "-V" if simulator == "iverilog" else "--version")
    if simulator == "iverilog":
        probe.version("vvp", "-V")
        binary = probe.directory / "simulation.vvp"
        probe.command(
            ["iverilog", "-g2012", "-Wall", "-s", "tb", "-o", str(binary),
             *map(str, rtl), str(source)], "compile"
        )
        return probe.command(["vvp", str(binary), *extra], "simulation")
    objects = probe.directory / "compile-obj"
    binary = probe.directory / "simulation"
    probe.command(
        ["verilator", "--binary", "--timing", "-Wno-fatal", "--top-module", "tb",
         "-j", "2", "--Mdir", str(objects), "-o", str(binary),
         *map(str, rtl), str(source)], "compile"
    )
    try:
        return probe.command([str(binary), *extra], "simulation")
    finally:
        # Delete only this run's known transient compiler outputs, retaining generated C++.
        if objects.exists():
            for path in objects.iterdir():
                if path.suffix in (".o", ".a", ".gch") and path.is_file():
                    path.unlink()


def run_mx(probe):
    source = probe.directory / "tb.sv"
    source.write_text(MX_TB)
    output = simulate(probe, source, [ROOT / "rtl/anvil_q2_fp2_mx_decode.sv"], "iverilog")
    seen = set()
    summary = None
    with output.open() as stream:
        for line in stream:
            words = line.split()
            if words[:1] == ["SUMMARY"]:
                summary = int(words[1])
            if words[:1] != ["RESULT"]:
                continue
            _, index, data, failed = words
            index = int(index)
            if index in seen or not 0 <= index < 65536:
                raise AssertionError(f"duplicate/out-of-range observation {index}")
            seen.add(index)
            payload, scale = index & 255, index >> 8
            expected, error = mx_decode(payload, scale)
            context = {"payload": payload, "scale": scale}
            probe.compare("mx-data", f"{expected:04x}", data.lower(), context)
            probe.compare("mx-error", int(error), int(failed), context)
    probe.compare("summary-count", 65536, summary, {})
    probe.compare("observation-count", 65536, len(seen), {})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("scalar", "mx"), required=True)
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="verilator")
    parser.add_argument("--repair-of")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    os.chdir(ROOT)
    probe = Probe(args.kind, args.repair_of)
    try:
        if args.kind == "scalar":
            run_scalar(probe, args.simulator, args.compact)
        else:
            run_mx(probe)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
