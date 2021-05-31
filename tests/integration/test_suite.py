import os
import sqlite3
import unittest
from io import StringIO
from unittest.mock import patch

from entity_context_crawler.__main__ import main


class TestSuite(unittest.TestCase):

    @patch('sys.stdout', new_callable=StringIO)
    def test_help(self, mock_stdout):
        #
        # WHEN running `ecc --help`
        #

        args = ['ecc', '--help']

        with self.assertRaises(SystemExit):
            main(args)

        #
        # THEN the help message should be printed
        #

        self.assertRegex(mock_stdout.getvalue(), r'usage')

    def test_build_matches_db(self):
        #
        # WHEN running `ecc build-matches-db` with valid input data
        #

        args = ['ecc', 'build-matches-db',
                'tests/integration/data/wikipedia.xml',
                'tests/integration/data/entities.json',
                'tests/integration/data/matches.db']

        res = main(args)

        #
        # THEN a non-empty Matches DB should be created
        #

        self.assertEqual(res, 0)
        self._check_matches_db()

        # Tidy up
        os.remove('tests/integration/data/matches.db')

    def test_build_matches_db_in_memory(self):
        #
        # WHEN running `ecc build-matches-db` with valid input data
        # AND  processing in memroy
        #

        args = ['ecc', 'build-matches-db',
                'tests/integration/data/wikipedia.xml',
                'tests/integration/data/entities.json',
                'tests/integration/data/matches.db',
                '--in-memory']

        res = main(args)

        #
        # THEN a non-empty Matches DB should be created
        #

        self.assertEqual(res, 0)
        self._check_matches_db()

        # Tidy up
        os.remove('tests/integration/data/matches.db')

    def test_build_contexts_db(self):
        #
        # GIVEN a non-empty Matches DB
        #

        args = ['ecc', 'build-matches-db',
                'tests/integration/data/wikipedia.xml',
                'tests/integration/data/entities.json',
                'tests/integration/data/matches.db']

        res = main(args)

        self.assertEqual(res, 0)
        self._check_matches_db()

        #
        # WHEN running `ecc build-contexts-db`
        #

        args = ['ecc', 'build-contexts-db',
                'tests/integration/data/entities.json',
                'tests/integration/data/qid-to-rid.txt',
                'tests/integration/data/matches.db',
                'tests/integration/data/contexts.db',
                '--context-size', '500',
                '--crop-sentences',
                '--csv-file', 'tests/integration/data/contexts.csv',
                '--limit-contexts', '100']

        res = main(args)

        #
        # THEN a non-empty Contexts DB should be created
        #

        self.assertEqual(res, 0)
        self._check_contexts_db()

        # Tidy up
        os.remove('tests/integration/data/matches.db')
        os.remove('tests/integration/data/contexts.db')
        os.remove('tests/integration/data/contexts.csv')

    def _check_matches_db(self):
        """ Check that the Matches DB is not empty """

        with sqlite3.connect('tests/integration/data/matches.db') as matches_conn:
            pages_count = matches_conn.execute('SELECT COUNT(*) FROM pages').fetchone()[0]
            mentions_count = matches_conn.execute('SELECT COUNT(*) FROM mentions').fetchone()[0]
            matches_count = matches_conn.execute('SELECT COUNT(*) FROM matches').fetchone()[0]

            self.assertGreater(pages_count, 0)
            self.assertGreater(mentions_count, 0)
            self.assertGreater(matches_count, 0)

    def _check_contexts_db(self):
        """ Check that the Contexts DB is not empty """

        with sqlite3.connect('tests/integration/data/contexts.db') as contexts_conn:
            pages_count = contexts_conn.execute('SELECT COUNT(*) FROM contexts').fetchone()[0]

            self.assertGreater(pages_count, 0)


if __name__ == '__main__':
    unittest.main()
