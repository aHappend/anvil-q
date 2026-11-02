"""Independent, public-pin arithmetic comparisons and frozen RMS discriminators.

Primitive acceptance is edge zero. Expected first post-edge valid offsets are
mul32=3, mul96x32=7, add128=3, round_sat=0, udiv128=129,
sdiv128=131, and isqrt128=65. Result retirement is a separate later edge.
The generated bench checks every intervening edge, rather than hiding latency
inside a blocking arithmetic wrapper. No hierarchical DUT observations are used.

RMS intermediates are compared through separately driven public arithmetic
interfaces; complete RMSNorm output comparisons belong to the memory leaf bench.
These primitive checks alone do not certify the integrated RMSNorm datapath.
For the fixed H=24, x=[1,0,...], gamma=65536 vector:
u=1099511300096, root remainder=11184785, reciprocal remainder=1638400,
and outputs=[256,0,...,0]. These are integer results, not approximations.
"""

import argparse
from dataclasses import dataclass
import json
from math import isqrt
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagnostic import simulate
from evidence import Evidence, rel
from reference import Q16, exp_q24, exp_trace, rms_trace, round_sat, silu, trunc_div


def literal(width, value):
    return f"{width}'h{value & ((1 << width)-1):0{(width+3)//4}x}"


def rms_alternatives(trace):
    """Incorrect alternatives, used only to establish separating stimulus."""
    x, gamma = trace["x"], trace["gamma"]
    s, mean, e, d, u = (trace[name] for name in ("S", "M", "E", "d", "u"))
    rounded_mean = (s * (1 << 32) + len(x)//2) // len(x)
    rounded_root = d + (4*e >= (2*d+1)**2)
    rounded_reciprocal = ((1 << 64) + d//2) // d
    premature = [round_sat(round_sat(v*u, 16)*g, 16)
                 for v, g in zip(x, gamma, strict=True)]
    direct = [round_sat(trunc_div(v*g*(1 << 64), d), 48)
              for v, g in zip(x, gamma, strict=True)]
    parent_d = isqrt(mean + 18446744073710)
    parent_u = (1 << 64) // parent_d
    parent_epsilon = [round_sat(v*g*parent_u, 48)
                      for v, g in zip(x, gamma, strict=True)]
    return dict(rounded_mean=rounded_mean, rounded_root=rounded_root,
                rounded_reciprocal=rounded_reciprocal,
                premature_rounding=premature, direct_division=direct,
                parent_epsilon=parent_epsilon)


def rms_discriminators():
    """Fixed constructions followed by a deterministic independently searched set."""
    vectors = [
        ("nonintegral_mean", [1]+[0]*23, [Q16]*24),
        ("zero", [0]*24, [Q16]*24),
        ("signed_extremes", [-(1 << 31), (1 << 31)-1]*12,
         [(1 << 31)-1, -(1 << 31)]*12),
    ]
    found = set()
    rng = random.Random(0xD1_524D53)
    for attempt in range(20000):
        limit = (16, 65536, 1 << 24, (1 << 31)-1)[attempt % 4]
        x = [rng.randint(-limit, limit) for _ in range(24)]
        # Large gamma magnifies reciprocal error; smaller gamma keeps the
        # comparison nonsaturated instead of hiding it behind a rail.
        gamma = [rng.randint(-((1 << 30)-1), (1 << 30)-1) for _ in range(24)]
        trace = rms_trace(x, gamma)
        alternatives = rms_alternatives(trace)
        separating = set()
        for name in ("rounded_mean", "rounded_root", "rounded_reciprocal"):
            field = dict(rounded_mean="M", rounded_root="d", rounded_reciprocal="u")[name]
            if alternatives[name] != trace[field]:
                separating.add(name)
        for name in ("premature_rounding", "direct_division", "parent_epsilon"):
            if any(actual != wrong and -(1 << 31) < actual < (1 << 31)-1
                   and -(1 << 31) < wrong < (1 << 31)-1
                   for actual, wrong in zip(trace["outputs"], alternatives[name], strict=True)):
                separating.add(name)
        if separating - found:
            vectors.append((f"searched_{attempt}", x, gamma))
            found.update(separating)
        if len(found) == 6:
            break
    required = {"rounded_mean", "rounded_root", "rounded_reciprocal",
                "premature_rounding", "direct_division", "parent_epsilon"}
    if found != required:
        raise AssertionError(f"missing RMS separating constructions: {sorted(required-found)}")
    traces = []
    for name, x, gamma in vectors:
        trace = rms_trace(x, gamma)
        trace.update(name=name, alternatives=rms_alternatives(trace))
        traces.append(trace)
    first = traces[0]
    if (first["S"], first["M"], first["mean_remainder"], first["E"], first["d"]) != (
            1, 178956970, 16, (1 << 48)+178956970, 16777221):
        raise AssertionError("fixed nonintegral RMS construction disagrees with specification")
    if (first["u"], first["root_remainder"], first["reciprocal_remainder"],
        first["outputs"]) != (1099511300096, 11184785, 1638400, [256]+[0]*23):
        raise AssertionError("fixed RMS reciprocal/output construction disagrees")
    return traces


@dataclass
class Primitive:
    name: str
    module: str
    inputs: dict
    outputs: dict
    cases: list
    latency: int | None
    parameters: str = ""


def primitives(traces):
    rng = random.Random(203)
    scalar_pairs = [(0, 0), (1, -1), (-(1 << 31), -(1 << 31)),
                    (-(1 << 31), (1 << 31)-1), ((1 << 31)-1, (1 << 31)-1)]
    scalar_pairs += [(rng.randint(-(1 << 31), (1 << 31)-1),
                      rng.randint(-(1 << 31), (1 << 31)-1)) for _ in range(48)]
    wide_pairs = [(a, b) for a in (-(1 << 95), (1 << 95)-1, -1, 0,
                                  0x8000000080000000, -0x8000000080000000)
                  for b in (-(1 << 31), -1, 1, (1 << 31)-1)]
    wide_pairs += [(rng.randint(-(1 << 95), (1 << 95)-1), b)
                   for _, b in scalar_pairs]
    add_pairs = [(0, 0), ((1 << 127)-1, 1), (-(1 << 127), -1),
                 ((1 << 96)-1, 1), (-(1 << 96), -1)]
    add_pairs += [(rng.randint(-(1 << 127), (1 << 127)-1),
                   rng.randint(-(1 << 127), (1 << 127)-1)) for _ in range(32)]
    divisions = [(0, 1), ((1 << 128)-1, 1), ((1 << 128)-1, (1 << 64)-1)]
    roots = [0, 1, 2, 3, 4, (1 << 128)-1]
    for trace in traces:
        divisions += [(trace["S"] << 32, 24), (1 << 64, trace["d"])]
        roots.append(trace["E"])
        scalar_pairs.extend(zip(trace["x"], trace["gamma"], strict=True))
        for p in trace["P"]:
            lo = trace["u"] & 0xffffffff
            hi = trace["u"] >> 32
            wide_pairs += [(p, lo if lo < (1 << 31) else lo-(1 << 32)), (p, hi)]
    division_cases = [(dict(numerator=n, denominator=d),
                       dict(quotient=n//d, remainder=n % d, out_error=0))
                      for n, d in divisions]
    # A zero divisor's numerical result is unspecified; compare its explicit
    # error and the unchanged documented latency, not a success-shaped value.
    division_cases.append((dict(numerator=123, denominator=0), dict(out_error=1)))
    signed_divisions = [(n, 131072) for n in (
        65536, -65536, 131073, -131073, 131072, -131072, -(1 << 127), (1 << 127)-1)]
    signed_divisions += [(rng.randint(-(1 << 127), (1 << 127)-1),
                          rng.randint(1, (1 << 32)-1)) for _ in range(24)]
    signed_cases = [(dict(numerator=n, denominator=d),
                     dict(quotient=trunc_div(n, d), remainder=abs(n) % d, out_error=0))
                    for n, d in signed_divisions]
    signed_cases.append((dict(numerator=-1, denominator=0), dict(out_error=1)))
    result = [
        Primitive("mul32", "anvil_d1_mul32", dict(in_a=32, in_b=32),
                  dict(out_product=64), [(dict(in_a=a, in_b=b), dict(out_product=a*b))
                                        for a, b in scalar_pairs], 3),
        Primitive("mul96", "anvil_d1_mul96x32", dict(in_a=96, in_b=32),
                  dict(out_product=128), [(dict(in_a=a, in_b=b), dict(out_product=a*b))
                                         for a, b in wide_pairs], 7),
        Primitive("udiv", "anvil_d1_udiv", dict(numerator=128, denominator=64),
                  dict(quotient=128, remainder=64, out_error=1), division_cases, 129,
                  "#(.NUM_W(128),.DEN_W(64))"),
        Primitive("sdiv", "anvil_d1_sdiv", dict(numerator=128, denominator=32),
                  dict(quotient=129, remainder=32, out_error=1), signed_cases, 131,
                  "#(.NUM_W(128),.DEN_W(32))"),
        Primitive("root", "anvil_d1_isqrt", dict(radicand=128),
                  dict(root=64, remainder=65),
                  [(dict(radicand=n), dict(root=isqrt(n), remainder=n-isqrt(n)**2))
                   for n in roots], 65),
    ]
    for subtract in (0, 1):
        cases = []
        for a, b in add_pairs:
            value = a-b if subtract else a+b
            cases.append((dict(in_a=a, in_b=b), dict(out_sum=value,
                          out_error=int(not -(1 << 127) <= value < (1 << 127)))))
        result.append(Primitive(f"add{subtract}", "anvil_d1_add128",
                                dict(in_a=128, in_b=128), dict(out_sum=128, out_error=1),
                                cases, 3, f"#(.SUBTRACT({subtract}))"))
    for shift in (0, 16, 24, 32, 48, 96):
        values = [0, -(1 << 127), (1 << 127)-1]
        if shift:
            half = 1 << (shift-1)
            values += [v for k in (-2147483648, -2, -1, 0, 1, 2147483647)
                       for v in ((k << shift)+half-1, (k << shift)+half,
                                 (k << shift)+half+1)]
        if shift == 48:
            values += [t for trace in traces for t in trace["T"]]
        result.append(Primitive(f"round{shift}", "anvil_d1_round_sat", dict(in_value=128),
                                dict(out_value=32),
                                [(dict(in_value=n), dict(out_value=round_sat(n, shift)))
                                 for n in values], 0, f"#(.SHIFT({shift}))"))
    arguments = [0, 1, -1, -Q16, -16*Q16, -16*Q16-1, -(1 << 31), (1 << 31)-1]
    arguments += [rng.randint(-16*Q16, 0) for _ in range(32)]
    result += [
        Primitive("exp", "anvil_d1_exp", dict(in_x=33), dict(out_value=25, out_error=1),
                  [(dict(in_x=x), dict(out_value=exp_q24(x), out_error=0))
                   for x in arguments], None),
        Primitive("silu", "anvil_d1_silu", dict(in_x=32), dict(out_value=32, out_error=1),
                  [(dict(in_x=x), dict(out_value=silu(x), out_error=0))
                   for x in arguments+[-x for x in arguments if -(1 << 31) < -x < (1 << 31)]],
                  None),
    ]
    return result


def primitive_bench(evidence):
    traces = rms_discriminators()
    tests = primitives(traces)
    # Freeze all input integers, intermediate quotients/remainders, roots and
    # expected output integers before compiling or executing the DUT.
    (evidence.path / "numerical-fixtures.json").write_text(json.dumps(dict(
        rms=traces, exponential=[exp_trace(case[0]["in_x"])
                                for test in tests if test.name == "exp" for case in test.cases],
        primitives=[vars(test) for test in tests]), indent=2)+"\n")
    declarations, instances, reset_outputs, tasks, calls = [], [], [], [], []
    for test in tests:
        name = test.name
        declarations.extend(f"reg [{w-1}:0] {name}_{port}=0;"
                            for port, w in test.inputs.items())
        declarations.extend(f"wire [{w-1}:0] {name}_{port};"
                            for port, w in test.outputs.items())
        declarations += [f"reg {name}_iv=0,{name}_or=0;",
                         f"wire {name}_ir,{name}_ov;"]
        bindings = [".clk(clk)", ".rst_n(rst_n)", ".flush(flush)",
                    f".in_valid({name}_iv)", f".in_ready({name}_ir)",
                    f".out_valid({name}_ov)", f".out_ready({name}_or)"]
        bindings.extend(f".{port}({name}_{port})" for port in test.inputs | test.outputs)
        instances.append(f"{test.module} {test.parameters} {name}_device"
                         f" ({','.join(bindings)});")
        signals = [f"{name}_ir", f"{name}_ov"]+[f"{name}_{p}" for p in test.outputs]
        reset_outputs.extend(signals)
        payload = "{"+",".join(f"{name}_{p}" for p in test.outputs)+"}"
        width = sum(test.outputs.values())
        task = [f"task automatic run_{name}(input integer index);",
                f"reg [{width}:0] held;", "integer elapsed;",
                "begin", "@(negedge clk);",
                f"while ({name}_ir !== 1'b1) @(negedge clk);"]
        task.append("case(index)")
        for index, (inputs, _) in enumerate(test.cases):
            assigns = " ".join(f"{name}_{p}={literal(test.inputs[p], v)};"
                               for p, v in inputs.items())
            task.append(f"{index}: begin {assigns} end")
        task += ["default: $fatal(1,\"BAD_CASE\");", "endcase",
                 f"{name}_iv=1; @(posedge clk);",
                 f"if ({name}_ir !== 1'b1) $fatal(1,\"ACCEPT_{name}\");",
                 "#1; elapsed=0;"]
        if test.latency is None:
            task += [f"while ({name}_ov !== 1'b1) begin",
                     f"if ({name}_ov !== 1'b0) $fatal(1,\"VALID_XZ_{name}\");",
                     f"@(negedge clk); {name}_iv=0; @(posedge clk); #1; elapsed=elapsed+1;",
                     "end"]
        else:
            task += [f"repeat ({test.latency}) begin",
                     f"if ({name}_ov !== 1'b0) $fatal(1,\"EARLY_VALID_{name} edge=%0d\",elapsed);",
                     f"@(negedge clk); {name}_iv=0; @(posedge clk); #1; elapsed=elapsed+1;",
                     "end",
                     f"if ({name}_ov !== 1'b1) $fatal(1,\"LATE_VALID_{name} edge=%0d\",elapsed);"]
        task.append("case(index)")
        for index, (_, outputs) in enumerate(test.cases):
            checks = " ".join(
                f'if ({name}_{p} !== {literal(test.outputs[p], v)}) '
                f'$fatal(1,"NUMERICAL_{name}_{p} case={index} actual=%h expected=%h",'
                f'{name}_{p},{literal(test.outputs[p], v)});'
                for p, v in outputs.items())
            task.append(f"{index}: begin {checks} end")
        task += ["endcase", f"held={{1'b1,{payload}}};",
                 f"@(negedge clk); {name}_iv=0;",
                 "repeat(3) begin @(posedge clk);",
                 f"if ({{{name}_ov,{payload}}} !== held) $fatal(1,\"STALLED_{name}\");",
                 "#1;",
                 f"if ({{{name}_ov,{payload}}} !== held) $fatal(1,\"STALLED_POST_{name}\");",
                 "end", f"@(negedge clk); {name}_or=1; @(posedge clk); #1;",
                 f"if ({name}_ov !== 1'b0) $fatal(1,\"RETIRE_{name}\");",
                 f"@(negedge clk); {name}_or=0;",
                 "comparisons=comparisons+1;", "end endtask"]
        tasks.append("\n".join(task))
        calls.append(f"for (integer n=0;n<{len(test.cases)};n=n+1) run_{name}(n);")
    count = sum(len(test.cases) for test in tests)
    reset_payload = "{"+",".join(reset_outputs)+"}"
    bench = "\n".join([
        "module tb; reg clk=0; always #5 clk=~clk;",
        "reg rst_n,flush=0; integer comparisons=0,reset_samples=0,watchdog=0;",
        'always @(posedge clk) begin watchdog=watchdog+1; '
        'if(watchdog>500000) $fatal(1,"NUMERICAL_CYCLE_BOUND"); end',
        *declarations, *instances,
        "task automatic check_reset; begin",
        f'if ({reset_payload} !== 0) $fatal(1,"RESET_XZ_OR_NONZERO t=%0t",$time);',
        "reset_samples=reset_samples+1; end endtask",
        "always @(posedge clk or negedge clk) if (!rst_n) check_reset();",
        *tasks, "initial begin rst_n=0;",
        "`ifdef VERILATOR", "#1;", "`else", "#0;", "`endif",
        "check_reset(); repeat(2) @(negedge clk); #1; rst_n=1;",
        *calls,
        f'if (comparisons!={count} || reset_samples<5) $fatal(1,"MISSING_COMPARISONS");',
        '$display("SUMMARY numerical_comparisons=%0d reset_samples=%0d",comparisons,reset_samples);',
        "$finish; end endmodule",
    ])
    (evidence.path / "numerical.sv").write_text(bench+"\n")
    return dict(primitive_cases=count, rms_traces=len(traces),
                fixed_rms_u=traces[0]["u"], fixed_rms_outputs=traces[0]["outputs"],
                rms_integrated_outputs_checked=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim", choices=("icarus", "verilator"), default="icarus")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    evidence = Evidence("numerical-"+args.sim, args.repair_of)
    try:
        summary = primitive_bench(evidence)
        summary["observations"] = simulate(evidence, "numerical.sv", args.sim)
        evidence.finish("passed", **summary)
        print(summary["observations"].strip())
    except Exception as exc:
        evidence.finish("failed", error=str(exc))
        print(str(exc), file=sys.stderr)
        print(rel(evidence.path / "receipt.json"), file=sys.stderr)
        return 1
    print(rel(evidence.path / "receipt.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
