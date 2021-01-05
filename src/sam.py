import random
from argparse import ArgumentParser, HelpFormatter

from cmd import build_baseline, build_contexts_db, build_es_test, eval_es_test, eval_model, query_es_test, \
    build_matches_db


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
        description='Match the entities (considering the link graph)')

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
    # Add build-es-test sub command
    #

    build_es_test_parser = sub_parsers.add_parser(
        'build-es-test', formatter_class=get_formatter, parents=[common_parser],
        description='Crop and store context for each entity match')

    build_es_test.add_parser_args(build_es_test_parser)
    build_es_test_parser.set_defaults(func=build_es_test.run)

    #
    # Add query-es-test sub command
    #

    query_es_test_parser = sub_parsers.add_parser(
        'query-es-test', formatter_class=get_formatter, parents=[common_parser],
        description='Query Elasticsearch index for test contexts')

    query_es_test.add_parser_args(query_es_test_parser)
    query_es_test_parser.set_defaults(func=query_es_test.run)

    #
    # Add eval-es-test sub command
    #

    eval_es_test_parser = sub_parsers.add_parser(
        'eval-es-test', formatter_class=get_formatter, parents=[common_parser],
        description='Determine how closely linked contexts of different entities are')

    eval_es_test.add_parser_args(eval_es_test_parser)
    eval_es_test_parser.set_defaults(func=eval_es_test.run)

    #
    # Add build-baseline sub command
    #

    build_baseline_parser = sub_parsers.add_parser(
        'build-baseline', formatter_class=get_formatter, parents=[common_parser],
        description='Build closed world ES index and open world DB')

    build_baseline.add_parser_args(build_baseline_parser)
    build_baseline_parser.set_defaults(func=build_baseline.run)

    #
    # Add eval-model sub command
    #

    eval_model_parser = sub_parsers.add_parser(
        'eval-model', formatter_class=get_formatter, parents=[common_parser],
        description='Evaluate model')

    eval_model.add_parser_args(eval_model_parser)
    eval_model_parser.set_defaults(func=eval_model.run)

    #
    # Seed random generator & Run specified sub command
    #

    args = parser.parse_args()

    if args.random_seed:
        random.seed(args.random_seed)

    args.func(args)


if __name__ == '__main__':
    main()
