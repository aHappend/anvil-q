#!/usr/bin/env python3
"""Independent public-port verification. Incomplete coverage fails closed.

The shared runtime executes --check l1 and --check clean-reproduction.
--probe creates advisory preparation evidence only.
No design sources or prior evidence are modified.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import resource
import shutil
import signal
import struct
import subprocess
import sys
import time
import threading
import uuid
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))
from protocol import UART, run_controller, run_uart, run_detokenizer, run_bpe, run_uart_controls
from storage import (
    run_boot, run_boot_boundaries, run_config, run_mapper, run_top,
    run_storage_faults, run_top_uart, top_test, run_large_images, run_top_resets,
    run_top_profiles,
    run_top_errors, run_top_reload,
    run_storage_edges,
    run_top_profile_uart, run_top_profile_reload,
    run_image_upper,
    run_watchdog_width,
)
from synthesis import run_synthesis
from mutations import run_mutations
from reproduce import clean_reproduction
from numerics import run_numerical, run_numerical_errors
from parameters import run_parameters
from adapters import run_adapters
from memory import run_memory
from text import run_normalization, run_dfa, run_tokenizer, run_tokenizer_capacity
from scheduling import resource_limits, scheduling_probe, scheduling_controls
from interactions import run_top_interactions, run_top_token_capacity, run_drain_prompts
from official import (
    run_official_discovery, run_official_intake, run_official_assets,
    run_official_checkpoint,
    run_official_environment,
    run_official_identity,
)
from qwen_tables import run_qwen_fragments
from qwen_regex import run_qwen_regex
from unicode_sources import run_unicode_sources, run_unicode_intake
from unicode_tables import run_unicode_conversion, run_unicode_rtl
from metadata import run_metadata
from qwen_integration import run_qwen_integration, run_qwen_boot
from qwen_shell import run_qwen_shell


ROOT = Path(__file__).resolve().parent.parent
SELECTORS = (
    "rtl/*.sv", "design/*.md", "fpga/*",
    "anvil_q1_reference/rtl/*.sv", "tests/*.py", "tests/data/*",
)
WALL_TIMEOUT = 14400


class VerificationFailure(Exception):
    pass


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as output:
        json.dump(value, output, indent=2, sort_keys=True)
        output.write("\n")


class Evidence:
    def __init__(self, label, preparation=False):
        parent = ROOT / "evidence" / ("preparation" if preparation else "verification")
        self.path = parent / (label + "-" + uuid.uuid4().hex)
        self.path.mkdir(parents=True, exist_ok=False)
        self.source_overrides = {}
        self.name_prefix = ""
        self.simulator_override = None
        self.compiled_simulations = {}
        self._root = self
        self._lock = threading.RLock()
        self._tool_lock = threading.RLock()
        self._cache_locks = {}
        self._child_index = 0
        self._case_index = 0
        self._active_children = {}
        self._peak_children = 0
        self._case_scopes = 0
        self._started = time.monotonic()
        self._limits = resource_limits(ROOT)
        self._slots = threading.BoundedSemaphore(self._limits["workers"])
        self.record = {
            "schema": 1,
            "kind": "verifier-preparation" if preparation else "verification",
            "acceptance_evidence": False,
            "argv": ["python3", "tests/verify.py", *sys.argv[1:]],
            "cwd": ".",
            "start_utc": utc(),
            "timeout_s": WALL_TIMEOUT,
            "timeout_scope": "Default per-child budget; child receipts record actual enforced limits",
            "parent_timeout_s": None,
            "parent_timeout_owner": "shared runtime",
            "children": [],
            "source_sha256": {},
            "tool_versions": {},
            "coverage": [],
            "case_batches": [],
            "scheduling": self._limits,
        }
        for selector in SELECTORS:
            for path in sorted(ROOT.glob(selector)):
                if path.is_file():
                    rel = path.relative_to(ROOT)
                    self.record["source_sha256"][str(rel)] = digest(path)
                    target = self.path / "sources" / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, target)

    def relative(self, path):
        return str(path.relative_to(ROOT))

    def run_cases(self, cases):
        """Settle every submitted case, including peers of a failing case."""
        cases = list(cases)
        labels = [label for label, _ in cases]
        if not cases or len(set(labels)) != len(labels):
            raise VerificationFailure("Case batches must be nonempty and uniquely labelled")
        batch = {"planned": labels, "results": [], "status": "running"}
        self.record["case_batches"].append(batch)

        def execute(label, function):
            scope = copy.copy(self)
            scope.source_overrides = dict(self.source_overrides)
            with self._lock:
                index = self._root._case_index
                self._root._case_index += 1
            safe_label = re.sub(r"[^a-zA-Z0-9_.-]", "-", label)
            scope.path = self.path / f"case-{index:04d}-{safe_label}"
            scope.path.mkdir()
            scope.record = dict(self.record)
            for key in ("children", "coverage", "case_batches"):
                scope.record[key] = []
            with self._lock:
                self._root._case_scopes += 1
            start = time.monotonic()
            result = {"name": label, "status": "running", "start_utc": utc(),
                      "directory": self.relative(scope.path)}
            try:
                function(scope)
                result["status"] = "passed"
            except BaseException as error:
                result.update(status="failed", error=f"{type(error).__name__}: {error}")
                raise
            finally:
                result.update(end_utc=utc(), duration_s=time.monotonic() - start)
                with self._lock:
                    for key in ("children", "coverage", "case_batches"):
                        self.record[key].extend(scope.record[key])
                    batch["results"].append(result)
                    self._root._case_scopes -= 1

        failures = []
        with ThreadPoolExecutor(max_workers=self._limits["workers"]) as executor:
            futures = [(label, executor.submit(execute, label, function))
                       for label, function in cases]
            for label, future in futures:
                try:
                    future.result()
                except BaseException as error:
                    failures.append((label, error))
        batch["status"] = "failed" if failures else "passed"
        if sorted(row["name"] for row in batch["results"]) != sorted(labels):
            raise VerificationFailure("Case accounting lost a submitted case")
        if failures:
            raise VerificationFailure(
                "; ".join(f"{label}: {error}" for label, error in failures)
            ) from failures[0][1]

    def child(self, argv, name, timeout=WALL_TIMEOUT, allow_failure=False, cwd=None):
        """Every child has immutable raw logs and a separate final receipt."""
        queued = time.monotonic()
        with self._slots:
            return self._child(argv, name, timeout, allow_failure, cwd,
                               time.monotonic() - queued)

    def _child(self, argv, name, timeout, allow_failure, cwd, queue_seconds):
        with self._lock:
            index = self._root._child_index
            self._root._child_index += 1
        directory = self.path / f"{index:03d}-{name}"
        directory.mkdir()
        record = {
            "index": index,
            "argv": [str(arg) for arg in argv],
            "cwd": "." if cwd is None else self.relative(cwd),
            "start_utc": utc(), "timeout_s": timeout,
            "stdout": self.relative(directory / "stdout.log"),
            "stderr": self.relative(directory / "stderr.log"),
            "timed_out": False, "child_settled": False,
            "queue_duration_s": queue_seconds,
        }
        start = time.monotonic()
        interrupted = None
        with (directory / "stdout.log").open("xb") as stdout:
            with (directory / "stderr.log").open("xb") as stderr:
                try:
                    process = subprocess.Popen(
                        record["argv"], cwd=ROOT if cwd is None else cwd,
                        stdout=stdout, stderr=stderr,
                        start_new_session=True,
                    )
                except OSError as error:
                    stderr.write((str(error) + "\n").encode())
                    record["exit_code"] = None
                    record["launch_error"] = str(error)
                    record["child_settled"] = True
                else:
                    with self._lock:
                        self._root._active_children[process.pid] = record["argv"]
                        self._root._peak_children = max(
                            self._root._peak_children, len(self._root._active_children))
                    try:
                        deadline = start + timeout
                        while True:
                            pid, status, usage = os.wait4(process.pid, os.WNOHANG)
                            if pid:
                                process.returncode = os.waitstatus_to_exitcode(status)
                                break
                            if time.monotonic() >= deadline:
                                record["timed_out"] = True
                                os.killpg(process.pid, signal.SIGTERM)
                                deadline = time.monotonic() + 10
                                while time.monotonic() < deadline:
                                    pid, status, usage = os.wait4(process.pid, os.WNOHANG)
                                    if pid:
                                        break
                                    time.sleep(.05)
                                if not pid:
                                    os.killpg(process.pid, signal.SIGKILL)
                                    _, status, usage = os.wait4(process.pid, 0)
                                process.returncode = os.waitstatus_to_exitcode(status)
                                break
                            time.sleep(.05)
                    except BaseException as error:
                        interrupted = error
                        os.killpg(process.pid, signal.SIGKILL)
                        _, status, usage = os.wait4(process.pid, 0)
                        process.returncode = os.waitstatus_to_exitcode(status)
                        record["interrupted"] = f"{type(error).__name__}: {error}"
                    finally:
                        with self._lock:
                            del self._root._active_children[process.pid]
                    record["exit_code"] = process.returncode
                    record["child_settled"] = process.poll() is not None
                    record["resources"] = {
                        "user_cpu_s": usage.ru_utime, "system_cpu_s": usage.ru_stime,
                        "max_rss_kib": usage.ru_maxrss,
                        "major_page_faults": usage.ru_majflt,
                        "input_blocks": usage.ru_inblock, "output_blocks": usage.ru_oublock,
                    }
                    try:
                        os.killpg(process.pid, 0)
                    except ProcessLookupError:
                        record["process_group_settled"] = True
                    else:
                        os.killpg(process.pid, signal.SIGKILL)
                        record["process_group_settled"] = False
        record["end_utc"] = utc()
        record["duration_s"] = time.monotonic() - start
        write_json(directory / "receipt.json", record)
        self.record["children"].append(record)
        if interrupted is not None:
            raise interrupted
        if not allow_failure and (
            record["exit_code"] != 0 or record["timed_out"]
            or not record["child_settled"] or not record.get("process_group_settled", True)
        ):
            raise VerificationFailure(
                f"{name} failed; see {self.relative(directory / 'receipt.json')}"
            )
        return record

    def tools(self, names, timeout=WALL_TIMEOUT):
        with self._tool_lock:
            self._tools(names, timeout)

    def _tools(self, names, timeout):
        missing = [name for name in names if shutil.which(name) is None]
        if missing:
            self.record["missing_tools"] = missing
            raise VerificationFailure("Missing required tools: " + ", ".join(missing))
        for name in names:
            if name not in self.record["tool_versions"]:
                flag = "-V" if name in ("iverilog", "vvp", "yosys") else "--version"
                record = self.child([name, flag], name + "-version", timeout=timeout)
                self.record["tool_versions"][name] = record

    def simulate(self, name, bench, sources, comparisons, *, simulator=None):
        # Only bounded arithmetic/FIFO leaves stay on the four-state interpreter.
        leaf = name == "half" or name.startswith(
            ("multiply-", "divide-", "sqrt-", "fifo-", "lowering-")
        )
        simulator = simulator or self.simulator_override or (
            "iverilog" if leaf else "verilator"
        )
        if simulator not in ("iverilog", "verilator"):
            raise VerificationFailure(f"Unsupported simulator: {simulator}")
        name = self.name_prefix + name
        sources = [self.source_overrides.get(source, source) for source in sources]
        directory = self.path / name
        directory.mkdir()
        source = directory / "bench.sv"
        source.write_text(bench, encoding="ascii")
        binary = directory / "simulation.vvp"
        record = {
            "name": name,
            "bench_sha256": digest(source),
            "required_comparisons": comparisons,
            "simulator": simulator,
            "status": "not-run",
        }
        self.record["coverage"].append(record)
        if simulator == "iverilog":
            self.tools(("iverilog", "vvp"))
            record["compile_receipt"] = self.child(
                ["iverilog", "-g2012", "-Wall", "-s", "bench", "-o",
                 self.relative(binary), *sources, self.relative(source)],
                name + "-compile",
            )
            result = self.child(["vvp", self.relative(binary)], name + "-simulate",
                                allow_failure=True)
        else:
            self.tools(("verilator", "g++", "make"))
            compiled_source = directory / "compiled-bench.sv"
            # Verilator has no inactive-region #0 support. Keep the original
            # bench, and settle reset 1 ps before checking, never a clock later.
            compiled_bench, reset_delays = re.subn(r"#0\s*;", "#1ps;", bench)
            runtime_args = []
            seed = re.search(r"reg\s+\[31:0\]\s+rng=(\d+);", compiled_bench)
            if seed:
                runtime_args.append("+verification_seed=" + seed[1])
                compiled_bench = compiled_bench[:seed.start()] + (
                    'reg [31:0] rng;\n'
                    '  initial if (!$value$plusargs("verification_seed=%d",rng)) '
                    '$fatal(1,"MISSING_VERIFICATION_SEED");'
                ) + compiled_bench[seed.end():]
            input_functions = []
            input_files = []

            def input_path(match):
                index = len(input_functions)
                runtime_args.append(f"+verification_file{index}={match[1]}")
                input_files.append({"path": match[1], "sha256": digest(ROOT / match[1])})
                input_functions.append(
                    f"  function automatic string verification_file{index}();\n"
                    "    string value;\n"
                    f'    if (!$value$plusargs("verification_file{index}=%s",value)) '
                    '$fatal(1,"MISSING_VERIFICATION_INPUT");\n'
                    "    return value;\n"
                    "  endfunction\n"
                )
                return f"$readmemh(verification_file{index}(),"

            compiled_bench = re.sub(r'\$readmemh\("([^"]+)",', input_path, compiled_bench)
            if input_functions:
                if compiled_bench.count("module bench;") != 1:
                    raise VerificationFailure("Missing unique bench module for input binding")
                compiled_bench = compiled_bench.replace(
                    "module bench;", "module bench;\n" + "".join(input_functions), 1
                )
            compiled_source.write_text(compiled_bench, encoding="ascii")
            record.update(
                compiled_bench_sha256=digest(compiled_source),
                reset_settle_delays_ps=reset_delays,
                four_state=False,
            )
            source_hashes = [(path, digest(ROOT / path)) for path in sources]
            compile_options = [
                "--binary", "--timing", "--assert",
                "--timescale", "1ns/1ps", "--top-module", "bench",
                "-Wno-fatal", "--x-initial", "unique", "--x-assign", "unique",
                "-j", "2",
            ]
            tool_identity = {}
            for tool_name in ("verilator", "g++", "make"):
                tool = self.record["tool_versions"][tool_name]
                tool_identity[tool_name] = {
                    "path": shutil.which(tool_name),
                    "stdout_sha256": digest(ROOT / tool["stdout"]),
                    "stderr_sha256": digest(ROOT / tool["stderr"]),
                    "executable_sha256": digest(Path(shutil.which(tool_name))),
                }
            cache_key = hashlib.sha256(json.dumps(
                [compiled_bench, source_hashes, compile_options, tool_identity],
                sort_keys=True
            ).encode()).hexdigest()
            with self._lock:
                cache_lock = self._cache_locks.setdefault(cache_key, threading.Lock())
            with cache_lock:
                cached = self.compiled_simulations.get(cache_key)
                cache_hit = cached is not None
                if cached is None:
                    object_dir = directory / "obj"
                    compile_record = self.child(
                        ["verilator", *compile_options,
                         "--Mdir", self.relative(object_dir), "-o", "simulation",
                         *sources, self.relative(compiled_source)],
                        name + "-compile",
                    )
                    binary = object_dir / "simulation"
                    cached = (binary, compile_record, digest(binary))
                    self.compiled_simulations[cache_key] = cached
            binary, compile_record, binary_hash = cached
            if digest(binary) != binary_hash:
                raise VerificationFailure("Compiled simulation changed before reuse")
            record.update(
                compile_cache_key=cache_key, executable_sha256=binary_hash,
                compile_receipt=compile_record,
                runtime_arguments=runtime_args, input_files=input_files,
                compile_cache_hit=cache_hit, compile_tool=tool_identity,
                compile_options=compile_options, source_sha256=source_hashes,
            )
            result = self.child([self.relative(binary), *runtime_args], name + "-simulate",
                                allow_failure=True)
        record.update(simulation_receipt=result, status="failed")
        if (result["exit_code"] != 0 or result["timed_out"] or
                not result["child_settled"] or not result.get("process_group_settled", True)):
            receipt = str(Path(result["stdout"]).parent / "receipt.json")
            raise VerificationFailure(f"{name} failed; see {receipt}")
        lines = (ROOT / result["stdout"]).read_text().splitlines()
        totals = [int(line.split()[1]) for line in lines if line.startswith("COMPARED ")]
        if len(totals) != 1 or totals[0] <= 0 or (
            comparisons is not None and totals[0] != comparisons
        ):
            raise VerificationFailure(f"{name}: invalid comparison count {totals}, required {comparisons}")
        record["actual_comparisons"] = totals[0]
        record["status"] = "passed"
        return record

    def finish(self, exit_code, reason):
        with self._lock:
            if self._root._active_children or self._root._case_scopes:
                raise VerificationFailure("Cannot publish evidence with unsettled work")
        self.record["children"].sort(key=lambda row: row["index"])
        simulations = [row for row in self.record["coverage"] if "simulator" in row]
        self.record["simulation_accounting"] = {
            "recorded": len(simulations),
            "by_status": {status: sum(row["status"] == status for row in simulations)
                          for status in ("passed", "expected-functional-rejection",
                                         "expected-harness-rejection",
                                         "failed", "not-run")},
            "passed_comparisons": sum(row.get("actual_comparisons", 0)
                                      for row in simulations if row["status"] == "passed"),
            "case_batch_count": len(self.record["case_batches"]),
            "planned_cases": sum(len(batch["planned"]) for batch in self.record["case_batches"]),
            "settled_cases": sum(len(batch["results"]) for batch in self.record["case_batches"]),
            "scope": "Nested batch counts include suite nodes; simulation rows count actual "
                     "attempts. Expected rejections require specific unchanged mutation assertions.",
        }
        self.record.update(
            end_utc=utc(), exit_code=exit_code, reason=reason,
            child_settled=all(c["child_settled"] and c.get("process_group_settled", True)
                              for c in self.record["children"]),
            duration_s=time.monotonic() - self._started,
            resources={
                "peak_concurrent_children": self._root._peak_children,
                "parent_max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "child_user_cpu_s": sum(c.get("resources", {}).get("user_cpu_s", 0)
                                        for c in self.record["children"]),
                "child_system_cpu_s": sum(c.get("resources", {}).get("system_cpu_s", 0)
                                          for c in self.record["children"]),
            },
        )
        current = {}
        for selector in SELECTORS:
            for path in ROOT.glob(selector):
                if path.is_file():
                    current[str(path.relative_to(ROOT))] = digest(path)
        self.record["sources_unchanged"] = current == self.record["source_sha256"]
        if not self.record["sources_unchanged"]:
            self.record["exit_code"] = 1
            self.record["reason"] = "Source set changed during verification; evidence invalid"
        if not self.record["child_settled"]:
            self.record["exit_code"] = 1
            self.record["reason"] = "A child process group did not settle; evidence invalid"
        write_json(self.path / "receipt.json", self.record)
        print(json.dumps({
            "exit_code": self.record["exit_code"],
            "reason": self.record["reason"],
            "receipt": self.relative(self.path / "receipt.json"),
        }))
        return self.record["exit_code"]


def literal(value, width):
    return f"{width}'h{value & ((1 << width) - 1):x}"


def half_reference(bits):
    value = struct.unpack("<e", bits.to_bytes(2, "little"))[0]
    if not math.isfinite(value):
        return None
    magnitude = math.floor(abs(value) * 65536 + 0.5)
    scaled = -magnitude if math.copysign(1, value) < 0 else magnitude
    return max(-(1 << 31), min((1 << 31) - 1, scaled))


def conversion_test(evidence):
    directory = evidence.path / "half-input"
    directory.mkdir()
    vectors = directory / "vectors.txt"
    with vectors.open("x") as output:
        for bits in range(65536):
            expected = half_reference(bits)
            output.write(f"{bits:04x} {int(expected is None):x} "
                         f"{(expected or 0) & 0xffffffff:08x}\n")
    bench = """
module bench;
  import anvil_edge_numeric_pkg::*;
  integer file, scanned, count;
  reg [15:0] bits;
  reg invalid;
  reg [31:0] expected;
  initial begin
    count=0;
    file=$fopen("VECTOR_PATH","r");
    if (!file) $fatal(1,"missing independent half vectors");
    while (!$feof(file)) begin
      scanned=$fscanf(file,"%h %h %h\\n",bits,invalid,expected);
      if (scanned!=3) $fatal(1,"malformed independent half vector");
      if (f16_invalid(bits)!==invalid)
        $fatal(1,"HALF_CLASS bits=%h",bits);
      if (!invalid && f16_q16(bits)!==expected)
        $fatal(1,"HALF_VALUE bits=%h expected=%h observed=%h",
               bits,expected,f16_q16(bits));
      count=count+1;
    end
    if (count!=65536) $fatal(1,"half coverage count=%0d",count);
    $display("COMPARED %0d",count);
    $finish;
  end
endmodule
""".replace("VECTOR_PATH", evidence.relative(vectors))
    evidence.simulate("half", bench, ["rtl/anvil_edge_numeric_pkg.sv"], 65536)


def arithmetic_test(evidence, kind, width, seed):
    rng = random.Random(seed)
    mask = (1 << width) - 1
    if kind == "multiply":
        low, high = -(1 << (width - 1)), (1 << (width - 1)) - 1
        edge = sorted({low, high, 0, -1, min(1, high)})
        pairs = [(a, b) for a in edge for b in edge]
        pairs += [(rng.randint(low, high), rng.randint(low, high)) for _ in range(32)]
        latency = 2 + ((math.ceil(width / 16) ** 2) - 1).bit_length()
        declarations = f"""
  reg signed [{width-1}:0] operand_a=0, operand_b=0;
  wire signed [{2*width-1}:0] product;
  anvil_edge_signed_multiplier #(.WIDTH({width})) dut(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(in_ready),
    .operand_a(operand_a),.operand_b(operand_b),
    .out_valid(out_valid),.out_ready(out_ready),.product(product));
"""
        trials = [
            (f"operand_a={literal(a,width)}; operand_b={literal(b,width)};",
             f"product!=={literal(a*b,2*width)}")
            for a, b in pairs
        ]
        reset_fields = "product!==0"
        source = "rtl/anvil_edge_signed_multiplier.sv"
    elif kind == "divide":
        edges = sorted({0, 1, mask, mask >> 1})
        pairs = [(a, b) for a in edges for b in edges]
        pairs += [(rng.getrandbits(width), rng.getrandbits(width)) for _ in range(32)]
        latency = width + 1
        declarations = f"""
  reg [{width-1}:0] numerator=0, denominator=0;
  wire [{width-1}:0] quotient, remainder;
  wire divide_by_zero;
  anvil_edge_unsigned_divider #(.WIDTH({width})) dut(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(in_ready),
    .numerator(numerator),.denominator(denominator),.out_valid(out_valid),
    .out_ready(out_ready),.quotient(quotient),.remainder(remainder),
    .divide_by_zero(divide_by_zero));
"""
        trials = []
        for a, b in pairs:
            q, r = divmod(a, b) if b else (0, 0)
            trials.append((
                f"numerator={literal(a,width)}; denominator={literal(b,width)};",
                f"quotient!=={literal(q,width)} || remainder!=={literal(r,width)} "
                f"|| divide_by_zero!==1'b{int(b==0)}",
            ))
        reset_fields = "quotient!==0 || remainder!==0 || divide_by_zero!==0"
        source = "rtl/anvil_edge_unsigned_divider.sv"
    else:
        values = [0, 1, 2, 3, 4, (1 << 128) - 1]
        for root in (2, 3, (1 << 32) - 1, 1 << 32, (1 << 64) - 1):
            values.extend([root * root - 1, root * root, root * root + 1])
        values += [rng.getrandbits(128) for _ in range(32)]
        latency = 65
        declarations = """
  reg [127:0] radicand=0;
  wire [63:0] root;
  anvil_edge_isqrt128 dut(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(in_ready),
    .radicand(radicand),.out_valid(out_valid),.out_ready(out_ready),.root(root));
"""
        trials = [
            (f"radicand={literal(n,128)};", f"root!=={literal(math.isqrt(n),64)}")
            for n in values
        ]
        reset_fields = "root!==0"
        source = "rtl/anvil_edge_isqrt128.sv"
    actions = []
    for index, (drive, mismatch) in enumerate(trials):
        actions.append(f"""
    @(negedge clk);
    if (in_ready!==1 || out_valid!==0) $fatal(1,"ARITH_IDLE trial={index}");
    {drive}
    in_valid=1;
    @(posedge clk);
    if (out_valid!==0) $fatal(1,"ARITH_E0 trial={index}");
    @(negedge clk); in_valid=0;
    for (cycle=1;cycle<{latency};cycle=cycle+1) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_EARLY trial={index} cycle=%0d",cycle);
    end
    @(posedge clk); #1;
    if (out_valid!==1 || ({mismatch}))
      $fatal(1,"ARITH_RESULT trial={index} latency={latency}");
    repeat ({rng.randint(2,7)}) begin
      @(posedge clk); #1;
      if (out_valid!==1 || in_ready!==0 || ({mismatch}))
        $fatal(1,"ARITH_STALL trial={index}");
    end
    @(negedge clk); out_ready=1;
    @(posedge clk); #1;
    if (out_valid!==0) $fatal(1,"ARITH_RETIRE trial={index}");
    @(negedge clk); out_ready=0;
    count=count+1;
""")
    bench = f"""
module bench;
  reg clk=0;
  reg rst_n;
  reg in_valid=0, out_ready=0;
  wire in_ready, out_valid;
  integer cycle, count=0;
  always #5 clk=~clk;
  {declarations}
  task automatic reset_check;
    begin
      if (in_ready!==0 || out_valid!==0 || ({reset_fields}))
        $fatal(1,"ARITH_RESET time=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    rst_n=0;
    #0; reset_check();
    repeat (2) @(negedge clk);
    rst_n=1;
    {''.join(actions)}
    @(negedge clk); {trials[-1][0]} in_valid=1;
    @(posedge clk);
    @(negedge clk); #1; in_valid=0; rst_n=0;
    #1; reset_check();
    repeat (2) @(negedge clk);
    rst_n=1;
    repeat ({latency+3}) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"ARITH_RESET_STALE");
    end
    if (count!={len(trials)}) $fatal(1,"ARITH_COUNT");
    $display("COMPARED %0d",count);
    $finish;
  end
  initial begin
    repeat (100000) @(posedge clk);
    $fatal(1,"ARITH_CYCLE_BOUND");
  end
endmodule
"""
    evidence.simulate(f"{kind}-w{width}-s{seed}", bench, [source], len(trials))


def fifo_test(evidence, depth, seed):
    rng = random.Random(seed)
    queue = []
    rows = []
    coverage = {"push": 0, "pop": 0, "full_replace": 0, "reset_nonempty": 0}
    pending = None
    # Fill, full replacement, drain, then random held-valid traffic and reset.
    schedule = [(1, 1, 0)] * depth + [(1, 1, 1)] * (depth + 2)
    schedule += [(1, 0, 1)] * (depth + 1)
    for cycle in range(1000):
        reset = cycle not in (201, 701)
        schedule.append((int(reset), int(rng.random() < .7), int(rng.random() < .6)))
    schedule += [(1, 0, 1)] * (depth + 1)
    for rst_n, offer, ready in schedule:
        if not rst_n:
            coverage["reset_nonempty"] += int(bool(queue))
            queue.clear()
            pending = None
        if pending is None and offer:
            pending = rng.randrange(512)
        valid = int(pending is not None)
        data = pending or 0
        out_valid = int(rst_n and bool(queue))
        pop = bool(out_valid and ready)
        in_ready = int(rst_n and (len(queue) < depth or pop))
        old = queue[0] if out_valid else 0
        empty = int(rst_n and not queue)
        full = int(rst_n and len(queue) == depth)
        rows.append(
            f"{rst_n:x} {valid:x} {ready:x} {data:x} {in_ready:x} "
            f"{out_valid:x} {old:x} {empty:x} {full:x}\n"
        )
        push = bool(valid and in_ready)
        coverage["full_replace"] += int(full and pop and push)
        coverage["push"] += int(push)
        coverage["pop"] += int(pop)
        if pop:
            queue.pop(0)
        if push:
            queue.append(data)
            pending = None
    if not all(coverage.values()):
        raise VerificationFailure(f"FIFO stimulus lacks required events: {coverage}")
    directory = evidence.path / f"fifo-input-d{depth}-s{seed}"
    directory.mkdir()
    vectors = directory / "vectors.txt"
    vectors.write_text("".join(rows), encoding="ascii")
    write_json(directory / "expected-events.json", coverage)
    bench = f"""
module bench;
  reg clk=0;
  reg rst_n;
  reg in_valid=0, out_ready=0;
  reg [8:0] in_data=0;
  wire in_ready,out_valid,empty,full;
  wire [8:0] out_data;
  reg expected_ready,expected_valid,expected_empty,expected_full;
  reg [8:0] expected_data;
  integer file,scanned,count=0;
  always #5 clk=~clk;
  anvil_edge_fifo #(.WIDTH(9),.DEPTH({depth})) dut(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(in_ready),
    .in_data(in_data),.out_valid(out_valid),.out_ready(out_ready),
    .out_data(out_data),.empty(empty),.full(full));
  task automatic reset_check;
    begin
      if ({{in_ready,out_valid,out_data,empty,full}}!==13'd0)
        $fatal(1,"FIFO_RESET time=%0t",$time);
    end
  endtask
  task automatic compare;
    begin
      if ({{in_ready,out_valid,out_data,empty,full}}!==
          {{expected_ready,expected_valid,expected_data,expected_empty,expected_full}})
        $fatal(1,"FIFO_QUEUE cycle=%0d expected=%h observed=%h",count,
          {{expected_ready,expected_valid,expected_data,expected_empty,expected_full}},
          {{in_ready,out_valid,out_data,empty,full}});
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    rst_n=0; #0; reset_check();
    repeat (2) @(negedge clk);
    file=$fopen("{evidence.relative(vectors)}","r");
    if (!file) $fatal(1,"missing independent FIFO vectors");
    while (!$feof(file)) begin
      @(negedge clk); #1;
      scanned=$fscanf(file,"%h %h %h %h %h %h %h %h %h\\n",
        rst_n,in_valid,out_ready,in_data,expected_ready,expected_valid,
        expected_data,expected_empty,expected_full);
      if (scanned!=9) $fatal(1,"malformed FIFO vector");
      #1; compare();
      @(posedge clk); compare();
      count=count+1;
    end
    if (count!={len(rows)}) $fatal(1,"FIFO_COUNT");
    $display("COMPARED %0d",count);
    $finish;
  end
  initial begin
    repeat (20000) @(posedge clk);
    $fatal(1,"FIFO_CYCLE_BOUND");
  end
endmodule
"""
    evidence.simulate(f"fifo-d{depth}-s{seed}", bench, ["rtl/anvil_edge_fifo.sv"], len(rows))


def run_arithmetic(evidence):
    evidence.tools(("iverilog", "vvp"))
    conversion_test(evidence)
    for seed in (1, 17, 89):
        for width in (1, 8, 16, 17, 32, 64, 128):
            arithmetic_test(evidence, "multiply", width, seed)
            arithmetic_test(evidence, "divide", width, seed)
        arithmetic_test(evidence, "sqrt", 128, seed)


def run_fifo(evidence):
    evidence.tools(("iverilog", "vvp"))
    for seed in (1, 17, 89):
        for depth in (1, 2, 3, 16):
            fifo_test(evidence, depth, seed)


L1_SUITES = (
    run_arithmetic, run_fifo, run_controller, run_uart, run_detokenizer,
    run_boot, run_config, run_mapper, run_bpe, run_normalization, run_dfa,
    run_tokenizer, run_numerical, run_parameters, run_adapters, run_memory,
    run_top, run_top_resets, run_synthesis,
    run_metadata,
    lambda evidence: run_mutations(evidence, fifo_test),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", choices=("l1", "clean-reproduction"))
    group.add_argument("--probe", choices=(
        "arithmetic", "fifo", "controller", "uart", "detokenizer", "boot",
        "config", "mapper", "top", "synthesis", "bpe", "mutations", "clean-focus",
        "reproduction",
        "numerical",
        "parameters",
        "storage-faults",
        "adapters",
        "top-uart",
        "memory",
        "boot-boundaries",
        "source-contract",
        "normalization",
        "dfa",
        "tokenizer",
        "numerical-errors",
        "tokenizer-capacity",
        "uart-controls",
        "large-images",
        "top-resets",
        "top-profiles",
        "top-errors",
        "top-reload",
        "storage-edges",
        "schedule",
        "top-profile-uart",
        "top-profile-reload",
        "top-reload-uart",
        "image-upper",
        "simulator-tiering",
        "simulator-compatibility",
        "scheduling-parallel",
        "scheduling-controls",
        "top-interactions",
        "top-token-capacity",
        "official-qwen-discovery",
        "official-qwen-intake",
        "drain-prompts",
        "official-qwen-assets",
        "official-qwen-reference",
        "official-dependency-repair",
        "official-oracle-identity",
        "official-qwen-fragments",
        "official-qwen-regex",
        "official-unicode-sources",
        "unicode-intake",
        "unicode-conversion",
        "unicode-rtl",
        "metadata",
        "official-qwen-integration",
        "official-qwen-boot",
        "official-qwen-shell",
        "official-qwen-shell-general",
    ))
    parser.add_argument("--repair-of", action="append", default=[],
                        help="Project-relative prior preparation receipt; retained, never overwritten")
    parser.add_argument("--schedule-receipt", action="append", default=[],
                        help="Measured preparation receipt for the read-only schedule probe")
    args = parser.parse_args()
    label = args.probe or args.check
    evidence = Evidence(label, preparation=args.probe is not None)
    exit_code, reason = 0, "Advisory unit comparisons passed; not full acceptance"
    try:
        evidence.record["repair_of"] = []
        for name in args.repair_of:
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts or (
                relative.parts[:2] != ("evidence", "preparation")
            ) or relative.name != "receipt.json":
                raise VerificationFailure("repair-of requires a project preparation receipt")
            prior = ROOT / relative
            evidence.record["repair_of"].append(
                {"path": name, "sha256": digest(prior)}
            )
        if args.probe == "arithmetic":
            run_arithmetic(evidence)
        elif args.probe == "fifo":
            run_fifo(evidence)
        elif args.probe == "controller":
            run_controller(evidence)
        elif args.probe == "uart":
            run_uart(evidence)
        elif args.probe == "detokenizer":
            run_detokenizer(evidence)
        elif args.probe == "boot":
            run_boot(evidence)
        elif args.probe == "config":
            run_config(evidence)
        elif args.probe == "mapper":
            run_mapper(evidence)
        elif args.probe == "top":
            run_top(evidence)
        elif args.probe == "top-uart":
            run_top_uart(evidence)
        elif args.probe == "synthesis":
            run_synthesis(evidence)
        elif args.probe == "bpe":
            run_bpe(evidence)
        elif args.probe == "mutations":
            run_mutations(evidence, fifo_test)
        elif args.probe == "clean-focus":
            evidence.tools(("iverilog", "vvp"))
            top_test(evidence)
            run_synthesis(evidence, ("minimum",))
        elif args.probe == "reproduction":
            clean_reproduction(evidence, SELECTORS, digest)
        elif args.probe == "numerical":
            run_numerical(evidence)
        elif args.probe == "parameters":
            run_parameters(evidence)
        elif args.probe == "storage-faults":
            run_storage_faults(evidence)
        elif args.probe == "adapters":
            run_adapters(evidence)
        elif args.probe == "memory":
            run_memory(evidence)
        elif args.probe == "boot-boundaries":
            run_boot_boundaries(evidence)
        elif args.probe == "normalization":
            run_normalization(evidence)
        elif args.probe == "dfa":
            run_dfa(evidence)
        elif args.probe == "tokenizer":
            run_tokenizer(evidence)
        elif args.probe == "numerical-errors":
            run_numerical_errors(evidence)
        elif args.probe == "tokenizer-capacity":
            run_tokenizer_capacity(evidence)
        elif args.probe == "uart-controls":
            run_uart_controls(evidence)
        elif args.probe == "large-images":
            run_large_images(evidence)
        elif args.probe == "top-resets":
            run_top_resets(evidence)
        elif args.probe == "top-profiles":
            run_top_profiles(evidence)
        elif args.probe == "top-errors":
            run_top_errors(evidence)
        elif args.probe == "top-reload":
            run_top_reload(evidence)
        elif args.probe == "top-profile-uart":
            run_top_profile_uart(evidence)
        elif args.probe == "top-profile-reload":
            run_top_profile_reload(evidence)
        elif args.probe == "top-reload-uart":
            top_test(evidence, 17, uart=True, reload_after=True)
        elif args.probe == "image-upper":
            run_watchdog_width(evidence)
            run_image_upper(evidence)
        elif args.probe == "storage-edges":
            run_storage_edges(evidence)
            for fault in ("nonzero-immutable-hole", "metadata-token-capacity",
                          "metadata-pretoken-capacity", "metadata-tag-capacity",
                          "metadata-class-capacity"):
                from storage import boot_test
                boot_test(evidence, 257, 17, fault)
        elif args.probe == "schedule":
            evidence.tools(("python3",))
            evidence.child(
                ["python3", "tests/scheduling.py", *args.schedule_receipt],
                "measured-scheduling-submatrix",
            )
        elif args.probe == "scheduling-parallel":
            scheduling_probe(evidence)
        elif args.probe == "scheduling-controls":
            scheduling_controls(evidence)
        elif args.probe == "top-interactions":
            run_top_interactions(evidence)
        elif args.probe == "top-token-capacity":
            run_top_token_capacity(evidence)
        elif args.probe == "official-qwen-discovery":
            run_official_discovery(evidence)
        elif args.probe == "official-qwen-intake":
            run_official_intake(evidence)
        elif args.probe == "drain-prompts":
            run_drain_prompts(evidence)
        elif args.probe == "official-qwen-assets":
            run_official_assets(evidence)
        elif args.probe == "official-qwen-reference":
            run_official_checkpoint(evidence)
        elif args.probe == "official-dependency-repair":
            run_official_environment(evidence)
        elif args.probe == "official-oracle-identity":
            run_official_identity(evidence)
            run_official_checkpoint(evidence)
        elif args.probe == "official-qwen-fragments":
            run_qwen_fragments(evidence)
        elif args.probe == "official-qwen-regex":
            run_qwen_regex(evidence)
        elif args.probe == "official-unicode-sources":
            run_unicode_sources(evidence)
        elif args.probe == "unicode-intake":
            run_unicode_intake(evidence)
        elif args.probe == "unicode-conversion":
            run_unicode_conversion(evidence)
        elif args.probe == "unicode-rtl":
            run_unicode_rtl(evidence)
        elif args.probe == "metadata":
            run_metadata(evidence)
        elif args.probe == "official-qwen-integration":
            run_qwen_integration(evidence)
        elif args.probe == "official-qwen-boot":
            run_qwen_boot(evidence)
        elif args.probe == "official-qwen-shell":
            run_qwen_shell(evidence)
        elif args.probe == "official-qwen-shell-general":
            run_qwen_shell(evidence, general_only=True)
        elif args.probe == "simulator-tiering":
            bench = UART.replace("DIVISOR", "4").replace("@DEPTH@", "1").replace("SEED", "1")
            for simulator in ("iverilog", "verilator"):
                evidence.simulate("uart-tiering-" + simulator, bench, [
                    "rtl/anvil_edge_fifo.sv", "rtl/anvil_edge_uart_io.sv",
                ], 78, simulator=simulator)
            top_test(evidence, 89, uart=True, startup_only=True)
            top_test(evidence, 89, uart=True)
            top_test(evidence, 17, uart=True)
        elif args.probe == "simulator-compatibility":
            from protocol import controller_test, detokenizer_test
            from storage import boot_test, mapper_test, synthetic_image
            from text import normalizer_test, dfa_test, tokenizer_test
            from numerics import core_test, Geometry
            from adapters import adapter_test

            controller_test(evidence, 3, 17)
            detokenizer_test(evidence, 17, "split-tiering", [b"\xe4", b"\xb8\xad"])
            for vocabulary in (256, 257, 1, 255):
                boot_test(evidence, vocabulary, 17, reload=vocabulary == 257)
            run_config(evidence)
            mapper_test(evidence, synthetic_image(257))
            normalizer_test(evidence, 17, "tiering", "e\u0301", 1)
            dfa_test(evidence, 17, "longest")
            tokenizer_test(evidence, 17, "tiering", "ABC e\u0301", mode=1, bos=True)
            core_test(evidence, Geometry(layers=2, hidden=16, intermediate=24, query_heads=2), 17)
            adapter_test(evidence, 4, 257, 17)
            run_memory(evidence)
            top_test(evidence, 17, reset_phase="prefill")
        elif args.probe == "source-contract":
            evidence.tools(("python3",), timeout=300)
            evidence.child(["python3", "tests/scheduling.py", "--source-contract"],
                           "source-contract", timeout=3600)
        elif args.check == "l1":
            evidence.tools(("iverilog", "vvp", "yosys"))
            evidence.run_cases((f"suite-{index}-{suite.__name__}", suite)
                               for index, suite in enumerate(L1_SUITES))
            run_qwen_fragments(evidence)
            run_qwen_regex(evidence)
            run_unicode_rtl(evidence)
            run_official_checkpoint(evidence)
            run_qwen_integration(evidence)
            run_qwen_boot(evidence)
            run_qwen_shell(evidence)
            raise VerificationFailure(
                "L1 incomplete: tests/data/requirements.json lists remaining mandatory "
                "coverage; exact official-profile conversion/RTL boot/tokenization and "
                "real-model integrations remain incomplete. "
                "Unit results cannot certify the production appliance."
            )
        else:
            clean_reproduction(evidence, SELECTORS, digest)
            reason = "Focused fresh-source autonomous inference and production synthesis passed; full product acceptance remains separate"
    except VerificationFailure as error:
        exit_code, reason = 1, str(error)
    except Exception as error:
        exit_code, reason = 1, f"Harness error: {type(error).__name__}: {error}"
        (evidence.path / "harness-error.log").write_text(
            __import__("traceback").format_exc(), encoding="utf-8",
        )
    return evidence.finish(exit_code, reason)


if __name__ == "__main__":
    sys.exit(main())
