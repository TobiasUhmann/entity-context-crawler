#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

from argparse import ArgumentParser, HelpFormatter
from os.path import isdir
from ryn.graphs.split import Dataset

from eval.evaluator import Evaluator
from eval.model import Model


def main():
    arg_parser = ArgumentParser(description='Evaluate relations prediction',
                                formatter_class=lambda prog: HelpFormatter(prog, max_help_position=60, width=120))

    arg_parser.add_argument('dataset_dir', metavar='dataset-dir',
                            help='path to directory containing data files in OpenKE format')

    args = arg_parser.parse_args()

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:24} {}'.format('Dataset dir', args.dataset_dir))
    print()

    #
    # Check for input/output files
    #

    if not isdir(args.dataset_dir):
        print('Dataset dir not found')
        exit()

    #
    # Evaluate
    #

    evaluate(args.dataset_dir)


def evaluate(dataset_dir):
    """For each open-world entity: Evaluate predicted triples"""

    #
    # Load data
    #

    print('Read dataset...', end='')
    dataset = Dataset.load(dataset_dir)
    print(' done')

    id2ent = dataset.id2ent
    id2rel = dataset.id2rel

    cw_entities = {id2ent[ent] for ent in dataset.cw_train.entities | dataset.cw_valid.entities}
    cw_triples = {(id2ent[head], id2ent[tail], id2rel[rel])
                  for head, tail, rel in dataset.cw_train.triples | dataset.cw_valid.triples}

    ow_entities = {id2ent[ent] for ent in dataset.ow_valid.owe}
    ow_triples = {(id2ent[head], id2ent[tail], id2rel[rel]) for head, tail, rel in dataset.ow_valid.triples}

    all_entities = cw_entities | ow_entities
    all_triples = cw_triples | ow_triples

    #
    # Create model
    #

    model = Model(all_triples)

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
        pred_ow_triples_hits = result.pred_ow_triples_hits

        print()
        print(ow_entity + ' -> ' + pred_cw_entity)
        print(50 * '-')
        count = 0
        for triple, hit in zip(pred_ow_triples, pred_ow_triples_hits):
            if count == 20:
                break
            head, tail, relation = triple
            hit_marker = '+' if hit else ' '
            print('{} {:30} {:30} {}'.format(hit_marker, truncate(head, 28), truncate(tail, 28), relation))
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
