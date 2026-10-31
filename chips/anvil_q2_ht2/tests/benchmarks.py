"""Deterministic benchmark inputs and independent raw-observation accounting.

This module does not operate a board, project bandwidth, or substitute synthetic
model fixtures for production observations.
"""

from collections import Counter, defaultdict
from decimal import Decimal, localcontext
import hashlib
import itertools
import json
from pathlib import Path, PurePosixPath
import re
import uuid

from reference import FP32, decimal_value

DOMAINS = ("dialogue", "mathematics", "code", "knowledge", "logic")
MODES = ("bf16-dense", "bf16-sparse", "fp16-dense", "fp16-sparse",
         "w4-dense", "w4-sparse", "w2-dense", "w2-sparse")
WIDTHS = (1, 2, 4)
KV_FORMATS = ("bf16", "int8")
BASELINES = ("anvil-q2-ht", "anvil-q2-fp")
BOUNDARY = "prefill:first-input-to-first-token;decode:first-draft-to-final-commit"
SHA256 = re.compile(r"[0-9a-f]{64}")
FORBIDDEN = {".vulcan", ".git", ".tooling", "VULCAN", "__pycache__"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, name, minimum=0, maximum=None):
    require(type(value) is int and value >= minimum and
            (maximum is None or value <= maximum), f"invalid {name}: {value!r}")
    return value


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def portable_path(root, relative):
    require(isinstance(relative, str) and relative and "\\" not in relative,
            "asset path must be a nonempty POSIX project-relative path")
    path = PurePosixPath(relative)
    require(not path.is_absolute() and ".." not in path.parts and
            not FORBIDDEN.intersection(path.parts) and
            ":" not in relative, f"forbidden asset path: {relative}")
    result = root / path
    require(result.resolve().is_relative_to(root.resolve()),
            f"asset escapes project: {relative}")
    # Resolve each component as well: an alias into runtime metadata is not an asset.
    resolved = result.resolve().relative_to(root.resolve())
    require(not FORBIDDEN.intersection(resolved.parts),
            f"asset resolves into runtime metadata: {relative}")
    return result


def validate_asset(root, binding):
    require(isinstance(binding, dict), "asset binding must be an object")
    path = portable_path(root, binding.get("path"))
    expected = binding.get("sha256")
    errors = []
    if not isinstance(expected, str) or not SHA256.fullmatch(expected):
        errors.append(f"{binding['path']}: missing immutable SHA-256")
    if not path.is_file():
        errors.append(f"{binding['path']}: missing file")
    if errors:
        raise ValueError("; ".join(errors))
    require(digest(path) == expected, f"{binding['path']}: SHA-256 mismatch")
    return path


def corpus(root, manifest):
    path = validate_asset(root, manifest["corpus"])
    data = json.loads(path.read_text())
    require(data["schema"] == 1 and set(data["domains"]) == set(DOMAINS),
            "corpus must contain exactly the five frozen domains")
    prompts = {}
    seen = set()
    for domain in DOMAINS:
        texts = data["domains"][domain]
        require(len(texts) >= 20, f"{domain}: fewer than twenty prompts")
        for number, text in enumerate(texts):
            require(isinstance(text, str) and text.strip() and text not in seen,
                    f"{domain}: empty or duplicate prompt")
            seen.add(text)
            prompts[f"{domain}-{number:02d}"] = {"domain": domain, "text": text}
    return prompts


def cells():
    return [{"engine": "ht2", "k": k, "mode": mode, "kv": kv}
            for k, mode, kv in itertools.product(WIDTHS, MODES, KV_FORMATS)] + [
                {"engine": name, "k": 1, "mode": "baseline", "kv": "baseline"}
                for name in BASELINES]


def cell_key(cell):
    return (cell["engine"], cell["k"], cell["mode"], cell["kv"])


def draft(prompt_id, prefix, current, k, vocabulary):
    """Proposals see committed IDs only, never logits or future target answers."""
    integer(k, "draft width", 1, 4)
    require(k in WIDTHS, "unsupported draft width")
    integer(vocabulary, "vocabulary", 1, 151936)
    integer(current, "current token", 0, vocabulary - 1)
    for token in prefix:
        integer(token, "prefix token", 0, vocabulary - 1)
    seed = json.dumps(["sha256-prefix-v1", prompt_id, prefix],
                      separators=(",", ":"), ensure_ascii=True).encode("ascii")
    ids = [current]
    parents = [0]
    for slot in range(1, k):
        value = hashlib.sha256(seed + bytes([slot])).digest()
        ids.append(int.from_bytes(value[:8], "little") % vocabulary)
        parents.append(slot - 1 if value[8] & 1 else 0)
    return ids, parents


def fp_vector(values):
    require(isinstance(values, list) and values, "empty numerical vector")
    result = []
    for bits in values:
        integer(bits, "FP32 bits", 0, 0xffffffff)
        require(bits & 0x7f800000 != 0x7f800000, "nonfinite numerical observation")
        result.append(decimal_value(bits, FP32))
    return result


def fidelity(actual, expected):
    """NRMSE is ||a-r||2/||r||2; cosine is checked without host float rounding."""
    require(len(actual) == len(expected), "numerical vector length mismatch")
    with localcontext() as context:
        context.prec = 80
        a, r = fp_vector(actual), fp_vector(expected)
        error = sum((x-y)**2 for x, y in zip(a, r))
        aa, rr = sum(x*x for x in a), sum(x*x for x in r)
        ar = sum(x*y for x, y in zip(a, r))
        nrmse = (error/rr).sqrt() if rr else (Decimal(0) if not error else Decimal("Infinity"))
        cosine = ar/(aa*rr).sqrt() if aa and rr else (
            Decimal(1) if not error else Decimal(0))
        return nrmse, cosine


def greedy(bits):
    values = fp_vector(bits)
    return max(range(len(values)), key=lambda index: (values[index], -index))


def selected_path(ids, parents, targets):
    require(len(ids) in WIDTHS and len(ids) == len(parents) == len(targets),
            "invalid tree lengths")
    require(parents[0] == 0 and
            all(type(p) is int and 0 <= p < i for i, p in enumerate(parents[1:], 1)),
            "invalid tree parents")
    path = [0]
    while True:
        children = [i for i in range(path[-1]+1, len(ids))
                    if parents[i] == path[-1] and ids[i] == targets[path[-1]]]
        if not children:
            return path, targets[path[-1]]
        path.append(children[0])


class PromptAccount:
    """Stream one prompt; retain counts/metrics, never per-layer tensor dumps."""

    def __init__(self, begin, vocabulary, eos_ids, hidden_size=1536):
        self.begin = begin
        self.cell = begin["cell"]
        require(self.cell in cells(), "unknown measurement cell")
        require(begin["boundary"] == BOUNDARY, "measurement boundary mismatch")
        self.clock = integer(begin["measured_clock_hz"], "measured clock", 1)
        self.vocabulary, self.eos_ids, self.hidden_size = vocabulary, eos_ids, hidden_size
        self.expected = begin["greedy_ids"]
        require(isinstance(self.expected, list) and self.expected,
                "missing independent greedy sequence")
        for token in self.expected:
            integer(token, "greedy token", 0, vocabulary-1)
        times = [integer(begin[name], name) for name in
                 ("prefill_start_ns", "prefill_end_ns", "decode_start_ns", "decode_end_ns")]
        require(times[0] < times[1] <= times[2] < times[3], "invalid measurement endpoints")
        self.prefill_ns, self.decode_ns = times[1]-times[0], times[3]-times[2]
        self.previous_commit = times[2]
        self.prefix = []
        self.current = self.expected[0]
        self.bytes_by_phase, self.bytes_by_class, self.beats = Counter(), Counter(), Counter()
        self.acceptance = Counter()
        self.seen = set()
        self.targets = {}
        self.compared = 0
        self.original_quality = []

    def ddr(self, item):
        phase, direction, category = item["phase"], item["direction"], item["category"]
        require(phase in ("prefill", "decode") and direction in ("read", "write") and
                category in {"weights", "scales", "zero_points", "kv", "control", "padding"},
                "invalid DDR classification")
        beats = integer(item["accepted_beats"], "accepted DDR beats")
        self.bytes_by_phase[phase] += 64 * beats
        self.bytes_by_class[phase, direction, category] += 64 * beats
        self.beats[phase, direction] += beats

    def vector(self, item):
        require(self.cell["engine"] == "ht2", "baseline vector in HT2 numerical checker")
        slot = integer(item["slot"], "vector slot", 0, self.cell["k"]-1)
        layer = integer(item["layer"], "vector layer", 0, 28)
        require((slot, layer) not in self.seen, "duplicate vector observation")
        self.seen.add((slot, layer))
        width = self.vocabulary if layer == 28 else self.hidden_size
        require(len(item["actual"]) == width, "partial layer or vocabulary vector")
        nrmse, cosine = fidelity(item["actual"], item["reference"])
        require(nrmse <= Decimal("0.01") and cosine >= Decimal("0.999"),
                "floating-point fidelity threshold failed")
        self.compared += 1
        if layer == 28:
            target = greedy(item["actual"])
            require(target == greedy(item["reference"]),
                    "target argmax differs from independent same-mode reference")
            self.targets[slot] = target
            if self.cell["mode"].startswith(("w4-", "w2-")):
                # This distinct comparison is reported, not tested as quantization-free fidelity.
                self.original_quality.append(tuple(str(x) for x in fidelity(
                    item["actual"], item["original_bf16"])))

    def batch(self, item):
        require(self.cell["engine"] == "ht2", "baseline speculative batch")
        require(self.seen == set(itertools.product(range(self.cell["k"]), range(29))),
                "missing production layer/logit comparisons")
        ids, parents = draft(self.begin["prompt_id"], self.prefix, self.current,
                             self.cell["k"], self.vocabulary)
        require(item["ids"] == ids and item["parents"] == parents,
                "draft differs from frozen non-target-aware generator")
        path, next_token = selected_path(ids, parents,
                                         [self.targets[i] for i in range(self.cell["k"])])
        mask = sum(1 << i for i in path)
        require(integer(item["accepted"], "accepted count", 1, self.cell["k"]) == len(path) and
                integer(item["mask"], "accepted mask", 1, 15) == mask and
                integer(item["next_token"], "next token", 0, self.vocabulary-1) == next_token and
                integer(item["position"], "position") == len(self.prefix)+len(path),
                "incorrect tree acceptance, next token or pointer")
        start = integer(item["accept_ns"], "batch acceptance time")
        end = integer(item["commit_ns"], "batch commit time")
        require(self.previous_commit <= start < end <= self.begin["decode_end_ns"],
                "nonmonotonic batch observation")
        if not self.prefix:
            require(start == self.begin["decode_start_ns"], "decode excludes initial draft overhead")
        accepted = [ids[i] for i in path]
        require(self.expected[len(self.prefix):len(self.prefix)+len(path)] == accepted,
                "accepted path disagrees with non-speculative greedy sequence")
        self.prefix.extend(accepted)
        self.current, self.previous_commit = next_token, end
        self.acceptance[len(path)] += 1
        self.seen.clear()
        self.targets.clear()

    def token(self, item):
        require(self.cell["engine"] in BASELINES, "HT2 tokens must use checked batch publication")
        value = integer(item["id"], "baseline token", 0, self.vocabulary-1)
        when = integer(item["commit_ns"], "baseline commit time")
        require(self.previous_commit < when <= self.begin["decode_end_ns"],
                "nonmonotonic baseline observation")
        self.prefix.append(value)
        self.previous_commit = when

    def finish(self, end):
        output = end["output_ids"]
        require(output == self.expected and self.prefix == output,
                "unobserved output tokens or different independent greedy sequence")
        require(self.previous_commit == self.begin["decode_end_ns"] and not self.seen,
                "decode endpoint is not final publication or vectors remain")
        require(len(output) >= 128 or output[-1] in self.eos_ids,
                "fewer than 128 tokens without model EOS")
        require(not any(token in self.eos_ids for token in output[:-1]),
                "generation continued after EOS")
        require(end["ended_eos"] is (output[-1] in self.eos_ids), "EOS marker mismatch")
        require(self.bytes_by_phase["prefill"] > 0 and self.bytes_by_phase["decode"] > 0,
                "missing actual DDR traffic")
        # Separate physical fabric counters catch omitted metadata/KV/control traffic.
        for phase, direction in itertools.product(("prefill", "decode"), ("read", "write")):
            count = integer(end["fabric_beats"][phase][direction], "fabric beat counter")
            require(self.beats[phase, direction] == count,
                    f"unaccounted {phase} {direction} DDR beats")
        return {
            "tokens": len(output), "decode_ns": self.decode_ns, "prefill_ns": self.prefill_ns,
            "measured_clock_hz": self.clock, "ddr_bytes": dict(self.bytes_by_phase),
            "ddr_classes": {"/".join(key): value for key, value in self.bytes_by_class.items()},
            "acceptance": dict(self.acceptance), "compared_vectors": self.compared,
            "quantized_vs_original_bf16": self.original_quality,
        }


def summarize(rows):
    tokens = sum(row["tokens"] for row in rows)
    duration = sum(row["decode_ns"] for row in rows)
    require(tokens > 0 and duration > 0, "empty benchmark measurement")
    traffic = sum(row["ddr_bytes"]["decode"] for row in rows)
    acceptance = Counter()
    for row in rows:
        acceptance.update(row["acceptance"])
    return {
        "tokens": tokens, "decode_ns": duration,
        "prefill_ns": sum(row["prefill_ns"] for row in rows),
        "decode_tpm": str(Decimal(tokens)*Decimal(60000000000)/Decimal(duration)),
        "decode_ddr_bytes": traffic,
        "decode_ddr_bytes_per_token": str(Decimal(traffic)/Decimal(tokens)),
        "prefill_ddr_bytes": sum(row["ddr_bytes"]["prefill"] for row in rows),
        "acceptance": dict(acceptance),
        "measured_clocks_hz": sorted({row["measured_clock_hz"] for row in rows}),
        "compared_vectors": sum(row["compared_vectors"] for row in rows),
    }


def prerequisites(root, manifest):
    """Collect all missing inputs; one missing checkpoint never hides other gaps."""
    errors, paths = [], {}
    assets = manifest["assets"]
    for role in ("config", "tokenizer", "tokenizer_config", "checkpoint_index",
                 "generational_handoff"):
        try:
            paths[role] = validate_asset(root, assets[role])
        except (ValueError, KeyError) as exc:
            errors.append(f"{role}: {exc}")
    for group in ("checkpoint_shards", "quantized_weight_inputs", "q2_fp_sources",
                  "independent_reference_sources", "observations"):
        entries = manifest[group]
        if not entries:
            errors.append(f"{group}: no immutable inputs supplied")
        for index, binding in enumerate(entries):
            try:
                paths[f"{group}/{index}"] = validate_asset(root, binding)
            except ValueError as exc:
                errors.append(f"{group}/{index}: {exc}")
    if "config" in paths:
        config = json.loads(paths["config"].read_text())
        dimensions = {"num_hidden_layers": 28, "hidden_size": 1536,
                      "intermediate_size": 8960, "num_attention_heads": 12,
                      "num_key_value_heads": 2, "vocab_size": 151936}
        for field, expected in dimensions.items():
            if config.get(field) != expected:
                errors.append(f"config: {field} must be {expected}")
        if Decimal(str(config.get("rms_norm_eps", 0))) != Decimal("0.000001"):
            errors.append("config: rms_norm_eps must be 1e-6")
        if "rope_theta" not in config:
            errors.append("config: missing authentic RoPE configuration")
    if "checkpoint_index" in paths:
        index = json.loads(paths["checkpoint_index"].read_text())
        supplied = {Path(item["path"]).name for item in manifest["checkpoint_shards"]}
        required = set(index.get("weight_map", {}).values())
        if not required or not required.issubset(supplied):
            errors.append("checkpoint_index: weight_map shards are not completely manifested")
    return paths, errors


def execute(run):
    from verify import ROOT, hashes
    run.tool("python3")
    fixtures = run.path / f"accounting-fixtures-{uuid.uuid4().hex[:8]}"
    _, stdout, _ = run.command(["python3", "tests/benchmark_checks.py",
                               "--fixtures", run.relative(fixtures)],
                               "benchmark-accounting-self-tests")
    run.receipt["benchmark_accounting_self_tests"] = stdout.strip()
    manifest_path = ROOT / "tests/benchmark_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    require(manifest["schema"] == 1 and manifest["widths"] == list(WIDTHS) and
            manifest["modes"] == list(MODES) and manifest["kv_formats"] == list(KV_FORMATS) and
            manifest["draft_policy"] == "sha256-prefix-v1" and
            manifest["generated_tokens_per_prompt"] == 128 and
            manifest["minimum_tokens_per_domain_cell"] == 1000,
            "benchmark manifest changes the admitted matrix or thresholds")
    prompts = corpus(ROOT, manifest)
    paths, errors = prerequisites(ROOT, manifest)
    matrix = [{"cell": cell, "domain": domain, "status": "missing-observations"}
              for cell in cells() for domain in DOMAINS]
    report = {
        "schema": 1, "manifest_sha256": digest(manifest_path),
        "corpus_sha256": manifest["corpus"]["sha256"], "prompt_count": len(prompts),
        "expected_domain_cells": len(matrix), "matrix": matrix, "input_errors": errors,
        "asset_hashes": {key: digest(path) for key, path in paths.items()},
        "scope": "Independent raw-observation analysis. Production provenance requires runtime admission.",
    }
    report_path = run.path / "benchmark-analysis.json"

    def save():
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        run.receipt["benchmarks"] = {
            "analysis": run.relative(report_path), "prompt_count": len(prompts),
            "expected_domain_cells": len(matrix), "input_errors": errors}
        run.save()

    save()
    if errors:
        raise RuntimeError("benchmark prerequisites missing or invalid: " + "; ".join(errors))
    config = json.loads(paths["config"].read_text())
    eos = config["eos_token_id"]
    eos_ids = eos if isinstance(eos, list) else [eos]
    for value in eos_ids:
        integer(value, "EOS token", 0, config["vocab_size"]-1)
    grouped = defaultdict(dict)
    source_hashes = {key: value for key, value in hashes().items()
                     if key.startswith(("rtl/", "anvil_q2_ht_reference/rtl/", "design/"))}
    for index, binding in enumerate(manifest["observations"]):
        path = paths[f"observations/{index}"]
        with path.open() as stream:
            header = json.loads(next(stream))
            require(header["schema"] == 1 and header["model"] == manifest["model"] and
                    header["source_sha256"] == source_hashes and
                    header["corpus_sha256"] == manifest["corpus"]["sha256"],
                    "observation source/model/corpus binding mismatch")
            require(header["asset_sha256"] == {
                key: value for key, value in report["asset_hashes"].items()
                if not key.startswith("observations/")},
                "observation assets/reference/baseline binding mismatch")
            require(header["board"] == "10AX115N2F45E1SG" and header["origin"] == "hardware",
                    "production accounting requires actual production-device observations")
            active = None
            for line_number, line in enumerate(stream, 2):
                item = json.loads(line)
                kind = item["type"]
                if kind == "begin":
                    require(active is None, "overlapping prompt observations")
                    prompt = item["prompt_id"]
                    require(prompt in prompts, "unknown corpus prompt")
                    active = PromptAccount(item, config["vocab_size"], eos_ids)
                    key = cell_key(item["cell"])
                    require(prompt not in grouped[key], "duplicate cell/prompt measurement")
                else:
                    require(active is not None, f"orphan observation at line {line_number}")
                    if kind == "end":
                        grouped[key][prompt] = active.finish(item)
                        active = None
                    else:
                        require(kind in ("ddr", "vector", "batch", "token"),
                                f"unknown observation at line {line_number}")
                        getattr(active, kind)(item)
            require(active is None, "truncated prompt observation")
    failures = []
    summaries = {}
    for entry in matrix:
        cell, domain = entry["cell"], entry["domain"]
        required = {key for key, prompt in prompts.items() if prompt["domain"] == domain}
        available = grouped[cell_key(cell)]
        missing = sorted(required - available.keys())
        entry["missing_prompts"] = missing
        if missing:
            failures.append(f"{cell_key(cell)}/{domain}: missing {len(missing)} prompts")
            continue
        summary = summarize([available[prompt] for prompt in sorted(required)])
        entry.update(status="measured", summary=summary)
        summaries[cell_key(cell), domain] = summary
        if summary["tokens"] < 1000:
            failures.append(f"{cell_key(cell)}/{domain}: fewer than 1000 committed tokens")
    report["measurement_errors"] = failures
    save()
    require(not failures, "; ".join(failures))
    chosen = {"engine": "ht2", **manifest["production_cell"]}
    require(chosen in cells() and chosen["k"] == 4 and
            chosen["mode"] in ("bf16-sparse", "w4-sparse", "w2-sparse"),
            "declared production cell must be K=4 BF16/sparse mixed-precision")
    baseline = {"engine": "ht2", "k": 1, "mode": "bf16-dense", "kv": chosen["kv"]}
    comparisons = []
    for domain in (*DOMAINS, "aggregate"):
        def combined(cell):
            selected = [value for prompt, value in grouped[cell_key(cell)].items()
                        if domain == "aggregate" or prompts[prompt]["domain"] == domain]
            return summarize(selected)
        result, dense = combined(chosen), combined(baseline)
        reduction = Decimal(1) - (Decimal(result["decode_ddr_bytes_per_token"]) /
                                  Decimal(dense["decode_ddr_bytes_per_token"]))
        comparisons.append({
            "domain": domain, "production": result, "dense_k1": dense,
            "ddr_reduction": str(reduction),
            "parent_speedups": {name: str(Decimal(result["decode_tpm"]) /
                                          Decimal(combined({"engine": name, "k": 1,
                                                           "mode": "baseline",
                                                           "kv": "baseline"})["decode_tpm"]))
                                for name in BASELINES},
        })
    report["production_comparisons"] = comparisons
    save()
    aggregate = comparisons[-1]
    require(Decimal(aggregate["production"]["decode_tpm"]) >= Decimal(3500),
            "measured aggregate production decode TPM is below 3500")
    require(Decimal(aggregate["ddr_reduction"]) > Decimal("0.5"),
            "actual per-committed-token DDR reduction is not greater than 50 percent")
