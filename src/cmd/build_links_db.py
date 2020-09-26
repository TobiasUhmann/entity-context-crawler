import sqlite3
import wikitextparser as wtp

from argparse import ArgumentParser, Namespace
from collections import defaultdict
from datetime import datetime
from os import remove
from os.path import isfile
from util.wikipedia import Wikipedia


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        wiki-xml
        links-db
        --commit-frequency
        --in-memory
        --limit-pages
        --overwrite
    """

    parser.add_argument('wiki_xml', metavar='wiki-xml',
                        help='Path to input Wikipedia XML')

    parser.add_argument('links_db', metavar='links-db',
                        help='Path to output links DB')

    default_commit_frequency = None
    parser.add_argument('--commit-frequency', dest='commit_frequency', type=int, metavar='INT',
                        default=default_commit_frequency,
                        help='Commit to database every ... pages instead of committing at the end only'
                             ' (default: {})'.format(default_commit_frequency))

    parser.add_argument('--in-memory', dest='in_memory', action='store_true',
                        help='Build complete links DB in memory before persisting it')

    default_limit_pages = None
    parser.add_argument('--limit-pages', dest='limit_pages', type=int, metavar='INT', default=default_limit_pages,
                        help='Early stop after ... pages (default: {})'.format(default_limit_pages))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite links DB if it already exists')


def run(args: Namespace):
    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('Wikipedia XML', args.wiki_xml))
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

    if isfile(args.links_db):
        if args.overwrite:
            remove(args.links_db)
        else:
            print('Links DB already exists. Use --overwrite to overwrite it')
            exit()

    #
    # Run link extractor
    #

    link_extractor = LinkExtractor(args.wiki_xml, args.links_db, args.commit_frequency, args.in_memory,
                                   args.limit_pages)
    link_extractor.run()


#
# LINK EXTRACTOR
#

class LinkExtractor:
    wikipedia_xml: str
    links_db: str

    commit_frequency: int
    in_memory: bool
    limit_pages: int

    def __init__(self, wikipedia_xml, links_db, commit_frequency, in_memory, limit_pages):
        self.wikipedia_xml = wikipedia_xml
        self.links_db = links_db

        self.commit_frequency = commit_frequency
        self.in_memory = in_memory
        self.limit_pages = limit_pages

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
            wikipedia = Wikipedia(wikipedia_xml, tag='page')
            for page_count, page in enumerate(wikipedia):

                if self.limit_pages and page_count > self.limit_pages:
                    break

                if page_count % self.commit_frequency == 0:
                    print('{} | COMMIT'.format(datetime.now().strftime('%H:%M:%S')))
                    links_conn.commit()

                if page_count % 1000 == 0:
                    row = (datetime.now().strftime("%H:%M:%S"), page_count, wikipedia.missing_titles,
                           wikipedia.missing_texts, wikipedia.skipped_templates, redirect_count, link_count)
                    print('{} | {:,} <page>s | {:,} missing titles | {:,} missing texts | {:,} skipped templates'
                          ' | {:,} redirects | {:,} links'.format(*row))

                from_doc = hash(page['title'].lower())

                if page['redirect']:
                    to_doc = hash(page['redirect'].lower())
                    redirects[from_doc].add(to_doc)
                    redirect_count += 1

                elif page['text']:
                    links = wtp.parse(page['text']).wikilinks
                    inserts = [(from_doc, hash(link.title.lower())) for link in links]
                    insert_links(links_conn, inserts)
                    link_count += len(inserts)

                else:
                    missing_text_count += 1

            print()
            print('Missing titles: {}'.format(wikipedia.missing_titles))
            print('Missing texts: {}'.format(wikipedia.missing_texts))

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
