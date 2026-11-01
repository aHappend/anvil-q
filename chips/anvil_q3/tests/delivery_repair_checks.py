"""Bounded synthesis-adaptation and missing-domain repair diagnostics."""

import argparse
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import ROOT, Run, write_json

SYNTHESIS_FAILURE = "evidence/check-synthesis/20261101T024842Z-96157c55d179/receipt.json"
BENCHMARK_SCOPE = "evidence/check-benchmark/20261101T021417Z-11f07242e755/receipt.json"


def adaptation_sensitivity():
    from synthesis_checks import scheduler_identifier_annotations

    text = (ROOT / "rtl/anvil_q3_bank_scheduler.sv").read_text()
    converted, annotations = scheduler_identifier_annotations(text)
    attribute = '(* fsm_encoding="none" *) '
    if converted.replace(attribute, "") != text or len(annotations) != 2:
        raise AssertionError("identifier adaptation changed more than synthesis attributes")
    rejected = []
    for row in annotations:
        for label, bad in (
                ("missing", text.replace(row["declaration"], "")),
                ("duplicate", text + "\n" + row["declaration"] + "\n"),
                ("width", text.replace(row["declaration"], "reg [31:0] " + row["register"] + ";"))):
            try:
                scheduler_identifier_annotations(bad)
            except AssertionError:
                rejected.append(row["register"] + ":" + label)
            else:
                raise AssertionError("changed annotation target accepted: " + label)
    return {"annotations": annotations, "rejected_declarations": rejected,
            "only_attributes_changed": True}


def benchmark_dispatch_sensitivity(folder):
    """Execute the real inventory/quality/row logic with explicitly mocked DUT data."""
    import benchmark_checks as checks

    fake = SimpleNamespace(path=folder, hashes={})
    fake.parallel = lambda jobs, **kwargs: [job() for job in jobs]
    calls = []
    lock, references = checks.quality_lock()
    data, _ = checks.corpus()
    by_id = {p["id"]: p for p in data["prompts"]}

    def decoder(run, g, seed=17, simulator=None, tokens=None, prefill_tokens=None, label=None):
        prompt = by_id[label]
        if (simulator != "verilator" or seed != 17 or
                tokens != prompt["prefill"] + prompt["decode"] or
                prefill_tokens != len(prompt["prefill"])):
            raise AssertionError("changed frozen benchmark dispatch")
        calls.append((g.CACHE_MODE, g.INT4_ASYM, g.BANKS, label))
        return {
            "logits": references[seed][label], "cycles": 1000 // g.BANKS,
            "token_cycles": [10] * len(tokens), "stalls": {"request": 1},
            "traffic": {"weight_bytes": 4, "cache_payload_metadata_bytes": 4},
            "compared_bits": 32, "trace_sha256": "offline-only", "geometry": {},
        }

    with (patch.object(checks, "tensor_speedup"),
          patch.object(checks, "validate_assets", return_value=[]),
          patch.object(checks, "official_weight_slice"),
          patch.object(checks, "quality_lock", return_value=(lock, references)),
          patch.object(checks, "decoder_case", side_effect=decoder)):
        rows = checks.benchmark(fake)
    if len(calls) != 44 or len(rows) != 44 or len(set(calls)) != 44:
        raise AssertionError("bounded 44-case benchmark inventory changed")
    rejected = []
    for domain in sorted(checks.DOMAINS):
        try:
            checks.assert_domain_coverage([r for r in rows if r["domain"] != domain])
        except AssertionError:
            rejected.append(domain)
        else:
            raise AssertionError("missing domain accepted: " + domain)
    try:
        checks.assert_domain_coverage(rows + rows[:1])
    except AssertionError:
        pass
    else:
        raise AssertionError("duplicate benchmark row accepted")
    if any(r["speedup"] != (8 if r["banks"] == 8 else 1) for r in rows):
        raise AssertionError("speedup lost identical-work baseline")
    native_calls = []

    def native_decoder(run, g, seed=17, simulator=None, tokens=None, prefill_tokens=None,
                       label=None, **kwargs):
        from quality_reference import mathematical_decoder
        from reference import Fixture

        prompt = by_id[label]
        if (simulator != "verilator" or seed != 17 or
                tokens != prompt["prefill"] + prompt["decode"] or
                prefill_tokens != len(prompt["prefill"])):
            raise AssertionError("changed native frozen benchmark dispatch")
        native_calls.append((kwargs.get("implementation", "q3"), label))
        return {
            "logits": mathematical_decoder(Fixture(g, seed), tokens),
            "cycles": 1000, "token_cycles": [10] * len(tokens),
            "stalls": {"request": 1}, "traffic": {
                "weight_bytes": 4, "cache_payload_metadata_bytes": 4},
            "compared_bits": 32, "bit_mismatches": 0, "trace_sha256": "offline-only",
            "geometry": {}, "native_source_binding": {"scope": "offline mock only"},
        }

    with (patch.object(checks, "supported_q1", return_value=True),
          patch.object(checks, "decoder_case", side_effect=native_decoder)):
        native = checks.native_q1_benchmark(fake, [{}], data, bounded_smoke=True)
    if (len(native) != 10 or len(native_calls) != 20 or
            {r["domain"] for r in native} != checks.DOMAINS or
            {label for _, label in native_calls} != set(by_id)):
        raise AssertionError("bounded native comparison lost frozen prompts/domains")
    return {"scope": "mocked dispatch/coverage only; no RTL numerical evidence",
            "q3_dispatches": calls, "missing_domains_rejected": rejected,
            "duplicate_rejected": True, "native_comparison_dispatches": native_calls}


def synthesis_probe(run):
    from parameters import A
    from synthesis_checks import synthesis_case

    run.versions([("yosys", "-V")])
    result = synthesis_case(run, replace(A, BANKS=8, CACHE_MODE=2, INT4_ASYM=1),
                            "identifier-repair")
    lowering = json.loads((run.path / "synthesis-identifier-repair/package-lowering.json").read_text())
    scheduler = next(row for row in lowering["sources"]
                     if row["source"] == "rtl/anvil_q3_bank_scheduler.sv")
    if len(scheduler["identifier_annotations"]) != 2:
        raise AssertionError("missing source-bound scheduler annotations")
    log = (ROOT / result["stdout"]).read_text()
    if re.search(r"Found FSM state register [^\n]*\.(capture_client|capture_slot)\.", log):
        raise AssertionError("identifier was still treated as FSM state")
    if not re.search(r"Extracting FSM [^\n]*\\state", log):
        raise AssertionError("genuine FSM extraction did not execute")
    return {"synthesis": result, "source_bound_annotations": scheduler,
            "genuine_fsm_extraction_preserved": True,
            "scope": "reduced diagnostic only; shipping-default synthesis/STA remain mandatory"}


def benchmark_probe(run):
    from benchmark_checks import THRESHOLDS, corpus, quality_lock
    from decoder_checks import decoder_case
    from parameters import A
    from quality_reference import cosine

    data, _ = corpus()
    lock, references = quality_lock()
    if lock != json.loads((ROOT / "tests/benchmark_lock.json").read_text()):
        raise AssertionError("frozen benchmark corpus changed")
    write_json(run.path / "frozen-quality-inputs.json", lock)
    prompt = next(p for p in data["prompts"] if p["domain"] == "Code/Syntax")
    run.versions([("verilator", "--version")])
    result = decoder_case(
        run, replace(A, BANKS=1), seed=17, simulator="verilator",
        tokens=prompt["prefill"] + prompt["decode"], prefill_tokens=len(prompt["prefill"]),
        label=prompt["id"])
    value = cosine(result["logits"], references[17][prompt["id"]])
    if value < THRESHOLDS[0, 0]:
        raise AssertionError("new-domain diagnostic below unchanged threshold")
    return {"exact": result, "domain": prompt["domain"], "cosine": str(value),
            "threshold": str(THRESHOLDS[0, 0]),
            "scope": "one previously missing domain; not five-domain aggregate acceptance"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", choices=("offline", "synthesis", "benchmark"), required=True)
    parser.add_argument("--worker-output")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.worker_output or "evidence/preparation/delivery-repair-" + stamp
    run = Run(output, "bounded " + args.probe + " repair diagnostic",
              repair_of=SYNTHESIS_FAILURE if args.probe == "synthesis" else BENCHMARK_SCOPE)
    print(run.rel(run.path / "receipt.json"), flush=True)
    try:
        run.versions([("python3", "--version")])
        if args.worker_output:
            result = synthesis_probe(run) if args.probe == "synthesis" else benchmark_probe(run)
        elif args.probe == "offline":
            folder = run.path / "offline-fixtures-0000"
            folder.mkdir()
            result = {"adaptation": adaptation_sensitivity(),
                      "benchmark": benchmark_dispatch_sensitivity(folder)}
        else:
            _, child = run.tool([
                "timeout", "--signal=TERM", "--kill-after=5s", "590s",
                "python3", "tests/delivery_repair_checks.py", "--probe", args.probe,
                "--worker-output", run.rel(run.path / ("diagnostic-" + stamp)),
            ])
            result = {"bounded_child": child, "budget_s": 590,
                      "scope": "advisory repair diagnostic, not admitted aggregate"}
    except Exception as exc:
        run.finish("failed", diagnosis=str(exc))
        raise
    run.finish("passed", result=result)


if __name__ == "__main__":
    main()
