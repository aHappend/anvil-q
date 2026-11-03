"""Syntax-only lowering for Yosys 0.33; no datapath or arithmetic replacement."""

import hashlib
import json
import re

from execution import ROOT, relative


def lower_int_casts(text):
    # int'(e) is a signed 32-bit conversion, including signed extension of e.
    pattern = re.compile(r"\bint'\s*\(")
    count = 0
    while match := pattern.search(text):
        start = match.end()
        end = start
        depth = 1
        while depth and end < len(text):
            depth += (text[end] == "(") - (text[end] == ")")
            end += 1
        if depth:
            raise ValueError("unterminated int cast")
        text = text[:match.start()] + "$signed(32'(" + text[start:end-1] + "))" + text[end:]
        count += 1
    return text, count


def materialize(output):
    packages = {}
    source_hashes = {}
    for path in sorted(ROOT.glob("rtl/*.sv")):
        text = path.read_text()
        source_hashes[relative(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        if match := re.fullmatch(r"\s*package\s+(\w+)\s*;(.*)endpackage\s*", text, re.S):
            packages[match[1]] = match[2]
    directory = output / "frontend-sources"
    directory.mkdir()
    paths = []
    records = []
    for path in sorted(ROOT.glob("rtl/*.sv")):
        text = path.read_text()
        if re.fullmatch(r"\s*package\s+(\w+)\s*;(.*)endpackage\s*", text, re.S):
            continue
        imports = []

        def inline(match):
            package = match[1]
            if package not in packages:
                raise ValueError(f"unsupported imported package {package}")
            imports.append(package)
            return packages[package]

        text = re.sub(r"\bimport\s+(\w+)::\*\s*;", inline, text)
        text, count = lower_int_casts(text)
        hoisted = []
        if path.name == "anvil_q1_ht3_decoder.sv":
            for declaration in ("wire [31:0] p_panel;", "wire [63:0] p_mask;"):
                if text.count(declaration) != 1 or text.count("begin: g_legal") != 1:
                    raise ValueError("decoder forward-declaration lowering no longer matches source")
                text = text.replace(declaration, "", 1)
                hoisted.append(declaration)
            text = text.replace("begin: g_legal",
                                "begin: g_legal\n    " + "\n    ".join(hoisted), 1)
        destination = directory / path.name
        with destination.open("x") as out:
            out.write(text)
        paths.append(relative(destination))
        records.append(dict(source=relative(path), output=relative(destination),
                            imported_packages=imports, signed32_casts=count,
                            hoisted_declarations=hoisted,
                            output_sha256=hashlib.sha256(destination.read_bytes()).hexdigest()))
    with (output / "frontend.json").open("x") as out:
        json.dump(dict(source_sha256=source_hashes, transformations=records,
                       rules=["inline unchanged wildcard-imported package declarations",
                              "int'(e) -> $signed(32'(e)); preserve operand signedness",
                              "hoist two decoder net declarations within their unchanged scope"],
                       arithmetic_replaced=False), out, indent=2)
    return paths
