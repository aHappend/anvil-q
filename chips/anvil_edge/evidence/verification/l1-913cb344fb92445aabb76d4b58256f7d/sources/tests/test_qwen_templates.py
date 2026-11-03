"""Rendering-only regressions; synthetic fixtures make no RTL coverage claim."""

from pathlib import Path
import re
import struct
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qwen_tables as qwen


class QwenTemplateTests(unittest.TestCase):
    def setUp(self):
        self.evidence = Mock()
        self.evidence.path = Path("evidence/preparation/rendering-fixture")
        self.evidence.relative.side_effect = str
        self.info = {
            "memory_bytes": 64,
            "maximum_token_bytes": 1,
            "fragments": [
                {"kind": kind, "base": qwen.BASE + index * 64,
                 "data_base": qwen.BASE + index * 64 + 32, "bytes": 64,
                 "record_count": 1, "file": f"qwen-{kind:03x}.bin"}
                for index, kind in enumerate(qwen.WIDTHS)
            ],
        }

    def assert_memory(self, bench, replacement):
        self.assertIn(replacement, bench)
        self.assertEqual(bench.count("reg [31:0] fragment_memory["), 1)
        self.assertEqual(bench.count("function automatic [31:0] memory("), 1)
        self.assertLess(bench.index("reg [31:0] fragment_memory["),
                        bench.index("function automatic [31:0] memory("))
        self.assertIn('initial $readmemh(', bench)
        self.assertIn('address[1:0]!=0 || !(', bench)
        self.assertIn('QWEN_FRAGMENT_READ_BOUNDS', bench)
        self.assertIn("memory=fragment_memory[(address-64'h100000)>>2];", bench)
        self.assertNotRegex(bench, r"@[A-Z][A-Z0-9_]*@")

    def test_all_three_actual_callers_render(self):
        pieces = [b"a"] * qwen.VOCABULARY
        records = bytes(32) + struct.pack("<QII", 0, 1, 1) * qwen.VOCABULARY
        cases = (
            ("detokenizer", lambda: qwen.detokenizer_probe(
                self.evidence, self.info, pieces, list(range(256)), 17),
             {0x201, 0x202}),
            ("ranked_bpe", lambda: qwen.bpe_probe(
                self.evidence, self.info, list(range(256)), [(104, 101, 256, 0)], 17),
             {0x204}),
            ("special_trie", lambda: qwen.trie_probe(
                self.evidence, self.info, {"added_tokens": [{"id": 151643}]}, 17),
             {0x201, 0x202, 0x205, 0x206, 0x20A}),
        )
        for name, run, allowed in cases:
            with self.subTest(caller=name), patch.object(Path, "read_bytes",
                                                       return_value=records):
                self.evidence.simulate.reset_mock()
                run()
                self.evidence.simulate.assert_called_once()
                args, kwargs = self.evidence.simulate.call_args
                self.assertEqual(kwargs["simulator"], "verilator")
                self.assert_memory(args[1], qwen.memory_function(
                    self.evidence, self.info, allowed))

    def test_all_callers_reject_unresolved_fields_before_simulation(self):
        from protocol import DETOKENIZER
        from text import BENCH
        replacement = qwen.memory_function(self.evidence, self.info, {0x204})
        for name, template in (("detokenizer", DETOKENIZER),
                               ("ranked_bpe", BENCH), ("special_trie", BENCH)):
            with self.subTest(caller=name):
                bench = qwen.replace_memory(template, replacement)
                fields = set(re.findall(r"@([A-Z][A-Z0-9_]*)@", bench))
                substitutions = {key: "0" for key in fields}
                qwen.render_bench(bench, substitutions)
                with self.assertRaisesRegex(ValueError, "@UNRESOLVED_FIELD@"):
                    qwen.render_bench(bench + "\n@UNRESOLVED_FIELD@", substitutions)
                with self.assertRaisesRegex(ValueError, "@MEMORY_DECLARATIONS@"):
                    qwen.render_bench(bench + "\n@MEMORY_DECLARATIONS@", substitutions)


if __name__ == "__main__":
    unittest.main()
