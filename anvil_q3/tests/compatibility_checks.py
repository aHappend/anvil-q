"""Compiled startup/recovery sweeps and compact dual-simulator portability.

The original multi-token compatibility workloads retain their exact geometry,
tokens and expectations. Icarus additionally executes single-token minimum-work
smokes rather than interpreting the full decoder sweeps.
"""

from dataclasses import replace
from decoder_checks import decoder_case
from execution import workload, write_json
from parameters import compatibility_geometries, legal, startup_geometry
from leaf_checks import codec_case


def compact_portability_jobs(run):
    jobs = []
    for profile in (1, 2, 3):
        for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
            if mode >= profile:
                continue
            g = replace(startup_geometry(profile), BANKS=1, INTERMEDIATE_SIZE=8,
                        VOCAB_SIZE=1, CACHE_MODE=mode, INT4_ASYM=asym)
            if profile != 3:
                g = replace(g, HIDDEN_SIZE=8, NUM_Q_HEADS=1)
            if not legal(g):
                raise AssertionError("illegal compact portability fixture")
            for simulator in ("iverilog", "verilator"):
                jobs.append(workload(
                    run, "portability", "decoder_case", decoder_case, g,
                    simulator=simulator, tokens=[0], prefill_tokens=1,
                    first_new=int(profile != 1), label="compact-portability"))
    return jobs


def compact_portability(run):
    jobs = compact_portability_jobs(run)
    ledger = run.parallel(jobs)
    if any(result["cycles"] > 500000 for result in ledger):
        raise AssertionError("portability smoke exceeds compact cycle tier")
    write_json(run.path / "compatibility-results.json", ledger)
    return ledger


def compatibility_jobs(run):
    jobs = compact_portability_jobs(run)
    for profile in (1, 2, 3):
        g = startup_geometry(profile)
        if not legal(g):
            raise AssertionError("illegal compatibility fixture")
        jobs.append(workload(
            run, "compatibility", "decoder_case", decoder_case, g,
            simulator="verilator", tokens=[1, 4], first_new=int(profile != 1),
            prelude=0 if profile == 1 else 1, prefill_tokens=1,
            compiled_host=profile == 1,
            label="implicit-startup" if profile == 1 else "explicit-startup-recovery"))
        for prelude, label in ((2, "bad-first-position"), (3, "idle-cancel-recovery"),
                               (4, "bad-token-recovery"), (5, "active-cancel-recovery")):
            jobs.append(workload(
                run, "compatibility", "decoder_case", decoder_case, g,
                simulator="verilator", tokens=[1, 4],
                prelude=prelude, prefill_tokens=1, label=label))
    for simulator in ("iverilog", "verilator"):
        for g in compatibility_geometries():
            if not legal(g):
                raise AssertionError("illegal legacy cache geometry")
            jobs.append(workload(
                run, "compatibility", "codec_case", codec_case,
                simulator, g.CACHE_MODE, profile=g.PROFILE, block=g.CACHE_BLOCK))
            if simulator == "verilator":
                jobs.append(workload(
                    run, "compatibility", "decoder_case", decoder_case,
                    g, simulator=simulator, tokens=[1, 2, 1, 2, 1, 2, 1],
                    first_new=1, compiled_host=True, label=f"legacy-c{g.CACHE_BLOCK}"))
    return jobs


def compatibility(run, plan=False):
    jobs = compatibility_jobs(run)
    if plan:
        return jobs
    ledger = run.parallel(jobs)
    if any(result["cycles"] > 500000 for job, result in zip(jobs, ledger)
           if job.group == "portability"):
        raise AssertionError("portability smoke exceeds compact cycle tier")
    write_json(run.path / "compatibility-results.json", ledger)
    return ledger
