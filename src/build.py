import sqlite3

from argparse import ArgumentParser, HelpFormatter
from datetime import datetime
from elasticsearch import Elasticsearch
from os import remove
from os.path import isfile, isdir
from ryn.graphs.split import Dataset
from typing import Set

from dao.contexts import create_contexts_table, insert_context, select_contexts


def main():
    """ Parse args, print applied config, check whether files and index exist, run program """

    #
    # Parse args
    #

    arg_parser = ArgumentParser(
        description='Build closed world ES index and open world DB',
        formatter_class=lambda prog: HelpFormatter(prog, max_help_position=60, width=120))

    arg_parser.add_argument('contexts_db', metavar='contexts-db',
                            help='path to input contexts DB')

    arg_parser.add_argument('dataset_dir', metavar='dataset-dir',
                            help='path to directory containing OpenKE files')

    arg_parser.add_argument('cw_index', metavar='cw-index',
                            help='name of output closed world ES index')

    arg_parser.add_argument('ow_db', metavar='ow-db',
                            help='path to output open world DB')

    default_es_host = 'localhost'
    arg_parser.add_argument('--es-host', dest='es_host', default=default_es_host,
                            help='default Elasticsearch host (default: %s)' % default_es_host)

    default_es_port = 9200
    arg_parser.add_argument('--es-port', dest='es_port', type=int, default=default_es_port,
                            help='default Elasticsearch port (default: %d)' % default_es_port)

    default_limit_contexts = 100
    arg_parser.add_argument('--limit-contexts', dest='limit_contexts', type=int, default=default_limit_contexts,
                            help='only process the first ... contexts for each entity'
                                 ' (default: {})'.format(default_limit_contexts))

    arg_parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                            help='overwrite ES index and DB if they already exist')

    args = arg_parser.parse_args()

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('Contexts DB', args.contexts_db))
    print('    {:20} {}'.format('Dataset dir', args.dataset_dir))
    print('    {:20} {}'.format('CW index', args.cw_index))
    print('    {:20} {}'.format('OW DB', args.ow_db))
    print()
    print('    {:20} {}'.format('ES host', args.es_host))
    print('    {:20} {}'.format('ES port', args.es_port))
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

    es = Elasticsearch(hosts=[args.es_host], port=args.es_port)
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

            es_doc = {'entity': entity_label, 'context': '\n'.join(masked_contexts)}
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


if __name__ == '__main__':
    main()
