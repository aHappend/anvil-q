"""Independent tensor mathematics and externally visible transaction inventory.

Reference arithmetic is FP64 over the selected stored tensors. No RTL helper,
internal signal, pipeline state, or computed DUT result enters the reference.
"""

from collections import defaultdict
import json
import math
import random

from numerical import bits32, decode, float32, floor_log2, power_two, round_even
from fractions import Fraction


CONFIGURATIONS = {
    "minimum": (1, 8, 8, 1, 1, 8, 1, 1, 1),
    "nonpower": (2, 24, 40, 3, 1, 8, 1, 3, 3),
    "gqa7": (2, 56, 72, 7, 1, 8, 8, 5, 3),
    "layers24": (24, 8, 8, 1, 1, 8, 1, 3, 1),
}
PARAMETERS = ("L", "H", "I", "Q", "K", "D", "G", "V", "S")


def encode16(value, mode):
    eb, fb = (8, 7) if mode == 1 else (5, 10)
    sign = int(value < 0)
    value = abs(Fraction(value))
    if not value:
        return sign << 15
    bias = (1 << (eb - 1)) - 1
    exponent = floor_log2(value)
    significand = round_even(value / power_two(max(exponent, 1-bias) - fb))
    if significand == 1 << (fb+1):
        significand >>= 1
        exponent += 1
    if exponent > bias:
        return (sign << 15) | (((1 << eb)-1) << fb)
    return (sign << 15) | (significand if exponent < 1-bias else
                           ((exponent+bias) << fb) | (significand & ((1 << fb)-1)))


class Architecture:
    def __init__(self, config, mode, seed):
        self.config = dict(zip(PARAMETERS, config))
        self.mode = mode
        self.seed = seed
        self.rng = random.Random(seed)
        self.fixture = {}
        self.memory = {}
        self.events = []
        self.group = ""
        self.position = 0
        self.populate()

    def tensor(self, key, value):
        encoding = encode16(value, self.mode or 2)
        self.fixture[key] = encoding
        eb, fb = (8, 7) if self.mode == 1 else (5, 10)
        self.memory[key] = float(decode(encoding, eb, fb)[3])

    def populate(self):
        c = self.config
        h, intermediate, layers, kv = c["H"], c["I"], c["L"], c["K"]*c["D"]
        for token in range(c["V"]):
            for col in range(h):
                self.tensor((0, 0, 0, token, col), Fraction(self.rng.randint(-24, 24), 64))
        for layer in range(layers):
            for kind in (5, 6, 7):
                if kind == 7 and layer:
                    continue
                for col in range(h):
                    self.tensor((kind, layer, 0, 0, col),
                                Fraction(self.rng.randint(48, 80), 64))
            for projection in range(7):
                rows = intermediate if projection == 6 else h
                cols = kv if projection in (1, 2) else (
                    intermediate if projection in (4, 5) else h)
                for row in range(rows):
                    for col in range(cols):
                        self.tensor((12, layer, projection, row, col),
                                    Fraction(self.rng.randint(-8, 8), 128))
                if projection < 3:
                    for col in range(cols):
                        self.tensor((4, layer, projection, 0, col),
                                    Fraction(self.rng.randint(-4, 4), 128))
                for row in range(rows):
                    for block in range(cols//8):
                        word = sum(self.rng.randrange(16) << (4*i) for i in range(8))
                        self.fixture[1, layer, projection, row, block] = word
                        self.memory[1, layer, projection, row, block] = word
                for group in range(rows//c["G"]):
                    for block in range(cols//8):
                        word = sum(7 << (4*i) for i in range(8))
                        self.fixture[2, layer, projection, group, block] = word
                        self.memory[2, layer, projection, group, block] = word
                    for col in range(cols):
                        self.tensor((3, layer, projection, group, col), Fraction(1, 128))
        for pos in range(c["S"]):
            for pair in range(c["D"]//2):
                angle = pos * 1000000.0**(-2*pair/c["D"])
                for parity, value in enumerate((math.cos(angle), math.sin(angle))):
                    key = (11, 0, 0, pos, 2*pair+parity)
                    bits = bits32(value) if self.mode else round(value*2**30) & 0xffffffff
                    self.fixture[key] = bits
                    self.memory[key] = float32(bits) if self.mode else value

    def write_fixture(self, path):
        c = self.config
        width = max(c["H"], c["I"])
        rows = max(width, c["V"], c["S"], 15)
        with path.open("w") as out:
            for (kind, layer, proj, row, col), value in sorted(self.fixture.items()):
                address = ((((kind*c["L"])+layer)*7+proj)*rows+row)*width+col
                out.write(f"@{address:x} {value:08x}\n")

    def read(self, kind, layer=0, proj=0, row=0, col=0):
        key = kind, layer, proj, row, col
        self.events.append(("M", 0, *key, None, self.group))
        return self.memory[key]

    def write(self, kind, value, layer=0, proj=0, row=0, col=0):
        key = kind, layer, proj, row, col
        self.events.append(("M", 1, *key, value, self.group))
        self.memory[key] = value

    def begin(self, name, layer=0):
        self.group = f"position{self.position}/layer{layer}/{name}"

    def norm(self, layer, source, destination, kind):
        self.begin("norm"+str(kind), layer)
        h = self.config["H"]
        values = [self.read(8, row=source, col=i) for i in range(h)]
        inverse = 1/math.sqrt(math.fsum(v*v for v in values)/h + float32(0x358637bd))
        for i in range(h):
            x = self.read(8, row=source, col=i)
            gamma = self.read(kind, layer=layer if kind != 7 else 0, col=i)
            self.write(8, x*gamma*inverse, row=destination, col=i)

    def gemv(self, layer, projection):
        self.begin("projection"+str(projection), layer)
        c = self.config
        inputs = c["I"] if projection == 6 else c["H"]
        outputs = (c["K"]*c["D"] if projection in (1, 2) else
                   c["I"] if projection in (4, 5) else c["H"])
        source = (1, 1, 1, 5, 8, 8, 11)[projection]
        destination = (2, 3, 4, 6, 9, 10, 12)[projection]
        for block in range(0, outputs, 8):
            sums = [[] for _ in range(8)]
            for row in range(inputs):
                if not self.mode and row % c["G"] == 0:
                    self.read(2, layer, projection, row//c["G"], block//8)
                    for lane in range(8):
                        self.read(3, layer, projection, row//c["G"], block+lane)
                x = self.read(8, row=source, col=row)
                if self.mode:
                    for lane in range(8):
                        weight = self.read(12, layer, projection, row, block+lane)
                        sums[lane].append(x*weight)
                else:
                    self.read(1, layer, projection, row, block//8)
            values = [math.fsum(terms) for terms in sums]
            if projection < 3:
                for lane in range(8):
                    values[lane] += self.read(4, layer, projection, 0, block+lane)
            for lane in range(8):
                self.write(8, values[lane], row=destination, col=block+lane)

    def rope(self, layer):
        self.begin("rope", layer)
        c = self.config
        for slot, heads in ((2, c["Q"]), (3, c["K"])):
            for head in range(heads):
                for pair in range(c["D"]//2):
                    col = head*c["D"]+pair
                    other = col+c["D"]//2
                    x, y = self.read(8, row=slot, col=col), self.read(8, row=slot, col=other)
                    cosine = self.read(11, row=self.position, col=2*pair)
                    sine = self.read(11, row=self.position, col=2*pair+1)
                    self.write(8, x*cosine-y*sine, row=slot, col=col)
                    self.write(8, y*cosine+x*sine, row=slot, col=other)

    def attention(self, layer):
        self.begin("attention", layer)
        c, pos = self.config, self.position
        dimension = c["D"]
        for slot, kind in ((3, 9), (4, 10)):
            for index in range(c["K"]*dimension):
                value = self.read(8, row=slot, col=index)
                self.write(kind, value, layer=layer, row=pos, col=index)
        for head in range(c["Q"]):
            kv = head//(c["Q"]//c["K"])

            def score(time):
                products = []
                for d in range(dimension):
                    q = self.read(8, row=2, col=head*dimension+d)
                    k = self.read(9, layer=layer, row=time, col=kv*dimension+d)
                    products.append(q*k)
                return math.fsum(products)/math.sqrt(dimension)

            maximum = max(score(time) for time in range(pos+1))
            for component in range(dimension):
                weights, products = [], []
                for time in range(pos+1):
                    weight = math.exp(score(time)-maximum)
                    weights.append(weight)
                    v = self.read(10, layer=layer, row=time, col=kv*dimension+component)
                    products.append(weight*v)
                self.write(8, math.fsum(products)/math.fsum(weights),
                           row=5, col=head*dimension+component)

    def elementwise(self, layer, mode):
        self.begin("silu" if mode == 2 else "residual"+str(mode), layer)
        c = self.config
        for index in range(c["I"] if mode == 2 else c["H"]):
            x = self.read(8, row=(0, 7, 9)[mode], col=index)
            y = self.read(8, row=(6, 12, 10)[mode], col=index)
            value = x*y/(1+math.exp(-x)) if mode == 2 else x+y
            self.write(8, value, row=(7, 0, 11)[mode], col=index)

    def execute(self):
        c = self.config
        for pos in range(c["S"]):
            self.position = pos
            self.begin("embedding")
            for i in range(c["H"]):
                x = self.read(0, row=pos % c["V"], col=i)
                self.write(8, x, col=i)
            for layer in range(c["L"]):
                self.norm(layer, 0, 1, 5)
                for projection in (0, 1, 2):
                    self.gemv(layer, projection)
                self.rope(layer)
                self.attention(layer)
                self.gemv(layer, 3)
                self.elementwise(layer, 0)
                self.norm(layer, 7, 8, 6)
                self.gemv(layer, 4)
                self.gemv(layer, 5)
                self.elementwise(layer, 2)
                self.gemv(layer, 6)
                self.elementwise(layer, 1)
            self.norm(0, 0, 14, 7)
            self.begin("logits")
            for vocabulary in range(c["V"]):
                products = []
                for i in range(c["H"]):
                    x = self.read(8, row=14, col=i)
                    w = self.read(0, row=vocabulary, col=i)
                    products.append(x*w)
                self.events.append(("O", vocabulary, math.fsum(products), self.group))
            self.events.append(("D",))
        return self.events


def metrics(actual, reference):
    error = max(abs(a-b) for a, b in zip(actual, reference))
    scale = max(1, max(map(abs, reference)))
    aa, bb = math.fsum(a*a for a in actual), math.fsum(b*b for b in reference)
    cosine = math.fsum(a*b for a, b in zip(actual, reference))/math.sqrt(aa*bb) if aa and bb else None
    ordered = lambda b: (~b & 0xffffffff) if b & 0x80000000 else b | 0x80000000
    pairs = [(bits32(a), bits32(b)) for a, b in zip(actual, reference)]
    return {
        "cosine": cosine, "normalized_max_absolute_error": error/scale,
        "max_ordered_ulp": max(abs(ordered(a)-ordered(b)) for a, b in pairs),
        "max_xor_bit_error": max(a ^ b for a, b in pairs),
        "reference_all_zero": bb == 0, "comparisons": len(actual),
    }


def compare_trace(model, path, report):
    groups = defaultdict(lambda: ([], []))
    observed = [line.split() for line in path.read_text().splitlines()]
    if not observed or observed[-1][0] != "C":
        raise ValueError("missing integration coverage trailer")
    if len(observed[-1]) != 9 or tuple(map(int, observed[-1][-2:])) != (model.mode, model.seed):
        raise ValueError("simulator did not execute requested precision and seed")
    events = observed[:-1]
    if len(events) != len(model.events):
        raise ValueError(f"integration trace count {len(events)} != {len(model.events)}")
    for index, (actual, expected) in enumerate(zip(events, model.events)):
        if actual[0] != expected[0]:
            raise ValueError(f"event {index}: {actual} != {expected}")
        if actual[0] == "M":
            if tuple(map(int, actual[1:7])) != expected[1:7]:
                raise ValueError(f"request address/order event {index}: {actual} != {expected}")
            if not expected[1]:
                continue
            bits, reference, group = int(actual[7], 16), expected[7], expected[8]
        elif actual[0] == "O":
            if int(actual[1]) != expected[1]:
                raise ValueError(f"logit order event {index}")
            bits, reference, group = int(actual[2], 16), expected[2], expected[3]
        else:
            continue
        if model.mode:
            value = float32(bits)
            if not math.isfinite(value):
                raise ValueError(f"nonfinite result event {index}")
            groups[group][0].append(value)
            groups[group][1].append(reference)
    results = {}
    passed = True
    for name, (actual, reference) in groups.items():
        result = metrics(actual, reference)
        final = name.endswith("/logits") and model.config["L"] == 24
        error_limit, cosine_limit = (0.01, 0.999) if final else (0.002, 0.9999)
        result["passed"] = result["normalized_max_absolute_error"] <= error_limit and (
            result["reference_all_zero"] or
            result["cosine"] is not None and result["cosine"] >= cosine_limit)
        result["error_limit"], result["cosine_limit"] = error_limit, cosine_limit
        results[name] = result
        passed &= result["passed"]
    report.write_text(json.dumps({
        "groups": results, "events_compared": len(events),
        "coverage": observed[-1], "passed": passed,
    }, indent=2) + "\n")
    return passed
