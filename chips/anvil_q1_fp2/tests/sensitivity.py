"""Disposable RTL mutations rejected by unchanged public-interface stimuli."""

import difflib
import json


MUTATIONS = (
    ("group-scale", "rtl/anvil_q1_fp2_bfp_tensor_array.sv",
     "a_scale[(g<32 ? 0 : 8)+:8]", "a_scale[0+:8]", "tensor", "NUMERICAL"),
    ("rounding", "rtl/anvil_q1_fp2_00_pkg.sv",
     "rounded={1'b0,kept}+{24'd0,guard_bit && (sticky_bit || kept[0])};",
     "rounded={1'b0,kept}+{24'd0,guard_bit};", "tensor", "NUMERICAL"),
    ("rsqrt-seed", "rtl/anvil_q1_fp2_fast_rsqrt.sv",
     "32'h5f3759df", "32'h5f000000", "rsqrt", "NUMERICAL"),
    ("residual-routing", "rtl/anvil_q1_fp2_epilogue_fusion.sv",
     "add_b=residual_value;", "add_b=32'd0;", "epilogue", "NUMERICAL"),
    ("online-rescaling", "rtl/anvil_q1_fp2_flash_attn.sv",
     "alpha<=exp_result[0];", "alpha<=32'h3f800000;", "attention", "NUMERICAL"),
    ("response-ownership", "rtl/anvil_q1_fp2_ddr_pingpong.sv",
     "response_data[ddr_rsp_id]<=ddr_rsp_rdata;",
     "response_data[!ddr_rsp_id]<=ddr_rsp_rdata;", "ddr", "DDR RESPONSE OWNERSHIP"),
    ("clear-priority", "rtl/anvil_q1_fp2_telemetry_csr.sv",
     "if (clear_event) begin", "if (1'b0 && clear_event) begin", "csr", "CSR cycle="),
)


class Variant:
    def __init__(self, parent, stem, overrides=None):
        self.parent = parent
        self.prefix = stem
        self.path = parent.path / stem
        self.relative = parent.relative / stem
        self.path.mkdir()
        self.receipt = parent.receipt
        self.source_overrides = overrides or {}

    def version(self, tool):
        self.parent.version(tool)

    def command(self, argv, stem, **kwargs):
        return self.parent.command(argv, self.prefix + "-" + stem, **kwargs)


def sensitivity(run, root, compile_and_run, simulate_pipeline, tensor_vectors,
                unary_vectors, simulate_commands, simulate_ddr, simulate_csr):
    results = []
    for name, source, before, after, kind, assertion in MUTATIONS:
        original = (root / source).read_text()
        if original.count(before) != 1:
            raise AssertionError(f"{name}: mutation anchor must occur exactly once")
        mutated = original.replace(before, after)
        mutation_path = run.path / (name + ".sv")
        mutation_path.write_text(mutated)
        (run.path / (name + ".diff")).write_text("".join(difflib.unified_diff(
            original.splitlines(True), mutated.splitlines(True),
            fromfile=source, tofile=str(mutation_path.relative_to(root)),
        )))
        controls = Variant(run, name + "-control")
        mutant = Variant(run, name + "-mutant", {source: str(mutation_path.relative_to(root))})

        def experiment(variant):
            if kind in ("tensor", "rsqrt"):
                records = tensor_vectors(17, 4096) if kind == "tensor" else unary_vectors(
                    kind, 17, 4096)
                simulate_pipeline(variant, kind, records, 17, "verilator")
            elif kind in ("epilogue", "attention"):
                simulate_commands(variant, kind, 17, 64 if kind == "attention" else 256,
                                  "verilator", compile_and_run)
            elif kind == "ddr":
                simulate_ddr(variant, 17, "verilator", compile_and_run)
            else:
                simulate_csr(variant, 17, "verilator", compile_and_run, 64)

        experiment(controls)
        start = len(run.receipt["commands"])
        try:
            experiment(mutant)
        except RuntimeError:
            commands = run.receipt["commands"][start:]
            compilations = [c for c in commands if "-compile" in c["stdout"]]
            simulations = [c for c in commands if "-simulate" in c["stdout"]]
            if not compilations or any(c["exit_code"] != 0 for c in compilations):
                raise AssertionError(f"{name}: compiler rejection is not defect sensitivity")
            if len(simulations) != 1:
                raise AssertionError(f"{name}: missing actual simulation")
            failed = simulations[0]
            logs = "".join((root / failed[key]).read_text() for key in ("stdout", "stderr"))
            if failed["timed_out"] or failed["exit_code"] in (None, 0) or assertion not in logs:
                raise AssertionError(f"{name}: not the required behavioral assertion")
            results.append({
                "mutation": name, "control": "passed", "mutant": "assertion-rejected",
                "assertion": assertion, "simulation_stdout": failed["stdout"],
                "simulation_stderr": failed["stderr"],
            })
            run.receipt["comparisons"].append(results[-1])
        else:
            raise AssertionError(f"{name}: mutation escaped unchanged assertions")
    (run.path / "mutation-results.json").write_text(json.dumps(results, indent=2) + "\n")
