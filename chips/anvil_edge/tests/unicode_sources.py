"""Read-only, pinned upstream Unicode dependency inspection; no tool installation.

The selected source release is a research candidate, not an executed official
tokenizer build. Cargo dependency ranges do not identify a wheel's linked code.
"""

import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tarfile
import urllib.request


TOKENIZERS_COMMIT = "e892882fd4608b468dcf9dc33ea95283882b8e6d"
CRATES = (
    ("unicode-normalization-alignments", "0.1.12",
     "43f613e4fa046e69818dd287fdc4bc78175ff20331479dab6e1b0f98d57062de"),
    ("onig_sys", "69.9.1",
     "c7f86c6eef3d6df15f23bcfb6af487cbd2fed4e5581d58d5bf1f5f8b7f6727dc"),
)
SOURCES = (
    "tokenizers/Cargo.toml",
    "tokenizers/src/utils/onig.rs",
    "tokenizers/src/normalizers/unicode.rs",
    "tokenizers/src/tokenizer/normalizer.rs",
    "tokenizers/src/pre_tokenizers/split.rs",
    "tokenizers/src/tokenizer/added_vocabulary.rs",
    "LICENSE",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def retrieve(directory, filename, url, expected=None):
    request = urllib.request.Request(url, headers={"User-Agent": "Anvil-Edge-verifier/1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read(32 * 1024 * 1024 + 1)
        status = response.status
    require(len(data) <= 32 * 1024 * 1024, "Source input exceeds bounded intake")
    actual = hashlib.sha256(data).hexdigest()
    require(expected is None or actual == expected, f"Immutable source hash mismatch: {filename}")
    with (directory / filename).open("xb") as output:
        output.write(data)
    return data, {"file": filename, "url": url, "sha256": actual,
                  "bytes": len(data), "http_status": status}


def members(raw, crate, version):
    """Read named bytes only: never extract archive paths or execute sources."""
    prefix = f"{crate}-{version}/"
    result = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for item in archive.getmembers():
            path = Path(item.name)
            require(not path.is_absolute() and ".." not in path.parts
                    and item.name.startswith(prefix), "Unsafe upstream archive member")
            if item.isfile():
                require(item.size <= 16 * 1024 * 1024, "Oversized upstream member")
                with archive.extractfile(item) as source:
                    result[item.name[len(prefix):]] = source.read()
            else:
                require(item.isdir(), "Unsupported upstream archive member type")
    return result


def inspect(directory):
    directory = Path(directory)
    records, source_files = [], {}
    for path in SOURCES:
        raw, record = retrieve(
            directory, "tokenizers-" + path.replace("/", "-"),
            f"https://raw.githubusercontent.com/huggingface/tokenizers/{TOKENIZERS_COMMIT}/{path}")
        source_files[path] = raw.decode("utf-8")
        records.append(record)
    cargo = source_files["tokenizers/Cargo.toml"]
    require('version = "0.21.4"' in cargo and
            'unicode-normalization-alignments = "0.1"' in cargo and
            'default = ["progressbar", "onig", "esaxx_fast"]' in cargo,
            "Candidate tokenizer source dependencies changed")
    require("use onig::Regex;" in source_files["tokenizers/src/utils/onig.rs"] and
            "Regex::new(regex_str)?" in source_files["tokenizers/src/utils/onig.rs"] and
            "normalized.nfc();" in source_files["tokenizers/src/normalizers/unicode.rs"] and
            "use unicode_normalization_alignments::UnicodeNormalization;" in
            source_files["tokenizers/src/tokenizer/normalizer.rs"],
            "Upstream Unicode implementation path not established")
    archives = {}
    for crate, version, checksum in CRATES:
        raw, record = retrieve(
            directory, f"{crate}-{version}.crate",
            f"https://static.crates.io/crates/{crate}/{crate}-{version}.crate", checksum)
        archives[crate] = members(raw, crate, version)
        records.append(record)
    normalization = archives["unicode-normalization-alignments"]
    tables = normalization["src/tables.rs"].decode("utf-8")
    version_match = re.search(
        r"pub const UNICODE_VERSION: \(u64, u64, u64\) = \((\d+), (\d+), (\d+)\);", tables)
    require(version_match is not None, "Normalization Unicode version not explicit")
    normalization_version = tuple(map(int, version_match.groups()))
    onig = archives["onig_sys"]
    version_lines = []
    for name, raw in onig.items():
        if ("unicode" in name.lower() or name.endswith("HISTORY")) and name.endswith((".c", ".h", "HISTORY")):
            for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
                if re.search(r"Unicode.*\d+\.\d+", line, re.IGNORECASE):
                    version_lines.append({"member": name, "line": number, "text": line.strip()})
    require(version_lines, "Oniguruma source does not establish a Unicode-version marker")
    result = {
        "scope": "Pinned upstream source inspection only, no code compiled or installed",
        "candidate_tokenizers_version": "0.21.4",
        "candidate_tokenizers_commit": TOKENIZERS_COMMIT,
        "normalization_dependency": "unicode-normalization-alignments 0.1.12",
        "normalization_unicode_version": normalization_version,
        "regex_candidate": "onig_sys 69.9.1 vendored Oniguruma; not a linked reference build",
        "regex_unicode_source_markers": version_lines,
        "sources": records,
        "normalization_source_members": {
            name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            for name, raw in normalization.items()
        },
        "missing": [
            "Executed official tokenizers reference with exact distribution/build and dependency versions",
            "Decision on faithfully representing mixed upstream Unicode versions in the frozen single-version metadata",
            "Complete official-profile NFC/regex tables and hardware equivalence",
        ],
        "official_reference_comparisons": 0,
        "rtl_executed": False,
    }
    with (directory / "upstream-unicode-inspection.json").open("x", encoding="ascii") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print(json.dumps(result, indent=2))


def run_unicode_sources(evidence):
    evidence.tools(("python3",))
    evidence.child(["python3", "tests/unicode_sources.py", evidence.relative(evidence.path)],
                   "pinned-upstream-unicode-source-inspection")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 tests/unicode_sources.py PROJECT_RELATIVE_EVIDENCE_DIRECTORY")
    destination = Path(sys.argv[1])
    if (destination.is_absolute() or ".." in destination.parts
            or destination.parts[:2] != ("evidence", "preparation") or not destination.is_dir()):
        raise SystemExit("Output must be an existing project-relative fresh preparation directory")
    inspect(destination)
