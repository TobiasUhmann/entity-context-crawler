import json
import os
import sqlite3

from argparse import ArgumentParser, Namespace
from os import remove
from os.path import isfile

from deepca.dumpr import dumpr
from spacy.lang.en import English
from spacy.matcher import PhraseMatcher

from dao.links_db import select_pages_linking_to, select_pages_linked_from, select_aliases
from dao.matches_db import insert_page, create_pages_table, create_matches_table, insert_match, Page, Match, select_page
from util.util import log


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        freenode-json
        wiki-xml
        links-db
        matches-db
        --commit-frequency
        --in-memory
        --limit-pages
        --overwrite
    """

    parser.add_argument('freenode_json', metavar='freenode-json',
                        help='Path to input Freenode JSON')

    parser.add_argument('wiki_xml', metavar='wiki-xml',
                        help='Path to input pre-processed Wikipedia XML')

    parser.add_argument('links_db', metavar='links-db',
                        help='Path to input links DB')

    parser.add_argument('matches_db', metavar='matches-db',
                        help='Path to output matches DB')

    default_commit_frequency = None
    parser.add_argument('--commit-frequency', dest='commit_frequency', type=int, metavar='INT',
                        default=default_commit_frequency,
                        help='Commit to database every ... pages instead of committing at the end only'
                             ' (default: {})'.format(default_commit_frequency))

    parser.add_argument('--in-memory', dest='in_memory', action='store_true',
                        help='Build complete matches DB in memory before persisting it')

    default_limit_docs = None
    parser.add_argument('--limit-pages', dest='limit_pages', type=int, metavar='INT', default=default_limit_docs,
                        help='Early stop after ... pages (default: {})'.format(default_limit_docs))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite matches DB if it already exists')


def run(args: Namespace):
    """
    - Print applied config
    - Check if files already exist
    - Run actual program
    """

    freenode_json = args.freenode_json
    wiki_xml = args.wiki_xml
    links_db = args.links_db
    matches_db = args.matches_db

    commit_frequency = args.commit_frequency
    in_memory = args.in_memory
    limit_pages = args.limit_pages
    overwrite = args.overwrite

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('freenode-json', freenode_json))
    print('    {:20} {}'.format('wiki-xml', wiki_xml))
    print('    {:20} {}'.format('links-db', links_db))
    print('    {:20} {}'.format('matches-db', matches_db))
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

    if not isfile(freenode_json):
        print('Freenode JSON not found')
        exit()

    if not isfile(wiki_xml):
        print('Wikipedia XML not found')
        exit()

    if not isfile(links_db):
        print('Links DB not found')
        exit()

    if isfile(matches_db):
        if overwrite:
            remove(matches_db)
        else:
            print('Matches DB already exists, use --overwrite to overwrite it')
            exit()

    #
    # Run actual program
    #

    _build_matches_db(freenode_json, wiki_xml, links_db, matches_db, commit_frequency, in_memory, limit_pages)


def _build_matches_db(freenode_json, wiki_xml, links_db, matches_db, commit_frequency, in_memory, limit_pages):
    if in_memory:
        _run_in_memory(freenode_json, wiki_xml, links_db, matches_db, commit_frequency, limit_pages)
    else:
        _run_on_disk(freenode_json, wiki_xml, links_db, matches_db, commit_frequency, limit_pages)


def _run_on_disk(freenode_json, wiki_xml, links_db, matches_db, commit_frequency, limit_pages):
    with sqlite3.connect(matches_db) as matches_conn:
        create_pages_table(matches_conn)
        create_matches_table(matches_conn)

        _persist_pages(matches_conn, wiki_xml, commit_frequency, limit_pages)
        _process_entities(freenode_json, links_db, matches_conn, commit_frequency, limit_pages)

        log('Done')


def _run_in_memory(freenode_json, wiki_xml, links_db, matches_db, commit_frequency, limit_pages):
    with sqlite3.connect(':memory:') as memory_matches_conn:
        create_pages_table(memory_matches_conn)
        create_matches_table(memory_matches_conn)

        _persist_pages(memory_matches_conn, wiki_xml, commit_frequency, limit_pages)
        _process_entities(freenode_json, links_db, memory_matches_conn, commit_frequency, limit_pages)

        print()
        log('Persist...')

        with sqlite3.connect(matches_db) as disk_matches_conn:
            for line in memory_matches_conn.iterdump():
                if line not in ('BEGIN;', 'COMMIT;'):  # let python handle the transactions
                    disk_matches_conn.execute(line)

        log('Done')


def _persist_pages(matches_conn, wiki_xml, commit_frequency, limit_pages):
    """ Iterate through all Wikipedia pages and save them in pages table """

    # Use dumpr to iterate through pre-processed Wiki dump
    with dumpr.BatchReader(wiki_xml) as reader:
        for page_count, dumpr_doc in enumerate(reader.docs):

            # Get relevant values from dumpr doc
            page_title = dumpr_doc.meta['title']
            page_content = dumpr_doc.content

            # Early stop if --limit-pages was specified
            if limit_pages and page_count == limit_pages:
                break

            # Commit regularly instead of once at the end if --commit-frequency is set
            if commit_frequency and page_count % commit_frequency == 0:
                log('Commit...')
                matches_conn.commit()

            # Log progress
            log('{} | {}'.format(page_count, page_title))

            # Skip pages without content, happens sometimes, maybe pages marked for deletion (?)
            if page_content is None:
                continue

            # Persist page in pages DB
            insert_page(matches_conn, Page(page_title, page_content))


def _process_entities(freenode_json, links_db, matches_conn, commit_frequency, limit_pages):
    """
    Iterate through all Freebase entities. For each entity, get its Wikipedia page as well
    as the directly linked pages. On those pages, search for the entity label and its aliases.
    Persist the matches in the matches DB.
    """

    print()
    log('Load Freenode JSON...')
    freenode_data = json.load(open(freenode_json, 'r'))
    log('Done')

    nlp = English()
    nlp.vocab.lex_attr_getters = {}

    missing_urls = 0

    with sqlite3.connect(links_db) as links_conn:
        for entity_count, freenode_data_item in enumerate(freenode_data.items()):
            mid, entity_data = freenode_data_item

            entity_label = entity_data['label']
            wiki_url = entity_data['wikipedia']

            if not wiki_url:
                missing_urls += 1
                continue

            page_title = wiki_url.rsplit('/', 1)[-1].replace('_', ' ')

            #
            # Query neighbor pages and entity aliases
            #

            pages_linked_from_current_page = select_pages_linked_from(links_conn, page_title)
            pages_linking_to_current_page = select_pages_linking_to(links_conn, page_title)

            neighbor_page_titles = pages_linking_to_current_page | {page_title} | pages_linked_from_current_page

            neighbor_pages = []
            for neighbor_page in neighbor_page_titles:
                neighbor_page = select_page(matches_conn, neighbor_page)
                if neighbor_page is not None:
                    neighbor_pages.append(neighbor_page)

            aliases = select_aliases(links_conn, page_title)

            #
            # Search neighbor pages
            #

            matcher = PhraseMatcher(nlp.vocab)

            patterns = list(nlp.pipe({entity_label} | aliases))
            matcher.add('Entities', None, *patterns)

            match_count = 0
            for neighbor_page in neighbor_pages:
                page_title = neighbor_page.title
                page_content = neighbor_page.content

                spacy_doc = nlp.make_doc(page_content)
                matches = matcher(spacy_doc)

                for match_id, start, end in matches:
                    match_span = spacy_doc[start:end]
                    match_text = match_span.text

                    start_char = match_span.start_char
                    end_char = match_span.end_char

                    context_start = max(match_span.start_char - 20, 0)
                    context_end = min(match_span.end_char + 20, len(page_content))
                    context = page_content[context_start:context_end]

                    match = Match(mid, match_text, page_title, start_char, end_char, context)
                    insert_match(matches_conn, match)
                    match_count += 1

            row = (entity_count, entity_label, len(neighbor_pages) - 1, match_count)
            log('{} | {} | {} neighbors | {} matches'.format(*row))

        print('Stats')
        print('\tEntities without Wikipedia page: {}'.format(missing_urls))
