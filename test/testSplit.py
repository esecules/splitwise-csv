import unittest
import sys
from money import Money
sys.path.append("../src")
from groupsplit import split

class APIInterfaceTests(unittest.TestCase):
    def test_splits(self):
        cases = [
            {"amount": "1.00", "ppl": 2, "expect": ("0.50","0.00")},
            {"amount": "1.00", "ppl": 3, "expect": ("0.33", "0.01")},
            {"amount": "12.97", "ppl": 5, "expect": ("2.59", "0.02")},
            {"amount": "52000", "ppl": 3, "expect": ("1733.33", "0.01")},
        ]
        for case in cases:
            expect = (Money(case['expect'][0], "CAD"), Money(case['expect'][1], "CAD"))
            self.assertEqual(expect, split(Money(case['amount'], "CAD"), case['ppl']))
