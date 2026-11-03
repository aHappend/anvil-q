import unittest
from fractions import Fraction

from reference import (bf16_to_q16, committed_block, dequantize, encode_ieee,
                       fp8_value, pow2, quantize_group)
from transformer_reference import (Geometry, Target, WeightImage, exp_q24, fp8_roundtrip,
                                   matvec, rms, round_boundary, silu, trunc_div)


class NumericalReferenceTests(unittest.TestCase):
    def test_ieee_halfway_and_gradual_underflow(self):
        self.assertEqual(encode_ieee(1 + pow2(-24), 23), 0x3F800000)
        self.assertEqual(encode_ieee(1 + 3 * pow2(-24), 23), 0x3F800002)
        self.assertEqual(encode_ieee(pow2(-150), 23), 0)
        self.assertEqual(encode_ieee(3 * pow2(-150), 23), 2)
        self.assertEqual(encode_ieee(pow2(-126) - pow2(-150), 23), 0x00800000)
        self.assertEqual(encode_ieee(pow2(128), 23), 0x7F800000)

    def test_e4m3fn_special_codes(self):
        self.assertEqual(fp8_value(1), Fraction(1, 512))
        self.assertEqual(fp8_value(0x7E), 448)
        self.assertEqual(fp8_value(0xFE), -448)
        self.assertEqual(fp8_value(0x78), 256)
        with self.assertRaises(ValueError):
            fp8_value(0x7F)
        self.assertEqual(dequantize(0x80, 0x3F800000), (0x80000000, 0x8000, 0))
        self.assertEqual(dequantize(1, 0x3F800000), (0x3B000000, 0x3B00, 0))
        self.assertEqual(dequantize(0x7E, 0x3F800000), (0x43E00000, 0x43E0, 0))
        self.assertEqual(dequantize(0x7F, 0x3F800000), (0, 0, 1))
        self.assertEqual(dequantize(0, 0), (0, 0, 1))
        self.assertEqual(dequantize(0x7E, 0x7F7FFFFF), (0, 0, 1))

    def test_bf16_double_rounding_and_q16(self):
        self.assertEqual(dequantize(0x38, 0x3F808000), (0x3F808000, 0x3F80, 0))
        self.assertEqual(dequantize(0x38, 0x3F818000), (0x3F818000, 0x3F82, 0))
        self.assertEqual(dequantize(0x38, 0x3FFF8000), (0x3FFF8000, 0x4000, 0))
        self.assertEqual(bf16_to_q16(0x3700), (1, 0))
        self.assertEqual(bf16_to_q16(0xB700), (0xFFFFFFFF, 0))
        self.assertEqual(bf16_to_q16(0x36FF), (0, 0))
        self.assertEqual(bf16_to_q16(0x7F7F), (0x7FFFFFFF, 0))
        self.assertEqual(bf16_to_q16(0xFF7F), (0x80000000, 0))
        self.assertEqual(bf16_to_q16(0x7FC0), (0, 1))

    def test_group_scale_midpoints_and_saturation(self):
        self.assertEqual(quantize_group([0, 0]), (0x3F800000, [0, 0]))
        self.assertEqual(quantize_group([448 << 16, 64, 192, -64, -192]),
                         (0x3F800000, [0x7E, 0, 2, 0x80, 0x82]))
        self.assertEqual(quantize_group([-0x80000000, 0x7FFFFFFF]),
                         (0x43000000, [0xF8, 0x78]))

    def test_first_mismatch_and_visible_eos(self):
        self.assertEqual(committed_block(0, [1, 2, 3, 4], [1, 9, 3, 4],
                                         4, 5, 1, 12, 99),
                         ([0, 1, 9], 1, True))
        self.assertEqual(committed_block(0, [1, 2, 3, 4], [1, 2, 3, 4],
                                         4, 5, 1, 12, 2),
                         ([0, 1, 2], 2, False))
        self.assertEqual(committed_block(0, [1, 2, 3, 4], [1, 2, 3, 4],
                                         4, 5, 11, 12, 99),
                         ([0], 0, False))

    def test_native_tensor_boundaries(self):
        self.assertEqual(round_boundary(32768), 1)
        self.assertEqual(round_boundary(-32768), -1)
        self.assertEqual(round_boundary((1 << 64)-1), 0x7FFFFFFF)
        self.assertEqual(trunc_div(-7, 3), -2)
        self.assertEqual(exp_q24(0), 1 << 24)
        self.assertEqual(exp_q24(-(16 << 16)-1), 0)
        self.assertEqual(silu(0), 0)
        self.assertEqual(matvec([[65536, -65536]], [65536, 32768]), [32768])
        self.assertEqual(rms([0]*8, [65536]*8), [0]*8)
        self.assertEqual(rms([65536]*8, [65536]*8), [65536]*8)
        self.assertEqual(fp8_roundtrip([65536, -65536, 0]), [65536, -65536, 0])

    def test_native_fixture_is_nonzero_and_sensitive(self):
        image = WeightImage(Geometry(layers=2), 17)
        target = Target(image)
        baseline = target.process(3)
        self.assertTrue(any(value != 0 for value in baseline))
        self.assertGreater(len(set(baseline)), 1)
        self.assertTrue(any(value for row in target.raw_cache[0] for value in row))
        changed = WeightImage(Geometry(layers=2), 17)
        changed.layers[1]["experts"][changed.geometry.experts]["bias"][2][0] += 65536
        self.assertNotEqual(baseline, Target(changed).process(3))


if __name__ == "__main__":
    unittest.main()
