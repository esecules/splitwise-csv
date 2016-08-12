import unittest
import sys
import subprocess
from money import Money
sys.path.append("../src")
from groupsplit import split, Splitwise

class UtilsTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(UtilsTests, self).__init__(*args, **kwargs)
        self.api = Splitwise()

    def test_splits(self):
        cases = [
            {"amount": "1.00", "ppl": 2, "expect": ("0.50","0.00")},
            {"amount": "1.00", "ppl": 3, "expect": ("0.33", "0.01")},
            {"amount": "12.97", "ppl": 5, "expect": ("2.59", "0.02")},
            {"amount": "52000.00", "ppl": 3, "expect": ("17333.33", "0.01")},
            {"amount": "1050.00", "ppl": 3, "expect": ("350.00", "0.00")},
        ]
        for case in cases:
            expect = (Money(case['expect'][0], "CAD"), Money(case['expect'][1], "CAD"))
            self.assertEqual(expect, split(Money(case['amount'], "CAD"), case['ppl']))

    def test_get_id(self):
        self.assertGreater(int(self.api.get_id()), 0)

    def test_get_groups(self):
        self.assertGreater(len(self.api.get_groups()), 0)

class SystemTests(unittest.TestCase):
    def __del__(self):
        api = Splitwise()
        for expense in api.get_expenses():
            api.delete_expense(expense['id'])

    def test_group_of_2(self):
        proc = subprocess.Popen(['python', '../src/groupsplit.py', 'transactions.csv', 'group_of_2',
                                 '--csv-settings=csv_settings.pkl', '--api-client=oauth_client.pkl',
                                 '-y'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        self.assertEqual(stderr, '')

    def test_group_of_3(self):
        proc = subprocess.Popen(['python', '../src/groupsplit.py', 'transactions.csv', 'group_of_3',
                                 '--csv-settings=csv_settings.pkl', '--api-client=oauth_client.pkl',
                                 '-y'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        self.assertEqual(stderr, '')
