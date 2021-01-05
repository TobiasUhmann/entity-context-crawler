from unittest import TestCase

from dao.qid_to_rid_txt import load_qid_to_rid


class Test(TestCase):
    def test_load_qid_to_rid(self):
        qid_to_rid = load_qid_to_rid('test-data/qid-to-rid-v1-test.txt')

        self.assertEqual(len(qid_to_rid), 3)
        self.assertEqual(qid_to_rid['Q108946'], 0)
        self.assertEqual(qid_to_rid['Q39792'], 1)
        self.assertEqual(qid_to_rid['Q1041'], 2)
