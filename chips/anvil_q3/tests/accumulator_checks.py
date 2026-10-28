"""Public acceptance/completion calendar, with arbitrary-integer signed sums."""

from collections import Counter
import random

from execution import sha256, write_json


def accumulator_vectors(path, seed):
    rng = random.Random(seed)
    mask = (1 << 128) - 1
    low, high = -(1 << 127), (1 << 127) - 1
    total = 0
    pending = None
    result = None
    rows = []
    coverage = Counter()

    def emit(value=0, first=0, valid=0, ready=1, reset=1, flush=0):
        nonlocal total, pending, result
        edge = len(rows)

        def observe():
            if not reset or flush:
                return 0
            can_accept = pending is None and (result is None or ready)
            return ((int(can_accept) << 130) | (int(result is not None) << 129) |
                    ((result[1] if result else 0) << 128) | ((result[0] & mask) if result else 0))

        if not reset:
            total = 0
            pending = result = None
        before = observe()
        if not reset or flush:
            if pending:
                coverage["annul-work-age-" + str(8 - (pending[0] - edge))] += 1
            if result:
                coverage["annul-stalled-result"] += 1
            total = 0
            pending = result = None
        else:
            accepted = valid and bool(before >> 130)
            retired = result is not None and ready
            if retired:
                coverage["retired"] += 1
                result = None
            elif result:
                coverage["stalled-result"] += 1
            if accepted:
                exact = (0 if first else total) + value
                error = not low <= exact <= high
                wrapped = ((exact - low) & mask) + low
                pending = edge + 8, wrapped, int(error)
                coverage["accepted"] += 1
                coverage["restart" if first else "continue"] += 1
                coverage["signed-overflow"] += error
                coverage["retire-launch"] += retired
            elif pending and pending[0] == edge:
                total = pending[1]
                result = pending[1:]
                pending = None
                coverage["completed-after-eight"] += 1
        after = observe()
        rows.append([reset, flush, valid, first, ready, value & mask, before, after])

    def add(value, first=0, stall=0):
        while pending is not None or result is not None:
            emit()
        emit(value=value, first=first, valid=1)
        for _ in range(8):
            emit(ready=0)
        for _ in range(stall):
            emit(ready=0)

    emit(reset=0)
    for first, value in ((1, high), (0, 1), (1, low), (0, -1), (1, 0),
                         (0, low), (0, high), (0, 1)):
        add(value, first, stall=33)
    # Carry crosses every 16-bit boundary and both signs at full width.
    for bits in range(16, 128, 16):
        add((1 << bits) - 1, first=1)
        emit(value=1, valid=1)
        for _ in range(8):
            emit()
        add(-(1 << bits), first=1)
        emit(value=-1, valid=1)
        for _ in range(8):
            emit()
    for age in range(1, 9):
        add(123, first=1)
        emit(value=456, valid=1)
        for _ in range(age - 1):
            emit()
        emit(flush=1, valid=1, ready=0)
    add(789, first=1, stall=32)
    emit(flush=1, ready=0)
    for _ in range(2000):
        emit(value=rng.randrange(low, high + 1), first=int(rng.random() < .2),
             valid=int(rng.random() < .8), ready=int(rng.random() < .7),
             flush=int(rng.random() < .01))
    for _ in range(12):
        emit()
    if pending or result:
        raise AssertionError("undrained accumulator stimulus")
    required = ("signed-overflow", "retire-launch", "stalled-result", "annul-stalled-result",
                "restart", "continue", "completed-after-eight")
    if any(not coverage[key] for key in required):
        raise AssertionError("missing accumulator interaction")
    path.write_text("".join(" ".join(format(v, "x") for v in row) + "\n" for row in rows))
    return len(rows), dict(coverage)


def accumulator_case(run, simulator="iverilog", seed=17):
    folder = run.path / f"accumulator-s{seed}-{simulator}"
    folder.mkdir()
    path = folder / "vectors.txt"
    cycles, coverage = accumulator_vectors(path, seed)
    write_json(folder / "inputs.json", {"cycles": cycles, "coverage": coverage,
                                      "sha256": sha256(path), "seed": seed})
    sources = ["rtl/anvil_q3_accumulator.sv", "tests/accumulator_tb.sv"]
    if simulator == "iverilog":
        binary = folder / "accumulator.vvp"
        run.tool(["iverilog", "-g2012", "-Wall", "-s", "accumulator_tb",
                  "-o", run.rel(binary), *sources])
        command = ["vvp", run.rel(binary)]
    elif simulator == "verilator":
        obj = folder / "obj"
        run.tool(["verilator", "--binary", "--timing", "--assert", "-Wno-fatal",
                  "--top-module", "accumulator_tb", "--Mdir", run.rel(obj),
                  "-o", "accumulator", *sources])
        command = [run.rel(obj / "accumulator")]
    else:
        raise ValueError(simulator)
    text, receipt = run.tool([*command, "+vectors=" + run.rel(path)])
    if f"ACCUMULATOR_COMPLETE cycles={cycles}" not in text:
        raise AssertionError("incomplete accumulator comparisons")
    result = {"seed": seed, "simulator": simulator, "cycles": cycles, "coverage": coverage,
              "stdout": receipt["stdout"]}
    write_json(folder / "result.json", result)
    return result
