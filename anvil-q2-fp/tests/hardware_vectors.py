"""Portable native hardware-bridge vectors and public-pin trace comparison.

Generate an immutable recipe (its receipt names vectors.json):
  python3 tests/hardware_vectors.py --generate --format fp16 --weights 1 --cache 1 --banks 4
Compare an actual bridge trace:
  python3 tests/hardware_vectors.py --compare evidence/.../vectors.json evidence/.../pins.jsonl
The bridge prepends project-relative tests/ to its Python import path, imports
MemoryService from hardware_vectors, and calls read/write with packed
coordinates from transformer_reference.key. No local transport/device is selected.

Each JSONL record is a PRE-edge public-pin snapshot with these exact fields:
  cycle: unsigned cycle number, starting at zero
  repeat: optional positive number of identical, transfer-free cycles
  rst_n, cancel: bits
  token: [valid, ready, id, position, new_sequence, phase]
  logit: [valid, ready, index, data]
  status: [done, error, cancel_done]
  banks: one array per bank containing
    [req_valid,req_ready,write,kind,layer,proj,row,col,wdata,tag,
     rsp_valid,rsp_ready,error,rdata,tag]
All values are unsigned JSON integers, not strings or unknown encodings.
Capture reset, every active cycle, payload stalls and the final drained done.
Only identical cycles without transfers/status pulses may use repeat.
Write-response data is unused by the ABI; its tag, error and payload stability
are still checked. Read-response data must equal the independent memory service.
Recipes specify actual native parameters and eight token positions, not a
reduced substitute. Reference-row reuse never reduces physical DUT execution.

Comparison establishes numerical/protocol conformance and measured public-pin
cycles and five-domain errors against the common 70-digit workload. It does
not establish timing, FPGA resources, physical provenance,
standalone lane II or three-pass hardware determinism. Those remain mandatory
shared-runtime gates. Precision is calculated only after every actual stage
write/logit has matched its normative bits, never instead of those bit checks.
"""

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark_checks import domain_indices
from native_reference import NativeParentTransformer, NativeTransformer, TensorMemory, native_geometry
from native_precision import NativeMathematicalTransformer
from retained import ROOT, Run, require_time_zero, with_time_zero_check
from simulation import compile_model, startup_check
from suite_manifest import manifest
from transformer_reference import Geometry, Transformer, coordinates, key


def relative_input(name):
    path = Path(name)
    assert not path.is_absolute() and ".." not in path.parts, "use project-relative input paths"
    assert not {".git", ".vulcan", ".tooling", "VULCAN"} & set(path.parts)
    resolved = (ROOT / path).resolve()
    relative = resolved.relative_to(ROOT)
    assert not {".git", ".vulcan", ".tooling", "VULCAN"} & set(relative.parts)
    assert resolved.is_file(), f"missing input: {name}"
    return resolved


def digest_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def recipe(fmt, weights, cache, banks, seed, product="fp"):
    assert banks in (1, 2, 4) and fmt in ("bf16", "fp16")
    assert weights in (0, 1) and cache in (0, 1) and seed in (17, 43, 89)
    assert product in ("fp", "parent")
    assert product != "parent" or (fmt == "fp16" and weights == 1), (
        "parent supports FP16 tensor loads and AWQ only; no native parent baseline")
    g = native_geometry()
    definition = manifest(g)
    definition.update(
        shape_class="native", product=product, geometry=asdict(g),
        selected=dict(fp_format=fmt, weight_mode=weights, cache_mode=cache, banks=banks, seed=seed),
        parameters=dict(NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
                        NUM_Q_HEADS=12, NUM_KV_HEADS=2, HEAD_DIM=128, GROUP_SIZE=128,
                        VOCAB_SIZE=151936, MAX_SEQ_LEN=32768, CACHE_BLOCK=16, QUEUE_DEPTH=3),
        commands=[dict(token_id=position % g.vocabulary, token_pos=position,
                       new_sequence=int(position == 0), token_phase=int(position == g.positions - 1))
                  for position in range(g.positions)],
        trace_schema="tests/hardware_vectors.py module docstring, pre-edge JSONL v1",
        memory_service=dict(python_path="tests", module="hardware_vectors", class_name="MemoryService"),
        scope="Native synthetic workload recipe; generation is not DUT execution or acceptance.",
    )
    definition["top"] = "anvil_q2_top" if product == "parent" else "anvil_q2_fp_top"
    definition["parameters"].update(BANKS=banks, CACHE_MODE=cache)
    if product == "fp":
        definition["parameters"].update(FP_FORMAT=int(fmt == "fp16"), WEIGHT_MODE=weights)
    if product == "parent":
        definition["matrix"] = [c for c in definition["matrix"]
                                if c["fp_format"] == "fp16" and c["weight_mode"] == 1]
        definition["domain_matrix_entries"] = len(definition["matrix"]) * len(definition["domains"])
        definition["parent_comparison"] = (
            "One actual FP16-load/Q16.16 parent run may be compared with both FP formats; "
            "native weights are not applicable, never a fabricated parent baseline.")
    return definition


class MemoryService:
    """Actual DUT writes populate RAM; readonly model tensors are generated lazily."""

    def __init__(self, definition, geometry=None):
        config = definition["selected"]
        self.g = geometry or Geometry(**definition["geometry"])
        self.product = definition["product"]
        self.cache_mode = config["cache_mode"]
        self.tensors = TensorMemory(config["fp_format"], config["weight_mode"],
                                    config["seed"], self.g, parent=self.product == "parent")
        self.ram = {}

    def read(self, address):
        unsigned(address, 103)
        kind = coordinates(address)[0]
        if kind == 8 or 9 <= kind <= 15 and kind != 11:
            self.validate_ram_address(address)
            if address not in self.ram:
                raise KeyError(f"uninitialized scratch/cache read: {coordinates(address)}")
            return self.ram[address]
        return self.tensors[address]

    def write(self, address, data):
        unsigned(address, 103)
        unsigned(data, 32)
        self.validate_ram_address(address)
        self.ram[address] = data

    def validate_ram_address(self, address):
        kind, layer, proj, row, col = coordinates(address)
        g = self.g
        allowed = (8, 9, 10) if self.cache_mode == 0 else (8, 12, 13, 14, 15)
        assert kind in allowed, "write to readonly tensor or incompatible cache format"
        assert proj == 0
        if kind == 8:
            sizes = {slot: g.hidden for slot in (0, 1, 2, 5, 6, 7, 8, 12, 14)}
            sizes.update({3: g.kv_heads * g.head_dim, 4: g.kv_heads * g.head_dim,
                          9: g.intermediate, 10: g.intermediate, 11: g.intermediate})
            assert layer == 0 and row in sizes and col < sizes[row], "illegal scratch coordinate"
        else:
            assert layer < g.layers and row < g.positions, "illegal cache layer/position"
            if self.cache_mode == 0:
                columns = g.kv_heads * g.head_dim // (1 if self.product == "parent" else 2)
            else:
                columns = g.kv_heads * g.head_dim // g.block
                if kind in (12, 13):
                    columns *= (g.block + 3) // 4
            assert col < columns, "illegal cache component/block coordinate"


def unsigned(number, width):
    assert type(number) is int and 0 <= number < 2**width, (
        f"unknown, noninteger or out-of-range {width}-bit public value: {number!r}")


class PinChecker:
    def __init__(self, definition, reference):
        self.definition, self.reference = definition, reference
        self.g = reference.g
        self.banks = definition["selected"]["banks"]
        self.memory = MemoryService(definition, self.g)
        self.used = Counter()
        self.pending = {}
        self.stage_writes = defaultdict(list)
        for index, stage in enumerate(reference.stages):
            for col in range(len(stage["bits"])):
                self.stage_writes[key(8, row=stage["slot"], col=col)].append(index)
        self.stage_ack = Counter()
        self.stage_ends = {}
        self.next_logit = iter(reference.logits)
        self.frontier = 0
        self.seen_ahead = set()
        self.commands, self.ends, self.last_logits = [], [], {}
        self.active = None
        self.row = 0
        self.cycle = 0
        self.previous = None
        self.requests = self.responses = self.writes = self.logits = self.peak = 0
        self.nonzero_write_acks = 0
        self.by_kind, self.write_kinds, self.by_bank, self.stalls, self.occupied = (
            Counter(), Counter(), Counter(), Counter(), Counter())
        self.cache_ack, self.committed = Counter(), set()
        g = self.g
        self.cache_words = (
            2 * g.kv_heads * g.head_dim // (1 if definition["product"] == "parent" else 2)
            if definition["selected"]["cache_mode"] == 0 else
            2 * (g.kv_heads * g.head_dim // g.block) * ((g.block + 3) // 4 + 1))

    def snapshot(self, frame):
        assert set(frame) <= {"cycle", "repeat", "rst_n", "cancel", "token", "logit", "status", "banks"}
        unsigned(frame["cycle"], 64)
        assert frame["cycle"] == self.cycle, "missing, duplicate or reordered public cycle"
        repeat = frame.get("repeat", 1)
        assert type(repeat) is int and repeat > 0
        for name in ("rst_n", "cancel"):
            unsigned(frame[name], 1)
        token, logit, status, banks = (frame[name] for name in ("token", "logit", "status", "banks"))
        for fields, widths in ((token, (1, 1, 32, 32, 1, 1)), (logit, (1, 1, 32, 32)),
                               (status, (1, 1, 1))):
            assert len(fields) == len(widths)
            for number, width in zip(fields, widths):
                unsigned(number, width)
        assert len(banks) == self.banks
        widths = (1, 1, 1, 4, 32, 3, 32, 32, 32, 64, 1, 1, 1, 32, 64)
        for fields in banks:
            assert len(fields) == len(widths)
            for number, width in zip(fields, widths):
                unsigned(number, width)
        transfers = token[0] and token[1] or logit[0] and logit[1] or any(
            b[0] and b[1] or b[10] and b[11] for b in banks)
        assert repeat == 1 or not (transfers or any(status) or frame["cancel"]), (
            "repeat concealed a transfer or pulse")
        if not frame["rst_n"]:
            assert not self.commands, "unexpected reset during native benchmark"
            assert token[1] == logit[0] == logit[2] == logit[3] == 0 and not any(status)
            assert all(not any([b[0], *b[2:10], b[11]]) for b in banks), (
                "reset public output not zero")
        else:
            assert self.previous is not None, "missing reset snapshot"
            assert frame["cancel"] == status[1] == status[2] == 0, "failed or cancelled benchmark"
            self.stability(frame)
            self.accept(frame, repeat)
        self.previous = frame
        self.cycle += repeat

    def stability(self, frame):
        previous = self.previous
        if not previous["rst_n"]:
            return
        for name in ("token", "logit"):
            a, b = previous[name], frame[name]
            if a[0] and not a[1]:
                assert [a[0], *a[2:]] == [b[0], *b[2:]], f"unstable held {name}"
        for a, b in zip(previous["banks"], frame["banks"]):
            if a[0] and not a[1]:
                assert [a[0], *a[2:10]] == [b[0], *b[2:10]], "unstable held request"
            if a[10] and not a[11]:
                assert [a[10], *a[12:]] == [b[10], *b[12:]], "unstable held response"

    def accept(self, frame, repeat):
        cycle, token, logit, status = (frame[name] for name in ("cycle", "token", "logit", "status"))
        if token[0] and token[1]:
            position = len(self.commands)
            assert self.active is None and position < self.g.positions, "extra/overlapping token"
            assert token[2:] == [position % self.g.vocabulary, position, int(position == 0),
                                int(position == self.g.positions - 1 and position != 0)]
            self.active, self.row = position, 0
            self.commands.append(cycle)
        for bank, fields in enumerate(frame["banks"]):
            if fields[0] and not fields[1]:
                self.stalls[bank] += repeat
            if fields[10] and fields[11]:
                tag = fields[14]
                assert tag in self.pending, "unknown/duplicate response tag"
                owner, data, start, address, write, stage = self.pending.pop(tag)
                assert owner == bank and (write or data == fields[13]) and fields[12] == 0, (
                    "response bank/data/error mismatch")
                assert cycle > start, "early/zero-cycle response"
                self.responses += 1
                self.occupied[bank] += cycle - start
                if write:
                    self.nonzero_write_acks += int(fields[13] != 0)
                    kind, layer, _, position, _ = coordinates(address)
                    if kind in (9, 10, 12, 13, 14, 15):
                        self.cache_ack[layer, position] += 1
                        if self.cache_ack[layer, position] == self.cache_words:
                            self.committed.add((layer, position))
                    if stage is not None:
                        self.stage_ack[stage] += 1
                        if self.stage_ack[stage] == len(self.reference.stages[stage]["bits"]):
                            self.stage_ends[stage] = cycle
            if fields[0] and fields[1]:
                assert self.active is not None and cycle > self.commands[self.active]
                address, tag = key(*fields[3:8]), fields[9]
                assert sum(fields[3:8]) & (self.banks - 1) == bank, "wrong request bank"
                assert tag >= self.frontier and tag not in self.seen_ahead, "reused request tag"
                self.seen_ahead.add(tag)
                while self.frontier in self.seen_ahead:
                    self.seen_ahead.remove(self.frontier)
                    self.frontier += 1
                self.requests += 1
                self.by_bank[bank] += 1
                self.by_kind[fields[3]] += 1
                write, data, stage = fields[2], fields[8], None
                if write:
                    index = self.used[address]
                    assert address in self.reference.writes and index < len(self.reference.writes[address]), (
                        "uncommanded or duplicate write")
                    assert data == self.reference.writes[address][index], (
                        f"numerical write mismatch at {coordinates(address)}")
                    if fields[3] == 8:
                        stage = self.stage_writes[address][index]
                    else:
                        assert fields[6] == self.active, "cache write for wrong token position"
                    self.used[address] += 1
                    self.memory.write(address, data)
                    self.writes += 1
                    self.write_kinds[fields[3]] += 1
                    expected_data = 0
                else:
                    if fields[3] in (9, 10, 12, 13, 14, 15):
                        assert fields[6] <= self.active and (fields[4], fields[6]) in self.committed, (
                            "uncommitted or noncausal cache read")
                    expected_data = self.memory.read(address)
                assert tag not in self.pending
                self.pending[tag] = (bank, expected_data, cycle, address, write, stage)
                self.peak = max(self.peak, len(self.pending))
        if logit[0] and logit[1]:
            assert self.active is not None
            try:
                expected = next(self.next_logit)
            except StopIteration as exc:
                raise AssertionError("extra logit") from exc
            assert (self.active, logit[2], logit[3]) == expected, "logit numerical/index mismatch"
            self.last_logits[self.active] = cycle
            self.row += 1
            self.logits += 1
        if status[0]:
            assert self.active is not None and self.row == self.g.vocabulary
            assert not self.pending and self.last_logits[self.active] < cycle, "early/undrained done"
            assert all((layer, self.active) in self.committed for layer in range(self.g.layers))
            self.ends.append(cycle)
            self.active = None

    def finish(self):
        assert self.commands and len(self.commands) == len(self.ends) == self.g.positions
        assert self.active is None and not self.pending and not self.seen_ahead
        assert self.frontier == self.requests == self.responses
        assert all(self.used[address] == len(values) for address, values in self.reference.writes.items()), (
            "missing expected writes")
        assert self.logits == len(self.reference.logits) == self.g.positions * self.g.vocabulary
        assert len(self.stage_ends) == len(self.reference.stages), "missing stage acknowledgements"
        assert not self.previous["logit"][0] and all(
            not b[0] and not b[10] for b in self.previous["banks"]), "undrained final public pins"
        assert set(self.by_bank) == set(range(self.banks)), "missing bank utilization"
        if self.banks > 1:
            assert self.peak > 1, "parallel bank execution serialized to one outstanding request"
        intervals, components = Counter(), Counter()
        for index, stage in enumerate(self.reference.stages):
            start = (self.commands[stage["position"]] if stage["domain"] == "embedding" else
                     self.stage_ends[index - 1])
            assert self.stage_ends[index] > start, "out-of-order stage completion"
            for domain in domain_indices(stage):
                intervals[domain] += self.stage_ends[index] - start
                components[domain] += len(stage["bits"])
        return dict(
            memory_requests_compared=self.requests, responses_compared=self.responses,
            writes_compared=self.writes, logits_compared=self.logits,
            nonzero_write_acknowledgements=self.nonzero_write_acks,
            accepted_command_to_final_accepted_logit_cycles=[
                self.last_logits[i] - start for i, start in enumerate(self.commands)],
            accepted_command_to_done_cycles=[end - start for start, end in zip(self.commands, self.ends)],
            requests_by_kind=dict(self.by_kind), requests_by_bank=dict(self.by_bank),
            accepted_writes_by_kind=dict(self.write_kinds),
            memory_stall_cycles_by_bank=dict(self.stalls),
            external_outstanding_cycles_by_bank=dict(self.occupied),
            cache_write_payload_bytes=4 * sum(
                count for kind, count in self.write_kinds.items() if kind in (9, 10, 12, 13, 14, 15)),
            domain_final_write_ack_intervals=dict(intervals),
            domain_stage_components_compared=dict(components),
            peak_outstanding=self.peak, stage_final_write_ack_cycles=self.stage_ends)


PIN_TRACE = r"""
  always @(posedge clk) begin
    $display("PIN %0d %h %h %h %h %h %h %h %h %h %h %h %h %h %h",
      cycles,rst_n,token_valid,token_ready,token_id,token_pos,new_sequence,token_phase,
      logit_valid,logit_ready,logit_index,logit_data,done,error,cancel_done);
    for(integer pin_bank=0;pin_bank<BANKS;pin_bank=pin_bank+1)
      $display("PIN_BANK %0d %h %h %h %h %h %h %h %h %h %h %h %h %h %h",
        pin_bank,req_valid[pin_bank],req_ready[pin_bank],req_write[pin_bank],
        req_kind[pin_bank*4+:4],req_layer[pin_bank*32+:32],req_proj[pin_bank*3+:3],
        req_row[pin_bank*32+:32],req_col[pin_bank*32+:32],req_data[pin_bank*32+:32],
        req_tag[pin_bank*64+:64],rsp_valid[pin_bank],rsp_ready[pin_bank],
        rsp_data[pin_bank*32+:32],rsp_tag[pin_bank*64+:64]);
    $display("PIN_END");
  end
"""


def simulated_pins(trace):
    frame = None
    with trace.open() as stream:
        for line in stream:
            fields = line.split()
            if not fields:
                continue
            if fields[0] == "PIN":
                assert frame is None
                values = [int(number, 16) for number in fields[2:]]
                assert len(values) == 14
                frame = dict(cycle=int(fields[1]), rst_n=values[0], cancel=0,
                             token=values[1:7], logit=values[7:11], status=values[11:14], banks=[])
            elif fields[0] == "PIN_BANK":
                assert frame is not None and int(fields[1]) == len(frame["banks"])
                values = [int(number, 16) for number in fields[2:]]
                assert len(values) == 14
                frame["banks"].append(values[:12] + [0] + values[12:])
            elif fields[0] == "PIN_END":
                assert frame is not None
                yield frame
                frame = None
    assert frame is None, "truncated public-pin snapshot"


def self_check(run):
    from token_checks import BENCH
    recipes = 0
    for config in manifest()["matrix"]:
        definition = recipe(config["fp_format"], config["weight_mode"], config["cache_mode"],
                            config["banks"], config["seed"])
        parameters = definition["parameters"]
        assert parameters["BANKS"] == config["banks"]
        assert parameters["CACHE_MODE"] == config["cache_mode"]
        assert parameters["FP_FORMAT"] == int(config["fp_format"] == "fp16")
        assert parameters["WEIGHT_MODE"] == config["weight_mode"]
        assert definition["top"] == "anvil_q2_fp_top"
        recipes += 1
        if config["fp_format"] == "fp16" and config["weight_mode"] == 1:
            parent = recipe("fp16", 1, config["cache_mode"], config["banks"], config["seed"], "parent")
            assert parent["top"] == "anvil_q2_top"
            assert "FP_FORMAT" not in parent["parameters"] and "WEIGHT_MODE" not in parent["parameters"]
            assert len(parent["matrix"]) == 18
            recipes += 1
    assert recipes == 90
    subprocess_output = run.command(
        ["python3", "tests/native_reference_checks.py"], "native-reference-self-check",
        timeout=21600)
    receipts = [line for line in subprocess_output.read_text().splitlines() if line.endswith("/receipt.json")]
    assert len(receipts) == 1
    child = json.loads((ROOT / receipts[0]).read_text())
    assert child["outcome"] == "passed-focused-only"
    assert child["source_sha256"] == run.receipt["source_sha256"]
    geometry = Geometry(layers=1, positions=1, vocabulary=1)
    reference = NativeTransformer("fp16", 1, 1, 17, geometry).execute()
    ordinary = Transformer("fp16", 1, 1, 17, geometry)
    definition = recipe("fp16", 1, 1, 2, 17)
    definition.update(shape_class="reduced-self-check", geometry=asdict(geometry))
    definition["parameters"].update(
        NUM_LAYERS=1, HIDDEN_SIZE=48, INTERMEDIATE_SIZE=48, NUM_Q_HEADS=6,
        NUM_KV_HEADS=1, HEAD_DIM=8, GROUP_SIZE=12, VOCAB_SIZE=1, MAX_SEQ_LEN=1, CACHE_BLOCK=2)
    service = MemoryService(definition)
    rejected_coordinates = 0
    for address in (key(8, row=13), key(8, row=0, col=geometry.hidden),
                    key(8, layer=1), key(12, layer=geometry.layers),
                    key(12, row=geometry.positions),
                    key(14, col=geometry.kv_heads * geometry.head_dim // geometry.block),
                    key(9), key(0)):
        try:
            service.write(address, 0)
        except AssertionError:
            rejected_coordinates += 1
        else:
            raise AssertionError("memory service accepted an illegal write coordinate")
    addresses = sorted(set(ordinary.loads) | set(reference.writes))
    memory = run.path / "memory.hex"
    memory.write_text("".join(
        f"{(address << 32) | ordinary.loads.get(address, 0):034x}\n" for address in addresses))
    bench = run.path / "bench.sv"
    text = BENCH
    ack = "pending_data[b]=req_write[b] ? 0 : contents[found];"
    assert text.count(ack) == 1
    text = text.replace(ack, "pending_data[b]=req_write[b] ? "
                        "(32'ha5a55a5a ^ req_tag[b*64+:32]) : contents[found];")
    before, after = text.rsplit("endmodule", 1)
    bench.write_text(with_time_zero_check(before + PIN_TRACE + "\nendmodule" + after))
    run.receipt["generated_sha256"] = {
        run.relative(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (memory, bench)}
    parameters = dict(BANKS=2, FORMAT=1, WEIGHTS=1, CACHE=1, ENTRIES=len(addresses),
                      LAYERS=1, HIDDEN=48, INTERMEDIATE=48, QHEADS=6, KVHEADS=1, DIM=8,
                      GROUP=12, VOCAB=1, POSITIONS=1, BLOCK=2, DEPTH=3)
    binary = compile_model(run, bench, sorted((ROOT / "rtl").glob("*.sv")), parameters)
    arguments = ["+SEED=17", f"+MEMORY={run.relative(memory)}"]
    startup_check(run, binary, arguments)
    trace = run.command([run.relative(binary), *arguments], "simulation", timeout=21600)
    checker = PinChecker(definition, reference)
    for frame in simulated_pins(trace):
        checker.snapshot(frame)
    metrics = checker.finish()
    assert metrics["nonzero_write_acknowledgements"] == metrics["writes_compared"] > 0
    metrics["precision_vs_mathematical"] = NativeMathematicalTransformer(
        17, geometry, observations=reference).execute().precision()
    rejected = {}
    for defect in ("logit-bit", "cache-write-bit", "unknown-response", "read-response-bit"):
        checker, injected = PinChecker(definition, reference), False
        try:
            for frame in simulated_pins(trace):
                if not injected:
                    if defect == "logit-bit" and frame["logit"][:2] == [1, 1]:
                        frame["logit"][3] ^= 1
                        injected = True
                    else:
                        for bank in frame["banks"]:
                            if defect == "cache-write-bit" and bank[:3] == [1, 1, 1] and bank[3] >= 12:
                                bank[8] ^= 1
                                injected = True
                                break
                            if defect == "unknown-response" and bank[10:12] == [1, 1]:
                                bank[14] = 2**64 - 1
                                injected = True
                                break
                            if (defect == "read-response-bit" and bank[10:12] == [1, 1] and
                                    bank[14] in checker.pending and not checker.pending[bank[14]][4]):
                                bank[13] ^= 1
                                injected = True
                                break
                checker.snapshot(frame)
            checker.finish()
        except AssertionError as exc:
            assert injected, "negative trace failed before injection"
            rejected[defect] = str(exc)
        else:
            raise AssertionError(f"checker accepted injected trace defect: {defect}")
    return dict(actual_reduced_rtl=metrics, trace_defects_rejected=rejected,
                illegal_memory_coordinates_rejected=rejected_coordinates,
                native_recipe_configurations_validated_not_executed=recipes,
                reference_self_check_receipt=receipts[0],
                scope="Actual reduced RTL validates the native bridge interface; not native hardware execution.")


def execute(args):
    run = Run("verifier-hardware-vector-interface")
    try:
        run.command(["python3", "--version"], "python-version")
        if args.self_check:
            metrics = self_check(run)
            run.finish("passed-focused-only", metrics=metrics)
        elif args.generate:
            definition = recipe(args.format, args.weights, args.cache, args.banks, args.seed, args.product)
            definition["source_sha256"] = run.receipt["source_sha256"]
            output = run.path / "vectors.json"
            with output.open("x") as stream:
                json.dump(definition, stream, indent=2)
                stream.write("\n")
            run.finish("generated-not-executed", metrics={"recipe": run.relative(output)})
        else:
            recipe_path, trace_path = map(relative_input, args.compare)
            definition = json.loads(recipe_path.read_text())
            config = definition["selected"]
            expected_recipe = recipe(config["fp_format"], config["weight_mode"], config["cache_mode"],
                                     config["banks"], config["seed"], definition["product"])
            assert definition == expected_recipe | {"source_sha256": run.receipt["source_sha256"]}, (
                "recipe contract/source identity mismatch")
            model = (NativeParentTransformer(config["cache_mode"], config["seed"])
                     if definition["product"] == "parent" else
                     NativeTransformer(config["fp_format"], config["weight_mode"],
                                       config["cache_mode"], config["seed"])).execute()
            checker = PinChecker(definition, model)
            run.receipt["input_sha256"] = {
                run.relative(path): digest_file(path)
                for path in (recipe_path, trace_path)}
            with trace_path.open() as stream:
                for line in stream:
                    checker.snapshot(json.loads(line))
            metrics = checker.finish()
            metrics["precision_vs_mathematical"] = NativeMathematicalTransformer(
                config["seed"], observations=model,
                parent=definition["product"] == "parent").execute().precision()
            run.finish("passed-focused-only", metrics=metrics,
                       limitations="Normative native bit/protocol trace checks, not physical provenance/timing approval.")
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError, KeyError, TypeError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--self-check", action="store_true")
    operation.add_argument("--generate", action="store_true")
    operation.add_argument("--compare", nargs=2, metavar=("RECIPE", "TRACE"))
    parser.add_argument("--format", choices=("bf16", "fp16"), default="bf16")
    parser.add_argument("--weights", type=int, choices=(0, 1), default=0)
    parser.add_argument("--cache", type=int, choices=(0, 1), default=0)
    parser.add_argument("--banks", type=int, choices=(1, 2, 4), default=4)
    parser.add_argument("--seed", type=int, choices=(17, 43, 89), default=17)
    parser.add_argument("--product", choices=("fp", "parent"), default="fp")
    raise SystemExit(execute(parser.parse_args()))
