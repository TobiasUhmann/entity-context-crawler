import os
import pickle
import sqlite3
from argparse import ArgumentParser, Namespace
from os import remove
from os.path import isfile, isdir
from typing import Set

from elasticsearch import Elasticsearch
from ryn.graphs import split

from dao.contexts_db import create_contexts_table, insert_context, select_contexts
from models.baseline_model import BaselineModel
from util.log import log


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        ryn-dataset
        contexts-db
        es-index
        ow-db
        pickle-file
        --es-host
        --limit-contexts
        --overwrite
    """

    parser.add_argument('ryn_dataset', metavar='ryn-dataset',
                        help='Path to (input) Ryn dataset directory')

    parser.add_argument('contexts_db', metavar='contexts-db',
                        help='Path to (input) contexts DB')

    parser.add_argument('es_index', metavar='es-index',
                        help='Name of (output) closed world Elasticsearch index')

    parser.add_argument('ow_db', metavar='ow-db',
                        help='Path to (output) open world contexts DB')

    parser.add_argument('pickle_file', metavar='pickle-file',
                        help='Path to (output) pickle file')

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
    - Check if output files already exist
    - Run actual program
    """

    ryn_dataset = args.ryn_dataset
    contexts_db = args.contexts_db
    es_index = args.es_index
    ow_db = args.ow_db
    pickle_file = args.pickle_file

    es_host = args.es_host
    limit_contexts = args.limit_contexts
    overwrite = args.overwrite
    random_seed = args.random_seed

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('ryn-dataset', ryn_dataset))
    print('    {:20} {}'.format('contexts-db', contexts_db))
    print('    {:20} {}'.format('es-index', es_index))
    print('    {:20} {}'.format('ow-db', ow_db))
    print('    {:20} {}'.format('pickle-file', pickle_file))
    print()
    print('    {:20} {}'.format('--es-host', es_host))
    print('    {:20} {}'.format('--limit-contexts', limit_contexts))
    print('    {:20} {}'.format('--overwrite', overwrite))
    print('    {:20} {}'.format('--random-seed', random_seed))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', python_hash_seed))
    print()

    #
    # Check if output files already exist
    #

    if not isdir(ryn_dataset):
        print('Ryn dataset directory not found')
        exit()

    if not isfile(contexts_db):
        print('Contexts DB not found')
        exit()

    es = Elasticsearch([es_host])
    if es.indices.exists(index=es_index):
        if overwrite:
            es.indices.delete(index=es_index, ignore=[400, 404])
        else:
            print('Closed world Elasticsearch index already exists, use --overwrite to overwrite it')
            exit()

    if isfile(ow_db):
        if overwrite:
            remove(ow_db)
        else:
            print('Open world DB already exists, use --overwrite to overwrite it')
            exit()

    if isfile(pickle_file):
        if overwrite:
            remove(pickle_file)
        else:
            print('Pickle file already exists, use --overwrite to overwrite it')
            exit()

    #
    # Run actual program
    #

    _build_baseline(ryn_dataset, es, contexts_db, es_index, ow_db, pickle_file, limit_contexts)


#
# BUILD
#

def _build_baseline(ryn_dataset: str, es: Elasticsearch, contexts_db: str, es_index: str, ow_db: str, pickle_file: str,
                    limit_contexts: int):
    """ Build closed world ES index and open world DB """

    with sqlite3.connect(contexts_db) as contexts_conn, \
            sqlite3.connect(ow_db) as ow_conn:
        #
        # Load data
        #

        log('Read dataset...')

        dataset = split.Dataset.load(path=ryn_dataset)

        id2ent = dataset.id2ent

        cw_ents: Set[int] = dataset.cw_train.owe
        ow_all_ents: Set[int] = dataset.ow_valid.owe | dataset.ow_test.owe

        log('Done')

        #
        # Build closed world ES index
        #

        log()
        log('Build closed world ES index...')

        for i, entity in enumerate(cw_ents):
            entity_label: str = id2ent[entity]

            log('{:,} closed world entities | {}'.format(i, entity_label))

            ow_contexts = [c.masked_context for c in select_contexts(contexts_conn, entity, limit_contexts)]
            ow_contexts = [masked_context.replace('#', '') for masked_context in ow_contexts]

            es_doc = {'entity': entity,
                      'context': '\n'.join(ow_contexts),
                      'entity_label': entity_label}

            es.index(index=es_index, body=es_doc)

        es.indices.refresh(index=es_index)

        log('Done')

        #
        # Build open world DB
        #

        log()
        log('Build open world DB...')

        create_contexts_table(ow_conn)

        for i, entity in enumerate(ow_all_ents):
            entity_label: str = id2ent[entity]

            log('{:,} open world entities | {}'.format(i, entity_label))

            ow_contexts = select_contexts(contexts_conn, entity, limit_contexts)

            for ow_context in ow_contexts:
                insert_context(ow_conn, ow_context)

        ow_conn.commit()

        log('Done')

        #
        # Calc and persist score matrix
        #

        log()
        log('Calc and persist score matrix...')

        model = BaselineModel(ryn_dataset, es, es_index, ow_db)
        model.calc_score_matrix(ow_all_ents)

        with open(pickle_file, 'wb') as fh:
            pickle.dump(model.score_matrix, fh)

        log('Done')
