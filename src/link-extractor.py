import argparse
import sqlite3
import wikitextparser as wtp

from collections import defaultdict
from datetime import datetime

from wikipedia import Wikipedia


#
# DEFAULT CONFIGURATION
#


WIKIPEDIA_XML = 'data/enwiki-latest-pages-articles.xml'
LINKS_DB = 'data/links.db'
IN_MEMORY = False
COMMIT_FREQUENCY = 10000
LIMIT = None


#
# DATABASE FUNCTIONS
#


def create_links_table(conn):
    sql_create_table = '''
        CREATE TABLE links (
            from_doc int,      -- hashed lowercase Wikipedia doc title
            to_doc int         -- hashed lowercase Wikipedia doc title
        )
    '''

    sql_create_index_1 = '''
        CREATE INDEX idx_from_doc 
        ON links (from_doc)
    '''

    sql_create_index_2 = '''
        CREATE INDEX idx_to_doc
        ON links (to_doc)
    '''

    cursor = conn.cursor()
    cursor.execute(sql_create_table)
    cursor.execute(sql_create_index_1)
    cursor.execute(sql_create_index_2)
    cursor.close()


def insert_links(conn, links):
    sql = '''
        INSERT INTO links (from_doc, to_doc)
        VALUES(?, ?)
    '''

    cursor = conn.cursor()
    cursor.executemany(sql, links)
    cursor.close()


#
# LINK EXTRACTOR
#


class LinkExtractor:
    wikipedia_xml: str
    links_db: str
    in_memory: bool
    commit_frequency: int
    limit: int

    def __init__(self, wikipedia_xml, links_db, in_memory, commit_frequency, limit):
        self.wikipedia_xml = wikipedia_xml
        self.links_db = links_db
        self.in_memory = in_memory
        self.commit_frequency = commit_frequency
        self.limit = limit

    def run(self):
        if self.in_memory:
            self.__run_in_memory()
        else:
            self.__run_on_disk()

    def __run_on_disk(self):
        with sqlite3.connect(self.links_db) as conn_links:
            create_links_table(conn_links)
            self.__process_wikipedia(conn_links)
            print('{} | DONE'.format(datetime.now().strftime('%H:%M:%S')))

    def __run_in_memory(self):
        with sqlite3.connect(':memory:') as conn_memory:
            create_links_table(conn_memory)
            self.__process_wikipedia(conn_memory)

            print('{} | PERSIST'.format(datetime.now().strftime('%H:%M:%S')))
            with sqlite3.connect(self.links_db) as conn_links:
                for line in conn_memory.iterdump():
                    if line not in ('BEGIN;', 'COMMIT;'):  # let python handle the transactions
                        conn_links.execute(line)

            print('{} | DONE'.format(datetime.now().strftime('%H:%M:%S')))

    def __process_wikipedia(self, conn):
        link_count = 0
        missing_text_count = 0

        redirects = defaultdict(set)
        redirect_count = 0

        with open(self.wikipedia_xml, 'rb') as wikipedia_xml:
            for page_count, page in enumerate(Wikipedia(wikipedia_xml, tag='page')):

                if self.limit and page_count > self.limit:
                    break

                if page_count % self.commit_frequency == 0:
                    print('{} | COMMIT'.format(datetime.now().strftime('%H:%M:%S')))
                    conn.commit()

                if page_count % 1000 == 0:
                    print('{} | {:,} <page>s | {:,} redirects | {:,} links | {:,} missing text'.format(
                        datetime.now().strftime("%H:%M:%S"), page_count, redirect_count, link_count,
                        missing_text_count))

                if (page_count + 1) % 100001 == 0:
                    break

                from_doc = hash(page['title'][0].lower())

                if page['redirect']:
                    to_doc = hash(page['redirect'][0].lower())
                    redirects[from_doc].add(to_doc)
                    redirect_count += 1

                elif page['text']:
                    links = wtp.parse(page['text'][0]).wikilinks
                    inserts = [(from_doc, hash(link.title.lower())) for link in links]
                    insert_links(conn, inserts)
                    link_count += len(inserts)

                else:
                    missing_text_count += 1

            conn.commit()
            print('{} | COMMIT'.format(datetime.now().strftime('%H:%M:%S')))


#
# MAIN
#


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create the link graph',
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=40, width=120))

    parser.add_argument('--wikipedia-xml', dest='wikipedia_xml', default=WIKIPEDIA_XML,
                        help='path to Wikipedia XML (default: "{}")'.format(WIKIPEDIA_XML))

    parser.add_argument('--links-db', dest='links_db', default=LINKS_DB,
                        help='path to links DB (default: "{}")'.format(LINKS_DB))

    parser.add_argument('--in-memory', dest='in_memory', default=IN_MEMORY, action='store_true',
                        help='build complete links DB in memory before persisting it (default: {})'.format(IN_MEMORY))

    parser.add_argument('--commit-frequency', dest='commit_frequency', default=COMMIT_FREQUENCY,
                        help='commit to database every ... pages (default: {})'.format(COMMIT_FREQUENCY))

    parser.add_argument('--limit', dest='limit', default=LIMIT, type=int,
                        help='terminate after ... pages (default: {})'.format(LIMIT))

    args = parser.parse_args()

    link_extractor = LinkExtractor(args.wikipedia_xml, args.links_db, args.in_memory, args.commit_frequency, args.limit)
    link_extractor.run()
