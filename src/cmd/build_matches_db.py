import json
import matplotlib.pyplot as plt
import os
import sqlite3

from argparse import ArgumentParser, Namespace
from collections import defaultdict
from datetime import datetime
from matplotlib.widgets import Slider
from os import remove
from os.path import isfile
from spacy.lang.en import English
from spacy.language import Language
from spacy.matcher import PhraseMatcher

from deepca.dumpr import dumpr

from dao.links_db import select_pages_linking_to, select_pages_linked_from
from dao.matches_db import insert_page, create_pages_table, create_matches_table, insert_match, Page, Match
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
        --limit-docs
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

        _process_wikipedia(freenode_json, wiki_xml, links_db, matches_conn, commit_frequency, limit_pages)

        log('Done')


def _run_in_memory(freenode_json, wiki_xml, links_db, matches_db, commit_frequency, limit_pages):
    with sqlite3.connect(':memory:') as memory_matches_conn:
        create_pages_table(memory_matches_conn)
        create_matches_table(memory_matches_conn)

        _process_wikipedia(freenode_json, wiki_xml, links_db, memory_matches_conn, commit_frequency, limit_pages)

        print()
        log('Persist...')

        with sqlite3.connect(matches_db) as disk_matches_conn:
            for line in memory_matches_conn.iterdump():
                if line not in ('BEGIN;', 'COMMIT;'):  # let python handle the transactions
                    disk_matches_conn.execute(line)

        log('Done')


def _process_wikipedia(freenode_json, wiki_xml, links_db, matches_conn, commit_frequency, limit_pages):
    nlp = English()
    nlp.vocab.lex_attr_getters = {}
    matcher = PhraseMatcher(nlp.vocab)

    with open(freenode_json, 'r') as file:
        wikidata = json.load(file)

    #
    # self.entities: entity -> {(MID, Wikipedia doc title)...}
    #
    # {
    #     ...
    #     'Spider-Man': {('/m/06ys2', 'Spider-Man'), ('/m/012s1d', 'Spider-Man (2002 film)')}
    #     'Spidey': {('/m/06ys2', 'Spider-Man')}
    #     ...
    # }
    #
    # Homonyms map to multiple Freenode nodes.

    entities = defaultdict(set)

    missing_urls = 0
    for mid in wikidata:
        labels = {wikidata[mid]['label']}

        wikipedia_url = wikidata[mid]['wikipedia']
        if wikipedia_url:
            doc_title = wikipedia_url.rsplit('/', 1)[-1].replace('_', ' ')

            for label in labels:
                entities[label].add((mid, doc_title))
        else:
            missing_urls += 1

    print('Missing URLs: %d' % missing_urls)

    patterns = list(nlp.pipe(entities.keys()))
    matcher.add('Entities', None, *patterns)

    #
    #
    #

    with sqlite3.connect(links_db) as links_conn, \
            dumpr.BatchReader(wiki_xml) as reader:

        for doc_count, dumpr_doc in enumerate(reader.docs):
            if limit_pages and doc_count > limit_pages:
                break

            if commit_frequency and doc_count % commit_frequency == 0:
                log('Commit...')
                matches_conn.commit()

            if dumpr_doc.content is None:
                continue

            _process_page(nlp, matcher, entities, dumpr_doc, matches_conn, links_conn, doc_count)


def _process_page(nlp, matcher, entities, dumpr_doc, matches_conn, links_conn, page_count):
    current_page = dumpr_doc.meta['title']

    #
    # Store doc in docs table
    #

    insert_page(matches_conn, Page(current_page, dumpr_doc.content))

    #
    # spaCy
    #

    spacy_doc = nlp.make_doc(dumpr_doc.content)
    matches = matcher(spacy_doc)

    #
    # Query neighbor pages
    #

    pages_linked_from_current_page = select_pages_linked_from(links_conn, current_page)
    pages_linking_to_current_page = select_pages_linking_to(links_conn, current_page)

    neighbor_pages = pages_linking_to_current_page | {current_page} | pages_linked_from_current_page

    #
    # Process all Freenode entities & save if in neighbor docs
    #

    match_count = 0
    for match_id, start, end in matches:
        entity_span = spacy_doc[start:end]
        entity_labels = entity_span.text

        if not entities[entity_labels]:
            continue

        entity_page_title = list(entities[entity_labels])[0][1]
        if entity_page_title not in neighbor_pages:
            continue

        mid = list(entities[entity_labels])[0][0]

        context_start = max(entity_span.start_char - 20, 0)
        context_end = min(entity_span.end_char + 20, len(dumpr_doc.content))
        context = dumpr_doc.content[context_start:context_end]

        match = Match(mid, entity_labels, current_page, entity_span.start_char, entity_span.end_char, context)
        insert_match(matches_conn, match)

        match_count += 1

    print('{} | {:,} Docs | {} | {:,} neighbors | {:,} matches'.format(
        datetime.now().strftime("%H:%M:%S"), page_count, current_page, len(neighbor_pages), match_count))
