"""Source-level control inventory, independent of the Designer's grouped ledger.

Arithmetic storage/expressions are explicitly excluded, never added RTL lines.
All other clocked actions, request/routing actions, named/positional connections,
explicit state transitions and implicit waiting edges are inventoried. A manual
semantic audit must classify every item not proved by byte-identical modules.
That audit is pinned to both complete source trees and is independently
reviewable; text similarity alone is not a control-equivalence proof.
"""

from collections import Counter
import hashlib
import json
import re

from rtl_rules import TOKEN


MODULES = {
    "top": "fp_top", "decoder_layer": "fp_decoder_layer",
    "swiglu_mlp": "fp_swiglu_mlp", "w4a16_gemv": "fp_gemv",
    "gqa_attention": "fp_gqa_attention", "rope": "fp_rope",
    "rmsnorm": "fp_rmsnorm", "elementwise": "fp_elementwise",
    "mem_port": "mem_port", "bus_mux": "bus_mux",
}
ORIGINAL_SHA256 = {
    "00_pkg": "0402e27ea553398cad6464ce72f71c0e4fc47e61c2455f958fb5393a82f70bb5",
    "awq_dequant": "288100e05780872313a9d2f485213959fc5809f56aae4b2c0d22cc61f8c91537",
    "bus_mux": "9b41a1c242c344871258f0ba9d861e669cb1688f4b5fb2a46818b729251c2af7",
    "decoder_layer": "2fc6e519adde2b04fc2c48e9dbd8968d5d212ff692514f4a822ea15cc4ad5f0b",
    "elementwise": "07c092ddf26bd21053bed2996880bb38cdd22e7d9914fd6bfa3ff2fdf5dbe793",
    "gqa_attention": "d0d1c9ebd91967347d4f4bb7c5f0b6b859a2876f945ac1e53def23617ca12edb",
    "mem_port": "fc0b18df80b47572561fd8c8018d465856405a224c03640137d791d0c90b4561",
    "parameters": "2d0f084668ac9ed561da2978c10eade6adf142c4ba9673f5bfc3d963755968f9",
    "rmsnorm": "f97472325fb321ceb39f7c8c9f44f0a8910b9f4ad4ad26a6b7e4b6ccae0666fd",
    "rope": "ccc1066da5f6ab98d43cb408eda6de9c2c7ffc1598c479f25e4636380f81daf2",
    "swiglu_mlp": "0e944b6e7bbbaaa28394432f449c50a966d6c3245ede6cf2a0ab6da05a20a4ce",
    "top": "b95e15d3f67d336d91a31b9edb467e9fef6d8171faa11dbc8aa760f06c9114ef",
    "w4a16_gemv": "86b9aaf74d99ca167e6370a3952739c1093f87f9eb03a1af623e279ff9ef3630",
}
ARITHMETIC = {
    "top": "activation logit_sum tensor_f16 tensor_value logit_activation logit_weight logit_product",
    "w4a16_gemv": (
        "qw qz scales activation accumulators bias_f16 bias_value output_value product "
        "activation_operand weight_operand"),
    "gqa_attention": (
        "q cache_data dot max_score current_score weighted denominator exponential "
        "read_key read_value dot_product scaled_score weighted_product score_difference "
        "exp_argument sqrt_dim dim_scaled"),
    "rope": "x y cosine sine x_cos y_sin y_cos x_sin rotated_x rotated_y",
    "rmsnorm": "sum reciprocal denominator mean x gamma read_x square norm_product result",
    "elementwise": "a b silu_value sum product",
}


class Parser:
    def __init__(self, text):
        matches = [m for m in TOKEN.finditer(text)
                   if not m.group().startswith(("//", "/*", '"'))]
        self.ts = [m.group() for m in matches]
        self.lines = [text.count("\n", 0, m.start())+1 for m in matches]
        self.i = 0

    def group(self):
        if self.ts[self.i] != "(":
            raise ValueError("expected parenthesized expression")
        start = self.i
        depth = 0
        while self.i < len(self.ts):
            token = self.ts[self.i]
            self.i += 1
            depth += (token == "(")-(token == ")")
            if depth == 0:
                return self.ts[start+1:self.i-1]
        raise ValueError("unterminated expression")

    def statement(self):
        start = self.i
        token = self.ts[self.i]
        self.i += 1
        if token == "begin":
            children = []
            if self.ts[self.i] == ":":
                self.i += 2
            while self.ts[self.i] != "end":
                children.append(self.statement())
            self.i += 1
            return ("sequence", start, children)
        if token == "if":
            condition = self.group()
            yes = self.statement()
            no = None
            if self.ts[self.i] == "else":
                self.i += 1
                no = self.statement()
            return ("if", start, condition, yes, no)
        if token in ("case", "casex", "casez"):
            expression = self.group()
            branches = []
            while self.ts[self.i] != "endcase":
                label = []
                while self.ts[self.i] != ":":
                    label.append(self.ts[self.i])
                    self.i += 1
                self.i += 1
                branches.append((label, self.statement()))
            self.i += 1
            return ("case", start, expression, branches)
        if token == "for":
            self.group()
            return ("loop", start, self.statement())
        if token in ("while", "repeat", "forever", "fork"):
            raise ValueError("unsupported control inventory statement: " + token)
        while self.ts[self.i-1] != ";":
            self.i += 1
            if self.i > len(self.ts):
                raise ValueError("unterminated statement")
        return ("leaf", start, self.ts[start:self.i-1])

    def blocks(self):
        result = []
        self.i = 0
        while self.i < len(self.ts):
            token = self.ts[self.i]
            if token in ("always", "always_comb"):
                start = self.i
                self.i += 1
                sensitivity = []
                if token == "always":
                    if self.ts[self.i] != "@":
                        raise ValueError("unsupported always sensitivity")
                    self.i += 1
                    if self.ts[self.i] == "*":
                        self.i += 1
                    else:
                        sensitivity = self.group()
                result.append((start, bool({"posedge", "negedge"} & set(sensitivity)),
                               self.statement()))
            elif token == "assign":
                self.i += 1
                result.append((self.i-1, False, self.statement()))
            else:
                self.i += 1
        return result


def state_written(node):
    kind = node[0]
    if kind == "leaf":
        return len(node[2]) > 1 and node[2][:2] == ["state", "<="]
    if kind == "sequence":
        return any(state_written(n) for n in node[2])
    if kind == "if":
        return state_written(node[3]) or (node[4] is not None and state_written(node[4]))
    if kind == "case":
        return any(state_written(n) for _, n in node[3])
    if kind == "loop":
        return state_written(node[2])
    raise ValueError("unknown inventory node")


def waiting_paths(node, guards=(), written=False):
    """Enumerate only paths on which the original FSM register is unassigned."""
    kind = node[0]
    if kind == "leaf":
        return [(guards, written or state_written(node))]
    if kind == "sequence":
        paths = [(guards, written)]
        for child in node[2]:
            paths = [outcome for path, assigned in paths
                     for outcome in waiting_paths(child, path, assigned)]
        return paths
    if kind == "loop":
        if state_written(node):
            raise ValueError("loop changes architectural FSM state")
        return [(guards, written)]
    if not state_written(node):
        return [(guards, written)]
    if kind == "if":
        condition = " ".join(node[2])
        return (waiting_paths(node[3], (*guards, condition), written) +
                (waiting_paths(node[4], (*guards, "!("+condition+")"), written)
                 if node[4] is not None else
                 [((*guards, "!("+condition+")"), written)]))
    if kind == "case":
        paths = []
        for label, child in node[3]:
            paths += waiting_paths(child, (*guards,
                " ".join(node[2])+" in {"+ " ".join(label)+"}"), written)
        if not any(label == ["default"] for label, _ in node[3]):
            paths.append(((*guards, "unmatched case"), written))
        return paths
    raise ValueError("unknown waiting-path node")


def inventory(path, module):
    parser = Parser(path.read_text())
    excluded = set(ARITHMETIC.get(module, "").split())
    items = []
    states = set()

    def add(kind, index, guards, text, state=None):
        item = {
            "kind": kind, "line": parser.lines[index], "guards": list(guards),
            "text": text, "state": state,
        }
        identity = module + "/" + json.dumps(item, sort_keys=True)
        item["id"] = module + "/" + hashlib.sha256(identity.encode()).hexdigest()[:20]
        items.append(item)

    def walk(node, sequential, guards=(), state=None):
        kind, index = node[:2]
        if kind == "sequence":
            for child in node[2]:
                walk(child, sequential, guards, state)
        elif kind == "if":
            condition = " ".join(node[2])
            # Grouped case arms are inventoried per state, without crediting
            # assignments guarded by an incompatible literal state equality.
            known = None
            if state is not None and re.fullmatch(r"\d+", state):
                if (len(node[2]) == 3 and node[2][:2] == ["state", "=="] and
                        re.fullmatch(r"\d+", node[2][2])):
                    known = state == node[2][2]
            if known is False:
                if node[4] is not None:
                    walk(node[4], sequential, (*guards, "!("+condition+")"), state)
                return
            walk(node[3], sequential, (*guards, condition), state)
            if node[4] is not None and known is not True:
                walk(node[4], sequential, (*guards, "!("+condition+")"), state)
        elif kind == "case":
            is_state = node[2] == ["state"]
            for label, child in node[3]:
                context = " ".join(node[2])+" in {"+" ".join(label)+"}"
                targets = [t for t in label if t != ","] if is_state else [state]
                for target in targets:
                    if is_state and sequential:
                        states.add(target)
                    walk(child, sequential, (*guards, context), target)
                    if is_state and sequential:
                        for conditions, assigned in waiting_paths(child):
                            if not assigned:
                                add("waiting_edge", child[1], (*guards, context, *conditions),
                                    "state holds", target)
        elif kind == "loop":
            walk(node[2], sequential, (*guards, "elaboration loop"), state)
        elif kind == "leaf":
            statement = node[2]
            if len(statement) < 3 or statement[0] in excluded:
                return
            if not re.fullmatch(r"[A-Za-z_]\w*", statement[0]):
                return
            if not any(t in ("=", "<=") for t in statement[1:]):
                return
            category = "transition_edge" if statement[:2] == ["state", "<="] else (
                "clocked_control_action" if sequential else "request_routing_decode_action")
            add(category, index, guards, " ".join(statement), state)
        else:
            raise ValueError("unknown inventory statement")

    for _, sequential, node in parser.blocks():
        walk(node, sequential)
    # A global reset/fault transition is a family of edges from every original
    # state, not one favorable denominator row. Invalid encodings share default.
    expanded = []
    for item in items:
        if item["kind"] == "transition_edge" and item["state"] is None and states:
            for state in sorted(states):
                copy = dict(item, state=state, id=item["id"]+"/from-"+state)
                expanded.append(copy)
        else:
            expanded.append(item)
    items = expanded
    ts = parser.ts
    functional_types = {"anvil_q1_"+name for name in MODULES}
    for index, token in enumerate(ts):
        if token not in functional_types or index == 0 or ts[index-1] == "module":
            continue
        parser.i = index+1
        if ts[parser.i] == "#":
            parser.i += 1
            parser.group()
        instance = ts[parser.i]
        parser.i += 1
        start = parser.i+1
        parser.group()
        end = parser.i-1
        arguments = []
        depth = 0
        for j in range(start, end):
            depth += (ts[j] in ("(", "[", "{"))-(ts[j] in (")", "]", "}"))
            if ts[j] == "," and depth == 0:
                arguments.append((start, ts[start:j]))
                start = j+1
        arguments.append((start, ts[start:end]))
        for port, (location, expression) in enumerate(arguments):
            if not expression:
                raise ValueError("empty functional connection in original " + module)
            label = (expression[1] if expression[0] == "." else str(port))
            add("functional_port_connection", location, (),
                instance+"/"+label+" = "+" ".join(expression))
    ids = [item["id"] for item in items]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate original inventory identity in " + module)
    return {
        "items": items, "excluded_arithmetic_signals": sorted(excluded),
        "counts": dict(Counter(item["kind"] for item in items)),
        "states": sorted(states),
    }


def parser_selftest(path):
    path.write_text("""module inventory_fixture(
  input wire clk, rst_n, cmd_valid, complete,
  output wire cmd_ready, output reg [31:0] wd
);
  reg [3:0] state;
  wire [68:0] activation_operand, weight_operand;
  assign activation_operand=0;
  assign weight_operand=0;
  assign cmd_ready=rst_n && state==0;
  always @* begin
    wd=0;
    case(state)
      1,3,9,11: begin
        if(state==9) wd=1;
        if(state==11) wd=2;
      end
    endcase
  end
  always @(posedge clk) begin
    if(!rst_n) state<=0;
    else case(state)
      0: if(cmd_valid) state<=9;
      9: if(complete) state<=11;
      11: state<=0;
      default: state<=0;
    endcase
  end
endmodule
""")
    result = inventory(path, "w4a16_gemv")
    items = result["items"]
    routed = [(i["state"], i["text"]) for i in items
              if i["kind"] == "request_routing_decode_action"]
    waits = [(i["state"], i["guards"][-1]) for i in items
             if i["kind"] == "waiting_edge"]
    reset_sources = {i["state"] for i in items
                     if i["kind"] == "transition_edge" and i["guards"] == ["! rst_n"]}
    return {
        "grouped_case_reachable_actions": routed == [
            (None, "cmd_ready = rst_n && state == 0"), (None, "wd = 0"),
            ("9", "wd = 1"), ("11", "wd = 2")],
        "waiting_edges": waits == [("0", "!(cmd_valid)"), ("9", "!(complete)")],
        "complete_reset_edge_family": reset_sources == {"0", "9", "11", "default"},
        "arithmetic_only_operands_excluded": not any(
            i["text"].startswith(("activation_operand ", "weight_operand "))
            for i in items),
    }


def audit(root, report, digest):
    hashes = {str(p.relative_to(root)): digest(p)
              for pattern in ("rtl/*.sv", "anvil_q1_reference/rtl/*.sv")
              for p in sorted(root.glob(pattern))}
    original = {f"anvil_q1_reference/rtl/anvil_q1_{name}.sv": value
                for name, value in ORIGINAL_SHA256.items()}
    actual = {path: value for path, value in hashes.items()
              if path.startswith("anvil_q1_reference/rtl/")}
    if actual != original:
        raise ValueError("Read-only original source inventory changed")
    modules = {}
    automatic = {}
    for parent, revised in MODULES.items():
        source = root / f"anvil_q1_reference/rtl/anvil_q1_{parent}.sv"
        destination = root / f"rtl/anvil_q1_{revised}.sv"
        record = inventory(source, parent)
        record["parent_file"] = str(source.relative_to(root))
        record["revised_file"] = str(destination.relative_to(root))
        record["byte_identical"] = digest(source) == digest(destination)
        modules[parent] = record
        if record["byte_identical"]:
            for item in record["items"]:
                automatic[item["id"]] = {"classification": "R",
                                         "proof": "Complete module is byte-identical"}
    expected = {item["id"] for m in modules.values() for item in m["items"]}
    inventory_sha256 = hashlib.sha256(json.dumps(
        {name: value["items"] for name, value in modules.items()},
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    audit_path = root / "tests/preservation_review.py"
    supplied = {}
    review_basis = None
    failures = []
    if audit_path.is_file():
        from preservation_review import manual_audit
        data = manual_audit(root, modules, hashes)
        review_basis = data.get("review_basis")
        if data["schema"] != 1 or data["source_sha256"] != hashes:
            failures.append("Manual source audit is not bound to these complete RTL source trees")
        entries = data["items"]
        for item in entries:
            identity = item["id"]
            if identity in supplied or identity not in expected or identity in automatic:
                raise ValueError("duplicate, unknown or automatic preservation item: " + identity)
            if item["classification"] not in ("R", "E", "C") or not item["proof"].strip():
                raise ValueError("missing classification/proof: " + identity)
            target = root / item["revised_file"]
            if item["revised_file"] not in hashes or not target.is_file():
                raise ValueError("invalid audited source location")
            begin, end = item["revised_lines"]
            if not 1 <= begin <= end <= len(target.read_text().splitlines()):
                raise ValueError("invalid audited source line range")
            supplied[identity] = item
    unresolved = sorted(expected-set(automatic)-set(supplied))
    if unresolved:
        failures.append("Unclassified original control items require independent semantic source audit")
    counts = Counter(item["classification"] for item in (*automatic.values(), *supplied.values()))
    preserved = counts["R"]+counts["E"]
    threshold_met = preserved*100 >= len(expected)*85
    result = {
        "source_sha256": hashes, "modules": modules,
        "inventory_sha256": inventory_sha256,
        "automatic_classifications": automatic,
        "manual_audit": str(audit_path.relative_to(root)),
        "manual_review_basis": review_basis,
        "manual_classifications": supplied,
        "classification_counts": dict(counts), "complete_original_denominator": len(expected),
        "unclassified": unresolved, "failures": failures,
        "preserved_items": preserved, "threshold_percent": 85,
        "threshold_met": threshold_met,
        "passed": not failures and threshold_met,
    }
    report.write_text(json.dumps(result, indent=2)+"\n")
    return result
