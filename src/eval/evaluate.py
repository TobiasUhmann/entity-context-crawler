#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

from eval.model import Model
from eval.result import Result


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate relations prediction',
        formatter_class=lambda prog: argparse.MetavarTypeHelpFormatter(prog, max_help_position=60, width=120))

    default_batch_size = 3
    parser.add_argument('--batch-size', dest='batch_size', type=int, default=default_batch_size,
                        help='entity batch size (default: {})'.format(default_batch_size))

    args = parser.parse_args()

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('Batch size', args.batch_size))
    print()

    #
    # Evaluate
    #

    evaluate(args.batch_size)


def evaluate(batch_size: int):
    entities = [x for x in range(10)]
    model = Model()

    for entities_batch in batches(entities, batch_size):
        triples_batch = model.predict(entities_batch)
        mmr = 1
        result = Result(triples_batch, mmr)
        model.train(triples_batch)


def batches(values, n=1):
    length = len(values)
    for i in range(0, length, n):
        yield values[i:min(i + n, length)]


if __name__ == '__main__':
    main()
