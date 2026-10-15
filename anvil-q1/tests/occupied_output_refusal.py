#!/usr/bin/env python3
"""Implementation-only regression source; execute only after focused admission."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 10


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def inventory(root):
    entries = {}

    def visit(path):
        info = path.lstat()
        record = dict(mode=info.st_mode, inode=info.st_ino,
                      mtime_ns=info.st_mtime_ns)
        if stat.S_ISLNK(info.st_mode):
            record.update(kind="symlink", target=os.readlink(path))
        elif stat.S_ISDIR(info.st_mode):
            record["kind"] = "directory"
        elif stat.S_ISREG(info.st_mode):
            data = path.read_bytes()
            record.update(kind="file", size=len(data), bytes_hex=data.hex(),
                          sha256=hashlib.sha256(data).hexdigest())
        else:
            record["kind"] = "other"
        entries[str(path.relative_to(root))] = record
        if record["kind"] == "directory":
            for child in sorted(path.iterdir()):
                visit(child)

    if not os.path.lexists(root):
        return {".": {"kind": "missing"}}
    visit(root)
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    # Do not resolve the leaf: an occupied dangling symlink must also be refused.
    out = Path(os.path.abspath(args.out))
    parent = out.parent.resolve()
    allowed = (ROOT / "evidence/preparation").resolve()
    if parent != allowed:
        parser.error("--out must be a direct child of project evidence/preparation")
    out = parent / out.name
    try:
        out.mkdir(exist_ok=False)
    except FileExistsError:
        parser.exit(2, f"error: refusing occupied regression destination: {out}\n")

    receipt = dict(name="occupied-output-refusal", outcome="fail",
                   argv=["python3", *sys.argv], cwd=str(ROOT),
                   start_time=utc(), timeout_s=TIMEOUT,
                   scope="placeholder fixture only; no accelerator acceptance")
    tick = time.monotonic()
    fixture = out / "OCCUPIED-FIXTURE-PLACEHOLDERS-NOT-ACCEPTANCE"
    process = None
    try:
        receipt["source_sha256"] = {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for pattern in ("rtl/*.sv", "tests/*.py", "design/*.md",
                            "hf_qwen25_05b_awq_spec/*.json")
            for path in sorted(ROOT.glob(pattern))}
        receipt["python"] = dict(executable=sys.executable, version=sys.version)
        fixture.mkdir()
        (fixture / "PLACEHOLDER.txt").write_bytes(
            b"PLACEHOLDER ONLY - never acceptance evidence\n")
        (fixture / "nested").mkdir()
        (fixture / "nested/sentinel.bin").write_bytes(bytes(range(256)))
        (fixture / "empty-placeholder").mkdir()
        (fixture / "dangling-placeholder").symlink_to("absent-placeholder")
        before = inventory(fixture)
        save(out / "fixture-before.json", before)

        support = out / "tripwires"
        support.mkdir()
        audit_log = out / "subprocess-tripwire.jsonl"
        tool_log = out / "tool-tripwire.log"
        armed = out / "audit-hook-armed.txt"
        # Audit interception also covers absolute tool paths, unlike PATH alone.
        hook = support / "sitecustomize.py"
        hook.write_text(
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "Path(os.environ['REFUSAL_AUDIT_ARMED']).write_text('armed\\n')\n"
            "def deny(event, args):\n"
            "    if event in ('subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn'):\n"
            "        with open(os.environ['REFUSAL_AUDIT_LOG'], 'a') as stream:\n"
            "            stream.write(json.dumps({'event': event, 'args': repr(args)})+'\\n')\n"
            "        raise RuntimeError('occupied-output regression subprocess tripwire')\n"
            "sys.addaudithook(deny)\n")
        tool_text = (
            "#!" + sys.executable + "\n"
            "import os, sys\n"
            "with open(os.environ['REFUSAL_TOOL_LOG'], 'a') as stream:\n"
            "    stream.write(repr(sys.argv)+'\\n')\n"
            "sys.exit(97)\n")
        for name in ("iverilog", "iverilog12", "iverilog13", "iverilog-12",
                     "iverilog-13", "vvp", "vvp12", "vvp13", "yosys", "timeout"):
            path = support / name
            path.write_text(tool_text)
            path.chmod(0o755)
        receipt["tripwire_sha256"] = {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(support.iterdir())}
        env = dict(os.environ, PATH=str(support) + os.pathsep + os.environ.get("PATH", ""),
                   PYTHONPATH=str(support), PYTHONDONTWRITEBYTECODE="1",
                   REFUSAL_AUDIT_ARMED=str(armed), REFUSAL_AUDIT_LOG=str(audit_log),
                   REFUSAL_TOOL_LOG=str(tool_log))
        receipt["environment_overrides"] = {key: env[key] for key in
            ("PATH", "PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "REFUSAL_AUDIT_ARMED",
             "REFUSAL_AUDIT_LOG", "REFUSAL_TOOL_LOG")}
        argv = ["python3", "tests/verify.py", "--check", "behavior", "--out",
                str(fixture.relative_to(ROOT))]
        receipt["command"] = dict(argv=argv, cwd=str(ROOT), start_time=utc(),
                                  timeout_s=TIMEOUT, timed_out=False)
        command_tick = time.monotonic()
        with (out / "cli.stdout").open("xb") as stdout, (
                out / "cli.stderr").open("xb") as stderr:
            process = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=stdout,
                                       stderr=stderr, start_new_session=True)
            try:
                process.wait(timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                receipt["command"]["timed_out"] = True
            finally:
                # Settle this one invocation's group, including a failing child's descendants.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=2)
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            settled = True
        else:
            settled = False
        receipt["command"].update(
            end_time=utc(), elapsed_s=time.monotonic()-command_tick,
            exit_code=process.returncode, process_group_settled=settled,
            stdout_path=str((out / "cli.stdout").relative_to(ROOT)),
            stderr_path=str((out / "cli.stderr").relative_to(ROOT)))
        after = inventory(fixture)
        save(out / "fixture-after.json", after)
        receipt["fixture_comparison"] = dict(
            fixture=str(fixture.relative_to(ROOT)),
            before=str((out / "fixture-before.json").relative_to(ROOT)),
            after=str((out / "fixture-after.json").relative_to(ROOT)),
            includes="Complete recursive inventory, modes, identities, mtimes, "
                     "symlink targets and every regular file's bytes and SHA256")
        checks = dict(
            explicit_refusal=(
                b"error: refusing occupied output destination:" in
                (out / "cli.stderr").read_bytes()),
            exit_is_refusal=process.returncode == 2,
            no_timeout=not receipt["command"]["timed_out"],
            process_group_settled=settled,
            fixture_inventory_and_bytes_unchanged=before == after,
            audit_hook_armed=armed.is_file() and armed.read_bytes() == b"armed\n",
            no_subprocess_invocation=not audit_log.exists(),
            no_tool_invocation=not tool_log.exists(),
            empty_stdout=(out / "cli.stdout").read_bytes() == b"")
        receipt["checks"] = checks
        receipt["tripwire_logs"] = dict(
            subprocess=str(audit_log.relative_to(ROOT)),
            tools=str(tool_log.relative_to(ROOT)),
            interpretation="Absent logs mean no invocation; armed marker is mandatory.")
        if not all(checks.values()):
            raise AssertionError(f"occupied-output refusal checks failed: {checks}")
        receipt["outcome"] = "pass"
    except (AssertionError, OSError, ValueError, subprocess.SubprocessError) as exc:
        receipt["diagnosis"] = str(exc)
        print(str(exc), file=sys.stderr)
    finally:
        receipt.update(end_time=utc(), elapsed_s=time.monotonic()-tick)
        save(out / "receipt.json", receipt)
    return 0 if receipt["outcome"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
