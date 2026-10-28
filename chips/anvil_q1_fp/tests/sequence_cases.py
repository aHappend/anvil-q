#!/usr/bin/env python3
"""Published anvil-sequence-v1 generator: ten seed-17 cases in index order."""

import random


SEED = 17
GENERATOR_VERSION = 1


def generate():
    rng = random.Random(SEED)
    cases = []
    for index in range(10):
        if index < 7:
            values = [str(rng.randrange(100)) for _ in range(8 + index)]
            reverse = index >= 4
            instruction = "Reverse" if reverse else "Copy"
            prompt = (f"{instruction} these space-separated integers. "
                      "Return only the resulting space-separated integers:\n" +
                      " ".join(values))
            answer = " ".join(reversed(values) if reverse else values)
            kind = "reversal" if reverse else "exact-copy"
        else:
            keys = rng.sample(range(100, 1000), 8)
            pairs = [(f"key{key}", f"value{rng.randrange(10000):04d}") for key in keys]
            query, answer = pairs[rng.randrange(len(pairs))]
            prompt = ("Return only the value assigned to " + query + ":\n" +
                      "\n".join(key + "=" + value for key, value in pairs))
            kind = "key-retrieval"
        cases.append({"id": f"{index:06d}", "kind": kind,
                      "prompt": prompt, "answers": [answer]})
    return cases


if __name__ == "__main__":
    import json
    print(json.dumps(generate(), indent=2) + "\n", end="")
