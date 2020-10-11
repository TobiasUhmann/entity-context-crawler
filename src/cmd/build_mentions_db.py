import json
import os
import sqlite3

from argparse import ArgumentParser, Namespace
from os import remove
from os.path import isfile

import wikitextparser as wtp
from spacy.lang.en import English
from spacy.matcher import PhraseMatcher

from dao.links_db import select_pages_linking_to, select_pages_linked_from
from dao.mentions_db import insert_mentions, Mention, create_mentions_table
from dao.pages_db import select_page
from util.util import log


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        freebase-json
        links-db
        pages-db
        mentions-db
        --commit-frequency
        --in-memory
        --limit-entities
        --overwrite
    """

    parser.add_argument('freebase_json', metavar='freebase-json',
                        help='Path to input Freebase JSON')

    parser.add_argument('links_db', metavar='links-db',
                        help='Path to input links DB')

    parser.add_argument('pages_db', metavar='pages-db',
                        help='Path to input pages DB')

    parser.add_argument('mentions_db', metavar='mentions-db',
                        help='Path to output mentions DB')

    default_commit_frequency = None
    parser.add_argument('--commit-frequency', dest='commit_frequency', type=int, metavar='INT',
                        default=default_commit_frequency,
                        help='Commit to database every ... pages instead of committing at the end only'
                             ' (default: {})'.format(default_commit_frequency))

    parser.add_argument('--in-memory', dest='in_memory', action='store_true',
                        help='Build complete mentions DB in memory before persisting it')

    default_limit_entities = None
    parser.add_argument('--limit-entities', dest='limit_entities', type=int, metavar='INT', default=default_limit_entities,
                        help='Early stop after ... entities (default: {})'.format(default_limit_entities))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite links DB if it already exists')


def run(args: Namespace):
    """
    - Print applied config
    - Check if files already exist
    - Run actual program
    """

    freebase_json = args.freebase_json
    links_db = args.links_db
    pages_db = args.pages_db
    mentions_db = args.mentions_db

    commit_frequency = args.commit_frequency
    in_memory = args.in_memory
    limit_entities = args.limit_entities
    overwrite = args.overwrite

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('freebase-json', freebase_json))
    print('    {:20} {}'.format('links-db', links_db))
    print('    {:20} {}'.format('pages-db', pages_db))
    print('    {:20} {}'.format('mentions-db', mentions_db))
    print()
    print('    {:20} {}'.format('--commit-frequency', commit_frequency))
    print('    {:20} {}'.format('--in-memory', in_memory))
    print('    {:20} {}'.format('--limit-entities', limit_entities))
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

    if not isfile(links_db):
        print('Links DB not found')
        exit()

    if not isfile(pages_db):
        print('Pages DB not found')
        exit()

    if isfile(mentions_db):
        if overwrite:
            remove(mentions_db)
        else:
            print('Mentions DB already exists, use --overwrite to overwrite it')
            exit()

    #
    # Run actual program
    #

    _build_mentions_db(freebase_json, links_db, pages_db, mentions_db, commit_frequency, in_memory, limit_entities)


def _build_mentions_db(freebase_json, links_db, pages_db, mentions_db, commit_frequency, in_memory, limit_entities):
    if in_memory:
        _run_in_memory(freebase_json, links_db, pages_db, mentions_db, commit_frequency, limit_entities)
    else:
        _run_on_disk(freebase_json, links_db, pages_db, mentions_db, commit_frequency, limit_entities)


def _run_on_disk(freebase_json, links_db, pages_db, mentions_db, commit_frequency, limit_entities):
    with sqlite3.connect(mentions_db) as mentions_conn:
        create_mentions_table(mentions_conn)

        _process_entities(freebase_json, links_db, pages_db, mentions_conn, commit_frequency, limit_entities)

        log('Done')


def _run_in_memory(freebase_json, links_db, pages_db, mentions_db, commit_frequency, limit_entities):
    with sqlite3.connect(':memory:') as memory_mentions_conn:
        create_mentions_table(memory_mentions_conn)

        _process_entities(freebase_json, links_db, pages_db, memory_mentions_conn, commit_frequency, limit_entities)

        print()
        log('Persist...')

        with sqlite3.connect(mentions_db) as disk_mentions_conn:
            for line in memory_mentions_conn.iterdump():
                if line not in ('BEGIN;', 'COMMIT;'):  # let python handle the transactions
                    disk_mentions_conn.execute(line)

        log('Done')


def _process_entities(freebase_json, links_db, pages_db, mentions_conn, commit_frequency, limit_entities):

    print()
    log('Load Freebase JSON...')
    freebase_data = json.load(open(freebase_json, 'r'))
    log('Done')

    nlp = English()
    nlp.vocab.lex_attr_getters = {}

    for entity_count, mid in enumerate(freebase_data):
        if limit_entities and limit_entities:
            break

        if commit_frequency and entity_count & commit_frequency == 0:
            log('Commit...')
            mentions_conn.commit()
            log('Done')

        _process_entity(freebase_data, links_db, pages_db, mentions_conn, mid, nlp)

        entity_label = freebase_data[mid]['label']
        log('{} | {}'.format(entity_count, entity_label))


def _process_entity(freebase_data, links_db, pages_db, mentions_conn, mid, nlp):
    """
    - Search the entity label on the entity page and on all neighbor pages
    - On each linking page:
        - Get all links to the entity page
        - Search for all matches of all link texts
    """

    entity_label = freebase_data[mid]['label']

    page_url = freebase_data[mid]['wikipedia']
    if not page_url:
        return

    page_title = page_url.rsplit('/', 1)[-1].replace('_', ' ')

    with sqlite3.connect(links_db) as links_conn:
        linking_pages = select_pages_linking_to(links_conn, page_title)
        linked_pages = select_pages_linked_from(links_conn, page_title)

    neighbor_pages = {page_title} | set(linking_pages) | set(linked_pages)

    mentions = []
    for neighbor_page in neighbor_pages:
        mentions += _find_mentions(pages_db, neighbor_page, [entity_label], nlp, mid, entity_label)

    for linking_page in linking_pages:
        aliases = _find_aliases(pages_db, linking_page)
        mentions += _find_mentions(pages_db, linking_page, aliases, nlp, mid, entity_label)

    insert_mentions(mentions_conn, mentions)


def _find_mentions(pages_db, page_title, search_terms, nlp, mid, entity_label):
    with sqlite3.connect(pages_db) as pages_conn:
        page = select_page(pages_conn, page_title)

    page_markup = _get_core_markup(page.markup)
    if not page_markup:
        return []

    matcher = PhraseMatcher(nlp.vocab)
    patterns = list(nlp.pipe(search_terms))
    matcher.add('Patterns', None, *patterns)

    page_text = wtp.parse(page_markup).plain_text()
    spacy_doc = nlp.make_doc(page_text)
    matches = matcher(spacy_doc)

    spans = {(start, end) for match_id, start, end in matches}
    filtered_spans = _filter_spans(spans)

    mentions = []
    for start, end in filtered_spans:
        match_span = spacy_doc[start:end]
        match_text = match_span.text

        start_char = match_span.start_char
        end_char = match_span.end_char

        context_start = max(match_span.start_char - 20, 0)
        context_end = min(match_span.end_char + 20, len(page_text))
        context = page_text[context_start:context_end]

        mention = Mention(mid, entity_label, match_text, page_title)
        mentions.append(mention)

    return mentions


def _find_aliases(pages_db, page_title):
    with sqlite3.connect(pages_db) as pages_conn:
        page = select_page(pages_conn, page_title)

    page_markup = _get_core_markup(page.markup)
    if not page_markup:
        return []

    wiki_links = wtp.parse(page_markup).wikilinks
    aliases = [link.text for link in wiki_links if link.title == page_title]

    return aliases


def _get_core_markup(markup: str) -> str:
    sections = wtp.parse(markup).get_sections(include_subsections=False, level=1)

    section_blacklist = {'References', 'Further Reading', 'External Links'}
    filtered_sections = [section for section in sections if section.title.strip() not in section_blacklist]

    return '\n'.join([section.content for section in filtered_sections])


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
