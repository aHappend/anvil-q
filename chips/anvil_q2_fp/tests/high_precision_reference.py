"""Common 70-digit mathematical workload, without tensor/operation rounding.

Both RTL products are compared to these same rational source tensors and true
sqrt/exp/RoPE functions. This precision metric does not replace bit conformance.
"""

from decimal import Decimal, localcontext

from fp_reference import rope_real
from transformer_reference import Transformer


def ratio(numerator, denominator=1):
    return Decimal(numerator) / Decimal(denominator)


class MathematicalTransformer(Transformer):
    def __init__(self, seed, geometry=None):
        with localcontext() as ctx:
            ctx.prec = 70
            super().__init__("fp32", 0, 0, seed, geometry)

    def _tensors(self):
        g, seed = self.g, self.seed
        self.embeddings = [
            [ratio((seed + row * 11 + col * 7) % 33 - 16, 31)
             for col in range(g.hidden)] for row in range(g.vocabulary)]
        self.weights, self.biases, self.norms = {}, {}, {}
        for layer in range(g.layers):
            for kind in (5, 6, 7):
                if kind == 7 and layer != 0:
                    continue
                self.norms[layer, kind] = [
                    1 + ratio((seed + kind + layer + col) % 5 - 2, 64)
                    for col in range(g.hidden)]
            for proj in range(7):
                inputs = g.intermediate if proj == 6 else g.hidden
                outputs = (g.kv_heads * g.head_dim if proj in (1, 2) else
                           g.intermediate if proj in (4, 5) else g.hidden)
                self.weights[layer, proj] = [
                    [ratio((seed * 3 + layer * 5 + proj * 7 + column * 11 + row * 13) % 7 - 3,
                           128 << ((seed + layer + proj + column // g.group + row) % 2))
                     for column in range(inputs)] for row in range(outputs)]
                self.biases[layer, proj] = [
                    ratio((seed + layer * 3 + proj * 5 + row) % 9 - 4, 256)
                    for row in range(outputs)] if proj < 3 else []

    def store(self, slot, vector, domain, layer, position):
        self.stages.append({"domain": domain, "layer": layer, "position": position,
                            "slot": slot, "real": [str(x) for x in vector]})
        # Base execute's nonempty-write invariant remains meaningful here, while
        # these mathematical observations are never used as RTL memory fixtures.
        self.writes[len(self.stages)] = [str(x) for x in vector]
        return vector

    def embedding(self, token):
        return self.embeddings[token][:]

    def normalization(self, x, layer, kind):
        root = (sum(v * v for v in x) / len(x) + Decimal("0.000001")).sqrt()
        return [v / root * gamma for v, gamma in zip(x, self.norms[layer, kind])]

    def projection(self, vector, layer, proj):
        return [sum(a * b for a, b in zip(vector, weights)) +
                (self.biases[layer, proj][row] if proj < 3 else 0)
                for row, weights in enumerate(self.weights[layer, proj])]

    def rotate(self, vector, position):
        result = list(vector)
        half = self.g.head_dim // 2
        for head in range(len(vector) // self.g.head_dim):
            for component in range(half):
                i = head * self.g.head_dim + component
                j = i + half
                cosine, sine = rope_real(position, component, self.g.head_dim)
                result[i] = vector[i] * cosine - vector[j] * sine
                result[j] = vector[j] * cosine + vector[i] * sine
        return result

    def commit(self, vector, layer, position, is_value):
        self.cache[layer, position, is_value] = vector[:]

    def attention(self, query, layer, position):
        g = self.g
        result = []
        for head in range(g.q_heads):
            offset = head // (g.q_heads // g.kv_heads) * g.head_dim
            q = query[head * g.head_dim:(head + 1) * g.head_dim]
            scores = [
                sum(a * b for a, b in zip(q, self.cache[layer, t, False][offset:offset + g.head_dim])) /
                Decimal(g.head_dim).sqrt() for t in range(position + 1)]
            maximum = max(scores)
            weights = [(s - maximum).exp() for s in scores]
            denominator = sum(weights)
            result.extend(sum(w * self.cache[layer, t, True][offset + dim]
                              for t, w in enumerate(weights)) / denominator
                          for dim in range(g.head_dim))
        return result

    def residual(self, a, b):
        return [x + y for x, y in zip(a, b)]

    def swiglu(self, gate, up):
        return [a / (1 + (-a).exp()) * b for a, b in zip(gate, up)]

    def output_dot(self, norm, row):
        return sum(a * b for a, b in zip(norm, self.embeddings[row]))

    def execute(self):
        with localcontext() as ctx:
            ctx.prec = 70
            return super().execute()
