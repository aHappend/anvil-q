"""Yosys 0.33 signed package-function return compatibility adapter.

Only generated copies change. A signed 32-bit function result is represented as
an unsigned 32-bit result with an explicit $signed cast at every qualified call.
This preserves the bit pattern, width and expression signedness. No arithmetic,
ports, state, parameters or synthesis acceptance assertions are changed.
"""

import hashlib
from pathlib import Path
import re

from evidence import ROOT, rel


FUNCTIONS = ("f16_q16", "round_q32_to_q16", "round_shift_sat32")


def adapted_sources(evidence):
    directory = evidence.path / ("frontend-source-" + evidence.path.name.rsplit("-", 1)[-1])
    directory.mkdir()
    paths, changes = [], []
    for original in sorted(ROOT.glob("anvil_q3_reference/rtl/*.sv")) + sorted(ROOT.glob("rtl/*.sv")):
        text = original.read_text()
        if original.parent.name == "rtl" and original.parent.parent.name == "anvil_q3_reference":
            before = text
            for name in FUNCTIONS:
                text = re.sub(r"(function\s+automatic)\s+signed\s+(\[31:0\]\s+"+name+r"\b)",
                              r"\1 \2", text)
                prefix = "anvil_q3_pkg::"+name+"("
                offset = 0
                while (index := text.find(prefix, offset)) >= 0:
                    start = index+len(prefix)
                    depth, end = 1, start
                    while depth and end < len(text):
                        depth += (text[end] == "(") - (text[end] == ")")
                        end += 1
                    if depth:
                        raise ValueError(f"unbalanced package call in {rel(original)}")
                    call = text[index:end]
                    text = text[:index]+"$signed("+call+")"+text[end:]
                    offset = end+len("$signed(")+1
            if text != before:
                changes.append(dict(source=rel(original),
                                    original_sha256=hashlib.sha256(before.encode()).hexdigest(),
                                    adapted_sha256=hashlib.sha256(text.encode()).hexdigest()))
        target = directory / original.name
        target.write_text(text)
        paths.append(target)
    evidence.record["frontend_adapter"] = dict(
        method="unsigned fixed-width function return; explicit signed cast at every call",
        changes=changes, generated_source_sha256={
            rel(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})
    evidence.save()
    return paths
