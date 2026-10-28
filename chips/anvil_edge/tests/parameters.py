"""Executable legal and illegal elaboration diagnostics, not text scanning."""

from pathlib import Path


def run_parameters(evidence):
    evidence.tools(("iverilog", "vvp"))
    root = Path(__file__).resolve().parent.parent
    sources = ["rtl/anvil_edge_numeric_pkg.sv"]
    sources += [str(path.relative_to(root)) for path in sorted((root / "rtl").glob("*.sv"))
                if path.name != "anvil_edge_numeric_pkg.sv"]
    minimum = {
        "NUM_LAYERS": 1, "HIDDEN_SIZE": 8, "INTERMEDIATE_SIZE": 8,
        "NUM_Q_HEADS": 1, "NUM_KV_HEADS": 1, "HEAD_DIM": 8,
        "GROUP_SIZE": 8, "VOCAB_SIZE": 257, "MAX_SEQ_LEN": 4,
        "MAX_PROMPT_BYTES": 3, "MAX_PROMPT_TOKENS": 3,
        "MAX_PRETOKEN_BYTES": 3, "MAX_TOKEN_BYTES": 4,
        "MAX_TRIE_NODES": 16, "MAX_SPECIAL_RECORDS": 16,
    }
    cases = []
    for dimension in ("NUM_LAYERS", "HIDDEN_SIZE", "INTERMEDIATE_SIZE", "NUM_Q_HEADS",
                      "NUM_KV_HEADS", "HEAD_DIM", "GROUP_SIZE", "VOCAB_SIZE", "MAX_SEQ_LEN"):
        cases.append((f"top-zero-{dimension.lower()}", "anvil_edge_top",
                      {**minimum, dimension: 0}, True))
    for name, overrides in (
        ("awq", {"AWQ_BITS": 3}),
        ("head-divisibility", {"NUM_Q_HEADS": 3, "HIDDEN_SIZE": 24, "NUM_KV_HEADS": 2}),
        ("head-product", {"HIDDEN_SIZE": 16}),
        ("odd-head-dimension", {"HEAD_DIM": 7}),
        ("group-divisibility", {"GROUP_SIZE": 3}),
        ("projection-packing", {"INTERMEDIATE_SIZE": 12, "GROUP_SIZE": 4}),
        ("sequence-overflow", {"MAX_SEQ_LEN": 16777216}),
        ("vocabulary-address-overflow", {"VOCAB_SIZE": "64'd536870912"}),
        ("prompt-bytes", {"MAX_PROMPT_BYTES": 0}),
        ("prompt-tokens", {"MAX_PROMPT_TOKENS": 0}),
        ("pretoken-bytes", {"MAX_PRETOKEN_BYTES": 0}),
        ("token-bytes", {"MAX_TOKEN_BYTES": 0}),
    ):
        cases.append(("top-invalid-" + name, "anvil_edge_top", {**minimum, **overrides}, True))
    for depth in (0, -1):
        cases.append((f"fifo-depth-{depth}", "anvil_edge_fifo",
                      {"WIDTH": 9, "DEPTH": depth}, True))
        for direction in ("RX", "TX"):
            cases.append((f"uart-{direction.lower()}-depth-{depth}", "anvil_edge_uart_io",
                          {f"{direction}_FIFO_DEPTH": depth}, True))
    for depth in (1, 2, 3, 16):
        cases.append((f"fifo-legal-depth-{depth}", "anvil_edge_fifo",
                      {"WIDTH": 9, "DEPTH": depth}, False))
    cases += [
        ("top-legal-minimum", "anvil_edge_top", minimum, False),
        ("top-legal-controller-only-capacity", "anvil_edge_top",
         {**minimum, "VOCAB_SIZE": 1}, False),
        ("top-legal-multilayer-gqa", "anvil_edge_top",
         {**minimum, "NUM_LAYERS": 2, "HIDDEN_SIZE": 16, "INTERMEDIATE_SIZE": 24,
          "NUM_Q_HEADS": 2}, False),
    ]
    for name, module, parameters, rejected in cases:
        directory = evidence.path / name
        directory.mkdir()
        bench = directory / "bench.sv"
        bindings = ",".join(f".{key}({value})" for key, value in parameters.items())
        bench.write_text(
            f"module bench;\n  {module} #({bindings}) dut();\n"
            '  initial begin #1; $display("ELABORATION_REACHED"); $finish; end\nendmodule\n',
            encoding="ascii",
        )
        binary = directory / "simulation.vvp"
        evidence.child(["iverilog", "-g2012", "-Wall", "-s", "bench", "-o",
                        evidence.relative(binary), *sources, evidence.relative(bench)],
                       name + "-compile")
        result = evidence.child(["vvp", evidence.relative(binary)], name + "-simulate",
                                allow_failure=rejected)
        stdout = (root / result["stdout"]).read_text()
        stderr = (root / result["stderr"]).read_text()
        if rejected:
            if (result["exit_code"] in (None, 0) or result["timed_out"] or
                    not result["child_settled"] or "PARAMETER ERROR" not in stdout + stderr or
                    "ELABORATION_REACHED" in stdout):
                raise RuntimeError(f"Illegal parameters lack executable diagnostic: {name}")
        elif "ELABORATION_REACHED" not in stdout:
            raise RuntimeError(f"Legal parameter elaboration did not execute: {name}")
        evidence.record["coverage"].append({
            "name": name, "status": "passed",
            "scope": "Executable elaboration only; not functional geometry coverage",
            "parameters": parameters, "expected_parameter_rejection": rejected,
            "observed_exit_code": result["exit_code"],
        })
