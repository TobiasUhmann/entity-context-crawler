#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

from eval.evaluator import Evaluator
from eval.model import Model


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate relations prediction',
        formatter_class=lambda prog: argparse.MetavarTypeHelpFormatter(prog, max_help_position=60, width=120))

    args = parser.parse_args()

    #
    # Evaluate
    #

    model = Model()
    triples = [(3, 2, 3), (3, 5, 3), (5, 3, 3), (2, 5, 3), (4, 5, 3), (6, 5, 3)]
    entities = [x for x in range(10)]

    evaluator = Evaluator(model, triples, entities)
    result = evaluator.run()

    results, mAP = result.results, result.map
    print(mAP)
    for res in results:
        print(res)


if __name__ == '__main__':
    main()
