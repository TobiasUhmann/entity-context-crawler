import unittest
from io import StringIO
from unittest.mock import patch

from entity_context_crawler.__main__ import main


class TestBuildMatchesDb(unittest.TestCase):

    @patch('sys.stdout', new_callable=StringIO)
    def test_help(self, mock_stdout):
        args = ['ecc', '--help']

        with self.assertRaises(SystemExit):
            main(args)

        self.assertRegex(mock_stdout.getvalue(), r'usage')


if __name__ == '__main__':
    unittest.main()
