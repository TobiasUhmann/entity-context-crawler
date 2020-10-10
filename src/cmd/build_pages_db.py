import os
import sqlite3

from argparse import ArgumentParser, Namespace
from os import remove
from os.path import isfile

from dao.pages_db import create_pages_table, insert_page, Page
from util.util import log
from util.wikipedia import Wikipedia


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        wiki-xml
        pages-db
        --commit-frequency
        --in-memory
        --limit-pages
        --overwrite
    """

    parser.add_argument('wiki_xml', metavar='wiki-xml',
                        help='Path to input Wiki XML')

    parser.add_argument('pages_db', metavar='pages-db',
                        help='Path to output pages DB')

    default_commit_frequency = None
    parser.add_argument('--commit-frequency', dest='commit_frequency', type=int, metavar='INT',
                        default=default_commit_frequency,
                        help='Commit to database every ... pages instead of committing at the end only'
                             ' (default: {})'.format(default_commit_frequency))

    parser.add_argument('--in-memory', dest='in_memory', action='store_true',
                        help='Build complete matches DB in memory before persisting it')

    default_limit_pages = None
    parser.add_argument('--limit-pages', dest='limit_pages', type=int, metavar='INT', default=default_limit_pages,
                        help='Early stop after ... pages (default: {})'.format(default_limit_pages))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite matches DB if it already exists')


def run(args: Namespace):
    """
    - Print applied config
    - Check if files already exist
    - Run actual program
    """

    wiki_xml = args.wiki_xml
    pages_db = args.pages_db

    commit_frequency = args.commit_frequency
    in_memory = args.in_memory
    limit_pages = args.limit_pages
    overwrite = args.overwrite

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('wiki-xml', wiki_xml))
    print('    {:20} {}'.format('pages-db', pages_db))
    print()
    print('    {:20} {}'.format('--commit-frequency', commit_frequency))
    print('    {:20} {}'.format('--in-memory', in_memory))
    print('    {:20} {}'.format('--limit-pages', limit_pages))
    print('    {:20} {}'.format('--overwrite', overwrite))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', python_hash_seed))
    print()

    #
    # Check if files already exist
    #

    if not isfile(wiki_xml):
        print('Wiki XML not found')
        exit()

    if isfile(pages_db):
        if overwrite:
            remove(pages_db)
        else:
            print('Pages DB already exists, use --overwrite to overwrite it')
            exit()

    #
    # Run actual program
    #

    _build_pages_db(wiki_xml, pages_db, commit_frequency, in_memory, limit_pages)


def _build_pages_db(wiki_xml, pages_db, commit_frequency, in_memory, limit_pages):
    if in_memory:
        _run_in_memory(wiki_xml, pages_db, commit_frequency, limit_pages)
    else:
        _run_on_disk(wiki_xml, pages_db, commit_frequency, limit_pages)

    log()
    log('Finished successfully')


def _run_on_disk(wiki_xml, pages_db, commit_frequency, limit_pages):
    with sqlite3.connect(pages_db) as pages_conn:
        create_pages_table(pages_conn)

        _process_wiki_xml(pages_conn, wiki_xml, commit_frequency, limit_pages)


def _run_in_memory(wiki_xml, pages_db, commit_frequency, limit_pages):
    """ Create pages DB in memory. Persist it in the end. """

    with sqlite3.connect(':memory:') as memory_pages_conn:
        create_pages_table(memory_pages_conn)

        _process_wiki_xml(memory_pages_conn, wiki_xml, commit_frequency, limit_pages)

        log()
        log('Persist...')

        with sqlite3.connect(pages_db) as disk_pages_conn:
            for line in memory_pages_conn.iterdump():
                if line not in ('BEGIN;', 'COMMIT;'):  # let python handle the transactions
                    disk_pages_conn.execute(line)

        log('Done')


def _process_wiki_xml(pages_conn, wiki_xml, commit_frequency, limit_pages):
    """ Iterate through all Wiki pages and store them in the pages DB """

    with open(wiki_xml, 'rb') as wiki_xml_fh:
        wikipedia = Wikipedia(wiki_xml_fh, tag='page')
        for page_count, page in enumerate(wikipedia):

            if limit_pages and page_count == limit_pages:
                break

            if page_count % 1000 == 0:
                log('{:,}'.format(page_count))

            if commit_frequency and page_count % commit_frequency == 0:
                log('Commit...')
                pages_conn.commit()
                log('Done')

            page_title = page['title']
            page_markup = page['text']

            insert_page(pages_conn, Page(page_title, page_markup))
