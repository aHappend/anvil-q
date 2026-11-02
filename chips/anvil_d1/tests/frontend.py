"""Yosys 0.33 port-cast compatibility adapter on generated copies only.

A bare unsigned wire cast at a module port trips genrtlil.cc:2063. Explicit
same-width signed alias nets preserve the connected bit pattern and signed
extension. Original parent/D1 sources are immutable; arithmetic, state,
parameters and structural acceptance assertions are unchanged.
"""

import hashlib
from evidence import ROOT, rel


def adapted_sources(evidence):
    directory = evidence.path / ("frontend-source-" + evidence.path.name.rsplit("-", 1)[-1])
    directory.mkdir()
    paths, changes = [], []
    for original in sorted(ROOT.glob("anvil_q3_reference/rtl/*.sv")) + sorted(ROOT.glob("rtl/*.sv")):
        text = original.read_text()
        if original.name == "anvil_q3_rmsnorm.sv":
            for name in ("square", "mean"):
                anchor = "$signed("+name+")"
                if text.count(anchor) != 1:
                    raise AssertionError(f"frontend anchor changed: {rel(original)} {name}")
                text = text.replace(anchor, "frontend_signed_"+name)
            text = text.replace("  wire unit_flush=", (
                "  wire signed [127:0] frontend_signed_square = square;\n"
                "  wire signed [127:0] frontend_signed_mean = mean;\n"
                "  wire unit_flush="), 1)
        if original.name == "anvil_q3_tensor_array.sv":
            declaration = "    reg [31:0] addition_row;\n"
            anchor = "    wire signed [127:0] base_sum="
            if text.count(declaration) != 1 or text.count(anchor) != 1:
                raise AssertionError("tensor forward-declaration adapter anchor changed")
            text = text.replace(declaration, "").replace(anchor, declaration+anchor, 1)
        if text != original.read_text():
            changes.append(dict(source=rel(original),
                                original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                                adapted_sha256=hashlib.sha256(text.encode()).hexdigest()))
        target = directory / original.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        paths.append(target)
    evidence.record["frontend_adapter"] = dict(
        method="same-width signed aliases for bare unsigned port casts",
        changes=changes, generated_source_sha256={
            rel(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})
    evidence.save()
    return paths
