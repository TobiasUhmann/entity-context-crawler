import random

from argparse import ArgumentParser, HelpFormatter

import build_contexts_db
import build_links_db
import build_matches_db


def main():
    """ Parse arguments and run specified sub command """

    #
    # Build main arg parser
    #

    def get_formatter(prog):
        return HelpFormatter(prog, max_help_position=40)

    parser = ArgumentParser(
        formatter_class=get_formatter,
        description='The Sentence (Sam)pler Tool Suite')

    parser.add_argument('--random-seed', dest='random_seed',
                        help='Use together with PYTHONHASHSEED for reproducibility')

    sub_parsers = parser.add_subparsers()

    #
    # Add build-links-db sub command
    #

    build_links_db_parser = sub_parsers.add_parser(
        'build-links-db',
        formatter_class=get_formatter,
        description='Build Wikipedia link graph')

    build_links_db.add_parser_args(build_links_db_parser)
    build_links_db_parser.set_defaults(func=build_links_db.run)

    #
    # Add build-matches-db sub command
    #

    build_matches_db_parser = sub_parsers.add_parser(
        'build-matches-db',
        formatter_class=get_formatter,
        description='Match the Freenode entities (considering the link graph)')

    build_matches_db.add_parser_args(build_matches_db_parser)
    build_matches_db_parser.set_defaults(func=build_matches_db.run)

    #
    # Add build-contexts-db sub command
    #

    build_contexts_db_parser = sub_parsers.add_parser(
        'build-contexts-db',
        formatter_class=get_formatter,
        description='Crop and store context for entity matches')

    build_contexts_db.add_parser_args(build_contexts_db_parser)
    build_contexts_db_parser.set_defaults(func=build_contexts_db.run)

    #
    # Seed random generator and run specified sub command
    #

    args = parser.parse_args()

    if args.random_seed:
        random.seed(args.random_seed)

    args.func(args)


if __name__ == '__main__':
    main()
