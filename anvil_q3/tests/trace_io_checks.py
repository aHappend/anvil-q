"""Advisory simulator trace-I/O fault injection, not numerical acceptance.

Run from the project root: python3 tests/trace_io_checks.py
The file-size limit applies only to a disposable simulator child, never the
shared runtime, source files, or prior evidence.
"""

import argparse
import os
from pathlib import Path
import re
import resource
import signal
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, Run


def check(run):
    run.versions([("python3", "--version"), ("iverilog", "-V"),
                  ("vvp", "-V"), ("verilator", "--version")])
    source = (ROOT / "tests/top_tb.sv").read_text()
    tasks = re.findall(r"  task automatic check_trace_io;.*?  endtask", source, re.S)
    if len(tasks) != 1:
        raise AssertionError("missing/ambiguous decoder trace-I/O task")
    bench = run.path / "trace_io_tb.sv"
    bench.write_text(
        "module trace_io_tb;\n"
        "  integer trace_fd, i;\n"
        "  reg [1023:0] trace_io_message;\n"
        "  string output_path;\n" + tasks[0] + "\n"
        "  initial begin\n"
        '    if (!$value$plusargs("output=%s",output_path)) $fatal(1,"missing output");\n'
        '    trace_fd=$fopen(output_path,"w");\n'
        '    if (trace_fd==0) $fatal(1,"open failed");\n'
        '    for (i=0;i<8192;i=i+1) $fwrite(trace_fd,"x");\n'
        "    check_trace_io();\n"
        "    $fclose(trace_fd);\n"
        '    $display("TRACE_IO_HEALTHY");\n'
        "    $finish;\n"
        "  end\n"
        "endmodule\n")
    results = []
    for simulator in ("iverilog", "verilator"):
        if simulator == "iverilog":
            binary = run.path / "trace_io.vvp"
            run.tool(["iverilog", "-g2012", "-Wall", "-s", "trace_io_tb",
                      "-o", run.rel(binary), run.rel(bench)])
            command = ["vvp", run.rel(binary)]
        else:
            obj = run.path / "obj"
            run.tool(["verilator", "--binary", "--timing", "--assert",
                      "--top-module", "trace_io_tb", "--Mdir", run.rel(obj),
                      "-o", "trace_io", run.rel(bench)])
            command = [run.rel(obj / "trace_io")]
        healthy = run.path / (simulator + "-healthy.tsv")
        text, good = run.tool(command + ["+output=" + run.rel(healthy)])
        if "TRACE_IO_HEALTHY" not in text or healthy.read_bytes() != b"x" * 8192:
            raise AssertionError("healthy simulator file output changed")
        limited = run.path / (simulator + "-limited.tsv")
        text, bad = run.tool(
            ["python3", "tests/trace_io_checks.py", "--limited-exec",
             *command, "+output=" + run.rel(limited)], expected=(1, -6))
        if ("TRACE_IO write/flush failed" not in text or
                "TRACE_IO_HEALTHY" in text or limited.stat().st_size != 1024):
            raise AssertionError("simulator did not reject the injected trace write failure")
        results.append({"simulator": simulator, "healthy_bytes": 8192,
                        "injected_limit_bytes": 1024,
                        "healthy_receipt": good, "rejected_io_receipt": bad})
    return {"cases": results, "scope": "isolated copied decoder I/O task only; "
            "no causal attribution of historical trace loss or runtime persistence certification"}


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--limited-exec":
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE, (1024, 1024))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        os.execvp(sys.argv[2], sys.argv[2:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run = Run("evidence/preparation/independent-trace-io",
              "simulator trace write error sensitivity", repair_of=args.repair_of)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        result = check(run)
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    run.finish("passed", result=result)


if __name__ == "__main__":
    main()
