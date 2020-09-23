import os
import random
import spacy
import sqlite3

from argparse import ArgumentParser
from datetime import datetime
from os import remove
from os.path import isfile
from typing import List, Tuple

from dao.contexts import create_contexts_table, insert_contexts
from dao.mid2ent import load_mid2ent
from dao.matches import select_contexts, select_mids_with_labels
from util import log


def main():
    """
    - Parse args
    - Print applied config
    - Seed random generator
    - Check if files already exist
    - Run actual program
    """

    arg_parser = ArgumentParser(description='Crop and store context for entity matches')

    arg_parser.add_argument('matches_db', metavar='matches-db',
                            help='path to input matches DB')

    arg_parser.add_argument('contexts_db', metavar='contexts-db',
                            help='path to output contexts DB')

    default_context_size = 100
    arg_parser.add_argument('--context-size', dest='context_size', type=int, default=default_context_size,
                            help='consider ... chars on each side of the entity mention'
                                 ' (default: %d)' % default_context_size)

    arg_parser.add_argument('--crop-sentences', dest='crop_sentences', action='store_true',
                            help='crop contexts at sentence boundaries (instead of token boundaries),'
                                 'sentences will be separated by new line')

    default_limit_contexts = 100
    arg_parser.add_argument('--limit-contexts', dest='limit_contexts', type=int, default=default_limit_contexts,
                            help='max number of contexts per entity (default: %d)' % default_limit_contexts)

    arg_parser.add_argument('--limit-entities', dest='limit_entities', type=int, default=None,
                            help='for debugging: process only first ... entities (default: None)')

    arg_parser.add_argument('--overwrite', action='store_true',
                            help='overwrite contexts DB if it already exists')

    arg_parser.add_argument('--random-seed', dest='random_seed',
                            help='random seed, use together with PYTHONHASHSEED for reproducibility')

    args = arg_parser.parse_args()

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('Matches DB', args.matches_db))
    print('    {:20} {}'.format('Contexts DB', args.contexts_db))
    print()
    print('    {:20} {}'.format('Context size', args.context_size))
    print('    {:20} {}'.format('Crop sentences', args.crop_sentences))
    print('    {:20} {}'.format('Limit contexts', args.limit_contexts))
    print('    {:20} {}'.format('Limit entities', args.limit_entities))
    print('    {:20} {}'.format('Overwrite', args.overwrite))
    print('    {:20} {}'.format('Random seed', args.random_seed))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', os.getenv('PYTHONHASHSEED')))
    print()

    #
    # Seed random generator
    #

    if args.random_seed:
        random.seed(args.random_seed)

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

    #
    # Run actual program
    #

    crop_contexts(args.matches_db, args.contexts_db, args.context_size, args.crop_sentences, args.limit_contexts,
                  args.limit_entities)


def crop_contexts(matches_db: str, contexts_db: str, context_size: int, crop_sentences: bool, limit_contexts: int,
                  limit_entities: int):
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

        nlp = spacy.load('en_core_web_lg')
        create_contexts_table(contexts_conn)

        mids_with_labels: List[Tuple[str, str]] = select_mids_with_labels(matches_conn, limit_entities)
        mid2ent = load_mid2ent(r'data/entity2id.txt')

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


if __name__ == '__main__':
    main()
