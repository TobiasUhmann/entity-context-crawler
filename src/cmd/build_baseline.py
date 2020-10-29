import os
import sqlite3

from argparse import ArgumentParser, Namespace
from datetime import datetime
from elasticsearch import Elasticsearch
from os import remove
from os.path import isfile, isdir
from ryn.graphs.split import Dataset
from typing import Set

from dao.contexts_db import create_contexts_table, insert_context, select_contexts


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        contexts-db
        dataset-dir
        cw-es-index
        ow-contexts-db
        --es-host
        --limit-contexts
        --overwrite
    """

    parser.add_argument('contexts_db', metavar='contexts-db',
                        help='Path to (input) contexts DB')

    parser.add_argument('dataset_dir', metavar='dataset-dir',
                        help='Path to (input) OpenKE dataset directory')

    parser.add_argument('cw_es_index', metavar='cw-es-index',
                        help='Name of (output) closed world Elasticsearch index')

    parser.add_argument('ow_contexts_db', metavar='ow-contexts-db',
                        help='Path to (output) open world contexts DB')

    default_es_host = 'localhost:9200'
    parser.add_argument('--es-host', dest='es_host', metavar='STR', default=default_es_host,
                        help='Elasticsearch host (default: {})'.format(default_es_host))

    default_limit_contexts = None
    parser.add_argument('--limit-contexts', dest='limit_contexts', type=int, metavar='INT',
                        default=default_limit_contexts,
                        help='Process only first ... contexts for each entity'
                             ' (default: {})'.format(default_limit_contexts))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite Elasticsearch index and contexts DB if they already exist')


def run(args: Namespace):
    """
    - Print applied config
    - Check if files already exist
    - Run actual program
    """

    contexts_db = args.contexts_db
    dataset_dir = args.dataset_dir
    cw_es_index = args.cw_es_index
    ow_contexts_db = args.ow_contexts_db

    es_host = args.es_host
    limit_contexts = args.limit_contexts
    overwrite = args.overwrite
    random_seed = args.random_seed

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('contexts-db', contexts_db))
    print('    {:20} {}'.format('dataset-dir', dataset_dir))
    print('    {:20} {}'.format('cw-es-index', cw_es_index))
    print('    {:20} {}'.format('ow-contexts-db', ow_contexts_db))
    print()
    print('    {:20} {}'.format('--es-host', es_host))
    print('    {:20} {}'.format('--limit-contexts', limit_contexts))
    print('    {:20} {}'.format('--overwrite', overwrite))
    print('    {:20} {}'.format('--random-seed', random_seed))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', python_hash_seed))
    print()

    #
    # Check if files already exist
    #

    if not isfile(contexts_db):
        print('Contexts DB not found')
        exit()

    if not isdir(dataset_dir):
        print('OpenKE dataset directory not found')
        exit()

    es = Elasticsearch([es_host])
    if es.indices.exists(index=cw_es_index):
        if overwrite:
            es.indices.delete(index=cw_es_index, ignore=[400, 404])
        else:
            print('Closed world Elasticsearch index already exists, use --overwrite to overwrite it')
            exit()

    if isfile(ow_contexts_db):
        if overwrite:
            remove(ow_contexts_db)
        else:
            print('Open world DB already exists, use --overwrite to overwrite it')
            exit()

    #
    # Run actual program
    #

    _build_baseline(es, contexts_db, dataset_dir, cw_es_index, ow_contexts_db, limit_contexts)


#
# BUILD
#

def _build_baseline(es, contexts_db, dataset_dir, cw_index, ow_db, limit_contexts):
    """ Build closed world ES index and open world DB """

    with sqlite3.connect(contexts_db) as contexts_conn, \
            sqlite3.connect(ow_db) as ow_conn:
        #
        # Load data
        #

        print('Read dataset...', end='')

        dataset = Dataset.load(dataset_dir)

        id2ent = dataset.id2ent

        cw_entities: Set[int] = dataset.cw_train.owe
        ow_entities: Set[int] = dataset.ow_valid.owe

        print(' done')

        #
        # Build closed world ES index
        #

        print()
        print('Build closed world ES index...')

        for i, entity in enumerate(cw_entities):
            entity_label: str = id2ent[entity]

            print('{} | {:,} closed world entities | {}'.format(datetime.now().strftime("%H:%M:%S"), i, entity_label))

            ow_contexts = [c.masked_context for c in select_contexts(contexts_conn, entity, limit_contexts)]
            ow_contexts = [masked_context.replace('#', '') for masked_context in ow_contexts]

            es_doc = {'entity': entity,
                      'context': '\n'.join(ow_contexts),
                      'entity_label': entity_label}

            es.index(index=cw_index, body=es_doc)

        es.indices.refresh(index=cw_index)

        print('Done.')

        #
        # Build open world DB
        #

        print()
        print('Build open world DB...')

        create_contexts_table(ow_conn)

        for i, entity in enumerate(ow_entities):
            entity_label: str = id2ent[entity]

            print('{} | {:,} open world entities | {}'.format(datetime.now().strftime("%H:%M:%S"), i, entity_label))

            ow_contexts = select_contexts(contexts_conn, entity, limit_contexts)

            for ow_context in ow_contexts:
                insert_context(ow_conn, ow_context)

        ow_conn.commit()

        print('Done.')
