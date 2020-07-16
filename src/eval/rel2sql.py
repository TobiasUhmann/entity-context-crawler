#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
from argparse import ArgumentParser, HelpFormatter
from os.path import isdir

from ryn.graphs.split import Dataset


def main():
    arg_parser = ArgumentParser(description='Read OpenKE relations txt files into SQLite DB for easier debugging',
                                formatter_class=lambda prog: HelpFormatter(prog, max_help_position=60, width=120))

    arg_parser.add_argument('dataset_dir', metavar='dataset-dir',
                            help='path to directory containing data files in OpenKE format')

    arg_parser.add_argument('sqlite_db', metavar='sqlite-db',
                            help='path to output SQLite DB')

    args = arg_parser.parse_args()

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:24} {}'.format('Dataset dir', args.dataset_dir))
    print('    {:24} {}'.format('SQLite DB', args.sqlite_db))
    print()

    #
    # Check for input/output files
    #

    if not isdir(args.dataset_dir):
        print('Dataset dir not found')
        exit()

    #
    # Fill database
    #

    rel2sql(args.dataset_dir, args.sqlite_db)


def rel2sql(dataset_dir, sqlite_db):
    #
    # Load data
    #

    print('Read dataset...', end='')
    dataset = Dataset.load(dataset_dir)
    print(' done')

    ent2id = dataset.ent2id
    rel2id = dataset.rel2id


if __name__ == '__main__':
    main()
