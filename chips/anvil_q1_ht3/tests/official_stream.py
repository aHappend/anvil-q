"""Public-pin compiled inference with complete, source-bound mid-token checkpoints."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from execution import (ROOT, clean_objects, execute, hashes, relative, remaining,
                       timestamp)
from retention import artifacts_intact, digest, execution_logs_intact
from campaign import (artifact, available, canonical_argv, logical, preserve)


TOP = "anvil_q1_ht3_top"
DRIVER = "tests/official_stream.cpp"
DEPENDENCIES = [DRIVER, "tests/official_stream.py", "tests/execution.py",
                "tests/campaign.py"]
COMPILE_OPTIONS = ["-O3", "-CFLAGS", "-O3"]
SUMMARY = re.compile(
    r"^SHARD cycles=(\d+) state=(\d+) accepted=(\d+) completed=(\d+) "
    r"current_logits=(\d+) reads=(\d+) writes=(\d+) debt=(\d+) csr=(\d+) "
    r"stalls=(\d+) max_debt=(\d+) complete=([01])$", re.MULTILINE)
SUMMARY_KEYS = ("cycles", "host_state", "accepted", "completed", "current_logits",
                "reads", "writes", "debt", "csr", "stalls", "max_debt", "complete")
TOKEN = re.compile(
    r"^TOKEN position=(\d+) id=(\d+) cycles=(\d+) reads=(\d+) writes=(\d+) "
    r"logits=(\d+) scored=([01])$", re.MULTILINE)


def compiled(output, parameters=None):
    sources = [relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))]
    current = hashes()
    version = execute(["verilator", "--version"], output, "stream-version",
                      ["verilator", "--version"]).strip()
    identity = dict(schema=1, top=TOP, parameters=parameters or {},
                    source_sha256={p: current[p] for p in [*sources, *DEPENDENCIES]},
                    tool_version=version, savable=True, public_pins_only=True,
                    compile_options=COMPILE_OPTIONS)
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
    cache = ROOT/"evidence/compiled"
    cache.mkdir(parents=True, exist_ok=True)
    for candidate in sorted(cache.glob(f"official-stream-{key}-*")):
        path, binary = candidate/"binding.json", candidate/"compile-obj"/f"V{TOP}"
        if not available(path) or not available(binary):
            continue
        record = json.loads(artifact(path).read_text())
        required = [relative(p) for p in (binary, candidate/"compile-obj/driver.cpp",
                    *[candidate/f"compile.{suffix}" for suffix in
                      ("receipt.json", "stdout.txt", "stderr.txt")])]
        if (record.get("identity") != identity
                or not artifacts_intact(record.get("artifact_sha256", {}), required)):
            continue
        receipt = json.loads(artifact(ROOT/record["compile_receipt"]).read_text())
        if (receipt.get("exit") == 0 and not receipt.get("timed_out")
                and execution_logs_intact(receipt)):
            preserve([path], "validated official stream build")
            return artifact(binary), path
    directory = cache/f"official-stream-{key}-{uuid.uuid4().hex[:12]}"
    objects = directory/"compile-obj"
    objects.mkdir(parents=True)
    shutil.copyfile(ROOT/DRIVER, objects/"driver.cpp")
    execute(["verilator", "--cc", "--exe", "--build", "--savable",
             "-Wno-fatal", "-j", "2", *COMPILE_OPTIONS,
             "--top-module", TOP, "--Mdir", relative(objects),
             *[f"-G{k}={v}" for k, v in (parameters or {}).items()],
             *sources, "driver.cpp"], directory, "compile", ["verilator", "--version"])
    binary = objects/f"V{TOP}"
    if not binary.is_file():
        raise AssertionError("zero compiler exit without official stream executable")
    artifacts = [binary, objects/"driver.cpp",
                 *[directory/f"compile.{suffix}" for suffix in
                   ("receipt.json", "stdout.txt", "stderr.txt")]]
    binding = directory/"binding.json"
    with binding.open("x") as out:
        json.dump(dict(identity=identity, compile_receipt=relative(directory/"compile.receipt.json"),
                       binary_sha256=digest(binary),
                       artifact_sha256={relative(p): digest(p) for p in artifacts}), out, indent=2)
    clean_objects(objects)
    preserve([binding], "official stream build and copied driver")
    return binary, binding


def intact(record):
    return artifacts_intact(record.get("artifact_sha256", {}))


def plan_bytes(descriptors, memory_bytes, tokens, scored, vocab):
    commands = [(0x0000, 0, 0, 0xffffffff, 0x02000001),
                (0x0154, 0, 0, 0xffffffff, 0x03000003),
                (0x0100, 0, 1, 0, 0)]
    for row in descriptors:
        values = (row["index"], row["kind"], row["layer"], row["projection"],
                  row["base"] & 0xffffffff, row["base"] >> 32, row["length"], 1)
        commands.extend((0x0010+4*i, value, 1, 0, 0) for i, value in enumerate(values))
        commands.append((0x0028, 0, 0, 0xffffffff, row["length"]))
    commands.extend([(0x0008, 6, 1, 0, 0), (0x0108, 0, 0, 0xfffffffb, 3)])
    lines = [f"HT3STREAM1 {vocab} {memory_bytes} {len(commands)} {len(tokens)}"]
    lines.extend(" ".join(map(str, row)) for row in commands)
    lines.extend(f"{token} {position} {int(position in scored)}"
                 for position, token in enumerate(tokens))
    return ("\n".join(lines)+"\n").encode()


def summary(text):
    matches = SUMMARY.findall(text)
    if len(matches) != 1:
        raise AssertionError("missing or duplicate complete stream-shard summary")
    result = dict(zip(SUMMARY_KEYS, map(int, matches[0])))
    if bool(result["complete"]) != (result["host_state"] == 5):
        raise AssertionError("stream completion flag/state mismatch")
    return result


def validated_chain(path, identity):
    """Every settled predecessor, raw log and complete checkpoint is hash-checked."""
    chain, seen = [], set()
    while path is not None:
        if path in seen or not available(path):
            return None
        seen.add(path)
        row = json.loads(artifact(path).read_text())
        if row.get("identity") != identity or not intact(row):
            return None
        receipt = json.loads(artifact(ROOT/row["receipt"]).read_text())
        if (receipt.get("exit") != 0 or receipt.get("timed_out")
                or receipt.get("tool_version_exit") != 0
                or receipt.get("tool_version", "").strip() != identity["tool_version"]):
            return None
        argv = canonical_argv(receipt.get("argv", []))
        if (argv != canonical_argv(row.get("argv", []))
                or not argv or argv[0] != identity["binary"]
                or "--plan" not in argv or "--image" not in argv
                or argv[argv.index("--image")+1] != identity["image"]
                or row["artifact_sha256"].get(argv[argv.index("--plan")+1]) !=
                   identity["plan_sha256"]
                or any(receipt.get("source_sha256", {}).get(p) != sha
                       for p, sha in identity["source_sha256"].items())):
            return None
        observed = summary(artifact(ROOT/receipt["stdout"]).read_text())
        if observed != row.get("summary"):
            return None
        row["binding"] = relative(path)
        chain.append(row)
        predecessor = row.get("predecessor")
        if predecessor:
            path = ROOT/predecessor["binding"]
            if not available(path) or digest(path) != predecessor["sha256"]:
                return None
        else:
            path = None
    chain.reverse()
    previous_cycles = 0
    for index, row in enumerate(chain):
        if (row["summary"]["cycles"] <= previous_cycles
                or (index and chain[index-1]["summary"]["complete"])):
            return None
        previous_cycles = row["summary"]["cycles"]
        argv = canonical_argv(row["argv"])
        if "--restore" in argv:
            if not index:
                return None
            prefix = argv[argv.index("--restore")+1]
            original = chain[index-1]["checkpoint"]
            if prefix != original:
                relocation = row.get("checkpoint_relocation", {})
                if relocation != dict(original=original, restored=prefix):
                    return None
                for suffix in (".rtl.bin", ".host.bin"):
                    sha = chain[index-1]["artifact_sha256"].get(original+suffix)
                    if (sha is None or row["artifact_sha256"].get(prefix+suffix) != sha
                            or digest(ROOT/(prefix+suffix)) != sha):
                        return None
        elif index:
            return None
    return chain


def run_stream(output, image, descriptors, tokens, scored, vocab, binary, binding,
               chunk_cycles=None, max_new_chunks=None):
    plan = output/"stream-plan.txt"
    plan.write_bytes(plan_bytes(descriptors, image["image_bytes"], tokens, scored, vocab))
    build = json.loads(artifact(binding).read_text())
    current = hashes()
    sources = [relative(p) for p in sorted(ROOT.glob("rtl/*.sv"))]+DEPENDENCIES
    if (digest(ROOT/image["image"]) != image["image_sha256"] or
            not intact(build) or any(
                build["identity"]["source_sha256"].get(p) != current[p] for p in sources)):
        raise AssertionError("stream input/build no longer matches the captured source image")
    identity = dict(schema=1, source_sha256={p: current[p] for p in sources},
                    tool_version=build["identity"]["tool_version"],
                    binary=logical(binary), binary_sha256=digest(binary),
                    build_binding_sha256=digest(binding), plan_sha256=digest(plan),
                    image=image["image"], image_sha256=image["image_sha256"],
                    image_bytes=image["image_bytes"],
                    clock="simulated 200 MHz core / 100 MHz DDR; not STA",
                    memory="one FIFO response beat per DDR edge, no artificial latency",
                    consumer="not ready every fifth core edge")
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:24]
    cache = ROOT/"evidence/compiled"/f"official-state-{key}"
    cache.mkdir(parents=True, exist_ok=True)
    chain = []
    candidates = sorted(cache.glob("chunk-*/binding.json"),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    for candidate in candidates:
        checked = validated_chain(candidate, identity)
        if checked is not None and (not chain or
                checked[-1]["summary"]["cycles"] > chain[-1]["summary"]["cycles"]):
            chain = checked
            # Later settled shards point to every earlier one.
            break
    reused = len(chain)
    while not chain or not chain[-1]["summary"]["complete"]:
        if remaining() < 90 or (max_new_chunks is not None and len(chain)-reused >= max_new_chunks):
            break
        if chunk_cycles is not None:
            cycles = chunk_cycles
        elif not chain:
            cycles = 10000
        else:
            prior = chain[-1]
            receipt = json.loads(artifact(ROOT/prior["receipt"]).read_text())
            start_cycles = chain[-2]["summary"]["cycles"] if len(chain) > 1 else 0
            rate = (prior["summary"]["cycles"]-start_cycles)/max(0.01, receipt["duration_s"])
            cycles = max(1, min(2000000, int(rate*min(60, (remaining()-60)/2))))
        directory = cache/f"chunk-{uuid.uuid4().hex[:12]}"
        directory.mkdir()
        argv = [relative(artifact(binary)), "--plan", relative(plan),
                "--image", relative(artifact(ROOT/image["image"])),
                "--output", relative(directory), "--cycles", str(cycles)]
        relocation, relocated_files = None, []
        if chain:
            checkpoint = chain[-1]["checkpoint"]
            rtl = artifact(ROOT/(checkpoint+".rtl.bin"))
            host = artifact(ROOT/(checkpoint+".host.bin"))
            if rtl.parent != host.parent:
                # The driver consumes a two-file prefix. Relocated pieces must
                # be assembled together in a fresh, explicitly bound namespace.
                restored = directory/f"restore-{uuid.uuid4().hex[:12]}"
                restored.mkdir()
                for source, suffix in ((rtl, ".rtl.bin"), (host, ".host.bin")):
                    shutil.copyfile(source, restored/("checkpoint"+suffix))
                    if digest(source) != digest(restored/("checkpoint"+suffix)):
                        raise AssertionError("checkpoint relocation changed bytes")
                    relocated_files.append(restored/("checkpoint"+suffix))
                argv += ["--restore", relative(restored/"checkpoint")]
                relocation = dict(original=checkpoint, restored=relative(restored/"checkpoint"))
            else:
                argv += ["--restore", relative(rtl.with_suffix("").with_suffix(""))]
        text = execute(argv, directory, "simulation", ["verilator", "--version"])
        observed = summary(text)
        artifacts = [directory/"checkpoint.rtl.bin", directory/"checkpoint.host.bin",
                     *[directory/f"simulation.{suffix}" for suffix in
                       ("receipt.json", "stdout.txt", "stderr.txt")],
                     *sorted(directory.glob("position-*.f32")), plan, *relocated_files]
        if not all(p.is_file() for p in artifacts):
            raise AssertionError("stream zero exit without complete checkpoints")
        row = dict(identity=identity, argv=argv, summary=observed,
                   checkpoint_relocation=relocation,
                   checkpoint=relative(directory/"checkpoint"),
                   predecessor=(dict(binding=chain[-1]["binding"],
                                     sha256=digest(ROOT/chain[-1]["binding"])) if chain else None),
                   receipt=relative(directory/"simulation.receipt.json"),
                   artifact_sha256={relative(p): digest(p) for p in artifacts})
        path = directory/"binding.json"
        with path.open("x") as out:
            json.dump(row, out, indent=2)
        preserve([path, binding, ROOT/image["image"],
                  *([ROOT/chain[-1]["binding"]] if chain else [])],
                 "settled RTL stream checkpoint and full input closure")
        row["binding"] = relative(path)
        chain.append(row)
        print(f"STREAM_PROGRESS cycles={observed['cycles']} "
              f"completed={observed['completed']}/{len(tokens)} "
              f"logits={observed['current_logits']}/{vocab}", flush=True)
    observations, measurements = {}, []
    for row in chain:
        directory = (ROOT/row["binding"]).parent
        text = artifact(directory/"simulation.stdout.txt").read_text()
        for match in TOKEN.findall(text):
            position, token, cycles, reads, writes, count, is_scored = map(int, match)
            if (position != len(measurements) or position >= len(tokens) or
                    token != tokens[position] or count != vocab or
                    bool(is_scored) != (position in scored) or cycles <= 0):
                raise AssertionError("missing, duplicated or misassociated completed official token")
            measurements.append(dict(position=position, token=token, cycles=cycles,
                                     ddr_read_beats=reads, ddr_write_beats=writes,
                                     simulated_tpm=60*200000000/cycles))
            if is_scored:
                path = directory/f"position-{position}.f32"
                if artifact(path).stat().st_size != 4*vocab:
                    raise AssertionError("short official RTL logit vector")
                values = np.fromfile(artifact(path), dtype="<f4").astype(np.float64)
                if not np.isfinite(values).all():
                    raise AssertionError("nonfinite captured official RTL logits")
                observations[position] = dict(path=relative(path), sha256=digest(path))
    complete = bool(chain and chain[-1]["summary"]["complete"])
    if chain and chain[-1]["summary"]["completed"] != len(measurements):
        raise AssertionError("checkpoint completion count differs from actual token summaries")
    if complete and (len(measurements) != len(tokens) or list(observations) != sorted(scored)):
        raise AssertionError("completed stream lacks mandatory scored/prefill/decode observations")
    result = dict(status="passed" if complete else "incomplete",
                  scope="compiled public-pin RTL stream only; numerical scoring is separate",
                  binary_binding=relative(binding), identity=identity,
                  summary=chain[-1]["summary"] if chain else None,
                  checkpoints=[row["binding"] for row in chain], reused_chunks=reused,
                  new_chunks=len(chain)-reused, observations=observations,
                  measurements=measurements, required_tokens=len(tokens),
                  required_scored_positions=sorted(scored))
    with (output/"stream-result.json").open("x") as out:
        json.dump(result, out, indent=2)
    return result


def self_test(output):
    from run_compatibility import fixture, logit_check

    fixture_dir = output/"checkpoint-images"
    fixture_dir.mkdir()
    vectors, expected = fixture(fixture_dir, 0, 17)
    lines = vectors.read_text().splitlines()
    _, uploads, count, ntokens = map(int, lines[0].split())
    memory = bytearray(uploads*64)
    for line in lines[1:uploads+1]:
        address, data = line.split()
        start = int(address, 16)
        memory[start:start+64] = int(data, 16).to_bytes(64, "little")
    image_path = fixture_dir/"image.bin"
    image_path.write_bytes(memory)
    descriptors = []
    for line in lines[uploads+1:uploads+count+1]:
        index, kind, layer, projection, base, length = line.split()
        descriptors.append(dict(index=int(index), kind=int(kind), layer=int(layer),
                                projection=int(projection), base=int(base, 16), length=int(length)))
    traffic = [list(map(int, line.split())) for line in lines[-ntokens:]]
    # This stream resumes a single contiguous sequence; the fixture's final
    # fresh-sequence token is verified separately by the compatibility suite.
    tokens = [row[0] for row in traffic[:2]]
    parameters = dict(NUM_LAYERS=1, HIDDEN_SIZE=8, INTERMEDIATE_SIZE=8,
                      NUM_Q_HEADS=1, NUM_KV_HEADS=1, HEAD_DIM=8,
                      GROUP_SIZE=8, VOCAB_SIZE=3, MAX_SEQ_LEN=4,
                      TILE_BEATS=3, KV_WINDOW=3, FLASH_TILE=3)
    binary, binding = compiled(output, parameters)
    image = dict(image=relative(image_path), image_bytes=len(memory), image_sha256=digest(image_path))
    first = output/f"first-{uuid.uuid4().hex[:12]}"
    second = output/f"resume-{uuid.uuid4().hex[:12]}"
    first.mkdir()
    second.mkdir()
    a = run_stream(first, image, descriptors, tokens, {0, 1}, 3, binary, binding,
                   chunk_cycles=4096, max_new_chunks=1)
    b = run_stream(second, image, descriptors, tokens, {0, 1}, 3, binary, binding,
                   chunk_cycles=4096)
    if b["status"] != "passed" or b["reused_chunks"] < len(a["checkpoints"]):
        raise AssertionError("compiled stream did not complete and resume validated work")
    metrics = [logit_check(np.fromfile(ROOT/b["observations"][p]["path"], dtype="<f4").tolist(),
                           expected[p]) for p in range(2)]
    last = b["summary"]
    if min(last[k] for k in ("reads", "writes", "csr", "stalls", "max_debt")) <= 0:
        raise AssertionError("stream transactor lacks actual protocol observations")
    return dict(status="passed", compact_geometry=parameters, fp64_logits=metrics,
                first=relative(first/"stream-result.json"),
                resumed=relative(second/"stream-result.json"),
                scope="compact transactor/checkpoint verification, not official model acceptance")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--self-test", action="store_true", required=True)
    args = parser.parse_args()
    output = ROOT/args.output
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(argv=["python3", "tests/official_stream.py", *sys.argv[1:]], cwd=".",
                   start=timestamp(), timeout=remaining(), source_sha256=hashes(),
                   tool_version=sys.version)
    try:
        result = self_test(output)
    except (OSError, RuntimeError, AssertionError, ValueError, KeyError) as exc:
        result = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    with (output/"result.json").open("x") as out:
        json.dump(result, out, indent=2)
    receipt.update(end=timestamp(), exit=int(result["status"] != "passed"),
                   timed_out=remaining() <= 0, result=relative(output/"result.json"))
    with (output/"receipt.json").open("x") as out:
        json.dump(receipt, out, indent=2)
    print(json.dumps(result), flush=True)
    return receipt["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
