from unittest import TestCase

from dao.mid2ryn_txt import load_mid2ryn


class Test(TestCase):
    def test_load_mid2ryn_1(self):
        mid2ryn = load_mid2ryn('mid2ryn_txt_test_file.txt')

        self.assertEqual(len(mid2ryn), 6)
        self.assertEqual(mid2ryn['/m/027rn'], 0)
        self.assertEqual(mid2ryn['/m/06cx9'], 1)
        self.assertEqual(mid2ryn['/m/017dcd'], 2)
        self.assertEqual(mid2ryn['/m/07s9rl0'], 4)
        self.assertEqual(mid2ryn['/m/044mz_'], 7)
        self.assertEqual(mid2ryn['/m/0jgd'], 68)
