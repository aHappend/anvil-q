"""Reachable singleton, queue/tile maxima, context and recovery comparisons.

Singletons exercise the minimum queue/tile tuple for every bank/cache variant.
The maximum tuple additionally executes eight-bank asymmetric-INT4 seven-token
prefill/decode in compiled Verilator, not the full extrema cross-product. Leaf tests
and parameter elaboration alone do not establish these integrated comparisons.
"""

from dataclasses import replace

from compatibility_checks import startup_geometry
from decoder_checks import decoder_case
from execution import write_json
from parameters import A, legal


def singleton_geometry(banks, mode, asym):
    return replace(A, BANKS=banks, CACHE_MODE=mode, INT4_ASYM=asym,
                   VOCAB_SIZE=1, MAX_SEQ_LEN=1, INTERMEDIATE_SIZE=8,
                   TILE_K=8, TILE_ROWS=1, QUEUE_DEPTH=1)


def singleton_case(run, banks=8, mode=0, asym=0, simulator="iverilog"):
    g = singleton_geometry(banks, mode, asym)
    if not legal(g):
        raise AssertionError("singleton geometry must remain legal")
    return decoder_case(run, g, simulator=simulator, tokens=[0, 0], prefill_tokens=1,
                        boundary=1, restart_at=1, label="singleton-limit-and-recovery")


def boundaries(run):
    ledger = []
    for simulator in ("verilator",):
        for banks in (1, 2, 4, 8):
            for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
                ledger.append(singleton_case(run, banks, mode, asym, simulator))
                write_json(run.path / "boundary-results.json", ledger)
        g = replace(A, BANKS=8, CACHE_MODE=2, INT4_ASYM=1,
                    QUEUE_DEPTH=16, TILE_K=128, TILE_ROWS=8)
        if not legal(g):
            raise AssertionError("maximum queue/tile geometry must remain legal")
        ledger.append(decoder_case(
            run, g, simulator=simulator, tokens=[1, 4, 2, 6, 3, 5, 7],
            prefill_tokens=4, label="queue-tile-maxima"))
        write_json(run.path / "boundary-results.json", ledger)
        for profile in (1, 2, 3):
            g = startup_geometry(profile)
            for boundary in (1, 2, 3, 4):
                if boundary == 2 and profile == 1:
                    continue  # PROFILE1 intentionally ignores phase; compatibility checks it.
                prefix = g.MAX_SEQ_LEN if boundary == 1 else 2 if boundary == 2 else 1
                tokens = [1, 4, 2, 6, 3, 5, 7, 8, 9][:prefix] + [2]
                ledger.append(decoder_case(
                    run, g, simulator=simulator, tokens=tokens,
                    prefill_tokens=1 if boundary == 2 else g.MAX_SEQ_LEN,
                    boundary=boundary, restart_at=prefix, label=f"boundary-{boundary}"))
                write_json(run.path / "boundary-results.json", ledger)
    return ledger


def integration_faults(run):
    ledger = []
    for simulator in ("verilator",):
        for profile in (1, 2, 3):
            for scenario in range(1, 10):
                if profile == 1 and scenario == 9:
                    continue  # No compressed metadata exists in the lossless-only profile.
                g = startup_geometry(profile)
                if scenario == 9:
                    g = replace(g, CACHE_MODE=1 if profile == 2 else 2,
                                INT4_ASYM=int(profile == 3))
                ledger.append(decoder_case(run, g, simulator=simulator, tokens=[1, 4],
                                           fault_scenario=scenario,
                                           label=f"integration-fault-{scenario}"))
                write_json(run.path / "integration-faults.json", ledger)
    return ledger
