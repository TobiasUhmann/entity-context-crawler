import json
import os
import sqlite3
import time
import urllib
from argparse import ArgumentParser, Namespace
from collections import defaultdict
from multiprocessing import Pool, cpu_count
from os import remove
from os.path import isfile
from typing import Tuple

import spacy
import wikitextparser as wtp
from spacy.language import Language
from spacy.matcher import PhraseMatcher

from entity_context_crawler.dao.matches_db import create_matches_table, Match, insert_match, Mention, insert_page, insert_or_ignore_mention, \
    Page, create_pages_table, create_mentions_table, PageStats
from entity_context_crawler.util.log import log
from entity_context_crawler.util.wikipedia import Wikipedia


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
    - Check if output files already exist
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
    # Check if output files already exist
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

    with open(freebase_json, 'r', encoding='utf-8') as f:
        freebase_data = json.load(f)

    with open(wiki_xml, 'rb') as wiki_xml_fh:
        wikipedia = Wikipedia(wiki_xml_fh, limit_pages)

        init_args = (freebase_data,)
        with Pool(cpu_count() // 2, initializer=_init_worker, initargs=init_args) as pool:
            for page_count, page_result in enumerate(pool.imap_unordered(_process_page, wikipedia)):

                db_page, db_matches, db_mentions, duration, exception = page_result

                if exception:
                    log('ERROR | {:9,} | {}'.format(page_count, str(exception)))
                    continue

                insert_page(matches_conn, db_page)

                for db_match in db_matches:
                    insert_match(matches_conn, db_match)

                for db_mention in db_mentions:
                    insert_or_ignore_mention(matches_conn, db_mention)

                matches_conn.commit()

                log_page_info(page_count, db_page.title, db_page.stats, duration)

        print()
        print('Stats')
        print('\tSkipped special pages: {}'.format(wikipedia.skipped_special_pages))
        print()


def log_page_info(page_count: int, page_title: str, stats: PageStats, duration: float):
    log(
        'INFO '
        ' | {:9,}'
        ' | {:6,} ms'
        ' | {:4}/{:4} links'
        ' | {:3}/{:3} mentions'
        ' | {:7,} chars'
        ' | {:3}% used'
        ' | {:4} matches'
        ' | {}'
            .format(
            page_count,
            round(duration * 1000),
            stats.entity_link_count, stats.link_count,
            stats.unique_mention_count, stats.mention_count,
            stats.text_len,
            0 if stats.text_len == 0 else round(stats.clean_text_len / stats.text_len * 100),
            stats.match_count,
            page_title,
        ))


worker_globals: Tuple


def _init_worker(freebase_data):
    global worker_globals

    entity_page_title_to_mid = _get_entity_page_title_to_mid(freebase_data)

    nlp = spacy.load('en_core_web_lg')

    worker_globals = (freebase_data, entity_page_title_to_mid, nlp)


def _get_entity_page_title_to_mid(freebase_data):
    entity_page_title_to_mid = {}
    for mid, entity_data in freebase_data.items():
        page_url = entity_data['wikipedia']
        if page_url:
            decoded_page_url = urllib.parse.unquote(page_url)
            page_title = decoded_page_url.rsplit('/', 1)[-1].replace('_', ' ')
            entity_page_title_to_mid[page_title] = mid

    return entity_page_title_to_mid


def _process_page(page: dict):
    global worker_globals
    freebase_data, entity_page_title_to_mid, nlp = worker_globals

    try:
        start_time = time.time()

        page_title = page['title']
        page_markup = page['text']

        # Parse markup -> AST
        parsed = wtp.parse(page_markup)

        # Get links that refer to Wiki pages of Freebase entities
        links = parsed.wikilinks
        entity_links = [link for link in links if link.title in entity_page_title_to_mid]

        # Get mention -> MID mapping from links, e.g.:
        # { 'Berlin' -> ['/m/abc'], 'Bonn' -> ['/m/xyz'], 'capital' -> ['/m/abc', '/m/xyz'] }
        #
        # Note: Multiple links with the same text that link different pages
        #       should not occur according to Wikipedia standards
        mention_to_mids = defaultdict(set)
        for link in entity_links:
            mention = link.text if link.text else link.title
            mention_to_mids[mention].add(entity_page_title_to_mid[link.title])

        # Remove non-unique mentions
        mention_to_mid = {mention: list(mids)[0] for mention, mids in mention_to_mids.items()
                          if len(mids) == 1}

        # Prepare DB mentions. Will be returned to the main thread
        mentions = list(nlp.pipe(mention_to_mid.keys()))
        db_mentions = [Mention(mid, freebase_data[mid]['label'], mention)
                       for mention, mid in mention_to_mid.items()]

        matcher = PhraseMatcher(nlp.vocab)
        matcher.add('Patterns', None, *mentions)

        # Markup -> plain text, clean up plain text
        page_text = parsed.plain_text()
        clean_page_text = clean_up_text(nlp, page_text)

        # Search mentions
        spacy_doc = nlp.make_doc(clean_page_text)
        matches = matcher(spacy_doc)

        db_matches = []
        for _, start, end in matches:
            match_span = spacy_doc[start:end]
            mention = match_span.text  # mention which matched (from the whole mention set)

            mid = mention_to_mid[mention]
            entity_label = freebase_data[mid]['label']

            start_char = match_span.start_char
            end_char = match_span.end_char

            context_start = max(match_span.start_char - 20, 0)
            context_end = min(match_span.end_char + 20, len(clean_page_text))
            context = clean_page_text[context_start:context_end]

            db_match = Match(mid, entity_label, mention, page_title, start_char, end_char, context)
            db_matches.append(db_match)

        stop_time = time.time()
        duration = stop_time - start_time

        stats = PageStats(
            len(links),
            len(entity_links),
            len(mention_to_mids),
            len(mention_to_mid),
            len(page_text),
            len(clean_page_text),
            len(db_matches),
        )

        db_page = Page(page_title, clean_page_text, stats)

        return db_page, db_matches, db_mentions, duration, None

    except Exception as e:
        return None, None, None, None, e


def clean_up_text(nlp: Language, page_text: str) -> str:
    """
    Remove sentence fragments and markup, leaving paragraphs with whole sentences.

    1. Split page text into paragraphs (split at '\n') and paragraphs into sentences (using NLP)
    2. Remove bad sentences (too short, contains markup chars, etc.)
    3. Join sentences and paragraphs back together
    """

    paragraphs = page_text.split('\n')
    clean_paragraphs = []

    for paragraph in paragraphs:

        # Optimization: If paragraph < 40, then no sentence >= 40, therefore skip expensive NLP
        if len(paragraph) < 40:
            continue

        doc = nlp(paragraph)
        sents = [sent.text for sent in doc.sents]

        clean_sents = [sent for sent in sents if
                       len(sent) >= 40
                       and sent[0].isupper()
                       and '|' not in sent
                       and '=' not in sent
                       and 'http' not in sent
                       and 'Category:' not in sent]

        clean_paragraph = ' '.join(clean_sents)

        if clean_paragraph:
            clean_paragraphs.append(clean_paragraph)

    clean_page_text = '\n\n'.join(clean_paragraphs)

    return clean_page_text
