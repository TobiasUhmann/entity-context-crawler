import os
import sqlite3
from argparse import ArgumentParser, Namespace
from os import path, makedirs, remove
from os.path import isdir, isfile
from typing import Set

from elasticsearch import Elasticsearch
from ryn.graphs import split

from dao.contexts_db import create_contexts_table, insert_context, Context
from dao.contexts_txt import load_contexts
from dao.score_matrix_pickle import save_score_matrix
from models.baseline_model import BaselineModel
from util.log import log


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        ryn-dataset
        baseline-name
        --es-host
        --limit-contexts
        --output-dir
        --overwrite
    """

    parser.add_argument('ryn_dataset', metavar='ryn-dataset',
                        help='Path to (input) Ryn dataset directory')

    parser.add_argument('baseline_name', metavar='baseline-name',
                        help='Name of (output) baseline model')

    default_es_host = 'localhost:9200'
    parser.add_argument('--es-host', dest='es_host', metavar='STR', default=default_es_host,
                        help='Elasticsearch host (default: {})'.format(default_es_host))

    default_limit_contexts = None
    parser.add_argument('--limit-contexts', dest='limit_contexts', type=int, metavar='INT',
                        default=default_limit_contexts,
                        help='Process only first ... contexts for each entity'
                             ' (default: {})'.format(default_limit_contexts))

    default_output_dir = './'
    parser.add_argument('--output-dir', dest='output_dir', metavar='STR',
                        help='Path to (output) output directory (default: {})'.format(default_output_dir))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite Elasticsearch index and contexts DB if they already exist')


def run(args: Namespace):
    """
    - Print applied config
    - Check if output files already exist
    - Run actual program
    """

    ryn_dataset = args.ryn_dataset
    baseline_name = args.baseline_name

    es_host = args.es_host
    limit_contexts = args.limit_contexts
    output_dir = args.output_dir
    overwrite = args.overwrite
    random_seed = args.random_seed

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('ryn-dataset', ryn_dataset))
    print('    {:20} {}'.format('baseline-name', baseline_name))
    print()
    print('    {:20} {}'.format('--es-host', es_host))
    print('    {:20} {}'.format('--limit-contexts', limit_contexts))
    print('    {:20} {}'.format('--output-dir', output_dir))
    print('    {:20} {}'.format('--overwrite', overwrite))
    print('    {:20} {}'.format('--random-seed', random_seed))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', python_hash_seed))

    #
    # Assert that (input) Ryn dataset dir exists
    #

    if not isdir(ryn_dataset):
        print('Ryn dataset directory not found')
        exit()

    #
    # Assert that (output) OW DB and score matrix pickle do not already exist
    #

    baseline_dir = path.join(output_dir, baseline_name)
    makedirs(baseline_dir, exist_ok=True)

    ow_db = path.join(baseline_dir, baseline_name + '.db')
    score_matrix_pickle = path.join(baseline_dir, baseline_name + '.p')

    if isfile(ow_db):
        if overwrite:
            remove(ow_db)
        else:
            print('OW DB already exists, use --overwrite to overwrite it')
            exit()

    if isfile(score_matrix_pickle):
        if overwrite:
            remove(score_matrix_pickle)
        else:
            print('Score matrix pickle already exists, use --overwrite to overwrite it')
            exit()

    #
    # Assert that (output) ES index does not already exist
    #

    es = Elasticsearch([es_host])
    es_index = baseline_name
    if es.indices.exists(index=es_index):
        if overwrite:
            es.indices.delete(index=es_index, ignore=[400, 404])
        else:
            print('ES index already exists, use --overwrite to overwrite it')
            exit()

    #
    # Run actual program
    #

    _build_baseline(ryn_dataset, baseline_name, es, es_index, limit_contexts, ow_db, score_matrix_pickle)


#
# BUILD
#

def _build_baseline(dataset_dir: str, baseline_name: str, es: Elasticsearch, es_index: str, limit_contexts: int,
                    ow_db: str, score_matrix_pickle: str):
    """ Use Ryn dataset to build baseline (consisting of ES index, OW DB, and score matrix pickle """

    #
    # Load split
    #

    log()
    log('Load split...')

    split_dir = path.join(dataset_dir, 'split')
    dataset = split.Dataset.load(path=split_dir)

    ent_to_lbl = dataset.id2ent
    ow_all_ents: Set[int] = dataset.ow_valid.owe | dataset.ow_test.owe

    log('Done')

    #
    # Load sentences
    #

    log()
    log('Load contexts...')

    train_contexts_file = f'{dataset_dir}/text/cw.train-sentences.txt'
    valid_contexts_file = f'{dataset_dir}/text/ow.valid-sentences.txt'
    test_contexts_file = f'{dataset_dir}/text/ow.test-sentences.txt'

    train_contexts = load_contexts(train_contexts_file)
    valid_contexts = load_contexts(valid_contexts_file)
    test_contexts = load_contexts(test_contexts_file)

    valid_test_contexts = {**valid_contexts, **test_contexts}

    log('Done')

    #
    # Build ES index
    #

    log()
    log('Build ES index...')

    for i, ent in enumerate(train_contexts):
        ent_lbl = ent_to_lbl[ent]

        log('CW entity {:,} | {}'.format(i, ent_lbl))

        contexts = list(train_contexts[ent])[:limit_contexts]
        joined_contexts = '\n'.join(contexts)

        es_doc = {'entity': ent, 'context': joined_contexts, 'entity_label': ent_lbl}
        es.index(index=es_index, body=es_doc)

    es.indices.refresh(index=es_index)

    log('Done')

    #
    # Build OW DB
    #

    log()
    log('Build OW DB...')

    with sqlite3.connect(ow_db) as ow_conn:
        create_contexts_table(ow_conn)

        for i, ent in enumerate(valid_test_contexts):
            ent_lbl = ent_to_lbl[ent]

            log('OW entity {:,} | {}'.format(i, ent_lbl))

            contexts = list(valid_test_contexts[ent])[:limit_contexts]
            joined_contexts = '\n'.join(contexts)

            insert_context(ow_conn, Context(ent, ent_lbl, None, None, None, joined_contexts))

        ow_conn.commit()

    log('Done')

    #
    # Calc and save score matrix
    #

    log()
    log('Calc and save score matrix...')

    model = BaselineModel(split_dir, es, es_index, ow_db)
    model.calc_score_matrix(ow_all_ents)

    save_score_matrix(score_matrix_pickle, model.score_matrix)

    log('Done')
