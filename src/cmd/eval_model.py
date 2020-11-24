import os
import random
from argparse import ArgumentParser, Namespace
from collections import Set
from os.path import isdir, isfile

import torch
from elasticsearch import Elasticsearch
from pykeen.evaluation import RankBasedMetricResults, RankBasedEvaluator, MetricResults
from ryn.graphs.split import Dataset

from eval.new_baseline_model import BaselineModel
from util.custom_types import Triple


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        model
        dataset-dir
        ow-contexts-db
        --baseline-cw-es-index
        --baseline-es-host
        --limit-entities
    """

    model_choices = ['baseline-10', 'baseline-100']
    parser.add_argument('model', metavar='model', choices=model_choices,
                        help='One of {}'.format(model_choices))

    parser.add_argument('dataset_dir', metavar='dataset-dir',
                        help='Path to (input) OpenKE dataset directory')

    parser.add_argument('ow_contexts_db', metavar='ow-contexts-db',
                        help='Path to (input) open world contexts DB')

    parser.add_argument('--baseline-cw-es-index', dest='baseline_cw_es_index', metavar='STR',
                        help='Name of (input) closed world Elasticsearch index')

    default_es_host = 'localhost:9200'
    parser.add_argument('--baseline-es-host', dest='baseline_es_host', metavar='STR', default=default_es_host,
                        help='Elasticsearch host (default: {})'.format(default_es_host))

    default_limit_entities = None
    parser.add_argument('--limit-entities', dest='limit_entities', type=int, metavar='INT',
                        default=default_limit_entities,
                        help='Process only first ... entities (default: {})'.format(default_limit_entities))


def run(args: Namespace):
    """
    - Print applied config
    - Check if files already exist
    - Run actual program
    """

    model = args.model
    dataset_dir = args.dataset_dir
    ow_contexts_db = args.ow_contexts_db

    baseline_cw_es_index = args.baseline_cw_es_index
    baseline_es_host = args.baseline_es_host
    limit_entities = args.limit_entities

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('model', model))
    print('    {:20} {}'.format('dataset-dir', dataset_dir))
    print('    {:20} {}'.format('ow-contexts-db', ow_contexts_db))
    print()
    print('    {:20} {}'.format('--baseline-cw-es-index', baseline_cw_es_index))
    print('    {:20} {}'.format('--baseline-es-host', baseline_es_host))
    print('    {:20} {}'.format('--limit-entities', limit_entities))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', python_hash_seed))
    print()

    #
    # Check mandatory params
    #

    if model in ['baseline-10', 'baseline-100']:
        if baseline_cw_es_index is None:
            print('--baseline-cw-es-index must be specified')
            exit()

    #
    # Check if files already exist
    #

    if not isdir(dataset_dir):
        print('OpenKE dataset directory not found')
        exit()

    if baseline_cw_es_index:
        baseline_es = Elasticsearch([baseline_es_host])
        if not baseline_es.indices.exists(index=baseline_cw_es_index):
            print('Closed world Elasticsearch index not found')
            exit()
    else:
        baseline_es = None

    if not isfile(ow_contexts_db):
        print('Open world DB not found')
        exit()

    #
    # Run actual program
    #

    _eval_model(model, dataset_dir, ow_contexts_db, baseline_es, baseline_cw_es_index, limit_entities)


def _eval_model(model_selection: str,
                dataset_dir: str,
                ow_contexts_db: str,
                baseline_es: Elasticsearch,
                baseline_cw_es_index: str,
                limit_entities: int):
    """
    - Load dataset
    - Build model
    - Evaluate model
    - Print results
    """

    print('Read dataset...', end='')
    dataset = Dataset.load(path=dataset_dir)
    print(' done')

    ow_entities: Set[int] = dataset.ow_valid.owe
    ow_triples: Set[Triple] = dataset.ow_valid.triples

    #
    # Build model
    #

    if model_selection in ['baseline-10', 'baseline-100']:
        model = BaselineModel(dataset, baseline_es, baseline_cw_es_index, ow_contexts_db)
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

    evaluator = RankBasedEvaluator()
    mapped_triples: torch.LongTensor = torch.tensor(list(ow_triples)[:100], dtype=torch.long)
    total_result: MetricResults = evaluator.evaluate(model, mapped_triples, batch_size=1024)

    print(total_result)

    #
    # Print results
    #

    # results, mean_ap = total_result.results, total_result.map
    #
    # print()
    # print('{:24} {:>8} {:>8} {:>8} {:>8}'.format('ENTITY', 'PREC', 'RECALL', 'F1', 'AP'))
    # print('-' * (24 + 4 * 9))
    # for ow_entity, result in zip(shuffled_ow_entities, results):
    #     label = truncate(id2ent[ow_entity], 24)
    #     prec, recall, f1, ap = result.precision, result.recall, result.f1, result.ap
    #     print('{:24} {:8.2f} {:8.2f} {:8.2f} {:8.2f}'.format(label, prec, recall, f1, ap))
    #
    # print()
    # print('mAP = {:.4f}'.format(mean_ap))


def truncate(text: str, max_len: int):
    return (text[:max_len - 3] + '...') if len(text) > max_len else text
