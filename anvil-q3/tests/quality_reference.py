"""Uncompressed real-valued Decimal decoder, separate from fixed-point equations."""

from decimal import Decimal, localcontext

PI = Decimal("3.141592653589793238462643383279502884197169399375105820974944592307816406286")


def trigonometry(angle):
    angle %= 2 * PI
    if angle > PI:
        angle -= 2 * PI
    s, c = angle, Decimal(1)
    ts, tc = s, c
    for n in range(1, 160):
        ts *= -angle * angle / ((2 * n) * (2 * n + 1))
        tc *= -angle * angle / ((2 * n - 1) * (2 * n))
        s += ts
        c += tc
        if max(abs(ts), abs(tc)) < Decimal("1e-65"):
            return c, s
    raise ArithmeticError("trigonometric reference did not converge")


def mathematical_decoder(fixture, tokens):
    g = fixture.g
    with localcontext() as context:
        context.prec = 70
        unit = Decimal(65536)
        embeddings = [[Decimal(x) / unit for x in row] for row in fixture.embeddings]
        gamma = {k: [Decimal(x) / unit for x in row] for k, row in fixture.gamma.items()}
        weights = {k: [[Decimal(x) / unit for x in row] for row in matrix]
                   for k, matrix in fixture.weights.items()}
        biases = {k: [Decimal(x) / unit for x in row] for k, row in fixture.bias.items()}

        def norm(x, scale):
            denominator = (sum(v * v for v in x) / len(x) + Decimal("0.000001")).sqrt()
            return [v * s / denominator for v, s in zip(x, scale)]

        def projection(layer, p, x):
            out = [sum(a * b for a, b in zip(row, x)) for row in weights[layer, p]]
            return [a + b for a, b in zip(out, biases[layer, p])] if p < 3 else out

        def rotation(x, position):
            out = list(x)
            for head in range(len(x) // g.HEAD_DIM):
                for pair in range(g.HEAD_DIM // 2):
                    angle = Decimal(position) * (
                        -Decimal(2 * pair) / g.HEAD_DIM * Decimal(1000000).ln()).exp()
                    c, s = trigonometry(angle)
                    a = head * g.HEAD_DIM + pair
                    b = a + g.HEAD_DIM // 2
                    out[a], out[b] = x[a] * c - x[b] * s, x[b] * c + x[a] * s
            return out

        cache = {}
        logits = []
        largest = Decimal(0)
        for position, token in enumerate(tokens):
            x = embeddings[token]
            for layer in range(g.NUM_LAYERS):
                n = norm(x, gamma[layer, 5])
                q = rotation(projection(layer, 0, n), position)
                k = rotation(projection(layer, 1, n), position)
                v = projection(layer, 2, n)
                cache[layer, position] = k, v
                attention = []
                for head in range(g.NUM_Q_HEADS):
                    kh = head // (g.NUM_Q_HEADS // g.NUM_KV_HEADS)
                    scores = [sum(q[head * g.HEAD_DIM + d] *
                                  cache[layer, t][0][kh * g.HEAD_DIM + d]
                                  for d in range(g.HEAD_DIM)) / Decimal(g.HEAD_DIM).sqrt()
                              for t in range(position + 1)]
                    exponentials = [(s - max(scores)).exp() for s in scores]
                    attention.extend(
                        sum(cache[layer, t][1][kh * g.HEAD_DIM + d] * exponentials[t]
                            for t in range(position + 1)) / sum(exponentials)
                        for d in range(g.HEAD_DIM))
                out = projection(layer, 3, attention)
                residual = [a + b for a, b in zip(x, out)]
                n = norm(residual, gamma[layer, 6])
                gate, up = projection(layer, 4, n), projection(layer, 5, n)
                activated = [a / (1 + (-a).exp()) * b for a, b in zip(gate, up)]
                down = projection(layer, 6, activated)
                x = [a + b for a, b in zip(residual, down)]
                largest = max(largest, *(abs(y) for row in
                              (n, q, k, v, attention, out, residual, gate, up, activated, down, x)
                              for y in row))
            final = norm(x, gamma[0, 7])
            row = [sum(a * b for a, b in zip(final, embedding)) for embedding in embeddings]
            largest = max(largest, *(abs(y) for y in final), *(abs(y) for y in row))
            logits.append(row)
        if largest >= Decimal(32767):
            raise AssertionError("quality corpus is not nonsaturating")
        return logits


def cosine(observed, reference):
    with localcontext() as context:
        context.prec = 70
        a = [Decimal(x) / 65536 for row in observed for x in row]
        b = [x for row in reference for x in row]
        if len(a) != len(b) or not a:
            raise AssertionError("quality array shape mismatch")
        aa, bb = sum(x * x for x in a), sum(x * x for x in b)
        if aa == 0 or bb == 0:
            raise AssertionError("undefined cosine: zero-vector quality corpus")
        return sum(x * y for x, y in zip(a, b)) / (aa * bb).sqrt()
