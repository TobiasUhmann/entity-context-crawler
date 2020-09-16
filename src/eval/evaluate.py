#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random

from argparse import ArgumentParser, HelpFormatter
from elasticsearch import Elasticsearch
from os.path import isdir
from ryn.graphs.split import Dataset

from eval.baseline_model import BaselineModel
from eval.evaluator import Evaluator


def main():
    arg_parser = ArgumentParser(description='Evaluate relations prediction',
                                formatter_class=lambda prog: HelpFormatter(prog, max_help_position=60, width=120))

    arg_parser.add_argument('dataset_dir', metavar='dataset-dir',
                            help='path to directory containing data files in OpenKE format')

    default_es_url = 'localhost:9200'
    arg_parser.add_argument('--es-url', dest='es_url', default=default_es_url,
                            help='Elasticsearch URL (default: %s)' % default_es_url)

    model_choices = ['baseline-10', 'baseline-100']
    default_model = model_choices[0]
    arg_parser.add_argument('--model', dest='model', choices=model_choices, default=default_model,
                            help='one of %s (default: %s)' % (model_choices, default_model))

    arg_parser.add_argument('--random-seed', dest='random_seed',
                            help='Seed for Python random. Use together with PYTHONHASHSEED.')

    args = arg_parser.parse_args()

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:24} {}'.format('Dataset dir', args.dataset_dir))
    print()
    print('    {:24} {}'.format('Elasticsearch URL', args.es_url))
    print('    {:24} {}'.format('Model', args.model))
    print('    {:24} {}'.format('Random seed', args.random_seed))
    print()
    print('    {:24} {}'.format('PYTHONHASHSEED', os.getenv('PYTHONHASHSEED')))
    print()

    #
    # Check for input/output files
    #

    if not isdir(args.dataset_dir):
        print('Dataset dir not found')
        exit()

    #
    # Optionally, init random generator
    #

    if args.random_seed:
        random.seed(args.random_seed)

    #
    # Evaluate
    #

    evaluate(args.dataset_dir, args.es_url, args.model)


def evaluate(dataset_dir, es_url, model):
    """For each open-world entity: Evaluate predicted triples"""

    #
    # Load data
    #

    print('Read dataset...', end='')
    dataset = Dataset.load(dataset_dir)
    print(' done')

    id2ent = dataset.id2ent
    id2rel = dataset.id2rel

    cw_triples = dataset.cw_train.triples | dataset.cw_valid.triples

    ow_entities = dataset.ow_valid.owe
    ow_triples = dataset.ow_valid.triples

    all_triples = cw_triples | ow_triples

    #
    # Sidebar: Model selection
    #

    if model == 'baseline-10':
        es = Elasticsearch([es_url])
        es_index = 'enwiki-latest-cw-contexts-10-500'
        ow_contexts_db = 'data/enwiki-latest-ow-contexts-10-500.db'
        ent2id = {ent: id for id, ent in id2ent.items()}
        model = BaselineModel(es, es_index, ow_contexts_db, id2ent, all_triples)

    elif model == 'baseline-100':
        es = Elasticsearch([es_url])
        es_index = 'enwiki-latest-cw-contexts-100-500'
        ow_contexts_db = 'data/enwiki-latest-ow-contexts-100-500.db'
        ent2id = {ent: id for id, ent in id2ent.items()}
        model = BaselineModel(es, es_index, ow_contexts_db, id2ent, all_triples)

    #
    # Evaluate model
    #

    some_ow_entities = random.sample(ow_entities, 10)
    total_result = Evaluator(model, ow_triples, some_ow_entities).run()

    results, mAP = total_result.results, total_result.map

    for ow_entity, result in zip(some_ow_entities, results):
        pred_ow_triples = result.pred_ow_triples
        precision = result.precision
        recall = result.recall
        f1 = result.f1
        ap = result.ap

        pred_cw_entity = result.pred_cw_entity
        pred_cw_entity_label = id2ent[pred_cw_entity] if pred_cw_entity != '' else '<None>'
        pred_ow_triples_hits = result.pred_ow_triples_hits

        print()
        print(id2ent[ow_entity] + ' -> ' + pred_cw_entity_label)
        print(50 * '-')
        count = 0
        for triple, hit_marker in zip(pred_ow_triples, pred_ow_triples_hits):
            if count == 20:
                break
                
            head, tail, rel = triple
            print('{} {:30} {:30} {}'.format(
                hit_marker,
                truncate('{}'.format(id2ent[head]), 28),
                truncate('{}'.format(id2ent[tail]), 28),
                '{}'.format(id2rel[rel])))
            count += 1
        if len(pred_ow_triples) - count > 0:
            print('[{} more hidden]'.format(len(pred_ow_triples) - count))
        print(50 * '-')
        print('{:20} {:.2f}'.format('Precision', precision))
        print('{:20} {:.2f}'.format('Recall', recall))
        print('{:20} {:.2f}'.format('F1-Score', f1))
        print('{:20} {:.2f}'.format('Average Precision', ap))

    print()
    print('mAP = ', mAP)


def truncate(str, max_len):
    return (str[:max_len - 3] + '...') if len(str) > max_len else str


if __name__ == '__main__':
    main()
