import os
import random

from argparse import ArgumentParser, Namespace
from elasticsearch import Elasticsearch
from os.path import isdir, isfile
from ryn.graphs.split import Dataset

from eval.baseline_model import BaselineModel
from eval.evaluator import Evaluator


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        dataset-dir
        cw-es-index
        ow-contexts-db
        --es-host
        --limit-entities
        --model
    """

    parser.add_argument('dataset_dir', metavar='dataset-dir',
                        help='Path to (input) OpenKE dataset directory')

    parser.add_argument('cw_es_index', metavar='cw-es-index',
                        help='Name of (input) closed world Elasticsearch index')

    parser.add_argument('ow_contexts_db', metavar='ow-contexts-db',
                        help='Path to (input) open world contexts DB')

    default_es_host = 'localhost:9200'
    parser.add_argument('--es-host', dest='es_host', metavar='STR', default=default_es_host,
                        help='Elasticsearch host (default: {})'.format(default_es_host))

    default_limit_entities = None
    parser.add_argument('--limit-entities', dest='limit_entities', type=int, metavar='INT',
                        default=default_limit_entities,
                        help='Process only first ... entities (default: {})'.format(default_limit_entities))

    model_choices = ['baseline-10', 'baseline-100']
    default_model = model_choices[1]
    parser.add_argument('--model', dest='model', metavar='STR', choices=model_choices, default=default_model,
                        help='One of {} (default: {})'.format(model_choices, default_model))


def run(args: Namespace):
    """
    - Print applied config
    - Check if files already exist
    - Run actual program
    """

    dataset_dir = args.dataset_dir
    cw_es_index = args.cw_es_index
    ow_contexts_db = args.ow_contexts_db

    es_host = args.es_host
    limit_entities = args.limit_entities
    model = args.model

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('dataset-dir', dataset_dir))
    print('    {:20} {}'.format('cw-es-index', cw_es_index))
    print('    {:20} {}'.format('ow-contexts-db', ow_contexts_db))
    print()
    print('    {:20} {}'.format('--es-host', es_host))
    print('    {:20} {}'.format('--limit-entities', limit_entities))
    print('    {:20} {}'.format('--model', model))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', python_hash_seed))
    print()

    #
    # Check if files already exist
    #

    if not isdir(dataset_dir):
        print('OpenKE dataset directory not found')
        exit()

    es = Elasticsearch([es_host])
    if not es.indices.exists(index=cw_es_index):
        print('Closed world Elasticsearch index not found')
        exit()

    if not isfile(ow_contexts_db):
        print('Open world DB not found')
        exit()

    #
    # Run actual program
    #

    _eval_model(dataset_dir, es, cw_es_index, ow_contexts_db, limit_entities, model)


def _eval_model(
        dataset_dir: str,
        es: Elasticsearch,
        cw_es_index: str,
        ow_contexts_db: str,
        limit_entities: int,
        model_selection: str):
    """
    - Load dataset
    - Build model
    - Evaluate model
    - Print results
    """

    print('Read dataset...', end='')
    dataset = Dataset.load(dataset_dir)
    print(' done')

    id2ent = dataset.id2ent

    ow_entities = dataset.ow_valid.owe
    ow_triples = dataset.ow_valid.triples

    #
    # Build model
    #

    if model_selection == 'baseline-10':
        model = BaselineModel(dataset, es, cw_es_index, ow_contexts_db)

    elif model_selection == 'baseline-100':
        model = BaselineModel(dataset, es, cw_es_index, ow_contexts_db)

    else:
        raise AssertionError()

    #
    # Evaluate model
    #

    if limit_entities:
        shuffled_ow_entities = random.sample(ow_entities, limit_entities)
    else:
        shuffled_ow_entities = list(ow_entities)
        random.shuffle(shuffled_ow_entities)

    total_result = Evaluator(model, ow_triples, shuffled_ow_entities).run()

    #
    # Print results
    #

    results, mean_ap = total_result.results, total_result.map

    print()
    print('{:24} {:>8} {:>8} {:>8} {:>8}'.format('ENTITY', 'PREC', 'RECALL', 'F1', 'AP'))
    print('-' * (24 + 4 * 9))
    for ow_entity, result in zip(shuffled_ow_entities, results):
        label = truncate(id2ent[ow_entity], 24)
        prec, recall, f1, ap = result.precision, result.recall, result.f1, result.ap
        print('{:24} {:8.2f} {:8.2f} {:8.2f} {:8.2f}'.format(label, prec, recall, f1, ap))

    print()
    print('mAP = {:.4f}'.format(mean_ap))


def truncate(text: str, max_len: int):
    return (text[:max_len - 3] + '...') if len(text) > max_len else text
