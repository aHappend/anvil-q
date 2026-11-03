"""80-digit Decimal inference characterization; never a tolerance-based oracle.

The bit-exact integer model remains authoritative. This independent real-valued
contraction uses exact generated Q16 weights, epsilon=2^-16, ideal exponential
and no tensor-boundary quantization. Report synthetic logit absolute/relative
error, not trained-checkpoint quality or hardware accuracy.
"""

from decimal import Decimal, localcontext
from reference import Fixture, Q16


class FloatingFixture:
    def __init__(self, fixture):
        self.fixture = fixture
        self.shape = fixture.shape
        self.cache = {}

    def word(self, key):
        return Decimal(self.fixture.initial[key])/Q16

    def raw(self, layer, matrix, head, row, cols):
        return [self.word((15, layer, 0, matrix << 28 | head << 24 | row, c))
                for c in range(cols)]

    def norm(self, x, kind, layer):
        root = (sum(v*v for v in x)/len(x)+Decimal(1)/Q16).sqrt()
        return [v*self.word((kind, layer, 0, 0, c))/root for c, v in enumerate(x)]

    def rotary(self, x, layer, pos):
        result = []
        for pair in range(len(x)//2):
            a, b = x[2*pair:2*pair+2]
            c = self.word((15, layer, 6, pos, pair*2))
            s = self.word((15, layer, 6, pos, pair*2+1))
            result.extend((a*c-b*s, a*s+b*c))
        return result

    def mla(self, layer, pos, x):
        s = self.shape
        c = [sum(a*b for a, b in zip(self.raw(layer, 0, 0, r, s.hidden), x, strict=True))
             for r in range(s.rank)]
        kr = self.rotary([sum(a*b for a, b in zip(
            self.raw(layer, 1, 0, r, s.hidden), x, strict=True)) for r in range(s.rope)], layer, pos)
        self.cache[layer, pos] = c, kr
        contexts = []
        for head in range(s.heads):
            qn = [sum(a*b for a, b in zip(self.raw(layer, 2, head, d, s.hidden), x, strict=True))
                  for d in range(s.nope)]
            qa = [sum(self.raw(layer, 4, head, d, s.rank)[r]*qn[d]
                      for d in range(s.nope)) for r in range(s.rank)]
            qr = self.rotary([sum(a*b for a, b in zip(
                self.raw(layer, 3, head, d, s.hidden), x, strict=True))
                for d in range(s.rope)], layer, pos)
            scores = [(sum(a*b for a, b in zip(qa, self.cache[layer, t][0], strict=True))+
                       sum(a*b for a, b in zip(qr, self.cache[layer, t][1], strict=True)))/
                      Decimal(s.nope+s.rope).sqrt() for t in range(pos+1)]
            exps = [(z-max(scores)).exp() for z in scores]
            contexts.append([sum(e*self.cache[layer, t][0][r] for t, e in enumerate(exps))/sum(exps)
                             for r in range(s.rank)])
        expanded = [[sum(self.raw(layer, 5, head, v, s.rank)[r]*contexts[head][r]
                         for r in range(s.rank)) for v in range(s.value)]
                    for head in range(s.heads)]
        return [sum(self.raw(layer, 6, 0, i, s.heads*s.value)[head*s.value+v]*expanded[head][v]
                    for head in range(s.heads) for v in range(s.value)) for i in range(s.hidden)]

    def expert(self, layer, expert, x):
        s = self.shape
        width = s.intermediate if expert == 127 else s.moe_intermediate

        def affine(matrix, row, vector):
            weights = [self.word((15, layer, 5, expert << 25 | matrix << 23 | row, col))
                       for col in range(len(vector))]
            return sum(a*b for a, b in zip(weights, vector, strict=True)) + self.word(
                (15, layer, 5, expert << 25 | 3 << 23 | row, matrix))

        work = []
        for row in range(width):
            gate = affine(0, row, x)
            work.append(gate/(1+(-gate).exp())*affine(1, row, x))
        return [affine(2, row, work) for row in range(s.hidden)]

    def token(self, token, pos):
        s = self.shape
        x = [self.word((0, 0, 0, token, col)) for col in range(s.hidden)]
        for layer in range(s.layers):
            attention = self.mla(layer, pos, self.norm(x, 5, layer))
            x = [a+b for a, b in zip(x, attention, strict=True)]
            norm = self.norm(x, 6, layer)
            if layer < s.first_dense:
                branch = self.expert(layer, 127, norm)
            else:
                scores = [sum(self.word((15, layer, 4, expert, col))*norm[col]
                              for col in range(s.hidden)) for expert in range(s.experts)]
                winners = sorted(range(s.experts), key=lambda e: (-scores[e], e))[:s.topk]
                weights = [(scores[e]-max(scores)).exp() for e in winners]
                denominator = sum(weights)
                shared = [self.expert(layer, e, norm) for e in (s.experts, s.experts+1)]
                routed = [self.expert(layer, e, norm) for e in winners]
                branch = [sum(v[col] for v in shared)+sum(
                    w*v[col]/denominator for w, v in zip(weights, routed, strict=True))
                    for col in range(s.hidden)]
            x = [a+b for a, b in zip(x, branch, strict=True)]
        final = self.norm(x, 7, 0)
        return [sum(self.word((0, 0, 0, word, col))*final[col] for col in range(s.hidden))
                for word in range(s.vocab)]


def characterize(seed):
    with localcontext() as context:
        context.prec = 80
        fixture = Fixture(seed=seed)
        model = FloatingFixture(fixture)
        records = []
        for pos in range(4):
            fixed, ideal = fixture.token(pos+2, pos), model.token(pos+2, pos)
            errors = [abs(Decimal(actual)/Q16-real)
                      for actual, real in zip(fixed, ideal, strict=True)]
            relative = [error/abs(real) for error, real in zip(errors, ideal, strict=True) if real]
            records.append(dict(position=pos, compared_scalars=len(fixed),
                                fixed_logits=fixed, ideal_logits=[str(v) for v in ideal],
                                maximum_absolute_error=str(max(errors)),
                                maximum_relative_error=str(max(relative)) if relative else None))
        return dict(seed=seed, precision_digits=80, records=records,
                    contraction_characterization=fixture.contraction_characterization,
                    accuracy_claim=False)
