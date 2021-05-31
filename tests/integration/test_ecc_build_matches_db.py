import os
import sqlite3
import unittest

from entity_context_crawler.__main__ import main


class TestEccBuildMatchesDb(unittest.TestCase):

    def test_normal(self):
        args = [
            'ecc',
            'build-matches-db',
            'data/wikipedia.xml',
            'data/entities.json',
            'data/matches.db'
        ]

        res = main(args)

        self.assertEqual(res, 0)

        with sqlite3.connect('data/matches.db') as matches_conn:
            pages_count = matches_conn.execute('SELECT COUNT(*) FROM pages').fetchone()[0]
            mentions_count = matches_conn.execute('SELECT COUNT(*) FROM mentions').fetchone()[0]
            matches_count = matches_conn.execute('SELECT COUNT(*) FROM matches').fetchone()[0]

            self.assertGreater(pages_count, 0)
            self.assertGreater(mentions_count, 0)
            self.assertGreater(matches_count, 0)

        matches_conn.close()
        os.remove('data/matches.db')


if __name__ == '__main__':
    unittest.main()
