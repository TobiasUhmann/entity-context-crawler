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

    ent2id = dataset.ent2id
    rel2id = dataset.rel2id

    cw_entities = {ent2id[ent] for ent in dataset.cw_train.entities | dataset.cw_valid.entities}
    cw_triples = {(ent2id[head], ent2id[tail], rel2id[rel])
                  for head, tail, rel in dataset.cw_train.triples | dataset.cw_valid.triples}

    ow_entities = {ent2id[ent] for ent in dataset.ow_valid.owe}
    ow_triples = {(ent2id[head], ent2id[tail], rel2id[rel]) for head, tail, rel in dataset.ow_valid.triples}

    all_entities = cw_entities | ow_entities
    all_triples = cw_triples | ow_triples

    #
    # Create model
    #

    model = Model(all_triples)

    #
    # Evaluate model
    #

    subset = random.sample(ow_entities, 10)
    evaluator = Evaluator(model, subset, ow_triples)

    total_result = evaluator.run()
    results, mAP = total_result.results, total_result.map

    for ow_entity, result in zip(subset, results):
        pred_cw_entity = result.pred_cw_entity
        pred_ow_triples = result.pred_ow_triples
        precision = result.precision
        recall = result.recall
        f1 = result.f1
        ap = result.ap

        print()
        print(ow_entity + ' -> ' + pred_cw_entity)
        print(50 * '-')
        for head, tail, relation in pred_ow_triples:
            print('{:30} {:30} {}'.format(truncate(head, 28), truncate(tail, 28), relation))
        print(50 * '-')
        print('{:20} {}'.format('Precision', precision))
        print('{:20} {}'.format('Recall', recall))
        print('{:20} {}'.format('F1-Score', f1))
        print('{:20} {}'.format('Average Precision', ap))

    print('mAP = ', mAP)


def truncate(str, max_len):
    return (str[:max_len - 3] + '...') if len(str) > max_len else str


if __name__ == '__main__':
    main()
