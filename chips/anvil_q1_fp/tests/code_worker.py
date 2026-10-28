"""Trusted one-case worker: may execute only in the qualified isolated container."""

import base64
import contextlib
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import socket
import sys


POLICY = "anvil-humaneval-isolated-v1"


def isolation():
    if not Path("/.dockerenv").is_file() or os.getuid() != 65534:
        raise RuntimeError("code worker requires the qualified non-root container")
    status = Path("/proc/self/status").read_text()
    if ("CapEff:\t0000000000000000" not in status or "NoNewPrivs:\t1" not in status or
            socket.if_nameindex() != [(1, "lo")]):
        raise RuntimeError("capability, privilege or network isolation differs")
    if Path("/data/sufeng").exists() or Path("/home").is_mount():
        raise RuntimeError("unexpected host filesystem visibility")
    try:
        with open("/anvil-write-probe", "x"):
            pass
    except OSError as error:
        if error.errno not in (13, 30):
            raise
    else:
        raise RuntimeError("container root filesystem is writable")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_AS, (384 * 1024 * 1024, 384 * 1024 * 1024))


def evaluate(payload):
    source = (payload["prompt"] + payload["completion"] + "\n" + payload["test"] +
              "\ncheck(" + payload["entry_point"] + ")\n")
    if not payload["entry_point"].isidentifier():
        raise ValueError("invalid HumanEval entry point")

    def expired(_signal, _frame):
        raise TimeoutError("HumanEval three-second case limit")

    handler = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 3)
    passed, error = False, None
    # Candidate output is not an evaluator protocol and cannot count as a pass.
    with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        try:
            namespace = {}
            exec(compile(source, "<isolated-humaneval>", "exec"), namespace)
            passed = True
        except BaseException as caught:
            error = type(caught).__name__
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, handler)
    return {
        "schema": 1, "case": payload["case"], "decode_sha256": payload["decode_sha256"],
        "passed": passed, "error": error, "policy": POLICY, "isolated": True,
        "program_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
    }


def main():
    isolation()
    if len(sys.argv) != 2:
        raise ValueError("worker requires exactly one encoded case")
    payload = json.loads(base64.b64decode(sys.argv[1], validate=True))
    print(json.dumps(evaluate(payload), sort_keys=True))


if __name__ == "__main__":
    main()
