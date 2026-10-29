"""Supplemental compact DeepSeek-policy production-shell experiments.

The vocabulary, merges and weights are synthetic, explicitly not official
complete-table or pretrained-model results. The actual DeepSeek Split compiler
and independently evaluated rules are exercised on a bounded letter alphabet.
"""

import hashlib
import json
from pathlib import Path
import re
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deepseek_dfa import compile_profile
from deepseek_preprocessing import Preprocessor, require
from official import ROOT, TOKENIZERS_VERSION
from protocol import bpe_reference
from qwen_integration import save
from qwen_regex import serialize
from qwen_shell import build_shell_inputs, shell_case
from qwen_tables import encode_fragments, inverse_byte_alphabet, table
from storage import words


def compact_inputs(directory, model_bos):
    import tokenizers

    require(tokenizers.__version__ == TOKENIZERS_VERSION,
            "Compact shell requires the already installed pinned tokenizer backend")
    directory = ROOT / directory
    source_path = ROOT / "tests/data/deepseek-tokenizer.json"
    source = json.loads(source_path.read_bytes())
    config_path = ROOT / "tests/data/deepseek-tokenizer_config.json"
    config = json.loads(config_path.read_bytes())
    require(source["normalizer"] == {"type": "Sequence", "normalizers": []} and
            config["add_bos_token"] is True and config["add_eos_token"] is False,
            "Pinned DeepSeek identity/prefix policy changed")
    bos, eos = config["bos_token"]["content"], config["eos_token"]["content"]
    pieces = [bytes([byte]) for byte in range(256)] + [
        b"AB", b"BC", b"ABC", bos.encode(), eos.encode(),
    ]
    flags = [1] * 259 + [2, 2]
    # BC wins before AB; a greedy ABC trie would produce the wrong prompt.
    merges = [(65, 66, 256, 2), (66, 67, 257, 0), (256, 67, 258, 1)]
    added = [{"id": token, "content": content, "special": True,
              "single_word": False, "lstrip": False, "rstrip": False,
              "normalized": False} for token, content in ((259, bos), (260, eos))]
    payloads = encode_fragments(pieces, flags, list(range(256)), merges, added)
    # Every fixture prompt contains only A..D: all have this exact DeepSeek
    # classification. Other scalars are outside this compact diagnostic's scope.
    profile = compile_profile([(1, False, False, True, False, False, False)])
    payloads.update(serialize(profile))
    payloads[0x207] = table(16, words(0, 0xD7FF, 0, 0) +
                           words(0xE000, 0x10FFFF, 0, 0))
    payloads.update({kind: table(width, b"")
                     for kind, width in ((0x20D, 16), (0x20E, 4), (0x20F, 16))})
    identity = hashlib.sha256(b"DeepSeek compact letter-policy shell fixture v1").digest()
    metadata = [2, 2, len(pieces), 0, 1, int(model_bos), 259 if model_bos else 0, 260, 0x100000,
                profile["classes"], profile["start"], profile["dead"], 32, 0,
                max(map(len, pieces)), 4096,
                *struct.unpack("<8I", identity), 0x100000, 0x100000, *([0] * 6)]
    require(len(metadata) == 32, "Compact DeepSeek metadata extent")
    payloads[0x200] = words(*metadata)

    alphabet = {byte: char for char, byte in inverse_byte_alphabet().items()}
    vocabulary = {"".join(alphabet[byte] for byte in piece): index
                  for index, piece in enumerate(pieces[:259])}
    vocabulary.update({bos: 259, eos: 260})
    backend_source = {
        **source,
        "model": {**source["model"], "vocab": vocabulary,
                  "merges": [[alphabet[66], alphabet[67]],
                             [alphabet[65] + alphabet[66], alphabet[67]],
                             [alphabet[65], alphabet[66]]]},
        "added_tokens": added,
    }
    official = tokenizers.Tokenizer.from_str(json.dumps(backend_source))
    if model_bos:
        official.post_processor = tokenizers.processors.Sequence([
            official.post_processor,
            tokenizers.processors.TemplateProcessing(
                single=f"{bos}:0 $A:0", special_tokens=[(bos, 259)]),
        ])
    preprocessor = Preprocessor()
    vectors = []
    merge_map = {(left, right): (result, rank) for left, right, result, rank in merges}
    for text in ("ABC", "ABCD"):
        expected = [259] if model_bos else []
        for part in preprocessor.split(text):
            expected.extend(bpe_reference(list(part.encode()), merge_map))
        observed = official.encode(text, add_special_tokens=model_bos).ids
        require(expected == observed and expected == ([259] if model_bos else []) +
                [65, 257] + ([68] if text.endswith("D") else []),
                "Compact independent DeepSeek token vector mismatch")
        decoded = b"".join(pieces[token] for token in expected)
        require(official.decode(observed, skip_special_tokens=False).encode() == decoded,
                "Compact independent DeepSeek decode mismatch")
        vectors.append({"input_utf8_hex": text.encode().hex(), "token_ids": expected})
    provenance = {
        "scope": "Synthetic 261-token vocabulary with restricted letter classification; "
                 "not official complete tables or pretrained inference",
        "policy": "automatic-BOS" if model_bos else "raw-text",
        "bos_id": 259, "eos_id": 260,
        "special_id_limit": "Synthetic IDs intentionally differ from official DeepSeek IDs",
        "source_tokenizer_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "source_config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "synthetic_backend_sha256": hashlib.sha256(
            json.dumps(backend_source, sort_keys=True).encode()).hexdigest(),
        "unicode_source_sha256": preprocessor.unicode_hashes,
        "payload_sha256": {f"{kind:x}": hashlib.sha256(blob).hexdigest()
                           for kind, blob in payloads.items()},
        "compared_prompt_vectors": len(vectors),
        "normalization": "identity", "chat_template": False,
        "reload": "Same image revalidated atomically between distinct prompts",
    }
    save(directory / "compact-policy.json", provenance)
    build_shell_inputs(
        directory, len(pieces), 263, vectors, payloads,
        scope="Compact synthetic DeepSeek " + provenance["policy"] + " policy; ",
        tokenizer_identity=identity.hex(),
        prompt_oracle="Independent DeepSeek Split + ranked byte merges, cross-checked "
                      "with pinned tokenizers backend and actual DeepSeek preprocessing",
        piece_byte_offset=0, provenance=provenance,
    )


def measure(evidence, info, rows, prefix):
    results = []
    for row in rows:
        child = row["simulation_receipt"]
        log = (ROOT / child["stdout"]).read_text()
        frames = []
        for line in log.splitlines():
            if line.startswith(prefix + "_FRAME "):
                frames.append({key: int(value) for key, value in
                               re.findall(r"(\w+)=(\d+)", line)})
        require(len(frames) == len(info["cases"]) == 2,
                "Both shell frames must have actual completion measurements")
        previous = 0
        for frame, expected in zip(frames, info["cases"]):
            require(frame["frame"] == expected["case"] and
                    frame["operations"] == len(expected["core_operation_ids"]) and
                    frame["embedding_reads"] ==
                    frame["operations"] * (8 * info["physical_capacity"] + 8) and
                    frame["activation_writes"] == expected["activation_write_count"] and
                    frame["output_bytes"] == len(bytes.fromhex(expected["output_utf8_hex"])) and
                    frame["cycles"] > previous,
                    "Actual shell counts differ from independently generated obligations")
            previous = frame["cycles"]
        boots = [{key: int(value) for key, value in re.findall(r"(\w+)=(\d+)", line)}
                 for line in log.splitlines() if line.startswith(prefix + "_BOOT ")]
        counts = [line for line in log.splitlines() if line.startswith(prefix + "_COUNTS ")]
        require(len(boots) == 2 and len(counts) == 1 and "reloads=1 " in counts[0],
                "Autonomous initial boot and idle reload were not both measured")
        results.append({
            "name": row["name"], "simulation_seconds": child["duration_s"],
            "compile_seconds": row["compile_receipt"]["duration_s"],
            "compile_cache_hit": row["compile_cache_hit"],
            "frames": frames, "boots": boots,
            "last_reported_cycle": frames[-1]["cycles"],
            "cycles_per_second": frames[-1]["cycles"] / child["duration_s"],
            "actual_comparisons": row["actual_comparisons"],
            "raw_stdout": child["stdout"], "simulation": child,
        })
    return results


def run_deepseek_shell_compact(evidence):
    evidence.tools(("python3", "verilator", "g++", "make"))
    evidence.record["deepseek_shell_scope"] = (
        "Supplemental compact synthetic fixtures only. No official complete-table "
        "shell run, pretrained benchmark, STA, HIL or clean-reproduction claim.")
    measurements, controls = [], []
    for model_bos in (False, True):
        policy = "bos" if model_bos else "raw"
        family = "deepseek-" + policy
        directory = evidence.path / ("fixture-" + policy)
        directory.mkdir()
        evidence.child(
            ["./.venv/bin/python", "tests/deepseek_shell.py",
             evidence.relative(directory), policy],
            family + "-compact-inputs")
        info = json.loads((directory / "shell-reference.json").read_bytes())
        before = len(evidence.record["coverage"])
        evidence.run_cases([
            (f"{family}-b{bypass}-s{seed}",
             lambda scope, seed=seed, bypass=bypass:
             shell_case(scope, info, seed, bypass, False, family=family))
            for seed in (1, 17, 89) for bypass in (0, 1)
        ], workers=1)
        rows = evidence.record["coverage"][before:]
        require(len(rows) == 6 and all(row["status"] == "passed" for row in rows),
                "Every compact DeepSeek transport/seed must pass")
        prefix = family.upper().replace("-", "_") + "_SHELL"
        measurements.extend(measure(evidence, info, rows, prefix))
        baseline = next(row for row in rows if row["name"] == f"{family}-shell-b1-s17")
        for mode, name, suffix in (
            (1, "wrong-value", "NUMERICAL_WRITE"),
            (2, "duplicate", "UNEXPECTED_WRITE"),
            (3, "missing", "DRAIN"),
        ):
            child = evidence.child(
                [*baseline["simulation_receipt"]["argv"], f"+scoreboard_fault={mode}"],
                family + "-scoreboard-" + name, allow_failure=True)
            output = (ROOT / child["stdout"]).read_text() + (ROOT / child["stderr"]).read_text()
            assertion = prefix + "_" + suffix
            require(child["exit_code"] not in (0, None) and not child["timed_out"] and
                    child["child_settled"] and child["process_group_settled"] and
                    f"SCOREBOARD_INJECT {name}" in output and assertion in output and
                    "%Error:" in output,
                    f"Compact DeepSeek monitor did not reject {policy}/{name}")
            controls.append({"policy": policy, "fault": name, "assertion": assertion,
                             "simulation": child,
                             "scope": "Compiled scoreboard control, not an RTL mutation kill"})
        # Preserve incremental completed-policy results even if a later policy fails.
        save(evidence.path / f"compact-{policy}-measurements.json", measurements[-6:])
        evidence.record["deepseek_shell_measurements"] = measurements
        evidence.record["deepseek_shell_controls"] = controls
    evidence.record["complete_table_feasibility"] = {
        "status": "Independent review required before complete-table execution",
        "budget_seconds": 2700,
        "measured_scope": "261 active, 263 physical rows; H8/L1; two prompts, eight "
                          "generated tokens each; initial boot plus same-image idle reload",
        "limitation": "Compact throughput is not complete-table feasibility proof. "
                      "Official table validation, full head traversal and table-search "
                      "costs must be included; no long run authorized by these measurements.",
    }


def run_deepseek_shell_feasibility(evidence, receipts):
    """Analyze retained production-shell runs; execute no complete-table retry."""
    require(len(receipts) == 3,
            "Supply compact DeepSeek, two-capacity shell and official DeepSeek boot receipts")
    records, bindings = [], []
    for name in receipts:
        path = Path(name)
        require(not path.is_absolute() and ".." not in path.parts and
                path.parts[:2] == ("evidence", "preparation") and path.name == "receipt.json",
                "Feasibility inputs must be project-relative preparation receipts")
        raw = (ROOT / path).read_bytes()
        record = json.loads(raw)
        require(record["exit_code"] == 0 and record["child_settled"] and
                record["sources_unchanged"], "Feasibility requires completed source-bound inputs")
        bindings.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest()})
        records.append(record)
    compact, head, boot = records
    measures = compact["deepseek_shell_measurements"]
    require(len(measures) == 12 and len(compact["deepseek_shell_controls"]) == 6,
            "Both policies, transports, three seeds and six monitor controls are required")
    head_points = sorted(head["head_row_shell_measurements"], key=lambda row: row["capacity"])
    require([row["capacity"] for row in head_points] == [257, 1025],
            "Two measured physical capacities are required")
    # Bind compiled production sources, not historical before-optimization RTL.
    for record, predicate in (
        (compact, lambda row: row["status"] == "passed"),
        (head, lambda row: "-after-" in row["name"]),
        (boot, lambda row: row["status"] == "passed"),
    ):
        rows = [row for row in record["coverage"] if predicate(row)]
        require(bool(rows), "No applicable source-bound simulations in feasibility input")
        for row in rows:
            for name, expected in row["source_sha256"]:
                require(name.startswith("rtl/") and
                        hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected,
                        f"Production source changed since feasibility measurement: {name}")
    operations = [point["after"]["operations"] for point in head_points]
    require(len(operations[0]) == len(operations[1]) == 9 and
            [(row["position"], row["token"]) for row in operations[0]] ==
            [(row["position"], row["token"]) for row in operations[1]],
            "Capacity slope must compare identical operations")
    slope = ((head_points[1]["after"]["inference_cycles"] -
              head_points[0]["after"]["inference_cycles"]) / (768 * 9))
    require(slope > 0, "Invalid measured physical-row slope")
    speeds = [row["cycles_per_second"] for row in measures]
    boot_rows = [row for row in boot["coverage"] if row["status"] == "passed"]
    require(len(boot_rows) == 1, "Expected one official full-table boot measurement")
    boot_seconds = boot_rows[0]["simulation_receipt"]["duration_s"]
    boot_directory = ROOT / Path(receipts[2]).parent
    scope_bytes = (boot_directory / "official-boot-scope.json").read_bytes()
    scope = json.loads(scope_bytes)
    vector_bytes = (boot_directory / "official-vectors.json").read_bytes()
    vectors = json.loads(vector_bytes)["vectors"][:5]
    required = json.loads((ROOT / "tests/data/requirements.json").read_bytes())["prompts"]
    require([row["text"] for row in vectors] == required and
            scope["active_vocabulary"] == 128815 and scope["physical_capacity"] == 131072,
            "Complete-table projection must retain all exact benchmark prompts and capacity")
    estimates = []
    for model_bos in (False, True):
        counts = [len(row["token_ids"]) + int(model_bos) + 7 for row in vectors]
        for label, count, boots in (
            ("one-general-prompt", counts[0], 1),
            ("all-five-prompts-with-idle-reload", sum(counts), 2),
        ):
            head_cycles = slope * scope["physical_capacity"] * count
            estimates.append({
                "policy": "automatic-BOS" if model_bos else "raw-text",
                "selection": label, "core_operations": count, "boot_epochs": boots,
                "head_cycle_linear_extrapolation": head_cycles,
                "head_seconds_at_fastest_compact_rate": head_cycles / max(speeds),
                "head_seconds_at_slowest_compact_rate": head_cycles / min(speeds),
                "plus_observed_boot_seconds_fast": head_cycles / max(speeds) +
                                                  boots * boot_seconds,
                "plus_observed_boot_seconds_slow": head_cycles / min(speeds) +
                                                  boots * boot_seconds,
            })
    missing = [{"path": row["path"], "sha256_at_repair_launch": row["sha256"],
                "currently_accessible": (ROOT / row["path"]).is_file()}
               for row in compact["repair_of"]]
    result = {
        "scope": "Advisory measured sizing, not a complete-table execution or timing guarantee",
        "budget_seconds": 2700, "receipt_bindings": bindings,
        "supplemental_inputs": {
            "official_boot_scope_sha256": hashlib.sha256(scope_bytes).hexdigest(),
            "official_vectors_sha256": hashlib.sha256(vector_bytes).hexdigest(),
        },
        "compact_elapsed_seconds": compact["duration_s"],
        "compact_passed_comparisons": compact["simulation_accounting"]["passed_comparisons"],
        "compact_frames": sum(len(row["frames"]) for row in measures),
        "compact_operations": sum(frame["operations"] for row in measures for frame in row["frames"]),
        "compact_output_bytes": sum(frame["output_bytes"] for row in measures for frame in row["frames"]),
        "compact_activation_writes": sum(frame["activation_writes"] for row in measures
                                         for frame in row["frames"]),
        "compact_final_cycle_range": [min(row["last_reported_cycle"] for row in measures),
                                      max(row["last_reported_cycle"] for row in measures)],
        "compact_cycle_rate_range": [min(speeds), max(speeds)],
        "physical_row_cycles_per_operation_fit": slope,
        "fit_capacity_points": [{"capacity": row["capacity"],
                                 "inference_cycles": row["after"]["inference_cycles"]}
                                for row in head_points],
        "observed_official_boot_seconds": boot_seconds,
        "observed_official_boot_image_bytes": scope["image_bytes"],
        "generation_assumption": "Eight non-EOS selections per prompt, as in the compact "
                                 "fixture. Complete-table synthetic outputs have not been "
                                 "calculated or executed here. Earlier EOS would reduce "
                                 "operation counts and cannot be excluded by this sizing.",
        "estimates": estimates,
        "excluded_costs": ["official prompt tokenization and ranked merge/table searches",
                           "non-head Transformer work and growing attention positions",
                           "compilation, official input conversion and independent references",
                           "DDR/flash extent and longer-sequence changes",
                           "large working-set cache and simulator-rate changes",
                           "remaining transports/seeds and functional controls"],
        "interpretation": "The linear fit extrapolates far beyond measured capacities and "
                          "uses whole-run compact clock throughput; it is not a proven "
                          "lower/upper bound. One general-prompt candidate and the unchanged "
                          "five-prompt matrix require separate independent feasibility review. "
                          "Do not schedule a complete-table retry from this analysis alone.",
        "prior_failure_access": missing,
        "failure_preservation_limit": "The original compact raw fixture was rejected with "
                                     "boot code06: a disabled BOS field incorrectly retained "
                                     "a nonzero ID. The repair only zeros that disabled field. "
                                     "A missing predecessor is not reconstructed or treated "
                                     "as passing; its recorded launch hash is only a link.",
    }
    save(evidence.path / "measured-feasibility.json", result)
    evidence.record["deepseek_shell_feasibility"] = result


if __name__ == "__main__":
    require(len(sys.argv) == 3 and sys.argv[2] in ("raw", "bos"),
            "Usage: ./.venv/bin/python tests/deepseek_shell.py FRESH_DIRECTORY raw|bos")
    directory = Path(sys.argv[1])
    require(not directory.is_absolute() and ".." not in directory.parts and
            directory.parts[:2] in (("evidence", "preparation"), ("evidence", "verification"))
            and directory.is_dir(), "A fresh project-relative evidence directory is required")
    compact_inputs(directory, model_bos=sys.argv[2] == "bos")
