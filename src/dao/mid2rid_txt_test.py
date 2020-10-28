from unittest import TestCase

from dao.mid2rid_txt import load_mid2rid


class Test(TestCase):
    def test_load_mid2rid_1(self):
        mid2rid = load_mid2rid('mid2rid_txt_test_file.txt')

        self.assertEqual(len(mid2rid), 6)
        self.assertEqual(mid2rid['/m/027rn'], 0)
        self.assertEqual(mid2rid['/m/06cx9'], 1)
        self.assertEqual(mid2rid['/m/017dcd'], 2)
        self.assertEqual(mid2rid['/m/07s9rl0'], 4)
        self.assertEqual(mid2rid['/m/044mz_'], 7)
        self.assertEqual(mid2rid['/m/0jgd'], 68)
