#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from typing import Set, Tuple, List

from eval.evaluator import Evaluator
from eval.model import Model

from ryn.graphs import split


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate relations prediction',
        formatter_class=lambda prog: argparse.MetavarTypeHelpFormatter(prog, max_help_position=60, width=120))

    args = parser.parse_args()

    #
    # Load data
    #

    dataset = split.Dataset.load('data/oke.fb15k237_0.50-0.70_50_30061990')

    #
    # Evaluate
    #

    triples: Set[Tuple[int, int, int]] = dataset.cw_train.triples
    triples = {(head, tail, tag) for head, tail, tag in triples
               if head < 100 and tail < 100}
    entity_ids: List[int] = list(dataset.ent2id.keys())
    entity_ids = [entity_id for entity_id in entity_ids if entity_id < 100]
    model = Model(dataset.ent2id, triples)

    evaluator = Evaluator(model, triples, entity_ids)
    result = evaluator.run()

    results, mAP = result.results, result.map
    print(mAP)
    for e_id, res in zip(entity_ids, results):
        predicted_triples = res.predicted_triples
        precision = res.precision
        recall = res.recall
        f1 = res.f1
        ap = res.ap

        print()
        print(dataset.ent2id[e_id])
        for head, tail, tag in predicted_triples:
            print(dataset.ent2id[head], '#', dataset.ent2id[tail], '#', dataset.rel2id[tag])
        print(precision, recall, f1, ap)


if __name__ == '__main__':
    main()
