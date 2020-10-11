import os
import sqlite3

from argparse import ArgumentParser, Namespace
from os import remove
from os.path import isfile

from deepca.dumpr import dumpr

from dao.pages_db import create_raw_pages_table, insert_raw_page, RawPage, TextPage, insert_text_page, \
    create_text_pages_table
from util.util import log
from util.wikipedia import Wikipedia


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        raw-wiki-xml
        text-wiki-xml
        pages-db
        --limit-pages
        --overwrite
    """

    parser.add_argument('raw_wiki_xml', metavar='raw-wiki-xml',
                        help='Path to (input) raw Wiki XML')

    parser.add_argument('text_wiki_xml', metavar='text-wiki-xml',
                        help='Path to (input) pre-processed text Wiki XML')

    parser.add_argument('pages_db', metavar='pages-db',
                        help='Path to (output) pages DB')

    default_limit_pages = None
    parser.add_argument('--limit-pages', dest='limit_pages', type=int, metavar='INT', default=default_limit_pages,
                        help='Early stop after ... pages (default: {})'.format(default_limit_pages))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite pages DB if it already exists')


def run(args: Namespace):
    """
    - Print applied config
    - Check if files already exist
    - Run actual program
    """

    raw_wiki_xml = args.raw_wiki_xml
    text_wiki_xml = args.text_wiki_xml
    pages_db = args.pages_db

    limit_pages = args.limit_pages
    overwrite = args.overwrite

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('raw-wiki-xml', raw_wiki_xml))
    print('    {:20} {}'.format('text-wiki-xml', text_wiki_xml))
    print('    {:20} {}'.format('pages-db', pages_db))
    print()
    print('    {:20} {}'.format('--limit-pages', limit_pages))
    print('    {:20} {}'.format('--overwrite', overwrite))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', python_hash_seed))

    #
    # Check if files already exist
    #

    if not isfile(raw_wiki_xml):
        print('Raw Wiki XML not found')
        exit()

    if not isfile(text_wiki_xml):
        print('Text Wiki XML not found')
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

    _build_pages_db(raw_wiki_xml, text_wiki_xml, pages_db, limit_pages)


def _build_pages_db(wiki_xml, wiki_text_xml, pages_db, limit_pages):
    with sqlite3.connect(pages_db) as pages_conn:

        create_raw_pages_table(pages_conn)
        _process_raw_wiki_xml(wiki_xml, pages_conn, limit_pages)

        create_text_pages_table(pages_conn)
        _process_text_wiki_xml(wiki_text_xml, pages_conn, limit_pages)


def _process_raw_wiki_xml(raw_wiki_xml, pages_conn, limit_pages):
    """ Iterate through all raw Wiki pages and store them in the pages DB """

    log()

    with open(raw_wiki_xml, 'rb') as raw_wiki_xml_fh:
        wikipedia = Wikipedia(raw_wiki_xml_fh, tag='page')
        for page_count, page in enumerate(wikipedia):

            if limit_pages and page_count == limit_pages:
                break

            if page_count % 1000 == 0:
                pages_conn.commit()
                log('{:,} raw pages'.format(page_count))

            page_title = page['title']
            page_markup = page['text']

            insert_raw_page(pages_conn, RawPage(page_title, page_markup))


def _process_text_wiki_xml(text_wiki_xml, pages_conn, limit_pages):
    """ Iterate through all text Wiki pages and store them in the pages DB """

    log()

    with dumpr.BatchReader(text_wiki_xml) as reader:
        for page_count, dumpr_doc in enumerate(reader.docs):

            if limit_pages and page_count == limit_pages:
                break

            if page_count % 1000 == 0:
                pages_conn.commit()
                log('{:,} text pages'.format(page_count))

            page_title = dumpr_doc.meta['title']
            page_text = dumpr_doc.content

            insert_text_page(pages_conn, TextPage(page_title, page_text))
