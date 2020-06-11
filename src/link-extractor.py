#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sqlite3
import wikitextparser as wtp

from collections import defaultdict
from datetime import datetime
from os import remove
from os.path import isfile

from wikipedia import Wikipedia

#
# DEFAULT CONFIG
#

COMMIT_FREQUENCY = 10000
LIMIT_PAGES = None


#
# MAIN
#

def main():
    #
    # Parse args
    #

    parser = argparse.ArgumentParser(
        description='Create the link graph',
        formatter_class=lambda prog: argparse.MetavarTypeHelpFormatter(prog, max_help_position=50, width=120))

    parser.add_argument('wikipedia_xml', metavar='wikipedia_xml', type=str,
                        help='path to input Wikipedia XML')

    parser.add_argument('links_db', metavar='links_db', type=str,
                        help='path to output links DB')

    parser.add_argument('--commit-frequency', dest='commit_frequency', default=COMMIT_FREQUENCY, type=int,
                        help='commit to database every ... pages (default: {})'.format(COMMIT_FREQUENCY))

    parser.add_argument('--in-memory', dest='in_memory', action='store_true',
                        help='build complete links DB in memory before persisting it)')

    parser.add_argument('--limit-pages', dest='limit_pages', default=LIMIT_PAGES, type=int,
                        help='terminate after ... pages (default: {})'.format(LIMIT_PAGES))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='overwrite distribution DB if it already exists')

    args = parser.parse_args()

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('Wikipedia XML', args.wikipedia_xml))
    print('    {:20} {}'.format('Links DB', args.links_db))
    print()
    print('    {:20} {}'.format('Commit frequency', args.commit_frequency))
    print('    {:20} {}'.format('In memory', args.in_memory))
    print('    {:20} {}'.format('Limit pages', args.limit_pages))
    print('    {:20} {}'.format('Overwrite', args.overwrite))
    print()

    #
    # Check for input/output files
    #

    if not isfile(args.wikipedia_xml):
        print('Wikipedia XML not found')
        exit()

    if isfile(args.dist_db):
        if args.overwrite:
            remove(args.dist_db)
        else:
            print('Links DB already exists. Use --overwrite to overwrite it')
            exit()

    #
    # Run link extractor
    #

    link_extractor = LinkExtractor(args.wikipedia_xml, args.links_db, args.commit_frequency, args.in_memory,
                                   args.page_limit)
    link_extractor.run()


#
# LINK EXTRACTOR
#

class LinkExtractor:
    wikipedia_xml: str
    links_db: str

    commit_frequency: int
    in_memory: bool
    limit: int

    def __init__(self, wikipedia_xml, links_db, commit_frequency, in_memory, limit):
        self.wikipedia_xml = wikipedia_xml
        self.links_db = links_db

        self.commit_frequency = commit_frequency
        self.in_memory = in_memory
        self.limit = limit

    def run(self):
        if self.in_memory:
            self.__run_in_memory()
        else:
            self.__run_on_disk()

    def __run_on_disk(self):
        with sqlite3.connect(self.links_db) as links_conn:
            create_links_table(links_conn)
            self.__process_wikipedia(links_conn)
            print('{} | DONE'.format(datetime.now().strftime('%H:%M:%S')))

    def __run_in_memory(self):
        with sqlite3.connect(':memory:') as memory_conn:
            create_links_table(memory_conn)
            self.__process_wikipedia(memory_conn)

            print('{} | PERSIST'.format(datetime.now().strftime('%H:%M:%S')))
            with sqlite3.connect(self.links_db) as conn_links:
                for line in memory_conn.iterdump():
                    if line not in ('BEGIN;', 'COMMIT;'):  # let python handle the transactions
                        conn_links.execute(line)

            print('{} | DONE'.format(datetime.now().strftime('%H:%M:%S')))

    def __process_wikipedia(self, links_conn):
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
                    links_conn.commit()

                if page_count % 1000 == 0:
                    print('{} | {:,} <page>s | {:,} redirects | {:,} links | {:,} missing text'.format(
                        datetime.now().strftime("%H:%M:%S"), page_count, redirect_count, link_count,
                        missing_text_count))

                if page_count >= 16512000:
                    print('{} | {:,} <page>s | {:,} redirects | {:,} links | {:,} missing text'.format(
                        datetime.now().strftime("%H:%M:%S"), page_count, redirect_count, link_count,
                        missing_text_count))

                    print(page)


                    from_doc = hash(page['title'][0].lower())

                    if page['redirect']:
                        to_doc = hash(page['redirect'][0].lower())
                        redirects[from_doc].add(to_doc)
                        redirect_count += 1

                    elif page['text']:
                        links = wtp.parse(page['text'][0]).wikilinks
                        inserts = [(from_doc, hash(link.title.lower())) for link in links]
                        insert_links(links_conn, inserts)
                        link_count += len(inserts)

                    else:
                        missing_text_count += 1

            links_conn.commit()
            print('{} | COMMIT'.format(datetime.now().strftime('%H:%M:%S')))


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
#
#

if __name__ == '__main__':
    main()
