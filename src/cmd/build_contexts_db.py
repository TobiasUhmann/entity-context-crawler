import csv
import json
import os
import random
import sqlite3
from argparse import ArgumentParser, Namespace
from os import remove
from os.path import isfile
from typing import List

import spacy
from spacy.lang.en import English
from spacy.language import Language
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc

from dao.contexts_db import create_contexts_table, insert_contexts, Context
from dao.matches_db import select_contexts, select_distinct_mentions
from dao.mid2rid_txt import load_mid2rid
from util.util import log, log_start, log_end


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
    - Check if files already exist
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
    # Check if files already exist
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
        :param mid2rid_txt:
    """

    with sqlite3.connect(matches_db) as matches_conn, \
            sqlite3.connect(contexts_db) as contexts_conn:

        log('Load Freebase JSON')
        freebase_data = json.load(open(freebase_json, 'r'))

        log('Load mid2rid TXT')
        mid2rid = load_mid2rid(mid2rid_txt)

        log('Load spaCy model')
        nlp: English = spacy.load('en_core_web_lg')
        log()

        create_contexts_table(contexts_conn)

        freebase_items = list(freebase_data.items())
        random.shuffle(freebase_items)
        for entity_count, freebase_item in enumerate(freebase_items):
            mid, entity_data = freebase_item

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
            all_contexts = select_contexts(matches_conn, mid, context_size)
            random.shuffle(all_contexts)
            sampled_contexts = all_contexts[:limit_contexts]

            # Crop contexts
            cropped_contexts = crop_contexts(nlp, sampled_contexts, crop_sentences)

            # Mask contexts
            mentions = select_distinct_mentions(matches_conn, mid)
            masks = list({entity_label} | set(mentions))
            masked_contexts = mask_contexts(nlp, cropped_contexts, masks)

            # Persist contexts
            db_contexts = [Context(mid2rid[mid], entity_label, cropped_context, masked_context)
                           for cropped_context, masked_context in zip(cropped_contexts, masked_contexts)]
            insert_contexts(contexts_conn, db_contexts)
            contexts_conn.commit()

            # Log progress (end)
            log_end(' | {:,}/{:,} contexts'.format(len(sampled_contexts), len(all_contexts)))

            # Persist stats
            if csv_file:
                with open(csv_file, 'a', newline='') as csv_fh:
                    csv.writer(csv_fh).writerow([entity_label, len(all_contexts)])


def crop_contexts(nlp: Language, ragged_contexts: List[str], crop_sentences: bool) -> List[str]:
    """
    Crop each context to the next token/sentence boundary. Might yield less contexts than
    given as contexts are dropped if cropped to the empty string
    """

    cropped_contexts = []

    for context in ragged_contexts:
        doc: Doc = nlp(context)

        if crop_sentences:
            # Remove last sentence, because it might be incomplete
            # Do not remove first sentence, because it would be removed in the following if it was incomplete
            sents: List[str] = [sent.string.strip() for sent in doc.sents][:-1]

            # Split sentences containing '\n' into multiple sentences
            splitted_sents = [sent.split('\n') for sent in sents]

            # Flatten the groups of splitted sentences and filter out empty strings
            flat_sents = [sent for group in splitted_sents for sent in group if len(sent) > 0]

            # Filter out bad "senteces":
            # - sentence does not start with upper case letter
            # - sentence is shorter than 40 chars
            filtered_sents = filter(lambda sent: not any((
                not sent[0].isupper(),
                len(sent) < 40,
            )), flat_sents)

            # Join remaining, real sentences
            cropped_context = '\n'.join(filtered_sents)

        else:
            # Remove first and last token because they might be incomplete
            tokens = [token.string.strip() for token in doc if not token.is_space][1:-1]

            # Note: No filtering of bad tokens here

            # Join remaining tokens
            cropped_context = ' '.join(tokens)

        # After all the filtering, context might be empty. Only take context if not empty
        if cropped_context:
            cropped_contexts.append(cropped_context)

    return cropped_contexts


def mask_contexts(nlp: Language, unmasked_contexts: List[str], masks: List[str]) -> List[str]:
    """ Replace all occurrences of all masks with hashes """

    matcher = PhraseMatcher(nlp.vocab)
    patterns = list(nlp.pipe(masks))
    matcher.add('Entities', None, *patterns)

    masked_contexts = []
    for unmasked_context in unmasked_contexts:
        spacy_doc = nlp.make_doc(unmasked_context)
        matches = matcher(spacy_doc)

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
        masked_contexts.append(masked_context)

    return masked_contexts
