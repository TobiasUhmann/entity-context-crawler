from unittest import TestCase

from dao.oid_to_rid_txt import load_oid_to_rid


class Test(TestCase):
    def test_load_oid_to_rid(self):
        oid_to_rid = load_oid_to_rid('test_data/qid-to-rid-v1-test.txt')

        self.assertEqual(len(oid_to_rid), 3)
        self.assertEqual(oid_to_rid['Q108946'], 0)
        self.assertEqual(oid_to_rid['Q39792'], 1)
        self.assertEqual(oid_to_rid['Q1041'], 2)
