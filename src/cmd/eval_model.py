import os
from argparse import ArgumentParser, Namespace
from os.path import isdir

import torch
from elasticsearch import Elasticsearch
from pykeen.evaluation import RankBasedEvaluator, RankBasedMetricResults
from ryn.graphs.split import Dataset

from models.baseline_model import BaselineModel
from util.log import log


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        model
        dataset-dir
        --baseline-es-host
        --baseline-es-index
        --baseline-ow-db
    """

    model_choices = ['baseline']
    parser.add_argument('model', metavar='model', choices=model_choices,
                        help='One of {}'.format(model_choices))

    parser.add_argument('dataset_dir', metavar='dataset-dir',
                        help='Path to (input) OpenKE dataset directory')

    default_es_host = 'localhost:9200'
    parser.add_argument('--baseline-es-host', dest='baseline_es_host', metavar='STR', default=default_es_host,
                        help='Elasticsearch host (default: {})'.format(default_es_host))

    parser.add_argument('--baseline-es-index', dest='baseline_es_index', metavar='STR',
                        help='Name of (input) closed world Elasticsearch index')

    parser.add_argument('--baseline-ow-db', dest='baseline_ow_db', metavar='STR',
                        help='Path to (input) open world contexts DB')


def run(args: Namespace):
    """
    - Print applied config
    - Check if files already exist
    - Run actual program
    """

    model = args.model
    dataset_dir = args.dataset_dir

    baseline_es_host = args.baseline_es_host
    baseline_es_index = args.baseline_es_index
    baseline_ow_db = args.baseline_ow_db

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('model', model))
    print('    {:20} {}'.format('dataset-dir', dataset_dir))
    print()
    print('    {:20} {}'.format('--baseline-es-host', baseline_es_host))
    print('    {:20} {}'.format('--baseline-es-index', baseline_es_index))
    print('    {:20} {}'.format('--baseline-ow-db', baseline_ow_db))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', python_hash_seed))
    print()

    #
    # Check mandatory params
    #

    if model == 'baseline':
        missing_params = False

        if baseline_es_index is None:
            print('--baseline-es-index must be specified')
            missing_params = True

        if baseline_ow_db is None:
            print('--baseline-ow-db must be specified')
            missing_params = True

        if missing_params:
            exit()

    #
    # Check if files already exist
    #

    if not isdir(dataset_dir):
        print('OpenKE dataset directory not found')
        exit()

    if baseline_es_index:
        baseline_es = Elasticsearch([baseline_es_host])
        if not baseline_es.indices.exists(index=baseline_es_index):
            print('Closed world Elasticsearch index not found')
            exit()
    else:
        baseline_es = None

    #
    # Run actual program
    #

    _eval_model(model, dataset_dir, baseline_es, baseline_es_index, baseline_ow_db)


def _eval_model(model_selection: str, dataset_dir: str, baseline_es: Elasticsearch, baseline_es_index: str,
                baseline_ow_db: str):
    """
    - Load dataset
    - Build model
    - Evaluate model
    - Print results
    """

    log('Read dataset...')
    dataset = Dataset.load(path=dataset_dir)
    log('Done')

    ow_ents = list(dataset.ow_valid.owe)
    ow_triples = [(head, rel, tail) for head, tail, rel in dataset.ow_valid.triples]

    #
    # Build model
    #

    if model_selection == 'baseline':
        model = BaselineModel(dataset_dir, baseline_es, baseline_es_index, baseline_ow_db)
        model.calc_score_matrix(ow_ents)
    else:
        raise AssertionError()

    #
    # Evaluate model
    #

    evaluator = RankBasedEvaluator()
    ow_triples_tensor: torch.LongTensor = torch.tensor(ow_triples, dtype=torch.long)
    result: RankBasedMetricResults = evaluator.evaluate(model, ow_triples_tensor, batch_size=1024)

    print(result)

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

# def truncate(text: str, max_len: int):
#     return (text[:max_len - 3] + '...') if len(text) > max_len else text
