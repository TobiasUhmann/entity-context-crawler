import sqlite3

from argparse import ArgumentParser, Namespace
from datetime import datetime
from elasticsearch import Elasticsearch
from os import remove
from os.path import isfile, isdir
from ryn.graphs.split import Dataset
from typing import Set

from dao.contexts import create_contexts_table, insert_context, select_contexts


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        contexts-db
        dataset-dir
        cw-es-index
        ow-contexts-db
        --limit-contexts
        --overwrite
    """

    parser.add_argument('contexts_db', metavar='contexts-db',
                        help='Path to input contexts DB')

    parser.add_argument('dataset_dir', metavar='dataset-dir',
                        help='Path to directory containing input OpenKE files')

    parser.add_argument('cw_es_index', metavar='cw-es-index',
                        help='Name of output closed world Elasticsearch index')

    parser.add_argument('ow_contexts_db', metavar='ow-contexts-db',
                        help='Path to output open world contexts DB')

    default_es_instance = 'localhost:9200'
    parser.add_argument('--es-instance', dest='es_instance', metavar='STR', default=default_es_instance,
                        help='Address of Elasticsearch instance (default: {})'.format(default_es_instance))

    default_limit_contexts = None
    parser.add_argument('--limit-contexts', dest='limit_contexts', type=int, metavar='INT',
                        default=default_limit_contexts,
                        help='Process only the first ... contexts for each entity'
                             ' (default: {})'.format(default_limit_contexts))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite Elasticsearch index and contexts DB if they already exist')


def run(args: Namespace):
    """ Parse args, print applied config, check whether files and index exist, run program """

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('Contexts DB', args.contexts_db))
    print('    {:20} {}'.format('Dataset dir', args.dataset_dir))
    print('    {:20} {}'.format('CW ES index', args.cw_es_index))
    print('    {:20} {}'.format('OW DB', args.ow_db))
    print()
    print('    {:20} {}'.format('ES instance', args.es_instance))
    print('    {:20} {}'.format('Limit contexts', args.limit_contexts))
    print('    {:20} {}'.format('Overwrite', args.overwrite))
    print()

    #
    # Check if contexts DB, closed world ES index and open world DB exist
    #

    if not isfile(args.contexts_db):
        print('Contexts DB not found')
        exit()

    if not isdir(args.dataset_dir):
        print('Dataset dir not found')
        exit()

    es = Elasticsearch([args.es_instance])
    if es.indices.exists(index=args.cw_index):
        if args.overwrite:
            es.indices.delete(index=args.cw_index, ignore=[400, 404])
        else:
            print('Closed world ES index already exists. Use --overwrite to overwrite it')
            exit()

    if isfile(args.ow_db):
        if args.overwrite:
            remove(args.ow_db)
        else:
            print('Open world DB already exists. Use --overwrite to overwrite it')
            exit()

    #
    # Run program
    #

    build(es, args.contexts_db, args.dataset_dir, args.cw_index, args.ow_db, args.limit_contexts)


#
# BUILD
#

def build(es, contexts_db, dataset_dir, cw_index, ow_db, limit_contexts):
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

            masked_contexts = select_contexts(contexts_conn, entity, limit_contexts)
            masked_contexts = [masked_context.replace('[MASK]', '') for masked_context in masked_contexts]

            es_doc = {'entity': entity,
                      'context': '\n'.join(masked_contexts),
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

            masked_contexts = select_contexts(contexts_conn, entity, limit_contexts)

            for masked_context in masked_contexts:
                insert_context(ow_conn, entity, masked_context, entity_label)

        ow_conn.commit()

        print('Done.')
