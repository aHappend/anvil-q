"""Literal-delay lowering controls, not RTL or performance acceptance."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cycle_driver import DELAY_TASK, external_delay_bench
from qwen_shell import SHELL


class DelayLoweringTests(unittest.TestCase):
    def test_exact_literals_and_unmodified_edge_waits(self):
        source = """module bench(input wire clk);
  initial begin
    #1ps; @(posedge clk); #1; @(negedge clk); #1 ;
    if (1) $fatal(1,"ORIGINAL_ASSERTION");
  end
endmodule
"""
        candidate, counts = external_delay_bench(source)
        self.assertEqual(counts, {"1ps": 1, "1ns": 2})
        self.assertIn("@(posedge clk); verification_delay(1000);", candidate)
        self.assertIn("@(negedge clk); verification_delay(1000);", candidate)
        self.assertIn('if (1) $fatal(1,"ORIGINAL_ASSERTION");', candidate)
        self.assertEqual(candidate.count(DELAY_TASK), 1)
        self.assertIn("wait (verification_alarms[slot]!=previous_value);", candidate)
        self.assertNotRegex(candidate, r"#(?!\s*\()")

    def test_shell_scoreboards_and_stimulus_are_not_rewritten(self):
        bench = SHELL.replace(
            "module bench;", "module bench(input wire clk);", 1
        ).replace(
            "  reg clk=0,rst_n;\n  always #5 clk=~clk;", "  reg rst_n;", 1
        ).replace("#0;", "#1ps;")
        # Instantiation placeholders are populated by shell_case before lowering.
        bench = bench.replace("@CAPACITY@", "257").replace("@EXTENT@", "65536")
        candidate, counts = external_delay_bench(bench)
        self.assertEqual(counts["1ps"], 1)
        self.assertGreater(counts["1ns"], 10)
        restored = candidate.replace(
            "module bench(input wire clk, input wire [7:0] verification_alarms);",
            "module bench(input wire clk);", 1
        ).replace(DELAY_TASK + "\nendmodule", "endmodule", 1)
        restored = restored.replace("verification_delay(1);", "#1ps;")
        restored = restored.replace("verification_delay(1000);", "#1;")
        self.assertEqual(restored, bench)
        # These remain independent public-pin checks, not candidate substitutes.
        for assertion in ("QWEN_SHELL_NUMERICAL_WRITE", "QWEN_SHELL_DRAIN",
                          "QWEN_SHELL_PREFILL_FEEDBACK", "QWEN_SHELL_UART_BIT",
                          "QWEN_SHELL_HOST_INTERVENTION_OR_BOOT_REENTRY"):
            self.assertEqual(candidate.count(assertion), bench.count(assertion))
        self.assertNotIn("dut.", candidate)

    def test_parameter_override_is_not_a_delay(self):
        source = """module bench(input wire clk);
  unit #(.DEPTH(3)) dut();
  initial begin #1; $finish; end
endmodule
"""
        candidate, _ = external_delay_bench(source)
        self.assertIn("unit #(.DEPTH(3)) dut();", candidate)

    def test_unsupported_delays_fail_closed(self):
        for delay in ("#0;", "#2;", "#1ns;", "#10;", "#(1);"):
            with self.subTest(delay=delay):
                source = f"""module bench(input wire clk);
  initial begin #1; {delay} $finish; end
endmodule
"""
                # #(1) is not a named module parameter assignment. It must not be
                # mistaken for a supported delay by the candidate renderer.
                with self.assertRaises(ValueError):
                    external_delay_bench(source)

    def test_unknown_module_and_identifier_collisions_fail_closed(self):
        for source in (
            "module bench; initial #1; endmodule",
            "module bench(input wire clk); endmodule",
            "module bench(input wire clk); initial #1; endmodule\n"
            "module second; endmodule",
            "module bench(input wire clk); integer verification_delay; "
            "initial #1; endmodule",
            "module bench(input wire clk); integer verification_alarms; "
            "initial #1; endmodule",
        ):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    external_delay_bench(source)


if __name__ == "__main__":
    # Match the preparation runner's artifact-directory argument without writing
    # outside the supplied fresh project evidence scope.
    output = Path(sys.argv.pop(1))
    if not output.is_dir():
        raise SystemExit("Expected an existing fresh evidence directory")
    unittest.main()
