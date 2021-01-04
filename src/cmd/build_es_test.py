import os
import sqlite3
from argparse import ArgumentParser, Namespace
from datetime import datetime
from os import remove
from os.path import isfile
from typing import List

from elasticsearch import Elasticsearch
from ryn.graphs.split import Dataset

from dao.contexts_db import create_contexts_table, insert_context, select_contexts, select_distinct_entities, Context


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        contexts-db
        es-index
        test-contexts-db
        --es-host
        --limit-contexts
        --overwrite
        --verbose
    """

    parser.add_argument('contexts_db', metavar='contexts-db',
                        help='Path to (input) contexts DB')

    parser.add_argument('es_index', metavar='es-index',
                        help='Name of (output) Elasticsearch index')

    parser.add_argument('test_contexts_db', metavar='test-contexts-db',
                        help='Path to (output) test contexts DB')

    default_es_host = 'localhost:9200'
    parser.add_argument('--es-host', dest='es_host', metavar='STR',
                        help='Elasticsearch host (default: {})'.format(default_es_host))

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
    """
    - Print applied config
    - Check if output files already exist
    - Run actual program
    """

    contexts_db = args.contexts_db
    es_index = args.es_index
    test_contexts_db = args.test_contexts_db

    es_host = args.es_host
    limit_contexts = args.limit_contexts
    overwrite = args.overwrite
    random_seed = args.random_seed
    verbose = args.verbose

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('contexts-db', contexts_db))
    print('    {:20} {}'.format('es-index', es_index))
    print('    {:20} {}'.format('test-contexts-db', test_contexts_db))
    print()
    print('    {:20} {}'.format('--es-host', es_host))
    print('    {:20} {}'.format('--limit-contexts', limit_contexts))
    print('    {:20} {}'.format('--overwrite', overwrite))
    print('    {:20} {}'.format('--random-seed', random_seed))
    print('    {:20} {}'.format('--verbose', verbose))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', python_hash_seed))
    print()

    #
    # Check if output files already exist
    #

    if not isfile(contexts_db):
        print('Contexts DB not found')
        exit()

    es = Elasticsearch([es_host])
    if es.indices.exists():
        if overwrite:
            es.indices.delete(index=es_index, ignore=[400, 404])
        else:
            print('Elasticsearch index already exists, use --overwrite to overwrite it')
            exit()

    if isfile(test_contexts_db):
        if overwrite:
            remove(test_contexts_db)
        else:
            print('Test contexts DB already exists, use --overwrite to overwrite it')
            exit()

    #
    # Run actual program
    #

    _build_es_test(es, contexts_db, es_index, test_contexts_db, limit_contexts, verbose)


#
# BUILD INDEX
#

def _build_es_test(es, contexts_db, index_name, test_contexts_db, limit_contexts, verbose):
    with sqlite3.connect(contexts_db) as contexts_conn, \
            sqlite3.connect(test_contexts_db) as test_contexts_conn:

        create_contexts_table(test_contexts_conn)

        entities: List[int] = select_distinct_entities(contexts_conn)

        dataset = Dataset.load('')  # TODO
        id2ent = dataset.id2ent

        for i, entity in enumerate(entities):
            entity_label = id2ent[entity]

            print('{} | {:,} entities | {}'.format(datetime.now().strftime("%H:%M:%S"), i, entity_label))

            contexts = select_contexts(contexts_conn, entity, limit_contexts)

            blanked_contexts = []
            for c in contexts:
                blanked_context = c.masked_context.replace('#', '')
                blanked_contexts.append(Context(c.entity, c.entity_label, c.mention, c.page_title, c.context,
                                                blanked_context))

            train_contexts = blanked_contexts[:int(0.7 * len(blanked_contexts))]

            if verbose:
                print()
                print(' {:5}  {:20}'.format('TRAIN', entity_label))
                print(100 * '-')
                for train_context in train_contexts:
                    print(repr(train_context.masked_context[:100]))
                print()

            es_doc = {'entity': entity,
                      'context': '\n'.join([c.masked_context for c in train_contexts]),
                      'entity_label': entity_label}

            es.index(index=index_name, body=es_doc)
            es.indices.refresh(index=index_name)

            test_contexts = blanked_contexts[int(0.7 * len(blanked_contexts)):]
            for test_context in test_contexts:
                insert_context(test_contexts_conn, test_context)

            test_contexts_conn.commit()
