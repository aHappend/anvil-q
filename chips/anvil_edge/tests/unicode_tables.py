"""Independent, offline Unicode conversion from provenance-pinned source releases.

The published tokenizers crate lock identifies a reproducible *candidate* source
graph, not an installed wheel. Regex Unicode 16 and normalization Unicode 9 are
kept distinct. No ANVLEDG3 profile metadata or bootable image is produced.
"""

from bisect import bisect_right
import copy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import re
import struct
import sys
import tomllib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from official import ROOT
from qwen_regex import (
    SYMBOLS, LETTERS, NUMBER, SPACE, CR, LF, WHITE, QUOTE, OTHER,
    compile_profile, rule_oracle, serialize, table_oracle,
)
from qwen_tables import table
from unicode_sources import CRATES, members


LIMIT = 0x110000
SCALAR_COUNT = LIMIT - 0x800
SCOPE = (
    "Offline candidate dependency source-to-table conversion and public-interface "
    "component comparisons; not executed official tokenizers, a bootable image, "
    "official-profile equivalence, or model inference"
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def scalar(value):
    return 0 <= value < LIMIT and not 0xD800 <= value < 0xE000


def inputs():
    manifest = json.loads((ROOT / "tests/data/unicode-provenance.json").read_bytes())
    result = {}
    for row in manifest["sources"]:
        name = row["file"]
        require(Path(name).name == name and name not in result, "Invalid Unicode input name")
        raw = (ROOT / "tests/data" / name).read_bytes()
        require(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"],
                f"Pinned Unicode input changed: {name}")
        result[name] = raw
    require(len(result) == 13, "Incomplete Unicode source intake")
    release = members(result["tokenizers-0.21.4.crate"], "tokenizers", "0.21.4")
    lock = tomllib.loads(release["Cargo.lock"].decode())
    packages = {row["name"]: row for row in lock["package"]
                if row["name"] in ("tokenizers", "onig", "onig_sys",
                                   "unicode-normalization-alignments")}
    require(packages["tokenizers"]["version"] == "0.21.4" and
            packages["onig"]["version"] == "6.5.1" and
            packages["onig"]["checksum"] ==
            "336b9c63443aceef14bea841b899035ae3abe89b7c486aaf4c5bd8aafedac3f0",
            "Published release dependency identity changed")
    for name, version, checksum in CRATES:
        require(packages[name]["version"] == version and
                packages[name]["checksum"] == checksum, "Published release lock mismatch")
    require(hashlib.sha256(result["onig-6.5.1.crate"]).hexdigest() ==
            packages["onig"]["checksum"], "Onig wrapper differs from the published release lock")
    wrapper = members(result["onig-6.5.1.crate"], "onig", "6.5.1")
    require("RegexOptions::REGEX_OPTION_NONE,\n            Syntax::default()," in
            wrapper["src/lib.rs"].decode() and
            "onig_sys::OnigDefaultSyntax" in wrapper["src/syntax.rs"].decode(),
            "Candidate regex default option/syntax path changed")
    require("Regex::new(regex_str)?" in release["src/utils/onig.rs"].decode(),
            "Published tokenizer release does not use the inspected regex path")
    return result, packages


def without_comments(source):
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)


def numbers(source):
    tokens = re.findall(r"0[xX][0-9a-fA-F]+|\d+", source)
    remainder = re.sub(r"0[xX][0-9a-fA-F]+|\d+|[\s,]", "", source)
    require(not remainder, f"Unparsed numeric table text: {remainder[:80]}")
    return [int(value, 16 if value.lower().startswith("0x") else 10) for value in tokens]


def rust_array(source, name):
    match = re.search(r"\bconst " + re.escape(name) + r":[^\n]* = &\[(.*?)\n\];",
                      source, re.DOTALL)
    require(match is not None, f"Missing source array {name}")
    return match[1]


def rust_decompositions(source, name):
    body = rust_array(source, name)
    # Rust Unicode escapes are data; never evaluate source code.
    expression = r"\((0x[0-9a-fA-F]+), &\[((?:'\\u\{[0-9a-fA-F]+\}',? *)*)\]\),"
    result = {}
    for match in re.finditer(expression, body):
        key = int(match[1], 16)
        values = tuple(int(value, 16) for value in re.findall(r"\\u\{([0-9a-fA-F]+)\}", match[2]))
        if key == 0 and not values:
            continue
        require(scalar(key) and values and all(map(scalar, values)) and key not in result,
                f"Invalid/duplicate source decomposition in {name}")
        result[key] = values
    require(not re.sub(expression, "", body).strip(), f"Unparsed Rust decomposition {name}")
    return result


def normalization_source(archive):
    source = archive["src/tables.rs"].decode()
    require("pub const UNICODE_VERSION: (u64, u64, u64) = (9, 0, 0);" in source,
            "Candidate normalization version changed")
    ccc = bytearray(LIMIT)
    seen = set()
    for packed in numbers(rust_array(source, "CANONICAL_COMBINING_CLASS_KV")):
        if packed == 0:
            continue
        key, value = packed >> 8, packed & 255
        require(scalar(key) and key not in seen and value != 0, "Invalid source CCC key")
        seen.add(key)
        ccc[key] = value
    canonical = rust_decompositions(source, "CANONICAL_DECOMPOSED_KV")
    compatible = rust_decompositions(source, "COMPATIBILITY_DECOMPOSED_KV")
    body = rust_array(source, "COMPOSITION_TABLE_KV")
    expression = r"\((0x[0-9a-fA-F]+), '\\u\{([0-9a-fA-F]+)\}'\),"
    compositions = {}
    for match in re.finditer(expression, body):
        packed, value = int(match[1], 16), int(match[2], 16)
        key = (packed >> 16, packed & 65535)
        if packed == 0 and value == 0:
            continue
        require(all(map(scalar, (*key, value))) and key not in compositions,
                "Invalid source composition pair")
        compositions[key] = value
    require(not re.sub(expression, "", body).strip(), "Unparsed Rust composition array")
    astral = source.split("fn composition_table_astral", 1)[1].split("\n}", 1)[0]
    for first, second, value in re.findall(
            r"\('\\u\{([0-9a-fA-F]+)\}', '\\u\{([0-9a-fA-F]+)\}'\)"
            r" => Some\('\\u\{([0-9a-fA-F]+)\}'\)", astral):
        key, value = (int(first, 16), int(second, 16)), int(value, 16)
        require(key not in compositions and max(key) >= 65536, "Invalid astral composition")
        compositions[key] = value
    require(len(compositions) > 900 and len(canonical) > 2000 and len(compatible) > 3000,
            "Incomplete normalization source parsing")
    return ccc, canonical, compatible, compositions


def property_ranges(source, name):
    match = re.search(r"\bCR_" + re.escape(name) + r"\[\] = \{(.*?)\};", source, re.DOTALL)
    require(match is not None, f"Missing Oniguruma property {name}")
    values = numbers(without_comments(match[1]))
    count, *coordinates = values
    require(len(coordinates) == 2 * count, f"Wrong source property count {name}")
    result = list(zip(coordinates[::2], coordinates[1::2]))
    previous = -1
    for first, last in result:
        require(previous < first <= last < LIMIT, f"Unordered property range {name}")
        previous = last
    return result


def folded_source(source):
    result = {}
    for width in (1, 2, 3):
        match = re.search(rf"\bOnigUnicodeFolds{width}\[\] = \{{(.*?)\}};", source, re.DOTALL)
        require(match is not None, "Missing source case-fold table")
        body = re.sub(r"(?m)^#define .*", "", without_comments(match[1]))
        values, cursor = numbers(body), 0
        while cursor < len(values):
            folded = tuple(values[cursor:cursor + width])
            count = values[cursor + width]
            cursor += width + 1
            require(count > 0 and cursor + count <= len(values), "Malformed source unfolding")
            for value in values[cursor:cursor + count]:
                require(value not in result and all(map(scalar, (*folded, value))),
                        "Invalid/duplicate case-fold source")
                result[value] = folded
            cursor += count
        require(cursor == len(values), "Unconsumed source case-fold records")
    return result


def primary_ucd(raw):
    """Parse primary UnicodeData, independently of generated hash/range tables."""
    categories, ccc, decomposition = bytearray(LIMIT), bytearray(LIMIT), {}
    pending = None
    previous = -1
    for line in raw.decode().splitlines():
        fields = line.split(";")
        require(len(fields) == 15, "Malformed primary UnicodeData record")
        value = int(fields[0], 16)
        require(previous < value < LIMIT, "Unordered UnicodeData record")
        previous = value
        category = (4 if fields[2] == "Pc" else
                    {"L": 1, "N": 2, "M": 3}.get(fields[2][0], 0))
        cls = int(fields[3])
        first = value
        if fields[1].endswith(", First>"):
            require(pending is None and not fields[5], "Invalid UnicodeData range start")
            pending = (value, fields[1].replace(", First>", ""), category, cls)
            continue
        if fields[1].endswith(", Last>"):
            require(pending is not None and
                    pending[1:] == (fields[1].replace(", Last>", ""), category, cls),
                    "Invalid UnicodeData range end")
            first = pending[0]
            pending = None
        else:
            require(pending is None, "Unclosed UnicodeData range")
        categories[first:value + 1] = bytes([category]) * (value - first + 1)
        ccc[first:value + 1] = bytes([cls]) * (value - first + 1)
        if fields[5]:
            parts = fields[5].split()
            compatibility = parts[0].startswith("<")
            sequence = tuple(int(part, 16) for part in parts[int(compatibility):])
            require(sequence and all(map(scalar, sequence)), "Invalid UnicodeData decomposition")
            decomposition[value] = (compatibility, sequence)
    require(pending is None, "Unclosed final UnicodeData range")
    return categories, ccc, decomposition


def hangul(value):
    index = value - 0xAC00
    if 0 <= index < 11172:
        result = (0x1100 + index // 588, 0x1161 + index % 588 // 28)
        return result + ((0x11A7 + index % 28,) if index % 28 else ())
    return None


def primary_expander(decompositions):
    @lru_cache(maxsize=None)
    def expand(value, compatibility):
        algorithmic = hangul(value)
        if algorithmic is not None:
            return algorithmic
        row = decompositions.get(value)
        if row is None or (row[0] and not compatibility):
            return (value,)
        return tuple(part for nested in row[1] for part in expand(nested, compatibility))
    return expand


def primary_compositions(raw, ccc, decompositions):
    exclusions = set()
    for line in raw.decode().splitlines():
        value = line.split("#", 1)[0].strip()
        if value:
            exclusions.add(int(value, 16))
    return {tuple(sequence): value for value, (compatibility, sequence) in decompositions.items()
            if not compatibility and len(sequence) == 2 and value not in exclusions
            and ccc[sequence[0]] == 0}


def full_casefold(raw):
    result = {}
    for line in raw.decode().splitlines():
        fields = line.split("#", 1)[0].strip().split(";")
        if len(fields) == 1:
            continue
        require(len(fields) == 4, "Malformed primary case-fold data")
        value, status = int(fields[0], 16), fields[1].strip()
        if status in ("C", "F"):
            require(value not in result, "Duplicate primary case-fold mapping")
            result[value] = tuple(int(part, 16) for part in fields[2].split())
    return result


def primary_whitespace(raw):
    result = bytearray(LIMIT)
    for line in raw.decode().splitlines():
        content = line.split("#", 1)[0].strip()
        if not content:
            continue
        interval, name = map(str.strip, content.split(";"))
        if name != "White_Space":
            continue
        values = interval.split("..")
        first, last = int(values[0], 16), int(values[-1], 16)
        result[first:last + 1] = b"\1" * (last - first + 1)
    return result


def compose_hangul(first, second):
    if 0x1100 <= first <= 0x1112 and 0x1161 <= second <= 0x1175:
        return 0xAC00 + (first - 0x1100) * 588 + (second - 0x1161) * 28
    if 0xAC00 <= first < 0xD7A4 and (first - 0xAC00) % 28 == 0 and 0x11A8 <= second <= 0x11C2:
        return first + second - 0x11A7
    return None


def normalize(values, mode, ccc, canonical, compatible, compositions):
    """UAX #15 reference on source maps, not an RTL state-machine translation."""
    if mode == 0:
        return list(values)
    expanded = []
    for value in values:
        sequence = hangul(value)
        if sequence is None:
            sequence = ((compatible.get(value) if mode in (2, 4) else None)
                        or canonical.get(value) or (value,))
        for item in sequence:
            position, cls = len(expanded), ccc[item]
            while cls and position and ccc[expanded[position - 1]] > cls:
                position -= 1
            expanded.insert(position, item)
    if mode in (3, 4):
        return expanded
    result, starter, previous_class = [], None, 0
    for item in expanded:
        cls = ccc[item]
        composite = None
        if starter is not None and (previous_class == 0 or previous_class < cls):
            composite = compose_hangul(result[starter], item)
            if composite is None:
                composite = compositions.get((result[starter], item))
        if composite is not None:
            result[starter] = composite
        else:
            if cls == 0:
                starter = len(result)
            result.append(item)
            previous_class = cls
    return result


class Converted:
    def __init__(self):
        raw, self.packages = inputs()
        self.raw = raw
        norm = members(raw["unicode-normalization-alignments-0.1.12.crate"],
                       "unicode-normalization-alignments", "0.1.12")
        onig = members(raw["onig_sys-69.9.1.crate"], "onig_sys", "69.9.1")
        self.ccc, self.canonical, self.compatible, self.compositions = normalization_source(norm)
        source = onig["oniguruma/src/unicode_property_data.c"].decode()
        self.categories, self.whitespace = bytearray(LIMIT), bytearray(LIMIT)
        for name, category in (("L", 1), ("N", 2), ("M", 3), ("Pc", 4)):
            for first, last in property_ranges(source, name):
                require(not any(self.categories[first:last + 1]), "Overlapping major properties")
                self.categories[first:last + 1] = bytes([category]) * (last - first + 1)
        require("#define CR_White_Space CR_Space" in source, "Whitespace alias changed")
        for first, last in property_ranges(source, "Space"):
            self.whitespace[first:last + 1] = b"\1" * (last - first + 1)
        self.folding = folded_source(onig["oniguruma/src/unicode_fold_data.c"].decode())
        self.classification_audit()
        self.normalization_audit()
        self.ranges = self.convert_ranges()
        self.range_starts = [row[0] for row in self.ranges]
        self.profile = compile_profile()
        self.blobs = self.serialize()
        self.roundtrip_audit()
        self.source_locations = {
            "normalization": {
                "archive": "tests/data/unicode-normalization-alignments-0.1.12.crate",
                "member": "src/tables.rs",
                "version_line": next(i for i, line in enumerate(norm["src/tables.rs"].decode().splitlines(), 1)
                                     if "pub const UNICODE_VERSION" in line),
                "lookup_member": "src/lookups.rs",
                "algorithm_member": "src/normalize.rs",
            },
            "regex": {
                "archive": "tests/data/onig_sys-69.9.1.crate",
                "member": "oniguruma/src/unicode_property_data.c",
                "letter_range_line": source[:source.index(
                    "0x1c80, 0x1c8a", source.index("CR_L[]"))].count("\n") + 1,
                "fold_member": "oniguruma/src/unicode_fold_data.c",
                "fold_algorithm_member": "oniguruma/src/unicode.c",
            },
        }

    def classification_audit(self):
        primary, _, _ = primary_ucd(self.raw["ucd-16.0.0-UnicodeData.txt"])
        whitespace = primary_whitespace(self.raw["ucd-16.0.0-PropList.txt"])
        require(self.categories == primary, "Generated Oniguruma categories differ from primary UCD16")
        require(self.whitespace == whitespace, "Generated whitespace differs from primary UCD16")
        require(self.folding == full_casefold(self.raw["ucd-16.0.0-CaseFolding.txt"]),
                "Generated Oniguruma full case folds differ from primary UCD16")
        # No contraction literal can consume a multiple-codepoint fold here.
        suffixes = tuple(tuple(map(ord, suffix)) for suffix in ("s", "t", "re", "ve", "m", "ll", "d"))
        require(not any(len(fold) > 1 and any(
            fold == suffix[start:start + len(fold)] for suffix in suffixes
            for start in range(len(suffix))) for fold in self.folding.values()),
            "Ordered-regex compiler needs multi-scalar literal-fold expansion")
        require(self.folding[0x017F] == (ord("s"),), "Missing long-s contraction witness")

    def normalization_audit(self):
        _, ccc, raw = primary_ucd(self.raw["ucd-9.0.0-UnicodeData.txt"])
        require(self.ccc == ccc, "Generated CCC differs from primary UCD9")
        expand = primary_expander(raw)
        canonical = {value: expand(value, False) for value, (compat, _) in raw.items() if not compat}
        compatible = {value: expand(value, True) for value in raw
                      if expand(value, True) != canonical.get(value)}
        require(self.canonical == canonical, "Canonical source expansions differ from primary UCD9")
        require(self.compatible == compatible, "Compatibility source expansions differ from primary UCD9")
        require(self.compositions == primary_compositions(
            self.raw["ucd-9.0.0-CompositionExclusions.txt"], ccc, raw),
            "Source composition pairs/exclusions differ from primary UCD9")
        self.normalization_vectors = 0
        self.normalization_comparisons = 0
        for line in self.raw["ucd-9.0.0-NormalizationTest.txt"].decode().splitlines():
            content = line.split("#", 1)[0].strip()
            if not content or content.startswith("@"):
                continue
            fields = content.split(";")
            require(len(fields) == 6 and not fields[-1].strip(), "Malformed normalization test row")
            values = [tuple(int(value, 16) for value in field.split()) for field in fields[:5]]
            # The twenty UAX #15 conformance identities for each published row.
            for mode, targets in ((1, (1, 1, 1, 3, 3)), (2, (3, 3, 3, 3, 3)),
                                  (3, (2, 2, 2, 4, 4)), (4, (4, 4, 4, 4, 4))):
                for given, target in zip(values, targets):
                    require(tuple(self.normalize(given, mode)) == values[target],
                            f"UCD9 normalization identity mismatch row={self.normalization_vectors} mode={mode}")
                    self.normalization_comparisons += 1
            self.normalization_vectors += 1
        require(self.normalization_vectors > 18000 and
                self.normalization_comparisons == self.normalization_vectors * 20,
                "Incomplete primary normalization conformance coverage")

    def symbol(self, value):
        folded = self.folding.get(value, (value,))
        if len(folded) == 1 and chr(folded[0]) in SYMBOLS[:8]:
            require(self.categories[value] == 1, "Literal-fold class is not a letter")
            return SYMBOLS.index(chr(folded[0]))
        if self.categories[value] == 1:
            return SYMBOLS.index("letter")
        if self.categories[value] == 2:
            return NUMBER
        return {32: SPACE, 13: CR, 10: LF, 39: QUOTE}.get(
            value, WHITE if self.whitespace[value] else OTHER)

    def normalize(self, values, mode=1):
        return normalize(values, mode, self.ccc, self.canonical, self.compatible, self.compositions)

    def convert_ranges(self):
        ranges = []
        for begin, end in ((0, 0xD800), (0xE000, LIMIT)):
            start, previous = begin, None
            for value in range(begin, end):
                properties = (self.ccc[value] | self.whitespace[value] << 8 |
                              int(self.categories[value] in (1, 2, 3, 4)) << 9)
                current = (self.symbol(value), properties)
                if previous is not None and current != previous:
                    ranges.append((start, value - 1, *previous))
                    start = value
                previous = current
            ranges.append((start, end - 1, *previous))
        require(sum(last - first + 1 for first, last, _, _ in ranges) == SCALAR_COUNT,
                "Converted ranges do not cover every Unicode scalar exactly")
        return ranges

    def serialize(self):
        blobs = serialize(self.profile)
        blobs[0x207] = table(16, b"".join(struct.pack("<4I", *row) for row in self.ranges))
        # NFC/NFD tables: compatibility expansions must not replace canonical data.
        pool, records = [], []
        for value, expansion in sorted(self.canonical.items()):
            records.append((value, len(pool), len(expansion), 0))
            pool.extend(expansion)
        self.decompositions, self.pool = records, pool
        blobs[0x20D] = table(16, b"".join(struct.pack("<4I", *row) for row in records))
        blobs[0x20E] = table(4, b"".join(struct.pack("<I", value) for value in pool))
        blobs[0x20F] = table(16, b"".join(struct.pack("<4I", *key, value, 0)
                                        for key, value in sorted(self.compositions.items())))
        return blobs

    def roundtrip_audit(self):
        for kind, blob in self.blobs.items():
            magic, version, width, count, size, reserved = struct.unpack_from("<4I2Q", blob)
            require(magic == 0x334C4254 and version == 1 and reserved == 0 and
                    size == count * width and len(blob) == 32 + size,
                    f"Malformed serialized table {kind:x}")
        ranges = list(struct.iter_unpack("<4I", self.blobs[0x207][32:]))
        require(ranges == self.ranges, "Serialized range values differ")
        canonical = {}
        pool = tuple(value for value, in struct.iter_unpack("<I", self.blobs[0x20E][32:]))
        for value, offset, length, flags in struct.iter_unpack("<4I", self.blobs[0x20D][32:]):
            require(flags == 0 and length and offset + length <= len(pool),
                    "Serialized canonical interval invalid")
            canonical[value] = pool[offset:offset + length]
        require(canonical == self.canonical, "Serialized canonical expansions differ")
        compositions = {}
        for first, second, value, reserved in struct.iter_unpack("<4I", self.blobs[0x20F][32:]):
            require(reserved == 0 and (first, second) not in compositions,
                    "Serialized composition reserved field/unique key violation")
            compositions[first, second] = value
        require(compositions == self.compositions, "Serialized composition pairs differ")
        self.scalar_comparisons = 0
        for value in range(LIMIT):
            if scalar(value):
                row = ranges[bisect_right(self.range_starts, value) - 1]
                expected = (self.symbol(value), self.ccc[value] | self.whitespace[value] << 8 |
                            int(self.categories[value] in (1, 2, 3, 4)) << 9)
                require(row[0] <= value <= row[1] and row[2:] == expected,
                        f"Serialized scalar classification mismatch U+{value:04X}")
                self.scalar_comparisons += 1
        require(self.scalar_comparisons == SCALAR_COUNT, "Missing scalar comparisons")

    def version_witnesses(self):
        _, newer_ccc, newer = primary_ucd(self.raw["ucd-16.0.0-UnicodeData.txt"])
        expand = primary_expander(newer)
        newer_canonical = {value: expand(value, False) for value, (compat, _) in newer.items()
                           if not compat}
        newer_compositions = primary_compositions(
            self.raw["ucd-16.0.0-CompositionExclusions.txt"], newer_ccc, newer)
        pair = (0x11935, 0x11930)
        newer_nfc = normalize(pair, 1, newer_ccc, newer_canonical, {}, newer_compositions)
        require(self.normalize(pair) == list(pair) and
                newer[0x11938] == (False, pair) and expand(0x11938, False) == pair and
                newer_ccc[pair[0]] == 0 and newer_ccc[pair[1]] == 0 and
                0x11938 not in self.canonical and pair not in self.compositions,
                "Missing concrete normalization-version witness")
        require(newer_nfc == [0x11938], "Primary Unicode16 NFC witness did not compose")
        old_categories, _, _ = primary_ucd(self.raw["ucd-9.0.0-UnicodeData.txt"])
        require(old_categories[0x1C89] == 0 and self.categories[0x1C89] == 1,
                "Missing concrete classification-version witness")
        return {
            "classification": {
                "scalar": "U+1C89", "unicode9": "Cn / not Letter",
                "candidate_oniguruma_and_ucd16": "Lu / Letter",
                "ucd16_source_line": next(
                    line for line in self.raw["ucd-16.0.0-UnicodeData.txt"].decode().splitlines()
                    if line.startswith("1C89;")),
            },
            "normalization": {
                "input_scalars": list(pair), "candidate_unicode9_nfc": list(pair),
                "ucd16_nfc": newer_nfc,
                "ucd16_source_line": next(
                    line for line in self.raw["ucd-16.0.0-UnicodeData.txt"].decode().splitlines()
                    if line.startswith("11938;")),
                "ucd16_composition_exclusion": False,
            },
            "conclusion": (
                "These pinned candidate dependencies have demonstrably different scalar semantics. "
                "No single-version profile is emitted. This does not identify an executed official build; "
                "official build identity and exact single-version representability remain acceptance blockers."
            ),
        }

    def report(self):
        return {
            "scope": SCOPE,
            "release_lock_packages": self.packages,
            "official_build_identity": "unconfirmed; no official tokenizer library executed",
            "official_reference_comparisons": 0,
            "regex_unicode_version": [16, 0, 0],
            "normalization_unicode_version": [9, 0, 0],
            "metadata_emitted": False, "bootable_image": False,
            "normalization_table_modes": ["NFC", "NFD"],
            "scalar_comparisons": self.scalar_comparisons,
            "normalization_conformance_rows": self.normalization_vectors,
            "normalization_conformance_comparisons": self.normalization_comparisons,
            "casefold_mappings": len(self.folding),
            "range_records": len(self.ranges),
            "decomposition_records": len(self.decompositions),
            "scalar_pool_records": len(self.pool),
            "composition_records": len(self.compositions),
            "literal_long_s_class": self.symbol(0x017F),
            "source_locations": self.source_locations,
            "version_witnesses": self.version_witnesses(),
            "table_hashes": {f"{kind:03x}": hashlib.sha256(blob).hexdigest()
                             for kind, blob in self.blobs.items()},
            "missing": [
                "Executed official tokenizer build and complete official token vectors",
                "Independently reviewed resolution of single-version metadata versus candidate dependencies",
                "Complete official-profile boot/image integrations for all three families",
                "Real weighted default-geometry benchmarks and native timing/physical-board acceptance",
            ],
        }


def audit(directory):
    converted = Converted()
    for kind, blob in converted.blobs.items():
        with (directory / f"candidate-unicode-{kind:03x}.bin").open("xb") as output:
            output.write(blob)
    with (directory / "unicode-conversion.json").open("x", encoding="ascii") as output:
        json.dump(converted.report(), output, indent=2)
        output.write("\n")
    print(json.dumps(converted.report(), indent=2))


def run_unicode_conversion(evidence):
    evidence.tools(("python3",))
    evidence.child(["python3", "tests/unicode_tables.py", evidence.relative(evidence.path)],
                   "offline-source-to-table-audit")


def memory_tables(converted, mapping):
    return {base + offset: int.from_bytes(converted.blobs[kind][offset:offset + 4], "little")
            for kind, base in mapping for offset in range(32, len(converted.blobs[kind]), 4)}


NORMALIZATION_TEXT = (
    "e\u0301 a\u0315\u0300 \u0344 A\u030a\u0301 "
    "\u1100\u1161\u11a8 \uac01 \u1100\u1161\u11a7 "
    "\U00011099\U000110ba \U0001d15e \U0001f600 "
    "\U00011935\U00011930 \U0001e030"
)


def normalizer_rtl(evidence, converted, seed, mode, text=NORMALIZATION_TEXT, suffix=""):
    from text import run_text_case
    memory = memory_tables(converted, (
        (0x207, 0x1000), (0x20D, 0x10000), (0x20E, 0x20000), (0x20F, 0x30000)))
    given = list(map(ord, text))
    expected = converted.normalize(given, mode)
    if text == NORMALIZATION_TEXT:
        require(expected != given and 0x1F600 in expected and 0x11935 in expected and
                0x11930 in expected and 0x1E030 in expected,
                "Required normalization-version/supplementary witnesses absent")
    else:
        require(text == "e\u0301" and expected == [0xE9], "Invalid compact portability fixture")
    dut = f"""
  wire [31:0] normalized_scalar;
  assign out_value={{32'd0,normalized_scalar}};
  anvil_edge_normalizer #(.MAX_SCALARS(256)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.config_valid(1'b1),
    .cfg_normalization(32'd{mode}),.cfg_ranges_base(64'h1000),
    .cfg_decomposition_base(64'h10000),.cfg_scalar_pool_base(64'h20000),
    .cfg_composition_base(64'h30000),.cfg_range_count(32'd{len(converted.ranges)}),
    .cfg_class_count(32'd{len(SYMBOLS)}),
    .cfg_decomposition_count(32'd{len(converted.decompositions)}),
    .cfg_scalar_pool_count(32'd{len(converted.pool)}),
    .cfg_composition_count(32'd{len(converted.compositions)}),
    .in_valid(in_valid),.in_ready(in_ready),.in_scalar(in_value),.in_last(in_last),
    .out_valid(out_valid),.out_ready(out_ready),.out_scalar(normalized_scalar),
    .out_last(out_last),.busy(busy),.done(done),.error(error),.error_code(error_code),
    .tbl_req_valid(tbl_req_valid),.tbl_req_ready(tbl_req_ready),.tbl_req_addr(tbl_req_addr),
    .tbl_rsp_valid(tbl_rsp_valid),.tbl_rsp_ready(tbl_rsp_ready),
    .tbl_rsp_data(tbl_rsp_data),.tbl_rsp_error(tbl_rsp_error));
"""
    run_text_case(evidence, f"source-unicode9-normalizer-m{mode}{suffix}", seed, dut, memory,
                  given, expected, provenance={
                      "scope": SCOPE, "reference": "Pinned upstream source maps, UCD9-conformance checked",
                      "normalization_unicode_version": [9, 0, 0],
                      "full_tables": True, "mode": mode,
                      "input_utf8_hex": text.encode().hex(),
                  })


def regex_text(converted):
    selected = sorted({value for index, row in enumerate(converted.ranges)
                       if index % 37 == 0 for value in row[:2]}
                      | {0, 0x10FFFF, 0x1C89, 0x1C8A, 0x11935, 0x11930,
                         0x1E030, 0x1E4D0, 0x1E4EC, 0x1F600, 0x0301})
    return (
        "I'm WE'RE she'd can't we'll you've '\u017f 'S 'T 'RE 'VE 'M 'LL 'D "
        "\u00df \ufb05 \ufb06 '\u017fT 'sT 123 \u0661\u0662 \u4e2d\u6587 "
        "e\u0301 \U0001f600 \U00011935\U00011930  a  ! \t x \r\n"
        + " ".join(map(chr, selected)) + "\r\n\t\u00a0  "
    )


def regex_spans(converted, text):
    symbols = [converted.symbol(ord(char)) for char in text]
    widths = [len(char.encode()) for char in text]
    offsets = [0]
    for width in widths:
        offsets.append(offsets[-1] + width)
    expected = [(offsets[first], offsets[end]) for first, end in rule_oracle(symbols)]
    require(expected == table_oracle(symbols, converted.profile, widths),
            "Full-classifier ordered-regex expectation differs from serialized semantics")
    return expected


def regex_rtl(evidence, converted, seed):
    from text import run_text_case
    profile = converted.profile
    memory = memory_tables(converted, (
        (0x207, 0x1000), (0x208, 0x40000), (0x209, 0x50000),
        (0x20B, 0x60000), (0x20C, 0x70000)))
    text = regex_text(converted)
    expected = regex_spans(converted, text)
    require(len(text.encode()) < 4096 and len(expected) > 100 and
            converted.symbol(0x017F) == SYMBOLS.index("s") and
            converted.symbol(0x1C89) in LETTERS, "Incomplete Unicode regex witnesses")
    dut = f"""
  wire [31:0] span_start,span_end;
  assign out_value={{span_start,span_end}};
  anvil_edge_tagged_dfa #(.MAX_SPAN_BYTES(4096)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.config_valid(1'b1),
    .cfg_ranges_base(64'h1000),.cfg_states_base(64'h40000),
    .cfg_transitions_base(64'h50000),.cfg_tag_ops_base(64'h60000),
    .cfg_accepts_base(64'h70000),.cfg_range_count(32'd{len(converted.ranges)}),
    .cfg_class_count(32'd{profile['classes']}),.cfg_state_count(32'd{len(profile['states'])}),
    .cfg_transition_count(32'd{len(profile['transitions'])}),
    .cfg_tag_op_count(32'd{len(profile['ops'])}),
    .cfg_accept_count(32'd{len(profile['accepts'])}),
    .cfg_start_state(32'd{profile['start']}),.cfg_dead_state(32'd{profile['dead']}),
    .cfg_tag_register_count(32'd{profile['registers']}),
    .in_valid(in_valid),.in_ready(in_ready),.in_scalar(in_value),.in_last(in_last),
    .out_valid(out_valid),.out_ready(out_ready),.out_start(span_start),
    .out_end(span_end),.out_last(out_last),.busy(busy),.done(done),
    .error(error),.error_code(error_code),.tbl_req_valid(tbl_req_valid),
    .tbl_req_ready(tbl_req_ready),.tbl_req_addr(tbl_req_addr),
    .tbl_rsp_valid(tbl_rsp_valid),.tbl_rsp_ready(tbl_rsp_ready),
    .tbl_rsp_data(tbl_rsp_data),.tbl_rsp_error(tbl_rsp_error));
"""
    run_text_case(evidence, "source-unicode16-regex", seed, dut, memory,
                  list(map(ord, text)), [(first << 32) | end for first, end in expected],
                  cycles=5000000, provenance={
                      "scope": SCOPE, "regex_unicode_version": [16, 0, 0],
                      "full_scalar_classifier": True, "input_utf8_hex": text.encode().hex(),
                      "expected_byte_spans": expected,
                  })


ONIG_DRIVER = r"""
#include <stdio.h>
#include <stdlib.h>
#include "oniguruma.h"
int main(int argc, char **argv) {
    OnigEncoding encoding = ONIG_ENCODING_UTF8;
    OnigRegex regex;
    OnigErrorInfo info;
    unsigned char diagnostic[ONIG_MAX_ERROR_MESSAGE_LEN];
    if (argc != 2 || onig_initialize(&encoding, 1) != ONIG_NORMAL) return 2;
    const unsigned char *pattern = (const unsigned char *)@PATTERN@;
    int result = onig_new(&regex, pattern, pattern + @PATTERN_BYTES@,
                         ONIG_OPTION_NONE, encoding, ONIG_SYNTAX_DEFAULT, &info);
    if (result != ONIG_NORMAL) {
        onig_error_code_to_str(diagnostic, result, &info);
        fprintf(stderr, "ONIG_COMPILE %s\n", diagnostic);
        return 3;
    }
    FILE *input = fopen(argv[1], "r");
    if (!input) return 4;
    unsigned cases;
    if (fscanf(input, "%u", &cases) != 1 || cases == 0) return 5;
    OnigRegion *region = onig_region_new();
    for (unsigned item = 0; item < cases; ++item) {
        unsigned length;
        if (fscanf(input, "%u", &length) != 1 || length > 1048576) return 6;
        unsigned char *text = malloc(length + 1);
        if (!text) return 7;
        for (unsigned byte = 0; byte < length; ++byte) {
            unsigned value;
            if (fscanf(input, "%x", &value) != 1 || value > 255) return 8;
            text[byte] = (unsigned char)value;
        }
        int cursor = 0;
        unsigned spans = 0;
        while (cursor < (int)length) {
            result = onig_search(regex, text, text + length, text + cursor,
                                 text + length, region, ONIG_OPTION_NONE);
            if (result != cursor || region->beg[0] != cursor ||
                region->end[0] <= cursor || region->end[0] > (int)length) {
                fprintf(stderr, "ONIG_PROGRESS case=%u cursor=%d result=%d\n", item, cursor, result);
                return 9;
            }
            printf("SPAN %u %d %d\n", item, region->beg[0], region->end[0]);
            cursor = region->end[0];
            ++spans;
        }
        printf("CASE %u %u\n", item, spans);
        free(text);
    }
    char extra;
    if (fscanf(input, " %c", &extra) != EOF) return 10;
    fclose(input);
    onig_region_free(region, 1);
    onig_free(regex);
    onig_end();
    printf("ONIG_CASES %u\n", cases);
    return 0;
}
"""


def onig_reference(evidence, converted):
    """Compile the pinned candidate engine locally; never install a library."""
    from qwen_regex import PATTERN
    from official import validate
    validate(evidence.path)
    pinned_qwen = json.loads((ROOT / "tests/data/qwen-tokenizer.json").read_bytes())
    require(pinned_qwen["pre_tokenizer"]["pretokenizers"][0]["pattern"] == {"Regex": PATTERN},
            "Regex driver no longer represents the pinned official expression")
    evidence.tools(("gcc",))
    archive = members(converted.raw["onig_sys-69.9.1.crate"], "onig_sys", "69.9.1")
    directory = evidence.path / "candidate-oniguruma"
    directory.mkdir()
    for name, raw in archive.items():
        if name.startswith("oniguruma/src/") or name in ("build.rs", "oniguruma/COPYING", "LICENSE.md"):
            target = directory / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as output:
                output.write(raw)
    # Same Unix configuration features as the crate's build.rs; sizes supplied
    # by the actual C compiler rather than assuming this machine's ABI.
    config = "\n".join(f"#define {key} {value}" for key, value in (
        ("HAVE_PROTOTYPES", 1), ("STDC_HEADERS", 1), ("HAVE_STRING_H", 1),
        ("HAVE_STDARG_H", 1), ("HAVE_STDLIB_H", 1), ("HAVE_LIMITS_H", 1),
        ("HAVE_INTTYPES_H", 1), ("HAVE_UNISTD_H", 1), ("HAVE_SYS_TYPES_H", 1),
        ("HAVE_SYS_TIME_H", 1), ("SIZEOF_INT", "__SIZEOF_INT__"),
        ("SIZEOF_SHORT", "__SIZEOF_SHORT__"), ("SIZEOF_LONG", "__SIZEOF_LONG__"),
        ("SIZEOF_VOIDP", "__SIZEOF_POINTER__"), ("SIZEOF_LONG_LONG", "__SIZEOF_LONG_LONG__"),
    )) + "\n"
    (directory / "config.h").write_text(config, encoding="ascii")
    source_files = re.search(r"let files = \[(.*?)\];", archive["build.rs"].decode(), re.DOTALL)
    require(source_files is not None, "Missing published C compilation source list")
    names = re.findall(r'"([a-z0-9_]+\.c)"', source_files[1])
    require(len(names) == 48 and len(names) == len(set(names)) and
            not re.sub(r'"[a-z0-9_]+\.c"\s*,', "", source_files[1]).strip(),
            "Incomplete candidate C source list")
    driver = ONIG_DRIVER.replace("@PATTERN@", json.dumps(PATTERN)).replace(
        "@PATTERN_BYTES@", str(len(PATTERN.encode())))
    (directory / "driver.c").write_text(driver, encoding="ascii")
    binary = directory / "regex-reference"
    evidence.child(
        ["gcc", "-O2", "-std=gnu99", "-Werror=implicit-function-declaration",
         "-I", evidence.relative(directory),
         "-I", evidence.relative(directory / "oniguruma/src"),
         *[evidence.relative(directory / "oniguruma/src" / name) for name in names],
         evidence.relative(directory / "driver.c"), "-o", evidence.relative(binary)],
        "compile-pinned-candidate-oniguruma")
    texts = [
        regex_text(converted), NORMALIZATION_TEXT, " \t\r\n  !   ",
        "'\u017f 's '\u017fT 'ST '\u00df \ufb05 \ufb06",
        "a\u1c89b \U0001e4d0\U0001e4ec \U00011935\U00011930",
    ]
    for seed in (1, 17, 89):
        rng = random.Random(seed)
        alphabet = list("sStTrReEvVmMlLdD'09 \r\n\t!?") + [
            "\u017f", "\u00df", "\ufb05", "\u0301", "\u00a0", "\u4e2d",
            "\u1c89", "\U0001e4d0", "\U0001e4ec", "\U0001f600",
        ]
        texts.extend("".join(rng.choices(alphabet, k=rng.randrange(1, 129))) for _ in range(1000))
    vector = directory / "vectors.txt"
    with vector.open("x", encoding="ascii") as output:
        output.write(str(len(texts)) + "\n")
        for text in texts:
            data = text.encode()
            output.write(str(len(data)) + " " + data.hex(" ") + "\n")
    result = evidence.child([evidence.relative(binary), evidence.relative(vector)],
                            "execute-pinned-candidate-oniguruma")
    expected = [regex_spans(converted, text) for text in texts]
    actual, totals, declared = [[] for _ in texts], {}, None
    for line in (ROOT / result["stdout"]).read_text().splitlines():
        fields = line.split()
        if fields[0] == "SPAN":
            require(len(fields) == 4 and 0 <= int(fields[1]) < len(texts), "Malformed regex span trace")
            actual[int(fields[1])].append((int(fields[2]), int(fields[3])))
        elif fields[0] == "CASE":
            require(len(fields) == 3 and int(fields[1]) not in totals, "Duplicate regex case trace")
            totals[int(fields[1])] = int(fields[2])
        elif fields[0] == "ONIG_CASES":
            require(len(fields) == 2 and declared is None, "Malformed regex summary")
            declared = int(fields[1])
        else:
            raise ValueError(f"Unrecognized candidate regex output: {line}")
    comparison = {
        "scope": "Compiled pinned candidate Oniguruma, not executed official tokenizer library",
        "cases": len(texts), "expected": expected, "observed": actual,
        "vector_sha256": hashlib.sha256(vector.read_bytes()).hexdigest(),
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "compile_source_files": names,
    }
    with (evidence.path / "candidate-oniguruma-comparison.json").open("x", encoding="ascii") as output:
        json.dump(comparison, output, indent=2)
        output.write("\n")
    require(declared == len(texts) and set(totals) == set(range(len(texts))) and
            all(totals[item] == len(actual[item]) for item in totals),
            "Candidate Oniguruma comparison accounting incomplete")
    for item, (observed, wanted) in enumerate(zip(actual, expected)):
        require(observed == wanted, f"Candidate Oniguruma ordered-regex mismatch case={item}: "
                f"expected={wanted}, observed={observed}, utf8={texts[item].encode().hex()}")
    print(json.dumps({"candidate_oniguruma_cases": len(texts),
                      "compared_byte_spans": sum(map(len, actual)),
                      "official_tokenizer_reference_comparisons": 0}))


def run_unicode_rtl(evidence):
    run_unicode_conversion(evidence)
    converted = Converted()
    onig_reference(evidence, converted)
    evidence.tools(("verilator", "g++", "make"))
    evidence.run_cases([
        *[(f"unicode9-normalization-m{mode}-s{seed}",
           lambda scope, mode=mode, seed=seed: normalizer_rtl(scope, converted, seed, mode))
          for mode in (1, 3) for seed in (1, 17, 89)],
        *[(f"unicode16-ordered-regex-s{seed}",
           lambda scope, seed=seed: regex_rtl(scope, converted, seed)) for seed in (1, 17, 89)],
    ])
    from text import normalizer_test
    portable = copy.copy(evidence)
    portable.simulator_override = "iverilog"
    # One compact four-state case for each shared memory implementation. These
    # check the edited bench helper, not official-tokenizer equivalence.
    normalizer_test(portable, 17, "compact-memory-helper-portability", "e\u0301", 1)
    normalizer_rtl(portable, converted, 17, 1, "e\u0301", "-dense-memory-portability")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 tests/unicode_tables.py PROJECT_RELATIVE_EVIDENCE_DIRECTORY")
    destination = Path(sys.argv[1])
    if (destination.is_absolute() or ".." in destination.parts
            or destination.parts[:2] not in (("evidence", "preparation"), ("evidence", "verification"))
            or not destination.is_dir()):
        raise SystemExit("Output must be an existing fresh project-relative evidence directory")
    audit(destination)
