import random
import sys
from argparse import ArgumentParser, HelpFormatter
from typing import List

from entity_context_crawler.cmd import build_contexts_db, build_matches_db


def main(argv: List[str] = None) -> int:
    """ Parse arguments and run specified sub command """

    #
    # Build main arg parser
    #

    def get_formatter(prog):
        return HelpFormatter(prog, max_help_position=40)

    parser = ArgumentParser(
        formatter_class=get_formatter,
        description='The Sentence (Sam)pler Tool Suite')

    sub_parsers = parser.add_subparsers(required=True)

    #
    # Build parent parser with common args
    #

    common_parser = ArgumentParser(add_help=False)

    common_parser.add_argument('--random-seed', dest='random_seed', metavar='STR',
                               help='Use together with PYTHONHASHSEED for reproducibility')

    #
    # Add build-matches-db sub command
    #

    build_matches_db_parser = sub_parsers.add_parser(
        'build-matches-db', formatter_class=get_formatter, parents=[common_parser],
        description='Match the Freebase entities (considering the link graph)')

    build_matches_db.add_parser_args(build_matches_db_parser)
    build_matches_db_parser.set_defaults(func=build_matches_db.run)

    #
    # Add build-contexts-db sub command
    #

    build_contexts_db_parser = sub_parsers.add_parser(
        'build-contexts-db', formatter_class=get_formatter, parents=[common_parser],
        description='Crop and store context for entity matches')

    build_contexts_db.add_parser_args(build_contexts_db_parser)
    build_contexts_db_parser.set_defaults(func=build_contexts_db.run)

    #
    # Seed random generator & Run specified sub command
    #

    if argv:
        args = parser.parse_args(argv[1:])
    else:
        args = parser.parse_args()

    if args.random_seed:
        random.seed(args.random_seed)

    args.func(args)

    return 0


if __name__ == '__main__':
    main(sys.argv)
