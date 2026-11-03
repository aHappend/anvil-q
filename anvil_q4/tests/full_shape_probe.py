"""Full official descriptor dimensions: real GEMV tile and boundary memory traffic."""

import argparse
from fractions import Fraction
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from descriptors import official, PINS
from execution import Experiment
from ieee_reference import evaluate, rounded


def fixture(path, name):
    model = official(name)
    h, inter, heads = (model[key] for key in
                       ("hidden_size", "intermediate_size", "num_attention_heads"))
    kv, d = model["num_key_value_heads"], h//heads
    vocabulary, context = model["vocab_size"], model["max_position_embeddings"]
    fmt, packing = (1, 8) if name == "qwen" else (2, 4)
    groups, words = (h+127)//128, (h+packing-1)//packing
    native = [evaluate(7, rounded(Fraction((col*13)%31-15, 16))[0])[0]
              for col in range(h)]
    activations = [evaluate(5, value)[0] for value in native]
    packed, zeros, scales, biases, expected = [], [], [], [], []
    offsets = (0, 16, 4, 20, 8, 24, 12, 28)
    for row in range(8):
        payload = [0]*words
        row_zeros = [(row+g*3) % (16 if fmt == 1 else 256) for g in range(groups)]
        row_scales = [0x3d000000 if g % 2 else 0x3eaaaaab for g in range(groups)]
        accumulator = 0
        for col in range(h):
            q = (row*17+col*13) % (16 if fmt == 1 else 256)
            shift = offsets[col%8] if fmt == 1 else 8*(col%4)
            payload[col//packing] |= q << shift
            value = evaluate(9, (q-row_zeros[col//128]) & 0xffffffff)[0]
            value = evaluate(2, value, row_scales[col//128])[0]
            value = evaluate(5, evaluate(7, value)[0])[0]
            product = evaluate(2, activations[col], value)[0]
            accumulator = evaluate(0, accumulator, product)[0]
        bias = evaluate(7, rounded(Fraction(row-3, 32))[0])[0]
        expected.append(evaluate(0, accumulator, evaluate(5, bias)[0])[0])
        packed.extend(payload); zeros.extend(row_zeros); scales.extend(row_scales)
        biases.append(bias)
    header = [h, inter, kv, d, vocabulary, context, model["num_hidden_layers"], fmt, words, groups]
    with path.open("w") as stream:
        stream.write(" ".join(map(str, header))+"\n")
        for values in (native, activations, packed, zeros, scales, biases, expected):
            stream.write(" ".join(f"{word:08x}" for word in values)+"\n")
    return {"profile": name, "hidden": h, "intermediate": inter, "kv_heads": kv,
            "head_dim": d, "vocabulary": vocabulary, "context": context,
            "layers": model["num_hidden_layers"], "weight_format": fmt,
            "gemv_rows_compared": 8, "embedding_words_compared": h,
            "scope": "synthetic full-input-width GEMV tile, last embedding token, last cache address",
            "fixture_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", action="store_true")
    parser.add_argument("--repair-of", action="append", default=[])
    args = parser.parse_args()
    experiment = Experiment("full-shape", args.preparation, args.repair_of)
    error = None
    try:
        experiment.receipt["official_config_sha256"] = PINS
        experiment.receipt["tool_version"] = experiment.run(["verilator", "--version"], "version")
        objects = experiment.directory/"compile-obj"
        sources = ("anvil_q4_00_fp_pkg", "anvil_q4_fp32", "anvil_q4_dequant",
                   "anvil_q4_activation_quantizer", "anvil_q4_tensor_array",
                   "anvil_q4_mem_port", "anvil_q4_gemv", "anvil_q4_token_io",
                   "anvil_q4_kv_cache")
        experiment.run([
            "verilator", "--binary", "--timing", "-Wno-fatal",
            "--top-module", "full_shape_tb", "--Mdir", experiment.rel(objects),
            "-o", "full-shape-sim", *("rtl/"+name+".sv" for name in sources),
            "tests/full_shape_tb.sv"], "compile")
        results = []
        experiment.receipt["cases"] = results
        for name in ("qwen", "deepseek"):
            path = experiment.directory/(name+".txt")
            geometry = fixture(path, name)
            output = experiment.run([experiment.rel(objects/"full-shape-sim"),
                                     "+VECTORS="+experiment.rel(path)], name)
            marker = f"SUMMARY full_shape hidden={geometry['hidden']} gemv_rows=8 "
            if marker not in output:
                raise AssertionError("missing full-shape exact numerical/address comparisons")
            results.append({**geometry, "summary": output[output.index(marker):].splitlines()[0]})
            experiment.save()
        experiment.prune_objects(objects)
    except (RuntimeError, ValueError, AssertionError, KeyError) as exc:
        error = exc
    finally:
        experiment.finish(error)
    if error:
        print(str(error), file=sys.stderr)
    return int(error is not None)


if __name__ == "__main__":
    raise SystemExit(main())
