import argparse
import re
import sqlite3

from argparse import ArgumentParser
from datetime import datetime
from os import remove
from os.path import isfile

from dao.contexts import insert_context, create_contexts_table
from dao.matches import select_distinct_entities, select_contexts


def main():
    """
    - Parse args
    - Print applied config
    - Check if files already exist
    - Crop contexts
    """

    parser = ArgumentParser(description='Crop and store context for entity matches')

    parser.add_argument('matches_db', metavar='matches-db',
                        help='path to input matches DB')

    parser.add_argument('contexts_db', metavar='contexts-db',
                        help='path to output contexts DB')

    default_context_size = 100
    parser.add_argument('--context-size', dest='context_size', type=int, default=default_context_size,
                        help='consider ... chars on each side of the entity mention'
                             ' (default: %d)' % default_context_size)

    parser.add_argument('--crop-sentences', dest='crop_sentences', action='store_true',
                        help='crop contexts at sentence boundaries (instead of token boundaries),'
                             'sentences will be separated by new line')

    default_limit_contexts = 100
    parser.add_argument('--limit-contexts', dest='limit_contexts', type=int, default=default_limit_contexts,
                        help='max number of contexts per entity (default: %d)' % default_limit_contexts)

    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite contexts DB if it already exists')

    args = parser.parse_args()

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
    print('    {:20} {}'.format('Overwrite', args.overwrite))
    print()

    #
    # Check for input/output files
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
    # Run program
    #

    crop_contexts(args.matches_db, args.contexts_db, args.context_size, args.crop_sentences, args.limit_contexts)


#
# CROP CONTEXTS
#

def crop_contexts(matches_db, contexts_db, context_size, crop_sentences, limit_contexts):
    with sqlite3.connect(matches_db) as matches_conn, \
            sqlite3.connect(contexts_db) as contexts_conn:

        create_contexts_table(contexts_conn)

        entities = select_distinct_entities(matches_conn)

        for i, entity in enumerate(entities):
            print('{} | {:,} entities | {}'.format(datetime.now().strftime("%H:%M:%S"), i, entity))

            contexts = select_contexts(matches_conn, entity, context_size, limit_contexts)

            cropped_contexts = []
            for context in contexts:
                regex = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s' if crop_sentences else r'\s'
                match = re.search(regex, context)
                if match:
                    start = match.end()
                    end = context.rfind(re.findall(regex, context)[-1])
                    if start < end:
                        cropped_contexts.append(context[start:end])

            masked_contexts = [context.replace(entity, '') for context in cropped_contexts]

            for masked_context in masked_contexts:
                insert_context(contexts_conn, entity, masked_context)

            contexts_conn.commit()


#
#
#

if __name__ == '__main__':
    main()
