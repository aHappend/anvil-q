"""Seeded public-interface one-layer model checks, independent of RTL algorithms."""

from decimal import Decimal, localcontext
import hashlib
import itertools
import json
import math
import random
import shutil

from reference import (BF16, FP16, FP32, add, convert, decimal_value, dot,
                       encode_ratio, kv_encode, multiply, tree)


def rounded(value, fmt=FP32):
    value = Decimal(value)
    numerator, denominator = abs(value).as_integer_ratio()
    result, error = encode_ratio(value.is_signed(), numerator, denominator, 0, fmt)
    if error:
        raise ValueError("nonfinite reference fixture")
    return result


def model(seed):
    rng = random.Random(seed)
    weights = {}
    embedding = [Decimal(rng.choice([-8, -4, 2, 6, 8])) / 8 for _ in range(8)]
    for index in (0, 1, 2, 3, *range(16, 28)):
        rows = 2 if index in (0, 1) else 5 if index == 3 else 8 if 16 <= index <= 22 else 1
        if index == 0:
            values = embedding + [-v for v in embedding]
        elif index == 1:
            signs = [Decimal(1 if v > 0 else -1) / 4 for v in embedding]
            values = [-v for v in signs] + signs
        elif index == 3:
            values = [Decimal(str(function(position * 1e6**(-pair/4))))
                      for position in range(5) for pair in range(4)
                      for function in (math.cos, math.sin)]
        elif index in (2, 23, 24):
            values = [Decimal(rng.choice([7, 8, 9])) / 8 for _ in range(8)]
        elif index >= 25:
            values = [Decimal(rng.choice([-1, 0, 1])) / 16 for _ in range(8)]
        else:
            # Diagonal paths keep token-dependent V observable, rather than
            # hiding attention defects behind identical values at every time.
            diagonal = Decimal("0.5") if index in (16, 17, 18) else Decimal("0.25")
            values = [diagonal if r == c and not (index == 20 and r in (1, 5))
                      else Decimal(0) for r in range(rows) for c in range(8)]
        weights[index] = [rounded(value, BF16) for value in values]
    return weights


class Reference:
    def __init__(self, weights, half, int8):
        self.fmt = FP16 if half else BF16
        self.int8 = int8
        self.weights = weights
        self.native = {i: [convert(v, BF16, self.fmt)[0] for v in values]
                       for i, values in weights.items()}
        self.quantized = False

    def expand(self, values):
        return [convert(v, self.fmt, FP32)[0] for v in values]

    def boundary(self, values):
        return [convert(v, FP32, self.fmt)[0] for v in values]

    def projection(self, values, index, bias=None):
        weights = self.weights[index] if self.quantized else self.native[index]
        weight_format = BF16 if self.quantized else self.fmt
        result = []
        for row in range(len(weights)//8):
            b = convert(self.native[bias][row], self.fmt, FP32)[0] if bias else 0
            result.append(dot(values + [0]*120, weights[8*row:8*row+8] + [0]*120,
                              [True]*8 + [False]*120, self.fmt, weight_format, b)[0])
        return result

    def norm(self, values, gamma):
        expanded = self.expand(values)
        total = sum(decimal_value(v)**2 for v in expanded)
        inverse = rounded(1 / (total / 8 + Decimal("0.000001")).sqrt())
        return self.boundary([multiply(multiply(x, inverse)[0], g)[0]
                              for x, g in zip(expanded, self.expand(self.native[gamma]))])

    def rotary(self, values, position):
        x = self.expand(values)
        coeff = self.expand(self.native[3][8*position:8*position+8])
        result = [0]*8
        for i in range(4):
            c, s = coeff[2*i:2*i+2]
            result[i] = add(multiply(x[i], c)[0], multiply(x[i+4], s)[0] ^ FP32.sign)[0]
            result[i+4] = add(multiply(x[i+4], c)[0], multiply(x[i], s)[0])[0]
        return self.boundary(result)

    def cache(self, values):
        bf = [convert(v, self.fmt, BF16)[0] for v in values]
        # Integrated fixture uses CACHE_BLOCK=1, including real stored INT8 scales.
        return [kv_encode([v], self.int8)[1][0] for v in bf]

    def infer(self, token, position, prefix):
        hidden = self.native[0][8*token:8*token+8]
        normalized = self.norm(hidden, 23)
        query = self.rotary(self.boundary(self.projection(normalized, 16, 25)), position)
        key = self.cache(self.rotary(self.boundary(self.projection(normalized, 17, 26)), position))
        value = self.cache(self.boundary(self.projection(normalized, 18, 27)))
        history = prefix + [(key, value)]
        scores = []
        for k, _ in history:
            score = 0
            for q, word in zip(self.expand(query), k):
                score = add(score, multiply(q, convert(word, BF16, FP32)[0])[0])[0]
            scores.append(decimal_value(multiply(score, rounded(Decimal(8).sqrt()**-1))[0]))
        maximum = max(scores)
        exponentials = [(score-maximum).exp() for score in scores]
        probabilities = [e / sum(exponentials) for e in exponentials]
        context = []
        for dimension in range(8):
            accumulated = 0
            for p, (_, v) in zip(probabilities, history):
                accumulated = add(accumulated, multiply(
                    rounded(p), convert(v[dimension], BF16, FP32)[0])[0])[0]
            context.append(accumulated)
        projected = self.boundary(self.projection(self.boundary(context), 19))
        hidden = self.boundary([add(a, b)[0] for a, b in
                                zip(self.expand(hidden), self.expand(projected))])
        normalized = self.norm(hidden, 24)
        gate = self.expand(self.boundary(self.projection(normalized, 20)))
        up = self.expand(self.boundary(self.projection(normalized, 21)))
        activated = self.boundary([multiply(multiply(g, rounded(
            1 / (1 + (-decimal_value(g)).exp())))[0], u)[0] for g, u in zip(gate, up)])
        projected = self.boundary(self.projection(activated, 22))
        hidden = self.boundary([add(a, b)[0] for a, b in
                                zip(self.expand(hidden), self.expand(projected))])
        logits = self.projection(self.norm(hidden, 2), 1)
        return logits, (key, value), probabilities

    def evaluate(self, ids, parents, position, prefix):
        logits, records, histories, probabilities = [], [], [], []
        for slot, token in enumerate(ids):
            ancestors = [] if slot == 0 else histories[parents[slot]]
            prediction, record, probs = self.infer(token, position+len(ancestors), prefix+ancestors)
            histories.append(ancestors+[record])
            logits.append(prediction)
            records.append(record)
            probabilities.append(probs)
        return logits, records, probabilities


def fixtures(run, seed, half, bits, sparse, int8):
    from verify import pack, top_fixture
    stem = f"seed{seed}-half{int(half)}-w{bits}-sparse{int(sparse)}-int8{int(int8)}"
    weights = model(seed)
    image, cfg = top_fixture(run, stem, half, bits, sparse, int8, weights)
    reference = Reference(weights, half, int8)
    reference.quantized = bits != 16
    prefix, pointer, transactions, expected = [], 0, [], []
    nonuniform = 0

    def append(ids, parents, fresh, label, cancel=0):
        nonlocal prefix, pointer, nonuniform
        position = 0 if fresh else pointer
        before = [] if fresh else prefix
        logits, records, probs = reference.evaluate(ids, parents, position, before)
        targets = [max(range(2), key=lambda i: (decimal_value(row[i]), -i)) for row in logits]
        accepted, mask, nxt, end, error = tree(
            len(ids), ids+[0]*(4-len(ids)), parents+[0]*(4-len(ids)),
            targets+[0]*(4-len(ids)), position, pointer,
            pack([1]*len(ids), 28), 0, 1, 5, fresh)
        if error:
            raise ValueError("independent matrix fixture overflows sequence")
        transactions.append((len(ids), position, int(fresh), pack(ids, 32), pack(parents, 2),
                             0 if cancel else accepted, 0 if cancel else mask,
                             0 if cancel else nxt, pointer if cancel else end, cancel))
        expected.append({"label": label, "logits": logits, "cancel": cancel,
                         "K": len(ids), "accepted": 0 if cancel else accepted, "mask": mask,
                         "targets": targets,
                         "nonuniform_rows": sum(len(p)>1 and max(p)-min(p)>Decimal("0.001") for p in probs)})
        if not cancel:
            prefix = before+[records[i] for i in range(len(ids)) if mask & (1 << i)]
            pointer = end
            nonuniform += expected[-1]["nonuniform_rows"]
        return targets

    def chain(count, fresh=True):
        ids, parents = [0], [0]
        before = [] if fresh else prefix
        position = 0 if fresh else pointer
        while len(ids) < count:
            logits, _, _ = reference.evaluate(ids, parents, position, before)
            ids.append(max(range(2), key=lambda i: (decimal_value(logits[-1][i]), -i)))
            parents.append(len(ids)-2)
        return ids, parents

    append([0], [0], True, "K1-prefix")
    ids, parents = chain(2, False)
    append(ids, parents, False, "K2-committed-prefix")
    ids, parents = chain(4)
    append(ids, parents, True, "K4-chain")
    # Noncontiguous matching path 0 -> 2 -> 3; slot 1 is a rejected sibling.
    ids, _ = chain(3)
    append([ids[0], ids[1]^1, ids[1], ids[2]], [0, 0, 0, 2], True, "K4-branch")
    ids, parents = chain(4)
    for phase in range(1, 5):
        append(ids, parents, True, f"cancel-phase-{phase}", phase)
    # All cancelled new sequences must preserve the three-token branch's prefix.
    append([1], [0], False, "post-cancel-prefix")
    if nonuniform == 0:
        raise ValueError("fixture failed to exercise nonuniform attention")
    path = run.path / f"{stem}-transactions.txt"
    path.write_text(str(len(transactions))+"\n"+"".join(
        f"{k} {p} {f} {ids:x} {parent:x} {a} {mask:x} {n} {end} {cancel}\n"
        for k, p, f, ids, parent, a, mask, n, end, cancel in transactions))
    expected_path = run.path / f"{stem}-expected.json"
    expected_path.write_text(json.dumps(expected, indent=2)+"\n")
    return stem, image, cfg, path, expected


def fidelity(actual, expected):
    if not actual or len(actual) != len(expected):
        raise AssertionError("MATRIX_NUMERICAL missing vector")
    x = [float(decimal_value(v)) for v in actual]
    y = [float(decimal_value(v)) for v in expected]
    if not all(math.isfinite(v) for v in x+y):
        raise AssertionError("MATRIX_NUMERICAL nonfinite logit")
    energy = sum(v*v for v in y)
    nrmse = math.sqrt(sum((a-b)**2 for a, b in zip(x, y))/max(energy, 1e-30))
    cosine = sum(a*b for a, b in zip(x, y))/math.sqrt(max(sum(a*a for a in x)*energy, 1e-60))
    if nrmse > 0.01 or cosine < 0.999:
        raise AssertionError(f"MATRIX_NUMERICAL NRMSE={nrmse:.8g} cosine={cosine:.8g} "
                             f"actual={actual} expected={expected}")
    if max(range(len(x)), key=lambda i: (x[i], -i)) != max(range(len(y)), key=lambda i: (y[i], -i)):
        raise AssertionError("MATRIX_GREEDY target ID mismatch")
    return nrmse, cosine


def compare(stdout, expected):
    observed, checked, witnesses = {}, set(), set()
    for line in stdout.splitlines():
        if line.startswith("RESULT matrix "):
            _, _, transaction, slot, index, value = line.split()
            key = tuple(map(int, (transaction, slot, index)))
            if key in observed:
                raise AssertionError("MATRIX_NUMERICAL duplicate result")
            observed[key] = int(value, 16)
        elif line.startswith("CHECKED matrix "):
            checked.add(int(line.split("transaction=")[1].split()[0]))
        elif line.startswith("WITNESS cancel "):
            witnesses.add(int(line.split("phase=")[1].split()[0]))
    if checked != set(range(len(expected))) or witnesses != {1, 2, 3, 4}:
        raise AssertionError("MATRIX_COVERAGE missing checked transaction/cancellation witness")
    results = []
    for transaction, row in enumerate(expected):
        if row["cancel"]:
            continue
        for slot, logits in enumerate(row["logits"]):
            actual = [observed.pop((transaction, slot, index)) for index in range(2)]
            nrmse, cosine = fidelity(actual, logits)
            results.append({"transaction": transaction, "slot": slot,
                            "nrmse": nrmse, "cosine": cosine})
    if any(not expected[t]["cancel"] for t, _, _ in observed):
        raise AssertionError("MATRIX_NUMERICAL unexpected logit")
    return results


def execute(run):
    from verify import ROOT, sources
    run.tool("verilator")
    run.tool("c++")
    obj = run.path / "top-matrix-compile-obj"
    run.receipt["integrated_matrix"] = []
    try:
        run.command(["verilator", "--binary", "--timing", "-Wno-fatal",
                     "--unroll-count", "1024", "--unroll-stmts", "100000",
                     "-CFLAGS", "-O2", "--top-module", "top_tb", "-GMATRIX=1",
                     "--Mdir", run.relative(obj), "-j", "2",
                     *[run.relative(p) for p in sources()], "tests/top_tb.sv"],
                    "top-matrix-compile")
        for seed, half, bits, sparse, int8 in itertools.product(
                (17, 89, 211), (False, True), (16, 4, 2), (False, True), (False, True)):
            with localcontext() as context:
                context.prec = 100
                stem, image, cfg, transactions, expected = fixtures(run, seed, half, bits, sparse, int8)
            _, stdout, _ = run.command(
                [run.relative(obj / "Vtop_tb"), "+image="+run.relative(image),
                 "+config="+run.relative(cfg), "+transactions="+run.relative(transactions)], stem)
            results = compare(stdout, expected)
            # A deliberately corrupted observed logit must reach this same checker.
            sensitivity = []
            for row in expected:
                if row["cancel"]:
                    continue
                vector = row["logits"][0]
                try:
                    fidelity([v ^ FP32.sign for v in vector], vector)
                except AssertionError as exc:
                    sensitivity.append(str(exc))
                else:
                    raise AssertionError("MATRIX_SENSITIVITY sign-flipped vector survived")
            run.receipt["integrated_matrix"].append({
                "seed": seed, "half": half, "weight_bits": bits, "sparse": sparse,
                "int8": int8, "fixture": stem, "transactions": len(expected),
                "checked_logits": 2*len(results), "comparisons": results,
                "checked_cases": [{"label": e["label"], "K": e["K"], "accepted": e["accepted"],
                                   "mask": e["mask"], "cancel": e["cancel"]} for e in expected],
                "sensitivity_rejections": sensitivity,
                "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                "summary": next(line for line in stdout.splitlines() if line.startswith("SUMMARY ")),
            })
            run.save()
            print(f"checked integrated {stem}: {len(results)} slot vectors", flush=True)
    finally:
        if obj.exists():
            shutil.rmtree(obj)
