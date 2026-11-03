"""Descriptors derived from authenticated public JSON and the admitted ABI."""

import hashlib
import json
from pathlib import Path

from ieee_reference import rounded
from fractions import Fraction


PINS = {
    "qwen": "ec0c1f5f875ad8bc1f78c5140c22dbdde1b55478442ad358e7a4d9ecf947a327",
    "deepseek": "37bd455e9679d2959536270fed49d25cc7c290a64f6e52abb97c71345a9cee41",
}


def official(name):
    path = Path(__file__).resolve().parent / f"official-{name}-config.json"
    if hashlib.sha256(path.read_bytes()).hexdigest() != PINS[name]:
        raise AssertionError(f"official {name} configuration SHA256 mismatch")
    return json.loads(path.read_text())


def descriptor(name="qwen", banks=16):
    model = official(name)
    fp = lambda value: rounded(Fraction(str(value)))[0]
    h, q, kv = (model[field] for field in
                ("hidden_size", "num_attention_heads", "num_key_value_heads"))
    context = model["max_position_embeddings"]
    quant = model.get("quantization_config")
    return [
        1, 4, 0, 1 if quant else 0, 0, 0, banks,
        model["num_hidden_layers"], h, model["intermediate_size"], q, kv,
        h//q, model["vocab_size"], context, quant["group_size"] if quant else 128,
        1, fp(model["rope_theta"]), fp(model["rms_norm_eps"]), 32,
        (context+31)//32, int(bool(quant)), q//kv, 1 if name == "qwen" else 2,
    ] + [0]*8


def descriptor_cases():
    qwen, deepseek = descriptor(), descriptor("deepseek")
    yield "official-qwen", qwen, False, True
    yield "official-deepseek", deepseek, False, True
    minimum = qwen.copy()
    for index, value in {3: 0, 6: 1, 7: 1, 8: 2, 9: 1, 10: 1, 11: 1,
                         12: 2, 13: 1, 14: 1, 15: 1, 19: 1, 20: 1, 22: 1}.items():
        minimum[index] = value
    yield "minimum", minimum, False, True
    maximum = minimum.copy()
    for index, value in {6: 16, 7: 64, 8: 8192, 9: 32768, 10: 128,
                         11: 128, 12: 64, 13: 262144, 14: 131072,
                         15: 128, 19: 32, 20: 131072}.items():
        maximum[index] = value
    yield "maximum", maximum, False, True
    for ratio in (1, 3, 6, 7, 8):
        image = minimum.copy()
        image[8], image[10], image[22] = ratio*2, ratio, ratio
        image[16] = 0
        yield f"ratio-{ratio}", image, False, True
    invalid = {
        0: (0, 2), 1: (0, 5), 2: (2,), 3: (3,), 4: (1, 2), 5: (2,),
        6: (0, 3, 32), 7: (0, 65), 8: (0, 1, 8193), 9: (0, 32769),
        10: (0, 129), 11: (0, 129), 12: (0, 1, 3, 257),
        13: (0, 262145), 14: (0, 131073), 15: (0, 129), 16: (2,),
        17: (0, 0x80000000, 0xbf800000, 0x7f800000, 0x7fc00000),
        18: (0, 0x80000000, 0xbf800000, 0x7f800000, 0x7fc00000),
        19: (0, 3, 64), 20: (0, 131073), 21: (2,), 22: (0, 2, 9),
    }
    for index, values in invalid.items():
        for value in values:
            image = minimum.copy()
            image[index] = value
            yield f"invalid-word-{index}-{value}", image, False, False
    for index in range(24, 32):
        image = minimum.copy()
        image[index] = 1
        yield f"reserved-{index}", image, False, False
    yield "invalid-index", minimum, True, False
    image = minimum.copy()
    image[14] = 2
    yield "insufficient-pages", image, False, False
    yield "after-invalid-index", minimum, False, True
