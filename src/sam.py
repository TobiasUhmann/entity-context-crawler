from argparse import ArgumentParser, HelpFormatter

import build_links_db


def main():
    def get_formatter(prog):
        return HelpFormatter(prog, max_help_position=40)

    parser = ArgumentParser(formatter_class=get_formatter)
    sub_parsers = parser.add_subparsers()

    build_links_db_parser = sub_parsers.add_parser('build-links-db', formatter_class=get_formatter)
    build_links_db.add_parser_args(build_links_db_parser)
    build_links_db_parser.set_defaults(func=build_links_db.run)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
