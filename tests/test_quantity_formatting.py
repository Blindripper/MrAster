import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from aster_multi_bot import format_qty


class FormatQuantityTests(unittest.TestCase):
    def test_removes_binary_noise_from_quantity(self):
        qty = 7318.400000000001
        step = 0.1
        self.assertEqual(format_qty(qty, step), "7318.4")

    def test_respects_step_precision(self):
        qty = 12.3456789
        step = 0.0001
        self.assertEqual(format_qty(qty, step), "12.3456")

    def test_handles_integer_steps(self):
        qty = 19.999
        step = 1.0
        self.assertEqual(format_qty(qty, step), "19")


if __name__ == "__main__":
    unittest.main()
