import json
import os
import sqlite3
from argparse import ArgumentParser, Namespace
from collections import defaultdict
from multiprocessing import Pool, cpu_count
from os import remove
from os.path import isfile
from typing import Tuple

import wikitextparser as wtp
from spacy.lang.en import English
from spacy.matcher import PhraseMatcher

from dao.matches_db import create_matches_table, Match, insert_match, Mention, insert_page, insert_or_ignore_mention, \
    Page, create_pages_table, create_mentions_table
from util.util import log
from util.wikipedia import Wikipedia


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        wiki-xml
        freebase-json
        matches-db
        --in-memory
        --limit-pages
        --overwrite
    """

    parser.add_argument('wiki_xml', metavar='wiki-xml',
                        help='Path to (input) Wikipedia XML')

    parser.add_argument('freebase_json', metavar='freebase-json',
                        help='Path to (input) Freebase JSON')

    parser.add_argument('matches_db', metavar='matches-db',
                        help='Path to (output) matches DB')

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
    freebase_json = args.freebase_json
    matches_db = args.matches_db

    in_memory = args.in_memory
    limit_pages = args.limit_pages
    overwrite = args.overwrite

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('wiki-xml', wiki_xml))
    print('    {:20} {}'.format('freebase-json', freebase_json))
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

    if not isfile(wiki_xml):
        print('Wikipedia XML not found')
        exit()

    if not isfile(freebase_json):
        print('Freebase JSON not found')
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

    _build_matches_db(wiki_xml, freebase_json, matches_db, in_memory, limit_pages)


def _build_matches_db(wiki_xml, freebase_json, matches_db, in_memory, limit_pages):
    if in_memory:
        _run_in_memory(wiki_xml, freebase_json, matches_db, limit_pages)
    else:
        _run_on_disk(wiki_xml, freebase_json, matches_db, limit_pages)


def _run_on_disk(wiki_xml, freebase_json, matches_db, limit_pages):
    with sqlite3.connect(matches_db) as matches_conn:
        _process_wiki_xml(wiki_xml, freebase_json, matches_conn, limit_pages)

        log()
        log('Finished successfully')


def _run_in_memory(wiki_xml, freebase_json, matches_db, limit_pages):
    with sqlite3.connect(':memory:') as memory_matches_conn:
        _process_wiki_xml(wiki_xml, freebase_json, memory_matches_conn, limit_pages)

        log()
        log('Persist...')

        with sqlite3.connect(matches_db) as disk_matches_conn:
            for line in memory_matches_conn.iterdump():
                if line not in ('BEGIN;', 'COMMIT;'):  # let python handle the transactions
                    disk_matches_conn.execute(line)

        log('Done')


def _process_wiki_xml(wiki_xml, freebase_json, matches_conn, limit_pages):
    """
    Iterate through all Freebase entities. For each entity, get its Wikipedia page as well
    as the directly linked pages. On those pages, search for the entity label and its aliases.
    Persist the matches in the matches DB.
    """

    create_pages_table(matches_conn)
    create_matches_table(matches_conn)
    create_mentions_table(matches_conn)

    freebase_data = json.load(open(freebase_json, 'r'))

    with open(wiki_xml, 'rb') as wiki_xml_fh:
        wikipedia = Wikipedia(wiki_xml_fh, tag='page')

        init_args = (freebase_data,)
        with Pool(cpu_count() // 2, initializer=_init_worker, initargs=init_args) as pool:
            for page_count, page_result in enumerate(pool.imap_unordered(_process_page, wikipedia)):

                db_page, db_matches, db_mentions, exception = page_result

                if exception:
                    log('ERROR | {} | {}'.format(page_count, str(exception)))
                    continue

                insert_page(matches_conn, db_page)

                for db_match in db_matches:
                    insert_match(matches_conn, db_match)

                for db_mention in db_mentions:
                    insert_or_ignore_mention(matches_conn, db_mention)

                matches_conn.commit()

                log('INFO  | {} | {} | {}'.format(page_count, db_page.title, len(db_matches)))


worker_globals: Tuple


def _init_worker(freebase_data):
    global worker_globals

    entity_page_title_to_mid = _get_entity_page_title_to_mid(freebase_data)

    nlp = English()
    nlp.vocab.lex_attr_getters = {}

    worker_globals = (freebase_data, entity_page_title_to_mid, nlp)


def _get_entity_page_title_to_mid(freebase_data):
    entity_page_title_to_mid = {}
    for mid, entity_data in freebase_data.items():
        page_url = entity_data['wikipedia']
        if page_url:
            page_title = page_url.rsplit('/', 1)[-1].replace('_', ' ')
            entity_page_title_to_mid[page_title] = mid

    return entity_page_title_to_mid


def _process_page(page):
    global worker_globals

    try:
        freebase_data, entity_page_title_to_mid, nlp = worker_globals

        page_title = page['title']
        page_markup = page['text']

        core_markup = _get_core_markup(page_markup)
        parsed = wtp.parse(core_markup)

        links = parsed.wikilinks
        entity_links = [link for link in links if link.title in entity_page_title_to_mid]

        mention_to_mids = defaultdict(list)
        for link in entity_links:
            mention = link.text if link.text else link.title
            mention_to_mids[mention].append(entity_page_title_to_mid[link.title])

        mention_to_mid = {mention: mids[0] for mention, mids in mention_to_mids.items() if len(mids) == 1}

        mentions = list(nlp.pipe(mention_to_mid.keys()))
        db_mentions = [Mention(mid, freebase_data[mid]['label'], mention) for mention, mid in mention_to_mid.items()]

        matcher = PhraseMatcher(nlp.vocab)
        matcher.add('Patterns', None, *mentions)

        page_text = parsed.plain_text()
        spacy_doc = nlp.make_doc(page_text)
        matches = matcher(spacy_doc)

        db_matches = []
        for _, start, end in matches:
            match_span = spacy_doc[start:end]
            mention = match_span.text

            mid = mention_to_mid[mention]
            entity_label = freebase_data[mid]['label']

            start_char = match_span.start_char
            end_char = match_span.end_char

            context_start = max(match_span.start_char - 20, 0)
            context_end = min(match_span.end_char + 20, len(page_text))
            context = page_text[context_start:context_end]

            db_match = Match(mid, entity_label, mention, page_title, start_char, end_char, context)
            db_matches.append(db_match)

        db_page = Page(page_title, page_text)

        return db_page, db_matches, db_mentions, None

    except Exception as e:
        return None, None, None, e


def _get_core_markup(markup: str) -> str:
    parsed = wtp.parse(markup)

    intro = parsed.get_sections(include_subsections=False, level=0)[0]
    sections = parsed.get_sections(include_subsections=True, level=2)

    section_blacklist = {'see also', 'references', 'further reading', 'external links'}
    filtered_sections = [section for section in sections
                         if section.title.strip().lower() not in section_blacklist]

    intro_markup = intro.contents
    section_markups = [section.contents for section in filtered_sections]

    markups = [intro_markup]
    markups.extend(section_markups)

    return '\n'.join(markups)
