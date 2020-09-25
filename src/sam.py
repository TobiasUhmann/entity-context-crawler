from argparse import ArgumentParser

import build_links_db


def main():
    parser = ArgumentParser()
    sub_parsers = parser.add_subparsers()

    build_links_db_parser = sub_parsers.add_parser('build-links-db')
    build_links_db.add_parser_args(build_links_db_parser)
    build_links_db_parser.set_defaults(func=build_links_db.run)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
