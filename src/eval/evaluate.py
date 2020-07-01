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

    model = Model()
    triples: Set[Tuple[int, int, int]] = dataset.cw_train.triples
    entities: List[int] = list(dataset.ent2id.keys())

    evaluator = Evaluator(model, triples, entities)
    result = evaluator.run()

    results, mAP = result.results, result.map
    print(mAP)
    for res in results:
        print(res)


if __name__ == '__main__':
    main()
