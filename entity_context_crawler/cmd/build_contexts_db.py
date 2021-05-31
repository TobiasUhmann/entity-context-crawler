import csv
import json
import os
import random
import sqlite3
from argparse import ArgumentParser, Namespace
from os import remove
from os.path import isfile
from typing import List, Tuple, Dict

import spacy
from spacy.lang.en import English
from spacy.language import Language
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc

from entity_context_crawler.dao.contexts_db import create_contexts_table, insert_contexts, Context
from entity_context_crawler.dao.matches_db import select_contexts, select_entity_mentions
from entity_context_crawler.dao.mid2rid_txt import load_mid2rid
from entity_context_crawler.util.log import log, log_start, log_end


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        freebase-json
        mid2rid-txt
        matches-db
        contexts-db
        --context-size
        --crop-sentences
        --csv-file
        --limit-contexts
        --limit-entities
        --overwrite
    """

    parser.add_argument('freebase_json', metavar='freebase-json',
                        help='Path to (input) Freebase JSON')

    parser.add_argument('mid2rid_txt', metavar='mid2rid-txt',
                        help='Path to (input) mid2rid TXT')

    parser.add_argument('matches_db', metavar='matches-db',
                        help='Path to (input) matches DB')

    parser.add_argument('contexts_db', metavar='contexts-db',
                        help='Path to (output) contexts DB')

    default_context_size = 100
    parser.add_argument('--context-size', dest='context_size', type=int, metavar='INT', default=default_context_size,
                        help='Consider ... chars on each side of the entity mention'
                             ' (default: {})'.format(default_context_size))

    parser.add_argument('--crop-sentences', dest='crop_sentences', action='store_true',
                        help='Crop contexts at sentence boundaries (instead of token boundaries),'
                             ' sentences will be separated by new lines')

    default_csv_file = None
    parser.add_argument('--csv-file', dest='csv_file', metavar='STR', default=default_csv_file,
                        help='Log context stats to CSV file at path ... (default: {})'.format(default_csv_file))

    default_limit_contexts = None
    parser.add_argument('--limit-contexts', dest='limit_contexts', type=int, metavar='INT',
                        default=default_limit_contexts,
                        help='Max number of contexts per entity (default: {})'.format(default_limit_contexts))

    default_limit_entities = None
    parser.add_argument('--limit-entities', dest='limit_entities', type=int, metavar='INT',
                        default=default_limit_entities,
                        help='Early stop after ... entities (default: {})'.format(default_limit_entities))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite contexts DB and CSV file if they already exist')


def run(args: Namespace):
    """
    - Print applied config
    - Check if output files already exist
    - Run actual program
    """

    freebase_json = args.freebase_json
    mid2rid_txt = args.mid2rid_txt
    matches_db = args.matches_db
    contexts_db = args.contexts_db

    context_size = args.context_size
    crop_sentences = args.crop_sentences
    csv_file = args.csv_file
    limit_contexts = args.limit_contexts
    limit_entities = args.limit_entities
    overwrite = args.overwrite
    random_seed = args.random_seed

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('freebase-json', freebase_json))
    print('    {:20} {}'.format('mid2rid-txt', mid2rid_txt))
    print('    {:20} {}'.format('matches-db', matches_db))
    print('    {:20} {}'.format('contexts_db', contexts_db))
    print()
    print('    {:20} {}'.format('--context-size', context_size))
    print('    {:20} {}'.format('--crop-sentences', crop_sentences))
    print('    {:20} {}'.format('--csv-file', csv_file))
    print('    {:20} {}'.format('--limit-contexts', limit_contexts))
    print('    {:20} {}'.format('--limit-entities', limit_entities))
    print('    {:20} {}'.format('--overwrite', overwrite))
    print('    {:20} {}'.format('--random-seed', random_seed))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', python_hash_seed))
    print()

    #
    # Check if output files already exist
    #

    if not isfile(freebase_json):
        print('Freebase JSON not found')
        exit()

    if not isfile(mid2rid_txt):
        print('mid2rid TXT not found')
        exit()

    if not isfile(matches_db):
        print('Matches DB not found')
        exit()

    if isfile(contexts_db):
        if overwrite:
            remove(contexts_db)
        else:
            print('Contexts DB already exists, use --overwrite to overwrite it')
            exit()

    if isfile(csv_file):
        if overwrite:
            remove(csv_file)
        else:
            print('CSV file already exists, use --overwrite to overwrite it')
            exit()

    #
    # Run actual program
    #

    _build_contexts_db(freebase_json, mid2rid_txt, matches_db, contexts_db, context_size, crop_sentences, csv_file,
                       limit_contexts, limit_entities)


def _build_contexts_db(freebase_json: str, mid2rid_txt: str, matches_db: str, contexts_db: str, context_size: int,
                       crop_sentences: bool, csv_file: str, limit_contexts: int, limit_entities: int):
    """
    - Load Freebase JSON
    - Load spaCy model
    - Create contexts DB
    - For each entity in matches DB
        - Query contexts
        - Shuffle and limit contexts
        - Crop to token/sentence boundary
        - Persist masked contexts
        - Log progress
    """

    with sqlite3.connect(matches_db) as matches_conn, \
            sqlite3.connect(contexts_db) as contexts_conn:

        log('Load Freebase JSON')
        with open(freebase_json, 'r', encoding='utf-8') as f:
            freebase_data: Dict[str, Dict] = json.load(f)

        log('Load mid2rid TXT')
        mid2rid: Dict[str, int] = load_mid2rid(mid2rid_txt)

        log('Load spaCy model')
        nlp: English = spacy.load('en_core_web_lg')
        log()

        create_contexts_table(contexts_conn)

        freebase_items = list(freebase_data.items())
        random.shuffle(freebase_items)
        for entity_count, freebase_item in enumerate(freebase_items):
            mid, entity_data = freebase_item

            if mid not in mid2rid:
                continue

            # Early stop after ... entities
            if limit_entities and entity_count == limit_entities:
                break

            entity_label = entity_data['label']
            wiki_url = entity_data['wikipedia']

            if not wiki_url:
                continue

            # Log progress (start)
            log_start('{:,} | {}'.format(entity_count, entity_label))

            # Sample contexts
            all_context_rows = select_contexts(matches_conn, mid, context_size)
            random.shuffle(all_context_rows)
            some_context_rows = all_context_rows[:limit_contexts]

            # Build entity PhraseMatcher
            entity_mentions = select_entity_mentions(matches_conn, mid)
            entity_patterns = list({entity_label} | set(entity_mentions))
            entity_matcher = PhraseMatcher(nlp.vocab)
            entity_matcher.add('', None, *list(nlp.pipe(entity_patterns)))

            # Crop and mask contexts
            cropped_context_rows = crop_contexts(nlp, some_context_rows, crop_sentences, entity_matcher)
            masked_context_rows = mask_contexts(nlp, cropped_context_rows, entity_matcher)

            # Persist contexts
            db_contexts = [Context(mid2rid[mid], entity_label, mention, page_title, unmasked_context, masked_context)
                           for masked_context, unmasked_context, page_title, mention in masked_context_rows]
            insert_contexts(contexts_conn, db_contexts)
            contexts_conn.commit()

            # Log progress (end)
            log_end(' | {:,}/{:,} contexts'.format(len(some_context_rows), len(all_context_rows)))

            # Persist stats
            if csv_file:
                with open(csv_file, 'a', encoding='utf-8', newline='') as csv_fh:
                    csv.writer(csv_fh).writerow([entity_label, len(all_context_rows)])


def crop_contexts(
        nlp: Language,
        ragged_context_rows: List[Tuple[str, str, str]],
        crop_sentences: bool,
        entity_matcher: PhraseMatcher
) -> List[Tuple[str, str, str]]:
    """
    Crop each context to the next token/sentence boundary and filter out sentences
    without any matches. Might yield less contexts than given as contexts are dropped
    if cropped to the empty string.

    :param ragged_context_rows [(ragged_context, page_title, mention)]
    :return [(cropped_context, page_title, mention)]
    """

    cropped_context_rows = []
    for ragged_context, page_title, mention in ragged_context_rows:
        context_doc: Doc = nlp(ragged_context)

        if crop_sentences:
            raw_sents = [sent.text for sent in context_doc.sents]

            # - Split sentences containing '\n' into multiple sentences
            # - Flatten the groups of splitted sentences
            # - Remove empty sentences
            # - Strip sentences
            splitted_sents = [sent.split('\n') for sent in raw_sents]
            flat_sents = [sent for group in splitted_sents for sent in group]
            stripped_sents = [sent.strip() for sent in flat_sents]
            non_empty_sents = [sent for sent in stripped_sents if len(sent) > 0]

            # - Remove bad "sentences" that do not start with an uppercase letter
            # - Remove last sentence, because it might be incomplete
            upper_sents = [sent for sent in non_empty_sents if sent[0].isupper()]
            complete_sents = upper_sents[:-1]

            # Remove sentences without entity matches
            match_sents = []
            for sent in complete_sents:
                sent_doc: Doc = nlp.make_doc(sent)
                entity_matches = entity_matcher(sent_doc)

                if entity_matches:
                    match_sents.append(sent)

            # Join remaining, real sentences
            cropped_context = '\n'.join(match_sents)

        else:
            # Remove first and last token because they might be incomplete
            tokens = [token.text.strip() for token in context_doc if not token.is_space][1:-1]

            # Note: No filtering of bad tokens here

            # Join remaining tokens
            cropped_context = ' '.join(tokens)

        # After all the filtering, context might be empty. Only take context if not empty
        if cropped_context:
            cropped_context_rows.append((cropped_context, page_title, mention))

    return cropped_context_rows


def mask_contexts(
        nlp: Language,
        unmasked_context_rows: List[Tuple[str, str, str]],
        entity_matcher: PhraseMatcher
) -> List[Tuple[str, str, str, str]]:
    """
    Replace all occurrences of all masks with hashes. Filter out context without
    any mentions.

    :param unmasked_context_rows: [(unmasked_context, page_title, mention)]
    :return [(masked_context, unmasked_context, page_title, mention)]
    """

    masked_context_rows = []
    for unmasked_context, page_title, mention in unmasked_context_rows:

        spacy_doc = nlp.make_doc(unmasked_context)
        matches = entity_matcher(spacy_doc)

        def contains(x, y):
            return x[0] <= y[0] and x[1] >= y[1] and (x[0] != y[0] or x[1] != y[1])

        spans = {(start, end) for match_id, start, end in matches}
        kept_spans = []
        for span in spans:
            keep_span = True
            for other_span in spans.difference({span}):
                if contains(other_span, span):
                    keep_span = False
                    break

            if keep_span:
                kept_spans.append(span)

        if len(kept_spans) == 0:
            continue

        mutable_context = list(unmasked_context)
        for start, end in kept_spans:
            match_span = spacy_doc[start:end]

            start_char = match_span.start_char
            end_char = match_span.end_char

            for i in range(start_char, end_char):
                mutable_context[i] = '#'

        masked_context = ''.join(mutable_context)

        masked_context_rows.append((masked_context, unmasked_context, page_title, mention))

    return masked_context_rows
