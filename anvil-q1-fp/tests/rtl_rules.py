"""Small lexical checks; netlist checks independently enforce structural rules."""

import re

TOKEN = re.compile(
    r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|'
    r"(?:\d+)?'[sS]?[bBoOdDhH][0-9a-fA-F_xXzZ?]+|"
    r"[A-Za-z_$][\w$]*|\d+|===|!==|<=|>=|==|!=|<<|>>|&&|\|\||\S"
)


def tokens(text):
    return [m.group() for m in TOKEN.finditer(text)
            if not m.group().startswith(("//", "/*", '"'))]


def matched(ts, index, opening, closing, direction=1):
    depth = 0
    for i in range(index, len(ts) if direction == 1 else -1, direction):
        if ts[i] == opening:
            depth += 1
        elif ts[i] == closing:
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("unbalanced RTL delimiters")


def inspect(path):
    ts = tokens(path.read_text())
    constants = set()
    for i, token in enumerate(ts):
        if token not in ("parameter", "localparam"):
            continue
        depth = 0
        for j in range(i+1, len(ts)):
            if ts[j] in ("(", "[", "{"):
                depth += 1
            if ts[j] in (")", "]", "}"):
                depth -= 1
            if depth < 0 or ts[j] == ";" and depth == 0:
                break
            if ts[j] == "=" and re.fullmatch(r"[A-Za-z_$][\w$]*", ts[j-1]):
                constants.add(ts[j-1])
    violations = []
    operators = []
    for i, token in enumerate(ts):
        if token not in ("/", "%"):
            continue
        left = i-1
        if ts[left] == ")":
            left = matched(ts, left, ")", "(", -1)
        right = i+1
        if ts[right] == "(":
            right = matched(ts, right, "(", ")")
        operands = ts[left:i] + ts[i+1:right+1]
        identifiers = {t for t in operands if re.fullmatch(r"[A-Za-z_$][\w$]*", t)}
        record = {"operator": token, "operands": operands,
                  "constant_identifiers": sorted(identifiers)}
        operators.append(record)
        if not identifiers <= constants:
            violations.append({"runtime_arithmetic": record})
    sequential_blocks = 0
    for i, token in enumerate(ts):
        if token != "always" or i+2 >= len(ts) or ts[i+1:i+3] != ["@", "("]:
            continue
        sensitivity_end = matched(ts, i+2, "(", ")")
        if not ({"posedge", "negedge"} & set(ts[i+3:sensitivity_end])):
            continue
        sequential_blocks += 1
        begin = sensitivity_end+1
        if ts[begin] != "begin":
            raise ValueError("sequential block without explicit begin/end")
        end = matched(ts, begin, "begin", "end")
        j = begin+1
        while j < end:
            if ts[j] == "for":
                if ts[j+1] != "(":
                    raise ValueError("malformed for")
                j = matched(ts, j+1, "(", ")")+1
                continue
            if ts[j] == "=":
                violations.append({"sequential_blocking_assignment": ts[max(begin, j-5):j+4]})
            j += 1
    return {"file": str(path), "sequential_blocks": sequential_blocks,
            "constant_operators": operators, "violations": violations}
