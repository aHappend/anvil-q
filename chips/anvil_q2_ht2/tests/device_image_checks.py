#!/usr/bin/env python3
"""Independent byte-layout checks and disposable device-image corruption controls."""

import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
from functools import lru_cache
import json
import math
from pathlib import Path
import random
import shutil
import struct
import sys
import uuid

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmarks import digest, portable_path, require, validate_asset
from reference import BF16, FP16, FP32, convert, encode_ratio

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def half_table():
    return np.array([convert(value, BF16, FP16)[0] for value in range(65536)], dtype="<u2")


def source_header(path):
    with path.open("rb") as stream:
        size = int.from_bytes(stream.read(8), "little")
        require(0 < size < 16*1024*1024, "invalid source header")
        entries = json.loads(stream.read(size))
    return entries, size+8


def roles(config, sequence):
    h, f = config["hidden_size"], config["intermediate_size"]
    d = h//config["num_attention_heads"]
    kv = config["num_key_value_heads"]*d
    expected = {0: ("model.embed_tokens.weight", config["vocab_size"], h, False),
                1: ("model.embed_tokens.weight" if config["tie_word_embeddings"] else
                    "lm_head.weight", config["vocab_size"], h, True),
                2: ("model.norm.weight", 1, h, False), 3: (None, sequence, d, False)}
    for layer in range(config["num_hidden_layers"]):
        names = ("self_attn.q_proj.weight", "self_attn.k_proj.weight",
                 "self_attn.v_proj.weight", "self_attn.o_proj.weight",
                 "mlp.gate_proj.weight", "mlp.up_proj.weight", "mlp.down_proj.weight",
                 "input_layernorm.weight", "post_attention_layernorm.weight",
                 "self_attn.q_proj.bias", "self_attn.k_proj.bias", "self_attn.v_proj.bias")
        shapes = ((h, h), (kv, h), (kv, h), (h, h), (f, h), (f, h), (h, f),
                  (1, h), (1, h), (1, h), (1, kv), (1, kv))
        for offset, (name, shape) in enumerate(zip(names, shapes)):
            expected[16+16*layer+offset] = (f"model.layers.{layer}."+name,
                                         *shape, offset < 7)
    return expected


def trig(angle):
    pi = Decimal("3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825342117068")
    x = angle % (2*pi)
    if x > pi:
        x -= 2*pi
    c, s, ct, st = Decimal(1), x, Decimal(1), x
    for n in range(1, 200):
        ct *= -x*x/((2*n-1)*(2*n))
        st *= -x*x/((2*n)*(2*n+1))
        c += ct
        s += st
        if max(abs(ct), abs(st)) < Decimal("1e-95"):
            return c, s
    raise ArithmeticError("independent coefficient series did not converge")


def decimal_native(value, half):
    numerator, denominator = abs(value).as_integer_ratio()
    word, error = encode_ratio(value.is_signed(), numerator, denominator, 0, FP32)
    require(not error, "coefficient overflow")
    return convert(word, FP32, FP16 if half else BF16)[0]


def check_rope(words, config, half):
    sequence, dimension = words.shape
    # Check every coefficient with scalar libm, independently of NumPy's producer.
    for position in range(sequence):
        angles = [position*math.pow(config["rope_theta"], -2*j/dimension)
                  for j in range(dimension//2)]
        values = np.asarray([f(a) for a in angles for f in (math.cos, math.sin)], dtype="<f4")
        if half:
            expected = values.astype("<f2").view("<u2")
        else:
            _, exponents = np.frexp(np.abs(values).astype("float64"))
            quantum = np.maximum(exponents-8, -133)
            rounded = np.ldexp(np.rint(np.ldexp(values.astype("float64"), -quantum)), quantum)
            expected = (rounded.astype("<f4").view("<u4") >> 16).astype("<u2")
        require(np.array_equal(words[position], expected), f"RoPE byte mismatch at {position}")
    selected = {0, min(1, sequence-1), sequence-1}
    selected.update(random.Random(211).sample(range(sequence), min(sequence, 13)))
    comparisons = 0
    with localcontext() as context:
        context.prec = 100
        theta = Decimal(str(config["rope_theta"])).ln()
        for position in sorted(selected):
            for pair in range(dimension//2):
                angle = Decimal(position)*(-Decimal(2*pair)/dimension*theta).exp()
                for part, value in enumerate(trig(angle)):
                    require(int(words[position, 2*pair+part]) == decimal_native(value, half),
                            f"high-precision RoPE mismatch at {position}/{pair}/{part}")
                    comparisons += 1
    return comparisons


def validate_image(path):
    image = json.loads(path.read_text())
    require(image["schema"] == 1 and image["kind"] == "ht2-native-ddr-image", "invalid image schema")
    mode, g = image["mode"], image["geometry"]
    require(mode in ("bf16", "fp16", "w4", "w2"), "invalid image precision")
    bindings = {binding["path"]: binding for binding in image["inputs"]}
    require(len(bindings) == len(image["inputs"]), "duplicate image input binding")
    paths = {name: validate_asset(ROOT, binding) for name, binding in bindings.items()}
    config_paths = [p for p in paths.values() if p.name == "config.json"]
    sources = [p for p in paths.values() if p.suffix == ".safetensors"]
    require(len(config_paths) == len(sources) == 1, "ambiguous checkpoint/configuration")
    config = json.loads(config_paths[0].read_text())
    entries, data_base = source_header(sources[0])
    sequence, block, group = (g[key] for key in ("MAX_SEQ_LEN", "CACHE_BLOCK", "GROUP_SIZE"))
    require(type(sequence) is int and 1 <= sequence <= min(32768, config["max_position_embeddings"]),
            "illegal sequence extent")
    require(type(group) is int and 1 <= group <= 128 and group & (group-1) == 0,
            "illegal quantization group")
    require(type(block) is int and 1 <= block <= 128 and block & (block-1) == 0,
            "illegal cache block")
    h = config["hidden_size"]
    require(config["num_attention_heads"] > 0 and h % config["num_attention_heads"] == 0,
            "invalid source attention shape")
    d = h//config["num_attention_heads"]
    actual_geometry = dict(NUM_LAYERS=config["num_hidden_layers"], HIDDEN_SIZE=h,
                           INTERMEDIATE_SIZE=config["intermediate_size"],
                           NUM_Q_HEADS=config["num_attention_heads"],
                           NUM_KV_HEADS=config["num_key_value_heads"], HEAD_DIM=d,
                           VOCAB_SIZE=config["vocab_size"], MAX_SEQ_LEN=sequence,
                           GROUP_SIZE=group, CACHE_BLOCK=block)
    require(g == actual_geometry and d % block == 0 and h % group == 0 and
            config["intermediate_size"] % group == 0, "source/image geometry mismatch")
    for name, expected in image["implementation_sha256"].items():
        require(digest(portable_path(ROOT, name)) == expected, "stale image implementation binding")
    data = validate_asset(ROOT, image["memory"])
    bank = validate_asset(ROOT, image["descriptors"]).read_bytes()
    require(len(bank) == 64*(16+16*config["num_hidden_layers"]), "descriptor bank length mismatch")
    require(data.stat().st_size == image["memory"]["bytes"], "memory extent mismatch")
    words = np.memmap(data, mode="r", dtype="uint8")
    checkpoint = np.memmap(sources[0], mode="r", dtype="uint8")
    qentries = {}
    if mode.startswith("w"):
        qmanifests = [p for p in paths.values() if p.name == "manifest.json"]
        require(len(qmanifests) == 1, "missing quantized source manifest")
        quantized = json.loads(qmanifests[0].read_text())
        require(quantized["source"] == bindings[str(sources[0].relative_to(ROOT))]
                and quantized["config"] == bindings[str(config_paths[0].relative_to(ROOT))]
                and quantized["group_size"] == group, "quantized source mismatch")
        qentries = {e["descriptor"]: e for e in quantized["tensors"] if e["bits"] == int(mode[1])}
    by_name = {p.name: p for p in paths.values()}
    regions, expected_segments, compared, rope_count = [], [], 0, 0
    expected = roles(config, sequence)
    for index in range(len(bank)//64):
        raw = bank[64*index:64*(index+1)]
        if index not in expected:
            require(raw == bytes(64), f"nonzero reserved descriptor {index}")
            continue
        # Decode by byte offsets rather than the assembler's struct format.
        fields = [int.from_bytes(raw[start:end], "little") for start, end in
                  ((0, 8), (8, 16), (16, 24), (24, 32), (32, 36), (36, 40),
                   (40, 44), (44, 48), (48, 52), (52, 56), (56, 64))]
        address, size, zero, scale, rows, columns, stride, zs, ss, flags, reserved = fields
        name, erows, ecolumns, matrix = expected[index]
        quant = matrix and mode.startswith("w")
        require((rows, columns, reserved) == (erows, ecolumns, 0),
                f"descriptor shape/reserved mismatch at {index}")
        require(flags == (0x100 if mode == "w4" else 0x103) if quant else
                flags == (0x102 if mode == "fp16" else 0x101),
                f"descriptor flags mismatch at {index}")
        if quant:
            bits = int(mode[1])
            require(index in qentries, "missing quantized tensor")
            entry = qentries[index]
            require((entry["source_tensor"], entry["rows"], entry["columns"]) ==
                    (name, rows, columns), "wrong quantized tensor")
            estride, ezs, ess = (columns*bits+7)//8, ((columns//group)*bits+7)//8, 2*(columns//group)
            require((stride, zs, ss, size) == (estride, ezs, ess, rows*estride),
                    f"metadata/row stride mismatch at {index}")
            spans = ((address, size, "payload"), (zero, rows*zs, "zeros"), (scale, rows*ss, "scales"))
        else:
            require((stride, size, zero, scale, zs, ss) ==
                    (2*columns, 2*rows*columns, 0, 0, 0, 0),
                    f"native layout mismatch at {index}")
            spans = ((address, size, "payload"),)
        for start, length, role in spans:
            end = start+length
            require(start >= 4096 and start % 64 == 0 and length > 0
                    and end <= data.stat().st_size, "payload region outside image")
            duplicate = False
            for old_start, old_end, old_index in regions:
                if start < old_end and old_start < end:
                    require((old_start, old_end, old_index, index, mode) in (
                        (start, end, 0, 1, "bf16"), (start, end, 0, 1, "fp16")) and
                            config["tie_word_embeddings"], "illegal descriptor overlap")
                    duplicate = True
            if not duplicate:
                regions.append((start, end, index))
                expected_segments.append(dict(address=start, bytes=length, descriptor=index,
                                              role=role, source_tensor=name))
            if name is None:
                rope_count += check_rope(words[start:end].view("<u2").reshape(rows, columns),
                                         config, mode == "fp16")
                compared += length
                continue
            if quant:
                span = entry[role]
                require(span["file"] in by_name and span["stride"]*rows == length,
                        "unbound/misshaped quantized span")
                origin = np.memmap(by_name[span["file"]], mode="r", dtype="uint8")
                offset = span["offset"]
            else:
                tensor = entries[name]
                require(tensor["dtype"] == "BF16" and tensor["shape"] in
                        ([rows, columns], [columns] if rows == 1 else []), "source shape mismatch")
                offset = data_base+tensor["data_offsets"][0]
                require(tensor["data_offsets"][1]-tensor["data_offsets"][0] == length,
                        "source length mismatch")
                origin = checkpoint
            require(type(offset) is int and offset >= 0 and offset+length <= origin.size,
                    "source span outside bound input")
            for delta in range(0, length, 1 << 20):
                count = min(1 << 20, length-delta)
                target = origin[offset+delta:offset+delta+count]
                if not quant:
                    native = target.view("<u2")
                    require(bool(np.all((native & 0x7f80) != 0x7f80)), "nonfinite source tensor")
                    if mode == "fp16":
                        converted = half_table()[native]
                        require(bool(np.all((converted & 0x7c00) != 0x7c00)),
                                "FP16 source conversion overflow")
                        target = converted.view("uint8")
                require(np.array_equal(words[start+delta:start+delta+count], target),
                        f"independent payload mismatch at {index}/{role}/{delta}")
                compared += count
    require(image["segments"] == expected_segments, "segment index disagrees with descriptor bank")
    cursor = 0
    for start, end, _ in sorted(regions):
        require(not np.any(words[cursor:start]), "nonzero undeclared image padding")
        cursor = end
    require(not np.any(words[cursor:]), "nonzero trailing image padding")
    require(data.stat().st_size % 64 == 0, "memory image must end on a DDR beat")
    require(len(image["configurations"]) == 12, "incomplete K/sparse/KV configuration matrix")
    seen = set()
    for item in image["configurations"]:
        kv, sparse, width = item["kv"], item["sparse"], item["k"]
        key = (kv, sparse, width)
        require(kv in ("bf16", "int8") and type(sparse) is bool and type(width) is int
                and width in (1, 2, 4) and key not in seen, "duplicate/invalid configuration")
        seen.add(key)
        record_bytes = 2*block if kv == "bf16" else block+2
        extent = (config["num_hidden_layers"]*2*config["num_key_value_heads"]*
                  (d//block)*(sequence+4)*record_bytes+63)//64*64
        base = data.stat().st_size
        require(base+extent <= 1 << 33 and (item["cache_base"], item["cache_bytes"]) ==
                (base, extent), "cache extent/pointer mismatch")
        mode_word = {"bf16": 1, "fp16": 2, "w4": 5, "w2": 9}[mode]
        mode_word += 16*int(sparse)+32*int(kv == "int8")
        require(item["ht2_mode"] == mode_word, "wrong configuration mode")
        lines = validate_asset(ROOT, item).read_text().splitlines()
        require(int(lines[0]) == len(lines)-1, "config row count mismatch")
        actual = [tuple(int(field, 16) for field in line.split()) for line in lines[1:]]
        expected_writes = [(64, mode_word), (68, width), (24, base & 0xffffffff),
                           (28, base >> 32), (32, extent & 0xffffffff), (36, extent >> 32)]
        expected_writes += [(0x1000+offset, int.from_bytes(bank[offset:offset+4], "little"))
                            for offset in range(0, len(bank), 4)]
        expected_writes.append((8, 1))
        require(actual == expected_writes, "configuration writes/publication mismatch")
    return dict(mode=mode, descriptors=len(expected), compared_payload_bytes=compared,
                decimal_rope_comparisons=rope_count, configurations=len(seen),
                memory_bytes=data.stat().st_size)


def binding(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path))


def fixture(directory):
    directory.mkdir(parents=True, exist_ok=False)
    config = dict(hidden_size=8, intermediate_size=8, num_attention_heads=1,
                  num_key_value_heads=1, num_hidden_layers=1, vocab_size=2,
                  max_position_embeddings=5, tie_word_embeddings=False,
                  hidden_act="silu", rms_norm_eps=1e-6, rope_theta=1000000.0,
                  use_sliding_window=False)
    cfg = directory / "config.json"
    cfg.write_text(json.dumps(config)+"\n")
    entries, payload, vectors = {}, bytearray(), {}
    for index, (name, rows, columns, _) in roles(config, 5).items():
        if name is None:
            continue
        values = np.zeros(rows*columns, dtype="<u2")
        if index == 0 or index in (2, 23, 24):
            values[:] = 0x3f80
        if index == 1:
            values[:8] = 0x3f80
        shape = [rows, columns] if index in (0, 1) or 16 <= index <= 22 else [columns]
        entries[name] = dict(dtype="BF16", shape=shape,
                             data_offsets=[len(payload), len(payload)+values.nbytes])
        payload.extend(values.tobytes())
        vectors[index] = values.reshape(rows, columns)
    raw = json.dumps(entries, separators=(",", ":")).encode()
    checkpoint = directory / "model.safetensors"
    checkpoint.write_bytes(len(raw).to_bytes(8, "little")+raw+payload)
    manifest = dict(checkpoint_shards=[binding(checkpoint)], assets={"config": binding(cfg)},
                    quantized_weight_inputs=[])
    quantized = dict(source=binding(checkpoint), config=binding(cfg), group_size=1, tensors=[])
    for bits in (4, 2):
        streams = {role: bytearray() for role in ("payload", "zeros", "scales")}
        for index, (name, rows, columns, matrix) in roles(config, 5).items():
            if not matrix:
                continue
            def packed(values):
                result = bytearray((len(values)*bits+7)//8)
                for n, value in enumerate(values):
                    result[n*bits//8] |= int(value) << (n*bits % 8)
                return result
            q = np.where(vectors[index] == 0x3f80, 2, 1).astype("uint8")
            parts = {"payload": packed(q.ravel()), "zeros": packed([1]*(rows*columns)),
                     "scales": b"\x80\x3f"*(rows*columns)}
            entry = dict(bits=bits, descriptor=index, source_tensor=name, rows=rows, columns=columns)
            for role, content in parts.items():
                filename = f"w{bits}-{role}.bin"
                entry[role] = dict(file=filename, offset=len(streams[role]), stride=len(content)//rows)
                streams[role].extend(content)
            quantized["tensors"].append(entry)
        for role, content in streams.items():
            path = directory / f"w{bits}-{role}.bin"
            path.write_bytes(content)
            manifest["quantized_weight_inputs"].append(binding(path))
    qmanifest = directory / "manifest.json"
    qmanifest.write_text(json.dumps(quantized)+"\n")
    manifest["quantized_weight_inputs"].insert(0, binding(qmanifest))
    return manifest


def controls(directory):
    from device_image import assemble, geometry
    directory.mkdir(parents=True, exist_ok=False)
    manifest = fixture(directory / "inputs")
    results, images, rejected = [], [], []
    for mode in ("bf16", "fp16", "w4", "w2"):
        output = directory / f"official-image-{mode}-{uuid.uuid4().hex[:8]}"
        assemble(ROOT, manifest, output, mode, 5, 1, 1)
        results.append(validate_image(output / "manifest.json"))
        images.append(str((output / "manifest.json").relative_to(ROOT)))
    original = json.loads(portable_path(ROOT, images[0]).read_text())

    def reject(label, change):
        copy = directory / f"official-image-defect-{label}-{uuid.uuid4().hex[:8]}"
        copy.mkdir()
        mutated = deepcopy(original)
        for key in ("memory", "descriptors"):
            path = copy / Path(mutated[key]["path"]).name
            shutil.copyfile(portable_path(ROOT, mutated[key]["path"]), path)
            mutated[key] = {**mutated[key], **binding(path)}
        change(mutated)
        for key in ("memory", "descriptors"):
            mutated[key]["sha256"] = digest(portable_path(ROOT, mutated[key]["path"]))
        path = copy / "manifest.json"
        path.write_text(json.dumps(mutated)+"\n")
        try:
            validate_image(path)
        except ValueError as exc:
            rejected.append(dict(defect=label, diagnostic=str(exc)))
        else:
            raise AssertionError(f"image corruption survived: {label}")

    def change_byte(image, key, offset):
        path = portable_path(ROOT, image[key]["path"])
        with path.open("r+b") as stream:
            stream.seek(offset)
            value = stream.read(1)
            stream.seek(offset)
            stream.write(bytes([value[0] ^ 1]))

    reject("weight", lambda m: change_byte(m, "memory", 4096))
    reject("descriptor-shape", lambda m: change_byte(m, "descriptors", 32))
    reject("descriptor-flags", lambda m: change_byte(m, "descriptors", 52))
    reject("reserved", lambda m: change_byte(m, "descriptors", 4*64))
    rope_address = next(s["address"] for s in original["segments"] if s["descriptor"] == 3)
    reject("rope", lambda m: change_byte(m, "memory", rope_address))
    reject("padding", lambda m: change_byte(m, "memory", 0))
    reject("cache-extent", lambda m: m["configurations"][0].update(cache_bytes=64))
    reject("mode", lambda m: m["configurations"][0].update(ht2_mode=0))
    reject("config-missing", lambda m: m["configurations"].pop())
    reject("source-digest", lambda m: m["inputs"][0].update(sha256="0"*64))
    reject("segment-map", lambda m: m["segments"][0].update(address=8192))
    for field, value in (("GROUP_SIZE", 0), ("CACHE_BLOCK", 0), ("MAX_SEQ_LEN", 0),
                         ("GROUP_SIZE", 3), ("CACHE_BLOCK", 3), ("MAX_SEQ_LEN", 6)):
        config = json.loads(validate_asset(ROOT, manifest["assets"]["config"]).read_text())
        args = dict(sequence=5, group=1, block=1)
        args[{"GROUP_SIZE": "group", "CACHE_BLOCK": "block", "MAX_SEQ_LEN": "sequence"}[field]] = value
        try:
            geometry(config, **args)
        except ValueError as exc:
            rejected.append(dict(defect=f"{field}={value}", diagnostic=str(exc)))
        else:
            raise AssertionError(f"illegal geometry survived: {field}={value}")
    require(len(rejected) == 17 and sum(r["compared_payload_bytes"] for r in results) > 0,
            "missing image comparison/sensitivity coverage")
    summary = dict(images=images, results=results, rejections=rejected,
                   scope="Synthetic byte-layout fixtures; not official model/device acceptance")
    (directory / "fixture-results.json").write_text(json.dumps(summary, indent=2)+"\n")
    return summary


def smoke(run, fixture_images):
    from verify import simulate, sources
    selected = [portable_path(ROOT, p) for p in fixture_images]
    first = json.loads(selected[0].read_text())
    bank = validate_asset(ROOT, first["descriptors"]).read_bytes()
    bank_path = run.path / "device-image-config-bank.hex"
    bank_path.write_text("".join(f"{int.from_bytes(bank[start:start+64], 'little'):0128x}\n"
                                for start in range(0, len(bank), 64)))
    config = next(c for c in first["configurations"] if
                  (c["kv"], c["sparse"], c["k"]) == ("bf16", True, 1))
    stdout = simulate(run, ROOT / "tests/device_image_config_tb.sv",
                      plusargs=["+config="+config["path"], "+bank="+run.relative(bank_path)])
    require("SUMMARY image_config descriptors=32 " in stdout, "missing Icarus descriptor readback")
    run.receipt["assembled_image_icarus_configuration"] = stdout.strip()
    run.save()
    obj = run.path / "device-image-smoke-compile-obj"
    try:
        run.tool("verilator")
        run.tool("c++")
        run.command(["verilator", "--binary", "--timing", "-Wno-fatal",
                     "--unroll-count", "1024", "--unroll-stmts", "100000",
                     "-CFLAGS", "-O2", "--top-module", "top_tb", "-GMATRIX=1",
                     "--Mdir", run.relative(obj), "-j", "2",
                     *[run.relative(p) for p in sources()], "tests/top_tb.sv"],
                    "device-image-smoke-compile")
        results = []
        for image_path in selected:
            image = json.loads(image_path.read_text())
            mode = image["mode"]
            memory = validate_asset(ROOT, image["memory"]).read_bytes()
            require(len(memory) < 131072, "compact smoke memory extent exceeded")
            hex_path = run.path / f"device-image-{mode}-smoke.hex"
            hex_path.write_text("\n".join(f"{value:02x}" for value in
                               memory+bytes(131072-len(memory)))+"\n")
            for kv in ("bf16", "int8"):
                config = next(c for c in image["configurations"] if c["kv"] == kv and
                              c["k"] == 1 and c["sparse"])
                record = b"\x80\x3f\x00"*16 if kv == "int8" else bytes(32)
                tx = run.path / f"device-image-{mode}-{kv}-transaction.txt"
                tx.write_text(f"1\n1 0 1 0 0 1 1 0 1 0 {len(record)} "
                              f"{int.from_bytes(record, 'little'):x}\n")
                plusargs = ["+image="+run.relative(hex_path), "+config="+config["path"],
                            "+transactions="+run.relative(tx)]
                _, stdout, _ = run.command([run.relative(obj / "Vtop_tb"), *plusargs],
                                           f"device-image-{mode}-{kv}-smoke")
                logits = [line.split()[2:] for line in stdout.splitlines() if
                          line.startswith("RESULT matrix ")]
                require(logits == [["0", "0", "0", "41000000"], ["0", "0", "1", "00000000"]],
                        f"independent identity logit mismatch: {logits}")
                checked = [line for line in stdout.splitlines() if
                           line.startswith("CHECKED matrix transaction=0 ")]
                require(len(checked) == 1 and checked[0].endswith(f"kv_bytes={len(record)}")
                        and "SUMMARY top " in stdout, "missing cache/transaction comparisons")
                results.append(dict(mode=mode, kv=kv, simulator="verilator",
                                    checked_logits=2, checked_kv_bytes=len(record),
                                    summary=next(s for s in stdout.splitlines() if s.startswith("SUMMARY "))))
        run.receipt["assembled_image_rtl_smokes"] = results
        run.save()
    finally:
        if obj.exists():
            shutil.rmtree(obj)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image")
    group.add_argument("--fixtures")
    args = parser.parse_args()
    result = (validate_image(portable_path(ROOT, args.image)) if args.image else
              controls(portable_path(ROOT, args.fixtures)))
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
