"""Shared structural workload and quality checks; missing baselines fail explicitly."""

from dataclasses import replace
from decimal import Decimal
import hashlib
import json

from decoder_checks import decoder_case
from execution import ROOT, sha256, write_json
from parameters import A
from quality_reference import cosine, mathematical_decoder
from reference import Fixture
from public_assets import validate_assets
from official_slice import official_weight_slice
from tensor_checks import tensor_speedup
from compatibility_checks import startup_geometry
from native_baselines import source_map, supported_q1

DOMAINS = {"Math/Arithmetic", "Code/Syntax", "Natural-Language QA",
           "Numeric Sequence", "Logic/Relational reasoning"}
THRESHOLDS = {(0, 0): Decimal("0.99"), (1, 0): Decimal("0.98"),
              (2, 0): Decimal("0.90"), (2, 1): Decimal("0.90")}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def tensor_digest(fixture):
    return digest(sorted((list(k), v) for k, v in fixture.memory.items()))


def corpus():
    path = ROOT / "tests/benchmark_corpus.json"
    data = json.loads(path.read_text())
    prompts = data["prompts"]
    if data["schema"] != 1 or {p["domain"] for p in prompts} != DOMAINS:
        raise AssertionError("five-domain corpus/schema mismatch")
    if len({p["id"] for p in prompts}) != len(prompts):
        raise AssertionError("duplicate prompt ID")
    for domain in DOMAINS:
        if sum(p["domain"] == domain for p in prompts) < 2:
            raise AssertionError("fewer than two prompts in " + domain)
    for p in prompts:
        if (not p["text"] or len(p["prefill"]) < 4 or len(p["decode"]) < 3 or
                not all(type(t) is int and 0 <= t < A.VOCAB_SIZE for t in p["prefill"] + p["decode"])):
            raise AssertionError("invalid prompt/token schedule")
    return data, sha256(path)


def quality_lock():
    data, corpus_hash = corpus()
    manifest = {"schema": 1, "corpus_sha256": corpus_hash, "seeds": {}}
    references = {}
    for seed in (17, 89, 257):
        fixture = Fixture(A, seed)
        refs = {p["id"]: mathematical_decoder(fixture, p["prefill"] + p["decode"])
                for p in data["prompts"]}
        references[seed] = refs
        manifest["seeds"][str(seed)] = {
            "tensor_sha256": tensor_digest(fixture),
            "mathematical_logits_sha256": digest(
                {key: [[str(x) for x in row] for row in value] for key, value in refs.items()})}
    return manifest, references


def quality_case(run, mode, asym, banks=8):
    data, _ = corpus()
    lock, references = quality_lock()
    if lock != json.loads((ROOT / "tests/benchmark_lock.json").read_text()):
        raise AssertionError("frozen quality inputs changed")
    prompt = data["prompts"][0]
    g = replace(A, BANKS=banks, CACHE_MODE=mode, INT4_ASYM=asym)
    result = decoder_case(run, g, seed=17, simulator="verilator",
                          tokens=prompt["prefill"] + prompt["decode"], label=prompt["id"])
    value = cosine(result["logits"], references[17][prompt["id"]])
    quality = {"cosine": str(value), "threshold": str(THRESHOLDS[mode, asym]),
               "prompt_id": prompt["id"], "cache_mode": mode, "int4_asymmetric": asym,
               "exact": result, "classification": data["classification"]}
    write_json(run.path / "quality-comparison.json", quality)
    if value < THRESHOLDS[mode, asym]:
        raise AssertionError("quality cosine below frozen acceptance")
    return quality


def baseline_prerequisites(assets, source_hashes, generations=("Q1", "Q2")):
    """Separate validated provenance from an executable generation adapter."""
    supplied = {name.rsplit("/", 1)[-1]: value for name, value in source_hashes.items()
                if name.startswith("anvil_q2_reference/rtl/")}
    rows, unmet = [], []
    for generation in generations:
        candidates = [asset for asset in assets if asset["category"] == "baseline" and
                      asset["generation"] == generation]
        source_bound = (
            generation == "Q2" and bool(supplied) and any(
                supplied == source_map(asset) for asset in candidates)
        ) or (generation == "Q1" and any(supported_q1(asset) for asset in candidates))
        rows.append({"generation": generation, "validated_assets": candidates,
                     "public_provenance_met": bool(candidates),
                     "source_bound_execution_adapter": source_bound})
        if not candidates:
            unmet.append(generation + ": independent native baseline assets/provenance absent "
                         "from declared public inputs")
        if not source_bound:
            unmet.append(generation + ": no independently source-bound native benchmark adapter")
    return {"generations": rows, "unmet": unmet,
            "supplied_reference": "anvil_q2_reference/rtl",
            "q1_wrapper_is_independent_q1": False}


def benchmark(run):
    tensor_speedup(run)
    declared = list(json.loads((ROOT / "tests/public_assets.json").read_text())["assets"])
    provenance = json.loads((ROOT / "design/model_provenance.json").read_text())
    for key in ("weight_assets", "tokenizer_assets", "generation_baselines"):
        declared.extend(provenance.get(key, []))
    assets = validate_assets(run, declared)
    baseline_status = baseline_prerequisites(assets, run.hashes)
    write_json(run.path / "cross-generation-prerequisites.json", baseline_status)
    official_weight_slice(run, assets)
    data, _ = corpus()
    lock, references = quality_lock()
    frozen = json.loads((ROOT / "tests/benchmark_lock.json").read_text())
    if lock != frozen:
        raise AssertionError("frozen corpus/tensors/reference changed; cannot replace failing fixtures")
    write_json(run.path / "frozen-quality-inputs.json", frozen)
    supplied_baselines(run, data)
    native_q1_benchmark(run, assets, data)
    results, outputs = [], {}
    for seed in (17, 89, 257):
        for mode, asym in THRESHOLDS:
            for banks in (1, 2, 4, 8):
                g = replace(A, BANKS=banks, CACHE_MODE=mode, INT4_ASYM=asym)
                if tensor_digest(Fixture(g, seed)) != frozen["seeds"][str(seed)]["tensor_sha256"]:
                    raise AssertionError("bank/cache variant changed immutable corpus tensors")
                domains = {domain: ([], []) for domain in DOMAINS}
                for prompt in data["prompts"]:
                    tokens = prompt["prefill"] + prompt["decode"]
                    result = decoder_case(run, g, seed=seed, simulator="verilator", tokens=tokens,
                                          prefill_tokens=len(prompt["prefill"]), label=prompt["id"])
                    actual = result.pop("logits")
                    reference = references[seed][prompt["id"]]
                    domains[prompt["domain"]][0].extend(actual)
                    domains[prompt["domain"]][1].extend(reference)
                    key = seed, mode, asym, prompt["id"]
                    if banks == 1:
                        outputs[key] = result["cycles"], actual
                    baseline_cycles, baseline_logits = outputs[key]
                    if actual != baseline_logits:
                        raise AssertionError("cache-matched output differs across banks")
                    prefill_cycles = sum(result["token_cycles"][:len(prompt["prefill"])])
                    decode_cycles = sum(result["token_cycles"][len(prompt["prefill"]):])
                    row = {"schema": 1, "generation": "Anvil-Q3", "profile": 3,
                           "model": "frozen nonzero synthetic fixture", "seed": seed,
                           "prompt_id": prompt["id"], "domain": prompt["domain"],
                           "classification": data["classification"],
                           "precision": "external binary16/AWQ W4; internal Q16.16",
                           "cache_mode": mode, "int4_asymmetric": asym, "banks": banks,
                           "prefill_cycles": prefill_cycles, "decode_cycles": decode_cycles,
                           "total_cycles": result["cycles"], "stalls": result["stalls"],
                           "weight_bytes": result["traffic"]["weight_bytes"],
                           "cache_payload_metadata_bytes":
                               result["traffic"]["cache_payload_metadata_bytes"],
                           "cosine": str(cosine(actual, reference)),
                           "compared_bits": result["compared_bits"], "bit_mismatches": 0,
                           "speedup": baseline_cycles / result["cycles"],
                           "trace_sha256": result["trace_sha256"], "geometry": result["geometry"]}
                    results.append(row)
                    write_json(run.path / "benchmark-rows.json", results)
                quality = {domain: str(cosine(actual, reference))
                           for domain, (actual, reference) in domains.items()}
                write_json(run.path / f"quality-s{seed}-m{mode}-a{asym}-b{banks}.json",
                           {"threshold": str(THRESHOLDS[mode, asym]), "domains": quality})
                if any(Decimal(value) < THRESHOLDS[mode, asym] for value in quality.values()):
                    raise AssertionError("per-domain aggregate cosine below frozen acceptance")
    if baseline_status["unmet"]:
        raise RuntimeError("cross-generation benchmark incomplete: " +
                           "; ".join(baseline_status["unmet"]))
    return results


def native_q1_benchmark(run, assets, data=None, simulator="verilator", bounded_smoke=False):
    """Native single-port Q1, same fixed corpus and independent profile-1 math.

    There is no Q1 multibank/cache-mode emulation. Speedup is measured only
    against identical Q1-profile work on Q3, including streaming and stalls.
    This is structural synthetic evaluation, not trained language-model quality.
    """
    candidates = [asset for asset in assets if supported_q1(asset)]
    if len(candidates) != 1:
        raise RuntimeError("exactly one supported source-bound native Q1 baseline is required")
    data = corpus()[0] if data is None else data
    g = replace(startup_geometry(1), BANKS=1, CACHE_MODE=0)
    seeds = (17,) if bounded_smoke else (17, 89, 257)
    prompts = data["prompts"][:1] if bounded_smoke else data["prompts"]
    fixtures, references = {}, {}
    for seed in seeds:
        fixture = Fixture(g, seed)
        references[seed] = {
            p["id"]: mathematical_decoder(fixture, p["prefill"] + p["decode"])
            for p in prompts}
        fixtures[str(seed)] = {
            "tensor_sha256": tensor_digest(fixture),
            "mathematical_logits_sha256": digest({
                key: [[str(x) for x in row] for row in value]
                for key, value in references[seed].items()})}
    write_json(run.path / "native-q1-input-lock.json", {
        "corpus_sha256": sha256(ROOT / "tests/benchmark_corpus.json"),
        "fixtures": fixtures, "asset": candidates[0], "bounded_smoke": bounded_smoke})
    ledger = []
    for seed in seeds:
        domains = {domain: ([], []) for domain in DOMAINS}
        for prompt in prompts:
            kwargs = dict(seed=seed, simulator=simulator,
                          tokens=prompt["prefill"] + prompt["decode"],
                          prefill_tokens=len(prompt["prefill"]), label=prompt["id"])
            native = decoder_case(run, g, implementation="q1-native",
                                  native_asset=candidates[0], **kwargs)
            q3 = decoder_case(run, g, **kwargs)
            if native["logits"] != q3["logits"]:
                raise AssertionError("Q3 profile1 differs from independently checked native Q1")
            actual, reference = native["logits"], references[seed][prompt["id"]]
            domains[prompt["domain"]][0].extend(actual)
            domains[prompt["domain"]][1].extend(reference)
            value = cosine(actual, reference)
            if value < THRESHOLDS[0, 0]:
                raise AssertionError("native Q1 quality below unchanged Mode0 threshold")
            ledger.append({
                "schema": 1, "generation": "Anvil-Q1 native public RTL",
                "implementation": "q1-native", "independent_q1_evidence": True,
                "classification": data["classification"], "model": "frozen nonzero synthetic fixture",
                "seed": seed, "prompt_id": prompt["id"], "domain": prompt["domain"],
                "banks": 1, "cache_mode": 0, "compatibility_profile": 1,
                "precision": "external binary16/AWQ W4; internal Q16.16",
                "prefill_cycles": sum(native["token_cycles"][:len(prompt["prefill"])]),
                "decode_cycles": sum(native["token_cycles"][len(prompt["prefill"]):]),
                "total_cycles": native["cycles"], "stalls": native["stalls"],
                "weight_bytes": native["traffic"]["weight_bytes"],
                "cache_payload_metadata_bytes": native["traffic"]["cache_payload_metadata_bytes"],
                "cosine": str(value), "threshold": str(THRESHOLDS[0, 0]),
                "compared_bits": native["compared_bits"], "bit_mismatches": native["bit_mismatches"],
                "trace_sha256": native["trace_sha256"], "geometry": native["geometry"],
                "source_binding": native["native_source_binding"],
                "q3_profile1_identical_work_cycles": q3["cycles"],
                "q3_over_native_q1_speedup": native["cycles"] / q3["cycles"],
                "bounded_smoke": bounded_smoke})
            write_json(run.path / "native-q1-benchmark-rows.json", ledger)
        quality = {domain: str(cosine(actual, reference))
                   for domain, (actual, reference) in domains.items() if actual}
        if not bounded_smoke and set(quality) != DOMAINS:
            raise AssertionError("native Q1 benchmark missing a domain comparison")
        write_json(run.path / f"native-q1-quality-s{seed}.json", {
            "domains": quality, "threshold": str(THRESHOLDS[0, 0]),
            "bounded_smoke": bounded_smoke})
        if any(Decimal(value) < THRESHOLDS[0, 0] for value in quality.values()):
            raise AssertionError("native Q1 per-domain quality below frozen threshold")
    return ledger


def supplied_baselines(run, data):
    """Measure supplied implementations, never relabel the Q1 wrapper as Q1 RTL."""
    source_binding = {name: value for name, value in run.hashes.items()
                      if name.startswith("anvil_q2_reference/rtl/")}
    if not source_binding:
        raise AssertionError("supplied baseline RTL is absent")
    frozen = {}
    references = {}
    for profile in (1, 2):
        for seed in (17, 89, 257):
            g = startup_geometry(profile)
            fixture = Fixture(g, seed)
            reference = {p["id"]: mathematical_decoder(fixture, p["prefill"] + p["decode"])
                         for p in data["prompts"]}
            references[profile, seed] = reference
            frozen[f"profile{profile}-seed{seed}"] = {
                "tensor_sha256": tensor_digest(fixture),
                "mathematical_logits_sha256": digest(
                    {key: [[str(x) for x in row] for row in value]
                     for key, value in reference.items()})}
    write_json(run.path / "supplied-baseline-input-lock.json", {
        "sources": source_binding, "corpus_sha256": sha256(ROOT / "tests/benchmark_corpus.json"),
        "fixtures": frozen, "scope": "frozen before supplied-baseline benchmark comparisons"})
    ledger, singles = [], {}
    for profile, implementation in ((1, "q1-wrapper"), (2, "q2")):
        for seed in (17, 89, 257):
            for mode in ((0,) if profile == 1 else (0, 1)):
                for banks in (1, 2, 4):
                    g = replace(startup_geometry(profile), BANKS=banks, CACHE_MODE=mode)
                    if tensor_digest(Fixture(g, seed)) != frozen[
                            f"profile{profile}-seed{seed}"]["tensor_sha256"]:
                        raise AssertionError("supplied baseline changed frozen tensors")
                    domains = {domain: ([], []) for domain in DOMAINS}
                    for prompt in data["prompts"]:
                        result = decoder_case(
                            run, g, seed, "verilator", tokens=prompt["prefill"] + prompt["decode"],
                            prefill_tokens=len(prompt["prefill"]), implementation=implementation,
                            label=prompt["id"])
                        reference = references[profile, seed][prompt["id"]]
                        actual = result["logits"]
                        domains[prompt["domain"]][0].extend(actual)
                        domains[prompt["domain"]][1].extend(reference)
                        key = profile, seed, mode, prompt["id"]
                        if banks == 1:
                            singles[key] = result["cycles"], actual
                        cycles, single_logits = singles[key]
                        if actual != single_logits:
                            raise AssertionError("supplied baseline bank-dependent numerical mismatch")
                        ledger.append({
                            "schema": 1, "generation": "Anvil-Q2 supplied RTL" if profile == 2 else
                            "Anvil-Q2 supplied Q1-compatible wrapper (not independent Q1 RTL)",
                            "implementation": implementation, "compatibility_profile": profile,
                            "model": "frozen nonzero synthetic fixture",
                            "classification": data["classification"], "seed": seed,
                            "prompt_id": prompt["id"], "domain": prompt["domain"], "banks": banks,
                            "cache_mode": mode, "cache_block": g.CACHE_BLOCK,
                            "precision": "external binary16/AWQ W4; internal Q16.16",
                            "prefill_cycles": sum(result["token_cycles"][:len(prompt["prefill"])]),
                            "decode_cycles": sum(result["token_cycles"][len(prompt["prefill"]):]),
                            "total_cycles": result["cycles"], "stalls": result["stalls"],
                            "weight_bytes": result["traffic"]["weight_bytes"],
                            "cache_payload_metadata_bytes":
                                result["traffic"]["cache_payload_metadata_bytes"],
                            "cosine": str(cosine(actual, reference)),
                            "compared_bits": result["compared_bits"], "bit_mismatches": 0,
                            "speedup": cycles / result["cycles"], "geometry": result["geometry"],
                            "trace_sha256": result["trace_sha256"], "source_hashes": source_binding,
                            "independent_q1_evidence": False})
                        write_json(run.path / "supplied-baseline-rows.json", ledger)
                    quality = {domain: str(cosine(actual, reference))
                               for domain, (actual, reference) in domains.items()}
                    write_json(run.path / f"baseline-quality-p{profile}-s{seed}-m{mode}-b{banks}.json",
                               {"domains": quality, "threshold": str(THRESHOLDS[mode, 0])})
                    if any(Decimal(value) < THRESHOLDS[mode, 0] for value in quality.values()):
                        raise AssertionError("supplied baseline per-domain quality below frozen threshold")
    return ledger
