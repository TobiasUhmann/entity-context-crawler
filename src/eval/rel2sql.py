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

    ent2id = dataset.id2ent
    rel2id = dataset.id2rel

    # replace IDs with texts
    cw_train_triples = {(ent2id[head], ent2id[tail], rel2id[rel]) for head, tail, rel in dataset.cw_train.triples}
    cw_valid_triples = {(ent2id[head], ent2id[tail], rel2id[rel]) for head, tail, rel in dataset.cw_valid.triples}
    ow_valid_triples = {(ent2id[head], ent2id[tail], rel2id[rel]) for head, tail, rel in dataset.ow_valid.triples}
    ow_test_triples = {(ent2id[head], ent2id[tail], rel2id[rel]) for head, tail, rel in dataset.ow_test.triples}

    #
    # Save triples in DB
    #

    print('Save CW train triples...', end='')
    create_triples_table(sqlite_db, 'cw_train_triples')
    insert_triples(sqlite_db, 'cw_train_triples', cw_train_triples)
    print(' done')

    print('Save CW valid triples...', end='')
    create_triples_table(sqlite_db, 'cw_valid_triples')
    insert_triples(sqlite_db, 'cw_valid_triples', cw_valid_triples)
    print(' done')

    print('Save OW valid triples...', end='')
    create_triples_table(sqlite_db, 'ow_valid_triples')
    insert_triples(sqlite_db, 'ow_valid_triples', ow_valid_triples)
    print(' done')

    print('Save OW test triples...', end='')
    create_triples_table(sqlite_db, 'ow_test_triples')
    insert_triples(sqlite_db, 'ow_test_triples', ow_test_triples)
    print(' done')


def create_triples_table(db, table):
    sql = '''
        CREATE TABLE {} (
            head text,
            tail text,
            rel text
        )
    '''.format(table)

    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        cursor.close()


def insert_triples(db, table, triples):
    sql = '''
        INSERT INTO {} (head, tail, rel)
        VALUES (?, ?, ?)
    '''.format(table)

    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.executemany(sql, triples)
        cursor.close()


if __name__ == '__main__':
    main()
