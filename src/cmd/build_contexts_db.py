import csv
import json
import os
import random
import sqlite3

from argparse import ArgumentParser, Namespace
from os import remove
from os.path import isfile

import spacy
from spacy.matcher import PhraseMatcher

from dao.contexts_db import create_contexts_table, insert_contexts
from dao.matches_db import select_contexts, select_distinct_mentions
from dao.mid2ent_txt import load_mid2ent
from util.util import log


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        freenode-json
        links-db
        matches-db
        contexts-db
        --context-size
        --crop-sentences
        --csv-file
        --limit-contexts
        --limit-entities
        --overwrite
    """

    parser.add_argument('freenode_json', metavar='freenode-json',
                        help='Path to input Freenode JSON')

    parser.add_argument('matches_db', metavar='matches-db',
                        help='Path to input matches DB')

    parser.add_argument('contexts_db', metavar='contexts-db',
                        help='Path to output contexts DB')

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

    freenode_json = args.freenode_json
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
    print('    {:20} {}'.format('freenode-json', freenode_json))
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

    if not isfile(freenode_json):
        print('Freenode JSON not found')
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

    _build_contexts_db(freenode_json, matches_db, contexts_db, context_size, crop_sentences, csv_file,
                       limit_contexts, limit_entities)


def _build_contexts_db(freenode_json: str, matches_db: str, contexts_db: str, context_size: int,
                       crop_sentences: bool, csv_file: str, limit_contexts: int, limit_entities: int):
    """
    - Load English spaCy model
    - Create contexts DB
    - For each entity in matches DB
        - Query contexts
        - Shuffle and limit contexts
        - Crop to token/sentence boundary
        - Mask entity in cropped context
        - Persist masked contexts
        - Log progress
    """

    with sqlite3.connect(matches_db) as matches_conn, \
            sqlite3.connect(contexts_db) as contexts_conn:

        print()
        log('Load Freenode JSON...')
        freenode_data = json.load(open(freenode_json, 'r'))
        log('Done')

        print('Load spaCy model...', end='')
        nlp = spacy.load('en_core_web_lg')
        print(' done')

        create_contexts_table(contexts_conn)
        mid2ent = load_mid2ent(r'data/entity2id.txt')

        for entity_count, freenode_data_item in enumerate(freenode_data.items()):
            if limit_entities and entity_count == limit_entities:
                break

            mid, entity_data = freenode_data_item

            entity_label = entity_data['label']
            wiki_url = entity_data['wikipedia']

            if not wiki_url:
                continue

            #
            # Get contexts
            #

            contexts = select_contexts(matches_conn, mid, context_size)
            random.shuffle(contexts)
            limited_contexts = contexts[:limit_contexts]

            #
            # Crop to token/sentence boundary
            #

            cropped_contexts = []
            for context in limited_contexts:
                doc = nlp(context)

                if crop_sentences:
                    sents = [sent.string.strip() for sent in doc.sents][1:-1]
                    cropped_context = '\n'.join(sents)
                else:
                    tokens = [token.string.strip() for token in doc if not token.is_space][1:-1]
                    cropped_context = ' '.join(tokens)

                if cropped_context:
                    cropped_contexts.append(cropped_context)

            #
            # Mask and persist contexts
            #

            aliases = select_distinct_mentions(matches_conn, mid)

            matcher = PhraseMatcher(nlp.vocab)
            patterns = list(nlp.pipe({entity_label} | set(aliases)))
            matcher.add('Entities', None, *patterns)

            contexts_batch = []
            for context in cropped_contexts:
                spacy_doc = nlp.make_doc(context)
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

                mutable_context = list(context)
                for start, end in kept_spans:
                    match_span = spacy_doc[start:end]

                    start_char = match_span.start_char
                    end_char = match_span.end_char

                    for i in range(start_char, end_char):
                        mutable_context[i] = '#'

                masked_context = ''.join(mutable_context)
                contexts_batch.append((mid2ent[mid], masked_context, entity_label))

            insert_contexts(contexts_conn, contexts_batch)
            contexts_conn.commit()

            #
            # Log progress
            #

            log('{:,} | {} | {:,}/{:,} contexts'.format(
                entity_count, entity_label, len(limited_contexts), len(contexts)))

            if csv_file:
                with open(csv_file, 'a', newline='') as csv_fh:
                    csv.writer(csv_fh).writerow([entity_label, len(contexts)])
