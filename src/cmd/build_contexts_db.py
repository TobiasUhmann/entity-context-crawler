import csv
import os
import random
import spacy
import sqlite3

from argparse import ArgumentParser, Namespace
from os import remove
from os.path import isfile
from typing import List, Tuple

from dao.contexts import create_contexts_table, insert_contexts
from dao.mid2ent import load_mid2ent
from dao.matches import select_contexts, select_mids_with_labels
from util.util import log


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        matches-db
        contexts-db
        --context-size
        --crop-sentences
        --csv-file
        --limit-contexts
        --limit-entities
        --overwrite
    """

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
                        help='Overwrite contexts DB if it already exists')


def run(args: Namespace):
    """
    - Print applied config
    - Check if files already exist
    - Run actual program
    """

    print('Applied config:')
    print('    {:20} {}'.format('Matches DB', args.matches_db))
    print('    {:20} {}'.format('Contexts DB', args.contexts_db))
    print()
    print('    {:20} {}'.format('Context size', args.context_size))
    print('    {:20} {}'.format('Crop sentences', args.crop_sentences))
    print('    {:20} {}'.format('CSV file', args.csv_file))
    print('    {:20} {}'.format('Limit contexts', args.limit_contexts))
    print('    {:20} {}'.format('Limit entities', args.limit_entities))
    print('    {:20} {}'.format('Overwrite', args.overwrite))
    print('    {:20} {}'.format('Random seed', args.random_seed))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', os.getenv('PYTHONHASHSEED')))
    print()

    #
    # Check if files already exist
    #

    if not isfile(args.matches_db):
        print('Matches DB not found')
        exit()

    if isfile(args.contexts_db):
        if args.overwrite:
            remove(args.contexts_db)
        else:
            print('Contexts DB already exists. Use --overwrite to overwrite it')
            exit()

    if isfile(args.csv_file):
        if args.overwrite:
            remove(args.csv_file)
        else:
            print('CSV file already exists. Use --overwrite to overwrite it')
            exit()

    #
    # Run actual program
    #

    crop_contexts(args.matches_db, args.contexts_db, args.context_size, args.crop_sentences, args.csv_file,
                  args.limit_contexts, args.limit_entities)


def crop_contexts(matches_db: str, contexts_db: str, context_size: int, crop_sentences: bool, csv_file: str,
                  limit_contexts: int, limit_entities: int):
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

        print('Load spaCy model...', end='')
        nlp = spacy.load('en_core_web_lg')
        print(' done')

        create_contexts_table(contexts_conn)
        mid2ent = load_mid2ent(r'data/entity2id.txt')

        print('Select MIDs...', end='')
        mids_with_labels: List[Tuple[str, str]] = select_mids_with_labels(matches_conn, limit_entities)
        print(' done')

        for i, mid_with_label, in enumerate(mids_with_labels):
            mid, entity_label = mid_with_label

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

            masked_contexts = [context.replace(entity_label, '[MASK]') for context in cropped_contexts]

            contexts_data = [(mid2ent[mid], masked_context, entity_label) for masked_context in masked_contexts]
            insert_contexts(contexts_conn, contexts_data)

            contexts_conn.commit()

            #
            # Log progress
            #

            log('{:,} | {} | {:,}/{:,} contexts'.format(i, entity_label, len(limited_contexts), len(contexts)))

            if csv_file:
                with open(csv_file, 'a', newline='') as csv_fh:
                    csv.writer(csv_fh).writerow([entity_label, len(contexts)])


if __name__ == '__main__':
    run()
