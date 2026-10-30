"""Independent public-pin decoder stimuli and exact full-array comparison.

Accepted-token requests and writes must follow token acceptance and cannot
follow completion; correct payloads do not excuse noncausal trace timestamps.
Token acceptance records must match the independently supplied workload IDs.
DONE timestamps name the edge after which done is observed, so they must equal
the final logit's pre-edge acceptance timestamp, not a later edge.
Each logged memory write must match an accepted write request of the same
token, kind and edge, including aborted traffic; payload comparison alone
does not establish request ownership.
Large or multi-token interpreted requests dispatch a compact portability smoke
and the unchanged complete workload on the compiled simulator. These are recorded
as different coverage scopes, not the originally admitted full Icarus matrix.
"""

from collections import Counter, defaultdict, deque
from dataclasses import asdict
import json
import re

from execution import ROOT, VERILATOR_UNROLL, sha256, write_json
from native_baselines import native_q1_sources
from reference import AdversarialFixture, Fixture


class NumericalMismatch(AssertionError):
    pass


def validate_simulation_tier(g, simulator, tokens):
    if simulator not in ("iverilog", "verilator"):
        raise ValueError("unknown decoder simulator: " + simulator)
    return simulator == "iverilog" and not (
        g.BANKS == 1 and g.HIDDEN_SIZE <= 32 and g.NUM_LAYERS == 1 and
        g.INTERMEDIATE_SIZE <= 8 and g.VOCAB_SIZE == 1 and len(tokens) == 1)


def trace_records(path):
    schemas = {
        "FAULT_WRITE": (9, 7), "WRITE": (9, 7), "LOGIT": (5, None),
        "DONE": (3, None), "TOKEN": (4, None), "REQUEST": (7, None),
        "FAULT_REQUEST": (7, None), "STALLS": (4, None), "SUMMARY": (6, None),
        "REJECT": (3, None), "IDLE_CANCEL": (1, None), "ACTIVE_CANCEL": (3, None),
        "ABORTED": (5, None), "COMPARED": (6, None),
    }
    offset = 0
    with path.open("rb") as stream:
        yield from _trace_lines(stream, schemas, path)


def _trace_lines(stream, schemas, path):
    offset = 0
    for number, raw in enumerate(stream, 1):
        location = f"{path.name}: line {number}, byte {offset}"
        offset += len(raw)
        if not raw.endswith(b"\n"):
            raise AssertionError(location + ": unterminated trace record")
        try:
            fields = raw.decode("ascii").rstrip("\r\n").split("\t")
        except UnicodeDecodeError as exc:
            raise AssertionError(location + ": non-ASCII trace record") from exc
        fields[0] = fields[0].strip()
        if fields[0] not in schemas:
            raise AssertionError(location + ": unknown trace record " + repr(fields[0]))
        count, hex_field = schemas[fields[0]]
        if len(fields) != count:
            raise AssertionError(location + f": {fields[0]} requires {count} fields, got {len(fields)}")
        for index, value in enumerate(fields[1:], 1):
            pattern = r"[0-9a-fA-F]{8}" if index == hex_field else r"-?[0-9]+"
            if re.fullmatch(pattern, value) is None:
                raise AssertionError(location + f": invalid {fields[0]} field {index}: {value!r}")
        yield fields


def allocate(fixture, folder, tokens):
    g = fixture.g
    shapes = {}

    def region(kind, layer, proj, rows, cols):
        shapes[kind, layer, proj] = rows, cols

    region(0, 0, 0, g.VOCAB_SIZE, g.HIDDEN_SIZE)
    for layer in range(g.NUM_LAYERS):
        for p in range(7):
            inputs, outputs = g.dimensions(p)
            region(1, layer, p, inputs, (outputs + 7) // 8)
            region(2, layer, p, inputs // g.GROUP_SIZE, (outputs + 7) // 8)
            region(3, layer, p, inputs // g.GROUP_SIZE, outputs)
            if p < 3:
                region(4, layer, p, 1, outputs)
        for kind in (5, 6):
            region(kind, layer, 0, 1, g.HIDDEN_SIZE)
        for kind in (9, 10):
            region(kind, layer, 0, g.MAX_SEQ_LEN, g.NUM_KV_HEADS * g.HEAD_DIM)
        for kind in (12, 13):
            words = (g.capacity * (4 if g.CACHE_MODE == 2 else 8) + 31) // 32 if g.CACHE_MODE else 1
            region(kind, layer, 0, g.MAX_SEQ_LEN, g.NUM_KV_HEADS * g.blocks * words)
        for kind in (14, 15):
            region(kind, layer, 0, g.MAX_SEQ_LEN, g.NUM_KV_HEADS * g.blocks)
    region(7, 0, 0, 1, g.HIDDEN_SIZE)
    region(8, 0, 0, 15, max(g.HIDDEN_SIZE, g.INTERMEDIATE_SIZE))
    region(11, 0, 0, g.MAX_SEQ_LEN, g.HEAD_DIM)
    offsets, memory, lines = {}, [], []
    for key, (rows, cols) in sorted(shapes.items()):
        offsets[key] = len(memory)
        lines.append("%d %d %d %d %d %d" % (*key, len(memory), rows, cols))
        memory.extend([0] * (rows * cols))
    for (kind, layer, p, row, col), value in fixture.memory.items():
        rows, cols = shapes[kind, layer, p]
        assert 0 <= row < rows and 0 <= col < cols
        memory[offsets[kind, layer, p] + row * cols + col] = value
    (folder / "map.tsv").write_text("\n".join(lines) + "\n")
    (folder / "memory.hex").write_text("".join("%08x\n" % v for v in memory))
    (folder / "tokens.txt").write_text("".join("%d\n" % v for v in tokens))
    return len(memory)


def compare_trace(folder, expected, g, prelude=0, boundary=0, restart_at=None, fault_scenario=0,
                  *, expected_tokens):
    if (len(expected_tokens) != len(expected["logits"]) or
            any(type(token) is not int or not 0 <= token < g.VOCAB_SIZE
                for token in expected_tokens)):
        raise AssertionError("invalid independent token workload")
    queues = defaultdict(deque)
    for row in expected["writes"]:
        queues[tuple(row[:6])].append(row[6])
    actual_logits = [[] for _ in expected["logits"]]
    logit_cycles = [[] for _ in expected["logits"]]
    compared = 0
    summary = None
    done = []
    rejections = []
    idle_cancels = 0
    active_cancels = 0
    traffic = defaultdict(int)
    start_cycles, end_cycles = {}, {}
    stalls = None
    aborted = []
    fault_requests = 0
    fault_writes = 0
    streamed = {}
    request_cycles = defaultdict(list)
    write_cycles = defaultdict(list)
    write_requests = Counter()
    observed_writes = Counter()
    abort_expected = defaultdict(deque)
    for row in expected["writes"]:
        if row[0] == 0:
            abort_expected[tuple(row[1:6])].append(row[6])
    for fields in trace_records(folder / "trace.tsv"):
        if fields[0] == "COMPARED":
            token, writes, requests, weights, cache = map(int, fields[1:])
            if (token in streamed or not (0 <= token < len(actual_logits) or token == -2) or
                    min(writes, requests, weights, cache) < 0 or writes > requests or
                    weights % 4 or cache % 4 or weights + cache > 4 * requests):
                raise AssertionError("invalid/duplicate streaming comparison summary")
            streamed[token] = writes
            traffic["total"] += requests
            traffic["weight_bytes"] += weights
            traffic["cache_payload_metadata_bytes"] += cache
            compared += 32 * writes
            if token == -2:
                fault_requests = requests
                fault_writes = writes
        elif fields[0] == "FAULT_WRITE":
            if int(fields[1]) != -2:
                raise AssertionError("invalid aborted token identity")
            key = tuple(map(int, fields[2:7]))
            observed_writes[-2, key[0], int(fields[8])] += 1
            if not abort_expected[key]:
                raise AssertionError("unexpected aborted-token write " + str(key))
            required = abort_expected[key].popleft()
            if int(fields[7], 16) != required:
                raise NumericalMismatch("aborted-token write differs from independent prefix oracle")
            compared += 32
            fault_writes += 1
        elif fields[0] == "WRITE":
            key = tuple(map(int, fields[1:7]))
            token, cycle = key[0], int(fields[8])
            if token not in start_cycles or cycle <= start_cycles[token]:
                raise AssertionError("write precedes its accepted token")
            write_cycles[token].append(cycle)
            observed_writes[token, key[1], cycle] += 1
            observed = int(fields[7], 16)
            if not queues[key]:
                raise AssertionError("unexpected/duplicate write %s value %08x" % (key, observed))
            required = queues[key].popleft()
            if observed != required:
                raise NumericalMismatch("write %s expected %08x observed %08x" % (key, required, observed))
            compared += 32
        elif fields[0] == "LOGIT":
            token, index, value, cycle = map(int, fields[1:])
            if not 0 <= token < len(actual_logits):
                raise AssertionError("logit token outside accepted workload")
            if index != len(actual_logits[token]):
                raise AssertionError("logit index order")
            actual_logits[token].append(value)
            logit_cycles[token].append(cycle)
            required = expected["logits"][token][index]
            if value != required:
                raise NumericalMismatch("logit token %d index %d expected %d observed %d" %
                                     (token, index, required, value))
            compared += 32
        elif fields[0] == "DONE":
            done.append(int(fields[1]))
            end_cycles[int(fields[1])] = int(fields[2])
        elif fields[0] == "TOKEN":
            token, identifier, cycle = map(int, fields[1:])
            if not 0 <= token < len(actual_logits) or token in start_cycles or cycle < 0:
                raise AssertionError("invalid/duplicate token timing record")
            if identifier != expected_tokens[token]:
                raise AssertionError("accepted token identifier differs from independent workload")
            start_cycles[token] = cycle
        elif fields[0] in ("REQUEST", "FAULT_REQUEST"):
            token, bank, kind, write, cycle, tag = map(int, fields[1:])
            if (not 0 <= bank < g.BANKS or not 0 <= kind < 16 or
                    write not in (0, 1) or not 0 <= tag < (1 << 64) or cycle < 0):
                raise AssertionError("invalid public memory request fields")
            if write and kind not in (8, 9, 10, 12, 13, 14, 15):
                raise AssertionError("memory write targets immutable tensor")
            if fields[0] == "FAULT_REQUEST":
                if not fault_scenario or token != -2:
                    raise AssertionError("request has no aborted-token owner")
            else:
                if token not in start_cycles or cycle <= start_cycles[token]:
                    raise AssertionError("request precedes its accepted token")
                request_cycles[token].append(cycle)
            if write:
                write_requests[token, kind, cycle] += 1
            traffic["total"] += 1
            if fields[0] == "FAULT_REQUEST":
                fault_requests += 1
            if kind in (1, 2, 3) and not write:
                traffic["weight_bytes"] += 4
            if kind in (9, 10, 12, 13, 14, 15):
                traffic["cache_payload_metadata_bytes"] += 4
        elif fields[0] == "STALLS":
            if stalls is not None:
                raise AssertionError("duplicate stall summary")
            stalls = dict(zip(("request", "response", "logit"), map(int, fields[1:])))
        elif fields[0] == "SUMMARY":
            if summary is not None:
                raise AssertionError("duplicate summary")
            summary = list(map(int, fields[1:]))
        elif fields[0] == "REJECT":
            rejections.append(tuple(map(int, fields[1:])))
        elif fields[0] == "IDLE_CANCEL":
            idle_cancels += 1
        elif fields[0] == "ACTIVE_CANCEL":
            if fields[1:] != ["1", "1"]:
                raise AssertionError("unconserved cancelled transactions")
            active_cancels += 1
        elif fields[0] == "ABORTED":
            aborted.append(list(map(int, fields[1:])))
        else:
            raise AssertionError("unknown trace record " + fields[0])
    remaining = {str(key): len(values) for key, values in queues.items() if values}
    if streamed:
        required_counts = Counter(row[0] for row in expected["writes"])
        if (set(streamed) != set(range(len(actual_logits))) | ({-2} if fault_scenario else set()) or
                any(streamed[i] != required_counts[i] for i in range(len(actual_logits))) or
                write_requests or observed_writes):
            raise AssertionError("streamed complete-write comparisons missing or mixed with raw trace")
        if fault_scenario and streamed[-2] > required_counts[0]:
            raise AssertionError("aborted writes exceed independent token prefix")
    elif remaining:
        raise AssertionError("missing expected writes " + json.dumps(remaining))
    if observed_writes != write_requests:
        raise AssertionError("memory writes differ from accepted write requests: "
                             f"unowned={dict(observed_writes - write_requests)}, "
                             f"unlogged={dict(write_requests - observed_writes)}")
    if actual_logits != expected["logits"]:
        raise AssertionError("incomplete logits")
    count = len(expected["logits"])
    if done != list(range(count)) or summary is None or summary[:2] != [count, count]:
        raise AssertionError("missing/duplicate completions or summary")
    if summary[2] != summary[3] or summary[2] <= 0 or compared <= 0:
        raise AssertionError("empty or unconserved transactions")
    if traffic["total"] != summary[2] or stalls is None:
        raise AssertionError("missing per-request traffic/stall records")
    if set(start_cycles) != set(range(count)) or set(end_cycles) != set(range(count)):
        raise AssertionError("incomplete per-token cycle measurements")
    if any(cycle > end_cycles[token]
           for token, cycles in request_cycles.items() for cycle in cycles):
        raise AssertionError("memory request follows token completion")
    if any(cycle > end_cycles[token]
           for token, cycles in write_cycles.items() for cycle in cycles):
        raise AssertionError("memory write follows token completion")
    if (summary[4] <= 0 or any(value < 0 for value in stalls.values()) or
            any(end_cycles[i] <= start_cycles[i] for i in range(count))):
        raise AssertionError("noncausal/negative benchmark cycle or stall measurement")
    for token in range(count):
        cycles = logit_cycles[token]
        if (not cycles or cycles[0] <= start_cycles[token] or
                any(later <= earlier for earlier, later in zip(cycles, cycles[1:])) or
                cycles[-1] > end_cycles[token] or end_cycles[token] >= summary[4]):
            raise AssertionError("noncausal logit/completion/summary timing")
        if end_cycles[token] != cycles[-1]:
            raise AssertionError("completion is not the final-logit post-edge cycle")
        if token and start_cycles[token] <= end_cycles[token - 1]:
            raise AssertionError("overlapping serialized token intervals")
    required_rejections = {0: [], 1: [(1, 0)], 2: [(1, 1), (1, 0)],
                           3: [(1, 0)], 4: [(g.VOCAB_SIZE, 0), (1, 0)],
                           5: [(1, 0)]}[prelude]
    if boundary:
        position = {1: g.MAX_SEQ_LEN, 2: restart_at, 3: restart_at + 1, 4: 1}[boundary]
        required_rejections += [(0, position), (0, 0)]
    if fault_scenario:
        required_rejections += [(1 if g.VOCAB_SIZE > 1 else 0, 0)]
        if aborted != [[fault_scenario, fault_requests, fault_requests, fault_writes]]:
            raise AssertionError("incomplete fault injection/completion/conservation coverage")
    elif aborted or fault_requests or fault_writes:
        raise AssertionError("unrequested fault scenario")
    if (rejections != required_rejections or idle_cancels != int(prelude == 3) or
            active_cancels != int(prelude == 5)):
        raise AssertionError("incomplete public-interface protocol prelude")
    return {"geometry": asdict(g), "tokens": count, "compared_bits": compared,
            "bit_mismatches": 0, "cycles": summary[4], "requests": summary[2],
            "rejected_commands": rejections, "idle_cancellations": idle_cancels,
            "active_cancellations": active_cancels,
            "integration_fault": aborted,
            "boundary_scenario": boundary, "restart_at": restart_at,
            "token_cycles": [end_cycles[i] - start_cycles[i] + 1 for i in range(count)],
            "traffic": dict(traffic), "stalls": stalls, "logits": actual_logits,
            "trace_sha256": sha256(folder / "trace.tsv"),
            "scope": "exact integer synthetic fixture; not trained-model inference"}


def decoder_case(run, g, seed=17, simulator="iverilog", tokens=None, first_new=1, prefill_tokens=4,
                 prelude=0, label=None, rtl=None, mutation_assertions=(),
                 boundary=0, restart_at=None, fault_scenario=0, adversarial=False,
                 implementation="q3", native_asset=None, testbench="tests/top_tb.sv",
                 stream_compare=True, sparse_scan=True, compiled_host=False,
                 host_cycle_limit=2000000000):
    tokens = tokens if tokens is not None else [1, 4, 2, 6, 3, 5, 7]
    if validate_simulation_tier(g, simulator, tokens):
        from dataclasses import replace
        from parameters import startup_geometry
        compact = replace(startup_geometry(g.PROFILE), BANKS=1, INTERMEDIATE_SIZE=8,
                          VOCAB_SIZE=1, MAX_SEQ_LEN=1, QUEUE_DEPTH=1,
                          TILE_K=8, TILE_ROWS=1,
                          CACHE_MODE=g.CACHE_MODE, INT4_ASYM=g.INT4_ASYM)
        if g.PROFILE != 3:
            compact = replace(compact, HIDDEN_SIZE=8, NUM_Q_HEADS=1)
        smoke = decoder_case(
            run, compact, seed, "iverilog", tokens=[0], prefill_tokens=1,
            first_new=int(g.PROFILE != 1),
            label=(label or "automatic") + f"-requested-b{g.BANKS}-tier-smoke")
        complete = decoder_case(
            run, g, seed, "verilator", tokens=tokens, first_new=first_new,
            prefill_tokens=prefill_tokens, prelude=prelude, label=label, rtl=rtl,
            mutation_assertions=mutation_assertions, boundary=boundary,
            restart_at=restart_at, fault_scenario=fault_scenario, adversarial=adversarial,
            implementation=implementation, native_asset=native_asset, testbench=testbench,
            stream_compare=stream_compare, sparse_scan=sparse_scan, compiled_host=compiled_host,
            host_cycle_limit=host_cycle_limit)
        complete["tier_dispatch"] = {
            "requested_simulator": "iverilog", "actual_full_simulator": "verilator",
            "requested_geometry": asdict(g),
            "compact_smoke": smoke,
            "coverage_limit": "not full-workload Icarus coverage; independent review required"}
        write_json(run.path / complete["result_path"], complete)
        return complete
    testbench = run.rel((ROOT / testbench).resolve())
    if implementation not in ("q3", "q2", "q1-wrapper", "q1-native"):
        raise ValueError("unknown decoder implementation")
    if compiled_host and (simulator != "verilator" or implementation != "q3" or
                          prelude or boundary or restart_at is not None or
                          fault_scenario or not sparse_scan or
                          testbench != "tests/top_tb.sv"):
        raise ValueError("compiled host supports normal Q3 public-pin workloads only")
    if implementation == "q1-native" and (
            native_asset is None or rtl is not None or g.PROFILE != 1 or
            g.BANKS != 1 or g.CACHE_MODE != 0 or prelude or boundary or fault_scenario):
        raise ValueError("native Q1 requires its public source binding and native single-port mode")
    if implementation in ("q2", "q1-wrapper") and (rtl is not None or g.BANKS == 8 or
            g.PROFILE != (1 if implementation == "q1-wrapper" else 2)):
        raise ValueError("unsupported supplied-parent adapter configuration")
    name = (f"decoder-p{g.PROFILE}-l{g.NUM_LAYERS}-h{g.HIDDEN_SIZE}-i{g.INTERMEDIATE_SIZE}"
            f"-d{g.HEAD_DIM}-b{g.BANKS}-m{g.CACHE_MODE}-a{g.INT4_ASYM}-s{seed}-{simulator}"
            + (f"-{label}" if label else "") +
            (f"-{implementation}" if implementation != "q3" else ""))
    folder = run.path / name
    folder.mkdir()
    fixture = (AdversarialFixture if adversarial else Fixture)(g, seed)
    if boundary and (restart_at is None or not 0 < restart_at < len(tokens)):
        raise ValueError("boundary requires successful tokens before and after recovery")
    expected = fixture.oracle(tokens, restart_at=restart_at)
    words = allocate(fixture, folder, tokens)
    write_json(folder / "expected.json", expected)
    mapping = {}
    for line in (folder / "map.tsv").read_text().splitlines():
        kind, layer, proj, base, rows, cols = map(int, line.split())
        mapping[kind, layer, proj] = base, cols
    with (folder / "expected-writes.txt").open("w") as out:
        out.write(str(len(expected["writes"])) + "\n")
        for token, kind, layer, proj, row, col, value in expected["writes"]:
            base, cols = mapping[kind, layer, proj]
            out.write(f"{base + row * cols + col} {token} {value:08x}\n")
    # Bind the exact frozen inputs before invoking either simulator.
    write_json(folder / "fixture.json", {
        "geometry": asdict(g), "seed": seed, "fixture_sha256": fixture.digest(),
        "testbench": {"path": "tests/decoder_host.cpp" if compiled_host else testbench,
                      "sha256": sha256(ROOT / ("tests/decoder_host.cpp"
                                              if compiled_host else testbench))},
        "tokens": tokens, "tokenizer": "synthetic integer IDs; no official tokenizer used",
        "classification": ("adversarial full-range exact-oracle synthetic fixture; no quality bound"
                           if adversarial else "nonzero structural/numerical synthetic fixture"),
        "inputs": {p.name: sha256(p) for p in folder.iterdir() if p.is_file()}})
    parameters = {**asdict(g), "WORDS": words,
                  "IMPLEMENTATION": {"q3": 0, "q2": 1, "q1-wrapper": 2,
                                     "q1-native": 3}[implementation]}
    source_root = ROOT / ("rtl" if implementation == "q3" else "anvil_q2_reference/rtl")
    sources = rtl if rtl is not None else [
        str(p.relative_to(ROOT)) for p in sorted(source_root.glob("*.sv"))]
    source_binding = None
    profiled = compiled_host and g.HIDDEN_SIZE >= 1024 and not mutation_assertions
    if implementation == "q1-native":
        sources, source_binding = native_q1_sources(run, native_asset)
    if simulator == "iverilog":
        binary = folder / "decoder.vvp"
        argv = ["iverilog", "-g2012", "-Wall", "-s", "top_tb", "-o", run.rel(binary)]
        argv += [f"-Ptop_tb.{k}={v}" for k, v in parameters.items()]
        run.tool(argv + sources + [testbench])
        command = ["vvp", run.rel(binary), "+directory=" + run.rel(folder)]
    elif simulator == "verilator":
        obj = folder / "obj"
        if compiled_host and not profiled:
            if "g++" not in getattr(run, "tool_versions", {}):
                run.versions([("g++", "--version")])
            constants = {"BANKS": g.BANKS, "QUEUE_DEPTH": g.QUEUE_DEPTH,
                         "LAYERS": g.NUM_LAYERS, "PROFILE": g.PROFILE,
                         "KV_DIM": g.NUM_KV_HEADS * g.HEAD_DIM,
                         "INTERMEDIATE": g.INTERMEDIATE_SIZE, "HIDDEN": g.HIDDEN_SIZE,
                         "VOCAB": g.VOCAB_SIZE}
            # GCC's vectorized generated wide-register copies fault on an unaligned load.
            # Measured O3/LTO/flattening did not improve this generated model.
            # Keep the effective size optimization explicit, including in make.
            flags = "-Os -fno-tree-vectorize -std=c++20 " + " ".join(
                f"-DHOST_{k}={v}" for k, v in constants.items())
            argv = ["verilator", "--cc", "--exe", "--build", "--assert", "-Wno-fatal",
                    *VERILATOR_UNROLL, "--top-module", "anvil_q3_top",
                    "--Mdir", run.rel(obj), "-o", "decoder", "-CFLAGS", flags,
                    "-MAKEFLAGS", "OPT_FAST=-Os"]
            argv += [f"-G{k}={v}" for k, v in asdict(g).items()]
            # make resolves C++ paths from Mdir; keep the generated command project-relative.
            import os
            host = os.path.relpath(ROOT / "tests/decoder_host.cpp", obj)
            run.tool(argv + sources + [host])
        elif not compiled_host:
            argv = ["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                    *VERILATOR_UNROLL,
                    "--top-module", "top_tb", "--Mdir", run.rel(obj), "-o", "decoder"]
            argv += [f"-G{k}={v}" for k, v in parameters.items()]
            run.tool(argv + sources + [testbench])
        command = [run.rel(obj / "decoder"), "+directory=" + run.rel(folder)]
    else:
        raise ValueError(simulator)
    command += [f"+tokens={len(tokens)}", f"+first_new={first_new}",
                f"+prefill={prefill_tokens}", f"+prelude={prelude}",
                f"+fault={fault_scenario}", f"+boundary={boundary}",
                f"+restart={-1 if restart_at is None else restart_at}",
                f"+stream_compare={int(stream_compare)}", f"+sparse_scan={int(sparse_scan)}"]
    if compiled_host:
        command.append(f"+host_cycles={host_cycle_limit}")
    if profiled:
        from compiled_build import profiled_host
        if "g++" not in getattr(run, "tool_versions", {}):
            run.versions([("g++", "--version")])
        binary = profiled_host(run, g, folder, sources, command[1:])
        command[0] = run.rel(binary)
    text, receipt = run.tool(command, expected=(0, 1, -6) if mutation_assertions else (0,),
                             timeout=14400)
    if profiled:
        run.release_intermediates(binary.parent)
    if mutation_assertions:
        if receipt["exit_code"] != 0:
            if not any(message in text for message in (*mutation_assertions, "NUMERICAL write",
                                                        "NUMERICAL unexpected write",
                                                        "NUMERICAL missing writes")):
                raise AssertionError("mutation failed for an unapproved/nonfunctional reason")
            result = {"functional_mutation_killed": True, "assertion": text,
                      "stdout": receipt["stdout"], "fixture_sha256": fixture.digest()}
        else:
            try:
                compare_trace(folder, expected, g, prelude=prelude,
                              boundary=boundary, restart_at=restart_at, fault_scenario=fault_scenario,
                              expected_tokens=tokens)
            except NumericalMismatch as exc:
                result = {"functional_mutation_killed": True, "assertion": str(exc),
                          "stdout": receipt["stdout"], "fixture_sha256": fixture.digest()}
            else:
                raise AssertionError("mutation survived; no complete numerical/protocol assertion failed")
    else:
        result = compare_trace(folder, expected, g, prelude=prelude,
                               boundary=boundary, restart_at=restart_at, fault_scenario=fault_scenario,
                               expected_tokens=tokens)
    if simulator == "iverilog" and not mutation_assertions and result["cycles"] > 500000:
        raise AssertionError(
            "executed compact smoke exceeded the 500000-cycle Icarus tier; "
            "retained execution is not compliant coverage")
    result["implementation"] = implementation
    result["simulator"] = simulator
    result["driver"] = "clock-stepped-public-pins" if compiled_host else "systemverilog"
    if profiled:
        result["compiler_optimization"] = {
            "method": "fresh GCC profile training; -O3 -fno-tree-vectorize",
            "training_cycles": 1000000, "diagnostic_edge_digest": False,
            "bindings": str((folder / "profile-bindings.json").relative_to(run.path)),
            "scope": "compiler-only; complete independent comparisons unchanged"}
    result["workload"] = {"seed": seed, "tokens": list(tokens),
                          "prefill_tokens": prefill_tokens}
    result["comparison_transport"] = "bounded online exact words" if stream_compare else "raw trace"
    result["result_path"] = str((folder / "result.json").relative_to(run.path))
    result["independent_q1_evidence"] = implementation == "q1-native"
    if source_binding is not None:
        result["native_source_binding"] = source_binding
    write_json(folder / "result.json", result)
    return result
