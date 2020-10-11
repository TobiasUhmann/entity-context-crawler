import json
import os
import sqlite3
import wikitextparser as wtp

from argparse import ArgumentParser, Namespace
from os import remove
from os.path import isfile
from typing import List

from spacy.lang.en import English
from spacy.matcher import PhraseMatcher

from dao.links_db import select_pages_linking_to, select_pages_linked_from, select_aliases
from dao.matches_db import create_matches_table, insert_match, Match
from util.util import log
from util.wikipedia import Wikipedia


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        freebase-json
        wiki-xml
        matches-db
        --in-memory
        --limit-pages
        --overwrite
    """

    parser.add_argument('freebase_json', metavar='freebase-json',
                        help='Path to input Freebase JSON')

    parser.add_argument('wiki_xml', metavar='wiki-xml',
                        help='Path to input Wikipedia XML')

    parser.add_argument('matches_db', metavar='matches-db',
                        help='Path to output matches DB')

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

    freebase_json = args.freebase_json
    wiki_xml = args.wiki_xml
    matches_db = args.matches_db

    in_memory = args.in_memory
    limit_pages = args.limit_pages
    overwrite = args.overwrite

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('freebase-json', freebase_json))
    print('    {:20} {}'.format('wiki-xml', wiki_xml))
    print('    {:20} {}'.format('matches-db', matches_db))
    print()
    print('    {:20} {}'.format('--in-memory', in_memory))
    print('    {:20} {}'.format('--limit-pages', limit_pages))
    print('    {:20} {}'.format('--overwrite', overwrite))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', python_hash_seed))
    print()

    #
    # Check if files already exist
    #

    if not isfile(freebase_json):
        print('Freebase JSON not found')
        exit()

    if not isfile(wiki_xml):
        print('Wikipedia XML not found')
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

    _build_matches_db(freebase_json, wiki_xml, matches_db, in_memory, limit_pages)


def _build_matches_db(freebase_json, wiki_xml, matches_db, in_memory, limit_pages):
    if in_memory:
        _run_in_memory(freebase_json, matches_db, limit_pages)
    else:
        _run_on_disk(freebase_json, wiki_xml, matches_db, limit_pages)

        log()
        log('Finished successfully')


def _run_on_disk(freebase_json, wiki_xml, matches_db, limit_pages):
    with sqlite3.connect(matches_db) as matches_conn:
        create_matches_table(matches_conn)

        _process_wikipedia(freebase_json, wiki_xml, matches_conn, limit_pages)


def _run_in_memory(freebase_json, wiki_xml, matches_db, limit_pages):
    with sqlite3.connect(':memory:') as memory_matches_conn:
        create_matches_table(memory_matches_conn)

        _process_wikipedia(freebase_json, wiki_xml, memory_matches_conn, limit_pages)

        log()
        log('Persist...')

        with sqlite3.connect(matches_db) as disk_matches_conn:
            for line in memory_matches_conn.iterdump():
                if line not in ('BEGIN;', 'COMMIT;'):  # let python handle the transactions
                    disk_matches_conn.execute(line)

        log('Done')


def _process_wikipedia(freebase_json, wiki_xml, matches_conn, limit_pages):

    log()
    log('Load Freebase JSON...')
    freebase_data = json.load(open(freebase_json, 'r'))
    log('Done')

    page_title_to_mid = {}
    for mid, entity_data in freebase_data.items():
        page_url = entity_data['wikipedia']
        if page_url:
            page_title = page_url.rsplit('/', 1)[-1].replace('_', ' ')
            page_title_to_mid[page_title] = mid

    nlp = English()
    nlp.vocab.lex_attr_getters = {}

    with open(wiki_xml, 'rb') as wiki_xml_fh:
        wikipedia = Wikipedia(wiki_xml_fh, tag='page')
        for page_count, page in enumerate(wikipedia):

            if limit_pages and page_count == limit_pages:
                break

            page_title = page['title']
            page_markup = page['text']

            mid = page_title_to_mid[page_title]
            if mid:
                entity_label = freebase_data[mid]['label']
                entity_label_matcher = _build_phrase_matcher(nlp, [entity_label])

                page_text = wtp.parse(page_markup).plain_text()
                spacy_doc = nlp.make_doc(page_text)
                matches = entity_label_matcher(spacy_doc)

                spans = {(start, end) for match_id, start, end in matches}
                filtered_spans = _filter_spans(spans)

                db_matches: List[Match] = []
                for start, end in filtered_spans:
                    match_span = spacy_doc[start:end]
                    match_text = match_span.text

                    start_char = match_span.start_char
                    end_char = match_span.end_char

                    context_start = max(match_span.start_char - 20, 0)
                    context_end = min(match_span.end_char + 20, len(page_text))
                    context = page_text[context_start:context_end]

                    db_match = Match(mid, entity_label, match_text, page_title, start_char, end_char, context)
                    db_matches.append(db_match)

                for m in db_matches:
                    insert_match(matches_conn, m)


def _build_phrase_matcher(nlp: English, patterns: List[str]) -> PhraseMatcher:
    matcher = PhraseMatcher(nlp.vocab)
    spacy_patterns = list(nlp.pipe(patterns))
    matcher.add('Patterns', None, *spacy_patterns)

    return matcher


def _filter_spans(spans):
    filtered_spans = []
    for span in spans:
        keep_span = True
        for other_span in spans.difference({span}):
            if _contains(other_span, span):
                keep_span = False
                break

        if keep_span:
            filtered_spans.append(span)

    return filtered_spans


def _contains(x, y):
    return x[0] <= y[0] and x[1] >= y[1] and (x[0] != y[0] or x[1] != y[1])
