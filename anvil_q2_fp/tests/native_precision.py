"""Streaming native five-domain precision against the common 70-digit workload."""

from collections import defaultdict
import math

from benchmark_checks import domain_indices
from high_precision_reference import MathematicalTransformer, ratio
from native_reference import as_float, native_geometry
from suite_manifest import DOMAINS


class Metrics:
    def __init__(self):
        self.count = 0
        self.maximum = 0.0
        self.parts = defaultdict(list)
        self.buffer = []

    def point(self, observed, expected):
        self.buffer.append((observed, expected))
        if len(self.buffer) == 1024:
            self.flush()

    def flush(self):
        if self.buffer:
            observed, expected = zip(*self.buffer)
            self.batch(observed, expected)
            self.buffer.clear()

    def batch(self, observed, expected):
        assert len(observed) == len(expected) and observed
        errors = [a - b for a, b in zip(observed, expected)]
        assert all(math.isfinite(x) for vector in (observed, expected, errors) for x in vector)
        self.count += len(errors)
        self.maximum = max(self.maximum, max(map(abs, errors)))
        for name, values in (
            ("absolute", (abs(x) for x in errors)),
            ("error2", (x * x for x in errors)),
            ("expected2", (x * x for x in expected)),
            ("observed2", (x * x for x in observed)),
            ("dot", (a * b for a, b in zip(observed, expected))),
        ):
            self.parts[name].append(math.fsum(values))

    def result(self):
        self.flush()
        assert self.count > 0
        totals = {name: math.fsum(values) for name, values in self.parts.items()}
        denominator = math.sqrt(totals["expected2"] * totals["observed2"])
        return dict(
            values_compared=self.count, max_absolute_error=self.maximum,
            mean_absolute_error=totals["absolute"] / self.count,
            rms_error=math.sqrt(totals["error2"] / self.count),
            normalized_rmse=math.sqrt(totals["error2"] / max(totals["expected2"], 1e-30)),
            cosine_similarity=totals["dot"] / denominator if denominator else None)


def observed_value(bits, parent):
    return ((bits - 2**32 if bits >= 2**31 else bits) / 65536 if parent else as_float(bits))


class PrecisionLogits:
    def __init__(self, owner, observations):
        self.owner = owner
        self.expected = iter(observations)
        self.count = 0

    def __len__(self):
        return self.count

    def append(self, item):
        position, row, ideal = item
        try:
            observed_position, observed_row, bits = next(self.expected)
        except StopIteration as exc:
            raise AssertionError("mathematical model produced extra logits") from exc
        assert (position, row) == (observed_position, observed_row)
        number = observed_value(bits, self.owner.parent)
        for domain in (0, 4):
            self.owner.metrics[domain].point(number, float(ideal))
        self.count += 1


class NativeMathematicalTransformer(MathematicalTransformer):
    def __init__(self, seed, geometry=None, observations=None, parent=False):
        self._output_cache = {}
        self.observations = observations
        self.parent = parent
        self.metrics = [Metrics() for _ in DOMAINS]
        super().__init__(seed, geometry or native_geometry())
        if observations is not None:
            self.logits = PrecisionLogits(self, observations.logits)

    def _tensors(self):
        self.weights, self.biases, self.norms = {}, {}, {}
        for layer in range(self.g.layers):
            for kind in (5, 6, 7):
                if kind != 7 or layer == 0:
                    self.norms[layer, kind] = [
                        1 + ratio((self.seed + kind + layer + col) % 5 - 2, 64)
                        for col in range(self.g.hidden)]

    def embedding(self, token):
        return [ratio((self.seed + 11 * token + 7 * col) % 33 - 16, 31)
                for col in range(self.g.hidden)]

    def projection(self, vector, layer, proj):
        outputs = (self.g.kv_heads * self.g.head_dim if proj in (1, 2) else
                   self.g.intermediate if proj in (4, 5) else self.g.hidden)
        assert len(vector) == (self.g.intermediate if proj == 6 else self.g.hidden)
        totals = [
            sum(a * ratio(
                (3 * self.seed + 5 * layer + 7 * proj + 11 * column + 13 * row) % 7 - 3,
                128 << ((self.seed + layer + proj + column // self.g.group + row) % 2))
                for column, a in enumerate(vector))
            for row in range(min(outputs, 14))]
        return [totals[row % 14] + (
            ratio((self.seed + 3 * layer + 5 * proj + row) % 9 - 4, 256) if proj < 3 else 0)
            for row in range(outputs)]

    def output_dot(self, norm, row):
        pattern = row % 3
        if pattern not in self._output_cache:
            self._output_cache[pattern] = sum(
                a * b for a, b in zip(norm, self.embedding(pattern)))
        return self._output_cache[pattern]

    def store(self, slot, vector, domain, layer, position):
        if slot == 14:
            self._output_cache.clear()
        if self.observations is None:
            return super().store(slot, vector, domain, layer, position)
        index = len(self.stages)
        assert index < len(self.observations.stages), "extra mathematical stage"
        observed = self.observations.stages[index]
        stage = dict(slot=slot, domain=domain, layer=layer, position=position)
        assert all(stage[field] == observed[field] for field in stage), "stage identity/order mismatch"
        numbers = [observed_value(bits, self.parent) for bits in observed["bits"]]
        ideals = [float(x) for x in vector]
        for index in domain_indices(stage):
            self.metrics[index].batch(numbers, ideals)
        self.stages.append(stage)
        self.writes[len(self.stages)] = [len(vector)]
        return vector

    def precision(self):
        assert self.observations is not None, "precision requires observed normative bit vectors"
        assert len(self.stages) == len(self.observations.stages)
        assert len(self.logits) == len(self.observations.logits)
        return {name: metrics.result() for name, metrics in zip(DOMAINS, self.metrics)}
