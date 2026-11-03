#!/usr/bin/env python3
"""Portable source-current L1 verification and retained preparation probes."""

import argparse
import difflib
import hashlib
import json
import random
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import bf16_to_q16, committed_block, dequantize, quantize_group

ROOT = Path(__file__).resolve().parents[1]


def timestamp():
    return datetime.now(timezone.utc).isoformat()


class Experiment:
    def __init__(self, stem, preparation=False):
        suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        self.directory = ROOT / "evidence" / ("preparation" if preparation else "verification") / (
            stem + "-" + suffix)
        self.directory.mkdir(parents=True)
        sources = sorted({p for pattern in (
            "rtl/*.sv", "anvil_d1_reference/rtl/*.sv", "design/*.md",
            "fpga/quartus_gate.json", "tests/*")
            for p in ROOT.glob(pattern) if p.is_file()})
        self.receipt = {
            "started_at": timestamp(),
            "entry_argv": [str(Path(sys.executable).name), "tests/verify.py", *sys.argv[1:]],
            "cwd": ".",
            "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sources},
            "commands": [], "results": {},
        }
        self.save()

    def save(self):
        (self.directory / "receipt.json").write_text(json.dumps(self.receipt, indent=2) + "\n")

    def execute(self, argv, name, timeout=600):
        relative = self.directory.relative_to(ROOT)
        record = {"argv": argv, "cwd": ".", "started_at": timestamp(),
                  "timeout_s": timeout,
                  "stdout": str(relative / (name + ".stdout.txt")),
                  "stderr": str(relative / (name + ".stderr.txt"))}
        self.receipt["commands"].append(record)
        self.save()
        start = time.monotonic()
        try:
            with (ROOT / record["stdout"]).open("w") as stdout, (
                    ROOT / record["stderr"]).open("w") as stderr:
                try:
                    result = subprocess.run(argv, cwd=ROOT, stdout=stdout, stderr=stderr,
                                            timeout=timeout, check=False)
                    record["exit_code"] = result.returncode
                    record["timed_out"] = False
                except subprocess.TimeoutExpired:
                    record["exit_code"] = None
                    record["timed_out"] = True
                    raise
        finally:
            record["ended_at"] = timestamp()
            record["duration_s"] = time.monotonic() - start
            self.save()
        if result.returncode:
            raise RuntimeError(f"{name} exited {result.returncode}; see {record['stdout']} "
                               f"and {record['stderr']}")
        return (ROOT / record["stdout"]).read_text()

    def finish(self, success, error=None):
        self.receipt.update(ended_at=timestamp(), success=success)
        if error:
            self.receipt["error"] = error
        self.save()
        print(str((self.directory / "receipt.json").relative_to(ROOT)), flush=True)

    def cleanup_intermediates(self):
        for directory in self.directory.iterdir():
            if directory.is_dir() and "-obj" in directory.name:
                for pattern in ("*.o", "*.a", "*.gch"):
                    for path in directory.glob(pattern):
                        path.unlink()


def dequant_vectors(path):
    scales = [0x00000001, 0x00000101, 0x007FFFFF, 0x00800000,
              0x00800001, 0x33800000, 0x3EAAAAAB, 0x3F000001,
              0x3F7FFFFF, 0x3F800000, 0x3F800001, 0x3FC00000,
              0x40000000, 0x477FE000, 0x7B000001, 0x7F7FFFFF]
    vectors = [(code, scale) for scale in scales for code in range(256)]
    vectors += [(code, scale) for scale in (
        0x3F808000, 0x3F818000, 0x3FFF8000, 0x007F8000, 0x00008000, 0x7F7F8000)
        for code in range(256)]
    rng = random.Random(17)
    vectors += [(rng.randrange(256), rng.randrange(1, 0x7F800000)) for _ in range(10000)]
    vectors += [(code, scale) for scale in (
        0, 0x80000000, 0xBF800000, 0x7F800000, 0x7FC00001, 0xFF800000)
        for code in (0, 1, 0x38, 0x7E, 0x7F, 0x80, 0xFF)]
    with path.open("w") as stream:
        for code, scale in vectors:
            fp32, bf16, error = dequantize(code, scale)
            stream.write(f"{code:02x} {scale:08x} {fp32:08x} {bf16:04x} {error:x}\n")
    return len(vectors)


def run_dequant(experiment, simulator, rtl="rtl/anvil_d2_fp8_dequant.sv",
                expect_mismatch=False):
    directory = experiment.directory.relative_to(ROOT)
    vectors = experiment.directory / "dequant-vectors.txt"
    count = dequant_vectors(vectors)
    if simulator == "icarus":
        experiment.execute(["iverilog", "-V"], "iverilog-version")
        binary = directory / "dequant.vvp"
        experiment.execute(["iverilog", "-g2012", "-Wall", "-s", "dequant_tb", "-o",
                            str(binary), rtl, "tests/dequant_tb.sv"],
                           "dequant-compile")
        argv = ["vvp", str(binary)]
    else:
        experiment.execute(["verilator", "--version"], "verilator-version")
        obj = directory / "dequant-obj"
        experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal",
                            "--top-module", "dequant_tb", "--Mdir", str(obj),
                            "-o", "dequant-sim", rtl,
                            "tests/dequant_tb.sv"], "dequant-compile", 1200)
        argv = [str(obj / "dequant-sim")]
    try:
        output = experiment.execute(argv + ["+vectors=" + str(vectors.relative_to(ROOT))],
                                    "dequant-simulation")
    except RuntimeError:
        command = experiment.receipt["commands"][-1]
        output = (ROOT / command["stdout"]).read_text() + (ROOT / command["stderr"]).read_text()
        if not expect_mismatch or command.get("timed_out") or "DEQUANT_MISMATCH" not in output:
            raise
        experiment.receipt["results"]["mutant"] = {
            "rejected_by": "normal exact-bit numerical scoreboard",
            "raw_diagnostic": output.strip(),
        }
        experiment.save()
        return
    if expect_mismatch:
        raise AssertionError("behavioral mutant survived normal numerical scoreboard")
    experiment.receipt["results"]["dequant"] = {
        "simulator": simulator, "vectors": count,
        "all_codes_at_distinct_scales": 16, "seeded_random_cases": 10000,
        "public_pin_scoreboard": True, "raw_summary": output.strip(),
    }
    experiment.save()


def run_public_smoke(experiment):
    directory = experiment.directory.relative_to(ROOT)
    obj = directory / "public-obj"
    sources = [str(p.relative_to(ROOT)) for pattern in (
        "rtl/*.sv", "anvil_d1_reference/rtl/*.sv") for p in sorted(ROOT.glob(pattern))]
    experiment.execute(["verilator", "--version"], "verilator-version")
    experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal",
                        "--top-module", "top_smoke_tb", "--Mdir", str(obj),
                        "-o", "public-sim", *sources, "tests/top_smoke_tb.sv"],
                       "public-compile", 1200)
    output = experiment.execute([str(obj / "public-sim")], "public-simulation", 1200)
    experiment.receipt["results"]["public-smoke"] = {
        "geometry": {"hidden": 8, "layers": 1, "banks": 2, "queue_depth": 3},
        "weight_fixture": "all-zero tensors; FP8 missing scales positive one",
        "oracle": "zero output projection gives zero logits and greedy token zero",
        "raw_summary": output.strip(),
        "scope": "bounded protocol smoke, not nonzero transformer numerical coverage",
    }
    experiment.save()


def run_numerical_leaf(experiment, leaf, simulator):
    directory = experiment.directory.relative_to(ROOT)
    vectors = experiment.directory / (leaf + "-vectors.txt")
    if leaf == "bf16":
        with vectors.open("w") as stream:
            for bits in range(65536):
                result, error = bf16_to_q16(bits)
                stream.write(f"{bits:04x} {result:08x} {error:x}\n")
        rtl = "rtl/anvil_d2_bf16_to_q16.sv"
        count = 65536
    else:
        rng = random.Random(233)
        lengths = [1, 2, 3, 4, 127, 128, 129, 255, 256]
        logical = [[0] * length for length in lengths]
        logical += [[-0x80000000, 0x7FFFFFFF, -1, 0, 1]]
        from reference import FP8_POSITIVES
        midpoints = [int((low + high) * 32768) for low, high in zip(
            FP8_POSITIVES, FP8_POSITIVES[1:])]
        logical += [[448 << 16, *midpoints], [-(448 << 16), *(-x for x in midpoints)]]
        logical += [[rng.randrange(-0x80000000, 0x80000000) for _ in range(length)]
                    for _ in range(12) for length in lengths]
        groups = [values[start:start+128] for values in logical
                  for start in range(0, len(values), 128)]
        count = sum(map(len, groups))
        with vectors.open("w") as stream:
            for group in groups:
                scale, codes = quantize_group(group)
                stream.write(f"{len(group)} {scale:08x}\n")
                for value, code in zip(group, codes):
                    stream.write(f"{value & 0xFFFFFFFF:08x} {code:02x}\n")
        rtl = "rtl/anvil_d2_fp8_group_quantizer.sv"
    top = leaf + "_tb"
    bench = "tests/" + top + ".sv"
    if simulator == "icarus":
        experiment.execute(["iverilog", "-V"], "iverilog-version")
        binary = directory / (leaf + ".vvp")
        experiment.execute(["iverilog", "-g2012", "-Wall", "-s", top, "-o",
                            str(binary), rtl, bench], leaf + "-compile")
        argv = ["vvp", str(binary)]
    else:
        experiment.execute(["verilator", "--version"], "verilator-version")
        obj = directory / (leaf + "-obj")
        experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal",
                            "--top-module", top, "--Mdir", str(obj),
                            "-o", leaf + "-sim", rtl, bench], leaf + "-compile", 1200)
        argv = [str(obj / (leaf + "-sim"))]
    output = experiment.execute(argv + ["+vectors=" + str(vectors.relative_to(ROOT))],
                                leaf + "-simulation")
    experiment.receipt["results"][leaf] = {
        "simulator": simulator, "vectors": count,
        "public_pin_scoreboard": True, "raw_summary": output.strip(),
    }
    experiment.save()


def run_synthesis_probe(experiment):
    directory = experiment.directory.relative_to(ROOT)
    sources = [str(p.relative_to(ROOT)) for pattern in (
        "rtl/*.sv", "anvil_d1_reference/rtl/*.sv") for p in sorted(ROOT.glob(pattern))]
    parameters = {
        "NUM_LAYERS": 1, "HIDDEN_SIZE": 8, "INTERMEDIATE_SIZE": 8,
        "NUM_Q_HEADS": 1, "KV_LORA_RANK": 2, "QK_NOPE_HEAD_DIM": 2,
        "QK_ROPE_HEAD_DIM": 2, "V_HEAD_DIM": 2, "ROUTED_EXPERTS": 2,
        "TOP_K": 1, "MOE_INTERMEDIATE_SIZE": 8, "FIRST_DENSE_LAYERS": 1,
        "VOCAB_SIZE": 4, "MAX_SEQ_LEN": 12, "BANKS": 2,
        "QUEUE_DEPTH": 3, "TILE_K": 8, "TILE_ROWS": 1,
    }
    script = experiment.directory / "integrated.ys"
    commands = [
        "read_verilog -sv " + " ".join(sources),
        "chparam " + " ".join(f"-set {key} {value}" for key, value in parameters.items()) +
        " anvil_d2_top",
        "hierarchy -check -top anvil_d2_top",
        "proc", "opt_expr", "opt_clean", "check -noinit -assert",
        "memory -nomap", "opt_clean", "check -noinit -assert", "stat",
        f"write_json {directory}/integrated.json",
    ]
    script.write_text("\n".join(commands) + "\n")
    experiment.execute(["yosys", "-V"], "yosys-version")
    experiment.execute(["yosys", "-s", str(script.relative_to(ROOT))],
                       "integrated-synthesis", 1800)
    netlist = json.loads((experiment.directory / "integrated.json").read_text())
    cell_counts = {}
    memory_bits = 0
    for module in netlist["modules"].values():
        if int(module.get("attributes", {}).get("blackbox", "0"), 2):
            raise AssertionError("black-box module in synthesized hierarchy")
        for cell in module.get("cells", {}).values():
            kind = cell["type"]
            cell_counts[kind] = cell_counts.get(kind, 0) + 1
            if "latch" in kind.lower() or kind in ("$div", "$mod", "$divfloor", "$modfloor"):
                raise AssertionError(f"forbidden synthesis cell {kind}")
            if kind.startswith("$mem"):
                params = cell["parameters"]
                memory_bits += int(params.get("WIDTH", "0"), 2) * int(
                    params.get("SIZE", "0"), 2)
    sequential = sum(value for kind, value in cell_counts.items() if "dff" in kind.lower())
    assert sequential > 100, f"insubstantial sequential state: {sequential}"
    assert memory_bits > 0, "no inferred memory state"
    top = netlist["modules"]["anvil_d2_top"]
    for instance in ("mtp", "fp8"):
        assert instance in top["cells"], f"missing integrated {instance}"
        assert any(isinstance(bit, int) for connections in top["cells"][instance][
            "connections"].values() for bit in connections), f"constant {instance}"
    experiment.receipt["results"]["synthesis-probe"] = {
        "parameters": parameters, "sequential_cell_definitions": sequential,
        "memory_definition_bits": memory_bits,
        "cell_definition_counts": cell_counts,
        "scope": "compact integrated synthesis; not physical timing/PPA or full geometry matrix",
    }
    experiment.save()


def run_dequant_mutant(experiment, defect):
    source_path = ROOT / "rtl/anvil_d2_fp8_dequant.sv"
    original = source_path.read_text()
    before, after = {
        "fp8-bias": ("})-11'sd10", "})-11'sd9"),
        "bf16-tie": ("bits[15] && ((|bits[14:0]) || bits[16])", "bits[15]"),
    }[defect]
    if original.count(before) != 1:
        raise AssertionError(f"mutation anchor for {defect} must occur exactly once")
    mutated = original.replace(before, after)
    copied = experiment.directory / "anvil_d2_fp8_dequant.sv"
    copied.write_text(mutated)
    (experiment.directory / "mutant.diff").write_text("".join(difflib.unified_diff(
        original.splitlines(True), mutated.splitlines(True),
        fromfile="rtl/anvil_d2_fp8_dequant.sv",
        tofile="disposable/anvil_d2_fp8_dequant.sv")))
    experiment.receipt["mutation"] = {
        "defect": defect, "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "mutated_sha256": hashlib.sha256(mutated.encode()).hexdigest(),
        "diff": str((experiment.directory / "mutant.diff").relative_to(ROOT)),
    }
    experiment.save()
    run_dequant(experiment, "verilator", str(copied.relative_to(ROOT)), expect_mismatch=True)


def run_service_probe(experiment, rtl="rtl/anvil_d2_fp8_mla_moe.sv",
                      expect_mismatch=False):
    rng = random.Random(89)
    directory = experiment.directory.relative_to(ROOT)
    vectors = experiment.directory / "service-vectors.txt"
    fixtures = []
    for row, length in enumerate([1, 2, 3, 4, 127, 128, 129, 255, 256] * 5):
        values = [rng.randrange(-0x80000000, 0x80000000) for _ in range(length)]
        for base in range(0, length, 128):
            part = values[base:base+128]
            scale, codes = quantize_group(part)
            fixtures.append((0, 1, row % 3, row, base, part, scale, codes))
    for sequence in range(24):
        count = 128 if sequence < 6 else [1, 2, 3, 4, 127, 128][sequence % 6]
        # Revisit the same expert key with changed scales and payload after flush.
        scale = [0x3EAAAAAB, 0x3F800001, 0x3F818000][sequence % 3]
        codes = [rng.randrange(127) | (rng.randrange(2) << 7) for _ in range(count)]
        fixtures.append((1, 1, 2, (sequence // 3) % 2, 0, [0] * count, scale, codes))
    with vectors.open("w") as stream:
        for operation, epoch, layer, row, base, values, scale, codes in fixtures:
            stream.write(f"{operation} {epoch} {layer} {row} {base} {len(values)} 0 {scale:08x}\n")
            for value, code in zip(values, codes):
                fp32, bf16, error = dequantize(code, scale)
                q16, qerror = bf16_to_q16(bf16)
                assert not error and not qerror
                stream.write(f"{value & 0xFFFFFFFF:08x} {code:02x} {fp32:08x} "
                             f"{bf16:04x} {q16:08x}\n")
    obj = directory / "service-obj"
    experiment.execute(["verilator", "--version"], "verilator-version")
    experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal",
                        "--top-module", "fp8_service_tb", "--Mdir", str(obj),
                        "-o", "service-sim", "rtl/anvil_d2_fp8_dequant.sv",
                        "rtl/anvil_d2_fp8_group_quantizer.sv",
                        "rtl/anvil_d2_bf16_to_q16.sv", rtl,
                        "tests/fp8_service_tb.sv"], "service-compile", 1200)
    try:
        output = experiment.execute([str(obj / "service-sim"),
                                     "+vectors=" + str(vectors.relative_to(ROOT))],
                                    "service-simulation")
    except RuntimeError:
        command = experiment.receipt["commands"][-1]
        output = (ROOT / command["stdout"]).read_text() + (ROOT / command["stderr"]).read_text()
        diagnostics = ("SERVICE_NUMERICAL_MISMATCH", "CACHE_PACKING_MISMATCH",
                       "CACHE_SCALE_WRITE_MISMATCH", "GROUP_READ_OR_FLUSH_INVALIDATION_ACCOUNTING")
        if not expect_mismatch or command.get("timed_out") or not any(
                diagnostic in output for diagnostic in diagnostics):
            raise
        experiment.receipt["results"]["mutant"] = {
            "rejected_by": "normal numerical/transfer scoreboard",
            "raw_diagnostic": output.strip(),
        }
        experiment.save()
        return
    if expect_mismatch:
        raise AssertionError("behavioral service mutant survived normal scoreboard")
    experiment.receipt["results"]["service"] = {
        "fixtures": len(fixtures), "seed": 89, "raw_summary": output.strip(),
        "scope": "cache packing/roundtrip and expert dequantized Q16 boundary; not MAC/logit coverage",
    }
    experiment.save()


def run_service_mutant(experiment, defect):
    source_path = ROOT / "rtl/anvil_d2_fp8_mla_moe.sv"
    original = source_path.read_text()
    before, after = {
        "byte-order": ("selected_byte=payload_q >> {element_index[1:0],3'b000}",
                       "selected_byte=payload_q >> {~element_index[1:0],3'b000}"),
        "scale-group": ("base_col>>7", "base_col>>6"),
        "scale-invalidation": ("resident_valid<=0; epoch_valid<=0;", "epoch_valid<=0;"),
    }[defect]
    if original.count(before) != 1:
        raise AssertionError(f"mutation anchor for {defect} must occur exactly once")
    mutated = original.replace(before, after)
    copied = experiment.directory / "anvil_d2_fp8_mla_moe.sv"
    copied.write_text(mutated)
    (experiment.directory / "mutant.diff").write_text("".join(difflib.unified_diff(
        original.splitlines(True), mutated.splitlines(True),
        fromfile="rtl/anvil_d2_fp8_mla_moe.sv",
        tofile="disposable/anvil_d2_fp8_mla_moe.sv")))
    experiment.receipt["mutation"] = {
        "defect": defect, "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "mutated_sha256": hashlib.sha256(mutated.encode()).hexdigest(),
        "diff": str((experiment.directory / "mutant.diff").relative_to(ROOT)),
    }
    experiment.save()
    run_service_probe(experiment, str(copied.relative_to(ROOT)), expect_mismatch=True)


def run_verdict_probe(experiment, simulator):
    directory = experiment.directory.relative_to(ROOT)
    vectors = experiment.directory / "verdict-vectors.txt"
    cases = 0
    with vectors.open("w") as stream:
        for proposed in range(5):
            for prefix in range(proposed+1):
                drafts = [1, 2, 3, 4]
                targets = drafts.copy()
                if prefix < proposed:
                    targets[prefix] += 10
                for limit in range(1, 6):
                    for first in (1, 9, 11):
                        untruncated, _, _ = committed_block(
                            0, drafts, targets, proposed, limit, first, 12, 99)
                        for eos_index in range(-1, len(untruncated)):
                            eos = 99 if eos_index < 0 else untruncated[eos_index]
                            expected, accepted, rejected = committed_block(
                                0, drafts, targets, proposed, limit, first, 12, eos)
                            packed_drafts = sum(token << (32*i) for i, token in enumerate(drafts))
                            packed_targets = sum(token << (32*i) for i, token in enumerate(targets))
                            packed_expected = sum(token << (32*i) for i, token in enumerate(expected))
                            stream.write(f"0 {packed_drafts:032x} {packed_targets:032x} "
                                         f"{proposed} {limit} {first} {eos:x} "
                                         f"{len(expected)} {accepted} {int(rejected)} "
                                         f"{packed_expected:040x} {prefix} {eos_index}\n")
                            cases += 1
    if simulator == "icarus":
        experiment.execute(["iverilog", "-V"], "iverilog-version")
        binary = directory / "verdict.vvp"
        experiment.execute(["iverilog", "-g2012", "-Wall", "-s", "verdict_tb", "-o",
                            str(binary), "rtl/anvil_d2_mtp_verdict.sv", "tests/verdict_tb.sv"],
                           "verdict-compile")
        argv = ["vvp", str(binary)]
    else:
        experiment.execute(["verilator", "--version"], "verilator-version")
        obj = directory / "verdict-obj"
        experiment.execute(["verilator", "--binary", "--timing", "-Wno-fatal",
                            "--top-module", "verdict_tb", "--Mdir", str(obj),
                            "-o", "verdict-sim", "rtl/anvil_d2_mtp_verdict.sv",
                            "tests/verdict_tb.sv"], "verdict-compile", 1200)
        argv = [str(obj / "verdict-sim")]
    output = experiment.execute(argv + ["+vectors=" + str(vectors.relative_to(ROOT))],
                                "verdict-simulation")
    experiment.receipt["results"]["verdict"] = {
        "cases": cases, "simulator": simulator, "raw_summary": output.strip(),
        "scope": "public-pin block publication unit; not native MTP-head prefix coverage",
    }
    experiment.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", choices=["dequant", "quantizer", "bf16", "public-smoke",
                                         "synthesis-probe", "fp8-bias", "bf16-tie",
                                         "fp8-service", "byte-order", "scale-group",
                                         "scale-invalidation", "verdict"],
                        required=True)
    parser.add_argument("--simulator", choices=["icarus", "verilator"], default="icarus")
    parser.add_argument("--repair-of", help="Project-relative retained failed receipt")
    args = parser.parse_args()
    experiment = Experiment("d2-" + args.probe, preparation=True)
    if args.repair_of:
        prior = Path(args.repair_of)
        if prior.is_absolute() or ".." in prior.parts or not (ROOT / prior).is_file():
            raise ValueError("--repair-of must name an existing project-relative receipt")
        experiment.receipt["repair_of"] = str(prior)
        experiment.save()
    try:
        experiment.execute(["python3", "--version"], "python-version")
        if args.probe == "dequant":
            run_dequant(experiment, args.simulator)
        elif args.probe == "public-smoke":
            run_public_smoke(experiment)
        elif args.probe == "synthesis-probe":
            run_synthesis_probe(experiment)
        elif args.probe in ("fp8-bias", "bf16-tie"):
            run_dequant_mutant(experiment, args.probe)
        elif args.probe == "fp8-service":
            run_service_probe(experiment)
        elif args.probe in ("byte-order", "scale-group", "scale-invalidation"):
            run_service_mutant(experiment, args.probe)
        elif args.probe == "verdict":
            run_verdict_probe(experiment, args.simulator)
        else:
            run_numerical_leaf(experiment, args.probe, args.simulator)
    except Exception as error:
        experiment.finish(False, str(error))
        raise
    finally:
        experiment.cleanup_intermediates()
    experiment.finish(True)


if __name__ == "__main__":
    main()
