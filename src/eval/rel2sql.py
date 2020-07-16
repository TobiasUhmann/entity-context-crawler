#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser, HelpFormatter


def main():
    arg_parser = ArgumentParser(description='Read OpenKE relations txt files into SQLite DB for easier debugging',
                                formatter_class=lambda prog: HelpFormatter(prog, max_help_position=60, width=120))

    arg_parser.add_argument('relations_txt', metavar='relations-txt',
                            help='path to input OpenKE relations txt file')

    arg_parser.add_argument('sqlite_db', metavar='sqlite-db',
                            help='path to target SQLite DB (create if not existing)')

    arg_parser.add_argument('table_name', metavar='table-name',
                            help='name of table in SQLite DB (must not exist yet)')

    args = arg_parser.parse_args()

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:24} {}'.format('Relations txt', args.relations_txt))
    print('    {:24} {}'.format('SQLite DB', args.sqlite_db))
    print('    {:24} {}'.format('Table name', args.table_name))
    print()

    #
    # Fill database
    #

    rel2sql()


def rel2sql():
    print('rel2sql')


if __name__ == '__main__':
    main()
