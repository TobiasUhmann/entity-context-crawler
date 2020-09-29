import os
import sqlite3
import wikitextparser as wtp

from argparse import ArgumentParser, Namespace
from collections import defaultdict
from os import remove
from os.path import isfile
from typing import Dict, Set

from dao.links_db import create_links_table, insert_links
from util.util import log
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
    """
    - Print applied config
    - Check if files already exist
    - Run actual program
    """

    wiki_xml = args.wiki_xml
    links_db = args.links_db

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
    print('    {:20} {}'.format('links-db', links_db))
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
        print('Wikipedia XML not found')
        exit()

    if isfile(links_db):
        if overwrite:
            remove(links_db)
        else:
            print('Links DB already exists, use --overwrite to overwrite it')
            exit()

    #
    # Run actual program
    #

    _build_links_db(wiki_xml, links_db, commit_frequency, in_memory, limit_pages)


def _build_links_db(wiki_xml, links_db, commit_frequency, in_memory, limit_pages):
    if in_memory:
        _run_in_memory(wiki_xml, links_db, commit_frequency, limit_pages)
    else:
        _run_on_disk(wiki_xml, links_db, commit_frequency, limit_pages)


def _run_on_disk(wiki_xml, links_db, commit_frequency, limit_pages):
    with sqlite3.connect(links_db) as links_conn:
        create_links_table(links_conn)

        _process_wikipedia(wiki_xml, links_conn, commit_frequency, limit_pages)

        log('Done')


def _run_in_memory(wiki_xml, links_db, commit_frequency, limit_pages):
    with sqlite3.connect(':memory:') as memory_conn:
        create_links_table(memory_conn)

        _process_wikipedia(wiki_xml, memory_conn, commit_frequency, limit_pages)

        print()
        log('Persist...')

        with sqlite3.connect(links_db) as conn_links:
            for line in memory_conn.iterdump():
                if line not in ('BEGIN;', 'COMMIT;'):  # let python handle the transactions
                    conn_links.execute(line)

        log('Done')


def _process_wikipedia(wiki_xml, links_conn, commit_frequency, limit_pages):
    link_count = 0
    missing_text_count = 0

    redirects: Dict[Set[str]] = defaultdict(set)
    redirect_count = 0

    with open(wiki_xml, 'rb') as wiki_xml:
        wikipedia = Wikipedia(wiki_xml, tag='page')
        for page_count, page in enumerate(wikipedia):

            if limit_pages and page_count > limit_pages:
                break

            if commit_frequency and page_count % commit_frequency == 0:
                log('Commit')
                links_conn.commit()

            if page_count % 1000 == 0:
                row = (page_count, wikipedia.missing_titles, wikipedia.missing_texts, wikipedia.skipped_templates,
                       redirect_count, link_count)
                log('{:,} <page>s | {:,} missing titles | {:,} missing texts | {:,} skipped templates'
                    ' | {:,} redirects | {:,} links'.format(*row))

            from_page = page['title']

            if page['redirect']:
                to_page = page['redirect']
                redirects[from_page].add(to_page)
                redirect_count += 1

            elif page['text']:
                wiki_links = wtp.parse(page['text']).wikilinks
                db_links = [(from_page, link.title) for link in wiki_links]
                insert_links(links_conn, db_links)
                link_count += len(db_links)

            else:
                missing_text_count += 1

        links_conn.commit()
        log('Commit')

        print()
        print('Stats:')
        print('\tMissing titles: {}'.format(wikipedia.missing_titles))
        print('\tMissing texts: {}'.format(wikipedia.missing_texts))
