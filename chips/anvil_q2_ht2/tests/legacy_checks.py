"""Independent legacy descriptor/CSR transactions and integrated legacy smoke."""

import hashlib
import struct


def bank(weight_mode, base=0x1000):
    """Literal legacy layouts: BF16 rows, Q16 RoPE, 16x128 tiled projections."""
    records = [bytes(64) for _ in range(32)]
    cursor = base
    for index in (0, 1, 2, 3, *range(16, 28)):
        rows = 2 if index < 2 else 5 if index == 3 else 8 if 16 <= index <= 22 else 1
        tiled = 16 <= index <= 22
        fmt = 3 if index == 3 else 2 if weight_mode else 0 if tiled else 1
        stride = (4096 if weight_mode else 1024) if tiled else 32 if fmt == 3 else 16
        length = stride if tiled else rows * stride
        main = cursor
        cursor = (cursor + length + 63) & ~63
        zero = scale = zero_stride = scale_stride = 0
        if fmt == 0:
            zero, zero_stride = cursor, 4
            cursor = (cursor + rows * zero_stride + 63) & ~63
            scale, scale_stride = cursor, 16
            cursor = (cursor + rows * scale_stride + 63) & ~63
        records[index] = struct.pack("<QQQQIIIIIIQ", main, length, zero, scale,
                                     rows, 8, stride, zero_stride, scale_stride,
                                     0x100 | fmt, 0)
    if cursor >= 0x10000:
        raise AssertionError("compact legacy fixture overlaps cache")
    return records


def changed(record, offset, value, width=8):
    data = bytearray(record)
    data[offset:offset+width] = value.to_bytes(width, "little")
    return bytes(data)


def vectors(run):
    operations, cases = [], []

    def command(op, address=0, data=0, error=0, expected=0):
        operations.append((op, address, data, error, expected))

    def write(address, data, error=0):
        command(0, address, data, error)

    def read(address, expected):
        command(1, address, expected=expected)

    def load(records, mode, cache=0, cache_base=0x10000):
        write(0x10, mode)
        write(0x14, cache)
        write(0x18, cache_base)
        write(0x1c, 0)
        write(0x20, 4096)
        write(0x24, 0)
        for index, record in enumerate(records):
            for word, value in enumerate(struct.unpack("<16I", record)):
                write(0x1000 + index*64 + word*4, value)
        # Reverse traversal and changed request pins distinguish registered reads.
        for index in reversed(range(32)):
            for word in (15, 13, 8, 0):
                read(0x1000 + index*64 + word*4,
                     int.from_bytes(records[index][4*word:4*word+4], "little"))

    def published(mode, cache, cache_base):
        return (((((1 << 1) | mode) << 2 | cache) << 33 | cache_base) << 33) | 4096

    def inspect(records):
        for index in (31, 0, *range(1, 31)):
            command(3, index, expected=int.from_bytes(records[index], "little"))
        command(3, 32, error=1)

    original = bank(1)
    load(original, 1)
    command(2, expected=published(1, 0, 0x10000))
    inspect(original)
    cases.append("BF16 first/final COPY, all committed descriptors, initial START/APPEND ranges")

    replacement = bank(0, 0x2000)
    load(replacement, 0, cache=2, cache_base=0x11000)
    # Shadow edits may not mutate the previously published bank.
    inspect(original)
    command(2, expected=published(0, 2, 0x11000))
    inspect(replacement)
    cases.append("W4 payload/zero/scale ranges and atomic second-bank publication")

    for name, index, patch in (
        ("KV START overlap", 0, changed(replacement[0], 0, 0x11000)),
        ("main APPEND overlap", 2, changed(replacement[2], 0,
                                          int.from_bytes(replacement[0][:8], "little"))),
        ("zero APPEND overlap", 16, changed(replacement[16], 16,
                                            int.from_bytes(replacement[16][:8], "little"))),
        ("scale APPEND overlap", 16, changed(replacement[16], 24,
                                             int.from_bytes(replacement[16][16:24], "little"))),
        ("nonidentical embedding alias", 1, changed(replacement[0], 8, 48)),
        ("reserved final descriptor", 31, changed(replacement[31], 0, 64)),
    ):
        damaged = list(replacement)
        damaged[index] = patch
        load(damaged, 0, cache=2, cache_base=0x11000)
        command(2, error=1)
        inspect(replacement)
        cases.append("rejected " + name + "; previous bank retained")

    alias = bank(1)
    alias[1] = alias[0]
    load(alias, 1, cache=1)
    command(2, expected=published(1, 1, 0x10000))
    inspect(alias)
    cases.append("identical embedding/head alias accepted")

    load(original, 1)
    for delay in (1, 30):
        command(6, data=delay, error=1)
        inspect(alias)
    command(2, expected=published(1, 0, 0x10000))
    inspect(original)
    cases.append("annul after START and during descriptor validation preserves publication")

    command(5, 3)  # busy and quiescent: busy still forbids mutation.
    write(0x1000, 0xdeadbeef, 1)
    read(0x1000, int.from_bytes(original[0][:4], "little"))
    command(5, 0)  # idle but nonquiescent also forbids mutation.
    write(0x18, 0x1234, 1)
    read(0x18, 0x10000)
    command(5, 2)
    command(0, 0x1001, 9, 1)
    command(1, 0x17fc, expected=0)

    for iteration in range(2):
        command(4)
        for word in range(512):
            read(0x1000 + 4*word, 0)
        write(0x17fc, 0xabcdef01 + iteration)
        read(0x17fc, 0xabcdef01 + iteration)
        read(0x17f8, 0)
        read(0x1000, 0)
    cases.append("two asynchronous reset epochs clear word validity without resetting payload RAM")
    path = run.path / "legacy-configuration-vectors.txt"
    path.write_text(str(len(operations)) + "\n" + "\n".join(
        f"{op} {a:x} {d:x} {e:b} {x:x}" for op, a, d, e, x in operations) + "\n")
    run.receipt["legacy_configuration_vectors"] = {
        "path": run.relative(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "operations": len(operations), "cases": cases,
        "oracle": "literal descriptor byte layouts and public address/value transaction model",
    }
    run.save()
    return path


def configuration(run, root, source_paths, lowered_paths):
    vector_path = vectors(run)
    results = []
    for snapshot, paths in (("original", source_paths), ("lowered", lowered_paths)):
        for module in ("anvil_q2_ht_configuration", "anvil_q2_ht2_legacy_configuration"):
            stem = "legacy-" + snapshot + "-" + module
            binary = run.path / (stem + ".vvp")
            run.command(
                ["iverilog", "-g2012", "-Wall", "-s", "legacy_configuration_tb",
                 "-DLEGACY_CONFIGURATION=" + module, "-o", run.relative(binary),
                 *[run.relative(p) for p in paths],
                 run.relative(root / "tests/legacy_configuration_tb.sv")], stem + "-compile")
            _, stdout, _ = run.command(
                ["vvp", run.relative(binary), "+vectors=" + run.relative(vector_path)],
                stem + "-simulate", timeout=600)
            binary.unlink()
            if "SUMMARY legacy_configuration " not in stdout:
                raise AssertionError("missing legacy public-interface comparisons")
            results.append({"snapshot": snapshot, "module": module, "stdout": stdout})
    # Latency is checked at pins by the benches; the semantic transaction ledger
    # must also be identical across the immutable parent, adaptation and lowering.
    if len({item["stdout"] for item in results}) != 1:
        raise AssertionError("legacy original/lowered semantic ledgers differ")
    run.receipt["legacy_configuration_regression"] = results
    run.save()
    defects(run, root, lowered_paths, vector_path)


def defects(run, root, paths, vector_path):
    source = next(p for p in paths if p.name == "anvil_q2_ht2_legacy_configuration.sv")
    text = source.read_text()
    mutations = (
        ("shadow-read-address", "shadow[shadow_read_address]", "shadow[0]", "LEGACY_CSR"),
        ("reset-mask", "if (!rst_n) word_valid<=0;",
         "if (!rst_n) word_valid<=16'hffff;", "LEGACY_CSR"),
        ("copy-first-prefetch", "state==NEXT && index+9'd1==ENTRIES",
         "state==NEXT && index+9'd1!=ENTRIES", "LEGACY_DESCRIPTOR"),
        ("copy-final-write", "if (available && state==COPY)",
         "if (available && state==COPY && index+9'd1<ENTRIES)", "LEGACY_DESCRIPTOR"),
        ("start-range-write", "(state==START || state==APPEND)",
         "(state==APPEND)", "LEGACY_CSR"),
        ("append-range-write", "(state==START || state==APPEND)",
         "(state==START)", "LEGACY_CSR"),
        ("scan-overlap", "overlap && !identical_embedding_alias",
         "1'b0 && !identical_embedding_alias", "LEGACY_PUBLICATION"),
        ("alias-identity", "descriptor==embedding_descriptor",
         "1'b1", "LEGACY_PUBLICATION"),
        ("early-publication", "loaded<=1; active_bank<=!active_bank;",
         "loaded<=1; active_bank<=active_bank;", "LEGACY_DESCRIPTOR"),
    )
    records = []
    for name, old, new, marker in mutations:
        if text.count(old) != 1:
            raise AssertionError(f"legacy defect did not uniquely match: {name}")
        directory = run.path / ("legacy-defect-" + name)
        directory.mkdir()
        mutated = directory / source.name
        mutated.write_text(text.replace(old, new))
        binary = directory / "legacy.vvp"
        run.command(
            ["iverilog", "-g2012", "-Wall", "-s", "legacy_configuration_tb",
             "-o", run.relative(binary),
             *[run.relative(mutated if p == source else p) for p in paths],
             run.relative(root / "tests/legacy_configuration_tb.sv")],
            "legacy-defect-" + name + "-compile")
        record, stdout, stderr = run.command(
            ["vvp", run.relative(binary), "+vectors=" + run.relative(vector_path)],
            "legacy-defect-" + name + "-simulate", timeout=600, check=False)
        binary.unlink()
        if (record["exit_code"] == 0 or record["timed_out"] or
                marker not in stdout + stderr):
            raise AssertionError(f"legacy defect missed intended comparison: {name}; {stdout}{stderr}")
        records.append({"defect": name, "assertion": marker,
                        "exit_code": record["exit_code"],
                        "source_sha256": hashlib.sha256(mutated.read_bytes()).hexdigest()})
    run.receipt["legacy_configuration_defects"] = records
    run.save()


def integration_fixture(run):
    records = bank(1)
    memory = bytearray(131072)
    for index, record in enumerate(records):
        if record == bytes(64):
            continue
        address, length = struct.unpack_from("<QQ", record)
        # Nonzero embedding/gamma and real zero projection/head data exercise
        # inference; every vocabulary result is exactly zero independently.
        if index in (0, 2, 23, 24):
            memory[address:address+length] = b"\x80\x3f" * (length//2)
        if index == 3:
            memory[address:address+length] = (b"\x00\x00\x01\x00" + bytes(4)) * (length//8)
    directory = run.path / "checkpoint-images"
    directory.mkdir(exist_ok=True)
    image = directory / "legacy-identity.hex"
    image.write_text("\n".join(f"{byte:02x}" for byte in memory) + "\n")
    writes = [(0x40, 0), (0x10, 1), (0x14, 0), (0x18, 0x10000),
              (0x1c, 0), (0x20, 4096), (0x24, 0)]
    for index, record in enumerate(records):
        writes.extend((0x1000 + 64*index + 4*word, value)
                      for word, value in enumerate(struct.unpack("<16I", record)))
    config = run.path / "legacy-integration-config.txt"
    config.write_text(str(len(writes)) + "\n" + "\n".join(
        f"{a:04x} {d:08x}" for a, d in writes) + "\n")
    return image, config


def integration(run, root, source_paths, lowered_paths):
    import shutil
    image, config = integration_fixture(run)
    run.tool("verilator")
    run.tool("c++")
    results = []
    for snapshot, paths in (("original", source_paths), ("lowered", lowered_paths)):
        obj = run.path / ("legacy-integration-" + snapshot + "-compile-obj")
        try:
            run.command(
                ["verilator", "--binary", "--timing", "-Wno-fatal", "--top-module", "top_tb",
                 "-GLEGACY=1", "-O2", "--Mdir", run.relative(obj), "-j", "2",
                 *[run.relative(p) for p in paths], run.relative(root / "tests/top_tb.sv")],
                "legacy-integration-" + snapshot + "-compile")
            _, stdout, _ = run.command(
                [run.relative(obj / "Vtop_tb"), "+image=" + run.relative(image),
                 "+config=" + run.relative(config)], "legacy-integration-" + snapshot)
            summary = next((line for line in stdout.splitlines()
                            if line.startswith("SUMMARY legacy_integration ")), None)
            if summary is None:
                raise AssertionError("missing actual legacy-mode inference comparisons")
            results.append({"snapshot": snapshot, "summary": summary})
        finally:
            if obj.exists():
                shutil.rmtree(obj)
    if results[0]["summary"] != results[1]["summary"]:
        raise AssertionError("original/lowered legacy inference results differ")
    run.receipt["legacy_integration_regression"] = results
    run.save()


def main():
    import argparse
    import sys
    from verify import ROOT, Run, sources
    from synthesis import expand_packages
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--section", choices=("configuration", "integration", "all"), default="all")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    run = Run("legacy-regression", preparation=True, repair_of=args.repair_of)
    run.receipt["argv"] = ["python3", "tests/legacy_checks.py", *sys.argv[1:]]
    run.save()
    try:
        run.tool("python3")
        paths = sources()
        lowered = expand_packages(run, ROOT, paths)
        if args.section in ("configuration", "all"):
            run.tool("iverilog")
            run.tool("vvp")
            configuration(run, ROOT, paths, lowered)
        if args.section in ("integration", "all"):
            integration(run, ROOT, paths, lowered)
    except Exception as exc:
        return run.finish(False, f"{type(exc).__name__}: {exc}")
    return run.finish(True, "bounded legacy regression passed")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
