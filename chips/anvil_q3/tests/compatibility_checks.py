"""Compiled startup/recovery sweeps and compact dual-simulator portability.

The original multi-token compatibility workloads retain their exact geometry,
tokens and expectations. Icarus additionally executes single-token minimum-work
smokes rather than interpreting the full decoder sweeps.
"""

from dataclasses import replace
from decoder_checks import decoder_case
from execution import write_json
from parameters import compatibility_geometries, legal, startup_geometry
from leaf_checks import codec_case


def compact_portability(run):
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
                jobs.append(lambda g=g, s=simulator, p=profile: decoder_case(
                    run, g, simulator=s, tokens=[0], prefill_tokens=1,
                    first_new=int(p != 1), label="compact-portability"))
    ledger = run.parallel(jobs)
    if any(result["cycles"] > 500000 for result in ledger):
        raise AssertionError("portability smoke exceeds compact cycle tier")
    write_json(run.path / "compatibility-results.json", ledger)
    return ledger


def compatibility(run):
    ledger = compact_portability(run)
    jobs = []
    for profile in (1, 2, 3):
        g = startup_geometry(profile)
        if not legal(g):
            raise AssertionError("illegal compatibility fixture")
        jobs.append(lambda g=g, p=profile: decoder_case(
            run, g, simulator="verilator", tokens=[1, 4], first_new=int(p != 1),
            prelude=0 if p == 1 else 1, prefill_tokens=1,
            compiled_host=p == 1,
            label="implicit-startup" if p == 1 else "explicit-startup-recovery"))
        for prelude, label in ((2, "bad-first-position"), (3, "idle-cancel-recovery"),
                               (4, "bad-token-recovery"), (5, "active-cancel-recovery")):
            jobs.append(lambda g=g, p=prelude, l=label: decoder_case(
                run, g, simulator="verilator", tokens=[1, 4],
                prelude=p, prefill_tokens=1, label=l))
    for simulator in ("iverilog", "verilator"):
        for g in compatibility_geometries():
            if not legal(g):
                raise AssertionError("illegal legacy cache geometry")
            jobs.append(lambda g=g, s=simulator: codec_case(
                run, s, g.CACHE_MODE, profile=g.PROFILE, block=g.CACHE_BLOCK))
            if simulator == "verilator":
                jobs.append(lambda g=g, s=simulator: decoder_case(
                    run, g, simulator=s, tokens=[1, 2, 1, 2, 1, 2, 1],
                    first_new=1, compiled_host=True, label=f"legacy-c{g.CACHE_BLOCK}"))
    ledger.extend(run.parallel(jobs))
    write_json(run.path / "compatibility-results.json", ledger)
    return ledger
