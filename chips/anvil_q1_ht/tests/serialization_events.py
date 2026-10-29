#!/usr/bin/env python3
"""Bounded scheduler-free save/restore capability experiment, not campaign admission.

python3 -B tests/serialization_events.py --build-only
New per-evaluation raw driver responses are retained losslessly as
driver-stdout.log.gz; decompress with gzip -dc to inspect the complete stream.
"""

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from experiments import top_probe
from reference import MATRIX
from verify import Evidence, ROOT, file_sha256


INPUTS = {
    "clk": 1, "ddr_clk": 1, "rst_n": 1, "token_valid": 1,
    "token_id": 32, "token_pos": 32, "new_sequence": 1, "logit_ready": 1,
    "csr_valid": 1, "csr_write": 1, "csr_address": 16, "csr_wdata": 32,
    "csr_rsp_ready": 1, "load_valid": 1, "load_address": 33, "load_data": 512,
    "load_byteenable": 64, "load_last": 1, "avm_waitrequest": 1,
    "avm_readdata": 512, "avm_readdatavalid": 1, "avm_response": 2,
    "avm_writeresponsevalid": 1,
}
OUTPUTS = {
    "token_ready": 1, "logit_valid": 1, "logit_index": 32, "logit_data": 32,
    "done": 1, "error": 1, "csr_ready": 1, "csr_rsp_valid": 1,
    "csr_rdata": 32, "csr_error": 1, "load_ready": 1, "load_done": 1,
    "load_error": 1, "avm_address": 33, "avm_burstcount": 8, "avm_read": 1,
    "avm_write": 1, "avm_writedata": 512, "avm_byteenable": 64,
}

PARAMETER_FIELDS = {
    "NUM_LAYERS": "layers", "HIDDEN_SIZE": "hidden",
    "INTERMEDIATE_SIZE": "intermediate", "NUM_Q_HEADS": "qheads",
    "NUM_KV_HEADS": "kvheads", "HEAD_DIM": "head_dim",
    "GROUP_SIZE": "group", "VOCAB_SIZE": "vocab", "MAX_SEQ_LEN": "max_seq",
    "TILE_BEATS": "tile", "KV_WINDOW": "window",
}


def parameters(config):
    shape = MATRIX[config]
    return {name: getattr(shape, field) for name, field in PARAMETER_FIELDS.items()}


def binding(spec):
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()

TRACE = r"""
always @(posedge clk) if(rst_n) begin
 if(token_valid && token_ready)
  $display("EVENT TOKEN %0.0f %h %h %h",$realtime/1ps,token_id,token_pos,new_sequence);
 if(csr_valid && csr_ready)
  $display("EVENT CSR %0.0f %h %h %h",$realtime/1ps,csr_write,csr_address,csr_wdata);
 if(csr_rsp_valid && csr_rsp_ready)
  $display("EVENT CSR_RSP %0.0f %h %h",$realtime/1ps,csr_rdata,csr_error);
 if(logit_valid && logit_ready)
  $display("EVENT LOGIT %0.0f %h %h",$realtime/1ps,logit_index,logit_data);
end
always @(posedge clk) begin
 #0.001;
 if(rst_n && done) $display("EVENT DONE %0.0f %h",$realtime/1ps,error);
end
always @(posedge ddr_clk) if(rst_n) begin
 if(load_valid && load_ready)
  $display("EVENT LOAD %0.0f %h %h %h %h",
           $realtime/1ps,load_address,load_data,load_byteenable,load_last);
 if(avm_read && !avm_waitrequest)
  $display("EVENT READ %0.0f %h %h %h",
           $realtime/1ps,avm_address,avm_burstcount,avm_byteenable);
 if(avm_write && !avm_waitrequest)
  $display("EVENT WRITE %0.0f %h %h %h %h",
           $realtime/1ps,avm_address,avm_burstcount,avm_writedata,avm_byteenable);
 if(avm_readdatavalid)
  $display("EVENT READ_RSP %0.0f %h %h",$realtime/1ps,avm_readdata,avm_response);
 if(avm_writeresponsevalid)
  $display("EVENT WRITE_RSP %0.0f %h",$realtime/1ps,avm_response);
end
"""


def canonical_events(text):
    rows = []
    for line in text.splitlines():
        if line.startswith("EVENT "):
            _, kind, when, *values = line.split()
            rows.append([kind, int(when), *[int(value, 16) for value in values]])
    return rows


def counters(text):
    rows = []
    for line in text.splitlines():
        if line.startswith(("TOKEN_COMPARED ", "CHECKS_PASSED top ")):
            rows.append(dict(re.findall(r"(\w+)=([^\s]+)", line)))
    return rows


def write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def project_path(relative):
    path = ROOT / relative
    if Path(relative).is_absolute() or not path.resolve().is_relative_to(ROOT):
        raise ValueError("capability artifacts must be project-relative")
    return path


class Driver:
    def __init__(self, executable, folder):
        self.stderr = (folder / "driver-stderr.log").open("xb")
        self.stdout_path = folder / "driver-stdout.log.gz"
        self.stdout = gzip.open(self.stdout_path, "xt")
        self.stdout_digest = hashlib.sha256()
        self.stdout_bytes = 0
        self.process = subprocess.Popen(
            [str(project_path(executable))], cwd=ROOT, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=self.stderr, text=True, bufsize=1)
        self.last_evaluation = None

    def request(self, text):
        self.process.stdin.write(text + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        self.stdout.write(line)
        raw = line.encode()
        self.stdout_digest.update(raw)
        self.stdout_bytes += len(raw)
        if not line:
            raise RuntimeError(f"driver stopped during {text.split()[0]}")
        return line.strip()

    def evaluate(self, time, pins):
        identity = (time, tuple(pins.items()))
        if self.last_evaluation is not None and self.last_evaluation[0] == identity:
            return dict(self.last_evaluation[1])
        words = [time]
        for name, width in INPUTS.items():
            value = pins[name]
            if width > 64:
                words.extend((value >> (32 * i)) & 0xffffffff
                             for i in range((width + 31) // 32))
            else:
                words.append(value)
        reply = [int(value, 16) for value in self.request(
            "E " + " ".join(f"{word:x}" for word in words)).split()]
        if not reply or reply.pop(0) != time:
            raise RuntimeError("driver returned wrong event time")
        outputs = {}
        for name, width in OUTPUTS.items():
            count = (width + 31) // 32 if width > 64 else 1
            if len(reply) < count:
                raise RuntimeError("driver returned short observation")
            outputs[name] = sum(reply.pop(0) << (32 * i) for i in range(count))
        if reply:
            raise RuntimeError("driver returned extra observation")
        self.last_evaluation = (identity, dict(outputs))
        return outputs

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.write("Q\n")
            self.process.stdin.flush()
        self.process.stdin.close()
        try:
            code = self.process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            raise RuntimeError("driver failed to settle")
        finally:
            try:
                self.stdout.close()
            finally:
                self.stderr.close()
        if code != 0:
            raise RuntimeError(f"driver exit {code}")


class Controller:
    """Explicit event/state machine; no generator, coroutine or replay state."""

    def __init__(self, spec, driver, folder, restored=None):
        self.spec, self.driver = spec, driver
        self.trace = (folder / "events.log").open("x")
        self.folder = folder
        if restored is not None:
            self.s = restored
        else:
            self.s = {
                "time": 0, "next_core": 5000, "next_ddr": 1875,
                "pins": {name: 0 for name in INPUTS}, "outputs": {},
                "memory": [0] * (spec["capacity"] + 64),
                "outstanding": 0, "cursor": 0, "response_writes": 0,
                "reads": 0, "writes": 0, "load_accepts": 0, "csr_compares": 0,
                "logits": 0, "ddr_cycles": 0, "reset_checks": 0,
                "core_edges": 0, "ddr_edges": 0, "simultaneous_events": 0,
                "held_payload": None, "op": 0, "phase": 0, "v": {},
                "wait": None, "due": None, "pending_post": False,
                "rng_state": random.Random(spec["seed"]).getstate(),
                "checkpoint_categories": [], "token_rows": [], "complete": False,
                "last_read_address": None, "response_address": None,
                "last_response_boundary": False, "stall_samples": 0,
                "cache_written_addresses": [], "cold_read_witnesses": 0,
                "cold_response": False, "controller_ticks": 0,
            }
        self.program = [
            ("edges", 6), ("release",), ("edges", 150), ("check_uncommitted",),
            ("csr", 0, 0, 0, 0, 0x02000001),
            ("csr", 0, 0x14, 0, 1, 0), ("csr", 0, 0x40, 0, 1, 0),
            ("csr", 1, 8, 4, 0, 0), ("upload",),
            ("csr", 1, 0xc, int(spec["mode"] == "BF16"), 0, 0),
            *[("csr", 1, word >> 32, word & 0xffffffff, 0, 0)
              for word in spec["descriptor_words"]],
            ("csr", 1, 8, 2, 0, 0), ("edges", 30), ("check_committed",),
            *[("token", *token) for token in spec["tokens"]], ("finish",),
        ]

    def require(self, condition, message):
        if not condition:
            raise AssertionError(
                f"{message} time={self.s['time']} op={self.s['op']} phase={self.s['phase']}")

    def event(self, kind, *values):
        self.trace.write("EVENT " + kind + " " + str(self.s["time"]) +
                         "".join(f" {value:x}" for value in values) + "\n")

    def wait(self, kind, phase, delay=0):
        self.s.update(wait=kind, phase=phase, due=None)
        if kind == "delta":
            self.s.update(wait=None, due=self.s["time"] + 1)
        elif delay:
            self.s["wait"] = kind + "+"

    def edge(self, phase):
        self.wait("cp", phase, 1)

    def next_operation(self):
        self.s.update(op=self.s["op"] + 1, phase=0, v={}, wait=None, due=None)

    def advance(self):
        s, p, o, v = self.s, self.s["pins"], self.s["outputs"], self.s["v"]
        while s["wait"] is None and s["due"] is None and not s["complete"]:
            op, *args = self.program[s["op"]]
            phase = s["phase"]
            if op == "edges":
                if phase == 0:
                    v["left"] = args[0]
                else:
                    v["left"] -= 1
                if v["left"]:
                    self.edge(1)
                else:
                    self.next_operation()
            elif op == "release":
                if phase == 0:
                    self.wait("cn", 1)
                else:
                    p["rst_n"] = 1
                    self.next_operation()
            elif op in ("check_uncommitted", "check_committed"):
                self.require(o["token_ready"] == int(op == "check_committed"),
                             "COMMITTED_IMAGE_READINESS")
                self.next_operation()
            elif op == "csr":
                wr, address, data, expected_error, expected_data = args
                if phase == 0:
                    self.wait("cn", 1)
                elif phase == 1:
                    p.update(csr_valid=1, csr_write=wr, csr_address=address, csr_wdata=data)
                    v["wait_cycles"] = 0
                    s["phase"] = 2
                elif phase == 2:
                    if o["csr_ready"] != 1 and v["wait_cycles"] < 10000:
                        self.edge(3)
                    else:
                        self.require(o["csr_ready"] == 1, "CSR_ACCEPT_NOT_PROGRESSING")
                        self.edge(4)
                elif phase == 3:
                    v["wait_cycles"] += 1
                    self.wait("cn", 2)
                elif phase == 4:
                    self.require(o["csr_rsp_valid"] == 0, "CSR_RESPONSE_TOO_EARLY")
                    self.wait("cn", 5)
                elif phase == 5:
                    p["csr_valid"] = 0
                    v["wait_cycles"] = 0
                    s["phase"] = 6
                elif phase == 6:
                    if o["csr_rsp_valid"] != 1 and v["wait_cycles"] < 10000:
                        self.edge(7)
                    else:
                        self.require(
                            o["csr_rsp_valid"] == 1 and o["csr_error"] == expected_error and
                            (wr or o["csr_rdata"] == expected_data), "CSR_MISMATCH")
                        v.update(held_data=o["csr_rdata"], stall=0)
                        self.edge(8)
                elif phase == 7:
                    v["wait_cycles"] += 1
                    s["phase"] = 6
                elif phase == 8:
                    self.require(
                        o["csr_rsp_valid"] == 1 and o["csr_rdata"] == v["held_data"] and
                        o["csr_error"] == expected_error and o["csr_ready"] == 0,
                        "CSR_STALL_OR_OUTSTANDING")
                    v["stall"] += 1
                    if v["stall"] < 3:
                        self.edge(8)
                    else:
                        self.wait("cn", 9)
                elif phase == 9:
                    p["csr_rsp_ready"] = 1
                    self.edge(10)
                elif phase == 10:
                    self.require(o["csr_rsp_valid"] == 0, "CSR_RETIRE")
                    self.wait("cn", 11)
                else:
                    p["csr_rsp_ready"] = 0
                    s["csr_compares"] += 1
                    self.next_operation()
            elif op == "upload":
                if phase == 0:
                    v["beat"] = 0
                    self.wait("dn", 1)
                elif phase == 1:
                    p.update(load_valid=1, load_last=int(v["beat"] == len(self.spec["image"]) - 1),
                             load_address=v["beat"] * 64, load_data=self.spec["image"][v["beat"]],
                             load_byteenable=(1 << 64) - 1)
                    v["waiting"] = 0
                    self.wait("delta", 2)
                elif phase == 2:
                    if o["load_ready"] != 1 and v["waiting"] < 10000:
                        self.wait("dp", 3, 1)
                    else:
                        self.require(o["load_ready"] == 1, "LOAD_NOT_PROGRESSING")
                        self.wait("dp", 5, 1)
                elif phase == 3:
                    self.wait("dn", 4, 1)
                elif phase == 4:
                    v["waiting"] += 1
                    s["phase"] = 2
                elif phase == 5:
                    self.require(o["load_error"] == 0, "LOAD_UNEXPECTED_ERROR")
                    self.wait("dn", 6)
                elif phase == 6:
                    p["load_valid"] = 0
                    v["beat"] += 1
                    if v["beat"] < len(self.spec["image"]):
                        self.wait("dn", 1)
                    else:
                        v["waiting"] = 0
                        s["phase"] = 7
                elif phase == 7:
                    if o["load_done"] != 1 and v["waiting"] < 10000:
                        self.wait("dp", 8, 1)
                    else:
                        self.require(
                            o["load_done"] == 1 and o["load_error"] == 0 and
                            s["writes"] == len(self.spec["image"]) and
                            s["load_accepts"] == s["writes"], "LOAD_ACK_OR_CONSERVATION")
                        self.require(s["memory"][:len(self.spec["image"])] == self.spec["image"],
                                     "PRELOAD_MEMORY_MISMATCH")
                        v["remaining"] = 30
                        self.edge(9)
                elif phase == 8:
                    v["waiting"] += 1
                    s["phase"] = 7
                else:
                    v["remaining"] -= 1
                    if v["remaining"]:
                        self.edge(9)
                    else:
                        self.next_operation()
            elif op == "token":
                token_id, position, sequence_start, expected = args
                if phase == 0:
                    self.wait("cn", 1)
                elif phase == 1:
                    p.update(token_id=token_id, token_pos=position,
                             new_sequence=int(sequence_start), token_valid=1)
                    self.require(o["token_ready"] == 1, "TOKEN_NOT_READY_ON_START")
                    self.edge(2)
                elif phase == 2:
                    self.require(o["token_ready"] == 0 and o["logit_valid"] == 0,
                                 "TOKEN_ACCEPT_EDGE")
                    self.wait("cn", 3)
                elif phase == 3:
                    p.update(token_valid=0, logit_ready=0)
                    v.update(cycles=0, token_logits=0, final_stalls=0)
                    self.wait("cn", 4)
                elif phase == 4:
                    p["logit_ready"] = int(v["cycles"] % 11 > 3)
                    if (o["logit_valid"] and o["logit_index"] == len(expected) - 1
                            and v["final_stalls"] < 31):
                        p["logit_ready"] = 0
                        v["final_stalls"] += 1
                    self.wait("delta", 5)
                elif phase == 5:
                    v.update(pre_valid=o["logit_valid"], pre_index=o["logit_index"],
                             pre_data=o["logit_data"],
                             pre_transfer=o["logit_valid"] and p["logit_ready"])
                    if o["logit_valid"]:
                        self.require(
                            o["logit_index"] == v["token_logits"] and
                            o["logit_data"] == (expected[v["token_logits"]] & 0xffffffff),
                            "TOP_LOGIT_MISMATCH")
                    self.edge(6)
                elif phase == 6:
                    if v["pre_valid"] and not v["pre_transfer"]:
                        self.require(o["logit_valid"] == 1 and o["logit_index"] == v["pre_index"]
                                     and o["logit_data"] == v["pre_data"],
                                     "TOP_STALLED_LOGIT_CHANGED")
                    if v["pre_transfer"]:
                        v["token_logits"] += 1
                        if v["token_logits"] == len(expected):
                            self.require(o["done"] == 1 and o["error"] == 0,
                                         "TOP_FINAL_LOGIT_COMPLETION")
                    if v["token_logits"] < len(expected):
                        self.require(o["done"] == 0, "TOP_EARLY_OR_ERROR_COMPLETION")
                    v["cycles"] += 1
                    if v["token_logits"] < len(expected):
                        self.wait("cn", 4)
                    else:
                        self.require(v["token_logits"] == len(expected) and s["reads"] > 0 and
                                     v["final_stalls"] == 31, "TOP_MISSING_LOGITS_DDR_OR_FINAL_STALL")
                        self.edge(7)
                else:
                    self.require(o["done"] == 0 and o["error"] == 0 and
                                 s["load_accepts"] == len(self.spec["image"]),
                                 "TOP_COMPLETION_OR_REUPLOAD")
                    s["logits"] += v["token_logits"]
                    line = (
                        f"TOKEN_COMPARED mode={self.spec['mode']} position={position} "
                        f"new_sequence={int(sequence_start)} logits={v['token_logits']} "
                        f"cycles={v['cycles']} reads={s['reads']}")
                    print(line, flush=True)
                    s["token_rows"].append(line)
                    self.next_operation()
            elif op == "finish":
                print(f"CHECKS_PASSED top mode={self.spec['mode']} logits={s['logits']} "
                      f"reads={s['reads']} preload_beats={s['load_accepts']} "
                      f"csr_compares={s['csr_compares']}", flush=True)
                s["complete"] = True
            else:
                raise RuntimeError("unknown controller operation")
            v = s["v"]

    def ddr_negative(self):
        s, p = self.s, self.s["pins"]
        s["last_response_boundary"] = False
        s["cold_response"] = False
        if not p["rst_n"]:
            p.update(avm_readdatavalid=0, avm_writeresponsevalid=0, avm_readdata=0,
                     avm_waitrequest=0, avm_response=0)
            s.update(outstanding=0, ddr_cycles=0, held_payload=None)
            return
        p.update(avm_readdatavalid=0, avm_writeresponsevalid=0, avm_response=0)
        s["response_address"] = None
        if s["outstanding"] > 0:
            p.update(avm_readdatavalid=1, avm_readdata=s["memory"][s["cursor"]])
            s["response_address"] = s["cursor"] * 64
            s["cursor"] += 1
            s["outstanding"] -= 1
            s["last_response_boundary"] = s["outstanding"] == 0
            op = self.program[s["op"]]
            address = s["response_address"]
            s["cold_response"] = (
                op[0] == "token" and op[2] >= self.spec["shape"]["window"] and
                address in s["cache_written_addresses"] and
                any(base <= address < base + length
                    for base, length in self.spec["cache_regions"]))
        if s["writes"] > s["response_writes"]:
            p["avm_writeresponsevalid"] = 1
            s["response_writes"] = s["writes"]
        s["ddr_cycles"] += 1

    def ddr_positive(self):
        s, p, o = self.s, self.s["pins"], self.s["outputs"]
        if not p["rst_n"]:
            return
        if p["load_valid"] and o["load_ready"]:
            s["load_accepts"] += 1
            self.event("LOAD", p["load_address"], p["load_data"],
                       p["load_byteenable"], p["load_last"])
        payload = [o[name] for name in ("avm_address", "avm_burstcount", "avm_read",
                                       "avm_write", "avm_writedata", "avm_byteenable")]
        self.require(s["held_payload"] is None or s["held_payload"] == payload,
                     "AVALON_COMMAND_CHANGED_DURING_STALL")
        s["held_payload"] = payload if (o["avm_read"] or o["avm_write"]) and p["avm_waitrequest"] else None
        address, count = o["avm_address"], o["avm_burstcount"]
        if o["avm_read"] and not p["avm_waitrequest"]:
            self.require(
                s["outstanding"] == 0 and 1 <= count <= 16 and address % 64 == 0 and
                (address & 4095) + count * 64 <= 4096 and
                address + count * 64 <= 1 << 33 and
                o["avm_byteenable"] == (1 << 64) - 1, "AVALON_READ_CONTRACT")
            s.update(outstanding=count, cursor=address >> 6, last_read_address=address)
            self.event("READ", address, count, o["avm_byteenable"])
        if p["avm_readdatavalid"]:
            s["reads"] += 1
            if s["cold_response"]:
                s["cold_read_witnesses"] += 1
            self.event("READ_RSP", p["avm_readdata"], p["avm_response"])
        if o["avm_write"] and not p["avm_waitrequest"]:
            self.require(not o["avm_read"] and count == 1 and address % 64 == 0,
                         "AVALON_WRITE_CONTRACT")
            self.require(address >> 6 < len(s["memory"]), "DDR_WRITE_OUTSIDE_FIXTURE")
            value = s["memory"][address >> 6]
            for byte in range(64):
                if (o["avm_byteenable"] >> byte) & 1:
                    mask = 255 << (byte * 8)
                    value = (value & ~mask) | (o["avm_writedata"] & mask)
            s["memory"][address >> 6] = value
            s["writes"] += 1
            if (address not in s["cache_written_addresses"] and
                    any(base <= address < base + length
                        for base, length in self.spec["cache_regions"])):
                s["cache_written_addresses"].append(address)
            self.event("WRITE", address, count, o["avm_writedata"], o["avm_byteenable"])
        if p["avm_writeresponsevalid"]:
            self.event("WRITE_RSP", p["avm_response"])

    def core_positive(self):
        p, o = self.s["pins"], self.s["outputs"]
        if not p["rst_n"]:
            return
        if p["token_valid"] and o["token_ready"]:
            self.event("TOKEN", p["token_id"], p["token_pos"], p["new_sequence"])
        if p["csr_valid"] and o["csr_ready"]:
            self.event("CSR", p["csr_write"], p["csr_address"], p["csr_wdata"])
        if o["csr_rsp_valid"] and p["csr_rsp_ready"]:
            self.event("CSR_RSP", o["csr_rdata"], o["csr_error"])
        if o["logit_valid"] and p["logit_ready"]:
            self.event("LOGIT", o["logit_index"], o["logit_data"])
        if o["logit_valid"] and not p["logit_ready"]:
            self.s["stall_samples"] += 1

    def reset_check(self):
        if not self.s["pins"]["rst_n"]:
            self.require(all(value == 0 for value in self.s["outputs"].values()),
                         "TOP_RESET_NONZERO")
            self.s["reset_checks"] += 1

    def tick(self):
        s, p = self.s, self.s["pins"]
        s["controller_ticks"] += 1
        times = [s["next_core"], s["next_ddr"]]
        if s["due"] is not None:
            times.append(s["due"])
        if s["pending_post"]:
            times.append(s["post_time"])
        s["time"] = time = min(times)
        core, ddr = time == s["next_core"], time == s["next_ddr"]
        due = s["due"] == time
        post = s["pending_post"] and s["post_time"] == time
        kinds = []
        if core:
            kind = "cn" if p["clk"] else "cp"
            kinds.append(kind)
            # Public transfers are observed before any rising-edge evaluation.
            if kind == "cp":
                self.core_positive()
                self.reset_check()
                s.update(pending_post=True, post_time=time + 1)
            p["clk"] ^= 1
            s["next_core"] += 5000
            s["core_edges"] += 1
        if ddr:
            kind = "dn" if p["ddr_clk"] else "dp"
            kinds.append(kind)
            if kind == "dp":
                self.ddr_positive()
            p["ddr_clk"] ^= 1
            s["next_ddr"] += 1875
            s["ddr_edges"] += 1
        if core and ddr:
            s["simultaneous_events"] += 1
        # The original timed harness releases reset at the shared compute/DDR
        # falling edge before the DDR negedge service process observes it.
        if not due and s["wait"] is not None:
            wait = s["wait"]
            if wait.rstrip("+") in kinds:
                s["wait"] = None
                if wait.endswith("+"):
                    s["due"] = time + 1
                else:
                    self.advance()
        if "dn" in kinds:
            self.ddr_negative()
        s["outputs"] = self.driver.evaluate(time, p)
        if "cn" in kinds:
            self.reset_check()
        if post:
            s["pending_post"] = False
            if p["rst_n"] and s["outputs"]["done"]:
                self.event("DONE", s["outputs"]["error"])
        if due:
            s["due"] = None
            self.advance()
        # Settle stimulus changes at the same timestamp, without advancing clocks.
        s["outputs"] = self.driver.evaluate(time, p)
        if s["time"] > self.spec["max_time_ps"]:
            raise AssertionError("selected original workload exceeded its per-token cycle bounds")

    def checkpoint_category(self):
        s, p, o = self.s, self.s["pins"], self.s["outputs"]
        categories = s["checkpoint_categories"]
        if not categories and s["outstanding"] > 0 and s["reads"] > 0:
            return "outstanding-ddr"
        if categories == ["outstanding-ddr"]:
            address = s["response_address"]
            if (s["last_response_boundary"] and p["avm_readdatavalid"] and p["ddr_clk"] and
                    address is not None and
                    any(base <= address < base + length
                        for base, length in self.spec["weight_regions"])):
                return "weight-tile-response-ownership-boundary"
        if len(categories) == 2 and o["logit_valid"] and not p["logit_ready"]:
            return "output-stall"
        if (len(categories) == 3 and self.spec["shape"]["max_seq"] >
                self.spec["shape"]["window"] and s["cold_response"] and
                p["avm_readdatavalid"] and p["ddr_clk"]):
            return "kv-wrap-spill-retrieval"
        return None


def driver_source():
    assignments = []
    observations = []
    for name, width in INPUTS.items():
        if width > 64:
            assignments.extend(f"take(in, dut.{name}[{i}]);" for i in range((width + 31) // 32))
        else:
            assignments.append(f"take(in, dut.{name});")
    for name, width in OUTPUTS.items():
        if width > 64:
            observations.extend(f"out << ' ' << uint64_t(dut.{name}[{i}]);"
                                for i in range((width + 31) // 32))
        else:
            observations.append(f"out << ' ' << uint64_t(dut.{name});")
    return r"""
#include "Vanvil_q1_ht_top.h"
#include "verilated.h"
#include "verilated_save.h"
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
template<class T> void take(std::istream& in, T& value) {
    uint64_t word;
    if (!(in >> std::hex >> word)) throw std::runtime_error("short input vector");
    value = word;
}
int main(int argc, char** argv) {
  try {
    VerilatedContext context;
    context.commandArgs(argc, argv);
    Vanvil_q1_ht_top dut(&context);
    std::string line, op, path;
    while (std::getline(std::cin, line)) {
      std::istringstream in(line);
      in >> op;
      if (op == "E") {
        uint64_t time; take(in, time); context.time(time);
        ASSIGNMENTS
        std::string extra;
        if(in >> extra) throw std::runtime_error("extra input vector field");
        dut.eval();
        if (context.gotFinish()) throw std::runtime_error("unexpected DUT finish");
        std::ostringstream out; out << std::hex << time;
        OBSERVATIONS
        std::cout << out.str() << std::endl;
      } else if (op == "S") {
        in >> path;
        VerilatedSave stream; stream.open(path.c_str());
        stream << context.time() << dut; stream.close();
        std::cout << "SAVED" << std::endl;
      } else if (op == "L") {
        in >> path;
        uint64_t time;
        VerilatedRestore stream; stream.open(path.c_str());
        stream >> time >> dut; stream.close(); context.time(time);
        std::cout << "RESTORED" << std::endl;
      } else if (op == "Q") {
        dut.final(); return 0;
      } else throw std::runtime_error("unknown driver operation");
    }
    throw std::runtime_error("unexpected controller EOF");
  } catch(const std::exception& e) {
    std::cerr << e.what() << '\n'; return 1;
  }
}
""".replace("ASSIGNMENTS", "\n".join(assignments)).replace(
        "OBSERVATIONS", "\n".join(observations))


def build(evidence, config=0):
    folder = evidence.folder / "event-driver"
    folder.mkdir(exist_ok=False)
    cpp = folder / "driver.cpp"
    cpp.write_text(driver_source())
    sources = sorted((evidence.folder / "sources/rtl").glob("*.sv"))
    geometry = parameters(config)
    versions = {
        tool: evidence.command([tool, "--version"],
                               "event-" + ("compiler" if tool == "g++" else tool) + "-version")
        for tool in ("verilator", "g++")
    }
    evidence.command(
        ["verilator", "--cc", "--exe", "--build", "--savable", "--assert",
         "-Wno-fatal", "-j", "2", "-CFLAGS", "-O3",
         "--top-module", "anvil_q1_ht_top",
         "--Mdir", evidence.relative(folder / "compiled"),
         *[f"-G{name}={value}" for name, value in geometry.items()],
         *[evidence.relative(path) for path in sources],
         # Make resolves driver paths relative to its generated build directory.
         "../driver.cpp"],
        "scheduler-free-executable-build")
    executable = folder / "compiled/Vanvil_q1_ht_top"
    if not executable.is_file():
        raise RuntimeError("successful compiler exit did not produce an executable")
    evidence.record["scheduler_free_build"] = {
        "executable": evidence.relative(executable),
        "executable_sha256": file_sha256(executable),
        "driver": evidence.relative(cpp), "driver_sha256": file_sha256(cpp),
        "parameters": geometry, "configuration": config, "tool_versions": versions,
        "compile_command": evidence.record["commands"][-1],
        "timed_schedulers": False,
        "restoration_demonstrated": False,
    }
    evidence.flush()
    return executable


def load_build(evidence, receipt, config=0):
    previous = json.loads(project_path(receipt).read_text())
    build_record = previous["scheduler_free_build"]
    if build_record["parameters"] != parameters(config):
        raise RuntimeError("scheduler-free predecessor was built for different geometry")
    for tool, expected in build_record.get("tool_versions", {}).items():
        label = "reuse-" + ("compiler" if tool == "g++" else tool) + "-version"
        if evidence.command([tool, "--version"], label) != expected:
            raise RuntimeError(f"scheduler-free predecessor uses different {tool}")
    for name, digest in evidence.record["source_sha256"].items():
        if name.startswith("rtl/") and previous["source_sha256"].get(name) != digest:
            raise RuntimeError("scheduler-free predecessor was built against different RTL")
    for key in ("driver", "executable"):
        if file_sha256(project_path(build_record[key])) != build_record[key + "_sha256"]:
            raise RuntimeError("scheduler-free predecessor artifact changed")
    if project_path(build_record["driver"]).read_text() != driver_source():
        raise RuntimeError("scheduler-free predecessor uses a different RPC driver")
    evidence.record["scheduler_free_build"] = {
        **build_record, "producer_receipt": receipt,
        "producer_receipt_sha256": file_sha256(project_path(receipt)),
        "reused": True,
    }
    evidence.flush()
    return project_path(build_record["executable"])


def spec_from_capture(evidence, mode, captured, executable, config=0):
    _, bench, options = captured
    directory = project_path(options["runtime_args"][0].split("=", 1)[1])
    case = evidence.record["runtime_cases"][-1]
    fixture = case["engineering_fixture"]
    if (fixture["shape"] != vars(MATRIX[config]) or
            evidence.record["scheduler_free_build"]["parameters"] != parameters(config)):
        raise ValueError("fixture/build geometry mismatch")
    image = [int(line, 16) for line in (directory / "image.hex").read_text().splitlines()]
    descriptors = [int(line, 16) for line in (directory / "descriptors.hex").read_text().splitlines()]
    spec = {
        "schema": 2, "mode": mode, "seed": 17, "configuration": config,
        "shape": vars(MATRIX[config]), "parameters": parameters(config),
        "campaign": evidence.folder.name + "-" + mode,
        "executable": evidence.relative(executable), "executable_sha256": file_sha256(executable),
        "source_sha256": evidence.record["source_sha256"],
        "source_artifacts": {
            evidence.relative(evidence.folder / "sources" / name): digest
            for name, digest in evidence.record["source_sha256"].items()
        },
        "capacity": int(re.search(r"reg \[511:0\] image \[0:(\d+)\]", bench)[1]) + 1,
        "image": image, "descriptor_words": descriptors, "tokens": fixture["tokens"],
        "weight_regions": [[base, length] for _, kind, _, _, base, length
                           in fixture["descriptors"] if kind == 1],
        "cache_regions": [[base, length] for _, kind, _, _, base, length
                          in fixture["descriptors"] if kind in (9, 10)],
        "input_sha256": case["input_sha256"],
        "build_binding": evidence.record["scheduler_free_build"],
        "max_time_ps": (10_000_000 * len(fixture["tokens"]) + 1_000_000) * 10000,
    }
    return spec


def validate_manifest_chain(spec, manifests):
    if not manifests:
        raise ValueError("missing segments")
    previous = None
    for index, manifest in enumerate(manifests):
        if manifest["sequence"] != index:
            raise ValueError("missing duplicate or reordered segment")
        if manifest["campaign"] != spec["campaign"]:
            raise ValueError("cross-campaign segment")
        if manifest["source_sha256"] != spec["source_sha256"]:
            raise ValueError("wrong-source segment")
        if manifest["spec_sha256"] != binding(spec):
            raise ValueError("configuration/mode/seed/tool/executable/fixture binding mismatch")
        if manifest["previous"] != previous:
            raise ValueError("broken segment chain")
        for key in ("events", "state", "dut_state"):
            if key in manifest:
                path = project_path(manifest[key])
                if not path.is_file() or file_sha256(path) != manifest[key + "_sha256"]:
                    raise ValueError("missing or corrupt segment artifact")
        payload = {key: value for key, value in manifest.items() if key != "identity"}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        if digest != manifest["identity"]:
            raise ValueError("corrupt segment manifest")
        previous = digest
    return previous


def execute_worker(spec_path, output_path, restore_path, segmented, stop_time=None):
    spec = json.loads(project_path(spec_path).read_text())
    folder = project_path(output_path)
    folder.mkdir(exist_ok=False)
    if file_sha256(project_path(spec["executable"])) != spec["executable_sha256"]:
        raise ValueError("changed executable")
    for field in ("input_sha256", "source_artifacts"):
        for relative, expected in spec[field].items():
            path = project_path(relative)
            if not path.is_file() or file_sha256(path) != expected:
                raise ValueError("changed workload input or source snapshot")
    previous, sequence, restored = None, 0, None
    if restore_path:
        previous_manifest = json.loads(project_path(restore_path).read_text())
        ancestors = previous_manifest["ancestors"]
        chain = [json.loads(project_path(path).read_text()) for path in ancestors]
        validate_manifest_chain(spec, [*chain, previous_manifest])
        previous, sequence = previous_manifest["identity"], previous_manifest["sequence"] + 1
        restored = json.loads(project_path(previous_manifest["state"]).read_text())
        if restored["complete"]:
            raise ValueError("cannot restore a complete workload")
    else:
        ancestors = []
    started = time.monotonic()
    driver = Driver(spec["executable"], folder)
    controller = Controller(spec, driver, folder, restored)
    restore_seconds = 0.0
    try:
        if restore_path:
            restoring = time.monotonic()
            result = driver.request("L " + previous_manifest["dut_state"])
            restore_seconds = time.monotonic() - restoring
            if result != "RESTORED":
                raise RuntimeError("DUT restoration not acknowledged")
            # Do not evaluate, reset, regenerate traffic, or replay a prefix on restore.
            print(f"RESTORED_STATE sequence={sequence} time={restored['time']} "
                  f"op={restored['op']} phase={restored['phase']}", flush=True)
        else:
            controller.s["outputs"] = driver.evaluate(0, controller.s["pins"])
            controller.reset_check()
            controller.advance()
        checkpoint = None
        running = time.monotonic()
        while not controller.s["complete"]:
            controller.tick()
            if stop_time is not None and controller.s["time"] >= stop_time:
                checkpoint = "bounded-cost-prefix"
                break
            if segmented:
                checkpoint = controller.checkpoint_category()
                if checkpoint:
                    controller.s["checkpoint_categories"].append(checkpoint)
                    break
        event_seconds = time.monotonic() - running
        controller.trace.close()
        manifest = {
            "schema": 1, "sequence": sequence, "campaign": spec["campaign"],
            "source_sha256": spec["source_sha256"], "previous": previous,
            "spec_sha256": binding(spec),
            "ancestors": [*ancestors, restore_path] if restore_path else [],
            "events": str((folder / "events.log").relative_to(ROOT)),
            "checkpoint": checkpoint, "complete": controller.s["complete"],
            "time": controller.s["time"], "pid": os.getpid(),
            "driver_pid": driver.process.pid,
            "summary": {
                name: controller.s[name] for name in (
                    "reads", "writes", "load_accepts", "csr_compares", "logits",
                    "ddr_cycles", "core_edges", "ddr_edges", "simultaneous_events",
                    "reset_checks", "stall_samples", "checkpoint_categories", "token_rows")
            },
        }
        manifest["summary"].update({
            name: controller.s[name] for name in (
                "cold_read_witnesses", "controller_ticks")
        })
        manifest["events_sha256"] = file_sha256(folder / "events.log")
        if checkpoint:
            state_path, dut_path = folder / "controller.json", folder / "dut.bin"
            write_json(state_path, controller.s)
            saving = time.monotonic()
            if driver.request("S " + str(dut_path.relative_to(ROOT))) != "SAVED":
                raise RuntimeError("DUT save not acknowledged")
            save_seconds = time.monotonic() - saving
            manifest.update(state=str(state_path.relative_to(ROOT)),
                            state_sha256=file_sha256(state_path),
                            dut_state=str(dut_path.relative_to(ROOT)),
                            dut_state_sha256=file_sha256(dut_path))
        else:
            save_seconds = 0.0
        manifest["cost"] = {
            "event_seconds": event_seconds, "save_seconds": save_seconds,
            "restore_seconds": restore_seconds,
            "elapsed_before_settlement_seconds": time.monotonic() - started,
            "dut_state_bytes": (project_path(manifest["dut_state"]).stat().st_size
                                if checkpoint else 0),
        }
    finally:
        try:
            if not controller.trace.closed:
                controller.trace.close()
        finally:
            driver.close()
    digest, size = hashlib.sha256(), 0
    with gzip.open(driver.stdout_path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    if digest.hexdigest() != driver.stdout_digest.hexdigest() or size != driver.stdout_bytes:
        raise AssertionError("lossless driver response retention mismatch")
    manifest["driver_stdout"] = {
        "path": str(driver.stdout_path.relative_to(ROOT)),
        "compression": "gzip",
        "sha256": file_sha256(driver.stdout_path),
        "uncompressed_sha256": digest.hexdigest(), "uncompressed_bytes": size,
    }
    payload = json.dumps(manifest, sort_keys=True).encode()
    manifest["identity"] = hashlib.sha256(payload).hexdigest()
    write_json(folder / "manifest.json", manifest)
    print(f"WORKER_SETTLED sequence={sequence} complete={int(controller.s['complete'])} "
          f"checkpoint={checkpoint} time={controller.s['time']}", flush=True)


def negative_segments(evidence, spec, manifests):
    import copy

    trials = [
        ("missing", manifests[1:]),
        ("duplicate", manifests[:1] + [manifests[0]] + manifests[1:]),
        ("reordered", [manifests[1], manifests[0], *manifests[2:]]),
    ]
    for name, field, value in (
        ("corrupt", "events_sha256", "0" * 64),
        ("wrong-source", "source_sha256", {}),
        ("cross-campaign", "campaign", spec["campaign"] + "-wrong"),
    ):
        changed = copy.deepcopy(manifests)
        changed[1][field] = value
        trials.append((name, changed))
    for name, trial in trials:
        path = evidence.folder / f"{spec['mode'].lower()}-invalid-{name}.json"
        write_json(path, trial)
        try:
            validate_manifest_chain(spec, trial)
        except ValueError as exc:
            evidence.record.setdefault("invalid_segment_rejections", []).append({
                "mode": spec["mode"], "category": name,
                "input": evidence.relative(path), "input_sha256": file_sha256(path),
                "rejection": str(exc),
            })
        else:
            raise AssertionError(f"invalid segment accepted: {name}")
    evidence.flush()


def capture_case(evidence, mode, config):
    captured = []
    original_simulate = evidence.simulate

    def capture(name, bench, **options):
        captured.append((name, bench, options))

    evidence.simulate = capture
    try:
        top_probe(evidence, mode, 17, config=config)
    finally:
        evidence.simulate = original_simulate
    if len(captured) != 2:
        raise AssertionError("expected reset and complete original timed harness")
    return captured


def cost_probe(evidence, executable, config, mode, cycles):
    """Measure a prefix without shortening the stored full workload or certifying it."""
    _, timed = capture_case(evidence, mode, config)
    spec = spec_from_capture(evidence, mode, timed, executable, config)
    spec_path = evidence.folder / f"{mode.lower()}-spec.json"
    write_json(spec_path, spec)
    midpoint, endpoint = cycles * 10000, cycles * 20000
    name, bench, options = timed
    # Neither boundary coincides with a rising compute or DDR edge.
    bounded = bench.rsplit("endmodule", 1)[0] + TRACE + f"""
initial begin
 #{endpoint // 1000};
 if(reset_checks==0 || csr_compares==0 || writes==0 || load_accepts<writes)
  $fatal(1,"COST_PREFIX_MISSING_OBSERVATIONS");
 $display("CHECKS_PASSED bounded_cost_prefix reset_checks=%0d csr_compares=%0d writes=%0d load_accepts=%0d full_workload_complete=0",
          reset_checks,csr_compares,writes,load_accepts);
 $display("BOUNDED_COST_PREFIX time_ps={endpoint} full_workload_complete=0");
 $finish;
end
endmodule
"""
    baseline = evidence.simulate(name + "-bounded-original-timed", bounded, **options)
    if f"BOUNDED_COST_PREFIX time_ps={endpoint}" not in baseline:
        raise AssertionError("timed cost prefix did not reach its declared bound")
    expected_events = canonical_events(baseline)
    runs = []
    for label, stop, predecessor in (
        ("continuous", endpoint, None),
        ("prefix", midpoint, None),
        ("restored", endpoint, "prefix"),
    ):
        folder = evidence.folder / f"{mode.lower()}-cost-{label}"
        command = [
            "python3", "-B", "tests/serialization_events.py", "--worker",
            evidence.relative(spec_path), "--output", evidence.relative(folder),
            "--stop-time-ps", str(stop),
        ]
        if predecessor:
            command.extend(["--restore", evidence.relative(
                evidence.folder / f"{mode.lower()}-cost-{predecessor}/manifest.json")])
        evidence.command(command, folder.name)
        manifest = json.loads((folder / "manifest.json").read_text())
        if manifest["complete"] or manifest["time"] != stop:
            raise AssertionError("bounded cost sample ended at an unexpected workload boundary")
        runs.append(manifest)
        evidence.record.setdefault("bounded_cost_stages", []).append({
            "configuration": config, "mode": mode, "stage": label,
            "manifest": evidence.relative(folder / "manifest.json"),
            "cost": manifest["cost"], "summary": manifest["summary"],
            "time_ps": stop, "complete_workload_parity": False,
        })
        evidence.flush()
    continuous, prefix, restored = runs
    for chain in ([continuous], [prefix, restored]):
        validate_manifest_chain(spec, chain)
        events = []
        for manifest in chain:
            events.extend(canonical_events(project_path(manifest["events"]).read_text()))
        if events != expected_events:
            raise AssertionError("bounded prefix timestamped public transactions differ")
    for key in ("state_sha256", "dut_state_sha256", "summary"):
        if continuous[key] != restored[key]:
            raise AssertionError(f"bounded restored prefix differs in complete saved {key}")
    fresh_process_binding_trials(evidence, spec, spec_path, prefix, mode)
    negative_segments(evidence, spec, [prefix, restored])
    evidence.record["bounded_cost_result"] = {
        "configuration": config, "mode": mode, "seed": 17,
        "full_original_tokens_preserved": len(spec["tokens"]),
        "full_original_logits_preserved": sum(len(token[3]) for token in spec["tokens"]),
        "ordered_prefix_transaction_rows": len(expected_events),
        "prefix_public_transactions_equal": True,
        "prefix_complete_saved_state_equal": True,
        "full_workload_parity": False, "kv_restoration_demonstrated": False,
        "schedule": (
            "Build and each mode's bounded cost measurement are separate invocations. "
            "No complete larger comparison or campaign is scheduled. Measured prefix "
            "cost is not a guaranteed full-run bound; independent execution accommodation "
            "is required before known-infeasible uninterrupted full comparisons."),
    }
    evidence.flush()


def fresh_process_binding_trials(evidence, spec, spec_path, predecessor, mode):
    import copy

    restore_path = evidence.relative(
        project_path(predecessor["state"]).parent / "manifest.json")
    changes = {
        "configuration": (spec["configuration"] + 1) % len(MATRIX),
        "mode": "BF16" if mode == "AWQ" else "AWQ",
        "seed": spec["seed"] + 1,
        "tool-options": {**spec["build_binding"], "compile_options": ["wrong-option"]},
        "fixture-binding": {**spec["input_sha256"], "missing-fixture": "0" * 64},
    }
    for label, value in changes.items():
        changed = copy.deepcopy(spec)
        field = {"tool-options": "build_binding", "fixture-binding": "input_sha256"}.get(label, label)
        changed[field] = value
        path = evidence.folder / f"{mode.lower()}-wrong-{label}-spec.json"
        write_json(path, changed)
        output = evidence.folder / f"{mode.lower()}-reject-{label}"
        text = evidence.command([
            "python3", "-B", "tests/serialization_events.py",
            "--worker", evidence.relative(path), "--output", evidence.relative(output),
            "--restore", restore_path, "--stop-time-ps", str(predecessor["time"] + 10000),
        ], f"{mode.lower()}-fresh-process-reject-{label}", expected_codes=(1,))
        if "binding mismatch" not in text and "changed workload input" not in text:
            raise AssertionError(f"fresh-process {label} rejection was not a binding failure")
        if any((output / name).exists()
               for name in ("driver-stdout.log", "driver-stdout.log.gz")):
            raise AssertionError("binding mismatch launched the DUT driver")
    evidence.record["fresh_process_binding_rejections"] = list(changes)
    evidence.flush()


def compare(evidence, executable, config=0, modes=("AWQ", "BF16")):
    timestamp_bench = r"""
`timescale 1ns/1ps
module tb;
real stamp;
initial begin
 #1.875;
 stamp=$realtime/1ps;
 if(stamp != 1875.0) $fatal(1,"PICOSECOND_STAMP_ROUNDED");
 $display("EVENT STAMP %0.0f 0",$realtime/1ps);
 #3.126;
 stamp=$realtime/1ps;
 if(stamp != 5001.0) $fatal(1,"POST_EDGE_STAMP_ROUNDED");
 $display("EVENT STAMP %0.0f 0",$realtime/1ps);
 $display("CHECKS_PASSED timestamp samples=2");
 $finish;
end
endmodule
"""
    for simulator in ("iverilog", "verilator"):
        text = evidence.simulate("timestamp-" + simulator, timestamp_bench,
                                 sources=[], simulator=simulator)
        if canonical_events(text) != [["STAMP", 1875, 0], ["STAMP", 5001, 0]]:
            raise AssertionError("trace formatting did not retain picosecond event deadlines")
    for mode in modes:
        captured = capture_case(evidence, mode, config)
        original_simulate = evidence.simulate
        four_state, timed = captured
        original_simulate(*four_state[:2], **four_state[2])
        name, bench, options = timed
        instrumented = bench.rsplit("endmodule", 1)[0] + TRACE + r"""
final $display("EVENT_COUNTS reset_checks=%0d ddr_cycles=%0d",reset_checks,ddr_cycles);
endmodule
"""
        baseline = original_simulate(name + "-original-timed", instrumented, **options)
        expected_events, expected_counters = canonical_events(baseline), counters(baseline)
        token_count = min(MATRIX[config].max_seq, MATRIX[config].window + 2) + 1
        if not expected_events or len(expected_counters) != token_count + 1:
            raise AssertionError("original complete workload did not compare every token")
        spec = spec_from_capture(evidence, mode, timed, executable, config)
        spec_path = evidence.folder / f"{mode.lower()}-spec.json"
        write_json(spec_path, spec)
        paths = []
        for segmented in (False, True):
            manifests, worker_text, events = [], "", []
            restore = None
            checkpoint_count = 3 + int(MATRIX[config].max_seq > MATRIX[config].window)
            for index in range(checkpoint_count + 1 if segmented else 1):
                folder = evidence.folder / f"{mode.lower()}-{'restored' if segmented else 'continuous'}-{index}"
                command = ["python3", "-B", "tests/serialization_events.py", "--worker",
                           evidence.relative(spec_path), "--output", evidence.relative(folder)]
                if segmented:
                    command.append("--segmented")
                if restore:
                    command.extend(["--restore", restore])
                worker_text += evidence.command(command, folder.name, timeout=3600)
                manifest_path = folder / "manifest.json"
                manifest = json.loads(manifest_path.read_text())
                manifests.append(manifest)
                events.extend(canonical_events(project_path(manifest["events"]).read_text()))
                paths.append(evidence.relative(manifest_path))
                restore = evidence.relative(manifest_path)
                if manifest["complete"]:
                    break
            if not manifests[-1]["complete"]:
                raise AssertionError("restored workload did not complete after required checkpoints")
            validate_manifest_chain(spec, manifests)
            if events != expected_events:
                first = next((i for i, pair in enumerate(zip(events, expected_events))
                              if pair[0] != pair[1]), min(len(events), len(expected_events)))
                raise AssertionError(
                    f"{mode} {'restored' if segmented else 'continuous'} transaction divergence "
                    f"index={first} alternative={events[first:first+1]} "
                    f"original={expected_events[first:first+1]} counts={len(events)}/{len(expected_events)}")
            # Token lines before a checkpoint are retained in its serialized scoreboard;
            # the full uninterrupted expectation is compared to the final saved ledger.
            summary = manifests[-1]["summary"]
            token_text = "\n".join(summary["token_rows"]) + "\n"
            final_lines = [line for line in worker_text.splitlines()
                           if line.startswith("CHECKS_PASSED top ")]
            actual_counters = counters(token_text + "\n".join(final_lines))
            if actual_counters != expected_counters:
                raise AssertionError(f"{mode} counters diverged: {actual_counters} != {expected_counters}")
            baseline_counts = dict(re.findall(
                r"(reset_checks|ddr_cycles)=(\d+)",
                next(line for line in baseline.splitlines() if line.startswith("EVENT_COUNTS "))))
            if any(summary[key] != int(value) for key, value in baseline_counts.items()):
                raise AssertionError(f"{mode} edge/reset coverage diverged: {summary} != {baseline_counts}")
            if segmented:
                categories = summary["checkpoint_categories"]
                required = ["outstanding-ddr", "weight-tile-response-ownership-boundary", "output-stall"]
                if checkpoint_count == 4:
                    required.append("kv-wrap-spill-retrieval")
                if categories != required:
                    raise AssertionError(f"required checkpoint boundary missing: {categories}")
                if len({manifest["pid"] for manifest in manifests}) != checkpoint_count + 1 or len(
                        {manifest["driver_pid"] for manifest in manifests}) != checkpoint_count + 1:
                    raise AssertionError("restoration did not use fresh processes")
                negative_segments(evidence, spec, manifests)
                continuous = evidence.record["parity"][-1]["summary"]
                if {k: v for k, v in summary.items() if k != "checkpoint_categories"} != {
                        k: v for k, v in continuous.items() if k != "checkpoint_categories"}:
                    raise AssertionError("restored coverage/counters differ from uninterrupted alternative")
            evidence.record.setdefault("parity", []).append({
                "mode": mode, "execution": "restored" if segmented else "continuous",
                "ordered_transaction_rows": len(events), "counters": actual_counters,
                "summary": summary, "manifests": [path for path in paths if
                    ("-restored-" if segmented else "-continuous-") in path],
                "all_original_timed_transactions_equal": True,
                "all_original_timed_cycles_equal": True,
                "independent_logits_equal": True,
            })
            evidence.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--config", type=int, choices=range(len(MATRIX)), default=0)
    parser.add_argument("--mode", choices=("AWQ", "BF16"))
    parser.add_argument("--cost-only", action="store_true")
    parser.add_argument("--cost-cycles", type=int, default=10000,
                        help="Compute cycles per bounded cost prefix, not a full workload")
    parser.add_argument("--build-receipt")
    parser.add_argument("--worker")
    parser.add_argument("--output")
    parser.add_argument("--restore")
    parser.add_argument("--segmented", action="store_true")
    parser.add_argument("--stop-time-ps", type=int)
    parser.add_argument("--repair-of", default=(
        "evidence/preparation/verifier-serialization-capability-"
        "20261028T224711Z-76a5d53e/receipt.json"))
    args = parser.parse_args()
    if args.worker:
        execute_worker(args.worker, args.output, args.restore, args.segmented, args.stop_time_ps)
        return 0
    if args.cost_only and (args.mode is None or args.cost_cycles <= 0 or args.cost_cycles % 3 == 0):
        parser.error("cost probes require one mode and positive cost cycles not divisible by three")
    if args.config != 0 and not (args.build_only or args.cost_only):
        parser.error("complete larger comparisons await independent execution-feasibility admission")
    evidence = Evidence("serialization-events", repair_of=args.repair_of)
    try:
        executable = (load_build(evidence, args.build_receipt, args.config)
                      if args.build_receipt else build(evidence, args.config))
        if args.cost_only:
            cost_probe(evidence, executable, args.config, args.mode, args.cost_cycles)
            evidence.finish(
                "bounded_cost_prefix_only",
                "Measured build/event/save/restore costs and compared exact bounded-prefix "
                "public transactions and saved state. Original full workload retained but "
                "not completed. No larger restoration or campaign acceptance established.")
            return 0
        if not args.build_only:
            compare(evidence, executable, args.config,
                    (args.mode,) if args.mode else ("AWQ", "BF16"))
            evidence.finish(
                "probe_passed",
                "Bounded configuration-0 AWQ/BF16 original timed, scheduler-free uninterrupted "
                "and fresh-process restored workloads agree in ordered public-pin transactions, "
                "logits, cycles and observed counters. Six invalid-segment categories rejected "
                "in each mode. Not admission of segmented campaigns or accelerator acceptance.")
            return 0
        evidence.finish(
            "executable_built_not_restoration",
            "Scheduler-free executable compiled and linked against frozen unchanged "
            f"configuration-{args.config} DUT. Functional parity and restoration are not yet established.")
        return 0
    except Exception as exc:
        evidence.finish("capability_probe_failed", f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
