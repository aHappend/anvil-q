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
    ledger = []
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
                result = decoder_case(
                    run, g, simulator=simulator, tokens=[0], prefill_tokens=1,
                    first_new=int(profile != 1), label="compact-portability")
                if result["cycles"] > 500000:
                    raise AssertionError("portability smoke exceeds compact cycle tier")
                ledger.append(result)
                write_json(run.path / "compatibility-results.json", ledger)
    return ledger


def compatibility(run):
    ledger = compact_portability(run)
    for profile in (1, 2, 3):
        g = startup_geometry(profile)
        if not legal(g):
            raise AssertionError("illegal compatibility fixture")
        ledger.append(decoder_case(
            run, g, simulator="verilator", tokens=[1, 4], first_new=int(profile != 1),
            prelude=0 if profile == 1 else 1, prefill_tokens=1,
            label="implicit-startup" if profile == 1 else "explicit-startup-recovery"))
        write_json(run.path / "compatibility-results.json", ledger)
        for prelude, label in ((2, "bad-first-position"), (3, "idle-cancel-recovery"),
                               (4, "bad-token-recovery"), (5, "active-cancel-recovery")):
            ledger.append(decoder_case(run, g, simulator="verilator", tokens=[1, 4],
                                       prelude=prelude, prefill_tokens=1, label=label))
            write_json(run.path / "compatibility-results.json", ledger)
    for simulator in ("iverilog", "verilator"):
        for g in compatibility_geometries():
            if not legal(g):
                raise AssertionError("illegal legacy cache geometry")
            ledger.append(codec_case(run, simulator, g.CACHE_MODE, profile=g.PROFILE,
                                     block=g.CACHE_BLOCK))
            if simulator == "verilator":
                ledger.append(decoder_case(
                    run, g, simulator=simulator, tokens=[1, 2, 1, 2, 1, 2, 1],
                    first_new=1, label=f"legacy-c{g.CACHE_BLOCK}"))
            write_json(run.path / "compatibility-results.json", ledger)
    return ledger
