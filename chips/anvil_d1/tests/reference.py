"""Independent integer equations for the admitted native D1 numerical contract.

No RTL or parent arithmetic helpers are imported. Memory observations are keyed
by the public (kind, layer, proj, row, col) tuple; write queues are per address,
so independently progressing memory clients do not impose an oracle bus order.
"""

from collections import defaultdict
from dataclasses import dataclass
from math import isqrt
import random

Q16 = 1 << 16
Q24 = 1 << 24


def sat32(x):
    return max(-(1 << 31), min((1 << 31) - 1, x))


def round_sat(x, shift):
    magnitude = abs(x)
    if shift:
        magnitude = (magnitude + (1 << (shift - 1))) >> shift
    return sat32(-magnitude if x < 0 else magnitude)


def trunc_div(n, d):
    if d <= 0:
        raise ValueError("nonpositive denominator")
    return -(abs(n) // d) if n < 0 else n // d


def rational_round(n, d):
    q, rem = divmod(abs(n), d)
    q += 2 * rem >= d
    return sat32(-q if n < 0 else q)


def exp_trace(x):
    if x >= 0:
        return {"x": x, "result": Q24, "terms": []}
    if x < -16 * Q16:
        return {"x": x, "result": 0, "terms": []}
    a = -x * 256
    n, r = divmod(a, 11629080)
    term = total = Q24
    terms = []
    for j in range(1, 7):
        numerator = term * r
        quotient = trunc_div(numerator, Q24 * j)
        remainder = abs(numerator) % (Q24 * j)
        term = -quotient
        total += term
        terms.append(dict(j=j, numerator=numerator, quotient=quotient,
                          remainder=remainder, term=term, total=total))
    return dict(x=x, a=a, n=n, r=r, terms=terms, result=max(total, 0) >> n)


def exp_q24(x):
    return exp_trace(x)["result"]


def silu(x):
    e = exp_q24(-abs(x))
    s = ((1 << 48) if x >= 0 else e * Q24) // (Q24 + e)
    return round_sat(x * s, 24)


def rms_trace(x, gamma):
    s = sum(v * v for v in x)
    mean, mean_rem = divmod(s << 32, len(x))
    e = mean + (1 << 48)
    d = isqrt(e)
    u, reciprocal_rem = divmod(1 << 64, d)
    products = [v * g for v, g in zip(x, gamma, strict=True)]
    return dict(x=list(x), gamma=list(gamma), S=s, M=mean,
                mean_remainder=mean_rem, E=e, d=d, root_remainder=e - d*d,
                u=u, reciprocal_remainder=reciprocal_rem, P=products,
                T=[v * u for v in products],
                outputs=[round_sat(v * u, 48) for v in products])


def rmsnorm(x, gamma):
    return rms_trace(x, gamma)["outputs"]


def dot(weights, x, shift=16, bias=0):
    return round_sat(sum(w * v for w, v in zip(weights, x, strict=True))
                     + (bias << 16), shift)


def rotate(x, table):
    result = []
    for p in range(len(x) // 2):
        a, b = x[2*p:2*p+2]
        c, s = table[2*p:2*p+2]
        result += [round_sat(a*c - b*s, 16), round_sat(a*s + b*c, 16)]
    return result


@dataclass(frozen=True)
class Shape:
    hidden: int = 16
    intermediate: int = 16
    moe_intermediate: int = 8
    heads: int = 2
    rank: int = 3
    nope: int = 2
    rope: int = 2
    value: int = 2
    layers: int = 2
    first_dense: int = 1
    experts: int = 7
    topk: int = 6
    vocab: int = 8
    maxseq: int = 5


class Fixture:
    """Deterministic generated Q16.16 weights and complete inference oracle."""

    def __init__(self, shape=Shape(), seed=17):
        self.shape = shape
        self.seed = seed
        self.initial = {}
        self.writes = defaultdict(list)
        self.cache = {}
        self.absorbed = {}
        self.routing = []
        self.contraction_characterization = []
        rng = random.Random(seed)

        def weight():
            return rng.randint(-Q16//3, Q16//3)

        h = shape.hidden
        for token in range(shape.vocab):
            for col in range(h):
                self.initial[0, 0, 0, token, col] = rng.randint(-Q16, Q16)
        for layer in range(shape.layers):
            for kind in (5, 6):
                for col in range(h):
                    self.initial[kind, layer, 0, 0, col] = rng.randint(Q16//2, Q16*3//2)
            for matrix, heads, rows, cols in (
                (0, 1, shape.rank, h), (1, 1, shape.rope, h),
                (2, shape.heads, shape.nope, h), (3, shape.heads, shape.rope, h),
                (4, shape.heads, shape.nope, shape.rank),
                (5, shape.heads, shape.value, shape.rank),
                (6, 1, h, shape.heads * shape.value),
            ):
                for head in range(heads):
                    for row in range(rows):
                        for col in range(cols):
                            self.initial[15, layer, 0, (matrix << 28) | (head << 24) | row, col] = weight()
            for e in range(shape.experts):
                for col in range(h):
                    self.initial[15, layer, 4, e, col] = weight()
            ids = [127] if layer < shape.first_dense else range(shape.experts + 2)
            for expert in ids:
                width = shape.intermediate if expert == 127 else shape.moe_intermediate
                for matrix, rows, cols in ((0, width, h), (1, width, h), (2, h, width)):
                    for row in range(rows):
                        for col in range(cols):
                            self.initial[15, layer, 5, (expert << 25) | (matrix << 23) | row, col] = weight()
                        self.initial[15, layer, 5, (expert << 25) | (3 << 23) | row, matrix] = weight()
            for pos in range(shape.maxseq):
                for pair in range(shape.rope // 2):
                    # Nontrivial exactly representable tables, not identity-only RoPE.
                    self.initial[15, layer, 6, pos, 2*pair] = 61440 - 1024*pos
                    self.initial[15, layer, 6, pos, 2*pair+1] = 16384 + 2048*pos
        for col in range(h):
            self.initial[7, 0, 0, 0, col] = rng.randint(Q16//2, Q16*3//2)

    def write(self, key, value):
        self.writes[key].append(value & 0xffffffff)

    def vector_write(self, kind, layer, proj, row, values, start=0):
        for col, value in enumerate(values, start):
            self.write((kind, layer, proj, row, col), value)

    def raw(self, layer, matrix, head, row, cols):
        return [self.initial[15, layer, 0, matrix << 28 | head << 24 | row, c]
                for c in range(cols)]

    def absorb(self, layer):
        s = self.shape
        for head in range(s.heads):
            a = [[sum(self.raw(layer, 4, head, d, s.rank)[r] *
                      self.raw(layer, 2, head, d, s.hidden)[j]
                      for d in range(s.nope))
                  for j in range(s.hidden)] for r in range(s.rank)]
            b = [[sum(self.raw(layer, 6, 0, i, s.heads*s.value)[head*s.value+v] *
                      self.raw(layer, 5, head, v, s.rank)[r]
                      for v in range(s.value))
                  for r in range(s.rank)] for i in range(s.hidden)]
            self.absorbed[layer, head] = (a, b)
            for proj, matrix in ((1, a), (2, b)):
                for row, values in enumerate(matrix):
                    for col, value in enumerate(values):
                        for word in range(3):
                            self.write((15, layer, proj, head << 28 | row, 3*col+word),
                                       (value >> (32*word)) & 0xffffffff)

    def mla(self, layer, pos, x):
        s = self.shape
        if (layer, 0) not in self.absorbed:
            self.absorb(layer)
        c = [dot(self.raw(layer, 0, 0, r, s.hidden), x) for r in range(s.rank)]
        kr0 = [dot(self.raw(layer, 1, 0, r, s.hidden), x) for r in range(s.rope)]
        self.vector_write(15, layer, 7, 6, kr0)
        table = [self.initial[15, layer, 6, pos, col] for col in range(s.rope)]
        kr = rotate(kr0, table)
        self.cache[layer, pos] = c, kr
        self.vector_write(15, layer, 3, pos, c + kr)
        qa, qr = [], []
        for head in range(s.heads):
            a, _ = self.absorbed[layer, head]
            qa.append([dot(row, x, 32) for row in a])
            qr0 = [dot(self.raw(layer, 3, head, r, s.hidden), x) for r in range(s.rope)]
            qr.append(rotate(qr0, table))
            self.vector_write(15, layer, 7, 5, qa[-1], head*s.rank)
            self.vector_write(15, layer, 7, 6, qr0, head*s.rope)
            self.vector_write(15, layer, 7, 6, qr[-1], head*s.rope)
        contexts = []
        for head in range(s.heads):
            scores = []
            for t in range(pos+1):
                ct, kt = self.cache[layer, t]
                numerator = sum(a*b for a, b in zip(qa[head], ct, strict=True))
                numerator += sum(a*b for a, b in zip(qr[head], kt, strict=True))
                scores.append(sat32(trunc_div(numerator, isqrt((s.nope+s.rope) << 32))))
            exponentials = [exp_q24(z-max(scores)) for z in scores]
            context = [rational_round(sum(e*self.cache[layer, t][0][r]
                                          for t, e in enumerate(exponentials)),
                                      sum(exponentials)) for r in range(s.rank)]
            contexts.append(context)
            self.vector_write(15, layer, 7, 7, context, head*s.rank)
        output = [round_sat(sum(self.absorbed[layer, head][1][i][r]*contexts[head][r]
                                for head in range(s.heads) for r in range(s.rank)), 32)
                  for i in range(s.hidden)]
        for head in range(s.heads):
            unabsorbed = [round_sat(sum(
                self.raw(layer, 4, head, d, s.rank)[r] *
                self.raw(layer, 2, head, d, s.hidden)[j] * x[j]
                for d in range(s.nope) for j in range(s.hidden)), 32)
                for r in range(s.rank)]
            if unabsorbed != qa[head]:
                raise AssertionError("unabsorbed query contraction mismatch")
        expanded = [round_sat(sum(
            self.raw(layer, 6, 0, i, s.heads*s.value)[head*s.value+v] *
            self.raw(layer, 5, head, v, s.rank)[r] * contexts[head][r]
            for head in range(s.heads) for v in range(s.value) for r in range(s.rank)), 32)
            for i in range(s.hidden)]
        if expanded != output:
            raise AssertionError("unabsorbed output contraction mismatch")
        conventional_q = []
        for head in range(s.heads):
            qn = [dot(self.raw(layer, 2, head, d, s.hidden), x) for d in range(s.nope)]
            conventional_q.extend(dot([self.raw(layer, 4, head, d, s.rank)[r]
                                       for d in range(s.nope)], qn) for r in range(s.rank))
        self.contraction_characterization.append(dict(
            layer=layer, position=pos,
            conventional_intermediate_rounding_query_differences=sum(
                a != b for a, b in zip(conventional_q,
                                      [v for head in qa for v in head], strict=True)),
            exact_unabsorbed_query_comparisons=s.heads*s.rank,
            exact_unabsorbed_output_comparisons=s.hidden))
        self.vector_write(15, layer, 7, 3, output)
        return output

    def expert(self, layer, expert, x):
        s = self.shape
        width = s.intermediate if expert == 127 else s.moe_intermediate

        def affine(matrix, row, values):
            weights = [self.initial[15, layer, 5, expert << 25 | matrix << 23 | row, col]
                       for col in range(len(values))]
            bias = self.initial[15, layer, 5, expert << 25 | 3 << 23 | row, matrix]
            return dot(weights, values, bias=bias)

        intermediate = [round_sat(silu(affine(0, i, x))*affine(1, i, x), 16)
                        for i in range(width)]
        output = [affine(2, i, intermediate) for i in range(s.hidden)]
        self.vector_write(15, layer, 7, 8, intermediate)
        self.vector_write(15, layer, 7, 4 if expert == 127 else 8,
                          output, 0 if expert == 127 else width)
        return output

    def moe(self, layer, x):
        s = self.shape
        if layer < s.first_dense:
            return self.expert(layer, 127, x)
        scores = [dot([self.initial[15, layer, 4, e, c] for c in range(s.hidden)], x)
                  for e in range(s.experts)]
        self.vector_write(15, layer, 7, 8, scores)
        exps = [exp_q24(z-max(scores)) for z in scores]
        probabilities = [e*Q24 // sum(exps) for e in exps]
        winners = sorted(range(s.experts), key=lambda e: (-scores[e], e))[:s.topk]
        p = sum(probabilities[e] for e in winners)
        weights = [probabilities[e]*Q24 // p for e in winners]
        remaining = Q24 - sum(weights)
        weights = [w + (i < remaining) for i, w in enumerate(weights)]
        self.routing.append(dict(layer=layer, scores=scores, probabilities=probabilities,
                                 winners=winners, weights=weights))
        shared = [self.expert(layer, e, x) for e in (s.experts, s.experts+1)]
        routed = [self.expert(layer, e, x) for e in winners]
        output = [round_sat(sum(v[i]*Q24 for v in shared) +
                            sum(v[i]*w for v, w in zip(routed, weights, strict=True)), 24)
                  for i in range(s.hidden)]
        self.vector_write(15, layer, 7, 4, output)
        return output

    def token(self, token, pos):
        s = self.shape
        x = [self.initial[0, 0, 0, token, c] for c in range(s.hidden)]
        self.vector_write(8, 0, 0, 0, x)
        for layer in range(s.layers):
            norm0 = rmsnorm(x, [self.initial[5, layer, 0, 0, c] for c in range(s.hidden)])
            self.vector_write(8, 0, 0, 1, norm0)
            branch = self.mla(layer, pos, norm0)
            residual = [sat32(a+b) for a, b in zip(x, branch, strict=True)]
            self.vector_write(8, 0, 0, 7, residual)
            norm1 = rmsnorm(residual, [self.initial[6, layer, 0, 0, c] for c in range(s.hidden)])
            self.vector_write(8, 0, 0, 8, norm1)
            branch = self.moe(layer, norm1)
            x = [sat32(a+b) for a, b in zip(residual, branch, strict=True)]
            self.vector_write(8, 0, 0, 0, x)
        final = rmsnorm(x, [self.initial[7, 0, 0, 0, c] for c in range(s.hidden)])
        self.vector_write(8, 0, 0, 14, final)
        return [dot([self.initial[0, 0, 0, token, c] for c in range(s.hidden)], final)
                for token in range(s.vocab)]
