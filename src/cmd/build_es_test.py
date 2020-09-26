import sqlite3

from argparse import ArgumentParser, Namespace
from datetime import datetime
from elasticsearch import Elasticsearch
from os import remove
from os.path import isfile
from ryn.app.splits import load_dataset
from typing import List

from dao.contexts import create_contexts_table, insert_context, select_contexts, select_distinct_entities


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        contexts-db
        es-url
        test-contexts-db
        --limit-contexts
        --overwrite
        --verbose
    """

    parser.add_argument('contexts_db', metavar='contexts-db',
                        help='Path to input contexts DB')

    parser.add_argument('es_url', metavar='es-url',
                        help='URL of output Elasticsearch index')

    parser.add_argument('test_contexts_db', metavar='test-contexts-db',
                        help='Path to output test contexts DB')

    default_limit_contexts = None
    parser.add_argument('--limit-contexts', dest='limit_contexts', type=int, metavar='INT',
                        default=default_limit_contexts,
                        help='Process only the first ... contexts for each entity'
                             ' (default: {})'.format(default_limit_contexts))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite Elasticsearch index and contexts DB if they already exist')

    parser.add_argument('--verbose', dest='verbose', action='store_true',
                        help='Print training contexts for each entity')


def run(args: Namespace):
    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('Contexts DB', args.contexts_db))
    print('    {:20} {}'.format('Elasticsearch URL', args.es_url))
    print('    {:20} {}'.format('Test contexts DB', args.test_contexts_db))
    print()
    print('    {:20} {}'.format('Limit contexts', args.limit_contexts))
    print('    {:20} {}'.format('Overwrite', args.overwrite))
    print('    {:20} {}'.format('Verbose', args.verbose))
    print()

    #
    # Check for input/output files and Elasticsearch index
    #

    if not isfile(args.contexts_db):
        print('Contexts DB not found')
        exit()

    es = Elasticsearch([args.es_url])
    if es.indices.exists():
        if args.overwrite:
            es.indices.delete(index=args.index_name, ignore=[400, 404])
        else:
            print('Elasticsearch index already exists. Use --overwrite to overwrite it')
            exit()

    if isfile(args.test_contexts_db):
        if args.overwrite:
            remove(args.test_contexts_db)
        else:
            print('Test contexts DB already exists. Use --overwrite to overwrite it')
            exit()

    #
    # Run program
    #

    build_index(es, args.contexts_db, args.index_name, args.test_contexts_db, args.limit_contexts, args.verbose)


#
# BUILD INDEX
#

def build_index(es, contexts_db, index_name, test_contexts_db, limit_contexts, verbose):
    with sqlite3.connect(contexts_db) as contexts_conn, \
            sqlite3.connect(test_contexts_db) as test_contexts_conn:

        create_contexts_table(test_contexts_conn)

        entities: List[int] = select_distinct_entities(contexts_conn)

        dataset = load_dataset()
        id2ent = dataset.id2ent

        for i, entity in enumerate(entities):
            entity_label = id2ent[entity]

            print('{} | {:,} entities | {}'.format(datetime.now().strftime("%H:%M:%S"), i, entity_label))

            masked_contexts = select_contexts(contexts_conn, entity, limit_contexts)
            masked_contexts = [masked_context.replace('[MASK]', '') for masked_context in masked_contexts]

            train_contexts = masked_contexts[:int(0.7 * len(masked_contexts))]

            if verbose:
                print()
                print(' {:5}  {:20}'.format('TRAIN', entity_label))
                print(100 * '-')
                for train_context in train_contexts:
                    print(repr(train_context[:100]))
                print()

            es_doc = {'entity': entity,
                      'context': '\n'.join(train_contexts),
                      'entity_label': entity_label}

            es.index(index=index_name, body=es_doc)
            es.indices.refresh(index=index_name)

            test_contexts = masked_contexts[int(0.7 * len(masked_contexts)):]
            for i, test_context in enumerate(test_contexts):
                insert_context(test_contexts_conn, entity, test_context, entity_label)

            test_contexts_conn.commit()
