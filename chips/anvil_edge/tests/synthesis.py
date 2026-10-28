"""Actual production hierarchy synthesis; no replacement core or blackboxes."""

import json
from pathlib import Path
import re


def portable_sources(evidence):
    """Retain a lexical lowering, never arithmetic or behavioral substitution."""
    root = Path(__file__).resolve().parent.parent
    directory = evidence.path / "yosys-sources"
    directory.mkdir()
    package = (root / "rtl/anvil_edge_numeric_pkg.sv").read_text()
    prefix, suffix = "package anvil_edge_numeric_pkg;", "endpackage\n"
    if not package.startswith(prefix) or not package.endswith(suffix):
        raise RuntimeError("Unexpected numeric package shape; refuse speculative lowering")
    functions = package[len(prefix):-len(suffix)]
    records = []
    sources = []
    for path in sorted((root / "rtl").glob("*.sv")):
        if path.name == "anvil_edge_numeric_pkg.sv":
            continue
        original = path.read_text()
        lowered = original
        lifted = "anvil_edge_numeric_pkg::" in original
        if lifted:
            if "\n  function " in original:
                raise RuntimeError(f"Potential local function collision in {path.name}")
            boundary = original.index("\n);") + len("\n);")
            lowered = original[:boundary] + functions + original[boundary:]
            lowered = lowered.replace("anvil_edge_numeric_pkg::", "")
        # Both pull-down-default ports are explicitly driven in the production
        # hierarchy. No omitted-port standalone fixture is synthesized here.
        defaults = []
        for name in ("response_complete", "abort_inference"):
            token = f"input tri0 {name}"
            if token in lowered:
                lowered = lowered.replace(token, f"input wire {name}")
                defaults.append(name)
        declaration_hoisted = False
        if path.name == "anvil_edge_image_loader.sv":
            declaration = "    wire [7:0] flash_data;\n"
            anchor = "    wire [31:0] assembled_word="
            if lowered.count(declaration) != 1 or lowered.count(anchor) != 1:
                raise RuntimeError("Unexpected flash-data declaration; refuse speculative lowering")
            lowered = lowered.replace(declaration, "")
            lowered = lowered.replace(anchor, declaration + anchor)
            declaration_hoisted = True
        port_views = []
        view_specs = {
            "anvil_edge_exp_q24.sv": [
                ("$signed(remainder_value)", "remainder_value", "yosys_signed_remainder"),
            ],
            "anvil_edge_silu_q16.sv": [
                ("$signed(sigmoid)", "sigmoid", "yosys_signed_sigmoid"),
                ("$signed({{32{operand[31]}},operand})", "{{32{operand[31]}},operand}",
                 "yosys_extended_operand"),
            ],
        }
        for expression, bits, name in view_specs.get(path.name, []):
            if lowered.count(expression) != 1:
                raise RuntimeError(f"Ambiguous signed view in {path.name}")
            anchor = ("  anvil_edge_unsigned_divider #(" if path.name == "anvil_edge_exp_q24.sv"
                      else "  anvil_edge_exp_q24 exp_unit(")
            boundary = lowered.index(anchor)
            lowered = lowered[:boundary] + (
                f"\n  wire signed [63:0] {name}={bits};\n"
            ) + lowered[boundary:]
            lowered = lowered.replace(expression, name)
            port_views.append({"expression": expression, "width": 64, "wire": name})
        preserved_memories = []

        def preserve_memory(match):
            preserved_memories.append(match[2])
            return match[1] + "(* nomem2reg *) " + match[2]

        lowered = re.sub(
            r"^(\s*)(reg\s+(?:\[[^\]]+\]\s+)?\w+\s*\[0:(?:MAX_|DEPTH)[^\]]+\];)",
            preserve_memory,
            lowered,
            flags=re.MULTILINE,
        )
        target = directory / path.name
        target.write_text(lowered, encoding="ascii")
        records.append({"source": str(path.relative_to(root)),
                        "lowered": evidence.relative(target),
                        "numeric_functions_lifted_verbatim": lifted,
                        "flash_data_declaration_hoisted": declaration_hoisted,
                        "signed_port_views": port_views,
                        "preserved_memory_declarations": preserved_memories,
                        "explicitly_driven_default_ports": defaults})
        sources.append(evidence.relative(target))
    top = (root / "rtl/anvil_edge_top.sv").read_text()
    if ".response_complete(done_r)" not in top or ".abort_inference(abort_r)" not in top:
        raise RuntimeError("Production default-port connectivity changed")
    (directory / "lowering.json").write_text(json.dumps({
        "transform": "Verbatim package functions become module-local; qualified references lose only the namespace. Explicitly driven tri0 ports become wire inputs. Flash data declaration is hoisted before its use. Signed expression views retain exact 64-bit port values. nomem2reg preserves the listed arrays as memories without changing their procedural reads/writes.",
        "arithmetic_changed": False, "records": records,
    }, indent=2) + "\n")
    return sources


def check_lowering(evidence, sources):
    """Same-cycle public outputs before/after lexical tool-compatibility lowering."""
    root = Path(__file__).resolve().parent.parent
    directory = evidence.path / "lowering-comparison"
    directory.mkdir()
    module_names = [Path(name).stem for name in sources]
    names = re.compile(r"\b(" + "|".join(map(re.escape, module_names)) + r")\b")
    renamed = []
    for name in sources:
        target = directory / Path(name).name
        target.write_text(names.sub(lambda match: "lowered_" + match[0], (root / name).read_text()),
                          encoding="ascii")
        renamed.append(evidence.relative(target))
    for unit, width in (("exp_q24", 64), ("silu_q16", 32)):
        bench = r"""
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg in_valid=0,out_ready=0;
  reg signed [@WIDTH@-1:0] x=0;
  wire a_ready,b_ready,a_valid,b_valid,a_error,b_error;
  wire [31:0] a_value,b_value;
  anvil_edge_@UNIT@ original(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(a_ready),.x(x),
    .out_valid(a_valid),.out_ready(out_ready),.value(a_value),.arithmetic_error(a_error));
  lowered_anvil_edge_@UNIT@ lowered(
    .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(b_ready),.x(x),
    .out_valid(b_valid),.out_ready(out_ready),.value(b_value),.arithmetic_error(b_error));
  integer comparisons=0,outputs=0,i;
  reg [63:0] rng=64'h123456789abcdef1;
  always @(posedge clk or negedge clk) begin
    if ((^{a_ready,b_ready,a_valid,b_valid,a_error,b_error,a_value,b_value})===1'bx)
      $fatal(1,"LOWERING_XZ");
    if ({a_ready,a_valid,a_error,a_value}!=={b_ready,b_valid,b_error,b_value})
      $fatal(1,"LOWERING_EQUIVALENCE");
    if (!rst_n && {a_ready,a_valid,a_error,a_value,b_ready,b_valid,b_error,b_value}!==0)
      $fatal(1,"LOWERING_RESET");
  end
  always @(posedge clk) if (rst_n && a_valid && out_ready) outputs=outputs+1;
  initial begin
    rst_n=0; #0;
    repeat (2) @(negedge clk);
    rst_n=1;
    for (i=0;i<80;i=i+1) begin
      @(negedge clk); #1;
      rng=rng ^ (rng<<13); rng=rng ^ (rng>>7); rng=rng ^ (rng<<17);
      case (i)
        0: x=0; 1: x=-1; 2: x=-1048576; 3: x=-1048577;
        4: x={1'b1,{(@WIDTH@-1){1'b0}}};
        5: x={1'b0,{(@WIDTH@-1){1'b1}}};
        default: x=rng;
      endcase
      in_valid=1; out_ready=0;
      do begin @(posedge clk); end while (!a_ready);
      #1; @(negedge clk); #1; in_valid=0;
      while (!a_valid) begin @(posedge clk); #1; end
      repeat (4) @(negedge clk);
      out_ready=1; @(posedge clk); #1; comparisons=comparisons+1;
      @(negedge clk); #1; out_ready=0;
    end
    if (outputs!=80 || comparisons!=80) $fatal(1,"LOWERING_COUNTS");
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin repeat (200000) @(posedge clk); $fatal(1,"LOWERING_CYCLE_BOUND"); end
endmodule
"""
        bench = bench.replace("@WIDTH@", str(width)).replace("@UNIT@", unit)
        original = ["rtl/anvil_edge_numeric_pkg.sv"]
        original.extend(str(path.relative_to(root)) for path in sorted((root / "rtl").glob("*.sv"))
                        if path.name != "anvil_edge_numeric_pkg.sv")
        evidence.simulate("lowering-" + unit, bench, original + renamed, 80)


def run_synthesis(evidence, configurations=("minimum", "default")):
    evidence.tools(("yosys", "iverilog", "vvp"))
    sources = portable_sources(evidence)
    check_lowering(evidence, sources)
    for configuration in configurations:
        directory = evidence.path / f"synthesis-{configuration}"
        directory.mkdir()
        netlist = directory / "netlist.json"
        parameters = ""
        if configuration == "minimum":
            parameters = " ".join(f"-chparam {name} {value}" for name, value in {
                "NUM_LAYERS": 1, "HIDDEN_SIZE": 8, "INTERMEDIATE_SIZE": 8,
                "NUM_Q_HEADS": 1, "NUM_KV_HEADS": 1, "HEAD_DIM": 8, "GROUP_SIZE": 8,
                "VOCAB_SIZE": 257, "MAX_SEQ_LEN": 4, "MAX_PROMPT_BYTES": 3,
                "MAX_PROMPT_TOKENS": 3, "MAX_PRETOKEN_BYTES": 3, "MAX_TOKEN_BYTES": 4,
                "MAX_TRIE_NODES": 16, "MAX_SPECIAL_RECORDS": 16,
                "RX_FIFO_DEPTH": 1, "TX_FIFO_DEPTH": 3,
            }.items())
        script = directory / "synthesize.ys"
        script.write_text(
            "read_verilog -sv -defer " + " ".join(sources) + "\n"
            f"hierarchy -check -top anvil_edge_top {parameters}\n"
            "proc\nmemory_collect\nopt\ncheck -assert\n"
            "select -assert-none t:$dlatch t:$adlatch t:$dlatchsr "
            "t:$div t:$mod t:$divfloor t:$modfloor\n"
            f"write_json {evidence.relative(netlist)}\n",
            encoding="ascii",
        )
        evidence.child(["yosys", "-Q", "-T", "-s", evidence.relative(script)],
                       f"synthesis-{configuration}")
        data = json.loads(netlist.read_text())
        modules = data["modules"]
        required = {
            "anvil_edge_top", "anvil_edge_uart_io", "anvil_edge_bpe_tokenizer",
            "anvil_edge_detokenizer", "anvil_edge_autoregressive_fsm",
            "anvil_edge_ddr4_boot_loader", "anvil_edge_core_adapter",
            "anvil_edge_memory_subsystem", "anvil_q1_top",
            "anvil_q1_rmsnorm", "anvil_q1_w4a16_gemv", "anvil_q1_gqa_attention",
        }
        seen = set()
        state_bits = 0
        cell_count = 0

        def visit(name):
            nonlocal state_bits, cell_count
            module = modules[name]
            if module.get("attributes", {}).get("blackbox") in ("1", 1, "00000000000000000000000000000001"):
                raise RuntimeError(f"Blackboxed reachable production module {name}")
            hdlname = module.get("attributes", {}).get("hdlname", name).split()[0].lstrip("\\")
            seen.add(hdlname)
            for cell in module.get("cells", {}).values():
                kind = cell["type"]
                if kind in modules:
                    visit(kind)
                else:
                    cell_count += 1
                    if any(bad in kind.lower() for bad in ("latch", "div", "mod")):
                        raise RuntimeError(f"Forbidden synthesized cell {kind}")
                    if "dff" in kind.lower():
                        state_bits += len(cell.get("connections", {}).get("Q", []))

        visit("anvil_edge_top")
        if required - seen or state_bits < 1000 or cell_count < 1000:
            raise RuntimeError(f"Incomplete production hierarchy: missing={required-seen}, "
                               f"state_bits={state_bits}, cells={cell_count}")
        if len(data.get("modules", {})) <= 1:
            raise RuntimeError("Production synthesis lost its modular hierarchy")
        result = {
            "configuration": configuration, "reachable_modules": sorted(seen),
            "state_bits": state_bits, "primitive_cells": cell_count,
            "forbidden_cells": 0, "physical_timing_acceptance": False,
        }
        (directory / "structural-result.json").write_text(json.dumps(result, indent=2) + "\n")
        evidence.record["coverage"].append({"name": f"synthesis-{configuration}",
                                            "status": "passed", **result})
