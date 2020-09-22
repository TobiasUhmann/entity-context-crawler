import os
import random

from argparse import ArgumentParser
from elasticsearch import Elasticsearch
from os.path import isdir
from ryn.graphs.split import Dataset

from eval.baseline_model import BaselineModel
from eval.evaluator import Evaluator


def main():
    """
    - Parse args
    - Print applied config
    - Seed random generator
    - Check if files already exist
    - Run actual program
    """

    arg_parser = ArgumentParser(description='Evaluate model')

    arg_parser.add_argument('dataset_dir', metavar='dataset-dir',
                            help='path to directory containing OpenKE data')

    default_es_url = 'localhost:9200'
    arg_parser.add_argument('--es-url', dest='es_url', metavar='STR', default=default_es_url,
                            help='Elasticsearch URL (default: {})'.format(default_es_url))

    default_limit_entities = None
    arg_parser.add_argument('--limit-entities', dest='limit_entities', metavar='INT', type=int,
                            default=default_limit_entities,
                            help='for debugging: process only first ... entities (default: {})'.format(
                                default_limit_entities))

    model_choices = ['baseline-10', 'baseline-100']
    default_model = model_choices[1]
    arg_parser.add_argument('--model', dest='model', metavar='STR', choices=model_choices, default=default_model,
                            help='one of {} (default: {})'.format(model_choices, default_model))

    arg_parser.add_argument('--random-seed', dest='random_seed', metavar='STR',
                            help='seed for Python random, use together with PYTHONHASHSEED')

    args = arg_parser.parse_args()

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:24} {}'.format('Dataset dir', args.dataset_dir))
    print()
    print('    {:24} {}'.format('Elasticsearch URL', args.es_url))
    print('    {:24} {}'.format('Limit entities', args.limit_entities))
    print('    {:24} {}'.format('Model', args.model))
    print('    {:24} {}'.format('Random seed', args.random_seed))
    print()
    print('    {:24} {}'.format('PYTHONHASHSEED', os.getenv('PYTHONHASHSEED')))
    print()

    #
    # Seed random generator
    #

    if args.random_seed:
        random.seed(args.random_seed)

    #
    # Check if files already exist
    #

    if not isdir(args.dataset_dir):
        print('Dataset dir not found')
        exit()

    #
    # Run actual program
    #

    evaluate(args.dataset_dir, args.limit_entities, args.es_url, args.model)


def evaluate(dataset_dir: str, limit_entities: int, es_url: str, model_selection: str):
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
        es = Elasticsearch([es_url])
        es_index = 'enwiki-latest-cw-contexts-10-500'
        ow_contexts_db = 'data/enwiki-latest-ow-contexts-10-500.db'
        model = BaselineModel(dataset, es, es_index, ow_contexts_db)

    elif model_selection == 'baseline-100':
        es = Elasticsearch([es_url])
        es_index = 'enwiki-latest-cw-contexts-100-500'
        ow_contexts_db = 'data/enwiki-latest-ow-contexts-100-500.db'
        model = BaselineModel(dataset, es, es_index, ow_contexts_db)

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


if __name__ == '__main__':
    main()
