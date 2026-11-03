"""Compile disposable mutants and require unchanged functional assertion kills."""

import difflib
import json
from pathlib import Path
import shutil

from protocol import UART, bpe_test, controller_test, detokenizer_test
from storage import boot_test


def run_mutations(evidence, fifo_test):
    evidence.tools(("verilator",))
    root = Path(__file__).resolve().parent.parent

    def uart_test():
        bench = UART.replace("DIVISOR", "4").replace("@DEPTH@", "1").replace("SEED", "1")
        evidence.simulate("uart-d4-f1-s1", bench,
                          ["rtl/anvil_edge_fifo.sv", "rtl/anvil_edge_uart_io.sv"], 78)

    experiments = [
        ("uart-bit-order", "anvil_edge_uart_io.sv",
         "{1'b1, tx_fifo_data[7:0], 1'b0}",
         "{1'b1, tx_fifo_data[0], tx_fifo_data[1], tx_fifo_data[2], tx_fifo_data[3], "
         "tx_fifo_data[4], tx_fifo_data[5], tx_fifo_data[6], tx_fifo_data[7], 1'b0}",
         uart_test, "UART_TX_BIT"),
        ("fifo-corruption", "anvil_edge_fifo.sv",
         "out_valid ? data[read_ptr] : {WIDTH{1'b0}}",
         "out_valid ? (data[read_ptr] ^ 1'b1) : {WIDTH{1'b0}}",
         lambda: fifo_test(evidence, 3, 17), "FIFO_QUEUE"),
        ("merge-rank", "anvil_edge_ranked_bpe.sv",
         "!best_valid || record_rank<best_rank", "!best_valid || record_rank>best_rank",
         lambda: bpe_test(evidence, 17), "BPE_BYTES"),
        ("detokenizer-offset", "anvil_edge_detokenizer.sv",
         "bytes_data_start+{1'b0, cursor}", "bytes_data_start+{1'b0, cursor}+65'd4",
         lambda: detokenizer_test(evidence, 17, "ascii", [b"A"]), "DETOK_LOOKUP"),
        ("argmax-tie", "anvil_edge_autoregressive_fsm.sv",
         "!winner_valid || core_logit_data > winner_value",
         "!winner_valid || core_logit_data >= winner_value",
         lambda: controller_test(evidence, 1, 17), "CONTROLLER_FINISH_OVERTAKE"),
        ("prefill-token", "anvil_edge_autoregressive_fsm.sv",
         "issue_id <= prompt[prompt_index+1];", "issue_id <= prompt[prompt_index];",
         lambda: controller_test(evidence, 3, 17), "CONTROLLER_OPERATION"),
        ("eos-termination", "anvil_edge_autoregressive_fsm.sv",
         "if (winner_id == eos) state <= FINISH;",
         "if (1'b0) state <= FINISH;",
         lambda: controller_test(evidence, 1, 17), "CONTROLLER_ARGMAX"),
        ("boot-crc", "anvil_edge_image_loader.sv",
         "if ((~crc_value)!=payload_crc)", "if (1'b0)",
         lambda: boot_test(evidence, 257, 17, "crc"), "BOOT_REJECTION"),
        ("boot-acknowledgement", "anvil_edge_image_loader.sv",
         "if (ddr_rsp_error)", "if (1'b0)",
         lambda: boot_test(evidence, 257, 17, "ddr-error"), "BOOT_REJECTION"),
    ]
    results = []
    for name, filename, before, after, experiment, assertion in experiments:
        directory = evidence.path / ("mutation-" + name)
        directory.mkdir()
        copy = directory / "rtl"
        shutil.copytree(root / "rtl", copy)
        target = copy / filename
        original = target.read_text()
        if original.count(before) != 1:
            raise RuntimeError(f"Mutation target is ambiguous: {name}")
        changed = original.replace(before, after)
        target.write_text(changed, encoding="ascii")
        (directory / "mutation.diff").write_text("".join(difflib.unified_diff(
            original.splitlines(True), changed.splitlines(True),
            fromfile="rtl/" + filename, tofile="mutant/rtl/" + filename,
        )), encoding="ascii")
        evidence.source_overrides = {
            "rtl/" + path.name: evidence.relative(path) for path in sorted(copy.glob("*.sv"))
        }
        evidence.name_prefix = name + "-"
        previous_simulator = evidence.simulator_override
        evidence.simulator_override = "verilator"
        first_child = len(evidence.record["children"])
        failure = None
        try:
            experiment()
        except Exception as error:
            failure = error
        finally:
            evidence.source_overrides = {}
            evidence.name_prefix = ""
            evidence.simulator_override = previous_simulator
        children = evidence.record["children"][first_child:]
        simulation = [child for child in children
                      if Path(child["argv"][0]).name == "simulation"]
        compiles = [child for child in children if child["argv"][0] == "verilator"
                    and "--binary" in child["argv"]]
        if not compiles or any(child["exit_code"] != 0 for child in compiles):
            raise RuntimeError(f"Mutant {name} did not compile; not a functional kill") from failure
        if len(simulation) != 1:
            raise RuntimeError(f"Mutant {name} lacks an executed simulation") from failure
        result = simulation[0]
        output = ((root / result["stdout"]).read_text() +
                  (root / result["stderr"]).read_text())
        if (failure is None or result["exit_code"] == 0 or result["timed_out"] or
                not result["child_settled"] or not result["process_group_settled"] or
                "%Error:" not in output or assertion not in output):
            raise RuntimeError(f"Mutant {name} not killed by required {assertion}") from failure
        rows = [row for row in evidence.record["coverage"]
                if row.get("simulation_receipt") is result]
        if len(rows) != 1 or rows[0]["status"] != "failed":
            raise RuntimeError(f"Mutant {name} lacks an accounted failed functional simulation")
        rows[0].update(status="expected-functional-rejection", mutation_assertion=assertion)
        results.append({"name": name, "assertion": assertion, "status": "killed",
                        "simulation": result, "diff": evidence.relative(directory / "mutation.diff")})
    if len(results) < 8:
        raise RuntimeError("Required eight mutation categories were not killed")
    (evidence.path / "mutation-results.json").write_text(json.dumps(results, indent=2) + "\n")
    evidence.record["coverage"].append({"name": "functional-mutations",
                                        "status": "passed", "killed": len(results),
                                        "results": evidence.relative(
                                            evidence.path / "mutation-results.json")})
