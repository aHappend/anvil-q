"""Executable frozen legality predicates and explicit mandatory geometries."""

from dataclasses import asdict, replace

from reference import Geometry


def legal(g):
    p = asdict(g)
    h, i, d, q, k = (p[n] for n in ("HIDDEN_SIZE", "INTERMEDIATE_SIZE", "HEAD_DIM",
                                   "NUM_Q_HEADS", "NUM_KV_HEADS"))
    l, v, s, group = (p[n] for n in ("NUM_LAYERS", "VOCAB_SIZE", "MAX_SEQ_LEN", "GROUP_SIZE"))
    if any(x <= 0 for x in (h, i, d, q, k, l, v, s, group)):
        return False
    if not (p["PROFILE"] in (1, 2, 3) and p["AWQ_BITS"] == 4 and
            p["BANKS"] in (1, 2, 4, 8) and 1 <= p["QUEUE_DEPTH"] <= 16 and
            p["INT4_ASYM"] in (0, 1) and 1 <= p["TILE_ROWS"] <= 8 and
            0 < p["TILE_K"] <= 128 and p["TILE_K"] % 8 == 0 and s <= 32768):
        return False
    if not (h == q * d and d % 2 == 0 and q % k == 0 and
            h % 8 == 0 and i % 8 == 0 and h % group == 0 and i % group == 0):
        return False
    if p["CACHE_MODE"] not in ((0,) if p["PROFILE"] == 1 else
                              (0, 1) if p["PROFILE"] == 2 else (0, 1, 2)):
        return False
    if p["PROFILE"] == 3:
        if q != 8 * k:
            return False
    else:
        block = p["CACHE_BLOCK"]
        if k * d % 8 or block <= 0 or block & (block - 1) or d % block:
            return False
    block = (64 if p["CACHE_MODE"] == 2 else 32) if p["PROFILE"] == 3 else p["CACHE_BLOCK"]
    blocks = (d + block - 1) // block
    words = (block * (4 if p["CACHE_MODE"] == 2 else 8) + 31) // 32
    coordinates = [h, i, d, q, k, l, v, group, k * d, 2 * d, k * blocks * words,
                   k * blocks, 15 * max(h, i)]
    extents = [4 * v * h, 4 * l * h * i, 4 * l * h * h, 4 * l * s * k * d,
               4 * l * s * k * blocks * words, 4 * l * s * k * blocks]
    return (max(coordinates) < 1 << 32 and max(extents) < 1 << 64 and
            d * (1 << 62) < 1 << 95 and s * (1 << 24) < 1 << 64)


A = Geometry()
A_PORTABILITY = replace(A, INTERMEDIATE_SIZE=8, VOCAB_SIZE=1)
B = Geometry(NUM_LAYERS=2, HIDDEN_SIZE=64, INTERMEDIATE_SIZE=96,
             HEAD_DIM=8, VOCAB_SIZE=31, MAX_SEQ_LEN=17)
C = Geometry(HIDDEN_SIZE=1024, INTERMEDIATE_SIZE=128, NUM_Q_HEADS=16,
             NUM_KV_HEADS=2, HEAD_DIM=64, GROUP_SIZE=128, TILE_K=128, TILE_ROWS=8)

PREFETCH_DIMENSIONS = {"NUM_LAYERS": 2, "HIDDEN_SIZE": 256, "INTERMEDIATE_SIZE": 384,
                       "NUM_KV_HEADS": 1, "HEAD_DIM": 2, "GROUP_SIZE": 8}


def leaf_legal(module, p):
    if module in ("anvil_q3_rmsnorm", "anvil_q3_rope"):
        if not (0 < p["NUM_LAYERS"] < 1 << 32 and
                0 < p["HIDDEN_SIZE"] * 15 < 1 << 32 and
                0 < p["MAX_SEQ_LEN"] <= 32768):
            return False
        if module == "anvil_q3_rope":
            return (p["HEAD_DIM"] > 0 and p["HEAD_DIM"] % 2 == 0 and
                    p["NUM_Q_HEADS"] > 0 and p["NUM_KV_HEADS"] > 0 and
                    p["HIDDEN_SIZE"] == p["NUM_Q_HEADS"] * p["HEAD_DIM"] and
                    p["NUM_KV_HEADS"] * p["HEAD_DIM"] < 1 << 32 and
                    p["HEAD_DIM"] * 2 < 1 << 32)
        return True
    if p["BANKS"] not in (1, 2, 4, 8):
        return False
    if module == "anvil_q3_bank_scheduler":
        return 1 <= p["CLIENTS"] <= 32 and 1 <= p["QUEUE_DEPTH"] <= 16
    if module == "anvil_q3_weight_prefetcher":
        return (0 < p["TILE_K"] <= 128 and p["TILE_K"] % 8 == 0 and
                1 <= p["TILE_ROWS"] <= 8 and
                all(p[key] > 0 for key in PREFETCH_DIMENSIONS) and
                p["NUM_KV_HEADS"] * p["HEAD_DIM"] < 1 << 32)
    raise ValueError("unknown leaf legality contract " + module)


def leaf_cases():
    cases = [
        ("anvil_q3_rmsnorm", {"NUM_LAYERS": 2, "HIDDEN_SIZE": 16, "MAX_SEQ_LEN": 32768}, True),
        ("anvil_q3_rope", {"NUM_LAYERS": 2, "HIDDEN_SIZE": 64, "HEAD_DIM": 8,
                           "NUM_Q_HEADS": 8, "NUM_KV_HEADS": 2, "MAX_SEQ_LEN": 32768}, True)]
    for banks in (1, 2, 4, 8):
        for depth in (1, 3, 16):
            cases.append(("anvil_q3_bank_scheduler",
                          {"BANKS": banks, "CLIENTS": 5, "QUEUE_DEPTH": depth}, True))
        for tile_k in (8, 24, 128):
            for rows in (1, 3, 8):
                cases.append(("anvil_q3_weight_prefetcher",
                              {**PREFETCH_DIMENSIONS, "BANKS": banks,
                               "TILE_K": tile_k, "TILE_ROWS": rows}, True))
    scheduler = {"BANKS": 8, "CLIENTS": 5, "QUEUE_DEPTH": 3}
    prefetch = {**PREFETCH_DIMENSIONS, "BANKS": 8, "TILE_K": 24, "TILE_ROWS": 3}
    for key, values in (("BANKS", (0, 3)), ("CLIENTS", (0, 33)), ("QUEUE_DEPTH", (0, 17))):
        cases += [("anvil_q3_bank_scheduler", {**scheduler, key: value}, False) for value in values]
    for key, values in (("BANKS", (0, 3)), ("TILE_K", (0, 7, 136)), ("TILE_ROWS", (0, 9)),
                        ("GROUP_SIZE", (0,)), ("NUM_LAYERS", (0,)), ("HIDDEN_SIZE", (0,)),
                        ("INTERMEDIATE_SIZE", (0,)), ("NUM_KV_HEADS", (0, 1 << 32)),
                        ("HEAD_DIM", (0,))):
        cases += [("anvil_q3_weight_prefetcher", {**prefetch, key: value}, False) for value in values]
    return cases


def behavioral_geometries():
    for name, base in (("A", A), ("B", B), ("C", C)):
        for banks in (1, 2, 4, 8):
            for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
                yield name, replace(base, BANKS=banks, CACHE_MODE=mode, INT4_ASYM=asym)


def compatibility_geometries():
    for profile in (1, 2):
        for block in (1, 16, 64):
            for mode in ((0,) if profile == 1 else (0, 1)):
                yield Geometry(PROFILE=profile, HIDDEN_SIZE=128, INTERMEDIATE_SIZE=128,
                               NUM_Q_HEADS=2, NUM_KV_HEADS=1, HEAD_DIM=64,
                               CACHE_MODE=mode, CACHE_BLOCK=block, GROUP_SIZE=8,
                               VOCAB_SIZE=3)


def startup_geometry(profile):
    if profile == 3:
        return A
    return replace(A, PROFILE=profile, NUM_Q_HEADS=2, HEAD_DIM=8)


def baseline_geometries():
    for profile, implementation in ((1, "q1-wrapper"), (2, "q2")):
        for mode in ((0,) if profile == 1 else (0, 1)):
            for banks in (1, 2, 4):
                yield implementation, replace(startup_geometry(profile),
                                              BANKS=banks, CACHE_MODE=mode)


def defaults(profile):
    return Geometry(PROFILE=profile, NUM_LAYERS={1: 24, 2: 28, 3: 36}[profile],
                    HIDDEN_SIZE={1: 896, 2: 1536, 3: 2048}[profile],
                    INTERMEDIATE_SIZE={1: 4864, 2: 8960, 3: 11008}[profile],
                    NUM_Q_HEADS={1: 14, 2: 12, 3: 16}[profile],
                    NUM_KV_HEADS=2, HEAD_DIM=64 if profile == 1 else 128,
                    GROUP_SIZE=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
                    TILE_K=128, TILE_ROWS=8)


def positive_cases():
    cases = list(behavioral_geometries())
    cases += [("compatibility", g) for g in compatibility_geometries()]
    cases += [("official-default", defaults(p)) for p in (1, 2, 3)]
    cases += [("official-cache-variant", replace(defaults(profile), CACHE_MODE=mode,
                                               INT4_ASYM=asym))
              for profile, mode, asym in ((2, 1, 0), (3, 1, 0), (3, 2, 0), (3, 2, 1))]
    cases += [("supplied-" + implementation, g)
              for implementation, g in baseline_geometries()]
    cases += [("tensor-only-128x128", replace(A, BANKS=b, HIDDEN_SIZE=128,
                                            INTERMEDIATE_SIZE=128, HEAD_DIM=16,
                                            GROUP_SIZE=128, TILE_K=128, TILE_ROWS=8))
              for b in (1, 2, 4, 8)]
    cases += [("startup-recovery", replace(A, PROFILE=p, NUM_Q_HEADS=2, HEAD_DIM=8))
              for p in (1, 2)]
    cases += [("compressed-metadata-fault-recovery",
               replace(startup_geometry(p), CACHE_MODE=1 if p == 2 else 2,
                       INT4_ASYM=int(p == 3))) for p in (2, 3)]
    cases += [("gqa-mutation-two-kv-heads", replace(A, HIDDEN_SIZE=32, NUM_Q_HEADS=16,
                                                 NUM_KV_HEADS=2))]
    for queue in (1, 3, 16):
        for tile_k in (8, 24, 128):
            for tile_rows in (1, 3, 8):
                cases.append(("queue-tile-boundary",
                              replace(A, QUEUE_DEPTH=queue, TILE_K=tile_k, TILE_ROWS=tile_rows)))
    for banks in (1, 2, 4, 8):
        for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
            cases.append(("singleton", replace(A, BANKS=banks, CACHE_MODE=mode, INT4_ASYM=asym,
                                               VOCAB_SIZE=1, MAX_SEQ_LEN=1,
                                               INTERMEDIATE_SIZE=8, TILE_K=8, TILE_ROWS=1,
                                               QUEUE_DEPTH=1)))
    unique = {}
    for label, g in cases:
        key = tuple(asdict(g).values())
        if key not in unique:
            unique[key] = (label, g)
    return list(unique.values())


def negative_cases():
    cases = []
    fields = {
        "PROFILE": (0, 4), "NUM_LAYERS": (0, -1), "HIDDEN_SIZE": (0, 15),
        "INTERMEDIATE_SIZE": (0, 23), "NUM_Q_HEADS": (0, 7),
        "NUM_KV_HEADS": (0, 3), "HEAD_DIM": (0, 3), "GROUP_SIZE": (0, 3),
        "AWQ_BITS": (3, 8), "VOCAB_SIZE": (0, 1 << 32), "MAX_SEQ_LEN": (0, 32769),
        "BANKS": (0, 3, 16), "CACHE_MODE": (-1, 3), "INT4_ASYM": (-1, 2),
        "QUEUE_DEPTH": (0, 17), "TILE_K": (0, 7, 136), "TILE_ROWS": (0, 9)}
    for field, values in fields.items():
        for value in values:
            cases.append((f"{field}={value}", replace(A, **{field: value})))
    cases += [("legacy-kv-product-two", replace(A, PROFILE=profile)) for profile in (1, 2)]
    cases += [("profile1-compressed", replace(next(compatibility_geometries()), CACHE_MODE=1))]
    for block in (0, 3, 128):
        cases.append(("legacy-cache-block", replace(list(compatibility_geometries())[-1],
                                                    CACHE_BLOCK=block)))
    return cases
