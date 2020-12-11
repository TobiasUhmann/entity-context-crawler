import json
import os
from argparse import ArgumentParser, Namespace
from os import path
from os.path import isdir, isfile

import torch
from elasticsearch import Elasticsearch
from pykeen.evaluation import RankBasedEvaluator, RankBasedMetricResults
from ryn.graphs import split

from dao import score_matrix_pkl
from eval.custom_evaluator import CustomEvaluator, TotalResult
from models.baseline_model import BaselineModel
from util.log import log


def add_parser_args(parser: ArgumentParser):
    """
    Add arguments to arg parser:
        model
        dataset-dir
        --baseline-dir
        --baseline-es-host
        --baseline-name
        --eval-mode
        --test
    """

    model_choices = ['baseline']
    parser.add_argument('model', metavar='model', choices=model_choices,
                        help='One of {}'.format(model_choices))

    parser.add_argument('ryn_dataset_dir', metavar='ryn-dataset-dir',
                        help='Path to (input) Ryn dataset directory')

    default_baseline_dir = './'
    parser.add_argument('--baseline-dir', dest='baseline_dir', metavar='STR', default=default_baseline_dir,
                        help='Path to (input) baseline directory (default: {})'.format(default_baseline_dir))

    default_es_host = 'localhost:9200'
    parser.add_argument('--baseline-es-host', dest='baseline_es_host', metavar='STR', default=default_es_host,
                        help='Elasticsearch host (default: {})'.format(default_es_host))

    parser.add_argument('--baseline-name', dest='baseline_name', metavar='STR',
                        help='Name of (output) baseline model')

    eval_mode_choices = ['custom', 'pykeen']
    default_eval_mode = 'pykeen'
    parser.add_argument('--eval-mode', dest='eval_mode', choices=eval_mode_choices, default=default_eval_mode,
                        help='One of {} (default: {})'.format(eval_mode_choices, default_eval_mode))

    parser.add_argument('--test', dest='test', action='store_true',
                    help='Evaluate on test set')


def run(args: Namespace):
    """
    - Print applied config
    - Check if output files already exist
    - Run actual program
    """

    model = args.model
    ryn_dataset_dir = args.ryn_dataset_dir

    baseline_dir = args.baseline_dir
    baseline_es_host = args.baseline_es_host
    baseline_name = args.baseline_name
    eval_mode = args.eval_mode
    test = args.test

    python_hash_seed = os.getenv('PYTHONHASHSEED')

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('model', model))
    print('    {:20} {}'.format('ryn-dataset-dir', ryn_dataset_dir))
    print()
    print('    {:20} {}'.format('--baseline-dir', baseline_dir))
    print('    {:20} {}'.format('--baseline-es-host', baseline_es_host))
    print('    {:20} {}'.format('--baseline-name', baseline_name))
    print('    {:20} {}'.format('--eval-mode', eval_mode))
    print('    {:20} {}'.format('--test', test))
    print()
    print('    {:20} {}'.format('PYTHONHASHSEED', python_hash_seed))
    print()

    #
    # Assert that Ryn dataset dir exists
    #

    if not isdir(ryn_dataset_dir):
        print('Ryn dataset directory not found')
        exit()

    #
    # Model dependent checks
    #

    if model == 'baseline':

        if baseline_name is None:
            print('--baseline-name must be specified')
            exit()

        baseline_es = Elasticsearch([baseline_es_host])
        baseline_es_index = baseline_name
        if not baseline_es.indices.exists(index=baseline_es_index):
            print('Elasticsearch index not found')
            exit()

        baseline_ow_db = path.join(baseline_dir, 'open_world_contexts.db')
        if not isfile(baseline_ow_db):
            print('Open world DB not found')
            exit()

        baseline_score_matrix_pkl = path.join(baseline_dir, 'score_matrix.pkl')
        if not isfile(baseline_score_matrix_pkl):
            print('Score matrix PKL not found')
            exit()

    else:
        raise AssertionError()

    #
    # Run actual program
    #

    _eval_model(model, ryn_dataset_dir, baseline_es, baseline_es_index, baseline_ow_db, baseline_score_matrix_pkl,
                eval_mode, test)


def _eval_model(model_str: str, ryn_dataset_dir: str, baseline_es: Elasticsearch, baseline_es_index: str,
                baseline_ow_db: str, baseline_score_matrix_pkl: str, eval_mode: str, test: bool):
    """
    - Load dataset
    - Build model
    - Eval model
    - Print results
    """

    log('Load Ryn dataset...')

    split_dataset_dir = path.join(ryn_dataset_dir, 'split')
    dataset: split.Dataset = split.Dataset.load(path=split_dataset_dir)

    if test:
        ow_ents = list(dataset.ow_valid.owe)
        ow_triples = [(head, rel, tail) for head, tail, rel in dataset.ow_valid.triples]
    else:
        ow_ents = list(dataset.ow_test.owe)
        ow_triples = [(head, rel, tail) for head, tail, rel in dataset.ow_test.triples]

    log('Done')

    #
    # Build model
    #

    if model_str == 'baseline':
        model = BaselineModel(split_dataset_dir, baseline_es, baseline_es_index, baseline_ow_db)
        model.score_matrix = score_matrix_pkl.load_score_matrix(baseline_score_matrix_pkl)

    else:
        raise AssertionError()

    #
    # Eval model & Output results
    #

    if eval_mode == 'custom':
        evaluator = CustomEvaluator(model, ow_triples, ow_ents)
        result: TotalResult = evaluator.run()

        print(result.map)

    elif eval_mode == 'pykeen':
        evaluator = RankBasedEvaluator()
        ow_triples_tensor: torch.LongTensor = torch.tensor(ow_triples, dtype=torch.long)
        result: RankBasedMetricResults = evaluator.evaluate(model, ow_triples_tensor, batch_size=1024)

        result_dict = {
            'mean_rank': result.mean_rank,
            'mean_reciprocal_rank': result.mean_reciprocal_rank,
            'hits_at_k': result.hits_at_k,
            'adjusted_mean_rank': result.adjusted_mean_rank
        }

        with open('data/result.json', 'w') as fh:
            json.dump(result_dict, fh, sort_keys=True)

    else:
        raise AssertionError()
